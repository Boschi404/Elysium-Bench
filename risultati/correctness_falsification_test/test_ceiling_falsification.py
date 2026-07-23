"""
Ceiling effect falsification test for CodeScoringEngine._evaluate_functional()
Hypothesis: correctness=40.0 because ALL tests pass (ceiling effect, not bug)
Test: create deliberately BROKEN solutions where tests FAIL, check if correctness drops
"""
import sys, os, json, subprocess, tempfile, shutil
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
from elysium_bench.scoring import CodeScoringEngine

TASK_DIR = Path('tasks/api_development/T01_api_development').resolve()
WORKSPACE_BASE = Path(tempfile.mkdtemp(prefix='falsify_'))
WEIGHTS = {'correctness': 40, 'completeness': 25, 'efficiency': 15, 'robustness': 10, 'clarity': 10}

results = []

# ── BROKEN SOLUTION 1: Syntax error ──
sol1_dir = WORKSPACE_BASE / 'broken_syntax'
sol1_dir.mkdir()
(sol1_dir / 'main.py').write_text('''
from fastapi import FastAPI
app = FastAPI()
@app.get("/users")
def get_users(
    return [{"id": 1, "name": "Alice"}]
''')
shutil.copytree(str(TASK_DIR / 'tests'), str(sol1_dir / 'tests'))

# ── BROKEN SOLUTION 2: Wrong return type ──
sol2_dir = WORKSPACE_BASE / 'broken_return'
sol2_dir.mkdir()
(sol2_dir / 'main.py').write_text('''
from fastapi import FastAPI
app = FastAPI()
@app.get("/users")
def get_users():
    return "not json"
@app.get("/")
def root():
    return "hello"
''')
shutil.copytree(str(TASK_DIR / 'tests'), str(sol2_dir / 'tests'))

# ── BROKEN SOLUTION 3: Minimal stub (no routes) ──
sol3_dir = WORKSPACE_BASE / 'minimal_stub'
sol3_dir.mkdir()
(sol3_dir / 'main.py').write_text('''
from fastapi import FastAPI
app = FastAPI()
''')
shutil.copytree(str(TASK_DIR / 'tests'), str(sol3_dir / 'tests'))

solutions = [
    ("BROKEN_SYNTAX (import fails)", sol1_dir),
    ("BROKEN_RETURN (wrong content-type)", sol2_dir),
    ("MINIMAL_STUB (no routes)", sol3_dir),
]

for label, sol_dir in solutions:
    print(f"\n{'='*60}")
    print(f"Testing: {label}")
    print(f"{'='*60}")
    
    try:
        engine = CodeScoringEngine(TASK_DIR, sol_dir, WEIGHTS)
        score = engine.evaluate()
        
        print(f"  correctness: {score.correctness}")
        print(f"  completeness: {score.completeness}")
        print(f"  efficiency: {score.efficiency}")
        print(f"  robustness: {score.robustness}")
        print(f"  clarity: {score.clarity}")
        print(f"  TOTAL: {score.total}")
        print(f"  PASSED: {score.passed}")
        
        # Run pytest manually to see what happened
        result = subprocess.run(
            [sys.executable, "-m", "pytest", str(sol_dir / "tests"), "-q", "--tb=short"],
            capture_output=True, text=True, timeout=30,
            cwd=str(sol_dir),
        )
        print(f"  pytest returncode: {result.returncode}")
        print(f"  pytest stdout: {result.stdout[:300]}")
        
        results.append({
            "label": label,
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
    except Exception as e:
        print(f"  ERROR: {e}")
        results.append({"label": label, "error": str(e)})

# ── Analysis ──
print("\n" + "="*60)
print("ANALYSIS")
print("="*60)

correctness_values = [r.get("correctness", -1) for r in results if "error" not in r]
print(f"Correctness scores: {correctness_values}")

if all(v == 40.0 for v in correctness_values):
    print("\n❌ HYPOTHESIS FALSIFIED: even BROKEN solutions get correctness=40.0")
    print("   The correctness scorer is BROKEN, not just a ceiling effect.")
elif all(v == 0.0 for v in correctness_values):
    print("\n⚠️ All broken solutions get 0.0 — tests may not have been found.")
elif len(set(correctness_values)) > 1:
    print(f"\n✅ HYPOTHESIS CONFIRMED: correctness VARIES ({set(correctness_values)})")
    print("   Broken solutions get lower scores → ceiling effect confirmed.")
else:
    print(f"\n⚠️ All values identical ({correctness_values[0]}) — inconclusive.")

# Save results
output_file = Path('risultati/correctness_falsification_test/results.json').resolve()
output_file.write_text(json.dumps(results, indent=2, default=str), encoding='utf-8')
print(f"\nResults saved to: {output_file}")
