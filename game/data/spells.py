"""
Spell definitions.

Fields:
  cost          — mana cost to cast
  power         — base damage power
  self_cost     — HP the caster pays at cast time (win or lose the roll)
  tier          — "basic" | "mid" | "advanced"
  description   — short in-game description shown in menus
  lore          — two-line flavour text shown when reading a grimtotem
  effectiveness — armor type multipliers
  special       — "slow" | "heal" | "evade" | "drain" | None
  heal_amount   — for heal/drain spells: HP restored to caster
  require_magic — minimum Magic skill to use the spell
  damage_type   — "frost" | "fire" | "lightning" | "shadow" | "heal"
"""

SPELLS = {

    # ══════════════════════════════════════════════════════════════
    #  BASIC TIER  (require_magic 5–14)
    # ══════════════════════════════════════════════════════════════

    "Frost Bolt": {
        "cost":          12,
        "power":         13,
        "self_cost":     0,
        "tier":          "basic",
        "description":   "A bolt of ice that bites and slows the target.",
        "lore":          "The frost does not kill you quickly. That is the point.\nA mage who learned patience before power.",
        "effectiveness": {"none": 1.3, "cloth": 1.0, "leather": 1.0, "mail": 1.3},
        "special":       "slow",
        "require_magic": 5,
        "damage_type":   "frost",
    },

    "Shock": {
        "cost":          8,
        "power":         10,
        "self_cost":     2,
        "tier":          "basic",
        "description":   "A quick electrical discharge. You also take 2 HP from the feedback.",
        "lore":          "Lightning is not conjured — it is redirected.\nThe body pays the toll for being the conduit.",
        "effectiveness": {"none": 1.2, "cloth": 1.0, "leather": 1.1, "mail": 1.4},
        "special":       None,
        "require_magic": 8,
        "damage_type":   "lightning",
    },

    # ══════════════════════════════════════════════════════════════
    #  MID TIER  (require_magic 15–35)
    # ══════════════════════════════════════════════════════════════

    "Fireball": {
        "cost":          15,
        "power":         18,
        "self_cost":     0,
        "tier":          "mid",
        "description":   "Concentrated flame hurled at your foe.",
        "lore":          "Fire is the first magic most learn and the last most master.\nIt does not discriminate — it burns what is near.",
        "effectiveness": {"none": 1.5, "cloth": 1.5, "leather": 1.2, "mail": 0.7},
        "special":       None,
        "require_magic": 15,
        "damage_type":   "fire",
    },

    "Healing Word": {
        "cost":          20,
        "power":         0,
        "self_cost":     0,
        "tier":          "mid",
        "description":   "A whispered word that knits flesh together. Restores 25 HP.",
        "lore":          "The word is not the medicine. The word is the permission.\nYour body already knows how to heal — the spell reminds it.",
        "effectiveness": {},
        "special":       "heal",
        "heal_amount":   25,
        "require_magic": 20,
        "damage_type":   "heal",
    },

    "Shadow Step": {
        "cost":          18,
        "power":         16,
        "self_cost":     0,
        "tier":          "mid",
        "description":   "You vanish briefly and strike from an unexpected angle.",
        "lore":          "You are not invisible. You are simply where they are not looking.\nThat is usually enough.",
        "effectiveness": {"none": 1.8, "cloth": 1.5, "leather": 1.3, "mail": 1.2},
        "special":       "evade",
        "require_magic": 25,
        "damage_type":   "shadow",
    },

    "Drain Life": {
        "cost":          15,
        "power":         20,
        "self_cost":     8,
        "tier":          "mid",
        "description":   "Necromancy. Tears vitality from the target and returns half to you. Costs 8 HP.",
        "lore":          "Life is not created by this spell — it is taken.\nThe toll you pay is the reminder of what you are doing.",
        "effectiveness": {"none": 1.5, "cloth": 1.3, "leather": 1.2, "mail": 1.0},
        "special":       "drain",
        "heal_amount":   10,
        "require_magic": 30,
        "damage_type":   "shadow",
    },

    # ══════════════════════════════════════════════════════════════
    #  ADVANCED TIER  (require_magic 36+)
    # ══════════════════════════════════════════════════════════════

    "Lightning Arc": {
        "cost":          32,
        "power":         26,
        "self_cost":     3,
        "tier":          "advanced",
        "description":   "Raw lightning that strips through all armour. You take 3 HP from the surge.",
        "lore":          "The arc does not stop at the target. It continues until it finds earth.\nYou are between it and earth.",
        "effectiveness": {"none": 1.5, "cloth": 1.5, "leather": 1.5, "mail": 1.5},
        "special":       None,
        "require_magic": 40,
        "damage_type":   "lightning",
    },

    "Soul Rend": {
        "cost":          25,
        "power":         38,
        "self_cost":     15,
        "tier":          "advanced",
        "description":   "Necromancy. Unmakes the target at the soul. Costs 15 HP from the caster.",
        "lore":          "You are not killing them. You are unmaking them.\nThe part of you that does this grows quieter afterward.",
        "effectiveness": {"none": 2.0, "cloth": 1.8, "leather": 1.6, "mail": 1.4},
        "special":       None,
        "require_magic": 55,
        "damage_type":   "shadow",
    },
}


def get_available_spells(magic_skill: int, learned_spells: list = None) -> dict:
    """
    Return spells the player can cast.
    Requires: magic_skill >= require_magic AND spell in learned_spells (if provided).
    If learned_spells is None, only the magic_skill gate applies (used for enemies).
    """
    return {
        name: spell
        for name, spell in SPELLS.items()
        if magic_skill >= spell["require_magic"]
        and (learned_spells is None or name in learned_spells)
    }


def spells_for_tier(tier: str) -> dict:
    """Return all spells in a given tier."""
    return {n: s for n, s in SPELLS.items() if s["tier"] == tier}
