---
type: patch-notes
version: v2.1→v2.2
status: archived
systems:
  - merchant
  - negotiate
  - world
---

# Patch 12 — Play Test 5 Fixes (v2.1 → v2.2)
**Date:** 2026-04-20
**Session:** Play Test 5 feedback pass + critical crash fix

---

## Critical Bug Fix

**Enemy.moves crash** (`engine/combat.py` line 261)
- `enemy_attack()` referenced `enemy.moves` which did not exist on the `Enemy` dataclass
- Added `moves: List[str] = field(default_factory=list)` to the `Enemy` dataclass in `enemies.py`
- Populated all 14 enemy templates with thematically appropriate move sets drawn from the `MOVES` dict
- Updated `spawn_enemy()` to pass `moves` from the template
- This was the crash reproduced with both Bandit Cutthroat and Goblin Shaman during Play Test 5

---

## Balance Changes

**Skill points at character creation: 180 → 100**
- `STARTING_POINTS` reduced from 180 to 100 in `engine/player.py`
- Per-skill cap of 40 added at character creation (`MAX_CREATION_SKILL = 40`)
- Cap enforced in `character_creation()` via `max_allowed` logic
- Mid-game skill upgrades (training hall) remain uncapped — this only gates creation
- Display text updated to inform the player cap exists and skills can grow past it through play

**Stealth entry probability rebalanced**
- Old system: `d20 + Stealth//5 >= 12` → at Stealth 5 this gave ~50% success rate
- New system: flat % formula `success = clamp(0.05, 0.95, 0.15 + (stealth - 5) * 0.013)`
- Stealth 5 → 15% success | Stealth 20 → ~34% | Stealth 40 → ~59% | hard cap 95%
- TK's repeated successful stealth entries at skill 5 should no longer be possible

**Spell access gated behind purchasing**
- `get_available_spells()` call in combat now passes `player.learned_spells`
- High Magic skill no longer grants access to spells the player hasn't purchased
- Players with no learned spells see a clear message directing them to a Mage Merchant
- `_assign_starting_spells()` already uses `learned_spells`; combined with the 40-skill creation cap, a max-creation Magic of 40 yields 2 starting spells at most

---

## Gameplay Changes

**Block resource use at full HP**
- `make_camp()` now checks `player.hp >= player.max_hp` before consuming firewood and food
- Players at full health are redirected with a short message and their supplies are preserved

**Foraging encounters**
- `_do_forage()` now runs an encounter check before the foraging success roll
- 14% chance: enemy spawned from the current road biome pool — combat runs, loot drops on win
- 6% chance: location (cave or castle) spotted — `explore_event()` triggered
- After any encounter, foraging attempt continues normally
- Encounter chance is independent of foraging success/failure

---

## UI / Content

**Skill reference guide added to Bag**
- New `show_skill_guide()` function added to `main.py`
- Accessible from the Bag menu (road and city) as "Skill Guide"
- Covers all 7 skills with plain-language descriptions of what each governs — no math, just concept
- Designed for reference during character creation and skill upgrade decisions

**Merchant greetings**
- Each merchant now delivers a unique greeting line on first approach
- 4 lines per merchant type, drawn at random and stored on the merchant dict for the visit
- Subsequent interactions show the tagline instead (greeting is a one-time moment of character)
- Types covered: Blacksmith, Apothecary, Librarian, Survival Trader, Dungeoneering Co., Leatherworker, Mage Merchant

**Dark Souls-style item descriptions (lore field)**
- Every item now carries a `lore` field: one cryptic line implying a history that isn't real but feels real
- Format: mechanical note (if relevant) + a name, fate, or location fragment — esoteric, never explanatory
- Displayed in the character sheet inventory beneath each item line
- Examples:
  - *Skull Ring*: "Cursed: -20 max HP. +8 Martial. Ser Rodrick was found wearing this. Drowned in his own blood, in a dry room."
  - *Grimtotem of Rending*: "Teaches: Soul Rend. No author, no date, no origin. The ink is not ink."
  - *Firewood*: "Cut from a fallen oak near Waldheim. The locals don't cut the standing ones anymore."

**Music volume reduced ~50%**
- All ambient loop beep durations halved in `ui/display.py`
- Affects: road, city, dungeon, and tension ambient loops
- Silence/pause durations unchanged — rhythm preserved, intensity reduced
- Non-ambient melodies (combat_start, victory, death, etc.) unchanged

---

## Deferred to Expansions.md

- **Stealth entry minigame** (Play Test 5 Item 6): "Strike stealthily vs. steal from room" — logged with full design notes
- **Class pick screen at game start** (Tony's idea): logged with archetype concepts and implementation notes

---

## Files Modified

| File | Change |
|---|---|
| `data/enemies.py` | Added `moves` field to `Enemy` dataclass; populated all 14 templates; updated `spawn_enemy()` |
| `data/items.py` | Added `lore` field to all items across all categories |
| `engine/player.py` | `STARTING_POINTS` 180→100; added `MAX_CREATION_SKILL = 40` |
| `engine/combat.py` | No changes (crash was in enemies.py + calling code) |
| `main.py` | Spell gate fix; skill cap enforcement; full-HP camp block; foraging encounters; skill guide; merchant greetings; stealth rebalance |
| `ui/display.py` | Ambient loop durations halved; lore display in character sheet inventory |
| `Expansions.md` | Added entries 6 (stealth minigame) and 7 (class pick screen) |
