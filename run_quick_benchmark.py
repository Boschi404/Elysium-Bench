"""Elysium-Bench Quick Runner — 10-Minute Benchmark
Uses the benchmark's scoring engine + direct Hermes CLI calls.
No baseline — focuses on measuring Elysium improvement across loops."""

import json
import shutil
import subprocess
import sys
import time
import yaml
from pathlib import Path

# Add project to path
BENCH_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(BENCH_DIR))

from elysium_bench.scoring import ScoringEngine, ScoreBreakdown
from elysium_bench.task_registry import TaskRegistry

RESULTS_DIR = BENCH_DIR / "results"
TASKS_DIR = BENCH_DIR / "tasks"
WORKSPACES_DIR = BENCH_DIR / "workspaces"
CONFIG_PATH = BENCH_DIR / "config_10min.yaml"

# Load config
config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
weights = {k: v["weight"] for k, v in config["scoring"].items()}
thresholds = config["thresholds"]
learning_min = thresholds["learning_min"]

# ─── Workspace Setup ────────────────────────────────────────────────
def create_workspace(task_dir: Path, task_id: str, loop: str) -> Path:
    ws = WORKSPACES_DIR / f"{task_id}_{loop}"
    if ws.exists():
        shutil.rmtree(ws)
    ws.mkdir(parents=True, exist_ok=True)
    
    # Create workspace/ subdir (where solution goes)
    (ws / "workspace").mkdir(exist_ok=True)
    
    # Copy tests
    test_dir = task_dir / "tests"
    if test_dir.exists():
        dest = ws / "workspace" / "tests"
        shutil.copytree(test_dir, dest, dirs_exist_ok=True)
        print(f"  📋 Copiati test da {test_dir}")
    
    # Copy repo starter files if they exist
    repo_dir = task_dir / "repo"
    if repo_dir.exists():
        for f in repo_dir.iterdir():
            shutil.copy2(f, ws / "workspace")
            print(f"  📁 Copiato repo/{f.name}")
    
    return ws


def solve_task(task_id: str, task_name: str, description: str, workspace: Path) -> dict:
    """Solve a task using Hermes CLI with Elysium skill."""
    ws_path = workspace / "workspace"
    
    prompt = f"""TASK: {task_id} - {task_name}
DESCRIPTION: {description}

WORKSPACE: {ws_path}

INSTRUCTIONS:
1. Solve this task completely in the workspace directory
2. Write ALL code to {ws_path}/
3. Ensure all tests in the {ws_path / "tests"}/ directory pass (if tests exist)
4. Use FastAPI with proper Pydantic validation
5. Return ONLY a brief summary of what you implemented
6. IMPORTANT: actually CREATE the files - write the complete code

SKILL: elysium-swarmloop
"""
    
    print(f"  ⏳ Invio a Hermes + Elysium...")
    start = time.time()
    
    try:
        result = subprocess.run(
            ["hermes", "chat", "-q", prompt, "--skills", "elysium-swarmloop", "-Q"],
            capture_output=True, text=True, timeout=360,
        )
        elapsed = time.time() - start
        
        # Check if solution files were created
        py_files = list(ws_path.glob("*.py"))
        
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "success": result.returncode == 0,
            "elapsed": round(elapsed, 1),
            "files_created": [str(f.relative_to(ws_path)) for f in py_files],
            "mode": "hermes_elysium",
        }
    except subprocess.TimeoutExpired:
        elapsed = time.time() - start
        return {
            "stdout": "", "stderr": "Timeout",
            "returncode": -1, "success": False,
            "elapsed": round(elapsed, 1),
            "files_created": [],
            "mode": "timeout",
        }


def score_task(task_dir: Path, workspace: Path) -> ScoreBreakdown:
    """Score a completed task using the benchmark's scoring engine."""
    solution_dir = workspace / "workspace"
    engine = ScoringEngine(
        task_dir=task_dir,
        solution_dir=solution_dir,
        weights=weights,
    )
    score = engine.evaluate()
    return score


