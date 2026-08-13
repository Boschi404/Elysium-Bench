"""Hidden tests: priority scheduler — exact order, cycles, scale."""
import random
import time

import pytest

from scheduler import Task, Scheduler


def test_simple_chain():
    s = Scheduler()
    s.add_task(Task("a", 1, []))
    s.add_task(Task("b", 1, ["a"]))
    s.add_task(Task("c", 1, ["b"]))
    assert s.run_order() == ["a", "b", "c"]


def test_independent_tasks_priority_order():
    s = Scheduler()
    s.add_task(Task("low", 1, []))
    s.add_task(Task("high", 10, []))
    s.add_task(Task("mid", 5, []))
    assert s.run_order() == ["high", "mid", "low"]


def test_priority_ties_lexicographic():
    s = Scheduler()
    s.add_task(Task("b", 3, []))
    s.add_task(Task("a", 3, []))
    s.add_task(Task("c", 3, []))
    assert s.run_order() == ["a", "b", "c"]


def test_diamond_dependency():
    s = Scheduler()
    s.add_task(Task("start", 1, []))
    s.add_task(Task("left", 5, ["start"]))
    s.add_task(Task("right", 5, ["start"]))
    s.add_task(Task("end", 1, ["left", "right"]))
    order = s.run_order()
    assert order[0] == "start"
    assert order[-1] == "end"
    assert set(order[1:3]) == {"left", "right"}
    assert order.index("left") < order.index("end")
    assert order.index("right") < order.index("end")


def test_dependency_beats_priority():
    s = Scheduler()
    s.add_task(Task("b", 100, ["a"]))  # very high priority but blocked
    s.add_task(Task("a", 1, []))
    s.add_task(Task("c", 50, []))
    assert s.run_order() == ["c", "a", "b"]


def test_disconnected_components():
    s = Scheduler()
    s.add_task(Task("x1", 2, []))
    s.add_task(Task("x2", 1, ["x1"]))
    s.add_task(Task("y1", 9, []))
    order = s.run_order()
    assert order.index("y1") < order.index("x1") < order.index("x2")


def test_cycle_detection_simple():
    s = Scheduler()
    s.add_task(Task("a", 1, ["b"]))
    s.add_task(Task("b", 1, ["a"]))
    assert not s.is_valid()
    assert set(s.detect_cycle()) == {"a", "b"}
    with pytest.raises(ValueError):
        s.run_order()


def test_cycle_detection_tail_plus_cycle():
    s = Scheduler()
    s.add_task(Task("a", 1, []))
    s.add_task(Task("b", 1, ["a"]))
    s.add_task(Task("c", 1, ["b", "d"]))
    s.add_task(Task("d", 1, ["c"]))
    cyc = s.detect_cycle()
    assert set(cyc) == {"c", "d"}


def test_self_loop_invalid():
    s = Scheduler()
    s.add_task(Task("a", 1, ["a"]))
    assert not s.is_valid()


def test_missing_dependency_invalid():
    s = Scheduler()
    s.add_task(Task("a", 1, ["ghost"]))
    assert not s.is_valid()


def test_large_graph_1000_nodes():
    """1000 nodes, random DAG: must be fast and topologically correct."""
    rng = random.Random(7)
    s = Scheduler()
    n = 1000
    edges = {}  # keep a local copy of the graph to verify independently
    for i in range(n):
        deps = [str(j) for j in range(i) if rng.random() < 0.005]
        edges[str(i)] = deps
        s.add_task(Task(str(i), rng.randint(0, 1000), deps))
    start = time.perf_counter()
    order = s.run_order()
    elapsed = time.perf_counter() - start
    assert len(order) == n
    assert elapsed < 5.0, f"too slow: {elapsed:.2f}s"
    pos = {t: i for i, t in enumerate(order)}
    # every dependency must appear before its dependent (verified from the
    # test's own copy of the graph, not from solver internals)
    for node, deps in edges.items():
        for d in deps:
            assert pos[d] < pos[node], f"{d} not before {node}"


def test_large_graph_validity_true():
    rng = random.Random(8)
    s = Scheduler()
    for i in range(500):
        deps = [str(j) for j in range(i) if rng.random() < 0.01]
        s.add_task(Task(str(i), 1, deps))
    assert s.is_valid()
