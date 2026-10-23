"""The Museum After Dark -- the city museum, shut for the night: a great
hall with a T. rex under a glass lantern, galleries of mummies, armour,
fossils and rockets downstairs, sculpture, vases, clocks, gems and
paintings upstairs, and the plaza, the hedge maze and the loading yard
outside.

Layout (north is -z; the plaza is to the south)::

    z -150  ============ the loading yard and the dinosaur lawn ============
    z  -84  -- EGYPT ----------|                       |-- FOSSILS ---------
               (the pyramid)   |    THE GREAT HALL     |  (the triceratops)
    z  -44  -- ARMOURY --------|  (the T. rex, under   |-- SPACE -----------
               (the castle)    |   the glass lantern)  |  (the rocket)
    z   -4  -- GIFT SHOP ------|-------- FOYER --------|- CAFE -|- SECURITY
    z   30  ========= windows ====== the portico ====== the terrace ========
         the hedge maze       the plaza and the fountain     the coach park
    z  150  ============================ the street =========================

Upstairs, round the great hall: the sculpture hall and the vase room
(west), the library and the portrait gallery (front, its balcony looking
down on the T. rex), the art gallery, the clock room and the gem vault
(east).  The seekers wait in the security office (the ``pen`` door into
the cafe).  The twist is the night watchman's searchlight sweeping the
great hall (the rules' ``alarm``): move in its beam and the alarm goes off.
"""
from __future__ import annotations

import math
import random
from typing import List, Sequence, Tuple

from ..kit import (ArenaArea, Surfaces, backdrop, car, carve, flight, gable, ground, letters,
                   perimeter, plate, rect, sign_decal, slab, strip_light, wall_sign)
from ...lastlight.kit import van
from . import catalogue as cat
from . import furniture as fx
from .catalogue import B, C, K, S, place, stamp
from .rooms import (DECAL_TILE, PAINT, covering, door_holes, grow, openings, paint, pen_door, shell, skirt,
                    tiled, trim, window)

HALF = (180.0, 150.0)
SKY = {"top": "#0c1630", "horizon": "#3a4e70", "sun": [-0.35, 0.6, 0.55], "clouds": 0.35,
       "tint": "#b4c2ea"}
AMBIENT = "#66749a"
GROUND = "#3e5e3a"
FOG = 640.0

SANDSTONE = "#d8ccb0"
CORNICE = "#ece4d0"
ROOF = "#5a5850"
MARBLE = "#ece8e0"
PAVING = "#a8a498"
LAWN = "#3e6e3a"
HEDGE = "#2e5e2a"
BONE = "#e6dac0"
BONE_DARK = "#c8b896"
STEEL = "#5a5e64"
GOLD = "#d8a838"
ROPE = "#a8202a"
BRASS = "#c8a050"
TRIM = "#f0ead8"
CEILING = "#e8e4dc"
SAND = "#d8b878"
WOOD = "#7a5335"
WOOD_DARK = "#4a3020"

T = 1.2
F1, C1 = 4.0, 19.0            # the main floor stands on a podium above the plaza
F2, C2 = 20.0, 34.4
WALL_TOP = 35.0
X0, X1, Z0, Z1 = -96.0, 96.0, -84.0, 30.0
IX0, IX1, IZ0, IZ1 = X0 + T, X1 - T, Z0 + T, Z1 - T
P = 0.6
XW, XE = -36.0, 36.0           # the wings' walls along the great hall
ZF = -4.0                      # the front rooms' wall
ZW = -44.0                     # between each wing's two galleries
XP = 66.0                      # the security office's wall
HALL = rect(XW + P / 2.0, XE - P / 2.0, IZ0, ZF - P / 2.0)
LANTERN = rect(-22.0, 22.0, -66.0, -22.0)
STAIRS = [(XW + P / 2.0, XW + P / 2.0 + 6.0), (XE - P / 2.0 - 6.0, XE - P / 2.0)]
STAIR_TOP, STAIR_BOTTOM = 6.0, 26.0
WELLS = [rect(a, c, STAIR_TOP, STAIR_BOTTOM + 1.0) for a, c in STAIRS]
PEN = rect(XP + P / 2.0, IX1, ZF + P / 2.0, IZ1)
PEN_DOOR = (8.0, 16.0)
TREX = (0.0, -44.0)

G = F1 + 12.0                  # a gallery doorway's head, downstairs and up
U = F2 + 11.0
GROUND_DOORS = {
    "hall": [(-10.0, 10.0, F1 + 11.0)],
    "xw": [(-66.0, -58.0, G), (-26.0, -18.0, G), (-2.0, 4.0, G)],
    "xe": [(-66.0, -58.0, G), (-26.0, -18.0, G), (-2.0, 4.0, G)],
    "zw_w": [(-72.0, -60.0, G)], "zf_w": [(-72.0, -64.0, G)],
    "zw_e": [(60.0, 72.0, G)], "zf_e": [(44.0, 52.0, G)],
    "xp": [(PEN_DOOR[0], PEN_DOOR[1], F1 + 10.0)],
}
UP_DOORS = {
    "hall": [(-20.0, 20.0, U)],
    "xw": [(-2.0, 4.0, U)], "xe": [(-2.0, 4.0, U)],
    "zw_w": [(-72.0, -60.0, U)], "zf_w": [(-72.0, -64.0, U)],
    "zw_e": [(60.0, 72.0, U)], "zf_e": [(44.0, 52.0, U), (76.0, 84.0, U)],
}
# the upper galleries look down into the great hall through glazed openings
HALL_WINDOWS = [(-72.0, -54.0, F2 + 3.0, F2 + 11.0), (-32.0, -14.0, F2 + 3.0, F2 + 11.0)]

GS, GT = F1 + 3.0, F1 + 12.0   # windows: ground floor sill and top, then upstairs
US, UT = F2 + 3.0, F2 + 11.0
FRONT = [(-8.0, 8.0, 0.0, F1 + 12.0), (58.0, 64.0, 0.0, F1 + 10.0),
         (-84.0, -72.0, GS, GT), (-60.0, -48.0, GS, GT), (-28.0, -20.0, GS, GT),
         (20.0, 28.0, GS, GT), (42.0, 54.0, GS, GT), (78.0, 88.0, GS, GT),
         (-84.0, -72.0, US, UT), (-60.0, -48.0, US, UT), (42.0, 54.0, US, UT),
         (78.0, 88.0, US, UT)]
BACK = [(-60.0, -52.0, 0.0, F1 + 10.0), (52.0, 60.0, 0.0, F1 + 10.0),
        (-86.0, -74.0, GS, GT), (72.0, 84.0, GS, GT),
        (-86.0, -74.0, US, UT), (-56.0, -44.0, US, UT), (-26.0, -14.0, F2 + 2.0, UT),
        (14.0, 26.0, F2 + 2.0, UT), (44.0, 56.0, US, UT), (74.0, 86.0, US, UT)]
WEST = [(-74.0, -56.0, GS, GT), (-32.0, -16.0, GS, GT), (0.0, 8.0, GS, GT),
        (14.0, 20.0, 0.0, F1 + 10.0),
        (-74.0, -56.0, US, UT), (-32.0, -16.0, US, UT), (2.0, 22.0, US, UT)]
EAST = [(-74.0, -56.0, GS, GT), (-32.0, -16.0, GS, GT), (10.0, 22.0, GS, GT),
        (-32.0, -16.0, US, UT), (2.0, 22.0, US, UT)]


def _within(holes: Sequence[Tuple[float, float, float, float]], lo: float, hi: float,
            y0: float, y1: float) -> List[Tuple[float, float, float, float]]:
    """The holes of a wall that open onto a room: along the wall between
    ``lo`` and ``hi`` and on the storey between ``y0`` and ``y1``."""
    return [h for h in holes if h[1] > lo and h[0] < hi and h[3] > y0 and h[2] < y1]


def _flat(b: ArenaArea, x: float, y: float, z: float, w: float, h: float, colour: str,
          decal: str, facing: str, depth: float = 0.2) -> None:
    """A flat thing hung on a wall -- a banner, a starfield, a clock face --
    its decal facing out along ``facing``, its back against the wall."""
    turn = {"z+": 0.0, "z-": 3.14159265, "x+": 1.57079633, "x-": -1.57079633}[facing]
    out = {"z+": (0.0, 1.0), "z-": (0.0, -1.0), "x+": (1.0, 0.0), "x-": (-1.0, 0.0)}[facing]
    b.box([x + out[0] * depth / 2.0, y, z + out[1] * depth / 2.0], [w, h, depth], colour,
          r=[0.0, turn, 0.0], decal=decal)


# ================================================================ the building
def _shell(b: ArenaArea) -> None:
    shell(b, rect(X0, X1, Z0, Z1), 0.0, WALL_TOP, SANDSTONE,
          {"z+": FRONT, "z-": BACK, "x-": WEST, "x+": EAST}, frame=TRIM)
    # the string course at the upper floor and the cornice under the roof
    slab(b, rect(X0 - 0.3, X1 + 0.3, Z1, Z1 + 0.3), F2, 1.0, CORNICE)
    slab(b, rect(X0 - 0.3, X1 + 0.3, Z0 - 0.3, Z0), F2, 1.0, CORNICE)
    slab(b, rect(X0 - 0.3, X0, Z0, Z1), F2, 1.0, CORNICE)
    slab(b, rect(X1, X1 + 0.3, Z0, Z1), F2, 1.0, CORNICE)
    # floors: the podium under the main floor, the doorsteps through the
    # walls, the upper floor (open over the great hall and the stairs), the
    # ceiling and the roof (open under the lantern)
    slab(b, rect(IX0, IX1, IZ0, IZ1), F1, F1, "#b8b0a0")
    for a, c, bottom, _ in FRONT:
        if bottom <= 0.0:
            slab(b, rect(a, c, IZ1, Z1), F1, F1, "#b8b0a0")
    for a, c, bottom, _ in BACK:
        if bottom <= 0.0:
            slab(b, rect(a, c, Z0, IZ0), F1, F1, "#b8b0a0")
    for a, c, bottom, _ in WEST:
        if bottom <= 0.0:
            slab(b, rect(X0, IX0, a, c), F1, F1, "#b8b0a0")
    plate(b, carve(rect(IX0, IX1, IZ0, IZ1), [HALL] + WELLS), F2, F2 - C1, CEILING)
    plate(b, carve(rect(IX0, IX1, IZ0, IZ1), [LANTERN]), WALL_TOP, WALL_TOP - C2, CEILING)
    plate(b, carve(rect(X0 - 0.5, X1 + 0.5, Z0 - 0.5, Z1 + 0.5), [LANTERN]), WALL_TOP + 1.0,
          1.0, ROOF)
    top = WALL_TOP + 1.6
    slab(b, rect(X0 - 1.2, X1 + 1.2, Z1 - 0.5, Z1 + 1.2), top, 0.6, CORNICE)
    slab(b, rect(X0 - 1.2, X1 + 1.2, Z0 - 1.2, Z0 + 0.5), top, 0.6, CORNICE)
    slab(b, rect(X0 - 1.2, X0 + 0.5, Z0 + 0.5, Z1 - 0.5), top, 0.6, CORNICE)
    slab(b, rect(X1 - 0.5, X1 + 1.2, Z0 + 0.5, Z1 - 0.5), top, 0.6, CORNICE)
    _lantern(b)
    # on the roof: vents, air handlers and the flag over the portico
    y = WALL_TOP + 1.0
    for x, z in ((-70.0, -60.0), (-70.0, -20.0), (66.0, -60.0), (66.0, -20.0)):
        b.box([x, y + 1.6, z], [8.0, 3.2, 6.0], "#9aa0a8", material="metal", decal="panels")
        b.cyl([x, y + 3.35, z], [3.4, 0.3, 3.4], "#3a3e44", material="metal")
    for x, z in ((-50.0, 10.0), (50.0, 10.0), (-84.0, 0.0), (84.0, -40.0)):
        b.cyl([x, y + 1.2, z], [1.2, 2.4, 1.2], "#8a9098", material="metal")
        b.cyl([x, y + 2.6, z], [2.0, 0.4, 2.0], "#6a7078", material="metal")
    b.cyl([0.0, 38.0 + 6.0, 38.0], [0.5, 12.0, 0.5], "#e8e4dc", material="metal")
    _flat(b, 2.4, 47.6, 38.0, 4.4, 3.0, "#f4f0e8", "banner_red", "z+", 0.1)


