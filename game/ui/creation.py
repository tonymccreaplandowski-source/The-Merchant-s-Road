"""
Character creation screens — class selection and skill allocation.
"""

import random

from engine.player import (
    Player, create_player, SKILLS, SKILL_DESCRIPTIONS,
    STARTING_POINTS, MIN_SKILL, MAX_INVENTORY, MAX_CREATION_SKILL, DOMINANT_SKILL_VALUE,
)
from data.classes import CLASS_CHOICES
from data.items import WEAPON_ITEMS, TRADE_ITEMS, ITEM_LOOKUP
from ui.display import (
    C, clear, pause, hr, title_screen, prompt_choice, typewrite,
)


def class_selection_screen() -> dict:
    """
    Display class selection. Returns the chosen class dict.
    Shows all 21 classes in pages of 7, with confirm step.
    """
    PAGE_SIZE = 7
    page      = 0
    total     = len(CLASS_CHOICES)
    pages     = (total + PAGE_SIZE - 1) // PAGE_SIZE

    while True:
        clear()
        title_screen("CHOOSE YOUR CLASS")
        start = page * PAGE_SIZE
        chunk = CLASS_CHOICES[start:start + PAGE_SIZE]

        print(f"  {C.DIM}Page {page + 1}/{pages}   Each class sets two dominant skills to {DOMINANT_SKILL_VALUE}.{C.RESET}")
        print()

        options = []
        for cls in chunk:
            s1, s2 = cls["skills"]
            options.append(
                f"{C.BYELLOW}{cls['name']:<14}{C.RESET}  "
                f"{C.BCYAN}{s1}{C.RESET} + {C.BCYAN}{s2}{C.RESET}"
            )
        if page < pages - 1:
            options.append(f"{C.DIM}Next page →{C.RESET}")
        if page > 0:
            options.append(f"{C.DIM}← Previous page{C.RESET}")

        choice = prompt_choice(options, "Select class (or page)")

        if page < pages - 1 and choice == len(options) - (1 if page > 0 else 0):
            page += 1
            continue
        if page > 0 and choice == len(options):
            page -= 1
            continue

        cls = chunk[choice - 1]
        clear()
        title_screen(cls["name"].upper())
        print()
        s1, s2 = cls["skills"]
        print(f"  {C.BCYAN}Dominant skills:{C.RESET}  {C.BYELLOW}{s1}{C.RESET} {DOMINANT_SKILL_VALUE}  +  {C.BYELLOW}{s2}{C.RESET} {DOMINANT_SKILL_VALUE}")
        print()
        hr("─")
        print()
        for line in cls["lore"]:
            print(f"  {C.DIM}\"{line}\"{C.RESET}")
        print()
        hr("─")
        print()
        print(f"  {C.DIM}After choosing, you will distribute {STARTING_POINTS - DOMINANT_SKILL_VALUE * 2} points")
        print(f"  across your remaining 5 skills (min {MIN_SKILL}, max {MAX_CREATION_SKILL} each).{C.RESET}")
        print()

        confirm = prompt_choice([
            f"{C.BGREEN}Choose {cls['name']}{C.RESET}",
            f"{C.BBLACK}Go back{C.RESET}",
        ], "Confirm?")

        if confirm == 1:
            return cls


