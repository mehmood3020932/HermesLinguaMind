"""
Hermes LinguaMind — API Gateway + Auth Service
Port: 8000 | Phase 3 — Production Ready
"""

import os
import time
import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, Request, Response, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import structlog
import uvicorn

# Import shared modules
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shared.models.common import (
    HermesResponse, HealthStatus, UserCreateRequest, UserLoginRequest,
    TokenResponse, UserRole, RateLimitInfo, UserORM, LanguageCode,
)
from shared.middleware.auth import (
    get_current_user, create_access_token, create_refresh_token,
    get_password_hash, verify_password, security,
    RequestIDMiddleware, RateLimitMiddleware, AuthConfig,
)
from shared.utils.helpers import (
    generate_request_id, timing_decorator, validate_email,
    validate_password_strength, sanitize_input
)
from shared.database import get_db_session, db_healthy, init_db
from sqlalchemy import select, or_

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(20),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
)

logger = structlog.get_logger("hermes.api_gateway")

# ============================================================
# APPLICATION SETUP
# ============================================================

app = FastAPI(
    title="Hermes LinguaMind API Gateway",
    description="Central gateway for all Hermes backend services",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Users are persisted in Postgres via UserORM (shared/models/common.py) and
# shared/database.py's async session factory — no in-memory/dict store, so
# accounts survive restarts and work correctly across multiple replicas.

def _user_to_dict(user: UserORM) -> Dict[str, Any]:
    """Serialize a UserORM row to the same shape the rest of this file expects."""
    return {
        "id": str(user.id),
        "email": user.email,
        "username": user.username,
        "hashed_password": user.hashed_password,
        "display_name": user.display_name,
        "role": user.role.value if hasattr(user.role, "value") else user.role,
        "native_language": user.native_language.value if hasattr(user.native_language, "value") else user.native_language,
        "learning_language": user.learning_language.value if hasattr(user.learning_language, "value") else user.learning_language,
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "coin_balance": 0,  # authoritative balance lives in coin_ledger service, not here
    }

# Service registry
# URLs are env-var driven so this gateway works correctly both inside Docker
# Compose (container DNS names) and when run standalone (localhost). Each
# default below matches the container_name/service key in docker-compose.yml.
def _svc_url(env_key: str, host: str, port: int) -> str:
    return os.getenv(env_key, f"http://{host}:{port}")

SERVICE_REGISTRY = {
    "llm": {"url": _svc_url("LLM_SERVICE_URL", "llm_orchestration", 8001), "health": "/health"},
    "tts": {"url": _svc_url("TTS_SERVICE_URL", "tts", 8002), "health": "/health"},
    "stt": {"url": _svc_url("STT_SERVICE_URL", "stt", 8003), "health": "/health"},
    "viseme": {"url": _svc_url("VISEME_SERVICE_URL", "viseme", 8004), "health": "/health"},
    "pronunciation": {"url": _svc_url("PRONUNCIATION_SERVICE_URL", "pronunciation", 8005), "health": "/health"},
    "coin_ledger": {"url": _svc_url("COIN_LEDGER_SERVICE_URL", "coin_ledger", 8006), "health": "/health"},
    "curriculum": {"url": _svc_url("CURRICULUM_SERVICE_URL", "curriculum", 8007), "health": "/health"},
    "memory": {"url": _svc_url("MEMORY_SERVICE_URL", "memory", 8008), "health": "/health"},
    "moderation": {"url": _svc_url("MODERATION_SERVICE_URL", "moderation", 8009), "health": "/health"},
    "grammar_rule_db": {"url": _svc_url("GRAMMAR_RULE_DB_SERVICE_URL", "grammar_rule_db", 8010), "health": "/health"},
    "content_generation": {"url": _svc_url("CONTENT_GENERATION_SERVICE_URL", "content_generation", 8011), "health": "/health"},
    "personalization": {"url": _svc_url("PERSONALIZATION_SERVICE_URL", "personalization", 8012), "health": "/health"},
    "gesture_emotion": {"url": _svc_url("GESTURE_EMOTION_SERVICE_URL", "gesture_emotion", 8013), "health": "/health"},
    "leaderboard": {"url": _svc_url("LEADERBOARD_SERVICE_URL", "leaderboard", 8014), "health": "/health"},
    "social_exchange": {"url": _svc_url("SOCIAL_EXCHANGE_SERVICE_URL", "social_exchange", 8015), "health": "/health"},
    "anti_fraud": {"url": _svc_url("ANTI_FRAUD_SERVICE_URL", "anti_fraud", 8016), "health": "/health"},
    "live_conversation": {"url": _svc_url("LIVE_CONVERSATION_SERVICE_URL", "live_conversation", 8017), "health": "/health"},
    "observability": {"url": _svc_url("OBSERVABILITY_SERVICE_URL", "observability", 8018), "health": "/health"},
    "security": {"url": _svc_url("SECURITY_SERVICE_URL", "security", 8019), "health": "/health"},
    "hermes_orchestrator": {"url": _svc_url("HERMES_ORCHESTRATOR_SERVICE_URL", "hermes_orchestrator", 8020), "health": "/health"},
    "email_service": {"url": _svc_url("EMAIL_SERVICE_URL", "email_service", 8021), "health": "/health"},
    "notification_service": {"url": _svc_url("NOTIFICATION_SERVICE_URL", "notification_service", 8022), "health": "/health"},
    "avatar_service": {"url": _svc_url("AVATAR_SERVICE_URL", "avatar_service", 8023), "health": "/health"},
}

# Application start time
_app_start_time = time.time()


@app.on_event("startup")
async def _startup_checks():
    """Fail fast instead of serving traffic on a broken/insecure config."""
    AuthConfig.validate_for_production()
    if not await db_healthy():
        logger.error("startup_db_unreachable", database_url=os.getenv("DATABASE_URL", "unset"))
        raise RuntimeError(
            "Postgres is unreachable at startup — user accounts are stored there now, "
            "so the gateway cannot serve auth traffic without it. Check DATABASE_URL / "
            "that the postgres container is healthy."
        )
    # Creates users/coin_balances/memories/etc if they don't exist yet.
    # Idempotent — safe even though coin_ledger/security/memory services
    # also call this on their own startup.
    await init_db()
    logger.info("startup_checks_passed")

# ============================================================
# MIDDLEWARE
# ============================================================

@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Log all requests with timing."""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    start_time = time.time()

    logger.info(
        "request_started",
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        client_ip=request.client.host if request.client else "unknown",
    )

    try:
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000

        logger.info(
            "request_completed",
            request_id=request_id,
            status_code=response.status_code,
            latency_ms=round(process_time, 2),
        )

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(round(process_time, 3))
        return response

    except Exception as e:
        process_time = (time.time() - start_time) * 1000
        logger.error(
            "request_failed",
            request_id=request_id,
            error=str(e),
            latency_ms=round(process_time, 2),
        )
        raise

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health", response_model=HealthStatus)
async def health_check():
    """Gateway health check endpoint."""
    uptime = time.time() - _app_start_time

    # Check downstream services
    dependencies = {}
    import httpx
    for service_name, config in SERVICE_REGISTRY.items():
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(f"{config['url']}{config['health']}")
                dependencies[service_name] = "healthy" if response.status_code == 200 else "degraded"
        except Exception:
            dependencies[service_name] = "unreachable"

    return HealthStatus(
        status="healthy",
        service="api_gateway",
        version="3.0.0",
        timestamp=datetime.utcnow(),
        uptime_seconds=uptime,
        dependencies=dependencies,
    )

# ============================================================
# AUTHENTICATION ENDPOINTS
# ============================================================

@app.post("/v1/auth/register", response_model=HermesResponse)
async def register_user(request: Request, user_data: UserCreateRequest):
    """Register a new user."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))

    # Validate email
    if not validate_email(user_data.email):
        return HermesResponse(
            success=False,
            error="Invalid email format",
            error_code="INVALID_EMAIL",
            request_id=request_id,
        )

    # Validate password
    is_strong, issues = validate_password_strength(user_data.password)
    if not is_strong:
        return HermesResponse(
            success=False,
            error="; ".join(issues),
            error_code="WEAK_PASSWORD",
            request_id=request_id,
        )

    # Check if user exists (case-insensitive on both email and username)
    async with get_db_session() as db:
        existing = await db.execute(
            select(UserORM).where(
                or_(UserORM.email == user_data.email, UserORM.username == user_data.username)
            )
        )
        if existing.scalar_one_or_none() is not None:
            return HermesResponse(
                success=False,
                error="User already exists",
                error_code="USER_EXISTS",
                request_id=request_id,
            )

        # Create user
        new_user = UserORM(
            email=user_data.email,
            username=user_data.username,
            hashed_password=get_password_hash(user_data.password),
            display_name=user_data.display_name or user_data.username,
            role=UserRole.LEARNER,
            native_language=user_data.native_language,
            learning_language=user_data.learning_language,
            date_of_birth=user_data.date_of_birth,
            country_code=user_data.country_code,
            is_active=True,
            is_verified=False,
        )
        db.add(new_user)
        await db.flush()  # populate new_user.id before we use it below
        user_id = str(new_user.id)
        user_record = _user_to_dict(new_user)

    logger.info("user_registered", user_id=user_id, email=user_data.email)

    # Issue tokens immediately so registering also logs the user in
    # (matches the mobile app's expectation of a full AuthResponse with
    # access_token/refresh_token/user coming back from /v1/auth/register).
    token_data = {"sub": user_id, "username": user_record["username"], "role": user_record["role"]}
    access_token = create_access_token(token_data)
    refresh_token_value = create_refresh_token(token_data)

    return HermesResponse(
        success=True,
        data={
            "access_token": access_token,
            "refresh_token": refresh_token_value,
            "token_type": "bearer",
            "expires_in": 1800,
            "user": {
                "id": user_id,
                "email": user_record["email"],
                "username": user_record["username"],
                "display_name": user_record["display_name"],
                "native_language": user_record["native_language"],
                "target_language": user_record["learning_language"],
                "coins": user_record["coin_balance"],
                "xp": 0,
                "streak_days": 0,
            },
        },
        request_id=request_id,
    )


@app.post("/v1/auth/login", response_model=HermesResponse)
async def login_user(request: Request, login_data: UserLoginRequest):
    """Authenticate user and return tokens."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))

    # Find user by username OR email — the app may send either under
    # `username` (see login_data.username).
    async with get_db_session() as db:
        result = await db.execute(
            select(UserORM).where(
                or_(UserORM.username == login_data.username, UserORM.email == login_data.username)
            )
        )
        user_orm = result.scalar_one_or_none()
        user = _user_to_dict(user_orm) if user_orm else None

        if not user or not verify_password(login_data.password, user["hashed_password"]):
            return HermesResponse(
                success=False,
                error="Invalid credentials",
                error_code="INVALID_CREDENTIALS",
                request_id=request_id,
            )

        if not user.get("is_active", True):
            return HermesResponse(
                success=False,
                error="Account deactivated",
                error_code="ACCOUNT_DEACTIVATED",
                request_id=request_id,
            )

        user_orm.last_login = datetime.utcnow()

    # Generate tokens
    token_data = {
        "sub": user["id"],
        "username": user["username"],
        "role": user["role"],
    }

    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    logger.info("user_login", user_id=user["id"], username=user["username"])

    return HermesResponse(
        success=True,
        data={
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": 1800,
            "user": {
                "id": user["id"],
                "email": user["email"],
                "username": user["username"],
                "display_name": user["display_name"],
                "native_language": user["native_language"],
                "target_language": user["learning_language"],
                "coins": user["coin_balance"],
                "xp": 0,
                "streak_days": 0,
            },
        },
        request_id=request_id,
    )


class RefreshTokenRequest(BaseModel):
    refresh_token: str


@app.post("/v1/auth/refresh", response_model=HermesResponse)
async def refresh_token(request: Request, body: RefreshTokenRequest):
    """Refresh access token.

    Takes the refresh token from the JSON body, NOT the Authorization
    header. That header is reserved for the access token everywhere else
    in this API (and the mobile client's HTTP interceptor auto-attaches
    whatever access token it has stored to every outgoing request,
    including this one) — requiring the refresh token there too creates
    an unresolvable collision: the client can't put two different tokens
    in the same header, and by the time this endpoint is called the
    access token is usually the very one that just expired. Body-based
    is also what every mobile/web client already expects for a refresh
    call.
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    refresh_token_str = body.refresh_token

    from jose import jwt
    from shared.middleware.auth import AuthConfig
    try:
        payload = jwt.decode(refresh_token_str, AuthConfig.SECRET_KEY, algorithms=[AuthConfig.ALGORITHM])
        if payload.get("type") != "refresh":
            raise ValueError("Not a refresh token")

        token_data = {
            "sub": payload["sub"],
            "username": payload.get("username"),
            "role": payload.get("role"),
        }

        new_access_token = create_access_token(token_data)
        # Rotate the refresh token too — the client stores whatever comes
        # back here as its new refresh token, so this endpoint must
        # return one (previously it didn't, which would have broken the
        # client's own storage step even after the header/body fix above).
        new_refresh_token = create_refresh_token(token_data)

        return HermesResponse(
            success=True,
            data={
                "access_token": new_access_token,
                "refresh_token": new_refresh_token,
                "token_type": "bearer",
                "expires_in": 1800,
            },
            request_id=request_id,
        )

    except Exception as e:
        logger.warning("token_refresh_failed", error=str(e))
        return HermesResponse(
            success=False,
            error="Invalid refresh token",
            error_code="INVALID_TOKEN",
            request_id=request_id,
        )


@app.get("/v1/auth/me", response_model=HermesResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current user profile."""
    async with get_db_session() as db:
        result = await db.execute(
            select(UserORM).where(UserORM.id == current_user["user_id"])
        )
        user_orm = result.scalar_one_or_none()
        if not user_orm:
            raise HTTPException(status_code=404, detail="User not found")
        user = _user_to_dict(user_orm)

    return HermesResponse(
        success=True,
        data={
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "display_name": user["display_name"],
            "role": user["role"],
            "native_language": user["native_language"],
            "target_language": user["learning_language"],
            "coins": user["coin_balance"],
            "xp": 0,
            "streak_days": 0,
        },
    )


# ============================================================
# HERMES ORCHESTRATOR — CONVENIENCE ALIAS
# ============================================================

@app.post("/v1/chat")
async def chat_via_orchestrator(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Convenience alias that forwards to the Hermes Orchestrator's
    /v1/orchestrate endpoint (multi-service intent → plan → execute → verify
    pipeline). Equivalent to POST /v1/hermes_orchestrator/orchestrate.

    The orchestrator's own HermesResponse (phase4/shared) returns its
    payload flat at the top level (text, emotion, gesture, coins_awarded,
    ...) rather than nested under a `data` key. The mobile app's ChatResponse
    model expects the gateway's usual `{success, request_id, data: {...},
    error}` envelope, matching every other endpoint, so we translate here
    rather than raw byte-passthrough.
    """
    import json

    import httpx

    target_url = f"{SERVICE_REGISTRY['hermes_orchestrator']['url']}/v1/orchestrate"
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    headers = {
        "X-User-ID": str(current_user["user_id"]),
        "X-Request-ID": request_id,
        "Content-Type": "application/json",
    }

    # The mobile app's ChatRequest sends `{user_id, message, session_context}`
    # where session_context is a flat dict of learning-context fields
    # (native_language, target_language, cefr_level, ...). The orchestrator's
    # SessionContext model requires its own `user_id` and only reads
    # arbitrary caller context back out through `custom_params`, so we
    # translate the shape here rather than passing the mobile app's body
    # straight through (which would 422 against the orchestrator's schema).
    try:
        incoming = json.loads(await request.body())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    user_id = incoming.get("user_id") or str(current_user["user_id"])
    orchestrator_payload = {
        "user_id": user_id,
        "message": incoming.get("message", ""),
        "session_context": {
            "user_id": user_id,
            "custom_params": incoming.get("session_context") or {},
        },
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                target_url,
                headers=headers,
                content=json.dumps(orchestrator_payload),
            )
    except httpx.RequestError as e:
        logger.error("orchestrator_proxy_error", error=str(e))
        raise HTTPException(status_code=503, detail="Hermes Orchestrator unavailable")

    if response.status_code >= 400:
        return JSONResponse(
            status_code=response.status_code,
            content=HermesResponse(
                success=False,
                error="Hermes Orchestrator returned an error",
                error_code="ORCHESTRATOR_ERROR",
                request_id=request_id,
            ).model_dump(mode="json"),
        )

    try:
        orch = response.json()
    except ValueError:
        return HermesResponse(
            success=False,
            error="Orchestrator returned a non-JSON response",
            error_code="ORCHESTRATOR_BAD_RESPONSE",
            request_id=request_id,
        )

    # `emotion` (neutral/happy/sad/excited/encouraging/...) is what the
    # companion character's on-screen expression is actually driven by —
    # map it into the `gesture` field the mobile app reads for that.
    return HermesResponse(
        success=orch.get("success", True),
        request_id=orch.get("request_id", request_id),
        error=orch.get("error_message"),
        data={
            "text": orch.get("text") or "",
            "audio_url": orch.get("audio_url"),
            "viseme_timeline": orch.get("viseme_timeline") or [],
            "gesture": (orch.get("emotion") or "neutral").upper(),
            "coins_awarded": orch.get("coins_awarded", 0),
        },
    )


# ============================================================
# MOBILE APP BRIDGE — STT / TTS / LEADERBOARD / SOCIAL
# ============================================================
# The Flutter app calls single-segment paths (e.g. POST /v1/stt,
# GET /v1/leaderboard) that don't fit the generic `/v1/{service}/{path}`
# proxy below (which needs two path segments). These routes bridge those
# exact calls to the real downstream services, translating request/response
# shapes where the mobile app's contract differs from the service's own
# (different field names, envelope nesting, or even HTTP verb/body vs
# query-param conventions).

from fastapi import UploadFile, File


@app.post("/v1/stt")
async def mobile_stt(
    audio: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """Bridges the mobile app's multipart audio upload (field name
    `audio`) to the STT service's JSON+base64 `/v1/transcribe` contract."""
    import base64

    import httpx

    raw = await audio.read()
    audio_b64 = base64.b64encode(raw).decode("utf-8")
    fmt = (audio.filename or "recording.m4a").rsplit(".", 1)[-1].lower()

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{SERVICE_REGISTRY['stt']['url']}/v1/transcribe",
                json={"audio_base64": audio_b64, "format": fmt},
            )
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="STT service unavailable")

    body = resp.json()
    if not body.get("success"):
        raise HTTPException(status_code=502, detail=body.get("error", "STT failed"))

    data = body.get("data") or {}
    return {"text": data.get("text", ""), "confidence": data.get("confidence")}


class _MobileTTSRequest(BaseModel):
    text: str
    voice: Optional[str] = "en-US-AriaNeural"


@app.post("/v1/tts")
async def mobile_tts(
    payload: _MobileTTSRequest,
    current_user: dict = Depends(get_current_user),
):
    """Bridges the mobile app's `{text, voice}` request to the real TTS
    service, and reshapes its `phoneme_timings` (viseme/start_time/end_time)
    into the `{time, viseme}` viseme_timeline the companion's lip-sync
    animation expects."""
    import httpx

    lang = (payload.voice or "en").split("-")[0].lower() or "en"

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{SERVICE_REGISTRY['tts']['url']}/v1/synthesize",
                json={"text": payload.text, "language": lang},
            )
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="TTS service unavailable")

    body = resp.json()
    if not body.get("success"):
        raise HTTPException(status_code=502, detail=body.get("error", "TTS failed"))

    data = body.get("data") or {}
    viseme_timeline = [
        {"time": t.get("start_time", 0.0), "viseme": t.get("viseme", "sil")}
        for t in data.get("phoneme_timings", [])
    ]
    return {
        "audio_base64": data.get("audio_base64", ""),
        "viseme_timeline": viseme_timeline,
    }


