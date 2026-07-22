"""Scoring engine — multi-dimensional evaluation inspired by SWE-bench methodology.

Supports multiple task types:
- code:  pytest-based (functional, quality, efficiency, robustness, integration)
- text:  rubric-based (correctness, completeness, clarity, structure, relevance)
- math:  exact_match + step checking (answer, reasoning, methodology, completeness)
- plan:  constraint-based (feasibility, optimality, completeness, clarity)
- data:  output validation (correctness, efficiency, completeness, formatting)
"""

from __future__ import annotations

import difflib
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class ScoreBreakdown:
    """Detailed scoring breakdown for a single task evaluation.

    Uses generic dimension names that apply across task types.
    For code tasks these map to the traditional dimensions.
    For text/math/plan tasks they map to domain-specific ones.
    """

    correctness: float = 0.0     # How correct is the answer? (maps to functional_correctness for code)
    completeness: float = 0.0    # Are all parts addressed? (maps to code_quality for code)
    efficiency: float = 0.0      # Is it optimal/concise? (same for all)
    robustness: float = 0.0      # Edge cases, error handling? (same for all)
    clarity: float = 0.0         # Is it well-structured/readable? (maps to integration for code)

    # Aliases for backward compatibility
    @property
    def functional_correctness(self) -> float: return self.correctness
    @functional_correctness.setter
    def functional_correctness(self, v: float): self.correctness = v

    @property
    def code_quality(self) -> float: return self.completeness
    @code_quality.setter
    def code_quality(self, v: float): self.completeness = v

    @property
    def integration(self) -> float: return self.clarity
    @integration.setter
    def integration(self, v: float): self.clarity = v

    total: float = 0.0
    passed: bool = False
    task_type: str = "code"

    test_results: dict[str, Any] = field(default_factory=dict)
    lint_errors: list[str] = field(default_factory=list)
    lint_warnings: list[str] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def compute_total(self, threshold: float = 60.0) -> float:
        self.total = self.correctness + self.completeness + self.efficiency + self.robustness + self.clarity
        self.passed = self.total >= threshold
        return self.total

    def to_dict(self) -> dict[str, Any]:
        return {
            "correctness": self.correctness,
            "completeness": self.completeness,
            "efficiency": self.efficiency,
            "robustness": self.robustness,
            "clarity": self.clarity,
            "total": self.total,
            "passed": self.passed,
            "task_type": self.task_type,
            "gaps": self.gaps,
            "notes": self.notes,
        }


class ScoringAdapter:
    """Routes scoring to the right engine based on task type."""

    def __init__(self, task_dir: Path, solution_dir: Path, weights: dict[str, int] | None = None):
        self.task_dir = Path(task_dir)
        self.solution_dir = Path(solution_dir)
        self.weights = weights or {"correctness": 40, "completeness": 25, "efficiency": 15, "robustness": 10, "clarity": 10}

        # Detect task type from task.yaml or fall back to code
        self.task_type = self._detect_task_type()

    def _detect_task_type(self) -> str:
        task_yaml = self.task_dir / "task.yaml"
        if task_yaml.exists():
            data = yaml.safe_load(task_yaml.read_text(encoding="utf-8"))
            return data.get("task_type", "code")
        return "code"

    def evaluate(self) -> ScoreBreakdown:
        if self.task_type == "code":
            engine = CodeScoringEngine(self.task_dir, self.solution_dir, self.weights)
            return engine.evaluate()
        elif self.task_type == "text":
            engine = TextScoringEngine(self.task_dir, self.solution_dir, self.weights)
            return engine.evaluate()
        elif self.task_type == "math":
            engine = MathScoringEngine(self.task_dir, self.solution_dir, self.weights)
            return engine.evaluate()
        elif self.task_type == "plan":
            engine = PlanScoringEngine(self.task_dir, self.solution_dir, self.weights)
            return engine.evaluate()
        elif self.task_type == "data":
            engine = DataScoringEngine(self.task_dir, self.solution_dir, self.weights)
            return engine.evaluate()
        else:
            # Default to code
            engine = CodeScoringEngine(self.task_dir, self.solution_dir, self.weights)
            return engine.evaluate()


# ═══════════════════════════════════════════════════════════════════════════
# CODE SCORING (existing pytest-based)
# ═══════════════════════════════════════════════════════════════════════════