def run_tests(workspace: Path) -> dict:
    """Run pytest on the workspace to check tests."""
    ws = workspace / "workspace"
    test_dir = ws / "tests"
    if not test_dir.exists():
        return {"passed": 0, "total": 0, "output": "No tests"}
    
    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(test_dir), "-q", "--tb=short"],
        capture_output=True, text=True, timeout=60,
        cwd=str(ws),
    )
    
    import re
    match_passed = re.search(r"(\d+)\s+passed", result.stdout)
    match_failed = re.search(r"(\d+)\s+failed", result.stdout)
    passed = int(match_passed.group(1)) if match_passed else 0
    failed = int(match_failed.group(1)) if match_failed else 0
    # If returncode is 0, all tests passed
    if result.returncode == 0 and match_passed:
        failed = 0
        passed = int(match_passed.group(1))
    return {"passed": passed, "total": passed + failed, "output": result.stdout}


# ═══════════════════════════════════════════════════════════════════
# MAIN BENCHMARK
# ═══════════════════════════════════════════════════════════════════

print(f"""
┌────────────────────────────────────────────────────────┐
│ 🚀 Elysium-Bench Quick Run (10 min)                   │
│ Elysium Swarmloop Skill — 3 tasks × 2 loops + Re-Test │
└────────────────────────────────────────────────────────┘
""")

# Discover tasks
registry = TaskRegistry(TASKS_DIR, config)
categories = registry.discover()
all_tasks = []
for cat in categories:
    all_tasks.extend(cat.tasks)
    print(f"  📂 {cat.name}: {len(cat.tasks)} tasks")

# Select tasks for loops
task_1 = next(t for t in all_tasks if t.id == "T01_api_development")  # T01
task_2 = next(t for t in all_tasks if t.id == "T02_api_development")  # T02

print(f"\n  🎯 Loop 1: {task_1.id} — {task_1.name}")
print(f"  🎯 Loop 2: {task_2.id} — {task_2.name}")
print(f"  🔁 Re-Test: {task_1.id} (same as Loop 1)")

results = {
    "benchmark": "Elysium-Bench Quick",
    "version": "0.4.1-quick",
    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    "skill": "elysium-swarmloop",
    "scores": {},
    "tests": {},
    "duration": {},
}

start_time = time.time()

# ─── LOOP 1: T01 with Elysium ─────────────────────────────────────
print(f"\n{'─'*60}")
print(f"  🔬 PHASE 1: LOOP 1 — Measurement Task WITH Elysium")
print(f"{'─'*60}")

task1_dir = task_1.task_dir
ws1 = create_workspace(task1_dir, task_1.id.replace("/", "_"), "loop1")
result1 = solve_task(task_1.id, task_1.name, task_1.description, ws1)
score1 = score_task(task1_dir, ws1)
tests1 = run_tests(ws1)

print(f"  ✅ Score: {score1.total:.1f}/100 | Files: {result1['files_created']}")
print(f"  📊 Tests: {tests1['passed']}/{tests1['total']} passed")
print(f"  ⏱  {result1['elapsed']}s | Mode: {result1['mode']}")

results["scores"]["loop1"] = score1.to_dict()
results["scores"]["loop1"]["total"] = round(score1.total, 1)
results["tests"]["loop1"] = tests1
results["duration"]["loop1"] = result1["elapsed"]

# ─── LOOP 2: T02 with Elysium ─────────────────────────────────────
print(f"\n{'─'*60}")
print(f"  🔄 PHASE 2: LOOP 2 — Practice Task WITH Elysium")
print(f"{'─'*60}")

ws2 = create_workspace(task_2.task_dir, task_2.id.replace("/", "_"), "loop2")
result2 = solve_task(task_2.id, task_2.name, task_2.description, ws2)
score2 = score_task(task_2.task_dir, ws2)
tests2 = run_tests(ws2)

print(f"  ✅ Score: {score2.total:.1f}/100 | Files: {result2['files_created']}")
print(f"  📊 Tests: {tests2['passed']}/{tests2['total']} passed")
print(f"  ⏱  {result2['elapsed']}s | Mode: {result2['mode']}")

results["scores"]["loop2"] = score2.to_dict()
results["scores"]["loop2"]["total"] = round(score2.total, 1)
results["tests"]["loop2"] = tests2
results["duration"]["loop2"] = result2["elapsed"]

# ─── RE-TEST: T01 again with Elysium ──────────────────────────────
print(f"\n{'─'*60}")
print(f"  🔁 PHASE 3: RE-TEST — Same task as Loop 1 WITH Elysium")
print(f"{'─'*60}")

