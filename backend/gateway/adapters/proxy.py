"""
Reverse-proxy phase adapter.

Each microservice keeps its own process/port (Strategy A).
The unified adapter mounts a conflict-free prefix per service and
forwards HTTP traffic upstream — no shared-module import collisions.
"""

from __future__ import annotations

from typing import Protocol

import httpx
from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse

from gateway.adapters.registry import SERVICE_REGISTRY, ServiceSpec
from gateway.logging_config import get_logger

logger = get_logger("hermes.proxy")

HOP_BY_HOP = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
    "host",
    "content-length",
}


class ClientProvider(Protocol):
    client: httpx.AsyncClient | None


def _filter_headers(headers) -> dict:
    return {k: v for k, v in headers.items() if k.lower() not in HOP_BY_HOP}


def build_proxy_router(spec: ServiceSpec, holder: ClientProvider) -> APIRouter:
    """Create a catch-all proxy router mounted at spec.mount_prefix."""
    router = APIRouter(tags=[f"{spec.tier}:{spec.name}"])

    async def _proxy(request: Request, path: str = "") -> Response:
        client = holder.client
        if client is None:
            return JSONResponse(
                status_code=503,
                content={
                    "success": False,
                    "error": {"code": "STARTING", "message": "Adapter starting"},
                },
            )

        upstream = f"{spec.upstream_url.rstrip('/')}/{path.lstrip('/')}" if path else spec.upstream_url
        if request.url.query:
            upstream = f"{upstream}?{request.url.query}"

        body = await request.body()
        headers = _filter_headers(request.headers)
        request_id = getattr(request.state, "request_id", None)
        if request_id:
            headers["X-Request-ID"] = request_id

        try:
            upstream_resp = await client.request(
                method=request.method,
                url=upstream,
                content=body if body else None,
                headers=headers,
                timeout=60.0,
            )
        except httpx.ConnectError:
            logger.error(
                "upstream_unreachable",
                service=spec.name,
                upstream=spec.upstream_url,
                request_id=request_id,
            )
            return JSONResponse(
                status_code=503,
                content={
                    "success": False,
                    "error": {
                        "code": "SERVICE_UNAVAILABLE",
                        "message": f"Upstream service '{spec.name}' is unreachable",
                        "upstream": spec.upstream_url,
                    },
                    "request_id": request_id,
                },
            )
        except httpx.TimeoutException:
            logger.error(
                "upstream_timeout",
                service=spec.name,
                upstream=upstream,
                request_id=request_id,
            )
            return JSONResponse(
                status_code=504,
                content={
                    "success": False,
                    "error": {
                        "code": "UPSTREAM_TIMEOUT",
                        "message": f"Upstream service '{spec.name}' timed out",
                    },
                    "request_id": request_id,
                },
            )

        return Response(
            content=upstream_resp.content,
            status_code=upstream_resp.status_code,
            headers=_filter_headers(upstream_resp.headers),
            media_type=upstream_resp.headers.get("content-type"),
        )

    router.add_api_route(
        "/",
        _proxy,
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
        include_in_schema=False,
    )
    router.add_api_route(
        "/{path:path}",
        _proxy,
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
        include_in_schema=True,
        name=f"proxy_{spec.name}",
    )
    return router


def mount_all_service_proxies(app, holder: ClientProvider) -> None:
    """Mount every phase service under its unique /svc/... prefix."""
    for spec in SERVICE_REGISTRY:
        router = build_proxy_router(spec, holder)
        app.include_router(router, prefix=spec.mount_prefix)
        logger.info(
            "phase_adapter_mounted",
            service=spec.name,
            tier=spec.tier,
            prefix=spec.mount_prefix,
            upstream=spec.upstream_url,
        )


async def check_upstream_health(client: httpx.AsyncClient, spec: ServiceSpec) -> dict:
    url = f"{spec.upstream_url.rstrip('/')}{spec.health_path}"
    try:
        resp = await client.get(url, timeout=3.0)
        return {
            "service": spec.name,
            "tier": spec.tier,
            "status": "healthy" if resp.status_code == 200 else "degraded",
            "status_code": resp.status_code,
            "url": url,
        }
    except Exception as exc:
        return {
            "service": spec.name,
            "tier": spec.tier,
            "status": "unreachable",
            "error": str(exc),
            "url": url,
        }
