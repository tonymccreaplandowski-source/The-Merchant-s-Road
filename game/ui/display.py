"""
Terminal display layer — pure ANSI, no external dependencies.
All rendering lives here. Game logic knows nothing about colours or layout.
"""

import os
import re


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

def beep(tone: str = "attack"):
    """
    Play a short system beep to accompany combat events.
    Tones: attack | hit | cast | heal | victory | death | menu
    Silently does nothing on non-Windows or if winsound is unavailable.
    """
    try:
        import winsound
        _tones = {
            "attack":  (440, 80),
            "hit":     (220, 100),
            "cast":    (660, 120),
            "heal":    (550, 100),
            "victory": (880, 250),
            "death":   (110, 500),
            "menu":    (330, 60),
        }
        freq, dur = _tones.get(tone, (440, 80))
        winsound.Beep(freq, dur)
    except Exception:
        pass


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
        [C.BRED + C.BOLD + "    ⚔   COMBAT   ⚔" + C.RESET],
        border_color=C.BRED,
    )
    print()

    # Enemy
    e_bar = hp_bar(enemy.hp, enemy.max_hp)
    print(f"  {C.BRED}{C.BOLD}{enemy.name}{C.RESET}  {C.BBLACK}[{enemy.armor_type} armour]{C.RESET}")
    print(f"  HP  {e_bar}  {enemy.hp}/{enemy.max_hp}")
    print(f"  {C.DIM}Combat {enemy.combat_skill}   Defense {enemy.defense_skill}   Agility {enemy.agility}{C.RESET}")
    print()
    hr("─")

    # Player
    p_bar = hp_bar(player.hp, player.max_hp)
    m_bar = mana_bar(player.mana, player.max_mana)

    # Equipped weapon name for quick reference
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
            print(f"  {C.BYELLOW}» {line.strip()}{C.RESET}")
    print()


def show_character_sheet(player):
    """Full character sheet display with class, sprite, equipment, and mana."""
    from engine.player  import SKILLS, SKILL_DESCRIPTIONS
    from engine.classes import get_class, print_sprite
    clear()

    dominant_skill, cls = get_class(player.skills)

    title_screen(f"{player.name.upper()} — {cls['name'].upper()}")

    # Sprite + class info
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

    # Equipment slots
    section("EQUIPMENT")
    slots = [("weapon", "Weapon"), ("armor", "Armour"), ("ring", "Ring"), ("necklace", "Necklace")]
    for slot_key, slot_label in slots:
        item = player.equipped.get(slot_key)
        if item:
            color = RARITY_COLOR.get(item.rarity, C.WHITE)
            bonuses = ""
            if item.stat_bonuses:
                parts = [f"+{v} {k}" for k, v in item.stat_bonuses.items()]
                bonuses = f"  {C.DIM}({', '.join(parts)}){C.RESET}"
            curse_tag = f"  {C.BRED}[CURSED]{C.RESET}" if item.cursed else ""
            print(f"  {C.BCYAN}{slot_label:<10}{C.RESET}  {color}{item.name}{C.RESET}{bonuses}{curse_tag}")
        else:
            print(f"  {C.BCYAN}{slot_label:<10}{C.RESET}  {C.BBLACK}— empty —{C.RESET}")

    # Skills
    section("SKILLS")
    for name in SKILLS:
        val    = player.skill(name)
        bar    = skill_bar(val)
        marker = f" {C.BYELLOW}★{C.RESET}" if name == dominant_skill else ""
        print(f"  {C.BCYAN}{name:<16}{C.RESET}  {bar}  {val:>3}{marker}  {C.DIM}{SKILL_DESCRIPTIONS[name]}{C.RESET}")

    # Inventory
    section("INVENTORY")
    print(f"  {C.DIM}Carrying {len(player.inventory)}/12 items{C.RESET}")
    print()
    if not player.inventory:
        print(f"  {C.BBLACK}Empty.{C.RESET}")
    else:
        total_val = player.inventory_value()
        for item in player.inventory:
            print(item_line(item))
        print()
        print(f"  {C.DIM}Total base value: {total_val}gp{C.RESET}")
    print()
    pause()
