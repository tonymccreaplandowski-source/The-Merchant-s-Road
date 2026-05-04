"""
Burglary mini-game — lockpicking + room-by-room loot, triggered from Prowl.

Skill formula: (Dungeoneering + Stealth) // 2 determines how many of the
6 tumblers are visible. At 0 skill all are hidden; at 60+ all are visible.
"""

import random
from engine.player import Player
from ui.display    import C, clear, pause, title_screen, section, prompt_choice, hr, typewrite


# ── Location definitions ──────────────────────────────────────────────────────
# (name, flavour, min_stealth, base_catch_pct, loot_bias, is_connected, search_spots)

BURGLARY_LOCATIONS = [
    {
        "name":        "Commoner's Home",
        "flavour":     "A single-room dwelling. Tallow candle still burning.",
        "min_stealth": 10,
        "catch_pct":   20,
        "catch_step":  12,   # +% per search spot entered
        "loot_bias":   "common",
        "connected":   False,
        "spots": [
            ("Bedside table",  "A cracked drawer with a candle stub and a few coins."),
            ("Kitchen pantry", "Smells of dried herbs. A tin box sits on the upper shelf."),
            ("Loose floorboard","One plank gives a hollow knock when you press it."),
        ],
    },
    {
        "name":        "Merchant's Stall",
        "flavour":     "Shuttered front, stock room in the back. The owner lives above.",
        "min_stealth": 25,
        "catch_pct":   35,
        "catch_step":  15,
        "loot_bias":   "uncommon",
        "connected":   False,
        "spots": [
            ("Lock box under the counter", "Small iron chest, still warm from the day's trade."),
            ("Stock shelves",              "Back wall of goods — some packed, some loose."),
            ("Owner's writing desk",       "Ledgers, receipts, and a personal pouch."),
        ],
    },
    {
        "name":        "Craftsman's Guild Hall",
        "flavour":     "Locked after hours. Apprentice quarters upstairs — careful.",
        "min_stealth": 45,
        "catch_pct":   50,
        "catch_step":  18,
        "loot_bias":   "uncommon",
        "connected":   False,
        "spots": [
            ("Treasurer's cabinet",  "Oak cabinet with a wax-sealed brass lock."),
            ("Tool storage",         "Rare materials and finished pieces waiting for collection."),
            ("Master's private room","Off the main hall. Probably shouldn't be in here."),
            ("Guild archive chest",  "Records, patents, and a sealed strongbox."),
        ],
    },
    {
        "name":        "Guild Master's Manor",
        "flavour":     "Walled grounds. A lantern burns in an upstairs window. Someone is home.",
        "min_stealth": 65,
        "catch_pct":   60,
        "catch_step":  20,
        "loot_bias":   "rare",
        "connected":   True,
        "spots": [
            ("Study desk",       "Correspondence, a signet ring, and something behind the ink pot."),
            ("Wardrobe strongbox","Hidden at the back. They always put it at the back."),
            ("Dining room cabinet","Crystal, silverware, and a locked display case."),
            ("Personal vault",   "Small but well-made. Someone paid for this."),
        ],
    },
    {
        "name":        "The Castle",
        "flavour":     "Stone walls. Torchlit corridors. Guards on rotation every four minutes.",
        "min_stealth": 75,
        "catch_pct":   70,
        "catch_step":  25,
        "loot_bias":   "rare",
        "connected":   True,
        "spots": [
            ("Guard captain's office",  "The good stuff is always where the boss sits."),
            ("Treasury antechamber",    "Not the vault — but adjacent to it. Close enough."),
            ("Lord's private chambers", "You shouldn't even be on this floor."),
            ("Armoury side room",       "Requisitioned materials. Surplus. Unaccounted for."),
        ],
    },
]


# ── Lockpick mini-game ────────────────────────────────────────────────────────

def _draw_tumblers(correct: int, visible_set: set) -> None:
    """
    Visual tumbler chart. 6 tumblers; the correct pin is UP (tall).
    Visible tumblers show their true state. Hidden show as ???.
    correct: 1-indexed pin number that is raised.
    visible_set: set of 1-indexed tumbler numbers the player can see.
    """
    labels = "  " + "  ".join(f" [{i}]" for i in range(1, 7))
    print(labels)
    print()

    ROWS = 4
    for row in range(ROWS):
        line = "  "
        for t in range(1, 7):
            if t in visible_set:
                if t == correct:
                    # Raised pin — visible and correct
                    cell = f"{C.BGREEN}████{C.RESET}"
                else:
                    # Lowered pin — visible and wrong
                    cell = f"{C.BBLACK}────{C.RESET}" if row == ROWS - 1 else "    "
            else:
                # Hidden
                cell = f"{C.BYELLOW}????" + C.RESET
            line += cell + "  "
        print(line)
    print()


