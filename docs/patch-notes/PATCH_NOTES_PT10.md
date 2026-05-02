---
type: patch-notes
version: v2.6
status: archived
systems:
  - ui
  - combat
  - merchant
  - world
---

# Patch Notes — Play Test 10
**Date:** 2026-04-21  
**Session:** PT10 Review & Fix Pass  
**Files Modified:** `main.py`, `ui/display.py`, `engine/combat.py`, `data/enemies.py`, `data/cities.py`

---

## Issues Fixed

### Issue 1 — Item Description Truncation
**Problem:** Item descriptions in the buy screen were cut at 50 characters, making them unreadable mid-word.  
**Fix:** Raised truncation limit to 65 characters (`item.description[:65]`) with a trailing `…` indicator.  
**File:** `main.py`

---

### Issue 2 — Road Flavor Text Timing
**Problem:** Flavor text appeared after the road menu selection, making the world feel reactive rather than atmospheric.  
**Fix:** Rewrote `road_loop` with a `_first_step` flag. The first step shows a "You step foot on the road to [dest]" message before the menu. Every subsequent iteration shows a flavor line at the top of the loop, before choices are presented.  
**File:** `main.py`

---

### Issue 3 — Combat Message Double Typewrite Animation
**Problem:** The same combat message re-animated on every screen redraw (e.g. when displaying the move menu), causing jarring repeated typewriter effects.  
**Fix:** Added a `_last_combat_message` module-level tracker in `display.py` and a `reset_combat_message()` function called at the start of each new combat. New messages typewrite at full speed; repeated messages print instantly with a quieter `»` prefix.  
**Files:** `ui/display.py`, `main.py`

---

### Issue 4a — Bandit Sorcerer AI Type
**Problem:** Bandit Sorcerer was classified as `half_mage` (35% spell chance), despite being described as a magic-focused enemy.  
**Fix:** Changed `enemy_type` to `"mage"` (65% spell cast chance per round).  
**File:** `data/enemies.py`

---

### Issue 4b — Enemy Damage Scaling
**Problem:** Enemy physical damage was calculated from raw move power only, ignoring the attacker/defender skill differential. Enemy hits felt inconsistent and didn't scale meaningfully with combat stats.  
**Fix:** Added a `skill_mod` multiplier to enemy physical attacks, mirroring the player-attack formula: `max(0.5, min(1.5, 1.0 + (combat_skill - player.defense) / 200.0))`. Applied to both the defensive-block branch and the normal hit branch.  
**File:** `engine/combat.py`

---

### Issue 4c — Hit Formula Too Permissive
**Problem:** The d20 hit check threshold was `defender_defense // 4 + 2`, making high-defense targets nearly as easy to hit as low-defense ones at low attacker skill.  
**Fix:** Tightened threshold to `defender_defense // 3 + 3`, making defense a more meaningful stat against weaker attackers.  
**File:** `engine/combat.py`

---

### Issue 5 — Scarcity Pricing Not Visibly Premium
**Problem:** Scarce city sell prices (modifier 1.35 × 0.65 = 0.878×) were *below* item base value, undermining the arbitrage incentive. Players sold scarce goods for less than they paid elsewhere.  
**Fix:** Raised scarce modifier from `1.35` to `1.60`. Scarce-city sell prices now exceed base value (1.60 × 0.65 = 1.04×). Buy prices at scarce cities are also appropriately elevated (1.60 × 1.30 = 2.08× base).  
**File:** `data/cities.py`

---

### Issue 6 — Training & Merchant Screens Exit Too Aggressively
**Problem:** The skill training screen and merchant buy/sell tabs both returned to the parent menu after a single action, requiring the player to navigate back in for each transaction.  
**Fix:** Wrapped `train_skills` in a `while True` loop with `pause()` between sessions. Added inner `while True` loops to both the Buy and Sell merchant tabs with explicit `← Leave` options, so players stay in the screen until they choose to exit.  
**File:** `main.py`

---

