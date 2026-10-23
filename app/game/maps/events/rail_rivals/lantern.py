"""Lantern Deep -- the lowest level of the Lantern Company's mine, a cavern
so big the lines run through it end to end, lit by lanterns, crystals,
mushrooms and the lava in the chasm.

Layout (north is -z; both tracks run west to east)::

    z -230 ============================ ROCK ====================================
           UPPER ADIT     the Crystal Grotto     |c|  the Old Workings  BOTTOM
           (daylight)                            |h|  (headframe,       LEVEL
             lane a ---\\  ===the west gallery==\\ |a|  scaffolds)      /-- lane b end
    z    0   the miners' camp                   DEVIL'S    the Foundry
             lane b ---/  ===the west gallery==/ |s|  BRIDGE           \\-- lane a end
           LOWER ADIT     the chapel             |m|  the Mushroom Glen  DEEP
           (daylight)                            | |                    STATION
    z +230 ============================ ROCK ====================================

A lava chasm splits the cavern north to south; the only ways over are the
Devil's Bridge -- a span of living rock where the two lines cross at right
angles -- and two rope bridges.  Both lines run through a timbered gallery
on each side.  Firedamp gathers in the low places and goes up when it
finds a flame: the rules vent one pocket after another (marks ``gas``).
"""
from __future__ import annotations

import math
import random

from ..kit import (
    WARM, ArenaArea, building, carve, ground, lantern, rect, room_walls, sign_decal,
    slab, threshold, wall_sign)
from . import rails
from .rails import (
    barrel, beside, buffer_stop, clear_of, coal_heap, crate_stack, depot, fillet,
    handcar, lay_track, length, lever, mile_post, mirror, rock, sleeper_pile, stair,
    telegraph, wagon, yard)

HALF = (380.0, 230.0)
SKY = {"top": "#100c0a", "horizon": "#2a1c14", "sun": [0.25, 0.9, 0.35],
       "clouds": 0.0, "tint": "#ffb070"}
AMBIENT = "#7a6250"
GROUND = "#4a3a30"
FOG = 520.0

FLOOR = "#4a3a30"
FLOOR_LIGHT = "#5a4838"
ROCK = "#3e3430"
ROCK_DARK = "#2e2622"
ROCK_LIGHT = "#5a4a40"
LAVA = "#ff6a1a"
LAVA_DARK = "#c83a10"
CRYSTAL = ("#5ae0ff", "#b06aff", "#7affc8")
TIMBER = "#6a4a2e"
TIMBER_DARK = "#4a3220"

CEILING = 50.0
CHASM = (-24.0, 24.0)
BRIDGE_Z = 34.0
LAVA_TOP = -24.0
BURN_Y = -10.0

_CORNERS = [(-360.0, -150.0), (-250.0, -150.0), (-170.0, -60.0), (-60.0, -60.0),
            (60.0, 60.0), (170.0, 60.0), (250.0, 150.0), (360.0, 150.0)]
LANE_A = fillet(_CORNERS, radius=30.0, step=4.0)
LANE_B = mirror(LANE_A)
GALLERIES = ((-150.0, -78.0), (78.0, 150.0))

KEEP: list = []


def _free(area, margin: float = 3.0) -> bool:
    x0, x1, z0, z1 = area
    return all(x1 + margin <= k[0] or x0 - margin >= k[1] or
               z1 + margin <= k[2] or z0 - margin >= k[3] for k in KEEP)


def _lane_free(area, margin: float = 9.0) -> bool:
    return clear_of(area, (LANE_A, LANE_B), margin)


def _dry(x0: float, x1: float, z0: float, z1: float, margin: float = 6.0) -> bool:
    """Clear of the chasm?"""
    return x1 + margin <= CHASM[0] or x0 - margin >= CHASM[1] or \
        (z0 >= -BRIDGE_Z + margin and z1 <= BRIDGE_Z - margin)


