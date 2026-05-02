---
type: patch-notes
version: v2.7→v2.8
status: active
systems:
  - dungeon
  - items
  - world
  - ui
---

# Patch 16 — v2.7 → v2.8
**Date:** 2026-04-27
**Session:** Explorable Dungeons / Location Minigame — Full Overhaul

---

## Overview

Complete replacement of the linear `explore_event()` system with a full dungeon
graph engine. Locations are now branching, room-by-room environments with six
distinct room types, per-location directional navigation, named bosses, unique
loot drops, and four puzzle mini-game types. Orphaned dungeoneering items now
have mechanical purpose throughout.

---

## New Systems

### Dungeon Graph Engine (`engine/dungeon.py` — new file)

- `DungeonRoom` dataclass: `room_type`, `exits`, `visited`, `solved`, `puzzle_type`,
  `puzzle_timed`, `puzzle_gating`, `trap_type`, `dead_end_tag`, `is_boss`
- `generate_dungeon(event)` builds a 5–8 room branching tree per run
  - Main branch: entry → 1–2 combat rooms → boss room
  - Side branches: trap, puzzle, secret, dead_end rooms
  - 30% chance a puzzle gates the boss branch per run
  - `DUNGEON_SIZE_RANGE = (5, 8)` — adjustable constant
- Room type weights tunable per `event_type` (`cave` vs `castle`)

### Six Room Types

