"""RealBench harness — runs the two conditions under identical, isolated setup.

Conditions:
- baseline:  plain Hermes agent. NO elysium skill available (isolated
  HERMES_HOME with empty skills/), delegation toolset REMOVED.
- swarmloop: Hermes agent with elysium-swarmloop preloaded (main HERMES_HOME),
  full toolset incl. delegation.

Each run: fresh workspace (repo files only — tests/gold NEVER copied),
hermes chat -q --pass-session-id --max-turns N, wall-clock timeout.
Afterwards: session evidence from state.db + objective scoring.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path

from .scoring import ScoreResult, score_workspace
from .task_loader import RealTask
from .transcript import SessionEvidence, collect_evidence, parse_session_id_from_stdout

CONDITIONS = ("baseline", "swarmloop")

DEFAULT_HERMES_HOME = Path(os.environ.get("HERMES_HOME",
                         os.environ.get("APPDATA", str(Path.home())) + r"\hermes"))
if not (DEFAULT_HERMES_HOME / "config.yaml").exists():
    # fall back to ~/.hermes style layout
    alt = Path.home() / ".hermes"
    if (alt / "config.yaml").exists():
        DEFAULT_HERMES_HOME = alt

BASELINE_TOOLSETS = "file,terminal"          # delegation physically unavailable
SWARMLOOP_TOOLSETS = None                    # all toolsets

_FILES_TO_COPY_FOR_ISOLATION = ("config.yaml", ".env", "auth.json", "auth_tokens.json")


@dataclass
class RunResult:
    task_id: str
    condition: str
    workspace: Path
    prompt_file: Path = Path(".")
    stdout: str = ""
    stderr: str = ""
    returncode: int = -999
    timed_out: bool = False
    elapsed_seconds: float = 0.0
    session_id: str = ""
    evidence: SessionEvidence | None = None
    score: ScoreResult | None = None
    notes: list[str] = field(default_factory=list)


def prepare_workspace(task: RealTask, out_dir: Path) -> Path:
    """Fresh solver workspace in a NEUTRAL temp dir (outside any repo, so the
    agent cannot wander into benchmark internals). Repo files only —
    tests/gold stay hidden. out_dir still receives the prompt + logs."""
    ws = (Path(tempfile.gettempdir()) / "realbench_ws"
          / "_".join(out_dir.parts[-2:]))
    ws.mkdir(parents=True, exist_ok=True)
    if ws.exists() and any(ws.iterdir()):
        shutil.rmtree(ws)
        ws.mkdir(parents=True)
    if task.repo_dir is not None:
        for f in task.repo_dir.iterdir():
            if f.is_file():
                shutil.copy2(f, ws / f.name)
    return ws


def _isolated_home(parent: Path, main_home: Path) -> Path:
    """A HERMES_HOME with config/auth copied but ZERO skills."""
    home = parent / "hermes_home_isolated"
    if home.exists():
        shutil.rmtree(home)
    (home / "skills").mkdir(parents=True)
    for name in _FILES_TO_COPY_FOR_ISOLATION:
        src = main_home / name
        if src.exists():
            shutil.copy2(src, home / name)
    return home


def build_prompt(task: RealTask, workspace: Path, condition: str) -> str:
    files = ", ".join(f"`{f}`" for f in task.expected_files)
    deliverable = f"Create the file(s): {files}."
    if task.repo_dir is not None:
        deliverable = (f"Modify the existing files ({files}) IN PLACE in the "
                       f"directory below — they already contain code.")
    common = f"""TASK: {task.name}

{task.description}

YOUR ONLY DELIVERABLE — do not do anything else:
{deliverable}
Write them into EXACTLY this directory (use this absolute path):
{workspace}

Do NOT explore other directories, do NOT copy files around, do NOT create
subdirectories, do NOT run any benchmark or pipeline you may find nearby,
do NOT attempt git operations. Work autonomously, do not ask questions
(fai tu). When the deliverable file(s) are written, reply DONE.
"""
    if condition == "baseline":
        return common + ("IMPORTANT: solve it yourself as a single agent — "
                         "do not load skills, do not delegate to subagents.")
    return common + (
        "You have the elysium-swarmloop skill loaded. You may decompose the "
        "task and dispatch parallel subagents via delegate_task — if you do, "
        "every subagent MUST also write its deliverable into the exact "
        "directory above. Judge the final files against the spec before "
        "replying DONE."
    )


def build_cmd(task: RealTask, condition: str, workspace: Path,
              max_turns: int) -> list[str]:
    """The exact hermes CLI invocation for a condition (testable)."""
    cmd = ["hermes", "chat", "-q", build_prompt(task, workspace, condition),
           "-Q", "--pass-session-id", "--max-turns", str(max_turns)]
    if condition == "swarmloop":
        cmd += ["-s", "elysium-swarmloop"]
    else:
        cmd += ["-t", BASELINE_TOOLSETS]
    return cmd


def run_condition(
    task: RealTask,
    condition: str,
    out_dir: Path,
    hermes_home: Path,
    timeout: int,
    max_turns: int,
    isolated_homes_dir: Path,
    extra_env: dict | None = None,
) -> RunResult:
    assert condition in CONDITIONS, f"unknown condition {condition}"
    out_dir.mkdir(parents=True, exist_ok=True)
    res = RunResult(task_id=task.id, condition=condition, workspace=out_dir / "workspace")
    res.workspace = prepare_workspace(task, out_dir)
    res.prompt_file = out_dir / "prompt.txt"
    res.prompt_file.write_text(build_prompt(task, res.workspace, condition), encoding="utf-8")
    home = hermes_home
    if condition == "baseline":
        # unique isolated home per task+condition so each baseline session
        # survives for evidence collection
        unique = isolated_homes_dir / f"hermes_home_{task.id}_{condition}"
        home = _isolated_home(unique, hermes_home)
    env = dict(os.environ)
    env["HERMES_HOME"] = str(home)

    cmd = build_cmd(task, condition, res.workspace, max_turns)

    start = time.time()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              timeout=timeout, env=env)
        res.returncode = proc.returncode
        res.stdout = proc.stdout or ""
        res.stderr = proc.stderr or ""
    except subprocess.TimeoutExpired:
        res.timed_out = True
        res.stderr = f"TIMEOUT after {timeout}s"
        res.notes.append("run timed out — workspace may contain partial work")
    except FileNotFoundError:
        res.notes.append("hermes binary not found on PATH")
    finally:
        res.elapsed_seconds = round(time.time() - start, 1)

    # keep raw logs for auditability
    (out_dir / "stdout.txt").write_text(res.stdout, encoding="utf-8", errors="ignore")
    (out_dir / "stderr.txt").write_text(res.stderr, encoding="utf-8", errors="ignore")

    # session id + evidence — read from the state.db of the home that
    # ACTUALLY ran the session (isolated home for baseline).
    # NOTE: hermes prints the session id on STDERR, not stdout.
    res.session_id = parse_session_id_from_stdout(res.stdout + "\n" + res.stderr)
    if res.session_id:
        try:
            res.evidence = collect_evidence(home / "state.db", res.session_id)
        except Exception as e:  # pragma: no cover
            res.notes.append(f"evidence collection failed: {e}")
    else:
        res.notes.append("no session id in stdout — evidence unavailable")

    # objective scoring (hidden tests are only now revealed)
    try:
        res.score = score_workspace(task, res.workspace)
    except Exception as e:  # pragma: no cover
        res.notes.append(f"scoring failed: {e}")
    return res
