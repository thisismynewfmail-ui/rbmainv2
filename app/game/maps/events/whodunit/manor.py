"""Blackwood Manor -- a country house on a stormy night, its grounds, and
what is under them.

Layout (north is -z; the drive and the gates are to the south)::

    z -150 ===================== the wall, the woods beyond ======================
              the GAZEBO          the back garden: rose beds, the POND     SHED
    z  -86    HEDGE   |    the CONSERVATORY (glass)    |              STABLES
    z  -52    MAZE    |study|billiard|corridor|dining|kitchen (cellar  (stalls,
              (west)  |----- LIBRARY --|-- GRAND HALL --|-- DRAWING ROOM  hay)
    z   28            |  (secret door)    (the stairs)      (piano)     CHAPEL
                        the drive, the fountain, the motor cars          and its
    z  150 ===================== the gates ======================== GRAVEYARD

Upstairs: the master bedroom, the landing, the nursery; the guest room,
the bathroom, the back corridor, the portrait gallery and the servants'
quarters (the back stairs come up from the kitchen).  Under the kitchen is
the wine cellar, and from the cellar a tunnel runs east under the lawn to
the crypt beneath the chapel.

The twist is the storm: every so often lightning takes the lights out.
"""
from __future__ import annotations

import random
from typing import List, Tuple

from ..kit import (ArenaArea, Surfaces, backdrop, car, carve, flight, gable, ground, lamp_post,
                   letters, perimeter, plate, rect, slab, step_paint, strip_light)
from ..prop_panic import furniture as fx
from ..prop_panic.catalogue import (B, BLACK, BRASS, C, GOLD, K, R, S, WHITE, WOOD,
                                    WOOD_DARK, place, stamp)
from ..prop_panic.rooms import (DECAL_TILE, covering, grow, interior, openings, partition, tiled,
                                 window)
from .common import candelabra, chandelier, hang, rails, room, stair

HALF = (170.0, 150.0)
SKY = {"top": "#121624", "horizon": "#3a3a52", "sun": [-0.3, 0.55, 0.4],
       "clouds": 0.95, "tint": "#a8b0d0"}
AMBIENT = "#5a6078"
GROUND = "#2e4a2a"
FOG = 520.0

LAWN = "#2e4a2a"
GRAVEL = "#8a8478"
STONE = "#8a8478"
STONE_DARK = "#5a5650"
WALLS = "#c8bca4"
TRIM = "#e8e0cc"
ROOF = "#3a3a44"
PANEL = "#5a3a24"
CEILING = "#e8e0cc"
HEDGE = "#24502a"
HEDGE_DARK = "#1e4424"

T = 1.2
F1, C1 = 0.6, 11.4
F2, C2 = 12.0, 22.6
WALL_TOP = 23.0
ROOF_TOP = 24.0
X0, X1, Z0, Z1 = -72.0, 72.0, -52.0, 28.0
IX0, IX1, IZ0, IZ1 = X0 + T, X1 - T, Z0 + T, Z1 - T
ZM = -12.0
XW, XE = -30.0, 30.0
XB1, XB2, XB3, XB4 = -42.0, -14.0, 14.0, 42.0
P = 0.6
CELLAR = -10.6            # the cellar, the tunnel and the crypt: their floor
LOW = -4.6                # the tunnel and the crypt: their ceiling

GROUND_DOORS = {
    "zm": [(-64.0, -58.0, 8.6), (-38.0, -34.0, 8.6), (-6.0, 6.0, 9.6), (52.0, 58.0, 8.6)],
    "xw": [(2.0, 8.0, 8.6)], "xe": [(2.0, 8.0, 8.6)],
    "xb1": [(-26.0, -20.0, 8.6)], "xb2": [(-34.0, -28.0, 8.6)],
    "xb3": [(-34.0, -28.0, 8.6)], "xb4": [(-46.0, -40.0, 8.6)],
}
UP_DOORS = {
    "zm": [(-64.0, -58.0, F2 + 8.0), (-6.0, 6.0, F2 + 8.6), (52.0, 58.0, F2 + 8.0)],
    "xw": [(2.0, 8.0, F2 + 8.0)], "xe": [(2.0, 8.0, F2 + 8.0)],
    "xb1": [(-26.0, -20.0, F2 + 8.0)], "xb2": [(-34.0, -28.0, F2 + 8.0)],
    "xb3": [(-34.0, -28.0, F2 + 8.0)], "xb4": [(-46.0, -40.0, F2 + 8.0)],
}

# the grand stair (hall to landing), the back stair (kitchen to the
# servants' room) and the cellar stair: x0, x1, z where it starts, z where
# it lands
GRAND = (-6.0, 6.0, 18.0, -1.0)
WELL = rect(-6.0, 6.0, -1.0, 18.0)
BACK = (65.0, 70.6, -16.0, -42.0)
BACK_WELL = rect(65.0, IX1, -42.0, -16.0)
DOWN = (43.4, 49.0, -16.0, -36.0)
DOWN_WELL = rect(43.4, 49.0, -36.0, -16.0)

CELLAR_ROOM = rect(XB4 + P / 2.0, IX1, IZ0, ZM - P / 2.0)       # its inside
TUNNEL_A = rect(X1, 112.0, -34.0, -28.0)
TUNNEL_B = rect(112.0, 118.0, -34.0, 52.0)
CRYPT = rect(104.0, 126.0, 52.0, 76.0)
CHAPEL = rect(100.0, 130.0, 50.0, 82.0)
CRYPT_STAIR = (106.0, 122.0, 70.0, 75.0)    # x bottom, x top, z0, z1
CONSERVATORY = rect(-30.0, 30.0, -86.0, Z0)
STABLES = rect(122.0, 164.0, -70.0, -24.0)
MAZE = rect(-162.0, -96.0, -56.0, 48.0)


# ================================================================ the house
G_SILL, G_TOP = 3.0, 8.8
U_SILL, U_TOP = 14.6, 20.4
FRONT = [(-5.0, 5.0, 0.0, 9.2),
         (-62.0, -54.0, G_SILL, G_TOP), (-46.0, -38.0, G_SILL, G_TOP),
         (-22.0, -14.0, G_SILL, G_TOP), (14.0, 22.0, G_SILL, G_TOP),
         (38.0, 46.0, G_SILL, G_TOP), (54.0, 62.0, G_SILL, G_TOP),
         (-62.0, -54.0, U_SILL, U_TOP), (-46.0, -38.0, U_SILL, U_TOP),
         (-22.0, -14.0, U_SILL, U_TOP), (-4.0, 4.0, U_SILL, U_TOP), (14.0, 22.0, U_SILL, U_TOP),
         (38.0, 46.0, U_SILL, U_TOP), (54.0, 62.0, U_SILL, U_TOP)]
BACKSIDE = [(-5.0, 5.0, 0.0, 9.2), (54.0, 60.0, 0.0, 9.2),
            (-62.0, -54.0, G_SILL, G_TOP), (-34.0, -24.0, G_SILL, G_TOP),
            (20.0, 28.0, G_SILL, G_TOP), (32.0, 38.0, G_SILL, G_TOP),
            (-62.0, -54.0, U_SILL, U_TOP), (-34.0, -28.0, U_SILL, U_TOP), (-4.0, 4.0, U_SILL, U_TOP),
            (20.0, 28.0, U_SILL, U_TOP), (32.0, 38.0, U_SILL, U_TOP), (50.0, 58.0, U_SILL, U_TOP)]
WEST = [(8.0, 14.0, 0.0, 9.2), (18.0, 24.0, G_SILL, G_TOP), (-6.0, 0.0, G_SILL, G_TOP),
        (-40.0, -32.0, G_SILL, G_TOP), (-24.0, -18.0, G_SILL, G_TOP),
        (18.0, 24.0, U_SILL, U_TOP), (-6.0, 0.0, U_SILL, U_TOP),
        (-40.0, -32.0, U_SILL, U_TOP), (-24.0, -18.0, U_SILL, U_TOP)]
EAST = [(8.0, 14.0, 0.0, 9.2), (18.0, 24.0, G_SILL, G_TOP), (-6.0, 0.0, G_SILL, G_TOP),
        (-30.0, -24.0, G_SILL, G_TOP),
        (18.0, 24.0, U_SILL, U_TOP), (-6.0, 0.0, U_SILL, U_TOP), (-30.0, -24.0, U_SILL, U_TOP)]


