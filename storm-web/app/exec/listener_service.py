"""Managed listener service (FIREPOWER plan section P15.3).

Before: to catch a reverse shell you ran ``nc -lvnp`` in another window.  Now the
operator starts/stops named listeners, and every connection is recorded as
evidence on a target (``listener:host:port``).

P1.2: ``interactive=True`` listeners no longer discard the accepted socket.
Each catch becomes a live session -- the operator can ``send`` a command into
the reverse shell and ``read`` the lines that come back, all over the API.
"""
from __future__ import annotations

import socket
import threading
import time
from typing import Any, Dict, List, Optional

from app.core import events
from app.exec.listener import Listener
from app.targets import TargetStore

class ListenerService:
    """Named, start/stop-able TCP listeners with connect evidence + live shells."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._listeners: Dict[str, Listener] = {}
        self._sessions: Dict[str, dict] = {}
        self._sess_lock = threading.Lock()

    def start(self, name: str, host: str = "127.0.0.1", port: int = 0,
              hold: bool = False, interactive: bool = False) -> Dict[str, Any]:
        with self._lock:
            if name in self._listeners and self._listeners[name] is not None:
                return self._info(name, self._listeners[name])
            lis = Listener(host, int(port), hold=hold, interactive=interactive,
                           on_connect=lambda addr, conn, h=host, p=port:
                               self._on_connect(addr, conn, h, p, name))
            self._listeners[name] = lis
            return self._info(name, lis)

    def stop(self, name: str) -> bool:
        with self._lock:
            lis = self._listeners.pop(name, None)
            mine = [k for k, s in self._sessions.items()
                    if s["listener"] == name] if lis else []
        if lis is None:
            return False
        lis.stop()
        for key in mine:
            self.close(key)
        return True

    def list(self) -> List[Dict[str, Any]]:
        with self._lock:
            items = list(self._listeners.items())
        return [self._info(name, lis) for name, lis in items]

    def get(self, name: str) -> Optional[Listener]:
        with self._lock:
            return self._listeners.get(name)

    # ------------------------------------------------------------- sessions

    def sessions(self) -> List[Dict[str, Any]]:
        with self._sess_lock:
            rows = list(self._sessions.values())
        out = []
        for s in rows:
            with s["lock"]:
                pending = len(s["lines"])
            out.append({"key": s["key"], "listener": s["listener"],
                        "peer": s["peer"], "connected_at": s["connected_at"],
                        "alive": s["alive"], "pending_lines": pending})
        return out

    def send(self, key: str, command: str) -> bool:
        """Write one command (newline-terminated) into a live session."""
        with self._sess_lock:
            s = self._sessions.get(key)
        if s is None or not s["alive"]:
            return False
        try:
            s["sock"].sendall((command.rstrip("\n") + "\n").encode("utf-8"))
        except OSError:
            s["alive"] = False
            return False
        events.publish("listener-send", key=key, listener=s["listener"],
                       command=command[:200])
        return True

    def read(self, key: str, clear: bool = True) -> List[str]:
        """Drain the lines the peer has produced since the last read."""
        with self._sess_lock:
            s = self._sessions.get(key)
        if s is None:
            return []
        with s["lock"]:
            lines = list(s["lines"])
            if clear:
                s["lines"].clear()
        return lines

    def close(self, key: str) -> bool:
        with self._sess_lock:
            s = self._sessions.pop(key, None)
        if s is None:
            return False
        s["alive"] = False
        try:
            s["sock"].shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        try:
            s["sock"].close()
        except OSError:
            pass
        return True

    def _spawn_session(self, conn: socket.socket, addr, name: str) -> str:
        key = "%s|%s:%s" % (name, addr[0], addr[1])
        sess = {"key": key, "listener": name,
                "peer": {"ip": str(addr[0]), "port": int(addr[1])},
                "sock": conn, "lines": [], "alive": True,
                "connected_at": time.time(), "lock": threading.Lock()}
        with self._sess_lock:
            self._sessions[key] = sess
        t = threading.Thread(target=self._session_loop, args=(sess,), daemon=True)
        t.start()
        events.publish("listener-session", key=key, listener=name,
                       peer=addr[0], peer_port=addr[1])
        return key

    def _session_loop(self, s: dict) -> None:
        buf = b""
        try:
            s["sock"].settimeout(0.5)
        except OSError:
            pass
        while s["alive"]:
            try:
                data = s["sock"].recv(4096)
            except socket.timeout:
                continue
            except OSError:
                break
            if not data:
                break
            buf += data
            while b"\n" in buf:
                line, buf = buf.split(b"\n", 1)
                with s["lock"]:
                    s["lines"].append(line.decode("utf-8", "replace"))
        if buf:  # peer died mid-line; keep the partial
            with s["lock"]:
                s["lines"].append(buf.decode("utf-8", "replace"))
        s["alive"] = False
        try:
            s["sock"].close()
        except OSError:
            pass

    # ------------------------------------------------------------- evidence

    def _on_connect(self, addr, conn, host: str, port: int, name: str) -> None:
        target = TargetStore().get_or_create("%s:%d" % (host, port),
                                             name="listener:%s:%d" % (host, port))
        TargetStore().add_finding(target["id"], "listener-connect",
                                  "connection from %s:%s" % (addr[0], addr[1]),
                                  evidence={"peer": addr[0], "port": addr[1],
                                            "listener": name})
        events.publish("listener", host=host, port=port, peer=addr[0], peer_port=addr[1])
        if conn is not None:
            self._spawn_session(conn, addr, name)

    @staticmethod
    def _info(name: str, lis: Listener) -> Dict[str, Any]:
        return {"name": name, "host": lis.host, "port": lis.port,
                "interactive": lis.interactive,
                "connections": len(lis.clients), "clients": lis.clients}

SERVICE = ListenerService()

def get_service() -> ListenerService:
    return SERVICE
