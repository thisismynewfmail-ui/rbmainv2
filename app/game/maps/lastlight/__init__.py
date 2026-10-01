"""Last Light -- one server, four places to make a stand, and the bunker.

Each area is a complete, walled-in map of its own, built at the origin by
its module and placed far from the others, so no two are ever in sight of
each other (they are 4800 units apart; nothing draws past 1400).  Only one
is played at a time: a round is fought in one until everybody is dead, and
the next round is somewhere else.  The holdout bunker, where people wait
for the next wave, sits on its own at the centre.

The parts of every area live in one list, and each area records the run of
it that is its own (``parts: [start, end]``) so the world can send a client
just the bunker and the area being played.
"""
from __future__ import annotations

from typing import Any, Dict, List

from ..builder import MapBuilder
from . import camp, docks, hospital, lobby, town
from .kit import KILL_Y, Area

SPACING = 2400.0

# id, module, name, offset, ground colour, fog distance
AREAS = [
    ("town", town, "Harrow Main Street", (-SPACING, 0.0), "#4f6b3a", 760.0),
    ("hospital", hospital, "St. Agnes Medical", (SPACING, 0.0), "#3f4a3a", 660.0),
    ("docks", docks, "Blackwater Docks", (0.0, -SPACING), "#3a4248", 560.0),
    ("camp", camp, "Cedar Pines Camp", (0.0, SPACING), "#4f6b34", 740.0),
]
AREA_IDS = [entry[0] for entry in AREAS]


def build() -> Dict[str, Any]:
    root = MapBuilder("Last Light", sky=lobby.SKY, ambient=lobby.AMBIENT,
                      fog=420.0, ground="#3a3f46")
    hold = Area(root, "lobby", "The Holdout", 0.0, 0.0, lobby.HALF, lobby.SKY,
                lobby.AMBIENT, "#3a3f46", fog=420.0)
    lobby.build(hold)
    holdout = hold.finish()

    areas: List[Dict[str, Any]] = []
    for area_id, module, name, (ox, oz), ground, fog in AREAS:
        area = Area(root, area_id, name, ox, oz, module.HALF, module.SKY,
                    module.AMBIENT, ground, fog=fog)
        module.build(area)
        areas.append(area.finish())

    for point in holdout["safe"]:
        root.spawn("survivors", point["p"][0], point["p"][1], point["p"][2],
                   point["yaw"])
    root.marker("mode", "survival")
    root.marker("lobby", holdout)
    root.marker("areas", areas)
    root.marker("nav_regions", [holdout["rect"]] + [a["rect"] for a in areas])
    root.kill_y = KILL_Y
    return root.to_dict()


def area_payload(map_data: Dict[str, Any], area_id: str) -> Dict[str, Any]:
    """The map one client needs while ``area_id`` is being played: the
    bunker's parts and that area's, and that area's sky."""
    markers = map_data["markers"]
    holdout = markers["lobby"]
    area = next((a for a in markers["areas"] if a["id"] == area_id),
                markers["areas"][0])
    parts = map_data["parts"]
    chosen = parts[holdout["parts"][0]:holdout["parts"][1]] + \
        parts[area["parts"][0]:area["parts"][1]]
    return {
        "name": "Last Light - %s" % area["name"],
        "parts": chosen,
        "spawns": map_data["spawns"],
        "markers": {"mode": "survival", "area": area["id"],
                    "area_name": area["name"], "lobby_rect": holdout["rect"],
                    "area_rect": area["rect"], "lure": area.get("lure")},
        "sky": area["sky"],
        "ambient": area["ambient"],
        "fog": area["fog"],
        "ground": area["ground"],
        "kill_y": map_data["kill_y"],
    }
