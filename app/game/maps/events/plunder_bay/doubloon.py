"""Doubloon Isle: a volcanic island of black sand and jungle, a river of
lava down the middle of it and a stepped temple on an island in the lava.

Layout (north is -z; the Scarlet Corsairs' ship off the west beach, the
Azure Buccaneers' off the east)::

    z -136  ~~~~~~~~~~~~~~~~~~~~ THE VOLCANO (smoking) ~~~~~~~~~~~~~~~~~~~~
    z  -64   cliffs     W mine  |  the lava falls  |  E mine     cliffs
    z  -50                 ===== north bridge =====
    z  -34            +------- moat of lava -------+
   SCARLET   jungle   |   the temple island:       |   jungle   BLUE
    QUEEN  hot spring =    THE STEPPED TEMPLE      =  hot spring  MARLIN
    beach   camp      |   (the idol on top)        |   camp     beach
    z   50            +----------------------------+
    z   64                 ===== south bridge =====
    z   86                    the lava pool
    z  104  ~~~~~~~~~~~~~~~~~~~ black sand, the sea ~~~~~~~~~~~~~~~~~~~

The lava is a trench, too deep to climb out of and burning at the bottom
(``extra["lava"]``): anybody who goes in -- pushed, or careless -- is lost,
and whatever they carried with them.  The bridges are the only ways over:
north, south, and either side of the temple.

The twist is the eruption (``extra["twist"] = "eruption"``): the volcano
throws lava bombs down on the island (wherever there is a ``rain`` mark)
and its gold geyser rains doubloons over the same spots.
"""
from __future__ import annotations

import math
import random

from ..calamity_coast.town import skirt
from ..kit import ArenaArea, backdrop, flight, rect, slab
from ...ironvale import carve
from ...lastlight.kit import tent
from .common import IRON, SEA, SEA_TOP, SEABED, SHIP_X, SHORE_X, TIMBER, Isle, galleon

HALF = (170.0, 120.0)
SKY = {"top": "#5a3a3a", "horizon": "#e8946a", "sun": [0.4, 0.5, -0.45], "clouds": 0.8,
       "tint": "#ffc8a0"}
AMBIENT = "#b0989a"
GROUND = "#3f6a32"
FOG = 760.0

TURF = "#3f6a32"
UNDER = "#36602c"
BLACK_SAND = "#3a3a40"
OBSIDIAN = "#2a2630"
BASALT = "#4a4448"
TEMPLE = "#a8a080"
TEMPLE_DARK = "#7a7460"
LAVA = "#ff6a1a"
LAVA_TOP = -6.0             # the lava at the bottom of its trench
KILL_Y = -3.0               # below this in a trench, you are in the lava
SOUTH = 104.0
NORTH = -64.0               # the volcano's foot
# the lava: the river down from the volcano, the moat round the temple
# island, the river on to the pool
RIVERS = [
    (-6.0, 6.0, NORTH, -34.0),
    (-34.0, 34.0, -34.0, -26.0),
    (-34.0, -26.0, -26.0, 42.0),
    (26.0, 34.0, -26.0, 42.0),
    (-34.0, 34.0, 42.0, 50.0),
    (-6.0, 6.0, 50.0, 80.0),
    (-12.0, 12.0, 80.0, 92.0),
]
# the stone bridges over it (x0, x1, z0, z1, along): their decks are at
# BRIDGE_TOP, a parapet down either side
BRIDGES = [(-8.0, 8.0, -54.0, -46.0, "x"), (-8.0, 8.0, 60.0, 68.0, "x"),
           (-36.0, -24.0, 4.0, 12.0, "x"), (24.0, 36.0, 4.0, 12.0, "x")]
BRIDGE_TOP = 0.6
TEMPLE_C = (0.0, 8.0)       # the pyramid's centre
TIERS = [(20.0, 0.0, 4.0), (16.0, 4.0, 8.0), (12.0, 8.0, 12.0), (8.0, 12.0, 16.0)]
STAIR_BAND = (4.0, 12.0)    # the z band its stairs climb, west and east
MINE = (70.0, 100.0, -60.0, -22.0)
SPRING = (54.0, 66.0, 56.0, 68.0)
CAMP = (80.0, 96.0, 74.0, 86.0)


def _m(r):
    x0, x1, z0, z1 = r
    return (-x1, -x0, z0, z1)


