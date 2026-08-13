"""Reference: mini regex engine — tokenized recursive matcher with memoization.

Memoization on (token_index, text_pos) makes matching polynomial and immune
to catastrophic backtracking.
"""

_ESCAPES = {'.': '.', '^': '^', '$': '$', '[': '[', ']': ']', '*': '*',
            '+': '+', '?': '?', '\\': '\\', 'n': '\n', 't': '\t'}
_META = set('.^$[]*+?\\')


def _parse_pattern(pattern: str):
    """Return a list of (atom, quantifier) tokens.
    atom: ('lit', c) | ('dot',) | ('cls', frozenset, negated)
    quantifier: '' | '*' | '+' | '?'
    """
    tokens = []
    i = 0
    n = len(pattern)
    last_was_quantifier = False
    while i < n:
        c = pattern[i]
        if c == '[':
            if last_was_quantifier:
                last_was_quantifier = False
            i += 1
            neg = False
            if i < n and pattern[i] == '^':
                neg = True
                i += 1
            chars = set()
            first = True
            while True:
                if i >= n:
                    raise ValueError("unterminated character class")
                cc = pattern[i]
                if cc == ']' and not first:
                    i += 1
                    break
                first = False
                if cc == '\\':
                    i += 1
                    if i >= n:
                        raise ValueError("bad escape in class")
                    chars.add(pattern[i])
                    i += 1
                    continue
                # range?
                if (i + 2 < n and pattern[i + 1] == '-'
                        and pattern[i + 2] != ']'):
                    lo, hi = pattern[i], pattern[i + 2]
                    if lo > hi:
                        raise ValueError("descending range")
                    for ch in range(ord(lo), ord(hi) + 1):
                        chars.add(chr(ch))
                    i += 3
                    continue
                chars.add(cc)
                i += 1
            if not chars:
                raise ValueError("empty character class")
            tokens.append([('cls', frozenset(chars), neg), ''])
        elif c == '.':
            tokens.append([('dot',), ''])
            i += 1
            last_was_quantifier = False
        elif c == '\\':
            i += 1
            if i >= n or pattern[i] not in _ESCAPES:
                raise ValueError("invalid escape")
            tokens.append([('lit', _ESCAPES[pattern[i]]), ''])
            i += 1
            last_was_quantifier = False
        elif c in '*+?':
            if not tokens or last_was_quantifier:
                raise ValueError("quantifier without atom")
            tokens[-1][1] = c
            i += 1
            last_was_quantifier = True
        else:
            tokens.append([('lit', c), ''])
            i += 1
            last_was_quantifier = False
    return tokens


class Regex:
    def __init__(self, pattern: str):
        if not isinstance(pattern, str):
            raise ValueError("pattern must be a string")
        self._tokens = _parse_pattern(pattern)

    # ── matcher ────────────────────────────────────────────────────────────
    def _atom_matches(self, atom, text, pos):
        if pos >= len(text):
            return -1
        kind = atom[0]
        if kind == 'lit':
            return pos + 1 if text[pos] == atom[1] else -1
        if kind == 'dot':
            return pos + 1 if text[pos] != '\n' else -1
        chars, neg = atom[1], atom[2]
        inside = text[pos] in chars
        return pos + 1 if inside != neg else -1

    def _longest(self, ti, pos, text, memo):
        """Max end position reachable from (token ti, text pos); -1 if none."""
        key = (ti, pos)
        if key in memo:
            return memo[key]
        if ti == len(self._tokens):
            memo[key] = pos
            return pos
        atom, q = self._tokens[ti]
        best = -1

        def try_next(p):
            nonlocal best
            if p < 0:
                return
            end = self._longest(ti + 1, p, text, memo)
            if end > best:
                best = end

        if q == '':
            try_next(self._atom_matches(atom, text, pos))
        elif q == '?':
            try_next(pos)
            try_next(self._atom_matches(atom, text, pos))
        else:
            p = pos
            if q == '*':
                try_next(p)
            while True:
                p = self._atom_matches(atom, text, p)
                if p < 0:
                    break
                try_next(p)
        memo[key] = best
        return best

    def match(self, text: str) -> bool:
        if not isinstance(text, str):
            return False
        memo = {}
        end = self._longest(0, 0, text, memo)
        return end == len(text)

    def find(self, text: str) -> list[str]:
        if not isinstance(text, str):
            raise TypeError("text must be a string")
        out = []
        i = 0
        memo = {}
        while i <= len(text):
            end = self._longest(0, i, text, memo)
            if end < 0:
                i += 1
            elif end == i:
                out.append("")
                i += 1
            else:
                out.append(text[i:end])
                i = end
        return out
