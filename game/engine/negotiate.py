"""
Negotiation mini-game — appeal system, session state, close resolution, outcome matrix.
"""

import random

from engine.player import Player
from ui.display import C, clear, pause, title_screen, prompt_choice, play_melody


MOTIVATIONS = [
    "status_approval",
    "love_acceptance",
    "control_authority",
    "safety_certainty",
]

APPEALS = [
    ("status_approval",   "Appeal to their reputation",
     '"After this, everyone in the city will know your name..."'),
    ("love_acceptance",   "Appeal to common ground",
     '"We\'re both just trying to get by out here. Help me and I\'ll remember it..."'),
    ("control_authority", "Defer to their judgment",
     '"You know this trade better than anyone. I trust your call on this..."'),
    ("safety_certainty",  "Offer certainty",
     '"No risk to you. I\'m not asking for a favour — just a fair arrangement..."'),
]

_SPEECH_FEEDBACK = {
    "certain": {
        True:  "Something in their posture opens. You're getting through.",
        False: "They stiffen. That was the wrong note.",
    },
    "tepid": {
        True:  "The merchant shifts slightly. Hard to tell.",
        False: "A flicker crosses their face. Uncertain.",
    },
    "ambiguous": {
        True:  "Their expression gives nothing away.",
        False: "Their expression gives nothing away.",
    },
}


def _p_dominant(player: Player) -> str:
    return max(player.skills, key=lambda s: player.skills[s])


def _speechcraft_tier(player: Player) -> str:
    val = player.skill("Speechcraft")
    if val >= 70:
        return "certain"
    if val >= 35:
        return "tepid"
    return "ambiguous"


def _apply_correct(player: Player, merchant: dict, session: dict) -> None:
    p_dom = _p_dominant(player)
    if p_dom == "Merchantilism":
        close_bonus   = player.skill("Merchantilism") * 0.10
        insult_reduce = player.skill("Merchantilism") * 0.08
    elif p_dom == "Speechcraft":
        close_bonus   = player.skill("Speechcraft") * 0.05
        insult_reduce = player.skill("Speechcraft") * 0.04
    elif p_dom == merchant["dominant_skill"]:
        close_bonus   = player.skill(p_dom) * 0.05
        insult_reduce = player.skill(p_dom) * 0.04
    else:
        close_bonus   = 0.0
        insult_reduce = 0.0

    session["close_pct"]  = min(85.0, session["close_pct"] + 8.0 + close_bonus)
    insult_delta          = max(3.0, 12.0 - insult_reduce)
    session["insult_pct"] = max(15.0, session["insult_pct"] - insult_delta)
    session["rounds_won"] += 1


def _apply_wrong(player: Player, merchant: dict, session: dict) -> None:
    p_dom = _p_dominant(player)
    if p_dom == "Merchantilism":
        insult_reduce = player.skill("Merchantilism") * 0.08
    elif p_dom == "Speechcraft":
        insult_reduce = player.skill("Speechcraft") * 0.04
    elif p_dom == merchant["dominant_skill"]:
        insult_reduce = player.skill(p_dom) * 0.04
    else:
        insult_reduce = 0.0

    insult_gain           = max(3.0, 12.0 - insult_reduce)
    session["insult_pct"] = session["insult_pct"] + insult_gain


def _insult_level(insult_pct: float) -> str:
    """Roll insult level using insult_pct as the high-insult threshold."""
    roll = random.randint(1, 100)
    if roll <= insult_pct:
        return "high"
    if roll <= insult_pct + 20:
        return "medium"
    return "low"


def _gp_vector(player: Player, agreement: bool) -> list:
    p_dom      = _p_dominant(player)
    gp_vector  = list(range(1, 11))
    choke_rate = 0.005 if p_dom == "Merchantilism" else 0.0025
    choke_pct  = player.skill(p_dom) * choke_rate
    choke_n    = round(choke_pct * len(gp_vector))
    choke_n    = max(0, min(choke_n, len(gp_vector) - 1))

    if agreement:
        gp_vector = gp_vector[choke_n:]
    else:
        gp_vector = gp_vector[:len(gp_vector) - choke_n] if choke_n > 0 else gp_vector

    return gp_vector if gp_vector else [1]


def _resolve_close(player: Player, merchant: dict, session: dict) -> tuple:
    agreement    = random.randint(1, 100) <= session["close_pct"]
    insult_level = _insult_level(session["insult_pct"])
    vec          = _gp_vector(player, agreement)
    gp_value     = random.choice(vec)

    if not agreement and insult_level == "high":
        merchant["ejected"]  = True
        merchant["gp_delta"] = 0
        result = "ejected"
    elif agreement and insult_level == "high":
        merchant["gp_delta"] = -gp_value
        result = "agree_high"
    elif agreement:
        merchant["gp_delta"] = +gp_value
        result = "agree"
    else:
        merchant["gp_delta"] = -gp_value
        result = "no_agree"

    merchant["negotiated"] = True
    return result, gp_value, insult_level