def _lantern(b: ArenaArea) -> None:
    """The glass lantern over the great hall: glazed walls on the roof round
    the opening, a glass top and its ribs."""
    x0, x1, z0, z1 = LANTERN
    y, h = WALL_TOP + 1.0, 6.0
    glass = "#9ec8e8"
    for x in (x0 - 0.4, x1 + 0.4):
        for z in (z0 - 0.4, z1 + 0.4):
            b.box([x, y + h / 2.0, z], [0.8, h, 0.8], STEEL, material="metal")
    for z, out in ((z0 - 0.15, -1.0), (z1 + 0.15, 1.0)):
        b.box([(x0 + x1) / 2.0, y + h / 2.0, z], [x1 - x0, h, 0.3], glass, material="glass",
              alpha=0.45)
        for k in range(1, 6):
            b.box([x0 + k * (x1 - x0) / 6.0, y + h / 2.0, z + out * 0.25], [0.3, h, 0.2], STEEL,
                  material="metal")
    for x, out in ((x0 - 0.15, -1.0), (x1 + 0.15, 1.0)):
        b.box([x, y + h / 2.0, (z0 + z1) / 2.0], [0.3, h, z1 - z0], glass, material="glass",
              alpha=0.45)
        for k in range(1, 6):
            b.box([x + out * 0.25, y + h / 2.0, z0 + k * (z1 - z0) / 6.0], [0.2, h, 0.3], STEEL,
                  material="metal")
    b.box([(x0 + x1) / 2.0, y + h + 0.15, (z0 + z1) / 2.0], [x1 - x0 + 1.6, 0.3, z1 - z0 + 1.6],
          glass, material="glass", alpha=0.45)
    for k in range(7):
        b.box([x0 - 0.8 + k * (x1 - x0 + 1.6) / 6.0, y + h + 0.5, (z0 + z1) / 2.0],
              [0.5, 0.4, z1 - z0 + 1.6], STEEL, material="metal")


def _portico(b: ArenaArea) -> None:
    """The front: a podium of steps up to six columns, the entablature with
    the museum's name, and a stepped pediment."""
    x0, x1, z1 = -31.5, 31.5, 46.0
    slab(b, rect(x0, x1, Z1, z1), F1, F1, "#c8bea8")
    flight(b, "z", z1 + 10.0, z1, x0, x1, 0.0, F1, "#c8bea8", fill=0.0)
    for x in (-27.5, -16.5, -5.5, 5.5, 16.5, 27.5):
        b.box([x, F1 + 0.5, z1 - 3.5], [3.6, 1.0, 3.6], MARBLE)
        b.cyl([x, F1 + 1.0 + 11.0, z1 - 3.5], [2.8, 22.0, 2.8], MARBLE)
        b.box([x, F1 + 23.5, z1 - 3.5], [3.6, 1.0, 3.6], MARBLE)
    slab(b, rect(x0, x1, Z1, z1 - 0.5), 32.0, 4.0, CORNICE)
    gable(b, rect(x0, x1, Z1, z1 - 0.5), 32.0, CORNICE, "z", tiers=4, rise=1.5, overhang=0.0)
    letters(b, 0.0, 30.0, z1 - 0.5, "CITY MUSEUM", 2.8, CORNICE, "#4a4038")
    # banners either side of the doors
    for x, decal in ((-12.5, "banner_red"), (12.5, "banner_blue")):
        _flat(b, x, F1 + 8.0, Z1, 4.0, 10.0, "#f4f0e8", decal, "z+")
    # the terrace outside the cafe, with its own steps down
    slab(b, rect(38.0, 92.0, Z1, 42.0), F1, F1, "#c8bea8")
    flight(b, "z", 50.0, 42.0, 38.0, 92.0, 0.0, F1, "#c8bea8", fill=0.0)
    # the side door's landing, and the loading docks at the back
    slab(b, rect(-104.0, X0, 10.0, 24.0), F1, F1, "#a8a498")
    flight(b, "x", -112.0, -104.0, 10.0, 24.0, 0.0, F1, "#a8a498", fill=0.0)
    slab(b, rect(-70.0, -42.0, -96.0, Z0), F1, F1, "#a8a498")
    flight(b, "x", -78.0, -70.0, -96.0, Z0, 0.0, F1, "#a8a498", fill=0.0)
    slab(b, rect(46.0, 66.0, -92.0, Z0), F1, F1, "#a8a498")
    flight(b, "z", -100.0, -92.0, 46.0, 66.0, 0.0, F1, "#a8a498", fill=0.0)
    for x in (-66.0, -56.0, -46.0):
        b.box([x, F1 - 1.0, -96.3], [1.4, 1.0, 0.6], "#2a2a2a")


def _wall(b: ArenaArea, axis: str, at: float, lo: float, hi: float, y0: float, y1: float,
          colour: str, doors: Sequence[Tuple[float, float, float]] = (),
          windows: Sequence[Tuple[float, float, float, float]] = ()) -> None:
    """An inside wall with doorways (start, end, head) and glazed openings,
    trimmed and framed."""
    holes = [(a, c, y0 - 1.0, head) for a, c, head in doors] + list(windows)
    openings(b, axis, at, P, lo, hi, y0, y1, colour, holes, glass=True)
    for a, c, head in doors:
        trim(b, axis, at, P, a, c, y0, head, TRIM)
    for a, c, sill, top in windows:
        window(b, axis, at, P, a, c, sill, top, TRIM)


def _walls(b: ArenaArea) -> None:
    gd, ud = GROUND_DOORS, UP_DOORS
    inner = "#d8d0c0"
    west, east = XW - P / 2.0, XE + P / 2.0
    for y0, y1, doors in ((F1, C1, gd), (F2, C2, ud)):
        _wall(b, "x", ZF, HALL[0], HALL[1], y0, y1, inner, doors["hall"])
        hall_windows = HALL_WINDOWS if y0 == F2 else []
        _wall(b, "z", XW, IZ0, IZ1, y0, y1, inner, doors["xw"], hall_windows)
        _wall(b, "z", XE, IZ0, IZ1, y0, y1, inner, doors["xe"], hall_windows)
        _wall(b, "x", ZW, IX0, west, y0, y1, inner, doors["zw_w"])
        _wall(b, "x", ZF, IX0, west, y0, y1, inner, doors["zf_w"])
        _wall(b, "x", ZW, east, IX1, y0, y1, inner, doors["zw_e"])
        _wall(b, "x", ZF, east, IX1, y0, y1, inner, doors["zf_e"])
    _wall(b, "z", XP, ZF + P / 2.0, IZ1, F1, C1, "#c8d0d8", gd["xp"])
    pen_door(b, "z", XP, PEN_DOOR[0], PEN_DOOR[1], F1, F1 + 10.0, 0.5, "#6a7a8a")
    wall_sign(b, XP - P / 2.0 - PAINT - 0.35, F1 + 12.4, 12.0, 9.0, 1.6,
              sign_decal("SECURITY", "#f2c230", "#1b2a35", 5.6), "x-", "#f2c230")
    # the balustrade across the portrait gallery's balcony over the hall
    b.box([0.0, F2 + 1.6, ZF], [40.0, 3.2, 0.4], MARBLE)
    b.box([0.0, F2 + 3.4, ZF], [40.0, 0.4, 0.8], CORNICE)


def _paint(b: ArenaArea) -> None:
    """Every room's walls and floor, downstairs and up."""
    gd, ud = GROUND_DOORS, UP_DOORS
    zf, zb = ZF + P / 2.0, ZF - P / 2.0
    wf, wb = ZW + P / 2.0, ZW - P / 2.0
    xw, xe = XW - P / 2.0, XE + P / 2.0

    def dh(doors, y0):
        return door_holes(doors, y0)

    def outer(holes, lo, hi, y0, y1):
        return _within(holes, lo, hi, y0, y1)

    rooms = [
        # name, inner rect, y0, y1, walls, floor, floor decal, holes per side
        ("foyer", rect(xw + P, xe - P, zf, IZ1), F1, C1, "#e8dcc8", "#c8bca8", "tiles",
         {"x-": dh(gd["xw"], F1), "x+": dh(gd["xe"], F1), "z-": dh(gd["hall"], F1),
          "z+": outer(FRONT, -36.0, 36.0, F1, C1)}),
        ("hall", HALL, F1, C2, "#d8d0c0", "#d8d0c0", "tiles",
         {"x-": dh(gd["xw"], F1) + HALL_WINDOWS, "x+": dh(gd["xe"], F1) + HALL_WINDOWS,
          "z-": outer(BACK, -36.0, 36.0, F1, C2),
          "z+": dh(gd["hall"], F1) + dh(ud["hall"], F2)}),
        ("egypt", rect(IX0, xw, IZ0, wb), F1, C1, "#d8bc84", SAND, "",
         {"x-": outer(WEST, IZ0, ZW, F1, C1), "x+": dh(gd["xw"], F1),
          "z-": outer(BACK, IX0, XW, F1, C1), "z+": dh(gd["zw_w"], F1)}),
        ("armoury", rect(IX0, xw, wf, zb), F1, C1, "#9a9aa0", "#7a7a80", "bricks",
         {"x-": outer(WEST, ZW, ZF, F1, C1), "x+": dh(gd["xw"], F1),
          "z-": dh(gd["zw_w"], F1), "z+": dh(gd["zf_w"], F1)}),
        ("shop", rect(IX0, xw, zf, IZ1), F1, C1, "#e8f0f8", "#8a6a4a", "planks",
         {"x-": outer(WEST, ZF, Z1, F1, C1), "x+": dh(gd["xw"], F1),
          "z-": dh(gd["zf_w"], F1), "z+": outer(FRONT, X0, XW, F1, C1)}),
        ("fossils", rect(xe, IX1, IZ0, wb), F1, C1, "#c8d8c0", "#a89a80", "",
         {"x-": dh(gd["xe"], F1), "x+": outer(EAST, IZ0, ZW, F1, C1),
          "z-": outer(BACK, XE, X1, F1, C1), "z+": dh(gd["zw_e"], F1)}),
        ("space", rect(xe, IX1, wf, zb), F1, C1, "#1a2038", "#2a2e40", "",
         {"x-": dh(gd["xe"], F1), "x+": outer(EAST, ZW, ZF, F1, C1),
          "z-": dh(gd["zw_e"], F1), "z+": dh(gd["zf_e"], F1)}),
        ("cafe", rect(xe, XP - P / 2.0, zf, IZ1), F1, C1, "#f0e0c8", "#8a5a3a", "planks",
         {"x-": dh(gd["xe"], F1), "x+": dh(gd["xp"], F1), "z-": dh(gd["zf_e"], F1),
          "z+": outer(FRONT, XE, XP, F1, C1)}),
        ("pen", PEN, F1, C1, "#c8d0d8", "#5a6a7a", "",
         {"x-": dh(gd["xp"], F1), "x+": outer(EAST, ZF, Z1, F1, C1), "z-": [],
          "z+": outer(FRONT, XP, X1, F1, C1)}),
        ("portraits", rect(xw + P, xe - P, zf, IZ1), F2, C2, "#7a2a2a", "#6a4a2a", "planks",
         {"x-": dh(ud["xw"], F2), "x+": dh(ud["xe"], F2), "z-": dh(ud["hall"], F2),
          "z+": outer(FRONT, -36.0, 36.0, F2, C2)}),
        ("library", rect(IX0, xw, zf, IZ1), F2, C2, "#3a5a4a", "#5a3a24", "planks",
         {"x-": outer(WEST, ZF, Z1, F2, C2), "x+": dh(ud["xw"], F2),
          "z-": dh(ud["zf_w"], F2), "z+": outer(FRONT, X0, XW, F2, C2)}),
        ("vases", rect(IX0, xw, wf, zb), F2, C2, "#e0d8c8", "#b8a890", "",
         {"x-": outer(WEST, ZW, ZF, F2, C2), "x+": _within(HALL_WINDOWS, ZW, ZF, F2, C2),
          "z-": dh(ud["zw_w"], F2), "z+": dh(ud["zf_w"], F2)}),
        ("sculpture", rect(IX0, xw, IZ0, wb), F2, C2, "#f0ece4", "#e0dcd4", "tiles",
         {"x-": outer(WEST, IZ0, ZW, F2, C2), "x+": _within(HALL_WINDOWS, IZ0, ZW, F2, C2),
          "z-": outer(BACK, IX0, XW, F2, C2), "z+": dh(ud["zw_w"], F2)}),
        ("art", rect(xe, IX1, zf, IZ1), F2, C2, "#f4f0e8", "#9a7a5a", "planks",
         {"x-": dh(ud["xe"], F2), "x+": outer(EAST, ZF, Z1, F2, C2),
          "z-": dh(ud["zf_e"], F2), "z+": outer(FRONT, XE, X1, F2, C2)}),
        ("clocks", rect(xe, IX1, wf, zb), F2, C2, "#4a3a5a", "#6a5a4a", "planks",
         {"x-": _within(HALL_WINDOWS, ZW, ZF, F2, C2), "x+": outer(EAST, ZW, ZF, F2, C2),
          "z-": dh(ud["zw_e"], F2), "z+": dh(ud["zf_e"], F2)}),
        ("gems", rect(xe, IX1, IZ0, wb), F2, C2, "#202838", "#30384a", "",
         {"x-": _within(HALL_WINDOWS, IZ0, ZW, F2, C2), "x+": outer(EAST, IZ0, ZW, F2, C2),
          "z-": outer(BACK, XE, X1, F2, C2), "z+": dh(ud["zw_e"], F2)}),
    ]
    for name, inner, y0, y1, colour, floor, decal, holes in rooms:
        x0, x1, z0, z1 = inner
        paint(b, "z", x0, 1, z0, z1, y0, y1, colour, holes["x-"])
        paint(b, "z", x1, -1, z0, z1, y0, y1, colour, holes["x+"])
        paint(b, "x", z0, 1, x0 + PAINT, x1 - PAINT, y0, y1, colour, holes["z-"])
        paint(b, "x", z1, -1, x0 + PAINT, x1 - PAINT, y0, y1, colour, holes["z+"])
        cut = []
        if name == "foyer":
            cut = [grow(rect(a, c, STAIR_TOP, STAIR_BOTTOM), 0.1) for a, c in STAIRS]
        elif name == "portraits":
            cut = [grow(w, 0.1) for w in WELLS]
        for piece in carve(inner, cut) if cut else [inner]:
            if decal:
                tiled(b, piece, y0, floor, decal, DECAL_TILE.get(decal, 8.0))
            else:
                covering(b, piece, y0, floor)


