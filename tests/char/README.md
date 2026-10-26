# Characterisation tests (the safety net)

This suite freezes the **current** shape of the Storm-Breaker backend so the
skeleton re-architecture (`docs/ADVANCED-UPDATE-PLAN.md` rev 2, Option C)
cannot quietly remove a route or change a response contract.

## What gets frozen

| Test file | Surface | Source of truth |
|-----------|---------|-----------------|
| `test_route_inventory.py` | Flask `url_map` (every `rule + methods` tuple) | generated; first run writes the baseline |
| `test_victim.py` | NR-1 victim surface (no session) | `tests/contract/victim.json` |
| `test_operator_get.py` | Authenticated operator GET shape | `audit.OPERATOR_GETS` (AST-imported) |
| `test_operator_post.py` | Authenticated operator POST shape | `audit.OPERATOR_POSTS` (AST-imported) |

Snapshots live in `tests/_frozen/<group>/<safe-key>.json` and describe
only the *shape*:

- HTTP status code
- `Content-Type` header
- JSON top-level: object keys (sorted), array length + element type, or scalar type
- HTML: `<title>` and body size
- Binary: `Content-Type` family + body size

Full bodies are intentionally **not** captured; cosmetic changes (new IDs,
fresh timestamps, dynamic rows) must not falsify the freeze. Genuine drifts
(missing key, wrong content-type, deleted route) always fail.

## Running

```bash
# 1. baseline (writes missing snapshots; if everything is new, you get
#    "first run baseline" skips — re-run to validate):
pytest

# 2. validate against committed snapshots:
pytest   # exit 0 == G1 green

# 3. re-baseline after an intentional schema change:
pytest --update-snapshots
git add tests/_frozen
git commit -m 'p1.x: refresh char snapshots after <reason> [gate=G1]'
```

## Adding a new endpoint

Three steps (tests-first discipline):

1. **Add the path** to either `tests/contract/victim.json`, the `OPERATOR_GETS`
   list in `audit/audit_storm_breaker.py`, or `OPERATOR_POSTS` there.
2. **Run with `--update-snapshots`** so the corresponding `tests/_frozen/`
   JSON is written.
3. **Re-run without the flag** to confirm parity; commit both the catalogue
   change and the new snapshot.

Do not edit a snapshot by hand; either re-capture it or accept the drift and
open an ADR.

## Layout

```
tests/
├── pytest.ini                      # addopts, markers, warnings filter
├── conftest.py                     # live_server + admin_session + storm_app
├── contract/
│   └── victim.json                 # NR-1 frozen victim surface
├── char/                           # this suite
│   ├── __init__.py
│   ├── _helpers.py                 # shape_snapshot(), compare_or_update()
│   ├── _catalog.py                 # AST-imports OPERATOR_* from audit
│   ├── test_route_inventory.py
│   ├── test_victim.py
│   ├── test_operator_get.py
│   ├── test_operator_post.py
│   └── README.md
├── _frozen/                        # committed JSON snapshots (one per route)
│   ├── route_inventory/url_map.json
│   ├── victim/<METHOD>_<PATH>.json
│   ├── operator_get/GET_<PATH>.json
│   └── operator_post/POST_<PATH>.json
└── _server.log                     # pytest-managed server log
```

## Why snapshot compare instead of value compare

The backend produces live data: campaign IDs, alerts, geofence names.
Freezing exact values would make the suite red every time the operator
clicks a button in the panel. Freezing the shape still catches the
regressions that matter for the contract (NR-1/NR-2) without false alarms.
