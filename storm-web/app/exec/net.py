"""Real network primitives (FIREPOWER plan sections P14.7 + P14.8).

``deep_recon`` / ``threat_intel`` *simulate* results from ``md5(domain)`` seeds.
These helpers do the real thing -- DNS resolve, reverse DNS, TCP connect scan,
WHOIS over port 43, GeoIP over HTTP -- so an operator gets observable truth.
stdlib only; every call returns a value and never raises.
"""
from __future__ import annotations

import json
import socket
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional, Sequence

# A short, high-signal default set; callers can pass their own.
DEFAULT_PORTS = [21, 22, 23, 25, 53, 80, 110, 143, 443, 445, 587, 993, 995,
                 2525, 3000, 3306, 3389, 5432, 5900, 6379, 8000, 8080, 8443,
                 9000, 27017]


def resolve(host: str) -> List[str]:
    """Forward DNS: all A/AAAA addresses for ``host`` (empty on failure)."""
    try:
        infos = socket.getaddrinfo(host, None)
    except OSError:
        return []
    return sorted({info[4][0] for info in infos})


def reverse_dns(ip: str) -> Optional[str]:
    """Reverse DNS for ``ip`` (None on failure)."""
    try:
        return socket.gethostbyaddr(ip)[0]
    except OSError:
        return None


def _probe(host: str, port: int, timeout: float) -> Optional[int]:
    sock = socket.socket()
    sock.settimeout(timeout)
    try:
        return port if sock.connect_ex((host, int(port))) == 0 else None
    finally:
        sock.close()


def port_scan(host: str, ports: Optional[Sequence[int]] = None,
              timeout: float = 0.5, workers: int = 64) -> Dict[str, object]:
    """Real TCP connect scan. Returns the ports that actually accepted."""
    targets = list(ports) if ports else list(DEFAULT_PORTS)
    started = time.time()
    if not targets:
        return {"host": host, "scanned": 0, "open": [], "duration": 0.0}
    with ThreadPoolExecutor(max_workers=max(1, min(workers, len(targets)))) as pool:
        found = [p for p in pool.map(lambda p: _probe(host, p, timeout), targets)
                 if p is not None]
    return {"host": host, "scanned": len(targets), "open": sorted(found),
            "duration": round(time.time() - started, 3)}


def grab_banner(host: str, port: int, timeout: float = 2.0) -> str:
    """Best-effort banner read (empty string if the port sends nothing)."""
    try:
        with socket.create_connection((host, int(port)), timeout=timeout) as sock:
            sock.settimeout(timeout)
            try:
                return sock.recv(256).decode("utf-8", "replace").strip()
            except OSError:
                return ""
    except OSError:
        return ""


def whois(domain: str, server: str = "whois.verisign-grs.com",
          timeout: float = 6.0, max_bytes: int = 20000) -> Dict[str, object]:
    """Minimal WHOIS over TCP/43 (raw text; no dependency)."""
    try:
        with socket.create_connection((server, 43), timeout=timeout) as sock:
            sock.sendall((domain + "\r\n").encode())
            chunks: List[bytes] = []
            total = 0
            while total < max_bytes:
                data = sock.recv(4096)
                if not data:
                    break
                chunks.append(data)
                total += len(data)
        return {"domain": domain, "server": server,
                "raw": b"".join(chunks).decode("utf-8", "replace")}
    except OSError as exc:
        return {"domain": domain, "server": server, "raw": "", "error": str(exc)}


def geoip(ip: str, timeout: float = 5.0) -> Dict[str, object]:
    """GeoIP via a public JSON endpoint; ``{"error": ...}`` when offline."""
    try:
        with urllib.request.urlopen("http://ip-api.com/json/%s" % ip, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8", "replace"))
    except Exception as exc:  # noqa: BLE001 -- a lookup must never raise
        return {"ip": ip, "error": str(exc)}