def _stairs(b: ArenaArea) -> None:
    """The two grand flights up the sides of the foyer, and the banisters
    round their wells on the gallery above."""
    h = 3.2
    for (x0, x1), (wx0, wx1, wz0, wz1) in zip(STAIRS, WELLS):
        flight(b, "z", STAIR_BOTTOM, STAIR_TOP, x0, x1, F1, F2, MARBLE, fill=F1 - 0.3)
        b.box([(x0 + x1) / 2.0, F1 + 0.06, STAIR_BOTTOM + 1.6], [x1 - x0 - 0.6, 0.04, 3.0], ROPE,
              collide=False)
        if x0 < 0:
            rail_x, end = (wx1 + 0.2, (wx0 + PAINT, wx1))
        else:
            rail_x, end = (wx0 - 0.2, (wx0, wx1 - PAINT))
        b.box([rail_x, F2 + h / 2.0, (wz0 + wz1 + 0.4) / 2.0], [0.4, h, wz1 - wz0 + 0.4], MARBLE)
        b.box([(end[0] + end[1]) / 2.0, F2 + h / 2.0, wz1 + 0.2], [end[1] - end[0], h, 0.4],
              MARBLE)
        for z in (wz0 + 0.4, wz1 + 0.2):
            b.box([rail_x, F2 + h + 0.3, z], [0.8, 0.6, 0.8], BRASS, material="metal")


def _lights(b: ArenaArea) -> None:
    downstairs = [(-66.0, -72.0), (-66.0, -56.0), (-66.0, -32.0), (-66.0, -16.0), (-66.0, 6.0),
                  (-66.0, 20.0), (66.0, -72.0), (66.0, -56.0), (66.0, -32.0), (66.0, -16.0),
                  (50.0, 6.0), (50.0, 20.0), (80.0, 6.0), (80.0, 20.0), (-16.0, 4.0),
                  (16.0, 4.0), (-16.0, 20.0), (16.0, 20.0)]
    for x, z in downstairs:
        strip_light(b, x, z, C1, 10.0, "x", colour="#fff0d0")
    upstairs = [(-76.0, -72.0), (-56.0, -72.0), (-76.0, -56.0), (-56.0, -56.0),
                (-66.0, -34.0), (-66.0, -14.0), (-76.0, 6.0), (-56.0, 6.0), (-66.0, 20.0),
                (76.0, -72.0), (56.0, -72.0), (76.0, -56.0), (56.0, -56.0), (66.0, -34.0),
                (66.0, -14.0), (52.0, 12.0), (80.0, 12.0), (66.0, 22.0), (-14.0, 12.0),
                (14.0, 12.0), (0.0, 22.0)]
    for x, z in upstairs:
        stamp(b, fx.pendant(3.0, shade="#e8d8b8"), x, z, C2)
    # the great hall: lamps hung round the lantern
    for x, z in ((-28.0, -74.0), (28.0, -74.0), (-28.0, -12.0), (28.0, -12.0),
                 (-28.0, -44.0), (28.0, -44.0)):
        stamp(b, fx.pendant(7.0, shade="#c8a050"), x, z, C2)


# ================================================================ the hall
def _trex(b: ArenaArea, cx: float, cz: float) -> None:
    """Sue's cousin: a T. rex skeleton striding to +x on its plinth, mounted
    on steel rods, behind a velvet rope."""
    y = F1
    b.box([cx, y + 0.6, cz], [30.0, 1.2, 12.0], "#4a4a52")
    b.box([cx + 9.0, y + 0.6, cz + 6.05], [5.0, 1.0, 0.1], BRASS,
          decal=sign_decal("T. REX", BRASS, "#2a2018", 5.0))
    base = y + 1.2

    def bone(x, ym, z, w, h, d, c=BONE):
        b.box([cx + x, base + ym, cz + z], [w, h, d], c)

    # the legs: feet, shins, knees, thighs, the pelvis
    for lx, lz in ((-1.6, -2.3), (1.2, 2.3)):
        bone(lx + 1.0, 0.4, lz, 4.2, 0.8, 1.4)
        b.cyl([cx + lx, base + 0.8 + 3.1, cz + lz], [1.0, 6.2, 1.0], BONE)
        b.sphere([cx + lx, base + 7.0, cz + lz], [1.7, 1.7, 1.7], BONE_DARK)
        b.cyl([cx + lx - 0.6, base + 7.0 + 2.9, cz + lz], [1.7, 5.8, 1.7], BONE)
    bone(-1.0, 13.2, 0.0, 5.6, 3.2, 4.0, BONE_DARK)
    # the spine, tail to neck: each vertebra a little off the last
    spine = []
    x, yv = -3.0, 14.6
    for k in range(7):
        spine.append((x, yv, 1.3 if k % 2 else 1.1, 1.2 if k % 2 else 1.0))
        x += 1.5
        yv += 0.2
    spine += [(7.3, 16.5, 1.0, 0.9), (8.5, 17.3, 0.92, 0.82), (9.6, 18.0, 0.86, 0.76)]
    tail = []
    x, yv = -4.4, 14.0
    for k in range(10):
        tail.append((x, yv, 1.2 - k * 0.07, 1.1 - k * 0.06))
        x -= 1.4
        yv -= 0.6
    for x, yv, h, d in spine + tail:
        bone(x, yv, 0.0, 1.7, h, d)
    for x, yv, h, _ in spine[:7]:
        bone(x, yv + h / 2.0 + 0.7, 0.0, 0.3, 1.4, 0.3, BONE_DARK)
    # the ribs, hung from the back
    for (x, yv, h, _), length in zip(spine[3:7], (5.0, 5.6, 5.2, 4.4)):
        top = yv - 0.25
        bone(x, top - 0.175, 0.0, 0.35, 0.35, 4.55)
        for z in (-2.1, 2.1):
            bone(x, top - length / 2.0, z, 0.35, length, 0.35)
    # the little arms
    for z in (-2.1, 2.1):
        bone(6.9, 12.2, z, 1.6, 0.35, 0.35)
        bone(7.6, 11.4, z, 0.35, 1.4, 0.35)
    # the skull: cranium, snout, the open jaw and its teeth
    bone(12.0, 18.4, 0.0, 5.0, 2.8, 2.6)
    bone(15.9, 18.6, 0.0, 3.2, 2.0, 2.0)
    bone(10.8, 16.6, 0.0, 0.8, 1.2, 1.8, BONE_DARK)
    bone(13.6, 16.0, 0.0, 6.4, 0.8, 2.0)
    for k in range(5):
        for z in (-0.8, 0.8):
            bone(14.6 + k * 0.62, 17.3, z, 0.25, 0.6, 0.25, "#f8f4e8")
            bone(12.3 + k * 0.62 + 0.3, 16.65, z, 0.25, 0.5, 0.25, "#f8f4e8")
    for z in (-1.33, 1.33):
        bone(11.6, 18.9, z, 1.0, 0.9, 0.06, "#2a2418")
    # the mount: steel rods from the plinth to the bones
    for x, yv, h, _ in (tail[4], spine[5], spine[8]):
        top = yv - h / 2.0 + 0.1
        b.cyl([cx + x, base + top / 2.0, cz], [0.4, top, 0.4], STEEL, material="metal")
    _ropes(b, [(cx - 19.0, cz - 10.5), (cx + 19.0, cz - 10.5), (cx + 19.0, cz + 10.5),
               (cx - 19.0, cz + 10.5)], F1)


def _ropes(b: ArenaArea, corners: Sequence[Tuple[float, float]], y: float) -> None:
    """A velvet rope on brass posts round a closed loop of corners (every
    side along x or z)."""
    loop = list(corners) + [corners[0]]
    for (xa, za), (xb, zb) in zip(loop, loop[1:]):
        length = abs(xb - xa) + abs(zb - za)
        n = max(1, int(round(length / 7.0)))
        for k in range(n):
            px, pz = xa + (xb - xa) * k / n, za + (zb - za) * k / n
            b.cyl([px, y + 1.5, pz], [0.6, 3.0, 0.6], BRASS, material="metal")
            b.sphere([px, y + 3.2, pz], [0.8, 0.8, 0.8], BRASS, material="metal")
        if xa == xb:
            b.box([xa, y + 2.5, (za + zb) / 2.0], [0.2, 0.25, abs(zb - za)], ROPE)
        else:
            b.box([(xa + xb) / 2.0, y + 2.5, za], [abs(xb - xa), 0.25, 0.2], ROPE)


