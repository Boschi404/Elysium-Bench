"""Elysium-Bench UI Server — FastAPI + Chart.js dashboard.

Start with: elysium-bench ui
Opens: http://localhost:8080

Features:
- Dashboard: historical run comparison (line chart) + system status
- Run: start new benchmarks with config selection + parallel category cards
- Progress: real-time SSE stream with per-category updates + named phases
- Results: detailed view per run
- Compare: side-by-side run comparison
"""

from __future__ import annotations

import asyncio
import json
import os
import platform
import queue
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from fastapi import FastAPI, Request, Query
    from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
    import uvicorn
except ImportError:
    raise ImportError("Install UI deps: pip install elysium-bench[ui]  or  pip install fastapi uvicorn")

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

from .runner import BenchmarkRunner
from .ui_templates import (
    PAGE_SHELL,
    DASHBOARD_PAGE,
    RUN_PAGE,
    RESULTS_PAGE,
    COMPARE_PAGE,
    STYLES,
)


# ── Globals ──────────────────────────────────────────────────────────────────
app = FastAPI(title="Elysium-Bench UI", version="0.3.0")

_progress_queues: dict[str, asyncio.Queue] = {}
_runs_dir: Path = Path("results")
_categories_list = [
    "api_development", "bug_fixing", "algorithm_implementation",
    "data_analysis", "mathematical_reasoning", "logical_deduction",
    "security_analysis", "code_review", "documentation_generation",
    "configuration_management",
]

# Track active run for status
_active_run_id: str | None = None
_bench_version: str = "0.4.1"


# ── Helpers ──────────────────────────────────────────────────────────────────