def _shell(b: ArenaArea) -> None:
    """The four outer walls (both storeys), the floors, the roof."""
    openings(b, "z", X0 + T / 2.0, T, Z0, Z1, 0.0, WALL_TOP, WALLS, WEST, glass=True)
    openings(b, "z", X1 - T / 2.0, T, Z0, Z1, 0.0, WALL_TOP, WALLS, EAST, glass=True)
    openings(b, "x", Z0 + T / 2.0, T, IX0, IX1, 0.0, WALL_TOP, WALLS, BACKSIDE, glass=True)
    openings(b, "x", Z1 - T / 2.0, T, IX0, IX1, 0.0, WALL_TOP, WALLS, FRONT, glass=True)
    for holes, axis, at, out in ((FRONT, "x", Z1 - T / 2.0, 1), (BACKSIDE, "x", Z0 + T / 2.0, -1),
                                 (WEST, "z", X0 + T / 2.0, -1), (EAST, "z", X1 - T / 2.0, 1)):
        for a, c, sill, top in holes:
            if sill > 0.5:
                window(b, axis, at, T, a, c, sill, top, TRIM, out=out)
    # a stone band at the first floor, all the way round
    slab(b, rect(X0 - 0.3, X1 + 0.3, Z1, Z1 + 0.3), 12.4, 1.0, STONE)
    slab(b, rect(X0 - 0.3, X1 + 0.3, Z0 - 0.3, Z0), 12.4, 1.0, STONE)
    slab(b, rect(X0 - 0.3, X0, Z0, Z1), 12.4, 1.0, STONE)
    slab(b, rect(X1, X1 + 0.3, Z0, Z1), 12.4, 1.0, STONE)
    # the ground floor over the cellar (with the cellar stair's well), the
    # first floor (with both stairwells), the ceiling under the roof
    plate(b, carve(rect(IX0, IX1, IZ0, IZ1), [DOWN_WELL]), F1, F1, "#6a5038")
    for a, c in ((-5.0, 5.0),):
        slab(b, rect(a, c, IZ1, Z1), F1, F1, "#6a5038")
    for a, c in ((-5.0, 5.0), (54.0, 60.0)):
        slab(b, rect(a, c, Z0, IZ0), F1, F1, "#6a5038")
    for a, c in ((8.0, 14.0),):
        slab(b, rect(X0, IX0, a, c), F1, F1, "#6a5038")
        slab(b, rect(IX1, X1, a, c), F1, F1, "#6a5038")
    plate(b, carve(rect(IX0, IX1, IZ0, IZ1), [WELL, BACK_WELL]), F2, F2 - C1, CEILING)
    slab(b, rect(IX0, IX1, IZ0, IZ1), WALL_TOP, WALL_TOP - C2, CEILING)
    slab(b, rect(X0 - 1.0, X1 + 1.0, Z0 - 1.0, Z1 + 1.0), ROOF_TOP, ROOF_TOP - WALL_TOP, ROOF)
    gable(b, rect(X0, X1, Z0, Z1), ROOF_TOP, ROOF, "x", tiers=6, rise=1.8, overhang=1.0)
    # chimneys at both ends, a little tower over the hall
    for x in (X0 + 6.0, X1 - 6.0):
        b.box([x, ROOF_TOP + 9.0, -12.0], [6.0, 18.0, 8.0], "#7a4a3a", decal="bricks")
        b.cyl([x - 1.5, ROOF_TOP + 18.8, -12.0], [1.4, 1.6, 1.4], "#9a6a4a")
        b.cyl([x + 1.5, ROOF_TOP + 18.8, -12.0], [1.4, 1.6, 1.4], "#9a6a4a")
    b.box([0.0, ROOF_TOP + 16.0, 8.0], [12.0, 10.0, 12.0], WALLS)
    b.cone([0.0, ROOF_TOP + 26.0, 8.0], [15.0, 10.0, 15.0], ROOF)
    for side, dx, dz in (("z+", 0.0, 6.06), ("x+", 6.06, 0.0), ("x-", -6.06, 0.0)):
        b.box([dx, ROOF_TOP + 16.0, 8.0 + dz], [0.12 if dx else 5.0, 5.0, 5.0 if dx else 0.12],
              "#3a3a44")
        b.box([dx * 1.01, ROOF_TOP + 16.0, 8.0 + dz * 1.01],
              [0.06 if dx else 4.0, 0.3, 0.3 if dx else 0.06], "#f2e8c8")
    # the porch: steps, columns, its roof
    slab(b, rect(-10.0, 10.0, Z1, Z1 + 8.0), F1, F1, STONE)
    for x in (-9.0, 9.0):
        b.cyl([x, F1 + 5.0, Z1 + 7.0], [1.6, 10.0, 1.6], TRIM)
    slab(b, rect(-11.0, 11.0, Z1, Z1 + 9.0), 11.8, 0.8, STONE)
    b.box([0.0, 13.0, Z1 + 8.8], [18.0, 1.6, 0.6], STONE)
    b.box([0.0, 13.0, Z1 + 9.15], [12.0, 1.0, 0.1], STONE_DARK)
    letters(b, 0.0, 13.0, Z1 + 9.2, "BLACKWOOD", 0.9, STONE_DARK, "#e8d8a0", "z+", depth=0.15)


def _partitions(b: ArenaArea) -> None:
    for y0, y1, doors in ((F1, C1, GROUND_DOORS), (F2, C2, UP_DOORS)):
        partition(b, "x", ZM, IX0, IX1, y0, y1, "#d8ccb4", doors["zm"], trim_colour=PANEL)
        partition(b, "z", XW, ZM + P / 2.0, IZ1, y0, y1, "#d8ccb4", doors["xw"], trim_colour=PANEL)
        partition(b, "z", XE, ZM + P / 2.0, IZ1, y0, y1, "#d8ccb4", doors["xe"], trim_colour=PANEL)
        for key, x in (("xb1", XB1), ("xb2", XB2), ("xb3", XB3), ("xb4", XB4)):
            partition(b, "z", x, IZ0, ZM - P / 2.0, y0, y1, "#d8ccb4", doors[key],
                      trim_colour=PANEL)


ROOMS_G = [
    # key, name, inner, wall colour, floor, decal
    ("library", "the library", rect(IX0, XW - P / 2.0, ZM + P / 2.0, IZ1), "#5a2a2a", "#5a3a24",
     "planks"),
    ("hall", "the grand hall", rect(XW + P / 2.0, XE - P / 2.0, ZM + P / 2.0, IZ1), "#e8dcc0",
     "#e8e4dc", "harlequin"),
    ("drawing", "the drawing room", rect(XE + P / 2.0, IX1, ZM + P / 2.0, IZ1), "#3a5a4a", "#6a4a2a",
     "planks"),
    ("study", "the study", rect(IX0, XB1 - P / 2.0, IZ0, ZM - P / 2.0), "#4a3a5a", "#5a3a24", "planks"),
    ("billiard", "the billiard room", rect(XB1 + P / 2.0, XB2 - P / 2.0, IZ0, ZM - P / 2.0), "#2a4a3a",
     "#5a3a24", "planks"),
    ("corridor", "the back corridor", rect(XB2 + P / 2.0, XB3 - P / 2.0, IZ0, ZM - P / 2.0), "#d8ccb4",
     "#e8e4dc", "harlequin"),
    ("dining", "the dining room", rect(XB3 + P / 2.0, XB4 - P / 2.0, IZ0, ZM - P / 2.0), "#6a2a3a",
     "#6a4a2a", "planks"),
    ("kitchen", "the kitchen", rect(XB4 + P / 2.0, IX1, IZ0, ZM - P / 2.0), "#e8e0c8", "#d8d4c8", "tiles"),
]
ROOMS_U = [
    ("master", "the master bedroom", rect(IX0, XW - P / 2.0, ZM + P / 2.0, IZ1), "#4a3a6a", "#7a3a4a", ""),
    ("landing", "the landing", rect(XW + P / 2.0, XE - P / 2.0, ZM + P / 2.0, IZ1), "#e8dcc0", "#7a2a2a", ""),
    ("nursery", "the nursery", rect(XE + P / 2.0, IX1, ZM + P / 2.0, IZ1), "#c8d8e8", "#8aa8c8", ""),
    ("guest", "the guest room", rect(IX0, XB1 - P / 2.0, IZ0, ZM - P / 2.0), "#5a6a4a", "#6a5a3a", "planks"),
    ("bath", "the bathroom", rect(XB1 + P / 2.0, XB2 - P / 2.0, IZ0, ZM - P / 2.0), "#c8e0d8", "#e8f0f0",
     "tiles"),
    ("upper", "the upstairs corridor", rect(XB2 + P / 2.0, XB3 - P / 2.0, IZ0, ZM - P / 2.0), "#e8dcc0",
     "#7a2a2a", ""),
    ("gallery", "the portrait gallery", rect(XB3 + P / 2.0, XB4 - P / 2.0, IZ0, ZM - P / 2.0), "#7a2a2a",
     "#5a3a24", "planks"),
    ("servants", "the servants' quarters", rect(XB4 + P / 2.0, IX1, IZ0, ZM - P / 2.0), "#c8bca4",
     "#7a6a5a", "planks"),
]
SIDES_G = {
    "library": ("x-", "x+", "z-", "z+"), "hall": ("x-", "x+", "z-", "z+"),
    "drawing": ("x-", "x+", "z-", "z+"),
}


def _holes(key: str, inner, doors, y0: float, up: bool) -> dict:
    """A room's doors and windows, side by side, for its paint."""
    x0, x1, z0, z1 = inner
    sill, top = (U_SILL, U_TOP) if up else (G_SILL, G_TOP)

    def win(holes, lo, hi):
        return [h for h in holes if h[1] > lo and h[0] < hi and (h[2] > F2 - 1.0) == up]

    def door(name, at, lo, hi):
        out = []
        for a, c, head in doors.get(name, ()):
            if c > lo and a < hi:
                out.append((a - 0.5, c + 0.5, y0 - 1.0, head + 0.5))
        return out

    holes = {"x-": [], "x+": [], "z-": [], "z+": []}
    walls = {"zm": ZM, "xw": XW, "xe": XE, "xb1": XB1, "xb2": XB2, "xb3": XB3, "xb4": XB4}
    front = z1 > ZM
    for name, at in walls.items():
        if name == "zm":
            if front:
                holes["z-"] += door(name, at, x0, x1)
            else:
                holes["z+"] += door(name, at, x0, x1)
        elif front == (name in ("xw", "xe")):
            if abs(at - x0) < 1.0:
                holes["x-"] += door(name, at, z0, z1)
            elif abs(at - x1) < 1.0:
                holes["x+"] += door(name, at, z0, z1)
    if abs(x0 - IX0) < 0.1:
        holes["x-"] += win(WEST, z0, z1) + [(a, c, s, t) for a, c, s, t in WEST
                                             if s < 0.5 and not up and c > z0 and a < z1]
    if abs(x1 - IX1) < 0.1:
        holes["x+"] += win(EAST, z0, z1) + [(a, c, s, t) for a, c, s, t in EAST
                                             if s < 0.5 and not up and c > z0 and a < z1]
    if abs(z1 - IZ1) < 0.1:
        holes["z+"] += win(FRONT, x0, x1) + [(a, c, s, t) for a, c, s, t in FRONT
                                              if s < 0.5 and not up and c > x0 and a < x1]
    if abs(z0 - IZ0) < 0.1:
        holes["z-"] += win(BACKSIDE, x0, x1) + [(a, c, s, t) for a, c, s, t in BACKSIDE
                                                 if s < 0.5 and not up and c > x0 and a < x1]
    del sill, top
    return holes


