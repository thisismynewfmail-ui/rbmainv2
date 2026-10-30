"""Port Royale: a colonial harbour town on a grid of cobbled streets, under
the fort on its hill.

Layout (north is -z; the Scarlet Corsairs' ship is moored off the west
waterfront, the Azure Buccaneers' off the east)::

    z -136  ================= the hill: cliffs ==================================
    z -112   the park    | THE FORT (y 8): barracks, treasury, the idol |  the old graves
    z  -60  ============= Governor's Row ======== (the fort's grand stair) ============
    z  -48  MANSION + clock tower | THE RUSTY ANCHOR |  the  | THE GOLDEN GULL | CHURCH + bell tower
    z   -8  ============= Main Street ===========  square  ============================
    z    4     houses              houses          (fountain,     houses          houses
    z   44  ============= South Street ==========   stalls,  ============================
    z   56     WAREHOUSE           fish market      gallows)  shipwright       WAREHOUSE
    z   86  ======================== the quay ==========================================
    z  104  ~~~~~~~~~~~~~~~~~~~~~~~~ the harbour ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
         W waterfront                                                    E waterfront

The town is mirrored east to west -- each crew's half has a big house with
a tower on it, a tavern, houses, a warehouse on its quay -- and the fort,
the square and the harbour are between them.

The twist is the redcoats (``extra["twist"] = "redcoats"``): the fort's
alarm bell rings and the garrison marches out of its ``barracks`` down the
grand stair to patrol the streets (``patrol`` marks, by ``route``, in
order), firing on any pirate they catch carrying the Crown's gold.
"""
from __future__ import annotations

import math
import random
from typing import Tuple

from ..calamity_coast.town import house, lookout_tower, skirt
from ..kit import (ArenaArea, backdrop, building, crenels, flight, gable, rect, room_walls, slab,
                   threshold)
from .common import (IRON, ROCK, ROCK_DARK, SAND_WET, SEA, SEA_TOP, SEABED, SHIP_X, SHORE_X,
                     TIMBER, Isle, galleon)

HALF = (170.0, 120.0)
SKY = {"top": "#3a6aa8", "horizon": "#f4c890", "sun": [0.65, 0.3, 0.35], "clouds": 0.6,
       "tint": "#ffe0b8"}
AMBIENT = "#b0a8b0"
GROUND = "#b8a888"
FOG = 860.0

EARTH = "#b8a888"
COBBLE = "#8a8478"
PAVING = "#c8bca4"
LAWN = "#5a8a44"
STONE = "#c8bca8"
STONE_DARK = "#9a907e"
REDCOAT = "#b8282a"
HILL = 8.0                  # the fort's terrace
QUAY = 104.0                # the harbour's edge
FORT = (-44.0, 44.0, -112.0, -60.0)
BLOCK_X = [(-100.0, -64.0), (-52.0, -16.0), (16.0, 52.0), (64.0, 100.0)]
ROW_A, ROW_B, ROW_C = (-48.0, -8.0), (4.0, 44.0), (56.0, 86.0)
HOUSE_COLOURS = ["#e8c890", "#d88a7a", "#9ac0d8", "#f0ece0", "#a8c890", "#e8b0a0", "#c8a8d8",
                 "#f0d890"]
ROOFS = ["#8a4a3a", "#6a4a3a", "#5a5a6a", "#7a3a2a"]


def _m(r: Tuple[float, float, float, float]) -> Tuple[float, float, float, float]:
    x0, x1, z0, z1 = r
    return (-x1, -x0, z0, z1)


