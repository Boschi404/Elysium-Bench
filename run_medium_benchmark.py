"""Elysium-Bench Medium Runner — 15-Minute Benchmark
4 categories × 3 loops + Re-Test = 16 tasks
Uses benchmark ScoringEngine + direct Hermes CLI calls."""

import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

BENCH_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(BENCH_DIR))

from elysium_bench.scoring import ScoringEngine
from elysium_bench.task_registry import TaskRegistry

RESULTS_DIR = BENCH_DIR / "results"
TASKS_DIR = BENCH_DIR / "tasks"
WORKSPACES_DIR = BENCH_DIR / "workspaces"

# ─── CONFIG ──────────────────────────────────────────────────────────
CATEGORIES = [
    "api_development",
    "bug_fixing",
    "algorithm_implementation",
    "data_analysis",
]
TOTAL_LOOPS = 3  # Loop 1 (measurement) + Loop 2-3 (practice)
TASKS_PER_CAT = TOTAL_LOOPS + 1  # T01-T04 per category (enough for loops)

WEIGHTS = {"correctness": 40, "completeness": 25, "efficiency": 15, "robustness": 10, "clarity": 10}


# ─── HELPERS ─────────────────────────────────────────────────────────
def clean_workspace():
    if WORKSPACES_DIR.exists():
        shutil.rmtree(WORKSPACES_DIR)
    WORKSPACES_DIR.mkdir(parents=True)


def create_workspace(task_dir: Path, task_id: str, tag: str) -> Path:
    ws = WORKSPACES_DIR / f"{task_id}_{tag}"
    if ws.exists():
        shutil.rmtree(ws)
    ws.mkdir(parents=True)
    (ws / "workspace").mkdir()

    # Copy tests
    test_dir = task_dir / "tests"
    if test_dir.exists():
        dest = ws / "workspace" / "tests"
        shutil.copytree(test_dir, dest, dirs_exist_ok=True)

    # Copy repo starter files
    repo_dir = task_dir / "repo"
    if repo_dir.exists():
        for f in repo_dir.iterdir():
            shutil.copy2(f, ws / "workspace")
    return ws


def solve_task(task, workspace: Path) -> dict:
    ws_path = workspace / "workspace"
    prompt = (
        f"TASK: {task.id} - {task.name}\n"
        f"DESCRIPTION: {task.description}\n"
        f"WORKSPACE: {ws_path}\n\n"
        f"INSTRUCTIONS:\n"
        f"1. Solve this task completely\n"
        f"2. Write ALL solution files to {ws_path}/\n"
        f"3. Ensure tests in {ws_path / 'tests'}/ pass\n"
        f"4. Use appropriate libraries/frameworks\n"
        f"5. Return a brief summary\n"
        f"SKILL: elysium-swarmloop\n"
    )
    start = time.time()
    try:
        result = subprocess.run(
            ["hermes", "chat", "-q", prompt, "--skills", "elysium-swarmloop", "-Q"],
            capture_output=True, text=True, timeout=360,
        )
        elapsed = time.time() - start
        py_files = list(ws_path.rglob("*.py"))
        return {
            "stdout": result.stdout, "stderr": result.stderr,
            "returncode": result.returncode,
            "success": result.returncode == 0,
            "elapsed": round(elapsed, 1),
            "files_created": [str(f.relative_to(ws_path)) for f in py_files],
            "mode": "hermes_elysium",
        }
    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": "Timeout", "returncode": -1,
                "success": False, "elapsed": round(time.time() - start, 1),
                "files_created": [], "mode": "timeout"}


def score_task(task_dir: Path, workspace: Path):
    solution_dir = workspace / "workspace"
    engine = ScoringEngine(task_dir=task_dir, solution_dir=solution_dir, weights=WEIGHTS)
    return engine.evaluate()


