"""Thunderhead Rock: a storm-lashed island of black basalt under a purple
sky -- a sheer-sided mesa with a lighthouse on top, a causeway of six-sided
columns stepping down from its summit like a giant's stair, a sea cave
straight through its foot, a wreck broken in two on the south strand and,
either side, the wreckers' village that put her there.

Layout (north is -z; the Scarlet Corsairs' ship off the west shore, the
Azure Buccaneers' off the east)::

    z -120  ===== cliffs ===== THE MESA: crags, THE LIGHTHOUSE ===== cliffs =====
    z  -91   cave mouth  ===== the sea cave, right through ======  cave mouth
    z  -68   stair up   the summit: shelters, THE IDOL (altar)   stair up
    z  -44   the stair's foot    THE GIANT'S CAUSEWAY               the stair's foot
   SCARLET   wreckers'        (columns stepping down             wreckers'  BLUE
    QUEEN    light, cottages    to the strand)                   light,     MARLIN
    z   54   cottages          the wreck of the Siren, in two    cottages
    z   84   tide pool          the wreckers' beacon             tide pool
    z  100  ~~~~~~~~~~~~~~~~~~~~~~~~ the south sea ~~~~~~~~~~~~~~~~~~~~~~~~~

The halves are mirror images.  The summit, the causeway, the cave and the
wreck are as far from one ship as the other.

The twist is the storm (``extra["twist"] = "storm"``): the sky opens and
lightning strikes over and over -- and it seeks out metal, so whoever is
carrying gold or jewels is struck first.  Under a roof (a cottage, a summit
shelter, the cave, the wreck's deck) nothing can reach you; out on the
summit with the idol in your arms, everything can.
"""
from __future__ import annotations

import math
import random

from ..calamity_coast.town import skirt
from ..kit import ArenaArea, backdrop, flight, rect, slab
from .common import IRON, PLANK, SEA_TOP, SEABED, SHIP_X, SHORE_X, TIMBER, Isle, galleon

HALF = (170.0, 120.0)
SKY = {"top": "#28243e", "horizon": "#8e88a8", "sun": [0.25, 0.45, -0.5], "clouds": 0.95,
       "tint": "#ccc6ea"}
AMBIENT = "#a0a0bc"
GROUND = "#4a7a44"
FOG = 640.0

TURF = "#4a7a44"
TURF_TOP = "#5a8a4e"
PATH = "#8a8478"
SHINGLE = "#8a8a94"
BASALT = "#3c3c48"
BASALT_LIGHT = "#50505e"
BASALT_DARK = "#2c2c36"
MOSS = "#6a9a4a"
LICHEN = "#e8a03a"
STONE = "#9a948a"
ROPE_C = "#c8a878"
CRYSTAL = "#7ab8ff"
SOUTH = 100.0
NORTH = -100.0               # the foot of the north cliffs either side of the mesa
MESA = (-36.0, 36.0, -112.0, -44.0)
TOP = 18.0                   # the summit
TURF_Y = TOP + 0.15
TUNNEL = (-96.0, -86.0)      # the sea cave's z band, right through the mesa
CAVE_H = 8.0
TOWER = (0.0, -86.0)
IDOL = (0.0, -68.0)
R = 2.2                      # a basalt column's circumradius
FLAT = R * math.sqrt(3.0)
STAIR = (36.0, 44.0)         # the side stairs' x band (east; mirrored west)
STAIR_Z = (-44.0, -80.0)
SHELTER = (14.0, 24.0, -66.0, -56.0)
COTTAGES = (((68.0, 84.0, -40.0, -28.0), "z+"), ((86.0, 102.0, -8.0, 8.0), "x-"),
            ((66.0, 80.0, 30.0, 42.0), "z-"))
LIGHT_E = (90.0, 100.0, -64.0, -52.0)      # the wreckers' light (east; mirrored)
WRECK = (4.0, 26.0, 46.0, 62.0)            # one half of the wreck (east; mirrored)
POOLS = ((46.0, 86.0, 6.0),)
KNOLLS = ((38.0, 52.0, -30.0, -16.0), (70.0, 86.0, 46.0, 62.0), (28.0, 44.0, 4.0, 18.0))
HENGE = (0.0, 22.0, 13.0)    # the storm henge: its centre and its ring's radius
HEATHER = ((62.0, 80.0, -88.0, -72.0), (36.0, 52.0, 40.0, 54.0), (76.0, 96.0, 70.0, 86.0))
GORSE = ((70.0, 86.0, -24.0, -16.0), (88.0, 98.0, 22.0, 30.0), (14.0, 26.0, 74.0, 86.0))
# the causeway's landings: a ring of columns all one height round each of
# these (column, row) cells, somewhere to stand on the way up
LANDINGS = ((0, 3), (-4, 6), (4, 6))


def _m(r):
    x0, x1, z0, z1 = r
    return (-x1, -x0, z0, z1)


def _col(b: ArenaArea, x: float, z: float, y0: float, h: float, colour: str, collide: bool = True,
         r: float = R) -> None:
    """A basalt column: a six-sided prism standing on ``y0``, ``h`` tall."""
    b.add("hexprism", [x, y0 + h / 2.0, z], [2.0 * r, h, r * math.sqrt(3.0)], colour, collide=collide)


