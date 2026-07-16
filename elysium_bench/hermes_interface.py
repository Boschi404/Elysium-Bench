"""Task execution interface — supports multiple modes:

1. Hermes CLI (primary): runs tasks through `hermes run` with Elysium Swarmloop skill
2. LLM Direct (fallback): sends task to configured LLM provider (Ollama, OpenAI, etc.)
3. Baseline: runs pytest directly on workspace (no agent, for comparison)
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from .llm_interface import LLMProvider, LLMTaskExecutor, create_llm_provider


class TaskExecutor:
    """Unified task executor: Hermes CLI → LLM Direct → Baseline pytest."""

    def __init__(self, llm_provider: LLMProvider | None = None, task_type: str = "code"):
        self.llm_executor = LLMTaskExecutor(llm_provider) if llm_provider else None
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
        """Execute a task. Tries: Hermes CLI → LLM Direct → Baseline pytest."""
        start = time.time()
        result = None

        # 1. Try Hermes CLI (primary — gives us Elysium Swarmloop orchestration)
        result = self._try_hermes_cli(task_id, task_description, workspace, timeout)

        # 2. Fallback: LLM Direct (if Hermes not available but LLM provider configured)
        if result is None and self.llm_executor:
            result = self.llm_executor.execute(
                task_id=task_id, task_name=task_name,
                task_description=task_description, task_type=self.task_type,
                workspace=workspace, timeout=timeout,
            )

        # 3. Final fallback: baseline pytest (no AI at all)
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
        """Try executing via `hermes run` CLI. Returns None if Hermes not found."""
        prompt = self._build_prompt(task_id, description, workspace)
        prompt_file = workspace / "hermes_prompt.txt"
        prompt_file.write_text(prompt, encoding="utf-8")

        cmd = [
            "hermes", "run",
            "--prompt-file", str(prompt_file),
            "--workdir", str(workspace / "workspace"),
            "--timeout", str(timeout),
            "--json",
        ]

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout + 60,
            )
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "success": result.returncode == 0,
                "mode": "hermes_cli",
            }
        except FileNotFoundError:
            return None  # Hermes not installed, try next mode
        except subprocess.TimeoutExpired:
            return {"stdout": "", "stderr": f"Hermes CLI timed out ({timeout}s)", "returncode": -1, "success": False, "mode": "hermes_timeout"}

    def _run_baseline(self, workspace: Path, timeout: int) -> dict[str, Any] | None:
        """Run pytest directly on whatever exists in workspace (no AI)."""
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
"""
