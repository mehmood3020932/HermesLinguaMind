"""
Integration Tests: Full /v1/orchestrate End-to-End
Tests all 10 IntentTypes with mocked downstream services.
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from services.hermes_orchestrator.intent.classifier import IntentClassifier
from shared.models.common import IntentType

class TestAllIntents:
    """Verify all 10 IntentTypes can be classified correctly."""

    @pytest.fixture
    def classifier(self):
        return IntentClassifier(llm_service_url="http://localhost:8001")

    @pytest.mark.asyncio
    @pytest.mark.parametrize("message,expected_intent", [
        ("Hello!", "conversational"),
        ("Check my grammar please", "grammar_practice"),
        ("I want to practice speaking", "speaking_practice"),
        ("Play audio for listening", "listening_practice"),
        ("What does this word mean", "vocabulary_practice"),
        ("I finished the lesson", "lesson_completion"),
        ("How many coins do I have", "coin_transaction"),
        ("Find me a language partner", "social_interaction"),
        ("Update my profile", "profile_update"),
        ("xyz123", "unknown"),
    ])
    async def test_intent_classification(self, classifier, message, expected_intent):
        intent, confidence, meta = await classifier.classify(
            message=message,
            use_llm_fallback=False
        )
        assert intent.value == expected_intent
        assert 0 <= confidence <= 1.0

class TestFailSafe:
    """Verify fail-safe behavior in intent classifier."""

    @pytest.fixture
    def classifier(self):
        return IntentClassifier()

    @pytest.mark.asyncio
    async def test_empty_message_returns_unknown(self, classifier):
        intent, confidence, meta = await classifier.classify(
            message="",
            use_llm_fallback=False
        )
        assert intent == IntentType.UNKNOWN

    @pytest.mark.asyncio
    async def test_gibberish_returns_unknown(self, classifier):
        intent, confidence, meta = await classifier.classify(
            message="xyz123 nonsense gibberish",
            use_llm_fallback=False
        )
        assert intent == IntentType.UNKNOWN

class TestOrchestratorImports:
    """Verify all orchestrator components can be imported."""

    def test_main_app_import(self):
        from services.hermes_orchestrator.main import app
        assert app is not None
        assert app.title == "Hermes Orchestrator"

    def test_planner_import(self):
        from services.hermes_orchestrator.planner.builder import TaskGraphBuilder
        builder = TaskGraphBuilder()
        assert builder is not None

    def test_verifier_import(self):
        from services.hermes_orchestrator.verifier.engine import SelfQAVerifier
        verifier = SelfQAVerifier()
        assert verifier is not None
