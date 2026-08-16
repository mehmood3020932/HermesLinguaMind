"""
Hermes LinguaMind — LLM Orchestration Service
Port: 8001 | Phase 3 — Production Ready
Provider abstraction with FreeLLMAPI + Ollama fallback
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import time
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel, Field
import structlog
import uvicorn
import httpx

from shared.models.common import HermesResponse, HealthStatus, LLMRequest, LLMResponse
from shared.utils.helpers import call_llm_with_fallback, generate_request_id, detect_language, build_native_language_system_prompt

logger = structlog.get_logger("hermes.llm")

app = FastAPI(
    title="Hermes LLM Orchestration",
    description="Provider-abstracted LLM routing with failover",
    version="3.0.0",
)

_app_start_time = time.time()

# Provider configuration.
# Real, genuinely-callable providers first (require the user's own API key),
# then a free-tier option, then self-hosted Ollama as the always-available
# last resort so the service degrades gracefully instead of faking output.
# Any provider without a configured API key is skipped automatically by
# call_llm_with_fallback (a request with a blank/invalid key returns a real
# 401 from the provider, which is treated as "unavailable, try next").
_ALL_PROVIDER_CONFIGS = {
    "openai": {
        "name": "openai",
        "url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        "api_key": os.getenv("OPENAI_API_KEY", ""),
        "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        "protocol": "openai",
        "priority": 1,
        "timeout": 30.0,
    },
    "anthropic": {
        "name": "anthropic",
        "url": os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com/v1"),
        "api_key": os.getenv("ANTHROPIC_API_KEY", ""),
        "model": os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5"),
        "protocol": "anthropic",
        "priority": 2,
        "timeout": 30.0,
    },
    "groq": {
        "name": "groq",
        "url": os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1"),
        "api_key": os.getenv("GROQ_API_KEY", ""),
        "model": os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        "protocol": "openai",
        "priority": 3,
        "timeout": 30.0,
    },
    "freellmapi": {
        "name": "freellmapi",
        "url": os.getenv("FREELLMAPI_BASE_URL", "https://api.freellmapi.com/v1"),
        "api_key": os.getenv("FREELLMAPI_KEY", ""),
        "model": "gpt-3.5-turbo",
        "protocol": "openai",
        "priority": 4,
        "timeout": 30.0,
    },
    # Hugging Face's OpenAI-compatible router — free tier available with a
    # personal HF access token (https://huggingface.co/settings/tokens),
    # used here for heavier open-weight models (Llama/Mistral/Qwen-class)
    # that would be too slow/large to run on Ollama's default light model.
    "huggingface": {
        "name": "huggingface",
        "url": os.getenv("HUGGINGFACE_BASE_URL", "https://router.huggingface.co/v1"),
        "api_key": os.getenv("HUGGINGFACE_API_KEY", ""),
        "model": os.getenv("HUGGINGFACE_MODEL", "meta-llama/Llama-3.2-3B-Instruct"),
        "protocol": "openai",
        "priority": 5,
        "timeout": 45.0,
    },
    "ollama": {
        "name": "ollama",
        "url": os.getenv("OLLAMA_BASE_URL", "http://ollama:11434/v1"),
        "api_key": "ollama",
        "model": os.getenv("OLLAMA_FALLBACK_MODEL", "llama3.1:8b"),
        "protocol": "openai",
        "priority": 7,
        "timeout": 60.0,
    },
}


def _build_colab_providers() -> List[Dict[str, Any]]:
    """
    Build one provider entry per Google Colab notebook tunnel the operator
    has running (one per free Google account, for extra heavy-model
    capacity at zero cost). Each notebook is expected to expose an
    OpenAI-compatible `/v1/chat/completions` endpoint — e.g. by running
    text-generation-webui with `--api --extension openai`, or a small
    FastAPI wrapper around `transformers`/`vllm`, then tunneling it out
    with ngrok/cloudflared and copying the public URL here.

    HONEST CAVEAT: this is a genuinely fragile fallback, not a production
    guarantee — free Colab sessions disconnect after inactivity, have a
    hard ~12h ceiling, and Google's ToS discourages using Colab as an
    always-on server. Treat this tier as free burst capacity for heavy
    models, sitting below Hugging Face and above the local Ollama model,
    which is the tier that's actually always available.

    Configure via COLAB_ENDPOINTS="https://acct1.ngrok-free.app/v1,https://acct2.ngrok-free.app/v1"
    (comma-separated — one URL per Google account's tunnel). Requests are
    round-robined across them so no single free account's quota/session
    absorbs all the traffic.
    """
    endpoints = [e.strip() for e in os.getenv("COLAB_ENDPOINTS", "").split(",") if e.strip()]
    model = os.getenv("COLAB_MODEL", "auto")
    providers = []
    for i, url in enumerate(endpoints):
        providers.append({
            "name": f"colab_{i+1}",
            "url": url,
            "api_key": os.getenv("COLAB_API_KEY", "colab"),
            "model": model,
            "protocol": "openai",
            "priority": 6,
            "timeout": 90.0,  # Colab cold starts / free-tier GPUs are slow
        })
    # Rotate the starting point each call so repeated requests don't always
    # hammer the same account first when several are configured.
    if len(providers) > 1:
        offset = int(time.time()) % len(providers)
        providers = providers[offset:] + providers[:offset]
    return providers

_order_env = os.getenv("LLM_PROVIDER_ORDER", "")
_order = [p.strip().lower() for p in _order_env.split(",") if p.strip()] or list(_ALL_PROVIDER_CONFIGS.keys())
PROVIDER_CONFIGS = [
    _ALL_PROVIDER_CONFIGS[name] for name in _order
    if name in _ALL_PROVIDER_CONFIGS and (name == "ollama" or _ALL_PROVIDER_CONFIGS[name]["api_key"])
]
# Colab notebook endpoints (0, 1, or many — one per Google account) are
# appended after the named providers. Controlled purely by whether
# COLAB_ENDPOINTS is set; empty by default so nothing changes unless the
# operator opts in.
PROVIDER_CONFIGS.extend(_build_colab_providers())
if not PROVIDER_CONFIGS:
    # Nothing configured at all — keep Ollama so the service still boots
    # and reports honestly via /v1/providers instead of crashing.
    PROVIDER_CONFIGS = [_ALL_PROVIDER_CONFIGS["ollama"]]

SYSTEM_PROMPTS = {
    "default": "You are Hermes, a friendly and knowledgeable language learning assistant.",
    "grammar_check": "You are a grammar expert. Analyze text for grammatical errors.",
    "pronunciation_feedback": "You are a pronunciation coach. Give encouraging feedback.",
    "conversation": "You are Hermes, a conversational language partner.",
    "lesson_generation": "You are a curriculum designer. Create engaging language lessons.",
}

_response_cache: Dict[str, Any] = {}
_cache_hits = 0
_cache_misses = 0

@app.get("/health", response_model=HealthStatus)
async def health_check():
    uptime = time.time() - _app_start_time
    dependencies = {}
    for provider in PROVIDER_CONFIGS:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(provider["url"].replace("/v1", ""))
                dependencies[provider["name"]] = "reachable"
        except Exception:
            dependencies[provider["name"]] = "unreachable"
    return HealthStatus(
        status="healthy", service="llm_orchestration", version="3.0.0",
        timestamp=datetime.utcnow(), uptime_seconds=uptime, dependencies=dependencies,
    )

@app.post("/v1/generate", response_model=HermesResponse)
async def generate_text(request: Request, llm_request: LLMRequest):
    request_id = getattr(request.state, "request_id", generate_request_id())
    start_time = time.time()
    cache_key = f"{llm_request.prompt}:{llm_request.model}:{llm_request.temperature}"
    cached = _response_cache.get(cache_key)
    if cached and not llm_request.stream:
        global _cache_hits
        _cache_hits += 1
        cached["cached"] = True
        return HermesResponse(success=True, data=cached, request_id=request_id)
    global _cache_misses
    _cache_misses += 1
    system_prompt = llm_request.system_prompt or SYSTEM_PROMPTS.get("default")
    if llm_request.language.value != "en":
        system_prompt += f" Respond in {llm_request.language.value} or the user's learning language."
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": llm_request.prompt},
    ]
    try:
        result = await call_llm_with_fallback(
            providers=PROVIDER_CONFIGS, messages=messages,
            temperature=llm_request.temperature, max_tokens=llm_request.max_tokens,
        )
        llm_response = LLMResponse(
            text=result["text"], model_used=result["model_used"],
            provider=result["provider"], tokens_used=result.get("tokens_used"),
            latency_ms=result["latency_ms"], cached=False,
        )
        if not llm_request.stream:
            _response_cache[cache_key] = llm_response.model_dump()
        total_latency = (time.time() - start_time) * 1000
        logger.info("llm_generation_complete", request_id=request_id, provider=result["provider"],
                    model=result["model_used"], total_latency_ms=round(total_latency, 2))
        return HermesResponse(success=True, data=llm_response.model_dump(), request_id=request_id)
    except Exception as e:
        logger.error("llm_generation_failed", request_id=request_id, error=str(e))
        return HermesResponse(success=False, error=f"LLM generation failed: {str(e)}",
                              error_code="LLM_ERROR", request_id=request_id)

class GrammarCheckRequest(BaseModel):
    text: str
    language: str = "en"
    cefr_level: Optional[str] = None

@app.post("/v1/grammar-check", response_model=HermesResponse)
async def grammar_check(request: Request, check_request: GrammarCheckRequest):
    request_id = getattr(request.state, "request_id", generate_request_id())
    prompt = f"""Analyze the following text for grammatical errors:

Text: "{check_request.text}"

Provide your analysis in this exact JSON format with is_grammatically_correct, errors list, suggested_rules, and confidence."""
    try:
        result = await call_llm_with_fallback(
            providers=PROVIDER_CONFIGS,
            messages=[{"role": "system", "content": SYSTEM_PROMPTS["grammar_check"]},
                      {"role": "user", "content": prompt}],
            temperature=0.3, max_tokens=1024,
        )
        response_text = result["text"]
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]
        grammar_result = json.loads(response_text.strip())
        return HermesResponse(success=True, data=grammar_result, request_id=request_id)
    except Exception as e:
        logger.error("grammar_check_failed", request_id=request_id, error=str(e))
        return HermesResponse(success=False, error=f"Grammar check failed: {str(e)}",
                              error_code="GRAMMAR_CHECK_ERROR", request_id=request_id)

class ConversationRequest(BaseModel):
    message: str
    conversation_history: List[Dict[str, str]] = Field(default_factory=list)
    language: str = "en"  # target language the user is LEARNING
    native_language: Optional[str] = None  # user's own/spoken language; auto-detected from `message` if omitted
    auto_detect_native_language: bool = True
    cefr_level: str = "A1"
    character_personality: str = "friendly_teacher"

@app.post("/v1/conversation", response_model=HermesResponse)
async def conversation(request: Request, conv_request: ConversationRequest):
    request_id = getattr(request.state, "request_id", generate_request_id())

    native_language = conv_request.native_language
    if not native_language and conv_request.auto_detect_native_language:
        native_language = detect_language(conv_request.message, fallback=conv_request.language)
    native_language = native_language or conv_request.language

    system_prompt = build_native_language_system_prompt(
        target_language=conv_request.language,
        native_language=native_language,
        cefr_level=conv_request.cefr_level,
        personality=conv_request.character_personality,
    )
    messages = [{"role": "system", "content": system_prompt}]
    for msg in conv_request.conversation_history[-10:]:
        messages.append(msg)
    messages.append({"role": "user", "content": conv_request.message})
    try:
        result = await call_llm_with_fallback(
            providers=PROVIDER_CONFIGS, messages=messages, temperature=0.8, max_tokens=512,
        )
        return HermesResponse(success=True, data={"response": result["text"], "provider": result["provider"],
                                                  "model": result["model_used"], "latency_ms": result["latency_ms"],
                                                  "native_language_used": native_language,
                                                  "target_language": conv_request.language},
                              request_id=request_id)
    except Exception as e:
        logger.error("conversation_failed", request_id=request_id, error=str(e))
        return HermesResponse(success=False, error="I'm having trouble connecting. Please try again.",
                              error_code="CONVERSATION_ERROR", request_id=request_id)

@app.get("/v1/providers", response_model=HermesResponse)
async def list_providers():
    providers_info = []
    for provider in PROVIDER_CONFIGS:
        status = "unknown"
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(provider["url"].replace("/v1", ""))
                status = "online" if response.status_code < 500 else "degraded"
        except Exception:
            status = "offline"
        providers_info.append({"name": provider["name"], "model": provider["model"],
                               "priority": provider["priority"], "status": status,
                               "timeout_seconds": provider["timeout"]})
    total = _cache_hits + _cache_misses
    return HermesResponse(success=True, data={"providers": providers_info, "cache_stats": {
        "hits": _cache_hits, "misses": _cache_misses,
        "hit_rate": _cache_hits / total if total > 0 else 0}},)

@app.get("/v1/metrics")
async def get_metrics():
    return {"cache_hits": _cache_hits, "cache_misses": _cache_misses,
            "providers_configured": len(PROVIDER_CONFIGS), "uptime_seconds": time.time() - _app_start_time}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
