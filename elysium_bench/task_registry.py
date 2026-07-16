"""Task registry — loads and manages benchmark task definitions."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class Task:
    """A single benchmark task."""

    id: str
    category: str
    name: str
    description: str
    difficulty: int  # 1-10
    tags: list[str] = field(default_factory=list)

    # Paths
    task_dir: Path | None = None
    repo_dir: Path | None = None  # Starting repo state
    test_dir: Path | None = None  # Test suite
    gold_patch: Path | None = None  # Gold patch for comparison

    # Constraints
    timeout_seconds: int = 600
    expected_files: list[str] = field(default_factory=list)
    forbidden_patterns: list[str] = field(default_factory=list)

    @classmethod
    def from_yaml(cls, path: Path) -> "Task":
        """Load task from a task.yaml file."""
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        task_dir = path.parent
        return cls(
            id=data["id"],
            category=data["category"],
            name=data["name"],
            description=data["description"],
            difficulty=data.get("difficulty", 5),
            tags=data.get("tags", []),
            task_dir=task_dir,
            repo_dir=task_dir / "repo" if (task_dir / "repo").exists() else None,
            test_dir=task_dir / "tests" if (task_dir / "tests").exists() else None,
            gold_patch=task_dir / "gold" / "patch.diff" if (task_dir / "gold").exists() else None,
            timeout_seconds=data.get("timeout_seconds", 600),
            expected_files=data.get("expected_files", []),
            forbidden_patterns=data.get("forbidden_patterns", []),
        )


@dataclass
class Category:
    """A task category (e.g., API Development, Bug Fixing)."""

    id: str
    name: str
    description: str
    weight: float
    tasks: list[Task] = field(default_factory=list)

    @property
    def task_count(self) -> int:
        return len(self.tasks)


class TaskRegistry:
    """Loads and manages all benchmark tasks."""

    def __init__(self, tasks_root: Path, config: dict[str, Any]):
        self.tasks_root = Path(tasks_root)
        self.config = config
        self.categories: list[Category] = []
        self._tasks_by_id: dict[str, Task] = {}

    def discover(self) -> list[Category]:
        """Discover all task categories and their tasks."""
        self.categories = []

        for cat_config in self.config.get("categories", []):
            cat_id = cat_config["id"]
            cat_dir = self.tasks_root / cat_id

            if not cat_dir.exists():
                print(f"  ⚠️  Category directory not found: {cat_dir}")
                continue

            category = Category(
                id=cat_id,
                name=cat_config["name"],
                description=cat_config["description"],
                weight=cat_config.get("weight", 1.0),
            )

            # Discover tasks in this category (T01, T02, ... T10)
            for task_dir in sorted(cat_dir.iterdir()):
                if not task_dir.is_dir() or not task_dir.name.startswith("T"):
                    continue
                task_yaml = task_dir / "task.yaml"
                if task_yaml.exists():
                    task = Task.from_yaml(task_yaml)
                    category.tasks.append(task)
                    self._tasks_by_id[task.id] = task

            self.categories.append(category)

        return self.categories

    def get_task(self, task_id: str) -> Task | None:
        """Get a task by its ID."""
        return self._tasks_by_id.get(task_id)

    def get_category(self, category_id: str) -> Category | None:
        """Get a category by its ID."""
        for cat in self.categories:
            if cat.id == category_id:
                return cat
        return None

    @property
    def total_tasks(self) -> int:
        return sum(len(cat.tasks) for cat in self.categories)

    def summary(self) -> str:
        """Human-readable summary of discovered tasks."""
        lines = [f"📋 Task Registry: {self.total_tasks} tasks in {len(self.categories)} categories"]
        for cat in self.categories:
            lines.append(f"  ├─ {cat.name} ({cat.id}): {cat.task_count} tasks")
            for task in cat.tasks[:3]:
                lines.append(f"  │  ├─ {task.id}: {task.name} (difficulty {task.difficulty}/10)")
            if cat.task_count > 3:
                lines.append(f"  │  └─ ... and {cat.task_count - 3} more")
        return "\n".join(lines)
