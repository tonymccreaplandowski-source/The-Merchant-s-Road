---
type: play-test
version: v2.6
status: archived
systems:
  - ui
  - combat
  - merchant
  - world
---

1. Text Truncated:
	1. " [5]  Grappling Hook  45gp  Thrown iron hook with rope. Dungeoneers swear by i…"
	2. [3]2  Adventurer's Map  57gp  A hand-drawn map of nearby roads. Increases chance…
2. Flavor text misplacement:
	1. the flavor text designed to add immersion from area to area while travelling are still occurring at the bottom of the screen and disappearing before giving the player a chance to read it. 
	2. it should instead replace the text that says "You step foot on the road to..." which is set  above the players options list / menu. 
	3. The line "you step foot onto the road to..." should be the first message that appears -> player hits entre -> then the first falvor message appears -> then player desides what to do from 0/6 steps -> continue as normal. 
3. Again, the text during combat is being written twice i.e. :
	1.  » Fast and vicious. Light armour, heavy intent. » Bandit Cutthroat moves first! attacks with Slash — 10 damage. - writes the first time then again whenever I entre a new menue e.g. type 1 to attack -> the next menu opens for picking weapon attack type -> it then types again. This should only occur its the string text is not the same != to the string text before it, otherwise the typewrite() method is not needed. 
4. On Combat:
	1. So I've run into a "bandit Sorcerer" and they're using all martial attacks:
		1.  » You use Slash! It's very effective! (14 dmg) » Bandit Sorcerer retaliates with Pierce for 7 damage.
		2. Also this bandits martial is 21, while mine is 20, and although they are using pierce they're only doing 9 damage. Is this because they're using the wrong attack type? I'm not weaing any armor so all damage via martial should do more lol 
		3. also they should obviously be attacking using spells! not martial.
		4. further more  my defense is 2 here and they're defense is 19? why? I see that they're weaing cloth armor - okay, so that small jump might make sense. 
		5. I haven't missed any attacks generally - not totally unreasonable but im curious if our assigned percentage is off. 
		6. Overall the combat is good, but the numbers feel off and like they aren't working the same for each other. My defense being 2 should mean im either taking more damage or always able to get hit.
		7. His martial being 21 and mine being 20 should mean that we're doing relatively the same damage depending on the weapon and armor and skills and attack types. 
		8. if they are labelled as a sorcerer they should be using magic and not martial.
		9. despite my martial being so low and his defense being high, my "slash" attack has been "very effective" every single attack, I haven't missed once.  
5. Every location currently is a fight. I'd like to maybe add this to an expansion pack that not all locations ought to be battles. But this will be a large overhaul so put this to the side for now. 
6. Menu reset:
	1. whevnever training, purchasing or selling the following is occuring:
		1. player makes a choice and is automatically removed from the menu back to the main city menu. 
	2. What should occur:
		1. player must be able to make several choices within one menu i.e. buy and item, stay in the same menu, buy another item, and choose to leave when they choose that option only, and not automatically without input. 
	3. Currently I must click the training menu -> click a skill to train -> automatically return to the main city menu -> click training again -> click new skill. 
	4. Instead we should be able to: click training menu -> train skill -> receive flavor text -> hit entre to continue -> train another skill or leave -> if train another skill -> another flavor text -> etc. 
7. Hunting minigame:
	1. what is the current probability of hitting the hunting mini-game? I have yet to see it once. 1
8. I should be able to access character sheet from the road as well as the city. 
9. I should be able to apply bandages from the road as well - not just combat .e.g. I should be able to go into  "gear" or just "inventory" and use items e.g. bandages 
	1. yea I just tried to apply them while in combat and wasn't able to either.
10. Merchant sourcing mechanics:
	1. when entering a city all merchants should have a percentage of "being found", the player should be prompted with "whom are you looking for?"
	2. each merchant type should be given a random percentage of being found for all skills. 
	3. some should always be given 100% chance of being found i.e. librarian, survival dungeoneering, and blacksmit (martial); 
	4. others should be given a percentage between 33% of either being at that city on that day or not. 
	5. if they are available that day; they should stay available until the player leaves and tries to find another city.