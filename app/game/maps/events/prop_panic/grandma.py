"""Grandma's Cottage -- a two-storey cottage on a quiet street, its front
garden full of gnomes, its back garden full of hiding places.

Layout (north is -z; the street is to the south)::

    z -150 ============================ HEDGE ==================================
              compost   SHED          the GREENHOUSE      vegetable   TREEHOUSE
                                      pond            patch (pumpkins)  (oak)
    z  -45   ----------- the patio ---- back doors ---------------------------
             GARAGE  |  conservatory | utility | kitchen                 |
             (the    |  dining room  |  hall + stairs | living room (fire)| chimney
    z   25   hunters)|---------------- porch ----------------------------
             drive   front garden: path, flower beds, gnomes, birdbath, bench
    z   95   ======= picket fence, gate ===================================
             the street: pavement, road, phone box, bins, roadworks
    z  150   ============================ HEDGE ==================================

Upstairs (the same plan): the guest room (the grandchildren's toys), the
landing, Grandma's bedroom; the bathroom, the box room and the sewing
room.  The hunters wait in the garage until its door rolls up (the
``pen`` solid).  Grandma's cat, Mittens, wanders between the ``cat`` marks.
"""
from __future__ import annotations

import random

from ..kit import (ArenaArea, Surfaces, backdrop, car, flight, gable, ground,
                   perimeter, rect, sign_decal, slab, step_paint, strip_light)
from . import catalogue as cat
from . import furniture as fx
from .catalogue import place, stamp
from .rooms import covering, door_holes, grow, interior, openings, partition, skirt, window

HALF = (175.0, 150.0)
SKY = {"top": "#5f9fdc", "horizon": "#dcefff", "sun": [0.45, 0.78, 0.3],
       "clouds": 0.55, "tint": "#fff2dc"}
AMBIENT = "#a8b0bc"
GROUND = "#5c9c48"
FOG = 760.0

LAWN = "#5c9c48"
HEDGE = "#3a7a34"
HEDGE_DARK = "#2e6a2a"
RENDER = "#efe6d2"
TIMBER = "#5a3a24"
ROOF = "#9a4a3a"
BRICK = "#9a4f3a"
PAVING = "#b8b0a0"
GRAVEL = "#c8bca4"
TRIM = "#f4f0e8"
CEILING = "#f4f0e8"

T = 1.2                 # outer walls
F1, C1 = 0.6, 11.0      # ground floor: floor top, ceiling
F2, C2 = 12.0, 21.6     # upstairs (C2: the ceiling's underside)
WALL_TOP = 22.0
ROOF_TOP = 23.0
X0, X1, Z0, Z1 = -60.0, 60.0, -45.0, 25.0
IX0, IX1, IZ0, IZ1 = X0 + T, X1 - T, Z0 + T, Z1 - T

# partitions: (axis, at, lo, hi)
ZM = -5.0               # front rooms / back rooms
XW, XE = -12.0, 12.0    # hall
XB1, XB2 = -24.0, 0.0   # back rooms
P = 0.6

GROUND_DOORS = {
    "zm": [(-45.0, -39.0, 8.4), (-9.6, -3.6, 8.4), (3.6, 9.6, 8.4), (40.0, 46.0, 8.4)],
    "xw": [(-3.4, 1.6, 8.4)], "xe": [(8.0, 14.0, 8.4)],
    "xb1": [(-30.0, -24.0, 8.4)], "xb2": [(-20.0, -14.0, 8.4)],
}
UP_DOORS = {k: [(a, c, F2 + 7.8) for a, c, _ in v] for k, v in GROUND_DOORS.items()}

STAIR = (-11.7, -5.5, 3.0, 21.0)     # x0, x1, top end (z), bottom end (z)
WELL = rect(-11.7, -5.5, 3.0, 22.0)

GARAGE = rect(-106.0, -68.0, -30.0, 12.0)
GARAGE_DOOR = (-100.0, -74.0)
GARAGE_FLOOR = 0.3

GREENHOUSE = rect(-72.0, -40.0, -112.0, -80.0)
SHED = rect(-124.0, -98.0, -134.0, -110.0)
POND = rect(-14.0, 22.0, -124.0, -98.0)
TREE = (94.0, -122.0)
HUT = rect(100.0, 110.0, -128.0, -112.0)
DECK = rect(84.0, 112.0, -132.0, -104.0)
DECK_TOP = 10.0


# ================================================================ the house
def _shell(b: ArenaArea) -> None:
    """The cottage's four outer walls (both storeys), its floors and roof."""
    g_sill, g_top = 3.0, 8.4
    u_sill, u_top = 14.6, 19.6
    big = (1.6, 9.8)
    front = [(-3.0, 3.0, 0.0, 8.6),
             (-50.0, -42.0, g_sill, g_top), (-28.0, -20.0, g_sill, g_top),
             (22.0, 30.0, g_sill, g_top), (42.0, 50.0, g_sill, g_top),
             (-50.0, -42.0, u_sill, u_top), (-28.0, -20.0, u_sill, u_top),
             (-3.0, 3.0, u_sill, u_top), (22.0, 30.0, u_sill, u_top), (42.0, 50.0, u_sill, u_top)]
    back = [(-57.0, -47.0) + big, (-45.0, -39.0, 0.0, 8.6), (-37.0, -27.0) + big,
            (-16.0, -9.0, g_sill, g_top), (8.0, 18.0, g_sill, g_top), (30.0, 36.0, 0.0, 8.6),
            (44.0, 54.0, g_sill, g_top),
            (-50.0, -42.0, u_sill, u_top), (-16.0, -9.0, u_sill, u_top),
            (10.0, 18.0, u_sill, u_top), (42.0, 50.0, u_sill, u_top)]
    west = [(4.0, 12.0, g_sill, g_top), (-38.0, -12.0) + big,
            (4.0, 12.0, u_sill, u_top), (-34.0, -26.0, u_sill, u_top)]
    east = [(-2.0, 3.0, g_sill, g_top), (17.0, 22.0, g_sill, g_top),
            (-38.0, -30.0, g_sill, g_top), (-20.0, -12.0, g_sill, g_top),
            (-3.0, 3.0, u_sill, u_top), (17.0, 22.0, u_sill, u_top),
            (-38.0, -30.0, u_sill, u_top), (-20.0, -12.0, u_sill, u_top)]
    openings(b, "z", X0 + T / 2.0, T, Z0, Z1, 0.0, WALL_TOP, RENDER, west, glass=True)
    openings(b, "z", X1 - T / 2.0, T, Z0, Z1, 0.0, WALL_TOP, RENDER, east, glass=True)
    openings(b, "x", Z0 + T / 2.0, T, IX0, IX1, 0.0, WALL_TOP, RENDER, back, glass=True)
    openings(b, "x", Z1 - T / 2.0, T, IX0, IX1, 0.0, WALL_TOP, RENDER, front, glass=True)
    for a, c, sill, top in front:
        if sill > 0.5:
            window(b, "x", Z1 - T / 2.0, T, a, c, sill, top, TRIM, shutters="#4a7a5a", out=1)
    for a, c, sill, top in back:
        if sill > 0.5:
            window(b, "x", Z0 + T / 2.0, T, a, c, sill, top, TRIM, out=-1)
    for a, c, sill, top in west:
        window(b, "z", X0 + T / 2.0, T, a, c, sill, top, TRIM, out=-1)
    for a, c, sill, top in east:
        window(b, "z", X1 - T / 2.0, T, a, c, sill, top, TRIM, out=1)
    # the timber band at the first floor, all the way round
    slab(b, rect(X0 - 0.25, X1 + 0.25, Z1, Z1 + 0.25), 12.0, 1.0, TIMBER)
    slab(b, rect(X0 - 0.25, X1 + 0.25, Z0 - 0.25, Z0), 12.0, 1.0, TIMBER)
    slab(b, rect(X0 - 0.25, X0, Z0, Z1), 12.0, 1.0, TIMBER)
    slab(b, rect(X1, X1 + 0.25, Z0, Z1), 12.0, 1.0, TIMBER)
    # floors: the ground floor pad, the first floor (with the stairwell),
    # the ceiling under the roof
    slab(b, rect(IX0, IX1, IZ0, IZ1), F1, F1, "#8a6f52")
    for a, c in ((-3.0, 3.0),):
        slab(b, rect(a, c, IZ1, Z1), F1, F1, "#8a6f52")
    slab(b, rect(-45.0, -39.0, Z0, IZ0), F1, F1, "#8a6f52")
    slab(b, rect(30.0, 36.0, Z0, IZ0), F1, F1, "#8a6f52")
    from ..kit import carve, plate
    plate(b, carve(rect(IX0, IX1, IZ0, IZ1), [WELL]), F2, F2 - C1, CEILING)
    slab(b, rect(IX0, IX1, IZ0, IZ1), WALL_TOP, WALL_TOP - C2, CEILING)
    slab(b, rect(X0 - 1.0, X1 + 1.0, Z0 - 1.0, Z1 + 1.0), ROOF_TOP, ROOF_TOP - WALL_TOP, ROOF)
    gable(b, rect(X0, X1, Z0, Z1), ROOF_TOP, ROOF, "x", tiers=5, rise=1.6, overhang=1.0)
    # the chimney, outside the living room's east wall
    b.box([62.0, 17.5, 10.0], [4.0, 35.0, 8.0], BRICK, decal="bricks")
    for dz in (-2.0, 2.0):
        b.cyl([62.0, 35.8, 10.0 + dz], [1.6, 1.6, 1.6], TERRACOTTA)
    # the porch
    slab(b, rect(-8.0, 8.0, Z1, Z1 + 6.0), F1, F1, WOOD_LIGHT)
    for x in (-7.2, 7.2):
        b.box([x, F1 + 4.6, Z1 + 5.2], [1.0, 9.2, 1.0], TRIM)
    slab(b, rect(-9.0, 9.0, Z1, Z1 + 7.0), 10.4, 0.6, ROOF)
    b.box([0.0, 9.0, Z1 + 0.3], [5.0, 1.0, 0.6], TRIM,
          decal=sign_decal("ROSE COTTAGE", TRIM, "#5a3a24", 5.0))


TERRACOTTA = "#c0663a"
WOOD_LIGHT = "#a07a52"
WOOD = "#7a5335"


