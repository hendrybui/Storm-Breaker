"""pivot blueprint (P3 batch extract)."""
from __future__ import annotations

import os, json, base64
import uuid as uuid_module
from datetime import datetime, timedelta
from functools import wraps
from flask import (Blueprint, request, jsonify, redirect, url_for, render_template, send_from_directory, make_response, session, Response)
from app.state import *  # noqa: F401,F403  -- P3
from app.state import BASE_DIR, CONFIG, _decode_data_url, _save_mobile_capture
import database as db

bp = Blueprint("pivot", __name__,
               template_folder=os.path.join(BASE_DIR, "flask_templates"))


@bp.route('/api/pivot/capabilities', methods=['GET'])
def api_pivot_caps():
    from pivot_engine import get_pivot_capabilities
    return jsonify(get_pivot_capabilities())

@bp.route('/api/pivot/attack-graph', methods=['POST'])
def api_pivot_graph():
    from pivot_engine import build_attack_graph
    data = request.get_json(force=True)
    hosts = data.get('hosts', [])
    credentials = data.get('credentials', [])
    sessions = data.get('sessions')
    result = build_attack_graph(hosts, credentials, sessions)
    track_event('pivot')
    # Save
    db.save_pivot_record('attack_graph', data.get('name', 'Attack Graph'),
                         result, result.get('total_hosts', 0),
                         result.get('total_lateral_paths', 0), 0,
                         session.get('IAm-logined', 'unknown'))
    db.log_operator_action(session.get('IAm-logined', 'unknown'), 'attack_graph',
                           f'Built attack graph: {result.get("total_hosts")} hosts', request.remote_addr)
    return jsonify(result)

@bp.route('/api/pivot/credential-reuse', methods=['POST'])
def api_pivot_cred_reuse():
    from pivot_engine import map_credential_reuse
    data = request.get_json(force=True)
    credentials = data.get('credentials', [])
    hosts = data.get('hosts', [])
    result = map_credential_reuse(credentials, hosts)
    track_event('pivot')
    return jsonify(result)

@bp.route('/api/pivot/privesc', methods=['POST'])
def api_pivot_privesc():
    from pivot_engine import suggest_privesc
    data = request.get_json(force=True)
    os_type = data.get('os_type', 'linux')
    current_user = data.get('current_user', 'user')
    result = suggest_privesc(os_type, current_user)
    track_event('pivot')
    return jsonify(result)

@bp.route('/api/pivot/kill-chain', methods=['POST'])
def api_pivot_killchain():
    from pivot_engine import track_kill_chain
    data = request.get_json(force=True)
    events = data.get('events', [])
    result = track_kill_chain(events)
    track_event('pivot')
    # Save
    db.save_pivot_record('kill_chain', 'Kill Chain Assessment',
                         result, 0, 0, result.get('coverage_percent', 0),
                         session.get('IAm-logined', 'unknown'))
    return jsonify(result)

@bp.route('/api/pivot/attack-surface', methods=['POST'])
def api_pivot_surface():
    from pivot_engine import score_attack_surface
    data = request.get_json(force=True)
    result = score_attack_surface(
        hosts=data.get('hosts', []),
        credentials=data.get('credentials', []),
        sessions=data.get('sessions', []),
        browser_exfil=data.get('browser_exfil', []))
    track_event('pivot')
    return jsonify(result)

@bp.route('/api/pivot/history', methods=['GET'])
def api_pivot_history():
    record_type = request.args.get('type')
    records = db.get_pivot_records(record_type)
    return jsonify({'records': records})

@bp.route('/api/pivot/<int:record_id>', methods=['DELETE'])
def api_pivot_delete(record_id):
    db.delete_pivot_record(record_id)
    return jsonify({'status': 'deleted'})
