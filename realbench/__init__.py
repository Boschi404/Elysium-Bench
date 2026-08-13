"""RealBench — a benchmark that actually tests whether Elysium Swarmloop works.

Design principles (vs the original Elysium-Bench):
1. Objective, hidden, discriminating graders — every code/math task is graded
   by executing a hidden test suite the solver never sees. No self-reported
   scores, no grep-scoring, no ceiling effect (gold=100, junk≈0).
2. Difficulty gradient + anti-gaming instances (generated at grading time).
3. Two conditions measured under identical setup:
   - baseline:  plain Hermes agent, NO skill, NO delegation toolset
   - swarmloop: Hermes agent with elysium-swarmloop preloaded + delegation
4. Subagent usage is VERIFIED from the session database (delegate_task calls,
   batches, retries), not self-reported.
5. Cost accounting from Hermes' own session tables (tokens, api calls, cost).
6. Blind LLM critic for open-ended tasks, with a meta-check that the critic
   itself can distinguish gold from junk (otherwise the critic is invalid).
7. The harness is itself tested (realbench/tests/) with fake executors.
"""

__version__ = "1.0.0"
