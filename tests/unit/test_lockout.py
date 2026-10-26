"""Unit tests for ``app.core.lockout`` (P7.3 — persisted login lockout)."""
from app.core.lockout import get, pop, set


def test_get_missing_is_none(tmp_path):
    db = str(tmp_path / 'l.db')
    assert get('1.2.3.4', db_path=db) is None


def test_set_get_roundtrip(tmp_path):
    db = str(tmp_path / 'l.db')
    set('1.2.3.4', 3, 12345.0, db_path=db)
    assert get('1.2.3.4', db_path=db) == (3, 12345.0)


def test_pop_removes(tmp_path):
    db = str(tmp_path / 'l.db')
    set('1.2.3.4', 1, 0.0, db_path=db)
    pop('1.2.3.4', db_path=db)
    assert get('1.2.3.4', db_path=db) is None
    pop('1.2.3.4', db_path=db)  # idempotent


def test_state_survives_new_connections(tmp_path):
    """Persistence semantics: each call opens its own connection, so the
    record survives a restart by construction."""
    db = str(tmp_path / 'l.db')
    set('5.6.7.8', 4, 999.0, db_path=db)
    set('9.9.9.9', 1, 1.0, db_path=db)  # unrelated ip untouched
    assert get('5.6.7.8', db_path=db) == (4, 999.0)


def test_set_overwrites(tmp_path):
    db = str(tmp_path / 'l.db')
    set('1.1.1.1', 1, 0.0, db_path=db)
    set('1.1.1.1', 5, 555.0, db_path=db)
    assert get('1.1.1.1', db_path=db) == (5, 555.0)


def test_unwritable_path_never_raises(tmp_path):
    db = str(tmp_path / 'nope' / 'sub' / 'l.db')  # dir does not exist
    assert get('1.2.3.4', db_path=db) is None
    set('1.2.3.4', 1, 0.0, db_path=db)  # must not raise
    pop('1.2.3.4', db_path=db)          # must not raise
