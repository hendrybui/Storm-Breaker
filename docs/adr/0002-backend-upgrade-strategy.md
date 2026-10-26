# ADR 0002 — Backend upgrade strategy: re-architect the skeleton, keep the organs

- Status: **ACCEPTED** (owner chose Option C, 2026-10-27)
- Date: 2026-10-27
- Supersedes: extends `0001-tauri-wrap.md` (wrap is still valid; this decides *what happens to the backend*)
- Deciders: owner

## Decision record
Owner selected **Option C — Strangler re-architecture** (skeleton rebuild in place, keep the feature
modules and victim contract). Option C is now the governing plan; see `docs/ADVANCED-UPDATE-PLAN.md`
(rev 2) and `docs/TODO.md`.

## Context — measured, not assumed
Facts gathered from the current tree:

- `storm-web/app.py` — 3,500 lines, 216 functions, **204 routes, 0 Blueprints, 0 app factory**,
  7 module-level mutable globals, 56 `except` blocks, **0 `async`, 0 threads/locks/queues**.
- `storm-web/database.py` — 1,485 lines, 81 functions, `sqlite3.connect` per call (no pool/migrations).
- 15 feature modules (~9,000 lines) are **dependency-light by design** (stdlib + flask/psutil/requests).
  They are mostly **generators** (emit scripts/commands/configs), not executors.
- Real third-party footprint: `flask`, `psutil`, `requests`. Everything else is stdlib.

Verdict: the backend is a **flat, synchronous, global-state monolith with a clean stdlib feature layer.**
Breadth is high; architecture is thin.

## Decision
Re-architect the **skeleton only**, in place, behind the existing HTTP surface (Strangler-Fig).
Keep the feature modules and the victim contract. Do NOT big-bang rewrite 204 routes.

Rebuild: app factory + blueprints, service layer, state adapter, repository/migrations, config,
error handling, job queue, logging. Wrap — never edit — the 15 modules.

## Options scored honestly
| Option | Score | Why |
|--------|-------|-----|
| A. Harden + Tauri wrap only | 6/10 | reliable + native, but backend stays a 3,500-line flat file; "advanced design" ask unmet |
| B. Clean-room full rewrite | 7/10 | pristine design, but gambles 204 routes + 30 tabs + victim contract, takes months, diverges from upstream |
| C. Strangler re-architecture | 9/10 | professional structure, keeps organs, low risk, staged | 

## Target shape
```
storm-web/
  app/__init__.py        create_app() factory
  app/config.py          env-based config
  app/extensions.py      csrf, limiter, db handles
  app/blueprints/        victims, c2, mobile, intel, payloads, reports, admin, ...
  app/services/          domain logic (was inline in app.py)
  app/core/state.py      StateStore adapter (memory | redis)
  app/core/db.py         repository + migrations
  app/core/jobs.py       background worker (scans, reports, notifications)
  app/adapters/          thin wrappers over the 15 modules (UNCHANGED modules)
```
Old `app.py` routes are moved verbatim, domain by domain; behavior stays identical until each domain is migrated.

## Migration protocol (this is the "precise execution")
1. Characterization tests first: freeze the current response of all 204 routes (freeze truth).
2. Introduce `create_app` + one blueprint at a time (mechanical move, no logic change).
3. Extract services from routes once moved; tests stay green throughout.
4. Replace state + db internals behind adapters.
5. Only then add new capability (async jobs, real crypto, optional LLM hook).

Every step behavior-preserving; the HTTP surface never changes.

## Honest costs / risks
- Upstream divergence from `ultrasecurity/Storm-Breaker` becomes permanent — accept it.
- Any "real" upgrade adds deps (e.g. `cryptography`), changing the stdlib-only selling point.
- Route-by-route migration is tedious; without characterization tests it will regress.

## Firepower truth (honest)
More tabs ≠ more firepower. The real gap: modules **generate** but rarely **execute/verify**.
Highest-value firepower = an async job layer that actually *runs* the generated payloads/scans, plus
real crypto and (optional) a real AI hook. Scope depth, not breadth.