def _paint(b: ArenaArea) -> None:
    for rooms, y0, y1, doors, up in ((ROOMS_G, F1, C1, GROUND_DOORS, False),
                                      (ROOMS_U, F2, C2, UP_DOORS, True)):
        for key, name, inner, colour, floor, decal in rooms:
            holes = _holes(key, inner, doors, y0, up)
            wells = [w for w, here in ((WELL, key in ("landing",)), (BACK_WELL, key == "servants"),
                                       (DOWN_WELL, key == "kitchen"))
                     if here]
            stair_foot = [rect(GRAND[0], GRAND[1], GRAND[3], GRAND[2])] if key == "hall" else []
            stair_foot += [rect(BACK[0], BACK[1], BACK[3], BACK[2])] if key == "kitchen" else []
            if wells or stair_foot:
                interior(b, inner, y0, y1, colour, holes)
                for piece in carve(inner, [grow(w, 0.1) for w in wells + stair_foot]):
                    if decal:
                        tiled(b, piece, y0, floor, decal, DECAL_TILE.get(decal, 8.0))
                    else:
                        covering(b, piece, y0, floor)
            else:
                interior(b, inner, y0, y1, colour, holes, floor=floor, floor_decal=decal)


def _stairs(b: ArenaArea) -> None:
    x0, x1, near, far = GRAND
    flight(b, "z", near, far, x0, x1, F1, F2, "#5a2a2a", fill=F1 - 0.3)
    step_paint(b, x0, x1, far, -1.0, F2)
    rails(b, WELL, F2, "z-", PANEL)
    # newel posts at the foot of the grand stair
    for x in (x0 - 0.6, x1 + 0.6):
        b.box([x, F1 + 2.2, near - 0.6], [0.8, 4.4, 0.8], PANEL)
        b.sphere([x, F1 + 4.8, near - 0.6], [1.0, 1.0, 1.0], BRASS, material="metal")
    x0, x1, near, far = BACK
    flight(b, "z", near, far, x0, x1, F1, F2, "#6a5a4a", fill=F1 - 0.3)
    rails(b, BACK_WELL, F2, "z-", PANEL)
    x0, x1, near, far = DOWN
    flight(b, "z", near, far, x0, x1, F1, CELLAR, "#6a6058", fill=CELLAR - 0.3)
    rails(b, rect(x0, x1, far, near), F1, "z+", PANEL)


# ===================================================== the rooms, furnished
def _ground_floor(b: ArenaArea) -> None:
    y = F1
    # ---- the library: shelves on every wall, a fireplace, reading chairs,
    # the globe, and the bookcase that is a door (into the billiard room)
    # shelves on the front wall between the windows and along the back wall
    for x, w in ((-66.0, 6.0), (-50.0, 6.0), (-34.0, 6.0)):
        stamp(b, fx.bookcase(w, 9.6, 2.0, WOOD_DARK, seed=int(-x)), x, IZ1 - 1.1, y, 2)
    for x, w in ((-67.5, 5.0), (-53.0, 6.0), (-45.0, 6.0)):
        stamp(b, fx.bookcase(w, 9.6, 2.0, WOOD_DARK, seed=int(-x) + 9), x, ZM + P / 2.0 + 1.1, y, 0)
    # the secret door: a bookcase swung open beside the gap in the shelves
    stamp(b, fx.bookcase(4.0, 9.6, 2.0, WOOD_DARK, seed=5), -32.5, ZM + P / 2.0 + 2.3, y, 1)
    stamp(b, fx.fireplace(9.0, 7.6, 2.4), XW - P / 2.0 - 1.3, 15.0, y, 3)
    stamp(b, fx.painting(5.0, 4.0, "portrait"), XW - P / 2.0 - 0.05, 15.0, y + 7.8, 3)
    stamp(b, fx.rug(16.0, 12.0, "#5a2a3a", border="#c8a040"), -50.0, 10.0, y)
    place(b, "armchair", -46.0, 14.0, y, 1, hide=False)
    place(b, "armchair", -46.0, 6.0, y, 1, hide=False)
    place(b, "globe", -60.0, 4.0, y, 0, hide=False)
    place(b, "side_table", -46.0, 10.0, y, 0, hide=False)
    stamp(b, candelabra(), -46.0, 10.0, y + 2.6)
    stamp(b, fx.table(8.0, 4.0, WOOD_DARK, WOOD_DARK), -58.0, -4.0, y)
    place(b, "book_stack", -59.5, -4.0, y + 3.0, 0, hide=False)
    place(b, "floor_lamp", -36.0, 22.0, y, 0, hide=False)
    hang(b, chandelier(), -50.0, C1, 6.0)
    # ---- the grand hall: the stair, the long clock, suits of armour,
    # portraits, the front door's rug
    place(b, "grandfather_clock", -22.0, ZM + P / 2.0 + 1.0, y, 0, hide=False)
    place(b, "armour", -26.0, 20.0, y, 1, hide=False)
    place(b, "armour", 26.0, 20.0, y, 3, hide=False)
    place(b, "umbrella_stand", 10.0, IZ1 - 1.0, y, 2, hide=False)
    place(b, "potted_plant", -10.0, IZ1 - 1.2, y, 0, hide=False)
    place(b, "potted_plant", 22.0, ZM + P / 2.0 + 1.2, y, 0, hide=False)
    stamp(b, fx.rug(8.0, 6.0, "#7a2a2a", border="#c8a040"), 0.0, 23.4, y)
    stamp(b, fx.table(5.0, 3.0, WOOD_DARK, WOOD_DARK), 18.0, 10.0, y)
    place(b, "vase", 18.0, 10.0, y + 3.0, 0, hide=False)
    for x in (-18.0, 18.0):
        hang(b, chandelier(4.0, 8), x, C1, 4.0)
    # ---- the drawing room: the piano, sofas round the fire, a drinks tray
    stamp(b, fx.fireplace(9.0, 7.6, 2.4), XE + P / 2.0 + 1.3, 16.0, y, 1)
    stamp(b, fx.sofa("#3a6a5a", 10.0, 3.8), 56.0, 22.0, y, 2)
    stamp(b, fx.sofa("#3a6a5a", 10.0, 3.8), 56.0, 6.0, y, 0)
    place(b, "armchair", 48.0, 14.0, y, 1, hide=False)
    stamp(b, fx.table(5.0, 3.0, WOOD_DARK, WOOD_DARK, h=2.0), 56.0, 14.0, y)
    # the grand piano
    stamp(b, [B(0.0, 2.4, 0.0, 6.0, 1.6, 7.0, BLACK), B(0.0, 4.0, -1.0, 6.0, 0.3, 5.0, BLACK),
              B(-2.4, 0.0, 2.6, 0.5, 2.4, 0.5, BLACK), B(2.4, 0.0, 2.6, 0.5, 2.4, 0.5, BLACK),
              B(0.0, 0.0, -3.0, 0.6, 2.4, 0.6, BLACK), B(0.0, 3.0, 3.6, 5.0, 0.3, 0.6, WHITE),
              B(0.0, 1.2, 5.2, 3.0, 1.6, 1.4, WOOD_DARK)], 40.0, -4.0, y, 0)
    stamp(b, fx.rug(14.0, 10.0, "#2a4a5a", border="#c8a040"), 54.0, 14.0, y)
    place(b, "floor_lamp", 66.0, -8.0, y, 0, hide=False)
    place(b, "radio", 34.0, 24.0, y, 2, hide=False)
    hang(b, chandelier(3.0), 52.0, C1, 14.0)
    # ---- the study: the desk, the safe, the map, the gun cabinet (empty)
    stamp(b, fx.table(8.0, 4.0, WOOD_DARK, WOOD_DARK), -56.0, -32.0, y)
    place(b, "dining_chair", -56.0, -35.0, y, 0, hide=False)
    place(b, "book_stack", -54.0, -32.0, y + 3.0, 1, hide=False)
    stamp(b, candelabra(), -59.0, -32.0, y + 3.0)
    stamp(b, [B(0.0, 0.0, 0.0, 4.0, 4.4, 3.0, "#3a3a3a", m="metal"),
              C(0.0, 2.2, 1.6, 1.0, 0.2, 1.0, SILVER_DIAL, r=[1.5708, 0.0, 0.0])],
          IX0 + 2.1, -44.0, y, 1)
    for z, w in ((-28.0, 6.0), (-15.0, 4.0)):
        stamp(b, fx.bookcase(w, 9.6, 2.0, WOOD_DARK, seed=int(-z)), IX0 + 1.1, z, y, 1)
    stamp(b, fx.rug(12.0, 10.0, "#4a2a5a", border="#c8a040"), -56.0, -30.0, y)
    hang(b, fx.pendant(3.0), -56.0, C1, -30.0)
    # ---- the billiard room
    stamp(b, [B(0.0, 0.0, 0.0, 7.0, 2.6, 13.0, WOOD_DARK), B(0.0, 2.6, 0.0, 7.4, 0.4, 13.4, WOOD_DARK),
              B(0.0, 2.62, 0.0, 6.2, 0.42, 12.2, "#2a7a3a")], -28.0, -30.0, y)
    for dx, dz, c in ((-1.0, 3.0, "#c82a2a"), (1.2, -2.0, "#f2c230"), (0.0, 0.0, WHITE),
                      (-1.6, -4.0, "#2a4ac8")):
        stamp(b, [S(0.0, 0.0, 0.0, 0.5, 0.5, 0.5, c)], -28.0 + dx, -30.0 + dz, y + 3.04)
    stamp(b, [B(0.0, 0.0, 0.0, 6.0, 7.0, 1.0, WOOD_DARK)], XB1 + P / 2.0 + 0.6, -40.0, y, 1)
    place(b, "armchair", -18.0, -46.0, y, 3, hide=False)
    place(b, "floor_lamp", -17.0, -20.0, y, 0, hide=False)
    for z in (-36.0, -24.0):
        hang(b, [C(0.0, -2.0, 0.0, 0.1, 2.0, 0.1, BLACK, ghost=True),
                 K(0.0, -3.4, 0.0, 3.0, 1.4, 1.6, "#2a5a3a", ghost=True),
                 S(0.0, -3.6, 0.0, 0.8, 0.5, 0.8, "#ffe2a8", m="neon", ghost=True)], -28.0, C1, z)
    # ---- the back corridor: the way to the conservatory
    place(b, "statuette", -10.0, -44.0, y, 0, hide=False)
    place(b, "statuette", 10.0, -44.0, y, 0, hide=False)
    place(b, "potted_plant", -10.0, -20.0, y, 0, hide=False)
    place(b, "umbrella_stand", 10.0, -20.0, y, 0, hide=False)
    stamp(b, fx.rug(6.0, 24.0, "#7a2a2a", border="#c8a040"), 0.0, -32.0, y)
    hang(b, fx.pendant(2.6), 0.0, C1, -26.0)
    hang(b, fx.pendant(2.6), 0.0, C1, -40.0)
    # ---- the dining room: the long table laid for dinner
    stamp(b, fx.table(8.0, 26.0, WOOD_DARK, WOOD_DARK, cloth=WHITE), 28.0, -31.0, y)
    for z in (-41.0, -36.0, -31.0, -26.0, -21.0):
        place(b, "dining_chair", 22.6, z, y, 1, hide=False)
        place(b, "dining_chair", 33.4, z, y, 3, hide=False)
    for z in (-38.0, -24.0):
        stamp(b, candelabra(), 28.0, z, y + 3.04)
    stamp(b, [B(0.0, 0.0, 0.0, 10.0, 4.0, 2.6, WOOD_DARK), B(0.0, 4.0, 0.0, 10.4, 0.3, 2.8, WOOD)],
          28.0, ZM - P / 2.0 - 1.4, y, 2)
    hang(b, chandelier(2.8, 8), 28.0, C1, -31.0)
    # ---- the kitchen: the range, the dresser, the big table, the stairs
    stamp(b, fx.counter(10.0), 65.3, IZ0 + 1.9, y, 0)
    stamp(b, fx.counter(4.0), 45.0, IZ0 + 1.9, y, 0)
    stamp(b, fx.stove(5.0), 50.0, IZ0 + 1.9, y, 0)
    stamp(b, fx.sink_unit(5.0), 62.0, ZM - P / 2.0 - 1.9, y, 2)
    stamp(b, fx.table(8.0, 5.0, WOOD, WOOD_DARK), 56.0, -30.0, y)
    for x in (53.0, 59.0):
        place(b, "dining_chair", x, -26.4, y, 2, hide=False)
        place(b, "dining_chair", x, -33.6, y, 0, hide=False)
    place(b, "flour_sack", 52.0, -14.6, y, 2, hide=False)
    place(b, "cheese_wheel", 56.0, -30.0, y + 3.0, 0, hide=False)
    place(b, "teapot", 58.0, -29.0, y + 3.0, 1, hide=False)
    for x in (52.0, 60.0):
        strip_light(b, x, -30.0, C1, 6.0, "z", "#fff4d8", 1.0)


