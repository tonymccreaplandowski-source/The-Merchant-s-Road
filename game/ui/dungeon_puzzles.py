"""
Dungeon puzzle mini-games.

Four types:
  riddle   — scripted question, text-input answer, one attempt
  reveal   — health-bar obscured object, progressive skill-rolls reveal it
  maze     — ASCII grid navigation via WASD (msvcrt), optional time limit
  sequence — three-symbol ordered lock, clues in room flavor text

Dungeoneering skill scales difficulty across all types.
Item hooks: Lock Picks bypass puzzle gates; Torch/Lantern improve maze visibility.
"""

import random
import time

from engine.player import Player
from ui.display    import C, clear, pause, hr, prompt_choice, typewrite


# ── Dungeoneering difficulty helper ──────────────────────────────────────────

def _dung_difficulty(player: Player, base: int = 13) -> int:
    """
    Return a roll threshold that decreases as Dungeoneering rises.
    base=13 is standard difficulty; range clamped to [5, 18].
    """
    reduction = player.skill("Dungeoneering") // 6
    return max(5, min(18, base - reduction))


# ═══════════════════════════════════════════════════════════════════════════════
# TYPE 1 — RIDDLE
# ═══════════════════════════════════════════════════════════════════════════════

RIDDLES = [
    {
        "text":       "I speak without a mouth and hear without ears. I have no body, but I come alive with wind. What am I?",
        "answers":    ["echo"],
        "clue":       "Think of what returns your voice in a canyon.",
    },
    {
        "text":       "The more you take, the more you leave behind. What am I?",
        "answers":    ["footsteps", "footstep", "steps", "tracks"],
        "clue":       "Consider what a traveller makes with every stride.",
    },
    {
        "text":       "I have cities, but no houses live there. I have mountains, but no trees grow. I have water, but no fish swim. I have roads, but no carts travel. What am I?",
        "answers":    ["map", "a map"],
        "clue":       "Cartographers make me. Travellers consult me.",
    },
    {
        "text":       "I fly without wings. I cry without eyes. Wherever I go, darkness follows. What am I?",
        "answers":    ["cloud", "a cloud", "storm cloud", "storm"],
        "clue":       "Look up when the light fails.",
    },
    {
        "text":       "I can be cracked, made, told, and played. What am I?",
        "answers":    ["joke", "a joke"],
        "clue":       "You hear it. Then you either laugh or groan.",
    },
    {
        "text":       "The man who makes it doesn't need it. The man who buys it doesn't use it. The man who uses it doesn't know it. What is it?",
        "answers":    ["coffin", "a coffin"],
        "clue":       "It is built for one purpose, used only once.",
    },
    {
        "text":       "I have hands but cannot clap. I have a face but no eyes. I tell you something every time you look, but never speak. What am I?",
        "answers":    ["clock", "a clock", "watch", "a watch"],
        "clue":       "Its face moves, but it never breathes.",
    },
    {
        "text":       "I am always in front of you but cannot be seen. What am I?",
        "answers":    ["future", "the future"],
        "clue":       "Not the past, not the present.",
    },
    {
        "text":       "The more there is of me, the less you can see. What am I?",
        "answers":    ["darkness", "dark", "shadow", "fog", "mist"],
        "clue":       "Torchlight is your enemy when answering this.",
    },
    {
        "text":       "I have no legs, no arms, no head — yet I carry a sword and stand at every city gate. What am I?",
        "answers":    ["lock", "a lock", "iron lock"],
        "clue":       "A key is what defeats it.",
    },
    {
        "text":       "Kings and queens bow before me. Mountains crumble at my touch. Yet a child of five can master me. What am I?",
        "answers":    ["time", "time itself"],
        "clue":       "It passes regardless of station.",
    },
    {
        "text":       "I am not alive, yet I grow. I have no lungs, yet I need air. I have no mouth, yet water kills me. What am I?",
        "answers":    ["fire", "flame", "a fire", "a flame"],
        "clue":       "It warms your camp. It ends with rain.",
    },
    {
        "text":       "I have a tail and a head, but no body. What am I?",
        "answers":    ["coin", "a coin"],
        "clue":       "Merchants handle thousands of me every day.",
    },
    {
        "text":       "I can fill a room but take up no space. What am I?",
        "answers":    ["light", "sunlight", "firelight"],
        "clue":       "Your torch produces it.",
    },
    {
        "text":       "What has teeth but cannot bite?",
        "answers":    ["comb", "a comb", "gear", "a gear", "key", "a key", "saw"],
        "clue":       "It is made of metal or bone, and keeps things in order.",
    },
    {
        "text":       "I am taken from a mine and shut in a wooden case. Almost everyone uses me, yet I am never seen. What am I?",
        "answers":    ["pencil", "a pencil", "lead", "graphite"],
        "clue":       "Scribes and scholars know me well.",
    },
    {
        "text":       "What can you hold in your right hand but never in your left?",
        "answers":    ["left hand", "your left hand", "the left hand"],
        "clue":       "Think about what the question is actually asking.",
    },
    {
        "text":       "The more you dry me, the wetter I get. What am I?",
        "answers":    ["towel", "a towel", "cloth", "rag"],
        "clue":       "Used after water, not before.",
    },
    {
        "text":       "I have four legs in the morning, two at noon, and three in the evening. What am I?",
        "answers":    ["human", "a human", "man", "a man", "person", "people"],
        "clue":       "This is the oldest riddle. The Sphinx asked it.",
    },
    {
        "text":       "I go up and down, yet never move from where I stand. What am I?",
        "answers":    ["stairs", "staircase", "a staircase", "steps"],
        "clue":       "You are standing in a structure that likely contains me.",
    },
    {
        "text":       "I am always hungry and must always be fed. The finger I touch will soon turn red. What am I?",
        "answers":    ["fire", "flame", "a fire"],
        "clue":       "It consumes wood and warms the cold.",
    },
    {
        "text":       "What breaks when you speak it?",
        "answers":    ["silence", "quiet", "stillness"],
        "clue":       "Before you answered, the room was full of it.",
    },
]


