"""zeroday blueprint (P3 batch extract)."""
from __future__ import annotations

import os, json, base64
import uuid as uuid_module
from datetime import datetime, timedelta
from functools import wraps
from flask import (Blueprint, request, jsonify, redirect, url_for, render_template, send_from_directory, make_response, session, Response)
from app.state import *  # noqa: F401,F403  -- P3
from app.state import BASE_DIR, CONFIG, _decode_data_url, _save_mobile_capture
import database as db

from zeroday_lab import ZeroDayLab
bp = Blueprint("zeroday", __name__,
               template_folder=os.path.join(BASE_DIR, "flask_templates"))


@bp.route('/api/zeroday/scan', methods=['POST'])

def api_zeroday_scan():
    target = request.form.get('target', '')
    scan_type = request.form.get('scan_type', 'full')
    result = ZeroDayLab.scan_target(target, scan_type)
    return jsonify({'success': True, 'result': result})

@bp.route('/api/zeroday/shellcode', methods=['POST'])

def api_zeroday_shellcode():
    sc_type = request.form.get('type', 'reverse_tcp_x64')
    lhost = request.form.get('lhost', '0.0.0.0')
    lport = request.form.get('lport', '4444')
    result = ZeroDayLab.generate_shellcode(sc_type, lhost, int(lport))
    return jsonify({'success': True, 'result': result})

@bp.route('/api/zeroday/rop', methods=['POST'])

def api_zeroday_rop():
    binary = request.form.get('binary', 'libc.so.6')
    func = request.form.get('target_function', 'system')
    result = ZeroDayLab.build_rop_chain(binary, func)
    return jsonify({'success': True, 'result': result})

@bp.route('/api/zeroday/fuzz', methods=['POST'])

def api_zeroday_fuzz():
    target = request.form.get('target', '')
    fuzz_type = request.form.get('fuzz_type', 'smart')
    result = ZeroDayLab.run_fuzzer(target, fuzz_type)
    return jsonify({'success': True, 'result': result})

@bp.route('/api/zeroday/cves', methods=['GET'])

def api_zeroday_cves():
    query = request.args.get('query', '')
    severity = request.args.get('severity', 'all')
    result = ZeroDayLab.search_cves(query, severity)
    return jsonify({'success': True, 'result': result})

@bp.route('/api/zeroday/shellcode-types', methods=['GET'])

def api_zeroday_shellcode_types():
    result = ZeroDayLab.get_shellcode_types()
    return jsonify({'success': True, 'result': result})
