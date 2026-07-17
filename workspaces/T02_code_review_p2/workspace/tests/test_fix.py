"""
Tests for T02_code_review — Memory Leak Pattern.

Verifies:
  - Leaky code exhibits the memory-accumulation behaviour
  - Fixed solution (LRU cache + weak references) bounds memory and
    does not prevent garbage collection of subscriber objects
"""

import gc
import sys
import time
import weakref
from pathlib import Path

import pytest

# Ensure workspace is on the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from leaky_code import (
    _cache as leaky_cache,
    cache_size as leaky_cache_size,
    get_data as leaky_get,
    EventEmitter as LeakyEmitter,
    DataSubscriber as LeakySubscriber,
)

from solution import (
    LRUCache,
    cache_size as fixed_cache_size,
    get_data as fixed_get,
    WeakEventEmitter,
    DataSubscriber as FixedSubscriber,
    DisposableSubscriber,
)


# ══════════════════════════════════════════════════════════════════════
#  Cache Leak Tests
# ══════════════════════════════════════════════════════════════════════

def test_original_cache_grows_unbounded():
    """The original leaky cache grows to the number of unique keys."""
    size_before = leaky_cache_size()
    n = 500
    for i in range(n):
        leaky_get(f"grow_key_{i}")
    size_after = leaky_cache_size()
    assert size_after - size_before == n, (
        f"Expected +{n} entries, got +{size_after - size_before}"
    )


def test_fixed_cache_bounded():
    """Fixed LRU cache never exceeds maxsize."""
    fixed_get("seed")  # warm-up
    size_before = fixed_cache_size()
    n = 1000
    for i in range(n):
        fixed_get(f"bound_key_{i}")
    size_after = fixed_cache_size()
    # maxsize=128, so after 1000 unique keys it should be bounded at ~128
    # (may start from 0 after warm-up, grows to maxsize)
    assert size_after <= 135, (
        f"Cache exceeded maxsize: {size_after}"
    )
    # Verify at least one entry was evicted (confirm LRU eviction active)
    assert size_after < n, (
        f"Cache grew unbounded: {size_after} >= {n}"
    )


def test_lru_cache_eviction_order():
    """LRUCache evicts the least-recently-used entry first."""
    c = LRUCache(maxsize=3)
    c.put("a", 1)
    c.put("b", 2)
    c.put("c", 3)

    # Touch 'a' to make it MRU
    assert c.get("a") == 1

    # Insert 'd' — should evict 'b' (oldest now)
    c.put("d", 4)

    assert c.get("a") == 1, "MRU entry 'a' should survive"
    assert c.get("b") is None, "LRU entry 'b' should be evicted"
    assert c.get("c") == 3
    assert c.get("d") == 4


def test_lru_cache_ttl():
    """LRUCache with TTL expires stale entries."""
    c = LRUCache(maxsize=10, ttl=0.05)  # 50 ms TTL
    c.put("x", 42)
    assert c.get("x") == 42
    time.sleep(0.06)
    assert c.get("x") is None, "TTL entry should expire"


def test_cache_stress():
    """Fixed cache handles many lookups without unbounded growth."""
    c = LRUCache(maxsize=32)
    for i in range(500):
        c.put(f"k{i}", i)
    for i in range(500):
        v = c.get(f"k{i}")
        # Only the last 32 should still be present
        if i >= 500 - 32:
            assert v is not None, f"key k{i} should be cached"
        # Earlier ones may or may not survive — acceptable
    assert len(c) <= 32


# ══════════════════════════════════════════════════════════════════════
#  Event Listener Leak Tests
# ══════════════════════════════════════════════════════════════════════

def test_leaky_listener_prevents_gc():
    """
    The original leaky subscriber cannot be GC'd because the emitter
    holds strong references to the bound methods.
    """
    emitter = LeakyEmitter()

    def create_and_drop():
        sub = LeakySubscriber("victim", emitter)
        wr = weakref.ref(sub)
        # Return the weakref; drop the subscriber
        return wr

    wr = create_and_drop()
    gc.collect()
    gc.collect()  # double collect for generational GC

    # The subscriber should NOT be collected because emitter holds it
    assert wr() is not None, (
        "Leaky subscriber was GC'd — leak scenario not reproduced"
    )