def _hall(b: ArenaArea) -> None:
    y = F1
    _trex(b, *TREX)
    # pilasters up the walls, banners between them
    hx0, hx1, hz0, hz1 = HALL
    for z in (-76.0, -42.0, -8.0):
        b.box([hx0 + PAINT + 0.6, (F1 + C2) / 2.0, z], [1.2, C2 - F1, 2.4], MARBLE)
        b.box([hx1 - PAINT - 0.6, (F1 + C2) / 2.0, z], [1.2, C2 - F1, 2.4], MARBLE)
    for x in (-30.0, -6.0, 6.0, 30.0):
        b.box([x, (F1 + C2) / 2.0, hz0 + PAINT + 0.6], [2.4, C2 - F1, 1.2], MARBLE)
    for x, decal in ((-18.0, "banner_red"), (18.0, "banner_blue")):
        _flat(b, x, F1 + 10.0, hz0 + PAINT, 5.0, 12.0, "#f4f0e8", decal, "z+")
    for z, decal in ((-50.0, "banner_blue"), (-38.0, "banner_red")):
        _flat(b, hx0 + PAINT, F1 + 22.0, z, 5.0, 10.0, "#f4f0e8", decal, "x+")
        _flat(b, hx1 - PAINT, F1 + 22.0, z, 5.0, 10.0, "#f4f0e8", decal, "x-")
    # the giant ammonite on the back wall
    b.sphere([0.0, F1 + 9.0, hz0 + PAINT + 0.8], [9.0, 9.0, 1.6], "#b89a6a")
    b.sphere([0.0, F1 + 9.0, hz0 + PAINT + 1.2], [6.0, 6.0, 1.6], "#a88a5a")
    b.sphere([0.0, F1 + 9.0, hz0 + PAINT + 1.6], [2.6, 2.6, 1.4], "#987a4a")
    # display cases between the doors, benches facing the rex, ferns
    for x, q in ((hx0 + PAINT + 1.6, 1), (hx1 - PAINT - 1.6, 3)):
        for z in (-50.0, -35.0):
            stamp(b, fx.display_case(5.0, 3.0), x, z, y, q)
    for x in (-12.0, 12.0):
        place(b, "museum_bench", x, -24.0, y, 2)
        place(b, "museum_bench", x, -64.0, y, 0)
    for x, z in ((-31.0, -79.0), (31.0, -79.0), (-31.0, -8.0), (31.0, -8.0)):
        place(b, "fern", x, z, y)
    for x in (-14.0, 14.0):
        place(b, "urn", x, -7.0, y)
    for x, z in ((-8.0, -78.0), (8.0, -78.0)):
        place(b, "stanchion", x, z, y)
    place(b, "dino_egg", 22.0, -79.0, y)
    place(b, "ammonite", -22.0, -79.6, y)
    place(b, "meteorite", 31.5, -30.0, y)


# ================================================================ downstairs
def _foyer(b: ArenaArea) -> None:
    y = F1
    # the information desk, facing the doors
    stamp(b, fx.counter(14.0, body="#6a4a3a", top=MARBLE, doors="#8a6a4a"), 0.0, 12.0, y)
    place(b, "book_stack", -4.0, 12.0, y + fx.COUNTER_TOP)
    place(b, "globe", 5.0, 11.6, y + fx.COUNTER_TOP)
    b.box([0.0, y + 0.06, 22.0], [16.0, 0.04, 9.0], "#8a2a2a", collide=False)
    # the donations box, the map board, the cloakroom rail, benches
    stamp(b, [B(0.0, 0.0, 0.0, 2.4, 3.0, 2.4, "#3a3a40"),
              B(0.0, 3.0, 0.0, 2.6, 2.4, 2.6, "#cfe8ff", m="glass", a=0.4)], -16.0, 26.0, y)
    stamp(b, [B(-2.6, 0.0, 0.0, 0.4, 7.0, 0.4, WOOD_DARK), B(2.6, 0.0, 0.0, 0.4, 7.0, 0.4, WOOD_DARK),
              B(0.0, 3.0, 0.0, 5.2, 4.0, 0.3, "#f4f0e8", dec="sp_coins")], 16.0, 26.0, y, 2)
    for x in (-22.0, 22.0):
        place(b, "potted_plant", x, 1.0, y)
    for x in (-10.0, 10.0):
        place(b, "stanchion", x, 3.0, y)
        place(b, "stanchion", x, 7.0, y)
    place(b, "museum_bench", -20.0, 16.0, y, 1)
    place(b, "museum_bench", 20.0, 16.0, y, 3)
    wall_sign(b, 0.0, y + 13.0, ZF + P / 2.0 + PAINT + 0.35, 16.0, 2.0,
              sign_decal("THE GREAT HALL", "#2a2a30", GOLD, 8.0), "z+", "#2a2a30")


def _egypt(b: ArenaArea) -> None:
    y = F1
    # the stepped pyramid: a model you can climb
    for k, colour in enumerate((SAND, "#cfae6a", SAND, "#cfae6a")):
        size = 16.0 - 4.0 * k
        b.box([-66.0, y + 1.0 + 2.0 * k, -64.0], [size, 2.0, size], colour)
    b.cone([-66.0, y + 9.2, -64.0], [3.2, 2.4, 3.2], GOLD)
    # the sarcophagi on their plinths
    for x in (-86.0, -46.0):
        stamp(b, [B(0.0, 0.0, 0.0, 4.6, 1.4, 8.6, "#3a3430"),
                  B(0.0, 1.4, 0.0, 3.4, 1.6, 7.6, "#c8a040"),
                  B(0.0, 3.0, 0.4, 2.6, 0.3, 5.6, "#2a5a9a"),
                  B(0.0, 3.0, -2.8, 2.4, 0.9, 1.8, GOLD)], x, -74.0, y)
    # obelisks either side of the door from the great hall
    for z in (-70.0, -54.0):
        stamp(b, [B(0.0, 0.0, 0.0, 3.4, 1.0, 3.4, "#a89070"),
                  B(0.0, 1.0, 0.0, 2.4, 10.0, 2.4, "#c8b090"),
                  K(0.0, 11.0, 0.0, 2.4, 2.0, 2.4, GOLD)], -40.0, z, y)
    # the seated pharaoh against the west wall
    stamp(b, [B(0.0, 0.0, 0.0, 6.0, 2.0, 7.0, "#a89070"),
              B(0.0, 2.0, -1.8, 4.6, 6.0, 2.6, "#8a7a5a"),
              B(0.0, 2.0, 0.6, 3.4, 2.6, 3.4, "#c8b090"),
              B(0.0, 4.6, -0.3, 3.0, 4.0, 2.0, "#c8b090"),
              B(0.0, 8.6, -0.4, 1.8, 2.2, 1.8, "#c8b090"),
              B(0.0, 8.0, -1.5, 2.8, 3.0, 1.4, "#2a5a9a"),
              B(-1.15, 6.6, -0.6, 0.6, 2.4, 0.8, "#2a5a9a"),
              B(1.15, 6.6, -0.6, 0.6, 2.4, 0.8, "#2a5a9a"),
              B(0.0, 7.6, 0.75, 0.5, 1.0, 0.5, GOLD)], -88.5, -50.0, y, 1)
    # canopic jars on a table, chests and coffins round the walls
    stamp(b, fx.table(9.0, 3.6, top="#6a4a2a", legs=WOOD_DARK), -80.0, -80.6, y)
    for x in (-82.5, -80.0, -77.5):
        place(b, "canopic_jar", x, -80.6, y + fx.TABLE_TOP, 0)
    place(b, "mummy_case", -38.0, -78.0, y, 3)
    place(b, "mummy_case", -38.0, -48.0, y, 3)
    place(b, "mummy_case", -93.6, -80.0, y, 1)
    place(b, "treasure_chest", -78.0, -48.0, y, 0)
    place(b, "treasure_chest", -54.0, -66.0, y, 1)
    place(b, "canopic_jar", -70.0, -80.8, y)
    place(b, "urn", -66.0, -80.8, y)
    for x, z in ((-92.6, -62.0), (-44.0, -47.0)):
        place(b, "fern", x, z, y)
    stamp(b, fx.display_case(5.0, 3.0), -52.0, -47.0, y, 2)
    stamp(b, [B(0.0, 0.0, 0.0, 1.6, 1.2, 1.0, GOLD), B(0.0, 1.2, 0.0, 1.2, 0.8, 0.8, "#2a5a9a")],
          -52.0, -47.0, y + 3.26)
    for x, decal in ((-66.0, "banner_red"), (-46.0, "banner_blue")):
        _flat(b, x, y + 11.0, IZ0 + PAINT, 4.0, 6.0, SAND, decal, "z+")
    # the painted frieze round the top of the walls, blue over gold
    x0, x1, z0, z1 = IX0 + PAINT, XW - P / 2.0 - PAINT, IZ0 + PAINT, ZW - P / 2.0 - PAINT
    for y0, h, colour in ((C1 - 2.4, 1.0, "#2a5a9a"), (C1 - 3.0, 0.6, GOLD)):
        yc = y0 + h / 2.0
        b.box([x0 + 0.03, yc, (z0 + z1) / 2.0], [0.06, h, z1 - z0], colour, collide=False)
        b.box([x1 - 0.03, yc, (z0 + z1) / 2.0], [0.06, h, z1 - z0], colour, collide=False)
        b.box([(x0 + x1) / 2.0, yc, z0 + 0.03], [x1 - x0 - 0.12, h, 0.06], colour, collide=False)
        b.box([(x0 + x1) / 2.0, yc, z1 - 0.03], [x1 - x0 - 0.12, h, 0.06], colour, collide=False)


def _armoury(b: ArenaArea) -> None:
    y = F1
    # the castle model on its table: walls, towers and a keep to hide in
    cx, cz, top = -66.0, -24.0, y + 2.4
    b.box([cx, y + 1.2, cz], [18.0, 2.4, 14.0], WOOD_DARK)
    stone = "#a8a8a0"
    for z in (cz - 5.0, cz + 5.0):
        if z > cz:
            for a, c in ((cx - 7.0, cx - 1.6), (cx + 1.6, cx + 7.0)):
                b.box([(a + c) / 2.0, top + 1.5, z], [c - a, 3.0, 0.8], stone)
            b.box([cx, top + 2.6, z], [3.2, 0.8, 0.8], stone)
        else:
            b.box([cx, top + 1.5, z], [14.0, 3.0, 0.8], stone)
    for x in (cx - 7.0, cx + 7.0):
        b.box([x, top + 1.5, cz], [0.8, 3.0, 9.2], stone)
    for x in (cx - 7.0, cx + 7.0):
        for z in (cz - 5.0, cz + 5.0):
            b.cyl([x, top + 2.3, z], [2.6, 4.6, 2.6], "#b8b8b0")
            b.cone([x, top + 5.8, z], [3.0, 2.4, 3.0], "#a8302a")
    b.box([cx, top + 3.0, cz - 1.0], [4.0, 6.0, 4.0], "#b8b8b0")
    b.cone([cx, top + 7.2, cz - 1.0], [4.4, 2.4, 4.4], "#a8302a")
    # the knight on his horse
    kx, kz = -86.0, -24.0
    stamp(b, [B(0.0, 0.0, 0.0, 6.0, 2.0, 12.0, "#6a6a70"),
              B(0.0, 2.0, 3.6, 0.8, 3.2, 0.8, "#4a3a2a"), B(0.0, 2.0, -3.6, 0.8, 3.2, 0.8, "#4a3a2a"),
              B(1.4, 2.0, 3.0, 0.8, 3.2, 0.8, "#4a3a2a"), B(-1.4, 2.0, -3.0, 0.8, 3.2, 0.8, "#4a3a2a"),
              B(0.0, 5.2, 0.0, 2.6, 2.8, 8.2, "#5a4a3a"),
              B(0.0, 6.4, 4.6, 1.6, 3.6, 1.8, "#5a4a3a"),
              B(0.0, 9.2, 5.6, 1.4, 1.4, 3.0, "#5a4a3a"),
              B(0.0, 6.0, -4.6, 0.6, 2.4, 1.0, "#2a2018"),
              B(0.0, 8.0, -0.4, 2.0, 3.0, 1.6, "#b8bcc4", m="metal"),
              B(0.0, 11.0, -0.4, 1.4, 1.6, 1.4, "#b8bcc4", m="metal"),
              B(0.0, 12.6, -0.4, 0.4, 0.8, 1.0, "#c8302a"),
              B(1.2, 9.4, 3.0, 0.3, 0.3, 9.0, WOOD)], kx, kz, y, 1)
    # suits of armour round the walls
    for x, z, q in ((-93.4, -36.0, 1), (-93.4, -12.0, 1), (-50.0, -42.4, 0), (-84.0, -42.4, 0),
                    (-52.0, -5.6, 2), (-82.0, -5.6, 2)):
        place(b, "armour", x, z, y, q)
    # shields and banners on the walls, a rack of spears, a cannon
    for z in (-40.0, -36.0, -12.0, -8.0):
        wall_sign(b, IX0 + PAINT + 0.35, y + 11.0, z, 2.6, 3.0, "sigil", "x+", "#8a2a2a")
    for x, decal in ((-52.0, "banner_red"), (-42.0, "banner_blue")):
        _flat(b, x, y + 9.0, -43.7 + PAINT, 4.0, 9.0, "#f4f0e8", decal, "z+")
    rack_z = ZF - P / 2.0 - PAINT - 0.4
    stamp(b, [B(0.0, 0.8, 0.0, 7.0, 0.4, 0.8, WOOD_DARK), B(0.0, 5.2, 0.0, 7.0, 0.4, 0.8, WOOD_DARK),
              B(-3.3, 0.0, 0.0, 0.4, 6.0, 0.8, WOOD_DARK), B(3.3, 0.0, 0.0, 0.4, 6.0, 0.8, WOOD_DARK)]
          + [C(-2.4 + k * 0.96, 0.0, 0.0, 0.24, 9.0, 0.24, "#8a8a90", m="metal") for k in range(6)],
          -58.0, rack_z, y, 2)
    stamp(b, [B(0.0, 0.6, 0.0, 2.4, 1.4, 4.0, WOOD_DARK),
              B(0.0, 2.0, 0.8, 1.2, 1.2, 5.0, "#3a3a3a", m="metal"),
              S(-1.55, 0.0, -0.6, 0.6, 2.4, 2.4, WOOD), S(1.55, 0.0, -0.6, 0.6, 2.4, 2.4, WOOD)],
          -46.0, -36.0, y, 1)
    place(b, "treasure_chest", -40.0, -12.0, y, 3)
    place(b, "treasure_chest", -74.0, -10.0, y, 2)
    stamp(b, fx.display_case(5.0, 3.0), -80.0, -12.0, y)


