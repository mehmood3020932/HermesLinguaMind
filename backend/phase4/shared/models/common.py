"""
Hermes LinguaMind — Shared Models
All Pydantic + SQLAlchemy models, enums used across all 20+ services.
"""
from enum import Enum, auto
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from uuid import uuid4

from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# ─────────────────────────────────────────────────────────────
# ENUMS
# ─────────────────────────────────────────────────────────────

class IntentType(str, Enum):
    """User intent classification — used by Orchestrator (Phase 4)"""
    CONVERSATIONAL = "conversational"
    GRAMMAR_PRACTICE = "grammar_practice"
    SPEAKING_PRACTICE = "speaking_practice"
    LISTENING_PRACTICE = "listening_practice"
    VOCABULARY_PRACTICE = "vocabulary_practice"
    LESSON_COMPLETION = "lesson_completion"
    COIN_TRANSACTION = "coin_transaction"
    SOCIAL_INTERACTION = "social_interaction"
    PROFILE_UPDATE = "profile_update"
    UNKNOWN = "unknown"

class CEFRLevel(str, Enum):
    A1 = "A1"
    A2 = "A2"
    B1 = "B1"
    B2 = "B2"
    C1 = "C1"
    C2 = "C2"

class LanguageCode(str, Enum):
    EN = "en"
    ES = "es"
    FR = "fr"
    DE = "de"
    IT = "it"
    PT = "pt"
    JA = "ja"
    KO = "ko"
    ZH = "zh"
    HI = "hi"
    AR = "ar"
    RU = "ru"

class EmotionTag(str, Enum):
    NEUTRAL = "neutral"
    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"
    SURPRISED = "surprised"
    CONFUSED = "confused"
    EXCITED = "excited"
    ENCOURAGING = "encouraging"

class VisemeType(str, Enum):
    SILENCE = "silence"
    AE_AH = "ae_ah"
    AA = "aa"
    AO_OW = "ao_ow"
    EH_AY = "eh_ay"
    ER = "er"
    IH_IY = "ih_iy"
    UW_UH = "uw_uh"
    OY = "oy"
    AW = "aw"
    F_V = "f_v"
    TH_DH = "th_dh"
    S_Z = "s_z"
    SH_CH_JH_ZH = "sh_ch_jh_zh"
    P_B_M = "p_b_m"
    T_D_N = "t_d_n"
    K_G_NG = "k_g_ng"
    W = "w"
    R = "r"
    L = "l"
    Y = "y"
    HH = "hh"

class TransactionType(str, Enum):
    AWARD = "award"
    SPEND = "spend"
    REFUND = "refund"
    PENALTY = "penalty"

class LessonStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    LOCKED = "locked"

class ModerationAction(str, Enum):
    ALLOW = "allow"
    WARN = "warn"
    BLOCK = "block"
    REVIEW = "review"

class GestureType(str, Enum):
    WAVE = "wave"
    POINT = "point"
    THUMBS_UP = "thumbs_up"
    NOD = "nod"
    SHAKE = "shake"
    THINKING = "thinking"
    WELCOME = "welcome"
    ENCOURAGE = "encourage"

# ─────────────────────────────────────────────────────────────
# PYDANTIC MODELS
# ─────────────────────────────────────────────────────────────

class UserBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    native_language: LanguageCode = LanguageCode.EN
    target_language: LanguageCode = LanguageCode.EN
    cefr_level: CEFRLevel = CEFRLevel.A1

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserResponse(UserBase):
    id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    coins: int = 0
    streak_days: int = 0

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 3600

