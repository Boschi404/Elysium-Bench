"""
Ceiling effect CONFIRMATION test: run scorer on a CORRECT solution
If correctness=40.0 → ceiling effect confirmed (all tests pass → max score)
If correctness<40.0 → bug in scorer (tests pass but score not given)
"""
import sys, os, json, subprocess, tempfile, shutil
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
from elysium_bench.scoring import CodeScoringEngine

TASK_DIR = Path('tasks/api_development/T01_api_development').resolve()
CORRECT_SOL = Path('workspace_test').resolve()
WEIGHTS = {'correctness': 40, 'completeness': 25, 'efficiency': 15, 'robustness': 10, 'clarity': 10}

results = []

# ── CORRECT SOLUTION: real FastAPI CRUD ──
print(f"\n{'='*60}")
print(f"Testing: CORRECT SOLUTION (workspace_test/main.py)")
print(f"{'='*60}")

# First, copy tests to solution dir so pytest can find them
import tempfile as tmp
sol_dir = Path(tmp.mkdtemp(prefix='correct_'))
shutil.copytree(str(CORRECT_SOL), str(sol_dir / 'workspace'), dirs_exist_ok=True)
shutil.copytree(str(TASK_DIR / 'tests'), str(sol_dir / 'workspace' / 'tests'), dirs_exist_ok=True)

# Run pytest
result = subprocess.run(
    [sys.executable, "-m", "pytest", str(sol_dir / 'workspace' / 'tests'), "-q", "--tb=short"],
    capture_output=True, text=True, timeout=30,
    cwd=str(sol_dir / 'workspace'),
)
print(f"  pytest returncode: {result.returncode}")
print(f"  pytest stdout:\n{result.stdout[:500]}")

# Now score
engine = CodeScoringEngine(TASK_DIR, sol_dir / 'workspace', WEIGHTS)
score = engine.evaluate()

print(f"\n  correctness: {score.correctness}")
print(f"  completeness: {score.completeness}")
print(f"  efficiency: {score.efficiency}")
print(f"  robustness: {score.robustness}")
print(f"  clarity: {score.clarity}")
print(f"  TOTAL: {score.total}")
print(f"  PASSED: {score.passed}")

results.append({
    "label": "CORRECT_SOLUTION (workspace_test)",
    "correctness": score.correctness,
    "completeness": score.completeness,
    "efficiency": score.efficiency,
    "robustness": score.robustness,
    "clarity": score.clarity,
    "total": score.total,
    "passed": score.passed,
    "pytest_returncode": result.returncode,
    "pytest_stdout": result.stdout[:500],
})

# ── Analysis ──
print(f"\n{'='*60}")
print("ANALYSIS")
print(f"{'='*60}")
print(f"Correctness: {score.correctness}")
print(f"Pytest returncode: {result.returncode} (0=pass, 1=fail)")

if result.returncode == 0 and score.correctness == 40.0:
    print("\n✅ CEILING EFFECT CONFIRMED:")
    print("   Tests all pass → correctness = max_score (40.0)")
    print("   The scorer IS working. The problem is that ALL benchmark")
    print("   solutions pass ALL tests → correctness is always 40.0")
    print("   This is NOT a bug — it's a ceiling effect.")
elif result.returncode == 0 and score.correctness < 40.0:
    print("\n❌ BUG CONFIRMED:")
    print("   Tests pass but correctness < 40.0 — scorer not giving full credit")
elif result.returncode != 0 and score.correctness == 40.0:
    print("\n❌ BUG CONFIRMED:")
    print("   Tests FAIL but correctness = 40.0 — scorer ignoring failures")
else:
    print(f"\n⚠️ UNEXPECTED: tests fail ({result.returncode}) and correctness={score.correctness}")

# Save
output_file = Path('risultati/correctness_falsification_test/correct_solution_result.json').resolve()
output_file.write_text(json.dumps(results, indent=2, default=str), encoding='utf-8')
print(f"\nResults saved to: {output_file}")
