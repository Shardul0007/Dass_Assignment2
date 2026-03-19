"""Race management module."""

from __future__ import annotations

from .errors import BusinessRuleError, NotFoundError
from .models import Race, RaceResult
from .store import Store


class RaceManagement:
    def __init__(self, store: Store) -> None:
        self._store = store

    def create_race(self, race_id: str, name: str, *, min_driver_skill: int = 0, min_car_condition: int = 1) -> None:
        if not race_id or not race_id.strip():
            raise ValueError("Race ID is required")
        if race_id in self._store.races:
            raise BusinessRuleError("Race already exists")
        if not name or not name.strip():
            raise ValueError("Race name is required")
        if min_driver_skill < 0:
            raise ValueError("min_driver_skill must be >= 0")
        if not (0 <= min_car_condition <= 100):
            raise ValueError("min_car_condition must be 0..100")

        self._store.races[race_id] = Race(
            race_id=race_id,
            name=name,
            min_driver_skill=min_driver_skill,
            min_car_condition=min_car_condition,
        )

    def require_race(self, race_id: str) -> Race:
        if race_id not in self._store.races:
            raise NotFoundError("Race not found")
        return self._store.races[race_id]

    def enter_race(
        self,
        race_id: str,
        driver_name: str,
        car_id: str,
        *,
        driver_skill_level: int,
        car_condition: int,
        required_skill: str = "driving",
    ) -> None:
        race = self.require_race(race_id)

        if race.status != "created":
            raise BusinessRuleError("Race is not open for entry")

        if driver_skill_level < race.min_driver_skill:
            raise BusinessRuleError("Driver skill too low")

        if car_condition < race.min_car_condition:
            raise BusinessRuleError("Car condition too low")

        race.driver_name = driver_name
        race.car_id = car_id

    def start_race(self, race_id: str) -> None:
        race = self.require_race(race_id)
        if race.status != "created":
            raise BusinessRuleError("Race cannot be started")
        if not race.driver_name or not race.car_id:
            raise BusinessRuleError("Race entry is incomplete")
        race.status = "running"

    def complete_race(self, race_id: str, outcome: str, *, prize_money: int = 0, damage: int = 0) -> RaceResult:
        race = self.require_race(race_id)
        if race.status != "running":
            raise BusinessRuleError("Race is not running")
        if outcome not in {"win", "loss"}:
            raise ValueError("Outcome must be 'win' or 'loss'")
        if prize_money < 0 or damage < 0:
            raise ValueError("prize_money and damage must be >= 0")

        result = RaceResult(race_id=race_id, outcome=outcome, prize_money=int(prize_money), damage=int(damage))
        race.status = "completed"

        return result