class IntentClassification(BaseModel):
    intent: IntentType
    confidence: float = Field(..., ge=0.0, le=1.0)
    raw_message: str
    language_detected: Optional[LanguageCode] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class TaskNode(BaseModel):
    """Single node in the orchestration task graph"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    service: str
    endpoint: str
    method: str = "POST"
    payload: Dict[str, Any] = Field(default_factory=dict)
    depends_on: List[str] = Field(default_factory=list)
    timeout_seconds: float = 30.0
    retries: int = 2
    fallback_action: str = "skip"  # skip | fail | mock

class TaskGraph(BaseModel):
    """Complete execution plan for an intent"""
    intent: IntentType
    request_id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    nodes: List[TaskNode]
    parallel_groups: List[List[str]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class AdapterResult(BaseModel):
    """Result from a single adapter call"""
    service: str
    endpoint: str
    success: bool
    data: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    latency_ms: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class VerificationResult(BaseModel):
    """Self-QA verification outcome"""
    check_type: str  # grammar_verify | coin_duplicate | drift_check | safety_check
    passed: bool
    details: Dict[str, Any] = Field(default_factory=dict)
    severity: str = "info"  # info | warning | critical
    retry_recommended: bool = False

class HermesResponse(BaseModel):
    """
    Unified response model returned by the Orchestrator to the mobile app.
    This is the SINGLE contract between backend and frontend.
    """
    model_config = ConfigDict(from_attributes=True)

    success: bool = True
    request_id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: Optional[str] = None

    # Core response content
    text: Optional[str] = None
    audio_url: Optional[str] = None
    viseme_timeline: Optional[List[Dict[str, Any]]] = None
    gesture: Optional[GestureType] = None
    emotion: Optional[EmotionTag] = EmotionTag.NEUTRAL

    # Gamification & progress
    coins_awarded: int = 0
    coins_total: Optional[int] = None
    streak_days: Optional[int] = None
    xp_gained: int = 0
    level_progress: Optional[float] = None

    # Learning content
    grammar_correction: Optional[Dict[str, Any]] = None
    pronunciation_score: Optional[float] = None
    vocabulary_items: Optional[List[Dict[str, Any]]] = None
    lesson_completed: Optional[str] = None

    # Social
    match_found: Optional[bool] = None
    match_profile: Optional[Dict[str, Any]] = None

    # Metadata
    intent: Optional[IntentType] = None
    confidence: Optional[float] = None
    latency_ms: float = 0.0
    verification_passed: bool = True
    fallback_used: bool = False

    # Error handling (friendly, never raw 500)
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    suggested_action: Optional[str] = None

    # Debug (stripped in production)
    debug: Optional[Dict[str, Any]] = Field(default_factory=dict)

class SessionContext(BaseModel):
    """Context passed with every orchestration request"""
    user_id: str
    session_id: Optional[str] = None
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list)
    current_lesson_id: Optional[str] = None
    current_module_id: Optional[str] = None
    preferred_voice: Optional[str] = None
    device_type: Optional[str] = None
    location: Optional[str] = None
    custom_params: Dict[str, Any] = Field(default_factory=dict)

class OrchestrateRequest(BaseModel):
    """Input to POST /v1/orchestrate"""
    user_id: str
    message: str
    session_context: Optional[SessionContext] = None
    audio_input: Optional[str] = None  # base64 encoded audio for speaking practice
    image_input: Optional[str] = None  # base64 encoded image

class CoinTransactionRequest(BaseModel):
    user_id: str
    amount: int
    transaction_type: TransactionType
    reason: str
    idempotency_key: str = Field(default_factory=lambda: str(uuid4()))
    metadata: Dict[str, Any] = Field(default_factory=dict)

class CoinTransactionResponse(BaseModel):
    transaction_id: str
    user_id: str
    amount: int
    balance: int
    transaction_type: TransactionType
    status: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class GrammarCheckRequest(BaseModel):
    text: str
    target_language: LanguageCode = LanguageCode.EN
    user_cefr: CEFRLevel = CEFRLevel.A1

class GrammarCheckResponse(BaseModel):
    original: str
    corrected: Optional[str] = None
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    explanations: List[str] = Field(default_factory=list)
    verified_by_rules: bool = False

class TTSRequest(BaseModel):
    text: str
    language: LanguageCode = LanguageCode.EN
    voice_id: Optional[str] = None
    speed: float = Field(default=1.0, ge=0.5, le=2.0)
    emotion: Optional[EmotionTag] = None

class TTSResponse(BaseModel):
    audio_url: str
    duration_seconds: float
    viseme_ready: bool = True
    engine_used: str

class STTRequest(BaseModel):
    audio_base64: str
    language: LanguageCode = LanguageCode.EN
    model: Optional[str] = None

class STTResponse(BaseModel):
    text: str
    confidence: float
    language_detected: LanguageCode
    word_timings: Optional[List[Dict[str, Any]]] = None

class PronunciationRequest(BaseModel):
    audio_base64: str
    expected_text: str
    language: LanguageCode = LanguageCode.EN
    user_cefr: CEFRLevel = CEFRLevel.A1

class PronunciationResponse(BaseModel):
    overall_score: float = Field(..., ge=0.0, le=100.0)
    word_scores: List[Dict[str, Any]] = Field(default_factory=list)
    phoneme_scores: List[Dict[str, Any]] = Field(default_factory=list)
    feedback: str
    tips: List[str] = Field(default_factory=list)

class VisemeRequest(BaseModel):
    text: str
    language: LanguageCode = LanguageCode.EN
    audio_duration_seconds: Optional[float] = None

class VisemeResponse(BaseModel):
    timeline: List[Dict[str, Any]]
    total_duration_ms: float
    viseme_count: int

class ModerationRequest(BaseModel):
    text: Optional[str] = None
    image_base64: Optional[str] = None
    user_id: str
    context: Optional[str] = None

class ModerationResponse(BaseModel):
    action: ModerationAction
    confidence: float
    categories: List[str] = Field(default_factory=list)
    reason: Optional[str] = None

class CurriculumRequest(BaseModel):
    user_id: str
    language: LanguageCode
    cefr_level: CEFRLevel
    module_id: Optional[str] = None

class CurriculumResponse(BaseModel):
    modules: List[Dict[str, Any]]
    current_module: Optional[Dict[str, Any]] = None
    progress_percent: float

class LessonCompleteRequest(BaseModel):
    user_id: str
    lesson_id: str
    module_id: str
    score: float = Field(..., ge=0.0, le=100.0)
    time_spent_seconds: int

class LessonCompleteResponse(BaseModel):
    success: bool
    xp_awarded: int
    coins_awarded: int
    next_lesson_unlocked: Optional[str] = None
    certificate_earned: Optional[str] = None

class PersonalizationRequest(BaseModel):
    user_id: str
    interaction_data: Dict[str, Any]
    analysis_type: str = "learning_style"  # learning_style | difficulty_adjust | content_recommend

class PersonalizationResponse(BaseModel):
    user_id: str
    learning_style: Optional[str] = None
    recommended_difficulty: Optional[CEFRLevel] = None
    recommended_content: List[Dict[str, Any]] = Field(default_factory=list)
    weak_areas: List[str] = Field(default_factory=list)
    strong_areas: List[str] = Field(default_factory=list)

class MemoryStoreRequest(BaseModel):
    user_id: str
    memory_type: str  # conversation | progress | preference | fact
    content: Dict[str, Any]
    ttl_seconds: Optional[int] = None

class MemoryRetrieveRequest(BaseModel):
    user_id: str
    memory_type: Optional[str] = None
    limit: int = 50
    since: Optional[datetime] = None

class GestureRequest(BaseModel):
    text: str
    emotion: Optional[EmotionTag] = None
    context: Optional[str] = None

class GestureResponse(BaseModel):
    gesture: GestureType
    intensity: float = Field(..., ge=0.0, le=1.0)
    duration_seconds: float = 1.5
    trigger_words: List[str] = Field(default_factory=list)

class LeaderboardRequest(BaseModel):
    period: str = "weekly"  # daily | weekly | monthly | all_time
    language: Optional[LanguageCode] = None
    limit: int = 100

class LeaderboardEntry(BaseModel):
    rank: int
    user_id: str
    username: str
    score: int
    avatar_url: Optional[str] = None

class SocialMatchRequest(BaseModel):
    user_id: str
    match_type: str = "conversation"  # conversation | study_buddy | language_exchange
    preferred_language: Optional[LanguageCode] = None
    cefr_level: Optional[CEFRLevel] = None

class SocialProfileRequest(BaseModel):
    user_id: str
    bio: Optional[str] = None
    interests: List[str] = Field(default_factory=list)
    learning_goals: List[str] = Field(default_factory=list)
    visibility: str = "public"  # public | friends | private

class AntiFraudCheckRequest(BaseModel):
    user_id: str
    action: str
    amount: Optional[int] = None
    ip_address: Optional[str] = None
    device_fingerprint: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class AntiFraudCheckResponse(BaseModel):
    risk_score: float = Field(..., ge=0.0, le=1.0)
    allowed: bool
    reason: Optional[str] = None
    action_required: Optional[str] = None

class LiveConversationStartRequest(BaseModel):
    user_id: str
    scenario: Optional[str] = None
    target_language: LanguageCode = LanguageCode.EN
    difficulty: CEFRLevel = CEFRLevel.A1
    duration_minutes: int = 10

class LiveConversationEndRequest(BaseModel):
    session_id: str
    user_id: str
    rating: Optional[int] = Field(default=None, ge=1, le=5)
    feedback: Optional[str] = None

class ContentGenerationRequest(BaseModel):
    content_type: str  # dialogue | story | exercise | quiz | explanation
    topic: str
    language: LanguageCode
    cefr_level: CEFRLevel
    count: int = 1
    constraints: Dict[str, Any] = Field(default_factory=dict)

class ContentGenerationResponse(BaseModel):
    items: List[Dict[str, Any]]
    content_type: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)

class GrammarRuleVerifyRequest(BaseModel):
    claim: str
    rule_reference: Optional[str] = None
    language: LanguageCode = LanguageCode.EN

class GrammarRuleVerifyResponse(BaseModel):
    claim: str
    verified: bool
    rule_found: bool
    rule_id: Optional[str] = None
    correction: Optional[str] = None
    explanation: Optional[str] = None
    confidence: float

class HealthResponse(BaseModel):
    status: str = "healthy"
    service: str
    version: str = "1.0.0"
    uptime_seconds: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    dependencies: Dict[str, str] = Field(default_factory=dict)

# ─────────────────────────────────────────────────────────────
# SQLALCHEMY MODELS (for PostgreSQL)
# ─────────────────────────────────────────────────────────────

class UserORM(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    username = Column(String(50), nullable=False, unique=True)
    email = Column(String(255), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    native_language = Column(String(10), default="en")
    target_language = Column(String(10), default="en")
    cefr_level = Column(String(5), default="A1")
    coins = Column(Integer, default=0)
    streak_days = Column(Integer, default=0)
    xp_total = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

class ConversationORM(Base):
    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String(36), nullable=False, index=True)
    session_id = Column(String(36), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # user | assistant | system
    content = Column(Text, nullable=False)
    intent = Column(String(50), default="unknown")
    emotion = Column(String(20), default="neutral")
    created_at = Column(DateTime, default=datetime.utcnow)
    metadata_json = Column(JSON, default=dict)

class CoinTransactionORM(Base):
    __tablename__ = "coin_transactions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String(36), nullable=False, index=True)
    amount = Column(Integer, nullable=False)
    transaction_type = Column(String(20), nullable=False)
    reason = Column(String(255), nullable=False)
    idempotency_key = Column(String(36), nullable=False, unique=True)
    status = Column(String(20), default="completed")
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

class LessonProgressORM(Base):
    __tablename__ = "lesson_progress"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String(36), nullable=False, index=True)
    lesson_id = Column(String(36), nullable=False)
    module_id = Column(String(36), nullable=False)
    status = Column(String(20), default="not_started")
    score = Column(Float, default=0.0)
    time_spent_seconds = Column(Integer, default=0)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AuditLogORM(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String(36), nullable=True, index=True)
    action = Column(String(100), nullable=False)
    service = Column(String(50), nullable=False)
    endpoint = Column(String(255), nullable=False)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    request_body = Column(Text, nullable=True)
    response_status = Column(Integer, nullable=True)
    latency_ms = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
