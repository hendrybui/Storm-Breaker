# WORKFLOW — the clean loop (Storm-Breaker re-architecture)

One page. If a task doesn't fit this loop, stop and update this file first.

## Daily loop (per task)

```
1. BRANCH   feat/t<n>-<track> off the last green tag        (one branch per track)
2. TESTS    write/extend the failing test FIRST             (tests/char = frozen shapes,
                                                             tests/unit = new code)
3. CODE     move code VERBATIM (NR-2); improvements are P7+ only
4. VERIFY   python3 -m pytest -q                → all green (char + unit)
            bash audit/run_audit.sh             → starts backend if needed,
              (or --stop)                         runs harness, exit 0 = PASS
            git diff -- storm-web/app.py | grep -E '^-.*@app.route' → investigate
5. LEDGER   docs/PROGRESS.md row (append-only) + evidence file in docs/evidence/
6. COMMIT   p<phase>.<step>: <action> [gate=Gx]
7. GATE     tag g<n>-ok ONLY when the whole gate scope is green; rollback = checkout
            the previous tag
```

## Repo hygiene rules (enforced by .gitignore since 2026-10-27)

- **Never track:** live DB (`storm-web/storm_breaker.db` + WAL sidecars), runtime token
  state (`check-c.json`), `secret_key.bin`, `Settings.json`, `__pycache__/`, `.vscode/`,
  env-specific ops scripts (`audit/restart_after_reboot.sh`), ephemeral recon data
  (`crtsh.txt`).
- **Always track:** `docs/` (planning + PROGRESS + evidence), `backups/` (deliberate
  rollback artifacts), `tests/_frozen/` (the contract).
- `config.php` IS tracked for now (deployment config); it contains plaintext creds —
  P7.1 (hashed operator password) will fix that; revisit tracking then.
- `git status` should be quiet after a clean commit. If it isn't, the mess goes in
  `.gitignore` or gets committed — never left dangling.

## Snapshot regeneration (additive routes only)

New routes are ADD-ONLY (NR-2). After adding routes:

```
python3 -m pytest tests/char/test_route_inventory.py --update-snapshots
git diff tests/_frozen/route_inventory/ | grep -E '^-"path"'   # MUST be empty
```

Any removed path = you broke the contract → revert.

## Where things live

| What | Where |
|------|-------|
| Mission / constraints | `docs/HANDOFF.md` |
| Task queue (gates G0-G9) | `docs/TODO.md` |
| Full plan | `docs/ADVANCED-UPDATE-PLAN.md` |
| Append-only progress + evidence pointers | `docs/PROGRESS.md` |
| Frozen HTTP contract | `tests/contract/victim.json`, `tests/_frozen/` |
| Unit tests (new code) | `tests/unit/` |
| Evidence per gate | `docs/evidence/*.txt` |
| Decision records | `docs/adr/` |
