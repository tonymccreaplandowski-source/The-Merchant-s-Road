---
type: coding-doc
version: v2.7→v2.8
status: active
systems:
  - stealth
  - ui
  - character
---

# Pickpocket Mini-Game — Coding Document for Claude Code
**Target Version:** v2.7 → v2.8
**Session context:** Play Test 13 — new feature addition
**Tone reference:** Oblivion-flavored (light, roguish, street-level)

---

## Overview

This document specifies two things:

1. **PT13 outstanding item** — Hunger stat visible on the road travel map HUD (small change, do this first)
2. **Pickpocket mini-game** — Full new system: `engine/pickpocket.py` + wired into `ui/city.py`

Do not add any features not listed here. Do not refactor unrelated code.

---

## Part 1 — Hunger on the Road HUD (small fix)

**File:** `ui/display.py` — function `show_world_map(player)`

**Current status bar line (around line 529):**
```python
print(
    f"{C.BGREEN}HP{C.RESET} {player.hp}/{player.max_hp}   "
    f"{C.BYELLOW}Gold{C.RESET} {player.gold}gp   "
    f"{C.BCYAN}Bag{C.RESET} {len(player.inventory)}/{12} items"
)
```

**Change:** Append a hunger indicator to this line when the player is `on_road`. When in a city, hunger is already on the character sheet — do not add it there.

Logic for hunger color/label (mirrors the character sheet logic already in `show_world_map`):
- `hunger >= 60` → `C.BGREEN`, label `"Fed"`
- `hunger >= 30` → `C.BYELLOW`, label `"Hungry"`
- `hunger >= 10` → `C.BRED`, label `"Starving"`
- `hunger < 10`  → `C.BRED`, label `"Critical"`

Only show the hunger stat when `player.on_road` is True. When in a city the status bar should remain unchanged.

The `hunger` value lives at `player.hunger` (int, 0–100), added in v2.7.

---

## Part 2 — Pickpocket Mini-Game

### 2.1 — Player State Additions

**File:** `engine/player.py` — `Player` dataclass

Add these two fields after the `days_elapsed` field (near the bottom of the dataclass):

```python
# Pickpocket / underworld state
city_heat:   Dict[str, int]  = field(default_factory=dict)   # heat per city key, 0–100
city_wanted: set             = field(default_factory=set)     # set of city keys where player is wanted
```

`city_heat` is a dict keyed by city string (e.g. `"ashenvale"`, `"caldervast"`). Values are integers 0–100.
`city_wanted` is a set of city key strings.

Both reset naturally on player death (Player object is destroyed). No save system. They persist for the life of the play session.

**Heat decay:** Heat decays passively based on `days_elapsed`. This is handled inside `pickpocket.py` when the prowl screen is entered — see Section 2.3.

---

### 2.2 — Guard Enemy (for Wanted system)

**File:** `data/enemies.py` — `ENEMY_TEMPLATES` list

Add this template to the list. It should not appear in any biome pool (it is spawned directly by `pickpocket.py`, not through `get_enemy_for_biome`):

```python
{
    "name":           "City Guard",
    "armor_type":     "mail",
    "hp_range":       (80, 110),
    "combat_range":   (55, 75),
    "defense_range":  (45, 65),
    "agility_range":  (30, 50),
    "description":    "A heavyset guard in city colours. He's seen your face before.",
    "biomes":         [],
    "loot_bias":      "uncommon",
    "enemy_type":     "combat",
    "enemy_spells":   [],
    "moves":          ["Strike", "Bash", "Shove"],
},
```

Also add a helper function at the bottom of `data/enemies.py` (alongside `get_enemy_for_biome`):

```python
def spawn_city_guard() -> Enemy:
    template = next(t for t in ENEMY_TEMPLATES if t["name"] == "City Guard")
    return spawn_enemy(template)
```

---

### 2.3 — City Entry Wanted Check

**File:** `ui/city.py` — `city_loop(player)` function

At the very top of `city_loop`, before the while loop begins, add a wanted check:

```python
from data.enemies import spawn_city_guard

city_key = player.current_city
if city_key in player.city_wanted:
    clear()
    title_screen("CITY GATES")
    print(f"\n  {C.BRED}A guard steps out of the gatehouse. He's been waiting.{C.RESET}")
    print(f'  {C.DIM}"There you are. We\'ve had reports. You\'re coming with me."{C.RESET}')
    print()
    pause("Press Enter to face him...")
    guard = spawn_city_guard()
    won = run_combat(player, guard)
    if not player.is_alive():
        from ui.road import game_over
        game_over(player)
        return
    if won:
        player.city_wanted.discard(city_key)
        player.city_heat[city_key] = min(100, player.city_heat.get(city_key, 0) + 20)
        print(f"\n  {C.BYELLOW}You stand over him. For now, you're free — but the city has a long memory.{C.RESET}")
        pause()
    else:
        # player fled combat — they're back on road, return
        return
```

