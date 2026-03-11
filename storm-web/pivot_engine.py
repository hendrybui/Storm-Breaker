"""
Storm-Breaker Pivot Engine
Attack path planning, lateral movement mapping, credential reuse analysis,
privilege escalation suggestions, kill chain tracking, and attack surface scoring.
"""

import json
import hashlib
import re
from datetime import datetime
from collections import defaultdict


# ═══════════════════════════════════════════════════════════════════
# ATTACK GRAPH BUILDER
# ═══════════════════════════════════════════════════════════════════

# Common service ports and attack relevance
_SERVICE_MAP = {
    21: {'service': 'FTP', 'attack_value': 60, 'techniques': ['credential_bruteforce', 'anonymous_login', 'file_exfil']},
    22: {'service': 'SSH', 'attack_value': 85, 'techniques': ['credential_bruteforce', 'key_theft', 'tunnel_pivot']},
    23: {'service': 'Telnet', 'attack_value': 70, 'techniques': ['credential_bruteforce', 'sniffing']},
    25: {'service': 'SMTP', 'attack_value': 50, 'techniques': ['email_relay', 'user_enum']},
    53: {'service': 'DNS', 'attack_value': 40, 'techniques': ['zone_transfer', 'dns_tunnel']},
    80: {'service': 'HTTP', 'attack_value': 55, 'techniques': ['web_exploit', 'directory_traversal', 'xss']},
    110: {'service': 'POP3', 'attack_value': 45, 'techniques': ['credential_bruteforce', 'email_exfil']},
    135: {'service': 'MSRPC', 'attack_value': 75, 'techniques': ['dcom_exec', 'service_enum']},
    139: {'service': 'NetBIOS', 'attack_value': 70, 'techniques': ['smb_relay', 'null_session']},
    143: {'service': 'IMAP', 'attack_value': 45, 'techniques': ['credential_bruteforce', 'email_exfil']},
    389: {'service': 'LDAP', 'attack_value': 80, 'techniques': ['ldap_enum', 'credential_dump', 'kerberoasting']},
    443: {'service': 'HTTPS', 'attack_value': 55, 'techniques': ['web_exploit', 'api_abuse', 'cert_analysis']},
    445: {'service': 'SMB', 'attack_value': 90, 'techniques': ['psexec', 'smb_relay', 'pass_the_hash', 'eternalblue']},
    1433: {'service': 'MSSQL', 'attack_value': 85, 'techniques': ['credential_bruteforce', 'xp_cmdshell', 'linked_servers']},
    1521: {'service': 'Oracle', 'attack_value': 80, 'techniques': ['credential_bruteforce', 'tns_poison']},
    3306: {'service': 'MySQL', 'attack_value': 75, 'techniques': ['credential_bruteforce', 'udf_exploit', 'data_exfil']},
    3389: {'service': 'RDP', 'attack_value': 90, 'techniques': ['credential_bruteforce', 'bluekeep', 'rdp_hijack']},
    5432: {'service': 'PostgreSQL', 'attack_value': 75, 'techniques': ['credential_bruteforce', 'copy_exploit']},
    5900: {'service': 'VNC', 'attack_value': 65, 'techniques': ['credential_bruteforce', 'auth_bypass']},
    5985: {'service': 'WinRM', 'attack_value': 85, 'techniques': ['credential_auth', 'powershell_remoting']},
    6379: {'service': 'Redis', 'attack_value': 70, 'techniques': ['unauth_access', 'rce_via_lua', 'key_dump']},
    8080: {'service': 'HTTP-Alt', 'attack_value': 55, 'techniques': ['web_exploit', 'admin_panel']},
    8443: {'service': 'HTTPS-Alt', 'attack_value': 55, 'techniques': ['web_exploit', 'admin_panel']},
    27017: {'service': 'MongoDB', 'attack_value': 70, 'techniques': ['unauth_access', 'data_exfil']},
}

