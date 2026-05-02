---
type: design
version: ongoing
status: active
systems:
  - world
  - stealth
  - merchant
  - character
---

# Expansions — Planned Features

Features logged here are designed and deferred. Not in scope for current patches.

---

## 1. Explorable Dungeons — Location Minigames
Full room-by-room dungeon exploration with puzzle rooms, traps, secret areas, and boss encounters. Richer than the current entry gate system.

---

## 2. Pickpocket Minigame 
A street-level stealth activity in city screens. Risk/reward mechanic for Stealth builds. 

---

## 3. Assassination Minigame
Target-based contracts with planning, timing, and escape phases. Stealth + Speechcraft combined.

---

## 4. Quests
NPC-driven objectives with multi-step resolution, journal tracking, and reward tiers.

---

## 5. Library Hunt Minigame
A research puzzle inside city libraries. Dungeoneering-gated. Unlocks rare lore and unique items.

---

## 6. Stealth Entry Minigame *(deferred from Play Test 5 — Item 6)*
**Context:** When a player successfully passes the stealth check at a cave or castle entrance, instead of a simple "you enter undetected" confirmation, they enter a short minigame.

**Planned choices on successful stealth entry:**
- **Strike stealthily** — ambush the first enemy (current force_first behaviour, wrapped in a choice screen)
- **Steal from the room** — attempt to loot without engaging. Gated by a secondary Stealth roll. If the roll fails, combat triggers anyway but loot still drops. Clean success = loot only, no fight.

**Design notes:**
- The steal option draws from the location's loot_bias pool, same as post-combat loot
- Detection risk on steal should scale inversely with Stealth skill (low Stealth = high chance of triggering combat regardless)
- Should feel like a meaningful choice: engage or ghost. Both are valid, with different risk profiles.

---

## 7. Class Pick Screen at Game Start *(deferred from Play Test 5)*
**Context:** Currently players allocate skill points freely at character creation. A class screen would be a thematic pre-step.

**Design intent:**
- 4–6 archetypes: e.g. Mercenary, Road Scholar, Forest Runner, Hedge Mage, Cutpurse, Merchant Prince
- Each class provides: flavour text, a suggested skill spread, and a unique starting bonus
  - Example: Mercenary starts with Chain Hauberk; Hedge Mage starts with one extra Grimtotem
- Skill points remain fully allocatable after class selection — class is flavour + bonus, not a hard lock
- Class selection appears before name entry

**Implementation notes:**
- Integrates at the top of `character_creation()` in main.py
- Class stored on Player object for potential later use in event/dialogue checks
- Pairs well with a future NPC reaction system
