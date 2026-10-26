# TODO — Storm-Breaker Upgrade (Handoff task list)

Owner: receiving agent. Read `docs/HANDOFF.md` first, then `docs/ADVANCED-UPDATE-PLAN.md`.
Rule: do tasks in order; do not start a phase until the prior gate is GREEN; tests before code;
append a `docs/PROGRESS.md` row per task.

Legend: `[ ]` todo · `[x]` done · `[~]` in progress · `[!]` blocked · ID format `P<phase>.<n>`
Gate IDs: G0..G9 (see plan §6). Every task lists files + gate + rollback.

## Quickstart — do these 10 first
- [ ] P0.1 git tag `pre-upgrade`
- [ ] P0.2 run `python3 audit/audit_storm_breaker.py` → save `docs/evidence/G0-audit.txt`
- [ ] P0.3 backup `storm-web/storm_breaker.db` → `backups/`
- [ ] P1.1 scaffold `tests/` + `pytest.ini`
- [ ] P1.2 server-launch fixture (localhost:2525)
- [ ] P1.3 characterization: freeze operator GET routes
- [ ] P1.4 characterization: freeze victim POST routes
- [ ] P1.5 characterization: assert response SCHEMA (keys), not values
- [ ] P1.6 run suite green → **G1**
- [ ] P2.1 create `storm-web/app/` package skeleton

---

## TRACK 0 — Safety net

### P0 Recon & Freeze
- [ ] P0.1 tag `pre-upgrade` — gate: tag exists
- [ ] P0.2 baseline audit → `docs/evidence/G0-audit.txt` — gate: exit 0
- [ ] P0.3 DB backup → `backups/storm_breaker.db.<ts>` — rollback: restore copy
- [x] P0.4 `tests/contract/victim.json` — rollback: delete
- [x] P0.5 `docs/adr/0001-tauri-wrap.md`
- [x] P0.6 `docs/TAB-MAP.md`

