"""Hidden tests: DAG scheduler — exact values, brute-force cross-checks, scale."""
import itertools
import random
import time

import pytest

from dag import Dag


def _dag_from(spec: dict):
    d = Dag()
    for tid, (dur, deps) in spec.items():
        d.add_task(tid, dur, deps)
    return d


def test_simple_chain():
    d = _dag_from({"a": (3, []), "b": (4, ["a"]), "c": (2, ["b"])})
    assert d.topological_order() == ["a", "b", "c"]
    assert d.critical_path_length() == 9
    assert d.earliest_start("a") == 0
    assert d.earliest_start("b") == 3
    assert d.earliest_start("c") == 7
    assert d.latest_start("a") == 0
    assert d.latest_start("b") == 3
    assert d.latest_start("c") == 7


def test_diamond():
    # a(2) -> b(3), c(5) -> d(1)
    d = _dag_from({"a": (2, []), "b": (3, ["a"]), "c": (5, ["a"]),
                   "d": (1, ["b", "c"])})
    assert d.critical_path_length() == 8  # a+c+d
    assert d.earliest_start("d") == 7
    assert d.latest_start("d") == 7
    assert d.earliest_start("b") == 2
    assert d.latest_start("b") == 4  # b has slack
    assert d.earliest_start("c") == 2
    assert d.latest_start("c") == 2


def test_independent_parallel_branches():
    d = _dag_from({"a": (10, []), "b": (20, []), "c": (1, ["a"]),
                   "d": (1, ["b"])})
    assert d.critical_path_length() == 21  # b+d
    assert d.earliest_start("d") == 20
    assert d.latest_start("a") == 10  # a: CP 21 - longest from a (11) = 10
    assert d.latest_start("c") == 20


def test_lexicographic_tie_break():
    d = _dag_from({"b": (1, []), "a": (1, []), "c": (1, [])})
    assert d.topological_order() == ["a", "b", "c"]


def test_cycle_detection():
    d = _dag_from({"a": (1, ["b"]), "b": (1, ["a"])})
    assert not d.is_valid()
    with pytest.raises(ValueError):
        d.topological_order()
    with pytest.raises(ValueError):
        d.critical_path_length()


def test_self_loop_invalid():
    d = _dag_from({"a": (1, ["a"])})
    assert not d.is_valid()


def test_missing_dependency_invalid():
    d = _dag_from({"a": (1, ["ghost"])})
    assert not d.is_valid()
    with pytest.raises(ValueError):
        d.critical_path_length()


def test_unknown_id_keyerror():
    d = _dag_from({"a": (1, [])})
    with pytest.raises(KeyError):
        d.earliest_start("nope")
    with pytest.raises(KeyError):
        d.latest_start("nope")


def test_empty_dag():
    d = Dag()
    assert d.is_valid()
    assert d.topological_order() == []
    assert d.critical_path_length() == 0


def _bruteforce_longest(spec: dict) -> int:
    """Independent check: enumerate ALL paths (tiny graphs only)."""
    ids = set(spec)
    best = 0
    starts = [t for t, (_, deps) in spec.items() if not deps]
    def dfs(node, total, seen):
        nonlocal best
        total += spec[node][0]
        best = max(best, total)
        for nxt in ids:
            if node in spec[nxt][1] and nxt not in seen:
                dfs(nxt, total, seen | {nxt})
    for s in starts:
        dfs(s, 0, {s})
    return best


def test_random_small_graphs_vs_bruteforce():
    rng = random.Random(4242)
    for _ in range(20):
        n = rng.randint(2, 7)
        ids = [f"t{i}" for i in range(n)]
        spec = {}
        for i, tid in enumerate(ids):
            deps = [ids[j] for j in range(i) if rng.random() < 0.35]
            spec[tid] = (rng.randint(1, 9), deps)
        d = _dag_from(spec)
        assert d.critical_path_length() == _bruteforce_longest(spec), spec
        # ES property: every dep must finish before its dependent starts
        for tid, (dur, deps) in spec.items():
            for dep in deps:
                assert d.earliest_start(tid) >= d.earliest_start(dep) + spec[dep][0]


def test_random_graph_es_ls_property():
    rng = random.Random(777)
    for _ in range(10):
        n = rng.randint(3, 12)
        ids = [f"t{i}" for i in range(n)]
        spec = {}
        for i, tid in enumerate(ids):
            deps = [ids[j] for j in range(i) if rng.random() < 0.3]
            spec[tid] = (rng.randint(1, 9), deps)
        d = _dag_from(spec)
        cp = d.critical_path_length()
        for tid in ids:
            es, ls = d.earliest_start(tid), d.latest_start(tid)
            assert es <= ls <= cp
            # slack = ls - es; on at least one task slack == 0 (CP exists)
        assert any(d.latest_start(t) == d.earliest_start(t) for t in ids)


def test_perf_2000_nodes():
    rng = random.Random(9)
    d = Dag()
    n = 2000
    spec = {}
    for i in range(n):
        deps = [str(j) for j in range(max(0, i - 10), i) if rng.random() < 0.1]
        spec[str(i)] = (rng.randint(1, 100), deps)
        d.add_task(str(i), spec[str(i)][0], deps)
    start = time.perf_counter()
    order = d.topological_order()
    cp = d.critical_path_length()
    for t in (str(0), str(n // 2), str(n - 1)):
        d.earliest_start(t)
        d.latest_start(t)
    elapsed = time.perf_counter() - start
    assert len(order) == n
    assert cp > 0
    assert elapsed < 5.0, f"too slow: {elapsed:.2f}s"
