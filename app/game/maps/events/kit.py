"""The building kit every event world's areas are made from.

An event world is one map holding several separate places, played one at a
time (app/game/worlds/arena.py), exactly the way Last Light keeps its four.
So every area is drawn in its own local coordinates -- centre at the origin,
ground at y = 0 -- by an :class:`ArenaArea`, which is a Last Light
:class:`~app.game.maps.lastlight.kit.Area` (it shifts each part into the
area's slot on the big map as it is added, and its parts are one contiguous
run of the map's list) with what a team game needs on top:

* **team spawns**, per team and per *stage*, so a world whose front line
  moves (a cart that has passed a depot, a bomb site taken) can move where a
  team comes back with it;
* **spectator cameras**, the shots a dead or eliminated player watches from
  when there is nobody left to follow;
* **switchable solids** -- start gates, falling floors, doors -- that are
  kept out of the static map and switched on and off by the round;
* ``extra``: anything else the rules want to know about the place (a track,
  a list of disguises, the lanes a storm closes along).

The Last Light kit's rules hold here too, because ``tools/mapcheck.py``
audits these maps the same way: one ground plane laid with
:class:`~app.game.maps.lastlight.kit.Surfaces`, solids that abut rather than
overlap, and anything a body can reach is solid.
"""
from __future__ import annotations

import math
import random
from contextlib import contextmanager
from typing import Any, Dict, Iterator, List, Optional, Sequence, Tuple

from ..builder import MapBuilder
from ..lastlight.kit import (  # noqa: F401  (re-exported for the area modules)
    ASPHALT, BRICK, BRICK_DARK, CONCRETE, CONCRETE_DARK, CONCRETE_LIGHT, FLOOR,
    GLASS, HAZARD, LAMP, LINE_WHITE, LINE_YELLOW, PAVEMENT, RUST, STEEL,
    STEEL_DARK, STOREY, WALL_T, WARM, WOOD, WOOD_DARK, WOOD_LIGHT, Area,
    Surfaces, barrier, bench, building, car, carve, chain_fence, crate, crenels,
    deploy_pad, dumpster, face_sign, flight, flood, floodlight, gable, hazard_rim,
    holed_wall, kerb, lamp_post, pallet_stack, plate, rect, room_walls, sandbags,
    sign_decal, slab, solid_fence, step_paint, strip_light, threshold, wall,
    wall_sign)

Rect = Tuple[float, float, float, float]

SPACING = 2600.0           # between areas: nothing draws past 1400
KILL_Y = -80.0
OFFSETS = [(-SPACING, 0.0), (SPACING, 0.0), (0.0, -SPACING), (0.0, SPACING),
           (-SPACING, -SPACING), (SPACING, SPACING), (-SPACING, SPACING),
           (SPACING, -SPACING)]


