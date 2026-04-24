"""
Equipment, inventory, and bag screens — gear, grimtotems, consumables, journal, skill guide.
"""

import time

from engine.player   import Player, MAX_INVENTORY
from engine.items_use import use_item_outside_combat, USABLE_EFFECTS_OUTSIDE_COMBAT
from ui.display      import (
    C, RARITY_COLOR,
    clear, pause, hr, section, title_screen, prompt_choice,
    item_line, rarity_tag, show_journal, play_melody, typewrite,
)

SKILL_GUIDE = {
    "Merchantilism": (
        "Governs your ability to turn a profit at every stall and counter. "
        "A higher score earns better sell prices and unlocks sharper buy discounts through negotiation. "
        "City merchants respect a face that knows the value of things."
    ),
    "Speechcraft": (
        "Your tongue is a tool as much as any blade. Speechcraft opens dialogue options with strangers, "
        "smooths over hostile encounters, and improves how NPCs read your intent. "
        "A skilled speaker can talk their way out of situations a fighter cannot."
    ),
    "Martial": (
        "Raw combat ability — how hard you hit, how reliably you connect, and how well you absorb punishment. "
        "Martial governs your attack roll, your base defense, and the power of physical weapon moves. "
        "Every fighter on the road has some. Not all have enough."
    ),
    "Magic": (
        "Determines your mana pool and whether you can cast the spells you've learned. "
        "High Magic does not grant new spells on its own — spells must be purchased via Grimtotems. "
        "What Magic does is make those spells hit harder and sustain longer. "
        "Unarmoured mages receive a passive bonus."
    ),
    "Stealth": (
        "Governs your ability to move unseen and strike first. "
        "Used when attempting to enter caves and castles undetected — at low skill, success is rare. "
        "Also boosts the power of the Snipe bow move, and improves your chance of escaping from combat. "
        "Low stealth means enemies hear you coming."
    ),
    "Survival": (
        "The road is long and unkind. Survival reduces the chance of wilderness events catching you off guard, "
        "improves your foraging results and success rate, boosts your initiative roll, "
        "and synergises with Pot Shot for bowmen. High Survival means the wilds feel less hostile."
    ),
    "Dungeoneering": (
        "Experience with caves, ruins, and the things that live in them. "
        "Scouting a location before you enter draws on Dungeoneering — high skill gives you an accurate "
        "enemy count; low skill leaves you guessing. Also governs trap awareness and unlocks certain "
        "exploration choices inside locations."
    ),
}


def read_grimtotem(player: Player, item) -> bool:
    """
    Let the player read a grimtotem and decide whether to learn the spell.
    Returns True if the spell was learned (item should be removed from inventory).
    """
    from data.spells import SPELLS
    spell_name = item.spell_name
    spell      = SPELLS.get(spell_name)
    if not spell:
        print(f"\n  {C.BRED}This tome is unreadable.{C.RESET}")
        pause()
        return False

    clear()
    title_screen(f"GRIMTOTEM — {item.name.upper()}")
    print()
    print(f"  {C.BYELLOW}{spell_name}{C.RESET}")
    print(f"  {C.DIM}{spell['description']}{C.RESET}")
    print()
    hr("─")
    print()
    for line in spell["lore"].split("\n"):
        typewrite(line)
        print()
    print()
    hr("─")
    print()

    if spell_name in player.learned_spells:
        print(f"  {C.BBLACK}You already know this spell. The words offer nothing new.{C.RESET}")
        pause()
        return False

    if player.skill("Magic") < spell["require_magic"]:
        print(f"  {C.BRED}Your Magic ({player.skill('Magic')}) is too low to attempt this spell.")
        print(f"  Requires: {spell['require_magic']}.{C.RESET}")
        print(f"  {C.DIM}The words shimmer, then blur. Perhaps in time.{C.RESET}")
        pause()
        return False

    options = [
        f"{C.BGREEN}Yes — commit it to memory{C.RESET}",
        f"{C.BBLACK}No, this reads like gibberish{C.RESET}",
    ]
    choice = prompt_choice(options, "Does this magic resonate with you?")
    if choice == 1:
        player.learned_spells.append(spell_name)
        tier_label = spell["tier"].capitalize()
        entry = (
            f"[GRIMTOTEM LEARNED: {spell_name}]  ({tier_label})\n"
            f"{spell['description']}\n\n"
            + spell["lore"]
        )
        if entry not in player.journal:
            player.journal.append(entry)
        play_melody("journal_entry")
        print()
        print(f"  {C.BGREEN}You commit the spell to memory. It is yours now.{C.RESET}")
        print(f"  {C.DIM}The grimtotem crumbles to ash in your hands.{C.RESET}")
        pause()
        return True
    else:
        print(f"\n  {C.DIM}You close the tome. The words meant nothing to you today.{C.RESET}")
        pause()
        return False


