"""Reference: LFU cache — dict + freq→OrderedDict (O(1) operations)."""
from collections import OrderedDict


class LFUCache:
    def __init__(self, capacity: int):
        if capacity < 1:
            raise ValueError("capacity must be >= 1")
        self.capacity = capacity
        self.values: dict[int, int] = {}
        self.freqs: dict[int, int] = {}
        self.lists: dict[int, OrderedDict] = {}  # freq -> keys in LRU order
        self.min_freq = 0

    def _bump(self, key):
        f = self.freqs[key]
        self.freqs[key] = f + 1
        lst = self.lists[f]
        lst.pop(key)
        if not lst:
            del self.lists[f]
            if f == self.min_freq:
                self.min_freq += 1
        self.lists.setdefault(f + 1, OrderedDict())[key] = None

    def get(self, key: int) -> int:
        if key not in self.values:
            return -1
        self._bump(key)
        return self.values[key]

    def put(self, key: int, value: int) -> None:
        if key in self.values:
            self.values[key] = value
            self._bump(key)
            return
        if len(self.values) >= self.capacity:
            lst = self.lists[self.min_freq]
            victim, _ = lst.popitem(last=False)
            if not lst:
                del self.lists[self.min_freq]
            del self.values[victim]
            del self.freqs[victim]
        self.values[key] = value
        self.freqs[key] = 1
        self.lists.setdefault(1, OrderedDict())[key] = None
        self.min_freq = 1
