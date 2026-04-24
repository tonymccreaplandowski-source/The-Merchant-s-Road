"""
Road flavor text — biome-aware, phase-aware lines shown during travel.
"""

import random

ROAD_FLAVOR = {
    "forest": {
        "early": [
            "The canopy closes overhead. The city is already out of sight.",
            "Birdsong fills the air. The road ahead is clear — for now.",
            "You pass a milestone half-buried in moss. The name has worn away.",
            "A deer watches you from the treeline, then vanishes without sound.",
            "The forest smells of rain and old wood. Your boots find soft earth.",
        ],
        "late": [
            "The trees thin ahead. You can feel the journey nearing its end.",
            "The road widens slightly — a sign that civilisation is close.",
            "Through the branches you catch a glimpse of smoke on the horizon.",
            "Your legs carry old aches now. The destination keeps you moving.",
            "The forest releases you slowly, tree by tree, into the open.",
        ],
    },
    "desert": {
        "early": [
            "The heat settles over you like a second coat. You're glad you packed water.",
            "The road turns to packed sand. Your shadow stretches long behind you.",
            "Dust rises with every step. The horizon shimmers in the heat.",
            "A vulture circles high overhead. It is patient. You intend to disappoint it.",
            "The city fades behind you into pale haze. The desert offers no shelter.",
        ],
        "late": [
            "The sand gives way to grit and gravel. You're nearly through.",
            "You can smell the settlement before you see it — cookfires and animals.",
            "The heat relents slightly. Walls appear in the distance.",
            "The road hardens underfoot. Other travellers have worn this path deep.",
            "You count the remaining distance in steps now, not miles.",
        ],
    },
    "mountain": {
        "early": [
            "The path climbs sharply. The air thins and cools with every hundred feet.",
            "Wind cuts across the ridge with no warning. You pull your coat tighter.",
            "Loose stone skitters down the slope below you. You watch your footing.",
            "The road narrows to a ledge between rock and sky. No room for mistakes.",
            "Cloud shadow moves across the peak above. The mountain seems indifferent.",
        ],
        "late": [
            "The descent begins. Easier on the lungs, harder on the knees.",
            "Smoke from hearth fires drifts up from the valley below.",
            "The mountain releases its grip on the road. Easier ground ahead.",
            "You can hear the settlement now — iron on iron, voices carrying on the wind.",
            "The worst of the climb is behind you. The path evens out.",
        ],
    },
    "cave": {
        "early": [
            "The road dips into shadow. Even outdoors here feels dim and enclosed.",
            "The ground is damp. Water drips somewhere in the dark nearby.",
            "The air carries a mineral chill that the sun doesn't quite reach.",
            "Formations of rock rise on either side, old and indifferent.",
            "Your torch casts long shadows. The road feels narrower than it is.",
        ],
        "late": [
            "Daylight appears in the distance. You've been counting on it.",
            "The air warms slightly. You're nearly out of the dark.",
            "The dripping fades behind you. Dry ground ahead.",
            "The road rises toward open sky. You pick up the pace without meaning to.",
            "One last stretch of shadow, then the open road returns.",
        ],
    },
}

_FLAVOR_DEFAULT = {
    "early": [
        "The road stretches out ahead. You press on.",
        "Miles pass beneath your feet. The world is quiet.",
        "You walk. The road asks nothing more of you yet.",
    ],
    "late": [
        "The destination is close. You can feel it.",
        "Not far now. The road has earned its end.",
        "The last miles are always the longest.",
    ],
}


def road_flavor_line(biome: str, step: int, total: int) -> str:
    """Return a random biome-aware, phase-aware flavor line for the current road step."""
    pool  = ROAD_FLAVOR.get(biome, _FLAVOR_DEFAULT)
    phase = "early" if total == 0 or step < total // 2 else "late"
    lines = pool.get(phase, _FLAVOR_DEFAULT[phase])
    return random.choice(lines)
