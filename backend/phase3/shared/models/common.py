"""
Hermes LinguaMind — Shared Models (Common)
Cumulative: Phase 1 + Phase 2 + Phase 3
All enums, base models, and shared data structures.
"""

from enum import Enum, IntEnum
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, date
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, ConfigDict, field_validator
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Date, JSON, Text, ForeignKey, Enum as SQLEnum, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID, ARRAY
from sqlalchemy.orm import declarative_base, relationship

# ============================================================
# SQLAlchemy Base
# ============================================================
Base = declarative_base()

# ============================================================
# ENUMS
# ============================================================

class UserRole(str, Enum):
    """User role enumeration."""
    LEARNER = "learner"
    NATIVE_SPEAKER = "native_speaker"
    MODERATOR = "moderator"
    ADMIN = "admin"

class CEFRLevel(str, Enum):
    """CEFR proficiency levels."""
    A1 = "A1"
    A2 = "A2"
    B1 = "B1"
    B2 = "B2"
    C1 = "C1"
    C2 = "C2"

class LanguageCode(str, Enum):
    """Supported language codes."""
    EN = "en"
    ES = "es"
    FR = "fr"
    DE = "de"
    IT = "it"
    PT = "pt"
    JA = "ja"
    KO = "ko"
    ZH = "zh"
    AR = "ar"
    HI = "hi"
    RU = "ru"
    TR = "tr"
    PL = "pl"
    NL = "nl"
    SV = "sv"
    DA = "da"
    NO = "no"
    FI = "fi"
    # --- Expanded to 100+ languages so the AI companion can teach in (and
    # explain via) the learner's own native tongue, not just a handful of
    # major European languages. ---
    UK = "uk"   # Ukrainian
    CS = "cs"   # Czech
    SK = "sk"   # Slovak
    HU = "hu"   # Hungarian
    RO = "ro"   # Romanian
    BG = "bg"   # Bulgarian
    EL = "el"   # Greek
    HE = "he"   # Hebrew
    TH = "th"   # Thai
    VI = "vi"   # Vietnamese
    ID = "id"   # Indonesian
    MS = "ms"   # Malay
    TL = "tl"   # Filipino/Tagalog
    BN = "bn"   # Bengali
    UR = "ur"   # Urdu
    FA = "fa"   # Persian/Farsi
    PA = "pa"   # Punjabi
    TA = "ta"   # Tamil
    TE = "te"   # Telugu
    MR = "mr"   # Marathi
    GU = "gu"   # Gujarati
    KN = "kn"   # Kannada
    ML = "ml"   # Malayalam
    SI = "si"   # Sinhala
    NE = "ne"   # Nepali
    MY = "my"   # Burmese
    KM = "km"   # Khmer
    LO = "lo"   # Lao
    MN = "mn"   # Mongolian
    KA = "ka"   # Georgian
    HY = "hy"   # Armenian
    AZ = "az"   # Azerbaijani
    KK = "kk"   # Kazakh
    UZ = "uz"   # Uzbek
    TG = "tg"   # Tajik
    KY = "ky"   # Kyrgyz
    TK = "tk"   # Turkmen
    PS = "ps"   # Pashto
    SD = "sd"   # Sindhi
    AM = "am"   # Amharic
    SW = "sw"   # Swahili
    ZU = "zu"   # Zulu
    XH = "xh"   # Xhosa
    AF = "af"   # Afrikaans
    YO = "yo"   # Yoruba
    IG = "ig"   # Igbo
    HA = "ha"   # Hausa
    SO = "so"   # Somali
    RW = "rw"   # Kinyarwanda
    ST = "st"   # Sesotho
    SN = "sn"   # Shona
    MG = "mg"   # Malagasy
    LT = "lt"   # Lithuanian
    LV = "lv"   # Latvian
    ET = "et"   # Estonian
    SL = "sl"   # Slovenian
    HR = "hr"   # Croatian
    SR = "sr"   # Serbian
    BS = "bs"   # Bosnian
    MK = "mk"   # Macedonian
    SQ = "sq"   # Albanian
    IS = "is"   # Icelandic
    GA = "ga"   # Irish
    CY = "cy"   # Welsh
    GD = "gd"   # Scottish Gaelic
    MT = "mt"   # Maltese
    EU = "eu"   # Basque
    CA = "ca"   # Catalan
    GL = "gl"   # Galician
    LB = "lb"   # Luxembourgish
    FO = "fo"   # Faroese
    BR = "br"   # Breton
    EO = "eo"   # Esperanto
    LA = "la"   # Latin
    SA = "sa"   # Sanskrit
    YI = "yi"   # Yiddish
    KU = "ku"   # Kurdish
    UG = "ug"   # Uyghur
    BO = "bo"   # Tibetan
    DV = "dv"   # Dhivehi/Maldivian
    JV = "jv"   # Javanese
    SU = "su"   # Sundanese

