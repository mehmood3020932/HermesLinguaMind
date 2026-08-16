"""
Hermes LinguaMind — Shared Utilities
Cumulative: Phase 1 + Phase 2 + Phase 3
"""

import asyncio
import hashlib
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union
from functools import wraps

import httpx
import structlog
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

logger = structlog.get_logger("hermes.helpers")

T = TypeVar("T")

# ============================================================
# LLM CALL HELPER (with retry, fallback, circuit breaker)
# ============================================================

class LLMProviderError(Exception):
    """Custom exception for LLM provider errors."""
    pass

class CircuitBreakerOpen(Exception):
    """Circuit breaker is open."""
    pass

class CircuitBreaker:
    """Simple circuit breaker implementation."""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures = 0
        self.last_failure_time: Optional[float] = None
        self.state = "closed"  # closed, open, half-open

    def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        if self.state == "open":
            if time.time() - (self.last_failure_time or 0) > self.recovery_timeout:
                self.state = "half-open"
                self.failures = 0
            else:
                raise CircuitBreakerOpen("Circuit breaker is open")

        try:
            result = func(*args, **kwargs)
            if self.state == "half-open":
                self.state = "closed"
                self.failures = 0
            return result
        except Exception as e:
            self.failures += 1
            self.last_failure_time = time.time()
            if self.failures >= self.failure_threshold:
                self.state = "open"
            raise

# Global circuit breakers per provider
_circuit_breakers: Dict[str, CircuitBreaker] = {}

def get_circuit_breaker(provider_name: str) -> CircuitBreaker:
    if provider_name not in _circuit_breakers:
        _circuit_breakers[provider_name] = CircuitBreaker()
    return _circuit_breakers[provider_name]


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((httpx.HTTPError, LLMProviderError)),
    before_sleep=before_sleep_log(logger, "warning"),
)
async def call_llm_provider(
    provider_url: str,
    api_key: str,
    model: str,
    messages: List[Dict[str, str]],
    temperature: float = 0.7,
    max_tokens: int = 1024,
    timeout: float = 30.0,
    protocol: str = "openai",
) -> Dict[str, Any]:
    """
    Call an LLM provider with retry and circuit breaker.

    Args:
        provider_url: Base URL of the provider
        api_key: API key for authentication
        model: Model name/identifier
        messages: List of message dicts with 'role' and 'content'
        temperature: Sampling temperature
        max_tokens: Maximum tokens to generate
        timeout: Request timeout in seconds
        protocol: "openai" for any OpenAI-compatible /chat/completions API
                  (OpenAI, Groq, FreeLLMAPI, Ollama's OpenAI-compat endpoint),
                  or "anthropic" for Anthropic's native /messages API, which
                  uses a different auth header and request/response shape.

    Returns:
        Dict containing response text, tokens used, and latency
    """
    provider_name = provider_url.split("//")[-1].split("/")[0]
    cb = get_circuit_breaker(provider_name)

    start_time = time.time()

    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            if protocol == "anthropic":
                system_msgs = [m["content"] for m in messages if m.get("role") == "system"]
                turn_msgs = [m for m in messages if m.get("role") != "system"]
                response = await client.post(
                    f"{provider_url}/messages",
                    headers={
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model,
                        "system": "\n".join(system_msgs) if system_msgs else None,
                        "messages": turn_msgs,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                    },
                )
                response.raise_for_status()
                data = response.json()
                text = "".join(block.get("text", "") for block in data.get("content", []))
                usage = data.get("usage", {})
                tokens_used = usage.get("input_tokens", 0) + usage.get("output_tokens", 0)
                model_used = data.get("model", model)
            else:
                response = await client.post(
                    f"{provider_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model,
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                    },
                )
                response.raise_for_status()
                data = response.json()
                text = data["choices"][0]["message"]["content"]
                tokens_used = data.get("usage", {}).get("total_tokens")
                model_used = data.get("model", model)

            latency_ms = (time.time() - start_time) * 1000

            result = {
                "text": text,
                "model_used": model_used,
                "tokens_used": tokens_used,
                "latency_ms": latency_ms,
                "cached": False,
            }

            logger.info(
                "llm_call_success",
                provider=provider_name,
                model=model,
                latency_ms=latency_ms,
                tokens=result["tokens_used"],
            )

            return result

        except httpx.HTTPStatusError as e:
            logger.error(
                "llm_http_error",
                provider=provider_name,
                status_code=e.response.status_code,
                response=e.response.text[:500],
            )
            raise LLMProviderError(f"HTTP {e.response.status_code}: {e.response.text[:200]}")
        except httpx.RequestError as e:
            logger.error("llm_request_error", provider=provider_name, error=str(e))
            raise LLMProviderError(f"Request failed: {str(e)}")
        except Exception as e:
            logger.error("llm_unexpected_error", provider=provider_name, error=str(e))
            raise LLMProviderError(f"Unexpected error: {str(e)}")


