"""Reference: DAG scheduler — Kahn + DP longest paths."""
import heapq


class Dag:
    def __init__(self):
        self._tasks: dict[str, tuple[int, list[str]]] = {}

    def add_task(self, task_id: str, duration: int, deps: list[str]) -> None:
        if duration < 1:
            raise ValueError("duration must be >= 1")
        if task_id in self._tasks:
            raise ValueError("duplicate task id")
        self._tasks[task_id] = (duration, list(deps))

    def is_valid(self) -> bool:
        for tid, (_, deps) in self._tasks.items():
            if tid in deps:
                return False
            for d in deps:
                if d not in self._tasks:
                    return False
        return self._no_cycle()

    def _no_cycle(self) -> bool:
        state: dict[str, int] = {}

        def dfs(u):
            state[u] = 1
            for d in self._tasks[u][1]:
                if d not in state:
                    if dfs(d):
                        return True
                elif state[d] == 1:
                    return True
            state[u] = 2
            return False

        return not any(t not in state and dfs(t) for t in self._tasks)

    def _check_ok(self):
        if not self.is_valid():
            raise ValueError("cycle or missing dependency")

    def topological_order(self) -> list[str]:
        self._check_ok()
        indeg = {t: 0 for t in self._tasks}
        children = {t: [] for t in self._tasks}
        for t, (_, deps) in self._tasks.items():
            indeg[t] = len(deps)
            for d in deps:
                children[d].append(t)
        heap = [t for t in indeg if indeg[t] == 0]
        heapq.heapify(heap)
        order = []
        while heap:
            t = heapq.heappop(heap)
            order.append(t)
            for c in children[t]:
                indeg[c] -= 1
                if indeg[c] == 0:
                    heapq.heappush(heap, c)
        return order

    def critical_path_length(self) -> int:
        self._check_ok()
        es = self._longest_to()  # es[t] already includes t's duration
        return max(es.values()) if es else 0

    def _longest_to(self) -> dict[str, int]:
        """Longest path duration ending at t, INCLUDING t."""
        best = {t: self._tasks[t][0] for t in self._tasks}
        for t in self.topological_order():
            dur, deps = self._tasks[t]
            base = 0
            for d in deps:
                base = max(base, best[d])
            best[t] = base + dur
        return best

    def earliest_start(self, task_id: str) -> int:
        if task_id not in self._tasks:
            raise KeyError(task_id)
        self._check_ok()
        longest_to = self._longest_to()
        _, deps = self._tasks[task_id]
        return max((longest_to[d] for d in deps), default=0)

    def latest_start(self, task_id: str) -> int:
        if task_id not in self._tasks:
            raise KeyError(task_id)
        self._check_ok()
        cp = self.critical_path_length()
        # longest path duration STARTING at task_id (including itself)
        longest_from = {t: self._tasks[t][0] for t in self._tasks}
        for t in reversed(self.topological_order()):
            dur, _ = self._tasks[t]
            # children: tasks that depend on t
            best = dur
            for other, (_, deps) in self._tasks.items():
                if t in deps:
                    best = max(best, dur + longest_from[other])
            longest_from[t] = best
        return cp - longest_from[task_id]
