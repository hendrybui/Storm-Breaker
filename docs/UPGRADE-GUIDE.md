# UPGRADE GUIDE — pre-upgrade → current (P13.1)

For an existing install. Compliments `docs/RUNBOOK.md` (operation) and
`docs/ADVANCED-UPDATE-PLAN.md` (why each change was made).

## What changed, in one table

| Area | Before | After | Additive? |
|---|---|---|---|
| Backend shape | 3,500-line `app.py`, 204 routes | app factory + 24 blueprints, add-only routes | yes |
| Runtime data | module globals, no locks | `app.state.STORE` (RLock + deque) | yes |
| Persistence | connect-per-call | WAL + indexes + idempotent migrations | yes |
| Operator auth | plaintext config.php | DB-backed lockout; hash shim available | yes |
| Delivery | CDN-dependent | vendored offline assets + Tauri app | yes |
| Action | generated strings only | exec/verify, strike, targets, report | yes |
| C2 | blind 1.5 s poll | managed listeners + server-driven jittered beacon | yes |
| Operator UX | fixed polling | SSE live channel + Live Ops tab | yes |

**No frozen module was edited and no route was removed** — verified at every gate.

## Upgrade steps

1. **Back up.**
   ```bash
   cp storm-web/storm_breaker.db backups/storm_breaker.db.$(date +%Y%m%d-%H%M%S)
   cp storm-web/config.php backups/config.php.bak
   ```
2. **Fetch.** `git fetch && git checkout <tag>` (e.g. `g12-ok`).
3. **Deps.** `pip install -r storm-web/requirements.txt && pip install -r requirements-dev.txt`
   New *runtime* deps: none. New *dev* dep: `pytest`.
4. **Migrate.** Automatic and idempotent on first boot (`migrate()`), additive
   tables only (`targets`, `target_findings`, `login_lockouts`). Existing tables
   are re-applied with `IF NOT EXISTS`.
5. **Verify.** `python3 -m pytest -q` (expect 299) then `bash audit/run_audit.sh`
   (expect exit 0). Serially.
6. **Optional.** Desktop app: `bash scripts/build_sidecar.sh && bash scripts/build_app.sh`.

## Signing (optional)

`docs/SIGNING.md`. Without certificates the build still succeeds; artifacts are
unsigned. Add the CI secrets in `docs/SIGNING.md` to sign on release.

## Rollback

```bash
git checkout pre-upgrade
cp backups/storm_breaker.db.<stamp> storm-web/storm_breaker.db
```

DB rollback is safe: migrations are additive, so a newer DB also boots on older
code (extra tables are simply ignored).

## Config notes

- `config.php` keeps its PHP-ish format (the parser is unchanged). P7.3 added a
  DB-backed brute-force lockout.
- Beacon defaults to the `always_on` profile (15 s). For snappier interactive
  work `POST /api/c2/beacon_config {"base_ms": 1500}`; the server then sets the
  cadence and the agent obeys.

## Post-upgrade checklist

- [ ] `pytest` green, audit exit 0
- [ ] `GET /api/targets`, `/api/live`, `/api/c2/beacons` reachable
- [ ] panel loads fully offline
- [ ] backups stored off-box
- [ ] (optional) signing secrets configured