async def call_llm_with_fallback(
    providers: List[Dict[str, Any]],
    messages: List[Dict[str, str]],
    temperature: float = 0.7,
    max_tokens: int = 1024,
) -> Dict[str, Any]:
    """
    Call LLM with automatic fallback across multiple providers.

    Args:
        providers: List of provider configs with 'url', 'api_key', 'model', 'priority'
        messages: List of message dicts
        temperature: Sampling temperature
        max_tokens: Maximum tokens

    Returns:
        LLM response dict
    """
    # Sort by priority
    sorted_providers = sorted(providers, key=lambda p: p.get("priority", 0))

    last_error = None

    for provider in sorted_providers:
        try:
            result = await call_llm_provider(
                provider_url=provider["url"],
                api_key=provider["api_key"],
                model=provider["model"],
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=provider.get("timeout", 30.0),
                protocol=provider.get("protocol", "openai"),
            )
            result["provider"] = provider.get("name", "unknown")
            return result
        except (LLMProviderError, CircuitBreakerOpen) as e:
            last_error = e
            logger.warning(
                "llm_provider_failed",
                provider=provider.get("name", "unknown"),
                error=str(e),
                trying_next=len(sorted_providers) > 1,
            )
            continue

    # All providers failed
    logger.error("llm_all_providers_failed", error=str(last_error))
    raise LLMProviderError(f"All providers failed. Last error: {last_error}")


# ============================================================
# IDEMPOTENCY KEY GENERATOR
# ============================================================

def generate_idempotency_key(user_id: str, transaction_type: str, timestamp: Optional[str] = None) -> str:
    """Generate a deterministic idempotency key."""
    ts = timestamp or datetime.utcnow().strftime("%Y%m%d%H%M%S")
    raw = f"{user_id}:{transaction_type}:{ts}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


# ============================================================
# RATE LIMITING HELPERS
# ============================================================

class RateLimiter:
    """In-memory rate limiter (use Redis in production)."""

    def __init__(self):
        self._store: Dict[str, List[float]] = {}

    def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> bool:
        now = time.time()
        window_start = now - window_seconds

        # Clean old entries
        if key in self._store:
            self._store[key] = [t for t in self._store[key] if t > window_start]
        else:
            self._store[key] = []

        if len(self._store[key]) < max_requests:
            self._store[key].append(now)
            return True
        return False

    def get_remaining(self, key: str, max_requests: int, window_seconds: int) -> int:
        now = time.time()
        window_start = now - window_seconds

        if key in self._store:
            self._store[key] = [t for t in self._store[key] if t > window_start]
            return max(0, max_requests - len(self._store[key]))
        return max_requests


# ============================================================
# VALIDATION HELPERS
# ============================================================

def validate_email(email: str) -> bool:
    """Basic email validation."""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_password_strength(password: str) -> tuple[bool, List[str]]:
    """Validate password strength and return issues."""
    issues = []
    if len(password) < 8:
        issues.append("Password must be at least 8 characters")
    if not any(c.isupper() for c in password):
        issues.append("Password must contain at least one uppercase letter")
    if not any(c.islower() for c in password):
        issues.append("Password must contain at least one lowercase letter")
    if not any(c.isdigit() for c in password):
        issues.append("Password must contain at least one digit")
    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        issues.append("Password must contain at least one special character")
    return len(issues) == 0, issues


