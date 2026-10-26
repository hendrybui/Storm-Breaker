"""Tests for the strike composition + listener (P14.5).

These are end-to-end: a real payload is generated, launched as a real process,
and its callback is caught on a real socket.  The assertion is on the *effect*
(connection received), not on a string.
"""
import socket

from app.exec.listener import Listener
from app.exec.strike import Strike, launch_payload
from app.exec.runner import ExecResult
from app.exec.verify import CheckResult


def test_listener_records_a_client():
    with Listener() as lis:
        c = socket.create_connection(("127.0.0.1", lis.port), timeout=2)
        assert lis.wait_for_client(timeout=2) is True
        assert lis.clients  # peer recorded
        c.close()


def test_listener_times_out_with_no_client():
    with Listener() as lis:
        assert lis.wait_for_client(timeout=0.3) is False


def test_strike_python_payload_callback_verified():
    s = launch_payload("python_reverse", lport=0, timeout=4.0)
    assert isinstance(s, Strike)
    assert isinstance(s.exec, ExecResult)
    assert isinstance(s.callback, CheckResult)
    assert s.callback.ok is True, s.summary()
    assert s.ok is True
    assert s.target.endswith(str(s.callback.detail).split(":")[-1])
    assert "VERIFIED" in s.summary()


def test_strike_bash_payload_callback_verified():
    s = launch_payload("bash_reverse", lport=0, timeout=4.0)
    assert s.callback.ok is True, s.summary()


def test_strike_generated_artifact_present():
    s = launch_payload("python_reverse", timeout=4.0)
    assert s.generated.get("code")
    assert s.generated.get("payload_type") == "python_reverse"
