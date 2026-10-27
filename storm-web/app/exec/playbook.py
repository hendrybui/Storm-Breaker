"""Playbook execution with execute + verify + checkpoint/rollback (P14.10).

The legacy ``/api/playbooks/<id>/execute`` chain *generates* things (payloads,
reports, lures) but never ran or confirmed anything.  These actions do:

  exec        run a command, assert its exit code (``expect_exit``)
  verify      confirm an effect (tcp / connect / http / file)
  strike      generate -> launch -> verify a payload callback
  checkpoint  mark a restore point (snapshots variables)
  rollback    restore the last (or named) checkpoint
  log, delay  trivial

Integrates without touching the legacy branches: the blueprint delegates any
step whose action ``handles()`` returns True.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.exec import runner, verify
from app.exec.strike import launch_payload

ENGINE_ACTIONS = {"exec", "verify", "strike", "checkpoint", "rollback", "log", "delay"}


def handles(action: str) -> bool:
    return action in ENGINE_ACTIONS


def substitute(value: Any, variables: Dict[str, Any]) -> Any:
    if isinstance(value, str):
        for key, val in (variables or {}).items():
            value = value.replace("{{%s}}" % key, str(val))
    return value


def _sub_params(params: Any, variables: Dict[str, Any]) -> Dict[str, Any]:
    return {k: substitute(v, variables) for k, v in (params or {}).items()}


def _now() -> str:
    return datetime.now().isoformat()


@dataclass
class RunContext:
    variables: Dict[str, Any] = field(default_factory=dict)
    checkpoints: List[Dict[str, Any]] = field(default_factory=list)
    rolled_back_to: Optional[str] = None

    def snapshot(self, name: str, index: Optional[int] = None,
                 at: Optional[float] = None) -> Dict[str, Any]:
        cp = {"name": name, "index": index, "at": at or time.time(),
              "variables": dict(self.variables)}
        self.checkpoints.append(cp)
        return cp


def new_context(variables: Optional[Dict[str, Any]] = None) -> RunContext:
    return RunContext(variables=dict(variables or {}))


def rollback(ctx: RunContext, to: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Restore the named (or last) checkpoint: variables back, stack trimmed."""
    if not ctx.checkpoints:
        return None
    target = None
    if to:
        for cp in reversed(ctx.checkpoints):
            if cp["name"] == to:
                target = cp
                break
    if target is None:
        target = ctx.checkpoints[-1]
    ctx.variables = dict(target["variables"])
    ctx.checkpoints = [c for c in ctx.checkpoints if c["at"] <= target["at"]]
    ctx.rolled_back_to = target["name"]
    return {"to": target["name"], "index": target["index"]}


def run_step(step: Dict[str, Any], ctx: RunContext,
             target_id: Optional[int] = None) -> Dict[str, Any]:
    action = step.get("action", "")
    params = _sub_params(step.get("params", {}), ctx.variables)

    if action == "log":
        return {"status": "success", "output": str(params.get("message", "")),
                "verified": None}

    if action == "delay":
        secs = min(int(params.get("seconds", 1)), 30)
        time.sleep(max(0, secs))
        return {"status": "success", "output": "Delayed %ds" % secs, "verified": None}

    if action == "checkpoint":
        cp = ctx.snapshot(params.get("name") or "cp", index=step.get("_index"))
        return {"status": "success", "output": "checkpoint %s" % cp["name"],
                "verified": None, "checkpoint": cp["name"]}

    if action == "rollback":
        rb = rollback(ctx, params.get("to"))
        return {"status": "success",
                "output": ("rolled back to %s" % rb["to"]) if rb else "no checkpoint",
                "verified": None, "rollback": rb}

    if action == "exec":
        cmd = params.get("cmd") or params.get("command")
        if not cmd:
            return {"status": "error", "output": "exec: no cmd", "verified": False}
        res = runner.run(cmd, shell=isinstance(cmd, str),
                         timeout=float(params.get("timeout", 60)))
        expect = int(params.get("expect_exit", 0))
        ok = res.exit_code == expect and not res.timed_out
        detail = "exit=%s (expected %s) in %.2fs" % (res.exit_code, expect, res.duration)
        if res.stdout.strip():
            detail += " | %s" % res.stdout.strip()[:200]
        if not ok and res.stderr.strip():
            detail += " | stderr: %s" % res.stderr.strip()[:200]
        return {"status": "success" if ok else "error", "output": detail,
                "verified": ok, "exec": res.as_dict()}

    if action == "verify":
        kind = params.get("kind", "tcp")
        if kind == "tcp":
            chk = verify.tcp_open(params.get("host", "127.0.0.1"),
                                  int(params.get("port", 0)),
                                  float(params.get("timeout", 2.0)))
        elif kind == "connect":
            chk = verify.wait_for_connect(params.get("host", "127.0.0.1"),
                                          int(params.get("port", 0)),
                                          float(params.get("timeout", 10.0)))
        elif kind == "http":
            chk = verify.http_probe(params.get("url", ""),
                                    timeout=float(params.get("timeout", 5.0)))
        elif kind == "file":
            chk = verify.file_exists(params.get("path", ""),
                                     int(params.get("min_bytes", 0)))
        else:
            return {"status": "error", "output": "verify: bad kind %r" % kind,
                    "verified": False}
        return {"status": "success" if chk.ok else "error", "output": chk.detail,
                "verified": chk.ok}

    if action == "strike":
        strike = launch_payload(params.get("payload_type", "python_reverse"),
                                params.get("lhost", "127.0.0.1"),
                                int(params.get("lport", 0)))
        if target_id is not None:
            try:
                from app.targets import TargetStore
                store = TargetStore()
                store.add_finding(int(target_id), "playbook-strike", strike.summary(),
                                  evidence={"verified": strike.callback.ok})
            except Exception:  # noqa: BLE001 -- evidence must not fail the run
                pass
        return {"status": "success" if strike.ok else "error",
                "output": strike.summary(), "verified": strike.callback.ok}

    return {"status": "skipped", "output": "not an engine action", "verified": None}


def run_playbook(steps: List[Dict[str, Any]], variables: Optional[Dict[str, Any]] = None,
                 on_fail: str = "stop",
                 target_id: Optional[int] = None) -> Dict[str, Any]:
    """Run engine steps in order.  ``on_fail``: stop | continue | rollback."""
    ctx = new_context(variables)
    results: List[Dict[str, Any]] = []
    ok = True

    for index, raw in enumerate(steps or []):
        step = dict(raw or {})
        action = step.get("action", "")
        if not handles(action):
            continue
        step["_index"] = index
        outcome = run_step(step, ctx, target_id=target_id)
        entry = {"step": index + 1, "action": action, "status": outcome["status"],
                 "output": outcome["output"], "verified": outcome.get("verified"),
                 "timestamp": _now()}
        if outcome.get("checkpoint"):
            entry["checkpoint"] = outcome["checkpoint"]

        if outcome["status"] == "error":
            ok = False
            behave = step.get("on_fail", on_fail)
            if behave == "rollback":
                entry["rollback"] = rollback(ctx, step.get("params", {}).get("to"))
            results.append(entry)
            if behave != "continue":
                break
            continue

        results.append(entry)

    return {"ok": ok, "results": results, "rolled_back_to": ctx.rolled_back_to}


__all__ = ["ENGINE_ACTIONS", "RunContext", "handles", "new_context", "rollback",
           "run_playbook", "run_step", "substitute"]
