---
type: handoff
version: v2.5→v2.6
status: archived
systems:
  - negotiate
  - merchant
---

# Negotiation Mini-Game Rebuild — Handoff Spec
**Target version:** v2.5 → v2.6  
**Files touched:** `engine/negotiate.py` (new), `engine/merchant.py`, `ui/city.py`

---

## 1. What This Replaces

The existing `negotiate_session()` in `ui/city.py` (dice-roll tactic system, flat discount multiplier) is scrapped entirely. The new system lives in `engine/negotiate.py` and is called from `ui/city.py`. The old `_negotiate_skill_boost()` helper is also removed.

---

## 2. Merchant Data Changes

### Replace `leading_skill` with `dominant_skill`
Every merchant dict gets a randomly assigned `dominant_skill` drawn from the full `SKILLS` list (7 values). This replaces the type-linked `leading_skill` field everywhere it appears in `merchant.py` and `city.py`.

```python
import random
from engine.player import SKILLS

merchant["dominant_skill"] = random.choice(SKILLS)
```

### Add `motivation`
Each merchant is assigned a hidden motivation integer at generation time.

```python
MOTIVATIONS = [
    "status_approval",    # 1
    "love_acceptance",    # 2
    "control_authority",  # 3
    "safety_certainty",   # 4
]
merchant["motivation"] = random.randint(0, 3)  # index into MOTIVATIONS
```

### Pricing: replace discount float with hard GP delta
Remove the `discount: float` field. Replace with:
```python
merchant["gp_delta"] = 0        # int; positive = player advantage, negative = penalty
merchant["negotiated"] = False
merchant["ejected"] = False      # True = player is locked out of this merchant
```

Update `buy_price()` and `sell_price()` in `merchant.py`:
```python
def buy_price(item, city, gp_delta: int = 0) -> int:
    base = max(1, round(item.base_value * city.price_modifier(item.name) * 1.30))
    return max(1, base - gp_delta)   # positive delta = cheaper to buy

def sell_price(item, city, gp_delta: int = 0) -> int:
    base = max(1, round(item.base_value * city.price_modifier(item.name) * 0.65))
    return max(1, base + gp_delta)   # positive delta = more earned on sell
```

For insult penalty: `gp_delta` is negative (player loses value on both ends). For ejection: merchant is inaccessible.

---

## 3. Appeal System

### The four appeals (display text per motivation)
Present all four every round. The player does not know the merchant's hidden motivation.

```python
APPEALS = [
    # (motivation_key, display_label, flavor_text)
    ("status_approval",   "Appeal to their reputation",
     "\"After this, everyone in the city will know your name...\""),
    ("love_acceptance",   "Appeal to common ground",
     "\"We're both just trying to get by out here. Help me and I'll remember it...\""),
    ("control_authority", "Defer to their judgment",
     "\"You know this trade better than anyone. I trust your call on this...\""),
    ("safety_certainty",  "Offer certainty",
     "\"No risk to you. I'm not asking for a favour — just a fair arrangement...\""),
]
```

> **Content note:** These flavor lines are placeholders. Expand with 2–3 variants per motivation for variety.

---

## 4. Session State

```python
session = {
    "close_pct":   35.0,   # starts at 35%
    "insult_pct":  65.0,   # starts at 65%
    "round":       1,      # 1–3
    "rounds_won":  0,
    "log":         [],     # list of flavor strings for display
}
```

**Caps (enforced after every delta):**
- `close_pct` max: 85.0
- `insult_pct` min: 15.0

---

## 5. Delta Formula

Run once per appeal attempt (correct or wrong). Determine the player's **dominant skill** first:

```python
p_dominant = max(player.skills, key=lambda s: player.skills[s])
```

