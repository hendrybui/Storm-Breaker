"""Tests for the playbook execute+verify engine (P14.10) -- real effects."""
import socket

from app.exec import playbook


def _listener():
    srv = socket.socket()
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", 0))
    srv.listen(1)
    return srv, srv.getsockname()[1]


def test_handles_only_engine_actions():
    assert playbook.handles("exec") and playbook.handles("verify")
    assert not playbook.handles("generate_payload")


def test_variable_substitution():
    assert playbook.substitute("hi {{name}}", {"name": "bob"}) == "hi bob"


def test_exec_success_is_verified():
    out = playbook.run_step({"action": "exec", "params": {"cmd": "echo PLAYBOOK_OK"}},
                            playbook.new_context())
    assert out["status"] == "success" and out["verified"] is True


def test_exec_nonzero_exit_is_error():
    out = playbook.run_step({"action": "exec", "params": {"cmd": "exit 3"}},
                            playbook.new_context())
    assert out["status"] == "error" and out["verified"] is False


def test_exec_expect_exit_matches():
    out = playbook.run_step({"action": "exec", "params": {"cmd": "exit 3", "expect_exit": 3}},
                            playbook.new_context())
    assert out["status"] == "success"


def test_verify_tcp_against_real_port():
    srv, port = _listener()
    try:
        opencheck = playbook.run_step(
            {"action": "verify", "params": {"kind": "tcp", "host": "127.0.0.1", "port": port}},
            playbook.new_context())
        assert opencheck["status"] == "success" and opencheck["verified"] is True
    finally:
        srv.close()
    closedcheck = playbook.run_step(
        {"action": "verify", "params": {"kind": "tcp", "host": "127.0.0.1", "port": port}},
        playbook.new_context())
    assert closedcheck["status"] == "error"


def test_checkpoint_rollback_restores_variables():
    ctx = playbook.new_context({"x": "1"})
    playbook.run_step({"action": "checkpoint", "params": {"name": "cp"}}, ctx)
    ctx.variables["x"] = "2"
    rb = playbook.rollback(ctx)
    assert rb["to"] == "cp" and ctx.variables["x"] == "1"


def test_run_playbook_rolls_back_on_failure():
    run = playbook.run_playbook([
        {"action": "checkpoint", "params": {"name": "cp"}},
        {"action": "exec", "params": {"cmd": "exit 5"}, "on_fail": "rollback"},
    ])
    assert run["ok"] is False
    assert run["rolled_back_to"] == "cp"
    assert run["results"][-1]["rollback"]["to"] == "cp"


def test_run_playbook_stops_by_default():
    run = playbook.run_playbook([
        {"action": "exec", "params": {"cmd": "exit 5"}},
        {"action": "log", "params": {"message": "not reached"}},
    ])
    assert len(run["results"]) == 1


def test_run_playbook_continue_on_failure():
    run = playbook.run_playbook([
        {"action": "exec", "params": {"cmd": "exit 5"}, "on_fail": "continue"},
        {"action": "log", "params": {"message": "still here"}},
    ])
    assert run["ok"] is False and len(run["results"]) == 2