SILVER_DIAL = "#c8ccd4"


def _upstairs(b: ArenaArea) -> None:
    y = F2
    # ---- the master bedroom
    stamp(b, fx.bed("#5a2a4a", 7.6, 11.0), -50.0, IZ1 - 6.0, y, 2)
    place(b, "side_table", -56.6, IZ1 - 2.0, y, 2, hide=False)
    place(b, "side_table", -43.4, IZ1 - 2.0, y, 2, hide=False)
    stamp(b, fx.wardrobe(WOOD_DARK, 7.0, 9.0), IX0 + 1.7, 8.0, y, 1)
    stamp(b, fx.dresser(WOOD_DARK, 7.0), -40.0, ZM + P / 2.0 + 1.5, y, 0)
    place(b, "hatbox", -40.0, ZM + P / 2.0 + 1.5, y + 3.6, 0, hide=False)
    place(b, "armchair", -36.0, 18.0, y, 3, hide=False)
    stamp(b, fx.rug(12.0, 9.0, "#4a2a5a", border="#c8a040"), -50.0, 10.0, y)
    hang(b, chandelier(3.0, 6), -50.0, C2, 6.0)
    # ---- the landing: portraits, a seat in the window
    stamp(b, [B(0.0, 0.0, 0.0, 8.0, 1.6, 2.4, PANEL), R(0.0, 1.6, 0.0, 7.6, 0.6, 2.0, "#7a2a2a")],
          0.0, IZ1 - 1.4, y, 2)
    place(b, "grandfather_clock", 24.0, IZ1 - 1.0, y, 2, hide=False)
    place(b, "potted_plant", -24.0, IZ1 - 1.2, y, 0, hide=False)
    place(b, "marble_bust", -24.0, ZM + P / 2.0 + 1.2, y, 0, hide=False)
    hang(b, chandelier(3.0, 6), 16.0, C2, 6.0)
    hang(b, chandelier(3.0, 6), -16.0, C2, 6.0)
    # ---- the nursery: the rocking horse, the toys, a doll's house
    stamp(b, fx.bed("#8ab0d8", 6.0, 9.0), 66.0, IZ1 - 5.0, y, 2)
    place(b, "rocking_horse", 48.0, 10.0, y, 1, hide=False)
    place(b, "teddy_bear", 66.0, 2.0, y, 3, hide=False)
    place(b, "toy_soldier", 40.0, 22.0, y, 2, hide=False)
    place(b, "jack_in_box", 44.0, 0.0, y, 1, hide=False)
    place(b, "toy_drum", 54.0, -6.0, y, 0, hide=False)
    stamp(b, [B(0.0, 0.0, 0.0, 6.0, 5.0, 3.0, "#e8c8a8"), B(0.0, 5.0, 0.0, 6.4, 0.6, 3.4, "#c84a3a"),
              B(-1.4, 1.0, 1.52, 1.4, 1.4, 0.06, "#ffe8a0", m="neon"),
              B(1.4, 1.0, 1.52, 1.4, 1.4, 0.06, "#ffe8a0", m="neon"),
              B(0.0, 3.2, 1.52, 1.4, 1.2, 0.06, "#ffe8a0", m="neon")],
          IX1 - 1.6, 12.0, y, 3)
    stamp(b, fx.rug(10.0, 8.0, "#8ab0d8"), 54.0, 10.0, y)
    hang(b, fx.pendant(2.6), 54.0, C2, 10.0)
    # ---- the guest room
    stamp(b, fx.bed("#4a6a3a", 7.0, 10.0), -50.0, IZ0 + 5.4, y, 0)
    stamp(b, fx.wardrobe(WOOD, 6.0, 8.6), -60.0, ZM - P / 2.0 - 1.6, y, 2)
    place(b, "side_table", -62.4, IZ0 + 1.4, y, 0, hide=False)
    place(b, "laundry_basket", -66.0, -16.0, y, 2, hide=False)
    hang(b, fx.pendant(2.6), -56.0, C2, -30.0)
    # ---- the bathroom
    stamp(b, fx.bathtub(4.6, 9.4), -36.0, IZ0 + 5.0, y, 0)
    stamp(b, fx.toilet(), -20.0, IZ0 + 1.6, y, 0)
    stamp(b, fx.basin(), -24.0, ZM - P / 2.0 - 1.4, y, 2)
    stamp(b, fx.basin(), -32.0, ZM - P / 2.0 - 1.4, y, 2)
    hang(b, fx.pendant(2.4), -28.0, C2, -30.0)
    # ---- the upstairs corridor
    stamp(b, fx.rug(6.0, 24.0, "#7a2a2a", border="#c8a040"), 0.0, -32.0, y)
    place(b, "marble_bust", -10.0, -46.0, y, 0, hide=False)
    place(b, "vase", 10.0, -46.0, y, 0, hide=False)
    hang(b, fx.pendant(2.4), 0.0, C2, -32.0)
    # ---- the portrait gallery: ancestors on both walls, benches
    for z in (-44.0, -22.0, -16.0):
        stamp(b, fx.painting(4.0, 5.0, "portrait"), XB3 + P / 2.0 + 0.05, z, y + 4.0, 1)
    for z in (-36.0, -24.0, -16.0):
        stamp(b, fx.painting(4.0, 5.0, "portrait"), XB4 - P / 2.0 - 0.05, z, y + 4.0, 3)
    place(b, "museum_bench", 28.0, -30.0, y, 1, hide=False)
    place(b, "museum_bench", 28.0, -42.0, y, 1, hide=False)
    place(b, "armour", 28.0, ZM - P / 2.0 - 1.0, y, 2, hide=False)
    for z in (-40.0, -22.0):
        strip_light(b, 28.0, z, C2, 6.0, "x", "#fff4d8", 1.0)
    # ---- the servants' quarters: bunks, a washstand, the back stair
    for z in (-28.0, -20.0):
        stamp(b, fx.bed("#8a8a7a", 5.6, 9.0), 46.9, z, y, 1)
    stamp(b, fx.wardrobe(WOOD, 5.0, 8.0), 46.0, ZM - P / 2.0 - 1.6, y, 2)
    place(b, "laundry_basket", 60.0, -46.0, y, 0, hide=False)
    hang(b, fx.pendant(2.4), 56.0, C2, -30.0)


