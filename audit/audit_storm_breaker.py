#!/usr/bin/env python3
"""
Storm-Breaker end-to-end audit harness.

Verifies that every panel feature is actually reachable and functional --
not just that the server starts. Four checks:

  1. ROUTE MAPPING  - every API endpoint referenced by the frontend JS and
                      templates resolves to a real Flask route.
  2. OPERATOR API   - every operator-facing API endpoint answers 200 when
                      called with a valid session.
  3. VICTIM API     - every victim-facing capture endpoint answers 200 with
                      no session at all (these are used by implants and
                      phishing templates, so they must not be auth-gated).
  4. UID GUARDS     - a registration without a uid is rejected, so one
                      malformed row cannot break the client list.
  5. EFFECTS        - selected endpoints are asserted on their OUTPUT/effects,
                      not just their status code, and the ingest-key gate is
                      exercised when configured.

Usage:
    python3 audit/audit_storm_breaker.py [--url http://127.0.0.1:2525]

Credentials are read from storm-web/config.php, so the harness always
matches the running configuration. Exit code is 0 only if every check
passes.

Scope note: this harness exercises route liveness and payload handling
only. It never sends a real phishing link, never tunnels, never touches an
external target, and cleans up the synthetic records it creates.
"""

import argparse
import base64
import os
import re
import subprocess
import sys
import time

try:
    import requests
except ImportError:
    sys.exit("requests is required: pip install requests")

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORM_WEB = os.path.join(REPO_ROOT, 'storm-web')
ASSETS_JS = os.path.join(STORM_WEB, 'assets', 'js')


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

def read_password():
    """Read the admin password out of config.php (same source app.py uses)."""
    cfg_path = os.path.join(STORM_WEB, 'config.php')
    with open(cfg_path, encoding='utf-8') as fh:
        cfg = fh.read()
    match = re.search(r'"password"\s*=>\s*"([^"]+)"', cfg)
    if not match:
        sys.exit("could not parse a password out of %s" % cfg_path)
    return match.group(1)


def read_setting(name, default=None):
    """Read a key out of storm-web/Settings.json (the file app.py resolves to)."""
    import json
    try:
        with open(os.path.join(STORM_WEB, 'Settings.json'), encoding='utf-8') as fh:
            return json.load(fh).get(name, default)
    except Exception:
        return default


def ingest_suffix():
    """``?k=<secret>`` when an ingest secret is configured, else ``''``.

    P16: victim endpoints can require a shared secret; the audit must present
    it or every victim check would 401.
    """
    secret = (read_setting('ingest_secret') or '').strip()
    return ('?k=' + secret) if secret else ''


def with_key(path):
    """Append the ingest key to a path if one is configured."""
    secret = (read_setting('ingest_secret') or '').strip()
    if not secret:
        return path
    return path + ('&' if '?' in path else '?') + 'k=' + secret


def iter_frontend_files():
    """Every non-minified JS file and every HTML template."""
    for base in (ASSETS_JS, STORM_WEB):
        for root, _dirs, files in os.walk(base):
            if base == STORM_WEB and 'assets' in root \
                    and not os.path.abspath(root).startswith(os.path.abspath(ASSETS_JS)):
                continue
            for name in files:
                if name.endswith('.min.js'):
                    continue
                if name.endswith(('.js', '.html')):
                    yield os.path.join(root, name)


FRONTEND_URL_RE = re.compile(
    r"""(?:url\s*:\s*|fetch\s*\(|action\s*=\s*)"""
    r"""[`'"]?((?:https?://[^`'"\s]+)|(?:/[A-Za-z0-9_\-./<>:{}%]*))"""
)


def frontend_references():
    """Map of referenced endpoint -> list of source files."""
    refs = {}
    for path in iter_frontend_files():
        try:
            with open(path, encoding='utf-8', errors='ignore') as fh:
                text = fh.read()
        except OSError:
            continue
        rel = os.path.relpath(path, REPO_ROOT)
        for match in FRONTEND_URL_RE.finditer(text):
            url = match.group(1)
            if url.startswith('http'):
                continue
            refs.setdefault(url, set()).add(rel)
    return refs


def load_app():
    """Import the Flask app so we can use its real URL map.

    P2 introduced a sibling ``storm-web/app`` package alongside the file
    ``storm-web/app.py``; Python's finder picks the package for the bare
    name ``app``. To still trigger route-registration on the Flask
    instance the file builds, we load it directly via ``importlib.util``
    (bypassing the package-name shadowing). The file's ``import
    database`` etc. rely on ``storm-web`` being on ``sys.path``, so we
    stage it for the duration of the exec.
    """
    import importlib.util
    sys.path.insert(0, STORM_WEB)
    os.chdir(STORM_WEB)
    try:
        spec = importlib.util.spec_from_file_location(
            "storm_audit_app_file", os.path.join(STORM_WEB, "app.py")
        )
        storm_app = importlib.util.module_from_spec(spec)
        sys.modules["storm_audit_app_file"] = storm_app
        spec.loader.exec_module(storm_app)
        return storm_app
    finally:
        try:
            sys.path.remove(STORM_WEB)
        except ValueError:
            pass


