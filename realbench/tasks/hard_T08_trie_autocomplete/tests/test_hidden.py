"""Hidden tests: trie — exact semantics, duplicates, sorted autocomplete, perf."""
import random
import string
import time

import pytest

from trie import Trie


def test_insert_and_search():
    t = Trie()
    t.insert("hello")
    assert t.search("hello") is True
    assert t.search("hell") is False
    assert t.search("hello!") is False


def test_starts_with():
    t = Trie()
    assert t.starts_with("") is False  # empty trie
    t.insert("apple")
    assert t.starts_with("") is True
    assert t.starts_with("a") is True
    assert t.starts_with("app") is True
    assert t.starts_with("apple") is True
    assert t.starts_with("apples") is False
    assert t.starts_with("b") is False


def test_empty_word():
    t = Trie()
    t.insert("")
    assert t.search("") is True
    assert t.count_prefix("") == 1
    assert t.autocomplete("", 10) == [""]


def test_duplicates_are_distinct_only_once():
    t = Trie()
    t.insert("abc")
    t.insert("abc")
    t.insert("abc")
    assert t.search("abc") is True
    assert t.count_prefix("a") == 1
    assert t.autocomplete("a", 5) == ["abc"]


def test_count_prefix():
    t = Trie()
    for w in ["car", "cat", "carpet", "dog", "cart"]:
        t.insert(w)
    assert t.count_prefix("ca") == 4
    assert t.count_prefix("car") == 3
    assert t.count_prefix("z") == 0


def test_autocomplete_sorted_lexicographic():
    t = Trie()
    for w in ["banana", "apple", "apricot", "avocado", "apricots"]:
        t.insert(w)
    assert t.autocomplete("a", 10) == ["apple", "apricot", "apricots",
                                       "avocado"]
    assert t.autocomplete("ap", 10) == ["apple", "apricot", "apricots"]
    assert t.autocomplete("b", 10) == ["banana"]
    assert t.autocomplete("z", 10) == []


def test_autocomplete_k_limit():
    t = Trie()
    for w in ["aa", "ab", "ac", "ad"]:
        t.insert(w)
    assert t.autocomplete("a", 2) == ["aa", "ab"]
    with pytest.raises(ValueError):
        t.autocomplete("a", 0)
    with pytest.raises(ValueError):
        t.autocomplete("a", -1)


def test_random_vs_bruteforce():
    rng = random.Random(9988)
    words = set()
    t = Trie()
    for _ in range(500):
        w = "".join(rng.choice(string.ascii_lowercase)
                    for _ in range(rng.randint(1, 8)))
        words.add(w)
        t.insert(w)
    for _ in range(200):
        q = "".join(rng.choice(string.ascii_lowercase)
                    for _ in range(rng.randint(0, 4)))
        expected = sorted(w for w in words if w.startswith(q))
        assert t.search(q) == (q in words)
        assert t.starts_with(q) == bool(expected)
        assert t.count_prefix(q) == len(expected)
        assert t.autocomplete(q, 100) == expected[:100]


def test_perf_100k_words_50k_queries():
    rng = random.Random(4242)
    alphabet = string.ascii_lowercase
    words = set()
    while len(words) < 100_000:
        words.add("".join(rng.choice(alphabet)
                          for _ in range(rng.randint(3, 20))))

    t = Trie()
    start = time.perf_counter()
    for w in words:
        t.insert(w)
    insert_elapsed = time.perf_counter() - start

    start = time.perf_counter()
    checksum = 0
    queries = ["".join(rng.choice(alphabet) for _ in range(rng.randint(1, 5)))
               for _ in range(50_000)]
    for q in queries:
        checksum += t.count_prefix(q)
        checksum += len(t.autocomplete(q, 5))
    query_elapsed = time.perf_counter() - start
    assert checksum > 0
    assert insert_elapsed < 5.0, f"insert too slow: {insert_elapsed:.2f}s"
    assert query_elapsed < 5.0, f"queries too slow: {query_elapsed:.2f}s"


def test_prefix_of_whole_word():
    t = Trie()
    t.insert("word")
    assert t.count_prefix("word") == 1
    assert t.autocomplete("word", 5) == ["word"]
