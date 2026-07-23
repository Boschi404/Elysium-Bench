"""Elysium-Bench Lungo — 5 categorie × 4 loop + Re-Test
Salva risultati in risultati/ in modo incrementale."""

import json, re, shutil, subprocess, sys, time, textwrap, traceback
from pathlib import Path

BENCH_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(BENCH_DIR))
from elysium_bench.scoring import ScoringEngine
from elysium_bench.task_registry import TaskRegistry

RISULTATI_DIR = BENCH_DIR / "risultati"
TASKS_DIR = BENCH_DIR / "tasks"
WORKSPACES_DIR = BENCH_DIR / "workspaces"
HERMES_TIMEOUT = 180  # 3 min max per task

CATEGORIES = [
    "api_development",
    "bug_fixing",
    "algorithm_implementation",
    "logical_deduction",
    "code_review",
]
TOTAL_LOOPS = 4
WEIGHTS = {"correctness": 40, "completeness": 25, "efficiency": 15, "robustness": 10, "clarity": 10}

def fmt(v): return f"{v:.1f}"

def clean_ws():
    if WORKSPACES_DIR.exists(): shutil.rmtree(WORKSPACES_DIR)
    WORKSPACES_DIR.mkdir(parents=True)

def create_ws(task_dir, task_id, tag):
    ws = WORKSPACES_DIR / f"{task_id}_{tag}"
    if ws.exists(): shutil.rmtree(ws)
    ws.mkdir(parents=True); (ws / "workspace").mkdir()
    for sd in ["tests", "repo"]:
        src = task_dir / sd
        if src.exists():
            dst = ws / "workspace" / sd
            if sd == "repo":
                for f in src.iterdir(): shutil.copy2(f, ws / "workspace")
            else:
                shutil.copytree(src, dst, dirs_exist_ok=True)
    return ws

def solve_task(task, workspace):
    ws_path = workspace / "workspace"
    prompt = textwrap.dedent(f"""\
    TASK: {task.id} - {task.name}
    DESCRIPTION: {task.description}
    WORKSPACE: {ws_path}
    INSTRUCTIONS:
    1. Solve this task completely
    2. Write ALL solution files to {ws_path}/
    3. Ensure tests in {ws_path / 'tests'}/ pass (if they exist)
    4. Return a brief summary
    SKILL: elysium-swarmloop""")
    
    start = time.time()
    try:
        r = subprocess.run(["hermes","chat","-q",prompt,"--skills","elysium-swarmloop","-Q"],
                          capture_output=True, text=True, timeout=HERMES_TIMEOUT)
        elapsed = time.time() - start
        files = sorted(f.relative_to(ws_path).as_posix() for f in ws_path.rglob("*") if f.is_file())
        return {"stdout": r.stdout, "stderr": r.stderr, "returncode": r.returncode,
                "success": r.returncode == 0, "elapsed": round(elapsed, 1),
                "files": files, "mode": "hermes_elysium"}
    except subprocess.TimeoutExpired:
        return {"stdout":"","stderr":"Timeout","returncode":-1,"success":False,
                "elapsed":round(time.time()-start,1),"files":[],"mode":"timeout"}

def score_task(task_dir, workspace):
    try:
        return ScoringEngine(task_dir=task_dir, solution_dir=workspace/"workspace", weights=WEIGHTS).evaluate()
    except Exception as e:
        print(f"\n    ⚠️ Scoring error: {e}")
        from elysium_bench.scoring import ScoreBreakdown
        s = ScoreBreakdown(task_type=task_dir.name.split("_")[0] if "_" in task_dir.name else "code")
        s.gaps.append(str(e))
        return s

def run_tests(workspace):
    ws = workspace / "workspace"
    td = ws / "tests"
    if not td.exists(): return {"passed":0,"total":0,"output":"No tests dir"}
    try:
        r = subprocess.run([sys.executable,"-m","pytest",str(td),"-q","--tb=short"],
                          capture_output=True,text=True,timeout=60,cwd=str(ws))
        mp = re.search(r"(\d+)\s+passed", r.stdout)
        mf = re.search(r"(\d+)\s+failed", r.stdout)
        passed = int(mp.group(1)) if mp else 0
        failed = int(mf.group(1)) if mf else 0
        if r.returncode == 0 and mp: passed = int(mp.group(1)); failed = 0
        return {"passed":passed,"total":passed+failed,"output":r.stdout}
    except: return {"passed":0,"total":0,"output":"Test error"}

# ═══════════════════ MAIN ═══════════════════
print(f"""
┌───────────────────────────────────────────────────────────────┐
│ 🚀 Elysium-Bench Lungo                                       │
│ {len(CATEGORIES)} categorie × {TOTAL_LOOPS} loop + Re-Test = {len(CATEGORIES)*(TOTAL_LOOPS+1)} task  │
│ Timeout: {HERMES_TIMEOUT}s per task | Salvataggio incrementale │
└───────────────────────────────────────────────────────────────┘
""")