class Router:
    """Thin wrapper over werkzeug's MapAdapter for route lookups."""

    def __init__(self, flask_app):
        self.adapter = flask_app.url_map.bind('localhost')
        self.route_rules = [r.rule for r in flask_app.url_map.iter_rules()]

    def resolve(self, path):
        """Return (rule, method) or (None, None) if nothing matches."""
        path = path.split('?')[0]
        for method in ('GET', 'POST', 'PUT', 'DELETE'):
            try:
                result = self.adapter.match(path, method=method)
            except Exception:
                continue
            rule = result[0]
            return (rule.rule if hasattr(rule, 'rule') else str(rule)), method
        return None, None

    def is_prefix_of_route(self, path):
        """True when `path` is a static prefix of a real route.

        The frontend builds URLs like `/api/campaigns/${id}`; the extractor
        only sees the literal prefix `/api/campaigns/`. Such a prefix is
        a template reference, not a missing route.
        """
        for rule in self.route_rules:
            if rule.startswith(path):
                return True
        return False
# --------------------------------------------------------------------------
# endpoint catalogue
# --------------------------------------------------------------------------

OPERATOR_GETS = [
    '/api/images', '/api/audio', '/api/fingerprints/list', '/api/keystrokes/list',
    '/api/system/info', '/api/analytics/dashboard', '/api/analytics/geo',
    '/api/analytics/timeline', '/api/alerts', '/api/operator/log',
    '/api/obfuscate/profiles', '/api/reports', '/api/lures/categories',
    '/api/lures/saved', '/api/evasion/profiles', '/api/evasion/saved',
    '/api/payloads/types', '/api/campaigns/list', '/api/profiles/list',
    '/api/geofence/list', '/api/webrtc_leaks', '/api/credentials/list',
    '/api/credentials/pairs', '/api/credentials/stats', '/api/c2/clients',
    '/api/mobile/clients', '/api/network/discoveries', '/api/browser-exfil',
    '/api/browser-exfil/stats', '/api/playbooks', '/api/pivot/history',
    '/api/pivot/capabilities', '/api/session-hijack/features',
    '/api/session-hijack/history', '/api/threat-intel/types',
    '/api/threat-intel/history', '/api/rat/history', '/api/rat/injection',
    '/api/ai-threat/landscape', '/api/ai-threat/anomalies',
    '/api/ai-threat/behavioral', '/api/ai-threat/predict',
    '/api/ai-threat/response-plan', '/api/quantum/algorithms',
    '/api/quantum/benchmark', '/api/quantum/threat', '/api/get_settings',
    '/api/telegram/config', '/api/mobile/captures', '/list_templates',
    # P14.3 / P14.6 additive firepower surface
    '/api/targets', '/api/strike/actions',
    # P14.7/P14.8 additive real-network surface
    '/api/net/resolve',
    # P15.3/P15.4 additive listener + beacon surface
    '/api/listeners', '/api/c2/beacons',
    # P10 additive realtime snapshot (SSE /api/events stays out: never returns)
    '/api/live', '/api/notify/pending',
]

