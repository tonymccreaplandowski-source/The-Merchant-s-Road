---
type: patch-notes
version: v1.3→v1.4
status: archived
systems:
  - combat
  - character
  - merchant
---

# Patch 4 — v1.3 → v1.4
**Date:** 2026-04-19
**Focus:** Camping Overhaul · Bushcraft · Hunting Minigame

---

## Camping Overhaul

- **Removed** the "2 camps left" hard limit system entirely.
- Camping now costs **1× Firewood + 1× food item** per rest. No arbitrary cap — scarcity is economic.
- HP and Mana restored now **scale with food quality**:

| Food | HP | Mana |
|---|---|---|
| Unknown Berries | +10 (20% poison risk: −15 HP) | 0 |
| Dried Fruit / Small Game Meat | +20 | +8 |
| Blueberries | +20 | +5 |
| Wild Mushrooms | +15 | +10 |
| Herb Bundle | +25 | +20 |
| Dried Rations | +30 | +15 |
| Dried Meat (hunted) | +35 | +15 |
| Venison / Bear Meat | +40 | +18 |

- Road menu now shows which resources are **missing** (firewood / food) rather than a camp counter.
- Players who lack resources are nudged toward Bushcraft.

---

## Bushcraft (New Road Option)

A new **standalone road option** available at all times while travelling.

- **Foraging**: Governed by Survival skill.
  - Success chance: `35% + (Survival × 0.5%)` — ranges from 35% at Survival 0 to 85% at Survival 100.
  - **Failure**: Adds 1 day to elapsed time and extends journey by 1 road step. Message: *"Your time spent foraging was unsuccessful. It has since grown dark. Your journey extends a day..."*
  - **Quality of finds scales with Survival tier:**

| Survival | Tier | Notable finds |
|---|---|---|
| < 20 | Low | Unknown Berries, damp Firewood |
| 20–49 | Mid | Blueberries, Firewood, Wild Mushrooms |
| 50–79 | High | Herb Bundle, Nightshade (identified), Firewood |
| 80+ | Expert | Herb Bundle, Nightshade, premium forage |

- Low Survival: finds unidentified items, risks eating poison. High Survival: identifies everything, better yield mix.

- **Hunting**: Available as a sub-option if the player has a **bow** equipped or in inventory. Unlocks the Hunting Minigame.

---

## Hunting Minigame (New)

A CK3-inspired **escalating kill chance** system. Not a fixed outcome — you build your position then commit.

### Animal availability
Scales with `(Stealth + Survival) / 2`:

| Avg skill | Animals unlocked |
|---|---|
| 0 | Squirrel |
| 20 | Fox, Owl |
| 30 | Badger |
| 40 | Deer |
| 55 | Elk (5% death risk on miss) |
| 70 | Bear (15% death risk) |
| 80 | Dire Wolf (25% death risk) |
| 90 | Wyvern (45% death risk) |
| 100 | Dragon (85% death risk — near-certain death) |

### Starting kill chance
`10 + (Stealth + Survival) / 5`
Combined skills of 40 → ~18%. Combined 100 → ~30%. Combined 160 → ~42%.

### Build-up rounds (max 3, or until 85% kill chance)
- **Move silently** (Stealth): On success, `+5 + (Stealth ÷ 10)%` kill chance. Higher Stealth = bigger gain per successful roll.
- **Track and position** (Survival): On success, `+3 + (Survival ÷ 15)%` kill chance + reduces injury risk. Rewards survival investment beyond just the shot.
- **Take the shot** (Martial): Ends build-up immediately.
- **Let it go**: Exits with no reward or penalty.

At 85% kill chance the game forces the decision: *"This is as good a chance as you'll get."*

### The shot (Martial)
`shot_roll = d20 + Martial ÷ 4` vs `difficulty = 22 − (kill_chance ÷ 5)`.
Higher positioning = lower difficulty. At 85% kill chance, difficulty drops to ~5.

### On miss — injury & death
- Injury risk on miss: `max(10%, 40% − Survival × 0.3%)`. High Survival = low risk.
- Bigger animals escalate: Elk kicks for 20 HP, Bear mauls for 35 HP, Dire Wolf 40 HP, Wyvern 60 HP.
- **Death risk** on lethal animals: chance the animal retaliates fatally. Dragon at 85% death risk — a missed shot is near-certain death.

### Yield on kill
| Survival | Meat count | Pelt chance | Bone/rare item |
|---|---|---|---|
| Low | ×1 | ~20% | ~5% |
| Mid | ×1–2 | ~45% | varies |
| High | ×2–3 | ~65% | varies |
| Expert | ×3 | ~85% | higher chance |

Bone items: Bone Tusk, Bear Claw, Wolf Tooth. Mystical beasts drop: Mystical Fang, Dragon Hide.

---

## New Items (16 total)

**Hunt yields (meat):** Small Game Meat · Dried Meat · Venison · Bear Meat

**Hunt yields (pelts/trade):** Squirrel Pelt · Fox Pelt · Deer Pelt · Elk Pelt · Bear Pelt · Bone Tusk · Bear Claw · Mystical Fang

**Forage finds:** Unknown Berries · Blueberries · Wild Mushrooms · Nightshade

---

## New Item Effects

- `heal_35` — Dried Meat
- `heal_40` — Venison, Bear Meat
- `mushroom_wild` — Wild Mushrooms: +15 HP, +10 Mana
- `berries_unknown` — Unknown Berries: +10 HP with 20% poison risk (−15 HP)

---

## Version String
Updated to `Alpha - World v1.4 | Camping & Bushcraft update`

---

## Known Pre-existing Issues (not introduced this patch)
- `engine/world.py` imports `random_cave`, `random_castle` from `engine/events.py` — these names are missing, causing an import error on full game load. Flagged for next patch.
