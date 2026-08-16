"""
Hermes LinguaMind — Coin Ledger Service
Port: 8006 | Phase 3 — Production

Real Postgres-backed ledger (was an in-process dict — real money/rewards
data must survive restarts and be safe under concurrent requests). Balance
updates use SELECT ... FOR UPDATE row locking so two simultaneous
transactions for the same user can't race each other. Idempotency is
enforced by the database's unique constraint on idempotency_key, not an
in-memory set that would reset on restart.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import time
from datetime import datetime, date
from uuid import UUID, uuid4

from fastapi import FastAPI, Request
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
import structlog
import uvicorn

from shared.models.common import (
    HermesResponse, HealthStatus, CoinTransactionRequest, CoinBalanceResponse,
    CoinTransactionType, FraudRiskLevel, CoinBalanceORM, CoinTransactionORM,
)
from shared.utils.helpers import generate_request_id
from shared.database import get_db_session, db_healthy, init_db

logger = structlog.get_logger("hermes.coin")
app = FastAPI(title="Hermes Coin Ledger", version="3.1.0")


@app.on_event("startup")
async def _init_schema():
    """Idempotent: creates tables if another service hasn't already."""
    await init_db()
_app_start_time = time.time()

MAX_DAILY_EARN = 500


@app.get("/health", response_model=HealthStatus)
async def health_check():
    is_db_healthy = await db_healthy()
    return HealthStatus(status="healthy" if is_db_healthy else "degraded", service="coin_ledger", version="3.1.0",
                        timestamp=datetime.utcnow(), uptime_seconds=time.time() - _app_start_time,
                        dependencies={"database": "connected" if is_db_healthy else "unreachable"})


@app.post("/v1/transaction", response_model=HermesResponse)
async def create_transaction(request: Request, tx_request: CoinTransactionRequest):
    request_id = getattr(request.state, "request_id", generate_request_id())

    async with get_db_session() as session:
        # Idempotency: check for an existing transaction with this key first.
        existing_stmt = select(CoinTransactionORM).where(CoinTransactionORM.idempotency_key == tx_request.idempotency_key)
        existing = (await session.execute(existing_stmt)).scalar_one_or_none()
        if existing is not None:
            return HermesResponse(success=True, data={
                "transaction": _tx_to_dict(existing), "idempotent": True,
            }, request_id=request_id)

        # Row-lock the balance so concurrent transactions for this user serialize.
        balance_stmt = select(CoinBalanceORM).where(CoinBalanceORM.user_id == tx_request.user_id).with_for_update()
        balance = (await session.execute(balance_stmt)).scalar_one_or_none()
        if balance is None:
            balance = CoinBalanceORM(user_id=tx_request.user_id, balance=0, lifetime_earned=0,
                                      lifetime_spent=0, daily_earned_today=0, last_daily_reset=date.today())
            session.add(balance)
            await session.flush()

        today = date.today()
        if balance.last_daily_reset != today:
            balance.daily_earned_today = 0
            balance.last_daily_reset = today

        if tx_request.amount > 0 and balance.daily_earned_today + tx_request.amount > MAX_DAILY_EARN:
            return HermesResponse(success=False, error=f"Daily earning limit of {MAX_DAILY_EARN} exceeded",
                                  error_code="DAILY_LIMIT_EXCEEDED", request_id=request_id)

        new_balance = balance.balance + tx_request.amount
        if new_balance < 0:
            return HermesResponse(success=False, error="Insufficient balance",
                                  error_code="INSUFFICIENT_BALANCE", request_id=request_id)

        transaction = CoinTransactionORM(
            id=uuid4(), user_id=tx_request.user_id, transaction_type=tx_request.transaction_type,
            amount=tx_request.amount, balance_after=new_balance, idempotency_key=tx_request.idempotency_key,
            description=tx_request.description or "", metadata_payload=tx_request.metadata or {},
            fraud_risk_level=FraudRiskLevel.LOW, fraud_review_status="none",
        )

        balance.balance = new_balance
        if tx_request.amount > 0:
            balance.lifetime_earned += tx_request.amount
            balance.daily_earned_today += tx_request.amount
        else:
            balance.lifetime_spent += abs(tx_request.amount)

        session.add(transaction)
        try:
            await session.flush()
        except IntegrityError:
            # Lost the race on the idempotency-key unique constraint — another
            # concurrent request with the same key committed first. Return that one.
            await session.rollback()
            async with get_db_session() as retry_session:
                existing = (await retry_session.execute(existing_stmt)).scalar_one_or_none()
                if existing is not None:
                    return HermesResponse(success=True, data={
                        "transaction": _tx_to_dict(existing), "idempotent": True,
                    }, request_id=request_id)
            return HermesResponse(success=False, error="Concurrent transaction conflict, please retry",
                                  error_code="CONFLICT", request_id=request_id)

        logger.info("transaction_created", request_id=request_id, tx_id=str(transaction.id),
                    user_id=str(tx_request.user_id), amount=tx_request.amount)

        return HermesResponse(success=True, data={
            "transaction": _tx_to_dict(transaction),
            "balance": _balance_to_dict(balance),
        }, request_id=request_id)


