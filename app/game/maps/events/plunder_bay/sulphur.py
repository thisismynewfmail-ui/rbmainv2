"""Sulphur Springs: a steaming island of hot springs where the crews come
for the yellow stone that goes into their gunpowder -- white travertine
terraces climbing in steps to a ruined bathhouse, each terrace brimming
with turquoise pools, a great spring ringed in rainbow colours at the
foot of them with a boardwalk across it, mud pots, fumaroles, and on
either wing the powder works: a sulphur mine in the cliffs, its heaps of
yellow stone and its magazine.

Layout (north is -z; the Scarlet Corsairs' ship off the west shore, the
Azure Buccaneers' off the east)::

    z -120  == the mine ==    THE BATHHOUSE (the idol in its pool)    == the mine ==
    z  -80                    terrace 4 ------------------- (12 up)
    z  -62   magazine        terrace 3 ---------------------- (9)       magazine
    z  -44                  terrace 2 ------------------------- (6)
    z  -24   sulphur heaps terrace 1 ------------------------------ (3)  sulphur heaps
   SCARLET                                                                BLUE
    QUEEN    the powder mill   ( THE GRAND SPRING, its boardwalk )  the powder mill  MARLIN
    z   80   mud pots, palms        fumaroles, geyser cones          mud pots, palms
    z  100  ~~~~~~~~~~~~~~~~~~~~~~~~~ the south sea ~~~~~~~~~~~~~~~~~~~~~~~~~

The halves are mirror images: every stair up the terraces has its twin.

The twist is the geysers (``extra["twist"] = "geysers"``): one after
another the springs blow (``geyser`` marks, each with its sinter cone) --
a ring round the vent, then a column of boiling water that throws
everybody standing on it high into the air (up a terrace, if they are
lucky), knocks the treasure out of their hands, and brings up old treasure
of its own.
"""
from __future__ import annotations

import math
import random

from ..calamity_coast.town import skirt
from ..kit import ArenaArea, backdrop, flight, rect, slab
from .common import (IRON, PLANK, ROCK, ROCK_DARK, SAND, SAND_WET, SEA_TOP, SEABED, SHIP_X, SHORE_X, TIMBER,
                     Isle, galleon)

HALF = (170.0, 120.0)
SKY = {"top": "#3a8ad0", "horizon": "#f4e8c8", "sun": [0.5, 0.62, 0.3], "clouds": 0.45, "tint": "#fff4e0"}
AMBIENT = "#c8c0b0"
GROUND = "#7aa040"
FOG = 760.0

TURF = "#7aa040"
JUNGLE = "#5a9a3a"
SINTER = "#f2ead8"           # travertine: the terraces' white stone
SINTER_SHADE = "#e4d8bc"
SINTER_DARK = "#cdbd9c"
SULPHUR = "#f2d230"
SULPHUR_DARK = "#d0a820"
SPRING = "#3ad0e0"
MUD = "#6a5a4a"
BOARD = "#a8805a"
PATH = "#d8c8a0"
SOUTH = 100.0
NORTH = -100.0               # the foot of the cliffs either side of the terraces
# the terraces: (half-width, front z, top) -- each steps up and in
TIERS = ((70.0, -24.0, 3.0), (62.0, -44.0, 6.0), (52.0, -62.0, 9.0), (40.0, -80.0, 12.0))
TOPY = TIERS[-1][2]
# the stairs up the terrace fronts (x band, east; mirrored) and up their sides
FRONT_STAIRS = ((37.0, 43.0), (15.0, 21.0), (39.0, 45.0), (11.0, 17.0))
SIDE_STAIRS = ((76.0, 70.0, -60.0, -54.0), (68.0, 62.0, -100.0, -94.0), (58.0, 52.0, -110.0, -104.0),
               (46.0, 40.0, -100.0, -94.0))
# the hot pools on each terrace: (x0, x1, z0, z1) east (mirrored), and one
# across the middle of each
POOLS = (((48.0, 64.0, -40.0, -28.0), (-10.0, 10.0, -40.0, -30.0)),
         ((24.0, 36.0, -58.0, -48.0), (-8.0, 8.0, -58.0, -48.0)),
         ((34.0, 48.0, -76.0, -66.0), (-6.0, 6.0, -76.0, -66.0)))
SPRING_C = (0.0, 40.0)
SPRING_R = 24.0
WALK_Z = (44.0, 48.0)        # the boardwalk across the spring
WALK_Y = 1.2
ADIT = (84.0, 96.0)          # the mine's mouth (east; mirrored), x band
ADIT_IN = (86.0, 94.0)
ADIT_BACK = -116.0
ADIT_H = 7.0
MAGAZINE = (96.0, 108.0, -66.0, -54.0)
HEAPS = (92.0, 108.0, -44.0, -28.0)
MILL = (86.0, 100.0, 28.0, 40.0)
MUDS = ((56.0, 4.0, 5.0), (80.0, 66.0, 6.0), (36.0, 84.0, 4.0))
GEYSERS = ((0.0, None, SPRING_C[1]), (46.0, None, 58.0), (30.0, None, -34.0), (52.0, None, -52.0),
           (26.0, None, -70.0), (88.0, None, 0.0))


