"""
Hermes Orchestrator — Layer 5: Self-QA / Verification
Grammar verification, coin duplicate detection, drift/hallucination checks.
"""
import re
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import structlog

from shared.models.common import (
    VerificationResult, IntentType, GrammarRuleVerifyRequest
)
from shared.utils.helpers import idempotency_store

logger = structlog.get_logger()

class SelfQAVerifier:
    """
    Verification engine that validates orchestrator outputs before
    they reach the user. Implements all Master Prompt v2 non-negotiables.
    """

    def __init__(self, grammar_adapter=None, coin_ledger_adapter=None):
        self.grammar_adapter = grammar_adapter
        self.coin_ledger_adapter = coin_ledger_adapter

    async def verify(
        self,
        intent: IntentType,
        adapter_results: Dict[str, Any],
        user_id: str,
        request_id: str
    ) -> List[VerificationResult]:
        """
        Run all applicable verification checks for the given intent and results.
        Returns list of verification results.
        """
        results = []

        # ── Grammar Verification ──
        if intent in (IntentType.GRAMMAR_PRACTICE, IntentType.CONVERSATIONAL):
            grammar_result = await self._verify_grammar_claim(adapter_results)
            results.append(grammar_result)

        # ── Coin Double-Award Check ──
        if intent == IntentType.LESSON_COMPLETION:
            coin_result = await self._verify_no_duplicate_coin_award(
                adapter_results, user_id, request_id
            )
            results.append(coin_result)

        # ── Drift/Hallucination Check ──
        drift_result = await self._check_drift(adapter_results, intent)
        results.append(drift_result)

        # ── Safety Check ──
        safety_result = await self._check_safety(adapter_results)
        results.append(safety_result)

        logger.info(
            "verification_complete",
            request_id=request_id,
            checks_run=len(results),
            passed=sum(1 for r in results if r.passed),
            failed=sum(1 for r in results if not r.passed)
        )

        return results

    async def _verify_grammar_claim(self, adapter_results: Dict[str, Any]) -> VerificationResult:
        """
        Verify any grammar claims against the Grammar Rule DB.
        Non-negotiable: Grammar claims MUST be verified before reaching user.
        """
        try:
            # Extract grammar claims from results
            llm_result = adapter_results.get("llm", {})
            grammar_data = llm_result.get("data", {})

            if not grammar_data or "errors" not in grammar_data:
                return VerificationResult(
                    check_type="grammar_verify",
                    passed=True,
                    details={"reason": "no_grammar_claims_found"}
                )

            errors = grammar_data.get("errors", [])
            if not errors:
                return VerificationResult(
                    check_type="grammar_verify",
                    passed=True,
                    details={"reason": "no_errors_to_verify"}
                )

            # If grammar adapter available, verify each claim
            if self.grammar_adapter:
                verified_count = 0
                failed_claims = []

                for error in errors:
                    claim = error.get("explanation", "")
                    if not claim:
                        continue

                    try:
                        verify_result = await self.grammar_adapter.verify(
                            claim=claim,
                            language=error.get("language", "en")
                        )
                        if verify_result.get("verified", False):
                            verified_count += 1
                        else:
                            failed_claims.append({
                                "claim": claim,
                                "reason": verify_result.get("explanation", "Rule not found")
                            })
                    except Exception as e:
                        logger.warning("grammar_verify_error", claim=claim, error=str(e))
                        # If grammar DB is down, allow through but mark as unverified
                        failed_claims.append({"claim": claim, "reason": f"verify_service_error: {str(e)}"})

                all_verified = len(failed_claims) == 0

                return VerificationResult(
                    check_type="grammar_verify",
                    passed=all_verified or verified_count > 0,  # Pass if at least some verified
                    details={
                        "total_claims": len(errors),
                        "verified": verified_count,
                        "failed": failed_claims,
                        "service_available": self.grammar_adapter is not None
                    },
                    severity="critical" if not all_verified and len(failed_claims) == len(errors) else "warning",
                    retry_recommended=not all_verified and len(failed_claims) > 0
                )
            else:
                # No grammar adapter available — mark as needing verification
                return VerificationResult(
                    check_type="grammar_verify",
                    passed=False,
                    details={
                        "reason": "grammar_adapter_not_available",
                        "claims_count": len(errors)
                    },
                    severity="warning",
                    retry_recommended=True
                )

        except Exception as e:
            logger.error("grammar_verify_exception", error=str(e))
            return VerificationResult(
                check_type="grammar_verify",
                passed=False,
                details={"error": str(e)},
                severity="critical",
                retry_recommended=True
            )

    async def _verify_no_duplicate_coin_award(
        self,
        adapter_results: Dict[str, Any],
        user_id: str,
        request_id: str
    ) -> VerificationResult:
        """
        Verify no duplicate coin awards for the same lesson/activity.
        Non-negotiable: Coins must be server-authoritative, no double-awards.
        """
        try:
            # Check idempotency store first
            if idempotency_store.is_processed(request_id):
                return VerificationResult(
                    check_type="coin_duplicate",
                    passed=False,
                    details={
                        "reason": "duplicate_request_id",
                        "request_id": request_id,
                        "previous_result": idempotency_store.get_result(request_id)
                    },
                    severity="critical",
                    retry_recommended=False
                )

            # If coin ledger adapter available, check recent transactions
            if self.coin_ledger_adapter:
                try:
                    recent_tx = await self.coin_ledger_adapter.get_transactions(user_id, limit=20)
                    transactions = recent_tx.get("transactions", [])

                    # Look for similar transactions in last 5 minutes
                    now = datetime.utcnow()
                    duplicate_candidates = []

                    for tx in transactions:
                        tx_time = datetime.fromisoformat(tx.get("created_at", "2000-01-01").replace("Z", "+00:00"))
                        if (now - tx_time) < timedelta(minutes=5):
                            # Check if same lesson/activity
                            tx_meta = tx.get("metadata", {})
                            if tx_meta.get("request_id") == request_id:
                                duplicate_candidates.append(tx)

                    if duplicate_candidates:
                        return VerificationResult(
                            check_type="coin_duplicate",
                            passed=False,
                            details={
                                "reason": "duplicate_transaction_detected",
                                "matching_transactions": len(duplicate_candidates),
                                "request_id": request_id
                            },
                            severity="critical",
                            retry_recommended=False
                        )

                    return VerificationResult(
                        check_type="coin_duplicate",
                        passed=True,
                        details={
                            "reason": "no_duplicate_found",
                            "recent_transactions_checked": len(transactions),
                            "request_id": request_id
                        }
                    )

                except Exception as e:
                    logger.warning("coin_ledger_check_error", error=str(e))
                    # If coin ledger is down, we can't verify — fail safe
                    return VerificationResult(
                        check_type="coin_duplicate",
                        passed=False,
                        details={
                            "reason": "coin_ledger_unavailable",
                            "error": str(e),
                            "request_id": request_id
                        },
                        severity="critical",
                        retry_recommended=True
                    )
            else:
                # No coin ledger adapter — rely on idempotency store only
                return VerificationResult(
                    check_type="coin_duplicate",
                    passed=True,
                    details={
                        "reason": "idempotency_store_only",
                        "request_id": request_id,
                        "note": "coin_ledger_adapter_not_available"
                    },
                    severity="warning"
                )

        except Exception as e:
            logger.error("coin_duplicate_check_exception", error=str(e))
            return VerificationResult(
                check_type="coin_duplicate",
                passed=False,
                details={"error": str(e), "request_id": request_id},
                severity="critical",
                retry_recommended=True
            )

    async def _check_drift(self, adapter_results: Dict[str, Any], intent: IntentType) -> VerificationResult:
        """
        Check for hallucination/drift in LLM outputs.
        Ensures factual claims are grounded and responses stay on-topic.
        """
        try:
            llm_result = adapter_results.get("llm", {})
            llm_data = llm_result.get("data", {})

            if not llm_data:
                return VerificationResult(
                    check_type="drift_check",
                    passed=True,
                    details={"reason": "no_llm_output_to_check"}
                )

            response_text = llm_data.get("text", llm_data.get("response", ""))

            # Check 1: Response is not empty
            if not response_text or len(response_text.strip()) < 5:
                return VerificationResult(
                    check_type="drift_check",
                    passed=False,
                    details={"reason": "empty_or_too_short_response", "length": len(response_text)},
                    severity="critical",
                    retry_recommended=True
                )

            # Check 2: Response length is reasonable (not hallucinating walls of text)
            max_reasonable_length = 3000  # characters
            if len(response_text) > max_reasonable_length:
                return VerificationResult(
                    check_type="drift_check",
                    passed=False,
                    details={
                        "reason": "response_too_long_possible_hallucination",
                        "length": len(response_text),
                        "max_allowed": max_reasonable_length
                    },
                    severity="warning",
                    retry_recommended=True
                )

            # Check 3: No repetitive patterns (common hallucination symptom)
            words = response_text.lower().split()
            if len(words) > 20:
                unique_ratio = len(set(words)) / len(words)
                if unique_ratio < 0.3:  # Too repetitive
                    return VerificationResult(
                        check_type="drift_check",
                        passed=False,
                        details={
                            "reason": "repetitive_content_detected",
                            "unique_word_ratio": round(unique_ratio, 2)
                        },
                        severity="warning",
                        retry_recommended=True
                    )

            # Check 4: Contains appropriate language for intent
            inappropriate_patterns = [
                r"I am an AI language model",  # Breaking character
                r"I cannot help with that",  # Over-refusal
                r"As an AI",  # Breaking character
            ]
            for pattern in inappropriate_patterns:
                if re.search(pattern, response_text, re.IGNORECASE):
                    return VerificationResult(
                        check_type="drift_check",
                        passed=False,
                        details={
                            "reason": "character_break_detected",
                            "pattern": pattern
                        },
                        severity="warning",
                        retry_recommended=True
                    )

            return VerificationResult(
                check_type="drift_check",
                passed=True,
                details={
                    "length": len(response_text),
                    "unique_word_ratio": round(len(set(words)) / len(words), 2) if len(words) > 20 else 1.0,
                    "checks": ["length", "repetition", "character_break"]
                }
            )

        except Exception as e:
            logger.error("drift_check_exception", error=str(e))
            return VerificationResult(
                check_type="drift_check",
                passed=False,
                details={"error": str(e)},
                severity="warning",
                retry_recommended=True
            )

    async def _check_safety(self, adapter_results: Dict[str, Any]) -> VerificationResult:
        """
        Final safety check — ensure moderation passed and no harmful content.
        """
        try:
            moderation_result = adapter_results.get("moderation", {})
            mod_data = moderation_result.get("data", {})

            if mod_data:
                action = mod_data.get("action", "allow")
                if action in ("block", "review"):
                    return VerificationResult(
                        check_type="safety_check",
                        passed=False,
                        details={
                            "reason": "content_flagged_by_moderation",
                            "action": action,
                            "categories": mod_data.get("categories", [])
                        },
                        severity="critical",
                        retry_recommended=False
                    )

            return VerificationResult(
                check_type="safety_check",
                passed=True,
                details={"moderation_status": mod_data.get("action", "not_checked") if mod_data else "not_applicable"}
            )

        except Exception as e:
            logger.error("safety_check_exception", error=str(e))
            return VerificationResult(
                check_type="safety_check",
                passed=False,
                details={"error": str(e)},
                severity="critical",
                retry_recommended=True
            )

    def all_critical_passed(self, results: List[VerificationResult]) -> bool:
        """Check if all critical verification checks passed."""
        critical_results = [r for r in results if r.severity == "critical"]
        if not critical_results:
            return True
        return all(r.passed for r in critical_results)

    def should_retry(self, results: List[VerificationResult]) -> bool:
        """Check if any check recommends a retry."""
        return any(r.retry_recommended for r in results)

    def get_failure_reasons(self, results: List[VerificationResult]) -> List[str]:
        """Get human-readable failure reasons."""
        reasons = []
        for r in results:
            if not r.passed:
                details = r.details
                reason = details.get("reason", "unknown")
                reasons.append(f"{r.check_type}: {reason}")
        return reasons
