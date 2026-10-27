#!/usr/bin/env python3
"""G10 acceptance — the whole firepower chain in one unattended pass.

scan -> strike -> verified callback -> evidence -> report.  Exit 0 == PASS.

Run from the repo root:  python3 scripts/acceptance_firepower.py
"""
import subprocess
import sys
import time

import requests

BASE = "http://127.0.0.1:2525"
USER, PASSWD = "admin", "PASS"


def main() -> int:
    proc = subprocess.Popen(["python3", "storm-web/app.py"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(60):
            try:
                requests.get(BASE + "/login.php", timeout=0.5)
                break
            except Exception:
                time.sleep(0.25)

        s = requests.Session()
        s.post(BASE + "/login", data={"username": USER, "password": PASSWD}, timeout=5)

        steps = []
        acts = s.get(BASE + "/api/strike/actions", timeout=10).json()
        steps.append(("strike surface exposed", "python_reverse" in acts["runnable"]))

        scan = s.post(BASE + "/api/net/scan",
                      json={"host": "127.0.0.1", "ports": "2525", "timeout": 0.5},
                      timeout=20).json()
        steps.append(("real scan finds :2525", 2525 in scan["open"]))

        d = s.post(BASE + "/api/strike/reverse",
                   json={"payload_type": "python_reverse"}, timeout=45).json()
        steps.append(("payload launched, callback VERIFIED", d.get("ok") is True))

        t = s.get(BASE + "/api/targets/%d" % d["target_id"], timeout=10).json()["target"]
        steps.append(("evidence persisted on target",
                      bool(t["findings"]) and t["findings"][0]["evidence"]["callback_ok"] is True))

        rep = s.get(BASE + "/api/targets/%d/report" % d["target_id"], timeout=10)
        steps.append(("report rendered",
                      rep.status_code == 200 and "callback=VERIFIED" in rep.text))

        ok = True
        for name, res in steps:
            print(("  PASS  " if res else "  FAIL  ") + name)
            ok = ok and res
        print("\nG10 ACCEPTANCE:", "PASS" if ok else "FAIL")
        return 0 if ok else 1
    finally:
        proc.terminate()
        time.sleep(0.5)


if __name__ == "__main__":
    sys.exit(main())
