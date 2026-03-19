"""Extra module: Garage for car registration, damage, and repair."""

from __future__ import annotations

from .errors import BusinessRuleError, NotFoundError
from .models import Car
from .store import Store


class Garage:
    def __init__(self, store: Store) -> None:
        self._store = store

    def add_car(self, car_id: str, model: str) -> None:
        if not car_id or not car_id.strip():
            raise ValueError("Car ID is required")
        if car_id in self._store.cars:
            raise BusinessRuleError("Car already exists")
        if not model or not model.strip():
            raise ValueError("Car model is required")
        self._store.cars[car_id] = Car(car_id=car_id, model=model)

    def require_car(self, car_id: str) -> Car:
        if car_id not in self._store.cars:
            raise NotFoundError("Car not found")
        return self._store.cars[car_id]

    def damage_car(self, car_id: str, amount: int) -> None:
        car = self.require_car(car_id)
        car.apply_damage(amount)

    def repair_car(self, car_id: str, amount: int) -> None:
        car = self.require_car(car_id)
        car.repair(amount)