def equip_screen(player: Player):
    """Let the player equip or unequip items from their inventory."""
    SLOT_LABELS = {
        "weapon":   "Weapon",
        "armor":    "Armour",
        "ring":     "Ring",
        "necklace": "Necklace",
    }
    SLOT_ORDER = ["weapon", "armor", "ring", "necklace"]

    while True:
        clear()
        title_screen("EQUIPMENT")

        section("EQUIPPED")
        for slot in SLOT_ORDER:
            item  = player.equipped.get(slot)
            label = SLOT_LABELS[slot]
            if item:
                color   = RARITY_COLOR.get(item.rarity, C.WHITE)
                bonuses = ""
                if item.stat_bonuses:
                    parts   = [f"{'+' if v >= 0 else ''}{v} {k}" for k, v in item.stat_bonuses.items()]
                    bonuses = f"  {C.DIM}({', '.join(parts)}){C.RESET}"
                curse_tag = f"  {C.BRED}[CURSED]{C.RESET}" if item.cursed else ""
                print(f"  {C.BCYAN}{label:<10}{C.RESET}  {color}{item.name}{C.RESET}{bonuses}{curse_tag}")
            else:
                print(f"  {C.BCYAN}{label:<10}{C.RESET}  {C.BBLACK}— empty —{C.RESET}")

        equippable      = [i for i in player.inventory if i.item_type in ("weapon", "armor", "ring", "necklace")]
        grimtotems      = [i for i in player.inventory if i.item_type == "grimtotem"]
        equipped_filled = [s for s in SLOT_ORDER if player.equipped.get(s)]

        options = []
        for item in equippable:
            color     = RARITY_COLOR.get(item.rarity, C.WHITE)
            curse_tag = f"  {C.BRED}[CURSED]{C.RESET}" if item.cursed else ""
            if item.armor_value:
                stat_hint = f"  {C.DIM}(def +{item.armor_value}){C.RESET}"
            elif item.stat_bonuses:
                parts     = [f"{'+' if v >= 0 else ''}{v} {k}" for k, v in item.stat_bonuses.items()]
                stat_hint = f"  {C.DIM}({', '.join(parts)}){C.RESET}"
            else:
                stat_hint = ""
            options.append(
                f"Equip  {color}{item.name}{C.RESET}  "
                f"[{item.item_type}]{stat_hint}{curse_tag}"
            )
        n_equip = len(options)

        for gt in grimtotems:
            color  = RARITY_COLOR.get(gt.rarity, C.WHITE)
            known  = gt.spell_name in player.learned_spells if gt.spell_name else False
            suffix = f"  {C.BBLACK}(already known){C.RESET}" if known else ""
            options.append(f"Read   {color}{gt.name}{C.RESET}  {C.DIM}[grimtotem]{C.RESET}{suffix}")
        n_grimtotem = len(grimtotems)

        for slot in equipped_filled:
            item = player.equipped[slot]
            color = RARITY_COLOR.get(item.rarity, C.WHITE)
            options.append(
                f"Unequip  {color}{item.name}{C.RESET}  "
                f"{C.DIM}[{slot}]{C.RESET}"
            )

        options.append(f"{C.BBLACK}← Back{C.RESET}")

        choice = prompt_choice(options, "Choose action")
        if choice == len(options):
            return

        if choice > n_equip and choice <= n_equip + n_grimtotem:
            gt      = grimtotems[choice - n_equip - 1]
            learned = read_grimtotem(player, gt)
            if learned:
                player.remove_item(gt)
            continue

        if choice <= n_equip:
            item = equippable[choice - 1]
            if item.cursed:
                _curse_desc = {
                    "reduce_max_hp": "reduces your maximum HP by 20",
                    "drain_hp":      "drains HP each round in combat",
                }.get(item.curse_effect or "", "applies a harmful enchantment")
                clear()
                print(f"\n  {C.BRED}{C.BOLD}⚠  This item is CURSED!{C.RESET}")
                print(f"  {C.BRED}{item.name}{C.RESET}{C.DIM}: {_curse_desc}.{C.RESET}")
                if item.stat_bonuses:
                    _parts = [f"{'+' if v >= 0 else ''}{v} {k}" for k, v in item.stat_bonuses.items()]
                    print(f"  {C.DIM}Bonuses: {', '.join(_parts)}{C.RESET}")
                print()
                confirm = prompt_choice([
                    f"Equip anyway  {C.BRED}(accept the curse){C.RESET}",
                    "Cancel",
                ])
                if confirm == 2:
                    continue

            prev_max_hp = player.max_hp
            prev = player.equip(item)
            player.remove_item(item)
            if prev:
                player.add_item(prev)
                print(f"\n  {C.BGREEN}Equipped {item.name}.")
                print(f"  {prev.name} returned to inventory.{C.RESET}")
            else:
                print(f"\n  {C.BGREEN}Equipped {item.name}.{C.RESET}")
            if item.cursed and item.curse_effect == "reduce_max_hp" and player.max_hp < prev_max_hp:
                print(f"  {C.BRED}Curse applied: Max HP {prev_max_hp} → {player.max_hp}.{C.RESET}")
            time.sleep(1.0)

        else:
            slot_idx = choice - n_equip - 1
            slot     = equipped_filled[slot_idx]
            if not player.can_carry():
                print(f"\n  {C.BRED}Inventory full. Drop an item before unequipping.{C.RESET}")
            else:
                item = player.unequip(slot)
                if item:
                    player.add_item(item)
                    print(f"\n  {C.DIM}Unequipped {item.name} → inventory.{C.RESET}")
            time.sleep(0.8)


