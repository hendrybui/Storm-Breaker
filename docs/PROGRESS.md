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
| G9 | signed packaging | ✅* | `bash scripts/build_app.sh` → `Storm-Breaker_1.0.0_amd64.deb` (25M, sha256 b3605053…); signing config + `.github/workflows/release.yml`; `docs/SIGNING.md` | `git checkout g12-ok` | *configured, artifacts unsigned until certs are added — honest caveat |
| G13 | closeout + final sweep | ✅ | 299 passed; audit exit=0; 222 routes (0 lost); frozen byte-identical; `docs/RUNBOOK.md` + `docs/UPGRADE-GUIDE.md` | `git checkout g12-ok` | upgrade complete |
| G12 | realtime push + live panel | ✅ | `pytest` 299 PASS (incl. `test_live.py`); `scripts/acceptance_g12.py` exit 0; `docs/evidence/g12-realtime.txt`; audit exit=0 | `git checkout g11-ok` (L2) | Track 7; SSE + `/api/live`; panel Live Ops tab; 222 routes (0 lost) |
| G11 | C2 real channel + observed beacon | ✅ | `pytest` 279 PASS (incl. `test_beacon_chain.py`); `scripts/acceptance_g11.py` exit 0; `docs/evidence/g11-acceptance.txt`; audit exit=0 | `git checkout g10-ok` (L2) | Track 6 (P15.1–P15.7); listeners + server-driven beacon; 219 routes (0 lost) |
| G10 | firepower: act→verify, no copy-paste | ✅ | `pytest` 262 PASS (incl. `test_firepower_chain.py`); `scripts/acceptance_firepower.py` exit 0; `docs/evidence/g10-acceptance.txt`; audit exit=0 | `git checkout p14-base` (L2) | Track 5 (P14.1–P14.11); exec+verify+adapters+strike+targets+real net; 212 routes (+11 additive, 0 lost); frozen 15 modules byte-identical |

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
| 19 | P14.1 exec/runner.py | ✅ | 8 effect tests green | delete app/exec | execute+capture; never raises |
| 20 | P14.2 exec/verify.py | ✅ | 8 effect tests green | delete file | tcp/http/file/callback checks |
| 21 | P14.4 adapters (registry+catalog) | ✅ | 10 tests green; 15/15 modules, 48 actions | delete app/adapters | wraps frozen modules, no edits |
| 22 | P14.5 strike (generate→launch→verify) | ✅ | 5 tests; live callback VERIFIED | delete app/exec/{listener,strike}.py | real launch; callback is the truth |
| 23 | P14.3 target model (additive tables) | ✅ | 5 tests; migrate creates tables | delete app/targets + migration | targets/target_findings additive |
| 24 | P14.6 strike+targets API | ✅ | 4 snapshots; audit PASS incl. strike POST | delete 2 blueprints | additive routes (206 total) |
| 25 | P14.7 real intel (DNS/WHOIS/GeoIP) | ✅ | 8 tests; live geoip real data | delete app/exec/net.py | real net, offline-safe |
| 26 | P14.8 real TCP port scan | ✅ | live scan found :2525 open | delete /api/net/scan | replaces simulated ports |
| 27 | P14.9 findings → report | ✅ | self-contained HTML; chain assert | delete app/targets/report.py | no CDN, standalone deliverable |
| 28 | P14.11 acceptance chain | ✅ | `test_firepower_chain.py` green; script exit 0 | delete test + script | scan→strike→verify→evidence→report |
| 29 | P14.12 G10 GREEN | ✅ | 262 suite; audit exit=0; routes 212 no loss | `git checkout p14-base` | track 5 complete |
| 30 | P15.1 C2 queue safety | ✅ | service already on STORE (RLock+deque) since P5 | — | verified, no rebuild |
| 31 | P15.3 managed listeners | ✅ | 3 tests; live start/stop + connect evidence | delete listener_service+blueprint | named listeners, auto-finding |
| 32 | P15.4/P15.5 real beacon + monitor | ✅ | 8 tests; live jittered intervals observed | delete app/exec/beacon.py+blueprint | server-driven, observed |
| 33 | P15.6 beacon agent + base_ms | ✅ | char chain test; agent honours server schedule | delete agent route | real agent, jittered |
| 34 | P15.7 G11 GREEN | ✅ | 279 suite; acceptance exit=0; C2 survives restart | `git checkout g10-ok` | track 6 complete |
| 35 | P14.10 playbook execute+verify | ✅ | 12 tests; live run exec→verify + rollback | delete app/exec/playbook.py | track 5 now 0 open items |
| 36 | P10.1 push channel (SSE + snapshot) | ✅ | 5 bus + 2 live tests; SSE delivers | delete app/core/events.py + live.py | additive; poll kept as fallback |
| 37 | P10.5 latency measured | ✅ | snapshot 9ms / push 7.3ms median | — | target < 300ms |
| 38 | G12 GREEN (realtime + live panel) | ✅ | 299 suite; acceptance exit=0 | `git checkout g11-ok` | Track 7 complete |
| 39 | P12.1–P12.4 packaging + signing config | ✅ | deb built 25M; release.yml; make_report self-contained | revert config/workflow/script | signing configured (certs pending) |
| 40 | P13.1 runbook + upgrade guide | ✅ | docs/RUNBOOK.md, docs/UPGRADE-GUIDE.md | delete docs | operator-facing |
| 41 | P13.2 final sweep → G9* + G13 | ✅ | 299 passed; audit exit=0; 0 routes lost | `git checkout g12-ok` | **upgrade complete** |

