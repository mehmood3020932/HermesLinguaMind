"""
Hermes LinguaMind — Anti-Fraud Service
Port: 8016 | Phase 3 — Production Ready
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import time
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any

from fastapi import FastAPI, Request
from pydantic import BaseModel, Field
import structlog
import uvicorn

from shared.models.common import HermesResponse, HealthStatus, FraudCheckRequest, FraudCheckResponse, FraudRiskLevel
from shared.utils.helpers import generate_request_id

logger = structlog.get_logger("hermes.antifraud")
app = FastAPI(title="Hermes Anti-Fraud", version="3.0.0")
_app_start_time = time.time()

# Fraud tracking
_user_transactions: Dict[str, List[Dict[str, Any]]] = {}
_ip_accounts: Dict[str, List[str]] = {}
_fraud_alerts: List[Dict[str, Any]] = []

RATE_WINDOW_MINUTES = 60
MAX_EARNINGS_PER_WINDOW = 200
MULTI_ACCOUNT_IP_THRESHOLD = 5

@app.get("/health", response_model=HealthStatus)
async def health_check():
    return HealthStatus(status="healthy", service="anti_fraud", version="3.0.0",
                        timestamp=datetime.utcnow(), uptime_seconds=time.time() - _app_start_time)

@app.post("/v1/check", response_model=HermesResponse)
async def check_fraud(request: Request, req: FraudCheckRequest):
    request_id = getattr(request.state, "request_id", generate_request_id())
    user_id = str(req.user_id)

    triggered_rules = []
    risk_score = 0.0

    # Track transaction
    if user_id not in _user_transactions:
        _user_transactions[user_id] = []

    tx_record = {"amount": req.amount, "type": req.transaction_type,
                 "timestamp": datetime.utcnow().isoformat(), "ip": req.ip_address}
    _user_transactions[user_id].append(tx_record)

    # Clean old transactions
    cutoff = (datetime.utcnow() - timedelta(minutes=RATE_WINDOW_MINUTES)).isoformat()
    _user_transactions[user_id] = [t for t in _user_transactions[user_id] if t["timestamp"] > cutoff]

    # Rule 1: Rate of earning
    if req.amount > 0:
        recent_earnings = sum(t["amount"] for t in _user_transactions[user_id] if t["amount"] > 0)
        if recent_earnings > MAX_EARNINGS_PER_WINDOW:
            triggered_rules.append("excessive_earning_rate")
            risk_score += 0.4

    # Rule 2: Multi-account from same IP
    if req.ip_address:
        if req.ip_address not in _ip_accounts:
            _ip_accounts[req.ip_address] = []
        if user_id not in _ip_accounts[req.ip_address]:
            _ip_accounts[req.ip_address].append(user_id)

        if len(_ip_accounts[req.ip_address]) > MULTI_ACCOUNT_IP_THRESHOLD:
            triggered_rules.append("multi_account_farming")
            risk_score += 0.5

    # Rule 3: Unusual transaction pattern
    user_txs = _user_transactions[user_id]
    if len(user_txs) > 5:
        amounts = [t["amount"] for t in user_txs]
        try:
            mean = statistics.mean(amounts)
            stdev = statistics.stdev(amounts) if len(amounts) > 1 else 0
            if req.amount > mean + 3 * stdev:
                triggered_rules.append("unusual_amount")
                risk_score += 0.3
        except statistics.StatisticsError:
            pass

    # Determine risk level
    if risk_score >= 0.7:
        risk_level = FraudRiskLevel.CRITICAL
        action = "block_and_review"
    elif risk_score >= 0.4:
        risk_level = FraudRiskLevel.HIGH
        action = "review_required"
    elif risk_score >= 0.2:
        risk_level = FraudRiskLevel.MEDIUM
        action = "monitor"
    else:
        risk_level = FraudRiskLevel.LOW
        action = "allow"

    # Create alert if medium or higher
    if risk_level in [FraudRiskLevel.MEDIUM, FraudRiskLevel.HIGH, FraudRiskLevel.CRITICAL]:
        alert = {"id": str(len(_fraud_alerts) + 1), "user_id": user_id, "alert_type": "auto_detection",
                 "risk_level": risk_level.value, "triggered_rules": triggered_rules,
                 "details": {"risk_score": risk_score, "ip": req.ip_address},
                 "review_status": "pending", "created_at": datetime.utcnow().isoformat()}
        _fraud_alerts.append(alert)
        logger.warning("fraud_alert", request_id=request_id, user_id=user_id, risk_level=risk_level.value,
                       rules=triggered_rules)

    response = FraudCheckResponse(
        is_fraudulent=risk_level in [FraudRiskLevel.HIGH, FraudRiskLevel.CRITICAL],
        risk_level=risk_level,
        risk_score=round(risk_score, 2),
        triggered_rules=triggered_rules,
        recommended_action=action,
        review_required=risk_level in [FraudRiskLevel.MEDIUM, FraudRiskLevel.HIGH, FraudRiskLevel.CRITICAL],
    )

    return HermesResponse(success=True, data=response.model_dump(), request_id=request_id)

@app.get("/v1/alerts", response_model=HermesResponse)
async def get_alerts(request: Request, status: str = None, risk_level: str = None):
    request_id = getattr(request.state, "request_id", generate_request_id())
    alerts = _fraud_alerts
    if status:
        alerts = [a for a in alerts if a["review_status"] == status]
    if risk_level:
        alerts = [a for a in alerts if a["risk_level"] == risk_level]
    return HermesResponse(success=True, data={"alerts": alerts, "total": len(alerts)}, request_id=request_id)

@app.get("/v1/metrics")
async def get_metrics():
    return {"uptime_seconds": time.time() - _app_start_time, "alerts": len(_fraud_alerts),
            "users_monitored": len(_user_transactions)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8016, log_level="info")
