"""
Hermes LinguaMind — Personalization Service
Port: 8012 | Phase 3 — Production Ready
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import time
from datetime import datetime
from typing import Dict, List, Any

from fastapi import FastAPI, Request
from pydantic import BaseModel, Field
import structlog
import uvicorn

from shared.models.common import HermesResponse, HealthStatus, PersonalizationRequest, PersonalizationResponse
from shared.utils.helpers import generate_request_id

logger = structlog.get_logger("hermes.personalization")
app = FastAPI(title="Hermes Personalization", version="3.0.0")
_app_start_time = time.time()

_user_profiles: Dict[str, Dict[str, Any]] = {}

@app.get("/health", response_model=HealthStatus)
async def health_check():
    return HealthStatus(status="healthy", service="personalization", version="3.0.0",
                        timestamp=datetime.utcnow(), uptime_seconds=time.time() - _app_start_time)

@app.post("/v1/analyze", response_model=HermesResponse)
async def analyze_user(request: Request, req: PersonalizationRequest):
    request_id = getattr(request.state, "request_id", generate_request_id())
    user_id = str(req.user_id)

    # Simple learning style inference based on interaction patterns
    sessions = req.learning_sessions or []
    history = req.interaction_history or []

    # Determine learning style
    visual_count = sum(1 for h in history if h.get("type") in ["image", "video", "diagram"])
    auditory_count = sum(1 for h in history if h.get("type") in ["audio", "listening"])
    kinesthetic_count = sum(1 for h in history if h.get("type") in ["speaking", "writing", "interactive"])
    total = visual_count + auditory_count + kinesthetic_count

    if total == 0:
        learning_style = "balanced"
    else:
        scores = {"visual": visual_count / total, "auditory": auditory_count / total, "kinesthetic": kinesthetic_count / total}
        learning_style = max(scores, key=scores.get)

    # Extract interest tags
    interest_tags = []
    for h in history:
        tags = h.get("tags", [])
        interest_tags.extend(tags)
    interest_tags = list(set(interest_tags))[:10]  # Top 10 unique tags

    # Calculate difficulty preference
    avg_score = sum(s.get("score", 0) for s in sessions) / len(sessions) if sessions else 50
    difficulty_pref = avg_score / 100  # 0.0 to 1.0

    # Determine pace — compute avg_duration unconditionally (previously
    # this only existed inside the `len(sessions) > 5` branch below, but
    # was referenced unconditionally in engagement_patterns further down,
    # crashing every request with 1-5 sessions — the common case for a
    # newer user — with an UnboundLocalError -> 500).
    avg_duration = sum(s.get("duration_minutes", 0) for s in sessions) / len(sessions) if sessions else 0
    if len(sessions) > 5:
        pace = "fast" if avg_duration < 10 else "moderate" if avg_duration < 25 else "slow"
    else:
        pace = "moderate"

    response = PersonalizationResponse(
        learning_style=learning_style,
        interest_tags=interest_tags,
        difficulty_preference=round(difficulty_pref, 2),
        recommended_pace=pace,
        engagement_patterns={"avg_session_duration": avg_duration if sessions else 0,
                             "sessions_per_week": len(sessions) / 7 if sessions else 0},
    )

    _user_profiles[user_id] = response.model_dump()

    logger.info("personalization_analyzed", request_id=request_id, user_id=user_id, style=learning_style)
    return HermesResponse(success=True, data=response.model_dump(), request_id=request_id)

@app.get("/v1/profile/{user_id}", response_model=HermesResponse)
async def get_profile(user_id: str, request: Request):
    request_id = getattr(request.state, "request_id", generate_request_id())
    profile = _user_profiles.get(user_id, {"learning_style": "balanced", "interest_tags": [],
                                            "difficulty_preference": 0.5, "recommended_pace": "moderate",
                                            "engagement_patterns": {}})
    return HermesResponse(success=True, data=profile, request_id=request_id)

@app.get("/v1/metrics")
async def get_metrics():
    return {"uptime_seconds": time.time() - _app_start_time, "profiles_analyzed": len(_user_profiles)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8012, log_level="info")