def _partitions(b: ArenaArea) -> None:
    for y0, y1, doors in ((F1, C1, GROUND_DOORS), (F2, C2, UP_DOORS)):
        partition(b, "x", ZM, IX0, IX1, y0, y1, "#e8dcc8", doors["zm"], trim_colour=TRIM)
        partition(b, "z", XW, ZM + P / 2.0, IZ1, y0, y1, "#e8dcc8", doors["xw"], trim_colour=TRIM)
        partition(b, "z", XE, ZM + P / 2.0, IZ1, y0, y1, "#e8dcc8", doors["xe"], trim_colour=TRIM)
        partition(b, "z", XB1, IZ0, ZM - P / 2.0, y0, y1, "#e8dcc8", doors["xb1"], trim_colour=TRIM)
        partition(b, "z", XB2, IZ0, ZM - P / 2.0, y0, y1, "#e8dcc8", doors["xb2"], trim_colour=TRIM)


def _paint(b: ArenaArea) -> None:
    """Every room's own walls and floor."""
    zf, zb = ZM + P / 2.0, ZM - P / 2.0
    gd, ud = GROUND_DOORS, UP_DOORS
    g_win_front = [(-50.0, -42.0, 3.0, 8.4), (-28.0, -20.0, 3.0, 8.4), (22.0, 30.0, 3.0, 8.4),
                   (42.0, 50.0, 3.0, 8.4)]
    u_win_front = [(-50.0, -42.0, 14.6, 19.6), (-28.0, -20.0, 14.6, 19.6), (-3.0, 3.0, 14.6, 19.6),
                   (22.0, 30.0, 14.6, 19.6), (42.0, 50.0, 14.6, 19.6)]
    g_back = [(-57.0, -47.0, 1.6, 9.8), (-45.0, -39.0, 0.0, 8.6), (-37.0, -27.0, 1.6, 9.8),
              (-16.0, -9.0, 3.0, 8.4), (8.0, 18.0, 3.0, 8.4), (30.0, 36.0, 0.0, 8.6),
              (44.0, 54.0, 3.0, 8.4)]
    u_back = [(-50.0, -42.0, 14.6, 19.6), (-16.0, -9.0, 14.6, 19.6), (10.0, 18.0, 14.6, 19.6),
              (42.0, 50.0, 14.6, 19.6)]
    g_west = [(4.0, 12.0, 3.0, 8.4), (-38.0, -12.0, 1.6, 9.8)]
    u_west = [(4.0, 12.0, 14.6, 19.6), (-34.0, -26.0, 14.6, 19.6)]
    g_east = [(-2.0, 3.0, 3.0, 8.4), (17.0, 22.0, 3.0, 8.4), (-38.0, -30.0, 3.0, 8.4),
              (-20.0, -12.0, 3.0, 8.4)]
    u_east = [(-3.0, 3.0, 14.6, 19.6), (17.0, 22.0, 14.6, 19.6), (-38.0, -30.0, 14.6, 19.6),
              (-20.0, -12.0, 14.6, 19.6)]

    def win(holes, lo, hi):
        return [h for h in holes if h[1] > lo and h[0] < hi]

    def doors(key, which, y0):
        return door_holes(which[key], y0)

    rooms = [
        # name, inner rect, y0, y1, colour, floor, decal, holes
        ("dining", rect(IX0, XW - P / 2.0, zf, IZ1), F1, C1, "#d8c0d0", "#8a5a3a", "planks",
         {"x-": win(g_west, zf, IZ1), "x+": doors("xw", gd, F1),
          "z-": doors("zm", gd, F1), "z+": win(g_win_front, IX0, XW)}),
        ("hall", rect(XW + P / 2.0, XE - P / 2.0, zf, IZ1), F1, C1, "#e8d8b0", "#7a5a3a", "planks",
         {"x-": doors("xw", gd, F1), "x+": doors("xe", gd, F1), "z-": doors("zm", gd, F1),
          "z+": [(-3.5, 3.5, F1 - 1.0, 9.1)]}),
        ("living", rect(XE + P / 2.0, IX1, zf, IZ1), F1, C1, "#c8d8b8", "#8a5a3a", "planks",
         {"x-": doors("xe", gd, F1), "x+": win(g_east, zf, IZ1), "z-": doors("zm", gd, F1),
          "z+": win(g_win_front, XE, IX1)}),
        ("conservatory", rect(IX0, XB1 - P / 2.0, IZ0, zb), F1, C1, "#f0ead8", "#c0663a", "",
         {"x-": win(g_west, IZ0, zb), "x+": doors("xb1", gd, F1), "z-": win(g_back, IX0, XB1),
          "z+": doors("zm", gd, F1)}),
        ("utility", rect(XB1 + P / 2.0, XB2 - P / 2.0, IZ0, zb), F1, C1, "#d8e0e8", "#9aa0a8", "",
         {"x-": doors("xb1", gd, F1), "x+": doors("xb2", gd, F1), "z-": win(g_back, XB1, XB2),
          "z+": doors("zm", gd, F1)}),
        ("kitchen", rect(XB2 + P / 2.0, IX1, IZ0, zb), F1, C1, "#f2e8b8", "#e8e4dc", "tiles",
         {"x-": doors("xb2", gd, F1), "x+": win(g_east, IZ0, zb), "z-": win(g_back, XB2, IX1),
          "z+": doors("zm", gd, F1)}),
        ("guest", rect(IX0, XW - P / 2.0, zf, IZ1), F2, C2, "#b8d8f0", "#5a7aa8", "",
         {"x-": win(u_west, zf, IZ1), "x+": doors("xw", ud, F2), "z-": doors("zm", ud, F2),
          "z+": win(u_win_front, IX0, XW)}),
        ("landing", rect(XW + P / 2.0, XE - P / 2.0, zf, IZ1), F2, C2, "#e8d8b0", "#7a3a3a", "",
         {"x-": doors("xw", ud, F2), "x+": doors("xe", ud, F2), "z-": doors("zm", ud, F2),
          "z+": win(u_win_front, XW, XE)}),
        ("bedroom", rect(XE + P / 2.0, IX1, zf, IZ1), F2, C2, "#e8c8c8", "#a87a6a", "",
         {"x-": doors("xe", ud, F2), "x+": win(u_east, zf, IZ1), "z-": doors("zm", ud, F2),
          "z+": win(u_win_front, XE, IX1)}),
        ("bath", rect(IX0, XB1 - P / 2.0, IZ0, zb), F2, C2, "#c8e8e0", "#e8f0f0", "tiles",
         {"x-": win(u_west, IZ0, zb), "x+": doors("xb1", ud, F2), "z-": win(u_back, IX0, XB1),
          "z+": doors("zm", ud, F2)}),
        ("boxroom", rect(XB1 + P / 2.0, XB2 - P / 2.0, IZ0, zb), F2, C2, "#d8ccb8", "#8a7a6a", "planks",
         {"x-": doors("xb1", ud, F2), "x+": doors("xb2", ud, F2), "z-": win(u_back, XB1, XB2),
          "z+": doors("zm", ud, F2)}),
        ("sewing", rect(XB2 + P / 2.0, IX1, IZ0, zb), F2, C2, "#e0d0f0", "#a89ab8", "",
         {"x-": doors("xb2", ud, F2), "x+": win(u_east, IZ0, zb), "z-": win(u_back, XB2, IX1),
          "z+": doors("zm", ud, F2)}),
    ]
    for name, inner, y0, y1, colour, floor, decal, holes in rooms:
        if name == "landing":
            # the stairwell is not floor: cover round it
            from ..kit import carve
            interior(b, inner, y0, y1, colour, holes)
            for piece in carve(inner, [grow(WELL, 0.1)]):
                covering(b, piece, y0, floor)
            continue
        if name == "hall":
            interior(b, inner, y0, y1, colour, holes)
            from ..kit import carve
            for piece in carve(inner, [grow(rect(STAIR[0], STAIR[1], STAIR[2], STAIR[3]), 0.1)]):
                covering(b, piece, y0, floor, decal)
            continue
        interior(b, inner, y0, y1, colour, holes, floor=floor, floor_decal=decal)


def _stairs(b: ArenaArea) -> None:
    x0, x1, top_z, bottom_z = STAIR
    flight(b, "z", bottom_z, top_z, x0, x1, F1, F2, "#7a5335", fill=F1 - 0.3)
    step_paint(b, x0, x1, top_z, -1.0, F2)
    # the banister round the well, on the landing
    b.box([x1 + 0.2, F2 + 1.6, (WELL[2] + WELL[3] + 0.4) / 2.0],
          [0.4, 3.2, WELL[3] - WELL[2] + 0.4], "#5a3a24")
    b.box([(x0 + x1) / 2.0, F2 + 1.6, WELL[3] + 0.2], [x1 - x0, 3.2, 0.4], "#5a3a24")
    for z in (WELL[2] + 0.4, WELL[3]):
        b.box([x1 + 0.2, F2 + 3.5, z], [0.6, 0.6, 0.6], "#3a2414")


def _lights(b: ArenaArea) -> None:
    for y in (C1, C2):
        for x, z in ((-35.0, 4.0), (-35.0, 16.0), (0.0, 14.0), (0.0, -1.0), (35.0, 4.0),
                     (35.0, 16.0), (-41.0, -24.0), (-12.0, -24.0), (20.0, -24.0), (44.0, -24.0)):
            if WELL[0] - 1.5 < x < WELL[1] + 1.5 and WELL[2] - 1.5 < z < WELL[3] + 1.5:
                continue
            stamp(b, fx.pendant(2.6), x, z, y)


def _house(b: ArenaArea) -> None:
    _shell(b)
    _partitions(b)
    _paint(b)
    _stairs(b)
    _lights(b)
    _furnish(b)


