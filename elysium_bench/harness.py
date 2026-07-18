"""Clean execution harness — Docker or venv-based isolation for reproducible runs."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


class Harness:
    """Provides a clean, isolated environment for each benchmark run.

    Two modes:
    - docker: Full container isolation (recommended, requires Docker)
    - venv: Lightweight venv isolation (fallback, always available)
    """

    def __init__(self, mode: str = "venv", cleanup: bool = True, workspace_base: Path | None = None):
        self.mode = mode
        self.cleanup = cleanup
        self.workspace_base = workspace_base
        self._temp_dirs: list[Path] = []

    def create_workspace(self, task_id: str, source_dir: Path = None) -> Path:
        """Create a clean workspace for a task.

        Returns the workspace directory path.
        """
        if self.mode == "docker":
            return self._create_docker_workspace(task_id, source_dir)

        # Use workspace_base if set (Hermes-compatible), else system temp
        base = self.workspace_base or Path(tempfile.mkdtemp())
        if base == self.workspace_base:
            base.mkdir(parents=True, exist_ok=True)

        workspace = base / f"bench_{task_id}"
        if workspace.exists():
            import shutil
            shutil.rmtree(workspace)
        workspace.mkdir(parents=True, exist_ok=True)
        self._temp_dirs.append(workspace)

        # Create workspace/ subdir for solution files
        dest = workspace / "workspace"
        dest.mkdir(exist_ok=True)

        if source_dir and source_dir.exists():
            _copy_tree(source_dir, dest)

        return workspace

    def _create_venv_workspace(self, task_id: str, source_dir: Path) -> Path:
        """Create an isolated venv workspace."""
        workspace = Path(tempfile.mkdtemp(prefix=f"elysium_bench_{task_id}_"))
        self._temp_dirs.append(workspace)

        # Copy source files to workspace
        dest = workspace / "workspace"
        dest.mkdir(exist_ok=True)

        if source_dir.exists():
            _copy_tree(source_dir, dest)

        # Create venv
        subprocess.run(
            [sys.executable, "-m", "venv", str(workspace / ".venv")],
            capture_output=True,
            timeout=60,
        )

        return workspace

    def _create_docker_workspace(self, task_id: str, source_dir: Path) -> Path:
        """Create a Docker-isolated workspace."""
        workspace = Path(tempfile.mkdtemp(prefix=f"elysium_docker_{task_id}_"))
        self._temp_dirs.append(workspace)

        dest = workspace / "workspace"
        dest.mkdir(exist_ok=True)

        if source_dir.exists():
            _copy_tree(source_dir, dest)

        return workspace

    def run_in_workspace(self, workspace: Path, command: list[str], timeout: int = 600) -> dict[str, Any]:
        """Execute a command inside the isolated workspace."""
        work_dir = workspace / "workspace"

        if self.mode == "docker":
            return self._run_docker(workspace, command, timeout)
        else:
            return self._run_venv(workspace, command, timeout)

    def _run_venv(self, workspace: Path, command: list[str], timeout: int) -> dict[str, Any]:
        """Run command in venv workspace."""
        work_dir = workspace / "workspace"
        venv_python = str(workspace / ".venv" / "Scripts" / "python.exe") if os.name == "nt" else str(workspace / ".venv" / "bin" / "python")

        # Replace 'python' with venv python
        cmd = [venv_python if arg in ("python", "python3") else arg for arg in command]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(work_dir),
            )
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "success": result.returncode == 0,
            }
        except subprocess.TimeoutExpired:
            return {"stdout": "", "stderr": "TIMEOUT", "returncode": -1, "success": False}

    def _run_docker(self, workspace: Path, command: list[str], timeout: int) -> dict[str, Any]:
        """Run command in Docker container."""
        container_name = f"elysium_bench_{workspace.name}"
        work_dir = workspace / "workspace"

        docker_cmd = [
            "docker", "run", "--rm",
            "--name", container_name,
            "-v", f"{work_dir}:/workspace",
            "-w", "/workspace",
            "python:3.10-slim",
        ] + command

        try:
            result = subprocess.run(docker_cmd, capture_output=True, text=True, timeout=timeout)
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "success": result.returncode == 0,
            }
        except subprocess.TimeoutExpired:
            # Clean up container
            subprocess.run(["docker", "rm", "-f", container_name], capture_output=True)
            return {"stdout": "", "stderr": "DOCKER_TIMEOUT", "returncode": -1, "success": False}
        except FileNotFoundError:
            # Docker not available, fall back to venv
            return self._run_venv(workspace, command, timeout)

    def cleanup_all(self) -> list[Path]:
        """Remove all temporary workspaces."""
        removed = []
        for d in self._temp_dirs:
            if d.exists():
                shutil.rmtree(d, ignore_errors=True)
                removed.append(d)
        self._temp_dirs.clear()
        return removed

    def __del__(self):
        if self.cleanup:
            self.cleanup_all()


def _copy_tree(src: Path, dst: Path) -> None:
    """Copy directory tree, skipping venvs and __pycache__."""
    for item in src.iterdir():
        if item.name in (".venv", "__pycache__", ".git", ".pytest_cache", "node_modules"):
            continue
        dest = dst / item.name
        if item.is_dir():
            dest.mkdir(exist_ok=True)
            _copy_tree(item, dest)
        else:
            shutil.copy2(item, dest)
