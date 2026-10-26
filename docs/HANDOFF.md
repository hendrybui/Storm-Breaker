# HANDOFF — Storm-Breaker Professional Re-architecture (Option C)

Audience: the next agent. Read order: this file → `docs/TODO.md` → `docs/ADVANCED-UPDATE-PLAN.md` →
`docs/PROGRESS.md`. Method: skill-first, proof-of-fix. Announce `Using [skill] to [purpose]` first.

## Mission (one line)
Rebuild Storm-Breaker's **skeleton** (factory + blueprints + services + state/db core + jobs) in place,
then ship it as a signed offline app — **without changing the backend's behavior or the victim contract.**

## Decision of record
ADR-0002 **ACCEPTED: Option C (Strangler)** — re-architect skeleton, keep the 15 modules + 16 templates +
204 routes + 24 tables. The HTTP surface is the seam.

## TL;DR
- **Wrap/refactor, don't rewrite.** No route logic changes during migration.
- Order is fixed: tests (P1) BEFORE any route move (P3).
- If `app.py`'s diff removes a route or changes a response shape → you broke NR-2, fix it.
- First three actions: tag `pre-upgrade` → run audit → read `tests/contract/victim.json`.

## Current State
- Repo `/mnt/Pandora/owncloud/Storm-Breaker`; branch `main` @ `d98c57d`; dirty tree:
  `README.pdf`, `storm-web/check-c.json`, `config.php`, `storm_breaker.db` (M); `.vscode/`,
  `audit/restart_after_reboot.sh`, `storm-web/crtsh.txt` (??).
- App: `storm-web/app.py` (3,500 lines, 204 routes, 0 blueprints/factory). DB: `storm-web/database.py`.
- Audit: `audit/audit_storm_breaker.py --url http://127.0.0.1:2525` (reads creds from `storm-web/config.php`).
- Python 3.12.3. Server: `cd storm-web && python3 app.py` (port 2525).

## Already produced (don't redo)
- ✅ `tests/contract/victim.json` (frozen victim contract)
- ✅ `docs/TAB-MAP.md` (30 tabs ↔ JS ↔ routes)
- ✅ `docs/adr/0001-tauri-wrap.md`, `docs/adr/0002-backend-upgrade-strategy.md`
- ✅ `docs/ADVANCED-UPDATE-PLAN.md` (rev 2), `docs/TODO.md`, `docs/PROGRESS.md`

## DO NOT TOUCH (without an ADR)
1. Victim endpoints/prefixes (§2.1 of plan) — exact.
2. Public signatures of the 15 modules.
3. Existing route paths / response shapes — add-only.
4. `result.txt` per-template behavior; `/t/` served as-is.

## Invariants (why the backend won't break)
- NR-1..NR-8 (plan §1). Victims run in the victim's browser → HTTP to `:2525` ONLY; Tauri IPC is
  operator-side only.
- Behavior-preserving rule: during P3 you MOVE code; you don't improve it. Improvements land in P4+.
- `StateStore` (P5) must exist before any worker count > 1.

## Task Queue
The full ordered list is `docs/TODO.md` (with Quickstart). Gate order:
`G0→G1→G2→G3→G4→G5→G6→G7→G8→G9`. Do not skip gates.

## Definition of Done (per task)
Tests first → code → char suite + audit green → no frozen-interface diff → PROGRESS.md row with evidence
→ rollback command recorded. (Sniper proof-of-fix.)

## Verification Commands
```
python3 audit/audit_storm_breaker.py --url http://127.0.0.1:2525 ; echo "exit=$?"
python3 -m pytest -q
git diff -- storm-web/app.py | grep -E '^\-.*@app.route'   # removed route = investigate
```

## Blockers / Escalation
- Needs a module signature change → wrap in `app/adapters/`, never edit the module.
- Victim contract must change → update `victim.json`, add a PROGRESS "BREAKING" row.
- Sidecar cross-OS fails → host OS only; add failing target to backlog.

## Change Discipline
- Branch per track: `feat/t1-skeleton`, `feat/t3-delivery`, …
- Commit format: `p<phase>.<step>: <action> [gate=Gx]`.
- Tag per green gate: `g0-ok`, `g1-ok`, … Rollback = checkout prior tag (plan §7).
- `docs/PROGRESS.md` is append-only.

## What "precisely executed" looks like
- 204 routes served from blueprints; char suite green the whole way.
- State/db/jobs extracted; victim contract byte-identical; audit green throughout.
- Signed installer boots the backend as a sidecar; panel offline; C2 < 300 ms.
