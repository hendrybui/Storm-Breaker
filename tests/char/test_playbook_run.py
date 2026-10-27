"""Acceptance for playbook execute+verify (P14.10) over real HTTP."""
from __future__ import annotations

import pytest
import requests


def _create(session: requests.Session, base: str, steps: list) -> int:
    resp = session.post(f"{base}/api/playbooks",
                        json={"name": "audit-run", "description": "p14.10",
                              "steps": steps, "variables": {}}, timeout=10)
    assert resp.status_code == 200
    return resp.json()["id"]


@pytest.mark.char
def test_playbook_run_executes_and_verifies(live_server: str,
                                            admin_session: requests.Session) -> None:
    pid = _create(admin_session, live_server, [
        {"action": "checkpoint", "params": {"name": "start"}},
        {"action": "exec", "params": {"cmd": "echo PLAYBOOK_OK"}},
        {"action": "verify", "params": {"kind": "tcp", "host": "127.0.0.1", "port": 2525}},
        {"action": "log", "params": {"message": "done"}},
    ])
    run = admin_session.post(f"{live_server}/api/playbooks/{pid}/run", json={},
                             timeout=30).json()
    assert run["status"] == "executed" and run["ok"] is True
    assert "PLAYBOOK_OK" in run["results"][1]["output"]
    assert run["results"][2]["verified"] is True    # the verify really checked :2525


@pytest.mark.char
def test_playbook_run_reports_failure_and_rolls_back(live_server: str,
                                                     admin_session: requests.Session) -> None:
    pid = _create(admin_session, live_server, [
        {"action": "checkpoint", "params": {"name": "cp"}},
        {"action": "exec", "params": {"cmd": "exit 9"}, "on_fail": "rollback"},
    ])
    run = admin_session.post(f"{live_server}/api/playbooks/{pid}/run", json={},
                             timeout=30).json()
    assert run["status"] == "failed" and run["ok"] is False
    assert run["rolled_back_to"] == "cp"
