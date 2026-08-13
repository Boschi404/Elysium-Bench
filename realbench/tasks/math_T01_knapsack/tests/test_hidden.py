"""Hidden tests: knapsack. Instances are generated HERE at grading time —
the solver never sees them, and the expected optima come from an independent
exact solver (verified by brute force on the small instances).
"""
import json
import random
import time
from pathlib import Path

import pytest

from knapsack import solve_knapsack

_EXPECTED = json.loads(
    (Path(__file__).parent / "expected_optimums.json").read_text())


def _make_instance(seed, n, wmax, cap):
    rng = random.Random(seed)
    values = [rng.randint(1, 100) for _ in range(n)]
    weights = [rng.randint(1, wmax) for _ in range(n)]
    return values, weights, cap


def test_tiny1():
    v, w, cap = _make_instance(101, 8, 5, 10)
    assert solve_knapsack(v, w, cap) == _EXPECTED["tiny1"]


def test_tiny2():
    v, w, cap = _make_instance(202, 10, 6, 15)
    assert solve_knapsack(v, w, cap) == _EXPECTED["tiny2"]


def test_tiny_all_items_fit():
    v, w, cap = _make_instance(303, 5, 3, 1000)
    assert solve_knapsack(v, w, cap) == _EXPECTED["tiny_all"]


def test_medium1():
    v, w, cap = _make_instance(404, 50, 20, 200)
    assert solve_knapsack(v, w, cap) == _EXPECTED["medium1"]


def test_medium2():
    v, w, cap = _make_instance(505, 100, 25, 500)
    assert solve_knapsack(v, w, cap) == _EXPECTED["medium2"]


def test_large1():
    v, w, cap = _make_instance(606, 200, 100, 5000)
    assert solve_knapsack(v, w, cap) == _EXPECTED["large1"]


def test_large2_perf():
    v, w, cap = _make_instance(707, 300, 150, 8000)
    start = time.perf_counter()
    result = solve_knapsack(v, w, cap)
    elapsed = time.perf_counter() - start
    assert result == _EXPECTED["large2"]
    assert elapsed < 10.0, f"too slow: {elapsed:.2f}s"


def test_zero_capacity():
    assert solve_knapsack([1, 2, 3], [1, 1, 1], 0) == 0


def test_returns_int():
    result = solve_knapsack([1, 2], [1, 1], 1)
    assert isinstance(result, int) and not isinstance(result, bool)
