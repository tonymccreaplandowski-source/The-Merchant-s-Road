---
type: play-test
version: v2.7
status: archived
systems:
  - merchant
  - negotiate
  - world
---

- "Read" should be an option either in the bag and in the inventory and they should be able to do that either in the city or on the road. 
	- looks like the pc was only able to go through 2 rounds - they don't get the chance to do  "round 3/3" - so technically there is supposed to be the final 4th round which is the "tensions are as high as they'll go". 
- Traceback (most recent call last):
```

  File "C:\Users\user\OneDrive\Documents\Second Brain\Craft\Text Based RPG\game\main.py", line 33, in <module>
    main()
  File "C:\Users\user\OneDrive\Documents\Second Brain\Craft\Text Based RPG\game\main.py", line 29, in main
    road_loop(player)
  File "C:\Users\user\OneDrive\Documents\Second Brain\Craft\Text Based RPG\game\ui\road.py", line 918, in road_loop
    bushcraft_screen(player)
  File "C:\Users\user\OneDrive\Documents\Second Brain\Craft\Text Based RPG\game\ui\road.py", line 667, in bushcraft_screen
    _do_forage(player)
  File "C:\Users\user\OneDrive\Documents\Second Brain\Craft\Text Based RPG\game\ui\road.py", line 388, in _do_forage
    explore_event(player, event)
  File "C:\Users\user\OneDrive\Documents\Second Brain\Craft\Text Based RPG\game\ui\road.py", line 228, in explore_event
    if event.lore and event.lore not in player.journal:
       ^^^^^^^^^^
AttributeError: 'RoadEvent' object has no attribute 'lore'
```
- 