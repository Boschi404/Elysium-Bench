"""CLI entry point for Elysium-Bench."""

from __future__ import annotations

import sys
from pathlib import Path

import click
from rich.console import Console

console = Console()


@click.group()
@click.version_option(version="0.1.0", prog_name="elysium-bench")
def main():
    """Elysium-Bench — Multi-Agent Self-Improvement Benchmark Suite.

    Measures Elysium Swarmloop's ability to improve over time
    by running similar tasks sequentially and comparing results.
    """
    pass


@main.command()
@click.option(
    "--config",
    "-c",
    default="config.yaml",
    help="Path to config.yaml",
    type=click.Path(exists=True),
)
@click.option(
    "--category",
    "-C",
    default=None,
    help="Run only this category (e.g., api_development)",
)
@click.option(
    "--mode",
    "-m",
    default=None,
    help="Execution mode: venv or docker",
    type=click.Choice(["venv", "docker"]),
)
@click.option(
    "--no-cleanup",
    is_flag=True,
    help="Keep temporary files after run (for debugging)",
)
def run(config: str, category: str | None, mode: str | None, no_cleanup: bool):
    """Run the full benchmark suite."""
    from .runner import BenchmarkRunner

    config_path = Path(config).resolve()
    if not config_path.exists():
        console.print(f"[bold red]❌ Config not found: {config_path}[/bold red]")
        sys.exit(1)

    runner = BenchmarkRunner(config_path)

    # Override config from CLI
    if mode:
        runner.config["environment"]["mode"] = mode
    if no_cleanup:
        runner.config["environment"]["cleanup"] = False

    # Optional: filter to single category
    if category:
        runner.config["categories"] = [
            c for c in runner.config["categories"] if c["id"] == category
        ]
        if not runner.config["categories"]:
            console.print(f"[bold red]❌ Category not found: {category}[/bold red]")
            sys.exit(1)

    try:
        report = runner.run()
        if not report:
            sys.exit(1)

        overall = report.get("overall_score", 0)
        improved = report.get("improvement_detected", False)

        console.print(f"\n[bold green]✅ Benchmark complete![/bold green]")
        console.print(f"   Overall Score: {overall:.1f}/100")
        console.print(f"   Improvement Detected: {'✅ YES' if improved else '❌ NO'}")

        if overall >= 85:
            console.print("[bold green]   Rating: EXCELLENT ⭐⭐⭐[/bold green]")
        elif overall >= 60:
            console.print("[bold yellow]   Rating: PASS ✓[/bold yellow]")
        else:
            console.print("[bold red]   Rating: NEEDS IMPROVEMENT[/bold red]")

    except KeyboardInterrupt:
        console.print("\n[bold yellow]⚠️  Benchmark interrupted by user[/bold yellow]")
        runner.harness.cleanup_all()
        sys.exit(130)
    except Exception as e:
        console.print(f"\n[bold red]❌ Error: {e}[/bold red]")
        if hasattr(runner, "harness"):
            runner.harness.cleanup_all()
        sys.exit(1)


@main.command()
@click.option(
    "--config",
    "-c",
    default="config.yaml",
    help="Path to config.yaml",
    type=click.Path(exists=True),
)
def list_tasks(config: str):
    """List all discovered tasks without running them."""
    from .task_registry import TaskRegistry

    import yaml

    config_path = Path(config).resolve()
    cfg = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    registry = TaskRegistry(config_path.parent / "tasks", cfg)
    registry.discover()

    console.print(registry.summary())
    console.print()

    # Detailed task listing
    for cat in registry.categories:
        console.print(f"\n[bold cyan]{cat.name}[/bold cyan]")
        for task in cat.tasks:
            console.print(f"  ├─ [bold]{task.id}[/bold]: {task.name}")
            console.print(f"  │  Difficulty: {task.difficulty}/10 | Tags: {', '.join(task.tags or ['none'])}")
            console.print(f"  │  Description: {task.description[:100]}...")


@main.command()
@click.argument("results_file", type=click.Path(exists=True))
def report(results_file: str):
    """Generate a report from a previous results JSON file."""
    import json

    results = json.loads(Path(results_file).read_text(encoding="utf-8"))
    console.print(f"[bold]📊 Report from: {results_file}[/bold]\n")
    console.print(f"Overall Score: {results['overall_score']}/100")
    console.print(f"Improvement: {'✅ Yes' if results.get('improvement_detected') else '❌ No'}")

    for cat_id, data in results.get("categories", {}).items():
        console.print(f"\n[bold cyan]{cat_id}[/bold cyan]")
        console.print(f"  Task 1 First: {data.get('task1_first', {}).get('total', 'N/A')}")
        console.print(f"  Task 1 Re-run: {data.get('task1_rerun', {}).get('total', 'N/A')}")
        console.print(f"  Δ Score: {data.get('delta_absolute', 0):+.1f}")
        console.print(f"  Learning Rate: {data.get('learning_rate', 0):.1f}%")


@main.command()
def init():
    """Initialize a new task template."""
    template_dir = Path(__file__).parent.parent / "templates" / "task_template"
    if template_dir.exists():
        console.print(f"[green]✅ Task template already exists at {template_dir}[/green]")
        return

    template_dir.mkdir(parents=True, exist_ok=True)

    # Create task.yaml template
    task_yaml = template_dir / "task.yaml"
    task_yaml.write_text(
        """# Task Definition Template
id: "TXX_category_name"
category: "api_development"  # api_development | bug_fixing | algorithm_implementation
name: "Task Name Here"
description: >
  Detailed description of what the task requires.
  What to implement, constraints, expected behavior.
difficulty: 5  # 1-10
tags:
  - python
  - api
timeout_seconds: 600
expected_files:
  - "solution.py"
forbidden_patterns:
  - "TODO"
""",
        encoding="utf-8",
    )

    (template_dir / "repo").mkdir(exist_ok=True)
    (template_dir / "tests").mkdir(exist_ok=True)
    (template_dir / "gold").mkdir(exist_ok=True)

    console.print(f"[green]✅ Task template created at {template_dir}[/green]")
    console.print("   Edit task.yaml, add starting code to repo/, tests to tests/, and gold patch to gold/")


if __name__ == "__main__":
    main()