### Correct appeal — close% gain
```python
base_gain = 8.0
if p_dominant == "Merchantilism":
    bonus = player.skill("Merchantilism") * 0.10
elif p_dominant == "Speechcraft":
    bonus = player.skill("Speechcraft") * 0.05
elif p_dominant == merchant["dominant_skill"]:
    bonus = player.skill(p_dominant) * 0.05
else:
    bonus = 0.0

close_gain = base_gain + bonus
session["close_pct"] = min(85.0, session["close_pct"] + close_gain)
session["rounds_won"] += 1
```

### Wrong appeal — insult% gain
```python
base_penalty = 12.0
if p_dominant == "Merchantilism":
    reduction = player.skill("Merchantilism") * 0.08
elif p_dominant == "Speechcraft":
    reduction = player.skill("Speechcraft") * 0.04
elif p_dominant == merchant["dominant_skill"]:
    reduction = player.skill(p_dominant) * 0.04
else:
    reduction = 0.0

insult_gain = max(3.0, base_penalty - reduction)   # floor: wrong is always wrong
session["insult_pct"] = max(15.0, session["insult_pct"] - insult_gain)
# Note: insult_pct decreases toward 15% floor as player improves position;
# wrong appeals on a fresh session push it upward (worsen).
# Correct: insult_pct should INCREASE on wrong, DECREASE on correct.
# See correction note below.
```

> **Correction note:** `insult_pct` represents the *chance of insult*. A correct appeal should reduce it; a wrong appeal should increase it. Restate as:
> - Correct appeal: `insult_pct -= insult_gain` (capped at 15.0 floor)
> - Wrong appeal: `insult_pct += insult_gain` (no explicit ceiling; outcome matrix handles it)

---

## 6. Speechcraft Feedback

This is a **separate, independent check** from the delta formula. It runs after every appeal resolution.

```python
speechcraft_val = player.skill("Speechcraft")

if speechcraft_val >= 70:
    tier = "certain"
elif speechcraft_val >= 35:
    tier = "tepid"
else:
    tier = "ambiguous"
```

**Feedback flavor by tier and outcome:**

| Tier | Correct appeal | Wrong appeal |
|---|---|---|
| certain | *"Something in their posture opens. You're getting through."* | *"They stiffen. That was the wrong note."* |
| tepid | *"The merchant shifts slightly. Hard to tell."* | *"A flicker crosses their face. Uncertain."* |
| ambiguous | *"Their expression gives nothing away."* | *"Their expression gives nothing away."* |

> **Cheese note (intentional):** At `certain` tier, a player who reads the feedback correctly after round 1 can confidently repeat the winning appeal in rounds 2 and 3. This is a deliberate reward for high Speechcraft investment.

> **Balancing flag:** Speechcraft tier thresholds (35 / 70) are subject to balancing review.

---

## 7. "Go for the Close"

Available at the start of any round as an explicit menu option. At round 3 it is **forced** — appeals are no longer available.

**Round 3 forced-close message:**
> *"Tensions have run as high as they can. There's nothing left to say — only to see how it lands."*

**Display before close resolution:**
Show current percentages clearly so the player can make an informed decision:
```
  Close chance:   [XX]%
  Insult chance:  [XX]%
```

---

## 8. Outcome Resolution

### Step 1 — Agreement roll
```python
import random
agreement = random.randint(1, 100) <= session["close_pct"]
```

### Step 2 — Insult level roll
```python
insult_roll = random.randint(1, 100)
if insult_roll <= 29:
    insult_level = "low"
elif insult_roll <= 59:
    insult_level = "medium"
else:
    insult_level = "high"
```

> **Balancing flag:** Insult tier thresholds (29 / 59) are subject to balancing review.

### Step 3 — Outcome matrix

| Agreement | Insult level | Result |
|---|---|---|
| True | low | Good deal, low GP penalty |
| True | medium | Good deal, medium GP penalty |
| True | high | Deal stands, heavy pricing premium |
| False | low | No deal, minor inconvenience |
| False | medium | No deal, moderate penalty |
| False | high | **Ejected** — merchant locked for this city visit |

