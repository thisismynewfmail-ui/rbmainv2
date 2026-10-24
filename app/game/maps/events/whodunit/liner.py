"""The SS Aurora -- an ocean liner on the North Atlantic, at night, among
the ice.

The ship lies along x, the bow at +x::

    x -120 .. -104 | -104 ............................................ 86 | 86 .. 123
      the stern      the hull: four decks                                   the bow
                     (the boat deck)          funnels, lifeboats, the BRIDGE
      aft deck       GYM | LIBRARY | SMOKING | STAIR HALL | the PALM COURT    fore deck
                     (the promenade deck: the deckhouse, the promenade round it)
                     AFT HALL | HOSPITAL | the STATEROOMS | STAIR HALL | DINING SALOON | GALLEY
                     (the saloon deck)
                     ENGINE ROOM | BOILER ROOM | CREW | the BATHS | the CARGO HOLD
                     (the lower deck)

Stairs: the grand staircase joins the saloon deck to the promenade deck;
the crew's stairs aft (the engine room, the aft hall, the aft deck) and
forward (the hold, the galley, the fore deck) join everything; outside
stairs climb from the aft deck and the fore deck to the boat deck.

Over the rail is over the side: the rules take anybody who ends up in the
sea (``fall_y``).  The twist is the fog: now and then the ship sails into a
bank of it and nobody can see past arm's length.
"""
from __future__ import annotations

import math
import random
from typing import List, Sequence, Tuple

from ..kit import ArenaArea, carve, flight, lantern, letters, plate, rect, slab, step_paint, strip_light
from ..prop_panic import furniture as fx
from ..prop_panic.catalogue import (B, BLACK, BRASS, C, CREAM, GOLD, K, R, S, WHITE, WOOD, WOOD_DARK,
                                    place, stamp)
from ..prop_panic.furniture import COUNTER_TOP, TABLE_TOP
from ..prop_panic.rooms import DECAL_TILE, covering, grow, interior, tiled
from .common import Walls, candelabra, chandelier, hang, room, stair

HALF = (150.0, 60.0)
SKY = {"top": "#060a18", "horizon": "#1a2a40", "sun": [-0.4, 0.5, -0.3],
       "clouds": 0.25, "tint": "#c8d8f0"}
AMBIENT = "#4a5878"
GROUND = "#0a1a2a"
FOG = 520.0

HULL = "#1a1a1e"
WHITE_PAINT = "#f2f0ea"
TEAK = "#a8784a"
STEEL = "#5a5e66"
IRON = "#2a2a2e"
PANEL = "#4a2a1a"
CEILING = "#f2ead8"
BUFF = "#d8a040"

SEA = 2.0
L0, L1, L2, L3, L4 = 4.0, 14.0, 24.0, 34.0, 44.0     # the decks' floors
C0, C1, C2, C3 = 13.4, 23.4, 33.4, 43.4              # and their ceilings
BOTTOM = -6.0
HX0, HX1 = -104.0, 86.0
W, T, P = 22.0, 1.2, 0.6
IW = W - T
IX0, IX1 = HX0 + T, HX1 - T
DX0, DX1, DZ = -76.0, 56.0, 14.0                     # the deckhouse
BX0, BX1, BZ = 28.0, 56.0, 10.0                      # the bridge house
STERN = [(-108.0, -104.0, 22.0), (-112.0, -108.0, 19.0), (-115.0, -112.0, 15.0),
         (-118.0, -115.0, 10.0), (-120.0, -118.0, 5.0)]
BOW = [(86.0, 94.0, 22.0), (94.0, 101.0, 19.0), (101.0, 108.0, 15.5), (108.0, 114.0, 12.0),
       (114.0, 119.0, 8.0), (119.0, 123.0, 4.5)]

AFT0 = rect(-100.0, -95.0, -16.0, -2.0)    # lower deck to the saloon deck (up toward +z)
FORE0 = rect(78.0, 83.0, -16.0, -2.0)
AFT1 = rect(-92.0, -87.0, 2.0, 16.0)       # saloon deck to the open deck (up toward +z)
FORE1 = rect(78.0, 83.0, 2.0, 16.0)
GRAND = rect(-8.0, 8.0, -5.0, 5.0)         # the grand staircase (up toward -x)
AFT2 = rect(-92.0, -76.0, -6.0, 2.0)       # the open deck to the boat deck (up toward +x)
FORE2 = rect(56.0, 72.0, 10.0, 14.0)       # (up toward -x)
CABINS = (-66.0, -48.67, -31.33, -14.0)
CZ = 2.8                                   # the stateroom corridor's walls
DOOR = 9.0


# ================================================================ the walls
def _ports(x0: float, x1: float, avoid: Sequence[float], y: float) -> List[tuple]:
    out = []
    x = x0 + 3.0
    while x + 2.0 < x1 - 2.0:
        if all(abs(x + 1.0 - a) > 2.6 for a in avoid):
            out.append((x, x + 2.0, y, y + 2.0, "win"))
        x += 5.0
    return out


def _walls() -> Walls:
    w = Walls(PANEL, BRASS)
    lower = (-70.0, -40.0, -10.0, 30.0, -97.5, 80.5)
    saloon = (-86.0, -66.0, -48.67, -31.33, -14.0, 14.0, 62.0, -89.5, 78.5)
    for side, z, out in (("s", -(W - T / 2.0), -1), ("n", W - T / 2.0, 1)):
        w.add("x", z, HX0, HX1, BOTTOM, L1, HULL, _ports(HX0, HX1, lower, 8.0), t=T, out=out)
        w.add("x", z, HX0, HX1, L1, L2, WHITE_PAINT, _ports(HX0, HX1, saloon, 17.6), t=T, out=out)
    for x in (HX0 + T / 2.0, HX1 - T / 2.0):
        w.add("z", x, -IW, IW, BOTTOM, L2, HULL, t=T)
    # ---- the lower deck's bulkheads
    for x in (-70.0, -40.0, -10.0, 30.0):
        w.add("z", x, -IW, IW, L0, C0, "#8a8e96", [(-2.2, 2.2, L0, L0 + DOOR, "door")])
    # ---- the saloon deck
    d1 = lambda a, c: (a, c, L1, L1 + DOOR, "door")         # noqa: E731
    for x in (-86.0, -66.0, -14.0):
        w.add("z", x, -IW, IW, L1, C1, "#d8ccb4", [d1(-2.2, 2.2)])
    w.add("z", 14.0, -IW, IW, L1, C1, "#d8ccb4", [d1(-6.0, 6.0)])
    w.add("z", 62.0, -IW, IW, L1, C1, "#d8ccb4", [d1(-12.4, -8.0), d1(8.0, 12.4)])
    mids = [(CABINS[k] + CABINS[k + 1]) / 2.0 for k in range(3)]
    for z in (-CZ, CZ):
        w.add("x", z, CABINS[0] + P / 2.0, CABINS[-1] - P / 2.0, L1, C1, "#d8ccb4",
              [d1(m - 2.2, m + 2.2) for m in mids])
    for x in CABINS[1:3]:
        w.add("z", x, CZ + P / 2.0, IW, L1, C1, "#d8ccb4")
        w.add("z", x, -IW, -CZ - P / 2.0, L1, C1, "#d8ccb4")
    # ---- the deckhouse
    d2 = lambda a, c: (a, c, L2, L2 + DOOR, "door")         # noqa: E731
    win = lambda a, c: (a, c, 26.4, 31.4, "win")            # noqa: E731
    sides = [win(-73.0, -68.0), win(-64.0, -59.0),
             win(-35.0, -30.0), win(-21.0, -16.0), d2(-13.0, -8.6), d2(8.4, 12.8),
             win(17.0, 23.0), d2(26.0, 30.4), win(34.0, 40.0), d2(43.0, 47.4), win(50.0, 54.0)]
    for z, out in ((-(DZ - P / 2.0), -1), (DZ - P / 2.0, 1)):
        holes = list(sides) + ([d2(-28.4, -24.0)] if out > 0 else [])
        w.add("x", z, DX0, DX1, L2, C2, WHITE_PAINT, holes, out=out)
    w.add("z", DX0 + P / 2.0, -DZ + P, DZ - P, L2, C2, WHITE_PAINT,
          [d2(6.0, 10.4), win(-11.0, -5.0)], out=-1)
    w.add("z", DX1 - P / 2.0, -DZ + P, DZ - P, L2, C2, WHITE_PAINT,
          [d2(-2.2, 2.2), win(-11.0, -5.0), win(3.6, 8.6)], out=1)
    w.add("z", -56.0, -DZ + P, DZ - P, L2, C2, "#d8ccb4", [d2(-2.2, 2.2)])
    w.add("z", -38.0, -DZ + P, DZ - P, L2, C2, "#d8ccb4", [d2(-2.2, 2.2)])
    w.add("z", -14.0, -DZ + P, DZ - P, L2, C2, "#d8ccb4", [d2(6.0, 10.4)])
    w.add("z", 14.0, -DZ + P, DZ - P, L2, C2, "#d8ccb4", [d2(-6.0, 6.0)])
    # ---- the bridge house on the boat deck
    d3 = lambda a, c: (a, c, L3, L3 + DOOR, "door")         # noqa: E731
    bw = lambda a, c: (a, c, 36.4, 41.4, "win")             # noqa: E731
    for z, out in ((-(BZ - P / 2.0), -1), (BZ - P / 2.0, 1)):
        w.add("x", z, BX0, BX1, L3, C3, WHITE_PAINT, [bw(31.0, 36.0), d3(43.0, 47.4), bw(50.0, 54.0)],
              out=out)
    w.add("z", BX0 + P / 2.0, -BZ + P, BZ - P, L3, C3, WHITE_PAINT, [d3(-2.2, 2.2)], out=-1)
    w.add("z", BX1 - P / 2.0, -BZ + P, BZ - P, L3, C3, WHITE_PAINT,
          [bw(-8.4, -3.4), bw(-2.2, 2.2), bw(3.4, 8.4)], out=1)
    w.add("z", 40.0, -BZ + P, BZ - P, L3, C3, "#d8ccb4", [d3(-2.2, 2.2)])
    return w