Note: `run_combat` is already imported at the top of `city.py` (check and add if not).

---

### 2.4 — "Prowl" City Menu Option

**File:** `ui/city.py` — `city_loop(player)` — the options list and choice dispatch

Add `"Prowl"` as a new menu option. It must be gated: if `player.skill("Stealth") < 10`, show it dimmed and unselectable.

In the options list, replace one of the existing entries or append before Travel:

```python
stealth_val = player.skill("Stealth")
if stealth_val >= 10:
    prowl_label = f"Prowl             {C.DIM}(work the streets — Stealth: {stealth_val}){C.RESET}"
else:
    prowl_label = f"{C.BBLACK}Prowl             (requires 10 Stealth — yours: {stealth_val}){C.RESET}"
```

Add it to the options list between "Rest at the Inn" and "Character Sheet" (or wherever fits the current order — just before Travel).

In the dispatch block:
```python
elif choice == <prowl_index>:
    if player.skill("Stealth") >= 10:
        from engine.pickpocket import prowl_screen
        prowl_screen(player)
        if not player.is_alive():
            from ui.road import game_over
            game_over(player)
            return
    else:
        print(f"\n  {C.BBLACK}You don't move quietly enough to work a crowd.{C.RESET}")
        pause()
```

Adjust all subsequent `elif choice ==` indices accordingly.

---

### 2.5 — New File: `engine/pickpocket.py`

Create this file from scratch. Full specification follows.

#### Imports

```python
import random
from engine.player import Player
from ui.display import C, clear, pause, title_screen, prompt_choice, play_melody, hr, section, typewrite
```

---

#### Mark Table

```python
MARKS = [
    # (name, desc, min_stealth, gold_min, gold_max, awareness, is_connected)
    # is_connected = True means caught triggers guard involvement, not just mark
    ("Drunk Beggar",         "Barely upright. Probably empty.",              0,   1,   8,  10, False),
    ("Weary Traveller",      "Road-worn. Staring into nothing.",            15,   6,  18,  20, False),
    ("City Peasant",         "Busy with errands. Alert enough.",            25,  10,  28,  30, False),
    ("Market Vendor",        "Eyes on their stall, not their purse.",       35,  18,  45,  40, False),
    ("Touring Merchant",     "Fat purse. Used to being comfortable.",       45,  30,  70,  50, False),
    ("Minor Noble",          "Draped in entitlement. Richer than they look.",60, 50, 110,  60, False),
    ("City Magistrate",      "Sharp eyes. Connected. Dangerous.",           75,  70, 160,  75, True),
    ("Guild Master",         "Moves like someone who expects to be watched.",85, 90, 220,  85, True),
]
```

---

#### Heat Decay Function

```python
def _decay_heat(player: Player, city_key: str) -> None:
    """Decay city heat based on days elapsed since last visit.
    Called each time prowl_screen is entered. Uses days_elapsed as a proxy for time away.
    Heat decays by 5 per 3 days elapsed (tracked cumulatively via a stored baseline).
    Simple approach: store nothing — just cap decay at 30 max per visit.
    Decay is 5 per 2 days elapsed since last prowl, capped at 30."""
    heat = player.city_heat.get(city_key, 0)
    if heat <= 0:
        return
    # Decay: 5 per 2 days of travel. We don't track last-prowl day, so use a 
    # simple heuristic: reduce by (days_elapsed // 2) * 5, capped at 30, floored at 0.
    # This will over-decay on repeated visits same session but that's fine — it's not saved.
    decay = min(30, (player.days_elapsed // 2) * 5)
    player.city_heat[city_key] = max(0, heat - decay)
```

> **Note:** This is intentionally simple. Days elapsed is a global counter on the player, not a per-city timestamp. The result is mild and forgiving decay — heat never fully clears unless the player travels extensively.

---

#### Mark Selection

