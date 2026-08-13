"""Blind LLM critic for open-ended tasks.

The critic runs in an isolated HERMES_HOME (no elysium skill), sees ONLY the
artifact + rubric, and is never told which condition produced the artifact.
It returns a strict JSON verdict.

Meta-check (validate_critic): the critic must rank the GOLD review above the
JUNK review by a healthy margin. If it cannot, the critic is invalid and any
text scores it produces must be discarded.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path

from .harness import _isolated_home

_JSON_BLOCK = re.compile(r"\{[\s\S]*\}", re.MULTILINE)


@dataclass
class CriticVerdict:
    score: float = 0.0            # 0-100
    planted_found: int = 0
    planted_total: int = 0
    false_positives: int = 0
    specificity: float = 0.0      # 0-15
    no_fp_score: float = 0.0      # 0-15
    comments: str = ""
    raw: str = ""
    valid_json: bool = False
    notes: list[str] = field(default_factory=list)


def _critic_prompt(rubric_path: Path, artifact_path: Path, diff_path: Path | None) -> str:
    rubric = rubric_path.read_text(encoding="utf-8") if rubric_path.exists() else ""
    diff = diff_path.read_text(encoding="utf-8") if diff_path and diff_path.exists() else ""
    artifact = artifact_path.read_text(encoding="utf-8") if artifact_path.exists() else ""
    return f"""You are an impartial benchmark grader. Grade the code review below
against the rubric. The diff under review and the rubric follow.

RUBRIC:
{rubric}

DIFF UNDER REVIEW:
{diff}

CODE REVIEW TO GRADE (file {artifact_path}):
{artifact}

Respond with ONLY a JSON object, no prose:
{{
  "planted_found": <int, how many of the planted issues the review identifies
    with the correct anchor content>,
  "planted_with_fix": <int, of those, how many also give a concrete fix>,
  "planted_total": <int>,
  "false_positives": <int, claimed issues that are NOT actually present>,
  "specificity_score": <0-15, references file/line regions and real
    identifiers vs generic advice>,
  "no_fp_score": <0-15, 15 minus false-positive penalty>,
  "score": <0-100 total per the rubric>,
  "comments": <one sentence>
}}"""


def run_critic(
    rubric_path: Path,
    artifact_path: Path,
    diff_path: Path | None,
    hermes_home: Path,
    isolated_homes_dir: Path,
    timeout: int = 480,
) -> CriticVerdict:
    v = CriticVerdict()
    home = _isolated_home(isolated_homes_dir, hermes_home)
    env = dict(os.environ)
    env["HERMES_HOME"] = str(home)
    prompt = _critic_prompt(rubric_path, artifact_path, diff_path)
    try:
        proc = subprocess.run(
            ["hermes", "chat", "-q", prompt, "-Q", "--max-turns", "3"],
            capture_output=True, text=True, timeout=timeout, env=env)
        v.raw = (proc.stdout or "") + (proc.stderr or "")
    except subprocess.TimeoutExpired:
        v.notes.append(f"critic timed out after {timeout}s")
        return v
    m = _JSON_BLOCK.search(v.raw)
    if not m:
        v.notes.append("critic returned no JSON block")
        return v
    try:
        data = json.loads(m.group(0))
        v.valid_json = True
        v.score = float(data.get("score", 0))
        v.planted_found = int(data.get("planted_found", 0))
        v.planted_total = int(data.get("planted_total", 0))
        v.false_positives = int(data.get("false_positives", 0))
        v.specificity = float(data.get("specificity_score", 0))
        v.no_fp_score = float(data.get("no_fp_score", 0))
        v.comments = str(data.get("comments", ""))
    except (json.JSONDecodeError, ValueError, TypeError) as e:
        v.notes.append(f"critic JSON invalid: {e}")
    return v


def validate_critic(
    task_dir: Path,
    hermes_home: Path,
    isolated_homes_dir: Path,
    timeout: int = 480,
    min_margin: float = 25.0,
) -> tuple[bool, dict]:
    """Meta-check: critic must rank gold review above junk review."""
    rubric = task_dir / "tests" / "rubric.yaml"
    gold = task_dir / "gold" / "review.md"
    junk = task_dir / "gold" / "junk_review.md"
    diff = task_dir / "repo" / "diff.patch"
    if not (rubric.exists() and gold.exists() and junk.exists()):
        return False, {"error": "missing rubric/gold/junk fixtures"}

    start = time.time()
    v_gold = run_critic(rubric, gold, diff, hermes_home, isolated_homes_dir, timeout)
    v_junk = run_critic(rubric, junk, diff, hermes_home, isolated_homes_dir, timeout)
    meta = {
        "gold_score": v_gold.score,
        "junk_score": v_junk.score,
        "margin": round(v_gold.score - v_junk.score, 1),
        "gold_notes": v_gold.notes,
        "junk_notes": v_junk.notes,
        "elapsed_seconds": round(time.time() - start, 1),
    }
    ok = v_gold.valid_json and v_junk.valid_json and (v_gold.score - v_junk.score) >= min_margin
    return ok, meta
