#!/usr/bin/env python3
"""
T01: Knights and Knaves Puzzle — Programmatic Verification

Knights always tell the truth.
Knaves always lie.

A says: "B is a Knave."
B says: "We are both Knights."
"""

from typing import Literal

Person = Literal["Knight", "Knave"]


def knight(statement: bool) -> bool:
    """A Knight's statement must be true."""
    return statement is True


def knave(statement: bool) -> bool:
    """A Knave's statement must be false."""
    return statement is False


def is_knave(person: Person) -> bool:
    return person == "Knave"


def is_knight(person: Person) -> bool:
    return person == "Knight"


def solve() -> list[tuple[Person, Person, str]]:
    """Try all 4 combinations and return consistent ones."""
    results = []

    for a_type in ("Knight", "Knave"):
        for b_type in ("Knight", "Knave"):
            # A says "B is a Knave"
            a_statement = is_knave(b_type)

            # B says "We are both Knights"
            b_statement = is_knight(a_type) and is_knight(b_type)

            # Check consistency
            a_consistent = (
                knight(a_statement) if a_type == "Knight" else knave(a_statement)
            )
            b_consistent = (
                knight(b_statement) if b_type == "Knight" else knave(b_statement)
            )

            if a_consistent and b_consistent:
                results.append((a_type, b_type, "consistent"))
            else:
                # Determine why it failed
                reason_parts = []
                if not a_consistent:
                    a_explanation = (
                        f"A={a_type} says 'B is Knave' = {a_statement}"
                        f" -> would be {'TRUE' if knight(a_statement) else 'FALSE'}"
                        f" for a {a_type}, contradiction"
                    )
                    reason_parts.append(a_explanation)
                if not b_consistent:
                    b_explanation = (
                        f"B={b_type} says 'Both Knights' = {b_statement}"
                        f" -> would be {'TRUE' if knight(b_statement) else 'FALSE'}"
                        f" for a {b_type}, contradiction"
                    )
                    reason_parts.append(b_explanation)
                results.append((a_type, b_type, "; ".join(reason_parts)))

    return results


def main():
    print("=" * 60)
    print("Knights and Knaves Puzzle — Solution Verification")
    print("=" * 60)
    print()

    results = solve()

    print("All 4 cases analysed:")
    print("-" * 60)
    for a, b, status in results:
        icon = "✅" if status == "consistent" else "❌"
        print(f"  A={a:<7} B={b:<7}  {icon} {status}")

    print()
    print("-" * 60)
    # Find the consistent solution
    consistent = [(a, b) for a, b, s in results if s == "consistent"]
    if len(consistent) == 1:
        a_type, b_type = consistent[0]
        print(f"✅ UNIQUE SOLUTION: A is {a_type}, B is {b_type}")
    elif len(consistent) > 1:
        print(f"⚠️  Multiple consistent solutions: {consistent}")
    else:
        print("❌ No consistent solution found")


if __name__ == "__main__":
    main()
