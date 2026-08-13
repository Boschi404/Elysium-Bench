"""Hidden tests: parser + evaluator behavior (via eval_text)."""
import pytest

from eval import eval_text


def test_arithmetic_precedence():
    assert eval_text("1 + 2 * 3", {}) == 7
    assert eval_text("(1 + 2) * 3", {}) == 9
    assert eval_text("10 - 3 - 2", {}) == 5
    assert eval_text("2 * -3", {}) == -6
    assert eval_text("-2 * 3", {}) == -6
    assert eval_text("--2", {}) == 2
    assert eval_text("10 / 4", {}) == 2.5
    assert eval_text("7 % 3", {}) == 1
    assert eval_text("2 + 3 * 4 - 1", {}) == 13


def test_float_and_int_mixing():
    assert eval_text("1 + 2.0", {}) == 3.0
    assert eval_text("5 / 2", {}) == 2.5


def test_string_concat():
    assert eval_text("'ab' + 'cd'", {}) == "abcd"
    assert eval_text("'x' + '' + 'y'", {}) == "xy"


def test_type_errors():
    with pytest.raises(TypeError):
        eval_text("1 + 'a'", {})
    with pytest.raises(TypeError):
        eval_text("'a' * 2", {})
    with pytest.raises(TypeError):
        eval_text("'a' - 'b'", {})
    with pytest.raises(TypeError):
        eval_text("1 < 'a'", {})


def test_division_by_zero():
    with pytest.raises(ZeroDivisionError):
        eval_text("5 / 0", {})
    with pytest.raises(ZeroDivisionError):
        eval_text("5 % 0", {})


def test_comparisons_and_chains():
    assert eval_text("1 < 2 < 3", {}) is True
    assert eval_text("1 < 3 < 2", {}) is False
    assert eval_text("2 > 1 >= 1", {}) is True
    assert eval_text("1 == 1.0", {}) is True
    assert eval_text("1 != 2", {}) is True
    assert eval_text("'a' < 'b'", {}) is True
    assert eval_text("'a' <= 'a'", {}) is True


def test_boolean_ops_precedence_and_shortcircuit():
    assert eval_text("true or false and false", {}) is True
    assert eval_text("false and 1/0 == 0", {}) is False   # short-circuit
    assert eval_text("true or 1/0 == 0", {}) is True      # short-circuit
    assert eval_text("0 and 5", {}) == 0                  # Python truthiness
    assert eval_text("3 or 5", {}) == 3
    assert eval_text("not true", {}) is False
    assert eval_text("not 1 == 2", {}) is True            # not binds looser than ==
    assert eval_text("not 0", {}) is True


def test_literals_and_env():
    assert eval_text("true", {}) is True
    assert eval_text("false", {}) is False
    assert eval_text("none", {}) is None
    assert eval_text("x + 1", {"x": 41}) == 42
    assert eval_text("x", {"x": "hello"}) == "hello"


def test_undefined_name():
    with pytest.raises(NameError):
        eval_text("nope", {})


def test_builtins():
    assert eval_text("len('abc')", {}) == 3
    assert eval_text("len('abc') + 1", {}) == 4
    assert eval_text("abs(-5)", {}) == 5
    assert eval_text("abs(3.5)", {}) == 3.5
    assert eval_text("int(3.7)", {}) == 3
    assert eval_text("int('42')", {}) == 42
    assert eval_text("str(3.5)", {}) == "3.5"
    assert eval_text("str(true)", {}) == "True"
    assert eval_text("min(3, 1, 2)", {}) == 1
    assert eval_text("max(3, 1, 2)", {}) == 3
    assert eval_text("min('b', 'a')", {}) == "a"
    assert eval_text("max(1,2) + min(3,4)", {}) == 5
    assert eval_text("int('42') + len('ab')", {}) == 44


def test_builtin_errors():
    with pytest.raises(TypeError):
        eval_text("len(5)", {})
    with pytest.raises(TypeError):
        eval_text("min(1, 'a')", {})
    with pytest.raises(TypeError):
        eval_text("max()", {})
    with pytest.raises(NameError):
        eval_text("unknown_fn(1)", {})
    with pytest.raises(ValueError):
        eval_text("int('abc')", {})
    with pytest.raises(TypeError):
        eval_text("abs('x')", {})


def test_parse_errors_have_position():
    for bad in ["1 +", "1 2", "(1 + 2", "1 + )", ",", "()"]:
        with pytest.raises(ValueError) as e:
            eval_text(bad, {})
        assert "position" in str(e.value).lower(), bad


def test_nested_calls_and_parens():
    assert eval_text("max(1, min(5, 2), 3)", {}) == 3
    assert eval_text("(1 + (2 * (3 + 1)))", {}) == 9


def test_long_expression():
    expr = " + ".join(str(i) for i in range(1, 200))
    assert eval_text(expr, {}) == sum(range(1, 200))
