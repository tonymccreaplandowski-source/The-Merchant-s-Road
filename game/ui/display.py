"""
Terminal display layer — pure ANSI, no external dependencies.
All rendering lives here. Game logic knows nothing about colours or layout.
"""

import os
import re
import sys
import time
import threading


# ── ANSI colour constants ─────────────────────────────────────────────────────

class C:
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"

    BLACK   = "\033[30m"
    RED     = "\033[31m"
    GREEN   = "\033[32m"
    YELLOW  = "\033[33m"
    BLUE    = "\033[34m"
    PURPLE  = "\033[35m"
    CYAN    = "\033[36m"
    WHITE   = "\033[37m"

    BRED    = "\033[91m"
    BGREEN  = "\033[92m"
    BYELLOW = "\033[93m"
    BBLUE   = "\033[94m"
    BPURPLE = "\033[95m"
    BCYAN   = "\033[96m"
    BWHITE  = "\033[97m"
    BBLACK  = "\033[90m"


RARITY_COLOR = {
    "common":   C.WHITE,
    "uncommon": C.BGREEN,
    "rare":     C.BBLUE,
    "epic":     C.BPURPLE,
}

BIOME_COLOR = {
    "desert":   C.BYELLOW,
    "forest":   C.BGREEN,
    "mountain": C.BBLUE,
    "cave":     C.BBLACK,
}


# ── Utilities ─────────────────────────────────────────────────────────────────

def _strip_ansi(text: str) -> str:
    """Return text with all ANSI escape sequences removed (for length calculation)."""
    return re.sub(r'\033\[[0-9;]*m', '', text)


def clear():
    os.system("cls" if os.name == "nt" else "clear")


def pause(msg: str = "Press Enter to continue..."):
    input(f"\n  {C.DIM}{msg}{C.RESET}")


def hr(char: str = "═", width: int = 62):
    print(C.BBLACK + char * width + C.RESET)


# ── Sound (Windows beeps, silently ignored on other platforms) ─────────────────

# Melodic sequences: list of (frequency_hz, duration_ms) pairs.
# 0 Hz = silent pause.
_MELODIES = {
    # ── Road ambient — A minor, slow and haunting ─────────────────────────────
    "ambient": [
        (110, 300), (0, 250),   # A2 — low root drone
        (165, 250), (0, 200),   # E3 — fifth, hollow
        (131, 200), (0, 300),   # C3 — minor third
        (147, 250), (0, 200),   # D3
        (220, 300), (0, 500),   # A3 — octave climb
        (196, 200), (0, 200),   # G3
        (175, 200), (0, 300),   # F3 — melancholy
        (165, 300), (0, 600),   # E3 — resolve
        (147, 200), (0, 200),   # D3 — descend
        (131, 250), (0, 300),   # C3
        (110, 400), (0, 2500),  # A2 — return to root, long silence
    ],
    # ── City ambient — C major, warm and wandering ────────────────────────────
    "ambient_city": [
        (523, 200), (0, 150),   # C4 — bright root
        (659, 200), (0, 150),   # E4 — major third
        (784, 180), (0, 200),   # G4 — fifth
        (659, 150), (0, 150),   # E4 — step back
        (587, 200), (0, 200),   # D4
        (523, 250), (0, 300),   # C4 — settle
        (440, 150), (0, 150),   # A3 — descend
        (494, 200), (0, 150),   # B3
        (523, 200), (0, 200),   # C4
        (392, 200), (0, 200),   # G3 — drop
        (440, 200), (0, 200),   # A3
        (523, 300), (0, 2000),  # C4 — resolve, pause
    ],
    # ── Dungeon ambient — E minor, oppressive and sparse ─────────────────────
    "ambient_dungeon": [
        (82,  500), (0, 500),   # E2 — deep drone
        (98,  300), (0, 400),   # G2 — minor third up
        (87,  250), (0, 500),   # F2 — dissonant half-step
        (82,  600), (0, 700),   # E2 — fall back
        (110, 300), (0, 300),   # A2 — step up
        (98,  200), (0, 300),   # G2
        (87,  250), (0, 400),   # F2 — unresolved
        (82,  700), (0, 3000),  # E2 — long, airless silence
    ],
    # ── Tension ambient — A minor, quick and unsettling ──────────────────────
    "ambient_tension": [
        (220, 100), (0, 80),    # A3 — quick pulse
        (196, 100), (0, 80),    # G3
        (175, 150), (0, 100),   # F3 — minor pull
        (165, 200), (0, 150),   # E3
        (220, 100), (0, 60),    # A3 — repeat, faster
        (233, 100), (0, 80),    # Bb3 — raised tension
        (220, 150), (0, 120),   # A3
        (175, 100), (0, 100),   # F3
        (165, 200), (0, 150),   # E3
        (147, 150), (0, 150),   # D3 — descend
        (165, 300), (0, 800),   # E3 — hold
        (0, 600),               # silence
    ],
    "city_arrive": [
        (523, 80), (659, 80), (784, 80), (1047, 180),
    ],
    "combat_start": [
        (330, 60), (294, 60), (262, 120),
    ],
    "victory": [
        (523, 80), (659, 80), (784, 80), (1047, 100),
        (0, 40),
        (784, 80), (1047, 200),
    ],
    "death": [
        (440, 120), (370, 120), (311, 120), (262, 300),
    ],
    "location_found": [
        (440, 60), (554, 60), (659, 100), (0, 40), (659, 80),
    ],
    "journal_entry": [
        (523, 60), (659, 120),
    ],
    "negotiate_win": [
        (523, 60), (659, 60), (784, 100), (1047, 180),
    ],
    "negotiate_lose": [
        (330, 80), (294, 80), (262, 160),
    ],
}


