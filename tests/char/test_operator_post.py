"""P1 freeze operator POST routes (NR-2)."""
from __future__ import annotations

import pytest
import requests

from ._catalog import OPERATOR_POSTS
from ._helpers import compare_or_update, shape_snapshot


@pytest.mark.parametrize("path, payload", OPERATOR_POSTS)
@pytest.mark.char
def test_operator_post_shape(live_server: str, admin_session: requests.Session,
                             path: str, payload: dict,
                             request: pytest.FixtureRequest) -> None:
    resp = admin_session.post(f"{live_server}{path}", json=payload, timeout=45)
    snap = shape_snapshot(resp)
    ok, msg = compare_or_update(
        group="operator_post",
        key=f"POST {path}",
        snap=snap,
        update=request.config.getoption("--update-snapshots"),
    )
    if ok and "first run baseline" in msg:
        pytest.skip(msg)
    assert ok, msg
