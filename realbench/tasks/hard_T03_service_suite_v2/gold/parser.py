"""Reference: parser.py — Pratt parser producing a small AST."""
from dataclasses import dataclass


@dataclass
class Num:
    value: object
    pos: int = 0


@dataclass
class Str:
    value: str
    pos: int = 0


@dataclass
class Name:
    name: str
    pos: int = 0


@dataclass
class Const:
    value: object
    pos: int = 0


@dataclass
class BinOp:
    op: str
    left: object
    right: object
    pos: int = 0


@dataclass
class UnaryOp:
    op: str
    operand: object
    pos: int = 0


@dataclass
class BoolOp:
    op: str
    left: object
    right: object
    pos: int = 0


@dataclass
class Compare:
    left: object
    ops: list
    comparators: list
    pos: int = 0


@dataclass
class Call:
    func: object
    args: list
    pos: int = 0


_BINARY_BP = {"or": (10, 10), "and": (20, 20), "+": (50, 50), "-": (50, 50),
              "*": (60, 60), "/": (60, 60), "%": (60, 60)}
_CMP_OPS = {"<", "<=", ">", ">=", "==", "!="}
_CMP_BP = (40, 40)


class _Parser:
    def __init__(self, tokens):
        self.toks = tokens
        self.i = 0

    def peek(self):
        return self.toks[self.i] if self.i < len(self.toks) else None

    def next(self):
        t = self.peek()
        if t is not None:
            self.i += 1
        return t

    def _kind(self, t):
        return t[0] if t else None

    def _val(self, t):
        return t[1] if t else None

    def expect_op(self, op):
        t = self.peek()
        if t is None or t[0] != "op" or t[1] != op:
            raise ValueError(f"expected '{op}' at token position {self.i}")
        self.i += 1

    def parse(self):
        if not self.toks:
            raise ValueError("empty expression at position 0")
        node = self.expr(0)
        if self.i < len(self.toks):
            raise ValueError(f"unexpected token at token position {self.i}")
        return node

    def expr(self, min_bp):
        left = self._nud()
        while True:
            t = self.peek()
            if t is None:
                break
            if t[0] == "op" and t[1] in _CMP_OPS:
                lbp, rbp = _CMP_BP
                if lbp <= min_bp:
                    break
                ops, comparators = [], []
                while (self.peek() is not None and self.peek()[0] == "op"
                       and self.peek()[1] in _CMP_OPS):
                    op = self.next()[1]
                    ops.append(op)
                    # same binding power: the chain continues in THIS loop,
                    # not inside the comparator parse
                    comparators.append(self.expr(40))
                left = Compare(left, ops, comparators, pos=left.pos)
                continue
            if t[0] == "kw" and t[1] in _BINARY_BP:
                lbp, rbp = _BINARY_BP[t[1]]
                if lbp <= min_bp:
                    break
                op = self.next()[1]
                right = self.expr(rbp)
                left = BoolOp(op, left, right, pos=left.pos)
                continue
            if t[0] == "op" and t[1] in _BINARY_BP:
                lbp, rbp = _BINARY_BP[t[1]]
                if lbp <= min_bp:
                    break
                op = self.next()[1]
                right = self.expr(rbp)
                left = BinOp(op, left, right, pos=left.pos)
                continue
            if t[0] == "op" and t[1] == "(":
                # call
                self.i += 1
                args = []
                if not (self.peek() and self.peek()[0] == "op"
                        and self.peek()[1] == ")"):
                    args.append(self.expr(0))
                    while (self.peek() and self.peek()[0] == "op"
                           and self.peek()[1] == ","):
                        self.i += 1
                        args.append(self.expr(0))
                self.expect_op(")")
                left = Call(left, args, pos=left.pos)
                continue
            break
        return left

    def _nud(self):
        t = self.next()
        if t is None:
            raise ValueError("unexpected end of input at position 0")
        kind, val = t[0], t[1]
        if kind == "num":
            return Num(val, pos=self.i)
        if kind == "str":
            return Str(val, pos=self.i)
        if kind == "ident":
            return Name(val, pos=self.i)
        if kind == "kw" and val in ("true", "false", "none"):
            return Const({"true": True, "false": False, "none": None}[val],
                         pos=self.i)
        if kind == "op" and val == "(":
            node = self.expr(0)
            self.expect_op(")")
            return node
        if kind == "op" and val == "-":
            return UnaryOp("-", self.expr(70), pos=self.i)
        if kind == "kw" and val == "not":
            return UnaryOp("not", self.expr(30), pos=self.i)
        raise ValueError(f"unexpected token {val!r} at token position {self.i}")


def parse(tokens):
    return _Parser(tokens).parse()
