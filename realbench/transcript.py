"""Transcript & session extraction — objective evidence from Hermes itself.

Reads Hermes' own session database (state.db) for a CLI run's session:
- token usage, api calls, cost (sessions table)
- delegate_task calls, dispatched subagent counts, batches, retries
- whether the elysium-swarmloop skill was loaded (system prompt scan)
"""
from __future__ import annotations

import json
import re
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class SessionEvidence:
    session_id: str = ""
    found: bool = False
    # sessions table
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    reasoning_tokens: int = 0
    api_call_count: int = 0
    tool_call_count: int = 0
    message_count: int = 0
    estimated_cost_usd: float = 0.0
    actual_cost_usd: float = 0.0
    wall_seconds: float = 0.0
    end_reason: str = ""
    # behavioral evidence
    delegate_calls: int = 0
    subagents_dispatched: int = 0
    batched_dispatches: int = 0       # delegate_task calls with >1 task
    unique_task_ids: set = field(default_factory=set)
    retries: int = 0                  # re-dispatches of same task id
    skill_loaded: bool = False
    skill_name: str = ""
    terminal_calls: int = 0
    write_file_calls: int = 0
    notes: list[str] = field(default_factory=list)


def _connect(db_path: Path) -> sqlite3.Connection:
    return sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)


def _extract_task_ids_from_args(arguments: str) -> list[str]:
    """Pull task ids from a delegate_task arguments JSON."""
    try:
        args = json.loads(arguments)
    except Exception:
        return []
    ids = []
    if "tasks" in args and isinstance(args["tasks"], list):
        for t in args["tasks"]:
            if isinstance(t, dict):
                # look for an explicit id field or derive from goal
                if "task_id" in t:
                    ids.append(str(t["task_id"]))
                elif "id" in t:
                    ids.append(str(t["id"]))
                else:
                    ids.append(str(t.get("goal", ""))[:40])
    elif "goal" in args:
        ids.append(str(args["goal"])[:40])
    return ids


def collect_evidence(db_path: Path, session_id: str) -> SessionEvidence:
    ev = SessionEvidence(session_id=session_id)
    if not db_path.exists():
        ev.notes.append(f"state.db not found at {db_path}")
        return ev
    try:
        conn = _connect(db_path)
    except sqlite3.Error as e:
        ev.notes.append(f"state.db unreadable: {e}")
        return ev
    try:
        row = conn.execute(
            "SELECT input_tokens, output_tokens, cache_read_tokens, "
            "reasoning_tokens, api_call_count, tool_call_count, message_count, "
            "estimated_cost_usd, actual_cost_usd, started_at, ended_at, "
            "end_reason, system_prompt_hash FROM sessions WHERE id = ?",
            (session_id,)).fetchone()
        if row is None:
            ev.notes.append(f"session {session_id} not found in sessions table")
            return ev
        ev.found = True
        (ev.input_tokens, ev.output_tokens, ev.cache_read_tokens,
         ev.reasoning_tokens, ev.api_call_count, ev.tool_call_count,
         ev.message_count, ev.estimated_cost_usd, ev.actual_cost_usd,
         started, ended, ev.end_reason, sys_hash) = row
        if started and ended:
            ev.wall_seconds = round(max(0.0, ended - started), 1)

        # skill loaded? The full system prompt lives in the system_prompts
        # table keyed by system_prompt_hash (sessions.system_prompt is empty).
        sys_prompt = ""
        if sys_hash:
            sp = conn.execute(
                "SELECT prompt FROM system_prompts WHERE hash = ?",
                (sys_hash,)).fetchone()
            if sp:
                sys_prompt = sp[0] or ""
        if sys_prompt and ("elysium-swarmloop" in sys_prompt
                           or "Elysium Swarmloop" in sys_prompt):
            ev.skill_loaded = True
            ev.skill_name = "elysium-swarmloop"

        # messages: count delegate_task calls and dispatched subagents
        cur = conn.execute(
            "SELECT tool_name, tool_calls, role FROM messages "
            "WHERE session_id = ? AND active = 1", (session_id,))
        task_id_counts: dict[str, int] = {}
        for tool_name, tool_calls, role in cur.fetchall():
            if tool_name == "delegate_task":
                ev.delegate_calls += 1
                ids = _extract_task_ids_from_args(tool_calls or "{}")
                n = len(ids) if ids else 1
                ev.subagents_dispatched += n
                if n > 1:
                    ev.batched_dispatches += 1
                for tid in ids:
                    task_id_counts[tid] = task_id_counts.get(tid, 0) + 1
                    ev.unique_task_ids.add(tid)
            elif tool_name == "terminal":
                ev.terminal_calls += 1
            elif tool_name == "write_file":
                ev.write_file_calls += 1
        ev.retries = sum(max(0, c - 1) for c in task_id_counts.values())
    finally:
        conn.close()
    return ev


def parse_session_id_from_stdout(stdout: str) -> str:
    """Extract the session id printed by `hermes chat --pass-session-id`."""
    patterns = [
        r"session[_:\s-]*(?:id)?\s*[:=]?\s*([0-9]{8}_[0-9]{6}_[a-f0-9]{6})",
        r"\b([0-9]{8}_[0-9]{6}_[a-f0-9]{6})\b",
    ]
    for pat in patterns:
        m = re.search(pat, stdout)
        if m:
            return m.group(1)
    return ""