# MITRE ATT&CK technique mapping for lateral movement
_MITRE_LATERAL = {
    'psexec': {'id': 'T1569.002', 'name': 'System Services: Service Execution', 'tactic': 'Execution'},
    'smb_relay': {'id': 'T1557.001', 'name': 'LLMNR/NBT-NS Poisoning', 'tactic': 'Credential Access'},
    'pass_the_hash': {'id': 'T1550.002', 'name': 'Pass the Hash', 'tactic': 'Lateral Movement'},
    'credential_bruteforce': {'id': 'T1110', 'name': 'Brute Force', 'tactic': 'Credential Access'},
    'rdp_hijack': {'id': 'T1563.002', 'name': 'RDP Hijacking', 'tactic': 'Lateral Movement'},
    'powershell_remoting': {'id': 'T1021.006', 'name': 'Windows Remote Management', 'tactic': 'Lateral Movement'},
    'ssh_pivot': {'id': 'T1021.004', 'name': 'SSH', 'tactic': 'Lateral Movement'},
    'tunnel_pivot': {'id': 'T1572', 'name': 'Protocol Tunneling', 'tactic': 'Command and Control'},
    'web_exploit': {'id': 'T1190', 'name': 'Exploit Public-Facing Application', 'tactic': 'Initial Access'},
    'credential_dump': {'id': 'T1003', 'name': 'OS Credential Dumping', 'tactic': 'Credential Access'},
    'kerberoasting': {'id': 'T1558.003', 'name': 'Kerberoasting', 'tactic': 'Credential Access'},
    'data_exfil': {'id': 'T1041', 'name': 'Exfiltration Over C2 Channel', 'tactic': 'Exfiltration'},
    'key_theft': {'id': 'T1552.004', 'name': 'Private Keys', 'tactic': 'Credential Access'},
    'dcom_exec': {'id': 'T1021.003', 'name': 'DCOM', 'tactic': 'Lateral Movement'},
}


def build_attack_graph(discovered_hosts, credentials=None, sessions=None):
    """
    Build an attack graph from discovered network hosts, captured credentials,
    and active sessions. Returns nodes, edges, and recommended attack paths.
    """
    nodes = []
    edges = []
    attack_paths = []

    # Build host nodes
    for i, host in enumerate(discovered_hosts):
        ip = host.get('ip', host.get('host', f'host_{i}'))
        ports = host.get('ports', host.get('open_ports', []))
        os_hint = host.get('os', host.get('os_hint', 'Unknown'))

        # Parse ports
        parsed_ports = _parse_ports(ports)

        # Calculate attack surface score
        surface_score = _calculate_attack_surface(parsed_ports)

        node = {
            'id': f'host_{i}',
            'ip': ip,
            'os': os_hint,
            'ports': parsed_ports,
            'attack_surface_score': surface_score,
            'is_high_value': surface_score >= 70,
            'services': [p['service'] for p in parsed_ports],
            'available_techniques': [],
            'credential_matches': [],
        }

        # Collect all applicable techniques
        techniques = set()
        for port_info in parsed_ports:
            port_num = port_info.get('port')
            if port_num in _SERVICE_MAP:
                for tech in _SERVICE_MAP[port_num]['techniques']:
                    techniques.add(tech)
        node['available_techniques'] = list(techniques)

        nodes.append(node)

    # Match credentials to hosts
    if credentials:
        for node in nodes:
            matches = _match_credentials(node, credentials)
            node['credential_matches'] = matches
            if matches:
                node['attack_surface_score'] = min(100, node['attack_surface_score'] + 20)

    # Build edges (lateral movement paths between hosts)
    for i, src in enumerate(nodes):
        for j, dst in enumerate(nodes):
            if i == j:
                continue
            edge = _find_lateral_path(src, dst)
            if edge:
                edges.append(edge)

    # Find optimal attack paths
    attack_paths = _find_attack_paths(nodes, edges)

    # MITRE ATT&CK coverage
    all_techniques = set()
    for node in nodes:
        all_techniques.update(node['available_techniques'])
    mitre_coverage = []
    for tech in all_techniques:
        if tech in _MITRE_LATERAL:
            mitre_coverage.append(_MITRE_LATERAL[tech])

    return {
        'nodes': nodes,
        'edges': edges,
        'attack_paths': attack_paths,
        'total_hosts': len(nodes),
        'high_value_targets': sum(1 for n in nodes if n['is_high_value']),
        'total_lateral_paths': len(edges),
        'mitre_coverage': mitre_coverage,
        'mitre_technique_count': len(mitre_coverage),
        'generated_at': datetime.now().isoformat(),
    }


