"""
Full item database.

item_type values:
  weapon / armor / ring / necklace / potion / book / material / consumable / gem

New optional fields (all default to None/0/False for backward compat):
  weapon_type  — "sword" | "dagger" | "axe" | "mace" | "bow" | "staff"
  armor_value  — defense points granted when equipped
  stat_bonuses — {skill_name: int} applied while equipped (ring/necklace)
  effect       — potion effect string: "heal_30" | "mana_25" | "str_boost" | "agi_boost"
  lore         — two-sentence lore text (books)
  cursed       — if True, applying debuff on equip
  curse_effect — "drain_hp" | "reduce_max_hp"
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict

RARITY_WEIGHTS = {
    "common":   60,
    "uncommon": 25,
    "rare":     12,
    "epic":      3,
}

RARITY_LABELS = {
    "common":   "Common",
    "uncommon": "Uncommon",
    "rare":     "Rare",
    "epic":     "EPIC",
}


@dataclass
class Item:
    name: str
    base_value: int
    rarity: str
    item_type: str
    description: str
    biome_tags: List[str]                    = field(default_factory=list)
    weapon_type: Optional[str]               = None
    armor_value: int                         = 0
    stat_bonuses: Optional[Dict[str, int]]   = None
    effect: Optional[str]                    = None
    lore: Optional[str]                      = None
    cursed: bool                             = False
    curse_effect: Optional[str]             = None
    spell_name: Optional[str]               = None   # grimtotems only


# ── TRADE GOODS (raw materials, gems) ────────────────────────────────────────
TRADE_ITEMS = [
    Item("Rough Cloth",      10, "common",   "material",   "Coarse fabric, useful for repairs.",                  ["dusthaven"]),
    Item("Dried Fruit",       8, "common",   "consumable", "Desert staple. Sweet and long-lasting.",              ["dusthaven"]),
    Item("Herb Bundle",      12, "common",   "consumable", "Forest herbs with mild healing properties.",          ["ashenvale"]),
    Item("Wolf Tooth",       15, "common",   "material",   "Curio value. Some alchemists want these.",            ["ashenvale"]),
    Item("Copper Ore",       18, "common",   "material",   "Raw copper from shallow deposits.",                   ["ironpeak"]),
    Item("Leather Strap",    14, "common",   "material",   "Tanned leather for bindings and repairs.",            ["ashenvale"]),
    Item("Goblin Ear",        6, "common",   "material",   "Proof of a kill. Bounty offices pay a small sum.",   []),
    Item("Iron Ore",         22, "common",   "material",   "Unrefined iron from mountain rock.",                  ["ironpeak"]),
    Item("Wolf Pelt",        70, "uncommon", "material",   "A thick, warm pelt. Good for desert trade.",         ["ashenvale"]),
    Item("Silk Cloth",       90, "uncommon", "material",   "Fine silk from desert caravan traders.",              ["dusthaven"]),
    Item("Amber Vial",       75, "uncommon", "consumable", "Mysterious amber liquid. Alchemical value.",          []),
    Item("Spice Pouch",      65, "uncommon", "material",   "Exotic spices from the desert markets.",              ["dusthaven"]),
    Item("Dragon Hide",     280, "rare",     "material",   "A shard of drake scale. Completely fireproof.",       []),
    Item("Moonstone",       320, "rare",     "gem",        "Glows faintly by night. Highly sought.",              []),
    Item("Enchanted Cloth", 290, "rare",     "material",   "Woven with minor protective magic.",                  []),
    Item("Daedric Shard",   900, "epic",     "material",   "A fragment from another plane. Immense power.",       []),
    Item("Phoenix Feather", 850, "epic",     "material",   "Still warm to the touch. Alchemists will pay anything.", []),
    Item("Star Ruby",       950, "epic",     "gem",        "Deep red, perfectly cut. Absolutely flawless.",       []),
    Item("Ancient Relic",  1100, "epic",     "material",   "Purpose unknown. Its age is unmistakable.",           []),
    Item("Silver Ring",      95, "uncommon", "gem",        "A simple silver band. Clean craftsmanship.",          []),
    Item("Gold Amulet",     350, "rare",     "gem",        "Engraved with forgotten sigils.",                     []),
]

# ── WEAPONS (equippable) ─────────────────────────────────────────────────────
WEAPON_ITEMS = [
    Item("Wooden Club",      20, "common",   "weapon", "Heavy wood. Crude but effective.",             ["ashenvale"], weapon_type="mace"),
    Item("Iron Sword",       40, "common",   "weapon", "A basic iron sword. Reliable.",                ["ironpeak"],  weapon_type="sword"),
    Item("Iron Axe",         45, "common",   "weapon", "A heavy chopping axe. Serviceable.",           ["ironpeak"],  weapon_type="axe"),
    Item("Short Bow",        55, "common",   "weapon", "Light and accurate at short range.",            ["ashenvale"], weapon_type="bow"),
    Item("Steel Dagger",     85, "uncommon", "weapon", "Well-balanced. Holds a sharp edge.",           ["ironpeak"],  weapon_type="dagger"),
    Item("Steel Mace",       90, "uncommon", "weapon", "A solid flanged mace. Mail's worst enemy.",    ["ironpeak"],  weapon_type="mace"),
    Item("Hunting Bow",     110, "uncommon", "weapon", "A longer bow with better range and pull.",     ["ashenvale"], weapon_type="bow"),
    Item("Mage Staff",      110, "uncommon", "weapon", "Carved ashwood with a crystal tip.",           ["ashenvale"], weapon_type="staff"),
    Item("Elven Blade",     300, "rare",     "weapon", "Ancient craftsmanship. Light as a whisper.",   [],            weapon_type="sword"),
    Item("Void Bow",        400, "rare",     "weapon", "Arrows from this bow arrive before you hear the shot.", [], weapon_type="bow"),
    Item("Cursed Blade",     50, "uncommon", "weapon", "A blade that hums with wrong energy.",         [],
         weapon_type="sword", cursed=True, curse_effect="drain_hp"),
]

# ── ARMOUR (equippable) ──────────────────────────────────────────────────────
# Armor types carry skill bonuses/penalties:
#   Cloth (Padded): +Magic 2          — suits mages, light and unobtrusive
#   Leather:        +Stealth 3, +Survival 1  — suits rogues and rangers
#   Mail/Plate:     +Martial, +Survival 2, -Stealth — suits warriors; penalises stealth builds
# No armour equipped grants a passive +3 Magic (applied in player.skill())
ARMOR_ITEMS = [
    Item("Padded Jacket",   35,  "common",   "armor", "Light cloth padding. Better than nothing.",       [], armor_value=3,
         stat_bonuses={"Magic": 2}),
    Item("Leather Vest",    65,  "common",   "armor", "Tanned hide stitched into a serviceable vest.",   [], armor_value=6,
         stat_bonuses={"Stealth": 3, "Survival": 1}),
    Item("Chain Hauberk",   120, "uncommon", "armor", "Interlocked iron rings. Heavy but effective.",    [], armor_value=10,
         stat_bonuses={"Martial": 3, "Survival": 2, "Stealth": -3}),
    Item("Scale Armour",    180, "uncommon", "armor", "Overlapping steel scales. Solid protection.",     [], armor_value=13,
         stat_bonuses={"Martial": 4, "Survival": 2, "Stealth": -4}),
    Item("Plate Cuirass",   350, "rare",     "armor", "Full-torso plate. Serious investment.",           [], armor_value=18,
         stat_bonuses={"Martial": 6, "Survival": 2, "Stealth": -6}),
]

# ── ACCESSORIES — rings and necklaces ────────────────────────────────────────
ACCESSORY_ITEMS = [
    Item("Copper Ring",      18, "common",   "ring",     "A plain copper band.",                     [], stat_bonuses={"Martial": 2}),
    Item("Thief's Signet",   80, "uncommon", "ring",     "Worn smooth by quick fingers.",            [], stat_bonuses={"Stealth": 5}),
    Item("Merchant's Band",  85, "uncommon", "ring",     "A ring favoured by successful traders.",   [], stat_bonuses={"Merchantilism": 5}),
    Item("Ranger's Cord",    70, "uncommon", "necklace", "Braided leather worn by forest scouts.",   [], stat_bonuses={"Survival": 5}),
    Item("Scholar's Chain", 120, "rare",     "necklace", "Thin gold links with a carved lens.",      [], stat_bonuses={"Dungeoneering": 6, "Magic": 3}),
    Item("Warband Totem",   140, "rare",     "necklace", "A soldier's charm. Inspires precision.",   [], stat_bonuses={"Martial": 6, "Survival": 3}),
    Item("Skull Ring",       30, "uncommon", "ring",     "Cold to the touch. Something is wrong.",   [],
         stat_bonuses={"Martial": 8}, cursed=True, curse_effect="reduce_max_hp"),
]

# ── POTIONS (consumable in and out of combat) ─────────────────────────────────
POTION_ITEMS = [
    Item("Health Potion",    30, "common",   "potion", "A red vial. Restores 30 HP.",                    [], effect="heal_30"),
    Item("Mana Draught",     35, "common",   "potion", "A blue vial. Restores 25 mana.",                 [], effect="mana_25"),
    Item("Strength Draft",   45, "uncommon", "potion", "Raises combat power for one fight.",             [], effect="str_boost"),
    Item("Swiftness Tonic",  40, "uncommon", "potion", "Raises agility for one fight.",                  [], effect="agi_boost"),
    Item("Full Restore",     90, "rare",     "potion", "Restores HP and mana fully. Tastes awful.",      [], effect="full_restore"),
]

# ── ROAD SUPPLIES (survival / dungeoneering merchant stock) ───────────────────
SUPPLY_ITEMS = [
    Item("Rope",               12, "common",   "material",   "Fifty feet of sturdy hemp. Always useful.",       [], effect=None),
    Item("Dried Rations",      15, "common",   "consumable", "Hard tack and salted meat. Restores 15 HP.",      [], effect="heal_15"),
    Item("Torch Bundle",       10, "common",   "consumable", "Three torches bound together. Lights the dark.",  [], effect="torch"),
    Item("Adventurer's Map",   45, "uncommon", "consumable",
         "A hand-drawn map of nearby roads. Increases chance of finding locations.",
         [], effect="map_bonus"),
    Item("Firewood",            8, "common",   "material",   "Split kindling for a road camp.",                 [], effect=None),
    Item("Tinderbox",          18, "common",   "material",   "Flint and steel. Never leave town without one.",  [], effect=None),
    Item("Bandages",           20, "common",   "consumable", "Clean linen wraps. Restores 20 HP out of combat.", [], effect="heal_20"),
    Item("Grappling Hook",     35, "uncommon", "material",   "Thrown iron hook with rope. Dungeoneers swear by it.", [], effect=None),
    Item("Lock Picks",         55, "uncommon", "material",   "A set of slender picks. Illegal in Greyspire.",   [], effect=None),
    Item("Lantern",            40, "uncommon", "consumable", "A hooded lantern. Reveals the unseen.",            [], effect="torch"),
]

# ── HUNT YIELDS (meat, pelts, bones — from hunting minigame) ─────────────────
HUNT_ITEMS = [
    Item("Small Game Meat",  8,  "common",   "consumable", "Squirrel or fox, roasted on a stick. Restores 20 HP.",      [], effect="heal_20"),
    Item("Dried Meat",       12, "common",   "consumable", "Smoked trail meat. Hearty road fare. Restores 35 HP.",      [], effect="heal_35"),
    Item("Venison",          20, "uncommon", "consumable", "Fresh deer, dressed in the field. Restores 40 HP.",         [], effect="heal_40"),
    Item("Bear Meat",        25, "uncommon", "consumable", "Dense, rich meat. A full belly. Restores 40 HP.",           [], effect="heal_40"),
    Item("Squirrel Pelt",    10, "common",   "material",   "Soft and small. Furriers pay little for it.",               []),
    Item("Fox Pelt",         28, "common",   "material",   "Russet fur. Decent trade value with leatherworkers.",       []),
    Item("Deer Pelt",        50, "uncommon", "material",   "Supple hide. Leatherworkers prize it.",                     []),
    Item("Elk Pelt",         80, "uncommon", "material",   "Thick and wide. Fine quality.",                             []),
    Item("Bear Pelt",       130, "rare",     "material",   "Immense and dense. Worth real coin.",                       []),
    Item("Bone Tusk",        35, "common",   "material",   "Curved bone from large game. Alchemists use these.",        []),
    Item("Bear Claw",        45, "uncommon", "material",   "A large, hooked claw. Curio merchants pay well.",           []),
    Item("Mystical Fang",   220, "rare",     "material",   "A fang from no natural creature. Glows faintly.",           []),
]

# ── GRIMTOTEMS (purchased from Librarian/Mage — learned via reading) ─────────
# Basic (10–40g), Mid (60–150g), Advanced (200–400g)
GRIMTOTEM_ITEMS = [
    Item("Grimtotem of Frost",    20,  "common",   "grimtotem", "A slim tome bound in blue thread. Frost Bolt.",            [], spell_name="Frost Bolt"),
    Item("Grimtotem of Shock",    15,  "common",   "grimtotem", "A singed pamphlet. Crackles faintly. Shock.",               [], spell_name="Shock"),
    Item("Grimtotem of Fire",     70,  "uncommon", "grimtotem", "A heat-warped tome. Fireball.",                             [], spell_name="Fireball"),
    Item("Grimtotem of Mending",  90,  "uncommon", "grimtotem", "Soft covers, gentle script. Healing Word.",                 [], spell_name="Healing Word"),
    Item("Grimtotem of Shadows", 110,  "uncommon", "grimtotem", "Dark ink on dark pages. Shadow Step.",                      [], spell_name="Shadow Step"),
    Item("Grimtotem of Draining",130,  "uncommon", "grimtotem", "Smells of old blood. Drain Life.",                          [], spell_name="Drain Life"),
    Item("Grimtotem of the Arc", 280,  "rare",     "grimtotem", "Scorched. Bindings fused. Lightning Arc.",                  [], spell_name="Lightning Arc"),
    Item("Grimtotem of Rending", 380,  "rare",     "grimtotem", "Black pages. No author listed. Soul Rend.",                 [], spell_name="Soul Rend"),
]

# ── FORAGE FINDS (from Bushcraft — quality scales with Survival) ──────────────
FORAGE_ITEMS = [
    Item("Unknown Berries",  3,  "common",   "consumable", "Unidentified wild berries. Eat at your own risk.",          [], effect="berries_unknown"),
    Item("Blueberries",      8,  "common",   "consumable", "Wild blueberries. Fresh and nutritious. Restores 20 HP.",   [], effect="heal_20"),
    Item("Wild Mushrooms",   10, "common",   "consumable", "Earthy forest mushrooms. Restores 15 HP and 10 Mana.",      [], effect="mushroom_wild"),
    Item("Nightshade",       30, "uncommon", "material",   "Identified: highly toxic. Do NOT eat. Alchemists pay well.", []),
]

# ── LORE BOOKS (readable, sell for small amounts) ─────────────────────────────
BOOK_ITEMS = [
    Item("The Merchant's Code",      15, "common",   "book",
         "A slim volume of trading laws.",
         [],
         lore="Trade in Al-Rimal is governed by unwritten rules older than any treaty. Break them once and the caravan masters will remember."),
    Item("Waldheim: A History",      12, "common",   "book",
         "Damp pages, faded ink.",
         [],
         lore="Waldheim was not always a settlement. Before the hunters came, it was a burial ground for a people whose name has not survived."),
    Item("Geology of Greyspire",      18, "common",   "book",
         "Densely technical, with margin notes.",
         [],
         lore="The ore veins beneath Greyspire run deeper than any mine has reached. The locals believe something lives in the unmined dark."),
    Item("On the Nature of Goblins", 10, "common",   "book",
         "Illustrated with unsettling accuracy.",
         [],
         lore="Goblins do not form armies by choice. Something is always driving them. When you kill one, ask yourself what it was running from."),
    Item("The Sellsword's Almanac",  20, "uncommon", "book",
         "A battered field manual.",
         [],
         lore="Every city worth defending has already been lost once. The Almanac is a record of what that costs — in coin, in blood, and in the kind of reputation that doesn't recover."),
]

# ── Combined lookup ───────────────────────────────────────────────────────────

ALL_ITEMS = (
    WEAPON_ITEMS + ARMOR_ITEMS + ACCESSORY_ITEMS +
    POTION_ITEMS + SUPPLY_ITEMS + TRADE_ITEMS +
    GRIMTOTEM_ITEMS + FORAGE_ITEMS + HUNT_ITEMS + BOOK_ITEMS
)

ITEM_LOOKUP = {item.name: item for item in ALL_ITEMS}


def get_items_by_rarity(rarity: str, item_type: str = None):
    """Return all items of a given rarity, optionally filtered by item_type."""
    return [
        i for i in ALL_ITEMS
        if i.rarity == rarity and (item_type is None or i.item_type == item_type)
    ]
