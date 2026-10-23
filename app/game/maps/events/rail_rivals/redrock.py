"""Redrock Mesa -- banded sandstone at sundown: a dinosaur dig, a mesa the
lines tunnel under, and a river gorge spanned by two lift bridges.

Layout (north is -z; both tracks run west to east)::

    z -250 ================ THE BUTTES =====================|gorge|===========
           RED BUTTE      the Bone Pit         THE MESA      |     | PAINTED
           NORTH YARD     (a T. rex in the    (ranch on top, |lift | BLUFF
             lane a ---\\    rock, scaffolds)   the crossing   =====  lane b end
    z    0              ---------------------->  in a cavern  |river| cliff dwellings
             lane b ---/                       underneath)    =====  trading post
           RED BUTTE                                          |lift | EAGLE ROCK
           SOUTH YARD                                         |     | lane a end
    z +250 ================ THE BUTTES =====================|gorge|===========

Both lines run into the mesa through portals in its west wall and cross in
the cavern under it, lit by lanterns on its pillars; stairs climb from the
cavern and up the outside to the ranch on top.  East of the mesa the river
gorge cuts the whole area in two, thirty units deep: each line crosses it
on a vertical-lift bridge whose deck the other side can winch up to the
top of its towers (the rules: app/game/worlds/rail_rivals.py).  Anyone who
falls in is swept away.
"""
from __future__ import annotations

import math
import random

from ..kit import (
    WARM, WOOD, WOOD_DARK, ArenaArea, backdrop, building, carve, flight, ground,
    lantern, perimeter, plate, rect, room_walls, sign_decal, slab, threshold,
    wall_sign)
from . import rails
from .rails import (
    barrel, beside, boxcar, buffer_stop, cactus, clear_of, coal_heap, crate_stack,
    depot, fillet, flatcar, lay_track, length, lever, mile_post, mirror, rock,
    sleeper_pile, span_of, split_at, stair, telegraph, wagon, water_tower,
    windmill, yard)

HALF = (400.0, 250.0)
SKY = {"top": "#35305e", "horizon": "#ff8a50", "sun": [0.82, 0.14, 0.3],
       "clouds": 0.4, "tint": "#ffb888"}
AMBIENT = "#a07a70"
GROUND = "#c06a3c"
FOG = 820.0

SAND = "#c8743e"
SAND_LIGHT = "#d88a50"
ROCK = "#a84a28"
ROCK_DARK = "#86381e"
ROCK_LIGHT = "#c06038"
BAND = "#e2b890"
ADOBE = "#c88a5a"
ADOBE_DARK = "#a86a42"
STEEL_RED = "#8a3a2a"
WATER = "#3a7a9a"

GORGE = (150.0, 190.0)
GORGE_FLOOR = -26.0
DROWN_Y = -14.0
BRIDGE = (144.0, 196.0)
LIFT = 24.0
MESA = rect(-70.0, 70.0, -80.0, 80.0)
MESA_WALL = 6.0
CEILING = 22.0
MESA_TOP = 30.0
PIT = rect(-172.0, -110.0, -50.0, 50.0)
PIT_FLOOR = -8.0

_CORNERS = [(-372.0, -170.0), (-262.0, -170.0), (-182.0, -90.0), (-100.0, -90.0),
            (100.0, 90.0), (250.0, 90.0), (300.0, 170.0), (372.0, 170.0)]
LANE_A = split_at(fillet(_CORNERS, radius=30.0, step=4.0), xs=BRIDGE)
LANE_B = mirror(LANE_A)

KEEP: list = []


def _free(area, margin: float = 3.0) -> bool:
    x0, x1, z0, z1 = area
    return all(x1 + margin <= k[0] or x0 - margin >= k[1] or
               z1 + margin <= k[2] or z0 - margin >= k[3] for k in KEEP)


def _lane_free(area, margin: float = 9.0) -> bool:
    return clear_of(area, (LANE_A, LANE_B), margin)