def _load_results_file(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None

def _list_runs() -> list[dict]:
    """Return all completed runs sorted newest first."""
    runs = []
    if not _runs_dir.exists():
        return runs
    for f in sorted(_runs_dir.glob("results_*.json"), reverse=True):
        data = _load_results_file(f)
        if data:
            runs.append({
                "id": f.stem.replace("results_", ""),
                "path": str(f),
                "timestamp": data.get("timestamp", ""),
                "overall_score": data.get("phases", {}).get("retest", {}).get("average", 0),
                "baseline_score": data.get("phases", {}).get("baseline", {}).get("average", 0),
                "loop1_score": data.get("phases", {}).get("loop1", {}).get("average", 0),
                "improvement": data.get("improvement", {}).get("delta_retest_vs_loop1", 0),
                "learning_detected": data.get("improvement", {}).get("learning_detected", False),
                "duration_seconds": data.get("duration_seconds", 0),
            })
    return runs


def _get_hermes_status() -> dict:
    """Detect Hermes Agent status by checking CLI and config."""
    status = {"available": False, "provider": "unknown", "model": "unknown"}

    # Try to detect hermes CLI
    hermes_bin = None
    for candidate in ["hermes", "hermes.exe"]:
        try:
            result = subprocess.run(
                [candidate, "--version"], capture_output=True, text=True, timeout=5,
                shell=(platform.system() == "Windows"),
            )
            if result.returncode == 0:
                hermes_bin = candidate
                status["available"] = True
                break
        except Exception:
            pass

    # Try to read config for provider/model
    if status["available"]:
        try:
            result = subprocess.run(
                [hermes_bin, "config", "get", "model"], capture_output=True, text=True, timeout=5,
                shell=(platform.system() == "Windows"),
            )
            if result.returncode == 0 and result.stdout.strip():
                raw = result.stdout.strip()
                if HAS_YAML and ":" in raw:
                    try:
                        parsed = yaml.safe_load(raw)
                        if isinstance(parsed, dict):
                            # Model section has: base_url, default, provider
                            if parsed.get("provider"):
                                status["provider"] = str(parsed["provider"])
                            if parsed.get("default"):
                                status["model"] = str(parsed["default"])
                            elif parsed.get("model"):
                                status["model"] = str(parsed["model"])
                    except Exception:
                        pass
        except Exception:
            pass

    # Fallback: check if Hermes config file exists
    if not status["available"]:
        config_paths = [
            Path.home() / ".hermes" / "config.yaml",
            Path.home() / "AppData" / "Local" / "hermes" / "config.yaml",
        ]
        for cfg_path in config_paths:
            if cfg_path.exists() and HAS_YAML:
                try:
                    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
                    if cfg and ("provider" in cfg or "model" in cfg):
                        status["available"] = True
                    if cfg.get("provider"):
                        status["provider"] = cfg["provider"]
                    if cfg.get("model"):
                        status["model"] = cfg["model"]
                    break
                except Exception:
                    pass

    return status


def _get_system_metrics() -> dict:
    """Get OS-level system metrics."""
    metrics = {"cpu_percent": "--", "ram_percent": "--", "disk_percent": "--"}

    if HAS_PSUTIL:
        try:
            metrics["cpu_percent"] = round(psutil.cpu_percent(interval=0.3), 1)
        except Exception:
            pass
        try:
            mem = psutil.virtual_memory()
            metrics["ram_percent"] = round(mem.percent, 1)
        except Exception:
            pass
        try:
            disk = psutil.disk_usage(str(_runs_dir.absolute()) if _runs_dir.exists() else Path.cwd())
            metrics["disk_percent"] = round(disk.percent, 1)
        except Exception:
            pass

    return metrics


def _get_bench_status() -> dict:
    """Get Elysium-Bench specific status."""
    runs = _list_runs()
    return {
        "total_runs": len(runs),
        "active_run": _active_run_id is not None,
        "version": _bench_version,
    }


def _run_benchmark_in_thread(run_id: str, config_updates: dict):
    """Run benchmark in background thread, pushing rich SSE progress events."""
    global _active_run_id
    _active_run_id = run_id

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def _send(msg: dict):
        if run_id in _progress_queues:
            await _progress_queues[run_id].put(msg)

    async def _run():
        try:
            await _send({"type": "status", "phase": "init", "message": "Loading config and discovering tasks..."})

            from .runner import BenchmarkRunner

            runner = BenchmarkRunner()

            # Apply CLI config overrides
            selected_category = config_updates.get("category", "")
            if selected_category:
                runner.config["categories"] = [
                    c for c in runner.config["categories"] if c["id"] == selected_category
                ]

            loops_count = int(config_updates.get("loops", 10))
            runner.config["phases"]["loops"]["count"] = loops_count

            await _send({"type": "status", "phase": "discovering", "message": "Discovering tasks..."})
            categories = runner.registry.discover()
            task_count = sum(len(c.tasks) for c in categories)
            await _send({"type": "status", "phase": "ready", "message": f"Found {task_count} tasks in {len(categories)} categories"})

            # Determine which categories are active
            active_categories = [c.id for c in categories] if categories else _categories_list
            if selected_category:
                active_categories = [selected_category]

            # ── Phase: Baseline ──────────────────────────────────────────
            if runner.config["phases"]["baseline"]["enabled"]:
                phase_label = "BASELINE — All tasks WITHOUT Elysium Swarmloop"
                await _send({
                    "type": "phase_start", "phase": "baseline",
                    "label": phase_label,
                })

                # Initialize all category cards as pending
                for cat_id in active_categories:
                    await _send({
                        "type": "category_update", "category": cat_id,
                        "status": "pending", "task": "queued",
                        "score": 0, "progress": 0,
                    })

                runner._run_baseline(categories)

                # Send per-category baseline scores
                for task_id, score in runner.baseline_scores.items():
                    cat_id = _task_to_category(task_id)
                    await _send({
                        "type": "category_update", "category": cat_id,
                        "status": "running", "task": task_id,
                        "score": score.total, "progress": 50,
                    })
                    await _send({
                        "type": "category_update", "category": cat_id,
                        "status": "done", "task": task_id,
                        "score": score.total, "progress": 100,
                    })

                avg = sum(s.total for s in runner.baseline_scores.values()) / max(len(runner.baseline_scores), 1)
                await _send({
                    "type": "phase_end", "phase": "baseline",
                    "score": round(avg, 1),
                    "label": "BASELINE complete",
                })

            # ── Phase: Loops ────────────────────────────────────────────
            loop_config = runner.config["phases"]["loops"]
            total_loops = loop_config["count"]

            for loop_num in range(1, total_loops + 1):
                is_measurement = (loop_num == 1)
                phase_id = f"loop{loop_num}"

                if is_measurement:
                    label = f"LOOP 1 — MEASUREMENT Tasks WITH Elysium"
                else:
                    label = f"LOOP {loop_num} — PRACTICE Tasks WITH Elysium"

                await _send({
                    "type": "phase_start", "phase": phase_id,
                    "label": label,
                })

                # Reset category cards for this phase
                for cat_id in active_categories:
                    await _send({
                        "type": "category_update", "category": cat_id,
                        "status": "pending", "task": f"loop {loop_num}",
                        "score": 0, "progress": 0,
                    })

                runner._run_loop(categories, loop_num=loop_num, is_measurement=is_measurement, loop_config=loop_config)

                scores = runner.loop1_scores if is_measurement else (runner.practice_scores[-1] if runner.practice_scores else {})
                avg = sum(s.total for s in scores.values()) / max(len(scores), 1)

                # Send per-category scores for this loop
                for task_id, score in scores.items():
                    cat_id = _task_to_category(task_id)
                    await _send({
                        "type": "category_update", "category": cat_id,
                        "status": "done", "task": task_id,
                        "score": score.total, "progress": 100,
                    })

                await _send({
                    "type": "phase_end", "phase": phase_id,
                    "score": round(avg, 1),
                    "label": f"LOOP {loop_num} complete",
                })

            # ── Phase: Re-Test ──────────────────────────────────────────
            if runner.config["phases"]["retest"]["enabled"]:
                label = "RE-TEST — Re-running Loop 1 tasks WITH Elysium"
                await _send({
                    "type": "phase_start", "phase": "retest",
                    "label": label,
                })

                for cat_id in active_categories:
                    await _send({
                        "type": "category_update", "category": cat_id,
                        "status": "pending", "task": "re-test",
                        "score": 0, "progress": 0,
                    })

                runner._run_retest(categories, loop_config)

                avg = sum(s.total for s in runner.retest_scores.values()) / max(len(runner.retest_scores), 1)

                for task_id, score in runner.retest_scores.items():
                    cat_id = _task_to_category(task_id)
                    await _send({
                        "type": "category_update", "category": cat_id,
                        "status": "done", "task": task_id,
                        "score": score.total, "progress": 100,
                    })

                await _send({
                    "type": "phase_end", "phase": "retest",
                    "score": round(avg, 1),
                    "label": "RE-TEST complete",
                })

            # ── Generate Report ──────────────────────────────────────────
            report = runner._generate_final_report()
            runner._save_results(report)

            result_file = f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            await _send({
                "type": "complete",
                "report": report,
                "file": result_file,
            })

        except Exception as e:
            import traceback
            traceback.print_exc()
            await _send({"type": "error", "message": str(e)})
        finally:
            _active_run_id = None

    loop.run_until_complete(_run())
    loop.close()


def _task_to_category(task_id: str) -> str:
    """Extract category from task ID like T01_api_development → api_development."""
    parts = task_id.split("_", 1)
    if len(parts) >= 2:
        cat = parts[1]
        if cat in _categories_list:
            return cat
    return task_id


# ── API Routes ───────────────────────────────────────────────────────────────

@app.get("/api/runs")
async def api_runs():
    return _list_runs()


@app.get("/api/runs/{run_id}")
async def api_run_detail(run_id: str):
    f = _runs_dir / f"results_{run_id}.json"
    data = _load_results_file(f)
    if not data:
        return JSONResponse({"error": "not found"}, status_code=404)
    return data


@app.get("/api/system-status")
async def api_system_status():
    """Return combined system status: Hermes + OS metrics + bench info."""
    return {
        "hermes": _get_hermes_status(),
        "system": _get_system_metrics(),
        "bench": _get_bench_status(),
        "timestamp": datetime.now().isoformat(),
    }


@app.post("/api/runs/start")
async def api_start_run(
    category: str = Query(default=""),
    loops: int = Query(default=10),
):
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    _progress_queues[run_id] = asyncio.Queue()

    thread = threading.Thread(
        target=_run_benchmark_in_thread,
        args=(run_id, {"category": category, "loops": loops}),
        daemon=True,
    )
    thread.start()

    return {"run_id": run_id, "status": "started"}


@app.get("/api/runs/{run_id}/stream")
async def api_run_stream(run_id: str):
    """SSE endpoint for real-time progress with per-category updates."""
    if run_id not in _progress_queues:
        return StreamingResponse(
            _fake_stream("Run not found"),
            media_type="text/event-stream",
        )

    async def event_stream():
        q = _progress_queues[run_id]
        while True:
            try:
                msg = await asyncio.wait_for(q.get(), timeout=30)
                yield f"data: {json.dumps(msg)}\n\n"
                if msg["type"] in ("complete", "error"):
                    break
            except asyncio.TimeoutError:
                yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"

        # Cleanup after 60s
        await asyncio.sleep(60)
        _progress_queues.pop(run_id, None)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


async def _fake_stream(msg: str):
    yield f"data: {json.dumps({'type': 'error', 'message': msg})}\n\n"


# ── HTML Pages ───────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    return PAGE_SHELL.format(
        title="Elysium-Bench Dashboard",
        styles=STYLES,
        content=DASHBOARD_PAGE,
    )


