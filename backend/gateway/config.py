"""Unified configuration for the Hermes LinguaMind adapter."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict


def _env(key: str, default: str = "") -> str:
    return os.getenv(key, default)


@dataclass(frozen=True)
class Settings:
    app_name: str = "Hermes LinguaMind Unified Adapter"
    app_version: str = "1.0.0"
    environment: str = field(default_factory=lambda: _env("ENVIRONMENT", "development"))
    log_level: str = field(default_factory=lambda: _env("LOG_LEVEL", "INFO"))
    host: str = field(default_factory=lambda: _env("ADAPTER_HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: int(_env("ADAPTER_PORT", "8080")))

    secret_key: str = field(
        default_factory=lambda: _env(
            "SECRET_KEY",
            _env("JWT_SECRET_KEY", "hermes-dev-secret-change-in-production"),
        )
    )
    database_url: str = field(
        default_factory=lambda: _env(
            "DATABASE_URL",
            "postgresql+asyncpg://hermes:hermes@postgres:5432/hermes_db",
        )
    )
    redis_url: str = field(
        default_factory=lambda: _env("REDIS_URL", "redis://redis:6379/0")
    )

    # Upstream microservice base URLs (compose network / localhost)
    service_urls: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        defaults = {
            "api_gateway": _env("API_GATEWAY_URL", "http://localhost:8000"),
            "llm": _env("LLM_SERVICE_URL", "http://localhost:8001"),
            "tts": _env("TTS_SERVICE_URL", "http://localhost:8002"),
            "stt": _env("STT_SERVICE_URL", "http://localhost:8003"),
            "viseme": _env("VISEME_SERVICE_URL", "http://localhost:8004"),
            "pronunciation": _env("PRONUNCIATION_SERVICE_URL", "http://localhost:8005"),
            "coin_ledger": _env("COIN_LEDGER_SERVICE_URL", "http://localhost:8006"),
            "curriculum": _env("CURRICULUM_SERVICE_URL", "http://localhost:8007"),
            "memory": _env("MEMORY_SERVICE_URL", "http://localhost:8008"),
            "moderation": _env("MODERATION_SERVICE_URL", "http://localhost:8009"),
            "grammar_rule_db": _env("GRAMMAR_RULE_DB_SERVICE_URL", "http://localhost:8010"),
            "content_generation": _env("CONTENT_GENERATION_SERVICE_URL", "http://localhost:8011"),
            "personalization": _env("PERSONALIZATION_SERVICE_URL", "http://localhost:8012"),
            "gesture_emotion": _env("GESTURE_EMOTION_SERVICE_URL", "http://localhost:8013"),
            "leaderboard": _env("LEADERBOARD_SERVICE_URL", "http://localhost:8014"),
            "social_exchange": _env("SOCIAL_EXCHANGE_SERVICE_URL", "http://localhost:8015"),
            "anti_fraud": _env("ANTI_FRAUD_SERVICE_URL", "http://localhost:8016"),
            "live_conversation": _env("LIVE_CONVERSATION_SERVICE_URL", "http://localhost:8017"),
            "observability": _env("OBSERVABILITY_SERVICE_URL", "http://localhost:8018"),
            "security": _env("SECURITY_SERVICE_URL", "http://localhost:8019"),
            "hermes_orchestrator": _env("HERMES_ORCHESTRATOR_URL", "http://localhost:8020"),
            "email_service": _env("EMAIL_SERVICE_URL", "http://localhost:8021"),
            "notification_service": _env("NOTIFICATION_SERVICE_URL", "http://localhost:8022"),
            "avatar_service": _env("AVATAR_SERVICE_URL", "http://localhost:8023"),
        }
        object.__setattr__(self, "service_urls", defaults)


settings = Settings()
