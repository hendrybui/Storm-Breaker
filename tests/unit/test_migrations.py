"""Unit tests for ``app.core.migrations`` (P5.5/P5.6).

Runs only against throwaway sqlite files under ``tmp_path`` — the live
operator DB at ``storm-web/storm_breaker.db`` is never touched here.
"""
import sqlite3

from app.core.migrations.runner import INDEXES, migrate


def _tables(db):
    conn = sqlite3.connect(db)
    try:
        return {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
    finally:
        conn.close()


def _indexes(db):
    conn = sqlite3.connect(db)
    try:
        return {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index'")}
    finally:
        conn.close()


def test_migrate_on_fresh_db(tmp_path):
    db = str(tmp_path / 'fresh.db')
    info = migrate(db)
    tables = _tables(db)
    assert {'mobile_commands', 'mobile_responses', 'c2_sessions',
            'mobile_sessions', 'tracking_data', 'mobile_captures',
            'credentials', 'rat_persistence'} <= tables
    idx = _indexes(db)
    for name in ('idx_mobile_commands_uid_executed',
                 'idx_credentials_cred_type',
                 'idx_c2_sessions_ip'):
        assert name in idx
    conn = sqlite3.connect(db)
    try:
        mode = conn.execute('PRAGMA journal_mode').fetchone()[0]
    finally:
        conn.close()
    assert str(mode).lower() == 'wal'
    assert info['pragmas']
    assert len(info['indexes']) == len(INDEXES)
    assert info['schema_version'] == 1


def test_migrate_is_idempotent(tmp_path):
    db = str(tmp_path / 'idem.db')
    first = migrate(db)
    second = migrate(db)
    assert first['indexes'] == second['indexes']


def test_migrate_preserves_existing_rows(tmp_path):
    db = str(tmp_path / 'data.db')
    migrate(db)
    conn = sqlite3.connect(db)
    conn.execute("INSERT INTO credentials (cred_type, value) "
                 "VALUES ('wifi', 'secret')")
    conn.commit()
    conn.close()

    migrate(db)  # re-run must not touch data

    conn = sqlite3.connect(db)
    try:
        n = conn.execute('SELECT COUNT(*) FROM credentials').fetchone()[0]
    finally:
        conn.close()
    assert n == 1