def _parse_ports(ports):
    """Normalize port data from various formats."""
    parsed = []
    if isinstance(ports, list):
        for p in ports:
            if isinstance(p, int):
                service_info = _SERVICE_MAP.get(p, {'service': f'port_{p}', 'attack_value': 30, 'techniques': []})
                parsed.append({'port': p, **service_info})
            elif isinstance(p, dict):
                port_num = p.get('port', 0)
                service_info = _SERVICE_MAP.get(port_num, {'service': p.get('service', f'port_{port_num}'), 'attack_value': 30, 'techniques': []})
                parsed.append({'port': port_num, **service_info})
            elif isinstance(p, str) and p.isdigit():
                port_num = int(p)
                service_info = _SERVICE_MAP.get(port_num, {'service': f'port_{port_num}', 'attack_value': 30, 'techniques': []})
                parsed.append({'port': port_num, **service_info})
    return parsed


def _calculate_attack_surface(ports):
    """Calculate attack surface score from open ports (0-100)."""
    if not ports:
        return 10

    scores = [p.get('attack_value', 30) for p in ports]
    # Weighted: highest port value + average of rest
    if len(scores) == 1:
        return scores[0]

    scores.sort(reverse=True)
    max_score = scores[0]
    avg_rest = sum(scores[1:]) / len(scores[1:])

    return min(100, int(max_score * 0.6 + avg_rest * 0.3 + len(ports) * 2))


def _match_credentials(node, credentials):
    """Find credentials that could work on a given host."""
    matches = []
    has_ssh = any(p['port'] == 22 for p in node['ports'])
    has_rdp = any(p['port'] == 3389 for p in node['ports'])
    has_smb = any(p['port'] == 445 for p in node['ports'])
    has_web = any(p['port'] in (80, 443, 8080, 8443) for p in node['ports'])
    has_db = any(p['port'] in (1433, 3306, 5432, 1521, 27017) for p in node['ports'])
    has_winrm = any(p['port'] == 5985 for p in node['ports'])

    for cred in credentials:
        cred_type = cred.get('type', '')
        username = cred.get('username', cred.get('value', ''))
        relevance = 'low'
        applicable_services = []

        if cred_type in ('password', 'credential_pair'):
            if has_ssh:
                applicable_services.append('SSH')
                relevance = 'high'
            if has_rdp:
                applicable_services.append('RDP')
                relevance = 'high'
            if has_smb:
                applicable_services.append('SMB')
                relevance = 'critical'
            if has_winrm:
                applicable_services.append('WinRM')
                relevance = 'critical'
            if has_db:
                applicable_services.append('Database')
                relevance = 'high'

        elif cred_type == 'api_key':
            if has_web:
                applicable_services.append('Web API')
                relevance = 'medium'

        elif cred_type == 'ssh_key':
            if has_ssh:
                applicable_services.append('SSH')
                relevance = 'critical'

        if applicable_services:
            matches.append({
                'credential': username[:30] + '...' if len(str(username)) > 30 else username,
                'type': cred_type,
                'applicable_services': applicable_services,
                'relevance': relevance,
            })

    return matches


