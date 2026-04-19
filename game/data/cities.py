"""
City definitions and biome pricing system.

World layout (west → east):
  [Al-Rimal] ── desert ── [Waldheim] ── mountain ── [Las Cumbres]

Pricing logic:
  Abundant items  →  merchant pays 70% of base value  (flooded with supply)
  Scarce items    →  merchant pays 135% of base value (desperate for stock)
  Normal items    →  merchant pays 100% of base value

This creates real arbitrage opportunity: buy from a city with abundance,
sell to a city where it's scarce.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class City:
    key: str
    name: str
    biome: str
    position: int
    description: str
    abundant: List[str]
    scarce: List[str]
    road_biome_east: Optional[str]

    def price_modifier(self, item_name: str) -> float:
        name_lower = item_name.lower()
        for tag in self.abundant:
            if tag in name_lower:
                return 0.70
        for tag in self.scarce:
            if tag in name_lower:
                return 1.35
        return 1.00

    def modifier_label(self, item_name: str) -> str:
        mod = self.price_modifier(item_name)
        if mod < 1.0:
            return "abundant"
        if mod > 1.0:
            return "scarce"
        return "normal"


CITIES = {
    "dusthaven": City(
        key="dusthaven",
        name="Dar-Nakhil",
        biome="desert",
        position=0,
        description=(
            "A sun-scorched trading post baked into the western sands. "
            "Caravans pass through leaving silk and spice. "
            "Iron and fur are rare commodities here."
        ),
        abundant=["cloth", "silk", "fruit", "spice", "copper"],
        scarce=["iron", "ore", "fur", "pelt", "wood", "herb", "mushroom", "shield", "sword", "dagger"],
        road_biome_east="desert",
    ),
    "ashenvale": City(
        key="ashenvale",
        name="Rabenmark",
        biome="forest",
        position=1,
        description=(
            "A quiet forest settlement where hunters and herbalists trade freely. "
            "Wood, fur, and herbs are plentiful. "
            "Desert goods and iron fetch a premium here."
        ),
        abundant=["wood", "herb", "fur", "pelt", "leather", "mushroom", "wolf", "tooth"],
        scarce=["silk", "spice", "fruit", "iron", "ore", "gem", "ruby", "amulet", "relic", "moonstone"],
        road_biome_east="mountain",
    ),
    "ironpeak": City(
        key="ironpeak",
        name="Greyspire",
        biome="mountain",
        position=2,
        description=(
            "A fortified mountain stronghold built above rich ore veins. "
            "Iron, stone, and steel are in abundance. "
            "Cloth, food, and forest goods are hard to come by."
        ),
        abundant=["iron", "ore", "copper", "stone", "shield", "sword", "dagger", "blade"],
        scarce=["cloth", "silk", "fruit", "herb", "mushroom", "pelt", "fur", "spice", "tooth"],
        road_biome_east=None,
    ),
}

CITY_ORDER = ["dusthaven", "ashenvale", "ironpeak"]


def get_city(key: str) -> City:
    return CITIES[key.lower()]


def get_road_biome(from_key: str, to_key: str) -> str:
    from_city = CITIES[from_key]
    to_city   = CITIES[to_key]
    if from_city.position < to_city.position:
        return from_city.road_biome_east or "forest"
    else:
        return to_city.road_biome_east or "forest"


def get_adjacent_city_keys(current_key: str) -> List[str]:
    pos = CITIES[current_key].position
    return [k for k, c in CITIES.items() if abs(c.position - pos) == 1]