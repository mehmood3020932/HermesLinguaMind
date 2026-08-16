"""Viseme Service Adapter"""
from typing import Dict, Any, Optional
from .base import BaseAdapter

class VisemeAdapter(BaseAdapter):
    def __init__(self, base_url: Optional[str] = None):
        super().__init__("viseme", base_url)

    async def generate(
        self,
        text: str,
        language: str = "en",
        audio_duration_seconds: Optional[float] = None
    ) -> Dict[str, Any]:
        result = await self._request("POST", "/v1/generate", payload={
            "text": text,
            "language": language,
            "audio_duration_seconds": audio_duration_seconds
        })
        return result.data if result.success else {"error": result.error}

    async def get_viseme_map(self) -> Dict[str, Any]:
        result = await self._request("GET", "/v1/viseme-map")
        return result.data if result.success else {"error": result.error}
