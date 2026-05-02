import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import random
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

from engine.player  import Player, SKILLS, MIN_SKILL, MAX_SKILL, STARTING_POINTS
from engine.combat  import (roll_initiative, fresh_state, calculate_damage,
                             apply_move_special, enemy_attack)
from engine.loot    import generate_loot
from data.enemies   import ENEMY_TEMPLATES, spawn_enemy
from data.items     import Item


# ── PC wrapper ───────────────────────────────────────────────────────────────

class PC:
    SKILL_NAMES = SKILLS

    def __init__(self, name: str = "Sim PC"):
        self.name        = name
        self.skill_array = self._random_skills()
        self.player      = self._build_player()

    def _random_skills(self) -> np.ndarray:
        n     = len(self.SKILL_NAMES)
        base  = np.full(n, MIN_SKILL, dtype=int)
        pool  = STARTING_POINTS - n * MIN_SKILL

        raw   = np.random.dirichlet(np.ones(n))
        extra = np.floor(raw * pool).astype(int)

        deficit = pool - extra.sum()
        order   = np.argsort(raw)[::-1]
        for i in range(deficit):
            extra[order[i]] += 1

        skills = np.clip(base + extra, MIN_SKILL, MAX_SKILL)

        diff = STARTING_POINTS - skills.sum()
        if diff != 0:
            idx = int(np.argmax(skills)) if diff < 0 else int(np.argmin(skills))
            skills[idx] += diff

        return skills

    def _build_player(self) -> Player:
        skill_dict = {name: int(v) for name, v in zip(self.SKILL_NAMES, self.skill_array)}
        p          = Player(name=self.name, skills=skill_dict)
        p.mana     = min(20, p.max_mana)
        return p

    def summary(self) -> str:
        lines = [f"PC: {self.name}"]
        for name, val in zip(self.SKILL_NAMES, self.skill_array):
            lines.append(f"  {name:<16} {val:>3}")
        return "\n".join(lines)


# ── Troll template ────────────────────────────────────────────────────────────

TROLL_TEMPLATE = next(t for t in ENEMY_TEMPLATES if t["name"] == "Mountain Troll")


# ── Fight helper ──────────────────────────────────────────────────────────────

def fight_troll(player: Player) -> tuple:
    troll  = spawn_enemy(TROLL_TEMPLATE)
    state  = fresh_state()
    rounds = 0

    player_first = roll_initiative(player, troll)

    while player.is_alive() and troll.is_alive():
        rounds += 1

        if player_first or rounds > 1:
            move          = random.choice(player.combat_moves())
            dmg, _, _, _  = calculate_damage(
                attacker_combat  = player.skill("Martial"),
                defender_defense = troll.defense_skill,
                move_name        = move,
                armor_type       = troll.armor_type,
                player           = player,
                state            = state,
            )
            apply_move_special(move, state, player, troll)
            troll.take_damage(dmg)
            if not troll.is_alive():
                break

        dmg, _, _ = enemy_attack(troll, player, state)
        player.take_damage(dmg)

        player_first = True

    return player.is_alive(), player.hp, rounds


# ── Loot helpers ──────────────────────────────────────────────────────────────

def process_loot(player: Player) -> Item:
    item = generate_loot(bias="rare")

    if item.item_type == "weapon":
        current = player.equipped.get("weapon")
        if current is None or item.base_value > current.base_value:
            if current:
                player.inventory.append(current)
            player.equipped["weapon"] = item
            return item

    elif item.item_type == "armor":
        current = player.equipped.get("armor")
        if current is None or item.armor_value > current.armor_value:
            if current:
                player.inventory.append(current)
            player.equipped["armor"] = item
            return item

    elif item.item_type in ("ring", "necklace"):
        slot = item.item_type
        if player.equipped.get(slot) is None:
            player.equipped[slot] = item
            return item

    if player.can_carry():
        player.inventory.append(item)

    return item


def _heal_value(item: Item) -> int:
    if item.item_type == "potion" and item.effect and item.effect.startswith("heal_"):
        try:
            return int(item.effect.split("_")[1])
        except (IndexError, ValueError):
            return 0
    return 0


def use_potions(player: Player):
    changed = True
    while changed and player.hp < player.max_hp:
        changed = False
        potions = sorted(
            [item for item in player.inventory if _heal_value(item) > 0],
            key=_heal_value,
        )
        for potion in potions:
            hp_missing = player.max_hp - player.hp
            heal_val   = _heal_value(potion)
            if hp_missing >= heal_val:
                player.heal(heal_val)
                player.remove_item(potion)
                changed = True
                break


