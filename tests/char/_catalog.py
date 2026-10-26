"""Endpoint catalogues for the characterization suite.

OPERATOR_GETS and OPERATOR_POSTS are extracted programmatically out of
``audit/audit_storm_breaker.py`` so this suite and the audit harness can
never disagree about which routes are covered. VICTIM_PUBLIC_PATHS is
parsed out of ``tests/contract/victim.json`` (NR-1 source of truth).
"""
from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple


REPO = Path(__file__).resolve().parents[2]
AUDIT_PATH = REPO / "audit" / "audit_storm_breaker.py"
VICTIM_PATH = REPO / "tests" / "contract" / "victim.json"


def _extract_audit_lists() -> Tuple[List[str], List[Tuple[str, Dict[str, Any]]]]:
    """AST-parse the audit script and pull OPERATOR_GETS + OPERATOR_POSTS."""
    src = AUDIT_PATH.read_text(encoding="utf-8")
    tree = ast.parse(src)
    by_name: Dict[str, Any] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
            continue
        if node.targets[0].id in ("OPERATOR_GETS", "OPERATOR_POSTS"):
            by_name[node.targets[0].id] = ast.literal_eval(node.value)

    gets = list(by_name.get("OPERATOR_GETS", []))
    posts = [(p, pl) for (p, pl) in by_name.get("OPERATOR_POSTS", [])]
    return gets, posts


OPERATOR_GETS, OPERATOR_POSTS = _extract_audit_lists()


def _load_victim_contract() -> Dict[str, Any]:
    return json.loads(VICTIM_PATH.read_text(encoding="utf-8"))


VICTIM_CONTRACT = _load_victim_contract()


def victim_pairs() -> List[Tuple[str, str]]:
    """[(path, method)] from tests/contract/victim.json."""
    return [(ep["path"], m) for ep in VICTIM_CONTRACT["endpoints"] for m in ep["methods"]]


def victim_paths() -> Set[str]:
    return {p for p, _ in victim_pairs()}
