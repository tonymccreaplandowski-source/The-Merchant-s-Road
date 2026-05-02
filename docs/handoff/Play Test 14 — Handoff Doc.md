---
type: handoff
version: v2.8
status: active
systems:
  - dungeon
  - items
  - world
  - ui
date: 2026-04-27
---

# Play Test 14 — Handoff Document

**Date:** 2026-04-27
**Version:** Alpha - World v2.8 | Explorable Dungeons Pass
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

## Session Summary

Full overhaul of the location/exploration system. The old linear room-by-room
combat queue has been replaced with a procedurally generated branching dungeon
graph. Each location visit now produces 5–8 rooms across a main branch (combat +
boss) and side branches (traps, puzzles, secrets, dead ends). Navigation uses
per-location directional labels. Four puzzle mini-game types were built from
scratch. All orphaned dungeoneering merchant items now have mechanical dungeon
roles. Named unique boss drops were added for all six existing locations.

---

## New Files

| File | Description |
|---|---|
| `game/engine/dungeon.py` | Room graph engine — `DungeonRoom` dataclass + `generate_dungeon()` |
| `game/ui/dungeon_puzzles.py` | Four puzzle mini-games: riddle, reveal, maze, sequence + dispatcher |

---

## Files Modified

| File | Change |
|---|---|
| `game/data/items.py` | Added `BOSS_LOOT_ITEMS` (6 named unique items); `ITEM_LOOKUP` includes boss items; pool comment clarifies they are excluded from random generation |
| `game/engine/events.py` | `RoadEvent` extended with `boss_name`, `boss_hp_mult`, `boss_dmg_mult`, `boss_drop_name`, `nav_labels`; all 6 events populated; `spawn_boss()` helper added |
| `game/ui/road.py` | `explore_event()` fully replaced; 9 new handler functions; new imports for dungeon engine and enemy spawning |

---

## Architecture Reference

### Dungeon Generation (`engine/dungeon.py`)

```python
DUNGEON_SIZE_RANGE = (5, 8)   # adjustable — total rooms per run

generate_dungeon(event) → Dict[int, DungeonRoom]
# Room 0 = entry. Boss room has .is_boss == True.
# Main branch: entry → combat(s) → boss
# Side branches: trap / puzzle / secret / dead_end
```

Room type weight tables in `ROOM_TYPE_WEIGHTS` — separate configs for `"cave"` and `"castle"`.

### Puzzle System (`ui/dungeon_puzzles.py`)

```python
run_puzzle(player, puzzle_type, timed=False, gating=False) → bool
# puzzle_type: "riddle" | "reveal" | "maze" | "sequence"
# timed: enables time limit on maze (30s base + 5s per 5 Dungeoneering)
# gating: True = failure locks this path, Lock Picks can bypass
```

- **Riddle:** 22 scripted questions, free-text answer, 1 attempt
- **Reveal:** Health-bar obscured object, 3 examination rounds, final multiple-choice guess
- **Maze:** 3 layouts, WASD via `msvcrt` (Windows only; falls back to skill check elsewhere), fog of war
- **Sequence:** 5 puzzles, 3-symbol ordered lock, Dungeoneering scales clue clarity

### Boss Spawning (`engine/events.py`)

```python
spawn_boss(event) → Enemy
# Takes highest-HP-ceiling biome template
# Applies boss_hp_mult to max_hp, boss_dmg_mult to combat_skill
# Sets enemy name to event.boss_name
```

### Retreat Formula (`ui/road.py`)

```python
# d100 ≤ (Dungeoneering + Stealth + Survival) / 3
# Grappling Hook: +30 to threshold (consumed)
# Rope: +15 to threshold (consumed)
# Miss by ≤ 20: −5 to −12 HP
# Miss by > 20: −15 to −25 HP
# Player always escapes — roll only determines cost
```

### Dungeoneering Item Hooks

