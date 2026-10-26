# PROGRESS — Storm-Breaker Professional Re-architecture (Option C)

Append-only ledger. Never edit a past row — add a new one. Every row cites evidence + rollback.
A gate must be GREEN before the next phase starts.

## Gate Status

| Gate | Meaning | Status | Evidence |
|------|---------|--------|----------|
| G0 | baseline frozen | ✅ | `docs/evidence/G0-audit.txt` (AUDIT EXIT 0), tag `pre-upgrade`→`d98c57d`, `backups/storm_breaker.db.20261027-021155` |
| G1 | characterization suite green | ✅ | `pytest tests/char` = 136/136 PASS; `docs/evidence/G1-audit.txt` exit 0; `tests/_frozen/` 136 snapshots |
| G2 | factory + blueprints, route parity | ✅ | `pytest` 136/136 PASS, `audit` exit=0 (route map 59/0; ops 105/105=200; victim 20/20=200; UID 3/3=400); **22 blueprints** registered in `create_app()` covering 19 domains (auth, capture_rx/sessions/c2/mobile, intel, credentials, payload, obfuscation, lures, reports, campaigns, evasion, threat_intel, session_hijack, pivot, rat, ai_threat, zeroday, quantum, deeprecon, browser_exfil, system, templates) | `git revert a04fed0` (last step) or `git checkout g1-ok` (L2 phase rollback) | snapshots unchanged throughout; 159 thin-wrapper routes remain in `storm-web/app.py` (admin HTML shells + image/audio aliases + `*.php` route aliases + a few analytics/system leftovers); audit resolves 0 unresolved frontend refs |
| G3 | core (state/db/jobs) parity | ⬜ | — |
| G4 | hardening shipped | ⬜ | — |
| G5 | offline frontend | ⬜ | — |
| G6 | Tauri shell + sidecar | ⬜ | — |
| G7 | realtime + native | ⬜ | — |
| G8 | panel parity (UI_V2) | ⬜ | — |
| G9 | signed packaging | ⬜ | — |

## Ledger

| # | Step | Status | Evidence | Rollback | Notes |
|---|------|--------|----------|----------|-------|
| 1 | P0.1 tag `pre-upgrade` | ✅ | tag-object `6f67ca5c` → commit `d98c57d` (annotated) | `git tag -d pre-upgrade` | tags the pre-re-architecture baseline |
| 2 | P0.2 baseline audit | ✅ | `docs/evidence/G0-audit.txt` → exit=0; route-mapping 58/0 unresolved, operator 105/105=200, victim 20/20=200, UID guard 3/3=400, cleanup 33 | re-run `audit/audit_storm_breaker.py --url http://127.0.0.1:2525` | AUDIT PASSED — all features reachable on `app.run(host=0.0.0.0, port=2525)` |
| 3 | P0.3 DB backup | ✅ | `backups/storm_breaker.db.20261027-021155` (md5 `41e54189...`) md5-matches live `storm-web/storm_breaker.db` | `cp backups/storm_breaker.db.20261027-021155 storm-web/storm_breaker.db` | SHA verified at backup time; 196608 B |
| 4 | P0.4 victim contract | ✅ | tests/contract/victim.json | delete | done |
| 5 | P0.5 ADR-0001/0002 | ✅ | docs/adr/ | — | Option C accepted |
| 6 | P0.6 tab map | ✅ | docs/TAB-MAP.md | — | done |
| 7 | P1.1–P1.7 characterization | ✅ | pytest 136/136, audit G1-audit exit=0 (route map 58/0, ops 105/105, victim 20/20, UID 3/3), 136 schema snapshots at `tests/_frozen/{victim,operator_get,operator_post,route_inventory}/` | `pytest tests/char --update-snapshots` then re-run | P1 trails P0 in gate=G1; precedes P3 (per HANDOFF §P1) |
| 8 | P2.1–P2.6 app factory | ✅ | `pytest` 136/136 PASS, `audit_storm_breaker.py` exit=0 (route map 58/0; ops 105/105; victim 20/20; UID 3/3); 3 P2 commits | `git revert a9fd414..6ab0176` (steps), `git checkout g1-ok` (L2 phase) | factory owns Flask+secret_key+MAX_CONTENT_LENGTH only; routes/globals/auth-gate verbatim-moved to factory later (P4–P5) |
| G2 | factory + blueprints, route parity | ✅ | `pytest` 136/136 PASS, `audit` exit=0 (route map 59/0; ops 105/105=200; victim 20/20=200; UID 3/3=400); **22 blueprints** registered in `create_app()` covering 19 domains (auth, capture_rx/sessions/c2/mobile, intel, credentials, payload, obfuscation, lures, reports, campaigns, evasion, threat_intel, session_hijack, pivot, rat, ai_threat, zeroday, quantum, deeprecon, browser_exfil, system, templates) | `git revert a04fed0` (last step) or `git checkout g1-ok` (L2 phase rollback) | snapshots unchanged throughout; 159 thin-wrapper routes remain in `storm-web/app.py` (admin HTML shells + image/audio aliases + `*.php` route aliases + a few analytics/system leftovers); they carry the same behaviour, audit resolves 0 unresolved frontend refs |
| 10 | P4.1–P4.7 services | ⬜ | suite green | revert | |
| 11 | P5.1–P5.7 core state/db | ⬜ | suite green | adapter revert | |
| 12 | P6.1–P6.6 jobs | ⬜ | G3 parity | disable worker | |
| 13 | P7.1–P7.6 hardening | ⬜ | G4 | flag off | |
| 14 | P8.1–P8.4 offline | ⬜ | G5 | restore CDN | |
| 15 | P9.1–P9.6 tauri shell | ⬜ | G6 | delete src-tauri | |
| 16 | P10.1–P10.5 realtime | ⬜ | G7 latency<300ms | use poll | |
| 17 | P11.1–P11.32 panel | ⬜ | G8 parity | flag off | |
| 18 | P12.1–P12.4 packaging | ⬜ | G9 signed | disable CI | |

