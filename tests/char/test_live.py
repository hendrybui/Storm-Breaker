"""Acceptance for the realtime channel (P10) over real HTTP."""
from __future__ import annotations

import threading
import time

import pytest
import requests

from ._helpers import ingest_suffix


@pytest.mark.char
def test_live_snapshot_shape(live_server: str, admin_session: requests.Session) -> None:
    data = admin_session.get(f"{live_server}/api/live", timeout=10).json()
    assert set(["events", "subscribers", "listeners", "beacons"]).issubset(data)


@pytest.mark.char
def test_sse_stream_delivers_a_beacon_event(live_server: str,
                                            admin_session: requests.Session) -> None:
    got: list = []

    def reader():
        with requests.get(f"{live_server}/api/events", cookies=admin_session.cookies,
                          stream=True, timeout=15) as resp:
            for line in resp.iter_lines(decode_unicode=True):
                # foreign beacons may share the bus; match only our own poll's event
                if line and line.startswith("data:") and "sse-agent" in line:
                    got.append(line)
                    break

    worker = threading.Thread(target=reader, daemon=True)
    worker.start()
    time.sleep(0.6)                                  # let the stream subscribe

    # a victim poll publishes a 'beacon' event on the bus
    requests.post(f"{live_server}/api/c2/poll{ingest_suffix()}",
                  json={"uid": "sse-agent"}, timeout=10)

    worker.join(8)
    assert got, "no SSE data received"
    assert "beacon" in got[0] and "sse-agent" in got[0]
