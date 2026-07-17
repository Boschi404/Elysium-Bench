# Code Review: Memory Leak Pattern

## Reviewer
Elysium Swarmloop — Autonomous Code Review Agent

---

## 1) Leak Sources Identified

### Leak A — Global Unbounded Cache (`_cache` dict in `leaky_code.py`)

| Attribute | Detail |
|-----------|--------|
| **Location** | `leaky_code.py`, lines 15-23 |
| **Type** | Unbounded dict with no eviction strategy |
| **Trigger** | Every call to `get_data(key)` with a new key adds a permanent entry |
| **Scaling** | O(n) memory growth — each unique key lives forever |
| **Real-world impact** | If keys are user IDs, session tokens, or timestamps in a long-running process (e.g., web server, daemon), RAM grows without bound until OOM kill |

### Leak B — Event Listeners Never Removed (`DataSubscriber` + `EventEmitter`)

| Attribute | Detail |
|-----------|--------|
| **Location** | `leaky_code.py`, lines 52-81 (emitter), lines 83-101 (subscriber) |
| **Type** | Strong reference cycle kept alive by emitter |
| **Trigger** | `DataSubscriber.__init__` calls `self.emitter.on("data", self.on_data)` but never calls `.off()` |
| **Scaling** | Each new subscriber adds 2+ entries to the emitter's listener lists; entries persist even after subscriber is no longer needed |

---

## 2) Why They Leak

### Leak A — Cache

Python's `dict` is a hash table that only grows. There is no code path that removes entries from `_cache`. The `get_data` function appends unconditionally on cache miss. In a long-running process with varied input keys, this acts as a monotonic memory accumulator.

**Reference chain:**
```
module globals → _cache dict → {key1: result1, key2: result2, ..., keyN: resultN}
```
All entries are reachable from the module root — the GC considers them alive forever.

### Leak B — Event Listeners

When `DataSubscriber.__init__` calls `emitter.on("data", self.on_data)`, the emitter's listener list stores a **bound method** object (`self.on_data`). A bound method has an implicit `__self__` attribute — a strong reference back to the `DataSubscriber` instance.

Even after every external reference to the subscriber is dropped (`del sub`), the emitter still holds:
```
emitter._listeners["data"] → [bound_method] → .__self__ → DataSubscriber instance
```

This means the subscriber **can never be garbage collected**. Every new subscriber leaks permanently. In a system that creates and discards subscribers over time (observer pattern, UI components, message bus listeners), memory grows linearly with subscriber churn.

**Additional detail:** Python's generational GC (cycle detector) cannot collect this because all references are one-directional — there is no cycle in the strong-reference sense that would trigger cycle GC. The subscriber stays alive purely through a strong reference chain rooted in the emitter, which is rooted in module globals.

---

## 3) Memory Profiling Approach

For a production investigation of these leaks, use the following toolset:

### Tool 1 — `tracemalloc` (stdlib, zero deps)

```python
import tracemalloc

# Start tracing
tracemalloc.start()

# Run suspect code...
snapshot1 = tracemalloc.take_snapshot()
# ... do work ...
snapshot2 = tracemalloc.take_snapshot()

# Compare
stats = snapshot2.compare_to(snapshot1, 'lineno')
for stat in stats[:10]:
    print(stat)
```

**What to look for:** growing allocations in `get_data` (cache dict insert) and `DataSubscriber.__init__` (bound-method objects not freed).

### Tool 2 — `gc` module (stdlib)

```python
import gc

gc.collect()  # force collection to isolate true leaks

# Find all dict objects (caches are dicts)
for obj in gc.get_objects():
    if isinstance(obj, dict) and len(obj) > 1000:
        print(f"Large dict: {len(obj)} entries at {hex(id(obj))}")

# Find unreachable but uncollected objects
print(f"Uncollectable: {gc.garbage}")
```

### Tool 3 — `objgraph` (pip install)

```python
import objgraph

# Visualise reference chain from emitter
objgraph.show_backrefs(
    [emitter._listeners["data"][0]],
    max_depth=5,
    filename="leak_chain.png"
)

# Count objects of a type
objgraph.show_most_common_types(limit=10)
```

### Tool 4 — `memory_profiler` / `psutil`

```python
import psutil
proc = psutil.Process()

# Log RSS over time
baseline = proc.memory_info().rss
for i in range(10000):
    get_data(f"key_{i}")
    if i % 1000 == 0:
        current = proc.memory_info().rss
        growth = (current - baseline) / 1024 / 1024
        print(f"[{i:5d}] RSS: {current/1024/1024:.1f} MB, growth: {growth:.1f} MB")
```