# ================================================================ the land
def _land(isle: Isle) -> None:
    b = isle.b
    hx, hz = HALF
    m = b.margin
    west = (-hx - m, -SHORE_X, -hz - m, hz + m)
    east = (SHORE_X, hx + m, -hz - m, hz + m)
    south = (-SHORE_X, SHORE_X, SOUTH, hz + m)
    pools = [rect(x - r, x + r, z - r, z + r) for x, z, r in POOLS] + \
            [rect(-x - r, -x + r, z - r, z + r) for x, z, r in POOLS]
    isle.land(TURF, holes=[west, east, south] + pools, soil="#4a3e34")
    for area in (west, east, south):
        slab(b, area, SEABED, 3.0, "#5a5a64", studs=True)
    # shingle beaches down into the sea
    for k, top in enumerate((-1.0, -2.0)):
        colour = SHINGLE if k == 0 else "#6c6c76"
        for sgn in (-1.0, 1.0):
            xa, xb = sorted((sgn * (SHORE_X + 3.0 * k), sgn * (SHORE_X + 3.0 * (k + 1))))
            b.box([(xa + xb) / 2.0, (SEABED + top) / 2.0, (NORTH + hz) / 2.0],
                  [xb - xa, top - SEABED, hz - NORTH], colour, studs=True)
        za, zb = SOUTH + 3.0 * k, SOUTH + 3.0 * (k + 1)
        b.box([0.0, (SEABED + top) / 2.0, (za + zb) / 2.0], [2 * SHORE_X, top - SEABED, zb - za], colour,
              studs=True)
    for area in ((-hx, -SHORE_X, -hz, hz), (SHORE_X, hx, -hz, hz), (-SHORE_X, SHORE_X, SOUTH, hz)):
        isle.water(area, SEABED, colour="#2a5a6e", alpha=0.62)
    for x0, x1, z0, z1 in ((-hx - m - 300.0, -hx - m, -hz - m - 300.0, hz + m + 300.0),
                           (hx + m, hx + m + 300.0, -hz - m - 300.0, hz + m + 300.0),
                           (-hx - m, hx + m, hz + m, hz + m + 300.0)):
        b.box([(x0 + x1) / 2.0, (SEABED - 6.0 + SEA_TOP) / 2.0, (z0 + z1) / 2.0],
              [x1 - x0, SEA_TOP - SEABED + 6.0, z1 - z0], "#24505e", material="glass", alpha=0.65,
              collide=False)
    # the tide pools
    for x, z, r in POOLS:
        for sgn in (-1.0, 1.0):
            pr = rect(sgn * x - r, sgn * x + r, z - r, z + r)
            slab(b, pr, -1.4, 3.0, "#5a5a64", studs=True)
            isle.water(pr, -1.4, -0.4, colour="#3a8a9a", alpha=0.6)
    # grassy knolls, a step and another
    for sgn in (-1.0, 1.0):
        for r in KNOLLS:
            xa, xb = sorted((sgn * r[0], sgn * r[1]))
            for k in range(2):
                inset = k * 2.5
                b.box([(xa + xb) / 2.0, 0.4 * (k + 1), (r[2] + r[3]) / 2.0],
                      [xb - xa - 2 * inset, 0.8 * (k + 1), r[3] - r[2] - 2 * inset], TURF if k else TURF_TOP,
                      studs=True)
    # covers: kept off what stands on the turf; the paths first, then the
    # cave's shingle floor and the beaches round them
    s = isle.s
    keep = [(MESA[0], MESA[1], MESA[2], TUNNEL[0]), (MESA[0], MESA[1], TUNNEL[1], MESA[3]), (STAIR[0], STAIR[1], STAIR_Z[1], STAIR_Z[0]), _m((STAIR[0], STAIR[1], STAIR_Z[1], STAIR_Z[0])),
            LIGHT_E, _m(LIGHT_E), WRECK, _m(WRECK), (-31.9, 31.9, -44.0, -2.0), (-3.0, 3.0, 80.0, 88.0),
            (HENGE[0] - 16.0, HENGE[0] + 16.0, HENGE[1] - 16.0, HENGE[1] + 16.0)]
    keep += [c for c, _d in COTTAGES] + [_m(c) for c, _d in COTTAGES]
    keep += list(KNOLLS) + [_m(k) for k in KNOLLS]
    for r in keep:
        s.reserve(r)
    for sgn in (-1.0, 1.0):
        def X(x: float, sgn: float = sgn) -> float:
            return sgn * x
        isle.trail([(X(109.5), -15.0), (X(58.0), -15.0), (X(58.0), -91.0), (X(40.0), -91.0)], colour=PATH)
        isle.trail([(X(58.0), -38.0), (X(40.0), -38.0)], colour=PATH)
        isle.trail([(X(109.5), 15.0), (X(60.0), 15.0), (X(60.0), 70.0), (X(30.0), 70.0)], colour=PATH)
    for x0, x1, z0, z1 in ((-SHORE_X, -100.0, NORTH, SOUTH), (100.0, SHORE_X, NORTH, SOUTH),
                           (-100.0, 100.0, 92.0, SOUTH), (-36.0, 36.0, -96.0, -86.0)):
        s.lay(rect(x0, x1, z0, z1), 0.1, SHINGLE)
    # heather and gorse, purple and yellow, in patches over the turf
    for patches, colour in ((HEATHER, "#9a62a8"), (GORSE, "#e8b832")):
        for r in patches:
            for rr in (r, _m(r)):
                s.lay(rect(*rr), 0.12, colour)


