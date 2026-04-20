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

    # Move-specific miss chance (Overhead, Smash)
    if special == "miss_chance" and random.random() < special_val:
        return 0, "missed", False, "miss"

    # ── D20 general hit roll ──────────────────────────────────────────────────
    # When defense is high relative to attacker, attacks can miss entirely.
    # Roll d20 + attacker_combat // 5.  Must beat defender_defense // 4 + 2.
    hit_roll    = random.randint(1, 20) + attacker_combat // 5
    hit_needed  = defender_defense // 4 + 2
    if hit_roll < hit_needed:
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
        bonus_mult = 1.0 + player.skill("Martial") / 200.0
        special_tag = "martial boost"
    elif player and special == "survival_boost":
        bonus_mult = 1.0 + player.skill("Survival") / 200.0
        special_tag = "survival boost"

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
    if special in ("evade", "survival_boost"):
        state["player_evading"] = True
        return "You keep moving — hard to pin down."
    if special == "stagger":
        state["enemy_staggered"] = 2
        return f"{enemy.name} loses their footing."
    if special == "mana_discount":
        player.mana_discount = 5
        return "You channel energy into your next spell."
    return ""


# ── Enemy spell cast ─────────────────────────────────────────────────────────

def cast_enemy_spell(spell_name: str, enemy: Enemy, player: Player) -> Tuple[int, str]:
    """
    Enemy casts a spell. Returns (damage, label).
    Enemies cast freely — no mana cost.
    """
    spell = SPELLS.get(spell_name)
    if not spell:
        return 0, "fizzled"

    if spell.get("damage_type") == "heal":
        return random.randint(5, 12), "shadow surge"

    armor      = player.equipped.get("armor")
    armor_type = armor.armor_type if armor else "none"
    eff        = spell["effectiveness"].get(armor_type, 1.0)
    skill_mod  = max(0.5, min(1.4, 1.0 + (enemy.combat_skill - player.defense) / 200.0))
    raw        = spell["power"] * eff * skill_mod * random.uniform(0.80, 1.20)
    return max(1, round(raw)), effectiveness_label(eff)


# ── Enemy attack ─────────────────────────────────────────────────────────────

def enemy_attack(enemy: Enemy, player: Player, state: Dict) -> Tuple[int, str, bool]:
    """
    Enemy attacks or casts depending on enemy_type.
    Returns (damage, description, is_spell).
    half_mage: 35% cast chance. mage: 65% cast chance.
    """
    # ── Decide whether to cast ────────────────────────────────────────────
    is_spell = False
    if enemy.enemy_spells:
        threshold = {"mage": 0.65, "half_mage": 0.35}.get(enemy.enemy_type, 0.0)
        if random.random() < threshold:
            is_spell = True

    if is_spell:
        spell_name = random.choice(enemy.enemy_spells)
        dmg, label = cast_enemy_spell(spell_name, enemy, player)

        if state.get("player_evading"):
            state["player_evading"] = False
            if random.random() < 0.50:
                return 0, f"{spell_name} (evaded)", True

        if state.get("player_defensive"):
            state["player_defensive"] = False
            dmg = max(1, round(dmg * 0.80))   # spells pierce armour better

        return dmg, f"casts {spell_name}!", True

    # ── Physical attack ───────────────────────────────────────────────────
    move_name = random.choice(list(MOVES.keys()))
    e_combat  = enemy.combat_skill
    if state.get("enemy_staggered", 0) > 0:
        e_combat = max(5, e_combat - 10)
        state["enemy_staggered"] -= 1

    if state.get("player_evading"):
        state["player_evading"] = False
        if random.random() < 0.50:
            return 0, move_name + " (dodged)", False

    damage, _, _, _ = calculate_damage(
        attacker_combat  = e_combat,
        defender_defense = player.defense,
        move_name        = move_name,
        armor_type       = "none",
    )

    if state.get("player_defensive"):
        state["player_defensive"] = False
        damage = max(1, round(damage * 0.60))

    retu