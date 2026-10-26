"""rat blueprint (P3 batch extract)."""
from __future__ import annotations

import os, json, base64
import uuid as uuid_module
from datetime import datetime, timedelta
from functools import wraps
from flask import (Blueprint, request, jsonify, redirect, url_for, render_template, send_from_directory, make_response, session, Response)
from app.state import *  # noqa: F401,F403  -- P3
from app.state import BASE_DIR, CONFIG, _decode_data_url, _save_mobile_capture
import database as db

import platform
bp = Blueprint("rat", __name__,
               template_folder=os.path.join(BASE_DIR, "flask_templates"))


@bp.route('/api/rat/recon', methods=['POST'])
def api_rat_recon():
    from rat_controller import deep_system_recon
    result = deep_system_recon()
    track_event('rat_recon')
    db.save_rat_operation('recon', 'System Reconnaissance', platform.system().lower(), {}, result, 'low')
    return jsonify(result)

@bp.route('/api/rat/persistence', methods=['POST'])
def api_rat_persistence():
    from rat_controller import generate_persistence
    data = request.get_json(force=True)
    os_type = data.get('os_type', 'windows')
    method = data.get('method', 'all')
    payload_cmd = data.get('payload_cmd', '')
    callback_url = data.get('callback_url', '')
    result = generate_persistence(os_type, method, payload_cmd, callback_url)
    track_event('rat_persistence')
    db.save_rat_operation('persistence', f'Persistence ({os_type})', os_type, data, result, 'high', 'T1547')
    return jsonify(result)

@bp.route('/api/rat/shells', methods=['POST'])
def api_rat_shells():
    from rat_controller import generate_reverse_shell
    data = request.get_json(force=True)
    shell_type = data.get('shell_type', 'all')
    lhost = data.get('lhost', '0.0.0.0')
    lport = data.get('lport', '4444')
    encoding = data.get('encoding', 'none')
    result = generate_reverse_shell(shell_type, lhost, lport, encoding)
    track_event('rat_shell')
    db.save_rat_operation('shell', f'Reverse Shell ({shell_type})', 'cross', data, result, 'critical', 'T1059')
    # Also save to shell sessions
    db.save_rat_shell(f'Shell-{shell_type}', shell_type, lhost, lport, '', json.dumps(result.get('shells', {})), encoding)
    return jsonify(result)

@bp.route('/api/rat/credentials/targets', methods=['GET'])
def api_rat_cred_targets():
    from rat_controller import get_credential_harvest_targets
    result = get_credential_harvest_targets()
    return jsonify(result)

@bp.route('/api/rat/lateral', methods=['POST'])
def api_rat_lateral():
    from rat_controller import generate_lateral_movement
    data = request.get_json(force=True)
    technique = data.get('technique', 'all')
    target_host = data.get('target_host', '')
    username = data.get('username', '')
    password = data.get('password', '')
    domain = data.get('domain', '')
    result = generate_lateral_movement(technique, target_host, username, password, domain)
    track_event('rat_lateral')
    db.save_rat_operation('lateral_movement', f'Lateral ({technique})', 'windows', data, result, 'critical', 'T1021')
    return jsonify(result)

@bp.route('/api/rat/anti-forensics', methods=['POST'])
def api_rat_antiforensics():
    from rat_controller import generate_anti_forensics
    data = request.get_json(force=True)
    action = data.get('action', 'all')
    target_os = data.get('target_os', 'windows')
    result = generate_anti_forensics(action, target_os)
    track_event('rat_antiforensics')
    db.save_rat_operation('anti_forensics', f'Anti-Forensics ({target_os})', target_os, data, result, 'critical', 'T1070')
    return jsonify(result)

@bp.route('/api/rat/cradles', methods=['POST'])
def api_rat_cradles():
    from rat_controller import generate_download_cradles
    data = request.get_json(force=True)
    payload_url = data.get('payload_url', '')
    output_path = data.get('output_path', 'payload.exe')
    result = generate_download_cradles(payload_url, output_path)
    track_event('rat_cradle')
    db.save_rat_operation('download_cradle', 'Download Cradle', 'cross', data, result, 'high', 'T1105')
    return jsonify(result)

@bp.route('/api/rat/injection', methods=['GET'])
def api_rat_injection():
    from rat_controller import get_injection_techniques
    result = get_injection_techniques()
    return jsonify(result)

@bp.route('/api/rat/c2-config', methods=['POST'])
def api_rat_c2_config():
    from rat_controller import build_c2_config
    data = request.get_json(force=True)
    result = build_c2_config(
        protocol=data.get('protocol', 'https'),
        domain=data.get('domain', ''),
        port=data.get('port', 443),
        jitter=data.get('jitter', 20),
        sleep=data.get('sleep', 60),
        kill_date=data.get('kill_date', ''),
        user_agent=data.get('user_agent', ''),
    )
    track_event('rat_c2_config')
    db.save_rat_operation('c2_config', 'C2 Configuration', 'cross', data, result, 'high')
    return jsonify(result)

@bp.route('/api/rat/encode', methods=['POST'])
def api_rat_encode():
    from rat_controller import encode_payload
    data = request.get_json(force=True)
    payload = data.get('payload', '')
    technique = data.get('technique', 'all')
    if not payload:
        return jsonify({'error': 'No payload provided'}), 400
    result = encode_payload(payload, technique)
    track_event('rat_encode')
    return jsonify(result)

@bp.route('/api/rat/tunnels', methods=['POST'])
def api_rat_tunnels():
    from rat_controller import build_tunnel_config
    data = request.get_json(force=True)
    result = build_tunnel_config(
        tunnel_type=data.get('tunnel_type', 'all'),
        local_port=data.get('local_port', 8080),
        remote_host=data.get('remote_host', ''),
        remote_port=data.get('remote_port', 80),
        proxy_port=data.get('proxy_port', 1080),
    )
    track_event('rat_tunnel')
    db.save_rat_operation('tunnel', 'Network Tunnel', 'cross', data, result, 'high', 'T1572')
    return jsonify(result)

@bp.route('/api/rat/history', methods=['GET'])
def api_rat_history():
    op_type = request.args.get('type')
    records = db.get_rat_operations(op_type)
    return jsonify({'records': records})

@bp.route('/api/rat/<int:record_id>', methods=['DELETE'])
def api_rat_delete(record_id):
    db.delete_rat_operation(record_id)
    return jsonify({'status': 'deleted'})
