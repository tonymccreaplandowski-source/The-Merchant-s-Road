---
type: handoff
version: v2.6
status: archived
systems:
  - architecture
  - ui
  - combat
  - world
---

# Refactor Handoff — main.py Split
**Date:** 2026-04-23
**Version:** Alpha - World v2.6 | Play Test 10 Pass
**Session type:** Developer refactor — no gameplay changes

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

## What Was Done This Session

`main.py` was 3200 lines. It has been split into 9 focused modules. No logic was changed — this was a pure structural refactor.

**main.py is now 33 lines** — just imports and `main()`.

---

## New Project Structure

```
game/
├── main.py                    — entry point only (33 lines)
│
├── data/
│   ├── classes.py             — CLASS_CHOICES (all 21 class definitions + lore)
│   ├── road_flavor.py         — ROAD_FLAVOR, _FLAVOR_DEFAULT, road_flavor_line()
│   ├── items.py               — all item definitions (unchanged)
│   ├── weapons.py             — MOVES dict (unchanged)
│   ├── spells.py              — SPELLS dict + get_available_spells() (unchanged)
│   ├── enemies.py             — enemy templates + spawn logic (unchanged)
│   └── cities.py              — city definitions, road connections (unchanged)
│
├── engine/
│   ├── merchant.py            — merchant types, stock pools, generation, sell_price/buy_price
│   ├── items_use.py           — use_potion(), use_item_outside_combat(), USABLE_EFFECTS_OUTSIDE_COMBAT
│   ├── player.py              — Player dataclass + create_player() (unchanged)
│   ├── combat.py              — combat engine (unchanged)
│   ├── events.py              — road events (unchanged)
│   ├── loot.py                — loot generation (unchanged)
│   └── world.py               — travel system (unchanged)
│
└── ui/
    ├── creation.py            — class_selection_screen(), character_creation()
    ├── combat_loop.py         — run_combat(), loot_screen()
    ├── equipment.py           — equip_screen(), bag_screen(), use_items_screen(),
    │                            show_inventory_screen(), show_skill_guide(), SKILL_GUIDE
    ├── city.py                — city_loop(), merchant_screen(), visit_market(),
    │                            negotiate_session(), train_skills(), rest_at_inn(),
    │                            read_book_menu(), _city_merchants cache
    ├── road.py                — road_loop(), explore_event(), make_camp(),
    │                            _do_forage(), hunting_minigame(), bushcraft_screen(),
    │                            wilderness_event() + sub-events, game_over()
    └── display.py             — all rendering, ANSI colors, ambient music (unchanged)
```

---

## Module Responsibilities (quick reference)

| Module | What to edit when... |
|---|---|
| `data/classes.py` | Adding/changing playable classes |
| `data/road_flavor.py` | Adding road biome flavor text |
| `engine/merchant.py` | Merchant types, stock pools, pricing formula |
| `engine/items_use.py` | Item effect logic (potions, consumables) |
| `ui/creation.py` | Character creation flow, skill allocation screen |
| `ui/combat_loop.py` | Combat turn loop, post-combat loot screen |
| `ui/equipment.py` | Equip/unequip, grimtotem reading, bag screen, skill guide |
| `ui/city.py` | City menu, market, negotiate minigame, training, inn, books |
| `ui/road.py` | Road loop, exploration (caves/castles), camp, forage, hunt, wilderness events |

---

## Key Constants — Where They Now Live

| Constant | Module |
|---|---|
| `STARTING_POINTS`, `MIN_SKILL`, `MAX_CREATION_SKILL`, `DOMINANT_SKILL_VALUE` | `engine/player.py` |
| `MAX_INVENTORY` | `engine/player.py` |
| `MERCHANT_NAMES`, `MERCHANT_TYPES`, `MERCHANT_GREETINGS` | `engine/merchant.py` |
| `_GUARANTEED_MERCHANTS`, `_VARIABLE_MERCHANT_CHANCE` | `engine/merchant.py` |
| `USABLE_EFFECTS_OUTSIDE_COMBAT` | `engine/items_use.py` |
| `CLASS_CHOICES` | `data/classes.py` |
| `ROAD_FLAVOR` | `data/road_flavor.py` |
| `CAMP_FOOD`, `FIREWOOD_NAMES` | `ui/road.py` |
| `FORAGE_TABLE` | `ui/road.py` |
| `HUNT_ANIMALS` | `ui/road.py` |
| `HERMIT_LORE` | `ui/road.py` |
| `WILDERNESS_BASE_CHANCE`, `WILDERNESS_SKILL_REDUCE` | `ui/road.py` |
| `_city_merchants` (merchant cache) | `ui/city.py` |
| `INN_FLAVOUR` | `ui/city.py` |
| `SKILL_GUIDE` | `ui/equipment.py` |
| `_TACTICS` (negotiate tactics list) | `ui/city.py` |

---

## Import Notes for Next Session

- `run_combat` and `loot_screen` live in `ui/combat_loop.py` — import from there if you need them
- `bag_screen` and `equip_screen` live in `ui/equipment.py`
- `read_grimtotem` lives in `ui/equipment.py` — used by both `equip_screen` and `read_book_menu`
- `sell_price` / `buy_price` live in `engine/merchant.py` (previously `_sell_price` / `_buy_price` in main.py — underscore prefix dropped, now public)
- `road_flavor_line` is the public name (previously `_road_flavor_line`)
- `_format_time` is private to `ui/road.py` — used only by `game_over`
- `_training_cost` is private to `ui/city.py` — used only by `train_skills`

---

## Verified Clean

All 10 files pass `ast.parse()` syntax check. Full import chain resolves without errors:

```
python -c "from ui.city import city_loop; from ui.road import road_loop; print('OK')"
```

No gameplay logic was altered. The game runs identically to the previous session.

---

## No Pending Issues

This session was purely structural. No bugs were introduced, no features changed.
The old 3200-line `main.py` has been replaced — do not restore it.

---

## Patch Notes Files

All saved in `C:\Users\user\OneDrive\Documents\Second Brain\Craft\Text Based RPG\`:
- `Patch 1 (v1.0 → v1.1).md` through `Patch 15 (v2.4 → v2.5).md` — prior sessions
- This session had no gameplay patch — structural refactor only
