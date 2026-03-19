"""In-memory data store for StreetRace Manager."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from .models import Car, CrewMember, Mission, Race, RaceResult


@dataclass
class Store:
    drivers: Dict[str, Dict[str, int]] = field(default_factory=dict)  # name -> skills
    crew: Dict[str, CrewMember] = field(default_factory=dict)  # name -> CrewMember
    cars: Dict[str, Car] = field(default_factory=dict)  # car_id -> Car
    inventory: Dict[str, int] = field(default_factory=dict)  # item -> qty
    races: Dict[str, Race] = field(default_factory=dict)  # race_id -> Race
    results: List[RaceResult] = field(default_factory=list)
    missions: Dict[str, Mission] = field(default_factory=dict)  # mission_id -> Mission

    cash: int = 0
