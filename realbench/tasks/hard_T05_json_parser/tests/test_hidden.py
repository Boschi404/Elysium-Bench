"""Hidden tests: strict JSON codec — exact values, escapes, error positions."""
import time

import pytest

from jsoncodec import dumps, parse


def test_primitives():
    assert parse("true") is True
    assert parse("false") is False
    assert parse("null") is None
    assert parse("42") == 42
    assert parse("-7") == -7
    assert parse("3.14") == 3.14
    assert parse("-0.5") == -0.5
    assert parse("1.5e3") == 1500.0
    assert parse("1e-3") == 0.001
    assert parse('"hello"') == "hello"
    assert parse('""') == ""


def test_containers():
    assert parse('{"a": 1, "b": [true, null]}') == {"a": 1, "b": [True, None]}
    assert parse("[]") == []
    assert parse("{}") == {}
    assert parse("[1, [2, [3, [4]]]]") == [1, [2, [3, [4]]]]


def test_string_escapes():
    assert parse(r'"a\"b"') == 'a"b'
    assert parse(r'"a\\b"') == "a\\b"
    assert parse(r'"a\nb\tc"') == "a\nb\tc"
    assert parse(r'"\u0041"') == "A"
    assert parse(r'"\u00e9"') == "\u00e9"
    # surrogate pair: U+1F600
    assert parse(r'"\ud83d\ude00"') == "\U0001F600"


def test_utf8_passthrough():
    assert parse('"caf\u00e9"') == "caf\u00e9"
    assert parse('"\u20ac"') == "\u20ac"


def test_nesting_200_deep():
    deep = "[" * 200 + "null" + "]" * 200
    v = parse(deep)
    for _ in range(200):
        assert isinstance(v, list) and len(v) == 1
        v = v[0]
    assert v is None


def test_invalid_json_raises_with_position():
    bad = ["", "   ", "{", "[", '{"a": 1', '{"a": 1,}', "[1,]", "[1 2]",
           "{'a': 1}", "{a: 1}", "01", "-", "+5", ".5", "5.", "5e",
           "NaN", "Infinity", "tru", "nul", '{"a": 1} trailing',
           '"\q"', '"unterminated', "0x10", "--5"]
    for b in bad:
        with pytest.raises(ValueError) as e:
            parse(b)
        assert "position" in str(e.value).lower(), f"no position for {b!r}"


def test_dumps_compact():
    assert dumps({"a": 1, "b": [True, None, "x"]}) == '{"a":1,"b":[true,null,"x"]}'
    assert dumps([]) == "[]"
    assert dumps("hi") == '"hi"'
    assert dumps(3.14) == "3.14"


def test_dumps_escapes():
    assert dumps('a"b') == r'"a\"b"'
    assert dumps("a\nb") == r'"a\nb"'
    assert dumps("a\\b") == r'"a\\b"'


def test_dumps_non_ascii_passthrough():
    assert dumps("caf\u00e9") == '"caf\u00e9"'


def test_roundtrip_random():
    import random
    rng = random.Random(55)

    def gen(depth=0):
        if depth > 4:
            return rng.choice([1, -2.5, "x", True, None])
        kind = rng.randint(0, 4)
        if kind == 0:
            return [gen(depth + 1) for _ in range(rng.randint(0, 4))]
        if kind == 1:
            return {f"k{i}": gen(depth + 1) for i in range(rng.randint(0, 4))}
        if kind == 2:
            return rng.choice([rng.randint(-1000, 1000), rng.random() * 100])
        if kind == 3:
            return "".join(chr(rng.randint(32, 126)) for _ in range(rng.randint(0, 10)))
        return rng.choice([True, False, None])

    for _ in range(50):
        obj = gen()
        assert parse(dumps(obj)) == obj


def test_dumps_type_errors():
    with pytest.raises(TypeError):
        dumps({1: "a"})
    with pytest.raises(TypeError):
        dumps({1, 2})


def test_parse_perf_100k_numbers():
    data = "[" + ",".join(str(i) for i in range(100_000)) + "]"
    start = time.perf_counter()
    result = parse(data)
    elapsed = time.perf_counter() - start
    assert len(result) == 100_000
    assert result[99999] == 99999
    assert elapsed < 5.0, f"too slow: {elapsed:.2f}s"
