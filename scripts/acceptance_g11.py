#!/usr/bin/env python3
"""G11 acceptance — C2 survival, managed listener, real observed beacon.

No copy-paste. Exit 0 == PASS.

Run from the repo root:  python3 scripts/acceptance_g11.py
"""
import os
import socket
import subprocess
import sys
import tempfile
import time

import requests

BASE = "http://127.0.0.1:2525"
USER, PASSWD = "admin", "PASS"
DEVNULL = subprocess.DEVNULL


def start_server():
    proc = subprocess.Popen(["python3", "storm-web/app.py"], stdout=DEVNULL, stderr=DEVNULL)
    for _ in range(60):
        try:
            requests.get(BASE + "/login.php", timeout=0.5)
            return proc
        except Exception:
            time.sleep(0.25)
    return proc


def session():
    s = requests.Session()
    s.post(BASE + "/login", data={"username": USER, "password": PASSWD}, timeout=5)
    return s


def main() -> int:
    steps = []
    server = start_server()
    try:
        s = session()

        # 1) C2 session survives a server restart (DB-backed registry)
        requests.post(BASE + "/api/c2/register", timeout=5,
                      json={"uid": "persist-check", "info": {"user": "x", "os": "y"}})
        server.terminate()
        time.sleep(1.0)
        server = start_server()
        s = session()
        clients = s.get(BASE + "/api/c2/clients", timeout=10).json()["clients"]
        steps.append(("C2 session survives restart",
                      any(c["uid"] == "persist-check" for c in clients)))

        # 2) managed listener: start, catch a real connection, stop
        info = s.post(BASE + "/api/listeners/start", timeout=5,
                      json={"name": "g11", "host": "127.0.0.1", "port": 0}).json()["listener"]
        sock = socket.create_connection(("127.0.0.1", info["port"]), timeout=2)
        sock.close()
        time.sleep(0.3)
        listed = s.get(BASE + "/api/listeners", timeout=5).json()["listeners"][0]
        steps.append(("listener start/stop + connect evidence", listed["connections"] >= 1))
        s.post(BASE + "/api/listeners/stop", json={"name": "g11"}, timeout=5)

        # 3) real beacon agent honours the SERVER schedule, and it is observed
        s.post(BASE + "/api/c2/beacon_config", json={"base_ms": 600}, timeout=5)
        src = s.get(BASE + "/api/c2/beacon_agent", params={"uid": "g11-agent"},
                    timeout=10).text
        path = tempfile.mktemp(suffix=".py")
        with open(path, "w") as fh:
            fh.write(src)
        agent = subprocess.Popen(["python3", path], stdout=DEVNULL, stderr=DEVNULL)
        try:
            time.sleep(4.5)
        finally:
            agent.terminate()
            os.unlink(path)

        detail = s.get(BASE + "/api/c2/beacons/g11-agent", timeout=10).json()
        stats = detail["stats"]
        expected = {row["expected_ms"] for row in detail["timeline"]}
        steps.append(("real agent beacons on server schedule", stats["count"] >= 3))
        steps.append(("server chose jittered intervals", len(expected) > 1))

        ok = True
        for name, res in steps:
            print(("  PASS  " if res else "  FAIL  ") + name)
            ok = ok and res
        print("\nG11 ACCEPTANCE:", "PASS" if ok else "FAIL")
        return 0 if ok else 1
    finally:
        server.terminate()
        time.sleep(0.5)


if __name__ == "__main__":
    sys.exit(main())