# ==================================================================== areas
class ArenaArea(Area):
    """One playable place of an event world, drawn at the origin.

    ``half_x`` and ``half_z`` are the playable half-sizes: an area need not
    be square (a race track is long and narrow, a dodgeball court short)."""

    def __init__(self, root: MapBuilder, area_id: str, name: str, ox: float,
                 oz: float, half_x: float, half_z: float, sky: Dict[str, Any],
                 ambient: str, ground: str, fog: float = 760.0):
        super().__init__(root, area_id, name, ox, oz, max(half_x, half_z), sky,
                         ambient, ground, fog=fog)
        self.half_x = float(half_x)
        self.half_z = float(half_z)
        self.spawns: Dict[str, List[Dict[str, Any]]] = {}
        self.cameras: List[Dict[str, Any]] = []
        self.dynamics: Dict[str, Dict[str, Any]] = {}
        self.extra: Dict[str, Any] = {}
        self.gravity = 1.0
        self.void = False          # open sky under the edges (an arena in the air)
        self.kill_y = KILL_Y

    # ------------------------------------------------------------ spawns
    def team_spawn(self, team: str, x: float, y: Optional[float], z: float,
                   yaw: float = 0.0, stage: int = 0) -> None:
        """Where ``team`` comes into the round (``stage`` 0) or comes back
        once the front has moved (1, 2...).  ``y`` None stands it on
        whatever is under it."""
        if y is None:
            y = self.surface(x, z, 60.0)
        self.spawns.setdefault(team, []).append(
            {"p": self.at(x, y, z), "yaw": round(yaw, 3), "stage": int(stage)})

    def spawn_row(self, team: str, x0: float, z0: float, x1: float, z1: float,
                  count: int, y: Optional[float] = None, yaw: float = 0.0,
                  stage: int = 0) -> None:
        for i in range(count):
            f = i / float(max(1, count - 1))
            self.team_spawn(team, x0 + (x1 - x0) * f, y, z0 + (z1 - z0) * f, yaw, stage)

    def camera(self, x: float, y: float, z: float, tx: float, ty: float,
               tz: float) -> None:
        """A shot for spectators with nobody to follow: from (x, y, z),
        looking at (tx, ty, tz)."""
        self.cameras.append({"p": self.at(x, y, z), "t": self.at(tx, ty, tz)})

    # ---------------------------------------------------------- dynamics
    @contextmanager
    def detached(self) -> Iterator[List[Dict[str, Any]]]:
        """Parts added inside this block are kept out of the static map
        (and out of every static collision list) and handed back instead."""
        held = self.parts
        mine: List[Dict[str, Any]] = []
        self.parts = mine
        try:
            yield mine
        finally:
            self.parts = held

    def dynamic(self, key: str, parts: List[Dict[str, Any]], on: bool = True,
                group: str = "") -> None:
        """Register a switchable solid: ``parts`` (from :meth:`detached`) are
        drawn and collide only while it is on."""
        boxes = []
        for part in parts:
            if not part.get("col"):
                continue
            px, py, pz = part["p"]
            sx, sy, sz = part["s"]
            boxes.append([[round(px - sx / 2, 3), round(py - sy / 2, 3), round(pz - sz / 2, 3)],
                          [round(px + sx / 2, 3), round(py + sy / 2, 3), round(pz + sz / 2, 3)]])
        self.dynamics[key] = {"parts": parts, "boxes": boxes, "on": bool(on),
                              "group": group}

    # ----------------------------------------------------------- finish
    def rect_world(self) -> List[float]:
        m = self.margin
        return [self.ox - self.half_x - m, self.ox + self.half_x + m,
                self.oz - self.half_z - m, self.oz + self.half_z + m]

    def finish(self) -> Dict[str, Any]:
        record = super().finish()
        record.update({
            "spawns": self.spawns, "cameras": self.cameras,
            "dynamic": self.dynamics, "extra": self.extra,
            "gravity": self.gravity, "half": [self.half_x, self.half_z],
            "void": self.void, "kill_y": self.kill_y,
        })
        return record


def build_world(title: str, mode: str,
                entries: Sequence[Tuple[str, Any, str]]) -> Dict[str, Any]:
    """Every area of one world on one map, far apart.

    ``entries`` is ``(area id, module, display name)``; each module has
    ``HALF`` (a number, or ``(half_x, half_z)``), ``SKY``, ``AMBIENT``,
    ``GROUND``, ``FOG`` and ``build(area)``."""
    first = entries[0][1]
    root = MapBuilder(title, sky=first.SKY, ambient=first.AMBIENT,
                      fog=getattr(first, "FOG", 700.0), ground=first.GROUND)
    records: List[Dict[str, Any]] = []
    kill_y = KILL_Y
    for index, (area_id, module, name) in enumerate(entries):
        ox, oz = OFFSETS[index]
        half = module.HALF
        hx, hz = (half, half) if isinstance(half, (int, float)) else half
        area = ArenaArea(root, area_id, name, ox, oz, hx, hz, module.SKY,
                         module.AMBIENT, module.GROUND, fog=getattr(module, "FOG", 700.0))
        module.build(area)
        record = area.finish()
        kill_y = min(kill_y, record["kill_y"])
        records.append(record)
    root.marker("mode", mode)
    root.marker("arena", 1)
    root.marker("areas", records)
    root.marker("nav_regions", [r["rect"] for r in records])
    root.kill_y = kill_y
    return root.to_dict()


