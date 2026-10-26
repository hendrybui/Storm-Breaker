"""jobs blueprint (P6.5 — additive job-status API).

ADD-ONLY endpoints (NR-2): legacy routes are untouched; these expose the
P6 background worker to the operator panel.
"""
from __future__ import annotations

import os

from flask import Blueprint, jsonify, request, session

from app.state import BASE_DIR
from app.core.jobs import get_queue
from app.services import intel as intelsvc
from app.services import artifacts as artifactsvc

bp = Blueprint("jobs", __name__,
               template_folder=os.path.join(BASE_DIR, "flask_templates"))


@bp.route('/api/jobs/<job_id>')
def api_job_status(job_id):
    if 'IAm-logined' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    st = get_queue().status(job_id)
    if st is None:
        return jsonify({'error': 'Job not found'}), 404
    return jsonify(st)


@bp.route('/api/credentials/scan-async', methods=['POST'])
def api_credentials_scan_async():
    """Queue the full credential scan; poll /api/jobs/<job_id> for the
    same payload the synchronous route returns (``result`` field)."""
    if 'IAm-logined' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    job_id = get_queue().enqueue(intelsvc.run_credential_scan)
    return jsonify({'status': 'queued', 'job_id': job_id}), 202


@bp.route('/api/reports/generate-async', methods=['POST'])
def api_report_generate_async():
    """Queue report generation; poll /api/jobs/<job_id> for the result."""
    if 'IAm-logined' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    from datetime import datetime
    data = request.json or {}
    config = {
        'title': data.get('title', 'Storm-Breaker Penetration Test Report'),
        'organization': data.get('organization', 'Security Assessment Team'),
        'target': data.get('target', 'Target Organization'),
        'author': data.get('author', session.get('IAm-logined', 'Operator')),
        'date': data.get('date', datetime.now().strftime('%Y-%m-%d')),
        'classification': data.get('classification', 'CONFIDENTIAL'),
    }
    job_id = get_queue().enqueue(
        artifactsvc.create_report, config, data.get('type', 'full'),
        session.get('IAm-logined', 'Operator'), request.remote_addr)
    return jsonify({'status': 'queued', 'job_id': job_id}), 202
