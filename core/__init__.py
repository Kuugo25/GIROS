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

    def __repr__(self):
        return f"<Character: {self.name}, {self.vision} user>"
