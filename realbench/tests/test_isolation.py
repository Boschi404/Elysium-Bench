"""Condition isolation + command construction + prompt honesty."""
import tempfile
from pathlib import Path

from realbench.harness import (
    build_cmd,
    build_prompt,
    prepare_workspace,
    _isolated_home,
)
from realbench.task_loader import get_task


def test_baseline_cmd_strips_delegation_and_skill(tmp_path):
    task = get_task("code_T01_lru_cache")
    ws = Path(tmp_path)
    cmd = build_cmd(task, "baseline", ws, 15)
    assert "-s" not in cmd and "elysium-swarmloop" not in cmd
    ti = cmd.index("-t")
    assert "file" in cmd[ti + 1] and "delegation" not in cmd[ti + 1]


def test_elysium_modes_preload_skill(tmp_path):
    task = get_task("code_T01_lru_cache")
    ws = Path(tmp_path)
    for mode in ("swarmloop", "maxeffort", "mesm"):
        cmd = build_cmd(task, mode, ws, 15)
        assert "-s" in cmd and "elysium-swarmloop" in cmd, mode
        assert "-t" not in cmd, mode  # full toolset


def test_trigger_keywords_exact_caps():
    task = get_task("hard_T01_mini_regex")
    p_max = build_prompt(task, Path("ws"), "maxeffort")
    p_mesm = build_prompt(task, Path("ws"), "mesm")
    p_base = build_prompt(task, Path("ws"), "swarmloop")
    assert p_max.startswith("MAX EFFORT\n")
    assert p_mesm.startswith("MESM\n")
    assert "MAX EFFORT" not in p_base
    assert "MESM" not in p_base
    assert "CONFIRMED" in p_mesm and "CONTINUE" in p_mesm


def test_swarmloop_cmd_preloads_skill_and_full_tools(tmp_path):
    task = get_task("code_T01_lru_cache")
    ws = Path(tmp_path)
    cmd = build_cmd(task, "swarmloop", ws, 15)
    assert "-s" in cmd and "elysium-swarmloop" in cmd
    assert "-t" not in cmd  # no toolset restriction


def test_baseline_prompt_forbids_delegation():
    task = get_task("code_T01_lru_cache")
    p = build_prompt(task, Path("ws"), "baseline").lower()
    assert "do not delegate" in p
    assert "do not load skills" in p


def test_swarmloop_prompt_invites_subagents():
    task = get_task("code_T01_lru_cache")
    p = build_prompt(task, Path("ws"), "swarmloop")
    assert "delegate_task" in p and "subagents" in p


def test_isolated_home_has_no_skills(tmp_path):
    main = tmp_path / "main"
    (main / "skills").mkdir(parents=True)
    (main / "skills" / "SKILL.md").write_text("x")
    (main / "config.yaml").write_text("model: test")
    (main / ".env").write_text("KEY=1")
    iso = _isolated_home(tmp_path / "iso_parent", main)
    assert (iso / "config.yaml").exists()
    assert (iso / ".env").exists()
    assert (iso / "skills").is_dir()
    assert list((iso / "skills").iterdir()) == []  # zero skills visible


def test_workspace_prep_excludes_tests_and_gold():
    task = get_task("code_T04_bug_hunt")
    ws = prepare_workspace(task, Path(tempfile.mkdtemp()))
    names = {p.name for p in ws.rglob("*")}
    assert "stats.py" in names  # repo files copied
    assert "test_hidden.py" not in names
    assert "gold" not in {p.name for p in ws.parent.iterdir()}
