"""
Service registry — single source of truth for every backend process the
gateway can reach. `tier` is a purely organizational grouping (core /
advanced / ops / orchestrator) for the /v1/tiers/{tier} browsing endpoint —
it has no relation to the old phase1/phase2/phase3/phase4 folder names,
and phase1/phase2 no longer exist in this repo (dead code, deleted).
Mount path prefix per service avoids /health and /v1 route collisions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from gateway.config import settings


@dataclass(frozen=True)
class ServiceSpec:
    name: str
    tier: str
    port: int
    mount_prefix: str
    health_path: str = "/health"
    description: str = ""

    @property
    def upstream_url(self) -> str:
        return settings.service_urls.get(self.name, f"http://localhost:{self.port}")


SERVICE_REGISTRY: List[ServiceSpec] = [
    # ── core (8000-8009) ──
    ServiceSpec("api_gateway", "core", 8000, "/svc/api-gateway", description="Auth + gateway"),
    ServiceSpec("llm", "core", 8001, "/svc/llm", description="LLM orchestration"),
    ServiceSpec("tts", "core", 8002, "/svc/tts", description="Text-to-speech"),
    ServiceSpec("stt", "core", 8003, "/svc/stt", description="Speech-to-text"),
    ServiceSpec("viseme", "core", 8004, "/svc/viseme", description="Viseme timeline"),
    ServiceSpec("pronunciation", "core", 8005, "/svc/pronunciation", description="Pronunciation scoring"),
    ServiceSpec("coin_ledger", "core", 8006, "/svc/coin-ledger", description="Coin economy"),
    ServiceSpec("curriculum", "core", 8007, "/svc/curriculum", description="Spaced repetition"),
    ServiceSpec("memory", "core", 8008, "/svc/memory", description="User memory"),
    ServiceSpec("moderation", "core", 8009, "/svc/moderation", description="Content safety"),
    # ── advanced (8010-8017) ──
    ServiceSpec("grammar_rule_db", "advanced", 8010, "/svc/grammar", description="Grammar rules"),
    ServiceSpec("content_generation", "advanced", 8011, "/svc/content", description="Content pipeline"),
    ServiceSpec("personalization", "advanced", 8012, "/svc/personalization", description="Personalization"),
    ServiceSpec("gesture_emotion", "advanced", 8013, "/svc/gesture", description="Gesture/emotion cues"),
    ServiceSpec("leaderboard", "advanced", 8014, "/svc/leaderboard", description="Leaderboards"),
    ServiceSpec("social_exchange", "advanced", 8015, "/svc/social", description="Social matching"),
    ServiceSpec("anti_fraud", "advanced", 8016, "/svc/anti-fraud", description="Anti-fraud"),
    ServiceSpec("live_conversation", "advanced", 8017, "/svc/live", description="Live conversation (WebSocket)"),
    # ── ops (8018-8019, 8021-8023) ──
    ServiceSpec("observability", "ops", 8018, "/svc/observability", description="Metrics/alerts"),
    ServiceSpec("security", "ops", 8019, "/svc/security", description="Audit/backup/compliance"),
    # NOTE: email_service (8021), notification_service (8022), and
    # avatar_service (8023) all run in supervisord.conf and have real
    # upstream URLs set in docker-compose.yml, but were missing from this
    # registry — meaning they were unreachable through the gateway even
    # though the processes were up. Added below; this is what actually
    # makes them callable at /svc/email, /svc/notifications, /svc/avatar.
    ServiceSpec("email_service", "ops", 8021, "/svc/email", description="Transactional email (SMTP)"),
    ServiceSpec("notification_service", "ops", 8022, "/svc/notifications", description="Push notifications (VAPID)"),
    ServiceSpec(
        "avatar_service", "ops", 8023, "/svc/avatar",
        description="OpenTalking avatar session gateway — auth + session ownership; "
                     "client opens WebRTC directly against OpenTalking using the "
                     "session data this returns",
    ),
    # ── orchestrator (8020) ──
    ServiceSpec(
        "hermes_orchestrator",
        "orchestrator",
        8020,
        "/svc/hermes",
        description="Intent → plan → execute → verify",
    ),
]

REGISTRY_BY_NAME: Dict[str, ServiceSpec] = {s.name: s for s in SERVICE_REGISTRY}


def services_by_tier(tier: str) -> List[ServiceSpec]:
    return [s for s in SERVICE_REGISTRY if s.tier == tier]
