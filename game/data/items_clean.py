"""
Full item database.

item_type values:
  weapon / armor / ring / necklace / potion / book / material / consumable / gem

New optional fields (all default to None/0/False for backward compat):
  weapon_type  — "sword" | "dagger" | "axe" | "mace" | "bow" | "staff"
  armor_value  — defense points granted when equipped
  stat_bonuses — {skill_name: int} applied while equipped (ring/necklace)
  effect       — potion effect string: "heal_30" | "mana_25" | "str_boost" | "agi_boost"
  lore         — flavour fragment shown in inventory: one cryptic line implying history
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
    Item("Rough Cloth",      10, "common",   "material",   "Coarse fabric, useful for repairs.",
         ["dusthaven"],
         lore="Cut from a bolt found outside Velrath. The city no longer trades in cloth."),
    Item("Dried Fruit",       8, "common",   "consumable", "Desert staple. Sweet and long-lasting.",
         ["dusthaven"],
         lore="The Al-Rimal caravans carried this for three hundred miles. Not all of them arrived."),
    Item("Herb Bundle",      12, "common",   "consumable", "Forest herbs with mild healing properties.",
         ["ashenvale"],
         lore="Pressed by a hand that knew what it was doing. The binding cord is funeral black."),
    Item("Wolf Tooth",       15, "common",   "material",   "Curio value. Some alchemists want these.",
         ["ashenvale"],
         lore="Brother Edric collected forty-seven of these. He stopped after the forty-eighth hunt."),
    Item("Copper Ore",       18, "common",   "material",   "Raw copper from shallow deposits.",
         ["ironpeak"],
         lore="The vein this came from was sealed in the third collapse. Nobody went back for the miners."),
    Item("Leather Strap",    14, "common",   "material",   "Tanned leather for bindings and repairs.",
         ["ashenvale"],
         lore="Stamped with the mark of a tannery that burned down in the Ashenvale riots."),
    Item("Goblin Ear",        6, "common",   "material",   "Proof of a kill. Bounty offices pay a small sum.",
         [],
         lore="The bounty office in Greyspire stopped asking questions after the third batch."),
    Item("Iron Ore",         22, "common",   "material",   "Unrefined iron from mountain rock.",
         ["ironpeak"],
         lore="Ironpeak's ore runs black near the deep shafts. Smelters charge extra to touch it."),
    Item("Wolf Pelt",        70, "uncommon", "material",   "A thick, warm pelt. Good for desert trade.",
         ["ashenvale"],
         lore="Sold by a hunter who swore this was the last wolf in the Greywood. It wasn't."),
    Item("Silk Cloth",       90, "uncommon", "material",   "Fine silk from desert caravan traders.",
         ["dusthaven"],
         lore="Woven in a city east of the known roads. The weaver's guild will not say which one."),
    Item("Amber Vial",       75, "uncommon", "consumable", "Mysterious amber liquid. Alchemical value.",
         [],
         lore="Lena of the Crossroads drank one. She described what she saw for six hours without stopping."),
    Item("Spice Pouch",      65, "uncommon", "material",   "Exotic spices from the desert markets.",
         ["dusthaven"],
         lore="The blend is unique to a single spice merchant in Al-Rimal. She has no apprentice."),
    Item("Dragon Hide",     280, "rare",     "material",   "A shard of drake scale. Completely fireproof.",
         [],
         lore="From the Thornspine, killed near Ashenvale a generation ago. Some say it had a name."),
    Item("Moonstone",       320, "rare",     "gem",        "Glows faintly by night. Highly sought.",
         [],
         lore="Found in the possession of a drowned man near the Greyspire docks. No boat was reported missing."),
    Item("Enchanted Cloth", 290, "rare",     "material",   "Woven with minor protective magic.",
         [],
         lore="The enchantment predates the guild that would have licensed it. No one knows who made it."),
    Item("Daedric Shard",   900, "epic",     "material",   "A fragment from another plane. Immense power.",
         [],
         lore="Recovered from the Pale Rift, three days east of any map. The expedition did not return whole."),
    Item("Phoenix Feather", 850, "epic",     "material",   "Still warm to the touch. Alchemists will pay anything.",
         [],
         lore="The bird it came from was last seen above the Ashfire Peaks in the year the second sun appeared."),
    Item("Star Ruby",       950, "epic",     "gem",        "Deep red, perfectly cut. Absolutely flawless.",
         [],
         lore="Found inside a sealed vault in the Merchant Lord's Folly. The vault had no door."),
    Item("Ancient Relic",  1100, "epic",     "material",   "Purpose unknown. Its age is unmistakable.",
         [],
         lore="Three scholars were asked to identify it. Each gave a different answer. None of them slept well after."),
    Item("Silver Ring",      95, "uncommon", "gem",        "A simple silver band. Clean craftsmanship.",
         [],
         lore="Engraved inside: 'For H. — come home.' No record of who H. was, or whether they did."),
    Item("Gold Amulet",     350, "rare",     "gem",        "Engraved with forgotten sigils.",
         [],
         lore="The sigils translate, roughly, as a name that has no modern equivalent and a warning about mirrors."),
]

# ── WEAPONS (equippable) ─────────────────────────────────────────────────────
WEAPON_ITEMS = [
    Item("Wooden Club",      20, "common",   "weapon", "Heavy wood. Crude but effective.",
         ["ashenvale"], weapon_type="mace",
         lore="Carved by someone who needed a weapon and had no iron. They made it work."),
    Item("Iron Sword",       40, "common",   "weapon", "A basic iron sword. Reliable.",
         ["ironpeak"], weapon_type="sword",
         lore="Standard issue for the Ironpeak militia, circa the border disputes. Most were never returned."),
    Item("Iron Axe",         45, "common",   "weapon", "A heavy chopping axe. Serviceable.",
         ["ironpeak"], weapon_type="axe",
         lore="The notch near the haft was not made by wood. The previous owner didn't elaborate."),
    Item("Short Bow",        55, "common",   "weapon", "Light and accurate at short range.",
         ["ashenvale"], weapon_type="bow",
         lore="A fletcher's practice bow that outlived every bow she made for sale."),
    Item("Steel Dagger",     85, "uncommon", "weapon", "Well-balanced. Holds a sharp edge.",
         ["ironpeak"], weapon_type="dagger",
         lore="Found beneath the floorboards of an inn on the old Dust Road. The innkeeper didn't ask whose it was."),
    Item("Steel Mace",       90, "uncommon", "weapon", "A solid flanged mace. Mail's worst enemy.",
         ["ironpeak"], weapon_type="mace",
         lore="Temple-blessed, once. The blessing wore off before the mace did."),
    Item("Hunting Bow",     110, "uncommon", "weapon", "A longer bow with better range and pull.",
         ["ashenvale"], weapon_type="bow",
         lore="Strung with gut from a creature the hunter refused to name. It draws heavier than it looks."),
    Item("Mage Staff",      110, "uncommon", "weapon", "Carved ashwood with a crystal tip.",
         ["ashenvale"], weapon_type="staff",
         lore="The crystal was grown, not cut. The mage who grew it is no longer accepting visitors."),
    Item("Elven Blade",     300, "rare",     "weapon", "Ancient craftsmanship. Light as a whisper.",
         [], weapon_type="sword",
         lore="Unsigned. The elven smith who made it did not want credit for what it would be used for."),
    Item("Void Bow",        400, "rare",     "weapon", "Arrows from this bow arrive before you hear the shot.",
         [], weapon_type="bow",
         lore="Commissioned by an assassin guild that no longer exists. The bow outlasted the contract."),
    Item("Cursed Blade",     50, "uncommon", "weapon", "A blade that hums with wrong energy.",
         [], weapon_type="sword", cursed=True, curse_effect="drain_hp",
         lore="Cursed: drains HP over time. Ser Aldous was found still holding it. He had been dead for a week."),
]

# ── ARMOUR (equippable) ──────────────────────────────────────────────────────
# Armor types carry skill bonuses/penalties:
#   Cloth (Padded): +Magic 2          — suits mages, light and unobtrusive
#   Leather:        +Stealth 3, +Survival 1  — suits rogues and rangers
#   Mail/Plate:     +Martial, +Survival 2, -Stealth — suits warriors; penalises stealth builds
# No armour equipped grants a passive +3 Magic (applied in player.skill())
ARMOR_ITEMS = [
    Item("Padded Jacket",   35,  "common",   "armor", "Light cloth padding. Better than nothing.",
         [], armor_value=3, stat_bonuses={"Magic": 2},
         lore="+2 Magic. A scholar's travelling coat, re-stitched for the road after she stopped needing it."),
    Item("Leather Vest",    65,  "common",   "armor", "Tanned hide stitched into a serviceable vest.",
         [], armor_value=6, stat_bonuses={"Stealth": 3, "Survival": 1},
         lore="+3 Stealth, +1 Survival. Worn by a scout who mapped the Greywood alone. He made it back most times."),
    Item("Chain Hauberk",   120, "uncommon", "armor", "Interlocked iron rings. Heavy but effective.",
         [], armor_value=10, stat_bonuses={"Martial": 3, "Survival": 2, "Stealth": -3},
         lore="+3 Martial, +2 Survival, -3 Stealth. Standard kit for the Greyspire garrison before the last war ended it."),
    Item("Scale Armour",    180, "uncommon", "armor", "Overlapping steel scales. Solid protection.",
         [], armor_value=13, stat_bonuses={"Martial": 4, "Survival": 2, "Stealth": -4},
         lore="+4 Martial, +2 Survival, -4 Stealth. Modelled on drake hide by a smith who'd never seen a drake. It still works."),
    Item("Plate Cuirass",   350, "rare",     "armor", "Full-torso plate. Serious investment.",
         [], armor_value=18, stat_bonuses={"Martial": 6, "Survival": 2, "Stealth": -6},
         lore="+6 Martial, +2 Survival, -6 Stealth. Commissioned by Lord Vayne of the Eastern Reach. He died before it was delivered."),
]

# ── ACCESSORIES — rings and necklaces ────────────────────────────────────────
ACCESSORY_ITEMS = [
    Item("Copper Ring",      18, "common",   "ring",     "A plain copper band.",
         [], stat_bonuses={"Martial": 2},
         lore="+2 Martial. Made by an apprentice smith to test his grip. He passed."),
    Item("Thief's Signet",   80, "uncommon", "ring",     "Worn smooth by quick fingers.",
         [], stat_bonuses={"Stealth": 5},
         lore="+5 Stealth. The guild mark on the inside was filed off, but not well enough."),
    Item("Merchant's Band",  85, "uncommon", "ring",     "A ring favoured by successful traders.",
         [], stat_bonuses={"Merchantilism": 5},
         lore="+5 Merchantilism. Passed down through the Elsin family for four generations. Sold at auction by the fifth."),
    Item("Ranger's Cord",    70, "uncommon", "necklace", "Braided leather worn by forest scouts.",
         [], stat_bonuses={"Survival": 5},
         lore="+5 Survival. Made from the first kill of a scout who spent thirty years in the Greywood without a map."),
    Item("Scholar's Chain", 120, "rare",     "necklace", "Thin gold links with a carved lens.",
         [], stat_bonuses={"Dungeoneering": 6, "Magic": 3},
         lore="+6 Dungeoneering, +3 Magic. The lens is ground to a prescription. Whatever she was looking for, she found it."),
    Item("Warband Totem",   140, "rare",     "necklace", "A soldier's charm. Inspires precision.",
         [], stat_bonuses={"Martial": 6, "Survival": 3},
         lore="+6 Martial, +3 Survival. Carved from the bone of the first enemy the unit ever faced together. They kept it after."),
    Item("Skull Ring",       30, "uncommon", "ring",     "Cold to the touch. Something is wrong.",
         [], stat_bonuses={"Martial": 8}, cursed=True, curse_effect="reduce_max_hp",
         lore="Cursed: -20 max HP. +8 Martial. Ser Rodrick was found wearing this. Drowned in his own blood, in a dry room."),
]

# ── POTIONS (consumable in and out of combat) ─────────────────────────────────
POTION_ITEMS = [
    Item("Health Potion",    30, "common",   "potion", "A red vial. Restores 30 HP.",
         [], effect="heal_30",
         lore="Restores 30 HP. Standard apothecary blend. The taste suggests the apothecary is cutting it with something."),
    Item("Mana Draught",     35, "common",   "potion", "A blue vial. Restores 25 mana.",
         [], effect="mana_25",
         lore="Restores 25 Mana. Brewed from deepwater kelp and something luminescent. The glow fades within an hour."),
    Item("Strength Draft",   45, "uncommon", "potion", "Raises combat power for one fight.",
         [], effect="str_boost",
         lore="+Martial for one combat. The Ironpeak arena banned this in the third year. It was too obvious."),
    Item("Swiftness Tonic",  40, "uncommon", "potion", "Raises agility for one fight.",
         [], effect="agi_boost",
         lore="+Agility for one combat. Based on a formula used by messengers during the Long Siege. They ran until they couldn't."),
    Item("Full Restore",     90, "rare",     "potion", "Restores HP and mana fully. Tastes awful.",
         [], effect="full_restore",
         lore="Fully restores HP and Mana. The alchemist who perfected this refused to sell it to armies. She sold it anyway."),
]

# ── ROAD SUPPLIES (survival / dungeoneering merchant stock) ───────────────────
SUPPLY_ITEMS = [
    Item("Rope",               12, "common",   "material",   "Fifty feet of sturdy hemp. Always useful.",
         [], effect=None,
         lore="The knot at one end was tied by someone who knew what they were doing. The other end was cut."),
    Item("Dried Rations",      15, "common",   "consumable", "Hard tack and salted meat. Restores 15 HP.",
         [], effect="heal_15",
         lore="Restores 15 HP. Road fare for soldiers who never came back to complain about the taste."),
    Item("Torch Bundle",       10, "common",   "consumable", "Three torches bound together. Lights the dark.",
         [], effect="torch",
         lore="Lights the way. The third torch in every bundle is always slightly shorter. Nobody knows why."),
    Item("Adventurer's Map",   45, "uncommon", "consumable",
         "A hand-drawn map of nearby roads. Increases chance of finding locations.",
         [], effect="map_bonus",
         lore="Increases location encounters. Drawn by a cartographer who noted 'here be mercy' over the eastern plains."),
    Item("Firewood",            8, "common",   "material",   "Split kindling for a road camp.",
         [], effect=None,
         lore="Cut from a fallen oak near Waldheim. The locals don't cut the standing ones anymore."),
    Item("Tinderbox",          18, "common",   "material",   "Flint and steel. Never leave town without one.",
         [], effect=None,
         lore="The flint is worn almost smooth. It belonged to someone who camped a great many nights alone."),
    Item("Bandages",           20, "common",   "consumable", "Clean linen wraps. Restores 20 HP out of combat.",
         [], effect="heal_20",
         lore="Restores 20 HP. Washed and pressed by hands that had done this many times before."),
    Item("Grappling Hook",     35, "uncommon", "material",   "Thrown iron hook with rope. Dungeoneers swear by it.",
         [], effect=None,
         lore="One of the tines was replaced. The original broke inside the Dripping Grotto. The man it belonged to did not."),
    Item("Lock Picks",         55, "uncommon", "material",   "A set of slender picks. Illegal in Greyspire.",
         [], effect=None,
         lore="Illegal in Greyspire. Made by a locksmith who understood that the best advertisement is a lock that opens."),
    Item("Lantern",            40, "uncommon", "consumable", "A hooded lantern. Reveals the unseen.",
         [], effect="torch",
         lore="Lights the way. The previous owner painted the hood black. They did not want to be seen looking."),
]

# ── HUNT YIELDS (meat, pelts, bones — from hunting minigame) ─────────────────
HUNT_ITEMS = [
    Item("Small Game Meat",  8,  "common",   "consumable", "Squirrel or fox, roasted on a stick. Restores 20 HP.",
         [], effect="heal_20",
         lore="Restores 20 HP. The kind of meal that keeps you moving. Nobody cooks it for the flavour."),
    Item("Dried Meat",       12, "common",   "consumable", "Smoked trail meat. Hearty road fare. Restores 35 HP.",
         [], effect="heal_35",
         lore="Restores 35 HP. Smoked over a fire that burned for three days. The hunter had a long wait ahead."),
    Item("Venison",          20, "uncommon", "consumable", "Fresh deer, dressed in the field. Restores 40 HP.",
         [], effect="heal_40",
         lore="Restores 40 HP. The deer was drinking from the stream near the old shrine when it was taken."),
    Item("Bear Meat",        25, "uncommon", "consumable", "Dense, rich meat. A full belly. Restores 40 HP.",
         [], effect="heal_40",
         lore="Restores 40 HP. The bear had been watching the camp for two nights before the hunter acted."),
    Item("Squirrel Pelt",    10, "common",   "material",   "Soft and small. Furriers pay little for it.",
         [],
         lore="Unremarkable. The kind of pelt every hunter keeps because throwing it away feels wasteful."),
    Item("Fox Pelt",         28, "common",   "material",   "Russet fur. Decent trade value with leatherworkers.",
         [],
         lore="The fox was known in the village near Ashenvale. Nobody admitted to being glad it was gone."),
    Item("Deer Pelt",        50, "uncommon", "material",   "Supple hide. Leatherworkers prize it.",
         [],
         lore="A clean kill. The hunter who dressed it knew what they were doing and left nothing behind."),
    Item("Elk Pelt",         80, "uncommon", "material",   "Thick and wide. Fine quality.",
         [],
         lore="Taken during the first frost. The elk had crossed the Ironpeak ridge — nobody hunts up there anymore."),
    Item("Bear Pelt",       130, "rare",     "material",   "Immense and dense. Worth real coin.",
         [],
         lore="The bear left three scars on the hunter before it fell. She keeps the pelt. She sold the claws."),
    Item("Bone Tusk",        35, "common",   "material",   "Curved bone from large game. Alchemists use these.",
         [],
         lore="The tusk was already cracked when the boar charged. It finished the job on the hunter's shield."),
    Item("Bear Claw",        45, "uncommon", "material",   "A large, hooked claw. Curio merchants pay well.",
         [],
         lore="Still sharp. The bear used it on a Greyspire soldier once. There is a record of the incident."),
    Item("Mystical Fang",   220, "rare",     "material",   "A fang from no natural creature. Glows faintly.",
         [],
         lore="The creature it came from had no name. It is in the journal of the hunter who killed it, under 'do not return here'."),
]

# ── GRIMTOTEMS (purchased from Librarian/Mage — learned via reading) ─────────
# Basic (10–40g), Mid (60–150g), Advanced (200–400g)
GRIMTOTEM_ITEMS = [
    Item("Grimtotem of Frost",    20,  "common",   "grimtotem", "A slim tome bound in blue thread. Frost Bolt.",
         [], spell_name="Frost Bolt",
         lore="Teaches: Frost Bolt. The pages are cold to the touch even in summer. The previous reader left no notes."),
    Item("Grimtotem of Shock",    15,  "common",   "grimtotem", "A singed pamphlet. Crackles faintly. Shock.",
         [], spell_name="Shock",
         lore="Teaches: Shock. Water-damaged. The author survived writing it, apparently, but not by much."),
    Item("Grimtotem of Fire",     70,  "uncommon", "grimtotem", "A heat-warped tome. Fireball.",
         [], spell_name="Fireball",
         lore="Teaches: Fireball. The binding is fused. Someone read this in a hurry, in a place with no exits."),
    Item("Grimtotem of Mending",  90,  "uncommon", "grimtotem", "Soft covers, gentle script. Healing Word.",
         [], spell_name="Healing Word",
         lore="Teaches: Healing Word. Written by a field medic who believed words did the work. She was right."),
    Item("Grimtotem of Shadows", 110,  "uncommon", "grimtotem", "Dark ink on dark pages. Shadow Step.",
         [], spell_name="Shadow Step",
         lore="Teaches: Shadow Step. The text is only legible in low light. This was intentional."),
    Item("Grimtotem of Draining",130,  "uncommon", "grimtotem", "Smells of old blood. Drain Life.",
         [], spell_name="Drain Life",
         lore="Teaches: Drain Life. Confiscated from a necromancer near Greyspire. She said she found it, not wrote it."),
    Item("Grimtotem of the Arc", 280,  "rare",     "grimtotem", "Scorched. Bindings fused. Lightning Arc.",
         [], spell_name="Lightning Arc",
         lore="Teaches: Lightning Arc. The last page is missing. Whatever conclusion the author reached, they kept it."),
    Item("Grimtotem of Rending", 380,  "rare",     "grimtotem", "Black pages. No author listed. Soul Rend.",
         [], spell_name="Soul Rend",
         lore="Teaches: Soul Rend. No author, no date, no origin. The ink is not ink."),
]

# ── FORAGE FINDS (from Bushcraft — quality scales with Survival) ──────────────
FORAGE_ITEMS = [
    Item("Unknown Berries",  3,  "common",   "consumable", "Unidentified wild berries. Eat at your own risk.",
         [], effect="berries_unknown",
         lore="Risk: poison (20%). The traveller who catalogued these used herself as the test. Her notes end mid-sentence."),
    Item("Blueberries",      8,  "common",   "consumable", "Wild blueberries. Fresh and nutritious. Restores 20 HP.",
         [], effect="heal_20",
         lore="Restores 20 HP. They grow near the old standing stones east of Ashenvale. Nobody plants them there."),
    Item("Wild Mushrooms",   10, "common",   "consumable", "Earthy forest mushrooms. Restores 15 HP and 10 Mana.",
         [], effect="mushroom_wild",
         lore="Restores 15 HP, 10 Mana. The cluster grew in a ring. The grass inside the ring was a different colour."),
    Item("Nightshade",       30, "uncommon", "material",   "Identified: highly toxic. Do NOT eat. Alchemists pay well.",
         [],
         lore="Lethal if consumed. The plant grows where something died. It prefers to grow where many things died."),
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
