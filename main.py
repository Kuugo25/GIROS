from core.loaders import load_characters, load_weapons

CHAR_FILE = "data/genshin_characters_v1.csv"
WEAPON_FILE = "data/genshin_weapons_v6.csv"

characters = load_characters(CHAR_FILE)
weapons = load_weapons(WEAPON_FILE)

# Example output
print(characters[0])
print(weapons[0])
