---
type: patch-notes
version: v1.5→v1.6
status: archived
systems:
  - world
  - ui
  - stealth
  - combat
---

# Patch 6 — v1.5 → v1.6
**Date:** 2026-04-19
**Focus:** Wilderness Events — Disease · Stranger Encounters · Weather · Snake Bites

---

## Overview

Four new random events can now fire on uneventful road steps — steps where no combat encounter or special location (cave/castle) triggers. These events add atmosphere, consequence, and a reason to invest in Survival and Speechcraft outside of combat.

---

## Trigger System

- **Per-step roll** on every "Press on" action.
- Base chance: **18% per step**.
- Reduction: `Survival × 0.12%` per skill point — at Survival 100, chance bottoms out at **6%**.
- Events only fire on uneventful steps (no combat, no cave/castle on that step).
- One of four event types is chosen at random when the roll succeeds.

---

## Event Types

### Snake Bite
A snake strikes from the undergrowth.

**Skill check:** `d20 + Survival ÷ 5` vs difficulty **13**

| Outcome | Effect |
|---|---|
| Success (spotted) | Narrow escape — no damage |
| Fail | 15–25 HP damage |
| Fail + 35% chance | Poisoned — **5 HP per road step for 2 steps** |

Poison is cured by camping with a **Herb Bundle**.

---

### Ill Wind (Disease)
A sickness carried on the air settles in the player's chest.

**Skill check:** `d20 + Survival ÷ 5` vs difficulty **12**

| Outcome | Effect |
|---|---|
| Success (early recognition) | −5 HP, disease avoided |
| Fail | −20 HP + disease active |

While **diseased**, the player loses **5 HP per road step** until they reach a town (auto-clears on arrival) or camp with a **Herb Bundle**.

---

### Weather
A sudden storm, thick fog, or sleet forces the player off course.

**Skill check:** `d20 + Survival ÷ 5` vs difficulty **11**

| Outcome | Effect |
|---|---|
| Success (read the signs) | +1 road step added |
| Fail | +2 road steps, −10 HP (exposure) |

Storm flavour is randomised from three variants each time.

---

### Stranger Encounter
A figure appears on the road. Three archetypes chosen at random:

**Lost Traveller**
- Speechcraft check vs difficulty **8**
- Success: +5–15 gold (grateful for company)
- Fail: they walk on without a word

**The Hermit**
- Speechcraft check vs difficulty **10**
- Success: receives an **uncommon item** + a hand-written **journal entry** (lore from the hermit)
- Fail: they disappear without a word
- Journal lore pool: 10 unique hand-written entries. Each entry is used at most once per save.

**Shady Figure**
- **Survival pre-check** vs difficulty **10** — high Survival players sense trouble and bypass the encounter entirely
- If pre-check fails → Speechcraft check vs difficulty **13**
  - Success: hold their eye, they back down
  - Fail: lose **10–25 gold**

---

## Hermit Lore (10 entries)

Hand-written cryptic lines added to the player journal on successful hermit encounters:

1. "The road south bends toward Caldervast. Don't linger at the crossroads after dark — something there listens."
2. "I've walked these woods for forty years. The silence has changed. It used to mean peace."
3. "There's a merchant in Ashenvale who smiles too wide. Count your fingers after you shake his hand."
4. "The old castle beyond the ridge — men used to dare each other to spend the night. They stopped doing that."
5. "Ravens don't fly at night. If you see one after dusk, turn back."
6. "A boy passed through here three days ago. Running east. He didn't say from what."
7. "The river downstream runs clear but tastes of iron. Has done for a season now."
8. "Some roads weren't built for trade. They were built to keep something in."
9. "I found a coin near the standing stones last spring. Old face on it. No king I've ever known."
10. "The stars have been wrong lately. Not wrong enough for most to notice. But wrong."

---

## Status Effects (New Player Fields)

Two new fields added to the `Player` dataclass:

| Field | Type | Purpose |
|---|---|---|
| `road_poison` | `int` | Steps of poison remaining (5 HP drain each) |
| `road_diseased` | `bool` | Disease active — 5 HP drain per step |

### Clearing conditions
- **Poison and disease**: cleared automatically on **town arrival** or **turning back**
- **Herb Bundle at camp**: clears both poison and disease with a message
- Both drain per step **before** encounter checks — a poisoned player who also fights takes damage from both

---

## Skill Influence Summary

| Skill | Effect |
|---|---|
| Survival (high) | Lower wilderness event trigger chance, better outcomes on snake/disease/weather checks, detect shady figures before they act |
| Speechcraft (high) | Better stranger outcomes — more gold from travellers, hermit items, avoid robbery |

---

## Version String
Updated to `Alpha - World v1.6 | Wilderness Events`

---

## Known Issues (Carried Forward)
- `engine/world.py` imports `random_cave`, `random_castle` from `engine/events.py` — these names are missing, causing an import error on full game load. Flagged for a dedicated patch.