def _hang_fix(b: ArenaArea) -> None:
    """Pictures on the hall's walls."""
    stamp(b, fx.painting(5.0, 6.0, "portrait"), XW + P / 2.0 + 0.05, -4.0, F1 + 3.6, 1)
    stamp(b, fx.painting(5.0, 6.0, "portrait"), XE - P / 2.0 - 0.05, 18.0, F1 + 3.6, 3)


# ================================================ the cellar, the tunnel, the crypt
def _underground(b: ArenaArea) -> None:
    # the wine cellar under the kitchen: its walls stand in the hole in
    # the lawn, its floor at CELLAR
    x0, x1, z0, z1 = CELLAR_ROOM
    slab(b, rect(x0, x1, z0, z1), CELLAR, 0.6, "#5a5048")
    b.box([x0 - T / 2.0, (CELLAR - 0.6) / 2.0, (z0 + z1) / 2.0], [T, -(CELLAR - 0.6), z1 - z0 + 2 * T],
          STONE_DARK)
    # the east wall, with the tunnel's mouth in it
    _wall_z(b, x1 + T / 2.0, z0 - T, z1 + T, CELLAR - 0.6, 0.0, [(-34.0, -28.0, LOW)])
    b.box([(x0 + x1) / 2.0, (CELLAR - 0.6) / 2.0, z0 - T / 2.0], [x1 - x0, -(CELLAR - 0.6), T],
          STONE_DARK)
    b.box([(x0 + x1) / 2.0, (CELLAR - 0.6) / 2.0, z1 + T / 2.0], [x1 - x0, -(CELLAR - 0.6), T],
          STONE_DARK)
    covering(b, rect(x0, x1, z0, z1), CELLAR, "#6a5e52")
    # wine racks and barrels
    for z in (-46.0, -40.0, -20.0):
        stamp(b, [B(0.0, 0.0, 0.0, 2.4, 7.6, 6.0, WOOD_DARK)] +
              [C(0.0, 0.8 + k * 1.3, dz, 0.9, 0.3, 0.9, "#4a1a2a", r=[0.0, 0.0, 1.5708])
               for k in range(5) for dz in (-1.8, 0.0, 1.8)], IX1 - 1.3, z, CELLAR, 0)
    for x, z in ((54.0, -46.0), (59.0, -46.0), (64.0, -14.6), (56.0, -14.6)):
        stamp(b, [C(0.0, 0.0, 0.0, 3.6, 4.4, 3.6, "#7a4a2a"),
                  C(0.0, 0.9, 0.0, 3.7, 0.3, 3.7, "#3a3a3a", m="metal"),
                  C(0.0, 3.2, 0.0, 3.7, 0.3, 3.7, "#3a3a3a", m="metal")], x, z, CELLAR)
    for x in (52.0, 62.0):
        hang(b, [C(0.0, -1.4, 0.0, 0.1, 1.4, 0.1, BLACK, ghost=True),
                 S(0.0, -1.8, 0.0, 0.7, 0.8, 0.7, "#ffb35a", m="neon", ghost=True)], x, 0.0, -30.0)
    # the tunnel: east under the lawn, then north to the crypt
    ax0, ax1, az0, az1 = TUNNEL_A
    bx0, bx1, bz0, bz1 = TUNNEL_B
    slab(b, rect(ax0, ax1, az0, az1), CELLAR, 0.6, "#5a5048")
    slab(b, rect(ax0 - T, ax0, az0, az1), CELLAR, 0.6, "#5a5048")
    slab(b, rect(bx0, bx1, bz0, bz1), CELLAR, 0.6, "#5a5048")
    h = LOW - (CELLAR - 0.6)
    yc = (LOW + CELLAR - 0.6) / 2.0
    # walls: A's south side, A's north side (to the corner), B's two sides
    b.box([(ax0 + bx0 - T) / 2.0, yc, az1 + T / 2.0], [bx0 - T - ax0, h, T], STONE_DARK)
    b.box([(ax0 + bx1 + T) / 2.0, yc, az0 - T / 2.0], [bx1 + T - ax0, h, T], STONE_DARK)
    b.box([bx0 - T / 2.0, yc, (az1 + T + CRYPT[2] - T) / 2.0], [T, h, CRYPT[2] - T - az1 - T],
          STONE_DARK)
    b.box([bx1 + T / 2.0, yc, (az0 + CRYPT[2] - T) / 2.0], [T, h, CRYPT[2] - T - az0], STONE_DARK)
    # its roof is the lawn's own turf, from the tunnel's ceiling up
    slab(b, rect(ax0, bx0 - T, az0 - T, az1 + T), 0.0, -LOW, LAWN, studs=True, material="grass")
    slab(b, rect(bx0 - T, bx1 + T, az0 - T, CRYPT[2] - T), 0.0, -LOW, LAWN, studs=True,
         material="grass")
    for k in range(6):
        z = -22.0 + k * 13.0
        b.box([bx1 - 0.2, LOW - 1.6, z], [0.3, 1.4, 0.6], "#3a3a3a", material="metal")
        b.box([bx1 - 0.55, LOW - 1.4, z], [0.5, 0.7, 0.5], "#ffb35a", material="neon", collide=False)
    for x in (82.0, 98.0):
        b.box([x, LOW - 1.6, az0 + 0.2], [0.6, 1.4, 0.3], "#3a3a3a", material="metal")
        b.box([x, LOW - 1.4, az0 + 0.55], [0.5, 0.7, 0.5], "#ffb35a", material="neon", collide=False)
    # the crypt: tombs, candles, the stair up into the chapel
    cx0, cx1, cz0, cz1 = CRYPT
    slab(b, rect(cx0, cx1, cz0, cz1), CELLAR, 0.6, "#4a4642")
    _wall_x(b, cz0 - T / 2.0, cx0 - T, cx1 + T, CELLAR - 0.6, 0.0, [(bx0, bx1, LOW)])
    b.box([(cx0 + cx1) / 2.0, (CELLAR - 0.6) / 2.0, cz1 + T / 2.0], [cx1 - cx0 + 2 * T, -(CELLAR - 0.6), T],
          STONE_DARK)
    b.box([cx0 - T / 2.0, (CELLAR - 0.6) / 2.0, (cz0 + cz1) / 2.0], [T, -(CELLAR - 0.6), cz1 - cz0],
          STONE_DARK)
    b.box([cx1 + T / 2.0, (CELLAR - 0.6) / 2.0, (cz0 + cz1) / 2.0], [T, -(CELLAR - 0.6), cz1 - cz0],
          STONE_DARK)
    sx0, sx1, sz0, sz1 = CRYPT_STAIR
    stair_hole = rect(sx0, sx1, sz0, sz1)
    plate(b, carve(rect(cx0, cx1, cz0, cz1), [stair_hole]), F1, F1 - LOW, STONE_DARK)
    flight(b, "x", sx0, sx1, sz0, sz1, CELLAR, F1, STONE, fill=CELLAR - 0.3)
    for x, z in ((110.0, 58.0), (120.0, 58.0), (110.0, 66.0)):
        stamp(b, [B(0.0, 0.0, 0.0, 4.0, 2.6, 7.0, "#8a8478"), B(0.0, 2.6, 0.0, 4.4, 0.4, 7.4, "#a8a49a"),
                  B(0.0, 3.0, 0.0, 1.0, 0.3, 4.0, "#6a6660")], x, z, CELLAR)
    stamp(b, candelabra("#6a6660"), 120.0, 64.0, CELLAR)
    for x in (107.0, 123.0):
        b.box([x, LOW - 1.6, cz0 + 0.2], [0.6, 1.4, 0.3], "#3a3a3a", material="metal")
        b.box([x, LOW - 1.4, cz0 + 0.55], [0.5, 0.7, 0.5], "#ffb35a", material="neon", collide=False)


def _wall_z(b: ArenaArea, at: float, lo: float, hi: float, y0: float, y1: float,
            gaps: List[Tuple[float, float, float]]) -> None:
    from ..kit import wall
    wall(b, "z", at, T, lo, hi, y0, y1, STONE_DARK, gaps=[(a, c, head) for a, c, head in gaps])


