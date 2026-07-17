"""
Tests for merge_sort implementation.

Covers: empty list, single element, already sorted, reverse sorted,
duplicates, large lists (100k+), key parameter, reverse parameter,
stability, and type validation.
"""

import copy
import math
import random
import sys
import time

import pytest

from merge_sort import merge_sort


#  ────────────── Basic edge cases ──────────────

class TestEmptyAndSingle:
    def test_empty_list(self):
        assert merge_sort([]) == []

    def test_single_element(self):
        assert merge_sort([42]) == [42]

    def test_single_element_string(self):
        assert merge_sort(["hello"]) == ["hello"]


#  ────────────── Core sorting correctness ──────────────

class TestSortingCorrectness:
    def test_already_sorted(self):
        arr = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        assert merge_sort(arr) == sorted(arr)

    def test_reverse_sorted(self):
        arr = [10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
        assert merge_sort(arr) == sorted(arr)

    def test_all_duplicates(self):
        arr = [5, 5, 5, 5, 5]
        assert merge_sort(arr) == sorted(arr)

    def test_mixed_with_duplicates(self):
        arr = [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5]
        assert merge_sort(arr) == sorted(arr)

    def test_random_small(self):
        for seed in range(50):
            rng = random.Random(seed)
            arr = [rng.randint(-1000, 1000) for _ in range(100)]
            assert merge_sort(arr) == sorted(arr), f"Failed on seed={seed}"

    def test_floats(self):
        arr = [3.14, 1.41, 2.72, 0.0, -1.5, 2.72]
        assert merge_sort(arr) == sorted(arr)

    def test_mixed_negative_positive(self):
        arr = [-5, 10, -3, 0, 7, -1, 8]
        assert merge_sort(arr) == sorted(arr)


#  ────────────── reverse parameter ──────────────

class TestReverse:
    def test_reverse_sorted(self):
        arr = [3, 1, 4, 1, 5]
        assert merge_sort(arr, reverse=True) == sorted(arr, reverse=True)

    def test_reverse_already_sorted_desc(self):
        arr = [10, 9, 8, 7, 6]
        assert merge_sort(arr, reverse=True) == sorted(arr, reverse=True)

    def test_reverse_empty(self):
        assert merge_sort([], reverse=True) == []

    def test_reverse_single(self):
        assert merge_sort([42], reverse=True) == [42]

    def test_reverse_duplicates(self):
        arr = [5, 3, 5, 1, 3]
        assert merge_sort(arr, reverse=True) == sorted(arr, reverse=True)


#  ────────────── key parameter ──────────────

class TestKey:
    def test_key_abs(self):
        arr = [-10, 3, -7, 2, -1, 8]
        assert merge_sort(arr, key=abs) == sorted(arr, key=abs)

    def test_key_len_strings(self):
        arr = ["banana", "apple", "cherry", "date", "elderberry"]
        assert merge_sort(arr, key=len) == sorted(arr, key=len)

    def test_key_str_lower(self):
        arr = ["Banana", "apple", "Cherry", "APPLE"]
        assert merge_sort(arr, key=str.lower) == sorted(arr, key=str.lower)

    def test_key_named_attr(self):
        class Item:
            def __init__(self, value):
                self.value = value
            def __repr__(self):
                return f"Item({self.value})"

        items = [Item(3), Item(1), Item(2)]
        sorted_items = merge_sort(items, key=lambda x: x.value)
        assert [i.value for i in sorted_items] == [1, 2, 3]

    def test_key_with_reverse(self):
        arr = ["aa", "b", "ccc", "dddd", "e"]
        assert merge_sort(arr, key=len, reverse=True) == sorted(arr, key=len, reverse=True)

    def test_key_stability(self):
        """Stability: elements with equal keys preserve original order."""
        pairs = [(1, "a"), (2, "b"), (1, "c"), (2, "d"), (1, "e")]
        result = merge_sort(pairs, key=lambda x: x[0])
        # Since keys are [1,2,1,2,1], sorted by key stable gives:
        # (1,"a"), (1,"c"), (1,"e"), (2,"b"), (2,"d")
        assert result[0] == (1, "a")
        assert result[1] == (1, "c")
        assert result[2] == (1, "e")
        assert result[3] == (2, "b")
        assert result[4] == (2, "d")


#  ────────────── Large lists (100k+) ──────────────

class TestLargeLists:
    LARGE_SIZE = 100_000

    def test_large_random(self):
        rng = random.Random(42)
        arr = [rng.randint(-10**6, 10**6) for _ in range(self.LARGE_SIZE)]
        expected = sorted(arr)

        start = time.perf_counter()
        result = merge_sort(arr)
        elapsed = time.perf_counter() - start

        assert result == expected
        # Should complete in reasonable time (<10 sec on any modern hardware)
        assert elapsed < 30, f"Too slow: {elapsed:.2f}s"

    def test_large_reverse_sorted(self):
        arr = list(range(self.LARGE_SIZE, 0, -1))
        expected = sorted(arr)

        start = time.perf_counter()
        result = merge_sort(arr)
        elapsed = time.perf_counter() - start

        assert result == expected
        assert elapsed < 30, f"Too slow: {elapsed:.2f}s"

    def test_large_already_sorted(self):
        arr = list(range(self.LARGE_SIZE))
        expected = sorted(arr)

        start = time.perf_counter()
        result = merge_sort(arr)
        elapsed = time.perf_counter() - start

        assert result == expected
        assert elapsed < 30, f"Too slow: {elapsed:.2f}s"

    def test_large_with_key(self):
        rng = random.Random(99)
        arr = [rng.randint(-10**6, 10**6) for _ in range(50_000)]
        expected = sorted(arr, key=abs)

        start = time.perf_counter()
        result = merge_sort(arr, key=abs)
        elapsed = time.perf_counter() - start

        assert result == expected
        assert elapsed < 30, f"Too slow: {elapsed:.2f}s"


#  ────────────── Stability (direct value sort) ──────────────

class TestStability:
    def test_stable_sort_equal_elements(self):
        """Merge sort is stable: equal elements should keep original order."""
        pairs = [(2, "x"), (1, "a"), (2, "y"), (1, "b")]
        result = merge_sort(pairs, key=lambda p: p[0])
        expected = [(1, "a"), (1, "b"), (2, "x"), (2, "y")]
        assert result == expected

    def test_stability_reverse(self):
        pairs = [(2, "x"), (1, "a"), (2, "y"), (1, "b")]
        result = merge_sort(pairs, key=lambda p: p[0], reverse=True)
        expected = [(2, "x"), (2, "y"), (1, "a"), (1, "b")]
        assert result == expected


#  ────────────── Error handling ──────────────

class TestErrorHandling:
    def test_non_list_input(self):
        with pytest.raises(TypeError):
            merge_sort("not a list")

    def test_incomparable_elements(self):
        """Mixing types that can't be compared should raise TypeError."""
        with pytest.raises(TypeError):
            merge_sort([1, "a", 3])

    def test_original_unmodified(self):
        """merge_sort should return a new list, not mutate the input."""
        original = [3, 1, 4, 1, 5]
        copy_arr = list(original)
        result = merge_sort(original)
        assert original == copy_arr, "Original list was mutated"
        assert result == [1, 1, 3, 4, 5]


#  ────────────── Return type ──────────────

class TestReturnType:
    def test_returns_list(self):
        assert isinstance(merge_sort([3, 1, 4]), list)
        assert isinstance(merge_sort([]), list)
        assert isinstance(merge_sort([42]), list)


#  ────────────── O(n log n) characteristic ──────────────

class TestComplexity:
    """Ensure runtime scales roughly O(n log n), not O(n^2)."""

    def test_nlogn_characteristic(self):
        """Verify n=200k completes in reasonable time."""
        rng = random.Random(12345)
        arr = [rng.randint(-10**6, 10**6) for _ in range(200_000)]

        start = time.perf_counter()
        result = merge_sort(arr)
        elapsed = time.perf_counter() - start

        expected = sorted(arr)
        assert result == expected
        # 200k elements in <60s is reasonable for a pure-Python merge sort
        assert elapsed < 60, f"Too slow for 200k elements: {elapsed:.2f}s"
