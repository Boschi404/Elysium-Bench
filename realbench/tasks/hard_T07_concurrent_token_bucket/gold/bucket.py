"""Reference: thread-safe token bucket with continuous refill."""
import threading
import time


class TokenBucket:
    def __init__(self, capacity: float, refill_rate: float):
        if capacity <= 0:
            raise ValueError("capacity must be > 0")
        if refill_rate <= 0:
            raise ValueError("refill_rate must be > 0")
        self.capacity = float(capacity)
        self.refill_rate = float(refill_rate)
        self._tokens = float(capacity)
        self._last = time.monotonic()
        self._lock = threading.Lock()

    def _refill(self, now: float) -> None:
        if now is None:
            now = time.monotonic()
        elapsed = now - self._last
        if elapsed > 0:
            self._tokens = min(self.capacity, self._tokens + elapsed * self.refill_rate)
            self._last = now
        elif elapsed < 0:
            # clock went backwards: reset reference, keep tokens
            self._last = now

    def available(self, now: float | None = None) -> float:
        with self._lock:
            self._refill(now)
            return self._tokens

    def try_acquire(self, n: float = 1.0, now: float | None = None) -> bool:
        with self._lock:
            self._refill(now)
            if self._tokens >= n:
                self._tokens -= n
                return True
            return False
