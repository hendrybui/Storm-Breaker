"""P1.4: evidence integrity — sha256 digests + HMAC-SHA256 signatures."""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "storm-web"))

from app.core.integrity import sha256_hex, sign_content, verify_content
from app.targets.report import render_html, verify_render, SIG_BEGIN


def test_sha256_known_vector():
    assert sha256_hex("abc") == ("ba7816bf8f01cfea414140de5dae2223"
                                 "b00361a396177a9cb410ff61f20015ad")


def test_sign_verify_roundtrip_and_tamper():
    sig = sign_content("evidence payload")
    assert sig["alg"] == "HMAC-SHA256"
    assert len(sig["signature"]) == 64 and len(sig["sha256"]) == 64
    assert verify_content("evidence payload", sig) is True
    assert verify_content("evidence payload!", sig) is False
    assert verify_content("", {}) is False
    forged = dict(sig, signature="0" * 64)
    assert verify_content("evidence payload", forged) is False


def test_target_report_carries_verifiable_signature():
    target = {"name": "acme", "host": "acme.local", "created_at": "t0",
              "updated_at": "t1", "findings": [
                  {"kind": "listener-connect", "detail": "d", "evidence": {"ip": "1"},
                   "created_at": "t2"}]}
    rendered = render_html(target)
    assert SIG_BEGIN in rendered
    assert verify_render(rendered) is True
    tampered = rendered.replace("acme", "other-co")
    assert verify_render(tampered) is False
    assert verify_render(rendered[: len(rendered) // 2]) is False