def _m(r):
    x0, x1, z0, z1 = r
    return (-x1, -x0, z0, z1)


def _both(r):
    return (r, _m(r))


# ================================================================ the land
def _land(isle: Isle) -> None:
    b = isle.b
    hx, hz = HALF
    m = b.margin
    west = (-hx - m, -SHORE_X, -hz - m, hz + m)
    east = (SHORE_X, hx + m, -hz - m, hz + m)
    south = (-SHORE_X, SHORE_X, SOUTH, hz + m)
    muds = [rect(x - r, x + r, z - r, z + r) for x, z, r in MUDS] + \
           [rect(-x - r, -x + r, z - r, z + r) for x, z, r in MUDS]
    isle.land(TURF, holes=[west, east, south] + muds, soil="#6a5040")
    for area in (west, east, south):
        slab(b, area, SEABED, 3.0, SAND_WET, studs=True)
    for k, top in enumerate((-1.0, -2.0)):
        colour = SAND if k == 0 else SAND_WET
        for sgn in (-1.0, 1.0):
            xa, xb = sorted((sgn * (SHORE_X + 3.0 * k), sgn * (SHORE_X + 3.0 * (k + 1))))
            b.box([(xa + xb) / 2.0, (SEABED + top) / 2.0, (NORTH + hz) / 2.0],
                  [xb - xa, top - SEABED, hz - NORTH], colour, studs=True)
        za, zb = SOUTH + 3.0 * k, SOUTH + 3.0 * (k + 1)
        b.box([0.0, (SEABED + top) / 2.0, (za + zb) / 2.0], [2 * SHORE_X, top - SEABED, zb - za], colour,
              studs=True)
    for area in ((-hx, -SHORE_X, -hz, hz), (SHORE_X, hx, -hz, hz), (-SHORE_X, SHORE_X, SOUTH, hz)):
        isle.water(area, SEABED, colour="#2a9ab8")
    for x0, x1, z0, z1 in ((-hx - m - 300.0, -hx - m, -hz - m - 300.0, hz + m + 300.0),
                           (hx + m, hx + m + 300.0, -hz - m - 300.0, hz + m + 300.0),
                           (-hx - m, hx + m, hz + m, hz + m + 300.0)):
        b.box([(x0 + x1) / 2.0, (SEABED - 6.0 + SEA_TOP) / 2.0, (z0 + z1) / 2.0],
              [x1 - x0, SEA_TOP - SEABED + 6.0, z1 - z0], "#2a88b0", material="glass", alpha=0.6,
              collide=False)
    # the mud pots: grey mud a step down, bubbling
    for x, z, r in MUDS:
        for sgn in (-1.0, 1.0):
            pr = rect(sgn * x - r, sgn * x + r, z - r, z + r)
            slab(b, pr, -0.8, 3.0, "#5a4a3c", studs=True)
            b.box([sgn * x, -0.45, z], [2 * r, 0.7, 2 * r], MUD, material="glass", alpha=0.92, collide=False)
            b.rig("rr_bubbles", sgn * x, -0.1, z, w=2 * r - 2.0, d=2 * r - 2.0, n=6)
    # the ground covers, kept off everything that stands on the ground
    s = isle.s
    hz_back = -hz - m
    keep = [(-TIERS[0][0], TIERS[0][0], hz_back, TIERS[0][1])]
    keep += [(SPRING_C[0] - 26.0, SPRING_C[0] + 26.0, SPRING_C[1] - 26.0, SPRING_C[1] + 26.0)]
    keep += [(-74.0, 74.0, WALK_Z[0], WALK_Z[1])]
    keep += [rect(x - r, x + r, z - r, z + r) for x, z, r in MUDS]
    keep += [rect(-x - r, -x + r, z - r, z + r) for x, z, r in MUDS]
    for r in (MAGAZINE, HEAPS, MILL, (ADIT[0], ADIT[1], hz_back, NORTH)):
        keep += list(_both(r))
    for x0, x1, z0, z1 in SIDE_STAIRS[:1]:
        keep += list(_both((min(x0, x1), max(x0, x1), z0, z1)))
    for xa, xb in FRONT_STAIRS[:1]:
        keep += list(_both((xa, xb, TIERS[0][1], TIERS[0][1] + 6.0)))
    for x, _y, z in GEYSERS:
        keep += list(_both((x - 3.5, x + 3.5, z - 3.5, z + 3.5))) if z > TIERS[0][1] else []
    for r in keep:
        s.reserve(r)
    for sgn in (-1.0, 1.0):
        def X(x: float, sgn: float = sgn) -> float:
            return sgn * x
        isle.trail([(X(109.5), -15.0), (X(82.0), -15.0), (X(82.0), -96.0), (X(90.0), -96.0)], colour=PATH)
        isle.trail([(X(82.0), -57.0), (X(77.0), -57.0)], colour=PATH)
        isle.trail([(X(109.5), 15.0), (X(78.0), 15.0), (X(78.0), 46.0), (X(75.0), 46.0)], colour=PATH)
        isle.trail([(X(40.0), -14.0), (X(40.0), 30.0)], colour=PATH)
    # the mine's rails, out of the adit
    for sgn in (-1.0, 1.0):
        xa, xb = sorted((sgn * 89.0, sgn * 91.0))
        s.lay(rect(xa, xb, -100.0, -74.0), 0.1, "#6a6a72")
    # beaches, sulphur-yellow crusts and jungle
    for x0, x1, z0, z1 in ((-SHORE_X, -102.0, NORTH, SOUTH), (102.0, SHORE_X, NORTH, SOUTH),
                           (-102.0, 102.0, 92.0, SOUTH)):
        s.lay(rect(x0, x1, z0, z1), 0.1, SAND)
    for r in ((60.0, 74.0, -18.0, -6.0), (20.0, 32.0, 66.0, 76.0), (90.0, 100.0, 54.0, 64.0)):
        for rr in _both(r):
            s.lay(rect(*rr), 0.12, "#e8d050")
    for r in ((84.0, 102.0, -8.0, 10.0), (52.0, 74.0, 70.0, 92.0), (86.0, 100.0, 70.0, 90.0)):
        for rr in _both(r):
            s.lay(rect(*rr), 0.12, JUNGLE)


