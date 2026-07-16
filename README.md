<p align="center">
  <img src="https://raw.githubusercontent.com/Boschi404/Elysium-Bench/main/assets/logo-banner.svg" alt="Elysium-Bench" width="100%">
</p>

<p align="center">
  <strong>The Multi-Domain Self-Improvement Benchmark</strong><br>
  <em>Does your agent actually get better with practice?</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-0.3.0-34d399?style=flat-square&labelColor=0f172a">
  <img src="https://img.shields.io/badge/license-MIT-22d3ee?style=flat-square&labelColor=0f172a">
  <img src="https://img.shields.io/badge/tasks-100-a78bfa?style=flat-square&labelColor=0f172a">
  <img src="https://img.shields.io/badge/categories-10-fbbf24?style=flat-square&labelColor=0f172a">
  <img src="https://img.shields.io/badge/loops-10-f472b6?style=flat-square&labelColor=0f172a">
</p>

---

## What is Elysium-Bench?

The official benchmark for [Elysium Swarmloop](https://github.com/Boschi404/Elysium-Swarmloop) — the self-improving multi-agent orchestration engine. It measures the one thing other benchmarks don't: **improvement over time.**

Most benchmarks ask *"How good is the agent right now?"* Elysium-Bench asks **"Does the agent get better after solving similar problems?"**

- **100 tasks across 10 domains** — code, data, math, logic, security, review, docs, devops
- **Multi-phase execution** — baseline (no Elysium) → 10 loops (with Elysium) → re-test → compare Δ
- **5 scoring engines** — code (pytest), text (rubric), math (exact match), plan (constraints), data (validation)
- **Zero-trace execution** — isolated venv/Docker workspaces, auto-cleanup, reproducible
- **One-command launcher** — `./run.sh` on Linux/macOS, `run.bat` on Windows

## Repository Structure

```
├── README.md
├── config.yaml                    # Benchmark configuration (categories, phases, hermes, scoring)
├── run.sh / run.bat               # One-command launcher
├── pyproject.toml                 # Python package metadata
├── requirements.txt
├── docker/
│   └── Dockerfile                 # Clean Docker environment
├── elysium_bench/
│   ├── cli.py                     # Click CLI (run, list-tasks, report, init)
│   ├── runner.py                  # Multi-phase orchestrator
│   ├── scoring.py                 # ScoringAdapter + 5 scoring engines
│   ├── metrics.py                 # Improvement metrics (Δ, transfer, stability, convergence)
│   ├── harness.py                 # Docker/venv clean environment isolation
│   ├── hermes_interface.py        # Hermes Agent integration (Elysium + baseline modes)
│   ├── task_registry.py           # YAML-based task discovery
│   └── reporter.py                # HTML/Markdown/JSON report generator
└── tasks/
    ├── api_development/           # 10 tasks — REST APIs (FastAPI)
    ├── bug_fixing/                # 10 tasks — Fix bugs in existing code
    ├── algorithm_implementation/  # 10 tasks — Sort, graph, DP, data structures
    ├── data_analysis/             # 10 tasks — SQL, pandas, statistical analysis
    ├── mathematical_reasoning/    # 10 tasks — Algebra, calculus, probability, proofs
    ├── logical_deduction/         # 10 tasks — Puzzles, syllogisms, truth tables
    ├── security_analysis/         # 10 tasks — SQLi, XSS, OWASP, threat modeling
    ├── code_review/               # 10 tasks — Bug detection, anti-patterns, PR review
    ├── documentation_generation/  # 10 tasks — READMEs, API docs, ADRs, user guides
    └── configuration_management/  # 10 tasks — Docker, K8s, Terraform, CI/CD
```

## The Multi-Phase Flow

```
PHASE 0 (BASELINE)
  └─ All 100 tasks WITHOUT Elysium → bare execution baseline
       │
       ▼
PHASE 1 (LOOP 1 — MEASUREMENT)
  └─ 10 tasks WITH Elysium (T01 from each category) → first Elysium score
       │
       ▼
PHASES 2–10 (PRACTICE LOOPS)
  └─ 10 tasks/loop WITH Elysium (T02→T10, different each loop) → 90 practice tasks
       │
       ▼
PHASE 11 (RE-TEST)
  └─ Same 10 tasks as Loop 1 WITH Elysium → compare Δ
       │
       ▼
  📈 Improvement Detected?
```

**This proves self-improvement:** after 10 loops of practice on similar tasks across 10 different domains, the agent should perform BETTER on the exact same tasks it saw in Loop 1. The delta between Loop 1 and Re-Test is the learning signal.

## Quick Start

```bash
# Clone and run
git clone https://github.com/Boschi404/Elysium-Bench.git
cd Elysium-Bench
pip install -e .

# Full benchmark (all 100 tasks, all phases)
elysium-bench run

# Single category
elysium-bench run --category data_analysis

# List all tasks without running
elysium-bench list-tasks

# View previous results
elysium-bench report results/results_20260716_120000.json
```

## Scoring System

Every task is scored 0–100 across 5 generic dimensions. The **ScoringAdapter** routes to the right engine based on `task_type`:

| Dimension | Weight | Code | Text | Math | Plan | Data |
|-----------|--------|------|------|------|------|------|
| **Correctness** | 40 | pytest pass rate | rubric keywords + reference similarity | exact/float answer match | constraint satisfaction | validation script |
| **Completeness** | 25 | lint + no stubs | all required sections present | reasoning steps found | all sections covered | required elements check |
| **Efficiency** | 15 | complexity analysis | conciseness check | optimal method used | optimization language | query/script efficiency |
| **Robustness** | 10 | error handling | edge case mentions | edge cases addressed | risk/contingency coverage | edge data handling |
| **Clarity** | 10 | import/syntax check | structure + formatting | step labeling | plan structure | formatting + readability |

**Pass threshold:** ≥ 60/100 · **Excellent:** ≥ 85/100 · **Learning detected:** ≥ 5% improvement

## Task Categories

| # | Category | Type | Difficulty | Examples |
|---|----------|------|------------|----------|
| 1 | API Development | `code` | 3–6 | CRUD, Auth JWT, Rate Limiter, Event Booking |
| 2 | Bug Fixing | `code` | 3–7 | SQL Injection, Race Condition, Memory Leak |
| 3 | Algorithm Implementation | `code` | 2–8 | Binary Search, Dijkstra, Red-Black Tree |
| 4 | Data Analysis | `data` | 3–8 | SQL queries, Pandas pipelines, ETL |
| 5 | Mathematical Reasoning | `math` | 3–8 | Linear algebra, Calculus, ε-δ proofs |
| 6 | Logical Deduction | `text` | 3–7 | Knights & Knaves, Syllogisms, Resolution |
| 7 | Security Analysis | `text` | 3–7 | SQLi, XSS, OWASP, Threat modeling |
| 8 | Code Review | `text` | 4–7 | Anti-patterns, PR review, API design |
| 9 | Documentation Generation | `text` | 3–6 | READMEs, API docs, ADRs, User guides |
| 10 | Configuration & DevOps | `plan` | 4–8 | Docker, K8s, Terraform, CI/CD |

## Output & Results

Results are saved to `./results/` after every run:

```
results/
├── results_20260716_120000.json    # Raw data — all scores, metrics, config
├── results_20260716_120000.md      # Markdown report
└── results_20260716_120000.html    # Interactive dark-themed dashboard
```

### Console Output

```
┌───────────────────────────────────────────────────────┐
│ 🚀 Elysium-Bench v0.3.0                               │
│ Multi-Phase Self-Improvement Benchmark                │
│ Baseline → 10 Elysium Loops → Re-Test → Improvement Δ │
└───────────────────────────────────────────────────────┘

────────────── 📋 PHASE 0: BASELINE — All tasks WITHOUT Elysium ───────────────
   Running 100 tasks without agent...

   Baseline Avg: 42.3/100 (no Elysium)

───── 🔬 PHASE 1: LOOP 1 — Measurement Tasks WITH Elysium ─────────────────
   T01_api_development: 72.5/100 ✅
   T01_data_analysis: 68.0/100 ✅
   T01_mathematical_reasoning: 74.0/100 ✅
   ...
   Loop 1 Avg: 71.2/100

───── 🔄 PHASE 2-10: Practice Loops ────────────────────────────────────────
   Loop 2 Avg: 73.1/100   Loop 6 Avg: 78.5/100
   Loop 3 Avg: 74.8/100   Loop 7 Avg: 79.2/100
   Loop 4 Avg: 76.2/100   Loop 8 Avg: 80.0/100
   Loop 5 Avg: 77.0/100   Loop 9 Avg: 80.5/100
                          Loop 10 Avg: 81.3/100

───── 🔁 PHASE 11: RE-TEST — Re-running Loop 1 tasks ──────────────────────
   T01_api_development: 81.0/100 | Δ: +8.5 📈
   T01_data_analysis: 79.5/100 | Δ: +11.5 📈

────────────────────────── 📊 FINAL REPORT ──────────────────────────────────
| Phase                    | Average Score |
|--------------------------|--------------|
| Baseline (no Elysium)   | 42.3/100     |
| Loop 1 (Elysium)        | 71.2/100     |
| Practice Loops Avg      | 77.6/100     |
| Re-Test (after 10 loops)| 82.5/100     |

| Metric                      | Value     |
|-----------------------------|-----------|
| Δ Re-Test vs Loop 1         | +11.3     |
| Δ Re-Test vs Baseline       | +40.2     |
| Improvement Detected        | ✅ YES    |
```

## Hermes Agent Integration

The benchmark integrates with [Hermes Agent](https://hermes-agent.nousresearch.com/) to run tasks through Elysium Swarmloop. Two modes are configured:

### Elysium Mode (Loops 1–11)

```yaml
hermes:
  skill: "elysium-swarmloop"    # Full multi-agent orchestration
  subagents_max: 100            # Maximum parallel subagents
  quality_threshold: 8          # Strict quality gate (8/10)
  retries_max: 5                # Aggressive retry policy
  streaming: true               # Streaming gather with immediate retry
  self_learning: true           # Pattern capture + calibration
  orchestrator_depth: 2         # Hierarchical orchestration
```

### Baseline Mode (Phase 0)

```yaml
hermes:
  disabled:
    skill: null                 # No skill loaded
    subagents_max: 0            # No subagents
    quality_threshold: 0        # No quality gate
    retries_max: 0              # No retries
```

When Hermes CLI is not available, the benchmark falls back to direct pytest execution for code tasks and rubric-based evaluation for non-code tasks.

## What This Benchmark Tests

| Elysium Claim | How It's Tested |
|---------------|-----------------|
| **Self-improvement over time** | Re-Test score vs Loop 1 score (Δ across 10 domains) |
| **Multi-agent orchestration** | 100 subagents per task, parallel dispatch |
| **Streaming quality gate** | Immediate retry on below-threshold results |
| **Pattern learning transfer** | Practice loop progression trend (Loops 2→10) |
| **Cross-domain generalization** | 10 different task types (code, text, math, plan, data) |
| **Stability under load** | 100 tasks × 10 loops = 1000 executions |

## Configurability

Everything is configurable via `config.yaml`:

- **Categories**: enable/disable, adjust weights, change task counts
- **Phases**: toggle baseline, change loop count, select which tasks are the measurement set
- **Scoring**: adjust dimension weights, change pass/excellent thresholds
- **Hermes**: tune subagents, threshold, retries for Elysium mode
- **Environment**: venv vs Docker, cleanup behavior, timeouts
- **Reporting**: output formats, verbosity

## Creating New Tasks

```bash
# Generate a task template
elysium-bench init

# Edit the task definition
vim tasks/<category>/TXX_your_task/task.yaml

# Add evaluation files
vim tasks/<category>/TXX_your_task/tests/rubric.yaml     # For text tasks
vim tasks/<category>/TXX_your_task/tests/expected.json   # For math tasks
vim tasks/<category>/TXX_your_task/tests/validate.py     # For data tasks
vim tasks/<category>/TXX_your_task/tests/test_solution.py # For code tasks
```

Task YAML format:

```yaml
id: "T01_your_category"
category: "your_category"
name: "Task Name"
task_type: "code"        # code | text | math | plan | data
description: >
  Detailed task description.
difficulty: 5
tags: [python, api]
timeout_seconds: 600
```

## License

MIT

## Authors

- **Boschi404** — Creator and Lead Architect
- **ffazecaldy** — Collaborator and Co-Architect
- **Hermes Agent** — Testing Agent

---

<p align="center">
  <sub>Built to measure what matters: not just how good your agent is, but how much better it becomes.</sub>
</p>
