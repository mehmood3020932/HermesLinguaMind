"""
Hermes LinguaMind — Memory Service
Port: 8008 | Phase 3 — Production

Real Postgres-backed conversation memory (was an in-process dict — every
restart used to wipe the user's entire relationship history with their AI
conversation partner).
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import time
from datetime import datetime
from uuid import uuid4

from fastapi import FastAPI, Request
from sqlalchemy import select, func, update

from shared.models.common import HermesResponse, HealthStatus, MemoryRequest, MemoryResponse, MemoryORM
from shared.utils.helpers import generate_request_id
from shared.database import get_db_session, db_healthy, init_db
import structlog
import uvicorn

logger = structlog.get_logger("hermes.memory")
app = FastAPI(title="Hermes Memory", version="3.1.0")


@app.on_event("startup")
async def _init_schema():
    """Idempotent: creates tables if another service hasn't already."""
    await init_db()
_app_start_time = time.time()

MAX_ACTIVE_MEMORIES_PER_USER = 100


@app.get("/health", response_model=HealthStatus)
async def health_check():
    is_db_healthy = await db_healthy()
    return HealthStatus(status="healthy" if is_db_healthy else "degraded", service="memory", version="3.1.0",
                        timestamp=datetime.utcnow(), uptime_seconds=time.time() - _app_start_time,
                        dependencies={"database": "connected" if is_db_healthy else "unreachable"})


@app.post("/v1/store", response_model=HermesResponse)
async def store_memory(request: Request, req: MemoryRequest):
    request_id = getattr(request.state, "request_id", generate_request_id())

    async with get_db_session() as session:
        memory = MemoryORM(
            id=uuid4(), user_id=req.user_id, memory_type=req.memory_type, content=req.content,
            importance_score=req.importance_score, context_tags=req.context_tags or [],
            summary=(req.content[:100] + "...") if len(req.content) > 100 else req.content,
            is_archived=False,
        )
        session.add(memory)
        await session.flush()

        # Keep only the most recent MAX_ACTIVE_MEMORIES_PER_USER un-archived;
        # older ones are archived (soft-deleted), not lost, matching the
        # is_archived flag the schema already provides for this.
        active_count = (await session.execute(
            select(func.count()).select_from(MemoryORM)
            .where(MemoryORM.user_id == req.user_id, MemoryORM.is_archived == False)  # noqa: E712
        )).scalar_one()

        if active_count > MAX_ACTIVE_MEMORIES_PER_USER:
            overflow = active_count - MAX_ACTIVE_MEMORIES_PER_USER
            to_archive = (await session.execute(
                select(MemoryORM.id).where(MemoryORM.user_id == req.user_id, MemoryORM.is_archived == False)  # noqa: E712
                .order_by(MemoryORM.created_at.asc()).limit(overflow)
            )).scalars().all()
            if to_archive:
                await session.execute(
                    update(MemoryORM).where(MemoryORM.id.in_(to_archive)).values(is_archived=True)
                )

        logger.info("memory_stored", request_id=request_id, user_id=str(req.user_id), memory_id=str(memory.id))
        return HermesResponse(success=True, data={"memory_id": str(memory.id)}, request_id=request_id)


@app.get("/v1/retrieve/{user_id}", response_model=HermesResponse)
async def retrieve(user_id: str, request: Request, memory_type: str = None, limit: int = 20):
    request_id = getattr(request.state, "request_id", generate_request_id())

    async with get_db_session() as session:
        stmt = select(MemoryORM).where(MemoryORM.user_id == user_id, MemoryORM.is_archived == False)  # noqa: E712
        if memory_type:
            stmt = stmt.where(MemoryORM.memory_type == memory_type)

        total_stmt = select(func.count()).select_from(stmt.subquery())
        total_count = (await session.execute(total_stmt)).scalar_one()

        rows = (await session.execute(
            stmt.order_by(MemoryORM.importance_score.desc(), MemoryORM.created_at.desc()).limit(limit)
        )).scalars().all()

        recent = [_memory_to_dict(m) for m in rows]
        summary = (" ".join(m["content"] for m in recent))[:200] + "..." if recent else ""
        response = MemoryResponse(memories=recent, summary=summary, relationship_depth=min(10, total_count // 10))
        return HermesResponse(success=True, data=response.model_dump(), request_id=request_id)


@app.get("/v1/metrics")
async def get_metrics():
    async with get_db_session() as session:
        total = (await session.execute(select(func.count()).select_from(MemoryORM))).scalar_one()
    return {"uptime_seconds": time.time() - _app_start_time, "total": total}


def _memory_to_dict(m: MemoryORM) -> dict:
    return {
        "id": str(m.id), "user_id": str(m.user_id), "memory_type": m.memory_type, "content": m.content,
        "importance_score": m.importance_score, "context_tags": m.context_tags or [], "summary": m.summary,
        "is_archived": m.is_archived, "created_at": m.created_at.isoformat() if m.created_at else None,
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8008, log_level="info")
