from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class AttemptRecord:
    attempt_number: int
    result: int
    timestamp_utc: str


@dataclass
class LeaderboardData:
    attempts: int = 0
    successes: int = 0
    recent_results: list[AttemptRecord] = field(default_factory=list)


class LocalLeaderboard:
    """Simple local persistence for attempt counts and recent results."""

    def __init__(self, path: Path, max_recent_results: int = 8) -> None:
        self._path = path
        self._max_recent_results = max_recent_results
        self._data = self._load()

    @property
    def data(self) -> LeaderboardData:
        return self._data

    def record_attempt(self, result: int) -> None:
        self._data.attempts += 1
        if result == 1:
            self._data.successes += 1

        record = AttemptRecord(
            attempt_number=self._data.attempts,
            result=result,
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
        )
        self._data.recent_results.insert(0, record)
        self._data.recent_results = self._data.recent_results[: self._max_recent_results]
        self.save()

    def save(self) -> None:
        payload = {
            "attempts": self._data.attempts,
            "successes": self._data.successes,
            "recent_results": [asdict(record) for record in self._data.recent_results],
        }
        self._path.write_text(json.dumps(payload, indent=2))

    def _load(self) -> LeaderboardData:
        if not self._path.exists():
            return LeaderboardData()

        payload = json.loads(self._path.read_text())
        recent_results = [
            AttemptRecord(
                attempt_number=int(item["attempt_number"]),
                result=int(item["result"]),
                timestamp_utc=str(item["timestamp_utc"]),
            )
            for item in payload.get("recent_results", [])
        ]
        return LeaderboardData(
            attempts=int(payload.get("attempts", 0)),
            successes=int(payload.get("successes", 0)),
            recent_results=recent_results,
        )
