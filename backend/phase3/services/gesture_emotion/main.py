"""
Hermes LinguaMind — Gesture/Emotion Service
Port: 8013 | Phase 3 — Production Ready
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import time
from datetime import datetime
from typing import List, Dict, Any

from fastapi import FastAPI, Request
from pydantic import BaseModel, Field
import structlog
import uvicorn

from shared.models.common import HermesResponse, HealthStatus, GestureRequest, GestureResponse, GestureType, EmotionTag
from shared.utils.helpers import generate_request_id

logger = structlog.get_logger("hermes.gesture")
app = FastAPI(title="Hermes Gesture/Emotion", version="3.0.0")
_app_start_time = time.time()

# Context-to-gesture mapping
CONTEXT_GESTURES = {
    "greeting": GestureType.WAVE,
    "farewell": GestureType.WAVE,
    "question": GestureType.THINK,
    "correction": GestureType.CORRECT,
    "praise": GestureType.CELEBRATE,
    "encouragement": GestureType.ENCOURAGE,
    "listening": GestureType.LISTEN,
    "speaking": GestureType.SPEAK,
    "agreement": GestureType.NOD,
    "disagreement": GestureType.SHAKE_HEAD,
    "surprise": GestureType.SURPRISED,
}

@app.get("/health", response_model=HealthStatus)
async def health_check():
    return HealthStatus(status="healthy", service="gesture_emotion", version="3.0.0",
                        timestamp=datetime.utcnow(), uptime_seconds=time.time() - _app_start_time)

@app.post("/v1/gesture", response_model=HermesResponse)
async def get_gesture(request: Request, req: GestureRequest):
    request_id = getattr(request.state, "request_id", generate_request_id())

    text_lower = req.text.lower()
    context_lower = req.context.lower()

    # Determine gesture based on context
    gesture = GestureType.IDLE
    emotion = req.current_emotion
    intensity = 0.5

    for ctx, g in CONTEXT_GESTURES.items():
        if ctx in context_lower or ctx in text_lower:
            gesture = g
            break

    # Adjust emotion based on content sentiment
    positive_words = ["good", "great", "excellent", "perfect", "correct", "well done", "amazing"]
    negative_words = ["wrong", "incorrect", "mistake", "error", "bad", "try again"]

    if any(w in text_lower for w in positive_words):
        emotion = EmotionTag.HAPPY
        intensity = 0.8
        if gesture == GestureType.IDLE:
            gesture = GestureType.CELEBRATE
    elif any(w in text_lower for w in negative_words):
        emotion = EmotionTag.CORRECTIVE
        intensity = 0.6
        if gesture == GestureType.IDLE:
            gesture = GestureType.ENCOURAGE

    # Adjust duration based on gesture complexity
    duration_map = {
        GestureType.IDLE: 1000, GestureType.WAVE: 1500, GestureType.POINT: 800,
        GestureType.THINK: 2000, GestureType.CELEBRATE: 2500, GestureType.ENCOURAGE: 1800,
        GestureType.CORRECT: 1200, GestureType.LISTEN: 3000, GestureType.SPEAK: 2000,
        GestureType.NOD: 800, GestureType.SHAKE_HEAD: 1000, GestureType.RAISE_EYEBROW: 600,
        GestureType.SMILE: 1500, GestureType.SURPRISED: 1200,
    }

    response = GestureResponse(
        gesture=gesture,
        emotion=emotion,
        intensity=round(intensity, 2),
        duration_ms=duration_map.get(gesture, 1000),
        transition_smoothness=0.85,
    )

    logger.info("gesture_selected", request_id=request_id, gesture=gesture.value, emotion=emotion.value)
    return HermesResponse(success=True, data=response.model_dump(), request_id=request_id)

@app.get("/v1/gestures", response_model=HermesResponse)
async def list_gestures():
    return HermesResponse(success=True, data={"gestures": [g.value for g in GestureType],
                                              "emotions": [e.value for e in EmotionTag]})

@app.get("/v1/metrics")
async def get_metrics():
    return {"uptime_seconds": time.time() - _app_start_time}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8013, log_level="info")
