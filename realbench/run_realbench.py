#!/usr/bin/env python
"""RealBench CLI — run the benchmark that actually tests Elysium Swarmloop.

Usage:
  python realbench/run_realbench.py --tasks code_T01_lru_cache,math_T01_knapsack \
      --conditions baseline,swarmloop --timeout 900 --max-turns 15
  python realbench/run_realbench.py --calibrate            # gold/junk integrity
  python realbench/run_realbench.py --validate-critic      # critic meta-check
  python realbench/run_realbench.py --selfcheck            # harness self-tests
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

REALBENCH_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(REALBENCH_DIR.parent))

from realbench.harness import DEFAULT_HERMES_HOME, run_condition
from realbench.report import evaluate_claims, write_report
from realbench.scoring import score_gold
from realbench.task_loader import discover_tasks, get_task


def run_benchmark(args) -> int:
    tasks = discover_tasks()
    if args.tasks == "all":
        selected = tasks
    else:
        selected = {tid: get_task(tid) for tid in args.tasks.split(",")}

    conds = args.conditions.split(",")
    out_root = Path(args.out_dir)
    out_root.mkdir(parents=True, exist_ok=True)
    isolated_homes = out_root / "_isolated_homes"
    isolated_homes.mkdir(parents=True, exist_ok=True)
    state_db = DEFAULT_HERMES_HOME / "state.db"

    print(f"🧪 RealBench — tasks={list(selected)} conditions={conds}")
    print(f"   HERMES_HOME={DEFAULT_HERMES_HOME} state.db={state_db.exists()}")
    print(f"   timeout={args.timeout}s max_turns={args.max_turns}\n")

    results: dict[str, dict] = {}
    jsonl_path = out_root / "results.jsonl"
    for task_id in selected:
        results[task_id] = {}
        for cond in conds:
            task_dir = out_root / task_id / cond
            print(f"▶ {task_id} [{cond}] ...", flush=True)
            t0 = time.time()
            r = run_condition(
                task=selected[task_id], condition=cond, out_dir=task_dir,
                hermes_home=DEFAULT_HERMES_HOME,
                timeout=args.timeout, max_turns=args.max_turns,
                isolated_homes_dir=isolated_homes,
            )
            results[task_id][cond] = r
            s = r.score.score if r.score else "?"
            ev = r.evidence
            print(f"   score={s} wall={r.elapsed_seconds}s "
                  f"subagents={ev.subagents_dispatched if ev else '?'} "
                  f"skill={ev.skill_loaded if ev else '?'} "
                  f"cost=~${ev.estimated_cost_usd if ev else '?'} "
                  f"({time.time() - t0:.0f}s)")
            if r.notes:
                for n in r.notes:
                    print(f"   ⚠ {n}")
            # incremental durability: append after every condition
            rec = {
                "task": task_id, "condition": cond,
                "score": r.score.score if r.score else None,
                "passed": r.score.passed if r.score else 0,
                "failed": r.score.failed if r.score else 0,
                "elapsed_seconds": r.elapsed_seconds,
                "timed_out": r.timed_out,
                "session_id": r.session_id,
                "skill_loaded": ev.skill_loaded if ev else None,
                "delegate_calls": ev.delegate_calls if ev else None,
                "subagents": ev.subagents_dispatched if ev else None,
                "batched": ev.batched_dispatches if ev else None,
                "retries": ev.retries if ev else None,
                "tokens": (ev.input_tokens + ev.output_tokens) if ev else None,
                "estimated_cost_usd": ev.estimated_cost_usd if ev else None,
                "notes": r.notes,
            }
            with open(jsonl_path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec) + "\n")

    calibration = None
    if args.calibrate:
        print("\n🔬 Calibration (gold vs junk)...")
        calibration = {}
        for task_id in selected:
            gold = score_gold(selected[task_id])
            calibration[task_id] = {"gold": gold.score,
                                    "gold_detail": gold.gap or f"{gold.passed}/{gold.passed + gold.failed}"}
            print(f"   {task_id}: gold={gold.score}")

    critic_meta = None
    if args.validate_critic:
        from realbench.critic import validate_critic
        from realbench.task_loader import TASKS_DIR
        tdir = TASKS_DIR / "text_T01_code_review"
        print("\n🧐 Validating blind critic (gold vs junk)...")
        ok, meta = validate_critic(tdir, DEFAULT_HERMES_HOME, isolated_homes,
                                   timeout=args.critic_timeout)
        critic_meta = {"ok": ok, **meta}
        print(f"   critic {'VALID' if ok else 'INVALID'}: {meta}")

    verdicts = evaluate_claims(results, calibration, critic_meta)
    md_path, json_path = write_report(results, verdicts, out_root,
                                      calibration, critic_meta)
    print(f"\n📄 Report: {md_path}")
    print(f"📄 Data:   {json_path}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="RealBench runner")
    ap.add_argument("--tasks", default="code_T01_lru_cache",
                    help="comma-separated task ids or 'all'")
    ap.add_argument("--conditions", default="baseline,swarmloop")
    ap.add_argument("--timeout", type=int, default=900, help="per-run wall seconds")
    ap.add_argument("--max-turns", type=int, default=15)
    ap.add_argument("--out-dir", default=str(Path.home() / "Downloads" / "Elysium-Bench" / "risultati" / "realbench"))
    ap.add_argument("--calibrate", action="store_true", help="also grade gold solutions")
    ap.add_argument("--validate-critic", action="store_true")
    ap.add_argument("--critic-timeout", type=int, default=480)
    ap.add_argument("--selfcheck", action="store_true",
                    help="run harness self-tests and exit")
    args = ap.parse_args()

    if args.selfcheck:
        import subprocess as sp
        r = sp.run([sys.executable, "-m", "pytest",
                    str(REALBENCH_DIR / "tests"), "-q"], cwd=str(REALBENCH_DIR))
        return r.returncode
    return run_benchmark(args)


if __name__ == "__main__":
    sys.exit(main())
