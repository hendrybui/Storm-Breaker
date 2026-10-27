"""In-process event bus for the realtime push channel (P10 / Track 7).

The panel used to poll fixed intervals and never saw anything happen live.
Producers (beacon arrivals, listener connections, verified strikes) publish
here; ``GET /api/events`` streams them to the browser via SSE.  The old HTTP
poll endpoints stay untouched as the fallback.

stdlib only; bounded queues so a slow subscriber cannot grow memory.
"""
from __future__ import annotations

import queue
import threading
import time
from collections import deque
from datetime import datetime
from typing import Any, Deque, Dict, List, Optional, Tuple

MAX_QUEUE = 200


class EventBus:
    def __init__(self, keep: int = 200) -> None:
        self._lock = threading.Lock()
        self._subs: Dict[int, "queue.Queue[dict]"] = {}
        self._next_id = 1
        self._recent: Deque[dict] = deque(maxlen=keep)

    # -- publish ------------------------------------------------------------
    def publish(self, kind: str, **data: Any) -> dict:
        event = {"kind": kind, "at": datetime.now().isoformat(), "ts": time.time()}
        event.update(data)
        with self._lock:
            self._recent.append(event)
            subs = list(self._subs.values())
        for q in subs:
            try:
                q.put_nowait(event)
            except queue.Full:  # drop on a stalled subscriber
                pass
        return event

    # -- subscribe ----------------------------------------------------------
    def subscribe(self) -> Tuple[int, "queue.Queue[dict]"]:
        q: "queue.Queue[dict]" = queue.Queue(maxsize=MAX_QUEUE)
        with self._lock:
            sid = self._next_id
            self._next_id += 1
            self._subs[sid] = q
        return sid, q

    def unsubscribe(self, sid: int) -> None:
        with self._lock:
            self._subs.pop(sid, None)

    def subscribers(self) -> int:
        with self._lock:
            return len(self._subs)

    def recent(self, limit: int = 50, kinds: Optional[List[str]] = None) -> List[dict]:
        with self._lock:
            items = list(self._recent)
        if kinds:
            items = [e for e in items if e.get("kind") in kinds]
        return items[-limit:]

    def clear(self) -> None:
        with self._lock:
            self._recent.clear()


BUS = EventBus()


def publish(kind: str, **data: Any) -> dict:
    return BUS.publish(kind, **data)
