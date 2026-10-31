"""Skull Cove: a horseshoe island round a lagoon, under a rock shaped like a
skull with a cave in its mouth.

Layout (north is -z; the Scarlet Corsairs' ship is moored off the west end,
the Azure Buccaneers' off the east)::

    z -136  ======== cliffs ==== SKULL ROCK (the cave, the idol) ==== cliffs ======
    z  -70  graves  tower  rocks |   the north beach   | rocks  tower  graves
    z  -46        W                ~~~~ THE LAGOON ~~~~                 E
   SCARLET  jungle, knoll, hut     the sunken sloop, the sandbar  hut, knoll, jungle  BLUE
    QUEEN                          ~~~~~~~~~~~~~~~~~~~~                          MARLIN
    z   30                               | channel |
    z   70      the west camp  ===== rope bridge =====  the east camp
    z  104  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ south sea ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The two halves are mirror images, for fairness: each crew has its own end
of the jungle with its hut, its knoll, its lookout tower and its graves,
and its half of the camp; everything in the middle -- the skull, the
lagoon, the bridge -- is as far from one ship as from the other.

The twist is the tide (``extra["twist"] = "tide"``): the sea falls from
high water to low and back, three levels (switchable water sheets in the
``tide`` group), and while it is out the sandbar across the lagoon is dry,
the sunken sloop's deck is above water and treasure lies on the lagoon
floor (``sunken`` marks) -- for as long as the tide stays out.
"""
from __future__ import annotations

import math
import random

from ..calamity_coast.town import skirt
from ..kit import ArenaArea, backdrop, flight, rect, slab
from ...lastlight.kit import tent, watchtower
from .common import (CANVAS, DECKING, HULL, HULL_DARK, IRON, PLANK, ROCK, ROCK_DARK,
                     ROCK_LIGHT, ROPE, SAND, SAND_DARK, SAND_WET, SEA, SHIP_X, SHORE_X, TIMBER,
                     TRIM, Isle, galleon)

HALF = (170.0, 120.0)
SKY = {"top": "#3f86d4", "horizon": "#f4dcb0", "sun": [0.55, 0.42, 0.3], "clouds": 0.55,
       "tint": "#fff2dc"}
AMBIENT = "#b4b8c4"
GROUND = "#4f8a3e"
FOG = 880.0

TURF = "#4f8a3e"
JUNGLE = "#3f7a34"
UNDER = "#447f38"           # the jungle floor
PATH = "#c8b07a"
BONE = "#d8cfb8"
BONE_DARK = "#b8ae96"
CAVE = "#4a463e"
HIGH = -1.0                 # high water
MID = -3.0
LOW = -5.0                  # low water
BED = -6.0                  # the seabed out by the ships, and the lagoon floor
BAR = -3.6                  # the sandbar's top: dry from mid tide down
LAGOON = (-46.0, 46.0, -46.0, 30.0)
CHANNEL = (-8.0, 8.0, 30.0, 104.0)
SOUTH = 104.0               # the south shore
SKULL_FRONT = -70.0         # the face of Skull Rock
CLIFF = -86.0               # the foot of the north cliffs either side of it
BACK = -120.0               # the north edge of the playable ground
RING_W = 4.0
RINGS = (-1.5, -3.0, -4.5)  # the lagoon's banks, stepping down to its floor
BEACH = (-1.2, -2.4, -3.6, -4.8)
BEACH_W = 3.0
# what the ground covers keep clear of: the tents, the huts, the towers,
# the knolls, the cave's floor
TENTS = [(40.0, 58.0, 54.0, 66.0), (20.0, 32.0, 40.0, 50.0)]
HUT = (76.0, 90.0, 34.0, 46.0)
TOWER = (86.0, 98.0, -60.0, -20.0)
KNOLL = (50.0, 62.0, -10.0, 2.0)
CAVE_FLOOR = (-14.0, 14.0, -102.0, -70.0)


