"""listeners blueprint (P15.3 -- additive managed-listener API).

ADD-ONLY endpoints (NR-2).  Start/stop named listeners; every connection is
recorded as evidence on a target.  P1.2: interactive listeners keep the catch
alive -- sessions/send/read/close drive the reverse shell over the API.
"""
from __future__ import annotations

import os

from flask import Blueprint, jsonify, request, session

from app.exec.listener_service import get_service
from app.state import BASE_DIR

bp = Blueprint("listeners", __name__,
               template_folder=os.path.join(BASE_DIR, "flask_templates"))

def _guard():
    if 'IAm-logined' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    return None

@bp.route('/api/listeners')
def api_listeners():
    bad = _guard()
    if bad:
        return bad
    return jsonify({'listeners': get_service().list()})

@bp.route('/api/listeners/start', methods=['POST'])
def api_listeners_start():
    bad = _guard()
    if bad:
        return bad
    data = request.json or {}
    name = data.get('name') or 'default'
    info = get_service().start(name, data.get('host', '127.0.0.1'),
                               int(data.get('port', 0)), bool(data.get('hold', False)),
                               bool(data.get('interactive', False)))
    return jsonify({'status': 'listening', 'listener': info})

@bp.route('/api/listeners/stop', methods=['POST'])
def api_listeners_stop():
    bad = _guard()
    if bad:
        return bad
    data = request.json or {}
    stopped = get_service().stop(data.get('name') or 'default')
    return jsonify({'status': 'stopped' if stopped else 'not-found'})

# ---- P1.2: live shell sessions on interactive listeners ----

@bp.route('/api/listeners/sessions')
def api_listeners_sessions():
    bad = _guard()
    if bad:
        return bad
    return jsonify({'sessions': get_service().sessions()})

@bp.route('/api/listeners/send', methods=['POST'])
def api_listeners_send():
    bad = _guard()
    if bad:
        return bad
    data = request.json or {}
    key = (data.get('key') or '').strip()
    command = (data.get('command') or '')
    if not key or not command.strip():
        return jsonify({'error': 'key and command required'}), 400
    sent = get_service().send(key, command)
    if not sent:
        return jsonify({'error': 'session not found or closed'}), 404
    return jsonify({'status': 'sent', 'key': key})

@bp.route('/api/listeners/read', methods=['POST'])
def api_listeners_read():
    bad = _guard()
    if bad:
        return bad
    data = request.json or {}
    key = (data.get('key') or '').strip()
    if not key:
        return jsonify({'error': 'key required'}), 400
    lines = get_service().read(key, clear=bool(data.get('clear', True)))
    return jsonify({'key': key, 'lines': lines})

@bp.route('/api/listeners/close', methods=['POST'])
def api_listeners_close():
    bad = _guard()
    if bad:
        return bad
    data = request.json or {}
    closed = get_service().close((data.get('key') or '').strip())
    return jsonify({'status': 'closed' if closed else 'not-found'})
