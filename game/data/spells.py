"""
Spell definitions for the mana system.

Each spell requires a minimum Magic skill to unlock.
Mana pool = player.skill("Magic") * 2
Restores fully on rest.

Spell special effects:
  heal   — restores HP instead of dealing damage
  slow   — reduces enemy agility by 15 for 2 turns
  evade  — 50% chance enemy misses next counter
"""

SPELLS = {
    "Frost Bolt": {
        "cost":          12,
        "power":         13,
        "description":   "A bolt of ice that bites and slows the target.",
        "effectiveness": {"none": 1.3, "cloth": 1.0, "leather": 1.0, "mail": 1.3},
        "special":       "slow",
        "require_magic": 5,
        "damage_type":   "frost",
    },
    "Fireball": {
        "cost":          15,
        "power":         18,
        "description":   "Concentrated flame hurled at your foe.",
        "effectiveness": {"none": 1.5, "cloth": 1.5, "leather": 1.2, "mail": 0.7},
        "special":       None,
        "require_magic": 10,
        "damage_type":   "fire",
    },
    "Healing Word": {
        "cost":          20,
        "power":         0,
        "description":   "A whispered word that knits flesh together. Restores 25 HP.",
        "effectiveness": {},
        "special":       "heal",
        "heal_amount":   25,
        "require_magic": 15,
        "damage_type":   "heal",
    },
    "Shadow Step": {
        "cost":          18,
        "power":         16,
        "description":   "You vanish briefly and strike from an unexpected angle.",
        "effectiveness": {"none": 1.8, "cloth": 1.5, "leather": 1.3, "mail": 1.2},
        "special":       "evade",
        "require_magic": 20,
        "damage_type":   "shadow",
    },
    "Lightning Arc": {
        "cost":          22,
        "power":         20,
        "description":   "Raw lightning. Strips through armour like it is not there.",
        "effectiveness": {"none": 1.5, "cloth": 1.5, "leather": 1.5, "mail": 1.5},
        "special":       None,
        "require_magic": 30,
        "damage_type":   "lightning",
    },
}


def get_available_spells(magic_skill: int) -> dict:
    """Return spells the player can cast given their current Magic skill."""
    return {
        name: spell
        for name, spell in SPELLS.items()
        if magic_skill >= spell["require_magic"]
    }