def _wall_x(b: ArenaArea, at: float, lo: float, hi: float, y0: float, y1: float,
            gaps: List[Tuple[float, float, float]]) -> None:
    from ..kit import wall
    wall(b, "x", at, T, lo, hi, y0, y1, STONE_DARK, gaps=[(a, c, head) for a, c, head in gaps])


# ============================================================ the conservatory
def _conservatory(b: ArenaArea) -> None:
    x0, x1, z0, z1 = CONSERVATORY
    slab(b, rect(x0, x1, z0, z1), F1, F1, "#e8e4dc")
    covering(b, rect(x0 + 1.0, x1 - 1.0, z0 + 1.0, z1 - 0.1), F1, "#c0663a")
    top = 15.0
    # white posts, glass between them, a door in the north side
    posts_x = [x0 + 0.5, -18.0, -6.0, 6.0, 18.0, x1 - 0.5]
    posts_z = [z0 + 0.5 + k * (z1 - 0.1 - z0 - 1.0) / 4.0 for k in range(5)]
    for x in posts_x:
        b.box([x, (F1 + top) / 2.0, z0 + 0.5], [1.0, top - F1, 1.0], WHITE)
    for z in posts_z[1:]:
        for x in (x0 + 0.5, x1 - 0.5):
            b.box([x, (F1 + top) / 2.0, z], [1.0, top - F1, 1.0], WHITE)
    for a, c in zip(posts_x, posts_x[1:]):
        if a < 0.0 < c:
            # the garden door: glass above it
            b.box([(a + c) / 2.0 - 0.0, (9.4 + top) / 2.0, z0 + 0.5], [c - a - 1.0, top - 9.4, 0.3],
                  "#bfe0e8", material="glass", alpha=0.35)
            b.box([(a + c) / 2.0, 9.2, z0 + 0.5], [c - a - 1.0, 0.4, 0.6], WHITE)
            continue
        b.box([(a + c) / 2.0, (F1 + top) / 2.0, z0 + 0.5], [c - a - 1.0, top - F1, 0.3], "#bfe0e8",
              material="glass", alpha=0.35)
    for a, c in zip(posts_z, posts_z[1:]):
        for x in (x0 + 0.5, x1 - 0.5):
            b.box([x, (F1 + top) / 2.0, (a + c) / 2.0], [0.3, top - F1, c - a - 1.0], "#bfe0e8",
                  material="glass", alpha=0.35)
    slab(b, rect(x0, x1, z0, z1), top + 0.4, 0.4, "#bfe0e8", material="glass", alpha=0.3)
    for x in posts_x[1:-1]:
        b.box([x, top + 0.6, (z0 + z1) / 2.0], [0.6, 0.4, z1 - z0], WHITE, collide=False)
    # palms, ferns, a fountain, wicker chairs
    stamp(b, [C(0.0, 0.0, 0.0, 8.0, 1.6, 8.0, STONE), C(0.0, 1.6, 0.0, 7.0, 0.1, 7.0, "#5ab0d0",
              m="glass"), C(0.0, 1.6, 0.0, 1.0, 3.4, 1.0, STONE), C(0.0, 5.0, 0.0, 3.0, 0.6, 3.0, STONE)],
          0.0, -70.0, F1)
    for x, z in ((-24.0, -80.0), (24.0, -80.0), (-24.0, -58.0), (24.0, -58.0), (-12.0, -82.0),
                 (12.0, -82.0)):
        place(b, "potted_plant" if (x + z) % 2 else "fern", x, z, F1, 0, hide=False)
    for x, q in ((-12.0, 1), (12.0, 3)):
        place(b, "rocking_chair", x, -64.0, F1, q, hide=False)
    place(b, "birdcage", -20.0, -70.0, F1, 0, hide=False)
    place(b, "statuette", 20.0, -70.0, F1, 0, hide=False)


# ================================================================ the grounds
def _grounds(b: ArenaArea, s: Surfaces, rng: random.Random) -> None:
    hx, hz = HALF
    # the drive from the gates to the porch, round the fountain
    s.lay(rect(-10.0, 10.0, Z1 + 8.0, 58.0), 0.12, GRAVEL)
    s.lay(rect(-10.0, 10.0, 94.0, hz), 0.12, GRAVEL)
    s.lay(rect(-26.0, 26.0, 58.0, 94.0), 0.12, GRAVEL)
    stamp(b, [C(0.0, 0.0, 0.0, 18.0, 1.8, 18.0, STONE), C(0.0, 1.8, 0.0, 16.4, 0.1, 16.4, "#4a80a0",
              m="glass"),
              C(0.0, 1.8, 0.0, 2.4, 5.4, 2.4, STONE), C(0.0, 7.2, 0.0, 7.0, 0.8, 7.0, STONE),
              C(0.0, 8.0, 0.0, 1.2, 3.0, 1.2, STONE), S(0.0, 11.0, 0.0, 2.2, 2.2, 2.2, STONE)],
          0.0, 76.0, 0.12)
    car(b, -18.0, 64.0, "z", "#2a2a3a")
    car(b, 18.0, 88.0, "z", "#5a1a1a")
    car(b, -18.0, 88.0, "z", "#2a4a3a")
    for x in (-14.0, 14.0):
        for z in (40.0, 110.0, 140.0):
            lamp_post(b, x, z, 12.0, "#2a2a2a", "#ffd88a")
    # topiary along the front of the house
    for x in (-60.0, -44.0, -28.0, 28.0, 44.0, 60.0):
        stamp(b, [C(0.0, 0.0, 0.0, 3.0, 1.6, 3.0, "#8a6a4a"), S(0.0, 1.6, 0.0, 4.4, 4.4, 4.4, HEDGE),
                  S(0.0, 5.8, 0.0, 3.0, 3.0, 3.0, HEDGE)], x, Z1 + 6.0, 0.0)
    # the gates in the wall
    for x in (-14.0, 14.0):
        b.box([x, 7.0, hz - 2.0], [4.0, 14.0, 4.0], STONE)
        b.sphere([x, 15.0, hz - 2.0], [3.0, 3.0, 3.0], STONE)
    _maze(b, rng)
    _stables(b, s)
    _chapel(b, s, rng)
    _back_garden(b, s, rng)