def _cabin_rooms() -> List[tuple]:
    out = []
    names = (("A1", "A2"), ("A3", "A4"), ("A5", "A6"))
    for k in range(3):
        x0 = CABINS[k] + P / 2.0
        x1 = CABINS[k + 1] - P / 2.0
        north, south = names[k]
        out.append(("c" + north, "stateroom " + north, rect(x0, x1, CZ + P / 2.0, IW), L1, C1,
                    ("#c8d8e8", "#e8d8c0", "#d8e8d0")[k], ("#3a4a6a", "#6a3a3a", "#3a5a3a")[k], ""))
        out.append(("c" + south, "stateroom " + south, rect(x0, x1, -IW, -CZ - P / 2.0), L1, C1,
                    ("#e8d0d8", "#d8d8c0", "#d0d8e8")[k], ("#6a3a5a", "#5a5a3a", "#3a3a6a")[k], ""))
    return out


ROOMS = [
    # key, name, inner, y0, y1, walls, floor, decal
    ("engine", "the engine room", rect(IX0, -70.3, -IW, IW), L0, C0, "#8a8e96", "", ""),
    ("boiler", "the boiler room", rect(-69.7, -40.3, -IW, IW), L0, C0, "#6a5a4a", "#3a3a3a", "tiles"),
    ("crew", "the crew's quarters", rect(-39.7, -10.3, -IW, IW), L0, C0, "#a8b0a0", "#5a5a4a", "planks"),
    ("baths", "the swimming bath", rect(-9.7, 29.7, -IW, IW), L0, C0, "#d8eef0", "", ""),
    ("hold", "the cargo hold", rect(30.3, IX1, -IW, IW), L0, C0, "#6a6458", "", ""),
    ("afthall", "the aft hall", rect(IX0, -86.3, -IW, IW), L1, C1, "#c8c8b8", "", ""),
    ("hospital", "the ship's hospital", rect(-85.7, -66.3, -IW, IW), L1, C1, "#e8f0f0", "#c8d0d0",
     "tiles"),
    ("corridor", "the stateroom corridor", rect(-65.7, -14.3, -CZ + P / 2.0, CZ - P / 2.0), L1, C1,
     "#e8dcc0", "#7a1a2a", ""),
    ("hall", "the grand staircase", rect(-13.7, 13.7, -IW, IW), L1, C1, "#e8dcc0", "", ""),
    ("dining", "the dining saloon", rect(14.3, 61.7, -IW, IW), L1, C1, "#f2ead8", "#7a5a3a", "planks"),
    ("galley", "the galley", rect(62.3, IX1, -IW, IW), L1, C1, "#e8e8e0", "", ""),
    ("gym", "the gymnasium", rect(DX0 + P, -56.3, -DZ + P, DZ - P), L2, C2, "#d8e0c8", "#8a6a4a",
     "planks"),
    ("library", "the library", rect(-55.7, -38.3, -DZ + P, DZ - P), L2, C2, "#3a4a3a", "#5a3a24",
     "planks"),
    ("smoking", "the smoking room", rect(-37.7, -14.3, -DZ + P, DZ - P), L2, C2, "#4a2a1a", "#3a2418",
     "planks"),
    ("tophall", "the top of the grand staircase", rect(-13.7, 13.7, -DZ + P, DZ - P), L2, C2,
     "#e8dcc0", "", ""),
    ("palm", "the palm court", rect(14.3, DX1 - P, -DZ + P, DZ - P), L2, C2, "#e8f0e0", "#d8e0c8",
     "tiles"),
    ("radio", "the wireless room", rect(BX0 + P, 39.7, -BZ + P, BZ - P), L3, C3, "#d8d8c8", "#5a5a4a",
     ""),
    ("wheel", "the bridge", rect(40.3, BX1 - P, -BZ + P, BZ - P), L3, C3, "#e8e0c8", "#8a6a4a",
     "planks"),
] + _cabin_rooms()


