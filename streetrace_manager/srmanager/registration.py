"""Registration module: driver registration and skills."""

from __future__ import annotations

from .errors import BusinessRuleError, NotRegisteredError
from .store import Store


class Registration:
    def __init__(self, store: Store) -> None:
        self._store = store

    def register_driver(self, name: str) -> None:
        if not name or not name.strip():
            raise ValueError("Driver name is required")
        if name in self._store.drivers:
            raise BusinessRuleError("Driver already registered")
        self._store.drivers[name] = {}

    def require_driver(self, name: str) -> None:
        if name not in self._store.drivers:
            raise NotRegisteredError("Driver is not registered")

    def set_driver_skill(self, name: str, skill: str, level: int) -> None:
        self.require_driver(name)
        if level < 0:
            raise ValueError("Skill level must be >= 0")
        if not skill or not skill.strip():
            raise ValueError("Skill name is required")
        self._store.drivers[name][skill] = level

    def driver_skill(self, name: str, skill: str) -> int:
        self.require_driver(name)
        return int(self._store.drivers[name].get(skill, 0))