class CodeScoringEngine:
    def __init__(self, task_dir: Path, solution_dir: Path, weights: dict[str, int]):
        self.task_dir = Path(task_dir)
        self.solution_dir = Path(solution_dir)
        self.weights = weights
        self._test_results: dict[str, Any] = {}

    def evaluate(self) -> ScoreBreakdown:
        score = ScoreBreakdown(task_type="code")
        score.correctness = self._evaluate_functional()
        score.test_results = self._test_results
        score.completeness, score.lint_errors, score.lint_warnings = self._evaluate_code_quality()
        score.efficiency = self._evaluate_efficiency()
        score.robustness = self._evaluate_robustness()
        score.clarity = self._evaluate_integration()
        score.compute_total()
        return score

    def _evaluate_functional(self) -> float:
        max_score = float(self.weights.get("correctness", 40))
        test_dir = self.task_dir / "tests"
        if not test_dir.exists():
            return 0.0
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", str(test_dir), "-q", "--tb=short"],
                capture_output=True, text=True, timeout=120,
                cwd=str(self.solution_dir),
            )
            self._test_results = {"stdout": result.stdout, "stderr": result.stderr, "returncode": result.returncode}
            if result.returncode == 0:
                return max_score
            passed, total = self._parse_pytest(result.stdout)
            return round(max_score * (passed / total), 1) if total > 0 else 0.0
        except (subprocess.TimeoutExpired, Exception):
            return 0.0

    @staticmethod
    def _parse_pytest(stdout: str) -> tuple[int, int]:
        passed = int((re.search(r"(\d+)\s+passed", stdout) or (0,))[0])
        failed = int((re.search(r"(\d+)\s+failed", stdout) or (0,))[0])
        return passed, passed + failed

    def _evaluate_code_quality(self) -> tuple[float, list[str], list[str]]:
        max_score = float(self.weights.get("completeness", 25))
        errors, warnings, penalty = [], [], 0.0
        for py_file in self.solution_dir.rglob("*.py"):
            content = py_file.read_text(encoding="utf-8", errors="ignore")
            if "TODO" in content:
                penalty += 3; warnings.append(f"{py_file.name}: TODO")
            if "\n    pass\n" in content or content.strip().endswith("pass"):
                penalty += 5; errors.append(f"{py_file.name}: stub pass")
            if "raise NotImplementedError" in content:
                penalty += 5; errors.append(f"{py_file.name}: NotImplementedError")
        try:
            result = subprocess.run(["ruff", "check", str(self.solution_dir), "--output-format", "concise"],
                                    capture_output=True, text=True, timeout=30)
            if result.stdout.strip():
                issues = result.stdout.strip().split("\n")
                penalty += min(len(issues) * 2, 15)
                errors.extend(issues[:5])
        except (FileNotFoundError, subprocess.TimeoutExpired):
            warnings.append("ruff not available")
        return max(0.0, max_score - penalty), errors, warnings

    def _evaluate_efficiency(self) -> float:
        max_score = float(self.weights.get("efficiency", 15))
        penalty = 0.0
        for py_file in self.solution_dir.rglob("*.py"):
            content = py_file.read_text(encoding="utf-8", errors="ignore")
            lines = content.split("\n")
            depth = 0
            for line in lines:
                s = line.strip()
                if any(s.startswith(k) for k in ("for ", "while ")):
                    depth += 1
                    if depth > 1: penalty += 2
                elif s == "": depth = 0
        return round(max(0.0, max_score - min(penalty, max_score)), 1)

    def _evaluate_robustness(self) -> float:
        max_score = float(self.weights.get("robustness", 10))
        score = max_score
        for py_file in self.solution_dir.rglob("*.py"):
            content = py_file.read_text(encoding="utf-8", errors="ignore")
            if "try:" not in content and "except" not in content: score -= 2
            if "raise" not in content and "ValueError" not in content: score -= 1
            if "->" not in content: score -= 2
        return max(0.0, score)

    def _evaluate_integration(self) -> float:
        max_score = float(self.weights.get("clarity", 10))
        for py_file in self.solution_dir.rglob("*.py"):
            if py_file.name.startswith("__") or py_file.name.startswith("test_"): continue
            try:
                compile(py_file.read_text(), str(py_file), "exec")
            except SyntaxError:
                return 0.0
        return max_score


