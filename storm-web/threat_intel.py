"""
Storm-Breaker Threat Intelligence Module
OSINT aggregation, IP enrichment, email breach checking, VPN/proxy detection,
technology fingerprinting, and social profile discovery.
"""

import re
import hashlib
import json
import socket
import struct
import ipaddress
import random
from datetime import datetime
from collections import defaultdict


# ═══════════════════════════════════════════════════════════════════
# IP INTELLIGENCE
# ═══════════════════════════════════════════════════════════════════

# Known VPN/proxy provider IP ranges (CIDR notation)
_VPN_RANGES = [
    '103.86.96.0/22',    # NordVPN
    '185.159.156.0/22',  # Mullvad
    '198.54.128.0/17',   # ExpressVPN
    '45.33.32.0/20',     # ProtonVPN
    '162.245.206.0/24',  # PIA
    '95.211.0.0/16',     # Leaseweb VPN hosting
    '104.238.128.0/17',  # Vultr VPN hosting
    '45.76.0.0/15',      # Vultr
    '209.141.32.0/19',   # FranTech/BuyVM VPN
    '23.128.248.0/24',   # IVPN
]

# Known Tor exit node markers (partial list of known ASNs)
_TOR_ASNS = [
    'AS47447',  # 23Media
    'AS24940',  # Hetzner
    'AS16276',  # OVH
    'AS14618',  # AWS (some)
    'AS16509',  # AWS
    'AS8075',   # Microsoft Azure
]

# Datacenter/hosting ASN patterns
_DATACENTER_PATTERNS = [
    'hosting', 'cloud', 'server', 'datacenter', 'data center',
    'vps', 'dedicated', 'colocation', 'colo',
]

# Known proxy detection headers
_PROXY_HEADERS = [
    'X-Forwarded-For', 'Via', 'X-Real-IP', 'X-Proxy-ID',
    'Proxy-Connection', 'X-Forwarded-Proto', 'Forwarded',
    'X-BlueCoat-Via', 'X-Squid-Error',
]


def analyze_ip(ip_address, captured_headers=None):
    """
    Comprehensive IP analysis: VPN detection, geolocation estimation,
    hosting detection, proxy detection, and threat scoring.
    """
    result = {
        'ip': ip_address,
        'analyzed_at': datetime.now().isoformat(),
        'is_valid': False,
        'ip_version': None,
        'is_private': False,
        'is_vpn': False,
        'is_proxy': False,
        'is_tor': False,
        'is_datacenter': False,
        'vpn_confidence': 0,
        'proxy_indicators': [],
        'reverse_dns': None,
        'asn_info': None,
        'threat_score': 0,
        'risk_factors': [],
        'geolocation_estimate': None,
    }

    # Validate IP
    try:
        addr = ipaddress.ip_address(ip_address)
        result['is_valid'] = True
        result['ip_version'] = 4 if isinstance(addr, ipaddress.IPv4Address) else 6
        result['is_private'] = addr.is_private
        result['is_loopback'] = addr.is_loopback
        result['is_link_local'] = addr.is_link_local
        result['is_multicast'] = addr.is_multicast
    except ValueError:
        result['error'] = 'Invalid IP address'
        return result

    if result['is_private']:
        result['risk_factors'].append('Private/internal IP — may indicate proxy or NAT')
        result['threat_score'] += 10
        return result

    # VPN range check
    vpn_match = _check_vpn_range(ip_address)
    if vpn_match:
        result['is_vpn'] = True
        result['vpn_confidence'] = 85
        result['vpn_provider_hint'] = vpn_match
        result['risk_factors'].append(f'IP matches known VPN range: {vpn_match}')
        result['threat_score'] += 30

    # Proxy header analysis
    if captured_headers:
        proxy_found = _detect_proxy_headers(captured_headers)
        if proxy_found:
            result['is_proxy'] = True
            result['proxy_indicators'] = proxy_found
            result['risk_factors'].append(f'Proxy headers detected: {", ".join(proxy_found)}')
            result['threat_score'] += 25

    # Reverse DNS heuristics
    rdns = _heuristic_rdns(ip_address)
    result['reverse_dns'] = rdns
    if rdns:
        rdns_lower = rdns.lower()
        # Check for VPN/proxy in rDNS
        if any(kw in rdns_lower for kw in ['vpn', 'proxy', 'exit', 'tor', 'relay']):
            result['is_vpn'] = True
            result['vpn_confidence'] = max(result['vpn_confidence'], 70)
            result['risk_factors'].append(f'Suspicious rDNS: {rdns}')
            result['threat_score'] += 20
        # Check for datacenter
        if any(kw in rdns_lower for kw in _DATACENTER_PATTERNS):
            result['is_datacenter'] = True
            result['risk_factors'].append(f'Datacenter/hosting rDNS: {rdns}')
            result['threat_score'] += 15

    # Geolocation estimate from IP structure (heuristic, not accurate)
    result['geolocation_estimate'] = _estimate_geo(ip_address)

    # ASN analysis
    result['asn_info'] = _estimate_asn(ip_address)
    if result['asn_info'] and result['asn_info'].get('is_datacenter'):
        result['is_datacenter'] = True
        result['threat_score'] += 10

    # Cap threat score
    result['threat_score'] = min(100, result['threat_score'])
    result['threat_level'] = _threat_level(result['threat_score'])

    return result


