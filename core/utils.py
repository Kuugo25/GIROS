# core/utils.py

import pandas as pd
from core.models import Character, Weapon
from core.talents import load_talent_multipliers
from core.character_buffs import init_buffs

TALENT_MULTIPLIERS = load_talent_multipliers("../data/talent_multipliers.csv")
init_buffs(TALENT_MULTIPLIERS)

CHARACTER_PATH = "../data/genshin_characters_v1.csv"
WEAPON_PATH = "../data/genshin_weapons_v6.csv"

# Loads in raw character data from CSV for base character
def make_clean_character(character_name: str, weapon_name: str = None, artifacts: dict = None) -> Character:
    # Load character
    char_df = pd.read_csv(CHARACTER_PATH)
    char_row = char_df[char_df["character_name"] == character_name].iloc[0]
    character = Character.load_from_csv_row(char_row)

    # Equip weapon if provided
    if weapon_name:
        weap_df = pd.read_csv(WEAPON_PATH)
        match = weap_df[weap_df["weapon_name"].str.contains(weapon_name, case=False)]
        if match.empty:
            raise ValueError(f"Weapon '{weapon_name}' not found.")
        weapon = Weapon.load_from_csv_row(match.iloc[0])
        character.weapon = weapon

    # Equip artifacts if provided
    if artifacts:
        character.artifacts = artifacts

    return character

# Allows talent level specification, one-step initializer (levels, artifacts, combo)
def character_factory(
    name="Hu Tao",
    weapon_name="Homa",
    artifacts=None,
    aa_level=6, skill_level=6, burst_level=6,
    combo="E12N1C", skill_type="AA"
):
    char = make_clean_character(name, weapon_name, artifacts)
    char.aa_level = aa_level
    char.skill_level = skill_level
    char.burst_level = burst_level
    char.default_combo = combo
    char.default_skill = skill_type

    # Only sync to base stats (not computed stats!)
    char.sync_stats(char.compute_total_stats())

    return char

# Wraps into zero-arg factory
def build_character_factory(name, weapon_name=None, artifacts=None, aa_level=1, skill_level=1, burst_level=1,
                            combo=None, skill_type="AA"):
    """
    Returns a reusable function that builds a clean Character object with specified setup.
    """
    def factory():
        from core.utils import character_factory
        return character_factory(
            name=name,
            weapon_name=weapon_name,
            artifacts=artifacts,
            aa_level=aa_level,
            skill_level=skill_level,
            burst_level=burst_level,
            combo=combo,
            skill_type=skill_type
        )
    return factory
