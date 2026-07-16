"""Task execution interface — runs tasks through Hermes Agent with Elysium Swarmloop.

The benchmark sends each task to `hermes run --skill elysium-swarmloop`.
Hermes Agent then orchestrates the task using its configured LLM (e.g. deepseek-v4-flash)
via the Elysium Swarmloop skill, handling subagent dispatch, quality gates, and self-learning.

Fallback chain:
1. `hermes run` CLI (primary) — full Elysium orchestration
2. Baseline pytest — no AI, measures empty workspace score
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path
from typing import Any


class TaskExecutor:
    """Executes tasks via Hermes Agent CLI or baseline pytest."""

    def __init__(self, llm_provider=None, task_type: str = "code"):
        # llm_provider kept for API compatibility but NOT used directly
        # Elysium uses Hermes Agent's configured LLM, not our direct calls
        self.task_type = task_type

    def execute(
        self,
        task_id: str,
        task_name: str,
        task_description: str,
        workspace: Path,
        timeout: int = 600,
        attempt: str = "first",
    ) -> dict[str, Any]:
        """Execute a task. Tries: Hermes CLI → Baseline pytest."""
        start = time.time()
        result = None

        # 1. Try Hermes CLI — runs task through Elysium Swarmloop skill
        result = self._try_hermes_cli(task_id, task_description, workspace, timeout)

        # 2. Fallback: baseline pytest (no AI, empty workspace)
        if result is None:
            result = self._run_baseline(workspace, timeout)

        if result is None:
            result = {"stdout": "", "stderr": "No execution mode available", "returncode": -1, "success": False, "mode": "none"}

        elapsed = time.time() - start
        result["elapsed_seconds"] = round(elapsed, 1)
        result["task_id"] = task_id
        result["attempt"] = attempt
        result["workspace"] = str(workspace)
        return result

    def _try_hermes_cli(self, task_id: str, description: str, workspace: Path, timeout: int) -> dict[str, Any] | None:
        """Execute via `hermes run --skill elysium-swarmloop`."""
        prompt = self._build_prompt(task_id, description, workspace)
        prompt_file = workspace / "hermes_prompt.txt"
        prompt_file.write_text(prompt, encoding="utf-8")

        cmd = [
            "hermes", "run",
            "--prompt-file", str(prompt_file),
            "--workdir", str(workspace / "workspace"),
            "--skill", "elysium-swarmloop",
            "--timeout", str(timeout),
            "--json",
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 60)
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "success": result.returncode == 0,
                "mode": "hermes_cli",
            }
        except FileNotFoundError:
            return None  # Hermes not installed
        except subprocess.TimeoutExpired:
            return {"stdout": "", "stderr": f"Hermes CLI timed out ({timeout}s)", "returncode": -1, "success": False, "mode": "hermes_timeout"}

    def _run_baseline(self, workspace: Path, timeout: int) -> dict[str, Any] | None:
        """Run pytest on workspace (no AI, just to measure zero baseline)."""
        test_dir = workspace / "workspace" / "tests"
        if test_dir.exists():
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "pytest", str(test_dir), "-q", "--tb=short"],
                    capture_output=True, text=True, timeout=timeout,
                    cwd=str(workspace / "workspace"),
                )
                return {
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "returncode": result.returncode,
                    "success": result.returncode == 0,
                    "mode": "baseline_pytest",
                }
            except (subprocess.TimeoutExpired, Exception):
                pass
        return {"stdout": "", "stderr": "Baseline mode — no tests found", "returncode": 0, "success": False, "mode": "baseline_empty"}

    @staticmethod
    def _build_prompt(task_id: str, description: str, workspace: Path) -> str:
        return f"""TASK: {task_id}
DESCRIPTION: {description}

WORKSPACE: {workspace}

INSTRUCTIONS:
1. Solve this task completely in the workspace directory
2. Write all code to {workspace}/workspace/
3. Ensure all tests in the tests/ directory pass
4. Return a summary of what you implemented

SKILL: elysium-swarmloop
"""
