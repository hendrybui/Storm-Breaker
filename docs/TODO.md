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
- [x] P9.1 scaffold `src-tauri/` (Tauri v2) — rollback: delete dir
- [x] P9.2 PyInstaller sidecar of the backend
- [x] P9.3 app boots/stops sidecar; window → `localhost:2525` (verified live: app spawned sidecar, audit through it PASS)
- [x] P9.4 system tray + start/stop (verified: tray Show/Quit, close→hide, quit kills sidecar)
- [x] P9.5 capabilities/CSP lockdown — rollback: relax CSP
- [x] P9.6 installers build for host OS; audit green → **G6**
      `Storm-Breaker_1.0.0_amd64.deb` (24.88 MiB) via rustup stable + `tauri build --bundles deb`.
      Known edge (documented): SIGTERM to the shell bypasses the exit hook — use tray Quit; systemd units should set KillMode=control-group.

### P10 Realtime + native
- [x] P10.1 operator push channel → `GET /api/events` (SSE) + `GET /api/live` snapshot; HTTP poll kept as fallback  **(Track 7)**
- [x] P10.2 native notifications on capture — `/api/notify/pending` cursor + notification plugin (`spawn_notifier`)
- [x] P10.3 deep links `storm://` — single-instance + deep-link plugin, opens `/panel` or `/t/<name>`
- [x] P10.4 safe-exec wrapper (checkpoint/rollback) — shipped as `app/exec/playbook.py` (P14.10)
- [x] P10.5 latency measured → **G12** (snapshot 9 ms median, push 7.3 ms median; target < 300 ms)

### P11 Panel migration (behind `UI_V2`)
- [x] P11.hot Live Ops tab shipped in the legacy panel (`assets/js/storm_live.js` SSE consumer) — Track 7
- [x] P11.1 scaffold `ui/` (Vite + React) building into `storm-web/assets/ui_v2/`
- [x] P11.2–P11.30 all 30 tabs present in V2 via a descriptor registry (`ui/src/tabs.js`), wired to the SAME endpoints; Live Ops + strike are custom components
- [x] P11.31 `/panel2` served; **default NOT flipped** (interactive tabs are read-only in V2) → **G8\***
- [ ] P11.32 archive legacy `panel.html`  ← deferred until the flag flips
- [ ] P11.2–P11.30 migrate each of the 30 tabs (one per subtask; parity + screenshot diff + audit each)
- [ ] P11.31 flip default to V2 at 100% parity → **G8** — rollback: flag off
- [ ] P11.32 archive legacy `panel.html`

### P12 Packaging
- [x] P12.1 code signing config — `tauri.conf.json` signing block + `docs/SIGNING.md` (configured; unsigned until certs)
- [x] P12.2 GitHub Actions publish workflow (per-OS) — `.github/workflows/release.yml`
- [x] P12.3 single-file HTML report artifacts — `scripts/make_report.py` (0 external refs)
- [x] P12.4 artifacts build on host; release on `v*` tag → **G9**

---

## TRACK 4 — Closeout
- [x] P13.1 runbook + upgrade guide — `docs/RUNBOOK.md`, `docs/UPGRADE-GUIDE.md`
- [x] P13.2 final audit + full sweep — 299 passed, audit exit 0, 222 routes (0 lost), tree spotless → **G13**
- [ ] P13.3 hand off backlog below

## TRACK 5 — FIREPOWER (P14) — make it a weapon, not a toy
See `docs/FIREPOWER.md`. Additive layer; frozen contract untouched; tests assert EFFECTS not strings.

- [x] P14.1 `app/exec/runner.py` — execute + capture (timeout, exit, stdout/stderr) + 8 effect tests
- [x] P14.2 `app/exec/verify.py` — tcp/http/file/callback checks + 8 effect tests
- [x] P14.3 `app/targets/model.py` + additive migration (`targets`, `target_findings`) — persistent aim + evidence
- [x] P14.4 `app/adapters/` — 15/15 modules wrapped as 48 callable Actions (registry + catalog), no signature edits
- [x] P14.5 wire `payload_generator` output → runner — `app/exec/strike.py` generate→launch→VERIFY callback (5 tests, live)
- [x] P14.6 strike API: `POST /api/strike/reverse` + `/api/strike/actions`; records evidence on a target (no manual terminal)
- [x] P14.7 real intel: `app/exec/net.py` DNS/reverse/WHOIS/GeoIP (offline-safe) + `/api/net/*` — replaces md5 seeds
- [x] P14.8 real recon executor: threaded TCP connect scan + `/api/net/scan` (real open ports)
- [x] P14.9 findings → self-contained HTML report (`app/targets/report.py` + `GET /api/targets/<id>/report`)
- [x] P14.10 playbook steps become execute+verify (`app/exec/playbook.py`, `POST /api/playbooks/<id>/run`, checkpoint/rollback) — **Track 5 now has 0 open items**
- [x] P14.11 **acceptance chain**: scan→strike→verify→evidence→report, unattended (`tests/char/test_firepower_chain.py`)
- [x] P14.12 gate `G10` — **GREEN**: 262 suite, audit exit=0, 0 routes lost, frozen modules byte-identical

## TRACK 6 — C2 / LISTENER / BEACON (P15) — real channel, managed listener, observed beacons

Gate G11. Coverage gaps (measured): C2 is poll-based (1500 ms, `c2_client.js:130`) over
UNLOCKED raw dicts with `list.pop(0)` (thread-unsafe, O(n), lost on restart);
no listener *service* exists (only the P14.5 strike listener); the beacon is a simulated
schedule (`evasion_framework.py:567,612`) never applied to real traffic nor observed.

- [x] P15.1 C2/mobile queues — **already locked** via `app.state.STORE` (`MemoryStore`, RLock+deque) from P5; verified, no rebuild needed
- [ ] P15.2 persistent channel (SSE/WebSocket) replacing the 1500 ms poll; keep poll as victim fallback  ← fold into P10
- [x] P15.3 `ListenerService` — start/stop named listeners, `GET /api/listeners`, auto-finding on connect
- [x] P15.4 real beacon — `/api/c2/poll` returns jittered `next_interval_ms`; real arrival timeline recorded
- [x] P15.5 beacon monitor — `GET /api/c2/beacons[/<uid>]`, `POST /api/c2/beacon_config`, `GET /api/c2/beacon_agent`
- [x] P15.6 agent-side: `/api/c2/beacon_agent` emits a drop-in agent; `base_ms` tune knob; agent proven to honour server schedule (`tests/char/test_beacon_chain.py`)
- [x] P15.7 gate `G11` — **GREEN**: jitter observed; listener start/stop verified; C2 survives restart; 0 routes lost (`scripts/acceptance_g11.py` exit 0)

Rollback: `git checkout g10-ok`.

## Backlog (NOT gated)
- [ ] Real crypto via `cryptography` (replace hand-rolled AES/XOR)
- [ ] Optional LLM hook for ai_threat (feature-flagged, offline fallback)
- [ ] Tauri mobile target
- [ ] Plugin/skill registry for modules + templates
- [ ] Multi-node scale-out (shared Redis + object store)
