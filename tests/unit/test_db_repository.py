"""Unit tests for ``app.core.db`` (P5.4 — Repository over frozen database.py)."""
import database
from app.core.db import Repository, get_repository, reset_repository


class FakeDB:
    """Minimal stand-in recording forwarded calls."""

    def __init__(self):
        self.calls = []

    def save_credential(self, *args, **kwargs):
        self.calls.append(('save_credential', args, kwargs))
        return 'saved!'

    def get_all_c2_sessions(self):
        return {'u1': {'ip': '9.9.9.9'}}


def test_delegation_forwards_args_and_returns():
    fake = FakeDB()
    repo = Repository(fake)
    out = repo.save_credential('wifi', 'pw', 'src', ip='1.2.3.4')
    assert out == 'saved!'
    assert fake.calls == [
        ('save_credential', ('wifi', 'pw', 'src'), {'ip': '1.2.3.4'})]
    assert repo.get_all_c2_sessions() == {'u1': {'ip': '9.9.9.9'}}


def test_default_module_is_frozen_database():
    assert Repository()._db is database


def test_covers_every_public_database_function():
    """Every public callable in database.py must have a Repository method."""
    repo = Repository()
    missing = []
    for name in dir(database):
        if name.startswith('_'):
            continue
        attr = getattr(database, name)
        if not callable(attr):
            continue
        if getattr(attr, '__module__', None) != 'database':
            continue
        if not hasattr(repo, name):
            missing.append(name)
    assert missing == [], 'Repository missing delegates: %s' % missing


def test_get_repository_singleton():
    reset_repository()
    r1 = get_repository()
    r2 = get_repository()
    assert r1 is r2
    assert isinstance(r1, Repository)
    reset_repository()
