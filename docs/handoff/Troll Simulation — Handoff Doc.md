---
type: handoff
version: v2.8
status: active
systems:
  - combat
  - loot
  - player
  - simulation
date: 2026-05-01
---

# Troll Simulation — Handoff Document

**Date:** 2026-05-01
**Version:** Alpha - World v2.8 | Play Test Simulation Pass
**Working folder:** `C:\Users\user\OneDrive\Documents\Second Brain\Craft\Text Based RPG\`

---

## Git Push Workflow

ALWAYS follow this order — the working folder is in OneDrive and is NOT the git repo:

```bat
xcopy /E /Y "C:\Users\user\OneDrive\Documents\Second Brain\Craft\Text Based RPG\game\*" "C:\dev\merchants-road\game\"
cd C:\dev\merchants-road
git add -A
git commit -m "feat: add troll_simulation.py"
git push
```

---

## Session Summary

Build a standalone simulation script (`game/troll_simulation.py`) that pits a randomly-generated PC against a gauntlet of 10 sequential Mountain Trolls. The goal is to visualise where in the gauntlet (troll 1–10) PCs tend to die, how fast HP drains across fights, and how much loot-and-potion pickup extends survival. The script produces a matplotlib chart and prints a summary table. It does **not** modify any existing game files.

---

## Objective

Answer the design question: **given a fully random skill allocation, how far does the average PC get against Mountain Trolls, and what kills them?**

---

## File to Create

```
game/troll_simulation.py
```

Run from the `game/` directory:

```bash
cd "C:\Users\user\OneDrive\Documents\Second Brain\Craft\Text Based RPG\game"
python troll_simulation.py
```

---

## Imports & Path Setup

The script must add `game/` to `sys.path` so it can import from the existing modules:

```python
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import random
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

from engine.player   import Player, SKILLS, MIN_SKILL, MAX_SKILL, STARTING_POINTS
from engine.combat   import (roll_initiative, fresh_state, calculate_damage,
                              apply_move_special, enemy_attack)
