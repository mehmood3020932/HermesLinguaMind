"""
Hermes LinguaMind — Notification Service
Port: 8022 | Phase 3 — Production Ready

Three real, fully open-source delivery channels — no Firebase/OneSignal/
paid push provider required:

  1. In-app: stored server-side (Redis-backed if REDIS_URL is set, else
     in-process) and fetched by the client on poll/login.
  2. Web Push: the open W3C Push API + VAPID (RFC 8292), delivered via
     `pywebpush` directly to the browser's push service — no third-party
     relay, no account, no cost. Requires a VAPID keypair (generate once
     with `vapid --gen`, or via pywebpush.webpush's helper) in
     VAPID_PRIVATE_KEY / VAPID_PUBLIC_KEY / VAPID_CLAIM_EMAIL.
  3. Webhook: generic HTTP POST to any URL the caller registers (e.g. to
     bridge into a self-hosted Matrix/Mattermost/ntfy.sh instance) — again
     zero paid dependency.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
import structlog
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

from shared.models.common import HermesResponse, HealthStatus
from shared.utils.helpers import generate_request_id

logger = structlog.get_logger("hermes.notification")

app = FastAPI(title="Hermes Notification Service", description="In-app + Web Push (VAPID) + webhook, all open-source", version="3.0.0")
_app_start_time = time.time()

REDIS_URL = os.getenv("REDIS_URL", "")
VAPID_PRIVATE_KEY = os.getenv("VAPID_PRIVATE_KEY", "")
VAPID_PUBLIC_KEY = os.getenv("VAPID_PUBLIC_KEY", "")
VAPID_CLAIM_EMAIL = os.getenv("VAPID_CLAIM_EMAIL", "mailto:admin@linguamax.local")

_redis = None
if REDIS_URL:
    try:
        import redis.asyncio as aioredis
        _redis = aioredis.from_url(REDIS_URL, decode_responses=True)
    except Exception as e:
        logger.warning("redis_unavailable_falling_back_to_memory", error=str(e))

# In-process fallback store: {user_id: [notification, ...]}
_memory_store: Dict[str, List[Dict[str, Any]]] = {}
# Registered web-push subscriptions and webhooks per user.
_push_subs: Dict[str, List[Dict[str, Any]]] = {}
_webhooks: Dict[str, List[str]] = {}


class Notification(BaseModel):
    user_id: str
    title: str
    body: str
    kind: str = Field("info", description="info | streak | coin | social | grammar | system")
    data: Dict[str, Any] = Field(default_factory=dict)
    channels: List[str] = Field(default_factory=lambda: ["in_app"], description="in_app | push | webhook")


class PushSubscription(BaseModel):
    user_id: str
    endpoint: str
    keys: Dict[str, str]  # {"p256dh": ..., "auth": ...} from the browser Push API


class WebhookRegistration(BaseModel):
    user_id: str
    url: str


async def _store_in_app(notif: Dict[str, Any]) -> None:
    user_id = notif["user_id"]
    if _redis:
        await _redis.lpush(f"notif:{user_id}", json.dumps(notif))
        await _redis.ltrim(f"notif:{user_id}", 0, 199)
    else:
        _memory_store.setdefault(user_id, []).insert(0, notif)
        _memory_store[user_id] = _memory_store[user_id][:200]


async def _send_push(user_id: str, notif: Dict[str, Any]) -> int:
    if not (VAPID_PRIVATE_KEY and VAPID_PUBLIC_KEY):
        return 0
    from pywebpush import webpush, WebPushException

    sent = 0
    for sub in _push_subs.get(user_id, []):
        try:
            webpush(
                subscription_info={"endpoint": sub["endpoint"], "keys": sub["keys"]},
                data=json.dumps({"title": notif["title"], "body": notif["body"], "data": notif.get("data", {})}),
                vapid_private_key=VAPID_PRIVATE_KEY,
                vapid_claims={"sub": VAPID_CLAIM_EMAIL},
            )
            sent += 1
        except WebPushException as e:
            logger.warning("webpush_failed", user_id=user_id, error=str(e))
    return sent


async def _send_webhooks(user_id: str, notif: Dict[str, Any]) -> int:
    urls = _webhooks.get(user_id, [])
    if not urls:
        return 0
    sent = 0
    async with httpx.AsyncClient(timeout=10) as client:
        for url in urls:
            try:
                await client.post(url, json=notif)
                sent += 1
            except Exception as e:
                logger.warning("webhook_failed", url=url, error=str(e))
    return sent


@app.get("/health", response_model=HealthStatus)
async def health_check():
    return HealthStatus(
        status="healthy",
        service="notification_service",
        version="3.0.0",
        timestamp=datetime.utcnow(),
        uptime_seconds=time.time() - _app_start_time,
        dependencies={
            "redis": "connected" if _redis else "in_memory_fallback",
            "web_push": "configured" if VAPID_PRIVATE_KEY else "not_configured",
        },
    )


@app.post("/v1/notify", response_model=HermesResponse)
async def send_notification(request: Request, notif: Notification):
    request_id = getattr(request.state, "request_id", generate_request_id())
    record = {
        "id": str(uuid.uuid4()),
        "user_id": notif.user_id,
        "title": notif.title,
        "body": notif.body,
        "kind": notif.kind,
        "data": notif.data,
        "read": False,
        "created_at": datetime.utcnow().isoformat(),
    }

    results = {"in_app": False, "push": 0, "webhook": 0}
    if "in_app" in notif.channels:
        await _store_in_app(record)
        results["in_app"] = True
    if "push" in notif.channels:
        results["push"] = await _send_push(notif.user_id, record)
    if "webhook" in notif.channels:
        results["webhook"] = await _send_webhooks(notif.user_id, record)

    logger.info("notification_dispatched", request_id=request_id, notification_id=record["id"], results=results)
    return HermesResponse(success=True, data={"notification": record, "delivery": results}, request_id=request_id)


@app.get("/v1/notify/{user_id}", response_model=HermesResponse)
async def list_notifications(user_id: str, unread_only: bool = False, limit: int = 50):
    if _redis:
        raw = await _redis.lrange(f"notif:{user_id}", 0, limit - 1)
        items = [json.loads(r) for r in raw]
    else:
        items = _memory_store.get(user_id, [])[:limit]
    if unread_only:
        items = [i for i in items if not i.get("read")]
    return HermesResponse(success=True, data={"notifications": items, "count": len(items)}, request_id=generate_request_id())


@app.post("/v1/notify/{user_id}/{notification_id}/read", response_model=HermesResponse)
async def mark_read(user_id: str, notification_id: str):
    items = _memory_store.get(user_id, [])
    found = False
    for i in items:
        if i["id"] == notification_id:
            i["read"] = True
            found = True
    if _redis:
        # Redis-backed lists are rewritten wholesale on read-state change (small lists, cheap).
        raw = await _redis.lrange(f"notif:{user_id}", 0, -1)
        parsed = [json.loads(r) for r in raw]
        for p in parsed:
            if p["id"] == notification_id:
                p["read"] = True
                found = True
        if found:
            await _redis.delete(f"notif:{user_id}")
            if parsed:
                await _redis.rpush(f"notif:{user_id}", *[json.dumps(p) for p in parsed])
    if not found:
        raise HTTPException(status_code=404, detail="Notification not found")
    return HermesResponse(success=True, data={"status": "marked_read"}, request_id=generate_request_id())


@app.post("/v1/push/subscribe", response_model=HermesResponse)
async def subscribe_push(sub: PushSubscription):
    _push_subs.setdefault(sub.user_id, []).append({"endpoint": sub.endpoint, "keys": sub.keys})
    return HermesResponse(success=True, data={"status": "subscribed", "vapid_public_key": VAPID_PUBLIC_KEY}, request_id=generate_request_id())


@app.post("/v1/webhook/register", response_model=HermesResponse)
async def register_webhook(reg: WebhookRegistration):
    _webhooks.setdefault(reg.user_id, []).append(reg.url)
    return HermesResponse(success=True, data={"status": "registered"}, request_id=generate_request_id())


@app.get("/v1/push/vapid-public-key")
async def get_vapid_public_key():
    if not VAPID_PUBLIC_KEY:
        raise HTTPException(status_code=503, detail="Web Push not configured (set VAPID_PUBLIC_KEY/VAPID_PRIVATE_KEY)")
    return {"public_key": VAPID_PUBLIC_KEY}


@app.get("/v1/metrics")
async def get_metrics():
    return {
        "uptime_seconds": time.time() - _app_start_time,
        "users_with_in_app": len(_memory_store) if not _redis else "redis_backed",
        "push_subscribers": sum(len(v) for v in _push_subs.values()),
        "webhook_registrations": sum(len(v) for v in _webhooks.values()),
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8022)))
