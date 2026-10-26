"""ai_threat blueprint (P3 batch extract)."""
from __future__ import annotations

import os, json, base64
import uuid as uuid_module
from datetime import datetime, timedelta
from functools import wraps
from flask import (Blueprint, request, jsonify, redirect, url_for, render_template, send_from_directory, make_response, session, Response)
from app.state import *  # noqa: F401,F403  -- P3
from app.state import BASE_DIR, CONFIG, _decode_data_url, _save_mobile_capture
import database as db

from ai_threat_analyzer import AIThreatAnalyzer
bp = Blueprint("ai_threat", __name__,
               template_folder=os.path.join(BASE_DIR, "flask_templates"))


@bp.route('/api/ai-threat/analyze', methods=['POST'])

def api_ai_threat_analyze():
    payload = request.form.get('payload', '')
    result = AIThreatAnalyzer.analyze_payload(payload)
    return jsonify({'success': True, 'result': result})

@bp.route('/api/ai-threat/behavioral', methods=['GET'])

def api_ai_threat_behavioral():
    ip = request.args.get('ip', '0.0.0.0')
    result = AIThreatAnalyzer.behavioral_analysis(ip)
    return jsonify({'success': True, 'result': result})

@bp.route('/api/ai-threat/anomalies', methods=['GET'])

def api_ai_threat_anomalies():
    result = AIThreatAnalyzer.detect_anomalies()
    return jsonify({'success': True, 'result': result})

@bp.route('/api/ai-threat/predict', methods=['GET'])

def api_ai_threat_predict():
    result = AIThreatAnalyzer.predictive_model()
    return jsonify({'success': True, 'result': result})

@bp.route('/api/ai-threat/response-plan', methods=['GET'])

def api_ai_threat_response_plan():
    threat_type = request.args.get('type', 'malware')
    severity = request.args.get('severity', 'high')
    result = AIThreatAnalyzer.generate_response_plan(threat_type, severity)
    return jsonify({'success': True, 'result': result})

@bp.route('/api/ai-threat/landscape', methods=['GET'])

def api_ai_threat_landscape():
    result = AIThreatAnalyzer.get_threat_landscape()
    return jsonify({'success': True, 'result': result})
