"""Sky Sprint -- an obstacle-course race in four places in the sky.

Each area is one course (app/game/maps/events/sky_sprint/common.py): a
start deck with a gate for each team, checkpoints (``cp`` marks, in order,
the last one the finish), the line the bots run (``route`` marks), jump
pads, speed strips and power-up spots as marks, and everything that moves
-- belts, sweepers, hammers, lasers, wind, blinking and crumbling tiles --
described in ``extra`` for app/game/worlds/sky_sprint.py and the client.
"""
from __future__ import annotations

from typing import Any, Dict

from ..kit import build_world
from . import candy, foundry, jade, neon

AREAS = [
    ("foundry", foundry, "The Foundry"),
    ("candy", candy, "Candy Clouds"),
    ("neon", neon, "Neon Grid"),
    ("jade", jade, "Jade Temple"),
]


def build() -> Dict[str, Any]:
    return build_world("Sky Sprint", "obby_race", AREAS)
