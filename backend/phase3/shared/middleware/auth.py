"""
Hermes LinguaMind — Authentication & Authorization Middleware
Phase 3 — Production Ready
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional, List
from uuid import UUID

from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
import structlog

logger = structlog.get_logger("hermes.auth")

# Password hashing
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

# Security scheme
security = HTTPBearer(auto_error=False)


class AuthConfig:
    """Authentication configuration.

    SECRET_KEY MUST come from the environment in any real deployment —
    docker-compose.yml already sets SECRET_KEY for the backend container.
    The literal string below is only a local-dev fallback (and is
    intentionally obvious/invalid-looking) so a misconfigured deployment
    fails loudly in review rather than silently signing tokens with a
    secret that's sitting in this public repo.
    """
    SECRET_KEY: str = os.getenv("SECRET_KEY", "INSECURE-DEV-ONLY-SET-SECRET_KEY-ENV-VAR")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    @classmethod
    def validate_for_production(cls) -> None:
        """Call at startup: refuse to run in production with a weak/default secret."""
        env = os.getenv("ENVIRONMENT", "development")
        if env == "production" and (
            cls.SECRET_KEY == "INSECURE-DEV-ONLY-SET-SECRET_KEY-ENV-VAR"
            or len(cls.SECRET_KEY) < 32
        ):
            raise RuntimeError(
                "SECRET_KEY is missing or too short for a production deployment. "
                "Set a real random 32+ char SECRET_KEY in the environment before starting."
            )


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a plain password."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=AuthConfig.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, AuthConfig.SECRET_KEY, algorithm=AuthConfig.ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create a JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=AuthConfig.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, AuthConfig.SECRET_KEY, algorithm=AuthConfig.ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, AuthConfig.SECRET_KEY, algorithms=[AuthConfig.ALGORITHM])
        return payload
    except JWTError as e:
        logger.warning("token_decode_failed", error=str(e))
        return None


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> dict:
    """
    Extract and validate the current user from the request.

    Args:
        request: FastAPI request object
        credentials: HTTP Bearer credentials, resolved by FastAPI via the
            `security` (HTTPBearer) scheme above — NOT a request-body field.
            (Previously this had a plain `= None` default instead of
            `= Depends(security)`. Since HTTPAuthorizationCredentials is a
            Pydantic model, FastAPI interpreted that as a body parameter to
            embed rather than a security dependency to resolve from the
            Authorization header. It "worked" by accident for any endpoint
            using only `Depends(get_current_user)` with no other body model,
            because the manual header-parsing fallback below always ended up
            doing the real work — but it silently broke any endpoint that
            *also* needed a real JSON body: FastAPI would then require the
            body wrapped as {"body": {...}, "credentials": ...} instead of
            just the plain JSON the caller sends.)

    Returns:
        Dict containing user information

    Raises:
        HTTPException: If authentication fails
    """
    # Prefer what the HTTPBearer scheme resolved; keep the manual header
    # parse only as a defensive fallback (e.g. a client sending the header
    # in a way HTTPBearer's parser doesn't recognize).
    token = None
    if credentials:
        token = credentials.credentials
    else:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    # Add request ID for tracing
    request_id = getattr(request.state, "request_id", None)

    return {
        "user_id": UUID(user_id),
        "username": payload.get("username"),
        "role": payload.get("role", "learner"),
        "request_id": request_id,
    }


class RoleChecker:
    """Role-based access control checker."""

    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    async def __call__(self, user: dict = None) -> dict:
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
            )

        if user.get("role") not in self.allowed_roles:
            logger.warning(
                "access_denied",
                user_id=str(user.get("user_id")),
                required_roles=self.allowed_roles,
                actual_role=user.get("role"),
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )

        return user


# Predefined role checkers
require_admin = RoleChecker(["admin"])
require_moderator = RoleChecker(["moderator", "admin"])
require_native_speaker = RoleChecker(["native_speaker", "moderator", "admin"])


class RateLimitMiddleware:
    """Rate limiting middleware."""

    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        self.app = app
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._store = {}

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive)
            client_ip = request.client.host if request.client else "unknown"

            # Simple in-memory rate limiting (use Redis in production)
            import time
            now = time.time()
            window_start = now - self.window_seconds

            if client_ip not in self._store:
                self._store[client_ip] = []

            self._store[client_ip] = [t for t in self._store[client_ip] if t > window_start]

            if len(self._store[client_ip]) >= self.max_requests:
                response = HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded",
                )
                await send({
                    "type": "http.response.start",
                    "status": 429,
                    "headers": [[b"content-type", b"application/json"]],
                })
                await send({
                    "type": "http.response.body",
                    "body": b'{"error":"Rate limit exceeded"}',
                })
                return

            self._store[client_ip].append(now)

        await self.app(scope, receive, send)


class RequestIDMiddleware:
    """Add unique request ID to each request for tracing."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            import uuid
            request_id = str(uuid.uuid4())
            scope["request_id"] = request_id

            # Add request ID to response headers
            original_send = send

            async def send_with_request_id(message):
                if message["type"] == "http.response.start":
                    headers = message.get("headers", [])
                    headers.append([b"X-Request-ID", request_id.encode()])
                    message["headers"] = headers
                await original_send(message)

            await self.app(scope, receive, send_with_request_id)
        else:
            await self.app(scope, receive, send)


class CORSMiddleware:
    """Custom CORS middleware."""

    def __init__(self, app, allow_origins: List[str], allow_methods: List[str] = None, allow_headers: List[str] = None):
        self.app = app
        self.allow_origins = allow_origins
        self.allow_methods = allow_methods or ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        self.allow_headers = allow_headers or ["*"]

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive)
            origin = request.headers.get("origin", "")

            if origin in self.allow_origins or "*" in self.allow_origins:
                if request.method == "OPTIONS":
                    await send({
                        "type": "http.response.start",
                        "status": 200,
                        "headers": [
                            [b"access-control-allow-origin", origin.encode()],
                            [b"access-control-allow-methods", ", ".join(self.allow_methods).encode()],
                            [b"access-control-allow-headers", ", ".join(self.allow_headers).encode()],
                            [b"access-control-max-age", b"600"],
                        ],
                    })
                    await send({"type": "http.response.body", "body": b""})
                    return

                original_send = send

                async def send_with_cors(message):
                    if message["type"] == "http.response.start":
                        headers = message.get("headers", [])
                        headers.append([b"access-control-allow-origin", origin.encode()])
                        message["headers"] = headers
                    await original_send(message)

                await self.app(scope, receive, send_with_cors)
                return

        await self.app(scope, receive, send)


print("✅ shared/middleware/auth.py created")
