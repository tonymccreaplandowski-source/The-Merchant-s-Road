"""
Dungeon generation system.

Produces a branching room graph (tree) for explorable cave/castle locations.
Room 0 is always the entry. The boss room is always the deepest main-branch room.
Side branches contain non-combat rooms: traps, puzzles, secrets, dead ends.

Adjustable constants:
  DUNGEON_SIZE_RANGE  — (min, max) total rooms per dungeon run
"""

import random
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Optional


# ── Tuning constants ──────────────────────────────────────────────────────────

DUNGEON_SIZE_RANGE = (5, 8)   # total rooms including entry + boss

# Room type weights per event_type — adjust values to shift dungeon composition
ROOM_TYPE_WEIGHTS: Dict[str, Dict[str, int]] = {
    "cave": {
        "combat":   30,
        "trap":     20,
        "puzzle":   22,
        "secret":   18,
        "dead_end": 10,
    },
    "castle": {
        "combat":   28,
        "trap":     25,
        "puzzle":   20,
        "secret":   15,
        "dead_end": 12,
    },
}

PUZZLE_TYPES  = ["riddle", "reveal", "maze", "sequence"]
TRAP_TYPES    = ["spike", "gas", "floor", "tripwire"]

# Dead end flavor tags — matched to atmospheric descriptions in ui/road.py
DEAD_END_TAGS = [
    "child_bedroom",
    "lovers_chamber",
    "weapons_cache",
    "flooded_cellar",
    "dark_shrine",
    "set_dining_hall",
]


# ── Room dataclass ─────────────────────────────────────────────────────────────

@dataclass
class DungeonRoom:
    room_id:        int
    room_type:      str                          # entry | combat | trap | puzzle | secret | dead_end | boss
    exits:          List[Tuple[str, int]] = field(default_factory=list)  # [(label, dest_room_id), ...]
    visited:        bool                  = False
    loot_bias:      str                   = "common"

    # combat / boss
    is_boss:        bool                  = False

    # dead end
    dead_end_tag:   str                   = ""

    # puzzle
    puzzle_type:    str                   = ""    # riddle | reveal | maze | sequence
    puzzle_timed:   bool                  = False  # True = time limit applies
    puzzle_gating:  bool                  = False  # True = only path to boss branch
    solved:         bool                  = False  # True once puzzle is successfully completed

    # trap
    trap_type:      str                   = ""    # spike | gas | floor | tripwire


# ── Internal helpers ──────────────────────────────────────────────────────────

def _pick_room_type(biome: str, used: Dict[str, int]) -> str:
    """
    Pick a side-branch room type using biome weights,
    with a soft penalty for types already appearing several times.
    """
    weights = dict(ROOM_TYPE_WEIGHTS.get(biome, ROOM_TYPE_WEIGHTS["cave"]))
    for rtype, count in used.items():
        if rtype in weights:
            weights[rtype] = max(1, weights[rtype] - count * 12)
    types = list(weights.keys())
    wts   = [weights[t] for t in types]
    return random.choices(types, weights=wts, k=1)[0]


def _sample_label(pool: List[str], used_labels: List[str]) -> str:
    """Pick a label from the pool, avoiding repeats where possible."""
    unused = [l for l in pool if l not in used_labels]
    if unused:
        return random.choice(unused)
    return random.choice(pool)  # fallback if pool is exhausted


# ── Public API ────────────────────────────────────────────────────────────────

def generate_dungeon(event) -> Dict[int, DungeonRoom]:
    """
    Build a room graph for the given RoadEvent.

    Returns:
        dict mapping room_id (int) → DungeonRoom
        Room 0 is always the entry point.
        The boss room has room.is_boss == True.
    """
    total      = random.randint(*DUNGEON_SIZE_RANGE)
    biome      = event.event_type   # "cave" | "castle"
    nav_pool   = list(event.nav_labels) if event.nav_labels else ["Deeper passage"]
    loot_bias  = event.loot_bias

    rooms:       Dict[int, DungeonRoom] = {}
    used_types:  Dict[str, int]         = {}
    used_labels: List[str]              = []
    next_id      = 0

    def new_id() -> int:
        nonlocal next_id
        _id = next_id
        next_id += 1
        return _id

    # ── Entry room ────────────────────────────────────────────────────────────
    entry_id = new_id()
    rooms[entry_id] = DungeonRoom(room_id=entry_id, room_type="entry", loot_bias=loot_bias)

    # ── Main branch: 1–2 combat rooms → boss ─────────────────────────────────
    # Reserve at least 2 slots for side branches from the total
    main_combat_count = max(1, min(2, total - 3))
    main_chain        = [entry_id]

    for i in range(main_combat_count):
        rid = new_id()
        is_last_before_boss = (i == main_combat_count - 1)

        if is_last_before_boss and random.random() < 0.30:
            # 30% chance: a puzzle room gates the boss branch
            ptype = random.choice(PUZZLE_TYPES)
            timed = random.random() < 0.5
            rooms[rid] = DungeonRoom(
                room_id=rid, room_type="puzzle",
                puzzle_type=ptype, puzzle_timed=timed, puzzle_gating=True,
                loot_bias=loot_bias,
            )
            used_types["puzzle"] = used_types.get("puzzle", 0) + 1
        else:
            rooms[rid] = DungeonRoom(room_id=rid, room_type="combat", loot_bias=loot_bias)
            used_types["combat"] = used_types.get("combat", 0) + 1

        main_chain.append(rid)

    # ── Boss room (always final on main branch) ───────────────────────────────
    boss_id = new_id()
    rooms[boss_id] = DungeonRoom(
        room_id=boss_id, room_type="boss", is_boss=True, loot_bias="rare",
    )
    main_chain.append(boss_id)

    # Wire up main chain exits
    for i, rid in enumerate(main_chain[:-1]):
        dest  = main_chain[i + 1]
        label = _sample_label(nav_pool, used_labels)
        used_labels.append(label)
        rooms[rid].exits.append((label, dest))

    # ── Side branches: fill remaining room budget ─────────────────────────────
    side_slots = total - len(rooms)
    # Any main-chain room except the boss can sprout a side branch
    branch_parents = main_chain[:-1]

    for _ in range(max(0, side_slots)):
        parent_id = random.choice(branch_parents)
        sid       = new_id()
        rtype     = _pick_room_type(biome, used_types)

        kwargs: dict = dict(room_id=sid, room_type=rtype, loot_bias=loot_bias)

        if rtype == "dead_end":
            kwargs["dead_end_tag"] = random.choice(DEAD_END_TAGS)
        elif rtype == "puzzle":
            kwargs.update(
                puzzle_type=random.choice(PUZZLE_TYPES),
                puzzle_timed=random.random() < 0.5,
                puzzle_gating=False,
            )
        elif rtype == "trap":
            kwargs["trap_type"] = random.choice(TRAP_TYPES)
        # secret and combat need no extra fields beyond the defaults

        rooms[sid] = DungeonRoom(**kwargs)
        used_types[rtype] = used_types.get(rtype, 0) + 1

        label = _sample_label(nav_pool, used_labels)
        used_labels.append(label)
        rooms[parent_id].exits.append((label, sid))
        # Dead ends and secrets have no onward exits — player backtracks

    return rooms
