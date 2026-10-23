"""Rail Rivals -- four frontier lines, two rival companies, one gold race.

Each area is a complete railroad of its own: two tracks from the west end
to the east end that cross in the middle (see rails.py), with the starting
yards, the depots, the brake levers, the coal and the terminus on each.
"""
from __future__ import annotations

from typing import Any, Dict

from ..kit import build_world
from . import dustbowl, lantern, redrock, silverpine

AREAS = [
    ("dustbowl", dustbowl, "Dustbowl Gulch"),
    ("silverpine", silverpine, "Silverpine Pass"),
    ("redrock", redrock, "Redrock Mesa"),
    ("lantern", lantern, "Lantern Deep"),
]


def build() -> Dict[str, Any]:
    return build_world("Rail Rivals", "payload_race", AREAS)