```python
def _select_mark(player: Player, city_key: str) -> tuple:
    """Return the best mark available based on player Stealth. 
    You always find a mark — quality depends on Stealth.
    Heat increases mark awareness."""
    stealth = player.skill("Stealth")
    available = [m for m in MARKS if stealth >= m[2]]
    if not available:
        available = [MARKS[0]]
    
    # Weight toward higher-tier marks but not exclusively
    weights = [i + 1 for i in range(len(available))]
    mark = random.choices(available, weights=weights, k=1)[0]
    
    # Heat penalty: each 20 heat adds 10 to mark awareness (up to +40)
    heat = player.city_heat.get(city_key, 0)
    heat_awareness_bonus = min(40, (heat // 20) * 10)
    
    name, desc, min_stl, gold_min, gold_max, base_awareness, is_connected = mark
    effective_awareness = base_awareness + heat_awareness_bonus
    
    return name, desc, gold_min, gold_max, effective_awareness, is_connected
```

---

#### Caught Resolution

```python
def _caught_screen(player: Player, city_key: str, mark_name: str, is_connected: bool, gold_stolen: int) -> str:
    """
    Handle being caught. Returns one of:
      "escaped"   — player got away clean
      "paid_off"  — player paid a fine
      "talked_out"— player talked their way clear
      "fought_won"— player fought and won
      "wanted"    — player fought and fled / situation escalated to wanted
      "dead"      — player died in combat (caller checks player.is_alive())
    """
    from data.enemies import spawn_city_guard
    from ui.combat_loop import run_combat

    stealth    = player.skill("Stealth")
    speechcraft= player.skill("Speechcraft")
    martial    = player.skill("Martial")

    clear()
    title_screen("CAUGHT")

    # Oblivion-flavored mark dialogue — rotate on mark type
    caught_lines = {
        "Drunk Beggar":      '"Oi! My coin! Thief! Someone— someone help!"',
        "Weary Traveller":   '"What — hey! Get your hand out of my— stop him!"',
        "City Peasant":      '"Thief! Thief in the market! Guard! GUARD!"',
        "Market Vendor":     '"I felt that, you little rat. Hands where I can see them."',
        "Touring Merchant":  '"Oh, how bold. Do you have any idea who I deal with?"',
        "Minor Noble":       '"How DARE you. Do you know who I am? Guards! GUARDS!"',
        "City Magistrate":   '"Step. Away. Slowly. And pray I\'m in a forgiving mood."',
        "Guild Master":      '"Interesting choice. I\'ll give you one breath to explain yourself."',
    }
    line = caught_lines.get(mark_name, '"Stop right there!"')
    print(f"\n  {C.BRED}You've been caught.{C.RESET}")
    print(f"  {C.DIM}{line}{C.RESET}")
    print()

    fine = gold_stolen + (gold_stolen // 2) + random.randint(5, 15)

    options = [
        f"Run               {C.DIM}[Stealth: {stealth}] — bolt and hope{C.RESET}",
        f"Talk your way out {C.DIM}[Speechcraft: {speechcraft}] — deny everything{C.RESET}",
        f"Intimidate        {C.DIM}[Martial: {martial}] — threaten them into silence{C.RESET}",
        f"Pay the fine      {C.DIM}({fine}gp — end this cleanly){C.RESET}",
        f"Fight             {C.DIM}[Martial: {martial}] — desperate option{C.RESET}",
    ]
    choice = prompt_choice(options, "Your move")

    # ── Run ──────────────────────────────────────────────────────────────────
    if choice == 1:
        roll = random.randint(1, 20) + stealth // 4
        threshold = 12 + (30 // 10)  # base 12, harder for connected marks
        if is_connected:
            threshold += 4
        if roll >= threshold:
            print(f"\n  {C.BGREEN}You spin and bolt through the crowd. By the time they react, you're gone.{C.RESET}")
            pause()
            return "escaped"
        else:
            print(f"\n  {C.BRED}You shove through the crowd but a hand catches your collar.{C.RESET}")
            print(f"  {C.DIM}You've only made it worse.{C.RESET}")
            pause()
            # Failed run = wanted status, no fine option remains
            player.city_wanted.add(city_key)
            player.city_heat[city_key] = min(100, player.city_heat.get(city_key, 0) + 25)
            print(f"\n  {C.BRED}You're known in this city now. The guard will be watching for you.{C.RESET}")
            pause()
            return "wanted"

    # ── Talk your way out ────────────────────────────────────────────────────
    elif choice == 2:
        roll = random.randint(1, 20) + speechcraft // 4
        threshold = 14 if is_connected else 11
        if roll >= threshold:
            print(f"\n  {C.BGREEN}\"What? Me? I stumbled — I was trying to catch them before they fell.\"")
            print(f"  {C.DIM}They don't fully believe you, but the crowd is watching and the accusation is thin.{C.RESET}")
            print(f"  {C.BYELLOW}They let it go. This time.{C.RESET}")
            pause()
            return "talked_out"
        else:
            print(f"\n  {C.BRED}Your story falls apart under their stare. They're not buying it.{C.RESET}")
            # Failed talk = heat goes up, escalate to fine or wanted
            player.city_heat[city_key] = min(100, player.city_heat.get(city_key, 0) + 15)
            if is_connected:
                player.city_wanted.add(city_key)
                print(f"  {C.BRED}They call for the guard. You're wanted in this city.{C.RESET}")
                pause()
                return "wanted"
            else:
                print(f"  {C.BYELLOW}They demand the fine: {fine}gp.{C.RESET}")
                if player.gold >= fine:
                    player.gold -= fine
                    print(f"  {C.DIM}You hand it over. They watch you go with hard eyes.{C.RESET}")
                    pause()
                    return "paid_off"
                else:
                    print(f"  {C.BRED}You don't have enough. They don't accept credit.{C.RESET}")
                    player.city_wanted.add(city_key)
                    pause()
                    return "wanted"

    # ── Intimidate ───────────────────────────────────────────────────────────
    elif choice == 3:
        roll = random.randint(1, 20) + martial // 4
        # Connected marks resist intimidation hard
        threshold = 18 if is_connected else 13
        if roll >= threshold:
            print(f"\n  {C.BGREEN}You lean in close. Your hand rests on your weapon.{C.RESET}")
            print(f'  {C.DIM}"Make a sound and I\'ll give you a reason to."')
            print(f"  {C.BYELLOW}They go pale. They say nothing. You walk.{C.RESET}")
            pause()
            return "escaped"
        else:
            if is_connected:
                print(f"\n  {C.BRED}They don't flinch. \"Guards! Assault and theft!\" You've escalated this badly.{C.RESET}")
                player.city_wanted.add(city_key)
                player.city_heat[city_key] = min(100, player.city_heat.get(city_key, 0) + 30)
                pause()
                return "wanted"
            else:
                print(f"\n  {C.BRED}They're not as scared as you hoped. They've found their voice.{C.RESET}")
                player.city_heat[city_key] = min(100, player.city_heat.get(city_key, 0) + 10)
                print(f"  {C.BYELLOW}They demand the fine: {fine}gp.{C.RESET}")
                if player.gold >= fine:
                    player.gold -= fine
                    print(f"  {C.DIM}You pay. They back off, shaken but satisfied.{C.RESET}")
                    pause()
                    return "paid_off"
                else:
                    player.city_wanted.add(city_key)
                    print(f"  {C.BRED}You can't pay. They scream. You're wanted.{C.RESET}")
                    pause()
                    return "wanted"

    # ── Pay the fine ─────────────────────────────────────────────────────────
    elif choice == 4:
        if player.gold >= fine:
            player.gold -= fine
            print(f"\n  {C.BYELLOW}You hand over the gold without a word.{C.RESET}")
            print(f"  {C.DIM}They watch you go. Smarter than you looked, apparently.{C.RESET}")
            pause()
            return "paid_off"
        else:
            print(f"\n  {C.BRED}You don't have {fine}gp. They're not sympathetic.{C.RESET}")
            player.city_wanted.add(city_key)
            player.city_heat[city_key] = min(100, player.city_heat.get(city_key, 0) + 20)
            print(f"  {C.BRED}They call it in. You're wanted.{C.RESET}")
            pause()
            return "wanted"

    # ── Fight ────────────────────────────────────────────────────────────────
    elif choice == 5:
        from data.enemies import spawn_city_guard
        from ui.combat_loop import run_combat

        print(f"\n  {C.BRED}You reach for your weapon. This was always going to get ugly.{C.RESET}")
        pause("Press Enter to fight...")

        if is_connected:
            # Connected marks summon a guard — fight two enemies sequentially
            print(f"\n  {C.BRED}A guard was already nearby. You're surrounded.{C.RESET}")
            pause()
            guard = spawn_city_guard()
            won = run_combat(player, guard)
            if not player.is_alive():
                return "dead"
            if not won:
                player.city_wanted.add(city_key)
                return "wanted"
            # Second fight: the mark's hired thug / personal guard (weaker guard)
            guard2 = spawn_city_guard()
            won = run_combat(player, guard2)
            if not player.is_alive():
                return "dead"
            if not won:
                player.city_wanted.add(city_key)
                return "wanted"
        else:
            # Fight just the mark (use a weakened guard template — common citizen)
            # Represent as a weaker enemy: improvise from a low-tier enemy
            from data.enemies import ENEMY_TEMPLATES, spawn_enemy
            # Use the "City Peasant Brawler" — we'll define this inline as a pseudo-template
            brawler_template = {
                "name":           f"Angry {mark_name}",
                "armor_type":     "none",
                "hp_range":       (20, 40),
                "combat_range":   (15, 28),
                "defense_range":  (8,  18),
                "agility_range":  (20, 40),
                "description":    "Furious, swinging wildly.",
                "biomes":         [],
                "loot_bias":      "common",
                "enemy_type":     "combat",
                "enemy_spells":   [],
                "moves":          ["Strike", "Shove"],
            }
            opponent = spawn_enemy(brawler_template)
            won = run_combat(player, opponent)
            if not player.is_alive():
                return "dead"
            if not won:
                player.city_wanted.add(city_key)
                return "wanted"

        # Won the fight
        player.city_wanted.add(city_key)  # Even winners get wanted for street fighting
        player.city_heat[city_key] = min(100, player.city_heat.get(city_key, 0) + 35)
        print(f"\n  {C.BYELLOW}They're down. But people saw. You need to move.{C.RESET}")
        print(f"  {C.BRED}You're wanted in this city.{C.RESET}")
        pause()
        return "fought_won"

    return "escaped"  # fallback
```