def area_payload(map_data: Dict[str, Any], area_id: str) -> Dict[str, Any]:
    """The map one client needs while ``area_id`` is being played: that
    area's parts, sky and markers, nothing of the others."""
    markers = map_data["markers"]
    area = next((a for a in markers["areas"] if a["id"] == area_id), markers["areas"][0])
    lo, hi = area["parts"]
    return {
        "name": area["name"],
        "parts": map_data["parts"][lo:hi],
        "spawns": area["spawns"],
        "markers": {"mode": markers.get("mode"), "arena": 1, "area": area["id"],
                    "area_name": area["name"], "area_rect": area["rect"],
                    "centre": area["centre"], "points": area["points"],
                    "landmarks": area["landmarks"], "cameras": area["cameras"],
                    "extra": area["extra"],
                    "dynamic": {k: {"parts": d["parts"], "boxes": d["boxes"],
                                    "on": d["on"], "group": d["group"]}
                                for k, d in area["dynamic"].items()}},
        "sky": area["sky"],
        "ambient": area["ambient"],
        "fog": area["fog"],
        "ground": area["ground"],
        "gravity": area.get("gravity", 1.0),
        "kill_y": area.get("kill_y", map_data["kill_y"]),
    }


# ============================================================ ground + edge
def ground(b: ArenaArea, colour: str, soil: str = "#5a4a38", material: str = "grass",
           holes: Sequence[Rect] = (), studs: bool = True) -> None:
    """Turf over soil out to under the boundary, with ``holes`` left open
    (a lake, a pit) for the area to fill in itself."""
    m = b.margin
    whole = rect(-b.half_x - m, b.half_x + m, -b.half_z - m, b.half_z + m)
    pieces = carve(whole, list(holes)) if holes else [whole]
    plate(b, pieces, 0.0, 0.6, colour, studs=studs, material=material)
    plate(b, pieces, -0.6, 5.4, soil)


