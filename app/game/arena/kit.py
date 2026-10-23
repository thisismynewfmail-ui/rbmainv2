"""The building kit every arena place is made from.

An arena world is one map holding four (or more) separate places, exactly
the way Last Light holds its areas: each place is drawn in its own local
coordinates by an :class:`ArenaArea` (centre at the origin, ground at y = 0)
which shifts every part into the place's slot on the big map as it is added,
and the parts a place adds are one contiguous run of the map's part list, so
a game host can send a client the one place being played and nothing else.

On top of the Last Light kit (which this re-exports, so a place module needs
one import) an arena place has:

* **spawn rooms per team** (or per role) -- ``spawn_room`` lays the painted
  pads and records the points; ``finish`` also lists them all as ``safe`` so
  ``tools/mapcheck.py`` checks every pad and routes from the first one to
  everything else in the place;
* **named points** of any kind (``mark``) for pickups, dig sites, vaults,
  levers, computers, turret pads... -- checked the same way;
* **data** -- whatever else the world's rules need from the geometry: a
  cart's track, paintable floors, a storm's centre -- stored with the place
  in world coordinates.

The rules of the Last Light kit hold here too: one ground plane, surfaces
laid through :class:`Surfaces` so no two covers overlap, solids that abut
rather than overlap, and anything a body can reach is solid.
"""
from __future__ import annotations

import math
import random
from typing import Any, Dict, List, Optional, Sequence, Tuple

from ..maps.builder import MapBuilder
from ..maps.lastlight.kit import (  # noqa: F401  (re-exported for the place modules)
    ASPHALT, ASPHALT_DARK, BLOOD, BRICK, BRICK_DARK, COLD, CONCRETE,
    CONCRETE_DARK, CONCRETE_LIGHT, CONTAINER_COLOURS, CONTAINER_H, FLOOR, GLASS,
    HAZARD, LAMP, LINE_WHITE, LINE_YELLOW, PAVEMENT, PAVEMENT_DARK, RUST,
    SANDBAG, STEEL, STEEL_DARK, STOREY, WALL_T, WARM, WOOD, WOOD_DARK,
    WOOD_LIGHT, Area, Surfaces, army_truck, barrel_prop, barrier, bench,
    boat, bollard, boundary, building, bus, car, carve, chain_fence,
    container, crate, crenels, deploy_pad, dumpster, face_sign, flight,
    flood, floodlight, gable, ground, hazard_rim, hesco, holed_wall, house,
    kerb, lamp_post, pallet_stack, plate, rect, room_walls, sandbags,
    sign_decal, skyline, slab, solid_fence, step_paint, strip_light, tent,
    threshold, treeline, van, wall, wall_sign, watchtower)

Rect = Tuple[float, float, float, float]

SPACING = 2400.0          # places sit this far apart on the big map
KILL_Y = -80.0
# where each place goes on the big map, in order; nothing is drawn past
# 1400 units, so no place is ever in sight of another
SLOTS = [(-SPACING, 0.0), (SPACING, 0.0), (0.0, -SPACING), (0.0, SPACING),
         (-SPACING, -SPACING), (SPACING, SPACING)]


