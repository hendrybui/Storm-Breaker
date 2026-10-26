"""Action registry for module adapters (FIREPOWER plan section P14.4).

The 15 feature modules are frozen (NR-3): their signatures must not change.
Adapters *wrap* them so every capability is reachable through one uniform,
enumerable surface -- an :class:`Action`.  This is the hook the firepower layer
(``app.exec.runner`` / ``verify``, P14.5+) and the job queue (P6) call through,
instead of importing a module by name at each call site.

Nothing here executes by itself; ``kind`` labels intent:

- ``generate`` -- emits an artifact (script, config, report)
- ``analyze``  -- read-only evaluation
- ``execute``  -- runs something
- ``notify``   -- side-effecting message
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List

KINDS = ("generate", "analyze", "execute", "notify")


@dataclass(frozen=True)
class Action:
    """A named, callable capability wrapped from a frozen module."""

    name: str      # e.g. "payloads.generate"
    module: str    # frozen module it wraps, e.g. "payload_generator"
    kind: str      # one of KINDS
    summary: str
    func: Callable

    def call(self, *args, **kwargs):
        """Invoke the wrapped frozen function."""
        return self.func(*args, **kwargs)

    def spec(self) -> dict:
        """JSON-able description (no callables)."""
        return {"name": self.name, "module": self.module,
                "kind": self.kind, "summary": self.summary}


_REGISTRY: Dict[str, Action] = {}


def register(name: str, module: str, kind: str, summary: str, func: Callable) -> Action:
    if kind not in KINDS:
        raise ValueError("bad kind %r (want one of %s)" % (kind, KINDS))
    if not callable(func):
        raise TypeError("%s: func is not callable" % name)
    if name in _REGISTRY:
        raise ValueError("duplicate action %r" % name)
    action = Action(name, module, kind, summary, func)
    _REGISTRY[name] = action
    return action


def get(name: str) -> Action:
    try:
        return _REGISTRY[name]
    except KeyError:
        raise KeyError("no such action %r (registry has %d)" % (name, len(_REGISTRY)))


def call(name: str, *args, **kwargs):
    """Look up and invoke an action by name."""
    return get(name).call(*args, **kwargs)


def names() -> List[str]:
    return sorted(_REGISTRY)


def modules() -> List[str]:
    return sorted({a.module for a in _REGISTRY.values()})


def actions_for(module: str) -> List[Action]:
    return sorted((a for a in _REGISTRY.values() if a.module == module),
                  key=lambda a: a.name)


def describe() -> List[dict]:
    return [a.spec() for a in sorted(_REGISTRY.values(), key=lambda a: a.name)]
