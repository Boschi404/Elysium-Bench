"""Hidden tests: segment tree — correctness vs brute force + O(log n) scale."""
import random
import time

import pytest

from segtree import SegmentTree


def test_simple_sums():
    st = SegmentTree([1, 2, 3, 4, 5])
    assert st.range_sum(0, 4) == 15
    assert st.range_sum(0, 0) == 1
    assert st.range_sum(2, 4) == 12
    assert st.range_sum(1, 3) == 9


def test_simple_mins():
    st = SegmentTree([5, 3, 8, 1, 9, 2])
    assert st.range_min(0, 5) == 1
    assert st.range_min(0, 2) == 3
    assert st.range_min(3, 5) == 1
    assert st.range_min(4, 4) == 9


def test_negatives():
    st = SegmentTree([-5, 3, -8, 1, -9, 2])
    assert st.range_sum(0, 5) == -16
    assert st.range_min(0, 5) == -9
    assert st.range_min(0, 2) == -8


def test_update_propagates():
    st = SegmentTree([1, 2, 3, 4, 5])
    st.update(2, 100)
    assert st.range_sum(0, 4) == 112
    assert st.range_sum(2, 2) == 100
    st.update(0, -10)
    assert st.range_min(0, 4) == -10
    assert st.range_sum(0, 4) == 101


def test_single_element():
    st = SegmentTree([42])
    assert st.range_sum(0, 0) == 42
    assert st.range_min(0, 0) == 42
    st.update(0, 7)
    assert st.range_sum(0, 0) == 7


def test_empty_list():
    st = SegmentTree([])
    with pytest.raises(IndexError):
        st.range_sum(0, 0)


def test_index_rules():
    st = SegmentTree([1, 2, 3])
    with pytest.raises(ValueError):
        st.range_sum(2, 1)
    with pytest.raises(IndexError):
        st.range_sum(0, 3)
    with pytest.raises(IndexError):
        st.range_min(-1, 1)
    with pytest.raises(IndexError):
        st.update(3, 9)
    with pytest.raises(IndexError):
        st.update(-1, 9)


def test_random_vs_bruteforce():
    rng = random.Random(31337)
    arr = [rng.randint(-100, 100) for _ in range(200)]
    st = SegmentTree(arr)
    for _ in range(1000):
        op = rng.random()
        if op < 0.55:
            l = rng.randint(0, 199)
            r = rng.randint(l, 199)
            assert st.range_sum(l, r) == sum(arr[l:r + 1])
            assert st.range_min(l, r) == min(arr[l:r + 1])
        else:
            i = rng.randint(0, 199)
            v = rng.randint(-1000, 1000)
            st.update(i, v)
            arr[i] = v


def test_perf_1e6_build_1e5_queries():
    rng = random.Random(11)
    n = 1_000_000
    values = [rng.randint(-1000, 1000) for _ in range(n)]
    start = time.perf_counter()
    st = SegmentTree(values)
    build_elapsed = time.perf_counter() - start

    start = time.perf_counter()
    checksum = 0
    for _ in range(100_000):
        l = rng.randint(0, n - 1)
        r = rng.randint(l, n - 1)
        if rng.random() < 0.5:
            checksum += st.range_sum(l, r)
        else:
            checksum += st.range_min(l, r)
    query_elapsed = time.perf_counter() - start
    # sanity: checksum changes with data (not a constant stub)
    assert checksum != 0
    assert build_elapsed < 10.0, f"build too slow: {build_elapsed:.2f}s"
    assert query_elapsed < 10.0, f"queries too slow: {query_elapsed:.2f}s"