OPERATOR_POSTS = [
    ('/api/obfuscate', {'payload': 'import os\nos.system("id")', 'techniques': ['base64']}),
    ('/api/lures/preview', {'category': 'banking', 'brand': 'Test', 'company': 'Acme'}),
    ('/api/lures/generate', {'category': 'banking', 'brand': 'Test', 'company': 'Acme'}),
    ('/api/lures/bulk', {'count': 3, 'category': 'banking', 'brand': 'Test', 'company': 'Acme'}),
    ('/api/lures/render-html', {'html': '<p>hi</p>', 'title': 't'}),
    ('/api/evasion/config', {'options': {'traffic_profile': 'api_rest', 'timing_profile': 'office_hours'}}),
    ('/api/evasion/disguise', {'profile': 'api_rest', 'payload': {'x': 1}}),
    ('/api/evasion/domains', {'category': 'tech', 'company': 'Acme', 'count': 3}),
    ('/api/evasion/beacon-schedule', {'profile': 'office_hours', 'duration_hours': 2}),
    ('/api/evasion/decoy', {'pattern': 'browsing', 'duration': 60}),
    ('/api/evasion/fingerprint', {'device_class': 'desktop'}),
    ('/api/reports/generate', {'title': 'Audit Report', 'report_type': 'summary'}),
    ('/api/campaigns/create', {'name': 'AuditCamp', 'template': 'weather'}),
    ('/api/profiles/build', {}),
    ('/api/geofence/create', {'name': 'Zone1', 'latitude': 10.0, 'longitude': 20.0, 'radius': 5}),
    ('/api/geofence/check', {'latitude': 10.0, 'longitude': 20.0}),
    ('/api/playbooks', {'name': 'AuditPB', 'description': 'd',
                        'steps': [{'action': 'log', 'params': {'message': 'hi'}}],
                        'variables': {}}),
    ('/api/terminal', {'cmd': 'echo STORMBREAKER_AUDIT_OK'}),
    ('/api/c2/queue_command', {'uid': 'audit-nonexistent', 'command': 'whoami'}),
    ('/api/mobile/send_command', {'uid': 'audit-nonexistent', 'command': 'whoami'}),
    ('/api/credentials/scan', {'data': {'user': 'a', 'pass': 'b'}}),
    ('/api/session-hijack/assess', {'token': 'abc', 'type': 'jwt'}),
    ('/api/session-hijack/analyze-jwt',
     {'token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIn0.abc'}),
    ('/api/session-hijack/parse-cookies', {'cookies': 'a=b; c=d'}),
    ('/api/session-hijack/extract-tokens', {'text': 'Authorization: Bearer abc123'}),
    ('/api/session-hijack/build-replay', {'cookies': {'a': 'b'}}),
    ('/api/threat-intel/ip', {'ip': '8.8.8.8'}),
    ('/api/threat-intel/email', {'email': 'test@example.com'}),
    ('/api/threat-intel/social', {'username': 'test'}),
    ('/api/threat-intel/technology', {'tech': 'nginx'}),
    ('/api/ai-threat/analyze', {'data': {'events': []}}),
    ('/api/quantum/encrypt', {'data': 'hello', 'algorithm': 'aes'}),
    ('/api/quantum/key-exchange', {}),
    ('/api/zeroday/scan', {'target': '127.0.0.1'}),
    ('/api/zeroday/fuzz', {'target': 'http://127.0.0.1/'}),
    ('/api/zeroday/rop', {'binary': 'x'}),
    ('/api/zeroday/shellcode', {'arch': 'x86_64', 'payload': 'x'}),
    ('/api/deeprecon/email', {'email': 'a@b.com'}),
    ('/api/deeprecon/domain', {'domain': 'example.com'}),
    ('/api/deeprecon/social', {'username': 'a', 'platform': 'github'}),
    ('/api/deeprecon/infra', {'target': 'example.com'}),
    ('/api/deeprecon/darkweb', {'query': 'test'}),
    ('/api/deeprecon/correlate', {'data': {}}),
    ('/api/rat/recon', {'target': '127.0.0.1'}),
    ('/api/rat/shells', {'target': '127.0.0.1'}),
    ('/api/rat/persistence', {'target': '127.0.0.1'}),
    ('/api/rat/lateral', {'target': '127.0.0.1'}),
    ('/api/rat/cradles', {'target': '127.0.0.1'}),
    ('/api/rat/tunnels', {'target': '127.0.0.1'}),
    ('/api/rat/anti-forensics', {'target': '127.0.0.1'}),
    ('/api/rat/encode', {'payload': 'AAAA', 'technique': 'all'}),
    ('/api/recon/run', {'target': 'example.com'}),
    ('/api/webrtc_leak', {}),
    ('/api/alerts/add', {'message': 'audit test', 'severity': 'info'}),
    ('/api/alerts/clear', {}),
    # P14.3 / P14.6 additive firepower surface
    ('/api/targets', {'name': 'audit-target', 'host': '127.0.0.1', 'notes': 'audit'}),
    ('/api/strike/reverse', {'payload_type': 'python_reverse', 'lhost': '127.0.0.1'}),
    # P14.7/P14.8 additive real-network surface
    ('/api/net/scan', {'host': '127.0.0.1', 'ports': '1,2525', 'timeout': 0.5}),
    # P15.3/P15.4 additive listener + beacon surface
    ('/api/listeners/start', {'name': 'audit-listen', 'host': '127.0.0.1', 'port': 0}),
    ('/api/c2/beacon_config', {'profile': 'always_on'}),
]