cfg = {"categories":[{"id":c,"name":c,"description":"","weight":1.0} for c in CATEGORIES]}
registry = TaskRegistry(TASKS_DIR, cfg)
categories = registry.discover()

task_map = {}
for cat in categories:
    tasks = {}
    for t in cat.tasks:
        m = re.match(r"T(\d+)", t.id)
        if m: tasks[int(m.group(1))] = t
    task_map[cat.id] = tasks
    tt = cat.tasks[0].task_type if cat.tasks else "?"
    print(f"  📂 {cat.id}: {len(tasks)} tasks (type={tt})")

clean_ws()
RISULTATI_DIR.mkdir(parents=True, exist_ok=True)
ts = time.strftime("%Y%m%d_%H%M%S")

all_results = {"timestamp":time.strftime("%Y-%m-%dT%H:%M:%S"),
               "categories":CATEGORIES,"total_loops":TOTAL_LOOPS,
               "skill":"elysium-swarmloop","loops":{}}
start_all = time.time()
completed = 0
failed = 0

# ─── RUN LOOPS ──────────────────────────────
for phase in range(1, TOTAL_LOOPS + 2):
    is_retest = phase == TOTAL_LOOPS + 1
    task_idx = 1 if is_retest else phase
    label = "🔬 LOOP 1 (measurement)" if phase == 1 else (
            "🔁 RE-TEST" if is_retest else f"🔄 LOOP {phase} (practice)")
    
    print(f"\n{'─'*60}")
    print(f"  {label}")
    print(f"{'─'*60}")
    
    phase_scores = {}
    for cat_id in CATEGORIES:
        t = task_map[cat_id].get(task_idx)
        if not t: continue
        
        print(f"\n  📌 {t.id}: {t.name} (type={t.task_type}, diff={t.difficulty})", end=" ", flush=True)
        
        ws = create_ws(t.task_dir, t.id, f"p{phase}")
        result = solve_task(t, ws)
        
        if result["mode"] == "timeout":
            print(f"→ ⏰ TIMEOUT ({HERMES_TIMEOUT}s)", flush=True)
            sd = {"correctness":0,"completeness":0,"efficiency":0,"robustness":0,"clarity":0,
                  "total":0,"passed":False,"task_type":t.task_type,"gaps":["Timeout"],"notes":[],
                  "tests":{"passed":0,"total":0,"output":"Timeout"},"files":[],"mode":"timeout"}
        else:
            score = score_task(t.task_dir, ws)
            tests = run_tests(ws)
            sd = score.to_dict()
            sd["total"] = round(score.total, 1)
            sd["tests"] = tests
            sd["files"] = result["files"]
            icon = "✅" if score.passed else "❌"
            test_str = f"{tests['passed']}/{tests['total']}" if tests['total'] > 0 else "no-tests"
            print(f"→ {fmt(score.total)}/100 {icon} [{test_str}] ⏱{result['elapsed']}s", flush=True)
        
        sd["duration_s"] = result["elapsed"]
        sd["mode"] = result["mode"]
        phase_scores[t.id] = sd
        completed += 1
    
    key = "retest" if is_retest else f"loop{phase}"
    all_results["loops"][key] = phase_scores
    
    # Salvataggio incrementale dopo ogni fase
    partial = {**all_results, "partial": True, "completed_phases": phase}
    (RISULTATI_DIR / f"checkpoint_{ts}_phase{phase}.json").write_text(
        json.dumps(partial, indent=2, default=str), encoding="utf-8")

# ─── REPORT ─────────────────────────────────
total_elapsed = time.time() - start_all
print(f"\n{'═'*60}")
print(f"  📊 FINAL REPORT")
print(f"{'═'*60}")

headers = ["Categoria"] + [f"L{i}" for i in range(1,TOTAL_LOOPS+1)] + ["Re-Test","Δ"]
print(f"\n  {'  '.join(f'{h:>8}' for h in headers)}")
print(f"  {'─'*(10*len(headers))}")

cats_data = {}
for cat_id in CATEGORIES:
    row = [cat_id[:16]]
    t1_id = f"T01_{cat_id}"
    l1 = all_results["loops"]["loop1"].get(t1_id,{}).get("total",0)
    row.append(l1)
    for li in range(2, TOTAL_LOOPS+1):
        tid = f"T{li:02d}_{cat_id}"
        sc = all_results["loops"][f"loop{li}"].get(tid,{}).get("total",0)
        row.append(sc)
    rt = all_results["loops"]["retest"].get(t1_id,{}).get("total",0)
    row.append(rt)
    delta = rt - l1
    cats_data[cat_id] = {"loop1": l1, "retest": rt, "delta": delta}
    d_icon = "📈" if delta > 0 else ("📉" if delta < 0 else "➡️")
    print("  " + "".join(f"{v:>9.1f}" if isinstance(v,float) else f"{v:>9}" for v in row) + f" {d_icon}")

