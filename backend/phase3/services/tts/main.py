"""
Hermes LinguaMind — TTS Service
Port: 8002 | Phase 3 — Production

Real text-to-speech pipeline:
  1. Primary: self-hosted Piper TTS (offline, ONNX voice models, no per-request cost)
  2. Fallback: OpenAI TTS API (cloud, requires OPENAI_API_KEY)

Phoneme/viseme timing is derived from the actual audio duration and word
boundaries of the synthesized speech — not fabricated ahead of synthesis.
No mock/simulated audio — if neither engine is available, the endpoint
returns a real error instead of a sine-wave placeholder.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import io
import time
import base64
import wave
import subprocess
import tempfile
from typing import List, Dict, Any, Optional
from datetime import datetime

import httpx
from fastapi import FastAPI, Request
import structlog
import uvicorn

from shared.models.common import HermesResponse, HealthStatus, TTSRequest, TTSResponse, EmotionTag
from shared.utils.helpers import generate_request_id

logger = structlog.get_logger("hermes.tts")

app = FastAPI(title="Hermes TTS Service", description="Text-to-Speech (Piper local + OpenAI fallback)", version="3.1.0")
_app_start_time = time.time()

PIPER_VOICES_DIR = os.getenv("PIPER_VOICES_DIR", "/app/voices")
PIPER_VOICE_MAP = {
    "en": os.getenv("PIPER_VOICE_EN", "en_US-amy-medium"),
    "es": os.getenv("PIPER_VOICE_ES", "es_ES-davefx-medium"),
    "fr": os.getenv("PIPER_VOICE_FR", "fr_FR-siwis-medium"),
    "de": os.getenv("PIPER_VOICE_DE", "de_DE-thorsten-medium"),
}
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_TTS_MODEL = os.getenv("OPENAI_TTS_MODEL", "tts-1")
OPENAI_TTS_VOICE = os.getenv("OPENAI_TTS_VOICE", "alloy")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

EMOTION_SPEED = {
    EmotionTag.NEUTRAL: 1.0, EmotionTag.HAPPY: 1.1, EmotionTag.SAD: 0.85,
    EmotionTag.EXCITED: 1.2, EmotionTag.CALM: 0.9, EmotionTag.ENCOURAGING: 1.05,
    EmotionTag.CORRECTIVE: 0.95, EmotionTag.CELEBRATORY: 1.15,
}


def _wav_duration_seconds(wav_bytes: bytes) -> float:
    with wave.open(io.BytesIO(wav_bytes), "rb") as w:
        return w.getnframes() / float(w.getframerate())


def _wav_sample_rate(wav_bytes: bytes) -> int:
    with wave.open(io.BytesIO(wav_bytes), "rb") as w:
        return w.getframerate()


def _estimate_word_timings(text: str, duration_seconds: float) -> List[Dict[str, Any]]:
    """Even distribution across real measured audio duration (word-level).
    Used only as a fallback if G2P phoneme conversion isn't available."""
    words = text.split()
    if not words:
        return []
    per_word = duration_seconds / len(words)
    timings = []
    t = 0.0
    for w in words:
        timings.append({"word": w, "start": round(t, 2), "end": round(t + per_word, 2)})
        t += per_word
    return timings


class G2PEngine:
    """Real grapheme-to-phoneme conversion (English) via g2p_en, producing
    ARPAbet phonemes. Used to build a genuine phoneme-level timeline (with
    'viseme' = lowercased ARPAbet code, matching the viseme service's
    VISEME_INTENSITY table) instead of guessing word boundaries only."""

    def __init__(self):
        self.g2p = None
        try:
            from g2p_en import G2p
            self.g2p = G2p()
        except Exception as e:
            logger.warning("g2p_unavailable", error=str(e))

    @property
    def available(self) -> bool:
        return self.g2p is not None

    def phoneme_timeline(self, text: str, duration_seconds: float) -> List[Dict[str, Any]]:
        """Distribute real measured audio duration proportionally across
        the actual phoneme sequence of the synthesized text (equal-weight
        within a word; true forced alignment would weight by phoneme
        duration statistics, which is a further optional upgrade)."""
        words = text.split()
        if not words:
            return []
        word_phonemes = []
        total_phonemes = 0
        for w in words:
            raw = self.g2p(w)
            phones = [p.lower().rstrip("012") for p in raw if p.strip() and p not in (" ", ",", ".", "!", "?")]
            phones = [p for p in phones if p.isalpha()]
            if not phones:
                phones = ["sil"]
            word_phonemes.append(phones)
            total_phonemes += len(phones)

        if total_phonemes == 0:
            return []

        per_phoneme = duration_seconds / total_phonemes
        timeline = []
        t = 0.0
        for phones in word_phonemes:
            for p in phones:
                timeline.append({"viseme": p, "start_time": round(t, 3), "end_time": round(t + per_phoneme, 3)})
                t += per_phoneme
        return timeline


g2p_engine = G2PEngine()


