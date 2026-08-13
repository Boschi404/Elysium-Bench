"""textutil.py — contains ONE planted bug (slugify drops the last word)."""
import re


def slugify(text):
    words = re.findall(r"\w+", text.lower())
    if not words:
        return ""
    return "-".join(words[:-1])  # BUG: drops the last word
