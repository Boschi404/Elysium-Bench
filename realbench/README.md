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

## The two conditions

- **baseline** — `hermes chat` with an isolated `HERMES_HOME` (zero skills
  installed, so elysium cannot load) and `-t file,terminal` (delegation
  toolset removed, subagents physically impossible). Prompt forbids
  delegation. Transcript is checked: if the skill loaded or subagents were
  used, the control is flagged FAIL.
- **swarmloop** — `hermes chat -s elysium-swarmloop`, full toolset, prompt
  invites decomposition + parallel subagents. Transcript is checked: the
  claim "multi-agent" is verified against actual `delegate_task` evidence.

## Tasks (all with hidden tests, difficulty gradient)

| Task | Type | Diff | Discriminates |
|---|---|---|---|
| `code_T01_lru_cache` | O(1) LRU cache | 3 | 100k-op perf test kills O(n) scans; random trace vs reference |
| `code_T02_task_scheduler` | Priority DAG scheduler | 5 | Exact order, cycles, 1000-node graph |
| `code_T03_service_suite` | 4 independent modules + contracts | 7 | Per-module partial credit; integration tests; **parallelism showcase** |
| `code_T04_bug_hunt` | 3 planted bugs across 3 files | 6 | One hidden test per bug — partial credit per fix |
| `math_T01_knapsack` | Exact 0/1 knapsack | 5 | Instances generated at grading time; greedy fails; text-scan useless |
| `text_T01_code_review` | Review of a flawed auth diff | 6 | Blind critic + meta-check (gold vs junk) |

## Claims under test

1. **Control valid** — baseline used no skill, no subagents.
2. **Multi-agent** — swarmloop actually dispatched subagents (verified).
3. **Quality** — swarmloop score ≥ baseline score (margin ≥10 = PASS,
   ≤-10 = FAIL, else INCONCLUSIVE).
4. **Wall-time** — swarmloop ≤ 1.25× baseline.
5. **Cost** — cost per point of score for both conditions.
6. **Benchmark discriminative** — every task: gold=100, junk<40, gap≥60.
7. **Critic valid** — blind critic ranks gold review above junk review.

## Usage

```bash
# 1. Harness self-tests (no LLM calls): graders must discriminate
python realbench/run_realbench.py --selfcheck

# 2. Full pilot: 3 tasks × 2 conditions with real Hermes runs
python realbench/run_realbench.py \
  --tasks code_T01_lru_cache,math_T01_knapsack,code_T03_service_suite \
  --conditions baseline,swarmloop --timeout 1500 --max-turns 15 \
  --calibrate --validate-critic --out-dir risultati/realbench_pilot

# 3. All tasks
python realbench/run_realbench.py --tasks all --conditions baseline,swarmloop
```

Results land in `REPORT.md` + `results.json` (per-task × per-condition:
score, tests passed, wall time, tokens, cost, subagents, delegate calls,
retries, verdicts).

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
