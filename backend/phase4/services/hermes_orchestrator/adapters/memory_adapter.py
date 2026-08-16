"""Memory Service Adapter"""
from typing import Dict, Any, Optional
from .base import BaseAdapter

class MemoryAdapter(BaseAdapter):
    def __init__(self, base_url: Optional[str] = None):
        super().__init__("memory", base_url)

    async def store(
        self,
        user_id: str,
        memory_type: str,
        content: Dict[str, Any],
        ttl_seconds: Optional[int] = None
    ) -> Dict[str, Any]:
        result = await self._request("POST", "/v1/store", payload={
            "user_id": user_id,
            "memory_type": memory_type,
            "content": content,
            "ttl_seconds": ttl_seconds
        })
        return result.data if result.success else {"error": result.error}

    async def retrieve(
        self,
        user_id: str,
        memory_type: Optional[str] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        result = await self._request("GET", f"/v1/retrieve/{user_id}", params={
            "memory_type": memory_type,
            "limit": limit
        })
        return result.data if result.success else {"error": result.error}
