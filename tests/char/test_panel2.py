"""P11 — the V2 panel is served and its bundle loads."""
from __future__ import annotations

import pytest
import requests


@pytest.mark.char
def test_panel2_serves_and_loads_bundle(live_server: str,
                                        admin_session: requests.Session) -> None:
    page = admin_session.get(f"{live_server}/panel2", timeout=10)
    assert page.status_code == 200
    assert 'id="root"' in page.text
    assert "ui_v2/app.js" in page.text          # url_for('static') -> /assets/...

    assert admin_session.get(f"{live_server}/assets/ui_v2/app.js",
                             timeout=10).status_code == 200
    assert admin_session.get(f"{live_server}/assets/ui_v2/app.css",
                             timeout=10).status_code == 200


@pytest.mark.char
def test_panel2_requires_login(live_server: str) -> None:
    resp = requests.get(f"{live_server}/panel2", timeout=10, allow_redirects=False)
    assert resp.status_code in (301, 302)
