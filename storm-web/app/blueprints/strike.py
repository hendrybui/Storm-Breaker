"""strike blueprint (P14.6 -- fire a payload from the panel).

ADD-ONLY endpoints (NR-2).  ``POST /api/strike/reverse`` composes the firepower
organs (adapter -> runner -> listener/verify) and records the verified result as
evidence on a target (P14.3).  The response's ``ok`` is the *verified callback*.
"""
from __future__ import annotations

import dataclasses
import os

from flask import Blueprint, jsonify, request, session

from app.adapters import call as call_action
from app.exec.strike import launch_payload
from app.state import BASE_DIR
from app.targets import TargetStore

bp = Blueprint("strike", __name__,
               template_folder=os.path.join(BASE_DIR, "flask_templates"))

# Locally launchable payload types (blocking reverse shells caught by a listener).
RUNNABLE = ("python_reverse", "bash_reverse")


def _guard():
    if 'IAm-logined' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    return None


@bp.route('/api/strike/actions')
def api_strike_actions():
    bad = _guard()
    if bad:
        return bad
    types = sorted((call_action("payloads.types") or {}).keys())
    return jsonify({'payloads': types, 'runnable': list(RUNNABLE)})


@bp.route('/api/strike/reverse', methods=['POST'])
def api_strike_reverse():
    bad = _guard()
    if bad:
        return bad
    data = request.json or {}
    payload_type = data.get('payload_type', 'python_reverse')
    if payload_type not in RUNNABLE:
        return jsonify({'error': 'payload_type must be one of %s' % (list(RUNNABLE),)}), 400

    strike = launch_payload(payload_type, data.get('lhost', '127.0.0.1'),
                            int(data.get('lport', 0)))

    store = TargetStore()
    target = store.get_or_create(strike.target, name='strike:%s' % payload_type)
    finding = store.add_finding(target['id'], 'strike', strike.summary(), evidence={
        'payload_type': payload_type,
        'callback_ok': strike.callback.ok,
        'exec_exit': strike.exec.exit_code,
        'timed_out': strike.exec.timed_out,
        'artifact': strike.generated.get('filename'),
    })
    return jsonify({
        'status': 'ok',
        'ok': strike.ok,
        'summary': strike.summary(),
        'target_id': target['id'],
        'finding_id': finding['id'],
        'exec': strike.exec.as_dict(),
        'callback': dataclasses.asdict(strike.callback),
    })
