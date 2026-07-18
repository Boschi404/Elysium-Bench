"""SWE-bench adapter — integrates SWE-bench Verified instances into Elysium-Bench.

Each task is a real GitHub issue from SWE-bench. The adapter:
1. Downloads instance data from HuggingFace (issue text, test patch, gold patch)
2. Clones the repo at the specified base commit
3. Runs the agent (with or without Elysium skill)
4. Evaluates the generated patch against the test suite
5. Returns SWE-bench binary score (resolved/unresolved) + Elysium continuous score

Requires: pip install datasets swebench
Optional: Docker (for SWE-bench evaluation harness)
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

from .hermes_interface import TaskExecutor


class SweBenchAdapter:
    """Adapter for SWE-bench Verified instances."""

    REPO_CACHE = Path.home() / ".cache" / "elysium-bench" / "swe_repos"
    INSTANCE_CACHE = Path.home() / ".cache" / "elysium-bench" / "swe_instances"

    def __init__(self, task_dir: Path, executor: TaskExecutor):
        self.task_dir = Path(task_dir)
        self.executor = executor
        self.instance_id = self._load_instance_id()

        # Ensure caches exist
        self.REPO_CACHE.mkdir(parents=True, exist_ok=True)
        self.INSTANCE_CACHE.mkdir(parents=True, exist_ok=True)

    def _load_instance_id(self) -> str:
        """Load instance_id from task.yaml."""
        import yaml
        data = yaml.safe_load((self.task_dir / "task.yaml").read_text(encoding="utf-8"))
        return data.get("instance_id", "")

    def prepare(self) -> Path:
        """Prepare the workspace: clone repo at base commit, apply setup.

        Returns the workspace path.
        """
        instance = self._get_instance()
        repo_name = instance["repo"].replace("/", "__")
        repo_path = self.REPO_CACHE / repo_name
        base_commit = instance["base_commit"]

        # Create workspace
        workspace = Path(tempfile.mkdtemp(prefix=f"swe_{self.instance_id}_"))
        work_dir = workspace / "workspace"
        work_dir.mkdir(exist_ok=True)

        # Clone or update repo cache
        if not repo_path.exists():
            print(f"   ⏳ Cloning {instance['repo']}...")
            subprocess.run(
                ["git", "clone", f"https://github.com/{instance['repo']}.git", str(repo_path)],
                capture_output=True, timeout=300,
            )

        # Checkout base commit
        subprocess.run(["git", "-C", str(repo_path), "fetch", "--all", "--quiet"], capture_output=True, timeout=60)
        subprocess.run(["git", "-C", str(repo_path), "checkout", "-f", base_commit], capture_output=True, timeout=30)

        # Copy repo to workspace
        self._copy_repo(repo_path, work_dir)

        # Run setup commands if defined
        self._run_setup(instance, work_dir)

        # Write the issue description as README for the agent
        (work_dir / "ISSUE.md").write_text(
            f"# {instance.get('problem_statement', 'Issue')}\n\n"
            f"{self.instance_id}\n\n"
            f"Repo: {instance['repo']}\n"
            f"Base commit: {base_commit}\n",
            encoding="utf-8"
        )

        return workspace

    def _get_instance(self) -> dict:
        """Load instance from HuggingFace cache or download it."""
        import yaml

        # Try local cache first
        cache_file = self.INSTANCE_CACHE / f"{self.instance_id}.json"
        if cache_file.exists():
            return json.loads(cache_file.read_text(encoding="utf-8"))

        # Load from task.yaml metadata
        data = yaml.safe_load((self.task_dir / "task.yaml").read_text(encoding="utf-8"))
        instance = {
            "instance_id": data.get("instance_id", ""),
            "repo": data.get("repo", ""),
            "base_commit": data.get("base_commit", ""),
            "problem_statement": data.get("description", ""),
            "hints_text": "",
            "test_patch": "",
            "fail_to_pass": [],
            "pass_to_pass": [],
        }

        # Try to load from HuggingFace datasets
        try:
            from datasets import load_dataset
            ds = load_dataset("princeton-nlp/SWE-bench_Verified", split="test")
            for ex in ds:
                if ex["instance_id"] == self.instance_id:
                    instance = {
                        "instance_id": ex["instance_id"],
                        "repo": ex["repo"],
                        "base_commit": ex["base_commit"],
                        "problem_statement": ex.get("problem_statement", ""),
                        "hints_text": ex.get("hints_text", ""),
                        "test_patch": ex.get("test_patch", ""),
                        "fail_to_pass": list(ex.get("fail_to_pass", [])),
                        "pass_to_pass": list(ex.get("pass_to_pass", [])),
                    }
                    break
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            cache_file.write_text(json.dumps(instance, indent=2), encoding="utf-8")
        except ImportError:
            print("   ⚠️  datasets not installed — using task.yaml metadata only")
        except Exception as e:
            print(f"   ⚠️  Could not load from HF: {e}")

        return instance

    def _copy_repo(self, src: Path, dst: Path) -> None:
        """Copy repo contents, skip .git."""
        for item in src.iterdir():
            if item.name == ".git":
                continue
            dest = dst / item.name
            if item.is_dir():
                shutil.copytree(item, dest, dirs_exist_ok=True)
            else:
                shutil.copy2(item, dest)

    def _run_setup(self, instance: dict, work_dir: Path) -> None:
        """Run setup commands defined in the SWE-bench instance."""
        setup = instance.get("setup_commands", None)
        if not setup:
            return
        if isinstance(setup, list):
            for cmd in setup:
                subprocess.run(cmd, shell=True, cwd=str(work_dir), capture_output=True, timeout=120)

    def evaluate_patch(self, workspace: Path, output_dir: Path = None) -> dict[str, Any]:
        """Evaluate the agent's generated patch using SWE-bench methodology.

        Returns: {resolved: bool, fail_to_pass: [...], pass_to_pass: [...]}
        """
        work_dir = workspace / "workspace"
        instance = self._get_instance()
        result = {
            "resolved": False,
            "fail_to_pass_ok": 0,
            "fail_to_pass_total": len(instance.get("fail_to_pass", [])),
            "pass_to_pass_ok": 0,
            "pass_to_pass_total": len(instance.get("pass_to_pass", [])),
            "errors": [],
        }

        # 1. Try using swebench evaluation harness
        harness_result = self._try_swebench_harness(work_dir, instance)
        if harness_result:
            return harness_result

        # 2. Fallback: manual test patch evaluation
        test_patch = instance.get("test_patch", "")
        if not test_patch:
            result["errors"].append("No test patch available")
            return result

        # Write test patch to workspace and apply it
        patch_file = work_dir / "eval_test.patch"
        patch_file.write_text(test_patch, encoding="utf-8")

        # Try to apply the test patch
        try:
            subprocess.run(
                ["git", "-C", str(work_dir), "apply", str(patch_file)],
                capture_output=True, timeout=30,
            )
        except Exception as e:
            result["errors"].append(f"Could not apply test patch: {e}")

        # Run pytest on the tests that were supposed to fail→pass
        test_dir = self._find_test_dir(work_dir)
        if test_dir:
            pytest_result = subprocess.run(
                [sys.executable, "-m", "pytest", str(test_dir), "-q", "--tb=short", "-x"],
                capture_output=True, text=True, timeout=120,
                cwd=str(work_dir),
            )
            result["resolved"] = pytest_result.returncode == 0
            result["pytest_stdout"] = pytest_result.stdout
            result["pytest_stderr"] = pytest_result.stderr

        return result

    def _try_swebench_harness(self, work_dir: Path, instance: dict) -> dict | None:
        """Try using the official SWE-bench evaluation harness."""
        try:
            from swebench.harness.test_spec import make_test_spec
            from swebench.harness.docker_utils import build_image, run_evaluation

            patch_file = work_dir / "agent_patch.diff"
            if not patch_file.exists():
                return None

            # Build test spec from instance
            test_spec = make_test_spec(instance)
            image_name = f"swe-bench-eval-{self.instance_id.replace('/', '_')}"

            # Build Docker image
            build_image(test_spec, image_name)

            # Run evaluation
            eval_result = run_evaluation(
                image_name=image_name,
                patch_path=str(patch_file),
                instance=instance,
            )
            return eval_result
        except ImportError:
            return None  # swebench not installed, use fallback
        except Exception as e:
            return {"resolved": False, "errors": [f"Harness error: {e}"]}

    def _find_test_dir(self, work_dir: Path) -> Path | None:
        """Find test directory in the repo."""
        for d in work_dir.rglob("tests"):
            if d.is_dir():
                return d
        return None

    def generate_patch(self, workspace: Path) -> Path:
        """Generate a diff from the workspace's repo state."""
        work_dir = workspace / "workspace"
        patch_file = work_dir / "agent_patch.diff"

        try:
            subprocess.run(
                ["git", "-C", str(work_dir), "add", "-A"],
                capture_output=True, timeout=30,
            )
            result = subprocess.run(
                ["git", "-C", str(work_dir), "diff", "--cached"],
                capture_output=True, text=True, timeout=30,
            )
            patch_file.write_text(result.stdout, encoding="utf-8")
        except Exception as e:
            patch_file.write_text(f"; Patch generation failed: {e}", encoding="utf-8")

        return patch_file