# ================================================================ the land
def _land(isle: Isle) -> None:
    b = isle.b
    hx, hz = HALF
    m = b.margin
    west = (-hx - m, -SHORE_X, -hz - m, hz + m)
    east = (SHORE_X, hx + m, -hz - m, hz + m)
    harbour = (-SHORE_X, SHORE_X, QUAY, hz + m)
    isle.land(EARTH, holes=[west, east, harbour], soil="#7a6a54")
    for area in (west, east, harbour):
        slab(b, area, SEABED, 3.0, SAND_WET)
    # the water, and the open sea beyond the harbour wall
    for x0, x1, z0, z1 in ((-hx, -SHORE_X, -hz, hz), (SHORE_X, hx, -hz, hz),
                           (-SHORE_X, SHORE_X, QUAY, hz)):
        isle.water((x0, x1, z0, z1), SEABED)
    for x0, x1, z0, z1 in ((-hx - m - 300.0, -hx - m, -hz - m - 300.0, hz + m + 300.0),
                           (hx + m, hx + m + 300.0, -hz - m - 300.0, hz + m + 300.0),
                           (-hx - m, hx + m, hz + m, hz + m + 300.0)):
        b.box([(x0 + x1) / 2.0, (SEABED - 6.0 + SEA_TOP) / 2.0, (z0 + z1) / 2.0],
              [x1 - x0, SEA_TOP - SEABED + 6.0, z1 - z0], SEA, material="glass", alpha=0.6,
              collide=False)
    s = isle.s
    # keep the covers off everything that stands on the ground itself
    for x0, x1 in BLOCK_X:
        for z0, z1 in (ROW_A, ROW_B, ROW_C):
            s.reserve((x0, x1, z0, z1))
    s.reserve(FORT)
    s.reserve((-6.0, 6.0, -60.0, -44.0))
    # the streets, the square, the quay, the waterfronts: cobbles and paving
    for r, colour in (((-SHORE_X, -100.0, -60.0, QUAY), COBBLE), ((100.0, SHORE_X, -60.0, QUAY), COBBLE),
                      ((-100.0, 100.0, -60.0, -48.0), COBBLE), ((-100.0, 100.0, -8.0, 4.0), COBBLE),
                      ((-100.0, 100.0, 44.0, 56.0), COBBLE), ((-SHORE_X, SHORE_X, 86.0, QUAY), STONE),
                      ((-64.0, -52.0, -48.0, 86.0), COBBLE), ((52.0, 64.0, -48.0, 86.0), COBBLE),
                      ((-16.0, 16.0, -48.0, 86.0), PAVING)):
        x0, x1, z0, z1 = r
        pieces_before = len(b.parts)
        s.lay(rect(x0, x1, z0, z1), 0.12, colour)
        for part in b.parts[pieces_before:]:
            part["dec"] = "pb_cobbles"
            part["dw"] = 1
    # the park and the old graves up on the hill either side of the fort
    for sgn in (-1.0, 1.0):
        xa, xb = sorted((sgn * 44.0, sgn * SHORE_X))
        s.lay(rect(xa, xb, -112.0, -60.0), 0.06, LAWN)


def _edges(isle: Isle) -> None:
    b = isle.b
    rng = isle.rng
    hx, hz = HALF
    m = b.margin
    rocks = [ROCK, ROCK_DARK, "#9a8f7c", ROCK]
    isle.cliffs("x", -SHORE_X, SHORE_X, -hz - m, -112.0, 30.0, rocks, green="#4a7a3a")
    for sgn in (-1.0, 1.0):
        a0, a1 = sorted((sgn * SHORE_X, sgn * (hx + m)))
        isle.cliffs("x", a0, a1, -hz - m, -hz, 36.0, rocks, base=SEABED, green="#4a7a3a",
                    step=14.5, recess=0.0)
        b.box([sgn * (hx + m / 2.0), (SEABED + 6.0) / 2.0, (m) / 2.0],
              [m, 6.0 - SEABED, 2 * hz + m], STONE_DARK)
    # the harbour wall across the mouth, a lamp on each end of it
    b.box([0.0, (SEABED + 6.0) / 2.0, hz + m / 2.0], [2 * hx, 6.0 - SEABED, m], STONE_DARK)
    for k in range(17):
        x = -hx + (k + 0.5) * 2 * hx / 17.0
        b.box([x, 6.0 + 0.6, hz + m / 2.0], [2 * hx / 17.0 - 1.4, 1.2, m - 2.0], STONE)
    skirt(b, hx, hz, "#8a8474", top=SEABED - 3.05)
    backdrop(b, "hills", 24.0, rng, sides=("z-",), colours=["#4a7a3a", "#5a8a44", "#3f6a32"])