def _mirror(r):
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
    isle.land(TURF, holes=[west, east, south, LAGOON, CHANNEL])
    # the seabed out by the ships and round the south shore; the lagoon's
    # floor; the channel's
    for area in (west, east, south):
        slab(b, area, BED, 3.0, SAND_WET, studs=True)
    slab(b, LAGOON, BED, 3.0, "#c8b884", studs=True)
    slab(b, CHANNEL, MID, 6.0, SAND_WET, studs=True)
    # beaches going down into the sea, a step lower each strip
    for k, top in enumerate(BEACH):
        colour = SAND if k == 0 else SAND_WET
        for sgn in (-1.0, 1.0):
            xa, xb = sorted((sgn * (SHORE_X + BEACH_W * k), sgn * (SHORE_X + BEACH_W * (k + 1))))
            b.box([(xa + xb) / 2.0, (BED + top) / 2.0, (BACK + hz) / 2.0],
                  [xb - xa, top - BED, hz - BACK], colour, studs=True)
        za, zb = SOUTH + BEACH_W * k, SOUTH + BEACH_W * (k + 1)
        spans = [(-SHORE_X, CHANNEL[0]), (CHANNEL[1], SHORE_X)] if k < 2 else [(-SHORE_X, SHORE_X)]
        for xa, xb in spans:
            b.box([(xa + xb) / 2.0, (BED + top) / 2.0, (za + zb) / 2.0],
                  [xb - xa, top - BED, zb - za], colour, studs=True)
    # the channel's floor carries on out to the beach's third strip
    b.box([0.0, (BED + MID) / 2.0, SOUTH + BEACH_W], [16.0, MID - BED, 2 * BEACH_W], SAND_WET,
          studs=True)
    # the lagoon's banks: rings stepping down, the channel cutting the top one
    x0, x1, z0, z1 = LAGOON
    for k, top in enumerate(RINGS):
        a, c = k * RING_W, (k + 1) * RING_W
        colour = SAND if k == 0 else (SAND_WET if k == 1 else "#c0ae7a")
        for xa, xb in ((x0 + a, x0 + c), (x1 - c, x1 - a)):
            b.box([(xa + xb) / 2.0, (BED + top) / 2.0, (z0 + a + z1 - a) / 2.0],
                  [xb - xa, top - BED, (z1 - a) - (z0 + a)], colour, studs=True)
        b.box([0.0, (BED + top) / 2.0, z0 + (a + c) / 2.0],
              [(x1 - c) - (x0 + c), top - BED, c - a], colour, studs=True)
        spans = [(x0 + c, CHANNEL[0]), (CHANNEL[1], x1 - c)] if k == 0 else [(x0 + c, x1 - c)]
        for xa, xb in spans:
            b.box([(xa + xb) / 2.0, (BED + top) / 2.0, z1 - (a + c) / 2.0],
                  [xb - xa, top - BED, c - a], colour, studs=True)
    b.box([0.0, (BED + MID) / 2.0, z1 - RING_W / 2.0], [16.0, MID - BED, RING_W], SAND_WET,
          studs=True)
    # the sandbar across the lagoon, dry from mid tide down
    inner = x1 - 3 * RING_W
    b.box([0.0, (BED + BAR) / 2.0, -5.0], [2 * inner, BAR - BED, 6.0], SAND, studs=True)
    # covers on the turf -- the beaches, the camp's sand, the trails, the
    # jungle floor -- kept off everything that stands on the ground itself
    s = isle.s
    for r in TENTS + [HUT, TOWER, KNOLL]:
        s.reserve(r)
        s.reserve(_mirror(r))
    s.reserve(CAVE_FLOOR)
    s.lay(rect(-SHORE_X, -96.0, CLIFF, SOUTH), 0.1, SAND)
    s.lay(rect(96.0, SHORE_X, CLIFF, SOUTH), 0.1, SAND)
    s.lay(rect(-96.0, 96.0, 88.0, SOUTH), 0.1, SAND)
    s.lay(rect(-46.0, 46.0, SKULL_FRONT, -46.0), 0.1, SAND)
    s.lay(rect(-46.0, 46.0, 30.0, 88.0), 0.1, SAND_DARK)
    for sgn in (-1.0, 1.0):
        def X(x: float, sgn: float = sgn) -> float:
            return sgn * x
        isle.trail([(X(109.5), -15.0), (X(92.0), -15.0), (X(92.0), -27.0), (X(74.0), -27.0),
                    (X(74.0), -50.0), (X(51.0), -50.0)], colour=PATH)
        isle.trail([(X(109.5), 15.0), (X(98.0), 15.0), (X(98.0), 6.0), (X(72.0), 6.0),
                    (X(72.0), 22.0), (X(51.0), 22.0)], colour=PATH)
        isle.trail([(X(76.0), 40.0), (X(68.0), 40.0), (X(68.0), 58.0), (X(51.0), 58.0)],
                   colour=PATH)
        isle.trail([(X(92.0), -20.0), (X(92.0), -15.0)], colour=PATH)
        xa, xb = sorted((X(96.0), X(46.0)))
        s.lay(rect(xa, xb, CLIFF, 88.0), 0.04, UNDER)