class IntentType(str, Enum):
    """Intent classification types."""
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

class TTSEngine(str, Enum):
    """TTS engine options."""
    PIPER = "piper"
    COQUI = "coqui"
    MMS = "mms"

class EmotionTag(str, Enum):
    """Emotion tags for TTS and gestures."""
    NEUTRAL = "neutral"
    HAPPY = "happy"
    SAD = "sad"
    EXCITED = "excited"
    CALM = "calm"
    ENCOURAGING = "encouraging"
    CORRECTIVE = "corrective"
    CELEBRATORY = "celebratory"

class VisemeType(str, Enum):
    """Viseme types for lip-sync."""
    SILENCE = "sil"
    AA = "aa"  # as in "bat"
    AH = "ah"  # as in "father"
    AO = "ao"  # as in "caught"
    AW = "aw"  # as in "bought"
    AY = "ay"  # as in "bite"
    B = "b"    # as in "bat"
    CH = "ch"  # as in "church"
    D = "d"    # as in "dog"
    DH = "dh"  # as in "this"
    EH = "eh"  # as in "bet"
    ER = "er"  # as in "bird"
    EY = "ey"  # as in "bait"
    F = "f"    # as in "fat"
    G = "g"    # as in "got"
    HH = "hh"  # as in "hat"
    IH = "ih"  # as in "bit"
    IY = "iy"  # as in "beat"
    JH = "jh"  # as in "judge"
    K = "k"    # as in "cat"
    L = "l"    # as in "let"
    M = "m"    # as in "met"
    N = "n"    # as in "net"
    NG = "ng"  # as in "sing"
    OW = "ow"  # as in "boat"
    OY = "oy"  # as in "boy"
    P = "p"    # as in "pat"
    R = "r"    # as in "rat"
    S = "s"    # as in "sat"
    SH = "sh"  # as in "shut"
    T = "t"    # as in "tat"
    TH = "th"  # as in "thin"
    UH = "uh"  # as in "but"
    UW = "uw"  # as in "boot"
    V = "v"    # as in "vat"
    W = "w"    # as in "wet"
    Y = "y"    # as in "yet"
    Z = "z"    # as in "zap"
    ZH = "zh"  # as in "measure"

class CoinTransactionType(str, Enum):
    """Types of coin transactions."""
    LESSON_COMPLETION = "lesson_completion"
    STREAK_BONUS = "streak_bonus"
    PERFECT_PRONUNCIATION = "perfect_pronunciation"
    GRAMMAR_CORRECTION = "grammar_correction"
    DAILY_LOGIN = "daily_login"
    REFERRAL = "referral"
    PURCHASE = "purchase"
    SPEND = "spend"
    REFUND = "refund"
    FRAUD_REVERSAL = "fraud_reversal"

class ContentTier(str, Enum):
    """Content quality tiers."""
    TIER1_REVIEWED = "tier1_reviewed"
    TIER2_AI_ONLY = "tier2_ai_only"
    TIER3_EXPERIMENTAL = "tier3_experimental"

