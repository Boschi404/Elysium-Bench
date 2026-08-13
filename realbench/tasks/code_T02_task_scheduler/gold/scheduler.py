"""Reference solution: priority scheduler (Kahn's algorithm + heap)."""
import heapq
from dataclasses import dataclass, field


@dataclass
class Task:
    id: str
    priority: int
    deps: list[str] = field(default_factory=list)


class Scheduler:
    def __init__(self):
        self._tasks: dict[str, Task] = {}

    def add_task(self, task: Task) -> None:
        self._tasks[task.id] = task

    def is_valid(self) -> bool:
        for t in self._tasks.values():
            if t.id in t.deps:
                return False
            for d in t.deps:
                if d not in self._tasks:
                    return False
        return not self._has_cycle()

    def _has_cycle(self) -> bool:
        state = {}  # 0=unvisited 1=in-stack 2=done
        def dfs(u):
            state[u] = 1
            for d in self._tasks[u].deps:
                if d not in state:
                    if dfs(d):
                        return True
                elif state[d] == 1:
                    return True
            state[u] = 2
            return False
        for t in self._tasks:
            if t not in state and dfs(t):
                return True
        return False

    def detect_cycle(self) -> list[str]:
        state = {}
        stack = []
        cyc = []
        def dfs(u):
            state[u] = 1
            stack.append(u)
            for d in self._tasks[u].deps:
                if d not in state:
                    if dfs(d):
                        return True
                elif state[d] == 1:
                    cyc.extend(stack[stack.index(d):])
                    return True
            stack.pop()
            state[u] = 2
            return False
        for t in self._tasks:
            if t not in state and dfs(t):
                return cyc
        return []

    def run_order(self) -> list[str]:
        if not self.is_valid():
            raise ValueError("cycle or missing dependency")
        indeg = {t: 0 for t in self._tasks}
        for t in self._tasks.values():
            for d in t.deps:
                indeg[t.id] += 1
        # max-heap via negative priority; tie-break ascending id
        heap = [(-self._tasks[t].priority, t) for t in indeg if indeg[t] == 0]
        heapq.heapify(heap)
        order = []
        while heap:
            _, t = heapq.heappop(heap)
            order.append(t)
            for other in self._tasks.values():
                if t in other.deps:
                    indeg[other.id] -= 1
                    if indeg[other.id] == 0:
                        heapq.heappush(heap, (-other.priority, other.id))
        return order
