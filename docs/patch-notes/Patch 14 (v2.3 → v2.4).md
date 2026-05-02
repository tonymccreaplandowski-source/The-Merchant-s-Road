---
type: patch-notes
version: v2.3→v2.4
status: archived
systems:
  - negotiate
  - merchant
  - character
---

# Patch 14 — v2.3 → v2.4
**Date:** 2026-04-20
**Session:** Play Test 7 Feedback Pass

---

## Bug Fixes

### Tinderbox description truncated in buy screen
- **File:** `main.py` — buy screen item option builder
- **Root cause:** `item.description[:40]` hard-sliced all descriptions at 40 characters. "Flint and steel. Never leave town without one." is 46 chars — the last 6 characters were cut.
- **Fix:** Increased to `[:50]` with a trailing `…` appended if the description exceeds 50 chars.

### Grim Totem READ option produced nothing
- **File:** `main.py` — `read_book_menu()`
- **Root cause:** The city "Read a Book" menu filtered `item_type == "book"` only. Grimtotems have `item_type == "grimtotem"` and never appeared there. Players who bought a grimtotem and went to "Read a Book" saw nothing.
- **Fix:** `read_book_menu()` now handles both books and grimtotems. Books appear first (add lore to journal), grimtotems appear second (calls `read_grimtotem()`). City menu option renamed from "Read a Book" to "Read". The readable-items counter in the city menu now counts both types.

### SPELL_REGISTRY crash in character sheet
- **File:** `ui/display.py` — `show_character_sheet()`
- **Root cause:** `from data.spells import SPELL_REGISTRY` — `SPELL_REGISTRY` does not exist in `spells.py`. Only `SPELLS` is exported. This would crash when viewing the character sheet with a player who has learned spells.
- **Fix:** Changed to `from data.spells import SPELLS` with correct dict-key access throughout.

---

## New Features

### Inventory moved to Bag menu
- **Files:** `ui/display.py`, `main.py`
- Inventory section removed from Character Sheet (`show_character_sheet()`). Character Sheet now shows: stats, equipment, skills, and spells only.
- New `show_inventory_screen()` function added to `main.py`.
- Bag menu updated: now has 4 options — Gear / Inventory / Journal / Skill Guide.

### Unknown Berries — sickness risk
- **Files:** `engine/player.py`, `main.py`
- Added three new fields to `Player` dataclass: `sick_skill` (str), `sick_days` (int), `sick_penalty` (int).
- `player.skill()` now subtracts `sick_penalty` from the affected skill while `sick_days > 0`.
- Eating Unknown Berries now has a **5% (1-in-20)** chance of triggering sickness: a random skill is debuffed by 5–15 points for 1–5 road steps.
- Sick days decrement each road step with a status message. Clears automatically on expiry, on city arrival, or when Herb Bundle is used.
- Previous 20% poison chance (flat -15 HP) replaced entirely by the new sickness system.

### Character Creation — Class Selection Screen
- **Files:** `engine/player.py`, `main.py`
- `MAX_CREATION_SKILL` reduced from 40 to 20 (minor skills only).
- New constant: `DOMINANT_SKILL_VALUE = 30`.
- New `CLASS_CHOICES` list: 21 classes, one for each unique skill pairing across all 7 skills.
- New `class_selection_screen()` function: paginated display (7 per page), confirm screen with class lore, dominant skill preview, and minor-skill point reminder.
- `character_creation()` updated: class selection now comes first. Dominant skills are locked at 30. Player then spends remaining 40 points across the other 5 skills (min 5, max 20 each). Class name shown on creation confirmation.

**All 21 classes:**
Mage · Warrior · Knight · Adventurer · Battlemage · Bard · Assassin · Ranger · Smuggler · Scholar · Merchant · Pathfinder · Alchemist · Infiltrator · Mercenary · Hexblade · Delver · Shaman · Wayfarer · Chronicler · Prospector

---

## Files Changed
- `game/main.py`
- `game/engine/player.py`
- `game/ui/display.py`