def build(b: ArenaArea) -> None:
    rng = random.Random(0x1A47)
    del KEEP[:]
    hz = b.half_z
    chasm = [rect(CHASM[0], CHASM[1], -hz, -BRIDGE_Z), rect(CHASM[0], CHASM[1], BRIDGE_Z, hz)]
    b.extra.update({"accent": "#ffb347", "twist": "firedamp", "drown_y": BURN_Y,
                    "lanes": {"a": _world(b, LANE_A), "b": _world(b, LANE_B)},
                    "names": {"a": "the upper line", "b": "the lower line"}})
    ground(b, FLOOR, soil=ROCK_DARK, material="plastic", holes=chasm)
    _cave(b, rng)
    _chasm(b, rng)
    for path in (LANE_A, LANE_B):
        lay_track(b, path, ballast="#5a5048")
    _yards(b)
    _termini(b)
    _depots(b)
    for kind, (hx, hzz) in (("depot", (24.0, 12.0)), ("lever", (5.0, 5.0))):
        for entry in b.points.get(kind, []):
            x, z = entry["p"][0] - b.ox, entry["p"][2] - b.oz
            KEEP.append(rect(x - hx, x + hx, z - hzz, z + hzz))
    _galleries(b)
    _bridge(b)
    _grotto(b, rng)
    _camp(b, rng)
    _chapel(b)
    _foundry(b, rng)
    _workings(b, rng)
    _glen(b, rng)
    _gas(b)
    _coaling(b, rng)
    _scatter(b, rng)
    telegraph(b, LANE_A, -1.0, every=70.0)
    telegraph(b, LANE_B, 1.0, every=70.0)
    for f, label in ((0.13, "LEVEL 9"), (0.5, "LEVEL 10"), (0.88, "LEVEL 11")):
        mile_post(b, LANE_A, f, -1.0, label)
        mile_post(b, LANE_B, f, 1.0, label)
    for x, z, name in ((-340, -150, "the upper adit"), (-340, 150, "the lower adit"),
                       (340, -150, "Bottom Level"), (340, 150, "Deep Station"),
                       (0, 0, "the Devil's Bridge"), (0, -130, "the north rope bridge"),
                       (0, 130, "the south rope bridge"), (-114, -60, "the upper gallery"),
                       (-114, 60, "the lower gallery"), (-170, -170, "the Crystal Grotto"),
                       (-180, 0, "the miners' camp"), (-170, 175, "the chapel"),
                       (170, 0, "the Foundry"), (170, -175, "the Old Workings"),
                       (175, 175, "the Mushroom Glen")):
        b.landmark(float(x), float(z), name)
    b.camera(-120.0, 36.0, 0.0, 0.0, 0.0, 0.0)
    b.camera(120.0, 34.0, -110.0, 170.0, 4.0, 0.0)
    b.camera(-250.0, 30.0, 110.0, -170.0, 4.0, 175.0)


def _world(b: ArenaArea, path):
    return [b.at(x, 0.0, z) for x, z in path]