@app.get("/v1/leaderboard")
async def mobile_leaderboard(
    period: str = "weekly",
    page: int = 1,
    page_size: int = 20,
    current_user: dict = Depends(get_current_user),
):
    import httpx

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{SERVICE_REGISTRY['leaderboard']['url']}/v1/leaderboard",
                json={"period": period, "page": page, "page_size": page_size},
            )
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Leaderboard service unavailable")

    body = resp.json()
    if not body.get("success"):
        raise HTTPException(status_code=502, detail=body.get("error", "Leaderboard failed"))
    data = body.get("data") or {}

    entries = []
    for e in data.get("entries", []):
        entries.append(
            {
                "rank": e.get("rank", 0),
                "user_id": e.get("user_id", ""),
                "username": e.get("username", e.get("user_id", "")),
                "display_name": e.get("display_name", e.get("username", e.get("user_id", ""))),
                # NOTE: the leaderboard service is an in-memory demo store
                # that only tracks a bare `score` per user — it isn't
                # joined against real user profiles yet, so username/
                # display_name/avatar will fall back to the raw user_id
                # until that service is backed by the real user table.
                "xp": e.get("score", 0),
                "streak_days": e.get("streak_days", 0),
                "avatar_url": e.get("avatar_url"),
                "is_current_user": str(e.get("user_id")) == str(current_user["user_id"]),
                "rank_change": e.get("rank_change", 0),
            }
        )

    return {
        "entries": entries,
        "total_count": data.get("total_participants", len(entries)),
        "current_user_rank": data.get("user_rank") or 0,
        "period": period,
    }