def character_creation() -> Player:
    clear()
    title_screen("CHARACTER CREATION")

    print(f"  {C.DIM}Before you set foot on the road, tell us who you are.{C.RESET}")
    print()

    while True:
        name = input(f"  {C.BCYAN}Your name: {C.RESET}").strip()
        if name:
            break
        name = "Traveller"
        break

    chosen_class          = class_selection_screen()
    dominant_s1, dominant_s2 = chosen_class["skills"]

    allocations = {skill: MIN_SKILL for skill in SKILLS}
    allocations[dominant_s1] = DOMINANT_SKILL_VALUE
    allocations[dominant_s2] = DOMINANT_SKILL_VALUE

    minor_skills = [s for s in SKILLS if s not in (dominant_s1, dominant_s2)]
    free_points  = STARTING_POINTS - DOMINANT_SKILL_VALUE * 2
    remaining    = free_points

    clear()
    title_screen(f"{chosen_class['name'].upper()} — SKILL ALLOCATION")
    print(f"  {C.BYELLOW}{dominant_s1}{C.RESET} and {C.BYELLOW}{dominant_s2}{C.RESET} are set to {DOMINANT_SKILL_VALUE} each.")
    print()
    print(f"  {C.DIM}Distribute {C.RESET}{C.BYELLOW}{free_points}{C.RESET}{C.DIM} points across your remaining 5 skills.")
    print(f"  Minimum per skill: {MIN_SKILL}    Maximum per skill: {MAX_CREATION_SKILL}  {C.RESET}{C.DIM}(skills can exceed this through play){C.RESET}")
    print()

    for skill in minor_skills:
        print(f"  {C.BCYAN}{skill:<16}{C.RESET}  {C.DIM}{SKILL_DESCRIPTIONS[skill]}{C.RESET}")
    print()

    for i, skill in enumerate(minor_skills):
        is_last = (i == len(minor_skills) - 1)
        while True:
            if is_last:
                auto = max(MIN_SKILL, min(MAX_CREATION_SKILL, remaining))
                print(f"  {C.BCYAN}{skill:<16}{C.RESET}  → auto-assigned {C.BYELLOW}{auto}{C.RESET} (remaining points)")
                allocations[skill] = auto
                remaining -= auto
                break
            try:
                max_allowed = min(MAX_CREATION_SKILL, remaining - MIN_SKILL * (len(minor_skills) - i - 1))
                print(f"  {C.DIM}Remaining: {remaining}  |  Min: {MIN_SKILL}  Max here: {max_allowed}{C.RESET}")
                raw = input(f"  {C.BCYAN}{skill:<16}{C.RESET}  → ").strip()
                val = int(raw)
                if val < MIN_SKILL:
                    print(f"  {C.RED}Minimum is {MIN_SKILL}.{C.RESET}")
                elif val > max_allowed:
                    print(f"  {C.RED}Maximum here is {max_allowed}.{C.RESET}")
                else:
                    allocations[skill] = val
                    remaining -= val
                    break
            except ValueError:
                print(f"  {C.RED}Please enter a whole number.{C.RESET}")

    player = create_player(name, allocations)

    common_weapons = [i for i in WEAPON_ITEMS if i.rarity == "common"]
    common_trade   = [i for i in TRADE_ITEMS   if i.rarity == "common"]

    starting_weapon = random.choice(common_weapons) if common_weapons else None
    health_potion   = ITEM_LOOKUP.get("Health Potion")
    starting_trade  = random.choice(common_trade)   if common_trade   else None

    for item in [starting_weapon, health_potion, starting_trade]:
        if item:
            player.add_item(item)

    if starting_weapon:
        player.equip(starting_weapon)
        player.remove_item(starting_weapon)

    print()
    print(f"  {C.BGREEN}✓ Character created!{C.RESET}  "
          f"{C.BYELLOW}{chosen_class['name']}{C.RESET}  —  "
          f"Total points spent: {sum(allocations.values())}")
    print(f"  {C.DIM}You begin in Rabenmark with {player.gold}gp.{C.RESET}")
    print()
    print(f"  {C.BYELLOW}Starting kit:{C.RESET}")
    if starting_weapon:
        print(f"    {C.BGREEN}Weapon{C.RESET}  — {starting_weapon.name} (equipped)")
    if health_potion:
        print(f"    {C.BGREEN}Potion{C.RESET}  — {health_potion.name}")
    if starting_trade:
        print(f"    {C.BGREEN}Goods{C.RESET}   — {starting_trade.name}  ({starting_trade.base_value}gp base)")

    pause("Press Enter to enter the world...")
    return player
