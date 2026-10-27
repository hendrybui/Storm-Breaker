"""Additive target-model tables (FIREPOWER plan section P14.3).

New tables only -- the 24-table baseline and every stored row are untouched
(NR-4). ``targets`` is the operator's persistent aim; ``target_findings`` is
the evidence trail attached to a target (a strike result, a scan, a note).
"""
from __future__ import annotations

import sqlite3
from typing import List

TABLES = [
    """CREATE TABLE IF NOT EXISTS targets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        host TEXT,
        notes TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS target_findings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        target_id INTEGER NOT NULL,
        kind TEXT NOT NULL,
        detail TEXT,
        evidence TEXT,
        created_at TEXT NOT NULL
    )""",
]

INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_target_findings_target "
    "ON target_findings(target_id)",
    "CREATE INDEX IF NOT EXISTS idx_targets_host ON targets(host)",
]


def ensure_targets(conn: sqlite3.Connection) -> List[str]:
    """Create the target tables/indexes if absent; return their names."""
    created: List[str] = []
    for ddl in TABLES + INDEXES:
        conn.execute(ddl)
        created.append(ddl.split("IF NOT EXISTS ", 1)[1].split(" ", 1)[0])
    return created
