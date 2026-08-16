"""
Hermes Orchestrator — Layer 3: Orchestration Planning (Task-Graph)
Builds execution plans based on IntentType.
"""
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import structlog

from shared.models.common import (
    IntentType, TaskNode, TaskGraph, SessionContext,
    CEFRLevel, LanguageCode
)

logger = structlog.get_logger()

# ─────────────────────────────────────────────────────────────
# INTENT → SERVICE SEQUENCE MAPPING
# ─────────────────────────────────────────────────────────────

INTENT_EXECUTION_PLANS = {
    IntentType.CONVERSATIONAL: [
        {"service": "moderation", "endpoint": "/v1/moderate", "method": "POST", "parallel": False},
        {"service": "llm", "endpoint": "/v1/conversation", "method": "POST", "parallel": False},
        {"service": "tts", "endpoint": "/v1/synthesize", "method": "POST", "parallel": True, "depends_on": ["llm"]},
        {"service": "viseme", "endpoint": "/v1/generate", "method": "POST", "parallel": True, "depends_on": ["llm"]},
        {"service": "gesture_emotion", "endpoint": "/v1/gesture", "method": "POST", "parallel": True, "depends_on": ["llm"]},
    ],
    IntentType.GRAMMAR_PRACTICE: [
        {"service": "llm", "endpoint": "/v1/grammar-check", "method": "POST", "parallel": False},
        {"service": "grammar_rule_db", "endpoint": "/v1/verify", "method": "POST", "parallel": False, "depends_on": ["llm"]},
        {"service": "tts", "endpoint": "/v1/synthesize", "method": "POST", "parallel": True, "depends_on": ["grammar_rule_db"]},
    ],
    IntentType.SPEAKING_PRACTICE: [
        {"service": "stt", "endpoint": "/v1/transcribe", "method": "POST", "parallel": False},
        {"service": "pronunciation", "endpoint": "/v1/score", "method": "POST", "parallel": False, "depends_on": ["stt"]},
        {"service": "llm", "endpoint": "/v1/generate", "method": "POST", "parallel": False, "depends_on": ["pronunciation"]},
    ],
    IntentType.LISTENING_PRACTICE: [
        {"service": "content_generation", "endpoint": "/v1/generate", "method": "POST", "parallel": False},
        {"service": "tts", "endpoint": "/v1/synthesize", "method": "POST", "parallel": False, "depends_on": ["content_generation"]},
    ],
    IntentType.VOCABULARY_PRACTICE: [
        {"service": "curriculum", "endpoint": "/v1/curriculum", "method": "POST", "parallel": False},
        {"service": "personalization", "endpoint": "/v1/analyze", "method": "POST", "parallel": True, "depends_on": ["curriculum"]},
    ],
    IntentType.LESSON_COMPLETION: [
        {"service": "curriculum", "endpoint": "/v1/complete-lesson", "method": "POST", "parallel": False},
        {"service": "anti_fraud", "endpoint": "/v1/check", "method": "POST", "parallel": True, "depends_on": ["curriculum"]},
        {"service": "coin_ledger", "endpoint": "/v1/transaction", "method": "POST", "parallel": False, "depends_on": ["anti_fraud"]},
        {"service": "coin_ledger", "endpoint": "/v1/reconcile", "method": "POST", "parallel": False, "depends_on": ["coin_ledger"]},
    ],
    IntentType.COIN_TRANSACTION: [
        {"service": "anti_fraud", "endpoint": "/v1/check", "method": "POST", "parallel": False},
        {"service": "coin_ledger", "endpoint": "/v1/transaction", "method": "POST", "parallel": False, "depends_on": ["anti_fraud"]},
        {"service": "coin_ledger", "endpoint": "/v1/reconcile", "method": "POST", "parallel": False, "depends_on": ["coin_ledger"]},
    ],
    IntentType.SOCIAL_INTERACTION: [
        {"service": "moderation", "endpoint": "/v1/moderate", "method": "POST", "parallel": False},
        {"service": "social_exchange", "endpoint": "/v1/match", "method": "POST", "parallel": False, "depends_on": ["moderation"]},
    ],
    IntentType.PROFILE_UPDATE: [
        {"service": "personalization", "endpoint": "/v1/analyze", "method": "POST", "parallel": False},
        {"service": "memory", "endpoint": "/v1/store", "method": "POST", "parallel": False, "depends_on": ["personalization"]},
    ],
    IntentType.UNKNOWN: [
        {"service": "llm", "endpoint": "/v1/generate", "method": "POST", "parallel": False},
        {"service": "moderation", "endpoint": "/v1/moderate", "method": "POST", "parallel": True, "depends_on": ["llm"]},
    ],
}