# ── Gauntlet ──────────────────────────────────────────────────────────────────

NUM_TROLLS = 10


def run_gauntlet(pc: PC) -> list:
    player   = pc.player
    hp_trace = []

    for troll_num in range(1, NUM_TROLLS + 1):
        hp_trace.append(player.hp)
        survived, _, _ = fight_troll(player)

        if not survived:
            break

        process_loot(player)
        use_potions(player)

    return hp_trace


# ── Simulation loop ───────────────────────────────────────────────────────────

NUM_SIMS = 10


def run_simulation() -> list:
    results = []
    for i in range(NUM_SIMS):
        pc       = PC(name=f"PC_{i+1}")
        trace    = run_gauntlet(pc)
        survived = (len(trace) == NUM_TROLLS and pc.player.hp > 0)
        died_on  = None if survived else len(trace)
        results.append({
            "pc":       pc,
            "hp_trace": trace,
            "died_on":  died_on,
            "survived": survived,
        })
    return results


# ── Chart ─────────────────────────────────────────────────────────────────────

def plot_results(results: list):
    fig, ax = plt.subplots(figsize=(12, 6))
    colors  = plt.cm.tab10.colors

    for i, r in enumerate(results):
        trace = r["hp_trace"]
        x     = list(range(1, len(trace) + 1))
        died_str = f"died T{r['died_on']}"
        label    = f"{r['pc'].name} ({'survived' if r['survived'] else died_str})"
        color = colors[i % len(colors)]

        ax.plot(x, trace, marker='o', markersize=5, label=label, color=color)

        if not r["survived"]:
            ax.plot(r["died_on"], 0, marker='x', markersize=12,
                    markeredgewidth=2, color='red', zorder=5)

    ax.axhline(y=100, color='green',  linestyle='--', alpha=0.5, linewidth=1, label='Full HP')
    ax.axhline(y=50,  color='orange', linestyle='--', alpha=0.5, linewidth=1, label='Danger (50)')
    ax.axhline(y=0,   color='red',    linestyle='--', alpha=0.4, linewidth=1)

    ax.set_title("PC vs Mountain Troll — 10-Gauntlet Survival Simulation", fontsize=14, pad=12)
    ax.set_xlabel("Troll #", fontsize=11)
    ax.set_ylabel("PC HP", fontsize=11)
    ax.set_xlim(0.5, NUM_TROLLS + 0.5)
    ax.set_ylim(-5, 115)
    ax.xaxis.set_major_locator(ticker.MultipleLocator(1))
    ax.grid(True, color='grey', alpha=0.4, linewidth=0.5)
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9)

    fig.tight_layout()
    out_path = (
        r"C:\Users\user\OneDrive\Documents\Second Brain\Craft\Text Based RPG"
        r"\docs\play-tests\troll_simulation_chart.png"
    )
    plt.savefig(out_path, dpi=150, bbox_inches='tight')
    print(f"\nChart saved -> {out_path}")
    plt.show()


# ── Summary table ─────────────────────────────────────────────────────────────

def print_summary(results: list):
    print("\n" + "=" * 60)
    print("  TROLL GAUNTLET -- SIMULATION RESULTS")
    print("=" * 60)
    deaths      = [r for r in results if not r["survived"]]
    survivors   = [r for r in results if r["survived"]]
    death_tolls = [r["died_on"] for r in deaths]

    print(f"  Simulations run : {len(results)}")
    print(f"  Survived all 10 : {len(survivors)}")
    print(f"  Deaths          : {len(deaths)}")
    if death_tolls:
        print(f"  Avg death on    : Troll #{sum(death_tolls)/len(death_tolls):.1f}")
        print(f"  Earliest death  : Troll #{min(death_tolls)}")
        print(f"  Latest death    : Troll #{max(death_tolls)}")
    print("-" * 60)
    for r in results:
        dom_skill = max(r["pc"].player.skills, key=lambda k: r["pc"].player.skills[k])
        outcome   = "SURVIVED" if r["survived"] else f"DIED  @ Troll #{r['died_on']}"
        print(f"  {r['pc'].name:<8}  dominant={dom_skill:<16}  {outcome}")
    print("=" * 60 + "\n")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    np.random.seed(None)
    random.seed(None)

    results = run_simulation()
    print_summary(results)
    plot_results(results)
