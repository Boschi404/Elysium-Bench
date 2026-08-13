"""Generate expected optimums for the knapsack hidden tests.

DP for all instances + brute-force cross-check on the tiny ones.
Run once:  python gen_optimums.py
"""
import json
import random
from itertools import combinations
from pathlib import Path


def make_instance(seed, n, wmax, cap):
    rng = random.Random(seed)
    values = [rng.randint(1, 100) for _ in range(n)]
    weights = [rng.randint(1, wmax) for _ in range(n)]
    return values, weights, cap


def dp_knapsack(values, weights, capacity):
    dp = [0] * (capacity + 1)
    for v, w in zip(values, weights):
        for c in range(capacity, w - 1, -1):
            if dp[c - w] + v > dp[c]:
                dp[c] = dp[c - w] + v
    return dp[capacity]


def brute_knapsack(values, weights, capacity):
    best = 0
    n = len(values)
    for mask in range(1 << n):
        total_w = sum(weights[i] for i in range(n) if mask & (1 << i))
        if total_w <= capacity:
            total_v = sum(values[i] for i in range(n) if mask & (1 << i))
            best = max(best, total_v)
    return best


INSTANCES = {
    "tiny1": make_instance(101, 8, 5, 10),
    "tiny2": make_instance(202, 10, 6, 15),
    "tiny_all": make_instance(303, 5, 3, 1000),
    "medium1": make_instance(404, 50, 20, 200),
    "medium2": make_instance(505, 100, 25, 500),
    "large1": make_instance(606, 200, 100, 5000),
    "large2": make_instance(707, 300, 150, 8000),
}

expected = {}
for name, (v, w, cap) in INSTANCES.items():
    opt = dp_knapsack(v, w, cap)
    if name.startswith("tiny"):
        brute = brute_knapsack(v, w, cap)
        assert brute == opt, f"{name}: DP {opt} != brute {brute}"
        print(f"{name}: DP={opt} brute={brute} OK")
    else:
        print(f"{name}: DP={opt}")
    expected[name] = opt

out = Path(__file__).parent.parent / "tests" / "expected_optimums.json"
out.write_text(json.dumps(expected, indent=2))
print(f"written: {out}")
