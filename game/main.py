"""
The Merchant's Road — Main game loop.

Run with:  python main.py
"""

import sys
import time
import random

from engine.player  import Player, create_player, SKILLS, SKILL_DESCRIPTIONS, STARTING_POINTS, MIN_SKILL, MAX_INVENTORY
from engine.world   import start_travel, take_road_step, abort_travel
from engine.combat  import (
    fresh_state, roll_initiative, calculate_damage,
    apply_move_special, enemy_attack, cast_spell, attempt_flee,
)
from engine.loot    import generate_loot
from engine.events  import get_event_enemies
from data.cities    import CITIES, get_adjacent_city_keys
from data.weapons   import MOVES
from data.spells    import get_available_spells
from data.items     import (
    WEAPON_ITEMS, ARMOR_ITEMS, ACCESSORY_ITEMS, POTION_ITEMS,
    SUPPLY_ITEMS, TRADE_ITEMS, get_items_by_rarity, ITEM_LOOKUP,
)
from ui.display     import (
    C, RARITY_COLOR, BIOME_COLOR,
    clear, pause, hr, section, title_screen,
    prompt_choice, item_line, rarity_tag,
    show_world_map, show_combat_screen, show_character_sheet,
    skill_bar, hp_bar, mana_bar, beep, play_melody,
    typewrite, show_journal,
    start_ambient_loop, stop_ambient_loop,
)


# ════════════════════════════════════════════════════════════════
#   HELPERS
# ════════════════════════════════════════════════════════════════

def _sell_price(item, city, discount: float = 1.0) -> int:
    """65% of base value, modified by city scarcity/abundance.
    discount < 1.0 means a successful negotiate improved the deal.
    For selling, a discount of 0.85 → sell bonus multiplier of 1.15.
    """
    sell_mult = 2.0 - discount   # 0.85 buy disc → 1.15 sell bonus; 1.0 → 1.0
    return max(1, round(item.base_value * city.price_modifier(item.name) * 0.65 * sell_mult))


def _buy_price(item, city, discount: float = 1.0) -> int:
    """130% of base value, modified by city pricing and negotiate discount."""
    return max(1, round(item.base_value * city.price_modifier(item.name) * 1.30 * discount))


# ── Merchant constants ────────────────────────────────────────────────────────

MERCHANT_NAMES = [
    "Aldric", "Berwen", "Cade", "Drusilla", "Eamon", "Farren",
    "Gwenda", "Halsten", "Irja", "Jovan", "Kael", "Lidda",
    "Maren", "Nath", "Orla", "Pell", "Quelda", "Rowan",
    "Sable", "Torsten", "Ulric", "Veyra", "Westan", "Xanthe",
    "Yvor", "Zara", "Brand", "Corra", "Daven", "Elsin",
]

# Each merchant type: (type_label, tagline, item_pool_fn)
# item_pool_fn returns the candidate item list to sample from
def _pool_blacksmith():
    return [i for i in WEAPON_ITEMS + ARMOR_ITEMS if not i.cursed]

def _pool_apothecary():
    return list(POTION_ITEMS)

def _pool_librarian():
    from data.items import BOOK_ITEMS
    return list(BOOK_ITEMS)

def _pool_survival():
    return [i for i in SUPPLY_ITEMS if i.item_type in ("material", "consumable")]

def _pool_dungeoneering():
    from data.items import BOOK_ITEMS
    dung_names = {"Rope", "Grappling Hook", "Lock Picks", "Lantern",
                  "Tinderbox", "Torch Bundle", "Adventurer's Map"}
    return (
        [i for i in SUPPLY_ITEMS if i.name in dung_names]
        + [i for i in BOOK_ITEMS]
    )

def _pool_leatherworker():
    leather_armor = [i for i in ARMOR_ITEMS
                     if i.stat_bonuses and "Stealth" in i.stat_bonuses and not i.cursed]
    return leather_armor + [i for i in ACCESSORY_ITEMS if not i.cursed]

MERCHANT_TYPES = [
    # (type_label, tagline, pool_fn, leading_skill)
    ("Blacksmith",        "Soot-stained hands, straight talk, sharp steel.",     _pool_blacksmith,        "Martial"),
    ("Apothecary",        "Herbs and remedies for every road ailment.",           _pool_apothecary,        "Magic"),
    ("Librarian",         "Quiet, watchful, and oddly well-informed.",            _pool_librarian,         "Dungeoneering"),
    ("Survival Trader",   "Rations, rope, and everything the road demands.",      _pool_survival,          "Survival"),
    ("Dungeoneering Co.", "Lanterns, picks, and maps of the unseen places.",      _pool_dungeoneering,     "Dungeoneering"),
    ("Leatherworker",     "Soft goods for those who prefer to stay unnoticed.",   _pool_leatherworker,     "Stealth"),
]


def _generate_merchant(used_names: set) -> dict:
    """Spawn a single merchant with a random type and stock."""
    mtype_label, tagline, pool_fn, leading_skill = random.choice(MERCHANT_TYPES)

    # Pick a unique name
    available = [n for n in MERCHANT_NAMES if n not in used_names]
    name = random.choice(available) if available else random.choice(MERCHANT_NAMES)
    used_names.add(name)

    pool  = pool_fn()
    stock = random.sample(pool, min(5, len(pool))) if pool else []

    return {
        "name":          name,
        "type":          mtype_label,
        "tagline":       tagline,
        "leading_skill": leading_skill,
        "stock":         list(stock),
        "sold_items":    [],       # items the player sold — can be bought back
        "discount":      1.0,      # set by negotiate session (< 1.0 = cheaper prices)
    }


def generate_city_merchants(city_key: str) -> list:
    """Return 3 merchants for a city visit. Called once per visit."""
    used = set()
    return [_generate_merchant(used) for _ in range(3)]


def _training_cost(level: int) -> int:
    if level < 25:  return 20
    if level < 50:  return 55
    if level < 75:  return 130
    return 300


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


