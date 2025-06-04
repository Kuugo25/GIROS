from core.talents import load_talent_multipliers
from core.character_buffs import init_buffs
from core.loaders import load_characters, load_weapons

TALENT_MULTIPLIERS = load_talent_multipliers("data/talent_multipliers.csv")
init_buffs(TALENT_MULTIPLIERS)

characters = load_characters("data/genshin_characters_v1.csv", "data/character_defaults.csv")
weapons = load_weapons("data/genshin_weapons_v6.csv")

hu_tao = next(c for c in characters if c.name == "Hu Tao")

damage = hu_tao.expected_damage_output(
    combo=hu_tao.default_combo,
    skill=hu_tao.default_skill,
    level=10,
    multipliers=TALENT_MULTIPLIERS,
    crit_rate=hu_tao.crit_rate,
    crit_dmg=hu_tao.crit_dmg,
    dmg_bonus=hu_tao.dmg_bonus,
    enemy_level=100,
    enemy_resistance=0.1
)

print(f"[{hu_tao.default_combo}] {hu_tao.name} Damage: {damage:.2f}")
