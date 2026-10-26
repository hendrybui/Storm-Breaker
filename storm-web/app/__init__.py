"""Storm-Breaker Flask application factory (HANDOFF plan section P2).

This package owns the Flask app's construction.  ``create_app()`` is the
single entry point used by both the legacy ``app.py`` shim and the
characterisation-test fixture.

Behaviour-preserving scope (NR-2): the factory only re-implements what
``storm-web/app.py`` lines 22-43 did at module-load time -- Flask
construction, secret-key load/persist, ``MAX_CONTENT_LENGTH`` override.
Route definitions, module-level globals (``CONFIG``, ``_LOGIN_FAILS``,
``C2_*``, ``_VICTIM_PUBLIC_*``, ``ANALYTICS``, ``RECON_CONFIG``,
``load_php_config``) and the ``@app.before_request`` auth / throttle
hooks stay in ``storm-web/app.py`` until P4-P5 move them into
services / state adapters.
"""
from __future__ import annotations

import os
import secrets as _secrets
import sys

# ``storm-web/app`` is a sub-package of ``storm-web``.  To import sibling
# modules the way ``app.py`` does today (each at module top level), the
# parent directory must be on ``sys.path``.
_HERE = os.path.dirname(os.path.abspath(__file__))
_PARENT = os.path.dirname(_HERE)
if _PARENT not in sys.path:
    sys.path.insert(0, _PARENT)


from flask import Flask  # noqa: E402

SECRET_KEY_PATH = os.path.join(_PARENT, "secret_key.bin")

DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 2525
STATIC_FOLDER = os.path.join(_PARENT, "assets")
TEMPLATE_FOLDER = os.path.join(_PARENT, "flask_templates")


def _load_or_create_secret_key() -> str:
    """Mirror app.py lines 28-39.

    Persistent random hex token stored in ``secret_key.bin`` so Flask
    sessions survive restarts.  An empty / missing file is regenerated.
    """
    try:
        with open(SECRET_KEY_PATH, encoding="utf-8") as fh:
            sk = fh.read().strip()
        if sk:
            return sk
    except OSError:
        pass
    sk = _secrets.token_hex(32)
    try:
        with open(SECRET_KEY_PATH, "w", encoding="utf-8") as fh:
            fh.write(sk)
    except OSError:
        # If we cannot persist the key (read-only fs etc.) keep the
        # in-memory value anyway; operator session will still work
        # for the lifetime of the process.
        pass
    return sk


def create_app() -> Flask:
    """Instantiate the Storm-Breaker Flask app, identically to app.py 0.X.X.

    Returns the configured app with secret_key + content-length disabled,
    plus every ``app.blueprints.*`` Blueprint registered (P3.x extracts
    share this single factory call).
    """
    app = Flask(__name__, static_folder=STATIC_FOLDER,
                template_folder=TEMPLATE_FOLDER)
    app.secret_key = _load_or_create_secret_key()
    # Disable upload size limit completely (verbatim from app.py:43).
    app.config["MAX_CONTENT_LENGTH"] = None
    app.config["PORT"] = int(os.environ.get("STORM_WEB_PORT", DEFAULT_PORT))
    app.config["HOST"] = os.environ.get("STORM_WEB_HOST", DEFAULT_HOST)

    # ----------------------------------------------------------------------------
    # Blueprint registration (P3.x).  Each import triggers the verb-module-level
    # decorators to run, attaching routes to their Blueprint objects.  Order is
    # irrelevant because each Blueprint owns a disjoint URL set.
    # ----------------------------------------------------------------------------
    from app.blueprints import auth  # noqa: F401  -- P3.1
    from app.blueprints import capture_rx          # noqa: F401  -- P3.2
    from app.blueprints import capture_sessions    # noqa: F401  -- P3.2
    app.register_blueprint(auth.bp)
    app.register_blueprint(capture_rx.bp)
    app.register_blueprint(capture_sessions.bp)

    return app


__all__ = ["create_app", "SECRET_KEY_PATH",
           "DEFAULT_HOST", "DEFAULT_PORT",
           "STATIC_FOLDER", "TEMPLATE_FOLDER"]