from engine.loot     import generate_loot
from data.enemies    import ENEMY_TEMPLATES, spawn_enemy
from data.items      import Item
```

---

## PC Class

Create a `PC` class (wrapper around the existing `Player` dataclass) with numpy-based random skill allocation.

```python
class PC:
    """
    Randomly allocated player character for simulation purposes.
    Skills stored internally as a numpy array; exposed to the engine
    as the standard Player dataclass.
    """

    SKILL_NAMES = SKILLS  # ['Merchantilism', 'Speechcraft', 'Martial',
                           #  'Magic', 'Stealth', 'Survival', 'Dungeoneering']

    def __init__(self, name: str = "Sim PC"):
        self.name        = name
        self.skill_array = self._random_skills()   # np.ndarray, shape (7,)
        self.player      = self._build_player()

    def _random_skills(self) -> np.ndarray:
        """
        Distribute STARTING_POINTS (100) across 7 skills.
        Each skill must be >= MIN_SKILL (5). Total must equal exactly 100.

        Method:
          1. Seed each skill with MIN_SKILL (7 × 5 = 35 points used).
          2. Distribute the remaining 65 points using a Dirichlet draw
             (alpha=1 for uniform randomness), scaled and rounded.
          3. Clamp each skill to MAX_SKILL (100) and normalise rounding
             errors so the total is exactly 100.
        """
        n          = len(self.SKILL_NAMES)
        base       = np.full(n, MIN_SKILL, dtype=int)
        pool       = STARTING_POINTS - n * MIN_SKILL   # 65 free points

        # Dirichlet sample gives a random probability vector summing to 1
        raw        = np.random.dirichlet(np.ones(n))
        extra      = np.floor(raw * pool).astype(int)

        # Fix rounding: add remainder 1 pt at a time to highest-draw skills
        deficit    = pool - extra.sum()
        order      = np.argsort(raw)[::-1]
        for i in range(deficit):
            extra[order[i]] += 1

        skills = np.clip(base + extra, MIN_SKILL, MAX_SKILL)

        # Final sanity: force total == 100 (clamp may cause drift)
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
```

---

## Troll Template

Pull the Mountain Troll directly from `ENEMY_TEMPLATES`:

```python
TROLL_TEMPLATE = next(t for t in ENEMY_TEMPLATES if t["name"] == "Mountain Troll")
```

Spawn a fresh troll for each fight:

```python
troll = spawn_enemy(TROLL_TEMPLATE)
```

---

## Combat Round Helper

Simulate one full combat between `player: Player` and a freshly spawned `troll: Enemy`. Returns `(survived: bool, hp_remaining: int, rounds_fought: int)`.

```python
def fight_troll(player: Player) -> tuple[bool, int, int]:
    """
    Simulate one PC vs Mountain Troll fight using the real combat engine.
    Returns (survived, hp_after_fight, rounds).
    Player HP is mutated in place.
    """
    troll  = spawn_enemy(TROLL_TEMPLATE)
    state  = fresh_state()
    rounds = 0

    player_first = roll_initiative(player, troll)

    while player.is_alive() and troll.is_alive():
        rounds += 1

        # ── Player's turn ──────────────────────────────────────────────
        if player_first or rounds > 1:
            move      = random.choice(player.combat_moves())
            dmg, _, _, _ = calculate_damage(
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

        # ── Enemy's turn ───────────────────────────────────────────────
        dmg, _, _ = enemy_attack(troll, player, state)
        player.take_damage(dmg)

        player_first = True   # after round 1 always both act

    return player.is_alive(), player.hp, rounds
```

---

## Loot & Auto-Equip Helper

After each troll kill, generate one loot item (bias = "rare", matching the troll's `loot_bias`). Auto-equip weapons and armor if they are better than what the player currently has. Add potions to inventory.

```python
def process_loot(player: Player) -> Item:
    """
    Generate one loot item from a Mountain Troll kill.
    Auto-equip weapons and armor if better than current.
    Add potions/consumables to inventory.
    Returns the item that was generated.
    """
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

    # Everything else goes to inventory (if space)
    if player.can_carry():
        player.inventory.append(item)

    return item
```

---

## Potion Use Rule

After every fight (win or lose), scan the player's inventory for healing potions. Use a potion **immediately** if `hp_missing >= potion_heal_value`. Process the cheapest (lowest heal) potion first to preserve stronger ones, repeating until no eligible potion remains or HP is full.

Parse heal value from the `effect` string (format: `"heal_N"` where N is the HP amount):

```python
def _heal_value(item: Item) -> int:
    """Extract heal amount from effect string, e.g. 'heal_30' → 30. Returns 0 if not a heal."""
    if item.item_type == "potion" and item.effect and item.effect.startswith("heal_"):
        try:
            return int(item.effect.split("_")[1])
        except (IndexError, ValueError):
            return 0
    return 0


def use_potions(player: Player):
    """
    Use healing potions from inventory when HP missing >= potion heal value.
    Uses weakest eligible potion first. Repeats until no eligible potion or HP full.
    """
    changed = True
    while changed and player.hp < player.max_hp:
        changed = False
        # Sort by heal value ascending (use smallest eligible first)
        potions = sorted(
            [item for item in player.inventory if _heal_value(item) > 0],
            key=_heal_value
        )
        for potion in potions:
            hp_missing = player.max_hp - player.hp
            heal_val   = _heal_value(potion)
            if hp_missing >= heal_val:
                player.heal(heal_val)
                player.remove_item(potion)
                changed = True
                break   # restart scan after each use
```

---

## Gauntlet Runner

Run one full gauntlet (PC vs trolls 1–10 sequentially). Returns a list of HP snapshots at the start of each fight (index 0 = starting HP before fight 1, index N = HP entering fight N+1). The list ends when the PC dies or completes all 10.

```python
NUM_TROLLS = 10

def run_gauntlet(pc: PC) -> list[int]:
    """
    Gauntlet: PC fights Mountain Trolls 1-10 sequentially.
    After each win: collect loot, auto-equip, use eligible potions.
    Ends when PC reaches 0 HP or all 10 trolls are defeated.

    Returns hp_trace: list of HP values recorded BEFORE each fight.
    Length = number of fights attempted (1–10).
    The final element is the HP the PC had when they entered their last fight.
    If they died, player.hp == 0 after the last fight.
    """
    player   = pc.player
    hp_trace = []

    for troll_num in range(1, NUM_TROLLS + 1):
        hp_trace.append(player.hp)
        survived, _, _ = fight_troll(player)

        if not survived:
            break

        # Post-fight: loot, equip, potions
        process_loot(player)
        use_potions(player)

    return hp_trace
```

---

## Simulation Loop

Run 10 independent gauntlets with fresh PCs each time. Collect results for charting.

```python
NUM_SIMS = 10

def run_simulation() -> list[dict]:
    """
    Run NUM_SIMS independent gauntlets.
    Returns list of result dicts:
      {
        'pc':         PC instance,
        'hp_trace':   list[int],   # HP before each fight (len = fights attempted)
        'died_on':    int,         # troll number that killed PC (None if survived all 10)
        'survived':   bool,
      }
    """
    results = []
    for i in range(NUM_SIMS):
        pc      = PC(name=f"PC_{i+1}")
        trace   = run_gauntlet(pc)
        # PC died if their last recorded HP entry was followed by death
        # i.e., they didn't reach all NUM_TROLLS fights AND pc.player.hp == 0
        survived = (len(trace) == NUM_TROLLS and pc.player.hp > 0)
        died_on  = None if survived else len(trace)
        results.append({
            "pc":       pc,
            "hp_trace": trace,
            "died_on":  died_on,
            "survived": survived,
        })
    return results
```

---

## Chart Spec

Produce a matplotlib line chart with the following properties:

- **Figure size:** 12 × 6
- **Title:** `"PC vs Mountain Troll — 10-Gauntlet Survival Simulation"`
- **X-axis:** Troll number 1–10 (label: `"Troll #"`, integer ticks)
- **Y-axis:** HP (label: `"PC HP"`, range 0–110)
- **One line per simulation:** plot HP trace from fight 1 to the last fight survived
  - x values = `[1, 2, ..., len(hp_trace)]`
  - y values = `hp_trace`
  - Label each line `"PC_N (died T#)" ` or `"PC_N (survived)"`
- **Death marker:** red `×` (marker `'x'`, size 12, linewidth 2) at the point of death `(died_on, 0)`
- **Horizontal reference lines:**
  - Green dashed at y=100 (full HP)
  - Orange dashed at y=50 (danger zone)
  - Red dashed at y=0
- **Legend:** outside the chart on the right (`bbox_to_anchor=(1.05, 1)`)
- **Grid:** light grey, alpha 0.4
- **Save to:** `C:\Users\user\OneDrive\Documents\Second Brain\Craft\Text Based RPG\docs\play-tests\troll_simulation_chart.png`
- **Also call** `plt.show()`

```python
def plot_results(results: list[dict]):
    fig, ax = plt.subplots(figsize=(12, 6))

    colors = plt.cm.tab10.colors

    for i, r in enumerate(results):
        trace    = r["hp_trace"]
        x        = list(range(1, len(trace) + 1))
        label    = f"{r['pc'].name} ({'survived' if r['survived'] else f'died T{r[\"died_on\"]}'})"
        color    = colors[i % len(colors)]

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
    print(f"\nChart saved → {out_path}")
    plt.show()
```

---

## Summary Table

Print a readable summary after the simulation:

```python
def print_summary(results: list[dict]):
    print("\n" + "═" * 60)
    print("  TROLL GAUNTLET — SIMULATION RESULTS")
    print("═" * 60)
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
    print("─" * 60)
    for r in results:
        dom_skill = max(r["pc"].player.skills, key=lambda k: r["pc"].player.skills[k])
        outcome   = "SURVIVED" if r["survived"] else f"DIED  @ Troll #{r['died_on']}"
        print(f"  {r['pc'].name:<8}  dominant={dom_skill:<16}  {outcome}")
    print("═" * 60 + "\n")
```

---

## Entry Point

```python
if __name__ == "__main__":
    np.random.seed(None)   # fresh seed each run; set to int for reproducibility
    random.seed(None)

    results = run_simulation()
    print_summary(results)
    plot_results(results)
```

---

## Dependencies

- `numpy` — for skill array allocation (`pip install numpy`)
- `matplotlib` — for charting (`pip install matplotlib`)
- All other imports are from the existing game codebase — no new files needed.

---

## Files Modified

| File | Change |
|------|--------|
| `game/troll_simulation.py` | **New file** — standalone simulation script |

No existing game files are touched.

---

## Known Edge Cases to Handle

| Situation | Resolution |
|-----------|-----------|
| Player has no weapon equipped | `player.combat_moves()` returns unarmed moves via `get_moves_for_weapon(None)` — already handled in the engine |
| Loot item is a book / grimtotem / material | Falls through to inventory append; won't break anything |
| Inventory full (12 items) | `can_carry()` returns False — loot item is silently skipped |
| Potion effect string is not `heal_N` format | `_heal_value()` returns 0, item is skipped |
| All 10 trolls defeated (PC survived) | `died_on = None`, no death marker plotted |
| Skill allocation rounding drift | Handled in `_random_skills()` — total is forced to exactly 100 |

---

## Next Steps After Simulation

Once results are reviewed, likely follow-up actions:

- Adjust Mountain Troll stat ranges if average death is too early (< troll 3) or too late (> troll 8)
- Test with fixed archetype PCs (e.g. heavy Martial vs heavy Magic) to isolate which builds survive longest
- Add a second chart tracking HP drain per round (average damage taken per fight)
- Consider whether loot-from-trolls meaningfully shifts survival odds (compare with/without loot variant)
