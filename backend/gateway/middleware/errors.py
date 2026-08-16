"""Global exception handlers — no raw 500s leak to clients."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from gateway.logging_config import get_logger

logger = get_logger("hermes.errors")


def _error_body(
    *,
    code: str,
    message: str,
    request_id: str | None = None,
    details: Any = None,
) -> Dict[str, Any]:
    body: Dict[str, Any] = {
        "success": False,
        "error": {
            "code": code,
            "message": message,
        },
    }
    if request_id:
        body["request_id"] = request_id
    if details is not None:
        body["error"]["details"] = details
    return body


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError):
        request_id = getattr(request.state, "request_id", None)
        logger.warning(
            "validation_error",
            path=str(request.url.path),
            errors=exc.errors(),
            request_id=request_id,
        )
        return JSONResponse(
            status_code=422,
            content=_error_body(
                code="VALIDATION_ERROR",
                message="Request validation failed",
                request_id=request_id,
                details=exc.errors(),
            ),
        )

    @app.exception_handler(HTTPException)
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        request_id = getattr(request.state, "request_id", None)
        logger.warning(
            "http_error",
            path=str(request.url.path),
            status=exc.status_code,
            detail=str(exc.detail),
            request_id=request_id,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body(
                code="HTTP_ERROR",
                message=str(exc.detail),
                request_id=request_id,
            ),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        request_id = getattr(request.state, "request_id", None)
        logger.exception(
            "unhandled_error",
            path=str(request.url.path),
            error=str(exc),
            request_id=request_id,
        )
        return JSONResponse(
            status_code=500,
            content=_error_body(
                code="INTERNAL_ERROR",
                message="An unexpected error occurred",
                request_id=request_id,
            ),
        )
