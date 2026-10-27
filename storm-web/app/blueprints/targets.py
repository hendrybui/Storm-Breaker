"""targets blueprint (P14.3 -- additive target/evidence API).

ADD-ONLY endpoints (NR-2).  Targets are the operator's persistent aim; findings
are the evidence attached to them.
"""
from __future__ import annotations

import os

from flask import Blueprint, Response, jsonify, request, session

from app.state import BASE_DIR
from app.targets import TargetStore
from app.targets.report import render_html

bp = Blueprint("targets", __name__,
               template_folder=os.path.join(BASE_DIR, "flask_templates"))


def _guard():
    if 'IAm-logined' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    return None


@bp.route('/api/targets')
def api_targets_list():
    bad = _guard()
    if bad:
        return bad
    return jsonify({'targets': TargetStore().list()})


@bp.route('/api/targets', methods=['POST'])
def api_targets_create():
    bad = _guard()
    if bad:
        return bad
    data = request.json or {}
    name = (data.get('name') or data.get('host') or '').strip()
    if not name:
        return jsonify({'error': 'name (or host) required'}), 400
    target = TargetStore().create(name, host=data.get('host', ''), notes=data.get('notes', ''))
    return jsonify({'status': 'ok', 'target': target}), 200


@bp.route('/api/targets/<int:target_id>')
def api_target_detail(target_id):
    bad = _guard()
    if bad:
        return bad
    target = TargetStore().get(target_id)
    if target is None:
        return jsonify({'error': 'Target not found'}), 404
    return jsonify({'target': target})


@bp.route('/api/targets/<int:target_id>/report')
def api_target_report(target_id):
    bad = _guard()
    if bad:
        return bad
    target = TargetStore().get(target_id)
    if target is None:
        return jsonify({'error': 'Target not found'}), 404
    return Response(render_html(target), mimetype='text/html')


@bp.route('/api/targets/<int:target_id>/findings', methods=['POST'])
def api_target_add_finding(target_id):
    bad = _guard()
    if bad:
        return bad
    store = TargetStore()
    if store.get(target_id) is None:
        return jsonify({'error': 'Target not found'}), 404
    data = request.json or {}
    finding = store.add_finding(target_id, data.get('kind', 'note'),
                               data.get('detail', ''), data.get('evidence'))
    return jsonify({'status': 'ok', 'finding': finding}), 200
