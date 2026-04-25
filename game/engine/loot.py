"""
Loot generation.
Weighted random selection by rarity tier, shifted by enemy loot_bias.

Bias modifiers push probability mass toward higher tiers:
  common   → default weights
  uncommon → boost uncommon/rare
  rare     → strong boost to rare, some epic
  epic     → rare is common, epic is reachable
"""

import random
from data.items import ALL_ITEMS, Item

# Base rarity weights (common = most frequent, epic = very rare)
RARITY_WEIGHTS = {
    "common":   60,
    "uncommon": 25,
    "rare":     12,
    "epic":      3,
}

# Per-bias multipliers applied on top of base rarity weights
LOOT_BIAS_MODIFIERS = {
    "common":   {"common": 1.0,  "uncommon": 1.0,  "rare": 1.0,  "epic": 1.0},
    "uncommon": {"common": 0.6,  "uncommon": 1.6,  "rare": 1.3,  "epic": 1.0},
    "rare":     {"common": 0.3,  "uncommon": 1.0,  "rare": 2.2,  "epic": 1.6},
    "epic":     {"common": 0.1,  "uncommon": 0.5,  "rare": 1.5,  "epic": 3.5},
}


def generate_loot_min_rarity(min_rarity: str = "uncommon") -> Item:
    """Generate loot guaranteed at or above min_rarity. Falls back to generate_loot() if pool is empty."""
    RARITY_ORDER = ["common", "uncommon", "rare", "epic"]
    min_idx      = RARITY_ORDER.index(min_rarity)
    eligible     = set(RARITY_ORDER[min_idx:])

    pool    = [item for item in ALL_ITEMS if item.rarity in eligible]
    weights = [RARITY_WEIGHTS[item.rarity] for item in pool]

    if not pool:
        return generate_loot()
    return random.choices(pool, weights=weights, k=1)[0]


def generate_loot(bias: str = "common") -> Item:
    """
    Generate one loot item using weighted random selection.
    bias corresponds to the defeated enemy's loot_bias field.
    """
    modifiers = LOOT_BIAS_MODIFIERS.get(bias, LOOT_BIAS_MODIFIERS["common"])

    pool    = []
    weights = []
    for item in ALL_ITEMS:
        base_w   = RARITY_WEIGHTS[item.rarity]

        adjusted = base_w * modifiers[item.rarity]
        pool.append(item)
        weights.append(adjusted)

    return random.choices(pool, weights=weights, k=1)[0]
