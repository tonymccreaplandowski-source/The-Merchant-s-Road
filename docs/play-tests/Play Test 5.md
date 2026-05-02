---
type: play-test
version: v2.0
status: archived
systems:
  - merchant
  - stealth
  - combat
  - ui
  - character
---

 1. should not be able to use resources on a camp if you have full health. 
 2. we need a place in character sheet where the person can re-read what the skills are and what they govern - for reference when trying to upgrade and stuff - and by this I mean a place where they can read ALL that the skills govern. Not necessariily the MATH behind everything but conceptually what they govern. 
 3. also i'd like to have each merchant say something to the player when they walk up.
 4. we need each item to have a description while in the inventory i.e. it should say what the curse does, or what the benefit does e.g. curse (-5 points to ....)
 5. music is super loud - we need to lower the value by about 50%
 6. when the player hits stealth and successfully enters a room with enemies they should be able to choose:
	 1. strike  the enemy steathly?
	 2. steal from the room?
7. we need to lower the total amount of points from 180 to 100 only - the player cannot be able to stack an ability to 100 right off the bat. 
8. When foraging this should act the same as traveling in that there is a chance for encounter with enemy or location i.e. its moving just not moving from town to town. 
9. TK seemed capable of sneaking inside a location twice in a row despite his stealth only being 5.
---

```
A Bandit Cutthroat blocks your path! Fast and vicious. Light armour, heavy intent. Traceback (most recent call last): File "C:\Users\tyler\Downloads\The-Merchant-s-Road-main\The-Merchant-s-Road-main\game\main.py", line 2361, in <module> main() ~~~~^^ File "C:\Users\tyler\Downloads\The-Merchant-s-Road-main\The-Merchant-s-Road-main\game\main.py", line 2357, in main road_loop(player)~~ ~~~~~~~^^^^^^^^ File "C:\Users\tyler\Downloads\The-Merchant-s-Road-main\The-Merchant-s-Road-main\game\main.py", line 2295, in road_loop won = run_combat(player, enemy) File "C:\Users\tyler\Downloads\The-Merchant-s-Road-main\The-Merchant-s-Road-main\game\main.py", line 392, in run_combat e_dmg, e_move, e_is_spell = enemy_attack(enemy, player, state)~~ ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^ File "C:\Users\tyler\Downloads\The-Merchant-s-Road-main\The-Merchant-s-Road-main\game\engine\combat.py", line 261, in enemy_attack move_name = random.choice(enemy.moves) if enemy.moves else "Strike" ^^^^^^^^^^^ AttributeError: 'Enemy' object has no attribute 'moves' C:\Users\tyler\Downloads\The-Merchant-s-Road-main\The-Merchant-s-Road-main\game>
```