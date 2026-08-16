"""
Hermes Orchestrator — Layer 2: Intent Classification
Rule-based fast path + LLM fallback for intent detection.
"""
import re
import json
from typing import Dict, Any, Tuple, Optional
from datetime import datetime

import httpx
import structlog

from shared.models.common import IntentType, LanguageCode
from shared.utils.helpers import async_retry, cache

logger = structlog.get_logger()

# ─────────────────────────────────────────────────────────────
# RULE-BASED KEYWORD MAP
# ─────────────────────────────────────────────────────────────

KEYWORD_INTENT_MAP = {
    IntentType.GRAMMAR_PRACTICE: [
        r"\bgrammar\b", r"\bcorrect\b", r"\bwrong\b", r"\bmistake\b",
        r"\berror\b", r"\bsentence structure\b", r"\btense\b",
        r"\bconjugation\b", r"\bpart of speech\b", r"\bsyntax\b",
        r"\bis this correct\b", r"\bcheck my\b", r"\bfix this\b",
        r"\bhow do you say\b.*\bcorrectly\b", r"\bgrammar exercise\b",
    ],
    IntentType.SPEAKING_PRACTICE: [
        r"\bspeak\b", r"\bspeaking\b", r"\bpronunciation\b", r"\bpronounce\b",
        r"\bhow do you say\b", r"\brepeat after me\b", r"\brecord\b",
        r"\bvoice\b", r"\boral\b", r"\btalk\b", r"\bconversation practice\b",
        r"\bspeaking exercise\b", r"\bfluency\b", r"\baccent\b",
        r"\bpractice.*speak\b", r"\bpractice.*pronunciation\b",
    ],
    IntentType.LISTENING_PRACTICE: [
        r"\blisten\b", r"\bhear\b", r"\baudio\b", r"\bcomprehension\b",
        r"\blistening exercise\b", r"\bdictation\b", r"\bwhat did they say\b",
        r"\bcan you read this\b", r"\bread aloud\b", r"\bplay audio\b",
    ],
    IntentType.VOCABULARY_PRACTICE: [
        r"\bvocabulary\b", r"\bword\b", r"\bmeaning\b", r"\bdefine\b",
        r"\bdefinition\b", r"\bsynonym\b", r"\bantonym\b", r"\bflashcard\b",
        r"\bnew word\b", r"\bwhat does.*mean\b", r"\btranslate\b",
        r"\bhow do you say\b", r"\bvocab\b", r"\bword list\b",
    ],
    IntentType.LESSON_COMPLETION: [
        r"\bcomplete lesson\b", r"\bfinish lesson\b", r"\blesson done\b",
        r"\bmark complete\b", r"\bfinish module\b", r"\bmodule complete\b",
        r"\bI finished\b", r"\bdone with lesson\b", r"\blevel up\b",
        r"\bquiz complete\b", r"\btest complete\b", r"\bexercise done\b",
    ],
    IntentType.COIN_TRANSACTION: [
        r"\bcoin\b", r"\breward\b", r"\bspend\b", r"\bpurchase\b",
        r"\bbuy\b", r"\bshop\b", r"\bstore\b", r"\btransaction\b",
        r"\bmy coins\b", r"\bbalance\b", r"\bredeem\b", r"\bclaim reward\b",
        r"\bhow many coin\b", r"\bhow much.*coin\b", r"\bcoin.*have\b",
    ],
    IntentType.SOCIAL_INTERACTION: [
        r"\bfriend\b", r"\bmatch\b", r"\bpartner\b", r"\bchat with\b",
        r"\bsocial\b", r"\bcommunity\b", r"\bfind someone\b",
        r"\blanguage partner\b", r"\bstudy buddy\b", r"\bgroup\b",
        r"\bcompetition\b", r"\bchallenge\b", r"\bleaderboard\b",
    ],
    IntentType.PROFILE_UPDATE: [
        r"\bprofile\b", r"\bsettings\b", r"\bpreferences\b",
        r"\bupdate my\b", r"\bchange my\b", r"\bedit profile\b",
        r"\bmy level\b", r"\bmy goal\b", r"\blearning style\b",
        r"\binterests\b", r"\bnative language\b", r"\btarget language\b",
    ],
}

# Patterns that strongly indicate conversational intent (low priority, catch-all)
CONVERSATION_PATTERNS = [
    r"\bhi\b", r"\bhello\b", r"\bhey\b", r"\bhow are you\b",
    r"\bthank\b", r"\bthanks\b", r"\bgood morning\b", r"\bgood evening\b",
    r"\bbye\b", r"\bgoodbye\b", r"\bsee you\b", r"\bwhat's up\b",
    r"\btell me about\b", r"\bcan you help\b", r"\bi need help\b",
    r"\bquestion\b", r"\bexplain\b", r"\bwhy\b",
    r"\bwhat(?!.*coin)\b", r"\bhow(?!.*many.*coin)\b", r"\bwhen\b", r"\bwhere\b", r"\bwho\b",
]

