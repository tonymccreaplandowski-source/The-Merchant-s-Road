# The Merchant's Road

A terminal-based RPG written in Python. Runs anywhere Python 3.10+ is installed.

The game is built around an idea borrowed from *The Elder Scrolls IV: Oblivion* — that the **merchant economy** is one of the most interesting and underused systems in RPGs. Rather than treating buying and selling as a chore between dungeons, this game puts trade at the centre of the experience.

---

## Running the Game

```bash
cd game
python main.py
```

Python 3.10 or higher. No pip installs required for the main game.
`numpy` and `matplotlib` are required only for the balance simulation tool (`troll_simulation.py`).

---

## Current Version

**Alpha v2.8** — Explorable Dungeons

---

## Concept

Three cities sit on a linear map. Prices differ by location based on local supply and demand. You carry goods across roads, fight what gets in your way, and build a character shaped entirely by how you spend your skill points.

Combat is turn-based — readable, deliberate, move-choice driven. The merchant system is fully built: negotiation runs as a real mini-game with NPC mood, timed offers, and Speechcraft-gated outcomes. Stealth and crime are in via a pickpocket and mugging system. Dungeons are now branching, room-by-room environments with puzzles, traps, and named bosses.

---

## Project Structure

```
game/
├── main.py                  # Entry point and game loop
├── troll_simulation.py      # Standalone combat balance tool
├── data/
│   ├── cities.py            # City definitions, biome pricing, adjacency
│   ├── classes.py           # 21 character class definitions
│   ├── enemies.py           # Enemy templates, randomised stat spawning
│   ├── items.py             # Full item database + 6 unique boss drops
│   ├── spells.py            # Spell definitions and Magic skill thresholds
│   └── weapons.py           # Move sets per weapon type, effectiveness matrices
├── engine/
│   ├── player.py            # Player dataclass — skills, equipment, mana, inventory
│   ├── combat.py            # Combat engine — damage, crits, initiative, spells, state
│   ├── dungeon.py           # Dungeon graph engine — room generation, boss spawning
│   ├── events.py            # Road events — cave and castle definitions with bosses
│   ├── items_use.py         # Item use logic (potions, bandages, tools)
│   ├── loot.py              # Loot generation with rarity bias
│   ├── merchant.py          # Merchant buy/sell and price calculation
│   ├── negotiate.py         # Negotiation mini-game engine
│   ├── pickpocket.py        # Pickpocket and mugging system
│   └── world.py             # Travel engine — road steps, encounter rolls, camping
└── ui/
    ├── city.py              # City menus and services
    ├── combat_loop.py       # Combat UI and turn flow
    ├── creation.py          # Character creation and class selection
    ├── display.py           # All rendering — ANSI colour, bars, menus, screens
    ├── dungeon_puzzles.py   # Four puzzle mini-games (riddle, reveal, maze, sequence)
    ├── equipment.py         # Equipment and inventory screens
    └── road.py              # Road travel, dungeon exploration, event handling
```

---

## The World

| City | Biome | Character |
|---|---|---|
| **Dar-Nakhil** | Desert | Silk and spice flow freely. Iron is scarce and expensive. |
| **Rabenmark** | Forest | Furs, herbs, and leather are in surplus. Desert goods fetch a premium. |
| **Penasco** | Mountain | Iron and steel are cheap. Cloth and food are hard to come by. |

Arbitrage is the core loop: buy what is abundant somewhere, sell it where it is scarce.

---

## Character System

100 points distributed across 7 skills. Your two dominant skills are chosen at class selection (locked at 30 each); remaining points are spent freely across the other five.

| Skill | Effect |
|---|---|
| **Merchantilism** | Better buy/sell prices, negotiation outcomes |
| **Speechcraft** | Unlocks dialogue options, improves NPC reactions; gates master-merchant negotiation tier |
| **Martial** | Increases combat damage, hit chance, and crit rate |
| **Magic** | Unlocks spells; determines mana pool size |
| **Stealth** | Improves flee chance, powers Snipe attacks, improves pickpocket success |
| **Survival** | Reduces road encounter rate, boosts initiative, improves dungeon retreat |
| **Dungeoneering** | Improves dungeon navigation, trap detection, puzzle clue quality, boss warnings |

### Character Classes (21 total)

Each class locks two dominant skills at 30. Class name and sprite are determined by your dominant pair.

Mage · Warrior · Knight · Adventurer · Battlemage · Bard · Assassin · Ranger · Smuggler · Scholar · Merchant · Pathfinder · Alchemist · Infiltrator · Mercenary · Hexblade · Delver · Shaman · Wayfarer · Chronicler · Prospector

---

## Combat

Turn-based. Each turn: **Attack** (weapon moves) / **Cast** (spells) / **Items** (potions) / **Flee**.

**Weapon types — move sets and armour effectiveness:**

| Type | Moves | Strong vs |
|---|---|---|
| Sword | Slash, Pierce, Parry | None / Cloth (Slash), Leather (Pierce) |
| Dagger | Stab, Pierce, Feint | None / Leather |
| Axe | Hack, Cleave, Overhead | None / Cloth — Overhead is high-risk/high-reward (25% miss, 17 power) |
| Mace | Bash, Smash, Stagger | None / Mail — best against armoured enemies |
| Bow | Pot Shot, Snipe, Long Shot | None / Cloth — Snipe scales with Stealth |
| Staff | Staff Strike, Sweep, Channel | Neutral — Channel reduces next spell cost by 5 mana |
| Unarmed | Strike, Shove, Pummel | None — Shove staggers enemy for 2 turns |

