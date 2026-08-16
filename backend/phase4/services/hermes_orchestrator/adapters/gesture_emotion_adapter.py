"""Gesture/Emotion Service Adapter"""
from typing import Dict, Any, Optional
from .base import BaseAdapter

class GestureEmotionAdapter(BaseAdapter):
    def __init__(self, base_url: Optional[str] = None):
        super().__init__("gesture_emotion", base_url)

    async def get_gesture(
        self,
        text: str,
        emotion: Optional[str] = None,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        result = await self._request("POST", "/v1/gesture", payload={
            "text": text,
            "emotion": emotion,
            "context": context
        })
        return result.data if result.success else {"error": result.error}

    async def list_gestures(self) -> Dict[str, Any]:
        result = await self._request("GET", "/v1/gestures")
        return result.data if result.success else {"error": result.error}