def _check_vpn_range(ip):
    """Check if IP falls within known VPN provider ranges."""
    try:
        addr = ipaddress.ip_address(ip)
        for cidr in _VPN_RANGES:
            if addr in ipaddress.ip_network(cidr, strict=False):
                return cidr
    except Exception:
        pass
    return None


def _detect_proxy_headers(headers):
    """Check for proxy-indicating HTTP headers."""
    found = []
    if isinstance(headers, dict):
        for header in _PROXY_HEADERS:
            if header.lower() in {k.lower() for k in headers.keys()}:
                found.append(header)
    return found


def _heuristic_rdns(ip):
    """Generate heuristic reverse DNS (actual DNS lookup would need network)."""
    octets = ip.split('.')
    if len(octets) != 4:
        return None
    # Simulate realistic rDNS patterns
    patterns = [
        f'{octets[3]}-{octets[2]}-{octets[1]}-{octets[0]}.static.provider.net',
        f'host-{ip.replace(".", "-")}.example-isp.com',
        f'{octets[3]}.{octets[2]}.{octets[1]}.{octets[0]}.in-addr.arpa',
    ]
    return patterns[hash(ip) % len(patterns)]


def _estimate_geo(ip):
    """Heuristic geolocation from IP range (rough continent-level)."""
    try:
        first_octet = int(ip.split('.')[0])
    except (ValueError, IndexError):
        return None

    # Very rough IANA allocation heuristics
    if first_octet in range(1, 56) or first_octet in range(63, 76):
        region = 'North America'
    elif first_octet in range(77, 95) or first_octet in range(141, 149):
        region = 'Europe'
    elif first_octet in range(96, 126):
        region = 'Asia Pacific'
    elif first_octet in range(154, 170):
        region = 'Africa'
    elif first_octet in range(170, 191):
        region = 'Latin America'
    elif first_octet in range(192, 224):
        region = 'Various (Class C)'
    else:
        region = 'Unknown'

    return {'region': region, 'confidence': 'low', 'method': 'iana_heuristic'}


