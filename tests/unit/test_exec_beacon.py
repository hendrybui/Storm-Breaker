"""Tests for beacon timing + observation (P15.4)."""
from datetime import datetime

from app.exec import beacon


def _ts(hour: int) -> float:
    return datetime(2026, 1, 1, hour).timestamp()


def test_interval_within_profile_bounds():
    for _ in range(40):
        ms = beacon.next_interval_ms("always_on", now=_ts(12))
        assert 12_000 <= ms <= 18_000  # base 15s +/- 20%


def test_interval_has_jitter():
    vals = {beacon.next_interval_ms("always_on", now=_ts(12)) for _ in range(30)}
    assert len(vals) > 1  # not a fixed cadence


def test_interactive_path_is_fast():
    assert beacon.next_interval_ms("low_slow", interactive=True) < 2000


def test_outside_active_hours_is_slower():
    active = beacon.next_interval_ms("night_owl", now=_ts(22))     # 20-4 active
    inactive = beacon.next_interval_ms("night_owl", now=_ts(12))   # inactive
    assert inactive > active


def test_tracker_records_missed_beacons():
    t = beacon.BeaconTracker()
    base = 1_000_000.0
    t.record("u1", 1000, ts=base)
    t.record("u1", 1000, ts=base + 1.0)
    t.record("u1", 1000, ts=base + 6.0)   # 5s gap vs 1s expected -> missed
    stats = t.stats("u1")
    assert stats["count"] == 3
    assert stats["missed"] >= 1
    assert stats["interval_ms"] is not None


def test_tracker_timeline_shape():
    t = beacon.BeaconTracker()
    t.record("u2", 1500, ts=100.0)
    t.record("u2", 1500, ts=101.5)
    line = t.timeline("u2")
    assert line[0]["actual_ms"] is None and line[1]["actual_ms"] == 1500


def test_schedule_returns_and_records():
    t = beacon.BeaconTracker()
    ms = t.schedule("u3", interactive=True)
    assert ms < 2000
    assert t.stats("u3")["count"] == 1


def test_agent_script_honours_server_interval():
    src = beacon.agent_script("http://127.0.0.1:2525", "abc")
    assert "/api/c2/poll" in src
    assert "next_interval_ms" in src
    compile(src, "agent", "exec")
