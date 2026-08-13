"""Re-collect session evidence from saved stdout.txt files.

The pilot ran with a broken skill-detection (system_prompts table wasn't
consulted). This script re-reads each run's saved session id and rebuilds
evidence with the fixed transcript.collect_evidence, then rewrites
results.json and REPORT.md. Baseline sessions whose isolated home was
overwritten by a later run are reported as lost.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from realbench.harness import DEFAULT_HERMES_HOME, RunResult
from realbench.report import evaluate_claims, write_report
from realbench.transcript import collect_evidence, parse_session_id_from_stdout

OUT = Path(__file__).resolve().parent.parent / "risultati" / (
    sys.argv[1] if len(sys.argv) > 1 else "realbench_pilot")
ISOLATED_ROOT = OUT / "_isolated_homes"

results: dict[str, dict[str, RunResult]] = {}
lost: list[str] = []

for task_dir in sorted(OUT.rglob("hard_*")) + sorted(OUT.rglob("code_*")) \
        + sorted(OUT.rglob("math_*")) + sorted(OUT.rglob("text_*")) \
        + sorted(OUT.rglob("night_*")):
    if not task_dir.is_dir() or "_isolated_homes" in task_dir.parts:
        continue
    task_id = task_dir.name
    results[task_id] = {}
    for cond_dir in [task_dir / c for c in
                     ("baseline", "swarmloop", "maxeffort", "mesm")
                     if (task_dir / c).exists()]:
        cond = cond_dir.name
        r = RunResult(task_id=task_id, condition=cond, workspace=cond_dir)
        stdout_file = cond_dir / "stdout.txt"
        stderr_file = cond_dir / "stderr.txt"
        raw = ""
        if stdout_file.exists():
            raw += stdout_file.read_text(encoding="utf-8", errors="ignore")
        if stderr_file.exists():
            raw += "\n" + stderr_file.read_text(encoding="utf-8", errors="ignore")
        r.session_id = parse_session_id_from_stdout(raw)
        if not r.session_id:
            lost.append(f"{task_id}/{cond}: no session id")
            results[task_id][cond] = r
            continue
        # which state.db holds this session?
        if cond == "baseline":
            db = (ISOLATED_ROOT / f"hermes_home_{task_id}_baseline"
                  / "hermes_home_isolated" / "state.db")
            if not db.exists():
                db = ISOLATED_ROOT / f"hermes_home_{task_id}_baseline" / "state.db"
        else:
            db = DEFAULT_HERMES_HOME / "state.db"
        r.evidence = collect_evidence(db, r.session_id)
        if not r.evidence.found:
            lost.append(f"{task_id}/{cond}: session {r.session_id} not found in {db.name}")
        results[task_id][cond] = r

# merge scores + wall times from the incremental results.jsonl (has ALL runs)
# plus the probe dirs' jsonl files (baselines live there)
jsonl_files = [OUT / "results.jsonl"]
for sibling in OUT.parent.glob("realbench_*probe*/results.jsonl"):
    if sibling != (OUT / "results.jsonl"):
        jsonl_files.append(sibling)
for pilot_jsonl in jsonl_files:
    if not pilot_jsonl.exists():
        continue
    for line in pilot_jsonl.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        data = json.loads(line)
        task_id, cond = data["task"], data["condition"]
        r = results.setdefault(task_id, {}).get(cond)
        if r is None:
            r = RunResult(task_id=task_id, condition=cond,
                          workspace=OUT / task_id / cond)
            results[task_id][cond] = r
        from realbench.scoring import ScoreResult
        if data.get("score") is not None:
            r.score = ScoreResult(
                task_id=task_id, score=data["score"], passed=data.get("passed", 0),
                failed=data.get("failed", 0),
                failed_test_names=data.get("failed_tests", []))
        r.elapsed_seconds = data.get("elapsed_seconds", 0.0)
        r.timed_out = bool(data.get("timed_out", False))
        r.session_id = data.get("session_id") or r.session_id
        r.notes = data.get("notes", [])

# summary of re-collected evidence
for task_id, conds in sorted(results.items()):
    for cond in ("baseline", "swarmloop", "maxeffort", "mesm"):
        r = conds.get(cond)
        if r and r.evidence:
            e = r.evidence
            print(f"{task_id:32s} {cond:9s} skill={e.skill_loaded!s:5s} "
                  f"delegate={e.delegate_calls} subagents={e.subagents_dispatched} "
                  f"retries={e.retries} toks={e.input_tokens + e.output_tokens} "
                  f"cost=${e.estimated_cost_usd}")

print("\nlost:", lost if lost else "none")

# calibration: re-grade gold for every task present in this pilot (fast)
from realbench.scoring import score_gold
from realbench.task_loader import get_task as _get_task

cal = {}
for task_id in sorted(results):
    try:
        g = score_gold(_get_task(task_id))
        cal[task_id] = {"gold": g.score}
    except Exception as e:  # noqa: BLE001
        cal[task_id] = {"gold": None, "note": str(e)}
print("\ncalibration:", {k: v["gold"] for k, v in cal.items()})

critic_meta = None
verdicts = evaluate_claims(results, cal, critic_meta)
md, js = write_report(results, verdicts, OUT, cal, critic_meta)

# ── merge the extra_nudge experiment into the report ──────────────────────
nudge_file = OUT / "extra_nudge" / "result.json"
if nudge_file.exists():
    nudge = json.loads(nudge_file.read_text(encoding="utf-8"))
    # results.json: add as extra condition for the task
    payload = json.loads(js.read_text(encoding="utf-8"))
    payload["tasks"].setdefault("code_T03_service_suite", {})
    payload["tasks"]["code_T03_service_suite"]["swarmloop+nudge"] = {
        "score": nudge["score"], "passed": nudge["passed"],
        "failed": nudge["failed"], "elapsed_seconds": nudge["wall"],
        "timed_out": nudge["timed_out"], "session_id": nudge["session_id"],
        "delegate_calls": nudge["delegate_calls"],
        "subagents_dispatched": nudge["subagents"],
        "batched_dispatches": nudge["batched"], "retries": nudge["retries"],
        "skill_loaded": nudge["skill_loaded"],
        "input_tokens": nudge["tokens"], "output_tokens": 0,
        "notes": ["supplementary run: explicit parallel-decomposition nudge"],
    }
    js.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    extra = [
        "",
        "## Supplementary experiment — explicit parallel-decomposition nudge",
        "",
        "Same task (code_T03_service_suite) and skill, but the prompt was changed",
        "to explicitly instruct: 'dispatch ONE subagent PER MODULE, all in",
        "parallel'. Result:",
        "",
        f"- score **{nudge['score']}** ({nudge['passed']}/{nudge['passed'] + nudge['failed']})",
        f"- wall {nudge['wall']}s — SLOWER than plain swarmloop (169.4s) and",
        "  baseline (70.6s)",
        f"- delegate_calls={nudge['delegate_calls']}, subagents={nudge['subagents']},",
        f"  batched={nudge['batched']} — one serial subagent, NOT the advertised",
        "  parallel batch of 4",
        f"- tokens={nudge['tokens']} (vs 62389 for plain swarmloop)",
        "",
        "Conclusion: the skill CAN dispatch subagents when pushed, but did not",
        "exploit the task's natural parallelism, and the result was slower with",
        "no quality gain over plain swarmloop.",
        "",
    ]
    md.write_text(md.read_text(encoding="utf-8") + "\n".join(extra), encoding="utf-8")

print(f"\nrewrote: {md.name}, {js.name}")
