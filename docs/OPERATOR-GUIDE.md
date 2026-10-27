# Storm-Breaker — Full Operator Guide & Feature Audit

**Audience:** the operator running this on their own box.
**Scope:** every tab, every endpoint, what actually executes, what only prints strings, what breaks, and how to drive it.
**Revision:** P16 (2026-10-28). Supersedes the README for operational detail — the README is upstream marketing, this is ground truth from the code.

> **Read this first.** Storm-Breaker is a *harvest + generate* tool with a thin
> *execute* layer bolted on in P14/P15. Roughly 90% of the surface produces
> commands/config for you to paste somewhere else. Only the section
> [8. The execution layer](#8-the-execution-layer-the-only-parts-that-touch-your-system)
> actually runs anything. Everything else is a very good cheat-sheet engine with
> a database attached.

---

## 1. Architecture & trust model

```
┌──────────────────────────────────────────────────────────────┐
│ Flask app  (storm-web/app.py  →  app.create_app())           │
│                                                              │
│  app.py          legacy shim: auth gate, lockout, __main__   │
│  app/__init__.py factory: secret key, ProxyFix, blueprints   │
│  app/blueprints/ 36 blueprints — every HTTP route            │
│  app/core/       db, jobs, events, retention, lockout,       │
│                  hardening (CSRF/CSP/upload caps), migrations │
│  app/services/   business logic (capture, c2, mobile, intel…)│
│  app/exec/       ← the ONLY code that runs things            │
│  app/adapters/   48 callable Actions wrapping the 15 modules │
│  app/targets/    persistent aim + evidence store             │
│                                                              │
│  storm-web/*.py  15 legacy domain modules (generators)       │
│  database.py     raw sqlite3 layer, 29 tables                │
└──────────────────────────────────────────────────────────────┘
        ▲                                    ▲
        │ operator (session cookie)          │ victims (no cookie)
        │ /panel /panel2  /api/*             │ /t/<name>, /receiver,
        │                                    │ /api/fingerprint, /api/c2/*, /api/mobile/*
```

**Two classes of caller.** This distinction drives the entire security model:

| Class | Reaches | Auth |
|---|---|---|
| **Operator** (you, in a browser) | panel, `/api/*`, `*.php` | session cookie `IAm-logined` |
| **Victim** (a phished browser/phone) | `/t/<name>/*`, `/receiver*`, `/api/fingerprint`, `/api/keystrokes`, `/api/session/*`, `/api/c2/*`, `/api/mobile/*`, `/api/*-exfil/receive`, `/api/network/receive`, `/c/<code>`, `/assets/*` | none |

The gate lives in `storm-web/app.py:_auth_gate`. Anything not explicitly public
returns `401` (for `/api/*` / `*.php`) or a `302` to `/login`. See
[4. Talking to the API](#4-auth-sessions-csrf-and-lockout).

**Public-exposure consequence:** `/api/terminal` is a remote web shell. If you
tunnel this out (serveo/cloudflared/ngrok) with the default `admin`/`PASS`, you
have published a shell. Change the password.

---

## 2. Running it

### 2.1 Three supported entry points

| Way | Command | Binds | Notes |
|---|---|---|---|
| Localhost only | `python3 run_localhost.py` | `127.0.0.1:2525` | safest |
| LAN / tunnel | `cd storm-web && python3 app.py` | `0.0.0.0:2525` | what serveo needs |
| Desktop app | `bash scripts/build_sidecar.sh && bash scripts/build_app.sh` | sidecar on `127.0.0.1:2525` | Tauri v2 shell |

`backend_entry.py` is the PyInstaller sidecar entry (chdirs next to the exe,
binds loopback only, runs migrations first).

**Start it from `storm-web/`.** Settings were cwd-relative until P16; `audit/run_audit.sh`
starts from the repo root, so the two paths used to read *different* `Settings.json`
files. As of P16 all settings reads are anchored to `storm-web/Settings.json`
regardless of cwd. The repo-root `Settings.json` is now vestigial.

### 2.2 Public tunnel (serveo)

```bash
ssh -R messiah.serveousercontent.com:80:localhost:2525 serveo.net
```

Pin the subdomain with the `name:80:` form or you get a random one each reconnect.
Serveo is free with no SLA — if your ssh drops, `messiah` is grabbable and your
webhook URL rots. When the serveo edge is up but your client is down you get `502`.

`ProxyFix` is enabled by default (`trust_proxy: true`, or `STORM_TRUST_PROXY=0` to
kill it), so `request.scheme`/`request.host_url` correctly report `https` and the
C2 agent base URL is not emitted as mixed content.

### 2.3 Settings reference (`storm-web/Settings.json`)

Read/written by the panel's Settings tab via `/api/get_settings` + `/api/save_settings`.
`save_settings` **merges**, so keys you don't send are preserved.

| Key | Effect | Wired in |
|---|---|---|
| `generic_webhook` | URL the app POSTs notification JSON to on every capture | `app/state.py:send_notification` |
| `public_url` | informational bookmark of your tunnel | nothing (free text) |
| `trust_proxy` | enable ProxyFix | `app/__init__.py:_trust_proxy` |
| `session_cookie_secure` | add `Secure` to the session cookie | `app/core/hardening.py` |
| `server_port` | 2525 | informational |
| `poll_interval` | 2000 ms — legacy panel poll delay | `panel.html` JS |
| `auto_refresh`, `sound_notifications` | panel UI toggles | `panel.html` JS |
| `telegram_token`, `telegram_chat_id`, `telegram_enabled` | Telegram bot | `telegram_bot.py:load_config` |
| `panel_username` | display name | `panel.html` |
| `require_login` | **actually** gates the app when false | `app.py:_require_login` |
| `auto_delete_days` | retention worker deletes captures older than N days | `app/core/retention.py` |
| `log_db` | write operator actions to `operator_log` | `app.py` / `db.log_operator_action` |
| `ingest_secret` | shared secret required from victim traffic. Empty = **off** | `app.py:_ingest_key_gate` |
| `rate_limit_per_min` | per-IP request ceiling/min for normal paths (default 1200) | `app.py:_rate_gate` |
| `ingest_rate_per_min` | per-IP request ceiling/min for victim paths (default 600) | `app.py:_rate_gate` |

`session_cookie_secure` defaults **false** because the LAN entry is plain
`http://192.168.1.5:2525` and a `Secure` cookie would stop being sent there. Turn
it on only if you reach the box exclusively through the tunnel.

### 2.4 Telegram

The bot reads `storm-web/telegram_config.json` if it exists, else falls back to
`telegram_token`/`telegram_chat_id` in `Settings.json` (P16 — it previously only
read the former, which didn't exist, so the bot was permanently disabled).

`telegram_chat_id` accepts a numeric id (`-1001234567890`) or `@channelname`.
A bare word gets `@` prepended. **A bot's own @username is not a chat id** — DM
the bot and use the numeric id, or use a channel you own. Verify with
`POST /api/telegram/test`.

---

## 3. Notifications

`send_notification(payload)` is called on every capture (images, fingerprints,
mobile data, credentials). It reads `generic_webhook` and POSTs the JSON there —
queued through the job worker when running, inline otherwise. Failures are
swallowed silently.

Pointing it at `/panel` (the legacy default) was a **no-op**: `/panel` is GET-only
and behind the auth gate, so the gate `302`s to `/login` before routing ever runs
and the body is never parsed. P16 adds a real sink:

| Endpoint | Auth | Purpose |
|---|---|---|
| `POST /api/notify/inbox` | **public** | receive a notification, store in a 200-item deque |
| `GET /api/notify/inbox` | operator | read the last 100 |
| `POST /api/notify/inbox/clear` | operator | empty it |

Default `generic_webhook` is now `http://127.0.0.1:2525/api/notify/inbox` — a
localhost round-trip so notifications survive serveo outages. To fan out to
Discord/Slack instead, just replace the URL.

---

## 4. Auth, sessions, CSRF and lockout

```bash
BASE=http://127.0.0.1:2525
J=/tmp/sb.jar
curl -s -c $J -d 'username=admin&password=PASS' $BASE/login   # → 302, sets cookie
curl -s -b $J $BASE/api/targets                                # → 200
```

- Credentials live in `storm-web/config.php` (PHP array, read by
  `state.load_php_config`). Default `admin` / `PASS`. Change it — the operator
  password is hashed and verified via `app/core/passwords.py`.
- **Lockout:** 5 failed logins on an IP → `429` for 60s, persisted in the
  `login_lockouts` table so it survives restarts. Keyed on `X-Forwarded-For`
  (first hop) when present, else `remote_addr`.
- **CSRF:** mutating requests that carry an operator session must present an
  `Origin`/`Referer` whose *hostname* matches the request host. No header at all →
  allowed (covers curl/scripts). Cross-origin → `403`. Victim paths are effectively
  exempt because victims don't hold a session.
- **Limits:** global `MAX_CONTENT_LENGTH` 64 MB (`STORM_MAX_UPLOAD_MB`), plus
  per-endpoint caps in `app/core/hardening.py:UPLOAD_TYPE_LIMITS` → `413`.
- **CSP** is attached to all HTML responses; everything external is vendored
  under `/assets/vendor/` so the panel works offline.

### Known weakness

`X-Forwarded-For` is trusted raw for the lockout key. On a public URL, anyone can
rotate the header per request and brute-force `admin/PASS` without ever tripping
the lock. Either change the password or don't expose `/login`.

---

## 4b. Victim-side shared secret (`ingest_secret`)

The victim surface used to accept *anything* carrying a `uid`. Anyone who learned
your tunnel URL could register fake agents and — worse — poll
`/api/c2/poll` with a **guessed `uid`** and drain that agent's queued commands.

Set `ingest_secret` to a random string to close it. Behaviour:

- Empty string → **off**, fully backwards compatible (the default is a generated
  value, so it ships on).
- When set, victim traffic must present the secret, via any of:
  `?k=<secret>` in the query · `X-Storm-Key:` header · `k` in the JSON body ·
  the `storm_k` cookie.
- Operator traffic is **exempt** — the panel keeps working untouched.
- Loading a lure page with `?k=<secret>` plants the `storm_k` cookie, so **kit JS
  needs no patching** and every later POST from that page authenticates itself.

**Therefore: put `?k=<secret>` on every lure URL you hand out.**

```
https://<tunnel>/t/weather/?k=<ingest_secret>
```

Mismatch or absence → `401 {"error": "Invalid or missing ingest key"}`.
The generated beacon agent (`/api/c2/beacon_agent`) embeds the key automatically.

## 4c. Rate limits

A dependency-free fixed-window limiter (per IP) now guards everything, because
`/receiver` previously had only the 60 MB global cap and no rate limit at all —
an unauthenticated POST loop could fill the disk.

| Scope | Default | Setting |
|---|---|---|
| Victim/ingest paths | 600 req/min per IP | `ingest_rate_per_min` |
| Everything else | 1200 req/min per IP | `rate_limit_per_min` |

`/assets/*` is exempt. Set either key to `0` to disable that bucket. Over the
limit → `429` with `Retry-After`.

Ingest paths are: `/receiver*`, `/api/fingerprint`, `/api/keystrokes`,
`/api/session/*`, `/api/c2/*`, `/api/mobile/*`, `/api/notify/inbox*`,
`/api/browser-exfil/receive`, `/api/network/receive`.

---

## 5. The 30 dashboard tabs

`panel.html` (legacy, `/panel`) and `ui/src/tabs.js` (V2 React, `/panel2`) define
the same 30 tabs. V2 renders the same endpoints but several tabs are read-only.

| # | Tab id | Label | Backing module / blueprint | Kind |
|---|---|---|---|---|
| 1 | `links` | Phishing Links | `templates.py`, `templates/` | serve lures |
| 2 | `images` | Images | `system.py` `capture_rx` | capture gallery |
| 3 | `audio` | Audio | `system.py` | capture gallery |
| 4 | `logs` | Live Traffic | `intel.py` | capture view |
| 5 | `terminal` | Terminal | `system.py:/api/terminal` | **executes** |
| 6 | `c2` | Victim Shells | `capture_c2.py` | poll-based C2 |
| 7 | `files` | File Manager | `capture_c2.py` | file list/pull |
| 8 | `mobile` | Mobile | `capture_mobile.py` | phone C2 |
| 9 | `analytics` | Analytics | `system.py` | dashboards |
| 10 | `intel` | Intel | `intel.py` | fingerprints |
| 11 | `credentials` | Credentials | `credential_parser.py` | parser |
| 12 | `live` | Live Ops | `live.py` (P10) | **SSE, realtime** |
| 13 | `payloads` | Payloads | `payload_generator.py` | generator |
| 14 | `campaigns` | Campaigns | `campaigns.py` | tracking links |
| 15 | `profiles` | Profiles | `intel.py` | victim profiles |
| 16 | `obfuscation` | Obfuscation | `obfuscation_engine.py` | generator |
| 17 | `reports` | Reports | `report_generator.py` | HTML reports |
| 18 | `lures` | Lures | `lure_generator.py` | generator |
| 19 | `exfil` | Exfiltration | `browser_exfil.py` | data receive |
| 20 | `network` | Network | `net.py` (P14.7) | **DNS/WHOIS/scan** |
| 21 | `playbooks` | Playbooks | `playbooks.py` (P14.10) | **execute+verify** |
| 22 | `evasion` | Evasion | `evasion_framework.py` | generator |
| 23 | `threat-intel` | Threat Intel | `threat_intel.py` | enrichment |
| 24 | `session-hijack` | Session Hijack | `session_hijacker.py` | token/jwt tools |
| 25 | `pivot` | Pivot Engine | `pivot_engine.py` | graphing |
| 26 | `rat` | RAT Controller | `rat_controller.py` | generator (+launch) |
| 27 | `ai-threat` | AI Threat | `ai_threat_analyzer.py` | heuristics |
| 28 | `zeroday` | Zero-Day Lab | `zeroday_lab.py` | scanner/gen |
| 29 | `quantum` | Quantum Crypto | `quantum_crypto.py` | toy crypto |
| 30 | `deeprecon` | Deep Recon | `deep_recon.py` | OSINT |

Tabs marked **generator** produce commands/config. Tabs marked **executes** touch
the machine. The distinction is the single most important thing in this document.

### Tab-by-tab

**1 — Phishing Links.** `list_templates` enumerates `storm-web/templates/*`
(12 lure kits: `free_wifi`, `mobile_instant`, `weather`, `zoom_meeting`,
`job_application`, `voice_msg`, `nearyou`, `camera_temp`, `advanced_demo`,
`microphone`, `normal_data`, `mobile_security_update`). Serving is `/t/<name>/`.
Campaign links are `/c/<code>` and are tracked in `campaign_links` + `tracking_data`.

**2 — Images / 3 — Audio.** Galleries over `storm-web/images/` and `storm-web/sounds/`,
plus `POST /api/delete_images` / `/api/delete_audio`. `POST /api/nuke` empties every
capture dir and the in-memory analytics dicts — **it does not delete DB rows**.

**4 — Live Traffic.** Fingerprints, keystroke logs, session event streams, WebRTC
leak records. Raw producers are victim-side: `POST /api/fingerprint`,
`POST /api/keystrokes`, `POST /api/session/{start,events,end}`, `POST /api/webrtc_leak`.

**5 — Terminal.** `POST /api/terminal {"cmd": "..."}` → runs it on the Flask
host via `subprocess` and returns stdout/stderr. This is the one endpoint that is
a genuine shell. **The key is `cmd`** — send `command` and you get a `200` with
empty output, silently. (`session cwd` is tracked, so `cd` works.)

**6 — Victim Shells / 7 — File Manager.** Poll-based C2 for browser-based
"agents": victim calls `POST /api/c2/register`, polls `POST /api/c2/poll`, returns
`POST /api/c2/response`. Operator side queues with `POST /api/c2/queue_command`
and reads with `GET /api/c2/get_responses/<uid>`. File transfer:
`queue` a `file_list`/`file_download`, victim answers via
`POST /api/c2/file_list_response` / `file_download_response`, operator fetches with
`GET /api/c2/get_file_list/<uid>` / `get_download/<uid>`. Poll interval is 1500 ms
in `c2_client.js` — **use `GET /api/events` (SSE) instead for the operator view.**
P15 added server-driven jitter: `POST /api/c2/beacon_config` and
`GET /api/c2/beacons[/<uid>]` observe real arrival timing.

**8 — Mobile.** Same shape for phones: `register`/`poll`/`response` +
`send_command`, and media ingest via `/api/mobile/{camera,screenshot,audio,screen_record,background_data}`.
Tracking samples land in `tracking_data`, viewable at
`GET /api/mobile/tracking_data/<uid>`.

**9 — Analytics.** `GET /api/analytics/{dashboard,timeline,geo}` from a live
`ANALYTICS` dict: CPU/mem/disk via psutil, geo scatter for Leaflet, event timeline.

**10 — Intel / 15 — Profiles.** `POST /api/profiles/build` folds a victim's
fingerprint + geolocation + WebRTC leaks into a `victim_profiles` row;
`GET /api/profiles/list`, plus notes/tags/risk endpoints. `GET /api/fingerprints/list`
and `GET /api/webrtc_leaks` are the raw views.

**11 — Credentials.** `POST /api/credentials/scan` (sync) or `/scan-async` (job
queue) runs `credential_parser.py` over arbitrary blobs to extract
user/pass/pair/connection-string shapes; `GET /api/credentials/{list,pairs,stats}`.

**12 — Live Ops.** The realtime tab. `GET /api/events` is an SSE stream fed by
`app/core/events.BUS`; `GET /api/live` is a JSON snapshot (recent events,
listeners, beacon stats). Measured latency 9 ms snapshot / 7.3 ms push. The HTTP
poll is kept as a fallback for browsers without EventSource.

**13 — Payloads.** 30+ payload shapes from `payload_generator.py`;
`GET /api/payloads/types`, `POST /api/payloads/generate`. Pure generation — no
launch. To actually fire one: `POST /api/strike/reverse` (see §8).

**14 — Campaigns.** `POST /api/campaigns/create` makes a tracked phishing campaign
with a UUID code; `POST /api/campaigns/<id>/add_link` attaches lure URLs. Visits hit
`GET /c/<code>`, recorded in `campaign_links`/`tracking_data`.

**16 — Obfuscation.** `obfuscation_engine.py` — base64/hex/xor/ROT/string-split and
staged encoders. `POST /api/obfuscate`, `GET /api/obfuscate/profiles`.

**17 — Reports.** `POST /api/reports/generate` (or `-async`) builds a
self-contained single-file HTML report via `scripts/make_report.py` — zero external
refs. Stored in `reports`, viewable at `GET /api/reports/<id>/view`,
downloadable via `POST /api/export/all`.

**18 — Lures.** `lure_generator.py` — realistic phishing copy per category
(banking/tech/social…). `POST /api/lures/{preview,generate,bulk,render-html}`,
`POST /api/lures/save` into `saved_lures`.

**19 — Exfiltration.** `POST /api/browser-exfil/receive` accepts bundles from
`assets/js/*.js` collectors (cookies, localStorage, history, autofill);
`GET /api/browser-exfil[/stats]` to read. `POST /api/network/receive` takes
internal-network discovery data.

**20 — Network (P14.7/P14.8).** The only *real* recon in the tool:
`GET /api/net/{resolve,reverse,whois,geoip}` (offline-safe DNS/whois) and
`POST /api/net/scan {"host":"x","ports":"1-1024"}` — a threaded TCP connect scan
that reports genuinely open ports.

**21 — Playbooks (P14.10).** Named step lists that are **executed and verified**
(`app/exec/playbook.py`) with checkpoint/rollback.
`POST /api/playbooks/<id>/run` is the real one; `/execute` is the legacy path.

**22 — Evasion.** `evasion_framework.py` — traffic profiles (jitter/timing),
domain fronting suggestions, decoys, browser/device fingerprints. Generator only.

**23 — Threat Intel.** `threat_intel.py` — deterministic enrichment for IP, email,
username, technology: `POST /api/threat-intel/{ip,email,social,technology}`,
`GET /api/threat-intel/types`, `POST /api/threat-intel/report`. Mostly
algorithmic, not live API calls.

**24 — Session Hijack.** JWT/cookie toolkit: `assess`, `analyze-jwt`,
`parse-cookies`, `extract-tokens`, `build-replay`, `GET /features`, `GET /history`.
Detects `alg:none`, weak HMAC, `kid` injection, missing expiry, etc.

**25 — Pivot Engine.** `pivot_engine.py` builds attack graphs, privesc paths,
credential-reuse maps, kill-chain coverage: `POST /api/pivot/{attack-graph,attack-surface,privesc,credential-reuse,kill-chain}`.

**26 — RAT Controller.** See §6 — it deserved its own section.

**27 — AI Threat.** `ai_threat_analyzer.py` — anomaly scoring, behavioural
baselining, prediction, response plans. Heuristics, no LLM (backlog item).

**28 — Zero-Day Lab.** `zeroday_lab.py` — CVE lookup, shellcode generators, ROP
chain builder, fuzz factory:
`POST /api/zeroday/{scan,shellcode,rop,fuzz}`, `GET /api/zeroday/{cves,shellcode-types}`.

**29 — Quantum Crypto.** `quantum_crypto.py` — real base64/AES-ish/xor transforms
plus lattice/RSA/CBOM *simulations*. `POST /api/quantum/{encrypt,entropy,key-exchange}`,
`GET /api/quantum/{algorithms,benchmark,threat}`.

**30 — Deep Recon.** `deep_recon.py` — `POST /api/deeprecon/{domain,email,social,infra,darkweb,correlate}`
for OSINT pivoting. Generator/report only.

---

## 6. RAT Controller (tab 26) — the honest version

**It is a generator, not an agent.** Nothing is dispatched to a target. The only
function that inspects anything is `deep_system_recon()`, and it profiles **the
Flask host** — your box — not the victim. It makes no `subprocess` calls at all;
it's `platform.*` + `socket` + `psutil`.

`storm-web/rat_controller.py` (1426 lines, 23 functions) + `app/blueprints/rat.py`
(13→16 routes) + `assets/js/rat_ui.js`.

| Card | Endpoint | Produces |
|---|---|---|
| Deep System Recon | `POST /api/rat/recon` | os/python/network/env/users/processes/drives/security of **this host** |
| Reverse Shell Generator | `POST /api/rat/shells` | 15 one-liners (bash tcp/udp, python, powershell, php, ruby, perl, netcat×2, java, node, go, msfvenom×3), optional encoding |
| Persistence | `POST /api/rat/persistence` | 6 Windows + 6 Linux methods with `install_cmd` **and `cleanup_cmd`** |
| Lateral Movement | `POST /api/rat/lateral` | psexec/wmi/winrm/rdp/scp/ssh templates |
| Anti-Forensics | `POST /api/rat/anti-forensics` | log clearing, timestomp, secure delete, AMSI bypass, Defender off, rootkit hiding |
| Credential Targets | `GET /api/rat/credentials/targets` | chrome/firefox/edge artifact paths + method |
| Download Cradles | `POST /api/rat/cradles` | certutil/IEX/bitsadmin/mshta/curl/wget stagers |
| Process Injection | `GET /api/rat/injection` | 7 techniques w/ MITRE ids and API steps |
| C2 Config | `POST /api/rat/c2-config` | JS­ON profile (sleep/jitter/kill-date/URIs/headers/DNS-C2) |
| Payload Encoder | `POST /api/rat/encode` | base64/hex/xor/reverse/rot13/decimal |
| Network Tunnels | `POST /api/rat/tunnels` | `ssh -L/-R/-D`, chisel, proxychains |
| **Launch & Verify** *(P16)* | `POST /api/rat/launch` | **runs a python_reverse locally, binds a listener, VERIFIES the callback** |
| History | `GET /api/rat/history[?type=]`, `DELETE /api/rat/<id>` | audit trail in `rat_operations` |

### Fixed in P16

- `rat_persistence` was a **dead table**: created, indexed, helpers written, never
  inserted. Now one row per generated method, readable at `GET /api/rat/persistence[?os=]`.
- `rat_shell_sessions` was **write-only**: every POST saved a row, no reader existed.
  Now `GET /api/rat/shells` lists and `DELETE /api/rat/shells/<id>` removes them.
- `POST /api/rat/launch` composes the P14 organs (adapter → runner → listener →
  verify) so the callback is *observed*, not promised. Panel buttons: **Launch &
  Verify**, **Saved**.

### Still wrong (know these)

- `lhost` defaults to `0.0.0.0` in the blueprint (`rat.py`), which is a bind-all
  address, not a routable one. Always type your real host.
- The C2 "encryption" block is **declarative**. `session_key` is randomised on
  every call, so two clicks give two different keys, and nothing enforces them.
  `key_exchange: RSA-2048` is a label.
- `deep_system_recon` returns your host — do not read it as victim recon.
- `POST /api/rat/launch` binds a listener on this host, so it proves the one-liner
  works locally; it does not prove a remote victim ran it.

---

## 7. Victim-side surface

Lure kit: `storm-web/templates/<name>/index.html` served at `/t/<name>/`, with
`/t/<name>/{post,handler,upload}.php` and `.php`-less equivalents for capture.
Collector JS lives in `storm-web/assets/js/` (`script.js`, `keylogger.js`,
`session-recorder.js`, `mobile-backdoor.js`, `c2_client.js`, `campaign_manager.js`)
and is pulled into the templates.

Flow: victim opens `/t/<name>/` → kit runs → posts to `/receiver`, `/api/fingerprint`,
`/api/keystrokes`, `/api/session/*`, `/api/c2/register` → nothing needs a session →
shows up in the panel and fires a webhook.

---

## 8. The execution layer — the only parts that touch your system

`storm-web/app/exec/` and `app/adapters/`. Everything here is post-P14 and additive;
the frozen legacy contract was never edited.

| Module | Role |
|---|---|
| `exec/runner.py` | run argv, capture exit/stdout/stderr/duration, timeout |
| `exec/verify.py` | prove an effect: `file_exists`, `tcp_open`, `wait_for_connect`, http |
| `exec/strike.py` | generate → launch → verify; `Strike.ok` is the *verified* callback |
| `exec/listener.py` | ephemeral listener that catches the callback |
| `exec/listener_service.py` | named, long-lived listeners (`/api/listeners/*`) |
| `exec/beacon.py` | server-driven jittered beacon schedule + arrival tracker |
| `exec/net.py` | real DNS/reverse/WHOIS/GeoIP + threaded TCP scan |
| `exec/playbook.py` | execute+verify steps with checkpoint/rollback |
| `adapters/` | 48 callable Actions wrapping the 15 modules, no signature edits |
| `targets/` | persistent targets + findings + self-contained HTML evidence report |

Endpoints that actually execute: `POST /api/terminal`, `POST /api/strike/reverse`,
`POST /api/net/scan`, `POST /api/listeners/{start,stop}`,
`POST /api/playbooks/<id>/run`, `POST /api/rat/launch`.

Unattended proof harnesses:

```bash
python3 scripts/acceptance_firepower.py   # scan → strike → VERIFIED → evidence → report
python3 scripts/acceptance_g11.py         # C2 survives restart, listener, beacon
python3 scripts/acceptance_g12.py         # SSE delivers listener/beacon/strike live
python3 scripts/demo_firepower.py         # act → verify, minimal
python3 scripts/demo_strike.py            # generate → launch → verify
```

---

## 9. Data model (29 tables)

`credentials`, `victim_profiles`, `c2_sessions`, `mobile_sessions`,
`mobile_captures`, `mobile_commands`, `mobile_responses`, `tracking_data`,
`geofences`, `browser_exfil`, `network_discoveries`, `campaigns`, `campaign_links`,
`session_hijacks`, `pivot_records`, `playbooks`, `reports`, `saved_lures`,
`evasion_configs`, `threat_intel`, `operator_log`, `login_lockouts`,
`rat_operations`, `rat_shell_sessions`, `rat_persistence`, `targets`,
`target_findings`, `rat_*`.

Schema is created by `database.py:init_database` plus additive migrations in
`app/core/migrations/` (baseline, targets). WAL + hot-path indexes are enabled.
A timestamped backup is the rollback path — `backups/`.

Blank the demo/residual data without dropping schema:

```bash
db=storm-web/storm_breaker.db
cp "$db" "backups/storm_breaker.db.$(date +%Y%m%d-%H%M%S)"
for t in $(sqlite3 "$db" ".tables"); do sqlite3 "$db" "DELETE FROM \"$t\";"; done
sqlite3 "$db" "DELETE FROM sqlite_sequence;"
```

---

## 10. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `502` from the tunnel, `curl localhost:2525` fails | your `ssh -R` died | restart it; use `autossh` |
| Everything in the panel 403s | CSRF gate host mismatch (pre-P16: any browser POST) | fixed in P16; hard-reload |
| `POST /receiver.php → 403` | same CSRF bug | fixed in P16 |
| `GET /api/get_settings` shows 3 keys | you're reading the repo-root Settings.json | fixed in P16 (anchored to storm-web) |
| C2 agent base URL is `http://` on an https page | no ProxyFix | `trust_proxy: true` (default) |
| Telegram silently does nothing | `telegram_config.json` missing / username used as chat id | `POST /api/telegram/test`, use a numeric id |
| `POST /api/mobile/background_data → 500` | string `data` payload | fixed in P16 |
| Beacon agent points at the wrong host | no `X-Forwarded-*` reaching Flask | check the tunnel forwards headers |
| Panel works, saves don't | you're mid-upgrade on an old cookie | re-login |
| Every `/t/<name>/` lure page 500s | `TEMPLATES_DIR` undefined (pre-P17) | fixed in P17; `NameError` in the log confirms it |
| Victim POSTs 401 | `ingest_secret` set and the URL lacks `?k=` | add `?k=<ingest_secret>` to the lure URL (§4b) |
| `429` from a capture loop | rate limiter (default 600/min per IP on ingest) | raise `ingest_rate_per_min` or set it `0` |

Run the gates:

```bash
python3 -m pytest -q               # 302 passed
bash audit/run_audit.sh; echo $?   # PASS, exit 0
```

Serially only — both bind `:2525`.

---

## 11. Security posture checklist before exposing

1. Change the operator password (`config.php` / hashed store). `admin`/`PASS` + a
   public `/api/terminal` = a public root shell.
2. `require_login: true` (now actually enforced).
3. Consider `session_cookie_secure: true` if tunnel-only.
4. Accept that `X-Forwarded-For` spoofing defeats the login lockout on a public URL.
5. `/api/nuke` is unauthenticated in effect only via the gate — it wipes captures
   and in-memory analytics, not the DB.
6. Rotate the tunnel hostname in your head as a credential: `messiah` can be
   grabbed by anyone while your client is down.

---

## 12. Changelog — what P16 changed

| File | Change |
|---|---|
| `app/__init__.py` | `ProxyFix` (x_for/x_proto/x_host/x_port) behind `_trust_proxy()` |
| `app.py` | `require_login` now enforced; `_SETTINGS_PATH` absolute; public POST sink |
| `app/core/hardening.py` | CSRF compares **hostname vs hostname** (was hostname vs host:port → 403'd every browser POST); opt-in Secure cookie |
| `app/blueprints/live.py` | new `POST/GET /api/notify/inbox`, `POST /api/notify/inbox/clear` |
| `app/blueprints/templates.py` | settings read/write anchored to `storm-web/Settings.json` |
| `app/blueprints/rat.py` | `GET /api/rat/shells` + `DELETE .../<id>`; `GET /api/rat/persistence`; persistence rows actually written; **`POST /api/rat/launch`** |
| `app/services/mobile.py` | `add_tracking` tolerates non-dict payloads (was 500) |
| `app/state.py` | `send_notification` reads settings by absolute path |
| `telegram_bot.py` | Settings.json fallback; `chat_id` normalisation |
| `assets/js/rat_ui.js` | Launch & Verify / Saved buttons + handlers |
| `Settings.json` | webhook → local sink; added `public_url`, `trust_proxy`, `session_cookie_secure`, `telegram_enabled` |
| `tests/_frozen/operator_get/GET_api_get_settings.json` | re-frozen (settings shape) |

Regression status after P16: **302 tests pass, audit exit 0, 0 routes lost.**

---

## 12b. Changelog — what P17 changed (the P0 hardening pass)

| Area | Change |
|---|---|
| **Ingest auth** | `app.py:_ingest_key_gate` + `_ingest_key_cookie`. Optional shared secret for victim traffic; planted via cookie so kit JS is untouched. |
| **Rate limiting** | `app.py:_rate_gate` — dependency-free fixed-window limiter, per IP, two buckets (`rate_limit_per_min`, `ingest_rate_per_min`), `/assets/*` exempt. |
| **Upload cap** | `/receiver` added to `UPLOAD_TYPE_LIMITS` (30 MB) — previously uncapped. |
| **Port ranges** | `app/blueprints/net.py:_parse_ports` — `"1-1024"` was documented but unparsed, silently scanning 25 default ports while reporting success. Response gains `requested`. |
| **Beacon agent** | `app/exec/beacon.py:agent_script(..., key)` + `blueprints/beacon.py:_ingest_key` — generated agent carries the secret or its register/poll would 401. |
| **Audit** | New `[5] EFFECTS` section (output assertions, `Origin`-bearing POSTs, key-gate exercise); `/api/terminal` fixed to send `cmd`; victim/uid checks present the key. |
| **CI** | New `.github/workflows/ci.yml` (push/PR: suite + audit). `release.yml` install line corrected. |
| **Deps** | `requirements.txt`, `requirements-dev.txt`, `storm-web/requirements.txt` fully pinned. |
| **Tests** | `_helpers.ingest_suffix()` + wiring in `test_victim.py` / `test_live.py`; two snapshots re-frozen (settings keys, `net/scan` now returns `requested`). |
| **🔴 All lure kits were 500** | `app/state.py` — `TEMPLATES_DIR` was referenced 5× in `blueprints/templates.py` and **defined nowhere**. Every `/t/<name>/` phishing page raised `NameError` → 500. It went unnoticed because the audit and the frozen victim contract only listed the `/t/` *prefix*, never a concrete kit path. Now defined + exported, and covered by a new audit assertion (all 13 kits must render) and two new frozen victim-contract paths. |
| **Settings** | `ingest_secret` (generated), `rate_limit_per_min`, `ingest_rate_per_min`. |

Regression status after P17: **302 tests pass, audit exit 0 (all 9 effect
assertions ok), 0 routes lost.**

---

## 12c. Changelog — what P18 changed (the resident agent + durable outbox)

| Area | Change |
|---|---|
| **Resident agent (P1.1)** | `app/exec/agent.py` — a persistent Python implant that speaks the **existing** `/api/c2/*` contract (register/poll/response), so it appears in the Victim Shells tab with zero new victim endpoints. Magic commands `__sysinfo __pwd __cd __file_get __file_put __persist __sleep __exit`; anything else is shell exec in a tracked CWD. Survives restarts via `~/.storm_agent.json` uid. |
| **Beacon clamp** | Server-driven `next_interval_ms` is clamped in-agent to `[200, 2000]` ms so `/api/agent/exec` returns in seconds instead of waiting out a 15 s beacon. |
| **Agent endpoints** | `GET /api/agent/agent.py` (self-fetch, bakes base+key, `?uid=` pins, `?download=1`), `GET /api/agent/commands`, `GET /api/agent/agents`, `POST /api/agent/spawn` (subprocess + registration poll; **`keep:true`** to leave it running — default terminates after registering), `POST /api/agent/exec` (queue + wait drain). |
| **Durable outbox (P1.3)** | `app/core/outbox.py` + `notification_outbox` table. `state.send_notification` now **records first, delivers second** — a webhook that fails is retried with backoff `(2,5,15,60,300,900)` s up to 6 attempts, then `failed`. Payload+URL snapshotted at record time. |
| **Outbox endpoints** | `GET /api/notifications/outbox`, `GET /api/notifications/stats`, `POST /api/notifications/outbox/<id>/retry`, `/replay`, `/purge`, `/drain` (returns `delivered_now` + `stats`). |
| **Audit** | Effects now 16 assertions: §8 outbox records+delivers, §9 agent spawns→registers→executes→listed. Spawn uses `keep:true` and **cleans up with `__exit`** so no stray agent beacons into later test runs. |
| **SSE test** | `test_sse_stream_delivers_a_beacon_event` now matches the event its own poll produced instead of the first line off the bus — foreign beacons no longer win the race. |
| **Live listener shells (P1.2)** | `interactive:true` listeners keep the catch alive. New endpoints `GET /api/listeners/sessions`, `POST /api/listeners/send|read|close`. Previously `hold=true` accepted the socket and dropped it — fd leak, no shell. Output is line-buffered: a peer that never sends `\n` shows nothing until it dies. Audit §10 asserts a real command roundtrip. |
| **Evidence integrity (P1.4)** | Reports are now tamper-evident. Every generated report carries `integrity` (sha256 + HMAC-SHA256, key = Settings `evidence_signing_key`, falling back to `ingest_secret`). `GET /api/reports/<id>/verify` re-verifies stored bytes; exported target reports embed a `<!-- EVIDENCE-SIGNATURE ... -->` trailer, checked by `POST /api/targets/report/verify` — a tampered copy fails. Stdlib only, no new deps. Audit §11 asserts generate→verify→tamper→fail. |
| **CSRF double-submit (P19)** | Browser-originated mutating POSTs now additionally need the `storm_csrf` token: login plants a readable cookie, the panel/mobile JS patches `fetch`/`XMLHttpRequest` to echo it as `X-CSRF-Token`, and `hardening.csrf_gate` compares cookie==header (plus session binding). Header-less clients (curl, the test harness) are untouched — `SameSite=Lax` still covers them, and the P16 Origin check still 403s cross-origin form posts. Deploy note: open tabs logged in before the upgrade have no token cookie → 403s until re-login. Audit operator section asserts tokenless→403, with-token→200. |

Regression status after P19: **314 tests pass, audit exit 0 (all 23 effect
assertions ok), 0 routes lost.**---

## 13. Known gaps / backlog

**Closed in P17** (keep the reasoning, it mattered):

- ~~No CI gate~~ → `.github/workflows/ci.yml` runs the suite + audit on every
  push/PR. (`release.yml` only ran on a version tag.)
- ~~Audit validated reachability, not behaviour~~ → section `[5] EFFECTS` asserts
  on computed values, sends a browser-like `Origin`, and exercises the key gate.
- ~~No victim-side authentication~~ → `ingest_secret` (§4b).
- ~~No rate limiting~~ → dependency-free limiter + `/receiver` upload cap (§4c).
- ~~Unpinned dependencies~~ → fully pinned `requirements.txt`, `release.yml` fixed
  to install the runtime lock.
- ~~Lockout keyed on a client-spoofable `X-Forwarded-For` first hop~~ →
  `app.py:_client_ip()` now uses the ProxyFix-corrected rightmost hop, so it
  matches what the trusted proxy actually appended.

**Still open:**

- The lockout is still per-IP, not per-account, so a botnet or a determined
  attacker with many hops can spread attempts. A real fix is per-username
  throttling on top.
- The ingest secret is a single global value shared by every victim and lure —
  no per-campaign scoping, no rotation, no revocation.
- Real crypto (`cryptography`) to replace the hand-rolled AES/XOR and the
  declarative C2 key block.
- No session rotation on privilege change; no CSRF double-submit token (the
  Origin + SameSite=Lax pair is what you have).
- `CSP` still allows `'unsafe-inline'` (legacy panel requirement).
- ~~No outbound retry/backoff for `generic_webhook`; failures are swallowed~~ →
  closed in P18 by the durable outbox (§12c): every notification is recorded
  first, delivered with backoff, replayable from the API.
- No multi-operator / RBAC — one session flag, one `config.php` user.
- Optional LLM hook for the AI Threat tab (feature-flag + offline fallback).
- `/api/terminal` has no PTY — line-at-a-time only.
- C2 is still poll-based; `P15.2` folding SSE in as the operator channel is open.
- V2 panel covers all 30 tabs but several are read-only — default not flipped
  (`P11.31`/`P11.32` open).
- `session_cookie_secure` is opt-in; auto-detecting the scheme would be better.
- Loose files in the repo root that are not part of the app: `sys`,
  `storm-web/sys`, `storm-web/re` (ImageMagick PostScript dumps), and the
  vestigial root `Settings.json`.

---

*Generated from source. Route count 234, tabs 30, domain modules 15, tables 29.*
