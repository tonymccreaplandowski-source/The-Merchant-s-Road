"""
Special road events — caves and castles.
These are explorable locations the player can choose to enter or pass by.
Each has its own encounter pool and loot bias.
"""

import random
import copy
from dataclasses import dataclass, field
from typing import List

from data.enemies import ENEMY_TEMPLATES, spawn_enemy, Enemy


@dataclass
class RoadEvent:
    event_type: str       # "cave" | "castle"
    name: str
    description: str
    flavour: str          # one-line atmospheric description when spotted on road
    enemy_biome: str      # biome key used to pull enemies from
    enemy_count: int      # how many fights inside (resolved at spawn from count_range)
    loot_bias: str        # loot quality bias inside
    lore_text: str = ""   # two-sentence lore entry added to Journal on clear
    count_range: tuple = (1, 4)   # min/max enemy count — resolved each time the event spawns


# ── Event pool ────────────────────────────────────────────────────────────────

CAVE_EVENTS = [
    RoadEvent(
        event_type="cave",
        name="The Hollow Den",
        description="A narrow cave mouth cut into the rock face. Scratch marks ring the entrance.",
        flavour="You spot a dark cave entrance to the side of the road.",
        enemy_biome="cave",
        enemy_count=2,
        loot_bias="uncommon",
        count_range=(1, 3),
        lore_text=(
            "The Hollow Den was once a waystation for hunters who worked this stretch of road. "
            "No one is sure when the creatures moved in, or what happened to the last party who tried to reclaim it."
        ),
    ),
    RoadEvent(
        event_type="cave",
        name="The Dripping Grotto",
        description="Water seeps through the ceiling. Something moves in the dark.",
        flavour="A grotto yawns open in the hillside — water trickles from inside.",
        enemy_biome="cave",
        enemy_count=3,
        loot_bias="rare",
        count_range=(2, 4),
        lore_text=(
            "The Dripping Grotto connects to an underground river that hasn't been mapped. "
            "Travellers who camped near the entrance reported hearing voices below, distinct from the water."
        ),
    ),
    RoadEvent(
        event_type="cave",
        name="The Smuggler's Cache",
        description="Crude shelves line the walls. Someone was here recently.",
        flavour="You notice a hidden cave, half-concealed by brush.",
        enemy_biome="cave",
        enemy_count=2,
        loot_bias="uncommon",
        count_range=(1, 3),
        lore_text=(
            "The Cache was used by a now-defunct caravan guild to move goods past the city toll roads. "
            "The guild's ledger, if it still exists, would name every official who looked the other way."
        ),
    ),
]

CASTLE_EVENTS = [
    RoadEvent(
        event_type="castle",
        name="The Broken Keep",
        description=(
            "A crumbling stone keep looms above the treeline. "
            "Its gate hangs open. Something stirs within."
        ),
        flavour="The silhouette of a ruined keep rises above the road ahead.",
        enemy_biome="castle",
        enemy_count=2,
        loot_bias="rare",
        count_range=(2, 4),
        lore_text=(
            "The Broken Keep was abandoned during a siege that nobody won, according to the only surviving account. "
            "The attacking force, the defending garrison, and the chronicler who wrote the account all vanished within the same week."
        ),
    ),
    RoadEvent(
        event_type="castle",
        name="The Forsaken Garrison",
        description=(
            "Banners hang in tatters. The courtyard is littered with old armour. "
            "Not all of it is empty."
        ),
        flavour="You pass what looks like an abandoned military garrison.",
        enemy_biome="castle",
        enemy_count=3,
        loot_bias="rare",
        count_range=(2, 5),
        lore_text=(
            "The garrison was ordered to hold position by a commander who never returned with new orders. "
            "The soldiers held. Long past reason. Long past life, some say."
        ),
    ),
    RoadEvent(
        event_type="castle",
        name="The Merchant Lord's Folly",
        description=(
            "A grand castle, half-built and long abandoned. "
            "Rumour says its owner fled owing debts to every city on the road."
        ),
        flavour="An unfinished castle stands alone on a hill — oddly grand, oddly silent.",
        enemy_biome="castle",
        enemy_count=2,
        loot_bias="rare",
        count_range=(1, 3),
        lore_text=(
            "The Merchant Lord commissioned the castle to demonstrate his wealth, a miscalculation that cost him exactly that. "
            "Builders were still working the eastern tower when the bailiffs arrived — they never finished, and neither did he."
        ),
    ),
]


def _resolve_event(event: RoadEvent) -> RoadEvent:
    """Return a shallow copy of the event with enemy_count resolved from count_range."""
    resolved = copy.copy(event)
    resolved.enemy_count = random.randint(*event.count_range)
    return resolved


def random_cave() -> RoadEvent:
    return _resolve_event(random.choice(CAVE_EVENTS))


def random_castle() -> RoadEvent:
    return _resolve_event(random.choice(CASTLE_EVENTS))


def get_event_enemies(event: RoadEvent) -> List[Enemy]:
    """Return the list of enemies the player will face inside this location."""
    enemies = []
    for _ in range(event.enemy_count):
        valid = [t for t in ENEMY_TEMPLATES if event.enemy_biome in t["biomes"]]
        if not valid:
            valid = ENEMY_TEMPLATES
        enemies.append(spawn_enemy(random.choice(valid)))
    return enemies
