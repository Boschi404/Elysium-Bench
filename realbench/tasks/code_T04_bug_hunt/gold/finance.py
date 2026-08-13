"""finance.py — fixed reference."""
def compound_interest(principal, rate, years):
    if principal < 0 or rate < 0 or years < 0:
        raise ValueError("negative inputs not allowed")
    return principal * ((1 + rate) ** years)
