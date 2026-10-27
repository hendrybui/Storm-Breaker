"""Managed listener service (FIREPOWER plan section P15.3).

Before: to catch a reverse shell you ran ``nc -lvnp`` in another window.  Now the
operator starts/stops named listeners, and every connection is recorded as
evidence on a target (``listener:host:port``).
"""
from __future__ import annotations

import threading
from typing import Any, Dict, List, Optional

from app.exec.listener import Listener
from app.targets import TargetStore


class ListenerService:
    """Named, start/stop-able TCP listeners with connect evidence."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._listeners: Dict[str, Listener] = {}

    def start(self, name: str, host: str = "127.0.0.1", port: int = 0,
              hold: bool = False) -> Dict[str, Any]:
        with self._lock:
            if name in self._listeners and self._listeners[name] is not None:
                return self._info(name, self._listeners[name])
            lis = Listener(host, int(port), hold=hold,
                           on_connect=lambda addr, h=host, p=port: self._on_connect(addr, h, p))
            self._listeners[name] = lis
            return self._info(name, lis)

    def stop(self, name: str) -> bool:
        with self._lock:
            lis = self._listeners.pop(name, None)
        if lis is None:
            return False
        lis.stop()
        return True

    def list(self) -> List[Dict[str, Any]]:
        with self._lock:
            items = list(self._listeners.items())
        return [self._info(name, lis) for name, lis in items]

    def get(self, name: str) -> Optional[Listener]:
        with self._lock:
            return self._listeners.get(name)

    @staticmethod
    def _info(name: str, lis: Listener) -> Dict[str, Any]:
        return {"name": name, "host": lis.host, "port": lis.port,
                "connections": len(lis.clients), "clients": lis.clients}

    @staticmethod
    def _on_connect(addr, host: str, port: int) -> None:
        target = TargetStore().get_or_create("%s:%d" % (host, port),
                                             name="listener:%s:%d" % (host, port))
        TargetStore().add_finding(target["id"], "listener-connect",
                                  "connection from %s:%s" % (addr[0], addr[1]),
                                  evidence={"peer": addr[0], "port": addr[1]})


SERVICE = ListenerService()


def get_service() -> ListenerService:
    return SERVICE
