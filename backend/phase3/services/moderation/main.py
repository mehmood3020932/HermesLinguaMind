"""
Hermes LinguaMind — Moderation Service
Port: 8009 | Phase 3 — Production Ready
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import time
import re
from datetime import datetime
from typing import List, Dict, Any

from fastapi import FastAPI, Request
from pydantic import BaseModel, Field
import structlog
import uvicorn

from shared.models.common import HermesResponse, HealthStatus, ModerationRequest, ModerationResponse
from shared.utils.helpers import generate_request_id

logger = structlog.get_logger("hermes.moderation")
app = FastAPI(title="Hermes Moderation", version="3.0.0")
_app_start_time = time.time()

BLOCKED = {
    "romantic": [r"\b(i love you|you are cute|date me)\b", r"\b(sexy|hot)\b"],
    "harmful": [r"\b(kill|hurt|attack|violence)\b", r"\b(suicide|self.?harm)\b"],
    "inappropriate": [r"\b(drug|gambling)\b"],
    "spam": [r"\b(buy now|free money)\b", r"\b(www\.|http://)\b"],
}

DEFLECTIONS = {
    "romantic": "I'm here to help you learn languages! Let's focus on your studies.",
    "harmful": "I'm concerned. If you're in crisis, please reach out to a trusted person or helpline.",
    "inappropriate": "Let's keep our conversation focused on language learning.",
    "spam": "I only discuss language learning. How can I help you practice today?",
}

@app.get("/health", response_model=HealthStatus)
async def health_check():
    return HealthStatus(status="healthy", service="moderation", version="3.0.0",
                        timestamp=datetime.utcnow(), uptime_seconds=time.time() - _app_start_time)

@app.post("/v1/moderate", response_model=HermesResponse)
async def moderate(request: Request, req: ModerationRequest):
    request_id = getattr(request.state, "request_id", generate_request_id())
    content = req.content.lower()
    flags = []
    action = "allow"
    reason = None
    deflection = None

    for category, patterns in BLOCKED.items():
        for pattern in patterns:
            if re.search(pattern, content, re.IGNORECASE):
                flags.append(category)
                action = "block"
                reason = f"Flagged as {category}"
                deflection = DEFLECTIONS.get(category)
                break
        if flags:
            break

    if len(req.content) > 10000:
        flags.append("excessive_length")
        action = "warn"

    confidence = 0.85 if flags else 0.1
    response = ModerationResponse(is_safe=len(flags) == 0, flags=flags, confidence=round(confidence, 2),
                                   action=action, reason=reason)

    if flags:
        logger.warning("flagged", request_id=request_id, flags=flags)

    return HermesResponse(success=True, data={**response.model_dump(), "deflection": deflection}, request_id=request_id)

@app.get("/v1/metrics")
async def get_metrics():
    return {"uptime_seconds": time.time() - _app_start_time}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8009, log_level="info")