def _find_lateral_path(src, dst):
    """Determine if lateral movement from src to dst is possible."""
    src_services = set(p.get('service', '') for p in src.get('ports', []))
    dst_ports = {p.get('port'): p for p in dst.get('ports', [])}

    methods = []

    # SMB lateral movement
    if 445 in dst_ports:
        methods.append({
            'technique': 'psexec',
            'mitre': 'T1569.002',
            'requirements': 'Admin credentials',
            'stealth': 'low',
        })
        if src.get('credential_matches'):
            methods.append({
                'technique': 'pass_the_hash',
                'mitre': 'T1550.002',
                'requirements': 'NTLM hash',
                'stealth': 'medium',
            })

    # RDP
    if 3389 in dst_ports:
        methods.append({
            'technique': 'rdp_hijack',
            'mitre': 'T1563.002',
            'requirements': 'Valid credentials or session token',
            'stealth': 'low',
        })

    # SSH
    if 22 in dst_ports:
        methods.append({
            'technique': 'ssh_pivot',
            'mitre': 'T1021.004',
            'requirements': 'SSH credentials or key',
            'stealth': 'high',
        })

    # WinRM
    if 5985 in dst_ports:
        methods.append({
            'technique': 'powershell_remoting',
            'mitre': 'T1021.006',
            'requirements': 'Admin credentials',
            'stealth': 'medium',
        })

    # DCOM
    if 135 in dst_ports:
        methods.append({
            'technique': 'dcom_exec',
            'mitre': 'T1021.003',
            'requirements': 'Admin credentials',
            'stealth': 'low',
        })

    if not methods:
        return None

    return {
        'source': src['id'],
        'source_ip': src['ip'],
        'target': dst['id'],
        'target_ip': dst['ip'],
        'methods': methods,
        'best_method': max(methods, key=lambda m: {'high': 3, 'medium': 2, 'low': 1}.get(m['stealth'], 0)),
        'path_score': min(100, sum(20 for m in methods)),
    }


def _find_attack_paths(nodes, edges):
    """Find recommended attack paths through the network."""
    paths = []

    # Sort nodes by attack surface score
    high_value = sorted(nodes, key=lambda n: n['attack_surface_score'], reverse=True)

    for target in high_value[:5]:  # Top 5 targets
        # Find all edges leading to this target
        incoming = [e for e in edges if e['target'] == target['id']]
        if incoming:
            best_edge = max(incoming, key=lambda e: e['path_score'])
            paths.append({
                'target': target['ip'],
                'target_id': target['id'],
                'attack_surface_score': target['attack_surface_score'],
                'pivot_from': best_edge['source_ip'],
                'method': best_edge['best_method'],
                'all_methods': len(best_edge['methods']),
                'high_value_services': [s for s in target['services'] if s in ('SMB', 'RDP', 'SSH', 'LDAP', 'WinRM')],
                'credential_matches': len(target.get('credential_matches', [])),
                'priority': 'critical' if target['attack_surface_score'] >= 80 else 'high' if target['attack_surface_score'] >= 60 else 'medium',
            })

    paths.sort(key=lambda p: p['attack_surface_score'], reverse=True)
    return paths


# ═══════════════════════════════════════════════════════════════════
# CREDENTIAL REUSE MAPPER
# ═══════════════════════════════════════════════════════════════════

