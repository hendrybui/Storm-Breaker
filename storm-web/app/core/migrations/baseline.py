"""Baseline migration (P5.5).

The baseline schema of Storm-Breaker is whatever ``database.init_database()``
creates (24 tables).  This module records that fact and re-applies it
idempotently -- ``init_database`` only ever issues ``CREATE TABLE IF NOT
EXISTS``, so running it against an existing database is a no-op.

Rollback: restore ``backups/storm_breaker.db.*`` (taken at G0).
"""
from __future__ import annotations

import sys as _sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_STORM_WEB = str(_HERE.parents[2])
if _STORM_WEB not in _sys.path:
    _sys.path.insert(0, _STORM_WEB)

import database as _database  # noqa: E402

SCHEMA_VERSION = 1


def ensure_baseline(db_path=None) -> None:
    """Idempotently ensure the 24 baseline tables exist.

    ``database.init_database`` only issues ``CREATE TABLE IF NOT EXISTS``
    statements, so this never alters an existing schema.  When a specific
    ``db_path`` is given (tests / dry runs), the module-level ``DB_PATH``
    is swapped temporarily -- identical DDL, different target file.
    """
    if db_path is None:
        _database.init_database()
        return
    orig = _database.DB_PATH
    _database.DB_PATH = db_path
    try:
        _database.init_database()
    finally:
        _database.DB_PATH = orig

