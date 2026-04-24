"""
Item usage logic — potion and consumable effects applied to the player.
"""

import random

from engine.player import Player, SKILLS

USABLE_EFFECTS_OUTSIDE_COMBAT = {
    "heal_15", "heal_20", "heal_30", "heal_35", "heal_40",
    "mana_25", "full_restore", "map_bonus", "mushroom_wild",
    "berries_unknown", "torch",
}


def use_potion(player: Player, potion, state: dict) -> str:
    """Apply a potion/consumable effect in combat. Returns a flavour message string."""
    effect = potion.effect or ""
    if effect == "heal_30":
        before = player.hp; player.heal(30)
        return f"You drink the {potion.name}. +{player.hp - before} HP."
    if effect == "heal_20":
        before = player.hp; player.heal(20)
        return f"You use the {potion.name}. +{player.hp - before} HP."
    if effect == "heal_15":
        before = player.hp; player.heal(15)
        return f"You eat the {potion.name}. +{player.hp - before} HP."
    if effect == "mana_25":
        before = player.mana; player.restore_mana(25)
        return f"You drink the {potion.name}. +{player.mana - before} Mana."
    if effect == "str_boost":
        state["player_str_boost"] = True
        return f"You drink the {potion.name}. Combat power surges!"
    if effect == "agi_boost":
        state["player_agi_boost"] = True
        return f"You drink the {potion.name}. You feel fleet-footed."
    if effect == "full_restore":
        player.heal(player.max_hp); player.restore_mana()
        return f"You drink the {potion.name}. HP and Mana fully restored!"
    if effect == "map_bonus":
        player.map_bonus = True
        return f"You study the {potion.name}. Nearby locations will be easier to find."
    if effect == "torch":
        return f"You light the {potion.name}. The dark pulls back a little."
    if effect == "heal_35":
        before = player.hp; player.heal(35)
        return f"You eat the {potion.name}. +{player.hp - before} HP."
    if effect == "heal_40":
        before = player.hp; player.heal(40)
        return f"You eat the {potion.name}. +{player.hp - before} HP."
    if effect == "mushroom_wild":
        before_hp = player.hp; player.heal(15); player.restore_mana(10)
        return f"You eat the {potion.name}. +{player.hp - before_hp} HP, +10 Mana."
    if effect == "berries_unknown":
        if random.random() < 0.05:
            sick_skill   = random.choice(SKILLS)
            sick_penalty = random.randint(5, 15)
            sick_days    = random.randint(1, 5)
            player.sick_skill   = sick_skill
            player.sick_penalty = sick_penalty
            player.sick_days    = sick_days
            return (
                f"You eat the {potion.name}. Something was wrong with them. "
                f"Your {sick_skill} feels dulled. "
                f"(-{sick_penalty} {sick_skill} for {sick_days} day{'s' if sick_days != 1 else ''})"
            )
        before = player.hp; player.heal(10)
        return f"You eat the {potion.name}. Tasted fine. +{player.hp - before} HP."
    return f"You use the {potion.name}."


def use_item_outside_combat(player: Player, item) -> str:
    """Apply a consumable effect outside of combat. Returns a message string."""
    effect = item.effect or ""
    if effect == "heal_15":
        before = player.hp; player.heal(15)
        return f"You eat the {item.name}. +{player.hp - before} HP."
    if effect == "heal_20":
        before = player.hp; player.heal(20)
        return f"You use the {item.name}. +{player.hp - before} HP."
    if effect == "heal_30":
        before = player.hp; player.heal(30)
        return f"You drink the {item.name}. +{player.hp - before} HP."
    if effect == "heal_35":
        before = player.hp; player.heal(35)
        return f"You eat the {item.name}. +{player.hp - before} HP."
    if effect == "heal_40":
        before = player.hp; player.heal(40)
        return f"You eat the {item.name}. +{player.hp - before} HP."
    if effect == "mana_25":
        before = player.mana; player.restore_mana(25)
        return f"You drink the {item.name}. +{player.mana - before} Mana."
    if effect == "full_restore":
        player.heal(player.max_hp); player.restore_mana()
        return f"You drink the {item.name}. HP and Mana fully restored!"
    if effect == "map_bonus":
        player.map_bonus = True
        return f"You study the {item.name}. Nearby locations will be easier to find."
    if effect == "torch":
        return f"You light the {item.name}. The dark pulls back a little."
    if effect == "mushroom_wild":
        before_hp = player.hp; player.heal(15); player.restore_mana(10)
        return f"You eat the {item.name}. +{player.hp - before_hp} HP, +10 Mana."
    if effect == "berries_unknown":
        if random.random() < 0.05:
            sick_skill   = random.choice(SKILLS)
            sick_penalty = random.randint(5, 15)
            sick_days    = random.randint(1, 5)
            player.sick_skill   = sick_skill
            player.sick_penalty = sick_penalty
            player.sick_days    = sick_days
            return (
                f"You eat the {item.name}. Something was wrong with them. "
                f"Your {sick_skill} feels dulled. "
                f"(-{sick_penalty} {sick_skill} for {sick_days} day{'s' if sick_days != 1 else ''})"
            )
        before = player.hp; player.heal(10)
        return f"You eat the {item.name}. Tasted fine. +{player.hp - before} HP."
    return f"You use the {item.name}."