class GestureType(str, Enum):
    """Character gesture types."""
    IDLE = "idle"
    WAVE = "wave"
    POINT = "point"
    THINK = "think"
    CELEBRATE = "celebrate"
    ENCOURAGE = "encourage"
    CORRECT = "correct"
    LISTEN = "listen"
    SPEAK = "speak"
    NOD = "nod"
    SHAKE_HEAD = "shake_head"
    RAISE_EYEBROW = "raise_eyebrow"
    SMILE = "smile"
    SURPRISED = "surprised"

class LeaderboardScope(str, Enum):
    """Leaderboard scopes."""
    FRIENDS = "friends"
    COUNTRY = "country"
    GLOBAL = "global"
    LANGUAGE_PAIR = "language_pair"

class SocialStatus(str, Enum):
    """Social exchange status."""
    PENDING = "pending"
    ACTIVE = "active"
    BLOCKED = "blocked"
    REPORTED = "reported"
    EXPIRED = "expired"

class FraudRiskLevel(str, Enum):
    """Fraud risk levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ConversationMode(str, Enum):
    """Live conversation modes."""
    TEXT = "text"
    VOICE = "voice"
    VIDEO = "video"

class BackupStatus(str, Enum):
    """Backup operation status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

# ============================================================
# PYDANTIC BASE MODELS
# ============================================================

class HermesResponse(BaseModel):
    """Standard API response wrapper."""
    model_config = ConfigDict(populate_by_name=True)

    success: bool = True
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    request_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class PaginatedResponse(BaseModel):
    """Paginated response wrapper."""
    model_config = ConfigDict(populate_by_name=True)

    items: List[Dict[str, Any]]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool

class HealthStatus(BaseModel):
    """Health check response."""
    model_config = ConfigDict(populate_by_name=True)

    status: str = "healthy"
    service: str
    version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    uptime_seconds: float
    dependencies: Dict[str, str] = Field(default_factory=dict)

# ============================================================
# SQLALCHEMY ORM MODELS
# ============================================================

class UserORM(Base):
    """User database model."""
    __tablename__ = "users"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    display_name = Column(String(100))
    role = Column(SQLEnum(UserRole), default=UserRole.LEARNER)
    native_language = Column(SQLEnum(LanguageCode), default=LanguageCode.EN)
    learning_language = Column(SQLEnum(LanguageCode), default=LanguageCode.ES)
    cefr_level = Column(SQLEnum(CEFRLevel), default=CEFRLevel.A1)
    date_of_birth = Column(Date)
    country_code = Column(String(2))
    avatar_url = Column(String(500))
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)

    # Relationships
    coin_balance = relationship("CoinBalanceORM", back_populates="user", uselist=False)
    transactions = relationship("CoinTransactionORM", back_populates="user")
    curriculum_progress = relationship("CurriculumProgressORM", back_populates="user")
    memories = relationship("MemoryORM", back_populates="user")
    social_profiles = relationship("SocialProfileORM", back_populates="user")

    __table_args__ = (
        Index("idx_user_email_active", "email", "is_active"),
        Index("idx_user_country", "country_code"),
    )

class CoinBalanceORM(Base):
    """Coin balance database model."""
    __tablename__ = "coin_balances"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    balance = Column(Integer, default=0, nullable=False)
    lifetime_earned = Column(Integer, default=0)
    lifetime_spent = Column(Integer, default=0)
    daily_earned_today = Column(Integer, default=0)
    last_daily_reset = Column(Date, default=date.today)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("UserORM", back_populates="coin_balance")

    __table_args__ = (
        Index("idx_coin_balance_user", "user_id"),
    )

