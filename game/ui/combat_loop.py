"""
Combat and loot screens — the full in-combat turn loop and post-combat loot.
"""

import time

from engine.player import Player, MAX_INVENTORY
from engine.combat import (
    fresh_state, roll_initiative, calculate_damage,
    apply_move_special, enemy_attack, cast_spell, attempt_flee,
)
from engine.loot   import generate_loot
from engine.items_use import use_potion
from data.weapons  import MOVES
from data.spells   import get_available_spells
from ui.display    import (
    C, RARITY_COLOR,
    clear, pause, title_screen, prompt_choice, item_line, rarity_tag,
    show_combat_screen, beep, play_melody,
    stop_ambient_loop, resume_ambient_loop,
    reset_combat_message, play_battle_music, stop_battle_music,
)


def run_combat(player: Player, enemy, force_first: bool = False) -> bool:
    """
    Full combat loop.
    Returns True if player wins, False if player fled or was killed.
    force_first: skip initiative roll and guarantee player acts first (stealth ambush).
    """
    state        = fresh_state()
    stop_ambient_loop()
    reset_combat_message()
    play_battle_music()
    player_first = True if force_first else roll_initiative(player, enemy)
    if force_first:
        state["enemy_staggered"] = 2

    if player_first:
        message = f"{enemy.description}\n  You win the initiative — you strike first!"
    else:
        e_dmg, e_move, e_is_spell = enemy_attack(enemy, player, state)
        player.take_damage(e_dmg)
        e_verb = "casts" if e_is_spell else "attacks with"
        if e_dmg == 0:
            message = f"{enemy.description}\n  {enemy.name} moves first — {e_move} (missed)"
        else:
            message = (
                f"{enemy.description}\n"
                f"  {enemy.name} moves first! {e_verb} {e_move} — "
                f"{C.BRED}{e_dmg}{C.RESET} damage."
            )
        beep("hit")
        if not player.is_alive():
            show_combat_screen(player, enemy, "You are struck down before you can act...")
            time.sleep(2)
            return False

    while player.is_alive() and enemy.is_alive():
        show_combat_screen(player, enemy, message)
        if message:
            pause("  Press Enter...")

        top = prompt_choice([
            f"{C.BOLD}Attack{C.RESET}   — weapon moves",
            f"{C.BBLUE}Cast{C.RESET}     — cast a spell",
            f"{C.BGREEN}Items{C.RESET}    — use a potion",
            f"{C.BBLACK}Flee{C.RESET}     — attempt to escape",
        ], "Choose action")

        action_taken = False

        # ── ATTACK ───────────────────────────────────────────────────────────
        if top == 1:
            moves        = player.combat_moves()
            move_options = []
            for mn in moves:
                move = MOVES[mn]
                move_options.append(
                    f"{C.BOLD}{mn:<14}{C.RESET}  {C.DIM}{move['description']}{C.RESET}"
                )
            move_options.append(f"{C.BBLACK}← Back{C.RESET}")

            show_combat_screen(player, enemy, message)
            mc = prompt_choice(move_options, "Choose move")
            if mc == len(move_options):
                message = "You hold your ground."
                continue

            move_name = moves[mc - 1]
            dmg, label, is_crit, special_tag = calculate_damage(
                attacker_combat=player.skill("Martial"),
                defender_defense=enemy.defense_skill,
                move_name=move_name,
                armor_type=enemy.armor_type,
                player=player,
                state=state,
            )
            special_msg = apply_move_special(move_name, state, player, enemy)
            enemy.take_damage(dmg)

            if dmg == 0:
                message = f"You use {C.BOLD}{move_name}{C.RESET}! Missed entirely!"
            else:
                crit_str = f"  {C.BYELLOW}✦ CRITICAL!{C.RESET}" if is_crit else ""
                message = (
                    f"You use {C.BOLD}{move_name}{C.RESET}! It's {label}! "
                    f"({C.BGREEN}{dmg}{C.RESET} dmg){crit_str}"
                )
            if special_tag:
                message += f"\n  [{special_tag}]"
            if special_msg:
                message += f"\n  {special_msg}"
            beep("attack")
            action_taken = True

        # ── CAST ─────────────────────────────────────────────────────────────
        elif top == 2:
            available = get_available_spells(player.skill("Magic"), player.learned_spells)
            if not available:
                if player.learned_spells:
                    message = "Your Magic skill is too low to cast any of your known spells."
                else:
                    message = "You have not learned any spells. Purchase a Grimtotem from a Mage Merchant."
                continue

            spell_options = []
            spell_names   = list(available.keys())
            for sn in spell_names:
                sp   = available[sn]
                cost = max(0, sp["cost"] - player.mana_discount)
                if player.mana >= cost:
                    color = C.BBLUE
                    glyph = "✦"
                else:
                    color = C.BBLACK
                    glyph = "✗"
                spell_options.append(
                    f"{color}{glyph} {sn:<16}{C.RESET}  "
                    f"{C.DIM}Cost: {cost} mana  {sp['description']}{C.RESET}"
                )
            spell_options.append(f"{C.BBLACK}← Back{C.RESET}")

            show_combat_screen(player, enemy, message)
            sc = prompt_choice(spell_options, "Cast which spell?")
            if sc == len(spell_options):
                message = "You hold your focus."
                continue

            sname  = spell_names[sc - 1]
            spell  = available[sname]
            cost   = max(0, spell["cost"] - player.mana_discount)

            if not player.spend_mana(cost):
                message = (
                    f"Not enough mana! {sname} costs {cost}, "
                    f"you have {player.mana}."
                )
                continue

            dmg, label, stag = cast_spell(sname, player, enemy, state)

            if spell.get("damage_type") == "heal":
                message = f"You cast {C.BPURPLE}{sname}{C.RESET}! You recover {C.BGREEN}{dmg}{C.RESET} HP."
                beep("heal")
            else:
                enemy.take_damage(dmg)
                message = (
                    f"You cast {C.BPURPLE}{sname}{C.RESET}! It's {label}! "
                    f"({C.BBLUE}{dmg}{C.RESET} magic damage)"
                )
                if stag:
                    message += f"\n  [{stag}]"
                beep("cast")
            action_taken = True

        # ── ITEMS ────────────────────────────────────────────────────────────
        elif top == 3:
            potions = [
                i for i in player.inventory
                if i.item_type in ("potion", "consumable") and i.effect
            ]
            if not potions:
                show_combat_screen(player, enemy, message)
                print(f"  {C.BRED}You're out of combat supplies.{C.RESET}")
                pause("Press Enter to return to combat...")
                continue

            pot_options = []
            for p in potions:
                pot_options.append(
                    f"{C.BGREEN}{p.name}{C.RESET}  {C.DIM}{p.description}{C.RESET}"
                )
            pot_options.append(f"{C.BBLACK}← Back{C.RESET}")

            show_combat_screen(player, enemy, message)
            pc = prompt_choice(pot_options, "Use which item?")
            if pc == len(pot_options):
                message = "You pocket your pack."
                continue

            chosen_potion = potions[pc - 1]
            result_msg    = use_potion(player, chosen_potion, state)
            player.remove_item(chosen_potion)
            message       = result_msg
            beep("heal")
            action_taken  = True

        # ── FLEE ─────────────────────────────────────────────────────────────
        elif top == 4:
            if attempt_flee(player, enemy):
                show_combat_screen(player, enemy, "You slip away into the shadows.")
                beep("menu")
                time.sleep(1.5)
                stop_battle_music()
                resume_ambient_loop()
                return False
            message      = "You couldn't escape!"
            action_taken = True

        # ── Enemy counter-attack ──────────────────────────────────────────────
        if action_taken and enemy.is_alive() and player.is_alive():
            e_dmg, e_move, e_is_spell = enemy_attack(enemy, player, state)
            player.take_damage(e_dmg)
            e_verb = "casts" if e_is_spell else "retaliates with"
            if e_dmg == 0:
                message += f"\n  {enemy.name} {e_verb} {e_move}! (missed)"
            else:
                message += (
                    f"\n  {enemy.name} {e_verb} {e_move} "
                    f"for {C.BRED}{e_dmg}{C.RESET} damage."
                )
            beep("hit")

    if not player.is_alive():
        show_combat_screen(player, enemy, "You collapse. The world fades to black...")
        stop_battle_music()
        play_melody("death")
        time.sleep(2)
        return False

    show_combat_screen(player, enemy, f"Victory! The {enemy.name} falls!")
    stop_battle_music()
    play_melody("victory")
    time.sleep(1.5)
    resume_ambient_loop()
    return True


def loot_screen(player: Player, enemy):
    loot = generate_loot(bias=enemy.loot_bias)
    clear()
    title_screen("LOOT")

    print(f"  {C.BGREEN}You search the fallen {enemy.name}...{C.RESET}")
    print()

    color = RARITY_COLOR.get(loot.rarity, C.WHITE)
    print(f"  Found:  {color}{C.BOLD}{loot.name}{C.RESET}  [{rarity_tag(loot.rarity)}]")
    print(f"  {C.DIM}{loot.description}{C.RESET}")
    print(f"  {C.BYELLOW}Base value: {loot.base_value}gp{C.RESET}")
    print()

    if not player.can_carry():
        print(f"  {C.BRED}Inventory full ({MAX_INVENTORY}/{MAX_INVENTORY})! Can't carry more.{C.RESET}")
        pause()
        return

    choice = prompt_choice(["Take the item", "Leave it behind"])
    if choice == 1:
        player.add_item(loot)
        print(f"\n  {C.BGREEN}Added {loot.name} to your inventory.{C.RESET}")
    else:
        print(f"\n  {C.DIM}You leave it behind.{C.RESET}")
    time.sleep(0.8)