# =============================================================== the edges
def _edges(isle: Isle) -> None:
    b = isle.b
    hx, hz = HALF
    rng = isle.rng
    m = b.margin
    rocks = (BASALT, BASALT_DARK, BASALT_LIGHT, "#34343e")
    for sgn in (-1.0, 1.0):
        a0, a1 = sorted((sgn * 36.0, sgn * SHORE_X))
        isle.cliffs("x", a0, a1, -hz - m, NORTH, rng.uniform(24.0, 28.0), rocks, green=MOSS, vines=False)
        a0, a1 = sorted((sgn * SHORE_X, sgn * (hx + m)))
        isle.cliffs("x", a0, a1, -hz - m, NORTH, 34.0, rocks, base=SEABED, green=MOSS, step=14.5,
                    recess=0.0, vines=False)
        b.box([sgn * (hx + m / 2.0), (SEABED + 6.0) / 2.0, (NORTH + hz + m) / 2.0],
              [m, 6.0 - SEABED, hz + m - NORTH], BASALT)
    b.box([0.0, (SEABED + 6.0) / 2.0, hz + m / 2.0], [2 * hx, 6.0 - SEABED, m], BASALT)
    # the reefs' broken tops: basalt columns standing out of the sea
    for k in range(20):
        z = NORTH + (k + 0.5) * (hz + m - NORTH) / 20.0
        for sgn in (-1.0, 1.0):
            _col(b, sgn * (hx + m / 2.0) + rng.uniform(-1.6, 1.6), z, 6.0, rng.uniform(2.0, 7.0),
                 rocks[k % len(rocks)], r=rng.uniform(2.0, 3.0))
    for k in range(24):
        x = -hx + (k + 0.5) * 2 * hx / 24.0
        _col(b, x, hz + m / 2.0 + rng.uniform(-1.6, 1.6), 6.0, rng.uniform(2.0, 7.0), rocks[k % len(rocks)],
             r=rng.uniform(2.0, 3.0))
    skirt(b, hx, hz, "#3a3a44", top=SEABED - 3.05)
    backdrop(b, "hills", 8.0, rng, sides=("z-",), colours=["#2e3a3a", "#34443e", "#283430"], depth=160.0)
    # far sea stacks in the murk
    for x, z, w, h in ((-420.0, -260.0, 40.0, 90.0), (380.0, 300.0, 50.0, 70.0), (470.0, -200.0, 30.0, 110.0),
                       (-480.0, 240.0, 44.0, 80.0)):
        b.box([x, h / 2.0 - 4.0, z], [w, h, w * 0.8], "#3a3a48", collide=False)
        b.box([x + w * 0.1, h - 3.0, z], [w * 0.7, 2.0, w * 0.6], MOSS, collide=False)


# ================================================================ the mesa
def _mesa(isle: Isle) -> None:
    """The mesa: sheer basalt, its summit turfed, a crown of columns round
    its rim, the sea cave straight through its foot."""
    b = isle.b
    rng = isle.rng
    x0, x1, z0, z1 = MESA
    t0, t1 = TUNNEL
    b.box([0.0, TOP / 2.0, (z0 + t0) / 2.0], [x1 - x0, TOP, t0 - z0], BASALT)
    b.box([0.0, (CAVE_H + TOP) / 2.0, (t0 + t1) / 2.0], [x1 - x0, TOP - CAVE_H, t1 - t0], BASALT_DARK)
    b.box([0.0, TOP / 2.0, (t1 + z1) / 2.0], [x1 - x0, TOP, z1 - t1], BASALT)
    slab(b, rect(x0, x1, z0, z1), TURF_Y, 0.15, TURF_TOP, studs=True)
    # lichen on the faces, out of reach
    for sgn in (-1.0, 1.0):
        for zz, yy in ((-98.0, 9.0), (-83.0, 12.0), (-60.0, 16.4), (-50.0, 11.0)):
            b.box([sgn * (x1 + 0.1), yy, zz], [0.2, 1.4, 1.8], LICHEN, collide=False)
    for xx in (-33.0, 33.0):
        b.box([xx, 9.0, z1 + 0.1], [3.0, 1.4, 0.2], LICHEN, collide=False)
    # the faces ribbed in columns, the way basalt sets: down the faces where
    # they show, standing on the stairs' treads where the stairs climb them
    rib = TOP - 0.4
    for sgn in (-1.0, 1.0):
        fx = sgn * (x1 + 0.15)
        runs = [(zz, 0.0) for zz in (-99.0, -97.2, -85.0, -83.2, -81.4)]
        runs += [(zz, CAVE_H) for zz in (-95.0, -93.0, -91.0, -89.0, -87.0)]
        runs += [(STAIR_Z[0] - 4.0 * k + 2.0, 2.0 * k) for k in range(1, 9)]
        for k, (zz, y0) in enumerate(runs):
            b.box([fx, (y0 + rib) / 2.0, zz], [0.3, rib - y0, 0.9], BASALT_LIGHT if k % 2 else "#45454f")
        for xx in (33.0, 35.0):
            b.box([sgn * xx, rib / 2.0, z1 + 0.15], [0.9, rib, 0.3], BASALT_LIGHT if xx > 34 else "#45454f")
    # the crown: columns along the north rim, two deep
    for i in range(-10, 11):
        x = 3.3 * i
        for j in range(2):
            z = -110.1 + FLAT * (j + 0.5 * (i % 2))
            _col(b, x, z, TURF_Y, rng.uniform(5.0, 15.0), (BASALT, BASALT_LIGHT, BASALT_DARK)[(i + j) % 3])
    # down the sides (a gap where the stairs come up), and the south corners
    for sgn in (-1.0, 1.0):
        for z in (-100.5, -96.7, -92.9, -89.1, -85.3, -72.6, -68.8, -65.0, -61.2, -57.4, -53.6, -49.8):
            _col(b, sgn * 33.0, z, TURF_Y, rng.uniform(3.0, 9.0), (BASALT, BASALT_LIGHT)[int(abs(z)) % 2])
        _col(b, sgn * 34.0, -46.0, TURF_Y, 3.6, BASALT_LIGHT)
        # columns standing loose on the summit: something to hide behind
        for dx, dz, h in ((0.0, 0.0, 4.6), (3.3, 1.9, 2.4), (0.0, 3.8, 3.2)):
            _col(b, sgn * (17.0 + dx), -94.0 + dz, TURF_Y, h, BASALT_LIGHT if h > 3 else BASALT)
        for dx, dz, h in ((0.0, 0.0, 3.0), (3.3, -1.9, 1.8)):
            _col(b, sgn * (8.0 + dx), -52.0 + dz, TURF_Y, h, BASALT)
    # the side stairs, cut into the faces
    for sgn in (-1.0, 1.0):
        a, c = sorted((sgn * STAIR[0], sgn * STAIR[1]))
        flight(b, "z", STAIR_Z[0], STAIR_Z[1], a, c, 0.0, TOP, BASALT_LIGHT, fill=0.0)


