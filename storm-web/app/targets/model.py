"""Target store -- aim at something, keep the evidence (P14.3).

A weapon remembers what it aimed at.  ``TargetStore`` persists targets and
their findings in the additive ``targets`` / ``target_findings`` tables
(created by ``app.core.migrations.targets``).  It talks to SQLite directly
so the frozen ``database.py`` is never edited (NR-3).
"""
from __future__ import annotations

import json
import sqlite3
import sys
from contextlib import closing
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

_HERE = Path(__file__).resolve().parent
_STORM_WEB = str(_HERE.parents[2])
if _STORM_WEB not in sys.path:
    sys.path.insert(0, _STORM_WEB)

import database as _database  # noqa: E402


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


class TargetStore:
    """Persistence for targets and the findings attached to them."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_path = db_path or _database.DB_PATH

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # -- targets -----------------------------------------------------------
    def create(self, name: str, host: str = "", notes: str = "") -> Dict[str, Any]:
        now = _now()
        with closing(self._connect()) as conn:
            cur = conn.execute(
                "INSERT INTO targets(name, host, notes, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?)", (name, host, notes, now, now))
            conn.commit()
            target_id = cur.lastrowid
        return self.get(target_id)

    def get_or_create(self, host: str, name: Optional[str] = None) -> Dict[str, Any]:
        with closing(self._connect()) as conn:
            row = conn.execute("SELECT id FROM targets WHERE host = ? ORDER BY id LIMIT 1",
                               (host,)).fetchone()
        if row:
            return self.get(row["id"])
        return self.create(name or host, host=host, notes="auto")

    def get(self, target_id: int) -> Optional[Dict[str, Any]]:
        with closing(self._connect()) as conn:
            row = conn.execute("SELECT * FROM targets WHERE id = ?", (target_id,)).fetchone()
        if row is None:
            return None
        target = dict(row)
        target["findings"] = self.findings(target_id)
        return target

    def list(self) -> List[Dict[str, Any]]:
        with closing(self._connect()) as conn:
            rows = conn.execute("SELECT * FROM targets ORDER BY id DESC").fetchall()
        return [dict(r) for r in rows]

    # -- findings ----------------------------------------------------------
    def add_finding(self, target_id: int, kind: str, detail: str = "",
                    evidence: Any = None) -> Dict[str, Any]:
        ev = json.dumps(evidence, default=str) if evidence is not None else None
        now = _now()
        with closing(self._connect()) as conn:
            cur = conn.execute(
                "INSERT INTO target_findings(target_id, kind, detail, evidence, created_at) "
                "VALUES (?, ?, ?, ?, ?)", (target_id, kind, detail, ev, now))
            conn.execute("UPDATE targets SET updated_at = ? WHERE id = ?", (now, target_id))
            conn.commit()
            finding_id = cur.lastrowid
        return self._finding(finding_id)

    def findings(self, target_id: int) -> List[Dict[str, Any]]:
        with closing(self._connect()) as conn:
            rows = conn.execute(
                "SELECT * FROM target_findings WHERE target_id = ? ORDER BY id",
                (target_id,)).fetchall()
        return [_decode_finding(r) for r in rows]

    def _finding(self, finding_id: int) -> Dict[str, Any]:
        with closing(self._connect()) as conn:
            row = conn.execute("SELECT * FROM target_findings WHERE id = ?",
                               (finding_id,)).fetchone()
        return _decode_finding(row)


def _decode_finding(row) -> Dict[str, Any]:
    d = dict(row)
    d["evidence"] = json.loads(d["evidence"]) if d.get("evidence") else None
    return d
