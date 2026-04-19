"""
Character class determination and ASCII sprite system.

Class is assigned at character creation based on the player's highest skill.
Each class has a name, flavour description, and an 8-bit style ASCII sprite.
"""

from typing import Dict, Tuple

# ── Class definitions ─────────────────────────────────────────────────────────

CLASSES: Dict[str, Dict] = {
    "Merchantilism": {
        "name":        "The Broker",
        "tagline":     "Where blades fail, coin prevails.",
        "description": (
            "A sharp mind and sharper tongue. The Broker moves through markets "
            "the way others move through crowds — with purpose, reading every "
            "face for weakness and every price for opportunity."
        ),
    },
    "Speechcraft": {
        "name":        "The Envoy",
        "tagline":     "Every word a move. Every silence a gambit.",
        "description": (
            "Doors open for the Envoy that remain shut for everyone else. "
            "They carry no great weapon — only a reputation, carefully built "
            "and ruthlessly maintained."
        ),
    },
    "Martial": {
        "name":        "The Sellsword",
        "tagline":     "Hired for steel. Stays for coin.",
        "description": (
            "A blade-for-hire who learned long ago that the road doesn't "
            "forgive hesitation. The Sellsword hits first, hits hard, "
            "and asks questions when the dust settles."
        ),
    },
    "Magic": {
        "name":        "The Hedge Mage",
        "tagline":     "Power without a school. Dangerous without a leash.",
        "description": (
            "Self-taught and unpredictable. The Hedge Mage learned their craft "
            "from crumbling texts and hard-won trial and error. "
            "Academies distrust them. Enemies fear them."
        ),
    },
    "Stealth": {
        "name":        "The Cutpurse",
        "tagline":     "You never hear them. You only notice what's missing.",
        "description": (
            "The Cutpurse survives by being overlooked. Light on their feet, "
            "lighter on their conscience. What they lack in brute strength "
            "they compensate for in patience and positioning."
        ),
    },
    "Survival": {
        "name":        "The Wayfarer",
        "tagline":     "The road is harsh. They've walked it longer than most.",
        "description": (
            "Hardened by seasons alone in the wilderness. The Wayfarer knows "
            "which berries kill and which paths avoid patrols. "
            "They arrive where others don't."
        ),
    },
    "Dungeoneering": {
        "name":        "The Delver",
        "tagline":     "What lives in the dark has already met them.",
        "description": (
            "Caves, crypts, forgotten ruins — the Delver calls them home. "
            "They carry a torch and a calm head, and they know the difference "
            "between a trapped floor and a dusty one."
        ),
    },
}


# ── ASCII Sprites (8-bit style, coloured) ─────────────────────────────────────
# Each sprite is a list of (text, color_code) tuples, one per row.
# Rendered left-to-right within each row.
# Uses ANSI color codes directly for portability.

R  = "\033[0m"           # reset
W  = "\033[97m"          # bright white  (highlights)
GY = "\033[90m"          # dark grey     (shadows / mail)
SL = "\033[37m"          # silver/grey   (armour)
RD = "\033[91m"          # red           (accents)
GD = "\033[93m"          # gold/yellow   (coin, hair)
GN = "\033[92m"          # green         (cloak, nature)
BL = "\033[94m"          # blue          (magic)
SK = "\033[33m"          # skin tone
BK = "\033[30m"          # black
PR = "\033[95m"          # purple        (magic)
CY = "\033[96m"          # cyan


def _row(*parts) -> str:
    """Build one sprite row from (text, color) pairs, auto-reset at end."""
    out = ""
    for color, text in parts:
        out += color + text
    return out + R


# ── THE SELLSWORD (Martial) ───────────────────────────────────────────────────
SELLSWORD_SPRITE = [
    _row((GY, "   ▄███▄   ")),
    _row((GY, "  ██"), (SK, "███"), (GY, "██  ")),
    _row((GY, "  ██"), (SK, "◉ ◉"), (GY, "██  ")),
    _row((GY, "  ██"), (SK, " ▄ "), (GY, "██  ")),
    _row((GY, " ▄█████████▄")),
    _row((GY, " ███"), (RD, "▀▄▀"), (GY, "████")),
    _row((GY, " ██"), (W,  "█████"), (GY, "██ ")),
    _row((GY, "  ██"), (GD, "═══"), (GY, "██  ")),
    _row((GY, "  ██ "), (W, "║"), (GY, " ██  ")),
    _row((GY, "  ▀█▀ "), (W, "║"), (GY, " ▀█▀ ")),
]

# ── THE BROKER (Merchantilism) ────────────────────────────────────────────────
BROKER_SPRITE = [
    _row((GD, "   ▄███▄   ")),
    _row((GD, "  █"), (SK, "█████"), (GD, "█  ")),
    _row((GD, "  █"), (SK, "◉   ◉"), (GD, "█  ")),
    _row((GD, "  █"), (SK, "  ▄  "), (GD, "█  ")),
    _row((GD, " ▄█████████▄")),
    _row((GD, " █"), (W,  "█████████"), (GD, "█")),
    _row((GD, " █"), (GD, "████"), (W, "◈"), (GD, "████"), (GD, "█")),
    _row((GD, "  █"), (GD, "███████"), (GD, "█  ")),
    _row((SK, "  █▌"), (GD, "   "), (SK, "▐█  ")),
    _row((SK, "  ▀▀ "), (GD, "   "), (SK, " ▀▀ ")),
]

