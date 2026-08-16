"""Social Exchange Service Adapter"""
from typing import Dict, Any, Optional
from .base import BaseAdapter

class SocialExchangeAdapter(BaseAdapter):
    def __init__(self, base_url: Optional[str] = None):
        super().__init__("social_exchange", base_url)

    async def find_match(
        self,
        user_id: str,
        match_type: str = "conversation",
        preferred_language: Optional[str] = None,
        cefr_level: Optional[str] = None
    ) -> Dict[str, Any]:
        result = await self._request("POST", "/v1/match", payload={
            "user_id": user_id,
            "match_type": match_type,
            "preferred_language": preferred_language,
            "cefr_level": cefr_level
        })
        return result.data if result.success else {"error": result.error}

    async def get_profile(self, user_id: str) -> Dict[str, Any]:
        result = await self._request("GET", f"/v1/profile/{user_id}")
        return result.data if result.success else {"error": result.error}

    async def update_profile(self, user_id: str, **kwargs) -> Dict[str, Any]:
        result = await self._request("POST", "/v1/profile", payload={"user_id": user_id, **kwargs})
        return result.data if result.success else {"error": result.error}

    async def report(self, reporter_id: str, reported_id: str, reason: str) -> Dict[str, Any]:
        result = await self._request("POST", "/v1/report", payload={
            "reporter_id": reporter_id,
            "reported_id": reported_id,
            "reason": reason
        })
        return result.data if result.success else {"error": result.error}
