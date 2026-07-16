"""Main benchmark runner — orchestrates the improvement loop."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import yaml
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table

from .harness import Harness
from .hermes_interface import HermesInterface
from .metrics import ImprovementMetrics
from .scoring import ScoreBreakdown, ScoringEngine
from .task_registry import Category, Task, TaskRegistry

console = Console()


class BenchmarkRunner:
    """Orchestrates the full benchmark: load tasks → run improvement loop → score → report."""

    def __init__(self, config_path: Path = Path("config.yaml")):
        self.config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        self.tasks_root = config_path.parent / "tasks"
        self.results_dir = config_path.parent / self.config["reporting"]["output_dir"]
        self.results_dir.mkdir(parents=True, exist_ok=True)

        # Components
        self.registry = TaskRegistry(self.tasks_root, self.config)
        self.harness = Harness(
            mode=self.config["environment"]["mode"],
            cleanup=self.config["environment"]["cleanup"],
        )
        self.hermes = HermesInterface(
            skill=self.config["hermes"]["skill"],
            subagents_max=self.config["hermes"]["subagents_max"],
            quality_threshold=self.config["hermes"]["quality_threshold"],
            retries_max=self.config["hermes"]["retries_max"],
        )

        # State
        self.all_results: dict[str, Any] = {}
        self.improvement_metrics: dict[str, ImprovementMetrics] = {}

    def run(self) -> dict[str, Any]:
        """Execute the full benchmark suite."""
        console.print("\n[bold cyan]🚀 Elysium-Bench v0.1.0[/bold cyan]")
        console.print("   Multi-Agent Self-Improvement Benchmark\n")

        # 1. Discover tasks
        console.print("[bold]Phase 1:[/bold] Discovering tasks...")
        categories = self.registry.discover()
        console.print(self.registry.summary())
        console.print()

        if not categories:
            console.print("[bold red]❌ No tasks discovered! Exiting.[/bold red]")
            return {}

        # 2. Run improvement loop for each category
        for category in categories:
            console.print(f"\n[bold cyan]{'='*60}[/bold cyan]")
            console.print(f"[bold]Category: {category.name} ({category.id})[/bold]")
            console.print(f"[bold cyan]{'='*60}[/bold cyan]\n")

            metrics = self._run_improvement_loop(category)
            self.improvement_metrics[category.id] = metrics

        # 3. Generate final report
        report = self._generate_report()
        self._save_results(report)

        return report

    def _run_improvement_loop(self, category: Category) -> ImprovementMetrics:
        """Run the improvement loop for one category.

        Flow: Task 1 → Task 2 → ... → Task N → Task 1 (re-run) → Compare
        """
        tasks = category.tasks
        loop_config = self.config["improvement_loop"]
        first_task_index = loop_config["first"] - 1  # 0-indexed
        sequence_count = min(loop_config["sequence"], len(tasks))

        metrics = ImprovementMetrics(category=category.id)

        # Phase A: Run Task 1 (baseline)
        baseline_task = tasks[first_task_index]
        console.print(f"[bold yellow]📌 PHASE A: Baseline — {baseline_task.id}: {baseline_task.name}[/bold yellow]")

        task1_result = self._run_single_task(baseline_task, attempt="first")
        task1_score = self._score_task(baseline_task, task1_result)
        metrics.task1_first_score = task1_score
        console.print(f"   Score: [bold]{task1_score.total:.1f}/100[/bold] {'✅' if task1_score.passed else '❌'}\n")

        # Phase B: Run remaining tasks (2..N)
        console.print(f"[bold yellow]📌 PHASE B: Sequence — {sequence_count - 1} tasks[/bold yellow]")
        sequence_tasks = [t for i, t in enumerate(tasks) if i != first_task_index][: sequence_count - 1]

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            seq_progress = progress.add_task("Running sequence...", total=len(sequence_tasks))

            for task in sequence_tasks:
                progress.update(seq_progress, description=f"  {task.id}: {task.name[:40]}...")

                result = self._run_single_task(task, attempt="sequence")
                score = self._score_task(task, result)
                metrics.sequence_scores.append(score)

                console.print(f"   {task.id}: [bold]{score.total:.1f}/100[/bold] {'✅' if score.passed else '❌'}")
                progress.advance(seq_progress)

        console.print()

        # Phase C: Re-run Task 1 (learning check)
        if loop_config["re_run"]:
            console.print(f"[bold yellow]📌 PHASE C: Re-Run — {baseline_task.id}: {baseline_task.name}[/bold yellow]")
            task1_rerun = self._run_single_task(baseline_task, attempt="rerun")
            task1_rerun_score = self._score_task(baseline_task, task1_rerun)
            metrics.task1_rerun_score = task1_rerun_score

            delta = task1_rerun_score.total - task1_score.total
            direction = "📈 IMPROVED" if delta > 0 else "📉 DECLINED" if delta < 0 else "➡️ UNCHANGED"
            console.print(f"   Score: [bold]{task1_rerun_score.total:.1f}/100[/bold] | Δ: {delta:+.1f} | {direction}\n")
        else:
            # If no re-run, use first score as rerun (no delta)
            metrics.task1_rerun_score = task1_score

        # Compute all metrics
        metrics.compute(learning_threshold=self.config["thresholds"]["learning_min"])
        console.print(metrics.summary())
        console.print()

        return metrics

    def _run_single_task(self, task: Task, attempt: str = "first") -> dict[str, Any]:
        """Execute a single task through the harness + Hermes."""
        start = time.time()

        # 1. Create isolated workspace
        source_dir = task.repo_dir or task.task_dir
        workspace = self.harness.create_workspace(f"{task.id}_{attempt}", source_dir)

        # 2. Copy test files into workspace
        if task.test_dir and task.test_dir.exists():
            import shutil

            dest_test = workspace / "workspace" / "tests"
            if not dest_test.exists():
                shutil.copytree(task.test_dir, dest_test, dirs_exist_ok=True)

        # 3. Execute via Hermes
        result = self.hermes.execute_task(
            task_id=task.id,
            task_description=task.description,
            workspace=workspace,
            timeout=task.timeout_seconds,
        )

        elapsed = time.time() - start
        result["elapsed_seconds"] = round(elapsed, 1)
        result["task_id"] = task.id
        result["attempt"] = attempt
        result["workspace"] = str(workspace)

        return result

    def _score_task(self, task: Task, task_result: dict[str, Any]) -> ScoreBreakdown:
        """Score a completed task using the multi-dimensional engine."""
        workspace = Path(task_result.get("workspace", ".")) / "workspace"
        engine = ScoringEngine(
            task_dir=task.task_dir or Path("."),
            solution_dir=workspace,
            weights=self.config["scoring"],
        )
        return engine.evaluate()

    def _generate_report(self) -> dict[str, Any]:
        """Generate the comprehensive benchmark report."""
        console.print(f"\n[bold cyan]{'='*60}[/bold cyan]")
        console.print("[bold cyan]📊 FINAL REPORT[/bold cyan]")
        console.print(f"[bold cyan]{'='*60}[/bold cyan]\n")

        # Overall scores
        overall_scores = []
        for cat_id, metrics in self.improvement_metrics.items():
            if metrics.task1_first_score:
                overall_scores.append(metrics.task1_first_score.total)
            if metrics.task1_rerun_score:
                overall_scores.append(metrics.task1_rerun_score.total)

        overall_avg = sum(overall_scores) / len(overall_scores) if overall_scores else 0.0

        # Table
        table = Table(title="Elysium-Bench Results")
        table.add_column("Category", style="cyan")
        table.add_column("Task 1 First", justify="right")
        table.add_column("Task 1 Re-run", justify="right")
        table.add_column("Δ Score", justify="right")
        table.add_column("Learning?", justify="center")
        table.add_column("Transfer Eff.", justify="right")
        table.add_column("Stability", justify="right")

        for cat_id, metrics in self.improvement_metrics.items():
            first = f"{metrics.task1_first_score.total:.1f}" if metrics.task1_first_score else "N/A"
            rerun = f"{metrics.task1_rerun_score.total:.1f}" if metrics.task1_rerun_score else "N/A"
            delta = f"{metrics.delta_absolute:+.1f}" if metrics.task1_first_score and metrics.task1_rerun_score else "N/A"
            learning = "✅" if metrics.learning_detected else "❌"
            transfer = f"{metrics.transfer_efficiency:.2f}"
            stability = f"{metrics.stability:.2f}"

            table.add_row(cat_id, first, rerun, delta, learning, transfer, stability)

        console.print(table)
        console.print(f"\n[bold]Overall Average Score: {overall_avg:.1f}/100[/bold]")

        # Build report dict
        report = {
            "benchmark": "Elysium-Bench",
            "version": "0.1.0",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "overall_score": round(overall_avg, 1),
            "categories": {},
            "improvement_detected": any(
                m.learning_detected for m in self.improvement_metrics.values()
            ),
        }

        for cat_id, metrics in self.improvement_metrics.items():
            report["categories"][cat_id] = metrics.to_dict()

        self.all_results = report
        return report

    def _save_results(self, report: dict[str, Any]) -> None:
        """Save results to disk in all configured formats."""
        timestamp = time.strftime("%Y%m%d_%H%M%S")

        # JSON
        json_path = self.results_dir / f"results_{timestamp}.json"
        json_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
        console.print(f"\n📁 Results saved: {json_path}")

        # Markdown
        md_path = self.results_dir / f"results_{timestamp}.md"
        md_content = self._format_markdown(report)
        md_path.write_text(md_content, encoding="utf-8")
        console.print(f"📁 Markdown report: {md_path}")

    def _format_markdown(self, report: dict[str, Any]) -> str:
        """Format report as markdown."""
        lines = [
            f"# Elysium-Bench Results",
            f"",
            f"**Version:** {report['version']}",
            f"**Date:** {report['timestamp']}",
            f"**Overall Score:** {report['overall_score']}/100",
            f"**Improvement Detected:** {'✅ Yes' if report['improvement_detected'] else '❌ No'}",
            f"",
            f"## Category Results",
            f"",
            f"| Category | Task 1 First | Task 1 Re-run | Δ Score | Learning? | Transfer Eff. | Stability |",
            f"|----------|-------------|--------------|---------|-----------|---------------|-----------|",
        ]

        for cat_id, data in report["categories"].items():
            t1 = data.get("task1_first", {})
            t1r = data.get("task1_rerun", {})
            first = f"{t1.get('total', 0):.1f}" if t1 else "N/A"
            rerun = f"{t1r.get('total', 0):.1f}" if t1r else "N/A"
            delta = f"{data['delta_absolute']:+.1f}"
            learning = "✅" if data.get("learning_detected") else "❌"
            transfer = f"{data.get('transfer_efficiency', 0):.2f}"
            stability = f"{data.get('stability', 0):.2f}"
            lines.append(f"| {cat_id} | {first} | {rerun} | {delta} | {learning} | {transfer} | {stability} |")

        lines.append("")
        lines.append(f"## Methodology")
        lines.append(f"- **Scoring dimensions:** Functional Correctness (40) + Code Quality (25) + Efficiency (15) + Robustness (10) + Integration (10)")
        lines.append(f"- **Improvement loop:** Task 1 → Tasks 2-10 → Task 1 re-run → Compare delta")
        lines.append(f"- **Threshold:** Pass ≥ 60/100, Learning ≥ 5% improvement")
        lines.append(f"- **Mode:** {self.config['environment']['mode']}")

        return "\n".join(lines)