def test_fixed_listener_allows_gc():
    """
    With weak references, the fixed subscriber IS collected when
    all external references are dropped.
    """
    emitter = WeakEventEmitter()

    def create_and_drop():
        sub = FixedSubscriber("free", emitter)
        wr = weakref.ref(sub)
        return wr

    wr = create_and_drop()
    gc.collect()
    gc.collect()

    assert wr() is None, (
        "Fixed subscriber should be GC'd but still alive"
    )


def test_disposable_listener_cleanup():
    """DisposableSubscriber's explicit dispose() deregisters listeners."""
    emitter = WeakEventEmitter()
    sub = DisposableSubscriber("disp", emitter)

    assert emitter.listener_count("data") == 1
    assert emitter.listener_count("status") == 1

    sub.dispose()

    # Emitter may not immediately prune if refs are weak but still alive;
    # force GC and trigger emit to prune
    gc.collect()
    emitter.emit("data", "ping")

    assert emitter.listener_count("data") == 0, (
        "Listener not cleaned up after dispose"
    )
    assert emitter.listener_count("status") == 0


def test_emit_after_subscriber_gc():
    """
    After the fixed subscriber is GC'd, emitting 'data' should not
    call the dead handler (no crash, no phantom output).
    """
    captured = []
    emitter = WeakEventEmitter()

    class SpySubscriber:
        def on_data(self, data):
            captured.append(data)

    sub = SpySubscriber()
    emitter.on("data", sub.on_data)
    wr = weakref.ref(sub)

    # Drop the subscriber and collect
    del sub
    gc.collect()

    # Emit should silently skip the dead weakref
    emitter.emit("data", "hello")

    assert wr() is None, "Subscriber should be GC'd"
    assert len(captured) == 0, (
        "Dead handler should not receive events"
    )


# ══════════════════════════════════════════════════════════════════════
#  Edge Cases
# ══════════════════════════════════════════════════════════════════════

def test_lru_cache_empty_get():
    """Getting from an empty cache returns None."""
    c = LRUCache(maxsize=10)
    assert c.get("nonexistent") is None


def test_lru_cache_zero_maxsize():
    """Cache with maxsize=0 stores nothing."""
    c = LRUCache(maxsize=0)
    c.put("x", 1)
    assert c.get("x") is None


def test_lru_cache_update_existing():
    """Updating an existing key refreshes its position."""
    c = LRUCache(maxsize=3)
    c.put("a", 1)
    c.put("b", 2)
    c.put("c", 3)
    # Update 'a' — should make it MRU
    c.put("a", 99)
    c.put("d", 4)
    assert c.get("a") == 99, "Updated value should survive"
    assert c.get("b") is None, "'b' should be evicted (oldest untouched)"


def test_lru_cache_clear():
    """Clearing the cache empties all entries."""
    c = LRUCache(maxsize=10)
    c.put("a", 1)
    c.put("b", 2)
    c.clear()
    assert c.get("a") is None
    assert c.get("b") is None
    assert len(c) == 0


def test_weak_emitter_multiple_same_event():
    """Multiple callbacks on the same event all fire."""
    emitter = WeakEventEmitter()
    results = []

    def cb1(x):
        results.append(f"a{x}")

    def cb2(x):
        results.append(f"b{x}")

    emitter.on("evt", cb1)
    emitter.on("evt", cb2)
    emitter.emit("evt", 42)

    assert "a42" in results
    assert "b42" in results


def test_weak_emitter_off():
    """Explicit off() removes a specific listener."""
    emitter = WeakEventEmitter()
    results = []

    def cb1(x):
        results.append(f"a{x}")

    def cb2(x):
        results.append(f"b{x}")

    emitter.on("evt", cb1)
    emitter.on("evt", cb2)
    emitter.off("evt", cb1)
    emitter.emit("evt", 99)

    assert results == ["b99"], f"Got {results}"
