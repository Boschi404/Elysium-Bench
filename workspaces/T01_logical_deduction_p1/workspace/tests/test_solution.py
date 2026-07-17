#!/usr/bin/env python3
"""Tests for the Knights and Knaves puzzle solver."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from solution import solve, is_knight, is_knave


def test_exactly_one_solution():
    """There must be exactly one consistent solution."""
    results = solve()
    consistent = [(a, b) for a, b, s in results if s == "consistent"]
    assert len(consistent) == 1, f"Expected 1 solution, got {len(consistent)}: {consistent}"
    # Store on module for reuse
    test_exactly_one_solution.solution = consistent[0]


def test_solution_a_knight_b_knave():
    """The unique solution must be A=Knight, B=Knave."""
    test_exactly_one_solution()
    a_type, b_type = test_exactly_one_solution.solution
    assert a_type == "Knight", f"A should be Knight, got {a_type}"
    assert b_type == "Knave", f"B should be Knave, got {b_type}"


def test_a_statement_true():
    """A says 'B is a Knave' — this must be true (A is Knight)."""
    assert is_knave("Knave") is True


def test_b_statement_false():
    """B says 'We are both Knights' — this must be false (B is Knave)."""
    both_knights = is_knight("Knight") and is_knight("Knave")
    assert both_knights is False


def test_inconsistent_cases_discarded():
    """Verify the 3 inconsistent cases are correctly rejected."""
    results = solve()
    inconsistent = [(a, b) for a, b, s in results if s != "consistent"]
    inconsistent_pairs = set(inconsistent)
    # Knight+Knight: A says B is Knave (false) — Knight can't lie
    assert ("Knight", "Knight") in inconsistent_pairs
    # Knave+Knight: B says both Knights (false) — Knight can't lie
    assert ("Knave", "Knight") in inconsistent_pairs
    # Knave+Knave: A says B is Knave (true) — Knave can't tell truth
    assert ("Knave", "Knave") in inconsistent_pairs
    assert len(inconsistent) == 3
