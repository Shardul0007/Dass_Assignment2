"""Core dataclasses (models) for StreetRace Manager."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class CrewMember:
    name: str
    role: str
    skills: Dict[str, int] = field(default_factory=dict)

    def set_skill(self, skill: str, level: int) -> None:
        if level < 0:
            raise ValueError("Skill level must be >= 0")
        self.skills[skill] = level

    def skill_level(self, skill: str) -> int:
        return int(self.skills.get(skill, 0))


@dataclass
class Car:
    car_id: str
    model: str
    condition: int = 100  # 0..100
    damaged: bool = False

    def apply_damage(self, amount: int) -> None:
        if amount < 0:
            raise ValueError("Damage amount must be >= 0")
        self.condition = max(0, self.condition - amount)
        self.damaged = self.condition < 100

    def repair(self, amount: int) -> None:
        if amount < 0:
            raise ValueError("Repair amount must be >= 0")
        self.condition = min(100, self.condition + amount)
        self.damaged = self.condition < 100


@dataclass
class Race:
    race_id: str
    name: str
    min_driver_skill: int = 0
    min_car_condition: int = 1
    driver_name: Optional[str] = None
    car_id: Optional[str] = None
    status: str = "created"  # created|running|completed


@dataclass
class RaceResult:
    race_id: str
    outcome: str  # win|loss
    prize_money: int = 0
    damage: int = 0


@dataclass
class Mission:
    mission_id: str
    mission_type: str
    required_roles: List[str]
    assigned_members: List[str] = field(default_factory=list)
    status: str = "planned"  # planned|active|completed