Critical hits: 5% base + Martial/500, capped at 30%, deal 1.5× damage.

Initiative: both sides roll d20 + modifier. Loser attacks second on round 1.

---

## Spells

| Spell | Magic Required | Mana Cost | Effect |
|---|---|---|---|
| Frost Bolt | 5 | 12 | Frost damage, slows enemy for 2 turns |
| Fireball | 10 | 15 | High fire damage |
| Healing Word | 15 | 20 | Restores 25 HP |
| Shadow Step | 20 | 18 | Shadow damage, 50% chance enemy misses next attack |
| Lightning Arc | 30 | 22 | Lightning damage, armour-ignoring |
| Drain Life | 35 | 25 | Damage + self-heal |
| Blizzard | 50 | 40 | High frost damage, extended slow |

---

## Merchant Negotiation

Activated when selling goods to city merchants. Runs as a timed mini-game:

- NPC starts in a mood state (suspicious / neutral / receptive) based on your Merchantilism
- Each round: make an offer, read the NPC's response, choose to push or concede
- Speechcraft unlocks additional dialogue options and a master-tier negotiation track
- Offers that are too aggressive sour the NPC's mood; too passive leaves gold on the table

---

## Road Travel

Each road is 4 steps. Each step may trigger a combat encounter, a dungeon event, or nothing. Encounter rate is reduced by Survival.

You can camp up to twice per segment, restoring 30 HP and 15 mana each time.

Status effects on the road: poison, disease, and berry sickness (temporary skill debuff). Hunger depletes per step and penalises Martial and Survival below certain thresholds.

---

## Dungeons

Triggered by cave and castle road events. Each run generates a 5–8 room branching dungeon graph.

**Room types:**

| Type | Description |
|---|---|
| Entry | Atmospheric — no encounter |
| Combat | Biome enemy; 30% loot roll on clear |
| Trap | Dungeoneering + Survival check; spike / gas / floor / tripwire variants |
| Puzzle | One of four mini-game types; optional or boss-gating |
| Secret | Dungeoneering roll only; pure upside |
| Dead end | Atmospheric lore; no encounter |
| Boss | Named, buffed final enemy; unique item drop on kill |

**Puzzle types:** Riddle (22 scripted), Reveal (progressive visual), Maze (7×7–9×9 ASCII grid, fog of war), Sequence (symbol lock).

**Dungeoneering items:** Grappling Hook, Rope, Lock Picks, Torch Bundle, Lantern, Adventurer's Map — all have specific dungeon mechanics.

### Named Bosses and Unique Drops

| Boss | Location | Unique Drop |
|---|---|---|
| The Den Warden | The Hollow Den | Warden's Hide Wraps (+5 Stealth, +3 Survival) |
| The Grotto Abomination | The Dripping Grotto | Tideborn Pendant (+6 Magic, +4 Dungeoneering) |
| The Cache Master | The Smuggler's Cache | Shadow Fingers (+7 Stealth, +3 Merchantilism) |
| The Castellan | The Broken Keep | Castellan's Vow (+5 Martial, +3 Survival) |
| The Forsaken Captain | The Forsaken Garrison | Captain's Verdict (+5 Martial, +4 Speechcraft) |
| The Vault Sentinel | The Merchant Lord's Folly | Folly Signet (+6 Merchantilism, +4 Speechcraft) |

---

## Stealth & Crime

Each city tracks a **heat** value (0–100) and a **wanted** state.

- **Pickpocket** — Stealth-gated; heat rises on success; failure triggers combat with city guard
- **Mug** — Forces combat; high heat consequence
- Heat decays over time. Wanted status bars city services until cleared.

---

## Items

- **Weapons** — equippable, determines combat move set
- **Armour** — equippable, flat defense + armour type for incoming damage calculation
- **Rings and Necklaces** — passive skill bonuses (and penalties on cursed items)
- **Potions** — usable in and out of combat
- **Lore Books and Grimtotems** — flavour text and learnable spells
- **Trade Goods** — buy low, sell high
- **Dungeoneering Tools** — mechanical use in dungeons
- **Cursed Items** — warning shown on equip; permanent max HP reduction while equipped

Inventory cap: 12 items.

---

## Roadmap

- [ ] Passive class abilities
- [ ] Carry weight system
- [ ] Archery guerrilla mode — run-and-shoot, sharpshooter
- [ ] Survival utility — foraging, campfire crafting
- [ ] Money sink services — glyphs, information, performance buffs
- [ ] Weather and exhaustion road events
- [ ] Multi-city expansion (4th and 5th city, longer routes)

---

## Design Notes

The core question: *can a merchant economy carry an RPG on its own?*

Combat exists to create real cost and risk on the road, not to be the main event. Everything feeds back into the economy — dungeon loot has sell value, road encounters drain supplies, negotiation skill determines how much gold you walk away with. The merchant loop is the spine; everything else hangs off it.

---

*Alpha — v2.8*
