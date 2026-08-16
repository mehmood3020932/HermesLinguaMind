"""
Unit Tests: Intent Classifier
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from services.hermes_orchestrator.intent.classifier import IntentClassifier
from shared.models.common import IntentType

@pytest.fixture
def classifier():
    return IntentClassifier(llm_service_url="http://localhost:8001")

class TestRuleBasedClassification:
    """Test rule-based intent classification without LLM calls."""

    @pytest.mark.asyncio
    async def test_conversational_greeting(self, classifier):
        intent, confidence, meta = await classifier.classify(
            "Hello, how are you today?",
            use_llm_fallback=False
        )
        assert intent == IntentType.CONVERSATIONAL
        assert confidence > 0

    @pytest.mark.asyncio
    async def test_grammar_practice(self, classifier):
        intent, confidence, meta = await classifier.classify(
            "Can you check my grammar? I think I made a mistake with tenses.",
            use_llm_fallback=False
        )
        assert intent == IntentType.GRAMMAR_PRACTICE
        assert confidence > 0

    @pytest.mark.asyncio
    async def test_vocabulary_practice(self, classifier):
        intent, confidence, meta = await classifier.classify(
            "What does 'serendipity' mean?",
            use_llm_fallback=False
        )
        assert intent == IntentType.VOCABULARY_PRACTICE
        assert confidence > 0

    @pytest.mark.asyncio
    async def test_speaking_practice(self, classifier):
        intent, confidence, meta = await classifier.classify(
            "I want to practice my pronunciation",
            use_llm_fallback=False
        )
        assert intent == IntentType.SPEAKING_PRACTICE
        assert confidence > 0

    @pytest.mark.asyncio
    async def test_listening_practice(self, classifier):
        intent, confidence, meta = await classifier.classify(
            "Can you play an audio for listening practice?",
            use_llm_fallback=False
        )
        assert intent == IntentType.LISTENING_PRACTICE
        assert confidence > 0

    @pytest.mark.asyncio
    async def test_lesson_completion(self, classifier):
        intent, confidence, meta = await classifier.classify(
            "I finished the lesson!",
            use_llm_fallback=False
        )
        assert intent == IntentType.LESSON_COMPLETION
        assert confidence > 0

    @pytest.mark.asyncio
    async def test_coin_transaction(self, classifier):
        intent, confidence, meta = await classifier.classify(
            "How many coins do I have?",
            use_llm_fallback=False
        )
        assert intent == IntentType.COIN_TRANSACTION
        assert confidence > 0

    @pytest.mark.asyncio
    async def test_social_interaction(self, classifier):
        intent, confidence, meta = await classifier.classify(
            "Find me a language partner",
            use_llm_fallback=False
        )
        assert intent == IntentType.SOCIAL_INTERACTION
        assert confidence > 0

    @pytest.mark.asyncio
    async def test_profile_update(self, classifier):
        intent, confidence, meta = await classifier.classify(
            "Update my learning goals",
            use_llm_fallback=False
        )
        assert intent == IntentType.PROFILE_UPDATE
        assert confidence > 0

    @pytest.mark.asyncio
    async def test_unknown_ambiguous(self, classifier):
        intent, confidence, meta = await classifier.classify(
            "xyz123 nonsense",
            use_llm_fallback=False
        )
        assert intent == IntentType.UNKNOWN
        assert confidence < 0.5

class TestConfidenceScoring:
    """Test confidence score calculations."""

    @pytest.mark.asyncio
    async def test_multiple_keywords_boost_confidence(self, classifier):
        _, confidence1, _ = await classifier.classify(
            "grammar", use_llm_fallback=False
        )
        _, confidence2, _ = await classifier.classify(
            "grammar check my mistakes with tenses", use_llm_fallback=False
        )
        assert confidence2 > confidence1

    @pytest.mark.asyncio
    async def test_confidence_bounded(self, classifier):
        _, confidence, _ = await classifier.classify(
            "grammar check fix my sentence structure error tense conjugation",
            use_llm_fallback=False
        )
        assert 0 <= confidence <= 1.0
