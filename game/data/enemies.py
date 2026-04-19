"""
Enemy definitions.
Stats are randomized on spawn within defined ranges — no two enemies are identical.

Armor types affect combat move effectiveness:
  none    — all moves effective
  cloth   — Slash effective, Bash okay, Pierce weak
  leather — Pierce effective, Slash okay, Bash okay
  mail    — Bash effective, Pierce okay, Slash weak
"""

import random
from dataclasses import dataclass, field
from typing import List


@dataclass
class Enemy:
    name: str
    armor_type: str
    hp: int
    max_hp: int
    combat_skill: int
    defense_skill: int
    agility: int
    description: str
    biomes: List[str]
    loot_bias: str

    def is_alive(self) -> bool:
        return self.hp > 0

    def take_damage(self, amount: int):
        self.hp = max(0, self.hp - amount)


ENEMY_TEMPLATES = [
    {
        "name":           "Goblin Scrapper",
        "armor_type":     "cloth",
        "hp_range":       (20, 40),
        "combat_range":   (10, 28),
        "defense_range":  (5,  18),
        "agility_range":  (30, 55),
        "description":    "A small, wiry goblin with a rusty blade and bad intentions.",
        "biomes":         ["forest", "desert", "mountain"],
        "loot_bias":      "common",
    },
    {
        "name":           "Road Bandit",
        "armor_type":     "leather",
        "hp_range":       (35, 60),
        "combat_range":   (22, 45),
        "defense_range":  (18, 35),
        "agility_range":  (20, 40),
        "description":    "A desperate traveller turned criminal. Dangerous but beatable.",
        "biomes":         ["forest", "desert"],
        "loot_bias":      "common",
    },
    {
        "name":           "Forest Wolf",
        "armor_type":     "none",
        "hp_range":       (25, 45),
        "combat_range":   (25, 42),
        "defense_range":  (8,  22),
        "agility_range":  (50, 75),
        "description":    "A lean grey wolf hunting alone. Fast and relentless.",
        "biomes":         ["forest"],
        "loot_bias":      "uncommon",
    },
    {
        "name":           "Sand Scorpion",
        "armor_type":     "mail",
        "hp_range":       (30, 55),
        "combat_range":   (18, 38),
        "defense_range":  (30, 50),
        "agility_range":  (15, 30),
        "description":    "An armoured desert predator. Its shell deflects most blades.",
        "biomes":         ["desert"],
        "loot_bias":      "uncommon",
    },
    {
        "name":           "Mountain Troll",
        "armor_type":     "mail",
        "hp_range":       (60, 100),
        "combat_range":   (35, 60),
        "defense_range":  (35, 55),
        "agility_range":  (5,  20),
        "description":    "A hulking brute with skin like stone. Slow, but devastating.",
        "biomes":         ["mountain"],
        "loot_bias":      "rare",
    },
    {
        "name":           "Cave Spider",
        "armor_type":     "cloth",
        "hp_range":       (20, 38),
        "combat_range":   (20, 35),
        "defense_range":  (8,  20),
        "agility_range":  (55, 80),
        "description":    "A large spider that drops from cave ceilings without warning.",
        "biomes":         ["cave"],
        "loot_bias":      "uncommon",
    },
    {
        "name":           "Skeleton Warrior",
        "armor_type":     "mail",
        "hp_range":       (40, 65),
        "combat_range":   (28, 50),
        "defense_range":  (25, 45),
        "agility_range":  (10, 28),
        "description":    "Animated bones clutching an ancient weapon. No fear. No mercy.",
        "biomes":         ["cave", "castle"],
        "loot_bias":      "rare",
    },
    {
        "name":           "Wild Boar",
        "armor_type":     "leather",
        "hp_range":       (35, 60),
        "combat_range":   (20, 38),
        "defense_range":  (12, 25),
        "agility_range":  (35, 55),
        "description":    "A bristled boar with tusks like daggers. It charges without hesitation.",
        "biomes":         ["forest", "mountain"],
        "loot_bias":      "uncommon",
    },
    {
        "name":           "Highwayman",
        "armor_type":     "leather",
        "hp_range":       (40, 65),
        "combat_range":   (28, 48),
        "defense_range":  (20, 38),
        "agility_range":  (25, 45),
        "description":    "A masked brigand who preys on lone travellers. Cocky until cornered.",
        "biomes":         ["desert", "mountain"],
        "loot_bias":      "uncommon",
    },
    {
        "name":           "Bandit Cutthroat",
        "armor_type":     "none",
        "hp_range":       (28, 48),
        "combat_range":   (30, 52),
        "defense_range":  (8,  20),
        "agility_range":  (40, 62),
        "description":    "Fast and vicious. Light armour, heavy intent.",
        "biomes":         ["forest", "desert", "mountain"],
        "loot_bias":      "common",
    },
    {
        "name":           "Castle Guard",
        "armor_type":     "mail",
        "hp_range":       (50, 80),
        "combat_range":   (32, 55),
        "defense_range":  (30, 50),
        "agility_range":  (10, 25),
        "description":    "A guard long abandoned by their lord. Still holding their post out of habit.",
        "biomes":         ["castle"],
        "loot_bias":      "rare",
    },
]


def spawn_enemy(template: dict) -> Enemy:
    hp = random.randint(*template["hp_range"])
    return Enemy(
        name=template["name"],
        armor_type=template["armor_type"],
        hp=hp,
        max_hp=hp,
        combat_skill=random.randint(*template["combat_range"]),
        defense_skill=random.randint(*template["defense_range"]),
        agility=random.randint(*template["agility_range"]),
        description=template["description"],
        biomes=list(template["biomes"]),
        loot_bias=template["loot_bias"],
    )


def get_enemy_for_biome(biome: str) -> Enemy:
    valid = [t for t in ENEMY_TEMPLATES if biome in t["biomes"]]
    if not valid:
        valid = ENEMY_TEMPLATES
    return spawn_enemy(random.choice(valid))