def _furnish(b: ArenaArea) -> None:
    y = F1
    # ---- the living room
    stamp(b, fx.fireplace(), 57.6, 10.0, y, 3)
    stamp(b, fx.rug(10.0, 9.0, "#8a3a3a", "paisley", "#c8a050"), 48.0, 10.0, y)
    place(b, "radio", 57.3, 8.0, y + 6.5, 3)
    place(b, "book_stack", 57.4, 12.6, y + 6.5, 3)
    place(b, "armchair", 47.0, 3.0, y, 1)
    place(b, "armchair", 47.0, 17.0, y, 1)
    stamp(b, fx.sofa("#6a8a5a"), 34.0, 10.0, y, 1)
    stamp(b, fx.table(3.6, 5.2, h=1.8), 41.0, 10.0, y)
    place(b, "teapot", 41.0, 9.0, y + 1.8, 1)
    place(b, "cookie_jar", 41.0, 11.6, y + 1.8)
    place(b, "television", 17.0, 19.0, y, 1)
    place(b, "grandfather_clock", 26.0, -4.0 + 0.6, y)
    place(b, "floor_lamp", 55.6, 1.4, y)
    place(b, "floor_lamp", 55.6, 18.6, y)
    place(b, "potted_plant", 15.0, -2.4, y)
    place(b, "rocking_chair", 30.0, 19.0, y, 2)
    place(b, "footstool", 29.0, 8.0, y)
    place(b, "yarn_basket", 51.0, 21.0, y)
    place(b, "side_table", 51.0, -2.6, y)
    stamp(b, fx.bookcase(6.0, 9.0, 2.0, seed=3), 37.0, IZ1 - 1.0, y, 2)
    stamp(b, fx.painting(6.0, 4.0, "portrait"), 40.0, ZM + P / 2.0, y + 4.4)
    stamp(b, fx.painting(4.0, 3.0, "sunrise"), XE + P / 2.0, 19.0, y + 4.6, 1)
    stamp(b, [cat.R(0.0, 0.0, 0.0, 3.0, 0.6, 2.4, "#c84a5a"),
              cat.R(0.0, 0.6, 0.0, 2.4, 0.3, 1.8, "#f0d0d8")], 54.0, -1.4, y)

    # ---- the hall
    place(b, "umbrella_stand", 6.0, 22.4, y)
    stamp(b, [cat.C(0.0, 0.0, 0.0, 1.4, 0.2, 1.4, "#3a2414"),
              cat.C(0.0, 0.2, 0.0, 0.3, 6.4, 0.3, "#5a3a24"),
              cat.B(0.0, 5.6, 0.0, 1.8, 0.2, 0.2, "#5a3a24"),
              cat.R(0.55, 3.0, 0.0, 0.8, 2.6, 1.0, "#3a4a6a"),
              cat.R(-0.55, 3.4, 0.0, 0.7, 2.2, 0.9, "#8a3a2a")], -4.4, 22.4, y)
    stamp(b, fx.dresser(WOOD, 5.0, 2.0), 10.7, 18.5, y, 3)
    place(b, "radio", 10.6, 18.5, y + 3.6, 3)
    place(b, "potted_plant", 10.6, -3.0, y)
    stamp(b, fx.rug(5.0, 16.0, "#7a2a2a", "", "#c8a050"), 1.0, 12.0, y)
    stamp(b, fx.painting(3.0, 4.0, "flowers"), XE - P / 2.0, 3.0, y + 4.2, 3)

    # ---- the dining room
    stamp(b, fx.rug(20.0, 12.0, "#6a4a6a", "", "#c8a050"), -35.0, 10.0, y)
    stamp(b, fx.table(16.0, 6.0, cloth="#f4f0e8"), -35.0, 10.0, y)
    for x in (-41.0, -35.0, -29.0):
        place(b, "dining_chair", x, 5.0, y, 0)
        place(b, "dining_chair", x, 15.0, y, 2)
    stamp(b, fx.dresser(WOOD_DARK, 10.0, 2.6), -32.0, ZM + P / 2.0 + 1.3, y)
    place(b, "teapot", -35.0, ZM + P / 2.0 + 1.3, y + 3.6)
    place(b, "cookie_jar", -29.0, ZM + P / 2.0 + 1.3, y + 3.6)
    stamp(b, fx.bookcase(6.0, 9.0, 2.0, seed=11), IX0 + 1.0, 18.0, y, 1)
    place(b, "birdcage", -15.0, 21.4, y)
    place(b, "potted_plant", -56.6, -2.4, y)
    place(b, "potted_plant", -14.6, -2.4, y)
    place(b, "floor_lamp", -54.6, 21.8, y)
    stamp(b, fx.painting(8.0, 5.0, "harvest_moon"), XW - P / 2.0, 12.0, y + 4.0, 3)

    # ---- the kitchen
    zc = IZ0 + 1.8
    stamp(b, fx.counter(10.0), 7.0, zc, y)
    stamp(b, fx.sink_unit(5.0), 14.5, zc, y)
    stamp(b, fx.counter(9.0), 21.5, zc, y)
    stamp(b, fx.stove(), 40.0, zc, y)
    stamp(b, fx.counter(12.0), 48.0, zc, y)
    stamp(b, fx.fridge(), IX1 - 2.0, IZ0 + 1.7, y)
    top = y + fx.COUNTER_TOP
    place(b, "toaster", 8.0, zc - 0.4, top)
    place(b, "teapot", 20.0, zc - 0.4, top)
    place(b, "cookie_jar", 46.0, zc - 0.4, top)
    place(b, "radio", 51.0, zc - 0.4, top)
    stamp(b, fx.counter(12.0), 30.0, -21.8, y, 0)
    stamp(b, fx.counter(12.0), 30.0, -25.4, y, 2)
    place(b, "cookie_jar", 27.0, -23.6, top)
    place(b, "toaster", 33.0, -23.6, top)
    stamp(b, fx.table(8.0, 5.0, cloth="#e8f0e0"), 16.0, -18.0, y)
    for x in (13.0, 19.0):
        place(b, "dining_chair", x, -14.0, y, 2)
        place(b, "dining_chair", x, -22.0, y, 0)
    place(b, "teapot", 16.0, -18.0, y + fx.TABLE_TOP)
    place(b, "pedal_bin", 1.6, -12.0, y)
    place(b, "potted_plant", 56.6, -7.6, y)
    stamp(b, fx.painting(2.4, 2.4, "clockface", "#5a3a24"), XB2 + P / 2.0, -32.0, y + 5.4, 1)

    # ---- the utility room
    stamp(b, fx.shelf_unit(10.0, 2, colour="#8a6a4a", metal=False), XB1 + P / 2.0 + 1.2, -36.5,
          y, 1)
    tops = [y + t for t in fx.shelf_tops(2)]
    place(b, "cookie_jar", XB1 + 1.5, -39.0, tops[1], 1)
    place(b, "hatbox", XB1 + 1.5, -34.0, tops[1], 1)
    place(b, "book_stack", XB1 + 1.5, -38.5, tops[2], 1)
    stamp(b, [cat.B(0.0, 0.0, 0.0, 3.6, 3.6, 3.4, "#f4f4f4"),
              cat.C(0.0, 1.0, 1.72, 2.2, 2.2, 0.06, "#9ad0e8", m="glass"),
              cat.B(0.0, 3.0, 1.72, 2.8, 0.4, 0.06, "#c8c8c8")], -4.0, IZ0 + 1.9, y)
    stamp(b, [cat.B(0.0, 0.0, 0.0, 3.6, 3.6, 3.4, "#f4f4f4"),
              cat.C(0.0, 1.0, 1.72, 2.2, 2.2, 0.06, "#3a3a3a", m="glass")], -8.0, IZ0 + 1.9, y)
    place(b, "laundry_basket", -13.0, IZ0 + 1.0, y)
    place(b, "laundry_basket", -17.0, -8.0, y)
    stamp(b, [cat.B(-1.4, 0.0, 0.0, 0.2, 3.0, 0.2, "#c8c8c8"), cat.B(1.4, 0.0, 0.0, 0.2, 3.0, 0.2, "#c8c8c8"),
              cat.B(0.0, 3.0, 0.0, 4.6, 0.2, 1.4, "#a8c8e8")], -12.0, -21.0, y)
    place(b, "umbrella_stand", -2.0, -8.0, y)

    # ---- the conservatory
    stamp(b, fx.table(10.0, 3.0, top="#c8b090", h=2.6), IX0 + 1.6, -29.0, y, 1)
    for z in (-32.5, -29.0, -25.5):
        place(b, "flower_pot", IX0 + 1.6, z, y + 2.6)
    place(b, "potted_plant", -50.0, -41.0, y)
    place(b, "potted_plant", -27.0, -41.0, y)
    place(b, "potted_plant", -27.0, -19.0, y)
    place(b, "rocking_chair", -40.0, -24.0, y, 2)
    place(b, "birdcage", -31.0, -11.0, y)
    place(b, "watering_can", -48.0, -10.0, y, 1)
    place(b, "armchair", -36.0, -34.0, y, 1)

    y = F2
    # ---- the landing
    stamp(b, fx.dresser(WOOD, 3.6, 2.0), 0.0, ZM + P / 2.0 + 1.0, y)
    place(b, "laundry_basket", 9.6, 21.8, y)
    place(b, "potted_plant", 10.6, -3.0, y)
    place(b, "rocking_horse", 5.0, 14.0, y)
    stamp(b, fx.bench(5.0, "#c8a8b8"), 0.0, IZ1 - 1.2, y, 2)
    stamp(b, fx.painting(4.0, 3.0, "sp_rainbow"), XE - P / 2.0, 4.0, y + 4.4, 3)

    # ---- Grandma's bedroom
    stamp(b, fx.bed("#c86a7a", 8.0, 11.0), IX1 - 5.5, 10.0, y, 3)
    place(b, "side_table", IX1 - 1.2, 3.0, y)
    place(b, "side_table", IX1 - 1.2, 17.0, y)
    stamp(b, fx.wardrobe(WOOD_DARK), 30.0, ZM + P / 2.0 + 1.5, y)
    stamp(b, fx.dresser(WOOD, 6.0, 2.6), 20.0, ZM + P / 2.0 + 1.3, y)
    place(b, "hatbox", 18.6, ZM + P / 2.0 + 1.3, y + 3.6)
    place(b, "book_stack", 21.8, ZM + P / 2.0 + 1.3, y + 3.6)
    place(b, "armchair", 19.0, 18.0, y, 1)
    place(b, "rocking_chair", 40.0, 20.0, y, 2)
    place(b, "yarn_basket", 24.0, 20.6, y)
    place(b, "floor_lamp", 14.6, 21.6, y)
    place(b, "hatbox", 37.0, -2.6, y)
    stamp(b, fx.rug(12.0, 9.0, "#e8c0c8", "rosebuds", "#a85a6a"), 40.0, 10.0, y)
    stamp(b, fx.painting(5.0, 3.0, "flowers"), IX1, 10.0, y + 5.4, 3)

    # ---- the guest room: the grandchildren's toys
    stamp(b, fx.bed("#5a8ad8", 5.0, 9.0), IX0 + 4.5, -0.6, y, 1)
    stamp(b, fx.bed("#d85a5a", 5.0, 9.0), IX0 + 4.5, 16.0, y, 1)
    stamp(b, fx.wardrobe("#8a6a4a"), -36.0, IZ1 - 1.5, y, 2)
    place(b, "teddy_bear", -30.0, 19.0, y, 2)
    place(b, "toy_block", -22.0, 2.0, y)
    place(b, "toy_block_b", -20.2, 2.0, y)
    place(b, "toy_block_c", -21.1, 2.0, y + 1.8)
    place(b, "rocking_horse", -40.0, 8.0, y, 1)
    place(b, "toy_drum", -16.0, 19.0, y)
    place(b, "jack_in_box", -46.0, 21.6, y)
    place(b, "beach_ball", -26.0, 11.0, y)
    stamp(b, fx.rug(12.0, 10.0, "#f2c230", "", "#3aa04a"), -32.0, 9.0, y)

    # ---- the sewing room
    stamp(b, fx.table(8.0, 4.0), 30.0, -38.0, y)
    stamp(b, [cat.B(0.0, 0.0, 0.0, 2.4, 1.0, 1.2, "#2a2a2a"),
              cat.B(-0.9, 1.0, 0.0, 0.5, 1.2, 0.8, "#2a2a2a"),
              cat.B(0.0, 2.2, 0.0, 2.4, 0.5, 0.8, "#2a2a2a"),
              cat.C(0.9, 1.0, 0.0, 0.2, 0.9, 0.2, SILVER)], 30.0, -38.4, y + fx.TABLE_TOP)
    stamp(b, [cat.C(0.0, 0.0, 0.0, 1.6, 0.2, 1.6, "#3a2414"),
              cat.C(0.0, 0.2, 0.0, 0.2, 3.4, 0.2, "#3a2414"),
              cat.R(0.0, 3.6, 0.0, 1.8, 2.6, 1.2, "#e8c0a0"),
              cat.R(0.0, 3.8, 0.0, 1.9, 1.4, 1.3, "#8a4a8a")], 45.0, -30.0, y)
    stamp(b, fx.shelf_unit(10.0, 2, colour="#8a6a4a", metal=False), XB2 + P / 2.0 + 1.2, -35.0,
          y, 1)
    tops = [y + t for t in fx.shelf_tops(2)]
    place(b, "hatbox", 1.5, -38.0, tops[1], 1)
    place(b, "yarn_basket", 1.5, -33.0, tops[1], 1)
    place(b, "book_stack", 1.5, -36.0, tops[2], 1)
    place(b, "yarn_basket", 20.0, -40.0, y)
    place(b, "yarn_basket", 52.0, -20.0, y)
    place(b, "hatbox", 12.0, -41.6, y)
    place(b, "armchair", 50.0, -10.0, y, 2)
    place(b, "floor_lamp", 56.6, -41.6, y)
    place(b, "laundry_basket", 14.0, -10.0, y)
    place(b, "footstool", 40.0, -14.0, y)
    stamp(b, fx.rug(10.0, 8.0, "#b8a8d8", "knit"), 30.0, -24.0, y)

    # ---- the bathroom
    stamp(b, fx.bathtub(), -52.0, IZ0 + 2.2, y, 1)
    stamp(b, fx.toilet(), -28.0, IZ0 + 1.5, y)
    stamp(b, fx.basin(), -36.0, IZ0 + 1.2, y)
    place(b, "laundry_basket", -27.0, -10.0, y)
    place(b, "potted_plant", -56.6, -7.6, y)
    place(b, "pedal_bin", -32.0, IZ0 + 0.8, y)
    stamp(b, [cat.B(-1.6, 0.0, 0.0, 0.2, 4.0, 0.2, SILVER), cat.B(1.6, 0.0, 0.0, 0.2, 4.0, 0.2, SILVER),
              cat.B(0.0, 3.4, 0.0, 3.4, 0.2, 0.2, SILVER),
              cat.B(0.0, 1.6, 0.0, 2.6, 1.9, 0.3, "#7ac8e8")], -52.0, -7.0, y, 2)

    # ---- the box room
    stamp(b, [cat.B(0.0, 0.0, 0.0, 3.6, 3.6, 3.6, "#c8a070", dec="crate_logo")], -21.4, -41.4, y)
    stamp(b, [cat.B(0.0, 0.0, 0.0, 3.6, 3.6, 3.6, "#b89060")], -21.4, -37.6, y)
    stamp(b, [cat.B(0.0, 0.0, 0.0, 3.0, 3.0, 3.0, "#d8b080")], -21.4, -41.2, y + 3.6)
    stamp(b, [cat.R(0.0, 0.0, 0.0, 4.0, 1.2, 2.6, "#6a3a2a"),
              cat.R(0.1, 1.2, 0.0, 3.6, 1.1, 2.4, "#3a5a6a")], -2.6, -40.0, y)
    place(b, "television", -12.0, IZ0 + 1.2, y)
    place(b, "radio", -15.0, -30.0, y)
    place(b, "hatbox", -6.0, -30.0, y)
    place(b, "book_stack", -9.0, -28.0, y)
    place(b, "book_stack", -21.4, -37.6, y + 3.6)
    place(b, "rocking_chair", -5.0, -20.0, y, 3)
    place(b, "floor_lamp", -2.0, -8.0, y)
    place(b, "umbrella_stand", -21.6, -8.0, y)