# ==================================================================== places
class ArenaArea(Area):
    """One place of an arena world: a Last Light area with team spawn rooms,
    named points and per-place data."""

    def __init__(self, root: MapBuilder, area_id: str, name: str,
                 ox: float, oz: float, half: float, sky: Dict[str, Any],
                 ambient: str, ground_colour: str, fog: float = 760.0):
        super().__init__(root, area_id, name, ox, oz, half, sky, ambient,
                         ground_colour, fog=fog)
        self.spawns: Dict[str, List[Dict[str, Any]]] = {}
        self.data: Dict[str, Any] = {}
        self.shot: Dict[str, Any] = {}

    # ----------------------------------------------------------- spawning
    def team_spawn(self, team: str, x: float, y: float, z: float,
                   yaw: float = 0.0) -> None:
        self.spawns.setdefault(team, []).append(
            {"p": self.at(x, y, z), "yaw": round(yaw, 3)})

    def spawn_room(self, team: str, cx: float, cz: float, cols: int, rows: int,
                   spacing: float = 8.0, y: float = 0.0, yaw: float = 0.0,
                   pad: str = "", pad_size: float = 5.0) -> None:
        """A grid of deploy pads, ``cols`` along x and ``rows`` along z, all
        facing ``yaw``.  ``pad`` paints them (blank: points only)."""
        for r in range(rows):
            for c in range(cols):
                x = cx + (c - (cols - 1) / 2.0) * spacing
                z = cz + (r - (rows - 1) / 2.0) * spacing
                if pad:
                    deploy_pad(self, x, z, y, pad, pad_size)
                self.team_spawn(team, x, y + 0.6, z, yaw)

    def spawn_ring(self, team: str, cx: float, cz: float, radius: float,
                   count: int, y: float = 0.0, face_in: bool = True) -> None:
        """Spawn points round a circle, each facing the middle (or out)."""
        for k in range(count):
            a = 2 * math.pi * k / count
            x, z = cx + math.sin(a) * radius, cz + math.cos(a) * radius
            yaw = math.atan2(cx - x, cz - z) if face_in else math.atan2(x - cx, z - cz)
            self.team_spawn(team, x, y + 0.6, z, yaw)

    # -------------------------------------------------------------- data
    def path(self, key: str, points: Sequence[Sequence[float]]) -> None:
        """A polyline in world coordinates under ``data[key]`` (a track,
        a road, a march route)."""
        self.data[key] = [self.at(p[0], p[1], p[2]) if len(p) == 3
                          else self.at(p[0], 0.0, p[1]) for p in points]

    def zone(self, key: str, x0: float, x1: float, z0: float, z1: float,
             y: float = 0.0, **extra: Any) -> None:
        """A rectangle in world coordinates, kept in ``data[key]`` (a list)."""
        entry = {"r": [round(x0 + self.ox, 2), round(x1 + self.ox, 2),
                       round(z0 + self.oz, 2), round(z1 + self.oz, 2)], "y": y}
        entry.update(extra)
        self.data.setdefault(key, []).append(entry)

    def thumb(self, eye: Sequence[float], look: Sequence[float], fov: float = 44.0,
              figures: Sequence[Sequence[Any]] = (), props: Sequence[Dict[str, Any]] = (),
              sky: Optional[Dict[str, Any]] = None) -> None:
        """The place's picture for the world page (``app/game/arena/thumbs.py``
        renders it from the real geometry): a camera, and the players posed
        in it -- ``(x, y, z, yaw, pose, holding)`` in local coordinates, all
        in the classic yellow, red and blue -- plus any props staged for the
        shot (a wave, a meteor, a dropped bag) in local coordinates."""
        self.shot = shot_spec(self, eye, look, fov, figures, props, sky)

    def finish(self) -> Dict[str, Any]:
        out = super().finish()
        out["thumb"] = self.shot
        out["spawns"] = self.spawns
        # every pad, for the mapcheck probes and its route check: the first
        # one is where the routes start, so every team's room has to join up
        out["safe"] = [s for team in sorted(self.spawns) for s in self.spawns[team]]
        out["data"] = self.data
        return out


