"""
Hermes LinguaMind — Shared Utilities
Common helpers used across all services.
"""
import json
import hashlib
import base64
import asyncio
import time
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from functools import wraps
import structlog

logger = structlog.get_logger()

# ─────────────────────────────────────────────────────────────
# CACHE HELPERS
# ─────────────────────────────────────────────────────────────

class InMemoryCache:
    """Simple TTL cache for development; swap to Redis in production."""

    def __init__(self):
        self._store: Dict[str, Dict[str, Any]] = {}

    def get(self, key: str) -> Optional[Any]:
        entry = self._store.get(key)
        if entry is None:
            return None
        if datetime.utcnow() > entry["expires_at"]:
            del self._store[key]
            return None
        return entry["value"]

    def set(self, key: str, value: Any, ttl_seconds: int = 300):
        self._store[key] = {
            "value": value,
            "expires_at": datetime.utcnow() + timedelta(seconds=ttl_seconds)
        }

    def delete(self, key: str):
        self._store.pop(key, None)

    def clear(self):
        self._store.clear()

cache = InMemoryCache()

# ─────────────────────────────────────────────────────────────
# LLM HELPERS
# ─────────────────────────────────────────────────────────────

def build_system_prompt(persona: str = "hermes", language: str = "en", cefr_level: str = "A1") -> str:
    """Build the Hermes system prompt with persona and constraints."""
    prompts = {
        "hermes": f"""You are Hermes, a friendly, patient AI language tutor.
You are helping a learner at CEFR level {cefr_level} learn {language}.
Rules:
- Keep responses concise (2-3 sentences max for A1-A2, slightly longer for B1+)
- Use the target language primarily, but provide translations for new vocabulary
- Be encouraging and supportive
- Correct grammar gently with explanations
- Ask follow-up questions to keep conversation going
- Never be condescending
- If you don't know something, say so honestly
- Always prioritize learner safety and well-being""",
        "grammar_checker": f"""You are a precise grammar checker for {language} at CEFR level {cefr_level}.
Analyze the text and identify errors. For each error:
1. State the error type
2. Provide the correction
3. Explain the rule briefly
4. Rate severity (minor/moderate/major)
Output in structured JSON format.""",
        "conversation": f"""You are Hermes in conversation mode. The learner is at {cefr_level} level.
Engage in natural dialogue. Adapt your vocabulary and grammar complexity to their level.
If they make mistakes, incorporate gentle corrections into your response naturally."""
    }
    return prompts.get(persona, prompts["hermes"])

# ─────────────────────────────────────────────────────────────
# SM-2 SPACED REPETITION
# ─────────────────────────────────────────────────────────────

def sm2_update(
    quality: int,
    repetitions: int = 0,
    ease_factor: float = 2.5,
    interval_days: int = 0
) -> Dict[str, Any]:
    """SuperMemo-2 algorithm for spaced repetition."""
    if quality < 0 or quality > 5:
        raise ValueError("Quality must be between 0 and 5")

    if quality >= 3:
        if repetitions == 0:
            interval_days = 1
        elif repetitions == 1:
            interval_days = 6
        else:
            interval_days = int(interval_days * ease_factor)
        repetitions += 1
    else:
        repetitions = 0
        interval_days = 1

    ease_factor = ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    ease_factor = max(1.3, ease_factor)

    return {
        "repetitions": repetitions,
        "ease_factor": round(ease_factor, 2),
        "interval_days": interval_days,
        "next_review": (datetime.utcnow() + timedelta(days=interval_days)).isoformat(),
        "quality": quality
    }

# ─────────────────────────────────────────────────────────────
# VALIDATION HELPERS
# ─────────────────────────────────────────────────────────────

def validate_email(email: str) -> bool:
    """Basic email validation."""
    import re
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))

def sanitize_input(text: str, max_length: int = 2000) -> str:
    """Sanitize user input — strip, truncate, basic XSS prevention."""
    if not text:
        return ""
    text = text.strip()
    text = text.replace("<", "&lt;").replace(">", "&gt;")
    text = text.replace("\"", "&quot;").replace("'", "&#x27;")
    if len(text) > max_length:
        text = text[:max_length]
    return text

def generate_idempotency_key(*args) -> str:
    """Generate a deterministic idempotency key from args."""
    content = "|".join(str(a) for a in args)
    return hashlib.sha256(content.encode()).hexdigest()[:32]