def _shell(b: ArenaArea, w: Walls) -> None:
    w.build(b)
    # the decks: the lower deck, the saloon deck, the open deck (round the
    # wells of the stairs), the deckhouse's roof, the bridge house's roof
    slab(b, rect(IX0, IX1, -IW, IW), L0, L0 - BOTTOM, "#3a3a3e")
    plate(b, carve(rect(IX0, IX1, -IW, IW), [AFT0, FORE0]), L1, L1 - C0, CEILING)
    plate(b, carve(rect(IX0, IX1, -IW, IW), [AFT1, FORE1, GRAND]), L2, L2 - C1, CEILING)
    slab(b, rect(DX0, DX1, -DZ, DZ), L3, L3 - C2, CEILING)
    slab(b, rect(BX0, BX1, -BZ, BZ), L4, L4 - C3, WHITE_PAINT)
    # the stern and the bow: solid, stepped in, their tops more open deck
    for x0, x1, hw in STERN + BOW:
        b.box([(x0 + x1) / 2.0, (BOTTOM + L1) / 2.0, 0.0], [x1 - x0, L1 - BOTTOM, 2 * hw], HULL)
        b.box([(x0 + x1) / 2.0, (L1 + L2) / 2.0, 0.0], [x1 - x0, L2 - L1, 2 * hw], WHITE_PAINT)
        tiled(b, rect(x0, x1, -hw, hw), L2, TEAK, "planks", DECAL_TILE["planks"])
    # paint and floors
    special = ("engine", "baths", "hold", "afthall", "hall", "galley", "tophall")
    for key, name, inner, y0, y1, colour, floor, decal in ROOMS:
        holes = w.holes_for(inner, y0, y1)
        if key in special:
            interior(b, inner, y0, y1, colour, holes)
        else:
            interior(b, inner, y0, y1, colour, holes, floor=floor, floor_decal=decal)
    flights0 = {"engine": [AFT0], "hold": [FORE0], "afthall": [AFT0, AFT1], "galley": [FORE0, FORE1],
                "hall": [GRAND], "tophall": [GRAND]}
    looks = {"engine": (L0, "#4a4a4e", "tiles"), "hold": (L0, "#6a5a44", "planks"),
             "afthall": (L1, "#8a8a80", "tiles"), "galley": (L1, "#d8d4c8", "tiles"),
             "hall": (L1, "#e8e4dc", "tiles"), "tophall": (L2, "#7a1a2a", "")}
    for key, name, inner, y0, y1, colour, floor, decal in ROOMS:
        if key not in looks:
            continue
        y, colour, decal = looks[key]
        for piece in carve(inner, [grow(r, 0.1) for r in flights0[key]]):
            if decal:
                tiled(b, piece, y, colour, decal, DECAL_TILE[decal])
            else:
                covering(b, piece, y, colour)
    # the open deck's planking, the boat deck's
    deck = carve(rect(IX0, IX1, -IW, IW), [rect(DX0, DX1, -DZ, DZ), grow(AFT1, 0.1), grow(FORE1, 0.1),
                                           AFT2, FORE2])
    for piece in deck:
        tiled(b, piece, L2, TEAK, "planks", DECAL_TILE["planks"])
    for piece in carve(rect(DX0, DX1, -DZ, DZ), [rect(BX0, BX1, -BZ, BZ)]):
        tiled(b, piece, L3, TEAK, "planks", DECAL_TILE["planks"])
    # the hull's paint outside: the red below the waterline, the gold line
    for z in (W + 0.06, -W - 0.06):
        b.box([(HX0 + HX1) / 2.0, SEA + 0.4, z], [HX1 - HX0, 2.4, 0.12], "#8a1a1a", collide=False)
        b.box([(HX0 + HX1) / 2.0, L1 - 0.8, z], [HX1 - HX0, 0.3, 0.12], GOLD, collide=False)
    for x0, x1, hw in STERN + BOW:
        for z in (hw + 0.06, -hw - 0.06):
            b.box([(x0 + x1) / 2.0, SEA + 0.4, z], [x1 - x0, 2.4, 0.12], "#8a1a1a", collide=False)
            b.box([(x0 + x1) / 2.0, L1 - 0.8, z], [x1 - x0, 0.3, 0.12], GOLD, collide=False)
    # her name on the bows (white on the black, over the ports) and the stern
    for z, facing in ((W + 0.02, "z+"), (-W - 0.02, "z-")):
        letters(b, 74.0, 11.7, z, "AURORA", 2.0, HULL, WHITE_PAINT, facing, depth=0.1)
    letters(b, STERN[-1][0] - 0.02, 18.6, 0.0, "AURORA", 1.6, WHITE_PAINT, HULL, "x-", depth=0.1)


# ================================================================ the rails
def rail(b: ArenaArea, a: Tuple[float, float], c: Tuple[float, float], y: float,
         colour: str = WHITE_PAINT, top: str = TEAK) -> None:
    """A ship's rail from ``a`` to ``c`` (x, z) on a deck at ``y``: posts and
    a broad cap, the gap under it too low for anybody to slip through."""
    (ax, az), (cx, cz) = a, c
    along_x = abs(cx - ax) >= abs(cz - az)
    length = abs(cx - ax) if along_x else abs(cz - az)
    mx, mz = (ax + cx) / 2.0, (az + cz) / 2.0
    if along_x:
        b.box([mx, y + 3.15, mz], [length, 0.3, 0.5], top)
        b.box([mx, y + 1.6, mz], [length, 0.16, 0.2], colour, collide=False)
    else:
        b.box([mx, y + 3.15, mz], [0.5, 0.3, length], top)
        b.box([mx, y + 1.6, mz], [0.2, 0.16, length], colour, collide=False)
    n = max(1, int(round(length / 2.4)))
    for k in range(n + 1):
        u = -length / 2.0 + 0.15 + k * (length - 0.3) / n
        px, pz = (mx + u, mz) if along_x else (mx, mz + u)
        b.box([px, y + 1.5, pz], [0.3, 3.0, 0.3], colour)


def _rails(b: ArenaArea) -> None:
    y = L2
    # along the hull, round the stern and the bow, step by step
    for s in (1, -1):
        rail(b, (HX0, s * (W - 0.6)), (HX1, s * (W - 0.6)), y)
        prev = W
        for x0, x1, hw in STERN:
            rail(b, (x0, s * (hw - 0.6)), (x1, s * (hw - 0.6)), y)
            if hw < prev:
                rail(b, (x1 + 0.25, s * (hw - 0.6)), (x1 + 0.25, s * (prev - 0.6)), y)
            prev = hw
        prev = W
        for x0, x1, hw in BOW:
            rail(b, (x0, s * (hw - 0.6)), (x1, s * (hw - 0.6)), y)
            if hw < prev:
                rail(b, (x0 - 0.25, s * (hw - 0.6)), (x0 - 0.25, s * (prev - 0.6)), y)
            prev = hw
    rail(b, (STERN[-1][0] + 0.25, -STERN[-1][2] + 0.6), (STERN[-1][0] + 0.25, STERN[-1][2] - 0.6), y)
    rail(b, (BOW[-1][1] - 0.25, -BOW[-1][2] + 0.6), (BOW[-1][1] - 0.25, BOW[-1][2] - 0.6), y)
    # round the boat deck (open where the outside stairs arrive), and the
    # wells of the crew's stairs on the open deck
    y = L3
    for s in (1, -1):
        rail(b, (DX0, s * (DZ - 0.35)), (BX0, s * (DZ - 0.35)), y)
    rail(b, (BX0, -(DZ - 0.35)), (DX1, -(DZ - 0.35)), y)
    rail(b, (BX0, DZ - 0.35), (FORE2[0] - 4.0, DZ - 0.35), y)
    rail(b, (DX1 - 0.35, -DZ + 0.6), (DX1 - 0.35, -BZ), y)
    rail(b, (DX0 + 0.35, -DZ + 0.6), (DX0 + 0.35, AFT2[2]), y)
    rail(b, (DX0 + 0.35, AFT2[3]), (DX0 + 0.35, DZ - 0.6), y)
    for well in (AFT1, FORE1):
        x0, x1, z0, z1 = well
        rail(b, (x0 - 0.25, z0), (x0 - 0.25, z1), L2)
        rail(b, (x1 + 0.25, z0), (x1 + 0.25, z1), L2)
    rail(b, (FORE1[0], FORE1[2] - 0.25), (FORE1[1], FORE1[2] - 0.25), L2)
    for well in (AFT0, FORE0):
        x0, x1, z0, z1 = well
        rail(b, (x0 - 0.25, z0), (x0 - 0.25, z1), L1, "#5a5a52", "#5a5a52")
        rail(b, (x1 + 0.25, z0), (x1 + 0.25, z1), L1, "#5a5a52", "#5a5a52")
        rail(b, (x0, z0 - 0.25), (x1, z0 - 0.25), L1, "#5a5a52", "#5a5a52")
    x0, x1, z0, z1 = GRAND
    for z in (z0 - 0.25, z1 + 0.25):
        rail(b, (x0, z), (x1 + 0.5, z), L2, "#2a1a12", BRASS)
    rail(b, (x1 + 0.25, z0), (x1 + 0.25, z1), L2, "#2a1a12", BRASS)