# ═══════════════════════════════════════════════════════════════════════════
# TEXT SCORING (rubric-based — for docs, writing, analysis)
# ═══════════════════════════════════════════════════════════════════════════

class TextScoringEngine:
    def __init__(self, task_dir: Path, solution_dir: Path, weights: dict[str, int]):
        self.task_dir = task_dir
        self.solution_dir = solution_dir
        self.weights = weights

    def evaluate(self) -> ScoreBreakdown:
        score = ScoreBreakdown(task_type="text")
        rubric = self._load_rubric()
        output_text = self._read_output()

        if not output_text:
            score.gaps.append("No output found")
            return score

        # Score each rubric criterion
        for criterion in rubric.get("criteria", []):
            name = criterion["name"]
            weight = criterion.get("weight", 10)
            checks = criterion.get("checks", [])
            max_points = weight

            points = 0.0
            for check in checks:
                if self._check_criterion(output_text, check):
                    points += max_points / len(checks)

            if name == "correctness": score.correctness = min(points, float(self.weights.get("correctness", 40)))
            elif name == "completeness": score.completeness = min(points, float(self.weights.get("completeness", 25)))
            elif name == "efficiency": score.efficiency = min(points, float(self.weights.get("efficiency", 15)))
            elif name == "robustness": score.robustness = min(points, float(self.weights.get("robustness", 10)))
            elif name == "clarity": score.clarity = min(points, float(self.weights.get("clarity", 10)))

        # Also check reference similarity if available
        ref_score = self._reference_similarity(output_text)
        score.correctness = max(score.correctness, ref_score * 0.5)

        score.compute_total()
        return score

    def _load_rubric(self) -> dict:
        rubric_file = self.task_dir / "tests" / "rubric.yaml"
        if rubric_file.exists():
            return yaml.safe_load(rubric_file.read_text(encoding="utf-8"))
        return {"criteria": []}

    def _read_output(self) -> str:
        """Read all text output from solution directory."""
        texts = []
        for f in sorted(self.solution_dir.rglob("*")):
            if f.is_file() and f.suffix in (".txt", ".md", ".sql", ".yaml", ".json", ".py", ".sh", ".dockerfile", ""):
                try:
                    texts.append(f.read_text(encoding="utf-8", errors="ignore"))
                except Exception:
                    pass
        return "\n".join(texts)

    def _check_criterion(self, text: str, check: str) -> bool:
        """Check if text satisfies a criterion. Supports keywords and patterns."""
        text_lower = text.lower()
        check_lower = check.lower()

        # Keyword presence
        if check_lower.startswith("contains:"):
            keyword = check_lower.replace("contains:", "").strip()
            return keyword in text_lower

        # Pattern/regex
        if check_lower.startswith("regex:"):
            pattern = check[6:].strip()
            return bool(re.search(pattern, text, re.IGNORECASE | re.DOTALL))

        # Min length
        if check_lower.startswith("min_length:"):
            n = int(check.split(":")[1].strip())
            return len(text.split()) >= n

        # Has structure
        if check_lower.startswith("has_structure:"):
            struct = check.split(":")[1].strip()
            return struct.lower() in text_lower

        # Default: general keyword presence
        return check_lower in text_lower

    def _reference_similarity(self, output: str) -> float:
        """Compare output to reference solution."""
        ref_file = self.task_dir / "tests" / "reference.txt"
        if not ref_file.exists():
            ref_file = self.task_dir / "gold" / "reference.txt"
        if not ref_file.exists():
            return 0.0

        reference = ref_file.read_text(encoding="utf-8", errors="ignore")
        if not reference.strip():
            return 0.0

        # Use difflib for fuzzy matching
        ratio = difflib.SequenceMatcher(None, output.lower(), reference.lower()).ratio()
        return ratio * float(self.weights.get("correctness", 40))


# ═══════════════════════════════════════════════════════════════════════════
# MATH SCORING (exact + step checking)
# ═══════════════════════════════════════════════════════════════════════════

