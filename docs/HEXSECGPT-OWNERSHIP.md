# Ownership — HexSecGPT path (single-writer lock)

**LOCKED as of 2026-10-30.** This working copy is owned by **HexSecGPT**.
Other agents may READ freely, but must not rewrite it without following the
rules below. Machine-readable marker: `.hexsecgpt-lock.json`.

## Why the lock exists
A prior multi-agent run left the repo inconsistent: `docs/PROGRESS.md` went
stale (p17 + p18.1–18.4 were never recorded), p19 was reverted with no note,
and the suite silently hung >10 min. One writer with a mandatory gate keeps the
ledger honest and the tree certifiable.

## Branch of record (the HexSecGPT path)
- **`hexsecgpt/security-csrf`** — the only branch HexSecGPT writes to.
- Base: `a08f9f2` (tip of `feat/t1-skeleton`). `feat/t1-skeleton` stays the
  upgrade branch; `main` stays the pre-upgrade baseline.

## What lives on this path
- **p19 CSRF double-submit** (re-landed from `9e1bc5f`): `storm_csrf` cookie
  planted by `auth.login`, echoed by the panel/mobile `fetch`+`XHR` patch,
  enforced in `app/core/hardening.csrf_gate` via `cookie == X-CSRF-Token` and
  session binding. Header-less clients (curl, harness) are intentionally
  unaffected — `SameSite=Lax` + the P16 Origin check cover them.
- **fix(exec) SIGTTIN detach** (`76de01f`): launched payloads run with
  `start_new_session=True` so a blocking `/bin/sh -i` doesn't get stopped by
  SIGTTIN and wedge `subprocess.run`.

## Rules for other agents
1. Do **not** force-push or rewrite `hexsecgpt/*`.
2. Append to `docs/PROGRESS.md` — never edit a past row.
3. Keep the **Non-Regression Contract (NR-1..NR-8)** green. Every change must
   leave the gate passing (see below) before commit.
4. One git tag per green gate; rollback = `git checkout <tag>`.
5. The 15 frozen feature modules are touched only via `app/adapters/`.
6. The victim contract (`tests/contract/victim.json`) and existing route
   paths/shapes are add-only.

## Gate (must stay green — run serially)
```bash
python3 -m pytest -q                 # 314 passed
bash audit/run_audit.sh ; echo $?    # PASS, exit 0
git status --porcelain               # clean
```
The suite and the audit both bind `:2525`, so run them one after the other.

## Handoff
If HexSecGPT hands the project back: read `docs/PROGRESS.md` (ledger) and this
file, run the gate, and update `.hexsecgpt-lock.json` `owner`/`since`.