class CoinTransactionORM(Base):
    """Coin transaction database model (append-only ledger)."""
    __tablename__ = "coin_transactions"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    transaction_type = Column(SQLEnum(CoinTransactionType), nullable=False)
    amount = Column(Integer, nullable=False)
    balance_after = Column(Integer, nullable=False)
    idempotency_key = Column(String(64), unique=True, nullable=False, index=True)
    description = Column(Text)
    metadata_payload = Column(JSON, default=dict)
    fraud_risk_level = Column(SQLEnum(FraudRiskLevel), default=FraudRiskLevel.LOW)
    fraud_review_status = Column(String(20), default="none")
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("UserORM", back_populates="transactions")

    __table_args__ = (
        Index("idx_tx_user_created", "user_id", "created_at"),
        Index("idx_tx_type", "transaction_type"),
        Index("idx_tx_fraud", "fraud_risk_level"),
    )

class CurriculumProgressORM(Base):
    """Curriculum progress database model."""
    __tablename__ = "curriculum_progress"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    lesson_id = Column(String(100), nullable=False)
    module_id = Column(String(100), nullable=False)
    language_pair = Column(String(10), nullable=False)
    status = Column(String(20), default="in_progress")
    score = Column(Float, default=0.0)
    attempts = Column(Integer, default=0)
    time_spent_seconds = Column(Integer, default=0)
    last_reviewed = Column(DateTime)
    next_review = Column(DateTime)
    sm2_interval = Column(Integer, default=1)
    sm2_ease_factor = Column(Float, default=2.5)
    sm2_repetitions = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("UserORM", back_populates="curriculum_progress")

    __table_args__ = (
        Index("idx_curriculum_user", "user_id"),
        Index("idx_curriculum_next_review", "next_review"),
        UniqueConstraint("user_id", "lesson_id", name="uq_user_lesson"),
    )

class MemoryORM(Base):
    """Conversation memory database model."""
    __tablename__ = "memories"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    memory_type = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    importance_score = Column(Float, default=0.5)
    context_tags = Column(ARRAY(String), default=list)
    summary = Column(Text)
    is_archived = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("UserORM", back_populates="memories")

    __table_args__ = (
        Index("idx_memory_user", "user_id"),
        Index("idx_memory_type", "memory_type"),
    )

class GrammarRuleORM(Base):
    """Grammar rule database model."""
    __tablename__ = "grammar_rules"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    rule_id = Column(String(100), unique=True, nullable=False)
    language_pair = Column(String(10), nullable=False, index=True)
    rule_name = Column(String(200), nullable=False)
    rule_description = Column(Text, nullable=False)
    examples = Column(JSON, default=list)
    exceptions = Column(JSON, default=list)
    cefr_level = Column(SQLEnum(CEFRLevel))
    category = Column(String(100))
    tags = Column(ARRAY(String), default=list)
    verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_grammar_pair_level", "language_pair", "cefr_level"),
        Index("idx_grammar_category", "category"),
    )

class ContentItemORM(Base):
    """Generated content database model."""
    __tablename__ = "content_items"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    content_type = Column(String(50), nullable=False)
    language_pair = Column(String(10), nullable=False)
    cefr_level = Column(SQLEnum(CEFRLevel), nullable=False)
    tier = Column(SQLEnum(ContentTier), default=ContentTier.TIER2_AI_ONLY)
    title = Column(String(300), nullable=False)
    body = Column(Text, nullable=False)
    metadata_payload = Column(JSON, default=dict)
    generated_by = Column(String(100))
    reviewed_by = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    review_status = Column(String(20), default="pending")
    usage_count = Column(Integer, default=0)
    avg_rating = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_content_pair_level", "language_pair", "cefr_level"),
        Index("idx_content_tier", "tier"),
    )

class SocialProfileORM(Base):
    """Social profile database model."""
    __tablename__ = "social_profiles"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    bio = Column(Text)
    interests = Column(ARRAY(String), default=list)
    available_for_exchange = Column(Boolean, default=False)
    preferred_times = Column(JSON, default=list)
    exchange_count = Column(Integer, default=0)
    rating = Column(Float, default=0.0)
    report_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("UserORM", back_populates="social_profiles")

    __table_args__ = (
        Index("idx_social_available", "available_for_exchange"),
    )

