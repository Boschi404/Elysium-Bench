"""Main benchmark runner — 10-loop multi-phase orchestration.

Flow:
  Phase 0 (BASELINE):   All tasks WITHOUT Elysium → bare execution baseline
  Phase 1 (LOOP 1):     Measurement tasks WITH Elysium (max config) → first score
  Phase 2-10 (LOOPS):   Practice tasks WITH Elysium → 9 practice loops
  Phase 11 (RE-TEST):   Same tasks as Loop 1 WITH Elysium → improvement delta
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import yaml
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table

from .harness import Harness
from .hermes_interface import TaskExecutor
from .llm_interface import LLMProvider, create_llm_provider
from .metrics import ImprovementMetrics
from .scoring import ScoreBreakdown, ScoringEngine
from .task_registry import Category, Task, TaskRegistry

console = Console()


class BenchmarkRunner:
    """Multi-phase benchmark: Baseline → 10 Loops → Re-Test."""

    def __init__(self, config_path: Path = Path("config.yaml")):
        self.config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        self.tasks_root = config_path.parent / "tasks"
        self.results_dir = config_path.parent / self.config["reporting"]["output_dir"]
        self.results_dir.mkdir(parents=True, exist_ok=True)

        self.registry = TaskRegistry(self.tasks_root, self.config)
        self.harness = Harness(
            mode=self.config["environment"]["mode"],
            cleanup=self.config["environment"]["cleanup"],
            workspace_base=Path.home() / "Desktop" / "Hermes" / ".elysium-bench",
        )

        # LLM provider: this is the actual AI that solves tasks
        llm_config = self.config.get("llm", {"enabled": False})
        self.llm_provider = create_llm_provider(llm_config)
        provider_name = llm_config.get("provider", "none") if self.llm_provider else "none"
        model_name = llm_config.get("model", "none") if self.llm_provider else "none"

        if self.llm_provider:
            console.print(f"   [bold cyan]LLM: {provider_name}/{model_name}[/bold cyan]")
        else:
            # Check if Hermes CLI is available
            import shutil
            if shutil.which("hermes"):
                console.print(f"   [bold cyan]Using Hermes CLI → deepseek-v4-flash + elysium-swarmloop[/bold cyan]")
            else:
                console.print(f"   [bold yellow]No LLM or Hermes CLI — baseline testing only[/bold yellow]")

        # State
        self.baseline_scores: dict[str, ScoreBreakdown] = {}   # task_id → score
        self.loop1_scores: dict[str, ScoreBreakdown] = {}       # task_id → score
        self.practice_scores: list[dict[str, ScoreBreakdown]] = []  # per-loop
        self.retest_scores: dict[str, ScoreBreakdown] = {}      # task_id → score
        self.start_time = time.time()

    # ═══════════════════════════════════════════════════════════════════════
    # PUBLIC API
    # ═══════════════════════════════════════════════════════════════════════

    def run(self) -> dict[str, Any]:
        """Execute the full multi-phase benchmark."""
        console.print()
        console.print(Panel.fit(
            "[bold cyan]🚀 Elysium-Bench v0.2.0[/bold cyan]\n"
            "[dim]Multi-Phase Self-Improvement Benchmark[/dim]\n"
            "[dim]Baseline → 10 Elysium Loops → Re-Test → Improvement Δ[/dim]",
            border_style="cyan",
        ))

        categories = self.registry.discover()
        if not categories:
            console.print("[bold red]❌ No tasks discovered![/bold red]")
            return {}
        console.print(self.registry.summary())
        console.print()

        # ── Phase 0: BASELINE (no Elysium) ─────────────────────────────────
        if self.config["phases"]["baseline"]["enabled"]:
            self._run_baseline(categories)

        # ── Phase 1-10: LOOPS with Elysium ────────────────────────────────
        loop_config = self.config["phases"]["loops"]
        total_loops = loop_config["count"]

        # Phase 1 = Loop 1 (measurement)
        self._run_loop(categories, loop_num=1, is_measurement=True, loop_config=loop_config)

        # Phase 2-10 = Practice loops
        for loop_num in range(2, total_loops + 1):
            self._run_loop(categories, loop_num=loop_num, is_measurement=False, loop_config=loop_config)

        # ── Phase 11: RE-TEST Loop 1 tasks ────────────────────────────────
        if self.config["phases"]["retest"]["enabled"]:
            self._run_retest(categories, loop_config)

        # ── Generate Final Report ──────────────────────────────────────────
        report = self._generate_final_report()
        self._save_results(report)
        return report

    # ═══════════════════════════════════════════════════════════════════════
    # PHASE 0: BASELINE (no Elysium)
    # ═══════════════════════════════════════════════════════════════════════

    def _run_baseline(self, categories: list[Category]) -> None:
        """Run ALL tasks WITHOUT Elysium — bare execution baseline."""
        console.print()
        console.rule("[bold yellow]📋 PHASE 0: BASELINE — All tasks WITHOUT Elysium[/bold yellow]")

        all_tasks = []
        for cat in categories:
            all_tasks.extend(cat.tasks)

        console.print(f"   Running {len(all_tasks)} tasks without agent...\n")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            pbar = progress.add_task("[yellow]Baseline...", total=len(all_tasks))

            for task in all_tasks:
                progress.update(pbar, description=f"  [dim]{task.id}: {task.name[:45]}...[/dim]")

                # Use baseline Hermes (disabled — no Elysium)
                result = self._run_single_task(task, use_llm=False, attempt="baseline")
                score = self._score_task(task, result)
                self.baseline_scores[task.id] = score

                icon = "✅" if score.passed else "❌"
                console.print(f"   {task.id}: [bold]{score.total:.1f}/100[/bold] {icon}")
                progress.advance(pbar)

        # Summary
        avg = sum(s.total for s in self.baseline_scores.values()) / len(self.baseline_scores) if self.baseline_scores else 0
        console.print(f"\n   [bold]Baseline Average: {avg:.1f}/100[/bold] (no Elysium)\n")

    # ═══════════════════════════════════════════════════════════════════════
    # PHASE 1-10: LOOPS (with Elysium)
    # ═══════════════════════════════════════════════════════════════════════

    def _run_loop(
        self,
        categories: list[Category],
        loop_num: int,
        is_measurement: bool,
        loop_config: dict,
    ) -> None:
        """Run a single loop: 1 task per category WITH Elysium."""
        if is_measurement:
            console.rule(f"[bold green]🔬 PHASE 1: LOOP 1 — Measurement Tasks WITH Elysium[/bold green]")
            label = "LOOP 1 (measurement)"
        else:
            console.rule(f"[bold blue]🔄 PHASE {loop_num}: LOOP {loop_num} — Practice Tasks WITH Elysium[/bold blue]")
            label = f"LOOP {loop_num} (practice)"

        # Determine which task index to use for this loop
        if is_measurement:
            # Use configured loop_1 task indices
            task_map = loop_config["loop_1_tasks"]
        else:
            # Use practice tasks: loop 2 → task index 2, loop 3 → task index 3, etc.
            task_idx = loop_num  # loop 2 uses task 2, loop 3 uses task 3...
            task_map = {cat_id: [task_idx] for cat_id in loop_config["loop_1_tasks"]}

        loop_tasks: list[Task] = []
        for cat in categories:
            indices = task_map.get(cat.id, [1])
            for idx in indices:
                if 1 <= idx <= len(cat.tasks):
                    loop_tasks.append(cat.tasks[idx - 1])  # 0-indexed

        console.print(f"   {label}: {len(loop_tasks)} tasks\n")

        scores: dict[str, ScoreBreakdown] = {}
        for task in loop_tasks:
            result = self._run_single_task(task, use_llm=True, attempt=f"loop{loop_num}")
            score = self._score_task(task, result)
            scores[task.id] = score
            icon = "✅" if score.passed else "❌"
            console.print(f"   {task.id}: [bold]{score.total:.1f}/100[/bold] {icon}")

        avg = sum(s.total for s in scores.values()) / len(scores) if scores else 0
        console.print(f"   [bold]Loop {loop_num} Avg: {avg:.1f}/100[/bold]\n")

        if is_measurement:
            self.loop1_scores = scores
        else:
            self.practice_scores.append(scores)

    # ═══════════════════════════════════════════════════════════════════════
    # PHASE 11: RE-TEST
    # ═══════════════════════════════════════════════════════════════════════

    def _run_retest(self, categories: list[Category], loop_config: dict) -> None:
        """Re-run Loop 1 tasks to measure improvement."""
        console.rule("[bold magenta]🔁 PHASE 11: RE-TEST — Re-running Loop 1 tasks[/bold magenta]")

        task_map = loop_config["loop_1_tasks"]
        retest_tasks: list[Task] = []
        for cat in categories:
            indices = task_map.get(cat.id, [1])
            for idx in indices:
                if 1 <= idx <= len(cat.tasks):
                    retest_tasks.append(cat.tasks[idx - 1])

        console.print(f"   Re-running {len(retest_tasks)} measurement tasks...\n")

        for task in retest_tasks:
            result = self._run_single_task(task, use_llm=True, attempt="retest")
            score = self._score_task(task, result)
            self.retest_scores[task.id] = score

            # Show delta vs Loop 1
            loop1_score = self.loop1_scores.get(task.id)
            if loop1_score:
                delta = score.total - loop1_score.total
                direction = "📈" if delta > 0 else "📉" if delta < 0 else "➡️"
                console.print(
                    f"   {task.id}: [bold]{score.total:.1f}/100[/bold] "
                    f"| Loop 1 was {loop1_score.total:.1f} | Δ: {direction} {delta:+.1f}"
                )
            else:
                console.print(f"   {task.id}: [bold]{score.total:.1f}/100[/bold]")

        avg = sum(s.total for s in self.retest_scores.values()) / len(self.retest_scores) if self.retest_scores else 0
        console.print(f"\n   [bold]Re-Test Avg: {avg:.1f}/100[/bold]\n")

    # ═══════════════════════════════════════════════════════════════════════
    # TASK EXECUTION
    # ═══════════════════════════════════════════════════════════════════════

    def _run_single_task(self, task: Task, use_llm: bool, attempt: str = "first") -> dict[str, Any]:
        """Execute a single task: via LLM (Elysium mode) or direct test run (baseline)."""
        start = time.time()

        # SWE-bench tasks need special preparation (clone repo at base commit)
        if task.category == "swe_bench":
            return self._run_swebench_task(task, use_llm, attempt)

        source_dir = task.repo_dir or task.task_dir
        workspace = self.harness.create_workspace(f"{task.id}_{attempt}", source_dir)

        if task.test_dir and task.test_dir.exists():
            import shutil
            dest_test = workspace / "workspace" / "tests"
            if not dest_test.exists():
                shutil.copytree(task.test_dir, dest_test, dirs_exist_ok=True)

        # Create TaskExecutor and execute
        executor = TaskExecutor(task_type=task.task_type if hasattr(task, 'task_type') else "code")
        result = executor.execute(
            task_id=task.id, task_name=task.name,
            task_description=task.description,
            workspace=workspace, timeout=task.timeout_seconds,
            attempt=attempt, force_baseline=not use_llm,
        )

        elapsed = time.time() - start
        result["elapsed_seconds"] = round(elapsed, 1)
        result["task_id"] = task.id
        result["attempt"] = attempt
        result["workspace"] = str(workspace)
        return result

    def _run_swebench_task(self, task: Task, use_llm: bool, attempt: str) -> dict[str, Any]:
        """Execute a SWE-bench task: clone repo, apply issue prompt, evaluate patch."""
        from .swebench_adapter import SweBenchAdapter
        start_time = time.time()

        executor = TaskExecutor(task_type="code")
        adapter = SweBenchAdapter(task.task_dir, executor)

        # Phase 1: Prepare workspace (clone repo at base commit)
        workspace = adapter.prepare()

        # Phase 2: Run the agent (Hermes CLI with/without Elysium skill)
        result = executor.execute(
            task_id=task.id, task_name=task.name,
            task_description=task.description,
            workspace=workspace, timeout=task.timeout_seconds,
        )

        # Phase 3: Generate patch from repo changes
        patch_file = adapter.generate_patch(workspace)
        result["patch_file"] = str(patch_file)
        patch_content = patch_file.read_text(encoding="utf-8") if patch_file.exists() else ""
        result["patch_length"] = len(patch_content)

        # Phase 4: Evaluate patch using SWE-bench methodology
        eval_result = adapter.evaluate_patch(workspace)
        result["swebench_eval"] = eval_result

        elapsed = time.time() - start_time
        result["elapsed_seconds"] = round(elapsed, 1)
        result["task_id"] = task.id
        result["attempt"] = attempt
        result["workspace"] = str(workspace)
        return result

    def _score_task(self, task: Task, task_result: dict[str, Any]) -> ScoreBreakdown:
        """Score a completed task."""
        workspace = Path(task_result.get("workspace", ".")) / "workspace"

        # Extract flat weights from nested config
        raw_scoring = self.config["scoring"]
        weights = {
            k: v["weight"] if isinstance(v, dict) else v
            for k, v in raw_scoring.items()
        }

        engine = ScoringEngine(
            task_dir=task.task_dir or Path("."),
            solution_dir=workspace,
            weights=weights,
        )
        return engine.evaluate()

    # ═══════════════════════════════════════════════════════════════════════
    # REPORTING
    # ═══════════════════════════════════════════════════════════════════════

    def _generate_final_report(self) -> dict[str, Any]:
        """Generate the comprehensive multi-phase report."""
        console.rule("[bold cyan]📊 FINAL REPORT[/bold cyan]")

        elapsed = time.time() - self.start_time

        # ── Build the main comparison table ────────────────────────────────
        table = Table(title="Elysium-Bench: Improvement Comparison")
        table.add_column("Task", style="cyan", width=35)
        table.add_column("Baseline\n(no Elysium)", justify="right", width=12)
        table.add_column("Loop 1\n(Elysium)", justify="right", width=12)
        table.add_column("Re-Test\n(after 10 loops)", justify="right", width=14)
        table.add_column("Δ vs Loop 1", justify="right", width=12)
        table.add_column("Δ vs Baseline", justify="right", width=14)
        table.add_column("Learning?", justify="center", width=10)

        improvements: list[float] = []
        for task_id in self.loop1_scores:
            baseline = self.baseline_scores.get(task_id)
            loop1 = self.loop1_scores[task_id]
            retest = self.retest_scores.get(task_id)

            bl_str = f"{baseline.total:.1f}" if baseline else "—"
            l1_str = f"{loop1.total:.1f}"
            rt_str = f"{retest.total:.1f}" if retest else "—"

            if retest and loop1:
                delta_loop1 = retest.total - loop1.total
                delta_sign = "+" if delta_loop1 > 0 else ""
                delta_str = f"{delta_sign}{delta_loop1:.1f}"
                improvements.append(delta_loop1)
            else:
                delta_str = "—"

            if retest and baseline:
                delta_bl = retest.total - baseline.total
                bl_sign = "+" if delta_bl > 0 else ""
                delta_bl_str = f"{bl_sign}{delta_bl:.1f}"
            else:
                delta_bl_str = "—"

            learning_threshold = self.config["thresholds"]["learning_min"]
            if retest and loop1:
                pct = ((retest.total - loop1.total) / loop1.total * 100) if loop1.total > 0 else 0
                learning = "✅" if pct >= learning_threshold else "❌"
            else:
                learning = "—"

            table.add_row(task_id, bl_str, l1_str, rt_str, delta_str, delta_bl_str, learning)

        console.print(table)

        # ── Summary stats ──────────────────────────────────────────────────
        baseline_avg = self._avg_score(self.baseline_scores)
        loop1_avg = self._avg_score(self.loop1_scores)
        retest_avg = self._avg_score(self.retest_scores)
        practice_avgs = [
            self._avg_score(scores) for scores in self.practice_scores if scores
        ]

        delta_l1_rt = retest_avg - loop1_avg if (retest_avg and loop1_avg) else 0
        delta_bl_rt = retest_avg - baseline_avg if (retest_avg and baseline_avg) else 0
        improved = delta_l1_rt >= self.config["thresholds"]["learning_min"]

        console.print()
        summary = Table(title="Score Progression Across Phases", show_header=False)
        summary.add_column("Metric", style="cyan")
        summary.add_column("Value", justify="right")

        summary.add_row("Baseline Avg (no Elysium)", f"{baseline_avg:.1f}/100")
        summary.add_row("Loop 1 Avg (Elysium, first run)", f"{loop1_avg:.1f}/100")
        if practice_avgs:
            summary.add_row("Practice Loops Avg", f"{sum(practice_avgs)/len(practice_avgs):.1f}/100")
        summary.add_row("Re-Test Avg (Elysium, after 10 loops)", f"{retest_avg:.1f}/100")
        summary.add_row("", "")
        summary.add_row("[bold]Δ Re-Test vs Loop 1[/bold]", f"[bold]{delta_l1_rt:+.1f}[/bold]")
        summary.add_row("[bold]Δ Re-Test vs Baseline[/bold]", f"[bold]{delta_bl_rt:+.1f}[/bold]")
        summary.add_row("[bold]Improvement Detected[/bold]", f"[bold]{'✅ YES' if improved else '❌ NO'}[/bold]")
        summary.add_row("Total Duration", f"{elapsed/60:.1f} min")

        console.print(summary)

        # ── Practice progression ───────────────────────────────────────────
        if practice_avgs:
            console.print()
            prog_table = Table(title="Practice Loop Progression (Loops 2-10)")
            prog_table.add_column("Loop", justify="center")
            prog_table.add_column("Avg Score", justify="right")
            prog_table.add_column("Δ from Loop 1", justify="right")
            prog_table.add_column("Trend", justify="center")

            for i, avg in enumerate(practice_avgs):
                loop_n = i + 2
                delta = avg - loop1_avg if loop1_avg else 0
                trend = "📈" if delta > 0 else "📉" if delta < 0 else "➡️"
                prog_table.add_row(f"Loop {loop_n}", f"{avg:.1f}", f"{delta:+.1f}", trend)

            console.print(prog_table)

        # ── Build report dict ──────────────────────────────────────────────
        report = {
            "benchmark": "Elysium-Bench",
            "version": self.config["benchmark"]["version"],
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "duration_seconds": round(elapsed, 1),
            "phases": {
                "baseline": {
                    "scores": {tid: s.to_dict() for tid, s in self.baseline_scores.items()},
                    "average": round(baseline_avg, 1),
                },
                "loop1": {
                    "scores": {tid: s.to_dict() for tid, s in self.loop1_scores.items()},
                    "average": round(loop1_avg, 1),
                },
                "practice": [
                    {
                        "loop": i + 2,
                        "scores": {tid: s.to_dict() for tid, s in scores.items()},
                        "average": round(self._avg_score(scores), 1),
                    }
                    for i, scores in enumerate(self.practice_scores)
                ],
                "retest": {
                    "scores": {tid: s.to_dict() for tid, s in self.retest_scores.items()},
                    "average": round(retest_avg, 1),
                },
            },
            "improvement": {
                "delta_retest_vs_loop1": round(delta_l1_rt, 1),
                "delta_retest_vs_baseline": round(delta_bl_rt, 1),
                "learning_detected": improved,
                "transfer_efficiency": (
                    round(sum(practice_avgs) / len(practice_avgs) / loop1_avg, 2)
                    if practice_avgs and loop1_avg > 0 else 0
                ),
            },
            "config": {
                "hermes_max_subagents": self.config["hermes"]["subagents_max"],
                "hermes_quality_threshold": self.config["hermes"]["quality_threshold"],
                "total_loops": self.config["phases"]["loops"]["count"],
                "total_tasks": self.registry.total_tasks,
            },
        }

        return report

    def _save_results(self, report: dict[str, Any]) -> None:
        """Save results to disk."""
        timestamp = time.strftime("%Y%m%d_%H%M%S")

        # JSON
        json_path = self.results_dir / f"results_{timestamp}.json"
        json_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
        console.print(f"\n📁 Results: {json_path}")

        # Markdown
        md_path = self.results_dir / f"results_{timestamp}.md"
        md_path.write_text(self._format_markdown(report), encoding="utf-8")
        console.print(f"📁 Report:  {md_path}")

        # HTML
        try:
            from .reporter import generate_html_report

            html_path = self.results_dir / f"results_{timestamp}.html"
            generate_html_report(report, html_path)
            console.print(f"📁 Dashboard: {html_path}")
        except Exception:
            pass

    def _format_markdown(self, report: dict[str, Any]) -> str:
        """Format report as markdown."""
        imp = report["improvement"]
        lines = [
            f"# Elysium-Bench Results",
            f"",
            f"**Version:** {report['version']} | **Date:** {report['timestamp']}",
            f"**Duration:** {report['duration_seconds']:.0f}s",
            f"",
            f"## Score Progression",
            f"",
            f"| Phase | Average Score |",
            f"|-------|--------------|",
            f"| Baseline (no Elysium) | {report['phases']['baseline']['average']}/100 |",
            f"| Loop 1 (Elysium) | {report['phases']['loop1']['average']}/100 |",
        ]
        for p in report["phases"]["practice"]:
            lines.append(f"| Loop {p['loop']} (practice) | {p['average']}/100 |")
        lines.append(f"| Re-Test (after 10 loops) | {report['phases']['retest']['average']}/100 |")
        lines.append(f"")
        lines.append(f"## Improvement")
        lines.append(f"")
        lines.append(f"| Metric | Value |")
        lines.append(f"|--------|-------|")
        lines.append(f"| Δ Re-Test vs Loop 1 | {imp['delta_retest_vs_loop1']:+.1f} |")
        lines.append(f"| Δ Re-Test vs Baseline | {imp['delta_retest_vs_baseline']:+.1f} |")
        lines.append(f"| Learning Detected | {'✅ YES' if imp['learning_detected'] else '❌ NO'} |")
        lines.append(f"| Transfer Efficiency | {imp['transfer_efficiency']:.2f} |")
        lines.append(f"")
        lines.append(f"## Config")
        lines.append(f"- Hermes subagents: {report['config']['hermes_max_subagents']}")
        lines.append(f"- Quality threshold: {report['config']['hermes_quality_threshold']}/10")
        lines.append(f"- Total loops: {report['config']['total_loops']}")
        lines.append(f"- Total tasks available: {report['config']['total_tasks']}")
        return "\n".join(lines)

    @staticmethod
    def _avg_score(scores: dict[str, ScoreBreakdown]) -> float:
        if not scores:
            return 0.0
        return sum(s.total for s in scores.values()) / len(scores)
