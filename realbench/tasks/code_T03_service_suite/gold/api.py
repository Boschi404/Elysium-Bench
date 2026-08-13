"""Reference: api.py"""
from parser import parse_event
from validator import validate_event


def process_line(line: str, store, rules: dict) -> dict:
    try:
        event = parse_event(line)
    except ValueError as exc:
        return {"status": "error", "error": str(exc)}
    if not validate_event(event, rules):
        return {"status": "rejected"}
    if store.insert(event):
        return {"status": "ok"}
    return {"status": "rejected"}
