"""P1 freeze operator GET routes (NR-2).

Each route must answer under a valid operator session with its
status/content-type/JSON shape unchanged. Re-baseline via:

    pytest tests/char/test_operator_get.py --update-snapshots
"""
from __future__ import annotations

import pytest
import requests

from ._catalog import OPERATOR_GETS
from ._helpers import compare_or_update, shape_snapshot


@pytest.mark.parametrize("path", OPERATOR_GETS)
@pytest.mark.char
def test_operator_get_shape(live_server: str, admin_session: requests.Session,
                            path: str, request: pytest.FixtureRequest) -> None:
    resp = admin_session.get(f"{live_server}{path}", timeout=20)
    snap = shape_snapshot(resp)
    ok, msg = compare_or_update(
        group="operator_get",
        key=f"GET {path}",
        snap=snap,
        update=request.config.getoption("--update-snapshots"),
    )
    if ok and "first run baseline" in msg:
        pytest.skip(msg)
    assert ok, msg
