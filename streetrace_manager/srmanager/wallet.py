"""Extra module: Wallet for cash management."""

from __future__ import annotations

from .errors import BusinessRuleError
from .store import Store


class Wallet:
    def __init__(self, store: Store) -> None:
        self._store = store

    def add_cash(self, amount: int) -> None:
        if amount <= 0:
            raise ValueError("Amount must be > 0")
        self._store.cash += int(amount)

    def spend_cash(self, amount: int) -> None:
        if amount <= 0:
            raise ValueError("Amount must be > 0")
        if self._store.cash < amount:
            raise BusinessRuleError("Insufficient cash")
        self._store.cash -= int(amount)
