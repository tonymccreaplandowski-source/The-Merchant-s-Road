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
    SUPPLY_ITEMS, TRADE_ITEMS, GRIMTOTEM_ITEMS, get_items_by_rarity, ITEM_LOOKUP,
)
from ui.display     import (
    C, RARITY_COLOR, BIOME_COLOR,
    clear, pause, hr, section, title_screen,
    prompt_choice, item_line, rarity_tag,
    show_world_map, show_combat_screen, show_character_sheet,
    skill_bar, hp_bar, mana_bar, beep, play_melody,
    typewrite, show_journal,
    start_ambient_loop, stop_ambient_loop, resume_ambient_loop,
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

def _pool_librarian(magic_skill: int = 0):
    from data.items import BOOK_ITEMS
    pool = list(BOOK_ITEMS)
    # Grimtotems appear with tier-based probability; Magic skill slightly boosts chance
    magic_bonus = magic_skill * 0.002   # 0.2% per Magic point
    tier_chances = {"basic": 0.22 + magic_bonus, "mid": 0.08 + magic_bonus * 0.5, "advanced": 0.02 + magic_bonus * 0.25}
    from data.spells import SPELLS
    for gt in GRIMTOTEM_ITEMS:
        spell = SPELLS.get(gt.spell_name, {})
        tier  = spell.get("tier", "basic")
        if random.random() < tier_chances.get(tier, 0.05):
            pool.append(gt)
    return pool

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

def _pool_mage():
    from data.spells import SPELLS
    pool = []
    # Mage merchant reliably stocks mid and advanced grimtotems
    mid_chance      = 0.60
    advanced_chance = 0.30
    from data.spells import SPELLS as _SP
    for gt in GRIMTOTEM_ITEMS:
        spell = _SP.get(gt.spell_name, {})
        tier  = spell.get("tier", "basic")
        chance = {"basic": 0.80, "mid": mid_chance, "advanced": advanced_chance}.get(tier, 0.5)
        if random.random() < chance:
            pool.append(gt)
    if not pool:   # fallback — always has something
        pool = [GRIMTOTEM_ITEMS[0]]
    return pool


MERCHANT_TYPES = [
    # (type_label, tagline, pool_fn, leading_skill)
    ("Blacksmith",        "Soot-stained hands, straight talk, sharp steel.",     _pool_blacksmith,        "Martial"),
    ("Apothecary",        "Herbs and remedies for every road ailment.",           _pool_apothecary,        "Magic"),
    ("Librarian",         "Quiet, watchful — lore texts and possibility of finding tomes.",  _pool_librarian, "Dungeoneering"),
    ("Survival Trader",   "Rations, rope, and everything the road demands.",      _pool_survival,          "Survival"),
    ("Dungeoneering Co.", "Lanterns, picks, and maps of the unseen places.",      _pool_dungeoneering,     "Dungeoneering"),
    ("Leatherworker",     "Soft goods for those who prefer to stay unnoticed.",   _pool_leatherworker,     "Stealth"),
    ("Mage Merchant",     "Grimoires, tomes, and spells for those with the gift.", _pool_mage,              "Magic"),
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


def _generate_merchant_typed(mtype_tuple: tuple, used_names: set) -> dict:
    """Spawn a merchant of a specific type."""
    mtype_label, tagline, pool_fn, leading_skill = mtype_tuple
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
        "sold_items":    [],
        "discount":      1.0,
    }


def generate_city_merchants(city_key: str) -> list:
    """Return 3 merchants. Slot 1 is always a Survival Trader (basic supplies guaranteed)."""
    used = set()
    supply_type = next(m for m in MERCHANT_TYPES if m[0] == "Survival Trader")
    guaranteed  = _generate_merchant_typed(supply_type, used)
    other_two   = [_generate_merchant(used) for _ in range(2)]
    return [guaranteed] + other_two


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
        return f"You drink the {potion.name}. Combat power surges!"
    if effect == "agi_boost":
        state["player_agi_boost"] = True
        return f"You drink the {potion.name}. You feel fleet-footed."
    if effect == "full_restore":
        player.heal(player.max_hp)
        player.restore_mana()
        return f"You drink the {potion.name}. HP and Mana fully restored!"
    if effect == "map_bonus":
        player.map_bonus = True
        return f"You study the {potion.name}. Nearby locations will be easier to find."
    if effect == "torch":
        return f"You light the {potion.name}. The dark pulls back a little."
    if effect == "heal_35":
        before = player.hp
        player.heal(35)
        gained = player.hp - before
        return f"You eat the {potion.name}. +{gained} HP."
    if effect == "heal_40":
        before = player.hp
        player.heal(40)
        gained = player.hp - before
        return f"You eat the {potion.name}. +{gained} HP."
    if effect == "mushroom_wild":
        before_hp = player.hp
        player.heal(15)
        player.restore_mana(10)
        gained_hp = player.hp - before_hp
        return f"You eat the {potion.name}. +{gained_hp} HP, +10 Mana."
    if effect == "berries_unknown":
        if random.random() < 0.20:
            player.take_damage(15)
            return f"You eat the {potion.name}. They were poisonous. -15 HP!"
        before = player.hp
        player.heal(10)
        gained = player.hp - before
        return f"You eat the {potion.name}. Tasted fine. +{gained} HP."
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
    print(f"  {C.BGREEN}✓ Character created!{C.RESET}  "
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

def run_combat(player: Player, enemy, force_first: bool = False) -> bool:
    """
    Full combat loop.
    Returns True if player wins, False if player fled or was killed.
    force_first: skip initiative roll and guarantee player acts first (stealth ambush).
    """
    state        = fresh_state()
    stop_ambient_loop()          # silence ambient while combat plays
    play_melody("combat_start")
    player_first = True if force_first else roll_initiative(player, enemy)
    if force_first:
        state["enemy_staggered"] = 2   # surprised enemy: -10 combat_skill for 2 rounds

    if player_first:
        message = f"{enemy.description}\n  You win the initiative — you strike first!"
    else:
        # Enemy attacks before the player's first turn
        e_dmg, e_move, e_is_spell = enemy_attack(enemy, player, state)
        player.take_damage(e_dmg)
        e_verb = "casts" if e_is_spell else "attacks with"
        if e_dmg == 0:
            message = f"{enemy.description}\n  {enemy.name} moves first — {e_move} (missed)"
        else:
            message = (
                f"{enemy.description}\n"
                f"  {enemy.name} moves first! {e_verb} {e_move} — "
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
                message = f"You use {C.BOLD}{move_name}{C.RESET}! Missed entirely!"
            else:
                crit_str = f"  {C.BYELLOW}✦ CRITICAL!{C.RESET}" if is_crit else ""
                message = (
                    f"You use {C.BOLD}{move_name}{C.RESET}! It's {label}! "
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
            cost   = max(0, spell["cost"] - player.mana_discount)

            if not player.spend_mana(cost):
                message = (
                    f"Not enough mana! {sname} costs {cost}, "
                    f"you have {player.mana}."
                )
                continue

            dmg, label, stag = cast_spell(sname, player, enemy, state)

            if spell.get("damage_type") == "heal":
                message = f"You cast {C.BPURPLE}{sname}{C.RESET}! You recover {C.BGREEN}{dmg}{C.RESET} HP."
                beep("heal")
            else:
                enemy.take_damage(dmg)
                message = (
                    f"You cast {C.BPURPLE}{sname}{C.RESET}! It's {label}! "
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
                resume_ambient_loop()   # resume correct context on escape
                return False
            # Failed flee → enemy attacks this turn
            message      = "You couldn't escape!"
            action_taken = True

        # ── Enemy counter-attack ──────────────────────────────────────────────
        if action_taken and enemy.is_alive() and player.is_alive():
            e_dmg, e_move, e_is_spell = enemy_attack(enemy, player, state)
            player.take_damage(e_dmg)
            e_verb = "casts" if e_is_spell else "retaliates with"
            if e_dmg == 0:
                message += f"\n  {enemy.name} {e_verb} {e_move}! (missed)"
            else:
                message += (
                    f"\n  {enemy.name} {e_verb} {e_move} "
                    f"for {C.BRED}{e_dmg}{C.RESET} damage."
                )
            beep("hit")

    # ── Combat end ────────────────────────────────────────────────────────────
    if not player.is_alive():
        show_combat_screen(player, enemy, "You collapse. The world fades to black...")
        play_melody("death")
        time.sleep(2)
        return False

    show_combat_screen(player, enemy, f"Victory! The {enemy.name} falls!")
    play_melody("victory")
    time.sleep(1.5)
    resume_ambient_loop()   # resume correct context after victory fanfare
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
        print(f"  {C.BRED}Inventory full ({MAX_INVENTORY}/{MAX_INVENTORY})! Can't carry more.{C.RESET}")
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

    # Check if already known
    if spell_name in player.learned_spells:
        print(f"  {C.BBLACK}You already know this spell. The words offer nothing new.{C.RESET}")
        pause()
        return False

    # Check Magic requirement
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
        # Add to journal
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
        equippable  = [i for i in player.inventory
                       if i.item_type in ("weapon", "armor", "ring", "necklace")]
        grimtotems  = [i for i in player.inventory if i.item_type == "grimtotem"]
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
            # ── Read Grimtotem ────────────────────────────────────────────
            gt = grimtotems[choice - n_equip - 1]
            learned = read_grimtotem(player, gt)
            if learned:
                player.remove_item(gt)
            continue

        if choice <= n_equip:
            # ── Equip ─────────────────────────────────────────────────────
            item = equippable[choice - 1]
            if item.cursed:
                clear()
                print(f"\n  {C.BRED}{C.BOLD}⚠ This item is cursed!{C.RESET}")
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
    ("Share a useful rumour",       "Dungeoneering", "You offer a piece of valuable road knowledge."),
    ("Stand your ground",           "Martial",       "You let quiet confidence do the talking."),
    ("Read the room",               "Survival",      "You hint at what you have survived. They sense it."),
    ("Let silence speak",           "Stealth",       "You say nothing. The quiet unnerves them more than words."),
    ("A show of power",             "Magic",         "You let something flicker. They reconsider their position."),
]

def negotiate_session(player: Player, merchant: dict) -> float:
    """
    3-round negotiation minigame. Returns a price multiplier for this merchant.
    0.75 = 25% off (perfect),  0.90 = 10% off,  0.98 = 2% off,  1.0 = no change,
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
        disc        = 0.75
        result_msg  = f"{C.BGREEN}Flawless. 25% discount on purchases \u2014 they'll pay 25% more for what you sell.{C.RESET}"
        play_melody("negotiate_win")
    elif rounds_won == 2:
        disc        = 0.90
        result_msg  = f"{C.BGREEN}Strong showing. 10% discount secured.{C.RESET}"
        play_melody("negotiate_win")
    elif rounds_won == 1:
        disc        = 0.98
        result_msg  = f"{C.BYELLOW}Narrow edge. 2% discount \u2014 barely worth it.{C.RESET}"
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
        buy_pct  = round((1 - disc) * 100)
        sell_pct = round((disc - 1) * 100) if disc > 1.0 else round((2.0 - disc - 1.0) * 100)
        disc_str = (
            f"  {C.BGREEN}[{buy_pct}% buy discount | +{sell_pct}% sell bonus]{C.RESET}"
            if disc < 1.0 else
            f"  {C.BRED}[+{round((disc - 1)*100)}% premium — they dislike you]{C.RESET}"
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
        print(f"\n  {C.BGREEN}✓ {skill_name} improved to {current + 1}!{C.RESET}")
    time.sleep(1.2)



INN_FLAVOUR = {
    "dusthaven": [
        "The inn smells of sand and spice. A caravan merchant snores in the corner.",
        "The innkeeper pours something bitter and warm. You don't ask what it is.",
        "Through the thin walls, you hear the desert wind. It doesn't stop all night.",
    ],
    "ashenvale": [
        "The fire crackles with forest wood. A hunter's hound sleeps by the hearth.",
        "Rain taps quietly at the roof. Somewhere outside, an owl calls once and goes silent.",
        "The bed is rough straw and old wool. You sleep like you haven't in weeks.",
    ],
    "ironpeak": [
        "The walls are thick stone. You feel safe here, or at least buried.",
        "Miners' voices carry from the floor below. Dice on a table, coin on the bar.",
        "The cold seeps in despite the fire. You pull the blanket close and don't argue with it.",
    ],
}

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
        city_key = player.current_city or "ashenvale"
        flavour  = random.choice(INN_FLAVOUR.get(city_key, INN_FLAVOUR["ashenvale"]))
        clear()
        title_screen("REST AT THE INN")
        print(f"  {C.DIM}{flavour}{C.RESET}")
        print()
        print(f"  {C.BGREEN}You wake rested. HP and Mana fully restored. (−10gp){C.RESET}")
    time.sleep(1.5)


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
#   BAG
# ════════════════════════════════════════════════════════════════

def bag_screen(player: Player):
    """Single access point for Gear and Journal — usable on road and in city."""
    while True:
        journal_ct = len(player.journal)
        j_hint = f"{C.DIM}({journal_ct} entr{'y' if journal_ct == 1 else 'ies'}){C.RESET}"
        clear()
        section("BAG")
        print()
        choice = prompt_choice([
            f"Gear     {C.DIM}(equipped items, grimtotems){C.RESET}",
            f"Journal  {j_hint}",
            f"{C.BBLACK}Back{C.RESET}",
        ])
        if choice == 1:
            equip_screen(player)
        elif choice == 2:
            show_journal(player)
        else:
            return

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
            f"Bag               {C.DIM}(gear + journal){C.RESET}",
            f"Training Hall     {C.DIM}(improve skills for gold){C.RESET}",
            f"Rest at the Inn   {C.DIM}(restore HP & mana — 10gp){C.RESET}",
            f"Character Sheet   {C.DIM}(stats, equipment, inventory){C.RESET}",
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
        n_base = 6   # 6 base options (market/bag/train/rest/char/books)

        if choice == 1:
            visit_market(player, city)
        elif choice == 2:
            bag_screen(player)
        elif choice == 3:
            train_skills(player)
        elif choice == 4:
            rest_at_inn(player)
        elif choice == 5:
            show_character_sheet(player)
        elif choice == 6:
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

def _location_header(player, event, room_num, total_known):
    icon      = "🕳" if event.event_type == "cave" else "🏰"
    loc_color = C.BBLACK if event.event_type == "cave" else C.BYELLOW
    clear()
    print()
    print(f"  {loc_color}{icon}  {event.name.upper()}{C.RESET}")
    if total_known > 0:
        print(f"  {C.DIM}Room {room_num} of {total_known}{C.RESET}")
    else:
        print(f"  {C.DIM}Deeper still...{C.RESET}")
    print()


def explore_event(player: Player, event):
    """Handle a cave or castle exploration event, room by room."""
    icon      = "🕳" if event.event_type == "cave" else "🏰"
    loc_color = C.BBLACK if event.event_type == "cave" else C.BYELLOW

    # Entry gate
    play_melody("location_found")
    clear()
    print()
    print(f"  {C.BYELLOW}{icon}  {event.name.upper()}{C.RESET}")
    print()
    typewrite(event.description)
    print()
    print(f"  {C.DIM}Enemies within: ???{C.RESET}")
    print()

    scouted      = False
    stealth_used = False
    total_known  = 0
    enemies      = get_event_enemies(event)
    force_first  = False

    while True:
        options = []
        if not scouted:
            options.append(f"Scout the area     {C.DIM}(Dungeoneering -- count enemies){C.RESET}")
        if not stealth_used:
            options.append(f"Attempt stealth    {C.DIM}(Stealth -- surprise first enemy){C.RESET}")
        options.append(f"Enter boldly       {C.DIM}(commit now){C.RESET}")
        options.append(f"Pass by            {C.DIM}(continue on the road){C.RESET}")

        choice_idx = prompt_choice(options)
        chosen     = options[choice_idx - 1]

        if "Scout the area" in chosen:
            scouted = True
            roll = random.randint(1, 20) + player.skill("Dungeoneering") // 5
            if roll >= 10:
                total_known = len(enemies)
                label = "enemy" if total_known == 1 else "enemies"
                print(f"\n  {C.BGREEN}You study the entrance carefully. {total_known} {label} inside.{C.RESET}")
            else:
                print(f"\n  {C.DIM}You couldn't make out much from the entrance.{C.RESET}")
            pause("Press Enter to continue...")
            clear()
            print()
            print(f"  {C.BYELLOW}{icon}  {event.name.upper()}{C.RESET}")
            print()
            typewrite(event.description)
            count_str = str(total_known) if total_known > 0 else "???"
            print(f"  {C.DIM}Enemies within: {count_str}{C.RESET}")
            print()

        elif "Attempt stealth" in chosen:
            stealth_used = True
            roll = random.randint(1, 20) + player.skill("Stealth") // 5
            if roll >= 12:
                force_first = True
                print(f"\n  {C.BGREEN}You slip inside undetected. The first enemy has no idea you're here.{C.RESET}")
            else:
                print(f"\n  {C.BYELLOW}You fumble the approach. No advantage gained.{C.RESET}")
            pause("Press Enter to continue...")
            clear()
            print()
            print(f"  {C.BYELLOW}{icon}  {event.name.upper()}{C.RESET}")
            print()
            count_str = str(total_known) if total_known > 0 else "???"
            print(f"  {C.DIM}Enemies within: {count_str}{C.RESET}")
            print()

        elif "Pass by" in chosen:
            print(f"\n  {C.DIM}You give it a wide berth and press on.{C.RESET}")
            time.sleep(0.8)
            return

        else:
            break

    # Room-by-room loop
    clear()
    print()
    typewrite(f"You enter {event.name}...", indent=f"  {loc_color}")
    print(C.RESET, end="")
    time.sleep(0.8)
    start_ambient_loop("dungeon")  # entering location

    for room_num, enemy in enumerate(enemies, 1):
        _location_header(player, event, room_num, total_known)

        is_ambush = force_first and room_num == 1
        if is_ambush:
            print(f"  {C.BGREEN}You strike from the shadows -- the {enemy.name} is caught off guard.{C.RESET}")
            time.sleep(0.8)

        print(f"  {C.BRED}{enemy.name} bars your way.{C.RESET}")
        time.sleep(1.0)

        won = run_combat(player, enemy, force_first=is_ambush)

        if not player.is_alive():
            game_over(player)
            return

        if not won:
            print(f"\n  {C.BYELLOW}You fall back and escape {event.name}.{C.RESET}")
            time.sleep(1.0)
            start_ambient_loop("road")  # fled location
            return

        # Mid-room search (not the final room)
        is_final = (room_num == len(enemies))
        if not is_final:
            _location_header(player, event, room_num, total_known)
            print(f"  {C.BGREEN}Room {room_num} cleared.{C.RESET}")
            print()
            print(f"  {C.DIM}You search the area...{C.RESET}")
            time.sleep(0.6)

            if random.random() < 0.30:
                loot  = generate_loot(bias="common")
                color = RARITY_COLOR.get(loot.rarity, C.WHITE)
                print(f"\n  Found: {color}{C.BOLD}{loot.name}{C.RESET}  [{rarity_tag(loot.rarity)}]")
                if player.can_carry():
                    pick = prompt_choice(["Take it", "Leave it"])
                    if pick == 1:
                        player.add_item(loot)
                        print(f"  {C.BGREEN}Added to inventory.{C.RESET}")
                else:
                    print(f"  {C.BRED}Inventory full -- left behind.{C.RESET}")
            else:
                print(f"\n  {C.DIM}Nothing of interest.{C.RESET}")

            print()
            nav = prompt_choice([
                "Press deeper",
                f"Retreat  {C.DIM}(leave {event.name}){C.RESET}",
            ])
            if nav == 1:
                start_ambient_loop("tension")  # pressing deeper
            if nav == 2:
                print(f"\n  {C.BYELLOW}You make your way back out of {event.name}.{C.RESET}")
                time.sleep(1.0)
                start_ambient_loop("road")  # retreated from location
                return

    # All rooms cleared -- final loot + lore
    clear()
    print()
    print(f"  {C.BGREEN}{C.BOLD}You clear {event.name}!{C.RESET}")
    print(f"  {C.DIM}You search the area carefully...{C.RESET}")
    time.sleep(1.2)

    for _ in range(2):
        loot  = generate_loot(bias=event.loot_bias)
        color = RARITY_COLOR.get(loot.rarity, C.WHITE)
        print(f"\n  Found: {color}{C.BOLD}{loot.name}{C.RESET}  [{rarity_tag(loot.rarity)}]  "
              f"{C.DIM}{loot.base_value}gp base{C.RESET}")
        if not player.can_carry():
            print(f"  {C.BRED}Inventory full -- left behind.{C.RESET}")
            pause("Press Enter to continue...")
            continue
        pick = prompt_choice(["Take it", "Leave it"])
        if pick == 1:
            player.add_item(loot)
            print(f"  {C.BGREEN}Added to inventory.{C.RESET}")
        pause("Press Enter to continue...")

    # Lore drop
    if event.lore_text and event.lore_text not in player.journal:
        player.journal.append(event.lore_text)
        play_melody("journal_entry")
        print()
        hr("─")
        print(f"  {C.BYELLOW}❖ Journal updated{C.RESET}")
        print()
        typewrite(event.lore_text)
        print()
        hr("─")
        pause("Press Enter to continue...")

    start_ambient_loop("road")  # all rooms cleared, back to road



# ════════════════════════════════════════════════════════════════
#   CAMPING, BUSHCRAFT & HUNTING
# ════════════════════════════════════════════════════════════════

# Food items usable for camping → (hp_restore, mana_restore, has_poison_risk)
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

# Item names that count as firewood for camping
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
        gain_str = f"+{hp_gain} HP"
        if mana_gain:
            gain_str += f", +{mana_gain} Mana"
        print(f"  {C.BGREEN}You rest well through the night. {gain_str}.{C.RESET}")
        print(f"  {C.DIM}HP: {player.hp}/{player.max_hp}  |  Mana: {player.mana}/{player.max_mana}{C.RESET}")
        # Herb Bundle cures road ailments
        if food.name == "Herb Bundle":
            if player.road_poison > 0 or player.road_diseased:
                player.road_poison   = 0
                player.road_diseased = False
                print(f"  {C.BGREEN}The herbs clear whatever ailed you. Poison and sickness fade.{C.RESET}")

    pause()


# ── Forage tables: item names by Survival tier, with weights ─────────────────
FORAGE_TABLE = {
    "low": [          # Survival < 20
        ("Unknown Berries", 50),
        ("Firewood",        30),
        ("Wild Mushrooms",  15),
        ("Blueberries",      5),
    ],
    "mid": [          # Survival 20-49
        ("Firewood",        35),
        ("Blueberries",     25),
        ("Wild Mushrooms",  20),
        ("Herb Bundle",     15),
        ("Unknown Berries",  5),
    ],
    "high": [         # Survival 50-79
        ("Firewood",        28),
        ("Blueberries",     22),
        ("Wild Mushrooms",  20),
        ("Herb Bundle",     18),
        ("Nightshade",      12),
    ],
    "expert": [       # Survival 80+
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
    success_chance = 35 + survival * 0.5   # 35% base → up to 85%

    clear()
    title_screen("FORAGING")
    print(f"  {C.DIM}You move quietly through the undergrowth...{C.RESET}")
    time.sleep(1.0)
    print()

    if random.random() * 100 > success_chance:
        player.days_elapsed += 1
        player.road_total   += 1   # journey extends by one step
        print(f"  {C.BBLACK}Your time spent foraging was unsuccessful.")
        print(f"  It has since grown dark. Your journey extends a day...{C.RESET}")
        pause()
        return

    # Determine quality tier
    if survival < 20:
        tier      = "low"
        qual_msg  = f"  {C.DIM}You find something. Hard to say exactly what.{C.RESET}"
    elif survival < 50:
        tier      = "mid"
        qual_msg  = f"  {C.DIM}You read the landscape well enough to find something useful.{C.RESET}"
    elif survival < 80:
        tier      = "high"
        qual_msg  = f"  {C.BGREEN}You know this terrain. You move efficiently and find good yield.{C.RESET}"
    else:
        tier      = "expert"
        qual_msg  = f"  {C.BGREEN}The wilderness gives up its secrets to you readily.{C.RESET}"

    print(qual_msg)
    print()

    table       = FORAGE_TABLE[tier]
    names, wts  = zip(*table)
    found_name  = random.choices(names, weights=wts, k=1)[0]
    found_item  = _LOOKUP.get(found_name)

    if found_item:
        if player.can_carry():
            player.add_item(found_item)
            print(f"  {C.BGREEN}You find: {found_name}{C.RESET}")
            print(f"  {C.DIM}{found_item.description}{C.RESET}")
        else:
            print(f"  {C.BYELLOW}You found {found_name} but your pack is full.{C.RESET}")
    pause()


# ── Hunting ───────────────────────────────────────────────────────────────────
# (name, desc, min_combined_avg, meat, pelt, bone_chance, miss_dmg, death_risk)
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

    # Forced shot / final decision
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

    # The shot
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
        options.append("Hunt for game  (bow ready)")
    options.append(f"{C.BBLACK}\u2190 Back to road{C.RESET}")

    choice = prompt_choice(options, "What will you do?")

    if choice == len(options):
        return
    if choice == 1:
        _do_forage(player)
    elif has_bow and choice == 2:
        hunting_minigame(player)



# ════════════════════════════════════════════════════════════════
#   WILDERNESS EVENTS
# ════════════════════════════════════════════════════════════════

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

WILDERNESS_BASE_CHANCE = 0.18   # per uneventful step
WILDERNESS_SKILL_REDUCE = 0.0012  # each Survival point shaves this off


def get_wilderness_chance(player: Player) -> float:
    return max(0.06, WILDERNESS_BASE_CHANCE - player.skill("Survival") * WILDERNESS_SKILL_REDUCE)


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
            loot = generate_loot(bias="uncommon")
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


# ════════════════════════════════════════════════════════════════
#   ROAD LOOP
# ════════════════════════════════════════════════════════════════

def road_loop(player):
    while player.on_road:
        dest_name  = CITIES[player.road_destination].name
        road_biome = player.road_biome

        show_world_map(player)
        print(f"  {C.DIM}You press on through the {road_biome} toward {dest_name}.{C.RESET}")
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
            f"Press on       {C.DIM}(continue towards {dest_name}){C.RESET}",
            camp_label,
            f"Bushcraft      {C.DIM}(forage or hunt — governed by Survival){C.RESET}",
            f"Bag            {C.DIM}(gear + journal){C.RESET}",
            f"Turn back      {C.DIM}(return to origin city){C.RESET}",
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
            abort_travel(player)
            player.road_poison   = 0
            player.road_diseased = False
            print(f"\n  {C.DIM}You turn back.{C.RESET}")
            time.sleep(0.8)
            return

        arrived, enemy, event = take_road_step(player)

        # ── Status effect drain (poison / disease) ────────────────────────────
        if player.road_poison > 0:
            player.take_damage(5)
            player.road_poison -= 1
            _ps = "s" if player.road_poison != 1 else ""
            rem = f"{player.road_poison} step{_ps} remaining" if player.road_poison > 0 else "poison has faded"
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

        if arrived:
            player.road_poison   = 0
            player.road_diseased = False
            city = CITIES[player.current_city]
            play_melody("city_arrive")
            start_ambient_loop("city")   # switch to city music on arrival
            show_world_map(player)
            print(f"\n  {C.BGREEN}You arrive in {city.name}. Day {player.days_elapsed}.{C.RESET}")
            time.sleep(1.5)
            return

        if enemy:
            clear()
            print()
            print(f"  {C.BRED}{C.BOLD}A {enemy.name} blocks your path!{C.RESET}")
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

        # ── Wilderness event (only on fully uneventful steps) ─────────────────
        if not arrived and not enemy and not event:
            if random.random() < get_wilderness_chance(player):
                wilderness_event(player)
                if not player.is_alive():
                    game_over(player)
                    return


# ════════════════════════════════════════════════════════════════
#   GAME OVER
# ════════════════════════════════════════════════════════════════

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


# ════════════════════════════════════════════════════════════════
#   ENTRY POINT
# ════════════════════════════════════════════════════════════════

# ════════════════════════════════════════════════════════════════
#   ENTRY POINT
# ════════════════════════════════════════════════════════════════

def main():
    clear()
    title_screen("THE MERCHANT\'S ROAD")
    print(f"  {C.DIM}Three cities. Open roads. One market worth mastering.{C.RESET}")
    print()
    print(f"  {C.BBLACK}Alpha - World v2.0  |  Quality of Life Pass{C.RESET}")
    print()
    pause("Press Enter to begin...")

    player = character_creation()
    start_ambient_loop("city")   # player starts in Rabenmark

    while True:
        city_loop(player)
        if player.on_road:
            start_ambient_loop("road")   # switching to road — change music
            road_loop(player)


if __name__ == "__main__":
    main()
