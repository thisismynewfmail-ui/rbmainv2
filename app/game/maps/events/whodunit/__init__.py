"""Whodunit -- a murder mystery in four grand old places.

Every area is a building full of rooms (and the grounds round it), with the
marks the rules and the bots use: ``clue`` spots, ``roam`` points in the
middle of each room, the guests' ``start`` spawns, and room names with a
height, so the case file can say where the murderer was seen.  Each area's
``extra["twist"]`` is what that place throws at the guests (see
app/game/worlds/whodunit.py).
"""
from __future__ import annotations

from typing import Any, Dict

from ..kit import build_world
from . import express, hotel, liner, manor

AREAS = [
    ("manor", manor, "Blackwood Manor"),
    ("express", express, "The Midnight Express"),
    ("hotel", hotel, "The Grand Meridian"),
    ("liner", liner, "The SS Aurora"),
]


def build() -> Dict[str, Any]:
    data = build_world("Whodunit", "murder_mystery", AREAS)
    # the places are all doors a little wider than a guest and stairs with a
    # rail either side: the bots' graph needs a finer grid to find them
    data.setdefault("markers", {})["nav_spacing"] = 2.0
    return data
