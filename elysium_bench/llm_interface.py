"""LLM provider interface — connects to any LLM (OpenAI, Anthropic, Ollama, OpenRouter) to execute tasks.

This is the core execution engine. Each task gets sent to the LLM as a prompt,
and the LLM writes the solution (code, text, math, plan, or data output) to the workspace.
No Hermes CLI dependency — works standalone with just API keys or local Ollama.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class LLMProvider(ABC):
    """Abstract base for LLM providers."""

    def __init__(self, model: str, config: dict[str, Any]):
        self.model = model
        self.config = config

    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str, timeout: int) -> str:
        """Send a prompt to the LLM and return the text response."""
        ...


class OpenAILikeProvider(LLMProvider):
    """Generic provider for OpenAI-compatible APIs (OpenAI, OpenRouter, Together, etc.)."""

    def generate(self, system_prompt: str, user_prompt: str, timeout: int) -> str:
        import httpx

        api_key = self.config.get("api_key") or os.environ.get(self.config.get("env_key", "OPENAI_API_KEY"))
        base_url = self.config.get("base_url", "https://api.openai.com/v1")

        if not api_key:
            raise ValueError(f"No API key found for {base_url}. Set {self.config.get('env_key', 'OPENAI_API_KEY')} env var or add to config.")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": self.config.get("temperature", 0.3),
            "max_tokens": self.config.get("max_tokens", 8000),
        }

        with httpx.Client(timeout=timeout + 30, follow_redirects=True) as client:
            resp = client.post(f"{base_url}/chat/completions", json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]


class OllamaProvider(LLMProvider):
    """Local Ollama provider — no API key needed."""

    def generate(self, system_prompt: str, user_prompt: str, timeout: int) -> str:
        import httpx

        base_url = self.config.get("base_url", "http://localhost:11434")
        payload = {
            "model": self.model,
            "system": system_prompt,
            "prompt": user_prompt,
            "options": {
                "temperature": self.config.get("temperature", 0.3),
                "num_predict": self.config.get("max_tokens", 8000),
            },
            "stream": False,
        }

        with httpx.Client(timeout=timeout + 30) as client:
            resp = client.post(f"{base_url}/api/generate", json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data.get("response", "")


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider."""

    def generate(self, system_prompt: str, user_prompt: str, timeout: int) -> str:
        import httpx

        api_key = self.config.get("api_key") or os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("No Anthropic API key found. Set ANTHROPIC_API_KEY env var.")

        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload = {
            "model": self.model,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
            "temperature": self.config.get("temperature", 0.3),
            "max_tokens": self.config.get("max_tokens", 8000),
        }

        with httpx.Client(timeout=timeout + 30) as client:
            resp = client.post("https://api.anthropic.com/v1/messages", json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            return data["content"][0]["text"]


# ─── Factory ─────────────────────────────────────────────────────────────────

def create_llm_provider(llm_config: dict[str, Any] | None) -> LLMProvider | None:
    """Factory: returns an LLMProvider based on config, or None if disabled."""
    if not llm_config or not llm_config.get("enabled", False):
        return None

    provider_name = llm_config.get("provider", "ollama")
    model = llm_config.get("model", "qwen2.5:7b")
    base_config = {k: v for k, v in llm_config.items() if k not in ("provider", "model", "enabled")}

    providers = {
        "openai": OpenAILikeProvider,
        "anthropic": AnthropicProvider,
        "ollama": OllamaProvider,
        "openrouter": lambda **kw: OpenAILikeProvider(**kw | {"base_url": "https://openrouter.ai/api/v1", "env_key": "OPENROUTER_API_KEY"}),
        "together": lambda **kw: OpenAILikeProvider(**kw | {"base_url": "https://api.together.xyz/v1", "env_key": "TOGETHER_API_KEY"}),
    }

    factory = providers.get(provider_name)
    if not factory:
        raise ValueError(f"Unknown LLM provider: {provider_name}. Supported: {list(providers.keys())}")

    if provider_name in ("openai", "anthropic", "ollama"):
        return factory(model=model, config=base_config)

    # For openrouter/together, inject base_url
    kwargs = {"model": model, "config": base_config}
    provider = factory(model=model, config=base_config)
    return provider


# ═══════════════════════════════════════════════════════════════════════════
# TASK EXECUTOR — sends task descriptions to the LLM and writes output
# ═══════════════════════════════════════════════════════════════════════════

SYSTEM_PROMPTS = {
    "code": (
        "You are an expert software engineer. Implement the task below completely.\n"
        "Write production-quality Python code to the workspace directory.\n"
        "Rules:\n"
        "- Write complete, working code. No stubs, no TODOs, no pass.\n"
        "- Include type hints and docstrings for all functions.\n"
        "- Handle edge cases and errors properly.\n"
        "- Make sure all tests in the tests/ directory would pass.\n"
        "- The workspace is at $WORKSPACE — write files there.\n"
        "- Return ONLY the code. Wrap each file in ```file:path/to/file.py ... ``` blocks."
    ),
    "text": (
        "You are an expert writer and analyst. Complete the task below.\n"
        "Rules:\n"
        "- Write clear, well-structured markdown.\n"
        "- Cover all required aspects completely.\n"
        "- Use headers, lists, and formatting for clarity.\n"
        "- Include examples where helpful.\n"
        "- Save your answer as solution.md in the workspace.\n"
        "- The workspace is at $WORKSPACE."
    ),
    "math": (
        "You are an expert mathematician. Solve the problem below.\n"
        "Rules:\n"
        "- Show all steps and reasoning clearly.\n"
        "- Use LaTeX notation where appropriate ($$...$$).\n"
        "- Verify your answer at the end.\n"
        "- Save as solution.md in the workspace.\n"
        "- The workspace is at $WORKSPACE."
    ),
    "plan": (
        "You are a senior infrastructure architect. Design the configuration/plan below.\n"
        "Rules:\n"
        "- Be specific with commands, configs, and file contents.\n"
        "- Include all necessary details for someone to implement.\n"
        "- Cover edge cases, error handling, and security.\n"
        "- Save as plan.md or the appropriate config file(s) in the workspace.\n"
        "- The workspace is at $WORKSPACE."
    ),
    "data": (
        "You are a data engineer. Write the SQL/analysis below.\n"
        "Rules:\n"
        "- Write correct, optimized queries.\n"
        "- Include comments explaining non-obvious parts.\n"
        "- Handle NULLs and edge cases.\n"
        "- Save as solution.sql or solution.py in the workspace.\n"
        "- The workspace is at $WORKSPACE."
    ),
}


class LLMTaskExecutor:
    """Executes benchmark tasks via an LLM provider."""

    def __init__(self, llm_provider: LLMProvider | None):
        self.provider = llm_provider
        self.enabled = llm_provider is not None

    def execute(
        self,
        task_id: str,
        task_name: str,
        task_description: str,
        task_type: str,
        workspace: Path,
        timeout: int = 600,
    ) -> dict[str, Any]:
        """Execute a task via the LLM."""
        start = time.time()

        if not self.enabled:
            # No LLM — run tests directly to check what exists in workspace
            return self._run_tests(workspace, timeout)

        work_path = workspace / "workspace"
        work_path.mkdir(parents=True, exist_ok=True)

        system_prompt = SYSTEM_PROMPTS.get(task_type, SYSTEM_PROMPTS["code"])
        system_prompt = system_prompt.replace("$WORKSPACE", str(work_path))

        user_prompt = (
            f"## Task: {task_id} — {task_name}\n\n"
            f"{task_description}\n\n"
            f"## Workspace\n"
        )

        # If task has existing code/source files, include them
        existing_files = list((workspace / "workspace").glob("**/*"))
        source_files = [f for f in existing_files if f.is_file() and f.name != "tests" and "tests" not in f.parts]
        if source_files:
            user_prompt += "\nExisting source files:\n"
            for f in source_files:
                try:
                    content = f.read_text(encoding="utf-8", errors="ignore")
                    user_prompt += f"\n### {f.relative_to(workspace/ 'workspace')}\n```\n{content[:2000]}\n```\n"
                except Exception:
                    pass

        # If tests exist, include them
        test_dir = workspace / "workspace" / "tests"
        if not test_dir.exists():
            test_dir = task_dir = Path(str(workspace).replace(str(workspace.name), "") + "/tasks") if False else None
            # Copy tests from task definition if not in workspace
            from pathlib import Path as P
            task_yaml_path = P(str(workspace).replace("_" + task_id.split("_", 1)[0], ""))  # approximate

        # Find tests in the task directory
        for path in [P(workspace).parent.parent / "tasks" / task_id.replace(task_id.split("_")[0], "").lstrip("_").replace("_", "/", 1)]:
            pass

        # Look for tests in various locations
        test_search = [
            P(workspace).parent.parent / "tasks" / cat_dir / f"T{i:02d}_{cat_name}" / "tests"
            for cat_dir in ["api_development", "bug_fixing", "algorithm_implementation", "data_analysis",
                          "mathematical_reasoning", "logical_deduction", "security_analysis",
                          "code_review", "documentation_generation", "configuration_management"]
            for i in range(1, 11)
        ]

        try:
            resp = self.provider.generate(system_prompt, user_prompt, timeout)
        except Exception as e:
            elapsed = time.time() - start
            return {
                "stdout": "",
                "stderr": f"LLM error: {e}",
                "returncode": -1,
                "success": False,
                "mode": "llm_error",
                "elapsed_seconds": round(time.time() - start, 1),
                "task_id": task_id,
            }

        # Parse response for file blocks and write them
        files_written = self._parse_and_write_files(resp, work_path)

        # If no file blocks found, write entire response as solution.md
        if not files_written:
            (work_path / "solution.md").write_text(resp, encoding="utf-8")
            files_written = ["solution.md"]

        elapsed = time.time() - start

        return {
            "stdout": f"LLM response received. Files written: {', '.join(files_written)}",
            "stderr": "",
            "returncode": 0,
            "success": True,
            "mode": f"llm_{self.provider.__class__.__name__.replace('Provider','').lower()}",
            "files_written": files_written,
            "elapsed_seconds": round(elapsed, 1),
            "task_id": task_id,
        }

    def _parse_and_write_files(self, response: str, work_path: Path) -> list[str]:
        """Parse ```file:path blocks from LLM response and write them."""
        files_written = []

        # Match ```file:path/to/file.py ... ``` blocks
        pattern = r"```file:([^\n]+)\n(.*?)```"
        for match in re.finditer(pattern, response, re.DOTALL):
            filepath = match.group(1).strip()
            content = match.group(2)
            # Handle both relative and absolute paths
            if Path(filepath).is_absolute():
                file_dest = Path(filepath)
            else:
                file_dest = work_path / filepath
            file_dest.parent.mkdir(parents=True, exist_ok=True)
            file_dest.write_text(content.strip() + "\n", encoding="utf-8")
            files_written.append(str(file_dest.relative_to(work_path)))

        # Also match plain ```python ... ``` blocks and write as main.py
        if not files_written:
            py_match = re.search(r"```python\n(.*?)```", response, re.DOTALL)
            if py_match:
                (work_path / "main.py").write_text(py_match.group(1).strip() + "\n", encoding="utf-8")
                files_written = ["main.py"]

        # Match ```sql ... ``` blocks
        if not files_written:
            sql_match = re.search(r"```sql\n(.*?)```", response, re.DOTALL)
            if sql_match:
                (work_path / "solution.sql").write_text(sql_match.group(1).strip() + "\n", encoding="utf-8")
                files_written = ["solution.sql"]

        # Match ```yaml or ```dockerfile blocks
        if not files_written:
            for ext, lang in [(".yaml", "yaml"), (".yml", "yaml"), (".dockerfile", "dockerfile"), (".sh", "bash"), (".tf", "hcl")]:
                match = re.search(rf"```{lang}\n(.*?)```", response, re.DOTALL)
                if match:
                    (work_path / f"solution{ext}").write_text(match.group(1).strip() + "\n", encoding="utf-8")
                    files_written = [f"solution{ext}"]
                    break

        return files_written

    def _run_tests(self, workspace: Path, timeout: int) -> dict[str, Any]:
        """Run pytest in workspace (baseline mode — no LLM)."""
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
        return {
            "stdout": "",
            "stderr": "Baseline mode — no LLM, no tests found",
            "returncode": 0,
            "success": False,
            "mode": "baseline_empty",
        }
