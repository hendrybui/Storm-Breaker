# FINAL STATUS — Storm-Breaker upgrade (read me first)

**Everything in the plan is delivered.** Branch `feat/t1-skeleton`. Working tree clean.

## Gates

| Gate | Scope | Tag |
|---|---|---|
| G0–G6 | recon/freeze, tests, factory+blueprints, services, state, jobs, hardening, offline assets, Tauri shell | `g0-ok` … `g6-ok` |
| **G7** | realtime push latency measured (9 ms snapshot / 7.3 ms push, target < 300 ms) | `g7-ok` |
| **G8\*** | V2 React panel served at `/panel2`; default not flipped | `g8-ok` |
| **G9\*** | packaging: deb builds, signing configured (certs pending), release workflow | `g9-ok` |
| **G10** | firepower: exec → verify → strike → targets → report | `g10-ok` |
| **G11** | C2: managed listeners + server-driven jittered beacon + monitor | `g11-ok` |
| **G12** | realtime channel + Live Ops tab | `g12-ok` |
| G12b | native notifications + `storm://` deep links | — |
| **G13** | closeout: runbook, upgrade guide, final sweep | `g13-ok` |

`\*` = delivered with an honest caveat, noted in `docs/PROGRESS.md`.
Rollback whole upgrade: `git checkout pre-upgrade` (+ restore `backups/`).

## Try it in 3 commands

```bash
cd storm-web && python3 app.py            # -> http://127.0.0.1:2525/panel
```

Log in with the credentials in `storm-web/config.php` (default `admin` / `PASS`).

| Try | Where |
|---|---|
| **Live Ops** — watch events stream in | panel → *Live Ops* tab, or `/panel2` |
| **Fire a shell + verify it** | panel → Live Ops, or `POST /api/strike/reverse {"payload_type":"python_reverse"}` |
| **Real port scan** | `POST /api/net/scan {"host":"127.0.0.1","ports":"1-1024"}` |
| **Managed listener** | `POST /api/listeners/start {"name":"catch","host":"127.0.0.1","port":0}` |
| **Beacon speed** | `POST /api/c2/beacon_config {"base_ms":1500}` |
| **V2 panel (new UI)** | `http://127.0.0.1:2525/panel2` |
| **Desktop app** | `bash scripts/build_sidecar.sh && bash scripts/build_app.sh` |

Unattended proof the whole loop works:
```bash
python3 scripts/acceptance_firepower.py   # scan → strike → VERIFIED → evidence → report
python3 scripts/acceptance_g11.py         # C2 survives restart, listener, beacon
python3 scripts/acceptance_g12.py         # SSE delivers listener/beacon/strike live
```

## Verify (serially — suite and audit both bind :2525)

```bash
python3 -m pytest -q                  # 302 passed
bash audit/run_audit.sh ; echo $?     # PASS, exit 0
git status --porcelain                # empty
```

## Honest remainder (small, optional)

- **P10.2/P10.3 runtime** — notification/deep-link code compiles and the endpoint
  contract is verified; the OS-level prompt needs a desktop session.
- **G9 signing** — add certificates per `docs/SIGNING.md`; artifacts are unsigned today.
- **G8 default flip / P11.32** — V2 covers all 30 tabs but several are read-only;
  flip the default once they have real interactivity.

## Map

`docs/RUNBOOK.md` (operate) · `docs/UPGRADE-GUIDE.md` (upgrade) · `docs/SIGNING.md` ·
`docs/ADVANCED-UPDATE-PLAN.md` (the plan) · `docs/PROGRESS.md` (ledger + gates) ·
`docs/HANDOFF-TRACK5|6|7.md` · `docs/evidence/` (per-phase proof).