SILVER = "#b8bcc2"
WOOD_DARK = "#543923"


# ================================================================ the garage
def _garage(b: ArenaArea) -> None:
    x0, x1, z0, z1 = GARAGE
    a, c = GARAGE_DOOR
    openings(b, "z", x0 + T / 2.0, T, z0, z1, 0.0, 12.0, BRICK)
    openings(b, "z", x1 - T / 2.0, T, z0, z1, 0.0, 12.0, BRICK)
    openings(b, "x", z0 + T / 2.0, T, x0 + T, x1 - T, 0.0, 12.0, BRICK)
    openings(b, "x", z1 - T / 2.0, T, x0 + T, x1 - T, 0.0, 12.0, BRICK, [(a, c, 0.0, 10.4)])
    slab(b, rect(x0 - 0.6, x1 + 0.6, z0 - 0.6, z1 + 0.6), 13.0, 1.0, "#5a5a5a")
    slab(b, rect(x0 + T, x1 - T, z0 + T, z1 - T), GARAGE_FLOOR, GARAGE_FLOOR, "#8a8a88")
    slab(b, rect(a, c, z1 - T, z1), GARAGE_FLOOR, GARAGE_FLOOR, "#8a8a88")
    interior(b, rect(x0 + T, x1 - T, z0 + T, z1 - T), GARAGE_FLOOR, 12.0, "#c8c8c0",
             {"z+": [(a, c, -1.0, 10.4)]})
    for x in (x0 + 10.0, x1 - 10.0):
        strip_light(b, x, (z0 + z1) / 2.0, 12.0, 24.0, "z")
    car(b, x0 + 9.0, -14.0, "z", colour="#3a6a9a", y=GARAGE_FLOOR)
    stamp(b, fx.counter(14.0, body="#6a5a4a", top="#4a3a2a", doors="#7a6a5a"),
          -86.0, z0 + T + 1.8, GARAGE_FLOOR)
    stamp(b, fx.shelf_unit(10.0, 2, colour="#5a6a7a"), x1 - T - 1.2, -12.0, GARAGE_FLOOR, 3)
    for k, z in enumerate((-15.5, -12.0, -8.5)):
        place(b, "paint_can", x1 - T - 1.3, z, GARAGE_FLOOR + 3.7, 3, hide=False)
    stamp(b, [cat.B(0.0, 0.0, 0.0, 8.0, 5.0, 0.3, "#8a6a4a", dec="planks")], -88.0, z0 + T + 0.15,
          GARAGE_FLOOR + 4.0)
    b.box([(a + c) / 2.0, 11.2, z1 - T - 0.5], [c - a, 1.6, 1.0], "#7a7a7a", material="metal")
    b.box([(a + c) / 2.0, 11.2, z1 + 0.15], [12.0, 1.2, 0.3], "#f2b01e",
          decal=sign_decal("HUNTERS WAIT HERE", "#f2b01e", "#1b2a35", 10.0))
    # the door that holds them: rolled down until the hunt starts
    with b.detached() as parts:
        b.box([(a + c) / 2.0, (GARAGE_FLOOR + 10.4) / 2.0, z1 - T / 2.0],
              [c - a, 10.4 - GARAGE_FLOOR, 0.6], "#d8d4c8", material="metal",
              decal="panels")
    b.dynamic("pen", parts, on=False, group="pen")