def build(b: ArenaArea) -> None:
    rng = random.Random(0x4ED4)
    del KEEP[:]
    m = b.margin
    gorge = rect(GORGE[0], GORGE[1], -b.half_z, b.half_z)
    b.extra.update({"accent": "#ff7a3a", "twist": "bridges", "drown_y": DROWN_Y,
                    "lanes": {"a": _world(b, LANE_A), "b": _world(b, LANE_B)},
                    "names": {"a": "the north line", "b": "the south line"},
                    "bridges": {"a": list(span_of(LANE_A, BRIDGE[0], BRIDGE[1], 80, 100)),
                                "b": list(span_of(LANE_B, BRIDGE[0], BRIDGE[1], -100, -80))}})
    ground(b, SAND, soil=ROCK_DARK, material="plastic", holes=[gorge, PIT])
    perimeter(b, 40.0, ROCK, ROCK_LIGHT, rng, ragged=30.0)
    # the gorge stops at the edge walls: rock closes its ends below the soil
    for sz in (-1.0, 1.0):
        z0, z1 = (b.half_z, b.half_z + m) if sz > 0 else (-b.half_z - m, -b.half_z)
        slab(b, rect(GORGE[0], GORGE[1], z0, z1), -6.0, 26.0, ROCK_DARK)
    backdrop(b, "mesas", 0.0, rng, [ROCK, "#9a4426", "#b85a32"], depth=150.0)
    _gorge(b, rng)
    _tracks(b)
    _bridges(b)
    _yards(b)
    _termini(b)
    _depots(b)
    for kind, (hx, hz) in (("depot", (24.0, 12.0)), ("lever", (5.0, 5.0))):
        for entry in b.points.get(kind, []):
            x, z = entry["p"][0] - b.ox, entry["p"][2] - b.oz
            KEEP.append(rect(x - hx, x + hx, z - hz, z + hz))
    _mesa(b, rng)
    _pit(b, rng)
    _east(b, rng)
    _coaling(b, rng)
    _scatter(b, rng)
    telegraph(b, LANE_A, -1.0)
    telegraph(b, LANE_B, 1.0)
    for f, label in ((0.1, "MP 1"), (0.55, "MP 2"), (0.92, "MP 3")):
        mile_post(b, LANE_A, f, -1.0, label)
        mile_post(b, LANE_B, f, 1.0, label)
    for x, z, name in ((-350, -170, "Red Butte north yard"), (-350, 170, "Red Butte south yard"),
                       (350, -170, "Painted Bluff"), (350, 170, "Eagle Rock"),
                       (-141, 0, "the Bone Pit"), (0, 0, "the cavern under the mesa"),
                       (0, -40, "the mesa top ranch"), (170, 90, "the south lift bridge"),
                       (170, -90, "the north lift bridge"), (170, 0, "the river gorge"),
                       (186, 0, "the cliff dwellings"), (300, 0, "the trading post"),
                       (-250, 0, "the windmill")):
        b.landmark(float(x), float(z), name)
    b.camera(-150.0, 70.0, 150.0, 0.0, 10.0, 0.0)
    b.camera(260.0, 60.0, 0.0, 160.0, -4.0, 0.0)
    b.camera(-260.0, 50.0, -40.0, -140.0, -4.0, 0.0)


def _world(b: ArenaArea, path):
    return [b.at(x, 0.0, z) for x, z in path]


# =================================================================== gorge
def _gorge(b: ArenaArea, rng: random.Random) -> None:
    """Thirty units of banded rock down to a river; ledges and the cliff
    dwellings on the east wall, reached by a stair from the rim."""
    hz = b.half_z
    # walls lined to the bottom (the ground's soil only goes six down)
    for x0, x1 in ((GORGE[0] - 4.0, GORGE[0]), (GORGE[1], GORGE[1] + 4.0)):
        slab(b, rect(x0, x1, -hz, hz), -6.0, 24.0, ROCK_DARK)
        # the bands in the rock, a step proud of the face where they show
        face = GORGE[0] if x1 == GORGE[0] else GORGE[1]
        sign = 1.0 if face == GORGE[0] else -1.0
        for y, colour in ((-9.0, BAND), (-15.0, ROCK_LIGHT), (-20.0, BAND)):
            b.box([face + sign * 0.02, y, 0.0], [0.04, 1.6, 2 * hz], colour, collide=False)
    slab(b, rect(GORGE[0], GORGE[1], -hz, hz), GORGE_FLOOR, 4.0, "#5a4a3a")
    b.box([(GORGE[0] + GORGE[1]) / 2.0, GORGE_FLOOR + 3.6, 0.0], [GORGE[1] - GORGE[0], 0.8, 2 * hz],
          WATER, material="glass", alpha=0.8, collide=False)
    for k in range(10):
        z = -hz + 20.0 + k * (2 * hz - 40.0) / 9.0 + rng.uniform(-8, 8)
        x = rng.uniform(GORGE[0] + 6.0, GORGE[1] - 6.0)
        rock(b, x, z, rng.uniform(4.0, 8.0), rng.uniform(5.0, 9.0), rng.uniform(4.0, 7.0),
             ROCK_DARK, y=GORGE_FLOOR)
    # the cliff dwellings: a ledge along the east wall, rooms against it
    ledge = rect(GORGE[1] - 9.0, GORGE[1], -36.0, 36.0)
    slab(b, ledge, -10.0, 2.0, ROCK)
    for k, z in enumerate((-28.0, -14.0, 2.0, 18.0)):
        w = 10.0 if k % 2 else 12.0
        room = rect(GORGE[1] - 7.0, GORGE[1], z - w / 2.0, z + w / 2.0)
        tall = 7.0 + (k % 2) * 1.0
        building(b, room, -10.0, tall, ADOBE, roof_colour=ADOBE_DARK,
                 doors={"x-": [(z - 1.5, z + 1.5, -10.0 + 6.2)]},
                 windows={"x-": [(z + w / 2.0 - 3.0, z + w / 2.0 - 1.6, -6.6, -5.2)]},
                 lights="", studs_roof=False)
        for j in range(3):
            b.box([GORGE[1] - 7.3, -10.0 + tall + 1.2 - 0.3, z - w / 2.0 + 2.0 + j * 3.0],
                  [0.8, 0.3, 0.3], WOOD_DARK)
    # the stair cut down the wall from the rim at the south end of the ledge
    flight(b, "z", 36.0, 58.0, GORGE[1] - 6.0, GORGE[1], -10.0, 0.0, ROCK_LIGHT, fill=-12.0)
    for z in (-36.0, 36.0):
        b.box([GORGE[1] - 8.6, -8.6, z], [0.8, 0.8 + 2.0, 0.8], WOOD_DARK)
    b.mark("perch", GORGE[1] - 4.0, -10.0, -6.0)
    lantern(b, GORGE[1] - 7.6, -2.4, 10.0, WARM)


# ================================================================= tracks
def _pieces(path):
    """The lane as laid on solid ground: everything but the lift span."""
    west = [p for p in path if p[0] <= BRIDGE[0] + 0.01]
    east = [p for p in path if p[0] >= BRIDGE[1] - 0.01]
    return west, east