def _lighthouse(isle: Isle) -> None:
    """The lighthouse on the summit: white and red, its lamp turning, a
    lightning rod on its cap that the storm finds first."""
    b = isle.b
    x, z = TOWER
    b.box([x, TURF_Y + 0.6, z], [14.0, 1.2, 14.0], "#8a8680")
    base = TURF_Y + 1.2
    b.cyl([x, (base + 50.0) / 2.0, z], [10.0, 50.0 - base, 10.0], "#f4f0e8")
    for k, (y0, y1) in enumerate(((26.0, 30.0), (36.0, 40.0), (46.0, 50.0))):
        b.cyl([x, (y0 + y1) / 2.0, z], [10.3, y1 - y0, 10.3], "#c8302a", collide=False)
    b.box([x, base + 2.6, z + 5.0], [3.2, 5.2, 0.6], "#3a2a20")
    b.box([x, base + 5.5, z + 5.2], [4.0, 0.6, 1.0], "#c8302a")
    for k in range(4):
        a = k * 1.6 + 0.8
        b.box([x + math.sin(a) * 5.0, 22.0 + k * 6.0, z + math.cos(a) * 5.0], [1.2, 1.8, 1.2], "#2a3440",
              collide=False)
    b.cyl([x, 50.3, z], [14.0, 0.6, 14.0], "#3a3a40", material="metal")
    for k in range(12):
        a = k * math.tau / 12.0
        b.cyl([x + math.cos(a) * 6.6, 51.4, z + math.sin(a) * 6.6], [0.3, 1.6, 0.3], "#3a3a40", material="metal")
    b.cyl([x, 53.6, z], [7.0, 6.0, 7.0], "#fff4c8", material="glass", alpha=0.45, collide=False)
    b.cyl([x, 53.0, z], [2.6, 4.2, 2.6], "#fff0a0", material="neon", collide=False)
    b.cone([x, 58.6, z], [8.4, 4.0, 8.4], "#c8302a")
    b.cyl([x, 63.6, z], [0.4, 6.0, 0.4], IRON, material="metal")
    b.sphere([x, 66.8, z], [0.9, 0.9, 0.9], "#c88a3a", material="metal")
    b.rig("rr_lighthouse", x, 53.0, z, len=240.0, rate=0.5)
    b.rig("pb_sparks", x, 67.0, z, r=2.4, n=5, seed=1.0)
    b.landmark(x, z, "the lighthouse")


def _summit(isle: Isle) -> None:
    """The summit: the idol's altar in front of the lighthouse, a storm
    shelter either side, treasure lying out in the weather."""
    b = isle.b
    isle.idol(IDOL[0], TURF_Y, IDOL[1], colour="#6a6a74")
    for sgn in (-1.0, 1.0):
        x0, x1 = sorted((sgn * SHELTER[0], sgn * SHELTER[1]))
        door = isle.hut(rect(x0, x1, SHELTER[2], SHELTER[3]), "x-" if sgn > 0 else "x+", y=TURF_Y,
                        colour=STONE, roof=TURF_TOP, height=7.0)
        isle.loot((x0 + x1) / 2.0, TURF_Y + 0.4, (SHELTER[2] + SHELTER[3]) / 2.0, "gem", "the summit shelter")
        b.box([door[0] - sgn * 0.15, TURF_Y + 7.6, door[1]], [0.3, 0.8, 4.0], "#c8302a" if sgn < 0 else "#2a6ab8",
              collide=False)
        isle.loot(sgn * 24.0, None, -50.0, "any", "the summit")
        isle.loot(sgn * 11.0, None, -80.0, "bar", "the lighthouse")
    isle.loot(0.0, None, -99.0, "gem", "behind the lighthouse")


def _cave(isle: Isle) -> None:
    """The sea cave through the mesa's foot: a low, dark gallery from one
    wing to the other, its walls bristling with storm crystals."""
    b = isle.b
    rng = isle.rng
    t0, t1 = TUNNEL
    for k, x in enumerate((-30.0, -18.0, -6.0, 6.0, 18.0, 30.0)):
        north = k % 2 == 0
        wz = t0 if north else t1
        face = 1.0 if north else -1.0
        b.box([x, 0.7, wz + face * 0.6], [3.4, 1.2, 1.2], BASALT_LIGHT)
        for j in range(3):
            h = rng.uniform(1.6, 2.8)
            b.box([x - 0.9 + j * 0.9, 1.3 + h / 2.0, wz + face * 0.6], [0.6, h, 0.6],
                  (CRYSTAL, "#b88aff", "#8affff")[j], material="neon", collide=False,
                  r=[face * (0.3 - j * 0.15), 0.0, (j - 1) * 0.35])
        b.box([x, CAVE_H - 0.2, wz + face * 1.4], [0.4, 0.4, 2.8], "#9ad8ff", material="neon", collide=False)
        b.rig("pb_sparks", x, 3.0, wz + face * 0.8, r=1.2, n=3, seed=k * 2.0, colour="#b8a8ff")
    isle.loot(0.0, 0.1, (t0 + t1) / 2.0, "gem", "the sea cave")
    isle.loot(-24.0, 0.1, (t0 + t1) / 2.0, "bar", "the sea cave")
    isle.loot(24.0, 0.1, (t0 + t1) / 2.0, "bar", "the sea cave")
    b.landmark(0.0, (t0 + t1) / 2.0, "the sea cave")


