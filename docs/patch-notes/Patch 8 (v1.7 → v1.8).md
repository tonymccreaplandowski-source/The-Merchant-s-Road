---
type: patch-notes
version: v1.7→v1.8
status: archived
systems:
  - combat
  - merchant
---

# Patch 8 — v1.7 → v1.8
**Date:** 2026-04-19
**Focus:** Weapon Move Skill Synergies — Bow Build Diversity

---

## Overview

The three bow moves now each reward a distinct skill investment, giving archer builds meaningful differentiation based on character build.

---

## Bow Move Synergy Matrix

| Move | Special | Skill | Damage Bonus | State Effect |
|---|---|---|---|---|
| Pot Shot | `survival_boost` | Survival | ×(1 + Survival ÷ 200) | Sets `player_evading` (50% counter miss) |
| Snipe | `stealth_boost` | Stealth | ×(1 + Stealth ÷ 100) | None |
| Long Shot | `martial_boost` | Martial | ×(1 + Martial ÷ 200) | None |

Snipe and Long Shot were already implemented. This patch adds Survival synergy to Pot Shot.

---

## Pot Shot Changes

**Before:** Special was `evade` — evade state only, no damage scaling.

**After:** Special is `survival_boost` — Survival-scaled damage multiplier *and* evade state (both effects preserved).

- A Survival 50 character gets ×1.25 damage on Pot Shot
- A Survival 100 character gets ×1.50 damage on Pot Shot
- The evade state (50% counter miss chance) still applies regardless of Survival level
- Description updated: *"A quick shot on the move. Boosted by Survival — harder to pin down."*

---

## Design Rationale

Each bow move is now tied to a different skill tree:
- **Survival** (Pot Shot) — ranger/outdoorsman; quick opportunistic shots from experience in the field
- **Stealth** (Snipe) — stalker/assassin; patient, precise shots from concealment
- **Martial** (Long Shot) — fighter; physical strength and combat training behind the draw

A bow character's most effective move is determined by where they invested their starting points.

---

## Files Changed
- `data/weapons.py` — Pot Shot special changed to `survival_boost`, description updated, docstring updated
- `engine/combat.py` — `survival_boost` added to `calculate_damage()` and `apply_move_special()`

---

## Version String
Updated to `Alpha - World v1.8 | Weapon Skill Synergies`

---

## Known Issues (Carried Forward)
- `engine/world.py` imports `random_cave`, `random_castle` from `engine/events.py` — these names are missing, causing an import error on full game load. Flagged for a dedicated patch.
