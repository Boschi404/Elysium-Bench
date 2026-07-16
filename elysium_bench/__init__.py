"""Elysium-Bench: Multi-Agent Self-Improvement Benchmark Suite.

Measures Elysium Swarmloop's core claims:
1. Self-improvement over time (learning delta on repeated tasks)
2. Multi-agent orchestration effectiveness
3. Quality gate reliability
4. Pattern learning transfer

Architecture:
    - 3 task categories × 10 tasks each (30 total)
    - Run task 1 → tasks 2-10 → re-run task 1 → compute improvement delta
    - SWE-bench-inspired scoring: functional + quality + efficiency + robustness
    - Clean environment isolation (Docker or venv)
    - Hermes Agent integration for autonomous execution
"""

__version__ = "0.1.0"
__author__ = "Boschi404, ffazecaldy"
