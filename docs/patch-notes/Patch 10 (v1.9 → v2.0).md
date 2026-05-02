---
type: patch-notes
version: v1.9→v2.0
status: archived
systems:
  - ui
  - combat
  - merchant
  - world
---

# Patch 10 — v1.9 → v2.0
**Date:** 2026-04-19
**Focus:** Bag Consolidation · Supply Guarantee · Inn Flavour · Spelling Fix

---

## Bag Menu (Task 7)

Gear and Journal are now consolidated into a single **Bag** menu, accessible from both the road and the city with the same interface.

### Bag contents
- **Gear** — equipped items, weapon/armour/accessory management, grimtotems
- **Journal** — lore entries and hermit writings

### Menu changes
**City loop** (before → after):
- Equipment, Journal, Read a Book (3 separate entries) → **Bag** (1 entry)
- Read a Book remains as a separate city option
- Base option count reduced from 7 to 6

**Road loop** (before → after):
- Gear, Journal (2 separate entries) → **Bag** (1 entry)
- Road options reduced from 6 to 5

---

## General Supply Merchant Guarantee (Task 9)

Previously, all 3 city merchants were randomly selected — it was possible to arrive in a city with no food, firewood, or basic road supplies available.

**Fix:** Merchant slot 1 is now always a **Survival Trader**, guaranteeing basic supplies (rations, firewood, rope, etc.) on every city visit. The other two slots remain fully random.

---

## Inn Flavour Messages (Task 10)

Resting at an inn now shows a short piece of atmospheric flavour text specific to each city, drawn at random from a pool of 3 per city.

### Dar-Nakhil (desert)
- "The inn smells of sand and spice. A caravan merchant snores in the corner."
- "The innkeeper pours something bitter and warm. You don't ask what it is."
- "Through the thin walls, you hear the desert wind. It doesn't stop all night."

### Rabenmark (forest)
- "The fire crackles with forest wood. A hunter's hound sleeps by the hearth."
- "Rain taps quietly at the roof. Somewhere outside, an owl calls once and goes silent."
- "The bed is rough straw and old wool. You sleep like you haven't in weeks."

### Greyspire (mountain)
- "The walls are thick stone. You feel safe here, or at least buried."
- "Miners' voices carry from the floor below. Dice on a table, coin on the bar."
- "The cold seeps in despite the fire. You pull the blanket close and don't argue with it."

The inn screen now clears and shows the flavour line above the rest confirmation, giving it room to breathe.

---

## Goblin Ear Spelling Fix (Task 11)

Confirmed already correct in `data/items.py` — description reads *"small sum"* as intended. No change required.

---

## Version String
Updated to `Alpha - World v2.0 | Quality of Life Pass`

---

## Known Issues (Carried Forward)
- `engine/world.py` imports `random_cave`, `random_castle` from `engine/events.py` — these names are missing, causing an import error on full game load. Flagged for a dedicated patch.
