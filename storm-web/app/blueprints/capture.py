"""P3.2 - capture blueprint (stub). Routes split into capture_rx + capture_sessions
in this package for size management; both register on the same Flask blueprint
`bp` here so the factory wiring is unchanged.
"""
from __future__ import annotations

# The actual route decorators live in capture_rx.py + capture_sessions.py so
# this module stays small (each decorator body is ~30 lines).
from .capture_rx import bp  # noqa: F401  -- re-export