class LeaderboardEntryORM(Base):
    """Leaderboard entry database model."""
    __tablename__ = "leaderboard_entries"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    scope = Column(SQLEnum(LeaderboardScope), nullable=False)
    period = Column(String(20), nullable=False)  # weekly, monthly, all_time
    score = Column(Integer, default=0)
    rank = Column(Integer)
    language_pair = Column(String(10))
    country_code = Column(String(2))
    week_start = Column(Date)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_leaderboard_scope_period", "scope", "period", "week_start"),
        Index("idx_leaderboard_rank", "scope", "period", "rank"),
        UniqueConstraint("user_id", "scope", "period", "week_start", "language_pair", name="uq_leaderboard_entry"),
    )

class FraudAlertORM(Base):
    """Fraud alert database model."""
    __tablename__ = "fraud_alerts"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    alert_type = Column(String(100), nullable=False)
    risk_level = Column(SQLEnum(FraudRiskLevel), nullable=False)
    details = Column(JSON, default=dict)
    triggered_rules = Column(ARRAY(String), default=list)
    reviewed_by = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    review_status = Column(String(20), default="pending")
    action_taken = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime)

    __table_args__ = (
        Index("idx_fraud_user", "user_id"),
        Index("idx_fraud_risk", "risk_level", "review_status"),
    )

class BackupLogORM(Base):
    """Backup operation log database model."""
    __tablename__ = "backup_logs"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    backup_type = Column(String(50), nullable=False)
    status = Column(SQLEnum(BackupStatus), default=BackupStatus.PENDING)
    s3_key = Column(String(500))
    file_size_bytes = Column(Integer)
    checksum = Column(String(64))
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    error_message = Column(Text)
    metadata_payload = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_backup_status", "status"),
        Index("idx_backup_type", "backup_type", "created_at"),
    )

class AuditLogORM(Base):
    """Security audit log database model."""
    __tablename__ = "audit_logs"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(100), nullable=False)
    resource_id = Column(String(100))
    ip_address = Column(String(45))
    user_agent = Column(Text)
    request_id = Column(String(36))
    details = Column(JSON, default=dict)
    severity = Column(String(20), default="info")
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_audit_user", "user_id", "created_at"),
        Index("idx_audit_action", "action", "created_at"),
        Index("idx_audit_severity", "severity"),
    )

# ============================================================
# REQUEST/RESPONSE MODELS
# ============================================================

class AvatarCharacterORM(Base):
    """A teachable avatar persona: DB-driven personality/voice/teaching-style,
    mapped to a concrete OpenTalking (github.com/datascale-ai/opentalking)
    avatar_id + model. Seeded by scripts/seed_avatar_characters.py."""
    __tablename__ = "avatar_characters"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    slug = Column(String(64), unique=True, nullable=False, index=True)
    display_name = Column(String(100), nullable=False)
    personality_prompt = Column(Text, nullable=False)  # system prompt / persona
    teaching_style = Column(String(50), default="conversational")
    opentalking_avatar_id = Column(String(100), nullable=False)  # asset id in OpenTalking's avatar library
    opentalking_model = Column(String(50), default="mock")  # mock | quicktalk | wav2lip | ...
    voice_id = Column(String(100))  # OpenTalking/edge-tts voice name
    emotion_profile = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_avatar_character_active", "is_active"),
    )


class AvatarSessionORM(Base):
    """Server-tracked mapping between a Hermes user and a live OpenTalking
    session. We never let the client dictate what character/session it can
    address — every message is re-validated against this row first."""
    __tablename__ = "avatar_sessions"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    character_id = Column(PGUUID(as_uuid=True), ForeignKey("avatar_characters.id"), nullable=False)
    opentalking_session_id = Column(String(100), nullable=False, index=True)
    status = Column(String(20), default="active")  # active | ended | error
    created_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime)

    __table_args__ = (
        Index("idx_avatar_session_user_status", "user_id", "status"),
    )