def _lockpick_attempt(player: Player) -> bool:
    """
    Runs one tumbler mini-game attempt. Consumes one Lock Pick on failure.
    Returns True if lock is opened.
    """
    from data.items import ITEM_LOOKUP

    from engine.lore_bonuses import get_lore_bonus
    pick_skill  = (player.skill("Dungeoneering") + player.skill("Stealth")) // 2
    pick_skill  = min(60, pick_skill + int(get_lore_bonus(player, "lockpick_skill_bonus")))
    n_visible   = min(6, pick_skill // 10)
    correct     = random.randint(1, 6)
    visible_set = set(random.sample(range(1, 7), n_visible)) if n_visible > 0 else set()

    clear()
    section("LOCKPICKING")
    print(f"  {C.DIM}One of these pins is raised. Pick the right one.{C.RESET}")
    print(f"  {C.DIM}Pick skill: {pick_skill}  |  Visible pins: {n_visible}/6{C.RESET}")
    print()
    hr()
    print()
    _draw_tumblers(correct, visible_set)

    # Identify guessable range (hidden tumblers)
    hidden = [t for t in range(1, 7) if t not in visible_set]
    if not hidden:
        # All pins visible — correct one is shown as green
        print(f"  {C.BGREEN}You can read the lock perfectly. The raised pin is obvious.{C.RESET}")
        pause("Press Enter to set the pin...")
        return True

    while True:
        try:
            raw = input(f"  {C.BCYAN}Pick tumbler (1–6): {C.RESET}").strip()
            val = int(raw)
            if 1 <= val <= 6:
                break
            print(f"  {C.RED}Enter a number between 1 and 6.{C.RESET}")
        except (ValueError, EOFError):
            print(f"  {C.RED}Invalid input.{C.RESET}")

    if val == correct:
        print(f"\n  {C.BGREEN}Click. The pin sets. You feel the lock give.{C.RESET}")
        pause("Press Enter to push the door...")
        return True
    else:
        print(f"\n  {C.BRED}The pick bites wrong. You feel it snap.{C.RESET}")
        # Consume one Lock Pick
        pick_item = next((i for i in player.inventory if i.name == "Lock Picks"), None)
        if pick_item:
            player.remove_item(pick_item)
            remaining = sum(1 for i in player.inventory if i.name == "Lock Picks")
            print(f"  {C.DIM}Lock Pick consumed. {remaining} remaining.{C.RESET}")
        pause()
        return False


# ── Search spot ───────────────────────────────────────────────────────────────

def _search_spot(player: Player, spot_name: str, spot_flavour: str, loot_bias: str) -> None:
    """One search attempt inside a location. Always offers loot roll."""
    from engine.loot  import generate_loot, generate_loot_min_rarity
    from ui.display   import RARITY_COLOR
    from data.items   import RARITY_LABELS

    clear()
    section(spot_name.upper())
    print(f"  {C.DIM}{spot_flavour}{C.RESET}")
    print()
    pause("Press Enter to search...")

    # Loot roll — higher find chance than road (this is targeted theft)
    if random.random() < 0.65:
        loot  = generate_loot(bias=loot_bias)
        color = RARITY_COLOR.get(loot.rarity, C.WHITE)
        print(f"\n  Found: {color}{C.BOLD}{loot.name}{C.RESET}  "
              f"{C.DIM}[{RARITY_LABELS.get(loot.rarity, loot.rarity)}]{C.RESET}")
        if loot.base_value > 0:
            print(f"  {C.DIM}Worth roughly {loot.base_value}gp{C.RESET}")
        if player.can_carry():
            pick = prompt_choice(["Take it", "Leave it"])
            if pick == 1:
                player.add_item(loot)
                print(f"  {C.BGREEN}Taken.{C.RESET}")
        else:
            print(f"  {C.BRED}Bag full — left behind.{C.RESET}")
    else:
        print(f"\n  {C.DIM}Nothing worth taking here.{C.RESET}")

    pause()


# ── Main screen ───────────────────────────────────────────────────────────────

def burglary_screen(player: Player) -> None:
    """Entry point — location select, lockpick, room loop."""
    from engine.pickpocket import _caught_screen

    city_key  = player.current_city
    stealth   = player.skill("Stealth")
    is_wanted = city_key in player.city_wanted

    # ── Wanted check ─────────────────────────────────────────────────────────
    clear()
    title_screen("BURGLARY")

    if is_wanted:
        print(f"\n  {C.BRED}You're wanted here. Working the buildings is suicide right now.{C.RESET}")
        pause()
        return

    # ── Check for lockpicks ───────────────────────────────────────────────────
    n_picks = sum(1 for i in player.inventory if i.name == "Lock Picks")
    if n_picks == 0:
        print(f"\n  {C.BYELLOW}You have no Lock Picks.{C.RESET}")
        print(f"  {C.DIM}Buy some from a merchant before trying this.{C.RESET}")
        pause()
        return

    print(f"\n  {C.DIM}You scan the street. Every building has a price.{C.RESET}")
    print(f"  {C.DIM}Lock Picks: {n_picks}  |  Stealth: {stealth}{C.RESET}")
    print()

    # ── Location select ───────────────────────────────────────────────────────
    available = [loc for loc in BURGLARY_LOCATIONS if stealth >= loc["min_stealth"]]
    if not available:
        print(f"  {C.BBLACK}You don't move quietly enough to case any building here yet.{C.RESET}")
        print(f"  {C.DIM}(Requires at least 10 Stealth){C.RESET}")
        pause()
        return

    loc_options = []
    for loc in available:
        catch = loc["catch_pct"]
        loc_options.append(
            f"{loc['name']}  "
            f"{C.DIM}(base catch: {catch}%  |  loot: {loc['loot_bias']}){C.RESET}"
        )
    loc_options.append(f"{C.BBLACK}← Back{C.RESET}")

    choice = prompt_choice(loc_options, "Case which building?")
    if choice == len(loc_options):
        return

    location  = available[choice - 1]
    catch_pct = location["catch_pct"]

    # ── Approach and lock ─────────────────────────────────────────────────────
    clear()
    title_screen(location["name"].upper())
    print(f"\n  {C.DIM}{location['flavour']}{C.RESET}")
    print()
    print(f"  {C.DIM}Catch chance: {catch_pct}%  |  Picks remaining: {n_picks}{C.RESET}")
    print()

    approach = prompt_choice([
        "Pick the lock     (use a Lock Pick)",
        f"{C.BBLACK}← Back{C.RESET}",
    ], "Your move")
    if approach == 2:
        return

    # ── Lockpicking loop ──────────────────────────────────────────────────────
    opened = False
    while True:
        n_picks = sum(1 for i in player.inventory if i.name == "Lock Picks")
        if n_picks == 0:
            print(f"\n  {C.BRED}You're out of Lock Picks. The door stays shut.{C.RESET}")
            pause()
            return

        success = _lockpick_attempt(player)
        if success:
            opened = True
            break

        # Failed attempt — check if player wants to retry
        n_picks = sum(1 for i in player.inventory if i.name == "Lock Picks")
        if n_picks == 0:
            print(f"\n  {C.BRED}No picks left. You slip away empty-handed.{C.RESET}")
            pause()
            return

        retry = prompt_choice([
            f"Try again  {C.DIM}({n_picks} pick{'s' if n_picks != 1 else ''} remaining){C.RESET}",
            f"{C.BBLACK}← Abandon{C.RESET}",
        ], "The lock holds.")
        if retry == 2:
            print(f"\n  {C.DIM}You pull back and vanish into the street.{C.RESET}")
            pause()
            return

    if not opened:
        return

    # ── Inside — search loop ──────────────────────────────────────────────────
    spots   = list(location["spots"])
    visited = set()

    while spots:
        clear()
        title_screen(f"{location['name'].upper()} — INSIDE")
        print(f"\n  {C.DIM}You're in. Every minute raises the risk.{C.RESET}")
        print(f"  {C.DIM}Current catch chance: {catch_pct}%{C.RESET}")
        print()

        # Check if caught on entry/move
        if random.randint(1, 100) <= catch_pct:
            _trigger_caught(player, city_key, location, catch_pct)
            return

        spot_opts = [
            f"{name}  {C.DIM}{flavour[:50]}...{C.RESET}" if len(flavour) > 50
            else f"{name}  {C.DIM}{flavour}{C.RESET}"
            for name, flavour in spots
        ]
        spot_opts.append(f"{C.BBLACK}← Get out{C.RESET}")

        spot_choice = prompt_choice(spot_opts, "Where do you look?")
        if spot_choice == len(spot_opts):
            print(f"\n  {C.DIM}You slip back out the way you came.{C.RESET}")
            pause()
            return

        name, flavour = spots.pop(spot_choice - 1)
        _search_spot(player, name, flavour, location["loot_bias"])

        # Raise catch chance after each search
        catch_pct = min(95, catch_pct + location["catch_step"])

    # All spots searched
    clear()
    print(f"\n  {C.DIM}You've swept the place. Time to go.{C.RESET}")
    pause()


def _trigger_caught(player: Player, city_key: str, location: dict, catch_pct: int) -> None:
    """Called when the player is caught inside a building."""
    from engine.pickpocket import _caught_screen

    mark_name = "City Guard" if location["connected"] else "Building Owner"
    clear()
    title_screen("CAUGHT")
    print(f"\n  {C.BRED}A noise. Footsteps. Light under the door.{C.RESET}")
    if location["name"] == "The Castle":
        print(f"  {C.BRED}The guard patrol is early. You have seconds.{C.RESET}")
    elif location["connected"]:
        print(f"  {C.BRED}Someone important just walked in.{C.RESET}")
    else:
        print(f"  {C.BYELLOW}The owner is home.{C.RESET}")
    pause()

    _caught_screen(player, city_key, mark_name, location["connected"], gold_stolen=0)