def use_potion(player: Player, potion, state: dict) -> str:
    """Apply a potion/consumable effect. Returns a flavour message string."""
    effect = potion.effect or ""
    if effect == "heal_30":
        before = player.hp
        player.heal(30)
        gained = player.hp - before
        return f"You drink the {potion.name}. +{gained} HP."
    if effect == "heal_20":
        before = player.hp
        player.heal(20)
        gained = player.hp - before
        return f"You use the {potion.name}. +{gained} HP."
    if effect == "heal_15":
        before = player.hp
        player.heal(15)
        gained = player.hp - before
        return f"You eat the {potion.name}. +{gained} HP."
    if effect == "mana_25":
        before = player.mana
        player.restore_mana(25)
        gained = player.mana - before
        return f"You drink the {potion.name}. +{gained} Mana."
    if effect == "str_boost":
        state["player_str_boost"] = True
        return f"You drink the {potion.name}. Combat power surges\!"
    if effect == "agi_boost":
        state["player_agi_boost"] = True
        return f"You drink the {potion.name}. You feel fleet-footed."
    if effect == "full_restore":
        player.heal(player.max_hp)
        player.restore_mana()
        return f"You drink the {potion.name}. HP and Mana fully restored\!"
    if effect == "map_bonus":
        player.map_bonus = True
        return f"You study the {potion.name}. Nearby locations will be easier to find."
    if effect == "torch":
        return f"You light the {potion.name}. The dark pulls back a little."
    return f"You use the {potion.name}."


# (generate_city_stock removed — replaced by generate_city_merchants above)


