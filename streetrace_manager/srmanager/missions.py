"""Mission planning module."""

from __future__ import annotations

from typing import List

from .errors import BusinessRuleError, NotFoundError
from .models import CrewMember, Mission
from .store import Store


class MissionPlanning:
    def __init__(self, store: Store) -> None:
        self._store = store

    def plan_mission(self, mission_id: str, mission_type: str, required_roles: List[str]) -> None:
        if not mission_id or not mission_id.strip():
            raise ValueError("Mission ID is required")
        if mission_id in self._store.missions:
            raise BusinessRuleError("Mission already exists")
        if not mission_type or not mission_type.strip():
            raise ValueError("Mission type is required")
        if not required_roles:
            raise ValueError("required_roles is required")

        self._store.missions[mission_id] = Mission(
            mission_id=mission_id,
            mission_type=mission_type,
            required_roles=list(required_roles),
        )

    def require_mission(self, mission_id: str) -> Mission:
        if mission_id not in self._store.missions:
            raise NotFoundError("Mission not found")
        return self._store.missions[mission_id]

    def assign_mission(self, mission_id: str, crew_members: List[CrewMember]) -> None:
        mission = self.require_mission(mission_id)
        if mission.status != "planned":
            raise BusinessRuleError("Mission is not in planned state")
        if not crew_members:
            raise ValueError("crew_members is required")

        roles_needed = list(mission.required_roles)
        assigned: List[str] = []

        for member in crew_members:
            if member.role in roles_needed:
                roles_needed.remove(member.role)
                assigned.append(member.name)

        if roles_needed:
            raise BusinessRuleError("Required roles not satisfied")

        mission.assigned_members = assigned
        mission.status = "active"

    def complete_mission(self, mission_id: str) -> None:
        mission = self.require_mission(mission_id)
        if mission.status != "active":
            raise BusinessRuleError("Mission is not active")
        mission.status = "completed"