def _water(isle: Isle) -> None:
    """The sea at three heights, switched by the tide: high water is on."""
    b = isle.b
    hx, hz = HALF
    m = b.margin
    seas = [(-hx, -SHORE_X, BACK, hz), (SHORE_X, hx, BACK, hz), (-SHORE_X, SHORE_X, SOUTH, hz)]
    for key, level in (("tide_hi", HIGH), ("tide_mid", MID), ("tide_lo", LOW)):
        with b.detached() as parts:
            for area in seas:
                isle.water(area, BED, level, colour=SEA)
            isle.water(LAGOON, BED, level, colour="#2a9aaa")
            if level > MID:
                isle.water(CHANNEL, MID, level, colour="#2a9aaa")
        b.dynamic(key, parts, on=(key == "tide_hi"), group="tide")
    # beyond the breakwaters the open sea is always there
    for x0, x1, z0, z1 in ((-hx - m - 300.0, -hx - m, -hz - m - 300.0, hz + m + 300.0),
                           (hx + m, hx + m + 300.0, -hz - m - 300.0, hz + m + 300.0),
                           (-hx - m, hx + m, hz + m, hz + m + 300.0)):
        b.box([(x0 + x1) / 2.0, (BED - 2.0 + HIGH) / 2.0, (z0 + z1) / 2.0],
              [x1 - x0, HIGH - BED + 2.0, z1 - z0], SEA, material="glass", alpha=0.6,
              collide=False)


def _edges(isle: Isle) -> None:
    """The north edge is cliff (and the skull); the other three are
    breakwaters of rock out in the sea."""
    b = isle.b
    rng = isle.rng
    hx, hz = HALF
    m = b.margin
    rocks = [ROCK, ROCK_DARK, "#9a8f7c", ROCK]
    for sgn in (-1.0, 1.0):
        a0, a1 = sorted((sgn * 36.0, sgn * SHORE_X))
        faces = isle.cliffs("x", a0, a1, -hz - m, CLIFF, 28.0, rocks, green=JUNGLE)
        # a waterfall down the face of one segment, into a pool
        u0, u1, face = next(f for f in faces if f[0] <= sgn * 99.0 <= f[1])
        fx = sgn * 99.0
        b.box([fx, 14.0, face + 0.4], [6.0, 28.0, 0.8], "#9ad8f0", material="glass", alpha=0.6,
              collide=False)
        b.cyl([fx, isle.top(fx, face + 4.0) + 0.1, face + 4.0], [10.0, 0.2, 6.0], "#bfe8f8",
              material="glass", alpha=0.7, collide=False)
        a0, a1 = sorted((sgn * SHORE_X, sgn * (hx + m)))
        # (too tall to jump on to from the breakwater)
        isle.cliffs("x", a0, a1, -hz - m, BACK, 36.0, rocks, base=BED, green=JUNGLE,
                    step=14.5, recess=0.0)
        b.box([sgn * (hx + m / 2.0), (BED + 6.0) / 2.0, (BACK + hz + m) / 2.0],
              [m, 6.0 - BED, hz + m - BACK], ROCK)
    b.box([0.0, (BED + 6.0) / 2.0, hz + m / 2.0], [2 * hx, 6.0 - BED, m], ROCK)
    for k in range(20):
        z = BACK + (k + 0.5) * (hz + m - BACK) / 20.0
        for sgn in (-1.0, 1.0):
            b.box([sgn * (hx + m / 2.0) + rng.uniform(-1.0, 1.0), 6.0 + 1.0 + (k % 3) * 0.4, z],
                  [m - 2.0 - (k % 2) * 0.6, 2.0 + (k % 3) * 0.8, (hz + m - BACK) / 20.0 - 2.0],
                  ROCK_LIGHT if k % 2 else ROCK)
    for k in range(18):
        x = -hx + (k + 0.5) * 2 * hx / 18.0
        b.box([x, 6.0 + 1.0 + (k % 3) * 0.4, hz + m / 2.0 + rng.uniform(-1.0, 1.0)],
              [2 * hx / 18.0 - 2.0, 2.0 + (k % 3) * 0.8, m - 2.0 - (k % 2) * 0.6],
              ROCK if k % 2 else ROCK_LIGHT)
    skirt(b, hx, hz, "#c8b884", top=BED - 3.05)
    backdrop(b, "hills", 20.0, rng, sides=("z-",), colours=["#3f7a3a", "#4a8a44", "#356a32"])