# Service-specific timeout configurations
SERVICE_TIMEOUTS = {
    "llm": 45.0,
    "tts": 20.0,
    "stt": 30.0,
    "viseme": 15.0,
    "pronunciation": 25.0,
    "coin_ledger": 10.0,
    "curriculum": 10.0,
    "memory": 8.0,
    "moderation": 10.0,
    "grammar_rule_db": 10.0,
    "content_generation": 30.0,
    "personalization": 15.0,
    "gesture_emotion": 10.0,
    "leaderboard": 8.0,
    "social_exchange": 15.0,
    "anti_fraud": 10.0,
    "live_conversation": 10.0,
    "observability": 5.0,
    "security": 5.0,
}

class TaskGraphBuilder:
    """
    Builds execution task graphs based on intent classification.
    Handles parallel group detection and dependency resolution.
    """

    def __init__(self):
        self._node_counter = 0

    def build(
        self,
        intent: IntentType,
        user_id: str,
        message: str,
        session_context: Optional[SessionContext] = None,
        audio_input: Optional[str] = None,
        image_input: Optional[str] = None
    ) -> TaskGraph:
        """
        Build a complete TaskGraph for the given intent.
        """
        self._node_counter = 0
        session_context = session_context or SessionContext(user_id=user_id)

        plan_template = INTENT_EXECUTION_PLANS.get(intent, INTENT_EXECUTION_PLANS[IntentType.UNKNOWN])

        nodes: List[TaskNode] = []
        node_map: Dict[str, str] = {}  # service_endpoint -> node_id

        for step in plan_template:
            node_id = self._next_node_id()
            service = step["service"]
            endpoint = step["endpoint"]

            # Build payload based on service and intent
            payload = self._build_payload(
                service=service,
                endpoint=endpoint,
                intent=intent,
                user_id=user_id,
                message=message,
                session_context=session_context,
                audio_input=audio_input,
                image_input=image_input,
                previous_results=node_map
            )

            # Resolve dependencies
            depends_on = []
            if "depends_on" in step:
                for dep_service in step["depends_on"]:
                    # Find the most recent node for this service
                    for nid, svc in [(k, v) for k, v in node_map.items()]:
                        if svc == dep_service:
                            depends_on.append(nid)
                            break

            node = TaskNode(
                id=node_id,
                service=service,
                endpoint=endpoint,
                method=step.get("method", "POST"),
                payload=payload,
                depends_on=depends_on,
                timeout_seconds=SERVICE_TIMEOUTS.get(service, 30.0),
                retries=2,
                fallback_action="skip" if intent != IntentType.COIN_TRANSACTION else "fail"
            )

            nodes.append(node)
            node_map[node_id] = service

        # Compute parallel execution groups
        parallel_groups = self._compute_parallel_groups(nodes)

        graph = TaskGraph(
            intent=intent,
            user_id=user_id,
            nodes=nodes,
            parallel_groups=parallel_groups
        )

        logger.info(
            "task_graph_built",
            intent=intent.value,
            node_count=len(nodes),
            parallel_groups=len(parallel_groups),
            user_id=user_id
        )

        return graph

    def _next_node_id(self) -> str:
        self._node_counter += 1
        return f"node_{self._node_counter:03d}"

    def _build_payload(
        self,
        service: str,
        endpoint: str,
        intent: IntentType,
        user_id: str,
        message: str,
        session_context: SessionContext,
        audio_input: Optional[str],
        image_input: Optional[str],
        previous_results: Dict[str, str]
    ) -> Dict[str, Any]:
        """Build service-specific payload based on the execution context."""

        lang = session_context.custom_params.get("target_language", "en")
        cefr = session_context.custom_params.get("cefr_level", "A1")

        # ── LLM Service ──
        if service == "llm":
            if endpoint == "/v1/conversation":
                return {
                    "messages": session_context.conversation_history + [{"role": "user", "content": message}],
                    "user_id": user_id,
                    "context": {
                        "language": lang,
                        "cefr_level": cefr,
                        "current_lesson": session_context.current_lesson_id,
                        "intent": intent.value
                    }
                }
            elif endpoint == "/v1/grammar-check":
                return {
                    "text": message,
                    "target_language": lang,
                    "user_cefr": cefr
                }
            elif endpoint == "/v1/generate":
                if intent == IntentType.SPEAKING_PRACTICE:
                    return {
                        "prompt": f"Provide encouraging feedback for speaking practice. User said: {message}",
                        "system_prompt": "You are a supportive language tutor giving speaking feedback.",
                        "max_tokens": 300,
                        "temperature": 0.7
                    }
                else:
                    return {
                        "prompt": f"Respond helpfully to: {message}",
                        "system_prompt": "You are Hermes, a friendly AI language tutor.",
                        "max_tokens": 500,
                        "temperature": 0.7
                    }

        # ── TTS Service ──
        elif service == "tts":
            text_to_speak = message
            # For conversational, use LLM response text (will be injected at runtime)
            if intent == IntentType.CONVERSATIONAL:
                text_to_speak = "{{llm_response_text}}"  # Placeholder for runtime injection
            elif intent == IntentType.GRAMMAR_PRACTICE:
                text_to_speak = "{{grammar_correction_text}}"
            elif intent == IntentType.LISTENING_PRACTICE:
                text_to_speak = "{{content_text}}"

            return {
                "text": text_to_speak,
                "language": lang,
                "voice_id": session_context.preferred_voice,
                "speed": 1.0,
                "emotion": "neutral"
            }

        # ── STT Service ──
        elif service == "stt":
            return {
                "audio_base64": audio_input or "",
                "language": lang
            }

        # ── Viseme Service ──
        elif service == "viseme":
            return {
                "text": "{{tts_text}}",
                "language": lang
            }

        # ── Pronunciation Service ──
        elif service == "pronunciation":
            return {
                "audio_base64": audio_input or "",
                "expected_text": message,
                "language": lang,
                "user_cefr": cefr
            }

        # ── Grammar Rule DB ──
        elif service == "grammar_rule_db":
            return {
                "claim": "{{llm_grammar_claim}}",
                "language": lang
            }

        # ── Content Generation ──
        elif service == "content_generation":
            return {
                "content_type": "dialogue",
                "topic": message,
                "language": lang,
                "cefr_level": cefr,
                "count": 1,
                "constraints": {"audio_enabled": True}
            }

        # ── Curriculum ──
        elif service == "curriculum":
            if endpoint == "/v1/curriculum":
                return {
                    "user_id": user_id,
                    "language": lang,
                    "cefr_level": cefr,
                    "module_id": session_context.current_module_id
                }
            elif endpoint == "/v1/complete-lesson":
                return {
                    "user_id": user_id,
                    "lesson_id": session_context.current_lesson_id or "lesson_unknown",
                    "module_id": session_context.current_module_id or "module_unknown",
                    "score": session_context.custom_params.get("score", 80.0),
                    "time_spent_seconds": session_context.custom_params.get("time_spent", 300)
                }

        # ── Personalization ──
        elif service == "personalization":
            return {
                "user_id": user_id,
                "interaction_data": {
                    "message": message,
                    "intent": intent.value,
                    "timestamp": datetime.utcnow().isoformat(),
                    "session_id": session_context.session_id
                },
                "analysis_type": "learning_style"
            }

        # ── Memory ──
        elif service == "memory":
            return {
                "user_id": user_id,
                "memory_type": "conversation",
                "content": {
                    "message": message,
                    "intent": intent.value,
                    "timestamp": datetime.utcnow().isoformat()
                },
                "ttl_seconds": 86400 * 30  # 30 days
            }

        # ── Moderation ──
        elif service == "moderation":
            return {
                "user_id": user_id,
                "text": message,
                "image_base64": image_input,
                "context": f"intent:{intent.value}"
            }

        # ── Gesture/Emotion ──
        elif service == "gesture_emotion":
            return {
                "text": "{{llm_response_text}}",
                "emotion": "{{detected_emotion}}",
                "context": intent.value
            }

        # ── Coin Ledger ──
        elif service == "coin_ledger":
            if endpoint == "/v1/transaction":
                from shared.utils.helpers import generate_idempotency_key
                return {
                    "user_id": user_id,
                    "amount": session_context.custom_params.get("coin_amount", 10),
                    "transaction_type": "award",
                    "reason": f"Lesson completion: {session_context.current_lesson_id}",
                    "idempotency_key": generate_idempotency_key(
                        user_id, session_context.current_lesson_id or "unknown", 
                        datetime.utcnow().strftime("%Y-%m-%d")
                    ),
                    "metadata": {"intent": intent.value, "lesson_id": session_context.current_lesson_id}
                }
            elif endpoint == "/v1/reconcile":
                return {"user_id": user_id}

        # ── Anti-Fraud ──
        elif service == "anti_fraud":
            return {
                "user_id": user_id,
                "action": "coin_award" if intent == IntentType.LESSON_COMPLETION else "transaction",
                "amount": session_context.custom_params.get("coin_amount", 10),
                "metadata": {"intent": intent.value, "lesson_id": session_context.current_lesson_id}
            }

        # ── Social Exchange ──
        elif service == "social_exchange":
            return {
                "user_id": user_id,
                "match_type": "conversation",
                "preferred_language": lang,
                "cefr_level": cefr
            }

        # ── Leaderboard ──
        elif service == "leaderboard":
            return {
                "period": "weekly",
                "language": lang,
                "limit": 10
            }

        # ── Live Conversation ──
        elif service == "live_conversation":
            return {
                "user_id": user_id,
                "scenario": message,
                "target_language": lang,
                "difficulty": cefr,
                "duration_minutes": 10
            }

        # ── Observability ──
        elif service == "observability":
            return {
                "service": "hermes_orchestrator",
                "metric_type": "intent_processed",
                "intent": intent.value,
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat()
            }

        # ── Security ──
        elif service == "security":
            return {
                "user_id": user_id,
                "action": "orchestrate",
                "service": "hermes_orchestrator",
                "endpoint": "/v1/orchestrate",
                "metadata": {"intent": intent.value}
            }

        return {"user_id": user_id, "message": message, "intent": intent.value}

    def _compute_parallel_groups(self, nodes: List[TaskNode]) -> List[List[str]]:
        """
        Compute which nodes can execute in parallel.
        Returns list of lists, where each inner list contains node IDs that can run together.
        """
        if not nodes:
            return []

        groups = []
        current_group = []
        current_deps = set()

        for node in nodes:
            # If node has no dependencies or all dependencies are in previous groups
            if not node.depends_on or all(
                dep_id in current_deps or any(dep_id in g for g in groups)
                for dep_id in node.depends_on
            ):
                current_group.append(node.id)
            else:
                # Start new group
                if current_group:
                    groups.append(current_group)
                    current_deps.update(current_group)
                current_group = [node.id]

        if current_group:
            groups.append(current_group)

        return groups