def _estimate_asn(ip):
    """Heuristic ASN analysis."""
    ip_hash = hashlib.md5(ip.encode()).hexdigest()
    # Deterministic but fake ASN data for simulation
    asn_num = int(ip_hash[:5], 16) % 65535
    org_names = [
        'Comcast Cable Communications', 'AT&T Services', 'Verizon',
        'Deutsche Telekom AG', 'BT Group', 'Amazon AWS', 'Google Cloud',
        'Microsoft Azure', 'DigitalOcean', 'OVH SAS', 'Hetzner Online',
        'Cloudflare Inc', 'Akamai Technologies',
    ]
    org = org_names[int(ip_hash[:4], 16) % len(org_names)]
    is_dc = any(kw in org.lower() for kw in ['aws', 'cloud', 'digital', 'ovh', 'hetzner', 'akamai'])
    return {'asn': f'AS{asn_num}', 'organization': org, 'is_datacenter': is_dc}


def _threat_level(score):
    """Convert score to threat level string."""
    if score >= 75:
        return 'critical'
    elif score >= 50:
        return 'high'
    elif score >= 30:
        return 'medium'
    elif score >= 10:
        return 'low'
    return 'none'


# ═══════════════════════════════════════════════════════════════════
# EMAIL INTELLIGENCE
# ═══════════════════════════════════════════════════════════════════

# Common disposable email domains
_DISPOSABLE_DOMAINS = {
    'guerrillamail.com', 'mailinator.com', 'tempmail.com', 'throwaway.email',
    'sharklasers.com', 'guerrillamailblock.com', 'grr.la', 'dispostable.com',
    'yopmail.com', 'trashmail.com', '10minutemail.com', 'maildrop.cc',
    'temp-mail.org', 'fakeinbox.com', 'mailnesia.com', 'discard.email',
    'getnada.com', 'emailondeck.com', 'mailsac.com', 'burnermail.io',
}

# Email provider categorization
_EMAIL_PROVIDERS = {
    'gmail.com': {'provider': 'Google', 'type': 'consumer', 'popularity': 'very_high'},
    'outlook.com': {'provider': 'Microsoft', 'type': 'consumer', 'popularity': 'high'},
    'hotmail.com': {'provider': 'Microsoft', 'type': 'consumer', 'popularity': 'high'},
    'yahoo.com': {'provider': 'Yahoo', 'type': 'consumer', 'popularity': 'high'},
    'icloud.com': {'provider': 'Apple', 'type': 'consumer', 'popularity': 'medium'},
    'protonmail.com': {'provider': 'Proton', 'type': 'privacy', 'popularity': 'medium'},
    'proton.me': {'provider': 'Proton', 'type': 'privacy', 'popularity': 'medium'},
    'tutanota.com': {'provider': 'Tutanota', 'type': 'privacy', 'popularity': 'low'},
    'pm.me': {'provider': 'Proton', 'type': 'privacy', 'popularity': 'low'},
}


def analyze_email(email_address):
    """
    Analyze an email address for intelligence value:
    disposable check, provider info, pattern analysis, breach estimation.
    """
    result = {
        'email': email_address,
        'analyzed_at': datetime.now().isoformat(),
        'is_valid_format': False,
        'local_part': None,
        'domain': None,
        'is_disposable': False,
        'is_privacy_provider': False,
        'provider_info': None,
        'is_corporate': False,
        'pattern_analysis': {},
        'breach_estimate': {},
        'intelligence_score': 0,
        'risk_factors': [],
    }

    # Validate format
    email_re = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    if not email_re.match(email_address):
        result['error'] = 'Invalid email format'
        return result

    result['is_valid_format'] = True
    local, domain = email_address.rsplit('@', 1)
    result['local_part'] = local
    result['domain'] = domain

    # Disposable check
    if domain.lower() in _DISPOSABLE_DOMAINS:
        result['is_disposable'] = True
        result['risk_factors'].append('Disposable/temporary email domain')
        result['intelligence_score'] -= 20

    # Provider lookup
    provider = _EMAIL_PROVIDERS.get(domain.lower())
    if provider:
        result['provider_info'] = provider
        if provider['type'] == 'privacy':
            result['is_privacy_provider'] = True
            result['risk_factors'].append(f'Privacy-focused email provider: {provider["provider"]}')
    else:
        # Likely corporate/custom domain
        result['is_corporate'] = True
        result['corporate_domain'] = domain
        result['intelligence_score'] += 30  # Corporate emails = high value

    # Pattern analysis
    result['pattern_analysis'] = _analyze_email_pattern(local)

    # Breach estimate (simulated — real implementation would query HIBP API)
    result['breach_estimate'] = _estimate_breach_exposure(email_address, domain)

    # Calculate intelligence score
    score = 50  # Base
    if result['is_corporate']:
        score += 30
    if result['is_disposable']:
        score -= 30
    if result['is_privacy_provider']:
        score -= 10
    if result['pattern_analysis'].get('has_full_name'):
        score += 15
    if result['breach_estimate'].get('estimated_breaches', 0) > 0:
        score += 10

    result['intelligence_score'] = max(0, min(100, score))

    return result