# =============================================================== the edges
def _edges(isle: Isle) -> None:
    b = isle.b
    hx, hz = HALF
    rng = isle.rng
    m = b.margin
    rocks = (ROCK, ROCK_DARK, "#9a8a70", "#8a7a62")
    for sgn in (-1.0, 1.0):
        for a, c in ((TIERS[0][0], ADIT[0]), (ADIT[1], SHORE_X)):
            a0, a1 = sorted((sgn * a, sgn * c))
            isle.cliffs("x", a0, a1, -hz - m, NORTH, rng.uniform(22.0, 26.0), rocks, green=JUNGLE, recess=1.0)
        a0, a1 = sorted((sgn * SHORE_X, sgn * (hx + m)))
        isle.cliffs("x", a0, a1, -hz - m, NORTH, 32.0, rocks, base=SEABED, green=JUNGLE, step=14.5,
                    recess=0.0)
        b.box([sgn * (hx + m / 2.0), (SEABED + 6.0) / 2.0, (NORTH + hz + m) / 2.0],
              [m, 6.0 - SEABED, hz + m - NORTH], ROCK)
    b.box([0.0, (SEABED + 6.0) / 2.0, hz + m / 2.0], [2 * hx, 6.0 - SEABED, m], ROCK)
    for k in range(18):
        z = NORTH + (k + 0.5) * (hz + m - NORTH) / 18.0
        for sgn in (-1.0, 1.0):
            b.box([sgn * (hx + m / 2.0) + rng.uniform(-1.0, 1.0), 6.0 + 1.0 + (k % 3) * 0.4, z],
                  [m - 2.0 - (k % 2) * 0.6, 2.0 + (k % 3) * 0.8, (hz + m - NORTH) / 18.0 - 2.0],
                  SULPHUR if k % 4 == 0 else "#a89a80")
    for k in range(18):
        x = -hx + (k + 0.5) * 2 * hx / 18.0
        b.box([x, 6.0 + 1.0 + (k % 3) * 0.4, hz + m / 2.0 + rng.uniform(-1.0, 1.0)],
              [2 * hx / 18.0 - 2.0, 2.0 + (k % 3) * 0.8, m - 2.0 - (k % 2) * 0.6],
              SULPHUR if k % 4 == 1 else "#a89a80")
    skirt(b, hx, hz, "#c8b884", top=SEABED - 3.05)
    backdrop(b, "hills", 10.0, rng, sides=("z-",), colours=["#4a8a3a", "#5a9a44", "#3e7a34"], depth=160.0)
    # a volcano far off, smoking
    b.cone([-260.0, 40.0, -420.0], [260.0, 120.0, 200.0], "#6a5a4a", collide=False)
    b.rig("rr_smoke", -260.0, 100.0, -420.0, wind=[0.6, 0.2], rate=0.12, h=80.0, size=12.0, colour="#d8d0c8")


