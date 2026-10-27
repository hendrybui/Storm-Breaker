"""Tests for the managed listener service (P15.3) -- real ports, real connects."""
import socket
import time

from app.exec import verify
from app.exec.listener_service import ListenerService


def test_start_list_stop_lifecycle():
    svc = ListenerService()
    info = svc.start("t1", "127.0.0.1", 0)
    port = info["port"]
    assert port > 0
    assert verify.tcp_open("127.0.0.1", port).ok is True
    assert [item["name"] for item in svc.list()] == ["t1"]

    assert svc.stop("t1") is True
    assert verify.tcp_open("127.0.0.1", port).ok is False
    assert svc.stop("t1") is False


def test_start_is_idempotent_and_records_connections():
    svc = ListenerService()
    first = svc.start("t2", "127.0.0.1", 0)
    again = svc.start("t2", "127.0.0.1", 0)
    assert again["port"] == first["port"]  # same listener, not a second one

    sock = socket.create_connection(("127.0.0.1", first["port"]), timeout=2)
    sock.close()
    time.sleep(0.2)

    assert svc.get("t2").clients  # peer recorded by the accept loop
    assert svc.list()[0]["connections"] >= 1
    svc.stop("t2")


def test_two_named_listeners_are_independent():
    svc = ListenerService()
    a = svc.start("a", "127.0.0.1", 0)
    b = svc.start("b", "127.0.0.1", 0)
    assert a["port"] != b["port"]
    assert sorted(item["name"] for item in svc.list()) == ["a", "b"]
    svc.stop("a")
    svc.stop("b")
