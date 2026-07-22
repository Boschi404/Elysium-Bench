"""Test that DataScoringEngine now produces varying scores for different inputs."""
import sys, os, tempfile
sys.path.insert(0, '/c/Users/Admin/Elysium-Bench')
from elysium_bench.scoring import DataScoringEngine
from pathlib import Path

base = Path(tempfile.mkdtemp())
task_dir = base / 'task'
sol_good = base / 'sol_good'
sol_bad = base / 'sol_bad'
task_dir.mkdir()
sol_good.mkdir()
sol_bad.mkdir()

weights = {'correctness': 40, 'completeness': 25, 'efficiency': 15, 'robustness': 10, 'clarity': 10}

# GOOD solution: SQL + Pandas + error handling + comments
(sol_good / 'solution.py').write_text("""import pandas as pd
import numpy as np

# Query to get top customers
df = pd.read_sql('''
    SELECT customer_id, SUM(amount) as total
    FROM orders
    WHERE status = 'completed'
    GROUP BY customer_id
    ORDER BY total DESC
''', conn)

# Handle nulls
try:
    df = df[df['total'].notnull()]
except Exception as e:
    print(f'Error: {e}')
""")

# BAD solution: minimal
(sol_bad / 'solution.py').write_text("x = 1")

engine_good = DataScoringEngine(task_dir, sol_good, weights)
score_good = engine_good.evaluate()

engine_bad = DataScoringEngine(task_dir, sol_bad, weights)
score_bad = engine_bad.evaluate()

print(f"GOOD: corr={score_good.correctness} comp={score_good.completeness} eff={score_good.efficiency} rob={score_good.robustness} cla={score_good.clarity} total={score_good.total}")
print(f"BAD:  corr={score_bad.correctness} comp={score_bad.completeness} eff={score_bad.efficiency} rob={score_bad.robustness} cla={score_bad.clarity} total={score_bad.total}")
print(f"DELTA: {score_good.total} vs {score_bad.total} = {score_good.total - score_bad.total}")

if score_good.total != score_bad.total:
    print("✅ SCORER NOW VARIES — fix confirmed")
else:
    print("❌ SCORER STILL INVARIANT — fix not working")
