from simulation.artifact import simulate_artifact
from simulation.talent_books import simulate_multiple_talent_runs
import copy

def simulate_artifact_farm(character, resin_spent=20, artifact_type="Sands"):
    """
    Simulate spending resin to farm an artifact and evaluate the impact on character performance.
    Returns a dict containing before/after stats and expected DPS gain.
    """
    result = {}

    # Clone the character to avoid mutating the original
    char_before = copy.deepcopy(character)

    # Damage before applying artifact
    dmg_before = char_before.expected_damage_output(
        talent_multiplier=character.talent_multiplier,
        crit_rate=character.crit_rate,
        crit_dmg=character.crit_dmg,
        dmg_bonus=character.dmg_bonus,
        enemy_level=90,
        enemy_resistance=0.1
    )

    # Simulate an artifact drop
    artifact = simulate_artifact(artifact_type)

    # Apply substat effects to the character
    for stat, value in artifact["substats"].items():
        apply_substat_to_character(character, stat, value)

    # Damage after applying artifact
    # ✅ Correct
    dmg_after = character.expected_damage_output(
        talent_multiplier=character.talent_multiplier,
        crit_rate=character.crit_rate,
        crit_dmg=character.crit_dmg,
        dmg_bonus=character.dmg_bonus,
        enemy_level=90,
        enemy_resistance=0.1
    )

    # Record results
    result["resin_spent"] = resin_spent
    result["activity"] = "artifact_farm"
    result["artifact"] = artifact
    result["damage_before"] = dmg_before
    result["damage_after"] = dmg_after
    result["dps_gain"] = dmg_after - dmg_before
    result["atk_before"] = char_before.base_stats["atk"]
    result["atk_after"] = character.base_stats["atk"]

    return result


def apply_substat_to_character(character, substat, value):
    """
    Adds a substat value to the character's relevant stat.
    You can expand this later to include crit, ER, EM, etc.
    """
    if substat == "ATK%":
        character.base_stats["atk"] *= (1 + value / 100)
    elif substat == "Flat ATK":
        character.base_stats["atk"] += value
    elif substat == "HP%":
        character.base_stats["hp"] *= (1 + value / 100)
    elif substat == "Flat HP":
        character.base_stats["hp"] += value
    elif substat == "DEF%":
        character.base_stats["def"] *= (1 + value / 100)
    elif substat == "Flat DEF":
        character.base_stats["def"] += value
    # You can store other effects in character object later
    # (e.g., crit_rate, crit_dmg, ER, EM)

def simulate_talent_farm(character, resin_spent=60, domain_level=4):
    """
    Simulates farming talent books and upgrading character talents based on cumulative inventory.
    Assumes: 20 resin per run, one upgrade from level 6 to 7 costs 9 Guides + 1 Philosophy.
    """
    runs = resin_spent // 20
    upgrade_success = False

    # Clone character to preserve baseline stats
    char_before = copy.deepcopy(character)

    dmg_before = char_before.expected_damage_output(
        talent_multiplier=character.talent_multiplier,
        crit_rate=character.crit_rate,
        crit_dmg=character.crit_dmg,
        dmg_bonus=character.dmg_bonus,
        enemy_level=90,
        enemy_resistance=0.1
    )

    # Simulate book farming
    books = simulate_multiple_talent_runs(runs=runs, domain_level=domain_level)

    # Add books to character's inventory
    for key in books:
        character.book_inventory[key] += books[key]

    # Upgrade cost table: level → (Guides, Philosophies)
    upgrade_costs = {
        6: (9, 1),
        7: (12, 1),
        8: (16, 2),
        9: (20, 2),
    }

    while character.talent_level in upgrade_costs:
        req_guides, req_philo = upgrade_costs[character.talent_level]
        if (character.book_inventory['Guides'] >= req_guides and
                character.book_inventory['Philosophies'] >= req_philo):
            character.book_inventory['Guides'] -= req_guides
            character.book_inventory['Philosophies'] -= req_philo
            character.talent_level += 1
            character.talent_multiplier *= 1.1
            upgrade_success = True
        else:
            break  # Not enough books to proceed

    dmg_after = character.expected_damage_output(
        talent_multiplier=character.talent_multiplier,
        crit_rate=character.crit_rate,
        crit_dmg=character.crit_dmg,
        dmg_bonus=character.dmg_bonus,
        enemy_level=90,
        enemy_resistance=0.1
    )

    return {
        'resin_spent': resin_spent,
        'activity': 'talent_farm',
        'domain_level': domain_level,
        'books_gained': books,
        'book_inventory': dict(character.book_inventory),  # snapshot
        'upgrade_applied': upgrade_success,
        'talent_level': character.talent_level,
        'damage_before': dmg_before,
        'damage_after': dmg_after,
        'dps_gain': dmg_after - dmg_before
    }

def simulate_with_policy(character, resin_budget, policy, domain_level=4):
    results = []
    resin_remaining = resin_budget

    while resin_remaining >= 20:
        activity = policy.choose_activity(character)

        if activity == "artifact_farm":
            result = simulate_artifact_farm(character, resin_spent=20)
        elif activity == "talent_farm":
            result = simulate_talent_farm(character, resin_spent=20, domain_level=domain_level)
        else:
            break

        accepted = policy.evaluate_upgrade(
            before_dps=result['damage_before'],
            after_dps=result['damage_after'],
            resin_cost=result['resin_spent']
        )

        result['accepted'] = accepted
        result['resin_remaining'] = resin_remaining
        result['dps'] = result['damage_after']
        results.append(result)

        if accepted or activity == "talent_farm":
            resin_remaining -= result['resin_spent']
        else:
            break

    return results