---

#### Pickpocket Flow

```python
def _pickpocket_attempt(player: Player, city_key: str, mark_name: str, mark_desc: str,
                         gold_min: int, gold_max: int, awareness: int, is_connected: bool) -> None:
    """
    3-round prep loop then a final lift attempt.
    Two axes: lift_chance and suspicion_pct.
    """
    stealth     = player.skill("Stealth")
    speechcraft = player.skill("Speechcraft")
    survival    = player.skill("Survival")
    martial     = player.skill("Martial")

    # Base stats — awareness makes suspicion start higher
    lift_chance   = max(15.0, 35.0 - awareness * 0.15)
    suspicion_pct = min(80.0, 30.0 + awareness * 0.40)

    log = []

    for round_num in range(1, 4):
        if lift_chance >= 80:
            # Good enough — skip to lift
            break

        clear()
        title_screen(f"PROWL — {mark_name.upper()}  (Round {round_num}/3)")
        print(f"  {C.DIM}{mark_desc}{C.RESET}")
        print()
        if log:
            for line in log:
                print(f"  {line}")
            print()
        print(f"  {C.BYELLOW}Lift chance:   {lift_chance:.0f}%{C.RESET}   "
              f"{C.BRED}Suspicion:  {suspicion_pct:.0f}%{C.RESET}")
        print()

        options = [
            f"Read the mark      {C.DIM}[Stealth: {stealth}] — study their patterns{C.RESET}",
            f"Create a distraction {C.DIM}[Speechcraft: {speechcraft}] — misdirect their attention{C.RESET}",
            f"Scout the crowd    {C.DIM}[Survival: {survival}] — check for witnesses{C.RESET}",
            f"Go for the lift    {C.DIM}(attempt at current odds){C.RESET}",
            f"Walk away          {C.DIM}(clean exit, no heat){C.RESET}",
        ]
        choice = prompt_choice(options, "Your approach")

        if choice == 5:
            print(f"\n  {C.DIM}You drift away through the crowd. Nobody noticed. Nobody ever does.{C.RESET}")
            pause()
            return

        if choice == 4:
            break

        if choice == 1:
            # Read the mark — Stealth check
            roll = random.randint(1, 20) + stealth // 4
            if roll >= 13:
                gain = 6 + stealth // 12
                lift_chance   = min(85, lift_chance + gain)
                suspicion_pct = max(10, suspicion_pct - 5)
                log.append(f"{C.BGREEN}✓ You clock their patterns. +{gain:.0f}% lift / suspicion ↓{C.RESET}")
            else:
                suspicion_pct = min(90, suspicion_pct + 5)
                log.append(f"{C.BRED}✗ You linger too long. They're starting to notice you. Suspicion ↑{C.RESET}")

        elif choice == 2:
            # Create a distraction — Speechcraft check
            roll = random.randint(1, 20) + speechcraft // 4
            if roll >= 12:
                gain = 8 + speechcraft // 15
                lift_chance   = min(85, lift_chance + gain)
                suspicion_pct = max(10, suspicion_pct - 10)
                log.append(f"{C.BGREEN}✓ The distraction lands. Their attention snaps away. +{gain:.0f}% lift / suspicion ↓↓{C.RESET}")
            else:
                suspicion_pct = min(90, suspicion_pct + 8)
                log.append(f"{C.BRED}✗ You overplay it. They're looking right at you now. Suspicion ↑{C.RESET}")

        elif choice == 3:
            # Scout the crowd — Survival check
            roll = random.randint(1, 20) + survival // 4
            if roll >= 11:
                # Reduces suspicion gain from a future catch — modelled as suspicion drop
                suspicion_pct = max(10, suspicion_pct - 8)
                log.append(f"{C.BGREEN}✓ You read the crowd. You know who's watching. Suspicion ↓{C.RESET}")
            else:
                log.append(f"{C.BBLACK}✗ The crowd gives nothing away. You're no wiser.{C.RESET}")

    # ── Final lift ────────────────────────────────────────────────────────────
    clear()
    title_screen(f"THE LIFT — {mark_name.upper()}")
    for line in log:
        print(f"  {line}")
    print()
    print(f"  {C.BYELLOW}Lift chance: {lift_chance:.0f}%   "
          f"{C.BRED}Suspicion: {suspicion_pct:.0f}%{C.RESET}")
    print()
    pause("Press Enter to make your move...")

    # Roll lift
    lift_roll = random.randint(1, 100)
    caught    = random.randint(1, 100) <= suspicion_pct

    if lift_roll <= lift_chance and not caught:
        # Clean lift
        gold_taken = random.randint(gold_min, gold_max)
        player.gold += gold_taken
        player.city_heat[city_key] = min(100, player.city_heat.get(city_key, 0) + 8)
        play_melody("victory")
        clear()
        title_screen("CLEAN LIFT")
        print(f"\n  {C.BGREEN}Your fingers close around it. By the time you've turned the corner, it's yours.{C.RESET}")
        print()
        print(f"  {C.BYELLOW}+{gold_taken}gp{C.RESET}")
        heat = player.city_heat.get(city_key, 0)
        print(f"  {C.DIM}City heat: {heat}/100{C.RESET}")
        pause()

    elif lift_roll <= lift_chance and caught:
        # Lifted it but they noticed
        gold_taken = random.randint(gold_min, gold_max)
        player.city_heat[city_key] = min(100, player.city_heat.get(city_key, 0) + 20)
        clear()
        print(f"\n  {C.BRED}You got the purse — but they felt it go.{C.RESET}")
        pause()
        outcome = _caught_screen(player, city_key, mark_name, is_connected, gold_taken)
        if outcome in ("escaped", "talked_out", "paid_off"):
            pass  # gold management already handled in caught screen
        if outcome == "fought_won":
            player.gold += gold_taken  # kept it after fighting

    else:
        # Failed lift — caught or just fumbled
        player.city_heat[city_key] = min(100, player.city_heat.get(city_key, 0) + 15)
        clear()
        if caught:
            print(f"\n  {C.BRED}Their hand shoots to their pocket the same moment yours does.{C.RESET}")
            pause()
            _caught_screen(player, city_key, mark_name, is_connected, 0)
        else:
            print(f"\n  {C.BYELLOW}You fumble it. The purse stays where it is. They didn't notice — small mercy.{C.RESET}")
            pause()
```