# ================================================================ the land
def _land(isle: Isle) -> None:
    b = isle.b
    hx, hz = HALF
    m = b.margin
    west = (-hx - m, -SHORE_X, -hz - m, hz + m)
    east = (SHORE_X, hx + m, -hz - m, hz + m)
    south = (-SHORE_X, SHORE_X, SOUTH, hz + m)
    springs = [SPRING, _m(SPRING)]
    isle.land(TURF, holes=[west, east, south] + RIVERS + springs, soil="#4a3a32")
    for area in (west, east, south):
        slab(b, area, SEABED, 3.0, "#2e2e34")
    # the beaches down into the sea: black sand
    for k, top in enumerate((-1.0, -2.0)):
        for sgn in (-1.0, 1.0):
            xa, xb = sorted((sgn * (SHORE_X + 3.0 * k), sgn * (SHORE_X + 3.0 * (k + 1))))
            b.box([(xa + xb) / 2.0, (SEABED + top) / 2.0, (NORTH + hz) / 2.0],
                  [xb - xa, top - SEABED, hz - NORTH], BLACK_SAND)
        za, zb = SOUTH + 3.0 * k, SOUTH + 3.0 * (k + 1)
        b.box([0.0, (SEABED + top) / 2.0, (za + zb) / 2.0], [2 * SHORE_X, top - SEABED, zb - za],
              BLACK_SAND)
    # the water, and the open sea beyond the reef
    for area in ((-hx, -SHORE_X, -hz, hz), (SHORE_X, hx, -hz, hz), (-SHORE_X, SHORE_X, SOUTH, hz)):
        isle.water(area, SEABED, colour="#2a6a8a")
    for x0, x1, z0, z1 in ((-hx - m - 300.0, -hx - m, -hz - m - 300.0, hz + m + 300.0),
                           (hx + m, hx + m + 300.0, -hz - m - 300.0, hz + m + 300.0),
                           (-hx - m, hx + m, hz + m, hz + m + 300.0)):
        b.box([(x0 + x1) / 2.0, (SEABED - 6.0 + SEA_TOP) / 2.0, (z0 + z1) / 2.0],
              [x1 - x0, SEA_TOP - SEABED + 6.0, z1 - z0], SEA, material="glass", alpha=0.6,
              collide=False)
    # the lava, at the bottom of every trench, and its crust at the edges
    for x0, x1, z0, z1 in RIVERS:
        b.box([(x0 + x1) / 2.0, LAVA_TOP - 1.0, (z0 + z1) / 2.0], [x1 - x0, 2.0, z1 - z0], LAVA,
              material="neon")
    # the hot springs: a pool a step down, steaming
    for x0, x1, z0, z1 in springs:
        slab(b, (x0, x1, z0, z1), -1.2, 4.8, BASALT)
        isle.water((x0, x1, z0, z1), -1.2, -0.3, colour="#6ad8d8", alpha=0.6)
    # covers: the beaches, the jungle floor, paths -- clear of what stands
    # on the ground itself
    s = isle.s
    for r in (MINE, _m(MINE), CAMP, _m(CAMP)):
        s.reserve(r)
    for x0, x1, z0, z1, top, colour in ((-SHORE_X, -96.0, NORTH, SOUTH, 0.1, BLACK_SAND),
                                        (96.0, SHORE_X, NORTH, SOUTH, 0.1, BLACK_SAND),
                                        (-96.0, 96.0, 94.0, SOUTH, 0.1, BLACK_SAND)):
        s.lay(rect(x0, x1, z0, z1), top, colour)
    for sgn in (-1.0, 1.0):
        def X(x: float, sgn: float = sgn) -> float:
            return sgn * x
        isle.trail([(X(109.5), -15.0), (X(86.0), -15.0), (X(86.0), -40.0)], colour="#6a5a48")
        isle.trail([(X(109.5), 15.0), (X(70.0), 15.0), (X(70.0), 4.0), (X(40.0), 4.0)],
                   colour="#6a5a48")
        isle.trail([(X(86.0), -15.0), (X(56.0), -15.0), (X(56.0), -50.0), (X(12.0), -50.0)],
                   colour="#6a5a48")
        isle.trail([(X(70.0), 15.0), (X(70.0), 40.0), (X(46.0), 40.0), (X(46.0), 64.0),
                    (X(12.0), 64.0)], colour="#6a5a48")
        xa, xb = sorted((X(96.0), X(34.0)))
        s.lay(rect(xa, xb, NORTH, 94.0), 0.04, UNDER)


