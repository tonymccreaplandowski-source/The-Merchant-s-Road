"""
Special road events — caves and castles.
These are explorable locations the player can choose to enter or pass by.
Each has its own encounter pool, loot bias, boss, and navigation labels.
"""

import random
import copy
from dataclasses import dataclass, field
from typing import List, Optional

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
    # ── Dungeon overhaul fields ───────────────────────────────────────────────
    boss_name: str = ""           # displayed name of the final room boss
    boss_hp_mult: float = 1.6     # HP multiplier applied to a standard biome enemy
    boss_dmg_mult: float = 1.35   # damage multiplier applied to the boss
    boss_drop_name: str = ""      # name of the unique item dropped on boss kill
    nav_labels: List[str] = field(default_factory=list)  # directional exit label pool


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
        boss_name="The Den Warden",
        boss_hp_mult=1.7,
        boss_dmg_mult=1.4,
        boss_drop_name="Warden's Hide Wraps",
        nav_labels=["North passage", "Side chamber", "Deeper tunnel", "Down the slope",
                    "Into the dark", "Low crawlway", "Eastern hollow"],
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
        boss_name="The Grotto Abomination",
        boss_hp_mult=1.8,
        boss_dmg_mult=1.4,
        boss_drop_name="Tideborn Pendant",
        nav_labels=["Follow the water", "Down the carved steps", "Wet passage north",
                    "Narrow fissure east", "Into the deep chamber", "Submerged alcove"],
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
        boss_name="The Cache Master",
        boss_hp_mult=1.6,
        boss_dmg_mult=1.3,
        boss_drop_name="Shadow Fingers",
        nav_labels=["Hidden back room", "Behind the shelving", "Trapdoor passage",
                    "Side tunnel west", "Concealed alcove", "Lower storage"],
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
        boss_name="The Castellan",
        boss_hp_mult=1.8,
        boss_dmg_mult=1.45,
        boss_drop_name="Castellan's Vow",
        nav_labels=["Up the gatehouse stairs", "Through the inner ward", "West tower",
                    "Down to the undercroft", "The great hall", "Collapsed east wing",
                    "Armory passage"],
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
        boss_name="The Forsaken Captain",
        boss_hp_mult=1.9,
        boss_dmg_mult=1.5,
        boss_drop_name="Captain's Verdict",
        nav_labels=["Barracks corridor", "Commander's wing", "The drill yard",
                    "Down to the cells", "Chapel passage", "North watchtower",
                    "Supply depot"],
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
        boss_name="The Vault Sentinel",
        boss_hp_mult=1.7,
        boss_dmg_mult=1.35,
        boss_drop_name="Folly Signet",
        nav_labels=["Through the grand entrance", "The unfinished east tower",
                    "Counting room passage", "Down to the vault", "Servants' corridor",
                    "Half-built gallery"],
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


def spawn_boss(event: RoadEvent) -> Enemy:
    """
    Spawn the boss enemy for this location.
    Draws the strongest valid biome enemy and applies the event's HP/damage multipliers.
    """
    valid = [t for t in ENEMY_TEMPLATES if event.enemy_biome in t["biomes"]]
    if not valid:
        valid = ENEMY_TEMPLATES
    # Pick the highest-HP-ceiling template as the base for the boss
    template = max(valid, key=lambda t: t["hp_range"][1])
    boss = spawn_enemy(template)
    boss.name         = event.boss_name
    boss.max_hp       = max(1, int(boss.max_hp * event.boss_hp_mult))
    boss.hp           = boss.max_hp
    boss.combat_skill = max(1, int(boss.combat_skill * event.boss_dmg_mult))
    return boss