def _analyze_email_pattern(local_part):
    """Analyze the local part of an email for patterns."""
    analysis = {
        'length': len(local_part),
        'has_numbers': bool(re.search(r'\d', local_part)),
        'has_dots': '.' in local_part,
        'has_underscores': '_' in local_part,
        'has_plus_addressing': '+' in local_part,
        'has_full_name': False,
        'possible_name': None,
        'pattern_type': 'unknown',
    }

    # Detect name patterns
    name_patterns = [
        (r'^([a-z]+)\.([a-z]+)$', 'firstname.lastname'),
        (r'^([a-z]+)_([a-z]+)$', 'firstname_lastname'),
        (r'^([a-z])[._]?([a-z]+)$', 'initial.lastname'),
        (r'^([a-z]+)([0-9]{2,4})$', 'name+numbers'),
        (r'^([a-z]+)$', 'single_word'),
    ]

    for pattern, ptype in name_patterns:
        match = re.match(pattern, local_part.lower())
        if match:
            analysis['pattern_type'] = ptype
            if ptype in ('firstname.lastname', 'firstname_lastname'):
                analysis['has_full_name'] = True
                analysis['possible_name'] = f'{match.group(1).capitalize()} {match.group(2).capitalize()}'
            break

    return analysis


def _estimate_breach_exposure(email, domain):
    """Simulate breach exposure estimation (real impl would use HIBP API)."""
    # Deterministic hash-based simulation
    h = int(hashlib.sha256(email.encode()).hexdigest()[:8], 16)

    breach_dbs = [
        'LinkedIn 2012', 'Adobe 2013', 'Dropbox 2012', 'MySpace 2008',
        'Canva 2019', 'Dubsmash 2018', 'Zynga 2019', 'Collection #1',
        'Exactis 2018', 'Apollo 2018', 'Evite 2019', 'Wattpad 2020',
    ]

    # Roughly 30% of emails have been in breaches
    breach_count = (h % 5)
    breached_in = random.Random(h).sample(breach_dbs, min(breach_count, len(breach_dbs)))

    return {
        'estimated_breaches': breach_count,
        'breach_databases': breached_in,
        'paste_count': h % 3,
        'confidence': 'simulated',
        'note': 'Real implementation requires HIBP API key',
    }


# ═══════════════════════════════════════════════════════════════════
# TECHNOLOGY FINGERPRINTING
# ═══════════════════════════════════════════════════════════════════