---

#### Mugging Flow

```python
def _mug_attempt(player: Player, city_key: str, mark_name: str, mark_desc: str,
                  gold_min: int, gold_max: int, awareness: int, is_connected: bool) -> None:
    """
    Mugging — skip stealth entirely. Pure Martial roll.
    Significantly higher heat gain. Stealth governs escape afterward.
    """
    stealth = player.skill("Stealth")
    martial = player.skill("Martial")

    clear()
    title_screen(f"MUGGING — {mark_name.upper()}")
    print(f"\n  {C.DIM}{mark_desc}{C.RESET}")
    print()
    print(f"  {C.BRED}This isn't subtle. It's direct. And it's going to cost this city's opinion of you.{C.RESET}")
    print()
    print(f"  {C.BYELLOW}Martial: {martial}   Stealth (escape): {stealth}{C.RESET}")
    print()

    options = [
        f"Step to them       {C.DIM}[Martial] — walk up and take it{C.RESET}",
        f"Back off           {C.DIM}(change your mind){C.RESET}",
    ]
    choice = prompt_choice(options, "")

    if choice == 2:
        print(f"\n  {C.DIM}You think better of it. Some lines stay uncrossed.{C.RESET}")
        pause()
        return

    # Mug roll — Martial vs awareness
    roll = random.randint(1, 20) + martial // 4
    threshold = 8 + awareness // 8

    # Heat: mugging always adds significant heat regardless of outcome
    mug_heat = 30 + (10 if is_connected else 0)
    player.city_heat[city_key] = min(100, player.city_heat.get(city_key, 0) + mug_heat)

    clear()
    title_screen(f"MUGGING — {mark_name.upper()}")

    if roll >= threshold:
        gold_taken = random.randint(gold_min, gold_max + 20)  # mugging nets slightly more
        player.gold += gold_taken
        print(f"\n  {C.BRED}You step into their path. The message is clear enough.{C.RESET}")
        print(f"  {C.DIM}They hand it over. Nobody argues with the look in your eyes.{C.RESET}")
        print()
        print(f"  {C.BYELLOW}+{gold_taken}gp{C.RESET}")
        print()

        # Escape roll — even on success, someone might have seen
        escape_roll = random.randint(1, 20) + stealth // 4
        if escape_roll >= 12:
            print(f"  {C.BGREEN}You're around the corner before anyone processes what happened.{C.RESET}")
        else:
            player.city_wanted.add(city_key)
            player.city_heat[city_key] = min(100, player.city_heat.get(city_key, 0) + 20)
            print(f"  {C.BRED}Someone saw. Word travels fast in a city this size.{C.RESET}")
            print(f"  {C.BRED}You're wanted here now.{C.RESET}")

        heat = player.city_heat.get(city_key, 0)
        print(f"\n  {C.DIM}City heat: {heat}/100{C.RESET}")
        pause()

    else:
        # Failed mug — they resisted or you hesitated
        print(f"\n  {C.BRED}You step to them but they don't back down. This is going sideways.{C.RESET}")
        print()
        pause()

        # Forced caught situation — always escalates
        if is_connected:
            player.city_wanted.add(city_key)
            print(f"  {C.BRED}They're already calling for help. Guards will be watching for you.{C.RESET}")
            pause()
        else:
            # Fight the mark
            from data.enemies import spawn_enemy
            from ui.combat_loop import run_combat
            brawler_template = {
                "name":           f"Resisting {mark_name}",
                "armor_type":     "none",
                "hp_range":       (25, 45),
                "combat_range":   (18, 30),
                "defense_range":  (10, 20),
                "agility_range":  (20, 38),
                "description":    "They've decided they'd rather fight than hand it over.",
                "biomes":         [],
                "loot_bias":      "common",
                "enemy_type":     "combat",
                "enemy_spells":   [],
                "moves":          ["Strike", "Shove"],
            }
            opponent = spawn_enemy(brawler_template)
            won = run_combat(player, opponent)
            if not player.is_alive():
                return
            if not won:
                player.city_wanted.add(city_key)
                print(f"\n  {C.BRED}You couldn't finish it. You're known here now.{C.RESET}")
                pause()
            else:
                player.city_wanted.add(city_key)
                print(f"\n  {C.BYELLOW}You walked away from it — but someone saw everything.{C.RESET}")
                print(f"  {C.BRED}You're wanted in this city.{C.RESET}")
                pause()
```

