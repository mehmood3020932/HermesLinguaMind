"""
Hermes LinguaMind — Grammar Rule DB Service
Port: 8010 | Phase 3 — Production Ready
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json
import time
from datetime import datetime
from typing import Dict, List, Any

import httpx
from fastapi import FastAPI, Request
from pydantic import BaseModel, Field
import structlog
import uvicorn

from shared.models.common import HermesResponse, HealthStatus, GrammarRuleORM, CEFRLevel, GrammarVerifyRequest, GrammarVerifyResponse
from shared.utils.helpers import generate_request_id

logger = structlog.get_logger("hermes.grammar")
app = FastAPI(title="Hermes Grammar DB", version="3.1.0")
_app_start_time = time.time()

LLM_SERVICE_URL = os.getenv("LLM_SERVICE_URL", "http://llm:8001")

# Seed grammar rules
_grammar_rules: List[Dict[str, Any]] = [
    {"rule_id": "en_es_001", "language_pair": "en-es", "rule_name": "Ser vs Estar",
     "rule_description": "Use 'ser' for permanent characteristics and 'estar' for temporary states.",
     "examples": [{"correct": "Soy alto", "incorrect": "Estoy alto"}],
     "exceptions": ["Estar can be used for location"], "cefr_level": "A1", "category": "verbs", "verified": True},
    {"rule_id": "en_fr_001", "language_pair": "en-fr", "rule_name": "Gender Agreement",
     "rule_description": "Adjectives must agree in gender and number with the noun they modify.",
     "examples": [{"correct": "Une grande maison", "incorrect": "Une grand maison"}],
     "exceptions": [], "cefr_level": "A1", "category": "agreement", "verified": True},
    {"rule_id": "en_de_001", "language_pair": "en-de", "rule_name": "Word Order V2",
     "rule_description": "In main clauses, the conjugated verb must be in second position.",
     "examples": [{"correct": "Ich gehe nach Hause", "incorrect": "Ich nach Hause gehe"}],
     "exceptions": ["Questions and subordinate clauses"], "cefr_level": "A2", "category": "syntax", "verified": True},
]

@app.get("/health", response_model=HealthStatus)
async def health_check():
    return HealthStatus(status="healthy", service="grammar_rule_db", version="3.0.0",
                        timestamp=datetime.utcnow(), uptime_seconds=time.time() - _app_start_time)

@app.get("/v1/rules", response_model=HermesResponse)
async def list_rules(request: Request, language_pair: str = None, cefr_level: str = None, category: str = None):
    request_id = getattr(request.state, "request_id", generate_request_id())
    rules = _grammar_rules
    if language_pair:
        rules = [r for r in rules if r["language_pair"] == language_pair]
    if cefr_level:
        rules = [r for r in rules if r["cefr_level"] == cefr_level]
    if category:
        rules = [r for r in rules if r["category"] == category]
    return HermesResponse(success=True, data={"rules": rules, "total": len(rules)}, request_id=request_id)

@app.post("/v1/verify", response_model=HermesResponse)
async def verify_grammar(request: Request, req: GrammarVerifyRequest):
    request_id = getattr(request.state, "request_id", generate_request_id())
    # Find applicable rules
    applicable = [r for r in _grammar_rules if r["language_pair"] == req.language_pair]
    if req.cefr_level:
        applicable = [r for r in applicable if r["cefr_level"] == req.cefr_level.value]

    # Layer 1: fast curated-rule substring check (catches known textbook errors)
    errors = []
    for rule in applicable:
        for ex in rule.get("examples", []):
            if ex.get("incorrect") and ex["incorrect"].lower() in req.text.lower():
                errors.append({"phrase": ex["incorrect"], "correction": ex["correct"],
                               "explanation": rule["rule_description"], "rule_id": rule["rule_id"]})

    confidence = 0.7

    # Layer 2: real LLM-based grammar analysis (catches errors the curated
    # rule set doesn't have an example for). Non-fatal — if the LLM service
    # is unreachable, Layer 1's result is still returned rather than failing
    # the whole request.
    try:
        async with httpx.AsyncClient(timeout=25.0) as client:
            llm_resp = await client.post(f"{LLM_SERVICE_URL}/v1/grammar-check", json={"text": req.text})
            llm_resp.raise_for_status()
            llm_data = llm_resp.json()
            if llm_data.get("success") and isinstance(llm_data.get("data"), dict):
                llm_errors = llm_data["data"].get("errors", [])
                existing_phrases = {e.get("phrase") for e in errors}
                for e in llm_errors:
                    if e.get("phrase") not in existing_phrases:
                        errors.append(e)
                confidence = float(llm_data["data"].get("confidence", 0.85))
    except Exception as e:
        logger.warning("llm_grammar_check_unavailable", request_id=request_id, error=str(e))

    is_correct = len(errors) == 0
    response = GrammarVerifyResponse(is_grammatically_correct=is_correct, errors=errors,
                                      suggested_rules=[r["rule_id"] for r in applicable[:3]],
                                      confidence=round(confidence if not is_correct else max(confidence, 0.9), 2))
    return HermesResponse(success=True, data=response.model_dump(), request_id=request_id)

@app.post("/v1/rules", response_model=HermesResponse)
async def add_rule(request: Request, rule: dict):
    request_id = getattr(request.state, "request_id", generate_request_id())
    rule["created_at"] = datetime.utcnow().isoformat()
    _grammar_rules.append(rule)
    logger.info("rule_added", request_id=request_id, rule_id=rule.get("rule_id"))
    return HermesResponse(success=True, data={"rule_id": rule.get("rule_id"), "status": "added"}, request_id=request_id)

@app.get("/v1/metrics")
async def get_metrics():
    return {"uptime_seconds": time.time() - _app_start_time, "total_rules": len(_grammar_rules)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8010, log_level="info")
