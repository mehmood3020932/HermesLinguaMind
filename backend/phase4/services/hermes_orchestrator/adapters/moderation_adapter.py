"""Moderation Service Adapter"""
from typing import Dict, Any, Optional
from .base import BaseAdapter

class ModerationAdapter(BaseAdapter):
    def __init__(self, base_url: Optional[str] = None):
        super().__init__("moderation", base_url)

    async def moderate(
        self,
        user_id: str,
        text: Optional[str] = None,
        image_base64: Optional[str] = None,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        result = await self._request("POST", "/v1/moderate", payload={
            "user_id": user_id,
            "text": text,
            "image_base64": image_base64,
            "context": context
        })
        return result.data if result.success else {"error": result.error}
