"""Effect-asserting tests for ``app.exec.runner`` (P14.1).

Each test asserts the *effect* of a real execution -- exit code, captured
stream, elapsed time -- not a generated string.  That is the toy-vs-weapon
line from ``docs/FIREPOWER.md``.
"""
import time

from app.exec.runner import ExecResult, run


def test_runs_and_captures_stdout():
    r = run("printf hello")
    assert isinstance(r, ExecResult)
    assert r.ok is True
    assert r.exit_code == 0
    assert r.stdout == "hello"
    assert r.timed_out is False


def test_nonzero_exit_is_data_not_exception():
    r = run(["sh", "-c", "exit 3"])
    assert r.ok is False
    assert r.exit_code == 3
    assert r.error is None


def test_stderr_is_captured():
    r = run("echo boom >&2")
    assert "boom" in r.stderr


def test_timeout_is_enforced():
    t0 = time.time()
    r = run(["sleep", "5"], timeout=0.5)  # argv form: no lingering grandchild
    assert r.timed_out is True
    assert r.ok is False
    assert "timeout" in (r.error or "")
    assert time.time() - t0 < 3


def test_missing_binary_reports_error_not_raise():
    r = run(["definitely_not_a_real_binary_xyz"])
    assert r.ok is False
    assert r.error
    assert r.exit_code == -1


def test_cwd_is_honoured(tmp_path):
    r = run(["pwd"], cwd=str(tmp_path))
    assert r.ok is True
    assert str(tmp_path) in r.stdout


def test_argv_keeps_metachars_literal():
    # shell=False for argv, so ';' is not interpreted
    r = run(["printf", "a;b"])
    assert r.stdout == "a;b"


def test_as_dict_is_serialisable():
    d = run("true").as_dict()
    assert d["exit_code"] == 0
    assert set(d) >= {"cmd", "stdout", "stderr", "ok", "timed_out"}
