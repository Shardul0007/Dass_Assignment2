"""Crew management module."""

from __future__ import annotations

from .errors import BusinessRuleError, NotFoundError
from .models import CrewMember
from .store import Store


class CrewManagement:
    def __init__(self, store: Store) -> None:
        self._store = store

    def hire_crew_member(self, name: str, role: str) -> None:
        if not name or not name.strip():
            raise ValueError("Crew member name is required")
        if not role or not role.strip():
            raise ValueError("Role is required")
        if name in self._store.crew:
            raise BusinessRuleError("Crew member already hired")
        self._store.crew[name] = CrewMember(name=name, role=role)

    def require_crew_member(self, name: str) -> CrewMember:
        if name not in self._store.crew:
            raise NotFoundError("Crew member not found")
        return self._store.crew[name]

    def set_crew_skill(self, name: str, skill: str, level: int) -> None:
        member = self.require_crew_member(name)
        if not skill or not skill.strip():
            raise ValueError("Skill name is required")
        member.set_skill(skill, level)
