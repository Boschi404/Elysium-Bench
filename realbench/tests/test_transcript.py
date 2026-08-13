"""Transcript evidence extraction — tested against a fake state.db."""
import json
import sqlite3
from pathlib import Path

from realbench.transcript import (
    SessionEvidence,
    collect_evidence,
    parse_session_id_from_stdout,
)


def _fake_db(tmp_path: Path, session_id: str, messages: list[tuple],
            sys_prompt: str, tokens=(1000, 500, 200, 0, 7, 4, 12, 0.05, 0.04,
                                      100.0, 250.0, "goal_achieved")) -> Path:
    db = tmp_path / "state.db"
    conn = sqlite3.connect(db)
    conn.execute("""CREATE TABLE sessions (
        id TEXT PRIMARY KEY, input_tokens INTEGER, output_tokens INTEGER,
        cache_read_tokens INTEGER, reasoning_tokens INTEGER, api_call_count INTEGER,
        tool_call_count INTEGER, message_count INTEGER, estimated_cost_usd REAL,
        actual_cost_usd REAL, started_at REAL, ended_at REAL, end_reason TEXT,
        system_prompt_hash TEXT)""")
    conn.execute("CREATE TABLE system_prompts (hash TEXT PRIMARY KEY, prompt TEXT)")
    conn.execute("""CREATE TABLE messages (
        id INTEGER PRIMARY KEY, session_id TEXT, role TEXT, content TEXT,
        tool_call_id TEXT, tool_calls TEXT, tool_name TEXT, timestamp REAL,
        token_count INTEGER, finish_reason TEXT, reasoning TEXT,
        reasoning_content TEXT, reasoning_details TEXT, codex_reasoning_items TEXT,
        codex_message_items TEXT, platform_message_id TEXT, observed INTEGER,
        active INTEGER, compacted INTEGER, effect_disposition TEXT,
        api_content TEXT, display_kind TEXT, display_metadata TEXT)""")
    hash_v = "h_" + session_id
    conn.execute("INSERT INTO system_prompts VALUES (?,?)", (hash_v, sys_prompt))
    conn.execute("INSERT INTO sessions VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                 (session_id,) + tokens + (hash_v,))
    for m in messages:
        conn.execute(
            "INSERT INTO messages (session_id, role, tool_name, tool_calls, active) "
            "VALUES (?,?,?,?,1)", m)
    conn.commit()
    conn.close()
    return db


def _delegate_args(tasks: list, goal: str | None = None) -> str:
    if tasks:
        return json.dumps({"tasks": tasks})
    return json.dumps({"goal": goal})


def test_collect_evidence_counts_delegation(tmp_path):
    msgs = [
        ("s1", "assistant", "delegate_task",
         _delegate_args([{"goal": "build parser"}, {"goal": "build validator"}])),
        ("s1", "assistant", "delegate_task", _delegate_args([], "fix api module")),
        ("s1", "assistant", "delegate_task", _delegate_args([{"goal": "build parser"}])),  # retry
        ("s1", "assistant", "write_file", None),
        ("s1", "assistant", "terminal", None),
    ]
    db = _fake_db(tmp_path, "s1", msgs, sys_prompt="system prompt with elysium-swarmloop loaded")
    ev = collect_evidence(db, "s1")
    assert ev.found
    assert ev.skill_loaded
    assert ev.delegate_calls == 3
    assert ev.subagents_dispatched == 2 + 1 + 1
    assert ev.batched_dispatches == 1
    assert ev.retries == 1  # 'build parser' dispatched twice
    assert ev.write_file_calls == 1
    assert ev.terminal_calls == 1
    assert ev.input_tokens == 1000 and ev.estimated_cost_usd == 0.05
    assert ev.wall_seconds == 150.0


def test_no_delegation_when_absent(tmp_path):
    msgs = [("s2", "assistant", "write_file", None)]
    db = _fake_db(tmp_path, "s2", msgs, sys_prompt="plain agent, no skill")
    ev = collect_evidence(db, "s2")
    assert ev.delegate_calls == 0 and ev.subagents_dispatched == 0
    assert not ev.skill_loaded


def test_missing_session(tmp_path):
    db = _fake_db(tmp_path, "s3", [], sys_prompt="x")
    ev = collect_evidence(db, "nope")
    assert not ev.found
    assert ev.notes


def test_parse_session_id_from_stdout():
    out = "some output\nSession id: 20260813_142530_ab12cd\nmore"
    assert parse_session_id_from_stdout(out) == "20260813_142530_ab12cd"
    assert parse_session_id_from_stdout("no session here") == ""
