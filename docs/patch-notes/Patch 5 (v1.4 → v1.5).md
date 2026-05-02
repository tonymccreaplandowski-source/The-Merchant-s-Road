---
type: patch-notes
version: v1.4→v1.5
status: archived
systems:
  - merchant
  - stealth
  - ui
---

# Patch 5 — v1.4 → v1.5
**Date:** 2026-04-19
**Focus:** Magic Overhaul · Grimtotem System · Mage Enemies · Spell Self-Costs

---

## Spell System Overhaul

### New Spell Fields
All spells now carry additional metadata:

| Field | Purpose |
|---|---|
| `tier` | `"basic"` / `"mid"` / `"advanced"` |
| `require_magic` | Minimum Magic skill to cast |
| `self_cost` | HP paid at the moment of casting (regardless of outcome) |
| `lore` | Two-line flavour text shown when reading a grimtotem |

### Spell Roster (8 spells total)

| Spell | Tier | Mana | HP Cost | Require Magic | Notes |
|---|---|---|---|---|---|
| Frost Bolt | basic | 12 | 0 | 5 | Slows target (2 turns) |
| Shock | basic | 8 | 2 | 8 | Minor self-cost; reliable damage |
| Fireball | mid | 18 | 0 | 15 | High power vs unarmoured |
| Healing Word | mid | 14 | 0 | 20 | Restores HP |
| Shadow Step | mid | 16 | 0 | 25 | Grants player_evading state |
| Drain Life | mid | 14 | 8 | 30 | Necromancy; HP cost reflects dark magic |
| Lightning Arc | advanced | 22 | 3 | 40 | High power; minor life toll |
| Soul Rend | advanced | 30 | 15 | 55 | Necromancy nuke; steep HP cost |

### Self-Cost Mechanic
- HP is deducted **before** the spell roll, regardless of hit or miss.
- In the combat spell menu, self-cost spells show a red `−Xhp` suffix as a warning.
- Drain Life and Soul Rend require the player to spend their own vitality to cast — magic has consequences.

---

## Grimtotem System (Spell Acquisition)

Spells are no longer available by default. They must be **found and learned** via Grimtotems.

### Flow
1. Player obtains a Grimtotem (from a Mage Merchant, Librarian, or loot).
2. Player opens **Bag → Grimtotems** and selects the tome.
3. The game displays the spell name, its two-line lore, and what the spell does.
4. Prompt: *"Does this magic resonate with you?"*
   - **Yes** — spell added to `learned_spells`, journal entry recorded, grimtotem consumed.
   - **No** — grimtotem stays in inventory.

### Grimtotem Catalogue (8 tomes)

| Grimtotem | Spell | Rarity | Value |
|---|---|---|---|
| Grimtotem of Frost | Frost Bolt | common | 20g |
| Grimtotem of Shock | Shock | common | 15g |
| Grimtotem of Fire | Fireball | uncommon | 70g |
| Grimtotem of Mending | Healing Word | uncommon | 90g |
| Grimtotem of Shadows | Shadow Step | uncommon | 110g |
| Grimtotem of Draining | Drain Life | uncommon | 130g |
| Grimtotem of the Arc | Lightning Arc | rare | 280g |
| Grimtotem of Rending | Soul Rend | rare | 380g |

### Journal Integration
- Each learned spell adds a lore entry to the player journal — grimtotems become a record of magical study.

---

## Mage Merchant (New Merchant Type)

A dedicated spell-goods merchant added to the merchant pool.

- **Stock**: Grimtotems weighted by tier:
  - Basic (Frost/Shock): ~80% each
  - Mid tier: ~60% each
  - Advanced: ~30% each
- Tagline: *"Grimoires, tomes, and spells for those who seek power beyond the blade."*
- Skill bonus: **Magic** (Merchantilism negotiation still applies).

---

## Librarian — Grimtotem Probability

The Librarian now has a **low but real** chance of stocking grimtotems alongside lore texts:

- Basic grimtotems: 22% base + Magic bonus
- Mid grimtotems: 8% base + Magic bonus
- Advanced grimtotems: 2% base + Magic bonus

Tagline updated: *"Quiet, watchful — lore texts and possibility of finding tomes."*

---

## Starting Spells (Character Creation)

Starting spells are assigned based on Magic skill at character creation. Only non-advanced spells within the character's Magic threshold are eligible.

| Magic Skill | Spells Granted |
|---|---|
| < 15 | None |
| 15–34 | 1 random |
| 35–54 | 2 random |
| 55–74 | 3 random |
| 75–94 | 4 random |
| 95+ | Up to 5 |

Starting mana is capped at 20 regardless of Magic skill (prevents early-game mana abundance).

---

## Mana Formula (Rebalanced)

Mana now grows faster at high Magic — a meaningful reward for deep investment:

| Magic Range | Growth Rate |
|---|---|
| 1–20 | ×2 per point |
| 21–50 | +3 per point (above 20) |
| 51–80 | +4 per point (above 50) |
| 81–100 | +5 per point (above 80) |

Max mana at 100 Magic = **350**.

---

## Mage Enemies (3 New)

| Enemy | Type | Spells |
|---|---|---|
| Goblin Shaman | half_mage (35% cast) | Frost Bolt, Shock |
| Bandit Sorcerer | half_mage (35% cast) | Fireball, Shock, Frost Bolt |
| Skeleton Mage | mage (65% cast) | Frost Bolt, Shadow Step, Drain Life |

### Enemy Spell Casting Rules
- `half_mage`: 35% chance per turn to cast instead of using a physical attack.
- `mage`: 65% chance per turn to cast.
- Enemies cast spells for free (no mana cost).
- Spell damage uses enemy `combat_skill` vs player `defense`, with armor effectiveness applied.
- Evade mechanic (50% dodge chance) applies to enemy spells.
- Defensive stance reduces spell damage by 20% (spells pierce armour better than physical attacks).

### Combat Message Updates
- Enemy attack messages now distinguish spell casts (`casts <spell>`) from physical moves (`retaliates with <move>`).
- Applies to both the initiative-loss block and the main combat counter-attack block.

---

## Version String
Updated to `Alpha - World v1.5 | Magic Overhaul`

---

## Known Issues (Carried Forward)
- `engine/world.py` imports `random_cave`, `random_castle` from `engine/events.py` — these names are missing, causing an import error on full game load. Flagged for a dedicated patch.
