"""Module adapters -- expose the 15 frozen modules as runnable Actions (P14.4).

Public surface::

    from app.adapters import get, call, names, modules, describe, actions_for

Importing this package registers the whole catalog (``app.adapters.catalog``).
The frozen modules themselves are never edited (NR-3).
"""
from __future__ import annotations

from .registry import (  # noqa: F401
    KINDS,
    Action,
    actions_for,
    call,
    describe,
    get,
    modules,
    names,
    register,
)
from . import catalog  # noqa: F401,E402  (import for side effect: registration)

__all__ = ["KINDS", "Action", "actions_for", "call", "describe", "get",
           "modules", "names", "register"]