def _maze(b: ArenaArea, rng: random.Random) -> None:
    """A hedge maze: posts at the grid's corners, hedges between them, cut
    by a fixed seed into a maze with a way in on the east side and a clearing
    with a statue in the middle."""
    x0, x1, z0, z1 = MAZE
    cols, rows = 8, 13
    cw, ch = (x1 - x0) / cols, (z1 - z0) / rows
    hh, t = 8.0, 1.6
    walls = {}
    for i in range(cols):
        for j in range(rows):
            walls[(i, j, "e")] = i < cols - 1
            walls[(i, j, "s")] = j < rows - 1
    seen = {(cols - 1, rows // 2)}
    stack = [(cols - 1, rows // 2)]
    maze_rng = random.Random(7331)
    while stack:
        i, j = stack[-1]
        options = [(i + di, j + dj) for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1))
                   if 0 <= i + di < cols and 0 <= j + dj < rows and (i + di, j + dj) not in seen]
        if not options:
            stack.pop()
            continue
        ni, nj = maze_rng.choice(options)
        if ni != i:
            walls[(min(i, ni), j, "e")] = False
        else:
            walls[(i, min(j, nj), "s")] = False
        seen.add((ni, nj))
        stack.append((ni, nj))
    # the clearing in the middle
    mi, mj = cols // 2 - 1, rows // 2 - 1
    for i in (mi, mi + 1):
        for j in (mj, mj + 1, mj + 2):
            if i == mi:
                walls[(i, j, "e")] = False
            if j < mj + 2:
                walls[(i, j, "s")] = False
    # posts at every corner, hedges between them
    for i in range(cols + 1):
        for j in range(rows + 1):
            b.box([x0 + i * cw, hh / 2.0, z0 + j * ch], [t, hh, t], HEDGE_DARK)
    for i in range(cols + 1):
        for j in range(rows):
            outer = i in (0, cols)
            gate = i == cols and j == rows // 2
            if gate or not (outer or walls.get((i - 1, j, "e"))):
                continue
            b.box([x0 + i * cw, hh / 2.0, z0 + (j + 0.5) * ch], [t, hh, ch - t], HEDGE)
    for j in range(rows + 1):
        for i in range(cols):
            outer = j in (0, rows)
            if not (outer or walls.get((i, j - 1, "s"))):
                continue
            b.box([x0 + (i + 0.5) * cw, hh / 2.0, z0 + j * ch], [cw - t, hh, t], HEDGE)
    cx, cz = x0 + (mi + 1) * cw, z0 + (mj + 1.5) * ch
    stamp(b, [C(0.0, 0.0, 0.0, 4.0, 2.0, 4.0, STONE), B(0.0, 2.0, 0.0, 2.0, 5.0, 2.0, "#a8a49a"),
              S(0.0, 7.6, 0.0, 2.2, 2.4, 2.2, "#a8a49a")], cx, cz, 0.0)
    for dx in (-5.0, 5.0):
        place(b, "museum_bench", cx + dx, cz + 5.0, 0.0, 0, hide=False)


def _stables(b: ArenaArea, s: Surfaces) -> None:
    x0, x1, z0, z1 = STABLES
    s.reserve(STABLES)
    slab(b, rect(x0, x1, z0, z1), 0.5, 0.5, "#6a5a44")
    # the back wall and the ends; stalls open to the south
    b.box([(x0 + x1) / 2.0, 6.0, z0 + 0.6], [x1 - x0, 11.0, 1.2], "#7a4a2a", decal="planks")
    for x in (x0 + 0.6, x1 - 0.6):
        b.box([x, 6.0, (z0 + 1.2 + z1) / 2.0], [1.2, 11.0, z1 - z0 - 1.2], "#7a4a2a")
    for k in range(1, 6):
        x = x0 + k * (x1 - x0) / 6.0
        b.box([x, 3.0, (z0 + 1.2 + z0 + 14.0) / 2.0], [0.6, 5.0, 12.8], "#6a3a1a")
    for k in range(7):
        x = x0 + 0.6 + k * (x1 - x0 - 1.2) / 6.0
        b.box([x, 6.0, z1 - 0.6], [1.0, 11.0, 1.0], "#5a3a1a")
    slab(b, rect(x0 - 1.0, x1 + 1.0, z0 - 1.0, z1 + 1.0), 12.0, 0.6, "#3a2a2a")
    gable(b, rect(x0, x1, z0, z1), 12.0, "#3a2a2a", "x", tiers=4, rise=1.4, overhang=1.0)
    for x in (x0 + 10.5, x0 + 24.5, x1 - 3.5):
        stamp(b, [B(0.0, 0.0, 0.0, 4.0, 2.4, 2.6, "#d8b860"), B(0.0, 2.4, 0.0, 4.0, 2.4, 2.6, "#c8a850")],
              x, z0 + 6.0, 0.5)
    # the carriage
    stamp(b, [B(0.0, 2.0, 0.0, 5.0, 4.0, 8.0, "#2a2a3a"), C(-2.8, 0.0, -2.6, 0.6, 3.6, 3.6, "#5a3a1a",
              r=[0.0, 0.0, 1.5708]), C(2.8, 0.0, -2.6, 0.6, 3.6, 3.6, "#5a3a1a", r=[0.0, 0.0, 1.5708]),
              C(-2.8, 0.0, 2.6, 0.6, 3.6, 3.6, "#5a3a1a", r=[0.0, 0.0, 1.5708]),
              C(2.8, 0.0, 2.6, 0.6, 3.6, 3.6, "#5a3a1a", r=[0.0, 0.0, 1.5708]),
              B(0.0, 6.0, 0.0, 5.4, 0.4, 8.4, "#1a1a2a")], x1 - 16.0, z0 + 22.0, 0.5)
    for x in (x0 + 10.0, x1 - 10.0):
        b.box([x, 10.2, z1 - 0.6], [1.0, 0.6, 1.4], "#3a3a3a", material="metal")
        b.box([x, 9.6, z1 - 0.6], [0.8, 0.7, 0.8], "#ffb35a", material="neon", collide=False)


def _chapel(b: ArenaArea, s: Surfaces, rng: random.Random) -> None:
    x0, x1, z0, z1 = CHAPEL
    s.reserve(CHAPEL)
    wall_top = 14.0
    door = [(112.0, 118.0, 0.0, 9.6)]
    sides = [(58.0, 64.0, 4.0, 11.0), (68.0, 74.0, 4.0, 11.0)]
    openings(b, "z", x0 + T / 2.0, T, z0, z1, 0.0, wall_top, STONE, sides, glass=True)
    openings(b, "z", x1 - T / 2.0, T, z0, z1, 0.0, wall_top, STONE, sides, glass=True)
    openings(b, "x", z0 + T / 2.0, T, x0 + T, x1 - T, 0.0, wall_top, STONE,
             [(112.0, 118.0, 5.0, 12.0)], glass=True)
    openings(b, "x", z1 - T / 2.0, T, x0 + T, x1 - T, 0.0, wall_top, STONE, door, glass=True)
    for x in (x0 + T / 2.0, x1 - T / 2.0):
        for a, c, sill, top in sides:
            window(b, "z", x, T, a, c, sill, top, STONE_DARK, out=1 if x > x0 + 5 else -1)
    slab(b, rect(112.0, 118.0, z1 - T, z1), F1, F1, STONE)
    plate(b, carve(rect(x0 + T, x1 - T, z0 + T, z1 - T), [CRYPT]), F1, F1, STONE)
    slab(b, rect(x0 - 1.0, x1 + 1.0, z0 - 1.0, z1 + 1.0), wall_top + 0.8, 0.8, ROOF)
    gable(b, rect(x0, x1, z0, z1), wall_top + 0.8, ROOF, "z", tiers=6, rise=1.6, overhang=1.0)
    # the bell tower over the door
    b.box([115.0, wall_top + 0.8 + 12.0, z1 - 2.0], [8.0, 24.0, 4.0], STONE)
    b.cone([115.0, wall_top + 0.8 + 29.0, z1 - 2.0], [9.0, 10.0, 5.0], ROOF)
    b.box([115.0, 33.0, z1 + 0.06], [3.0, 3.0, 0.12], "#1a1a1a")
    b.sphere([115.0, 33.0, z1 + 0.2], [1.6, 1.8, 1.0], BRASS, material="metal", collide=False)
    # inside: pews, the altar, the organ, the crypt stair
    for z in (58.0, 62.0, 66.0):
        for x in (106.0, 124.0):
            stamp(b, [B(0.0, 0.0, 0.0, 9.0, 1.6, 1.4, WOOD_DARK), B(0.0, 1.6, -0.6, 9.0, 1.6, 0.3, WOOD_DARK)],
                  x, z, F1, 0)
    stamp(b, [B(0.0, 0.0, 0.0, 8.0, 3.0, 3.0, "#e8e0cc"), B(0.0, 3.0, 0.0, 8.4, 0.2, 3.4, GOLD)],
          115.0, z0 + T + 3.0, F1, 0)
    stamp(b, candelabra(), 112.0, z0 + T + 3.0, F1 + 3.2)
    stamp(b, candelabra(), 118.0, z0 + T + 3.0, F1 + 3.2)
    stamp(b, [B(0.0, 0.0, 0.0, 6.0, 8.0, 2.4, WOOD_DARK)] +
          [C(-2.4 + k * 0.8, 8.0, 0.0, 0.4, 2.0 + (k % 3) * 0.8, 0.4, BRASS, m="metal") for k in range(7)],
          x0 + T + 1.6, 54.0, F1, 1)
    stamp(b, fx.rug(4.0, 12.0, "#7a2a2a", border=GOLD), 115.0, 62.0, F1)
    rails(b, rect(CRYPT_STAIR[0], CRYPT_STAIR[1], CRYPT_STAIR[2], CRYPT_STAIR[3]), F1, "x+", WOOD_DARK)
    for z in (60.0, 72.0):
        hang(b, chandelier(3.0, 6), 115.0, wall_top, z)
    # the graveyard: headstones in rows, an iron fence, a mausoleum
    gx0, gx1, gz1 = 92.0, 160.0, 140.0
    for k in range(int((gx1 - gx0) / 2.0)):
        x = gx0 + 1.0 + k * 2.0
        if 108.0 < x < 122.0:
            continue
        b.box([x, 2.6, gz1], [0.3, 5.2, 0.3], "#2a2a2a", material="metal")
    for j, z in enumerate((94.0, 104.0, 114.0, 124.0, 134.0)):
        for i, x in enumerate((96.0, 102.0, 128.0, 134.0, 140.0)):
            if rng.random() < 0.15:
                continue
            tall = 3.0 + rng.uniform(0.0, 2.2)
            if (i + j) % 3 == 0:
                b.box([x, tall / 2.0, z], [0.6, tall, 0.6], "#8a8a88")
                b.box([x, tall * 0.72, z], [2.4, 0.6, 0.6], "#8a8a88")
            else:
                b.box([x, tall / 2.0, z], [2.6, tall, 0.8], "#9a9a96")
                b.cyl([x, tall, z], [2.6, 0.8, 2.6], "#9a9a96", r=[1.5708, 0.0, 0.0])
            s.lay(rect(x - 1.6, x + 1.6, z + 0.6, z + 4.0), 0.25, "#3a3024")
    # the mausoleum
    mx, mz = 154.0, 116.0
    b.box([mx, 6.0, mz], [12.0, 12.0, 10.0], "#a8a49a")
    b.box([mx, 12.8, mz], [13.4, 1.6, 11.4], "#8a8478")
    b.box([mx - 6.06, 4.6, mz], [0.12, 9.0, 4.0], "#3a3a3a")
    for z in (mz - 3.0, mz + 3.0):
        b.cyl([mx - 7.0, 6.0, z], [1.4, 12.0, 1.4], "#c8c4b8")


def _back_garden(b: ArenaArea, s: Surfaces, rng: random.Random) -> None:
    hx, hz = HALF
    # the path from the conservatory, the gazebo, the pond, the shed
    s.lay(rect(-4.0, 4.0, -132.0, -86.0), 0.12, GRAVEL)
    s.lay(rect(-60.0, 60.0, -112.0, -104.0), 0.12, GRAVEL)
    gx, gz = -60.0, -126.0
    s.reserve(rect(gx - 10.0, gx + 10.0, gz - 10.0, gz + 10.0))
    stamp(b, [C(0.0, 0.0, 0.0, 18.0, 1.2, 18.0, STONE)], gx, gz, 0.0)
    for k in range(8):
        import math
        a = k * math.pi / 4.0
        b.cyl([gx + math.cos(a) * 7.6, 6.2, gz + math.sin(a) * 7.6], [0.8, 10.0, 0.8], WHITE)
    b.cone([gx, 14.2, gz], [20.0, 6.0, 20.0], "#e8e0cc")
    place(b, "museum_bench", gx, gz + 3.0, 1.2, 0, hide=False)
    stamp(b, [C(0.0, 0.0, 0.0, 22.0, 0.6, 22.0, STONE), C(0.0, 0.6, 0.0, 20.0, 0.06, 20.0, "#2a5a7a",
              m="glass")], 50.0, -126.0, 0.0)
    s.reserve(rect(38.0, 62.0, -138.0, -114.0))
    s.reserve(rect(gx - 10.0, gx + 10.0, gz - 10.0, gz + 10.0))
    # rose beds along the path
    for x in (-36.0, -20.0, 20.0, 36.0):
        stamp(b, fx.raised_bed(10.0, 4.0, "#7a2a3a"), x, -98.0, 0.0)
    # the gardener's shed
    sx, sz = 120.0, -126.0
    s.reserve(rect(sx - 9.0, sx + 9.0, sz - 7.0, sz + 7.0))
    b.box([sx, 5.0, sz - 6.4], [18.0, 10.0, 1.2], "#5a4a3a", decal="planks")
    b.box([sx - 8.4, 5.0, sz + 0.6], [1.2, 10.0, 12.8], "#5a4a3a", decal="planks")
    b.box([sx + 8.4, 5.0, sz + 0.6], [1.2, 10.0, 12.8], "#5a4a3a", decal="planks")
    slab(b, rect(sx - 9.6, sx + 9.6, sz - 7.6, sz + 7.6), 10.6, 0.6, "#3a2a2a")
    slab(b, rect(sx - 7.8, sx + 7.8, sz - 5.8, sz + 7.0), 0.4, 0.4, "#5a4a3a")
    place(b, "wheelbarrow", sx - 3.0, sz - 2.0, 0.4, 1, hide=False)
    place(b, "watering_can", sx + 4.0, sz - 3.0, 0.4, 0, hide=False)
    place(b, "flower_pot", sx + 5.0, sz + 3.0, 0.4, 0, hide=False)
    # trees
    for x, z in ((-110.0, -110.0), (-140.0, -130.0), (90.0, -96.0), (150.0, -100.0),
                 (-120.0, 100.0), (-150.0, 130.0), (60.0, 120.0), (80.0, 136.0), (-60.0, 120.0),
                 (-90.0, 134.0), (150.0, 30.0), (-150.0, 70.0)):
        b.cyl([x, 6.0, z], [2.0, 12.0, 2.0], "#3a2a1a")
        b.sphere([x, 15.0, z], [12.0, 10.0, 12.0], "#1e3a22")


# ======================================================================= meta
def _meta(b: ArenaArea) -> None:
    # the guests arrive in the hall, the library and the drawing room
    starts = [(-20.0, 14.0), (-12.0, 22.0), (12.0, 22.0), (20.0, 14.0), (-20.0, 2.0),
              (20.0, 2.0), (-24.0, -6.0), (24.0, -6.0), (-56.0, 20.0), (-40.0, 0.0),
              (-62.0, 12.0), (40.0, 22.0), (64.0, 0.0), (46.0, 8.0), (12.0, 4.0), (-12.0, 4.0)]
    for x, z in starts:
        b.team_spawn("start", x, F1, z, yaw=3.14159)
    g, u = F1, F2
    room(b, "the library", -50.0, g, 10.0, [(-62.0, 20.0), (-38.0, -4.0), (-52.0, -2.0), (-40.0, 20.0)])
    room(b, "the grand hall", -16.0, g, 8.0, [(-24.0, 22.0), (24.0, 24.0), (-10.0, -6.0), (10.0, -8.0)])
    room(b, "the drawing room", 44.0, g, 10.0, [(66.0, 24.0), (36.0, 6.0), (60.0, -8.0)])
    room(b, "the study", -56.0, g, -26.0, [(-62.0, -46.0), (-46.0, -18.0)])
    room(b, "the billiard room", -28.0, g, -40.0, [(-38.0, -16.0), (-18.0, -30.0)])
    room(b, "the back corridor", 0.0, g, -30.0, [(-8.0, -46.0)])
    room(b, "the dining room", 18.0, g, -16.0, [(18.0, -46.0), (38.0, -34.0)])
    room(b, "the kitchen", 58.0, g, -40.0, [(52.0, -22.0), (64.0, -46.0)])
    room(b, "the wine cellar", 58.0, CELLAR, -26.0, [(52.0, -40.0), (66.0, -20.0)])
    room(b, "the tunnel", 115.0, CELLAR, 10.0, [(90.0, -31.0), (115.0, 30.0)])
    room(b, "the crypt", 115.0, CELLAR, 64.0, [(106.0, 56.0)])
    room(b, "the master bedroom", -50.0, u, 2.0, [(-66.0, 22.0), (-36.0, -6.0)])
    room(b, "the landing", -18.0, u, 8.0, [(-20.0, 20.0), (18.0, -6.0), (10.0, 24.0)])
    room(b, "the nursery", 52.0, u, 2.0, [(66.0, -8.0), (36.0, 22.0)])
    room(b, "the guest room", -56.0, u, -30.0, [(-62.0, -36.0)])
    room(b, "the bathroom", -28.0, u, -30.0, [(-18.0, -22.0)])
    room(b, "the upstairs corridor", 0.0, u, -30.0, [(8.0, -18.0)])
    room(b, "the portrait gallery", 22.0, u, -36.0, [(20.0, -18.0), (36.0, -46.0)])
    room(b, "the servants' quarters", 56.0, u, -30.0, [(56.0, -40.0)])
    room(b, "the conservatory", 0.0, F1, -76.0, [(-22.0, -66.0), (22.0, -82.0), (8.0, -58.0)])
    room(b, "the hedge maze", -134.0, 0.0, -4.0,
         [(-158.0, -52.0), (-100.0, 44.0), (-130.0, 20.0), (-112.0, -36.0)])
    room(b, "the drive", 0.0, 0.12, 110.0, [(-30.0, 76.0), (30.0, 62.0), (0.0, 130.0)])
    room(b, "the stables", 143.0, 0.5, -44.0, [(139.5, -60.0), (156.0, -36.0)])
    room(b, "the chapel", 115.0, F1, 66.0, [(104.0, 74.0), (126.0, 56.0)])
    room(b, "the graveyard", 126.0, 0.0, 120.0, [(110.0, 128.0), (156.0, 96.0), (140.0, 130.0)])
    room(b, "the gazebo", -60.0, 1.2, -126.0, [(-60.0, -120.0)])
    room(b, "the pond", 50.0, 0.12, -108.0, [(30.0, -108.0), (56.0, -104.6)])
    room(b, "the garden shed", 120.0, 0.4, -124.0, [(118.0, -130.0)])
    room(b, "the back lawn", -30.0, 0.0, -138.0, [(-100.0, -90.0), (90.0, -140.0), (-120.0, -140.0)])
    # the stairs, for the bots: grand, back, cellar, crypt
    stair(b, (0.0, F1, GRAND[2] + 1.6), (0.0, F2, GRAND[3] - 1.6))
    stair(b, ((BACK[0] + BACK[1]) / 2.0, F1, BACK[2] + 1.6), ((BACK[0] + BACK[1]) / 2.0, F2, BACK[3] - 1.6))
    stair(b, ((DOWN[0] + DOWN[1]) / 2.0, CELLAR, DOWN[3] - 1.6), ((DOWN[0] + DOWN[1]) / 2.0, F1, DOWN[2] + 1.6))
    cx0, cx1, cz0, cz1 = CRYPT_STAIR
    stair(b, (cx0 - 0.4, CELLAR, cz0 - 4.0), (cx1 + 1.6, F1, (cz0 + cz1) / 2.0))
    b.camera(0.0, 60.0, 150.0, 0.0, 8.0, 0.0)
    b.camera(-150.0, 50.0, -140.0, -60.0, 6.0, -60.0)
    b.camera(160.0, 40.0, 140.0, 115.0, 6.0, 70.0)
    b.extra.update({"accent": "#c8a040", "twist": "storm", "twist_every": [32.0, 46.0],
                    "twist_for": 7.0, "round_seconds": 190.0})


def build(b: ArenaArea) -> None:
    rng = random.Random(1888)
    hx, hz = HALF
    cellar_hole = rect(XB4 + P / 2.0 - T, X1, Z0, ZM - P / 2.0 + T)
    tunnel_holes = [rect(X1, TUNNEL_B[0] - T, TUNNEL_A[2] - T, TUNNEL_A[3] + T),
                    rect(TUNNEL_B[0] - T, TUNNEL_B[1] + T, TUNNEL_A[2] - T, CRYPT[2] - T),
                    rect(CRYPT[0] - T, CRYPT[1] + T, CRYPT[2] - T, CRYPT[3] + T)]
    ground(b, LAWN, holes=[cellar_hole] + tunnel_holes)
    s = Surfaces(b)
    s.reserve(rect(X0, X1, Z0, Z1 + 9.0))
    s.reserve(CONSERVATORY)
    s.reserve(MAZE)
    for hole in tunnel_holes:
        s.reserve(hole)
    perimeter(b, 14.0, STONE_DARK)
    backdrop(b, "pines", 0.0, rng, colours=["#1a2a20", "#22342a", "#162418"])
    _shell(b)
    _partitions(b)
    _paint(b)
    _stairs(b)
    _ground_floor(b)
    _hang_fix(b)
    _upstairs(b)
    _underground(b)
    _conservatory(b)
    _grounds(b, s, rng)
    _meta(b)