class MathScoringEngine:
    def __init__(self, task_dir: Path, solution_dir: Path, weights: dict[str, int]):
        self.task_dir = task_dir
        self.solution_dir = solution_dir
        self.weights = weights

    def evaluate(self) -> ScoreBreakdown:
        score = ScoreBreakdown(task_type="math")
        output = self._read_output()
        if not output:
            score.gaps.append("No output")
            return score

        # Load expected answer
        expected = self._load_expected()
        if not expected:
            score.gaps.append("No expected answer defined")
            return score

        # 1. Answer correctness (exact or numeric match)
        score.correctness = self._check_answer(output, expected)

        # 2. Reasoning/steps (check for methodology)
        score.completeness = self._check_reasoning(output)

        # 3. Efficiency (conciseness of solution)
        score.efficiency = self._check_efficiency(output, expected)

        # 4. Robustness (edge cases, verification)
        score.robustness = self._check_robustness(output, expected)

        # 5. Clarity (formatting, step labeling)
        score.clarity = self._check_clarity(output)

        score.compute_total()
        return score

    def _read_output(self) -> str:
        texts = []
        for f in sorted(self.solution_dir.rglob("*")):
            if f.is_file() and f.suffix in (".txt", ".md", ".py", ""):
                try:
                    texts.append(f.read_text(encoding="utf-8", errors="ignore"))
                except Exception:
                    pass
        return "\n".join(texts)

    def _load_expected(self) -> dict:
        exp_file = self.task_dir / "tests" / "expected.json"
        if exp_file.exists():
            return json.loads(exp_file.read_text(encoding="utf-8"))
        return {}

    def _check_answer(self, output: str, expected: dict) -> float:
        max_score = float(self.weights.get("correctness", 40))
        expected_answer = expected.get("answer")
        if expected_answer is None:
            return 0.0

        # Try numeric comparison
        if isinstance(expected_answer, (int, float)):
            # Find numbers in output
            numbers = re.findall(r'[-+]?\d*\.?\d+', output)
            for n in numbers:
                try:
                    if abs(float(n) - float(expected_answer)) < 0.001:
                        return max_score
                except ValueError:
                    pass
            # Partial credit: answer present but wrong
            if numbers:
                return max_score * 0.3
            return 0.0

        # String comparison
        if isinstance(expected_answer, str):
            if expected_answer.lower() in output.lower():
                return max_score
            return max_score * 0.2  # Partial: output exists but answer not found

        return 0.0

    def _check_reasoning(self, output: str) -> float:
        max_score = float(self.weights.get("completeness", 25))
        # Check for reasoning steps: step labels, logical flow
        indicators = [
            r'step\s*\d', r'first', r'then', r'finally', r'therefore',
            r'because', r'since', r'let\s', r'suppose', r'assume',
            r'calculate', r'compute', r'solve', r'formula',
        ]
        found = sum(1 for pat in indicators if re.search(pat, output, re.IGNORECASE))
        return min(max_score, found * (max_score / max(len(indicators), 1)))

    def _check_efficiency(self, output: str, expected: dict) -> float:
        max_score = float(self.weights.get("efficiency", 15))
        expected_method = expected.get("method", "")
        if expected_method and expected_method.lower() in output.lower():
            return max_score
        # Check for concise solution (not excessively long)
        if len(output.split()) < 500:
            return max_score * 0.7
        return max_score * 0.3

    def _check_robustness(self, output: str, expected: dict) -> float:
        max_score = float(self.weights.get("robustness", 10))
        edge_cases = expected.get("edge_cases", [])
        if not edge_cases:
            return max_score * 0.5
        found = sum(1 for ec in edge_cases if ec.lower() in output.lower())
        return max_score * (found / len(edge_cases))

    def _check_clarity(self, output: str) -> float:
        max_score = float(self.weights.get("clarity", 10))
        score = 0.0
        if re.search(r'^#|^\*\*|^##', output, re.MULTILINE): score += 3  # Headers
        if re.search(r'\d+\.\s', output): score += 3  # Numbered steps
        if len(output.split('\n')) > 3: score += 2  # Multi-line structure
        if len(output) > 50: score += 2  # Not too short
        return min(max_score, score)


# ═══════════════════════════════════════════════════════════════════════════
# PLAN SCORING (constraint-based)
# ═══════════════════════════════════════════════════════════════════════════