class PiperEngine:
    """Self-hosted TTS via the `piper` CLI/binary and ONNX voice models."""

    def __init__(self):
        self.available_voices: Dict[str, str] = {}
        self._probe()

    def _probe(self):
        for lang, voice in PIPER_VOICE_MAP.items():
            onnx_path = os.path.join(PIPER_VOICES_DIR, f"{voice}.onnx")
            if os.path.exists(onnx_path):
                self.available_voices[lang] = onnx_path

    @property
    def available(self) -> bool:
        try:
            subprocess.run(["piper", "--help"], capture_output=True, timeout=5)
            return True
        except Exception:
            return False

    def synthesize(self, text: str, language: str) -> bytes:
        voice_path = self.available_voices.get(language) or self.available_voices.get("en")
        if not voice_path:
            raise RuntimeError(f"No Piper voice model found for '{language}' in {PIPER_VOICES_DIR}")
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            out_path = tmp.name
        try:
            proc = subprocess.run(
                ["piper", "--model", voice_path, "--output_file", out_path],
                input=text.encode("utf-8"), capture_output=True, timeout=30,
            )
            if proc.returncode != 0:
                raise RuntimeError(f"piper exited {proc.returncode}: {proc.stderr.decode(errors='ignore')}")
            with open(out_path, "rb") as f:
                return f.read()
        finally:
            try:
                os.unlink(out_path)
            except Exception:
                pass


class OpenAITTSFallback:
    """Cloud fallback via OpenAI's real /audio/speech endpoint."""

    def __init__(self):
        self.api_key = OPENAI_API_KEY

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    async def synthesize(self, text: str, speed: float) -> bytes:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{OPENAI_BASE_URL}/audio/speech",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": OPENAI_TTS_MODEL,
                    "voice": OPENAI_TTS_VOICE,
                    "input": text,
                    "response_format": "wav",
                    "speed": max(0.25, min(4.0, speed)),
                },
            )
            response.raise_for_status()
            return response.content


piper_engine = PiperEngine()
cloud_fallback = OpenAITTSFallback()


@app.get("/health", response_model=HealthStatus)
async def health_check():
    uptime = time.time() - _app_start_time
    piper_ok = piper_engine.available and bool(piper_engine.available_voices)
    deps = {
        "piper_local": "ready" if piper_ok else "unavailable",
        "openai_tts_fallback": "configured" if cloud_fallback.available else "not_configured",
    }
    status = "healthy" if (piper_ok or cloud_fallback.available) else "degraded"
    return HealthStatus(status=status, service="tts", version="3.1.0",
                         timestamp=datetime.utcnow(), uptime_seconds=uptime,
                         dependencies=deps)


@app.post("/v1/synthesize", response_model=HermesResponse)
async def synthesize(request: Request, tts_request: TTSRequest):
    request_id = getattr(request.state, "request_id", generate_request_id())

    if len(tts_request.text) > 5000:
        return HermesResponse(success=False, error="Text exceeds maximum length of 5000 characters",
                               error_code="TEXT_TOO_LONG", request_id=request_id)

    lang = tts_request.language.value
    emotion_speed = EMOTION_SPEED.get(tts_request.emotion, 1.0)
    final_speed = tts_request.speed * emotion_speed

    wav_bytes = None
    engine_used = None

    # 1) Self-hosted Piper first
    if piper_engine.available and lang in piper_engine.available_voices:
        try:
            wav_bytes = piper_engine.synthesize(tts_request.text, lang)
            engine_used = "piper-local"
        except Exception as e:
            logger.warning("piper_synthesis_failed", error=str(e), request_id=request_id)

    # 2) Fallback to OpenAI TTS API
    if wav_bytes is None and cloud_fallback.available:
        try:
            wav_bytes = await cloud_fallback.synthesize(tts_request.text, final_speed)
            engine_used = "openai-tts-api"
        except Exception as e:
            logger.error("openai_tts_failed", error=str(e), request_id=request_id)

    if wav_bytes is None:
        return HermesResponse(
            success=False,
            error="No TTS engine available: Piper voice model not found and no OPENAI_API_KEY fallback is configured.",
            error_code="TTS_UNAVAILABLE",
            request_id=request_id,
        )

    duration_seconds = _wav_duration_seconds(wav_bytes)
    sample_rate = _wav_sample_rate(wav_bytes)
    if g2p_engine.available:
        phoneme_timings = g2p_engine.phoneme_timeline(tts_request.text, duration_seconds)
    else:
        # Honest fallback: word-level timing only, no fabricated phonemes.
        phoneme_timings = _estimate_word_timings(tts_request.text, duration_seconds)
    audio_base64 = base64.b64encode(wav_bytes).decode("utf-8")

    tts_response = TTSResponse(
        audio_base64=audio_base64,
        format="wav",
        sample_rate=sample_rate,
        duration_seconds=round(duration_seconds, 2),
        phoneme_timings=phoneme_timings,
        engine_used=engine_used,
    )

    logger.info("tts_synthesis_complete", request_id=request_id, engine=engine_used,
                duration_seconds=duration_seconds, chars=len(tts_request.text))

    return HermesResponse(success=True, data=tts_response.model_dump(), request_id=request_id)


@app.get("/v1/engines", response_model=HermesResponse)
async def engines():
    return HermesResponse(success=True, data={
        "piper_local_available": piper_engine.available,
        "piper_voices_loaded": list(piper_engine.available_voices.keys()),
        "openai_fallback_available": cloud_fallback.available,
    })


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002, log_level="info")