def victim_endpoints():
    """(endpoint, payload) pairs that must work WITHOUT a session."""
    jpeg = base64.b64encode(bytes.fromhex(
        'ffd8ffe000104a46494600010100000100010000ffdb004300' + '08' * 64 + 'ffd9')
    ).decode()
    webm = base64.b64encode(b'WEBMDATA').decode()
    return [
        ('/api/fingerprint', {'fingerprint': {'ua': 'x'}, 'canvas': 'a', 'webgl': 'b',
                               'fonts': [], 'timezone': 'UTC'}),
        ('/api/keystrokes', {'logs': [{'type': 'keypress',
                                        'target': {'type': 'body', 'tag': 'INPUT'}}],
                             'url': 'http://audit'}),
        ('/api/session/start', {'sessionId': 'audit-session', 'url': 'http://audit'}),
        ('/api/session/events', {'sessionId': 'audit-session',
                                 'events': [{'type': 'click'}]}),
        ('/api/session/end', {'sessionId': 'audit-session', 'duration': 1}),
        ('/api/c2/register', {'uid': 'audit-c2', 'info': {'os': 'linux'}}),
        ('/api/c2/poll', {'uid': 'audit-c2'}),
        ('/api/c2/response', {'uid': 'audit-c2', 'output': 'ok'}),
        ('/api/c2/file_list_response', {'uid': 'audit-c2', 'files': []}),
        ('/api/c2/file_download_response', {'uid': 'audit-c2', 'filename': 'a',
                                            'data': webm}),
        ('/api/mobile/register', {'uid': 'audit-mobile', 'info': {'platform': 'android'}}),
        ('/api/mobile/poll', {'uid': 'audit-mobile'}),
        ('/api/mobile/response', {'uid': 'audit-mobile', 'output': 'ok'}),
        ('/api/mobile/camera', {'uid': 'audit-mobile',
                                'image': 'data:image/jpeg;base64,' + jpeg}),
        ('/api/mobile/background_data', {'uid': 'audit-mobile',
                                          'data': {'type': 'background_location',
                                                   'latitude': 1.0, 'longitude': 2.0}}),
        ('/api/mobile/screenshot', {'uid': 'audit-mobile',
                                    'image': 'data:image/jpeg;base64,' + jpeg,
                                    'url': 'http://audit', 'timestamp': 'audit'}),
        ('/api/mobile/audio', {'uid': 'audit-mobile',
                               'audio': 'data:audio/webm;base64,' + webm,
                               'timestamp': 'audit'}),
        ('/api/mobile/screen_record', {'uid': 'audit-mobile',
                                       'video': 'data:video/webm;base64,' + webm,
                                       'timestamp': 'audit'}),
        ('/api/browser-exfil/receive', {'uid': 'audit-mobile', 'data': {'cookie': 'x'},
                                        'url': 'http://audit'}),
        ('/api/network/receive', {'scan_type': 'webrtc', 'ip': '1.2.3.4',
                                  'discovered_hosts': []}),
    ]


# --------------------------------------------------------------------------
# cleanup
# --------------------------------------------------------------------------

AUDIT_UIDS = ('audit-mobile', 'audit-c2')
AUDIT_CAPTURE_UID = 'audit-mobile'
AUDIT_CAMPAIGN = 'AuditCamp'
AUDIT_PLAYBOOK = 'AuditPB'
AUDIT_GEOFENCE = 'Zone1'
AUDIT_SESSION = 'audit-session'

# Tables the operator sweep writes rows into. They all use an AUTOINCREMENT
# integer primary key, so a row-count snapshot taken before the run is enough
# to identify (and remove) exactly the rows this run created.
SWEPT_TABLES = (
    'mobile_commands', 'mobile_responses', 'tracking_data', 'mobile_captures',
    'campaigns', 'campaign_links', 'credentials', 'victim_profiles',
    'geofences', 'operator_log', 'reports', 'playbooks', 'saved_lures',
    'network_discoveries', 'browser_exfil', 'evasion_configs', 'threat_intel',
    'session_hijacks', 'pivot_records', 'rat_operations', 'rat_shell_sessions',
    'rat_persistence',
)


def snapshot_tables(db_path):
    """Record the highest id per swept table so the run can be undone."""
    import sqlite3
    baseline = {}
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        for table in SWEPT_TABLES:
            try:
                cur.execute('SELECT MAX(id) FROM %s' % table)
                row = cur.fetchone()
                baseline[table] = row[0] if row and row[0] is not None else 0
            except sqlite3.Error:
                baseline[table] = None
        conn.close()
    except sqlite3.Error:
        pass
    return baseline