# ============================================================
# ENCODING / DECODING HELPERS
# ============================================================

def safe_json_dumps(obj: Any) -> str:
    """Safely serialize object to JSON string."""
    def default_encoder(o):
        if isinstance(o, datetime):
            return o.isoformat()
        if isinstance(o, uuid.UUID):
            return str(o)
        raise TypeError(f"Object of type {type(o)} is not JSON serializable")

    return json.dumps(obj, default=default_encoder)


def generate_request_id() -> str:
    """Generate a unique request ID."""
    return str(uuid.uuid4())


# ============================================================
# TIMING / PERFORMANCE HELPERS
# ============================================================

def timing_decorator(func_name: Optional[str] = None):
    """Decorator to measure function execution time."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                latency = (time.time() - start) * 1000
                logger.info(
                    "function_timing",
                    function=func_name or func.__name__,
                    latency_ms=latency,
                    status="success",
                )
                return result
            except Exception as e:
                latency = (time.time() - start) * 1000
                logger.error(
                    "function_timing",
                    function=func_name or func.__name__,
                    latency_ms=latency,
                    status="error",
                    error=str(e),
                )
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = func(*args, **kwargs)
                latency = (time.time() - start) * 1000
                logger.info(
                    "function_timing",
                    function=func_name or func.__name__,
                    latency_ms=latency,
                    status="success",
                )
                return result
            except Exception as e:
                latency = (time.time() - start) * 1000
                logger.error(
                    "function_timing",
                    function=func_name or func.__name__,
                    latency_ms=latency,
                    status="error",
                    error=str(e),
                )
                raise

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator


# ============================================================
# CACHE HELPERS
# ============================================================

class SimpleCache:
    """Simple in-memory cache with TTL."""

    def __init__(self):
        self._store: Dict[str, tuple[Any, float]] = {}

    def get(self, key: str) -> Optional[Any]:
        if key in self._store:
            value, expiry = self._store[key]
            if time.time() < expiry:
                return value
            del self._store[key]
        return None

    def set(self, key: str, value: Any, ttl_seconds: int = 300):
        self._store[key] = (value, time.time() + ttl_seconds)

    def delete(self, key: str):
        self._store.pop(key, None)

    def clear(self):
        self._store.clear()


# ============================================================
# SECURITY HELPERS
# ============================================================

def hash_sensitive_data(data: str) -> str:
    """Hash sensitive data for logging."""
    return hashlib.sha256(data.encode()).hexdigest()[:16]


def mask_email(email: str) -> str:
    """Mask email for display/logging."""
    if "@" not in email:
        return "***"
    local, domain = email.split("@")
    masked_local = local[:2] + "***" if len(local) > 2 else "***"
    return f"{masked_local}@{domain}"


def sanitize_input(text: str, max_length: int = 10000) -> str:
    """Sanitize user input."""
    if not text:
        return ""
    # Remove null bytes
    text = text.replace("\x00", "")
    # Limit length
    text = text[:max_length]
    # Basic XSS prevention
    text = text.replace("<script", "&lt;script")
    text = text.replace("javascript:", "")
    return text


# ============================================================
# LANGUAGE / LOCALIZATION HELPERS
# ============================================================

LANGUAGE_NAMES = {
    "en": "English", "es": "Spanish", "fr": "French", "de": "German", "it": "Italian",
    "pt": "Portuguese", "ja": "Japanese", "ko": "Korean", "zh": "Chinese", "ar": "Arabic",
    "hi": "Hindi", "ru": "Russian", "tr": "Turkish", "pl": "Polish", "nl": "Dutch",
    "sv": "Swedish", "da": "Danish", "no": "Norwegian", "fi": "Finnish", "uk": "Ukrainian",
    "cs": "Czech", "sk": "Slovak", "hu": "Hungarian", "ro": "Romanian", "bg": "Bulgarian",
    "el": "Greek", "he": "Hebrew", "th": "Thai", "vi": "Vietnamese", "id": "Indonesian",
    "ms": "Malay", "tl": "Filipino", "bn": "Bengali", "ur": "Urdu", "fa": "Persian",
    "pa": "Punjabi", "ta": "Tamil", "te": "Telugu", "mr": "Marathi", "gu": "Gujarati",
    "kn": "Kannada", "ml": "Malayalam", "si": "Sinhala", "ne": "Nepali", "my": "Burmese",
    "km": "Khmer", "lo": "Lao", "mn": "Mongolian", "ka": "Georgian", "hy": "Armenian",
    "az": "Azerbaijani", "kk": "Kazakh", "uz": "Uzbek", "tg": "Tajik", "ky": "Kyrgyz",
    "tk": "Turkmen", "ps": "Pashto", "sd": "Sindhi", "am": "Amharic", "sw": "Swahili",
    "zu": "Zulu", "xh": "Xhosa", "af": "Afrikaans", "yo": "Yoruba", "ig": "Igbo",
    "ha": "Hausa", "so": "Somali", "rw": "Kinyarwanda", "st": "Sesotho", "sn": "Shona",
    "mg": "Malagasy", "lt": "Lithuanian", "lv": "Latvian", "et": "Estonian", "sl": "Slovenian",
    "hr": "Croatian", "sr": "Serbian", "bs": "Bosnian", "mk": "Macedonian", "sq": "Albanian",
    "is": "Icelandic", "ga": "Irish", "cy": "Welsh", "gd": "Scottish Gaelic", "mt": "Maltese",
    "eu": "Basque", "ca": "Catalan", "gl": "Galician", "lb": "Luxembourgish", "fo": "Faroese",
    "br": "Breton", "eo": "Esperanto", "la": "Latin", "sa": "Sanskrit", "yi": "Yiddish",
    "ku": "Kurdish", "ug": "Uyghur", "bo": "Tibetan", "dv": "Dhivehi", "jv": "Javanese",
    "su": "Sundanese",
}


def get_language_name(code: str) -> str:
    """Get human-readable language name."""
    return LANGUAGE_NAMES.get(code, code)


def get_supported_languages() -> List[Dict[str, str]]:
    """Get list of supported languages."""
    return [{"code": k, "name": v} for k, v in LANGUAGE_NAMES.items()]


# ============================================================
# NATIVE-LANGUAGE DETECTION
# Lets the AI companion figure out which language the user is actually
# typing/speaking in *right now*, so it can explain the target language
# being learned in the user's own words — offline, free, no external API.
# ============================================================

_detector_available = None


def detect_language(text: str, fallback: str = "en") -> str:
    """
    Detect the language a piece of text is written in, using the
    open-source `langdetect` library (offline, no API call, no cost).

    Falls back to `fallback` if the text is too short/ambiguous, low
    confidence, or the library isn't installed — never raises, so callers
    can use this unconditionally in a request path. Short strings (greetings
    like "Hi") are genuinely unreliable to classify, so anything under
    ~15 characters, or a top guess under 65% confidence, is treated as
    "not enough signal" rather than trusted.
    """
    global _detector_available
    text = (text or "").strip()
    if len(text) < 15:
        return fallback

    if _detector_available is False:
        return fallback

    try:
        from langdetect import DetectorFactory, detect_langs

        DetectorFactory.seed = 0  # deterministic results
        _detector_available = True
        candidates = detect_langs(text)
        if not candidates or candidates[0].prob < 0.65:
            return fallback
        code = candidates[0].lang.split("-")[0]  # normalize zh-cn/zh-tw etc.
        return code if code in LANGUAGE_NAMES else fallback
    except ImportError:
        _detector_available = False
        logger.warning("langdetect_not_installed", note="falling back to default language")
        return fallback
    except Exception as e:
        logger.debug("language_detection_failed", error=str(e))
        return fallback


def build_native_language_system_prompt(
    target_language: str,
    native_language: str,
    cefr_level: str = "A1",
    personality: str = "friendly_teacher",
) -> str:
    """
    Build the system prompt that makes Hermes teach the TARGET language
    while explaining everything in the user's NATIVE/spoken language —
    the "AI dost" behavior: explanations in the language the user is
    comfortable in, practice content in the language they're learning.
    """
    target_name = get_language_name(target_language)
    native_name = get_language_name(native_language)

    if target_language == native_language:
        # Same language on both sides — just be a normal friendly tutor.
        return (
            f"You are Hermes, a warm, encouraging AI language-learning companion — "
            f"like a supportive friend, not a textbook. The user is practicing "
            f"{target_name} at CEFR level {cefr_level}. Personality: {personality}. "
            f"Keep replies short, natural, and conversational."
        )

    return f"""You are Hermes, a warm, encouraging AI language-learning companion — like a close friend who happens to be fluent in {target_name}, not a textbook.

