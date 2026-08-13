# RealBench — Elysium Swarmloop: does it actually work?

Run: 2026-08-13 22:34:42

## Results per task × condition

| Task | Condition | Score | Tests | Wall | Tokens | Cost | Subagents | Skill | Delegate calls | Retries |
|------|-----------|-------|-------|------|--------|------|-----------|-------|-----------------|---------|
| hard_T07_concurrent_token_bucket | baseline | **100.0** | 10/10 | 85.2s | 10822 | ~$0.000 | 0 | no | 0 | 0 |
| hard_T08_trie_autocomplete | baseline | **100.0** | 10/10 | 82.9s | 8782 | ~$0.000 | 0 | no | 0 | 0 |

## Verdicts on the skill's claims

- ✅ **hard_T07_concurrent_token_bucket: control valid (baseline: no skill, no subagents)** — PASS: baseline skill_loaded=False subagents=0 (transcript-verified)
- ✅ **hard_T08_trie_autocomplete: control valid (baseline: no skill, no subagents)** — PASS: baseline skill_loaded=False subagents=0 (transcript-verified)

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
