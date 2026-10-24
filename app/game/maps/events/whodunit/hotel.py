"""The Grand Meridian Hotel -- a masked ball in a city hotel of the thirties.

Layout (the street is to the south, +z; the alley behind, -z)::

    z -76 ======================= the back of the next block ======================
              the ALLEY: bins, crates, the delivery van, the FIRE ESCAPE
    z -40 +------------+---------+-----------+------------+-------------------+
          |SWITCHBOARD |MANAGER'S| CLOAKROOM | SERVICE    |     KITCHEN       |  the
    side  |            | OFFICE  |           | HALL(stair)|                   |  MOTOR
    street+------------+---------+-----------+------------+-------------------+  COURT
          |     the MERIDIAN BAR | the LOBBY (atrium,     |  the BALLROOM     |  (cars)
          |  (booths, the piano) | the grand stair)       |  (stage, balcony) |
    z  30 +----------------------+-----------+------------+-------------------+
              the pavement, the canopy, the STREET, the shops across it

Upstairs: the gallery round the atrium; the guest corridor and rooms 101 to
104 over the bar; the writing room, the linen room, the service landing
and the honeymoon suite along the back; the ballroom's balcony.  The fire
escape climbs the back wall from the alley to the writing room and on up to
the roof: the roof garden, the water tower, the great sign, and the glass
over the atrium.

The twist is the masquerade: now and then the band strikes up, every guest
puts the same mask on, and nobody can tell who is who.
"""
from __future__ import annotations

import random
from typing import List, Tuple

from ..kit import (ArenaArea, Surfaces, backdrop, car, carve, crate, dumpster, flight, ground,
                   lamp_post, lantern, letters, perimeter, plate, rect, slab, step_paint,
                   strip_light)
from ..prop_panic import furniture as fx
from ..prop_panic.catalogue import (B, BLACK, BRASS, C, CREAM, GOLD, K, R, S, WHITE, WOOD,
                                    WOOD_DARK, place, stamp)
from ..prop_panic.furniture import COUNTER_TOP, TABLE_TOP
from ..prop_panic.rooms import DECAL_TILE, covering, grow, interior, tiled
from .common import Walls, candelabra, chandelier, hang, room, stair

HALF = (92.0, 76.0)
SKY = {"top": "#0a0c1c", "horizon": "#3a2a4a", "sun": [0.25, 0.6, 0.45],
       "clouds": 0.35, "tint": "#d8c8e8"}
AMBIENT = "#6a6080"
GROUND = "#34343a"
FOG = 560.0

STONE = "#d8c8a4"           # the limestone front
STONE_DARK = "#8a7a60"
BRONZE = "#6a5434"          # the window frames
PART = "#d8ccb4"            # the inside walls
PANEL = "#3a2a1a"           # door trims
CEILING = "#f2ead8"
CARPET = "#7a1a2a"
ASPHALT = "#34343a"
PAVING = "#8a8680"
IRON = "#2a2a2e"
JADE = "#1e5a4a"

T, P = 1.2, 0.6
F1, C1 = 0.6, 12.6
F2, C2 = 13.2, 24.0
TOP = 24.6                  # the roof, where you walk on it
X0, X1, Z0, Z1 = -60.0, 60.0, -40.0, 30.0
IX0, IX1, IZ0, IZ1 = X0 + T, X1 - T, Z0 + T, Z1 - T
ZM = -10.0                  # the front rooms | the back row
XW, XE = -20.0, 20.0        # the bar | the lobby | the ballroom
XB0, XB1, XB2 = -44.0, -30.0, 0.0
XR = -40.0                  # upstairs: rooms 101/103 | 102/104
ZC0, ZC1 = 7.0, 13.0        # upstairs: the guest corridor between these
GD, UD = F1 + 10.0, F2 + 9.0             # door heads, downstairs and up
G_SILL, G_TOP = 3.6, 10.4
U_SILL, U_TOP = 15.6, 21.8

ATRIUM = rect(-14.0, 14.0, -4.0, 24.0)   # open from the lobby floor to the glass
GRAND = (-5.0, 5.0, 20.0, -4.0)          # x0, x1, z on the lobby floor, z at the gallery
VOID = rect(XE + P / 2.0, IX1, -4.0, IZ1)  # the ballroom's height, over its floor
WELL = rect(5.0, XE - P / 2.0, IZ0, IZ0 + 5.0)   # the service stair's well
STAGE = rect(46.0, IX1, -2.0, 26.0)
DANCE = rect(26.0, 44.0, 3.0, 21.0)
FIRE = (-36.0, -52.6, -36.6, -45.4, -40.4, -50.0)   # the fire escape: see _fire_escape


# ============================================================== the walls
def _walls() -> Walls:
    w = Walls(PANEL, BRONZE)
    g, u = (G_SILL, G_TOP), (U_SILL, U_TOP)
    # ---- the outside, in two storeys (so a door upstairs is a doorway)
    front_lo = [(-56.0, -50.0, *g, "win"), (-32.0, -26.0, *g, "win"), (-44.2, -39.8, 0.0, GD, "door"),
                (-17.0, -11.0, *g, "win"), (11.0, 17.0, *g, "win"), (-6.0, 6.0, 0.0, F1 + 11.4, "door"),
                (24.0, 30.0, 3.6, 12.0, "win"), (36.0, 42.0, 3.6, 12.0, "win"),
                (48.0, 54.0, 3.6, 12.0, "win")]
    front_hi = [(-52.0, -46.0, *u, "win"), (-34.0, -26.0, *u, "win"), (-17.0, -11.0, *u, "win"),
                (-4.0, 4.0, *u, "win"), (11.0, 17.0, *u, "win"), (24.0, 30.0, 14.4, U_TOP, "win"),
                (36.0, 42.0, 14.4, U_TOP, "win"), (48.0, 54.0, 14.4, U_TOP, "win")]
    back_lo = [(-54.0, -48.0, *g, "win"), (-40.0, -34.0, *g, "win"), (-22.0, -16.0, *g, "win"),
               (-10.0, -4.0, *g, "win"), (26.0, 32.0, *g, "win"), (36.0, 42.0, *g, "win"),
               (46.0, 50.4, 0.0, GD, "door")]
    back_hi = [(-58.0, -53.6, F2, UD, "door"), (-48.0, -42.0, *u, "win"), (-38.0, -32.0, *u, "win"),
               (-22.0, -16.0, *u, "win"), (-10.0, -4.0, *u, "win"), (8.0, 14.0, *u, "win"),
               (28.0, 34.0, *u, "win"), (40.0, 46.0, *u, "win")]
    west_lo = [(-1.0, 5.0, *g, "win"), (9.0, 15.0, *g, "win"), (19.0, 25.0, *g, "win"),
               (-30.0, -24.0, *g, "win")]
    west_hi = [(-4.0, 2.0, *u, "win"), (8.2, 11.8, *u, "win"), (21.0, 27.0, *u, "win"),
               (-34.0, -28.0, *u, "win"), (-22.0, -16.0, *u, "win")]
    east_lo = [(-30.0, -24.0, *g, "win"), (-20.0, -15.6, 0.0, GD, "door")]
    east_hi = [(-34.0, -28.0, *u, "win"), (-18.0, -12.0, *u, "win")]
    for y0, y1, holes in ((0.0, F2, front_lo), (F2, TOP, front_hi)):
        w.add("x", Z1 - T / 2.0, IX0, IX1, y0, y1, STONE, holes, t=T, floor=F1, out=1)
    for y0, y1, holes in ((0.0, F2, back_lo), (F2, TOP, back_hi)):
        w.add("x", Z0 + T / 2.0, IX0, IX1, y0, y1, STONE, holes, t=T, floor=F1, out=-1)
    for y0, y1, holes in ((0.0, F2, west_lo), (F2, TOP, west_hi)):
        w.add("z", X0 + T / 2.0, Z0, Z1, y0, y1, STONE, holes, t=T, floor=F1, out=-1)
    for y0, y1, holes in ((0.0, F2, east_lo), (F2, TOP, east_hi)):
        w.add("z", X1 - T / 2.0, Z0, Z1, y0, y1, STONE, holes, t=T, floor=F1, out=1)
    # ---- downstairs
    door = lambda a, c: (a, c, F1, GD, "door")            # noqa: E731
    w.add("x", ZM, IX0, IX1, F1, C1, PART,
          [door(-54.0, -49.6), door(-38.0, -33.6), door(-14.0, -9.6), door(9.6, 14.0), door(26.0, 30.4)])
    w.add("z", XW, ZM + P / 2.0, IZ1, F1, C1, PART, [door(16.0, 22.0)])
    w.add("z", XE, ZM + P / 2.0, IZ1, F1, C1, PART, [(2.0, 14.0, F1, F1 + 11.4, "door")])
    for x in (XB0, XB1, XB2, XE):
        w.add("z", x, IZ0, ZM - P / 2.0, F1, C1, PART, [door(-28.0, -23.6)])
    # ---- upstairs
    up = lambda a, c: (a, c, F2, UD, "door")              # noqa: E731
    w.add("x", ZM, IX0, IX1, F2, C2, PART, [up(-14.0, -9.6), up(9.6, 14.0), up(50.0, 54.4)])
    w.add("z", XW, ZM + P / 2.0, IZ1, F2, C2, PART, [up(7.8, 12.2)])
    w.add("z", XE, ZM + P / 2.0, IZ1, F2, C2, PART, [up(-9.2, -4.8)])
    w.add("x", ZC0, IX0, XW - P / 2.0, F2, C2, PART, [up(-52.0, -47.6), up(-32.0, -27.6)])
    w.add("x", ZC1, IX0, XW - P / 2.0, F2, C2, PART, [up(-52.0, -47.6), up(-32.0, -27.6)])
    w.add("z", XR, ZM + P / 2.0, ZC0 - P / 2.0, F2, C2, PART, [up(1.6, 6.0)])
    w.add("z", XR, ZC1 + P / 2.0, IZ1, F2, C2, PART)
    for x in (XB1, XB2, XE):
        w.add("z", x, IZ0, ZM - P / 2.0, F2, C2, PART, [up(-28.0, -23.6)])
    return w


