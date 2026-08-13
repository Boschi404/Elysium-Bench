"""Reference: eval.py — lex + parse + evaluate."""
from lexer import tokenize
from parser import parse
from parser import (Num, Str, Name, Const, BinOp, UnaryOp, BoolOp,
                    Compare, Call)

_BUILTINS = {"len", "abs", "int", "str", "min", "max"}


def _truthy(v):
    return not (v is None or v is False or v == 0 or v == "")


def _eval(node, env):
    if isinstance(node, Num) or isinstance(node, Str):
        return node.value
    if isinstance(node, Const):
        return node.value
    if isinstance(node, Name):
        if node.name not in env:
            raise NameError(f"undefined name '{node.name}'")
        return env[node.name]
    if isinstance(node, UnaryOp):
        v = _eval(node.operand, env)
        if node.op == "not":
            return not _truthy(v)
        if node.op == "-":
            if not isinstance(v, (int, float)) or isinstance(v, bool):
                raise TypeError("unary - requires a number")
            return -v
    if isinstance(node, BinOp):
        l, r = _eval(node.left, env), _eval(node.right, env)
        op = node.op
        if op == "+":
            if isinstance(l, str) and isinstance(r, str):
                return l + r
            if isinstance(l, (int, float)) and isinstance(r, (int, float)) \
                    and not isinstance(l, bool) and not isinstance(r, bool):
                return l + r
            raise TypeError("+ requires two numbers or two strings")
        if op == "-" or op == "*" or op == "/" or op == "%":
            if not (isinstance(l, (int, float)) and isinstance(r, (int, float))
                    and not isinstance(l, bool) and not isinstance(r, bool)):
                raise TypeError(f"{op} requires numbers")
            if op == "-":
                return l - r
            if op == "*":
                return l * r
            if op == "/":
                if r == 0:
                    raise ZeroDivisionError("division by zero")
                return l / r
            if r == 0:
                raise ZeroDivisionError("modulo by zero")
            return l % r
    if isinstance(node, BoolOp):
        l = _eval(node.left, env)
        if node.op == "and":
            return _eval(node.right, env) if _truthy(l) else l
        return l if _truthy(l) else _eval(node.right, env)
    if isinstance(node, Compare):
        l = _eval(node.left, env)
        for op, comp in zip(node.ops, node.comparators):
            r = _eval(comp, env)
            if isinstance(l, (int, float)) and isinstance(r, (int, float)) \
                    and not isinstance(l, bool) and not isinstance(r, bool):
                ok = _num_cmp(l, r, op)
            elif isinstance(l, str) and isinstance(r, str):
                ok = _num_cmp(l, r, op)
            else:
                raise TypeError(f"cannot compare {type(l).__name__} with "
                                f"{type(r).__name__}")
            if not ok:
                return False
            l = r
        return True
    if isinstance(node, Call):
        if not isinstance(node.func, Name) or node.func.name not in _BUILTINS:
            raise NameError(f"unknown function '{getattr(node.func, 'name', '?')}'")
        args = [_eval(a, env) for a in node.args]
        return _call_builtin(node.func.name, args)
    raise ValueError(f"cannot evaluate {type(node).__name__}")


def _num_cmp(a, b, op):
    if op == "<":
        return a < b
    if op == "<=":
        return a <= b
    if op == ">":
        return a > b
    if op == ">=":
        return a >= b
    if op == "==":
        return a == b
    return a != b


def _call_builtin(name, args):
    if name == "len":
        if len(args) != 1 or not isinstance(args[0], str):
            raise TypeError("len() requires exactly one string argument")
        return len(args[0])
    if name == "abs":
        if len(args) != 1 or not isinstance(args[0], (int, float)) \
                or isinstance(args[0], bool):
            raise TypeError("abs() requires exactly one numeric argument")
        return abs(args[0])
    if name == "int":
        if len(args) != 1:
            raise TypeError("int() requires exactly one argument")
        v = args[0]
        if isinstance(v, bool):
            raise TypeError("int() argument must be a number or string")
        return int(v)
    if name == "str":
        if len(args) != 1:
            raise TypeError("str() requires exactly one argument")
        return str(args[0])
    if name in ("min", "max"):
        if not args:
            raise TypeError(f"{name}() requires at least one argument")
        all_num = all(isinstance(a, (int, float)) and not isinstance(a, bool)
                      for a in args)
        all_str = all(isinstance(a, str) for a in args)
        if not (all_num or all_str):
            raise TypeError(f"{name}() arguments must be all numbers or "
                            f"all strings")
        return (min(args) if name == "min" else max(args))
    raise NameError(f"unknown function '{name}'")


def eval_text(text: str, env: dict):
    tokens = tokenize(text)
    ast = parse(tokens)
    return _eval(ast, env)