### Methodology

1. **Baseline** — start tracing immediately after import, before any calls
2. **Exercise** — run 10,000 unique cache keys, create 500 subscribers and discard them
3. **Snapshot comparison** — compare tracemalloc snapshots for per-line allocation deltas
4. **RSS monitoring** — confirm RSS grows monotonically (leak) vs. plateaus (fix)
5. **GC verification** — after dropping all external references to subscribers, count how many are still alive via gc.get_objects() + type filter

---

## 4) Fix: LRU Cache + Weak References

### Fix A: Bounded LRU Cache

**`solution.py`** replaces the global `dict` with `LRUCache` (or `@functools.lru_cache` for simple functions):

```python
from collections import OrderedDict

class LRUCache:
    def __init__(self, maxsize=128, ttl=None):
        self._maxsize = maxsize
        self._ttl = ttl                     # optional time-to-live
        self._cache: OrderedDict = OrderedDict()

    def get(self, key):
        if key not in self._cache:
            return None
        ts, val = self._cache[key]
        if self._ttl and (time.monotonic() - ts) > self._ttl:
            del self._cache[key]            # expired
            return None
        self._cache.move_to_end(key)        # MRU promotion
        return val

    def put(self, key, value):
        self._cache[key] = (time.monotonic(), value)
        self._cache.move_to_end(key)
        while len(self._cache) > self._maxsize:
            self._cache.popitem(last=False) # evict LRU
```

**How it stops the leak:** The cache cannot exceed `maxsize` entries. The oldest (least-recently-used) entry is evicted when capacity is reached. Optional TTL purges stale data based on time. Memory is bounded by `maxsize × average_entry_size`, predictable and controllable.

**Alternative:** `@functools.lru_cache(maxsize=128)` on `_fetch_from_source` for zero-boilerplate LRU when no TTL is needed.

### Fix B: Weak References for Event Listeners

**`solution.py`** uses `weakref.WeakMethod` to store callbacks:

```python
import weakref

class WeakEventEmitter:
    def on(self, event, callback):
        self._listeners.setdefault(event, []).append(
            weakref.WeakMethod(callback)
        )

    def emit(self, event, *args, **kwargs):
        live = []
        for wm in self._listeners.get(event, []):
            cb = wm()               # dereference — may return None
            if cb is not None:
                live.append(wm)
                cb(*args, **kwargs)
        self._listeners[event] = live  # prune dead refs
```

**How it stops the leak:** `weakref.WeakMethod` wraps the bound method without holding a strong reference to the underlying object. When the `DataSubscriber` instance has no external references, the GC collects it, and the `WeakMethod` returns `None` on subsequent dereferences. The `.emit()` lazily prunes these dead references.

The reference chain becomes:
```
emitter._listeners → [WeakMethod] → (weak) → DataSubscriber
```
The weak link breaks the chain — the subscriber is freed when no hard reference remains.

### Alternative Fix: Explicit Cleanup Handle

For imperative codebases where weak references feel implicit, return a disposable token:

```python
handle = emitter.on("data", handler)   # returns Subscription
# later:
handle.dispose()                       # explicitly removes the listener
```

This was implemented as `DisposableSubscriber` in `solution.py` as a belt-and-suspenders pattern.

---

## Verification

All fixes are verified by `tests/test_fix.py`:

| Test | What it proves |
|------|---------------|
| `test_cache_bounded` | Cache never exceeds `maxsize` (fixed), vs unbounded growth (leaky) |
| `test_cache_eviction_lru` | Least-recently-used entry is evicted first |
| `test_cache_ttl` | Stale entries are purged after TTL expiry |
| `test_listener_gc_fixed` | Subscriber is GC'd after dropping external refs |
| `test_listener_leak_proof` | Leaky subscriber survives GC; fixed subscriber does not |
| `test_cache_stress` | Predictable memory usage under high load |
| `test_emit_after_gc` | Emitting after subscriber GC no longer calls dead handlers |

---

## Summary

| Source | Root cause | Fix | Memory bound |
|--------|-----------|-----|-------------|
| Global cache dict | No eviction policy | LRU cache (maxsize + TTL) | O(maxsize) |
| Event listeners | Strong refs in emitter | `weakref.WeakMethod` on callbacks | O(active subscribers) |

**Key principle:** Every data structure that accumulates entries over the lifetime of a process must have either a size bound (LRU/TTL) or a cleanup path (weak refs / explicit dispose). Without one of these, it is a memory leak.