def _causeway(isle: Isle) -> None:
    """The giant's causeway: hundreds of six-sided columns packed like a
    honeycomb, stepping down from the summit to the strand -- climb it
    straight, or zig-zag."""
    b = isle.b
    rng = isle.rng
    shades = (BASALT, BASALT_LIGHT, BASALT_DARK, "#444452")

    def zat(i: int, j: int) -> float:
        return -42.1 + FLAT * (j + 0.5 * (i % 2))

    def height(i: int, j: int) -> float:
        return max(0.5, 17.6 - (zat(i, j) + 42.1) * 0.41 - abs(3.3 * i) * 0.1)

    # each landing: its cell and the six round it, all at the cell's height
    flat = {}
    for i0, j0 in LANDINGS:
        for cell in ((i0, j0 - 1), (i0, j0), (i0, j0 + 1), (i0 - 1, j0 - 1), (i0 - 1, j0), (i0 + 1, j0 - 1),
                     (i0 + 1, j0)):
            flat[cell] = height(i0, j0)
    for i in range(-9, 10):
        x = 3.3 * i
        j = 0
        while zat(i, j) <= -2.0:
            z = zat(i, j)
            h = flat.get((i, j)) or height(i, j) + rng.uniform(-0.3, 0.3)
            _col(b, x, z, 0.0, h, shades[(i * 7 + j * 3) % len(shades)])
            if (i + j) % 5 == 0 and (i, j) not in flat:
                _col(b, x, z, h, 0.1, MOSS, collide=False, r=R * 0.8)
            j += 1
    for (i0, j0), kind in zip(LANDINGS, ("bar", "any", "any")):
        isle.loot(3.3 * i0, height(i0, j0), zat(i0, j0), kind, "the causeway")
    b.landmark(0.0, -24.0, "the giant's causeway")


def _wreck(isle: Isle) -> None:
    """The Siren, broken in two on the south strand: each half a hull with
    its deck still on at the stern end (a roof over your head), open at
    the break; her masts fallen across the sand."""
    b = isle.b
    for sgn in (-1.0, 1.0):
        x0, x1 = sorted((sgn * WRECK[0], sgn * WRECK[1]))
        z0, z1 = WRECK[2], WRECK[3]
        outer = x1 if sgn > 0 else x0
        inner = x0 if sgn > 0 else x1
        fa, fb = sorted((inner, outer - sgn * 2.0))
        b.box([(fa + fb) / 2.0, 0.4, (z0 + z1) / 2.0], [fb - fa, 0.8, z1 - z0 - 2.4], "#6a4a2e")
        for zz in (z0 + 0.6, z1 - 0.6):
            b.box([(x0 + x1) / 2.0 - sgn * 1.0, 3.5, zz], [x1 - x0 - 2.0, 7.0, 1.2], "#5a3a22")
            b.box([(x0 + x1) / 2.0 - sgn * 1.0, 5.0, zz + (0.62 if zz > (z0 + z1) / 2 else -0.62)],
                  [x1 - x0 - 2.0, 0.8, 0.04], "#c8a040", collide=False)
        b.box([outer - sgn * 1.0, 3.5, (z0 + z1) / 2.0], [2.0, 7.0, z1 - z0], "#5a3a22")
        b.box([outer + sgn * 0.8, 3.0, (z0 + z1) / 2.0], [1.6, 6.0, 10.0], "#4a3018")
        # the deck still on over the stern half: shelter from the storm
        da, db = sorted((sgn * 13.0, outer))
        b.box([(da + db) / 2.0, 7.3, (z0 + z1) / 2.0], [db - da, 0.6, z1 - z0], "#8a6a44")
        # its broken edge, and the planks splintered at the break
        for k in range(5):
            b.box([sgn * (13.0 - 0.6 * (k % 2)), 7.2, z0 + 2.0 + k * 3.0], [1.2 + 0.4 * (k % 3), 0.6, 2.6],
                  "#8a6a44")
        for zz, h in ((z0 + 0.6, 5.2), (z1 - 0.6, 3.8)):
            b.box([inner - sgn * 0.4, h / 2.0, zz], [1.2, h, 1.0], "#4a3018")
        # the mainmast stump on the deck, a torn flag still on it
        mx = sgn * 19.0
        b.cyl([mx, 7.6 + 6.0, (z0 + z1) / 2.0], [1.2, 12.0, 1.2], "#4a3018")
        b.rig("rr_flag", mx, 19.0, (z0 + z1) / 2.0, yaw=math.pi / 2.0, w=4.0, h=2.6,
              colours=["#1a1a1e", "#2a2a2e"])
        # her figurehead, a siren with her arms out
        b.box([outer + sgn * 2.0, 4.6, (z0 + z1) / 2.0], [1.2, 3.2, 1.4], "#e8b830", material="metal")
        b.sphere([outer + sgn * 2.2, 6.8, (z0 + z1) / 2.0], [1.2, 1.4, 1.2], "#e8b830", material="metal")
        # inside, in the dark under the deck
        isle.loot(sgn * 19.0, 0.8, (z0 + z1) / 2.0 - 3.0, "gem", "the wreck")
        isle.barrel(sgn * 21.5, z1 - 4.0)
        isle.loot(sgn * 8.0, None, (z0 + z1) / 2.0, "bar", "the wreck")
        # a fallen mast across the sand, low enough to step over
        b.box([sgn * 9.0, 0.6, 74.0], [1.2, 1.2, 16.0], "#4a3018")
        b.box([sgn * 9.0, 0.7, 70.0], [5.0, 0.4, 0.5], "#4a3018")
    isle.loot(0.0, None, 54.0, "any", "the wreck")
    b.landmark(0.0, 54.0, "the wreck of the Siren")


