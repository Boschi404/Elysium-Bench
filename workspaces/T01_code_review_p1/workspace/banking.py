"""
banking.py — Banking account with a TOCTOU race condition.

The bug is the classic check-then-act (read-modify-write) pattern
without synchronization, between get_balance() and set_balance().
"""

import threading
import time


class UnsafeBankAccount:
    """A bank account with a deliberate race condition.

    The deposit() and withdraw() methods follow the dangerous pattern:

        balance = get_balance()   # READ
        balance += amount         # MODIFY
        set_balance(balance)      # WRITE

    When two threads interleave between the read and the write, one
    thread's update is silently lost — a classic TOCTOU (time-of-check
    to time-of-use) race.
    """

    def __init__(self, initial_balance: float = 0.0):
        self._balance = initial_balance

    # ── public helpers (used by both buggy and fixed versions) ──────

    @property
    def balance(self) -> float:
        """Return the current balance (thread-safe read via lock)."""
        return self.get_balance()

    def get_balance(self) -> float:
        """Read the current balance.  NOT protected — races with set."""
        return self._balance

    def set_balance(self, value: float) -> None:
        """Write the balance.  NOT protected — races with get."""
        self._balance = value

    # ── buggy operations ────────────────────────────────────────────

    def deposit(self, amount: float) -> None:
        """Add *amount* to the balance.  **RACY** — not thread-safe."""
        current = self.get_balance()
        # Artificial delay to make the race window wider (easier to
        # trigger in tests, represents real-world IO / network latency).
        time.sleep(0.001)
        self.set_balance(current + amount)

    def withdraw(self, amount: float) -> None:
        """Subtract *amount* from the balance.  **RACY** — not thread-safe."""
        if self.get_balance() < amount:
            raise ValueError("Insufficient funds")
        current = self.get_balance()
        # Same deliberate delay to expose the race.
        time.sleep(0.001)
        self.set_balance(current - amount)

    def transfer(self, target: "UnsafeBankAccount", amount: float) -> None:
        """Transfer *amount* to *target*.  **DOUBLY RACY** — two accounts."""
        self.withdraw(amount)
        target.deposit(amount)

    def __repr__(self) -> str:
        return f"UnsafeBankAccount(balance={self._balance})"


# ── Simulate concurrent withdrawals to reproduce the bug ───────────

def demonstrate_race() -> dict:
    """Run 10 concurrent withdrawals of €10 on a €100 account.

    If the race is NOT fixed, the final balance will be > €0 instead
    of the expected €0, because some withdrawals are silently lost.
    """
    account = UnsafeBankAccount(initial_balance=100.0)
    n_threads = 10
    amount = 10

    threads = [
        threading.Thread(target=account.withdraw, args=(amount,))
        for _ in range(n_threads)
    ]

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    return {
        "initial": 100.0,
        "expected": 0.0,
        "actual": account.balance,
        "lost": account.balance,  # any positive amount is lost money
        "race_detected": account.balance > 0,
    }


if __name__ == "__main__":
    result = demonstrate_race()
    print(f"Initial:   €{result['initial']:.2f}")
    print(f"Expected:  €{result['expected']:.2f}")
    print(f"Actual:    €{result['actual']:.2f}")
    print(f"Lost:      €{result['lost']:.2f}")
    print(f"Race?      {'⚠️  YES' if result['race_detected'] else '✅  NO'}")
