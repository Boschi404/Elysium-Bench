"""
banking_fixed.py — Thread-safe banking account using a mutex lock.

Fixes the TOCTOU race by wrapping every read-modify-write cycle in
a threading.Lock so that the critical section is atomic.
"""

import threading
import time


class SafeBankAccount:
    """A thread-safe bank account using a single mutex.

    Every public mutating method acquires ``self._lock`` before
    reading or writing ``_balance``, guaranteeing that no other
    thread can interleave in the middle of a deposit/withdraw.
    """

    def __init__(self, initial_balance: float = 0.0):
        self._balance = initial_balance
        self._lock = threading.Lock()

    # ── public helpers ──────────────────────────────────────────────

    @property
    def balance(self) -> float:
        """Return the current balance — safe to read without the lock
        because Python guarantees atomic reads/writes for simple
        attributes on CPython (GIL), but we use the lock anyway for
        correctness on other implementations (Jython, IronPython)."""
        with self._lock:
            return self._balance

    # ── thread-safe operations ──────────────────────────────────────

    def deposit(self, amount: float) -> None:
        """Add *amount* to the balance.  Thread-safe via lock."""
        with self._lock:
            current = self._balance
            time.sleep(0.001)  # same delay as buggy version for fair comparison
            self._balance = current + amount

    def withdraw(self, amount: float) -> None:
        """Subtract *amount* from the balance.  Thread-safe via lock."""
        with self._lock:
            if self._balance < amount:
                raise ValueError("Insufficient funds")
            current = self._balance
            time.sleep(0.001)
            self._balance = current - amount

    def transfer(self, target: "SafeBankAccount", amount: float) -> None:
        """Transfer *amount* to *target*.  Avoids deadlock by locking
        consistently (always lock self, then target)."""
        # Lock in a fixed order to prevent deadlock.
        first = self if id(self) < id(target) else target
        second = target if first is self else self
        with first._lock:
            with second._lock:
                if self._balance < amount:
                    raise ValueError("Insufficient funds")
                self._balance -= amount
                target._balance += amount

    def __repr__(self) -> str:
        return f"SafeBankAccount(balance={self._balance})"


# ── Alternative: atomic compare-and-swap approach ──────────────────

class CasBankAccount:
    """A thread-safe bank account using compare-and-swap semantics.

    Instead of a mutex, this version relies on the GIL to make
    attribute assignment atomic, and uses a retry loop to detect
    concurrent modifications.  This is the pattern behind
    ``queue.Queue`` and many lock-free data structures.

    While this works under CPython's GIL, the Lock-based approach
    (SafeBankAccount) is the recommended production pattern because
    it is explicit, portable, and easier to reason about.
    """

    def __init__(self, initial_balance: float = 0.0):
        self._balance = initial_balance
        self._lock = threading.Lock()  # only used for CAS, never held across RMW

    @property
    def balance(self) -> float:
        with self._lock:
            return self._balance

    # NOTE: Pure CAS without a lock would require an atomic hardware
    # instruction (e.g. cmpxchg on x86) or a Python C extension.
    # This example keeps the lock for the CAS check itself, but the
    # *window* is as small as possible — just the comparison + swap,
    # not the whole business logic.
    def _cas(self, expected: float, new: float) -> bool:
        """Compare-and-swap: set _balance = new iff _balance == expected."""
        with self._lock:
            if self._balance == expected:
                self._balance = new
                return True
            return False

    def deposit(self, amount: float) -> None:
        while True:
            current = self._balance
            time.sleep(0.001)
            if self._cas(current, current + amount):
                return

    def withdraw(self, amount: float) -> None:
        while True:
            current = self._balance
            if current < amount:
                raise ValueError("Insufficient funds")
            time.sleep(0.001)
            if self._cas(current, current - amount):
                return


# ── Demonstrate that the fixed version works correctly ─────────────

def demonstrate_fixed() -> dict:
    """Run 10 concurrent withdrawals of €10 from a €100 account.

    With the lock in place all 10 withdrawals are accounted for and
    the final balance is exactly €0.
    """
    account = SafeBankAccount(initial_balance=100.0)
    n_threads = 10
    amount = 10

    errors = []
    def safe_withdraw():
        try:
            account.withdraw(amount)
        except ValueError as e:
            errors.append(str(e))

    threads = [
        threading.Thread(target=safe_withdraw)
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
        "errors": errors,
        "consistent": account.balance == 0.0,
    }


if __name__ == "__main__":
    result = demonstrate_fixed()
    print(f"Initial:   €{result['initial']:.2f}")
    print(f"Expected:  €{result['expected']:.2f}")
    print(f"Actual:    €{result['actual']:.2f}")
    print(f"Errors:    {len(result['errors'])}")
    print(f"Consistent? {'✅  YES' if result['consistent'] else '⚠️  NO'}")
