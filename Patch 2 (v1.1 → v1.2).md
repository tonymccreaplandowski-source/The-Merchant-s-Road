# Patch 2 (v1.1 → v1.2)

_Based on Play Test 2 feedback._

---

## Merchant System — Full Overhaul

- The single generic shop is gone. Each city now has **3 named merchants** per visit, each specialising in a trade: Blacksmith, Apothecary, Librarian, Survival Trader, Dungeoneering Co., or Leatherworker
- Merchants are assigned random names (Aldric, Berwen, Drusilla, etc.) and carry stock relevant to their type
- **Inventory is locked per visit** — the same 3 merchants and their same stock remain until you leave the city and come back, at which point new merchants are generated
- **Sell-back** — items you sell to a merchant go into their stock and can be bought back from them at standard buy price

## Negotiate Minigame

- Each merchant has a **Negotiate** button — a 3-round minigame using Merchantilism, Speechcraft, Dungeoneering, or Martial skill
- Each round you pick a tactic; both sides roll d20 + skill modifier vs merchant resistance
- Results: **3/3 wins = 18% discount**, 2/3 = 10% off, 1/3 = 5% off, 0/3 = 8% price premium
- Negotiation is one-shot per merchant per visit — prices are locked after the session

## Armor Type Skill Bonuses

- Armor now carries passive skill bonuses and penalties based on type:
  - **Padded Jacket** (cloth): +2 Magic
  - **Leather Vest** (leather): +3 Stealth, +1 Survival
  - **Chain Hauberk** (mail): +3 Martial, +2 Survival, −3 Stealth
  - **Scale Armour** (mail): +4 Martial, +2 Survival, −4 Stealth
  - **Plate Cuirass** (mail): +6 Martial, +2 Survival, −6 Stealth
- **No armour equipped** grants a passive +3 Magic (unarmoured mage bonus)
- These incentives naturally push Stealth builds toward leather, Magic builds toward cloth or nothing, and Martial builds toward mail

## Journal System

- Clearing a cave or castle now drops a **2-sentence lore entry** added to the player's Journal
- The **Journal** is accessible from the city menu and displays all collected lore
- Journal flavour text changes as it fills:
  - _0 entries:_ "These pages are empty and ready to be filled with your adventures."
  - _1–9:_ "You've been exploring the world. You realise not all is as you once thought."
  - _10–19:_ "Pages falling out, leather torn. This book is full of all that has been seen."
  - _20+:_ "Some call you sage, others call you wise. You know that you've seen the edges of the world."

## Exploration Balance

- **BASE_ENCOUNTER_CHANCE** raised from 0.28 → 0.35
- **EVENT_CHANCE** raised from 0.45 → 0.65 — significantly more locations, fewer lone mob encounters
- Each of the 6 explorable locations (3 caves, 3 castles) now has its own lore text

## Combat Fixes

- **Attack effectiveness is now hidden when choosing a move** — the strong/weak/okay tag only appears in the result message after the strike lands
- **D20 miss mechanic** — a general hit roll (d20 + attacker_combat // 5 vs defender_defense // 4 + 2) now applies to all attacks; high-defense enemies can cause genuine misses
- **Long Shot (bow) nerfed** — base power reduced 11 → 8; Martial scaling bonus halved (Martial/200 instead of Martial/100)

## New Supply Items

Ten new items available from Survival and Dungeoneering merchants:
Rope, Dried Rations (heal 15 HP), Torch Bundle, **Adventurer's Map** (increases location find chance for one road segment), Firewood, Tinderbox, Bandages (heal 20 HP), Grappling Hook, Lock Picks, Lantern

## City Rename

- **Peñasco → Greyspire** (the mountain stronghold, ironpeak)

## Music & Sound

- New melodic beep sequences (Windows) play on: city arrival, combat start, victory, death, location discovery, journal update, negotiate win/loss
- Melodies run in a background thread — non-blocking

## Typewriter Effect

- Location descriptions and dungeon entry text now type out character by character
- Combat messages and narrative moments use the same effect where appropriate

---

_Next: Play Test 3_
