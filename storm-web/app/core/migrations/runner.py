"""Schema migrations for Storm-Breaker (P5.5 / P5.6).

``runner.migrate()`` is idempotent and additive only:

1. baseline tables        (P5.5 -- via ``database.init_database``)
2. ``journal_mode=WAL``   (P5.6 -- persistent DB-file property;
                           rollback: ``PRAGMA journal_mode=DELETE;``)
3. hot-path indexes       (P5.6 -- ``CREATE INDEX IF NOT EXISTS`` only;
                           rollback: ``DROP INDEX <name>;``)

No table is altered, dropped, or reshaped -- the 24-table baseline and
every stored row remain byte-compatible.
"""
from __future__ import annotations

import sqlite3
import sys as _sys
from pathlib import Path
from typing import List

from app.core.migrations.baseline import ensure_baseline

_HERE = Path(__file__).resolve().parent
_STORM_WEB = str(_HERE.parents[2])
if _STORM_WEB not in _sys.path:
    _sys.path.insert(0, _STORM_WEB)

# Additive, idempotent indexes over columns the hot routes filter on.
# Column names are copied verbatim from ``database.init_database`` DDL.
INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_mobile_commands_uid_executed "
    "ON mobile_commands(uid, executed)",
    "CREATE INDEX IF NOT EXISTS idx_mobile_responses_uid_retrieved "
    "ON mobile_responses(uid, retrieved)",
    "CREATE INDEX IF NOT EXISTS idx_tracking_data_uid "
    "ON tracking_data(uid)",
    "CREATE INDEX IF NOT EXISTS idx_mobile_captures_uid "
    "ON mobile_captures(uid)",
    "CREATE INDEX IF NOT EXISTS idx_mobile_sessions_ip "
    "ON mobile_sessions(ip)",
    "CREATE INDEX IF NOT EXISTS idx_c2_sessions_ip "
    "ON c2_sessions(ip)",
    "CREATE INDEX IF NOT EXISTS idx_credentials_cred_type "
    "ON credentials(cred_type)",
    "CREATE INDEX IF NOT EXISTS idx_threat_intel_type "
    "ON threat_intel(intel_type)",
    "CREATE INDEX IF NOT EXISTS idx_session_hijacks_victim_ip "
    "ON session_hijacks(victim_ip)",
    "CREATE INDEX IF NOT EXISTS idx_pivot_records_type "
    "ON pivot_records(record_type)",
    "CREATE INDEX IF NOT EXISTS idx_rat_operations_type "
    "ON rat_operations(operation_type)",
    "CREATE INDEX IF NOT EXISTS idx_rat_persistence_target_os "
    "ON rat_persistence(target_os)",
]


def default_db_path() -> str:
    import database  # noqa: PLC0415 -- sibling import, path set above
    return database.DB_PATH


def apply_pragmas(conn: sqlite3.Connection) -> List[str]:
    """Enable WAL on an open connection.  Returns applied pragma names."""
    applied: List[str] = []
    mode = conn.execute("PRAGMA journal_mode=WAL").fetchone()[0]
    if str(mode).lower() == "wal":
        applied.append("journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    applied.append("synchronous=NORMAL")
    return applied


# Additive tables (P7.3): persistent login brute-force lockout.
TABLES = [
    """CREATE TABLE IF NOT EXISTS login_lockouts (
        ip TEXT PRIMARY KEY,
        fails INTEGER NOT NULL DEFAULT 0,
        until REAL NOT NULL DEFAULT 0
    )""",
]


def apply_tables(conn: sqlite3.Connection) -> List[str]:
    """Create every additive table that does not exist yet."""
    created: List[str] = []
    for ddl in TABLES:
        conn.execute(ddl)
        created.append(ddl.split("IF NOT EXISTS ", 1)[1].split(" ", 1)[0])
    return created


def apply_indexes(conn: sqlite3.Connection) -> List[str]:
    """Create every index in ``INDEXES`` that does not exist yet."""
    created: List[str] = []
    for ddl in INDEXES:
        conn.execute(ddl)
        created.append(ddl.split("IF NOT EXISTS ", 1)[1].split(" ", 1)[0])
    return created


def migrate(db_path: str = None) -> dict:
    """Bring ``db_path`` (default: the live operator DB) up to schema v1.

    Idempotent: safe to call on every server start.  Never mutates table
    definitions or row data.
    """
    target = db_path or default_db_path()
    applied: dict = {"schema_version": 1, "db_path": target,
                     "pragmas": [], "indexes": []}

    # 1) baseline tables (P5.5)
    ensure_baseline(target)

    # 2)+3) pragmas + indexes (P5.6)
    conn = sqlite3.connect(target)
    try:
        applied["pragmas"] = apply_pragmas(conn)
        applied["tables"] = apply_tables(conn)
        applied["indexes"] = apply_indexes(conn)
        conn.commit()
    finally:
        conn.close()
    return applied