def _edges(isle: Isle) -> None:
    b = isle.b
    rng = isle.rng
    hx, hz = HALF
    m = b.margin
    rocks = [BASALT, OBSIDIAN, "#5a5052", BASALT]
    for sgn in (-1.0, 1.0):
        a0, a1 = sorted((sgn * 70.0, sgn * SHORE_X))
        isle.cliffs("x", a0, a1, -hz - m, NORTH, 30.0, rocks, green="#3a5a2a")
        a0, a1 = sorted((sgn * SHORE_X, sgn * (hx + m)))
        isle.cliffs("x", a0, a1, -hz - m, NORTH, 36.0, rocks, base=SEABED, green="#3a5a2a",
                    step=14.5, recess=0.0)
        b.box([sgn * (hx + m / 2.0), (SEABED + 6.0) / 2.0, (NORTH + hz + m) / 2.0],
              [m, 6.0 - SEABED, hz + m - NORTH], OBSIDIAN)
    b.box([0.0, (SEABED + 6.0) / 2.0, hz + m / 2.0], [2 * hx, 6.0 - SEABED, m], OBSIDIAN)
    for k in range(18):
        x = -hx + (k + 0.5) * 2 * hx / 18.0
        b.box([x, 6.0 + 1.0 + (k % 3) * 0.4, hz + m / 2.0 + rng.uniform(-1.0, 1.0)],
              [2 * hx / 18.0 - 2.0, 2.0 + (k % 3) * 0.8, m - 2.0 - (k % 2) * 0.6],
              BASALT if k % 2 else OBSIDIAN)
    skirt(b, hx, hz, "#2e2e34", top=SEABED - 3.05)
    backdrop(b, "hills", 10.0, rng, sides=("x-", "x+", "z+"), colours=["#3a5a32", "#2e4a2a"],
             depth=260.0)


# ============================================================ the volcano
def _volcano(isle: Isle) -> None:
    b = isle.b
    hz = HALF[1]
    m = b.margin
    back = -hz - m
    # the cone in steps: the lowest solid and too tall to climb, the rest
    # far out of reach
    b.box([0.0, 11.0, (back + NORTH) / 2.0], [140.0, 22.0, NORTH - back], BASALT)
    for k, (w, z0, y0, y1) in enumerate(((112.0, -128.0, 22.0, 32.0), (84.0, -122.0, 32.0, 40.0),
                                          (58.0, -116.0, 40.0, 46.0))):
        z1 = NORTH - 6.0 - k * 6.0
        b.box([0.0, (y0 + y1) / 2.0, (z0 + z1) / 2.0], [w, y1 - y0, z1 - z0],
              OBSIDIAN if k % 2 else BASALT, collide=False)
    # the crater's rim and the fire in it
    for sgn in (-1.0, 1.0):
        b.box([sgn * 18.0, 48.0, -99.0], [8.0, 4.0, 30.0], "#3a3236", collide=False)
    b.box([0.0, 48.0, -111.0], [28.0, 4.0, 6.0], "#3a3236", collide=False)
    b.box([0.0, 48.0, -87.0], [28.0, 4.0, 6.0], "#3a3236", collide=False)
    b.box([0.0, 46.6, -99.0], [28.0, 1.2, 18.0], LAVA, material="neon", collide=False)
    # lava running down its face in streams, and the falls into the river
    for x, w in ((-24.0, 3.0), (-9.0, 2.4), (20.0, 3.4)):
        for k, (y0, y1, z) in enumerate(((22.0, 32.0, NORTH - 6.0), (32.0, 40.0, NORTH - 12.0),
                                          (40.0, 46.0, NORTH - 18.0))):
            b.box([x + k * 1.2, (y0 + y1) / 2.0, z + 0.15], [w, y1 - y0, 0.3], LAVA,
                  material="neon", collide=False)
    b.box([0.0, (LAVA_TOP + 22.0) / 2.0, NORTH + 0.2], [8.0, 22.0 - LAVA_TOP, 0.4], LAVA,
          material="neon")
    # smoke over it, piled up into the sky
    for k in range(7):
        b.sphere([math.sin(k * 1.3) * 6.0, 52.0 + k * 13.0, -99.0 + k * 4.0],
                 [26.0 + k * 6.0, 14.0 + k * 3.0, 26.0 + k * 6.0], "#5a5258" if k % 2 else "#6a6266",
                 collide=False, alpha=0.85)

    b.landmark(0.0, -90.0, "the volcano")


