"""textutil.py — fixed reference."""
import re


def slugify(text):
    words = re.findall(r"\w+", text.lower())
    return "-".join(words)
