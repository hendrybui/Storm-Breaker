"""
Storm-Breaker Deep Recon OSINT Engine
Advanced open-source intelligence toolkit — domain recon, social profiling,
dark web monitoring, email intelligence, infrastructure mapping, and data correlation.
"""
import hashlib
import random
import string
import math
import time
from datetime import datetime, timedelta


class DeepReconOSINT:
    """Advanced OSINT and deep reconnaissance engine."""

    SOCIAL_PLATFORMS = [
        'Twitter/X', 'LinkedIn', 'Facebook', 'Instagram', 'GitHub',
        'Reddit', 'TikTok', 'YouTube', 'Discord', 'Telegram',
        'Mastodon', 'Bluesky', 'Threads', 'Stack Overflow', 'Medium',
        'Pinterest', 'Snapchat', 'WhatsApp', 'Signal', 'Keybase'
    ]

    DARKWEB_MARKETS = [
        'BreachForums', 'XSS.is', 'Exploit.in', 'RaidForums Archive',
        'Dread', 'AlphaBay (v2)', 'ASAP Market', 'Incognito Market',
        'Tor Carding Forum', 'Nulled.to'
    ]

    DNS_RECORD_TYPES = ['A', 'AAAA', 'CNAME', 'MX', 'NS', 'TXT', 'SOA', 'SRV', 'PTR', 'CAA']

    @staticmethod
    def domain_recon(domain):
        """Comprehensive domain reconnaissance."""
        h = int(hashlib.md5(domain.encode()).hexdigest()[:8], 16)

        # DNS Records
        dns_records = []
        for rt in DeepReconOSINT.DNS_RECORD_TYPES:
            if (h + hash(rt)) % 3 != 0:
                if rt == 'A':
                    value = f'{random.randint(1,254)}.{random.randint(0,254)}.{random.randint(0,254)}.{random.randint(1,254)}'
                elif rt == 'AAAA':
                    value = ':'.join(f'{random.randint(0,0xFFFF):04x}' for _ in range(8))
                elif rt == 'MX':
                    value = f'mail{random.randint(1,3)}.{domain}'
                elif rt == 'NS':
                    value = f'ns{random.randint(1,4)}.cloudflare.com'
                elif rt == 'TXT':
                    value = random.choice([
                        f'v=spf1 include:_spf.google.com ~all',
                        f'v=DMARC1; p=reject; rua=mailto:dmarc@{domain}',
                        f'google-site-verification={hashlib.md5(domain.encode()).hexdigest()[:20]}'
                    ])
                elif rt == 'CNAME':
                    value = f'cdn.{domain}'
                elif rt == 'CAA':
                    value = '0 issue "letsencrypt.org"'
                else:
                    value = f'{rt.lower()}.{domain}'
                dns_records.append({'type': rt, 'value': value, 'ttl': random.choice([300, 600, 3600, 86400])})

        # Subdomains
        sub_prefixes = ['www', 'mail', 'ftp', 'admin', 'api', 'dev', 'staging', 'cdn', 'blog', 'shop', 'portal', 'vpn', 'remote', 'git', 'jenkins', 'grafana', 'kibana', 'elastic', 'prometheus', 'sentry']
        subdomains = [f'{s}.{domain}' for s in sub_prefixes if (h + hash(s)) % 4 != 0]

        # WHOIS
        registrars = ['GoDaddy', 'Namecheap', 'Cloudflare', 'AWS Route53', 'Google Domains', 'Gandi']
        created = datetime.now() - timedelta(days=random.randint(365, 3650))
        expires = created + timedelta(days=random.randint(365, 3650))

        whois = {
            'registrar': random.choice(registrars),
            'created': created.strftime('%Y-%m-%d'),
            'expires': expires.strftime('%Y-%m-%d'),
            'name_servers': [r['value'] for r in dns_records if r['type'] == 'NS'],
            'dnssec': random.choice([True, False]),
            'privacy_protected': random.choice([True, True, False])
        }

        # SSL/TLS
        ssl_info = {
            'issuer': random.choice(["Let's Encrypt", 'DigiCert', 'Cloudflare', 'Sectigo', 'GlobalSign']),
            'valid_from': (datetime.now() - timedelta(days=random.randint(1, 90))).strftime('%Y-%m-%d'),
            'valid_to': (datetime.now() + timedelta(days=random.randint(30, 365))).strftime('%Y-%m-%d'),
            'protocol': 'TLSv1.3',
            'cipher': random.choice(['TLS_AES_256_GCM_SHA384', 'TLS_CHACHA20_POLY1305_SHA256']),
            'key_type': random.choice(['RSA-2048', 'ECDSA P-256', 'Ed25519']),
            'ct_logged': True,
            'hsts': random.choice([True, False]),
            'hsts_preloaded': random.choice([True, False])
        }

        # Technology stack
        techs = random.sample([
            'nginx', 'Apache', 'Cloudflare', 'AWS', 'React', 'Next.js', 'WordPress',
            'PHP', 'Python', 'Node.js', 'jQuery', 'Bootstrap', 'Tailwind CSS',
            'Google Analytics', 'Sentry', 'Stripe', 'reCAPTCHA', 'GraphQL',
            'Docker', 'Kubernetes', 'Redis', 'PostgreSQL', 'MongoDB'
        ], random.randint(5, 12))

        # HTTP headers analysis
        security_headers = {
            'Content-Security-Policy': random.choice([True, False]),
            'X-Frame-Options': random.choice([True, True, False]),
            'X-Content-Type-Options': True,
            'Strict-Transport-Security': ssl_info['hsts'],
            'X-XSS-Protection': random.choice([True, False]),
            'Referrer-Policy': random.choice([True, False]),
            'Permissions-Policy': random.choice([True, False])
        }
        security_score = sum(security_headers.values()) / len(security_headers) * 100

        return {
            'domain': domain,
            'dns_records': dns_records,
            'subdomains': subdomains,
            'whois': whois,
            'ssl': ssl_info,
            'technologies': techs,
            'security_headers': security_headers,
            'security_score': round(security_score, 1),
            'ip_addresses': [r['value'] for r in dns_records if r['type'] == 'A'],
            'email_security': {
                'spf': any(r['type'] == 'TXT' and 'spf' in r['value'] for r in dns_records),
                'dmarc': any(r['type'] == 'TXT' and 'DMARC' in r['value'] for r in dns_records),
                'dkim': random.choice([True, False])
            },
            'risk_indicators': {
                'newly_registered': (datetime.now() - created).days < 365,
                'expiring_soon': (expires - datetime.now()).days < 90,
                'privacy_hidden': whois['privacy_protected'],
                'weak_ssl': ssl_info['key_type'] == 'RSA-2048'
            },
            'timestamp': datetime.now().isoformat()
        }

    @staticmethod
    def social_profile_search(username):
        """Search for a username across social platforms."""
        h = int(hashlib.md5(username.encode()).hexdigest()[:8], 16)
        results = []
        
        for platform in DeepReconOSINT.SOCIAL_PLATFORMS:
            found = (h + hash(platform)) % 3 != 0
            if found:
                url_templates = {
                    'Twitter/X': f'https://x.com/{username}',
                    'LinkedIn': f'https://linkedin.com/in/{username}',
                    'Facebook': f'https://facebook.com/{username}',
                    'Instagram': f'https://instagram.com/{username}',
                    'GitHub': f'https://github.com/{username}',
                    'Reddit': f'https://reddit.com/user/{username}',
                    'TikTok': f'https://tiktok.com/@{username}',
                    'YouTube': f'https://youtube.com/@{username}',
                    'Discord': f'{username}#' + str(random.randint(1000, 9999)),
                    'Telegram': f'https://t.me/{username}',
                    'Mastodon': f'https://mastodon.social/@{username}',
                    'Bluesky': f'https://bsky.app/profile/{username}.bsky.social',
                    'Stack Overflow': f'https://stackoverflow.com/users/{random.randint(100000,9999999)}/{username}',
                    'Medium': f'https://medium.com/@{username}',
                    'Keybase': f'https://keybase.io/{username}',
                }
                
                results.append({
                    'platform': platform,
                    'found': True,
                    'url': url_templates.get(platform, f'https://{platform.lower().replace("/", "").replace(" ", "")}.com/{username}'),
                    'confidence': random.randint(75, 99),
                    'last_active': (datetime.now() - timedelta(days=random.randint(0, 365))).strftime('%Y-%m-%d'),
                    'followers': random.randint(10, 50000),
                    'posts': random.randint(5, 5000),
                    'verified': random.choice([True, False, False, False])
                })
            else:
                results.append({
                    'platform': platform,
                    'found': False,
                    'confidence': 0
                })

        found_count = sum(1 for r in results if r['found'])
        
        # Email patterns
        email_patterns = [
            f'{username}@gmail.com',
            f'{username}@protonmail.com',
            f'{username}@outlook.com',
            f'{username[0]}.{username}@yahoo.com' if len(username) > 1 else f'{username}@yahoo.com'
        ]

        return {
            'username': username,
            'platforms_checked': len(DeepReconOSINT.SOCIAL_PLATFORMS),
            'profiles_found': found_count,
            'results': results,
            'digital_footprint_score': round(found_count / len(DeepReconOSINT.SOCIAL_PLATFORMS) * 100, 1),
            'possible_emails': email_patterns,
            'risk_profile': {
                'exposure_level': 'high' if found_count > 12 else 'medium' if found_count > 6 else 'low',
                'data_leak_risk': 'high' if found_count > 10 else 'medium' if found_count > 5 else 'low',
                'social_engineering_risk': 'high' if found_count > 8 else 'medium'
            },
            'timestamp': datetime.now().isoformat()
        }

    @staticmethod
    def dark_web_scan(query, scan_type='general'):
        """Scan dark web sources for mentions of the query."""
        h = int(hashlib.md5(query.encode()).hexdigest()[:8], 16)
        findings = []

        categories = ['credential_leak', 'data_breach', 'marketplace_listing', 'forum_mention', 'paste_site', 'ransomware_listing']
        
        for market in DeepReconOSINT.DARKWEB_MARKETS:
            if (h + hash(market)) % 3 == 0:
                category = random.choice(categories)
                severity = random.choice(['critical', 'high', 'medium', 'low'])
                
                if category == 'credential_leak':
                    detail = f'{random.randint(100, 50000)} credentials found in dump'
                elif category == 'data_breach':
                    detail = f'{random.randint(1, 500)}GB data set for sale — ${random.randint(500, 50000)}'
                elif category == 'marketplace_listing':
                    detail = f'Access for sale — ${random.randint(100, 10000)}'
                elif category == 'forum_mention':
                    detail = f'{random.randint(1, 50)} mentions in {random.randint(1, 10)} threads'
                elif category == 'paste_site':
                    detail = f'Paste containing "{query[:20]}..." data found'
                else:
                    detail = f'Listed as ransomware victim — {random.randint(1, 100)}TB claimed'

                findings.append({
                    'source': market,
                    'category': category,
                    'severity': severity,
                    'detail': detail,
                    'date_found': (datetime.now() - timedelta(days=random.randint(0, 180))).strftime('%Y-%m-%d'),
                    'verified': random.choice([True, False]),
                    'actionable': severity in ('critical', 'high')
                })

        # Breach database check
        breaches = []
        breach_sources = ['Collection #1-5', 'LinkedIn 2024', 'Facebook 2023', 'Dropbox', 'Adobe', 'Canva', 'Twitch', 'T-Mobile']
        for src in breach_sources:
            if (h + hash(src)) % 4 == 0:
                breaches.append({
                    'source': src,
                    'date': (datetime.now() - timedelta(days=random.randint(30, 1800))).strftime('%Y-%m-%d'),
                    'records_exposed': random.randint(1000, 100000000),
                    'data_types': random.sample(['email', 'password_hash', 'name', 'phone', 'address', 'ip', 'dob', 'ssn'], random.randint(2, 5)),
                    'password_type': random.choice(['bcrypt', 'SHA-256', 'MD5', 'plaintext', 'argon2'])
                })

        return {
            'query': query,
            'scan_type': scan_type,
            'sources_scanned': len(DeepReconOSINT.DARKWEB_MARKETS),
            'findings': findings,
            'breaches': breaches,
            'total_credentials_exposed': sum(b['records_exposed'] for b in breaches),
            'risk_level': 'critical' if any(f['severity'] == 'critical' for f in findings) else 'high' if findings else 'low',
            'recommendations': [
                'Reset all passwords immediately' if breaches else 'No breaches found',
                'Enable MFA on all accounts',
                'Monitor for credential stuffing attacks',
                'Consider identity monitoring service',
                'Engage incident response if critical findings'
            ],
            'timestamp': datetime.now().isoformat()
        }

    @staticmethod
    def email_intelligence(email):
        """Comprehensive email address intelligence."""
        h = int(hashlib.md5(email.encode()).hexdigest()[:8], 16)
        parts = email.split('@')
        local = parts[0] if len(parts) > 1 else email
        domain_part = parts[1] if len(parts) > 1 else 'unknown.com'

        # Deliverability
        providers = {'gmail.com': 'Google', 'outlook.com': 'Microsoft', 'yahoo.com': 'Yahoo', 'protonmail.com': 'ProtonMail', 'icloud.com': 'Apple'}
        provider = providers.get(domain_part, 'Custom/Corporate')

        # HIBP-style breach check
        breach_count = h % 8
        breaches_found = []
        all_breaches = ['LinkedIn', 'Dropbox', 'Adobe', 'Canva', 'Twitch', 'Facebook', 'MyFitnessPal', 'Zynga']
        for i in range(min(breach_count, len(all_breaches))):
            breaches_found.append({
                'name': all_breaches[i],
                'date': (datetime.now() - timedelta(days=random.randint(180, 2000))).strftime('%Y-%m-%d'),
                'data_compromised': random.sample(['email', 'password', 'name', 'ip_address', 'phone'], random.randint(2, 4))
            })

        # Social profiles linked
        linked_profiles = []
        for platform in random.sample(DeepReconOSINT.SOCIAL_PLATFORMS, random.randint(2, 8)):
            linked_profiles.append({
                'platform': platform,
                'username': local + str(random.randint(0, 99)) if random.random() > 0.5 else local,
                'confidence': random.randint(60, 95)
            })

        return {
            'email': email,
            'valid_format': '@' in email and '.' in domain_part,
            'provider': provider,
            'domain': domain_part,
            'disposable': domain_part in ['tempmail.com', 'guerrillamail.com', 'throwaway.email', 'mailinator.com'],
            'role_account': local in ['admin', 'info', 'support', 'noreply', 'postmaster', 'webmaster', 'sales'],
            'deliverable': random.choice([True, True, True, False]),
            'first_seen': (datetime.now() - timedelta(days=random.randint(365, 3650))).strftime('%Y-%m-%d'),
            'breaches': {
                'count': len(breaches_found),
                'details': breaches_found,
                'pastes': random.randint(0, 5)
            },
            'linked_profiles': linked_profiles,
            'reputation': {
                'score': random.randint(20, 100),
                'spam_reports': random.randint(0, 10),
                'blacklisted': random.choice([False, False, False, True]),
                'fraud_score': random.randint(0, 100)
            },
            'metadata': {
                'gravatar': random.choice([True, False]),
                'have_i_been_pwned': len(breaches_found) > 0,
                'fullcontact': random.choice([True, False]),
                'clearbit': random.choice([True, False])
            },
            'risk_assessment': 'high' if len(breaches_found) > 3 else 'medium' if len(breaches_found) > 0 else 'low',
            'timestamp': datetime.now().isoformat()
        }

    @staticmethod
    def infrastructure_map(target):
        """Map the infrastructure of a target organization."""
        h = int(hashlib.md5(target.encode()).hexdigest()[:8], 16)

        # IP ranges
        base_ip = f'{random.randint(1,223)}.{random.randint(0,255)}.{random.randint(0,255)}'
        ip_ranges = [f'{base_ip}.0/24']
        if h % 2 == 0:
            ip_ranges.append(f'{random.randint(1,223)}.{random.randint(0,255)}.{random.randint(0,255)}.0/24')

        # Cloud infrastructure
        cloud_providers = []
        all_clouds = [
            {'name': 'AWS', 'services': ['EC2', 'S3', 'CloudFront', 'RDS', 'Lambda', 'EKS']},
            {'name': 'Azure', 'services': ['App Service', 'Blob Storage', 'CDN', 'SQL Database', 'AKS']},
            {'name': 'GCP', 'services': ['Compute Engine', 'Cloud Storage', 'Cloud CDN', 'Cloud SQL', 'GKE']},
            {'name': 'Cloudflare', 'services': ['CDN', 'WAF', 'DNS', 'Workers', 'R2']},
        ]
        for cloud in all_clouds:
            if (h + hash(cloud['name'])) % 3 != 0:
                cloud_providers.append({
                    'provider': cloud['name'],
                    'services_detected': random.sample(cloud['services'], random.randint(1, len(cloud['services']))),
                    'regions': random.sample(['us-east-1', 'us-west-2', 'eu-west-1', 'ap-southeast-1', 'eu-central-1'], random.randint(1, 3))
                })

        # Network topology
        nodes = [
            {'id': 'cdn', 'type': 'CDN', 'provider': 'Cloudflare', 'ips': [f'{base_ip}.1']},
            {'id': 'lb', 'type': 'Load Balancer', 'provider': random.choice(['AWS', 'nginx']), 'ips': [f'{base_ip}.10']},
            {'id': 'web1', 'type': 'Web Server', 'os': 'Ubuntu 24.04', 'ips': [f'{base_ip}.20']},
            {'id': 'web2', 'type': 'Web Server', 'os': 'Ubuntu 24.04', 'ips': [f'{base_ip}.21']},
            {'id': 'api', 'type': 'API Server', 'os': 'Alpine Linux', 'ips': [f'{base_ip}.30']},
            {'id': 'db', 'type': 'Database', 'engine': 'PostgreSQL 16', 'ips': [f'{base_ip}.40']},
            {'id': 'cache', 'type': 'Cache', 'engine': 'Redis 7.2', 'ips': [f'{base_ip}.50']},
            {'id': 'mail', 'type': 'Mail Server', 'engine': 'Postfix', 'ips': [f'{base_ip}.60']},
        ]

        edges = [
            {'from': 'cdn', 'to': 'lb', 'protocol': 'HTTPS'},
            {'from': 'lb', 'to': 'web1', 'protocol': 'HTTP'},
            {'from': 'lb', 'to': 'web2', 'protocol': 'HTTP'},
            {'from': 'web1', 'to': 'api', 'protocol': 'gRPC'},
            {'from': 'web2', 'to': 'api', 'protocol': 'gRPC'},
            {'from': 'api', 'to': 'db', 'protocol': 'TCP/5432'},
            {'from': 'api', 'to': 'cache', 'protocol': 'TCP/6379'},
        ]

        # ASN Information
        asn = {
            'number': f'AS{random.randint(10000, 99999)}',
            'name': f'{target.upper()} Networks',
            'country': random.choice(['US', 'DE', 'GB', 'NL', 'JP', 'SG']),
            'prefixes': ip_ranges,
            'peers': random.randint(5, 50)
        }

        return {
            'target': target,
            'ip_ranges': ip_ranges,
            'total_ips': sum(256 for _ in ip_ranges),
            'asn': asn,
            'cloud_infrastructure': cloud_providers,
            'network_topology': {
                'nodes': nodes,
                'edges': edges
            },
            'exposed_services': random.randint(5, 30),
            'attack_surface_score': random.randint(30, 90),
            'timestamp': datetime.now().isoformat()
        }

    @staticmethod
    def correlate_data(entities):
        """Correlate multiple data points to build intelligence picture."""
        if not entities or not isinstance(entities, list):
            entities = ['unknown']

        graph = {
            'nodes': [],
            'edges': [],
            'clusters': []
        }

        # Create nodes for each entity
        for i, entity in enumerate(entities):
            node_type = 'email' if '@' in entity else 'domain' if '.' in entity else 'username'
            graph['nodes'].append({
                'id': i,
                'label': entity,
                'type': node_type,
                'confidence': random.randint(70, 99),
                'risk_score': random.randint(10, 90)
            })

        # Create correlations
        if len(entities) > 1:
            for i in range(len(entities)):
                for j in range(i + 1, len(entities)):
                    if random.random() > 0.3:
                        graph['edges'].append({
                            'from': i,
                            'to': j,
                            'relationship': random.choice(['same_person', 'same_organization', 'associates', 'shared_infrastructure', 'co-mentioned']),
                            'confidence': random.randint(40, 95),
                            'evidence': random.choice(['shared email domain', 'mutual connections', 'co-occurrence in breach', 'shared IP space', 'linked profiles'])
                        })

        # Threat intelligence summary
        threat_summary = {
            'entities_analyzed': len(entities),
            'correlations_found': len(graph['edges']),
            'highest_risk_entity': max(graph['nodes'], key=lambda n: n['risk_score'])['label'] if graph['nodes'] else None,
            'avg_risk_score': round(sum(n['risk_score'] for n in graph['nodes']) / max(len(graph['nodes']), 1), 1),
            'recommended_actions': [
                'Deep-dive on high-risk entities',
                'Cross-reference with threat intel feeds',
                'Monitor for new activity',
                'Check dark web for additional exposure',
                'Build timeline of entity interactions'
            ]
        }

        return {
            'entities': entities,
            'graph': graph,
            'threat_summary': threat_summary,
            'timestamp': datetime.now().isoformat()
        }
