"""Storm-Breaker core layer (HANDOFF plan section P5).

Owns the process-wide primitives the rest of the app is built on:

- :mod:`app.core.state`   -- ``StateStore`` interface + ``MemoryStore``
  (behavior-identical in-memory default).
- :mod:`app.core.db`      -- ``Repository``: a thin 1:1 delegate over the
  frozen ``storm-web/database.py`` module (P5.4).
- :mod:`app.core.migrations` -- baseline schema + WAL / index migrations
  (P5.5, P5.6).

Nothing in this package changes request behavior; blueprints keep their
frozen HTTP contract (NR-2).
"""