# ============================================================ the gardens
def _front_garden(b: ArenaArea, s: Surfaces) -> None:
    s.lay(rect(-4.0, 4.0, Z1 + 6.0, 95.0), 0.15, PAVING)
    s.lay(rect(GARAGE_DOOR[0], GARAGE_DOOR[1], GARAGE[3], 95.0), 0.12, GRAVEL)
    for z0, z1 in ((38.0, 58.0), (66.0, 88.0)):
        for x in (-7.5, 7.5):
            stamp(b, fx.raised_bed(3.0, z1 - z0, "#d85a8a"), x, (z0 + z1) / 2.0, 0.0, 0)
    place(b, "birdbath", 30.0, 60.0)
    for x, z, q in ((-30.0, 45.0, 0), (40.0, 40.0, 3), (55.0, 75.0, 2), (-45.0, 80.0, 1),
                    (18.0, 88.0, 2), (-20.0, 70.0, 0), (-60.0, 40.0, 1)):
        place(b, "garden_gnome", x, z, 0.0, q)
    place(b, "wheelbarrow", -55.0, 60.0, 0.0, 1)
    place(b, "flower_pot", -6.0, Z1 + 8.0)
    place(b, "flower_pot", 6.0, Z1 + 8.0)
    place(b, "watering_can", 12.0, Z1 + 7.0, 0.0, 3)
    stamp(b, fx.bench(6.0), 46.0, 90.0, 0.0, 2)
    b.tree(62.0, 55.0, 0.0, 1.25, leaf_c="#3a8a3a")
    b.tree(-36.0, 62.0, 0.0, 1.1, leaf_c="#4a9a3a")
    b.tree(110.0, 40.0, 0.0, 1.4, leaf_c="#3a8a3a")
    for x in (-130.0, 130.0):
        stamp(b, fx.hedge(10.0, 5.0, 30.0, HEDGE), x, 60.0)
    place(b, "garden_gnome", 100.0, 70.0, 0.0, 3)
    place(b, "flower_pot", 120.0, 85.0)
    place(b, "birdbath", -140.0, 30.0)
    # the picket fence along the street, with the gate and the drive open
    spans = [(-HALF[0], GARAGE_DOOR[0] - 2.0), (GARAGE_DOOR[1] + 2.0, -4.0), (4.0, HALF[0])]
    for a, c in spans:
        b.box([(a + c) / 2.0, 1.2, 95.3], [c - a, 0.3, 0.3], TRIM)
        b.box([(a + c) / 2.0, 2.6, 95.3], [c - a, 0.3, 0.3], TRIM)
        n = int((c - a) // 1.6)
        for k in range(n + 1):
            x = a + 0.25 + (c - a - 0.5) * k / max(1, n)
            b.box([x, 1.7, 94.95], [0.5, 3.4, 0.4], TRIM)
    for x in (-4.6, 4.6):
        b.box([x, 2.2, 95.0], [1.0, 4.4, 1.0], TRIM)
        b.sphere([x, 4.8, 95.0], [1.0, 0.8, 1.0], TRIM)


def _street(b: ArenaArea, s: Surfaces) -> None:
    s.lay(rect(-HALF[0], HALF[0], 96.0, 104.0), 0.3, "#a8a8a0")
    s.lay(rect(-HALF[0], HALF[0], 104.0, 128.0), 0.1, "#4a4e54")
    s.lay(rect(-HALF[0], HALF[0], 128.0, 136.0), 0.3, "#a8a8a0")
    for x in range(-160, 170, 24):
        b.box([x, 0.11, 116.0], [10.0, 0.02, 0.6], "#e8e8e0", collide=False)
    for x in (-120.0, -40.0, 40.0, 120.0):
        stamp(b, fx.lamp_stand(12.0), x, 102.6, 0.3)
    car(b, 70.0, 109.0, "x", colour="#c8a03a", y=0.1)
    car(b, -70.0, 123.0, "x", colour="#8a3a6a", y=0.1)
    # a red phone box you can step into
    px, pz = -30.0, 100.0
    b.box([px - 2.3, 4.6, pz], [0.4, 8.6, 4.6], "#c82a2a")
    b.box([px + 2.3, 4.6, pz], [0.4, 8.6, 4.6], "#c82a2a")
    b.box([px, 4.6, pz - 2.1], [4.2, 8.6, 0.4], "#c82a2a")
    b.box([px, 9.2, pz], [5.2, 0.6, 5.2], "#c82a2a",
          decal=sign_decal("TELEPHONE", "#1b1b1b", "#ffffff", 4.0))
    b.box([px, 0.35, pz + 0.2], [4.2, 0.1, 3.8], "#5a5a5a")
    b.box([px - 1.2, 4.6, pz - 1.6], [1.2, 1.6, 0.6], "#2a2a2a")
    place(b, "bin", 20.0, 99.6, 0.3)
    place(b, "bin", 22.0, 99.6, 0.3)
    place(b, "bin", -88.0, 99.6, 0.3)
    place(b, "traffic_cone", 100.0, 113.0, 0.1)
    place(b, "traffic_cone", 104.0, 110.0, 0.1)
    place(b, "traffic_cone", 108.0, 114.0, 0.1)
    b.box([104.0, 0.12, 112.0], [6.0, 0.04, 4.0], "#2a2a2a", collide=False)
    from ..kit import barrier
    barrier(b, 112.0, 112.0, 8.0, "z")
    # the bus stop over the road
    stamp(b, [cat.B(-3.2, 0.0, 0.0, 0.3, 8.0, 0.3, SILVER), cat.B(3.2, 0.0, 0.0, 0.3, 8.0, 0.3, SILVER),
              cat.B(0.0, 0.0, -1.2, 6.1, 8.0, 0.2, "#cfe8ff", m="glass", a=0.4),
              cat.B(0.0, 8.0, -0.3, 7.2, 0.4, 3.0, "#3a6a3a")], 120.0, 133.2, 0.3)
    stamp(b, fx.bench(5.0), 120.0, 133.0, 0.3)
    b.box([127.0, 5.3, 129.0], [0.4, 10.0, 0.4], SILVER, material="metal")
    b.box([127.0, 10.6, 129.0], [3.0, 2.0, 0.3], "#3a6aaa", decal=sign_decal("BUS", "#3a6aaa", "#ffffff"))
    stamp(b, [cat.C(0.0, 0.0, 0.0, 1.6, 3.6, 1.6, "#c82a2a"), cat.S(0.0, 3.2, 0.0, 1.6, 0.9, 1.6, "#c82a2a"),
              cat.B(0.0, 2.4, 0.78, 0.9, 0.2, 0.1, "#1b1b1b")], 8.0, 99.2, 0.3)
    # the neighbours' hedges over the road
    for a, c in ((-HALF[0], -60.0), (-50.0, 50.0), (60.0, HALF[0])):
        stamp(b, fx.hedge(c - a, 6.0, 5.0, HEDGE), (a + c) / 2.0, 139.0)


def _back_garden(b: ArenaArea, s: Surfaces) -> None:
    s.lay(rect(-32.0, 32.0, -62.0, Z0), 0.15, PAVING)
    s.lay(rect(-4.0, 4.0, -96.0, -62.0), 0.15, PAVING)
    s.lay(rect(-96.0, -32.0, -68.0, -62.0), 0.15, PAVING)
    s.lay(rect(-60.0, -52.0, -80.0, -68.0), 0.15, PAVING)
    s.lay(rect(-104.0, -96.0, -110.0, -68.0), 0.15, PAVING)
    # the patio set
    stamp(b, fx.table(6.0, 6.0, top="#e8e8e8", legs="#c8c8c8"), 0.0, -53.0, 0.15)
    stamp(b, [cat.C(0.0, 3.0, 0.0, 0.3, 5.0, 0.3, "#c8c8c8"),
              cat.K(0.0, 8.0, 0.0, 9.0, 2.0, 9.0, "#d85a5a", ghost=True)], 0.0, -53.0, 0.15)
    for x, z, q in ((0.0, -48.6, 2), (0.0, -57.4, 0), (-4.4, -53.0, 1), (4.4, -53.0, 3)):
        place(b, "dining_chair", x, z, 0.15, q)
    place(b, "flower_pot", -30.0, -47.0, 0.15)
    place(b, "flower_pot", 30.0, -47.0, 0.15)
    place(b, "potted_plant", -24.0, -60.0, 0.15)
    # the washing line
    for x in (40.0, 90.0):
        b.box([x, 5.5, -66.0], [0.6, 11.0, 0.6], "#c8c8c8", material="metal")
    b.box([65.0, 10.6, -66.0], [49.4, 0.12, 0.12], "#e8e8e8")
    for x, c in ((50.0, "#f4f4f4"), (58.0, "#c8d8f0"), (66.0, "#f0c8d0"), (74.0, "#f4f4f4"),
                 (82.0, "#d8f0c8")):
        b.box([x, 8.2, -66.0], [5.0, 4.6, 0.12], c, decal="linen")
    place(b, "laundry_basket", 62.0, -70.0)
    # the vegetable patch
    for k in range(3):
        for j in range(2):
            x, z = 30.0 + j * 24.0, -82.0 - k * 14.0
            stamp(b, fx.raised_bed(16.0, 5.0, "#5a9a3a"), x, z)
    place(b, "pumpkin", 22.0, -82.0, 1.66)
    place(b, "pumpkin", 60.0, -96.0, 1.66)
    place(b, "pumpkin", 34.0, -110.0, 1.66)
    place(b, "pumpkin", 42.0, -89.0)
    place(b, "pumpkin", 48.0, -103.0)
    place(b, "watering_can", 66.0, -88.0, 0.0, 2)
    place(b, "wheelbarrow", 70.0, -110.0, 0.0, 0)
    stamp(b, [cat.B(0.0, 0.0, 0.0, 0.4, 7.0, 0.4, "#6a4a2a"),
              cat.B(0.0, 5.0, 0.0, 5.0, 0.4, 0.4, "#6a4a2a"),
              cat.R(0.0, 3.0, 0.0, 2.2, 3.0, 1.2, "#5a6aa8"),
              cat.S(0.0, 6.0, 0.0, 1.6, 1.6, 1.6, "#d8b878"),
              cat.C(0.0, 7.4, 0.0, 2.6, 0.2, 2.6, "#c8a050"),
              cat.C(0.0, 7.6, 0.0, 1.4, 0.8, 1.4, "#c8a050")], 42.0, -96.0, 0.0)
    _greenhouse(b)
    _shed(b)
    _pond(b)
    _treehouse(b)
    # swings, the birdhouse, compost and the apple trees
    for x in (-8.0, 8.0):
        b.box([60.0 + x, 6.0, -140.0], [0.5, 12.0, 0.5], "#c84a3a", material="metal")
    b.box([60.0, 12.25, -140.0], [16.5, 0.5, 0.5], "#c84a3a", material="metal")
    for x in (-3.0, 3.0):
        b.box([60.0 + x, 7.0, -140.0], [0.1, 10.0, 0.1], "#8a8a8a", collide=False)
        b.box([60.0 + x, 1.8, -140.0], [2.0, 0.3, 1.0], "#3a3a3a")
    stamp(b, [cat.B(0.0, 0.0, 0.0, 0.4, 7.0, 0.4, "#6a4a2a"),
              cat.B(0.0, 7.0, 0.0, 2.0, 1.8, 2.0, "#c8a070"),
              cat.B(0.0, 7.6, 1.02, 0.6, 0.6, 0.04, "#2a1a10"),
              cat.B(0.0, 8.8, 0.0, 2.6, 0.4, 2.6, "#9a4a3a")], -24.0, -78.0)
    for x in (-150.0, -142.0):
        b.box([x, 2.4, -140.0], [7.0, 4.8, 7.0], "#6a4a2a", decal="planks")
    for x, z, sc in ((-120.0, -72.0, 1.2), (132.0, -70.0, 1.3), (-148.0, -104.0, 1.1),
                     (30.0, -138.0, 1.0), (140.0, -136.0, 1.2)):
        b.tree(x, z, 0.0, sc, leaf_c="#3a8a3a")
    place(b, "birdbath", 120.0, -90.0)
    place(b, "garden_gnome", -10.0, -94.0, 0.0, 0)
    place(b, "garden_gnome", 24.0, -96.0, 0.0, 3)
    place(b, "garden_gnome", 26.0, -126.0, 0.0, 2)
    place(b, "flower_pot", -140.0, -60.0)
    stamp(b, fx.bench(6.0), 4.0, -130.0, 0.0, 0)


def _greenhouse(b: ArenaArea) -> None:
    x0, x1, z0, z1 = GREENHOUSE
    t = 0.6
    sides = {
        "x-": [(z0 + 2.0, z1 - 2.0, 1.0, 8.4)],
        "x+": [(z0 + 2.0, z1 - 2.0, 1.0, 8.4)],
        "z-": [(x0 + 2.0, x1 - 2.0, 1.0, 8.4)],
        "z+": [(x0 + 2.0, -58.5, 1.0, 8.4), (-58.0, -52.0, 0.0, 8.0), (-51.5, x1 - 2.0, 1.0, 8.4)],
    }
    openings(b, "z", x0 + t / 2.0, t, z0, z1, 0.0, 9.0, WHITE, sides["x-"], glass=True)
    openings(b, "z", x1 - t / 2.0, t, z0, z1, 0.0, 9.0, WHITE, sides["x+"], glass=True)
    openings(b, "x", z0 + t / 2.0, t, x0 + t, x1 - t, 0.0, 9.0, WHITE, sides["z-"], glass=True)
    openings(b, "x", z1 - t / 2.0, t, x0 + t, x1 - t, 0.0, 9.0, WHITE, sides["z+"], glass=True)
    b.box([(x0 + x1) / 2.0, 9.2, (z0 + z1) / 2.0], [x1 - x0, 0.4, z1 - z0], "#cfe8ff",
          material="glass", alpha=0.35)
    for x in (x0 + 8.0, x1 - 8.0):
        b.box([x, 9.6, (z0 + z1) / 2.0], [0.4, 0.4, z1 - z0], WHITE)
    slab(b, rect(x0 + t, x1 - t, z0 + t, z1 - t), 0.2, 0.2, "#a8a090")
    slab(b, rect(-58.0, -52.0, z1 - t, z1), 0.2, 0.2, "#a8a090")
    for x in (x0 + 2.4, x1 - 2.4):
        stamp(b, fx.table(22.0, 3.0, top="#a07a52", h=2.6), x, (z0 + z1) / 2.0, 0.2, 1)
    for z in (-106.0, -101.0, -96.0, -91.0, -86.0):
        place(b, "flower_pot", x0 + 2.4, z, 2.8)
    for z in (-104.0, -94.0, -84.0):
        place(b, "potted_plant", x1 - 2.4, z, 2.8)
    place(b, "watering_can", -56.0, -100.0, 0.2, 1)
    place(b, "potted_plant", -56.0, -90.0, 0.2)
    place(b, "flower_pot", -50.0, -108.0, 0.2)


WHITE = "#f2f0ea"


def _shed(b: ArenaArea) -> None:
    x0, x1, z0, z1 = SHED
    t = 0.8
    openings(b, "z", x0 + t / 2.0, t, z0, z1, 0.0, 9.0, "#6a4a2a")
    openings(b, "z", x1 - t / 2.0, t, z0, z1, 0.0, 9.0, "#6a4a2a",
               [(-125.0, -119.0, 0.0, 7.8), (-131.0, -128.0, 3.6, 6.4)], glass=True)
    openings(b, "x", z0 + t / 2.0, t, x0 + t, x1 - t, 0.0, 9.0, "#6a4a2a")
    openings(b, "x", z1 - t / 2.0, t, x0 + t, x1 - t, 0.0, 9.0, "#6a4a2a",
               [(-114.0, -108.0, 3.6, 6.4)], glass=True)
    slab(b, rect(x0 - 0.8, x1 + 0.8, z0 - 0.8, z1 + 0.8), 9.8, 0.8, "#3a4a3a")
    gable(b, rect(x0, x1, z0, z1), 9.8, "#3a4a3a", "x", tiers=3, rise=1.0, overhang=0.8)
    slab(b, rect(x0 + t, x1 - t, z0 + t, z1 - t), 0.3, 0.3, "#8a6a4a")
    slab(b, rect(x1 - t, x1, -125.0, -119.0), 0.3, 0.3, "#8a6a4a")
    stamp(b, fx.shelf_unit(10.0, 2, colour="#8a6a4a", metal=False), -116.0, z0 + t + 1.2, 0.3)
    tops = [0.3 + v for v in fx.shelf_tops(2)]
    place(b, "flower_pot", -119.0, z0 + t + 1.2, tops[1])
    place(b, "watering_can", -114.0, z0 + t + 1.2, tops[1])
    place(b, "garden_gnome", -117.0, z0 + t + 1.2, tops[2])
    place(b, "wheelbarrow", -120.0, -114.0, 0.3, 1)
    place(b, "garden_gnome", -102.0, -130.0, 0.3, 3)
    stamp(b, [cat.B(0.0, 0.0, 0.0, 2.6, 1.6, 3.2, "#3a8a3a"),
              cat.B(0.0, 1.6, -1.4, 0.2, 2.6, 0.2, "#2a2a2a"),
              cat.B(0.0, 4.2, -1.4, 2.0, 0.2, 0.2, "#2a2a2a")], -106.0, -116.0, 0.3)
    for k, z in enumerate((-130.0, -127.0, -124.0)):
        b.box([x0 + t + 0.15, 5.0, z], [0.3, 3.0 + k * 0.4, 0.2], "#5a5a5a")


def _pond(b: ArenaArea) -> None:
    x0, x1, z0, z1 = POND
    t = 1.2
    from ..kit import room_walls
    room_walls(b, POND, t, 0.0, 1.4, "#8a8a80")
    slab(b, rect(x0 + t, x1 - t, z0 + t, z1 - t), 0.3, 0.3, "#4a4a3a")
    b.box([(x0 + x1) / 2.0, 0.9, (z0 + z1) / 2.0], [x1 - x0 - 2 * t, 1.0, z1 - z0 - 2 * t],
          "#4a8ab8", collide=False, material="glass", alpha=0.7)
    for x, z in ((-6.0, -104.0), (8.0, -116.0), (14.0, -106.0)):
        b.cyl([x, 1.42, z], [2.0, 0.04, 2.0], "#4a8a3a", collide=False)
    b.box([4.0, 2.0, -97.4], [8.0, 1.2, 1.2], "#8a8a80")


def _treehouse(b: ArenaArea) -> None:
    tx, tz = TREE
    x0, x1, z0, z1 = DECK
    b.cyl([tx, 13.0, tz], [5.0, 26.0, 5.0], "#6a4a2a")
    b.sphere([tx, 32.0, tz], [30.0, 18.0, 30.0], "#3a8a3a", collide=False)
    b.sphere([tx + 12.0, 27.0, tz + 10.0], [16.0, 10.0, 16.0], "#4a9a3a", collide=False)
    slab(b, DECK, DECK_TOP, 0.6, "#8a6a4a")
    for x in (x0 + 0.6, x1 - 0.6):
        for z in (z0 + 0.6, z1 - 0.6):
            b.box([x, (DECK_TOP - 0.6) / 2.0, z], [1.0, DECK_TOP - 0.6, 1.0], "#6a4a2a")
    # the rail round the deck, open where the stairs arrive (x0, z -112..-106)
    rail = DECK_TOP + 1.2
    b.box([(x0 + x1) / 2.0, rail, z0 + 0.2], [x1 - x0, 2.4, 0.4], "#6a4a2a")
    b.box([(x0 + x1) / 2.0, rail, z1 - 0.2], [x1 - x0, 2.4, 0.4], "#6a4a2a")
    b.box([x1 - 0.2, rail, (z0 + z1) / 2.0], [0.4, 2.4, z1 - z0 - 0.8], "#6a4a2a")
    b.box([x0 + 0.2, rail, (z0 + 0.4 - 112.0) / 2.0], [0.4, 2.4, -112.0 - (z0 + 0.4)], "#6a4a2a")
    b.box([x0 + 0.2, rail, (-106.0 + z1 - 0.4) / 2.0], [0.4, 2.4, (z1 - 0.4) + 106.0], "#6a4a2a")
    flight(b, "x", 70.0, x0, -112.0, -106.0, 0.0, DECK_TOP, "#8a6a4a", fill=-0.3)
    # the hut
    hx0, hx1, hz0, hz1 = HUT
    top = DECK_TOP + 8.0
    openings(b, "z", hx0 + 0.4, 0.8, hz0, hz1, DECK_TOP, top, "#a07a52",
               [(-123.0, -117.0, DECK_TOP - 1.0, DECK_TOP + 6.6)])
    openings(b, "z", hx1 - 0.4, 0.8, hz0, hz1, DECK_TOP, top, "#a07a52",
               [(-123.0, -117.0, DECK_TOP + 3.0, DECK_TOP + 6.0)], glass=True)
    openings(b, "x", hz0 + 0.4, 0.8, hx0 + 0.8, hx1 - 0.8, DECK_TOP, top, "#a07a52")
    openings(b, "x", hz1 - 0.4, 0.8, hx0 + 0.8, hx1 - 0.8, DECK_TOP, top, "#a07a52",
               [(102.0, 108.0, DECK_TOP + 3.0, DECK_TOP + 6.0)], glass=True)
    slab(b, rect(hx0 - 0.8, hx1 + 0.8, hz0 - 0.8, hz1 + 0.8), top + 0.8, 0.8, "#3a6a3a")
    gable(b, rect(hx0, hx1, hz0, hz1), top + 0.8, "#3a6a3a", "z", tiers=3, rise=1.0,
          overhang=0.8)
    from ..kit import wall_sign
    wall_sign(b, hx0 - 0.35, DECK_TOP + 7.2, -120.0, 5.0, 1.0,
              sign_decal("NO GROWN-UPS", "#f2c230", "#c82a2a", 5.0), "x-", "#f2c230")
    place(b, "teddy_bear", 107.0, -125.6, DECK_TOP, 3)
    place(b, "book_stack", 102.4, -126.4, DECK_TOP)
    place(b, "radio", 107.4, -113.6, DECK_TOP, 2)
    place(b, "toy_block", 102.6, -113.8, DECK_TOP)


# ======================================================== more garden
def _ring(b: ArenaArea, area, height: float, colour: str, t: float = 0.8,
          gap: str = "", span=(0.0, 0.0)) -> None:
    """A low square wall round ``area`` (a sandpit, a pool, a well)."""
    from ..kit import room_walls
    doors = {gap: [(span[0], span[1], -1.0)]} if gap else None
    room_walls(b, area, t, 0.0, height, colour, doors=doors)


def _summerhouse(b: ArenaArea, area, door_side: str, colour: str, roof: str) -> None:
    """A little wooden house with a door and windows, its floor a step up."""
    x0, x1, z0, z1 = area
    t = 0.8
    top = 9.0
    mx, mz = (x0 + x1) / 2.0, (z0 + z1) / 2.0
    holes = {"x-": [(mz - 3.0, mz + 3.0, 3.0, 6.4)], "x+": [(mz - 3.0, mz + 3.0, 3.0, 6.4)],
             "z-": [(mx - 3.0, mx + 3.0, 3.0, 6.4)], "z+": [(mx - 3.0, mx + 3.0, 3.0, 6.4)]}
    door = (mx - 3.0, mx + 3.0) if door_side in ("z-", "z+") else (mz - 3.0, mz + 3.0)
    holes[door_side] = [(door[0], door[1], -1.0, 7.6)]
    openings(b, "z", x0 + t / 2.0, t, z0, z1, 0.0, top, colour, holes["x-"], glass=True)
    openings(b, "z", x1 - t / 2.0, t, z0, z1, 0.0, top, colour, holes["x+"], glass=True)
    openings(b, "x", z0 + t / 2.0, t, x0 + t, x1 - t, 0.0, top, colour, holes["z-"], glass=True)
    openings(b, "x", z1 - t / 2.0, t, x0 + t, x1 - t, 0.0, top, colour, holes["z+"], glass=True)
    slab(b, rect(x0 + t, x1 - t, z0 + t, z1 - t), 0.6, 0.6, "#a07a52")
    if door_side == "z+":
        slab(b, rect(door[0], door[1], z1 - t, z1), 0.6, 0.6, "#a07a52")
    elif door_side == "z-":
        slab(b, rect(door[0], door[1], z0, z0 + t), 0.6, 0.6, "#a07a52")
    elif door_side == "x-":
        slab(b, rect(x0, x0 + t, door[0], door[1]), 0.6, 0.6, "#a07a52")
    else:
        slab(b, rect(x1 - t, x1, door[0], door[1]), 0.6, 0.6, "#a07a52")
    slab(b, rect(x0 - 0.8, x1 + 0.8, z0 - 0.8, z1 + 0.8), top + 0.8, 0.8, roof)
    gable(b, area, top + 0.8, roof, "x" if x1 - x0 >= z1 - z0 else "z", tiers=3, rise=1.0,
          overhang=0.8)
    strip_light(b, mx, mz, top, min(x1 - x0, z1 - z0) - 6.0, "x")


def _extras(b: ArenaArea, s: Surfaces) -> None:
    # ---- the front lawns: a sandpit, a paddling pool, a wishing well,
    # a rose arch over the path, the summerhouse and Grandma's car
    _ring(b, rect(-52.0, -38.0, 30.0, 44.0), 1.0, "#a07a52")
    slab(b, rect(-51.2, -38.8, 30.8, 43.2), 0.8, 0.8, "#e8d8a0")
    stamp(b, [cat.C(0.0, 0.0, 0.0, 1.0, 1.0, 1.0, "#d83a3a"),
              cat.B(0.0, 1.0, 0.0, 1.1, 0.08, 0.08, "#d83a3a")], -47.0, 34.0, 0.8)
    stamp(b, [cat.B(0.0, 0.0, 0.0, 0.3, 0.1, 2.6, "#3a6ad0"),
              cat.B(0.0, 0.0, 1.5, 0.9, 0.1, 0.8, "#3a6ad0")], -42.0, 39.0, 0.8)
    place(b, "beach_ball", -44.0, 34.0, 0.8)
    place(b, "toy_block_b", -40.6, 41.6, 0.8)
    _ring(b, rect(-150.0, -138.0, 60.0, 72.0), 1.2, "#3a8ad8", t=0.6)
    slab(b, rect(-149.4, -138.6, 60.6, 71.4), 0.2, 0.2, "#e8f0f8")
    b.box([-144.0, 0.7, 66.0], [10.8, 0.8, 10.8], "#6ac0f0", collide=False, material="glass",
          alpha=0.6)
    place(b, "rubber_duck", -142.0, 68.0, 0.2)
    _ring(b, rect(-118.0, -112.0, 74.0, 80.0), 2.4, "#8a8a80")
    slab(b, rect(-117.2, -112.8, 74.8, 79.2), 0.3, 0.3, "#2a3a4a")
    for x in (-117.6, -112.4):
        b.box([x, 4.6, 77.0], [0.4, 4.4, 0.4], "#6a4a2a")
    b.box([-115.0, 7.0, 77.0], [5.6, 0.4, 0.4], "#6a4a2a")
    for i in range(3):
        b.box([-115.0, 7.2 + 0.4 * i + 0.2, 77.0], [7.0 - 1.8 * i, 0.4, 3.6 - 0.9 * i], "#9a4a3a")
    b.box([-115.0, 5.6, 77.0], [0.06, 2.8, 0.06], "#8a8a8a", collide=False)
    b.cyl([-115.0, 3.8, 77.0], [0.8, 0.8, 0.8], "#6a4a2a")
    for x in (-4.7, 4.7):
        b.box([x, 4.5, 62.0], [0.5, 9.0, 0.5], TRIM)
    b.box([0.0, 9.25, 62.0], [9.9, 0.5, 0.8], TRIM)
    for x in (-4.0, -1.5, 1.5, 4.0):
        b.sphere([x, 10.0, 62.0], [2.4, 1.6, 1.6], "#3a8a3a", collide=False)
        b.sphere([x + 0.4, 10.6, 62.3], [0.6, 0.6, 0.6], "#e84a6a", collide=False)
    _summerhouse(b, rect(112.0, 132.0, 30.0, 46.0), "z+", "#e8d8b8", "#5a7a5a")
    place(b, "rocking_chair", 116.0, 34.0, 0.6, 1)
    place(b, "book_stack", 128.0, 33.0, 0.6)
    place(b, "side_table", 127.6, 41.0, 0.6)
    place(b, "potted_plant", 115.0, 42.6, 0.6)
    place(b, "birdcage", 122.0, 32.2, 0.6)
    car(b, -95.0, 78.0, "z", colour="#7ab0c8", y=0.12)

    # ---- the back lawns: the gazebo, a trampoline, the orchard, the hens
    slab(b, rect(118.0, 142.0, -72.0, -48.0), 1.2, 1.2, "#a07a52")
    for x in (118.6, 141.4):
        for z in (-71.4, -48.6):
            b.box([x, 5.4, z], [0.8, 8.4, 0.8], TRIM)
    slab(b, rect(117.0, 143.0, -73.0, -47.0), 10.2, 0.6, "#5a7a5a")
    gable(b, rect(118.0, 142.0, -72.0, -48.0), 10.2, "#5a7a5a", "x", tiers=3, rise=1.0,
          overhang=1.0)
    stamp(b, fx.bench(10.0, "#e8e8e8", "#e8e8e8"), 130.0, -70.0, 1.2, 0)
    stamp(b, fx.bench(10.0, "#e8e8e8", "#e8e8e8"), 130.0, -50.0, 1.2, 2)
    stamp(b, fx.table(5.0, 4.0, top="#f4f0e8", legs="#c8c8c8", cloth="#f0c8d0"), 130.0, -60.0, 1.2)
    place(b, "teapot", 129.0, -60.0, 1.2 + fx.TABLE_TOP)
    place(b, "cookie_jar", 131.4, -59.6, 1.2 + fx.TABLE_TOP)
    place(b, "potted_plant", 121.0, -51.0, 1.2)
    place(b, "potted_plant", 139.0, -69.0, 1.2)
    b.cyl([150.0, 1.4, -112.0], [14.0, 2.8, 14.0], "#3a6ad0")
    b.cyl([150.0, 2.84, -112.0], [12.4, 0.08, 12.4], "#1b1d20")
    for x, z in ((112.0, -92.0), (132.0, -92.0), (152.0, -84.0), (112.0, -134.0),
                 (132.0, -138.0), (156.0, -138.0)):
        b.tree(x, z, 0.0, 0.9, leaf_c="#4a9a3a")
        for dx, dz in ((-1.6, 1.2), (1.4, -0.8)):
            b.sphere([x + dx * 2.0, 0.3, z + dz * 2.0], [0.6, 0.6, 0.6], "#d83a2a",
                     collide=False)
    for x, z in ((122.0, -100.0), (124.0, -100.0)):
        b.box([x, 1.0, z], [1.9, 2.0, 1.9], "#a07a52", decal="planks")
    place(b, "wheelbarrow", 140.0, -100.0, 0.0, 3)
    place(b, "pumpkin", 127.0, -104.0)
    # the hen house, up on legs, with a ramp and a run round it
    hx0, hx1, hz0, hz1 = -162.0, -146.0, -96.0, -84.0
    for x in (hx0 + 0.5, hx1 - 0.5):
        for z in (hz0 + 0.5, hz1 - 0.5):
            b.box([x, 1.0, z], [0.8, 2.0, 0.8], "#6a4a2a")
    slab(b, rect(hx0, hx1, hz0, hz1), 2.4, 0.4, "#8a6a4a")
    openings(b, "z", hx0 + 0.3, 0.6, hz0, hz1, 2.4, 8.4, "#c84a3a")
    openings(b, "z", hx1 - 0.3, 0.6, hz0, hz1, 2.4, 8.4, "#c84a3a",
             [(-92.0, -88.0, 2.4, 7.4)])
    openings(b, "x", hz0 + 0.3, 0.6, hx0 + 0.6, hx1 - 0.6, 2.4, 8.4, "#c84a3a")
    openings(b, "x", hz1 - 0.3, 0.6, hx0 + 0.6, hx1 - 0.6, 2.4, 8.4, "#c84a3a",
             [(-155.0, -152.0, 4.4, 6.6)], glass=True)
    slab(b, rect(hx0 - 0.6, hx1 + 0.6, hz0 - 0.6, hz1 + 0.6), 9.0, 0.6, "#3a3a3a")
    flight(b, "x", hx1 + 5.0, hx1, -92.0, -88.0, 0.0, 2.4, "#8a6a4a", fill=-0.3)
    for z in (-94.0, -90.0, -86.0):
        b.box([hx0 + 1.4, 3.6, z], [2.0, 2.4, 3.2], "#a07a52")
        b.box([hx0 + 2.42, 3.4, z], [0.04, 1.2, 2.4], "#e8d080", collide=False)
    run = rect(-172.0, -136.0, -108.0, -76.0)
    rx0, rx1, rz0, rz1 = run
    for a_, c_, z in ((rx0, rx1, rz0), (rx0, rx1, rz1)):
        b.box([(a_ + c_) / 2.0, 1.5, z], [c_ - a_, 3.0, 0.2], "#c8c8c8", decal="netting")
    b.box([rx0, 1.5, (rz0 + rz1) / 2.0], [0.2, 3.0, rz1 - rz0 - 0.2], "#c8c8c8", decal="netting")
    b.box([rx1, 1.5, (rz0 + rz1) / 2.0 + 6.0], [0.2, 3.0, rz1 - rz0 - 12.2], "#c8c8c8",
          decal="netting")
    for x, z in ((-158.0, -102.0), (-150.0, -100.0), (-142.0, -104.0), (-166.0, -80.0)):
        stamp(b, [cat.S(0.0, 0.0, 0.0, 1.2, 1.1, 1.6, "#f4f0e8"),
                  cat.S(0.0, 0.8, 0.6, 0.7, 0.7, 0.7, "#f4f0e8"),
                  cat.B(0.0, 1.4, 0.6, 0.14, 0.3, 0.4, "#d83a2a"),
                  cat.B(0.0, 1.0, 1.0, 0.2, 0.16, 0.26, "#f2b01e")], x, z)
    place(b, "watering_can", -140.0, -80.0, 0.0, 0)
    for k in range(4):
        b.box([-160.0, 0.7 + k * 1.4, -125.0], [8.0 - k * 1.6, 1.4, 4.0], "#8a5a3a",
              decal="planks")


# ============================================================ the edges
def _edges(b: ArenaArea, rng: random.Random) -> None:
    perimeter(b, 20.0, HEDGE, cap=HEDGE_DARK, rng=rng, ragged=3.0)
    skirt(b, HALF[0], HALF[1], "#4a8a3a")
    backdrop(b, "hills", -6.0, rng, colours=["#4a8a3a", "#5a9a4a", "#3a7a34"],
             sides=("x-", "x+", "z-"), depth=80.0)
    # the houses over the road
    for k, x in enumerate(range(-150, 170, 46)):
        z = HALF[1] + 60.0 + (k % 2) * 8.0
        colour = ["#efe6d2", "#e8d0c0", "#d8e0e8", "#f0e0c0"][k % 4]
        b.box([x, 9.0, z], [30.0, 18.0, 22.0], colour, collide=False)
        for i in range(4):
            b.box([x, 18.0 + 1.6 * i + 0.8, z], [30.0 - 6.0 * i, 1.6, 22.0 - 4.8 * i],
                  "#8a4a3a", collide=False)
        for wx in (-8.0, 8.0):
            b.box([x + wx, 11.0, z - 11.05], [5.0, 4.0, 0.1], "#cfe8ff", collide=False,
                  material="glass")


# ================================================================ the meta
def _on(b: ArenaArea, level: float, x: float, z: float) -> float:
    """The floor at (x, z) on the storey whose floor is ``level``."""
    return b.surface(x, z, level + 1.0)


def _meta(b: ArenaArea) -> None:
    # hiders start in the front garden; hunters in the garage
    for x, z in ((-14.0, 44.0), (14.0, 44.0), (-14.0, 62.0), (14.0, 62.0), (-14.0, 80.0),
                 (14.0, 80.0), (-26.0, 52.0), (26.0, 52.0), (-26.0, 72.0), (26.0, 72.0),
                 (-30.0, 36.0), (38.0, 32.0), (-2.0, 91.0), (48.0, 62.0), (-48.0, 70.0),
                 (60.0, 84.0)):
        b.team_spawn("props", x, None, z, yaw=3.14159)
    for x in (-96.0, -91.0, -86.0, -81.0, -76.0):
        for z in (2.0, 7.0):
            b.team_spawn("hunters", x, GARAGE_FLOOR, z, yaw=0.0)
    for x, z in ((-79.0, -18.0), (-79.0, -10.0)):
        b.team_spawn("hunters", x, GARAGE_FLOOR, z, yaw=0.0)
    b.mark("pen", -87.0, GARAGE_FLOOR, 0.0, r=16.0)

    hides = [
        (F1, 40.0, -1.0), (F1, 52.0, 6.0), (F1, 20.0, 12.0), (F1, 28.0, 14.0),
        (F1, 4.0, 4.0), (F1, -24.0, 1.0), (F1, -48.0, 18.0), (F1, -20.0, 19.0),
        (F1, 10.0, -10.0), (F1, 44.0, -16.0), (F1, 24.0, -32.0), (F1, -10.0, -14.0),
        (F1, -18.0, -36.0), (F1, -34.0, -16.0), (F1, -50.0, -36.0),
        (F2, 24.0, 14.0), (F2, 44.0, 2.0), (F2, -24.0, 6.0), (F2, -42.0, 18.0),
        (F2, 6.0, 6.0), (F2, 16.0, -30.0), (F2, 46.0, -36.0), (F2, -34.0, -30.0),
        (F2, -10.0, -36.0), (F2, -4.0, -16.0),
        (0.0, -24.0, 40.0), (0.0, 40.0, 70.0), (0.0, -60.0, 84.0), (0.0, 30.0, 84.0),
        (0.2, -6.0, -50.0), (0.0, 20.0, -90.0), (0.0, 64.0, -104.0), (0.2, -48.0, -96.0),
        (0.3, -110.0, -120.0), (DECK_TOP, 90.0, -108.0), (DECK_TOP, 105.0, -119.0),
        (0.0, -120.0, -60.0), (0.0, 130.0, -100.0), (0.3, 16.0, 100.0), (0.1, 110.0, 119.0),
        (0.0, -140.0, 40.0), (0.0, 120.0, 70.0), (0.0, -150.0, 145.0), (0.0, 150.0, 145.0),
    ]
    for level, x, z in hides:
        b.mark("hide", x, _on(b, level, x, z), z)
    searches = [
        (F1, 40.0, 2.0, "the living room"), (F1, 2.0, 10.0, "the hall"),
        (F1, -35.0, 1.0, "the dining room"), (F1, 30.0, -12.0, "the kitchen"),
        (F1, -12.0, -28.0, "the utility room"), (F1, -40.0, -18.0, "the conservatory"),
        (F2, 3.0, 10.0, "the landing"), (F2, 36.0, 2.0, "Grandma's bedroom"),
        (F2, -30.0, 4.0, "the grandchildren's room"), (F2, 25.0, -26.0, "the sewing room"),
        (F2, -40.0, -20.0, "the bathroom"), (F2, -12.0, -26.0, "the box room"),
        (0.0, 40.0, 60.0, "the front garden"), (0.0, -40.0, 60.0, "the gnome lawn"),
        (0.1, 0.0, 116.0, "the street"), (0.2, 10.0, -58.0, "the patio"),
        (0.0, 50.0, -89.0, "the vegetable patch"), (0.2, -56.0, -96.0, "the greenhouse"),
        (0.3, -110.0, -124.0, "the shed"), (0.0, 4.0, -134.0, "the pond"),
        (DECK_TOP, 98.0, -108.0, "the treehouse"),
    ]
    for level, x, z, name in searches:
        b.mark("search", x, _on(b, level, x, z), z, name=name)
        b.landmark(x, z, name)
    for level, x, z in ((F1, 52.0, 5.0), (F1, 30.0, -10.0), (F1, -40.0, -14.0),
                        (F1, -30.0, 1.0), (F2, 3.0, 12.0), (F2, 30.0, 2.0), (0.0, 20.0, 40.0),
                        (0.2, 12.0, -58.0), (0.0, 40.0, -75.0), (0.0, -30.0, -90.0)):
        b.mark("cat", x, _on(b, level, x, z), z)
    b.landmark(-87.0, 0.0, "the garage")
    b.camera(0.0, 60.0, 135.0, 0.0, 8.0, 0.0)
    b.camera(150.0, 55.0, -130.0, 0.0, 8.0, -40.0)
    b.camera(-150.0, 45.0, 90.0, -40.0, 5.0, 20.0)
    # two storeys of rooms and a big garden take a while to search
    b.extra.update({"accent": "#e85a7a", "twist": "cat", "pen_key": "pen", "round_seconds": 250.0})


def build(b: ArenaArea) -> None:
    rng = random.Random(1907)
    ground(b, LAWN)
    s = Surfaces(b)
    s.reserve(rect(X0 - 1.0, X1 + 1.0, Z0 - 1.0, Z1 + 7.0))
    s.reserve(GARAGE)
    s.reserve(GREENHOUSE)
    s.reserve(SHED)
    s.reserve(POND)
    s.reserve(rect(60.0, 64.0, 6.0, 14.0))
    for area in (rect(-52.0, -38.0, 30.0, 44.0), rect(-150.0, -138.0, 60.0, 72.0),
                 rect(-118.0, -112.0, 74.0, 80.0), rect(112.0, 132.0, 30.0, 46.0),
                 rect(118.0, 142.0, -72.0, -48.0)):
        s.reserve(area)
    _edges(b, rng)
    _house(b)
    _garage(b)
    _front_garden(b, s)
    _street(b, s)
    _back_garden(b, s)
    _extras(b, s)
    _meta(b)
    cat.finish(b, "flower_pot")
