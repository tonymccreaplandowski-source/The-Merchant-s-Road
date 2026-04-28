"""
City interaction screens — market, negotiate, merchants, training, inn, books, city loop.
"""

import sys
import time
import random

from engine.player    import Player, MAX_INVENTORY, SKILLS
from engine.merchant  import (
    MERCHANT_GREETINGS, generate_city_merchants,
    sell_price, buy_price,
)
from engine.negotiate import negotiate_session
from data.cities     import CITIES, get_adjacent_city_keys
from engine.world    import start_travel
from ui.display      import (
    C, RARITY_COLOR, BIOME_COLOR,
    clear, pause, hr, section, title_screen, prompt_choice,
    show_world_map, show_character_sheet, skill_bar, play_melody,
)
from ui.equipment    import bag_screen, read_grimtotem


# ── Training cost helper ──────────────────────────────────────────────────────

def _training_cost(level: int) -> int:
    if level < 25:  return 20
    if level < 50:  return 55
    if level < 75:  return 130
    return 300


# ── Inn flavour lines by city ─────────────────────────────────────────────────

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



# ── Merchant screen ───────────────────────────────────────────────────────────

def merchant_screen(player: Player, city, merchant: dict):
    """Interact with a single named merchant — Sell / Buy / Negotiate / Leave."""
    while True:
        if merchant.get("ejected"):
            clear()
            title_screen(f"{merchant['name'].upper()} — {merchant['type'].upper()}")
            print(f"\n  {C.BRED}[Thrown out — not welcome here]{C.RESET}")
            pause()
            return

        gp_delta = merchant.get("gp_delta", 0)
        disc_str = (
            f"  {C.BGREEN}[+{gp_delta}gp advantage on all trades]{C.RESET}"
            if gp_delta > 0 else
            f"  {C.BRED}[-{abs(gp_delta)}gp penalty on all trades]{C.RESET}"
            if gp_delta < 0 else ""
        )

        clear()
        title_screen(f"{merchant['name'].upper()} — {merchant['type'].upper()}")
        if not merchant.get("greeted"):
            greetings = MERCHANT_GREETINGS.get(merchant["type"], [])
            if greetings:
                greeting = merchant.setdefault("greeting", random.choice(greetings))
                print(f"  {C.BYELLOW}\"{greeting}\"{C.RESET}")
            merchant["greeted"] = True
        else:
            print(f"  {C.DIM}\"{merchant['tagline']}\"{C.RESET}{disc_str}")
        print(f"  {C.DIM}[{city.biome.capitalize()} pricing]{C.RESET}")
        print()
        print(f"  {C.BYELLOW}Your gold: {player.gold}gp{C.RESET}  "
              f"{C.DIM}Bag: {len(player.inventory)}/{MAX_INVENTORY}{C.RESET}")
        print()

        if merchant.get("negotiated"):
            delta = merchant.get("gp_delta", 0)
            if delta > 0:
                neg_label = f"Negotiate  {C.DIM}(done — +{delta}gp advantage){C.RESET}"
            elif delta < 0:
                neg_label = f"Negotiate  {C.DIM}(done — -{abs(delta)}gp penalty){C.RESET}"
            else:
                neg_label = f"Negotiate  {C.DIM}(no deal reached){C.RESET}"
        else:
            neg_label = f"Negotiate  {C.DIM}(haggle for better prices){C.RESET}"

        tab = prompt_choice([
            "Sell items",
            "Buy items",
            neg_label,
            "Leave",
        ])
        if tab == 4:
            return

        if tab == 3:
            negotiate_session(player, merchant)
            continue

        # ── SELL ──────────────────────────────────────────────────────────────
        if tab == 1:
            while True:
                gp_delta = merchant.get("gp_delta", 0)
                if not player.inventory:
                    print(f"\n  {C.BBLACK}You have nothing to sell.{C.RESET}")
                    pause("Press Enter to go back...")
                    break

                clear()
                title_screen(f"SELL — {merchant['name'].upper()}")
                print(f"  {C.BYELLOW}Gold: {player.gold}gp{C.RESET}")
                print()

                options = []
                for item in player.inventory:
                    sp  = sell_price(item, city, gp_delta)
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
                options.append(f"{C.BBLACK}← Leave selling{C.RESET}")

                choice = prompt_choice(options, "Sell which item?")
                if choice == len(options):
                    break

                item = player.inventory[choice - 1]
                sp   = sell_price(item, city, gp_delta)
                player.remove_item(item)
                player.gold += sp
                merchant["sold_items"].append(item)
                print(f"\n  {C.BGREEN}Sold {item.name} for {sp}gp.  Gold: {player.gold}gp{C.RESET}")
                pause("Press Enter to sell another or leave...")

        # ── BUY ───────────────────────────────────────────────────────────────
        elif tab == 2:
            while True:
                gp_delta    = merchant.get("gp_delta", 0)
                all_buyable = merchant["stock"] + merchant["sold_items"]
                if not all_buyable:
                    print(f"\n  {C.BBLACK}Nothing left in stock.{C.RESET}")
                    pause("Press Enter to go back...")
                    break

                clear()
                title_screen(f"BUY — {merchant['name'].upper()}")
                print(f"  {C.BYELLOW}Gold: {player.gold}gp{C.RESET}  "
                      f"{C.DIM}Bag: {len(player.inventory)}/{MAX_INVENTORY}{C.RESET}")
                print()

                options = []
                for item in all_buyable:
                    bp          = buy_price(item, city, gp_delta)
                    mod         = city.price_modifier(item.name)
                    is_sellback = item in merchant["sold_items"]
                    tag         = f"  {C.BYELLOW}[yours]{C.RESET}" if is_sellback else ""
                    if mod < 1.0:
                        price_str = f"{C.BGREEN}{bp}gp ▼{C.RESET}"
                    elif mod > 1.0:
                        price_str = f"{C.BRED}{bp}gp ▲{C.RESET}"
                    else:
                        price_str = f"{C.WHITE}{bp}gp{C.RESET}"
                    affordable = "" if player.gold >= bp else f"  {C.BRED}✗{C.RESET}"
                    desc_text  = item.description[:65] + ("…" if len(item.description) > 65 else "")
                    options.append(
                        f"{RARITY_COLOR.get(item.rarity, C.WHITE)}{item.name}{C.RESET}"
                        f"{tag}  {price_str}{affordable}  "
                        f"{C.DIM}{desc_text}{C.RESET}"
                    )
                options.append(f"{C.BBLACK}← Leave buying{C.RESET}")

                choice = prompt_choice(options, "Buy which item?")
                if choice == len(options):
                    break

                item = all_buyable[choice - 1]
                bp   = buy_price(item, city, gp_delta)

                if player.gold < bp:
                    print(f"\n  {C.BRED}Not enough gold. Need {bp}gp, have {player.gold}gp.{C.RESET}")
                    pause("Press Enter to continue...")
                elif not player.can_carry():
                    print(f"\n  {C.BRED}Pack full ({MAX_INVENTORY}/{MAX_INVENTORY} items).{C.RESET}")
                    pause("Press Enter to continue...")
                else:
                    player.gold -= bp
                    player.add_item(item)
                    if item in merchant["sold_items"]:
                        merchant["sold_items"].remove(item)
                    else:
                        merchant["stock"].remove(item)
                    print(f"\n  {C.BGREEN}Bought {item.name} for {bp}gp. Gold: {player.gold}gp{C.RESET}")
                    pause("Press Enter to buy another or leave...")


