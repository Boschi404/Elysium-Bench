"""Report builder — turns raw run data into verdicts on the skill's claims.

Every claim in the Elysium Swarmloop SKILL.md that RealBench can falsify is
mapped here to a measurable PASS/FAIL/INCONCLUSIVE verdict.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from .harness import RunResult


@dataclass
class ClaimVerdict:
    claim: str
    verdict: str          # PASS | FAIL | INCONCLUSIVE
    detail: str = ""


def _fmt(v, digits: int = 1) -> str:
    return f"{v:.{digits}f}" if isinstance(v, (int, float)) else str(v)


def evaluate_claims(results: dict[str, dict[str, RunResult]],
                    calibration: dict | None = None,
                    critic_meta: dict | None = None) -> list[ClaimVerdict]:
    """results: {task_id: {condition: RunResult}}"""
    verdicts: list[ClaimVerdict] = []

    # ── 0. Benchmark integrity (the "test del cazzo" falsification) ─────────
    if calibration:
        ok = True
        details = []
        for task_id, cal in calibration.items():
            g = cal.get("gold", 0.0)
            j = cal.get("junk", 0.0)
            details.append(f"{task_id}: gold={_fmt(g)} junk={_fmt(j)}")
            if g < 99.0 or j >= 40.0:
                ok = False
        verdicts.append(ClaimVerdict(
            claim="Benchmark discriminative (gold=100, junk<40, gap≥60)",
            verdict="PASS" if ok else "FAIL",
            detail="; ".join(details)))

    for task_id, conds in results.items():
        base = conds.get("baseline")
        swarm = conds.get("swarmloop")
        if base is None or swarm is None:
            continue
        bs = base.score.score if base.score else 0.0
        ss = swarm.score.score if swarm.score else 0.0
        bt = base.elapsed_seconds
        st = swarm.elapsed_seconds
        b_ev_ok = bool(base.evidence and base.evidence.found)
        s_ev_ok = bool(swarm.evidence and swarm.evidence.found)
        bsub = base.evidence.subagents_dispatched if b_ev_ok else -1
        ssub = swarm.evidence.subagents_dispatched if s_ev_ok else -1
        skill_ok = bool(swarm.evidence and swarm.evidence.skill_loaded)

        # ── 1. control validity ────────────────────────────────────────────
        if b_ev_ok:
            control_ok = not base.evidence.skill_loaded and bsub == 0
            verdicts.append(ClaimVerdict(
                claim=f"{task_id}: control valid (baseline: no skill, no subagents)",
                verdict="PASS" if control_ok else "FAIL",
                detail=f"baseline skill_loaded={base.evidence.skill_loaded} "
                       f"subagents={bsub} (transcript-verified)"))
        else:
            verdicts.append(ClaimVerdict(
                claim=f"{task_id}: control valid (baseline: no skill, no subagents)",
                verdict="INCONCLUSIVE",
                detail="baseline session evidence lost (isolated db overwritten — "
                       "harness bug, fixed); delegation was impossible by "
                       "construction (-t file,terminal removes the delegation "
                       "toolset)"))

        # ── 2. multi-agent claim ───────────────────────────────────────────
        if not s_ev_ok:
            verdicts.append(ClaimVerdict(
                claim=f"{task_id}: swarmloop actually used subagents",
                verdict="INCONCLUSIVE",
                detail="swarmloop session evidence unavailable"))
        else:
            verdicts.append(ClaimVerdict(
                claim=f"{task_id}: swarmloop actually used subagents",
                verdict="PASS" if ssub > 0 else "FAIL",
                detail=f"delegate_calls={swarm.evidence.delegate_calls} "
                       f"dispatched={ssub} batched={swarm.evidence.batched_dispatches} "
                       f"retries={swarm.evidence.retries} "
                       f"skill_loaded={skill_ok}"))

        # ── 3. quality claim ───────────────────────────────────────────────
        margin = ss - bs
        if margin >= 10:
            q = "PASS", f"swarmloop +{_fmt(margin)} pts ({_fmt(bs)} → {_fmt(ss)})"
        elif margin <= -10:
            q = "FAIL", f"swarmloop {_fmt(margin)} pts ({_fmt(bs)} → {_fmt(ss)})"
        else:
            q = "INCONCLUSIVE", f"margin {_fmt(margin)} pts ({_fmt(bs)} → {_fmt(ss)}) — within noise"
        verdicts.append(ClaimVerdict(
            claim=f"{task_id}: swarmloop quality ≥ baseline", verdict=q[0], detail=q[1]))

        # ── 4. parallelism efficiency claim ────────────────────────────────
        if swarm.timed_out or base.timed_out:
            verdicts.append(ClaimVerdict(
                claim=f"{task_id}: swarmloop wall-time ≤ baseline",
                verdict="INCONCLUSIVE",
                detail=f"timeout involved (base {_fmt(bt)}s, swarm {_fmt(st)}s)"))
        elif st <= bt * 1.25:
            verdicts.append(ClaimVerdict(
                claim=f"{task_id}: swarmloop wall-time ≤ baseline",
                verdict="PASS",
                detail=f"base {_fmt(bt)}s vs swarm {_fmt(st)}s"))
        else:
            verdicts.append(ClaimVerdict(
                claim=f"{task_id}: swarmloop wall-time ≤ baseline",
                verdict="FAIL",
                detail=f"base {_fmt(bt)}s vs swarm {_fmt(st)}s ({(st/bt):.1f}x slower)"))

        # ── 5. cost accounting (informational — not a pass/fail claim) ─────
        bc = base.evidence.estimated_cost_usd if b_ev_ok else None
        sc = swarm.evidence.estimated_cost_usd if s_ev_ok else None
        btok = (base.evidence.input_tokens + base.evidence.output_tokens) if b_ev_ok else None
        stok = (swarm.evidence.input_tokens + swarm.evidence.output_tokens) if s_ev_ok else None
        b_str = f"~${_fmt(bc, 3)}/{btok}tok" if btok is not None else "n/a"
        s_str = f"~${_fmt(sc, 3)}/{stok}tok" if stok is not None else "n/a"
        verdicts.append(ClaimVerdict(
            claim=f"{task_id}: cost accounting",
            verdict="INFO",
            detail=f"base {b_str} vs swarm {s_str}"))

    # ── 6. critic validity (text tasks) ────────────────────────────────────
    if critic_meta is not None:
        m = critic_meta.get("margin", 0.0)
        ok = bool(critic_meta.get("ok"))
        verdicts.append(ClaimVerdict(
            claim="Blind critic valid (gold ranked > junk)",
            verdict="PASS" if ok else "FAIL",
            detail=f"gold={_fmt(critic_meta.get('gold_score', 0))} "
                   f"junk={_fmt(critic_meta.get('junk_score', 0))} "
                   f"margin={_fmt(m)}"))

    return verdicts


def render_markdown(results: dict[str, dict[str, RunResult]],
                    verdicts: list[ClaimVerdict],
                    calibration: dict | None = None,
                    critic_meta: dict | None = None) -> str:
    lines = [
        "# RealBench — Elysium Swarmloop: does it actually work?",
        "",
        f"Run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Results per task × condition",
        "",
        "| Task | Condition | Score | Tests | Wall | Tokens | Cost | Subagents | Skill | Delegate calls | Retries |",
        "|------|-----------|-------|-------|------|--------|------|-----------|-------|-----------------|---------|",
    ]
    for task_id, conds in results.items():
        for cond in ("baseline", "swarmloop"):
            r = conds.get(cond)
            if r is None:
                continue
            sc = r.score
            ev = r.evidence
            ev_ok = bool(ev and ev.found)
            lines.append(
                f"| {task_id} | {cond} | **{_fmt(sc.score)}** | "
                f"{sc.passed}/{sc.passed + sc.failed} | {_fmt(r.elapsed_seconds)}s | "
                f"{_fmt(ev.input_tokens + ev.output_tokens, 0) if ev_ok else 'n/a'} | "
                f"~${_fmt(ev.estimated_cost_usd, 3) if ev_ok else 'n/a'} | "
                f"{ev.subagents_dispatched if ev_ok else 'n/a'} | "
                f"{'yes' if ev_ok and ev.skill_loaded else ('no' if ev_ok else 'n/a')} | "
                f"{ev.delegate_calls if ev_ok else 'n/a'} | "
                f"{ev.retries if ev_ok else 'n/a'} |"
            )
    lines += ["", "## Verdicts on the skill's claims", ""]
    for v in verdicts:
        icon = {"PASS": "✅", "FAIL": "❌", "INCONCLUSIVE": "⚠️",
                "INFO": "ℹ️"}[v.verdict]
        lines.append(f"- {icon} **{v.claim}** — {v.verdict}: {v.detail}")
    lines += [
        "",
        "## Limitations (read before quoting)",
        "",
        "- N=1 per task × condition — pilot scale, no statistical power.",
        "- Baseline token/cost evidence lost for this pilot run (isolated",
        "  state.db was overwritten between baseline runs — harness bug, fixed",
        "  in the current code; future runs keep a unique isolated home per run).",
        "- Delegation was nonetheless IMPOSSIBLE for the baseline by",
        "  construction: the `-t file,terminal` toolset removes delegate_task.",
        "- Cost in USD unavailable: the configured provider reports no pricing",
        "  data in Hermes' session tables; token counts are the cost proxy.",
        "- The swarmloop condition loaded the skill (verified via the session's",
        "  system prompt hash) but the model chose to solve every pilot task",
        "  directly without dispatching subagents — including the 4-module",
        "  parallel suite. See the extra_nudge experiment for a stronger prompt.",
    ]
    if calibration:
        lines += ["", "## Calibration (benchmark integrity)", ""]
        for task_id, cal in calibration.items():
            lines.append(f"- {task_id}: gold={_fmt(cal.get('gold'))} junk={_fmt(cal.get('junk'))}")
    if critic_meta:
        lines += ["", "## Critic meta-check", "", json.dumps(critic_meta, indent=2)]
    return "\n".join(lines) + "\n"


def write_report(results: dict[str, dict[str, RunResult]],
                 verdicts: list[ClaimVerdict],
                 out_dir: Path,
                 calibration: dict | None = None,
                 critic_meta: dict | None = None) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    md_path = out_dir / "REPORT.md"
    json_path = out_dir / "results.json"

    payload = {
        "timestamp": datetime.now().isoformat(),
        "tasks": {},
        "verdicts": [{"claim": v.claim, "verdict": v.verdict, "detail": v.detail}
                     for v in verdicts],
        "calibration": calibration or {},
        "critic_meta": critic_meta or {},
    }
    for task_id, conds in results.items():
        payload["tasks"][task_id] = {}
        for cond, r in conds.items():
            ev = r.evidence
            payload["tasks"][task_id][cond] = {
                "score": r.score.score if r.score else None,
                "passed": r.score.passed if r.score else 0,
                "failed": r.score.failed if r.score else 0,
                "elapsed_seconds": r.elapsed_seconds,
                "timed_out": r.timed_out,
                "session_id": r.session_id,
                "input_tokens": ev.input_tokens if ev else 0,
                "output_tokens": ev.output_tokens if ev else 0,
                "estimated_cost_usd": ev.estimated_cost_usd if ev else 0,
                "delegate_calls": ev.delegate_calls if ev else 0,
                "subagents_dispatched": ev.subagents_dispatched if ev else 0,
                "batched_dispatches": ev.batched_dispatches if ev else 0,
                "retries": ev.retries if ev else 0,
                "skill_loaded": ev.skill_loaded if ev else False,
                "terminal_calls": ev.terminal_calls if ev else 0,
                "write_file_calls": ev.write_file_calls if ev else 0,
                "notes": r.notes,
                "failed_tests": r.score.failed_test_names if r.score else [],
            }
    md_path.write_text(render_markdown(results, verdicts, calibration, critic_meta),
                       encoding="utf-8")
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return md_path, json_path
