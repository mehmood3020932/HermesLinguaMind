"""
Hermes Orchestrator — Main Service (Port 8020)
Layer 2 (Intent) + Layer 3 (Planning) + Layer 4 (Execution) + Layer 5 (Verification)
"""
import os
import sys
import time
import asyncio
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from contextlib import asynccontextmanager
from uuid import uuid4

import httpx
import structlog
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from shared.models.common import (
    IntentType, HermesResponse, OrchestrateRequest, SessionContext,
    TaskGraph, TaskNode, AdapterResult, VerificationResult,
    HealthResponse, IntentClassification
)
from shared.utils.helpers import Timer, idempotency_store, cache
from shared.middleware.auth import get_optional_user, RequestIDMiddleware, CORS_CONFIG

from services.hermes_orchestrator.intent.classifier import IntentClassifier
from services.hermes_orchestrator.planner.builder import TaskGraphBuilder
from services.hermes_orchestrator.verifier.engine import SelfQAVerifier

from services.hermes_orchestrator.adapters import (
    LLMAdapter, TTSAdapter, STTAdapter, VisemeAdapter,
    PronunciationAdapter, CoinLedgerAdapter, CurriculumAdapter,
    MemoryAdapter, ModerationAdapter, GrammarRuleDbAdapter,
    ContentGenerationAdapter, PersonalizationAdapter,
    GestureEmotionAdapter, LeaderboardAdapter,
    SocialExchangeAdapter, AntiFraudAdapter,
    LiveConversationAdapter, ObservabilityAdapter,
    SecurityAdapter
)

logger = structlog.get_logger()

# ─────────────────────────────────────────────────────────────
# LIFESPAN MANAGEMENT
# ─────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    app.state.start_time = time.time()
    app.state.request_count = 0
    app.state.error_count = 0

    # Initialize adapters
    app.state.adapters = {
        "llm": LLMAdapter(),
        "tts": TTSAdapter(),
        "stt": STTAdapter(),
        "viseme": VisemeAdapter(),
        "pronunciation": PronunciationAdapter(),
        "coin_ledger": CoinLedgerAdapter(),
        "curriculum": CurriculumAdapter(),
        "memory": MemoryAdapter(),
        "moderation": ModerationAdapter(),
        "grammar_rule_db": GrammarRuleDbAdapter(),
        "content_generation": ContentGenerationAdapter(),
        "personalization": PersonalizationAdapter(),
        "gesture_emotion": GestureEmotionAdapter(),
        "leaderboard": LeaderboardAdapter(),
        "social_exchange": SocialExchangeAdapter(),
        "anti_fraud": AntiFraudAdapter(),
        "live_conversation": LiveConversationAdapter(),
        "observability": ObservabilityAdapter(),
        "security": SecurityAdapter(),
    }

    # Initialize core components
    app.state.intent_classifier = IntentClassifier()
    app.state.task_graph_builder = TaskGraphBuilder()
    app.state.verifier = SelfQAVerifier(
        grammar_adapter=app.state.adapters["grammar_rule_db"],
        coin_ledger_adapter=app.state.adapters["coin_ledger"]
    )

    logger.info("orchestrator_startup_complete", port=8020)
    yield

    # Shutdown: close all adapters
    for name, adapter in app.state.adapters.items():
        try:
            await adapter.close()
        except Exception as e:
            logger.warning("adapter_close_error", name=name, error=str(e))
    logger.info("orchestrator_shutdown_complete")

# ─────────────────────────────────────────────────────────────
# FASTAPI APP
# ─────────────────────────────────────────────────────────────