def run_tests(workspace: Path) -> dict:
    ws = workspace / "workspace"
    test_dir = ws / "tests"
    if not test_dir.exists():
        return {"passed": 0, "total": 0, "output": "No tests"}
    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(test_dir), "-q", "--tb=short"],
        capture_output=True, text=True, timeout=60, cwd=str(ws),
    )
    m_pass = re.search(r"(\d+)\s+passed", result.stdout)
    m_fail = re.search(r"(\d+)\s+failed", result.stdout)
    passed = int(m_pass.group(1)) if m_pass else 0
    failed = int(m_fail.group(1)) if m_fail else 0
    if result.returncode == 0 and m_pass:
        passed = int(m_pass.group(1))
        failed = 0
    return {"passed": passed, "total": passed + failed, "output": result.stdout}


def fmt_score(s) -> str:
    return f"{s.total:.1f}"


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

print(f"""
┌───────────────────────────────────────────────────────────────┐
│ 🚀 Elysium-Bench Medium (15 min)                             │
│ {len(CATEGORIES)} categorie × {TOTAL_LOOPS} loop + Re-Test      │
└───────────────────────────────────────────────────────────────┘
""")

# Discover tasks
config = {"categories": [{"id": c, "name": c, "description": "", "weight": 1.0} for c in CATEGORIES]}
registry = TaskRegistry(TASKS_DIR, config)
categories = registry.discover()

# Build task map: category → {task_idx: Task}
all_tasks = {}
for cat in categories:
    cat_tasks = {}
    for t in cat.tasks:
        # Extract number from T01, T02, etc.
        m = re.match(r"T(\d+)", t.id)
        if m:
            idx = int(m.group(1))
            cat_tasks[idx] = t
    all_tasks[cat.id] = cat_tasks
    print(f"  📂 {cat.name}: {len(cat_tasks)} tasks disponibili")

clean_workspace()
all_results = {
    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    "categories": CATEGORIES,
    "total_loops": TOTAL_LOOPS,
    "skill": "elysium-swarmloop",
    "loops": {},
    "improvement": {},
}
start_all = time.time()

# ─── LOOPS ────────────────────────────────────────────────────────────
for loop_num in range(1, TOTAL_LOOPS + 2):  # 1, 2, 3, 4 (4 = re-test)
    is_retest = loop_num == TOTAL_LOOPS + 1
    task_idx = 1 if is_retest else loop_num  # Re-test = T01 again

    phase_name = f"LOOP {loop_num} (measurement)" if loop_num == 1 else (
        f"RE-TEST (Loop 1 tasks)" if is_retest else f"LOOP {loop_num} (practice)")
    emoji = "🔬" if loop_num == 1 else ("🔁" if is_retest else "🔄")

    print(f"\n{'─'*60}")
    print(f"  {emoji} PHASE {loop_num}: {phase_name}")
    print(f"{'─'*60}")

    loop_scores = {}
    for cat_id in CATEGORIES:
        task = all_tasks[cat_id].get(task_idx)
        if not task:
            print(f"  ⚠️  {cat_id}: task T{task_idx:02d} non trovato, skippo")
            continue

        print(f"\n  📌 {task.id}: {task.name} (diff={task.difficulty})")

        ws = create_workspace(task.task_dir, task.id.replace("/", "_"), f"loop{loop_num}")
        result = solve_task(task, ws)
        score = score_task(task.task_dir, ws)
        tests = run_tests(ws)

        score_data = score.to_dict()
        score_data["total"] = round(score.total, 1)
        score_data["duration_s"] = result["elapsed"]
        score_data["tests"] = tests
        score_data["files"] = result["files_created"]

        loop_scores[task.id] = score_data

        icon = "✅" if score.passed else "❌"
        print(f"    Score: {fmt_score(score)}/100 {icon}")
        print(f"    Tests: {tests['passed']}/{tests['total']} | "
              f"Files: {result['files_created']} | ⏱ {result['elapsed']}s")

    key = f"loop{loop_num}" if not is_retest else "retest"
    all_results["loops"][key] = loop_scores