# ============================================================ the terraces
def _terraces(isle: Isle) -> None:
    """The travertine terraces: four great white steps, built as strips
    that never overlap -- each tier's front strip and the side strips
    running back beside the tier above it -- their faces hung with
    flowstone, stairs cut up the fronts and the sides."""
    b = isle.b
    hz = HALF[1]
    back = -hz - b.margin
    for k, (hw, front, top) in enumerate(TIERS):
        shade = (SINTER, SINTER_SHADE)[k % 2]
        if k + 1 < len(TIERS):
            hw2, front2, _t2 = TIERS[k + 1]
            b.box([0.0, top / 2.0, (front2 + front) / 2.0], [2 * hw, top, front - front2], shade)
            for sgn in (-1.0, 1.0):
                b.box([sgn * (hw2 + hw) / 2.0, top / 2.0, (back + front2) / 2.0], [hw - hw2, top, front2 - back],
                      shade)
        else:
            b.box([0.0, top / 2.0, (back + front) / 2.0], [2 * hw, top, front - back], shade)
    # flowstone: ribs of white hanging down the fronts, thicker at the top
    for k, (hw, front, top) in enumerate(TIERS):
        y0 = 0.0 if k == 0 else TIERS[k - 1][2]
        stair = FRONT_STAIRS[k]
        x = -hw + 2.0
        n = 0
        while x < hw - 2.0:
            if not (stair[0] - 1.6 < abs(x) < stair[1] + 1.6):
                drop = (top - y0) * (0.55 + 0.4 * ((n * 7) % 5) / 4.0)
                b.box([x, top - drop / 2.0, front + 0.2], [1.2 + (n % 3) * 0.3, drop, 0.4],
                      (SINTER_SHADE, SINTER_DARK, "#e8c8a0")[n % 3])
            x += 2.6
            n += 1
    # the stairs: up each front, and up each side
    for k, (xa, xb) in enumerate(FRONT_STAIRS):
        hw, front, top = TIERS[k]
        below = 0.0 if k == 0 else TIERS[k - 1][2]
        for sgn in (-1.0, 1.0):
            a, c = sorted((sgn * xa, sgn * xb))
            flight(b, "z", front + 6.0, front, a, c, below, top, SINTER_DARK, fill=below)
    for k, (near, far, z0, z1) in enumerate(SIDE_STAIRS):
        below = 0.0 if k == 0 else TIERS[k - 1][2]
        for sgn in (-1.0, 1.0):
            flight(b, "x", sgn * near, sgn * far, z0, z1, below, TIERS[k][2], SINTER_DARK, fill=below)
    # the hot pools on the terraces: a lip of stone round turquoise water
    for k, pools in enumerate(POOLS):
        top = TIERS[k][2]
        for r in (pools[0], _m(pools[0]), pools[1]):
            _pool(isle, r, top)
    b.landmark(0.0, -34.0, "the first terrace")
    b.landmark(0.0, -70.0, "the high terraces")


def _pool(isle: Isle, r, top: float, lip: float = 0.6, colour: str = SPRING) -> None:
    """A hot pool on a terrace: a rim of stone, a pale floor, steaming
    water to the shins."""
    b = isle.b
    x0, x1, z0, z1 = r
    t = 0.8
    b.box([(x0 + x1) / 2.0, top + lip / 2.0, z0 + t / 2.0], [x1 - x0, lip, t], SINTER_SHADE)
    b.box([(x0 + x1) / 2.0, top + lip / 2.0, z1 - t / 2.0], [x1 - x0, lip, t], SINTER_SHADE)
    for xx in (x0 + t / 2.0, x1 - t / 2.0):
        b.box([xx, top + lip / 2.0, (z0 + z1) / 2.0], [t, lip, z1 - z0 - 2 * t], SINTER_SHADE)
    b.box([(x0 + x1) / 2.0, top + 0.03, (z0 + z1) / 2.0], [x1 - x0 - 2 * t, 0.06, z1 - z0 - 2 * t], "#bff4f4",
          collide=False)
    b.box([(x0 + x1) / 2.0, top + 0.06 + 0.2, (z0 + z1) / 2.0], [x1 - x0 - 2 * t, 0.4, z1 - z0 - 2 * t], colour,
          material="glass", alpha=0.55, collide=False)
    b.rig("rr_smoke", (x0 + x1) / 2.0, top + 0.5, (z0 + z1) / 2.0, wind=[0.3, 0.2], rate=0.16, h=7.0,
          size=1.5, n=6, colour="#ffffff")


