"""Hidden tests: parser module — exact behavior, malformed inputs."""
import pytest

from parser import parse_event


def test_basic_parse():
    assert parse_event("TS=100 TYPE=click VAL=3.5") == {
        "ts": 100, "type": "click", "val": 3.5}


def test_fields_any_order():
    assert parse_event("VAL=2.5 TYPE=view TS=5") == {
        "ts": 5, "type": "view", "val": 2.5}


def test_extra_whitespace_tolerated():
    assert parse_event("  TS=7    TYPE=buy   VAL=0.25  ") == {
        "ts": 7, "type": "buy", "val": 0.25}


def test_negative_and_float_values():
    assert parse_event("TS=-3 TYPE=tick VAL=-0.125") == {
        "ts": -3, "type": "tick", "val": -0.125}


def test_missing_field_raises():
    with pytest.raises(ValueError):
        parse_event("TS=1 TYPE=x")


def test_non_numeric_ts_raises():
    with pytest.raises(ValueError):
        parse_event("TS=abc TYPE=x VAL=1.0")


def test_non_numeric_val_raises():
    with pytest.raises(ValueError):
        parse_event("TS=1 TYPE=x VAL=hello")


def test_empty_string_raises():
    with pytest.raises(ValueError):
        parse_event("")


def test_unknown_fields_tolerated():
    # extra unknown fields must not crash the parser
    ev = parse_event("TS=1 TYPE=x VAL=2.0 EXTRA=foo")
    assert ev["ts"] == 1 and ev["type"] == "x" and ev["val"] == 2.0
