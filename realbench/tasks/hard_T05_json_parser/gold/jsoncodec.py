"""Reference: strict JSON codec (no stdlib json)."""
import re

_WS = " \t\n\r"
_ESCAPE_MAP = {'"': '"', "\\": "\\", "/": "/", "b": "\b", "f": "\f",
               "n": "\n", "r": "\r", "t": "\t"}
_NUMBER_RE = re.compile(r"-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?")


def parse(text: str):
    if not isinstance(text, str):
        raise ValueError("input must be a string")
    parser = _Parser(text)
    value = parser._value()
    parser._skip_ws()
    if parser.i < len(parser.s):
        raise ValueError(f"trailing content at position {parser.i}")
    return value


class _Parser:
    def __init__(self, s):
        self.s = s
        self.i = 0

    def _skip_ws(self):
        while self.i < len(self.s) and self.s[self.i] in _WS:
            self.i += 1

    def _err(self, msg):
        raise ValueError(f"{msg} at position {self.i}")

    def _value(self):
        self._skip_ws()
        if self.i >= len(self.s):
            self._err("unexpected end of input")
        c = self.s[self.i]
        if c == "{":
            return self._object()
        if c == "[":
            return self._array()
        if c == '"':
            return self._string()
        if c == "t":
            self._literal("true", True)
            return True
        if c == "f":
            self._literal("false", False)
            return False
        if c == "n":
            self._literal("null", None)
            return None
        if c == "-" or c.isdigit():
            return self._number()
        self._err(f"unexpected character {c!r}")

    def _literal(self, word, value):
        if self.s[self.i:self.i + len(word)] != word:
            self._err(f"invalid literal (expected {word})")
        self.i += len(word)
        return value

    def _string(self):
        start = self.i
        self.i += 1
        out = []
        while True:
            if self.i >= len(self.s):
                self._err("unterminated string")
            c = self.s[self.i]
            if c == '"':
                self.i += 1
                return "".join(out)
            if c == "\\":
                self.i += 1
                if self.i >= len(self.s):
                    self._err("unterminated escape")
                e = self.s[self.i]
                if e == "u":
                    self.i += 1
                    code = self._hex4()
                    if 0xD800 <= code <= 0xDBFF:
                        # high surrogate: require low surrogate
                        if (self.i + 1 < len(self.s)
                                and self.s[self.i:self.i + 2] == "\\u"):
                            self.i += 2
                            low = self._hex4()
                            if 0xDC00 <= low <= 0xDFFF:
                                code = 0x10000 + ((code - 0xD800) << 10) \
                                    + (low - 0xDC00)
                            else:
                                self._err("invalid low surrogate")
                        else:
                            self._err("lone high surrogate")
                    elif 0xDC00 <= code <= 0xDFFF:
                        self._err("lone low surrogate")
                    out.append(chr(code))
                elif e in _ESCAPE_MAP:
                    out.append(_ESCAPE_MAP[e])
                    self.i += 1
                else:
                    self._err(f"invalid escape \\{e}")
                continue
            if c < " ":
                self._err("unescaped control character in string")
            out.append(c)
            self.i += 1

    def _hex4(self):
        h = self.s[self.i:self.i + 4]
        if len(h) != 4 or not all(ch in "0123456789abcdefABCDEF" for ch in h):
            self._err("invalid \\u escape")
        self.i += 4
        return int(h, 16)

    def _number(self):
        m = _NUMBER_RE.match(self.s, self.i)
        if not m:
            self._err("invalid number")
        raw = m.group(0)
        if raw.startswith("0") and len(raw) > 1 and raw[1].isdigit():
            self._err("leading zeros not allowed")
        self.i = m.end()
        if any(ch in raw for ch in ".eE"):
            return float(raw)
        return int(raw)

    def _array(self):
        self.i += 1
        out = []
        self._skip_ws()
        if self.i < len(self.s) and self.s[self.i] == "]":
            self.i += 1
            return out
        while True:
            out.append(self._value())
            self._skip_ws()
            if self.i >= len(self.s):
                self._err("unterminated array")
            c = self.s[self.i]
            if c == "]":
                self.i += 1
                return out
            if c != ",":
                self._err("expected ',' or ']' in array")
            self.i += 1
            self._skip_ws()
            if self.i < len(self.s) and self.s[self.i] == "]":
                self._err("trailing comma in array")

    def _object(self):
        self.i += 1
        out = {}
        self._skip_ws()
        if self.i < len(self.s) and self.s[self.i] == "}":
            self.i += 1
            return out
        while True:
            self._skip_ws()
            if self.i >= len(self.s) or self.s[self.i] != '"':
                self._err("object keys must be strings")
            key = self._string()
            self._skip_ws()
            if self.i >= len(self.s) or self.s[self.i] != ":":
                self._err("expected ':' in object")
            self.i += 1
            out[key] = self._value()
            self._skip_ws()
            if self.i >= len(self.s):
                self._err("unterminated object")
            c = self.s[self.i]
            if c == "}":
                self.i += 1
                return out
            if c != ",":
                self._err("expected ',' or '}' in object")
            self.i += 1
            self._skip_ws()
            if self.i < len(self.s) and self.s[self.i] == "}":
                self._err("trailing comma in object")


_ESCAPE_OUT = {'"': '\\"', "\\": "\\\\", "\b": "\\b", "\f": "\\f",
               "\n": "\\n", "\r": "\\r", "\t": "\\t"}


def dumps(obj):
    if obj is None:
        return "null"
    if obj is True:
        return "true"
    if obj is False:
        return "false"
    if isinstance(obj, int) and not isinstance(obj, bool):
        return str(obj)
    if isinstance(obj, float):
        if obj != obj or obj in (float("inf"), float("-inf")):
            raise ValueError("cannot serialize NaN/Infinity")
        s = repr(obj)
        return s
    if isinstance(obj, str):
        out = ['"']
        for c in obj:
            if c in _ESCAPE_OUT:
                out.append(_ESCAPE_OUT[c])
            elif ord(c) < 0x20:
                out.append(f"\\u{ord(c):04x}")
            else:
                out.append(c)
        out.append('"')
        return "".join(out)
    if isinstance(obj, (list, tuple)):
        return "[" + ",".join(dumps(x) for x in obj) + "]"
    if isinstance(obj, dict):
        if not all(isinstance(k, str) for k in obj):
            raise TypeError("dict keys must be strings")
        return "{" + ",".join(f'{dumps(k)}:{dumps(v)}'
                              for k, v in obj.items()) + "}"
    raise TypeError(f"cannot serialize {type(obj).__name__}")