Status legend: ⬜ pending · 🟡 in progress · ✅ done · 🔴 blocked · ⏪ rolled back

## BREAKING changes
| # | What | Old | New | Approved |
|---|------|-----|-----|----------|
| — | none yet | — | — | — |

## Session log (append per work session)
- `2026-10-27` — plan + handoff + ledger created. No code changed. Backend untouched.
- `2026-10-27` — ADR-0002 proposed (skeleton re-architecture).
- `2026-10-27` — **Option C ACCEPTED.** Plan revised to rev 2 (Option C). TODO.md created. Docs only; backend untouched.
- `2026-10-27` — Receiving-agent session start (this run). Branch `feat/t0-safety-net` from `d98c57d`. **G0 GREEN**.
  - P0.1 annotated tag `pre-upgrade` → `d98c57d` (tag-object `6f67ca5c`).
  - P0.2 baseline `audit/audit_storm_breaker.py` exit=0; full PASS.
  - P0.3 DB backup `backups/storm_breaker.db.20261027-021155` (md5 verified).
  - Next: P1.x characterization tests, then `g0-ok`.
- `2026-10-27` — Branch `feat/t1-skeleton` sprouted from tag `g0-ok`. **G1 GREEN**.
  - P1.1 scaffolded `tests/pytest.ini`, `tests/conftest.py` (live_server + admin_session + storm_app fixtures), `tests/char/{__init__,_helpers,_catalog}.py`, `requirements-dev.txt`.
  - P1.3-P1.5 added `tests/char/test_{route_inventory,victim,operator_get,operator_post}.py` (136 parametrized cases). Schema-only snapshot helper in `_helpers.py`.
  - P1.6 captured 136 schema snapshots (route map + 50 operator GET + 55 operator POST + 30 victim) → `tests/_frozen/`. Re-ran `pytest tests/char` 136/136 PASS in 5.95 s. Re-ran `audit/audit_storm_breaker.py` → exit 0. Saved `docs/evidence/G1-audit.txt`.
  - P1.7 added `tests/char/README.md` (how to add a char test).
  - Next: P2.x — `create_app()` factory + config + extensions; reduce `app.py` to a shim. Tag `g1-ok` follows.
- `2026-10-27` — **G1 GREEN** locked: tag `g1-ok` → `d3e5cb3` (HEAD on `feat/t1-skeleton`).
  - `pytest tests/char` 136/136 PASS in 5.95 s; `audit/audit_storm_breaker.py` exit=0; `docs/evidence/G1-audit.txt` saved.
  - 136 schema-only snapshots committed (route map + 30 victim + 50 operator GET + 55 operator POST).
