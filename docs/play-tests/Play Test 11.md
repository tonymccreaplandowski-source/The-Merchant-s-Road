---
type: play-test
version: v2.6
status: archived
systems:
  - character
  - merchant
  - negotiate
  - world
  - items
---

1. class swap - alchemist should be magic and survival
	1. not magic and mercantilism. 
2. Hunger meter, how long can a human go without food in real life? 
	1. let impact this at the game level. 
3. So the likelihood of who I want to buy from shouldn't be revealed until AFTER I say that I'd like to buy from them - THEN it tells me who is available/. 1
4. traveling music persists despite walking back to the original city. 
5. Player was able to back out of negotiations and reset:
	1. we should lock them in to negotiations once started. 
	2. Never mind, they were locked out from negotiating but the merchant should say something of a flavor message like, "Um.. weird? No bother" i.e. slight annoyance that you walked away mid negotiation. 
	3. Also when negotiating, the merchants always seem to roll consistently strong e.g. 25 and up.  Even when they shared skill e.g. martial, it seemed really consistent. Maybe they're just bad rolls, but lets investigate to make sure. 
6. Location:
	1. at the end of a location complete i.e. beats all enemies they should always find some kind of loot that is uncommon or above or of equal weight in value in gold. 
	2. Their escape from a location should specific should depend on survival AND stealth - at location only. 
	3. Instead of the "push deeper" option; we should ask describe options of what is available at the location and allow the player to tell us where they'd like to go e.g.
		1. they kill first combatant -> collect loot -> Where would you like to go next? Leave, upstairs to tower, down stairs to dungeon...
7. Combat:
	1. mages are very strong, maybe reduce lethality by about 1%.  
	2. the player was unable to commit a lot of damage even with 33 martial and an enemy with 15 defense. 
	3. Perhaps this needs balanced. They "missed" a lot - but perhaps they should miss less and increase the chance to do  "ineffective damage". Not sure what our underlying math is but lets investigate.  
	4. Something seems off regarding the high defense of enemies and the players low defense and the the ability to hit often? we need to get a clear picture of the math.
	5. for example what kind of impact of having 30 martial and the enemy having 31 defense? 
8. We should have skill up items that are findable in the wilderness.  
9. Journal:
	1. once the text is in the journal we don't need to typewrite() in this location. 
	2. There's going to be too much - we should have the player load the journal and it just appears. 
