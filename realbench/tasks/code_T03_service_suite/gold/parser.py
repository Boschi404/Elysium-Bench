"""Reference: parser.py"""
import re

_FIELD_RE = re.compile(r"(TS|TYPE|VAL)=(\S+)")


def parse_event(text: str) -> dict:
    if not isinstance(text, str) or not text.strip():
        raise ValueError("empty input")
    fields = {}
    for key, value in _FIELD_RE.findall(text):
        if key in fields:
            raise ValueError(f"duplicate field {key}")
        fields[key] = value
    for required in ("TS", "TYPE", "VAL"):
        if required not in fields:
            raise ValueError(f"missing field {required}")
    try:
        ts = int(fields["TS"])
    except ValueError:
        raise ValueError("TS is not an integer")
    try:
        val = float(fields["VAL"])
    except ValueError:
        raise ValueError("VAL is not numeric")
    return {"ts": ts, "type": fields["TYPE"], "val": val}