def _shop(b: ArenaArea) -> None:
    y = F1
    tops = [y + t for t in fx.shelf_tops(3)]
    stock = ["book_stack", "dino_egg", "canopic_jar", "ammonite", "rubber_duck", "toy_block"]
    k = 0
    for gx in (-76.0, -56.0):
        stamp(b, fx.shelf_unit(14.0, 3, colour="#e8e0d0", metal=False), gx, 8.8, y, 2)
        stamp(b, fx.shelf_unit(14.0, 3, colour="#e8e0d0", metal=False), gx, 11.2, y, 0)
        for z, q in ((8.7, 2), (11.3, 0)):
            for level in (0, 1, 2):
                for dx in (-4.4, 0.0, 4.4):
                    k += 1
                    if k % 3 == 0:
                        continue
                    place(b, stock[k % len(stock)], gx + dx, z, tops[level], q)
    # the till by the door into the foyer
    stamp(b, fx.counter(10.0, body="#3a6a8a", top="#f4f4f4", doors="#4a7a9a"), -41.0, 21.0, y, 3)
    place(b, "cash_register", -41.0, 19.0, y + fx.COUNTER_TOP, 3)
    place(b, "plush_dino", -41.0, 24.0, y + fx.COUNTER_TOP, 3)
    # tables of globes, rockets and statuettes by the windows
    for x in (-78.0, -54.0):
        stamp(b, fx.table(9.0, 5.0, top="#c8a878", legs="#8a6a4a"), x, 23.0, y)
        place(b, "globe", x - 2.6, 23.0, y + fx.TABLE_TOP)
        place(b, "toy_rocket", x + 0.2, 23.0, y + fx.TABLE_TOP)
        place(b, "statuette", x + 2.8, 23.0, y + fx.TABLE_TOP)
    # the postcard spinner and the big plush rex
    stamp(b, [C(0.0, 0.0, 0.0, 1.6, 0.3, 1.6, "#3a3a40"), C(0.0, 0.3, 0.0, 0.3, 6.0, 0.3, "#8a8a90"),
              B(0.0, 2.0, 0.0, 2.2, 4.0, 2.2, "#f4f0e8", dec="flowers")], -90.0, -0.6, y)
    for (dx, dy, dz, w, h, d) in ((0.0, 0.0, 0.0, 5.0, 4.6, 4.0), (0.0, 4.2, 1.2, 3.2, 3.0, 3.0),
                                  (0.0, 6.6, 2.2, 2.6, 2.0, 3.2), (0.0, 0.0, -3.0, 2.0, 2.0, 3.6)):
        b.sphere([-88.0 + dx, y + dy + h / 2.0, 22.0 + dz], [w, h, d], "#5aa04a")
    for z in (-2.0, 2.0):
        b.sphere([-88.0 + z * 0.6, y + 0.9, 23.8], [1.4, 1.8, 1.4], "#4a8a3a")
    place(b, "plush_dino", -46.0, -1.0, y, 1)
    place(b, "teddy_bear", -48.0, 3.6, y, 1)
    place(b, "bin", -92.8, 26.6, y)
    wall_sign(b, -66.0, y + 13.0, IZ1 - PAINT - 0.35, 12.0, 2.0,
              sign_decal("GIFT SHOP", "#3a6a8a", "#ffffff", 6.0), "z-", "#3a6a8a")


def _triceratops(b: ArenaArea, cx: float, cz: float) -> None:
    """A triceratops skeleton facing -x, on a low plinth."""
    y = F1
    b.box([cx, y + 0.5, cz], [22.0, 1.0, 10.0], "#4a4a52")
    base = y + 1.0

    def bone(x, ym, z, w, h, d, c=BONE):
        b.box([cx + x, base + ym, cz + z], [w, h, d], c)

    for lx in (-4.6, 4.2):
        for lz in (-2.2, 2.2):
            b.cyl([cx + lx, base + 2.6, cz + lz], [1.2, 5.2, 1.2], BONE)
            bone(lx - 0.3, 0.2, lz, 1.8, 0.4, 1.4, BONE_DARK)
    bone(4.2, 6.4, 0.0, 3.6, 2.6, 4.8, BONE_DARK)
    bone(-4.6, 6.0, 0.0, 2.8, 2.0, 4.6, BONE_DARK)
    for k in range(8):
        x = -5.4 + k * 1.45
        bone(x, 7.6 + (0.15 if k % 2 else 0.0), 0.0, 1.7, 1.0 + 0.1 * (k % 2), 0.9 + 0.1 * (k % 2))
    for k in range(5):
        x = 6.0 + k * 1.3
        bone(x, 7.2 - k * 0.55, 0.0, 1.5, 0.9 - k * 0.1, 0.8 - k * 0.08)
    for x in (-3.0, -1.4, 0.2, 1.8):
        bone(x, 7.0, 0.0, 0.3, 0.3, 4.4)
        for z in (-2.05, 2.05):
            bone(x, 5.2, z, 0.3, 3.6, 0.3)
    # the head: the frill, the skull, three horns, the beak
    bone(-7.0, 7.8, 0.0, 0.6, 5.0, 6.2, BONE_DARK)
    bone(-8.6, 7.2, 0.0, 3.0, 2.2, 2.4)
    bone(-10.6, 6.8, 0.0, 1.4, 1.2, 1.4)
    b.cone([cx - 9.0, base + 9.3, cz - 0.8], [0.6, 1.8, 0.6], "#f8f4e8")
    b.cone([cx - 9.0, base + 9.3, cz + 0.8], [0.6, 1.8, 0.6], "#f8f4e8")
    b.cone([cx - 10.4, base + 7.9, cz], [0.5, 1.0, 0.5], "#f8f4e8")
    _ropes(b, [(cx - 14.0, cz - 8.0), (cx + 14.0, cz - 8.0), (cx + 14.0, cz + 8.0),
               (cx - 14.0, cz + 8.0)], F1)


def _fossils(b: ArenaArea) -> None:
    y = F1
    _triceratops(b, 70.0, -64.0)
    # the bear on its rock
    b.box([86.0, y + 1.2, -50.0], [8.0, 2.4, 6.0], "#6a6258")
    for (dx, yy, dz, w, h, d, c) in ((0.0, 2.4, 0.0, 4.0, 4.6, 3.4, "#5a3a24"),
                                      (0.0, 6.6, -0.4, 2.6, 2.4, 2.4, "#5a3a24"),
                                      (0.0, 7.0, -1.6, 1.2, 1.0, 1.2, "#3a2414")):
        b.sphere([86.0 + dx, y + yy + h / 2.0, -50.0 + dz], [w, h, d], c)
    for dx in (-0.9, 0.9):
        b.sphere([86.0 + dx, y + 9.0 + 0.4, -50.0 - 0.2], [0.8, 0.8, 0.6], "#5a3a24")
    # the nest of eggs, the meteorite, the totem poles
    for k in range(8):
        a = k * 0.785398
        b.box([44.0 + 3.4 * math.cos(a), y + 0.5, -74.0 + 3.4 * math.sin(a)],
              [1.4 + (k % 2) * 0.2, 1.0 + (k % 3) * 0.15, 1.4], "#7a6a58")
    place(b, "dino_egg", 43.4, -74.6, y)
    place(b, "dino_egg", 45.2, -73.2, y, 1)
    stamp(b, fx.plinth(3.0, 2.0), 92.0, -79.0, y)
    place(b, "meteorite", 92.0, -79.0, y + 2.2)
    place(b, "totem", 92.8, -64.0, y, 3)
    place(b, "totem", 40.0, -47.0, y, 1)
    for x in (52.0, 78.0):
        stamp(b, fx.display_case(5.0, 3.0), x, -46.8, y, 2)
    for x, kind in ((52.0, "ammonite"), (78.0, "dino_egg")):
        place(b, kind, x, -50.6, y, 2)
    place(b, "ammonite", 38.6, -60.0, y, 1)
    place(b, "fern", 92.8, -48.0, y)
    place(b, "fern", 38.8, -81.0, y)
    stamp(b, fx.table(8.0, 4.0, top="#6a5a4a", legs=WOOD_DARK), 66.0, -80.6, y)
    place(b, "ammonite", 64.0, -80.6, y + fx.TABLE_TOP)
    place(b, "dino_egg", 68.0, -80.6, y + fx.TABLE_TOP)


