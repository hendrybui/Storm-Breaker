#!/usr/bin/env bash
# Storm-Breaker audit wrapper — starts the backend if it isn't running,
# runs the audit harness, and leaves the panel usable afterwards.
#
# Usage:
#   bash audit/run_audit.sh              # audit against http://127.0.0.1:2525
#   bash audit/run_audit.sh <base-url>   # audit against another base URL
#   bash audit/run_audit.sh --stop       # stop the backend, run nothing
#
# Exit code = audit exit code (1 also means "could not start backend").
set -u
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PID_FILE=/tmp/sb_audit_server.pid
LOG_FILE=/tmp/sb_audit_server.log
BASE_URL="http://127.0.0.1:2525"

server_up() { ss -tln 2>/dev/null | grep -q ':2525'; }

stop_server() {
    if [ -f "$PID_FILE" ]; then
        kill "$(cat "$PID_FILE")" 2>/dev/null
        rm -f "$PID_FILE"
    fi
    fuser -k 2525/tcp 2>/dev/null
    sleep 1
    server_up && echo "WARN: something still listens on 2525"
}

if [ "${1:-}" = "--stop" ]; then
    stop_server
    echo "backend stopped"
    exit 0
fi

[ "${1:-}" != "" ] && BASE_URL="$1"

cd "$APP_DIR"

if ! server_up; then
    echo "[*] starting backend (log: $LOG_FILE) ..."
    nohup python3 storm-web/app.py > "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"
    for _ in $(seq 1 30); do
        grep -aq 'Running on' "$LOG_FILE" 2>/dev/null && break
        server_up && break
        sleep 0.5
    done
    if ! server_up; then
        echo "ERROR: backend failed to start — tail of $LOG_FILE:" >&2
        tail -20 "$LOG_FILE" >&2
        exit 1
    fi
    echo "[*] backend up on :2525"
else
    echo "[*] backend already running on :2525"
fi

python3 audit/audit_storm_breaker.py --url "$BASE_URL"
AUDIT_EXIT=$?
echo "audit exit=$AUDIT_EXIT   (backend left running; 'bash audit/run_audit.sh --stop' stops it)"
exit $AUDIT_EXIT