@app.get("/v1/balance/{user_id}", response_model=HermesResponse)
async def get_balance(user_id: str, request: Request):
    request_id = getattr(request.state, "request_id", generate_request_id())
    uid = UUID(user_id)

    async with get_db_session() as session:
        balance = (await session.execute(
            select(CoinBalanceORM).where(CoinBalanceORM.user_id == uid)
        )).scalar_one_or_none()

        if balance is None:
            response = CoinBalanceResponse(user_id=uid, balance=0, lifetime_earned=0,
                                           lifetime_spent=0, daily_earned_today=0, daily_limit=MAX_DAILY_EARN)
        else:
            response = CoinBalanceResponse(
                user_id=uid, balance=balance.balance, lifetime_earned=balance.lifetime_earned,
                lifetime_spent=balance.lifetime_spent, daily_earned_today=balance.daily_earned_today,
                daily_limit=MAX_DAILY_EARN,
            )
        return HermesResponse(success=True, data=response.model_dump(), request_id=request_id)


@app.get("/v1/transactions/{user_id}", response_model=HermesResponse)
async def get_transactions(user_id: str, request: Request, limit: int = 50, offset: int = 0):
    request_id = getattr(request.state, "request_id", generate_request_id())
    uid = UUID(user_id)

    async with get_db_session() as session:
        total = (await session.execute(
            select(func.count()).select_from(CoinTransactionORM).where(CoinTransactionORM.user_id == uid)
        )).scalar_one()

        rows = (await session.execute(
            select(CoinTransactionORM).where(CoinTransactionORM.user_id == uid)
            .order_by(CoinTransactionORM.created_at.desc()).offset(offset).limit(limit)
        )).scalars().all()

        return HermesResponse(success=True, data={
            "transactions": [_tx_to_dict(tx) for tx in rows],
            "total": total, "limit": limit, "offset": offset,
        }, request_id=request_id)


@app.post("/v1/reconcile", response_model=HermesResponse)
async def reconcile_ledger(request: Request):
    """Real reconciliation: recompute each user's balance from the
    append-only transaction log and compare against the stored balance row,
    directly against Postgres (not an in-memory snapshot that would always
    trivially match itself)."""
    request_id = getattr(request.state, "request_id", generate_request_id())
    discrepancies = []

    async with get_db_session() as session:
        balances = (await session.execute(select(CoinBalanceORM))).scalars().all()
        for balance in balances:
            calculated = (await session.execute(
                select(func.coalesce(func.sum(CoinTransactionORM.amount), 0))
                .where(CoinTransactionORM.user_id == balance.user_id)
            )).scalar_one()
            if calculated != balance.balance:
                discrepancies.append({
                    "user_id": str(balance.user_id), "stored": balance.balance,
                    "calculated": calculated, "difference": calculated - balance.balance,
                })

        if discrepancies:
            return HermesResponse(success=False, error="Reconciliation failed", error_code="RECONCILIATION_FAILED",
                                  data={"discrepancies": discrepancies}, request_id=request_id)
        return HermesResponse(success=True, data={"status": "reconciled", "users_checked": len(balances)},
                              request_id=request_id)


@app.get("/v1/metrics")
async def get_metrics():
    async with get_db_session() as session:
        total_transactions = (await session.execute(select(func.count()).select_from(CoinTransactionORM))).scalar_one()
        total_volume = (await session.execute(
            select(func.coalesce(func.sum(func.abs(CoinTransactionORM.amount)), 0))
        )).scalar_one()
        active_users = (await session.execute(select(func.count()).select_from(CoinBalanceORM))).scalar_one()

    return {
        "uptime_seconds": time.time() - _app_start_time,
        "total_transactions": total_transactions,
        "total_volume": total_volume,
        "active_users": active_users,
    }


def _tx_to_dict(tx: CoinTransactionORM) -> dict:
    return {
        "id": str(tx.id), "user_id": str(tx.user_id), "transaction_type": tx.transaction_type.value,
        "amount": tx.amount, "balance_after": tx.balance_after, "idempotency_key": tx.idempotency_key,
        "description": tx.description, "metadata": tx.metadata_payload,
        "fraud_risk_level": tx.fraud_risk_level.value, "fraud_review_status": tx.fraud_review_status,
        "created_at": tx.created_at.isoformat() if tx.created_at else None,
    }


def _balance_to_dict(balance: CoinBalanceORM) -> dict:
    return {
        "user_id": str(balance.user_id), "balance": balance.balance, "lifetime_earned": balance.lifetime_earned,
        "lifetime_spent": balance.lifetime_spent, "daily_earned_today": balance.daily_earned_today,
        "last_daily_reset": balance.last_daily_reset.isoformat() if balance.last_daily_reset else None,
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8006, log_level="info")
