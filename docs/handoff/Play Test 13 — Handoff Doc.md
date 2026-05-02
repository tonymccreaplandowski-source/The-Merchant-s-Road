---
type: handoff
version: v2.7
status: active
systems:
  - stealth
  - character
  - ui
---

# Play Test 13 — Handoff Document
**Date:** 2026-04-24
**Version:** Alpha - World v2.7 | Play Test 12 Pass
**Working folder:** `C:\Users\user\OneDrive\Documents\Second Brain\Craft\Text Based RPG\`

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
├── main.py                  — entry point, title screen
├── sounds/
│   ├── battle_theme_1.wav   — looping battle music
│   └── test12.wav           — looping location music (caves, castles)
├── data/
│   ├── items.py             — all item definitions + ITEM_LOOKUP + ALL_ITEMS
│   ├── items_clean.py       — (legacy, unused)
│   ├── weapons.py           — weapon move definitions (MOVES dict)
│   ├── spells.py            — spell definitions + get_available_spells()
│   ├── enemies.py           — enemy templates + spawn logic
│   ├── cities.py            — city definitions, road connections
│   ├── classes.py           — CLASS_CHOICES list (21 classes, dominant skill pairs)
│   └── road_flavor.py       — biome/phase-aware road flavor lines
├── engine/
│   ├── player.py            — Player dataclass + create_player()
│   ├── combat.py            — combat engine: calculate_damage, cast_spell, enemy_attack
│   ├── events.py            — RoadEvent dataclass + cave/castle pools
│   ├── loot.py              — generate_loot() + generate_loot_min_rarity()
│   ├── world.py             — travel system: start_travel(), take_road_step()
│   ├── negotiate.py         — negotiation mini-game (4-round system)
│   ├── merchant.py          — merchant generation + pricing
│   ├── items_use.py         — item effect logic (combat + out-of-combat)
│   └── classes.py           — class detection + ASCII sprite map
└── ui/
    ├── display.py           — rendering, ANSI colors, music system
    ├── city.py              — city loop, market, training, inn, read_book_menu()
    ├── road.py              — road loop, explore_event(), camping, hunting, foraging
    ├── combat_loop.py       — in-combat turn loop + loot screen
    ├── equipment.py         — bag_screen(), equip, inventory, use items, journal, read
    └── creation.py          — character creation flow
```

---

## What Was Done This Session (v2.6 → v2.7)

### PT12 Bug Fixes

**`event.lore` AttributeError crash**
- `explore_event()` referenced `event.lore` but `RoadEvent` uses `lore_text`
- Fixed in `ui/road.py` — both the journal check and the typewrite call
- Also replaced `typewrite(event.lore_text)` with instant print (journal consistency)

**Negotiation only gave 2 playable rounds**
- Loop was `range(1, 4)` with forced close triggering at `round_num == 3`
- Players never saw Round 3/3 — jumped straight to forced close after Round 2
- Fixed: `range(1, 5)`, forced close at `round_num == 4`
- Now: 3 full choice rounds + "tensions are as high as they'll go" on the 4th

**"Read" only accessible from city top menu**
- Added "Read" to `bag_screen()` in `ui/equipment.py` (lazy import of `read_book_menu` avoids circular dependency)
- Now accessible from both city and road via Bag

### PT11 Items Implemented

**Traveling music persists on turn-back**
- `abort_travel()` in `road_loop()` now calls `start_ambient_loop("city")` before returning

**Final location loot guaranteed uncommon+**
- Added `generate_loot_min_rarity(min_rarity)` to `engine/loot.py`
- Filters ALL_ITEMS to eligible rarities, uses base RARITY_WEIGHTS
- `explore_event()` final-clear loot (2 items) now calls `generate_loot_min_rarity("uncommon")`
- Mid-location room loot (30% chance) remains common-biased

**Journal instant display**
- `show_journal()` in `ui/display.py` replaced `typewrite(entry)` with line-by-line `print()`

**Mage lethality — 2% reduction**
- `cast_enemy_spell()` in `engine/combat.py`: raw damage multiplied by `0.98`

**Location retreat roll**
- "Retreat" mid-location now rolls `d20 + (Survival + Stealth) // 10`
- Roll ≥ 12: clean escape. Roll < 12: −5 to −15 HP before escaping
- Player can still always escape — the check only determines whether it costs HP

**Hunger meter (new system)**
- `Player.hunger: int = 100` added to dataclass (`engine/player.py`)
- Depletes −13 per road step (`engine/world.py:take_road_step()`)
- Thresholds:
  - ≥ 60: well-fed (no effect)
  - 30–59: Hungry (flavor message on road, no mechanical penalty)
  - 10–29: Starving (−5 Martial and −5 Survival via `skill()` method)
  - < 10: Critically Low (−10 all skills + −5 HP per road step)
- Restored by:
  - Camping (`make_camp()`) — uses `FOOD_HUNGER_RESTORE` dict, +20 to +40 depending on food
  - Eating items directly (`use_item_outside_combat()`) — same dict, shown in message suffix
  - Inn rest (`rest_at_inn()`) — restores to 100
- Displayed on character sheet (color-coded label + /100 value)
- Displayed on road each step if below 60

### Location Music (new)