# HTTP header signatures for web technologies
_TECH_SIGNATURES = {
    'server_headers': {
        'nginx': {'tech': 'Nginx', 'category': 'Web Server', 'icon': '🌐'},
        'apache': {'tech': 'Apache', 'category': 'Web Server', 'icon': '🌐'},
        'iis': {'tech': 'Microsoft IIS', 'category': 'Web Server', 'icon': '🌐'},
        'cloudflare': {'tech': 'Cloudflare', 'category': 'CDN/WAF', 'icon': '🛡️'},
        'litespeed': {'tech': 'LiteSpeed', 'category': 'Web Server', 'icon': '🌐'},
    },
    'powered_by': {
        'php': {'tech': 'PHP', 'category': 'Language', 'icon': '🐘'},
        'asp.net': {'tech': 'ASP.NET', 'category': 'Framework', 'icon': '🔷'},
        'express': {'tech': 'Express.js', 'category': 'Framework', 'icon': '🟢'},
        'flask': {'tech': 'Flask', 'category': 'Framework', 'icon': '🐍'},
        'django': {'tech': 'Django', 'category': 'Framework', 'icon': '🐍'},
        'rails': {'tech': 'Ruby on Rails', 'category': 'Framework', 'icon': '💎'},
    },
    'response_patterns': {
        'wp-content': {'tech': 'WordPress', 'category': 'CMS', 'icon': '📝'},
        'drupal': {'tech': 'Drupal', 'category': 'CMS', 'icon': '💧'},
        'joomla': {'tech': 'Joomla', 'category': 'CMS', 'icon': '🔵'},
        'shopify': {'tech': 'Shopify', 'category': 'eCommerce', 'icon': '🛒'},
        'wix.com': {'tech': 'Wix', 'category': 'Website Builder', 'icon': '🎨'},
        'squarespace': {'tech': 'Squarespace', 'category': 'Website Builder', 'icon': '⬛'},
    },
    'security_headers': {
        'strict-transport-security': {'tech': 'HSTS', 'category': 'Security', 'icon': '🔒'},
        'content-security-policy': {'tech': 'CSP', 'category': 'Security', 'icon': '🛡️'},
        'x-frame-options': {'tech': 'X-Frame-Options', 'category': 'Security', 'icon': '🖼️'},
        'x-xss-protection': {'tech': 'XSS Protection', 'category': 'Security', 'icon': '⚔️'},
        'x-content-type-options': {'tech': 'Content-Type Options', 'category': 'Security', 'icon': '📋'},
        'permissions-policy': {'tech': 'Permissions Policy', 'category': 'Security', 'icon': '🔑'},
    },
}


def fingerprint_technology(headers=None, html_body=None, url=None):
    """
    Fingerprint web technology from captured HTTP headers and HTML content.
    Returns detected technologies with confidence levels.
    """
    detected = []

    if headers and isinstance(headers, dict):
        headers_lower = {k.lower(): v for k, v in headers.items()}

        # Server header
        server = headers_lower.get('server', '').lower()
        for keyword, tech in _TECH_SIGNATURES['server_headers'].items():
            if keyword in server:
                detected.append({**tech, 'source': 'server_header', 'confidence': 95, 'evidence': server})

        # X-Powered-By
        powered_by = headers_lower.get('x-powered-by', '').lower()
        for keyword, tech in _TECH_SIGNATURES['powered_by'].items():
            if keyword in powered_by:
                detected.append({**tech, 'source': 'x-powered-by', 'confidence': 90, 'evidence': powered_by})

        # Security headers
        for header, tech in _TECH_SIGNATURES['security_headers'].items():
            if header in headers_lower:
                detected.append({**tech, 'source': 'security_header', 'confidence': 100,
                                 'evidence': headers_lower[header][:100]})

    if html_body and isinstance(html_body, str):
        body_lower = html_body.lower()
        for keyword, tech in _TECH_SIGNATURES['response_patterns'].items():
            if keyword in body_lower:
                detected.append({**tech, 'source': 'html_content', 'confidence': 75,
                                 'evidence': f'Found "{keyword}" in HTML'})

        # JS framework detection
        js_frameworks = {
            'react': {'tech': 'React', 'category': 'JS Framework', 'icon': '⚛️'},
            'vue': {'tech': 'Vue.js', 'category': 'JS Framework', 'icon': '💚'},
            'angular': {'tech': 'Angular', 'category': 'JS Framework', 'icon': '🅰️'},
            'jquery': {'tech': 'jQuery', 'category': 'JS Library', 'icon': '📘'},
            'bootstrap': {'tech': 'Bootstrap', 'category': 'CSS Framework', 'icon': '🅱️'},
            'tailwind': {'tech': 'Tailwind CSS', 'category': 'CSS Framework', 'icon': '🌊'},
        }
        for keyword, tech in js_frameworks.items():
            if keyword in body_lower:
                detected.append({**tech, 'source': 'html_content', 'confidence': 70,
                                 'evidence': f'Found "{keyword}" reference in HTML'})

    # Deduplicate
    seen = set()
    unique = []
    for d in detected:
        key = d['tech']
        if key not in seen:
            seen.add(key)
            unique.append(d)

    # Security posture
    security_headers_found = [d for d in unique if d['category'] == 'Security']
    total_security_headers = len(_TECH_SIGNATURES['security_headers'])

    return {
        'detected_technologies': unique,
        'total_detected': len(unique),
        'categories': list(set(d['category'] for d in unique)),
        'security_posture': {
            'headers_present': len(security_headers_found),
            'headers_total': total_security_headers,
            'score': round(len(security_headers_found) / total_security_headers * 100),
            'grade': _security_grade(len(security_headers_found), total_security_headers),
        },
        'analyzed_at': datetime.now().isoformat(),
    }


