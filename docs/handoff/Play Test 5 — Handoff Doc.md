---
type: handoff
version: v2.0
status: archived
systems:
  - merchant
  - stealth
  - combat
  - ui
  - character
---

# Play Test 5 — Handoff Document
**Date:** 2026-04-20
**Version:** Alpha - World v2.0 | Quality of Life Pass
**Git repo:** `C:\dev\merchants-road\` (separate from OneDrive working folder)

---

## Git Push Workflow

ALWAYS follow this order — the working folder is in OneDrive and is NOT the git repo:

```bat
xcopy /E /Y "C:\Users\user\OneDrive\Documents\Second Brain\Craft\Text Based RPG\game\*" "C:\dev\merchants-road\game\"
cd C:\dev\merchants-road
git add -A
git commit -m "message"
git push
```

---

## Project Structure

```
game/
├── main.py                  — all game screens, loops, UI logic
├── data/
│   ├── items.py             — all item definitions + ITEM_LOOKUP + ALL_ITEMS
│   ├── weapons.py           — weapon move definitions (MOVES dict)
│   ├── spells.py            — spell definitions + SPELLS dict
│   ├── enemies.py           — enemy templates + spawn logic
│   └── cities.py            — city definitions, road connections
├── engine/
│   ├── player.py            — Player dataclass + create_player()
│   ├── combat.py            — combat engine: calculate_damage, cast_spell, attempt_flee, etc.
│   ├── events.py            — road events: random_cave(), random_castle(), get_event_enemies()
│   ├── loot.py              — weighted loot generation
│   ├── world.py             — travel system: start_travel(), take_road_step(), abort_travel()
│   └── classes.py           — class detection + ASCII sprite map
└── ui/
    └── display.py           — all rendering, ANSI colors, ambient music system
```

---

## What Was Done This Session (Patches 6–11)

### Patch 6 — Wilderness Events (v1.5 → v1.6)
- 18% base chance of wilderness event on uneventful road steps (reduced by Survival)
- 4 event types: snake bite (poison), disease, weather (cold drain), stranger (gold gamble)
- `road_poison` and `road_diseased` fields added to Player dataclass
- Poison/disease drain 5 HP per step; clears on city arrival

### Patch 7 — Location Entry System (v1.6 → v1.7)
- Caves and castles now have an entry gate: Scout (Dungeoneering), Stealth attempt, Enter Boldly, Pass By
- Room-by-room navigation with mid-room loot find (30% chance) and Press Deeper / Retreat choice
- `force_first` parameter added to `run_combat()` for stealth ambush (surprised enemy, -10 combat_skill for 2 rounds)

### Patch 8 — Weapon Skill Synergies (v1.7 → v1.8)
- Bow moves now each scale with a distinct skill: Pot Shot → Survival, Snipe → Stealth, Long Shot → Martial
- `survival_boost` special added to weapons.py and combat.py

### Patch 9 — Negotiation Expansion (v1.8 → v1.9)
- All 7 skills now have a negotiation tactic (added Survival, Stealth, Magic)
- Discount tiers sharpened: 1 win = 2%, 2 wins = 10%, 3 wins (flawless) = 25%
- Sell bonus explicitly displayed in merchant header: `[25% buy discount | +25% sell bonus]`

### Patch 10 — QoL Pass (v1.9 → v2.0)
- Gear + Journal consolidated into single Bag menu (road: 6→5 options, city: 7→6 options)
- Merchant slot 1 always a Survival Trader (guaranteed food/firewood/rope)
- Inn flavour text: 3 lines per city drawn at random on rest
- Version string updated to v2.0

### Patch 11 — Context-Based Ambient Music (v2.0 → v2.1)
- 4 ambient loops: road (A minor, haunting), city (C major, warm), dungeon (E minor, oppressive), tension (A minor, urgent)
- `start_ambient_loop(context)` switches cleanly between loops; `resume_ambient_loop()` restores pre-combat context
- Switch points: game start → city, travel begins → road, city arrival → city, dungeon entry → dungeon, press deeper → tension, retreat/flee/victory → road or resume

---

## Bug Fixes Applied This Session

| File | Issue | Fix |
|---|---|---|
| `engine/combat.py` | `cast_spell` missing | Added player spell cast function |
| `engine/combat.py` | `attempt_flee` missing | Added flee attempt function |
| `engine/combat.py` | `cast_enemy_spell` + `enemy_attack` truncated | Restored full functions |
| `engine/loot.py` | Imported `ITEMS`, `RARITY_WEIGHTS` (didn't exist) | Changed to `ALL_ITEMS`; defined `RARITY_WEIGHTS` locally |
| `engine/loot.py` | `generate_loot()` truncated mid-line | Restored rest of function |
| `engine/player.py` | `create_player()` missing `return p` | Appended return statement |
| `data/items.py` | `ITEM_LOOKUP`, `ALL_ITEMS`, `get_items_by_rarity` missing | Restored + completed `Sellsword's Almanac` lore |
| `ui/display.py` | `show_combat_screen`, `show_character_sheet`, `show_journal` truncated | Restored all three functions |
| `main.py` | `\!` escape sequences throughout (SyntaxWarning) | Stripped all 24 instances via sed |
| `main.py` | `main()` function truncated | Restored with correct version string and game loop |

