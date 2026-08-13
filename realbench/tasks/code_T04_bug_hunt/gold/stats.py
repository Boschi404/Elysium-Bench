"""stats.py — fixed reference."""
def mean(values):
    if not values:
        raise ValueError("empty input")
    return sum(values) / len(values)


def median(values):
    if not values:
        raise ValueError("empty input")
    s = sorted(values)
    n = len(s)
    if n % 2 == 1:
        return s[n // 2]
    return (s[n // 2 - 1] + s[n // 2]) / 2


def stddev(values):
    if len(values) < 2:
        raise ValueError("need at least 2 values")
    m = mean(values)
    return (sum((x - m) ** 2 for x in values) / (len(values) - 1)) ** 0.5