# ==================================================================== cave
def _cave(b: ArenaArea, rng: random.Random) -> None:
    """Rock walls to the roof, the roof itself, and the rock's own shapes:
    columns down the walls, stalactites, a few stalagmites."""
    m = b.margin
    hx, hz = b.half_x, b.half_z
    room_walls(b, rect(-hx - m, hx + m, -hz - m, hz + m), m, 0.0, CEILING, ROCK)
    slab(b, rect(-hx - m, hx + m, -hz - m, hz + m), CEILING + 6.0, 6.0, ROCK_DARK)
    # the walls' inner faces broken up by columns and shelves of rock
    for side in ("x-", "x+", "z-", "z+"):
        along_x = side in ("z-", "z+")
        span = 2 * (hx if along_x else hz)
        count = int(span // 34)
        sign = -1.0 if side.endswith("-") else 1.0
        for i in range(count):
            u = -span / 2.0 + (i + 0.5) * span / count + rng.uniform(-5, 5)
            d = rng.uniform(4.0, 10.0)
            w = rng.uniform(10.0, 20.0)
            at = sign * ((hz if along_x else hx) - d / 2.0)
            x, z = (u, at) if along_x else (at, u)
            spot = rect(x - (w if along_x else d) / 2.0, x + (w if along_x else d) / 2.0,
                        z - (d if along_x else w) / 2.0, z + (d if along_x else w) / 2.0)
            if not _free(spot, 2.0) or not _lane_free(spot, 8.0) or not _dry(*spot, 2.0):
                continue
            size = [w, CEILING, d] if along_x else [d, CEILING, w]
            b.box([x, CEILING / 2.0, z], size, rng.choice([ROCK, ROCK_DARK, ROCK_LIGHT]))
    # stalactites over everything, well above anybody's head
    for k in range(120):
        x, z = rng.uniform(-hx + 6, hx - 6), rng.uniform(-hz + 6, hz - 6)
        h = rng.uniform(4.0, 14.0)
        w = rng.uniform(2.0, 5.0)
        b.cone([x, CEILING - h / 2.0, z], [w, h, w * rng.uniform(0.8, 1.2)],
               rng.choice([ROCK, ROCK_LIGHT, ROCK_DARK]), r=[math.pi, 0, 0], collide=False)
    # the roof's own lights: crystal seams that glow through the dark
    for k in range(40):
        x, z = rng.uniform(-hx + 10, hx - 10), rng.uniform(-hz + 10, hz - 10)
        b.box([x, CEILING - 0.1, z], [rng.uniform(4, 12), 0.2, rng.uniform(0.6, 1.4)],
              rng.choice(CRYSTAL), material="neon", collide=False, r=[0, rng.uniform(0, 3.1), 0])


# ================================================================== chasm
def _chasm(b: ArenaArea, rng: random.Random) -> None:
    """Lava thirty down, the chasm's walls lined to the bottom, the rock
    closing its ends under the cave wall, and two rope bridges."""
    hz = b.half_z
    holes = [rect(CHASM[0], CHASM[1], -hz, -BRIDGE_Z), rect(CHASM[0], CHASM[1], BRIDGE_Z, hz)]
    laid = []
    for h in holes:
        x0, x1, z0, z1 = h
        for r in (rect(x0 - 4.0, x0, z0 - 4.0, z1 + 4.0), rect(x1, x1 + 4.0, z0 - 4.0, z1 + 4.0),
                  rect(x0, x1, z0 - 4.0, z0), rect(x0, x1, z1, z1 + 4.0)):
            for p in carve(r, holes + laid):
                slab(b, p, -6.0, 24.0, ROCK_DARK)
                laid.append(p)
        slab(b, h, LAVA_TOP, 4.0, LAVA, material="neon")
        # crusts floating on the lava
        for k in range(8):
            cz = rng.uniform(z0 + 6.0, z1 - 6.0)
            b.box([rng.uniform(x0 + 5.0, x1 - 5.0), LAVA_TOP + 0.05 + k * 0.002, cz],
                  [rng.uniform(4, 9), 0.1, rng.uniform(3, 7)], "#3a2420", collide=False)
        # the glow up the walls
        for x, e in ((x0, 1.0), (x1, -1.0)):
            b.box([x + e * 0.03, LAVA_TOP + 3.0, (z0 + z1) / 2.0], [0.06, 4.0, z1 - z0 - 0.2],
                  "#ff8a3a", material="neon", collide=False)
    # the rope bridges, a step up from the edge, posts at both ends
    for z in (-130.0, 130.0):
        slab(b, rect(CHASM[0] - 4.0, CHASM[1] + 4.0, z - 2.2, z + 2.2), 0.4, 0.4, TIMBER,
             studs=True)
        for x in (CHASM[0] - 3.0, CHASM[1] + 3.0):
            for e in (-1.0, 1.0):
                b.box([x, 2.0, z + e * 2.0], [0.6, 4.0, 0.6], TIMBER_DARK)
        for e in (-1.0, 1.0):
            b.box([0.0, 3.0, z + e * 2.0], [CHASM[1] - CHASM[0] + 5.4, 0.25, 0.25], "#c8a070")
            for x in range(int(CHASM[0]), int(CHASM[1]) + 1, 4):
                b.box([x, 1.7, z + e * 2.0], [0.15, 2.6, 0.15], "#c8a070")
        KEEP.append(rect(CHASM[0] - 6.0, CHASM[1] + 6.0, z - 4.0, z + 4.0))
    KEEP.append(rect(CHASM[0] - 6.0, CHASM[1] + 6.0, -hz, -BRIDGE_Z + 2.0))
    KEEP.append(rect(CHASM[0] - 6.0, CHASM[1] + 6.0, BRIDGE_Z - 2.0, hz))


# ================================================================= bridge
def _bridge(b: ArenaArea) -> None:
    """The Devil's Bridge: the rock span the lines cross on, with the lamp
    statues at its free corners and arches of rock under its edges."""
    for x, z in ((-16.0, 16.0), (16.0, -16.0)):
        b.box([x, 1.0, z], [6.0, 2.0, 6.0], ROCK_LIGHT)
        b.box([x, 4.6, z], [2.6, 5.2, 2.0], "#8a7a6a")
        b.box([x, 8.0, z], [1.8, 1.6, 1.6], "#c8a070")
        b.box([x, 8.95, z], [2.0, 0.3, 1.8], "#5a4a3a")
        b.box([x + 1.9, 6.6, z], [1.2, 0.6, 0.6], "#8a7a6a")
        lantern(b, x + 2.4, 6.6, z, WARM)
        b.box([x + 2.4, 6.75, z], [0.3, 0.3, 0.3], rails.IRON, collide=False)
    for z, e in ((-BRIDGE_Z, -1.0), (BRIDGE_Z, 1.0)):
        b.box([0.0, -12.0, z + e * 1.0], [CHASM[1] - CHASM[0], 12.0, 2.0], ROCK_LIGHT)
    rails.gold_sign(b, -30.0, 4.0, -26.0, 14.0, 2.2, "DEVIL'S BRIDGE", "z+")
    KEEP.append(rect(-34.0, 34.0, -BRIDGE_Z - 2.0, BRIDGE_Z + 2.0))


# =================================================================== yards
def _adit(b: ArenaArea, z: float) -> None:
    """A timbered tunnel mouth in the west wall with daylight at its end."""
    x = -b.half_x
    for e in (-1.0, 1.0):
        b.box([x + 1.0, 8.0, z + e * 9.0], [2.0, 16.0, 2.0], TIMBER)
    b.box([x + 1.0, 16.8, z], [2.0, 1.6, 20.0], TIMBER)
    b.box([x + 0.03, 8.0, z], [0.06, 16.0, 16.0], "#fff4d8", material="neon", collide=False)


def _yards(b: ArenaArea) -> None:
    for lane, z, side, name, roof in (("a", -150.0, -1.0, "UPPER ADIT", "#7a3a22"),
                                      ("b", 150.0, 1.0, "LOWER ADIT", "#2a3a5a")):
        area = yard(b, lane, -376.0, -322.0, z, side, name, roof, sign=(rails.CREAM, "#2a1a10"))
        _adit(b, z + side * 34.0)
        KEEP.append(rect(-380.0, -300.0, min(z, area[2]) - 14.0, max(z, area[3]) + 26.0))
    # a train of ore cars waits on the stub between the adits
    lay_track(b, [(-380.0, 0.0), (-290.0, 0.0)], ballast="#5a5048")
    buffer_stop(b, -376.0, 0.0, math.pi / 2.0, rails.RED)
    buffer_stop(b, -294.0, 0.0, math.pi / 2.0, rails.RED)
    for k, x in enumerate((-360.0, -344.0, -328.0, -312.0)):
        _ore_car(b, x, 0.0, "#8a8a92" if k % 2 else "#e8b23a")
    KEEP.append(rect(-382.0, -288.0, -6.0, 6.0))


def _ore_car(b: ArenaArea, x: float, z: float, load: str) -> None:
    """A tipping ore car, solid, its load heaped in it."""
    b.box([x, 0.9, z], [4.0, 0.9, 3.6], rails.IRON, material="metal")
    b.box([x, 2.6, z], [6.0, 2.6, 4.6], "#5a5550", material="metal")
    b.box([x, 4.2, z], [5.0, 0.6, 3.6], load, studs=True)


def _termini(b: ArenaArea) -> None:
    for lane, z, side, name, roof in (("a", 150.0, 1.0, "DEEP STATION", "#2a3a5a"),
                                      ("b", -150.0, -1.0, "BOTTOM LEVEL", "#7a3a22")):
        area = yard(b, lane, 322.0, 376.0, z, side, name, roof, sign=(rails.GOLD, "#2a1a10"),
                    end="finish")
        # the cage of the main shaft behind the station: a lift to nowhere
        cx, cz = 364.0, z + side * 40.0
        for dx in (-6.0, 6.0):
            for dz in (-6.0, 6.0):
                b.box([cx + dx, CEILING / 2.0, cz + dz], [1.4, CEILING, 1.4], rails.IRON,
                      material="metal")
        b.box([cx, 4.0, cz], [9.0, 8.0, 9.0], "#4a4642", material="metal")
        b.box([cx, 4.0, cz - side * 4.52], [5.0, 6.0, 0.04], "#ffd27a", material="neon",
              collide=False)
        wall_sign(b, cx, 10.0, cz - side * 4.85, 10.0, 1.6,
                  sign_decal("MAIN SHAFT", rails.CREAM, "#2a1a10", 6.2),
                  "z-" if side > 0 else "z+", rails.CREAM)
        KEEP.append(rect(300.0, 380.0, min(z, area[2]) - 10.0, max(z, area[3]) + 10.0))
        KEEP.append(rect(cx - 8.0, cx + 8.0, cz - 8.0, cz + 8.0))


def _depots(b: ArenaArea) -> None:
    depot(b, "a", LANE_A, 0.3, 1.0, "LEVEL 9 STATION", 1, "#7a3a22")
    depot(b, "a", LANE_A, 0.7, -1.0, "FOUNDRY HALT", 2, "#2a3a5a")
    depot(b, "b", LANE_B, 0.3, -1.0, "LEVEL 9 SOUTH", 1, "#2a3a5a")
    depot(b, "b", LANE_B, 0.7, 1.0, "WORKINGS HALT", 2, "#7a3a22")
    for lane, path, sides in (("a", LANE_A, (1.0, -1.0)), ("b", LANE_B, (-1.0, 1.0))):
        for index, (f, side) in enumerate(zip((0.42, 0.77), sides)):
            lever(b, lane, path, f, side, index)


# =============================================================== galleries
def _galleries(b: ArenaArea) -> None:
    """Both lines run through a timbered gallery either side of the chasm:
    props both sides every eight units, a cap over the track, lanterns
    hung from the caps."""
    for x0, x1 in GALLERIES:
        for z in (-60.0, 60.0):
            n = int((x1 - x0) // 8.0)
            for i in range(n + 1):
                x = x0 + i * (x1 - x0) / n
                for e in (-1.0, 1.0):
                    b.box([x, 6.0, z + e * 7.5], [1.2, 12.0, 1.2], TIMBER)
                b.box([x, 12.6, z], [1.4, 1.2, 16.4], TIMBER_DARK)
                if i % 2 == 1:
                    lantern(b, x, 12.0, z, WARM)
            for e in (-1.0, 1.0):
                b.box([(x0 + x1) / 2.0, 13.6, z + e * 7.5], [x1 - x0 + 1.2, 0.8, 1.2], TIMBER)
            KEEP.append(rect(x0 - 2.0, x1 + 2.0, z - 9.0, z + 9.0))


# ================================================================== grotto
def _grotto(b: ArenaArea, rng: random.Random) -> None:
    """The Crystal Grotto, north-west: clusters of glowing crystal, solid,
    big enough to hide behind, and a still pool under them."""
    pool = rect(-200.0, -160.0, -214.0, -190.0)
    b.box([-180.0, 0.03, -202.0], [40.0, 0.06, 24.0], "#2a5a7a", collide=False)
    for k in range(9):
        cx = rng.uniform(-250.0, -110.0)
        cz = rng.uniform(-222.0, -168.0)
        spot = rect(cx - 7.0, cx + 7.0, cz - 7.0, cz + 7.0)
        if not _lane_free(spot) or not _free(spot, 1.0) or \
                (spot[1] > pool[0] and spot[0] < pool[1] and spot[3] > pool[2] and spot[2] < pool[3]):
            continue
        colour = rng.choice(CRYSTAL)
        b.box([cx, 1.0, cz], [10.0, 2.0, 10.0], ROCK_LIGHT)
        for j in range(5):
            h = rng.uniform(5.0, 14.0)
            w = rng.uniform(1.6, 3.0)
            px = cx + rng.uniform(-3.0, 3.0)
            pz = cz + rng.uniform(-3.0, 3.0)
            b.box([px, 2.0 + h / 2.0, pz], [w, h, w], colour, material="neon")
            b.cone([px, 2.0 + h + w * 0.6, pz], [w, w * 1.2, w], colour, material="neon")
        KEEP.append(spot)
    KEEP.append(pool)


# ==================================================================== camp
def _camp(b: ArenaArea, rng: random.Random) -> None:
    """The miners' camp between the west galleries: shacks, the canteen,
    a rail-cart repair shed, and lanterns on poles."""
    for x, z, w, d, name in ((-230.0, -26.0, 22.0, 16.0, "CANTEEN"),
                             (-230.0, 26.0, 20.0, 14.0, "BUNKS"),
                             (-182.0, -16.0, 14.0, 12.0, "TOOLS"),
                             (-182.0, 22.0, 14.0, 12.0, "POWDER")):
        area = rect(x - w / 2.0, x + w / 2.0, z - d / 2.0, z + d / 2.0)
        if not _lane_free(area) or not _free(area, 2.0):
            continue
        face = "z+" if z < 0 else "z-"
        building(b, area, 0.0, 8.0, TIMBER, roof_colour="#3a2a1e", floor_colour="#5a4632",
                 doors={face: [(x - 2.0, x + 2.0, 6.6)]},
                 windows={face: [(x + 3.0, x + w / 2.0 - 2.0, 3.0, 5.6)]}, glass=True,
                 lights=WARM, boards=True)
        threshold(b, area, face, (x - 2.0, x + 2.0))
        sz = area[3] + 0.05 if face == "z+" else area[2] - 0.05
        wall_sign(b, x - w / 4.0, 7.4, sz, w / 2.2, 1.2,
                  sign_decal(name, rails.CREAM, "#2a1a10", w / 2.2 / 1.2), face, rails.CREAM)
        KEEP.append(area)
    for x, z in ((-206.0, 0.0), (-160.0, 0.0), (-250.0, 0.0)):
        lantern(b, x, 0.0, z, WARM, post=9.0)
        KEEP.append(rect(x - 1.0, x + 1.0, z - 1.0, z + 1.0))
    wagon(b, -270.0, -60.0, "x", "#c8b898")
    KEEP.append(rect(-277.0, -263.0, -64.0, -56.0))


# ================================================================= chapel
def _chapel(b: ArenaArea) -> None:
    """St. Barbara's chapel, south-west: the miners' saint, candles, pews."""
    area = rect(-196.0, -150.0, 160.0, 196.0)
    building(b, area, 0.0, 14.0, "#8a7a6a", roof_colour="#3a3030", floor_colour="#6a5a4a",
             doors={"z-": [(-178.0, -168.0, 10.0)]},
             windows={"x-": [(168.0, 174.0, 5.0, 10.0), (182.0, 188.0, 5.0, 10.0)],
                      "x+": [(168.0, 174.0, 5.0, 10.0), (182.0, 188.0, 5.0, 10.0)]},
             glass=True, lights="#ffd27a")
    threshold(b, area, "z-", (-178.0, -168.0))
    from ..kit import gable
    gable(b, area, 15.2, "#3a3030", "z", 4, 1.4, 0.8)
    b.box([-173.0, 22.0, 163.0], [6.0, 12.0, 6.0], "#8a7a6a")
    b.cone([-173.0, 31.0, 163.0], [7.0, 6.0, 7.0], "#3a3030", collide=False)
    for k in range(4):
        z = 172.0 + k * 5.0
        for x in (-186.0, -160.0):
            b.box([x, 0.4 + 0.75, z], [10.0, 1.5, 1.4], TIMBER)
    b.box([-173.0, 1.6, 192.0], [10.0, 3.2, 3.0], "#c8b8a0")
    b.box([-173.0, 5.0, 193.2], [2.0, 3.6, 1.0], "#e8d8c0")
    for k in range(7):
        b.box([-178.0 + k * 1.6, 3.4, 191.0], [0.3, 0.4, 0.3], "#ffd27a", material="neon")
    wall_sign(b, -173.0, 12.4, 159.65, 18.0, 1.6,
              sign_decal("ST. BARBARA", rails.CREAM, "#2a1a10", 11.2), "z-", rails.CREAM)
    KEEP.append(rect(area[0] - 2.0, area[1] + 2.0, area[2] - 3.0, area[3] + 2.0))


# ================================================================= foundry
def _foundry(b: ArenaArea, rng: random.Random) -> None:
    """The Foundry, east of the chasm between the lines: a hall of
    furnaces, its stacks up into the roof, lava troughs out front."""
    hall = rect(196.0, 260.0, -26.0, 26.0)
    building(b, hall, 0.0, 22.0, "#5a4a42", roof_colour="#2e2622", floor_colour="#3a3230",
             doors={"x-": [(-8.0, 8.0, 14.0)], "x+": [(-6.0, 6.0, 12.0)]},
             windows={"z-": [(204.0, 220.0, 10.0, 16.0), (236.0, 252.0, 10.0, 16.0)],
                      "z+": [(204.0, 220.0, 10.0, 16.0), (236.0, 252.0, 10.0, 16.0)]},
             glass=False, lights="#ffb35a")
    threshold(b, hall, "x-", (-8.0, 8.0))
    threshold(b, hall, "x+", (-6.0, 6.0))
    for x in (212.0, 244.0):
        b.box([x, 4.0, -12.0], [12.0, 8.0, 10.0], "#3a3230")
        b.box([x, 3.0, -6.96], [6.0, 4.0, 0.08], LAVA, material="neon", collide=False)
        b.box([x, (23.2 + CEILING) / 2.0, -12.0], [5.0, CEILING - 23.2, 5.0], "#5a3a2e")
    for k in range(3):
        b.box([206.0 + k * 22.0, 1.6, 14.0], [6.0, 3.2, 4.0], "#4a4642", material="metal")
    wall_sign(b, 195.65, 18.0, 0.0, 30.0, 3.0,
              sign_decal("LANTERN CO. FOUNDRY", "#2a1a10", rails.GOLD, 10.0), "x-", "#2a1a10")
    KEEP.append(rect(hall[0] - 4.0, hall[1] + 4.0, hall[2] - 2.0, hall[3] + 2.0))
    # the lava troughs between the hall and the chasm, a bridge plank over each
    for z in (-14.0, 14.0):
        for r in (rect(150.0, 186.0, z - 3.0, z - 2.0), rect(150.0, 186.0, z + 2.0, z + 3.0)):
            slab(b, r, 1.2, 1.2, "#5a4a42")
        b.box([168.0, 0.3, z], [36.0, 0.6, 4.0], LAVA, material="neon", collide=False)
        KEEP.append(rect(148.0, 188.0, z - 4.0, z + 4.0))


# ================================================================ workings
def _workings(b: ArenaArea, rng: random.Random) -> None:
    """The Old Workings, north-east: a headframe over a shaft, scaffold
    decks at two heights joined by stairs -- the high ground east of the
    chasm -- and ore cars on a spur."""
    hx, hz = 176.0, -186.0
    for dx in (-8.0, 8.0):
        for dz in (-8.0, 8.0):
            b.box([hx + dx, 17.0, hz + dz], [1.4, 34.0, 1.4], TIMBER_DARK)
    slab(b, rect(hx - 10.0, hx + 10.0, hz - 10.0, hz + 10.0), 14.0, 0.8, TIMBER)
    slab(b, rect(hx - 10.0, hx + 4.0, hz - 10.0, hz + 10.0), 28.0, 0.8, TIMBER)
    b.cyl([hx, 37.0, hz], [9.0, 0.9, 9.0], rails.IRON, r=[0, 0, math.pi / 2.0],
          collide=False, material="metal")
    b.box([hx, 34.4, hz], [1.0, 1.0, 1.0], rails.IRON, material="metal")
    stair(b, "x", hx - 34.0, hx - 10.0, hz - 3.0, hz + 3.0, 0.0, 14.0, TIMBER)
    stair(b, "z", hz + 10.0, hz - 10.0, hx + 4.0, hx + 10.0, 14.0, 28.0, TIMBER)
    for e in (-1.0, 1.0):
        b.box([hx, 15.3, hz + e * 9.6], [20.0, 0.3, 0.3], TIMBER_DARK)
        b.box([hx - 3.0, 29.3, hz + e * 9.6], [14.0, 0.3, 0.3], TIMBER_DARK)
    lantern(b, hx, 27.2, hz, WARM)
    b.mark("perch", hx, 14.0, hz)
    b.mark("perch", hx, 28.0, hz)
    KEEP.append(rect(hx - 36.0, hx + 36.0, hz - 12.0, hz + 12.0))
    # the shaft's spur, ore cars and a handcar on it
    lay_track(b, [(110.0, -214.0), (250.0, -214.0)], ballast="#5a5048")
    buffer_stop(b, 112.0, -214.0, math.pi / 2.0, rails.RED)
    buffer_stop(b, 248.0, -214.0, math.pi / 2.0, rails.RED)
    for k, x in enumerate((128.0, 144.0, 214.0)):
        _ore_car(b, x, -214.0, "#e8b23a" if k == 1 else "#8a8a92")
    handcar(b, 232.0, -214.0, "x")
    KEEP.append(rect(108.0, 252.0, -219.0, -209.0))


# ==================================================================== glen
def _glen(b: ArenaArea, rng: random.Random) -> None:
    """The Mushroom Glen, south-east: giant glowing toadstools, stalks you
    hide behind, caps far over your head."""
    for k in range(16):
        x = rng.uniform(96.0, 290.0)
        z = rng.uniform(150.0, 222.0)
        s = rng.uniform(0.9, 1.8)
        spot = rect(x - 6.0 * s, x + 6.0 * s, z - 6.0 * s, z + 6.0 * s)
        if not _lane_free(spot, 7.0) or not _free(spot, 1.0) or not _dry(*spot):
            continue
        h = 8.0 * s + 2.0
        b.cyl([x, h / 2.0, z], [2.2 * s, h, 2.2 * s], "#e8dcc8")
        cap = rng.choice(["#ff5a8a", "#5affd2", "#ffb347", "#a07aff"])
        b.sphere([x, h + 1.4 * s, z], [11.0 * s, 4.0 * s, 11.0 * s], cap, collide=False,
                 material="neon")
        b.cyl([x, h - 0.3, z], [10.6 * s, 0.3, 10.6 * s], "#f4ece0", collide=False)
        KEEP.append(spot)
    for k in range(24):
        x = rng.uniform(96.0, 290.0)
        z = rng.uniform(110.0, 224.0)
        spot = rect(x - 1.5, x + 1.5, z - 1.5, z + 1.5)
        if not _lane_free(spot, 6.0) or not _free(spot, 0.5) or not _dry(*spot):
            continue
        b.cyl([x, 0.6, z], [0.8, 1.2, 0.8], "#e8dcc8")
        b.sphere([x, 1.5, z], [2.4, 1.0, 2.4], rng.choice(["#ff5a8a", "#5affd2"]),
                 material="neon")
        KEEP.append(spot)


# ===================================================================== gas
def _gas(b: ArenaArea) -> None:
    """Where firedamp gathers: low hollows marked by the miners' warning
    boards (the rules vent them one after another)."""
    for x, z in ((-120.0, -110.0), (-120.0, 110.0), (120.0, -110.0), (120.0, 110.0),
                 (-280.0, -70.0), (290.0, 70.0)):
        b.box([x, 0.03, z], [16.0, 0.06, 16.0], "#3a4a2a", collide=False)
        post = (x + 9.0, z)
        b.box([post[0], 2.0, post[1]], [0.5, 4.0, 0.5], TIMBER_DARK)
        b.box([post[0], 4.6, post[1]], [3.6, 1.4, 0.3], "#e8c83a",
              decal=sign_decal("FIREDAMP", "#e8c83a", "#2a1a10", 2.6))
        b.mark("gas", x, 1.0, z)


# ================================================================ coaling
def _coaling(b: ArenaArea, rng: random.Random) -> None:
    for x, z in ((-60.0, 0.0), (60.0, 0.0), (-250.0, -100.0), (250.0, 100.0)):
        coal_heap(b, x, z, rng)
        KEEP.append(rect(x - 5.0, x + 5.0, z - 5.0, z + 5.0))


# ================================================================ scatter
def _scatter(b: ArenaArea, rng: random.Random) -> None:
    """Stalagmites, fallen rock, timber, the track gang's leavings."""
    for k in range(40):
        x = rng.uniform(-360.0, 360.0)
        z = rng.uniform(-220.0, 220.0)
        w = rng.uniform(3.0, 7.0)
        spot = rect(x - w, x + w, z - w, z + w)
        if not _lane_free(spot, 8.0) or not _free(spot) or not _dry(*spot):
            continue
        if abs(x) > b.half_x - w - 2 or abs(z) > b.half_z - w - 2:
            continue
        if k % 2:
            h = rng.uniform(6.0, 16.0)
            b.cone([x, h / 2.0, z], [w * 1.4, h, w * 1.4], rng.choice([ROCK, ROCK_LIGHT]))
            b.box([x, 1.0, z], [w * 1.2, 2.0, w * 1.2], ROCK)
        else:
            rock(b, x, z, w * 1.4, rng.uniform(3.0, 7.0), w * 1.1,
                 rng.choice([ROCK, ROCK_DARK, ROCK_LIGHT]))
        KEEP.append(spot)
    total = length(LANE_A)
    for f, side in ((0.06, 1.0), (0.2, -1.0), (0.55, 1.0), (0.82, -1.0), (0.95, 1.0)):
        for path, sgn in ((LANE_A, 1.0), (LANE_B, -1.0)):
            x, z, _ = beside(path, total * f, side * sgn * 12.0)
            x, z = round(x), round(z)
            spot = rect(x - 3.0, x + 3.0, z - 3.0, z + 3.0)
            if _lane_free(spot, 7.0) and _free(spot) and _dry(*spot):
                if (f * 100) % 2 < 1:
                    sleeper_pile(b, x, z, "x", 3)
                else:
                    barrel(b, x, z, "#5a5a64")
                    crate_stack(b, x + 3.0, z, rng)
                KEEP.append(spot)
