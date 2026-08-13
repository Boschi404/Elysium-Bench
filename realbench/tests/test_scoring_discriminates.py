"""THE core test: the hidden graders must actually discriminate.

gold → 100 (solvability proven)
junk → ≈0 (gaming impossible)
weak/partial → strictly between (difficulty gradient exists)

This is the exact property the original Elysium-Bench lacked (ceiling effect:
every solution scored 40/40 because tests swallowed all exceptions).
"""
import shutil
import tempfile
from pathlib import Path

import pytest

from realbench.scoring import score_workspace
from realbench.task_loader import discover_tasks

TASKS = discover_tasks()

JUNK = {
    "code_T01_lru_cache": "lru.py",
    "code_T02_task_scheduler": "scheduler.py",
    "code_T03_service_suite": None,  # handled specially below
    "code_T04_bug_hunt": None,       # empty workspace = junk
    "math_T01_knapsack": "knapsack.py",
}

JUNK_SOURCES = {
    "code_T01_lru_cache": """
class LRUCache:
    def __init__(self, capacity): self.c = capacity
    def get(self, key): return -1
    def put(self, key, value): pass
""",
    "code_T02_task_scheduler": """
class Task:
    def __init__(self, id, priority, deps=None): pass
class Scheduler:
    def __init__(self): pass
    def add_task(self, task): pass
    def run_order(self): return []
    def is_valid(self): return True
    def detect_cycle(self): return []
""",
    "math_T01_knapsack": """
def solve_knapsack(values, weights, capacity):
    return 0
""",
}

# a weak-but-sane knapsack: greedy by value density (fails exactness)
GREEDY_KNAPSACK = """
def solve_knapsack(values, weights, capacity):
    items = sorted(range(len(values)),
                   key=lambda i: values[i] / weights[i], reverse=True)
    total_v = 0
    total_w = 0
    for i in items:
        if total_w + weights[i] <= capacity:
            total_w += weights[i]
            total_v += values[i]
    return total_v
"""


def _ws_with(files: dict[str, str]) -> Path:
    tmp = tempfile.mkdtemp(prefix="realbench_junk_")
    ws = Path(tmp)
    for name, content in files.items():
        (ws / name).write_text(content)
    return ws


@pytest.mark.parametrize("task_id", list(JUNK))
def test_junk_scores_low(task_id):
    """A degenerate solution must score FAR below gold. (Easy sanity tests —
    e.g. 'missing key returns -1' or a no-op perf test — may legitimately
    pass even for a stub; what matters is the gap to gold.)"""
    task = TASKS[task_id]
    junk_file = JUNK[task_id]
    if junk_file is None or junk_file not in JUNK_SOURCES:
        # junk = totally empty workspace (nothing implemented at all)
        ws = _ws_with({})
    else:
        ws = _ws_with({junk_file: JUNK_SOURCES[junk_file]})
    res = score_workspace(task, ws)
    shutil.rmtree(ws)
    from realbench.scoring import score_gold
    gold = score_gold(task).score
    assert res.score < 40, f"{task_id}: junk scored {res.score} — grader is gameable"
    assert gold - res.score >= 60, (
        f"{task_id}: gold={gold} junk={res.score} — gap too small to discriminate")


@pytest.mark.parametrize("task_id", ["code_T01_lru_cache", "code_T02_task_scheduler",
                                     "code_T04_bug_hunt", "math_T01_knapsack",
                                     "code_T03_service_suite"])
def test_gold_scores_full(task_id):
    from realbench.scoring import score_gold
    res = score_gold(TASKS[task_id])
    assert res.score >= 99.0, (
        f"{task_id}: gold scored {res.score} "
        f"({res.passed}/{res.passed + res.failed}) — task/tests broken: {res.gap} "
        f"{res.failed_test_names[:5]}")


def test_knapsack_gradient_exists():
    """Greedy (weak) must score strictly between junk and gold."""
    task = TASKS["math_T01_knapsack"]
    ws = _ws_with({"knapsack.py": GREEDY_KNAPSACK})
    res = score_workspace(task, ws)
    shutil.rmtree(ws)
    assert 0 < res.score < 99, f"greedy scored {res.score} — no gradient"


def test_bug_hunt_gradient_exists():
    """Unfixed repo (sanity passes, bugs remain) must score partial."""
    task = TASKS["code_T04_bug_hunt"]
    tmp = tempfile.mkdtemp(prefix="realbench_bugs_")
    ws = Path(tmp)
    for f in task.repo_dir.iterdir():
        if f.is_file():
            shutil.copy2(f, ws / f.name)
    res = score_workspace(task, ws)
    shutil.rmtree(ws)
    assert 0 < res.score < 99, f"unfixed repo scored {res.score} — no partial credit"


def test_service_suite_gradient_exists():
    """3 of 4 gold modules + missing api → partial, not 0, not 100."""
    task = TASKS["code_T03_service_suite"]
    tmp = tempfile.mkdtemp(prefix="realbench_svc_")
    ws = Path(tmp)
    for f in task.gold_dir.iterdir():
        if f.is_file() and f.name != "api.py":
            shutil.copy2(f, ws / f.name)
    res = score_workspace(task, ws)
    shutil.rmtree(ws)
    assert 0 < res.score < 99, f"partial suite scored {res.score}"


def test_hidden_tests_never_ship_to_solver():
    from realbench.harness import prepare_workspace
    task = TASKS["code_T01_lru_cache"]
    tmp = Path(tempfile.mkdtemp(prefix="realbench_prep_"))
    ws = prepare_workspace(task, tmp)
    names = {p.name for p in ws.rglob("*")}
    shutil.rmtree(tmp)
    assert "test_hidden.py" not in names, "hidden tests leaked into workspace"
    assert "expected_optimums.json" not in names