@app.get("/run", response_class=HTMLResponse)
async def run_page():
    return PAGE_SHELL.format(
        title="Run Benchmark — Elysium-Bench",
        styles=STYLES,
        content=RUN_PAGE,
    )


@app.get("/results/{run_id}", response_class=HTMLResponse)
async def results_page(run_id: str):
    return PAGE_SHELL.format(
        title=f"Results {run_id} — Elysium-Bench",
        styles=STYLES,
        content=RESULTS_PAGE.format(run_id=run_id),
    )


@app.get("/compare", response_class=HTMLResponse)
async def compare_page(
    a: str = Query(default=""),
    b: str = Query(default=""),
):
    return PAGE_SHELL.format(
        title="Compare Runs — Elysium-Bench",
        styles=STYLES,
        content=COMPARE_PAGE.format(run_a=a, run_b=b),
    )


# ── Launcher ─────────────────────────────────────────────────────────────────

def start_ui(host: str = "127.0.0.1", port: int = 8080):
    """Start the UI server."""
    print(f"""
  ╔═══════════════════════════════════════════════════╗
  ║         🚀 Elysium-Bench UI v{_bench_version}                  ║
  ╠═══════════════════════════════════════════════════╣
  ║  Dashboard   → http://{host}:{port}                 ║
  ║  Run Bench   → http://{host}:{port}/run              ║
  ║  Compare     → http://{host}:{port}/compare          ║
  ║  System API  → http://{host}:{port}/api/system-status ║
  ╚═══════════════════════════════════════════════════╝
""")
    uvicorn.run(app, host=host, port=port, log_level="warning")
