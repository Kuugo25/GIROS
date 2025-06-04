from simulation.artifact import simulate_artifact
from simulation.talent_books import simulate_multiple_talent_runs
from core.talents import compute_combo_multiplier, load_talent_multipliers
import copy

TALENT_MULTIPLIERS = load_talent_multipliers("data/talent_multipliers.csv")

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
        enemy_level=100,
        enemy_resistance=0.1
    )

    # Simulate an artifact drop
    artifact = simulate_artifact(artifact_type)

    # Apply substat effects to the character
    for stat, value in artifact["substats"].items():
        apply_substat_to_character(character, stat, value)

    # Damage after applying artifact
    dmg_after = character.expected_damage_output(
        talent_multiplier=character.talent_multiplier,
        crit_rate=character.crit_rate,
        crit_dmg=character.crit_dmg,
        dmg_bonus=character.dmg_bonus,
        enemy_level=100,
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
    elif substat == "CRIT Rate%":
        character.crit_rate += value / 100
    elif substat == "CRIT DMG%":
        character.crit_dmg += value / 100
    elif substat == "Energy Recharge%":
        # You could later use this for buff logic or ER-based scaling
        pass
    elif substat == "Elemental Mastery":
        # Placeholder: implement actual EM logic later
        pass


def simulate_talent_farm(character, resin_spent=60, domain_level=4):
    runs = resin_spent // 20
    upgrade_success = False

    # Compute before-upgrade damage
    char_before = copy.deepcopy(character)
    dmg_before = char_before.expected_damage_output(
        combo=character.default_combo,
        skill=character.default_skill,
        level=character.talent_level,
        multipliers=TALENT_MULTIPLIERS,
        crit_rate=character.crit_rate,
        crit_dmg=character.crit_dmg,
        dmg_bonus=character.dmg_bonus,
        enemy_level=100,
        enemy_resistance=0.1
    )

    # Simulate book farming
    books = simulate_multiple_talent_runs(runs=runs, domain_level=domain_level)
    for k, v in books.items():
        character.book_inventory[k] += v

    # Upgrade cost in "Teachings"
    upgrade_costs = {
        1: 3,
        2: 6,
        3: 12,
        4: 18,
        5: 27,
        6: 36,
        7: 54,
        8: 108,
        9: 144
    }

    while character.talent_level in upgrade_costs:
        required_teachings = upgrade_costs[character.talent_level]
        total_teachings = (
            character.book_inventory['Teachings']
            + character.book_inventory['Guides'] * 3
            + character.book_inventory['Philosophies'] * 9
        )

        if total_teachings >= required_teachings:
            # Consume books in order: Teachings > Guides > Philosophies
            remaining = required_teachings
            for tier, value, name in [(1, 1, 'Teachings'), (3, 1, 'Guides'), (9, 1, 'Philosophies')]:
                used = min(character.book_inventory[name], remaining // tier)
                character.book_inventory[name] -= used
                remaining -= used * tier
            character.talent_level += 1
            upgrade_success = True
        else:
            break

    # Compute after-upgrade damage
    dmg_after = character.expected_damage_output(
        combo=character.default_combo,
        skill=character.default_skill,
        level=character.talent_level,
        multipliers=TALENT_MULTIPLIERS,
        crit_rate=character.crit_rate,
        crit_dmg=character.crit_dmg,
        dmg_bonus=character.dmg_bonus,
        enemy_level=100,
        enemy_resistance=0.1
    )

    return {
        'resin_spent': resin_spent,
        'activity': 'talent_farm',
        'domain_level': domain_level,
        'books_gained': books,
        'book_inventory': dict(character.book_inventory),
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

