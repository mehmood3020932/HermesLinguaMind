"""
Hermes LinguaMind — Gateway (Unified Adapter / Orchestrator Entry Point)
=========================================================================
Single public entry point for every backend service (23 services + the
Hermes orchestrator). Formerly `src/`, renamed to `gateway/` as part of
retiring the old phase1-4 folder naming now that phase1/ and phase2/ are
deleted — services are grouped by `tier` (core/advanced/ops/orchestrator)
purely for browsing, not by dead folder numbers.

This gateway:
  - mounts each service under a unique /svc/... prefix (no route clashes)
  - reverse-proxies to upstream services
  - applies global request logging + unified error handling
  - exposes aggregated health, registry, and convenience chat/orchestrate aliases
    that route straight to the Hermes Orchestrator (see /v1/chat below) —
    this is the live request path the Flutter app's chat/companion feature
    already calls today via ApiEndpoints.chat -> POST /v1/chat.

Run:
  uvicorn gateway.main:app --host 0.0.0.0 --port 8080
"""

from __future__ import annotations

import time
from contextlib import asynccontextmanager
from typing import Any, Dict, Optional

import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from gateway.adapters import (
    SERVICE_REGISTRY,
    check_upstream_health,
    mount_all_service_proxies,
    services_by_tier,
)
from gateway.adapters.registry import REGISTRY_BY_NAME
from gateway.config import settings
from gateway.logging_config import configure_logging, get_logger
from gateway.middleware import RequestLoggingMiddleware, register_exception_handlers

configure_logging()
logger = get_logger("hermes.adapter")


class _ClientHolder:
    """Mutable holder so routers created at import-time share the lifespan client."""

    client: Optional[httpx.AsyncClient] = None


http_holder = _ClientHolder()


class ChatProxyRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    session_context: Optional[Dict[str, Any]] = None


def _json_from_upstream(resp: httpx.Response) -> JSONResponse:
    try:
        content = resp.json()
    except Exception:
        content = {"raw": resp.text}
    return JSONResponse(status_code=resp.status_code, content=content)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.start_time = time.time()
    http_holder.client = httpx.AsyncClient(
        follow_redirects=True,
        limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
    )
    app.state.http_client = http_holder.client

    logger.info(
        "unified_adapter_started",
        version=settings.app_version,
        environment=settings.environment,
        services=len(SERVICE_REGISTRY),
        port=settings.port,
    )
    yield

    if http_holder.client is not None:
        await http_holder.client.aclose()
        http_holder.client = None
    logger.info("unified_adapter_stopped")


app = FastAPI(
    title=settings.app_name,
    description=(
        "Unified gateway for every Hermes LinguaMind backend service. "
        "Each service is mounted under /svc/* to eliminate route conflicts."
    ),
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── Global middleware (last added = outermost) ─────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggingMiddleware)
register_exception_handlers(app)

# ── Mount every service under conflict-free /svc/* prefixes ────────
mount_all_service_proxies(app, http_holder)


# ── Gateway-native control plane ────────────────────────────────────

@app.get("/", tags=["adapter"])
async def root():
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "tiers": ["core", "advanced", "ops", "orchestrator"],
        "docs": "/docs",
        "health": "/health",
        "registry": "/v1/services",
    }


@app.get("/health", tags=["adapter"])
async def health(request: Request, deep: bool = False):
    """Shallow gateway health; ?deep=true probes all upstream /health endpoints."""
    uptime = round(time.time() - request.app.state.start_time, 2)
    payload: Dict[str, Any] = {
        "status": "healthy",
        "service": "hermes_gateway",
        "version": settings.app_version,
        "uptime_seconds": uptime,
        "services_by_tier": {
            "core": len(services_by_tier("core")),
            "advanced": len(services_by_tier("advanced")),
            "ops": len(services_by_tier("ops")),
            "orchestrator": len(services_by_tier("orchestrator")),
        },
    }

    if deep:
        client = http_holder.client
        if client is None:
            payload["status"] = "starting"
            return payload
        results = [await check_upstream_health(client, spec) for spec in SERVICE_REGISTRY]
        unhealthy = [r for r in results if r["status"] != "healthy"]
        payload["upstreams"] = results
        payload["status"] = "degraded" if unhealthy else "healthy"
        payload["unhealthy_count"] = len(unhealthy)

    return payload


@app.get("/v1/services", tags=["adapter"])
async def list_services():
    """Full service registry."""
    return {
        "success": True,
        "count": len(SERVICE_REGISTRY),
        "services": [
            {
                "name": s.name,
                "tier": s.tier,
                "port": s.port,
                "mount": s.mount_prefix,
                "upstream": s.upstream_url,
                "health": f"{s.mount_prefix}{s.health_path}",
                "description": s.description,
            }
            for s in SERVICE_REGISTRY
        ],
    }


@app.get("/v1/tiers/{tier}", tags=["adapter"])
async def tier_services(tier: str):
    valid_tiers = {"core", "advanced", "ops", "orchestrator"}
    if tier not in valid_tiers:
        return JSONResponse(
            status_code=404,
            content={
                "success": False,
                "error": {"code": "UNKNOWN_TIER", "message": f"Tier '{tier}' not found. Valid: {sorted(valid_tiers)}"},
            },
        )
    specs = services_by_tier(tier)
    return {
        "success": True,
        "tier": tier,
        "count": len(specs),
        "services": [
            {"name": s.name, "mount": s.mount_prefix, "port": s.port} for s in specs
        ],
    }


@app.post("/v1/chat", tags=["adapter", "orchestrator"])
async def chat_alias(body: ChatProxyRequest):
    """Convenience alias → Hermes Orchestrator (Phase 4) /v1/orchestrate."""
    hermes = REGISTRY_BY_NAME["hermes_orchestrator"]
    client = http_holder.client
    if client is None:
        return JSONResponse(
            status_code=503,
            content={"success": False, "error": {"code": "STARTING", "message": "Adapter starting"}},
        )
    upstream = f"{hermes.upstream_url.rstrip('/')}/v1/orchestrate"
    try:
        resp = await client.post(upstream, json=body.model_dump(), timeout=60.0)
        return _json_from_upstream(resp)
    except httpx.ConnectError:
        return JSONResponse(
            status_code=503,
            content={
                "success": False,
                "error": {
                    "code": "SERVICE_UNAVAILABLE",
                    "message": "Hermes orchestrator unreachable",
                    "upstream": hermes.upstream_url,
                },
            },
        )


@app.post("/v1/orchestrate", tags=["adapter", "orchestrator"])
async def orchestrate_alias(request: Request):
    """Passthrough alias → Hermes Orchestrator /v1/orchestrate."""
    hermes = REGISTRY_BY_NAME["hermes_orchestrator"]
    client = http_holder.client
    if client is None:
        return JSONResponse(
            status_code=503,
            content={"success": False, "error": {"code": "STARTING", "message": "Adapter starting"}},
        )
    upstream = f"{hermes.upstream_url.rstrip('/')}/v1/orchestrate"
    payload = await request.json()
    try:
        resp = await client.post(upstream, json=payload, timeout=60.0)
        return _json_from_upstream(resp)
    except httpx.ConnectError:
        return JSONResponse(
            status_code=503,
            content={
                "success": False,
                "error": {
                    "code": "SERVICE_UNAVAILABLE",
                    "message": "Hermes orchestrator unreachable",
                },
            },
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "gateway.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower(),
    )