ROOMS = [
    # key, name, inner, y0, y1, walls, floor, decal
    ("bar", "the Meridian Bar", rect(IX0, XW - P / 2.0, ZM + P / 2.0, IZ1), F1, C1, "#1e3a32",
     "#3a2418", "planks"),
    ("lobby", "the lobby", rect(XW + P / 2.0, XE - P / 2.0, ZM + P / 2.0, IZ1), F1, C2, "#e8dcc0",
     "", ""),
    ("ballroom", "the ballroom", rect(XE + P / 2.0, IX1, ZM + P / 2.0, IZ1), F1, C2, "#e8d4b0", "", ""),
    ("switchboard", "the switchboard room", rect(IX0, XB0 - P / 2.0, IZ0, ZM - P / 2.0), F1, C1,
     "#c8d0c0", "#6a6a5a", "tiles"),
    ("office", "the manager's office", rect(XB0 + P / 2.0, XB1 - P / 2.0, IZ0, ZM - P / 2.0), F1, C1,
     "#3a4a3a", "#2a4a3a", ""),
    ("cloakroom", "the cloakroom", rect(XB1 + P / 2.0, XB2 - P / 2.0, IZ0, ZM - P / 2.0), F1, C1,
     "#6a3a3a", "#5a3a24", "planks"),
    ("service", "the service hall", rect(XB2 + P / 2.0, XE - P / 2.0, IZ0, ZM - P / 2.0), F1, C1,
     "#c8c8b8", "", ""),
    ("kitchen", "the kitchen", rect(XE + P / 2.0, IX1, IZ0, ZM - P / 2.0), F1, C1, "#e8e8e0",
     "#d8d4c8", "tiles"),
    ("r101", "room 101", rect(IX0, XR - P / 2.0, ZC1 + P / 2.0, IZ1), F2, C2, "#5a6a8a", "#3a4a6a", ""),
    ("r102", "room 102", rect(XR + P / 2.0, XW - P / 2.0, ZC1 + P / 2.0, IZ1), F2, C2, "#8a6a5a",
     "#6a3a3a", ""),
    ("r103", "room 103", rect(IX0, XR - P / 2.0, ZM + P / 2.0, ZC0 - P / 2.0), F2, C2, "#6a8a6a",
     "#3a5a3a", ""),
    ("r104", "room 104", rect(XR + P / 2.0, XW - P / 2.0, ZM + P / 2.0, ZC0 - P / 2.0), F2, C2,
     "#8a7a5a", "#5a4a3a", ""),
    ("corridor", "the guest corridor", rect(IX0, XW - P / 2.0, ZC0 + P / 2.0, ZC1 - P / 2.0), F2, C2,
     "#e8dcc0", CARPET, ""),
    ("writing", "the writing room", rect(IX0, XB1 - P / 2.0, IZ0, ZM - P / 2.0), F2, C2, "#3a2a2a",
     "#5a3a24", "planks"),
    ("linen", "the linen room", rect(XB1 + P / 2.0, XB2 - P / 2.0, IZ0, ZM - P / 2.0), F2, C2,
     "#d8e0e8", "#a8a8a0", "planks"),
    ("landing", "the service landing", rect(XB2 + P / 2.0, XE - P / 2.0, IZ0, ZM - P / 2.0), F2, C2,
     "#c8c8b8", "", ""),
    ("suite", "the honeymoon suite", rect(XE + P / 2.0, IX1, IZ0, ZM - P / 2.0), F2, C2, "#e8c8d0",
     "#8a2a3a", ""),
]


def _shell(b: ArenaArea, w: Walls) -> None:
    """The walls, the floors and the ceilings, the paint, the roof."""
    w.build(b)
    # the ground floor (and the step in every outside door), the first
    # floor (round the atrium, the ballroom and the service stair), the
    # ceiling under the roof (round the atrium's glass)
    slab(b, rect(IX0, IX1, IZ0, IZ1), F1, F1, "#5a4a3a")
    for a, c in ((-44.2, -39.8), (-6.0, 6.0)):
        slab(b, rect(a, c, IZ1, Z1), F1, F1, STONE_DARK)
    slab(b, rect(46.0, 50.4, Z0, IZ0), F1, F1, STONE_DARK)
    slab(b, rect(IX1, X1, -20.0, -15.6), F1, F1, STONE_DARK)
    plate(b, carve(rect(IX0, IX1, IZ0, IZ1), [ATRIUM, VOID, WELL]), F2, F2 - C1, CEILING)
    plate(b, carve(rect(IX0, IX1, IZ0, IZ1), [ATRIUM]), TOP, TOP - C2, CEILING)
    # the paint, and the floors (cut round the stairs)
    for key, name, inner, y0, y1, colour, floor, decal in ROOMS:
        holes = w.holes_for(inner, y0, y1)
        if key in ("lobby", "ballroom", "service", "landing"):
            interior(b, inner, y0, y1, colour, holes)
        else:
            interior(b, inner, y0, y1, colour, holes, floor=floor, floor_decal=decal)
    lobby = rect(XW + P / 2.0, XE - P / 2.0, ZM + P / 2.0, IZ1)
    for piece in carve(lobby, [grow(rect(GRAND[0], GRAND[1], GRAND[3], GRAND[2]), 0.1)]):
        tiled(b, piece, F1, "#e8e4dc", "harlequin", DECAL_TILE["harlequin"])
    for piece in carve(lobby, [grow(ATRIUM, 0.1)]):
        covering(b, piece, F2, CARPET)
    ball = rect(XE + P / 2.0, IX1, ZM + P / 2.0, IZ1)
    for piece in carve(ball, [STAGE, DANCE]):
        tiled(b, piece, F1, "#8a5a2a", "planks", DECAL_TILE["planks"])
    tiled(b, DANCE, F1, "#b89040", "harlequin", DECAL_TILE["harlequin"])
    covering(b, rect(XE + P / 2.0, IX1, ZM + P / 2.0, -4.1), F2, CARPET)
    service = rect(XB2 + P / 2.0, XE - P / 2.0, IZ0, ZM - P / 2.0)
    for piece in carve(service, [grow(WELL, 0.1)]):
        tiled(b, piece, F1, "#8a8a80", "tiles", DECAL_TILE["tiles"])
        covering(b, piece, F2, "#7a7a70")


# ============================================================== the stairs
def _stairs(b: ArenaArea) -> None:
    x0, x1, near, far = GRAND
    flight(b, "z", near, far, x0, x1, F1, F2, "#7a1a2a", fill=F1 - 0.3)
    step_paint(b, x0 + 0.4, x1 - 0.4, far, -1.0, F2)
    # a balustrade up each side, a step at a time, and the newels at the foot
    steps = 7
    run = (near - far) / steps
    for i in range(steps):
        top = F1 + (F2 - F1) * (i + 1) / steps
        z = near - run * (i + 0.5)
        for x in (x0 + 0.2, x1 - 0.2):
            b.box([x, top + 1.5, z], [0.4, 3.0, run], "#2a1a12")
            b.box([x, top + 3.1, z], [0.6, 0.2, run], BRASS, material="metal")
    for x in (x0 + 0.2, x1 - 0.2):
        b.box([x, F1 + 2.6, near + 0.5], [1.0, 5.2, 1.0], "#2a1a12")
        b.sphere([x, F1 + 5.7, near + 0.5], [1.2, 1.2, 1.2], BRASS, material="metal")
    # the gallery's rail round the atrium (open where the stair arrives)
    ax0, ax1, az0, az1 = ATRIUM
    rail = "#2a1a12"
    b.box([ax0 - 0.2, F2 + 1.6, (az0 + az1) / 2.0], [0.4, 3.2, az1 - az0 + 0.8], rail)
    b.box([ax1 + 0.2, F2 + 1.6, (az0 + az1) / 2.0], [0.4, 3.2, az1 - az0 + 0.8], rail)
    b.box([0.0, F2 + 1.6, az1 + 0.2], [ax1 - ax0, 3.2, 0.4], rail)
    for a, c in ((ax0, x0), (x1, ax1)):
        b.box([(a + c) / 2.0, F2 + 1.6, az0 - 0.2], [c - a, 3.2, 0.4], rail)
    for x in (ax0 - 0.2, ax1 + 0.2):
        b.box([x, F2 + 3.3, (az0 + az1) / 2.0], [0.6, 0.2, az1 - az0 + 0.8], BRASS, material="metal")
    b.box([0.0, F2 + 3.3, az1 + 0.2], [ax1 - ax0, 0.2, 0.6], BRASS, material="metal")
    # the service stair, from beside the kitchen door up to the landing
    wx0, wx1, wz0, wz1 = WELL
    flight(b, "x", wx1, wx0, wz0, wz1, F1, F2, "#6a6a62", fill=F1 - 0.3)
    b.box([(wx0 + wx1) / 2.0, F2 + 1.6, wz1 + 0.2], [wx1 - wx0, 3.2, 0.4], "#5a5a52")


