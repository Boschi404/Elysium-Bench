"""Hidden tests: token bucket — exact refill math + real concurrency stress."""
import threading
import time

import pytest

from bucket import TokenBucket


def test_initial_capacity_available():
    b = TokenBucket(capacity=10, refill_rate=2)
    assert b.available(now=0.0) == 10


def test_acquire_consumes():
    b = TokenBucket(capacity=10, refill_rate=2)
    assert b.try_acquire(8, now=0.0) is True
    assert b.available(now=0.0) == 2.0


def test_acquire_more_than_available_fails_without_partial():
    b = TokenBucket(capacity=10, refill_rate=2)
    b.try_acquire(8, now=0.0)
    assert b.try_acquire(5, now=0.0) is False
    assert b.available(now=0.0) == 2.0  # nothing consumed on failure


def test_continuous_refill_exact():
    b = TokenBucket(capacity=10, refill_rate=2)
    b.try_acquire(10, now=0.0)          # empty at t=0
    assert b.available(now=0.0) == 0.0
    assert b.available(now=3.0) == 6.0  # 3s * 2 tok/s
    assert b.available(now=4.5) == 9.0  # 4.5s * 2 tok/s
    assert b.available(now=100.0) == 10.0  # capped at capacity


def test_refill_cap_never_exceeds_capacity():
    b = TokenBucket(capacity=5, refill_rate=10)
    assert b.available(now=1000.0) == 5.0


def test_partial_refill_then_acquire():
    b = TokenBucket(capacity=10, refill_rate=2)
    b.try_acquire(10, now=0.0)
    assert b.try_acquire(1, now=1.0) is True   # 2 tokens refilled
    assert b.available(now=1.0) == 1.0


def test_acquire_zero_and_negative():
    b = TokenBucket(capacity=10, refill_rate=2)
    assert b.try_acquire(0, now=0.0) is True
    assert b.try_acquire(0.0, now=0.0) is True


def test_constructor_validation():
    with pytest.raises(ValueError):
        TokenBucket(capacity=0, refill_rate=1)
    with pytest.raises(ValueError):
        TokenBucket(capacity=1, refill_rate=0)
    with pytest.raises(ValueError):
        TokenBucket(capacity=-1, refill_rate=1)


def test_deterministic_sequence():
    b = TokenBucket(capacity=4, refill_rate=1)
    assert b.try_acquire(2, now=0.0) is True
    assert b.try_acquire(2, now=0.0) is True
    assert b.try_acquire(1, now=0.0) is False
    assert b.try_acquire(1, now=2.0) is True   # 2 refilled, 1 consumed
    assert b.try_acquire(1, now=2.0) is True   # 1 still available
    assert b.available(now=2.0) == 0.0
    assert b.try_acquire(1, now=2.0) is False  # empty again


def test_concurrency_stress_8_threads():
    """8 threads × 2000 acquisitions: no over-grant, no crashes."""
    capacity = 100.0
    rate = 50.0
    b = TokenBucket(capacity=capacity, refill_rate=rate)
    results = []
    lock = threading.Lock()
    start = time.monotonic()

    def worker(tid):
        granted = 0
        for i in range(2000):
            now = time.monotonic()
            if b.try_acquire(1, now=now):
                granted += 1
        with lock:
            results.append((tid, granted, time.monotonic() - start))

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    total_granted = sum(g for _, g, _ in results)
    elapsed = max(e for _, _, e in results)
    # upper bound: capacity + continuous refill over elapsed time
    upper = capacity + rate * elapsed + 1e-6
    assert total_granted <= upper, (
        f"over-granted: {total_granted} > {upper:.1f} "
        f"(capacity {capacity} + refill {rate}/s × {elapsed:.2f}s)")
    assert total_granted > 0
