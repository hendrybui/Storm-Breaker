"""lures blueprint (P3 batch extract)."""
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

bp = Blueprint("lures", __name__,
               template_folder=os.path.join(BASE_DIR, "flask_templates"))


@bp.route('/api/lures/categories')
def api_lure_categories():
    if 'IAm-logined' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    return jsonify({'categories': artifactsvc.lure_categories()})

@bp.route('/api/lures/preview', methods=['POST'])
def api_lure_preview():
    if 'IAm-logined' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    data = request.json
    return jsonify(artifactsvc.lure_preview(
        data.get('category', ''), data.get('template_index', 0)))

@bp.route('/api/lures/generate', methods=['POST'])
def api_lure_generate():
    if 'IAm-logined' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    data = request.json
    log_note = f'Generated {data.get("type", "email")} lure: {data.get("category")}'
    return jsonify(artifactsvc.generate_lure(
        category=data.get('category', ''),
        template_index=data.get('template_index', 0),
        variables=data.get('variables', {}),
        lure_type=data.get('type', 'email'),
        log_note=log_note,
        operator=session.get('IAm-logined', 'unknown'),
        ip=request.remote_addr,
    ))

@bp.route('/api/lures/render-html', methods=['POST'])
def api_lure_render_html():
    """Render a generated lure as a professional HTML email"""
    if 'IAm-logined' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    data = request.json
    return jsonify(artifactsvc.render_lure_html(
        subject=data.get('subject', ''),
        body=data.get('body', ''),
        variables=data.get('variables', {}),
    ))

@bp.route('/api/lures/bulk', methods=['POST'])
def api_lure_bulk():
    if 'IAm-logined' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    data = request.json
    return jsonify(artifactsvc.generate_bulk_lures(
        category=data.get('category', ''),
        template_index=data.get('template_index', 0),
        targets=data.get('targets', []),
        variables=data.get('variables', {}),
        lure_type=data.get('type', 'email'),
    ))

@bp.route('/api/lures/saved', methods=['GET'])
def api_saved_lures():
    if 'IAm-logined' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    return jsonify({'lures': artifactsvc.saved_lures()})

@bp.route('/api/lures/save', methods=['POST'])
def api_save_lure():
    if 'IAm-logined' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    data = request.json
    lure_id = artifactsvc.save_lure(
        name=data.get('name', 'Untitled Lure'),
        category=data.get('category', ''),
        lure_type=data.get('type', 'email'),
        subject=data.get('subject', ''),
        body=data.get('body', ''),
        variables=data.get('variables', {}),
    )
    return jsonify({'id': lure_id, 'status': 'saved'})

@bp.route('/api/lures/saved/<int:lure_id>', methods=['DELETE'])
def api_delete_lure(lure_id):
    if 'IAm-logined' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    artifactsvc.delete_saved_lure(lure_id)
    return jsonify({'status': 'deleted'})