# ============================================================== the stairs
def _balustrade(b: ArenaArea, axis: str, near: float, far: float, sides: Sequence[float],
                y0: float, y1: float, colour: str, cap: str) -> None:
    steps = max(1, int(math.ceil(abs(y1 - y0) / 2.0 - 1e-6)))
    run = (far - near) / steps
    for i in range(steps):
        top = y0 + (y1 - y0) * (i + 1) / steps
        mid = near + run * (i + 0.5)
        for s in sides:
            if axis == "x":
                b.box([mid, top + 1.5, s], [abs(run), 3.0, 0.4], colour)
                b.box([mid, top + 3.1, s], [abs(run), 0.2, 0.6], cap, material="metal")
            else:
                b.box([s, top + 1.5, mid], [0.4, 3.0, abs(run)], colour)
                b.box([s, top + 3.1, mid], [0.6, 0.2, abs(run)], cap, material="metal")


def _stairs(b: ArenaArea) -> None:
    for well, y0, y1 in ((AFT0, L0, L1), (FORE0, L0, L1), (AFT1, L1, L2), (FORE1, L1, L2)):
        x0, x1, z0, z1 = well
        flight(b, "z", z0, z1, x0, x1, y0, y1, "#6a6a62", fill=y0 - 0.3)
    x0, x1, z0, z1 = GRAND
    flight(b, "x", x1, x0, z0, z1, L1, L2, "#7a1a2a", fill=L1 - 0.3)
    _balustrade(b, "x", x1, x0, (z0 + 0.2, z1 - 0.2), L1, L2, "#2a1a12", BRASS)
    for z in (z0 + 0.2, z1 - 0.2):
        b.box([x1 + 0.5, L1 + 2.6, z], [1.0, 5.2, 1.0], "#2a1a12")
        b.sphere([x1 + 0.5, L1 + 5.7, z], [1.2, 1.2, 1.2], BRASS, material="metal")
    # the outside stairs to the boat deck
    x0, x1, z0, z1 = AFT2
    flight(b, "x", x0, x1, z0, z1, L2, L3, WHITE_PAINT, fill=L2 - 0.3)
    _balustrade(b, "x", x0, x1, (z0 + 0.2, z1 - 0.2), L2, L3, WHITE_PAINT, TEAK)
    x0, x1, z0, z1 = FORE2
    flight(b, "x", x1, x0, z0, z1, L2, L3, WHITE_PAINT, fill=L2 - 0.3)
    _balustrade(b, "x", x1, x0, (z0 + 0.2, z1 - 0.2), L2, L3, WHITE_PAINT, TEAK)


# ============================================================ the lower deck
def _lower(b: ArenaArea) -> None:
    y = L0
    # ---- the engine room: two great engines, the shafts aft, the gauges
    for z in (-10.0, 10.0):
        b.box([-83.0, y + 3.0, z], [18.0, 6.0, 7.0], "#3a3e46", material="metal")
        for k in range(4):
            b.cyl([-90.0 + k * 4.6, y + 7.4, z], [3.4, 2.8, 3.4], "#5a5e66", material="metal")
            b.cyl([-90.0 + k * 4.6, y + 9.0, z], [2.0, 0.4, 2.0], BRASS, material="metal")
        b.cyl([-97.4, y + 2.4, z], [1.4, 10.8, 1.4], "#8a8e96", r=[0.0, 0.0, 1.5708],
              material="metal", collide=False)
    b.box([-98.0, y + 2.0, 13.0], [4.0, 4.0, 2.0], "#3a3e46", material="metal")
    for k, c in enumerate(("#f2f0ea", "#f2f0ea", "#f2f0ea")):
        b.cyl([-98.0 - 1.2 + k * 1.2, y + 3.4, 11.98], [1.0, 0.06, 1.0], c, r=[1.5708, 0.0, 0.0],
              collide=False)
    stamp(b, [C(0.0, 0.0, 0.0, 1.0, 3.2, 1.0, BRASS, m="metal"),
              C(0.0, 3.2, 0.0, 1.6, 0.4, 1.6, BRASS, m="metal")], -78.0, 2.0, y)
    for x in (-90.0, -78.0):
        strip_light(b, x, 0.0, C0, 4.0, "x", "#fff4dc", 1.0)
    # ---- the boiler room: four boilers, their furnaces, the coal
    for x in (-62.0, -48.0):
        for z in (-11.0, 11.0):
            b.cyl([x, y + 4.0, z], [7.0, 8.0, 7.0], "#4a3a32", material="metal")
            b.cyl([x, y + 8.2, z], [6.0, 0.4, 6.0], "#3a2a22", material="metal")
            b.box([x, y + 1.6, z - (3.56 if z > 0 else -3.56)], [2.0, 1.6, 0.12], "#ff7a1a",
                  material="neon", collide=False)
    for x0, x1 in ((-69.7, -66.0), (-44.0, -40.3)):
        for z, s in ((-17.0, 1), (17.0, -1)):
            b.box([(x0 + x1) / 2.0, y + 1.2, z], [x1 - x0, 2.4, 6.0], "#1a1a1a")
    for x in (-62.0, -48.0):
        strip_light(b, x, 0.0, C0, 4.0, "x", "#ffd8a8", 1.0)
    # ---- the crew's quarters: bunks, the mess table, lockers
    for x in (-36.0, -28.0, -20.0):
        for z in (-17.6, 17.6):
            for k, yy in enumerate((y, y + 4.4)):
                b.box([x, yy + 0.8, z], [6.6, 0.6, 3.0], "#6a5a44")
                b.box([x, yy + 1.4, z], [6.0, 0.4, 2.6], "#c8c0b0", collide=False)
            for dx in (-3.2, 3.2):
                b.box([x + dx, y + 3.2, z + (1.3 if z > 0 else -1.3)], [0.3, 6.4, 0.3], "#4a3a2a")
    stamp(b, fx.table(14.0, 3.6, "#8a7a5a", "#5a4a3a"), -25.0, 0.0, y)
    for z in (-2.8, 2.8):
        b.box([-25.0, y + 0.9, z], [12.0, 1.8, 1.2], "#5a4a3a")
    place(b, "teapot", -25.0, 0.0, y + TABLE_TOP, 0, hide=False)
    for z in (-9.0, 9.0):
        b.box([-38.8, y + 3.5, z], [1.6, 7.0, 6.0], "#4a5a6a", material="metal")
    for x in (-32.0, -18.0):
        strip_light(b, x, 0.0, C0, 4.0, "x", "#fff4dc", 1.0)
    # ---- the swimming bath: the pool, its rim, the cubicles, the steps
    px0, px1, pz0, pz1 = 0.0, 22.0, -8.0, 8.0
    tiled(b, rect(px0, px1, pz0, pz1), y, "#3a8aa8", "tiles", DECAL_TILE["tiles"])
    for piece in carve(rect(-9.7, 29.7, -IW, IW), [rect(px0 - 1.0, px1 + 1.0, pz0 - 1.0, pz1 + 1.0)]):
        tiled(b, piece, y, "#e8f0f0", "tiles", DECAL_TILE["tiles"])
    rim = 1.2
    for a, c, d, e in ((px0 - 1.0, px1 + 1.0, pz0 - 1.0, pz0), (px0 - 1.0, px1 + 1.0, pz1, pz1 + 1.0),
                       (px0 - 1.0, px0, pz0, pz1), (px1, px1 + 1.0, pz0, pz1)):
        b.box([(a + c) / 2.0, y + rim / 2.0, (d + e) / 2.0], [c - a, rim, e - d], "#e8f0f0")
    b.box([(px0 + px1) / 2.0, y + 0.9, 0.0], [px1 - px0, 0.06, pz1 - pz0], "#5ab8d8",
          material="glass", collide=False, alpha=0.55)
    for x in range(-6, 28, 6):
        for s in (1, -1):
            b.box([float(x), y + 3.5, s * (IW - 1.5)], [0.3, 7.0, 3.0], "#c8e0e8")
    for x in (-4.0, 26.0):
        for z in (-12.0, 12.0):
            b.cyl([x, (y + C0) / 2.0, z], [1.4, C0 - y, 1.4], "#e8f0f0")
    stamp(b, [B(0.0, 0.0, 0.0, 1.6, 4.0, 1.6, WHITE), B(0.0, 4.0, 0.0, 2.0, 0.3, 2.0, "#c8401e")],
          24.0, 10.0, y)
    for x in (2.0, 18.0):
        strip_light(b, x, 0.0, C0, 6.0, "x", "#e8f8ff", 1.2)
    # ---- the cargo hold: crates, trunks, a motor car in its sling
    for x, z, h in ((36.0, -16.0, 2), (40.0, -16.0, 1), (36.0, 16.0, 1), (52.0, 14.0, 2), (66.0, 16.0, 1),
                    (70.0, 12.0, 2), (58.0, -16.0, 1), (66.0, -10.0, 1)):
        for k in range(h):
            b.box([x, y + 1.8 + k * 3.6, z], [3.6, 3.6, 3.6], ("#8a6a3a", "#7a5a32")[k % 2])
    from ..kit import car
    car(b, 48.0, -2.0, "x", "#5a1a1a", y=y)
    for dx in (-5.0, 5.0):
        b.box([48.0 + dx, (y + 5.0 + C0) / 2.0, -2.0], [0.12, C0 - y - 5.0, 0.12], "#c8b080",
              collide=False)
    b.box([48.0, C0 - 0.4, -2.0], [11.0, 0.4, 0.4], "#8a8e96", material="metal", collide=False)
    for x, z in ((40.0, 4.0), (60.0, 2.0)):
        place(b, "treasure_chest", x, z, y, 0, hide=False)
    place(b, "hatbox", 42.4, 4.0, y, 0, hide=False)
    for x in (40.0, 56.0, 72.0):
        strip_light(b, x, 0.0, C0, 4.0, "x", "#ffe8b8", 1.0)


