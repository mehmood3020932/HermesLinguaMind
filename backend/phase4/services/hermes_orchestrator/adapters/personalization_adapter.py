"""Personalization Service Adapter"""
from typing import Dict, Any, Optional
from .base import BaseAdapter

class PersonalizationAdapter(BaseAdapter):
    def __init__(self, base_url: Optional[str] = None):
        super().__init__("personalization", base_url)

    async def analyze(
        self,
        user_id: str,
        interaction_data: Dict[str, Any],
        analysis_type: str = "learning_style"
    ) -> Dict[str, Any]:
        result = await self._request("POST", "/v1/analyze", payload={
            "user_id": user_id,
            "interaction_data": interaction_data,
            "analysis_type": analysis_type
        })
        return result.data if result.success else {"error": result.error}

    async def get_profile(self, user_id: str) -> Dict[str, Any]:
        result = await self._request("GET", f"/v1/profile/{user_id}")
        return result.data if result.success else {"error": result.error}
