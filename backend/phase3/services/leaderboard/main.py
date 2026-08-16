"""
Hermes LinguaMind — Leaderboard Service
Port: 8014 | Phase 3 — Production Ready
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import time
from datetime import datetime, timedelta
from typing import Dict, List, Any
from uuid import UUID

from fastapi import FastAPI, Request
from pydantic import BaseModel, Field
import structlog
import uvicorn

from shared.models.common import HermesResponse, HealthStatus, LeaderboardRequest, LeaderboardResponse, LeaderboardScope
from shared.utils.helpers import generate_request_id

logger = structlog.get_logger("hermes.leaderboard")
app = FastAPI(title="Hermes Leaderboard", version="3.0.0")
_app_start_time = time.time()

_leaderboard_entries: List[Dict[str, Any]] = []

@app.get("/health", response_model=HealthStatus)
async def health_check():
    return HealthStatus(status="healthy", service="leaderboard", version="3.0.0",
                        timestamp=datetime.utcnow(), uptime_seconds=time.time() - _app_start_time)

@app.post("/v1/leaderboard", response_model=HermesResponse)
async def get_leaderboard(request: Request, req: LeaderboardRequest):
    request_id = getattr(request.state, "request_id", generate_request_id())

    # Filter entries
    entries = _leaderboard_entries
    if req.scope:
        entries = [e for e in entries if e["scope"] == req.scope.value]
    if req.period:
        entries = [e for e in entries if e["period"] == req.period]
    if req.language_pair:
        entries = [e for e in entries if e.get("language_pair") == req.language_pair]
    if req.country_code:
        entries = [e for e in entries if e.get("country_code") == req.country_code]

    # Sort by score descending
    entries.sort(key=lambda x: x["score"], reverse=True)

    # Assign ranks
    for i, entry in enumerate(entries):
        entry["rank"] = i + 1

    # Paginate
    start = (req.page - 1) * req.page_size
    paginated = entries[start:start + req.page_size]

    # Calculate period
    now = datetime.utcnow()
    if req.period == "weekly":
        period_start = now - timedelta(days=now.weekday())
        period_end = period_start + timedelta(days=6)
    elif req.period == "monthly":
        period_start = now.replace(day=1)
        period_end = (period_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    else:
        period_start = datetime.min
        period_end = now

    response = LeaderboardResponse(
        entries=paginated,
        user_rank=None,
        user_score=None,
        total_participants=len(entries),
        period_start=period_start,
        period_end=period_end,
    )

    return HermesResponse(success=True, data=response.model_dump(), request_id=request_id)

@app.post("/v1/submit-score", response_model=HermesResponse)
async def submit_score(request: Request, user_id: str, scope: str, score: int, language_pair: str = None, country_code: str = None):
    request_id = getattr(request.state, "request_id", generate_request_id())

    entry = {
        "user_id": user_id,
        "scope": scope,
        "period": "weekly",
        "score": score,
        "language_pair": language_pair,
        "country_code": country_code,
        "week_start": datetime.utcnow().strftime("%Y-%m-%d"),
        "updated_at": datetime.utcnow().isoformat(),
    }

    # Update existing or add new
    existing = next((e for e in _leaderboard_entries if e["user_id"] == user_id and e["scope"] == scope), None)
    if existing:
        existing["score"] = max(existing["score"], score)
        existing["updated_at"] = datetime.utcnow().isoformat()
    else:
        _leaderboard_entries.append(entry)

    logger.info("score_submitted", request_id=request_id, user_id=user_id, score=score)
    return HermesResponse(success=True, data={"status": "submitted", "score": score}, request_id=request_id)

@app.get("/v1/metrics")
async def get_metrics():
    return {"uptime_seconds": time.time() - _app_start_time, "total_entries": len(_leaderboard_entries)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8014, log_level="info")
