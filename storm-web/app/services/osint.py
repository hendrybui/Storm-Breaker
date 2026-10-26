"""OSINT service (P4.6) — threat-intel, deeprecon, pivot, session-hijack.

Extracted verbatim from ``app/blueprints/threat_intel.py``,
``app/blueprints/deeprecon.py``, ``app/blueprints/pivot.py`` and
``app/blueprints/session_hijack.py`` route bodies.  Blueprints keep
request parsing + ``jsonify``; the frozen analysis modules
(``threat_intel``, ``deep_recon``, ``pivot_engine``, ``session_hijacker``),
persistence, analytics and operator-audit logging live here.

No behavior change intended — ``tests/char`` freezes response shapes.
"""
from __future__ import annotations

import json

import database as db

from app.state import track_event


# -- Threat intel --------------------------------------------------------------------

def threat_types():
    from threat_intel import get_supported_intel_types
    return get_supported_intel_types()


def analyze_ip(ip: str, headers, operator: str) -> dict:
    from threat_intel import analyze_ip as _analyze
    result = _analyze(ip, headers)
    track_event('threat_intel')
    db.save_threat_intel('ip', ip, result, result.get('threat_score', 0),
                         result.get('threat_level', 'none'), operator)
    return result


def analyze_email(email: str, operator: str) -> dict:
    from threat_intel import analyze_email as _analyze
    result = _analyze(email)
    track_event('threat_intel')
    db.save_threat_intel('email', email, result,
                         result.get('intelligence_score', 0),
                         'high' if result.get('intelligence_score', 0) > 70 else 'medium',
                         operator)
    return result


def fingerprint_technology(headers, html_body) -> dict:
    from threat_intel import fingerprint_technology as _fp
    result = _fp(headers, html_body)
    track_event('threat_intel')
    return result


def discover_social_profiles(username, email) -> dict:
    from threat_intel import discover_social_profiles as _discover
    result = _discover(username, email)
    track_event('threat_intel')
    return result


def build_threat_report(data: dict, operator: str, ip: str) -> dict:
    from threat_intel import build_threat_report as _build
    result = _build(
        ip_address=data.get('ip'),
        email=data.get('email'),
        username=data.get('username'),
        headers=data.get('headers'),
        html_body=data.get('html_body'))
    track_event('threat_intel')
    db.save_threat_intel('full_report', json.dumps({k: data.get(k, '') for k in ('ip', 'email', 'username')}),
                         result, result.get('overall_threat_score', 0),
                         result.get('overall_threat_level', 'none'),
                         operator)
    db.log_operator_action(operator, 'threat_report',
                           f'Built threat report', ip)
    return result


def threat_history(intel_type=None) -> list:
    return db.get_threat_intel(intel_type)


def delete_threat_intel(intel_id: int) -> None:
    db.delete_threat_intel(intel_id)


# -- DeepRecon -------------------------------------------------------------------------

def deeprecon_domain(domain: str):
    from deep_recon import DeepReconOSINT
    return DeepReconOSINT.domain_recon(domain)


def deeprecon_social(username: str):
    from deep_recon import DeepReconOSINT
    return DeepReconOSINT.social_profile_search(username)


def deeprecon_darkweb(query: str):
    from deep_recon import DeepReconOSINT
    return DeepReconOSINT.dark_web_scan(query)


def deeprecon_email(email: str):
    from deep_recon import DeepReconOSINT
    return DeepReconOSINT.email_intelligence(email)


def deeprecon_infra(target: str):
    from deep_recon import DeepReconOSINT
    return DeepReconOSINT.infrastructure_map(target)


def deeprecon_correlate(entities: list):
    from deep_recon import DeepReconOSINT
    return DeepReconOSINT.correlate_data(entities)


# -- Pivot -----------------------------------------------------------------------------

def pivot_capabilities():
    from pivot_engine import get_pivot_capabilities
    return get_pivot_capabilities()