# =========================================================== the bathhouse
def _bathhouse(isle: Isle) -> None:
    """The ruined bathhouse on the top terrace: a mosaic floor, a plunge
    pool with the idol's altar in the middle of it, a colonnade (half of it
    fallen), and the governor who built it, in gilt, at the back."""
    b = isle.b
    rng = isle.rng
    y = TOPY
    # the mosaic: blue, a gold border, white, laid one on the other
    for (x0, x1, z0, z1), top, colour in (((-24.0, 24.0, -112.0, -81.0), 0.05, "#2a6ab8"),
                                           ((-22.0, 22.0, -111.0, -82.0), 0.1, "#e8b830"),
                                           ((-20.0, 20.0, -110.0, -83.0), 0.15, SINTER)):
        b.box([(x0 + x1) / 2.0, y + top / 2.0, (z0 + z1) / 2.0], [x1 - x0, top, z1 - z0], colour, collide=False)
    for k in range(10):
        a = k * math.tau / 10.0
        b.box([math.cos(a) * 17.0, y + 0.17, -99.0 + math.sin(a) * 11.0], [1.6, 0.04, 1.6],
              ("#c86a3a", "#2a6ab8")[k % 2], collide=False, r=[0.0, a, 0.0])
    # the plunge pool and its altar
    _pool(isle, (-12.0, 12.0, -104.0, -88.0), y + 0.15, lip=1.0, colour="#4ad8e8")
    isle.idol(0.0, y + 0.15, -96.0, colour=SINTER_DARK)
    # the colonnade: whole columns and broken ones, an architrave on the whole
    heights = []
    for sgn in (-1.0, 1.0):
        for k, z in enumerate((-110.0, -103.5, -97.0, -90.5, -84.0)):
            whole = (k + (0 if sgn < 0 else 1)) % 3 != 0
            h = 9.0 if whole else rng.uniform(2.6, 5.0)
            heights.append((sgn, z, h))
            b.cyl([sgn * 17.0, y + 0.15 + h / 2.0, z], [1.8, h, 1.8], SINTER)
            b.box([sgn * 17.0, y + 0.15 + h + 0.4, z], [2.6, 0.8, 2.6], SINTER_SHADE)
            if not whole:
                b.cyl([sgn * (19.0 + k * 0.4), y + 0.15 + 0.8, z + 3.0], [1.8, 1.6, 1.8], SINTER_SHADE)
    for sgn in (-1.0, 1.0):
        run = [z for s2, z, h in heights if s2 == sgn and h > 8.0]
        # an architrave over each pair of neighbouring whole columns
        for za, zb in zip(run, run[1:]):
            if abs(zb - za) < 7.0:
                b.box([sgn * 17.0, y + 0.15 + 9.8 + 0.6, (za + zb) / 2.0], [2.4, 1.2, zb - za + 2.6], SINTER_SHADE)
    # the back wall with its niche, and the governor in it
    b.box([0.0, y + 6.0, -117.0], [36.0, 12.0, 2.0], SINTER_SHADE)
    b.box([0.0, y + 12.6, -117.0], [38.0, 1.2, 2.6], SINTER_DARK)
    b.box([0.0, y + 1.2, -114.0], [4.0, 2.4, 3.6], SINTER_DARK)
    gy = y + 2.4
    for dx in (-0.6, 0.6):
        b.box([dx, gy + 1.2, -114.0], [1.0, 2.4, 1.2], "#e8b830", material="metal")
    b.box([0.0, gy + 3.6, -114.0], [2.8, 2.6, 1.4], "#e8b830", material="metal")
    b.box([0.0, gy + 5.5, -114.0], [1.4, 1.3, 1.3], "#e8b830", material="metal")
    b.box([0.0, gy + 6.4, -114.0], [2.6, 0.6, 2.0], "#2a2a2e")
    b.box([1.8, gy + 4.6, -113.6], [0.6, 0.6, 2.6], "#e8b830", material="metal")
    # steam off the pool, braziers either side of the altar's pool
    for sgn in (-1.0, 1.0):
        isle.torch(sgn * 14.0, -84.0, y + 0.15, h=4.0)
    isle.loot(0.0, None, -86.0 + 0.5, "gem", "the bathhouse")
    isle.loot(-28.0, None, -100.0, "bar", "the bathhouse")
    isle.loot(28.0, None, -100.0, "bar", "the bathhouse")
    b.landmark(0.0, -100.0, "the bathhouse")


