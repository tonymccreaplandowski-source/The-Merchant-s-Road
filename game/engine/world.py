"""
World map and travel engine.

Linear map (west → east):
  [Dar-Nakhil] ── desert ── [Rabenmark] ── mountain ── [Greyspire]

Travel is broken into steps. Each step has a chance of either a combat
encounter or a special event (cave / castle). The Survival skill reduces
overall encounter frequency.

take_road_step returns a 3-tuple:
  (arrived: bool, enemy: Enemy|None, event: RoadEvent|None)
"""

import random
from typing import Optional, Tuple

from data.cities  import CITIES, CITY_ORDER, get_road_biome, get_adjacent_city_keys
from data.enemies import get_enemy_for_biome, Enemy
from engine.player import Player
from engine.events import RoadEvent, random_cave, random_castle

ROAD_STEPS            = 6     # steps to cross one road segment
BASE_ENCOUNTER_CHANCE = 0.35  # base encounter rate per road step
EVENT_CHANCE          = 0.65  # of any encounter, this portion becomes a special location
MAP_BONUS_CHANCE      = 0.15  # additional event chance added when Adventurer's Map is active


def get_encounter_chance(player: Player) -> float:
    """Survival skill reduces encounter frequency (max −0.40 at skill 100)."""
    reduction = player.skill("Survival") / 250.0
    return max(0.08, BASE_ENCOUNTER_CHANCE - reduction)


def get_event_chance(player: Player) -> float:
    """How much of any encounter roll becomes a special location vs a straight mob fight."""
    bonus = MAP_BONUS_CHANCE if player.map_bonus else 0.0
    return min(0.90, EVENT_CHANCE + bonus)


def start_travel(player: Player, destination_key: str) -> None:
    """Begin travel toward destination. Mutates player travel state."""
    origin = player.current_city
    biome  = get_road_biome(origin, destination_key)

    player.road_origin      = origin
    player.road_destination = destination_key
    player.road_biome       = biome
    player.road_steps       = 0
    player.road_total       = ROAD_STEPS
    player.road_camps       = 0   # reset camp counter for new road segment
    player.on_road          = True
    player.current_city     = None


def take_road_step(
    player: Player,
) -> Tuple[bool, Optional[Enemy], Optional[RoadEvent]]:
    """
    Advance one step along the road. Increments days_elapsed by 1.

    Returns:
      (True,  None,  None)   — player has arrived at destination
      (False, Enemy, None)   — combat encounter
      (False, None,  Event)  — special event (cave / castle)
      (False, None,  None)   — uneventful step
    """
    player.road_steps    += 1
    player.days_elapsed  += 1   # each forward step costs one day

    # ── Arrival ──────────────────────────────────────────────────────────────
    if player.road_steps >= player.road_total:
        player.current_city     = player.road_destination
        player.on_road          = False
        player.road_destination = None
        player.road_origin      = None
        player.road_steps       = 0
        player.road_total       = 0
        player.road_camps       = 0
        return True, None, None

    # ── Encounter roll ────────────────────────────────────────────────────────
    if random.random() < get_encounter_chance(player):

        # Decide: special event (cave/castle) or straight mob fight?
        evt_chance = get_event_chance(player)
        if random.random() < evt_chance:
            # Map bonus consumed after contributing to this roll
            player.map_bonus = False
            event = random_cave() if random.random() < 0.5 else random_castle()
            return False, None, event
        else:
            enemy = get_enemy_for_biome(player.road_biome)
            return False, enemy, None

    return False, None, None


def abort_travel(player: Player) -> None:
    """Cancel travel and return the player to their origin city."""
    player.current_city     = player.road_origin or "ashenvale"
    player.on_road          = False
    player.road_destination = None
    player.road_origin      = None
    player.road_steps       = 0
    player.road_total       = 0
    player.road_camps       = 0