# ── THE ENVOY (Speechcraft) ───────────────────────────────────────────────────
ENVOY_SPRITE = [
    _row((BL, "   ▄███▄   ")),
    _row((BL, "  █"), (SK, "█████"), (BL, "█  ")),
    _row((BL, "  █"), (SK, "◉   ◉"), (BL, "█  ")),
    _row((BL, "  █"), (SK, "  ‿  "), (BL, "█  ")),
    _row((BL, " ▄█████████▄")),
    _row((BL, " █"), (W,  "█████████"), (BL, "█")),
    _row((BL, " █"), (W,  "█"), (GD, "▀▄▀"), (W, "█████"), (BL, "█")),
    _row((BL, "  █"), (W,  "███████"), (BL, "█  ")),
    _row((SK, "  █▌"), (BL, "   "), (SK, "▐█  ")),
    _row((SK, "  ▀▀ "), (BL, "   "), (SK, " ▀▀ ")),
]

# ── THE HEDGE MAGE (Magic) ────────────────────────────────────────────────────
MAGE_SPRITE = [
    _row((PR, "  ✦▄███▄✦  ")),
    _row((PR, "  █"), (SK, "█████"), (PR, "█  ")),
    _row((PR, "  █"), (SK, "★   ★"), (PR, "█  ")),
    _row((PR, "  █"), (SK, "  ▄  "), (PR, "█  ")),
    _row((PR, " ▄█████████▄")),
    _row((PR, " █"), (BL, "█████████"), (PR, "█")),
    _row((PR, " █"), (BL, "██"), (W, "✦"), (BL, "██████"), (PR, "█")),
    _row((PR, "  █"), (BL, "███████"), (PR, "█  ")),
    _row((PR, "  █▌"), (BL, "   "), (PR, "▐█  ")),
    _row((PR, "  ▀▀ "), (BL, "✦ ✦"), (PR, " ▀▀ ")),
]

# ── THE CUTPURSE (Stealth) ────────────────────────────────────────────────────
CUTPURSE_SPRITE = [
    _row((GY, "   ▄███▄   ")),
    _row((GK := BK, "  █"), (SK, "█████"), (BK, "█  ")),
    _row((BK, "  █"), (SK, "◉   ◉"), (BK, "█  ")),
    _row((BK, "  █"), (SK, "  ─  "), (BK, "█  ")),
    _row((BK, " ▄█████████▄")),
    _row((BK, " █"), (GY, "█████████"), (BK, "█")),
    _row((BK, " █"), (GY, "███"), (RD, "✦"), (GY, "█████"), (BK, "█")),
    _row((BK, "  █"), (GY, "███████"), (BK, "█  ")),
    _row((BK, "  █▌"), (GY, "   "), (BK, "▐█  ")),
    _row((BK, "  ▀▀ "), (GY, "   "), (BK, " ▀▀ ")),
]

# ── THE WAYFARER (Survival) ───────────────────────────────────────────────────
WAYFARER_SPRITE = [
    _row((GN, "   ▄███▄   ")),
    _row((GN, "  █"), (SK, "█████"), (GN, "█  ")),
    _row((GN, "  █"), (SK, "◉   ◉"), (GN, "█  ")),
    _row((GN, "  █"), (SK, "  ▄  "), (GN, "█  ")),
    _row((GN, " ▄█████████▄")),
    _row((GN, " █"), (W,  "█████████"), (GN, "█")),
    _row((GN, " █"), (GD, "█"), (W, "███████"), (GN, "█")),
    _row((GN, "  █"), (W,  "███████"), (GN, "█  ")),
    _row((GN, "  █▌"), (W,  " ╿ "), (GN, "▐█  ")),
    _row((GN, "  ▀▀ "), (W,  "   "), (GN, " ▀▀ ")),
]

# ── THE DELVER (Dungeoneering) ────────────────────────────────────────────────
DELVER_SPRITE = [
    _row((GY, "  ▄▄███▄▄  ")),
    _row((GY, "  █"), (SK, "█████"), (GY, "█  ")),
    _row((GY, "  █"), (SK, "◉   ◉"), (GY, "█  ")),
    _row((GY, "  █"), (SK, "  ▄  "), (GY, "█  ")),
    _row((GY, " ▄█████████▄")),
    _row((GY, " █"), (SL, "█████████"), (GY, "█")),
    _row((GY, " █"), (SL, "██"), (GD, "☀"), (SL, "██████"), (GY, "█")),
    _row((GY, "  █"), (SL, "███████"), (GY, "█  ")),
    _row((GY, "  █▌"), (SL, "   "), (GY, "▐█  ")),
    _row((GY, "  ▀▀ "), (GD, "╙─╜"), (GY, " ▀▀ ")),
]


SPRITE_MAP = {
    "Merchantilism": BROKER_SPRITE,
    "Speechcraft":   ENVOY_SPRITE,
    "Martial":       SELLSWORD_SPRITE,
    "Magic":         MAGE_SPRITE,
    "Stealth":       CUTPURSE_SPRITE,
    "Survival":      WAYFARER_SPRITE,
    "Dungeoneering": DELVER_SPRITE,
}


# ── Public API ────────────────────────────────────────────────────────────────

def get_class(skills: Dict[str, int]) -> Tuple[str, Dict]:
    """
    Determine a player's class from their skill allocations.
    Returns (dominant_skill_key, class_dict).
    Ties broken by skill order in CLASSES.
    """
    dominant = max(skills, key=lambda k: skills.get(k, 0))
    return dominant, CLASSES[dominant]


def get_sprite(dominant_skill: str):
    """Return the sprite row list for the given dominant skill."""
    return SPRITE_MAP.get(dominant_skill, SELLSWORD_SPRITE)


def print_sprite(dominant_skill: str, indent: int = 4):
    """Print the sprite to stdout with optional indent."""
    sprite = get_sprite(dominant_skill)
    pad = " " * indent
    for row in sprite:
        print(pad + row)