# ════════════════════════════════════════════════════════════════
#   CHARACTER CREATION
# ════════════════════════════════════════════════════════════════

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

    print()
    section("SKILL ALLOCATION")
    print(f"  {C.DIM}Distribute {C.RESET}{C.BYELLOW}{STARTING_POINTS}{C.RESET}{C.DIM} points across your 7 skills.")
    print(f"  Minimum per skill: {MIN_SKILL}    Maximum per skill: 100{C.RESET}")
    print()

    for skill in SKILLS:
        print(f"  {C.BCYAN}{skill:<16}{C.RESET}  {C.DIM}{SKILL_DESCRIPTIONS[skill]}{C.RESET}")
    print()

    allocations = {}
    remaining   = STARTING_POINTS

    for i, skill in enumerate(SKILLS):
        is_last = (i == len(SKILLS) - 1)
        while True:
            if is_last:
                auto = max(MIN_SKILL, min(100, remaining))
                print(f"  {C.BCYAN}{skill:<16}{C.RESET}  → auto-assigned {C.BYELLOW}{auto}{C.RESET} (remaining points)")
                allocations[skill] = auto
                remaining -= auto
                break
            try:
                max_allowed = min(100, remaining - MIN_SKILL * (len(SKILLS) - i - 1))
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

    # ── Starting items ──────────────────────────────────────────────────────
    # Give the player a small starting kit: 1 random common weapon,
    # 1 Health Potion, and 1 random common trade good.
    common_weapons = [i for i in WEAPON_ITEMS if i.rarity == "common"]
    common_trade   = [i for i in TRADE_ITEMS   if i.rarity == "common"]

    starting_weapon = random.choice(common_weapons) if common_weapons else None
    health_potion   = ITEM_LOOKUP.get("Health Potion")
    starting_trade  = random.choice(common_trade)   if common_trade   else None

    for item in [starting_weapon, health_potion, starting_trade]:
        if item:
            player.add_item(item)

    # Auto-equip the starting weapon
    if starting_weapon:
        player.equip(starting_weapon)
        player.remove_item(starting_weapon)

    print()
    print(f"  {C.BGREEN}✓ Character created\!{C.RESET}  "
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


# ════════════════════════════════════════════════════════════════
#   COMBAT
# ════════════════════════════════════════════════════════════════

def run_combat(player: Player, enemy) -> bool:
    """
    Full combat loop.
    Returns True if player wins, False if player fled or was killed.
    """
    state        = fresh_state()
    stop_ambient_loop()          # silence ambient while combat plays
    play_melody("combat_start")
    player_first = roll_initiative(player, enemy)

    if player_first:
        message = f"{enemy.description}\n  You win the initiative — you strike first\!"
    else:
        # Enemy attacks before the player's first turn
        e_dmg, e_move = enemy_attack(enemy, player, state)
        player.take_damage(e_dmg)
        if e_dmg == 0:
            message = f"{enemy.description}\n  {enemy.name} moves first but misses with {e_move}\!"
        else:
            message = (
                f"{enemy.description}\n"
                f"  {enemy.name} moves first\! {e_move} hits for "
                f"{C.BRED}{e_dmg}{C.RESET} damage."
            )
        beep("hit")
        if not player.is_alive():
            show_combat_screen(player, enemy, "You are struck down before you can act...")
            time.sleep(2)
            return False

    # ── Main combat loop ──────────────────────────────────────────────────────
    while player.is_alive() and enemy.is_alive():
        show_combat_screen(player, enemy, message)

        top = prompt_choice([
            f"{C.BOLD}Attack{C.RESET}   — weapon moves",
            f"{C.BBLUE}Cast{C.RESET}     — cast a spell",
            f"{C.BGREEN}Items{C.RESET}    — use a potion",
            f"{C.BBLACK}Flee{C.RESET}     — attempt to escape",
        ], "Choose action")

        action_taken = False

        # ── ATTACK ───────────────────────────────────────────────────────────
        if top == 1:
            moves        = player.combat_moves()
            move_options = []
            for mn in moves:
                move = MOVES[mn]
                # Effectiveness is intentionally NOT shown here — it reveals
                # itself in the result message after the strike lands.
                move_options.append(
                    f"{C.BOLD}{mn:<14}{C.RESET}  {C.DIM}{move['description']}{C.RESET}"
                )
            move_options.append(f"{C.BBLACK}← Back{C.RESET}")

            show_combat_screen(player, enemy, message)
            mc = prompt_choice(move_options, "Choose move")
            if mc == len(move_options):
                message = "You hold your ground."
                continue

            move_name = moves[mc - 1]
            dmg, label, is_crit, special_tag = calculate_damage(
                attacker_combat=player.skill("Martial"),
                defender_defense=enemy.defense_skill,
                move_name=move_name,
                armor_type=enemy.armor_type,
                player=player,
                state=state,
            )
            special_msg = apply_move_special(move_name, state, player, enemy)
            enemy.take_damage(dmg)

            if dmg == 0:
                message = f"You use {C.BOLD}{move_name}{C.RESET}\! Missed entirely\!"
            else:
                crit_str = f"  {C.BYELLOW}✦ CRITICAL\!{C.RESET}" if is_crit else ""
                message = (
                    f"You use {C.BOLD}{move_name}{C.RESET}\! It's {label}\! "
                    f"({C.BGREEN}{dmg}{C.RESET} dmg){crit_str}"
                )
            if special_tag:
                message += f"\n  [{special_tag}]"
            if special_msg:
                message += f"\n  {special_msg}"
            beep("attack")
            action_taken = True

        # ── CAST ─────────────────────────────────────────────────────────────
        elif top == 2:
            available = get_available_spells(player.skill("Magic"))
            if not available:
                message = "Your Magic skill is too low to cast any spells."
                continue

            spell_options = []
            spell_names   = list(available.keys())
            for sn in spell_names:
                sp   = available[sn]
                cost = max(0, sp["cost"] - player.mana_discount)
                if player.mana >= cost:
                    color = C.BBLUE
                    glyph = "✦"
                else:
                    color = C.BBLACK
                    glyph = "✗"
                spell_options.append(
                    f"{color}{glyph} {sn:<16}{C.RESET}  "
                    f"{C.DIM}Cost: {cost} mana  {sp['description']}{C.RESET}"
                )
            spell_options.append(f"{C.BBLACK}← Back{C.RESET}")

            show_combat_screen(player, enemy, message)
            sc = prompt_choice(spell_options, "Cast which spell?")
            if sc == len(spell_options):
                message = "You hold your focus."
                continue

            sname  = spell_names[sc - 1]
            spell  = available[sname]
            cost   = spell["cost"]

            if not player.spend_mana(cost):
                message = (
                    f"Not enough mana\! {sname} costs {cost}, "
                    f"you have {player.mana}."
                )
                continue

            dmg, label, stag = cast_spell(sname, player, enemy, state)

            if spell.get("damage_type") == "heal":
                message = f"You cast {C.BPURPLE}{sname}{C.RESET}\! You recover {C.BGREEN}{dmg}{C.RESET} HP."
                beep("heal")
            else:
                enemy.take_damage(dmg)
                message = (
                    f"You cast {C.BPURPLE}{sname}{C.RESET}\! It's {label}\! "
                    f"({C.BBLUE}{dmg}{C.RESET} magic damage)"
                )
                if stag:
                    message += f"\n  [{stag}]"
                beep("cast")
            action_taken = True

        # ── ITEMS ────────────────────────────────────────────────────────────
        elif top == 3:
            potions = [i for i in player.inventory if i.item_type == "potion"]
            if not potions:
                show_combat_screen(player, enemy, message)
                print(f"  {C.BRED}You're out of combat supplies.{C.RESET}")
                pause("Press Enter to return to combat...")
                continue

            pot_options = []
            for p in potions:
                pot_options.append(
                    f"{C.BGREEN}{p.name}{C.RESET}  {C.DIM}{p.description}{C.RESET}"
                )
            pot_options.append(f"{C.BBLACK}← Back{C.RESET}")

            show_combat_screen(player, enemy, message)
            pc = prompt_choice(pot_options, "Use which item?")
            if pc == len(pot_options):
                message = "You pocket your pack."
                continue

            chosen_potion = potions[pc - 1]
            result_msg    = use_potion(player, chosen_potion, state)
            player.remove_item(chosen_potion)
            message      = result_msg
            beep("heal")
            action_taken = True

        # ── FLEE ─────────────────────────────────────────────────────────────
        elif top == 4:
            if attempt_flee(player, enemy):
                show_combat_screen(player, enemy, "You slip away into the shadows.")
                beep("menu")
                time.sleep(1.5)
                start_ambient_loop()   # resume ambient on escape
                return False
            # Failed flee → enemy attacks this turn
            message      = "You couldn't escape\!"
            action_taken = True

        # ── Enemy counter-attack ──────────────────────────────────────────────
        if action_taken and enemy.is_alive() and player.is_alive():
            e_dmg, e_move = enemy_attack(enemy, player, state)
            player.take_damage(e_dmg)
            if e_dmg == 0:
                message += f"\n  {enemy.name} attacks with {e_move}\! (missed)"
            else:
                message += (
                    f"\n  {enemy.name} retaliates with {e_move} "
                    f"for {C.BRED}{e_dmg}{C.RESET} damage."
                )
            beep("hit")

    # ── Combat end ────────────────────────────────────────────────────────────
    if not player.is_alive():
        show_combat_screen(player, enemy, "You collapse. The world fades to black...")
        play_melody("death")
        time.sleep(2)
        return False

    show_combat_screen(player, enemy, f"Victory\! The {enemy.name} falls\!")
    play_melody("victory")
    time.sleep(1.5)
    start_ambient_loop()   # resume ambient after victory fanfare
    return True


# ════════════════════════════════════════════════════════════════
#   LOOT SCREEN
# ════════════════════════════════════════════════════════════════

def loot_screen(player: Player, enemy):
    loot = generate_loot(bias=enemy.loot_bias)
    clear()
    title_screen("LOOT")

    print(f"  {C.BGREEN}You search the fallen {enemy.name}...{C.RESET}")
    print()

    color = RARITY_COLOR.get(loot.rarity, C.WHITE)
    print(f"  Found:  {color}{C.BOLD}{loot.name}{C.RESET}  [{rarity_tag(loot.rarity)}]")
    print(f"  {C.DIM}{loot.description}{C.RESET}")
    print(f"  {C.BYELLOW}Base value: {loot.base_value}gp{C.RESET}")
    print()

    if not player.can_carry():
        print(f"  {C.BRED}Inventory full ({MAX_INVENTORY}/{MAX_INVENTORY})\! Can't carry more.{C.RESET}")
        pause()
        return

    choice = prompt_choice(["Take the item", "Leave it behind"])
    if choice == 1:
        player.add_item(loot)
        print(f"\n  {C.BGREEN}Added {loot.name} to your inventory.{C.RESET}")
    else:
        print(f"\n  {C.DIM}You leave it behind.{C.RESET}")
    time.sleep(0.8)


# ════════════════════════════════════════════════════════════════
#   EQUIPMENT SCREEN
# ════════════════════════════════════════════════════════════════

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

        # ── Current slots ─────────────────────────────────────────────────
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

        # ── Build option list ─────────────────────────────────────────────
        equippable = [i for i in player.inventory
                      if i.item_type in ("weapon", "armor", "ring", "necklace")]
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

        if choice <= n_equip:
            # ── Equip ─────────────────────────────────────────────────────
            item = equippable[choice - 1]
            if item.cursed:
                clear()
                print(f"\n  {C.BRED}{C.BOLD}⚠ This item is cursed\!{C.RESET}")
                print(f"  {C.DIM}{item.name} carries a dark enchantment. Equipping it may harm you.{C.RESET}")
                confirm = prompt_choice([
                    f"Equip anyway  {C.BRED}(accept the risk){C.RESET}",
                    "Cancel",
                ])
                if confirm == 2:
                    continue

            prev = player.equip(item)
            player.remove_item(item)
            if prev:
                player.add_item(prev)
                print(f"\n  {C.BGREEN}Equipped {item.name}.")
                print(f"  {prev.name} returned to inventory.{C.RESET}")
            else:
                print(f"\n  {C.BGREEN}Equipped {item.name}.{C.RESET}")
            time.sleep(1.0)

        else:
            # ── Unequip ───────────────────────────────────────────────────
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


# ════════════════════════════════════════════════════════════════
#   CITY — NEGOTIATE MINIGAME
# ════════════════════════════════════════════════════════════════

def _negotiate_skill_boost(player: Player, merchant: dict) -> int:
    """
    Calculate the flat bonus added to the player's roll each negotiate round.

    Skill boost tiers (per 1 skill point):
      Merchantilism  → 0.01  (full power:  skill 100 = +1.0 per point = +10 total / 10 points)
      Speechcraft    → 0.005 (half power:  skill 100 = +0.5)
      Other skills   → 0.001 (quarter pt:  skill 100 = +0.1 each)

    Exception: if the player's highest skill matches the merchant's leading skill,
    that skill is boosted to Merchantilism rate (0.01).

    Returns an integer bonus (rounded) to add to player_roll.
    """
    p_leading  = max(player.skills, key=lambda s: player.skills[s])
    m_leading  = merchant.get("leading_skill", "")

    boost = 0.0
    for skill_name in player.skills:
        val = player.skill(skill_name)
        if skill_name == "Merchantilism":
            boost += val * 0.01
        elif skill_name == "Speechcraft":
            boost += val * 0.005
        elif skill_name == p_leading and p_leading == m_leading:
            boost += val * 0.01   # matching leading skill = Merchantilism rate
        else:
            boost += val * 0.001
    return round(boost)


_TACTICS = [
    ("Appeal to shared interests", "Merchantilism",  "You invoke market wisdom and mutual benefit."),
    ("Flatter their craftsmanship", "Speechcraft",   "You compliment the quality of their wares."),
    ("Share a useful rumour",       "Dungeoneering",  "You offer a piece of valuable road knowledge."),
    ("Stand your ground",           "Martial",        "You let quiet confidence do the talking."),
]

def negotiate_session(player: Player, merchant: dict) -> float:
    """
    3-round negotiation minigame. Returns a price multiplier for this merchant.
    0.82 = 18% off (perfect),  0.90 = 10% off,  0.95 = 5% off,  1.0 = no change,
    1.08 = 8% premium (botched).
    Can only be run once per merchant — sets merchant["negotiated"] flag.
    """
    if merchant.get("negotiated"):
        disc = merchant["discount"]
        label = (
            f"{C.BGREEN}Already negotiated — {round((1 - disc)*100)}% discount active.{C.RESET}"
            if disc < 1.0 else
            f"{C.BRED}Already negotiated — they won't talk again.{C.RESET}"
        )
        clear()
        title_screen(f"NEGOTIATE — {merchant['name']}")
        print(f"\n  {label}")
        pause()
        return disc

    difficulty   = random.randint(28, 68)
    rounds_won   = 0
    round_log    = []

    for round_num in range(1, 4):
        clear()
        title_screen(f"NEGOTIATE — {merchant['name']}  ({merchant['type']})")
        print(f"  {C.DIM}\"{merchant['tagline']}\"{C.RESET}")
        m_lead = merchant.get("leading_skill", "")
        p_lead = max(player.skills, key=lambda s: player.skills[s])
        match_hint = (
            f"  {C.BGREEN}[Leading skill match: {m_lead}]{C.RESET}"
            if m_lead and p_lead == m_lead else
            f"  {C.DIM}[Their expertise: {m_lead}]{C.RESET}"
        )
        print(match_hint)
        print()
        if round_log:
            for log_line in round_log:
                print(f"  {log_line}")
            print()
        print(f"  {C.BYELLOW}Round {round_num}/3   Wins so far: {rounds_won}{C.RESET}")
        print()

        options = []
        for tactic_name, skill_name, _ in _TACTICS:
            val = player.skill(skill_name)
            options.append(
                f"{C.BOLD}{tactic_name:<32}{C.RESET}  "
                f"{C.DIM}[{skill_name}: {val}]{C.RESET}"
            )
        options.append(f"{C.BBLACK}← Walk away{C.RESET}")

        choice = prompt_choice(options, "Your approach")
        if choice == len(options):
            merchant["negotiated"] = True
            merchant["discount"]   = 1.0
            clear()
            print(f"\n  {C.DIM}You step back. The prices stay where they are.{C.RESET}")
            pause()
            return 1.0

        tactic_name, skill_name, flavour = _TACTICS[choice - 1]
        skill_val     = player.skill(skill_name)
        skill_boost   = _negotiate_skill_boost(player, merchant)
        player_roll   = random.randint(1, 20) + skill_val // 4 + skill_boost
        merchant_roll = random.randint(1, 20) + difficulty // 4

        boost_str = f"  {C.BBLUE}+{skill_boost} skill{C.RESET}" if skill_boost > 0 else ""
        if player_roll >= merchant_roll:
            rounds_won += 1
            round_log.append(
                f"{C.BGREEN}✓ Round {round_num}:{C.RESET} {flavour}{boost_str}  "
                f"{C.DIM}(rolled {player_roll} vs {merchant_roll}){C.RESET}"
            )
        else:
            round_log.append(
                f"{C.BRED}✗ Round {round_num}:{C.RESET} They hold firm.{boost_str}  "
                f"{C.DIM}(rolled {player_roll} vs {merchant_roll}){C.RESET}"
            )
        time.sleep(0.4)

    # ── Result ────────────────────────────────────────────────────────────
    clear()
    title_screen("NEGOTIATION RESULT")
    for log_line in round_log:
        print(f"  {log_line}")
    print()

    if rounds_won == 3:
        disc        = 0.82
        result_msg  = f"{C.BGREEN}Flawless. 18% discount secured for this merchant.{C.RESET}"
        play_melody("negotiate_win")
    elif rounds_won == 2:
        disc        = 0.90
        result_msg  = f"{C.BGREEN}Strong showing. 10% discount secured.{C.RESET}"
        play_melody("negotiate_win")
    elif rounds_won == 1:
        disc        = 0.95
        result_msg  = f"{C.BYELLOW}Partial win. 5% discount secured.{C.RESET}"
    else:
        disc        = 1.08
        result_msg  = f"{C.BRED}They're insulted. Prices are 8% higher now.{C.RESET}"
        play_melody("negotiate_lose")

    print(f"  {result_msg}")
    print(f"  {C.DIM}Rounds won: {rounds_won}/3{C.RESET}")
    merchant["discount"]   = disc
    merchant["negotiated"] = True
    pause()
    return disc


# ════════════════════════════════════════════════════════════════
#   CITY — MERCHANT SCREEN (single merchant)
# ════════════════════════════════════════════════════════════════

def merchant_screen(player: Player, city, merchant: dict):
    """Interact with a single named merchant — Sell / Buy / Negotiate / Leave."""
    while True:
        disc     = merchant.get("discount", 1.0)
        disc_str = (
            f"  {C.BGREEN}[{round((1 - disc)*100)}% discount active]{C.RESET}"
            if disc < 1.0 else
            f"  {C.BRED}[+{round((disc - 1)*100)}% premium]{C.RESET}"
            if disc > 1.0 else ""
        )

        clear()
        title_screen(f"{merchant['name'].upper()} — {merchant['type'].upper()}")
        print(f"  {C.DIM}\"{merchant['tagline']}\"{C.RESET}{disc_str}")
        print(f"  {C.DIM}[{city.biome.capitalize()} pricing]{C.RESET}")
        print()
        print(f"  {C.BYELLOW}Your gold: {player.gold}gp{C.RESET}  "
              f"{C.DIM}Bag: {len(player.inventory)}/{MAX_INVENTORY}{C.RESET}")
        print()

        neg_label = (
            f"Negotiate  {C.DIM}(prices already set){C.RESET}"
            if merchant.get("negotiated") else
            f"Negotiate  {C.DIM}(haggle for better prices){C.RESET}"
        )
        tab = prompt_choice([
            "Sell items",
            "Buy items",
            neg_label,
            "Leave",
        ])
        if tab == 4:
            return

        # ════ NEGOTIATE ═══════════════════════════════════════════════════
        if tab == 3:
            negotiate_session(player, merchant)
            continue

        # ════ SELL TAB ════════════════════════════════════════════════════
        if tab == 1:
            if not player.inventory:
                print(f"\n  {C.BBLACK}You have nothing to sell.{C.RESET}")
                pause("Press Enter to go back...")
                continue

            clear()
            title_screen(f"SELL — {merchant['name'].upper()}")
            print(f"  {C.BYELLOW}Gold: {player.gold}gp{C.RESET}")
            print()

            options = []
            for item in player.inventory:
                sp  = _sell_price(item, city, disc)
                mod = city.price_modifier(item.name)
                if mod > 1.0:
                    price_str = f"{C.BGREEN}{sp}gp ▲ (scarce){C.RESET}"
                elif mod < 1.0:
                    price_str = f"{C.BRED}{sp}gp ▼ (abundant){C.RESET}"
                else:
                    price_str = f"{C.WHITE}{sp}gp{C.RESET}"
                options.append(
                    f"{RARITY_COLOR.get(item.rarity, C.WHITE)}{item.name}{C.RESET}  "
                    f"{price_str}  {C.DIM}base {item.base_value}gp{C.RESET}"
                )
            options.append(f"{C.BBLACK}← Back{C.RESET}")

            choice = prompt_choice(options, "Sell which item?")
            if choice == len(options):
                continue

            item = player.inventory[choice - 1]
            sp   = _sell_price(item, city, disc)
            player.remove_item(item)
            player.gold += sp
            merchant["sold_items"].append(item)   # player can buy it back
            print(f"\n  {C.BGREEN}Sold {item.name} for {sp}gp.  Gold: {player.gold}gp{C.RESET}")
            time.sleep(0.9)

        # ════ BUY TAB ════════════════════════════════════════════════════
        elif tab == 2:
            all_buyable = merchant["stock"] + merchant["sold_items"]
            if not all_buyable:
                print(f"\n  {C.BBLACK}Nothing left in stock.{C.RESET}")
                pause("Press Enter to go back...")
                continue

            clear()
            title_screen(f"BUY — {merchant['name'].upper()}")
            print(f"  {C.BYELLOW}Gold: {player.gold}gp{C.RESET}  "
                  f"{C.DIM}Bag: {len(player.inventory)}/{MAX_INVENTORY}{C.RESET}")
            print()

            options = []
            for item in all_buyable:
                bp  = _buy_price(item, city, disc)
                mod = city.price_modifier(item.name)
                # Mark items sold back by the player
                is_sellback = item in merchant["sold_items"]
                tag = f"  {C.BYELLOW}[yours]{C.RESET}" if is_sellback else ""
                if mod < 1.0:
                    price_str = f"{C.BGREEN}{bp}gp ▼{C.RESET}"
                elif mod > 1.0:
                    price_str = f"{C.BRED}{bp}gp ▲{C.RESET}"
                else:
                    price_str = f"{C.WHITE}{bp}gp{C.RESET}"
                affordable = "" if player.gold >= bp else f"  {C.BRED}✗{C.RESET}"
                options.append(
                    f"{RARITY_COLOR.get(item.rarity, C.WHITE)}{item.name}{C.RESET}"
                    f"{tag}  {price_str}{affordable}  "
                    f"{C.DIM}{item.description[:40]}{C.RESET}"
                )
            options.append(f"{C.BBLACK}← Back{C.RESET}")

            choice = prompt_choice(options, "Buy which item?")
            if choice == len(options):
                continue

            item = all_buyable[choice - 1]
            bp   = _buy_price(item, city, disc)

            if player.gold < bp:
                print(f"\n  {C.RED}Not enough gold. Need {bp}gp, have {player.gold}gp.{C.RESET}")
                time.sleep(1.0)
            elif not player.can_carry():
                print(f"\n  {C.RED}Pack full ({MAX_INVENTORY}/{MAX_INVENTORY} items).{C.RESET}")
                time.sleep(1.0)
            else:
                player.gold -= bp
                player.add_item(item)
                # Remove from the correct list
                if item in merchant["sold_items"]:
                    merchant["sold_items"].remove(item)
                else:
                    merchant["stock"].remove(item)
                print(f"\n  {C.BGREEN}Bought {item.name} for {bp}gp. Gold: {player.gold}gp{C.RESET}")
                time.sleep(0.9)


# ════════════════════════════════════════════════════════════════
#   CITY — MARKET (choose from 3 merchants)
# ════════════════════════════════════════════════════════════════

# Module-level merchant cache. City key → list of merchant dicts.
# Cleared when the player leaves a city.
_city_merchants: dict = {}


def visit_market(player: Player, city):
    """Show the 3 merchants available this visit and let the player pick one."""
    global _city_merchants
    city_key = city.key

    # Generate merchants once per city visit
    if city_key not in _city_merchants:
        _city_merchants[city_key] = generate_city_merchants(city_key)

    merchants = _city_merchants[city_key]

    while True:
        clear()
        title_screen(f"THE MARKET — {city.name.upper()}")
        print(f"  {C.DIM}Three merchants have set up stalls today.{C.RESET}")
        print(f"  {C.BYELLOW}Your gold: {player.gold}gp{C.RESET}")
        print()

        options = []
        for m in merchants:
            disc     = m.get("discount", 1.0)
            neg_tag  = (
                f"  {C.BGREEN}[{round((1-disc)*100)}% off]{C.RESET}" if disc < 1.0 else
                f"  {C.BRED}[+{round((disc-1)*100)}% up]{C.RESET}"   if disc > 1.0 else ""
            )
            options.append(
                f"{C.BCYAN}{m['name']:<12}{C.RESET}  "
                f"{C.BOLD}{m['type']}{C.RESET}{neg_tag}  "
                f"{C.DIM}{m['tagline']}{C.RESET}"
            )
        options.append(f"{C.BBLACK}← Leave the market{C.RESET}")

        choice = prompt_choice(options, "Approach which merchant?")
        if choice == len(options):
            return

        merchant_screen(player, city, merchants[choice - 1])


# ════════════════════════════════════════════════════════════════
#   CITY — TRAINING
# ════════════════════════════════════════════════════════════════

def train_skills(player: Player):
    clear()
    title_screen("TRAINING HALL")
    print(f"  {C.DIM}A local master offers to sharpen your abilities.{C.RESET}")
    print(f"  {C.BYELLOW}Gold: {player.gold}gp{C.RESET}")
    print()

    section("CHOOSE A SKILL TO TRAIN")
    options = []
    for skill in SKILLS:
        current = player.skill(skill)
        cost    = _training_cost(current)
        bar     = skill_bar(current)
        if current >= 100:
            options.append(f"{C.BCYAN}{skill:<16}{C.RESET}  {bar}  {current}/100  {C.DIM}MAXED{C.RESET}")
        else:
            color = C.BGREEN if player.gold >= cost else C.BRED
            options.append(
                f"{C.BCYAN}{skill:<16}{C.RESET}  {bar}  {current}/100  "
                f"→ {color}{cost}gp{C.RESET}"
            )
    options.append(f"{C.BBLACK}← Leave{C.RESET}")

    choice = prompt_choice(options, "Train which skill?")
    if choice == len(options):
        return

    skill_name = SKILLS[choice - 1]
    current    = player.skill(skill_name)
    cost       = _training_cost(current)

    if current >= 100:
        print(f"\n  {C.RED}That skill is already at its peak.{C.RESET}")
    elif player.gold < cost:
        print(f"\n  {C.RED}Not enough gold. Need {cost}gp, have {player.gold}gp.{C.RESET}")
    else:
        player.gold -= cost
        player.train(skill_name)
        print(f"\n  {C.BGREEN}✓ {skill_name} improved to {current + 1}\!{C.RESET}")
    time.sleep(1.2)


# ════════════════════════════════════════════════════════════════
#   CITY — REST
# ════════════════════════════════════════════════════════════════

def rest_at_inn(player: Player):
    cost = 10
    if player.hp == player.max_hp and player.mana == player.max_mana:
        print(f"\n  {C.DIM}You're already at full health and mana. No need to rest.{C.RESET}")
    elif player.gold < cost:
        print(f"\n  {C.RED}Can't afford the inn. Need {cost}gp.{C.RESET}")
    else:
        player.gold -= cost
        player.heal(player.max_hp)
        player.restore_mana()
        print(f"\n  {C.BGREEN}You rest at the inn. HP and Mana fully restored. (−{cost}gp){C.RESET}")
    time.sleep(1.2)


# ════════════════════════════════════════════════════════════════
#   CITY — READ BOOK
# ════════════════════════════════════════════════════════════════

def read_book_menu(player: Player):
    """Let the player read a lore book from inventory, adding it to the journal."""
    books = [i for i in player.inventory if i.item_type == "book" and i.lore]
    if not books:
        clear()
        print(f"\n  {C.BBLACK}You have no books to read.{C.RESET}")
        pause()
        return

    while True:
        clear()
        title_screen("READ A BOOK")
        print(f"  {C.DIM}Reading a book adds its lore to your journal.{C.RESET}")
        print()

        options = []
        for b in books:
            already = b.lore in player.journal
            tag = f"  {C.BBLACK}[already read]{C.RESET}" if already else ""
            options.append(
                f"{RARITY_COLOR.get(b.rarity, C.WHITE)}{b.name}{C.RESET}"
                f"  {C.DIM}{b.description}{C.RESET}{tag}"
            )
        options.append(f"{C.BBLACK}← Back{C.RESET}")

        choice = prompt_choice(options, "Read which book?")
        if choice == len(options):
            return

        book = books[choice - 1]
        clear()
        title_screen(book.name.upper())
        print(f"  {C.DIM}\"{book.description}\"{C.RESET}")
        print()
        hr()
        print()
        # Typewrite the lore text
        words = book.lore.split()
        line  = ""
        for word in words:
            if len(line) + len(word) + 1 > 58:
                typewrite(line.strip())
                line = word + " "
            else:
                line += word + " "
        if line.strip():
            typewrite(line.strip())
        print()
        hr()

        if book.lore not in player.journal:
            player.journal.append(book.lore)
            play_melody("journal_entry")
            print(f"  {C.BYELLOW}✦ Lore added to your Journal.{C.RESET}")
        else:
            print(f"  {C.DIM}You've already noted this lore.{C.RESET}")

        pause()


# ════════════════════════════════════════════════════════════════
#   CITY LOOP
# ════════════════════════════════════════════════════════════════

def city_loop(player: Player):
    """Main city interaction loop. Exits when the player begins travelling."""
    global _city_merchants

    while True:
        city = CITIES[player.current_city]
        show_world_map(player)
        print(f"  {C.BCYAN}{C.BOLD}{city.name}{C.RESET}  {C.DIM}{city.description}{C.RESET}")
        print()
        section("WHAT WOULD YOU LIKE TO DO?")

        adjacent   = get_adjacent_city_keys(player.current_city)
        journal_ct = len(player.journal)
        journal_hint = (
            f"{C.DIM}({journal_ct} entr{'y' if journal_ct == 1 else 'ies'}){C.RESET}"
        )

        # Count unread books in inventory
        books_in_bag = [i for i in player.inventory if i.item_type == "book" and i.lore]
        book_hint = (
            f"  {C.BYELLOW}({len(books_in_bag)} unread){C.RESET}" if books_in_bag else ""
        )

        options = [
            f"The Market        {C.DIM}(3 merchants — buy, sell, negotiate){C.RESET}",
            f"Equipment         {C.DIM}(manage equipped items){C.RESET}",
            f"Training Hall     {C.DIM}(improve skills for gold){C.RESET}",
            f"Rest at the Inn   {C.DIM}(restore HP & mana — 10gp){C.RESET}",
            f"Character Sheet   {C.DIM}(stats, equipment, inventory){C.RESET}",
            f"Journal           {journal_hint}",
            f"Read a Book       {C.DIM}(add lore to your journal){C.RESET}{book_hint}",
        ]
        for dest_key in adjacent:
            dest       = CITIES[dest_key]
            road_color = BIOME_COLOR.get(dest.road_biome_east or dest.biome, C.WHITE)
            options.append(
                f"Travel to {C.BOLD}{dest.name}{C.RESET}  "
                f"{road_color}[{dest.biome} region]{C.RESET}"
            )
        options.append(f"{C.BBLACK}Quit{C.RESET}")

        choice = prompt_choice(options, "Your choice")
        n_base = 7   # 7 base options (market/equip/train/rest/char/journal/books)

        if choice == 1:
            visit_market(player, city)
        elif choice == 2:
            equip_screen(player)
        elif choice == 3:
            train_skills(player)
        elif choice == 4:
            rest_at_inn(player)
        elif choice == 5:
            show_character_sheet(player)
        elif choice == 6:
            show_journal(player)
        elif choice == 7:
            read_book_menu(player)
        elif choice <= n_base + len(adjacent):
            dest_key = adjacent[choice - n_base - 1]
            # Clear merchants for this city — they'll refresh next visit
            _city_merchants.pop(player.current_city, None)
            start_travel(player, dest_key)
            return   # hand off to road loop
        else:
            clear()
            print()
            print(f"  {C.BYELLOW}Farewell, {player.name}. May your purse stay heavy.{C.RESET}")
            print()
            sys.exit(0)


# ════════════════════════════════════════════════════════════════
#   SPECIAL EVENTS — CAVE & CASTLE
# ════════════════════════════════════════════════════════════════

def explore_event(player: Player, event):
    """Handle a cave or castle exploration event."""
    icon = "🕳" if event.event_type == "cave" else "🏰"
    play_melody("location_found")
    clear()
    print()
    print(f"  {C.BYELLOW}{icon}  {event.name.upper()}{C.RESET}")
    print()
    typewrite(event.description)
    print()

    choice = prompt_choice([
        f"Enter and explore  {C.DIM}(what lies within is unknown){C.RESET}",
        f"Pass by            {C.DIM}(continue on the road){C.RESET}",
    ])

    if choice == 2:
        print(f"\n  {C.DIM}You give it a wide berth and press on.{C.RESET}")
        time.sleep(0.8)
        return

    # ── Enter ─────────────────────────────────────────────────────────────────
    enemies   = get_event_enemies(event)
    loc_color = C.BBLACK if event.event_type == "cave" else C.BYELLOW
    clear()
    print()
    typewrite(f"You enter {event.name}...", indent=f"  {loc_color}")
    print(C.RESET, end="")
    time.sleep(0.8)

    for i, enemy in enumerate(enemies, 1):
        print(f"\n  {C.BRED}Enemy {i}/{len(enemies)}: {enemy.name} appears\!{C.RESET}")
        time.sleep(1.0)

        won = run_combat(player, enemy)

        if not player.is_alive():
            game_over(player)
            return

        if not won:
            print(f"\n  {C.BYELLOW}You retreat from {event.name}.{C.RESET}")
            time.sleep(1.0)
            return

    # ── All cleared — loot + lore ─────────────────────────────────────────────
    clear()
    print()
    print(f"  {C.BGREEN}{C.BOLD}You clear {event.name}\!{C.RESET}")
    print(f"  {C.DIM}You search the area carefully...{C.RESET}")
    time.sleep(1.2)

    for _ in range(2):
        loot  = generate_loot(bias=event.loot_bias)
        color = RARITY_COLOR.get(loot.rarity, C.WHITE)
        print(f"\n  Found: {color}{C.BOLD}{loot.name}{C.RESET}  [{rarity_tag(loot.rarity)}]  "
              f"{C.DIM}{loot.base_value}gp base{C.RESET}")
        if not player.can_carry():
            print(f"  {C.BRED}Inventory full — left behind.{C.RESET}")
            pause("Press Enter to continue...")
            continue
        pick = prompt_choice(["Take it", "Leave it"])
        if pick == 1:
            player.add_item(loot)
            print(f"  {C.BGREEN}Added to inventory.{C.RESET}")
        pause("Press Enter to continue...")

    # ── Lore doc drop ─────────────────────────────────────────────────────────
    if event.lore_text and event.lore_text not in player.journal:
        player.journal.append(event.lore_text)
        play_melody("journal_entry")
        print()
        hr("─")
        print(f"  {C.BYELLOW}✦ Journal updated{C.RESET}")
        print()
        typewrite(event.lore_text)
        print()
        hr("─")
        pause("Press Enter to continue...")   # give the player time to read


# ════════════════════════════════════════════════════════════════
#   ROAD LOOP
# ════════════════════════════════════════════════════════════════

CAMP_LIMIT = 2   # maximum camps allowed per road segment

def road_loop(player: Player):
    """Handle travel steps, encounters, and arrival."""
    while player.on_road:
        dest_name  = CITIES[player.road_destination].name
        road_biome = player.road_biome

        show_world_map(player)
        print(f"  {C.DIM}You press on through the {road_biome} toward {dest_name}.{C.RESET}")
        print()
        section("ROAD")

        camps_left  = CAMP_LIMIT - player.road_camps
        camp_plural = "s" if camps_left > 1 else ""
        if camps_left > 0:
            camp_label = f"Make camp  {C.DIM}(rest — restore 30 HP, {camps_left} camp{camp_plural} left){C.RESET}"
        else:
            camp_label = f"{C.BBLACK}Make camp  (no camps remaining this road){C.RESET}"

        options = [
            f"Press on      {C.DIM}(continue towards {dest_name}){C.RESET}",
            camp_label,
            f"Gear          {C.DIM}(manage equipped items on the road){C.RESET}",
            f"Journal       {C.DIM}({len(player.journal)} entr{'y' if len(player.journal) == 1 else 'ies'}){C.RESET}",
            f"Turn back     {C.DIM}(return to origin city){C.RESET}",
        ]
        choice = prompt_choice(options)

        # ── Camp ─────────────────────────────────────────────────────────
        if choice == 2:
            if player.road_camps >= CAMP_LIMIT:
                print(f"\n  {C.BRED}You've already camped twice on this stretch. Press on.{C.RESET}")
                time.sleep(1.2)
                continue
            player.road_camps += 1
            player.heal(30)
            player.restore_mana(15)
            print(f"\n  {C.BGREEN}You make camp and rest. +30 HP, +15 Mana. "
                  f"({player.road_camps}/{CAMP_LIMIT} camps used){C.RESET}")
            time.sleep(1.2)
            continue

        # ── Gear on road ─────────────────────────────────────────────────
        if choice == 3:
            equip_screen(player)
            continue

        # ── Journal on road ──────────────────────────────────────────────
        if choice == 4:
            show_journal(player)
            continue

        # ── Turn back ────────────────────────────────────────────────────
        if choice == 5:
            abort_travel(player)
            print(f"\n  {C.DIM}You turn back.{C.RESET}")
            time.sleep(0.8)
            return

        # ── Press on ─────────────────────────────────────────────────────
        arrived, enemy, event = take_road_step(player)

        if arrived:
            city = CITIES[player.current_city]
            play_melody("city_arrive")
            show_world_map(player)
            print(f"\n  {C.BGREEN}You arrive in {city.name}. Day {player.days_elapsed}.{C.RESET}")
            time.sleep(1.5)
            return

        if enemy:
            clear()
            print()
            print(f"  {C.BRED}{C.BOLD}A {enemy.name} blocks your path\!{C.RESET}")
            print(f"  {C.DIM}{enemy.description}{C.RESET}")
            time.sleep(1.2)

            won = run_combat(player, enemy)

            if not player.is_alive():
                game_over(player)
                return

            if won:
                loot_screen(player, enemy)

        if event:
            explore_event(player, event)


# ════════════════════════════════════════════════════════════════
#   GAME OVER
# ════════════════════════════════════════════════════════════════

def game_over(player: Player):
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


# ════════════════════════════════════════════════════════════════
#   ENTRY POINT
# ════════════════════════════════════════════════════════════════

def main():
    clear()
    title_screen("THE MERCHANT'S ROAD")
    print(f"  {C.DIM}Three cities. Open roads. One market worth mastering.{C.RESET}")
    print()
    print(f"  {C.BBLACK}Alpha - World v1.3  |  Merchant system: Phase 2{C.RESET}")
    print()
    pause("Press Enter to begin...")
    start_ambient_loop()

    player = character_creation()

    while player.is_alive():
        if player.current_city and not player.on_road:
            city_loop(player)
        elif player.on_road:
            road_loop(player)


if __name__ == "__main__":
    main()
