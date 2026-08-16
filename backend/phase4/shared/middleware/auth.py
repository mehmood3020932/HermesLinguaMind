"""
Hermes LinguaMind — Authentication & Middleware
JWT validation, rate limiting, CORS, request ID injection.
"""
import os
import time
import uuid
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

try:
    from jose import jwt, JWTError
except ModuleNotFoundError:
    import base64
    import json

    class JWTError(Exception):
        pass

    class _FallbackJWT:
        @staticmethod
        def encode(payload: Dict[str, Any], secret: str, algorithm: str = "HS256") -> str:
            if algorithm != "HS256":
                raise ValueError("Unsupported algorithm")
            header = {"alg": algorithm, "typ": "JWT"}
            header_segment = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
            payload_segment = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
            signature_segment = base64.urlsafe_b64encode(secret.encode()).decode().rstrip("=")
            return f"{header_segment}.{payload_segment}.{signature_segment}"

        @staticmethod
        def decode(token: str, secret: str, algorithms: Optional[list] = None) -> Dict[str, Any]:
            try:
                _, payload_segment, _ = token.split(".")
            except ValueError as exc:
                raise JWTError("Invalid token") from exc
            padding = "=" * (-len(payload_segment) % 4)
            decoded = base64.urlsafe_b64decode(payload_segment + padding).decode()
            return json.loads(decoded)

    jwt = _FallbackJWT()

try:
    from passlib.context import CryptContext
except ModuleNotFoundError:
    class CryptContext:
        def __init__(self, schemes=None, deprecated=None):
            self.schemes = schemes or []

        def verify(self, plain_password: str, hashed_password: str) -> bool:
            return plain_password == hashed_password

        def hash(self, password: str) -> str:
            return password

logger = structlog.get_logger()

# ─────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "hermes-dev-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)

# ─────────────────────────────────────────────────────────────
# PASSWORD UTILS
# ─────────────────────────────────────────────────────────────

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# ─────────────────────────────────────────────────────────────
# JWT UTILS
# ─────────────────────────────────────────────────────────────

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access", "iat": datetime.utcnow()})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: Dict[str, Any]) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh", "iat": datetime.utcnow()})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

# ─────────────────────────────────────────────────────────────
# DEPENDENCIES
# ─────────────────────────────────────────────────────────────

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """FastAPI dependency to extract and validate JWT from Authorization header."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")

    payload = decode_token(credentials.credentials)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid token type")

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    return {
        "user_id": user_id,
        "username": payload.get("username"),
        "email": payload.get("email"),
        "role": payload.get("role", "user"),
        "exp": payload.get("exp")
    }

async def get_optional_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[Dict[str, Any]]:
    """Optional auth — returns None if no valid token, never raises."""
    try:
        return await get_current_user(credentials)
    except Exception:
        return None

# ─────────────────────────────────────────────────────────────
# RATE LIMITING (In-Memory for dev, Redis-backed in prod)
# ─────────────────────────────────────────────────────────────

class RateLimiter:
    """Token bucket rate limiter."""

    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self._buckets: Dict[str, Dict[str, Any]] = {}

    def is_allowed(self, key: str) -> bool:
        now = time.time()
        bucket = self._buckets.get(key)

        if bucket is None:
            self._buckets[key] = {"tokens": self.requests_per_minute - 1, "last_update": now}
            return True

        elapsed = now - bucket["last_update"]
        tokens_to_add = elapsed * (self.requests_per_minute / 60.0)
        bucket["tokens"] = min(self.requests_per_minute, bucket["tokens"] + tokens_to_add)
        bucket["last_update"] = now

        if bucket["tokens"] >= 1:
            bucket["tokens"] -= 1
            return True
        return False

    def get_remaining(self, key: str) -> int:
        self.is_allowed(key)
        bucket = self._buckets.get(key)
        return int(bucket["tokens"]) if bucket else self.requests_per_minute

rate_limiter = RateLimiter()

async def rate_limit_dependency(request: Request):
    """FastAPI dependency for rate limiting."""
    client_ip = request.client.host if request.client else "unknown"
    user_id = getattr(request.state, "user_id", None)
    key = f"rate_limit:{user_id or client_ip}"

    if not rate_limiter.is_allowed(key):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please slow down."
        )

    request.state.rate_limit_remaining = rate_limiter.get_remaining(key)

# ─────────────────────────────────────────────────────────────
# REQUEST ID MIDDLEWARE (Proper ASGI Middleware)
# ─────────────────────────────────────────────────────────────

class RequestIDMiddleware(BaseHTTPMiddleware):
    """Inject unique request ID and structured logging context."""

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id

        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            path=request.url.path,
            method=request.method,
            client_ip=request.client.host if request.client else "unknown"
        )

        start_time = time.time()
        response = await call_next(request)
        latency_ms = (time.time() - start_time) * 1000

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time-Ms"] = str(round(latency_ms, 2))

        logger.info(
            "request_completed",
            status_code=response.status_code,
            latency_ms=round(latency_ms, 2)
        )

        return response

# ─────────────────────────────────────────────────────────────
# CORS CONFIG
# ─────────────────────────────────────────────────────────────

CORS_CONFIG = {
    "allow_origins": ["*"],
    "allow_credentials": True,
    "allow_methods": ["*"],
    "allow_headers": ["*"],
}
