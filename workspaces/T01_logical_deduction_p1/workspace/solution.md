# T01: Knights and Knaves Puzzle — Logical Deduction

## Problem

On an island, Knights always tell the truth, Knaves always lie.

- **A says:** "B is a Knave."
- **B says:** "We are both Knights."

Determine the identity of A and B.

---

## Assumptions

- Knight ≡ always tells the truth
- Knave ≡ always lies
- Each person is either a Knight or a Knave (no third option)

---

## Case Analysis

### Case 1: A is a **Knight** (truth-teller)

| Step | Reasoning |
|------|-----------|
| A's statement "B is a Knave" must be **true** | (Knights tell truth) |
| Therefore **B is a Knave** | |
| B (a Knave) says "We are both Knights" | |
| This statement is **false** (A=Knight, B=Knave → not both Knights) | |
| A Knave **must lie** → false statement ✓ | **Consistent** |

**Result: A = Knight, B = Knave** ✅

### Case 2: A is a **Knave** (liar)

| Step | Reasoning |
|------|-----------|
| A's statement "B is a Knave" must be **false** | (Knaves lie) |
| Therefore B is **not a Knave** → **B is a Knight** | |
| B (a Knight) says "We are both Knights" | |
| This statement is **false** (A=Knave, B=Knight → not both Knights) | |
| A Knight **cannot lie** → contradiction | **❌ Inconsistent** |

**Result: Contradiction — discarded**

---

## Truth Table

| A | B | A says "B is Knave" | B says "Both Knights" | Consistent? |
|---|---|---------------------|-----------------------|-------------|
| Knight | Knave | True ✓ | False (Knave lies ✓) | **✅ Yes** |
| Knight | Knight | False ✗ (Knight can't lie) | True | ❌ No |
| Knave | Knight | False (Knave lies ✓) | False ✗ (Knight can't lie) | ❌ No |
| Knave | Knave | True ✗ (Knave can't tell truth) | False | ❌ No |

---

## ✅ Final Answer

| Person | Identity |
|--------|----------|
| **A** | **Knight** (truth-teller) |
| **B** | **Knave** (liar) |

- A truthfully says B is a Knave → ✓
- B falsely claims both are Knights → Knave lies → ✓