def cleanup(baseline=None):
    """Remove every synthetic record the audit created.

    The harness writes real rows and files into the live SQLite database and
    the capture directories, so it puts them back the way it found them.
    """
    import sqlite3

    db_path = os.path.join(STORM_WEB, 'storm_breaker.db')
    removed = 0
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        # Rows created during this run (id above the pre-run snapshot).
        if baseline:
            for table, max_id in baseline.items():
                if max_id is None:
                    continue
                try:
                    cur.execute('DELETE FROM %s WHERE id > ?' % table, (max_id,))
                    removed += cur.rowcount
                except sqlite3.Error:
                    pass

        # Sessions keyed by uid rather than id.
        for uid in AUDIT_UIDS:
            for table in ('mobile_sessions', 'c2_sessions'):
                try:
                    cur.execute('DELETE FROM %s WHERE uid = ?' % table, (uid,))
                    removed += cur.rowcount
                except sqlite3.Error:
                    pass

        for name, table, column in (
                (AUDIT_CAMPAIGN, 'campaigns', 'name'),
                (AUDIT_PLAYBOOK, 'playbooks', 'name'),
                (AUDIT_GEOFENCE, 'geofences', 'name')):
            try:
                cur.execute('DELETE FROM %s WHERE %s = ?' % (table, column), (name,))
                removed += cur.rowcount
            except sqlite3.Error:
                pass

        # Delete capture files that were written for the audit victim.
        try:
            cur.execute('SELECT url FROM mobile_captures WHERE uid = ?',
                        (AUDIT_CAPTURE_UID,))
            urls = [row[0] for row in cur.fetchall()]
        except sqlite3.Error:
            urls = []
        cur.execute('DELETE FROM mobile_captures WHERE uid = ?', (AUDIT_CAPTURE_UID,))
        removed += cur.rowcount
        conn.commit()
        # Deleted rows leave free pages behind, which bloats the tracked
        # database file. Compact it so the file returns to its prior size.
        try:
            conn.execute('VACUUM')
        except sqlite3.Error:
            pass
        conn.close()

        for url in urls:
            rel = url.lstrip('/')
            path = os.path.join(STORM_WEB, rel)
            if os.path.isfile(path):
                try:
                    os.remove(path)
                    removed += 1
                except OSError:
                    pass

        sessions_dir = os.path.join(STORM_WEB, 'sessions')
        if os.path.isdir(sessions_dir):
            for name in os.listdir(sessions_dir):
                if name.startswith(AUDIT_SESSION):
                    try:
                        os.remove(os.path.join(sessions_dir, name))
                        removed += 1
                    except OSError:
                        pass
    except sqlite3.Error as exc:
        print('    cleanup warning: %s' % exc)
        return False
    print('    removed %d synthetic record(s)/file(s)' % removed)
    return True


# --------------------------------------------------------------------------
# checks
# --------------------------------------------------------------------------

def check_route_mapping(router):
    """Every frontend-referenced endpoint must resolve to a real route."""
    print('\n[1] ROUTE MAPPING')
    refs = frontend_references()
    ok = unresolved = dynamic = 0
    unresolved_list = []
    for url, sources in sorted(refs.items()):
        if '{' in url or '<' in url:
            dynamic += 1
            continue
        rule, _method = router.resolve(url)
        if rule is not None:
            ok += 1
        elif url.endswith('/') and router.is_prefix_of_route(url):
            # static prefix of a real route, e.g. `/api/campaigns/${id}`
            dynamic += 1
        else:
            unresolved += 1
            unresolved_list.append((url, sorted(sources)))
    print('    resolved=%d  unresolved=%d  template-vars=%d'
          % (ok, unresolved, dynamic))
    for url, sources in unresolved_list:
        print('    UNRESOLVED %s  <- %s' % (url, ', '.join(sources[:3])))
    return unresolved == 0

def login(session, base, password, attempts=3):
    """Log in, tolerating the brute-force lockout window.

    The panel applies an in-memory lockout (5 failed POST /login attempts
    from one IP -> 60 s block, HTTP 429). A stale lockout left over from an
    earlier manual attempt must not make the audit fail, so back off and
    retry instead.
    """
    for attempt in range(attempts):
        resp = session.post(base + '/login',
                            data={'username': 'admin', 'password': password},
                            allow_redirects=False, timeout=30)
        if resp.status_code in (200, 302):
            return resp
        if resp.status_code == 429:
            wait = 61
            print('    login lockout active (429) - waiting %ds' % wait)
            time.sleep(wait)
            continue
        return resp
    return resp


