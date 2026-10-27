"""Durable notification outbox with retry + exponential backoff (P1.3).

Before this, ``send_notification`` fired a bare ``requests.post`` and swallowed
every exception: a webhook that was down for ten seconds lost the event, and the
panel's notification deque died with the process.

Now every notification is **recorded to SQLite first** (so it survives a restart)
and delivery is attempted by a background worker with bounded retries.  The
request path only pays for one row insert.

Deliberately stdlib-only (sqlite3 + threading); ``requests`` is imported lazily
inside the delivery function so the module is usable without it.

States: ``pending`` -> ``delivered`` | ``failed`` (after ``MAX_ATTEMPTS``).
"""
from __future__ import annotations

import json
import threading
import time
from typing import Any, Dict, List, Optional

MAX_ATTEMPTS = 6
# Backoff applied *after* attempt N fails (seconds), clamped to the last entry.
BACKOFF = (2, 5, 15, 60, 300, 900)

POLL_INTERVAL = 3.0
DELIVER_TIMEOUT = 10.0

_thread: Optional[threading.Thread] = None
_stop = threading.Event()
_lock = threading.Lock()


# --- db plumbing -------------------------------------------------------------

def _db_path() -> str:
    import database  # lazy: avoids import-order issues at boot
    return database.DB_PATH


def _conn():
    import sqlite3
    conn = sqlite3.connect(_db_path(), timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


# --- writes ------------------------------------------------------------------

def record(payload: Dict[str, Any], url: str) -> int:
    """Persist one notification.  Returns the outbox row id."""
    with _conn() as conn:
        cur = conn.execute(
            "INSERT INTO notification_outbox (url, payload, status, attempts,"
            " next_attempt_at, created_at) VALUES (?, ?, 'pending', 0, ?, ?)",
            (url, json.dumps(payload, default=str), time.time(), time.time()))
        return int(cur.lastrowid)


def deliver(row_id: int) -> bool:
    """Attempt delivery of one row.  Returns True when delivered."""
    with _conn() as conn:
        row = conn.execute("SELECT * FROM notification_outbox WHERE id = ?",
                           (row_id,)).fetchone()
    if row is None or row['status'] == 'delivered':
        return row is not None

    import requests
    error = None
    try:
        resp = requests.post(row['url'], json=json.loads(row['payload']),
                             timeout=DELIVER_TIMEOUT)
        if resp.status_code >= 400:
            error = 'HTTP %s' % resp.status_code
    except Exception as exc:  # noqa: BLE001 -- a broken webhook must not raise
        error = '%s: %s' % (type(exc).__name__, exc)

    attempts = int(row['attempts']) + 1
    with _conn() as conn:
        if error is None:
            conn.execute(
                "UPDATE notification_outbox SET status='delivered', attempts=?,"
                " delivered_at=?, last_error=NULL WHERE id = ?",
                (attempts, time.time(), row_id))
            return True
        if attempts >= MAX_ATTEMPTS:
            conn.execute(
                "UPDATE notification_outbox SET status='failed', attempts=?,"
                " last_error=? WHERE id = ?", (attempts, error, row_id))
            return False
        delay = BACKOFF[min(attempts - 1, len(BACKOFF) - 1)]
        conn.execute(
            "UPDATE notification_outbox SET status='pending', attempts=?,"
            " next_attempt_at=?, last_error=? WHERE id = ?",
            (attempts, time.time() + delay, error, row_id))
        return False


def retry(row_id: int) -> bool:
    """Force a row back to ``pending`` now (clears a terminal failure)."""
    with _conn() as conn:
        cur = conn.execute(
            "UPDATE notification_outbox SET status='pending', attempts=0,"
            " next_attempt_at=?, last_error=NULL WHERE id = ? AND status != 'delivered'",
            (time.time(), row_id))
        return cur.rowcount > 0


def replay_failed() -> int:
    """Re-queue everything not delivered.  Returns the number touched."""
    with _conn() as conn:
        cur = conn.execute(
            "UPDATE notification_outbox SET status='pending', attempts=0,"
            " next_attempt_at=? WHERE status != 'delivered'", (time.time(),))
        return cur.rowcount


def purge_delivered() -> int:
    with _conn() as conn:
        cur = conn.execute("DELETE FROM notification_outbox WHERE status='delivered'")
        return cur.rowcount


# --- reads -------------------------------------------------------------------

def due(limit: int = 20) -> List[Dict[str, Any]]:
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM notification_outbox WHERE status='pending'"
            " AND next_attempt_at <= ? ORDER BY next_attempt_at LIMIT ?",
            (time.time(), limit)).fetchall()
    return [_as_dict(r) for r in rows]


def list_rows(limit: int = 100, status: Optional[str] = None) -> List[Dict[str, Any]]:
    q = "SELECT * FROM notification_outbox"
    args: tuple = ()
    if status:
        q += " WHERE status = ?"
        args = (status,)
    q += " ORDER BY id DESC LIMIT ?"
    with _conn() as conn:
        rows = conn.execute(q, args + (limit,)).fetchall()
    return [_as_dict(r) for r in rows]


def stats() -> Dict[str, int]:
    with _conn() as conn:
        rows = conn.execute(
            "SELECT status, COUNT(*) c FROM notification_outbox GROUP BY status").fetchall()
    out = {'pending': 0, 'delivered': 0, 'failed': 0}
    for r in rows:
        out[r['status']] = int(r['c'])
    return out


def _as_dict(row) -> Dict[str, Any]:
    d = dict(row)
    try:
        d['payload'] = json.loads(d.get('payload') or '{}')
    except Exception:
        pass
    return d


def deliver_due() -> int:
    """One sweep.  Returns how many deliveries succeeded."""
    return sum(1 for row in due() if deliver(row['id']))


# --- worker ------------------------------------------------------------------

def _run() -> None:
    while not _stop.wait(POLL_INTERVAL):
        try:
            deliver_due()
        except Exception:  # noqa: BLE001 -- never let the worker die
            pass


def start() -> None:
    """Start the retry worker (idempotent)."""
    global _thread
    with _lock:
        if _thread is not None and _thread.is_alive():
            return
        _stop.clear()
        _thread = threading.Thread(target=_run, name='storm-outbox', daemon=True)
        _thread.start()


def stop(wait: bool = False) -> None:
    global _thread
    _stop.set()
    t = _thread
    if wait and t is not None and t is not threading.current_thread():
        t.join(timeout=3)
    _thread = None


def running() -> bool:
    return _thread is not None and _thread.is_alive()


__all__ = ["record", "deliver", "retry", "replay_failed", "purge_delivered",
           "due", "list_rows", "stats", "deliver_due", "start", "stop", "running",
           "MAX_ATTEMPTS"]
