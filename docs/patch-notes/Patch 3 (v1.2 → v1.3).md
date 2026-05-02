---
type: patch-notes
version: v1.2→v1.3
status: archived
systems:
  - combat
  - merchant
  - items
---

# Patch 3 (v1.2 → v1.3)

_Based on Play Test 3 feedback._

---

## Bug Fixes

- **Journal crash resolved** — a stray identifier in `show_journal` caused the game to crash after reading the first lore entry. Fixed.
- **Books now readable** — books purchased from the Librarian previously sat inert in inventory. A new **Read a Book** option in the city menu lets the player read any book, typewriting the lore text to screen and adding it to the Journal. Already-read books are flagged accordingly.

---

## UX & Pacing

- **Press Enter gates added throughout** — after every significant piece of writing (lore entries, loot results, combat supply messages) the game now waits for the player to press Enter before transitioning. No more being rushed back to the road before you've finished reading.
- **Loot screen pace fixed** — each item found after clearing a location now pauses for Enter before the next appears. Lore text also waits for Enter after displaying.
- **"Out of combat supplies"** — attempting to use items in combat with an empty pouch now prints a clear message and returns to the combat menu, rather than silently continuing.
- **Enemy stat labels updated** — the enemy combat panel now reads **Martial / Defense / Stealth** to match player-facing skill names, replacing the old "Combat / Defense / Agility" labels.
- **Enemy count hidden** — the explore prompt no longer reveals how many enemies are inside a location or the loot quality. What lies within is unknown until you enter.

---

## Balance & Tuning

- **Starting skill points reduced: 210 → 180** — forces more deliberate, specialised character builds and raises the stakes on early decisions.
- **Lightning Arc mana cost increased: 22 → 32** — the spell was too efficient for its damage output. It remains the most powerful spell but now demands a real mana investment.
- **Road steps increased: 4 → 6** — travel between cities is longer, creating more encounters, more resource tension, and more meaningful decisions on the road.
- **Enemy count randomised** — location enemy counts are now resolved from a range at spawn time rather than being fixed. Caves range from 1–3 or 2–4 depending on the location; castles from 1–3 up to 2–5. The player never knows how many await them.

---

## Ambient Music

- **Dark fantasy ambient loop** — a slow, haunting A-minor melody now plays continuously in the background using the Windows beep system. No external dependencies required.
- The ambient track **cuts out when combat begins** and **resumes after victory** (following the victory fanfare) or after a successful escape. It does not resume on death.

---

## Negotiation — Skill-Boost System

The negotiate minigame now rewards relevant skills with a flat bonus added to the player's roll each round.

- **Merchantilism** — full power: +0.01 per skill point (+1.0 at skill 100). Always the strongest boost; incentivises the merchant RP path.
- **Speechcraft** — half power: +0.005 per skill point (+0.5 at skill 100). Charismatic characters always get a solid deal, just not as good as a true merchant.
- **All other skills** — quarter power: +0.001 per skill point each. Small but present — being broadly capable helps.
- **Matching leading skill** — if the player's highest skill matches the merchant's area of expertise (e.g., a Martial-focused player dealing with a Blacksmith), that skill is boosted to full Merchantilism rate (+0.01 per point). A master of their craft gets respect from another master of theirs.
- **Stacking** — all applicable boosts stack. A merchant-mage dealing with an Apothecary (whose leading skill is Magic), with high Merchantilism and Speechcraft, gets the strongest possible deal. Difficult to fully achieve with only 180 starting points.
- The negotiate screen now displays the merchant's area of expertise and flags when a leading-skill match is active.

---

## Road Access

- **Gear and Journal now accessible on the road** — the road travel menu includes Gear and Journal options. Players can swap equipment between encounters and read lore entries without needing to reach a city first.

---

## World

- **"Las Cumbres" removed** — the Spanish-style name was replaced with Greyspire in a previous patch; all remaining references in comments and the book *Geology of Las Cumbres* (now *Geology of Greyspire*) have been updated. No Spanish-dialect words remain in visible game text.

---

_Next: Play Test 4_