@app.post("/v1/submit-score")
async def mobile_submit_score(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    import json

    import httpx

    try:
        payload = json.loads(await request.body())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    user_id = payload.get("user_id") or str(current_user["user_id"])
    xp = payload.get("xp", 0)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{SERVICE_REGISTRY['leaderboard']['url']}/v1/submit-score",
                params={"user_id": user_id, "scope": "global", "score": xp},
            )
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Leaderboard service unavailable")

    body = resp.json()
    if not body.get("success"):
        raise HTTPException(status_code=502, detail=body.get("error", "Submit score failed"))
    return {"status": "submitted"}


@app.post("/v1/match")
async def mobile_match(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    import json

    import httpx

    try:
        payload = json.loads(await request.body())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{SERVICE_REGISTRY['social_exchange']['url']}/v1/match",
                json={
                    "user_id": str(current_user["user_id"]),
                    "native_language": payload.get("native_language", "en"),
                    "target_language": payload.get("target_language", "en"),
                },
            )
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Social service unavailable")

    body = resp.json()
    if not body.get("success"):
        raise HTTPException(status_code=502, detail=body.get("error", "Match failed"))
    data = body.get("data") or {}
    matches = data.get("matches") or []
    top = matches[0] if matches else {}

    def _profile(p: dict) -> dict:
        return {
            "user_id": p.get("user_id", ""),
            "username": p.get("username", p.get("user_id", "")),
            "display_name": p.get("display_name", p.get("username", "")),
            "avatar_url": p.get("avatar_url"),
            "bio": p.get("bio"),
            "xp": p.get("xp", 0),
            "streak_days": p.get("streak_days", 0),
            "languages": p.get("languages", []),
            "is_online": p.get("is_online", False),
            "last_active": p.get("last_active"),
        }

    return {
        "match_id": top.get("user_id", ""),
        "partner": _profile(top),
        "common_languages": top.get("common_languages", []),
        "compatibility_score": top.get("score", 0),
    }