| Item | Where Checked | Effect | Consumed? |
|---|---|---|---|
| Adventurer's Map | Pre-entry | Reveals 2 room types ahead | Yes |
| Torch Bundle | Dungeon entry | Maze fog radius 1→2, trap +2, secret +4 | Yes |
| Lantern | Dungeon entry | Maze fog radius 1→3, trap +5, secret +8, reveal +4 | No |
| Tinderbox | Dungeon entry | Prerequisite to activate Torch/Lantern | No |
| Lock Picks | Puzzle gate / secret | Bypass gating puzzle OR +1 loot in secret | Yes |
| Rope | Retreat | +15 to retreat threshold | Yes |
| Grappling Hook | Retreat | +30 to retreat threshold | Yes |

### Boss Drop Items

| Item | Location | Slot | Key Stats |
|---|---|---|---|
| Warden's Hide Wraps | The Hollow Den | Armor (leather, AV 8) | +5 Stealth, +3 Survival, +2 Dungeoneering |
| Tideborn Pendant | The Dripping Grotto | Necklace | +6 Magic, +4 Dungeoneering |
| Shadow Fingers | The Smuggler's Cache | Ring | +7 Stealth, +3 Merchantilism |
| Castellan's Vow | The Broken Keep | Armor (mail, AV 14) | +5 Martial, +3 Survival, −2 Stealth |
| Captain's Verdict | The Forsaken Garrison | Weapon (sword) | +5 Martial, +4 Speechcraft |
| Folly Signet | The Merchant Lord's Folly | Ring | +6 Merchantilism, +4 Speechcraft |

---

## Deferred / Out of Scope

The following were discussed or noted but not actioned this session:

1. **Dungeon minimap display** — ASCII map of discovered rooms. Discussed during design, opted for directional nav instead. Can be added as a Dungeoneering-gated option.
2. **Hunger drain inside dungeons** — currently hunger drains only on road steps. Dungeon rooms do not tick hunger. Could add per-room drain for longer runs.
3. **Boss variant spells** — boss enemies draw the highest-HP template but don't have boss-specific spell lists. Could add boss-unique spells or abilities in a future pass.
4. **Additional maze layouts** — launched with 3. Can expand easily by adding to `MAZE_LAYOUTS` list in `ui/dungeon_puzzles.py`.
5. **Additional puzzle pool expansion** — 22 riddles, 5 sequences at launch. Can grow both lists without any structural changes.
6. **Grappling Hook castle alternate route** — the design specified unlocking an "upper route" exit in castle events. The retreat bonus is implemented but the alternate path was not wired into dungeon generation. Requires per-event exit logic.

---

## State Handed Forward

The full dungeon system is implemented and all imports verified clean. The game
runs normally on Windows — the `msvcrt` dependency in the maze puzzle degrades
gracefully to a skill check on non-Windows platforms (sandbox/CI safe).

**Key things to watch during PT14:**

- The `explore_event()` function in `ui/road.py` is the main entry point — all
  dungeon logic flows from there via the room graph loop
- `DungeonRoom.solved` is the field that tracks whether a gating puzzle was
  passed — navigation checks this to lock/unlock exits
- Boss drops are in `ITEM_LOOKUP` but NOT in `ALL_ITEMS` — they are intentionally
  excluded from the random loot pool. Do not move them into `ALL_ITEMS`
- `DUNGEON_SIZE_RANGE` in `engine/dungeon.py` is the first thing to adjust if
  rooms feel too many or too few

---

## Next Play Test Goals (PT14)

- Does directional navigation feel natural, or do the labels feel arbitrary?
- Is 5–8 rooms the right density per location visit?
- Are bosses appropriately difficult? Does the HP × 1.6–1.9 multiplier feel dangerous without being unfair?
- Do boss unique drops feel worth earning? Are stat bonuses well-balanced?
- Riddle difficulty — does Dungeoneering scaling on the clue feel meaningful?
- Maze fog and time pressure — is the timed/untimed 50/50 split working? Is the time generous enough?
- Dead end rooms — do the atmospheric descriptions land? Are they the right length?
- Dungeoneering items — does carrying a Grappling Hook or Lock Picks feel like a real decision?
- Retreat risk — is the new three-skill formula fair? Does Dungeoneering investment pay off noticeably?
- Gating puzzle moments — satisfying or frustrating when the only path to the boss is locked behind a puzzle?
