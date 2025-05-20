import pandas as pd
from core.models import Character, Weapon

def load_characters(filepath):
    df = pd.read_csv(filepath)
    characters = []
    for _, row in df.iterrows():
        stats = {
            'atk': row['atk_90_90'],
            'hp': row['hp_90_90'],
            'def': row['def_90_90']
        }
        char = Character(
            name=row['character_name'],
            vision=row['vision'],
            weapon_type=row['weapon_type'],
            base_stats=stats,
            special_stat_type=row['ascension_special_stat'],
            special_stat_value=row['special_6']
        )
        characters.append(char)
    return characters

def load_weapons(filepath):
    df = pd.read_csv(filepath)
    weapons = []
    for _, row in df.iterrows():
        weapon = Weapon(
            name=row['weapon_name'],
            type=row['type'],
            rarity=row['rarity'],
            base_atk=row['max_atk'],
            substat_type=row['substat_type'],
            substat_value=row['max_substat'],
            passive=row['passive_ability']
        )
        weapons.append(weapon)
    return weapons