@app.get("/v1/profile/{user_id}")
async def mobile_get_profile(
    user_id: str,
    current_user: dict = Depends(get_current_user),
):
    import httpx

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                f"{SERVICE_REGISTRY['social_exchange']['url']}/v1/profile/{user_id}"
            )
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Social service unavailable")

    if resp.status_code == 404:
        raise HTTPException(status_code=404, detail="Profile not found")

    body = resp.json()
    if not body.get("success"):
        raise HTTPException(status_code=502, detail=body.get("error", "Get profile failed"))
    data = body.get("data") or {}
    return {
        "user_id": data.get("user_id", user_id),
        "username": data.get("username", user_id),
        "display_name": data.get("display_name", data.get("username", user_id)),
        "avatar_url": data.get("avatar_url"),
        "bio": data.get("bio"),
        "xp": data.get("xp", 0),
        "streak_days": data.get("streak_days", 0),
        "languages": data.get("languages", []),
        "is_online": data.get("is_online", False),
        "last_active": data.get("last_active"),
    }


@app.post("/v1/report")
async def mobile_report(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    import json

    import httpx

    try:
        payload = json.loads(await request.body())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{SERVICE_REGISTRY['social_exchange']['url']}/v1/report",
                params={
                    "reporter_id": str(current_user["user_id"]),
                    "reported_id": payload.get("user_id", ""),
                    "reason": payload.get("reason", "unspecified"),
                },
            )
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Social service unavailable")

    body = resp.json()
    if not body.get("success"):
        raise HTTPException(status_code=502, detail=body.get("error", "Report failed"))
    return {"status": "reported"}


