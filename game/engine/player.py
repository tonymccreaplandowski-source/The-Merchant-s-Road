"""
Player character sheet, skills, equipment, inventory, mana, and progression.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from data.items import Item

SKILLS = [
    "Merchantilism",
    "Speechcraft",
    "Martial",
    "Magic",
    "Stealth",
    "Survival",
    "Dungeoneering",
]

SKILL_DESCRIPTIONS = {
    "Merchantilism":  "Affects buy/sell prices and negotiation outcomes.",
    "Speechcraft":    "Opens dialogue options and improves NPC reactions.",
    "Martial":        "Increases combat damage and hit chance.",
    "Magic":          "Unlocks spells. Determines max mana pool.",
    "Stealth":        "Improves flee chance and powers Snipe attacks.",
    "Survival":       "Reduces road encounters. Boosts initiative roll.",
    "Dungeoneering":  "Improves cave/castle exploration and trap detection.",
}

STARTING_POINTS  = 210
MIN_SKILL        = 5
MAX_SKILL        = 100
MAX_INVENTORY    = 12     # hard cap on carried items


@dataclass
class Player:
    name: str
    skills: Dict[str, int]          = field(default_factory=dict)
    hp: int                         = 100
    max_hp: int                     = 100
    gold: int                       = 50
    inventory: List[Item]           = field(default_factory=list)

    # Equipment slots
    equipped: Dict[str, Optional[Item]] = field(default_factory=lambda: {
        "weapon":   None,
        "armor":    None,
        "ring":     None,
        "necklace": None,
    })

    # Mana
    mana: int                       = 0   # set after creation based on Magic skill
    mana_discount: int              = 0   # temporary discount from Channel move

    # Travel state
    current_city: Optional[str]     = "ashenvale"
    on_road: bool                   = False
    road_destination: Optional[str] = None
    road_origin: Optional[str]      = None
    road_steps: int                 = 0
    road_total: int                 = 0
    road_biome: str                 = "forest"
    road_camps: int                 = 0   # camps used this road segment (max 2)

    # Time
    days_elapsed: int               = 0

    # ── Skill access ──────────────────────────────────────────────────────
    def skill(self, name: str) -> int:
        """Return base skill + any bonuses from equipped accessories."""
        base   = self.skills.get(name, 0)
        bonus  = 0
        for slot in ("ring", "necklace"):
            item = self.equipped.get(slot)
            if item and item.stat_bonuses:
                bonus += item.stat_bonuses.get(name, 0)
        return min(MAX_SKILL, base + bonus)

    def base_skill(self, name: str) -> int:
        return self.skills.get(name, 0)

    # ── Max mana ─────────────────────────────────────────────────────────
    @property
    def max_mana(self) -> int:
        return self.skill("Magic") * 2

    # ── Defense ──────────────────────────────────────────────────────────
    @property
    def defense(self) -> int:
        """Total defense: small martial base + equipped armour value."""
        base       = max(2, self.skill("Martial") // 8)
        armor_item = self.equipped.get("armor")
        armor_val  = armor_item.armor_value if armor_item else 0
        return base + armor_val

    # ── Available combat moves ────────────────────────────────────────────
    def combat_moves(self) -> list:
        from data.weapons import get_moves_for_weapon
        weapon = self.equipped.get("weapon")
        wtype  = weapon.weapon_type if weapon else None
        return get_moves_for_weapon(wtype)

    # ── HP management ────────────────────────────────────────────────────
    def heal(self, amount: int):
        self.hp = min(self.max_hp, self.hp + amount)

    def take_damage(self, amount: int):
        self.hp = max(0, self.hp - amount)

    def is_alive(self) -> bool:
        return self.hp > 0

    # ── Mana management ───────────────────────────────────────────────────
    def restore_mana(self, amount: int = None):
        if amount is None:
            self.mana = self.max_mana
        else:
            self.mana = min(self.max_mana, self.mana + amount)

    def spend_mana(self, amount: int) -> bool:
        """Returns False if not enough mana."""
        cost = max(0, amount - self.mana_discount)
        self.mana_discount = 0
        if self.mana < cost:
            return False
        self.mana -= cost
        return True

    # ── Inventory ─────────────────────────────────────────────────────────
    def can_carry(self) -> bool:
        return len(self.inventory) < MAX_INVENTORY

    def add_item(self, item: Item) -> bool:
        if not self.can_carry():
            return False
        self.inventory.append(item)
        return True

    def remove_item(self, item: Item):
        self.inventory.remove(item)

    def inventory_value(self) -> int:
        return sum(i.base_value for i in self.inventory)

    # ── Equipment ─────────────────────────────────────────────────────────
    def equip(self, item: Item) -> Optional[Item]:
        """
        Equip an item from inventory. Returns the previously equipped item
        (which goes back to inventory), or None.
        Handles cursed item effects.
        """
        slot = _item_slot(item)
        if slot is None:
            return None

        # Warn on cursed but allow equip
        prev = self.equipped.get(slot)
        self.equipped[slot] = item

        # Apply curse
        if item.cursed and item.curse_effect == "reduce_max_hp":
            self.max_hp = max(20, self.max_hp - 20)
            self.hp     = min(self.hp, self.max_hp)

        return prev

    def unequip(self, slot: str) -> Optional[Item]:
        """Remove and return the item in a slot (goes back to inventory)."""
        item = self.equipped.get(slot)
        if item:
            self.equipped[slot] = None
            # Reverse curse
            if item.cursed and item.curse_effect == "reduce_max_hp":
                self.max_hp = min(100, self.max_hp + 20)
        return item

    # ── Skill training ────────────────────────────────────────────────────
    def train(self, skill_name: str) -> bool:
        current = self.skills.get(skill_name, 0)
        if current >= MAX_SKILL:
            return False
        self.skills[skill_name] = current + 1
        if skill_name == "Magic":
            self.restore_mana()   # mana pool expands with Magic skill
        return True


def _item_slot(item: Item) -> Optional[str]:
    """Map item_type to equipment slot key."""
    return {
        "weapon":   "weapon",
        "armor":    "armor",
        "ring":     "ring",
        "necklace": "necklace",
    }.get(item.item_type)


def create_player(name: str, skill_allocations: Dict[str, int]) -> Player:
    total = sum(skill_allocations.values())
    if total > STARTING_POINTS:
        raise ValueError(f"Skill total {total} exceeds {STARTING_POINTS}.")
    p = Player(name=name, skills=dict(skill_allocations))
    p.mana = p.max_mana   # initialise mana from Magic skill
    return p