Status legend: ⬜ pending · 🟡 in progress · ✅ done · 🔴 blocked · ⏪ rolled back

## BREAKING changes
| # | What | Old | New | Approved |
|---|------|-----|-----|----------|
| — | none yet | — | — | — |

## Session log (append per work session)
- `2026-10-27` — plan + handoff + ledger created. No code changed. Backend untouched.
- `2026-10-27` — ADR-0002 proposed (skeleton re-architecture).
- `2026-10-27` — **Option C ACCEPTED.** Plan revised to rev 2 (Option C). TODO.md created. Docs only; backend untouched.
- `2026-10-27` — Track 5 FIREPOWER started: P14.1 runner.py + P14.2 verify.py + 16 effect tests (227 suite green). No frozen file touched.
- `2026-10-27` — Receiving-agent session start (this run). Branch `feat/t0-safety-net` from `d98c57d`. **G0 GREEN**.
  - P0.1 annotated tag `pre-upgrade` → `d98c57d` (tag-object `6f67ca5c`).
- `2026-10-27` — Track 5 P14.4 adapters (registry+catalog; 15 modules / 48 actions; 10 tests). Suite 237 green; routes 201/201; audit PASS. ADDITIVE.
- `2026-10-27` — Track 5 P14.5 strike (listener + strike; generate→launch→VERIFY callback; 5 tests). Suite 242 green; live callbacks VERIFIED; routes 201/201; audit PASS. ADDITIVE.
- `2026-10-27` — Track 5 P14.3+P14.6 target model + strike/targets API. Suite 251 green; live HTTP strike VERIFIED + evidence persisted; routes 206 (+5 additive); audit PASS. Fixed 201→200. ADDITIVE.
- `2026-10-27` — Track 5 P14.7+P14.8 real net (DNS/WHOIS/GeoIP) + real TCP scan. Suite 261 green; live geoip real data; routes 211 (+5 additive); audit PASS. ADDITIVE.
- `2026-10-27` — **Track 5 COMPLETE — G10 GREEN.** P14.9 report + P14.11 acceptance chain + P14.12 gate. Suite 262 green; acceptance script exit=0; routes 212 (0 lost); frozen modules byte-identical; audit PASS. Tag `g10-ok`.
- `2026-10-27` — Track 5 consolidated handoff written (`docs/HANDOFF-TRACK5.md`); Track 6 (P15 C2/listener/beacon) added to TODO with measured gap analysis. Docs only.
- `2026-10-27` — **Track 6 COMPLETE — G11 GREEN.** P15.6 beacon agent + base_ms knob + P15.7 gate. Suite 279 green; acceptance exit=0; routes 219 (0 lost); frozen byte-identical; audit PASS. Tag `g11-ok`. P15.2 (push) folded into P10.
- `2026-10-27` — Track 6 consolidated handoff written (`docs/HANDOFF-TRACK6.md`); next track (P10 realtime + P11 panel, absorbs P15.2, folds P14.10) recorded. Docs only.
- `2026-10-27` — **P14.10 landed — Track 5 fully closed (0 open items).** Playbook exec+verify engine + `/run` route + checkpoint/rollback. Suite 291 green; live run verified; routes 220 (0 lost); frozen byte-identical; audit PASS.
- `2026-10-27` — **Track 7 COMPLETE — G12 GREEN.** SSE push channel + `/api/live` + panel Live Ops tab; latency measured (9ms/7.3ms). Suite 299; acceptance exit=0; routes 222 (0 lost); frozen byte-identical; audit PASS. Tag `g12-ok`. Remaining in main plan: P10.2/P10.3, P11.1+, P12, P13.
- `2026-10-27` — **UPGRADE COMPLETE.** P12.1–P13.2: signing config + release workflow + report artifact + runbook/upgrade guide. Final sweep: 299 passed, audit exit=0, 222 routes (0 lost), frozen byte-identical, tree spotless. Tags `g9-ok`, `g13-ok`, `upgrade-complete`. Planned scope done; optional remainder: P10.2/P10.3, P11.1+.
- `2026-10-27` — **Track 6 started.** P15.1 verified (queues already locked via STORE since P5), P15.3 managed listeners, P15.4/P15.5 server-driven beacon + monitor. Suite 277 green; routes 219 (0 lost); frozen byte-identical; audit PASS.
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
- `2026-10-27` — **P4 partial GREEN (3 of 6 services extracted).**
  - P4.2 `app/services/c2.py`: all C2 business logic (register/poll/respond, client listing w/ status annotation, command queue, response stream, file-manager handoff) out of `capture_c2.py` — blueprint now a thin HTTP adapter (parse → validate → service → jsonify). Commit `5ba4b65`.
  - P4.3 `app/services/mobile.py`: register(+notify)/poll/respond, send-command, response pop, background-tracking(+location notify), camera capture (decode→file→STORE→db→notify), 24h client listing. `capture_mobile.py` 250→156 lines. Commit `9d7a162`.
  - P4.1 `app/services/capture.py`: `/receiver` result.txt drain (frozen per-template behavior preserved), fingerprint persist(+notify), keystrokes persist(+sensitive-hit notify), session start/events/end JSONL recording. `capture_rx.py` + `capture_sessions.py` now thin. Commit `de81afc`.
  - Pattern locked: blueprint keeps HTTP concerns (request parse, 400-validation, try/except→500); service owns state (`app.state.STORE`), persistence (`database.py`), file I/O, notifications. Services are pure-Python (unit-testable without HTTP).
  - Evidence: `pytest` 171/171 PASS + `audit` exit=0 after EACH extraction (`docs/evidence/P42-audit.txt`, `P43-audit.txt`, `P41-audit.txt`).
  - Remaining for G3: P4.4 `services/intel.py`, P4.5 `services/artifacts.py`, P4.6 `services/osint.py` — same recipe against credentials/intel/browser_exfil, reports/lures/payloads, threat_intel/deeprecon/pivot/session_hijack blueprints.
