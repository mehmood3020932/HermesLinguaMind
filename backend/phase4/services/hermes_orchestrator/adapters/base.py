"""
Hermes Orchestrator — Base Adapter
All service adapters inherit from this base class.
"""
import os
import time
from typing import Dict, Any, Optional, TypeVar, Generic
from abc import ABC

import httpx
import structlog

from shared.utils.helpers import async_retry, CircuitBreaker, Timer
from shared.models.common import AdapterResult

logger = structlog.get_logger()
T = TypeVar("T")

class ServiceAdapterError(Exception):
    """Base exception for adapter errors."""
    def __init__(self, service: str, message: str, status_code: int = 500):
        self.service = service
        self.status_code = status_code
        super().__init__(f"[{service}] {message}")

class ServiceUnavailable(ServiceAdapterError):
    """Service is down or unreachable."""
    pass

class BaseAdapter(ABC, Generic[T]):
    """
    Base class for all service adapters.
    Provides: HTTP client, circuit breaker, retries, logging, timeout handling.
    """

    DEFAULT_TIMEOUT = 30.0
    DEFAULT_RETRIES = 2

    def __init__(
        self,
        service_name: str,
        base_url: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
        retries: int = DEFAULT_RETRIES
    ):
        self.service_name = service_name
        self.base_url = base_url or os.getenv(
            f"{service_name.upper()}_SERVICE_URL",
            f"http://localhost:{self._default_port()}"
        )
        self.timeout = timeout
        self.retries = retries
        self.circuit_breaker = CircuitBreaker(service_name)
        self._client: Optional[httpx.AsyncClient] = None

    def _default_port(self) -> int:
        """Default port mapping for services."""
        port_map = {
            "api_gateway": 8000,
            "llm": 8001,
            "tts": 8002,
            "stt": 8003,
            "viseme": 8004,
            "pronunciation": 8005,
            "coin_ledger": 8006,
            "curriculum": 8007,
            "memory": 8008,
            "moderation": 8009,
            "grammar_rule_db": 8010,
            "content_generation": 8011,
            "personalization": 8012,
            "gesture_emotion": 8013,
            "leaderboard": 8014,
            "social_exchange": 8015,
            "anti_fraud": 8016,
            "live_conversation": 8017,
            "observability": 8018,
            "security": 8019,
            "hermes_orchestrator": 8020,
        }
        return port_map.get(self.service_name, 8000)

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout, connect=5.0),
                limits=httpx.Limits(max_keepalive_connections=20, max_connections=50)
            )
        return self._client

    async def _request(
        self,
        method: str,
        endpoint: str,
        payload: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None
    ) -> AdapterResult:
        """
        Make an HTTP request with circuit breaker, retries, and comprehensive logging.
        """
        url = f"{self.base_url}{endpoint}"
        request_id = headers.get("X-Request-ID", "unknown") if headers else "unknown"

        with Timer(f"{self.service_name}_{endpoint}") as timer:
            try:
                result = await self.circuit_breaker.call(
                    self._do_request,
                    method, url, payload, params, headers, timeout
                )
                result.latency_ms = timer.elapsed_ms
                return result
            except Exception as e:
                logger.error(
                    "adapter_request_failed",
                    service=self.service_name,
                    endpoint=endpoint,
                    error=str(e),
                    request_id=request_id
                )
                return AdapterResult(
                    service=self.service_name,
                    endpoint=endpoint,
                    success=False,
                    error=str(e),
                    latency_ms=timer.elapsed_ms
                )

    @async_retry(max_retries=2, backoff_base=1.0)
    async def _do_request(
        self,
        method: str,
        url: str,
        payload: Optional[Dict[str, Any]],
        params: Optional[Dict[str, Any]],
        headers: Optional[Dict[str, str]],
        timeout: Optional[float] = None
    ) -> AdapterResult:
        client = await self._get_client()

        response = await client.request(
            method=method,
            url=url,
            json=payload,
            params=params,
            headers=headers or {},
            timeout=timeout or self.timeout
        )
        response.raise_for_status()

        return AdapterResult(
            service=self.service_name,
            endpoint=url.replace(self.base_url, ""),
            success=True,
            data=response.json() if response.content else {}
        )

    async def health_check(self) -> bool:
        """Quick health check for the service."""
        try:
            result = await self._request("GET", "/health", timeout=5.0)
            return result.success and result.data.get("status") == "healthy"
        except Exception:
            return False

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()
