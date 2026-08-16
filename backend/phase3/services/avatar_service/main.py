"""
Hermes LinguaMind — Avatar Service
Port: 8023 | Phase 3

Real adapter in front of a self-hosted OpenTalking instance
(https://github.com/datascale-ai/opentalking, Apache-2.0). This is the piece
the master spec called "OpenTalking Real Avatar" — it did not exist before
this file: only a phoneme->viseme timeline generator (services/viseme)
existed, with nothing driving an actual avatar renderer or WebRTC session.

What this service does and does NOT do
---------------------------------------
OpenTalking's own docs are explicit that "user authentication and account
management" are OUT OF SCOPE for OpenTalking and should be handled by an
"upstream gateway" — that's this service. So:

  - We own: auth (every route requires a valid Hermes JWT), which
    character/persona a user may address, and a server-side record of every
    session (AvatarSessionORM) so a client can never claim a session that
    doesn't belong to it.
  - OpenTalking owns: the actual LLM turn, TTS, lip-sync rendering, and the
    WebRTC media session. We proxy /sessions and /speak and /interrupt to
    it over plain HTTP — we do NOT re-implement WebRTC signaling or touch
    audio/video bytes ourselves; that would just be a slower, buggier copy
    of what OpenTalking already does correctly.
  - The client (Flutter app) still needs to open the WebRTC connection
    directly against OpenTalking's own api container using the session id
    we hand back (see AVATAR_INTEGRATION.md — this is the one piece that
    is NOT done here, because it requires flutter_webrtc in the mobile app,
    which is a separate, larger change outside this backend-only session).

Speech input: rather than also configuring OpenTalking's STT provider
(which defaults to a paid DashScope endpoint), voice messages are
transcribed with Hermes's own free/self-hosted faster-whisper STT service
first, then sent to OpenTalking as text via /speak. One STT stack, not two.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import time
from datetime import datetime
from typing import Optional, Any, Dict
from uuid import UUID

import httpx
import structlog
import uvicorn
from fastapi import FastAPI, Request, HTTPException, Depends, UploadFile, File
from pydantic import BaseModel, Field
from sqlalchemy import select

from shared.models.common import HermesResponse, HealthStatus, AvatarCharacterORM, AvatarSessionORM
from shared.middleware.auth import get_current_user
from shared.utils.helpers import generate_request_id
from shared.database import get_db_session, db_healthy, init_db

logger = structlog.get_logger("hermes.avatar")
app = FastAPI(title="Hermes Avatar Service", version="3.1.0")
_app_start_time = time.time()

# Internal docker-network URL of OpenTalking's `api` container (see
# docker-compose.yml, `avatar` profile). NOT the public-facing URL — the
# client's WebRTC connection goes straight to OpenTalking, not through us.
OPENTALKING_API_URL = os.getenv("OPENTALKING_API_INTERNAL_URL", "http://avatar_api:8000")
# What we hand back to the client so IT can reach OpenTalking directly for
# WebRTC/SSE. In production this should be the public hostname behind
# nginx's /avatar-api/ proxy (see nginx/nginx.conf), not a container name.
OPENTALKING_PUBLIC_URL = os.getenv("OPENTALKING_API_PUBLIC_URL", "/avatar-api")
STT_SERVICE_URL = os.getenv("STT_SERVICE_URL", "http://localhost:8003")

_http = httpx.AsyncClient(timeout=15.0)


@app.on_event("startup")
async def _startup():
    await init_db()


@app.get("/health", response_model=HealthStatus)
async def health_check():
    """Reports 'degraded' (not 'unhealthy') when OpenTalking is unreachable —
    the rest of Hermes (curriculum, chat, gamification) works fine without
    it; only avatar sessions are unavailable."""
    is_db_healthy = await db_healthy()
    opentalking_reachable = False
    try:
        resp = await _http.get(f"{OPENTALKING_API_URL}/health", timeout=3.0)
        opentalking_reachable = resp.status_code < 500
    except Exception:
        opentalking_reachable = False

    status = "healthy" if (is_db_healthy and opentalking_reachable) else "degraded"
    uptime = time.time() - _app_start_time
    return HealthStatus(
        status=status, service="avatar_service", version="3.1.0",
        timestamp=datetime.utcnow(), uptime_seconds=uptime,
    )


class CreateSessionRequest(BaseModel):
    character_slug: str = Field(..., description="e.g. 'hermes-default', 'maria-spanish-tutor'")


class SpeakRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)


async def _get_character(db, slug: str) -> AvatarCharacterORM:
    result = await db.execute(
        select(AvatarCharacterORM).where(
            AvatarCharacterORM.slug == slug, AvatarCharacterORM.is_active == True  # noqa: E712
        )
    )
    character = result.scalar_one_or_none()
    if not character:
        raise HTTPException(status_code=404, detail=f"No active avatar character '{slug}'")
    return character


async def _get_owned_session(db, session_id: UUID, user_id: str) -> AvatarSessionORM:
    result = await db.execute(
        select(AvatarSessionORM).where(
            AvatarSessionORM.id == session_id, AvatarSessionORM.user_id == user_id
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        # 404, not 403 — don't confirm to a caller whether a session id
        # exists for someone else.
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status != "active":
        raise HTTPException(status_code=409, detail=f"Session is {session.status}, not active")
    return session


@app.post("/v1/sessions", response_model=HermesResponse)
async def create_session(
    request: Request,
    body: CreateSessionRequest,
    current_user: dict = Depends(get_current_user),
):
    """Starts a real OpenTalking session for this user and this character,
    and records it server-side. Returns everything the Flutter client needs
    to open its own WebRTC connection directly to OpenTalking."""
    request_id = getattr(request.state, "request_id", generate_request_id())

    async with get_db_session() as db:
        character = await _get_character(db, body.character_slug)

        try:
            ot_resp = await _http.post(
                f"{OPENTALKING_API_URL}/sessions",
                json={
                    "avatar_id": character.opentalking_avatar_id,
                    "model": character.opentalking_model,
                },
            )
            ot_resp.raise_for_status()
            ot_data = ot_resp.json()
        except httpx.HTTPError as e:
            logger.error("opentalking_unreachable", error=str(e), request_id=request_id)
            return HermesResponse(
                success=False,
                error="Avatar service is temporarily unavailable",
                error_code="AVATAR_BACKEND_DOWN",
                request_id=request_id,
            )

        opentalking_session_id = ot_data.get("session_id") or ot_data.get("id")
        if not opentalking_session_id:
            logger.error("opentalking_bad_response", body=ot_data, request_id=request_id)
            return HermesResponse(
                success=False,
                error="Avatar backend returned an unexpected response",
                error_code="AVATAR_BACKEND_ERROR",
                request_id=request_id,
            )

        session_row = AvatarSessionORM(
            user_id=current_user["user_id"],
            character_id=character.id,
            opentalking_session_id=opentalking_session_id,
            status="active",
        )
        db.add(session_row)
        await db.flush()

        logger.info(
            "avatar_session_created",
            user_id=current_user["user_id"],
            character=body.character_slug,
            opentalking_session_id=opentalking_session_id,
        )

        return HermesResponse(
            success=True,
            data={
                "session_id": str(session_row.id),
                "opentalking_session_id": opentalking_session_id,
                # Client opens WebRTC + SSE directly against these, using
                # opentalking_session_id — we are not in that data path.
                "webrtc_offer_path": f"{OPENTALKING_PUBLIC_URL}/sessions/{opentalking_session_id}/webrtc/offer",
                "events_path": f"{OPENTALKING_PUBLIC_URL}/sessions/{opentalking_session_id}/events",
                "character": {
                    "slug": character.slug,
                    "display_name": character.display_name,
                    "teaching_style": character.teaching_style,
                },
            },
            request_id=request_id,
        )


@app.post("/v1/sessions/{session_id}/message", response_model=HermesResponse)
async def send_message(
    session_id: UUID,
    request: Request,
    body: SpeakRequest,
    current_user: dict = Depends(get_current_user),
):
    """Forwards a text turn to OpenTalking's real /sessions/{id}/speak
    endpoint. OpenTalking itself drives the LLM->TTS->render pipeline and
    streams the reply back to the client over the WebRTC/SSE paths handed
    out by create_session — this call just kicks the turn off."""
    request_id = getattr(request.state, "request_id", generate_request_id())

    async with get_db_session() as db:
        session = await _get_owned_session(db, session_id, current_user["user_id"])

        try:
            ot_resp = await _http.post(
                f"{OPENTALKING_API_URL}/sessions/{session.opentalking_session_id}/speak",
                json={"text": body.text},
            )
            ot_resp.raise_for_status()
        except httpx.HTTPError as e:
            logger.error("opentalking_speak_failed", error=str(e), request_id=request_id)
            return HermesResponse(
                success=False, error="Failed to deliver message to avatar",
                error_code="AVATAR_SPEAK_FAILED", request_id=request_id,
            )

        return HermesResponse(success=True, data={"delivered": True}, request_id=request_id)


@app.post("/v1/sessions/{session_id}/audio", response_model=HermesResponse)
async def send_audio(
    session_id: UUID,
    request: Request,
    current_user: dict = Depends(get_current_user),
    audio: UploadFile = File(...),
):
    """Transcribes the uploaded clip with Hermes's own STT service, then
    forwards the transcript exactly like send_message. Real transcription,
    not a stub — but it does add one hop of latency versus giving
    OpenTalking's own STT the raw audio; documented trade-off, see the
    module docstring."""
    request_id = getattr(request.state, "request_id", generate_request_id())

    async with get_db_session() as db:
        session = await _get_owned_session(db, session_id, current_user["user_id"])

    import base64
    audio_bytes = await audio.read()
    audio_format = (audio.filename or "clip.wav").rsplit(".", 1)[-1].lower() or "wav"
    try:
        # Matches services/stt/main.py's real STTRequest contract exactly:
        # JSON body with base64 audio, not multipart — the transcript comes
        # back as data.text in the HermesResponse envelope.
        stt_resp = await _http.post(
            f"{STT_SERVICE_URL}/v1/transcribe",
            json={
                "audio_base64": base64.b64encode(audio_bytes).decode("ascii"),
                "format": audio_format,
            },
        )
        stt_resp.raise_for_status()
        stt_body = stt_resp.json()
        if not stt_body.get("success"):
            raise httpx.HTTPError(stt_body.get("error", "STT service returned an error"))
        transcript = stt_body.get("data", {}).get("text", "")
    except httpx.HTTPError as e:
        logger.error("stt_failed", error=str(e), request_id=request_id)
        return HermesResponse(
            success=False, error="Speech transcription failed",
            error_code="STT_FAILED", request_id=request_id,
        )

    if not transcript.strip():
        return HermesResponse(
            success=False, error="Could not hear anything in that clip",
            error_code="EMPTY_TRANSCRIPT", request_id=request_id,
        )

    return await send_message(session_id, request, SpeakRequest(text=transcript), current_user)


@app.post("/v1/sessions/{session_id}/interrupt", response_model=HermesResponse)
async def interrupt_session(
    session_id: UUID,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Barge-in: forwards to OpenTalking's real /interrupt endpoint, which
    cancels the in-flight LLM/TTS/render pipeline for that session."""
    request_id = getattr(request.state, "request_id", generate_request_id())

    async with get_db_session() as db:
        session = await _get_owned_session(db, session_id, current_user["user_id"])

        try:
            ot_resp = await _http.post(
                f"{OPENTALKING_API_URL}/sessions/{session.opentalking_session_id}/interrupt"
            )
            ot_resp.raise_for_status()
        except httpx.HTTPError as e:
            logger.error("opentalking_interrupt_failed", error=str(e), request_id=request_id)
            return HermesResponse(
                success=False, error="Failed to interrupt avatar",
                error_code="AVATAR_INTERRUPT_FAILED", request_id=request_id,
            )

        return HermesResponse(success=True, data={"interrupted": True}, request_id=request_id)


@app.delete("/v1/sessions/{session_id}", response_model=HermesResponse)
async def end_session(
    session_id: UUID,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Marks the session ended on our side. NOTE: OpenTalking's public docs
    describe a `session.terminated` bus event but do not document an
    explicit client-facing DELETE /sessions/{id} endpoint as of this
    writing, so we do not claim to call one — the OpenTalking session will
    idle out on its own. If/when they document (or we confirm) an explicit
    teardown endpoint, wire it in here."""
    request_id = getattr(request.state, "request_id", generate_request_id())

    async with get_db_session() as db:
        session = await _get_owned_session(db, session_id, current_user["user_id"])
        session.status = "ended"
        session.ended_at = datetime.utcnow()

    return HermesResponse(success=True, data={"ended": True}, request_id=request_id)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8023)