def _henge(isle: Isle) -> None:
    """The storm henge: a ring of standing columns, an iron spike on each,
    round a stepped dais -- the old wreckers' altar to the weather.  The
    storm loves it."""
    b = isle.b
    rng = isle.rng
    cx, cz, ring = HENGE
    _col(b, cx, cz, 0.0, 0.8, BASALT_LIGHT, r=6.0)
    _col(b, cx, cz, 0.8, 0.8, BASALT, r=3.8)
    lintel = 8.6                 # the paired stones carrying a lintel
    paired = (1, 2, 5, 6)
    for k in range(8):
        a = math.pi / 8.0 + k * math.pi / 4.0
        x, z = cx + math.cos(a) * ring, cz + math.sin(a) * ring
        h = lintel if k in paired else 7.0 + (k % 3) * 1.4 + rng.uniform(0.0, 0.6)
        _col(b, x, z, 0.0, h, (BASALT, BASALT_LIGHT, BASALT_DARK)[k % 3], r=1.8)
        b.box([x, 2.4 + (k % 2) * 1.6, z - 1.56], [1.6, 0.4, 0.1], CRYSTAL, material="neon", collide=False)
        if k in paired:
            continue
        _col(b, x, z, h, 0.3, "#c88a3a", r=1.0)
        b.cyl([x, h + 2.2, z], [0.3, 3.8, 0.3], IRON, material="metal")
        b.rig("pb_sparks", x, h + 4.3, z, r=1.2, n=3, seed=k * 1.3)
    # lintels across the paired stones, the way the old ones stand
    for k in (1, 5):
        a0 = math.pi / 8.0 + k * math.pi / 4.0
        a1 = a0 + math.pi / 4.0
        p0 = (cx + math.cos(a0) * ring, cz + math.sin(a0) * ring)
        p1 = (cx + math.cos(a1) * ring, cz + math.sin(a1) * ring)
        mx, mz = (p0[0] + p1[0]) / 2.0, (p0[1] + p1[1]) / 2.0
        ln = math.hypot(p1[0] - p0[0], p1[1] - p0[1]) + 3.0
        b.box([mx, lintel + 0.7, mz], [ln, 1.4, 2.4], BASALT_LIGHT, collide=False,
              r=[0.0, -math.atan2(p1[1] - p0[1], p1[0] - p0[0]), 0.0])
    isle.loot(cx, None, cz, "gem", "the storm henge")
    b.landmark(cx, cz, "the storm henge")


def _beacon(isle: Isle) -> None:
    """The wreckers' beacon: an iron basket of fire on a post, the false
    light that drew the Siren onto the rocks."""
    b = isle.b
    x, z = 0.0, 84.0
    for k in range(10):
        a = k * math.tau / 10.0
        b.box([x + math.cos(a) * 3.6, 0.6, z + math.sin(a) * 3.6], [1.6, 1.2, 1.6], BASALT_LIGHT)
    b.cyl([x, 4.0, z], [0.9, 8.0, 0.9], IRON, material="metal")
    b.cyl([x, 8.6, z], [3.4, 1.2, 3.4], IRON, material="metal")
    b.cone([x, 10.4, z], [2.8, 2.4, 2.8], "#ff8a2a", material="neon", collide=False)
    b.rig("rr_flame", x, 9.2, z, s=1.6)
    b.rig("rr_smoke", x, 12.0, z, wind=[0.9, 0.5], rate=0.3, h=26.0, size=2.4, colour="#4a4448")
    isle.dig(-14.0, None, 88.0, "by the beacon")
    isle.dig(14.0, None, 88.0, "by the beacon")
    b.landmark(x, z, "the wreckers' beacon")


# ================================================================ the wings
def _tree(isle: Isle, x: float, z: float, h: float, lean: float) -> None:
    """A tree the lightning has had: a black trunk, splintered, its few
    branches bare, embers still glowing in the split."""
    b = isle.b
    y = isle.top(x, z)
    b.cyl([x, y + h / 2.0, z], [1.2, h, 1.2], "#2a2420")
    for k, (a, l) in enumerate(((0.6, 4.0), (2.4, 3.2), (4.2, 3.6))):
        yy = y + h * (0.55 + k * 0.15)
        b.box([x + math.cos(a) * l * 0.45, yy + 0.8, z + math.sin(a) * l * 0.45], [l, 0.5, 0.5], "#2a2420",
              collide=False, r=[0.0, -a, 0.5 + lean * 0.2])
    b.box([x, y + h + 0.2, z], [0.5, 0.4, 0.5], "#ff7a2a", material="neon", collide=False)