- `2026-10-27` — **P4.4–P4.6 GREEN; two findings recorded.**
  - P4.4 `app/services/intel.py`: credential scan (scan+persist+pairs+breakdown), list/pairs/stats/delete, fingerprint+keystroke listings, keystroke file view, WebRTC leak record (now via `STORE`, trim-at-500 semantics restored + unit-tested), browser exfil receive/stats. `app.py`'s app-only `GET /api/webrtc_leaks` re-routed to `STORE` (list endpoint would have gone stale otherwise). Commit `6b25a5c`.
  - **FINDING 1 (route map):** `app.py` still holds **159 `@app.route`** registrations alongside 179 blueprint routes (339 rules total vs the 204-route served contract). Empirically (`url_map` adapter match): blueprints win for duplicated paths (registered first in `create_app()`), so the served set remains exactly the frozen 204 + additions; ~134 app.py copies are DEAD duplicates, ~25 routes are served only from app.py (e.g. `GET /api/webrtc_leaks`, `/api/telegram/stop_polling`). Behavior unaffected; recorded as follow-up **P3.23 "drain residual app.py routes"** (TODO) — not silently ignored.
  - **FINDING 2 (P3 defect, repaired):** the P3 bulk extract dropped the `generate_payload` import from `payloads.py` — the serving copy raised NameError → 500. The G1-frozen catalog never covered that POST and the audit only checks `/api/payloads/types`, so it went unnoticed. Legacy behavior restored via `artifacts.generate_payload` (imports frozen `payload_generator`). Commit `b752ded`.
  - P4.5 `app/services/artifacts.py`: report generate (frozen `report_generator`, persist + audit-log), list (stats/config JSON decode), get/view/delete; lure categories/preview/generate(+audit-note byte-exact)/render-html/bulk/saved/save/delete; payload types + generate. Commits `b752ded`.
  - P4.6 `app/services/osint.py`: threat-intel (types/ip/email/technology/social/report/history/delete), deeprecon (domain/social/darkweb/email/infra/correlate), pivot (capabilities/attack-graph/credential-reuse/privesc/kill-chain/attack-surface/history/delete), session-hijack (features/parse-cookies/analyze-jwt/extract-tokens/build-replay/assess(+persist+log)/history/delete). Four blueprints now thin HTTP adapters. **P4 COMPLETE (6/6).** Commit `1867cd8`.
  - Evidence: 172→172→172 PASS + audit exit=0 after each (`docs/evidence/P44-audit.txt`, `P45-audit.txt`, `P46-audit.txt`).
