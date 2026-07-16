"""Hermes Agent integration — runs tasks through Hermes with Elysium Swarmloop skill."""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


class HermesInterface:
    """Interface to execute benchmark tasks via Hermes Agent CLI."""

    def __init__(
        self,
        skill: str = "elysium-swarmloop",
        subagents_max: int = 50,
        quality_threshold: int = 7,
        retries_max: int = 3,
    ):
        self.skill = skill
        self.subagents_max = subagents_max
        self.quality_threshold = quality_threshold
        self.retries_max = retries_max

    def execute_task(
        self,
        task_id: str,
        task_description: str,
        workspace: Path,
        timeout: int = 600,
    ) -> dict[str, Any]:
        """Execute a task via Hermes Agent.

        Builds a prompt that instructs Hermes to solve the task,
        then monitors the output for completion.
        """
        prompt = self._build_prompt(task_id, task_description, workspace)

        start_time = time.time()

        try:
            # Try Hermes CLI first
            result = self._run_hermes_cli(prompt, workspace, timeout)
        except FileNotFoundError:
            # Fallback: simulate with direct execution
            result = self._run_direct(prompt, workspace, timeout)

        elapsed = time.time() - start_time
        result["elapsed_seconds"] = round(elapsed, 1)
        result["task_id"] = task_id

        return result

    def _build_prompt(self, task_id: str, description: str, workspace: Path) -> str:
        """Build the Hermes prompt for this task."""
        return f"""TASK: {task_id}
DESCRIPTION: {description}

WORKSPACE: {workspace}

INSTRUCTIONS:
1. Solve this task completely in the workspace directory
2. Write all code to {workspace}/workspace/
3. Ensure all tests in the tests/ directory pass
4. Follow the quality criteria from elysium-swarmloop
5. Return a summary of what you implemented

SKILL: {self.skill}
SUBAgents_MAX: {self.subagents_max}
QUALITY_THRESHOLD: {self.quality_threshold}/10
RETRIES_MAX: {self.retries_max}
"""

    def _run_hermes_cli(self, prompt: str, workspace: Path, timeout: int) -> dict[str, Any]:
        """Run task through hermes CLI."""
        # Save prompt to a temp file
        prompt_file = workspace / "hermes_prompt.txt"
        prompt_file.write_text(prompt, encoding="utf-8")

        cmd = [
            "hermes", "run",
            "--prompt-file", str(prompt_file),
            "--workdir", str(workspace / "workspace"),
            "--skill", self.skill,
            "--timeout", str(timeout),
            "--json",
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout + 60,  # Extra buffer
            )
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "success": result.returncode == 0,
                "mode": "hermes_cli",
            }
        except subprocess.TimeoutExpired:
            return {
                "stdout": "",
                "stderr": f"Hermes CLI timed out after {timeout}s",
                "returncode": -1,
                "success": False,
                "mode": "hermes_cli_timeout",
            }

    def _run_direct(self, prompt: str, workspace: Path, timeout: int) -> dict[str, Any]:
        """Direct execution fallback when Hermes CLI is not available.

        This is a simplified mode that:
        1. Reads task.yaml for exact instructions
        2. Runs any available test suite
        3. Returns structured results
        """
        # Try to run tests directly
        test_dir = workspace / "workspace" / "tests"
        if test_dir.exists():
            try:
                test_result = subprocess.run(
                    [sys.executable, "-m", "pytest", str(test_dir), "-q", "--tb=short"],
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    cwd=str(workspace / "workspace"),
                )
                return {
                    "stdout": test_result.stdout,
                    "stderr": test_result.stderr,
                    "returncode": test_result.returncode,
                    "success": test_result.returncode == 0,
                    "mode": "direct_pytest",
                }
            except (subprocess.TimeoutExpired, Exception):
                pass

        return {
            "stdout": prompt,
            "stderr": "Hermes CLI not available — direct mode executed without agent",
            "returncode": 0,
            "success": False,
            "mode": "direct_fallback",
        }
