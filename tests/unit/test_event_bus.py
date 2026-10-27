"""Tests for the realtime event bus (P10)."""
import queue

from app.core.events import EventBus


def test_publish_reaches_subscriber():
    bus = EventBus()
    sid, q = bus.subscribe()
    bus.publish("beacon", uid="u1", expected_ms=1000)
    event = q.get_nowait()
    assert event["kind"] == "beacon" and event["uid"] == "u1"
    bus.unsubscribe(sid)
    assert bus.subscribers() == 0


def test_fanout_to_multiple_subscribers():
    bus = EventBus()
    _, q1 = bus.subscribe()
    _, q2 = bus.subscribe()
    bus.publish("strike", ok=True)
    assert q1.get_nowait()["kind"] == "strike"
    assert q2.get_nowait()["kind"] == "strike"


def test_recent_is_bounded_and_filterable():
    bus = EventBus(keep=5)
    for i in range(20):
        bus.publish("beacon" if i % 2 else "listener", i=i)
    assert len(bus.recent(100)) == 5
    assert all(e["kind"] == "beacon" for e in bus.recent(100, kinds=["beacon"]))


def test_slow_subscriber_drops_instead_of_blocking():
    bus = EventBus()
    _, q = bus.subscribe()
    for i in range(300):          # MAX_QUEUE is 200
        bus.publish("beacon", i=i)
    assert q.qsize() <= 200


def test_unsubscribe_stops_delivery():
    bus = EventBus()
    sid, q = bus.subscribe()
    bus.unsubscribe(sid)
    bus.publish("beacon", uid="x")
    with __import__("pytest").raises(queue.Empty):
        q.get_nowait()