# ============================================================ the saloon deck
def _saloon(b: ArenaArea) -> None:
    y = L1
    # ---- the aft hall: lifejackets, the notices
    for z in (-12.0, 12.0):
        stamp(b, fx.shelf_unit(6.0, 2, 1.8, "#8a8e96"), -101.8, z, y, 1)
        for k, top in enumerate(fx.shelf_tops(2)[1:2]):
            for j in range(3):
                stamp(b, [R(0.0, 0.0, 0.0, 1.4, 1.0, 1.6, "#e85a1e")], -101.8, z - 2.0 + j * 2.0, y + top)
    b.box([-86.36, y + 5.0, 10.0], [0.08, 3.0, 4.0], "#c8b080", collide=False)
    strip_light(b, -94.0, 0.0, C1, 4.0, "x", "#fff4dc", 1.0)
    # ---- the hospital: beds, the cabinet, the doctor's desk
    for x in (-82.0, -76.0, -70.0):
        stamp(b, fx.bed("#e8f0f0", 4.4, 8.0, frame="#c8ccd4"), x, IW - 4.0, y, 2)
    stamp(b, [B(0.0, 0.0, 0.0, 5.0, 7.0, 1.8, "#e8f0f0"),
              B(0.0, 1.0, 0.92, 4.4, 5.4, 0.06, "#cfe8ff", m="glass", a=0.4)], -76.0, -IW + 0.9, y, 0)
    stamp(b, fx.table(5.0, 2.6, WOOD_DARK, WOOD_DARK), -82.0, -12.0, y)
    place(b, "dining_chair", -82.0, -14.4, y, 0, hide=False)
    stamp(b, [B(0.0, 0.0, 0.0, 7.0, 2.8, 2.6, "#c8ccd4", m="metal"),
              B(0.0, 2.8, 0.0, 7.0, 0.3, 2.6, WHITE)], -72.0, -9.0, y)
    for x in (-80.0, -72.0):
        strip_light(b, x, 0.0, C1, 4.0, "x", "#ffffff", 1.0)
    # ---- the staterooms: a bed, a wardrobe, a chair, a trunk in each
    for k in range(3):
        x0, x1 = CABINS[k] + P / 2.0, CABINS[k + 1] - P / 2.0
        mid = (x0 + x1) / 2.0
        for s in (1, -1):
            colour = ("#3a4a8a", "#8a2a3a", "#2a6a4a", "#6a3a6a", "#8a6a2a", "#3a6a8a")[k * 2 + (s < 0)]
            stamp(b, fx.bed(colour, 7.0, 10.0), x1 - 4.0, s * (IW - 5.0), y, 2 if s > 0 else 0)
            stamp(b, fx.wardrobe(WOOD_DARK, 5.0, 8.0, 2.4), x0 + 1.2, s * (IW - 4.0), y, 1)
            place(b, "armchair", x0 + 2.4, s * 8.0, y, 1, hide=False)
            place(b, "treasure_chest" if (k + (s > 0)) % 2 else "hatbox", x1 - 4.0, s * (IW - 11.2), y,
                  0, hide=False)
            stamp(b, fx.rug(6.0, 5.0, "#c8a040"), mid, s * 11.0, y)
            hang(b, fx.pendant(1.8, CREAM), mid, C1, s * 11.0)
    for x in (-58.0, -40.0, -22.0):
        strip_light(b, x, 0.0, C1, 3.0, "x", "#ffe8b8", 1.0)
    # ---- the foot of the grand staircase: the purser, the shop
    stamp(b, fx.counter(12.0, 2.4, "#3a2a1e", BRASS, "#5a3a24"), 0.0, -14.0, y, 0)
    stamp(b, [B(0.0, 0.0, 0.0, 3.0, 4.0, 2.8, "#3a3a3a", m="metal"),
              C(0.0, 2.0, 1.44, 1.0, 0.12, 1.0, "#c8ccd4", m="metal")], 6.0, -IW + 1.4, y, 0)
    stamp(b, fx.shelf_unit(8.0, 2, 1.8, WOOD_DARK, metal=False), -6.0, -IW + 0.9, y, 0)
    stamp(b, [B(0.0, 0.0, 0.0, 1.0, 0.3, 1.4, "#c8b080")], 2.0, -14.0, y + COUNTER_TOP)
    stamp(b, fx.display_case(5.0, 2.6, 3.0), -6.0, 15.0, y)
    stamp(b, fx.display_case(5.0, 2.6, 3.0), 6.0, 15.0, y)
    stamp(b, [S(0.0, 0.0, 0.0, 0.7, 0.7, 0.7, "#cfe8ff", m="glass")], -6.0, 15.0, y + 3.1)
    hang(b, chandelier(3.0, 8, GOLD), 0.0, C1, 12.0)
    hang(b, chandelier(3.0, 8, GOLD), 0.0, C1, -12.0)
    # ---- the dining saloon: tables for six, pillars, the captain's table
    for x in (20.0, 30.0, 40.0):
        for z in (-15.0, -5.0, 5.0, 15.0):
            stamp(b, [C(0.0, 0.0, 0.0, 0.8, TABLE_TOP, 0.8, WOOD_DARK),
                      C(0.0, TABLE_TOP, 0.0, 4.6, 0.2, 4.6, WHITE)], x, z, y)
            stamp(b, candelabra(), x, z, y + TABLE_TOP + 0.2)
            place(b, "dining_chair", x - 3.0, z, y, 1, hide=False)
            place(b, "dining_chair", x + 3.0, z, y, 3, hide=False)
    stamp(b, fx.table(4.0, 16.0, WOOD_DARK, WOOD_DARK, cloth=WHITE), 54.0, 0.0, y)
    for z in (-6.0, -2.0, 2.0, 6.0):
        place(b, "dining_chair", 51.4, z, y, 1, hide=False)
        place(b, "dining_chair", 56.6, z, y, 3, hide=False)
    for z in (-5.0, 5.0):
        stamp(b, candelabra(), 54.0, z, y + TABLE_TOP)
    for z in (-10.0, 10.0):
        b.cyl([46.0, (y + C1) / 2.0, z], [1.4, C1 - y, 1.4], "#e8dcc0")
    stamp(b, fx.counter(8.0, 2.0, WOOD_DARK, WOOD_DARK, "#6a4a2a"), 38.0, IW - 1.0, y, 2)
    for x in (24.0, 36.0, 48.0):
        hang(b, chandelier(2.6, 6, GOLD), x, C1, 0.0)
    # ---- the galley
    for x in (66.0, 70.4):
        stamp(b, fx.stove(4.0, 2.8), x, -IW + 1.4, y, 0)
    stamp(b, fx.counter(8.0, 2.8), 70.0, IW - 1.4, y, 2)
    stamp(b, fx.table(3.6, 9.0, "#c8ccd4", "#8a8e96"), 68.0, 0.0, y)
    place(b, "cheese_wheel", 68.0, -2.0, y + TABLE_TOP, 0, hide=False)
    place(b, "teapot", 68.0, 2.0, y + TABLE_TOP, 0, hide=False)
    for x in (66.0, 74.0):
        strip_light(b, x, 0.0, C1, 4.0, "z", "#ffffff", 1.0)