def _space(b: ArenaArea) -> None:
    y = F1
    zb = ZF - P / 2.0 - PAINT
    # the starfield over the front wall
    _flat(b, 74.0, y + 8.0, zb, 36.0, 12.0, "#0a0e1a", "starfield", "z-", 0.1)
    # the rocket
    rx, rz = 88.0, -36.0
    for dx, dz in ((-2.4, 0.0), (2.4, 0.0), (0.0, -2.4), (0.0, 2.4)):
        b.box([rx + dx, y + 1.6, rz + dz], [0.4 if dx else 1.6, 3.2, 1.6 if dx else 0.4], "#c8302a")
    b.cyl([rx, y + 0.4 + 5.5, rz], [3.6, 11.0, 3.6], "#f4f4f4", material="metal")
    b.cyl([rx, y + 7.0, rz], [3.8, 0.8, 3.8], "#2a4a9a")
    b.cone([rx, y + 12.9, rz], [3.6, 3.0, 3.6], "#c8302a")
    # the lunar lander
    lx, lz = 60.0, -26.0
    for dx in (-3.2, 3.2):
        for dz in (-3.2, 3.2):
            b.cyl([lx + dx, y + 1.5, lz + dz], [0.4, 3.0, 0.4], "#b8bcc4", material="metal")
            b.cyl([lx + dx, y + 0.1, lz + dz], [1.4, 0.2, 1.4], "#b8bcc4", material="metal")
    b.box([lx, y + 4.5, lz], [6.6, 3.0, 6.6], "#d8b040", decal="ea25_foil")
    b.box([lx, y + 7.5, lz], [4.0, 3.0, 4.0], "#c8ccd4", material="metal")
    b.cyl([lx + 1.2, y + 9.8, lz], [0.2, 1.6, 0.2], "#8a8a90")
    # the planets, hung from the ceiling
    for px, pz, size, colour in ((50.0, -12.0, 4.6, "#d89a5a"), (72.0, -14.0, 3.0, "#3a7ad8"),
                                 (80.0, -24.0, 2.4, "#c8502a"), (46.0, -38.0, 3.6, "#e8d8a8")):
        cy = C1 - 4.0 - size / 2.0
        b.sphere([px, cy, pz], [size, size, size], colour)
        b.cyl([px, (cy + C1) / 2.0, pz], [0.12, C1 - cy, 0.12], "#2a2a2a", collide=False)
    b.cyl([46.0, C1 - 4.0 - 1.8, -38.0], [7.0, 0.2, 7.0], "#c8b888")
    # the astronaut, the telescope, moon rocks and globes
    stamp(b, fx.plinth(3.4, 1.6), 76.0, zb - 2.2, y)
    stamp(b, [B(-0.5, 0.0, 0.0, 0.9, 2.6, 1.0, "#f4f4f4"), B(0.5, 0.0, 0.0, 0.9, 2.6, 1.0, "#f4f4f4"),
              B(0.0, 2.6, 0.0, 2.4, 2.8, 1.6, "#f4f4f4"), B(0.0, 2.8, -1.0, 1.8, 2.2, 0.4, "#c8ccd4"),
              S(0.0, 5.3, 0.0, 1.8, 1.8, 1.8, "#f4f4f4"), B(0.0, 5.7, 0.7, 1.2, 0.8, 0.5, "#d8a838",
                                                             m="glass")],
          76.0, zb - 2.2, y + 1.8, 2)
    stamp(b, [C(-0.8, 0.0, 0.6, 0.2, 4.0, 0.2, "#3a3a3a"), C(0.8, 0.0, 0.6, 0.2, 4.0, 0.2, "#3a3a3a"),
              C(0.0, 0.0, -0.8, 0.2, 4.0, 0.2, "#3a3a3a"), B(0.0, 4.0, 0.0, 1.2, 0.4, 1.2, "#3a3a3a"),
              B(0.0, 4.4, 0.6, 0.9, 0.9, 4.0, "#e8e8e8", m="metal")], 44.0, -14.0, y)
    stamp(b, fx.table(8.0, 4.0, top="#2a2e40", legs="#1a1e2a"), 62.0, zb - 2.2, y)
    place(b, "meteorite", 60.0, zb - 2.2, y + fx.TABLE_TOP)
    place(b, "globe", 64.0, zb - 2.2, y + fx.TABLE_TOP)
    place(b, "toy_rocket", 92.6, -8.0, y)
    place(b, "globe", 40.0, -40.0, y)
    place(b, "meteorite", 92.0, -16.0, y, 1)


def _cafe(b: ArenaArea) -> None:
    y = F1
    zb = ZF + P / 2.0 + PAINT
    stamp(b, fx.counter(9.0, body="#7a4a2a", top="#e8e4dc", doors="#9a6a4a"), 59.5, zb + 1.8, y)
    b.box([63.0, y + fx.COUNTER_TOP + 1.4, zb + 1.2], [1.8, 2.8, 1.4], "#3a3a3a", material="metal")
    place(b, "teapot", 56.0, zb + 1.8, y + fx.COUNTER_TOP)
    place(b, "cookie_jar", 59.0, zb + 1.8, y + fx.COUNTER_TOP)
    wall_sign(b, 59.5, y + 10.0, zb + 0.35, 8.0, 3.0,
              sign_decal("CAFE", "#3a2a1a", "#f4e0b0", 2.6), "z+", "#3a2a1a")
    for tx, tz in ((44.0, 10.0), (44.0, 22.0), (55.0, 22.0)):
        stamp(b, fx.table(4.4, 4.4, top="#f4f0e8", legs="#3a3a3a"), tx, tz, y)
        place(b, "dining_chair", tx - 3.4, tz, y, 1)
        place(b, "dining_chair", tx + 3.4, tz, y, 3)
    place(b, "teapot", 44.0, 22.0, y + fx.TABLE_TOP)
    place(b, "potted_plant", 39.0, 27.0, y)
    place(b, "potted_plant", 63.6, 27.0, y)
    place(b, "bin", 39.0, 14.0, y)


def _security(b: ArenaArea) -> None:
    """The security office: the seekers' pen."""
    y = F1
    x0, x1, z0, z1 = PEN
    stamp(b, fx.counter(14.0, body="#3a4a5a", top="#2a2a2a", doors="#4a5a6a"), 81.0, z0 + PAINT + 1.8,
          y)
    for x in (75.0, 81.0, 87.0):
        b.box([x, y + 8.0, z0 + PAINT + 0.2], [5.0, 3.4, 0.4], "#1a2a2a", decal="neongrid")
    for k in range(3):
        b.box([x1 - PAINT - 1.2, y + 4.0, 1.6 + k * 2.9], [2.4, 8.0, 2.8], "#6a7a8a",
              material="metal")
    place(b, "dining_chair", 78.0, z0 + 5.2, y, 2, hide=False)
    place(b, "dining_chair", 84.0, z0 + 5.2, y, 2, hide=False)
    place(b, "water_cooler", 92.6, 26.6, y, hide=False)


# ================================================================ upstairs
def _portraits(b: ArenaArea) -> None:
    y = F2
    for x in (-21.0, -7.0, 7.0, 21.0):
        stamp(b, fx.painting(6.0, 7.0, "portrait"), x, IZ1 - PAINT, y + 4.0, 2)
    for x in (-27.0, 27.0):
        stamp(b, fx.painting(4.0, 5.0, "portrait"), x, ZF + P / 2.0 + PAINT, y + 5.0)
    place(b, "museum_bench", -8.0, 16.0, y, 0)
    place(b, "museum_bench", 8.0, 16.0, y, 0)
    stamp(b, fx.plinth(2.6, 3.0), 0.0, 22.0, y)
    place(b, "marble_bust", 0.0, 22.0, y + 3.2)
    for x in (-18.0, 18.0):
        stamp(b, fx.plinth(2.4, 2.4), x, 4.0, y)
        place(b, "statuette", x, 4.0, y + 2.6)
    place(b, "stanchion", -4.0, 6.0, y)
    place(b, "stanchion", 4.0, 6.0, y)
    place(b, "fern", -26.0, 27.0, y)
    place(b, "fern", 26.0, 27.0, y)


def _library(b: ArenaArea) -> None:
    y = F2
    zb = ZF + P / 2.0 + PAINT
    for x in (-87.0, -56.0, -46.0):
        stamp(b, fx.bookcase(8.0, 11.0, 2.0, seed=int(-x)), x, zb + 1.0, y)
    for z in (13.0, 23.0):
        stamp(b, fx.bookcase(8.0, 11.0, 2.0, seed=int(z)), XW - P / 2.0 - PAINT - 1.0, z, y, 3)
    stamp(b, fx.table(12.0, 6.0, top="#5a3a24", legs="#3a2414"), -68.0, 12.0, y)
    chart = b.box([-68.0, y + fx.TABLE_TOP + 0.02, 12.0], [9.0, 0.04, 4.4], "#e8d8b0",
                  collide=False, decal="canvas")
    chart["dw"] = 1
    place(b, "book_stack", -72.5, 10.6, y + fx.TABLE_TOP)
    place(b, "globe", -63.6, 13.0, y + fx.TABLE_TOP)
    for x in (-74.0, -62.0):
        place(b, "dining_chair", x, 7.0, y, 0)
        place(b, "dining_chair", x, 17.0, y, 2)
    place(b, "armchair", -86.0, 22.0, y, 1)
    place(b, "armchair", -48.0, 22.0, y, 3)
    place(b, "floor_lamp", -91.6, 27.0, y)
    place(b, "floor_lamp", -42.0, 6.0, y)
    place(b, "globe", -86.0, 12.0, y)
    place(b, "book_stack", -52.0, 27.4, y)


def _vases(b: ArenaArea) -> None:
    y = F2
    kinds = ["vase", "urn", "amphora"]
    k = 0
    for x in (-84.0, -70.0, -56.0, -44.0):
        for z in (-34.0, -22.0, -12.0):
            stamp(b, fx.plinth(2.6, 3.0), x, z, y)
            place(b, kinds[k % 3], x, z, y + 3.2, k % 4)
            k += 1
    stamp(b, fx.display_case(5.0, 3.0), IX0 + PAINT + 1.6, -40.0, y, 1)
    place(b, "vase", -92.6, -8.0, y)
    place(b, "amphora", -40.0, -41.6, y)
    place(b, "fern", -92.8, -26.0 + 0.0, y)


def _sculpture(b: ArenaArea) -> None:
    y = F2
    # the discus thrower
    stamp(b, fx.plinth(5.0, 2.0), -66.0, -64.0, y)
    stamp(b, [B(-0.7, 0.0, 0.0, 0.9, 4.4, 1.0, MARBLE), B(0.7, 0.0, 0.6, 0.9, 4.4, 1.0, MARBLE),
              B(0.0, 4.4, 0.0, 2.4, 3.4, 1.4, MARBLE), S(0.0, 7.8, 0.0, 1.4, 1.6, 1.4, MARBLE),
              B(-2.4, 6.2, 0.0, 2.6, 0.7, 0.7, MARBLE), B(2.2, 5.2, 0.0, 2.2, 0.7, 0.7, MARBLE),
              S(3.5, 5.0, 0.0, 1.4, 1.4, 0.4, "#b8a888")], -66.0, -64.0, y + 2.2)
    # the thinker
    stamp(b, fx.plinth(4.0, 2.4), -46.0, -76.0, y)
    stamp(b, [B(0.0, 0.0, 0.0, 3.0, 1.6, 2.6, "#5a6a5a"), B(0.0, 1.6, -0.4, 2.0, 3.0, 1.6, "#4a5a4a"),
              B(-0.5, 1.6, 0.9, 0.8, 1.4, 1.8, "#4a5a4a"), B(0.5, 1.6, 0.9, 0.8, 1.4, 1.8, "#4a5a4a"),
              S(0.0, 4.4, 0.2, 1.4, 1.6, 1.4, "#4a5a4a"), B(0.0, 3.2, 0.6, 0.6, 1.4, 0.6, "#4a5a4a")],
          -46.0, -76.0, y + 2.6, 2)
    # a colonnade down the room
    for x in (-82.0, -50.0):
        for z in (-72.0, -56.0):
            b.cyl([x, (F2 + C2) / 2.0, z], [2.4, C2 - F2, 2.4], MARBLE)
    for x, z in ((-92.4, -78.0), (-92.4, -50.0), (-60.0, -81.0), (-72.0, -81.0)):
        stamp(b, fx.plinth(2.4, 3.0), x, z, y)
        place(b, "marble_bust", x, z, y + 3.2, 1 if x < -90 else 0)
    place(b, "statuette", -40.0, -80.0, y)
    place(b, "statuette", -40.0, -48.0, y)
    place(b, "fern", -86.0, -47.0, y)


