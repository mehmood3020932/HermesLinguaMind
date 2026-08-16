"""
Hermes LinguaMind — Pronunciation Scoring Service
Port: 8005 | Phase 3 — Production

Real scoring pipeline:
  1. Transcribe the learner's audio with self-hosted faster-whisper
     (word-level timestamps + real per-segment confidence from the model).
  2. Align the recognized words against the expected text with a genuine
     sequence-alignment algorithm (difflib) to find substitutions,
     omissions, and insertions — not fabricated per-phoneme noise.
  3. Score each expected word using the alignment result and the ASR
     model's own confidence for that stretch of audio.

This is an honest, ASR-grounded approximation. True phoneme-level
forced alignment (e.g. Wav2Vec2 CTC + a phonemizer) would give finer
per-phoneme detail; that is a heavier optional upgrade documented in
/v1/calibration below, not something this service claims to already do.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import time
import base64
import tempfile
import difflib
from typing import List, Dict, Any, Optional
from datetime import datetime

from fastapi import FastAPI, Request
import structlog
import uvicorn

from shared.models.common import HermesResponse, HealthStatus, PronunciationRequest, PronunciationResponse
from shared.utils.helpers import generate_request_id

logger = structlog.get_logger("hermes.pronunciation")

app = FastAPI(title="Hermes Pronunciation Service", description="ASR-grounded pronunciation scoring", version="3.1.0")
_app_start_time = time.time()

WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "base")
WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "cpu")
WHISPER_COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "int8")


class WhisperASR:
    def __init__(self):
        self.model = None
        self.load_error: Optional[str] = None
        try:
            from faster_whisper import WhisperModel
            self.model = WhisperModel(WHISPER_MODEL_SIZE, device=WHISPER_DEVICE, compute_type=WHISPER_COMPUTE_TYPE)
            logger.info("pronunciation_asr_loaded", model=WHISPER_MODEL_SIZE)
        except Exception as e:
            self.load_error = str(e)
            logger.warning("pronunciation_asr_unavailable", error=str(e))

    @property
    def available(self) -> bool:
        return self.model is not None

    def transcribe(self, wav_path: str, language: Optional[str]):
        segments_iter, info = self.model.transcribe(wav_path, language=language, task="transcribe", word_timestamps=True)
        words = []
        for seg in segments_iter:
            seg_conf = round(float(getattr(seg, "avg_logprob", -0.5)) + 1.0, 2)
            seg_conf = max(0.0, min(1.0, seg_conf))
            for w in (getattr(seg, "words", None) or []):
                words.append({"text": w.word.strip().lower(), "confidence": seg_conf})
        return words, info


asr = WhisperASR()


def _clean(word: str) -> str:
    return "".join(c.lower() for c in word if c.isalpha())


def _score_against_transcript(expected_text: str, recognized_words: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Align expected words to what was actually recognized, using real
    sequence-matching (not random noise). A matched word scores high
    (scaled by the ASR model's confidence for that audio region); a
    substituted/omitted word scores low."""
    expected = [_clean(w) for w in expected_text.split() if _clean(w)]
    recognized = [_clean(w["text"]) for w in recognized_words]
    conf_by_index = [w["confidence"] for w in recognized_words]

    matcher = difflib.SequenceMatcher(a=expected, b=recognized, autojunk=False)
    word_scores = [None] * len(expected)

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for offset in range(i2 - i1):
                exp_idx = i1 + offset
                rec_idx = j1 + offset
                conf = conf_by_index[rec_idx] if rec_idx < len(conf_by_index) else 0.85
                word_scores[exp_idx] = {"matched": True, "score": round(0.75 + 0.25 * conf, 2), "confidence": conf}
        elif tag == "replace":
            span = max(i2 - i1, 1)
            for offset in range(i2 - i1):
                exp_idx = i1 + offset
                rec_idx = j1 + min(offset, max(j2 - j1 - 1, 0)) if j2 > j1 else None
                conf = conf_by_index[rec_idx] if rec_idx is not None and rec_idx < len(conf_by_index) else 0.3
                # Partial credit if the substituted word is textually close
                # (e.g. close homophone / minor mispronunciation) via
                # character-level similarity, still driven by real strings.
                similarity = 0.0
                if j2 > j1:
                    cand = recognized[j1 + min(offset, j2 - j1 - 1)]
                    similarity = difflib.SequenceMatcher(a=expected[exp_idx], b=cand).ratio()
                score = round(0.2 + 0.5 * similarity, 2)
                word_scores[exp_idx] = {"matched": False, "score": score, "confidence": round(conf, 2)}
        elif tag == "delete":
            for offset in range(i2 - i1):
                word_scores[i1 + offset] = {"matched": False, "score": 0.1, "confidence": 0.0}
        # "insert" (extra words the learner said that weren't expected) doesn't
        # penalize a specific expected word; it's reflected in overall fluency
        # only, which this simplified scorer doesn't separately report.

    for idx, val in enumerate(word_scores):
        if val is None:
            word_scores[idx] = {"matched": False, "score": 0.1, "confidence": 0.0}

    return [
        {"word": expected_word, **word_scores[idx]}
        for idx, expected_word in enumerate(w for w in expected_text.split() if _clean(w))
    ]


