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

bp = Blueprint("reports", __name__,
               template_folder=os.path.join(BASE_DIR, "flask_templates"))


@bp.route('/api/reports/generate', methods=['POST'])
def api_generate_report():
    if 'IAm-logined' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    from report_generator import generate_report
    data = request.json or {}
    config = {
        'title': data.get('title', 'Storm-Breaker Penetration Test Report'),
        'organization': data.get('organization', 'Security Assessment Team'),
        'target': data.get('target', 'Target Organization'),
        'author': data.get('author', session.get('IAm-logined', 'Operator')),
        'date': data.get('date', datetime.now().strftime('%Y-%m-%d')),
        'classification': data.get('classification', 'CONFIDENTIAL'),
    }
    result = generate_report(config)
    # Save to database
    report_id = db.save_report(
        name=config['title'],
        report_type=data.get('type', 'full'),
        config=config,
        html_content=result['html'],
        stats=result['stats'],
    )
    db.log_operator_action(session.get('IAm-logined', 'unknown'), 'generate_report',
                           f'Generated report: {config["title"]}', request.remote_addr)
    return jsonify({'id': report_id, 'stats': result['stats'], 'generated_at': result['generated_at']})

@bp.route('/api/reports')
def api_list_reports():
    if 'IAm-logined' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    reports = db.get_reports()
    for r in reports:
        if isinstance(r.get('stats'), str):
            try:
                r['stats'] = json.loads(r['stats'])
            except Exception:
                pass
        if isinstance(r.get('config'), str):
            try:
                r['config'] = json.loads(r['config'])
            except Exception:
                pass
    return jsonify({'reports': reports})

@bp.route('/api/reports/<int:report_id>')
def api_get_report(report_id):
    if 'IAm-logined' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    report = db.get_report(report_id)
    if not report:
        return jsonify({'error': 'Report not found'}), 404
    return jsonify(report)

@bp.route('/api/reports/<int:report_id>/view')
def api_view_report(report_id):
    if 'IAm-logined' not in session:
        return redirect('/login')
    report = db.get_report(report_id)
    if not report:
        return 'Report not found', 404
    return Response(report['html_content'], mimetype='text/html')

@bp.route('/api/reports/<int:report_id>', methods=['DELETE'])
def api_delete_report(report_id):
    if 'IAm-logined' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    db.delete_report(report_id)
    return jsonify({'status': 'deleted'})
