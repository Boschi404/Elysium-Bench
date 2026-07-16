# 🚀 Elysium-Bench

**Multi-Agent Self-Improvement Benchmark Suite**

> *"Does your agent actually get better with practice?"*

Elysium-Bench is the official benchmark for [Elysium Swarmloop](https://github.com/Boschi404/Elysium-Swarmloop) — the self-improving multi-agent orchestration engine. It measures the one thing other benchmarks don't: **improvement over time.**

---

## 🎯 Core Concept

Most benchmarks ask: *"How good is the agent right now?"*

Elysium-Bench asks: **"Does the agent get better after solving similar problems?"**

### The Improvement Loop

```
Task 1 (baseline) → Task 2 → Task 3 → ... → Task 10 → Task 1 (re-run)
                                                          ↓
                                                    Compare scores
                                                          ↓
                                                   📈 Learning Δ
```

If Elysium Swarmloop truly **learns from experience and improves the underlying LLM**, then the re-run of Task 1 should score higher than the first run. That's the `Δ Score` — the learning delta.

---

## 📊 Scoring System

Inspired by [SWE-bench](https://www.swebench.com/) methodology, each task is scored across 5 dimensions (0–100 total):

| Dimension | Weight | What it measures |
|-----------|--------|-----------------|
| **Functional Correctness** | 40 | All tests pass — fail→pass + pass→pass (no regressions) |
| **Code Quality** | 25 | Linting, type hints, docstrings, no stubs/TODOs |
| **Efficiency** | 15 | Algorithmic complexity, resource usage, runtime |
| **Robustness** | 10 | Edge cases, error handling, input validation |
| **Integration** | 10 | Imports work, interface contracts match, no orphans |

**Pass threshold:** ≥ 60/100  
**Learning detected:** ≥ 5% improvement on re-run

---

## 🗂️ Task Categories

| Category | Tasks | Difficulty | Description |
|----------|-------|------------|-------------|
| **API Development** | 10 | 3–6/10 | Implement REST APIs from specifications (FastAPI) |
| **Bug Fixing** | 10 | 3–7/10 | Fix bugs in existing codebases (race conditions, SQL injection, memory leaks) |
| **Algorithm Implementation** | 10 | 2–8/10 | Implement algorithms from descriptions (sort, graph, DP, data structures) |

**30 tasks total** — each with its own test suite, gold reference, and quality criteria.

---

## 🚀 Quick Start

### One Command

```bash
# Linux/macOS
./run.sh

# Windows
run.bat
```

### Options

```bash
./run.sh --mode docker          # Docker isolation (cleanest)
./run.sh --category api_development  # Single category
./run.sh --quick                # Fast test: 1 category, reduced tasks
./run.sh --list                 # List all tasks without running
./run.sh --no-cleanup           # Keep temp files for debugging
```

### Python CLI

```bash
pip install -e .
elysium-bench run               # Full benchmark
elysium-bench run -C bug_fixing # Single category
elysium-bench list-tasks        # Discover all tasks
elysium-bench report results/xxx.json  # View saved report
```

---

## 📈 Output

After running, results are saved to `./results/`:

```
results/
├── results_20260716_120000.json    # Raw data (all scores, metrics)
├── results_20260716_120000.md      # Markdown report
└── results_20260716_120000.html    # Interactive dashboard
```

### Example Output

```
╔══════════════════════════════════════════════════════════╗
║           🚀  Elysium-Bench v0.1.0                       ║
╚══════════════════════════════════════════════════════════╝

📋 Task Registry: 30 tasks in 3 categories
  ├─ API Development (api_development): 10 tasks
  ├─ Bug Fixing (bug_fixing): 10 tasks
  └─ Algorithm Implementation (algorithm_implementation): 10 tasks

============================================================
Category: API Development (api_development)
============================================================

📌 PHASE A: Baseline — T01_api_development: Create User CRUD API
   Score: 62.5/100 ✅

📌 PHASE B: Sequence — 9 tasks
   T02: 65.0/100 ✅
   T03: 68.0/100 ✅
   ...
   T10: 78.5/100 ✅

📌 PHASE C: Re-Run — T01_api_development: Create User CRUD API
   Score: 74.0/100 | Δ: +11.5 | 📈 IMPROVED

📈 Improvement Metrics — api_development
   Task 1 first run:  62.5/100
   Task 1 re-run:     74.0/100
   Δ Score:           📈 +11.5 (+18.4%)
   Transfer Efficiency: 1.05
   Stability:           0.92
   Convergence:         5 tasks
   Learning Detected:   ✅ YES
```

---

## 🧪 Deterministic Design

- **Fixed task specifications** — every run uses the same descriptions, tests, and gold patches
- **Clean environment** — each task runs in an isolated venv or Docker container
- **Auto-cleanup** — temp files and venvs are removed after each run (disable with `--no-cleanup`)
- **Reproducible scoring** — same solution always gets the same score
- **No external dependencies** — tasks use only file-based storage or in-memory data

---

## 🔗 Integration with Hermes Agent

The benchmark integrates with [Hermes Agent](https://hermes-agent.nousresearch.com/) to run tasks through Elysium Swarmloop:

```yaml
# config.yaml
hermes:
  skill: "elysium-swarmloop"   # Skill loaded for each task
  subagents_max: 50            # Max parallel subagents
  quality_threshold: 7         # Quality gate threshold
  retries_max: 3               # Max retries per subagent task
```

When `hermes` CLI is available, tasks run through the full multi-agent orchestration. If not available, the benchmark falls back to direct execution with pytest validation.

---

## 🏗️ Architecture

```
elysium_bench/
├── runner.py              # Main orchestrator — improvement loop
├── scoring.py             # Multi-dimensional scoring engine
├── metrics.py             # Improvement Δ calculator
├── harness.py             # Docker/venv isolation
├── hermes_interface.py    # Hermes Agent integration
├── task_registry.py       # Task discovery & loading
├── reporter.py            # HTML/Markdown/JSON reports
└── cli.py                 # CLI entry point

tasks/
├── api_development/       # 10 tasks: CRUD, auth, file upload, rate limiting...
├── bug_fixing/            # 10 tasks: SQL injection, race conditions, memory leaks...
└── algorithm_implementation/  # 10 tasks: sort, graph, DP, red-black tree...
```

---

## 📐 Methodology (SWE-bench Inspired)

Like SWE-bench, Elysium-Bench evaluates on **real software engineering tasks**, not toy problems:

- **Fail→Pass tests**: Tests that verify the task was completed correctly
- **Pass→Pass tests**: Tests that verify existing functionality wasn't broken (regression)
- **Binary per-test, continuous per-dimension**: SWE-bench is binary (resolved/unresolved). Elysium-Bench adds granularity with the 5-dimension scoring.
- **Gold patches**: Each task has a reference implementation that serves as ground truth.

**Key difference from SWE-bench:** SWE-bench measures one-shot capability. Elysium-Bench measures **learning rate** — does the agent improve after seeing similar problems?

---

## 🔬 What This Benchmark Tests

| Elysium Claim | How It's Tested |
|---------------|----------------|
| **Self-improvement** | Task 1 re-run score vs first-run score (Δ) |
| **Multi-agent orchestration** | 30 parallel task executions with subagent dispatch |
| **Quality gate** | Score dimensions measure completeness, no stubs allowed |
| **Pattern learning** | Transfer efficiency: does later-task performance improve? |
| **Stability** | Variance across similar tasks within a category |

---

## 📋 Contributing

Add new tasks:

```bash
elysium-bench init   # Creates a task template

# Edit tasks/<category>/TXX_your_task/task.yaml
# Add starting code to repo/
# Add test suite to tests/
# Add gold reference to gold/
```

---

## 📄 License

MIT — same as Elysium Swarmloop.

---

**Built by Boschi404 + ffazecaldy**  
*Measuring what matters: not just how good your agent is, but how much better it becomes.*