def _display_result(merchant: dict, session: dict, result: str, gp_value: int, insult_level: str) -> None:
    clear()
    title_screen("NEGOTIATION RESULT")
    for line in session["log"]:
        print(f"  {line}")
    if session["log"]:
        print()

    if result == "ejected":
        print(f"  {C.BRED}They've had enough. {merchant['name']} throws you out — "
              f"you won't be welcome here again.{C.RESET}")
        play_melody("negotiate_lose")
    elif result == "agree":
        print(f"  {C.BGREEN}They agree. +{gp_value}gp advantage on all trades "
              f"with {merchant['name']}.{C.RESET}")
        print(f"  {C.DIM}Insult level: {insult_level}{C.RESET}")
        play_melody("negotiate_win")
    elif result == "agree_high":
        print(f"  {C.BYELLOW}They accept, but the deal is sour. "
              f"-{gp_value}gp penalty on all trades.{C.RESET}")
        print(f"  {C.DIM}The insult runs deep despite the agreement.{C.RESET}")
        play_melody("negotiate_lose")
    else:
        print(f"  {C.BRED}No deal. -{gp_value}gp penalty on all trades.{C.RESET}")
        print(f"  {C.DIM}Insult level: {insult_level}{C.RESET}")
        play_melody("negotiate_lose")

    print()
    print(f"  {C.DIM}Rounds won: {session['rounds_won']}/3{C.RESET}")
    pause()


def _go_for_close(player: Player, merchant: dict, session: dict, forced: bool) -> None:
    clear()
    title_screen(f"NEGOTIATE — {merchant['name']}  ({merchant['type']})")
    if forced:
        print(f"\n  {C.DIM}Tensions have run as high as they can. "
              f"There's nothing left to say — only to see how it lands.{C.RESET}")
        print()
    for line in session["log"]:
        print(f"  {line}")
    if session["log"]:
        print()
    print(f"  {C.BYELLOW}Close chance:   {session['close_pct']:.0f}%{C.RESET}")
    print(f"  {C.BRED}Insult chance:  {session['insult_pct']:.0f}%{C.RESET}")
    print()
    pause("Press Enter to close the deal...")
    result, gp_value, insult_level = _resolve_close(player, merchant, session)
    _display_result(merchant, session, result, gp_value, insult_level)


def negotiate_session(player: Player, merchant: dict) -> None:
    if merchant.get("ejected"):
        clear()
        title_screen(f"NEGOTIATE — {merchant['name']}")
        print(f"\n  {C.BRED}You were thrown out. {merchant['name']} won't speak to you.{C.RESET}")
        pause()
        return

    if merchant.get("negotiated"):
        delta = merchant.get("gp_delta", 0)
        if delta > 0:
            label = f"{C.BGREEN}Already negotiated — +{delta}gp advantage active.{C.RESET}"
        elif delta < 0:
            label = f"{C.BRED}Already negotiated — {abs(delta)}gp penalty active.{C.RESET}"
        else:
            label = f"{C.DIM}Already negotiated — no deal reached.{C.RESET}"
        clear()
        title_screen(f"NEGOTIATE — {merchant['name']}")
        print(f"\n  {label}")
        pause()
        return

    session = {
        "close_pct":  35.0,
        "insult_pct": 65.0,
        "round":      1,
        "rounds_won": 0,
        "log":        [],
    }

    for round_num in range(1, 5):
        session["round"] = round_num

        if round_num == 4:
            _go_for_close(player, merchant, session, forced=True)
            return

        clear()
        title_screen(f"NEGOTIATE — {merchant['name']}  ({merchant['type']})")
        print(f"  {C.DIM}\"{merchant['tagline']}\"{C.RESET}")
        print()
        if session["log"]:
            for line in session["log"]:
                print(f"  {line}")
            print()
        print(f"  {C.BYELLOW}Round {round_num}/3   "
              f"Close: {session['close_pct']:.0f}%   "
              f"Insult: {session['insult_pct']:.0f}%{C.RESET}")
        print()

        options = []
        for _, label, flavor in APPEALS:
            options.append(f"{C.BOLD}{label:<32}{C.RESET}  {C.DIM}{flavor}{C.RESET}")
        options.append(
            f"{C.BYELLOW}Go for the Close{C.RESET}  "
            f"{C.DIM}(Close: {session['close_pct']:.0f}% / "
            f"Insult: {session['insult_pct']:.0f}%){C.RESET}"
        )
        options.append(f"{C.BBLACK}← Walk away{C.RESET}")

        choice = prompt_choice(options, "Your approach")

        if choice == len(options):
            merchant["negotiated"] = True
            clear()
            print(f"\n  {C.DIM}You step back. No deal was reached.{C.RESET}")
            pause()
            return

        if choice == len(options) - 1:
            _go_for_close(player, merchant, session, forced=False)
            return

        motivation_key, label, _ = APPEALS[choice - 1]
        correct = (motivation_key == MOTIVATIONS[merchant["motivation"]])

        if correct:
            _apply_correct(player, merchant, session)
        else:
            _apply_wrong(player, merchant, session)

        tier     = _speechcraft_tier(player)
        feedback = _SPEECH_FEEDBACK[tier][correct]
        result_tag = f"{C.BGREEN}✓{C.RESET}" if correct else f"{C.BRED}✗{C.RESET}"

        session["log"].append(
            f"{result_tag} {C.BOLD}Round {round_num}:{C.RESET} "
            f"{C.DIM}{feedback}{C.RESET}"
        )