---

## Architecture Notes

### Player dataclass (engine/player.py)
Key fields: `hp`, `max_hp`, `mana`, `max_mana`, `gold`, `inventory`, `equipped`, `skills` (dict), `learned_spells` (list), `journal` (list), `on_road`, `current_city`, `road_destination`, `road_steps`, `road_total`, `road_poison`, `road_diseased`, `days_elapsed`

Key methods: `skill(name)`, `add_item()`, `remove_item()`, `equip()`, `take_damage()`, `heal()`, `spend_mana()`, `is_alive()`, `can_carry()`

### Combat flow (engine/combat.py)
`run_combat(player, enemy, force_first=False)` → returns True (win) or False (flee/death)
- Calls `stop_ambient_loop()` on entry, `resume_ambient_loop()` on exit
- State dict tracks: `player_defensive`, `player_evading`, `enemy_staggered`, `enemy_slowed`
- `calculate_damage()` returns `(dmg, label, is_crit, special_tag)`
- `cast_spell()` returns `(dmg_or_heal, label, status_tag)` — mana cost handled by caller
- `attempt_flee()` — Stealth-boosted, agility-penalised chance

### Ambient music (ui/display.py)
- `start_ambient_loop(context)` — accepts `"road"`, `"city"`, `"dungeon"`, `"tension"`
- `stop_ambient_loop()` — silences immediately
- `resume_ambient_loop()` — restores `_current_context` (use after combat)
- All audio is `winsound.Beep` — Windows only, silently ignored on other platforms

### Items (data/items.py)
- `ALL_ITEMS` — flat list of every item
- `ITEM_LOOKUP` — dict by name
- Lists: `WEAPON_ITEMS`, `ARMOR_ITEMS`, `ACCESSORY_ITEMS`, `POTION_ITEMS`, `SUPPLY_ITEMS`, `TRADE_ITEMS`, `GRIMTOTEM_ITEMS`, `FORAGE_ITEMS`, `HUNT_ITEMS`, `BOOK_ITEMS`

### Main game loop (main.py)
```
main()
  └── character_creation()
  └── start_ambient_loop("city")
  └── while True:
        city_loop(player)       — returns when player starts travel
        start_ambient_loop("road")
        road_loop(player)       — returns on city arrival
```

---

## Known Issues / Carry-Forward

None currently. The `random_cave` / `random_castle` import error (carried through Patches 7–10) was resolved.

---

## File Truncation Pattern — Watch For This

Multiple files were truncated mid-function due to context window limits in earlier sessions. Pattern to watch for:
- File ends mid-string or mid-expression (syntax error)
- Function ends with assignment but no `return` when a value is expected
- List or dict closes without the lookup/helper at the bottom of the file

If a new import error appears, check the bottom of the imported file first.

The audit script lives at:
`C:\Users\user\AppData\Roaming\Claude\...\outputs\deep_audit.py`
Run it with `python3 deep_audit.py` from the sandbox to catch truncations before pushing.

---

## Patch Notes Files

All saved in `C:\Users\user\OneDrive\Documents\Second Brain\Craft\Text Based RPG\`:
- `Patch 6 (v1.5 → v1.6).md` — Wilderness Events
- `Patch 7 (v1.6 → v1.7).md` — Location Entry System
- `Patch 8 (v1.7 → v1.8).md` — Weapon Synergies
- `Patch 9 (v1.8 → v1.9).md` — Negotiation Expansion
- `Patch 10 (v1.9 → v2.0).md` — QoL Pass
- `Patch 11 (v2.0 → v2.1).md` — Ambient Music

---

## Suggested Play Test 5 Focus Areas

Things to watch during the test:
- Wilderness events triggering correctly and not stacking weirdly with road enemies
- Location entry gate flow (Scout + Stealth + Enter all work in sequence)
- Tension music switching on "Press Deeper" and restoring to road on exit
- City music correctly switching on arrival (not staying as road)
- Negotiation: confirm 25% flawless discount feels impactful
- Guaranteed Survival Trader appearing as merchant slot 1 every city visit
- Inn flavour text displaying before rest confirmation
- Bag menu accessible from both road and city
- `cast_spell` working correctly for all spell types including heal and drain
- `attempt_flee` working and restoring correct ambient context after flee
