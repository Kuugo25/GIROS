# simulation/simulator.py
from simulation.artifact import simulate_artifact
from simulation.talent_books import simulate_multiple_talent_runs
import copy
import random

def simulate_artifact_farm(character, resin_spent=20, artifact_type=None, multipliers=None):
    if artifact_type is None:
        artifact_type = random.choice(["Flower", "Feather", "Sands", "Goblet", "Circlet"])

    if multipliers is None:
        raise ValueError("Talent multipliers must be provided.")
    result = {}

    # 1) Baseline DPS on a fresh copy
    char_before = copy.deepcopy(character)
    char_before.sync_stats(char_before.compute_total_stats())
    dmg_before = char_before.expected_damage_output(
        combo=char_before.default_combo,
        multipliers=multipliers,
        crit_rate=char_before.crit_rate,
        crit_dmg=char_before.crit_dmg,
        enemy_level=100,
        enemy_resistance=0.1
    )
    # Simulate drop
    new_artifact = simulate_artifact(artifact_type)

    # 3) Test DPS on another copy with the new piece in that slot
    char_test = copy.deepcopy(character)
    char_test.artifacts[artifact_type] = new_artifact
    char_test.sync_stats(char_test.compute_total_stats())
    dmg_after = char_test.expected_damage_output(
        combo=char_test.default_combo,
        multipliers=multipliers,
        crit_rate=char_test.crit_rate,
        crit_dmg=char_test.crit_dmg,
        enemy_level=100,
        enemy_resistance=0.1
    )

    # 4) Accept or reject
    accepted = (dmg_after > dmg_before)
    if accepted:
        # Equip the real character
        character.artifacts[artifact_type] = new_artifact
        character.sync_stats(character.compute_total_stats())
    else:
        dmg_after = dmg_before

    return {
        "resin_spent": resin_spent,
        "activity": "artifact_farm",
        "artifact_type": artifact_type,
        "artifact": new_artifact,
        "accepted": accepted,
        "damage_before": dmg_before,
        "damage_after": dmg_after,
        "dps_gain": dmg_after - dmg_before,
        "upgrade_counts": new_artifact["upgrades"]
    }

import copy

