"""Reference: repl.py"""
from eval import eval_text


def run(text: str, env: dict | None = None) -> dict:
    env = {} if env is None else env
    try:
        return {"status": "ok", "value": eval_text(text, env)}
    except Exception as e:  # noqa: BLE001 — the contract says never raise
        return {"status": "error", "error": str(e)}
