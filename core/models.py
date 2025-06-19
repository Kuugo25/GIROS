from core.utils import calculate_damage
from core.character_buffs import apply_skill_buff
import re

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

    @classmethod
    def load_from_csv_row(cls, row):
        raw_type = row["substat_type"].strip()

        substat_type_mapping = {
            "ATK": "ATK%",
            "HP": "HP%",
            "DEF": "DEF%",
            "CRIT Rate": "CRIT Rate",
            "CRIT DMG": "CRIT DMG",
            "Elemental Mastery": "Elemental Mastery",
            "Energy Recharge": "Energy Recharge%",
            "Physical DMG Bonus": "Physical DMG Bonus"  # Optional to support now
        }

        substat_type = substat_type_mapping.get(raw_type)
        if not substat_type:
            raise ValueError(f"Unknown substat type: '{raw_type}'")

        substat_val = row["max_substat"]
        if isinstance(substat_val, str) and "%" in substat_val:
            substat_value = float(substat_val.strip('%')) / 100
        else:
            substat_value = float(substat_val)

        return cls(
            name=row["weapon_name"],
            type=row["type"],
            rarity=row["rarity"],
            base_atk=int(row["max_atk"]),
            substat_type=substat_type,
            substat_value=substat_value,
            passive=None
        )

