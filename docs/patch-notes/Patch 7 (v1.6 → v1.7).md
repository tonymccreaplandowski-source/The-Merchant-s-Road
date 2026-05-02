---
type: patch-notes
version: v1.6→v1.7
status: archived
systems:
  - combat
  - merchant
  - ui
---

# Patch 7 — v1.6 → v1.7
**Date:** 2026-04-19
**Focus:** Location Entry System — Room Navigation · Stealth Entry · Dungeoneering Scout

---

## Overview

Caves and castles now have a full entry gate and room-by-room navigation system. Players no longer auto-commit to a location on sight — they can gather information, attempt a stealth approach, and choose to retreat between rooms.

---

## Entry Gate (replaces 2-option prompt)

When a cave or castle is discovered on the road, the player sees the location name, description, and `Enemies within: ???`. Three actions are available before committing:

### Scout the Area *(Dungeoneering)*
`d20 + Dungeoneering ÷ 5` vs difficulty **10** — one use only.
- **Success:** `???` is replaced with the actual enemy count (e.g. `Enemies within: 3`)
- **Fail:** `"You couldn't make out much from the entrance."`

### Attempt Stealth *(Stealth)*
`d20 + Stealth ÷ 5` vs difficulty **12** — one use only.
- **Success:** First enemy is surprised — player guaranteed initiative + enemy `combat_skill −10` for 2 rounds
- **Fail:** `"You fumble the approach. No advantage gained."`

Both options can be used before entering (Scout first, then Stealth, then Enter). Neither is required.

### Enter Boldly
Commits to the location with no checks.

### Pass By
Continue on the road with no consequence.

---

## Room-by-Room Navigation

Each enemy inside a location now occupies its own room. After clearing a room (except the final one) the player is shown a mid-room screen and given a choice.

### Mid-Room Screen
- Shows `Room X of Y` if Dungeoneering revealed the count, otherwise `"Deeper still..."`
- `"Room X cleared."`
- **30% chance:** a common item is found — player can take it or leave it
- **70% chance:** `"Nothing of interest."`
- Two options: `Press deeper` or `Retreat (leave location)`

Retreating mid-dungeon exits with whatever was collected — no final loot and no lore entry.

### Final Room
Clears as before: 2 loot drops (biased by location type) + lore journal entry if available.

---

## Combat Changes

`run_combat()` now accepts an optional `force_first: bool` parameter.
- When `True`: skips the initiative roll and guarantees the player acts first
- Used by stealth ambush on room 1 of a location

---

## Version String
Updated to `Alpha - World v1.7 | Location Entry System`

---

## Known Issues (Carried Forward)
- `engine/world.py` imports `random_cave`, `random_castle` from `engine/events.py` — these names are missing, causing an import error on full game load. Flagged for a dedicated patch.
