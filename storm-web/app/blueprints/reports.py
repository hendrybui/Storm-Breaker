"""reports blueprint (P3 batch extract)."""
from __future__ import annotations

import os, json, base64
import uuid as uuid_module
from datetime import datetime, timedelta
from functools import wraps
from flask import (Blueprint, request, jsonify, redirect, url_for, render_template, send_from_directory, make_response, session, Response)
from app.state import *  # noqa: F401,F403  -- P3
from app.state import BASE_DIR, CONFIG, _decode_data_url, _save_mobile_capture
import database as db
from app.services import artifacts as artifactsvc

bp = Blueprint("reports", __name__,
               template_folder=os.path.join(BASE_DIR, "flask_templates"))


@bp.route('/api/reports/generate', methods=['POST'])
def api_generate_report():
    if 'IAm-logined' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    from report_generator import generate_report  # noqa: F401  -- P6.4 moves gen off request path
    data = request.json or {}
    config = {
        'title': data.get('title', 'Storm-Breaker Penetration Test Report'),
        'organization': data.get('organization', 'Security Assessment Team'),
        'target': data.get('target', 'Target Organization'),
        'author': data.get('author', session.get('IAm-logined', 'Operator')),
        'date': data.get('date', datetime.now().strftime('%Y-%m-%d')),
        'classification': data.get('classification', 'CONFIDENTIAL'),
    }
    return jsonify(artifactsvc.create_report(
        config, data.get('type', 'full'),
        session.get('IAm-logined', 'Operator'), request.remote_addr))

@bp.route('/api/reports')
def api_list_reports():
    if 'IAm-logined' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    return jsonify({'reports': artifactsvc.list_reports()})

@bp.route('/api/reports/<int:report_id>')
def api_get_report(report_id):
    if 'IAm-logined' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    report = artifactsvc.get_report(report_id)
    if not report:
        return jsonify({'error': 'Report not found'}), 404
    return jsonify(report)

@bp.route('/api/reports/<int:report_id>/view')
def api_view_report(report_id):
    if 'IAm-logined' not in session:
        return redirect('/login')
    report = artifactsvc.get_report(report_id)
    if not report:
        return 'Report not found', 404
    return Response(report['html_content'], mimetype='text/html')

@bp.route('/api/reports/<int:report_id>/verify')
def api_verify_report(report_id):
    """P1.4: recompute the report's evidence signature over stored bytes."""
    if 'IAm-logined' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    from app.core.integrity import verify_content
    report = artifactsvc.get_report(report_id)
    if not report:
        return jsonify({'error': 'Report not found'}), 404
    stats = report.get('stats')
    if isinstance(stats, str):
        try:
            stats = json.loads(stats)
        except Exception:
            stats = {}
    integrity = (stats or {}).get('integrity')
    ok = verify_content(report.get('html_content') or '', integrity)
    return jsonify({'status': 'verified' if ok else 'tampered-or-unsigned',
                    'report_id': report_id})

@bp.route('/api/reports/<int:report_id>', methods=['DELETE'])
def api_delete_report(report_id):
    if 'IAm-logined' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    artifactsvc.delete_report(report_id)
    return jsonify({'status': 'deleted'})
