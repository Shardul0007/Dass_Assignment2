"""Facade/orchestrator for StreetRace Manager.

This class composes the required modules:
- Registration
- Crew Management
- Inventory
- Race Management
- Results
- Mission Planning

And two extra modules:
- Garage
- Wallet

The goal is to keep the external API simple while enabling module-level integration
tests and a function-level call graph.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from .crew import CrewManagement
from .garage import Garage
from .inventory import Inventory
from .missions import MissionPlanning
from .models import CrewMember, Mission, Race, RaceResult
from .races import RaceManagement
from .registration import Registration
from .results import Results
from .store import Store
from .wallet import Wallet


@dataclass
class StreetRaceManager:
    """Top-level orchestrator for the system."""

    store: Store = field(default_factory=Store)

    registration: Registration = field(init=False)
    crew_management: CrewManagement = field(init=False)
    garage: Garage = field(init=False)
    inventory: Inventory = field(init=False)
    wallet: Wallet = field(init=False)
    race_management: RaceManagement = field(init=False)
    results: Results = field(init=False)
    mission_planning: MissionPlanning = field(init=False)

    def __post_init__(self) -> None:
        self.registration = Registration(self.store)
        self.crew_management = CrewManagement(self.store)
        self.garage = Garage(self.store)
        self.inventory = Inventory(self.store)
        self.wallet = Wallet(self.store)
        self.race_management = RaceManagement(self.store)
        self.results = Results(self.store)
        self.mission_planning = MissionPlanning(self.store)

    # Convenience accessors (used by CLI/tests)
    @property
    def drivers(self):  # type: ignore[no-untyped-def]
        return self.store.drivers

    @property
    def crew(self):  # type: ignore[no-untyped-def]
        return self.store.crew

    @property
    def cars(self):  # type: ignore[no-untyped-def]
        return self.store.cars

    @property
    def races(self):  # type: ignore[no-untyped-def]
        return self.store.races

    @property
    def missions(self):  # type: ignore[no-untyped-def]
        return self.store.missions

    @property
    def cash(self) -> int:
        return int(self.store.cash)

    # --- Module 1: Registration ---
    def register_driver(self, name: str) -> None:
        self.registration.register_driver(name)

    def set_driver_skill(self, name: str, skill: str, level: int) -> None:
        self.registration.set_driver_skill(name, skill, level)

    def driver_skill(self, name: str, skill: str) -> int:
        return self.registration.driver_skill(name, skill)

    # --- Module 2: Crew Management ---
    def hire_crew_member(self, name: str, role: str) -> None:
        self.crew_management.hire_crew_member(name, role)

    def set_crew_skill(self, name: str, skill: str, level: int) -> None:
        self.crew_management.set_crew_skill(name, skill, level)

    def _require_crew_member(self, name: str) -> CrewMember:
        return self.crew_management.require_crew_member(name)

    # --- Extra Module A: Garage ---
    def add_car(self, car_id: str, model: str) -> None:
        self.garage.add_car(car_id, model)

    def damage_car(self, car_id: str, amount: int) -> None:
        self.garage.damage_car(car_id, amount)

    def repair_car(self, car_id: str, amount: int) -> None:
        self.garage.repair_car(car_id, amount)

    # --- Module 3: Inventory ---
    def add_item(self, item: str, qty: int) -> None:
        self.inventory.add_item(item, qty)

    def consume_item(self, item: str, qty: int) -> None:
        self.inventory.consume_item(item, qty)

    # --- Extra Module B: Wallet ---
    def add_cash(self, amount: int) -> None:
        self.wallet.add_cash(amount)

    def spend_cash(self, amount: int) -> None:
        self.wallet.spend_cash(amount)

    # --- Module 4: Race Management ---
    def create_race(self, race_id: str, name: str, *, min_driver_skill: int = 0, min_car_condition: int = 1) -> None:
        self.race_management.create_race(
            race_id,
            name,
            min_driver_skill=min_driver_skill,
            min_car_condition=min_car_condition,
        )

    def enter_race(self, race_id: str, driver_name: str, car_id: str, *, required_skill: str = "driving") -> None:
        self.registration.require_driver(driver_name)
        car = self.garage.require_car(car_id)

        driver_skill_level = self.registration.driver_skill(driver_name, required_skill)

        self.race_management.enter_race(
            race_id,
            driver_name,
            car_id,
            driver_skill_level=driver_skill_level,
            car_condition=car.condition,
            required_skill=required_skill,
        )

    def start_race(self, race_id: str) -> None:
        self.race_management.start_race(race_id)

    def complete_race(self, race_id: str, outcome: str, *, prize_money: int = 0, damage: int = 0) -> RaceResult:
        race: Race = self.race_management.require_race(race_id)
        result = self.race_management.complete_race(race_id, outcome, prize_money=prize_money, damage=damage)

        self.results.record(result)

        if result.prize_money:
            self.wallet.add_cash(result.prize_money)
        if race.car_id and result.damage:
            self.garage.damage_car(race.car_id, result.damage)

        return result

    # --- Module 5: Results ---
    def list_results(self, race_id: Optional[str] = None) -> List[RaceResult]:
        return self.results.list_results(race_id)

    # --- Module 6: Mission Planning ---
    def plan_mission(self, mission_id: str, mission_type: str, required_roles: List[str]) -> None:
        self.mission_planning.plan_mission(mission_id, mission_type, required_roles)

    def assign_mission(self, mission_id: str, crew_names: List[str]) -> None:
        crew_members = [self._require_crew_member(name) for name in crew_names]
        self.mission_planning.assign_mission(mission_id, crew_members)

    def complete_mission(self, mission_id: str) -> None:
        self.mission_planning.complete_mission(mission_id)

    def _require_mission(self, mission_id: str) -> Mission:
        return self.mission_planning.require_mission(mission_id)
