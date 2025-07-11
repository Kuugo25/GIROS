# core/formulas.py
def calculate_damage(
    base_stat,
    talent_multiplier,
    crit_rate,
    crit_dmg,
    dmg_bonus,
    enemy_level,
    character_level,
    enemy_resistance,
    def_ignore=0.0,
    def_reduction=0.0,
    reaction_multiplier=1.0,
    em=0,
    reaction_type=None
):
    """
    Calculate the expected damage output based on Genshin Impact's damage formula.

    Parameters:
    - base_stat (float): The main stat used for damage calculation (e.g., ATK, HP, DEF).
    - talent_multiplier (float): The talent scaling multiplier (e.g., 2.0 for 200%).
    - crit_rate (float): Critical hit rate (0 to 1).
    - crit_dmg (float): Critical damage bonus (e.g., 0.5 for 50%).
    - dmg_bonus (float): Total damage bonus percentage (e.g., 0.2 for 20%).
    - enemy_level (int): The level of the enemy.
    - character_level (int): The level of the character.
    - enemy_resistance (float): Enemy's resistance to the damage type (e.g., 0.1 for 10%).
    - def_ignore (float): Percentage of enemy defense ignored (0 to 1).
    - def_reduction (float): Percentage of enemy defense reduced (0 to 1).
    - reaction_multiplier (float): Multiplier for elemental reactions (e.g., 1.5 for Melt).
    - em (float): Elemental Mastery of the character.
    - reaction_type (str): Type of elemental reaction ('amplifying' or 'transformative').

    Returns:
    - float: The calculated damage output.
    """

    # Base Damage
    base_damage = base_stat * talent_multiplier/100

    # Critical Multiplier
    crit_multiplier = 1 + crit_rate * crit_dmg

    # Damage Bonus Multiplier
    dmg_bonus_multiplier = 1 + dmg_bonus

    # Defense Multiplier
    def_multiplier = (character_level + 100) / (
        (1 - def_reduction) * (1 - def_ignore) * (enemy_level + 100) + character_level + 100
    )

    # Resistance Multiplier
    if enemy_resistance < 0:
        res_multiplier = 1 - (enemy_resistance / 2)
    elif enemy_resistance < 0.75:
        res_multiplier = 1 - enemy_resistance
    else:
        res_multiplier = 1 / (4 * enemy_resistance + 1)

    # Reaction Bonus Multiplier
    if reaction_type == 'amplifying':
        em_bonus = 2.78 * em / (em + 1400)
        reaction_bonus_multiplier = reaction_multiplier * (1 + em_bonus)
    elif reaction_type == 'transformative':
        em_bonus = 16 * em / (em + 2000)
        reaction_bonus_multiplier = reaction_multiplier * (1 + em_bonus)
    else:
        reaction_bonus_multiplier = 1.0

    # Total Damage Calculation
    damage = base_damage * crit_multiplier * dmg_bonus_multiplier * def_multiplier * res_multiplier * reaction_bonus_multiplier

    return damage

def calculate_heal(
    base_hp: float,
    heal_pct: float,
    heal_flat: float,
    healing_bonus: float
) -> float:
    """
    Compute one tick of healing:
      (base_hp * heal_pct + heal_flat) * (1 + healing_bonus)
    """
    raw = base_hp * heal_pct + heal_flat
    return raw * (1 + healing_bonus)
