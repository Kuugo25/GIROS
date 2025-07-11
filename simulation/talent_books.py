import random

import random

def simulate_talent_book_run(domain_level=4):
    """
    Simulates one run of a talent book domain using the wiki’s two‐roll model:
      1) First roll produces *only* 2★ Teachings (range & avg from the table).
      2) Second roll produces 2–4 “packs,” each of which can be 2★, 3★, or 4★
         with probabilities chosen to reproduce the table’s overall averages.
    """
    # --- pick your first‐roll Teaching count from the table --- #
    if domain_level == 1:
        first_teach = random.randint(3, 4)       # ★★ Range 3–4, avg 3.2
        pack_min, pack_max = 0, 0                # domain I has no second roll
        p_guides, p_phils = 0, 0
    elif domain_level == 2:
        first_teach = random.randint(2, 3)       # ★★ Range 2–3, avg 2.5
        pack_min, pack_max = 0, 0
        p_guides, p_phils = 0, 0
    elif domain_level == 3:
        first_teach = random.randint(1, 2)       # ★★ Range 1–2, avg 1.8
        pack_min, pack_max = 2, 3                # second‐roll 2–3 packs
        # overall avg guides=2.0, phils≈0.05 ⇒ p3≈2.0/2.5, p4≈0.05/2.5
        p_guides, p_phils = 2.0/2.5, 0.05/2.5
    elif domain_level == 4:
        first_teach = random.randint(2, 3)       # ★★ Range 2–3, avg 2.2
        pack_min, pack_max = 2, 4                # second‐roll 2–4 packs
        # overall avg guides=1.98, phils=0.22 ⇒ total packs avg≈3
        # so p_guides≈1.98/3, p_phils≈0.22/3
        p_guides, p_phils = 1.98/3.0, 0.22/3.0
    else:
        raise ValueError("Domain level must be between 1 and 4")

    # --- start totals with your first‐roll teachings --- #
    teachings    = first_teach
    guides       = 0
    philosophies = 0

    # --- second roll: drop between pack_min–pack_max packs, each random rarity --- #
    for _ in range(random.randint(pack_min, pack_max)):
        r = random.random()
        if r < p_guides:
            guides += 1
        elif r < p_guides + p_phils:
            philosophies += 1
        else:
            teachings += 1

    return {
        'Teachings': teachings,
        'Guides': guides,
        'Philosophies': philosophies
    }

def simulate_multiple_talent_runs(runs=3, domain_level=4):
    """
    Simulates multiple talent domain runs at a given domain level.
    """
    total = {'Teachings': 0, 'Guides': 0, 'Philosophies': 0}
    for _ in range(runs):
        result = simulate_talent_book_run(domain_level=domain_level)
        for k in total:
            total[k] += result[k]
    return total

def recommend_talent_upgrade(character, multipliers):
    import copy
    from core.talents import compute_combo_multiplier

    current_levels = {
        "AA": character.aa_level,
        "Skill": character.skill_level,
        "Burst": character.burst_level,
    }

    combo = character.default_combo
    skill = character.default_skill
    vision = character.vision

    # Baseline damage
    base_dmg = character.expected_damage_output(
        combo=combo,
        skill=skill,
        multipliers=multipliers,
        crit_rate=character.crit_rate,
        crit_dmg=character.crit_dmg,
        dmg_bonus=character.elemental_dmg_bonus.get(vision, 0),
        enemy_level=100,
        enemy_resistance=0.1
    )

    gains = {}
    for talent in ["AA", "Skill", "Burst"]:
        char_copy = copy.deepcopy(character)

        # Skip if already level 10
        if getattr(char_copy, f"{talent.lower()}_level") >= 10:
            continue

        # Simulate upgrading this one talent
        setattr(char_copy, f"{talent.lower()}_level", current_levels[talent] + 1)

        dmg = char_copy.expected_damage_output(
            combo=combo,
            skill=skill,
            multipliers=multipliers,
            crit_rate=char_copy.crit_rate,
            crit_dmg=char_copy.crit_dmg,
            dmg_bonus=char_copy.elemental_dmg_bonus.get(vision, 0),
            enemy_level=100,
            enemy_resistance=0.1
        )
        gains[talent] = dmg - base_dmg

    if not gains:
        return {"recommendation": None, "reason": "All talents already at max level."}

    best_talent = max(gains, key=gains.get)
    return {
        "recommendation": best_talent,
        "damage_gain": gains[best_talent],
        "all_gains": dict(sorted(gains.items(), key=lambda x: x[1], reverse=True))
    }
