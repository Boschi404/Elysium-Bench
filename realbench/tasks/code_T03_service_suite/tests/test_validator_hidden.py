"""Hidden tests: validator module."""
from validator import validate_event


def test_no_rules_accepts_everything():
    assert validate_event({"ts": 1, "type": "x", "val": 2.0}, {}) is True


def test_allowed_types():
    rules = {"allowed_types": ["click", "view"]}
    assert validate_event({"ts": 1, "type": "click", "val": 0.0}, rules)
    assert not validate_event({"ts": 1, "type": "buy", "val": 0.0}, rules)


def test_min_ts():
    rules = {"min_ts": 100}
    assert validate_event({"ts": 100, "type": "x", "val": 0.0}, rules)
    assert not validate_event({"ts": 99, "type": "x", "val": 0.0}, rules)


def test_max_val():
    rules = {"max_val": 10.0}
    assert validate_event({"ts": 0, "type": "x", "val": 10.0}, rules)
    assert not validate_event({"ts": 0, "type": "x", "val": 10.1}, rules)


def test_combined_rules():
    rules = {"allowed_types": ["a"], "min_ts": 5, "max_val": 1.0}
    assert validate_event({"ts": 5, "type": "a", "val": 1.0}, rules)
    assert not validate_event({"ts": 5, "type": "b", "val": 1.0}, rules)
    assert not validate_event({"ts": 4, "type": "a", "val": 1.0}, rules)
    assert not validate_event({"ts": 5, "type": "a", "val": 1.5}, rules)


def test_non_dict_returns_false():
    assert validate_event(None, {}) is False
    assert validate_event("not a dict", {}) is False
