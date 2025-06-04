# core/character_buffs.py

TALENT_MULTIPLIERS = None  # This gets populated via init

def init_buffs(multipliers):
    global TALENT_MULTIPLIERS
    TALENT_MULTIPLIERS = multipliers

def hu_tao_skill_buff(character):
    hp = character.base_stats.get("hp", 0)
    skill_level = character.skill_level
    scaling_percent = TALENT_MULTIPLIERS.get(character.name, {}) \
        .get("Skill", {}) \
        .get(skill_level, {}) \
        .get("ATK_Bonus%HP", 0) / 100
    atk_bonus = hp * scaling_percent
    character.base_stats["atk"] += atk_bonus

BUFF_FUNCTIONS = {
    "Hu Tao": hu_tao_skill_buff,
    # Add more characters here as needed
}

def apply_skill_buff(character):
    if character.name in BUFF_FUNCTIONS:
        BUFF_FUNCTIONS[character.name](character)
