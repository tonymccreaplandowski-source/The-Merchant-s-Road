# The Merchant's Road

A terminal-based RPG written in Python. No external dependencies. Runs anywhere Python 3.10+ is installed.

The game is built around an idea borrowed from *The Elder Scrolls IV: Oblivion* — that the **merchant economy** is one of the most interesting and underused systems in RPGs. Rather than treating buying and selling as a chore between dungeons, this game puts trade at the centre of the experience.

---

## Running the Game

```bash
cd game
python main.py
```

Python 3.10 or higher. No pip installs required.

---

## Concept

Three cities sit on a linear map. Prices differ by location based on local supply and demand. You carry goods across roads, fight whatever gets in your way, and build a character shaped entirely by how you spend your skill points.

Combat is turn-based in the style of Pokemon — readable, deliberate, move-choice driven. The merchant system (Phase 2, in progress) will add full negotiation: NPC mood, dialogue options, bluffing, and a Speechcraft-gated master merchant tier.

---

## Project Structure

```
game/
├── main.py              # Entry point — game loop, combat, city menus
├── data/
│   ├── cities.py        # City definitions, biome pricing, adjacency
│   ├── enemies.py       # Enemy templates, randomised stat spawning
│   ├── items.py         # Full item database (weapons, armour, potions, books, gems)
│   ├── spells.py        # Spell definitions and Magic skill unlock thresholds
│   └── weapons.py       # Move sets per weapon type, effectiveness matrices
├── engine/
│   ├── player.py        # Player dataclass — skills, equipment, mana, inventory
│   ├── combat.py        # Combat engine — damage, crits, initiative, spells, state
│   ├── world.py         # Travel engine — road steps, encounter rolls, camp limit
│   ├── loot.py          # Loot generation with rarity bias
│   ├── events.py        # Cave and castle road events
│   └── classes.py       # Character class detection and ASCII sprite renderer
└── ui/
    └── display.py       # All rendering — ANSI colour, bars, menus, screens
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

210 points distributed across 7 skills at character creation. Your dominant skill determines your class and ASCII character sprite.

| Skill | Effect |
|---|---|
| **Merchantilism** | Better buy/sell prices, negotiation outcomes |
| **Speechcraft** | Unlocks dialogue options, improves NPC reactions |
| **Martial** | Increases combat damage, hit chance, and crit rate |
| **Magic** | Unlocks spells; determines mana pool (Magic x 2) |
| **Stealth** | Improves flee chance, powers Snipe attacks |
| **Survival** | Reduces road encounter rate, boosts initiative roll |
| **Dungeoneering** | Improves cave/castle exploration, trap detection |

---

## Combat

Turn-based. Each turn: **Attack** (weapon moves) / **Cast** (spells) / **Items** (potions) / **Flee**.

Weapon types each have three moves with different effectiveness profiles against armour types (none / cloth / leather / mail):

| Type | Moves |
|---|---|
| Sword | Slash, Pierce, Parry |
| Dagger | Stab, Pierce, Feint |
| Axe | Hack, Cleave, Overhead |
| Mace | Bash, Smash, Stagger |
| Bow | Pot Shot, Snipe, Long Shot |
| Staff | Staff Strike, Sweep, Channel |
| Unarmed | Strike, Shove, Pummel |

Critical hits: 5% base + Martial/500, capped at 30%, deal 1.5x damage.

Initiative: both sides roll d20 + modifier. The loser attacks second on the first turn.

---

## Spells

| Spell | Magic Required | Mana Cost | Effect |
|---|---|---|---|
| Frost Bolt | 5 | 12 | Frost damage, slows enemy for 2 turns |
| Fireball | 10 | 15 | High fire damage, weak vs mail |
| Healing Word | 15 | 20 | Restores 25 HP |
| Shadow Step | 20 | 18 | Shadow damage, 50% chance enemy misses next attack |
| Lightning Arc | 30 | 22 | Lightning damage, fully armour-ignoring |

---

## Items

- **Weapons** — equippable, determines your combat move set
- **Armour** — equippable, adds flat defense points
- **Rings and Necklaces** — passive skill bonuses while equipped
- **Potions** — usable in and out of combat
- **Lore Books** — two-sentence flavour text, sellable
- **Trade Goods** — buy low, sell high between cities
- **Cursed Items** — warning shown on equip; negative effects on the player

Inventory cap: 12 items.

---

## Road Travel

Each road is 4 steps. Each forward step costs one day and may trigger a combat encounter, a cave or castle event, or nothing. Encounter rate is reduced by your Survival skill.

You can make camp up to twice per road segment, restoring 30 HP and 15 mana each time.

---

## Roadmap

- [ ] Phase 2 merchant system — full negotiation, NPC mood, Speechcraft dialogue tree
- [ ] Passive abilities per class
- [ ] Multi-room dungeons with x/y/z navigation
- [ ] Situational events — weather, exhaustion, biome encounters
- [ ] Carry weight system
- [ ] Archery guerrilla tactics — run-and-shoot, sharpshooter mode
- [ ] Survival utility — foraging, campfire crafting
- [ ] Money sink services — glyphs, information, performance buffs
- [ ] Puzzle encounters

---

## Design Notes

The core question this project is exploring: *can an economy system carry an RPG on its own?*

The merchant negotiation mechanic (Phase 2) is intended to feel like a genuine skill game — reading the NPC, timing your offers, knowing when to walk away — rather than a stat check you either pass or fail. Combat exists to create risk and cost on the road, not to be the main event. Everything feeds back into the economy.

---

*Alpha — v1.2*