def shot_spec(area: "ArenaArea", eye: Sequence[float], look: Sequence[float], fov: float,
              figures: Sequence[Sequence[Any]], props: Sequence[Dict[str, Any]],
              sky: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    out: Dict[str, Any] = {"eye": area.at(*eye), "look": area.at(*look), "fov": float(fov),
                           "figures": [], "props": []}
    for f in figures:
        f = list(f) + [0.0, "idle", None][len(f) - 3:] if len(f) < 6 else list(f)
        x, y, z, yaw, pose, holding = f[:6]
        out["figures"].append({"p": area.at(x, y, z), "yaw": float(yaw), "pose": pose,
                               "holding": holding, "extra": f[6] if len(f) > 6 else None})
    for prop in props:
        part = dict(prop)
        part["p"] = area.at(*part["p"])
        out["props"].append(part)
    if sky:
        out["sky"] = sky
    return out


def build_world(name: str, entries: Sequence[Tuple[str, Any, str, str, float]],
                kill_y: float = KILL_Y, card: Optional[Dict[str, Any]] = None
                ) -> Dict[str, Any]:
    """The whole map: every place built in its own slot.

    ``entries`` is ``(id, module, name, ground colour, fog)`` per place; each
    module has ``HALF``, ``SKY``, ``AMBIENT`` and ``build(area)``.
    """
    first = entries[0][1]
    root = MapBuilder(name, sky=first.SKY, ambient=first.AMBIENT, fog=420.0,
                      ground="#3a3f46")
    areas: List[Dict[str, Any]] = []
    card_shot: Dict[str, Any] = {}
    for index, (area_id, module, area_name, ground_colour, fog) in enumerate(entries):
        ox, oz = SLOTS[index]
        area = ArenaArea(root, area_id, area_name, ox, oz, module.HALF, module.SKY,
                         module.AMBIENT, ground_colour, fog=fog)
        module.build(area)
        if card and card.get("area") == area_id:
            # the world's own card: a moment staged in one of its places
            card_shot = shot_spec(area, card["eye"], card["look"], card.get("fov", 44.0),
                                  card.get("figures", ()), card.get("props", ()),
                                  card.get("sky"))
            card_shot["area"] = area_id
        areas.append(area.finish())
    root.marker("mode", "arena")
    root.marker("card", card_shot)
    root.marker("areas", areas)
    root.marker("nav_regions", [a["rect"] for a in areas])
    root.kill_y = kill_y
    return root.to_dict()


def area_payload(map_data: Dict[str, Any], area_id: str) -> Dict[str, Any]:
    """The map a client needs while ``area_id`` is being played: that place's
    parts, its sky, and the markers the client draws objectives from."""
    areas = map_data["markers"]["areas"]
    area = next((a for a in areas if a["id"] == area_id), areas[0])
    parts = map_data["parts"][area["parts"][0]:area["parts"][1]]
    return {
        "name": "%s - %s" % (map_data["name"], area["name"]),
        "parts": parts,
        "spawns": {},
        "markers": {"mode": "arena", "area": area["id"], "area_name": area["name"],
                    "area_rect": area["rect"], "centre": area["centre"],
                    "points": area.get("points") or {},
                    "landmarks": area.get("landmarks") or [],
                    "data": area.get("data") or {}},
        "sky": area["sky"],
        "ambient": area["ambient"],
        "fog": area["fog"],
        "ground": area["ground"],
        "kill_y": map_data["kill_y"],
    }


# ================================================================ structures
def tower(b: Area, x: float, z: float, half: float, height: float, colour: str,
          stair: str = "z-", roof: str = "", floors: int = 1,
          rail: str = "", rail_h: float = 3.0) -> float:
    """A square tower of solid blocks you climb by an outside stair, with a
    railed deck on top.  Returns the deck height."""
    top = height
    slab(b, rect(x - half, x + half, z - half, z + half), top, top, colour)
    run = max(10.0, top * 1.55)
    if stair == "z-":
        flight(b, "z", z - half - run, z - half, x - 2.6, x + 2.6, 0.0, top, colour, fill=0.0)
    elif stair == "z+":
        flight(b, "z", z + half + run, z + half, x - 2.6, x + 2.6, 0.0, top, colour, fill=0.0)
    elif stair == "x-":
        flight(b, "x", x - half - run, x - half, z - 2.6, z + 2.6, 0.0, top, colour, fill=0.0)
    else:
        flight(b, "x", x + half + run, x + half, z - 2.6, z + 2.6, 0.0, top, colour, fill=0.0)
    if rail:
        gap = {"z-": "z-", "z+": "z+", "x-": "x-", "x+": "x+"}[stair]
        along = x if gap[0] == "z" else z
        room_walls(b, rect(x - half, x + half, z - half, z + half), 0.8, top, top + rail_h,
                   rail, doors={gap: [(along - 2.8, along + 2.8, top + rail_h)]})
    if roof:
        for dx in (-1, 1):
            for dz in (-1, 1):
                b.box([x + dx * (half - 0.4), top + rail_h + 3.0, z + dz * (half - 0.4)],
                      [0.8, 6.0, 0.8], rail or colour)
        slab(b, rect(x - half - 0.6, x + half + 0.6, z - half - 0.6, z + half + 0.6),
             top + rail_h + 6.6, 0.6, roof)
    return top


def steps_block(b: Area, axis: str, near: float, far: float, lo: float, hi: float,
                y0: float, y1: float, colour: str) -> None:
    """A stair standing on whatever is at ``y0`` (filled down to it)."""
    flight(b, axis, near, far, lo, hi, y0, y1, colour, fill=y0)


def pillar_row(b: Area, axis: str, at: float, lo: float, hi: float, count: int,
               height: float, size: float, colour: str, y: float = 0.0,
               cap: str = "") -> None:
    """Free-standing columns in a line (a colonnade, a pier's posts)."""
    for k in range(count):
        u = lo + (hi - lo) * (k + 0.5) / count
        x, z = (u, at) if axis == "x" else (at, u)
        b.box([x, y + height / 2.0, z], [size, height, size], colour)
        if cap:
            b.box([x, y + height + 0.4, z], [size + 1.2, 0.8, size + 1.2], cap)


def crate_stack(b: Area, x: float, z: float, layers: int = 2, size: float = 5.0,
                colour: str = WOOD, y: float = 0.0, rng: Optional[random.Random] = None) -> None:
    """Crates on crates, each a little smaller so the stack reads as boxes
    and no two faces line up."""
    rng = rng or random.Random(int(x * 13 + z * 7))
    s = size
    for k in range(layers):
        crate(b, x + rng.uniform(-0.4, 0.4) * (k > 0), y, z + rng.uniform(-0.4, 0.4) * (k > 0),
              s, colour)
        y += s
        s *= 0.82


def scatter(rng: random.Random, count: int, x0: float, x1: float, z0: float, z1: float,
            keep_out: Sequence[Rect] = (), pad: float = 4.0,
            spacing: float = 6.0) -> List[Tuple[float, float]]:
    """``count`` points inside a rectangle, clear of ``keep_out`` and of each
    other -- for trees, rocks and clutter."""
    out: List[Tuple[float, float]] = []
    tries = 0
    while len(out) < count and tries < count * 60:
        tries += 1
        x, z = rng.uniform(x0, x1), rng.uniform(z0, z1)
        if any(r[0] - pad < x < r[1] + pad and r[2] - pad < z < r[3] + pad for r in keep_out):
            continue
        if any((x - a) ** 2 + (z - c) ** 2 < spacing * spacing for a, c in out):
            continue
        out.append((x, z))
    return out


def palm(b: MapBuilder, x: float, z: float, y: float = 0.0, scale: float = 1.0,
         trunk: str = "#8a6a42", leaf: str = "#3f8a3a") -> None:
    """A palm: a segmented trunk and a crown of fronds (the fronds are leaves:
    see-through and overhead)."""
    h = 14.0 * scale
    for k in range(4):
        b.cyl([x, y + h * (k + 0.5) / 4.0, z], [1.6 * scale - k * 0.15, h / 4.0, 1.6 * scale - k * 0.15],
              trunk if k % 2 == 0 else "#7a5a36")
    for k in range(6):
        a = k * math.pi / 3.0
        b.box([x + math.sin(a) * 3.2 * scale, y + h + 0.4, z + math.cos(a) * 3.2 * scale],
              [1.6 * scale, 0.4, 6.6 * scale], leaf, r=[0.3, a, 0], collide=False)
    b.sphere([x, y + h + 0.6, z], [2.2 * scale, 1.8 * scale, 2.2 * scale], "#5a4a2a",
             collide=False)


def cactus(b: MapBuilder, x: float, z: float, y: float = 0.0, scale: float = 1.0,
           colour: str = "#4f8a3a") -> None:
    h = 8.0 * scale
    b.box([x, y + h / 2.0, z], [1.6 * scale, h, 1.6 * scale], colour)
    b.box([x + 1.6 * scale, y + h * 0.55, z], [1.6 * scale, 1.2 * scale, 1.2 * scale], colour)
    b.box([x + 2.0 * scale, y + h * 0.55 + 1.6 * scale, z], [1.0 * scale, 2.6 * scale,
                                                               1.0 * scale], colour)


def rock_cluster(b: MapBuilder, x: float, z: float, rng: random.Random, y: float = 0.0,
                 scale: float = 1.0, colour: str = "#7d8288") -> None:
    """Three boulders leaning together: cover you can stand behind."""
    for k in range(3):
        s = scale * rng.uniform(0.8, 1.3)
        b.rock(x + rng.uniform(-3.0, 3.0) * scale, z + rng.uniform(-3.0, 3.0) * scale, y, s,
               colour)


def rail_line(b: MapBuilder, points: Sequence[Sequence[float]], y: float = 0.0,
              gauge: float = 3.2, rail: str = "#5a5f66", sleeper: str = "#5a3a22",
              every: float = 3.0) -> None:
    """Rails and sleepers along an axis-aligned polyline (x, z) at ground
    height ``y``.  Both are solid and well under a step (anything standing in
    a walkway has to be), the rails sit on the sleepers, and nothing overlaps
    on a plane."""
    for (x0, z0), (x1, z1) in zip(points, points[1:]):
        dx, dz = x1 - x0, z1 - z0
        length = math.hypot(dx, dz)
        if length < 0.5:
            continue
        ux, uz = dx / length, dz / length
        along_x = abs(ux) > abs(uz)
        count = max(1, int(length / every))
        for k in range(count):
            t = (k + 0.5) / count
            sx, sz = x0 + dx * t, z0 + dz * t
            if along_x:
                b.box([sx, y + 0.15, sz], [1.0, 0.3, gauge + 1.6], sleeper)
            else:
                b.box([sx, y + 0.15, sz], [gauge + 1.6, 0.3, 1.0], sleeper)
        for side in (-1, 1):
            if along_x:
                b.box([(x0 + x1) / 2.0, y + 0.45, z0 + side * gauge / 2.0],
                      [abs(dx), 0.3, 0.4], rail, material="metal")
            else:
                b.box([x0 + side * gauge / 2.0, y + 0.45, (z0 + z1) / 2.0],
                      [0.4, 0.3, abs(dz)], rail, material="metal")


def neon_strip(b: MapBuilder, x: float, y: float, z: float, length: float, axis: str,
               colour: str, depth_out: float = 0.0) -> None:
    """A neon tube along a wall face (the caller puts it proud of the wall)."""
    size = [length, 0.4, 0.3] if axis == "x" else [0.3, 0.4, length]
    b.box([x, y, z], size, colour, material="neon", collide=False)