# ============================================================
# SERVICE ROUTING / PROXY
# ============================================================

@app.api_route("/v1/{service}/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_to_service(
    service: str,
    path: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Proxy requests to downstream services."""
    if service not in SERVICE_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Service '{service}' not found")

    service_config = SERVICE_REGISTRY[service]
    target_url = f"{service_config['url']}/v1/{path}"

    import httpx

    method = request.method
    headers = dict(request.headers)
    headers["X-User-ID"] = str(current_user["user_id"])
    headers["X-Request-ID"] = getattr(request.state, "request_id", str(uuid.uuid4()))

    body = await request.body()

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method=method,
                url=target_url,
                headers=headers,
                content=body,
                params=dict(request.query_params),
            )

            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers),
            )
    except httpx.RequestError as e:
        logger.error("proxy_error", service=service, error=str(e))
        raise HTTPException(status_code=503, detail=f"Service '{service}' unavailable")


# ============================================================
# RATE LIMIT INFO
# ============================================================

@app.get("/v1/rate-limit", response_model=HermesResponse)
async def get_rate_limit_info(request: Request):
    """Get current rate limit status."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))

    return HermesResponse(
        success=True,
        data=RateLimitInfo(
            limit=100,
            remaining=95,
            reset_at=datetime.utcnow() + timedelta(minutes=1),
            window="1 minute",
        ).model_dump(),
        request_id=request_id,
    )


# ============================================================
# SERVICE DISCOVERY
# ============================================================

@app.get("/v1/services", response_model=HermesResponse)
async def list_services():
    """List all available services."""
    return HermesResponse(
        success=True,
        data={
            "services": [
                {
                    "name": name,
                    "url": config["url"],
                    "health_endpoint": config["health"],
                }
                for name, config in SERVICE_REGISTRY.items()
            ],
            "total": len(SERVICE_REGISTRY),
        },
    )


# ============================================================
# ERROR HANDLERS
# ============================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    return JSONResponse(
        status_code=exc.status_code,
        content=HermesResponse(
            success=False,
            error=exc.detail,
            error_code=f"HTTP_{exc.status_code}",
            request_id=request_id,
        ).model_dump(mode="json"),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    logger.error("unhandled_exception", request_id=request_id, error=str(exc), exc_info=True)
    return JSONResponse(
        status_code=500,
        content=HermesResponse(
            success=False,
            error="Internal server error",
            error_code="INTERNAL_ERROR",
            request_id=request_id,
        ).model_dump(mode="json"),
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
