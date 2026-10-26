# TAB-MAP — panel tabs ↔ JS ↔ backend routes

Recon artifact (plan step P0.6). 30 sidebar tabs found in `storm-web/flask_templates/panel.html`
(via `data-sidebar-tab`/`data-tab`). Use this to migrate tabs one at a time (Phase 5) with parity checks.

| # | Tab ID | Frontend JS (`assets/js/`) | Backend area | Frozen? |
|---|--------|----------------------------|--------------|---------|
| 1 | links | script.js | `/list_templates`, `/t/<name>/` | victim-adjacent |
| 2 | images | script.js | `/api/images`, `/images/<f>` | — |
| 3 | audio | script.js | `/api/audio`, `/sounds/<f>` | — |
| 4 | logs | script.js | `/receiver`, `/receiver.php` | victim |
| 5 | terminal | script.js | `/api/terminal` (subprocess) | — |
| 6 | c2 | c2_client.js | `/api/c2/*` | victim endpoints frozen |
| 7 | files | file_manager.js | `/api/c2/get_file_list`, `/api/c2/get_download` | — |
| 8 | mobile | mobile_control.js, mobile-backdoor.js | `/api/mobile/*` | victim endpoints frozen |
| 9 | analytics | advanced_dashboard.js | `/api/analytics/*`, `/api/system/info` | — |
| 10 | intel | victim_profiler.js | `/api/fingerprints/*`, `/api/keystrokes/*`, `/api/webrtc_*` | — |
| 11 | credentials | credentials_intel.js | `/api/credentials/*` | — |
| 12 | payloads | payload_generator.js | `/api/payloads/*` | — |
| 13 | campaigns | campaign_manager.js | `/api/campaigns/*`, `/c/<code>` | victim-adjacent |
| 14 | profiles | victim_profiler.js | `/api/profiles/*` | — |
| 15 | obfuscation | obfuscation_ui.js | `/api/obfuscate*` | — |
| 16 | reports | report_generator_ui.js | `/api/reports*` | — |
| 17 | lures | lure_generator_ui.js | `/api/lures/*` | — |
| 18 | exfil | browser_exfil_ui.js | `/api/browser-exfil*` | victim endpoint frozen |
| 19 | network | network_discovery_ui.js | `/api/network/*` | victim endpoint frozen |
| 20 | playbooks | playbook_ui.js | `/api/playbooks/*` | — |
| 21 | evasion | evasion_ui.js | `/api/evasion/*` | — |
| 22 | threat-intel | threat_intel_ui.js | `/api/threat-intel/*` | — |
| 23 | session-hijack | session_hijacker_ui.js | `/api/session-hijack/*` | — |
| 24 | pivot | pivot_engine_ui.js | `/api/pivot/*` | — |
| 25 | rat | rat_ui.js | `/api/rat/*` | — |
| 26 | ai-threat | ai_threat_ui.js | `/api/ai-threat/*` | — |
| 27 | zeroday | zeroday_ui.js | `/api/zeroday/*` | — |
| 28 | quantum | quantum_crypto_ui.js | `/api/quantum/*` | — |
| 29 | deeprecon | deep_recon_ui.js | `/api/deeprecon/*` | — |
| 30 | alerts | script.js | `/api/alerts*` | — |

Notes:
- Tabs 1–4, 30 share `script.js`; tab 8 spans two JS files; tabs 10 and 14 share `victim_profiler.js`.
- `settings` is a sidebar tab without a routes group (writes `Settings.json`).
- CDN libs referenced by the panel: chart.js 4.4.0, leaflet 1.9.4 (candidates for P2.2 vendoring).

## External CDN references (for offline vendoring — P2.2)
```
https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js
https://unpkg.com/leaflet@1.9.4/dist/leaflet.js
```
(Tailwind / FontAwesome / Google Fonts also appear via `<link>` — grep `cdn.` and `unpkg.` and
`fonts.googleapis` in `panel.html`, `login.html`, and `templates/*/index.html` before vendoring.)
