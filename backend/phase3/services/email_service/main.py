"""
Hermes LinguaMind — Email Service
Port: 8021 | Phase 3 — Production Ready

Real email delivery over standard SMTP (aiosmtplib) — works with ANY SMTP
server: a paid provider if the user configures one, but just as well with
fully free/self-hosted options (a local Postfix container, MailHog/Mailpit
for dev, Proton/Gmail SMTP with an app password, etc.). No proprietary
"email API" SDK is used, so there's no vendor lock-in and no paid API
requirement.

If SMTP_HOST is not configured, the service does not fake success — it
queues the rendered message to /app/outbox as an .eml file and returns a
"queued_local" status, so nothing is silently lost during local dev.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import time
import uuid
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path
from typing import Any, Dict, List, Optional

import structlog
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from jinja2 import Environment, BaseLoader, select_autoescape
from pydantic import BaseModel, EmailStr, Field

from shared.models.common import HermesResponse, HealthStatus
from shared.utils.helpers import generate_request_id

logger = structlog.get_logger("hermes.email")

app = FastAPI(title="Hermes Email Service", description="SMTP email delivery (open-source, provider-agnostic)", version="3.0.0")
_app_start_time = time.time()

SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
FROM_EMAIL = os.getenv("EMAIL_FROM", "no-reply@linguamax.local")
FROM_NAME = os.getenv("EMAIL_FROM_NAME", "LinguaMax")
OUTBOX_DIR = Path(os.getenv("EMAIL_OUTBOX_DIR", "/app/outbox"))
OUTBOX_DIR.mkdir(parents=True, exist_ok=True)

_jinja = Environment(loader=BaseLoader(), autoescape=select_autoescape(["html"]))

# Built-in, dependency-free templates (kept in code so the service has zero
# external template-storage requirement; override by passing html_body).
_TEMPLATES: Dict[str, str] = {
    "welcome": (
        "<h2>Welcome to {{ app_name }}, {{ name }}!</h2>"
        "<p>You're all set to start learning {{ target_language }}. "
        "Your AI companion is ready whenever you are.</p>"
    ),
    "streak_reminder": (
        "<h2>Don't lose your {{ streak_days }}-day streak, {{ name }}!</h2>"
        "<p>A quick 5-minute session today keeps it alive.</p>"
    ),
    "password_reset": (
        "<h2>Reset your password</h2>"
        "<p>Hi {{ name }}, click below within {{ expires_minutes }} minutes:</p>"
        "<p><a href=\"{{ reset_link }}\">{{ reset_link }}</a></p>"
    ),
    "coin_reward": (
        "<h2>You earned {{ coins }} coins!</h2>"
        "<p>Nice work, {{ name }}. Keep the momentum going.</p>"
    ),
}


class SendEmailRequest(BaseModel):
    to: EmailStr
    subject: str
    template: Optional[str] = Field(None, description="One of: " + ", ".join(_TEMPLATES.keys()))
    context: Dict[str, Any] = Field(default_factory=dict)
    html_body: Optional[str] = Field(None, description="Raw HTML body; overrides template if given")
    text_body: Optional[str] = None
    cc: List[EmailStr] = Field(default_factory=list)


class SendEmailResponse(BaseModel):
    email_id: str
    status: str  # "sent" | "queued_local" | "failed"
    provider: str


async def _send_via_smtp(msg: EmailMessage) -> None:
    import aiosmtplib

    await aiosmtplib.send(
        msg,
        hostname=SMTP_HOST,
        port=SMTP_PORT,
        username=SMTP_USER or None,
        password=SMTP_PASSWORD or None,
        start_tls=SMTP_USE_TLS,
        timeout=15,
    )


def _render_html(req: SendEmailRequest) -> str:
    if req.html_body:
        return req.html_body
    if req.template:
        tpl_src = _TEMPLATES.get(req.template)
        if not tpl_src:
            raise HTTPException(status_code=400, detail=f"Unknown template '{req.template}'. Known: {list(_TEMPLATES.keys())}")
        return _jinja.from_string(tpl_src).render(**req.context)
    raise HTTPException(status_code=400, detail="Provide either 'template' or 'html_body'")


@app.get("/health", response_model=HealthStatus)
async def health_check():
    return HealthStatus(
        status="healthy",
        service="email_service",
        version="3.0.0",
        timestamp=datetime.utcnow(),
        uptime_seconds=time.time() - _app_start_time,
        dependencies={"smtp": "configured" if SMTP_HOST else "not_configured (local outbox mode)"},
    )


@app.post("/v1/email/send", response_model=HermesResponse)
async def send_email(request: Request, req: SendEmailRequest):
    request_id = getattr(request.state, "request_id", generate_request_id())
    email_id = str(uuid.uuid4())
    html = _render_html(req)

    msg = EmailMessage()
    msg["From"] = f"{FROM_NAME} <{FROM_EMAIL}>"
    msg["To"] = req.to
    if req.cc:
        msg["Cc"] = ", ".join(req.cc)
    msg["Subject"] = req.subject
    msg["Message-ID"] = f"<{email_id}@linguamax.local>"
    msg.set_content(req.text_body or "This email requires an HTML-capable client.")
    msg.add_alternative(html, subtype="html")

    if SMTP_HOST:
        try:
            await _send_via_smtp(msg)
            status = "sent"
            provider = f"smtp:{SMTP_HOST}"
            logger.info("email_sent", request_id=request_id, email_id=email_id, to=req.to)
        except Exception as e:
            logger.error("email_send_failed", request_id=request_id, error=str(e))
            status = "failed"
            provider = f"smtp:{SMTP_HOST}"
    else:
        # No SMTP configured — write a real .eml to disk instead of faking success.
        out_path = OUTBOX_DIR / f"{email_id}.eml"
        out_path.write_bytes(bytes(msg))
        status = "queued_local"
        provider = "local_outbox"
        logger.info("email_queued_local", request_id=request_id, path=str(out_path))

    resp = SendEmailResponse(email_id=email_id, status=status, provider=provider)
    return HermesResponse(success=status != "failed", data=resp.model_dump(), request_id=request_id)


@app.get("/v1/email/templates")
async def list_templates():
    return {"templates": list(_TEMPLATES.keys())}


@app.get("/v1/metrics")
async def get_metrics():
    return {
        "uptime_seconds": time.time() - _app_start_time,
        "smtp_configured": bool(SMTP_HOST),
        "outbox_pending": len(list(OUTBOX_DIR.glob("*.eml"))),
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8021)))
