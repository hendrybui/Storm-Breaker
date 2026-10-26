"""P1 route-inventory test (NR-2).

Tooling seam: the Flask URL map must still contain every operator route
from the audit catalogue; NR-2 guarantees ADD-only operator routes
during the skeleton refactor. Victim paths are covered separately by
``test_victim.py`` (NR-1) because some legitimate victim paths are not
registered in ``url_map`` (e.g. ``/favicon.ico`` is answered by Flask's
static-folder fallback, not by an explicit ``@app.route``).

Re-baseline with: ``pytest tests/char/test_route_inventory.py --update-snapshots``.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from ._catalog import OPERATOR_GETS, OPERATOR_POSTS
from ._helpers import FROZEN_ROOT


_FROZEN = FROZEN_ROOT / "route_inventory"


def _rules(storm_app) -> list[dict]:
    out: list[dict] = []
    for rule in storm_app.url_map.iter_rules():
        methods = tuple(
            sorted(m for m in (rule.methods or set())
                   if m not in ("HEAD", "OPTIONS"))
        )
        out.append({"rule": rule.rule, "endpoint": rule.endpoint,
                    "methods": methods})
    return sorted(out, key=lambda r: (r["rule"], r["methods"]))


@pytest.mark.char
def test_route_inventory(storm_app, request: pytest.FixtureRequest) -> None:
    update = request.config.getoption("--update-snapshots")
    actual = _rules(storm_app)
    snapshot_file = _FROZEN / "url_map.json"

    if update or not snapshot_file.exists():
        _FROZEN.mkdir(parents=True, exist_ok=True)
        snapshot_file.write_text(
            json.dumps({"rules": actual}, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        if not update:
            pytest.skip(f"baseline written to {snapshot_file.name}; re-run")
        return

    frozen = json.loads(snapshot_file.read_text(encoding="utf-8"))
    frozen_rules = {(r["rule"], tuple(r["methods"])) for r in frozen["rules"]}
    actual_rules = {(r["rule"], tuple(r["methods"])) for r in actual}

    missing = frozen_rules - actual_rules
    assert not missing, (
        f"NR-2 violation: {len(missing)} route(s) disappeared from url_map: "
        f"{sorted(missing)[:10]}{'...' if len(missing) > 10 else ''}"
    )

    # Every operator route from the audit catalogue must still resolve.
    adapter = storm_app.url_map.bind("localhost")
    for path in OPERATOR_GETS:
        try:
            adapter.match(path, method="GET")
        except Exception:
            pytest.fail(f"operator GET {path} no longer matches url_map (NR-2)")
    for path, _ in OPERATOR_POSTS:
        try:
            adapter.match(path, method="POST")
        except Exception:
            pytest.fail(f"operator POST {path} no longer matches url_map (NR-2)")
