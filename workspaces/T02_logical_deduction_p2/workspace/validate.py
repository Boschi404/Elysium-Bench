"""
Validation script for T02: Zebra Puzzle (Einstein's Riddle)
Verifies the solution satisfies all 15 clues programmatically.
"""

import json

# The solution: 5 houses indexed 0-4 (left to right)
solution = {
    "houses": [
        {"color": "Yellow", "nationality": "Norwegian", "drink": "Water",
         "cigarette": "Dunhill", "pet": "Cats"},
        {"color": "Blue", "nationality": "Dane", "drink": "Tea",
         "cigarette": "Blends", "pet": "Horses"},
        {"color": "Red", "nationality": "English", "drink": "Milk",
         "cigarette": "Pall Mall", "pet": "Birds"},
        {"color": "Green", "nationality": "German", "drink": "Coffee",
         "cigarette": "Prince", "pet": "Zebra"},
        {"color": "White", "nationality": "Swede", "drink": "Beer",
         "cigarette": "Blue Master", "pet": "Dogs"},
    ]
}


def get_index(key, value):
    """Find house index where attribute matches."""
    for i, h in enumerate(solution["houses"]):
        if h[key] == value:
            return i
    return -1


def check(label, condition, detail=""):
    """Check a single clue and print result."""
    status = "✅ PASS" if condition else "❌ FAIL"
    print(f"  {status} | {label}" + (f" | {detail}" if detail else ""))
    return condition