def _tracks(b: ArenaArea) -> None:
    for path in (LANE_A, LANE_B):
        for piece in _pieces(path):
            lay_track(b, piece)


def _bridges(b: ArenaArea) -> None:
    """A vertical-lift bridge on each line: four steel towers on the banks,
    the deck between them -- down at track height or up at the tops of the
    towers, never both -- and a control cabin on the east bank."""
    for lane, z in (("a", 90.0), ("b", -90.0)):
        for up in (False, True):
            base = LIFT if up else 0.0
            with b.detached() as parts:
                deck = rect(BRIDGE[0], BRIDGE[1], z - 6.0, z + 6.0)
                slab(b, deck, base + rails.BALLAST_TOP, 1.0, STEEL_RED, studs=True,
                     material="metal")
                lay_track(b, [(BRIDGE[0], z), (BRIDGE[1], z)], base=base, skip=[(0.0, 999.0)])
                for e in (-1.0, 1.0):
                    for x in range(int(BRIDGE[0]) + 3, int(BRIDGE[1]), 7):
                        b.box([x, base + rails.BALLAST_TOP + 1.3, z + e * 5.6], [0.5, 2.6, 0.5],
                              "#5a2a1e", material="metal")
                    b.box([(BRIDGE[0] + BRIDGE[1]) / 2.0, base + rails.BALLAST_TOP + 2.6 + 0.2,
                           z + e * 5.6], [BRIDGE[1] - BRIDGE[0] - 1.0, 0.4, 0.4], "#5a2a1e",
                          material="metal")
                    # the truss girders under the deck
                    b.box([(BRIDGE[0] + BRIDGE[1]) / 2.0, base - 2.4, z + e * 4.2],
                          [BRIDGE[1] - BRIDGE[0] - 12.0, 3.6, 0.8], STEEL_RED, material="metal")
            b.dynamic("bridge_%s_%s" % (lane, "up" if up else "down"), parts, on=not up,
                      group="bridge_%s" % lane)
        # the towers, their top beams and counterweights, solid
        for tx in (BRIDGE[0] - 3.0, BRIDGE[1] + 3.0):
            for e in (-1.0, 1.0):
                b.box([tx, 18.0, z + e * 8.0], [2.6, 36.0, 2.6], STEEL_RED, material="metal")
                b.box([tx, 12.0, z + e * 8.0 + e * 1.9], [2.0, 6.0, 1.2], "#4a4642",
                      material="metal")
            b.box([tx, 37.0, z], [3.4, 2.0, 19.2], STEEL_RED, material="metal")
            b.cyl([tx, 37.0, z], [3.6, 0.6, 3.6], "#2a2826", collide=False, material="metal",
                  r=[0, 0, math.pi / 2.0])
            lantern(b, tx, 36.0, z, "#ff4a2a")
        # the control cabin on the east bank, its winch inside
        side = 1.0 if z > 0 else -1.0
        cab = rect(BRIDGE[1] + 6.0, BRIDGE[1] + 20.0, z + side * 12.0, z + side * 24.0) if side > 0 \
            else rect(BRIDGE[1] + 6.0, BRIDGE[1] + 20.0, z - 24.0, z - 12.0)
        door_side = "z-" if side > 0 else "z+"
        building(b, cab, 0.0, 8.0, ADOBE, roof_colour=STEEL_RED, floor_colour="#6a4a32",
                 doors={door_side: [(cab[0] + 4.5, cab[0] + 9.5, 6.4)]},
                 windows={"x-": [(cab[2] + 3.0, cab[3] - 3.0, 3.6, 6.4)]}, glass=True,
                 lights=WARM)
        threshold(b, cab, door_side, (cab[0] + 4.5, cab[0] + 9.5))
        wx, wz = (cab[0] + cab[1]) / 2.0 + 2.0, (cab[2] + cab[3]) / 2.0
        b.box([wx, 1.6, wz], [3.0, 3.2, 3.0], "#4a4642", material="metal")
        b.cyl([wx, 3.6, wz], [2.4, 3.4, 2.4], "#2a2826", r=[math.pi / 2.0, 0, 0],
              collide=False, material="metal")
        wall_sign(b, (cab[0] + cab[1]) / 2.0, 9.6, cab[2] - 0.05 if side > 0 else cab[3] + 0.05,
                  12.0, 1.6, sign_decal("BRIDGE No. %d" % (2 if z > 0 else 1), rails.CREAM,
                                        "#3a2414", 7.5), door_side, rails.CREAM)
        b.mark("winch", wx, 1.0, wz, lane=lane)
        KEEP.append(rect(BRIDGE[0] - 6.0, BRIDGE[1] + 6.0, z - 11.0, z + 11.0))
        KEEP.append(rect(cab[0] - 2.0, cab[1] + 2.0, cab[2] - 2.0, cab[3] + 2.0))


