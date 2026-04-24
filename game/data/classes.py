"""
Character class definitions — name, dominant skills, and lore lines.
"""

CLASS_CHOICES = [
    {
        "name":    "Mage",
        "skills":  ["Magic", "Speechcraft"],
        "lore":    [
            "The words come first. The fire follows.",
            "You studied in a place that no longer has a name. What you learned there cannot be untaught.",
        ],
    },
    {
        "name":    "Warrior",
        "skills":  ["Martial", "Survival"],
        "lore":    [
            "The road is not a place. It is a condition.",
            "You have buried three travelling companions. You are still walking.",
        ],
    },
    {
        "name":    "Knight",
        "skills":  ["Martial", "Speechcraft"],
        "lore":    [
            "A blade opens doors. A word keeps them open.",
            "You once served a lord whose name is no longer spoken in the right company.",
        ],
    },
    {
        "name":    "Adventurer",
        "skills":  ["Martial", "Dungeoneering"],
        "lore":    [
            "There is always another door below the last one.",
            "You carry the marks of three separate cave-ins and have never once considered turning back.",
        ],
    },
    {
        "name":    "Battlemage",
        "skills":  ["Martial", "Magic"],
        "lore":    [
            "Steel breaks. The arcane does not. You wield both.",
            "The scar on your casting hand is from the first time you tried to hold a sword and a spell at once. You got better.",
        ],
    },
    {
        "name":    "Bard",
        "skills":  ["Merchantilism", "Survival"],
        "lore":    [
            "Every city has a price. Every secret has a song.",
            "You have been asked to leave fourteen establishments. You consider this a reasonable average.",
        ],
    },
    {
        "name":    "Assassin",
        "skills":  ["Martial", "Stealth"],
        "lore":    [
            "The target never knew your name. That was the point.",
            "You do not remember your first contract. You remember the second — it was harder to walk away from.",
        ],
    },
    {
        "name":    "Ranger",
        "skills":  ["Stealth", "Survival"],
        "lore":    [
            "The forest does not hide from you. You have simply learned its language.",
            "You spent three winters alone in the mountain passes. The quiet still feels like home.",
        ],
    },
    {
        "name":    "Smuggler",
        "skills":  ["Stealth", "Merchantilism"],
        "lore":    [
            "The best goods are the ones that don't appear on any manifest.",
            "You know every guard rotation on the Merchant's Road. Some of them know you back.",
        ],
    },
    {
        "name":    "Scholar",
        "skills":  ["Magic", "Dungeoneering"],
        "lore":    [
            "Knowledge does not wait to be found. It hides, specifically, from the unworthy.",
            "The texts you carry are not permitted in three of the five cities. You have memorised the routes.",
        ],
    },
    {
        "name":    "Merchant",
        "skills":  ["Merchantilism", "Speechcraft"],
        "lore":    [
            "The road is long. Profit is longer.",
            "You have survived ambush, drought, plague season, and a bad deal in Ashenvale. The road has not broken you yet.",
        ],
    },
    {
        "name":    "Pathfinder",
        "skills":  ["Survival", "Dungeoneering"],
        "lore":    [
            "You go first. That is the arrangement.",
            "There is no map for where you have been. You stopped needing maps a long time ago.",
        ],
    },
    {
        "name":    "Alchemist",
        "skills":  ["Magic", "Merchantilism"],
        "lore":    [
            "Everything has a formula. Everything has a price. These are not separate observations.",
            "The reagents in your pack are worth more than most men earn in a season — and considerably more dangerous.",
        ],
    },
    {
        "name":    "Infiltrator",
        "skills":  ["Stealth", "Speechcraft"],
        "lore":    [
            "You were in the room. No one saw you leave.",
            "You have worn seven names on this road. Only one of them is yours, and you do not use it lightly.",
        ],
    },
    {
        "name":    "Mercenary",
        "skills":  ["Martial", "Merchantilism"],
        "lore":    [
            "The cause changes. The coin does not.",
            "You have fought under four banners. None of them are flying anymore.",
        ],
    },
    {
        "name":    "Hexblade",
        "skills":  ["Stealth", "Magic"],
        "lore":    [
            "The dark is not a hiding place. It is a weapon.",
            "You learned your spells from a source you do not name in polite company. It has not asked for payment yet.",
        ],
    },
    {
        "name":    "Delver",
        "skills":  ["Stealth", "Dungeoneering"],
        "lore":    [
            "Every ruin has a way in. You have yet to find one that doesn't.",
            "You move through buried places like you were made for them. Some days it feels that way.",
        ],
    },
    {
        "name":    "Shaman",
        "skills":  ["Survival", "Magic"],
        "lore":    [
            "The land speaks. You have learned to stop interrupting.",
            "You carry no grimoire. The forest remembers what books forget.",
        ],
    },
    {
        "name":    "Wayfarer",
        "skills":  ["Survival", "Speechcraft"],
        "lore":    [
            "You have walked every road on this map and a few that aren't on it.",
            "People open doors for you. You have never been entirely sure why, and you have never stopped to ask.",
        ],
    },
    {
        "name":    "Chronicler",
        "skills":  ["Speechcraft", "Dungeoneering"],
        "lore":    [
            "Everything that was buried was buried for a reason. You write it down anyway.",
            "Three cities have tried to confiscate your notes. You still have them.",
        ],
    },
    {
        "name":    "Prospector",
        "skills":  ["Merchantilism", "Dungeoneering"],
        "lore":    [
            "There is no ruin too deep if the price is right.",
            "You can assess the value of a tomb before you've opened it. You've been wrong twice.",
        ],
    },
]