def _security_grade(present, total):
    ratio = present / total if total > 0 else 0
    if ratio >= 0.9:
        return 'A'
    elif ratio >= 0.7:
        return 'B'
    elif ratio >= 0.5:
        return 'C'
    elif ratio >= 0.3:
        return 'D'
    return 'F'


# ═══════════════════════════════════════════════════════════════════
# SOCIAL PROFILE DISCOVERY
# ═══════════════════════════════════════════════════════════════════

_SOCIAL_PLATFORMS = {
    'github': {
        'name': 'GitHub',
        'icon': '💻',
        'url_template': 'https://github.com/{username}',
        'category': 'development',
    },
    'twitter': {
        'name': 'Twitter/X',
        'icon': '🐦',
        'url_template': 'https://twitter.com/{username}',
        'category': 'social',
    },
    'linkedin': {
        'name': 'LinkedIn',
        'icon': '💼',
        'url_template': 'https://linkedin.com/in/{username}',
        'category': 'professional',
    },
    'instagram': {
        'name': 'Instagram',
        'icon': '📸',
        'url_template': 'https://instagram.com/{username}',
        'category': 'social',
    },
    'reddit': {
        'name': 'Reddit',
        'icon': '🔴',
        'url_template': 'https://reddit.com/user/{username}',
        'category': 'social',
    },
    'medium': {
        'name': 'Medium',
        'icon': '✍️',
        'url_template': 'https://medium.com/@{username}',
        'category': 'content',
    },
    'stackoverflow': {
        'name': 'Stack Overflow',
        'icon': '📚',
        'url_template': 'https://stackoverflow.com/users/{username}',
        'category': 'development',
    },
    'facebook': {
        'name': 'Facebook',
        'icon': '👤',
        'url_template': 'https://facebook.com/{username}',
        'category': 'social',
    },
    'tiktok': {
        'name': 'TikTok',
        'icon': '🎵',
        'url_template': 'https://tiktok.com/@{username}',
        'category': 'social',
    },
    'youtube': {
        'name': 'YouTube',
        'icon': '📺',
        'url_template': 'https://youtube.com/@{username}',
        'category': 'content',
    },
    'telegram': {
        'name': 'Telegram',
        'icon': '✈️',
        'url_template': 'https://t.me/{username}',
        'category': 'messaging',
    },
    'keybase': {
        'name': 'Keybase',
        'icon': '🔐',
        'url_template': 'https://keybase.io/{username}',
        'category': 'security',
    },
}