def play_melody(name: str) -> None:
    """Play a named melody in a background thread (non-blocking).
    Silently does nothing on non-Windows or if winsound is unavailable.
    """
    tones = _MELODIES.get(name)
    if not tones:
        return

    def _play():
        try:
            import winsound
            for freq, dur in tones:
                if freq == 0:
                    time.sleep(dur / 1000.0)
                else:
                    winsound.Beep(freq, dur)
        except Exception:
            pass

    t = threading.Thread(target=_play, daemon=True)
    t.start()


# ── Ambient music loop ───────────────────────────────────────────────────────

_ambient_stop_event = threading.Event()
_ambient_thread: threading.Thread = None
_current_context: str = "road"   # tracks which context is (or was last) playing

# Maps context names to melody keys in _MELODIES
_CONTEXT_MELODY = {
    "road":    "ambient",
    "city":    "ambient_city",
    "dungeon": "ambient_dungeon",
    "tension": "ambient_tension",
}


def start_ambient_loop(context: str = "road") -> None:
    """Start the ambient loop for the given context (road/city/dungeon/tension).
    If the same context is already playing, does nothing.
    If a different context is playing, stops it and starts the new one.
    Silently does nothing on non-Windows or if winsound is unavailable.
    """
    global _ambient_thread, _current_context

    # Switch context: stop the running loop so the new one can start cleanly
    if _ambient_thread is not None and _ambient_thread.is_alive():
        if _current_context == context:
            return   # already playing this context — no-op
        _ambient_stop_event.set()
        _ambient_thread.join(timeout=0.6)

    _current_context = context
    _ambient_stop_event.clear()

    melody_key = _CONTEXT_MELODY.get(context, "ambient")

    def _loop():
        try:
            import winsound
            tones = _MELODIES[melody_key]
            while not _ambient_stop_event.is_set():
                for freq, dur in tones:
                    if _ambient_stop_event.is_set():
                        return
                    if freq == 0:
                        # Break long pauses into short chunks so we can stop quickly
                        elapsed = 0
                        chunk = 50
                        while elapsed < dur and not _ambient_stop_event.is_set():
                            time.sleep(min(chunk, dur - elapsed) / 1000.0)
                            elapsed += chunk
                    else:
                        winsound.Beep(freq, dur)
        except Exception:
            pass

    _ambient_thread = threading.Thread(target=_loop, daemon=True)
    _ambient_thread.start()


def resume_ambient_loop() -> None:
    """Resume the ambient loop using whatever context was last active.
    Used after combat ends (flee or victory) to restore the pre-combat music.
    """
    start_ambient_loop(_current_context)


def stop_ambient_loop() -> None:
    """Stop the ambient loop as soon as the current note finishes."""
    _ambient_stop_event.set()


def beep(tone: str = "attack"):
    """
    Play a short system beep to accompany combat events.
    Tones: attack | hit | cast | heal | victory | death | menu
    Silently does nothing on non-Windows or if winsound is unavailable.
    """
    try:
        import winsound
        _tones = {
            "attack":  (440,  80),
            "hit":     (220, 100),
            "cast":    (660, 120),
            "heal":    (550, 100),
            "victory": (880, 250),
            "death":   (110, 500),
            "menu":    (330,  60),
        }
        freq, dur = _tones.get(tone, (440, 80))
        winsound.Beep(freq, dur)
    except Exception:
        pass