# =================================================================== yards
def _yards(b: ArenaArea) -> None:
    """Red Butte's two yards: adobe engine houses, flat-roofed with their
    vigas showing, and a water tank between."""
    for lane, z, side, name, roof in (("a", -170.0, -1.0, "RED BUTTE NORTH", "#7a2a1e"),
                                      ("b", 170.0, 1.0, "RED BUTTE SOUTH", "#2a3a6a")):
        area = yard(b, lane, -380.0, -326.0, z, side, name, roof,
                    sign=(BAND, "#5a2414"))
        house = rect(-392.0, -340.0, -244.0, -212.0) if side < 0 else \
            rect(-392.0, -340.0, 212.0, 244.0)
        _adobe(b, house, 15.0, doors={"x+": [(house[2] + 6.0, house[3] - 6.0, 12.0)]},
               windows={"z+" if side < 0 else "z-": [(-384.0, -372.0, 6.0, 10.0),
                                                     (-362.0, -350.0, 6.0, 10.0)]})
        threshold(b, house, "x+", (house[2] + 6.0, house[3] - 6.0))
        KEEP.append(rect(-400.0, -280.0, min(z, area[2]) - 12.0, max(z, area[3]) + 12.0))
        KEEP.append(house)
    water_tower(b, -330.0, 0.0, "#8a5a3a")
    KEEP.append(rect(-340.0, -304.0, -10.0, 10.0))
    # a short train of ore cars in the middle between the yards
    lay_track(b, [(-392.0, -40.0), (-300.0, -40.0)])
    buffer_stop(b, -388.0, -40.0, math.pi / 2.0, rails.RED)
    buffer_stop(b, -304.0, -40.0, math.pi / 2.0, rails.RED)
    boxcar(b, -368.0, -40.0, "x", "#8a3a2a", "RED BUTTE & PACIFIC", door="open")
    flatcar(b, -342.0, -40.0, "x", "rails", random.Random(7))
    flatcar(b, -320.0, -40.0, "x", "crates", random.Random(8), length=16.0)
    KEEP.append(rect(-394.0, -298.0, -45.0, -35.0))