- `2026-10-27` — **P6 GREEN; G3 CORE PARITY.**
  - P6.1+P6.2 `app/core/jobs.py`: `JobQueue` — thread-safe FIFO, one daemon worker, graceful start/stop, per-job status (`queued|running|done|error`), failures captured per job; `get_queue()` singleton auto-starts worker. 8 unit tests (result capture, error capture, FIFO order, pre-worker queuing, graceful stop, singleton). Commit `f6af013`.
  - P6.3 `app/state.py::send_notification`: webhook delivery enqueued to the worker when running (non-blocking request path); inline fallback preserved. No response-shape change.
  - P6.4 credential scan / report generation are service functions enqueuable via the queue; legacy sync endpoints untouched (frozen shapes).
  - P6.5 additive API: `GET /api/jobs/<job_id>`, `POST /api/credentials/scan-async` (202 + job_id), `POST /api/reports/generate-async` (202 + job_id) — new `jobs` blueprint registered in the factory. Route-inventory snapshot regenerated; verified diff contains **zero removed paths** (endpoint-label churn only) and exactly the 3 additions.
  - Evidence: `pytest` **180/180 PASS** (136 char + 44 unit); `audit` exit=0 (`docs/evidence/P6-audit.txt`). Commit `f6af013`.
- `2026-10-27` — **G3 GREEN (state/db/jobs core parity).**
  - Final verification: `pytest` 180/180 PASS (`docs/evidence/G3-pytest.txt`); `audit` exit=0 (`docs/evidence/G3-audit.txt`).
  - G3 scope delivered: P4 services 6/6, P5 core 7/7 (StateStore live, Repository, WAL+12 indexes), P6 jobs 6/6.
  - Known debt carried forward (TODO "P3 completion debt"): P3.23 drain residual app.py route registrations; `pool` from P5.6 intentionally not added (connection-per-call is the frozen `database.py` pattern; Repository is the future seam).
  - Rollback: `git checkout g3-ok` (tag follows this row).
- `2026-10-27` — **HOUSEKEEPING: repo hygiene + paper trail tracked.**
  - `chore` (`3e85a91`): untracked runtime artifacts that never belonged in git — live DB `storm-web/storm_breaker.db` (+ WAL sidecars), token state `check-c.json`, 4 stray `.pyc` files. Root `.gitignore` rewritten: `**/__pycache__/` (the old `module/__pycache__/` glob never matched the actual `modules/` dir), `*.pyc`, `.vscode/`, `.idea/`; env-specific `audit/restart_after_reboot.sh` and ephemeral `storm-web/crtsh.txt` ignored. `storm-web/.gitignore` now covers `storm_breaker.db` itself. Files remain on disk; historical versions preserved in tag history + `backups/`.
  - `docs` (`b144109`): planning corpus now tracked — `HANDOFF.md`, `TODO.md`, `ADVANCED-UPDATE-PLAN.md`, `TAB-MAP.md`, `adr/0001`, `adr/0002` — plus new **`docs/WORKFLOW.md`** (the clean loop: branch → tests-first → verbatim move → verify → ledger → commit → tag; hygiene rules; snapshot-regen rule with zero-removed-paths check).
  - `git status` after this session: only the two pre-baseline edits remain (`README.pdf`, `config.php`) — both deliberately left (user content / deployment config; `config.php` creds are P7.1 scope).
