"""Effect-asserting tests for ``app.exec.verify`` (P14.2).

Real sockets and a real HTTP server -- the checks must observe reality.
"""
import http.server
import socket
import threading
import time

from app.exec.verify import (CheckResult, all_ok, file_exists, http_probe,
                             tcp_open, wait_for_connect)


def _free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def _serve_tcp(port: int):
    srv = socket.socket()
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", port))
    srv.listen(5)
    stop = threading.Event()

    def loop():
        srv.settimeout(0.2)
        while not stop.is_set():
            try:
                conn, _ = srv.accept()
                conn.close()
            except socket.timeout:
                pass
            except OSError:
                break

    threading.Thread(target=loop, daemon=True).start()
    return srv, stop


class _Ok(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, *a):
        pass


def test_tcp_open_true():
    port = _free_port()
    srv, stop = _serve_tcp(port)
    try:
        r = tcp_open("127.0.0.1", port)
        assert isinstance(r, CheckResult)
        assert r.ok is True
        assert "connected" in r.detail
    finally:
        stop.set()
        srv.close()


def test_tcp_open_false_on_closed_port():
    r = tcp_open("127.0.0.1", _free_port(), timeout=0.5)
    assert r.ok is False
    assert r.detail


def test_wait_for_connect_succeeds_when_listener_appears_late():
    port = _free_port()
    box = {}

    def delayed():
        time.sleep(0.4)
        s = socket.socket()
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("127.0.0.1", port))
        s.listen(1)
        box["s"] = s
        threading.Thread(target=lambda: s.accept(), daemon=True).start()

    threading.Thread(target=delayed, daemon=True).start()
    try:
        r = wait_for_connect("127.0.0.1", port, timeout=5.0, interval=0.1)
        assert r.ok is True
    finally:
        box.get("s") and box["s"].close()


def test_wait_for_connect_times_out():
    r = wait_for_connect("127.0.0.1", _free_port(), timeout=0.5, interval=0.1)
    assert r.ok is False


def test_http_probe_matches_expected_status():
    port = _free_port()
    srv = http.server.HTTPServer(("127.0.0.1", port), _Ok)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        r = http_probe("http://127.0.0.1:%d/" % port, expect_status=200)
        assert r.ok is True
        assert "HTTP 200" in r.detail
    finally:
        srv.shutdown()
        srv.server_close()


def test_http_probe_connection_refused():
    r = http_probe("http://127.0.0.1:%d/" % _free_port(), timeout=0.5)
    assert r.ok is False


def test_file_exists_and_min_bytes(tmp_path):
    p = tmp_path / "artifact.txt"
    p.write_text("hi")
    assert file_exists(str(p)).ok is True
    assert file_exists(str(p), min_bytes=100).ok is False
    assert file_exists(str(tmp_path / "missing")).ok is False


def test_all_ok_is_conjunctive():
    good = tcp_open("127.0.0.1", 0, timeout=0.1)  # port 0 -> refused
    assert all_ok([CheckResult("a", True, "", 0.0),
                   CheckResult("b", True, "", 0.0)]) is True
    assert all_ok([CheckResult("a", True, "", 0.0), good]) is False
