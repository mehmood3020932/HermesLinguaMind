"""Observability Service Adapter"""
from typing import Dict, Any, Optional
from .base import BaseAdapter

class ObservabilityAdapter(BaseAdapter):
    def __init__(self, base_url: Optional[str] = None):
        super().__init__("observability", base_url)

    async def ingest_metrics(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        result = await self._request("POST", "/v1/metrics/ingest", payload=metrics)
        return result.data if result.success else {"error": result.error}

    async def get_metrics(self, service_name: str) -> Dict[str, Any]:
        result = await self._request("GET", f"/v1/metrics/{service_name}")
        return result.data if result.success else {"error": result.error}

    async def get_all_metrics(self) -> Dict[str, Any]:
        result = await self._request("GET", "/v1/metrics/all")
        return result.data if result.success else {"error": result.error}

    async def get_alerts(self) -> Dict[str, Any]:
        result = await self._request("GET", "/v1/alerts")
        return result.data if result.success else {"error": result.error}