class UserCreateRequest(BaseModel):
    """User creation request."""
    model_config = ConfigDict(populate_by_name=True)

    email: str
    username: str
    password: str
    display_name: Optional[str] = None
    native_language: LanguageCode = LanguageCode.EN
    learning_language: LanguageCode = LanguageCode.ES
    date_of_birth: Optional[date] = None
    country_code: Optional[str] = None

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v

class UserLoginRequest(BaseModel):
    """User login request."""
    model_config = ConfigDict(populate_by_name=True)

    username: str
    password: str

class TokenResponse(BaseModel):
    """JWT token response."""
    model_config = ConfigDict(populate_by_name=True)

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class LLMRequest(BaseModel):
    """LLM orchestration request."""
    model_config = ConfigDict(populate_by_name=True)

    prompt: str
    system_prompt: Optional[str] = None
    model: Optional[str] = None
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=1024, ge=1, le=4096)
    language: LanguageCode = LanguageCode.EN
    stream: bool = False

class LLMResponse(BaseModel):
    """LLM orchestration response."""
    # protected_namespaces=() — `model_used` isn't Pydantic's reserved
    # `model_*` config machinery, it's our own field name (which provider
    # served the request); this only silences a warning, not a real
    # collision, and renaming it would break the JSON contract every
    # client already expects.
    model_config = ConfigDict(populate_by_name=True, protected_namespaces=())

    text: str
    model_used: str
    provider: str
    tokens_used: Optional[int] = None
    latency_ms: float
    cached: bool = False

class TTSRequest(BaseModel):
    """Text-to-speech request."""
    model_config = ConfigDict(populate_by_name=True)

    text: str
    language: LanguageCode = LanguageCode.EN
    engine: TTSEngine = TTSEngine.PIPER
    emotion: EmotionTag = EmotionTag.NEUTRAL
    speed: float = Field(default=1.0, ge=0.5, le=2.0)
    speaker_id: Optional[int] = None

class TTSResponse(BaseModel):
    """Text-to-speech response."""
    model_config = ConfigDict(populate_by_name=True)

    audio_base64: str
    format: str = "wav"
    sample_rate: int = 22050
    duration_seconds: float
    phoneme_timings: List[Dict[str, Any]]
    engine_used: str

class STTRequest(BaseModel):
    """Speech-to-text request."""
    model_config = ConfigDict(populate_by_name=True)

    audio_base64: str
    language: LanguageCode = LanguageCode.EN
    format: str = "wav"
    sample_rate: int = 16000

class STTResponse(BaseModel):
    """Speech-to-text response."""
    model_config = ConfigDict(populate_by_name=True)

    text: str
    confidence: float
    language_detected: str
    segments: List[Dict[str, Any]]
    processing_time_ms: float

class VisemeRequest(BaseModel):
    """Viseme generation request."""
    model_config = ConfigDict(populate_by_name=True)

    phoneme_timings: List[Dict[str, Any]]
    language: LanguageCode = LanguageCode.EN
    fps: int = Field(default=30, ge=15, le=60)

class VisemeResponse(BaseModel):
    """Viseme generation response."""
    model_config = ConfigDict(populate_by_name=True)

    viseme_timeline: List[Dict[str, Any]]
    total_duration_ms: float
    frame_count: int
    fps: int

class PronunciationRequest(BaseModel):
    """Pronunciation scoring request."""
    model_config = ConfigDict(populate_by_name=True)

    audio_base64: str
    expected_text: str
    language: LanguageCode = LanguageCode.EN
    native_language: Optional[LanguageCode] = None

class PronunciationResponse(BaseModel):
    """Pronunciation scoring response."""
    model_config = ConfigDict(populate_by_name=True)

    overall_score: float = Field(..., ge=0.0, le=100.0)
    phoneme_scores: List[Dict[str, Any]]
    word_scores: List[Dict[str, Any]]
    feedback: str
    feedback_native_language: Optional[str] = None
    confidence: float

