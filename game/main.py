"""
The Merchant's Road — Main entry point.

Run with:  python main.py
"""

from ui.display  import C, clear, pause, title_screen, start_ambient_loop, stop_ambient_loop
from ui.creation import character_creation
from ui.city     import city_loop
from ui.road     import road_loop


def main():
    clear()
    title_screen("THE MERCHANT'S ROAD")
    print(f"  {C.DIM}Three cities. Open roads. One market worth mastering.{C.RESET}")
    print()
    print(f"  {C.BBLACK}Alpha - World v2.8  |  Play Test 16 Pass{C.RESET}")
    print()
    pause("Press Enter to begin...")

    player = character_creation()

    while True:
        city_loop(player)
        if player.on_road:
            start_ambient_loop("road")
            road_loop(player)


if __name__ == "__main__":
    main()
