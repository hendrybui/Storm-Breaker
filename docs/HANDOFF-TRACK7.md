# HANDOFF — Track 7 (REALTIME + LIVE PANEL) → next agent

**Status: G12 GREEN — track complete.** Read top-to-bottom before touching anything.

| | |
|---|---|
| Branch | `feat/t1-skeleton` |
| Head | `64519c4` |
| Tags | `g11-ok` (track rollback), `g12-ok` (gate) |
| Gate | **G12 ✅** — `docs/PROGRESS.md` gate table |
| Suite | **299 passed** |
| Audit | **exit 0** |
| Routes | 222 (0 lost, +2 additive) |
| Frozen modules | 15 modules + `database.py` **byte-identical** |

Rollback for the entire track: `git checkout g11-ok`.

---

## 1. What Track 7 changed (the point)

Every organ existed but the operator drove it from the API and the browser
polled blind fixed intervals. Now there is a **push channel** and a **live view**.

| Task | Deliverable |
|---|---|
| P10.1 | `app/core/events.py` (bounded, thread-safe bus) + `app/blueprints/live.py`: `GET /api/events` (SSE) and `GET /api/live` (JSON snapshot). HTTP poll kept as fallback. |
| producers | `beacon.TRACKER.record` → `beacon`; `ListenerService._on_connect` → `listener`; `strike` blueprint → `strike` |
| P10.4 | checkpoint/rollback already shipped as `app/exec/playbook.py` (P14.10) |
| P10.5 | measured: snapshot 9 ms median, push 7.3 ms median (target < 300 ms) |
| live UI | `assets/js/storm_live.js` + a **Live Ops tab** in `flask_templates/panel.html` (sidebar button, `#tab-live`, script include) |

## 2. Design rules this track obeyed

1. **Additive only** — no frozen module edited; no existing route changed; poll endpoints untouched as fallback.
2. **`/api/events` stays OUT of the audit catalogue** — it never returns, so a non-streaming client would block. `/api/live` is in the catalogue instead.
3. **Bounded queues** — a stalled SSE subscriber drops events instead of growing memory (`MAX_QUEUE = 200`).
4. **Producers never depend on the bus succeeding** (`publish` swallows `queue.Full`).
5. **Run the suite and the audit SERIALLY** — both bind `:2525`.

## 3. How to verify

```bash
python3 -m pytest -q                                  # expect 299 passed
python3 scripts/acceptance_g12.py ; echo "exit=$?"     # expect PASS, exit 0
git diff --stat pre-upgrade..HEAD -- <15 frozen modules> storm-web/database.py   # EMPTY
bash audit/run_audit.sh ; echo "exit=$?"               # expect PASS, exit 0
git status --porcelain                                 # expect empty
```

Evidence: `docs/evidence/g12-realtime.txt`.

## 4. Do NOT touch (frozen)

The 15 `storm-web/` modules + `storm-web/database.py`. Wrap and delegate.

## 5. What remains in the main plan (NOT this track)

- **P10.2 / P10.3** — Tauri-side: native notification on capture, `storm://` deep links.
- **P11.1+** — the React/Vite/shadcn panel migration (`UI_V2`). Track 7 shipped the
  live UI on the **legacy** panel rather than scaffolding `ui/`; decide which first.
- **P12.x** — code signing + CI publish workflow.
- **P13.x** — runbook + final sweep.

Suggested next gate **G13** for whichever of the above is taken first.

## 6. Conventions

- Commit format: `p<phase>.<step>: <what> [gate=<G>]`; per-milestone tags `g<n>-ok`.
- Tasks → `docs/TODO.md`; delivered rows → `docs/PROGRESS.md` + evidence file.
- Prior handoffs: `docs/HANDOFF-TRACK5.md`, `docs/HANDOFF-TRACK6.md`.