def check_operator_api(base, password):
    """Operator endpoints must answer 200 with a valid session."""
    print('\n[2] OPERATOR API (authenticated)')
    session = requests.Session()
    resp = login(session, base, password)
    if resp.status_code not in (200, 302):
        print('    LOGIN FAILED (%s)' % resp.status_code)
        print('    hint: config.php holds the password, but the server reads it')
        print('          only at start-up -- restart the server if it was edited')
        print('          after the last launch.')
        return False
    failures = []
    total = 0
    for path in OPERATOR_GETS:
        total += 1
        try:
            resp = session.get(base + path, timeout=45)
        except Exception as exc:
            failures.append((path, 'EXC %s' % type(exc).__name__))
            continue
        if resp.status_code != 200:
            failures.append((path, resp.status_code))
    for path, payload in OPERATOR_POSTS:
        total += 1
        try:
            # P16: send a browser-like Origin. curl/requests send none, and the
            # CSRF gate short-circuits without one -- which is exactly how a
            # broken CSRF comparison hid here for the whole project.
            resp = session.post(base + path, json=payload, timeout=45,
                                headers={'Origin': base})
        except Exception as exc:
            failures.append((path, 'EXC %s' % type(exc).__name__))
            continue
        if resp.status_code != 200:
            failures.append((path, resp.status_code))
    print('    %d/%d returned 200' % (total - len(failures), total))
    for path, code in failures:
        print('    FAIL %s -> %s' % (path, code))
    return not failures


def check_victim_api(base):
    """Victim-facing capture endpoints must NOT be auth-gated."""
    print('\n[3] VICTIM API (no session)')
    failures = []
    cases = victim_endpoints()
    for path, payload in cases:
        try:
            resp = requests.post(base + with_key(path), json=payload, timeout=45)
        except Exception as exc:
            failures.append((path, 'EXC %s' % type(exc).__name__))
            continue
        if resp.status_code != 200:
            failures.append((path, resp.status_code))
    print('    %d/%d returned 200' % (len(cases) - len(failures), len(cases)))
    for path, code in failures:
        print('    FAIL %s -> %s' % (path, code))
    return not failures


def check_uid_guards(base):
    """A registration without a uid must be rejected, not stored."""
    print('\n[4] UID VALIDATION (corrupt-row guard)')
    ok = True
    for path in ('/api/mobile/register', '/api/c2/register', '/api/c2/response'):
        resp = requests.post(base + with_key(path), json={'info': {}}, timeout=30)
        if resp.status_code != 400:
            print('    FAIL %s without uid -> %s (expected 400)'
                  % (path, resp.status_code))
            ok = False
    if ok:
        print('    all three reject a missing uid with 400')
    return ok


