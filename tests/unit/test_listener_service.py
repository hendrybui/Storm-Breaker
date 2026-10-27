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

def test_interactive_listener_drives_a_live_shell():
    svc = ListenerService()
    info = svc.start("sh", "127.0.0.1", 0, interactive=True)
    port = info["port"]

    # fake reverse shell: banner, then echo whatever it receives
    import subprocess, sys, textwrap
    payload = textwrap.dedent("""
        import socket, sys
        s = socket.create_connection(("127.0.0.1", %d), timeout=5)
        s.sendall(b"uid=0(root) gid=0(root)\\n")
        while True:
            line = s.recv(1024)
            if not line:
                break
            s.sendall(b"out>" + line)
    """) % port
    proc = subprocess.Popen([sys.executable, "-c", payload],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        deadline = time.time() + 5
        while time.time() < deadline and not svc.sessions():
            time.sleep(0.1)
        rows = svc.sessions()
        assert rows and rows[0]["alive"]
        key = rows[0]["key"]

        assert svc.send(key, "id") is True
        deadline = time.time() + 5
        lines = []
        while time.time() < deadline:
            lines += svc.read(key)                     # accumulate: drains clear
            if any("out>id" in ln for ln in lines):
                break
            time.sleep(0.1)
        assert any("uid=0(root)" in ln for ln in lines)   # the banner
        assert any("out>id" in ln for ln in lines)        # the command's echo

        assert svc.send("nope|1:2", "x") is False
        assert svc.read("nope") == []
        assert svc.close(key) is True
        assert svc.close(key) is False
    finally:
        proc.terminate()
        svc.stop("sh")
        assert svc.sessions() == []                        # stop tears down sessions
