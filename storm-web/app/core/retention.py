"""Capture-dir retention / rotation (HANDOFF plan section P7.5).

Removes top-level capture files older than a retention window from the
capture directories (``images/``, ``sounds/``, ``videos/``,
``keystrokes/``, ``fingerprints/``, ``sessions/``).  Mirrors the 30-day
convention of ``database.cleanup_old_data(days=30)`` — file rotation
only; DB rows are never touched by this module.

Runs on a daemon worker (one per process, started by the factory) every
hour; first pass is delayed so normal boots/tests are never disturbed.

Configuration:
- ``STORM_RETENTION_DAYS``  retention window in days (default 30; ``0``
  disables the worker entirely — nothing is ever deleted).
- ``STORM_RETENTION_INTERVAL_S``  loop interval (default 3600).
"""
from __future__ import annotations

import os
import threading
import time
from pathlib import Path
from typing import List, Optional

_HERE = Path(__file__).resolve().parent
STORM_WEB_DIR = str(_HERE.parents[2])

DEFAULT_DIRS: List[str] = ['images', 'sounds', 'videos', 'keystrokes',
                           'fingerprints', 'sessions']

_worker_lock = threading.Lock()
_worker_started = False


def rotate_capture_dirs(retention_days: float,
                        base_dir: Optional[str] = None,
                        dirs: Optional[List[str]] = None,
                        now: Optional[float] = None) -> int:
    """Delete top-level capture files older than ``retention_days``.

    Returns the number of files removed.  Never recurses into
    subdirectories and never touches dotfiles.  Per-file errors are
    skipped (rotation must never break the app).
    """
    base = base_dir or STORM_WEB_DIR
    cutoff = (now if now is not None else time.time()) - retention_days * 86400
    removed = 0
    for name in (dirs if dirs is not None else DEFAULT_DIRS):
        d = os.path.join(base, name)
        try:
            entries = os.listdir(d)
        except OSError:
            continue
        for entry in entries:
            if entry.startswith('.'):
                continue
            fp = os.path.join(d, entry)
            try:
                if not os.path.isfile(fp):
                    continue
                if os.path.getmtime(fp) < cutoff:
                    os.remove(fp)
                    removed += 1
            except OSError:
                continue
    return removed


def _retention_days() -> int:
    try:
        return int(os.environ.get('STORM_RETENTION_DAYS', '30'))
    except ValueError:
        return 30


def start_retention_worker() -> bool:
    """Start the hourly rotation daemon (once per process).

    Returns ``True`` when a worker was started; ``False`` when disabled
    (``STORM_RETENTION_DAYS=0``) or already running.
    """
    global _worker_started
    days = _retention_days()
    if days <= 0:
        return False
    with _worker_lock:
        if _worker_started:
            return False
        _worker_started = True

    interval = 3600
    try:
        interval = int(os.environ.get('STORM_RETENTION_INTERVAL_S', '3600'))
    except ValueError:
        pass

    def _loop() -> None:
        time.sleep(60)  # delayed first pass: never disturb boots/tests
        while True:
            try:
                rotate_capture_dirs(days)
            except Exception:
                pass
            time.sleep(interval)

    t = threading.Thread(target=_loop, name='storm-retention', daemon=True)
    t.start()
    return True


def reset_worker_flag() -> None:
    """Test helper: forget that a worker was started."""
    global _worker_started
    with _worker_lock:
        _worker_started = False


__all__ = ["DEFAULT_DIRS", "rotate_capture_dirs", "start_retention_worker",
           "reset_worker_flag"]