The user's TARGET language (what they want to learn): {target_name} ({target_language})
The user's NATIVE / currently-spoken language: {native_name} ({native_language})
Current level: CEFR {cefr_level}. Personality: {personality}.

How to respond, every single time:
1. Explain any grammar, vocabulary, corrections, or instructions in {native_name}, so the user genuinely understands — never leave them guessing.
2. Give the user practice phrases/sentences to say or write in {target_name}, and always translate them into {native_name} right after.
3. If the user writes to you in {native_name}, reply mostly in {native_name}, weaving in a few {target_name} words or phrases (with translation) so they keep absorbing the target language.
4. If the user attempts {target_name}, gently correct any mistakes — explain the correction in {native_name}, then show the corrected sentence in {target_name}.
5. Keep the tone warm, patient, and encouraging, like a friend cheering them on — never robotic or exam-like.
"""



# ============================================================
# SM-2 SPACED REPETITION ALGORITHM
# ============================================================

def sm2_update(
    quality: int,
    repetitions: int,
    ease_factor: float,
    interval: int,
) -> tuple[int, float, int]:
    """
    SM-2 algorithm update.

    Args:
        quality: Response quality (0-5)
        repetitions: Number of successful repetitions
        ease_factor: Current ease factor
        interval: Current interval in days

    Returns:
        Tuple of (new_interval, new_ease_factor, new_repetitions)
    """
    if quality < 3:
        return 1, ease_factor, 0

    if repetitions == 0:
        new_interval = 1
    elif repetitions == 1:
        new_interval = 6
    else:
        new_interval = int(interval * ease_factor)

    new_ease_factor = max(1.3, ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)))
    new_repetitions = repetitions + 1

    return new_interval, new_ease_factor, new_repetitions


# ============================================================
# BATCH PROCESSING HELPERS
# ============================================================

async def batch_process(
    items: List[T],
    process_func: Callable[[T], Any],
    batch_size: int = 10,
    concurrency: int = 5,
) -> List[Any]:
    """Process items in batches with concurrency control."""
    semaphore = asyncio.Semaphore(concurrency)
    results = []

    async def process_with_limit(item: T) -> Any:
        async with semaphore:
            return await process_func(item)

    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        batch_results = await asyncio.gather(
            *[process_with_limit(item) for item in batch],
            return_exceptions=True,
        )
        results.extend(batch_results)

    return results


# ============================================================
# HEALTH CHECK HELPERS
# ============================================================

async def check_dependency_health(url: str, timeout: float = 5.0) -> Dict[str, Any]:
    """Check health of a dependency service."""
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(f"{url}/health")
            return {
                "url": url,
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "status_code": response.status_code,
                "latency_ms": response.elapsed.total_seconds() * 1000,
            }
    except Exception as e:
        return {
            "url": url,
            "status": "unreachable",
            "error": str(e),
            "latency_ms": None,
        }


print("✅ shared/utils/helpers.py created")
