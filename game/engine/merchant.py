"""
Merchant system — types, stock pools, generation, and pricing helpers.
"""

import random

from engine.player import SKILLS
from data.items import (
    WEAPON_ITEMS, ARMOR_ITEMS, ACCESSORY_ITEMS, POTION_ITEMS,
    SUPPLY_ITEMS, GRIMTOTEM_ITEMS,
)


# ── Pricing ───────────────────────────────────────────────────────────────────

def sell_price(item, city, gp_delta: int = 0) -> int:
    """65% of base value, modified by city scarcity/abundance and negotiate gp_delta."""
    base = max(1, round(item.base_value * city.price_modifier(item.name) * 0.65))
    return max(1, base + gp_delta)


def buy_price(item, city, gp_delta: int = 0) -> int:
    """130% of base value, modified by city pricing and negotiate gp_delta."""
    base = max(1, round(item.base_value * city.price_modifier(item.name) * 1.30))
    return max(1, base - gp_delta)


# ── Merchant names ────────────────────────────────────────────────────────────

MERCHANT_NAMES = [
    "Aldric", "Berwen", "Cade", "Drusilla", "Eamon", "Farren",
    "Gwenda", "Halsten", "Irja", "Jovan", "Kael", "Lidda",
    "Maren", "Nath", "Orla", "Pell", "Quelda", "Rowan",
    "Sable", "Torsten", "Ulric", "Veyra", "Westan", "Xanthe",
    "Yvor", "Zara", "Brand", "Corra", "Daven", "Elsin",
]


# ── Stock pool functions ──────────────────────────────────────────────────────

def _pool_blacksmith():
    return [i for i in WEAPON_ITEMS + ARMOR_ITEMS if not i.cursed]

def _pool_apothecary():
    return list(POTION_ITEMS)

def _pool_librarian(magic_skill: int = 25):
    from data.items import BOOK_ITEMS
    pool = list(BOOK_ITEMS)
    magic_bonus = magic_skill * 0.002
    tier_chances = {"basic": 0.22 + magic_bonus, "mid": 0.08 + magic_bonus * 0.5, "advanced": 0.02 + magic_bonus * 0.25}
    from data.spells import SPELLS
    for gt in GRIMTOTEM_ITEMS:
        spell = SPELLS.get(gt.spell_name, {})
        tier  = spell.get("tier", "basic")
        if random.random() < tier_chances.get(tier, 0.05):
            pool.append(gt)
    return pool

def _pool_survival():
    return [i for i in SUPPLY_ITEMS if i.item_type in ("material", "consumable")]

def _pool_dungeoneering():
    from data.items import BOOK_ITEMS
    dung_names = {"Rope", "Grappling Hook", "Lock Picks", "Lantern",
                  "Tinderbox", "Torch Bundle", "Adventurer's Map"}
    return (
        [i for i in SUPPLY_ITEMS if i.name in dung_names]
        + list(BOOK_ITEMS)
    )

def _pool_leatherworker():
    leather_armor = [i for i in ARMOR_ITEMS
                     if i.stat_bonuses and "Stealth" in i.stat_bonuses and not i.cursed]
    return leather_armor + [i for i in ACCESSORY_ITEMS if not i.cursed]

def _pool_mage():
    from data.spells import SPELLS
    pool = []
    mid_chance      = 0.60
    advanced_chance = 0.30
    for gt in GRIMTOTEM_ITEMS:
        spell  = SPELLS.get(gt.spell_name, {})
        tier   = spell.get("tier", "basic")
        chance = {"basic": 0.80, "mid": mid_chance, "advanced": advanced_chance}.get(tier, 0.5)
        if random.random() < chance:
            pool.append(gt)
    if not pool:
        pool = [GRIMTOTEM_ITEMS[0]]
    return pool


# ── Merchant type registry ────────────────────────────────────────────────────
# (type_label, tagline, pool_fn)

MERCHANT_TYPES = [
    ("Blacksmith",        "Soot-stained hands, straight talk, sharp steel.",                     _pool_blacksmith),
    ("Apothecary",        "Herbs and remedies for every road ailment.",                          _pool_apothecary),
    ("Librarian",         "Quiet, watchful — lore texts and possibility of finding tomes.",      _pool_librarian),
    ("Survival Trader",   "Rations, rope, and everything the road demands.",                     _pool_survival),
    ("Dungeoneering Co.", "Lanterns, picks, and maps of the unseen places.",                     _pool_dungeoneering),
    ("Leatherworker",     "Soft goods for those who prefer to stay unnoticed.",                  _pool_leatherworker),
    ("Mage Merchant",     "Grimoires, tomes, and spells for those with the gift.",               _pool_mage),
]

