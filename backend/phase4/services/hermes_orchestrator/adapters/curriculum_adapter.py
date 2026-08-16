"""Curriculum Service Adapter"""
from typing import Dict, Any, Optional
from .base import BaseAdapter

class CurriculumAdapter(BaseAdapter):
    def __init__(self, base_url: Optional[str] = None):
        super().__init__("curriculum", base_url)

    async def get_curriculum(
        self,
        user_id: str,
        language: str,
        cefr_level: str,
        module_id: Optional[str] = None
    ) -> Dict[str, Any]:
        result = await self._request("POST", "/v1/curriculum", payload={
            "user_id": user_id,
            "language": language,
            "cefr_level": cefr_level,
            "module_id": module_id
        })
        return result.data if result.success else {"error": result.error}

    async def complete_lesson(
        self,
        user_id: str,
        lesson_id: str,
        module_id: str,
        score: float,
        time_spent_seconds: int
    ) -> Dict[str, Any]:
        result = await self._request("POST", "/v1/complete-lesson", payload={
            "user_id": user_id,
            "lesson_id": lesson_id,
            "module_id": module_id,
            "score": score,
            "time_spent_seconds": time_spent_seconds
        })
        return result.data if result.success else {"error": result.error}
