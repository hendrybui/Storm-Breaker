# FIREPOWER — turning the well-machined frame into a weapon

## Honest verdict (measured 2026-10-27)

The P1–P9 upgrade rebuilt the *frame* (factory, blueprints, services, state, jobs, tests, Tauri shell,
offline assets, packaging). It did **not** change what the app can actually **hit**. The barrel is original.

Evidence:

| Signal | Finding |
|--------|---------|
| Modules that EXECUTE | only `obfuscation_engine`, `payload_generator`, `rat_controller` (and only locally) |
| Modules that SIMULATE | `deep_recon` (84 md5/random "seeds"), `ai_threat_analyzer` (44), `zeroday_lab` (26), `quantum_crypto` (28) |
| Fake intel | `threat_intel.py:217` `md5(ip)` GeoIP; `:325` "simulated — real impl would query HIBP" |
| Fake OSINT | `deep_recon.py:35` `md5(domain)` seeds DNS/WHOIS/CT |
| Execution in new app/ | only `app/blueprints/system.py` (runs commands on the **server host**, not the target) |
| "Execute" API | `payload_generator.py:360 def execute(cmd)` — one helper, not a layer |

**So: pretty, safe, tells you what *could* be done. That is the toy pattern.**

## Toy vs Weapon — the only line that matters

| | Toy | Weapon |
|--|-----|--------|
| Loop | generate → **you** copy-paste → hope | select target → fire → app **runs, observes, confirms** |
| Output | a string | an exit code + captured output + evidence |
| Aim | you remember the IP | persistent target record |
| Truth | "should work" | "verified: callback received" |

A weapon has three organs the app lacks: **Execution**, **Verification**, **Target model**.
Without them, every extra module is just more paper.

## The four gaps (fix these, in order)

1. **Execution** — run the generated artifact. `subprocess`/`socket`/`ssh` with timeout, exit code,
   captured stdout/stderr as artifacts. Modules keep frozen signatures; `app/adapters/` exposes them
   as *runnable actions*.
2. **Verification** — after every action, check the effect: tcp connect, http probe, file landed,
   callback received. **No claim without a check.**
3. **Target model** — new additive tables: `targets`, `target_findings`, `evidence`. Aim deliberately;
   evidence accumulates per host, feeds `report_generator`.
4. **Real intel** — replace md5-seeded simulation with real calls (DNS/WHOIS/CT/GeoIP) via `requests`,
   with graceful offline fallback so NR-8 still holds.

## The layer (additive — frozen contract untouched)

```
storm-web/app/
  exec/runner.py     execute(cmd|payload) -> {exit, stdout, stderr, artifacts}   (NEW)
  exec/verify.py     tcp/http/file/callback checks -> {ok, detail}               (NEW)
  targets/model.py   target + evidence store (new tables, additive migration)    (NEW)
  adapters/          wraps the 15 frozen modules as executable actions           (NEW)
```

Rides the existing `app/core/jobs.py` worker (P6) so long actions don't block requests.

## Acceptance test = the definition of "not a toy"

One click against one lab host, **unattended**, produces:
`scan → open listener → deliver payload → receive callback → verify session → record evidence → report`.
If a human still copy-pastes between steps, it's a toy. Target: zero copy-paste, verified result,
evidence attached.

## Ordering (this beats crypto and AI)
`execution → verification → target model → real intel` **before** real crypto and AI hooks.
Firepower first; the rest is finish.

## Non-regression
- NR-1..NR-8 unchanged. Modules are WRAPPED, never edited (NR-3).
- New tables additive (NR-4). New routes additive (NR-2).
- Every new action ships a test that asserts the *effect*, not the string.