# ========================================================== the spring
def _spring(isle: Isle) -> None:
    """The grand spring: a basin of white sinter with the water in rings of
    colour -- red at the rim, through orange, yellow and green to blue in
    the depths -- steaming, a boardwalk across it on stilts."""
    b = isle.b
    cx, cz = SPRING_C
    b.box([cx, 0.15, cz], [52.0, 0.3, 52.0], SINTER)
    for k, (d, colour) in enumerate(((48.0, "#c8402a"), (43.0, "#e8702a"), (37.0, "#f0a030"), (31.0, "#e8d040"),
                                     (25.0, "#7ac85a"), (18.0, "#3ab8b0"), (10.0, "#1a6ab8"))):
        b.cyl([cx, 0.3 + 0.02 * (k + 1) - 0.01, cz], [d, 0.02, d], colour, collide=False)
    b.cyl([cx, 0.6, cz], [46.0, 0.4, 46.0], "#bff8ff", material="glass", alpha=0.22, collide=False)
    for k in range(4):
        a = k * math.tau / 4.0 + 0.6
        b.rig("rr_smoke", cx + math.cos(a) * 13.0, 0.8, cz + math.sin(a) * 13.0, wind=[0.4, 0.2], rate=0.12,
              h=14.0, size=2.4, n=7, colour="#ffffff")
    b.rig("pb_glow", cx, 0.62, cz, n=30, w=40.0, d=40.0, seed=4.0, colours=["#ffffff", "#fff4c0", "#c8fff8"])
    # the boardwalk: planks on stilts, a step up at each end
    za, zb = WALK_Z
    b.box([0.0, WALK_Y - 0.15, (za + zb) / 2.0], [140.0, 0.3, zb - za], BOARD)
    for k in range(24):
        x = -69.0 + k * 6.0
        for zz in (za + 0.4, zb - 0.4):
            b.cyl([x, (WALK_Y - 0.3) / 2.0, zz], [0.5, WALK_Y - 0.3, 0.5], TIMBER)
        if k % 3 == 1:
            b.cyl([x, WALK_Y + 1.0, za + 0.2], [0.36, 2.0, 0.36], TIMBER)
            b.cyl([x, WALK_Y + 1.0, zb - 0.2], [0.36, 2.0, 0.36], TIMBER)
    for sgn in (-1.0, 1.0):
        flight(b, "x", sgn * 74.0, sgn * 70.0, za, zb, 0.0, WALK_Y, TIMBER, fill=0.0)
    isle.loot(0.0, WALK_Y, (za + zb) / 2.0, "gem", "the boardwalk")
    b.landmark(cx, cz, "the grand spring")


def _cone(isle: Isle, x: float, z: float, y: float) -> float:
    """A geyser's cone of sinter, its vent dark in the top; returns the
    height of the vent's lip, where the geyser blows from."""
    b = isle.b
    b.cyl([x, y + 0.3, z], [7.0, 0.6, 7.0], SINTER_SHADE)
    b.cyl([x, y + 0.9, z], [5.0, 0.6, 5.0], SINTER)
    b.cyl([x, y + 1.21, z], [1.8, 0.02, 1.8], "#3a3430", collide=False)
    b.rig("rr_smoke", x, y + 1.3, z, wind=[0.3, 0.2], rate=0.22, h=8.0, size=1.6, colour="#ffffff")
    return y + 1.2


def _geysers(isle: Isle) -> None:
    b = isle.b
    for k, (x, _y, z) in enumerate(GEYSERS):
        for sgn in ((1.0,) if x == 0.0 else (-1.0, 1.0)):
            px = sgn * x
            if k == 0:
                y = 0.3                          # in the middle of the grand spring
            else:
                y = isle.top(px, z, 20.0)
            lip = _cone(isle, px, z, y)
            b.mark("geyser", px, lip, z)
    b.landmark(0.0, SPRING_C[1], "Old Faithless")