# ======================================================== the promenade deck
def _deckhouse(b: ArenaArea) -> None:
    y = L2
    # ---- the gymnasium: bicycles, the rowing machine, the electric horse
    for x in (-72.0, -68.0, -64.0):
        stamp(b, [B(0.0, 0.0, 0.0, 0.4, 1.6, 2.6, IRON), B(0.0, 1.6, -0.8, 0.4, 1.2, 0.4, IRON),
                  B(0.0, 2.8, -0.8, 0.8, 0.3, 1.2, "#3a2a1a"), C(0.0, 0.0, 0.9, 0.3, 2.6, 0.3, IRON),
                  B(0.0, 2.6, 0.9, 1.6, 0.2, 0.2, IRON)], x, -9.0, y)
    stamp(b, [B(0.0, 0.0, 0.0, 1.6, 0.6, 6.0, WOOD), B(0.0, 0.6, -1.0, 1.2, 0.4, 1.2, "#3a2a1a")],
          -64.0, 8.0, y)
    stamp(b, [B(0.0, 0.0, 0.0, 1.2, 2.4, 1.2, IRON), R(0.0, 2.4, 0.0, 1.6, 1.6, 4.0, "#8a5a3a"),
              R(0.0, 3.6, 2.4, 1.0, 1.6, 1.0, "#8a5a3a"), B(0.0, 4.0, -0.2, 1.4, 0.4, 1.4, "#3a2a1a")],
          -60.0, 7.0, y)
    b.cyl([-60.0, C2 - 0.6, -6.0], [0.1, 1.2, 0.1], IRON, collide=False)
    b.cyl([-60.0, C2 - 3.4, -6.0], [1.6, 4.4, 1.6], "#7a2a1a")
    for k in range(6):
        b.box([-75.3, y + 1.2 + k * 1.3, 0.0], [0.2, 0.2, 6.0], WOOD, collide=False)
    b.box([-75.3, y + 4.6, -3.1], [0.3, 7.6, 0.2], WOOD)
    b.box([-75.3, y + 4.6, 3.1], [0.3, 7.6, 0.2], WOOD)
    strip_light(b, -66.0, 0.0, C2, 6.0, "x", "#ffffff", 1.0)
    # ---- the library: shelves, reading tables, a writing desk
    for z in (-12.4, 12.4):
        stamp(b, fx.bookcase(14.0, 7.6, 1.6, WOOD_DARK, seed=int(z) + 50), -47.0, z, y, 0 if z < 0 else 2)
    for x in (-51.0, -43.0):
        stamp(b, fx.table(4.0, 3.0, WOOD_DARK, WOOD_DARK), x, -5.0, y)
        stamp(b, [C(0.0, 0.0, 0.0, 0.5, 1.2, 0.5, BRASS, m="metal"),
                  K(0.0, 1.2, 0.0, 1.2, 0.8, 1.2, "#1e5a3a")], x, -5.0, y + TABLE_TOP)
        place(b, "dining_chair", x, -7.4, y, 0, hide=False)
    for x in (-51.0, -43.0):
        place(b, "armchair", x, 6.0, y, 2, hide=False)
    place(b, "globe", -39.8, 9.0, y, 0, hide=False)
    for x in (-51.0, -43.0):
        hang(b, fx.pendant(1.8, "#1e5a3a"), x, C2, 0.0)
    # ---- the smoking room: the fire, leather chairs, card tables
    stamp(b, fx.fireplace(8.0, 7.0, 2.4), -37.7 + 1.2, -7.5, y, 1)
    stamp(b, fx.painting(4.0, 3.0, "portrait"), -37.7, -7.5, y + 7.6, 1)
    for x, z in ((-31.0, -8.0), (-31.0, -3.0)):
        place(b, "armchair", x, z, y, 3, hide=False)
    for x, z in ((-28.0, 6.0), (-20.0, -6.0)):
        stamp(b, fx.table(4.0, 4.0, "#1e5a3a", WOOD_DARK), x, z, y)
        for dx, q in ((-2.8, 1), (2.8, 3)):
            place(b, "armchair", x + dx, z, y, q, hide=False)
    stamp(b, fx.counter(6.0, 2.0, "#3a2418", BRASS, "#5a3a24"), -20.0, -11.6, y, 0)
    for x in (-30.0, -20.0):
        hang(b, fx.pendant(1.8, "#c8a040"), x, C2, 0.0)
    # ---- the top of the grand staircase: the clock, the dome's light
    b.box([-13.62, y + 5.2, 0.0], [0.16, 4.6, 5.0], "#5a3a24", collide=False)
    b.cyl([-13.5, y + 5.6, 0.0], [2.4, 0.1, 2.4], "#f2e8c8", r=[0.0, 0.0, 1.5708], collide=False)
    letters(b, -13.46, y + 3.6, 0.0, "HONOUR", 0.6, "#5a3a24", "#e8c860", "x+", depth=0.04)
    hang(b, chandelier(3.4, 10, GOLD), 0.0, C2, 0.0)
    for z in (-11.0, 11.0):
        place(b, "fern", -11.6, z, y, 0, hide=False)
        place(b, "fern", 11.6, z, y, 0, hide=False)
    # ---- the palm court: wicker, palms, a fountain, trellis on the walls
    for x, z in ((22.0, -8.0), (22.0, 8.0), (34.0, -8.0), (34.0, 8.0), (46.0, -8.0), (46.0, 8.0)):
        stamp(b, [C(0.0, 0.0, 0.0, 0.5, TABLE_TOP, 0.5, "#c8a868"),
                  C(0.0, TABLE_TOP, 0.0, 3.0, 0.2, 3.0, "#e8d8b0")], x, z, y)
        place(b, "dining_chair", x - 2.4, z, y, 1, hide=False)
        place(b, "dining_chair", x + 2.4, z, y, 3, hide=False)
    stamp(b, [C(0.0, 0.0, 0.0, 6.0, 1.2, 6.0, "#e8e0d0"),
              C(0.0, 1.2, 0.0, 5.4, 0.06, 5.4, "#5ab8d8", m="glass", a=0.7),
              C(0.0, 1.2, 0.0, 0.8, 2.4, 0.8, "#e8e0d0"), C(0.0, 3.6, 0.0, 2.4, 0.4, 2.4, "#e8e0d0")],
          34.0, 0.0, y)
    for x in (16.4, 53.4):
        for z in (-11.4, 11.4):
            place(b, "potted_plant", x, z, y, 0, hide=False)
    for x in (24.0, 44.0):
        hang(b, chandelier(2.6, 8, BRASS), x, C2, 0.0)


