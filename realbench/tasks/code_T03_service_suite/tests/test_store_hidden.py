"""Hidden tests: store module — capacity/eviction semantics are subtle."""
import pytest

from store import EventStore


def test_insert_and_count():
    s = EventStore(10)
    assert s.insert({"ts": 1}) is True
    assert s.insert({"ts": 2}) is True
    assert s.count() == 2


def test_query_since_sorted():
    s = EventStore(10)
    for ts in [5, 1, 3, 2, 4]:
        s.insert({"ts": ts})
    assert [e["ts"] for e in s.query_since(3)] == [3, 4, 5]
    assert [e["ts"] for e in s.query_since(0)] == [1, 2, 3, 4, 5]


def test_evicts_oldest_when_full():
    s = EventStore(3)
    s.insert({"ts": 10})
    s.insert({"ts": 20})
    s.insert({"ts": 30})
    assert s.insert({"ts": 40}) is True  # evicts ts=10
    assert [e["ts"] for e in s.query_since(0)] == [20, 30, 40]


def test_rejects_when_not_newer_than_all():
    """A new event must NOT evict an event with ts >= its own ts."""
    s = EventStore(2)
    s.insert({"ts": 10})
    s.insert({"ts": 20})
    assert s.insert({"ts": 15}) is False  # 15 would evict 10, but 20 >= 15
    assert s.count() == 2
    assert [e["ts"] for e in s.query_since(0)] == [10, 20]


def test_accepts_equal_ts_when_room():
    s = EventStore(3)
    s.insert({"ts": 5})
    s.insert({"ts": 5})
    assert s.count() == 2
    assert len(s.query_since(5)) == 2


def test_stable_order_for_equal_ts():
    s = EventStore(4)
    s.insert({"ts": 1, "seq": "a"})
    s.insert({"ts": 1, "seq": "b"})
    s.insert({"ts": 1, "seq": "c"})
    assert [e["seq"] for e in s.query_since(1)] == ["a", "b", "c"]
