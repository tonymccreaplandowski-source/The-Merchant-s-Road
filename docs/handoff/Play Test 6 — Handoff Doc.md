---
type: handoff
version: v2.2
status: archived
systems:
  - world
  - ui
  - stealth
  - combat
---

# Play Test 6 — Handoff Document
**Date:** 2026-04-20
**Version:** Alpha - World v2.2 | Play Test 5 Feedback Pass
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
│   ├── items.py             — all item definitions + ITEM_LOOKUP + ALL_ITEMS + lore fields
│   ├── weapons.py           — weapon move definitions (MOVES dict)
│   ├── spells.py            — spell definitions + SPELLS dict + get_available_spells()
│   ├── enemies.py           — enemy templates + spawn logic (includes moves field)
│   └── cities.py            — city definitions, road connections
├── engine/
│   ├── player.py            — Player dataclass + create_player() + STARTING_POINTS/MAX_CREATION_SKILL
│   ├── combat.py            — combat engine: calculate_damage, cast_spell, attempt_flee, enemy_attack
│   ├── events.py            — road events: random_cave(), random_castle(), get_event_enemies()
│   ├── loot.py              — weighted loot generation
│   ├── world.py             — travel system: start_travel(), take_road_step(), abort_travel()
│   └── classes.py           — class detection + ASCII sprite map
└── ui/
    └── display.py           — all rendering, ANSI colors, ambient music system
```

---

## What Was Done This Session (Patch 12 — v2.1 → v2.2)

### Critical Bug Fix
- `Enemy` dataclass was missing `moves` field → crashed on any physical enemy attack
- Added `moves: List[str]` to dataclass; populated all 14 templates; updated `spawn_enemy()`

### Balance
- Skill points at character creation: **180 → 100**
- Per-skill cap at creation: **40** (`MAX_CREATION_SKILL` in `engine/player.py`)
- Mid-game training remains uncapped
- Stealth entry: replaced d20 roll with flat % formula
  - `success = clamp(0.05, 0.95, 0.15 + (stealth - 5) * 0.013)`
  - Skill 5 → 15% | Skill 20 → ~34% | Skill 40 → ~59% | cap 95%
- Spell access gated: `get_available_spells()` now requires `learned_spells`; high Magic alone no longer grants spells

### Gameplay
- Camp blocked at full HP (firewood/food preserved)
- Foraging has encounter chance: 14% enemy, 6% location (same road pool)

### UI / Content
- **Skill Guide** added to Bag menu (road + city) — plain-language descriptions of all 7 skills
- **Merchant greetings** — unique line per merchant type on first approach (4 lines/type, drawn randomly)
- **Item lore** — every item has a Dark Souls-style one-line fragment in inventory display
  - Format: mechanic note (if relevant) + name/fate/place — esoteric, implies history
- **Music volume** — ambient loop beep durations halved (~50% quieter)

### Deferred to Expansions.md
- Stealth entry minigame (Item 6 from Play Test 5)
- Class pick screen at game start

---

## Architecture Notes

### Player dataclass (engine/player.py)
Key constants: `STARTING_POINTS = 100`, `MIN_SKILL = 5`, `MAX_SKILL = 100`, `MAX_CREATION_SKILL = 40`

Key fields: `hp`, `max_hp`, `mana`, `max_mana`, `gold`, `inventory`, `equipped`, `skills` (dict), `learned_spells` (list), `journal` (list), `on_road`, `current_city`, `road_destination`, `road_steps`, `road_total`, `road_poison`, `road_diseased`, `days_elapsed`

### Enemy dataclass (data/enemies.py)
Fields: `name`, `armor_type`, `hp`, `max_hp`, `combat_skill`, `defense_skill`, `agility`, `description`, `biomes`, `loot_bias`, `enemy_type` ("combat"/"half_mage"/"mage"), `enemy_spells`, **`moves`** (new — list of move names from MOVES dict)

### Spell system (data/spells.py)
`get_available_spells(magic_skill, learned_spells)` — both args required for player use.
`learned_spells=None` still works for enemy-only calls (no spell purchasing gating for enemies).

### Stealth entry (main.py → explore_event)
```python
success_chance = max(0.05, min(0.95, 0.15 + (stealth_val - 5) * 0.013))
if random.random() < success_chance:
    force_first = True
```

### Ambient music (ui/display.py)
- `start_ambient_loop(context)` — accepts `"road"`, `"city"`, `"dungeon"`, `"tension"`
- All note durations halved from v2.1 values
- All audio is `winsound.Beep` — Windows only, silently ignored elsewhere

### Items (data/items.py)
- All items now have a `lore` field (Optional[str]) — shown in character sheet inventory
- Lore format: one line, cryptic, implies a history. Mechanical note prepended where relevant.
- `ALL_ITEMS`, `ITEM_LOOKUP`, category lists all intact

### Bag menu (main.py)
- Now has 3 options: Gear / Journal / **Skill Guide**
- Skill guide is a separate `show_skill_guide()` function above `bag_screen()`

---

## Known Issues / Carry-Forward

**File truncation risk** — During this session, large Write operations to `enemies.py` and `items.py` truncated at the file tail. Both were repaired. Going forward, prefer Edit operations over full-file Write where possible. If a new import error appears on a file that was recently edited, check the bottom of that file first.

The audit script lives at:
`C:\Users\user\AppData\Roaming\Claude\...\outputs\deep_audit.py`
Run it with `python3 deep_audit.py` from the sandbox to catch truncations before pushing.

---

## Suggested Play Test 6 Focus Areas

Things to watch during the test:
- Combat no longer crashes on any enemy — confirm with a range of enemy types
- Stealth entry at low skill feels appropriately difficult (should fail often at skill 5–10)
- Spell cast menu shows only purchased spells — confirm "no spells known" message appears for new characters without grimtotems
- Skill point allocation: confirm 100 points total and 40-per-skill cap enforced at creation
- Camp blocked at full HP — confirm message and resource preservation
- Foraging encounters — confirm enemy and location spawns work correctly during foraging
- Skill Guide in Bag — confirm it renders cleanly and covers all 7 skills
- Merchant greetings — confirm each type delivers a unique line on first approach
- Item lore — confirm visible in character sheet inventory for all item types
- Music volume — confirm ambient loops are noticeably quieter than v2.1

---

## Patch Notes Files

All saved in `C:\Users\user\OneDrive\Documents\Second Brain\Craft\Text Based RPG\`:
- `Patch 1 (v1.0 → v1.1).md` through `Patch 11 (v2.0 → v2.1).md` — prior sessions
- `Patch 12 (v2.1 → v2.2).md` — this session (Play Test 5 feedback pass)

---

## Expansions.md (Planned Features — Not In Scope)

Located at: `C:\Users\user\OneDrive\Documents\Second Brain\Craft\Text Based RPG\Expansions.md`

Current entries:
1. Explorable Dungeons — Location Minigames
2. Pickpocket Minigame
3. Assassination Minigame
4. Quests
5. Library Hunt Minigame
6. Stealth Entry Minigame *(with full design notes)*
7. Class Pick Screen at Game Start *(with full design notes)*
