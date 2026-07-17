"""
solution.py — Fixed version of leaky_code.py.

Fixes:
  1. Unbounded cache → LRU cache via `functools.lru_cache` + custom TTL via
     `cachetools.TTLCache` (maxsize + time-based eviction).
  2. Event listener leak → weak references via `weakref.WeakMethod` so the
     emitter does not prevent garbage collection of subscriber objects.
"""

import time
import weakref
from collections import OrderedDict
from typing import Any, Callable


# ── Fix 1: LRU Cache with optional TTL ─────────────────────────────────

class LRUCache:
    """
    Thread-safe LRU cache with bounded size.

    Evicts the least-recently-used entry when the cache exceeds `maxsize`.
    Optional `ttl` discards entries older than `ttl` seconds.
    """

    def __init__(self, maxsize: int = 128, ttl: float | None = None):
        self._maxsize = maxsize
        self._ttl = ttl
        self._cache: OrderedDict[str, tuple[float, Any]] = OrderedDict()

    def get(self, key: str) -> Any | None:
        """Return cached value or None if missing / expired."""
        if key not in self._cache:
            return None

        timestamp, value = self._cache[key]

        # TTL expiry check
        if self._ttl is not None and (time.monotonic() - timestamp) > self._ttl:
            del self._cache[key]
            return None

        # MRU promotion — LRU semantics
        self._cache.move_to_end(key)
        return value

    def put(self, key: str, value: Any) -> None:
        """Insert or update a cache entry."""
        now = time.monotonic()
        self._cache[key] = (now, value)
        self._cache.move_to_end(key)   # most recently used

        # Evict oldest entries when over capacity
        while len(self._cache) > self._maxsize:
            self._cache.popitem(last=False)  # FIFO = LRU

    def __len__(self) -> int:
        return len(self._cache)

    def clear(self) -> None:
        self._cache.clear()


# Global bounded cache (replaces the unbounded dict)
_cache = LRUCache(maxsize=128, ttl=300.0)  # 128 entries, 5 min TTL

def get_data(key: str) -> Any:
    """Retrieve data with bounded LRU caching."""
    cached = _cache.get(key)
    if cached is not None:
        return cached

    result = _fetch_from_source(key)
    _cache.put(key, result)
    return result

def _fetch_from_source(key: str) -> dict:
    """Simulated upstream call."""
    time.sleep(0.01)
    return {"key": key, "value": f"data_{key}", "timestamp": time.time()}

def cache_size() -> int:
    return len(_cache)


# ── Fix 2: Weak-reference-backed event emitter ─────────────────────────

class WeakEventEmitter:
    """
    Event emitter using weak references for callbacks.

    Bound methods are stored as `weakref.WeakMethod`; plain functions
    as `weakref.ref`.  When the subscriber object is garbage-collected,
    the weak reference becomes dead and is lazily pruned on emit/off.
    """

    def __init__(self):
        self._listeners: dict[str, list[weakref.ref | weakref.WeakMethod]] = {}

    @staticmethod
    def _wrap(callback: Callable) -> weakref.ref | weakref.WeakMethod:
        """Wrap a callback in the appropriate weak-reference type."""
        if hasattr(callback, "__self__"):
            return weakref.WeakMethod(callback)
        return weakref.ref(callback)

    @staticmethod
    def _deref(
        w: weakref.ref | weakref.WeakMethod,
    ) -> Callable | None:
        """Dereference, returning the callable or None if dead."""
        return w()

    def on(self, event: str, callback: Callable) -> None:
        """Register a listener via weak reference."""
        self._listeners.setdefault(event, []).append(self._wrap(callback))

    def off(self, event: str, callback: Callable) -> None:
        """Remove a specific listener, comparing by identity where possible."""
        # Capture identity tokens for comparison
        try:
            cb_func = callback.__func__
            cb_self = callback.__self__
            is_bound = True
        except AttributeError:
            cb_func = callback
            cb_self = None
            is_bound = False

        dead: list[weakref.ref | weakref.WeakMethod] = []
        for w in self._listeners.get(event, []):
            cb = self._deref(w)
            if cb is None:
                dead.append(w)
                continue
            if is_bound:
                try:
                    if cb.__func__ is cb_func and cb.__self__ is cb_self:
                        dead.append(w)
                except AttributeError:
                    pass
            elif cb is callback:
                dead.append(w)

        for w in dead:
            self._listeners[event].remove(w)

    def emit(self, event: str, *args: Any, **kwargs: Any) -> None:
        """Fire an event to all live listeners, pruning dead refs."""
        live: list[weakref.ref | weakref.WeakMethod] = []
        for w in self._listeners.get(event, []):
            cb = self._deref(w)
            if cb is not None:
                live.append(w)
                cb(*args, **kwargs)
        # Prune dead references
        self._listeners[event] = live

    def listener_count(self, event: str) -> int:
        """Return number of registered listeners (may include dead refs)."""
        return len(self._listeners.get(event, []))


class DataSubscriber:
    """
    Subscriber that uses weak-event emitter.

    Since the emitter only holds a weak reference to `self.on_data`,
    this object CAN be GC'd when all external references drop.
    """

    def __init__(self, name: str, emitter: WeakEventEmitter):
        self.name = name
        self.emitter = emitter
        self.emitter.on("data", self.on_data)
        self.emitter.on("status", self.on_status)

    def on_data(self, data: Any) -> None:
        print(f"[{self.name}] received data: {data}")

    def on_status(self, status: str) -> None:
        print(f"[{self.name}] status: {status}")

    def __del__(self):
        print(f"[{self.name}] __del__ called")


# ── Helper for manual cleanup pattern (belt and suspenders) ────────────

class DisposableSubscriber:
    """Alternative: explicit cleanup via a disposable handle."""

    def __init__(self, name: str, emitter: WeakEventEmitter):
        self.name = name
        self.emitter = emitter
        self._handles = [
            ("data", self.on_data),
            ("status", self.on_status),
        ]
        for event, cb in self._handles:
            self.emitter.on(event, cb)

    def dispose(self) -> None:
        """Explicitly deregister all listeners."""
        for event, cb in self._handles:
            self.emitter.off(event, cb)
        self._handles.clear()

    def on_data(self, data: Any) -> None:
        print(f"[{self.name}] received data: {data}")

    def on_status(self, status: str) -> None:
        print(f"[{self.name}] status: {status}")

    def __del__(self):
        print(f"[{self.name}] __del__ called")