app = FastAPI(
    title="Hermes Orchestrator",
    description="Layer 2-5 Orchestration Brain for Hermes LinguaMind",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(RequestIDMiddleware)
app.add_middleware(CORSMiddleware, **CORS_CONFIG)

# ─────────────────────────────────────────────────────────────
# HEALTH CHECK
# ─────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse)
async def health_check():
    uptime = time.time() - getattr(app.state, "start_time", time.time())

    # Check critical downstream services
    deps = {}
    critical_services = ["llm", "moderation", "coin_ledger"]
    for svc in critical_services:
        adapter = app.state.adapters.get(svc)
        if adapter:
            try:
                healthy = await asyncio.wait_for(adapter.health_check(), timeout=3.0)
                deps[svc] = "healthy" if healthy else "degraded"
            except Exception:
                deps[svc] = "unreachable"

    overall = "healthy" if all(v == "healthy" for v in deps.values()) else "degraded"

    return HealthResponse(
        status=overall,
        service="hermes_orchestrator",
        version="1.0.0",
        uptime_seconds=round(uptime, 2),
        dependencies=deps
    )

# ─────────────────────────────────────────────────────────────
# INTENT CLASSIFICATION ENDPOINT
# ─────────────────────────────────────────────────────────────

@app.post("/v1/orchestrate/classify-intent", response_model=IntentClassification)
async def classify_intent(request: Dict[str, Any]):
    """Classify user message intent (Layer 2 — standalone endpoint)."""
    message = request.get("message", "")
    context = request.get("context", {})

    if not message or len(message.strip()) < 1:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    intent, confidence, metadata = await app.state.intent_classifier.classify(
        message=message,
        context=context,
        use_llm_fallback=True
    )

    return IntentClassification(
        intent=intent,
        confidence=confidence,
        raw_message=message,
        metadata=metadata
    )

# ─────────────────────────────────────────────────────────────
# MAIN ORCHESTRATION ENDPOINT
# ─────────────────────────────────────────────────────────────

@app.post("/v1/orchestrate", response_model=HermesResponse)
async def orchestrate(request: OrchestrateRequest):
    """
    Main orchestration endpoint — full Layer 2→3→4→5 pipeline.
    """
    start_time = time.perf_counter()
    request_id = f"req_{int(time.time() * 1000)}_{hash(request.user_id) % 10000}"

    logger.info(
        "orchestration_start",
        request_id=request_id,
        user_id=request.user_id,
        message_preview=request.message[:100] if request.message else ""
    )

    try:
        # ── Step 1: Intent Classification ──
        with Timer("intent_classification") as t_intent:
            intent, confidence, intent_meta = await app.state.intent_classifier.classify(
                message=request.message,
                context=request.session_context.custom_params if request.session_context else {},
                use_llm_fallback=True
            )

        # ── Step 2: Build Task Graph ──
        with Timer("task_graph_build") as t_plan:
            task_graph = app.state.task_graph_builder.build(
                intent=intent,
                user_id=request.user_id,
                message=request.message,
                session_context=request.session_context,
                audio_input=request.audio_input,
                image_input=request.image_input
            )

        # ── Step 3: Execute Task Graph ──
        with Timer("task_execution") as t_exec:
            adapter_results = await execute_task_graph(
                task_graph=task_graph,
                adapters=app.state.adapters,
                user_message=request.message
            )

        # ── Step 4: Self-QA Verification ──
        with Timer("verification") as t_verify:
            verification_results = await app.state.verifier.verify(
                intent=intent,
                adapter_results=adapter_results,
                user_id=request.user_id,
                request_id=request_id
            )

        # ── Step 5: Build Response ──
        response = build_hermes_response(
            intent=intent,
            confidence=confidence,
            adapter_results=adapter_results,
            verification_results=verification_results,
            request_id=request_id,
            user_id=request.user_id,
            start_time=start_time
        )

        # Store idempotency for coin transactions
        if intent == IntentType.LESSON_COMPLETION and response.coins_awarded > 0:
            idempotency_store.mark_processed(request_id, {
                "coins_awarded": response.coins_awarded,
                "lesson_id": request.session_context.current_lesson_id if request.session_context else None
            })

        app.state.request_count += 1
        logger.info(
            "orchestration_success",
            request_id=request_id,
            intent=intent.value,
            latency_ms=response.latency_ms,
            verification_passed=response.verification_passed
        )

        return response

    except Exception as e:
        app.state.error_count += 1
        logger.error(
            "orchestration_error",
            request_id=request_id,
            error=str(e),
            error_type=type(e).__name__
        )
        # NEVER return raw 500 — always friendly fallback
        return HermesResponse(
            success=False,
            request_id=request_id,
            user_id=request.user_id,
            text="I'm sorry, I'm having a little trouble right now. Let's try again in a moment! 🌟",
            emotion="neutral",
            error_message="A temporary issue occurred. Please retry.",
            error_code="ORCHESTRATOR_001",
            suggested_action="retry",
            latency_ms=(time.perf_counter() - start_time) * 1000,
            fallback_used=True
        )

# ─────────────────────────────────────────────────────────────
# TASK GRAPH EXECUTION ENGINE
# ─────────────────────────────────────────────────────────────

async def execute_task_graph(
    task_graph: TaskGraph,
    adapters: Dict[str, Any],
    user_message: str
) -> Dict[str, Any]:
    """
    Execute task graph with parallel optimization.
    Resolves placeholders from previous results.
    """
    results: Dict[str, Any] = {}
    completed_nodes: Dict[str, Any] = {}

    # Execute by dependency order (parallel groups)
    for group in task_graph.parallel_groups:
        tasks = []
        node_map = {}

        for node_id in group:
            node = next((n for n in task_graph.nodes if n.id == node_id), None)
            if not node:
                continue

            # Skip if dependencies not met
            if node.depends_on and not all(d in completed_nodes for d in node.depends_on):
                logger.warning("dependency_not_met", node=node_id, missing=node.depends_on)
                continue

            # Resolve placeholders in payload
            payload = resolve_payload_placeholders(
                node.payload, completed_nodes, user_message
            )

            # Get adapter
            adapter = adapters.get(node.service)
            if not adapter:
                logger.error("adapter_not_found", service=node.service)
                completed_nodes[node_id] = AdapterResult(
                    service=node.service,
                    endpoint=node.endpoint,
                    success=False,
                    error=f"Adapter not found for {node.service}"
                )
                continue

            # Create task
            task = execute_single_node(adapter, node, payload)
            tasks.append(task)
            node_map[len(tasks) - 1] = node_id

        # Execute parallel group
        if tasks:
            group_results = await asyncio.gather(*tasks, return_exceptions=True)

            for idx, result in enumerate(group_results):
                node_id = node_map[idx]
                if isinstance(result, Exception):
                    node_service = task_graph.nodes[[n.id for n in task_graph.nodes].index(node_id)].service
                    completed_nodes[node_id] = AdapterResult(
                        service=node_service,
                        endpoint="",
                        success=False,
                        error=str(result)
                    )
                else:
                    completed_nodes[node_id] = result

    # Organize results by service name
    for node in task_graph.nodes:
        if node.id in completed_nodes:
            results[node.service] = completed_nodes[node.id]

    return results

async def execute_single_node(adapter, node: TaskNode, payload: Dict[str, Any]) -> AdapterResult:
    """Execute a single task node."""
    try:
        result = await adapter._request(
            method=node.method,
            endpoint=node.endpoint,
            payload=payload
        )
        return result
    except Exception as e:
        logger.error("node_execution_failed", 
                    service=node.service, 
                    endpoint=node.endpoint,
                    error=str(e))
        return AdapterResult(
            service=node.service,
            endpoint=node.endpoint,
            success=False,
            error=str(e)
        )

def resolve_payload_placeholders(
    payload: Dict[str, Any],
    completed_nodes: Dict[str, AdapterResult],
    user_message: str
) -> Dict[str, Any]:
    """Replace {{placeholder}} values with actual results from previous nodes."""
    resolved = {}

    for key, value in payload.items():
        if isinstance(value, str) and value.startswith("{{") and value.endswith("}}"):
            placeholder = value[2:-2]

            if placeholder == "llm_response_text":
                # Find LLM result
                llm_result = None
                for nid, result in completed_nodes.items():
                    if hasattr(result, 'service') and result.service == "llm" and result.success:
                        llm_result = result
                        break
                if llm_result and llm_result.success:
                    text = llm_result.data.get("text", llm_result.data.get("response", user_message))
                    resolved[key] = text
                else:
                    resolved[key] = user_message

            elif placeholder == "grammar_correction_text":
                llm_result = None
                for nid, result in completed_nodes.items():
                    if hasattr(result, 'service') and result.service == "llm" and result.success:
                        llm_result = result
                        break
                if llm_result and llm_result.success:
                    corrected = llm_result.data.get("corrected", user_message)
                    resolved[key] = corrected
                else:
                    resolved[key] = user_message

            elif placeholder == "content_text":
                content_result = None
                for nid, result in completed_nodes.items():
                    if hasattr(result, 'service') and result.service == "content_generation" and result.success:
                        content_result = result
                        break
                if content_result and content_result.success:
                    items = content_result.data.get("items", [])
                    text = items[0].get("text", "") if items else user_message
                    resolved[key] = text
                else:
                    resolved[key] = user_message

            elif placeholder == "tts_text":
                resolved[key] = user_message

            elif placeholder == "detected_emotion":
                llm_result = None
                for nid, result in completed_nodes.items():
                    if hasattr(result, 'service') and result.service == "llm" and result.success:
                        llm_result = result
                        break
                if llm_result and llm_result.success:
                    emotion = llm_result.data.get("emotion", "neutral")
                    resolved[key] = emotion
                else:
                    resolved[key] = "neutral"

            elif placeholder == "llm_grammar_claim":
                llm_result = None
                for nid, result in completed_nodes.items():
                    if hasattr(result, 'service') and result.service == "llm" and result.success:
                        llm_result = result
                        break
                if llm_result and llm_result.success:
                    errors = llm_result.data.get("errors", [])
                    claim = errors[0].get("explanation", "") if errors else ""
                    resolved[key] = claim
                else:
                    resolved[key] = ""

            else:
                resolved[key] = value
        else:
            resolved[key] = value

    return resolved

# ─────────────────────────────────────────────────────────────
# RESPONSE AGGREGATOR
# ─────────────────────────────────────────────────────────────

def build_hermes_response(
    intent: IntentType,
    confidence: float,
    adapter_results: Dict[str, Any],
    verification_results: List[VerificationResult],
    request_id: str,
    user_id: str,
    start_time: float
) -> HermesResponse:
    """Aggregate all adapter results into unified HermesResponse."""

    latency_ms = (time.perf_counter() - start_time) * 1000
    all_critical_passed = all(
        r.passed for r in verification_results if r.severity == "critical"
    )

    # Extract LLM text
    llm_result = adapter_results.get("llm")
    llm_data = {}
    if llm_result:
        if hasattr(llm_result, 'data'):
            llm_data = llm_result.data
        elif isinstance(llm_result, dict):
            llm_data = llm_result.get("data", {})

    response_text = ""
    if isinstance(llm_data, dict):
        response_text = llm_data.get("text", llm_data.get("response", ""))

    # Extract TTS audio
    tts_result = adapter_results.get("tts")
    tts_data = {}
    if tts_result:
        if hasattr(tts_result, 'data'):
            tts_data = tts_result.data
        elif isinstance(tts_result, dict):
            tts_data = tts_result.get("data", {})

    audio_url = ""
    if isinstance(tts_data, dict):
        audio_url = tts_data.get("audio_url", "")

    # Extract viseme timeline
    viseme_result = adapter_results.get("viseme")
    viseme_data = {}
    if viseme_result:
        if hasattr(viseme_result, 'data'):
            viseme_data = viseme_result.data
        elif isinstance(viseme_result, dict):
            viseme_data = viseme_result.get("data", {})

    viseme_timeline = None
    if isinstance(viseme_data, dict):
        viseme_timeline = viseme_data.get("timeline")

    # Extract gesture
    gesture_result = adapter_results.get("gesture_emotion")
    gesture_data = {}
    if gesture_result:
        if hasattr(gesture_result, 'data'):
            gesture_data = gesture_result.data
        elif isinstance(gesture_result, dict):
            gesture_data = gesture_result.get("data", {})

    gesture = None
    if isinstance(gesture_data, dict):
        gesture = gesture_data.get("gesture")

    # Extract coins
    coin_result = adapter_results.get("coin_ledger")
    coin_data = {}
    if coin_result:
        if hasattr(coin_result, 'data'):
            coin_data = coin_result.data
        elif isinstance(coin_result, dict):
            coin_data = coin_result.get("data", {})

    coins_awarded = 0
    coins_total = None
    if isinstance(coin_data, dict):
        coins_awarded = coin_data.get("amount", 0)
        coins_total = coin_data.get("balance")

    # Extract grammar correction
    grammar_correction = None
    if isinstance(llm_data, dict) and "errors" in llm_data:
        grammar_correction = {
            "original": llm_data.get("original", ""),
            "corrected": llm_data.get("corrected"),
            "errors": llm_data.get("errors", [])
        }

    # Extract pronunciation score
    pron_result = adapter_results.get("pronunciation")
    pron_data = {}
    if pron_result:
        if hasattr(pron_result, 'data'):
            pron_data = pron_result.data
        elif isinstance(pron_result, dict):
            pron_data = pron_result.get("data", {})

    pronunciation_score = None
    if isinstance(pron_data, dict):
        pronunciation_score = pron_data.get("overall_score")

    # Build response
    response = HermesResponse(
        success=all_critical_passed,
        request_id=request_id,
        user_id=user_id,
        text=response_text or "I'm here to help you learn! What would you like to practice? 📚",
        audio_url=audio_url or None,
        viseme_timeline=viseme_timeline,
        gesture=gesture,
        emotion="neutral",
        coins_awarded=coins_awarded,
        coins_total=coins_total,
        xp_gained=coins_awarded,
        grammar_correction=grammar_correction,
        pronunciation_score=pronunciation_score,
        intent=intent,
        confidence=confidence,
        latency_ms=round(latency_ms, 2),
        verification_passed=all_critical_passed,
        fallback_used=not all_critical_passed,
        debug={
            "adapter_results": {k: (v.success if hasattr(v, 'success') else True) 
                              for k, v in adapter_results.items()},
            "verification_results": [
                {"check": r.check_type, "passed": r.passed, "severity": r.severity}
                for r in verification_results
            ]
        }
    )

    return response

# ─────────────────────────────────────────────────────────────
# METRICS ENDPOINT
# ─────────────────────────────────────────────────────────────

@app.get("/v1/metrics")
async def get_metrics():
    """Service metrics for observability."""
    uptime = time.time() - getattr(app.state, "start_time", time.time())
    total = getattr(app.state, "request_count", 0)
    errors = getattr(app.state, "error_count", 0)

    return {
        "service": "hermes_orchestrator",
        "uptime_seconds": round(uptime, 2),
        "total_requests": total,
        "error_count": errors,
        "error_rate": round(errors / max(total, 1), 4),
        "circuit_breaker_states": {
            name: adapter.circuit_breaker.state
            for name, adapter in app.state.adapters.items()
        }
    }

# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8020, log_level="info")