class IntentClassifier:
    """
    Two-tier intent classification:
    1. Fast rule-based keyword matching
    2. LLM-based fallback for ambiguous cases
    """

    def __init__(self, llm_service_url: str = "http://localhost:8001"):
        self.llm_service_url = llm_service_url
        self._compiled_patterns: Dict[IntentType, list] = {}
        self._compile_patterns()

    def _compile_patterns(self):
        """Pre-compile regex patterns for performance."""
        for intent, patterns in KEYWORD_INTENT_MAP.items():
            self._compiled_patterns[intent] = [re.compile(p, re.IGNORECASE) for p in patterns]
        self._conversation_patterns = [re.compile(p, re.IGNORECASE) for p in CONVERSATION_PATTERNS]

    async def classify(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        use_llm_fallback: bool = True
    ) -> Tuple[IntentType, float, Dict[str, Any]]:
        """
        Classify user message into IntentType.
        Returns: (intent, confidence, metadata)
        """
        context = context or {}

        # ── Tier 1: Rule-based classification ──
        rule_result = self._rule_based_classify(message)
        if rule_result[1] >= 0.85:  # High confidence threshold
            logger.info("intent_rule_match", intent=rule_result[0].value, confidence=rule_result[1])
            return (rule_result[0], rule_result[1], {"method": "rule_based", "matched_keywords": rule_result[2]})

        # ── Tier 2: LLM fallback for ambiguous cases ──
        if use_llm_fallback:
            try:
                llm_result = await self._llm_classify(message, context)
                # Blend rule + LLM confidence
                blended_confidence = max(rule_result[1], llm_result[1])
                if llm_result[1] > rule_result[1]:
                    logger.info("intent_llm_override", 
                               rule_intent=rule_result[0].value, 
                               llm_intent=llm_result[0].value,
                               confidence=blended_confidence)
                    return (llm_result[0], blended_confidence, {"method": "llm_fallback", "llm_reasoning": llm_result[2]})
            except Exception as e:
                logger.warning("llm_classification_failed", error=str(e), fallback_to_rule=True)

        # ── Default: Use best rule match or conversational ──
        if rule_result[1] >= 0.3:
            return (rule_result[0], rule_result[1], {"method": "rule_based_low_confidence"})

        # Check if it looks like a conversation
        convo_score = self._conversation_score(message)
        if convo_score > 0:
            return (IntentType.CONVERSATIONAL, min(0.6, convo_score), {"method": "conversation_heuristic"})

        return (IntentType.UNKNOWN, 0.3, {"method": "fallback"})

    def _rule_based_classify(self, message: str) -> Tuple[IntentType, float, list]:
        """Score message against keyword patterns. Returns (intent, confidence, matched_keywords)."""
        message_lower = message.lower()
        scores: Dict[IntentType, float] = {}
        matched_keywords: Dict[IntentType, list] = {}

        for intent, patterns in self._compiled_patterns.items():
            matches = []
            for pattern in patterns:
                if pattern.search(message_lower):
                    matches.append(pattern.pattern)

            if matches:
                # Score based on number and specificity of matches
                score = min(0.3 + (len(matches) * 0.25), 0.95)
                # Boost for multiple distinct keywords
                unique_stems = len(set(m[:15] for m in matches))
                if unique_stems >= 2:
                    score = min(score + 0.15, 0.98)
                scores[intent] = score
                matched_keywords[intent] = matches[:3]  # Limit stored matches

        if not scores:
            return (IntentType.UNKNOWN, 0.0, [])

        best_intent = max(scores, key=scores.get)
        return (best_intent, scores[best_intent], matched_keywords.get(best_intent, []))

    def _conversation_score(self, message: str) -> float:
        """Score how conversational a message is."""
        message_lower = message.lower()
        matches = sum(1 for p in self._conversation_patterns if p.search(message_lower))
        return min(matches * 0.15, 0.7)

    @async_retry(max_retries=2, backoff_base=1.0)
    async def _llm_classify(self, message: str, context: Dict[str, Any]) -> Tuple[IntentType, float, str]:
        """Call LLM service for intent classification."""

        # Check cache first
        cache_key = f"intent_llm:{hash(message) % 1000000}"
        cached = cache.get(cache_key)
        if cached:
            return (IntentType(cached["intent"]), cached["confidence"], cached.get("reasoning", ""))

        prompt = f"""Classify the following user message into exactly one intent category.

User message: "{message}"
Context: {json.dumps(context, default=str)[:500]}

Available intents:
- conversational: General chat, greetings, questions about anything
- grammar_practice: User wants grammar help, correction, or exercises
- speaking_practice: User wants to practice speaking, pronunciation
- listening_practice: User wants listening comprehension or audio content
- vocabulary_practice: User wants to learn new words, definitions, translations
- lesson_completion: User finished a lesson, quiz, or exercise
- coin_transaction: User mentions coins, rewards, purchases, balance
- social_interaction: User wants to interact with others, find partners
- profile_update: User wants to update settings, preferences, goals
- unknown: Cannot determine intent

Respond ONLY in this JSON format:
{{"intent": "<one_of_above>", "confidence": 0.0-1.0, "reasoning": "brief explanation"}}"""

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{self.llm_service_url}/v1/generate",
                json={
                    "prompt": prompt,
                    "system_prompt": "You are an intent classification assistant. Respond only in valid JSON.",
                    "max_tokens": 200,
                    "temperature": 0.1
                }
            )
            response.raise_for_status()
            data = response.json()

            # Parse LLM response
            llm_text = data.get("text", data.get("response", ""))
            # Extract JSON from response (handle markdown code blocks)
            json_match = re.search(r'\{.*\}', llm_text, re.DOTALL)
            if json_match:
                llm_text = json_match.group()

            result = json.loads(llm_text)
            intent_str = result.get("intent", "unknown").lower().strip()
            confidence = float(result.get("confidence", 0.5))
            reasoning = result.get("reasoning", "")

            # Map to enum
            try:
                intent = IntentType(intent_str)
            except ValueError:
                intent = IntentType.UNKNOWN
                confidence *= 0.5

            # Cache result
            cache.set(cache_key, {
                "intent": intent.value,
                "confidence": confidence,
                "reasoning": reasoning
            }, ttl_seconds=3600)

            return (intent, confidence, reasoning)
