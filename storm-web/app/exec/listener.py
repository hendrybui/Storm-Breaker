"""A minimal TCP listener for verifying callbacks (FIREPOWER plan section P14.5).

A reverse shell without something to catch it is a toy. :class:`Listener` binds
a port, accepts in a background thread, records peers, and lets a strike *wait
for and verify* the callback without a human watching a terminal.

stdlib only.  Default ``hold=False`` closes each accepted connection
immediately, which makes a blocking ``sh -i`` payload return promptly and keeps
tests deterministic.
"""
from __future__ import annotations

import socket
import threading
import time
from typing import List, Tuple


class Listener:
    """Background TCP listener that records connecting peers."""

    def __init__(self, host: str = "127.0.0.1", port: int = 0, hold: bool = False,
                 interactive: bool = False, on_connect=None):
        self.host = host
        self.hold = hold
        self.interactive = interactive
        self.on_connect = on_connect
        self._srv = socket.socket()
        self._srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._srv.bind((host, port))
        self._srv.listen(5)
        self.port = self._srv.getsockname()[1]
        self._clients: List[Tuple[str, int]] = []
        self._stop = threading.Event()
        self._cv = threading.Condition()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def _loop(self) -> None:
        self._srv.settimeout(0.2)
        while not self._stop.is_set():
            try:
                conn, addr = self._srv.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            with self._cv:
                self._clients.append(addr)
                self._cv.notify_all()
            if self.on_connect is not None:
                try:
                    self.on_connect(addr, conn)
                except Exception:  # noqa: BLE001 -- a callback must not kill the loop
                    pass
            if not self.hold and not self.interactive:
                conn.close()

    @property
    def clients(self) -> List[Tuple[str, int]]:
        return list(self._clients)

    def wait_for_client(self, timeout: float = 5.0) -> bool:
        """Block until a client connects (True) or ``timeout`` elapses (False)."""
        deadline = time.time() + timeout
        with self._cv:
            while not self._clients:
                remaining = deadline - time.time()
                if remaining <= 0:
                    return False
                self._cv.wait(remaining)
        return True

    def stop(self) -> None:
        self._stop.set()
        try:
            self._srv.close()
        except OSError:
            pass
        self._thread.join(timeout=1.0)

    def __enter__(self) -> "Listener":
        return self

    def __exit__(self, *_exc) -> None:
        self.stop()
