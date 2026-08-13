# RealBench — Elysium Swarmloop: does it actually work?

Run: 2026-08-14 00:04:14

## Results per task × condition

| Task | Condition | Score | Tests | Wall | Tokens | Cost | Subagents | Skill | Delegate calls | Retries |
|------|-----------|-------|-------|------|--------|------|-----------|-------|-----------------|---------|
| hard_T01_mini_regex | baseline | **100.0** | 17/17 | 759.0s | 40183 | ~$0.000 | 0 | no | 0 | 0 |
| hard_T01_mini_regex | swarmloop | **100.0** | 17/17 | 997.4s | 115472 | ~$0.000 | 0 | yes | 0 | 0 |
| hard_T01_mini_regex | maxeffort | **100.0** | 17/17 | 398.9s | 89393 | ~$0.000 | 0 | yes | 0 | 0 |
| hard_T02_dag_executor | baseline | **100.0** | 12/12 | 201.7s | 17959 | ~$0.000 | 0 | no | 0 | 0 |
| hard_T03_service_suite_v2 | baseline | **100.0** | 34/34 | 627.4s | 41115 | ~$0.000 | 0 | no | 0 | 0 |
| hard_T03_service_suite_v2 | swarmloop | **97.1** | 33/34 | 452.9s | 101004 | ~$0.000 | 0 | yes | 0 | 0 |
| hard_T03_service_suite_v2 | maxeffort | **100.0** | 34/34 | 340.3s | 93988 | ~$0.000 | 0 | yes | 0 | 0 |
| hard_T03_service_suite_v2 | mesm | **97.1** | 33/34 | 310.6s | 90367 | ~$0.000 | 0 | yes | 0 | 0 |
| hard_T04_lfu_cache | baseline | **100.0** | 11/11 | 53.9s | 7339 | ~$0.000 | 0 | no | 0 | 0 |
| hard_T05_json_parser | baseline | **83.3** | 10/12 | 254.5s | 22226 | ~$0.000 | 0 | no | 0 | 0 |
| hard_T05_json_parser | swarmloop | **100.0** | 12/12 | 162.5s | 66138 | ~$0.000 | 0 | yes | 0 | 0 |
| hard_T05_json_parser | maxeffort | **100.0** | 12/12 | 206.3s | 72719 | ~$0.000 | 0 | yes | 0 | 0 |
| hard_T05_json_parser | mesm | **100.0** | 12/12 | 207.2s | 70042 | ~$0.000 | 0 | yes | 0 | 0 |
| hard_T06_segment_tree | baseline | **100.0** | 9/9 | 67.5s | 7535 | ~$0.000 | 0 | no | 0 | 0 |
| hard_T07_concurrent_token_bucket | baseline | **100.0** | 10/10 | 85.2s | 10822 | ~$0.000 | 0 | no | 0 | 0 |
| hard_T08_trie_autocomplete | baseline | **100.0** | 10/10 | 82.9s | 8782 | ~$0.000 | 0 | no | 0 | 0 |
| night_T01_binary_codec | baseline | **100.0** | 17/17 | 148.3s | 13163 | ~$0.000 | 0 | no | 0 | 0 |
| night_T02_btree | baseline | **100.0** | 13/13 | 332.4s | 23732 | ~$0.000 | 0 | no | 0 | 0 |
| night_T02_btree | swarmloop | **100.0** | 13/13 | 153.3s | 61098 | ~$0.000 | 0 | yes | 0 | 0 |
| night_T02_btree | maxeffort | **100.0** | 13/13 | 131.4s | 62274 | ~$0.000 | 0 | yes | 0 | 0 |

## Verdicts on the skill's claims

