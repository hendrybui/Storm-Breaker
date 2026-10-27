"""Acceptance chain (P15.6) — a REAL agent beacons on the SERVER's schedule.

Proves the loop is server-driven: a spawned agent sleeps for the jittered
``next_interval_ms`` it is handed, and the server observes the arrivals.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import time

import pytest
import requests


@pytest.mark.char
def test_beacon_agent_follows_server_schedule(live_server: str,
                                              admin_session: requests.Session) -> None:
    cfg = admin_session.post(f"{live_server}/api/c2/beacon_config",
                             json={"base_ms": 600}, timeout=10).json()
    assert cfg["base_ms"] == 600

    uid = "chain-agent"
    src = admin_session.get(f"{live_server}/api/c2/beacon_agent",
                            params={"uid": uid}, timeout=10).text
    assert "next_interval_ms" in src

    path = tempfile.mktemp(suffix=".py")
    with open(path, "w") as fh:
        fh.write(src)
    proc = subprocess.Popen([sys.executable, path],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        deadline = time.time() + 6
        stats = {}
        while time.time() < deadline:
            stats = admin_session.get(f"{live_server}/api/c2/beacons/{uid}",
                                      timeout=10).json()["stats"]
            if stats.get("count", 0) >= 3:
                break
            time.sleep(0.3)
    finally:
        proc.terminate()
        os.unlink(path)

    # the agent actually beacons, on the server's ~600ms schedule (not a fixed 1500)
    assert stats.get("count", 0) >= 3, stats
    assert stats["interval_ms"] is not None
    assert 250 <= stats["interval_ms"] <= 1500, stats
