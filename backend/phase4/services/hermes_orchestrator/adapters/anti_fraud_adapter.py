"""Anti-Fraud Service Adapter"""
from typing import Dict, Any, Optional
from .base import BaseAdapter

class AntiFraudAdapter(BaseAdapter):
    def __init__(self, base_url: Optional[str] = None):
        super().__init__("anti_fraud", base_url)

    async def check(
        self,
        user_id: str,
        action: str,
        amount: Optional[int] = None,
        ip_address: Optional[str] = None,
        device_fingerprint: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        result = await self._request("POST", "/v1/check", payload={
            "user_id": user_id,
            "action": action,
            "amount": amount,
            "ip_address": ip_address,
            "device_fingerprint": device_fingerprint,
            "metadata": metadata or {}
        })
        return result.data if result.success else {"error": result.error}

    async def get_alerts(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        params = {}
        if user_id:
            params["user_id"] = user_id
        result = await self._request("GET", "/v1/alerts", params=params)
        return result.data if result.success else {"error": result.error}