### Issue 7 — Hunt Option Hidden Without Bow
**Problem:** The hunt option in Bushcraft was not shown at all when the player had no bow, giving no feedback about why it was unavailable.  
**Fix:** Hunt option is always visible. When no bow is equipped, it displays as disabled with an explanation: `(requires a bow)`.  
**File:** `main.py`

---

### Issue 8 — Character Sheet Inaccessible on Road
**Problem:** The Character Sheet could only be accessed from cities, not from the road menu.  
**Fix:** Added "Character Sheet" as Option 5 on the road menu. "Turn back" shifted to Option 6.  
**File:** `main.py`

---

### Issue 9a — Cannot Use Consumables Outside Combat
**Problem:** Potions and consumable items had no use function outside of combat, forcing unnecessary pre-combat planning or wasteful item hoarding.  
**Fix:** Added `use_item_outside_combat()` and `use_items_screen()` functions. "Use Item" is now Option 3 in the bag screen with a filtered list of items usable outside combat.  
**File:** `main.py`

---

### Issue 9b — Combat Item Filter Showing Wrong Items
**Problem:** The in-combat item list was showing non-consumable items, cluttering combat choices.  
**Fix:** Combat item filter now correctly checks `item.item_type in ("potion", "consumable") and item.effect`.  
**File:** `main.py`

---

### Issue 10 — Merchant Availability Too Unpredictable
**Problem:** All merchants had the same 33% availability roll, meaning essential vendors (Blacksmith, Librarian) were frequently absent with no explanation.  
**Fix:** Introduced two tiers: `_GUARANTEED_MERCHANTS` (Blacksmith, Survival Trader, Librarian, Dungeoneering Co.) always appear; variable merchants (Alchemist, Fence, Enchanter) roll at 33% chance. Rewrote `generate_city_merchants` and `visit_market` accordingly. Availability persists per city visit session.  
**File:** `main.py`

---

### Issue 11 — Firewood Scarcity Price Indistinguishable From Base
**Problem:** Scarce items (e.g. Firewood in Greyspire) showed the same gp value as their base price due to the low 1.35 modifier. The `▲ (scarce)` label appeared with no visible price premium.  
**Fix:** Resolved by the scarcity modifier fix (Issue 5). With modifier 1.60, sell prices exceed base value. Buy prices at scarce cities are now meaningfully higher (2.08× base).  
**Files:** `data/cities.py`, `main.py` (sell screen already shows `base Xgp` for comparison)

---

### Issue 12 — Skull Ring [CURSED] Penalty Not Applied or Visible
**Problem:** The Skull Ring displayed a `[CURSED]` tag but neither warned the player of the specific penalty before equipping, nor applied any visible HP consequence after equipping.  
**Fix (display):** Added cursed HP penalty indicator to the Character Sheet vitals line: `[CURSED −20 max HP]` shown in red next to the HP bar when a `reduce_max_hp` cursed item is equipped.  
**Fix (equip flow):** Pre-equip warning now shows the specific curse effect description and the item's stat bonuses, with a confirm/cancel prompt. Post-equip message shows the actual HP change: `Curse applied: Max HP X → Y`.  
**Files:** `ui/display.py`, `main.py`

---

## File Integrity Notes

During this session, three files were found to have been truncated mid-content (likely from prior edit operations):

- `ui/display.py` — truncated at line 587, mid-expression in the skills loop. Missing: skills display completion, learned spells section, `pause()`, and `show_journal()`. **Restored.**
- `data/enemies.py` — truncated at line 269, mid-expression in `get_enemy_for_biome`. Missing: final fallback line and `return` statement. **Restored.**
- `data/cities.py` — truncated at line 110, mid-expression in `get_road_biome`. Missing: closing return and entire `get_adjacent_city_keys` function. **Restored.**

All five modified files pass `python -m py_compile` with no errors.

---

## Compile Status (post-fix)

| File | Status |
|---|---|
| `ui/display.py` | ✓ OK |
| `engine/combat.py` | ✓ OK |
| `data/enemies.py` | ✓ OK |
| `data/cities.py` | ✓ OK |
| `main.py` | ✓ OK |
