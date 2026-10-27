"""P19: CSRF double-submit gate — browser-like mutating POSTs need the token."""
import re
from pathlib import Path

import requests

_CONFIG = Path(__file__).resolve().parents[2] / 'storm-web' / 'config.php'


def _admin_password() -> str:
    m = re.search(r'"password"\s*=>\s*"([^"]+)"', _CONFIG.read_text())
    assert m, 'no admin password in config.php'
    return m.group(1)


def _login(base):
    s = requests.Session()
    r = s.post(f'{base}/login',
               data={'username': 'admin', 'password': _admin_password()},
               allow_redirects=False, timeout=10)
    assert r.status_code in (200, 302), r.status_code
    return s


def test_csrf_blocks_browser_like_post_without_token(live_server):
    s = _login(live_server)
    r = s.post(f'{live_server}/api/alerts/clear', timeout=10,
               headers={'Origin': live_server})
    assert r.status_code == 403, (r.status_code, r.text[:120])


def test_csrf_accepts_matching_token(live_server):
    s = _login(live_server)
    tok = s.cookies.get('storm_csrf')
    assert tok, 'login must plant the storm_csrf cookie'
    r = s.post(f'{live_server}/api/alerts/clear', timeout=10,
               headers={'Origin': live_server, 'X-CSRF-Token': tok})
    assert r.status_code == 200, (r.status_code, r.text[:120])


def test_csrf_rejects_wrong_token(live_server):
    s = _login(live_server)
    r = s.post(f'{live_server}/api/alerts/clear', timeout=10,
               headers={'Origin': live_server, 'X-CSRF-Token': 'nope'})
    assert r.status_code == 403


def test_csrf_cross_origin_still_403(live_server):
    s = _login(live_server)
    tok = s.cookies.get('storm_csrf')
    r = s.post(f'{live_server}/api/alerts/clear', timeout=10,
               headers={'Origin': 'https://evil.example', 'X-CSRF-Token': tok})
    assert r.status_code == 403


def test_csrf_untouched_without_origin(live_server):
    """curl-style clients (no Origin) keep working — SameSite=Lax covers them."""
    s = _login(live_server)
    r = s.post(f'{live_server}/api/alerts/clear', timeout=10)
    assert r.status_code == 200, (r.status_code, r.text[:120])
