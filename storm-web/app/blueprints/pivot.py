"""pivot blueprint (P3 batch extract; thinned to HTTP adapter at P4.6).

Business logic lives in ``app/services/osint.py`` (pivot_engine).
Response shapes are frozen and enforced by tests/char.
"""
from __future__ import annotations

import os, json, base64
import uuid as uuid_module
from datetime import datetime, timedelta
from functools import wraps
from flask import (Blueprint, request, jsonify, redirect, url_for, render_template, send_from_directory, make_response, session, Response)
from app.state import *  # noqa: F401,F403  -- P3
from app.state import BASE_DIR, CONFIG, _decode_data_url, _save_mobile_capture
import database as db
from app.services import osint as osintsvc

bp = Blueprint("pivot", __name__,
               template_folder=os.path.join(BASE_DIR, "flask_templates"))


@bp.route('/api/pivot/capabilities', methods=['GET'])
def api_pivot_caps():
    return jsonify(osintsvc.pivot_capabilities())

@bp.route('/api/pivot/attack-graph', methods=['POST'])
def api_pivot_graph():
    data = request.get_json(force=True)
    return jsonify(osintsvc.build_attack_graph(
        data.get('hosts', []), data.get('credentials', []),
        data.get('sessions'), data.get('name', 'Attack Graph'),
        session.get('IAm-logined', 'unknown'), request.remote_addr))

@bp.route('/api/pivot/credential-reuse', methods=['POST'])
def api_pivot_cred_reuse():
    data = request.get_json(force=True)
    return jsonify(osintsvc.map_credential_reuse(
        data.get('credentials', []), data.get('hosts', [])))

@bp.route('/api/pivot/privesc', methods=['POST'])
def api_pivot_privesc():
    data = request.get_json(force=True)
    return jsonify(osintsvc.suggest_privesc(
        data.get('os_type', 'linux'), data.get('current_user', 'user')))

@bp.route('/api/pivot/kill-chain', methods=['POST'])
def api_pivot_killchain():
    data = request.get_json(force=True)
    return jsonify(osintsvc.track_kill_chain(
        data.get('events', []), session.get('IAm-logined', 'unknown')))

@bp.route('/api/pivot/attack-surface', methods=['POST'])
def api_pivot_surface():
    data = request.get_json(force=True)
    return jsonify(osintsvc.score_attack_surface(
        hosts=data.get('hosts', []),
        credentials=data.get('credentials', []),
        sessions=data.get('sessions', []),
        browser_exfil=data.get('browser_exfil', [])))

@bp.route('/api/pivot/history', methods=['GET'])
def api_pivot_history():
    record_type = request.args.get('type')
    return jsonify({'records': osintsvc.pivot_history(record_type)})

@bp.route('/api/pivot/<int:record_id>', methods=['DELETE'])
def api_pivot_delete(record_id):
    osintsvc.delete_pivot_record(record_id)
    return jsonify({'status': 'deleted'})
