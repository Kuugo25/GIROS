# core/defaults.py
import csv

def load_default_combos(filepath="data/character_defaults.csv"):
    """
    Loads default attack combo and skill for each character from CSV.

    Returns:
        dict: {
            "Hu Tao": {"combo": "E12N1C", "skill": "AA"},
            ...
        }
    """
    defaults = {}
    with open(filepath, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            char = row["character"]
            defaults[char] = {
                "combo": row["default_combo"],
                "skill": row["default_skill"]
            }
    return defaults


