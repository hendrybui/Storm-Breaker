# Storm-Breaker — Advanced Update Plan (rev 2 — Option C)

Status: ACTIVE — Option C accepted via ADR-0002
Target baseline: commit `d98c57d` (branch `main`)
Method: skill-first / proof-of-fix; behavior-preserving refactors; the HTTP surface is the seam
Hard rule: **the update must not weaken the backend or the victim contract.** Non-Regression Contract §1 governs.
✅ = already produced; ⬜ = to do by the receiving agent.

---

## 0. Purpose & Scope

Re-architect Storm-Breaker's **skeleton** (flat monolith → layered app) in place, then deliver it as a
signed, offline-capable operator app. **Keep the feature modules and the victim contract untouched.**

Diagnosis (measured): `app.py` = 3,500 lines / 204 routes / 0 blueprints / 0 factory / 7 globals /
0 async. `database.py` = 1,485 lines / connect-per-call. 15 modules are stdlib-only generators.
→ Rebuild the skeleton; wrap the organs.

In scope: characterization tests, app factory + blueprints, service layer, state/db core, job queue,
hardening, offline frontend, Tauri shell, realtime, panel migration, packaging.
Backlog (not gated): real crypto, optional AI hook, mobile, plugin registry, multi-node.

## 1. Non-Regression Contract (the guarantee)

| ID | Rule | Enforced by |
|----|------|-------------|
| NR-1 | Victim endpoints keep path + method + shape (§2.1). | `tests/contract/victim.json` |
| NR-2 | Operator routes ADD-ONLY during migration; same path/response. | characterization tests |
| NR-3 | No public module signature changes. Wrap via `app/adapters/`. | `TEST-MODULES` |
| NR-4 | DB schema additive; migrations idempotent; backup before migrate. | `app/core/migrations/` |
| NR-5 | Every phase ends GREEN on `audit/audit_storm_breaker.py` + characterization suite. | gate per phase (§6) |
| NR-6 | New UI behind flag; legacy `panel.html` stays default until parity. | flag `UI_V2` |
| NR-7 | One git tag per green gate; rollback = checkout tag. Branch per track. | tags `g0-ok`… |
| NR-8 | Nothing victim-served requires a server-side build at capture time. | static-only vendor |

If any step can't satisfy NR-1..NR-8 → stop, open an ADR.

## 2. Frozen Interfaces (do not break)

### 2.1 Victim endpoints — frozen exactly
See `tests/contract/victim.json` (source: `app.py` `_VICTIM_PUBLIC_PATHS` + prefixes `/t/ /assets/ /c/`).

### 2.2 Modules (public API frozen)
`credential_parser, payload_generator, obfuscation_engine, report_generator, lure_generator, telegram_bot,
evasion_framework, threat_intel, session_hijacker, pivot_engine, rat_controller, ai_threat_analyzer,
zeroday_lab, quantum_crypto, deep_recon`.

### 2.3 Database (additive only — 24 tables)
See `docs/TAB-MAP.md` §notes for the full table list; never drop/rename.

## 3. Target Architecture (Strangler)

```
storm-web/
  app/__init__.py        create_app() factory            (NEW)
  app/config.py          env-based config                (NEW)
  app/extensions.py      csrf, limiter, db handles       (NEW)
  app/blueprints/        victims, c2, mobile, capture,   (NEW — routes moved VERBATIM)
                         intel, tools, osint, admin, analytics
  app/services/          domain logic extracted from routes (NEW)
  app/core/state.py      StateStore adapter (memory|redis) (NEW)
  app/core/db.py         repository + migrations/          (NEW)
  app/core/jobs.py       background worker                 (NEW)
  app/adapters/          thin wrappers over 15 modules      (NEW; modules UNCHANGED)
  app.py                 shrinks to a shim -> create_app() (KEPT, reduced)
15 modules, 16 templates, victim endpoints, DB tables        (UNCHANGED)
```
Old routes are moved domain-by-domain. Behavior stays identical until each domain is migrated.

## 4. Phase Plan

### TRACK 0 — Safety net
| ID | Action | Gate | Rollback |
|----|--------|------|----------|
| P0.1 | tag `pre-upgrade` | — | — |
| P0.2 | baseline audit → `docs/evidence/G0-audit.txt` | — | — |
| P0.3 | DB backup → `backups/` | — | restore |
| P0.4 ✅ | victim contract file | — | delete |
| P0.5 ✅ | ADR-0001 | — | — |
| P0.6 ✅ | `docs/TAB-MAP.md` | — | — |
| P1.1–P1.6 | **characterization tests** freezing 204 route responses | **G0→G1** | — |

