"""
Weapon type definitions and move sets.

Each weapon type unlocks exactly 3 combat moves.
Moves have their own power, effectiveness matrix, and optional special effect.

Special effects:
  defensive    — reduces next incoming hit by 40%
  evade        — 50% chance enemy misses their counter-attack
  stealth_boost— damage multiplied by (1 + Stealth/100)
  martial_boost— damage multiplied by (1 + Martial/100)
  miss_chance  — this move has a % chance to miss entirely (high risk/reward)
  stagger      — reduces enemy combat_skill by 10 for 2 turns
  slow         — reduces enemy agility by 15 for 2 turns (used by spells too)
"""

MOVES = {
    # ── UNARMED (default, no weapon equipped) ───────────────────────────
    "Strike": {
        "power": 6,
        "description": "A basic unarmed strike. Better than nothing.",
        "effectiveness": {"none": 1.2, "cloth": 1.0, "leather": 0.8, "mail": 0.6},
        "special": None,
    },
    "Shove": {
        "power": 4,
        "description": "A heavy push. Low damage, disrupts enemy rhythm.",
        "effectiveness": {"none": 1.0, "cloth": 1.0, "leather": 1.0, "mail": 1.0},
        "special": "stagger",
    },
    "Pummel": {
        "power": 8,
        "description": "Rapid unarmed strikes. Unreliable but relentless.",
        "effectiveness": {"none": 1.2, "cloth": 1.0, "leather": 0.7, "mail": 0.5},
        "special": None,
    },

    # ── SWORD ────────────────────────────────────────────────────────────
    "Slash": {
        "power": 9,
        "description": "A wide horizontal cut.",
        "effectiveness": {"none": 1.5, "cloth": 1.5, "leather": 1.0, "mail": 0.6},
        "special": None,
    },
    "Pierce": {
        "power": 8,
        "description": "A controlled thrust aimed at gaps in armour.",
        "effectiveness": {"none": 1.5, "cloth": 0.9, "leather": 1.5, "mail": 1.0},
        "special": None,
    },
    "Parry": {
        "power": 4,
        "description": "A defensive counter-strike. Weakens their next blow.",
        "effectiveness": {"none": 1.0, "cloth": 1.0, "leather": 1.0, "mail": 1.0},
        "special": "defensive",
    },

    # ── DAGGER ───────────────────────────────────────────────────────────
    "Stab": {
        "power": 11,
        "description": "A precise upward stab. Punishes light armour.",
        "effectiveness": {"none": 1.5, "cloth": 1.2, "leather": 1.5, "mail": 0.7},
        "special": None,
    },
    "Feint": {
        "power": 5,
        "description": "A deliberate fake-out. Hard to counter effectively.",
        "effectiveness": {"none": 1.0, "cloth": 1.0, "leather": 1.0, "mail": 1.0},
        "special": "evade",
    },

    # ── AXE ──────────────────────────────────────────────────────────────
    "Hack": {
        "power": 10,
        "description": "A heavy chopping strike.",
        "effectiveness": {"none": 1.5, "cloth": 1.5, "leather": 1.3, "mail": 0.8},
        "special": None,
    },
    "Cleave": {
        "power": 12,
        "description": "A sweeping blow with full body weight.",
        "effectiveness": {"none": 1.5, "cloth": 1.5, "leather": 1.2, "mail": 0.7},
        "special": None,
    },
    "Overhead": {
        "power": 17,
        "description": "A devastating overhead strike. 25% chance to miss.",
        "effectiveness": {"none": 1.5, "cloth": 1.5, "leather": 1.2, "mail": 0.9},
        "special": "miss_chance",
        "special_value": 0.25,
    },

    # ── MACE ─────────────────────────────────────────────────────────────
    "Bash": {
        "power": 9,
        "description": "A direct blunt strike. Made for mail.",
        "effectiveness": {"none": 1.5, "cloth": 1.0, "leather": 1.0, "mail": 1.5},
        "special": None,
    },
    "Smash": {
        "power": 13,
        "description": "A two-handed blow. Devastating vs armour. 20% miss chance.",
        "effectiveness": {"none": 1.3, "cloth": 0.9, "leather": 0.9, "mail": 1.8},
        "special": "miss_chance",
        "special_value": 0.20,
    },
    "Stagger": {
        "power": 6,
        "description": "Aimed at their balance, not their body.",
        "effectiveness": {"none": 1.0, "cloth": 1.0, "leather": 1.0, "mail": 1.2},
        "special": "stagger",
    },

    # ── BOW ──────────────────────────────────────────────────────────────
    "Pot Shot": {
        "power": 7,
        "description": "A quick shot while staying mobile. Reduces counter risk.",
        "effectiveness": {"none": 1.3, "cloth": 1.3, "leather": 1.0, "mail": 0.7},
        "special": "evade",
    },
    "Snipe": {
        "power": 14,
        "description": "A patient, precise shot. Boosted by your Stealth skill.",
        "effectiveness": {"none": 1.5, "cloth": 1.5, "leather": 1.3, "mail": 1.0},
        "special": "stealth_boost",
    },
    "Long Shot": {
        "power": 8,
        "description": "A ranged strike with some Martial pull behind it.",
        "effectiveness": {"none": 1.4, "cloth": 1.4, "leather": 1.2, "mail": 0.9},
        "special": "martial_boost",
    },

    # ── STAFF ────────────────────────────────────────────────────────────
    "Staff Strike": {
        "power": 7,
        "description": "A basic strike with the staff.",
        "effectiveness": {"none": 1.2, "cloth": 1.0, "leather": 1.0, "mail": 0.8},
        "special": None,
    },
    "Sweep": {
        "power": 9,
        "description": "A wide sweep covering multiple angles.",
        "effectiveness": {"none": 1.3, "cloth": 1.2, "leather": 1.0, "mail": 0.7},
        "special": None,
    },
    "Channel": {
        "power": 3,
        "description": "A light strike. Reduces cost of your next spell by 5 mana.",
        "effectiveness": {"none": 1.0, "cloth": 1.0, "leather": 1.0, "mail": 1.0},
        "special": "mana_discount",
    },
}

# Weapon type key → list of 3 move names
WEAPON_MOVE_SETS = {
    "unarmed": ["Strike", "Shove",       "Pummel"],
    "sword":   ["Slash",  "Pierce",      "Parry"],
    "dagger":  ["Stab",   "Pierce",      "Feint"],
    "axe":     ["Hack",   "Cleave",      "Overhead"],
    "mace":    ["Bash",   "Smash",       "Stagger"],
    "bow":     ["Pot Shot","Snipe",       "Long Shot"],
    "staff":   ["Staff Strike","Sweep",  "Channel"],
}

DEFAULT_MOVES = WEAPON_MOVE_SETS["unarmed"]


def get_moves_for_weapon(weapon_type: str) -> list:
    return WEAPON_MOVE_SETS.get(weapon_type or "unarmed", DEFAULT_MOVES)
