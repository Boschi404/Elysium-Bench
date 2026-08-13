"""Claim verdicts — the mapping from raw data to PASS/FAIL must be honest."""
from pathlib import Path

from realbench.harness import RunResult
from realbench.report import evaluate_claims
from realbench.scoring import ScoreResult
from realbench.transcript import SessionEvidence


def _res(score, elapsed, subagents, skill_loaded, delegate_calls=0,
         retries=0, timed_out=False, cost=0.0, tokens=0) -> RunResult:
    r = RunResult(task_id="t", condition="x", workspace=Path("."),
                  prompt_file=Path("."))
    r.score = ScoreResult(task_id="t", score=score, passed=int(score / 10),
                          failed=10 - int(score / 10))
    r.elapsed_seconds = elapsed
    r.timed_out = timed_out
    ev = SessionEvidence(found=True, session_id="s")
    ev.skill_loaded = skill_loaded
    ev.subagents_dispatched = subagents
    ev.delegate_calls = delegate_calls
    ev.retries = retries
    ev.estimated_cost_usd = cost
    ev.input_tokens = tokens
    r.evidence = ev
    return r


def test_control_invalid_when_baseline_cheats():
    results = {"t": {
        "baseline": _res(80, 100, subagents=5, skill_loaded=True),
        "swarmloop": _res(85, 200, subagents=10, skill_loaded=True),
    }}
    verdicts = evaluate_claims(results)
    v = next(x for x in verdicts if x.claim.startswith("t: control valid"))
    assert v.verdict == "FAIL"


def test_multiagent_claim_pass_and_fail():
    ok = {"t": {
        "baseline": _res(80, 100, 0, False),
        "swarmloop": _res(90, 300, 12, True, delegate_calls=3, retries=1),
    }}
    v = next(x for x in evaluate_claims(ok)
             if x.claim.startswith("t: swarmloop actually used subagents"))
    assert v.verdict == "PASS" and "12" in v.detail and "retries=1" in v.detail

    no_sub = {"t": {
        "baseline": _res(80, 100, 0, False),
        "swarmloop": _res(90, 300, 0, True),
    }}
    v = next(x for x in evaluate_claims(no_sub)
             if x.claim.startswith("t: swarmloop actually used subagents"))
    assert v.verdict == "FAIL"


def test_quality_margins():
    better = {"t": {
        "baseline": _res(60, 100, 0, False),
        "swarmloop": _res(90, 300, 4, True),
    }}
    v = next(x for x in evaluate_claims(better)
             if x.claim.startswith("t: swarmloop quality"))
    assert v.verdict == "PASS"

    worse = {"t": {
        "baseline": _res(90, 100, 0, False),
        "swarmloop": _res(60, 300, 4, True),
    }}
    v = next(x for x in evaluate_claims(worse)
             if x.claim.startswith("t: swarmloop quality"))
    assert v.verdict == "FAIL"

    noise = {"t": {
        "baseline": _res(85, 100, 0, False),
        "swarmloop": _res(90, 300, 4, True),
    }}
    v = next(x for x in evaluate_claims(noise)
             if x.claim.startswith("t: swarmloop quality"))
    assert v.verdict == "INCONCLUSIVE"


def test_wall_time_verdict():
    fast = {"t": {
        "baseline": _res(80, 400, 0, False),
        "swarmloop": _res(85, 300, 8, True),
    }}
    v = next(x for x in evaluate_claims(fast)
             if x.claim.startswith("t: swarmloop wall-time"))
    assert v.verdict == "PASS"

    slow = {"t": {
        "baseline": _res(80, 100, 0, False),
        "swarmloop": _res(85, 400, 8, True),
    }}
    v = next(x for x in evaluate_claims(slow)
             if x.claim.startswith("t: swarmloop wall-time"))
    assert v.verdict == "FAIL"


def test_calibration_fails_when_junk_scores():
    cal = {"t1": {"gold": 100, "junk": 60}, "t2": {"gold": 100, "junk": 0}}
    v = next(x for x in evaluate_claims({}, calibration=cal)
             if x.claim.startswith("Benchmark discriminative"))
    assert v.verdict == "FAIL"
    cal2 = {"t1": {"gold": 100, "junk": 0}}
    v = next(x for x in evaluate_claims({}, calibration=cal2)
             if x.claim.startswith("Benchmark discriminative"))
    assert v.verdict == "PASS"


def test_critic_verdict():
    v = next(x for x in evaluate_claims({}, critic_meta={"ok": True, "margin": 60})
             if x.claim.startswith("Blind critic"))
    assert v.verdict == "PASS"
    v = next(x for x in evaluate_claims({}, critic_meta={"ok": False, "margin": 3})
             if x.claim.startswith("Blind critic"))
    assert v.verdict == "FAIL"