# ============================================================ the temple
def _temple(isle: Isle) -> None:
    b = isle.b
    cx, cz = TEMPLE_C
    bands = [(-24.0, -8.0, STAIR_BAND[0], STAIR_BAND[1]), (8.0, 24.0, STAIR_BAND[0], STAIR_BAND[1])]
    for k, (h, y0, y1) in enumerate(TIERS):
        for x0, x1, z0, z1 in carve((cx - h, cx + h, cz - h, cz + h), bands):
            part = b.box([(x0 + x1) / 2.0, (y0 + y1) / 2.0, (z0 + z1) / 2.0],
                         [x1 - x0, y1 - y0, z1 - z0], TEMPLE if k % 2 == 0 else TEMPLE_DARK,
                         decal="pb_glyphs")
            part["dw"] = 1
        # jungle growing over the edge of the tier above this one
        if k < len(TIERS) - 1:
            b.box([cx - h + 1.0, y1 + 0.3, cz - h + 6.0], [2.0, 0.6, 6.0], "#3a6a2a")
            b.box([cx + h - 1.0, y1 + 0.3, cz + h - 6.0], [2.0, 0.6, 6.0], "#3a6a2a")
    # the stairs up the west and east faces
    flight(b, "x", cx - 24.0, cx - 8.0, cz - 4.0, cz + 4.0, 0.0, 16.0, TEMPLE, fill=0.0)
    flight(b, "x", cx + 24.0, cx + 8.0, cz - 4.0, cz + 4.0, 0.0, 16.0, TEMPLE, fill=0.0)
    # serpent heads at the foot of each stair, open-mouthed
    for sgn in (-1.0, 1.0):
        for dz in (-5.2, 5.2):
            b.box([sgn * 24.4, 1.4, cz + dz], [3.0, 2.8, 2.4], "#6a8a5a")
            b.box([sgn * 24.4, 2.9, cz + dz], [2.0, 0.2, 1.2], "#c83a2a", collide=False)
    # the top: pillars at the corners, the idol's altar, braziers
    for dx in (-6.4, 6.4):
        for dz in (-6.4, 6.4):
            b.box([cx + dx, 16.0 + 3.0, cz + dz], [1.6, 6.0, 1.6], TEMPLE_DARK)
            b.box([cx + dx, 16.0 + 6.3, cz + dz], [2.2, 0.6, 2.2], TEMPLE)
    isle.idol(cx, 16.0, cz, TEMPLE)
    # treasure and digging round its foot
    isle.dig(cx - 14.0, None, cz - 24.0, "the temple's north side")
    isle.dig(cx + 14.0, None, cz + 26.0, "the temple's south side")
    isle.loot(cx - 12.0, 8.0, cz - 13.0, "gem", "the temple's second tier")
    isle.loot(cx + 12.0, 8.0, cz + 13.0, "gem", "the temple's second tier")
    isle.loot(cx, 0.0, cz - 28.0, "any", "the temple island")
    isle.loot(cx, 0.0, cz + 30.0, "any", "the temple island")
    for x, z in ((-22.0, -20.0), (22.0, -20.0), (-22.0, 36.0), (22.0, 36.0)):
        isle.torch(x, z)
    b.landmark(cx, cz, "the temple")


def _bridges(isle: Isle) -> None:
    """Stone bridges over the lava: north, south, and either side of the
    temple."""
    b = isle.b
    for x0, x1, z0, z1, along in BRIDGES:
        b.box([(x0 + x1) / 2.0, 0.3, (z0 + z1) / 2.0], [x1 - x0, 0.6, z1 - z0], "#8a8478")
        # the arch under it, inside the trench, well in from the deck's
        # edges (a body on the rim beside the bridge must not find a floor
        # under its feet that is only there below the parapet)
        b.box([(x0 + x1) / 2.0, -1.4, (z0 + z1) / 2.0], [x1 - x0 - 4.8, 2.8, z1 - z0 - 3.2],
              "#6a6460")
        # parapets along each side
        for z in (z0 + 0.4, z1 - 0.4):
            b.box([(x0 + x1) / 2.0, 0.6 + 0.9, z], [x1 - x0, 1.8, 0.8], "#7a746a")
    isle.loot(0.0, 0.6, -50.0, "any", "the north bridge")
    isle.loot(0.0, 0.6, 64.0, "any", "the south bridge")


