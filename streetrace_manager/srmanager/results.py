"""Results module: record and query race results."""

from __future__ import annotations

from typing import Optional

from .models import RaceResult
from .store import Store


class Results:
    def __init__(self, store: Store) -> None:
        self._store = store

    def record(self, result: RaceResult) -> None:
        self._store.results.append(result)

    def list_results(self, race_id: Optional[str] = None) -> list[RaceResult]:
        if race_id is None:
            return list(self._store.results)
        return [r for r in self._store.results if r.race_id == race_id]