# ── Typewriter effect ─────────────────────────────────────────────────────────

def typewrite(text: str, delay: float = 0.025, indent: str = "  ") -> None:
    """Print text one character at a time for a typewriter effect.
    Strips ANSI codes for delay timing, but prints raw text so colours work.
    """
    print(indent, end="", flush=True)
    for ch in text:
        sys.stdout.write(ch)
        sys.stdout.flush()
        if ch not in (" ", "\t"):
            time.sleep(delay)
    print()  # newline at end


# ── Layout primitives ─────────────────────────────────────────────────────────

def title_screen(text: str):
    clear()
    width = 62
    print()
    print(C.BYELLOW + C.BOLD + "═" * width + C.RESET)
    pad = (width - len(text)) // 2
    print(C.BYELLOW + C.BOLD + " " * pad + text + C.RESET)
    print(C.BYELLOW + C.BOLD + "═" * width + C.RESET)
    print()


def section(text: str, color: str = C.BCYAN):
    print()
    print(color + C.BOLD + f"  ── {text} ──" + C.RESET)
    print()


def box(lines: list, width: int = 62, border_color: str = C.BWHITE):
    """Render a bordered box around a list of pre-coloured content lines."""
    print(border_color + "╔" + "═" * (width - 2) + "╗" + C.RESET)
    for line in lines:
        visible_len = len(_strip_ansi(line))
        pad = max(0, width - 2 - visible_len - 2)
        print(border_color + "║" + C.RESET + " " + line + " " * pad + " " + border_color + "║" + C.RESET)
    print(border_color + "╚" + "═" * (width - 2) + "╝" + C.RESET)


# ── Bars ──────────────────────────────────────────────────────────────────────

def hp_bar(current: int, maximum: int, length: int = 20) -> str:
    ratio  = current / maximum if maximum > 0 else 0
    filled = round(ratio * length)
    empty  = length - filled
    if ratio > 0.6:
        color = C.BGREEN
    elif ratio > 0.3:
        color = C.BYELLOW
    else:
        color = C.BRED
    return "[" + color + "█" * filled + C.BBLACK + "░" * empty + C.RESET + "]"


def mana_bar(current: int, maximum: int, length: int = 20) -> str:
    """Blue mana pool bar, mirrors hp_bar style."""
    if maximum <= 0:
        return "[" + C.BBLACK + "░" * length + C.RESET + "]"
    ratio  = current / maximum
    filled = round(ratio * length)
    empty  = length - filled
    return "[" + C.BBLUE + "█" * filled + C.BBLACK + "░" * empty + C.RESET + "]"


def skill_bar(value: int, length: int = 18) -> str:
    filled = round((value / 100) * length)
    empty  = length - filled
    if value >= 75:
        color = C.BGREEN
    elif value >= 40:
        color = C.BYELLOW
    else:
        color = C.BRED
    return color + "▓" * filled + C.BBLACK + "░" * empty + C.RESET


# ── Formatted strings ─────────────────────────────────────────────────────────

def rarity_tag(rarity: str) -> str:
    color = RARITY_COLOR.get(rarity, C.WHITE)
    labels = {"common": "Common", "uncommon": "Uncommon", "rare": "Rare", "epic": "EPIC"}
    return color + labels.get(rarity, rarity.upper()) + C.RESET


def item_line(item, show_value: bool = True) -> str:
    color    = RARITY_COLOR.get(item.rarity, C.WHITE)
    val_part = f"  {C.DIM}{item.base_value}gp{C.RESET}" if show_value else ""
    curse_tag = f"  {C.BRED}[CURSED]{C.RESET}" if getattr(item, "cursed", False) else ""
    return f"  {color}{item.name}{C.RESET}  [{rarity_tag(item.rarity)}]{val_part}{curse_tag}"


# ── Menu prompt ───────────────────────────────────────────────────────────────