class Character:
    def __init__(self, name, vision, weapon_type, base_stats, special_stat_type, special_stat_value, default_combo=None, default_skill=None, weapon=None):
        self.name = name
        self.vision = vision
        self.weapon_type = weapon_type
        self.base_stats = base_stats  # {'atk': ..., 'hp': ..., 'def': ...}
        self.special_stat_type = special_stat_type
        self.special_stat_value = special_stat_value
        self.weapon = weapon
        self.base_crit_rate = 0.05  # 5%
        self.base_crit_dmg = 0.50  # 50%
        self.crit_rate = self.base_crit_rate
        self.crit_dmg = self.base_crit_dmg
        self.dmg_bonus = 0.2
        self.elemental_dmg_bonus = {
            "Pyro": 0.0,
            "Hydro": 0.0,
            "Electro": 0.0,
            "Cryo": 0.0,
            "Geo": 0.0,
            "Anemo": 0.0,
            "Dendro": 0.0,
            "Physical": 0.0  # Optional, in case of Physical DMG Bonus
        }
        self.healing_bonus = 0
        self.talent_multiplier = 2.0  # Placeholder — ideally from actual skill level
        self.aa_level = 6
        self.skill_level = 6
        self.burst_level = 6
        self.default_combo = default_combo
        self.default_skill = default_skill
        self.artifacts = {
            "Flower": None,
            "Feather": None,
            "Sands": None,
            "Goblet": None,
            "Circlet": None
        }
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
        if combo and skill and multipliers:
            from core.talents import compute_combo_multiplier
            level_map = {
                "AA": self.aa_level,
                "Skill": self.skill_level,
                "Burst": self.burst_level
            }
            level = level_map.get(skill)
            talent_multiplier = compute_combo_multiplier(multipliers, self.name, skill, level, combo)

        if talent_multiplier is None:
            raise ValueError("talent_multiplier must be provided directly or computable from combo/skill/level")

        # Compute damage
        damage = calculate_damage(
            base_stat=self.base_stats['atk'],
            talent_multiplier=talent_multiplier,
            crit_rate = crit_rate if crit_rate is not None else self.crit_rate,
            crit_dmg = crit_dmg if crit_dmg is not None else self.crit_dmg,
            dmg_bonus = dmg_bonus if dmg_bonus is not None else self.dmg_bonus,
            character_level=character_level,
            enemy_level=enemy_level,
            enemy_resistance=enemy_resistance,
            **kwargs
        )

        # Revert the ATK buff if it was applied
        if buff_applied:
            self.base_stats['atk'] = original_atk

        return damage

    def sync_stats(self, stats: dict):
        """
        Apply computed total stats to the character object for accurate damage calculation.
        """
        self.base_stats["atk"] = stats["total_atk"]
        self.base_stats["hp"] = stats["total_hp"]
        self.base_stats["def"] = stats["total_def"]
        self.crit_rate = stats["crit_rate"]
        self.crit_dmg = stats["crit_dmg"]
        self.dmg_bonus = stats["elemental_dmg_bonus"].get(self.vision, 0)
        # Optionally include these if your damage formula uses them:
        self.elemental_mastery = stats["elemental_mastery"]
        self.energy_recharge = stats["energy_recharge"]
        self.healing_bonus = stats["healing_bonus"]

    @classmethod
    def load_from_csv_row(cls, row):

        ascension_stat_map = {
            "ATK": "ATK%",
            "DEF": "DEF%",
            "HP": "HP%",
            "CRIT Rate": "CRIT Rate",
            "CRIT DMG": "CRIT DMG",
            "Elemental Mastery": "Elemental Mastery",
            "Energy Recharge": "Energy Recharge%",
            "Healing Bonus": "Healing Bonus%",
            "Physical DMG Bonus": "Physical DMG Bonus",
            "Pyro DMG Bonus": "Pyro DMG Bonus",
            "Hydro DMG Bonus": "Hydro DMG Bonus",
            "Electro DMG Bonus": "Electro DMG Bonus",
            "Cryo DMG Bonus": "Cryo DMG Bonus",
            "Geo DMG Bonus": "Geo DMG Bonus",
            "Anemo DMG Bonus": "Anemo DMG Bonus",
            "Dendro DMG Bonus": "Dendro DMG Bonus"
        }

        base_stats = {
            "hp": float(row["hp_90_90"]),
            "atk": float(row["atk_90_90"]),
            "def": float(row["def_90_90"])
        }

        raw_stat_type = row["ascension_special_stat"].strip()
        special_stat_type = ascension_stat_map.get(raw_stat_type, raw_stat_type)  # fallback to raw if not mapped
        special_value = str(row.get("special_6", "0")).strip()

        if "%" in special_value:
            special_stat_value = float(special_value.replace("%", "")) / 100
        elif re.match(r"^\d+(\.\d+)?$", special_value):
            special_stat_value = float(special_value)
        else:
            special_stat_value = 0.0

        return cls(
            name=row["character_name"],
            vision=row["vision"],
            weapon_type=row["weapon_type"],
            base_stats=base_stats,
            special_stat_type=special_stat_type,
            special_stat_value=special_stat_value,
            default_combo="E12N1C",  # You can adjust this later per character
            default_skill="AA"
        )

    def compute_total_stats(self):

        # Base stats
        base_hp = self.base_stats["hp"]
        base_atk = self.base_stats["atk"]
        base_def = self.base_stats["def"]
        elemental_dmg_bonus = {k: 0.0 for k in self.elemental_dmg_bonus.keys()}
        weapon_base_atk = self.weapon.base_atk if self.weapon else 0
        base_atk += weapon_base_atk

        # Initialize bonuses
        percent_bonus = {"hp": 0.0, "atk": 0.0, "def": 0.0}
        flat_bonus = {"hp": 0.0, "atk": 0.0, "def": 0.0}
        crit_rate = 0.05
        crit_dmg = 0.50
        elemental_mastery = 0.0
        healing_bonus = 0.0
        energy_recharge = 1.0  # Base ER is 100%

        # Ascension special stat
        if self.special_stat_type == "HP%":
            percent_bonus["hp"] += self.special_stat_value
        elif self.special_stat_type == "ATK%":
            percent_bonus["atk"] += self.special_stat_value
        elif self.special_stat_type == "DEF%":
            percent_bonus["def"] += self.special_stat_value
        elif self.special_stat_type == "CRIT Rate":
            crit_rate += self.special_stat_value
        elif self.special_stat_type == "CRIT DMG":
            crit_dmg += self.special_stat_value
        elif self.special_stat_type.endswith("DMG Bonus"):
            element = self.special_stat_type.replace(" DMG Bonus", "")
            if element in self.elemental_dmg_bonus:
                self.elemental_dmg_bonus[element] += self.special_stat_value
        elif "Healing Bonus" in self.special_stat_type:
            self.healing_bonus += self.special_stat_value
        elif self.special_stat_type == "Elemental Mastery":
            elemental_mastery += self.special_stat_value
        elif self.special_stat_type == "Energy Recharge%":
            energy_recharge += self.special_stat_value

        # Weapon substat
        if self.weapon:
            sub = self.weapon.substat_type
            val = self.weapon.substat_value
            if sub == "HP%":
                percent_bonus["hp"] += val
            elif sub == "ATK%":
                percent_bonus["atk"] += val
            elif sub == "DEF%":
                percent_bonus["def"] += val
            elif sub == "CRIT Rate":
                crit_rate += val
            elif sub == "CRIT DMG":
                crit_dmg += val
            elif sub == "Elemental Mastery":
                elemental_mastery += val
            elif sub == "Energy Recharge%":
                energy_recharge += val

        # Artifacts
        for art in self.artifacts.values():
            if art:
                # Main stat
                stat = art["main_stat"]
                val = art["main_stat_value"]
                if stat == "HP%":
                    percent_bonus["hp"] += val / 100
                elif stat == "Flat HP":
                    flat_bonus["hp"] += val
                elif stat == "ATK%":
                    percent_bonus["atk"] += val / 100
                elif stat == "Flat ATK":
                    flat_bonus["atk"] += val
                elif stat == "DEF%":
                    percent_bonus["def"] += val / 100
                elif stat == "Flat DEF":
                    flat_bonus["def"] += val
                elif stat == "CRIT Rate%":
                    crit_rate += val / 100
                elif stat == "CRIT DMG%":
                    crit_dmg += val / 100
                elif stat == "Elemental Mastery":
                    elemental_mastery += val
                elif stat == "Energy Recharge%":
                    energy_recharge += val / 100
                elif stat == "Healing Bonus%":
                    healing_bonus += val / 100
                elif stat.endswith("DMG Bonus"):
                    element = stat.replace(" DMG Bonus", "")
                    if element in elemental_dmg_bonus:
                        elemental_dmg_bonus[element] += val / 100

                # Substats
                for sub, val in art["substats"].items():
                    if sub == "HP%":
                        percent_bonus["hp"] += val / 100
                    elif sub == "Flat HP":
                        flat_bonus["hp"] += val
                    elif sub == "ATK%":
                        percent_bonus["atk"] += val / 100
                    elif sub == "Flat ATK":
                        flat_bonus["atk"] += val
                    elif sub == "DEF%":
                        percent_bonus["def"] += val / 100
                    elif sub == "Flat DEF":
                        flat_bonus["def"] += val
                    elif sub == "CRIT Rate%":
                        crit_rate += val / 100
                    elif sub == "CRIT DMG%":
                        crit_dmg += val / 100
                    elif sub == "Elemental Mastery":
                        elemental_mastery += val
                    elif sub == "Energy Recharge%":
                        energy_recharge += val / 100

        # Final totals
        total_hp = base_hp * (1 + percent_bonus["hp"]) + flat_bonus["hp"]
        total_atk = base_atk * (1 + percent_bonus["atk"]) + flat_bonus["atk"]
        total_def = base_def * (1 + percent_bonus["def"]) + flat_bonus["def"]

        return {
            "base_hp": base_hp,
            "base_atk": base_atk,
            "base_def": base_def,
            "weapon_base_atk": weapon_base_atk,
            "percent_bonus": percent_bonus,
            "flat_bonus": flat_bonus,
            "total_hp": total_hp,
            "total_atk": total_atk,
            "total_def": total_def,
            "crit_rate": crit_rate,
            "crit_dmg": crit_dmg,
            "elemental_mastery": elemental_mastery,
            "energy_recharge": energy_recharge,
            "healing_bonus": healing_bonus,
            "elemental_dmg_bonus": elemental_dmg_bonus,
        }

