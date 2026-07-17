"""
Merge Sort Implementation
-------------------------
Implements merge sort algorithm with O(n log n) worst-case time complexity.

Features:
- Sort lists of integers/floats in ascending or descending order
- Support for a `key` parameter (like built-in sorted())
- Handles empty list, single element, already sorted, reverse sorted, duplicates
- Efficient for large lists (100k+ elements)
- Stable sort (preserves relative order of equal elements)
"""

from collections.abc import Callable


def merge_sort(
    arr: list,
    key: Callable | None = None,
    reverse: bool = False,
) -> list:
    """
    Sort a list using the merge sort algorithm.

    Args:
        arr: The list to sort. Can contain any comparable elements.
        key: Optional callable that extracts a comparison key from each element.
             Works like key in built-in sorted().
        reverse: If True, sort in descending order. Defaults to False (ascending).

    Returns:
        A new list sorted according to the parameters.

    Time Complexity: O(n log n) worst case, O(n) auxiliary space.
    Stable: Yes (preserves original order of equal elements).

    Examples:
        >>> merge_sort([3, 1, 4, 1, 5])
        [1, 1, 3, 4, 5]
        >>> merge_sort([3, 1, 4, 1, 5], reverse=True)
        [5, 4, 3, 1, 1]
        >>> merge_sort(["banana", "apple", "cherry"], key=len)
        ['apple', 'banana', 'cherry']
        >>> merge_sort([])
        []
        >>> merge_sort([42])
        [42]
    """
    if not isinstance(arr, list):
        raise TypeError(f"Expected list, got {type(arr).__name__}")

    # Handle trivial cases
    if len(arr) <= 1:
        return list(arr)  # Return a copy, like sorted() does

    # Use key if provided, otherwise identity
    if key is None:
        return _merge_sort_impl(arr, reverse=reverse)
    else:
        # For key-based sorting, we use an index-based approach
        # to maintain stability: sort indices by key(arr[i]), then rearrange
        # This avoids calling key() repeatedly during merge
        return _merge_sort_with_key(arr, key, reverse=reverse)


def _merge_sort_impl(arr: list, reverse: bool = False) -> list:
    """
    Internal merge sort implementation for direct value comparison.

    Uses iterative (bottom-up) merge sort to avoid recursion depth issues
    on large lists (100k+ elements).
    """
    n = len(arr)
    result = list(arr)  # Working copy

    # Temporary buffer for merging
    temp = [None] * n

    # Bottom-up merge sort: start with width=1, double each iteration
    width = 1
    while width < n:
        for left in range(0, n, 2 * width):
            mid = min(left + width, n)
            right = min(left + 2 * width, n)

            if mid < right:  # Only merge if there are two sublists
                _merge(result, left, mid, right, temp, reverse)

        width *= 2

    return result


def _merge(
    arr: list,
    left: int,
    mid: int,
    right: int,
    temp: list,
    reverse: bool,
) -> None:
    """
    Merge two sorted subarrays arr[left:mid] and arr[mid:right] in-place
    using the temp buffer.
    """
    i, j, k = left, mid, left

    if not reverse:
        # Ascending merge
        while i < mid and j < right:
            if arr[i] <= arr[j]:
                temp[k] = arr[i]
                i += 1
            else:
                temp[k] = arr[j]
                j += 1
            k += 1
    else:
        # Descending merge
        while i < mid and j < right:
            if arr[i] >= arr[j]:
                temp[k] = arr[i]
                i += 1
            else:
                temp[k] = arr[j]
                j += 1
            k += 1

    # Copy remaining elements from left half
    while i < mid:
        temp[k] = arr[i]
        i += 1
        k += 1

    # Copy remaining elements from right half
    while j < right:
        temp[k] = arr[j]
        j += 1
        k += 1

    # Copy merged data back to original array
    for i in range(left, right):
        arr[i] = temp[i]


# ---- Key-based sorting using indices for stability ----
# This approach creates a list of indices, sorts them using a Schwartzian
# transform (decorate-sort-undecorate) pattern for efficiency.
#
# We transform each element into (key_value, original_index, element), sort,
# then extract just the elements. This is O(n) key calls and stable.
# However for very large lists with expensive key functions, we use an
# index-based merge approach to avoid the memory overhead of tuples.


def _merge_sort_with_key(arr: list, key: Callable, reverse: bool = False) -> list:
    """
    Stable merge sort using a Schwartzian transform approach with a key function.
    Computes keys once, then uses them throughout.

    Uses bottom-up merge for large-list safety.
    """
    n = len(arr)
    if n <= 1:
        return list(arr)

    # Precompute keys once (O(n) key calls)
    keys = [key(item) for item in arr]

    # Create indexed elements: (key, original_index, value)
    # Using original_index ensures stability when keys are equal
    indexed = list(zip(keys, range(n), arr))

    # Bottom-up merge sort on indexed list
    temp = [None] * n

    width = 1
    while width < n:
        for left in range(0, n, 2 * width):
            mid = min(left + width, n)
            right = min(left + 2 * width, n)

            if mid < right:
                _merge_indexed(indexed, left, mid, right, temp, reverse)

        width *= 2

    # Extract sorted values
    return [item for _, _, item in indexed]


def _merge_indexed(
    arr: list,
    left: int,
    mid: int,
    right: int,
    temp: list,
    reverse: bool,
) -> None:
    """
    Merge two sorted segments of the indexed list.
    Each element is a (key, original_index, value) tuple.

    Comparison logic:
    - Ascending: compare key first; if equal, compare original_index (stability)
    - Descending: compare key reversed; if equal, compare original_index
    """
    i, j, k = left, mid, left

    if not reverse:
        while i < mid and j < right:
            # Compare by key first, then by original index for stability
            if arr[i][0] < arr[j][0] or (arr[i][0] == arr[j][0] and arr[i][1] <= arr[j][1]):
                temp[k] = arr[i]
                i += 1
            else:
                temp[k] = arr[j]
                j += 1
            k += 1
    else:
        while i < mid and j < right:
            if arr[i][0] > arr[j][0] or (arr[i][0] == arr[j][0] and arr[i][1] <= arr[j][1]):
                temp[k] = arr[i]
                i += 1
            else:
                temp[k] = arr[j]
                j += 1
            k += 1

    while i < mid:
        temp[k] = arr[i]
        i += 1
        k += 1

    while j < right:
        temp[k] = arr[j]
        j += 1
        k += 1

    for idx in range(left, right):
        arr[idx] = temp[idx]
