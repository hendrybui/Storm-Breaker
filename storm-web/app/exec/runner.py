"""Execution layer -- make actions actually RUN (FIREPOWER plan section P14.1).

The 15 feature modules largely *generate* scripts / commands / configs; almost
nothing ran them.  :func:`run` executes a command or a generated payload,
captures the **effect** (exit code, stdout, stderr, wall time) and never
raises -- a failure is data, not an exception.

Design notes:
- stdlib only (``subprocess``); no new runtime dependency (NR-8 spirit).
- ``shell`` defaults to True for a string command, False for an argv list, so
  a generator's shell one-liner runs while an argv list keeps metachars literal.
- Pure result object (:class:`ExecResult`) so callers -- including the P6 job
  worker -- can assert on the *effect*.  Long actions should be enqueued via
  ``app.core.jobs``; this module stays synchronous on purpose.
"""
from __future__ import annotations

import subprocess
import time
from dataclasses import asdict, dataclass, field
from typing import List, Mapping, Optional, Sequence, Union

DEFAULT_TIMEOUT = 30.0

Command = Union[str, Sequence[str]]


@dataclass
class ExecResult:
    """The observable effect of one execution."""

    cmd: str
    exit_code: int
    stdout: str
    stderr: str
    duration: float
    timed_out: bool
    ok: bool
    error: Optional[str] = None
    started_at: float = field(default_factory=time.time)

    def as_dict(self) -> dict:
        return asdict(self)


def _render(cmd: Command) -> str:
    return cmd if isinstance(cmd, str) else " ".join(cmd)


def _decode(blob) -> str:
    if blob is None:
        return ""
    if isinstance(blob, (bytes, bytearray)):
        return blob.decode("utf-8", errors="replace")
    return str(blob)


def run(cmd: Command, *, shell: Optional[bool] = None, cwd: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT, env: Optional[Mapping[str, str]] = None,
        stdin_text: Optional[str] = None, start_new_session: bool = False) -> ExecResult:
    """Execute ``cmd`` and return its :class:`ExecResult`.  Never raises."""
    if shell is None:
        shell = isinstance(cmd, str)
    started = time.time()
    kwargs = dict(
        shell=shell,
        cwd=cwd,
        timeout=timeout,
        env=dict(env) if env is not None else None,
        stdin=subprocess.PIPE if stdin_text is not None else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=start_new_session,
    )
    try:
        proc = subprocess.run(
            cmd, **kwargs,
            input=stdin_text.encode() if stdin_text is not None else None,
        )
    except subprocess.TimeoutExpired as exc:
        return ExecResult(_render(cmd), -1, _decode(exc.stdout), _decode(exc.stderr),
                          time.time() - started, True, False,
                          error="timeout after %.1fs" % timeout, started_at=started)
    except FileNotFoundError as exc:
        return ExecResult(_render(cmd), -1, "", str(exc), time.time() - started,
                          False, False, error="not found: %s" % _render(cmd),
                          started_at=started)
    except OSError as exc:
        return ExecResult(_render(cmd), -1, "", str(exc), time.time() - started,
                          False, False, error=str(exc), started_at=started)
    return ExecResult(_render(cmd), proc.returncode, _decode(proc.stdout),
                      _decode(proc.stderr), time.time() - started, False,
                      proc.returncode == 0, started_at=started)