# ─────────────────────────────────────────────────────────────
# RETRY DECORATOR
# ─────────────────────────────────────────────────────────────

def async_retry(max_retries: int = 3, backoff_base: float = 1.0, max_backoff: float = 60.0):
    """Decorator for async functions with exponential backoff."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        backoff = min(backoff_base * (2 ** attempt), max_backoff)
                        logger.warning(
                            "retry_attempt",
                            func=func.__name__,
                            attempt=attempt + 1,
                            max_retries=max_retries,
                            backoff=backoff,
                            error=str(e)
                        )
                        await asyncio.sleep(backoff)
                    else:
                        logger.error(
                            "retry_exhausted",
                            func=func.__name__,
                            max_retries=max_retries,
                            error=str(e)
                        )
                        raise last_exception
            return None
        return wrapper
    return decorator

# ─────────────────────────────────────────────────────────────
# TIMING & METRICS
# ─────────────────────────────────────────────────────────────

class Timer:
    """Context manager for timing operations."""

    def __init__(self, name: str = "operation"):
        self.name = name
        self.start_time: Optional[float] = None
        self.elapsed_ms: float = 0.0

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, *args):
        self.elapsed_ms = (time.perf_counter() - self.start_time) * 1000
        logger.info("timer_elapsed", name=self.name, elapsed_ms=round(self.elapsed_ms, 2))

# ─────────────────────────────────────────────────────────────
# CIRCUIT BREAKER
# ─────────────────────────────────────────────────────────────

class CircuitBreaker:
    """Circuit breaker pattern for downstream service resilience."""

    FAILURE_THRESHOLD = 3
    RECOVERY_TIMEOUT = 30

    def __init__(self, name: str):
        self.name = name
        self.state = "CLOSED"
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self._lock = asyncio.Lock()

    async def call(self, func: Callable, *args, **kwargs):
        async with self._lock:
            if self.state == "OPEN":
                if time.time() - self.last_failure_time > self.RECOVERY_TIMEOUT:
                    self.state = "HALF_OPEN"
                    self.failure_count = 0
                    logger.info("circuit_breaker_half_open", service=self.name)
                else:
                    raise CircuitBreakerOpen(f"Circuit breaker OPEN for {self.name}")

        try:
            result = await func(*args, **kwargs)
            async with self._lock:
                if self.state == "HALF_OPEN":
                    self.state = "CLOSED"
                    self.failure_count = 0
                    logger.info("circuit_breaker_closed", service=self.name)
            return result
        except Exception as e:
            async with self._lock:
                self.failure_count += 1
                self.last_failure_time = time.time()
                if self.failure_count >= self.FAILURE_THRESHOLD:
                    self.state = "OPEN"
                    logger.error("circuit_breaker_open", service=self.name, failures=self.failure_count)
            raise

class CircuitBreakerOpen(Exception):
    pass

# ─────────────────────────────────────────────────────────────
# IDEMPOTENCY HELPERS
# ─────────────────────────────────────────────────────────────

class IdempotencyStore:
    """Track processed idempotency keys to prevent duplicate operations."""

    def __init__(self):
        self._processed: Dict[str, Dict[str, Any]] = {}

    def is_processed(self, key: str) -> bool:
        entry = self._processed.get(key)
        if entry is None:
            return False
        if datetime.utcnow() > entry["expires_at"]:
            del self._processed[key]
            return False
        return True

    def mark_processed(self, key: str, result: Any):
        self._processed[key] = {
            "result": result,
            "expires_at": datetime.utcnow() + timedelta(hours=24)
        }

    def get_result(self, key: str) -> Optional[Any]:
        entry = self._processed.get(key)
        if entry and datetime.utcnow() <= entry["expires_at"]:
            return entry["result"]
        return None

idempotency_store = IdempotencyStore()

# ─────────────────────────────────────────────────────────────
# JSON HELPERS
# ─────────────────────────────────────────────────────────────

def safe_json_dumps(obj: Any, default: Any = None) -> str:
    """Safely serialize to JSON with fallback."""
    try:
        return json.dumps(obj, default=str, ensure_ascii=False)
    except Exception:
        return json.dumps(default or {"error": "serialization_failed"})


def safe_json_loads(text: str, default: Any = None) -> Any:
    """Safely parse JSON with fallback."""
    try:
        return json.loads(text)
    except Exception:
        return default or {}
