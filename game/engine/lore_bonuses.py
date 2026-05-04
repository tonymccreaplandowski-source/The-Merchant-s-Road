"""
Lore bonus lookup — contextual bonuses granted by reading lore books.

Usage:
    from engine.lore_bonuses import get_lore_bonus
    bonus = get_lore_bonus(player, "combat_damage_pct", context="goblin scout")
    bonus = get_lore_bonus(player, "hunt_kill_bonus")

Each book's lore_bonus dict can have:
    type              — string key used to look up the bonus
    value             — the bonus amount when condition is met (or always, if no requires_context)
    requires_context  — substring that must appear in context for value to apply
    fallback          — amount used when context does not match (default 0)
"""

from data.items import BOOK_ITEMS


def _read_books(player):
    return [b for b in BOOK_ITEMS if b.lore and b.lore in player.journal and b.lore_bonus]


def get_lore_bonus(player, bonus_type: str, context: str = "") -> float:
    """
    Returns total bonus value for the given type from all books the player has read.
    context: optional string matched against requires_context (substring, case-insensitive).
    """
    total = 0.0
    for book in _read_books(player):
        lb = book.lore_bonus
        if lb.get("type") != bonus_type:
            continue
        required = lb.get("requires_context", "")
        if required:
            if required.lower() in context.lower():
                total += lb.get("value", 0)
            else:
                total += lb.get("fallback", 0)
        else:
            total += lb.get("value", 0)
    return total
