"""Hidden tests: LFU cache — frequency eviction, LRU tie-break, O(1)."""
import random
import time

import pytest

from lfu import LFUCache


def test_basic_get_put():
    c = LFUCache(2)
    c.put(1, 1)
    c.put(2, 2)
    assert c.get(1) == 1
    assert c.get(2) == 2


def test_missing_key():
    c = LFUCache(2)
    assert c.get(99) == -1


def test_capacity_one():
    c = LFUCache(1)
    c.put(1, 10)
    c.put(2, 20)
    assert c.get(1) == -1
    assert c.get(2) == 20


def test_evict_lowest_frequency():
    c = LFUCache(3)
    c.put(1, 1); c.put(2, 2); c.put(3, 3)
    assert c.get(1) == 1      # freq(1)=2
    assert c.get(1) == 1      # freq(1)=3
    assert c.get(2) == 2      # freq(2)=2
    c.put(4, 4)               # evicts 3 (freq 1)
    assert c.get(3) == -1
    assert c.get(1) == 1 and c.get(2) == 2 and c.get(4) == 4


def test_lru_tiebreak_among_equal_freq():
    c = LFUCache(2)
    c.put(1, 1); c.put(2, 2)
    assert c.get(1) == 1      # 1 touched more recently than 2
    c.put(3, 3)               # both freq 1 → evict LRU = 2
    assert c.get(2) == -1
    assert c.get(1) == 1 and c.get(3) == 3


def test_put_update_increments_freq():
    c = LFUCache(2)
    c.put(1, 1); c.put(2, 2)
    c.put(1, 100)             # update: freq(1)=2, recency refreshed
    c.put(3, 3)               # evict LRU among freq-1 keys: 2 (1 has freq 2)
    assert c.get(1) == 100
    assert c.get(2) == -1
    assert c.get(3) == 3


def test_put_update_refreshes_recency_in_tiebreak():
    c = LFUCache(2)
    c.put(1, 1); c.put(2, 2)
    c.put(1, 10)              # update: freq(1)=2
    c.put(2, 20)              # update: freq(2)=2, and 2 now most recent
    c.put(3, 30)              # both freq 2 → evict LRU = 1
    assert c.get(1) == -1
    assert c.get(2) == 20
    assert c.get(3) == 30


def test_get_increments_freq_even_at_capacity():
    c = LFUCache(2)
    c.put(1, 1); c.put(2, 2)
    c.get(1); c.get(1); c.get(1)   # freq(1)=4
    c.put(3, 3)                    # evicts 2 (freq 1)
    assert c.get(2) == -1
    assert c.get(1) == 1


class _RefLFU:
    """Independent reference implementation (explicitly NOT O(1))."""
    def __init__(self, capacity):
        self.cap = capacity
        self.data = {}   # key -> [value, freq, seq]
        self.seq = 0

    def _touch(self, key):
        self.seq += 1
        self.data[key][2] = self.seq

    def get(self, key):
        if key not in self.data:
            return -1
        self.data[key][1] += 1
        self._touch(key)
        return self.data[key][0]

    def put(self, key, value):
        if key in self.data:
            self.data[key][0] = value
            self.data[key][1] += 1
            self._touch(key)
            return
        if len(self.data) >= self.cap:
            victim = min(self.data, key=lambda k: (self.data[k][1],
                                                   self.data[k][2]))
            del self.data[victim]
        self.seq += 1
        self.data[key] = [value, 1, self.seq]


def test_random_trace_matches_reference():
    rng = random.Random(20240)
    c = LFUCache(capacity=5)
    ref = _RefLFU(5)
    for _ in range(3000):
        key = rng.randint(0, 12)
        if rng.random() < 0.6:
            v = rng.randint(0, 1000)
            c.put(key, v)
            ref.put(key, v)
        else:
            assert c.get(key) == ref.get(key), f"divergence on get({key})"
    # verify full state equality
    for k in range(13):
        assert c.get(k) == ref.get(k), f"state divergence on {k}"


def test_performance_100k_operations():
    c = LFUCache(capacity=64)
    start = time.perf_counter()
    for i in range(100_000):
        c.put(i % 97, i)
        c.get((i * 7) % 97)
    elapsed = time.perf_counter() - start
    assert elapsed < 5.0, f"too slow: {elapsed:.2f}s (O(n) scan?)"


def test_eviction_keeps_recent_high_freq():
    c = LFUCache(3)
    c.put(1, 1); c.put(2, 2); c.put(3, 3)
    c.get(2); c.get(2); c.get(3)   # freq: 2→3, 3→2, 1→1
    c.put(4, 4)                    # evicts 1
    assert c.get(1) == -1
    assert {c.get(k) for k in (2, 3, 4)} == {2, 3, 4}
