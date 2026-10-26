"""P3.2 part B - /api/session/{start,events,end}.

Routes verbatim from storm-web/app.py:638-731 (lines moved at
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


bp = Blueprint("capture_sessions", __name__,
               template_folder=os.path.join(BASE_DIR, "flask_templates"))


@bp.route('/api/session/start', methods=['POST'])
def session_start():
    """Handle session recording start."""
    try:
        data = request.json
        if not data or 'sessionId' not in data:
            return jsonify({'error': 'No session ID provided'}), 400
        return jsonify(capturesvc.session_start(data))
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/api/session/events', methods=['POST'])
def session_events():
    """Handle session recording events."""
    try:
        data = request.json
        if not data or 'sessionId' not in data or 'events' not in data:
            return jsonify({'error': 'Invalid data'}), 400
        return jsonify(capturesvc.session_events(data))
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/api/session/end', methods=['POST'])
def session_end():
    """Handle session recording end."""
    try:
        data = request.json
        if not data or 'sessionId' not in data:
            return jsonify({'error': 'No session ID provided'}), 400
        return jsonify(capturesvc.session_end(data))
    except Exception as e:
        return jsonify({'error': str(e)}), 500
