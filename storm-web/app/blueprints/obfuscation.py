"""obfuscation blueprint (P3 batch extract)."""
from __future__ import annotations

import os, json, base64
import uuid as uuid_module
from datetime import datetime, timedelta
from functools import wraps
from flask import (Blueprint, request, jsonify, redirect, url_for, render_template, send_from_directory, make_response, session, Response)
from app.state import *  # noqa: F401,F403  -- P3
from app.state import BASE_DIR, CONFIG, _decode_data_url, _save_mobile_capture
import database as db

bp = Blueprint("obfuscation", __name__,
               template_folder=os.path.join(BASE_DIR, "flask_templates"))


@bp.route('/api/obfuscate', methods=['POST'])
def api_obfuscate():
    if 'IAm-logined' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    from obfuscation_engine import obfuscate_payload, get_profiles, get_supported_techniques
    data = request.json
    payload = data.get('payload', '')
    language = data.get('language', 'powershell')
    profile = data.get('profile', 'medium')
    custom = data.get('custom_techniques')
    if not payload:
        return jsonify({'error': 'No payload provided'}), 400
    result = obfuscate_payload(payload, language, profile, custom)
    db.log_operator_action(session.get('IAm-logined', 'unknown'), 'obfuscate',
                           f'Obfuscated {language} payload with {profile} profile', request.remote_addr)
    return jsonify(result)

@bp.route('/api/obfuscate/profiles')
def api_obfuscate_profiles():
    if 'IAm-logined' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    from obfuscation_engine import get_profiles, get_supported_techniques
    return jsonify({
        'profiles': get_profiles(),
        'techniques': {
            lang: get_supported_techniques(lang)
            for lang in ['powershell', 'python', 'javascript', 'bash']
        }
    })
