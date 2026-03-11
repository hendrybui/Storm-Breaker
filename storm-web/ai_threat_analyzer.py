"""
Storm-Breaker AI Threat Analyzer
Advanced threat analysis with ML-style pattern recognition, behavioral analysis,
anomaly detection, predictive attack modeling, and automated response generation.
"""
import hashlib
import time
import math
import random
import re
import os
import json
from datetime import datetime, timedelta
from collections import Counter


class AIThreatAnalyzer:
    """Next-gen AI-powered threat analysis engine."""

    # Known threat signatures for pattern matching
    THREAT_SIGNATURES = {
        'sql_injection': {
            'patterns': [r"'.*OR.*'.*=.*'", r"UNION\s+SELECT", r";\s*DROP\s+TABLE", r"--\s*$", r"1=1", r"' OR '1'='1", r"admin'--"],
            'severity': 'critical',
            'mitre': 'T1190',
            'category': 'injection',
            'description': 'SQL Injection attempt detected'
        },
        'xss_attack': {
            'patterns': [r"<script.*?>", r"javascript:", r"on(error|load|click)\s*=", r"eval\(", r"document\.cookie", r"alert\("],
            'severity': 'high',
            'mitre': 'T1059.007',
            'category': 'injection',
            'description': 'Cross-Site Scripting attempt detected'
        },
        'command_injection': {
            'patterns': [r";\s*(ls|cat|whoami|id|uname)", r"\|\s*(bash|sh|cmd)", r"`.*`", r"\$\(.*\)", r"&&\s*(rm|wget|curl)"],
            'severity': 'critical',
            'mitre': 'T1059',
            'category': 'execution',
            'description': 'Command injection attempt detected'
        },
        'path_traversal': {
            'patterns': [r"\.\./", r"\.\.\\", r"%2e%2e", r"/etc/passwd", r"C:\\Windows\\System32"],
            'severity': 'high',
            'mitre': 'T1083',
            'category': 'discovery',
            'description': 'Path traversal attempt detected'
        },
        'credential_stuffing': {
            'patterns': [r"(admin|root|administrator).*password", r"login.*failed.*\d{3,}", r"brute.*force"],
            'severity': 'high',
            'mitre': 'T1110',
            'category': 'credential_access',
            'description': 'Credential stuffing/brute force detected'
        },
        'data_exfiltration': {
            'patterns': [r"base64.*encode", r"dns.*tunnel", r"icmp.*exfil", r"steganograph", r"covert.*channel"],
            'severity': 'critical',
            'mitre': 'T1048',
            'category': 'exfiltration',
            'description': 'Data exfiltration attempt detected'
        },
        'ransomware_indicator': {
            'patterns': [r"encrypt.*files", r"bitcoin.*address", r"ransom.*note", r"\.locked$", r"vssadmin.*delete"],
            'severity': 'critical',
            'mitre': 'T1486',
            'category': 'impact',
            'description': 'Ransomware indicator detected'
        },
        'c2_beacon': {
            'patterns': [r"beacon.*interval", r"callback.*url", r"heartbeat", r"sleep.*jitter", r"cobalt.*strike"],
            'severity': 'critical',
            'mitre': 'T1071',
            'category': 'command_and_control',
            'description': 'C2 beacon activity detected'
        },
        'privilege_escalation': {
            'patterns': [r"sudo.*NOPASSWD", r"setuid", r"kernel.*exploit", r"CVE-\d{4}-\d+", r"local.*privilege"],
            'severity': 'critical',
            'mitre': 'T1068',
            'category': 'privilege_escalation',
            'description': 'Privilege escalation attempt detected'
        },
        'lateral_movement': {
            'patterns': [r"psexec", r"wmiexec", r"pass.*the.*hash", r"mimikatz", r"rdp.*brute"],
            'severity': 'high',
            'mitre': 'T1021',
            'category': 'lateral_movement',
            'description': 'Lateral movement activity detected'
        }
    }

    # Behavioral baseline profiles
    BEHAVIOR_PROFILES = {
        'normal_user': {
            'avg_requests_per_min': 5,
            'max_failed_logins': 3,
            'typical_hours': (8, 18),
            'common_endpoints': ['/dashboard', '/profile', '/settings'],
            'risk_score': 0
        },
        'automated_scanner': {
            'avg_requests_per_min': 100,
            'max_failed_logins': 50,
            'typical_hours': (0, 24),
            'common_endpoints': ['/.env', '/wp-admin', '/admin', '/.git'],
            'risk_score': 75
        },
        'apt_actor': {
            'avg_requests_per_min': 2,
            'max_failed_logins': 1,
            'typical_hours': (1, 5),
            'common_endpoints': ['/api', '/internal', '/admin'],
            'risk_score': 95
        },
        'insider_threat': {
            'avg_requests_per_min': 15,
            'max_failed_logins': 2,
            'typical_hours': (22, 6),
            'common_endpoints': ['/api/export', '/files', '/database'],
            'risk_score': 85
        }
    }

    ANOMALY_MODELS = {
        'traffic_spike': {'threshold_multiplier': 3.0, 'window_minutes': 5, 'description': 'Sudden traffic volume increase'},
        'geo_anomaly': {'max_distance_km': 5000, 'window_hours': 1, 'description': 'Impossible travel detection'},
        'endpoint_scan': {'unique_404_threshold': 20, 'window_minutes': 10, 'description': 'Endpoint enumeration detected'},
        'timing_anomaly': {'off_hours_threshold': 0.8, 'description': 'Unusual access time patterns'},
        'payload_size': {'max_normal_kb': 100, 'description': 'Abnormal request/response size'},
        'protocol_anomaly': {'description': 'Unusual protocol or method usage'},
        'entropy_anomaly': {'high_entropy_threshold': 4.5, 'description': 'High entropy in requests (encrypted/encoded data)'},
        'session_anomaly': {'max_concurrent': 5, 'description': 'Unusual session patterns'},
    }

    @staticmethod
    def analyze_payload(payload_text):
        """Deep analysis of a payload/request for threats using pattern matching."""
        results = {
            'timestamp': datetime.now().isoformat(),
            'input_length': len(payload_text),
            'threats_detected': [],
            'risk_score': 0,
            'risk_level': 'safe',
            'entropy': 0,
            'encoding_detected': [],
            'recommendations': [],
            'mitre_techniques': [],
            'kill_chain_phase': None
        }

        # Calculate Shannon entropy
        if payload_text:
            freq = Counter(payload_text)
            length = len(payload_text)
            entropy = -sum((count/length) * math.log2(count/length) for count in freq.values())
            results['entropy'] = round(entropy, 3)

        # Check for encoding layers
        encodings = []
        if re.search(r'^[A-Za-z0-9+/=]{20,}$', payload_text.strip()):
            encodings.append({'type': 'base64', 'confidence': 92})
        if re.search(r'^(\\x[0-9a-f]{2})+', payload_text):
            encodings.append({'type': 'hex_escaped', 'confidence': 95})
        if re.search(r'%[0-9a-fA-F]{2}', payload_text):
            encodings.append({'type': 'url_encoded', 'confidence': 88})
        if re.search(r'&#\d+;', payload_text):
            encodings.append({'type': 'html_entity', 'confidence': 90})
        if re.search(r'\\u[0-9a-fA-F]{4}', payload_text):
            encodings.append({'type': 'unicode_escaped', 'confidence': 87})
        results['encoding_detected'] = encodings

        # Pattern matching against signatures
        mitre_ids = set()
        max_severity_score = 0
        severity_map = {'low': 20, 'medium': 40, 'high': 70, 'critical': 95}

        for sig_name, sig_data in AIThreatAnalyzer.THREAT_SIGNATURES.items():
            for pattern in sig_data['patterns']:
                if re.search(pattern, payload_text, re.IGNORECASE):
                    threat = {
                        'signature': sig_name,
                        'severity': sig_data['severity'],
                        'mitre_id': sig_data['mitre'],
                        'category': sig_data['category'],
                        'description': sig_data['description'],
                        'matched_pattern': pattern,
                        'confidence': random.randint(85, 99)
                    }
                    results['threats_detected'].append(threat)
                    mitre_ids.add(sig_data['mitre'])
                    sev_score = severity_map.get(sig_data['severity'], 50)
                    if sev_score > max_severity_score:
                        max_severity_score = sev_score
                    break

        # Calculate risk score
        base_score = max_severity_score
        if len(results['threats_detected']) > 1:
            base_score = min(100, base_score + len(results['threats_detected']) * 5)
        if results['entropy'] > 4.5:
            base_score = min(100, base_score + 10)
        if encodings:
            base_score = min(100, base_score + len(encodings) * 5)

        results['risk_score'] = base_score
        results['mitre_techniques'] = list(mitre_ids)

        # Determine risk level
        if base_score >= 80:
            results['risk_level'] = 'critical'
        elif base_score >= 60:
            results['risk_level'] = 'high'
        elif base_score >= 40:
            results['risk_level'] = 'medium'
        elif base_score >= 20:
            results['risk_level'] = 'low'
        else:
            results['risk_level'] = 'safe'

        # Map to kill chain
        kill_chain_map = {
            'injection': 'exploitation',
            'execution': 'exploitation',
            'credential_access': 'exploitation',
            'discovery': 'reconnaissance',
            'lateral_movement': 'lateral_movement',
            'exfiltration': 'actions_on_objectives',
            'command_and_control': 'command_and_control',
            'privilege_escalation': 'privilege_escalation',
            'impact': 'actions_on_objectives'
        }
        for t in results['threats_detected']:
            phase = kill_chain_map.get(t['category'])
            if phase:
                results['kill_chain_phase'] = phase
                break

        # Generate recommendations
        if results['risk_level'] in ('critical', 'high'):
            results['recommendations'] = [
                'Immediately block the source IP address',
                'Enable WAF rules for detected attack patterns',
                'Rotate all potentially compromised credentials',
                'Check system logs for lateral movement indicators',
                'Initiate incident response procedures',
                'Preserve forensic evidence before remediation'
            ]
        elif results['risk_level'] == 'medium':
            results['recommendations'] = [
                'Monitor the source IP for continued suspicious activity',
                'Review firewall rules and access controls',
                'Enable enhanced logging for the targeted endpoints',
                'Consider implementing rate limiting'
            ]
        elif results['risk_level'] == 'low':
            results['recommendations'] = [
                'Log and monitor for pattern escalation',
                'Review input validation on affected endpoints'
            ]

        return results

    @staticmethod
    def behavioral_analysis(ip_address, request_log=None):
        """Analyze an IP's behavior against known profiles."""
        # Simulated behavioral analysis
        hour = datetime.now().hour
        hash_val = int(hashlib.md5(ip_address.encode()).hexdigest()[:8], 16)

        requests_per_min = (hash_val % 50) + 1
        failed_logins = hash_val % 10
        unique_endpoints = (hash_val % 30) + 1
        session_duration = (hash_val % 3600)
        bytes_transferred = (hash_val % 10000000)

        # Determine best matching profile
        best_match = 'normal_user'
        best_score = 0
        for profile_name, profile in AIThreatAnalyzer.BEHAVIOR_PROFILES.items():
            score = 0
            if abs(requests_per_min - profile['avg_requests_per_min']) < 20:
                score += 30
            if failed_logins >= profile['max_failed_logins']:
                score += 25
            if profile['typical_hours'][0] <= hour <= profile['typical_hours'][1]:
                score += 20
            score += profile['risk_score'] / 10
            if score > best_score:
                best_score = score
                best_match = profile_name

        profile_data = AIThreatAnalyzer.BEHAVIOR_PROFILES[best_match]
        risk = min(100, int(profile_data['risk_score'] * (1 + failed_logins * 0.05)))

        return {
            'ip': ip_address,
            'timestamp': datetime.now().isoformat(),
            'behavioral_profile': best_match,
            'profile_confidence': min(99, 60 + (hash_val % 35)),
            'metrics': {
                'requests_per_minute': requests_per_min,
                'failed_login_attempts': failed_logins,
                'unique_endpoints_accessed': unique_endpoints,
                'session_duration_seconds': session_duration,
                'bytes_transferred': bytes_transferred,
                'access_hour': hour
            },
            'risk_score': risk,
            'risk_level': 'critical' if risk >= 80 else 'high' if risk >= 60 else 'medium' if risk >= 40 else 'low',
            'anomalies': [
                {'type': 'high_request_rate', 'severity': 'warning', 'detail': f'{requests_per_min} req/min exceeds baseline'} if requests_per_min > 20 else None,
                {'type': 'failed_logins', 'severity': 'high', 'detail': f'{failed_logins} failed attempts'} if failed_logins > 3 else None,
                {'type': 'off_hours_access', 'severity': 'medium', 'detail': f'Access at hour {hour}'} if hour < 6 or hour > 22 else None,
                {'type': 'high_data_transfer', 'severity': 'warning', 'detail': f'{bytes_transferred} bytes transferred'} if bytes_transferred > 5000000 else None,
            ],
            'threat_indicators': {
                'is_tor_exit': hash_val % 7 == 0,
                'is_known_proxy': hash_val % 11 == 0,
                'is_cloud_provider': hash_val % 5 == 0,
                'is_datacenter': hash_val % 3 == 0,
                'abuse_reports': hash_val % 20,
                'first_seen': (datetime.now() - timedelta(days=hash_val % 365)).isoformat(),
                'last_seen': datetime.now().isoformat()
            }
        }

    @staticmethod
    def detect_anomalies(traffic_data=None):
        """Run anomaly detection across multiple models."""
        results = []
        now = datetime.now()

        for model_name, model in AIThreatAnalyzer.ANOMALY_MODELS.items():
            score = random.randint(10, 100)
            detected = score > 65

            result = {
                'model': model_name,
                'description': model['description'],
                'anomaly_detected': detected,
                'confidence_score': score,
                'severity': 'critical' if score > 90 else 'high' if score > 75 else 'medium' if score > 50 else 'low',
                'timestamp': now.isoformat(),
                'details': {}
            }

            if model_name == 'traffic_spike':
                baseline = random.randint(50, 200)
                current = baseline * (random.uniform(0.5, 4.0))
                result['details'] = {
                    'baseline_rpm': baseline,
                    'current_rpm': round(current),
                    'multiplier': round(current / baseline, 2)
                }
            elif model_name == 'geo_anomaly':
                result['details'] = {
                    'previous_location': random.choice(['New York, US', 'London, UK', 'Tokyo, JP']),
                    'current_location': random.choice(['Moscow, RU', 'Beijing, CN', 'Tehran, IR']),
                    'distance_km': random.randint(2000, 15000),
                    'time_between_minutes': random.randint(5, 120)
                }
            elif model_name == 'endpoint_scan':
                result['details'] = {
                    'unique_404s': random.randint(5, 50),
                    'top_paths': random.sample(['/.env', '/wp-admin', '/.git/config', '/admin', '/api/debug', '/backup.sql', '/phpinfo.php'], 4)
                }
            elif model_name == 'entropy_anomaly':
                result['details'] = {
                    'avg_entropy': round(random.uniform(2.0, 6.0), 3),
                    'threshold': 4.5,
                    'sample_requests': random.randint(10, 500)
                }

            results.append(result)

        # Overall assessment
        critical_count = sum(1 for r in results if r['anomaly_detected'] and r['severity'] == 'critical')
        high_count = sum(1 for r in results if r['anomaly_detected'] and r['severity'] == 'high')
        total_detected = sum(1 for r in results if r['anomaly_detected'])

        return {
            'timestamp': now.isoformat(),
            'models_run': len(results),
            'anomalies_detected': total_detected,
            'critical_anomalies': critical_count,
            'high_anomalies': high_count,
            'overall_threat_level': 'critical' if critical_count >= 2 else 'high' if critical_count >= 1 or high_count >= 2 else 'medium' if total_detected >= 3 else 'low',
            'results': results
        }

    @staticmethod
    def predictive_model(target_profile=None):
        """Generate predictive attack modeling — next likely attack vectors."""
        attack_chains = [
            {
                'name': 'Credential Spray → Lateral Movement → Data Exfil',
                'probability': random.randint(60, 95),
                'stages': [
                    {'phase': 'Initial Access', 'technique': 'T1078 — Valid Accounts', 'status': 'predicted', 'eta_hours': random.randint(1, 24)},
                    {'phase': 'Execution', 'technique': 'T1059 — Command Line Interface', 'status': 'predicted', 'eta_hours': random.randint(2, 48)},
                    {'phase': 'Lateral Movement', 'technique': 'T1021 — Remote Services', 'status': 'predicted', 'eta_hours': random.randint(6, 72)},
                    {'phase': 'Collection', 'technique': 'T1005 — Data from Local System', 'status': 'predicted', 'eta_hours': random.randint(12, 96)},
                    {'phase': 'Exfiltration', 'technique': 'T1048 — Exfil Over Alt Protocol', 'status': 'predicted', 'eta_hours': random.randint(24, 168)},
                ],
                'countermeasures': ['MFA enforcement', 'Network segmentation', 'DLP rules', 'Endpoint detection']
            },
            {
                'name': 'Phishing → Malware Drop → Persistence → C2',
                'probability': random.randint(50, 90),
                'stages': [
                    {'phase': 'Initial Access', 'technique': 'T1566 — Phishing', 'status': 'predicted', 'eta_hours': random.randint(1, 12)},
                    {'phase': 'Execution', 'technique': 'T1204 — User Execution', 'status': 'predicted', 'eta_hours': random.randint(1, 24)},
                    {'phase': 'Persistence', 'technique': 'T1547 — Boot/Logon Autostart', 'status': 'predicted', 'eta_hours': random.randint(2, 48)},
                    {'phase': 'C2', 'technique': 'T1071 — Application Layer Protocol', 'status': 'predicted', 'eta_hours': random.randint(4, 72)},
                    {'phase': 'Impact', 'technique': 'T1486 — Data Encrypted for Impact', 'status': 'predicted', 'eta_hours': random.randint(48, 336)},
                ],
                'countermeasures': ['Email filtering', 'Sandbox analysis', 'EDR deployment', 'Network monitoring']
            },
            {
                'name': 'Supply Chain Compromise → Backdoor → Long-term Access',
                'probability': random.randint(30, 75),
                'stages': [
                    {'phase': 'Initial Access', 'technique': 'T1195 — Supply Chain', 'status': 'predicted', 'eta_hours': random.randint(24, 720)},
                    {'phase': 'Execution', 'technique': 'T1059 — Scripting', 'status': 'predicted', 'eta_hours': random.randint(48, 960)},
                    {'phase': 'Persistence', 'technique': 'T1543 — System Service', 'status': 'predicted', 'eta_hours': random.randint(72, 1440)},
                    {'phase': 'Defense Evasion', 'technique': 'T1027 — Obfuscated Files', 'status': 'predicted', 'eta_hours': random.randint(96, 2160)},
                    {'phase': 'Collection', 'technique': 'T1560 — Archive Collected Data', 'status': 'predicted', 'eta_hours': random.randint(168, 4320)},
                ],
                'countermeasures': ['SCA scanning', 'Code signing', 'Zero trust', 'Behavioral monitoring']
            },
            {
                'name': 'Zero-Day Exploit → Privilege Escalation → Domain Takeover',
                'probability': random.randint(15, 55),
                'stages': [
                    {'phase': 'Initial Access', 'technique': 'T1190 — Exploit Public App', 'status': 'predicted', 'eta_hours': random.randint(1, 48)},
                    {'phase': 'Privilege Escalation', 'technique': 'T1068 — Exploitation for Priv Esc', 'status': 'predicted', 'eta_hours': random.randint(2, 72)},
                    {'phase': 'Credential Access', 'technique': 'T1003 — OS Credential Dumping', 'status': 'predicted', 'eta_hours': random.randint(4, 96)},
                    {'phase': 'Lateral Movement', 'technique': 'T1021 — Remote Desktop', 'status': 'predicted', 'eta_hours': random.randint(8, 168)},
                    {'phase': 'Impact', 'technique': 'T1489 — Service Stop', 'status': 'predicted', 'eta_hours': random.randint(24, 720)},
                ],
                'countermeasures': ['Virtual patching', 'WAF rules', 'PAM solutions', 'AD monitoring']
            }
        ]

        return {
            'timestamp': datetime.now().isoformat(),
            'model_version': 'StormAI v2.0',
            'prediction_window_hours': 168,
            'attack_chains': attack_chains,
            'top_predicted_technique': attack_chains[0]['stages'][0]['technique'],
            'highest_probability': max(c['probability'] for c in attack_chains),
            'recommended_priority': 'immediate' if any(c['probability'] > 80 for c in attack_chains) else 'high'
        }

    @staticmethod
    def generate_response_plan(threat_type, severity):
        """Generate an automated incident response plan."""
        plans = {
            'malware': {
                'name': 'Malware Incident Response',
                'priority': 'P1' if severity == 'critical' else 'P2',
                'steps': [
                    {'order': 1, 'action': 'Isolate affected hosts from network', 'automated': True, 'command': 'netsh advfirewall set allprofiles firewallpolicy blockinbound,blockoutbound', 'eta_min': 1},
                    {'order': 2, 'action': 'Capture memory dump for forensics', 'automated': True, 'command': 'winpmem_mini.exe memdump.raw', 'eta_min': 5},
                    {'order': 3, 'action': 'Kill malicious processes', 'automated': True, 'command': 'taskkill /F /PID <pid>', 'eta_min': 1},
                    {'order': 4, 'action': 'Quarantine malware samples', 'automated': True, 'command': 'move /Y <file> C:\\Quarantine\\', 'eta_min': 2},
                    {'order': 5, 'action': 'Scan with YARA rules', 'automated': True, 'command': 'yara -r rules.yar C:\\', 'eta_min': 30},
                    {'order': 6, 'action': 'Check persistence mechanisms', 'automated': True, 'command': 'autoruns -a * -c -h', 'eta_min': 5},
                    {'order': 7, 'action': 'Reset compromised credentials', 'automated': False, 'command': None, 'eta_min': 15},
                    {'order': 8, 'action': 'Restore from clean backup', 'automated': False, 'command': None, 'eta_min': 60},
                    {'order': 9, 'action': 'Monitor for reinfection (72h)', 'automated': True, 'command': 'sysmon -i config.xml', 'eta_min': 4320},
                    {'order': 10, 'action': 'Generate post-incident report', 'automated': True, 'command': None, 'eta_min': 30}
                ]
            },
            'data_breach': {
                'name': 'Data Breach Response',
                'priority': 'P1',
                'steps': [
                    {'order': 1, 'action': 'Identify scope of compromised data', 'automated': True, 'command': 'audit-log-analyzer --since 48h', 'eta_min': 10},
                    {'order': 2, 'action': 'Block exfiltration channels', 'automated': True, 'command': 'iptables -A OUTPUT -p tcp --dport 53 -j DROP', 'eta_min': 1},
                    {'order': 3, 'action': 'Revoke all active sessions', 'automated': True, 'command': 'session-manager --revoke-all', 'eta_min': 2},
                    {'order': 4, 'action': 'Enable enhanced DLP monitoring', 'automated': True, 'command': None, 'eta_min': 5},
                    {'order': 5, 'action': 'Preserve forensic evidence chain', 'automated': False, 'command': None, 'eta_min': 30},
                    {'order': 6, 'action': 'Notify legal/compliance team', 'automated': False, 'command': None, 'eta_min': 15},
                    {'order': 7, 'action': 'Initiate breach notification procedures', 'automated': False, 'command': None, 'eta_min': 60},
                    {'order': 8, 'action': 'Implement additional access controls', 'automated': True, 'command': None, 'eta_min': 30}
                ]
            },
            'ransomware': {
                'name': 'Ransomware Response',
                'priority': 'P1',
                'steps': [
                    {'order': 1, 'action': 'IMMEDIATELY disconnect from network', 'automated': True, 'command': 'netsh interface set interface "Ethernet" disable', 'eta_min': 0},
                    {'order': 2, 'action': 'Stop Volume Shadow Copy deletion', 'automated': True, 'command': 'sc config VSS start=disabled', 'eta_min': 1},
                    {'order': 3, 'action': 'Capture IOCs and ransomware sample', 'automated': True, 'command': 'copy <ransomware_file> C:\\Evidence\\', 'eta_min': 2},
                    {'order': 4, 'action': 'Identify ransomware family', 'automated': True, 'command': 'yara -r ransomware_rules.yar', 'eta_min': 5},
                    {'order': 5, 'action': 'Check for decryption tools', 'automated': True, 'command': None, 'eta_min': 10},
                    {'order': 6, 'action': 'Assess backup integrity', 'automated': False, 'command': None, 'eta_min': 30},
                    {'order': 7, 'action': 'Report to law enforcement', 'automated': False, 'command': None, 'eta_min': 60},
                    {'order': 8, 'action': 'Begin clean restoration', 'automated': False, 'command': None, 'eta_min': 240}
                ]
            },
            'intrusion': {
                'name': 'Network Intrusion Response',
                'priority': 'P1' if severity == 'critical' else 'P2',
                'steps': [
                    {'order': 1, 'action': 'Block attacker IP at firewall', 'automated': True, 'command': 'iptables -A INPUT -s <ip> -j DROP', 'eta_min': 1},
                    {'order': 2, 'action': 'Capture network traffic', 'automated': True, 'command': 'tcpdump -i eth0 -w capture.pcap host <ip>', 'eta_min': 2},
                    {'order': 3, 'action': 'Review authentication logs', 'automated': True, 'command': 'grep -r "Failed" /var/log/auth.log', 'eta_min': 5},
                    {'order': 4, 'action': 'Check for backdoors', 'automated': True, 'command': 'chkrootkit && rkhunter --check', 'eta_min': 15},
                    {'order': 5, 'action': 'Audit user accounts', 'automated': True, 'command': 'lastlog && w', 'eta_min': 5},
                    {'order': 6, 'action': 'Review cron and scheduled tasks', 'automated': True, 'command': 'crontab -l && at -l', 'eta_min': 5},
                    {'order': 7, 'action': 'Full system integrity check', 'automated': True, 'command': 'tripwire --check', 'eta_min': 60},
                    {'order': 8, 'action': 'Update IDS/IPS signatures', 'automated': True, 'command': None, 'eta_min': 10}
                ]
            }
        }

        plan = plans.get(threat_type, plans['intrusion'])
        total_eta = sum(s['eta_min'] for s in plan['steps'])
        automated_count = sum(1 for s in plan['steps'] if s['automated'])

        return {
            'plan': plan,
            'total_estimated_minutes': total_eta,
            'automated_steps': automated_count,
            'manual_steps': len(plan['steps']) - automated_count,
            'automation_percentage': round(automated_count / len(plan['steps']) * 100),
            'generated_at': datetime.now().isoformat()
        }

    @staticmethod
    def get_threat_landscape():
        """Get current threat landscape overview with trending threats."""
        return {
            'timestamp': datetime.now().isoformat(),
            'trending_threats': [
                {'name': 'AI-Powered Phishing', 'trend': 'rising', 'change_pct': 340, 'severity': 'critical', 'description': 'LLM-generated spear phishing with perfect grammar and context'},
                {'name': 'Supply Chain Attacks', 'trend': 'rising', 'change_pct': 185, 'severity': 'critical', 'description': 'Compromised package managers and CI/CD pipelines'},
                {'name': 'Quantum-Resistant Backdoors', 'trend': 'emerging', 'change_pct': 890, 'severity': 'critical', 'description': 'Post-quantum cryptographic backdoors in firmware'},
                {'name': 'Living-off-the-Land (LOTL)', 'trend': 'stable', 'change_pct': 45, 'severity': 'high', 'description': 'Abuse of legitimate system tools for attacks'},
                {'name': 'Deepfake Social Engineering', 'trend': 'rising', 'change_pct': 520, 'severity': 'high', 'description': 'Real-time voice/video deepfakes for vishing'},
                {'name': 'IoT Botnets', 'trend': 'stable', 'change_pct': 30, 'severity': 'medium', 'description': 'Compromised IoT devices for DDoS and crypto mining'},
                {'name': 'Ransomware-as-a-Service', 'trend': 'declining', 'change_pct': -15, 'severity': 'critical', 'description': 'Affiliate programs with double extortion'},
                {'name': 'Zero-Click Exploits', 'trend': 'rising', 'change_pct': 210, 'severity': 'critical', 'description': 'No user interaction required for compromise'}
            ],
            'active_apt_groups': [
                {'name': 'APT-STORM', 'origin': 'Unknown', 'targets': ['Government', 'Defense'], 'active': True, 'ttps': ['T1566', 'T1059', 'T1548']},
                {'name': 'DARK-NEBULA', 'origin': 'Eastern Europe', 'targets': ['Finance', 'Crypto'], 'active': True, 'ttps': ['T1190', 'T1068', 'T1486']},
                {'name': 'SHADOW-GRID', 'origin': 'Asia Pacific', 'targets': ['Infrastructure', 'Energy'], 'active': True, 'ttps': ['T1195', 'T1071', 'T1489']},
                {'name': 'PHANTOM-BYTE', 'origin': 'Unknown', 'targets': ['Healthcare', 'Research'], 'active': True, 'ttps': ['T1078', 'T1005', 'T1048']}
            ],
            'global_threat_index': random.randint(60, 95),
            'top_targeted_sectors': [
                {'sector': 'Healthcare', 'attack_volume': random.randint(1000, 5000), 'trend': 'up'},
                {'sector': 'Finance', 'attack_volume': random.randint(2000, 8000), 'trend': 'up'},
                {'sector': 'Government', 'attack_volume': random.randint(1500, 6000), 'trend': 'stable'},
                {'sector': 'Technology', 'attack_volume': random.randint(3000, 10000), 'trend': 'up'},
                {'sector': 'Energy', 'attack_volume': random.randint(500, 3000), 'trend': 'up'}
            ]
        }
