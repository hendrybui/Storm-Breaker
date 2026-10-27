#!/usr/bin/env python3
"""P12.3 — single-file HTML report artifact.

Renders a target's findings + evidence into ONE self-contained HTML file
(inline CSS, no CDN) that can be handed to a client as-is.

    python3 scripts/make_report.py --target 13 --out report.html
"""
from __future__ import annotations

import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "storm-web"))

from app.core.migrations.runner import migrate  # noqa: E402
from app.targets import TargetStore  # noqa: E402
from app.targets.report import render_html  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="Render a target report as one HTML file")
    ap.add_argument("--target", type=int, required=True, help="target id")
    ap.add_argument("--out", default=None, help="output path (default report_target_<id>.html)")
    args = ap.parse_args()

    migrate()
    target = TargetStore().get(args.target)
    if target is None:
        print("no target with id %d" % args.target)
        return 1

    html = render_html(target)
    out = args.out or "report_target_%d.html" % args.target
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(html)

    findings = len(target.get("findings") or [])
    print("wrote %s (%d bytes, %d finding(s), self-contained)"
          % (out, len(html), findings))
    return 0


if __name__ == "__main__":
    sys.exit(main())