def _half(isle: Isle, sgn: float) -> None:
    """One crew's wing (mirrored for the other): the wreckers' cottages
    with turf on their roofs, the wreckers' light on its tower, nets,
    boats and the lightning-struck trees."""
    b = isle.b
    rng = isle.rng
    west = sgn < 0

    def X(x: float) -> float:
        return sgn * x

    # ---- the cottages: stone, turf roofs, smoking chimneys
    for k, (area, door) in enumerate(COTTAGES):
        x0, x1 = sorted((X(area[0]), X(area[1])))
        if door in ("x-", "x+") and west:
            door = "x+" if door == "x-" else "x-"
        dx, dz = isle.hut(rect(x0, x1, area[2], area[3]), door, colour=STONE, roof=TURF_TOP, height=7.0)
        trim = "#c8302a" if west else "#2a6ab8"
        for e in (-1.0, 1.0):
            if door in ("z-", "z+"):
                out = -1.0 if door == "z-" else 1.0
                lx, lz, size = dx + e * 3.6, dz + out * 0.3, [0.8, 1.0, 0.6]
            else:
                out = -1.0 if door == "x-" else 1.0
                lx, lz, size = dx + out * 0.3, dz + e * 3.6, [0.6, 1.0, 0.8]
            b.box([lx, 6.1, lz], size, "#ffb84a", material="neon", collide=False)
        if door in ("z-", "z+"):
            b.box([dx, 7.3, dz + (-0.15 if door == "z-" else 0.15)], [x1 - x0, 0.6, 0.3], trim, collide=False)
        else:
            b.box([dx + (-0.15 if door == "x-" else 0.15), 7.3, dz], [0.3, 0.6, area[3] - area[2]], trim,
                  collide=False)
        cx = x1 - 2.0 if sgn > 0 else x0 + 2.0
        cz = area[2] + 2.0
        b.box([cx, 6.0, cz], [1.8, 12.0, 1.8], "#6a6460")
        b.rig("rr_smoke", cx, 12.4, cz, wind=[0.9, 0.5], rate=0.25, h=16.0, size=1.4, colour="#5a5458")
        isle.loot((x0 + x1) / 2.0, 0.4, (area[2] + area[3]) / 2.0, "bar" if k == 1 else "any", "a cottage")
    # ---- the wreckers' light: a timber tower with a great lantern on top
    lx0, lx1 = sorted((X(LIGHT_E[0]), X(LIGHT_E[1])))
    lz0, lz1 = LIGHT_E[2], LIGHT_E[3]
    deck = 10.0
    for px in (lx0 + 0.6, lx1 - 0.6):
        for pz in (lz0 + 0.6, lz1 - 0.6):
            b.cyl([px, (deck - 0.6) / 2.0, pz], [1.0, deck - 0.6, 1.0], TIMBER)
    b.box([(lx0 + lx1) / 2.0, deck - 0.3, (lz0 + lz1) / 2.0], [lx1 - lx0, 0.6, lz1 - lz0], PLANK)
    sa, sb = sorted((X(93.0), X(97.0)))
    flight(b, "z", -40.0, lz1, sa, sb, 0.0, deck, TIMBER, fill=0.0)
    b.box([(lx0 + lx1) / 2.0, deck + 0.5, lz0 + 0.2], [lx1 - lx0, 1.0, 0.4], TIMBER)
    for ex in (lx0 + 0.2, lx1 - 0.2):
        b.box([ex, deck + 0.5, (lz0 + lz1) / 2.0 - 0.2], [0.4, 1.0, lz1 - lz0 - 0.4], TIMBER)
    for ea, eb in ((lx0, sa), (sb, lx1)):
        b.box([(ea + eb) / 2.0, deck + 0.5, lz1 - 0.2], [eb - ea, 1.0, 0.4], TIMBER)
    cx, cz = X(97.6), lz0 + 2.4
    b.box([cx, deck + 0.2, cz], [2.8, 0.4, 2.8], IRON, material="metal")
    b.box([cx, deck + 1.6, cz], [2.4, 2.4, 2.4], "#ffd890", material="glass", alpha=0.5, collide=False)
    b.cyl([cx, deck + 1.4, cz], [1.2, 2.0, 1.2], "#ff9a3a", material="neon", collide=False)
    b.cone([cx, deck + 3.4, cz], [3.0, 1.6, 3.0], IRON, material="metal")
    b.cyl([cx, deck + 6.6, cz], [0.3, 5.0, 0.3], IRON, material="metal")
    b.rig("pb_sparks", cx, deck + 9.2, cz, r=1.4, n=3, seed=sgn * 4.0)
    isle.loot(X(94.0), None, -57.0, "gem", "the wreckers' light")
    # ---- nets drying on poles, a boat upturned on the shingle, oars
    for k in range(3):
        nz = 50.0 + k * 6.0
        ny = isle.top(X(104.0), nz)
        for e in (-2.2, 2.2):
            b.cyl([X(104.0), ny + 2.9, nz + e], [0.4, 5.8, 0.4], TIMBER)
        b.box([X(104.0), ny + 3.2, nz], [0.1, 4.2, 4.0], "#4a5a5a", alpha=0.7)
        b.box([X(104.0), ny + 5.6, nz], [0.24, 0.24, 4.8], ROPE_C, collide=False)
    bx, bz = X(104.0), -70.0
    by = isle.top(bx, bz)
    b.box([bx, by + 0.9, bz], [3.6, 1.8, 10.0], "#3a6a8a" if not west else "#8a3a3a")
    b.box([bx, by + 1.9, bz], [3.0, 0.2, 9.0], "#2a2420")
    b.box([bx, by + 0.15, bz + 7.4], [0.4, 0.3, 4.6], TIMBER, collide=False, r=[0.0, 0.3, 0.0])
    # ---- crates and barrels washed up, the lightning-struck trees, rocks
    isle.crates(X(96.0), 22.0, n=3)
    isle.barrel(X(80.0), -50.0)
    isle.barrel(X(83.4), -51.0)
    for x, z, h in ((88.0, 26.0, 11.0), (50.0, -70.0, 13.0), (90.0, 68.0, 10.0), (48.0, 40.0, 12.0)):
        if isle.clear(X(x), z, 3.0):
            _tree(isle, X(x), z, h, sgn)
    for x, z, n in ((76.0, -60.0, 3), (44.0, 76.0, 2), (96.0, 40.0, 2), (64.0, 80.0, 3), (36.0, -6.0, 2)):
        for k in range(n):
            px, pz = X(x + (k % 2) * 3.3), z + k * 1.9
            if isle.clear(px, pz, 3.0):
                _col(b, px, pz, isle.top(px, pz), rng.uniform(1.4, 3.6), (BASALT, BASALT_LIGHT)[k % 2])
    isle.flag(X(108.0), 0.0, None, "#c8302a" if west else "#2a6ab8", h=11.0)
    # ---- X's and loot
    isle.dig(X(70.0), None, -12.0, "the wreckers' green")
    isle.dig(X(92.0), None, 52.0, "by the nets")
    isle.dig(X(46.0), None, -54.0, "under the mesa")
    isle.dig(X(82.0), None, 82.0, "the south shingle")
    isle.dig(X(96.0), None, -86.0, "under the cliffs")
    isle.loot(X(104.0), None, -40.0, "any", "the shingle")
    isle.loot(X(76.0), None, 20.0, "any", "the wreckers' green")
    isle.loot(X(40.0), None, 60.0, "any", "the strand")
    isle.loot(X(60.0), None, -100.0 + 6.0, "any", "the cave mouth")



