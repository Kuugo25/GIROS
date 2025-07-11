# simulation/artifact.py
import random

MAIN_STAT_VALUES_5_STAR = {
    'Flat HP': 4780,
    'Flat ATK': 311,
    'HP%': 46.6,
    'ATK%': 46.6,
    'DEF%': 58.3,
    'Elemental Mastery': 186.5,
    'Energy Recharge%': 51.8,
    'CRIT Rate%': 31.1,
    'CRIT DMG%': 62.2,
    'Healing Bonus%': 35.9,
    'Physical DMG Bonus%': 58.3,
    'Pyro DMG Bonus%': 46.6,
    'Hydro DMG Bonus%': 46.6,
    'Electro DMG Bonus%': 46.6,
    'Cryo DMG Bonus%': 46.6,
    'Geo DMG Bonus%': 46.6,
    'Anemo DMG Bonus%': 46.6,
    'Dendro DMG Bonus%': 46.6
}

# Same as your code
def generate_artifact_main_stat(artifact_type):
    if artifact_type == "Flower":
        return "Flat HP", MAIN_STAT_VALUES_5_STAR["Flat HP"]
    elif artifact_type == "Feather":
        return "Flat ATK", MAIN_STAT_VALUES_5_STAR["Flat ATK"]
    elif artifact_type == "Sands":
        weights = {
            'HP%': 26.68,
            'ATK%': 26.66,
            'DEF%': 26.66,
            'Energy Recharge%': 10.00,
            'Elemental Mastery': 10.00
        }
    elif artifact_type == "Goblet":
        weights = {
            'HP%': 19.25,
            'ATK%': 19.25,
            'DEF%': 19,
            'Pyro DMG Bonus%': 5,
            'Electro DMG Bonus%': 5,
            'Cryo DMG Bonus%': 5,
            'Hydro DMG Bonus%': 5,
            'Dendro DMG Bonus%': 5,
            'Anemo DMG Bonus%': 5,
            'Geo DMG Bonus%': 5,
            'Physical DMG Bonus%': 5,
            'Elemental Mastery': 2.5
        }
    elif artifact_type == "Circlet":
        weights = {
            'HP%': 19.25,
            'ATK%': 19.25,
            'DEF%': 19,
            'CRIT Rate%': 10,
            'CRIT DMG%': 10,
            'Healing Bonus%': 10,
            'Elemental Mastery': 4
        }
    else:
        raise ValueError("Unsupported artifact type")

    main_stat = random.choices(list(weights.keys()), weights=list(weights.values()), k=1)[0]
    return main_stat, MAIN_STAT_VALUES_5_STAR[main_stat]

def generate_substats(exclude_stat=None):
    weights = {
        'Flat HP': 6,
        'Flat ATK': 6,
        'Flat DEF': 6,
        'HP%': 4,
        'ATK%': 4,
        'DEF%': 4,
        'Energy Recharge%': 4,
        'Elemental Mastery': 4,
        'CRIT Rate%': 3,
        'CRIT DMG%': 3
    }

    if exclude_stat in weights:
        weights.pop(exclude_stat)

    substats = random.sample(list(weights.keys()), k=4)
    return substats

def simulate_artifact_rolls(substats, num_upgrades):
    value_ranges = {
        'Flat HP': [209.13, 239, 268.88, 298.75],
        'Flat ATK': [13.62, 15.56, 17.51, 19.45],
        'Flat DEF': [16.2, 18.52, 20.83, 23.15],
        'HP%': [4.08, 4.66, 5.25, 5.83],
        'ATK%': [4.08, 4.66, 5.25, 5.83],
        'DEF%': [5.10, 5.83, 6.56, 7.29],
        'Elemental Mastery': [16.32, 18.65, 20.98, 23.31],
        'Energy Recharge%': [4.53, 5.18, 5.83, 6.48],
        'CRIT Rate%': [2.72, 3.11, 3.50, 3.89],
        'CRIT DMG%': [5.44, 6.22, 6.99, 7.77],
    }

    rolls = {}
    upgrades = {}
    for stat in substats:
        initial = random.choice(value_ranges[stat])
        rolls[stat] = initial
        upgrades[stat] = 0  # no upgrades yet

    for _ in range(num_upgrades):
        stat = random.choice(substats)
        rolls[stat] += random.choice(value_ranges[stat])
        upgrades[stat] += 1

    return rolls, upgrades

def simulate_artifact(artifact_type="Sands"):
    main_stat_name, main_stat_value = generate_artifact_main_stat(artifact_type)
    starts_with_3 = random.random() < 0.8

    all_substats = generate_substats(exclude_stat=main_stat_name)
    base_substats = all_substats[:3] if starts_with_3 else all_substats[:4]

    # Initialize rolls and upgrade counters
    value_ranges = {
        'Flat HP': [209.13, 239, 268.88, 298.75],
        'Flat ATK': [13.62, 15.56, 17.51, 19.45],
        'Flat DEF': [16.2, 18.52, 20.83, 23.15],
        'HP%': [4.08, 4.66, 5.25, 5.83],
        'ATK%': [4.08, 4.66, 5.25, 5.83],
        'DEF%': [5.10, 5.83, 6.56, 7.29],
        'Elemental Mastery': [16.32, 18.65, 20.98, 23.31],
        'Energy Recharge%': [4.53, 5.18, 5.83, 6.48],
        'CRIT Rate%': [2.72, 3.11, 3.50, 3.89],
        'CRIT DMG%': [5.44, 6.22, 6.99, 7.77],
    }

    rolls = {}
    upgrades = {}
    for stat in base_substats:
        rolls[stat] = random.choice(value_ranges[stat])
        upgrades[stat] = 0

    if starts_with_3:
        # First upgrade at +4: add new stat
        new_stat = all_substats[3]
        rolls[new_stat] = random.choice(value_ranges[new_stat])
        upgrades[new_stat] = 0
        upgrade_candidates = base_substats + [new_stat]
        remaining_upgrades = 4
    else:
        upgrade_candidates = base_substats
        remaining_upgrades = 5

    for _ in range(remaining_upgrades):
        stat = random.choice(upgrade_candidates)
        rolls[stat] += random.choice(value_ranges[stat])
        upgrades[stat] += 1

    return {
        "type": artifact_type,
        "main_stat": main_stat_name,
        "main_stat_value": main_stat_value,
        "substats": dict(rolls),
        "upgrades": upgrades
    }
