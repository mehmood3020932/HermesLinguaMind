"""STT Service Adapter"""
from typing import Dict, Any, Optional
from .base import BaseAdapter

class STTAdapter(BaseAdapter):
    def __init__(self, base_url: Optional[str] = None):
        super().__init__("stt", base_url)

    async def transcribe(
        self,
        audio_base64: str,
        language: str = "en",
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        result = await self._request("POST", "/v1/transcribe", payload={
            "audio_base64": audio_base64,
            "language": language,
            "model": model
        })
        return result.data if result.success else {"error": result.error}

    async def list_models(self) -> Dict[str, Any]:
        result = await self._request("GET", "/v1/models")
        return result.data if result.success else {"error": result.error}
