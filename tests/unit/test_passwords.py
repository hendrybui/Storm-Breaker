"""Unit tests for ``app.core.passwords`` (P7.1 — hashed operator password)."""
import pytest

from app.core.passwords import (
    check_operator_login,
    hash_password,
    verify_password,
)


def test_hash_verify_roundtrip():
    encoded = hash_password('s3cret!')
    assert encoded.startswith('pbkdf2_sha256$')
    assert verify_password('s3cret!', encoded)
    assert not verify_password('wrong', encoded)


def test_hash_is_salted_unique():
    assert hash_password('same') != hash_password('same')


def test_verify_rejects_garbage_encoded():
    assert not verify_password('x', 'not-a-valid-encoded-string')
    assert not verify_password('x', '')
    assert not verify_password('x', 'pbkdf2_sha256$abc$zz$zz')


def test_fallback_to_plaintext_when_no_hash():
    config_users = {'admin': {'password': 'plainpass'}}
    assert check_operator_login('admin', 'plainpass', config_users, hash_store={})
    assert not check_operator_login('admin', 'nope', config_users, hash_store={})
    assert not check_operator_login('ghost', 'x', config_users, hash_store={})


def test_hash_wins_over_plaintext():
    config_users = {'admin': {'password': 'old-plain'}}  # stale plaintext
    store = {'admin': hash_password('new-pass')}
    assert check_operator_login('admin', 'new-pass', config_users, hash_store=store)
    # legacy plaintext no longer accepted once a hash exists
    assert not check_operator_login('admin', 'old-plain', config_users, hash_store=store)


def test_unknown_user_rejected():
    assert not check_operator_login('nobody', 'x', {}, hash_store={})