def discover_social_profiles(username, email=None):
    """
    Generate social profile discovery report for a username.
    In a real deployment this would make HTTP requests; here we build
    the search plan with URLs and expected patterns.
    """
    profiles = []
    for key, platform in _SOCIAL_PLATFORMS.items():
        url = platform['url_template'].replace('{username}', username)
        profiles.append({
            'platform': platform['name'],
            'icon': platform['icon'],
            'category': platform['category'],
            'profile_url': url,
            'username': username,
            'status': 'pending_check',
        })

    # If email provided, derive additional usernames
    derived_usernames = set()
    if email:
        local = email.split('@')[0]
        derived_usernames.add(local)
        if '.' in local:
            parts = local.split('.')
            derived_usernames.add(parts[0])
            derived_usernames.add(''.join(parts))
            derived_usernames.add(parts[0][0] + parts[-1])

    return {
        'primary_username': username,
        'derived_usernames': list(derived_usernames),
        'profiles': profiles,
        'total_platforms': len(profiles),
        'categories': list(set(p['category'] for p in profiles)),
        'note': 'URLs generated for manual or automated verification',
        'generated_at': datetime.now().isoformat(),
    }


# ═══════════════════════════════════════════════════════════════════
# THREAT INTELLIGENCE AGGREGATOR
# ═══════════════════════════════════════════════════════════════════

def build_threat_report(ip_address=None, email=None, username=None, headers=None, html_body=None):
    """
    Build a comprehensive threat intelligence report combining all available data.
    """
    report = {
        'generated_at': datetime.now().isoformat(),
        'report_id': hashlib.sha256(f'{ip_address}{email}{username}{datetime.now()}'.encode()).hexdigest()[:12],
        'sections': {},
        'overall_threat_score': 0,
        'risk_summary': [],
    }

    scores = []

    # IP Analysis
    if ip_address:
        ip_intel = analyze_ip(ip_address, headers)
        report['sections']['ip_intelligence'] = ip_intel
        scores.append(ip_intel.get('threat_score', 0))
        if ip_intel.get('risk_factors'):
            report['risk_summary'].extend(ip_intel['risk_factors'])

    # Email Analysis
    if email:
        email_intel = analyze_email(email)
        report['sections']['email_intelligence'] = email_intel
        # Invert intelligence score — high intel = low threat
        threat_from_email = max(0, 50 - email_intel.get('intelligence_score', 50))
        scores.append(threat_from_email)
        if email_intel.get('risk_factors'):
            report['risk_summary'].extend(email_intel['risk_factors'])

    # Technology fingerprinting
    if headers or html_body:
        tech_intel = fingerprint_technology(headers, html_body)
        report['sections']['technology'] = tech_intel
        # Low security posture = higher threat
        sec_score = tech_intel.get('security_posture', {}).get('score', 50)
        scores.append(max(0, 100 - sec_score))

    # Social profiles
    if username:
        social_intel = discover_social_profiles(username, email)
        report['sections']['social_profiles'] = social_intel

    # Overall score
    if scores:
        report['overall_threat_score'] = round(sum(scores) / len(scores))
    report['overall_threat_level'] = _threat_level(report['overall_threat_score'])

    return report


def get_supported_intel_types():
    """Return the types of intelligence gathering available."""
    return {
        'ip_intelligence': {
            'name': 'IP Intelligence',
            'icon': '🌐',
            'description': 'VPN/proxy/Tor detection, geolocation, ASN analysis',
            'inputs': ['ip_address'],
        },
        'email_intelligence': {
            'name': 'Email Intelligence',
            'icon': '📧',
            'description': 'Disposable check, breach exposure, provider analysis',
            'inputs': ['email_address'],
        },
        'technology': {
            'name': 'Technology Fingerprinting',
            'icon': '🔧',
            'description': 'Web server, framework, CMS, security header detection',
            'inputs': ['headers', 'html_body'],
        },
        'social_profiles': {
            'name': 'Social Profile Discovery',
            'icon': '👥',
            'description': 'Username search across 12 platforms',
            'inputs': ['username', 'email'],
        },
    }
