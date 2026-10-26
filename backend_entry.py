#!/usr/bin/env python3
"""PyInstaller entry point for the Storm-Breaker backend sidecar (P9.2).

Differences from running storm-web/app.py directly (both sanctioned by
the P9 plan — this file is NEW packaging code, not frozen backend code):

- binds 127.0.0.1 only: the Tauri window talks to the sidecar over
  localhost; the public tunnel use-case is the legacy entry's job.
- chdirs next to the executable so relative writes (Settings.json)
  land in a stable, user-visible place.
- runs migrations + DB init before serving (same as app.py __main__).
"""
import multiprocessing
import os
import sys

multiprocessing.freeze_support()

if getattr(sys, 'frozen', False):
    # onedir layout: <dist>/storm-breaker-backend/<exe> (+ _internal/)
    os.chdir(os.path.dirname(os.path.abspath(sys.executable)))

import database as db  # noqa: E402

db.init_database()

from app import create_app  # noqa: E402

app = create_app()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=2525, debug=False)
