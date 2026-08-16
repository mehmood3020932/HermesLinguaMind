"""
Hermes LinguaMind — Live Conversation Service
Port: 8017 | Phase 3 — Production Ready
WebRTC streaming for call mode
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import time
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Set

import httpx
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import structlog
import uvicorn

from shared.models.common import HermesResponse, HealthStatus, LiveConversationRequest, LiveConversationResponse, ConversationMode
from shared.utils.helpers import generate_request_id

logger = structlog.get_logger("hermes.live")
app = FastAPI(title="Hermes Live Conversation", version="3.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
_app_start_time = time.time()

STT_SERVICE_URL = os.getenv("STT_SERVICE_URL", "http://stt:8003")
LLM_SERVICE_URL = os.getenv("LLM_SERVICE_URL", "http://llm:8001")
TTS_SERVICE_URL = os.getenv("TTS_SERVICE_URL", "http://tts:8002")
VISEME_SERVICE_URL = os.getenv("VISEME_SERVICE_URL", "http://viseme:8004")

# Active sessions
_active_sessions: Dict[str, Dict[str, Any]] = {}
_websocket_connections: Dict[str, WebSocket] = {}

@app.get("/health", response_model=HealthStatus)
async def health_check():
    return HealthStatus(status="healthy", service="live_conversation", version="3.0.0",
                        timestamp=datetime.utcnow(), uptime_seconds=time.time() - _app_start_time,
                        dependencies={"webrtc": "ready", "websocket": "ready"})

@app.post("/v1/start", response_model=HermesResponse)
async def start_conversation(request: Request, req: LiveConversationRequest):
    request_id = getattr(request.state, "request_id", generate_request_id())

    session_id = f"session_{str(req.user_id)}_{int(time.time())}"

    session = {
        "session_id": session_id,
        "user_id": str(req.user_id),
        "mode": req.mode.value,
        "language": req.language.value,
        "native_language": req.native_language.value if req.native_language else None,
        "topic": req.topic,
        "difficulty": req.difficulty.value if req.difficulty else "A1",
        "started_at": datetime.utcnow().isoformat(),
        "status": "active",
    }

    _active_sessions[session_id] = session

    # ICE servers for WebRTC
    ice_servers = [
        {"urls": "stun:stun.l.google.com:19302"},
    ]

    response = LiveConversationResponse(
        session_id=session_id,
        websocket_url=f"ws://localhost:8017/v1/ws/{session_id}",
        ice_servers=ice_servers,
        estimated_latency_ms=3500,  # Realistic for free-tier
        mode=req.mode,
    )

    logger.info("conversation_started", request_id=request_id, session_id=session_id, mode=req.mode.value)
    return HermesResponse(success=True, data=response.model_dump(), request_id=request_id)

@app.websocket("/v1/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    _websocket_connections[session_id] = websocket

    logger.info("websocket_connected", session_id=session_id)
    session = _active_sessions.get(session_id, {})
    language = session.get("language", "en")
    # None until we've heard the user speak/write at least once; then either
    # the client-declared value or an auto-detection from their own words —
    # this is what lets the AI companion explain the target language in
    # whatever language the user is actually talking in (Urdu, region-local
    # language, etc.) instead of assuming English.
    native_language = session.get("native_language")
    conversation_history: List[Dict[str, str]] = []

    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            while True:
                incoming = await websocket.receive_json()
                audio_b64 = incoming.get("audio_base64")

                if not audio_b64:
                    await websocket.send_json({
                        "type": "error", "session_id": session_id,
                        "timestamp": datetime.utcnow().isoformat(),
                        "message": "Expected JSON message with an 'audio_base64' field.",
                    })
                    continue

                try:
                    # 1) Real speech-to-text
                    stt_resp = await client.post(
                        f"{STT_SERVICE_URL}/v1/transcribe",
                        json={"audio_base64": audio_b64, "language": language,
                              "format": incoming.get("format", "webm"), "sample_rate": incoming.get("sample_rate", 48000)},
                    )
                    stt_resp.raise_for_status()
                    stt_data = stt_resp.json()
                    if not stt_data.get("success"):
                        raise RuntimeError(stt_data.get("error", "STT failed"))
                    user_text = stt_data["data"]["text"]

                    # 2) Real LLM conversational reply — teach `language`
                    # (the target) while explaining in `native_language`
                    # (auto-detected from the user's own words if not set).
                    llm_resp = await client.post(
                        f"{LLM_SERVICE_URL}/v1/conversation",
                        json={
                            "message": user_text,
                            "conversation_history": conversation_history[-10:],
                            "language": language,
                            "native_language": native_language,
                            "auto_detect_native_language": native_language is None,
                            "cefr_level": session.get("difficulty", "A1"),
                        },
                    )
                    llm_resp.raise_for_status()
                    llm_data = llm_resp.json()
                    if not llm_data.get("success"):
                        raise RuntimeError(llm_data.get("error", "LLM generation failed"))
                    reply_text = llm_data["data"]["response"]

                    # Lock in the detected native language for the rest of
                    # this session so it doesn't flip-flop turn to turn.
                    if native_language is None:
                        native_language = llm_data["data"].get("native_language_used", language)
                        session["native_language"] = native_language

                    conversation_history.append({"role": "user", "content": user_text})
                    conversation_history.append({"role": "assistant", "content": reply_text})

                    # 3) Real text-to-speech for the reply
                    tts_resp = await client.post(
                        f"{TTS_SERVICE_URL}/v1/synthesize",
                        json={"text": reply_text, "language": language},
                    )
                    tts_resp.raise_for_status()
                    tts_data = tts_resp.json()
                    reply_audio_base64 = None
                    viseme_timeline = None
                    if tts_data.get("success"):
                        reply_audio_base64 = tts_data["data"]["audio_base64"]
                        phoneme_timings = tts_data["data"].get("phoneme_timings") or []

                        # 4) Real viseme/lip-sync timeline from the actual phoneme timings
                        if phoneme_timings:
                            try:
                                viseme_resp = await client.post(
                                    f"{VISEME_SERVICE_URL}/v1/generate",
                                    json={"phoneme_timings": phoneme_timings, "language": language, "fps": 30},
                                )
                                viseme_resp.raise_for_status()
                                viseme_data = viseme_resp.json()
                                if viseme_data.get("success"):
                                    viseme_timeline = viseme_data["data"]["viseme_timeline"]
                            except Exception as viseme_err:
                                logger.warning("live_viseme_failed", session_id=session_id, error=str(viseme_err))
                    else:
                        logger.warning("live_tts_failed", session_id=session_id, error=tts_data.get("error"))

                    await websocket.send_json({
                        "type": "response",
                        "session_id": session_id,
                        "timestamp": datetime.utcnow().isoformat(),
                        "status": "processed",
                        "transcript": user_text,
                        "reply_text": reply_text,
                        "reply_audio_base64": reply_audio_base64,
                        "viseme_timeline": viseme_timeline,
                        "target_language": language,
                        "native_language": native_language,
                    })

                except Exception as pipeline_error:
                    logger.error("live_pipeline_failed", session_id=session_id, error=str(pipeline_error))
                    await websocket.send_json({
                        "type": "error", "session_id": session_id,
                        "timestamp": datetime.utcnow().isoformat(),
                        "message": f"Processing failed: {pipeline_error}",
                    })

    except WebSocketDisconnect:
        logger.info("websocket_disconnected", session_id=session_id)
        _websocket_connections.pop(session_id, None)
        if session_id in _active_sessions:
            _active_sessions[session_id]["status"] = "ended"
            _active_sessions[session_id]["ended_at"] = datetime.utcnow().isoformat()

@app.post("/v1/end/{session_id}", response_model=HermesResponse)
async def end_conversation(session_id: str, request: Request):
    request_id = getattr(request.state, "request_id", generate_request_id())

    if session_id in _active_sessions:
        _active_sessions[session_id]["status"] = "ended"
        _active_sessions[session_id]["ended_at"] = datetime.utcnow().isoformat()

        # Close websocket if open
        if session_id in _websocket_connections:
            try:
                await _websocket_connections[session_id].close()
            except Exception:
                pass
            _websocket_connections.pop(session_id, None)

    logger.info("conversation_ended", request_id=request_id, session_id=session_id)
    return HermesResponse(success=True, data={"status": "ended", "session_id": session_id}, request_id=request_id)

@app.get("/v1/sessions", response_model=HermesResponse)
async def list_sessions(request: Request):
    request_id = getattr(request.state, "request_id", generate_request_id())
    active = [s for s in _active_sessions.values() if s["status"] == "active"]
    return HermesResponse(success=True, data={"active_sessions": active, "total_active": len(active)}, request_id=request_id)

@app.get("/v1/benchmark")
async def get_benchmark():
    return {
        "mode": "voice",
        "estimated_latency_ms": 3500,
        "breakdown": {
            "stt_processing": 800,
            "llm_response": 1500,
            "tts_synthesis": 1000,
            "network_overhead": 200,
        },
        "target_latency_ms": 2000,
        "optimization_notes": "Latency can be reduced with GPU hosting and model quantization.",
    }

@app.get("/v1/metrics")
async def get_metrics():
    active = sum(1 for s in _active_sessions.values() if s["status"] == "active")
    return {"uptime_seconds": time.time() - _app_start_time, "active_sessions": active,
            "total_sessions": len(_active_sessions), "websocket_connections": len(_websocket_connections)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8017, log_level="info")