MERCHANT_GREETINGS = {
    "Blacksmith": [
        "Steel doesn't lie. Let's see what you need.",
        "I don't do small talk. You buying or not?",
        "Good timing. Just finished a batch.",
        "You look like you've been in a fight. Want to be better prepared for the next one?",
    ],
    "Apothecary": [
        "Come closer — you look pale. I may have something for that.",
        "The road takes its toll. I have remedies.",
        "Everything I sell, I've tested. Not always on myself.",
        "Healing is just chemistry. Don't let the mystics tell you otherwise.",
    ],
    "Librarian": [
        "Quietly. I prefer quiet customers.",
        "Knowledge is weight. Worth carrying.",
        "I don't ask what you're looking for. I just show you what I have.",
        "Most people don't read. That's why most people don't survive.",
    ],
    "Survival Trader": [
        "First rule of the road: never leave without rope.",
        "Rations, firewood, the basics. You'd be surprised how many forget them.",
        "The road doesn't care about your skills. It cares whether you packed right.",
        "You heading out again? Let's make sure you're ready this time.",
    ],
    "Dungeoneering Co.": [
        "You look like someone who goes places they shouldn't. I respect that.",
        "A lantern and a good lock pick. Everything else is a liability.",
        "The dark is predictable. It's the things in the dark that aren't.",
        "We supply half the dungeoneers in this region. The surviving half.",
    ],
    "Leatherworker": [
        "Quiet gear for quiet people. Take a look.",
        "Mail makes noise. Leather doesn't. Worth thinking about.",
        "A good vest has saved more lives than a sword. Probably.",
        "I don't ask what you use it for. Just whether it fits.",
    ],
    "Mage Merchant": [
        "The grimtotems choose their readers. I just carry them.",
        "Magic skill means nothing without the words. I sell the words.",
        "Don't touch anything you haven't paid for. Some of these... respond.",
        "I've had this stock since before the last king. Some of it longer.",
    ],
}

# Guaranteed types are always present; variable ones roll 33% per city visit.
_GUARANTEED_MERCHANTS    = {"Blacksmith", "Survival Trader", "Librarian", "Dungeoneering Co."}
_VARIABLE_MERCHANT_CHANCE = 0.33


# ── Generation ────────────────────────────────────────────────────────────────

def _generate_merchant_typed(mtype_tuple: tuple, used_names: set) -> dict:
    mtype_label, tagline, pool_fn = mtype_tuple
    available = [n for n in MERCHANT_NAMES if n not in used_names]
    name      = random.choice(available) if available else random.choice(MERCHANT_NAMES)
    used_names.add(name)
    pool  = pool_fn()
    stock = random.sample(pool, min(5, len(pool))) if pool else []
    return {
        "name":           name,
        "type":           mtype_label,
        "tagline":        tagline,
        "dominant_skill": random.choice(SKILLS),
        "motivation":     random.randint(0, 3),
        "stock":          list(stock),
        "sold_items":     [],
        "gp_delta":       0,
        "negotiated":     False,
        "ejected":        False,
    }


def generate_city_merchants(city_key: str) -> list:
    """
    Generate all merchant types for a city visit.
    Guaranteed types are always available; variable types roll 33%.
    Each merchant dict carries an "available" boolean.
    """
    used      = set()
    merchants = []
    for mtype_tuple in MERCHANT_TYPES:
        mtype_label  = mtype_tuple[0]
        is_guaranteed = mtype_label in _GUARANTEED_MERCHANTS
        available     = is_guaranteed or (random.random() < _VARIABLE_MERCHANT_CHANCE)
        if available:
            m = _generate_merchant_typed(mtype_tuple, used)
        else:
            m = {
                "name":           mtype_label,
                "type":           mtype_label,
                "tagline":        "Not in town today.",
                "dominant_skill": random.choice(SKILLS),
                "motivation":     random.randint(0, 3),
                "stock":          [],
                "sold_items":     [],
                "gp_delta":       0,
                "negotiated":     False,
                "ejected":        False,
                "available":      False,
            }
        m["available"] = available
        merchants.append(m)
    return merchants