# ── Market (merchant selection) ───────────────────────────────────────────────

_city_merchants: dict = {}   # city key → list of merchant dicts, cleared on city exit


def visit_market(player: Player, city):
    """
    Merchant availability system: shows all merchant types with their availability.
    Available merchants can be visited; unavailable ones show 'Not in town today'.
    """
    global _city_merchants
    city_key = city.key

    if city_key not in _city_merchants:
        _city_merchants[city_key] = generate_city_merchants(city_key)

    merchants = _city_merchants[city_key]

    while True:
        clear()
        title_screen(f"THE MARKET — {city.name.upper()}")
        print(f"  {C.DIM}Whom are you looking for?{C.RESET}")
        print(f"  {C.BYELLOW}Your gold: {player.gold}gp{C.RESET}")
        print()

        options    = []
        option_map = []

        for m in merchants:
            gp_delta = m.get("gp_delta", 0)
            is_avail = m.get("available", True)
            is_ejected = m.get("ejected", False)
            neg_tag  = (
                f"  {C.BRED}[thrown out]{C.RESET}" if is_ejected else
                f"  {C.BGREEN}[+{gp_delta}gp advantage]{C.RESET}" if m.get("negotiated") and gp_delta > 0 else
                f"  {C.BRED}[-{abs(gp_delta)}gp penalty]{C.RESET}" if m.get("negotiated") and gp_delta < 0 else ""
            )
            if is_ejected:
                options.append(
                    f"{C.BBLACK}{m['type']:<22}  {m['name']} — {C.BRED}[Thrown out — not welcome here]{C.RESET}"
                )
                option_map.append(None)
            elif is_avail:
                options.append(
                    f"{C.BOLD}{m['type']:<22}{C.RESET}  "
                    f"{C.DIM}{m['name']} — {m['tagline'][:45]}{C.RESET}{neg_tag}"
                )
                option_map.append(m)
            else:
                options.append(
                    f"{C.BBLACK}{m['type']:<22}  Not in town today.{C.RESET}"
                )
                option_map.append(None)

        options.append(f"{C.BBLACK}← Leave market{C.RESET}")

        choice = prompt_choice(options, "Who are you looking for?")
        if choice == len(options):
            return

        selected = option_map[choice - 1]
        if selected is None:
            chosen_m = merchants[choice - 1]
            if chosen_m.get("ejected"):
                print(f"\n  {C.BRED}You're not welcome there anymore.{C.RESET}")
            else:
                print(f"\n  {C.BBLACK}They're not in town today.{C.RESET}")
            pause("Press Enter to continue...")
            continue

        merchant_screen(player, city, selected)


