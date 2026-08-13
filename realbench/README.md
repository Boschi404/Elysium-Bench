# RealBench — the benchmark that actually tests Elysium Swarmloop

> The original Elysium-Bench graded "binary search" with tests that never
> called binary search, swallowed exceptions with `except: pass`, and gave
> 40/40 correctness to any module containing any function. RealBench replaces
> it with hidden, execution-based graders and a controlled experiment that
> verifies the swarmloop's claims against objective evidence.

## What's different

| | Elysium-Bench (old) | RealBench |
|---|---|---|
| Correctness signal | pytest with exception-swallowing tests → ceiling 40/40 for everyone | Hidden tests run against real behavior: gold=100, junk≈0, gradient in between |
| Grading style | grep (TODO, `try:`, `->`) + self-reported scores | Execution only. Partial credit per test, per module, per bug |
| "Multi-agent" evidence | Assumed | Verified from Hermes' own session DB: `delegate_task` calls, dispatched count, batches, retries |
| Control group | None (baseline = empty workspace) | Plain Hermes agent, no skill, delegation toolset physically removed |
| Cost | Not measured | Real tokens/cost from `sessions`/`session_model_usage` tables |
| Open-ended tasks | Keyword rubrics | Blind LLM critic with a meta-check: if it can't rank gold > junk, its scores are discarded |
| Harness quality | Untested | 30 self-tests incl. grader-discrimination proofs (gold=100, junk<40, gap≥60) |

## The two tiers

- **basic** (`code_*`, `math_*`, `text_*`) — difficulty 3-7. Easy enough that a
  plain agent scores ~100 (that was the original benchmark's ceiling problem).
- **hard** (`hard_*`) — difficulty 7-9: regex engine, DAG critical-path
  analysis, expression language (lexer+parser+eval+repl), LFU cache, strict
  JSON codec, segment tree. Baseline scores must land well below 100 — these
  are the tasks where Elysium's claimed advantages can actually show up.

## The four conditions

- **baseline** — plain Hermes agent, no skill (isolated `HERMES_HOME` with
  zero skills), delegation toolset removed, prompt forbids subagents.
- **swarmloop** — `hermes chat -s elysium-swarmloop` (elysium base mode).
- **maxeffort** — same, with the exact `MAX EFFORT` trigger on the first
  prompt line (activates the skill's Quality-First Mode: threshold 9/10,
  9 iterations, global re-check).
- **mesm** — same, with the exact `MESM` trigger (Quality-First + Swarmloop
  Mode intensified: threshold 9.5/10, 5 rounds, blind A/B, sandbox racing;
  the skill's own docs call this the most expensive configuration).
  The prompt pre-confirms the pre-flight cost check and round check-ins
  (benchmark auto-approval) so the run cannot stall waiting for a human.

## Claims under test

For each elysium mode vs baseline, per task:
1. **Control valid** — baseline used no skill, no subagents (transcript).
2. **Multi-agent** — the mode actually dispatched subagents (verified from
   the session DB: delegate calls, batches, retries).
3. **Quality** — score ≥ baseline (margin ≥10 = PASS, ≤-10 = FAIL).
4. **Wall-time** — ≤ 1.25× baseline.
5. **Cost** — tokens and cost per condition (informational).
6. **Benchmark discriminative** — every task: gold=100, junk<40, gap≥60.
7. **Critic valid** — blind critic ranks gold review above junk review.

## Usage

```bash
# 1. Harness self-tests (no LLM calls): graders must discriminate
python realbench/run_realbench.py --selfcheck

# 2. Difficulty probe: baseline scores on the hard tier must be < 100
python realbench/run_realbench.py \
  --tasks hard_T01_mini_regex,hard_T02_dag_executor,hard_T03_service_suite_v2 \
  --conditions baseline --timeout 1200 --max-turns 15 \
  --out-dir risultati/realbench_hard_probe

# 3. Full matrix: 4 conditions × hard tasks (MESM is slow/expensive)
python realbench/run_realbench.py \
  --tasks hard_T01_mini_regex,hard_T02_dag_executor,hard_T03_service_suite_v2 \
  --conditions baseline,swarmloop,maxeffort,mesm --timeout 2400 --max-turns 20 \
  --calibrate --out-dir risultati/realbench_hard_pilot
```

Results land in `REPORT.md` + `results.json` + `results.jsonl`
(incremental — one line per completed condition).

## How honesty is enforced

- **Hidden tests are copied into the workspace only at scoring time** —
  verified by self-test `test_hidden_tests_never_ship_to_solver`.
- **Anti-gaming**: knapsack instances are generated at grading time from
  fixed seeds (hardcoding impossible); test-suite answers cannot be
  extracted from the task description.
- **No self-reported scores**: the only score source is executed tests or
  the blind critic (which is itself validated).
- **Subagent claims are audited**: transcript/db evidence, not the agent's
  own summary.
- **If the harness can't measure something, it says so** (`INCONCLUSIVE`,
  `gap` fields) instead of inventing a number.
