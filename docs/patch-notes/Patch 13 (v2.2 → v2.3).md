---
type: patch-notes
version: v2.2→v2.3
status: archived
systems:
  - combat
  - merchant
  - world
---

# Patch 13 — v2.2 → v2.3
**Date:** 2026-04-20
**Session:** Play Test 6 Feedback Pass

---

## Bug Fixes

### Critical — Combat crash on physical enemy attack
- **File:** `engine/combat.py` — `enemy_attack()`, lines 284 and 291
- **Root cause:** Both lines used `move.get("power", enemy.base_damage)` as a damage fallback. Python evaluates all function arguments eagerly, so `enemy.base_damage` was accessed every time regardless of whether the move had a `"power"` key. `base_damage` was never defined on the `Enemy` dataclass — a ghost attribute left over from earlier authoring.
- **Effect:** Every physical enemy attack crashed with `AttributeError: 'Enemy' object has no attribute 'base_damage'`. Confirmed crash trigger: foraging encounter with Bandit Cutthroat.
- **Fix:** Replaced both instances of `enemy.base_damage` with `max(5, enemy.combat_skill // 3)` — a derived fallback that scales with enemy strength and requires no dataclass changes.

---

## Content

### City ambient music — loop extended
- **File:** `ui/display.py` — `_MELODIES["ambient_city"]`
- **Change:** Added 12 new notes as a second musical phrase (total: 24 notes).
- **Character:** Continues in C major — ascends to A4 peak, resolves back down through B3 to C4 with a long closing pause. Feels like a natural second half to the existing phrase.

---

## Notes

- Road ambient music unchanged.
- No changes to enemy templates, player dataclass, or game logic.
- `enemy.base_damage` is confirmed absent from the entire codebase — the fallback in `combat.py` was the only reference.

---

## Files Changed
- `game/engine/combat.py`
- `game/ui/display.py`
