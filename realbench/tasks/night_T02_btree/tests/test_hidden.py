"""Hidden tests: B-tree — insert/delete correctness vs reference + perf."""
import random
import time

import pytest

from btree import BTree


def test_insert_search_basic():
    t = BTree(2)
    for k in [10, 20, 5, 6, 12, 30, 7, 17]:
        t.insert(k)
    assert t.keys() == [5, 6, 7, 10, 12, 17, 20, 30]
    for k in [10, 20, 5, 6, 12, 30, 7, 17]:
        assert t.search(k) is True
    for k in [1, 100, 13, 0, -5]:
        assert t.search(k) is False


def test_insert_duplicate_raises():
    t = BTree(2)
    t.insert(42)
    with pytest.raises(ValueError):
        t.insert(42)


def test_constructor_validation():
    with pytest.raises(ValueError):
        BTree(0)
    with pytest.raises(ValueError):
        BTree(1)
    with pytest.raises(ValueError):
        BTree(-3)


def test_larger_min_degree():
    t = BTree(3)
    for k in range(100):
        t.insert(k)
    assert t.keys() == list(range(100))
    assert all(t.search(k) for k in range(100))


def test_delete_leaf_simple():
    t = BTree(2)
    for k in [10, 20, 30]:
        t.insert(k)
    assert t.delete(20) is True
    assert t.keys() == [10, 30]
    assert t.delete(20) is False


def test_delete_absent():
    t = BTree(2)
    for k in [1, 2, 3]:
        t.insert(k)
    assert t.delete(99) is False
    assert t.keys() == [1, 2, 3]


def test_delete_all_keys():
    t = BTree(2)
    keys = list(range(50))
    for k in keys:
        t.insert(k)
    for k in keys:
        assert t.delete(k) is True, f"failed to delete {k}"
    assert t.keys() == []
    assert t.search(25) is False


def test_delete_reverse_order():
    t = BTree(2)
    keys = list(range(50))
    for k in keys:
        t.insert(k)
    for k in reversed(keys):
        assert t.delete(k) is True
    assert t.keys() == []


def test_delete_internal_node_predecessor_successor():
    t = BTree(2)
    # build a tree tall enough to have internal keys
    for k in range(100):
        t.insert(k)
    # delete internal-node keys (keys that become internal in a t=2 tree)
    for k in [49, 25, 12, 6, 75]:
        assert t.delete(k) is True
    remaining = [k for k in range(100) if k not in {49, 25, 12, 6, 75}]
    assert t.keys() == remaining


def test_random_insert_delete_vs_reference():
    rng = random.Random(20260813)
    t = BTree(2)
    ref = set()
    for _ in range(5000):
        if rng.random() < 0.6:
            k = rng.randint(0, 500)
            if k in ref:
                with pytest.raises(ValueError):
                    t.insert(k)
            else:
                t.insert(k)
                ref.add(k)
        else:
            k = rng.randint(0, 500)
            assert t.delete(k) == (k in ref)
            ref.discard(k)
        if rng.random() < 0.05:  # periodic full check
            assert t.keys() == sorted(ref)
    assert t.keys() == sorted(ref)
    for k in list(ref)[:100]:
        assert t.search(k) is True


def test_random_vs_reference_min_degree_3():
    rng = random.Random(777)
    t = BTree(3)
    ref = set()
    for _ in range(3000):
        if rng.random() < 0.55:
            k = rng.randint(0, 300)
            if k not in ref:
                t.insert(k)
                ref.add(k)
        else:
            k = rng.randint(0, 300)
            assert t.delete(k) == (k in ref)
            ref.discard(k)
    assert t.keys() == sorted(ref)


def test_perf_50k_inserts_25k_deletes():
    rng = random.Random(1)
    t = BTree(2)
    start = time.perf_counter()
    for _ in range(50_000):
        k = rng.randint(0, 1_000_000)
        try:
            t.insert(k)
        except ValueError:
            pass
    for _ in range(25_000):
        t.delete(rng.randint(0, 1_000_000))
    elapsed = time.perf_counter() - start
    assert elapsed < 10.0, f"too slow: {elapsed:.2f}s"
    assert len(t.keys()) > 10_000


def test_single_key_lifecycle():
    t = BTree(2)
    assert t.keys() == []
    t.insert(5)
    assert t.keys() == [5]
    assert t.delete(5) is True
    assert t.keys() == []
    t.insert(7)
    assert t.search(7) is True
