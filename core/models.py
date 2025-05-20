from core.utils import calculate_damage
class Weapon:
    def __init__(self, name, type, rarity, base_atk, substat_type, substat_value, passive):
        self.name = name
        self.type = type
        self.rarity = rarity
        self.base_atk = base_atk
        self.substat_type = substat_type
        self.substat_value = substat_value
        self.passive = passive

    def __repr__(self):
        return f"<Weapon: {self.name} ({self.rarity}★)>"

class Character:
    def __init__(self, name, vision, weapon_type, base_stats, special_stat_type, special_stat_value, weapon=None):
        self.name = name
        self.vision = vision
        self.weapon_type = weapon_type
        self.base_stats = base_stats  # {'atk': ..., 'hp': ..., 'def': ...}
        self.special_stat_type = special_stat_type
        self.special_stat_value = special_stat_value
        self.weapon = weapon
        self.crit_rate = 0.5  # Placeholder stats
        self.crit_dmg = 1.0
        self.dmg_bonus = 0.2
        self.talent_multiplier = 2.0  # Placeholder — ideally from actual skill level
        self.talent_level = 6
        self.book_inventory = {
            'Teachings': 0,
            'Guides': 0,
            'Philosophies': 0
        }

    def __repr__(self):
        weapon_name = self.weapon.name if self.weapon else "None"
        return f"<Character: {self.name}, {self.vision}, Weapon: {weapon_name}>"

    def expected_damage_output(self, talent_multiplier, crit_rate, crit_dmg, dmg_bonus=0, **kwargs):
        return calculate_damage(
            base_stat=self.base_stats['atk'],
            talent_multiplier=talent_multiplier,
            crit_rate=crit_rate,
            crit_dmg=crit_dmg,
            dmg_bonus=dmg_bonus,
            character_level=90,
            **kwargs
        )
