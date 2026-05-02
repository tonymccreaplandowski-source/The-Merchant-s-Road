---
type: patch-notes
version: v1.8→v1.9
status: archived
systems:
  - merchant
  - negotiate
---

# Patch 9 — v1.8 → v1.9
**Date:** 2026-04-19
**Focus:** Negotiation Expansion — All 7 Skills · Sharpened Tiers · Sell-Side Bonus

---

## Overview

The negotiation minigame now surfaces all seven player skills as usable tactics, introduces a sharper discount curve that rewards flawless runs significantly more, and makes the sell-side bonus explicit in the merchant UI.

---

## New Tactics (3 Added)

| Tactic | Skill | Flavour |
|---|---|---|
| Read the room | Survival | "You hint at what you have survived. They sense it." |
| Let silence speak | Stealth | "You say nothing. The quiet unnerves them more than words." |
| A show of power | Magic | "You let something flicker. They reconsider their position." |

All 7 skills now have a negotiation tactic. Full tactic list:

1. Appeal to shared interests — Merchantilism
2. Flatter their craftsmanship — Speechcraft
3. Share a useful rumour — Dungeoneering
4. Stand your ground — Martial
5. Read the room — Survival
6. Let silence speak — Stealth
7. A show of power — Magic

---

## Discount Tier Changes

| Rounds Won | Old Discount | New Discount | Sell Bonus |
|---|---|---|---|
| 0 | −8% penalty | −8% penalty | −8% sell penalty |
| 1 | +5% | +2% | +2% |
| 2 | +10% | +10% | +10% |
| 3 | +18% | **+25%** | **+25%** |

The low end is softer (2% for a single win barely matters), the ceiling is significantly higher (25% flawless reward vs 18% before). Mediocre negotiation barely moves the needle — excellent negotiation is now genuinely impactful.

---

## Sell-Side Bonus

The sell bonus was already calculated via `_sell_price` using `2.0 - discount` internally, but was never shown to the player. It is now explicitly displayed in the merchant header:

```
[25% buy discount | +25% sell bonus]
```

The buy discount and sell bonus are always equal — a 25% discount on purchases means the merchant also pays 25% more for your goods.

---

## Version String
Updated to `Alpha - World v1.9 | Negotiation Expansion`

---

## Known Issues (Carried Forward)
- `engine/world.py` imports `random_cave`, `random_castle` from `engine/events.py` — these names are missing, causing an import error on full game load. Flagged for a dedicated patch.
