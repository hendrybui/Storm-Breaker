#!/usr/bin/env python3
"""FIREPOWER smoke demo -- act, then verify, with real effects (P14.1 + P14.2).

Run: python3 scripts/demo_firepower.py

Shows the toy-vs-weapon difference in four steps: a *generated* payload is
actually executed and its effect confirmed, with no human copy-paste.
"""
import os
import socket
import sys
import tempfile
import threading

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "storm-web"))

from app.exec.runner import run          # noqa: E402
from app.exec.verify import file_exists, tcp_open, wait_for_connect  # noqa: E402


def free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


print("== FIREPOWER smoke: act -> verify ==")

print("\n[1] Execute a *generated* payload (was just a string before)")
r = run("python3 -c \"print('generated payload executed')\"")
print("    cmd   :", r.cmd)
print("    exit  :", r.exit_code, "| ok:", r.ok, "| %.3fs" % r.duration)
print("    stdout:", r.stdout.strip())

print("\n[2] Execute -> VERIFY a real file effect (evidence, not a promise)")
path = tempfile.mktemp(prefix="storm-evidence-")
r = run("echo strike > %s" % path)
print("    exit  :", r.exit_code)
print("    verify.file_exists :", file_exists(path).ok, "->", file_exists(path).detail)
os.remove(path)

print("\n[3] Aim at a port that is NOT listening (callback not yet arrived)")
port = free_port()
print("    before:", tcp_open("127.0.0.1", port, timeout=0.3).ok)

stop = threading.Event()


def listener():
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("127.0.0.1", port))
    s.listen(1)
    s.settimeout(0.2)
    while not stop.is_set():
        try:
            c, _ = s.accept()
            c.close()
        except socket.timeout:
            pass
    s.close()


threading.Thread(target=listener, daemon=True).start()
res = wait_for_connect("127.0.0.1", port, timeout=3.0, interval=0.1)
print("    after :", res.ok, "->", res.detail)
stop.set()

print("\n[4] Verdict")
print("    run() executed it; verify() confirmed it. No copy-paste, no 'should work'.")