def _rain(isle: Isle) -> None:
    """Where the storm strikes when there is nobody out to strike: open
    ground all over the island, the summit included."""
    b = isle.b
    for x, z in ((100.0, -40.0), (100.0, 30.0), (76.0, -16.0), (60.0, 40.0), (80.0, 70.0), (50.0, -80.0),
                 (44.0, 20.0), (30.0, 84.0), (90.0, -76.0), (40.0, -40.0)):
        for sgn in (-1.0, 1.0):
            b.mark("rain", sgn * x, isle.top(sgn * x, z), z)
    for x, z in ((0.0, -56.0), (-20.0, -74.0), (20.0, -74.0), (0.0, 22.0), (0.0, 70.0)):
        b.mark("rain", x, isle.top(x, z, 30.0), z)


# ================================================================ meta
def _meta(isle: Isle) -> None:
    b = isle.b
    for x, z, name in ((-90.0, -6.0, "the west cottages"), (90.0, -6.0, "the east cottages"),
                       (-96.0, -56.0, "the west wreckers' light"), (96.0, -56.0, "the east wreckers' light"),
                       (0.0, -60.0, "the summit"),
                       (-SHIP_X, 0.0, "the Scarlet Queen"), (SHIP_X, 0.0, "the Blue Marlin")):
        b.landmark(x, z, name)
    b.camera(0.0, 46.0, 104.0, 0.0, 12.0, -40.0)
    b.camera(-110.0, 40.0, 60.0, -10.0, 10.0, -40.0)
    b.camera(50.0, 34.0, -20.0, 0.0, 22.0, -80.0)
    b.camera(-60.0, 10.0, -91.0, 0.0, 4.0, -91.0)
    b.extra.update({"twist": "storm", "water": SEA_TOP, "storm_every": [48.0, 64.0], "storm_for": 24.0,
                    "warn": 6.0})
    # the weather: rain and thunder always, the lighthouse and the
    # wreckers' rods taking strikes; surf, a few birds braving it
    b.rig("rr_weather", 0.0, 0.0, 0.0, weather="storm", wind=[0.9, 0.4], rod_every=34,
          rods=[b.at(TOWER[0], 67.0, TOWER[1]), b.at(-96.0, 19.4, -57.6), b.at(96.0, 19.4, -57.6)])
    b.rig("rr_surf", 0.0, SEA_TOP + 0.3, SOUTH + 6.5, w=2 * SHORE_X - 10.0, yaw=0.0)
    for sgn in (-1.0, 1.0):
        b.rig("rr_surf", sgn * (SHORE_X + 6.5), SEA_TOP + 0.3, -50.0, w=80.0, yaw=sgn * math.pi / 2.0)
        b.rig("rr_surf", sgn * (SHORE_X + 6.5), SEA_TOP + 0.3, 60.0, w=60.0, yaw=sgn * math.pi / 2.0)
        b.rig("rr_gulls", sgn * 80.0, 34.0, -30.0, r=26.0, n=3, seed=sgn * 2.0)
        b.rig("pb_glow", sgn * 46.0, -0.45, 86.0, n=14, w=10.0, d=10.0, seed=sgn * 3.0,
              colours=["#7ab8ff", "#b8a8ff", "#9ad8ff"])


def build(b: ArenaArea) -> None:
    rng = random.Random(0x7A1D)
    isle = Isle(b, rng)
    _land(isle)
    _edges(isle)
    _mesa(isle)
    _lighthouse(isle)
    _summit(isle)
    _cave(isle)
    _causeway(isle)
    _wreck(isle)
    _henge(isle)
    _beacon(isle)
    _half(isle, -1.0)
    _half(isle, 1.0)
    _rain(isle)
    galleon(isle, "red", 0.0)
    galleon(isle, "blue", 0.0)
    _meta(isle)
