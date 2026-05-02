---
type: play-test
version: v2.2
status: archived
systems:
  - world
  - ui
  - stealth
  - combat
---

- music is still too loud - not sure if there is a way to lower it. 
- can we extend the loop to maybe like 5 extra beeps? 7
* game crash when attempting to forage for food and encountering a bandit:
```
  You move quietly through the undergrowth...

  A Bandit Cutthroat finds you before you find anything useful.
  Fast and vicious. Light armour, heavy intent.
Traceback (most recent call last):
  File "C:\Users\user\OneDrive\Documents\Second Brain\Craft\Text Based RPG\game\main.py", line 2527, in <module>
    main()
  File "C:\Users\user\OneDrive\Documents\Second Brain\Craft\Text Based RPG\game\main.py", line 2523, in main
    road_loop(player)
  File "C:\Users\user\OneDrive\Documents\Second Brain\Craft\Text Based RPG\game\main.py", line 2408, in road_loop
    bushcraft_screen(player)
  File "C:\Users\user\OneDrive\Documents\Second Brain\Craft\Text Based RPG\game\main.py", line 2184, in bushcraft_screen
    _do_forage(player)
  File "C:\Users\user\OneDrive\Documents\Second Brain\Craft\Text Based RPG\game\main.py", line 1884, in _do_forage
    won = run_combat(player, enc_enemy)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\user\OneDrive\Documents\Second Brain\Craft\Text Based RPG\game\main.py", line 439, in run_combat
    e_dmg, e_move, e_is_spell = enemy_attack(enemy, player, state)
                                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\user\OneDrive\Documents\Second Brain\Craft\Text Based RPG\game\engine\combat.py", line 291, in enemy_attack
    base       = move.get("power", enemy.base_damage) * random.uniform(0.8, 1.2)
                                   ^^^^^^^^^^^^^^^^^
AttributeError: 'Enemy' object has no attribute 'base_damage'. Did you mean: 'take_damage'?
```