"""
Hermes Orchestrator — Service Adapters
Thin async HTTP clients for all downstream microservices.
"""
from .base import BaseAdapter, ServiceAdapterError, ServiceUnavailable
from .llm_adapter import LLMAdapter
from .tts_adapter import TTSAdapter
from .stt_adapter import STTAdapter
from .viseme_adapter import VisemeAdapter
from .pronunciation_adapter import PronunciationAdapter
from .coin_ledger_adapter import CoinLedgerAdapter
from .curriculum_adapter import CurriculumAdapter
from .memory_adapter import MemoryAdapter
from .moderation_adapter import ModerationAdapter
from .grammar_rule_db_adapter import GrammarRuleDbAdapter
from .content_generation_adapter import ContentGenerationAdapter
from .personalization_adapter import PersonalizationAdapter
from .gesture_emotion_adapter import GestureEmotionAdapter
from .leaderboard_adapter import LeaderboardAdapter
from .social_exchange_adapter import SocialExchangeAdapter
from .anti_fraud_adapter import AntiFraudAdapter
from .live_conversation_adapter import LiveConversationAdapter
from .observability_adapter import ObservabilityAdapter
from .security_adapter import SecurityAdapter

__all__ = [
    "BaseAdapter", "ServiceAdapterError", "ServiceUnavailable",
    "LLMAdapter", "TTSAdapter", "STTAdapter", "VisemeAdapter",
    "PronunciationAdapter", "CoinLedgerAdapter", "CurriculumAdapter",
    "MemoryAdapter", "ModerationAdapter", "GrammarRuleDbAdapter",
    "ContentGenerationAdapter", "PersonalizationAdapter",
    "GestureEmotionAdapter", "LeaderboardAdapter",
    "SocialExchangeAdapter", "AntiFraudAdapter",
    "LiveConversationAdapter", "ObservabilityAdapter",
    "SecurityAdapter",
]
