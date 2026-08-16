"""
Hermes LinguaMind — STT Service
Port: 8003 | Phase 3 — Production

Real speech-to-text pipeline:
  1. Primary: self-hosted faster-whisper (CPU/GPU, offline, no per-request cost)
  2. Fallback: OpenAI Whisper API (cloud, requires OPENAI_API_KEY)

No mock/simulated output — if neither engine is available, the endpoint
returns a real 503-style error instead of fabricating a transcript.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import time
import base64
import tempfile
from typing import Optional
from datetime import datetime

import httpx
from fastapi import FastAPI, Request
import structlog
import uvicorn

from shared.models.common import HermesResponse, HealthStatus, STTRequest, STTResponse
from shared.utils.helpers import generate_request_id

logger = structlog.get_logger("hermes.stt")

app = FastAPI(title="Hermes STT Service", description="Speech-to-Text (faster-whisper + OpenAI fallback)", version="3.1.0")
_app_start_time = time.time()

WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "base")
WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "cpu")
WHISPER_COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "int8")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_STT_MODEL = os.getenv("OPENAI_STT_MODEL", "whisper-1")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")


class LocalWhisperEngine:
    """Self-hosted STT via faster-whisper. Loaded lazily so the service still
    boots (and reports honestly) even if the model files aren't present yet."""

    def __init__(self):
        self.model = None
        self.load_error: Optional[str] = None
        self._load()

    def _load(self):
        try:
            from faster_whisper import WhisperModel
            self.model = WhisperModel(WHISPER_MODEL_SIZE, device=WHISPER_DEVICE, compute_type=WHISPER_COMPUTE_TYPE)
            logger.info("faster_whisper_loaded", model=WHISPER_MODEL_SIZE, device=WHISPER_DEVICE)
        except Exception as e:
            self.load_error = str(e)
            logger.warning("faster_whisper_unavailable", error=str(e))
            self.model = None

    @property
    def available(self) -> bool:
        return self.model is not None

    def transcribe(self, wav_path: str, language: Optional[str]) -> dict:
        segments_iter, info = self.model.transcribe(wav_path, language=language, task="transcribe")
        segments = []
        text_parts = []
        for seg in segments_iter:
            text_parts.append(seg.text)
            segments.append({
                "text": seg.text.strip(),
                "start": round(seg.start, 2),
                "end": round(seg.end, 2),
                "confidence": round(float(getattr(seg, "avg_logprob", -0.5)) + 1.0, 2) if hasattr(seg, "avg_logprob") else 0.9,
            })
        return {
            "text": " ".join(t.strip() for t in text_parts).strip(),
            "language_detected": info.language,
            "confidence": round(float(getattr(info, "language_probability", 0.9)), 2),
            "segments": segments,
        }


class OpenAIWhisperFallback:
    """Cloud fallback via OpenAI's real /audio/transcriptions endpoint."""

    def __init__(self):
        self.api_key = OPENAI_API_KEY

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    async def transcribe(self, wav_bytes: bytes, language: Optional[str]) -> dict:
        async with httpx.AsyncClient(timeout=60.0) as client:
            files = {"file": ("audio.wav", wav_bytes, "audio/wav")}
            data = {"model": OPENAI_STT_MODEL, "response_format": "verbose_json"}
            if language:
                data["language"] = language
            response = await client.post(
                f"{OPENAI_BASE_URL}/audio/transcriptions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                files=files,
                data=data,
            )
            response.raise_for_status()
            result = response.json()
            segments = [
                {
                    "text": s.get("text", "").strip(),
                    "start": round(s.get("start", 0.0), 2),
                    "end": round(s.get("end", 0.0), 2),
                    "confidence": round(1.0 - min(abs(s.get("no_speech_prob", 0.1)), 1.0), 2),
                }
                for s in result.get("segments", [])
            ]
            return {
                "text": result.get("text", "").strip(),
                "language_detected": result.get("language", language or "unknown"),
                "confidence": 0.95,
                "segments": segments,
            }


local_engine = LocalWhisperEngine()
cloud_fallback = OpenAIWhisperFallback()


@app.get("/health", response_model=HealthStatus)
async def health_check():
    uptime = time.time() - _app_start_time
    deps = {
        "faster_whisper_local": "ready" if local_engine.available else "unavailable",
        "openai_whisper_fallback": "configured" if cloud_fallback.available else "not_configured",
    }
    status = "healthy" if (local_engine.available or cloud_fallback.available) else "degraded"
    return HealthStatus(status=status, service="stt", version="3.1.0",
                         timestamp=datetime.utcnow(), uptime_seconds=uptime,
                         dependencies=deps)


@app.post("/v1/transcribe", response_model=HermesResponse)
async def transcribe(request: Request, stt_request: STTRequest):
    request_id = getattr(request.state, "request_id", generate_request_id())
    start_time = time.time()

    try:
        audio_bytes = base64.b64decode(stt_request.audio_base64)
    except Exception as e:
        return HermesResponse(success=False, error=f"Invalid base64 audio: {e}",
                               error_code="INVALID_AUDIO", request_id=request_id)

    language = stt_request.language.value if stt_request.language else None
    result = None
    engine_used = None
    tmp_path = None

    # 1) Try self-hosted engine first (free, no external dependency)
    if local_engine.available:
        try:
            with tempfile.NamedTemporaryFile(suffix=f".{stt_request.format or 'wav'}", delete=False) as tmp:
                tmp.write(audio_bytes)
                tmp_path = tmp.name
            result = local_engine.transcribe(tmp_path, language)
            engine_used = "faster-whisper-local"
        except Exception as e:
            logger.warning("local_stt_failed", error=str(e), request_id=request_id)
        finally:
            if tmp_path:
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass

    # 2) Fallback to OpenAI Whisper API
    if result is None and cloud_fallback.available:
        try:
            result = await cloud_fallback.transcribe(audio_bytes, language)
            engine_used = "openai-whisper-api"
        except Exception as e:
            logger.error("openai_stt_failed", error=str(e), request_id=request_id)

    if result is None:
        return HermesResponse(
            success=False,
            error="No STT engine available: local faster-whisper model failed to load and no OPENAI_API_KEY fallback is configured.",
            error_code="STT_UNAVAILABLE",
            request_id=request_id,
        )

    processing_time = (time.time() - start_time) * 1000
    stt_response = STTResponse(
        text=result["text"],
        confidence=result["confidence"],
        language_detected=result["language_detected"],
        segments=result["segments"],
        processing_time_ms=round(processing_time, 2),
    )

    logger.info("stt_transcription_complete", request_id=request_id, engine=engine_used,
                language=stt_response.language_detected, confidence=stt_response.confidence,
                processing_time_ms=processing_time)

    payload = stt_response.model_dump()
    payload["engine_used"] = engine_used
    return HermesResponse(success=True, data=payload, request_id=request_id)


@app.get("/v1/models", response_model=HermesResponse)
async def list_models():
    return HermesResponse(success=True, data={
        "local_model_loaded": WHISPER_MODEL_SIZE if local_engine.available else None,
        "local_available": local_engine.available,
        "local_load_error": local_engine.load_error,
        "cloud_fallback_available": cloud_fallback.available,
        "supported_languages": ["en", "es", "fr", "de", "it", "pt", "ja", "ko", "zh", "ar", "hi", "ru"],
    })


@app.get("/v1/metrics")
async def get_metrics():
    return {
        "uptime_seconds": time.time() - _app_start_time,
        "local_engine_ready": local_engine.available,
        "cloud_fallback_configured": cloud_fallback.available,
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003, log_level="info")
