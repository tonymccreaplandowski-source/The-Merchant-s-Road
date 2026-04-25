import random
from engine.player import Player
from ui.display import C, clear, pause, title_screen, prompt_choice, play_melody, hr, section, typewrite


MARKS = [
    # (name, desc, min_stealth, gold_min, gold_max, awareness, is_connected)
    ("Drunk Beggar",         "Barely upright. Probably empty.",               0,   1,   8,  10, False),
    ("Weary Traveller",      "Road-worn. Staring into nothing.",             15,   6,  18,  20, False),
    ("City Peasant",         "Busy with errands. Alert enough.",             25,  10,  28,  30, False),
    ("Market Vendor",        "Eyes on their stall, not their purse.",        35,  18,  45,  40, False),
    ("Touring Merchant",     "Fat purse. Used to being comfortable.",        45,  30,  70,  50, False),
    ("Minor Noble",          "Draped in entitlement. Richer than they look.",60,  50, 110,  60, False),
    ("City Magistrate",      "Sharp eyes. Connected. Dangerous.",            75,  70, 160,  75, True),
    ("Guild Master",         "Moves like someone who expects to be watched.",85,  90, 220,  85, True),
]


def _decay_heat(player: Player, city_key: str) -> None:
    heat = player.city_heat.get(city_key, 0)
    if heat <= 0:
        return
    decay = min(30, (player.days_elapsed // 2) * 5)
    player.city_heat[city_key] = max(0, heat - decay)


def _select_mark(player: Player, city_key: str) -> tuple:
    stealth   = player.skill("Stealth")
    available = [m for m in MARKS if stealth >= m[2]]
    if not available:
        available = [MARKS[0]]

    weights = [i + 1 for i in range(len(available))]
    mark    = random.choices(available, weights=weights, k=1)[0]

    heat                 = player.city_heat.get(city_key, 0)
    heat_awareness_bonus = min(40, (heat // 20) * 10)

    name, desc, min_stl, gold_min, gold_max, base_awareness, is_connected = mark
    effective_awareness = base_awareness + heat_awareness_bonus

    return name, desc, gold_min, gold_max, effective_awareness, is_connected


def _caught_screen(player: Player, city_key: str, mark_name: str, is_connected: bool, gold_stolen: int) -> str:
    """
    Returns one of: "escaped", "paid_off", "talked_out", "fought_won", "wanted", "dead"
    """
    from data.enemies import spawn_city_guard
    from ui.combat_loop import run_combat

    stealth     = player.skill("Stealth")
    speechcraft = player.skill("Speechcraft")
    martial     = player.skill("Martial")

    clear()
    title_screen("CAUGHT")

    caught_lines = {
        "Drunk Beggar":      '"Oi! My coin! Thief! Someone— someone help!"',
        "Weary Traveller":   '"What — hey! Get your hand out of my— stop him!"',
        "City Peasant":      '"Thief! Thief in the market! Guard! GUARD!"',
        "Market Vendor":     '"I felt that, you little rat. Hands where I can see them."',
        "Touring Merchant":  '"Oh, how bold. Do you have any idea who I deal with?"',
        "Minor Noble":       '"How DARE you. Do you know who I am? Guards! GUARDS!"',
        "City Magistrate":   '"Step. Away. Slowly. And pray I\'m in a forgiving mood."',
        "Guild Master":      '"Interesting choice. I\'ll give you one breath to explain yourself."',
    }
    line = caught_lines.get(mark_name, '"Stop right there!"')
    print(f"\n  {C.BRED}You've been caught.{C.RESET}")
    print(f"  {C.DIM}{line}{C.RESET}")
    print()

    fine = gold_stolen + (gold_stolen // 2) + random.randint(5, 15)

    options = [
        f"Run               {C.DIM}[Stealth: {stealth}] — bolt and hope{C.RESET}",
        f"Talk your way out {C.DIM}[Speechcraft: {speechcraft}] — deny everything{C.RESET}",
        f"Intimidate        {C.DIM}[Martial: {martial}] — threaten them into silence{C.RESET}",
        f"Pay the fine      {C.DIM}({fine}gp — end this cleanly){C.RESET}",
        f"Fight             {C.DIM}[Martial: {martial}] — desperate option{C.RESET}",
    ]
    choice = prompt_choice(options, "Your move")

    # ── Run ──────────────────────────────────────────────────────────────────
    if choice == 1:
        roll      = random.randint(1, 20) + stealth // 4
        threshold = 12 + (4 if is_connected else 0)
        if roll >= threshold:
            print(f"\n  {C.BGREEN}You spin and bolt through the crowd. By the time they react, you're gone.{C.RESET}")
            pause()
            return "escaped"
        else:
            print(f"\n  {C.BRED}You shove through the crowd but a hand catches your collar.{C.RESET}")
            print(f"  {C.DIM}You've only made it worse.{C.RESET}")
            pause()
            player.city_wanted.add(city_key)
            player.city_heat[city_key] = min(100, player.city_heat.get(city_key, 0) + 25)
            print(f"\n  {C.BRED}You're known in this city now. The guard will be watching for you.{C.RESET}")
            pause()
            return "wanted"

    # ── Talk your way out ────────────────────────────────────────────────────
    elif choice == 2:
        roll      = random.randint(1, 20) + speechcraft // 4
        threshold = 14 if is_connected else 11
        if roll >= threshold:
            print(f"\n  {C.BGREEN}\"What? Me? I stumbled — I was trying to catch them before they fell.\"")
            print(f"  {C.DIM}They don't fully believe you, but the crowd is watching and the accusation is thin.{C.RESET}")
            print(f"  {C.BYELLOW}They let it go. This time.{C.RESET}")
            pause()
            return "talked_out"
        else:
            print(f"\n  {C.BRED}Your story falls apart under their stare. They're not buying it.{C.RESET}")
            player.city_heat[city_key] = min(100, player.city_heat.get(city_key, 0) + 15)
            if is_connected:
                player.city_wanted.add(city_key)
                print(f"  {C.BRED}They call for the guard. You're wanted in this city.{C.RESET}")
                pause()
                return "wanted"
            else:
                print(f"  {C.BYELLOW}They demand the fine: {fine}gp.{C.RESET}")
                if player.gold >= fine:
                    player.gold -= fine
                    print(f"  {C.DIM}You hand it over. They watch you go with hard eyes.{C.RESET}")
                    pause()
                    return "paid_off"
                else:
                    print(f"  {C.BRED}You don't have enough. They don't accept credit.{C.RESET}")
                    player.city_wanted.add(city_key)
                    pause()
                    return "wanted"

    # ── Intimidate ───────────────────────────────────────────────────────────
    elif choice == 3:
        roll      = random.randint(1, 20) + martial // 4
        threshold = 18 if is_connected else 13
        if roll >= threshold:
            print(f"\n  {C.BGREEN}You lean in close. Your hand rests on your weapon.{C.RESET}")
            print(f'  {C.DIM}"Make a sound and I\'ll give you a reason to."')
            print(f"  {C.BYELLOW}They go pale. They say nothing. You walk.{C.RESET}")
            pause()
            return "escaped"
        else:
            if is_connected:
                print(f"\n  {C.BRED}They don't flinch. \"Guards! Assault and theft!\" You've escalated this badly.{C.RESET}")
                player.city_wanted.add(city_key)
                player.city_heat[city_key] = min(100, player.city_heat.get(city_key, 0) + 30)
                pause()
                return "wanted"
            else:
                print(f"\n  {C.BRED}They're not as scared as you hoped. They've found their voice.{C.RESET}")
                player.city_heat[city_key] = min(100, player.city_heat.get(city_key, 0) + 10)
                print(f"  {C.BYELLOW}They demand the fine: {fine}gp.{C.RESET}")
                if player.gold >= fine:
                    player.gold -= fine
                    print(f"  {C.DIM}You pay. They back off, shaken but satisfied.{C.RESET}")
                    pause()
                    return "paid_off"
                else:
                    player.city_wanted.add(city_key)
                    print(f"  {C.BRED}You can't pay. They scream. You're wanted.{C.RESET}")
                    pause()
                    return "wanted"

    # ── Pay the fine ─────────────────────────────────────────────────────────
    elif choice == 4:
        if player.gold >= fine:
            player.gold -= fine
            print(f"\n  {C.BYELLOW}You hand over the gold without a word.{C.RESET}")
            print(f"  {C.DIM}They watch you go. Smarter than you looked, apparently.{C.RESET}")
            pause()
            return "paid_off"
        else:
            print(f"\n  {C.BRED}You don't have {fine}gp. They're not sympathetic.{C.RESET}")
            player.city_wanted.add(city_key)
            player.city_heat[city_key] = min(100, player.city_heat.get(city_key, 0) + 20)
            print(f"  {C.BRED}They call it in. You're wanted.{C.RESET}")
            pause()
            return "wanted"

    # ── Fight ────────────────────────────────────────────────────────────────
    elif choice == 5:
        print(f"\n  {C.BRED}You reach for your weapon. This was always going to get ugly.{C.RESET}")
        pause("Press Enter to fight...")

        if is_connected:
            print(f"\n  {C.BRED}A guard was already nearby. You're surrounded.{C.RESET}")
            pause()
            guard = spawn_city_guard()
            won   = run_combat(player, guard)
            if not player.is_alive():
                return "dead"
            if not won:
                player.city_wanted.add(city_key)
                return "wanted"
            guard2 = spawn_city_guard()
            won    = run_combat(player, guard2)
            if not player.is_alive():
                return "dead"
            if not won:
                player.city_wanted.add(city_key)
                return "wanted"
        else:
            from data.enemies import spawn_enemy
            brawler_template = {
                "name":          f"Angry {mark_name}",
                "armor_type":    "none",
                "hp_range":      (20, 40),
                "combat_range":  (15, 28),
                "defense_range": (8,  18),
                "agility_range": (20, 40),
                "description":   "Furious, swinging wildly.",
                "biomes":        [],
                "loot_bias":     "common",
                "enemy_type":    "combat",
                "enemy_spells":  [],
                "moves":         ["Strike", "Shove"],
            }
            opponent = spawn_enemy(brawler_template)
            won      = run_combat(player, opponent)
            if not player.is_alive():
                return "dead"
            if not won:
                player.city_wanted.add(city_key)
                return "wanted"

        player.city_wanted.add(city_key)
        player.city_heat[city_key] = min(100, player.city_heat.get(city_key, 0) + 35)
        print(f"\n  {C.BYELLOW}They're down. But people saw. You need to move.{C.RESET}")
        print(f"  {C.BRED}You're wanted in this city.{C.RESET}")
        pause()
        return "fought_won"

    return "escaped"


def _pickpocket_attempt(player: Player, city_key: str, mark_name: str, mark_desc: str,
                        gold_min: int, gold_max: int, awareness: int, is_connected: bool) -> None:
    stealth     = player.skill("Stealth")
    speechcraft = player.skill("Speechcraft")
    survival    = player.skill("Survival")

    lift_chance   = max(15.0, 35.0 - awareness * 0.15)
    suspicion_pct = min(80.0, 30.0 + awareness * 0.40)

    log = []

    for round_num in range(1, 4):
        if lift_chance >= 80:
            break

        clear()
        title_screen(f"PROWL — {mark_name.upper()}  (Round {round_num}/3)")
        print(f"  {C.DIM}{mark_desc}{C.RESET}")
        print()
        if log:
            for line in log:
                print(f"  {line}")
            print()
        print(f"  {C.BYELLOW}Lift chance:   {lift_chance:.0f}%{C.RESET}   "
              f"{C.BRED}Suspicion:  {suspicion_pct:.0f}%{C.RESET}")
        print()

        options = [
            f"Read the mark        {C.DIM}[Stealth: {stealth}] — study their patterns{C.RESET}",
            f"Create a distraction {C.DIM}[Speechcraft: {speechcraft}] — misdirect their attention{C.RESET}",
            f"Scout the crowd      {C.DIM}[Survival: {survival}] — check for witnesses{C.RESET}",
            f"Go for the lift      {C.DIM}(attempt at current odds){C.RESET}",
            f"Walk away            {C.DIM}(clean exit, no heat){C.RESET}",
        ]
        choice = prompt_choice(options, "Your approach")

        if choice == 5:
            print(f"\n  {C.DIM}You drift away through the crowd. Nobody noticed. Nobody ever does.{C.RESET}")
            pause()
            return

        if choice == 4:
            break

        if choice == 1:
            roll = random.randint(1, 20) + stealth // 4
            if roll >= 13:
                gain          = 6 + stealth // 12
                lift_chance   = min(85, lift_chance + gain)
                suspicion_pct = max(10, suspicion_pct - 5)
                log.append(f"{C.BGREEN}✓ You clock their patterns. +{gain:.0f}% lift / suspicion ↓{C.RESET}")
            else:
                suspicion_pct = min(90, suspicion_pct + 5)
                log.append(f"{C.BRED}✗ You linger too long. They're starting to notice you. Suspicion ↑{C.RESET}")

        elif choice == 2:
            roll = random.randint(1, 20) + speechcraft // 4
            if roll >= 12:
                gain          = 8 + speechcraft // 15
                lift_chance   = min(85, lift_chance + gain)
                suspicion_pct = max(10, suspicion_pct - 10)
                log.append(f"{C.BGREEN}✓ The distraction lands. Their attention snaps away. +{gain:.0f}% lift / suspicion ↓↓{C.RESET}")
            else:
                suspicion_pct = min(90, suspicion_pct + 8)
                log.append(f"{C.BRED}✗ You overplay it. They're looking right at you now. Suspicion ↑{C.RESET}")

        elif choice == 3:
            roll = random.randint(1, 20) + survival // 4
            if roll >= 11:
                suspicion_pct = max(10, suspicion_pct - 8)
                log.append(f"{C.BGREEN}✓ You read the crowd. You know who's watching. Suspicion ↓{C.RESET}")
            else:
                log.append(f"{C.BBLACK}✗ The crowd gives nothing away. You're no wiser.{C.RESET}")

    # ── Final lift ────────────────────────────────────────────────────────────
    clear()
    title_screen(f"THE LIFT — {mark_name.upper()}")
    for line in log:
        print(f"  {line}")
    print()
    print(f"  {C.BYELLOW}Lift chance: {lift_chance:.0f}%   "
          f"{C.BRED}Suspicion: {suspicion_pct:.0f}%{C.RESET}")
    print()
    pause("Press Enter to make your move...")

    lift_roll = random.randint(1, 100)
    caught    = random.randint(1, 100) <= suspicion_pct

    if lift_roll <= lift_chance and not caught:
        gold_taken = random.randint(gold_min, gold_max)
        player.gold += gold_taken
        player.city_heat[city_key] = min(100, player.city_heat.get(city_key, 0) + 8)
        play_melody("victory")
        clear()
        title_screen("CLEAN LIFT")
        print(f"\n  {C.BGREEN}Your fingers close around it. By the time you've turned the corner, it's yours.{C.RESET}")
        print()
        print(f"  {C.BYELLOW}+{gold_taken}gp{C.RESET}")
        heat = player.city_heat.get(city_key, 0)
        print(f"  {C.DIM}City heat: {heat}/100{C.RESET}")
        pause()

    elif lift_roll <= lift_chance and caught:
        gold_taken = random.randint(gold_min, gold_max)
        player.city_heat[city_key] = min(100, player.city_heat.get(city_key, 0) + 20)
        clear()
        print(f"\n  {C.BRED}You got the purse — but they felt it go.{C.RESET}")
        pause()
        outcome = _caught_screen(player, city_key, mark_name, is_connected, gold_taken)
        if outcome == "fought_won":
            player.gold += gold_taken

    else:
        player.city_heat[city_key] = min(100, player.city_heat.get(city_key, 0) + 15)
        clear()
        if caught:
            print(f"\n  {C.BRED}Their hand shoots to their pocket the same moment yours does.{C.RESET}")
            pause()
            _caught_screen(player, city_key, mark_name, is_connected, 0)
        else:
            print(f"\n  {C.BYELLOW}You fumble it. The purse stays where it is. They didn't notice — small mercy.{C.RESET}")
            pause()


def _mug_attempt(player: Player, city_key: str, mark_name: str, mark_desc: str,
                 gold_min: int, gold_max: int, awareness: int, is_connected: bool) -> None:
    stealth = player.skill("Stealth")
    martial = player.skill("Martial")

    clear()
    title_screen(f"MUGGING — {mark_name.upper()}")
    print(f"\n  {C.DIM}{mark_desc}{C.RESET}")
    print()
    print(f"  {C.BRED}This isn't subtle. It's direct. And it's going to cost this city's opinion of you.{C.RESET}")
    print()
    print(f"  {C.BYELLOW}Martial: {martial}   Stealth (escape): {stealth}{C.RESET}")
    print()

    options = [
        f"Step to them  {C.DIM}[Martial] — walk up and take it{C.RESET}",
        f"Back off      {C.DIM}(change your mind){C.RESET}",
    ]
    choice = prompt_choice(options, "")

    if choice == 2:
        print(f"\n  {C.DIM}You think better of it. Some lines stay uncrossed.{C.RESET}")
        pause()
        return

    roll      = random.randint(1, 20) + martial // 4
    threshold = 8 + awareness // 8

    mug_heat = 30 + (10 if is_connected else 0)
    player.city_heat[city_key] = min(100, player.city_heat.get(city_key, 0) + mug_heat)

    clear()
    title_screen(f"MUGGING — {mark_name.upper()}")

    if roll >= threshold:
        gold_taken = random.randint(gold_min, gold_max + 20)
        player.gold += gold_taken
        print(f"\n  {C.BRED}You step into their path. The message is clear enough.{C.RESET}")
        print(f"  {C.DIM}They hand it over. Nobody argues with the look in your eyes.{C.RESET}")
        print()
        print(f"  {C.BYELLOW}+{gold_taken}gp{C.RESET}")
        print()

        escape_roll = random.randint(1, 20) + stealth // 4
        if escape_roll >= 12:
            print(f"  {C.BGREEN}You're around the corner before anyone processes what happened.{C.RESET}")
        else:
            player.city_wanted.add(city_key)
            player.city_heat[city_key] = min(100, player.city_heat.get(city_key, 0) + 20)
            print(f"  {C.BRED}Someone saw. Word travels fast in a city this size.{C.RESET}")
            print(f"  {C.BRED}You're wanted here now.{C.RESET}")

        heat = player.city_heat.get(city_key, 0)
        print(f"\n  {C.DIM}City heat: {heat}/100{C.RESET}")
        pause()

    else:
        print(f"\n  {C.BRED}You step to them but they don't back down. This is going sideways.{C.RESET}")
        print()
        pause()

        if is_connected:
            player.city_wanted.add(city_key)
            print(f"  {C.BRED}They're already calling for help. Guards will be watching for you.{C.RESET}")
            pause()
        else:
            from data.enemies import spawn_enemy
            from ui.combat_loop import run_combat
            brawler_template = {
                "name":          f"Resisting {mark_name}",
                "armor_type":    "none",
                "hp_range":      (25, 45),
                "combat_range":  (18, 30),
                "defense_range": (10, 20),
                "agility_range": (20, 38),
                "description":   "They've decided they'd rather fight than hand it over.",
                "biomes":        [],
                "loot_bias":     "common",
                "enemy_type":    "combat",
                "enemy_spells":  [],
                "moves":         ["Strike", "Shove"],
            }
            opponent = spawn_enemy(brawler_template)
            won      = run_combat(player, opponent)
            if not player.is_alive():
                return
            if not won:
                player.city_wanted.add(city_key)
                print(f"\n  {C.BRED}You couldn't finish it. You're known here now.{C.RESET}")
                pause()
            else:
                player.city_wanted.add(city_key)
                print(f"\n  {C.BYELLOW}You walked away from it — but someone saw everything.{C.RESET}")
                print(f"  {C.BRED}You're wanted in this city.{C.RESET}")
                pause()


def _heat_label(heat: int) -> str:
    if heat == 0:
        return f"{C.BGREEN}Clean{C.RESET}"
    elif heat < 25:
        return f"{C.BYELLOW}Low heat{C.RESET}"
    elif heat < 50:
        return f"{C.BYELLOW}Noticed{C.RESET}"
    elif heat < 75:
        return f"{C.BRED}Hot{C.RESET}"
    else:
        return f"{C.BRED}Burning{C.RESET}"


def prowl_screen(player: Player) -> None:
    city_key = player.current_city
    _decay_heat(player, city_key)

    heat      = player.city_heat.get(city_key, 0)
    is_wanted = city_key in player.city_wanted

    mark_name, mark_desc, gold_min, gold_max, awareness, is_connected = _select_mark(player, city_key)

    clear()
    title_screen("PROWL")

    if is_wanted:
        print(f"\n  {C.BRED}You're wanted here. The guard knows your face.{C.RESET}")
        print(f"  {C.DIM}Working the streets with a price on your head is suicide.{C.RESET}")
        pause()
        return

    print(f"\n  {C.DIM}You scan the crowd. It doesn't take long.{C.RESET}")
    print()
    print(f"  {C.BYELLOW}Mark:{C.RESET}  {mark_name}")
    print(f"  {C.DIM}{mark_desc}{C.RESET}")
    print()
    print(f"  {C.DIM}Awareness:    {awareness}/100{C.RESET}")
    print(f"  {C.DIM}City heat:    {_heat_label(heat)}  ({heat}/100){C.RESET}")
    if is_connected:
        print(f"  {C.BRED}[Connected] — this mark has reach. Getting caught will escalate.{C.RESET}")
    print()

    martial = player.skill("Martial")
    options = [
        f"Pickpocket  {C.DIM}[Stealth] — quiet, careful, lower heat{C.RESET}",
        f"Mug them    {C.DIM}[Martial: {martial}] — direct, high heat, significant risk{C.RESET}",
        f"Walk away   {C.DIM}(leave the streets){C.RESET}",
    ]
    choice = prompt_choice(options, "Your approach")

    if choice == 3:
        print(f"\n  {C.DIM}You think better of it. The crowd swallows you whole.{C.RESET}")
        pause()
        return

    if choice == 1:
        _pickpocket_attempt(player, city_key, mark_name, mark_desc,
                            gold_min, gold_max, awareness, is_connected)
    elif choice == 2:
        _mug_attempt(player, city_key, mark_name, mark_desc,
                     gold_min, gold_max, awareness, is_connected)
