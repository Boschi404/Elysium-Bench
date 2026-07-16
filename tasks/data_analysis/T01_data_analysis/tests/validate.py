"""Validation script for T01_data_analysis: SQL: Sales Report Query"""
import sys, os, json, re

solution_dir = os.environ.get("SOLUTION_DIR", ".")
score = 0.0

# Check for output files
output_files = list(__import__("pathlib").Path(solution_dir).rglob("*"))
sql_or_py_files = [f for f in output_files if f.suffix in (".sql", ".py") and not f.name.startswith("test_")]

if sql_or_py_files:
    content = sql_or_py_files[0].read_text(encoding="utf-8", errors="ignore")
    # Basic checks
    if len(content) > 20: score += 10
    if "SELECT" in content.upper() or "def " in content or "import " in content: score += 15
    if "FROM" in content.upper() or "groupby" in content.lower() or "merge" in content.lower(): score += 15
    print(f"SCORE: {score}")
else:
    print("SCORE: 0")
