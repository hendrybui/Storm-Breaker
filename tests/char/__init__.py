"""
Characterization tests for the Storm-Breaker backend.

This package is the safety net for every future skeleton refactor (HANDOFF
section P1, NR-1 + NR-2). Tests are organized as:

  test_route_inventory.py -- Flask URL map hasn't dropped a route (NR-2).
  test_victim.py          -- NR-1 frozen victim surface; no-session replay.
  test_operator_get.py    -- Authenticated operator GET shape.
  test_operator_post.py   -- Authenticated operator POST shape.

Schema-only snapshots live in tests/_frozen/ as JSON files (one per route).
Run `pytest --update-snapshots` from the repo root to refresh them after an
intentional change (e.g. adding a column to a response). Add new endpoints
the same way: write a parametrized case, then run with --update-snapshots.
"""
