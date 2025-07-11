# core/character_buffs.py

TALENT_MULTIPLIERS = None  # This gets populated via init

def init_buffs(multipliers):
    global TALENT_MULTIPLIERS
    TALENT_MULTIPLIERS = multipliers

def hu_tao_skill_buff(character):
    # recompute full stats so total_hp is up-to-date
    stats = character.compute_total_stats()
    hp = stats["total_hp"]
    skill_level = character.skill_level
    entry = (
        TALENT_MULTIPLIERS
          .get(character.name, {})
          .get("Skill", {})
          .get(skill_level, {})
          .get("ATK_Bonus%HP", {})
    )
    scaling_percent = entry.get("value", 0.0) / 100.0
    atk_bonus = hp * scaling_percent

    if not hasattr(character, "_artifact_bonuses"):
        character._artifact_bonuses = {
                "percent_bonus": {"hp": 0.0, "atk": 0.0, "def": 0.0},
                "flat_bonus": {"hp": 0.0, "atk": 0.0, "def": 0.0},
                "crit_rate": 0.0,
                "crit_dmg": 0.0,
                "elemental_mastery": 0.0,
                "energy_recharge": 0.0,
                "healing_bonus": 0.0,
                "elemental_dmg_bonus": {}
            }
    character._artifact_bonuses["flat_bonus"]["atk"] += atk_bonus

def furina_burst_buff(character):
    """
    After she casts Q, give a flat + (scaling from talent) % damage bonus to
    all damage types. We'll just write it onto character.dmg_bonus here.
    """
    if character.name != "Furina":
        return False

    # grab the BUFF entry dict, then pull its "value"
    lvl = character.burst_level
    buff_entry = (
        TALENT_MULTIPLIERS
          .get("Furina", {})
          .get("Burst", {})
          .get(lvl, {})
          .get("Fanfare DMG Bonus%", {})
    )# or whatever your CSV column is called
    raw_val = buff_entry.get("value", 0.0)
    bonus = raw_val / 100.0

    # either add it to her universal dmg_bonus:
    character.dmg_bonus += bonus

    # or add it on every element:
    for elem in character.elemental_dmg_bonus:
        character.elemental_dmg_bonus[elem] += bonus

    return True

def bennett_burst_buff(character):
    """
    After Bennett casts Q, give a flat ATK bonus:
      bonus_atk = (base_atk + weapon_base_atk) * (TeamBuff% from multipliers)
    """
    if character.name != "Bennett":
        return False

    # pull the TeamBuff% value for his Burst at current level
    lvl = character.burst_level
    raw = TALENT_MULTIPLIERS \
          .get("Bennett", {}) \
          .get("Burst", {}) \
          .get(lvl, {}) \
          .get("InspirationBuff", 0.0)
    buff_pct = raw / 100.0

    # compute his “base ATK” (character.base_stats['atk'] already excludes weapon)
    base_atk = character.base_stats["atk"] + (character.weapon.base_atk if character.weapon else 0)
    flat_bonus = base_atk * buff_pct

    # stash it into the artifact_bonuses flat ATK slot
    if not hasattr(character, "_artifact_bonuses"):
        character._artifact_bonuses = {
            "percent_bonus": {"hp":0.0, "atk":0.0, "def":0.0},
            "flat_bonus":    {"hp":0.0, "atk":0.0, "def":0.0},
            "crit_rate":0.0, "crit_dmg":0.0,
            "elemental_mastery":0.0, "energy_recharge":0.0,
            "healing_bonus":0.0, "elemental_dmg_bonus":{}
        }
    character._artifact_bonuses["flat_bonus"]["atk"] += flat_bonus

    return True

BUFF_FUNCTIONS = {
    "Hu Tao": hu_tao_skill_buff,
    # Add more characters here as needed
}
BURST_BUFFS = {
    "Furina": furina_burst_buff,
    "Bennett": bennett_burst_buff,
}
def apply_skill_buff(character) -> bool:
    """Return True if we actually applied a buff (i.e. Hu Tao's E)."""
    if character.name in BUFF_FUNCTIONS:
        BUFF_FUNCTIONS[character.name](character)
        return True
    return False

def apply_burst_buff(character) -> bool:
    """Called once per 'Q' in your combo string."""
    fn = BURST_BUFFS.get(character.name)
    if fn:
        return fn(character)
    return False