# ── Training ──────────────────────────────────────────────────────────────────

def train_skills(player: Player):
    while True:
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
            print(f"\n  {C.BRED}That skill is already at its peak.{C.RESET}")
            pause("Press Enter to continue...")
        elif player.gold < cost:
            print(f"\n  {C.BRED}Not enough gold. Need {cost}gp, have {player.gold}gp.{C.RESET}")
            pause("Press Enter to continue...")
        else:
            player.gold -= cost
            player.train(skill_name)
            print(f"\n  {C.BGREEN}✓ {skill_name} improved to {current + 1}!{C.RESET}")
            print(f"  {C.DIM}Gold remaining: {player.gold}gp{C.RESET}")
            pause("Press Enter to train again or leave...")


# ── Inn ───────────────────────────────────────────────────────────────────────

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
        player.hunger = 100
        city_key = player.current_city or "ashenvale"
        flavour  = random.choice(INN_FLAVOUR.get(city_key, INN_FLAVOUR["ashenvale"]))
        clear()
        title_screen("REST AT THE INN")
        print(f"  {C.DIM}{flavour}{C.RESET}")
        print()
        print(f"  {C.BGREEN}You wake rested. HP and Mana fully restored. (−10gp){C.RESET}")
    time.sleep(1.5)


# ── Read book ─────────────────────────────────────────────────────────────────

def read_book_menu(player: Player):
    """Let the player read a lore book or grimtotem from inventory."""
    from ui.display import RARITY_COLOR, typewrite, hr, play_melody
    books      = [i for i in player.inventory if i.item_type == "book" and i.lore]
    grimtotems = [i for i in player.inventory if i.item_type == "grimtotem"]
    if not books and not grimtotems:
        clear()
        print(f"\n  {C.BBLACK}You have nothing to read.{C.RESET}")
        pause()
        return

    while True:
        clear()
        title_screen("READ")
        print(f"  {C.DIM}Books add lore to your journal. Grimtotems teach spells.{C.RESET}")
        print()

        options = []
        for b in books:
            already = b.lore in player.journal
            tag     = f"  {C.BBLACK}[already read]{C.RESET}" if already else ""
            options.append(
                f"{RARITY_COLOR.get(b.rarity, C.WHITE)}{b.name}{C.RESET}"
                f"  {C.DIM}[book]{C.RESET}{tag}"
            )
        n_books = len(books)
        for gt in grimtotems:
            known = gt.spell_name in player.learned_spells if gt.spell_name else False
            tag   = f"  {C.BBLACK}[already known]{C.RESET}" if known else ""
            options.append(
                f"{RARITY_COLOR.get(gt.rarity, C.WHITE)}{gt.name}{C.RESET}"
                f"  {C.DIM}[grimtotem — {gt.spell_name}]{C.RESET}{tag}"
            )
        options.append(f"{C.BBLACK}← Back{C.RESET}")

        choice = prompt_choice(options, "Read which?")
        if choice == len(options):
            return

        if choice > n_books:
            gt      = grimtotems[choice - n_books - 1]
            learned = read_grimtotem(player, gt)
            if learned:
                player.remove_item(gt)
                grimtotems = [i for i in player.inventory if i.item_type == "grimtotem"]
            continue

        book = books[choice - 1]
        clear()
        title_screen(book.name.upper())
        print(f"  {C.DIM}\"{book.description}\"{C.RESET}")
        print()
        hr()
        print()
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


# ── City loop ─────────────────────────────────────────────────────────────────