def map_credential_reuse(credentials, discovered_hosts):
    """
    Map captured credentials against discovered hosts to identify
    credential reuse opportunities.
    """
    reuse_map = []

    for cred in credentials:
        cred_id = cred.get('id', hashlib.md5(str(cred).encode()).hexdigest()[:8])
        username = cred.get('username', cred.get('value', 'unknown'))
        cred_type = cred.get('type', 'unknown')

        applicable_hosts = []
        for host in discovered_hosts:
            ip = host.get('ip', host.get('host', ''))
            ports = host.get('ports', host.get('open_ports', []))
            parsed = _parse_ports(ports)

            services = _applicable_services_for_cred(parsed, cred_type)
            if services:
                applicable_hosts.append({
                    'ip': ip,
                    'services': services,
                    'technique': 'credential_bruteforce' if cred_type in ('password', 'credential_pair') else 'api_auth',
                })

        if applicable_hosts:
            reuse_map.append({
                'credential_id': cred_id,
                'username': username[:30],
                'type': cred_type,
                'applicable_host_count': len(applicable_hosts),
                'hosts': applicable_hosts,
                'reuse_risk': 'critical' if len(applicable_hosts) >= 3 else 'high' if len(applicable_hosts) >= 2 else 'medium',
            })

    return {
        'credentials_analyzed': len(credentials),
        'reusable_credentials': len(reuse_map),
        'reuse_map': reuse_map,
        'total_attack_opportunities': sum(r['applicable_host_count'] for r in reuse_map),
        'generated_at': datetime.now().isoformat(),
    }


def _applicable_services_for_cred(ports, cred_type):
    """Determine which services a credential type can target."""
    services = []
    auth_ports = {22: 'SSH', 3389: 'RDP', 445: 'SMB', 5985: 'WinRM',
                  1433: 'MSSQL', 3306: 'MySQL', 5432: 'PostgreSQL', 21: 'FTP'}
    for port_info in ports:
        p = port_info.get('port')
        if cred_type in ('password', 'credential_pair') and p in auth_ports:
            services.append(auth_ports[p])
        elif cred_type == 'api_key' and p in (80, 443, 8080, 8443):
            services.append('Web API')
    return services


# ═══════════════════════════════════════════════════════════════════
# PRIVILEGE ESCALATION KNOWLEDGE BASE
# ═══════════════════════════════════════════════════════════════════

