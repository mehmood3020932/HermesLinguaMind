"""
Hermes LinguaMind — Social Exchange Service
Port: 8015 | Phase 3 — Production Ready
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import time
from datetime import datetime, timedelta
from typing import Dict, List, Any
from uuid import UUID, uuid4

from fastapi import FastAPI, Request
from pydantic import BaseModel, Field
import structlog
import uvicorn

from shared.models.common import HermesResponse, HealthStatus, SocialMatchRequest, SocialMatchResponse, SocialStatus, LanguageCode
from shared.utils.helpers import generate_request_id

logger = structlog.get_logger("hermes.social")
app = FastAPI(title="Hermes Social Exchange", version="3.0.0")
_app_start_time = time.time()

_social_profiles: Dict[str, Dict[str, Any]] = {}
_matches: List[Dict[str, Any]] = []
_reports: List[Dict[str, Any]] = []
MIN_AGE = 13

@app.get("/health", response_model=HealthStatus)
async def health_check():
    return HealthStatus(status="healthy", service="social_exchange", version="3.0.0",
                        timestamp=datetime.utcnow(), uptime_seconds=time.time() - _app_start_time)

@app.post("/v1/match", response_model=HermesResponse)
async def find_matches(request: Request, req: SocialMatchRequest):
    request_id = getattr(request.state, "request_id", generate_request_id())
    user_id = str(req.user_id)

    # Get all available profiles
    available = []
    for uid, profile in _social_profiles.items():
        if uid == user_id:
            continue
        if not profile.get("available_for_exchange", False):
            continue
        if profile.get("native_language") != req.target_language.value:
            continue
        if profile.get("learning_language") != req.native_language.value:
            continue

        # Age check
        dob = profile.get("date_of_birth")
        if dob:
            from datetime import date
            birth = datetime.strptime(dob, "%Y-%m-%d").date() if isinstance(dob, str) else dob
            age = (date.today() - birth).days // 365
            if age < MIN_AGE:
                continue

        # Interest matching
        score = 0
        if req.interests:
            common = set(req.interests) & set(profile.get("interests", []))
            score += len(common) * 10

        available.append({"user_id": uid, "score": score, **profile})

    # Sort by score
    available.sort(key=lambda x: x["score"], reverse=True)

    response = SocialMatchResponse(matches=available[:10], match_count=len(available))
    return HermesResponse(success=True, data=response.model_dump(), request_id=request_id)

@app.post("/v1/profile", response_model=HermesResponse)
async def update_profile(request: Request, user_id: str, profile: dict):
    request_id = getattr(request.state, "request_id", generate_request_id())
    _social_profiles[user_id] = {**_social_profiles.get(user_id, {}), **profile, "updated_at": datetime.utcnow().isoformat()}
    logger.info("profile_updated", request_id=request_id, user_id=user_id)
    return HermesResponse(success=True, data={"status": "updated"}, request_id=request_id)

@app.get("/v1/profile/{user_id}", response_model=HermesResponse)
async def get_profile(user_id: str, request: Request):
    """Fetch a stored social profile. Added to complement the existing
    POST /v1/profile (update) — the mobile app needs a way to read a
    profile back, which wasn't exposed before."""
    request_id = getattr(request.state, "request_id", generate_request_id())
    profile = _social_profiles.get(user_id)
    if profile is None:
        # Return an empty-but-valid profile rather than a 404 so a brand
        # new user (no social activity yet) doesn't break the mobile UI.
        profile = {
            "user_id": user_id,
            "username": user_id,
            "display_name": user_id,
            "xp": 0,
            "streak_days": 0,
            "languages": [],
            "is_online": False,
        }
    return HermesResponse(success=True, data=profile, request_id=request_id)

@app.post("/v1/report", response_model=HermesResponse)
async def report_user(request: Request, reporter_id: str, reported_id: str, reason: str):
    request_id = getattr(request.state, "request_id", generate_request_id())

    # Check cooldown
    recent_reports = [r for r in _reports if r["reporter_id"] == reporter_id
                      and r["created_at"] > (datetime.utcnow() - timedelta(hours=24)).isoformat()]
    if len(recent_reports) >= 3:
        return HermesResponse(success=False, error="Report cooldown active", error_code="REPORT_COOLDOWN", request_id=request_id)

    report = {"id": str(uuid4()), "reporter_id": reporter_id, "reported_id": reported_id,
              "reason": reason, "status": "pending", "created_at": datetime.utcnow().isoformat()}
    _reports.append(report)

    # Update reported user's profile
    if reported_id in _social_profiles:
        _social_profiles[reported_id]["report_count"] = _social_profiles[reported_id].get("report_count", 0) + 1

    logger.warning("user_reported", request_id=request_id, reporter=reporter_id, reported=reported_id, reason=reason)
    return HermesResponse(success=True, data={"status": "reported", "report_id": report["id"]}, request_id=request_id)

@app.get("/v1/metrics")
async def get_metrics():
    return {"uptime_seconds": time.time() - _app_start_time, "profiles": len(_social_profiles),
            "matches": len(_matches), "reports": len(_reports)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8015, log_level="info")
