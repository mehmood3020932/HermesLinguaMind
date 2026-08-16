"""
Unit Tests: Self-QA Verification Engine
"""
import pytest
import sys
import os
from unittest.mock import AsyncMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from services.hermes_orchestrator.verifier.engine import SelfQAVerifier
from shared.models.common import (
    VerificationResult, IntentType, AdapterResult
)

class TestGrammarVerification:
    """Test grammar claim verification."""

    @pytest.fixture
    def verifier(self):
        mock_grammar = AsyncMock()
        mock_coin = AsyncMock()
        return SelfQAVerifier(grammar_adapter=mock_grammar, coin_ledger_adapter=mock_coin)

    @pytest.mark.asyncio
    async def test_no_grammar_claims_passes(self, verifier):
        results = await verifier.verify(
            intent=IntentType.CONVERSATIONAL,
            adapter_results={"llm": {"data": {"text": "Hello!"}}},
            user_id="user_1",
            request_id="req_1"
        )

        grammar_check = next(r for r in results if r.check_type == "grammar_verify")
        assert grammar_check.passed is True
        assert grammar_check.details["reason"] == "no_grammar_claims_found"

    @pytest.mark.asyncio
    async def test_grammar_verified_by_rules(self, verifier):
        verifier.grammar_adapter.verify = AsyncMock(return_value={
            "verified": True,
            "rule_id": "rule_123",
            "confidence": 0.95
        })

        results = await verifier.verify(
            intent=IntentType.GRAMMAR_PRACTICE,
            adapter_results={
                "llm": {
                    "data": {
                        "errors": [{"explanation": "Past tense of go is went", "language": "en"}]
                    }
                }
            },
            user_id="user_1",
            request_id="req_1"
        )

        grammar_check = next(r for r in results if r.check_type == "grammar_verify")
        assert grammar_check.passed is True
        assert grammar_check.details["verified"] == 1

class TestCoinDuplicateCheck:
    """Test coin double-award prevention."""

    @pytest.fixture
    def verifier(self):
        mock_grammar = AsyncMock()
        mock_coin = AsyncMock()
        return SelfQAVerifier(grammar_adapter=mock_grammar, coin_ledger_adapter=mock_coin)

    @pytest.mark.asyncio
    async def test_duplicate_request_id_blocked(self, verifier):
        from shared.utils.helpers import idempotency_store

        idempotency_store.mark_processed("req_dup_1", {"coins": 10})

        results = await verifier.verify(
            intent=IntentType.LESSON_COMPLETION,
            adapter_results={},
            user_id="user_1",
            request_id="req_dup_1"
        )

        coin_check = next(r for r in results if r.check_type == "coin_duplicate")
        assert coin_check.passed is False
        assert coin_check.severity == "critical"

        idempotency_store._processed.pop("req_dup_1", None)

    @pytest.mark.asyncio
    async def test_no_duplicate_allows_through(self, verifier):
        verifier.coin_ledger_adapter.get_transactions = AsyncMock(return_value={
            "transactions": []
        })

        results = await verifier.verify(
            intent=IntentType.LESSON_COMPLETION,
            adapter_results={},
            user_id="user_1",
            request_id="req_new_1"
        )

        coin_check = next(r for r in results if r.check_type == "coin_duplicate")
        assert coin_check.passed is True

class TestDriftCheck:
    """Test hallucination/drift detection."""

    @pytest.fixture
    def verifier(self):
        return SelfQAVerifier()

    @pytest.mark.asyncio
    async def test_empty_response_fails(self, verifier):
        results = await verifier.verify(
            intent=IntentType.CONVERSATIONAL,
            adapter_results={"llm": {"data": {"text": ""}}},
            user_id="user_1",
            request_id="req_1"
        )

        drift = next(r for r in results if r.check_type == "drift_check")
        assert drift.passed is False
        assert drift.retry_recommended is True

    @pytest.mark.asyncio
    async def test_character_break_detected(self, verifier):
        results = await verifier.verify(
            intent=IntentType.CONVERSATIONAL,
            adapter_results={
                "llm": {"data": {"text": "I am an AI language model created by OpenAI"}}
            },
            user_id="user_1",
            request_id="req_1"
        )

        drift = next(r for r in results if r.check_type == "drift_check")
        assert drift.passed is False

    @pytest.mark.asyncio
    async def test_normal_response_passes(self, verifier):
        results = await verifier.verify(
            intent=IntentType.CONVERSATIONAL,
            adapter_results={
                "llm": {"data": {"text": "Hello! How are you doing today? Let's practice some vocabulary!"}}
            },
            user_id="user_1",
            request_id="req_1"
        )

        drift = next(r for r in results if r.check_type == "drift_check")
        assert drift.passed is True

class TestSafetyCheck:
    """Test safety/moderation verification."""

    @pytest.fixture
    def verifier(self):
        return SelfQAVerifier()

    @pytest.mark.asyncio
    async def test_blocked_content_fails(self, verifier):
        results = await verifier.verify(
            intent=IntentType.CONVERSATIONAL,
            adapter_results={
                "moderation": {
                    "data": {"action": "block", "categories": ["hate_speech"]}
                }
            },
            user_id="user_1",
            request_id="req_1"
        )

        safety = next(r for r in results if r.check_type == "safety_check")
        assert safety.passed is False
        assert safety.severity == "critical"

    @pytest.mark.asyncio
    async def test_allowed_content_passes(self, verifier):
        results = await verifier.verify(
            intent=IntentType.CONVERSATIONAL,
            adapter_results={
                "moderation": {"data": {"action": "allow"}}
            },
            user_id="user_1",
            request_id="req_1"
        )

        safety = next(r for r in results if r.check_type == "safety_check")
        assert safety.passed is True

class TestVerifierUtilities:
    """Test helper methods on verifier."""

    def test_all_critical_passed(self):
        v = SelfQAVerifier()
        results = [
            VerificationResult(check_type="a", passed=True, severity="info"),
            VerificationResult(check_type="b", passed=True, severity="critical"),
        ]
        assert v.all_critical_passed(results) is True

    def test_critical_failure_detected(self):
        v = SelfQAVerifier()
        results = [
            VerificationResult(check_type="a", passed=True, severity="info"),
            VerificationResult(check_type="b", passed=False, severity="critical"),
        ]
        assert v.all_critical_passed(results) is False
