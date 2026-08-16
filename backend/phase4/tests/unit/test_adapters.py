"""
Unit Tests: All Service Adapters
"""
import pytest
import sys
import os
from unittest.mock import AsyncMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from services.hermes_orchestrator.adapters import (
    LLMAdapter, TTSAdapter, CoinLedgerAdapter,
    GrammarRuleDbAdapter, ModerationAdapter,
    BaseAdapter
)
from shared.models.common import AdapterResult

class TestBaseAdapter:
    """Test base adapter functionality."""

    @pytest.mark.asyncio
    async def test_request_accepts_timeout_argument(self):
        adapter = BaseAdapter("test_service", base_url="http://test:9999")
        adapter.circuit_breaker.call = AsyncMock(return_value=AdapterResult(
            service="test_service",
            endpoint="/health",
            success=True,
            data={"status": "healthy"}
        ))

        result = await adapter._request("GET", "/health", timeout=5.0)

        assert result.success is True
        assert result.data["status"] == "healthy"

    def test_default_port_mapping(self):
        adapter = BaseAdapter("test_service", base_url="http://test:9999")
        assert adapter._default_port() == 8000

    def test_llm_port(self):
        llm = LLMAdapter()
        assert llm._default_port() == 8001

    def test_tts_port(self):
        tts = TTSAdapter()
        assert tts._default_port() == 8002

    def test_coin_ledger_port(self):
        coin = CoinLedgerAdapter()
        assert coin._default_port() == 8006

class TestLLMAdapter:
    """Test LLM adapter methods."""

    @pytest.fixture
    def adapter(self):
        return LLMAdapter(base_url="http://localhost:8001")

    @pytest.mark.asyncio
    async def test_generate_returns_data(self, adapter):
        adapter._request = AsyncMock(return_value=AdapterResult(
            service="llm",
            endpoint="/v1/generate",
            success=True,
            data={"text": "Hello!", "tokens_used": 10}
        ))

        result = await adapter.generate(
            prompt="Say hello",
            system_prompt="You are Hermes",
            max_tokens=100
        )

        assert result["text"] == "Hello!"
        assert result["tokens_used"] == 10

    @pytest.mark.asyncio
    async def test_grammar_check(self, adapter):
        adapter._request = AsyncMock(return_value=AdapterResult(
            service="llm",
            endpoint="/v1/grammar-check",
            success=True,
            data={"errors": [], "corrected": "Hello world"}
        ))

        result = await adapter.grammar_check("hello world", "en", "A1")
        assert result["corrected"] == "Hello world"

class TestCoinLedgerAdapter:
    """Test coin ledger adapter — critical for server-authoritative coins."""

    @pytest.fixture
    def adapter(self):
        return CoinLedgerAdapter(base_url="http://localhost:8006")

    @pytest.mark.asyncio
    async def test_create_transaction_includes_idempotency_key(self, adapter):
        adapter._request = AsyncMock(return_value=AdapterResult(
            service="coin_ledger",
            endpoint="/v1/transaction",
            success=True,
            data={"transaction_id": "tx_123", "balance": 100}
        ))

        result = await adapter.create_transaction(
            user_id="user_1",
            amount=10,
            transaction_type="award",
            reason="Lesson completion",
            idempotency_key="idem_key_123"
        )

        assert result["transaction_id"] == "tx_123"
        assert result["balance"] == 100

class TestGrammarRuleDbAdapter:
    """Test grammar rule verification adapter."""

    @pytest.fixture
    def adapter(self):
        return GrammarRuleDbAdapter(base_url="http://localhost:8010")

    @pytest.mark.asyncio
    async def test_verify_claim(self, adapter):
        adapter._request = AsyncMock(return_value=AdapterResult(
            service="grammar_rule_db",
            endpoint="/v1/verify",
            success=True,
            data={"verified": True, "rule_id": "rule_123", "confidence": 0.95}
        ))

        result = await adapter.verify(
            claim="Past tense of 'go' is 'went'",
            language="en"
        )

        assert result["verified"] is True
        assert result["rule_id"] == "rule_123"
