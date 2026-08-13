"""Reference: exact 0/1 knapsack via DP over capacity."""
def solve_knapsack(values: list[int], weights: list[int], capacity: int) -> int:
    dp = [0] * (capacity + 1)
    for v, w in zip(values, weights):
        for c in range(capacity, w - 1, -1):
            cand = dp[c - w] + v
            if cand > dp[c]:
                dp[c] = cand
    return dp[capacity]
