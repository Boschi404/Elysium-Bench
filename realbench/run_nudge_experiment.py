"""Supplementary experiment: swarmloop with an EXPLICIT parallel-decomposition
nudge. If the skill still dispatches no subagents, the multi-agent claim is
tested at its strongest fair prompt.
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from realbench.harness import (
    DEFAULT_HERMES_HOME, RunResult, _isolated_home, prepare_workspace, run_condition)
from realbench.scoring import score_workspace
from realbench.task_loader import get_task
from realbench.transcript import collect_evidence, parse_session_id_from_stdout
from realbench.harness import build_prompt

import os
import subprocess

TASK = get_task("code_T03_service_suite")
OUT = Path(__file__).resolve().parent.parent / "risultati" / "realbench_pilot" / "extra_nudge"

OUT.mkdir(parents=True, exist_ok=True)
ws = prepare_workspace(TASK, OUT)
iso_parent = OUT / "_isolated"

base = build_prompt(TASK, ws, "swarmloop")
nudge = base.replace(
    "You have the elysium-swarmloop skill loaded. You may decompose the "
    "task and dispatch parallel subagents via delegate_task — if you do, "
    "every subagent MUST also write its deliverable into the exact "
    "directory above. Judge the final files against the spec before "
    "replying DONE.",
    "You have the elysium-swarmloop skill loaded. This task has FOUR "
    "INDEPENDENT modules (parser, validator, store, api). USE IT AS "
    "DESIGNED: dispatch ONE subagent PER MODULE, all in parallel via "
    "delegate_task — every subagent MUST write its deliverable into the "
    "exact directory above. Then integrate and judge the final files "
    "against the spec before replying DONE.")
(OUT / "prompt.txt").write_text(nudge, encoding="utf-8")

cmd = ["hermes", "chat", "-q", nudge, "-Q", "--pass-session-id",
       "--max-turns", "20", "-s", "elysium-swarmloop"]
env = dict(os.environ)
env["HERMES_HOME"] = str(DEFAULT_HERMES_HOME)

start = time.time()
try:
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=1500, env=env)
    stdout, stderr = proc.stdout or "", proc.stderr or ""
    timed_out = False
except subprocess.TimeoutExpired:
    stdout, stderr, timed_out = "", "TIMEOUT", True
elapsed = round(time.time() - start, 1)
(OUT / "stdout.txt").write_text(stdout, encoding="utf-8", errors="ignore")
(OUT / "stderr.txt").write_text(stderr, encoding="utf-8", errors="ignore")

sid = parse_session_id_from_stdout(stdout + "\n" + stderr)
ev = collect_evidence(DEFAULT_HERMES_HOME / "state.db", sid) if sid else None
sc = score_workspace(TASK, ws)

print("score:", sc.score, f"{sc.passed}/{sc.passed + sc.failed}")
print("session:", sid)
if ev:
    print(f"skill={ev.skill_loaded} delegate_calls={ev.delegate_calls} "
          f"subagents={ev.subagents_dispatched} batched={ev.batched_dispatches} "
          f"retries={ev.retries} tokens={ev.input_tokens + ev.output_tokens} "
          f"cost=${ev.estimated_cost_usd}")
print("wall:", elapsed, "timed_out:", timed_out)

(OUT / "result.json").write_text(json.dumps({
    "task": TASK.id, "condition": "swarmloop+nudge", "score": sc.score,
    "passed": sc.passed, "failed": sc.failed, "wall": elapsed,
    "timed_out": timed_out, "session_id": sid,
    "skill_loaded": ev.skill_loaded if ev else None,
    "delegate_calls": ev.delegate_calls if ev else None,
    "subagents": ev.subagents_dispatched if ev else None,
    "batched": ev.batched_dispatches if ev else None,
    "retries": ev.retries if ev else None,
    "tokens": (ev.input_tokens + ev.output_tokens) if ev else None,
}, indent=2), encoding="utf-8")
