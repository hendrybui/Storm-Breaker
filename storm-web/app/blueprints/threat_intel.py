"""threat_intel blueprint (P3 batch extract; thinned to HTTP adapter at P4.6).

Business logic lives in ``app/services/osint.py``.  Response shapes are
frozen and enforced by tests/char.
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

bp = Blueprint("threat_intel", __name__,
               template_folder=os.path.join(BASE_DIR, "flask_templates"))


@bp.route('/api/threat-intel/types', methods=['GET'])
def api_threat_types():
    return jsonify(osintsvc.threat_types())

@bp.route('/api/threat-intel/ip', methods=['POST'])
def api_threat_ip():
    data = request.get_json(force=True)
    return jsonify(osintsvc.analyze_ip(
        data.get('ip', ''), data.get('headers'),
        session.get('IAm-logined', 'unknown')))

@bp.route('/api/threat-intel/email', methods=['POST'])
def api_threat_email():
    data = request.get_json(force=True)
    return jsonify(osintsvc.analyze_email(
        data.get('email', ''), session.get('IAm-logined', 'unknown')))

@bp.route('/api/threat-intel/technology', methods=['POST'])
def api_threat_tech():
    data = request.get_json(force=True)
    return jsonify(osintsvc.fingerprint_technology(
        data.get('headers', {}), data.get('html_body', '')))

@bp.route('/api/threat-intel/social', methods=['POST'])
def api_threat_social():
    data = request.get_json(force=True)
    return jsonify(osintsvc.discover_social_profiles(
        data.get('username', ''), data.get('email')))

@bp.route('/api/threat-intel/report', methods=['POST'])
def api_threat_report():
    data = request.get_json(force=True)
    return jsonify(osintsvc.build_threat_report(
        data, session.get('IAm-logined', 'unknown'), request.remote_addr))

@bp.route('/api/threat-intel/history', methods=['GET'])
def api_threat_history():
    intel_type = request.args.get('type')
    return jsonify({'records': osintsvc.threat_history(intel_type)})

@bp.route('/api/threat-intel/<int:intel_id>', methods=['DELETE'])
def api_threat_delete(intel_id):
    osintsvc.delete_threat_intel(intel_id)
    return jsonify({'status': 'deleted'})
