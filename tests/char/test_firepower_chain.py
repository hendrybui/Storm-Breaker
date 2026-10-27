"""Acceptance chain (P14.11) — one pass, no copy-paste, everything verified.

scan -> strike -> verified callback -> evidence on target -> report.
This is the G10 acceptance test: if a human has to copy-paste between steps,
it fails.
"""
from __future__ import annotations

import pytest
import requests


@pytest.mark.char
def test_firepower_chain(live_server: str, admin_session: requests.Session) -> None:
    # 1) the strike surface is exposed
    acts = admin_session.get(f"{live_server}/api/strike/actions", timeout=10)
    assert acts.status_code == 200
    assert "python_reverse" in acts.json()["runnable"]

    # 2) REAL scan finds the live server port
    scan = admin_session.post(f"{live_server}/api/net/scan",
                              json={"host": "127.0.0.1", "ports": "2525", "timeout": 0.5},
                              timeout=20).json()
    assert 2525 in scan["open"], scan

    # 3) fire a payload and VERIFY the callback
    strike = admin_session.post(f"{live_server}/api/strike/reverse",
                                json={"payload_type": "python_reverse"}, timeout=45)
    assert strike.status_code == 200
    data = strike.json()
    assert data["ok"] is True, data["summary"]
    assert data["callback"]["ok"] is True

    # 4) the verified result is persisted as evidence on a target
    target = admin_session.get(f"{live_server}/api/targets/{data['target_id']}",
                               timeout=10).json()["target"]
    assert target["findings"], "no evidence recorded"
    assert target["findings"][0]["evidence"]["callback_ok"] is True

    # 5) the evidence renders into a standalone report
    report = admin_session.get(f"{live_server}/api/targets/{data['target_id']}/report",
                               timeout=10)
    assert report.status_code == 200
    assert "text/html" in report.headers.get("Content-Type", "")
    assert "callback=VERIFIED" in report.text