def simulate_talent_farm(character, resin_spent=60, domain_level=4, multipliers=None):
    from simulation.talent_books import simulate_multiple_talent_runs

    if multipliers is None:
        raise ValueError("Talent multipliers must be provided.")

    # --- 1) Farm books ---
    runs = resin_spent // 20
    books = simulate_multiple_talent_runs(runs=runs, domain_level=domain_level)
    # init inventory if needed
    if not hasattr(character, "book_inventory"):
        character.book_inventory = {"Teachings":0,"Guides":0,"Philosophies":0}
    for tier, qty in books.items():
        character.book_inventory[tier] += qty

    def total_teachings_avail():
        return (character.book_inventory["Teachings"]
                + character.book_inventory["Guides"] * 3
                + character.book_inventory["Philosophies"] * 9)

    # --- 2) Baseline DPS ---
    char_before = copy.deepcopy(character)
    char_before.sync_stats(char_before.compute_total_stats())
    dmg_before = char_before.expected_damage_output(
        combo=char_before.default_combo,
        multipliers=multipliers,
        crit_rate=char_before.crit_rate,
        crit_dmg=char_before.crit_dmg,
        enemy_level=100,
        enemy_resistance=0.1
    )

    # cost table
    upgrade_costs = {1:3,2:6,3:12,4:18,5:27,6:36,7:54,8:108,9:144}

    # --- 3) Greedy upgrade loop ---
    while True:
        gains = {}
        # consider each talent
        for talent in ("AA","Skill","Burst"):
            lvl = getattr(character, talent.lower()+"_level")
            if lvl >= 10:
                continue
            cost = upgrade_costs.get(lvl)
            if cost is None or total_teachings_avail() < cost:
                continue

            # simulate bumping that one talent by 1
            test = copy.deepcopy(character)
            setattr(test, talent.lower()+"_level", lvl+1)
            test.sync_stats(test.compute_total_stats())
            d_after = test.expected_damage_output(
                combo=test.default_combo,
                multipliers=multipliers,
                crit_rate=test.crit_rate,
                crit_dmg=test.crit_dmg,
                enemy_level=100,
                enemy_resistance=0.1
            )
            gains[talent] = d_after - dmg_before

        if not gains:
            break

        # pick the single best
        best = max(gains, key=gains.get)
        lvl = getattr(character, best.lower()+"_level")
        cost = upgrade_costs[lvl]

        # consume books
        remaining = cost
        for tier, val, name in [(1,1,"Teachings"), (3,1,"Guides"), (9,1,"Philosophies")]:
            use = min(character.book_inventory[name], remaining//tier)
            character.book_inventory[name] -= use
            remaining -= use * tier

        # apply the upgrade
        setattr(character, best.lower()+"_level", lvl+1)

    # --- 4) Final DPS ---
    character.sync_stats(character.compute_total_stats())
    dmg_after = character.expected_damage_output(
        combo=character.default_combo,
        multipliers=multipliers,
        crit_rate=character.crit_rate,
        crit_dmg=character.crit_dmg,
        enemy_level=100,
        enemy_resistance=0.1
    )

    return {
        "resin_spent": resin_spent,
        "activity": "talent_farm",
        "books_gained": books,
        "book_inventory": dict(character.book_inventory),
        "damage_before": dmg_before,
        "damage_after": dmg_after,
        "dps_gain": dmg_after - dmg_before,
        "talent_levels": {
            "AA": character.aa_level,
            "Skill": character.skill_level,
            "Burst": character.burst_level
        }
    }

def simulate_with_policy(character, resin_budget, policy, domain_level=4):
    results = []
    resin_remaining = resin_budget

    while resin_remaining >= 20:
        activity = policy.choose_activity(character)

        if activity == "artifact_farm":
            result = simulate_artifact_farm(
                character,
                resin_spent = 20,
                multipliers=policy.multipliers
            )
        elif activity == "talent_farm":
            result = simulate_talent_farm(character, resin_spent=20, domain_level=domain_level, multipliers=policy.multipliers)
        else:
            break

        accepted = policy.evaluate_upgrade(
            before_dps=result['damage_before'],
            after_dps=result['damage_after'],
            resin_cost=result['resin_spent']
        )

        result['accepted'] = accepted
        result['resin_remaining'] = resin_remaining
        result['dps'] = result['damage_after']
        results.append(result)

        if accepted or activity == "talent_farm":
            resin_remaining -= result['resin_spent']
        else:
            break

    return results


def compare_artifact_vs_talent_strategy(character_factory, multipliers, resin_budget=300, domain_level=4):
    """
    Compares DPS improvement from farming artifacts vs. talents using a fixed resin budget.

    Parameters:
    - character_factory: A function that returns a fresh Character instance with base stats, weapon, artifacts.
    - multipliers: Talent multiplier data.
    - resin_budget: Total resin to spend.
    - domain_level: Domain level for talent farming.
    """
    from simulation.simulator import simulate_artifact_farm, simulate_talent_farm
    import copy

    # === Prepare fresh character instances for both paths ===
    base_char = character_factory()
    char_artifacts = copy.deepcopy(base_char)
    char_talents = copy.deepcopy(base_char)

    # === Sync both characters to start clean ===
    char_artifacts.sync_stats(char_artifacts.compute_total_stats())
    char_talents.sync_stats(char_talents.compute_total_stats())

    # === Baseline DPS ===
    artifact_dps_start = char_artifacts.expected_damage_output(
        combo=char_artifacts.default_combo,
        multipliers=multipliers,
        crit_rate=char_artifacts.crit_rate,
        crit_dmg=char_artifacts.crit_dmg,
        enemy_level=100,
        enemy_resistance=0.1
    )

    # === Simulate artifact farming ===
    for _ in range(resin_budget // 20):
        simulate_artifact_farm(char_artifacts, resin_spent=20, multipliers=multipliers)

    char_artifacts.sync_stats(char_artifacts.compute_total_stats())  # Sync after upgrades

    artifact_dps_end = char_artifacts.expected_damage_output(
        combo=char_artifacts.default_combo,
        multipliers=multipliers,
        crit_rate=char_artifacts.crit_rate,
        crit_dmg=char_artifacts.crit_dmg,
        enemy_level=100,
        enemy_resistance=0.1
    )

    artifact_gain = artifact_dps_end - artifact_dps_start
    artifact_pct = artifact_gain / artifact_dps_start * 100

    # === Simulate talent farming ===
    char_talents.sync_stats(char_talents.compute_total_stats())
    talent_result = simulate_talent_farm(
        char_talents,
        resin_spent=resin_budget,
        domain_level=domain_level,
        multipliers=multipliers
    )

    # === Output comparison ===
    print("\n=== DPS Comparison ===")
    print(f"Resin Budget: {resin_budget}")

    # — always print your talent‐farm DPS before/after & Δ
    tbefore = talent_result["damage_before"]
    tafter  = talent_result["damage_after"]
    tgain = talent_result["dps_gain"]

    talent_pct = tgain / tbefore * 100 if tbefore else 0

    # — decide winner
    if (artifact_dps_end - artifact_dps_start) > tgain:
        print("\nResult: Artifact farming gave higher gains.")
    else:
        print("\nResult: Talent farming gave higher gains.")
    print(
        f"\n→ Final Talent Levels: AA {char_talents.aa_level}, Skill {char_talents.skill_level}, Burst {char_talents.burst_level}"
    )

    print(f"→ Artifact Farm: {artifact_dps_start:.2f} → {artifact_dps_end:.2f} "
          f"(Δ {artifact_gain:.2f}, {artifact_pct:+.2f}%)")

    print(f"→ Talent Farm : {tbefore:.2f} → {tafter:.2f} "
          f"(Δ {tgain:.2f}, {talent_pct:+.2f}%)")

    # --- Collect post–artifact‐farm artifacts and stats ---
    final_artifacts = char_artifacts.artifacts
    final_stats = char_artifacts.compute_total_stats()
    vision = char_artifacts.vision

    # --- Collect books gained from talent farming ---
    books_gained = talent_result["books_gained"]

    print("\n=== Post–Artifact‐Farm Artifacts ===")
    for slot, art in final_artifacts.items():
        print(f"{slot}: {art}")

    print("\n=== Post–Artifact‐Farm Stats ===")
    print(f"Total HP: {final_stats['total_hp']:.2f}")
    print(f"Total ATK: {final_stats['total_atk']:.2f}")
    print(f"Total DEF: {final_stats['total_def']:.2f}")
    print(f"Crit Rate: {final_stats['crit_rate']:.2%}")
    print(f"Crit DMG: {final_stats['crit_dmg']:.2%}")
    print(f"{vision} Bonus:   {final_stats['elemental_dmg_bonus'][vision]:.2%}")

    print("\n=== Talent Books Gained ===")
    for tier, qty in books_gained.items():
        print(f"{tier}: {qty}")

    return {
        "artifact_delta": artifact_dps_end - artifact_dps_start,
        "talent_delta": tgain,
        "final_artifacts": final_artifacts,
        "final_stats": final_stats,
        "books_gained": books_gained
    }

import copy
import random
from simulation.artifact      import simulate_artifact
from simulation.talent_books  import simulate_multiple_talent_runs

def simulate_artifact_farm_heal(
    character,
    resin_spent: int = 20,
    artifact_type: str = None,
    multipliers = None,
    metric_fn = None,
    domain_level: int = None,
    **kwargs
):
    """
    Like simulate_artifact_farm, but accept an upgrade only if it improves metric_fn.
    Returns a dict with metric_before/after/gain.
    """
    if multipliers is None or metric_fn is None:
        raise ValueError("Must provide multipliers and metric_fn.")

    # pick a slot
    if artifact_type is None:
        artifact_type = random.choice(["Flower","Feather","Sands","Goblet","Circlet"])

    # baseline metric
    before = metric_fn(character)

    # roll new artifact
    new_art = simulate_artifact(artifact_type)

    # test on a copy
    test = copy.deepcopy(character)
    test.artifacts[artifact_type] = new_art
    test.sync_stats(test.compute_total_stats())
    after = metric_fn(test)

    accepted = (after > before)
    if accepted:
        # equip for real
        character.artifacts[artifact_type] = new_art
        character.sync_stats(character.compute_total_stats())
        gain = after - before
    else:
        gain = 0.0
        after = before

    return {
        "resin_spent": resin_spent,
        "activity": "artifact_farm_heal",
        "artifact_type": artifact_type,
        "artifact": new_art,
        "accepted": accepted,
        "metric_before": before,
        "metric_after": after,
        "metric_gain": gain,
        "upgrade_counts": new_art["upgrades"],
    }


def simulate_talent_farm_heal(
    character,
    resin_spent: int = 60,
    domain_level: int = 4,
    multipliers = None,
    metric_fn = None,
):
    """
    Like simulate_talent_farm, but greedily pick the single talent‐up
    that maximizes metric_fn gain each step.
    """
    if multipliers is None or metric_fn is None:
        raise ValueError("Must provide multipliers and metric_fn.")

    # 1) Farm books
    runs = resin_spent // 20
    books = simulate_multiple_talent_runs(runs=runs, domain_level=domain_level)
    if not hasattr(character, "book_inventory"):
        character.book_inventory = {"Teachings":0,"Guides":0,"Philosophies":0}
    for tier, qty in books.items():
        character.book_inventory[tier] += qty

    def total_books():
        return (
            character.book_inventory["Teachings"]
            + character.book_inventory["Guides"] * 3
            + character.book_inventory["Philosophies"] * 9
        )

    # 2) Greedy loop
    before = metric_fn(character)
    upgrade_costs = {1:3,2:6,3:12,4:18,5:27,6:36,7:54,8:108,9:144}

    while True:
        best_gain = 0.0
        best_talent = None
        # consider AA, Skill, Burst
        for tal in ("AA","Skill","Burst"):
            lvl = getattr(character, tal.lower()+"_level")
            cost = upgrade_costs.get(lvl)
            if lvl >= 10 or cost is None or total_books() < cost:
                continue

            # simulate one‐level bump
            test = copy.deepcopy(character)
            setattr(test, tal.lower()+"_level", lvl+1)
            test.sync_stats(test.compute_total_stats())
            after = metric_fn(test)
            gain = after - before

            if gain > best_gain:
                best_gain, best_talent = gain, tal

        if best_talent is None:
            break  # no more upgrades

        # consume the required books
        need = upgrade_costs[getattr(character, best_talent.lower()+"_level")]
        for tier, val, name in [(1,1,"Teachings"),(3,1,"Guides"),(9,1,"Philosophies")]:
            use = min(character.book_inventory[name], need // tier)
            character.book_inventory[name] -= use
            need -= use * tier

        # apply the upgrade
        setattr(character, best_talent.lower()+"_level",
                getattr(character, best_talent.lower()+"_level") + 1)
        character.sync_stats(character.compute_total_stats())
        before += best_gain

    after = metric_fn(character)
    return {
        "resin_spent": resin_spent,
        "activity": "talent_farm_heal",
        "books_gained": books,
        "book_inventory": dict(character.book_inventory),
        "metric_before": before,
        "metric_after": after,
        "metric_gain": after - before,
        "talent_levels": {
            "AA": character.aa_level,
            "Skill": character.skill_level,
            "Burst": character.burst_level
        }
    }


def simulate_with_metric(
        character,
        resin_budget: int,
        multipliers,
        metric_fn,                 # (char) -> float
        artifact_runner,           # simulate_artifact_farm or simulate_artifact_farm_heal
        talent_runner,             # simulate_talent_farm or simulate_talent_farm_heal
        domain_level: int = 4,
        policy: str = "greedy_swap",
        threshold: float = None,   # for threshold_then_switch
        primary: str = "artifact", # for threshold_then_switch
        threshold_stats: dict = None  # for stat_threshold_then_swap
):
    """
    Generic loop: spend resin in 20-pt chunks, choosing actions per `policy`.

    Policies:
      - "artifact_only"
      - "talent_only"
      - "greedy_swap"
      - "threshold_then_switch"
      - "stat_threshold_then_swap":
            Farm `primary` until all keys in `threshold_stats` are met
            (character.compute_total_stats() or attributes),
            then farm the other runner until no metric gain.
    """
    results = []
    resin = resin_budget
    current = metric_fn(character)

    def run_step(runner, **kwargs):
        nonlocal current
        before = current
        out = runner(**kwargs)
        after = metric_fn(character)
        out["metric_before"] = before
        out["metric_after"]  = after
        out["metric_gain"]   = after - before
        current = after
        return out, after - before

    while resin >= 20:
        # ── stat_threshold_then_swap ──
        if policy == "stat_threshold_then_swap":
            if not threshold_stats:
                raise ValueError("‘stat_threshold_then_swap’ requires a threshold_stats dict.")

            # pick primary vs secondary runner
            prim_runner = talent_runner if primary == "talent" else artifact_runner
            sec_runner = artifact_runner if primary == "talent" else talent_runner
            prim_name = "talent" if primary == "talent" else "artifact"
            sec_name = "artifact" if primary == "talent" else "talent"

            # Phase 1: farm primary until stats met
            while resin >= 20:
                stats = character.compute_total_stats()
                if all(
                        stats.get(k, getattr(character, k, None)) >= v
                        for k, v in threshold_stats.items()
                ):
                    break

                # for artifact runner, omit domain_level arg
                if prim_runner is artifact_runner:
                    out, gain = run_step(
                        prim_runner,
                        character=character,
                        resin_spent=20,
                        multipliers=multipliers,
                        metric_fn=metric_fn
                    )
                else:
                    out, gain = run_step(
                        prim_runner,
                        character=character,
                        resin_spent=20,
                        multipliers=multipliers,
                        metric_fn=metric_fn,
                        domain_level=domain_level
                    )

                out["activity"] = f"{prim_name}_farm"
                results.append(out)
                resin -= 20

            # Phase 2: once thresholds met, farm secondary until no gain
            while resin >= 20:
                # again, drop domain_level for artifact runner
                if sec_runner is artifact_runner:
                    out, gain = run_step(
                        sec_runner,
                        character=character,
                        resin_spent=20,
                        multipliers=multipliers,
                        metric_fn=metric_fn
                    )
                else:
                    out, gain = run_step(
                        sec_runner,
                        character=character,
                        resin_spent=20,
                        multipliers=multipliers,
                        metric_fn=metric_fn,
                        domain_level=domain_level
                    )

                if gain <= 0:
                    break
                out["activity"] = f"{sec_name}_farm"
                results.append(out)
                resin -= 20

            return results

        # ── artifact_only ──
        if policy == "artifact_only":
            out, gain = run_step(
                artifact_runner,
                character=character,
                resin_spent=20,
                multipliers=multipliers,
                metric_fn=metric_fn
            )
            if gain <= 0:
                break
            out["activity"] = "artifact_only"
            results.append(out)
            resin -= 20

        # ── talent_only ──
        elif policy == "talent_only":
            out, gain = run_step(
                talent_runner,
                character=character,
                resin_spent=20,
                multipliers=multipliers,
                metric_fn=metric_fn,
                domain_level=domain_level
            )
            out["activity"] = "talent_only"
            results.append(out)
            resin -= 20

        # ── greedy_swap ──
        elif policy == "greedy_swap":
            # 1) Try artifact first
            out, gain = run_step(
                artifact_runner,
                character=character,
                resin_spent=20,
                multipliers=multipliers,
                metric_fn=metric_fn
            )
            if gain > 0:
                out["activity"] = "artifact_farm"
                results.append(out)
                resin -= 20
                continue

            # 2) Then try talent
            out, gain = run_step(
                talent_runner,
                character=character,
                resin_spent=20,
                multipliers=multipliers,
                metric_fn=metric_fn,
                domain_level=domain_level
            )
            if gain > 0:
                out["activity"] = "talent_farm"
                results.append(out)
                resin -= 20
                continue

            # 3) Neither gave gain → FALLBACK: bump **only Burst** to 10
            while resin >= 20 and character.burst_level < 10:
                out, gain = run_step(
                    talent_runner,
                    character=character,
                    resin_spent=20,
                    multipliers=multipliers,
                    metric_fn=metric_fn,
                    domain_level=domain_level
                )
                out["activity"] = "talent_farm_fallback"
                results.append(out)
                resin -= 20

            # 4) Once Burst is LEVEL 10, burn all remaining resin on artifacts
            while resin >= 20:
                out, gain = run_step(
                    artifact_runner,
                    character=character,
                    resin_spent=20,
                    multipliers=multipliers,
                    metric_fn=metric_fn
                )
                out["activity"] = "artifact_farm_fallback"
                results.append(out)
                resin -= 20

            break

        # ── threshold_then_switch ──
        elif policy == "threshold_then_switch":
            if threshold is None:
                raise ValueError("‘threshold_then_switch’ requires a threshold.")
            prim = artifact_runner if primary=="artifact" else talent_runner
            name_prim = "artifact" if primary=="artifact" else "talent"

            out, gain = run_step(
                prim,
                character=character,
                resin_spent=20,
                multipliers=multipliers,
                metric_fn=metric_fn,
                domain_level=domain_level
            )
            out["activity"] = f"{name_prim}_farm"
            results.append(out)
            resin -= 20
            if gain < threshold:
                primary = "talent" if primary=="artifact" else "artifact"
            continue

        else:
            raise ValueError(f"Unknown policy '{policy}'")

    return results