# ============================================================ skull rock
def _skull(isle: Isle) -> None:
    """The rock, the cave in its mouth, and what is in the cave."""
    b = isle.b
    rng = isle.rng
    hz = HALF[1]
    m = b.margin
    back = -hz - m
    f = SKULL_FRONT
    floor = 0.1
    slab(b, CAVE_FLOOR, floor, floor, CAVE)
    # the solid of it: two cheeks, the back, the roof over the cave, the
    # jaw either side of the mouth and the lintel over it
    b.box([-25.0, 15.0, (back + f) / 2.0], [22.0, 30.0, f - back], BONE)
    b.box([25.0, 15.0, (back + f) / 2.0], [22.0, 30.0, f - back], BONE)
    b.box([0.0, 15.0, (back - 102.0) / 2.0], [28.0, 30.0, -102.0 - back], BONE_DARK)
    b.box([0.0, 21.0, (-102.0 + f) / 2.0], [28.0, 18.0, f + 102.0], BONE)
    for sgn in (-1.0, 1.0):
        b.box([sgn * 10.5, (floor + 12.0) / 2.0, f - 2.0], [7.0, 12.0 - floor, 4.0], BONE_DARK)
    b.box([0.0, 11.0, f - 2.0], [14.0, 2.0, 4.0], BONE_DARK)
    # the cranium over it all
    b.sphere([0.0, 34.0, -98.0], [74.0, 40.0, 54.0], BONE, collide=False)
    b.sphere([0.0, 46.0, -100.0], [52.0, 22.0, 40.0], "#e4dcc8", collide=False)
    # its face: the brow, eye sockets with a fire deep in them, the nose,
    # the cheekbones, cracks and moss
    b.box([0.0, 30.0, f + 0.8], [52.0, 3.0, 1.6], "#e4dcc8", collide=False)
    for sgn in (-1.0, 1.0):
        b.sphere([sgn * 12.0, 22.0, f + 0.4], [13.0, 11.0, 3.0], "#141210", collide=False)
        b.sphere([sgn * 12.0, 21.0, f + 1.6], [4.0, 3.2, 1.2], "#ff5a1a", material="neon",
                 collide=False)
        b.box([sgn * 21.0, 13.0, f + 0.6], [9.0, 4.0, 1.2], "#e4dcc8", collide=False)
        b.box([sgn * 2.0, 15.4, f + 0.4], [1.4, 5.0, 0.8], "#141210", collide=False,
              r=[0.0, 0.0, sgn * 0.45])
        b.box([sgn * 17.0, 8.0, f + 0.08], [0.4, 6.0, 0.16], "#8a8270", collide=False,
              r=[0.0, 0.0, sgn * 0.3])
        b.box([sgn * 30.0, 18.0, f + 0.3], [8.0, 6.0, 0.6], "#5a7a3a", collide=False)
    # the teeth: points hanging from the lintel, two standing either side
    for k in range(7):
        x = -6.0 + k * 2.0
        b.cone([x, 9.0, f + 0.2], [1.4, 2.0, 1.0], "#f0e8d4", collide=False,
               r=[math.pi, 0.0, 0.0])
    for sgn in (-1.0, 1.0):
        b.box([sgn * 7.6, 0.1 + 1.2, f + 0.6], [1.2, 2.4, 1.2], "#f0e8d4")
    # inside: torches on the walls, heaps of gold, bones, the altar
    for x, z in ((-13.2, -80.0), (13.2, -80.0), (-13.2, -96.0), (13.2, -96.0)):
        sgn = -1.0 if x < 0 else 1.0
        b.box([x, 6.2, z], [1.6, 0.4, 0.8], IRON, material="metal", collide=False)
        b.cone([x - sgn * 0.3, 7.0, z], [0.7, 1.2, 0.7], "#ffb03a", material="neon",
               collide=False)
    for x, z, w in ((-9.0, -100.0, 5.0), (9.0, -100.0, 5.0), (-11.0, -88.0, 3.6),
                    (11.0, -86.0, 3.6)):
        b.sphere([x, floor + 0.5, z], [w, 1.4, w * 0.8], "#e8b830", material="metal")
        b.sphere([x + 0.6, floor + 1.2, z - 0.2], [w * 0.5, 0.8, w * 0.4], "#f4cc48",
                 material="metal", collide=False)
    for x, z, a in ((-6.0, -84.0, 0.3), (5.0, -90.0, -0.8)):
        b.box([x, floor + 0.12, z], [2.6, 0.24, 0.5], "#ece4d0", collide=False, r=[0.0, a, 0.0])
        b.sphere([x + 1.6, floor + 0.45, z + 0.5], [0.9, 0.9, 0.9], "#ece4d0", collide=False)
    for x, z in ((-12.0, -76.0), (12.0, -76.0), (-12.0, -100.0), (12.0, -100.0)):
        b.cone([x, floor + 1.6, z], [2.0, 3.2, 2.0], ROCK_DARK)
        b.cone([x, 10.8, z], [1.6, 2.4, 1.6], ROCK_DARK, collide=False, r=[math.pi, 0.0, 0.0])
    isle.idol(0.0, floor, -94.0)
    # boulders fallen at the foot of the cliffs either side
    for sgn in (-1.0, 1.0):
        for k in range(4):
            x = sgn * (44.0 + k * 17.0 + rng.uniform(-3.0, 3.0))
            isle.rock(x, CLIFF + 5.0 + rng.uniform(0.0, 2.0), rng.uniform(5.0, 8.0),
                      rng.uniform(3.6, 5.0), rng.uniform(3.0, 6.0))


