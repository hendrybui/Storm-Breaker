"""Unit tests for ``app.core.jobs`` (P6.1/P6.2 — background job queue)."""
import time

import pytest

from app.core.jobs import JobQueue, get_queue, new_job_id, reset_queue


def wait_for_state(q, job_id, states, timeout=5.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        st = q.status(job_id)
        if st and st['state'] in states:
            return st
        time.sleep(0.01)
    raise AssertionError('job %s did not reach %s (last=%s)' %
                         (job_id, states, q.status(job_id)))


def test_job_id_format():
    jid = new_job_id()
    assert jid.startswith('job_')
    assert new_job_id() != jid


def test_enqueue_runs_and_records_result():
    q = JobQueue()
    q.start_worker()
    try:
        jid = q.enqueue(lambda a, b: a + b, 2, b=3)
        st = wait_for_state(q, jid, {'done'})
        assert st['result'] == 5
        assert st['state'] == 'done'
        assert st['enqueued_at'] is not None
        assert st['started_at'] is not None
        assert st['finished_at'] is not None
    finally:
        q.stop_worker()


def test_error_is_captured_not_raised():
    q = JobQueue()
    q.start_worker()
    try:
        def boom():
            raise ValueError('nope')

        jid = q.enqueue(boom)
        st = wait_for_state(q, jid, {'error'})
        assert st['state'] == 'error'
        assert 'nope' in st['error']
        assert st['result'] is None
    finally:
        q.stop_worker()


def test_status_unknown_job_is_none():
    q = JobQueue()
    assert q.status('nope') is None


def test_queued_before_worker_starts():
    q = JobQueue()  # no worker yet
    jid = q.enqueue(lambda: 'x')
    assert q.status(jid)['state'] == 'queued'
    q.start_worker()
    try:
        wait_for_state(q, jid, {'done'})
    finally:
        q.stop_worker()


def test_fifo_order():
    q = JobQueue()
    order = []

    def add(n):
        order.append(n)

    q.start_worker()
    try:
        for n in range(5):
            q.enqueue(add, n)
        deadline = time.time() + 5
        while time.time() < deadline and len(order) < 5:
            time.sleep(0.01)
        assert order == [0, 1, 2, 3, 4]
    finally:
        q.stop_worker()


def test_graceful_stop_finishes_running_loop():
    q = JobQueue()
    q.start_worker()
    assert q.running
    q.stop_worker()
    assert not q.running
    # stopping twice must be safe
    q.stop_worker()


def test_get_queue_singleton_running():
    reset_queue()
    q1 = get_queue()
    q2 = get_queue()
    assert q1 is q2
    assert q1.running
    reset_queue()
