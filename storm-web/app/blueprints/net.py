"""net blueprint (P14.7/P14.8 -- additive real-network API).

ADD-ONLY endpoints (NR-2).  Real DNS / scan / WHOIS / GeoIP, distinct from the
simulated ``deeprecon``/``threat-intel`` routes.
"""
from __future__ import annotations

import os

from flask import Blueprint, jsonify, request, session

from app.state import BASE_DIR
from app.exec import net

bp = Blueprint("net", __name__,
               template_folder=os.path.join(BASE_DIR, "flask_templates"))


def _guard():
    if 'IAm-logined' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    return None


@bp.route('/api/net/resolve')
def api_net_resolve():
    bad = _guard()
    if bad:
        return bad
    host = request.args.get('host') or 'localhost'
    return jsonify({'host': host, 'addresses': net.resolve(host)})


@bp.route('/api/net/reverse')
def api_net_reverse():
    bad = _guard()
    if bad:
        return bad
    ip = request.args.get('ip')
    if not ip:
        return jsonify({'error': 'ip required'}), 400
    return jsonify({'ip': ip, 'name': net.reverse_dns(ip)})


@bp.route('/api/net/scan', methods=['POST'])
def api_net_scan():
    bad = _guard()
    if bad:
        return bad
    data = request.json or {}
    host = data.get('host')
    if not host:
        return jsonify({'error': 'host required'}), 400
    ports = data.get('ports')
    if isinstance(ports, str):
        ports = [int(p) for p in ports.replace(',', ' ').split() if p.strip().isdigit()]
    result = net.port_scan(host, ports, timeout=float(data.get('timeout', 0.5)))
    return jsonify({'status': 'ok', **result})


@bp.route('/api/net/whois')
def api_net_whois():
    bad = _guard()
    if bad:
        return bad
    domain = request.args.get('domain')
    if not domain:
        return jsonify({'error': 'domain required'}), 400
    res = net.whois(domain)
    return jsonify({'status': 'ok', 'domain': domain, 'server': res['server'],
                    'chars': len(res.get('raw', '')), 'error': res.get('error')})


@bp.route('/api/net/geoip')
def api_net_geoip():
    bad = _guard()
    if bad:
        return bad
    ip = request.args.get('ip')
    if not ip:
        return jsonify({'error': 'ip required'}), 400
    return jsonify({'status': 'ok', 'geo': net.geoip(ip)})