class CoinTransactionRequest(BaseModel):
    """Coin transaction request."""
    model_config = ConfigDict(populate_by_name=True)

    user_id: UUID
    transaction_type: CoinTransactionType
    amount: int
    idempotency_key: str
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class CoinBalanceResponse(BaseModel):
    """Coin balance response."""
    model_config = ConfigDict(populate_by_name=True)

    user_id: UUID
    balance: int
    lifetime_earned: int
    lifetime_spent: int
    daily_earned_today: int
    daily_limit: int

class CurriculumRequest(BaseModel):
    """Curriculum request."""
    model_config = ConfigDict(populate_by_name=True)

    user_id: UUID
    language_pair: str
    cefr_level: Optional[CEFRLevel] = None
    lesson_count: int = Field(default=5, ge=1, le=20)

class CurriculumResponse(BaseModel):
    """Curriculum response."""
    model_config = ConfigDict(populate_by_name=True)

    lessons: List[Dict[str, Any]]
    adaptive_difficulty: float
    recommended_focus_areas: List[str]
    streak_days: int
    total_lessons_completed: int

class MemoryRequest(BaseModel):
    """Memory store request."""
    model_config = ConfigDict(populate_by_name=True)

    user_id: UUID
    memory_type: str
    content: str
    importance_score: float = Field(default=0.5, ge=0.0, le=1.0)
    context_tags: Optional[List[str]] = None

class MemoryResponse(BaseModel):
    """Memory response."""
    model_config = ConfigDict(populate_by_name=True)

    memories: List[Dict[str, Any]]
    summary: str
    relationship_depth: int

class ModerationRequest(BaseModel):
    """Content moderation request."""
    model_config = ConfigDict(populate_by_name=True)

    content: str
    content_type: str = "text"
    user_id: Optional[UUID] = None
    context: Optional[str] = None

class ModerationResponse(BaseModel):
    """Content moderation response."""
    model_config = ConfigDict(populate_by_name=True)

    is_safe: bool
    flags: List[str] = Field(default_factory=list)
    confidence: float
    action: str = "allow"
    reason: Optional[str] = None

class GrammarVerifyRequest(BaseModel):
    """Grammar verification request."""
    model_config = ConfigDict(populate_by_name=True)

    text: str
    language_pair: str
    cefr_level: Optional[CEFRLevel] = None

class GrammarVerifyResponse(BaseModel):
    """Grammar verification response."""
    model_config = ConfigDict(populate_by_name=True)

    is_grammatically_correct: bool
    errors: List[Dict[str, Any]]
    suggested_rules: List[str]
    confidence: float

class ContentGenerationRequest(BaseModel):
    """Content generation request."""
    model_config = ConfigDict(populate_by_name=True)

    content_type: str
    language_pair: str
    cefr_level: CEFRLevel
    count: int = Field(default=1, ge=1, le=100)
    tier: ContentTier = ContentTier.TIER2_AI_ONLY
    topics: Optional[List[str]] = None

class PersonalizationRequest(BaseModel):
    """Personalization signal request."""
    model_config = ConfigDict(populate_by_name=True)

    user_id: UUID
    interaction_history: Optional[List[Dict[str, Any]]] = None
    learning_sessions: Optional[List[Dict[str, Any]]] = None

class PersonalizationResponse(BaseModel):
    """Personalization response."""
    model_config = ConfigDict(populate_by_name=True)

    learning_style: str
    interest_tags: List[str]
    difficulty_preference: float
    recommended_pace: str
    engagement_patterns: Dict[str, Any]

class GestureRequest(BaseModel):
    """Gesture/emotion cue request."""
    model_config = ConfigDict(populate_by_name=True)

    text: str
    context: str
    current_emotion: EmotionTag = EmotionTag.NEUTRAL
    conversation_history: Optional[List[str]] = None

class GestureResponse(BaseModel):
    """Gesture/emotion cue response."""
    model_config = ConfigDict(populate_by_name=True)

    gesture: GestureType
    emotion: EmotionTag
    intensity: float = Field(..., ge=0.0, le=1.0)
    duration_ms: int
    transition_smoothness: float

