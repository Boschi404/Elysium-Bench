"""Hidden tests for bug hunt — one file per bug, partial credit per file."""
import math
import pytest

import stats
import finance
import textutil


# ── stats.py: median even-length bug ─────────────────────────────────────────
def test_stats_mean_sanity():
    assert stats.mean([1, 2, 3]) == 2.0


def test_stats_median_odd():
    assert stats.median([1, 3, 2]) == 2


def test_stats_median_even_BUG():
    """Even-length median must average the two middle values."""
    assert stats.median([1, 2, 3, 4]) == 2.5


def test_stats_stddev():
    assert abs(stats.stddev([2, 4, 4, 4, 5, 5, 7, 9]) - 2.138) < 0.01


# ── finance.py: compound interest formula bug ────────────────────────────────
def test_finance_sanity():
    assert finance.compound_interest(100, 0.0, 5) == 100


def test_finance_formula_BUG():
    """1000 at 5% for 10 years must be ~1628.89."""
    assert abs(finance.compound_interest(1000, 0.05, 10) - 1628.89) < 0.5


def test_finance_negative_inputs():
    with pytest.raises(ValueError):
        finance.compound_interest(-1, 0.05, 1)


# ── textutil.py: slugify off-by-one bug ──────────────────────────────────────
def test_textutil_sanity():
    assert textutil.slugify("Hello") == "hello"


def test_textutil_two_words_BUG():
    assert textutil.slugify("Hello World") == "hello-world"


def test_textutil_multiple_words_BUG():
    assert textutil.slugify("The Quick Brown Fox") == "the-quick-brown-fox"


def test_textutil_punctuation():
    assert textutil.slugify("Hi, there!") == "hi-there"
