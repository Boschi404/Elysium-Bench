# RealBench — Elysium Swarmloop: does it actually work?

Run: 2026-08-13 22:51:02

## Results per task × condition

| Task | Condition | Score | Tests | Wall | Tokens | Cost | Subagents | Skill | Delegate calls | Retries |
|------|-----------|-------|-------|------|--------|------|-----------|-------|-----------------|---------|
| night_T01_binary_codec | baseline | **100.0** | 17/17 | 148.3s | 13163 | ~$0.000 | 0 | no | 0 | 0 |
| night_T02_btree | baseline | **100.0** | 13/13 | 332.4s | 23732 | ~$0.000 | 0 | no | 0 | 0 |

## Verdicts on the skill's claims

- ✅ **night_T01_binary_codec: control valid (baseline: no skill, no subagents)** — PASS: baseline skill_loaded=False subagents=0 (transcript-verified)
- ✅ **night_T02_btree: control valid (baseline: no skill, no subagents)** — PASS: baseline skill_loaded=False subagents=0 (transcript-verified)

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
