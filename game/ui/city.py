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
    play_location_music, stop_location_music,
)
from ui.equipment    import bag_screen, read_grimtotem


def _bonus_str(item) -> str:
    """Return a compact stat-bonus string for display, e.g. '+2 Martial, -1 Stealth'."""
    if not item.stat_bonuses:
        return ""
    parts = [f"{'+' if v >= 0 else ''}{v} {k}" for k, v in item.stat_bonuses.items()]
    return f"  {C.DIM}({', '.join(parts)}){C.RESET}"


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
    play_location_music("merchant_theme.wav")
    while True:
        if merchant.get("ejected"):
            clear()
            title_screen(f"{merchant['name'].upper()} — {merchant['type'].upper()}")
            print(f"\n  {C.BRED}[Thrown out — not welcome here]{C.RESET}")
            pause()
            stop_location_music()
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
            stop_location_music()
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
                if gp_delta > 0:
                    print(f"  {C.BGREEN}[Negotiation active: +{gp_delta}gp on every sale]{C.RESET}")
                elif gp_delta < 0:
                    print(f"  {C.BRED}[Negotiation penalty: {gp_delta}gp on every sale]{C.RESET}")
                print()

                options = []
                for item in player.inventory:
                    sp   = sell_price(item, city, gp_delta)
                    base = sell_price(item, city, 0)
                    mod  = city.price_modifier(item.name)
                    if mod > 1.0:
                        price_str = f"{C.BGREEN}{sp}gp ▲ (scarce){C.RESET}"
                    elif mod < 1.0:
                        price_str = f"{C.BRED}{sp}gp ▼ (abundant){C.RESET}"
                    else:
                        price_str = f"{C.WHITE}{sp}gp{C.RESET}"
                    delta_tag = (
                        f"  {C.BGREEN}[+{gp_delta}]{C.RESET}" if gp_delta > 0 else
                        f"  {C.BRED}[{gp_delta}]{C.RESET}"    if gp_delta < 0 else ""
                    )
                    options.append(
                        f"{RARITY_COLOR.get(item.rarity, C.WHITE)}{item.name}{C.RESET}  "
                        f"{price_str}{delta_tag}{_bonus_str(item)}  {C.DIM}base {item.base_value}gp{C.RESET}"
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
                if gp_delta > 0:
                    print(f"  {C.BGREEN}[Negotiation active: -{gp_delta}gp off every purchase]{C.RESET}")
                elif gp_delta < 0:
                    print(f"  {C.BRED}[Negotiation penalty: +{abs(gp_delta)}gp on every purchase]{C.RESET}")
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
                    desc_text  = item.description[:55] + ("…" if len(item.description) > 55 else "")
                    options.append(
                        f"{RARITY_COLOR.get(item.rarity, C.WHITE)}{item.name}{C.RESET}"
                        f"{tag}  {price_str}{affordable}{_bonus_str(item)}  "
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
    cost = 8
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
        print(f"  {C.BGREEN}You wake rested. HP and Mana fully restored. (−{cost}gp){C.RESET}")
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


# ── Jobs — commission sales ────────────────────────────────────────────────────

_JOB_CUSTOMERS = [
    ("Curious Townsperson",   "Looking around, no particular hurry.",       0),
    ("Cautious Homesteader",  "Careful with coin. Needs convincing.",       1),
    ("Eager Young Merchant",  "Wants to impress. Easy to read.",            0),
    ("Seasoned Tradesman",    "Seen it all. Hard sell.",                    2),
    ("Retired Soldier",       "Practical. Values reliability over charm.",  1),
    ("Merchant's Spouse",     "Shopping for the household.",                0),
    ("Minor Official",        "Self-important. Responds to status.",        2),
    ("Dockworker",            "No-nonsense. Wants a straight deal.",        1),
]

_HUNGER_PER_ATTEMPT = 25   # hunger cost per sales attempt (4 attempts = full day)
_MAX_ATTEMPTS       = 4


def jobs_screen(player: Player, city):
    """Commission sales job — pitch items to customers on behalf of a chosen merchant."""
    from engine.negotiate import MOTIVATIONS, APPEALS, _speechcraft_tier, _SPEECH_FEEDBACK

    global _city_merchants
    city_key  = city.key

    if city_key not in _city_merchants:
        _city_merchants[city_key] = generate_city_merchants(city_key)

    merchants = [m for m in _city_merchants[city_key]
                 if m.get("available") and m.get("stock")]

    if not merchants:
        clear()
        title_screen("JOBS")
        print(f"\n  {C.BBLACK}No merchants are looking for sales help today.{C.RESET}")
        pause()
        return

    # ── Choose a merchant to work for ─────────────────────────────────────────
    clear()
    title_screen("JOBS — MERCHANT'S ASSISTANT")
    print(f"  {C.DIM}Work as a sales agent. Earn 5% commission per closed deal.{C.RESET}")
    print(f"  {C.DIM}You have {_MAX_ATTEMPTS} pitches before hunger forces you to stop.{C.RESET}")
    print()

    m_options = [
        f"{C.BCYAN}{m['name']}{C.RESET}  {C.DIM}({m['type']}){C.RESET}"
        for m in merchants
    ]
    choice = prompt_choice(m_options, "Work for whom?")
    if choice == len(m_options):
        return

    merchant  = merchants[choice - 1]
    stock     = merchant["stock"]

    if not stock:
        print(f"\n  {C.BBLACK}{merchant['name']} has nothing in stock to sell.{C.RESET}")
        pause()
        return

    total_commission = 0
    deals_closed     = 0

    for attempt in range(1, _MAX_ATTEMPTS + 1):
        if player.hunger < _HUNGER_PER_ATTEMPT:
            clear()
            title_screen("JOBS")
            print(f"\n  {C.BRED}You're too hungry to keep working. Eat something first.{C.RESET}")
            pause()
            break

        item     = random.choice(stock)
        customer = random.choice(_JOB_CUSTOMERS)
        cust_name, cust_desc, difficulty = customer
        motivation_idx = random.randint(0, len(MOTIVATIONS) - 1)

        close_pct  = 35.0 + difficulty * -8
        insult_pct = 45.0 + difficulty * 10

        clear()
        title_screen(f"JOBS — PITCH {attempt}/{_MAX_ATTEMPTS}")
        print(f"  {C.DIM}Working for: {C.RESET}{C.BCYAN}{merchant['name']}{C.RESET}"
              f"  {C.DIM}({merchant['type']}){C.RESET}")
        print(f"  {C.BYELLOW}Gold: {player.gold}gp{C.RESET}  "
              f"{C.DIM}Hunger: {player.hunger}/100{C.RESET}")
        print()
        hr()
        print(f"  {C.BCYAN}Customer:{C.RESET}  {cust_name}")
        print(f"  {C.DIM}{cust_desc}{C.RESET}")
        print()
        sp   = sell_price(item, city, 0)
        commission = max(1, round(item.base_value * 0.05))
        print(f"  {C.BCYAN}Pitch item:{C.RESET}  "
              f"{RARITY_COLOR.get(item.rarity, C.WHITE)}{item.name}{C.RESET}"
              f"  {C.BYELLOW}{sp}gp{C.RESET}  "
              f"{C.DIM}(commission: {commission}gp if closed){C.RESET}")
        print()

        # 2-round pitch
        pitch_log = []
        for rnd in range(1, 3):
            print(f"  {C.DIM}Close chance: {close_pct:.0f}%   Insult: {insult_pct:.0f}%{C.RESET}")
            if pitch_log:
                for line in pitch_log:
                    print(f"  {line}")
            print()

            appeal_opts = [
                f"{C.BOLD}{label:<32}{C.RESET}  {C.DIM}{flavor}{C.RESET}"
                for _, label, flavor in APPEALS
            ]
            appeal_opts.append(f"{C.BYELLOW}Go for the close{C.RESET}  "
                               f"{C.DIM}({close_pct:.0f}% chance){C.RESET}")

            pick    = prompt_choice(appeal_opts, "Your pitch")
            if pick == len(appeal_opts):
                break

            mkey, _, _ = APPEALS[pick - 1]
            correct    = (mkey == MOTIVATIONS[motivation_idx])

            if correct:
                close_pct  = min(90.0, close_pct + 22.0)
                insult_pct = max(10.0, insult_pct - 15.0)
            else:
                insult_pct = min(90.0, insult_pct + 12.0)

            tier     = _speechcraft_tier(player)
            feedback = _SPEECH_FEEDBACK[tier][correct]
            tag      = f"{C.BGREEN}✓{C.RESET}" if correct else f"{C.BRED}✗{C.RESET}"
            pitch_log.append(f"{tag} {C.DIM}{feedback}{C.RESET}")

            clear()
            title_screen(f"JOBS — PITCH {attempt}/{_MAX_ATTEMPTS}  Round {rnd}/2")
            print(f"  {C.BCYAN}Customer:{C.RESET}  {cust_name}  {C.DIM}— {cust_desc}{C.RESET}")
            print(f"  {C.BCYAN}Item:{C.RESET}  {item.name}  {C.BYELLOW}{sp}gp{C.RESET}")
            print()

        # Resolve — lore bonus: Sellsword's Almanac boosts close rate
        from engine.lore_bonuses import get_lore_bonus
        effective_close = min(95.0, close_pct + get_lore_bonus(player, "jobs_close_pct"))
        agreement   = random.randint(1, 100) <= effective_close
        high_insult = random.randint(1, 100) <= insult_pct

        print()
        if agreement and not high_insult:
            player.hunger = max(0, player.hunger - _HUNGER_PER_ATTEMPT)
            player.gold  += commission
            total_commission += commission
            deals_closed     += 1
            print(f"  {C.BGREEN}Deal closed. +{commission}gp commission.{C.RESET}")
            print(f"  {C.DIM}Gold: {player.gold}gp  |  Hunger: {player.hunger}/100{C.RESET}")
        elif high_insult:
            player.hunger = max(0, player.hunger - _HUNGER_PER_ATTEMPT)
            print(f"  {C.BRED}They took offence and walked. No deal.{C.RESET}")
            print(f"  {C.DIM}Hunger: {player.hunger}/100{C.RESET}")
        else:
            player.hunger = max(0, player.hunger - _HUNGER_PER_ATTEMPT)
            print(f"  {C.BYELLOW}They weren't convinced. No deal.{C.RESET}")
            print(f"  {C.DIM}Hunger: {player.hunger}/100{C.RESET}")

        pause()

        if attempt < _MAX_ATTEMPTS:
            cont = prompt_choice([
                "Next customer",
                f"{C.BBLACK}Call it a day{C.RESET}",
            ])
            if cont == 2:
                break

    # Summary
    clear()
    title_screen("END OF SHIFT")
    print(f"  {C.DIM}You finish up with {merchant['name']}.{C.RESET}")
    print()
    print(f"  Deals closed:   {C.BYELLOW}{deals_closed}/{_MAX_ATTEMPTS}{C.RESET}")
    print(f"  Commission:     {C.BGREEN}+{total_commission}gp{C.RESET}")
    print(f"  Hunger remaining: {player.hunger}/100")
    if player.hunger < 30:
        print(f"\n  {C.BRED}You're running low on energy. Find food soon.{C.RESET}")
    pause()


# ── Library ──────────────────────────────────────────────────────────────────

_LIBRARY_ENTRIES = [
    (
        "How to Play",
        """\
  The Merchant's Road is a text-based RPG built on choices, skill checks, and trade.
  Your goal: earn gold, survive the road, and grow strong enough to take on harder
  challenges. Each city visit lets you trade, train, and prepare. Each road segment
  is a gauntlet of random events. Reach the next city — that is the game loop.\
""",
    ),
    (
        "Skills",
        """\
  MARTIAL       — Governs melee combat damage and accuracy.
  STEALTH       — Pickpocketing, evading enemies, prowling at night.
  DUNGEONEERING — Traps, puzzles, maze navigation, exploration rewards.
  SURVIVAL      — Bushcraft, hunting, foraging, resisting road hazards.
  MAGIC         — Spell power and mana pool. Unarmoured characters gain +3 passive.
  SPEECHCRAFT   — Negotiation, persuasion, diplomacy checks.
  MERCHANTILISM — Buy/sell prices, trade margins, negotiation close bonus.\
""",
    ),
    (
        "Combat",
        """\
  Combat is resolved in rounds. Each round you choose: Attack, use a Spell,
  use an Item, or Flee. Weapons have damage types (Slash, Pierce, Bash) that
  interact with enemy armour. Higher Martial = more damage dealt and better
  hit chance. Enemies have HP and armour types (none, cloth, leather, mail).
  Spells cost Mana and scale with your Magic skill. Fleeing uses Stealth +
  Survival to determine escape success.\
""",
    ),
    (
        "The Road",
        """\
  Each step on the road costs Hunger. Reach 0 Hunger and you take HP damage
  per step. Keep food and firewood in your pack. Random events occur each step
  — encounters, discoveries, hazards. Biome affects what you find: forests give
  herbs and game; mountains give ore; deserts are harsh but reward high Survival.
  Road poison: -5 HP per step for 2 steps. Disease: -5 HP per step until town.
  Both can be cured by camping with a Herb Bundle.\
""",
    ),
    (
        "Dungeons & Locations",
        """\
  Locations (caves, castles) are branching room graphs. Start at the entry and
  navigate toward the boss. Side rooms include: Traps (Dungeoneering + Survival
  check), Puzzles (riddles, sequences, mazes — Dungeoneering), Secrets (hidden
  loot), Dead Ends (atmosphere + occasional items). Bosses guard rare loot.
  Press [0] to retreat from any room. Trap rooms always have a Back exit —
  you are never forced out unless the dungeon collapses.\
""",
    ),
    (
        "Negotiation",
        """\
  Visit a merchant and choose Negotiate. You have up to 3 rounds to appeal to
  their motivation (Status, Acceptance, Control, Certainty). Match their hidden
  motivation to build your Close chance. Go for the Close when ready — or wait
  and be forced into it at round 4. A successful deal gives a per-transaction
  gp bonus (shown on buy/sell screens). A botched deal gives a penalty.
  High insult + no agreement = ejected. Merchantilism and Speechcraft both help.\
""",
    ),
    (
        "Camping & Hunger",
        """\
  Hunger depletes each road step. Eat food directly from your Bag to partially
  restore it. To camp: you need Firewood + at least 1 food item.
  Quick camp (1 food + 1 firewood): partial HP/mana and hunger restore.
  Sleep overnight (2 food + 1 firewood): full hunger reset to 100, HP restored,
  one day passes. Herb Bundle at camp cures poison and disease.
  Bushcraft (Survival skill) lets you forage food and firewood on the road.\
""",
    ),
    (
        "Stealth & Prowl",
        """\
  Prowl is available in cities with 10+ Stealth. On the streets you can attempt
  to Pickpocket citizens — governed by Stealth. Success yields items or gold.
  Failure raises City Heat. At 100 Heat you become Wanted — guards attack on entry.
  Heat decays slowly over road travel. When entering dungeons with enemies, a
  Stealth check lets you attempt a surprise attack or sneak past them entirely.\
""",
    ),
    (
        "Equipment & Armour",
        """\
  Armour types: Cloth (+Magic, light), Leather (+Stealth, +Survival),
  Mail (+Martial, +Survival, -Stealth). Stat bonuses are always visible in
  the buy/sell screens and on your Character Sheet. Rings and Necklaces grant
  passive skill bonuses when equipped. Cursed items cannot be unequipped and
  some reduce your max HP — the penalty is shown on your Character Sheet.
  Weapons have damage types that counter specific armour (Bash vs mail, etc.).\
""",
    ),
    (
        "Training",
        """\
  Visit the Training Hall to spend gold raising a skill directly.
  Cost scales with your current level: cheap at low levels, expensive at high.
  Tiers: 1–24 (20gp), 25–49 (55gp), 50–74 (130gp), 75+ (300gp).
  Skills gained through combat, negotiation, and exploration can push beyond
  the training cap. Items and equipment add on top of your base skill scores.\
""",
    ),
]


def library_screen(player: Player):
    """The Library — game reference manual and inventory book/grimtotem reader."""
    from ui.display import typewrite

    while True:
        clear()
        title_screen("THE LIBRARY")
        print(f"  {C.DIM}A reference for travellers. Knowledge freely given.{C.RESET}")
        print()

        readable_items = [i for i in player.inventory
                          if i.item_type in ("book", "grimtotem")]
        read_hint = (
            f"  {C.BYELLOW}({len(readable_items)} item{'s' if len(readable_items) != 1 else ''}){C.RESET}"
            if readable_items else f"  {C.DIM}(none in inventory){C.RESET}"
        )

        options = [f"{C.BCYAN}{title}{C.RESET}" for title, _ in _LIBRARY_ENTRIES]
        options.append(f"Read from inventory{read_hint}")
        options.append(f"{C.BBLACK}← Back{C.RESET}")

        choice = prompt_choice(options, "Open which section?")

        if choice == len(options):
            return
        if choice == len(options) - 1:
            read_book_menu(player)
            continue

        title, body = _LIBRARY_ENTRIES[choice - 1]
        clear()
        title_screen(f"LIBRARY — {title.upper()}")
        print()
        for line in body.split("\n"):
            print(line)
        print()
        pause("Press Enter to return to the Library...")


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
            f"Rest at the Inn   {C.DIM}(restore HP & mana — 8gp){C.RESET}",
            prowl_label,
            f"Jobs              {C.DIM}(pitch wares for a merchant — earn commission){C.RESET}",
            f"Character Sheet   {C.DIM}(stats, equipment, inventory){C.RESET}",
            f"Library           {C.DIM}(game reference + books){C.RESET}{book_hint}",
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
            jobs_screen(player, city)
        elif choice == 7:
            show_character_sheet(player)
        elif choice == 8:
            library_screen(player)
        elif choice == 9:
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
