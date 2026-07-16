"""Task execution interface — routes to LLM provider or baseline direct execution.

Two modes:
- Elysium mode: sends task to LLM provider (OpenAI, Anthropic, Ollama, OpenRouter)
- Baseline mode: runs pytest directly on whatever exists in workspace (no LLM)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .llm_interface import LLMProvider, LLMTaskExecutor, create_llm_provider


class TaskExecutor:
    """Unified task executor: LLM-powered (Elysium) vs direct (baseline)."""

    def __init__(self, llm_provider: LLMProvider | None, task_type: str = "code"):
        self.executor = LLMTaskExecutor(llm_provider)
        self.task_type = task_type

    @property
    def enabled(self) -> bool:
        return self.executor.enabled

    def execute(
        self,
        task_id: str,
        task_name: str,
        task_description: str,
        workspace: Path,
        timeout: int = 600,
    ) -> dict[str, Any]:
        """Execute a task — via LLM if available, else direct test run."""
        return self.executor.execute(
            task_id=task_id,
            task_name=task_name,
            task_description=task_description,
            task_type=self.task_type,
            workspace=workspace,
            timeout=timeout,
        )
