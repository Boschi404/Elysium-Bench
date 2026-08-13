"""Reference: store.py — bounded event store, strictly-newer-than-all policy."""
class EventStore:
    def __init__(self, capacity: int):
        if capacity < 1:
            raise ValueError("capacity must be >= 1")
        self.capacity = capacity
        self._events: list[dict] = []

    def insert(self, event: dict) -> bool:
        if not isinstance(event, dict) or "ts" not in event:
            return False
        if len(self._events) < self.capacity:
            self._events.append(event)
            return True
        newest = max(e["ts"] for e in self._events)
        if event["ts"] <= newest:
            # incoming is not strictly newer than all stored events → reject
            return False
        oldest = min(self._events, key=lambda e: e["ts"])
        self._events.remove(oldest)
        self._events.append(event)
        return True

    def query_since(self, ts: int) -> list[dict]:
        return [e for e in sorted(self._events, key=lambda e: e["ts"])
                if e["ts"] >= ts]

    def count(self) -> int:
        return len(self._events)