# ============================================================== the fort
def _fort(isle: Isle) -> None:
    b = isle.b
    x0, x1, z0, z1 = FORT
    # the hill under it, faced with stone, and the grand stair up its front
    b.box([0.0, HILL / 2.0, (z0 + z1) / 2.0], [x1 - x0, HILL, z1 - z0], STONE_DARK)
    flight(b, "z", -44.0, -60.0, -6.0, 6.0, 0.0, HILL, STONE, fill=0.0)
    for sgn in (-1.0, 1.0):
        b.box([sgn * 7.0, HILL / 2.0 + 0.5, -52.0], [2.0, HILL + 1.0, 16.0], STONE_DARK)
    slab(b, (x0 + 1.6, x1 - 1.6, z0 + 1.6, z1 - 1.6), HILL + 0.12, 0.12, "#b0a490")
    # its walls round the edge of the terrace, the gate in the front one
    room_walls(b, (x0, x1, z0, z1), 1.6, HILL, HILL + 3.4, STONE,
               doors={"z+": [(-14.0, 14.0, HILL + 3.4)]})
    crenels(b, "x", z1 - 0.8, x0 + 1.6, x1 - 1.6, HILL + 3.4, STONE, gaps=[(-14.0, 14.0)])
    crenels(b, "z", x0 + 0.8, z0 + 1.6, z1 - 1.6, HILL + 3.4, STONE)
    crenels(b, "z", x1 - 0.8, z0 + 1.6, z1 - 1.6, HILL + 3.4, STONE)
    # the gatehouse: a tower each side of the gate, an arch over it
    for sgn in (-1.0, 1.0):
        b.box([sgn * 10.0, HILL + 7.0, z1 - 3.0], [8.0, 14.0, 6.0], STONE)
        b.box([sgn * 10.0, HILL + 14.6, z1 - 3.0], [8.8, 1.2, 6.8], STONE_DARK)
        b.box([sgn * 10.0, HILL + 15.7, z1 - 3.0], [3.0, 1.0, 3.0], STONE, collide=False)
    b.box([0.0, HILL + 9.5, z1 - 3.0], [12.0, 3.0, 6.0], STONE)
    # the barracks and the treasury, facing each other across the yard
    for sgn, name in ((-1.0, "barracks"), (1.0, "treasury")):
        bx0, bx1 = sorted((sgn * 14.0, sgn * 38.0))
        building(b, (bx0, bx1, -104.0, -84.0), HILL + 0.12, 10.0, "#d8ccb4" if sgn < 0 else "#c8bca0",
                 t=1.2, roof_colour="#6a4a3a", roof_t=0.8, floor_colour="#8a7a64",
                 doors={"z+": [((bx0 + bx1) / 2.0 - 3.0, (bx0 + bx1) / 2.0 + 3.0, HILL + 8.6)]},
                 windows={"z+": [(bx0 + 2.4, bx0 + 6.0, HILL + 3.6, HILL + 7.0),
                                 (bx1 - 6.0, bx1 - 2.4, HILL + 3.6, HILL + 7.0)]},
                 glass=True, lights="#ffd8a0")
        gable(b, (bx0, bx1, -104.0, -84.0), HILL + 0.12 + 10.8, "#6a4a3a", "x", tiers=3,
              rise=1.2, overhang=0.6)
        threshold(b, (bx0, bx1, -104.0, -84.0), "z+",
                  ((bx0 + bx1) / 2.0 - 3.0, (bx0 + bx1) / 2.0 + 3.0), t=1.2, y0=HILL + 0.12)
    # in the barracks: bunks, a rack of muskets; in the treasury: gold
    for k in range(3):
        x = -34.0 + k * 7.0
        b.box([x, HILL + 0.52 + 0.6, -99.0], [5.0, 1.2, 3.0], TIMBER)
        b.box([x, HILL + 0.52 + 2.6, -99.0], [5.0, 0.4, 3.0], TIMBER)
    for k in range(3):
        x = 18.0 + k * 7.0
        b.box([x, HILL + 0.52 + 0.8, -100.0], [4.0, 1.6, 2.4], "#7a4a28")
        b.box([x, HILL + 0.52 + 1.8, -100.0], [3.6, 0.4, 2.0], "#e8b830", material="metal")
    # the yard: the flag, cannons along the front wall, powder kegs
    b.cyl([0.0, HILL + 9.0, -96.0], [0.6, 18.0, 0.6], "#e8e8e8")
    # the governor's colours: navy, a gold sun in the middle, a gold border
    b.box([2.4, HILL + 16.0, -96.0], [4.2, 2.8, 0.12], "#1a2a5a", collide=False)
    b.cyl([2.4, HILL + 16.0, -95.9], [1.4, 0.1, 1.4], "#e8c840", collide=False,
          r=[math.pi / 2.0, 0.0, 0.0])
    b.box([2.4, HILL + 17.3, -95.92], [4.2, 0.2, 0.04], "#e8c840", collide=False)
    b.box([2.4, HILL + 14.7, -95.92], [4.2, 0.2, 0.04], "#e8c840", collide=False)
    for x in (-30.0, -20.0, 20.0, 30.0):
        b.box([x, HILL + 0.82, z1 - 4.4], [2.4, 1.4, 3.0], "#4a3a2a")
        b.cyl([x, HILL + 1.6 + 0.6, z1 - 2.2], [1.0, 4.4, 1.0], IRON, material="metal",
              collide=False, r=[math.pi / 2.0 - 0.1, 0.0, 0.0])
    for x, z in ((-36.0, -74.0), (-33.0, -74.0), (36.0, -74.0)):
        isle.barrel(x, z, HILL + 0.12, "#4a3a2a")
    isle.idol(0.0, HILL + 0.12, -76.0, STONE)
    # the marks: the barracks door the garrison comes out of, the treasury's
    # gold, an X in the yard
    for k in range(6):
        b.mark("barracks", -26.0 + (k % 3) * 2.4, HILL + 0.24, -80.0 + (k // 3) * 2.4)
    for x in (18.0, 25.0, 32.0):
        isle.loot(x, HILL + 0.52, -96.0, "bar", "the treasury")
    isle.dig(26.0, HILL + 0.24, -70.0, "the fort's yard")
    isle.loot(-40.0, HILL + 0.24, -64.0, "gem", "the fort's walls")
    b.landmark(0.0, -86.0, "the fort")


# ================================================== the mansion, the church
def _tower_pair(isle: Isle) -> None:
    b = isle.b
    for sgn in (-1.0, 1.0):
        def X(x: float, sgn: float = sgn) -> float:
            return sgn * x
        west = sgn < 0
        # the big house: the governor's mansion (west), the church (east)
        x0, x1 = sorted((X(100.0), X(78.0)))
        area = (x0, x1, -46.0, -26.0)
        door_x = (x0 + x1) / 2.0
        building(b, area, 0.0, 16.0, "#f0e8d8" if west else "#e8e0d0", t=1.6,
                 roof_colour="#5a5a6a" if west else "#6a5a4a", roof_t=1.0, floor_colour="#8a6a4a",
                 doors={"z+": [(door_x - 3.0, door_x + 3.0, 9.0)]},
                 windows={"z+": [(x0 + 2.0, x0 + 5.2, 3.4, 8.0), (x1 - 5.2, x1 - 2.0, 3.4, 8.0),
                                 (x0 + 5.4, x0 + 7.8, 10.4, 14.0), (x1 - 7.8, x1 - 5.4, 10.4, 14.0)],
                          "x-" if west else "x+": [(-42.0, -38.0, 3.4, 8.0), (-34.0, -30.0, 3.4, 8.0)]},
                 glass=True, lights="#ffe0b0")
        gable(b, area, 17.0, "#5a5a6a" if west else "#6a5a4a", "x", tiers=4, rise=1.4,
              overhang=0.8)
        threshold(b, area, "z+", (door_x - 3.0, door_x + 3.0), t=1.6)
        # columns either side of its door
        for dx in (-4.2, 4.2):
            b.cyl([door_x + dx, 5.0, -25.0], [1.2, 10.0, 1.2], "#f4f0e8")
        b.box([door_x, 10.4, -24.6], [11.0, 0.8, 2.4], "#f4f0e8")
        # its tower beside it: a clock tower, a bell tower
        top = lookout_tower(b, X(71.0), -40.0, 0.0, 22.0, "#e8e0d0" if west else "#d8d0c0",
                            STONE_DARK, core=6.0, width=3.4, cap=STONE, start="x+" if west else "x-")
        if west:
            b.cyl([X(71.0), 17.0, -36.9], [3.6, 0.3, 3.6], "#f4f0e8", collide=False,
                  r=[math.pi / 2.0, 0.0, 0.0])
            b.box([X(71.0), 17.6, -36.7], [0.2, 1.4, 0.1], "#1a1a1a", collide=False)
            b.box([X(71.0) + 0.5, 17.0, -36.7], [1.1, 0.2, 0.1], "#1a1a1a", collide=False)
        isle.loot(X(71.0), top, -40.0 + 4.6, "gem" if not west else "bar",
                  "the bell tower" if not west else "the clock tower")
        # the garden in front: hedges, a statue (mansion); graves (church)
        if west:
            for gx in (-98.0, -80.0):
                b.box([gx, 1.2, -18.0], [6.0, 2.4, 8.0], "#3a6a32")
            b.box([-89.0, 1.0, -16.0], [2.4, 2.0, 2.4], STONE)
            b.box([-89.0, 3.6, -16.0], [1.4, 3.2, 1.0], "#e8e4dc")
            isle.dig(-72.0, None, -16.0, "the governor's roses")
            isle.loot(-89.0, 0.4, -36.0, "gem", "the governor's mansion")
        else:
            for k in range(6):
                gx, gz = 70.0 + (k % 3) * 8.0, -20.0 + (k // 3) * 8.0
                b.box([gx, 0.1, gz + 1.6], [2.0, 0.2, 3.4], "#6a6a5a", collide=False)
                b.box([gx, 1.2, gz - 0.4], [1.6, 2.4, 0.5], STONE)
            isle.dig(98.0, None, -14.0, "the churchyard")
            isle.loot(89.0, 0.4, -36.0, "gem", "the church plate")
            # the pews and the altar inside
            for k in range(3):
                b.box([86.0, 0.4 + 0.5, -40.0 + k * 4.0], [10.0, 1.0, 1.0], TIMBER)
            b.box([96.0, 0.4 + 1.0, -36.0], [2.0, 2.0, 6.0], "#e8e0d0")


# ========================================================== taverns, houses
def _town(isle: Isle) -> None:
    b = isle.b
    rng = isle.rng
    colours = list(HOUSE_COLOURS)
    k = 0
    for sgn in (-1.0, 1.0):
        def X(x: float, sgn: float = sgn) -> float:
            return sgn * x
        west = sgn < 0
        # the tavern (west) and the inn (east) in row A's inner block
        x0, x1 = sorted((X(50.0), X(20.0)))
        area = (x0, x1, -44.0, -22.0)
        mid = (x0 + x1) / 2.0
        building(b, area, 0.0, 11.0, "#a87a52" if west else "#c8a878", t=1.4,
                 roof_colour="#5a3a2a", roof_t=0.8, floor_colour="#6a4a32",
                 doors={"z+": [(mid - 3.0, mid + 3.0, 8.6)]},
                 windows={"z+": [(x0 + 2.4, x0 + 7.0, 3.0, 7.0), (x1 - 7.0, x1 - 2.4, 3.0, 7.0)]},
                 glass=True, lights="#ffc880")
        gable(b, area, 11.8, "#5a3a2a", "x", tiers=3, rise=1.3, overhang=0.8)
        threshold(b, area, "z+", (mid - 3.0, mid + 3.0), t=1.4)
        sign = "THE RUSTY ANCHOR" if west else "THE GOLDEN GULL"
        b.box([mid, 10.0, -21.4], [12.0, 2.0, 0.4], "#2a1a10",
              decal="t~%s~#2a1a10~#e8c860~6.00" % sign)
        # inside: the bar, tables, barrels
        b.box([mid, 0.4 + 1.6, -40.6], [14.0, 3.2, 2.0], "#5a3a22")
        for tx in (-6.0, 6.0):
            b.cyl([mid + tx, 0.4 + 1.2, -31.0], [3.4, 2.4, 3.4], TIMBER)
        for bx in (x0 + 3.0, x1 - 3.0):
            isle.barrel(bx, -41.0, 0.4)
        isle.loot(mid, 0.4, -34.0, "any", "the Rusty Anchor" if west else "the Golden Gull")
        # its yard behind: barrels, an X
        isle.dig(X(34.0), None, -14.0, "behind the tavern" if west else "behind the inn")
        for bx in (X(46.0), X(43.0)):
            isle.barrel(bx, -12.0)
        # houses in row B: two facing Main Street, two facing South Street
        for bxa, bxb in ((100.0, 64.0), (52.0, 16.0)):
            xa, xb = sorted((X(bxa), X(bxb)))
            w = xb - xa
            for (za, zb, door) in ((6.0, 22.0, "z-"), (26.0, 42.0, "z+")):
                for (ua, ub) in ((xa + 1.0, xa + w / 2.0 - 1.0), (xa + w / 2.0 + 1.0, xb - 1.0)):
                    colour = colours[k % len(colours)]
                    roof = ROOFS[k % len(ROOFS)]
                    house(b, (ua, ub, za, zb), 0.0, colour, roof, door, height=11.0,
                          rng=rng, furnish=True)
                    k += 1
        # row C: the warehouse on the quay, and the fish market / shipwright
        xa, xb = sorted((X(98.0), X(66.0)))
        area = (xa, xb, 58.0, 84.0)
        mid = (xa + xb) / 2.0
        building(b, area, 0.0, 13.0, "#8a6a4a" if west else "#7a6a5a", t=1.2,
                 roof_colour="#4a4a52", roof_t=0.8, floor_colour="#6a5a48",
                 doors={"z+": [(mid - 5.0, mid + 5.0, 10.0)], "z-": [(mid - 3.0, mid + 3.0, 8.0)]},
                 lights="#ffe0a8")
        gable(b, area, 13.8, "#4a4a52", "x", tiers=3, rise=1.3, overhang=0.6)
        threshold(b, area, "z+", (mid - 5.0, mid + 5.0), t=1.2)
        threshold(b, area, "z-", (mid - 3.0, mid + 3.0), t=1.2)
        isle.crates(xa + 3.0, 61.0, 0.4, n=4)
        isle.crates(xb - 7.0, 76.0, 0.4, n=3)
        isle.barrel(mid - 6.0, 80.0, 0.4)
        isle.barrel(mid + 6.0, 62.0, 0.4)
        isle.loot(mid, 0.4, 70.0, "bar", "the west warehouse" if west else "the east warehouse")
        isle.loot(xa + 4.0 if west else xb - 4.0, 0.4, 78.0, "any", "the warehouse")
        # the fish market (west) / the shipwright's yard (east): an open shed
        xa, xb = sorted((X(50.0), X(20.0)))
        for px in (xa + 1.0, xb - 1.0):
            for pz in (60.0, 82.0):
                b.cyl([px, 4.5, pz], [1.0, 9.0, 1.0], TIMBER)
        slab(b, (xa, xb, 58.0, 84.0), 9.6, 0.6, "#6a4a3a")
        gable(b, (xa, xb, 58.0, 84.0), 9.6, "#6a4a3a", "x", tiers=2, rise=1.0, overhang=0.4)
        if west:
            for k2 in range(3):
                b.box([xa + 6.0 + k2 * 9.0, 1.2, 70.0], [6.0, 2.4, 3.0], "#8a6a48")
                b.box([xa + 6.0 + k2 * 9.0, 2.5, 70.0], [5.4, 0.2, 2.4], "#a8c8d8", collide=False)
            isle.loot(xa + 15.0, None, 64.0, "any", "the fish market")
        else:
            b.box([(xa + xb) / 2.0, 1.4, 71.0], [5.0, 2.8, 16.0], "#8a5a34")
            b.box([(xa + xb) / 2.0, 3.0, 71.0], [3.6, 0.4, 14.0], "#5a3a22", collide=False)
            for dz in (-6.0, 0.0, 6.0):
                b.box([(xa + xb) / 2.0, 0.6, 71.0 + dz], [7.0, 1.2, 1.0], TIMBER)
            isle.loot((xa + xb) / 2.0 + 6.0, None, 64.0, "any", "the shipwright's yard")


# ================================================== the square and the quay
def _square(isle: Isle) -> None:
    b = isle.b
    rng = isle.rng
    y = 0.12
    # the fountain
    b.cyl([0.0, y + 0.8, -24.0], [12.0, 1.6, 12.0], STONE)
    b.cyl([0.0, y + 1.5, -24.0], [10.6, 0.1, 10.6], "#4a9ac8", material="glass", alpha=0.7,
          collide=False)
    b.cyl([0.0, y + 3.2, -24.0], [2.0, 3.2, 2.0], STONE)
    b.cyl([0.0, y + 5.0, -24.0], [5.0, 0.6, 5.0], STONE)
    b.sphere([0.0, y + 6.0, -24.0], [1.4, 1.4, 1.4], "#9ad8f0", material="glass", alpha=0.7,
             collide=False)
    # market stalls: a counter under a striped awning on four posts
    for sx, sz, colour in ((-10.0, -8.0, "#c8302a"), (10.0, -8.0, "#2a6ab8"),
                           (-10.0, 14.0, "#e8b830"), (10.0, 14.0, "#3a8a4a")):
        b.box([sx, y + 1.1, sz], [6.0, 2.2, 2.4], "#8a6a48")
        for dx in (-2.8, 2.8):
            for dz in (-1.4, 2.2):
                b.cyl([sx + dx, y + 3.6, sz + dz], [0.4, 7.2, 0.4], TIMBER)
        b.box([sx, y + 7.4, sz + 0.4], [6.6, 0.3, 4.6], colour)
        b.box([sx, y + 2.4, sz], [5.4, 0.4, 2.0], rng.choice(["#e8c860", "#c86a3a", "#8ac85a"]),
              collide=False)
        isle.loot(sx, y, sz + 3.4, "any", "the market")
    # the gallows: a platform, steps up, a beam with a noose
    b.box([0.0, y + 2.0, 32.0], [8.0, 4.0, 6.0], TIMBER)
    flight(b, "z", 40.0, 35.0, -1.6, 1.6, y, y + 4.0, TIMBER, fill=y)
    for dx in (-3.0, 3.0):
        b.cyl([dx, y + 4.0 + 4.0, 31.0], [0.6, 8.0, 0.6], TIMBER)
    b.box([0.0, y + 4.0 + 8.2, 31.0], [7.0, 0.6, 0.6], TIMBER)
    b.box([0.0, y + 4.0 + 6.8, 31.0], [0.12, 2.2, 0.12], "#c8a878", collide=False)
    isle.loot(0.0, y + 4.0, 33.0, "any", "the gallows")
    # a statue nearer the harbour, lamps along the square
    b.box([0.0, y + 1.2, 62.0], [4.0, 2.4, 4.0], STONE)
    b.box([0.0, y + 5.0, 62.0], [1.8, 5.2, 1.4], "#7a8a7a")
    b.sphere([0.0, y + 8.4, 62.0], [1.6, 1.6, 1.6], "#7a8a7a", collide=False)
    for lz in (-40.0, -4.0, 22.0, 48.0, 76.0):
        for lx in (-14.6, 14.6):
            b.cyl([lx, y + 4.0, lz], [0.5, 8.0, 0.5], IRON, material="metal")
            b.box([lx, y + 8.4, lz], [1.2, 0.8, 1.2], "#ffd890", material="neon")
    isle.dig(-10.0, y, 72.0, "under the statue's gaze")
    b.landmark(0.0, 0.0, "the square")
    b.landmark(0.0, 32.0, "the gallows")


def _quay(isle: Isle) -> None:
    b = isle.b
    y = 0.12
    for x in range(-104, 108, 16):
        b.cyl([float(x), y + 0.9, QUAY - 1.4], [1.2, 1.8, 1.2], IRON, material="metal")
    for sgn in (-1.0, 1.0):
        def X(x: float, sgn: float = sgn) -> float:
            return sgn * x
        # a crane at each end of the quay, cargo under it
        cx = X(36.0)
        b.box([cx, y + 1.0, 96.0], [4.0, 2.0, 4.0], STONE_DARK)
        b.cyl([cx, y + 2.0 + 6.0, 96.0], [1.4, 12.0, 1.4], TIMBER)
        b.box([cx, y + 2.0 + 12.4, 99.0], [1.0, 1.0, 8.0], TIMBER, collide=False)
        b.box([cx, y + 2.0 + 9.0, 102.6], [0.2, 6.0, 0.2], "#c8a878", collide=False)
        isle.crates(X(44.0) - (3.8 if sgn > 0 else 0.0), 92.0, y, n=4)
        isle.barrel(X(26.0), 94.0, y)
        isle.loot(X(30.0), y, 90.0, "bar", "the quay")
        isle.dig(X(84.0), y, 94.0, "the west quay" if sgn < 0 else "the east quay")
        # rowboats on the water, tied up below the quay
        b.box([X(20.0), SEABED + 0.8 + 1.0, 110.0], [3.0, 1.8, 8.0], "#8a5a34")
        b.box([X(20.0), SEABED + 0.8 + 1.95, 110.0], [2.2, 0.1, 7.0], "#3a2a1a", collide=False)
        b.box([X(20.0), SEABED + 0.4, 110.0], [3.0, 0.8, 8.0], "#5a3a22")
        # lamps and crates along the waterfront
        for z in (-40.0, 30.0, 70.0):
            b.cyl([X(106.0), y + 4.0, z], [0.5, 8.0, 0.5], IRON, material="metal")
            b.box([X(106.0), y + 8.4, z], [1.2, 0.8, 1.2], "#ffd890", material="neon")
        isle.crates(X(104.0) - (3.8 if sgn > 0 else 0.0), -50.0, y, n=3)
        isle.loot(X(106.0), y, -30.0, "any", "the waterfront")
    b.landmark(0.0, 95.0, "the quay")


def _hill(isle: Isle) -> None:
    """Either side of the fort: the governor's park (west) and the old
    graves (east), up against the cliff."""
    b = isle.b
    for sgn in (-1.0, 1.0):
        def X(x: float, sgn: float = sgn) -> float:
            return sgn * x
        y = isle.top(X(80.0), -90.0)
        for x, z in ((54.0, -104.0), (68.0, -70.0), (96.0, -100.0), (102.0, -72.0), (82.0, -84.0)):
            b.cyl([X(x), y + 4.0, z], [1.4, 8.0, 1.4], "#6a4a32")
            b.sphere([X(x), y + 10.0, z], [8.0, 7.0, 8.0], "#3f7a3a")
        if sgn < 0:
            # a gazebo in the park
            for dx in (-4.0, 4.0):
                for dz in (-4.0, 4.0):
                    b.cyl([X(70.0) + dx, y + 3.5, -90.0 + dz], [0.6, 7.0, 0.6], "#f0ece0")
            b.box([X(70.0), y + 7.3, -90.0], [10.0, 0.6, 10.0], "#f0ece0")
            b.cone([X(70.0), y + 9.0, -90.0], [11.0, 2.8, 11.0], "#5a7a8a")
            isle.dig(X(84.0), y, -96.0, "the governor's park")
        else:
            for k in range(6):
                gx, gz = X(60.0 + (k % 3) * 9.0), -98.0 + (k // 3) * 9.0
                b.box([gx, y + 0.1, gz + 1.6], [2.0, 0.2, 3.4], "#5a6a4a", collide=False)
                b.box([gx, y + 1.4, gz - 0.4], [0.4, 2.8, 0.4], STONE)
                b.box([gx, y + 2.2, gz - 0.4], [1.8, 0.4, 0.4], STONE)
            isle.dig(X(90.0), y, -84.0, "the old graves")
        isle.loot(X(104.0), y, -104.0, "any", "the hill")


# ================================================================ meta
def _patrols(isle: Isle) -> None:
    """The redcoats' beats: three loops out of the fort's gate and back."""
    b = isle.b
    s = 0.12
    routes = [
        [(0.0, HILL + 0.24, -70.0), (0.0, HILL, -61.0), (0.0, s, -42.0), (-40.0, s, -54.0),
         (-58.0, s, -54.0), (-58.0, s, -2.0), (-10.0, s, -2.0), (-10.0, s, -40.0),
         (0.0, s, -42.0)],
        [(0.0, HILL + 0.24, -70.0), (0.0, HILL, -61.0), (0.0, s, -42.0), (40.0, s, -54.0),
         (58.0, s, -54.0), (58.0, s, -2.0), (10.0, s, -2.0), (10.0, s, -40.0),
         (0.0, s, -42.0)],
        [(0.0, HILL + 0.24, -70.0), (0.0, HILL, -61.0), (0.0, s, -42.0), (-6.0, s, 50.0),
         (-58.0, s, 50.0), (-58.0, s, 92.0), (58.0, s, 92.0), (58.0, s, 50.0), (6.0, s, 50.0),
         (0.0, s, -42.0)],
    ]
    for r, points in enumerate(routes):
        for i, (x, y, z) in enumerate(points):
            b.mark("patrol", x, y, z, route=r, i=i)


def _meta(isle: Isle) -> None:
    b = isle.b
    for x, z, name in ((-89.0, -36.0, "the governor's mansion"), (89.0, -36.0, "the church"),
                       (-35.0, -33.0, "the Rusty Anchor"), (35.0, -33.0, "the Golden Gull"),
                       (-82.0, 71.0, "the west warehouse"), (82.0, 71.0, "the east warehouse"),
                       (-SHIP_X, 0.0, "the Scarlet Queen"), (SHIP_X, 0.0, "the Blue Marlin")):
        b.landmark(x, z, name)
    b.camera(0.0, 50.0, 112.0, 0.0, 4.0, 0.0)
    b.camera(-140.0, 40.0, 90.0, -40.0, 0.0, 0.0)
    b.camera(140.0, 40.0, -90.0, 40.0, 0.0, -20.0)
    b.camera(0.0, 26.0, -20.0, 0.0, 10.0, -76.0)
    b.extra.update({"twist": "redcoats", "water": SEA_TOP, "redcoats_every": [55.0, 75.0],
                    "redcoats_for": 34.0, "warn": 6.0})


def build(b: ArenaArea) -> None:
    rng = random.Random(8283)
    isle = Isle(b, rng)
    _land(isle)
    _edges(isle)
    _fort(isle)
    _tower_pair(isle)
    _town(isle)
    _square(isle)
    _quay(isle)
    _hill(isle)
    _patrols(isle)
    galleon(isle, "red", 0.0)
    galleon(isle, "blue", 0.0)
    _meta(isle)
