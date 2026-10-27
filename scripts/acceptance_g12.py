#!/usr/bin/env python3
"""G12 acceptance — realtime push + panel, driven end to end, no copy-paste.

Proves the operator can SEE live activity: the panel ships the Live Ops tab and
an SSE stream carries listener / beacon / strike events as they happen.

Exit 0 == PASS.  Run from the repo root:  python3 scripts/acceptance_g12.py
"""
import json
import socket
import subprocess
import sys
import threading
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


def main() -> int:
    steps = []
    server = start_server()
    events = []
    stop = threading.Event()

    try:
        s = requests.Session()
        s.post(BASE + "/login", data={"username": USER, "password": PASSWD}, timeout=5)

        # 1) the panel actually ships the live surface
        panel = s.get(BASE + "/panel", timeout=10).text
        steps.append(("panel ships the Live Ops tab", 'id="tab-live"' in panel))
        steps.append(("panel loads the push consumer", "storm_live.js" in panel))

        # 2) subscribe to the SSE stream
        def reader():
            try:
                with requests.get(BASE + "/api/events", cookies=s.cookies,
                                  stream=True, timeout=30) as resp:
                    for line in resp.iter_lines(decode_unicode=True):
                        if stop.is_set():
                            break
                        if line and line.startswith("data:"):
                            events.append(json.loads(line[5:]))
            except Exception:
                pass

        worker = threading.Thread(target=reader, daemon=True)
        worker.start()
        time.sleep(0.6)

        # 3) listener connection -> 'listener' event
        info = s.post(BASE + "/api/listeners/start", timeout=5,
                      json={"name": "g12", "host": "127.0.0.1", "port": 0}).json()["listener"]
        c = socket.create_connection(("127.0.0.1", info["port"]), timeout=2)
        c.close()

        # 4) victim poll -> 'beacon' event
        requests.post(BASE + "/api/c2/poll", json={"uid": "g12-agent"}, timeout=10)

        # 5) strike -> 'strike' event with a verified callback
        strike = s.post(BASE + "/api/strike/reverse",
                        json={"payload_type": "python_reverse"}, timeout=45).json()

        time.sleep(1.0)
        stop.set()
        worker.join(3)

        kinds = [e.get("kind") for e in events]
        steps.append(("SSE delivered a listener event", "listener" in kinds))
        steps.append(("SSE delivered a beacon event", "beacon" in kinds))
        steps.append(("SSE delivered a strike event", "strike" in kinds))
        strike_events = [e for e in events if e.get("kind") == "strike"]
        steps.append(("strike event carries the VERIFIED callback",
                      bool(strike_events) and strike_events[0].get("callback_ok") is True))

        # 6) snapshot endpoint agrees
        live = s.get(BASE + "/api/live", timeout=10).json()
        steps.append(("live snapshot reports the listener", len(live["listeners"]) >= 1))

        ok = True
        for name, res in steps:
            print(("  PASS  " if res else "  FAIL  ") + name)
            ok = ok and res
        print("   (strike summary: %s)" % strike.get("summary"))
        print("\nG12 ACCEPTANCE:", "PASS" if ok else "FAIL")
        return 0 if ok else 1
    finally:
        stop.set()
        server.terminate()
        time.sleep(0.5)


if __name__ == "__main__":
    sys.exit(main())