def _art(b: ArenaArea) -> None:
    y = F2
    zb = ZF + P / 2.0 + PAINT
    for x, decal in ((64.0, "sunrise"), (91.0, "flowers")):
        stamp(b, fx.painting(8.0 if x < 90 else 4.0, 6.0, decal), x, zb, y + 4.0)
    for z, decal in ((12.0, "harvest_moon"), (22.0, "sunset_grid")):
        stamp(b, fx.painting(6.0, 5.0, decal), XE + P / 2.0 + PAINT, z, y + 4.0, 1)
    stamp(b, fx.painting(10.0, 6.0, "starfield"), 66.0, IZ1 - PAINT, y + 4.0, 2)
    # a free-standing wall down the middle, a picture on each face
    b.box([66.0, y + 5.0, 12.0], [14.0, 10.0, 0.8], "#e8e0d0")
    stamp(b, fx.painting(8.0, 5.0, "portrait"), 66.0, 12.4, y + 3.0)
    stamp(b, fx.painting(8.0, 5.0, "flowers"), 66.0, 11.6, y + 3.0, 2)
    for x in (56.0, 76.0):
        place(b, "museum_bench", x, 4.0, y, 2)
    place(b, "museum_bench", 66.0, 21.0, y, 0)
    for x, z in ((44.0, 4.0), (88.0, 6.0)):
        stamp(b, fx.plinth(2.4, 2.4), x, z, y)
        place(b, "statuette", x, z, y + 2.6)
    # the easel
    stamp(b, [B(-1.4, 0.0, 0.0, 0.3, 7.0, 0.3, WOOD), B(1.4, 0.0, 0.0, 0.3, 7.0, 0.3, WOOD),
              B(0.0, 0.0, -1.4, 0.3, 6.6, 0.3, WOOD), B(0.0, 2.6, 0.2, 3.6, 0.3, 0.6, WOOD),
              B(0.0, 2.9, 0.25, 3.4, 3.0, 0.2, "#f4f0e8", dec="canvas")], 86.0, 22.0, y, 3)
    place(b, "floor_lamp", 92.6, 27.0, y)
    place(b, "vase", 40.0, 27.0, y)


def _clocks(b: ArenaArea) -> None:
    y = F2
    _flat(b, 64.0, y + 7.5, ZF - P / 2.0 - PAINT, 9.0, 9.0, "#f4ecd8", "clockface", "z-", 0.4)
    for x, z, q in ((48.0, -42.4, 0), (84.0, -42.4, 0), (93.4, -10.0, 3), (93.4, -38.0, 3),
                    (56.0, -5.6, 2), (88.0, -5.6, 2)):
        place(b, "grandfather_clock", x, z, y, q)
    # the orrery
    stamp(b, [C(0.0, 0.0, 0.0, 6.0, 2.8, 6.0, WOOD_DARK), C(0.0, 2.8, 0.0, 0.4, 2.2, 0.4, BRASS, m="metal"),
              S(0.0, 4.6, 0.0, 1.6, 1.6, 1.6, "#ffd86a"), B(1.4, 4.0, 0.0, 2.8, 0.2, 0.2, BRASS, m="metal"),
              S(2.8, 4.2, 0.0, 0.8, 0.8, 0.8, "#3a7ad8"), B(0.0, 3.6, -1.9, 0.2, 0.2, 3.8, BRASS, m="metal"),
              S(0.0, 3.8, -3.6, 1.0, 1.0, 1.0, "#c8502a")], 66.0, -24.0, y)
    for x in (52.0, 80.0):
        stamp(b, fx.display_case(5.0, 3.0), x, -24.0, y)
    place(b, "treasure_chest", 52.0, -16.0, y, 0)
    place(b, "globe", 80.0, -16.0, y)
    place(b, "radio", 42.0, -10.0, y, 1)


def _gems(b: ArenaArea) -> None:
    y = F2
    rng = random.Random(311)
    colours = ["#b05ae8", "#5ad8e8", "#e85aa0", "#8ae85a", "#e8c85a"]
    for gx, gz, size in ((66.0, -64.0, 10.0), (46.0, -76.0, 5.0), (86.0, -52.0, 5.0),
                         (84.0, -78.0, 6.0)):
        b.box([gx, y + 1.0, gz], [size, 2.0, size * 0.8], "#4a4458")
        n = int(size)
        for k in range(n):
            colour = colours[(k + int(size)) % len(colours)]
            w = round(rng.uniform(0.6, 1.2), 2)
            h = round(rng.uniform(1.6, size * 0.6), 2)
            dx = (k - (n - 1) / 2.0) * (size - 1.4) / max(1, n - 1)
            dz = rng.uniform(-size * 0.25, size * 0.25)
            b.box([gx + dx, y + 2.0 + h / 2.0, gz + dz], [w, h, w], colour, material="glass",
                  alpha=0.75)
    for x in (50.0, 82.0):
        stamp(b, fx.display_case(5.0, 3.0), x, -46.8, y, 2)
    place(b, "treasure_chest", 92.0, -64.0, y, 3)
    place(b, "treasure_chest", 40.0, -60.0, y, 1)
    place(b, "vase", 58.0, -81.4, y)
    place(b, "urn", 74.0, -81.4, y)


# ================================================================ outside
def _plaza(b: ArenaArea, s: Surfaces) -> None:
    # the lawns either side of the plaza, the paving, the street
    for x0, x1 in ((-118.0, -44.0), (44.0, 118.0)):
        s.lay(rect(x0, x1, 62.0, 112.0), 0.25, LAWN)
    s.lay(rect(-HALF[0], HALF[0], 30.0, 122.0), 0.2, PAVING)
    s.lay(rect(-HALF[0], HALF[0], 122.0, 126.0), 0.35, "#b8b4a8")
    s.lay(rect(-HALF[0], HALF[0], 126.0, HALF[1]), 0.1, "#3a3e44")
    for x in range(-170, 175, 20):
        b.box([x, 0.11, 138.0], [10.0, 0.02, 0.6], "#e8e8e0", collide=False)
    rng = random.Random(4471)
    for x in range(-160, 165, 16):
        if rng.random() < 0.4:
            continue
        car(b, x, 131.0, "x", colour=rng.choice(["#c8402a", "#3a6ab0", "#e8e8e8", "#2a2a2a",
                                                 "#3a8a5a"]), y=0.1, length=10.0)
    # the fountain
    fy = 0.2
    b.cyl([0.0, fy + 0.8, 88.0], [26.0, 1.6, 26.0], "#b8b0a0")
    b.cyl([0.0, fy + 1.625, 88.0], [23.0, 0.05, 23.0], "#3a6a9a", material="glass", alpha=0.8,
          collide=False)
    b.cyl([0.0, fy + 1.6 + 2.0, 88.0], [3.6, 4.0, 3.6], "#b8b0a0")
    b.cyl([0.0, fy + 5.6 + 0.4, 88.0], [10.0, 0.8, 10.0], "#b8b0a0")
    b.cyl([0.0, fy + 6.4 + 1.0, 88.0], [1.2, 2.0, 1.2], "#b8b0a0")
    b.sphere([0.0, fy + 8.4 + 0.7, 88.0], [1.6, 1.4, 1.6], GOLD)
    # trees, lamps, benches and banners round the lawns
    for x, z in ((-104.0, 72.0), (-60.0, 100.0), (-96.0, 104.0), (64.0, 74.0), (100.0, 100.0),
                 (56.0, 104.0)):
        b.tree(x, z, 0.25, 1.15, leaf_c="#2e6a34")
    for x in (-40.0, 40.0):
        for z in (60.0, 84.0, 108.0):
            stamp(b, fx.lamp_stand(12.0), x, z, 0.2)
    for x in (-120.0, 120.0):
        for z in (40.0, 76.0):
            stamp(b, fx.lamp_stand(12.0), x, z, 0.2)
    for x, z, q in ((-24.0, 70.0, 1), (24.0, 70.0, 3), (-24.0, 106.0, 1), (24.0, 106.0, 3)):
        stamp(b, fx.bench(6.0, wood="#6a4a2a"), x, z, 0.2, q)
    for x, decal in ((-30.0, "banner_red"), (30.0, "banner_blue"), (-64.0, "banner_blue"),
                     (64.0, "banner_red")):
        b.cyl([x, 0.2 + 8.0, 58.0], [0.5, 16.0, 0.5], "#3a3a40", material="metal")
        _flat(b, x, 10.0, 58.25, 3.0, 8.0, "#f4f0e8", decal, "z+", 0.15)
    # the lions at the foot of the steps
    for x in (-36.0, 36.0):
        stamp(b, [B(0.0, 0.0, 0.0, 4.0, 2.4, 8.0, "#c8bea8"),
                  B(0.0, 2.4, -0.6, 2.6, 2.4, 5.4, "#b8ae98"),
                  B(0.0, 4.8, 2.0, 2.8, 2.8, 2.4, "#b8ae98"),
                  B(0.0, 4.6, 3.4, 1.6, 1.4, 0.8, "#a89e88")], x, 52.0, 0.2)
    # the ticket kiosk and the hot dog cart
    stamp(b, [B(0.0, 0.0, 0.0, 6.0, 6.0, 5.0, "#8a2a2a"), B(0.0, 6.0, 0.0, 7.0, 0.6, 6.0, "#f4f0e8"),
              B(0.0, 2.8, 2.55, 4.0, 2.4, 0.1, "#cfe8ff", m="glass", a=0.5)], -70.0, 46.0, 0.2)
    stamp(b, [B(0.0, 1.0, 0.0, 5.0, 2.6, 3.0, "#f4f4f4"), B(0.0, 3.6, 0.0, 5.4, 0.3, 3.4, "#d8402a"),
              C(-2.4, 0.0, 1.6, 0.2, 7.0, 0.2, "#8a8a90"), C(2.4, 0.0, -1.6, 0.2, 7.0, 0.2, "#8a8a90"),
              B(0.0, 7.0, 0.0, 6.0, 0.3, 4.4, "#f2c230"),
              S(-1.8, 0.0, 1.6, 0.4, 1.4, 1.4, "#2a2a2a"), S(1.8, 0.0, 1.6, 0.4, 1.4, 1.4, "#2a2a2a")],
          70.0, 54.0, 0.2, 1)
    # the things a hider can be out here
    for x, z, kind, q in ((-8.0, 70.0, "bin", 0), (8.0, 106.0, "bin", 0), (-52.0, 54.0, "fern", 0),
                          (52.0, 54.0, "fern", 0), (-30.0, 116.0, "stanchion", 0),
                          (30.0, 116.0, "stanchion", 0), (-120.0, 56.0, "bin", 0),
                          (120.0, 60.0, "traffic_cone", 0), (-14.0, 114.0, "urn", 0),
                          (14.0, 114.0, "urn", 0), (96.0, 116.0, "bin", 0)):
        place(b, kind, x, z, 0.2, q)
    for x, z in ((-80.0, 90.0), (80.0, 88.0)):
        place(b, "statuette", x, z, 0.25)
    place(b, "garden_gnome", -110.0, 92.0, 0.25)
    place(b, "birdbath", 92.0, 80.0, 0.25)
    # the cafe terrace: tables and parasols
    for tx in (46.0, 72.0, 84.0):
        stamp(b, fx.table(4.4, 4.4, top="#f4f0e8", legs="#3a3a3a"), tx, 36.0, F1)
        b.cyl([tx, F1 + fx.TABLE_TOP + 2.5, 36.0], [0.3, 5.0, 0.3], "#8a8a90")
        b.cone([tx, F1 + fx.TABLE_TOP + 5.0 + 0.8, 36.0], [6.0, 1.6, 6.0], "#2a6a8a")
        place(b, "dining_chair", tx - 3.6, 36.0, F1, 1)
    place(b, "potted_plant", 90.0, 40.0, F1)


