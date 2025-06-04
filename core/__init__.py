# core/__init__.py
from .models import Character, Weapon
from .loaders import load_characters, load_weapons
from .talents import load_talent_multipliers, compute_combo_multiplier
from .character_buffs import apply_skill_buff
from .utils import calculate_damage
