"""
Phase 4 Complete Test Suite
Runs all unit + integration tests with import verification.
"""
import sys
import os
import importlib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_all_imports():
    """GATE B: Verify all imports work."""
    modules = [
        "shared.models.common",
        "shared.utils.helpers",
        "shared.middleware.auth",
        "services.hermes_orchestrator.intent.classifier",
        "services.hermes_orchestrator.planner.builder",
        "services.hermes_orchestrator.verifier.engine",
        "services.hermes_orchestrator.adapters.base",
        "services.hermes_orchestrator.adapters.llm_adapter",
        "services.hermes_orchestrator.adapters.tts_adapter",
        "services.hermes_orchestrator.adapters.coin_ledger_adapter",
        "services.hermes_orchestrator.adapters.grammar_rule_db_adapter",
    ]

    for module in modules:
        imported = importlib.import_module(module)
        assert imported is not None, f"Failed to import {module}"

def test_intent_enum_matches():
    """Verify IntentType enum has exactly 10 values as documented."""
    from shared.models.common import IntentType
    expected = {
        "conversational", "grammar_practice", "speaking_practice",
        "listening_practice", "vocabulary_practice", "lesson_completion",
        "coin_transaction", "social_interaction", "profile_update", "unknown"
    }
    actual = {i.value for i in IntentType}
    assert actual == expected

def test_hermes_response_model():
    """Verify HermesResponse model structure."""
    from shared.models.common import HermesResponse, IntentType

    resp = HermesResponse(
        success=True,
        request_id="test_123",
        user_id="user_1",
        text="Hello!",
        intent=IntentType.CONVERSATIONAL,
        confidence=0.95
    )
    assert resp.success is True
    assert resp.fallback_used is False

def test_service_registry_includes_orchestrator():
    """Verify gateway registry includes Phase 4 service."""
    from services.hermes_orchestrator.adapters.base import BaseAdapter
    adapter = BaseAdapter("hermes_orchestrator")
    assert adapter._default_port() == 8020

def test_circuit_breaker_exists():
    """Verify circuit breaker pattern is available."""
    from shared.utils.helpers import CircuitBreaker, CircuitBreakerOpen
    cb = CircuitBreaker("test")
    assert cb.state == "CLOSED"
    assert cb.FAILURE_THRESHOLD == 3

def test_idempotency_store():
    """Verify idempotency tracking works."""
    from shared.utils.helpers import idempotency_store
    assert idempotency_store.is_processed("new_key") is False
    idempotency_store.mark_processed("new_key", {"result": "ok"})
    assert idempotency_store.is_processed("new_key") is True
    assert idempotency_store.get_result("new_key") == {"result": "ok"}