_PRIVESC_TECHNIQUES = {
    'windows': [
        {
            'name': 'Unquoted Service Path',
            'id': 'PRIVESC-W001',
            'mitre': 'T1574.009',
            'difficulty': 'easy',
            'description': 'Services with unquoted paths containing spaces allow DLL hijacking',
            'check': 'wmic service get name,displayname,pathname,startmode | findstr /i "auto" | findstr /i /v "c:\\windows" | findstr /i /v """',
            'exploit': 'Place malicious executable in the path before the space',
            'impact': 'SYSTEM',
        },
        {
            'name': 'Always Install Elevated',
            'id': 'PRIVESC-W002',
            'mitre': 'T1548.002',
            'difficulty': 'easy',
            'description': 'MSI packages always install with elevated privileges',
            'check': 'reg query HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\Installer /v AlwaysInstallElevated',
            'exploit': 'msiexec /quiet /qn /i malicious.msi',
            'impact': 'SYSTEM',
        },
        {
            'name': 'DLL Hijacking',
            'id': 'PRIVESC-W003',
            'mitre': 'T1574.001',
            'difficulty': 'medium',
            'description': 'Replace or inject DLLs loaded by privileged processes',
            'check': 'Process Monitor: filter for "NAME NOT FOUND" DLL loads from writable paths',
            'exploit': 'Place crafted DLL in the DLL search order path',
            'impact': 'Process privilege level',
        },
        {
            'name': 'Token Impersonation (Potato)',
            'id': 'PRIVESC-W004',
            'mitre': 'T1134.001',
            'difficulty': 'medium',
            'description': 'Impersonate tokens via SeImpersonatePrivilege',
            'check': 'whoami /priv | findstr SeImpersonatePrivilege',
            'exploit': 'JuicyPotato, PrintSpoofer, GodPotato',
            'impact': 'SYSTEM',
        },
        {
            'name': 'Stored Credentials',
            'id': 'PRIVESC-W005',
            'mitre': 'T1552.001',
            'difficulty': 'easy',
            'description': 'Credentials stored in registry, files, or credential manager',
            'check': 'cmdkey /list && dir /s /b *pass*.txt *cred*.xml unattend.xml',
            'exploit': 'runas /savecred /user:admin cmd.exe',
            'impact': 'Stored user privilege level',
        },
        {
            'name': 'Scheduled Task Manipulation',
            'id': 'PRIVESC-W006',
            'mitre': 'T1053.005',
            'difficulty': 'medium',
            'description': 'Modify or create scheduled tasks running as SYSTEM',
            'check': 'schtasks /query /fo LIST /v | findstr /i "run as"',
            'exploit': 'Replace task binary or create new task with SYSTEM privileges',
            'impact': 'SYSTEM',
        },
    ],
    'linux': [
        {
            'name': 'SUID Binary Exploitation',
            'id': 'PRIVESC-L001',
            'mitre': 'T1548.001',
            'difficulty': 'easy',
            'description': 'Exploit binaries with SUID bit set to escalate privileges',
            'check': 'find / -perm -4000 -type f 2>/dev/null',
            'exploit': 'Check GTFOBins for SUID exploitation of found binaries',
            'impact': 'root',
        },
        {
            'name': 'Sudo Misconfiguration',
            'id': 'PRIVESC-L002',
            'mitre': 'T1548.003',
            'difficulty': 'easy',
            'description': 'Exploit overly permissive sudo rules',
            'check': 'sudo -l',
            'exploit': 'Check GTFOBins for sudo exploitation of allowed commands',
            'impact': 'root',
        },
        {
            'name': 'Kernel Exploit',
            'id': 'PRIVESC-L003',
            'mitre': 'T1068',
            'difficulty': 'hard',
            'description': 'Exploit kernel vulnerabilities for privilege escalation',
            'check': 'uname -r && cat /etc/os-release',
            'exploit': 'DirtyPipe (CVE-2022-0847), DirtyCow (CVE-2016-5195)',
            'impact': 'root',
        },
        {
            'name': 'Cron Job Exploitation',
            'id': 'PRIVESC-L004',
            'mitre': 'T1053.003',
            'difficulty': 'medium',
            'description': 'Exploit writable cron scripts or wildcard injection',
            'check': 'cat /etc/crontab && ls -la /etc/cron.* && crontab -l',
            'exploit': 'Modify writable cron scripts or use tar wildcard injection',
            'impact': 'Cron user (often root)',
        },
        {
            'name': 'Writable /etc/passwd',
            'id': 'PRIVESC-L005',
            'mitre': 'T1098',
            'difficulty': 'easy',
            'description': 'Add new root user if /etc/passwd is writable',
            'check': 'ls -la /etc/passwd',
            'exploit': 'echo "root2:$(openssl passwd -1 password):0:0::/root:/bin/bash" >> /etc/passwd',
            'impact': 'root',
        },
        {
            'name': 'Capabilities Exploitation',
            'id': 'PRIVESC-L006',
            'mitre': 'T1548',
            'difficulty': 'medium',
            'description': 'Exploit Linux capabilities on binaries',
            'check': 'getcap -r / 2>/dev/null',
            'exploit': 'Exploit cap_setuid, cap_net_raw, cap_dac_read_search capabilities',
            'impact': 'root (depending on capability)',
        },
    ],
}


def get_privesc_techniques(os_type=None):
    """Return privilege escalation techniques, optionally filtered by OS."""
    if os_type:
        os_key = os_type.lower()
        if os_key in ('windows', 'win', 'win32', 'win64'):
            return {'os': 'windows', 'techniques': _PRIVESC_TECHNIQUES['windows']}
        elif os_key in ('linux', 'unix', 'macos', 'darwin'):
            return {'os': 'linux', 'techniques': _PRIVESC_TECHNIQUES['linux']}
    return _PRIVESC_TECHNIQUES