# ============================================================== the lagoon
def _lagoon(isle: Isle) -> None:
    b = isle.b
    rng = isle.rng
    # the sloop that sank in it: a broken hull on the bottom, its deck
    # awash at high water and dry at low, its mast still standing
    deck = -2.6
    b.box([0.0, (BED + deck) / 2.0, -20.0], [20.0, deck - BED, 8.0], HULL)
    b.box([12.0, (BED + deck - 0.6) / 2.0, -20.0], [4.0, deck - 0.6 - BED, 5.6], HULL)
    b.box([15.2, (BED + deck - 1.2) / 2.0, -20.0], [2.4, deck - 1.2 - BED, 3.0], HULL_DARK)
    b.box([-11.6, (BED + deck - 1.6) / 2.0, -20.0], [3.2, deck - 1.6 - BED, 6.4], HULL_DARK)
    # its stove-in side, a step up from the bottom to the deck
    b.box([0.0, (BED + deck - 1.7) / 2.0, -14.8], [12.0, deck - 1.7 - BED, 2.4], HULL_DARK)
    for k, x in enumerate((-8.0, -4.0, 0.0, 4.0, 8.0)):
        b.box([x, deck + 0.05, -20.0], [3.6, 0.1, 7.6], DECKING if k % 2 else "#8a6a48",
              collide=False)
    # ribs standing up where the side is gone, the mast leaning, a rag of sail
    for k in range(4):
        b.box([-6.0 + k * 3.6, deck + 1.5, -23.7], [0.5, 3.0, 0.6], HULL_DARK)
    lean, length = 0.32, 14.0
    mx, my = 2.0 + math.sin(lean) * length / 2.0, deck + math.cos(lean) * length / 2.0
    b.cyl([mx, my, -20.0], [1.2, length, 1.2], TIMBER, collide=False, r=[0.0, 0.0, -lean])
    tx, ty = 2.0 + math.sin(lean) * length * 0.8, deck + math.cos(lean) * length * 0.8
    b.box([tx + 0.2, ty - 2.2, -19.3], [5.0, 4.0, 0.16], "#d8d0b8", collide=False,
          r=[0.0, 0.0, -lean * 0.5])
    b.box([-6.0, deck + 0.9, -20.4], [6.0, 1.8, 1.2], "#7a4a28")
    b.box([-6.0, deck + 1.95, -20.4], [6.2, 0.3, 1.4], TRIM, material="metal")
    # an islet with a palm, rocks standing up out of the water, weed
    b.box([26.0, (BED + 0.4) / 2.0, 12.0], [10.0, 0.4 - BED, 8.0], SAND, studs=True)
    b.box([26.0, 0.4 + 0.3, 12.0], [6.0, 0.6, 4.0], "#d8c48c", studs=True)
    isle.palm(25.0, 12.0, 1.0, 13.0)
    for x, z, w in ((-30.0, 14.0, 6.0), (-26.0, -28.0, 4.0), (26.0, -28.0, 4.6), (12.0, 6.0, 3.0)):
        b.box([x, BED + 2.2, z], [w, 4.4, w * 0.8], ROCK)
        b.box([x + 0.4, BED + 4.4 + 0.5, z - 0.3], [w * 0.6, 1.0, w * 0.5], ROCK_LIGHT)
    for x, z in ((-12.0, 6.0), (16.0, 2.0), (-4.0, 18.0), (18.0, -32.0), (-18.0, -12.0)):
        b.box([x, BED + 0.08, z], [3.0, 0.16, 1.2], "#3a7a4a", collide=False,
              r=[0.0, x * 0.1, 0.0])
    # boulders round the banks, sitting on the top ring
    x0, x1, z0, z1 = LAGOON
    for x, z, w, d in ((x0 + 2.0, z0 + 6.0, 4.0, 7.0), (x1 - 2.0, z0 + 8.0, 4.0, 6.0),
                       (x0 + 2.0, 12.0, 4.0, 5.0), (x1 - 2.0, -24.0, 4.0, 6.0),
                       (-26.0, z0 + 2.0, 6.0, 4.0), (30.0, z0 + 2.0, 7.0, 4.0)):
        h = rng.uniform(2.0, 3.6)
        b.box([x, RINGS[0] + h / 2.0, z], [w, h, d], ROCK if w > 4.0 else ROCK_DARK)
    # a jetty out from the south bank each side, a rowboat beside it
    for sgn in (-1.0, 1.0):
        jx = sgn * 22.0
        b.box([jx, 0.4, 22.5], [4.0, 0.4, 15.0], PLANK)
        for z in (16.0, 22.0):
            for dx in (-1.6, 1.6):
                b.cyl([jx + dx, (BED + 0.2) / 2.0, z], [0.6, 0.2 - BED, 0.6], TIMBER)
        bx = jx + sgn * 4.4
        b.box([bx, (RINGS[1] - 0.6) / 2.0, 24.0], [3.0, -0.6 - RINGS[1], 6.0], "#8a5a34")
        b.box([bx, -0.57, 24.0], [2.2, 0.06, 5.0], "#3a2a1a", collide=False)
    # what lies on the bottom when the tide goes out
    for x, y, z in ((-20.0, BED, -31.0), (20.0, BED, -31.0), (0.0, BED, -31.0),
                    (-6.0, deck, -18.0), (6.0, deck, -21.0), (-22.0, BED, 2.0), (16.0, BED, 18.0)):
        b.mark("sunken", x, y, z)