l1_avg = sum(cd["loop1"] for cd in cats_data.values()) / len(cats_data)
rt_avg = sum(cd["retest"] for cd in cats_data.values()) / len(cats_data)
delta_avg = rt_avg - l1_avg
pct_improvement = ((rt_avg - l1_avg) / l1_avg * 100) if l1_avg > 0 else 0

print(f"\n  {'─'*50}")
print(f"  {'Loop 1 Avg':<30} {l1_avg:<9.1f}")
print(f"  {'Re-Test Avg':<30} {rt_avg:<9.1f}")
print(f"  {'Δ Re-Test vs Loop 1':<30} {delta_avg:>+8.1f}")
print(f"  {'Improvement':<30} {'✅ YES' if pct_improvement >= 5 else '❌ NO'} ({pct_improvement:+.1f}%)")
print(f"  {'Durata':<30} {total_elapsed/60:.1f} min ({total_elapsed:.0f}s)")
print(f"  {'Task completati':<30} {completed}")

# ─── SALVATAGGIO FINALE ─────────────────────
report = {
    "benchmark": "Elysium-Bench Lungo",
    "version": "0.4.1-lungo",
    "timestamp": all_results["timestamp"],
    "duration_minutes": round(total_elapsed/60, 1),
    "duration_seconds": round(total_elapsed, 1),
    "skill": "elysium-swarmloop",
    "categories": CATEGORIES,
    "total_loops": TOTAL_LOOPS,
    "per_category": cats_data,
    "avg_loop1": round(l1_avg, 1),
    "avg_retest": round(rt_avg, 1),
    "avg_delta": round(delta_avg, 1),
    "improvement_pct": round(pct_improvement, 1),
    "improvement_detected": pct_improvement >= 5,
    "loops": all_results["loops"],
}

# JSON finale
jp = RISULTATI_DIR / f"risultati_lungo_{ts}.json"
jp.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")

# MD
md_lines = [
    f"# Elysium-Bench — Benchmark Lungo",
    f"",
    f"**Durata:** {total_elapsed/60:.1f} min | **Skill:** elysium-swarmloop | **Provider:** OpenCode Go (deepseek-v4-flash)",
    f"**Categorie:** {', '.join(CATEGORIES)} | **Task completati:** {completed}",
    f"",
    f"## 📊 Progressione",
    f"",
    f"| Categoria | " + " | ".join(f"L{i}" for i in range(1,TOTAL_LOOPS+1)) + " | Re-Test | Δ |",
    f"|---|" + "|".join("---" for _ in range(TOTAL_LOOPS+2)),
]
for cat_id, cd in cats_data.items():
    row = f"| {cat_id} | {cd['loop1']:.1f}"
    for li in range(2, TOTAL_LOOPS+1):
        tid = f"T{li:02d}_{cat_id}"
        sc = all_results["loops"][f"loop{li}"].get(tid,{}).get("total",0)
        row += f" | {sc:.1f}"
    row += f" | {cd['retest']:.1f} | {cd['delta']:+.1f} |"
    md_lines.append(row)

md_lines += [
    f"",
    f"**Loop 1 Avg:** {l1_avg:.1f} | **Re-Test Avg:** {rt_avg:.1f} | **Δ:** {delta_avg:+.1f}",
    f"**Improvement:** {'✅ YES' if pct_improvement >= 5 else '❌ NO'} ({pct_improvement:+.1f}%)",
    f"",
    f"## ⏱ Dettaglio Task",
    f"",
    f"| Phase | Task | Score | Tests | Durata | Mode |",
    f"|-------|------|:----:|:-----:|:------:|:----:|",
]
for phase_key, scores in all_results["loops"].items():
    for tid, sd in scores.items():
        t = sd["tests"]
        ts_str = f"{t['passed']}/{t['total']}" if t['total']>0 else "no-tests"
        md_lines.append(f"| {phase_key} | {tid} | {sd['total']:.1f} | {ts_str} | {sd['duration_s']}s | {sd.get('mode','')} |")

md_lines += [f"",f"📁 File: `risultati/risultati_lungo_{ts}.json`",f"",
             f"📁 Checkpoint: `risultati/checkpoint_{ts}_phase*.json`",f""]
mp = RISULTATI_DIR / f"risultati_lungo_{ts}.md"
mp.write_text("\n".join(md_lines), encoding="utf-8")

# Pulisci checkpoint
for f in RISULTATI_DIR.glob(f"checkpoint_{ts}_*.json"):
    f.unlink()

clean_ws()
print(f"\n  📁 Risultati salvati in: risultati/")
print(f"     {jp.name}")
print(f"     {mp.name}")
print(f"  🧹 Workspaces puliti")
print(f"\n  ✅ Benchmark completo!\n")