- `test12.wav` added to `game/sounds/`
- `play_location_music()` and `stop_location_music()` added to `ui/display.py`
- `_location_music_active: bool` flag tracks whether location music is running
- `resume_ambient_loop()` checks this flag — after combat inside a location, restores `test12.wav` instead of the beep dungeon ambient
- `explore_event()` in `ui/road.py`:
  - Entry: `play_location_music()`
  - Press deeper: `play_location_music()` (re-cues loop)
  - All exit paths (fled, retreat, full clear): `stop_location_music()` then `start_ambient_loop("road")`

---

## Architecture Notes

### Hunger System (`engine/player.py`, `engine/world.py`)

```python
# Player field
hunger: int = 100

# skill() method appends at end:
if self.hunger < 10:
    bonus -= 10
elif self.hunger < 30 and name in ("Martial", "Survival"):
    bonus -= 5

# world.py — take_road_step():
player.hunger = max(0, player.hunger - 13)
```

**FOOD_HUNGER_RESTORE dict** is in `engine/items_use.py` and imported by `ui/road.py` for camping.

### Loot System (`engine/loot.py`)

```python
generate_loot(bias="common")              # existing — weighted by loot_bias
generate_loot_min_rarity("uncommon")      # new — floors rarity, no common items
```

### Location Music (`ui/display.py`)

```python
_location_music_active: bool = False

play_location_music(filename="test12.wav")  # stops beep loop, starts WAV loop, sets flag
stop_location_music()                        # clears flag, stops WAV

resume_ambient_loop()  # checks _location_music_active — restores WAV or beep accordingly
```

WAV system uses `winsound.PlaySound` with `SND_ASYNC | SND_LOOP`. Calling `play_battle_music()` automatically preempts location WAV (one async WAV at a time on Windows). After combat, `resume_ambient_loop()` restores whichever was active.

### Negotiation (`engine/negotiate.py`)

```python
for round_num in range(1, 5):       # 4 iterations
    if round_num == 4:              # forced close on 4th
        _go_for_close(..., forced=True)
        return
    # rounds 1, 2, 3 show the choice menu
```

### Bag Screen (`ui/equipment.py`)

Options: Gear / Inventory / Use Item / **Read** / Journal / Skill Guide / Back
"Read" lazily imports `read_book_menu` from `ui.city` to avoid circular import.

---

## Deferred — Not In Scope This Session

The following were discussed and explicitly set aside:

1. **Location navigation overhaul** — replace "Press deeper" with descriptive directional options (e.g. "Upstairs to the tower", "Down to the dungeon"). Requires per-location descriptor data that doesn't yet exist.
2. **Skill-up items in wilderness** — items that permanently raise a skill by 1 when used. Requires new item types, loot integration, and a use-effect handler.
3. **Alchemist class fix** — `["Magic", "Merchantilism"]` → `["Magic", "Survival"]` (abandoned by user this session)
4. **Merchant availability reveal order** — hide availability until player selects a type (abandoned this session)
5. **Negotiation walk-away flavor** — merchant reacts when player exits mid-negotiation (abandoned this session)
6. **Combat hit threshold** — reduce miss rate, replace pure misses with ineffective hits (abandoned this session)

---

## Suggested PT13 Focus Areas

- **Hunger meter** — does −13/step feel right? Can players manage hunger comfortably with camping and food? Does the Starving/Critical feedback read clearly? Does the HP drain at <10 feel fair or punishing?
- **Location music** — does `test12.wav` loop cleanly? Does it stop and resume correctly around combat (enter fight → battle music → victory → test12.wav resumes)?
- **Negotiation** — does 3+1 rounds feel balanced? Are merchants still rolling too strong?
- **Read in Bag** — accessible from road and city without issues?
- **Location retreat roll** — does the Survival+Stealth check feel appropriate? Is the HP cost on failed retreat reasonable?
- **Final location loot** — always uncommon or above on full clear?
- **Journal** — instant display, no typewrite lag?
- **Hunger + camping interaction** — does camping correctly restore hunger? Does the food quality difference (Dried Rations vs Unknown Berries) feel meaningful?

---

## Files Changed This Session

| File | Change |
|---|---|
| `game/main.py` | Version → v2.7, Play Test 12 Pass |
| `game/engine/player.py` | Added `hunger` field + skill penalties in `skill()` |
| `game/engine/combat.py` | Enemy spell damage × 0.98 |
| `game/engine/negotiate.py` | `range(1,5)`, forced close at round 4 |
| `game/engine/loot.py` | Added `generate_loot_min_rarity()` |
| `game/engine/world.py` | `player.hunger -= 13` per road step |
| `game/engine/items_use.py` | `FOOD_HUNGER_RESTORE` dict + hunger suffix on food messages |
| `game/ui/display.py` | Journal instant print, hunger bar on character sheet, `play_location_music()` / `stop_location_music()`, updated `resume_ambient_loop()` |
| `game/ui/road.py` | Music fix, `event.lore_text` crash, uncommon+ final loot, retreat roll, hunger drain/display, camp hunger restore, location music calls |
| `game/ui/city.py` | Inn restores `player.hunger = 100` |
| `game/ui/equipment.py` | "Read" added to `bag_screen()` |
| `game/sounds/test12.wav` | New file — location ambient music |
