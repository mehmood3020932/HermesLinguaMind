"""Leaderboard Service Adapter"""
from typing import Dict, Any, Optional
from .base import BaseAdapter

class LeaderboardAdapter(BaseAdapter):
    def __init__(self, base_url: Optional[str] = None):
        super().__init__("leaderboard", base_url)

    async def get_leaderboard(
        self,
        period: str = "weekly",
        language: Optional[str] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        params = {"period": period, "limit": limit}
        if language:
            params["language"] = language
        result = await self._request("GET", "/v1/leaderboard", params=params)
        return result.data if result.success else {"error": result.error}

    async def submit_score(self, user_id: str, score: int, category: str) -> Dict[str, Any]:
        result = await self._request("POST", "/v1/submit-score", payload={
            "user_id": user_id,
            "score": score,
            "category": category
        })
        return result.data if result.success else {"error": result.error}