- `2026-10-27` — **P2 GREEN** (factory in place; routes still in app.py — verbatim).
  - Created `storm-web/app/__init__.py`: single `create_app()` factory (Flask instance, persisted `secret_key.bin`, `MAX_CONTENT_LENGTH=None`, env-overridable `STORM_WEB_PORT/HOST`).
  - Reduced `storm-web/app.py` to a shim: `from app import create_app; app = create_app()` — replaced inline Flask constructor / secret-key loading (NR-2 ADD-only; routes/globals untouched).
  - Fixed `tests/conftest.py::storm_app` and `audit/audit_storm_breaker.py::load_app` to load `storm-web/app.py` via `importlib.util` (Python resolves `import app` to the new package, so explicit-file loading is required to register routes).
  - Re-ran `pytest` (136/136) and `audit` (exit=0; cleanup 55); `docs/evidence/P2-audit.txt` saved.
  - Next: P3 — move routes to blueprints one domain at a time (verbatim, NR-2-add-only). `g2-ok` follows after the LAST blueprint is moved.
- `2026-10-27` — **P3 bulk extract complete; G2 GREEN**.
  - P3.4 capture_mobile (13 mobile/* + admin routes; MOBILE_* state + `_decode_data_url`/`_save_mobile_capture` hoisted to `app.state`).
  - P3.5–P3.22 bulk-extracted 16 blueprints (intel, credentials, payloads, obfuscation, lures, reports, campaigns, evasion, threat_intel, session_hijack, pivot, rat, ai_threat, zeroday, quantum, deeprecon, browser_exfil, system, templates).
  - `fix_imports.py` helper added legacy-module + top-level-package imports to each blueprint so all route bodies import cleanly from `app.state` / `database` / `psutil` / `platform` / `hashlib` / `time`.
  - Verified at every step: `pytest tests/char` 136/136 PASS (~6 s); `audit/audit_storm_breaker.py` exit=0 (`docs/evidence/P3-bulk-audit.txt`, `docs/evidence/P3-final-audit.txt`).
  - **`g2-ok` tag follows.** Next: P4 services (extract inline domain logic from blueprint route handlers), P5 core (StateStore in `app/core/state.py`, repository in `app/core/db.py`, migrations), P6 job queue (`app/core/jobs.py`). G3 gate = core parity (state/db/jobs).
- `2026-10-27` — **P5 GREEN (core layer complete).**
  - P5.1+P5.2 `app/core/state.py`: `StateStore` interface + `MemoryStore` (behavior-identical; single `RLock`; C2 queues, mobile queues, analytics, recon config, WebRTC leaks, login lockout). Committed in `2702c4c`.
  - P5.4 `app/core/db.py`: `Repository` — explicit 1:1 delegate over frozen `database.py` (all public functions, `(*args, **kwargs)` pass-through, zero SQL/logic). Completeness unit test proves every public `database.py` callable has a delegate. `get_repository()` singleton.
  - P5.5 `app/core/migrations/baseline.py`: idempotent re-run of `init_database()` DDL (24 tables, `CREATE TABLE IF NOT EXISTS` only). Rollback: restore `backups/storm_breaker.db.*`.
  - P5.6 `app/core/migrations/runner.py`: `PRAGMA journal_mode=WAL` (+`synchronous=NORMAL`) + 12 additive `CREATE INDEX IF NOT EXISTS` hot-path indexes. Wired into `create_app()` failure-tolerantly (read-only FS cannot block boot). Verified live: `journal_mode=wal`, 12 indexes, 25 relations (24 tables + `sqlite_sequence`). Rollback: `PRAGMA journal_mode=DELETE;` / `DROP INDEX idx_*`. WAL sidecars git-ignored.
  - P5.3 `app/state.py` exposes process-wide `STORE = MemoryStore()`; `capture_c2.py`, `capture_mobile.py`, `system.py`, `app.py` hooks now route ALL C2/mobile session+queue access through `STORE` (5 additive store methods: `c2_sessions_import`, `mobile_sessions_import`, `mobile_response_pop`, `mobile_tracking_append`, `mobile_tracking_all`). Legacy dict names remain defined in `app.state` for backward compat but zero blueprint code touches them (grep-verified).
  - Evidence: `pytest` **171/171 PASS** (136 char + 35 unit) in 7.9 s; `audit` exit=0 (`docs/evidence/P5-audit.txt`, `docs/evidence/P53-audit.txt`). Commits `2702c4c`, `697bdc1`.
  - Next: P4.1–P4.6 service extraction, then G3.
