import csv
from collections import defaultdict
import re

def load_talent_multipliers(path="data/talent_multipliers.csv"):
    multipliers = defaultdict(
        lambda: defaultdict(
            lambda: defaultdict(dict)
        )
    )

    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            char = row["character"]
            skill = row["skill"]       # e.g., AA, Skill, Burst
            level = int(row["level"])  # e.g., 1 to 15
            hit_type = row["type"]     # e.g., N1, N2, C, etc.

            # Combine hits if needed (e.g., "59.36 + 62.8")
            raw_val = row["multiplier"]
            value = sum(float(part.strip()) for part in raw_val.split("+"))

            multipliers[char][skill][level][hit_type] = value

    return multipliers

def compute_combo_multiplier(multipliers, character, skill, level, combo: str):
    """
    Supports patterns like 'N1C', 'N1N2C', '12N1C', '3N2N3C'
    Where a number prefix repeats the combo that follows.
    """
    # Match optional repetition prefix (e.g., 12 in 12N1C)
    match = re.match(r"^(\d+)?([A-Z0-9]+)$", combo)
    if not match:
        raise ValueError(f"Invalid combo format: {combo}")

    repeat = int(match.group(1)) if match.group(1) else 1
    sequence = match.group(2)

    # Break sequence into 2-character units like N1, C
    hits = []
    i = 0
    while i < len(sequence):
        if sequence[i] == 'C':  # 'C' is always single
            hits.append('C')
            i += 1
        else:
            hits.append(sequence[i:i + 2])  # e.g., 'N1', 'N2'
            i += 2

    # Calculate total
    total = 0.0
    for _ in range(repeat):
        for hit in hits:
            val = multipliers[character][skill][level].get(hit, 0)
            total += val
    return total

