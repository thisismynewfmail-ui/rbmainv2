"""Plunder Bay -- a treasure haul between two pirate crews, in four places.

Each area is an island with a crew's galleon moored off each end
(app/game/maps/events/plunder_bay/common.py): the ``hold`` mark on each
ship's deck is where treasure is carried in, ``dig`` marks are where X
marks the spot, ``loot`` marks where loose treasure turns up, and ``idol``
the cursed idol's altar.  Each place's twist is in ``extra["twist"]`` with
its own marks: the tide's ``sunken`` treasure, the kraken's ``tentacle``
spots, the redcoats' ``patrol`` routes, the eruption's ``rain`` (and the
volcano's crater, ``extra["vent"]``, where it is thrown out of).
"""
from __future__ import annotations

from typing import Any, Dict

from ..kit import build_world
from . import doubloon, reef, royale, skullcove

AREAS = [
    ("skullcove", skullcove, "Skull Cove"),
    ("reef", reef, "Coral Reef"),
    ("royale", royale, "Port Royale"),
    ("doubloon", doubloon, "Doubloon Isle"),
]


def build() -> Dict[str, Any]:
    return build_world("Plunder Bay", "treasure_haul", AREAS)