---

#### Heat Display Helper

```python
def _heat_label(heat: int) -> str:
    """Return a colored heat description string."""
    if heat == 0:
        return f"{C.BGREEN}Clean{C.RESET}"
    elif heat < 25:
        return f"{C.BYELLOW}Low heat{C.RESET}"
    elif heat < 50:
        return f"{C.BYELLOW}Noticed{C.RESET}"
    elif heat < 75:
        return f"{C.BRED}Hot{C.RESET}"
    else:
        return f"{C.BRED}Burning{C.RESET}"
```

---

#### Main Entry Point: `prowl_screen`

```python
def prowl_screen(player: Player) -> None:
    """
    Entry point called from city_loop. 
    Shows the mark, heat status, and the Pickpocket vs Mug choice.
    """
    city_key = player.current_city
    _decay_heat(player, city_key)

    heat       = player.city_heat.get(city_key, 0)
    is_wanted  = city_key in player.city_wanted

    mark_name, mark_desc, gold_min, gold_max, awareness, is_connected = _select_mark(player, city_key)

    clear()
    title_screen("PROWL")

    if is_wanted:
        print(f"\n  {C.BRED}You're wanted here. The guard knows your face.{C.RESET}")
        print(f"  {C.DIM}Working the streets with a price on your head is suicide.{C.RESET}")
        pause()
        return

    print(f"\n  {C.DIM}You scan the crowd. It doesn't take long.{C.RESET}")
    print()
    print(f"  {C.BYELLOW}Mark:{C.RESET}  {mark_name}")
    print(f"  {C.DIM}{mark_desc}{C.RESET}")
    print()
    print(f"  {C.DIM}Awareness:    {awareness}/100{C.RESET}")
    print(f"  {C.DIM}City heat:    {_heat_label(heat)}  ({heat}/100){C.RESET}")
    if is_connected:
        print(f"  {C.BRED}[Connected] — this mark has reach. Getting caught will escalate.{C.RESET}")
    print()

    martial = player.skill("Martial")
    options = [
        f"Pickpocket   {C.DIM}[Stealth] — quiet, careful, lower heat{C.RESET}",
        f"Mug them     {C.DIM}[Martial: {martial}] — direct, high heat, significant risk{C.RESET}",
        f"Walk away    {C.DIM}(leave the streets){C.RESET}",
    ]
    choice = prompt_choice(options, "Your approach")

    if choice == 3:
        print(f"\n  {C.DIM}You think better of it. The crowd swallows you whole.{C.RESET}")
        pause()
        return

    if choice == 1:
        _pickpocket_attempt(player, city_key, mark_name, mark_desc,
                             gold_min, gold_max, awareness, is_connected)

    elif choice == 2:
        _mug_attempt(player, city_key, mark_name, mark_desc,
                      gold_min, gold_max, awareness, is_connected)
```

