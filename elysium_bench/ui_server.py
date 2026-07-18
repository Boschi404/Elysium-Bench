"""Elysium-Bench UI Server — FastAPI + Chart.js dashboard.

Start with: elysium-bench ui
Opens: http://localhost:8080

Features:
- Dashboard: historical run comparison (line chart)
- Run: start new benchmarks with config selection
- Progress: real-time SSE stream during execution
- Results: detailed view per run
- Compare: side-by-side run comparison
"""

from __future__ import annotations

import asyncio
import json
import os
import queue
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
app = FastAPI(title="Elysium-Bench UI", version="0.2.0")

# Progress streams: run_id → asyncio.Queue of status updates
_progress_queues: dict[str, asyncio.Queue] = {}
_runs_dir: Path = Path("results")


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


def _run_benchmark_in_thread(run_id: str, config_updates: dict):
    """Run benchmark in background thread, pushing progress to SSE queue."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def _send(msg: dict):
        if run_id in _progress_queues:
            await _progress_queues[run_id].put(msg)

    async def _run():
        try:
            await _send({"type": "status", "phase": "init", "message": "Loading config..."})

            from .runner import BenchmarkRunner
            import yaml

            runner = BenchmarkRunner()

            # Apply CLI config overrides
            for key, val in config_updates.items():
                if key == "category" and val:
                    runner.config["categories"] = [
                        c for c in runner.config["categories"] if c["id"] == val
                    ]
                elif key == "loops" and val:
                    runner.config["phases"]["loops"]["count"] = int(val)

            await _send({"type": "status", "phase": "discovering", "message": "Discovering tasks..."})
            categories = runner.registry.discover()

            task_count = sum(len(c.tasks) for c in categories)
            await _send({"type": "status", "phase": "ready", "message": f"Found {task_count} tasks in {len(categories)} categories"})

            # Run each phase with progress
            if runner.config["phases"]["baseline"]["enabled"]:
                await _send({"type": "phase_start", "phase": "baseline", "label": "BASELINE — All tasks WITHOUT Elysium"})
                runner._run_baseline(categories)
                avg = sum(s.total for s in runner.baseline_scores.values()) / max(len(runner.baseline_scores), 1)
                await _send({"type": "phase_end", "phase": "baseline", "score": round(avg, 1)})

            loop_config = runner.config["phases"]["loops"]
            total_loops = loop_config["count"]

            for loop_num in range(1, total_loops + 1):
                is_m = (loop_num == 1)
                label = f"LOOP {loop_num} — {'Measurement' if is_m else 'Practice'} Tasks WITH Elysium"
                await _send({"type": "phase_start", "phase": f"loop_{loop_num}", "label": label})
                runner._run_loop(categories, loop_num=loop_num, is_measurement=is_m, loop_config=loop_config)

                scores = runner.loop1_scores if is_m else (runner.practice_scores[-1] if runner.practice_scores else {})
                avg = sum(s.total for s in scores.values()) / max(len(scores), 1)
                await _send({"type": "phase_end", "phase": f"loop_{loop_num}", "score": round(avg, 1)})

            if runner.config["phases"]["retest"]["enabled"]:
                await _send({"type": "phase_start", "phase": "retest", "label": "RE-TEST — Re-running Loop 1 tasks"})
                runner._run_retest(categories, loop_config)
                avg = sum(s.total for s in runner.retest_scores.values()) / max(len(runner.retest_scores), 1)
                await _send({"type": "phase_end", "phase": "retest", "score": round(avg, 1)})

            # Generate report
            report = runner._generate_final_report()
            runner._save_results(report)

            await _send({
                "type": "complete",
                "report": report,
                "file": f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            })

        except Exception as e:
            await _send({"type": "error", "message": str(e)})

    loop.run_until_complete(_run())
    loop.close()


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
    """SSE endpoint for real-time progress."""
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
    print(f"\n  🚀 Elysium-Bench UI")
    print(f"  ├─ http://{host}:{port}        Dashboard")
    print(f"  ├─ http://{host}:{port}/run     Start new benchmark")
    print(f"  └─ http://{host}:{port}/compare Compare runs\n")
    uvicorn.run(app, host=host, port=port, log_level="warning")