def perimeter(b: ArenaArea, height: float, colour: str, cap: str = "",
              rng: Optional[random.Random] = None, ragged: float = 0.0,
              gaps: Sequence[str] = ()) -> None:
    """The edge of the world: a solid wall round the playable rectangle, as
    thick as the margin, with an optional ragged crest on top (cliffs,
    snow, a broken skyline).  ``gaps`` leaves a side open (the sea)."""
    m = b.margin
    hx, hz = b.half_x, b.half_z
    sides = [s for s in ("x-", "x+", "z-", "z+") if s not in gaps]
    room_walls(b, rect(-hx - m, hx + m, -hz - m, hz + m), m, 0.0, height, colour,
               sides=sides)
    if ragged <= 0:
        return
    rng = rng or random.Random(hash(b.id) & 0xFFFF)
    cap = cap or colour
    for side in sides:
        along_x = side in ("z-", "z+")
        span = 2 * (hx if along_x else hz)
        count = max(4, int(span // 26))
        sign = -1 if side.endswith("-") else 1
        for i in range(count):
            u = -span / 2 + (i + 0.5) * span / count
            top = rng.uniform(ragged * 0.35, ragged)
            at = sign * ((hz if along_x else hx) + m / 2.0)
            w = span / count - 1.5
            if along_x:
                b.box([u, height + top / 2.0, at], [w, top, m + 1.0 + (i % 3) * 0.13],
                      cap, collide=False)
            else:
                b.box([at, height + top / 2.0 + 0.011, u], [m + 1.0 + (i % 3) * 0.13, top, w],
                      cap, collide=False)


def backdrop(b: ArenaArea, kind: str, base: float, rng: random.Random,
             colours: Sequence[str] = (), sides: Sequence[str] = ("x-", "x+", "z-", "z+"),
             depth: float = 60.0) -> None:
    """Scenery beyond the wall, out of reach, so the edge of the world is a
    horizon rather than a wall: ``mesas``, ``peaks``, ``pines``, ``city``,
    ``hills`` or ``clouds``.  Nothing here collides."""
    hx, hz = b.half_x + b.margin, b.half_z + b.margin
    palette = list(colours) or ["#5a4a3a", "#6a5844", "#4a3e32"]
    for side in sides:
        along_x = side in ("z-", "z+")
        span = 2 * (hx if along_x else hz)
        sign = -1 if side.endswith("-") else 1
        count = max(5, int(span // 40))
        for i in range(count):
            u = -span / 2 + (i + 0.5) * span / count + rng.uniform(-8, 8)
            d = (hz if along_x else hx) + rng.uniform(depth * 0.3, depth)
            x, z = (u, sign * d) if along_x else (sign * d, u)
            c = rng.choice(palette)
            # every piece stands on its own base height, so two that overlap
            # never share a bottom face
            sink = 3.0 + (i * 7 + len(side)) % 23 * 0.071
            if kind == "mesas":
                h = rng.uniform(30, 90)
                w = rng.uniform(40, 90)
                b.box([x, base - sink + (h + sink) / 2, z], [w, h + sink, w * rng.uniform(0.6, 1.0)],
                      c, collide=False)
                b.box([x, base + h + 2.0, z], [w * 0.92, 4.0, w * 0.6], palette[0], collide=False)
            elif kind == "peaks":
                h = rng.uniform(80, 200)
                w = rng.uniform(90, 160)
                b.cone([x, base + h / 2, z], [w, h, w], c, collide=False)
                b.cone([x, base + h * 0.86, z], [w * 0.3, h * 0.28, w * 0.3], "#f4f6f8",
                       collide=False)
            elif kind == "pines":
                for k in range(3):
                    s = rng.uniform(2.2, 3.6)
                    px, pz = x + rng.uniform(-18, 18), z + rng.uniform(-14, 14)
                    b.cone([px, base + 9 * s, pz], [11 * s, 18 * s, 11 * s], c, collide=False)
            elif kind == "hills":
                w = rng.uniform(90, 180)
                b.sphere([x, base - w * 0.25, z], [w, w * 0.7, w], c, collide=False)
            elif kind == "city":
                h = rng.uniform(40, 160)
                w = rng.uniform(24, 46)
                b.box([x, base - sink + (h + sink) / 2, z], [w, h + sink, w], c, collide=False)
                for k in range(int(h // 14)):
                    if rng.random() < 0.35:
                        face = -sign * (w / 2 + 0.06)
                        wx, wz = (x + rng.uniform(-w / 3, w / 3), z + face) if along_x \
                            else (x + face, z + rng.uniform(-w / 3, w / 3))
                        b.box([wx, base + 8 + k * 14, wz],
                              [3.0 if along_x else 0.12, 2.6, 0.12 if along_x else 3.0],
                              rng.choice(["#ffd27a", "#cfe8ff", "#ffb35a"]),
                              material="neon", collide=False)
            elif kind == "clouds":
                s = rng.uniform(30, 70)
                b.sphere([x, base + rng.uniform(-30, 30), z], [s * 1.8, s * 0.7, s],
                         c, collide=False, alpha=0.85)


def dirt_road(b: MapBuilder, s: Surfaces, x0: float, x1: float, z0: float, z1: float,
              colour: str, top: float = 0.62) -> None:
    """A road or a path laid on the ground plane (carved round what is
    already there, so it never fights with it)."""
    s.lay(rect(x0, x1, z0, z1), top, colour)


def lantern(b: MapBuilder, x: float, y: float, z: float, colour: str = WARM,
            post: float = 0.0) -> None:
    """A hanging lantern or a lamp on a post: the glass is lit, the frame is
    iron, and it is fixed to what it hangs from."""
    if post > 0:
        b.cyl([x, y + post / 2.0, z], [0.6, post, 0.6], STEEL_DARK, material="metal")
        y += post
    b.box([x, y + 0.15, z], [1.4, 0.3, 1.4], STEEL_DARK, collide=False, material="metal")
    b.box([x, y - 0.75, z], [1.0, 1.5, 1.0], colour, collide=False, material="neon")


def ring_points(cx: float, cz: float, radius: float, count: int,
                start: float = 0.0) -> List[Tuple[float, float, float]]:
    """``count`` points round a circle, each with the yaw that faces its
    centre."""
    out = []
    for i in range(count):
        a = start + i * 2 * math.pi / count
        x, z = cx + math.sin(a) * radius, cz + math.cos(a) * radius
        out.append((x, z, math.atan2(cx - x, cz - z)))
    return out