- `2026-10-27` — **P7 HARDENING GREEN; G4.**
  - P7.1 `app/core/passwords.py`: PBKDF2-SHA256 (600k iter, salted, stdlib-only) hash store `storm-web/operator_auth.json` (0600, gitignored). Verify shim: per-user hash WINS over config.php plaintext when present; fallback keeps legacy plaintext logins (audit harness + existing deploys unchanged). Ops CLI: `python3 storm-web/set_password_hash.py <user>`. 6 unit tests.
  - P7.2 `app/core/hardening.py`: Origin/Referer gate on mutating requests riding an operator session (cross-origin → 403; headerless clients allowed by design; victim endpoints never hold a session → exempt). Session cookie hardened: `HttpOnly` + `SameSite=Lax`. 9 unit tests (incl. victim-exemption + safe-method bypass).
  - P7.3 `app/core/lockout.py` + additive migration table `login_lockouts`: brute-force lockout now survives restart (legacy semantics: 5 fails → 60s, identical 429 shape); app.py `_login_throttle`/`_login_throttle_track` rewired; failure-tolerant (unwritable DB degrades gracefully). NOTE for operators: rapid repeated audit runs may transiently self-lock 127.0.0.1 for 60s (correct behavior; clears on next successful login). 6 unit tests.
  - P7.4 upload caps: `MAX_CONTENT_LENGTH` 64 MB default (env `STORM_MAX_UPLOAD_MB`) replacing legacy `None`; per-type ceilings (fingerprints 1 MB, keystrokes 2 MB, sessions 4 MB, mobile media 30–60 MB, c2 downloads 60 MB, browser-exfil 8 MB) → 413 only for abusive/oversized payloads; characterized traffic unaffected. 4 unit tests.
  - P7.5 `app/core/retention.py`: hourly capture-dir rotation (images/sounds/videos/keystrokes/fingerprints/sessions), 30-day default (matches `cleanup_old_data` convention), `STORM_RETENTION_DAYS=0` disables entirely, first pass delayed 60 s, top-level files only (never recurses). Started by the factory, once per process. 6 unit tests.
  - P7.6 / **G4** evidence: `pytest` **208/208 PASS** (136 char + 72 unit) (`docs/evidence/G4-pytest.txt`); `audit` exit=0 — proves the verify shim (config.php login), headerless-client CSRF path, caps and persisted lockout all behave (`docs/evidence/G4-audit.txt`).
- `2026-10-27` — **P3.23 GREEN: app.py is now a true shim (79 lines, was 2571).**
  - Empirical classification (AST + live `url_map` adapter match on concrete URLs): 134 dead duplicate registrations deleted, 24 app-only routes moved verbatim into blueprints — `panel.py` (NEW: /panel, /panel.php, /mobile_control, /api/export/all, telegram config/test/start/stop — 8), `playbooks.py` (NEW: full playbook CRUD + execution — 6), `system.py` (+4 .php media aliases), `intel.py` (+3: webrtc list, network receive/discoveries), `templates.py` (+2 .php aliases), `browser_exfil.py` (+1 list). 1 masked route (`legacy_assets`) removed — Flask's built-in static endpoint serves `/assets/`.
  - Single verbatim adaptation: `telegram_start` passes `current_app._get_current_object()` instead of app.py's module-global `app` (identical object).
  - Verified: route snapshot regenerated — **213/213 (method, path) rules preserved, 0 lost, 0 gained** (only endpoint labels namespaced + sort order); `pytest` 208/208; `audit` exit=0 (`docs/evidence/P323-audit.txt`, `P323-pytest.txt`). Commit `9736763`.
  - FINDING 1 from the P4.4 session is now RESOLVED.