# ======================================================== the island halves
def _half(isle: Isle, sgn: float) -> None:
    b = isle.b
    rng = isle.rng

    def X(x: float) -> float:
        return sgn * x

    west = sgn < 0
    # ---- the old gold mine: a hill with a tunnel through it, rails, carts
    x0, x1 = sorted((X(MINE[0]), X(MINE[1])))
    z0, z1 = MINE[2], MINE[3]
    tx = X(85.0)
    ta, tb = tx - 4.0, tx + 4.0
    for xa, xb in ((x0, ta), (tb, x1)):
        b.box([(xa + xb) / 2.0, 11.0, (z0 + z1) / 2.0], [xb - xa, 22.0, z1 - z0], BASALT)
    b.box([tx, (7.5 + 22.0) / 2.0, (z0 + z1) / 2.0], [8.0, 22.0 - 7.5, z1 - z0], BASALT)
    b.box([(x0 + x1) / 2.0, 22.6, (z0 + z1) / 2.0], [x1 - x0 - 2.0, 1.2, z1 - z0 - 2.0], "#3a5a2a",
          collide=False)
    slab(b, (ta, tb, z0, z1), 0.1, 0.1, "#5a4a3a")
    # the timber frames at the mouths, props along the tunnel
    for z in (z0 + 0.6, z1 - 0.6, (z0 + z1) / 2.0):
        for xx in (ta + 0.4, tb - 0.4):
            b.box([xx, 0.1 + 3.7, z], [0.8, 7.4, 0.8], TIMBER)
        b.box([tx, 7.0, z], [8.0, 0.8, 0.8], TIMBER, collide=False)
    # rails, a cart, lamps on the walls, a vein of gold
    for dx in (-1.2, 1.2):
        b.box([tx + dx, 0.14, (z0 + z1) / 2.0], [0.24, 0.08, z1 - z0], IRON, material="metal",
              collide=False)
    b.box([tx, 0.2 + 1.3, z0 + 10.0], [3.0, 2.2, 4.4], "#5a4a3a")
    b.box([tx, 0.2 + 2.5, z0 + 10.0], [2.6, 0.4, 4.0], "#e8b830", material="metal",
          collide=False)
    for z in (z0 + 8.0, z1 - 8.0):
        b.box([ta + 0.3, 4.0, z], [0.6, 0.4, 0.8], IRON, material="metal")
        b.box([ta + 0.35, 4.7, z], [0.5, 1.0, 0.5], "#ffcf7a", material="neon")
    b.box([tb - 0.06, 3.0, (z0 + z1) / 2.0 + 4.0], [0.12, 2.4, 6.0], "#e8b830", material="metal")
    isle.loot(tx, 0.2, (z0 + z1) / 2.0, "gem", "the gold mine")
    isle.loot(tx, 0.2, z1 - 4.0, "bar", "the gold mine")
    isle.dig(tx, 0.1, z0 + 4.0, "the end of the mine")
    # ---- the hot spring: rocks round it, steam
    sx0, sx1 = sorted((X(SPRING[0]), X(SPRING[1])))
    for xa, za in ((sx0 - 2.0, SPRING[2] + 2.0), (sx1 + 2.0, SPRING[3] - 3.0)):
        isle.rock(xa, za, 3.0, 3.0, 1.8)
    isle.loot((sx0 + sx1) / 2.0, -1.2, (SPRING[2] + SPRING[3]) / 2.0, "gem", "the hot spring")
    # ---- the treasure hunters' camp by the beach
    cx0, cx1 = sorted((X(CAMP[0]), X(CAMP[1])))
    tent(b, (cx0, cx1, CAMP[2], CAMP[3]), 6.4, "#c8b890" if west else "#d8c8a0",
         doors={"z-": [((cx0 + cx1) / 2.0 - 2.4, (cx0 + cx1) / 2.0 + 2.4, 5.8)]}, floor="#6a5a48")
    isle.campfire(X(76.0), 68.0)
    isle.crates(X(100.0) - (3.8 if not west else 0.0), 64.0, n=3)
    isle.loot((cx0 + cx1) / 2.0, 0.4, 80.0, "any", "the hunters' tent")
    # ---- the jungle: palms, bamboo, boulders of obsidian, giant ferns
    for x, z in ((104.0, -50.0), (104.0, 30.0), (104.0, 60.0), (100.0, 90.0), (60.0, -30.0),
                 (78.0, 26.0), (46.0, 20.0), (62.0, 84.0), (90.0, 46.0), (44.0, -40.0),
                 (52.0, 50.0), (88.0, -4.0)):
        px, pz = X(x + rng.uniform(-2.0, 2.0)), z + rng.uniform(-2.0, 2.0)
        if isle.clear(px, pz, 2.0):
            isle.palm(px, pz, h=rng.uniform(13.0, 19.0))
    for x, z in ((48.0, -24.0), (80.0, 52.0), (40.0, 80.0)):
        if not isle.clear(X(x), z, 4.0):
            continue
        y = isle.top(X(x), z)
        for k in range(6):
            a = k * 1.05
            b.cyl([X(x) + math.cos(a) * 1.6, y + 5.0 + k * 0.4, z + math.sin(a) * 1.6],
                  [0.7, 10.0 + k * 0.8, 0.7], "#7aa84a" if k % 2 else "#6a983a")
    for x, z, w in ((58.0, -6.0, 5.0), (84.0, 30.0, 4.0), (40.0, 30.0, 4.4), (66.0, 66.0, 3.6)):
        if isle.clear(X(x), z, 3.0):
            isle.rock(X(x), z, w, w * 0.8, w * 0.6, colour=OBSIDIAN, cap=BASALT)
    for x, z in ((52.0, -12.0), (76.0, 40.0), (40.0, 58.0), (90.0, 10.0), (60.0, 30.0)):
        if isle.clear(X(x), z, 3.0):
            isle.fern(X(x), z, colour="#4a7a2a")
    # ---- X's, loot
    isle.dig(X(92.0), None, 26.0, "the black beach" if west else "the black sand")
    isle.dig(X(60.0), None, -56.0, "under the volcano")
    isle.dig(X(46.0), None, 30.0, "the jungle")
    isle.loot(X(104.0), None, -30.0, "any", "the beach")
    isle.loot(X(66.0), None, 2.0, "any", "the jungle")
    # the torches along the beach
    for z in (-28.0, 28.0):
        isle.torch(X(108.0), z)