def suggest_privesc(os_type, current_user, available_info=None):
    """
    Suggest privilege escalation paths based on current access level and available info.
    """
    os_key = 'windows' if any(k in os_type.lower() for k in ('win', 'nt', 'windows')) else 'linux'
    techniques = _PRIVESC_TECHNIQUES.get(os_key, [])

    suggestions = []
    for tech in techniques:
        priority = 'recommended'
        if tech['difficulty'] == 'easy':
            priority = 'try_first'
        elif tech['difficulty'] == 'hard':
            priority = 'last_resort'

        suggestions.append({
            **tech,
            'priority': priority,
            'estimated_time': '5min' if tech['difficulty'] == 'easy' else '15min' if tech['difficulty'] == 'medium' else '30min+',
        })

    # Sort: easy first
    difficulty_order = {'easy': 0, 'medium': 1, 'hard': 2}
    suggestions.sort(key=lambda s: difficulty_order.get(s['difficulty'], 3))

    return {
        'os': os_key,
        'current_user': current_user,
        'total_techniques': len(suggestions),
        'suggestions': suggestions,
        'quick_wins': [s for s in suggestions if s['difficulty'] == 'easy'],
        'generated_at': datetime.now().isoformat(),
    }


# ═══════════════════════════════════════════════════════════════════
# KILL CHAIN TRACKER
# ═══════════════════════════════════════════════════════════════════

KILL_CHAIN_PHASES = {
    'reconnaissance': {
        'name': 'Reconnaissance',
        'icon': '🔍',
        'phase': 1,
        'description': 'Information gathering on target',
        'indicators': ['fingerprint', 'network_scan', 'social_profile', 'email_intel', 'tech_fingerprint'],
    },
    'weaponization': {
        'name': 'Weaponization',
        'icon': '⚔️',
        'phase': 2,
        'description': 'Payload creation and obfuscation',
        'indicators': ['payload_generated', 'obfuscation', 'lure_created'],
    },
    'delivery': {
        'name': 'Delivery',
        'icon': '📧',
        'phase': 3,
        'description': 'Delivering payload to target',
        'indicators': ['lure_sent', 'phishing_link', 'campaign_link_click'],
    },
    'exploitation': {
        'name': 'Exploitation',
        'icon': '💥',
        'phase': 4,
        'description': 'Exploiting vulnerability or social engineering',
        'indicators': ['template_visit', 'camera_capture', 'mic_capture', 'location_capture'],
    },
    'installation': {
        'name': 'Installation',
        'icon': '📥',
        'phase': 5,
        'description': 'Establishing persistence',
        'indicators': ['c2_register', 'mobile_register', 'backdoor_install'],
    },
    'command_control': {
        'name': 'Command & Control',
        'icon': '🎮',
        'phase': 6,
        'description': 'Remote access and control',
        'indicators': ['c2_command', 'mobile_command', 'c2_response'],
    },
    'actions': {
        'name': 'Actions on Objectives',
        'icon': '🎯',
        'phase': 7,
        'description': 'Achieving mission goals',
        'indicators': ['credential_capture', 'browser_exfil', 'data_export', 'lateral_movement', 'privesc'],
    },
}


def track_kill_chain(events):
    """
    Map a list of events to kill chain phases and calculate coverage.
    events: list of dicts with 'type' and optional 'timestamp', 'details'
    """
    phase_status = {}
    for key, phase in KILL_CHAIN_PHASES.items():
        matching = [e for e in events if e.get('type') in phase['indicators']]
        phase_status[key] = {
            **phase,
            'completed': len(matching) > 0,
            'event_count': len(matching),
            'events': matching[:5],
            'first_event': matching[0].get('timestamp') if matching else None,
        }

    completed = sum(1 for p in phase_status.values() if p['completed'])
    total = len(KILL_CHAIN_PHASES)

    return {
        'phases': phase_status,
        'completed_phases': completed,
        'total_phases': total,
        'coverage_percent': round(completed / total * 100),
        'next_phase': _next_phase(phase_status),
        'kill_chain_complete': completed == total,
        'assessed_at': datetime.now().isoformat(),
    }


