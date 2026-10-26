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


bp = Blueprint("capture_sessions", __name__,
               template_folder=os.path.join(BASE_DIR, "flask_templates"))


@bp.route('/api/session/start', methods=['POST'])
def session_start():
    """Handle session recording start."""
    try:
        data = request.json
        if not data or 'sessionId' not in data:
            return jsonify({'error': 'No session ID provided'}), 400
        sessions_dir = os.path.join(BASE_DIR, 'sessions')
        os.makedirs(sessions_dir, exist_ok=True)
        session_id = data.get('sessionId')
        filepath = os.path.join(sessions_dir, f'{session_id}_meta.json')
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        send_notification({
            "type": "Session Recording Started",
            "sessionId": session_id,
            "url": data.get('url', 'Unknown'),
            "timestamp": datetime.now().isoformat()
        })
        return jsonify({'status': 'success', 'sessionId': session_id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/api/session/events', methods=['POST'])
def session_events():
    """Handle session recording events."""
    try:
        data = request.json
        if not data or 'sessionId' not in data or 'events' not in data:
            return jsonify({'error': 'Invalid data'}), 400
        sessions_dir = os.path.join(BASE_DIR, 'sessions')
        os.makedirs(sessions_dir, exist_ok=True)
        session_id = data.get('sessionId')
        filepath = os.path.join(sessions_dir, f'{session_id}_events.jsonl')
        with open(filepath, 'a') as f:
            for event in data.get('events', []):
                f.write(json.dumps(event) + '\n')
        return jsonify({'status': 'success', 'count': len(data.get('events', []))})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/api/session/end', methods=['POST'])
def session_end():
    """Handle session recording end."""
    try:
        data = request.json
        if not data or 'sessionId' not in data:
            return jsonify({'error': 'No session ID provided'}), 400
        session_id = data.get('sessionId')
        sessions_dir = os.path.join(BASE_DIR, 'sessions')
        meta_filepath = os.path.join(sessions_dir, f'{session_id}_meta.json')
        if os.path.exists(meta_filepath):
            with open(meta_filepath, 'r') as f:
                meta = json.load(f)
            meta['endTime'] = data.get('timestamp')
            meta['duration'] = data.get('duration', 0)
            with open(meta_filepath, 'w') as f:
                json.dump(meta, f, indent=2)
        send_notification({
            "type": "Session Recording Ended",
            "sessionId": session_id,
            "duration": data.get('duration', 0),
            "timestamp": datetime.now().isoformat()
        })
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
