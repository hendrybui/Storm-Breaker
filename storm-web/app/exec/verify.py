"""Verification layer -- confirm the effect, don't assume it (P14.2).

After an action runs, something must *check* it worked: a TCP connect, an HTTP
probe, a file landing, a callback arriving.  Every check returns a
:class:`CheckResult` and never raises -- "no claim without a check".

stdlib only (``socket`` / ``urllib``).  These are the primitives the recon
executor (P14.8), the listener/callback action (P14.6) and the acceptance
demo (P14.11) build on.
"""
from __future__ import annotations

import os
import socket
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Iterable, List, Optional


@dataclass
class CheckResult:
    """The outcome of one verification check."""

    name: str
    ok: bool
    detail: str
    duration: float


def _mk(name: str, ok: bool, detail: str, started: float) -> CheckResult:
    return CheckResult(name, ok, detail, time.time() - started)


def tcp_open(host: str, port: int, timeout: float = 2.0) -> CheckResult:
    """True iff a TCP connection to ``host:port`` completes."""
    started = time.time()
    try:
        with socket.create_connection((host, int(port)), timeout=timeout):
            return _mk("tcp_open", True, "connected %s:%s" % (host, port), started)
    except OSError as exc:
        return _mk("tcp_open", False, str(exc), started)


def wait_for_connect(host: str, port: int, timeout: float = 10.0,
                     interval: float = 0.2) -> CheckResult:
    """Poll ``tcp_open`` until it succeeds or ``timeout`` elapses.

    This is how a reverse-shell action awaits the victim's callback without a
    human watching a terminal (P14.6).
    """
    started = time.time()
    deadline = started + timeout
    last = ""
    while True:
        try:
            with socket.create_connection((host, int(port)), timeout=min(interval * 2, 1.0)):
                return _mk("wait_for_connect", True,
                           "connected after %.2fs" % (time.time() - started), started)
        except OSError as exc:
            last = str(exc)
        if time.time() >= deadline:
            return _mk("wait_for_connect", False,
                       "no connect within %.1fs (%s)" % (timeout, last), started)
        time.sleep(interval)


def http_probe(url: str, expect_status: Optional[int] = None,
               timeout: float = 3.0) -> CheckResult:
    """True iff ``url`` answers with the expected (or a 2xx/3xx) status."""
    started = time.time()

    def _judge(code: int) -> bool:
        return code == expect_status if expect_status else 200 <= code < 400

    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            code = resp.status
            return _mk("http_probe", _judge(code), "HTTP %s %s" % (code, url), started)
    except urllib.error.HTTPError as exc:  # non-2xx still carries a status
        code = exc.code
        return _mk("http_probe", _judge(code), "HTTP %s %s" % (code, url), started)
    except Exception as exc:  # noqa: BLE001 - a check must never raise
        return _mk("http_probe", False, str(exc), started)


def file_exists(path: str, min_bytes: int = 0) -> CheckResult:
    """True iff ``path`` is a file of at least ``min_bytes`` bytes."""
    started = time.time()
    try:
        size = os.path.getsize(path)
        ok = os.path.isfile(path) and size >= min_bytes
        return _mk("file_exists", ok, "%s (%d bytes)" % (path, size), started)
    except OSError as exc:
        return _mk("file_exists", False, str(exc), started)


def all_ok(results: Iterable[CheckResult]) -> bool:
    """True iff every check passed (a strike is only 'verified' if all did)."""
    return all(r.ok for r in results)
