"""Plunder Bay -- a treasure haul between two pirate crews, on twelve islands.

Each area is an island with a crew's galleon moored off each end
(app/game/maps/events/plunder_bay/common.py): the ``hold`` mark on each
ship's deck is where treasure is carried in, ``dig`` marks are where X
marks the spot, ``loot`` marks where loose treasure turns up, and ``idol``
the cursed idol's altar.  Each place's twist is in ``extra["twist"]`` with
its own marks: the tide's ``sunken`` treasure, the kraken's ``tentacle``
spots, the redcoats' (and the ghosts') ``patrol`` routes, the eruption's
``rain`` (and the volcano's crater, ``extra["vent"]``, where it is thrown
out of), the maelstrom's ``rim``, the geysers' ``geyser`` marks.  A place
can dress a twist for itself (``extra["style"]``, ``extra["twist_text"]``):
the Company's marines for redcoats, a frost kraken, a fireworks barge for
the volcano.
"""
from __future__ import annotations

from typing import Any, Dict

from ..kit import build_world
from . import (doubloon, frostfang, ghostfleet, glowtide, jollyroger, monsoon, reef, royale, skullcove,
               sulphur, thunderhead, whalebone)

AREAS = [
    ("skullcove", skullcove, "Skull Cove"),
    ("reef", reef, "Coral Reef"),
    ("royale", royale, "Port Royale"),
    ("doubloon", doubloon, "Doubloon Isle"),
    ("whalebone", whalebone, "Whalebone Atoll"),
    ("thunderhead", thunderhead, "Thunderhead Rock"),
    ("sulphur", sulphur, "Sulphur Springs"),
    ("ghostfleet", ghostfleet, "Ghost Fleet Cove"),
    ("glowtide", glowtide, "Glowtide Lagoon"),
    ("frostfang", frostfang, "Frostfang Floe"),
    ("monsoon", monsoon, "Monsoon Bazaar"),
    ("jollyroger", jollyroger, "Jolly Roger Fair"),
]


def build() -> Dict[str, Any]:
    return build_world("Plunder Bay", "treasure_haul", AREAS)