def prompt_choice(options: list, prompt: str = "Your choice") -> int:
    """
    Print numbered options and return the player's 1-based selection.
    Loops until a valid integer is entered.
    """
    print()
    for i, opt in enumerate(options, 1):
        print(f"  {C.BYELLOW}[{i}]{C.RESET}  {opt}")
    print()
    while True:
        try:
            raw = input(f"  {C.BCYAN}{prompt}: {C.RESET}").strip()
            val = int(raw)
            if 1 <= val <= len(options):
                return val
            print(f"  {C.RED}Please enter a number between 1 and {len(options)}.{C.RESET}")
        except (ValueError, EOFError):
            print(f"  {C.RED}Invalid input — enter a number.{C.RESET}")


# ── Full screens ──────────────────────────────────────────────────────────────

def show_world_map(player):
    """Render the world map with the player's position highlighted."""
    from data.cities import CITIES, CITY_ORDER

    clear()
    title_screen("THE MERCHANT'S ROAD")

    print(f"  {C.DIM}West {'─' * 38} East{C.RESET}")
    print()

    # Map row
    map_row = "  "
    for i, key in enumerate(CITY_ORDER):
        city   = CITIES[key]
        bc     = BIOME_COLOR.get(city.biome, C.WHITE)
        is_here = (player.current_city == key and not player.on_road)
        if is_here:
            label = C.BYELLOW + C.BOLD + f"★ {city.name.upper()} ★" + C.RESET
        else:
            label = bc + f"[ {city.name} ]" + C.RESET
        map_row += label
        if i < len(CITY_ORDER) - 1:
            road_biome = city.road_biome_east or "forest"
            rc = BIOME_COLOR.get(road_biome, C.WHITE)
            map_row += f"  {rc}──────{C.RESET}  "

    print(map_row)
    print()

    # Biome labels
    labels_row = "  "
    offsets    = [0, 16, 14]
    for i, key in enumerate(CITY_ORDER):
        city = CITIES[key]
        bc   = BIOME_COLOR.get(city.biome, C.WHITE)
        labels_row += " " * offsets[i] + bc + city.biome.capitalize() + C.RESET
    print(labels_row)
    print()

    # Status bar
    hr()
    if player.on_road:
        dest  = player.road_destination
        steps = player.road_steps
        total = player.road_total
        dest_name = CITIES[dest].name if dest else "?"
        print(f"  {C.BYELLOW}Travelling → {dest_name}  ({steps}/{total} steps){C.RESET}", end="   ")
    else:
        city = CITIES.get(player.current_city or "ashenvale")
        print(f"  {C.BYELLOW}Location: {city.name}{C.RESET}", end="   ")
    print(
        f"{C.BGREEN}HP{C.RESET} {player.hp}/{player.max_hp}   "
        f"{C.BYELLOW}Gold{C.RESET} {player.gold}gp   "
        f"{C.BCYAN}Bag{C.RESET} {len(player.inventory)}/{12} items"
    )
    print()



def show_combat_screen(player, enemy, message: str = ""):
    """Render the combat encounter screen."""
    clear()
    print()
    box(
        [C.BRED + C.BOLD + "    \u2694   COMBAT   \u2694" + C.RESET],
        border_color=C.BRED,
    )
    print()

    # Enemy
    e_bar = hp_bar(enemy.hp, enemy.max_hp)
    print(f"  {C.BRED}{C.BOLD}{enemy.name}{C.RESET}  {C.BBLACK}[{enemy.armor_type} armour]{C.RESET}")
    print(f"  HP  {e_bar}  {enemy.hp}/{enemy.max_hp}")
    print(f"  {C.DIM}Martial {enemy.combat_skill}   Defense {enemy.defense_skill}   Stealth {enemy.agility}{C.RESET}")
    print()
    hr("─")

    # Player
    p_bar = hp_bar(player.hp, player.max_hp)
    m_bar = mana_bar(player.mana, player.max_mana)

    weapon = player.equipped.get("weapon")
    weapon_label = (
        f"  {C.DIM}[{weapon.name}]{C.RESET}" if weapon else
        f"  {C.BBLACK}[unarmed]{C.RESET}"
    )

    print(f"  {C.BGREEN}{C.BOLD}{player.name}{C.RESET}{weapon_label}")
    print(f"  HP  {p_bar}  {player.hp}/{player.max_hp}")
    if player.max_mana > 0:
        print(f"  MP  {m_bar}  {player.mana}/{player.max_mana}")
    print(f"  {C.DIM}Martial {player.skill('Martial')}   Stealth {player.skill('Stealth')}   Defense {player.defense}{C.RESET}")

    if message:
        print()
        hr("─")
        for line in message.split("\n"):
            print(f"  {C.BYELLOW}\u00bb {line.strip()}{C.RESET}")
    print()