def _boat_deck(b: ArenaArea) -> None:
    y = L3
    # three funnels, buff with black tops
    for x in (-54.0, -30.0, -6.0):
        b.cyl([x, y + 9.0, 0.0], [10.0, 18.0, 7.0], BUFF)
        b.cyl([x, y + 20.0, 0.0], [10.0, 4.0, 7.0], "#1a1a1e")
        b.cyl([x, y + 0.3, 0.0], [11.0, 0.6, 8.0], "#3a3a3e")
    # lifeboats in their chocks, under davits
    for x in (-66.0, -42.0, -18.0, 12.0):
        for s in (1, -1):
            z = s * 11.6
            for dx in (-2.8, 2.8):
                b.box([x + dx, y + 0.4, z], [0.8, 0.8, 2.4], WOOD_DARK)
            b.box([x, y + 1.9, z], [10.0, 2.2, 3.0], WHITE_PAINT)
            b.box([x, y + 3.05, z], [9.6, 0.1, 2.6], "#c8b890", collide=False)
            for dx in (-5.6, 5.6):
                b.box([x + dx, y + 3.0, s * 13.2], [0.5, 6.0, 0.5], WHITE_PAINT)
                b.box([x + dx, y + 6.2, s * 12.4], [0.5, 0.4, 2.1], WHITE_PAINT)
    # mushroom ventilators, low enough to step over (a tall cowl is a
    # perch a bot can jump onto and not find its way down from)
    for x, z in ((-42.0, 4.6), (-42.0, -4.6), (-18.0, 4.6), (-18.0, -4.6), (20.0, 0.0)):
        b.cyl([x, y + 0.6, z], [1.0, 1.2, 1.0], WHITE_PAINT)
        b.cyl([x, y + 1.6, z], [2.2, 0.8, 2.2], WHITE_PAINT)
        b.cyl([x, y + 1.15, z], [1.6, 0.1, 1.6], "#1a1a1e", collide=False)
    # deck chairs
    for x in (-72.0, -70.0, 20.0, 23.0):
        for s in (1, -1):
            stamp(b, [B(0.0, 0.0, 0.0, 1.8, 1.2, 5.0, TEAK), B(0.0, 1.2, -2.0, 1.8, 1.6, 0.4, TEAK)],
                  x, s * 6.0, y, 0 if s > 0 else 2)
    # ---- the bridge: the wheel, the telegraphs, the compass, the chart table
    yy = L3
    stamp(b, [C(0.0, 0.0, 0.0, 1.0, 3.4, 1.0, BRASS, m="metal")], 52.0, 0.0, yy)
    b.cyl([52.6, yy + 4.4, 0.0], [3.0, 0.3, 3.0], WOOD_DARK, r=[0.0, 0.0, 1.5708], collide=False)
    for z in (-4.0, 4.0):
        stamp(b, [C(0.0, 0.0, 0.0, 0.8, 3.2, 0.8, BRASS, m="metal"),
                  C(0.0, 3.2, 0.0, 1.6, 1.6, 0.8, BRASS, m="metal")], 53.0, z, yy)
    stamp(b, [C(0.0, 0.0, 0.0, 1.2, 3.4, 1.2, WOOD_DARK), S(0.0, 3.4, 0.0, 1.4, 1.0, 1.4, BRASS, m="metal")],
          47.0, 0.0, yy)
    stamp(b, fx.table(5.0, 3.0, WOOD, WOOD_DARK), 50.5, -7.0, yy)
    stamp(b, [B(0.0, 0.0, 0.0, 4.0, 0.05, 2.6, "#e8e0c8")], 50.5, -7.0, yy + TABLE_TOP)
    strip_light(b, 48.0, 0.0, C3, 6.0, "x", "#fff4dc", 1.0)
    # ---- the wireless room: the set, the operator's chair, a bunk
    stamp(b, fx.table(8.0, 3.0, WOOD_DARK, WOOD_DARK), 34.0, -BZ + P + 1.6, yy)
    for k, x in enumerate((31.0, 34.0, 37.0)):
        stamp(b, [B(0.0, 0.0, 0.0, 2.4, 2.4, 1.6, "#3a3a3a", m="metal"),
                  B(0.0, 1.4, 0.82, 0.6, 0.4, 0.04, "#8aff8a", m="neon", ghost=True)], x, -BZ + P + 1.6,
              yy + TABLE_TOP)
    place(b, "dining_chair", 34.0, -BZ + P + 4.0, yy, 2, hide=False)
    b.box([34.0, yy + 1.2, BZ - P - 1.6], [8.0, 2.4, 3.0], "#5a4a3a")
    b.box([34.0, yy + 2.6, BZ - P - 1.6], [7.6, 0.4, 2.6], "#c8c0b0", collide=False)
    strip_light(b, 34.0, 0.0, C3, 4.0, "x", "#fff4dc", 1.0)


def _open_deck(b: ArenaArea) -> None:
    y = L2
    # deck chairs along the promenade, life rings on the rail, lamps
    for x in range(-70, 54, 8):
        for s in (1, -1):
            if any(a - 3.0 < x < c + 3.0 for a, c in ((-13.0, -8.6), (8.4, 12.8), (26.0, 30.4),
                                                      (43.0, 47.4), (-28.4, -24.0))):
                continue
            stamp(b, [B(0.0, 0.0, 0.0, 1.8, 1.2, 4.0, TEAK), B(0.0, 1.2, -1.6, 1.8, 1.6, 0.4, TEAK)],
                  float(x), s * 16.0, y, 0 if s > 0 else 2)
    for x in (-60.0, -20.0, 20.0, 60.0):
        for s in (1, -1):
            b.cyl([x, y + 2.0, s * (W - 0.26)], [2.4, 0.4, 2.4], "#e85a1e", r=[1.5708, 0.0, 0.0],
                  collide=False)
    for x in range(-64, 56, 16):
        for s in (1, -1):
            b.box([float(x), C2 - 1.0, s * (DZ + 0.4)], [0.8, 0.8, 0.8], "#ffe8b8", material="neon",
                  collide=False)
            b.box([float(x), C2 - 0.5, s * (DZ + 0.2)], [0.3, 0.2, 0.4], IRON, collide=False)
    # the aft deck: the flagstaff, deck games, a bench
    b.cyl([STERN[-1][0] + 1.2, y + 8.0, 0.0], [0.4, 16.0, 0.4], WOOD_DARK)
    b.box([STERN[-1][0] + 1.2, y + 14.4, 1.4], [0.08, 2.4, 2.8], "#c8202a", collide=False)
    for k in range(4):
        b.box([-100.0 + k * 0.0, y + 0.03, -12.0 + k * 2.0], [12.0, 0.04, 0.2], WHITE_PAINT, collide=False)
    stamp(b, fx.bench(6.0), -100.0, 12.0, y, 1)
    # the fore deck: the hatch, the derrick, the windlass, the mast
    b.box([96.0, y + 0.8, 0.0], [12.0, 1.6, 12.0], WOOD_DARK)
    b.box([96.0, y + 1.65, 0.0], [12.4, 0.1, 12.4], "#5a5040", collide=False)
    b.cyl([104.0, y + 22.0, 0.0], [1.6, 44.0, 1.6], "#c8a868")
    b.cyl([104.0, y + 30.0, 0.0], [4.4, 3.0, 4.4], "#c8a868")
    b.cyl([104.0, y + 31.6, 0.0], [4.6, 0.2, 4.6], "#3a3a3e", collide=False)
    b.box([100.0, y + 10.0, 0.0], [8.0, 0.6, 0.6], "#5a5e66", material="metal", collide=False)
    for z in (-3.0, 3.0):
        b.cyl([112.0, y + 1.4, z], [2.4, 2.8, 2.4], IRON, material="metal")
    for x, z in ((90.0, -16.0), (90.0, 16.0), (106.0, -10.0), (106.0, 10.0)):
        for dx in (-0.8, 0.8):
            b.cyl([x + dx, y + 1.0, z], [1.0, 2.0, 1.0], IRON, material="metal")
    b.cyl([BOW[-1][1] - 1.2, y + 6.0, 0.0], [0.3, 12.0, 0.3], WOOD_DARK)
    # running lights: red to port, green to starboard, white at the mast
    b.box([54.0, L3 + 6.0, -BZ - 0.1], [1.2, 1.2, 0.2], "#ff3a3a", material="neon", collide=False)
    b.box([54.0, L3 + 6.0, BZ + 0.1], [1.2, 1.2, 0.2], "#3aff6a", material="neon", collide=False)
    b.sphere([104.0, y + 44.4, 0.0], [1.0, 1.0, 1.0], "#ffffff", material="neon", collide=False)


