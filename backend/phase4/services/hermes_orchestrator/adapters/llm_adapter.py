"""LLM Orchestration Service Adapter"""
from typing import Dict, Any, Optional
from .base import BaseAdapter

class LLMAdapter(BaseAdapter):
    def __init__(self, base_url: Optional[str] = None):
        super().__init__("llm", base_url)

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 500,
        temperature: float = 0.7,
        **kwargs
    ) -> Dict[str, Any]:
        result = await self._request("POST", "/v1/generate", payload={
            "prompt": prompt,
            "system_prompt": system_prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
            **kwargs
        })
        return result.data if result.success else {"error": result.error}

    async def grammar_check(self, text: str, target_language: str = "en", user_cefr: str = "A1") -> Dict[str, Any]:
        result = await self._request("POST", "/v1/grammar-check", payload={
            "text": text,
            "target_language": target_language,
            "user_cefr": user_cefr
        })
        return result.data if result.success else {"error": result.error}

    async def conversation(self, messages: list, user_id: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        result = await self._request("POST", "/v1/conversation", payload={
            "messages": messages,
            "user_id": user_id,
            "context": context or {}
        })
        return result.data if result.success else {"error": result.error}