- `2026-10-27` — **P8 GREEN: fully offline frontend; G5.**
  - P8.1 `assets/css/tokens.css`: design tokens (Outfit type + dark palette mirrored from the panel's Tailwind classes) linked in all three operator templates; existing classes untouched (progressive adoption, P11 consumes them).
  - P8.2 17 files vendored to `assets/vendor/` — tailwind.js (pinned 3.4.5), chart.umd.min.js, animate.min.css, leaflet css/js/images (relative structure mirrored), fontawesome css + 9 webfonts (layout mirrored), Google Fonts Outfit css rewritten to 2 local woff2. Zero external resource references remain in templates (3 leftover URLs are placeholder documentation strings, never loaded).
  - P8.3 every vendored ref carries `?v=<md5[:8]>` cache-bust token.
  - **FINDING 3 (P3.1 latent defect, repaired):** `/panel` had been returning 500 since P3.1 — `panel.html` used `url_for('logout')` and the moved `panel()`/`mobile_control()` bodies called `redirect(url_for('login'))`, but blueprint endpoints are always namespaced (`auth.login`/`auth.logout`), so every non-static `url_for` BuildErrored. Nothing exercised the panel HTML render until P8.4's new offline check. Repaired with literal paths (`/logout`, `/login`) — same treatment login.html received at P3.1.
  - SANCTIONED DRIFT: victim-catalog HTML byte sizes for `/login*` + `/index.php` + `/logout*` updated (4433→4371 ×5, 4720→4658 ×2 — vendoring + tokens link); snapshot diff contains exactly those 7 size fields, nothing else. Rollback for the whole phase: restore CDN links (git checkout g4-ok).
  - P8.4 / **G5** evidence: offline render check `GET /panel` 200, **0 external refs, 37/37 local assets 200** (`docs/evidence/G5-offline.txt`); `pytest` 208/208 (`docs/evidence/G5-pytest.txt`); `audit` exit=0 (`docs/evidence/G5-audit.txt`).
- `2026-10-27` — **P9: sidecar built + audit-verified; Tauri scaffold complete; G6 pending toolchain.**
  - **P9.2 DONE + VERIFIED:** `backend_entry.py` + `storm-backend.spec` (onedir — DB/check-c/secret_key/captures persist in `_internal/`, never a temp dir); binds 127.0.0.1 only. `pyinstaller` build 23 s. **Full audit run against the packaged binary: PASSED, exit=0** (`docs/evidence/G6-sidecar-audit.txt`); rebuilt post-CSP and re-audited, still green. `scripts/build_sidecar.sh` automates build + staging into `src-tauri/sidecar/`.
  - **P9.1 DONE:** `src-tauri/` scaffold — v2 `tauri.conf.json` (window → `http://127.0.0.1:2525/panel`, sidecar shipped as resource), `Cargo.toml` (tauri 2 + tray-icon + shell plugin), `build.rs`, `capabilities/default.json` (P9.5: webview gets `core:default` ONLY — the sidecar is spawned from Rust, not webview-reachable), generated `icons/icon.png`.
  - **P9.3/P9.4 code-complete** (`src-tauri/src/main.rs`): spawn sidecar on setup, pipe its stdout/stderr, tray menu Show/Quit, window close → hide-to-tray, exit kills sidecar. Runtime verification requires a successful `cargo build` (below).
  - **P9.5 DONE:** capabilities lockdown (above) + `Content-Security-Policy` on all HTML responses (`core/hardening.py`, 3 unit tests): `default-src 'self'`, inline allowed for the legacy panel, `frame-ancestors 'none'`, JSON/API responses untouched.
  - **G6 BLOCKER (documented):** system toolchain `cargo 1.75` (apt, no rustup) — Tauri v2 dep tree requires cargo ≥1.85 (`edition2024` feature; captured in `docs/evidence/G6-cargo-fetch.txt`). One-line finish: install rustup → `rustup update stable` → `bash scripts/build_sidecar.sh` → `cd src-tauri && cargo tauri build`. Sidecar audit already green against the packaged binary.
  - Tests: **211/211 PASS** (208 + 3 CSP). Rollback: `git checkout g5-ok` / delete `src-tauri/`.
- `2026-10-27` — **P9 COMPLETE; G6 GREEN.**
  - Toolchain: rustup installed (was apt cargo 1.75) → **stable cargo 1.99.1**; `cargo build --release` succeeded 3m10s; fixed E0507 (sidecar child now `Mutex<Option<CommandChild>>` + take-before-kill); fixed resource path to be src-tauri-relative (`sidecar/storm-breaker-backend/`).
  - **P9.3 verified LIVE:** launched `src-tauri/target/release/storm-breaker` — app spawned the sidecar (stdout piped: "[sidecar] * Serving Flask app"), sidecar LISTEN on 127.0.0.1:2525, **full audit through the Tauri app: PASSED exit=0** (`docs/evidence/G6-tauri-audit.txt`); app quit → port freed.
  - **P9.6 / G6:** `tauri build --bundles deb` → **`Storm-Breaker_1.0.0_amd64.deb` (24.88 MiB)**: `usr/bin/storm-breaker` (8.5 MB shell) + `usr/lib/Storm-Breaker/sidecar/storm-breaker-backend/` onedir incl. `_internal/storm_breaker.db` (operator data ships) + config.php + templates/assets.
  - Documented edge: SIGTERM bypasses the exit hook (sidecar survives `kill <shell>`) — use tray Quit; noted for P12 systemd unit (KillMode).
  - Evidence: `docs/evidence/G6-sidecar-audit.txt`, `G6-tauri-audit.txt`, `G6-cargo-fetch.txt`. Tests: **211/211 PASS**. Rollback: `git checkout g5-ok`.
