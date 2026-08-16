"""Live Conversation Service Adapter"""
from typing import Dict, Any, Optional
from .base import BaseAdapter

class LiveConversationAdapter(BaseAdapter):
    def __init__(self, base_url: Optional[str] = None):
        super().__init__("live_conversation", base_url)

    async def start(
        self,
        user_id: str,
        scenario: Optional[str] = None,
        target_language: str = "en",
        difficulty: str = "A1",
        duration_minutes: int = 10
    ) -> Dict[str, Any]:
        result = await self._request("POST", "/v1/start", payload={
            "user_id": user_id,
            "scenario": scenario,
            "target_language": target_language,
            "difficulty": difficulty,
            "duration_minutes": duration_minutes
        })
        return result.data if result.success else {"error": result.error}

    async def end(
        self,
        session_id: str,
        user_id: str,
        rating: Optional[int] = None,
        feedback: Optional[str] = None
    ) -> Dict[str, Any]:
        result = await self._request("POST", f"/v1/end/{session_id}", payload={
            "user_id": user_id,
            "rating": rating,
            "feedback": feedback
        })
        return result.data if result.success else {"error": result.error}

    async def list_sessions(self, user_id: str) -> Dict[str, Any]:
        result = await self._request("GET", "/v1/sessions", params={"user_id": user_id})
        return result.data if result.success else {"error": result.error}