class PlanScoringEngine:
    def __init__(self, task_dir: Path, solution_dir: Path, weights: dict[str, int]):
        self.task_dir = task_dir
        self.solution_dir = solution_dir
        self.weights = weights

    def evaluate(self) -> ScoreBreakdown:
        score = ScoreBreakdown(task_type="plan")
        output = self._read_output()
        if not output:
            score.gaps.append("No output")
            return score

        constraints = self._load_constraints()

        # 1. Correctness: all constraints satisfied?
        score.correctness = self._check_constraints(output, constraints)

        # 2. Completeness: all required sections present?
        score.completeness = self._check_completeness(output, constraints)

        # 3. Efficiency: optimal solution?
        score.efficiency = self._check_optimality(output, constraints)

        # 4. Robustness: contingencies, risks addressed?
        score.robustness = self._check_robustness_plan(output)

        # 5. Clarity: well-structured plan?
        score.clarity = self._check_clarity_plan(output)

        score.compute_total()
        return score

    def _read_output(self) -> str:
        texts = []
        for f in sorted(self.solution_dir.rglob("*")):
            if f.is_file() and f.suffix in (".txt", ".md", ".yaml", ".json", ""):
                try:
                    texts.append(f.read_text(encoding="utf-8", errors="ignore"))
                except Exception:
                    pass
        return "\n".join(texts)

    def _load_constraints(self) -> dict:
        c_file = self.task_dir / "tests" / "constraints.yaml"
        if c_file.exists():
            return yaml.safe_load(c_file.read_text(encoding="utf-8"))
        return {}

    def _check_constraints(self, output: str, constraints: dict) -> float:
        max_score = float(self.weights.get("correctness", 40))
        required = constraints.get("required_elements", [])
        forbidden = constraints.get("forbidden_elements", [])
        if not required:
            return max_score * 0.5

        points = 0.0
        for elem in required:
            if elem.lower() in output.lower():
                points += max_score / len(required)
        for elem in forbidden:
            if elem.lower() in output.lower():
                points -= max_score / len(forbidden) if forbidden else 0
        return max(0.0, points)

    def _check_completeness(self, output: str, constraints: dict) -> float:
        max_score = float(self.weights.get("completeness", 25))
        sections = constraints.get("required_sections", ["overview", "steps", "timeline", "resources"])
        found = sum(1 for s in sections if s.lower() in output.lower())
        return max_score * (found / len(sections)) if sections else max_score * 0.5

    def _check_optimality(self, output: str, constraints: dict) -> float:
        max_score = float(self.weights.get("efficiency", 15))
        # Check for optimization language
        indicators = ["optimal", "efficient", "minimize", "maximize", "best", "shortest", "fastest", "cost"]
        found = sum(1 for ind in indicators if ind in output.lower())
        return max_score * min(1.0, found / 4)

    def _check_robustness_plan(self, output: str) -> float:
        max_score = float(self.weights.get("robustness", 10))
        indicators = ["risk", "contingency", "fallback", "backup", "alternative", "if.*fail", "mitigation"]
        found = sum(1 for ind in indicators if re.search(ind, output, re.IGNORECASE))
        return max_score * min(1.0, found / 3)

    def _check_clarity_plan(self, output: str) -> float:
        max_score = float(self.weights.get("clarity", 10))
        score = 0.0
        if re.search(r'^#|^##', output, re.MULTILINE): score += 3
        if re.search(r'\d+\.\s', output): score += 3
        if len(output.split('\n')) > 5: score += 2
        if len(output) > 100: score += 2
        return min(max_score, score)


# ═══════════════════════════════════════════════════════════════════════════
# DATA SCORING (SQL/pandas output validation)
# ═══════════════════════════════════════════════════════════════════════════