- ✅ **Benchmark discriminative (gold=100, junk<40, gap≥60)** — PASS: hard_T01_mini_regex: gold=100.0 junk=0.0; hard_T02_dag_executor: gold=100.0 junk=0.0; hard_T03_service_suite_v2: gold=100.0 junk=0.0; hard_T04_lfu_cache: gold=100.0 junk=0.0; hard_T05_json_parser: gold=100.0 junk=0.0; hard_T06_segment_tree: gold=100.0 junk=0.0; hard_T07_concurrent_token_bucket: gold=100.0 junk=0.0; hard_T08_trie_autocomplete: gold=100.0 junk=0.0; night_T01_binary_codec: gold=100.0 junk=0.0; night_T02_btree: gold=100.0 junk=0.0
- ✅ **hard_T01_mini_regex: control valid (baseline: no skill, no subagents)** — PASS: baseline skill_loaded=False subagents=0 (transcript-verified)
- ❌ **hard_T01_mini_regex [elysium base]: actually used subagents** — FAIL: delegate_calls=0 dispatched=0 batched=0 retries=0 skill_loaded=True
- ⚠️ **hard_T01_mini_regex [elysium base]: quality ≥ baseline** — INCONCLUSIVE: margin 0.0 pts (100.0 → 100.0) — within noise
- ❌ **hard_T01_mini_regex [elysium base]: wall-time ≤ baseline** — FAIL: base 759.0s vs elysium base 997.4s (1.3x slower)
- ℹ️ **hard_T01_mini_regex [elysium base]: cost accounting** — INFO: base ~$0.000/40183tok vs elysium base ~$0.000/115472tok
- ❌ **hard_T01_mini_regex [MAX EFFORT]: actually used subagents** — FAIL: delegate_calls=0 dispatched=0 batched=0 retries=0 skill_loaded=True
- ⚠️ **hard_T01_mini_regex [MAX EFFORT]: quality ≥ baseline** — INCONCLUSIVE: margin 0.0 pts (100.0 → 100.0) — within noise
- ✅ **hard_T01_mini_regex [MAX EFFORT]: wall-time ≤ baseline** — PASS: base 759.0s vs MAX EFFORT 398.9s
- ℹ️ **hard_T01_mini_regex [MAX EFFORT]: cost accounting** — INFO: base ~$0.000/40183tok vs MAX EFFORT ~$0.000/89393tok
- ✅ **hard_T02_dag_executor: control valid (baseline: no skill, no subagents)** — PASS: baseline skill_loaded=False subagents=0 (transcript-verified)
- ✅ **hard_T03_service_suite_v2: control valid (baseline: no skill, no subagents)** — PASS: baseline skill_loaded=False subagents=0 (transcript-verified)
- ❌ **hard_T03_service_suite_v2 [elysium base]: actually used subagents** — FAIL: delegate_calls=0 dispatched=0 batched=0 retries=0 skill_loaded=True
- ⚠️ **hard_T03_service_suite_v2 [elysium base]: quality ≥ baseline** — INCONCLUSIVE: margin -2.9 pts (100.0 → 97.1) — within noise
- ✅ **hard_T03_service_suite_v2 [elysium base]: wall-time ≤ baseline** — PASS: base 627.4s vs elysium base 452.9s
- ℹ️ **hard_T03_service_suite_v2 [elysium base]: cost accounting** — INFO: base ~$0.000/41115tok vs elysium base ~$0.000/101004tok
- ❌ **hard_T03_service_suite_v2 [MAX EFFORT]: actually used subagents** — FAIL: delegate_calls=0 dispatched=0 batched=0 retries=0 skill_loaded=True
- ⚠️ **hard_T03_service_suite_v2 [MAX EFFORT]: quality ≥ baseline** — INCONCLUSIVE: margin 0.0 pts (100.0 → 100.0) — within noise
- ✅ **hard_T03_service_suite_v2 [MAX EFFORT]: wall-time ≤ baseline** — PASS: base 627.4s vs MAX EFFORT 340.3s
- ℹ️ **hard_T03_service_suite_v2 [MAX EFFORT]: cost accounting** — INFO: base ~$0.000/41115tok vs MAX EFFORT ~$0.000/93988tok
- ❌ **hard_T03_service_suite_v2 [MESM]: actually used subagents** — FAIL: delegate_calls=0 dispatched=0 batched=0 retries=0 skill_loaded=True
- ⚠️ **hard_T03_service_suite_v2 [MESM]: quality ≥ baseline** — INCONCLUSIVE: margin -2.9 pts (100.0 → 97.1) — within noise
- ✅ **hard_T03_service_suite_v2 [MESM]: wall-time ≤ baseline** — PASS: base 627.4s vs MESM 310.6s
- ℹ️ **hard_T03_service_suite_v2 [MESM]: cost accounting** — INFO: base ~$0.000/41115tok vs MESM ~$0.000/90367tok
- ✅ **hard_T04_lfu_cache: control valid (baseline: no skill, no subagents)** — PASS: baseline skill_loaded=False subagents=0 (transcript-verified)
- ✅ **hard_T05_json_parser: control valid (baseline: no skill, no subagents)** — PASS: baseline skill_loaded=False subagents=0 (transcript-verified)
- ❌ **hard_T05_json_parser [elysium base]: actually used subagents** — FAIL: delegate_calls=0 dispatched=0 batched=0 retries=0 skill_loaded=True
- ✅ **hard_T05_json_parser [elysium base]: quality ≥ baseline** — PASS: elysium base +16.7 pts (83.3 → 100.0)
- ✅ **hard_T05_json_parser [elysium base]: wall-time ≤ baseline** — PASS: base 254.5s vs elysium base 162.5s
- ℹ️ **hard_T05_json_parser [elysium base]: cost accounting** — INFO: base ~$0.000/22226tok vs elysium base ~$0.000/66138tok
- ❌ **hard_T05_json_parser [MAX EFFORT]: actually used subagents** — FAIL: delegate_calls=0 dispatched=0 batched=0 retries=0 skill_loaded=True
- ✅ **hard_T05_json_parser [MAX EFFORT]: quality ≥ baseline** — PASS: MAX EFFORT +16.7 pts (83.3 → 100.0)
- ✅ **hard_T05_json_parser [MAX EFFORT]: wall-time ≤ baseline** — PASS: base 254.5s vs MAX EFFORT 206.3s
- ℹ️ **hard_T05_json_parser [MAX EFFORT]: cost accounting** — INFO: base ~$0.000/22226tok vs MAX EFFORT ~$0.000/72719tok
- ❌ **hard_T05_json_parser [MESM]: actually used subagents** — FAIL: delegate_calls=0 dispatched=0 batched=0 retries=0 skill_loaded=True
- ✅ **hard_T05_json_parser [MESM]: quality ≥ baseline** — PASS: MESM +16.7 pts (83.3 → 100.0)
- ✅ **hard_T05_json_parser [MESM]: wall-time ≤ baseline** — PASS: base 254.5s vs MESM 207.2s
- ℹ️ **hard_T05_json_parser [MESM]: cost accounting** — INFO: base ~$0.000/22226tok vs MESM ~$0.000/70042tok
- ✅ **hard_T06_segment_tree: control valid (baseline: no skill, no subagents)** — PASS: baseline skill_loaded=False subagents=0 (transcript-verified)
- ✅ **hard_T07_concurrent_token_bucket: control valid (baseline: no skill, no subagents)** — PASS: baseline skill_loaded=False subagents=0 (transcript-verified)
- ✅ **hard_T08_trie_autocomplete: control valid (baseline: no skill, no subagents)** — PASS: baseline skill_loaded=False subagents=0 (transcript-verified)
- ✅ **night_T01_binary_codec: control valid (baseline: no skill, no subagents)** — PASS: baseline skill_loaded=False subagents=0 (transcript-verified)
- ✅ **night_T02_btree: control valid (baseline: no skill, no subagents)** — PASS: baseline skill_loaded=False subagents=0 (transcript-verified)
- ❌ **night_T02_btree [elysium base]: actually used subagents** — FAIL: delegate_calls=0 dispatched=0 batched=0 retries=0 skill_loaded=True
- ⚠️ **night_T02_btree [elysium base]: quality ≥ baseline** — INCONCLUSIVE: margin 0.0 pts (100.0 → 100.0) — within noise
- ✅ **night_T02_btree [elysium base]: wall-time ≤ baseline** — PASS: base 332.4s vs elysium base 153.3s
- ℹ️ **night_T02_btree [elysium base]: cost accounting** — INFO: base ~$0.000/23732tok vs elysium base ~$0.000/61098tok
- ❌ **night_T02_btree [MAX EFFORT]: actually used subagents** — FAIL: delegate_calls=0 dispatched=0 batched=0 retries=0 skill_loaded=True
- ⚠️ **night_T02_btree [MAX EFFORT]: quality ≥ baseline** — INCONCLUSIVE: margin 0.0 pts (100.0 → 100.0) — within noise
- ✅ **night_T02_btree [MAX EFFORT]: wall-time ≤ baseline** — PASS: base 332.4s vs MAX EFFORT 131.4s
- ℹ️ **night_T02_btree [MAX EFFORT]: cost accounting** — INFO: base ~$0.000/23732tok vs MAX EFFORT ~$0.000/62274tok

