"""live blueprint (P10 -- additive realtime push channel).

ADD-ONLY endpoints (NR-2):

  GET /api/events   Server-Sent Events stream of bus events (operator panel)
  GET /api/live     JSON snapshot: recent events + listeners + beacon stats

Kept out of the audit catalogue: ``/api/events`` never returns (long-lived
stream), so a non-streaming client would block on it.
"""
from __future__ import annotations

import json
import os
import queue
import threading
import time
from collections import deque

from flask import Blueprint, Response, jsonify, request, session

from app.core.events import BUS
from app.exec import beacon
from app.exec.listener_service import get_service
from app.state import BASE_DIR

bp = Blueprint("live", __name__,
               template_folder=os.path.join(BASE_DIR, "flask_templates"))


def _guard():
    if 'IAm-logined' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    return None


# --- P16: webhook sink -----------------------------------------------------
# generic_webhook used to point at /panel, which is GET-only AND behind the
# auth gate -> the before_request gate 302'd to /login before routing, so the
# POSTed JSON was silently swallowed (requests quietly followed the redirect
# and got a 200).  This is a real receiver: bounded, lock-guarded, inspectable.
_INBOX = deque(maxlen=200)
_INBOX_LOCK = threading.Lock()


@bp.route('/api/notify/inbox', methods=['POST'])
def api_notify_inbox_post():
    """PUBLIC sink for generic_webhook deliveries (no session required)."""
    payload = request.get_json(silent=True)
    if payload is None:
        payload = request.get_data(as_text=True)[:8000]
    with _INBOX_LOCK:
        _INBOX.append({'ts': time.time(), 'payload': payload})
        count = len(_INBOX)
    return jsonify({'status': 'stored', 'count': count})


@bp.route('/api/notify/inbox')
def api_notify_inbox_get():
    """Operator read of the last delivered notifications."""
    bad = _guard()
    if bad:
        return bad
    with _INBOX_LOCK:
        items = list(_INBOX)
    return jsonify({'count': len(items), 'items': items[-100:]})


@bp.route('/api/notify/inbox/clear', methods=['POST'])
def api_notify_inbox_clear():
    bad = _guard()
    if bad:
        return bad
    with _INBOX_LOCK:
        _INBOX.clear()
    return jsonify({'status': 'cleared'})


@bp.route('/api/live')
def api_live():
    bad = _guard()
    if bad:
        return bad
    return jsonify({
        'events': BUS.recent(int(request.args.get('limit', 50))),
        'subscribers': BUS.subscribers(),
        'listeners': get_service().list(),
        'beacons': beacon.TRACKER.all_stats(),
        'profile': beacon.CONFIG.default(),
        'base_ms': beacon.CONFIG.base_ms(),
    })


@bp.route('/api/notify/pending')
def api_notify_pending():
    """P10.2 — cursor poll for the desktop shell's native notifications.

    Deliberately UNAUTHENTICATED: the Tauri shell polls it over loopback with
    no cookie jar. Read-only, so that is safe.
    """
    since = float(request.args.get('since', 0) or 0)
    events = [e for e in BUS.recent(int(request.args.get('limit', 100)))
              if e.get('ts', 0) > since]
    return jsonify({'events': events, 'now': time.time()})


@bp.route('/api/events')
def api_events():
    """SSE stream.  EventSource sends cookies, so the operator session applies."""
    sid, q = BUS.subscribe()
    heartbeat = float(request.args.get('heartbeat', 15))

    def stream():
        try:
            yield ': connected\n\n'
            last = time.time()
            while True:
                try:
                    event = q.get(timeout=1.0)
                    yield 'event: %s\ndata: %s\n\n' % (
                        event.get('kind', 'message'), json.dumps(event))
                    last = time.time()
                except queue.Empty:
                    if time.time() - last >= heartbeat:
                        yield ': keepalive\n\n'
                        last = time.time()
        finally:
            BUS.unsubscribe(sid)

    return Response(stream(), mimetype='text/event-stream',
                    headers={'Cache-Control': 'no-cache',
                             'X-Accel-Buffering': 'no'})