def _sea(b: ArenaArea, rng: random.Random) -> None:
    """The sea to the horizon, and the ice."""
    b.box([0.0, SEA - 0.1, 0.0], [2600.0, 0.2, 2600.0], "#0a1a2a", collide=False, alpha=0.94)
    for k in range(9):
        a = rng.uniform(0.0, 2.0 * math.pi)
        d = rng.uniform(260.0, 520.0)
        x, z = math.cos(a) * d, math.sin(a) * d
        h = rng.uniform(14.0, 46.0)
        w = rng.uniform(26.0, 60.0)
        b.cone([x, SEA + h / 2.0 - 2.0, z], [w, h, w * rng.uniform(0.6, 1.0)], "#dce8f0", collide=False)
        b.box([x + w * 0.2, SEA + 1.0 + k * 0.07, z], [w * 0.8, 2.6, w * 0.5], "#c8d8e4", collide=False)


# ======================================================================= meta
def _meta(b: ArenaArea) -> None:
    starts = [(25.0, 0.0), (35.0, 0.0), (45.0, 0.0), (25.0, -10.0), (35.0, -10.0), (25.0, 10.0),
              (35.0, 10.0), (48.0, -15.0), (48.0, 15.0), (-10.0, -8.0), (10.0, 8.0), (-10.0, 8.0)]
    for x, z in starts:
        b.team_spawn("start", x, L1, z, yaw=1.5708)
    for x, z in ((22.0, -2.0), (46.0, 2.0)):
        b.team_spawn("start", x, L2, z, yaw=1.5708)
    for x, z in ((-42.0, 18.6), (-2.0, -18.6)):
        b.team_spawn("start", x, L2, z, yaw=1.5708)
    room(b, "the engine room", -86.0, L0, 0.0, [(-74.0, 0.0), (-92.0, -3.0), (-97.5, 18.0)])
    room(b, "the boiler room", -55.0, L0, 0.0, [(-55.0, -16.0), (-66.0, 4.0)])
    room(b, "the crew's quarters", -25.0, L0, 8.0, [(-36.0, -11.0), (-14.0, 12.0)])
    room(b, "the swimming bath", 11.0, L0, -12.0, [(11.0, 0.0), (-5.0, 16.0), (27.0, -14.0)])
    room(b, "the cargo hold", 60.0, L0, -4.0, [(36.0, 8.0), (76.0, 4.0), (52.0, -16.0)])
    room(b, "the aft hall", -96.0, L1, 4.0, [(-101.0, 2.0), (-90.0, -16.0)])
    room(b, "the ship's hospital", -76.0, L1, 4.0, [(-84.0, -18.0), (-68.0, 10.0)])
    room(b, "the stateroom corridor", -40.0, L1, 0.0, [(-60.0, 0.0), (-20.0, 0.0)])
    for k in range(3):
        x0, x1 = CABINS[k] + P / 2.0, CABINS[k + 1] - P / 2.0
        mid = (x0 + x1) / 2.0
        names = (("A1", "A2"), ("A3", "A4"), ("A5", "A6"))[k]
        room(b, "stateroom " + names[0], mid, L1, 6.6, [(x0 + 3.2, 13.0)])
        room(b, "stateroom " + names[1], mid, L1, -6.6, [(x0 + 3.2, -13.0)])
    room(b, "the grand staircase", -10.0, L1, 10.0, [(10.0, -8.0), (-10.0, -18.0)])
    room(b, "the dining saloon", 35.0, L1, 0.0, [(20.0, -19.0), (48.0, 19.0), (58.0, -14.0)])
    room(b, "the galley", 72.0, L1, -8.0, [(65.0, 6.0), (82.0, 1.0)])
    room(b, "the gymnasium", -66.0, L2, 0.0, [(-72.0, 12.0), (-60.0, -11.0)])
    room(b, "the library", -47.0, L2, 2.0, [(-41.0, -10.0)])
    room(b, "the smoking room", -26.0, L2, -2.0, [(-34.0, 10.0), (-17.0, 5.0)])
    room(b, "the top of the grand staircase", -11.0, L2, 0.0, [(10.6, -9.0)])
    room(b, "the palm court", 28.0, L2, 0.0, [(52.0, -6.0), (20.0, 4.0)])
    room(b, "the promenade", -2.0, L2, 19.4, [(-58.0, 19.4), (40.0, -18.6), (-30.0, -18.6)])
    room(b, "the aft deck", -100.0, L2, -10.0, [(-112.0, 6.0), (-84.0, 12.0)])
    room(b, "the fore deck", 92.0, L2, -12.0, [(116.0, 0.0), (66.0, -12.0)])
    room(b, "the boat deck", -36.0, L3, 8.0, [(-66.0, -6.0), (2.0, -8.6), (26.0, 6.0)])
    room(b, "the bridge", 48.0, L3, 4.0, [(44.0, -6.0)])
    room(b, "the wireless room", 34.0, L3, 2.0, [(31.0, 4.0)])
    # every staircase, for the bots
    for well, y0, y1 in ((AFT0, L0, L1), (FORE0, L0, L1), (AFT1, L1, L2), (FORE1, L1, L2)):
        x0, x1, z0, z1 = well
        stair(b, ((x0 + x1) / 2.0, y0, z0 - 1.6), ((x0 + x1) / 2.0, y1, z1 + 1.6))
    x0, x1, z0, z1 = GRAND
    stair(b, (x1 + 1.6, L1, 0.0), (x0 - 1.6, L2, 0.0))
    x0, x1, z0, z1 = AFT2
    stair(b, (x0 - 1.6, L2, 0.0), (x1 + 1.6, L3, 0.0))
    x0, x1, z0, z1 = FORE2
    stair(b, (x1 + 1.6, L2, (z0 + z1) / 2.0), (x0 - 1.6, L3, (z0 + z1) / 2.0))
    b.camera(-160.0, 60.0, 90.0, -20.0, 20.0, 0.0)
    b.camera(150.0, 50.0, -70.0, 60.0, 24.0, 0.0)
    b.camera(0.0, 70.0, 0.0, 30.0, 30.0, 0.0)
    b.extra.update({"accent": "#8ad8ff", "twist": "fog", "twist_every": [36.0, 50.0],
                    "twist_for": 12.0, "twist_warn": 4.0, "fall_what": "the sea", "fall_y": SEA + 1.0, "sea": SEA,
                    "round_seconds": 190.0})


def build(b: ArenaArea) -> None:
    rng = random.Random(1912)
    b.void = True
    _sea(b, rng)
    walls = _walls()
    _shell(b, walls)
    _rails(b)
    _stairs(b)
    _lower(b)
    _saloon(b)
    _deckhouse(b)
    _boat_deck(b)
    _open_deck(b)
    _meta(b)
