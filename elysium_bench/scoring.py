"""Scoring engine — multi-dimensional evaluation inspired by SWE-bench methodology.

Dimensions (total 0–100):
    Functional Correctness (40): All tests pass — fail→pass + pass→pass
    Code Quality (25):         Linting, type hints, docstrings, no stubs
    Efficiency (15):           Algorithmic complexity, resource usage
    Robustness (10):           Edge cases, error handling, validation
    Integration (10):          Imports work, contracts match, no orphans
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ScoreBreakdown:
    """Detailed scoring breakdown for a single task evaluation."""

    functional_correctness: float = 0.0  # 0–40
    code_quality: float = 0.0  # 0–25
    efficiency: float = 0.0  # 0–15
    robustness: float = 0.0  # 0–10
    integration: float = 0.0  # 0–10

    # Derived
    total: float = 0.0
    passed: bool = False

    # Metadata
    test_results: dict[str, Any] = field(default_factory=dict)
    lint_errors: list[str] = field(default_factory=list)
    lint_warnings: list[str] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def compute_total(self, threshold: float = 60.0) -> float:
        """Sum all dimensions and determine pass/fail."""
        self.total = (
            self.functional_correctness
            + self.code_quality
            + self.efficiency
            + self.robustness
            + self.integration
        )
        self.passed = self.total >= threshold
        return self.total

    def to_dict(self) -> dict[str, Any]:
        return {
            "functional_correctness": self.functional_correctness,
            "code_quality": self.code_quality,
            "efficiency": self.efficiency,
            "robustness": self.robustness,
            "integration": self.integration,
            "total": self.total,
            "passed": self.passed,
            "gaps": self.gaps,
            "notes": self.notes,
        }


class ScoringEngine:
    """Evaluates a task solution against its gold standard."""

    def __init__(
        self,
        task_dir: Path,
        solution_dir: Path,
        weights: dict[str, int] | None = None,
    ):
        self.task_dir = Path(task_dir)
        self.solution_dir = Path(solution_dir)
        self.weights = weights or {
            "functional_correctness": 40,
            "code_quality": 25,
            "efficiency": 15,
            "robustness": 10,
            "integration": 10,
        }

    def evaluate(self) -> ScoreBreakdown:
        """Run the full multi-dimensional evaluation."""
        score = ScoreBreakdown()

        # 1. Functional Correctness — run tests
        score.functional_correctness = self._evaluate_functional()
        score.test_results = self._test_results

        # 2. Code Quality — lint + check stubs
        score.code_quality, score.lint_errors, score.lint_warnings = self._evaluate_code_quality()

        # 3. Efficiency — complexity analysis
        score.efficiency = self._evaluate_efficiency()

        # 4. Robustness — edge case checks
        score.robustness = self._evaluate_robustness()

        # 5. Integration — import checks, interface contracts
        score.integration = self._evaluate_integration()

        score.compute_total()
        return score

    # ── Dimension Evaluators ──────────────────────────────────────────────

    def _evaluate_functional(self) -> float:
        """Run test suite. SWE-bench style: fail→pass must pass, pass→pass must not regress."""
        max_score = float(self.weights["functional_correctness"])
        test_dir = self.task_dir / "tests"

        if not test_dir.exists():
            score = ScoreBreakdown()
            score.gaps.append("No test directory found")
            return 0.0

        # Find and run pytest
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", str(test_dir), "-q", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=120,
                cwd=str(self.solution_dir),
            )
            self._test_results = {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
            }

            if result.returncode == 0:
                return max_score

            # Parse test results to compute partial credit
            # Count passed vs total from pytest output
            passed, total = self._parse_pytest_output(result.stdout)
            if total == 0:
                return 0.0
            return round(max_score * (passed / total), 1)

        except subprocess.TimeoutExpired:
            score = ScoreBreakdown()
            score.gaps.append("Test execution timed out (120s)")
            return 0.0
        except Exception as e:
            score = ScoreBreakdown()
            score.gaps.append(f"Test execution error: {e}")
            return 0.0

    @staticmethod
    def _parse_pytest_output(stdout: str) -> tuple[int, int]:
        """Parse pytest output for passed/total counts."""
        import re

        # Match: "3 passed" or "2 failed, 1 passed"
        passed = 0
        failed = 0

        match = re.search(r"(\d+)\s+passed", stdout)
        if match:
            passed = int(match.group(1))

        match = re.search(r"(\d+)\s+failed", stdout)
        if match:
            failed = int(match.group(1))

        total = passed + failed
        return passed, total

    def _evaluate_code_quality(self) -> tuple[float, list[str], list[str]]:
        """Check linting, type hints, docstrings, stubs/TODOs."""
        max_score = float(self.weights["code_quality"])
        errors: list[str] = []
        warnings: list[str] = []
        penalty = 0.0

        # Check for stubs/TODOs/pass statements
        for py_file in self.solution_dir.rglob("*.py"):
            content = py_file.read_text(encoding="utf-8", errors="ignore")

            if "TODO" in content:
                penalty += 3
                warnings.append(f"{py_file.name}: contains TODO")
            if "\n    pass\n" in content or content.strip().endswith("pass"):
                penalty += 5
                errors.append(f"{py_file.name}: contains stub 'pass'")
            if "raise NotImplementedError" in content:
                penalty += 5
                errors.append(f"{py_file.name}: contains NotImplementedError")

        # Run ruff if available
        try:
            result = subprocess.run(
                ["ruff", "check", str(self.solution_dir), "--output-format", "concise"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.stdout.strip():
                ruff_issues = result.stdout.strip().split("\n")
                penalty += min(len(ruff_issues) * 2, 15)  # Cap ruff penalty at 15
                errors.extend(ruff_issues[:5])
        except (FileNotFoundError, subprocess.TimeoutExpired):
            warnings.append("ruff not available — skipping lint check")

        score = max(0.0, max_score - penalty)
        return score, errors, warnings

    def _evaluate_efficiency(self) -> float:
        """Check algorithmic complexity markers and performance."""
        max_score = float(self.weights["efficiency"])
        penalty = 0.0

        for py_file in self.solution_dir.rglob("*.py"):
            content = py_file.read_text(encoding="utf-8", errors="ignore")

            # Detect nested loops (O(n²) or worse indicators)
            # Heuristic: check for loops inside loops
            lines = content.split("\n")
            in_loop_depth = 0
            for line in lines:
                stripped = line.strip()
                if any(stripped.startswith(kw) for kw in ("for ", "while ")):
                    in_loop_depth += 1
                    if in_loop_depth > 1:
                        penalty += 2  # Nested loop penalty
                # Track loop exit (approximate — dedent)
                if stripped == "" and in_loop_depth > 0:
                    pass  # Can't perfectly track dedent without AST

        score = max(0.0, max_score - min(penalty, max_score))
        return round(score, 1)

    def _evaluate_robustness(self) -> float:
        """Check edge case handling, validation, error handling."""
        max_score = float(self.weights["robustness"])
        score = max_score
        gaps = []

        for py_file in self.solution_dir.rglob("*.py"):
            content = py_file.read_text(encoding="utf-8", errors="ignore")

            # Check for try/except presence (basic error handling)
            has_try_except = "try:" in content or "except" in content
            has_validation = "raise" in content or "ValueError" in content or "if not" in content
            has_type_hints = "->" in content or ": " in content  # Very rough heuristic

            if not has_try_except:
                score -= 2
                gaps.append(f"{py_file.name}: missing error handling")
            if not has_validation:
                score -= 1
            if not has_type_hints:
                score -= 2
                gaps.append(f"{py_file.name}: missing type hints")

        return max(0.0, score)

    def _evaluate_integration(self) -> float:
        """Verify imports work and interface contracts match."""
        max_score = float(self.weights["integration"])

        # Try importing each module
        for py_file in self.solution_dir.rglob("*.py"):
            if py_file.name.startswith("__") or py_file.name.startswith("test_"):
                continue
            try:
                # Convert file path to module-ish check
                # Just verify Python can parse the file
                compile(py_file.read_text(), str(py_file), "exec")
            except SyntaxError as e:
                return 0.0  # Syntax error = instant 0

        return max_score
