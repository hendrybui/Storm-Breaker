"""Unit tests for ``app.core.hardening`` (P7.2 CSRF gate + P7.4 upload caps)."""
import pytest

from app.core.hardening import per_type_upload_limit


@pytest.fixture()
def app():
    from app import create_app
    return create_app()


@pytest.fixture()
def client(app):
    """Flask test client with a logged-in operator session."""
    c = app.test_client()
    with c.session_transaction() as sess:
        sess['IAm-logined'] = 'admin'
    return c


BASE = 'http://localhost'
CHEAP_POST = '/api/lures/preview'   # real operator POST route, harmless body


def test_csrf_blocks_cross_origin_mutating_request(app, client):
    rv = client.post(CHEAP_POST, json={},
                     headers={'Origin': 'https://evil.example'})
    assert rv.status_code == 403


def test_csrf_allows_same_origin(app, client):
    rv = client.post(CHEAP_POST, json={},
                     headers={'Origin': BASE})
    assert rv.status_code != 403


def test_csrf_allows_headerless_clients(app, client):
    """curl / scripts / the char suite send no Origin — allowed by design
    (the cookie-level SameSite=Lax control covers browser-based CSRF)."""
    rv = client.post(CHEAP_POST, json={})
    assert rv.status_code != 403


def test_csrf_exempts_unauthenticated_victim_traffic(app):
    """Victim endpoints have no operator session — the gate never fires."""
    c = app.test_client()
    rv = c.post('/api/fingerprint', data='{}',
                content_type='application/json',
                headers={'Origin': 'https://evil.example'})
    assert rv.status_code != 403


def test_csrf_ignores_safe_methods(app, client):
    rv = client.get('/api/lures/categories',
                    headers={'Origin': 'https://evil.example'})
    assert rv.status_code != 403


def test_referer_fallback_checked(app, client):
    rv = client.post(CHEAP_POST, json={},
                     headers={'Referer': 'https://evil.example/panel'})
    assert rv.status_code == 403


def test_cookies_hardened(app):
    assert app.config.get('SESSION_COOKIE_HTTPONLY') is True
    assert app.config.get('SESSION_COOKIE_SAMESITE') == 'Lax'


def test_global_upload_cap_set(app):
    assert app.config['MAX_CONTENT_LENGTH'] is not None
    assert app.config['MAX_CONTENT_LENGTH'] >= 32 * 1024 * 1024


def test_per_type_limit_exceeded():
    limits = {'/api/fingerprint': 1024}
    assert per_type_upload_limit('/api/fingerprint', 2048, limits) == 1024
    assert per_type_upload_limit('/api/fingerprint', 512, limits) is None
    assert per_type_upload_limit('/api/unknown', 999999999, limits) is None


def test_per_type_limit_gate_returns_413(app):
    from app.core.hardening import upload_cap_gate
    with app.test_request_context(
            '/api/fingerprint', method='POST',
            environ_base={'CONTENT_LENGTH': str(10 * 1024 * 1024)}):
        rv = upload_cap_gate()
        assert rv is not None and rv[1] == 413


def test_per_type_limit_gate_allows_small(app):
    from app.core.hardening import upload_cap_gate
    with app.test_request_context(
            '/api/fingerprint', method='POST',
            environ_base={'CONTENT_LENGTH': '256'}):
        assert upload_cap_gate() is None


# -- P9.5: CSP on HTML responses ------------------------------------------------
def test_csp_header_on_html(app, client):
    rv = client.get('/login')
    assert 'Content-Security-Policy' in rv.headers
    csp = rv.headers['Content-Security-Policy']
    assert "default-src 'self'" in csp
    assert "frame-ancestors 'none'" in csp


def test_csp_header_absent_on_json(app, client):
    rv = client.get('/api/lures/categories')
    assert 'Content-Security-Policy' not in rv.headers


def test_csp_allows_inline_and_self(app, client):
    """panel.html needs inline scripts/styles (tailwind play + legacy JS)."""
    rv = client.get('/login')
    csp = rv.headers['Content-Security-Policy']
    assert "script-src 'self' 'unsafe-inline'" in csp
    assert "style-src 'self' 'unsafe-inline'" in csp
    assert "connect-src 'self'" in csp
