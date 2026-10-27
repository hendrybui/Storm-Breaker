"""Evidence integrity (P1.4): sha256 digests + HMAC-SHA256 signatures.

Reports are deliverable artifacts. Each gets a sha256 digest and an
HMAC-SHA256 signature over its exact bytes, keyed with the server's signing
secret (Settings.json ``evidence_signing_key``, falling back to
``ingest_secret``). ``verify`` detects tampering: the HMAC cannot be
recomputed without the key, and the digest pins the exact bytes.

Stdlib only (hashlib/hmac) — no new dependencies for the PyInstaller build.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os

_HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_SETTINGS_PATH = os.path.join(_HERE, "Settings.json")

_ALG = "HMAC-SHA256"


def _secret() -> bytes:
    try:
        with open(_SETTINGS_PATH, "r", encoding="utf-8") as fh:
            settings = json.load(fh)
    except Exception:
        settings = {}
    raw = settings.get("evidence_signing_key") or settings.get("ingest_secret") or ""
    if not raw:
        raw = "storm-breaker-evidence"
    return str(raw).encode("utf-8")


def sha256_hex(content) -> str:
    data = content.encode("utf-8") if isinstance(content, str) else content
    return hashlib.sha256(data).hexdigest()


def sign_content(content: str) -> dict:
    content = content or ""
    return {
        "alg": _ALG,
        "sha256": sha256_hex(content),
        "signature": hmac.new(_secret(), content.encode("utf-8"),
                              hashlib.sha256).hexdigest(),
    }


def verify_content(content: str, integrity: dict) -> bool:
    if not integrity or integrity.get("alg") != _ALG:
        return False
    content = content or ""
    expected = hmac.new(_secret(), content.encode("utf-8"),
                        hashlib.sha256).hexdigest()
    sig_ok = hmac.compare_digest(str(integrity.get("signature") or ""), expected)
    return sig_ok and sha256_hex(content) == integrity.get("sha256")
