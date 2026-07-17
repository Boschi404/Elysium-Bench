"""
Binary Search Implementation
============================
Implement binary search on a sorted list.

Handles:
- Exact match found → returns the index
- Element not found → returns -1
- Empty list → returns -1
- Single element → works correctly
- Duplicate elements → returns any valid index
- Very large lists → O(log n) time complexity
"""

from typing import List


def binary_search(arr: List[int], target: int) -> int:
    """
    Perform binary search on a sorted list.

    Args:
        arr: A sorted list of integers (ascending order)
        target: The integer value to search for

    Returns:
        The index of the target if found, or -1 if not found

    Time complexity: O(log n)
    Space complexity: O(1)
    """
    left, right = 0, len(arr) - 1

    while left <= right:
        # Use mid = left + (right - left) // 2 to avoid integer overflow
        mid = left + (right - left) // 2
        mid_val = arr[mid]

        if mid_val == target:
            return mid
        elif mid_val < target:
            left = mid + 1
        else:
            right = mid - 1

    return -1