---

## Part 3 — Heat Summary: What Raises and Lowers It

| Action | Heat Change |
|---|---|
| Clean pickpocket | +8 |
| Failed lift (not caught) | +15 |
| Caught — paid fine | +heat from caught screen (~15–20) |
| Caught — talked out | +0 additional |
| Caught — ran (success) | +0 additional |
| Caught — ran (fail) | +25 |
| Caught — intimidate (success) | +0 |
| Caught — intimidate (fail) | +10–30 |
| Caught — fight (any result) | +35 |
| Mugging (success, clean escape) | +30 |
| Mugging (success, seen) | +50 |
| Mugging (fail) | +30+ |
| Entering city as wanted + winning | +20 |
| Passive decay (per visit to prowl screen) | −(days_elapsed // 2) × 5, capped −30 |

**Wanted status** is set when: failed run, failed intimidate vs connected mark, failed talk vs connected mark, can't pay fine, fighting (any result). Wanted is cleared only by winning the guard fight at city entry.

---

## Part 4 — Files to Create or Modify

| File | Action | Description |
|---|---|---|
| `engine/pickpocket.py` | **CREATE** | Full file as specified in Part 2 |
| `engine/player.py` | **MODIFY** | Add `city_heat` and `city_wanted` fields to dataclass |
| `data/enemies.py` | **MODIFY** | Add City Guard template + `spawn_city_guard()` helper |
| `ui/city.py` | **MODIFY** | Add wanted check at top of `city_loop`, add "Prowl" menu option |
| `ui/display.py` | **MODIFY** | Add hunger to road HUD in `show_world_map` (on_road only) |

---

## Part 5 — Known Integration Points to Verify

- `run_combat` import in `pickpocket.py` — import from `ui.combat_loop`, same as rest of codebase
- `player.is_alive()` — already on `Player` dataclass, no change needed
- `play_melody("victory")` — already exists in `ui/display.py`, use on clean lift
- `pause()` and `prompt_choice()` — already in `ui/display.py`
- `spawn_enemy()` — import from `data.enemies`, already exists
- The brawler template used inline in fight scenarios does **not** need to be added to `ENEMY_TEMPLATES` — it is constructed inline each time

---

## Notes for Claude Code

- Do not add a save/load hook for `city_heat` or `city_wanted`. These are intentionally session-only.
- Do not add skill progression on success. Skills only improve via the Training Hall.
- Do not add new sound cues beyond `play_melody("victory")` on clean lift — keep it minimal.
- The `city_wanted` check in `city_loop` must happen **before** the `while True:` loop begins, so it fires on entry, not mid-session.
- Hunger display on the road HUD should only appear when `player.on_road` — the city HUD line stays unchanged.
- All flavor text should be dry, street-level, Oblivion-flavored. No purple prose. No exclamation marks in narration.
