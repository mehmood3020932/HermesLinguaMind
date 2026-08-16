"""Pronunciation Service Adapter"""
from typing import Dict, Any, Optional
from .base import BaseAdapter

class PronunciationAdapter(BaseAdapter):
    def __init__(self, base_url: Optional[str] = None):
        super().__init__("pronunciation", base_url)

    async def score(
        self,
        audio_base64: str,
        expected_text: str,
        language: str = "en",
        user_cefr: str = "A1"
    ) -> Dict[str, Any]:
        result = await self._request("POST", "/v1/score", payload={
            "audio_base64": audio_base64,
            "expected_text": expected_text,
            "language": language,
            "user_cefr": user_cefr
        })
        return result.data if result.success else {"error": result.error}

    async def calibrate(self, user_id: str, audio_base64: str, language: str = "en") -> Dict[str, Any]:
        result = await self._request("POST", "/v1/calibration", payload={
            "user_id": user_id,
            "audio_base64": audio_base64,
            "language": language
        })
        return result.data if result.success else {"error": result.error}
