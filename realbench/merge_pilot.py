"""Merge probe baselines into the hard_pilot dir for the final report.

Usage: python realbench/merge_pilot.py [pilot_dir] [probe_dirs...]
Copies each probe's baseline run (stdout/stderr/prompt + isolated home) into
pilot_dir/<task>/baseline/ if not already present.
"""
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PILOT = REPO / "risultati" / (sys.argv[1] if len(sys.argv) > 1 else "realbench_hard_pilot")
PROBES = [REPO / "risultati" / p for p in
          (sys.argv[2:] if len(sys.argv) > 2
           else ["realbench_hard_probe", "realbench_hard_probe2",
                 "realbench_night_probe"])]

merged = []
for probe in PROBES:
    if not probe.exists():
        continue
    for task_dir in probe.glob("*/"):
        task_id = task_dir.name
        src = task_dir / "baseline"
        if not src.exists():
            continue
        dst = PILOT / task_id / "baseline"
        if (dst / "stdout.txt").exists():
            continue
        dst.mkdir(parents=True, exist_ok=True)
        for name in ("stdout.txt", "stderr.txt", "prompt.txt"):
            if (src / name).exists():
                shutil.copy2(src / name, dst / name)
        # copy isolated home (baseline session evidence)
        iso_src = probe / "_isolated_homes" / f"hermes_home_{task_id}_baseline"
        iso_dst = PILOT / "_isolated_homes" / f"hermes_home_{task_id}_baseline"
        if iso_src.exists():
            if iso_dst.exists():
                shutil.rmtree(iso_dst)
            shutil.copytree(iso_src, iso_dst)
        merged.append(f"{task_id}: baseline merged from {probe.name}")

print("\n".join(merged) if merged else "nothing to merge")