# ============================================================== the jungle
def _jungle(isle: Isle, sgn: float) -> None:
    """One end of the jungle (``sgn`` -1 west, +1 east): a hut, a knoll, a
    lookout tower, graves under the cliff, palms and rocks, the beach by
    the ship."""
    b = isle.b
    rng = isle.rng

    def X(x: float) -> float:
        return sgn * x

    west = sgn < 0
    # the hut in its clearing, its door facing the lagoon
    xa, xb = sorted((X(HUT[0]), X(HUT[1])))
    isle.hut((xa, xb, HUT[2], HUT[3]), "x+" if west else "x-",
             colour="#a8845a" if west else "#9a7a52")
    inside = (xa + xb) / 2.0
    b.box([inside, 0.4 + 1.0, 43.4], [4.0, 2.0, 2.0], TIMBER)
    b.box([inside - sgn * 2.4, 0.4 + 0.15, 39.0], [3.0, 0.3, 5.0], "#c8b8a0", collide=False)
    isle.barrel(inside - sgn * 3.6, 36.8, 0.4)
    # its garden: a row of posts with a rail, and the patch beside it
    for k in range(6):
        x = X(73.0 + k * 3.0)
        b.cyl([x, isle.top(x, 54.0) + 1.2, 54.0], [0.6, 2.4, 0.6], TIMBER)
    b.box([X(80.5), 0.04 + 2.0, 54.0], [15.4, 0.3, 0.3], TIMBER, collide=False)
    # the lookout tower over the north end of the jungle
    watchtower(b, X(92.0), -54.0, h=16.0, colour=TIMBER, stair="z+")
    isle.flag(X(92.0) + sgn * 5.4, -59.4, 26.2, "#141414")
    # the knoll: a block of rock with steps up its south side, an X on top
    k0, k1 = sorted((X(KNOLL[0]), X(KNOLL[1])))
    b.box([(k0 + k1) / 2.0, 3.0, (KNOLL[2] + KNOLL[3]) / 2.0],
          [k1 - k0, 6.0, KNOLL[3] - KNOLL[2]], ROCK)
    b.box([(k0 + k1) / 2.0, 6.3, (KNOLL[2] + KNOLL[3]) / 2.0 - 1.0],
          [k1 - k0 - 1.6, 0.6, KNOLL[3] - KNOLL[2] - 3.6], "#5a8a44")
    sx = X(56.0)
    flight(b, "z", KNOLL[3] + 6.0, KNOLL[3], sx - 2.4, sx + 2.4, 0.04, 6.0, ROCK_DARK, fill=0.04)
    isle.palm(X(60.0), -6.0, 6.6, 12.0)
    # graves under the cliff: crosses and mounds
    for k in range(4):
        gx, gz = X(74.0 + (k % 2) * 6.0), -70.0 + (k // 2) * 6.0
        y = isle.top(gx, gz)
        b.box([gx, y + 0.1, gz + 1.6], [2.0, 0.2, 3.4], "#6a5a40", collide=False)
        b.box([gx, y + 1.4, gz - 0.4], [0.4, 2.8, 0.4], TIMBER)
        b.box([gx, y + 2.2, gz - 0.4], [1.8, 0.4, 0.4], TIMBER)
    # palms along the beach, palms and bushes through the jungle (none on a
    # trail)
    for z in (-72.0, -44.0, -30.0, 24.0, 62.0, 84.0, 98.0):
        x, zz = X(104.0 + rng.uniform(-3.0, 3.0)), z + rng.uniform(-2.0, 2.0)
        if isle.clear(x, zz, 2.0):
            isle.palm(x, zz, h=rng.uniform(12.0, 18.0))
    for x, z in ((58.0, -64.0), (84.0, -36.0), (60.0, -32.0), (88.0, -6.0), (58.0, 12.0),
                 (84.0, 26.0), (56.0, 40.0), (92.0, 62.0), (60.0, 76.0), (82.0, 84.0),
                 (80.0, -8.0), (64.0, -40.0), (90.0, 48.0)):
        x, z = X(x + rng.uniform(-2.0, 2.0)), z + rng.uniform(-2.0, 2.0)
        if isle.clear(x, z, 2.0):
            isle.palm(x, z, h=rng.uniform(13.0, 19.0))
    for x, z in ((70.0, -66.0), (52.0, -42.0), (82.0, -30.0), (54.0, 18.0), (84.0, 0.0),
                 (90.0, 30.0), (62.0, 66.0), (86.0, 72.0), (52.0, 84.0), (66.0, -18.0),
                 (78.0, 14.0), (58.0, 48.0)):
        if isle.clear(X(x), z, 3.0):
            isle.bush(X(x), z, size=rng.uniform(2.6, 4.0))
    for x, z in ((76.0, -44.0), (60.0, -20.0), (86.0, 10.0), (64.0, 30.0), (88.0, 54.0),
                 (74.0, 80.0), (54.0, -60.0), (82.0, 66.0)):
        if isle.clear(X(x), z, 2.6):
            isle.fern(X(x), z)
    # rocks: one big enough to stand on, a step up it on the south side
    top = isle.rock(X(58.0), 30.0, 7.0, 6.0, 4.0)
    b.box([X(58.0), 0.04 + 1.0, 34.5], [4.0, 2.0, 3.0], ROCK_DARK)
    isle.rock(X(84.0), -12.0, 6.0, 5.0, 3.2)
    # the beach by the ship: a rowboat drawn up, nets drying, crates
    bx = X(104.0)
    y = isle.top(bx, -40.0)
    b.box([bx, y + 0.85, -40.0], [4.6, 1.7, 10.0], "#8a5a34")
    b.box([bx, y + 1.75, -40.0], [3.4, 0.1, 8.6], "#3a2a1a", collide=False)
    b.box([bx, y + 1.85, -38.0], [4.4, 0.3, 0.8], TIMBER, collide=False)
    isle.crates(X(100.0) - (3.8 if not west else 0.0), 28.0, n=3)
    for k in range(3):
        b.cyl([X(98.0), 0.1 + 2.0, 60.0 + k * 4.0], [0.5, 4.0, 0.5], TIMBER)
    net = b.box([X(98.0), 0.1 + 3.2, 64.0], [0.2, 2.4, 8.4], "#c8c0a8", decal="netting")
    net["dw"] = 1
    isle.torch(X(108.0), -24.0)
    isle.torch(X(108.0), 24.0)
    # marks: X's, loose treasure, the hut, the tower top, the knoll, the rock
    isle.dig(X(86.0), None, -34.0, "the twin palms" if west else "the east palms")
    isle.dig(X(80.0), None, 58.0, "the hermit's garden" if west else "the old garden")
    isle.dig(X(56.0), 6.6, -5.0, "the top of the knoll")
    isle.dig(X(77.0), None, -67.0, "the pirates' graves")
    isle.loot(X(100.0), None, 72.0, "bar", "the beach")
    isle.loot(X(96.0), None, -64.0, "any", "the north beach")
    isle.loot(X(72.0), None, 12.0, "any", "the jungle path")
    isle.loot(inside, 0.4, 40.0, "any", "the hut")
    isle.loot(X(92.0), 16.8, -54.0, "bar", "the lookout")
    isle.loot(X(58.0), top, 29.0, "gem", "the big rock")


# ================================================================ the camp
def _camp(isle: Isle) -> None:
    b = isle.b
    rng = isle.rng
    for sgn in (-1.0, 1.0):
        def X(x: float, sgn: float = sgn) -> float:
            return sgn * x
        for (x0, x1, z0, z1), h, colour in ((TENTS[0], 7.0, CANVAS if sgn < 0 else "#e8dcc0"),
                                            (TENTS[1], 6.4, "#c8b890")):
            xa, xb = sorted((X(x0), X(x1)))
            mid = (xa + xb) / 2.0
            tent(b, (xa, xb, z0, z1), h, colour, doors={"z+": [(mid - 2.4, mid + 2.4, h - 0.6)]},
                 floor="#7a6a52")
        isle.campfire(X(30.0), 72.0)
        for k in range(3):
            isle.barrel(X(52.0 + k * 3.0), 74.0)
        isle.crates(X(60.0) - (3.8 if sgn > 0 else 0.0), 80.0, n=4)
        isle.flag(X(18.0), 92.0, None, "#141414", h=14.0)
        for x, z in ((24.0, 96.0), (48.0, 92.0), (74.0, 98.0)):
            isle.palm(X(x), z, h=rng.uniform(12.0, 17.0))
        for x, z in ((36.0, 84.0), (40.0, 74.0)):
            y = isle.top(X(x), z)
            b.box([X(x), y + 0.5, z], [3.4, 1.0, 1.6], TIMBER)
        isle.torch(X(14.0), 62.0)
        isle.torch(X(44.0), 50.0)
        # bunting between two poles over the camp, out of reach
        for x in (34.0, 62.0):
            b.cyl([X(x), 0.1 + 5.0, 70.0], [0.5, 10.0, 0.5], TIMBER)
        b.box([X(48.0), 9.6, 70.0], [27.6, 0.12, 0.12], ROPE, collide=False)
        for k in range(9):
            fx = X(36.0 + k * 3.0)
            b.cone([fx, 8.9, 70.0], [1.2, 1.4, 0.1], ("#c8302a", "#e8b830", "#2a6ab8")[k % 3],
                   collide=False, r=[math.pi, 0.0, 0.0])
        isle.dig(X(36.0), None, 80.0, "the west camp" if sgn < 0 else "the east camp")
        isle.loot(X(49.0), 0.4, 60.0, "any", "the captain's tent")
        isle.loot(X(44.0), None, 92.0, "any", "the camp")
    # the rope bridge over the channel, with steps up to it each side
    y = 3.0
    isle.rope_bridge(-10.0, 10.0, 70.0, y, width=6.0, bed=MID)
    flight(b, "x", -18.0, -10.0, 67.0, 73.0, 0.1, y, TIMBER, fill=0.1)
    flight(b, "x", 18.0, 10.0, 67.0, 73.0, 0.1, y, TIMBER, fill=0.1)
    isle.loot(0.0, y, 70.0, "bar", "the rope bridge")


# ======================================================= the north beach
def _north_beach(isle: Isle) -> None:
    b = isle.b
    for sgn in (-1.0, 1.0):
        def X(x: float, sgn: float = sgn) -> float:
            return sgn * x
        isle.rock(X(38.0), -60.0, 6.0, 5.0, 3.6)
        isle.palm(X(22.0), -50.0, h=15.0)
        isle.palm(X(44.0), -52.0, h=13.0)
        isle.dig(X(24.0), None, -62.0, "under the skull's left eye" if sgn < 0
                 else "under the skull's right eye")
        isle.loot(X(12.0), None, -54.0, "any", "the north beach")
        isle.torch(X(16.0), -66.0)
    isle.dig(0.0, 0.1, -84.0, "deep in the skull")
    for x, z, kind in ((-10.0, -95.0, "gem"), (10.0, -95.0, "gem"), (0.0, -78.0, "any")):
        isle.loot(x, 0.1, z, kind, "the skull cave")
    # driftwood on the sand
    y = isle.top(-4.0, -52.0)
    b.box([-4.0, y + 0.5, -52.0], [10.0, 1.0, 1.2], TIMBER)
    b.box([6.0, y + 0.2, -58.0], [4.0, 0.4, 1.0], "#9a8a6a", collide=False, r=[0.0, 0.6, 0.0])


# ================================================================ meta
def _meta(isle: Isle) -> None:
    b = isle.b
    for x, z, name in ((0.0, -90.0, "the skull cave"), (0.0, -8.0, "the lagoon"),
                       (-78.0, 0.0, "the west jungle"), (78.0, 0.0, "the east jungle"),
                       (0.0, 70.0, "the rope bridge"), (-40.0, 70.0, "the west camp"),
                       (40.0, 70.0, "the east camp"), (0.0, -58.0, "the north beach"),
                       (-SHIP_X, 0.0, "the Scarlet Queen"), (SHIP_X, 0.0, "the Blue Marlin")):
        b.landmark(x, z, name)
    b.camera(0.0, 60.0, 110.0, 0.0, 0.0, -20.0)
    b.camera(-150.0, 40.0, 90.0, -60.0, 0.0, 0.0)
    b.camera(150.0, 40.0, -90.0, 60.0, 0.0, 0.0)
    b.camera(0.0, 30.0, -40.0, 0.0, 6.0, -80.0)
    b.extra.update({"twist": "tide", "water": HIGH, "levels": [HIGH, MID, LOW],
                    "tide_every": [55.0, 75.0], "tide_for": 28.0, "warn": 5.0})


def build(b: ArenaArea) -> None:
    rng = random.Random(6061)
    isle = Isle(b, rng)
    _land(isle)
    _water(isle)
    _edges(isle)
    _skull(isle)
    _lagoon(isle)
    _jungle(isle, -1.0)
    _jungle(isle, 1.0)
    _camp(isle)
    _north_beach(isle)
    galleon(isle, "red", 0.0)
    galleon(isle, "blue", 0.0)
    _meta(isle)
