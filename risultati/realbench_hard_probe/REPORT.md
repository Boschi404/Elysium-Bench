# RealBench — Elysium Swarmloop: does it actually work?

Run: 2026-08-13 22:31:32

## Results per task × condition

| Task | Condition | Score | Tests | Wall | Tokens | Cost | Subagents | Skill | Delegate calls | Retries |
|------|-----------|-------|-------|------|--------|------|-----------|-------|-----------------|---------|
| hard_T01_mini_regex | baseline | **100.0** | 17/17 | 759.0s | 40183 | ~$0.000 | 0 | no | 0 | 0 |
| hard_T02_dag_executor | baseline | **100.0** | 12/12 | 201.7s | 17959 | ~$0.000 | 0 | no | 0 | 0 |
| hard_T03_service_suite_v2 | baseline | **100.0** | 34/34 | 627.4s | 41115 | ~$0.000 | 0 | no | 0 | 0 |
| hard_T04_lfu_cache | baseline | **100.0** | 11/11 | 53.9s | 7339 | ~$0.000 | 0 | no | 0 | 0 |
| hard_T05_json_parser | baseline | **83.3** | 10/12 | 254.5s | 22226 | ~$0.000 | 0 | no | 0 | 0 |
| hard_T06_segment_tree | baseline | **100.0** | 9/9 | 67.5s | 7535 | ~$0.000 | 0 | no | 0 | 0 |

## Verdicts on the skill's claims

- ✅ **hard_T01_mini_regex: control valid (baseline: no skill, no subagents)** — PASS: baseline skill_loaded=False subagents=0 (transcript-verified)
- ✅ **hard_T02_dag_executor: control valid (baseline: no skill, no subagents)** — PASS: baseline skill_loaded=False subagents=0 (transcript-verified)
- ✅ **hard_T03_service_suite_v2: control valid (baseline: no skill, no subagents)** — PASS: baseline skill_loaded=False subagents=0 (transcript-verified)
- ✅ **hard_T04_lfu_cache: control valid (baseline: no skill, no subagents)** — PASS: baseline skill_loaded=False subagents=0 (transcript-verified)
- ✅ **hard_T05_json_parser: control valid (baseline: no skill, no subagents)** — PASS: baseline skill_loaded=False subagents=0 (transcript-verified)
- ✅ **hard_T06_segment_tree: control valid (baseline: no skill, no subagents)** — PASS: baseline skill_loaded=False subagents=0 (transcript-verified)

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
