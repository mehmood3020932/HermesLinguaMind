"""Coin Ledger Service Adapter"""
from typing import Dict, Any, Optional
from .base import BaseAdapter

class CoinLedgerAdapter(BaseAdapter):
    def __init__(self, base_url: Optional[str] = None):
        super().__init__("coin_ledger", base_url)

    async def create_transaction(
        self,
        user_id: str,
        amount: int,
        transaction_type: str,
        reason: str,
        idempotency_key: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        result = await self._request("POST", "/v1/transaction", payload={
            "user_id": user_id,
            "amount": amount,
            "transaction_type": transaction_type,
            "reason": reason,
            "idempotency_key": idempotency_key,
            "metadata": metadata or {}
        })
        return result.data if result.success else {"error": result.error}

    async def get_balance(self, user_id: str) -> Dict[str, Any]:
        result = await self._request("GET", f"/v1/balance/{user_id}")
        return result.data if result.success else {"error": result.error}

    async def get_transactions(self, user_id: str, limit: int = 50) -> Dict[str, Any]:
        result = await self._request("GET", f"/v1/transactions/{user_id}", params={"limit": limit})
        return result.data if result.success else {"error": result.error}

    async def reconcile(self, user_id: str) -> Dict[str, Any]:
        result = await self._request("POST", "/v1/reconcile", payload={"user_id": user_id})
        return result.data if result.success else {"error": result.error}
