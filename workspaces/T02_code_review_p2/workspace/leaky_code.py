"""
leaky_code.py — Code with intentional memory leak patterns.

Leak sources:
  1. Global unbounded cache dict (never evicts)
  2. Event listeners never removed (prevents GC of subscriber objects)
"""

import time
import threading
from typing import Any, Callable

# ── Leak Source 1: Global unbounded cache ──────────────────────────────
_cache: dict[str, Any] = {}

def get_data(key: str) -> Any:
    """Retrieve data, caching results forever with no eviction."""
    if key in _cache:
        return _cache[key]

    # Simulate expensive fetch
    result = _fetch_from_source(key)
    _cache[key] = result            # ← stored forever, never removed
    return result

def _fetch_from_source(key: str) -> dict:
    """Simulated upstream call."""
    time.sleep(0.01)
    return {"key": key, "value": f"data_{key}", "timestamp": time.time()}

def cache_size() -> int:
    """Expose cache size for testing."""
    return len(_cache)


# ── Leak Source 2: Event listener never removed ────────────────────────

class EventEmitter:
    """Simple pub/sub — listeners are strong references that are never cleaned up."""

    def __init__(self):
        self._listeners: dict[str, list[Callable]] = {}

    def on(self, event: str, callback: Callable) -> None:
        """Register a listener (no deregistration mechanism)."""
        self._listeners.setdefault(event, []).append(callback)

    def off(self, event: str, callback: Callable) -> None:
        """Remove a listener — intentionally missing from leaky version."""
        # This method deliberately omitted to demonstrate the leak.
        pass

    def emit(self, event: str, *args: Any, **kwargs: Any) -> None:
        for cb in self._listeners.get(event, []):
            cb(*args, **kwargs)

    def listener_count(self, event: str) -> int:
        return len(self._listeners.get(event, []))


class DataSubscriber:
    """
    Subscriber that registers itself on an emitter but never deregisters.

    Because the emitter holds a strong reference to the bound method
    `self.on_data`, and the bound method holds `self` via __self__,
    this object can never be garbage-collected even after all external
    references to it are dropped.
    """

    def __init__(self, name: str, emitter: EventEmitter):
        self.name = name
        self.emitter = emitter
        # Leak: registering but never removing
        self.emitter.on("data", self.on_data)
        self.emitter.on("status", self.on_status)

    def on_data(self, data: Any) -> None:
        print(f"[{self.name}] received data: {data}")

    def on_status(self, status: str) -> None:
        print(f"[{self.name}] status: {status}")

    def __del__(self):
        # Destructor — used in tests to verify GC happens in fixed version
        print(f"[{self.name}] __del__ called")
