# ADR 0001 — Wrap Storm-Breaker with a Tauri shell (don't rewrite the backend)

- Status: Proposed (plan step P0.5 — accept before Phase 3)
- Date: 2026-10-27
- Deciders: upgrade operator, receiving agent

## Context
Storm-Breaker is a working Flask app: `storm-web/app.py` (204 routes), 15 standard-library modules,
24-table SQLite DB, 30-tab jQuery panel, 16 phishing templates. It runs on the Flask dev server at
`0.0.0.0:2525` and is launched manually. Gaps: no packaging, CDN-coupled UI, poll-based C2, no tests/CI.

The upgrade must be "advanced and efficient" but MUST NOT weaken the backend.

## Decision
WRAP the existing app in a Tauri v2 shell that runs the Flask backend as a **sidecar** binary. The
backend keeps its behavior and interfaces; Tauri adds windowing, tray, native notifications, IPC/WS push,
offline UI, and packaging on top.

## Consequences
- (+) Backend untouched → zero victim-contract risk (NR-1), zero module-signature risk (NR-3).
- (+) Fastest path to a signed, installable app; reuses all 30 features.
- (−) Dual stack (Rust + Python). Mitigated: sidecar is a thin PyInstaller launcher; host-OS first,
      other OSes via CI later.
- (−) Two build toolchains. Mitigated: keep Tauri shell additive (`src-tauri/` can be deleted to revert).

## Alternatives considered
- Rewrite backend in Rust/Python-async — larger blast radius, rejected for this cycle.
- Electron instead of Tauri — bigger binaries, bundled Chromium; Tauri reuses OS WebView.
- Keep browser-only, just vendor assets — no packaging/tray/native; kept as Fallback A.

## Non-negotiables carried from the plan
NR-1..NR-8 (see `docs/ADVANCED-UPDATE-PLAN.md` §1). Victims speak HTTP to `:2525` only; Tauri IPC is
operator-side only.
