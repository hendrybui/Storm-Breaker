"""
Characterization-test fixtures.

Two session-scoped fixtures drive the entire suite:

  live_server   - spawns `python3 storm-web/app.py` on :2525 once, polls
                  /login.php until it responds, then yields the base URL.
                  Teardown is SIGTERM (then SIGKILL after 5 s).

  admin_session - a requests.Session that has POSTed /login with the
                  admin credentials parsed out of storm-web/config.php
                  (same source the running Flask process uses).

Plus a session-scoped fixture that imports the Flask app in-process so the
route-inventory test can introspect the live URL map.
"""
from __future__ import annotations

import json
import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Iterator

import pytest
import requests


REPO = Path(__file__).resolve().parents[1]  # tests/ -> repo root
STORM_WEB = REPO / "storm-web"
BASE_URL = "http://127.0.0.1:2525"
SERVER_LOG = REPO / "tests" / "_server.log"
FROZEN_DIR = REPO / "tests" / "_frozen"
LOCKOUT_STATUS = 429
LOGIN_OK = {200, 302}


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--update-snapshots",
        action="store_true",
        default=False,
        help="rewrite tests/_frozen/*.json with current response shape",
    )


def pytest_configure(config: pytest.Config) -> None:
    FROZEN_DIR.mkdir(parents=True, exist_ok=True)
    config.addinivalue_line("markers", "char: characterization tests")
    config.addinivalue_line("markers", "snapshot_manage: capture / refresh snapshots")


# ---------------------------------------------------------------------------
# Live-server fixture
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def live_server() -> Iterator[str]:
    """Spawn the backend once for the whole suite, yield BASE_URL, terminate."""
    env = os.environ.copy()
    env.setdefault("PYTHONUNBUFFERED", "1")
    log_fh = open(SERVER_LOG, "wb")
    proc = subprocess.Popen(
        [sys.executable, "app.py"],
        cwd=str(STORM_WEB),
        stdout=log_fh,
        stderr=subprocess.STDOUT,
        env=env,
        preexec_fn=os.setsid,
    )
    deadline = time.time() + 60
    while time.time() < deadline:
        try:
            r = requests.get(f"{BASE_URL}/login.php", timeout=1,
                             allow_redirects=False)
            if r.status_code < 500:
                break
        except requests.RequestException:
            pass
        time.sleep(0.3)
    else:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        raise RuntimeError(f"server failed to come up; see {SERVER_LOG}")
    try:
        yield BASE_URL
    finally:
        try:
            os.killpg(proc.pid, signal.SIGTERM)
            proc.wait(timeout=5)
        except (subprocess.TimeoutExpired, ProcessLookupError):
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        log_fh.close()


# ---------------------------------------------------------------------------
# Admin login fixture
# ---------------------------------------------------------------------------

def _read_admin_password() -> str:
    cfg = (STORM_WEB / "config.php").read_text(encoding="utf-8")
    m = re.search(r'"password"\s*=>\s*"([^"]+)"', cfg)
    assert m, "could not parse admin password out of storm-web/config.php"
    return m.group(1)


@pytest.fixture(scope="session")
def admin_session(live_server: str) -> Iterator[requests.Session]:
    """Log in once, tolerate the in-memory 60 s brute-force lockout window.

    Flask stores the ``IAm-logined`` value inside the encrypted ``session``
    cookie, so the fixture success criterion is "POST /login returns 200 or
    302" (302 = redirect to /panel), matching audit/audit_storm_breaker.py.
    """
    password = _read_admin_password()
    s = requests.Session()

    for attempt in range(3):
        r = s.post(
            f"{live_server}/login",
            data={"username": "admin", "password": password},
            allow_redirects=False,
            timeout=5,
        )
        if r.status_code in LOGIN_OK:
            break
        if r.status_code == LOCKOUT_STATUS:
            time.sleep(61)
            continue
        raise RuntimeError(
            f"login failed: status={r.status_code} body={r.text[:200]!r}"
        )
    yield s


# ---------------------------------------------------------------------------
# In-process app import for static introspection
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def storm_app(live_server: str):
    """Import the live Flask *instance* so route-inventory can walk url_map.

    P2 introduced a sibling ``storm-web/app`` package alongside the file
    ``storm-web/app.py``; Python's finder picks the package for the bare
    name ``app``. To still trigger route-registration on the Flask
    instance the file ``storm-web/app.py`` builds, we load it directly
    via ``importlib.util`` (bypassing the package-name shadowing). The
    file's ``import database`` etc. rely on ``storm-web/`` being on
    ``sys.path``, so we stage it for the duration of the exec.
    """
    import importlib.util
    sys.path.insert(0, str(STORM_WEB))
    try:
        spec = importlib.util.spec_from_file_location(
            "storm_web_app_file", str(STORM_WEB / "app.py")
        )
        if spec is None or spec.loader is None:
            raise RuntimeError(f"could not load storm-web/app.py as a module spec")
        _module = importlib.util.module_from_spec(spec)
        sys.modules["storm_web_app_file"] = _module
        spec.loader.exec_module(_module)  # runs app.py -> registers 204 routes
        return _module.app
    finally:
        try:
            sys.path.remove(str(STORM_WEB))
        except ValueError:
            pass
