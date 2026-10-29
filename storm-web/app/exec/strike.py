"""Strike composition -- generate, launch, VERIFY (P14.5).

The shell between "string" and "strike".  This ties the three organs together:

    adapter (generate a payload)  ->  runner (launch it)
                                  ->  listener + verify (confirm the callback)

and returns a single :class:`Strike` whose ``ok`` is the *verified* callback,
not a promise.  Blocking payloads (a reverse shell) are run as a direct child
process (argv, no shell wrapper) so a timeout kills cleanly.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.adapters import call as call_action
from app.exec.listener import Listener
from app.exec.runner import ExecResult, run
from app.exec.verify import CheckResult

_INTERPRETER = {
    "python": ["python3", "-c"],
    "bash": ["bash", "-c"],
    "javascript": ["node", "-e"],
}


def _interpreter_for(payload_type: str):
    for prefix, argv in _INTERPRETER.items():
        if payload_type.startswith(prefix):
            return argv
    return ["python3", "-c"]


@dataclass
class Strike:
    """The verified outcome of one generate -> launch -> catch cycle."""

    payload_type: str
    target: str            # host:port the payload was aimed at (the listener)
    generated: dict        # the adapter artifact
    exec: ExecResult       # what the launch produced
    callback: CheckResult  # did the payload actually connect back?

    @property
    def ok(self) -> bool:
        """A strike is successful only if the callback was VERIFIED."""
        return self.callback.ok

    def summary(self) -> str:
        return "%s -> %s | callback=%s | exec_exit=%s%s" % (
            self.payload_type, self.target,
            "VERIFIED" if self.callback.ok else "NO CONNECTION",
            self.exec.exit_code, " (timed out)" if self.exec.timed_out else "",
        )


def launch_payload(payload_type: str = "python_reverse", lhost: str = "127.0.0.1",
                   lport: int = 0, *, timeout: float = 4.0, hold: bool = False) -> Strike:
    """Generate ``payload_type``, run it against a local listener, verify callback."""
    with Listener(lhost, lport, hold=hold) as listener:
        generated = call_action("payloads.generate", payload_type,
                                {"lhost": lhost, "lport": str(listener.port)})
        code = generated.get("code", "")
        argv = _interpreter_for(payload_type) + [code]
        # start_new_session: a blocking payload (e.g. /bin/sh -i) would
        # otherwise inherit the caller's controlling tty; run as a background
        # process group it takes SIGTTIN and *stops*, so subprocess.run's
        # waitpid never reaps it and the strike hangs.  Detaching fixes that.
        ex = run(argv, timeout=timeout, start_new_session=True)
        got = listener.wait_for_client(timeout=min(timeout, 3.0))
        callback = CheckResult("callback", got,
                               "callback %s:%d" % (lhost, listener.port)
                               if got else "no callback on %s:%d" % (lhost, listener.port),
                               0.0)
        return Strike(payload_type, "%s:%d" % (lhost, listener.port),
                      generated, ex, callback)