@app.get("/health", response_model=HealthStatus)
async def health_check():
    uptime = time.time() - _app_start_time
    return HealthStatus(status="healthy" if asr.available else "degraded", service="pronunciation", version="3.1.0",
                        timestamp=datetime.utcnow(), uptime_seconds=uptime,
                        dependencies={"faster_whisper": "ready" if asr.available else "unavailable"})


@app.post("/v1/score", response_model=HermesResponse)
async def score_pronunciation(request: Request, pron_request: PronunciationRequest):
    request_id = getattr(request.state, "request_id", generate_request_id())

    if not asr.available:
        return HermesResponse(
            success=False,
            error=f"Pronunciation ASR model unavailable: {asr.load_error}",
            error_code="PRONUNCIATION_ENGINE_UNAVAILABLE",
            request_id=request_id,
        )

    tmp_path = None
    try:
        audio_bytes = base64.b64decode(pron_request.audio_base64)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        recognized_words, info = asr.transcribe(tmp_path, pron_request.language.value)
        word_results = _score_against_transcript(pron_request.expected_text, recognized_words)

        overall_score = (sum(w["score"] for w in word_results) / len(word_results) * 100) if word_results else 0.0

        if overall_score >= 90:
            feedback = "Excellent pronunciation! Your accent is very clear and natural."
        elif overall_score >= 75:
            feedback = "Good pronunciation! A few minor adjustments will make you sound even more natural."
        elif overall_score >= 60:
            feedback = "Fair pronunciation. Focus on the words marked low and practice them slowly."
        else:
            feedback = "Keep practicing! Try saying the sentence more slowly and clearly."

        native_map = {
            "es": "¡Buen intento! Practica las palabras marcadas.",
            "fr": "Bon effort! Concentrez-vous sur les mots marqués.",
            "de": "Guter Versuch! Konzentrieren Sie sich auf die markierten Wörter.",
            "hi": "अच्छा प्रयास! चिह्नित शब्दों पर ध्यान दें।",
            "zh": "不错的尝试！专注于标记的单词。",
            "ja": "良い試みです！マークされた単語に集中してください。",
            "ar": "محاولة جيدة! ركز على الكلمات المحددة.",
        }
        native_feedback = None
        if pron_request.native_language:
            native_feedback = native_map.get(pron_request.native_language.value, feedback)

        pron_response = PronunciationResponse(
            overall_score=round(overall_score, 1),
            phoneme_scores=[],  # true per-phoneme scoring needs Wav2Vec2 CTC + a phonemizer; not fabricated here
            word_scores=word_results,
            feedback=feedback,
            feedback_native_language=native_feedback,
            confidence=round(float(getattr(info, "language_probability", 0.85)), 2),
        )

        logger.info("pronunciation_scored", request_id=request_id, overall_score=overall_score,
                    language=pron_request.language.value, engine="faster-whisper-alignment")

        return HermesResponse(success=True, data=pron_response.model_dump(), request_id=request_id)

    except Exception as e:
        logger.error("pronunciation_scoring_failed", request_id=request_id, error=str(e))
        return HermesResponse(success=False, error=f"Pronunciation scoring failed: {str(e)}",
                              error_code="PRONUNCIATION_ERROR", request_id=request_id)
    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass


@app.get("/v1/calibration", response_model=HermesResponse)
async def get_calibration_info():
    return HermesResponse(success=True, data={
        "model": f"faster-whisper-{WHISPER_MODEL_SIZE}",
        "scoring_method": "asr_transcription_plus_sequence_alignment",
        "supported_languages": ["en", "es", "fr", "de", "it"],
        "notes": (
            "Word-level scoring is derived from real ASR transcription confidence "
            "and edit-distance alignment against the expected text. True per-phoneme "
            "forced alignment (Wav2Vec2 CTC + phonemizer) is not implemented — no "
            "fabricated accuracy benchmark numbers are reported here."
        ),
    })


@app.get("/v1/metrics")
async def get_metrics():
    return {"uptime_seconds": time.time() - _app_start_time, "asr_ready": asr.available, "model": WHISPER_MODEL_SIZE}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8005, log_level="info")