def run_riddle(player: Player, gating: bool = False) -> bool:
    """
    Present a riddle. One attempt only.
    Returns True if solved (or bypassed with Lock Picks), False otherwise.
    gating: if True, failure locks progress (shown in flavor text).
    """
    riddle = random.choice(RIDDLES)
    diff   = _dung_difficulty(player, base=14)

    clear()
    print()
    hr("─")
    print(f"  {C.BYELLOW}❖  A RIDDLE IS CARVED INTO THE STONE{C.RESET}")
    hr("─")
    print()
    typewrite(riddle["text"])
    print()

    # Dungeoneering clue — better skill reveals the hint
    dung_roll = random.randint(1, 20) + player.skill("Dungeoneering") // 5
    if dung_roll >= diff:
        print(f"  {C.DIM}Your knowledge stirs. {riddle['clue']}{C.RESET}")
        print()

    # Lock Picks bypass
    has_picks = any(i.name == "Lock Picks" for i in player.inventory)
    if has_picks and gating:
        print(f"  {C.DIM}You have Lock Picks. You could force the mechanism instead.{C.RESET}")
        print()
        use = prompt_choice(["Answer the riddle", "Use Lock Picks (consumed)"])
        if use == 2:
            picks = next(i for i in player.inventory if i.name == "Lock Picks")
            player.remove_item(picks)
            print(f"\n  {C.BGREEN}The picks find purchase in the lock. The door grinds open.{C.RESET}")
            time.sleep(1.0)
            return True

    # Text input
    print(f"  {C.DIM}You have one attempt.{C.RESET}")
    print()
    try:
        answer = input(f"  {C.BYELLOW}Your answer:{C.RESET}  ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        answer = ""

    accepted = [a.lower() for a in riddle["answers"]]
    if answer in accepted:
        print(f"\n  {C.BGREEN}The stone shifts. The answer echoes and fades.{C.RESET}")
        time.sleep(1.0)
        return True
    else:
        correct = riddle["answers"][0]
        if gating:
            print(f"\n  {C.BRED}Wrong. The mechanism locks. The answer was: {correct}.{C.RESET}")
        else:
            print(f"\n  {C.BYELLOW}Nothing happens. The answer was: {correct}.{C.RESET}")
        time.sleep(1.2)
        return False


# ═══════════════════════════════════════════════════════════════════════════════
# TYPE 2 — REVEAL (health-bar obscured object)
# ═══════════════════════════════════════════════════════════════════════════════

REVEAL_OBJECTS = [
    {
        "name":    "a sealed iron chest",
        "clues":   [
            "...cold metal... rectangular... handles worn smooth...",
            "...hinged lid... reinforced corners... a heavy lock...",
            "...stamped with a merchant's mark... iron-banded... full of something...",
        ],
        "options": ["An iron chest", "A stone altar", "A weapon rack", "A crate of bones"],
        "correct": 0,
        "reward":  "loot",
    },
    {
        "name":    "an ancient weapon rack",
        "clues":   [
            "...tall... wooden uprights... something held horizontally...",
            "...brackets of iron... the thing it holds is long and thin...",
            "...pegs at regular intervals... blades or shafts, hard to tell...",
        ],
        "options": ["A weapon rack", "A bookshelf", "A ladder", "A bed frame"],
        "correct": 0,
        "reward":  "loot",
    },
    {
        "name":    "a locked door",
        "clues":   [
            "...a vertical plane... hinges on one side... resistance when pushed...",
            "...wood or iron... a gap at the bottom... cold air through it...",
            "...a keyhole at shoulder height... something beyond it...",
        ],
        "options": ["A locked door", "A sealed window", "A mirror", "A painting"],
        "correct": 0,
        "reward":  "access",
    },
    {
        "name":    "a stone altar",
        "clues":   [
            "...flat surface... waist height... something resting on top...",
            "...carved from single stone... symbols along the base...",
            "...offerings placed... cold to the touch... an object at the centre...",
        ],
        "options": ["A stone altar", "A workbench", "A dining table", "A sarcophagus lid"],
        "correct": 0,
        "reward":  "loot",
    },
]


def _render_bar(revealed: int, total: int = 5) -> str:
    """Render a depletion bar. revealed = segments uncovered so far."""
    filled  = "█" * revealed
    empty   = "░" * (total - revealed)
    return f"  {C.BYELLOW}╔{'═' * 22}╗{C.RESET}\n  {C.BYELLOW}║{C.RESET} {C.BRED}{filled}{C.DIM}{empty}{C.RESET} {C.BYELLOW}║{C.RESET}\n  {C.BYELLOW}╚{'═' * 22}╝{C.RESET}"


def run_reveal(player: Player, gating: bool = False) -> bool:
    """
    Progressive reveal puzzle. Player makes skill rolls to uncover a description,
    then names what they see. One final guess.
    Returns True on correct identification or Lock Picks bypass.
    """
    obj     = random.choice(REVEAL_OBJECTS)
    clues   = list(obj["clues"])
    options = list(obj["options"])
    correct = obj["correct"]

    clear()
    print()
    hr("─")
    print(f"  {C.BYELLOW}❖  SOMETHING IS OBSCURED IN THE DARK{C.RESET}")
    hr("─")
    print()
    print(f"  {C.DIM}Something is here. You can't quite make it out.{C.RESET}")
    print()

    # Lock Picks bypass (only on gating rooms, and only if the reward is access)
    has_picks = any(i.name == "Lock Picks" for i in player.inventory)
    if has_picks and gating and obj["reward"] == "access":
        print(f"  {C.DIM}You have Lock Picks. You could try to bypass whatever this is.{C.RESET}")
        print()
        use = prompt_choice(["Examine it", "Use Lock Picks (consumed)"])
        if use == 2:
            picks = next(i for i in player.inventory if i.name == "Lock Picks")
            player.remove_item(picks)
            print(f"\n  {C.BGREEN}The lock surrenders. You don't need to know what was behind it.{C.RESET}")
            time.sleep(1.0)
            return True

    # Torch/Lantern bonus
    has_lantern     = any(i.name == "Lantern"      for i in player.inventory)
    has_torch       = any(i.name == "Torch Bundle" for i in player.inventory)
    light_bonus     = 4 if has_lantern else (2 if has_torch else 0)
    if light_bonus:
        src = "lantern light" if has_lantern else "torchlight"
        print(f"  {C.BYELLOW}Your {src} helps. (+{light_bonus} to examine rolls){C.RESET}")
        print()

    # Examination rounds — 3 rounds, each reveals a clue on success
    revealed   = 0
    clues_seen = []
    TOTAL_SEGS = 5

    examine_options = [
        f"Examine closely    {C.DIM}[Dungeoneering]{C.RESET}",
        f"Listen carefully   {C.DIM}[Survival]{C.RESET}",
        f"Reach out and feel {C.DIM}[Martial]{C.RESET}",
    ]

    for rnd in range(3):
        clear()
        print()
        hr("─")
        print(f"  {C.BYELLOW}❖  SOMETHING IS OBSCURED — Round {rnd+1}/3{C.RESET}")
        hr("─")
        print()
        print(_render_bar(revealed, TOTAL_SEGS))
        print()
        if clues_seen:
            print(f"  {C.DIM}What you've gathered so far:{C.RESET}")
            for c in clues_seen:
                print(f"  {C.DIM}→ {c}{C.RESET}")
            print()

        diff  = _dung_difficulty(player, base=12)
        choice = prompt_choice(examine_options + [f"Make your guess now {C.DIM}(end early){C.RESET}"])

        if choice == len(examine_options) + 1:
            break

        if choice == 1:
            roll = random.randint(1, 20) + player.skill("Dungeoneering") // 4 + light_bonus
            skill_name = "Dungeoneering"
        elif choice == 2:
            roll = random.randint(1, 20) + player.skill("Survival") // 4 + light_bonus
            skill_name = "Survival"
        else:
            roll = random.randint(1, 20) + player.skill("Martial") // 4 + light_bonus
            skill_name = "Martial"

        if roll >= diff and clues:
            clue = clues.pop(0)
            clues_seen.append(clue)
            revealed = min(TOTAL_SEGS, revealed + 2)
            print(f"\n  {C.BGREEN}[{skill_name}] You make out: {clue}{C.RESET}")
        else:
            print(f"\n  {C.DIM}[{skill_name}] You can't get a clear read on it.{C.RESET}")

        time.sleep(0.8)

    # Final guess
    clear()
    print()
    hr("─")
    print(f"  {C.BYELLOW}❖  WHAT IS IT?{C.RESET}")
    hr("─")
    print()
    print(_render_bar(revealed, TOTAL_SEGS))
    print()
    if clues_seen:
        for c in clues_seen:
            print(f"  {C.DIM}→ {c}{C.RESET}")
        print()

    print(f"  {C.DIM}One guess. Make it count.{C.RESET}")
    print()

    guess = prompt_choice(options)
    if guess - 1 == correct:
        print(f"\n  {C.BGREEN}Yes. You knew what you were looking at.{C.RESET}")
        time.sleep(1.0)
        return True
    else:
        print(f"\n  {C.BYELLOW}Wrong. It was {obj['name']}.{C.RESET}")
        time.sleep(1.2)
        return False


# ═══════════════════════════════════════════════════════════════════════════════
# TYPE 3 — ASCII MAZE
# ═══════════════════════════════════════════════════════════════════════════════

# Maze layouts: 0 = wall, 1 = open, S = start coords, E = exit coords
# Grid is rendered row-by-row; player position shown as @
MAZE_LAYOUTS = [
    {
        "grid": [
            [0,1,0,0,0,0,0],
            [0,1,1,1,0,1,0],
            [0,0,0,1,0,1,0],
            [0,1,1,1,1,1,0],
            [0,1,0,0,0,1,0],
            [0,1,1,0,1,1,0],
            [0,0,1,1,1,0,0],
        ],
        "start": (0, 1),   # (row, col)
        "exit":  (6, 4),
        "base_moves": 40,
    },
    {
        "grid": [
            [0,0,0,1,0,0,0],
            [0,1,1,1,1,1,0],
            [0,1,0,0,0,1,0],
            [0,1,1,0,1,1,0],
            [0,0,1,0,1,0,0],
            [0,1,1,1,1,1,0],
            [0,0,0,0,1,0,0],
        ],
        "start": (0, 3),
        "exit":  (6, 4),
        "base_moves": 38,
    },
    {
        "grid": [
            [0,1,0,0,0,1,0],
            [0,1,1,1,0,1,0],
            [0,0,0,1,1,1,0],
            [0,1,0,0,0,1,0],
            [0,1,1,1,0,1,0],
            [0,0,0,1,1,1,0],
            [0,0,0,0,0,1,0],
        ],
        "start": (0, 1),
        "exit":  (6, 5),
        "base_moves": 42,
    },
]

_WALL  = "█"
_OPEN  = "·"
_PLAYER= f"{C.BGREEN}@{C.RESET}"
_EXIT  = f"{C.BYELLOW}E{C.RESET}"
_FOG   = " "


def _render_maze(grid, player_pos, exit_pos, fog_radius: int) -> str:
    rows = []
    pr, pc = player_pos
    er, ec = exit_pos
    for r, row in enumerate(grid):
        line = "  "
        for c, cell in enumerate(row):
            if (r, c) == player_pos:
                line += _PLAYER
            elif (r, c) == exit_pos:
                # Always show exit if within fog radius, else hide in fog
                if abs(r - pr) <= fog_radius and abs(c - pc) <= fog_radius:
                    line += _EXIT
                else:
                    line += _FOG
            elif abs(r - pr) <= fog_radius and abs(c - pc) <= fog_radius:
                line += _WALL if cell == 0 else _OPEN
            else:
                line += _FOG
            line += " "
        rows.append(line)
    return "\n".join(rows)


def run_maze(player: Player, timed: bool = False) -> bool:
    """
    ASCII maze mini-game. WASD navigation via msvcrt.
    Returns True if player reaches the exit, False if they give up or time runs out.
    timed: if True, player has a move/time limit (extended by Dungeoneering).
    """
    layout     = random.choice(MAZE_LAYOUTS)
    grid       = [row[:] for row in layout["grid"]]   # deep copy
    start      = tuple(layout["start"])
    exit_pos   = tuple(layout["exit"])
    pos        = list(start)
    rows       = len(grid)
    cols       = len(grid[0])

    # Fog of war radius — Dungeoneering improves visibility
    dung = player.skill("Dungeoneering")
    has_lantern = any(i.name == "Lantern"      for i in player.inventory)
    has_torch   = any(i.name == "Torch Bundle" for i in player.inventory)
    if has_lantern:
        fog_radius = 3
    elif has_torch:
        fog_radius = 2
    elif dung >= 50:
        fog_radius = 2
    else:
        fog_radius = 1

    # Move / time budget for timed mazes
    base_moves    = layout["base_moves"]
    bonus_moves   = (dung // 5) * 5          # +5 moves per 5 Dungeoneering levels
    move_budget   = base_moves + bonus_moves
    moves_used    = 0

    # Timed: convert to wall-clock seconds (loose approximation — 1 move ≈ enough time)
    time_limit    = None
    start_time    = None
    if timed:
        # Base 30 s + 5 s per 5 Dungeoneering above 0
        time_limit = 30 + (dung // 5) * 5
        start_time = time.time()

    # msvcrt is Windows-only — import lazily so module loads on all platforms
    try:
        import msvcrt as _msvcrt
        _has_keys = True
    except ImportError:
        _msvcrt = None   # type: ignore
        _has_keys = False

    # Fallback for non-Windows: treat maze as a skill check
    if not _has_keys:
        dung_roll = random.randint(1, 20) + player.skill("Dungeoneering") // 4
        diff      = 12 if not timed else 15
        clear()
        print()
        hr("─")
        print(f"  {C.BYELLOW}❖  A MAZE BLOCKS YOUR PATH{C.RESET}")
        hr("─")
        print(f"  {C.DIM}You study the layout carefully...{C.RESET}")
        time.sleep(0.8)
        if dung_roll >= diff:
            print(f"\n  {C.BGREEN}Your spatial sense guides you through.{C.RESET}")
            time.sleep(1.0)
            return True
        else:
            print(f"\n  {C.DIM}You can't find the way. The maze defeats you.{C.RESET}")
            time.sleep(1.0)
            return False

    clear()
    print()
    hr("─")
    print(f"  {C.BYELLOW}❖  A MAZE BLOCKS YOUR PATH{C.RESET}")
    hr("─")
    print(f"  {C.DIM}Navigate from {C.BGREEN}@{C.RESET}{C.DIM} to {C.BYELLOW}E{C.RESET}{C.DIM}."
          f"  WASD to move.  Q to give up.{C.RESET}")
    if timed:
        print(f"  {C.BRED}Time limit: {time_limit}s"
              f"  (Dungeoneering bonus: +{(dung // 5) * 5}s){C.RESET}")
    else:
        print(f"  {C.DIM}Move budget: {move_budget} steps"
              f"  (Dungeoneering bonus: +{bonus_moves} steps){C.RESET}")
    print()
    pause("  Press Enter to begin...")

    while True:
        # Check time
        elapsed = 0.0
        if timed and start_time is not None:
            elapsed = time.time() - start_time
            if elapsed >= time_limit:
                clear()
                print(f"\n  {C.BRED}The passage collapses around you. You're forced back.{C.RESET}")
                time.sleep(1.2)
                return False

        # Check move budget (non-timed)
        if not timed and moves_used >= move_budget:
            clear()
            print(f"\n  {C.BRED}You've lost your way completely. You stumble back to the entrance.{C.RESET}")
            time.sleep(1.2)
            return False

        # Render
        clear()
        print()
        if timed and start_time is not None:
            remaining = max(0, time_limit - elapsed)
            print(f"  {C.BRED}Time: {remaining:.0f}s remaining{C.RESET}")
        else:
            print(f"  {C.DIM}Moves: {moves_used}/{move_budget}{C.RESET}")
        print()
        print(_render_maze(grid, tuple(pos), exit_pos, fog_radius))
        print()
        print(f"  {C.DIM}WASD to move  |  Q to give up{C.RESET}")

        # Read key
        try:
            key = _msvcrt.getch()
        except Exception:
            return False

        # Arrow keys send two bytes on Windows: b'\xe0' + direction byte
        if key == b'\xe0':
            try:
                key2 = _msvcrt.getch()
            except Exception:
                continue
            move_map = {b'H': (-1,0), b'P': (1,0), b'K': (0,-1), b'M': (0,1)}
            delta = move_map.get(key2)
        else:
            move_map = {
                b'w': (-1, 0), b'W': (-1, 0),
                b's': ( 1, 0), b'S': ( 1, 0),
                b'a': ( 0,-1), b'A': ( 0,-1),
                b'd': ( 0, 1), b'D': ( 0, 1),
            }
            delta = move_map.get(key)

        if key in (b'q', b'Q'):
            print(f"\n  {C.DIM}You turn back. The maze remains unsolved.{C.RESET}")
            time.sleep(0.8)
            return False

        if delta is None:
            continue

        nr, nc = pos[0] + delta[0], pos[1] + delta[1]
        if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == 1:
            pos[0], pos[1] = nr, nc
            moves_used += 1
        # else: wall, no move, no cost

        # Check exit
        if tuple(pos) == exit_pos:
            clear()
            print(f"\n  {C.BGREEN}You find the way through. Light ahead.{C.RESET}")
            time.sleep(1.0)
            return True


# ═══════════════════════════════════════════════════════════════════════════════
# TYPE 4 — SEQUENCE / LOGIC
# ═══════════════════════════════════════════════════════════════════════════════

SEQUENCE_PUZZLES = [
    {
        "setup":   "Three symbols are carved above the door: a moon, a sun, and a flame.",
        "clue_hi": "The inscription reads: 'Light rises before warmth. Warmth fades before dark.'",
        "clue_lo": "The inscription is worn. You make out 'rises' and 'fades'.",
        "order":   ["Sun", "Flame", "Moon"],
        "options": ["Sun", "Flame", "Moon"],
    },
    {
        "setup":   "Three levers: iron, copper, and silver.",
        "clue_hi": "The engraving reads: 'What is mined first. What is minted most. What is valued least.'",
        "clue_lo": "The engraving is scratched. You read 'mined', 'minted', 'valued'.",
        "order":   ["Iron", "Copper", "Silver"],
        "options": ["Iron", "Copper", "Silver"],
    },
    {
        "setup":   "Three stone tiles: a crown, a sword, and a coin.",
        "clue_hi": "Carved text reads: 'Before rule there is force. Before force there is need.'",
        "clue_lo": "The text is partial. You read 'rule', 'force', 'need'.",
        "order":   ["Coin", "Sword", "Crown"],
        "options": ["Coin", "Sword", "Crown"],
    },
    {
        "setup":   "Three pressure plates bear markings: water, earth, and air.",
        "clue_hi": "Above the door: 'From stone all rivers flow. From rivers all winds rise.'",
        "clue_lo": "Some letters are gone. You read 'stone', 'rivers', 'winds'.",
        "order":   ["Earth", "Water", "Air"],
        "options": ["Earth", "Water", "Air"],
    },
    {
        "setup":   "Three runes glow faintly: red, blue, and white.",
        "clue_hi": "A mage's note reads: 'Blue cools before white. White ignites before red. Red rules last.'",
        "clue_lo": "The note is burned at the edges. You make out 'cools', 'ignites', 'rules'.",
        "order":   ["Blue", "White", "Red"],
        "options": ["Blue", "White", "Red"],
    },
]


def run_sequence(player: Player, gating: bool = False) -> bool:
    """
    Three-symbol ordered lock. Clue clarity scales with Dungeoneering.
    One attempt. Lock Picks bypass on gating rooms.
    Returns True on correct sequence or bypass.
    """
    puzzle = random.choice(SEQUENCE_PUZZLES)
    diff   = _dung_difficulty(player, base=13)
    dung   = player.skill("Dungeoneering")

    clear()
    print()
    hr("─")
    print(f"  {C.BYELLOW}❖  A LOCKED MECHANISM BLOCKS THE WAY{C.RESET}")
    hr("─")
    print()
    typewrite(puzzle["setup"])
    print()

    # Clue quality based on Dungeoneering
    roll = random.randint(1, 20) + dung // 4
    if roll >= diff:
        print(f"  {C.BGREEN}{puzzle['clue_hi']}{C.RESET}")
    else:
        print(f"  {C.DIM}{puzzle['clue_lo']}{C.RESET}")
    print()

    # Lock Picks bypass
    has_picks = any(i.name == "Lock Picks" for i in player.inventory)
    if has_picks and gating:
        print(f"  {C.DIM}You have Lock Picks. You could force the lock.{C.RESET}")
        print()
        use = prompt_choice(["Solve the sequence", "Use Lock Picks (consumed)"])
        if use == 2:
            picks = next(i for i in player.inventory if i.name == "Lock Picks")
            player.remove_item(picks)
            print(f"\n  {C.BGREEN}The picks do their work. The mechanism surrenders.{C.RESET}")
            time.sleep(1.0)
            return True

    opts    = puzzle["options"]
    correct = puzzle["order"]

    print(f"  {C.DIM}Choose the correct order (3 selections):{C.RESET}")
    print()

    # Three consecutive choices
    remaining = list(opts)
    chosen    = []

    for step in range(1, 4):
        print(f"  {C.DIM}Step {step}/3  —  Already chosen: {chosen if chosen else 'none'}{C.RESET}")
        print()
        pick_idx = prompt_choice(remaining)
        pick     = remaining.pop(pick_idx - 1)
        chosen.append(pick)
        print()

    if chosen == correct:
        print(f"  {C.BGREEN}The mechanism clicks. Something shifts beyond the door.{C.RESET}")
        time.sleep(1.0)
        return True
    else:
        correct_str = " → ".join(correct)
        if gating:
            print(f"  {C.BRED}Wrong order. The mechanism locks. Correct: {correct_str}{C.RESET}")
        else:
            print(f"  {C.BYELLOW}Nothing. Wrong order. Correct: {correct_str}{C.RESET}")
        time.sleep(1.2)
        return False

# ═══════════════════════════════════════════════════════════════════════════════
# DISPATCHER
# ═══════════════════════════════════════════════════════════════════════════════

def run_puzzle(player, puzzle_type, timed=False, gating=False):
    """
    Dispatch to the correct puzzle mini-game.
    Returns True if the puzzle was solved (or bypassed), False otherwise.
    """
    if puzzle_type == "riddle":
        return run_riddle(player, gating=gating)
    elif puzzle_type == "reveal":
        return run_reveal(player, gating=gating)
    elif puzzle_type == "maze":
        return run_maze(player, timed=timed)
    elif puzzle_type == "sequence":
        return run_sequence(player, gating=gating)
    else:
        return run_riddle(player, gating=gating)