def use_items_screen(player: Player):
    """Let the player use consumables outside of combat (road / bag screen)."""
    while True:
        usable = [
            i for i in player.inventory
            if (i.item_type in ("potion", "consumable"))
            and (i.effect in USABLE_EFFECTS_OUTSIDE_COMBAT)
        ]

        clear()
        section("USE ITEM")
        print()

        if not usable:
            print(f"  {C.BBLACK}You have no usable items in your pack.{C.RESET}")
            print()
            pause()
            return

        options = []
        for item in usable:
            color = RARITY_COLOR.get(item.rarity, C.WHITE)
            options.append(
                f"{color}{item.name}{C.RESET}  "
                f"{C.DIM}{item.description}{C.RESET}"
            )
        options.append(f"{C.BBLACK}← Back{C.RESET}")

        choice = prompt_choice(options, "Use which item?")
        if choice == len(options):
            return

        item = usable[choice - 1]
        msg  = use_item_outside_combat(player, item)
        player.remove_item(item)
        print(f"\n  {C.BGREEN}{msg}{C.RESET}")
        print(f"  {C.DIM}HP: {player.hp}/{player.max_hp}{C.RESET}")
        pause("Press Enter to continue...")


def show_skill_guide():
    """Display a full conceptual reference for all 7 skills."""
    clear()
    title_screen("SKILL GUIDE")
    print(f"  {C.DIM}A reference for what each skill governs. No numbers — just what it means to invest.{C.RESET}")
    print()
    hr()
    for skill, desc in SKILL_GUIDE.items():
        print(f"  {C.BCYAN}{C.BOLD}{skill}{C.RESET}")
        words = desc.split()
        line  = "  "
        for word in words:
            if len(line) + len(word) + 1 > 74:
                print(f"{C.DIM}{line}{C.RESET}")
                line = "  " + word + " "
            else:
                line += word + " "
        if line.strip():
            print(f"{C.DIM}{line}{C.RESET}")
        print()
    hr()
    pause()


def show_inventory_screen(player: Player):
    """Show full inventory with lore fragments."""
    clear()
    section("INVENTORY")
    print()
    if not player.inventory:
        print(f"  {C.BBLACK}(empty){C.RESET}")
    else:
        for i, item in enumerate(player.inventory, 1):
            print(f"  {C.DIM}{i:2}.{C.RESET}  {item_line(item)}")
            if item.lore:
                print(f"       {C.BBLACK}\"{item.lore}\"{C.RESET}")
    print()
    print(f"  {C.DIM}Carrying {len(player.inventory)}/{MAX_INVENTORY} items{C.RESET}")
    print()
    pause()


def bag_screen(player: Player):
    """Single access point for Gear, Inventory, Journal, Skill Guide, and item use."""
    while True:
        journal_ct = len(player.journal)
        j_hint     = f"{C.DIM}({journal_ct} entr{'y' if journal_ct == 1 else 'ies'}){C.RESET}"
        inv_hint   = f"{C.DIM}({len(player.inventory)}/{MAX_INVENTORY} items){C.RESET}"
        usable_ct  = sum(
            1 for i in player.inventory
            if i.item_type in ("potion", "consumable") and i.effect
        )
        use_hint = f"  {C.BYELLOW}({usable_ct} usable){C.RESET}" if usable_ct else ""
        clear()
        section("BAG")
        print()
        choice = prompt_choice([
            f"Gear        {C.DIM}(equipped items, grimtotems){C.RESET}",
            f"Inventory   {inv_hint}",
            f"Use Item    {C.DIM}(potions, bandages, rations){C.RESET}{use_hint}",
            f"Journal     {j_hint}",
            f"Skill Guide {C.DIM}(what each skill governs){C.RESET}",
            f"{C.BBLACK}Back{C.RESET}",
        ])
        if choice == 1:
            equip_screen(player)
        elif choice == 2:
            show_inventory_screen(player)
        elif choice == 3:
            use_items_screen(player)
        elif choice == 4:
            show_journal(player)
        elif choice == 5:
            show_skill_guide()
        else:
            return
