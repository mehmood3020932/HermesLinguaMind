"""
Hermes LinguaMind — Viseme Service
Port: 8004 | Phase 3 — Production Ready
Phoneme-to-viseme timeline generation for lip-sync
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import time
from typing import List, Dict, Any
from datetime import datetime

from fastapi import FastAPI, Request
from pydantic import BaseModel, Field
import structlog
import uvicorn

from shared.models.common import HermesResponse, HealthStatus, VisemeRequest, VisemeResponse
from shared.utils.helpers import generate_request_id

logger = structlog.get_logger("hermes.viseme")

app = FastAPI(title="Hermes Viseme Service", description="Audio-to-viseme timeline for lip-sync", version="3.0.0")
_app_start_time = time.time()

# Viseme intensity mapping
VISEME_INTENSITY = {
    "sil": 0.0, "aa": 0.9, "ah": 0.8, "ao": 0.85, "aw": 0.85, "ay": 0.9,
    "b": 0.7, "ch": 0.6, "d": 0.5, "dh": 0.5, "eh": 0.7, "er": 0.6, "ey": 0.85,
    "f": 0.4, "g": 0.5, "hh": 0.3, "ih": 0.6, "iy": 0.7, "jh": 0.6, "k": 0.5,
    "l": 0.6, "m": 0.3, "n": 0.4, "ng": 0.4, "ow": 0.85, "oy": 0.9, "p": 0.3,
    "r": 0.5, "s": 0.4, "sh": 0.4, "t": 0.4, "th": 0.3, "uh": 0.7, "uw": 0.7,
    "v": 0.4, "w": 0.5, "y": 0.5, "z": 0.4, "zh": 0.4,
}

@app.get("/health", response_model=HealthStatus)
async def health_check():
    uptime = time.time() - _app_start_time
    return HealthStatus(status="healthy", service="viseme", version="3.0.0",
                        timestamp=datetime.utcnow(), uptime_seconds=uptime)

@app.post("/v1/generate", response_model=HermesResponse)
async def generate_visemes(request: Request, viseme_request: VisemeRequest):
    request_id = getattr(request.state, "request_id", generate_request_id())

    try:
        phoneme_timings = viseme_request.phoneme_timings
        fps = viseme_request.fps
        frame_duration_ms = 1000.0 / fps

        viseme_timeline = []

        # Convert phoneme timings to frame-based viseme timeline
        if phoneme_timings:
            total_duration_ms = phoneme_timings[-1]["end_time"] * 1000
            num_frames = int(total_duration_ms / frame_duration_ms) + 1

            for frame_idx in range(num_frames):
                frame_time_ms = frame_idx * frame_duration_ms
                frame_time_s = frame_time_ms / 1000.0

                # Find active phoneme at this time
                active_viseme = "sil"
                active_intensity = 0.0

                for timing in phoneme_timings:
                    if timing["start_time"] <= frame_time_s <= timing["end_time"]:
                        active_viseme = timing.get("viseme", "sil")
                        active_intensity = VISEME_INTENSITY.get(active_viseme, 0.5)
                        break

                # Apply smoothing between frames
                if frame_idx > 0 and viseme_timeline:
                    prev_intensity = viseme_timeline[-1]["intensity"]
                    active_intensity = 0.7 * active_intensity + 0.3 * prev_intensity

                viseme_timeline.append({
                    "frame": frame_idx,
                    "time_ms": round(frame_time_ms, 1),
                    "viseme": active_viseme,
                    "intensity": round(active_intensity, 2),
                    "blend_shapes": generate_blend_shapes(active_viseme, active_intensity),
                })

        total_duration_ms = viseme_timeline[-1]["time_ms"] if viseme_timeline else 0

        viseme_response = VisemeResponse(
            viseme_timeline=viseme_timeline,
            total_duration_ms=total_duration_ms,
            frame_count=len(viseme_timeline),
            fps=fps,
        )

        logger.info("viseme_generation_complete", request_id=request_id,
                    frame_count=len(viseme_timeline), fps=fps, duration_ms=total_duration_ms)

        return HermesResponse(success=True, data=viseme_response.model_dump(), request_id=request_id)

    except Exception as e:
        logger.error("viseme_generation_failed", request_id=request_id, error=str(e))
        return HermesResponse(success=False, error=f"Viseme generation failed: {str(e)}",
                              error_code="VISEME_ERROR", request_id=request_id)

def generate_blend_shapes(viseme: str, intensity: float) -> Dict[str, float]:
    """Generate blend shape weights for a viseme."""
    blend_shapes = {
        "jawOpen": 0.0,
        "mouthClose": 0.0,
        "mouthFunnel": 0.0,
        "mouthPucker": 0.0,
        "mouthSmile": 0.0,
        "mouthFrown": 0.0,
        "mouthStretchLeft": 0.0,
        "mouthStretchRight": 0.0,
        "mouthDimpleLeft": 0.0,
        "mouthDimpleRight": 0.0,
        "mouthPressLeft": 0.0,
        "mouthPressRight": 0.0,
        "mouthUpperUp": 0.0,
        "mouthLowerDown": 0.0,
    }

    if viseme == "sil":
        pass
    elif viseme in ["aa", "ah", "ao", "aw"]:
        blend_shapes["jawOpen"] = 0.6 * intensity
        blend_shapes["mouthUpperUp"] = 0.3 * intensity
        blend_shapes["mouthLowerDown"] = 0.3 * intensity
    elif viseme in ["b", "p", "m"]:
        blend_shapes["mouthClose"] = 0.8 * intensity
        blend_shapes["mouthPucker"] = 0.2 * intensity
    elif viseme in ["f", "v"]:
        blend_shapes["mouthUpperUp"] = 0.4 * intensity
        blend_shapes["mouthLowerDown"] = 0.1 * intensity
    elif viseme in ["w", "uw"]:
        blend_shapes["mouthPucker"] = 0.7 * intensity
        blend_shapes["jawOpen"] = 0.2 * intensity
    elif viseme in ["iy", "ih"]:
        blend_shapes["mouthSmile"] = 0.4 * intensity
        blend_shapes["jawOpen"] = 0.2 * intensity
    elif viseme in ["s", "z", "sh", "zh", "ch", "jh"]:
        blend_shapes["mouthStretchLeft"] = 0.3 * intensity
        blend_shapes["mouthStretchRight"] = 0.3 * intensity
    elif viseme in ["th", "dh"]:
        blend_shapes["jawOpen"] = 0.3 * intensity
        blend_shapes["mouthUpperUp"] = 0.2 * intensity
        blend_shapes["mouthLowerDown"] = 0.1 * intensity
    else:
        blend_shapes["jawOpen"] = 0.4 * intensity

    return {k: round(v, 3) for k, v in blend_shapes.items()}

@app.get("/v1/viseme-map", response_model=HermesResponse)
async def get_viseme_map():
    return HermesResponse(success=True, data={
        "visemes": list(VISEME_INTENSITY.keys()),
        "intensity_map": VISEME_INTENSITY,
        "blend_shape_count": 14,
    })

@app.get("/v1/metrics")
async def get_metrics():
    return {"uptime_seconds": time.time() - _app_start_time}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8004, log_level="info")
