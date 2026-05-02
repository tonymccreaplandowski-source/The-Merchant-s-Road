---
type: play-test
version: v2.4
status: archived
systems:
  - merchant
  - negotiate
---

1. Truncation? 
	"  [5]  Adventurer's Map  57gp  ✗  A hand-drawn map of nearby roads. Increases chance.."
	- cuts off. 
2. Character sheet does not reflect class - I picked mage and currently says "envoy"
3. break down in logic:
	1. ``` 
	    » [Target slowed — enemy loses next attack]
  » Goblin Scrapper retaliates with Shove for 3 damage.
	   ```
		2. code says enemy loses attack but then retaliates?
		3. also this message wrote out again despite moving through on to the next menu which did not need to occur:
			1. I attacked
			2. message wrote out (good)
			3. I then chose to attack again, opened the spell menu and message wrote again (not good)
			4. i.e. if the message is the same, we don't need to write out again, if it is a different message then we can write out. 
4. "  You press on through the desert toward Dar-Nakhil." - this message should be replaced with the flavor messages during travel, not written at the bottom of the screen and the passed on so quickly that I can't read them.