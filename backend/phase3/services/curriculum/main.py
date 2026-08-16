"""
Hermes LinguaMind — Curriculum Service
Port: 8007 | Phase 3 — Production Ready
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

from shared.models.common import HermesResponse, HealthStatus, CurriculumRequest, CurriculumResponse, CEFRLevel
from shared.utils.helpers import sm2_update, generate_request_id

logger = structlog.get_logger("hermes.curriculum")
app = FastAPI(title="Hermes Curriculum", version="3.0.0")
_app_start_time = time.time()

_curriculum_progress: Dict[str, List[Dict[str, Any]]] = {}
LESSON_TEMPLATES = {
    "A1": [{"id": "a1_greetings", "title": "Greetings", "module": "basics", "difficulty": 1.0},
           {"id": "a1_numbers", "title": "Numbers", "module": "basics", "difficulty": 1.1},
           {"id": "a1_family", "title": "Family", "module": "vocabulary", "difficulty": 1.2}],
    "A2": [{"id": "a2_past", "title": "Past Tense", "module": "grammar", "difficulty": 2.0},
           {"id": "a2_shopping", "title": "Shopping", "module": "conversation", "difficulty": 2.1}],
    "B1": [{"id": "b1_perfect", "title": "Present Perfect", "module": "grammar", "difficulty": 3.0},
           {"id": "b1_opinions", "title": "Opinions", "module": "conversation", "difficulty": 3.1}],
    "B2": [{"id": "b2_conditionals", "title": "Conditionals", "module": "grammar", "difficulty": 4.0}],
    "C1": [{"id": "c1_idioms", "title": "Idioms", "module": "vocabulary", "difficulty": 5.0}],
    "C2": [{"id": "c2_nuance", "title": "Nuance", "module": "vocabulary", "difficulty": 6.0}],
}

@app.get("/health", response_model=HealthStatus)
async def health_check():
    return HealthStatus(status="healthy", service="curriculum", version="3.0.0",
                        timestamp=datetime.utcnow(), uptime_seconds=time.time() - _app_start_time)

def _get_progress(user_id: str, language_pair: str) -> List[Dict[str, Any]]:
    key = f"{user_id}:{language_pair}"
    if key not in _curriculum_progress:
        _curriculum_progress[key] = []
    return _curriculum_progress[key]

@app.post("/v1/curriculum", response_model=HermesResponse)
async def get_curriculum(request: Request, req: CurriculumRequest):
    request_id = getattr(request.state, "request_id", generate_request_id())
    user_id = str(req.user_id)
    progress = _get_progress(user_id, req.language_pair)
    target = req.cefr_level.value if req.cefr_level else "A1"
    level_lessons = LESSON_TEMPLATES.get(target, [])

    lessons = []
    for lesson in level_lessons:
        lp = next((p for p in progress if p["lesson_id"] == lesson["id"]), None)
        lessons.append({**lesson, "status": lp["status"] if lp else "not_started",
                        "score": lp["score"] if lp else 0.0, "attempts": lp["attempts"] if lp else 0,
                        "streak_bonus": False})

    completed = [l for l in lessons if l["status"] == "completed"]
    avg = sum(l["score"] for l in completed) / len(completed) if completed else 0.0
    adaptive = float(target.replace("A", "").replace("B", "").replace("C", "")) + (0.5 if avg > 85 else (-0.5 if avg < 60 else 0))

    response = CurriculumResponse(lessons=lessons[:req.lesson_count], adaptive_difficulty=round(adaptive, 1),
                                   recommended_focus_areas=["grammar"] if avg < 60 else ["vocabulary"] if avg < 75 else ["balanced"],
                                   streak_days=0, total_lessons_completed=len(completed))
    return HermesResponse(success=True, data=response.model_dump(), request_id=request_id)

@app.post("/v1/complete-lesson", response_model=HermesResponse)
async def complete_lesson(request: Request, user_id: str, lesson_id: str, language_pair: str, score: float):
    request_id = getattr(request.state, "request_id", generate_request_id())
    progress = _get_progress(user_id, language_pair)
    existing = next((p for p in progress if p["lesson_id"] == lesson_id), None)
    quality = min(5, max(0, int(score / 20)))

    if existing:
        new_i, new_e, new_r = sm2_update(quality, existing.get("sm2_repetitions", 0),
                                          existing.get("sm2_ease_factor", 2.5), existing.get("sm2_interval", 1))
        existing.update({"status": "completed", "score": score, "attempts": existing["attempts"] + 1,
                         "sm2_interval": new_i, "sm2_ease_factor": new_e, "sm2_repetitions": new_r,
                         "next_review": (datetime.utcnow() + timedelta(days=new_i)).isoformat(),
                         "completed_at": datetime.utcnow().isoformat()})
    else:
        new_i, new_e, new_r = sm2_update(quality, 0, 2.5, 1)
        progress.append({"lesson_id": lesson_id, "status": "completed", "score": score, "attempts": 1,
                         "sm2_interval": new_i, "sm2_ease_factor": new_e, "sm2_repetitions": new_r,
                         "next_review": (datetime.utcnow() + timedelta(days=new_i)).isoformat(),
                         "completed_at": datetime.utcnow().isoformat()})

    logger.info("lesson_completed", request_id=request_id, user_id=user_id, lesson_id=lesson_id, score=score)
    return HermesResponse(success=True, data={"status": "completed", "next_review_in_days": new_i}, request_id=request_id)

@app.get("/v1/metrics")
async def get_metrics():
    return {"uptime_seconds": time.time() - _app_start_time, "records": sum(len(v) for v in _curriculum_progress.values())}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8007, log_level="info")