### P1 Characterization tests (the safety net — MUST precede refactor)
- [ ] P1.1 scaffold `tests/` + `pytest.ini` + `conftest.py` — files: `tests/`
- [ ] P1.2 fixture boots server / uses test client at `:2525`
- [ ] P1.3 freeze operator GET responses (auth'd) — files: `tests/char/test_ops_get.py`
- [ ] P1.4 freeze victim POST responses (no session) — files: `tests/char/test_victim.py`
- [ ] P1.5 schema-only assertions (keys/types) to survive cosmetic change
- [ ] P1.6 run suite + audit green → **G1** — evidence to PROGRESS
- [ ] P1.7 document how to add a char test — files: `tests/char/README.md`

---

## TRACK 1 — Skeleton rebuild

### P2 App factory
- [ ] P2.1 create `storm-web/app/` package — files: `app/__init__.py`
- [ ] P2.2 `app/config.py` env config (PORT, DB_PATH, SECRET) — rollback: revert
- [ ] P2.3 `app/extensions.py` (csrf/limiter/db handles placeholders)
- [ ] P2.4 `create_app()` wiring secret + `before_request` auth gate (verbatim)
- [ ] P2.5 point entrypoint at `create_app`; reduce `app.py` to a shim
- [ ] P2.6 char suite green (no routes moved yet) — evidence

### P3 Blueprint extraction (move routes VERBATIM, one domain at a time)
Each task: move only, no logic change; run char suite after each.
- [ ] P3.1 blueprint `auth` (/login,/logout)
- [ ] P3.2 blueprint `capture` (/receiver, /api/fingerprint, /api/keystrokes, /api/session/*)
- [ ] P3.3 blueprint `c2` (/api/c2/*)
- [ ] P3.4 blueprint `mobile` (/api/mobile/*)
- [ ] P3.5 blueprint `intel` (/api/fingerprints, /api/keystrokes, /api/webrtc_*, /api/profiles/*)
- [ ] P3.6 blueprint `credentials` (/api/credentials/*)
- [ ] P3.7 blueprint `tools_payloads` (/api/payloads/*)
- [ ] P3.8 blueprint `tools_obfuscation` (/api/obfuscate*)
- [ ] P3.9 blueprint `tools_lures` (/api/lures/*)
- [ ] P3.10 blueprint `tools_reports` (/api/reports*)
- [ ] P3.11 blueprint `campaigns` (/api/campaigns/*, /c/<code>)
- [ ] P3.12 blueprint `evasion` (/api/evasion/*)
- [ ] P3.13 blueprint `threat_intel` (/api/threat-intel/*)
- [ ] P3.14 blueprint `session_hijack` (/api/session-hijack/*)
- [ ] P3.15 blueprint `pivot` (/api/pivot/*)
- [ ] P3.16 blueprint `rat` (/api/rat/*)
- [ ] P3.17 blueprint `ai_threat` (/api/ai-threat/*)
- [ ] P3.18 blueprint `zeroday` (/api/zeroday/*)
- [ ] P3.19 blueprint `quantum` (/api/quantum/*)
- [ ] P3.20 blueprint `deeprecon` (/api/deeprecon/*)
- [ ] P3.21 blueprint `analytics` (/api/analytics/*, /api/system/*)
- [ ] P3.22 blueprint `admin` (alerts, settings, telegram, operator-log, nuke, export)
- [ ] P3.23 blueprint `static` (template/asset serving /t/, /assets/)
- [ ] P3.24 char suite + audit green → **G2 route parity**

### P4 Service extraction
- [x] P4.1 `services/capture.py` (ingest image/audio/keystroke/fingerprint/geo)
- [x] P4.2 `services/c2.py`
- [x] P4.3 `services/mobile.py`
- [x] P4.4 `services/intel.py` (profiles, credentials, webrtc)
- [x] P4.5 `services/artifacts.py` (reports, lures, payloads)
- [x] P4.6 `services/osint.py` (threat-intel, deeprecon, pivot, session-hijack)
- [x] P4.7 char suite green

### P5 Core (state / db / migrations)
- [x] P5.1 `core/state.py` StateStore interface
- [x] P5.2 MemoryStore impl (behavior-identical default)
- [x] P5.3 route C2/mobile queues through StateStore (deque + lock)
- [x] P5.4 `core/db.py` repository over `database.py`
- [x] P5.5 `core/migrations/` + baseline migration — rollback: restore backup
- [x] P5.6 enable WAL + indexes + pool — rollback: PRAGMA revert
- [x] P5.7 char suite green

### P6 Job queue
- [x] P6.1 `core/jobs.py` queue abstraction
- [x] P6.2 worker thread with graceful start/stop
- [x] P6.3 move notifications (webhook/telegram) off request path
- [x] P6.4 move credential scan / report gen off request path
- [x] P6.5 additive job-status API
- [x] P6.6 char suite + audit green → **G3 core parity**

### P3 completion debt (recorded 2026-10-27, see PROGRESS FINDING 1)
- [x] P3.23 drain residual `app.py` routes: ~134 dead duplicate registrations + ~25 routes served only from app.py → blueprints, verbatim (char inventory protects; rollback: git checkout g3-ok)

---

## TRACK 2 — Hardening

- [x] P7.1 hashed operator password (+verify shim for `config.php`) — rollback: revert
- [x] P7.2 CSRF on mutating operator routes only (victims exempt)
- [x] P7.3 persist login lockout (survives restart)
- [x] P7.4 upload caps + per-type limits
- [x] P7.5 retention/rotation job for capture dirs
- [x] P7.6 auth/caps tests + audit green → **G4**

---

## TRACK 3 — Delivery

### P8 Offline frontend
- [x] P8.1 generate design tokens (`assets/css/tokens.css`)
- [x] P8.2 vendor CDN assets (chart.js, leaflet, tailwind, fontawesome, fonts) → `/assets/vendor/`
- [x] P8.3 cache-busting on static refs
- [x] P8.4 panel renders with network disabled → **G5** — rollback: restore CDN links

### P9 Tauri shell
- [ ] P9.1 scaffold `src-tauri/` (Tauri v2) — rollback: delete dir
- [ ] P9.2 PyInstaller sidecar of the backend
- [ ] P9.3 app boots/stops sidecar; window → `localhost:2525`
- [ ] P9.4 system tray + start/stop
- [ ] P9.5 capabilities/CSP lockdown — rollback: relax CSP
- [ ] P9.6 installers build for host OS; audit green → **G6**

### P10 Realtime + native
- [ ] P10.1 operator push channel (IPC/WS); keep HTTP poll as fallback
- [ ] P10.2 native notifications on capture
- [ ] P10.3 deep links `storm://`
- [ ] P10.4 safe-exec wrapper (checkpoint/rollback/retry) for terminal + playbooks — flag off
- [ ] P10.5 latency test < 300 ms + idle-call delta measured → **G7**

### P11 Panel migration (behind `UI_V2`)
- [ ] P11.1 scaffold `ui/` (React/Vite/shadcn)
- [ ] P11.2–P11.30 migrate each of the 30 tabs (one per subtask; parity + screenshot diff + audit each)
- [ ] P11.31 flip default to V2 at 100% parity → **G8** — rollback: flag off
- [ ] P11.32 archive legacy `panel.html`

### P12 Packaging
- [ ] P12.1 code signing config
- [ ] P12.2 GitHub Actions publish workflow (per-OS)
- [ ] P12.3 single-file HTML report artifacts
- [ ] P12.4 signed artifacts on tag → **G9**

---

## TRACK 4 — Closeout
- [ ] P13.1 runbook + upgrade guide
- [ ] P13.2 final audit + full sweep
- [ ] P13.3 hand off backlog below

## Backlog (NOT gated)
- [ ] Real crypto via `cryptography` (replace hand-rolled AES/XOR)
- [ ] Optional LLM hook for ai_threat (feature-flagged, offline fallback)
- [ ] Tauri mobile target
- [ ] Plugin/skill registry for modules + templates
- [ ] Multi-node scale-out (shared Redis + object store)
