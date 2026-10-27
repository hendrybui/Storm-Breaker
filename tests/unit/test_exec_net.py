"""Effect-asserting tests for real network primitives (P14.7/P14.8)."""
import socket

from app.exec import net


def _listener(port=0):
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("127.0.0.1", port))
    s.listen(5)
    return s, s.getsockname()[1]


def _closed_port():
    s, p = _listener()
    s.close()
    return p


def test_resolve_localhost():
    assert "127.0.0.1" in net.resolve("localhost")


def test_resolve_bad_host_is_empty():
    assert net.resolve("no-such-host.invalid") == []


def test_port_scan_finds_a_real_open_port():
    srv, port = _listener()
    try:
        res = net.port_scan("127.0.0.1", [port], timeout=0.5)
        assert res["open"] == [port]
        assert res["scanned"] == 1
    finally:
        srv.close()


def test_port_scan_reports_closed_port_absent():
    port = _closed_port()
    res = net.port_scan("127.0.0.1", [port], timeout=0.3)
    assert res["open"] == []


def test_port_scan_mixed(tmp_path):
    srv, open_port = _listener()
    closed = _closed_port()
    try:
        res = net.port_scan("127.0.0.1", [open_port, closed], timeout=0.3)
        assert open_port in res["open"] and closed not in res["open"]
    finally:
        srv.close()


def test_reverse_dns_shape():
    name = net.reverse_dns("127.0.0.1")
    assert name is None or isinstance(name, str)


def test_whois_returns_dict():
    res = net.whois("example.com", timeout=6)
    assert res["domain"] == "example.com"
    assert "raw" in res and isinstance(res["raw"], str)


def test_geoip_returns_dict():
    res = net.geoip("8.8.8.8", timeout=6)
    assert isinstance(res, dict)
