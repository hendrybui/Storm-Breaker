"""Schema-only response snapshot helpers.

A "shape" snapshot captures:

  - HTTP status code
  - Content-Type header
  - body_kind  : json | html | binary | text | unknown
  - shape      : the JSON top-level structure (object keys / array length /
                 HTML title / binary size / text first-line)

It deliberately does NOT capture whole response bodies. That means cosmetic
changes (timestamps, generated IDs, new analytics snapshots, etc.) won't
falsely fail the freeze. Genuine schema drift (a key disappearing, the
content-type changing, a route dropping a methods set) WILL fail it.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, Tuple

import requests


FROZEN_ROOT = Path(__file__).resolve().parents[1] / "_frozen"
_TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)


def ingest_suffix() -> str:
    """``?k=<secret>`` when storm-web/Settings.json configures an ingest secret.

    P16: victim endpoints can require a shared secret, and these replays send no
    session. Without the suffix every victim characterization test would 401.
    """
    p = Path(__file__).resolve().parents[2] / "storm-web" / "Settings.json"
    try:
        secret = (json.loads(p.read_text(encoding="utf-8")).get("ingest_secret") or "").strip()
    except Exception:
        return ""
    return ("?k=" + secret) if secret else ""


def _safe_json_payload(resp: requests.Response) -> Any:
    try:
        return resp.json()
    except (ValueError, json.JSONDecodeError):
        return None


def shape_snapshot(resp: requests.Response) -> Dict[str, Any]:
    """Return a small, JSON-serialisable description of a response."""
    ct = (resp.headers.get("Content-Type") or "").split(";")[0].strip().lower()
    snap: Dict[str, Any] = {
        "status": resp.status_code,
        "content_type": ct,
        "body_kind": "unknown",
        "shape": None,
    }

    if ct == "application/json":
        data = _safe_json_payload(resp)
        if data is None:
            snap["body_kind"] = "binary_or_unparseable"
            snap["shape"] = {"first_bytes_hex": resp.content[:80].hex()}
            return snap
        snap["body_kind"] = "json"
        if isinstance(data, dict):
            snap["shape"] = {
                "type": "object",
                "key_count": len(data),
                "keys": sorted(data.keys()),
            }
        elif isinstance(data, list):
            element_type = type(data[0]).__name__ if data else "empty"
            snap["shape"] = {
                "type": "array",
                "length": len(data),
                "element_type": element_type,
            }
        elif data is None:
            snap["shape"] = {"type": "null"}
        else:
            snap["shape"] = {"type": type(data).__name__}
        return snap

    if ct.startswith("text/html"):
        snap["body_kind"] = "html"
        m = _TITLE_RE.search(resp.text)
        snap["shape"] = {
            "type": "html",
            "title": (m.group(1).strip() if m else None),
            "size": len(resp.text),
        }
        return snap

    if ct.startswith(("image/", "audio/", "video/", "font/",
                      "application/octet-stream", "application/pdf")):
        snap["body_kind"] = "binary"
        snap["shape"] = {"type": "binary", "size": len(resp.content)}
        return snap

    snap["body_kind"] = "text"
    first_line = resp.text.splitlines()[0][:120] if resp.text else ""
    snap["shape"] = {"type": "text", "size": len(resp.text), "first_line": first_line}
    return snap


def snapshot_path(group: str, key: str) -> Path:
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", key).strip("_") or "root"
    return FROZEN_ROOT / group / f"{safe}.json"


def write_snapshot(group: str, key: str, snap: Dict[str, Any]) -> Path:
    p = snapshot_path(group, key)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(snap, indent=2, sort_keys=True) + "\n",
                 encoding="utf-8")
    return p


def load_snapshot(group: str, key: str) -> Dict[str, Any]:
    return json.loads(snapshot_path(group, key).read_text(encoding="utf-8"))


def compare_or_update(group: str, key: str, snap: Dict[str, Any],
                      update: bool) -> Tuple[bool, str]:
    """Snapshot the response. Returns (matched, status_message).

    If update is True  -> overwrite the frozen file (always returns True).
    If no snapshot yet -> write one and skip comparison (returns True with
                          an explainer message; first run baseline).
    Otherwise          -> strict equality vs the frozen snapshot.
    """
    p = snapshot_path(group, key)
    if update:
        write_snapshot(group, key, snap)
        return True, f"snapshot updated: {p.relative_to(FROZEN_ROOT.parent)}"
    if not p.exists():
        write_snapshot(group, key, snap)
        return True, (f"snapshot {p.name} written (first run baseline); "
                      f"re-run without --update-snapshots to validate")
    expected = load_snapshot(group, key)
    if expected == snap:
        return True, "matches frozen shape"
    diff_keys = []
    for k in sorted(set(expected) | set(snap)):
        if expected.get(k) != snap.get(k):
            diff_keys.append(k)
    return False, f"drift in fields {diff_keys}: expected={expected} actual={snap}"