def validate_all():
    clues = solution["houses"]
    all_pass = True

    print("=" * 72)
    print("  ZEBRA PUZZLE — SOLUTION VALIDATION")
    print("=" * 72)

    # --- Uniqueness checks ---
    print("\n--- Category Uniqueness ---")
    for category in ["color", "nationality", "drink", "cigarette", "pet"]:
        values = [h[category] for h in clues]
        unique = len(values) == len(set(values))
        all_pass &= check(f"All 5 {category}s are unique", unique,
                          f"got {values}")

    # --- Clue-by-clue ---
    print("\n--- Clue Verification ---")

    # Clue 1: Norwegian in first house
    n1 = clues[0]["nationality"] == "Norwegian"
    all_pass &= check("Clue 1: Norwegian in first house", n1,
                      f"House 1 = {clues[0]['nationality']}")

    # Clue 2: Englishman in red house
    eng_idx = get_index("nationality", "English")
    red_idx = get_index("color", "Red")
    c2 = eng_idx == red_idx and eng_idx >= 0
    all_pass &= check("Clue 2: Englishman in red house", c2,
                      f"English at H{eng_idx+1}, Red at H{red_idx+1}")

    # Clue 3: Green left of White (immediately)
    green_idx = get_index("color", "Green")
    white_idx = get_index("color", "White")
    c3 = white_idx - green_idx == 1
    all_pass &= check("Clue 3: Green left of White", c3,
                      f"Green at H{green_idx+1}, White at H{white_idx+1}")

    # Clue 4: Dane drinks tea
    dane_idx = get_index("nationality", "Dane")
    tea_idx = get_index("drink", "Tea")
    c4 = dane_idx == tea_idx and dane_idx >= 0
    all_pass &= check("Clue 4: Dane drinks tea", c4,
                      f"Dane at H{dane_idx+1}, Tea at H{tea_idx+1}")

    # Clue 5: Pall Mall smoker keeps birds
    pm_idx = get_index("cigarette", "Pall Mall")
    birds_idx = get_index("pet", "Birds")
    c5 = pm_idx == birds_idx and pm_idx >= 0
    all_pass &= check("Clue 5: Pall Mall = Birds", c5,
                      f"Pall Mall at H{pm_idx+1}, Birds at H{birds_idx+1}")

    # Clue 6: Yellow house smokes Dunhill
    yellow_idx = get_index("color", "Yellow")
    dunhill_idx = get_index("cigarette", "Dunhill")
    c6 = yellow_idx == dunhill_idx and yellow_idx >= 0
    all_pass &= check("Clue 6: Yellow = Dunhill", c6,
                      f"Yellow at H{yellow_idx+1}, Dunhill at H{dunhill_idx+1}")

    # Clue 7: Center house drinks milk
    c7 = clues[2]["drink"] == "Milk"
    all_pass &= check("Clue 7: Center drinks milk", c7,
                      f"House 3 = {clues[2]['drink']}")

    # Clue 8: Blends next to Cats
    blends_idx = get_index("cigarette", "Blends")
    cats_idx = get_index("pet", "Cats")
    c8 = abs(blends_idx - cats_idx) == 1
    all_pass &= check("Clue 8: Blends next to Cats", c8,
                      f"Blends at H{blends_idx+1}, Cats at H{cats_idx+1}")

    # Clue 9: German smokes Prince
    german_idx = get_index("nationality", "German")
    prince_idx = get_index("cigarette", "Prince")
    c9 = german_idx == prince_idx and german_idx >= 0
    all_pass &= check("Clue 9: German smokes Prince", c9,
                      f"German at H{german_idx+1}, Prince at H{prince_idx+1}")

    # Clue 10: Blue Master = Beer
    bm_idx = get_index("cigarette", "Blue Master")
    beer_idx = get_index("drink", "Beer")
    c10 = bm_idx == beer_idx and bm_idx >= 0
    all_pass &= check("Clue 10: Blue Master = Beer", c10,
                      f"Blue Master at H{bm_idx+1}, Beer at H{beer_idx+1}")

    # Clue 11: Norwegian next to Blue
    nor_idx = get_index("nationality", "Norwegian")
    blue_idx = get_index("color", "Blue")
    c11 = abs(nor_idx - blue_idx) == 1
    all_pass &= check("Clue 11: Norwegian next to Blue", c11,
                      f"Norwegian at H{nor_idx+1}, Blue at H{blue_idx+1}")

    # Clue 12: Horses next to Dunhill
    horses_idx = get_index("pet", "Horses")
    dunhill_idx2 = get_index("cigarette", "Dunhill")
    c12 = abs(horses_idx - dunhill_idx2) == 1
    all_pass &= check("Clue 12: Horses next to Dunhill", c12,
                      f"Horses at H{horses_idx+1}, Dunhill at H{dunhill_idx2+1}")

    # Clue 13: Blends neighbor drinks Water
    blends_idx2 = get_index("cigarette", "Blends")
    water_idx = get_index("drink", "Water")
    c13 = abs(blends_idx2 - water_idx) == 1
    all_pass &= check("Clue 13: Blends neighbor = Water", c13,
                      f"Blends at H{blends_idx2+1}, Water at H{water_idx+1}")

    # Clue 14: Swede keeps dogs
    swede_idx = get_index("nationality", "Swede")
    dogs_idx = get_index("pet", "Dogs")
    c14 = swede_idx == dogs_idx and swede_idx >= 0
    all_pass &= check("Clue 14: Swede keeps dogs", c14,
                      f"Swede at H{swede_idx+1}, Dogs at H{dogs_idx+1}")

    # Clue 15: Green house drinks coffee
    green_idx2 = get_index("color", "Green")
    coffee_idx = get_index("drink", "Coffee")
    c15 = green_idx2 == coffee_idx and green_idx2 >= 0
    all_pass &= check("Clue 15: Green drinks coffee", c15,
                      f"Green at H{green_idx2+1}, Coffee at H{coffee_idx+1}")

    # --- Final answer check ---
    print("\n--- Final Answer ---")
    zebra_idx = get_index("pet", "Zebra")
    owner = clues[zebra_idx]["nationality"]
    print(f"  The {owner} owns the zebra (House {zebra_idx+1})")

    # Summary
    print("\n--- Summary ---")
    print(f"  All clues satisfied: {'✅ YES' if all_pass else '❌ NO (see failures above)'}")

    # Print final grid
    print("\n--- Final Grid ---")
    print(f"  {'House':<7} {'Color':<8} {'Nationality':<12} {'Drink':<8} {'Cigarette':<12} {'Pet':<8}")
    print(f"  {'-'*55}")
    for i, h in enumerate(clues):
        print(f"  {i+1:<7} {h['color']:<8} {h['nationality']:<12} "
              f"{h['drink']:<8} {h['cigarette']:<12} {h['pet']:<8}")

    return all_pass


if __name__ == "__main__":
    import sys
    result = validate_all()
    sys.exit(0 if result else 1)
