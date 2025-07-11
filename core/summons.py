# core/summons.py
import math
import copy
from core.formulas    import calculate_damage
from core.character_buffs import furina_burst_buff
from core.formulas import calculate_heal

class Summon:
    def __init__(self, character, multipliers, skill_key, hit_key, level, element, interval, duration):
        self.c         = character
        self.multipliers = multipliers
        self.skill_key = skill_key
        self.hit_key   = hit_key
        self.level     = level
        self.element   = element
        self.interval  = interval
        self.duration  = duration

    def ticks(self):
        # at least one hit, even if interval > duration
        return max(1, math.floor(self.duration / self.interval))

    def total_damage(self):
        entry = self.multipliers[self.c.name][self.skill_key][self.level] \
            .get(self.hit_key, {})
        raw = entry.get("value", 0.0)
        scale = entry.get("scaling", "")

        # pick base stat
        if scale == "HP":
            base_stat = self.c.total_hp
        elif scale == "ATK":
            base_stat = self.c.total_atk
        else:
            raise ValueError(f"Unexpected scaling {scale!r} on {self.hit_key!r}")

        tm = raw
        ticks = self.ticks()

        # DEBUG – print everything
        print(f"[Summon] {self.hit_key} @ lvl{self.level} → raw%={raw:.2f}, "
              f"scaling={scale}, base_stat={base_stat:.2f}, tm={tm:.4f}, "
              f"ticks={ticks}")

        bonus = self.c.elemental_dmg_bonus.get(self.element, 0.0)

        # —— Furina passive: every 1 000 HP gives +0.7% Salon-Member DMG, capped at 28% ——
        if self.c.name == "Furina":
            hp_chunks = int(self.c.total_hp // 1000)
            salon_bonus = min(hp_chunks * 0.007, 0.28)
            bonus += salon_bonus

        cr, cd = self.c.crit_rate, self.c.crit_dmg

        dmg = 0.0
        for _ in range(ticks):
            dmg += calculate_damage(
                base_stat=base_stat,
                talent_multiplier=tm,
                crit_rate=cr,
                crit_dmg=cd,
                dmg_bonus=bonus,
                character_level=90,
                enemy_level=100,
                enemy_resistance=0.1
            )
        return dmg

def simulate_furina_e_summons(character, multipliers, apply_q_buff: bool = False):
    """
    Total damage from her E summons over their 30 s lifetime.
    If apply_q_buff=True, we first cast Q and apply its team buff.
    """
    lvl = character.skill_level

    # work on a deep copy so we never pollute the caller
    char = copy.deepcopy(character)
    char.sync_stats(char.compute_total_stats())

    # optionally apply her Burst buff
    if apply_q_buff:
        # this will add the proper level-scaling dmg bonus into char.elemental_dmg_bonus
        furina_burst_buff(char)

    total = 0.0

    # one-off bubble
    bubble = Summon(
        character=char,
        multipliers=multipliers,
        skill_key="Skill",
        hit_key="OusiaBubble",
        level=lvl,
        element="Hydro",
        interval=9999,
        duration=0.1
    )
    total += bubble.total_damage()

    # continuous summons
    GLOBAL_CD = 0.5
    native_intervals = {
        "GentilhommeUsher":       2.9,
        "SurintendanteChevalmarin": 1.19,
        "MademoiselleCrabaletta":   4.8,
    }
    for hit_key, base_cd in native_intervals.items():
        s = Summon(
            character=char,
            multipliers=multipliers,
            skill_key="Skill",
            hit_key=hit_key,
            level=lvl,
            element="Hydro",
            interval=base_cd + GLOBAL_CD,
            duration=30.0
        )
        total += s.total_damage()

    return total

class HealEffect:
    def __init__(self, character, multipliers, skill_key, level, interval, duration):
        self.c           = character
        self.multipliers = multipliers
        self.skill_key   = skill_key
        self.level       = level
        self.interval    = interval
        self.duration    = duration

    def ticks(self):
        return max(1, math.floor(self.duration / self.interval))

    def total_heal(self):
        entries = self.multipliers[self.c.name][self.skill_key][self.level]
        pct_entries  = [e for k,e in entries.items() if "Heal%"     in k]
        flat_entries = [e for k,e in entries.items() if "HealFlat" in k]

        # sync so total_hp and healing_bonus are current
        self.c.sync_stats(self.c.compute_total_stats())
        hp = self.c.total_hp
        hb = self.c.healing_bonus

        total = 0.0
        for _ in range(self.ticks()):
            for ent in pct_entries:
                total += calculate_heal(
                    base_hp       = hp,
                    heal_pct      = ent["value"]/100,
                    heal_flat     = 0,
                    healing_bonus = hb
                )
            for ent in flat_entries:
                total += calculate_heal(
                    base_hp       = 0,
                    heal_pct      = 0,
                    heal_flat     = ent["value"],
                    healing_bonus = hb
                )
        return total