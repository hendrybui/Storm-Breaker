"""Persistent login brute-force lockout (HANDOFF plan section P7.3).

The legacy in-memory ``LOGIN_FAILS`` dict died with the process — a
restart cleared every brute-force lock.  This module keeps the exact
same (fails, until) semantics but persists them in the operator DB
(table ``login_lockouts``, added additively by the P7.3 migration).

Connection-per-call, matching the frozen ``database.py`` pattern.
Every function is failure-tolerant: an unwritable DB degrades to the
legacy in-memory-equivalent behavior (``get`` → ``None``) instead of
blocking logins.
"""
from __future__ import annotations

import sqlite3
import sys as _sys
from pathlib import Path
from typing import Optional, Tuple

_HERE = Path(__file__).resolve().parent
_STORM_WEB = str(_HERE.parents[2])
if _STORM_WEB not in _sys.path:
    _sys.path.insert(0, _STORM_WEB)

import database as _database  # noqa: E402

DB_PATH = _database.DB_PATH

_DDL = '''CREATE TABLE IF NOT EXISTS login_lockouts (
    ip TEXT PRIMARY KEY,
    fails INTEGER NOT NULL DEFAULT 0,
    until REAL NOT NULL DEFAULT 0
)'''


def _conn(db_path: Optional[str]) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path or DB_PATH)
    conn.execute(_DDL)
    return conn


def get(ip: str, db_path: Optional[str] = None) -> Optional[Tuple[int, float]]:
    """Return ``(fails, until_epoch)`` for ``ip`` or ``None``."""
    try:
        conn = _conn(db_path)
        try:
            row = conn.execute(
                'SELECT fails, until FROM login_lockouts WHERE ip = ?',
                (ip,)).fetchone()
            conn.commit()
        finally:
            conn.close()
        return (row[0], row[1]) if row else None
    except Exception:
        return None


def set(ip: str, fails: int, until: float,
        db_path: Optional[str] = None) -> None:
    """Upsert the lockout record for ``ip`` (silent on failure)."""
    try:
        conn = _conn(db_path)
        try:
            conn.execute(
                'INSERT INTO login_lockouts (ip, fails, until) '
                'VALUES (?, ?, ?) ON CONFLICT(ip) DO UPDATE SET '
                'fails = excluded.fails, until = excluded.until',
                (ip, int(fails), float(until)))
            conn.commit()
        finally:
            conn.close()
    except Exception:
        pass


def pop(ip: str, db_path: Optional[str] = None) -> None:
    """Clear the lockout record for ``ip`` (idempotent, silent on failure)."""
    try:
        conn = _conn(db_path)
        try:
            conn.execute('DELETE FROM login_lockouts WHERE ip = ?', (ip,))
            conn.commit()
        finally:
            conn.close()
    except Exception:
        pass


__all__ = ["get", "set", "pop", "DB_PATH"]