## Limitations (read before quoting)

- N=1 per task × condition — pilot scale, no statistical power.
- Cost in USD unavailable: the configured provider reports no pricing
  data in Hermes' session tables; token counts are the cost proxy.
- The elysium conditions loaded the skill (verified via the session's
  system prompt hash) but the model NEVER dispatched subagents — not
  in base, MAX EFFORT, or MESM mode, not even on the 4-module parallel
  suite. The multi-agent claim is therefore untested-in-practice by
  this model on these tasks: all gains/losses come from the skill's
  single-agent structure (band filter, quality gates, self-check).
  An earlier forced-delegation experiment (extra_nudge) showed the
  skill CAN dispatch when the prompt explicitly demands it.
- Baseline tokens shown for the 4 matrix tasks; baseline runs of the
  other tasks came from probes (same setup).

## Calibration (benchmark integrity)

- hard_T01_mini_regex: gold=100.0 junk=None
- hard_T02_dag_executor: gold=100.0 junk=None
- hard_T03_service_suite_v2: gold=100.0 junk=None
- hard_T04_lfu_cache: gold=100.0 junk=None
- hard_T05_json_parser: gold=100.0 junk=None
- hard_T06_segment_tree: gold=100.0 junk=None
- hard_T07_concurrent_token_bucket: gold=100.0 junk=None
- hard_T08_trie_autocomplete: gold=100.0 junk=None
- night_T01_binary_codec: gold=100.0 junk=None
- night_T02_btree: gold=100.0 junk=None
