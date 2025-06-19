from simulation.artifact import simulate_artifact
from simulation.talent_books import simulate_multiple_talent_runs
from core.talents import compute_combo_multiplier, load_talent_multipliers
import copy

def simulate_artifact_farm(character, resin_spent=20, artifact_type="Sands", multipliers=None):
    if multipliers is None:
        raise ValueError("Talent multipliers must be provided.")
    result = {}

    # Clone for baseline damage
    char_before = copy.deepcopy(character)
    for artifact in character.artifacts.values():
        if artifact:
            apply_artifact(char_before, artifact)
    char_before.sync_stats()

    dmg_before = char_before.expected_damage_output(
        combo=char_before.default_combo,
        skill=char_before.default_skill,
        level=(
            char_before.aa_level if char_before.default_skill == "AA" else
            char_before.skill_level if char_before.default_skill == "Skill" else
            char_before.burst_level
        ),
        multipliers=multipliers,
        crit_rate=char_before.crit_rate,
        crit_dmg=char_before.crit_dmg,
        dmg_bonus=char_before.elemental_dmg_bonus.get(char_before.vision, 0),
        enemy_level=100,
        enemy_resistance=0.1
    )
    # Simulate drop
    new_artifact = simulate_artifact(artifact_type)

    # Clone again to simulate applying the new artifact
    char_test = copy.deepcopy(character)

    # Remove old artifact effect (if any)
    old_artifact = char_test.artifacts.get(artifact_type)
    if old_artifact:
        apply_artifact(char_test, old_artifact, remove=True)
        char_test.artifacts[artifact_type] = None

    # Set and apply new artifact
    char_test.artifacts[artifact_type] = new_artifact
    apply_artifact(char_test, new_artifact)
    char_test.sync_stats()

    print("Before:", char_before.base_stats, char_before.crit_rate, char_before.crit_dmg, char_before.elemental_dmg_bonus.get(char_before.vision, 0))
    print("After:", char_test.base_stats, char_test.crit_rate, char_test.crit_dmg, char_test.elemental_dmg_bonus.get(char_test.vision, 0))

    # Damage after
    dmg_after = char_test.expected_damage_output(
        combo=char_test.default_combo,
        skill=char_test.default_skill,
        level=(
            char_test.aa_level if char_test.default_skill == "AA" else
            char_test.skill_level if char_test.default_skill == "Skill" else
            char_test.burst_level
        ),
        multipliers=multipliers,
        crit_rate=char_test.crit_rate,
        crit_dmg=char_test.crit_dmg,
        dmg_bonus=char_test.elemental_dmg_bonus.get(char_test.vision, 0),
        enemy_level=100,
        enemy_resistance=0.1
    )

    # Accept artifact only if damage increased
    accepted = dmg_after > dmg_before
    if accepted:
        character.artifacts[artifact_type] = new_artifact
        apply_artifact(character, new_artifact)
        character.sync_stats()
    else:
        dmg_after = dmg_before  # no change

    result.update({
        "resin_spent": resin_spent,
        "activity": "artifact_farm",
        "artifact": new_artifact,
        "artifact_type": artifact_type,
        "accepted": accepted,
        "damage_before": dmg_before,
        "damage_after": dmg_after,
        "dps_gain": dmg_after - dmg_before,
        "upgrade_counts": new_artifact["upgrades"]
    })
    return result

def apply_artifact(character, artifact, remove=False):
    modifier = -1 if remove else 1

    main = artifact["main_stat"]

    # Normalize common naming issues
    normalization = {
        "CRIT DMG": "CRIT DMG%",
        "CRIT Rate": "CRIT Rate%",
        "ATK": "Flat ATK",
        "HP": "Flat HP",
        "DEF": "Flat DEF"
    }
    raw_main = artifact["main_stat"]
    normalized_main = normalization.get(raw_main, raw_main)
    main_value = artifact.get("main_stat_value", artifact["substats"].get(normalized_main, 0))
    apply_substat_to_character(character, normalized_main, modifier * main_value)

    # Apply substats
    for stat, value in artifact["substats"].items():
        stat = normalization.get(stat, stat)  # normalize substats too
        apply_substat_to_character(character, stat, modifier * value)

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
        character.energy_recharge += value / 100
    elif substat == "Elemental Mastery":
        character.elemental_mastery += value
    elif substat.endswith("DMG Bonus"):
        element = substat.replace(" DMG Bonus", "")
        if element in character.elemental_dmg_bonus:
            character.elemental_dmg_bonus[element] += value / 100
    else:
        print(f"[WARN] Unknown substat: {substat} — skipped.")

    if value > 0:
        print(f"Applied {substat} +{value:.2f}")
    else:
        print(f"Removed {substat} {-value:.2f}")

def simulate_talent_farm(character, resin_spent=60, domain_level=4, multipliers=None):
    if multipliers is None:
        raise ValueError("Talent multipliers must be provided.")
    runs = resin_spent // 20
    upgrade_success = False

    # Compute before-upgrade damage
    char_before = copy.deepcopy(character)
    dmg_before = char_before.expected_damage_output(
        combo=character.default_combo,
        skill=character.default_skill,
        level=character.talent_level,
        multipliers=multipliers,
        crit_rate=character.crit_rate,
        crit_dmg=character.crit_dmg,
        dmg_bonus=character.elemental_dmg_bonus.get(character.vision, 0),
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
        multipliers=multipliers,
        crit_rate=character.crit_rate,
        crit_dmg=character.crit_dmg,
        dmg_bonus=character.elemental_dmg_bonus.get(character.vision, 0),
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
            result = simulate_talent_farm(character, resin_spent=20, domain_level=domain_level, multipliers=policy.multipliers)
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

