"""Unit tests for ``app.core.state`` (P5.1/P5.2 — StateStore + MemoryStore).

These lock the MemoryStore semantics that P5.3 blueprint rewiring must
preserve: FIFO command queues, drain-empties responses, pop-on-read file
lists/downloads, analytics trimming at 500, and lock-guarded counters.
"""
import threading

import pytest

from app.core.state import MemoryStore, StateStore


@pytest.fixture()
def store():
    return MemoryStore()


# -- interface ---------------------------------------------------------------
def test_interface_methods_raise_not_implemented():
    s = StateStore()
    with pytest.raises(NotImplementedError):
        s.close()


# -- C2 ------------------------------------------------------------------------
class TestC2:
    def test_session_set_get(self, store):
        store.c2_session_set('u1', {'os': 'win'}, '10.0.0.1')
        got = store.c2_session_get('u1')
        assert got['info'] == {'os': 'win'}
        assert got['ip'] == '10.0.0.1'
        assert 'last_seen' in got

    def test_session_get_missing_is_none(self, store):
        assert store.c2_session_get('ghost') is None

    def test_update_last_seen_ignores_unknown_uid(self, store):
        store.c2_session_update_last_seen('ghost')  # must not raise/create
        assert store.c2_session_get('ghost') is None

    def test_all_sessions_returns_snapshot(self, store):
        store.c2_session_set('u1', {}, '1.1.1.1')
        snap = store.c2_all_sessions()
        assert 'u1' in snap
        snap['u2'] = {}  # mutating the snapshot must not leak into the store
        assert store.c2_session_get('u2') is None

    def test_commands_fifo(self, store):
        store.c2_command_enqueue('u1', 'whoami')
        store.c2_command_enqueue('u1', 'ls')
        assert store.c2_command_dequeue('u1') == 'whoami'
        assert store.c2_command_dequeue('u1') == 'ls'
        assert store.c2_command_dequeue('u1') is None

    def test_responses_drain_empties(self, store):
        store.c2_response_append('u1', 'out1', 'T1')
        store.c2_response_append('u1', 'out2', 'T2')
        drained = store.c2_response_drain('u1')
        assert drained == [{'timestamp': 'T1', 'output': 'out1'},
                           {'timestamp': 'T2', 'output': 'out2'}]
        assert store.c2_response_drain('u1') == []

    def test_file_list_pop_on_read(self, store):
        store.c2_file_list_set('u1', {'files': ['a']})
        assert store.c2_file_list_drain('u1') == {'files': ['a']}
        assert store.c2_file_list_drain('u1') is None

    def test_download_pop_on_read(self, store):
        store.c2_download_set('u1', {'b64': 'xx'})
        assert store.c2_download_drain('u1') == {'b64': 'xx'}
        assert store.c2_download_drain('u1') is None


# -- Mobile ---------------------------------------------------------------------
class TestMobile:
    def test_session_set_get(self, store):
        store.mobile_session_set('m1', {'model': 'X'}, '2.2.2.2', 'R1')
        got = store.mobile_session_get('m1')
        assert got['info'] == {'model': 'X'}
        assert got['ip'] == '2.2.2.2'
        assert got['registered_at'] == 'R1'
        assert 'last_seen' in got

    def test_all_sessions_snapshot(self, store):
        store.mobile_session_set('m1', {}, '1.1.1.1', 'R')
        assert 'm1' in store.mobile_all_sessions()

    def test_commands_fifo(self, store):
        store.mobile_command_enqueue('m1', 'sms')
        store.mobile_command_enqueue('m1', 'gps')
        assert store.mobile_command_dequeue('m1') == 'sms'
        assert store.mobile_command_dequeue('m1') == 'gps'
        assert store.mobile_command_dequeue('m1') is None

    def test_capture_set_but_get_delegates_to_repository(self, store):
        store.mobile_capture_set('m1', 'screenshot', 'f.jpg', '/images/f.jpg', {})
        assert store.mobile_captures_get('m1') == []

    def test_tracking_roundtrip(self, store):
        assert store.mobile_tracking_get('m1') == []
        store.mobile_tracking_set('m1', {'lat': 1.0})
        assert store.mobile_tracking_get('m1') == [{'lat': 1.0}]


# -- Analytics ---------------------------------------------------------------------
class TestAnalytics:
    def test_event_append_counts(self, store):
        store.analytics_event_append({'type': 'visit', 'ip': '1.1.1.1'})
        snap = store.analytics_get()
        assert snap['total_visits'] == 1
        assert snap['events'][0]['type'] == 'visit'
        assert '1.1.1.1' in snap['ip_addresses']

    def test_events_trimmed_at_500(self, store):
        for i in range(505):
            store.analytics_event_append({'type': 'e%d' % i})
        snap = store.analytics_get()
        assert len(snap['events']) == 500
        assert snap['total_visits'] == 505  # counter keeps full history

    def test_clear(self, store):
        store.analytics_event_append({'type': 'visit', 'ip': '2.2.2.2'})
        store.analytics_clear()
        snap = store.analytics_get()
        assert snap['events'] == [] and snap['ip_addresses'] == set()

    def test_set_replaces(self, store):
        store.analytics_set({'total_visits': 42, 'events': [1]})
        assert store.analytics_get()['total_visits'] == 42

    def test_thread_safety_counter(self, store):
        def worker():
            for _ in range(20):
                store.analytics_event_append({'type': 't'})

        threads = [threading.Thread(target=worker) for _ in range(25)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert store.analytics_get()['total_visits'] == 25 * 20


# -- Recon / WebRTC / lockout ------------------------------------------------------------
def test_recon_config_defaults_and_update(store):
    cfg = store.recon_config_get()
    assert cfg['auto_fingerprint'] is True
    assert cfg['auto_credential_scan'] is False
    store.recon_config_update({'auto_credential_scan': True})
    assert store.recon_config_get()['auto_credential_scan'] is True
    assert store.recon_config_get()['auto_webrtc'] is True  # untouched key


def test_webrtc_leak_roundtrip(store):
    assert store.webrtc_leaks_get() == []
    store.webrtc_leak_append({'ip': 'leak'})
    assert store.webrtc_leaks_get() == [{'ip': 'leak'}]


def test_login_fail_lifecycle(store):
    assert store.login_fail_get('3.3.3.3') is None
    store.login_fail_set('3.3.3.3', 2, 12345.0)
    assert store.login_fail_get('3.3.3.3') == (2, 12345.0)
    store.login_fail_pop('3.3.3.3')
    assert store.login_fail_get('3.3.3.3') is None


def test_close_is_noop(store):
    assert store.close() is None

