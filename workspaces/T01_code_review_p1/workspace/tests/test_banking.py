"""
Tests for T01_code_review — Race Condition Bug.

These tests verify:
1. That the *buggy* account loses money under concurrent access.
2. That the *fixed* account preserves correctness under concurrent load.
3. That basic sequential operations work in both versions.
"""

import threading
import pytest

from banking import UnsafeBankAccount
from banking_fixed import SafeBankAccount, CasBankAccount


# ====================================================================
# 1 — Bug reproduction tests
# ====================================================================

class TestUnsafeBankAccount:
    """Prove the race condition exists."""

    def test_sequential_operations_are_correct(self):
        """In a single-threaded context the buggy account works fine."""
        acc = UnsafeBankAccount(100.0)
        acc.deposit(50)
        acc.withdraw(30)
        assert acc.balance == 120.0

    def test_concurrent_withdrawals_lose_money(self):
        """10 concurrent €10 withdrawals from €100 — the race causes lost
        updates, so the final balance is > €0 when it should be €0."""
        acc = UnsafeBankAccount(100.0)
        n_threads = 10
        amount = 10

        threads = [
            threading.Thread(target=acc.withdraw, args=(amount,))
            for _ in range(n_threads)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # The race means NOT all withdrawals are applied.
        assert acc.balance > 0, (
            f"Expected a positive balance due to lost updates, "
            f"got {acc.balance}"
        )

    def test_concurrent_deposits_lose_money(self):
        """10 concurrent €10 deposits from €0 — same race, lost updates."""
        acc = UnsafeBankAccount(0.0)
        n_threads = 10
        amount = 10

        threads = [
            threading.Thread(target=acc.deposit, args=(amount,))
            for _ in range(n_threads)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Expected: €100, actual: < €100 (lost updates).
        assert acc.balance < 100.0, (
            f"Expected balance < 100 due to race, got {acc.balance}"
        )

    def test_race_is_reproducible(self):
        """Run the race demo 5 times — at least 3 should show the bug."""
        race_count = 0
        for _ in range(5):
            acc = UnsafeBankAccount(100.0)
            threads = [
                threading.Thread(target=acc.withdraw, args=(10,))
                for _ in range(10)
            ]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            if acc.balance > 0:
                race_count += 1

        assert race_count >= 3, (
            f"Race should trigger in most runs, triggered in {race_count}/5"
        )


# ====================================================================
# 2 — Fix verification tests (Lock-based)
# ====================================================================

class TestSafeBankAccount:
    """Prove the lock-based fix is thread-safe."""

    def test_sequential_are_correct(self):
        """Single-threaded operations still work."""
        acc = SafeBankAccount(100.0)
        acc.deposit(50)
        acc.withdraw(30)
        assert acc.balance == 120.0

    def test_concurrent_withdrawals_preserve_every_cent(self):
        """10 concurrent €10 withdrawals from €100 → exactly €0."""
        acc = SafeBankAccount(100.0)
        n_threads = 10
        amount = 10
        errors = []

        def safe_withdraw():
            try:
                acc.withdraw(amount)
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

        assert acc.balance == 0.0, f"Expected €0, got €{acc.balance}"
        # Exactly one of the 10 threads should have triggered
        # "Insufficient funds" if all 10 succeeded on the first 9.
        # (Depends on scheduling — at least 0, at most 9 errors.)
        assert len(errors) <= 9

    def test_concurrent_deposits_preserve_every_cent(self):
        """10 concurrent €10 deposits from €0 → exactly €100."""
        acc = SafeBankAccount(0.0)
        n_threads = 10
        amount = 10

        threads = [
            threading.Thread(target=acc.deposit, args=(amount,))
            for _ in range(n_threads)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert acc.balance == 100.0, f"Expected €100, got €{acc.balance}"

    def test_high_contention(self):
        """50 threads hammering deposit+withdraw in a cycle should end at 0."""
        acc = SafeBankAccount(0.0)
        n_threads = 50
        barrier = threading.Barrier(n_threads)

        def race():
            barrier.wait()  # all threads start simultaneously
            for _ in range(20):
                acc.deposit(10)
                acc.withdraw(10)

        threads = [threading.Thread(target=race) for _ in range(n_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert acc.balance == 0.0, (
            f"High-contention balance drift: €{acc.balance}"
        )

    def test_transfer_atomicity(self):
        """Transfer between two accounts preserves total sum."""
        a = SafeBankAccount(100.0)
        b = SafeBankAccount(50.0)
        n_threads = 20

        threads = [
            threading.Thread(target=a.transfer, args=(b, 5))
            for _ in range(n_threads)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        total = a.balance + b.balance
        assert total == 150.0, (
            f"Transfer race lost money: total €{total}, expected €150"
        )

    def test_negative_withdrawal_raises(self):
        """Withdrawing more than the balance still raises ValueError."""
        acc = SafeBankAccount(50.0)
        with pytest.raises(ValueError, match="Insufficient funds"):
            acc.withdraw(100)


# ====================================================================
# 3 — CAS-based fix verification
# ====================================================================

class TestCasBankAccount:
    """Prove the CAS-based (retry-loop) fix is also correct."""

    def test_sequential_correct(self):
        acc = CasBankAccount(100.0)
        acc.deposit(50)
        acc.withdraw(30)
        assert acc.balance == 120.0

    def test_cas_handles_concurrent_deposits(self):
        acc = CasBankAccount(0.0)
        n = 20
        threads = [
            threading.Thread(target=acc.deposit, args=(10,))
            for _ in range(n)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert acc.balance == 200.0, f"Expected €200, got €{acc.balance}"

    def test_cas_withdraw_raises_on_insufficient(self):
        acc = CasBankAccount(10.0)
        with pytest.raises(ValueError, match="Insufficient"):
            acc.withdraw(100)
