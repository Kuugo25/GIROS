# core/talents.py
import csv
from collections import defaultdict
import re

def load_talent_multipliers(path="data/talent_multipliers.csv"):
    multipliers = defaultdict(
        lambda: defaultdict(
            lambda: defaultdict(dict)
        )
    )

    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            char = row["character"]
            skill = row["skill"]       # e.g., AA, Skill, Burst
            level = int(row["level"])  # e.g., 1 to 15
            hit_type = row["type"]     # e.g., N1, N2, C, etc.

            # Combine hits if needed (e.g., "59.36 + 62.8")
            raw_val = row["multiplier"]
            value = sum(float(part.strip()) for part in raw_val.split("+"))

            scaling = row.get("scaling","").strip().upper()  # e.g. "HP","ATK","BUFF"
            multipliers[char][skill][level][hit_type] = {
                "value": value,
                "scaling": scaling
            }

    return multipliers

import re


def compute_combo_hits(
    multipliers: defaultdict,
    character,        # your Character instance
    combo: str
):
    """
    Returns a list of (mult, scaling_stat) tuples for every hit.
    E.g. "12N2C Q" → 12×(N1,N2,C) + Q  yield something like:
      [(.45,"ATK"), (.57,"ATK"), (.66,"ATK"),  # 12 repeats of N1/N2/C
       ...,
       (2.33,"HP")]                              # Q
    """
    hits = []
    for seg in combo.split():
        m = re.match(r"^(\d*)(.+)$", seg)
        count = int(m.group(1) or 1)
        body  = m.group(2)

        # pick AA vs Burst & level
        if "Q" in body:
            skill = "Burst"
            lvl   = character.burst_level
        else:
            skill = "AA"
            lvl   = character.aa_level

        # expand body into tokens ["N1","N2","C"] or ["Q"]
        tokens = []
        i = 0
        while i < len(body):
            c = body[i]
            if c in ("C","Q"):
                tokens.append(c)
                i += 1
            else:  # starts with "N"
                j = i+1
                while j < len(body) and body[j].isdigit(): j+=1
                n = int(body[i+1:j])
                # check for trailing C
                extend = j < len(body) and body[j]=="C"
                if extend: j+=1
                tokens += [f"N{k}" for k in range(1,n+1)]
                if extend:
                    tokens.append("C")
                i = j

        # look up each token count×
        for _ in range(count):
            for tok in tokens:
                entry = multipliers[character.name][skill][lvl].get(tok)
                if not entry:
                    continue
                # entry == {"value": float, "scaling": "HP"/"ATK"/"BUFF"}
                hits.append((entry["value"], entry["scaling"]))
    return hits


