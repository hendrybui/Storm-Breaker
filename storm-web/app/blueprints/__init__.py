"""Per-domain Flask blueprints extracted from storm-web/app.py (P3.x).

Each module here owns one logical surface (auth, capture, c2, ...). The
factory in ``storm-web/app/__init__.py::create_app`` registers the
blueprints at import time.

NR-2 contract: import order, dict identity, and route paths here are all
preserved -- ``tests/char/test_*.py`` snapshots are the safety net.
"""
