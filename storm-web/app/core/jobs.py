"""Background job queue for Storm-Breaker (HANDOFF plan section P6).

``JobQueue`` is a small, dependency-free FIFO with one daemon worker
thread and per-job status tracking.  It exists so work that used to run
inline on the request path (webhook/telegram notifications, credential
scans, report generation) can move off it (P6.3/P6.4) without touching
the frozen HTTP contract: the legacy endpoints keep their exact
responses, and new async variants are additive only (P6.5).

Design notes:
- Jobs are plain callables; failures are captured per job (state
  ``error``) and never kill the worker.
- ``stop_worker()`` is graceful: the worker drains pending items it has
  already dequeued, then exits; queued-but-not-started jobs stay queued
  and are reported as such by :meth:`status`.
- The module-level default queue auto-starts its worker on first use
  (:func:`get_queue`), mirroring the process-wide primitives in
  ``app.core.state`` / ``app.core.db``.
"""
from __future__ import annotations

import itertools
import queue as _queue
import threading
import time
from typing import Any, Callable, Dict, Optional

_counter = itertools.count(1)
_counter_lock = threading.Lock()


def new_job_id() -> str:
    """Generate a unique, human-sortable job id."""
    with _counter_lock:
        return 'job_%d_%d' % (int(time.time()), next(_counter))


class JobQueue:
    """FIFO job queue with a single worker thread + status registry."""

    def __init__(self, worker_timeout: float = 0.2) -> None:
        self._q: '_queue.Queue' = _queue.Queue()
        self._lock = threading.Lock()
        self._jobs: Dict[str, dict] = {}
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._worker_timeout = worker_timeout

    # -- public API -----------------------------------------------------
    def enqueue(self, func: Callable, *args: Any,
                job_id: Optional[str] = None, **kwargs: Any) -> str:
        """Queue ``func(*args, **kwargs)``; returns the job id."""
        if job_id is None:
            job_id = new_job_id()
        rec = {'id': job_id, 'state': 'queued', 'result': None,
               'error': None, 'enqueued_at': time.time(),
               'started_at': None, 'finished_at': None}
        with self._lock:
            self._jobs[job_id] = rec
        self._q.put((job_id, func, args, kwargs))
        return job_id

    def status(self, job_id: str) -> Optional[dict]:
        """Snapshot of one job's record (``None`` when unknown)."""
        with self._lock:
            rec = self._jobs.get(job_id)
            return dict(rec) if rec is not None else None

    def start_worker(self) -> None:
        """Start the daemon worker (idempotent)."""
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run,
                                        name='storm-jobs', daemon=True)
        self._thread.start()

    def stop_worker(self, wait: bool = False) -> None:
        """Signal the worker to exit after its current job (idempotent)."""
        self._stop.set()
        t = self._thread
        if wait and t is not None and t is not threading.current_thread():
            t.join(timeout=5)
        self._thread = None

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    # -- worker ----------------------------------------------------------
    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                job_id, func, args, kwargs = \
                    self._q.get(timeout=self._worker_timeout)
            except _queue.Empty:
                continue
            with self._lock:
                rec = self._jobs.get(job_id)
                if rec is not None:
                    rec['state'] = 'running'
                    rec['started_at'] = time.time()
            try:
                result = func(*args, **kwargs)
                with self._lock:
                    rec = self._jobs.get(job_id)
                    if rec is not None:
                        rec['state'] = 'done'
                        rec['result'] = result
                        rec['finished_at'] = time.time()
            except Exception as e:  # noqa: BLE001 -- jobs must not kill worker
                with self._lock:
                    rec = self._jobs.get(job_id)
                    if rec is not None:
                        rec['state'] = 'error'
                        rec['error'] = '%s: %s' % (type(e).__name__, e)
                        rec['finished_at'] = time.time()


# --- module-level default queue ------------------------------------------------
_default: Optional[JobQueue] = None
_default_lock = threading.Lock()


def get_queue() -> JobQueue:
    """Process-wide job queue; worker auto-starts on first use."""
    global _default
    if _default is None:
        with _default_lock:
            if _default is None:
                q = JobQueue()
                q.start_worker()
                _default = q
    return _default


def reset_queue() -> None:
    """Stop + drop the default queue (used by tests)."""
    global _default
    with _default_lock:
        if _default is not None:
            _default.stop_worker()
        _default = None


__all__ = ["JobQueue", "get_queue", "reset_queue", "new_job_id"]
