"""
Combat engine — fully overhauled.

Changes from v1:
  - Initiative dice roll decides who attacks first each fight
  - Weapon-based move sets (from player.combat_moves())
  - Special move effects: defensive / evade / stealth_boost / martial_boost /
                          miss_chance / stagger / slow / mana_discount
  - Critical hits: 5% base + (Martial / 500), 1.5x damage multiplier
  - Spell casting via mana pool
  - Player has a real defense stat (from armour + martial)
  - Combat state dict tracks temporary status effects
"""

import random
from typing import Tuple, Dict, Any

from engine.player import Player
from data.enemies  import Enemy
from data.weapons  import MOVES
from data.spells   import SPELLS

FLEE_BASE_CHANCE = 0.35
CRIT_BASE        = 0.05   # 5% base crit chance


# ── Critical hit ─────────────────────────────────────────────────────────────

def crit_chance(player: Player) -> float:
    return min(0.30, CRIT_BASE + player.skill("Martial") / 500.0)


def roll_crit(player: Player) -> bool:
    return random.random() < crit_chance(player)


# ── Initiative ───────────────────────────────────────────────────────────────

def roll_initiative(player: Player, enemy: Enemy) -> bool:
    """
    Returns True if player goes first.
    Player rolls d20 + (Survival // 5).
    Enemy rolls d20 + (agility // 10).
    """
    p_roll = random.randint(1, 20) + player.skill("Survival") // 5
    e_roll = random.randint(1, 20) + enemy.agility // 10
    return p_roll >= e_roll   # ties go to player


# ── Effectiveness label ───────────────────────────────────────────────────────

def effectiveness_label(value: float) -> str:
    if value >= 1.40:  return "very effective"
    if value >= 1.00:  return "effective"
    if value >= 0.80:  return "not very effective"
    return "barely effective"


# ── Fresh combat state ────────────────────────────────────────────────────────

def fresh_state() -> Dict[str, Any]:
    return {
        "player_defensive":   False,   # Parry — reduces next hit by 40%
        "player_evading":     False,   # Feint/Pot Shot — 50% miss chance on enemy counter
        "enemy_staggered":    0,       # turns remaining enemy combat_skill -10
        "enemy_slowed":       0,       # turns remaining enemy agility -15
        "player_str_boost":   False,   # Strength Draft active
        "player_agi_boost":   False,   # Swiftness Tonic active
    }


# ── Damage calculation ────────────────────────────────────────────────────────

def calculate_damage(
    attacker_combat: int,
    defender_defense: int,
    move_name: str,
    armor_type: str,
    player: Player = None,
    state: Dict = None,
) -> Tuple[int, str, bool, str]:
    """
    Returns (damage, effectiveness_label, is_crit, special_triggered).
    special_triggered is a string describing any special effect applied, or "".
    """
    move          = MOVES[move_name]
    effectiveness = move["effectiveness"].get(armor_type, 1.0)
    label         = effectiveness_label(effectiveness)
    special       = move.get("special")
    special_val   = move.get("special_value", 0.0)

    # Miss chance (Overhead, Smash)
    if special == "miss_chance" and random.random() < special_val:
        return 0, "missed", False, "miss"

    # Skill modifier
    skill_mod = max(0.5, min(1.5, 1.0 + (attacker_combat - defender_defense) / 200.0))

    # Str boost
    if state and state.get("player_str_boost"):
        skill_mod = min(1.5, skill_mod + 0.15)

    # Special damage boosts
    special_tag = ""
    bonus_mult  = 1.0
    if player and special == "stealth_boost":
        bonus_mult = 1.0 + player.skill("Stealth") / 100.0
        special_tag = "stealth boost"
    elif player and special == "martial_boost":
        bonus_mult = 1.0 + player.skill("Martial") / 100.0
        special_tag = "martial boost"

    variance = random.uniform(0.85, 1.15)
    raw      = move["power"] * effectiveness * skill_mod * bonus_mult * variance

    # Critical hit
    is_crit = False
    if player and roll_crit(player):
        raw    *= 1.5
        is_crit = True

    damage = max(1, round(raw))
    return damage, label, is_crit, special_tag


def apply_move_special(move_name: str, state: Dict, player: Player, enemy: Enemy) -> str:
    """
    Apply non-damage special effects of a move to the combat state.
    Returns a description string or "".
    """
    special = MOVES[move_name].get("special")
    if special == "defensive":
        state["player_defensive"] = True
        return "You brace for their counter."
    if special == "evade":
        state["player_evading"] = True
        return "You keep them guessing."
    if special == "stagger":
        state["enemy_staggered"] = 2
        return f"{enemy.name} loses their footing."
    if special == "mana_discount":
        player.mana_discount = 5
        return "You channel energy into your next spell."
    return ""


# ── Enemy attack ─────────────────────────────────────────────────────────────

def enemy_attack(enemy: Enemy, player: Player, state: Dict) -> Tuple[int, str]:
    """
    Enemy picks a random move (from generic MOVES pool) and attacks.
    Applies player defensive / evading status.
    Returns (damage, move_name).
    """
    move_name = random.choice(list(MOVES.keys()))
    e_combat  = enemy.combat_skill
    if state.get("enemy_staggered", 0) > 0:
        e_combat  = max(5, e_combat - 10)
        state["enemy_staggered"] -= 1

    # Player evading — 50% miss
    if state.get("player_evading"):
        state["player_evading"] = False
        if random.random() < 0.50:
            return 0, move_name + " (dodged)"

    damage, _, _, _ = calculate_damage(
        attacker_combat=e_combat,
        defender_defense=player.defense,
        move_name=move_name,
        armor_type="none",
    )

    # Player defensive — absorb 40%
    if state.get("player_defensive"):
        state["player_defensive"] = False
        damage = max(1, round(damage * 0.60))

    return damage, move_name


# ── Spell cast ────────────────────────────────────────────────────────────────

def cast_spell(
    spell_name: str,
    player: Player,
    enemy: Enemy,
    state: Dict,
) -> Tuple[int, str, str]:
    """
    Cast a spell. Returns (damage_or_heal, result_description, special_tag).
    Does NOT deduct mana — caller handles spend_mana() so UI can abort.
    """
    spell       = SPELLS[spell_name]
    special     = spell.get("special")
    special_tag = ""

    if spell.get("damage_type") == "heal":
        amount = spell.get("heal_amount", 20)
        player.heal(amount)
        return amount, "heal", ""

    effectiveness = spell["effectiveness"].get(enemy.armor_type, 1.0)
    label         = effectiveness_label(effectiveness)
    skill_mod     = max(0.5, min(1.5, 1.0 + (player.skill("Magic") - enemy.defense_skill) / 200.0))
    variance      = random.uniform(0.85, 1.15)

    is_crit = roll_crit(player)
    raw     = spell["power"] * effectiveness * skill_mod * variance
    if is_crit:
        raw *= 1.5

    damage = max(1, round(raw))

    if special == "slow" and state is not None:
        state["enemy_slowed"] = 2
        special_tag = "target slowed"
    if special == "evade" and state is not None:
        state["player_evading"] = True
        special_tag = "you phase out"

    return damage, label, special_tag


# ── Flee ─────────────────────────────────────────────────────────────────────

def attempt_flee(player: Player, enemy: Enemy) -> bool:
    stealth_bonus   = player.skill("Stealth") / 200.0
    agility_penalty = enemy.agility           / 200.0
    chance = max(0.10, min(0.85, FLEE_BASE_CHANCE + stealth_bonus - agility_penalty))
    return random.random() < chance
