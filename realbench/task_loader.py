"""Task loader for realbench tasks."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

REALBENCH_DIR = Path(__file__).resolve().parent
TASKS_DIR = REALBENCH_DIR / "tasks"


@dataclass
class RealTask:
    id: str
    category: str
    name: str
    description: str
    task_type: str
    difficulty: int
    timeout_seconds: int
    expected_files: list[str] = field(default_factory=list)
    task_dir: Path | None = None
    tests_dir: Path | None = None
    repo_dir: Path | None = None
    gold_dir: Path | None = None

    @classmethod
    def from_yaml(cls, path: Path) -> "RealTask":
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        task_dir = path.parent
        return cls(
            id=data["id"],
            category=data["category"],
            name=data["name"],
            description=data["description"],
            task_type=data.get("task_type", "code"),
            difficulty=int(data.get("difficulty", 5)),
            timeout_seconds=int(data.get("timeout_seconds", 900)),
            expected_files=list(data.get("expected_files", [])),
            task_dir=task_dir,
            tests_dir=task_dir / "tests" if (task_dir / "tests").exists() else None,
            repo_dir=task_dir / "repo" if (task_dir / "repo").exists() else None,
            gold_dir=task_dir / "gold" if (task_dir / "gold").exists() else None,
        )


def discover_tasks() -> dict[str, RealTask]:
    tasks: dict[str, RealTask] = {}
    for yaml_path in sorted(TASKS_DIR.glob("*/task.yaml")):
        task = RealTask.from_yaml(yaml_path)
        tasks[task.id] = task
    return tasks


def get_task(task_id: str) -> RealTask:
    tasks = discover_tasks()
    if task_id not in tasks:
        raise KeyError(f"unknown task {task_id}; available: {sorted(tasks)}")
    return tasks[task_id]
