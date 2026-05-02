---
type: play-test
version: v2.3
status: archived
systems:
  - combat
  - merchant
---

1. city options 7 and 8 should be consolidated into 1 option called "Travel" and then the player should be prompted "Where would you like to go?" -> player clicks entre to continue -> they are shown whichever option is available i.e. if in rabenmark they can go either to GS or DN, if in DN they may only go to RM etc.
2. Each section of the road should procedurally generate random flavor lines about what the player might see while travelling. Gives the player a reason pause and increases the immersion.
	1. e.g. at step 0 "you begin your journey towrds and... you see.."
	2. step 1 "your first night under the stars has pass... .\
	3. step 2 etc.. 
3. when faced with an ecnounter on the road right before combat, either while during buschcraft or at a location, the player must always hit "enter" before the fight inititates. Currently, the player sees the screen that they have been discovered and it stays for only a second before switching screen. 
4. Writing animation for context information:
	1. ```
	    » You use Smash! Missed entirely!
  » [miss]
  » Road Bandit retaliates with Pierce! (missed)
	   ```
		The above informaiton just appears, there is no writing animation while in combat.
5. my duneoneering was really low but I always seem successfully able to determine how many people are in a room without fail.
6. CRASH:
	1. ```
	     Skeleton Warrior bars your way.
Traceback (most recent call last):
  File "C:\Users\user\OneDrive\Documents\Second Brain\Craft\Text Based RPG\game\main.py", line 2857, in <module>
    main()
  File "C:\Users\user\OneDrive\Documents\Second Brain\Craft\Text Based RPG\game\main.py", line 2853, in main
    road_loop(player)
  File "C:\Users\user\OneDrive\Documents\Second Brain\Craft\Text Based RPG\game\main.py", line 2803, in road_loop
    explore_event(player, event)
  File "C:\Users\user\OneDrive\Documents\Second Brain\Craft\Text Based RPG\game\main.py", line 1977, in explore_event
    won = run_combat(player, enemy, force_first=is_ambush)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\user\OneDrive\Documents\Second Brain\Craft\Text Based RPG\game\main.py", line 707, in run_combat
    e_dmg, e_move, e_is_spell = enemy_attack(enemy, player, state)
                                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\user\OneDrive\Documents\Second Brain\Craft\Text Based RPG\game\engine\combat.py", line 289, in enemy_attack
    armor_type = armor.armor_type if armor else "none"
                 ^^^^^^^^^^^^^^^^
AttributeError: 'Item' object has no attribute 'armor_type'. Did you mean: 'armor_value'?
	    ```