"""Operator password hardening (HANDOFF plan section P7.1).

Legacy behavior (frozen): ``auth.py`` compares the submitted password
against the plaintext in ``config.php`` (``app.state.CONFIG``).

Hardened behavior (additive): if a per-user PBKDF2 hash exists in
``storm-web/operator_auth.json`` (gitignored), the hash wins and the
legacy plaintext is no longer accepted for that user.  Users without a
hash keep the legacy plaintext path, so existing deployments and the
audit harness keep working unchanged.

Encoded format: ``pbkdf2_sha256$<iterations>$<salt_hex>$<hash_hex>``
(hashlib.pbkdf2_hmac; stdlib only, no new dependencies).

Create/rotate a hash:
    python3 storm-web/set_password_hash.py <username>
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
from pathlib import Path
from typing import Dict, Optional

# storm-web/operator_auth.json (next to config.php)
AUTH_STORE_PATH = str(Path(__file__).resolve().parents[2] / 'operator_auth.json')

_ITERATIONS = 600_000


def hash_password(password: str, iterations: int = _ITERATIONS) -> str:
    """Encode ``password`` as ``pbkdf2_sha256$<iter>$<salt>$<hash>``."""
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        'sha256', password.encode('utf-8'), bytes.fromhex(salt), iterations)
    return 'pbkdf2_sha256$%d$%s$%s' % (iterations, salt, digest.hex())


def verify_password(password: str, encoded: str) -> bool:
    """Constant-time verification of ``password`` against ``encoded``.

    Malformed encodings verify to ``False`` (never raise).
    """
    try:
        algo, iterations, salt_hex, hash_hex = encoded.split('$', 3)
        if algo != 'pbkdf2_sha256':
            return False
        digest = hashlib.pbkdf2_hmac(
            'sha256', password.encode('utf-8'),
            bytes.fromhex(salt_hex), int(iterations))
        return hmac.compare_digest(digest.hex(), hash_hex)
    except Exception:
        return False


def load_hash_store(path: str = AUTH_STORE_PATH) -> Dict[str, str]:
    """Load ``{username: encoded}`` (``{}`` when missing/corrupt)."""
    try:
        with open(path, 'r', encoding='utf-8') as fh:
            data = json.load(fh)
        return {str(k): str(v) for k, v in data.items()}
    except Exception:
        return {}


def save_hash_store(store: Dict[str, str],
                    path: str = AUTH_STORE_PATH) -> None:
    """Persist the hash store with 0600 permissions."""
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as fh:
        json.dump(store, fh, indent=2)
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)


def set_password_hash(username: str, password: str,
                      path: str = AUTH_STORE_PATH) -> str:
    """Create/rotate one user's hash.  Returns the encoded string."""
    store = load_hash_store(path)
    encoded = hash_password(password)
    store[username] = encoded
    save_hash_store(store, path)
    return encoded


def check_operator_login(username: str, password: str,
                         config_users: Dict[str, Dict[str, str]],
                         hash_store: Optional[Dict[str, str]] = None,
                         path: str = AUTH_STORE_PATH) -> bool:
    """Verify an operator login attempt.

    Order: per-user hash (if present) wins; otherwise fall back to the
    legacy plaintext comparison against ``config_users`` — so the audit
    harness and existing deployments behave exactly as before.
    """
    store = load_hash_store(path) if hash_store is None else hash_store
    encoded = store.get(username)
    if encoded is not None:
        return verify_password(password, encoded)
    user = config_users.get(username)
    if user is None:
        return False
    return hmac.compare_digest(str(user.get('password', '')),
                               str(password or ''))


__all__ = [
    "AUTH_STORE_PATH", "hash_password", "verify_password",
    "load_hash_store", "save_hash_store", "set_password_hash",
    "check_operator_login",
]
