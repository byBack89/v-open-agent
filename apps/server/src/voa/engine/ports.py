"""Injected ID and UTC ports with deterministic replay implementations (SPEC §4.1)."""

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Literal, Protocol

IdPrefix = Literal["risk", "alert", "obs", "sess", "notice"]


class IdFactory(Protocol):
    def new(self, prefix: IdPrefix) -> str: ...


class UtcClock(Protocol):
    def at(self, mono_ns: int) -> datetime: ...


@dataclass
class SequentialIdFactory:
    """Independent per-prefix counters; create a fresh factory for each replay."""

    _counts: dict[IdPrefix, int] = field(default_factory=dict, init=False, repr=False)

    def new(self, prefix: IdPrefix) -> str:
        count = self._counts.get(prefix, 0) + 1
        self._counts[prefix] = count
        return f"{prefix}_{count:04d}"


@dataclass(frozen=True)
class FixedEpochClock:
    """Map nanoseconds to UTC, truncating to datetime's microsecond precision."""

    epoch: datetime = datetime(2026, 11, 9, tzinfo=UTC)

    def __post_init__(self) -> None:
        if self.epoch.utcoffset() != timedelta(0):
            raise ValueError("epoch must be timezone-aware UTC")

    def at(self, mono_ns: int) -> datetime:
        return self.epoch + timedelta(microseconds=mono_ns // 1_000)
