"""deeprecon blueprint (P3 batch extract)."""
from __future__ import annotations

import os, json, base64
import uuid as uuid_module
from datetime import datetime, timedelta
from functools import wraps
from flask import (Blueprint, request, jsonify, redirect, url_for, render_template, send_from_directory, make_response, session, Response)
from app.state import *  # noqa: F401,F403  -- P3
from app.state import BASE_DIR, CONFIG, _decode_data_url, _save_mobile_capture
import database as db

from deep_recon import DeepReconOSINT
bp = Blueprint("deeprecon", __name__,
               template_folder=os.path.join(BASE_DIR, "flask_templates"))


@bp.route('/api/deeprecon/domain', methods=['POST'])

def api_deeprecon_domain():
    domain = request.form.get('domain', '')
    result = DeepReconOSINT.domain_recon(domain)
    return jsonify({'success': True, 'result': result})

@bp.route('/api/deeprecon/social', methods=['POST'])

def api_deeprecon_social():
    username = request.form.get('username', '')
    result = DeepReconOSINT.social_profile_search(username)
    return jsonify({'success': True, 'result': result})

@bp.route('/api/deeprecon/darkweb', methods=['POST'])

def api_deeprecon_darkweb():
    query = request.form.get('query', '')
    result = DeepReconOSINT.dark_web_scan(query)
    return jsonify({'success': True, 'result': result})

@bp.route('/api/deeprecon/email', methods=['POST'])

def api_deeprecon_email():
    email = request.form.get('email', '')
    result = DeepReconOSINT.email_intelligence(email)
    return jsonify({'success': True, 'result': result})

@bp.route('/api/deeprecon/infra', methods=['POST'])

def api_deeprecon_infra():
    target = request.form.get('target', '')
    result = DeepReconOSINT.infrastructure_map(target)
    return jsonify({'success': True, 'result': result})

@bp.route('/api/deeprecon/correlate', methods=['POST'])

def api_deeprecon_correlate():
    entities_raw = request.form.get('entities', '[]')
    try:
        entities = json.loads(entities_raw)
    except json.JSONDecodeError:
        entities = [e.strip() for e in entities_raw.split(',') if e.strip()]
    result = DeepReconOSINT.correlate_data(entities)
    return jsonify({'success': True, 'result': result})


if __name__ == '__main__':
    # Initialize database
    db.init_database()
    app.run(host='0.0.0.0', port=2525, debug=False)
