"""TTS Service Adapter"""
from typing import Dict, Any, Optional
from .base import BaseAdapter

class TTSAdapter(BaseAdapter):
    def __init__(self, base_url: Optional[str] = None):
        super().__init__("tts", base_url)

    async def synthesize(
        self,
        text: str,
        language: str = "en",
        voice_id: Optional[str] = None,
        speed: float = 1.0,
        emotion: Optional[str] = None
    ) -> Dict[str, Any]:
        result = await self._request("POST", "/v1/synthesize", payload={
            "text": text,
            "language": language,
            "voice_id": voice_id,
            "speed": speed,
            "emotion": emotion
        })
        return result.data if result.success else {"error": result.error}

    async def list_engines(self) -> Dict[str, Any]:
        result = await self._request("GET", "/v1/engines")
        return result.data if result.success else {"error": result.error}
