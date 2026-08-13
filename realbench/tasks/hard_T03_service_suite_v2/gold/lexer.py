"""Reference: lexer.py"""
import re

_NUM_RE = re.compile(r"\d+(\.\d+)?([eE][+-]?\d+)?")
_ID_RE = re.compile(r"[a-zA-Z_][a-zA-Z0-9_]*")
_TWO_CHAR_OPS = ("<=", ">=", "==", "!=")
_ONE_CHAR_OPS = "+-*/%(),<>"
_KEYWORDS = {"true", "false", "none", "and", "or", "not"}
_ESCAPES = {"n": "\n", "t": "\t", "\\": "\\", "'": "'"}


def tokenize(text: str) -> list[tuple]:
    tokens = []
    i = 0
    n = len(text)
    while i < n:
        c = text[i]
        if c.isspace():
            i += 1
            continue
        if c == "#":
            while i < n and text[i] != "\n":
                i += 1
            continue
        if c.isdigit():
            m = _NUM_RE.match(text, i)
            raw = m.group(0)
            value = float(raw) if ("." in raw or "e" in raw or "E" in raw) \
                else int(raw)
            tokens.append(("num", value))
            i = m.end()
            continue
        if c == "'":
            i += 1
            buf = []
            while True:
                if i >= n:
                    raise ValueError(
                        f"unterminated string at position {i}")
                ch = text[i]
                if ch == "\n":
                    raise ValueError(
                        f"unterminated string at position {i}")
                if ch == "'":
                    i += 1
                    break
                if ch == "\\":
                    i += 1
                    if i >= n or text[i] not in _ESCAPES:
                        raise ValueError(
                            f"invalid escape at position {i}")
                    buf.append(_ESCAPES[text[i]])
                    i += 1
                    continue
                buf.append(ch)
                i += 1
            tokens.append(("str", "".join(buf)))
            continue
        if c.isalpha() or c == "_":
            m = _ID_RE.match(text, i)
            word = m.group(0)
            if word in _KEYWORDS:
                tokens.append(("kw", word))
            else:
                tokens.append(("ident", word))
            i = m.end()
            continue
        two = text[i:i + 2]
        if two in _TWO_CHAR_OPS:
            tokens.append(("op", two))
            i += 2
            continue
        if c in _ONE_CHAR_OPS:
            tokens.append(("op", c))
            i += 1
            continue
        raise ValueError(f"illegal character {c!r} at position {i}")
    return tokens
