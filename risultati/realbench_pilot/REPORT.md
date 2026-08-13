# RealBench — Elysium Swarmloop: does it actually work?

Run: 2026-08-13 20:32:50

## Results per task × condition

| Task | Condition | Score | Tests | Wall | Tokens | Cost | Subagents | Skill | Delegate calls | Retries |
|------|-----------|-------|-------|------|--------|------|-----------|-------|-----------------|---------|
| code_T01_lru_cache | baseline | **100.0** | 9/9 | 60.5s | n/a | ~$n/a | n/a | n/a | n/a | n/a |
| code_T01_lru_cache | swarmloop | **100.0** | 9/9 | 148.6s | 49331 | ~$0.000 | 0 | yes | 0 | 0 |
| code_T03_service_suite | baseline | **96.2** | 25/26 | 70.6s | n/a | ~$n/a | n/a | n/a | n/a | n/a |
| code_T03_service_suite | swarmloop | **100.0** | 26/26 | 169.4s | 62389 | ~$0.000 | 0 | yes | 0 | 0 |
| math_T01_knapsack | baseline | **100.0** | 9/9 | 72.4s | n/a | ~$n/a | n/a | n/a | n/a | n/a |
| math_T01_knapsack | swarmloop | **100.0** | 9/9 | 68.7s | 49762 | ~$0.000 | 0 | yes | 0 | 0 |

## Verdicts on the skill's claims

- ✅ **Benchmark discriminative (gold=100, junk<40, gap≥60)** — PASS: code_T01_lru_cache: gold=100.0 junk=0.0; math_T01_knapsack: gold=100.0 junk=0.0; code_T03_service_suite: gold=100.0 junk=0.0
- ⚠️ **code_T01_lru_cache: control valid (baseline: no skill, no subagents)** — INCONCLUSIVE: baseline session evidence lost (isolated db overwritten — harness bug, fixed); delegation was impossible by construction (-t file,terminal removes the delegation toolset)
- ❌ **code_T01_lru_cache: swarmloop actually used subagents** — FAIL: delegate_calls=0 dispatched=0 batched=0 retries=0 skill_loaded=True
- ⚠️ **code_T01_lru_cache: swarmloop quality ≥ baseline** — INCONCLUSIVE: margin 0.0 pts (100.0 → 100.0) — within noise
- ❌ **code_T01_lru_cache: swarmloop wall-time ≤ baseline** — FAIL: base 60.5s vs swarm 148.6s (2.5x slower)
- ℹ️ **code_T01_lru_cache: cost accounting** — INFO: base n/a vs swarm ~$0.000/49331tok
- ⚠️ **code_T03_service_suite: control valid (baseline: no skill, no subagents)** — INCONCLUSIVE: baseline session evidence lost (isolated db overwritten — harness bug, fixed); delegation was impossible by construction (-t file,terminal removes the delegation toolset)
- ❌ **code_T03_service_suite: swarmloop actually used subagents** — FAIL: delegate_calls=0 dispatched=0 batched=0 retries=0 skill_loaded=True
- ⚠️ **code_T03_service_suite: swarmloop quality ≥ baseline** — INCONCLUSIVE: margin 3.8 pts (96.2 → 100.0) — within noise
- ❌ **code_T03_service_suite: swarmloop wall-time ≤ baseline** — FAIL: base 70.6s vs swarm 169.4s (2.4x slower)
- ℹ️ **code_T03_service_suite: cost accounting** — INFO: base n/a vs swarm ~$0.000/62389tok
- ⚠️ **math_T01_knapsack: control valid (baseline: no skill, no subagents)** — INCONCLUSIVE: baseline session evidence lost (isolated db overwritten — harness bug, fixed); delegation was impossible by construction (-t file,terminal removes the delegation toolset)
- ❌ **math_T01_knapsack: swarmloop actually used subagents** — FAIL: delegate_calls=0 dispatched=0 batched=0 retries=0 skill_loaded=True
- ⚠️ **math_T01_knapsack: swarmloop quality ≥ baseline** — INCONCLUSIVE: margin 0.0 pts (100.0 → 100.0) — within noise
- ✅ **math_T01_knapsack: swarmloop wall-time ≤ baseline** — PASS: base 72.4s vs swarm 68.7s
- ℹ️ **math_T01_knapsack: cost accounting** — INFO: base n/a vs swarm ~$0.000/49762tok
- ✅ **Blind critic valid (gold ranked > junk)** — PASS: gold=99.0 junk=22.0 margin=77.0

## Limitations (read before quoting)

- N=1 per task × condition — pilot scale, no statistical power.
- Baseline token/cost evidence lost for this pilot run (isolated
  state.db was overwritten between baseline runs — harness bug, fixed
  in the current code; future runs keep a unique isolated home per run).
- Delegation was nonetheless IMPOSSIBLE for the baseline by
  construction: the `-t file,terminal` toolset removes delegate_task.
- Cost in USD unavailable: the configured provider reports no pricing
  data in Hermes' session tables; token counts are the cost proxy.
- The swarmloop condition loaded the skill (verified via the session's
  system prompt hash) but the model chose to solve every pilot task
  directly without dispatching subagents — including the 4-module
  parallel suite. See the extra_nudge experiment for a stronger prompt.

## Calibration (benchmark integrity)

- code_T01_lru_cache: gold=100.0 junk=None
- math_T01_knapsack: gold=100.0 junk=None
- code_T03_service_suite: gold=100.0 junk=None

## Critic meta-check

{
  "ok": true,
  "gold_score": 99.0,
  "junk_score": 22.0,
  "margin": 77.0,
  "elapsed_seconds": 169.1
}

## Supplementary experiment — explicit parallel-decomposition nudge

Same task (code_T03_service_suite) and skill, but the prompt was changed
to explicitly instruct: 'dispatch ONE subagent PER MODULE, all in
parallel'. Result:

- score **100.0** (26/26)
- wall 196.2s — SLOWER than plain swarmloop (169.4s) and
  baseline (70.6s)
- delegate_calls=1, subagents=1,
  batched=0 — one serial subagent, NOT the advertised
  parallel batch of 4
- tokens=55783 (vs 62389 for plain swarmloop)

Conclusion: the skill CAN dispatch subagents when pushed, but did not
exploit the task's natural parallelism, and the result was slower with
no quality gain over plain swarmloop.