Ejection only on `agreement=False AND insult_level="high"`.  
`agreement=True AND insult_level="high"` = deal stands but `gp_delta` is heavily negative (punishing buy/sell spread).

---

## 9. GP Vector Payout

The payout is a hard GP integer applied as `merchant["gp_delta"]`.

### Base vector
```python
gp_vector = list(range(1, 11))   # [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
```

### Choke calculation
Determine choke % from player's dominant skill (same dominance check as delta formula):

```python
if p_dominant == "Merchantilism":
    choke_rate = 0.005   # 0.5% per skill point
else:
    choke_rate = 0.0025  # 0.25% per skill point (Speechcraft, matching dominant, or none)

choke_pct = player.skill(p_dominant) * choke_rate
choke_n   = round(choke_pct * len(gp_vector))   # standard rounding: .5 rounds up
choke_n   = max(0, min(choke_n, len(gp_vector) - 1))  # never empty the vector
```

### Direction of choke
- **Agreement outcome:** choke from the **low end** (raises the floor — player can't roll a bad deal)
  ```python
  gp_vector = gp_vector[choke_n:]
  ```
- **Insult/penalty outcome:** choke from the **high end** (lowers the ceiling — caps the worst punishment)
  ```python
  gp_vector = gp_vector[:len(gp_vector) - choke_n] if choke_n > 0 else gp_vector
  ```

### Final GP delta
```python
gp_value = random.choice(gp_vector)
```

Apply sign based on outcome:
- Agreement (any insult level): `merchant["gp_delta"] = +gp_value`
- No-agreement + low/medium insult: `merchant["gp_delta"] = -gp_value`
- Ejection: `merchant["ejected"] = True`, `merchant["gp_delta"] = 0` (moot)
- Agreement + high insult: `merchant["gp_delta"] = -gp_value` (deal exists but is punishing)

---

## 10. UI Integration (`ui/city.py`)

Replace the `negotiate_session()` call with a call to `engine/negotiate.py`:

```python
from engine.negotiate import negotiate_session
```

`merchant_screen()` reads `merchant["gp_delta"]` and `merchant["ejected"]` instead of `merchant["discount"]`.

Update the market listing to show ejected merchants as inaccessible (same display as `available=False`).

Update `disc_str` display logic to reflect hard GP delta:
- Positive delta: `+Xgp advantage on all trades`
- Negative delta: `-Xgp penalty on all trades`
- Ejected: `[Thrown out — not welcome here]`

---

## 11. File Summary

| File | Action |
|---|---|
| `engine/negotiate.py` | **Create.** All negotiation logic: session state, delta formula, feedback, close resolution, outcome matrix, vector payout. |
| `engine/merchant.py` | **Modify.** Replace `leading_skill` → `dominant_skill` (random). Add `motivation`, `gp_delta`, `ejected` fields. Refactor `buy_price()` / `sell_price()` to use `gp_delta: int`. |
| `ui/city.py` | **Modify.** Replace `negotiate_session()` body with import + call. Update `merchant_screen()` display logic for new fields. Update ejected merchant display in `visit_market()`. Remove `_negotiate_skill_boost()`. |

---

## 12. Balancing Flags (Do Not Hard-Code as Final)

The following values are confirmed for implementation but flagged for post-playtest tuning:

- Base close delta per correct appeal: `8.0`
- Base insult delta per wrong appeal: `12.0`
- Merchantilism close rate: `0.10` / insult reduction: `0.08`
- Speechcraft / matching dominant close rate: `0.05` / insult reduction: `0.04`
- Speechcraft feedback tiers: `< 35` ambiguous / `35–69` tepid / `≥ 70` certain
- Insult tier thresholds: `≤ 29` low / `30–59` medium / `≥ 60` high
- GP vector size: `1–10`
- Choke rates: Merchantilism `0.5%/pt`, others `0.25%/pt`

---

*Prepared for Claude Code handoff — Negotiate Rebuild v2.6*
