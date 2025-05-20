import random

def generate_artifact_main_stat(artifact_type):
    if artifact_type == "Sands":
        stats = {
            'HP%': 26.68,
            'ATK%': 26.66,
            'DEF%': 26.66,
            'Energy Recharge%': 10.00,
            'Elemental Mastery': 10.00
        }
    elif artifact_type == "Goblet":
        stats = {
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
        stats = {
            'HP%': 19.25,
            'ATK%': 19.25,
            'DEF%': 19,
            'Crit Rate%': 10,
            'Crit DMG': 10,
            'Healing Bonus%': 10,
            'Elemental Mastery': 4
        }
    else:
        raise ValueError("Unsupported artifact type")

    return random.choices(
        population=list(stats.keys()),
        weights=list(stats.values()),
        k=1
    )[0]

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

    substats = random.choices(
        population=list(weights.keys()),
        weights=list(weights.values()),
        k=4
    )
    return substats

def simulate_artifact_rolls(substats):
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
    for sub in substats:
        value = random.choice(value_ranges.get(sub, [0]))
        rolls[sub] = value

    for _ in range(5):  # 5 upgrades from +4 to +20
        stat = random.choice(substats)
        rolls[stat] += random.choice(value_ranges.get(stat, [0]))

    return rolls

def simulate_artifact(artifact_type="Sands"):
    main_stat = generate_artifact_main_stat(artifact_type)
    substats = generate_substats(exclude_stat=main_stat)
    rolls = simulate_artifact_rolls(substats)

    return {
        "type": artifact_type,
        "main_stat": main_stat,
        "substats": rolls
    }
