"""Grammar Rule DB Service Adapter"""
from typing import Dict, Any, Optional
from .base import BaseAdapter

class GrammarRuleDbAdapter(BaseAdapter):
    def __init__(self, base_url: Optional[str] = None):
        super().__init__("grammar_rule_db", base_url)

    async def get_rules(
        self,
        language: str = "en",
        cefr_level: Optional[str] = None,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        params = {"language": language}
        if cefr_level:
            params["cefr_level"] = cefr_level
        if category:
            params["category"] = category
        result = await self._request("GET", "/v1/rules", params=params)
        return result.data if result.success else {"error": result.error}

    async def verify(
        self,
        claim: str,
        rule_reference: Optional[str] = None,
        language: str = "en"
    ) -> Dict[str, Any]:
        result = await self._request("POST", "/v1/verify", payload={
            "claim": claim,
            "rule_reference": rule_reference,
            "language": language
        })
        return result.data if result.success else {"error": result.error}
