"""
Road, exploration, wilderness, camping, hunting, and game-over screens.
"""

import sys
import time
import random

from engine.player   import Player
from engine.loot     import generate_loot, generate_loot_min_rarity
from engine.items_use import FOOD_HUNGER_RESTORE
from engine.events   import get_event_enemies, spawn_boss
from engine.dungeon  import generate_dungeon, DungeonRoom
from engine.world    import take_road_step, abort_travel
from data.cities     import CITIES
from data.items      import ITEM_LOOKUP
from data.road_flavor import road_flavor_line
from ui.display      import (
    C, RARITY_COLOR,
    clear, pause, hr, section, title_screen, prompt_choice,
    show_world_map, show_character_sheet,
    rarity_tag, typewrite, beep, play_melody,
    start_ambient_loop,
    play_location_music, stop_location_music,
)
from data.enemies        import ENEMY_TEMPLATES, spawn_enemy
from ui.combat_loop      import run_combat, loot_screen
from ui.equipment        import bag_screen
from ui.dungeon_puzzles  import run_puzzle


def _format_time(days: int) -> str:
    """Convert a raw day count into a human-readable duration string."""
    if days <= 0:
        return "less than a day"
    years  = days // 365
    months = (days % 365) // 30
    rem    = days % 30
    parts  = []
    if years:
        parts.append("{} year{}".format(years, "s" if years > 1 else ""))
    if months:
        parts.append("{} month{}".format(months, "s" if months > 1 else ""))
    if rem or not parts:
        parts.append("{} day{}".format(rem, "s" if rem > 1 else ""))
    return ", ".join(parts)


# ── Exploration (caves & castles) ─────────────────────────────────────────────

# Dead-end room atmospheric descriptions — indexed by dead_end_tag
_DEAD_END_FLAVOR = {
    "child_bedroom": (
        "A small room. A child's straw mattress in the corner, flattened but intact. "
        "A wooden toy soldier leans against the wall, missing one arm. "
        "Someone hung a bundle of dried flowers above the bed — they are long dead, "
        "but the twine holds. You cannot tell how long ago this was."
    ),
    "lovers_chamber": (
        "Two chairs drawn close to a cold hearth, facing each other. "
        "A cup on each armrest. The fire has not burned here in years. "
        "On the floor between the chairs, a locket — open, both portrait panels scraped clean. "
        "Whoever removed the faces did not want them found together."
    ),
    "weapons_cache": (
        "Iron racks line the walls, most of them empty. Three broken blades remain, "
        "too shattered to be worth salvaging. A dark stain on the floor near the door "
        "is old enough to have turned black. Whatever happened here, it was not a clean fight. "
        "The room smells of rust and old leather and something underneath both."
    ),
    "flooded_cellar": (
        "Water has risen to knee height, black and still. Your torch reflects in it "
        "without distortion — the surface is perfectly calm. Something moves below. "
        "Not fast. Not toward you. But it moves. "
        "You stand there longer than you should before you back away."
    ),
    "dark_shrine": (
        "Symbols cover every surface — carved, not painted. They form no pattern you "
        "recognise, but your eyes keep trying to find one. A bowl in the centre of the room "
        "holds dried residue, dark red. No candles. No offering you understand. "
        "The room is colder than the passage behind you, and silent in a way that feels deliberate."
    ),
    "set_dining_hall": (
        "A long table, fully set. Plates, cups, cutlery — dust-covered but undisturbed. "
        "Twelve chairs. Two are pushed back, as if the occupants stood suddenly. "
        "The food is long gone, but the serving dishes remain in place. "
        "Nobody cleared this table. Nobody came back to clear it."
    ),
}


def _loc_header(event, label: str = ""):
    icon      = "🕳" if event.event_type == "cave" else "🏰"
    loc_color = C.BBLACK if event.event_type == "cave" else C.BYELLOW
    clear()
    print()
    print(f"  {loc_color}{icon}  {event.name.upper()}{C.RESET}")
    if label:
        print(f"  {C.DIM}{label}{C.RESET}")
    print()


def _retreat_check(player: Player, event) -> bool:
    """
    Roll retreat. Returns True = clean escape, False = damaged but escaped.
    Formula: d100 ≤ (Dungeoneering + Stealth + Survival) / 3.
    """
    dung  = player.skill("Dungeoneering")
    stlth = player.skill("Stealth")
    surv  = player.skill("Survival")
    avg   = (dung + stlth + surv) / 3

    # Grappling Hook gives a large boost
    has_hook = any(i.name == "Grappling Hook" for i in player.inventory)
    has_rope = any(i.name == "Rope"           for i in player.inventory)
    bonus    = 0
    if has_hook:
        hook_item = next(i for i in player.inventory if i.name == "Grappling Hook")
        player.remove_item(hook_item)
        bonus = 30
        print(f"\n  {C.BYELLOW}You throw the grappling hook and haul yourself toward the exit.{C.RESET}")
        time.sleep(0.6)
    elif has_rope:
        rope_item = next(i for i in player.inventory if i.name == "Rope")
        player.remove_item(rope_item)
        bonus = 15
        print(f"\n  {C.BYELLOW}You use your rope to navigate the passage quickly.{C.RESET}")
        time.sleep(0.6)

    roll    = random.randint(1, 100)
    success = roll <= min(95, avg + bonus)

    print(f"  {C.DIM}Retreat roll: {roll:.0f} vs. threshold {min(95, avg + bonus):.0f}{C.RESET}")
    time.sleep(0.4)

    if success:
        print(f"\n  {C.BGREEN}You find your way out without incident.{C.RESET}")
        return True
    else:
        # Damage scales with how badly the roll missed
        miss    = roll - (avg + bonus)
        if miss > 30:
            dmg = random.randint(15, 25)
        else:
            dmg = random.randint(5, 12)
        player.take_damage(dmg)
        print(f"\n  {C.BRED}Your retreat is harried. −{dmg} HP.  HP: {player.hp}/{player.max_hp}{C.RESET}")
        return False


def _offer_loot(player: Player, bias: str = "common"):
    """Try a loot roll and offer the player the item."""
    if random.random() < 0.30:
        loot  = generate_loot(bias=bias)
        color = RARITY_COLOR.get(loot.rarity, C.WHITE)
        print(f"\n  Found: {color}{C.BOLD}{loot.name}{C.RESET}  [{rarity_tag(loot.rarity)}]")
        if player.can_carry():
            pick = prompt_choice(["Take it", "Leave it"])
            if pick == 1:
                player.add_item(loot)
                print(f"  {C.BGREEN}Added to inventory.{C.RESET}")
        else:
            print(f"  {C.BRED}Inventory full — left behind.{C.RESET}")
    else:
        print(f"\n  {C.DIM}Nothing of interest in the debris.{C.RESET}")


def _handle_combat_room(player: Player, event, room: DungeonRoom,
                        force_first: bool = False) -> bool:
    """
    Spawn and fight a single combat room enemy.
    Returns True if player won and is still alive, False to abort dungeon.
    """
    valid = [t for t in ENEMY_TEMPLATES if event.enemy_biome in t["biomes"]]
    if not valid:
        valid = ENEMY_TEMPLATES
    enemy = spawn_enemy(random.choice(valid))

    if force_first:
        print(f"  {C.BGREEN}You have the element of surprise.{C.RESET}")
        time.sleep(0.8)

    print(f"  {C.BRED}{enemy.name} stands in your path.{C.RESET}")
    time.sleep(1.0)

    won = run_combat(player, enemy, force_first=force_first)

    if not player.is_alive():
        return False
    if not won:
        return False  # fled
    return True


