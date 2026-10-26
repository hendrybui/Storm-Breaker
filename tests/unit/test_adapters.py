"""Tests for the module adapter registry (P14.4).

Asserts coverage (all 15 frozen modules reachable), registry integrity, and
one *real effect*: a generated payload that must compile as valid Python.
"""
import json

import pytest

from app.adapters import (Action, actions_for, call, describe, get, modules,
                          names, register)

EXPECTED_MODULES = {
    "payload_generator", "obfuscation_engine", "rat_controller", "report_generator",
    "lure_generator", "threat_intel", "deep_recon", "ai_threat_analyzer",
    "zeroday_lab", "quantum_crypto", "session_hijacker", "pivot_engine",
    "evasion_framework", "credential_parser", "telegram_bot",
}


def test_all_15_frozen_modules_are_covered():
    assert EXPECTED_MODULES <= set(modules())


def test_registry_has_no_duplicate_names():
    assert len(names()) == len(set(names()))


def test_describe_is_json_serialisable():
    payload = json.dumps(describe())  # would raise on a callable leaking through
    assert payload.count('"name"') == len(names())


def test_get_returns_action_with_metadata():
    a = get("payloads.generate")
    assert isinstance(a, Action)
    assert a.module == "payload_generator"
    assert a.kind == "generate"
    assert a.spec()["name"] == "payloads.generate"


def test_unknown_action_raises_keyerror():
    with pytest.raises(KeyError):
        get("does.not.exist")


def test_actions_for_filters_by_module():
    for a in actions_for("rat_controller"):
        assert a.module == "rat_controller"
    assert actions_for("no_such_module") == []


def test_register_rejects_bad_kind_and_duplicate():
    with pytest.raises(ValueError):
        register("x.badkind", "m", "nope", "s", lambda: None)
    with pytest.raises(ValueError):
        register("payloads.generate", "payload_generator", "generate", "dup", lambda: None)


def test_kinds_are_labelled():
    allowed = {"generate", "analyze", "execute", "notify"}
    assert {get(n).kind for n in names()} <= allowed


def test_effect_generated_python_payload_is_valid_python():
    """Real effect: the artifact the adapter emits must actually be code."""
    res = call("payloads.generate", "python_reverse", {"lhost": "127.0.0.1", "lport": "4444"})
    assert isinstance(res, dict) and res.get("code")
    compile(res["code"], "<payload>", "exec")  # raises if the payload is not valid Python

    oneliner = res["oneliner"]
    assert "socket" in oneliner


def test_call_convenience_matches_action_call():
    assert call("quantum.algorithms") == get("quantum.algorithms").call()
