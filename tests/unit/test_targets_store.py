"""Tests for the target model (P14.3) against a migrated temp DB."""
import pytest

from app.core.migrations.runner import migrate
from app.targets import TargetStore


@pytest.fixture()
def store(tmp_path):
    db = str(tmp_path / "targets.db")
    migrate(db)  # baseline + additive tables incl. targets/target_findings
    return TargetStore(db)


def test_create_and_get_roundtrip(store):
    t = store.create("host-a", host="10.0.0.1", notes="first")
    assert t["id"] > 0
    assert t["name"] == "host-a"
    got = store.get(t["id"])
    assert got["host"] == "10.0.0.1"
    assert got["findings"] == []


def test_get_or_create_is_idempotent_by_host(store):
    a = store.get_or_create("10.0.0.9")
    b = store.get_or_create("10.0.0.9")
    assert a["id"] == b["id"]


def test_findings_attach_and_decode_evidence(store):
    t = store.create("host-b", host="10.0.0.2")
    f = store.add_finding(t["id"], "strike", "callback VERIFIED",
                          evidence={"exec_exit": 0, "ok": True})
    assert f["id"] > 0
    assert f["evidence"] == {"exec_exit": 0, "ok": True}
    assert len(store.get(t["id"])["findings"]) == 1


def test_add_finding_updates_target_timestamp(store):
    t = store.create("host-c")
    before = store.get(t["id"])["updated_at"]
    store.add_finding(t["id"], "scan", "port 80 open")
    after = store.get(t["id"])["updated_at"]
    assert after >= before


def test_list_and_missing(store):
    store.create("x")
    assert len(store.list()) == 1
    assert store.get(999) is None
