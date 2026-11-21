"""Blackout Relay's maps: Ironvale and the places the server rotates to.

The world was one map -- Ironvale Relay -- and is now a rotation: when a
round ends the server rolls one of the others at random and everybody goes
there for the next, with that map's own arrival sequence.  Every map plays
by the same rules (a relay in the middle that both teams deploy from, a
flag at each end, outposts to fall back to) and every one is its own place.

All of them live on one map, far apart, and a client is only ever sent the
one being played (the parts each area adds are one contiguous run of the
map's list).  Ironvale stays where it always was, at the origin; the others
sit on the z axis either side of it, so the line every map is mirrored
about is the world's own x = 0 -- which is what lets ``tools/mapcheck.py``
hold the whole rotation to the mirror at once.
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

from .. import ironvale
from ..builder import MapBuilder
from . import kit

# Red is blue turned round, on every map (tools/mapcheck.py checks it).
MIRROR_AXIS = "x"

SPACING = 1600.0

# id, module, name -- in the order the world page shows them.  Ironvale is
# built by its own module (app/game/maps/ironvale.py) and stays at the origin.
AREAS: List[Tuple[str, Any, str]] = [
    ("ironvale", None, "Ironvale Relay"),
]

IRONVALE_INTRO = [
    "Ironvale Relay -- deploy from the Relay, run the flag home.",
    "Lose your own flag and your team falls back to the bunkers, right across "
    "the carrier's way out.",
    "There is a hatch behind every keep. The tunnels come out inside all four bunkers.",
]


def _load() -> None:
    """Import the area modules (late, so a broken one names itself)."""
    import importlib
    from .areas import ORDER
    del AREAS[1:]
    for area_id, name in ORDER:
        module = importlib.import_module("%s.%s" % (__name__, area_id))
        AREAS.append((area_id, module, name))


def offset(index: int) -> float:
    """Where the ``index``-th new map sits on the z axis (0 is Ironvale)."""
    if index <= 0:
        return 0.0
    k = (index + 1) // 2
    return SPACING * k * (1 if index % 2 else -1)


def _ironvale(root: MapBuilder) -> Dict[str, Any]:
    data = ironvale.build()
    start = len(root.parts)
    root.parts.extend(data["parts"])
    markers = {k: v for k, v in data["markers"].items()}
    markers["captures_to_win"] = int(markers.get("captures_to_win", 5))
    markers["round_seconds"] = 1800.0
    markers["intro"] = list(IRONVALE_INTRO)
    probes = []
    for key in ("flag_red", "flag_blue"):
        probes.append({"p": markers[key]["p"], "label": key})
    for key in ("muster_red", "muster_blue", "outpost_red", "outpost_blue"):
        probes += [{"p": e["p"], "label": key} for e in markers.get(key) or []]
    mx, mz = ironvale.MAP_X, ironvale.MAP_Z
    return {
        "id": "ironvale", "name": "Ironvale Relay", "sky": data["sky"],
        "ambient": data["ambient"], "fog": data["fog"], "ground": data["ground"],
        "rect": [-mx, mx, -mz, mz], "centre": [0.0, 0.0, 0.0],
        "parts": [start, len(root.parts)], "spawns": data["spawns"],
        "markers": markers, "landmarks": [], "cameras": [], "points": {},
        "kill_y": data["kill_y"], "probes": probes, "dynamic": {},
        "extra": {"accent": "#ff9a5a"},
        "half": [mx, mz],
    }


def build() -> Dict[str, Any]:
    _load()
    root = MapBuilder("Blackout Relay")
    records = [_ironvale(root)]
    first = records[0]
    root.sky, root.ambient, root.fog, root.ground = (first["sky"], first["ambient"],
                                                     first["fog"], first["ground"])
    kill_y = first["kill_y"]
    for index, (area_id, module, name) in enumerate(AREAS[1:], 1):
        half = module.HALF
        hx, hz = (half, half) if isinstance(half, (int, float)) else half
        area = kit.RelayArea(root, area_id, name, 0.0, offset(index), hx, hz, module.SKY,
                             module.AMBIENT, module.GROUND, fog=getattr(module, "FOG", 800.0))
        module.build(area)
        record = area.finish()
        kill_y = min(kill_y, record["kill_y"])
        records.append(record)
    root.spawns = dict(first["spawns"])
    for key in ("flag_red", "flag_blue"):
        root.marker(key, first["markers"][key])
    root.marker("mode", "ctf")
    root.marker("areas", records)
    root.marker("nav_regions", [r["rect"] for r in records])
    root.kill_y = kill_y
    return root.to_dict()


def area_payload(map_data: Dict[str, Any], area_id: str) -> Dict[str, Any]:
    """The map one client is sent while ``area_id`` is being played: that
    area's parts, sky and markers, nothing of the others."""
    areas = map_data["markers"]["areas"]
    area = next((a for a in areas if a["id"] == area_id), areas[0])
    lo, hi = area["parts"]
    markers = dict(area["markers"])
    markers.update({"area": area["id"], "area_name": area["name"],
                    "area_rect": area["rect"], "centre": area["centre"],
                    "landmarks": area.get("landmarks") or [],
                    "cameras": area.get("cameras") or [],
                    "extra": area.get("extra") or {}})
    return {
        "name": area["name"],
        "parts": map_data["parts"][lo:hi],
        "spawns": area["spawns"],
        "markers": markers,
        "sky": area["sky"],
        "ambient": area["ambient"],
        "fog": area["fog"],
        "ground": area["ground"],
        "kill_y": area.get("kill_y", map_data.get("kill_y", -80.0)),
    }
