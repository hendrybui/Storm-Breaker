"""payloads blueprint (P3 batch extract)."""
from __future__ import annotations

import os, json, base64
import uuid as uuid_module
from datetime import datetime, timedelta
from functools import wraps
from flask import (Blueprint, request, jsonify, redirect, url_for, render_template, send_from_directory, make_response, session, Response)
from app.state import *  # noqa: F401,F403  -- P3
from app.state import BASE_DIR, CONFIG, _decode_data_url, _save_mobile_capture
import database as db

from payload_generator import PAYLOAD_TYPES
from app.services import artifacts as artifactsvc
bp = Blueprint("payloads", __name__,
               template_folder=os.path.join(BASE_DIR, "flask_templates"))


@bp.route('/api/payloads/types')
def payloads_types():
    """Get available payload types"""
    return jsonify({'types': artifactsvc.payload_types()})

@bp.route('/api/payloads/generate', methods=['POST'])
def payloads_generate():
    """Generate a payload"""
    try:
        data = request.json
        payload_type = data.get('type')
        config = {
            'lhost': data.get('lhost', '127.0.0.1'),
            'lport': data.get('lport', '4444'),
            'callback_url': data.get('callback_url', ''),
            'template': data.get('template', ''),
            'obfuscate': data.get('obfuscate', False),
        }
        
        result = artifactsvc.generate_payload(payload_type, config)
        if 'error' in result:
            return jsonify(result), 400
        
        track_event('payload_generated', {'type': payload_type})
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