# ===================================================== the rooms, furnished
def _bar(b: ArenaArea) -> None:
    y = F1
    # the bar itself, the back bar with its bottles and its mirror
    stamp(b, fx.counter(22.0, 2.4, "#2a1a14", "#c8a040", "#3a2a1e"), -37.0, -3.0, y, 0)
    for x0, x1 in ((-47.0, -39.0), (-31.6, -22.0)):
        stamp(b, fx.shelf_unit(x1 - x0, 2, 1.6, WOOD_DARK, metal=False), (x0 + x1) / 2.0, -8.85, y, 0)
        for k, top in enumerate(fx.shelf_tops(2)[1:]):
            for j in range(int((x1 - x0 - 1.0) // 1.1)):
                colour = ("#c8a040", "#3a8a5a", "#c84a3a", "#6a8ac8", "#e8e0c8")[(j + k) % 5]
                stamp(b, [C(0.0, 0.0, 0.0, 0.5, 1.3, 0.5, colour, m="glass", ghost=True)],
                      x0 + 0.9 + j * 1.1, -8.85, y + top)
        b.box([(x0 + x1) / 2.0, y + 9.6, ZM + P / 2.0 + 0.09], [x1 - x0, 2.4, 0.08], "#a8c0c8",
              material="metal", collide=False)
    for x in range(-46, -26, 3):
        stamp(b, [C(0.0, 0.0, 0.0, 0.5, 2.6, 0.5, BRASS, m="metal"),
                  C(0.0, 2.6, 0.0, 1.4, 0.4, 1.4, "#7a1a2a")], float(x), -0.2, y)
    for x in (-44.0, -37.0, -30.0):
        hang(b, fx.pendant(2.2, "#c8a040"), x, C1, -3.0)
    # booths along the west wall, a window over every table
    for z in (2.0, 12.0, 22.0):
        stamp(b, [B(0.0, 0.0, 0.0, 2.0, 0.3, 2.0, WOOD_DARK), C(0.0, 0.3, 0.0, 0.6, TABLE_TOP - 0.3, 0.6, BRASS),
                  B(0.0, TABLE_TOP, 0.0, 4.0, 0.3, 3.0, WOOD_DARK)], IX0 + 2.2, z, y)
        for side in (-1, 1):
            stamp(b, [B(0.0, 0.0, 0.0, 4.0, 1.8, 1.6, "#7a1a2a"),
                      B(0.0, 0.0, side * 1.0, 4.0, 5.0, 0.4, WOOD_DARK)], IX0 + 2.0, z + side * 2.8, y)
        stamp(b, candelabra(), IX0 + 2.2, z, y + TABLE_TOP + 0.3)
    # the piano, the singer's microphone, little round tables
    stamp(b, [C(-2.0, 0.0, -2.4, 0.4, 2.4, 0.4, BLACK), C(2.0, 0.0, -2.4, 0.4, 2.4, 0.4, BLACK),
              C(0.0, 0.0, 2.4, 0.4, 2.4, 0.4, BLACK), R(0.0, 2.4, 0.0, 5.0, 1.4, 6.0, BLACK),
              B(0.0, 3.0, -3.2, 5.0, 0.4, 1.0, WHITE), B(0.0, 3.8, 0.4, 4.6, 0.1, 5.0, "#1a1a1a")],
          -34.0, 23.0, y)
    stamp(b, [B(0.0, 0.0, 0.0, 2.4, 1.6, 1.4, "#2a1a14"), R(0.0, 1.6, 0.0, 2.2, 0.5, 1.2, "#7a1a2a")],
          -34.0, 18.6, y)
    stamp(b, [C(0.0, 0.0, 0.0, 1.0, 0.2, 1.0, BRASS, m="metal"),
              C(0.0, 0.2, 0.0, 0.16, 4.4, 0.16, BRASS, m="metal"),
              S(0.0, 4.6, 0.0, 0.5, 0.7, 0.5, "#c8ccd4", m="metal")], -40.0, 22.0, y)
    for x, z in ((-46.0, 9.0), (-36.0, 7.0), (-26.0, 9.0), (-46.0, 19.0), (-26.0, 26.5)):
        stamp(b, [C(0.0, 0.0, 0.0, 0.6, TABLE_TOP, 0.6, BRASS, m="metal"),
                  C(0.0, TABLE_TOP, 0.0, 3.2, 0.2, 3.2, WOOD_DARK),
                  C(0.0, TABLE_TOP + 0.2, 0.0, 0.5, 0.6, 0.5, "#ffd88a", m="neon", ghost=True)],
              x, z, y)
        place(b, "dining_chair", x - 2.4, z, y, 1, hide=False)
        place(b, "dining_chair", x + 2.4, z, y, 3, hide=False)
    for x, z in ((-46.0, 14.0), (-28.0, 18.0)):
        hang(b, fx.pendant(2.6, "#1e5a4a"), x, C1, z)
    for x in (-50.0, -30.0):
        hang(b, fx.pendant(2.6, "#1e5a4a"), x, C1, 26.0)
    letters(b, XW - P / 2.0 - 0.05, 8.6, 4.0, "COCKTAILS", 1.1, "#1e3a32", "#ffb35a", "x-", depth=0.1)
    place(b, "potted_plant", -23.0, 27.0, y, 0, hide=False)
    place(b, "potted_plant", -56.6, 27.0, y, 0, hide=False)


def _lobby(b: ArenaArea) -> None:
    y = F1
    # the reception desk, the keys behind it, the bell and the book
    stamp(b, fx.counter(10.0, 2.4, "#2a2a30", "#c8a040", "#3a3a40"), -15.0, 7.0, y, 1)
    b.box([XW + P / 2.0 + 0.2, y + 7.2, 7.0], [0.4, 3.2, 9.0], WOOD_DARK, collide=False)
    for k in range(8):
        for j in range(3):
            b.box([XW + P / 2.0 + 0.44, y + 6.2 + j * 1.0, 3.5 + k * 1.0], [0.08, 0.3, 0.2], BRASS,
                  material="metal", collide=False)
    stamp(b, [C(0.0, 0.0, 0.0, 0.7, 0.3, 0.7, BRASS, m="metal"),
              S(0.0, 0.3, 0.0, 0.6, 0.4, 0.6, BRASS, m="metal")], -15.0, 4.0, y + COUNTER_TOP)
    stamp(b, [B(0.0, 0.0, 0.0, 1.6, 0.3, 2.2, "#5a1a1a")], -15.0, 8.6, y + COUNTER_TOP)
    stamp(b, [C(0.0, 0.0, 0.0, 0.6, 1.4, 0.6, BRASS, m="metal"),
              K(0.0, 1.4, 0.0, 1.4, 0.8, 1.4, JADE)], -15.0, 11.0, y + COUNTER_TOP)
    # seats in the front corners, palms, the clock, the bell boy's trolley
    for x in (-13.0, 13.0):
        stamp(b, fx.sofa("#1e5a4a", 8.0, 3.4), x, IZ1 - 1.9, y, 2)
        stamp(b, fx.table(4.0, 2.4, "#2a2a30", BRASS, h=1.6), x, 23.0, y)
        place(b, "armchair", x + (4.6 if x < 0 else -4.6), 23.0, y, 3 if x < 0 else 1, hide=False)
    for x in (-18.6, 18.6, -7.6, 7.6):
        place(b, "potted_plant" if abs(x) > 10 else "fern", x, 27.4, y, 0, hide=False)
    place(b, "grandfather_clock", -18.4, ZM + P / 2.0 + 0.8, y, 0, hide=False)
    place(b, "trolley", 9.0, 13.0, y, 0, hide=False)
    stamp(b, [B(0.0, 0.0, 0.0, 1.6, 3.4, 1.2, WOOD_DARK), B(0.0, 3.4, 0.0, 1.8, 0.2, 1.4, BRASS)],
          9.5, 18.0, y)
    for x in (-7.2, 7.2):
        place(b, "fern", x, ZM + P / 2.0 + 1.4, y, 0, hide=False)
    stamp(b, fx.display_case(4.0, 2.4, 3.0), 16.6, -7.0, y)
    stamp(b, [S(0.0, 0.0, 0.0, 0.8, 0.8, 0.8, "#cfe8ff", m="glass")], 16.6, -7.0, y + 3.1)
    stamp(b, fx.sofa("#1e5a4a", 6.0, 2.8), 18.2, 21.0, y, 3)
    # lights: under the gallery, and the great chandelier under the glass
    for x in (-17.0, 17.0):
        for z in (-6.0, 4.0, 14.0, 26.0):
            hang(b, fx.pendant(1.6, CREAM), x, C1, z)
    for x in (-9.0, 0.0, 9.0):
        hang(b, fx.pendant(1.6, CREAM), x, C1, -7.0)
        hang(b, fx.pendant(1.6, CREAM), x, C1, 26.6)
    hang(b, chandelier(7.0, 10, GOLD), 0.0, TOP + 0.8, 10.0)
    for x in (-17.0, 17.0):
        for z in (0.0, 18.0):
            hang(b, fx.pendant(1.8, CREAM), x, C2, z)
    stamp(b, fx.painting(6.0, 4.0, "portrait"), 0.0, ZM + P / 2.0, F2 + 3.0, 0)
    for x, z in ((-18.75, -8.75), (18.75, 27.85), (-18.75, 27.85)):
        place(b, "potted_plant", x, z, F2, 0, hide=False)


def _ballroom(b: ArenaArea) -> None:
    y = F1
    sx0, sx1, sz0, sz1 = STAGE
    stage = y + 2.0
    slab(b, STAGE, stage, 2.0, "#3a2418")
    tiled(b, STAGE, stage, "#6a4a2a", "planks", DECAL_TILE["planks"])
    b.box([sx0 - 0.6, y + 0.5, (sz0 + sz1) / 2.0], [1.2, 1.0, 10.0], "#3a2418")
    b.box([sx0 - 0.04, y + 1.6, (sz0 + sz1) / 2.0], [0.08, 0.3, sz1 - sz0 - 1.0], "#ffd88a",
          material="neon", collide=False)
    # the curtains and the name in gold behind the band
    for a, c in ((sz0, sz0 + 9.0), (sz1 - 9.0, sz1)):
        b.box([IX1 - 0.5, (stage + 20.0) / 2.0, (a + c) / 2.0], [0.9, 20.0 - stage, c - a], "#8a1a2a")
    b.box([IX1 - 0.5, 21.2, (sz0 + sz1) / 2.0], [0.9, 2.4, sz1 - sz0], "#8a1a2a")
    b.box([IX1 - 0.06, 14.0, (sz0 + sz1) / 2.0], [0.04, 8.0, sz1 - sz0 - 18.0], "#2a1a1a",
          collide=False)
    letters(b, IX1 - 0.1, 14.0, (sz0 + sz1) / 2.0, "MERIDIAN", 1.4, "#2a1a1a", "#e8c860", "x-",
            depth=0.1)
    # the band: piano, drums, the stands and their chairs, the bass
    stamp(b, [C(-2.0, 0.0, -2.4, 0.4, 2.4, 0.4, BLACK), C(2.0, 0.0, -2.4, 0.4, 2.4, 0.4, BLACK),
              C(0.0, 0.0, 2.4, 0.4, 2.4, 0.4, BLACK), R(0.0, 2.4, 0.0, 5.0, 1.4, 6.0, BLACK),
              B(0.0, 3.0, -3.2, 5.0, 0.4, 1.0, WHITE)], 53.0, 20.0, stage, 1)
    for k, (dz, h) in enumerate(((0.0, 1.6), (2.2, 1.2), (-2.2, 1.2))):
        stamp(b, [C(0.0, 0.0, 0.0, 2.0 - k * 0.4, h, 2.0 - k * 0.4, "#c8ccd4", m="metal"),
                  C(0.0, h, 0.0, 2.0 - k * 0.4, 0.1, 2.0 - k * 0.4, WHITE)], 55.0, 4.0 + dz, stage)
    stamp(b, [C(0.0, 0.0, 0.0, 0.2, 4.0, 0.2, "#c8ccd4", m="metal"),
              C(0.0, 4.0, 0.0, 2.0, 0.1, 2.0, GOLD, m="metal")], 56.4, 6.8, stage)
    for z in (8.0, 11.0, 14.0):
        place(b, "dining_chair", 51.0, z, stage, 3, hide=False)
        stamp(b, [C(0.0, 0.0, 0.0, 0.2, 3.4, 0.2, BLACK), B(0.0, 3.4, 0.0, 0.2, 1.4, 1.8, BLACK)],
              48.6, z, stage)
    stamp(b, [R(0.0, 0.0, 0.0, 1.6, 4.6, 1.0, "#7a3a1a"), C(0.0, 4.6, 0.0, 0.3, 2.2, 0.3, BLACK)],
          50.0, 1.0, stage)
    stamp(b, [C(0.0, 0.0, 0.0, 1.0, 0.2, 1.0, BRASS, m="metal"),
              C(0.0, 0.2, 0.0, 0.16, 4.4, 0.16, BRASS, m="metal"),
              S(0.0, 4.6, 0.0, 0.5, 0.7, 0.5, "#c8ccd4", m="metal")], 47.6, 10.0, stage)
    # round tables along the windows and under the balcony
    for x, z in ((26.0, 25.0), (34.0, 25.0), (42.0, 25.0), (34.0, -6.4), (42.0, -6.4)):
        stamp(b, [C(0.0, 0.0, 0.0, 0.8, TABLE_TOP, 0.8, GOLD, m="metal"),
                  C(0.0, TABLE_TOP, 0.0, 4.0, 0.2, 4.0, WHITE),
                  C(0.0, TABLE_TOP + 0.2, 0.0, 0.6, 0.8, 0.6, "#ffd88a", m="neon", ghost=True)],
              x, z, y)
        place(b, "dining_chair", x - 2.8, z, y, 1, hide=False)
        place(b, "dining_chair", x + 2.8, z, y, 3, hide=False)
    # the champagne tower
    stamp(b, fx.table(5.0, 3.0, WHITE, GOLD, cloth=WHITE), 23.4, -6.4, y)
    for k, n in enumerate((4, 3, 2, 1)):
        stamp(b, [C(0.0, 0.0, 0.0, 0.7 * n + 0.4, 0.6, 0.7 * n + 0.4, "#f2e8c8", m="glass", a=0.6)],
              23.4, -6.4, y + TABLE_TOP + k * 0.6)
    # chandeliers over the floor
    for x in (30.0, 40.0):
        hang(b, chandelier(5.0, 10, GOLD), x, C2, 12.0)
    for x in (24.0, 36.0, 48.0):
        hang(b, fx.pendant(1.6, CREAM), x, C1, -7.0)
    # the balcony: its rail, chairs along the wall
    b.box([(XE + P / 2.0 + IX1) / 2.0, F2 + 1.6, -4.2], [IX1 - XE - P / 2.0, 3.2, 0.4], "#2a1a12")
    b.box([(XE + P / 2.0 + IX1) / 2.0, F2 + 3.3, -4.2], [IX1 - XE - P / 2.0, 0.2, 0.6], GOLD,
          material="metal")
    for x in (26.0, 34.0, 42.0):
        place(b, "dining_chair", x, ZM + P / 2.0 + 1.0, F2, 0, hide=False)
    for x in (30.0, 46.0):
        place(b, "side_table", x, ZM + P / 2.0 + 1.2, F2, 0, hide=False)
    for x in (24.0, 36.0, 48.0):
        hang(b, fx.pendant(1.6, CREAM), x, C2, -7.0)


def _back_rooms(b: ArenaArea) -> None:
    y = F1
    # ---- the switchboard: the board, the operators' desk, the telegraph
    sx = IX0
    b.box([sx + 0.8, y + 4.0, -17.0], [1.6, 8.0, 10.0], "#3a2a1e")
    for row in range(5):
        for k in range(8):
            b.box([sx + 1.64, y + 3.0 + row * 1.0, -21.0 + k * 1.1], [0.08, 0.3, 0.3],
                  ("#ffb35a", "#8aff8a", "#ff6a6a")[(row + k) % 3], material="neon", collide=False)
    stamp(b, fx.counter(10.0, 2.0, "#5a3a24", "#2a1a14", "#6a4a2a"), sx + 2.6, -17.0, y, 1)
    for z in (-20.0, -17.0, -14.0):
        place(b, "dining_chair", sx + 5.4, z, y, 3, hide=False)
    stamp(b, fx.table(5.0, 3.0, WOOD_DARK, WOOD_DARK), -51.0, -34.0, y)
    place(b, "radio", -51.0, -34.0, y + TABLE_TOP, 0, hide=False)
    for x in (-47.0,):
        stamp(b, [B(0.0, 0.0, 0.0, 2.4, 6.0, 2.0, "#6a6a5a", m="metal")], x, -36.8, y)
    place(b, "grandfather_clock", -46.0, ZM - P / 2.0 - 0.6, y, 2, hide=False)
    strip_light(b, -51.0, -24.0, C1, 6.0, "z", "#fff4dc", 1.0)
    # ---- the manager's office: the desk, the safe, the files, his portrait
    stamp(b, fx.table(7.0, 3.6, WOOD_DARK, WOOD_DARK), -37.0, -31.0, y)
    stamp(b, [B(0.0, 0.0, 0.0, 2.0, 0.2, 1.4, "#2a4a3a")], -37.0, -31.0, y + TABLE_TOP)
    stamp(b, [C(0.0, 0.0, 0.0, 0.5, 1.2, 0.5, BRASS, m="metal"), K(0.0, 1.2, 0.0, 1.2, 0.8, 1.2, JADE)],
          -39.6, -32.0, y + TABLE_TOP)
    place(b, "armchair", -37.0, -35.0, y, 0, hide=False)
    for x in (-39.0, -35.0):
        place(b, "dining_chair", x, -27.6, y, 2, hide=False)
    stamp(b, [B(0.0, 0.0, 0.0, 3.0, 4.0, 2.8, "#3a3a3a", m="metal"),
              C(0.0, 2.0, 1.44, 1.0, 0.12, 1.0, "#c8ccd4", m="metal", turn=0)], -33.0, -36.8, y, 0)
    for z in (-20.0, -16.0):
        stamp(b, [B(0.0, 0.0, 0.0, 2.4, 6.0, 2.2, "#5a5a4a", m="metal")], XB1 - P / 2.0 - 1.2, z, y)
    stamp(b, fx.bookcase(6.0, 8.6, 1.8, WOOD_DARK, seed=44), XB0 + P / 2.0 + 1.0, -17.0, y, 1)
    stamp(b, fx.painting(4.0, 5.0, "portrait"), -37.0, ZM - P / 2.0, y + 4.6, 2)
    stamp(b, fx.rug(8.0, 10.0, "#5a2a2a", border=GOLD), -37.0, -24.0, y)
    strip_light(b, -37.0, -24.0, C1, 6.0, "z", "#fff4dc", 1.0)
    # ---- the cloakroom: the counter, the racks of coats, the hats
    stamp(b, fx.counter(10.0, 2.0, "#5a3a24", "#c8a040", "#6a4a2a"), -21.0, -16.0, y, 0)
    place(b, "umbrella_stand", -14.6, -12.4, y, 0, hide=False)
    place(b, "umbrella_stand", -27.4, -12.4, y, 0, hide=False)
    coats = ("#2a2a3a", "#5a2a2a", "#3a4a3a", "#6a5a4a", "#1a1a1a", "#7a6a5a")
    for z in (-22.0, -29.0, -35.6):
        for xa, xb in ((-28.0, -18.0), (-12.0, -2.0)):
            for x in (xa, xb):
                b.cyl([x, y + 3.4, z], [0.4, 6.8, 0.4], BRASS, material="metal")
            b.box([(xa + xb) / 2.0, y + 6.6, z], [xb - xa, 0.2, 0.2], BRASS, material="metal")
            n = int((xb - xa - 1.0) // 1.0)
            for k in range(n):
                b.box([xa + 0.9 + k * 1.0, y + 4.4, z], [0.8, 4.2, 1.6], coats[(k * 7 + int(z)) % 6])
    stamp(b, fx.shelf_unit(8.0, 2, 1.8, WOOD_DARK, metal=False), -5.0, ZM - P / 2.0 - 0.95, y, 2)
    for k, top in enumerate(fx.shelf_tops(2)[1:]):
        for j in range(3):
            place(b, "hatbox", -7.6 + j * 2.6, ZM - P / 2.0 - 0.95, y + top, 0, hide=False)
    for x in (-21.0, -7.0):
        strip_light(b, x, -26.0, C1, 8.0, "z", "#fff4dc", 1.0)
    # ---- the service hall: the lift, the lockers, laundry, the clock
    b.box([4.0, (F1 + C2) / 2.0, -13.0], [6.0, C2 - F1, 5.4], "#2a2a2e", material="metal")
    for yy in (F1, F2):
        b.box([4.0, yy + 4.4, -15.76], [4.4, 8.8, 0.12], BRASS, material="metal", collide=False)
        b.box([4.0, yy + 9.4, -15.76], [1.6, 1.0, 0.12], "#ffb35a", material="neon", collide=False)
    for z in (-21.5, -19.5, -17.5):
        stamp(b, [B(0.0, 0.0, 0.0, 1.4, 7.0, 1.9, "#4a5a6a", m="metal")], 1.1, z, y)
    place(b, "laundry_basket", 7.0, -24.0, y, 0, hide=False)
    place(b, "trolley", 16.5, -18.0, y, 0, hide=False)
    stamp(b, [B(0.0, 0.0, 0.0, 1.4, 2.0, 1.0, "#5a5a52", m="metal")], 17.0, ZM - P / 2.0 - 0.5, y + 4.0)
    strip_light(b, 10.0, -22.0, C1, 8.0, "z", "#fff4dc", 1.0)
    # ---- the kitchen: ranges, the hood, tables, the iceboxes, the sinks
    for x in (25.0, 29.4, 33.8):
        stamp(b, fx.stove(4.0, 2.8), x, IZ0 + 1.4, y, 0)
        stamp(b, [C(0.0, 0.0, 0.0, 1.4, 1.2, 1.4, "#c8ccd4", m="metal")], x - 1.0, IZ0 + 1.4,
              y + COUNTER_TOP)
    stamp(b, fx.counter(7.6, 2.8), 40.0, IZ0 + 1.4, y, 0)
    b.box([32.0, y + 9.0, IZ0 + 1.6], [20.0, 1.6, 3.2], "#9aa0a8", material="metal", collide=False)
    for x, z in ((36.0, -24.0), (50.0, -28.0)):
        stamp(b, fx.table(9.0, 3.6, "#c8ccd4", "#8a8e96"), x, z, y)
    place(b, "cheese_wheel", 34.0, -24.0, y + TABLE_TOP, 0, hide=False)
    place(b, "watermelon", 38.6, -24.0, y + TABLE_TOP, 0, hide=False)
    place(b, "teapot", 50.0, -28.0, y + TABLE_TOP, 0, hide=False)
    for z in (-36.6, -32.6):
        stamp(b, fx.fridge("#e8f0f0", 3.8, 3.0, 7.6), IX1 - 1.6, z, y, 3)
    for x in (36.0, 41.6):
        stamp(b, fx.sink_unit(5.0, 2.8), x, ZM - P / 2.0 - 1.4, y, 2)
    stamp(b, fx.shelf_unit(6.0, 3, 2.0), 52.0, ZM - P / 2.0 - 1.0, y, 2)
    for k, top in enumerate(fx.shelf_tops(3)[1:]):
        for j in range(3):
            stamp(b, [C(0.0, 0.0, 0.0, 1.2, 1.0, 1.2, "#c8ccd4", m="metal", ghost=True)],
                  50.0 + j * 2.0, ZM - P / 2.0 - 1.0, y + top)
    for z in (-14.0, -17.0):
        place(b, "flour_sack", 22.4, z, y, 0, hide=False)
    for x in (30.0, 44.0, 54.0):
        strip_light(b, x, -22.0, C1, 8.0, "z", "#ffffff", 1.0)


def _upstairs(b: ArenaArea) -> None:
    y = F2
    # ---- room 101: a bed on the inside wall, the wardrobe, a chair
    stamp(b, fx.bed("#3a4a8a", 7.0, 10.0), XR - P / 2.0 - 5.0, 21.0, y, 3)
    stamp(b, fx.wardrobe(WOOD_DARK, 6.0, 8.6, 3.0), IX0 + 1.5, 17.0, y, 1)
    place(b, "armchair", -55.0, 26.4, y, 1, hide=False)
    place(b, "side_table", XR - P / 2.0 - 1.2, 27.4, y, 0, hide=False)
    stamp(b, fx.rug(8.0, 6.0, "#c8a040"), -50.0, 21.0, y)
    hang(b, fx.pendant(2.0, CREAM), -50.0, C2, 21.0)
    # ---- room 102: twin beds under the window, a desk
    for x in (-36.0, -24.0):
        stamp(b, fx.bed("#7a3a3a", 5.0, 9.0), x, IZ1 - 4.5, y, 2)
    place(b, "side_table", -30.0, IZ1 - 1.2, y, 0, hide=False)
    stamp(b, fx.table(2.6, 5.0, WOOD_DARK, WOOD_DARK), XW - P / 2.0 - 1.4, 17.0, y)
    place(b, "dining_chair", XW - P / 2.0 - 3.6, 17.0, y, 1, hide=False)
    hang(b, fx.pendant(2.0, CREAM), -30.0, C2, 20.0)
    # ---- room 103: the bed, a bath behind a screen
    stamp(b, fx.bed("#3a6a4a", 7.0, 10.0), XR - P / 2.0 - 5.0, -5.0, y, 3)
    stamp(b, fx.bathtub(4.4, 9.0), IX0 + 2.4, -4.0, y, 0)
    stamp(b, [B(0.0, 0.0, 0.0, 0.3, 6.0, 4.0, "#c8b090")], IX0 + 5.4, 2.4, y)
    stamp(b, fx.basin(), IX0 + 1.6, 4.4, y, 1)
    hang(b, fx.pendant(2.0, CREAM), -48.0, C2, -2.0)
    # ---- room 104: bed against the back, a desk, a trunk
    stamp(b, fx.bed("#8a6a3a", 7.0, 10.0), -32.5, ZM + P / 2.0 + 5.0, y, 0)
    stamp(b, fx.table(2.6, 5.0, WOOD_DARK, WOOD_DARK), XW - P / 2.0 - 1.4, -4.0, y)
    place(b, "dining_chair", XW - P / 2.0 - 3.6, -4.0, y, 1, hide=False)
    place(b, "treasure_chest", -32.5, 2.2, y, 0, hide=False)
    hang(b, fx.pendant(2.0, CREAM), -30.0, C2, -2.0)
    # ---- the corridor: lamps on the walls, a table at the end
    for x in (-54.0, -44.0, -36.0, -26.0):
        strip_light(b, x, 10.0, C2, 3.0, "x", "#ffe8b8", 1.0)
    stamp(b, fx.table(2.0, 4.0, WOOD_DARK, WOOD_DARK), IX0 + 1.1, 10.0, y)
    place(b, "vase", IX0 + 1.1, 10.0, y + TABLE_TOP, 0, hide=False)
    # ---- the writing room: the fire, desks, the card table, the books
    stamp(b, fx.fireplace(9.0, 7.6, 2.4), -40.5, ZM - P / 2.0 - 1.2, y, 2)
    stamp(b, fx.painting(5.0, 3.6, "portrait"), -40.5, ZM - P / 2.0, y + 8.4, 2)
    for z in (-38.0 + 4.2, -14.6):
        stamp(b, fx.bookcase(6.0, 8.6, 1.8, WOOD_DARK, seed=int(-z)), XB1 - P / 2.0 - 0.9, z, y, 3)
    for x, z in ((-50.0, -31.0), (-50.0, -21.0)):
        stamp(b, fx.table(5.0, 2.6, WOOD_DARK, WOOD_DARK), x, z, y)
        place(b, "dining_chair", x, z - 2.4, y, 0, hide=False)
        stamp(b, [C(0.0, 0.0, 0.0, 0.5, 1.2, 0.5, BRASS, m="metal"),
                  K(0.0, 1.2, 0.0, 1.2, 0.8, 1.2, JADE)], x + 1.6, z, y + TABLE_TOP)
    stamp(b, fx.table(4.4, 4.4, "#1e5a3a", WOOD_DARK), -38.0, -30.0, y)
    for dx, q in ((-3.0, 1), (3.0, 3)):
        place(b, "dining_chair", -38.0 + dx, -30.0, y, q, hide=False)
    for x in (-44.0, -37.0):
        place(b, "armchair", x, -17.0, y, 0, hide=False)
    stamp(b, fx.rug(10.0, 6.0, "#5a2a2a", border=GOLD), -40.5, -17.0, y)
    place(b, "globe", -34.6, -36.4, y, 0, hide=False)
    for x in (-50.0, -38.0):
        strip_light(b, x, -26.0, C2, 6.0, "z", "#ffe8b8", 1.0)
    # ---- the linen room: shelves of sheets, baskets, the ironing board
    for x0, x1 in ((-29.2, -23.0), (-15.2, -10.8)):
        stamp(b, fx.shelf_unit(x1 - x0, 3, 2.0, "#c8c0b0", metal=False), (x0 + x1) / 2.0, IZ0 + 1.0, y, 0)
        for k, top in enumerate(fx.shelf_tops(3)[1:3]):
            for j in range(int((x1 - x0) // 2.0)):
                stamp(b, [B(0.0, 0.0, 0.0, 1.6, 0.9, 1.6, ("#f2f0ea", "#e8e0d0", "#d8e4f0")[(j + k) % 3])],
                      x0 + 1.0 + j * 2.0, IZ0 + 1.0, y + top)
    for x in (-24.0, -18.0, -6.0):
        place(b, "laundry_basket", x, -14.0, y, 0, hide=False)
    stamp(b, [B(0.0, 2.8, 0.0, 5.0, 0.2, 1.4, "#c8d8e8"), C(-1.6, 0.0, 0.0, 0.2, 2.8, 0.2, "#8a8e96"),
              C(1.6, 0.0, 0.0, 0.2, 2.8, 0.2, "#8a8e96")], -15.0, -26.0, y)
    place(b, "trolley", -10.0, -30.0, y, 0, hide=False)
    for x in (-21.0, -7.0):
        strip_light(b, x, -26.0, C2, 8.0, "z", "#ffffff", 1.0)
    # ---- the service landing: the lift door, the room-service trolley
    place(b, "trolley", 14.0, -20.0, y, 0, hide=False)
    stamp(b, [S(0.0, 0.0, 0.0, 1.4, 0.8, 1.4, "#c8ccd4", m="metal")], 14.0, -20.0, y + 1.2)
    stamp(b, fx.table(4.0, 2.4, WOOD, WOOD_DARK), 4.0, -21.0, y)
    place(b, "teapot", 4.0, -21.0, y + TABLE_TOP, 0, hide=False)
    strip_light(b, 10.0, -24.0, C2, 8.0, "z", "#ffffff", 1.0)
    # ---- the honeymoon suite: the four-poster, the golden bath, roses
    bx = IX1 - 5.5
    stamp(b, fx.bed("#8a1a2a", 9.0, 11.0, sheet="#f2e8e8", frame=GOLD), bx, -23.0, y, 3)
    for dx in (-5.3, 5.3):
        for dz in (-4.8, 4.8):
            b.cyl([bx + dx, y + 4.6, -23.0 + dz], [0.4, 9.2, 0.4], GOLD, material="metal")
    b.box([bx, y + 9.3, -23.0], [11.0, 0.2, 10.0], "#e8c8d0", collide=False)
    stamp(b, fx.bathtub(4.4, 9.0), 26.0, -32.0, y, 0)
    b.box([26.0, y + 1.42, -32.0], [3.6, 0.06, 7.8], GOLD, collide=False)
    stamp(b, fx.sofa("#e8c8d0", 8.0, 3.2), 36.0, ZM - P / 2.0 - 1.8, y, 2)
    stamp(b, fx.table(4.0, 2.4, GOLD, GOLD, h=1.6), 36.0, -15.6, y)
    stamp(b, [C(0.0, 0.0, 0.0, 1.2, 1.4, 1.2, "#c8ccd4", m="metal"),
              C(0.0, 1.4, 0.0, 0.4, 1.4, 0.4, "#1e4a2a", m="glass")], 36.0, -15.6, y + 1.6)
    stamp(b, fx.dresser(WOOD_DARK, 5.0, 2.2, 3.4), 44.0, IZ0 + 1.1, y, 0)
    place(b, "vase", 44.0, IZ0 + 1.1, y + 3.4, 0, hide=False)
    place(b, "vase", 30.0, -14.0, y, 0, hide=False)
    stamp(b, fx.wardrobe(WOOD_DARK, 6.0, 8.6, 3.0), 53.0, IZ0 + 1.5, y, 0)
    for x in (28.0, 40.0, 50.0):
        hang(b, fx.pendant(2.0, "#e8c8d0"), x, C2, -24.0)


# ================================================================== the roof
def _roof(b: ArenaArea) -> None:
    y = TOP
    # tar and gravel, round the glass and the garden deck
    for piece in carve(rect(IX0, IX1, IZ0, IZ1), [grow(ATRIUM, 0.7), rect(-56.0, -28.0, 4.0, 26.0)]):
        covering(b, piece, y, "#5a5650")
    # the parapet round the edge (open where the fire escape comes up)
    fx0, fx1 = FIRE[2], FIRE[2] + 4.6
    h = 2.4
    for a, c in ((IX0, fx0), (fx1, IX1)):
        b.box([(a + c) / 2.0, y + h / 2.0, Z0 + T / 2.0], [c - a, h, T], STONE)
        b.box([(a + c) / 2.0, y + h + 0.15, Z0 + T / 2.0], [c - a, 0.3, T + 0.4], STONE_DARK)
    b.box([0.0, y + h / 2.0, Z1 - T / 2.0], [IX1 - IX0, h, T], STONE)
    b.box([0.0, y + h + 0.15, Z1 - T / 2.0], [IX1 - IX0, 0.3, T + 0.4], STONE_DARK)
    for x in (X0 + T / 2.0, X1 - T / 2.0):
        b.box([x, y + h / 2.0, (Z0 + Z1) / 2.0], [T, h, Z1 - Z0], STONE)
        b.box([x, y + h + 0.15, (Z0 + Z1) / 2.0], [T + 0.4, 0.3, Z1 - Z0 + 0.4], STONE_DARK)
    # the glass over the atrium, on a curb, ribbed; the beam the
    # chandelier hangs from
    ax0, ax1, az0, az1 = ATRIUM
    curb = 1.2
    b.box([0.0, y + curb / 2.0, az0 - 0.3], [ax1 - ax0 + 1.2, curb, 0.6], IRON)
    b.box([0.0, y + curb / 2.0, az1 + 0.3], [ax1 - ax0 + 1.2, curb, 0.6], IRON)
    b.box([ax0 - 0.3, y + curb / 2.0, (az0 + az1) / 2.0], [0.6, curb, az1 - az0], IRON)
    b.box([ax1 + 0.3, y + curb / 2.0, (az0 + az1) / 2.0], [0.6, curb, az1 - az0], IRON)
    b.box([0.0, y + curb + 0.15, (az0 + az1) / 2.0], [ax1 - ax0 + 1.2, 0.3, az1 - az0 + 1.2],
          "#a8d0e0", material="glass", alpha=0.35)
    for k in range(1, 7):
        z = az0 - 0.6 + k * (az1 - az0 + 1.2) / 7.0
        b.box([0.0, y + curb + 0.35, z], [ax1 - ax0 + 1.2, 0.1, 0.2], IRON, collide=False)
    b.box([0.0, y + 1.0, 10.0], [ax1 - ax0, 0.4, 0.6], IRON)
    # the sign over the street
    for x in (-18.0, -6.0, 6.0, 18.0):
        b.box([x, (y + 29.6) / 2.0, 26.3], [0.8, 29.6 - y, 0.8], IRON)
    b.box([0.0, 34.0, 26.3], [46.0, 8.8, 0.6], "#1a1a24")
    letters(b, 0.0, 32.6, 26.6, "MERIDIAN", 4.4, "#1a1a24", "#ff7ac8", "z+", depth=0.3)
    letters(b, 0.0, 36.9, 26.6, "THE GRAND", 1.4, "#1a1a24", "#ffd88a", "z+", depth=0.3)
    for yy in (29.75, 38.25):
        b.box([0.0, yy, 26.66], [45.4, 0.3, 0.12], "#ff7ac8", material="neon", collide=False)
    for x in (-22.85, 22.85):
        b.box([x, 34.0, 26.66], [0.3, 8.8, 0.12], "#ff7ac8", material="neon", collide=False)
    # the water tower
    tx, tz = 40.0, -26.0
    for dx in (-2.6, 2.6):
        for dz in (-2.6, 2.6):
            b.box([tx + dx, y + 5.0, tz + dz], [0.6, 10.0, 0.6], IRON)
    b.box([tx, y + 10.2, tz], [7.0, 0.4, 7.0], IRON)
    b.cyl([tx, y + 13.9, tz], [7.0, 7.0, 7.0], "#6a4a2a")
    for yy in (y + 11.6, y + 14.2, y + 16.8):
        b.cyl([tx, yy, tz], [7.2, 0.3, 7.2], IRON, collide=False)
    b.cone([tx, y + 18.6, tz], [7.6, 2.4, 7.6], "#3a3a3e")
    # the lift's motor room, a chimney, the vents
    b.box([4.0, y + 3.5, -13.0], [7.0, 7.0, 6.4], STONE_DARK)
    b.box([4.0, y + 2.8, -16.24], [2.6, 5.6, 0.08], WOOD_DARK, collide=False)
    b.box([-40.5, y + 3.0, -12.2], [3.4, 6.0, 3.4], "#7a4a3a", decal="bricks")
    b.cyl([-40.5, y + 6.4, -12.2], [1.6, 0.8, 1.6], "#5a3a2a")
    for x, z in ((20.0, -30.0), (24.0, -30.0), (-14.0, -30.0)):
        b.cyl([x, y + 1.2, z], [1.4, 2.4, 1.4], "#8a8e96", material="metal")
        b.cone([x, y + 2.8, z], [2.0, 0.8, 2.0], "#8a8e96", material="metal")
    # the roof garden: a deck, a pergola, tables, planters, lights
    gx0, gx1, gz0, gz1 = -56.0, -28.0, 4.0, 26.0
    covering(b, rect(gx0, gx1, gz0, gz1), y, "#8a6a4a", "planks")
    for x in (gx0 + 1.0, gx1 - 1.0):
        for z in (gz0 + 1.0, gz1 - 1.0):
            b.box([x, y + 3.6, z], [0.6, 7.2, 0.6], "#f2ead8")
    for z in (gz0 + 1.0, gz1 - 1.0):
        b.box([(gx0 + gx1) / 2.0, y + 7.5, z], [gx1 - gx0 - 1.4, 0.6, 0.6], "#f2ead8")
    for k in range(7):
        x = gx0 + 2.0 + k * (gx1 - gx0 - 4.0) / 6.0
        b.box([x, y + 8.0, (gz0 + gz1) / 2.0], [0.4, 0.4, gz1 - gz0 - 1.4], "#f2ead8")
        for j in range(5):
            b.sphere([x, y + 7.6, gz0 + 3.0 + j * 4.0], [0.4, 0.4, 0.4],
                     ("#ffd88a", "#ff7ac8", "#8ad8ff")[(k + j) % 3], material="neon", collide=False)
    for x, z in ((-50.0, 10.0), (-42.0, 18.0), (-34.0, 10.0)):
        stamp(b, [C(0.0, 0.0, 0.0, 0.6, TABLE_TOP, 0.6, WHITE),
                  C(0.0, TABLE_TOP, 0.0, 3.4, 0.2, 3.4, WHITE)], x, z, y)
        place(b, "dining_chair", x - 2.4, z, y, 1, hide=False)
        place(b, "dining_chair", x + 2.4, z, y, 3, hide=False)
    for x in (-54.0, -46.0, -38.0, -30.0):
        stamp(b, fx.raised_bed(5.0, 2.4, "#4a8a3a", "#4a3424", "#c8c0b0"), x, gz1 + 1.4, y)
    place(b, "radio", -54.6, 20.0, y, 1, hide=False)


# ======================================================= the fire escape
def _fire_escape(b: ArenaArea) -> None:
    """From the alley up the back wall to the writing room's door, and on
    up to the roof: iron treads (open, so the alley shows through), two
    landings, a rail on the outside."""
    foot, mid, top, lane_a, wall_gap, outer = FIRE
    lane_b = lane_a                                   # where the two flights meet
    tread = 0.4

    def treads(x_from: float, x_to: float, y_from: float, y_to: float, z0: float, z1: float) -> None:
        steps = max(1, int(round((y_to - y_from) / 1.9)))
        run = (x_to - x_from) / steps
        rise = (y_to - y_from) / steps
        for i in range(steps):
            a, c = x_from + run * i, x_from + run * (i + 1)
            yy = y_from + rise * (i + 1)
            b.box([(a + c) / 2.0, yy - tread / 2.0, (z0 + z1) / 2.0], [abs(c - a), tread, z1 - z0], IRON,
                  material="metal")
            # an open rail: a post on every tread and a bar along the top,
            # the gap under it far too low for anybody to slip through
            b.box([a + (0.1 if c > a else -0.1), yy + 1.4, z0 + 0.15], [0.2, 2.8, 0.3], IRON,
                  material="metal")
            b.box([(a + c) / 2.0, yy + 2.95, z0 + 0.15], [abs(c - a), 0.3, 0.3], IRON, material="metal")

    # flight one: the alley to the first floor, along the wall
    treads(foot, mid, 0.0, F2, lane_a, wall_gap)
    # the first-floor landing, at the writing room's door
    land = rect(-59.6, mid, outer, Z0)
    slab(b, land, F2, tread, IRON)
    b.box([land[0] + 0.15, F2 + 1.5, (outer + Z0) / 2.0], [0.3, 3.0, Z0 - outer], IRON, material="metal")
    b.box([(land[0] + mid) / 2.0, F2 + 1.5, outer + 0.15], [mid - land[0] - 0.3, 3.0, 0.3], IRON,
          material="metal")
    # flight two: the landing to the roof, outside the first
    treads(mid, top, F2, TOP, outer, lane_b)
    # the top landing, through the gap in the parapet
    slab(b, rect(top, top + 4.6, outer, Z0), TOP, tread, IRON)
    b.box([top + 4.45, TOP + 1.5, (outer + Z0) / 2.0], [0.3, 3.0, Z0 - outer], IRON, material="metal")
    b.box([top + 2.3, TOP + 1.5, outer + 0.15], [4.0, 3.0, 0.3], IRON, material="metal")
    b.box([top + 0.15, TOP + 1.5, (lane_a + Z0) / 2.0], [0.3, 3.0, Z0 - lane_a], IRON, material="metal")
    lantern(b, -55.8, F2 + 9.6, Z0 - 0.7)


# ============================================================ outside
def _street(b: ArenaArea, s: Surfaces, rng: random.Random) -> None:
    hx, hz = HALF
    kerb = 0.6
    s.lay(rect(-hx, hx, Z1, 40.0), kerb, PAVING)
    s.lay(rect(-hx, hx, 62.0, hz), kerb, PAVING)
    s.lay(rect(-72.0, X0, Z0, Z1), kerb, PAVING)
    s.lay(rect(X1, hx, Z0, Z1), kerb, "#7a7670")
    # the line down the road, the crossing at the door
    for k in range(-9, 10):
        b.box([k * 10.0, 0.03, 51.0], [5.0, 0.06, 0.5], "#e8e0c8", collide=False)
    for k in range(-3, 4):
        b.box([k * 2.4, 0.03, 51.0], [1.4, 0.06, 21.0], "#e8e8e8", collide=False)
    # the canopy over the door, the red carpet, the ropes, the doorman
    slab(b, rect(-9.0, 9.0, Z1, 39.0), 13.0, 0.4, "#1a1a24")
    b.box([0.0, 12.6, 39.1], [18.0, 1.6, 0.4], "#1a1a24")
    letters(b, 0.0, 12.6, 39.3, "GRAND MERIDIAN", 0.9, "#1a1a24", "#e8c860", "z+", depth=0.1)
    for x in (-8.4, 8.4):
        b.cyl([x, (kerb + 12.6) / 2.0, 38.0], [0.6, 12.6 - kerb, 0.6], BRASS, material="metal")
    for k in range(5):
        b.box([-7.0 + k * 3.5, 12.55, 34.0], [1.4, 0.1, 1.4], "#ffe8b8", material="neon",
              collide=False)
    covering(b, rect(-4.0, 4.0, Z1, 40.0), kerb, "#8a1a2a")
    for x in (-5.4, 5.4):
        for z in (32.0, 35.0, 38.0):
            place(b, "stanchion", x, z, kerb, 0, hide=False)
    stamp(b, [B(0.0, 0.0, 0.0, 1.6, 3.4, 1.2, WOOD_DARK), B(0.0, 3.4, 0.0, 1.8, 0.2, 1.4, BRASS)],
          9.6, 33.0, kerb)
    # cars at the kerb and on the road
    car(b, -2.0, 44.0, "x", "#1a1a1e", length=14.0)
    car(b, -34.0, 44.0, "x", "#e8b81e")
    car(b, 30.0, 58.0, "x", "#7a1a1a")
    car(b, -66.0, 58.0, "x", "#2a4a6a")
    car(b, -82.0, 8.0, "z", "#e8b81e")
    # lamps both sides, a post box, a hydrant, a bench
    for x in (-50.0, -22.0, 22.0, 50.0):
        lamp_post(b, x, 38.6, 13.0, IRON, "#ffd88a", y=kerb, arm="z+")
    for x in (-60.0, -20.0, 20.0, 60.0):
        lamp_post(b, x, 63.4, 13.0, IRON, "#ffd88a", y=kerb, arm="z-")
    for z in (-20.0, 14.0):
        lamp_post(b, -71.0, z, 13.0, IRON, "#ffd88a", y=kerb, arm="x-")
    stamp(b, [C(0.0, 0.0, 0.0, 1.6, 3.6, 1.6, "#8a1a1a"), S(0.0, 3.6, 0.0, 1.6, 0.9, 1.6, "#8a1a1a")],
          -27.0, 38.4, kerb)
    stamp(b, [C(0.0, 0.0, 0.0, 1.0, 2.2, 1.0, "#c8401e"), S(0.0, 2.2, 0.0, 1.0, 0.6, 1.0, "#c8401e")],
          27.0, 38.8, kerb)
    # the side street: the newsstand and the telephone box
    stamp(b, [B(0.0, 0.0, 0.0, 4.0, 6.0, 5.0, "#2a4a3a"), B(0.0, 6.0, 0.0, 4.6, 0.4, 5.6, "#c8a040"),
              B(-2.06, 1.2, 0.0, 0.12, 3.0, 4.0, "#e8e0c8", dec="canvas")], -66.0, 22.0, kerb)
    stamp(b, [B(0.0, 0.0, 0.0, 3.2, 8.0, 3.2, "#2a4a3a"), B(0.0, 8.0, 0.0, 3.4, 0.4, 3.4, "#c8a040"),
              B(-1.66, 1.0, 0.0, 0.12, 5.6, 2.4, "#ffe8b8", m="neon")], -66.0, -14.0, kerb)
    # the motor court
    car(b, 76.0, -30.0, "x", "#2a2a3a", y=kerb)
    car(b, 76.0, 4.0, "x", "#5a1a2a", y=kerb)
    car(b, 76.0, 20.0, "x", "#1e4a3a", y=kerb, length=13.0)
    stamp(b, [B(0.0, 0.0, 0.0, 2.0, 5.6, 1.6, "#c8401e"), S(0.0, 5.6, 0.0, 1.6, 1.6, 1.6, "#f2e8c8")],
          88.0, -10.0, kerb)
    stamp(b, fx.bench(6.0), 66.0, -6.0, kerb, 1)
    for z in (-36.0, 26.0):
        stamp(b, fx.raised_bed(6.0, 3.0, "#3a7a3a", "#4a3424", STONE), 88.0, z, kerb, 1)
    # the alley: bins, crates, the van, puddles, the kitchen door's lamp
    dumpster(b, -10.0, -46.0, "x", "#2f5f3a")
    dumpster(b, 24.0, -46.0, "x", "#3a4a5a")
    crate(b, 36.0, 0.0, -70.0, 4.0, WOOD)
    crate(b, 40.4, 0.0, -70.0, 4.0, WOOD)
    crate(b, 38.2, 4.0, -70.0, 4.0, WOOD)
    crate(b, -62.0, 0.0, -70.0, 5.0, WOOD)
    crate(b, -80.0, 0.0, -46.0, 4.0, WOOD)
    for x in (44.0, 52.4):
        b.cyl([x, 1.6, -42.0], [1.8, 3.2, 1.8], "#6a6e76", material="metal")
    car(b, 6.0, -64.0, "x", "#4a5a6a", length=14.0)
    for x, z, w_, d_ in ((-30.0, -58.0, 8.0, 5.0), (14.0, -52.0, 6.0, 4.0), (60.0, -60.0, 9.0, 4.0)):
        b.box([x, 0.02, z], [w_, 0.04, d_], "#2a3a4a", material="glass", collide=False, alpha=0.7)
    lantern(b, 48.2, F1 + 11.4, Z0 - 0.7)
    del rng


def _across(b: ArenaArea, rng: random.Random) -> None:
    """The shops across the street, fixed to the face of the next block,
    and the windows of the blocks all round, some of them lit."""
    hx, hz = HALF
    face = hz
    lit = ("#ffd88a", "#ffe8c8", "#cfe8ff", "#ffb35a")
    for side in ("z+", "z-", "x+", "x-"):
        along = side in ("z+", "z-")
        span = hx if along else hz
        sign = 1.0 if side.endswith("+") else -1.0
        wall = (hz if along else hx) * sign - sign * 0.06
        for row, yy in enumerate((17.0, 22.0, 27.0, 32.0)):
            if side == "z+" and yy < 18.0:
                continue
            u = -span + 6.0
            while u < span - 6.0:
                colour = rng.choice(lit) if rng.random() < 0.4 else "#22222a"
                material = "neon" if colour != "#22222a" else ""
                if along:
                    b.box([u, yy, wall], [3.0, 3.0, 0.12], colour, material=material, collide=False)
                else:
                    b.box([wall, yy, u], [0.12, 3.0, 3.0], colour, material=material, collide=False)
                u += 7.0
    shops = ((-80.0, -50.0, "BAKERY", "#c87a3a"), (-40.0, -6.0, "PALACE", "#c83a5a"),
             (6.0, 36.0, "FLORIST", "#3a8a5a"), (46.0, 80.0, "NEWS", "#3a5a8a"))
    for x0, x1, name, colour in shops:
        mid = (x0 + x1) / 2.0
        b.box([mid, 6.6, face - 0.3], [x1 - x0, 12.0, 0.6], "#2a2a30")
        b.box([mid, 4.6, face - 0.66], [x1 - x0 - 8.0, 6.0, 0.12], "#ffe2a8", material="neon",
              collide=False)
        b.box([mid, 9.6, face - 1.6], [x1 - x0, 0.4, 2.6], colour)
        letters(b, mid, 11.2, face - 0.6, name, 1.6, "#2a2a30", "#ffe8c8", "z-", depth=0.1)
    # the cinema's marquee, its bulbs
    b.box([-23.0, 14.0, face - 3.0], [30.0, 3.2, 6.0], "#1a1a24")
    for k in range(24):
        b.sphere([-37.0 + k * 1.2, 15.8, face - 6.06], [0.4, 0.4, 0.4], "#ffd88a", material="neon",
                 collide=False)
    letters(b, -23.0, 14.0, face - 6.0, "TONIGHT", 1.6, "#1a1a24", "#ff7ac8", "z-", depth=0.1)


# ======================================================================= meta
def _meta(b: ArenaArea) -> None:
    starts = [(30.0, 6.0), (36.0, 12.0), (42.0, 6.0), (30.0, 18.0), (40.0, 18.0), (34.0, 4.0),
              (27.0, 12.0), (41.0, 8.0), (-10.0, 14.0), (12.0, 8.0), (-9.0, 4.0), (10.0, 4.0),
              (-40.0, 13.0), (-28.0, 3.0), (-50.0, 26.0), (-25.0, 20.0)]
    for x, z in starts:
        b.team_spawn("start", x, F1, z, yaw=3.14159 if z < 10 else 0.0)
    g, u = F1, F2
    room(b, "the ballroom", 35.0, g, 12.0, [(24.0, 2.0), (44.0, 22.0), (38.0, -3.0)])
    b.mark("clue", 52.0, F1 + 2.0, 4.0)
    room(b, "the lobby", -10.0, g, 17.0, [(-10.0, -6.0), (11.0, 0.0), (0.0, 25.0), (-12.0, 16.0)])
    room(b, "the Meridian Bar", -40.0, g, 14.0, [(-52.0, -6.0), (-24.0, -6.0), (-52.0, 7.0), (-29.0, 21.0)])
    room(b, "the switchboard room", -50.0, g, -24.0, [(-56.0, -31.0), (-48.0, -14.0)])
    room(b, "the manager's office", -37.0, g, -21.0, [(-35.0, -13.0), (-41.0, -37.0)])
    room(b, "the cloakroom", -15.0, g, -26.0, [(-24.0, -32.0), (-6.0, -18.0)])
    room(b, "the service hall", 10.0, g, -24.0, [(15.0, -30.0), (4.0, -26.0)])
    room(b, "the kitchen", 40.0, g, -18.0, [(28.0, -30.0), (55.0, -20.0)])
    room(b, "the gallery", -17.0, u, 10.0, [(17.0, 0.0), (0.0, 26.6), (-10.0, -7.0)])
    room(b, "the ballroom balcony", 38.0, u, -6.2, [(54.0, -6.2), (24.0, -6.2)])
    room(b, "the guest corridor", -44.0, u, 10.0, [(-53.0, 10.0)])
    room(b, "room 101", -52.0, u, 21.0, [(-46.0, 15.6)])
    room(b, "room 102", -30.0, u, 18.0, [(-30.0, 16.0)])
    room(b, "room 103", -48.0, u, 2.0, [(-46.0, 4.6)])
    room(b, "room 104", -26.0, u, 2.0, [(-34.0, 4.8)])
    room(b, "the writing room", -44.0, u, -24.0, [(-55.0, -36.0), (-34.0, -22.0), (-48.0, -14.0)])
    room(b, "the linen room", -15.0, u, -20.0, [(-26.0, -34.0), (-4.0, -20.0)])
    room(b, "the service landing", 8.0, u, -26.0, [(3.0, -36.0)])
    room(b, "the honeymoon suite", 40.0, u, -24.0, [(30.0, -20.0), (46.0, -32.0)])
    room(b, "the roof", 22.0, TOP, -6.0, [(-10.0, -34.0), (50.0, -10.0), (24.0, 14.0)])
    room(b, "the roof garden", -42.0, TOP, 14.0, [(-50.0, 22.0)])
    room(b, "the fire escape", -56.0, F2, -45.0, [], roam=False)
    room(b, "the street", 0.0, 0.0, 54.0, [(-50.0, 56.0), (50.0, 46.0), (20.0, 58.0)])
    room(b, "the alley", 0.0, 0.0, -56.0, [(-40.0, -66.0), (30.0, -58.0), (-70.0, -50.0)])
    room(b, "the side street", -80.0, 0.0, -10.0, [(-84.0, 20.0), (-82.0, -30.0)])
    room(b, "the motor court", 76.0, F1, -12.0, [(84.0, 12.0), (70.0, -36.0)])
    # the stairs, for the bots: the grand stair, the service stair, the fire escape
    stair(b, (0.0, F1, GRAND[2] + 1.6), (0.0, F2, GRAND[3] - 1.6))
    stair(b, (17.5, F1, WELL[3] + 2.2), (2.6, F2, WELL[2] + 2.5))
    foot, mid, top, lane_a, wall_gap, outer = FIRE
    stair(b, (foot + 2.0, 0.0, (lane_a + wall_gap) / 2.0), (mid - 2.4, F2, (lane_a + wall_gap) / 2.0))
    stair(b, (mid - 2.4, F2, (outer + lane_a) / 2.0), (top + 2.3, TOP, -44.0))
    b.camera(0.0, 40.0, 70.0, 0.0, 14.0, 0.0)
    b.camera(-110.0, 60.0, -100.0, -20.0, 10.0, -20.0)
    b.camera(36.0, 18.0, 26.0, 44.0, 6.0, 4.0)
    b.extra.update({"accent": "#e8c860", "twist": "masks", "twist_every": [40.0, 55.0],
                    "twist_for": 12.0, "twist_warn": 3.0, "round_seconds": 190.0})


def build(b: ArenaArea) -> None:
    rng = random.Random(1933)
    ground(b, ASPHALT, soil="#2a2a2e", material="concrete", studs=False)
    s = Surfaces(b)
    s.reserve(rect(X0, X1, Z0, Z1))
    perimeter(b, 34.0, "#4a3a3a")
    backdrop(b, "city", 0.0, rng, colours=["#1a1a24", "#22222e", "#2a2430"])
    walls = _walls()
    _shell(b, walls)
    _stairs(b)
    _bar(b)
    _lobby(b)
    _ballroom(b)
    _back_rooms(b)
    _upstairs(b)
    _roof(b)
    _fire_escape(b)
    _street(b, s, rng)
    _across(b, rng)
    _meta(b)
