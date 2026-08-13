"""Hidden tests for LRU cache — objective, discriminating, anti-gaming.

These tests are NEVER shown to the solver. They verify the actual spec
with exact traces and a performance bound that a naive O(n) implementation
cannot meet.
"""
import random
import time

import pytest


def _mk(capacity=2):
    from lru import LRUCache  # import from workspace root (conftest adds path)
    return LRUCache(capacity)


def test_basic_put_get():
    c = _mk(2)
    c.put(1, 1)
    c.put(2, 2)
    assert c.get(1) == 1
    assert c.get(2) == 2


def test_missing_key_returns_minus_one():
    c = _mk(2)
    assert c.get(99) == -1
    c.put(1, 1)
    assert c.get(2) == -1


def test_capacity_one_evicts():
    c = _mk(1)
    c.put(1, 10)
    c.put(2, 20)
    assert c.get(1) == -1
    assert c.get(2) == 20


def test_update_existing_key_no_eviction():
    c = _mk(2)
    c.put(1, 1)
    c.put(2, 2)
    c.put(1, 100)  # update, not insert
    assert c.get(1) == 100
    assert c.get(2) == 2  # must still be present


def test_get_refreshes_recency():
    c = _mk(2)
    c.put(1, 1)
    c.put(2, 2)
    assert c.get(1) == 1    # 1 is now MRU
    c.put(3, 3)             # evicts 2 (LRU), not 1
    assert c.get(2) == -1
    assert c.get(1) == 1
    assert c.get(3) == 3


def test_eviction_order_multi():
    c = _mk(3)
    c.put(1, 1); c.put(2, 2); c.put(3, 3)
    c.put(4, 4)  # evict 1
    assert c.get(1) == -1
    assert c.get(2) == 2
    assert c.get(3) == 3
    assert c.get(4) == 4


def test_update_moves_to_mru():
    c = _mk(3)
    c.put(1, 1); c.put(2, 2); c.put(3, 3)
    c.put(1, 11)   # 1 becomes MRU
    c.put(4, 4)    # evicts 2
    assert c.get(2) == -1
    assert c.get(1) == 11
    assert c.get(3) == 3
    assert c.get(4) == 4


class _RefLRU:
    """Independent reference implementation used to generate traces."""
    def __init__(self, capacity):
        self.cap = capacity
        self.order = []  # LRU -> MRU
        self.map = {}

    def get(self, key):
        if key not in self.map:
            return -1
        self.order.remove(key)
        self.order.append(key)
        return self.map[key]

    def put(self, key, value):
        if key in self.map:
            self.map[key] = value
            self.order.remove(key)
            self.order.append(key)
            return
        if len(self.map) >= self.cap:
            evict = self.order.pop(0)
            del self.map[evict]
        self.map[key] = value
        self.order.append(key)


def test_random_trace_matches_reference():
    """1000 random ops vs an independent reference implementation."""
    rng = random.Random(12345)
    c = _mk(capacity=4)
    ref = _RefLRU(4)
    for _ in range(1000):
        key = rng.randint(0, 9)
        if rng.random() < 0.6:
            v = rng.randint(0, 1000)
            c.put(key, v)
            ref.put(key, v)
        else:
            assert c.get(key) == ref.get(key), f"divergence on get({key})"


def test_performance_100k_operations():
    """100k mixed ops must complete quickly: linear scan will fail this."""
    c = _mk(capacity=64)
    start = time.perf_counter()
    for i in range(100_000):
        c.put(i % 97, i)
        c.get((i * 7) % 97)
    elapsed = time.perf_counter() - start
    assert elapsed < 5.0, f"too slow: {elapsed:.2f}s for 100k ops (O(n) scan?)"
