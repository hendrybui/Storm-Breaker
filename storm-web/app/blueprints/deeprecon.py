"""deeprecon blueprint (P3 batch extract; thinned to HTTP adapter at P4.6).

Business logic lives in ``app/services/osint.py`` (DeepReconOSINT).
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

bp = Blueprint("deeprecon", __name__,
               template_folder=os.path.join(BASE_DIR, "flask_templates"))


@bp.route('/api/deeprecon/domain', methods=['POST'])

def api_deeprecon_domain():
    domain = request.form.get('domain', '')
    return jsonify({'success': True, 'result': osintsvc.deeprecon_domain(domain)})

@bp.route('/api/deeprecon/social', methods=['POST'])

def api_deeprecon_social():
    username = request.form.get('username', '')
    return jsonify({'success': True, 'result': osintsvc.deeprecon_social(username)})

@bp.route('/api/deeprecon/darkweb', methods=['POST'])

def api_deeprecon_darkweb():
    query = request.form.get('query', '')
    return jsonify({'success': True, 'result': osintsvc.deeprecon_darkweb(query)})

@bp.route('/api/deeprecon/email', methods=['POST'])

def api_deeprecon_email():
    email = request.form.get('email', '')
    return jsonify({'success': True, 'result': osintsvc.deeprecon_email(email)})

@bp.route('/api/deeprecon/infra', methods=['POST'])

def api_deeprecon_infra():
    target = request.form.get('target', '')
    return jsonify({'success': True, 'result': osintsvc.deeprecon_infra(target)})

@bp.route('/api/deeprecon/correlate', methods=['POST'])

def api_deeprecon_correlate():
    entities_raw = request.form.get('entities', '[]')
    try:
        entities = json.loads(entities_raw)
    except json.JSONDecodeError:
        entities = [e.strip() for e in entities_raw.split(',') if e.strip()]
    return jsonify({'success': True, 'result': osintsvc.deeprecon_correlate(entities)})


if __name__ == '__main__':
    # Initialize database
    db.init_database()
    app.run(host='0.0.0.0', port=2525, debug=False)