def city_loop(player: Player):
    """Main city interaction loop. Exits when the player begins travelling."""
    global _city_merchants

    from data.enemies import spawn_city_guard
    from ui.combat_loop import run_combat

    city_key = player.current_city
    if city_key in player.city_wanted:
        clear()
        title_screen("CITY GATES")
        print(f"\n  {C.BRED}A guard steps out of the gatehouse. He's been waiting.{C.RESET}")
        print(f'  {C.DIM}"There you are. We\'ve had reports. You\'re coming with me."{C.RESET}')
        print()
        pause("Press Enter to face him...")
        guard = spawn_city_guard()
        won = run_combat(player, guard)
        if not player.is_alive():
            from ui.road import game_over
            game_over(player)
            return
        if won:
            player.city_wanted.discard(city_key)
            player.city_heat[city_key] = min(100, player.city_heat.get(city_key, 0) + 20)
            print(f"\n  {C.BYELLOW}You stand over him. For now, you're free — but the city has a long memory.{C.RESET}")
            pause()
        else:
            return

    while True:
        city = CITIES[player.current_city]
        show_world_map(player)
        print(f"  {C.BCYAN}{C.BOLD}{city.name}{C.RESET}  {C.DIM}{city.description}{C.RESET}")
        print()
        section("WHAT WOULD YOU LIKE TO DO?")

        adjacent     = get_adjacent_city_keys(player.current_city)
        journal_ct   = len(player.journal)
        journal_hint = f"{C.DIM}({journal_ct} entr{'y' if journal_ct == 1 else 'ies'}){C.RESET}"

        readable_items = [i for i in player.inventory if i.item_type in ("book", "grimtotem")]
        book_hint = (
            f"  {C.BYELLOW}({len(readable_items)} item{'s' if len(readable_items) != 1 else ''}){C.RESET}"
            if readable_items else ""
        )

        stealth_val = player.skill("Stealth")
        if stealth_val >= 10:
            prowl_label = f"Prowl             {C.DIM}(work the streets — Stealth: {stealth_val}){C.RESET}"
        else:
            prowl_label = f"{C.BBLACK}Prowl             (requires 10 Stealth — yours: {stealth_val}){C.RESET}"

        options = [
            f"The Market        {C.DIM}(3 merchants — buy, sell, negotiate){C.RESET}",
            f"Bag               {C.DIM}(gear + journal){C.RESET}",
            f"Training Hall     {C.DIM}(improve skills for gold){C.RESET}",
            f"Rest at the Inn   {C.DIM}(restore HP & mana — 10gp){C.RESET}",
            prowl_label,
            f"Character Sheet   {C.DIM}(stats, equipment, inventory){C.RESET}",
            f"Read              {C.DIM}(books + grimtotems){C.RESET}{book_hint}",
            f"Travel            {C.DIM}(set out on the road){C.RESET}",
            f"{C.BBLACK}Quit{C.RESET}",
        ]

        choice = prompt_choice(options, "Your choice")

        if choice == 1:
            visit_market(player, city)
        elif choice == 2:
            bag_screen(player)
        elif choice == 3:
            train_skills(player)
        elif choice == 4:
            rest_at_inn(player)
        elif choice == 5:
            if stealth_val >= 10:
                from engine.pickpocket import prowl_screen
                prowl_screen(player)
                if not player.is_alive():
                    from ui.road import game_over
                    game_over(player)
                    return
            else:
                print(f"\n  {C.BBLACK}You don't move quietly enough to work a crowd.{C.RESET}")
                pause()
        elif choice == 6:
            show_character_sheet(player)
        elif choice == 7:
            read_book_menu(player)
        elif choice == 8:
            if not adjacent:
                print(f"\n  {C.BBLACK}No roads lead out of {city.name}.{C.RESET}")
                pause()
                continue
            clear()
            show_world_map(player)
            section("WHERE WOULD YOU LIKE TO GO?")
            dest_options = []
            for dest_key in adjacent:
                dest       = CITIES[dest_key]
                road_color = BIOME_COLOR.get(dest.road_biome_east or dest.biome, C.WHITE)
                dest_options.append(
                    f"{C.BOLD}{dest.name}{C.RESET}  "
                    f"{road_color}[{dest.biome} road]{C.RESET}"
                )
            dest_options.append(f"{C.BBLACK}← Back{C.RESET}")
            dest_choice = prompt_choice(dest_options, "Your destination")
            if dest_choice == len(dest_options):
                continue
            dest_key = adjacent[dest_choice - 1]
            _city_merchants.pop(player.current_city, None)
            start_travel(player, dest_key)
            return
        else:
            clear()
            print()
            print(f"  {C.BYELLOW}Farewell, {player.name}. May your purse stay heavy.{C.RESET}")
            print()
            sys.exit(0)