def _next_phase(phase_status):
    """Find the next incomplete phase."""
    for key in sorted(phase_status, key=lambda k: phase_status[k]['phase']):
        if not phase_status[key]['completed']:
            return {
                'phase': key,
                'name': phase_status[key]['name'],
                'description': phase_status[key]['description'],
                'needed_events': phase_status[key]['indicators'],
            }
    return None  # All complete


# ═══════════════════════════════════════════════════════════════════
# ATTACK SURFACE SCORING
# ═══════════════════════════════════════════════════════════════════

def score_attack_surface(hosts, credentials, sessions, browser_exfil):
    """
    Calculate overall attack surface score from all gathered intelligence.
    """
    scores = {
        'network_exposure': 0,
        'credential_coverage': 0,
        'session_control': 0,
        'data_access': 0,
    }

    # Network exposure
    if hosts:
        total_ports = sum(len(h.get('ports', h.get('open_ports', []))) for h in hosts)
        high_value_ports = 0
        for h in hosts:
            ports = h.get('ports', h.get('open_ports', []))
            for p in ports:
                port_num = p if isinstance(p, int) else p.get('port', 0)
                if port_num in (445, 3389, 22, 5985, 1433, 389):
                    high_value_ports += 1
        scores['network_exposure'] = min(100, len(hosts) * 10 + high_value_ports * 15)

    # Credential coverage
    if credentials:
        cred_types = set(c.get('type', '') for c in credentials)
        scores['credential_coverage'] = min(100, len(credentials) * 15 + len(cred_types) * 10)

    # Session control
    if sessions:
        scores['session_control'] = min(100, len(sessions) * 20)

    # Data access
    if browser_exfil:
        scores['data_access'] = min(100, len(browser_exfil) * 10)

    overall = sum(scores.values()) / len(scores) if scores else 0

    return {
        'scores': scores,
        'overall_score': round(overall),
        'grade': _grade(overall),
        'summary': _surface_summary(scores),
        'assessed_at': datetime.now().isoformat(),
    }


def _grade(score):
    if score >= 80:
        return 'Critical Exposure'
    elif score >= 60:
        return 'High Exposure'
    elif score >= 40:
        return 'Moderate Exposure'
    elif score >= 20:
        return 'Low Exposure'
    return 'Minimal Exposure'


def _surface_summary(scores):
    summaries = []
    if scores['network_exposure'] >= 60:
        summaries.append('Significant network attack surface — multiple high-value services exposed')
    if scores['credential_coverage'] >= 60:
        summaries.append('Strong credential coverage — multiple credential types captured')
    if scores['session_control'] >= 60:
        summaries.append('Active session control — C2/mobile sessions established')
    if scores['data_access'] >= 60:
        summaries.append('Extensive data access — browser exfiltration yielding results')
    if not summaries:
        summaries.append('Limited attack surface — additional reconnaissance recommended')
    return summaries


def get_pivot_capabilities():
    """Return available pivot engine capabilities."""
    return {
        'attack_graph': {
            'name': 'Attack Graph Builder',
            'icon': '🕸️',
            'description': 'Build network attack graph from discovered hosts and credentials',
        },
        'credential_reuse': {
            'name': 'Credential Reuse Mapper',
            'icon': '🔑',
            'description': 'Map captured credentials to applicable hosts and services',
        },
        'privesc': {
            'name': 'Privilege Escalation',
            'icon': '⬆️',
            'description': 'Suggest privesc techniques for Windows and Linux',
        },
        'kill_chain': {
            'name': 'Kill Chain Tracker',
            'icon': '⛓️',
            'description': 'Track progress through the cyber kill chain phases',
        },
        'attack_surface': {
            'name': 'Attack Surface Scoring',
            'icon': '📊',
            'description': 'Score overall attack surface from all gathered data',
        },
    }
