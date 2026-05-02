---
type: patch-notes
version: v2.4→v2.5
status: archived
systems:
  - stealth
  - character
  - ui
  - world
---

# Patch 15 — v2.4 → v2.5
**Date:** 2026-04-20
**Session:** Play Test 8 Feedback Pass

---

## Bug Fixes

### Critical — `armor.armor_type` crash on enemy attack
- **File:** `data/items.py`, `engine/combat.py`
- **Root cause:** The `Item` dataclass had `armor_value` but no `armor_type` field. `combat.py` referenced `armor.armor_type` directly in `enemy_attack()` and `cast_enemy_spell()` — crashing whenever the player had armour equipped during combat.
- **Fix:** Added `armor_type: Optional[str] = None` to `Item` dataclass. All five armour items populated with correct type: Padded Jacket → `"cloth"`, Leather Vest → `"leather"`, Chain Hauberk / Scale Armour / Plate Cuirass → `"mail"`. All `armor.armor_type` references in `combat.py` changed to `getattr(armor, "armor_type", None) or "none"` for safety.

---

## UX Improvements

### Travel options consolidated
- **File:** `main.py` — `city_loop()`
- Per-city "Travel to X" options removed from the main city menu.
- Replaced with a single **"Travel"** option. Selecting it shows a sub-menu: "Where would you like to go?" with all available destinations listed. Back option returns to city menu.

### Procedural road flavor lines
- **File:** `main.py`
- Added `ROAD_FLAVOR` dict and `_road_flavor_line()` helper.
- Each road step now prints a random flavor line after the step resolves.
- Lines are **biome-aware** (forest / desert / mountain / cave each have their own voice) and **phase-aware** (early-journey lines feel fresh and open; late-journey lines feel worn-in and close to arrival). Each pool has 5 lines per phase.
- Falls back to generic lines for unrecognised biomes.

### Pause before road encounters
- **File:** `main.py` — `road_loop()`
- Replaced `time.sleep(1.2)` with `pause("Press Enter to engage...")` when an enemy appears on the road.
- Enemy name is now typewritten rather than printed. Player must confirm before combat begins.

### Pokémon-style combat animation
- **Files:** `ui/display.py`, `main.py`
- Combat message lines (`»`) are now rendered via `typewrite()` (character-by-character animation) instead of plain `print()`.
- After each combat screen render in the main combat loop, a `pause("Press Enter...")` prompt appears — the player confirms they've read the result before the action menu loads. Empty-message displays (no prior action) skip the pause.

### Dungeoneering scout — tiered results
- **File:** `main.py` — `explore_event()`
- Threshold raised and formula adjusted: `d20 + (Dungeoneering // 4)`.
- **Three tiers:**
  - **Fail (< 12):** "You couldn't make out much from the entrance."
  - **Partial (12–17):** Approximate count ±1. "You make out movement — roughly X enemies, maybe more."
  - **Full success (18+):** Exact count. Low-skill characters will fail more often and receive imprecise information when they do succeed.

---

## Files Changed
- `game/main.py`
- `game/engine/combat.py`
- `game/data/items.py`
- `game/ui/display.py`