def show_character_sheet(player):
    """Full character sheet display with class, sprite, equipment, skills, and inventory."""
    from engine.player  import SKILLS, SKILL_DESCRIPTIONS, MAX_INVENTORY
    from engine.classes import get_class, print_sprite
    clear()

    dominant_skill, cls = get_class(player.skills)
    title_screen(f"{player.name.upper()} \u2014 {cls['name'].upper()}")

    print(f"  {C.BYELLOW}\"{cls['tagline']}\"{C.RESET}")
    print()
    print_sprite(dominant_skill, indent=4)
    print()
    print(f"  {C.DIM}{cls['description']}{C.RESET}")
    print()
    hr()

    # Vitals
    print(f"  {C.BGREEN}HP{C.RESET}    {player.hp}/{player.max_hp}   {hp_bar(player.hp, player.max_hp)}")
    if player.max_mana > 0:
        print(f"  {C.BBLUE}Mana{C.RESET}  {player.mana}/{player.max_mana}   {mana_bar(player.mana, player.max_mana)}")
    print(f"  {C.BYELLOW}Gold{C.RESET}  {player.gold}gp")
    print(f"  {C.DIM}Days on the road: {player.days_elapsed}{C.RESET}")
    print()

    # Equipment
    section("EQUIPMENT")
    slots = [("weapon", "Weapon"), ("armor", "Armour"), ("ring", "Ring"), ("necklace", "Necklace")]
    for slot_key, slot_label in slots:
        item = player.equipped.get(slot_key)
        if item:
            color = RARITY_COLOR.get(item.rarity, C.WHITE)
            bonuses = ""
            if item.stat_bonuses:
                parts = [f"{'+' if v >= 0 else ''}{v} {k}" for k, v in item.stat_bonuses.items()]
                bonuses = f"  {C.DIM}({', '.join(parts)}){C.RESET}"
            curse_tag = f"  {C.BRED}[CURSED]{C.RESET}" if item.cursed else ""
            print(f"  {C.BCYAN}{slot_label:<10}{C.RESET}  {color}{item.name}{C.RESET}{bonuses}{curse_tag}")
        else:
            print(f"  {C.BCYAN}{slot_label:<10}{C.RESET}  {C.BBLACK}\u2014 empty \u2014{C.RESET}")
    print()
    hr()

    # Skills
    section("SKILLS")
    for skill in SKILLS:
        val  = player.skill(skill)
        bar  = skill_bar(val)
        desc = SKILL_DESCRIPTIONS.get(skill, "")
        print(f"  {C.BCYAN}{skill:<16}{C.RESET}  {bar}  {C.BYELLOW}{val:3}{C.RESET}  {C.DIM}{desc}{C.RESET}")
    print()
    hr()

    # Learned spells
    if getattr(player, "learned_spells", None):
        section("SPELLS")
        from data.spells import SPELL_REGISTRY
        for spell_name in player.learned_spells:
            spell = SPELL_REGISTRY.get(spell_name)
            if spell:
                if spell.mana_cost > 0:
                    cost_str = f"  {C.DIM}({spell.mana_cost} MP){C.RESET}"
                else:
                    cost_str = f"  {C.BRED}({spell.self_cost} HP){C.RESET}"
                print(f"  {C.BPURPLE}{spell.name}{C.RESET}{cost_str}  {C.DIM}{spell.description}{C.RESET}")
        print()
        hr()

    # Inventory
    section("INVENTORY")
    if not player.inventory:
        print(f"  {C.BBLACK}(empty){C.RESET}")
    else:
        for i, item in enumerate(player.inventory, 1):
            print(f"  {C.DIM}{i:2}.{C.RESET}  {item_line(item)}")
    print()
    print(f"  {C.DIM}Carrying {len(player.inventory)}/{MAX_INVENTORY} items{C.RESET}")
    print()

    pause()


def show_journal(player):
    """Display all lore entries in the player's journal."""
    clear()
    title_screen("JOURNAL")
    if not player.journal:
        print(f"  {C.DIM}Your journal is empty. Explore caves and castles to fill it.{C.RESET}")
        print()
    else:
        for i, entry in enumerate(player.journal, 1):
            print(f"  {C.BYELLOW}Entry {i}{C.RESET}")
            print()
            typewrite(entry)
            print()
            hr("─")
            print()
    pause()