class LeaderboardRequest(BaseModel):
    """Leaderboard request."""
    model_config = ConfigDict(populate_by_name=True)

    scope: LeaderboardScope
    period: str = "weekly"
    language_pair: Optional[str] = None
    country_code: Optional[str] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=100)

class LeaderboardResponse(BaseModel):
    """Leaderboard response."""
    model_config = ConfigDict(populate_by_name=True)

    entries: List[Dict[str, Any]]
    user_rank: Optional[int] = None
    user_score: Optional[int] = None
    total_participants: int
    period_start: datetime
    period_end: datetime

class SocialMatchRequest(BaseModel):
    """Social matching request."""
    model_config = ConfigDict(populate_by_name=True)

    user_id: UUID
    target_language: LanguageCode
    native_language: LanguageCode
    interests: Optional[List[str]] = None
    preferred_age_range: Optional[tuple] = None

class SocialMatchResponse(BaseModel):
    """Social matching response."""
    model_config = ConfigDict(populate_by_name=True)

    matches: List[Dict[str, Any]]
    match_count: int

class FraudCheckRequest(BaseModel):
    """Fraud check request."""
    model_config = ConfigDict(populate_by_name=True)

    user_id: UUID
    transaction_type: str
    amount: int
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_data: Optional[Dict[str, Any]] = None

class FraudCheckResponse(BaseModel):
    """Fraud check response."""
    model_config = ConfigDict(populate_by_name=True)

    is_fraudulent: bool
    risk_level: FraudRiskLevel
    risk_score: float
    triggered_rules: List[str]
    recommended_action: str
    review_required: bool

class LiveConversationRequest(BaseModel):
    """Live conversation initiation request."""
    model_config = ConfigDict(populate_by_name=True)

    user_id: UUID
    mode: ConversationMode = ConversationMode.VOICE
    language: LanguageCode = LanguageCode.EN  # target language the user wants to LEARN
    native_language: Optional[LanguageCode] = None  # user's own/spoken language; auto-detected from speech if omitted
    topic: Optional[str] = None
    difficulty: Optional[CEFRLevel] = None

class LiveConversationResponse(BaseModel):
    """Live conversation response."""
    model_config = ConfigDict(populate_by_name=True)

    session_id: str
    websocket_url: str
    ice_servers: List[Dict[str, Any]]
    estimated_latency_ms: int
    mode: ConversationMode

class BackupRequest(BaseModel):
    """Backup operation request."""
    model_config = ConfigDict(populate_by_name=True)

    backup_type: str = "full"
    tables: Optional[List[str]] = None
    compress: bool = True
    encrypt: bool = True

class BackupResponse(BaseModel):
    """Backup operation response."""
    model_config = ConfigDict(populate_by_name=True)

    backup_id: UUID
    status: BackupStatus
    s3_key: Optional[str] = None
    file_size_bytes: Optional[int] = None
    started_at: datetime
    estimated_completion: Optional[datetime] = None

# ============================================================
# UTILITY MODELS
# ============================================================

class RateLimitInfo(BaseModel):
    """Rate limit information."""
    model_config = ConfigDict(populate_by_name=True)

    limit: int
    remaining: int
    reset_at: datetime
    window: str

class ServiceMetrics(BaseModel):
    """Service metrics."""
    model_config = ConfigDict(populate_by_name=True)

    service_name: str
    requests_total: int
    requests_per_second: float
    avg_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    error_rate: float
    active_connections: int
    cpu_percent: float
    memory_percent: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class SecurityScanResult(BaseModel):
    """Security scan result."""
    model_config = ConfigDict(populate_by_name=True)

    scan_id: str
    scan_type: str
    severity_counts: Dict[str, int]
    findings: List[Dict[str, Any]]
    passed: bool
    scanned_at: datetime = Field(default_factory=datetime.utcnow)

print("✅ shared/models/common.py created (all enums + ORM + Pydantic models)")
