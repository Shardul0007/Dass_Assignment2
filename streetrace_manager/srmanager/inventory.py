"""Inventory module: manage items and quantities."""

from __future__ import annotations

from .errors import BusinessRuleError
from .store import Store


class Inventory:
    def __init__(self, store: Store) -> None:
        self._store = store

    def add_item(self, item: str, qty: int) -> None:
        if not item or not item.strip():
            raise ValueError("Item name is required")
        if qty <= 0:
            raise ValueError("Quantity must be > 0")
        self._store.inventory[item] = int(self._store.inventory.get(item, 0)) + int(qty)

    def consume_item(self, item: str, qty: int) -> None:
        if not item or not item.strip():
            raise ValueError("Item name is required")
        if qty <= 0:
            raise ValueError("Quantity must be > 0")
        current = int(self._store.inventory.get(item, 0))
        if current < qty:
            raise BusinessRuleError("Not enough inventory")
        new_qty = current - qty
        if new_qty == 0:
            self._store.inventory.pop(item, None)
        else:
            self._store.inventory[item] = new_qty
