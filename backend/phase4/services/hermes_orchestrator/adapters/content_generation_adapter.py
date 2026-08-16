"""Content Generation Service Adapter"""
from typing import Dict, Any, Optional
from .base import BaseAdapter

class ContentGenerationAdapter(BaseAdapter):
    def __init__(self, base_url: Optional[str] = None):
        super().__init__("content_generation", base_url)

    async def generate(
        self,
        content_type: str,
        topic: str,
        language: str,
        cefr_level: str,
        count: int = 1,
        constraints: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        result = await self._request("POST", "/v1/generate", payload={
            "content_type": content_type,
            "topic": topic,
            "language": language,
            "cefr_level": cefr_level,
            "count": count,
            "constraints": constraints or {}
        })
        return result.data if result.success else {"error": result.error}

    async def get_content(self, content_id: str) -> Dict[str, Any]:
        result = await self._request("GET", f"/v1/content/{content_id}")
        return result.data if result.success else {"error": result.error}
