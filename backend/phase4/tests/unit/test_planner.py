"""
Unit Tests: Task Graph Builder
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from services.hermes_orchestrator.planner.builder import TaskGraphBuilder
from shared.models.common import IntentType, SessionContext

class TestTaskGraphBuilder:
    """Test task graph construction for all intents."""

    @pytest.fixture
    def builder(self):
        return TaskGraphBuilder()

    @pytest.fixture
    def session(self):
        return SessionContext(
            user_id="user_1",
            target_language="en",
            cefr_level="A1"
        )

    def test_conversational_graph_structure(self, builder, session):
        graph = builder.build(
            intent=IntentType.CONVERSATIONAL,
            user_id="user_1",
            message="Hello",
            session_context=session
        )

        assert graph.intent == IntentType.CONVERSATIONAL
        assert len(graph.nodes) == 5

        services = [n.service for n in graph.nodes]
        assert "moderation" in services
        assert "llm" in services
        assert "tts" in services
        assert "viseme" in services
        assert "gesture_emotion" in services

    def test_grammar_practice_graph(self, builder, session):
        graph = builder.build(
            intent=IntentType.GRAMMAR_PRACTICE,
            user_id="user_1",
            message="Check my grammar",
            session_context=session
        )

        services = [n.service for n in graph.nodes]
        assert "llm" in services
        assert "grammar_rule_db" in services
        assert "tts" in services

    def test_lesson_completion_includes_coin_ledger(self, builder, session):
        graph = builder.build(
            intent=IntentType.LESSON_COMPLETION,
            user_id="user_1",
            message="I finished the lesson",
            session_context=session
        )

        services = [n.service for n in graph.nodes]
        assert "curriculum" in services
        assert "anti_fraud" in services
        assert "coin_ledger" in services

        coin_nodes = [n for n in graph.nodes if n.service == "coin_ledger"]
        assert len(coin_nodes) >= 1

    def test_parallel_groups_detected(self, builder, session):
        graph = builder.build(
            intent=IntentType.CONVERSATIONAL,
            user_id="user_1",
            message="Hello",
            session_context=session
        )

        assert len(graph.parallel_groups) >= 2

    def test_all_intents_have_graphs(self, builder, session):
        """Every intent type must produce a valid task graph."""
        for intent in IntentType:
            graph = builder.build(
                intent=intent,
                user_id="user_1",
                message="test message",
                session_context=session
            )
            assert len(graph.nodes) > 0, f"Intent {intent.value} has no nodes"
            assert graph.request_id is not None

    def test_payload_placeholders_present(self, builder, session):
        graph = builder.build(
            intent=IntentType.CONVERSATIONAL,
            user_id="user_1",
            message="Hello",
            session_context=session
        )

        tts_node = next(n for n in graph.nodes if n.service == "tts")
        assert "{{" in str(tts_node.payload)
