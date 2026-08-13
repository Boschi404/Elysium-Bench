"""Hidden tests: mini regex engine — exact semantics, adversarial cases."""
import time

import pytest

from regex import Regex


def test_literal_match():
    r = Regex("abc")
    assert r.match("abc") is True
    assert r.match("ab") is False
    assert r.match("abcd") is False
    assert r.match("xbc") is False


def test_dot_any_char():
    r = Regex("a.c")
    assert r.match("abc")
    assert r.match("aZc")
    assert not r.match("ac")


def test_dot_not_newline():
    r = Regex("a.c")
    assert not r.match("a\nc")


def test_class_ranges():
    r = Regex("[a-z][0-9]")
    assert r.match("b7")
    assert not r.match("B7")
    assert not r.match("7b")


def test_negated_class():
    r = Regex("[^a-z]")
    assert r.match("A")
    assert r.match("1")
    assert not r.match("a")


def test_escapes():
    assert Regex(r"\.").match(".")
    assert Regex(r"\\").match("\\")
    assert Regex(r"a\nb").match("a\nb")
    assert Regex(r"a\tb").match("a\tb")
    assert Regex(r"\*").match("*")


def test_quantifiers_basic():
    assert Regex("ab*c").match("ac")
    assert Regex("ab*c").match("abbbc")
    assert Regex("ab+c").match("abc")
    assert not Regex("ab+c").match("ac")
    assert Regex("ab?c").match("ac")
    assert Regex("ab?c").match("abc")
    assert not Regex("ab?c").match("abbc")


def test_class_quantifier():
    r = Regex("[ab]+")
    assert r.match("abba")
    assert not r.match("")
    assert Regex("[ab]*").match("")


def test_greedy_leftmost_longest_find():
    r = Regex("a.*a")
    assert r.find("aXaYa") == ["aXaYa"]
    r2 = Regex("a[^a]*a")
    # "aXaYa" = a X a Y a: first match "aXa", remainder "Ya" has no match
    assert r2.find("aXaYa") == ["aXa"]  # same as re.findall


def test_multiple_matches_non_overlapping():
    r = Regex("ab")
    assert r.find("ababab") == ["ab", "ab", "ab"]
    assert r.find("xabab") == ["ab", "ab"]


def test_empty_pattern():
    r = Regex("")
    assert r.match("")
    assert not r.match("a")
    assert r.find("a") == ["", ""]


def test_star_on_non_matching_text():
    assert Regex("a*").find("b") == ["", ""]


def test_unicode_literal():
    assert Regex("caf\u00e9").match("caf\u00e9")
    assert not Regex("caf\u00e9").match("cafe")


def test_invalid_patterns_raise():
    for bad in ["*a", "+a", "?a", "a**", "a*+", "a??", "[", "[]", "[^]",
                "[z-a]", "a\\", "\\q"]:
        with pytest.raises(ValueError):
            Regex(bad)


def test_class_edge_dash_literal():
    assert Regex("[a-]").match("-")
    assert Regex("[-a]").match("a")
    assert Regex(r"[\]]").match("]")


def test_backtracking_perf_safe():
    r = Regex("a*a*a*a*a*b")
    start = time.perf_counter()
    result = r.match("a" * 30)
    elapsed = time.perf_counter() - start
    assert result is False
    assert elapsed < 2.0, f"catastrophic backtracking: {elapsed:.2f}s"


def test_long_chain_star():
    r = Regex("a*a*a*b")
    assert r.match("aaab")
    assert not r.match("aaa")
