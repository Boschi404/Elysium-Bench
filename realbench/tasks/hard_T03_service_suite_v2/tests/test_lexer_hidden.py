"""Hidden tests: lexer — exact token streams and error positions."""
import pytest

from lexer import tokenize


def test_numbers():
    assert tokenize("42") == [("num", 42)]
    toks = tokenize("3.14")
    assert toks[0][0] == "num" and toks[0][1] == 3.14
    toks = tokenize("1.5e3")
    assert toks[0][0] == "num" and toks[0][1] == 1500.0
    toks = tokenize("1e-3")
    assert toks[0][0] == "num" and abs(toks[0][1] - 0.001) < 1e-12
    toks = tokenize("7")
    assert isinstance(toks[0][1], int)


def test_strings_with_escapes():
    assert tokenize("'hi'") == [("str", "hi")]
    assert tokenize(r"'a\nb'") == [("str", "a\nb")]
    assert tokenize(r"'it\'s'") == [("str", "it's")]
    assert tokenize(r"'a\\b'") == [("str", "a\\b")]
    assert tokenize("''") == [("str", "")]


def test_identifiers_and_keywords():
    assert tokenize("foo_bar x1") == [("ident", "foo_bar"), ("ident", "x1")]
    assert tokenize("true false none and or not") == [
        ("kw", "true"), ("kw", "false"), ("kw", "none"),
        ("kw", "and"), ("kw", "or"), ("kw", "not")]


def test_operators():
    assert tokenize("+ - * / % ( ) , < <= > >= == !=") == [
        ("op", "+"), ("op", "-"), ("op", "*"), ("op", "/"), ("op", "%"),
        ("op", "("), ("op", ")"), ("op", ","), ("op", "<"), ("op", "<="),
        ("op", ">"), ("op", ">="), ("op", "=="), ("op", "!=")]


def test_comments_skipped():
    assert tokenize("1 + 2 # comment\n+ 3") == [
        ("num", 1), ("op", "+"), ("num", 2), ("op", "+"), ("num", 3)]
    assert tokenize("# only a comment") == []


def test_whitespace_tolerated():
    assert tokenize("  1\t+\n2  ") == [("num", 1), ("op", "+"), ("num", 2)]


def test_illegal_char_error_with_position():
    with pytest.raises(ValueError) as e:
        tokenize("1 + @")
    assert "position" in str(e.value).lower()
    assert "3" in str(e.value) or "4" in str(e.value)  # zero-based or 1-based


def test_double_quote_string_illegal():
    with pytest.raises(ValueError):
        tokenize('"hello"')


def test_unclosed_string():
    with pytest.raises(ValueError):
        tokenize("'unterminated")


def test_unclosed_string_with_newline():
    with pytest.raises(ValueError):
        tokenize("'line1\nline2'")


def test_dot_alone_illegal():
    with pytest.raises(ValueError):
        tokenize("1 + .")


def test_lone_equal_illegal():
    with pytest.raises(ValueError):
        tokenize("a = b")
