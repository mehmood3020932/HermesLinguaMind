"""Security Service Adapter"""
from typing import Dict, Any, Optional
from .base import BaseAdapter

class SecurityAdapter(BaseAdapter):
    def __init__(self, base_url: Optional[str] = None):
        super().__init__("security", base_url)

    async def log_audit(
        self,
        user_id: Optional[str],
        action: str,
        service: str,
        endpoint: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_body: Optional[str] = None,
        response_status: Optional[int] = None,
        latency_ms: float = 0.0
    ) -> Dict[str, Any]:
        result = await self._request("POST", "/v1/audit/log", payload={
            "user_id": user_id,
            "action": action,
            "service": service,
            "endpoint": endpoint,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "request_body": request_body,
            "response_status": response_status,
            "latency_ms": latency_ms
        })
        return result.data if result.success else {"error": result.error}

    async def get_audit_logs(self, user_id: Optional[str] = None, limit: int = 100) -> Dict[str, Any]:
        params = {"limit": limit}
        if user_id:
            params["user_id"] = user_id
        result = await self._request("GET", "/v1/audit/logs", params=params)
        return result.data if result.success else {"error": result.error}

    async def trigger_backup(self) -> Dict[str, Any]:
        result = await self._request("POST", "/v1/backup")
        return result.data if result.success else {"error": result.error}

    async def get_compliance_status(self) -> Dict[str, Any]:
        result = await self._request("GET", "/v1/compliance/status")
        return result.data if result.success else {"error": result.error}
