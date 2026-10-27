"""outbox blueprint (P1.3) -- operator surface for the notification outbox.

ADD-ONLY (NR-2): new ``/api/notifications/*`` routes; nothing existing moves.

Inspect, retry, replay and purge durable notification deliveries that the
worker in :mod:`app.core.outbox` has queued.
"""
from __future__ import annotations

import os

from flask import Blueprint, jsonify, request, session

from app.core import outbox
from app.state import BASE_DIR

bp = Blueprint("outbox", __name__,
               template_folder=os.path.join(BASE_DIR, "flask_templates"))


def _guard():
    if 'IAm-logined' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    return None


@bp.route('/api/notifications/outbox')
def api_outbox_list():
    bad = _guard()
    if bad:
        return bad
    limit = min(int(request.args.get('limit', 100)), 1000)
    status = request.args.get('status')
    return jsonify({'items': outbox.list_rows(limit=limit, status=status),
                    'stats': outbox.stats(), 'worker_running': outbox.running()})


@bp.route('/api/notifications/stats')
def api_outbox_stats():
    bad = _guard()
    if bad:
        return bad
    return jsonify({'stats': outbox.stats(), 'worker_running': outbox.running(),
                    'max_attempts': outbox.MAX_ATTEMPTS})


@bp.route('/api/notifications/outbox/<int:row_id>/retry', methods=['POST'])
def api_outbox_retry(row_id):
    bad = _guard()
    if bad:
        return bad
    queued = outbox.retry(row_id)
    if not queued:
        return jsonify({'error': 'not found, or already delivered'}), 404
    return jsonify({'status': 'requeued', 'id': row_id})


@bp.route('/api/notifications/outbox/replay', methods=['POST'])
def api_outbox_replay():
    bad = _guard()
    if bad:
        return bad
    return jsonify({'status': 'ok', 'requeued': outbox.replay_failed()})


@bp.route('/api/notifications/outbox/purge', methods=['POST'])
def api_outbox_purge():
    bad = _guard()
    if bad:
        return bad
    return jsonify({'status': 'ok', 'removed': outbox.purge_delivered()})


@bp.route('/api/notifications/outbox/drain', methods=['POST'])
def api_outbox_drain():
    """Force one delivery sweep now instead of waiting for the worker tick."""
    bad = _guard()
    if bad:
        return bad
    return jsonify({'status': 'ok', 'delivered_now': outbox.deliver_due(),
                    'stats': outbox.stats()})
