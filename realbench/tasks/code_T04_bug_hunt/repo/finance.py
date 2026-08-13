"""finance.py — contains ONE planted bug (compound interest formula)."""
def compound_interest(principal, rate, years):
    if principal < 0 or rate < 0 or years < 0:
        raise ValueError("negative inputs not allowed")
    return principal * (rate ** years)  # BUG: should be (1 + rate) ** years
