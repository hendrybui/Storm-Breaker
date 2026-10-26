"""threat_intel blueprint (P3 batch extract)."""
from __future__ import annotations

import os, json, base64
import uuid as uuid_module
from datetime import datetime, timedelta
from functools import wraps
from flask import (Blueprint, request, jsonify, redirect, url_for, render_template, send_from_directory, make_response, session, Response)
from app.state import *  # noqa: F401,F403  -- P3
from app.state import BASE_DIR, CONFIG, _decode_data_url, _save_mobile_capture
import database as db

bp = Blueprint("threat_intel", __name__,
               template_folder=os.path.join(BASE_DIR, "flask_templates"))


@bp.route('/api/threat-intel/types', methods=['GET'])
def api_threat_types():
    from threat_intel import get_supported_intel_types
    return jsonify(get_supported_intel_types())

@bp.route('/api/threat-intel/ip', methods=['POST'])
def api_threat_ip():
    from threat_intel import analyze_ip
    data = request.get_json(force=True)
    ip = data.get('ip', '')
    headers = data.get('headers')
    result = analyze_ip(ip, headers)
    track_event('threat_intel')
    db.save_threat_intel('ip', ip, result, result.get('threat_score', 0),
                         result.get('threat_level', 'none'),
                         session.get('IAm-logined', 'unknown'))
    return jsonify(result)

@bp.route('/api/threat-intel/email', methods=['POST'])
def api_threat_email():
    from threat_intel import analyze_email
    data = request.get_json(force=True)
    email = data.get('email', '')
    result = analyze_email(email)
    track_event('threat_intel')
    db.save_threat_intel('email', email, result, result.get('intelligence_score', 0),
                         'high' if result.get('intelligence_score', 0) > 70 else 'medium',
                         session.get('IAm-logined', 'unknown'))
    return jsonify(result)

@bp.route('/api/threat-intel/technology', methods=['POST'])
def api_threat_tech():
    from threat_intel import fingerprint_technology
    data = request.get_json(force=True)
    headers = data.get('headers', {})
    html_body = data.get('html_body', '')
    result = fingerprint_technology(headers, html_body)
    track_event('threat_intel')
    return jsonify(result)

@bp.route('/api/threat-intel/social', methods=['POST'])
def api_threat_social():
    from threat_intel import discover_social_profiles
    data = request.get_json(force=True)
    username = data.get('username', '')
    email = data.get('email')
    result = discover_social_profiles(username, email)
    track_event('threat_intel')
    return jsonify(result)

@bp.route('/api/threat-intel/report', methods=['POST'])
def api_threat_report():
    from threat_intel import build_threat_report
    data = request.get_json(force=True)
    result = build_threat_report(
        ip_address=data.get('ip'),
        email=data.get('email'),
        username=data.get('username'),
        headers=data.get('headers'),
        html_body=data.get('html_body'))
    track_event('threat_intel')
    db.save_threat_intel('full_report', json.dumps({k: data.get(k, '') for k in ('ip', 'email', 'username')}),
                         result, result.get('overall_threat_score', 0),
                         result.get('overall_threat_level', 'none'),
                         session.get('IAm-logined', 'unknown'))
    db.log_operator_action(session.get('IAm-logined', 'unknown'), 'threat_report',
                           f'Built threat report', request.remote_addr)
    return jsonify(result)

@bp.route('/api/threat-intel/history', methods=['GET'])
def api_threat_history():
    intel_type = request.args.get('type')
    records = db.get_threat_intel(intel_type)
    return jsonify({'records': records})

@bp.route('/api/threat-intel/<int:intel_id>', methods=['DELETE'])
def api_threat_delete(intel_id):
    db.delete_threat_intel(intel_id)
    return jsonify({'status': 'deleted'})


# ═══════════════════════════════════════════════════════════════
# SESSION HIJACKER API
# ═══════════════════════════════════════════════════════════════
