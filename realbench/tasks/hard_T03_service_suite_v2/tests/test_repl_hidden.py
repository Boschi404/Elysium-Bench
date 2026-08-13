"""Hidden tests: repl.run contract."""
from repl import run


def test_ok_flow():
    assert run("1 + 2") == {"status": "ok", "value": 3}


def test_env_passed():
    assert run("x * 2", {"x": 21}) == {"status": "ok", "value": 42}


def test_env_defaults_to_empty():
    r = run("1 + 1")
    assert r["status"] == "ok" and r["value"] == 2


def test_lex_error_captured():
    r = run("1 + @")
    assert r["status"] == "error"
    assert "position" in r["error"].lower()


def test_parse_error_captured():
    r = run("(1 +")
    assert r["status"] == "error"
    assert "position" in r["error"].lower()


def test_eval_errors_captured():
    assert run("5 / 0")["status"] == "error"
    assert run("missing_var")["status"] == "error"
    assert run("1 + 'a'")["status"] == "error"


def test_never_raises():
    # a batch of nasty inputs must never raise
    for bad in ["", "   ", "'unterminated", ")", "((", "1 2", "@@@",
                "len()", "min()", "'a' - 1", "1 / 0", "x"]:
        r = run(bad)
        assert isinstance(r, dict) and r["status"] in ("ok", "error"), bad


def test_comments_in_repl():
    assert run("1 + 2 # the answer\n") == {"status": "ok", "value": 3}
