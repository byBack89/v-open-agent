"""TASK-05 deterministic port contracts (ENG-14)."""

from datetime import UTC, datetime, timedelta, timezone

import pytest

from voa.engine.ports import FixedEpochClock, IdFactory, SequentialIdFactory, UtcClock


def test_prefix_sequences_are_independent_and_repeatable() -> None:
    for _ in range(2):
        ids: IdFactory = SequentialIdFactory()
        assert ids.new("risk") == "risk_0001"
        assert ids.new("alert") == "alert_0001"
        assert ids.new("obs") == "obs_0001"
        assert ids.new("sess") == "sess_0001"
        assert ids.new("notice") == "notice_0001"
        assert ids.new("risk") == "risk_0002"
        assert ids.new("alert") == "alert_0002"
        assert ids.new("obs") == "obs_0002"
        assert ids.new("sess") == "sess_0002"
        assert ids.new("notice") == "notice_0002"


def test_sequences_do_not_wrap_at_four_digits() -> None:
    ids = SequentialIdFactory()
    for _ in range(9_999):
        ids.new("obs")
    assert ids.new("obs") == "obs_10000"


def test_default_clock_maps_epoch_and_delayed_input_without_state() -> None:
    clock: UtcClock = FixedEpochClock()
    epoch = datetime(2026, 11, 9, tzinfo=UTC)
    assert clock.at(0) == epoch
    assert clock.at(12_345_678_999) == epoch + timedelta(microseconds=12_345_678)
    assert clock.at(0) == epoch


def test_custom_epoch_uses_integer_microsecond_precision() -> None:
    epoch = datetime(2026, 1, 1, 23, 59, 59, 999999, tzinfo=UTC)
    clock = FixedEpochClock(epoch=epoch)
    assert clock.at(999) == epoch
    assert clock.at(1_000) == datetime(2026, 1, 2, tzinfo=UTC)
    assert clock.at(86_400_000_000_000) == epoch + timedelta(days=1)


@pytest.mark.parametrize(
    "epoch",
    [datetime(2026, 11, 9), datetime(2026, 11, 9, tzinfo=timezone(timedelta(hours=9)))],
)
def test_clock_rejects_missing_or_non_utc_timezone(epoch: datetime) -> None:
    with pytest.raises(ValueError, match="UTC"):
        FixedEpochClock(epoch=epoch)