def _handle_trap_room(player: Player, event, room: DungeonRoom):
    """
    Trap room. Dungeoneering + Survival check. Possible HP loss or status.
    Returns True if player is still alive after the trap.
    """
    trap_flavor = {
        "spike":    ("Pressure plates glitter faintly underfoot. Notches in the walls.",
                     "The floor drops fractionally. Iron spikes punch through."),
        "gas":      ("A faint sweet smell. Residue of old powder on the ground.",
                     "The canister ruptures. A pale gas floods the passage."),
        "floor":    ("The stonework here is too smooth. Too regular.",
                     "The floor gives way without warning. You plunge into a lower chamber."),
        "tripwire": ("A glint of wire at ankle height, nearly invisible in the dark.",
                     "The wire catches your boot. Something heavy swings from the ceiling."),
    }
    detect_flavor, trigger_flavor = trap_flavor.get(
        room.trap_type, ("Something feels wrong here.", "It springs before you can react.")
    )

    _loc_header(event, "— Trap Room")
    typewrite(detect_flavor)
    print()

    dung = player.skill("Dungeoneering")
    surv = player.skill("Survival")
    roll = random.randint(1, 20) + dung // 5 + surv // 10

    # Lantern/torch improve trap detection
    has_lantern = any(i.name == "Lantern"      for i in player.inventory)
    has_torch   = any(i.name == "Torch Bundle" for i in player.inventory)
    if has_lantern:
        roll += 4
    elif has_torch:
        roll += 2

    diff = max(8, 17 - dung // 8)   # scales: high Dungeoneering = lower threshold

    if roll >= diff + 6:
        # Disarm — bonus loot
        print(f"\n  {C.BGREEN}You spot the mechanism, trace its workings, and disarm it cleanly.{C.RESET}")
        print(f"  {C.DIM}Traps often guard something.{C.RESET}")
        time.sleep(0.6)
        _offer_loot(player, bias=event.loot_bias)
    elif roll >= diff:
        # Spotted but still triggered — halved damage
        dmg = random.randint(4, 10)
        player.take_damage(dmg)
        print(f"\n  {C.BYELLOW}You see it but can't fully avoid it. −{dmg} HP.{C.RESET}")
        print(f"  {C.DIM}HP: {player.hp}/{player.max_hp}{C.RESET}")
    else:
        # Full trigger
        print(f"\n  {C.BRED}{trigger_flavor}{C.RESET}")
        time.sleep(0.5)
        dmg = random.randint(10, 25)
        # Gas trap adds poison on bad roll
        if room.trap_type == "gas" and random.random() < 0.45:
            player.road_poison = 2
            print(f"  {C.BRED}The gas burns your lungs. −{dmg} HP and poisoned (2 steps).{C.RESET}")
        else:
            print(f"  {C.BRED}The trap catches you full. −{dmg} HP.{C.RESET}")
        player.take_damage(dmg)
        print(f"  {C.DIM}HP: {player.hp}/{player.max_hp}{C.RESET}")

    time.sleep(0.8)
    pause("Press Enter to continue...")
    return player.is_alive()


def _handle_puzzle_room(player: Player, event, room: DungeonRoom) -> bool:
    """
    Puzzle room. Dispatch to puzzle system.
    Returns True if puzzle was solved (may unlock progress or grant loot).
    """
    _loc_header(event, "— Puzzle Room")

    if room.puzzle_gating:
        print(f"  {C.BYELLOW}The only way forward is sealed. Something must be solved.{C.RESET}")
    else:
        print(f"  {C.DIM}A challenge presents itself. It is not the only way forward.{C.RESET}")
    print()
    time.sleep(0.8)

    solved = run_puzzle(player, room.puzzle_type,
                        timed=room.puzzle_timed, gating=room.puzzle_gating)
    room.solved = solved

    if solved:
        if room.puzzle_gating:
            print(f"\n  {C.BGREEN}The passage opens.{C.RESET}")
        else:
            # Optional puzzle reward
            loot  = generate_loot_min_rarity("uncommon")
            color = RARITY_COLOR.get(loot.rarity, C.WHITE)
            print(f"\n  {C.BGREEN}Well solved.{C.RESET}")
            print(f"  Found: {color}{C.BOLD}{loot.name}{C.RESET}  [{rarity_tag(loot.rarity)}]")
            if player.can_carry():
                pick = prompt_choice(["Take it", "Leave it"])
                if pick == 1:
                    player.add_item(loot)
        # Puzzle lore
        lore_line = f"A puzzle in {event.name} — solved."
        if lore_line not in player.journal:
            player.journal.append(lore_line)
    else:
        if room.puzzle_gating:
            print(f"\n  {C.BRED}The passage stays sealed. You must find another route.{C.RESET}")
        else:
            print(f"\n  {C.DIM}The challenge remains unsolved. You move on.{C.RESET}")

    time.sleep(0.8)
    pause("Press Enter to continue...")
    return solved


def _handle_secret_room(player: Player, event, room: DungeonRoom):
    """
    Secret area. Dungeoneering roll to find it. Pure upside — no penalty.
    """
    _loc_header(event, "— Something Feels Off")
    print(f"  {C.DIM}A draft comes from nowhere. A crack, perhaps. A seam in the stonework.{C.RESET}")
    print()
    time.sleep(0.6)

    dung = player.skill("Dungeoneering")
    # Lantern bonus
    has_lantern = any(i.name == "Lantern"      for i in player.inventory)
    has_torch   = any(i.name == "Torch Bundle" for i in player.inventory)
    light_bonus = 8 if has_lantern else (4 if has_torch else 0)

    # Lock Picks bonus for secret compartments
    has_picks    = any(i.name == "Lock Picks" for i in player.inventory)
    picks_bonus  = 6 if has_picks else 0

    roll = random.randint(1, 20) + dung // 4 + light_bonus + picks_bonus

    if roll >= 18:
        # Full success — rare+ guaranteed
        print(f"  {C.BGREEN}You find it. A hidden alcove, sealed and undisturbed.{C.RESET}")
        time.sleep(0.6)
        for _ in range(2):
            loot  = generate_loot_min_rarity("rare")
            color = RARITY_COLOR.get(loot.rarity, C.WHITE)
            print(f"\n  Found: {color}{C.BOLD}{loot.name}{C.RESET}  [{rarity_tag(loot.rarity)}]"
                  f"  {C.DIM}{loot.base_value}gp base{C.RESET}")
            if player.can_carry():
                pick = prompt_choice(["Take it", "Leave it"])
                if pick == 1:
                    player.add_item(loot)
            else:
                print(f"  {C.BRED}Inventory full — left behind.{C.RESET}")
        if has_picks:
            picks_item = next(i for i in player.inventory if i.name == "Lock Picks")
            player.remove_item(picks_item)
            print(f"\n  {C.DIM}Your lock picks opened a sealed compartment inside. (Consumed){C.RESET}")
    elif roll >= 12:
        # Partial — uncommon loot
        print(f"  {C.BYELLOW}You sense something but can't quite locate it. "
              f"Your hand finds a loose stone.{C.RESET}")
        time.sleep(0.6)
        loot  = generate_loot_min_rarity("uncommon")
        color = RARITY_COLOR.get(loot.rarity, C.WHITE)
        print(f"\n  Found: {color}{C.BOLD}{loot.name}{C.RESET}  [{rarity_tag(loot.rarity)}]")
        if player.can_carry():
            pick = prompt_choice(["Take it", "Leave it"])
            if pick == 1:
                player.add_item(loot)
        else:
            print(f"  {C.BRED}Inventory full — left behind.{C.RESET}")
    else:
        print(f"  {C.DIM}You search but find nothing. The draft may have been nothing at all.{C.RESET}")

    time.sleep(0.6)
    pause("Press Enter to continue...")


def _handle_dead_end(player: Player, event, room: DungeonRoom):
    """Dead end. Atmospheric lore only — no reward, no penalty."""
    _loc_header(event, "— Dead End")
    flavor = _DEAD_END_FLAVOR.get(
        room.dead_end_tag,
        "The passage closes off into rubble. Whatever was here, it's long gone."
    )
    typewrite(flavor)
    print()
    time.sleep(1.0)
    pause("Press Enter to turn back...")


def _handle_boss_room(player: Player, event, force_first: bool = False) -> bool:
    """
    Boss room. Named, buffed enemy. Returns True on victory, False on death/flee.
    """
    dung = player.skill("Dungeoneering")

    # Pre-boss warning — scales with Dungeoneering
    if dung >= 80:
        print(f"\n  {C.BRED}You know exactly what waits beyond this door: {event.boss_name}.{C.RESET}")
        print(f"  {C.BRED}Formidable. Do not underestimate it.{C.RESET}")
    elif dung >= 50:
        print(f"\n  {C.BRED}Something powerful waits ahead. The {event.boss_name}.{C.RESET}")
    elif dung >= 25:
        print(f"\n  {C.BYELLOW}Something powerful is close. You can feel it.{C.RESET}")
    else:
        print(f"\n  {C.DIM}The air changes. Something heavy lives in this room.{C.RESET}")
    time.sleep(1.0)

    boss = spawn_boss(event)

    _loc_header(event, f"— {event.boss_name.upper()}")
    print(f"  {C.BRED}{C.BOLD}{boss.name} rises to meet you.{C.RESET}")
    print(f"  {C.DIM}HP: {boss.hp}   Combat: {boss.combat_skill}{C.RESET}")
    time.sleep(1.2)

    won = run_combat(player, boss, force_first=force_first)

    if not player.is_alive():
        return False
    if not won:
        return False
    return True


def _boss_clear_reward(player: Player, event):
    """Award boss drop + location loot + journal on full clear."""
    clear()
    print()
    print(f"  {C.BGREEN}{C.BOLD}{event.boss_name} is defeated.{C.RESET}")
    print()
    time.sleep(0.8)

    # Named unique boss drop
    if event.boss_drop_name:
        drop = ITEM_LOOKUP.get(event.boss_drop_name)
        if drop:
            color = RARITY_COLOR.get(drop.rarity, C.WHITE)
            print(f"  {C.BYELLOW}The {event.boss_name} drops:{C.RESET}")
            print(f"  {color}{C.BOLD}{drop.name}{C.RESET}  [{rarity_tag(drop.rarity)}]"
                  f"  {C.DIM}{drop.base_value}gp base{C.RESET}")
            if drop.lore:
                print(f"  {C.DIM}{drop.lore}{C.RESET}")
            print()
            if player.can_carry():
                pick = prompt_choice(["Take it", "Leave it"])
                if pick == 1:
                    player.add_item(drop)
                    print(f"  {C.BGREEN}Added to inventory.{C.RESET}")
            else:
                print(f"  {C.BRED}Inventory full — left behind.{C.RESET}")
            print()

    # Room search — 2 × uncommon+
    print(f"  {C.DIM}You search the chamber carefully...{C.RESET}")
    time.sleep(0.8)
    for _ in range(2):
        loot  = generate_loot_min_rarity("uncommon")
        color = RARITY_COLOR.get(loot.rarity, C.WHITE)
        print(f"\n  Found: {color}{C.BOLD}{loot.name}{C.RESET}  [{rarity_tag(loot.rarity)}]"
              f"  {C.DIM}{loot.base_value}gp base{C.RESET}")
        if player.can_carry():
            pick = prompt_choice(["Take it", "Leave it"])
            if pick == 1:
                player.add_item(loot)
        else:
            print(f"  {C.BRED}Inventory full — left behind.{C.RESET}")

    # Journal
    if event.lore_text and event.lore_text not in player.journal:
        player.journal.append(event.lore_text)
        play_melody("journal_entry")
        print()
        hr("─")
        print(f"  {C.BYELLOW}❖ Journal updated — {event.name}{C.RESET}")
        print()
        for line in event.lore_text.split("\n"):
            print(f"  {line}")
        print()
        hr("─")


def explore_event(player: Player, event):
    """
    Entry point for a cave or castle exploration event.
    Generates a dungeon graph and walks the player through it room by room.
    """
    icon      = "🕳" if event.event_type == "cave" else "🏰"
    loc_color = C.BBLACK if event.event_type == "cave" else C.BYELLOW

    # ── Entry screen ──────────────────────────────────────────────────────────
    play_melody("location_found")
    clear()
    print()
    print(f"  {C.BYELLOW}{icon}  {event.name.upper()}{C.RESET}")
    print()
    typewrite(event.description)
    print()
    print(f"  {C.DIM}What lies within: ???{C.RESET}")
    print()

    # ── Pre-entry choices ─────────────────────────────────────────────────────
    scouted      = False
    stealth_used = False
    force_first  = False
    cached_dungeon = None   # set when Adventurer's Map is used; reused on entry

    # Adventurer's Map — peek at 2 room types before entering
    has_map = any(i.name == "Adventurer's Map" for i in player.inventory)

    while True:
        options = []
        if not scouted:
            options.append(f"Scout the area     {C.DIM}(Dungeoneering — count rooms){C.RESET}")
        if not stealth_used:
            options.append(f"Attempt stealth    {C.DIM}(Stealth — ambush first enemy){C.RESET}")
        if has_map:
            options.append(f"Use Adventurer's Map  {C.DIM}(reveals 2 rooms ahead){C.RESET}")
        options.append(f"Enter boldly       {C.DIM}(commit now){C.RESET}")
        options.append(f"Pass by            {C.DIM}(continue on the road){C.RESET}")

        choice_idx = prompt_choice(options)
        chosen     = options[choice_idx - 1]

        if "Scout the area" in chosen:
            scouted = True
            roll    = random.randint(1, 20) + player.skill("Dungeoneering") // 4
            if roll >= 18:
                print(f"\n  {C.BGREEN}You read the location well. "
                      f"You count the rooms and sense the layout.{C.RESET}")
            elif roll >= 12:
                print(f"\n  {C.BYELLOW}You make out movement and depth — "
                      f"several distinct chambers.{C.RESET}")
            else:
                print(f"\n  {C.DIM}You couldn't make out much from the entrance.{C.RESET}")
            pause("Press Enter to continue...")

        elif "Attempt stealth" in chosen:
            stealth_used   = True
            stealth_val    = player.skill("Stealth")
            success_chance = max(0.05, min(0.95, 0.15 + (stealth_val - 5) * 0.013))
            if random.random() < success_chance:
                force_first = True
                print(f"\n  {C.BGREEN}You slip inside undetected. "
                      f"The first enemy has no idea you're here.{C.RESET}")
            else:
                print(f"\n  {C.BYELLOW}You fumble the approach. No advantage gained.{C.RESET}")
            pause("Press Enter to continue...")

        elif "Adventurer's Map" in chosen:
            has_map = False
            map_item = next(i for i in player.inventory if i.name == "Adventurer's Map")
            player.remove_item(map_item)
            # Generate the dungeon once and cache it so the preview matches the run
            cached_dungeon = generate_dungeon(event)
            preview_rooms  = [r for r in cached_dungeon.values()
                               if r.room_type not in ("entry",)][:2]
            print(f"\n  {C.BYELLOW}The map reveals what lies ahead:{C.RESET}")
            for i, pr in enumerate(preview_rooms, 1):
                rtype_label = pr.room_type.replace("_", " ").title()
                print(f"  {C.DIM}Room {i}: {rtype_label}{C.RESET}")
            print(f"  {C.DIM}(Map consumed){C.RESET}")
            pause("Press Enter to continue...")

        elif "Pass by" in chosen:
            print(f"\n  {C.DIM}You give it a wide berth and press on.{C.RESET}")
            time.sleep(0.8)
            return

        else:
            break  # Enter boldly

    # ── Activate torch/lantern on entry ───────────────────────────────────────
    has_lantern     = any(i.name == "Lantern"      for i in player.inventory)
    has_torch       = any(i.name == "Torch Bundle" for i in player.inventory)
    has_tinderbox   = any(i.name == "Tinderbox"    for i in player.inventory)

    if (has_torch or has_lantern) and not has_tinderbox:
        print(f"\n  {C.BYELLOW}You have a light source but no tinderbox. "
              f"You cannot light it.{C.RESET}")
        has_torch   = False
        has_lantern = False
    elif has_lantern:
        print(f"\n  {C.BYELLOW}You light your lantern. The darkness retreats.{C.RESET}")
    elif has_torch:
        torch_item = next(i for i in player.inventory if i.name == "Torch Bundle")
        player.remove_item(torch_item)
        print(f"\n  {C.BYELLOW}You light a torch. The shadows pull back.{C.RESET}")

    clear()
    print()
    typewrite(f"You enter {event.name}...", indent=f"  {loc_color}")
    print(C.RESET, end="")
    time.sleep(0.8)
    play_location_music()

    # ── Generate dungeon ──────────────────────────────────────────────────────
    rooms     = generate_dungeon(event)
    current   = 0          # always start at room 0 (entry)
    rooms[current].visited = True
    dungeon_cleared = False

    # ── Navigation loop ───────────────────────────────────────────────────────
    while True:
        room = rooms[current]

        # ── Handle room ───────────────────────────────────────────────────────
        if not room.visited or room.room_type in ("combat", "boss"):
            room.visited = True

            if room.room_type == "entry":
                _loc_header(event, "— Entrance")
                print(f"  {C.DIM}You stand inside the entrance. The air changes.{C.RESET}")
                time.sleep(0.6)

            elif room.room_type == "combat":
                _loc_header(event, "— Combat")
                alive = _handle_combat_room(player, event, room,
                                             force_first=(force_first and current == 0))
                force_first = False   # only applies to room 0
                if not player.is_alive():
                    game_over(player)
                    return
                if not alive:
                    print(f"\n  {C.BYELLOW}You fall back out of {event.name}.{C.RESET}")
                    time.sleep(1.0)
                    stop_location_music()
                    start_ambient_loop("road")
                    return
                # Between-combat loot roll
                print()
                print(f"  {C.DIM}You search the area...{C.RESET}")
                time.sleep(0.5)
                _offer_loot(player, bias=room.loot_bias)

            elif room.room_type == "trap":
                alive = _handle_trap_room(player, event, room)
                if not alive:
                    game_over(player)
                    return

            elif room.room_type == "puzzle":
                _handle_puzzle_room(player, event, room)

            elif room.room_type == "secret":
                _handle_secret_room(player, event, room)

            elif room.room_type == "dead_end":
                _handle_dead_end(player, event, room)

            elif room.room_type == "boss":
                won = _handle_boss_room(player, event,
                                         force_first=force_first)
                if not player.is_alive():
                    game_over(player)
                    return
                if not won:
                    print(f"\n  {C.BYELLOW}You flee {event.name}.{C.RESET}")
                    time.sleep(1.0)
                    stop_location_music()
                    start_ambient_loop("road")
                    return
                # Victory
                dungeon_cleared = True
                _boss_clear_reward(player, event)
                stop_location_music()
                start_ambient_loop("road")
                pause()
                return

        # ── Navigation: build exit menu ───────────────────────────────────────
        exits   = room.exits
        # Check if any gating puzzle blocks an exit
        nav_opts = []
        nav_dest = []

        for label, dest_id in exits:
            dest_room = rooms[dest_id]
            # Gating puzzle already attempted and failed — lock the exit
            if (dest_room.room_type == "puzzle"
                    and dest_room.puzzle_gating
                    and dest_room.visited
                    and not dest_room.solved):
                nav_opts.append(f"{C.BBLACK}{label}  (sealed — puzzle unsolved){C.RESET}")
                nav_dest.append(None)   # blocked
            else:
                visited_mark = f"  {C.DIM}[visited]{C.RESET}" if dest_room.visited else ""
                nav_opts.append(f"{label}{visited_mark}")
                nav_dest.append(dest_id)

        nav_opts.append(f"Retreat  {C.DIM}(leave {event.name}){C.RESET}")
        nav_dest.append("retreat")

        print()
        choice = prompt_choice(nav_opts)
        dest = nav_dest[choice - 1]

        if dest == "retreat":
            clean = _retreat_check(player, event)
            if not player.is_alive():
                game_over(player)
                return
            time.sleep(1.0)
            stop_location_music()
            start_ambient_loop("road")
            return

        if dest is None:
            print(f"\n  {C.DIM}That passage is sealed. Find another way.{C.RESET}")
            time.sleep(0.8)
            continue

        current = dest
        play_location_music()  # re-cue loop on room transition


# ── Camping ───────────────────────────────────────────────────────────────────

CAMP_FOOD = {
    "Unknown Berries":  (10,  0,  True),
    "Dried Fruit":      (20,  8,  False),
    "Blueberries":      (20,  5,  False),
    "Small Game Meat":  (20,  8,  False),
    "Wild Mushrooms":   (15, 10,  False),
    "Herb Bundle":      (25, 20,  False),
    "Dried Rations":    (30, 15,  False),
    "Dried Meat":       (35, 15,  False),
    "Venison":          (40, 18,  False),
    "Bear Meat":        (40, 18,  False),
}

FIREWOOD_NAMES = {"Firewood"}


def make_camp(player: Player):
    """Resource-based camping. Costs 1 Firewood + 1 food item."""
    clear()
    title_screen("MAKE CAMP")

    firewood = next((i for i in player.inventory if i.name in FIREWOOD_NAMES), None)
    food     = next((i for i in player.inventory if i.name in CAMP_FOOD), None)

    if not firewood:
        print(f"\n  {C.BRED}You have no firewood. You cannot start a fire.{C.RESET}")
        print(f"  {C.DIM}Buy firewood in a city, or try Bushcraft to forage some.{C.RESET}")
        pause()
        return

    if not food:
        print(f"\n  {C.BRED}You have nothing to eat. Camp would be a cold, hungry affair.{C.RESET}")
        print(f"  {C.DIM}Stock up on rations before you travel, or try Bushcraft.{C.RESET}")
        pause()
        return

    if player.hp >= player.max_hp:
        print(f"\n  {C.BGREEN}You are in full health.{C.RESET}{C.DIM} Save your supplies for when you need them.{C.RESET}")
        pause()
        return

    hp_gain, mana_gain, poison_risk = CAMP_FOOD[food.name]

    print(f"\n  {C.DIM}You find a sheltered spot and build a fire.{C.RESET}")
    print(f"  {C.DIM}Consuming: {C.RESET}{firewood.name}{C.DIM} + {C.RESET}{food.name}")
    print()

    player.remove_item(firewood)
    player.remove_item(food)

    if poison_risk and random.random() < 0.20:
        player.take_damage(15)
        print(f"  {C.BRED}The berries were poisonous. -15 HP.{C.RESET}")
        print(f"  {C.DIM}HP: {player.hp}/{player.max_hp}{C.RESET}")
    else:
        player.heal(hp_gain)
        player.restore_mana(mana_gain)
        hunger_restore = FOOD_HUNGER_RESTORE.get(food.name, 30)
        player.hunger  = min(100, player.hunger + hunger_restore)
        gain_str = f"+{hp_gain} HP"
        if mana_gain:
            gain_str += f", +{mana_gain} Mana"
        gain_str += f", +{hunger_restore} hunger"
        print(f"  {C.BGREEN}You rest well through the night. {gain_str}.{C.RESET}")
        print(f"  {C.DIM}HP: {player.hp}/{player.max_hp}  |  Mana: {player.mana}/{player.max_mana}{C.RESET}")
        if food.name == "Herb Bundle":
            if player.road_poison > 0 or player.road_diseased or player.sick_days > 0:
                player.road_poison   = 0
                player.road_diseased = False
                player.sick_skill    = None
                player.sick_days     = 0
                player.sick_penalty  = 0
                print(f"  {C.BGREEN}The herbs clear whatever ailed you. Poison and sickness fade.{C.RESET}")

    pause()


# ── Foraging ──────────────────────────────────────────────────────────────────

FORAGE_TABLE = {
    "low": [
        ("Unknown Berries", 50),
        ("Firewood",        30),
        ("Wild Mushrooms",  15),
        ("Blueberries",      5),
    ],
    "mid": [
        ("Firewood",        35),
        ("Blueberries",     25),
        ("Wild Mushrooms",  20),
        ("Herb Bundle",     15),
        ("Unknown Berries",  5),
    ],
    "high": [
        ("Firewood",        28),
        ("Blueberries",     22),
        ("Wild Mushrooms",  20),
        ("Herb Bundle",     18),
        ("Nightshade",      12),
    ],
    "expert": [
        ("Herb Bundle",     28),
        ("Firewood",        22),
        ("Blueberries",     20),
        ("Nightshade",      18),
        ("Wild Mushrooms",  12),
    ],
}


def _do_forage(player: Player):
    """Attempt foraging. Success chance and quality both scale with Survival."""
    from data.items import ITEM_LOOKUP as _LOOKUP
    survival       = player.skill("Survival")
    success_chance = 35 + survival * 0.5

    clear()
    title_screen("FORAGING")
    print(f"  {C.DIM}You move quietly through the undergrowth...{C.RESET}")
    time.sleep(1.0)
    print()

    encounter_roll = random.random()
    biome          = getattr(player, "road_biome", "forest")
    if encounter_roll < 0.14:
        from data.enemies import get_enemy_for_biome
        enc_enemy = get_enemy_for_biome(biome)
        print(f"  {C.BRED}A {enc_enemy.name} finds you before you find anything useful.{C.RESET}")
        print(f"  {C.DIM}{enc_enemy.description}{C.RESET}")
        time.sleep(1.2)
        won = run_combat(player, enc_enemy)
        if not player.is_alive():
            return
        if won:
            loot_screen(player, enc_enemy)
        clear()
        title_screen("FORAGING")
        print(f"  {C.DIM}The encounter behind you, you search the area once more...{C.RESET}")
        time.sleep(0.8)
        print()
    elif encounter_roll < 0.20:
        from engine.events import random_cave, random_castle
        event = random.choice([random_cave(), random_castle()])
        print(f"  {C.BYELLOW}While foraging, you stumble upon something...{C.RESET}")
        print(f"  {C.DIM}{event.flavour}{C.RESET}")
        time.sleep(1.2)
        explore_event(player, event)
        if not player.is_alive():
            return
        clear()
        title_screen("FORAGING")
        print(f"  {C.DIM}You return to your search...{C.RESET}")
        time.sleep(0.8)
        print()

    if random.random() * 100 > success_chance:
        player.days_elapsed += 1
        player.road_total   += 1
        print(f"  {C.BBLACK}Your time spent foraging was unsuccessful.")
        print(f"  It has since grown dark. Your journey extends a day...{C.RESET}")
        pause()
        return

    if survival < 20:
        tier, qual_msg = "low",    f"  {C.DIM}You find something. Hard to say exactly what.{C.RESET}"
    elif survival < 50:
        tier, qual_msg = "mid",    f"  {C.DIM}You read the landscape well enough to find something useful.{C.RESET}"
    elif survival < 80:
        tier, qual_msg = "high",   f"  {C.BGREEN}You know this terrain. You move efficiently and find good yield.{C.RESET}"
    else:
        tier, qual_msg = "expert", f"  {C.BGREEN}The wilderness gives up its secrets to you readily.{C.RESET}"

    print(qual_msg)
    print()

    table      = FORAGE_TABLE[tier]
    names, wts = zip(*table)
    found_name = random.choices(names, weights=wts, k=1)[0]
    found_item = _LOOKUP.get(found_name)

    if found_item:
        if player.can_carry():
            player.add_item(found_item)
            print(f"  {C.BGREEN}You find: {found_name}{C.RESET}")
            print(f"  {C.DIM}{found_item.description}{C.RESET}")
        else:
            print(f"  {C.BYELLOW}You found {found_name} but your pack is full.{C.RESET}")
    pause()


# ── Hunting ───────────────────────────────────────────────────────────────────

HUNT_ANIMALS = [
    ("Squirrel",  "A small, quick creature. Easy prey.",             0,  "Small Game Meat", "Squirrel Pelt", 0.05,  0,  0.00),
    ("Fox",       "Lean and clever. Alert ears.",                   20,  "Small Game Meat", "Fox Pelt",      0.10,  5,  0.00),
    ("Owl",       "Silent-winged and sharp-eyed.",                  20,  "Small Game Meat", "Squirrel Pelt", 0.08,  5,  0.00),
    ("Badger",    "Stocky and aggressive when cornered.",           30,  "Dried Meat",      "Fox Pelt",      0.15, 10,  0.00),
    ("Deer",      "Graceful. Alert to every sound.",                40,  "Venison",         "Deer Pelt",     0.20, 12,  0.00),
    ("Elk",       "Towering. Dangerous when cornered.",             55,  "Venison",         "Elk Pelt",      0.25, 20,  0.05),
    ("Bear",      "Massive. Do not miss.",                          70,  "Bear Meat",       "Bear Pelt",     0.40, 35,  0.15),
    ("Dire Wolf", "A beast beyond natural proportions.",            80,  "Bear Meat",       "Bear Pelt",     0.45, 40,  0.25),
    ("Wyvern",    "A flying terror. Wings like thunder.",           90,  "Bear Meat",       "Mystical Fang", 0.60, 60,  0.45),
    ("Dragon",    "Ancient. Absolute. You should not be here.",    100,  "Bear Meat",       "Mystical Fang", 0.80, 999, 0.85),
]


def _get_huntable_animals(player):
    avg       = (player.skill("Stealth") + player.skill("Survival")) / 2
    available = [a for a in HUNT_ANIMALS if avg >= a[2]]
    return available if available else [HUNT_ANIMALS[0]]


def hunting_minigame(player):
    from data.items import ITEM_LOOKUP as _LOOKUP

    available = _get_huntable_animals(player)
    weights   = [max(1, len(available) - i) for i in range(len(available))]
    animal    = random.choices(available, weights=weights, k=1)[0]
    a_name, a_desc, _, meat_name, pelt_name, bone_chance, miss_dmg, death_risk = animal

    stealth  = player.skill("Stealth")
    survival = player.skill("Survival")
    martial  = player.skill("Martial")

    kill_chance = 10 + (stealth + survival) / 5
    injury_risk = max(0.10, (40 - survival * 0.3) / 100)

    clear()
    title_screen(f"HUNTING — {a_name.upper()}")
    print(f"\n  {C.DIM}You spot a {a_name} in the undergrowth.{C.RESET}")
    print(f"  {C.DIM}{a_desc}{C.RESET}")
    print()
    print(f"  {C.BYELLOW}Starting kill chance: {kill_chance:.0f}%{C.RESET}   "
          f"{C.DIM}Injury risk on miss: {injury_risk*100:.0f}%{C.RESET}")
    if death_risk > 0:
        print(f"  {C.BRED}Lethal retaliation risk: {death_risk*100:.0f}%{C.RESET}")
    pause()

    round_log = []
    forced    = False

    for round_num in range(1, 4):
        if kill_chance >= 85:
            forced = True
            break

        clear()
        title_screen(f"HUNTING — {a_name.upper()}  (Round {round_num}/3)")
        print(f"  {C.DIM}{a_desc}{C.RESET}")
        print()
        if round_log:
            for line in round_log:
                print(f"  {line}")
            print()
        print(f"  {C.BYELLOW}Kill chance: {kill_chance:.0f}%   "
              f"Injury risk: {injury_risk*100:.0f}%{C.RESET}")
        print()

        options = [
            f"Move silently       {C.DIM}[Stealth: {stealth}]  — close the distance{C.RESET}",
            f"Track and position  {C.DIM}[Survival: {survival}]  — read its movement{C.RESET}",
            f"Take the shot now   {C.DIM}[Martial: {martial}]{C.RESET}",
            f"Let it go           {C.DIM}(abandon the hunt){C.RESET}",
        ]
        choice = prompt_choice(options, "Your approach")

        if choice == 4:
            print(f"\n  {C.DIM}You lower your bow. The {a_name} vanishes into the trees.{C.RESET}")
            pause()
            return

        if choice == 3:
            break

        if choice == 1:
            diff = random.randint(10, 25)
            roll = random.randint(1, 20) + stealth // 4
            if roll >= diff:
                gain        = 5 + stealth // 10
                kill_chance = min(85, kill_chance + gain)
                round_log.append(
                    f"{C.BGREEN}✓ You close the distance silently. "
                    f"+{gain:.0f}% kill chance → {kill_chance:.0f}%{C.RESET}")
            else:
                round_log.append(f"{C.BRED}✗ A twig snaps. The {a_name} tenses but holds.{C.RESET}")

        elif choice == 2:
            diff = random.randint(10, 22)
            roll = random.randint(1, 20) + survival // 4
            if roll >= diff:
                gain        = 3 + survival // 15
                kill_chance = min(85, kill_chance + gain)
                inj_drop    = survival // 20
                injury_risk = max(0.05, injury_risk - inj_drop / 100)
                round_log.append(
                    f"{C.BGREEN}✓ You read its pattern. "
                    f"+{gain:.0f}% kill chance → {kill_chance:.0f}%  "
                    f"Injury risk ↓{C.RESET}")
            else:
                round_log.append(f"{C.BRED}✗ The animal shifts. You wait it out.{C.RESET}")

        if kill_chance >= 85:
            forced = True

    # Final shot decision
    clear()
    title_screen(f"HUNTING — {a_name.upper()}")
    for line in round_log:
        print(f"  {line}")
    print()
    if forced and kill_chance >= 85:
        print(f"  {C.BGREEN}You are close enough to count the breaths between its ribs.{C.RESET}")
        print(f"  {C.BYELLOW}This is as good a chance as you'll get.{C.RESET}")
    else:
        print(f"  {C.BYELLOW}Time is running out. You must decide now.{C.RESET}")
    print()

    options = [
        f"Take the shot   {C.DIM}[Martial: {martial}]  Kill chance: {kill_chance:.0f}%{C.RESET}",
        f"Let it go       {C.DIM}(walk away){C.RESET}",
    ]
    if prompt_choice(options, "") == 2:
        print(f"\n  {C.DIM}You lower your bow. Some hunts are not meant to end.{C.RESET}")
        pause()
        return

    clear()
    title_screen(f"THE SHOT — {a_name.upper()}")
    print(f"  {C.DIM}Kill chance: {kill_chance:.0f}%{C.RESET}")
    print()
    time.sleep(0.8)

    difficulty = max(4, 22 - int(kill_chance // 5))
    shot_roll  = random.randint(1, 20) + martial // 4

    if shot_roll >= difficulty:
        play_melody("victory")
        print(f"  {C.BGREEN}The arrow finds its mark. The {a_name} falls.{C.RESET}")
        print()

        yields     = []
        meat_count = 1 + (survival // 40)
        meat_item  = _LOOKUP.get(meat_name)
        for _ in range(meat_count):
            if meat_item and player.can_carry():
                player.add_item(meat_item)
                yields.append(meat_name)

        pelt_chance = min(0.90, 0.20 + survival * 0.007)
        if random.random() < pelt_chance:
            pelt_item = _LOOKUP.get(pelt_name)
            if pelt_item and player.can_carry():
                player.add_item(pelt_item)
                yields.append(pelt_name)

        if random.random() < bone_chance:
            if a_name in ("Wyvern", "Dragon"):
                bone_pool = ["Mystical Fang", "Dragon Hide"]
            else:
                bone_pool = ["Bone Tusk", "Bear Claw", "Wolf Tooth"]
            bitem = _LOOKUP.get(random.choice(bone_pool))
            if bitem and player.can_carry():
                player.add_item(bitem)
                yields.append(bitem.name)

        if yields:
            print(f"  {C.BYELLOW}You salvage:{C.RESET}")
            for y in sorted(set(yields)):
                cnt = yields.count(y)
                print(f"    {C.DIM}{'x'+str(cnt)+' ' if cnt > 1 else ''}{y}{C.RESET}")
        else:
            print(f"  {C.DIM}Your pack is full — you carry nothing away.{C.RESET}")

    else:
        print(f"  {C.BRED}The shot goes wide. The {a_name} bolts.{C.RESET}")
        print()
        time.sleep(0.8)

        if death_risk > 0 and random.random() < death_risk:
            print(f"  {C.BRED}{C.BOLD}The {a_name} turns on you!{C.RESET}")
            time.sleep(0.6)
            if a_name == "Dragon":
                print(f"  {C.BRED}A torrent of flame engulfs you completely.{C.RESET}")
                player.take_damage(player.hp)
            else:
                player.take_damage(miss_dmg)
                print(f"  {C.BRED}It mauls you savagely. -{miss_dmg} HP.  "
                      f"HP: {player.hp}/{player.max_hp}{C.RESET}")
        elif miss_dmg > 0 and random.random() < injury_risk:
            player.take_damage(miss_dmg)
            print(f"  {C.BRED}As it flees it catches you with a glancing blow. "
                  f"-{miss_dmg} HP.{C.RESET}")
            print(f"  {C.DIM}HP: {player.hp}/{player.max_hp}{C.RESET}")
        else:
            print(f"  {C.DIM}You escape without injury.{C.RESET}")

    pause()


def bushcraft_screen(player):
    clear()
    title_screen("BUSHCRAFT")

    survival = player.skill("Survival")
    has_bow  = (
        any(getattr(i, "weapon_type", None) == "bow" for i in player.inventory)
        or getattr(player.equipped.get("weapon"), "weapon_type", None) == "bow"
    )

    print(f"  {C.DIM}Survival: {survival}   "
          f"Forage success: ~{min(85, int(35 + survival * 0.5))}%{C.RESET}")
    print()

    options = ["Forage for resources"]
    if has_bow:
        options.append(f"Hunt for game  {C.DIM}(bow ready — Stealth + Survival){C.RESET}")
    else:
        options.append(f"{C.BBLACK}Hunt for game  (requires a bow — none in pack){C.RESET}")
    options.append(f"{C.BBLACK}← Back to road{C.RESET}")

    choice = prompt_choice(options, "What will you do?")

    if choice == len(options):
        return
    if choice == 1:
        _do_forage(player)
    elif choice == 2:
        if has_bow:
            hunting_minigame(player)
        else:
            print(f"\n  {C.BBLACK}You need a bow to hunt. Pick one up from a Blacksmith or loot one on the road.{C.RESET}")
            pause("Press Enter to continue...")


# ── Wilderness events ─────────────────────────────────────────────────────────

HERMIT_LORE = [
    "The road south bends toward Caldervast. Don't linger at the crossroads after dark — something there listens.",
    "I've walked these woods for forty years. The silence has changed. It used to mean peace.",
    "There's a merchant in Ashenvale who smiles too wide. Count your fingers after you shake his hand.",
    "The old castle beyond the ridge — men used to dare each other to spend the night. They stopped doing that.",
    "Ravens don't fly at night. If you see one after dusk, turn back.",
    "A boy passed through here three days ago. Running east. He didn't say from what.",
    "The river downstream runs clear but tastes of iron. Has done for a season now.",
    "Some roads weren't built for trade. They were built to keep something in.",
    "I found a coin near the standing stones last spring. Old face on it. No king I've ever known.",
    "The stars have been wrong lately. Not wrong enough for most to notice. But wrong.",
]

WILDERNESS_BASE_CHANCE  = 0.18
WILDERNESS_SKILL_REDUCE = 0.0012


def get_wilderness_chance(player: Player) -> float:
    return max(0.06, WILDERNESS_BASE_CHANCE - player.skill("Survival") * WILDERNESS_SKILL_REDUCE)


def _we_snake(player: Player):
    section("SNAKE BITE")
    typewrite("A flash of movement near your boot — too late to fully react.")
    print()
    roll = random.randint(1, 20) + player.skill("Survival") // 5
    if roll >= 13:
        print(f"  {C.BGREEN}You catch the movement just in time and leap back. The snake retreats into the undergrowth.{C.RESET}")
    else:
        dmg = random.randint(15, 25)
        player.take_damage(dmg)
        beep("hit")
        print(f"  {C.BRED}Fangs catch your ankle. You wrench free but the damage is done. −{dmg} HP.{C.RESET}")
        if random.random() < 0.35:
            player.road_poison = 2
            print(f"  {C.BRED}Your leg goes numb. You've been poisoned.{C.RESET}")
            print(f"  {C.DIM}(−5 HP per road step for 2 steps — cure with Herb Bundle at camp){C.RESET}")
    print()
    pause("Press Enter to continue...")


def _we_disease(player: Player):
    section("ILL WIND")
    typewrite("Something in the air — a rotting sweetness, a crawling unease. You feel it settle in your chest.")
    print()
    roll = random.randint(1, 20) + player.skill("Survival") // 5
    if roll >= 12:
        player.take_damage(5)
        print(f"  {C.BYELLOW}You recognise the warning signs early and push through. −5 HP.{C.RESET}")
        print(f"  {C.DIM}HP: {player.hp}/{player.max_hp}{C.RESET}")
    else:
        player.take_damage(20)
        player.road_diseased = True
        beep("hit")
        print(f"  {C.BRED}You don't catch it in time. −20 HP and the sickness takes hold.{C.RESET}")
        print(f"  {C.DIM}(−5 HP per road step until you reach a town — cure by camping with Herb Bundle){C.RESET}")
        print(f"  {C.DIM}HP: {player.hp}/{player.max_hp}{C.RESET}")
    print()
    pause("Press Enter to continue...")


def _we_weather(player: Player):
    storm = random.choice([
        "A sudden storm rolls in off the hills.",
        "Thick fog descends without warning.",
        "Sleet hammers the road from nowhere.",
    ])
    section("WEATHER")
    typewrite(storm + " The road ahead becomes treacherous.")
    print()
    roll = random.randint(1, 20) + player.skill("Survival") // 5
    if roll >= 11:
        player.road_total += 1
        print(f"  {C.BYELLOW}You read the signs early and find what cover you can — but the delay costs you a day.{C.RESET}")
        print(f"  {C.DIM}(+1 road step added){C.RESET}")
    else:
        player.road_total += 2
        dmg = 10
        player.take_damage(dmg)
        beep("hit")
        print(f"  {C.BRED}Caught in the open, you suffer {dmg} HP of exposure. Your journey is pushed back significantly.{C.RESET}")
        print(f"  {C.DIM}(+2 road steps added){C.RESET}")
        print(f"  {C.DIM}HP: {player.hp}/{player.max_hp}{C.RESET}")
    print()
    pause("Press Enter to continue...")


def _we_stranger(player: Player):
    archetype = random.choice(["lost_traveller", "hermit", "shady_figure"])

    if archetype == "lost_traveller":
        section("TRAVELLER")
        typewrite("A figure on the road ahead — weary pack, no obvious destination. They slow as you approach.")
        print()
        roll = random.randint(1, 20) + player.skill("Speechcraft") // 5
        if roll >= 8:
            gold = random.randint(5, 15)
            player.gold += gold
            print(f"  {C.BGREEN}You exchange a few words. They're grateful for the company and press coins into your palm before parting.{C.RESET}")
            print(f"  {C.BYELLOW}+{gold}gp{C.RESET}")
        else:
            print(f"  {C.DIM}They glance at you briefly and walk on without a word. Ships passing.{C.RESET}")
        print()
        pause("Press Enter to continue...")

    elif archetype == "hermit":
        section("THE HERMIT")
        typewrite("An old figure sits by a dead fire off the side of the road, watching you approach without moving.")
        print()
        roll = random.randint(1, 20) + player.skill("Speechcraft") // 5
        if roll >= 10:
            print(f"  {C.BGREEN}They study you for a long moment, then reach into their bundle.{C.RESET}")
            print(f'  {C.DIM}"Take this. The road ahead will ask more of you than you think."{C.RESET}')
            loot  = generate_loot(bias="uncommon")
            color = RARITY_COLOR.get(loot.rarity, C.WHITE)
            if player.can_carry():
                player.add_item(loot)
                print(f"  Found: {color}{C.BOLD}{loot.name}{C.RESET}")
            else:
                print(f"  {C.BYELLOW}They offer you something but your pack is full. You cannot carry it.{C.RESET}")
            unused = [l for l in HERMIT_LORE if l not in player.journal]
            if unused:
                lore = random.choice(unused)
                player.journal.append(lore)
                play_melody("journal_entry")
                print()
                hr("─")
                print(f"  {C.BYELLOW}❖ Journal updated{C.RESET}")
                print()
                typewrite(lore)
                print()
                hr("─")
        else:
            print(f"  {C.DIM}They watch you pass without a word. Their eyes stay on you until you've rounded the bend.{C.RESET}")
        print()
        pause("Press Enter to continue...")

    else:  # shady_figure
        section("STRANGER")
        typewrite("Someone is standing in the middle of the road. Hood pulled low. Watching you come.")
        print()
        surv_roll = random.randint(1, 20) + player.skill("Survival") // 5
        if surv_roll >= 10:
            print(f"  {C.BYELLOW}Something is wrong — your instincts say don't stop. You give them a wide berth and keep moving.{C.RESET}")
            print()
            pause("Press Enter to continue...")
            return
        speech_roll = random.randint(1, 20) + player.skill("Speechcraft") // 5
        if speech_roll >= 13:
            print(f"  {C.BGREEN}You meet their eye and hold it. They read something in your face and step aside without a word.{C.RESET}")
        else:
            loss = random.randint(10, 25)
            player.gold = max(0, player.gold - loss)
            beep("hit")
            print(f"  {C.BRED}A blade appears from the cloak. \"Your coin or worse.\" You hand it over.{C.RESET}")
            print(f"  {C.BYELLOW}−{loss}gp{C.RESET}")
        print()
        pause("Press Enter to continue...")


def wilderness_event(player: Player):
    """Roll and fire a random wilderness event. Modifies player state in-place."""
    etype = random.choice(["snake", "disease", "weather", "stranger"])
    clear()
    print()
    if etype == "snake":
        _we_snake(player)
    elif etype == "disease":
        _we_disease(player)
    elif etype == "weather":
        _we_weather(player)
    else:
        _we_stranger(player)


# ── Game over ─────────────────────────────────────────────────────────────────

def game_over(player):
    clear()
    title_screen("YOU HAVE FALLEN")
    print(f"  {player.name}'s journey has ended.")
    print()
    print(f"  {C.BYELLOW}Days on the road:{C.RESET}  {_format_time(player.days_elapsed)}")
    print(f"  {C.BYELLOW}Gold carried:    {C.RESET}  {player.gold}gp")
    print(f"  {C.DIM}Items lost:        {len(player.inventory)}{C.RESET}")
    print()
    hr()
    print()
    pause("Press Enter to exit...")
    sys.exit(0)


# ── Road loop ─────────────────────────────────────────────────────────────────

def road_loop(player):
    _first_step = True

    while player.on_road:
        dest_name  = CITIES[player.road_destination].name
        road_biome = player.road_biome

        show_world_map(player)

        if _first_step:
            print(f"  {C.BYELLOW}You step foot on the road to {dest_name}.{C.RESET}")
            pause("  Press Enter to set out...")
            _first_step = False

        flavor = road_flavor_line(road_biome, player.road_steps, player.road_total)
        show_world_map(player)
        print(f"  {C.DIM}{flavor}{C.RESET}")
        print()
        section("ROAD")

        has_fire = any(i.name in FIREWOOD_NAMES for i in player.inventory)
        has_food = any(i.name in CAMP_FOOD for i in player.inventory)
        if has_fire and has_food:
            camp_label = f"Make camp      {C.DIM}(costs 1 Firewood + 1 food item){C.RESET}"
        else:
            missing = []
            if not has_fire: missing.append("firewood")
            if not has_food: missing.append("food")
            camp_label = (f"{C.BBLACK}Make camp      "
                          f"(missing: {', '.join(missing)}){C.RESET}")

        options = [
            f"Press on         {C.DIM}(continue towards {dest_name}){C.RESET}",
            camp_label,
            f"Bushcraft        {C.DIM}(forage or hunt — governed by Survival){C.RESET}",
            f"Bag              {C.DIM}(gear + journal){C.RESET}",
            f"Character Sheet  {C.DIM}(stats, equipment, inventory){C.RESET}",
            f"Turn back        {C.DIM}(return to origin city){C.RESET}",
        ]
        choice = prompt_choice(options)

        if choice == 2:
            make_camp(player)
            continue

        if choice == 3:
            bushcraft_screen(player)
            if not player.is_alive():
                game_over(player)
                return
            continue

        if choice == 4:
            bag_screen(player)
            continue

        if choice == 5:
            show_character_sheet(player)
            continue

        if choice == 6:
            abort_travel(player)
            player.road_poison   = 0
            player.road_diseased = False
            start_ambient_loop("city")
            print(f"\n  {C.DIM}You turn back.{C.RESET}")
            time.sleep(0.8)
            return

        arrived, enemy, event = take_road_step(player)

        # ── Status effect drain (poison / disease) ────────────────────────────
        if player.road_poison > 0:
            player.take_damage(5)
            player.road_poison -= 1
            _ps  = "s" if player.road_poison != 1 else ""
            rem  = f"{player.road_poison} step{_ps} remaining" if player.road_poison > 0 else "poison has faded"
            print(f"  {C.BRED}Poison courses through you. −5 HP. ({rem}){C.RESET}")
            time.sleep(0.6)
            if not player.is_alive():
                game_over(player)
                return

        if player.road_diseased:
            player.take_damage(5)
            print(f"  {C.BRED}The sickness weighs on you. −5 HP.{C.RESET}")
            time.sleep(0.6)
            if not player.is_alive():
                game_over(player)
                return

        if player.sick_days > 0:
            player.sick_days -= 1
            if player.sick_days == 0:
                print(f"  {C.BGREEN}The berry sickness fades. Your {player.sick_skill} feels normal again.{C.RESET}")
                player.sick_skill   = None
                player.sick_penalty = 0
                time.sleep(0.6)
            else:
                _sd = "day" if player.sick_days == 1 else "days"
                print(f"  {C.BYELLOW}You still feel unwell. ({player.sick_skill} dulled — {player.sick_days} {_sd} remaining){C.RESET}")
                time.sleep(0.5)

        # ── Hunger drain ──────────────────────────────────────────────────────
        if player.hunger < 10:
            player.take_damage(5)
            print(f"  {C.BRED}You are too weak to continue without food. −5 HP.  HP: {player.hp}/{player.max_hp}{C.RESET}")
            time.sleep(0.6)
            if not player.is_alive():
                game_over(player)
                return
        elif player.hunger < 30:
            print(f"  {C.BRED}[Starving]{C.RESET}  {C.DIM}Weakness gnaws at you. (−5 Martial, −5 Survival){C.RESET}")
            time.sleep(0.4)
        elif player.hunger < 60:
            print(f"  {C.BYELLOW}[Hungry]{C.RESET}  {C.DIM}Your stomach growls.{C.RESET}")
            time.sleep(0.3)

        if arrived:
            player.road_poison   = 0
            player.road_diseased = False
            player.sick_skill    = None
            player.sick_days     = 0
            player.sick_penalty  = 0
            city = CITIES[player.current_city]
            play_melody("city_arrive")
            start_ambient_loop("city")
            show_world_map(player)
            print(f"\n  {C.BGREEN}You arrive in {city.name}. Day {player.days_elapsed}.{C.RESET}")
            time.sleep(1.5)
            return

        if enemy:
            clear()
            print()
            typewrite(f"A {enemy.name} blocks your path!")
            print(f"\n  {C.DIM}{enemy.description}{C.RESET}")
            print()
            pause("  Press Enter to engage...")
            won = run_combat(player, enemy)
            if not player.is_alive():
                game_over(player)
                return
            if won:
                loot_screen(player, enemy)

        if event:
            explore_event(player, event)

        if not arrived and not enemy and not event:
            if random.random() < get_wilderness_chance(player):
                wilderness_event(player)
                if not player.is_alive():
                    game_over(player)
                    return