def build_attack_graph(hosts, credentials, sessions, name: str,
                       operator: str, ip: str) -> dict:
    from pivot_engine import build_attack_graph as _build
    result = _build(hosts, credentials, sessions)
    track_event('pivot')
    # Save
    db.save_pivot_record('attack_graph', name,
                         result, result.get('total_hosts', 0),
                         result.get('total_lateral_paths', 0), 0,
                         operator)
    db.log_operator_action(operator, 'attack_graph',
                           f'Built attack graph: {result.get("total_hosts")} hosts', ip)
    return result


def map_credential_reuse(credentials, hosts) -> dict:
    from pivot_engine import map_credential_reuse as _map
    result = _map(credentials, hosts)
    track_event('pivot')
    return result


def suggest_privesc(os_type: str, current_user: str) -> dict:
    from pivot_engine import suggest_privesc as _suggest
    result = _suggest(os_type, current_user)
    track_event('pivot')
    return result


def track_kill_chain(events: list, operator: str) -> dict:
    from pivot_engine import track_kill_chain as _track
    result = _track(events)
    track_event('pivot')
    # Save
    db.save_pivot_record('kill_chain', 'Kill Chain Assessment',
                         result, 0, 0, result.get('coverage_percent', 0),
                         operator)
    return result


def score_attack_surface(hosts, credentials, sessions, browser_exfil) -> dict:
    from pivot_engine import score_attack_surface as _score
    result = _score(
        hosts=hosts,
        credentials=credentials,
        sessions=sessions,
        browser_exfil=browser_exfil)
    track_event('pivot')
    return result


def pivot_history(record_type=None) -> list:
    return db.get_pivot_records(record_type)


def delete_pivot_record(record_id: int) -> None:
    db.delete_pivot_record(record_id)


# -- Session hijack ----------------------------------------------------------------------

def hijack_features():
    from session_hijacker import get_supported_features
    return get_supported_features()


def parse_cookies(cookie_string, cookie_list) -> dict:
    from session_hijacker import parse_cookies as _parse
    result = _parse(cookie_string, cookie_list)
    track_event('session_hijack')
    return result


def analyze_jwt(token: str) -> dict:
    from session_hijacker import analyze_jwt as _analyze
    result = _analyze(token)
    track_event('session_hijack')
    return result


def extract_tokens(data: dict) -> dict:
    from session_hijacker import extract_tokens as _extract
    result = _extract(data)
    track_event('session_hijack')
    return result


def build_replay(cookies, target_url: str, method: str) -> dict:
    from session_hijacker import build_replay_request as _build
    result = _build(cookies, target_url, method)
    track_event('session_hijack')
    return result


def assess_session(cookie_data, jwt_tokens, victim_ip_label: str,
                   operator: str, ip: str) -> dict:
    """Assess + persist + audit-log (legacy ``api_hijack_assess`` body)."""
    from session_hijacker import assess_session as _assess
    result = _assess(cookie_data, jwt_tokens)
    track_event('session_hijack')
    # Save assessment
    db.save_session_hijack(
        victim_ip=victim_ip_label,
        session_data=result,
        token_count=result.get('token_inventory', {}).get('total', 0),
        critical_tokens=result.get('token_inventory', {}).get('auth_tokens', 0),
        hijack_feasibility=result.get('hijack_feasibility', 'unknown'),
        risk_score=result.get('risk_score', 0))
    db.log_operator_action(operator, 'session_assess',
                           f'Assessed session for {victim_ip_label}', ip)
    return result


def hijack_history(victim_ip=None) -> list:
    return db.get_session_hijacks(victim_ip)


def delete_hijack(hijack_id: int) -> None:
    db.delete_session_hijack(hijack_id)


__all__ = [
    "threat_types", "analyze_ip", "analyze_email", "fingerprint_technology",
    "discover_social_profiles", "build_threat_report", "threat_history",
    "delete_threat_intel",
    "deeprecon_domain", "deeprecon_social", "deeprecon_darkweb",
    "deeprecon_email", "deeprecon_infra", "deeprecon_correlate",
    "pivot_capabilities", "build_attack_graph", "map_credential_reuse",
    "suggest_privesc", "track_kill_chain", "score_attack_surface",
    "pivot_history", "delete_pivot_record",
    "hijack_features", "parse_cookies", "analyze_jwt", "extract_tokens",
    "build_replay", "assess_session", "hijack_history", "delete_hijack",
]