# ================================================================ the wings
def _half(isle: Isle, sgn: float) -> None:
    """One crew's wing (mirrored for the other): the powder works -- the
    sulphur mine in the cliffs, its rails and heaps of yellow stone, the
    magazine -- the powder mill, the mud pots, palms and jungle."""
    b = isle.b
    rng = isle.rng
    west = sgn < 0

    def X(x: float) -> float:
        return sgn * x

    hz = HALF[1]
    back = -hz - b.margin
    # ---- the sulphur mine: its mouth framed in timber, a gallery into the
    # cliff, crystals in the walls
    a0, a1 = sorted((X(ADIT[0]), X(ADIT[1])))
    i0, i1 = sorted((X(ADIT_IN[0]), X(ADIT_IN[1])))
    cliff = 24.0
    for wa, wb in ((a0, i0), (i1, a1)):
        b.box([(wa + wb) / 2.0, cliff / 2.0, (back + NORTH) / 2.0], [wb - wa, cliff, NORTH - back], ROCK)
    b.box([(i0 + i1) / 2.0, (ADIT_H + cliff) / 2.0, (back + NORTH) / 2.0], [i1 - i0, cliff - ADIT_H, NORTH - back],
          ROCK_DARK)
    b.box([(i0 + i1) / 2.0, ADIT_H / 2.0, (back + ADIT_BACK) / 2.0], [i1 - i0, ADIT_H, ADIT_BACK - back], ROCK_DARK)
    b.box([(a0 + a1) / 2.0, cliff + 0.6, (back + NORTH) / 2.0], [a1 - a0 - 1.0, 1.2, NORTH - back - 2.0], JUNGLE,
          collide=False)
    # the props: posts up to a cap beam a little deeper than they are
    for px in (i0 + 0.5, i1 - 0.5):
        b.box([px, (ADIT_H - 1.0) / 2.0, NORTH + 0.5], [1.0, ADIT_H - 1.0, 1.0], TIMBER)
        b.box([px, (ADIT_H - 1.0) / 2.0, -108.0], [1.0, ADIT_H - 1.0, 1.0], TIMBER)
    b.box([(i0 + i1) / 2.0, ADIT_H - 0.5, NORTH + 0.6], [i1 - i0, 1.0, 1.2], TIMBER)
    b.box([(i0 + i1) / 2.0, ADIT_H - 0.5, -108.0], [i1 - i0, 1.0, 1.2], TIMBER)
    b.box([(i0 + i1) / 2.0, ADIT_H + 0.6, NORTH + 0.05], [4.0, 1.0, 0.1], "#e8d050", collide=False)
    for k, zz in enumerate((-104.0, -112.0)):
        for wx, face in ((i0, 1.0), (i1, -1.0)):
            for j in range(3):
                b.box([wx + face * 0.5, 1.2 + j * 0.9, zz + j * 1.1 - 1.0], [0.7, 1.8, 0.7],
                      (SULPHUR, "#fff07a", SULPHUR_DARK)[j], material="neon", collide=False,
                      r=[0.3 * (j - 1), 0.0, face * 0.4])
    b.box([(i0 + i1) / 2.0, ADIT_H - 0.2, -112.0], [0.4, 0.4, 3.0], "#ffe07a", material="neon", collide=False)
    isle.loot((i0 + i1) / 2.0, 0.0, -112.0, "gem", "the sulphur mine")
    # a cart on the rails, loaded with yellow stone
    cx = X(90.0)
    b.box([cx, 1.6, -82.0], [3.0, 2.0, 4.4], "#6a4a2e")
    b.box([cx, 2.9, -82.0], [2.4, 0.6, 3.6], SULPHUR)
    for zz in (-83.4, -80.6):
        b.cyl([cx, 0.6, zz], [1.0, 3.4, 1.0], IRON, material="metal", collide=False, r=[0.0, 0.0, math.pi / 2.0])
    # ---- the heaps of sulphur, yellow and stepped
    hx0, hx1 = sorted((X(HEAPS[0]), X(HEAPS[1])))
    for k in range(3):
        inset = k * 2.6
        top = 1.0 * (k + 1)
        b.box([(hx0 + hx1) / 2.0, top / 2.0, (HEAPS[2] + HEAPS[3]) / 2.0],
              [hx1 - hx0 - 2 * inset, top, HEAPS[3] - HEAPS[2] - 2 * inset], (SULPHUR, SULPHUR_DARK, "#ffe060")[k],
              studs=True)
    isle.dig((hx0 + hx1) / 2.0, None, (HEAPS[2] + HEAPS[3]) / 2.0, "the sulphur heaps")
    # ---- the magazine: a stone house for the powder, its door painted
    mx0, mx1 = sorted((X(MAGAZINE[0]), X(MAGAZINE[1])))
    door = isle.hut(rect(mx0, mx1, MAGAZINE[2], MAGAZINE[3]), "x-" if not west else "x+", colour="#a89a88",
                    roof="#8a4a3a", height=7.0)
    b.box([door[0] - sgn * 0.15, 7.4, door[1]], [0.3, 0.8, 5.0], "#c8302a" if west else "#2a6ab8", collide=False)
    for k in range(4):
        isle.barrel(X(92.0 - (k % 2) * 3.0), -70.0 + (k // 2) * 3.2, colour="#5a3a22")
    isle.loot((mx0 + mx1) / 2.0, 0.4, (MAGAZINE[2] + MAGAZINE[3]) / 2.0, "bar", "the magazine")
    isle.flag(X(106.0), -50.0, None, "#c8302a" if west else "#2a6ab8", h=12.0)
    # ---- the powder mill: timber, its stone grinding on the green
    lx0, lx1 = sorted((X(MILL[0]), X(MILL[1])))
    isle.hut(rect(lx0, lx1, MILL[2], MILL[3]), "z-", colour="#a8845a", roof="#6a8a4a", height=8.0)
    b.cyl([X(93.0), 1.0, 46.0], [4.0, 2.0, 4.0], "#8a8478")
    b.cyl([X(93.0), 2.4, 46.0], [0.6, 0.8, 0.6], TIMBER)
    isle.loot((lx0 + lx1) / 2.0, 0.4, (MILL[2] + MILL[3]) / 2.0, "any", "the powder mill")
    # ---- fumaroles: rocks crusted yellow, steaming
    for x, z in ((64.0, 28.0), (20.0, 88.0), (100.0, 80.0), (66.0, -90.0)):
        y = isle.top(X(x), z)
        isle.rock(X(x), z, 3.4, 3.0, 1.6, y=y, colour="#9a8a70", cap=SULPHUR)
        b.rig("rr_smoke", X(x), y + 2.4, z, wind=[0.4, 0.3], rate=0.24, h=12.0, size=1.6, colour="#fffbe8")
    # ---- dead trees bleached by the steam, palms by the shore
    for x, z, h in ((58.0, 16.0, 9.0), (30.0, 60.0, 8.0), (70.0, 84.0, 10.0)):
        y = isle.top(X(x), z)
        b.cyl([X(x), y + h / 2.0, z], [1.0, h, 1.0], "#e8e0d0")
        for k, a in enumerate((0.5, 2.3, 4.1)):
            b.box([X(x) + math.cos(a) * 1.2, y + h * (0.6 + k * 0.12), z + math.sin(a) * 1.2], [2.8, 0.4, 0.4],
                  "#e8e0d0", collide=False, r=[0.0, -a, 0.5])
    for x, z in ((106.0, -36.0), (106.0, 30.0), (104.0, 50.0), (106.0, 74.0), (94.0, 92.0), (60.0, 94.0),
                 (96.0, 2.0), (90.0, -6.0)):
        px, pz = X(x + rng.uniform(-1.0, 1.0)), z + rng.uniform(-1.0, 1.0)
        if isle.clear(px, pz, 2.0):
            isle.palm(px, pz, h=rng.uniform(12.0, 16.0))
    for x, z in ((98.0, 64.0), (54.0, 76.0), (88.0, 84.0)):
        if isle.clear(X(x), z, 3.0):
            isle.bush(X(x), z, size=3.0, colour="#4a8a3a")
    # ---- X's and loot about the wing
    isle.dig(X(98.0), None, -82.0, "under the cliffs")
    isle.dig(X(66.0), None, 60.0, "the south fumaroles")
    isle.dig(X(94.0), None, 20.0, "by the mill")
    isle.dig(X(56.0), None, -12.0, "below the terraces")
    isle.dig(X(66.0), None, -76.0, "the high wing")
    isle.loot(X(104.0), None, -20.0, "any", "the beach")
    isle.loot(X(76.0), None, -30.0, "any", "the powder works")
    isle.loot(X(44.0), None, 76.0, "any", "the south fumaroles")
    isle.loot(X(30.0), None, 0.0, "any", "below the terraces")
    # ---- loot on the terraces, this side
    isle.loot(X(56.0), None, -34.0, "any", "the first terrace")
    isle.loot(X(66.0), None, -70.0, "bar", "the terrace's edge")
    isle.loot(X(46.0), None, -90.0, "any", "the high terraces")
    isle.loot(X(30.0), None, -54.0, "gem", "a terrace pool")


# ================================================================ meta
def _meta(isle: Isle) -> None:
    b = isle.b
    for x, z, name in ((-90.0, -108.0, "the west mine"), (90.0, -108.0, "the east mine"),
                       (-102.0, -60.0, "the west magazine"), (102.0, -60.0, "the east magazine"),
                       (-93.0, 34.0, "the west powder mill"), (93.0, 34.0, "the east powder mill"),
                       (-SHIP_X, 0.0, "the Scarlet Queen"), (SHIP_X, 0.0, "the Blue Marlin")):
        b.landmark(x, z, name)
    b.camera(0.0, 44.0, 110.0, 0.0, 6.0, -30.0)
    b.camera(-110.0, 40.0, 40.0, -10.0, 8.0, -50.0)
    b.camera(40.0, 30.0, -30.0, 0.0, 14.0, -100.0)
    b.camera(-40.0, 14.0, 70.0, 0.0, 2.0, 40.0)
    b.extra.update({"twist": "geysers", "water": SEA_TOP, "geysers_every": [50.0, 66.0], "geysers_for": 26.0,
                    "warn": 6.0})
    for sgn in (-1.0, 1.0):
        b.rig("pb_parrots", sgn * 80.0, 24.0, 70.0, r=16.0, n=4, seed=sgn * 3.0)
        b.rig("pb_crabs", sgn * 108.0, 0.2, -60.0, q=[sgn * 108.0, 0.2, -20.0], n=3, seed=sgn * 2.0)
        b.rig("rr_surf", sgn * (SHORE_X + 6.5), SEA_TOP + 0.3, -50.0, w=80.0, yaw=sgn * math.pi / 2.0)
        b.rig("rr_surf", sgn * (SHORE_X + 6.5), SEA_TOP + 0.3, 60.0, w=60.0, yaw=sgn * math.pi / 2.0)
    for k, (x, z) in enumerate(((-60.0, -60.0), (60.0, -60.0), (0.0, 80.0))):
        b.rig("rr_gulls", x, 34.0 + k * 3.0, z, r=24.0, n=4, seed=k + 5)
    b.rig("rr_surf", 0.0, SEA_TOP + 0.3, SOUTH + 6.5, w=2 * SHORE_X - 10.0, yaw=0.0)


def build(b: ArenaArea) -> None:
    rng = random.Random(0x5F06)
    isle = Isle(b, rng)
    _land(isle)
    _edges(isle)
    _terraces(isle)
    _bathhouse(isle)
    _spring(isle)
    _geysers(isle)
    _half(isle, -1.0)
    _half(isle, 1.0)
    galleon(isle, "red", 0.0)
    galleon(isle, "blue", 0.0)
    _meta(isle)