class DataScoringEngine:
    def __init__(self, task_dir: Path, solution_dir: Path, weights: dict[str, int]):
        self.task_dir = task_dir
        self.solution_dir = solution_dir
        self.weights = weights

    def evaluate(self) -> ScoreBreakdown:
        score = ScoreBreakdown(task_type="data")
        output = self._read_output()
        if not output:
            score.gaps.append("No output")
            return score

        # Try running as SQL or Python, then use rubric
        # For simplicity, use rubric + test script if available
        score.correctness = self._run_validation_script()
        score.completeness = self._rubric_check(output, "completeness")
        score.efficiency = self._rubric_check(output, "efficiency")
        score.robustness = self._rubric_check(output, "robustness")
        score.clarity = self._rubric_check(output, "clarity")
        score.compute_total()
        return score

    def _read_output(self) -> str:
        texts = []
        for f in sorted(self.solution_dir.rglob("*")):
            if f.is_file() and f.suffix in (".sql", ".py", ".txt", ".md", ".csv", ".json", ""):
                try:
                    texts.append(f.read_text(encoding="utf-8", errors="ignore"))
                except Exception:
                    pass
        return "\n".join(texts)

    def _run_validation_script(self) -> float:
        """Run a Python validation script if available."""
        max_score = float(self.weights.get("correctness", 40))
        script = self.task_dir / "tests" / "validate.py"
        if not script.exists():
            return 0.0

        try:
            result = subprocess.run(
                [sys.executable, str(script)],
                capture_output=True, text=True, timeout=60,
                cwd=str(self.solution_dir),
                env={**__import__("os").environ, "SOLUTION_DIR": str(self.solution_dir)},
            )
            if result.returncode == 0:
                return max_score
            # Parse score from stdout if available
            match = re.search(r'SCORE:\s*(\d+(?:\.\d+)?)', result.stdout)
            if match:
                return min(max_score, float(match.group(1)))
            return max_score * 0.2
        except Exception:
            return 0.0

    def _rubric_check(self, output: str, dimension: str) -> float:
        """Evaluate a scoring dimension for data tasks.

        If a rubric.yaml exists, use it for keyword-based checks.
        If no rubric exists, fall back to CONTENT-AWARE heuristics
        (not a static constant) so the score actually reflects output quality.
        """
        weight_map = {"completeness": 25, "efficiency": 15, "robustness": 10, "clarity": 10}
        max_score = float(self.weights.get(dimension, weight_map.get(dimension, 10)))

        rubric_file = self.task_dir / "tests" / "rubric.yaml"
        if rubric_file.exists():
            rubric = yaml.safe_load(rubric_file.read_text(encoding="utf-8"))
            for crit in rubric.get("criteria", []):
                if crit.get("name") == dimension:
                    checks = crit.get("checks", [])
                    points = sum(1.0 for c in checks if c.lower() in output.lower())
                    return max_score * (points / len(checks)) if checks else max_score * 0.5
            return max_score * 0.5

        # ── CONTENT-AWARE FALLBACK (replaces static max_score * 0.3) ──
        # When no rubric.yaml exists, evaluate the actual output content
        # so the score VARIES with input quality instead of being constant.
        output_lower = output.lower().strip()
        if not output_lower:
            return 0.0

        if dimension == "completeness":
            # Check for SQL/Pandas completeness indicators
            score = 0.0
            if "select" in output_lower or "insert" in output_lower or "update" in output_lower:
                score += max_score * 0.3  # Has SQL operations
            if "join" in output_lower or "group by" in output_lower or "order by" in output_lower:
                score += max_score * 0.25  # Has advanced SQL
            if "where" in output_lower or "having" in output_lower:
                score += max_score * 0.2  # Has filtering
            if "import pandas" in output_lower or "import numpy" in output_lower or "df[" in output_lower:
                score += max_score * 0.25  # Uses data libraries
            return min(max_score, score)

        if dimension == "efficiency":
            # Penalize excessively long solutions
            lines = output_lower.split("\n")
            non_empty = [l for l in lines if l.strip()]
            if len(non_empty) < 5:
                return max_score * 0.3
            if len(non_empty) > 100:
                return max_score * 0.4  # Too verbose
            return max_score * 0.8  # Reasonable length

        if dimension == "robustness":
            # Check for error handling in data code
            score = 0.0
            if "try:" in output_lower or "except" in output_lower:
                score += max_score * 0.4
            if "isnull" in output_lower or "isna" in output_lower or "notnull" in output_lower:
                score += max_score * 0.3  # Null checks
            if "if" in output_lower and "else" in output_lower:
                score += max_score * 0.3  # Conditional logic
            return min(max_score, score)

        if dimension == "clarity":
            # Check for comments, formatting, readable structure
            score = 0.0
            if "#" in output_lower and ("--" in output_lower or '"""' in output_lower):
                score += max_score * 0.4  # Has comments
            if "\n\n" in output_lower:
                score += max_score * 0.3  # Has paragraph breaks
            if any(kw in output_lower for kw in ["select", "from", "where", "import"]):
                score += max_score * 0.3  # Has structured syntax
            return min(max_score, score)

        return max_score * 0.3  # Final fallback (should rarely reach here)


# ── Legacy compatibility ──────────────────────────────────────────────────
ScoringEngine = ScoringAdapter
