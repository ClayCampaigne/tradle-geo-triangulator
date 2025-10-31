#!/usr/bin/env python3
"""Quick local test of the tradle_guesser module."""

from tradle_guesser import load_country_data, best_guesses

print("Testing tradle_guesser module...")
print("\n1. Loading country data...")

try:
    centroid_list, distance_df = load_country_data()
    print(f"✓ Successfully loaded {len(centroid_list)} countries")
    print(f"\nFirst 5 countries:")
    print(centroid_list.head())

    print(f"\n2. Testing best_guesses function...")
    result = best_guesses(
        [("Thailand", 7705, 'NW'), ("Eritrea", 4985)],
        centroid_list,
        distance_df
    )
    print(f"✓ Successfully computed guesses")
    print(f"\nTop 5 candidates:")
    print(result.head())

    print("\n✓ All tests passed!")

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