# ─── REPORT ───────────────────────────────────────────────────────────
total_elapsed = time.time() - start_all
print(f"\n{'═'*60}")
print(f"  📊 FINAL REPORT")
print(f"{'═'*60}")

# Log results per category
print(f"\n  {'Category':<30} {'Loop 1':<10} {'Loop 2':<10} {'Loop 3':<10} {'Re-Test':<10} {'Δ':<10}")
print(f"  {'─'*70}")

improvements = {}

for cat_id in CATEGORIES:
    t1_id = f"T01_{cat_id}"
    t2_id = f"T02_{cat_id}"
    t3_id = f"T03_{cat_id}"
    row = [cat_id]

    l1 = all_results["loops"]["loop1"].get(t1_id, {}).get("total", 0)
    l2 = all_results["loops"]["loop2"].get(t2_id, {}).get("total", 0)
    l3 = all_results["loops"]["loop3"].get(t3_id, {}).get("total", 0)
    rt = all_results["loops"]["retest"].get(t1_id, {}).get("total", 0)
    
    row.extend([f"{l1:.1f}", f"{l2:.1f}", f"{l3:.1f}", f"{rt:.1f}"])
    
    delta = rt - l1
    improvements[cat_id] = delta
    d_icon = "📈" if delta > 0 else ("📉" if delta < 0 else "➡️")
    row.append(f"{d_icon} {delta:+.1f}")
    
    print(f"  {row[0]:<30} {row[1]:<10} {row[2]:<10} {row[3]:<10} {row[4]:<10} {row[5]:<10}")

# Summary
print(f"\n  {'─'*50}")
l1_avg = sum(
    all_results["loops"]["loop1"].get(f"T01_{c}", {}).get("total", 0) for c in CATEGORIES
) / len(CATEGORIES)
rt_avg = sum(
    all_results["loops"]["retest"].get(f"T01_{c}", {}).get("total", 0) for c in CATEGORIES
) / len(CATEGORIES)
delta_avg = rt_avg - l1_avg
pct_improvement = ((rt_avg - l1_avg) / l1_avg * 100) if l1_avg > 0 else 0
learning_detected = pct_improvement >= 5

print(f"  {'Loop 1 Avg':<30} {l1_avg:<10.1f}")
print(f"  {'Re-Test Avg':<30} {rt_avg:<10.1f}")
print(f"  {'Δ Re-Test vs Loop 1':<30} {delta_avg:>+6.1f}")
print(f"  {'Improvement Detected':<30} {'✅ YES' if learning_detected else '❌ NO'}")
print(f"  {'Total Duration':<30} {total_elapsed/60:.1f} min ({total_elapsed:.0f}s)")
print(f"  {'Total Tasks':<30} {sum(len(v) for v in all_results['loops'].values())}")

# Build JSON report
report = {
    "benchmark": "Elysium-Bench Medium",
    "version": "0.4.1-medium",
    "timestamp": all_results["timestamp"],
    "duration_minutes": round(total_elapsed / 60, 1),
    "duration_seconds": round(total_elapsed, 1),
    "skill": "elysium-swarmloop",
    "categories": CATEGORIES,
    "total_loops": TOTAL_LOOPS,
    "per_category_improvement": {
        c: round(d, 1) for c, d in improvements.items()
    },
    "averages": {
        "loop1": round(l1_avg, 1),
        "retest": round(rt_avg, 1),
        "delta": round(delta_avg, 1),
        "improvement_pct": round(pct_improvement, 1),
        "learning_detected": learning_detected,
    },
    "loops": all_results["loops"],
}

# Save
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
ts = time.strftime("%Y%m%d_%H%M%S")
json_path = RESULTS_DIR / f"medium_results_{ts}.json"
json_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
print(f"\n  📁 Saved: {json_path}")

# Cleanup
clean_workspace()
print(f"  🧹 Workspaces cleaned")
print(f"\n  ✅ Benchmark complete!\n")