def _adobe(b: ArenaArea, area, height: float, *, doors=None, windows=None, y0: float = 0.0,
           roof_colour: str = ADOBE_DARK, lights: str = WARM, parapet: float = 1.4,
           gaps=None) -> None:
    """A pueblo-style building: thick adobe walls, a flat roof behind a low
    parapet, and the roof beams (vigas) poking out under it."""
    building(b, area, y0, height, ADOBE, roof_colour=roof_colour, floor_colour="#7a5232",
             doors=doors, windows=windows, glass=False, lights=lights, parapet=parapet,
             parapet_gaps=gaps)
    x0, x1, z0, z1 = area
    y = y0 + height - 1.2
    for k in range(int((x1 - x0) // 5.0)):
        x = x0 + 2.5 + k * 5.0
        for zz, e in ((z0, -1.0), (z1, 1.0)):
            b.box([x, y, zz + e * 0.9], [0.7, 0.7, 1.8], WOOD_DARK)


# ================================================================= termini
def _termini(b: ArenaArea) -> None:
    for lane, z, side, name, roof in (("a", 170.0, 1.0, "EAGLE ROCK", "#2a3a6a"),
                                      ("b", -170.0, -1.0, "PAINTED BLUFF", "#7a2a1e")):
        area = yard(b, lane, 326.0, 380.0, z, side, name, roof, sign=(rails.GOLD, "#3a2414"),
                    end="finish")
        house = rect(332.0, 384.0, z + 24.0, z + 46.0) if side > 0 else \
            rect(332.0, 384.0, z - 46.0, z - 24.0)
        _adobe(b, house, 12.0, doors={"x-": [(house[2] + 6.0, house[3] - 6.0, 9.0)]},
               windows={"z-" if side > 0 else "z+": [(336.0, 348.0, 4.0, 8.0),
                                                     (364.0, 376.0, 4.0, 8.0)]},
               roof_colour=roof)
        threshold(b, house, "x-", (house[2] + 6.0, house[3] - 6.0))
        KEEP.append(rect(300.0, 400.0, min(z, area[2], house[2]) - 8.0,
                         max(z, area[3], house[3]) + 8.0))


# ================================================================== depots
def _depots(b: ArenaArea) -> None:
    depot(b, "a", LANE_A, 0.3, 1.0, "BONE PIT HALT", 1, "#7a2a1e")
    depot(b, "a", LANE_A, 0.87, -1.0, "CANYON RIM", 2, "#2a3a6a")
    depot(b, "b", LANE_B, 0.3, -1.0, "BONE PIT SOUTH", 1, "#2a3a6a")
    depot(b, "b", LANE_B, 0.87, 1.0, "BLUFF RIM", 2, "#7a2a1e")
    for lane, path, sides in (("a", LANE_A, (1.0, 1.0)), ("b", LANE_B, (-1.0, -1.0))):
        for index, (f, side) in enumerate(zip((0.42, 0.66), sides)):
            lever(b, lane, path, f, side, index)


# ==================================================================== mesa
def _portals(path, x_outer: float, x_inner: float):
    """The z span a lane needs through a wall between x_outer and x_inner."""
    zs = []
    for i in range(len(path) - 1):
        (ax, az), (bx, bz) = path[i], path[i + 1]
        for x in (x_outer, x_inner):
            if (ax - x) * (bx - x) <= 0 and ax != bx:
                zs.append(az + (bz - az) * (x - ax) / (bx - ax))
    return (min(zs) - 9.0, max(zs) + 9.0) if zs else None


def _mesa(b: ArenaArea, rng: random.Random) -> None:
    """The mesa: rock walls round a cavern where the lines cross, four
    pillars holding up the roof, stairs inside and out to the top, and a
    ranch up there."""
    x0, x1, z0, z1 = MESA
    t = MESA_WALL
    gaps = {}
    for side, outer, inner in (("x-", x0, x0 + t), ("x+", x1, x1 - t)):
        spans = []
        for path in (LANE_A, LANE_B):
            span = _portals(path, outer, inner)
            if span:
                spans.append((span[0], span[1], 16.0))
        gaps[side] = spans
    room_walls(b, MESA, t, 0.0, CEILING, ROCK, doors=gaps)
    # the roof, with a hole over each inside stair
    holes = [rect(-10.0, 22.0, z0 + t, z0 + t + 6.0), rect(-22.0, 10.0, z1 - t - 6.0, z1 - t)]
    plate(b, carve(MESA, holes), MESA_TOP, MESA_TOP - CEILING, ROCK_DARK)
    plate(b, carve(rect(x0 + 0.5, x1 - 0.5, z0 + 0.5, z1 - 0.5), holes), MESA_TOP + 0.4, 0.4,
          SAND_LIGHT, studs=True)
    # the portals' timber frames and the rock above them
    for side, spans in gaps.items():
        wx = x0 - 0.7 if side == "x-" else x1 + 0.7
        for a, c, head in spans:
            b.box([wx, head + 0.8, (a + c) / 2.0], [1.4, 1.6, c - a + 2.0], WOOD_DARK)
            for zz in (a - 0.3, c + 0.3):
                b.box([wx, head / 2.0, zz], [1.4, head, 1.4], WOOD_DARK)
    # the outside: buttresses and bands so the walls read as cliffs
    for k in range(18):
        if k % 2 == 0:
            x = x0 + 8.0 + (k // 2) * (x1 - x0 - 16.0) / 8.0
            for zz, e in ((z0, -1.0), (z1, 1.0)):
                d = rng.uniform(3.0, 6.0)
                h = rng.uniform(16.0, 34.0)
                bx = rect(x - 6.0, x + 6.0, zz + e * 0.0 - (d if e < 0 else 0.0),
                          zz + (d if e > 0 else 0.0))
                if _stair_clear(bx):
                    b.box([x, h / 2.0, (bx[2] + bx[3]) / 2.0], [12.0, h, d],
                          rng.choice([ROCK, ROCK_DARK, ROCK_LIGHT]))
    for y, colour in ((8.0, BAND), (18.0, ROCK_LIGHT), (26.0, BAND)):
        for zz, e in ((z0, -1.0), (z1, 1.0)):
            b.box([0.0, y, zz + e * 0.02], [x1 - x0, 1.4, 0.04], colour, collide=False)
        for xx, e in ((x0, -1.0), (x1, 1.0)):
            for a, c in _between(z0, z1, gaps["x-" if e < 0 else "x+"], y):
                b.box([xx + e * 0.02, y, (a + c) / 2.0], [0.04, 1.4, c - a], colour,
                      collide=False)
    # pillars in the cavern, lanterns on them
    for px, pz in ((-36.0, 0.0), (36.0, 0.0), (0.0, -42.0), (0.0, 42.0)):
        b.box([px, CEILING / 2.0, pz], [10.0, CEILING, 10.0], ROCK_DARK)
        for e in (-1.0, 1.0):
            lantern(b, px + e * 5.4, 9.0, pz, WARM)
            b.box([px + e * 5.15, 9.15, pz], [0.3, 0.3, 0.6], rails.IRON, collide=False)
    for lx, lz in ((-50.0, -30.0), (50.0, 30.0), (-50.0, 30.0), (50.0, -30.0), (0.0, 0.0)):
        lantern(b, lx, CEILING, lz, WARM)
    # the inside stairs, one along each long wall, up through the roof
    stair(b, "x", -46.0, 22.0, z0 + t, z0 + t + 6.0, 0.0, MESA_TOP, ROCK_LIGHT)
    stair(b, "x", 46.0, -22.0, z1 - t - 6.0, z1 - t, 0.0, MESA_TOP, ROCK_LIGHT)
    # the outside stairs, up the north and south faces
    stair(b, "x", -60.0, 4.0, z0 - 8.0, z0 - 2.0, 0.0, MESA_TOP, ROCK_LIGHT)
    slab(b, rect(4.0, 12.0, z0 - 8.0, z0), MESA_TOP, MESA_TOP + 0.3, ROCK_LIGHT)
    stair(b, "x", 60.0, -4.0, z1 + 2.0, z1 + 8.0, 0.0, MESA_TOP, ROCK_LIGHT)
    slab(b, rect(-12.0, -4.0, z1, z1 + 8.0), MESA_TOP, MESA_TOP + 0.3, ROCK_LIGHT)
    # crystals and a cart of ore in the cavern's corners
    for cx, cz in ((-56.0, -2.0), (56.0, 2.0)):
        for k in range(4):
            b.box([cx + rng.uniform(-2.6, 2.6), 1.4 + k * 0.5, cz + rng.uniform(-2.6, 2.6)],
                  [1.2, 2.8 + k, 1.2], "#ffb35a", material="neon")
        b.box([cx, 1.0, cz], [7.0, 2.0, 7.0], ROCK_DARK)
    # what the cavern keeps: crates and powder by the walls, stalactites
    for cx, cz in ((-54.0, 18.0), (54.0, -18.0), (-20.0, -60.0), (20.0, 60.0)):
        crate_stack(b, cx, cz, rng, WOOD)
        barrel(b, cx + 3.6, cz + 1.0, "#8a3a2a")
    for k in range(26):
        px, pz = rng.uniform(x0 + 10.0, x1 - 10.0), rng.uniform(z0 + 10.0, z1 - 10.0)
        h = rng.uniform(2.5, 5.5)
        b.cone([px, CEILING - h / 2.0, pz], [rng.uniform(1.6, 3.2), h, rng.uniform(1.6, 3.2)],
               rng.choice([ROCK_DARK, ROCK]), r=[math.pi, 0, 0], collide=False)
    wall_sign(b, x0 + t + 0.3, 14.0, 0.0, 26.0, 3.0,
              sign_decal("MESA CROSSING", BAND, "#5a2414", 8.6), "x+", BAND)
    # the ranch on top: the house, a windmill, a tank, a corral
    y = MESA_TOP + 0.4
    house = rect(-56.0, -30.0, -24.0, 4.0)
    _adobe(b, house, 9.0, y0=y, doors={"x+": [(-14.0, -6.0, y + 7.0)]},
           windows={"z-": [(-50.0, -42.0, y + 3.0, y + 6.0)], "z+": [(-50.0, -42.0, y + 3.0, y + 6.0)]})
    threshold(b, house, "x+", (-14.0, -6.0), y0=y)
    windmill(b, 30.0, 24.0, 20.0, y=y)
    b.cyl([44.0, y + 3.0, -24.0], [10.0, 6.0, 10.0], "#8a8478", material="metal")
    for e, (ax, az, bx, bz) in enumerate(((10.0, 34.0, 40.0, 34.0), (10.0, 54.0, 40.0, 54.0),
                                          (10.0, 34.0, 10.0, 54.0))):
        for k in range(int(max(abs(bx - ax), abs(bz - az)) // 6.0) + 1):
            px = ax + (bx - ax) * k / max(1, int(max(abs(bx - ax), abs(bz - az)) // 6.0))
            pz = az + (bz - az) * k / max(1, int(max(abs(bx - ax), abs(bz - az)) // 6.0))
            b.box([px, y + 1.6, pz], [0.6, 3.2, 0.6], WOOD_DARK)
        if az == bz:
            b.box([(ax + bx) / 2.0, y + 2.6, az], [bx - ax, 0.4, 0.4], WOOD)
        else:
            b.box([ax, y + 2.6, (az + bz) / 2.0], [0.4, 0.4, bz - az], WOOD)
    b.box([28.0, y + 2.0, 44.0], [6.0, 4.0, 5.0], "#d8b860", studs=True)
    b.mark("perch", 0.0, y, -50.0)
    b.mark("perch", 0.0, y, 50.0)
    KEEP.append(rect(x0 - 10.0, x1 + 10.0, z0 - 10.0, z1 + 10.0))


def _stair_clear(area) -> bool:
    """Buttresses keep off the outside stairs."""
    for s in (rect(-62.0, 14.0, MESA[2] - 10.0, MESA[2]), rect(-14.0, 62.0, MESA[3], MESA[3] + 10.0)):
        if area[1] > s[0] and area[0] < s[1] and area[3] > s[2] and area[2] < s[3]:
            return False
    return True


def _between(lo: float, hi: float, gaps, y: float):
    """[lo, hi] with the doorways that reach height ``y`` taken out."""
    out, at = [], lo
    for a, c, head in sorted(gaps):
        if head <= y:
            continue
        if a > at:
            out.append((at, a))
        at = max(at, c)
    if hi > at:
        out.append((at, hi))
    return out


# ===================================================================== pit
def _pit(b: ArenaArea, rng: random.Random) -> None:
    """The Bone Pit: eight units down, a T. rex half out of the rock, the
    grid strung over it, scaffold walks across, ramps at both ends."""
    x0, x1, z0, z1 = PIT
    laid = []
    for r in (rect(x0 - 1.0, x0, z0 - 1.0, z1 + 1.0), rect(x1, x1 + 1.0, z0 - 1.0, z1 + 1.0),
              rect(x0, x1, z0 - 1.0, z0), rect(x0, x1, z1, z1 + 1.0)):
        for p in carve(r, [PIT] + laid):
            slab(b, p, -6.0, -6.0 - PIT_FLOOR, ROCK_DARK)
            laid.append(p)
    slab(b, PIT, PIT_FLOOR, 1.2, "#b86a3c", studs=True)
    # stairs down at both ends and one in the middle of the west side
    flight(b, "z", z0 + 14.0, z0, -146.0, -136.0, PIT_FLOOR, 0.0, ROCK_LIGHT, fill=PIT_FLOOR)
    flight(b, "z", z1 - 14.0, z1, -146.0, -136.0, PIT_FLOOR, 0.0, ROCK_LIGHT, fill=PIT_FLOOR)
    flight(b, "x", x0 + 12.0, x0, -4.0, 4.0, PIT_FLOOR, 0.0, ROCK_LIGHT, fill=PIT_FLOOR)
    # the skeleton, lying north-south, solid bone
    bone = "#efe2c4"
    fy = PIT_FLOOR
    sx = -126.0
    for k in range(16):
        z = -30.0 + k * 3.6
        h = 6.0 + 3.0 * math.sin(k / 15.0 * math.pi)
        b.box([sx, fy + h, z], [2.0, 1.6, 2.6], bone)
        if 3 <= k <= 9:
            for e in (-1.0, 1.0):
                b.box([sx + e * 2.6, fy + h - 1.4, z], [0.8, 2.6, 0.8], bone)
                b.box([sx + e * 3.6, fy + h - 3.6, z], [0.8, 2.6, 0.8], bone)
                b.box([sx + e * 4.0, fy + 1.0 + (h - 5.0) / 2.0 - 0.6, z], [0.8, max(1.0, h - 5.6), 0.8],
                      bone)
    # the skull at the north end, jaw open
    b.box([sx, fy + 7.0, -36.0], [5.0, 4.0, 7.0], bone)
    b.box([sx, fy + 4.4, -37.0], [4.2, 1.2, 6.0], bone)
    for e in (-1.0, 1.0):
        b.box([sx + e * 2.52, fy + 8.0, -37.6], [0.04, 1.2, 1.2], "#3a2a1e", collide=False)
    for k in range(5):
        b.box([sx - 1.6 + k * 0.8, fy + 5.4, -39.4], [0.3, 1.0, 0.3], bone, collide=False)
    # legs and the tail on the floor
    for z, e in ((-6.0, -1.0), (8.0, 1.0)):
        b.box([sx + e * 5.0, fy + 2.0, z], [1.6, 4.0, 1.6], bone)
        b.box([sx + e * 5.0, fy + 0.4, z - 1.6], [2.4, 0.8, 4.0], bone)
    for k in range(6):
        b.box([sx + 1.2 * k, fy + 0.9, 30.0 + k * 3.4], [1.8, 1.8, 3.0], bone)
    # the grid: strings over the dig (paint on the floor) and the pegs
    for k in range(7):
        x = x0 + 4.0 + k * 9.0
        b.box([x, fy + 0.02, 0.0], [0.08, 0.04, z1 - z0 - 8.0], "#f2f2f2", collide=False)
    for k in range(11):
        z = z0 + 4.0 + k * 9.2
        b.box([(x0 + x1) / 2.0, fy + 0.02 + 0.005, z], [x1 - x0 - 8.0, 0.04, 0.08], "#f2f2f2",
              collide=False)
    # scaffold walks across the pit at rim height
    for z in (-26.0, 24.0):
        slab(b, rect(x0 - 2.0, x1 + 2.0, z - 2.0, z + 2.0), 0.5, 0.5, WOOD, studs=True)
        for x in (x0 + 12.0, x0 + 31.0, x1 - 12.0):
            b.box([x, (PIT_FLOOR + 0.0) / 2.0, z], [0.8, -PIT_FLOOR, 0.8], WOOD_DARK)
        for e in (-1.0, 1.0):
            b.box([(x0 + x1) / 2.0, 2.2, z + e * 1.8], [x1 - x0, 0.3, 0.3], WOOD_DARK)
            for x in range(int(x0), int(x1) + 1, 10):
                b.box([x, 1.35, z + e * 1.8], [0.3, 1.7, 0.3], WOOD_DARK)
    # the dig camp round the rim: tents, sifting screens, a crane
    for x, z in ((-190.0, -30.0), (-190.0, 8.0), (-96.0, -24.0)):
        tent = rect(x - 7.0, x + 7.0, z - 6.0, z + 6.0)
        if _lane_free(tent) and _free(tent, 1.0):
            b.box([x, 0.8, z], [14.0, 1.6, 12.0], "#6a4a32")
            b.box([x, 3.4, z], [12.0, 3.6, 10.0], "#e8dcc0")
            b.box([x, 6.0, z], [8.0, 1.6, 10.0], "#e8dcc0")
            KEEP.append(tent)
    for x, z in ((-96.0, 14.0), (-188.0, 34.0)):
        for dx in (-2.0, 2.0):
            for dz in (-1.5, 1.5):
                b.box([x + dx, 1.4, z + dz], [0.5, 2.8, 0.5], WOOD_DARK)
        b.box([x, 3.0, z], [5.0, 0.4, 3.6], "#8a8478")
        KEEP.append(rect(x - 3.0, x + 3.0, z - 3.0, z + 3.0))
    gold = rails.gold_sign
    gold(b, -141.0, 5.0, -56.0, 20.0, 2.6, "THE BONE PIT", "z-")
    KEEP.append(rect(x0 - 4.0, x1 + 4.0, z0 - 8.0, z1 + 4.0))


# ==================================================================== east
def _east(b: ArenaArea, rng: random.Random) -> None:
    """East of the gorge: the trading post, a corral of wagons, and the
    lookout on the west rim."""
    post = rect(276.0, 324.0, -16.0, 16.0)
    _adobe(b, post, 11.0, doors={"x-": [(-4.0, 4.0, 8.0)], "x+": [(-4.0, 4.0, 8.0)]},
           windows={"z-": [(282.0, 292.0, 4.0, 8.0), (308.0, 318.0, 4.0, 8.0)],
                    "z+": [(282.0, 292.0, 4.0, 8.0), (300.0, 308.0, 4.0, 8.0)]},
           gaps={"z+": [(312.0, 318.0)]})
    threshold(b, post, "x-", (-4.0, 4.0))
    threshold(b, post, "x+", (-4.0, 4.0))
    wall_sign(b, 275.65, 9.0, 0.0, 22.0, 2.4,
              sign_decal("TRADING POST", BAND, "#5a2414", 9.2), "x-", BAND)
    stair(b, "z", 36.0, 16.0, 312.0, 318.0, 0.0, 12.4, WOOD)
    b.mark("perch", 300.0, 12.4, 0.0)
    KEEP.append(rect(post[0] - 4.0, post[1] + 4.0, post[2] - 2.0, 38.0))
    for x, z, along in ((240.0, -30.0, "z"), (250.0, 30.0, "z"), (350.0, 40.0, "x")):
        spot = rect(x - 7.0, x + 7.0, z - 7.0, z + 7.0)
        if _lane_free(spot) and _free(spot):
            wagon(b, x, z, along, "#e8d8c0")
            KEEP.append(spot)
    # Eagle Rock village: adobe houses between the trading post and the
    # termini, flat roofs you can hop between, a well in the plaza
    for x, z, w, d, h in ((240.0, 40.0, 20.0, 16.0, 8.0), (268.0, 52.0, 16.0, 14.0, 10.0),
                          (240.0, -44.0, 18.0, 16.0, 9.0), (270.0, -56.0, 16.0, 14.0, 8.0),
                          (352.0, -64.0, 20.0, 18.0, 10.0), (350.0, 70.0, 18.0, 16.0, 8.0)):
        area = rect(x - w / 2.0, x + w / 2.0, z - d / 2.0, z + d / 2.0)
        if not _lane_free(area) or not _free(area, 2.0):
            continue
        facing = "z-" if z > 0 else "z+"
        _adobe(b, area, h, doors={facing: [(x - 2.0, x + 2.0, 6.6)]},
               windows={"x-": [(z - 3.0, z + 1.0, 3.2, 5.6)], "x+": [(z - 1.0, z + 3.0, 3.2, 5.6)]},
               parapet=1.0)
        threshold(b, area, facing, (x - 2.0, x + 2.0))
        b.box([x + w / 2.0 + 1.0, h / 2.0 + 0.2, z], [2.0, h + 0.4, 2.0], ADOBE_DARK)
        KEEP.append(area)
    b.cyl([300.0, 1.4, -40.0], [6.0, 2.8, 6.0], "#8a7a68")
    for e in (-2.6, 2.6):
        b.box([300.0 + e, 4.4, -40.0], [0.6, 3.2, 0.6], WOOD_DARK)
    b.box([300.0, 6.2, -40.0], [6.4, 0.6, 0.8], WOOD_DARK)
    KEEP.append(rect(296.0, 304.0, -44.0, -36.0))
    # the lookout on the west rim, a telescope on its rail
    lk = rect(118.0, 140.0, -10.0, 10.0)
    slab(b, lk, 1.4, 1.7, ROCK_LIGHT, studs=True)
    for e in (-1.0, 1.0):
        b.box([129.0, 2.4, e * 9.6], [22.0, 2.0, 0.8], ROCK)
    b.box([139.6, 2.4, 0.0], [0.8, 2.0, 18.4], ROCK)
    b.box([136.0, 3.6, 0.0], [0.4, 3.0, 0.4], rails.IRON, material="metal")
    b.cyl([136.6, 5.2, 0.0], [0.6, 2.4, 0.6], rails.GOLD, collide=False, material="metal",
          r=[0, 0, math.pi / 2.0 - 0.2])
    KEEP.append(rect(lk[0] - 2.0, lk[1] + 2.0, lk[2] - 2.0, lk[3] + 2.0))


# ================================================================ coaling
def _coaling(b: ArenaArea, rng: random.Random) -> None:
    for x, z in ((-210.0, 0.0), (112.0, 30.0), (40.0, -112.0), (-40.0, 112.0), (230.0, 0.0)):
        coal_heap(b, x, z, rng)
        KEEP.append(rect(x - 5.0, x + 5.0, z - 5.0, z + 5.0))
    windmill(b, -250.0, 0.0, 24.0)
    KEEP.append(rect(-254.0, -246.0, -4.0, 4.0))


# ================================================================ scatter
def _scatter(b: ArenaArea, rng: random.Random) -> None:
    """Hoodoos and balanced rocks, cacti, and the track gang's leavings."""
    for k in range(46):
        x = rng.uniform(-380.0, 380.0)
        z = rng.uniform(-240.0, 240.0)
        w = rng.uniform(4.0, 9.0)
        spot = rect(x - w, x + w, z - w, z + w)
        if not _lane_free(spot, 9.0) or not _free(spot):
            continue
        if GORGE[0] - 8 < x + w and x - w < GORGE[1] + 8:
            continue
        if abs(x) > b.half_x - w - 2 or abs(z) > b.half_z - w - 2:
            continue
        if k % 3 == 0:
            # a hoodoo: a column, banded, a cap rock balanced on top
            h = rng.uniform(14.0, 26.0)
            b.box([x, h / 2.0, z], [w * 0.8, h, w * 0.8], rng.choice([ROCK, ROCK_LIGHT]))
            b.box([x, h * 0.5, z], [w * 0.8 + 0.04, 1.2, w * 0.8 + 0.04], BAND, collide=False)
            b.box([x + 0.4, h + 1.4, z - 0.3], [w * 1.3, 2.8, w * 1.1], ROCK_DARK)
        elif k % 3 == 1:
            rock(b, x, z, w * 1.4, rng.uniform(4.0, 9.0), w * 1.1,
                 rng.choice([ROCK, ROCK_DARK, ROCK_LIGHT]))
        else:
            cactus(b, x, z, rng.uniform(0.9, 1.3))
        KEEP.append(spot)
    total = length(LANE_A)
    for f, side in ((0.05, 1.0), (0.2, -1.0), (0.48, 1.0), (0.78, -1.0), (0.95, 1.0)):
        for path, sgn in ((LANE_A, 1.0), (LANE_B, -1.0)):
            x, z, _ = beside(path, total * f, side * sgn * 12.0)
            x, z = round(x), round(z)
            spot = rect(x - 3.0, x + 3.0, z - 3.0, z + 3.0)
            if _lane_free(spot, 7.0) and _free(spot):
                if (f * 100) % 2 < 1:
                    sleeper_pile(b, x, z, "z", 3)
                else:
                    crate_stack(b, x, z, rng)
                    barrel(b, x + 3.0, z + 1.0, "#8a3a2a")
                KEEP.append(spot)