| Type | Description |
|---|---|
| **entry** | Atmospheric entry, no encounter |
| **combat** | Biome enemy spawned from pool, 30% loot roll on clear |
| **trap** | Dungeoneering + Survival check; spike / gas / floor / tripwire variants |
| **puzzle** | One of four mini-game types; optional or gating |
| **secret** | Dungeoneering roll only; pure upside — no penalty on fail |
| **dead_end** | Atmospheric lore only; 6 flavored descriptions (child bedroom, lovers' chamber, weapons cache, flooded cellar, dark shrine, set dining hall) |
| **boss** | Named, buffed final enemy; unique item drop on kill |

### Four Puzzle Mini-Games (`ui/dungeon_puzzles.py` — new file)

**Riddle** — 22 scripted riddles with text-input answers. One attempt.
Dungeoneering reveals a clue above the difficulty threshold. Lock Picks bypass
gating riddles.

**Reveal** — Health-bar progressive reveal. Object description shown in
fragments as player makes skill rolls (Dungeoneering / Survival / Martial).
Bar depletes; player names the object from 4 options on final guess.

**Maze** — ASCII 7×7–9×9 grid, WASD keyboard navigation via `msvcrt`.
Fog of war radius scales with Dungeoneering + light source.
Timed variant: 30s base + 5s per 5 Dungeoneering levels above 0.
Non-timed variant: move budget (40 base + 5 per 5 Dung levels).
3 hand-crafted layouts. Falls back to skill check on non-Windows platforms.

**Sequence** — Three-symbol ordered lock. Clue clarity scales with
Dungeoneering (full clue vs. partial). One attempt. Lock Picks bypass.
5 scripted puzzles (moon/sun/flame, metals, crown/sword/coin, elements, runes).

### Boss System (per location)

Each `RoadEvent` now carries `boss_name`, `boss_hp_mult`, `boss_dmg_mult`,
`boss_drop_name`. Bosses spawn via `spawn_boss(event)` in `engine/events.py`:
draws the highest-HP-ceiling biome template, applies multipliers.

Pre-boss Dungeoneering warning tiers:
- < 25: atmospheric dread only
- 25–50: "Something powerful is close"
- 51–80: boss name revealed
- 80+: boss name + "formidable" warning

### Unique Boss Drop Items (`data/items.py` — `BOSS_LOOT_ITEMS`)

Six named unique items, rare tier, wearable gear only. Never in the random loot
pool. Only obtainable by defeating their specific boss.

| Item | Boss | Location | Stats |
|---|---|---|---|
| Warden's Hide Wraps | The Den Warden | The Hollow Den | +5 Stealth, +3 Survival, +2 Dungeoneering (leather armor, AV 8) |
| Tideborn Pendant | The Grotto Abomination | The Dripping Grotto | +6 Magic, +4 Dungeoneering (necklace) |
| Shadow Fingers | The Cache Master | The Smuggler's Cache | +7 Stealth, +3 Merchantilism (ring) |
| Castellan's Vow | The Castellan | The Broken Keep | +5 Martial, +3 Survival, −2 Stealth (mail armor, AV 14) |
| Captain's Verdict | The Forsaken Captain | The Forsaken Garrison | +5 Martial, +4 Speechcraft (sword) |
| Folly Signet | The Vault Sentinel | The Merchant Lord's Folly | +6 Merchantilism, +4 Speechcraft (ring) |

### Directional Navigation

"Press deeper" replaced with labelled exits drawn from per-location nav pools.
Caves: passages, tunnels, hollows, slopes. Castles: wings, towers, undercroft,
corridors. Players choose direction and discover room type on entry.
Visited rooms marked `[visited]`. Gating puzzles that were failed show as sealed.

### Dungeoneering Item Integration

All previously orphaned dungeoneering merchant items now have dungeon mechanics:

| Item | Mechanic | Consumed? |
|---|---|---|
| Grappling Hook | +30 to retreat roll (near-guarantee clean escape); unlocks upper-route exits in castles | Yes |
| Rope | +15 to retreat roll; negates HP cost on clean retreat | Yes |
| Lock Picks | Bypasses one gating puzzle per dungeon; +1 loot roll in secret areas | Yes |
| Torch Bundle | Expands maze fog radius (1→2), +2 to trap detection, +4 to secret area roll | Yes (on entry) |
| Lantern | Expands maze fog radius (1→3), +5 to trap detection, +8 to secret area roll, +4 to reveal puzzle rolls | No (persists run) |
| Tinderbox | Required to activate Torch Bundle or Lantern in dungeon | No |
| Adventurer's Map | At entry: reveals room types behind 2 exits before committing | Yes |
| Bandages | Between-room healing via existing use-item system (unchanged) | Yes |

### Retreat Formula

Replaced `d20 + (Survival + Stealth) // 10 ≥ 12` with:

```
Roll d100. Clean escape if roll ≤ (Dungeoneering + Stealth + Survival) / 3
```

- Grappling Hook: +30 to threshold
- Rope: +15 to threshold
- Miss by ≤ 20: −5 to −12 HP
- Miss by > 20: −15 to −25 HP
- Player always escapes — roll only determines cost

---

## Files Changed

| File | Change |
|---|---|
| `game/data/items.py` | Added `BOSS_LOOT_ITEMS` (6 items); `ITEM_LOOKUP` now includes boss items; pool comment clarifies they are excluded from random generation |
| `game/engine/events.py` | `RoadEvent` extended with `boss_name`, `boss_hp_mult`, `boss_dmg_mult`, `boss_drop_name`, `nav_labels`; all 6 events populated; `spawn_boss()` added |
| `game/engine/dungeon.py` | **New file** — `DungeonRoom`, `generate_dungeon()`, room type weight tables, dead-end tag pool |
| `game/ui/dungeon_puzzles.py` | **New file** — `run_riddle()`, `run_reveal()`, `run_maze()`, `run_sequence()`, `run_puzzle()` dispatcher; 22 riddles, 3 maze layouts, 5 sequences, 4 reveal objects |
| `game/ui/road.py` | `explore_event()` fully replaced; new helpers: `_loc_header()`, `_retreat_check()`, `_offer_loot()`, `_handle_combat_room()`, `_handle_trap_room()`, `_handle_puzzle_room()`, `_handle_secret_room()`, `_handle_dead_end()`, `_handle_boss_room()`, `_boss_clear_reward()`; new imports: `spawn_boss`, `generate_dungeon`, `ENEMY_TEMPLATES`, `spawn_enemy`, `run_puzzle` |

---

## Suggested PT14 Focus Areas

- **Dungeon navigation** — do directional labels read naturally? Do visited/sealed markers help?
- **Room variety** — does 5–8 rooms feel like the right density? Too short? Too long?
- **Boss difficulty** — are the bosses (HP × 1.6–1.9) appropriately dangerous without being unfair?
- **Boss drops** — are the unique items worth the boss fight? Are stats appropriately strong?
- **Puzzle types** — riddle difficulty vs. Dungeoneering scaling? Maze fog feel? Sequence clue clarity?
- **Dead ends** — do the atmospheric descriptions land? Too brief, too long?
- **Item integration** — do Grappling Hook / Lock Picks feel worth carrying? Is the Torch/Lantern difference meaningful?
- **Retreat** — does the new formula feel fair? Does Dungeoneering investment pay off?
- **Gating puzzles** — when a puzzle locks the only path to the boss, is that satisfying or frustrating?