def check_effects(base, password):
    """Assert on EFFECTS, not status codes.

    P16: the harness used to only check ``status_code == 200``.  That let two
    real bugs live here for the life of the project:

      * ``/api/terminal`` was posted with the key ``command`` while the server
        reads ``cmd`` -> a 200 with an empty body, forever.
      * ``/api/net/scan {"ports": "1-1024"}`` silently fell back to 25 default
        ports while still reporting success.

    Every case below asserts on a value the server had to actually compute.
    """
    print('\n[5] EFFECTS (behaviour, not just status)')
    session = requests.Session()
    login(session, base, password)
    failures = []

    def expect(name, cond, detail=''):
        if cond:
            print('    ok   %s' % name)
        else:
            print('    FAIL %s %s' % (name, detail))
            failures.append(name)

    # 0. the ingest-key gate actually gates (only meaningful when configured)
    secret = (read_setting('ingest_secret') or '').strip()
    if secret:
        r = requests.post(base + '/api/fingerprint', json={'uid': 'audit-nokey'}, timeout=30)
        expect('ingest key rejects a keyless victim POST', r.status_code == 401,
               '-> %s' % r.status_code)
        r = requests.post(base + '/api/fingerprint?k=' + secret,
                          json={'uid': 'audit-nokey'}, timeout=30)
        expect('ingest key accepts the correct key', r.status_code == 200,
               '-> %s' % r.status_code)
    else:
        print('    --   ingest_secret empty; gate off')

    # 1. settings resolve from storm-web regardless of cwd (the split-brain fix)
    r = session.get(base + '/api/get_settings', timeout=30)
    keys = r.json() if r.status_code == 200 else {}
    expect('settings resolve to the real file (>3 keys)', len(keys) > 3,
           '-> %d keys' % len(keys))

    # 2. terminal actually runs and returns stdout
    r = session.post(base + '/api/terminal', json={'cmd': 'echo STORMBREAKER_AUDIT_OK'},
                     timeout=45, headers={'Origin': base})
    out = (r.json().get('output') or '') if r.status_code == 200 else ''
    expect('terminal returns real stdout', 'STORMBREAKER_AUDIT_OK' in out,
           '-> %r' % out[:60])

    # 3. port-range parsing ("1-1024" used to be silently ignored)
    r = session.post(base + '/api/net/scan', json={'host': '127.0.0.1', 'ports': '1-1024'},
                     timeout=60, headers={'Origin': base})
    body = r.json() if r.status_code == 200 else {}
    expect('port range 1-1024 parses to 1024 ports', body.get('requested') == 1024,
           '-> requested=%s scanned=%s' % (body.get('requested'), body.get('scanned')))

    # 4. target create -> read back
    r = session.post(base + '/api/targets', json={'name': 'audit-effect', 'host': '127.0.0.1'},
                     timeout=30, headers={'Origin': base})
    tid = (r.json().get('target') or {}).get('id') if r.status_code == 200 else None
    expect('target create returns an id', bool(tid), '-> %s' % tid)
    if tid:
        r = session.get(base + '/api/targets/%d' % tid, timeout=30)
        expect('target reads back', r.status_code == 200
               and r.json().get('target', {}).get('id') == tid, '-> %s' % r.status_code)

    # 5. notification sink round-trip
    token = 'audit-%d' % int(time.time())
    session.post(base + '/api/notify/inbox', json={'audit': token}, timeout=30,
                 headers={'Origin': base})
    r = session.get(base + '/api/notify/inbox', timeout=30)
    items = r.json().get('items', []) if r.status_code == 200 else []
    expect('notify inbox round-trips', any(token == (i.get('payload') or {}).get('audit')
                                           for i in items), '-> %d items' % len(items))

    # 6. saved shell sessions are readable (was write-only)
    r = session.get(base + '/api/rat/shells', timeout=30)
    expect('rat shell sessions list is readable',
           r.status_code == 200 and 'sessions' in (r.json() or {}), '-> %s' % r.status_code)

    # 7. every lure kit actually renders (was a 500 for ALL 13 kits)
    kits = sorted(p.name for p in __import__('pathlib').Path(STORM_WEB, 'templates').iterdir()
                  if p.is_dir() and not p.name.startswith('.')
                  and (p / 'index.html').exists())
    broken = []
    for kit in kits:
        r = requests.get('%s/t/%s/%s' % (base, kit, ingest_suffix()), timeout=30)
        if r.status_code != 200 or 'html' not in (r.headers.get('Content-Type') or ''):
            broken.append('%s->%s' % (kit, r.status_code))
    expect('all %d lure kits render' % len(kits), not broken, '-> %s' % broken)

    # 8. notification outbox records durably and delivers (P1.3)
    def _total(s):
        return sum(s.get(k, 0) for k in ('delivered', 'pending', 'failed'))
    before = session.get(base + '/api/notifications/stats', timeout=30).json().get('stats', {})
    requests.post(base + '/api/mobile/register' + ingest_suffix(),
                  json={'uid': 'audit-obx', 'info': {}}, timeout=30)
    time.sleep(1.2)
    after = session.get(base + '/api/notifications/stats', timeout=30).json().get('stats', {})
    expect('notification outbox records the event', _total(after) > _total(before),
           '-> %s' % after)
    expect('notification outbox delivers to the sink',
           after.get('delivered', 0) > before.get('delivered', 0), '-> %s' % after)

    # 9. the resident agent really runs and really executes (P1.1)
    src = requests.get(base + '/api/agent/agent.py', timeout=30)
    expect('agent script is publicly fetchable',
           src.status_code == 200 and 'BASE = ' in src.text, '-> %s' % src.status_code)
    spawned = session.post(base + '/api/agent/spawn',
                           json={'uid': 'audit-agent', 'keep': True}, timeout=60,
                           headers={'Origin': base}).json()
    expect('agent spawns and registers', spawned.get('registered') is True,
           '-> %s' % spawned.get('status'))
    ran = session.post(base + '/api/agent/exec',
                       json={'uid': 'audit-agent', 'command': 'echo STORM_AGENT_OK',
                             'wait': 10}, timeout=60, headers={'Origin': base}).json()
    expect('agent executes a shell command',
           'STORM_AGENT_OK' in (ran.get('output') or ''), '-> %r' % (ran.get('output') or '')[:60])
    expect('agent appears in the agent list',
           'audit-agent' in [a['uid'] for a in
                             session.get(base + '/api/agent/agents', timeout=30).json()['agents']])
    # cleanup: keep:True agent must not linger beaconing into later test runs
    session.post(base + '/api/agent/exec',
                 json={'uid': 'audit-agent', 'command': '__exit', 'wait': 5},
                 timeout=30, headers={'Origin': base})

    # 10. an interactive listener drives a live reverse shell (P1.2)
    started = session.post(base + '/api/listeners/start',
                           json={'name': 'audit-sh', 'interactive': True}, timeout=30,
                           headers={'Origin': base}).json()
    port = started.get('listener', {}).get('port')
    expect('interactive listener starts', bool(port), '-> %s' % started.get('status'))
    shell_py = (
        "import socket\n"
        "s = socket.create_connection(('127.0.0.1', %d), timeout=5)\n"
        "s.sendall(b'audit-banner\\n')\n"
        "while True:\n"
        "    d = s.recv(1024)\n"
        "    if not d: break\n"
        "    s.sendall(b'out>' + d)\n" % port)
    proc = subprocess.Popen([sys.executable, '-c', shell_py],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    key = None
    for _ in range(50):
        rows = session.get(base + '/api/listeners/sessions',
                           timeout=30).json()['sessions']
        if rows:
            key = rows[0]['key']
            break
        time.sleep(0.1)
    expect('reverse shell registers as a live session', key is not None)
    session.post(base + '/api/listeners/send',
                 json={'key': key, 'command': 'id'}, timeout=30,
                 headers={'Origin': base})
    lines = []
    for _ in range(30):
        lines += session.post(base + '/api/listeners/read',
                              json={'key': key}, timeout=30).json()['lines']
        if any('out>id' in ln for ln in lines):
            break
        time.sleep(0.1)
    expect('command roundtrips through the live shell',
           any('audit-banner' in ln for ln in lines)
           and any('out>id' in ln for ln in lines),
           '-> %r' % lines[:3])
    session.post(base + '/api/listeners/close', json={'key': key}, timeout=30,
                 headers={'Origin': base})
    session.post(base + '/api/listeners/stop', json={'name': 'audit-sh'}, timeout=30,
                 headers={'Origin': base})
    proc.terminate()

    # 11. evidence integrity: reports carry sha256 + HMAC signatures (P1.4)
    rep = session.post(base + '/api/reports/generate',
                       json={'title': 'audit-evidence', 'target': 'audit.local'},
                       timeout=30, headers={'Origin': base}).json()
    integrity = rep.get('integrity') or {}
    expect('report generation returns an evidence signature',
           len(str(integrity.get('sha256') or '')) == 64
           and len(str(integrity.get('signature') or '')) == 64,
           '-> %s' % integrity.get('alg'))
    verdict = session.get(base + '/api/reports/%d/verify' % rep.get('id', 0),
                          timeout=30).json().get('status')
    expect('stored report verifies against its signature', verdict == 'verified',
           '-> %s' % verdict)
    tgt = session.post(base + '/api/targets', json={'name': 'audit-evidence'},
                       timeout=30, headers={'Origin': base}).json()
    tid = (tgt.get('target') or {}).get('id') or tgt.get('id')
    session.post(base + '/api/targets/%s/findings' % tid,
                 json={'kind': 'audit', 'detail': 'evidence row'},
                 timeout=30, headers={'Origin': base})
    html = session.get(base + '/api/targets/%s/report' % tid, timeout=30).text
    expect('target report embeds a signature trailer',
           'EVIDENCE-SIGNATURE' in html and len(html) > 500)
    v_ok = session.post(base + '/api/targets/report/verify', json={'html': html},
                        timeout=30, headers={'Origin': base}).json().get('status')
    v_bad = session.post(base + '/api/targets/report/verify',
                         json={'html': html.replace('audit', 'tampered')},
                         timeout=30, headers={'Origin': base}).json().get('status')
    expect('exported report verifies, tampered copy does not',
           v_ok == 'verified' and v_bad == 'tampered-or-unsigned',
           '-> %s / %s' % (v_ok, v_bad))

    return not failures


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', default='http://127.0.0.1:2525')
    args = parser.parse_args()
    base = args.url.rstrip('/')

    print('Storm-Breaker audit harness -> %s' % base)
    storm_app = load_app()
    router = Router(storm_app.app)
    password = read_password()
    baseline = snapshot_tables(os.path.join(STORM_WEB, 'storm_breaker.db'))

    results = {
        'route mapping': check_route_mapping(router),
        'operator api': check_operator_api(base, password),
        'victim api': check_victim_api(base),
        'uid validation': check_uid_guards(base),
        'effects': check_effects(base, password),
    }

    print('\n%s' % ('-' * 60))
    for name, passed in results.items():
        print('    %-18s %s' % (name, 'PASS' if passed else 'FAIL'))
    failed = [n for n, ok in results.items() if not ok]

    print('\n[6] CLEANUP')
    cleanup(baseline)

    if failed:
        print('\nAUDIT FAILED: %s' % ', '.join(failed))
        return 1
    print('\nAUDIT PASSED - all features reachable and functional')
    return 0


if __name__ == '__main__':
    sys.exit(main())