### TRACK 1 — Skeleton rebuild
| ID | Action | Gate | Rollback |
|----|--------|------|----------|
| P2.1–P2.6 | app factory + config + extensions; `app.py` → shim | — | revert commit |
| P3.1–P3.24 | move routes to blueprints domain-by-domain (verbatim) | **G2 route parity** | revert per blueprint |
| P4.1–P4.6 | extract services from routes | — | revert |
| P5.1–P5.7 | StateStore + repository + migrations + WAL/indexes/pool | — | PRAGMA/adapter revert |
| P6.1–P6.6 | job queue + worker; move scans/reports/notifications off the request path | **G3 core parity** | disable worker |

### TRACK 2 — Hardening
| ID | Action | Gate | Rollback |
|----|--------|------|----------|
| P7.1–P7.6 | hashed creds, CSRF, lockout persist, upload caps, retention | **G4 hardening** | flag off |

### TRACK 3 — Delivery
| ID | Action | Gate | Rollback |
|----|--------|------|----------|
| P8.1–P8.4 | design tokens + vendor CDN assets offline | **G5 offline** | restore CDN |
| P9.1–P9.6 | Tauri shell + sidecar + tray + CSP | **G6 shell** | delete `src-tauri` |
| P10.1–P10.6 | push channel, poll fallback, native notif, deep links, safe-exec | **G7 realtime** | use poll |
| P11.1–P11.n | panel migration tab-by-tab behind `UI_V2` | **G8 parity** | flag off |
| P12.1–P12.4 | signing, CI publish, report artifacts | **G9 packaging** | disable CI |

### TRACK 4 — Closeout
| ID | Action | Gate |
|----|--------|------|
| P13.1–P13.3 | runbook, final sweep, backlog handoff | — |

Full task-level list: **`docs/TODO.md`**. Progress ledger: **`docs/PROGRESS.md`**.

## 5. End-to-End Path

`P0→G0→P1→G1→P2→P3→G2→P4→P5→P6→G3→P7→G4→P8→G5→P9→G6→P10→G7→P11→G8→P12→G9→P13`

A phase starts only when the prior gate is GREEN. A failed gate rolls back the phase, not the project.

## 6. Verification & Gates

- Reliability: `python3 audit/audit_storm_breaker.py --url http://127.0.0.1:2525` exits 0.
- Behavior: characterization suite + route/method/schema diff = add-only.
- Victim: replay `tests/contract/victim.json` with no session.
- Proof-of-fix: tests first, green, evidence pasted into `docs/PROGRESS.md`.

## 7. Rollback Matrix

| Level | Scope | Action |
|-------|-------|--------|
| L0 | hunk | `git checkout -- <file>` |
| L1 | step | revert step commit |
| L2 | phase | checkout prior gate tag |
| L3 | whole project | checkout `pre-upgrade`; restore DB backup |

## 8. Risk Register

| ID | Risk | Mitigation |
|----|------|-----------|
| RK1 | refactor regresses routes | characterization tests BEFORE any move (P1) |
| RK2 | state split across workers | StateStore before worker>1 |
| RK3 | victim breakage | freeze contract; HTTP-only for victims |
| RK4 | upstream divergence | accept; document in ADR-0002 |
| RK5 | CSP blocks charts/maps | allow-list + de-inline handlers |
| RK6 | silent DB corruption | backup + idempotent migrations |

## 9. Definition of Done (per step)

1. Additive or ADR-justified. 2. Tests first, then code; suite + audit green.
3. No §2 frozen-interface diff. 4. PROGRESS.md row appended with evidence. 5. Rollback recorded.

## 10. Skill Invocation Map

| Phase | Skill | Purpose |
|-------|-------|---------|
| all | `superpower` | skill-first, checklists, proof-of-fix |
| P0,P1,debug | `sniper-debugging` | isolate→root cause→verify |
| P8,P11 | `ui-design-system`, `artifacts-builder` | tokens, anti-slop, offline UI |
| P9,P10,P12 | `tauri`, `tauri-sidecar`, `tauri-csp`, `tauri-code-signing` | shell, packaging |