def _maze(b: ArenaArea, s: Surfaces) -> None:
    """The hedge maze west of the museum: six by six cells of tall clipped
    hedge (too tall to climb), a statue in its heart."""
    x0, z0, cell, n = -170.0, -70.0, 10.0, 6
    s.lay(rect(x0 - 4.0, x0 + n * cell + 4.0, z0 - 4.0, z0 + n * cell + 4.0), 0.2, "#c8bca4")
    rng = random.Random(1907)
    # carve a maze by a depth-first walk; every wall starts up
    walls_v = {(i, j): True for i in range(n + 1) for j in range(n)}   # x = x0 + i*cell
    walls_h = {(i, j): True for i in range(n) for j in range(n + 1)}   # z = z0 + j*cell
    seen = {(2, 2), (3, 2), (2, 3), (3, 3)}
    for i, j in ((2, 2), (2, 3)):
        walls_v[(i + 1, j)] = False
    for i in (2, 3):
        walls_h[(i, 3)] = False
    stack = [(2, 2)]
    while stack:
        i, j = stack[-1]
        options = [(i + di, j + dj, di, dj) for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1))
                   if 0 <= i + di < n and 0 <= j + dj < n and (i + di, j + dj) not in seen]
        if not options:
            stack.pop()
            continue
        ni, nj, di, dj = rng.choice(options)
        if di:
            walls_v[(max(i, ni), j)] = False
        else:
            walls_h[(i, max(j, nj))] = False
        seen.add((ni, nj))
        stack.append((ni, nj))
    walls_h[(1, n)] = False            # the way in from the plaza
    walls_v[(n, 1)] = False            # and from the museum's side
    walls_v[(n, 4)] = False
    height, t = 10.0, 1.6
    posts = set()
    for (i, j), up in walls_v.items():
        if up:
            x = x0 + i * cell
            b.box([x, 0.2 + height / 2.0, z0 + (j + 0.5) * cell], [t, height, cell - 2.0], HEDGE)
            posts.update({(i, j), (i, j + 1)})
    for (i, j), up in walls_h.items():
        if up:
            z = z0 + j * cell
            b.box([x0 + (i + 0.5) * cell, 0.2 + height / 2.0, z], [cell - 2.0, height, t], HEDGE)
            posts.update({(i, j), (i + 1, j)})
    for i, j in posts:
        b.box([x0 + i * cell, 0.2 + (height + 0.4) / 2.0, z0 + j * cell], [2.0, height + 0.4, 2.0],
              "#2a5426")
    # the heart of the maze
    cx, cz = x0 + 3.0 * cell, z0 + 3.0 * cell
    stamp(b, fx.plinth(3.0, 2.0), cx, cz, 0.2)
    place(b, "statuette", cx, cz, 2.4)
    place(b, "birdbath", cx - 6.0, cz + 6.0, 0.2)
    place(b, "garden_gnome", cx + 6.0, cz - 6.0, 0.2, 2)
    place(b, "fern", x0 + 0.5 * cell, z0 + 0.5 * cell, 0.2)
    place(b, "urn", x0 + 5.5 * cell, z0 + 5.5 * cell, 0.2)


def _yard(b: ArenaArea, s: Surfaces) -> None:
    s.lay(rect(-30.0, 30.0, -140.0, -100.0), 0.25, LAWN)
    s.lay(rect(-HALF[0], HALF[0], -HALF[1], Z0), 0.1, "#7a7e80")
    s.lay(rect(-HALF[0], X0, Z0, 30.0), 0.1, "#7a7e80")
    s.lay(rect(X1, HALF[0], Z0, 30.0), 0.1, "#4a4e54")
    # the dinosaur lawn: a brontosaurus you can climb
    bx, bz, by = 0.0, -120.0, 0.25
    green = "#4a8a5a"
    for dx in (-4.0, 4.0):
        for dz in (-3.0, 3.0):
            b.cyl([bx + dx, by + 4.0, bz + dz], [2.4, 8.0, 2.4], green)
    b.box([bx, by + 10.0, bz], [14.0, 5.0, 8.0], green)
    for k in range(6):
        b.box([bx + 8.0 + k * 1.8, by + 12.0 + k * 1.8, bz], [2.4, 2.4 - k * 0.1, 2.0 - k * 0.08],
              green)
    b.box([bx + 18.4, by + 22.4, bz], [3.4, 1.8, 2.0], green)
    for k in range(7):
        b.box([bx - 8.0 - k * 1.9, by + 9.0 - k * 1.1, bz], [2.6, 2.2 - k * 0.2, 2.0 - k * 0.18],
              green)
    # the loading yard: the van at the dock, crates, pallets, bins
    van(b, -56.0, -112.0, "z", colour="#e8ecec", stripe="#8a2a2a", length=24.0, y=0.1, front=-1)
    for x, z in ((-90.0, -100.0), (-84.0, -104.0), (-100.0, -128.0), (60.0, -112.0),
                 (90.0, -120.0)):
        b.box([x, 2.6, z], [5.0, 5.0, 5.0], "#a07a52", decal="crate_logo")
    for x, z in ((-120.0, -110.0), (40.0, -130.0), (110.0, -100.0)):
        place(b, "box_pallet", x, z, 0.1)
    for x, z in ((-40.0, -94.0), (-36.0, -94.0), (30.0, -92.0)):
        place(b, "bin", x, z, 0.1)
    for x, z in ((-130.0, -140.0), (-126.0, -136.0), (130.0, -136.0)):
        place(b, "traffic_cone", x, z, 0.1)
    # the coach park east of the museum
    van(b, 140.0, -20.0, "z", colour="#2a6a8a", stripe="#f2c230", length=32.0, y=0.1)
    for z in (-60.0, 20.0):
        car(b, 120.0, z, "z", colour="#8a3a6a" if z > 0 else "#3a6ab0", y=0.1, length=10.0)
    place(b, "traffic_cone", 120.0, 0.0, 0.1)
    place(b, "bin", 104.0, -40.0, 0.1)
    place(b, "potted_plant", 104.0, 10.0, 0.1)


def _edges(b: ArenaArea, rng: random.Random) -> None:
    perimeter(b, 26.0, "#5a5e66", cap="#4a4e56", rng=rng, ragged=3.0)
    skirt(b, HALF[0], HALF[1], "#3a3e46")
    backdrop(b, "city", -4.0, rng, colours=["#2a3040", "#343a4a", "#3a4050", "#2e3444"],
             depth=70.0)


# ================================================================ the meta
def _on(b: ArenaArea, level: float, x: float, z: float) -> float:
    return b.surface(x, z, level + 1.0)


def _meta(b: ArenaArea) -> None:
    for x, z in ((-60.0, 60.0), (-30.0, 64.0), (30.0, 64.0), (60.0, 60.0), (-84.0, 58.0),
                 (84.0, 58.0), (-20.0, 88.0), (20.0, 88.0), (-30.0, 100.0), (30.0, 100.0),
                 (-50.0, 118.0), (50.0, 118.0), (-130.0, 90.0), (130.0, 90.0), (-140.0, 40.0),
                 (140.0, 44.0)):
        b.team_spawn("props", x, None, z, yaw=3.14159)
    for x in (72.0, 76.5, 81.0, 85.5):
        for z in (10.0, 15.0, 20.0, 25.0):
            b.team_spawn("hunters", x, F1, z, yaw=-1.5708)
    b.mark("pen", 80.0, F1, 16.0, r=14.0)
    # the searchlight's beat: a loop round the T. rex
    for x, z in ((-22.0, -70.0), (0.0, -74.0), (22.0, -70.0), (28.0, -44.0), (22.0, -18.0),
                 (0.0, -14.0), (-22.0, -18.0), (-28.0, -44.0)):
        b.mark("sweep", x, F1, z)
    hides = [
        # downstairs
        (F1, -28.0, -60.0), (F1, 28.0, -28.0), (F1, -24.0, -78.0), (F1, 26.0, -79.0),
        (F1, -80.0, -66.0), (F1, -52.0, -58.0), (F1, -88.0, -60.0),
        (F1, -78.0, -34.0), (F1, -50.0, -14.0), (F1, -88.0, -8.0),
        (F1, -86.0, 2.0), (F1, -66.0, 18.0), (F1, -46.0, 10.0),
        (F1, 48.0, -60.0), (F1, 88.0, -70.0), (F1, 60.0, -50.0),
        (F1, 70.0, -36.0), (F1, 48.0, -24.0), (F1, 82.0, -12.0),
        (F1, 50.0, 4.0), (F1, 62.0, 16.0), (F1, -26.0, 22.0), (F1, 26.0, 20.0),
        # upstairs
        (F2, -16.0, 24.0), (F2, 22.0, 12.0), (F2, -88.0, 4.0), (F2, -56.0, 22.0),
        (F2, -76.0, -28.0), (F2, -50.0, -6.0), (F2, -78.0, -66.0), (F2, -56.0, -50.0),
        (F2, 50.0, -64.0), (F2, 76.0, -72.0), (F2, 46.0, -30.0), (F2, 84.0, -30.0),
        (F2, 50.0, 22.0), (F2, 80.0, 18.0),
        # outside
        (0.2, -60.0, 46.0), (0.2, 96.0, 64.0), (0.2, -100.0, 120.0), (0.2, 100.0, 116.0),
        (0.25, -76.0, 80.0), (0.25, 84.0, 98.0), (0.2, -134.0, -34.0), (0.2, -125.0, -5.0),
        (0.1, -110.0, -130.0), (0.1, 100.0, -126.0), (0.1, 150.0, -60.0), (0.1, 160.0, 20.0),
        (0.25, -20.0, -110.0), (0.1, -150.0, 60.0),
    ]
    for level, x, z in hides:
        b.mark("hide", x, _on(b, level, x, z), z)
    searches = [
        (F1, 0.0, -24.0, "the great hall"), (F1, 0.0, 20.0, "the foyer"),
        (F1, -76.0, -56.0, "the Egyptian room"), (F1, -60.0, -36.0, "the armoury"),
        (F1, -66.0, 0.0, "the gift shop"), (F1, 50.0, -56.0, "the fossil hall"),
        (F1, 70.0, -18.0, "the space gallery"), (F1, 50.0, 16.0, "the cafe"),
        (F2, 0.0, 12.0, "the portrait gallery"), (F2, -66.0, 2.0, "the library"),
        (F2, -64.0, -28.0, "the vase room"), (F2, -66.0, -52.0, "the sculpture hall"),
        (F2, 66.0, -34.0, "the clock room"), (F2, 66.0, -54.0, "the gem vault"),
        (F2, 56.0, 14.0, "the art gallery"),
        (0.2, 0.0, 64.0, "the plaza"), (0.2, 0.0, 112.0, "the fountain"),
        (0.2, -140.0, -47.0, "the hedge maze"), (0.2, -100.0, 40.0, "the ticket kiosk"),
        (0.1, -40.0, -110.0, "the loading yard"), (0.1, 30.0, -120.0, "the dinosaur lawn"),
        (0.1, 140.0, 10.0, "the coach park"), (F1, 64.0, 38.0, "the terrace"),
    ]
    for level, x, z, name in searches:
        b.mark("search", x, _on(b, level, x, z), z, name=name)
        b.landmark(x, z, name)
    b.landmark(80.0, 16.0, "the security office")
    b.camera(0.0, 40.0, 150.0, 0.0, 14.0, 30.0)
    b.camera(-30.0, 26.0, -10.0, 4.0, 8.0, -50.0)
    b.camera(-40.0, 15.0, -82.0, -80.0, 4.0, -60.0)
    b.extra.update({"accent": "#c8a050", "twist": "alarm", "pen_key": "pen"})


def build(b: ArenaArea) -> None:
    rng = random.Random(6620)
    ground(b, GROUND, soil="#3a3428", material="grass")
    s = Surfaces(b)
    s.reserve(rect(X0 - 0.5, X1 + 0.5, Z0 - 0.5, Z1 + 0.5))
    s.reserve(rect(-31.5, 31.5, Z1, 56.0))
    s.reserve(rect(38.0, 92.0, Z1, 50.0))
    s.reserve(rect(-112.0, X0, 10.0, 24.0))
    s.reserve(rect(-78.0, -42.0, -96.0, Z0))
    s.reserve(rect(46.0, 66.0, -100.0, Z0))
    _edges(b, rng)
    _shell(b)
    _portico(b)
    _walls(b)
    _paint(b)
    _stairs(b)
    _lights(b)
    _hall(b)
    _foyer(b)
    _egypt(b)
    _armoury(b)
    _shop(b)
    _fossils(b)
    _space(b)
    _cafe(b)
    _security(b)
    _portraits(b)
    _library(b)
    _vases(b)
    _sculpture(b)
    _art(b)
    _clocks(b)
    _gems(b)
    _maze(b, s)
    _plaza(b, s)
    _yard(b, s)
    _meta(b)
    cat.finish(b, "vase")