ws1r = create_workspace(task1_dir, task_1.id.replace("/", "_"), "retest")
result1r = solve_task(task_1.id, task_1.name, task_1.description, ws1r)
score1r = score_task(task1_dir, ws1r)
tests1r = run_tests(ws1r)

print(f"  ✅ Score: {score1r.total:.1f}/100 | Files: {result1r['files_created']}")
print(f"  📊 Tests: {tests1r['passed']}/{tests1r['total']} passed")
print(f"  ⏱  {result1r['elapsed']}s | Mode: {result1r['mode']}")

results["scores"]["retest"] = score1r.to_dict()
results["scores"]["retest"]["total"] = round(score1r.total, 1)
results["tests"]["retest"] = tests1r
results["duration"]["retest"] = result1r["elapsed"]

# ─── CALCULATE IMPROVEMENT ────────────────────────────────────────
total_elapsed = time.time() - start_time
print(f"\n{'═'*60}")
print(f"  📊 FINAL RESULTS")
print(f"{'═'*60}")

loop1_total = score1.total
loop2_total = score2.total
retest_total = score1r.total

delta_l1_rt = retest_total - loop1_total
delta_l1_l2 = loop2_total - loop1_total
pct_improvement = ((retest_total - loop1_total) / loop1_total * 100) if loop1_total > 0 else 0
improved = pct_improvement >= learning_min

print(f"\n  {'Phase':<30} {'Score':<10} {'Δ':<10}")
print(f"  {'─'*50}")
print(f"  {'Loop 1 (T01 - first pass)':<30} {loop1_total:<10.1f} {'—':<10}")
print(f"  {'Loop 2 (T02 - practice)':<30} {loop2_total:<10.1f} {delta_l1_l2:>+6.1f}")
print(f"  {'Re-Test (T01 - after practice)':<30} {retest_total:<10.1f} {delta_l1_rt:>+6.1f}")
print(f"")
print(f"  {'Δ Re-Test vs Loop 1':<30} {delta_l1_rt:>+6.1f} {'📈' if delta_l1_rt > 0 else '📉' if delta_l1_rt < 0 else '➡️'}")
print(f"  {'Improvement Detected':<30} {'✅ YES' if improved else '❌ NO'}")
print(f"  {'Total Duration':<30} {total_elapsed/60:.1f} min ({total_elapsed:.0f}s)")

# Build final report
report = {
    "benchmark": "Elysium-Bench Quick",
    "version": "0.4.1-quick",
    "timestamp": results["timestamp"],
    "duration_minutes": round(total_elapsed / 60, 1),
    "duration_seconds": round(total_elapsed, 1),
    "skill_used": "elysium-swarmloop",
    "categories_tested": ["api_development"],
    "tasks": {
        "loop1": {
            "task_id": task_1.id,
            "name": task_1.name,
            "difficulty": task_1.difficulty,
            "score": round(loop1_total, 1),
            "tests": tests1,
            "duration_s": result1["elapsed"],
        },
        "loop2": {
            "task_id": task_2.id,
            "name": task_2.name,
            "difficulty": task_2.difficulty,
            "score": round(loop2_total, 1),
            "tests": tests2,
            "duration_s": result2["elapsed"],
        },
        "retest": {
            "task_id": task_1.id,
            "name": task_1.name,
            "difficulty": task_1.difficulty,
            "score": round(retest_total, 1),
            "tests": tests1r,
            "duration_s": result1r["elapsed"],
        },
    },
    "improvement": {
        "delta_retest_vs_loop1": round(delta_l1_rt, 1),
        "delta_loop2_vs_loop1": round(delta_l1_l2, 1),
        "improvement_pct": round(pct_improvement, 1),
        "learning_detected": improved,
        "learning_threshold_pct": learning_min,
    },
    "hermes_config": config.get("hermes", {}),
}

# Save JSON
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
json_path = RESULTS_DIR / f"quick_results_{time.strftime('%Y%m%d_%H%M%S')}.json"
json_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
print(f"\n  📁 Results saved: {json_path}")

# Cleanup workspaces
shutil.rmtree(WORKSPACES_DIR, ignore_errors=True)
print(f"  🧹 Workspaces cleaned")

print(f"\n  ✅ Benchmark complete!\n")
