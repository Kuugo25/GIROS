from core.utils import calculate_damage
from core.character_buffs import apply_skill_buff

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
    def __init__(self, name, vision, weapon_type, base_stats, special_stat_type, special_stat_value, default_combo=None, default_skill=None, weapon=None):
        self.name = name
        self.vision = vision
        self.weapon_type = weapon_type
        self.base_stats = base_stats  # {'atk': ..., 'hp': ..., 'def': ...}
        self.special_stat_type = special_stat_type
        self.special_stat_value = special_stat_value
        self.weapon = weapon
        self.crit_rate = 0.2 # Placeholder stats
        self.crit_dmg = 1.0
        self.dmg_bonus = 0.2
        self.talent_multiplier = 2.0  # Placeholder — ideally from actual skill level
        self.talent_level = 6
        self.skill_level = 6  # Default level for Hu Tao's E
        self.default_combo = default_combo
        self.default_skill = default_skill
        self.book_inventory = {
            'Teachings': 0,
            'Guides': 0,
            'Philosophies': 0
        }

    def __repr__(self):
        weapon_name = self.weapon.name if self.weapon else "None"
        return f"<Character: {self.name}, {self.vision}, Weapon: {weapon_name}>"

    def expected_damage_output(
            self,
            talent_multiplier=None,
            crit_rate=None,
            crit_dmg=None,
            dmg_bonus=0,
            character_level=90,
            combo=None,
            skill=None,
            level=None,
            multipliers=None,
            enemy_level=100,
            enemy_resistance=0.1,
            **kwargs
    ):
        buff_applied = False
        original_atk = self.base_stats['atk']  # Save base ATK before any buff

        # Apply skill buff if 'E' is in combo
        if combo and "E" in combo:
            apply_skill_buff(self)
            combo = combo.replace("E", "")
            buff_applied = True

        # Compute multiplier if combo is provided
        if combo and skill and level and multipliers:
            from core.talents import compute_combo_multiplier
            talent_multiplier = compute_combo_multiplier(multipliers, self.name, skill, level, combo)

        if talent_multiplier is None:
            raise ValueError("talent_multiplier must be provided directly or computable from combo/skill/level")

        # Compute damage
        damage = calculate_damage(
            base_stat=self.base_stats['atk'],
            talent_multiplier=talent_multiplier,
            crit_rate=crit_rate,
            crit_dmg=crit_dmg,
            dmg_bonus=dmg_bonus,
            character_level=character_level,
            enemy_level=enemy_level,
            enemy_resistance=enemy_resistance,
            **kwargs
        )

        # Revert the ATK buff if it was applied
        if buff_applied:
            self.base_stats['atk'] = original_atk

        return damage