def _rain(isle: Isle) -> None:
    """Where the eruption's bombs come down and its gold lands: open
    ground all over the island (both halves alike)."""
    b = isle.b
    spots = [(100.0, -40.0), (100.0, 0.0), (100.0, 46.0), (78.0, -50.0), (72.0, -10.0),
             (60.0, 20.0), (80.0, 60.0), (50.0, 80.0), (40.0, -50.0), (44.0, 6.0), (36.0, 98.0),
             (20.0, -40.0)]
    for x, z in spots:
        for sgn in (-1.0, 1.0):
            px = sgn * x
            b.mark("rain", px, isle.top(px, z), z)
    for x, z in ((0.0, -14.0), (0.0, 30.0), (-23.0, -10.0), (23.0, 26.0)):
        b.mark("rain", x, isle.top(x, z), z)


# ================================================================ meta
def _meta(isle: Isle) -> None:
    b = isle.b
    for x, z, name in ((-85.0, -40.0, "the west mine"), (85.0, -40.0, "the east mine"),
                       (-60.0, 62.0, "the west hot spring"), (60.0, 62.0, "the east hot spring"),
                       (0.0, -50.0, "the north bridge"), (0.0, 64.0, "the south bridge"),
                       (0.0, 86.0, "the lava pool"),
                       (-SHIP_X, 0.0, "the Scarlet Queen"), (SHIP_X, 0.0, "the Blue Marlin")):
        b.landmark(x, z, name)
    b.camera(0.0, 60.0, 116.0, 0.0, 4.0, 0.0)
    b.camera(-140.0, 40.0, 90.0, -40.0, 0.0, 0.0)
    b.camera(140.0, 40.0, -80.0, 40.0, 0.0, 0.0)
    b.camera(-40.0, 30.0, 8.0, 0.0, 12.0, 8.0)
    b.extra.update({"twist": "eruption", "water": SEA_TOP, "eruption_every": [55.0, 75.0],
                    "eruption_for": 26.0, "warn": 6.0, "lava": [list(r) for r in RIVERS],
                    "lava_y": KILL_Y,
                    "bridges": [[x0, x1, z0, z1, BRIDGE_TOP] for x0, x1, z0, z1, _a in BRIDGES],
                    # the crater the eruption is thrown out of (no place to go)
                    "vent": [0.0, 48.0, -99.0]})


def build(b: ArenaArea) -> None:
    rng = random.Random(9394)
    isle = Isle(b, rng)
    _land(isle)
    _edges(isle)
    _volcano(isle)
    _temple(isle)
    _bridges(isle)
    _half(isle, -1.0)
    _half(isle, 1.0)
    _rain(isle)
    galleon(isle, "red", 0.0)
    galleon(isle, "blue", 0.0)
    _meta(isle)
