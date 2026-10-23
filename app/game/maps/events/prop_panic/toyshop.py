"""Tinker's Toy Emporium -- a two-floor toy shop on a town square, round an
atrium with a giant toy rocket in it.

Layout (north is -z; the square is to the south)::

    z -135  ===================== the loading yard (van, pallets) ===========
    z  -75  ---- WORKSHOP ---------|---- STOCKROOM ------|-- STAFF ROOM ----
                (Tinker's bench)   | (shelving, pallets) | (the seekers' pen)
    z  -36  ------------------------------------------------------------------
             PLUSH & DOLLS   stairs  [ ATRIUM: the rocket,  stairs   BLOCKS &
             (the plush            ]   the train set, the            THE BALL PIT
             mountain)             ]   giant teddy        ]
    z   35  ==== shop windows ===== front doors ===== shop windows ===========
             the town square: carousel, fountain, kiosk, balloon cart
    z  135  ============== shopfronts round the square ======================

Upstairs, a gallery runs round the atrium: the games corner, the music
corner, outdoor toys, and at the back the space room and the party room.
The seekers wait in the staff room (the ``pen`` door into the shop).  The
twist is the power: every so often the lights go out (the rules' blackout).
"""
from __future__ import annotations

import random

from ..kit import (ArenaArea, Surfaces, backdrop, car, carve, flight, ground, letters, perimeter,
                   plate, rect, room_walls, sign_decal, slab, step_paint, strip_light)
from ...lastlight.kit import van
from . import catalogue as cat
from . import furniture as fx
from .catalogue import place, stamp
from .rooms import covering, door_holes, grow, interior, partition, pen_door, shell, skirt

HALF = (165.0, 135.0)
SKY = {"top": "#6a8ac8", "horizon": "#f0d8c0", "sun": [0.5, 0.6, 0.4],
       "clouds": 0.45, "tint": "#fff0dc"}
AMBIENT = "#b0a8b8"
GROUND = "#8a8478"
FOG = 700.0

COBBLE = "#9a9488"
BRICK = "#a0503a"
CREAM = "#f4e8d0"
TRIM = "#f4f0e8"
SHOP_RED = "#c8402a"
RED, BLUE, YELLOW, GREEN, PURPLE = "#d8402a", "#2f6ad0", "#f2c230", "#3aa04a", "#8a4ad0"

T = 1.2
F1, C1 = 0.6, 13.0
F2, C2 = 14.0, 26.4
WALL_TOP = 27.0
X0, X1, Z0, Z1 = -90.0, 90.0, -75.0, 35.0
IX0, IX1, IZ0, IZ1 = X0 + T, X1 - T, Z0 + T, Z1 - T
ZB = -36.0                     # the back rooms' wall
ATRIUM = rect(-24.0, 24.0, -30.0, 6.0)
WELLS = [rect(-31.0, -25.0, -10.2, 9.0), rect(25.0, 31.0, -10.2, 9.0)]
P = 0.6
PEN = rect(54.0 + P / 2.0, IX1, IZ0, ZB - P / 2.0)
PEN_DOOR = (66.0, 74.0)

FRONT = [(-8.0, 8.0, 0.0, 11.0),
         (-80.0, -50.0, 1.6, 11.0), (-40.0, -14.0, 1.6, 11.0), (14.0, 40.0, 1.6, 11.0),
         (50.0, 80.0, 1.6, 11.0),
         (-80.0, -50.0, 16.0, 24.0), (-40.0, -14.0, 16.0, 24.0), (-8.0, 8.0, 16.0, 24.0),
         (14.0, 40.0, 16.0, 24.0), (50.0, 80.0, 16.0, 24.0)]
BACK = [(12.0, 30.0, 0.0, 10.0),
        (-70.0, -50.0, 16.0, 24.0), (-30.0, -10.0, 16.0, 24.0), (10.0, 30.0, 16.0, 24.0),
        (50.0, 70.0, 16.0, 24.0)]
WEST = [(14.0, 20.0, 0.0, 10.0), (24.0, 32.0, 3.0, 10.0), (-64.0, -44.0, 3.0, 10.0),
        (-60.0, -40.0, 16.0, 24.0), (-10.0, 10.0, 16.0, 24.0)]
EAST = [(14.0, 20.0, 0.0, 10.0), (24.0, 32.0, 3.0, 10.0),
        (-60.0, -40.0, 16.0, 24.0), (-10.0, 10.0, 16.0, 24.0)]


# ================================================================ the shop
def _shell(b: ArenaArea) -> None:
    shell(b, rect(X0, X1, Z0, Z1), 0.0, WALL_TOP, BRICK,
          {"z+": FRONT, "z-": BACK, "x-": WEST, "x+": EAST}, frame=TRIM)
    # floors, the first floor round the atrium and the stairwells, the ceiling
    slab(b, rect(IX0, IX1, IZ0, IZ1), F1, F1, "#c8b898")
    for a, c in ((-8.0, 8.0),):
        slab(b, rect(a, c, IZ1, Z1), F1, F1, "#c8b898")
    slab(b, rect(12.0, 30.0, Z0, IZ0), F1, F1, "#c8b898")
    slab(b, rect(X0, IX0, 14.0, 20.0), F1, F1, "#c8b898")
    slab(b, rect(IX1, X1, 14.0, 20.0), F1, F1, "#c8b898")
    plate(b, carve(rect(IX0, IX1, IZ0, IZ1), [ATRIUM] + WELLS), F2, F2 - C1, "#f4ece0")
    slab(b, rect(IX0, IX1, IZ0, IZ1), WALL_TOP, WALL_TOP - C2, "#f4ece0")
    slab(b, rect(X0 - 0.5, X1 + 0.5, Z0 - 0.5, Z1 + 0.5), WALL_TOP + 1.0, 1.0, "#5a5a62")
    # the front parapet with the shop's name on it
    b.box([0.0, WALL_TOP + 3.5, Z1 + 0.25], [X1 - X0 + 1.0, 5.0, 0.5], SHOP_RED)
    letters(b, 0.0, WALL_TOP + 3.5, Z1 + 0.5, "TINKER'S TOY EMPORIUM", 4.0, YELLOW, SHOP_RED,
            pitch=3.2)
    # a striped awning over each shop window and the doors
    for a, c in ((-81.0, -49.0), (-41.0, -13.0), (-9.0, 9.0), (13.0, 41.0), (49.0, 81.0)):
        n = int((c - a) // 2.0)
        for k in range(n):
            x = a + (k + 0.5) * (c - a) / n
            b.box([x, 12.6, Z1 + 2.0], [(c - a) / n, 0.5, 4.0], RED if k % 2 else TRIM)
    # the doors' brass handles and the step
    slab(b, rect(-10.0, 10.0, Z1, Z1 + 3.0), F1, F1, "#a89a88")


def _partitions(b: ArenaArea) -> None:
    ground_doors = [(-54.0, -44.0, 10.0), (6.0, 16.0, 10.0), (34.0, 44.0, 10.0),
                    (PEN_DOOR[0], PEN_DOOR[1], 10.0)]
    partition(b, "x", ZB, IX0, IX1, F1, C1, CREAM, ground_doors, trim_colour=TRIM)
    partition(b, "z", -10.0, IZ0, ZB - P / 2.0, F1, C1, CREAM, [(-62.0, -54.0, 10.0)],
              trim_colour=TRIM)
    partition(b, "z", 54.0, IZ0, ZB - P / 2.0, F1, C1, CREAM)
    pen_door(b, "x", ZB, PEN_DOOR[0], PEN_DOOR[1], F1, 10.0, 0.5, "#e8d8b8")
    up_doors = [(-60.0, -48.0, F2 + 9.0), (-6.0, 6.0, F2 + 9.0), (48.0, 60.0, F2 + 9.0)]
    partition(b, "x", ZB, IX0, IX1, F2, C2, "#e8e0f0", up_doors, trim_colour=TRIM)
    partition(b, "z", 0.0, IZ0, ZB - P / 2.0, F2, C2, "#e8e0f0", [(-62.0, -52.0, F2 + 9.0)],
              trim_colour=TRIM)


def _paint(b: ArenaArea) -> None:
    zf = ZB + P / 2.0

    def win(holes, lo, hi, y0, y1):
        return [h for h in holes if h[1] > lo and h[0] < hi and h[3] > y0 and h[2] < y1]

    gd = [(-54.0, -44.0, 10.0), (6.0, 16.0, 10.0), (34.0, 44.0, 10.0), (66.0, 74.0, 10.0)]
    ud = [(-60.0, -48.0, F2 + 9.0), (-6.0, 6.0, F2 + 9.0), (48.0, 60.0, F2 + 9.0)]
    # the shop floor: one big room, the back rooms behind it
    interior(b, rect(IX0, IX1, zf, IZ1), F1, C1, "#f8e0a0",
             {"x-": win(WEST, zf, IZ1, F1, C1), "x+": win(EAST, zf, IZ1, F1, C1),
              "z+": win(FRONT, IX0, IX1, F1, C1), "z-": door_holes(gd, F1)},
             walls={"x-": "#f0c8d8", "x+": "#c8e0f0"})
    for piece in carve(rect(IX0, IX1, zf, IZ1), [grow(w, 0.1) for w in WELLS]):
        covering(b, piece, F1, "#ece0cc")
    interior(b, rect(IX0, -10.3, IZ0, ZB - P / 2.0), F1, C1, "#d8c8a8",
             {"x-": win(WEST, IZ0, ZB, F1, C1), "x+": door_holes([(-62.0, -54.0, 10.0)], F1),
              "z+": door_holes(gd[:1], F1)}, floor="#9a7a5a", floor_decal="planks")
    interior(b, rect(-9.7, 53.7, IZ0, ZB - P / 2.0), F1, C1, "#c8ccd0",
             {"x-": door_holes([(-62.0, -54.0, 10.0)], F1), "z-": win(BACK, -10.0, 54.0, F1, C1),
              "z+": door_holes(gd[1:3], F1)}, floor="#9aa0a8")
    interior(b, PEN, F1, C1, "#d8e8d0", {"z+": door_holes(gd[3:], F1)}, floor="#8a9a8a")
    # upstairs: the gallery, and the space room and party room behind it
    interior(b, rect(IX0, IX1, zf, IZ1), F2, C2, "#e8d8f8",
             {"x-": win(WEST, zf, IZ1, F2, C2), "x+": win(EAST, zf, IZ1, F2, C2),
              "z+": win(FRONT, IX0, IX1, F2, C2), "z-": door_holes(ud, F2)})
    for piece in carve(rect(IX0, IX1, zf, IZ1), [grow(w, 0.1) for w in [ATRIUM] + WELLS]):
        covering(b, piece, F2, "#6a8ac8", "felt")
    interior(b, rect(IX0, -0.3, IZ0, ZB - P / 2.0), F2, C2, "#1a2a5a",
             {"x-": win(WEST, IZ0, ZB, F2, C2), "x+": door_holes([(-62.0, -52.0, F2 + 9.0)], F2),
              "z-": win(BACK, IX0, 0.0, F2, C2), "z+": door_holes(ud[:2], F2)},
             floor="#2a3a6a", floor_decal="starfield")
    interior(b, rect(0.3, IX1, IZ0, ZB - P / 2.0), F2, C2, "#f8d8e8",
             {"x+": win(EAST, IZ0, ZB, F2, C2), "x-": door_holes([(-62.0, -52.0, F2 + 9.0)], F2),
              "z-": win(BACK, 0.0, IX1, F2, C2), "z+": door_holes(ud[1:], F2)},
             floor="#e8a8c8", floor_decal="party")


def _stairs(b: ArenaArea) -> None:
    for x0, x1 in ((-31.0, -25.0), (25.0, 31.0)):
        flight(b, "z", 8.0, -10.2, x0, x1, F1, F2, "#c8402a", fill=F1 - 0.3, lights=YELLOW)
        step_paint(b, x0, x1, -10.2, -1.0, F2)
    # the rails round the atrium and the stairwells, upstairs
    h = 3.4
    for x0, x1 in ((-25.0, -24.0), (24.0, 25.0)):
        b.box([(x0 + x1) / 2.0, F2 + h / 2.0, (-30.4 + 9.4) / 2.0], [1.0, h, 39.8], SHOP_RED)
    b.box([0.0, F2 + h / 2.0, -30.2], [48.0, h, 0.4], SHOP_RED)
    b.box([0.0, F2 + h / 2.0, 6.2], [48.0, h, 0.4], SHOP_RED)
    for x0, x1, xr in ((-31.0, -25.0, -31.2), (25.0, 31.0, 31.2)):
        b.box([(x0 + x1) / 2.0, F2 + h / 2.0, 9.2], [x1 - x0, h, 0.4], SHOP_RED)
        b.box([xr, F2 + h / 2.0, (-10.2 + 9.4) / 2.0], [0.4, h, 19.6], SHOP_RED)
    for x in (-24.5, 24.5):
        for z in (-30.2, 6.2):
            b.box([x, F2 + h + 0.4, z], [1.2, 0.8, 1.2], YELLOW)


def _lights(b: ArenaArea) -> None:
    for y in (C1, C2):
        for x in (-70.0, -45.0, 45.0, 70.0):
            for z in (-20.0, 15.0):
                strip_light(b, x, z, y, 14.0, "z")
        for x in (-50.0, 0.0, 50.0):
            strip_light(b, x, -56.0, y, 14.0, "z")
        if y == C1:
            for x in (-12.0, 12.0):
                strip_light(b, x, 20.0, y, 10.0, "x")
    for x in (-12.0, 12.0):
        strip_light(b, x, 20.0, C2, 10.0, "x")


# ============================================================ furnishing
def _rocket(b: ArenaArea) -> None:
    """The giant toy rocket in the atrium, on its plinth inside the train set."""
    cx, cz = 0.0, -12.0
    b.box([cx, F1 + 0.6, cz], [12.0, 1.2, 12.0], "#3a3a6a")
    b.box([cx, F1 + 1.25, cz], [11.0, 0.1, 11.0], YELLOW, collide=False)
    y = F1 + 1.2
    for dx, dz in ((-3.6, 0.0), (3.6, 0.0), (0.0, -3.6), (0.0, 3.6)):
        b.box([cx + dx, y + 3.0, cz + dz], [1.2 if dx else 0.6, 6.0, 0.6 if dx else 1.2], RED)
    b.cyl([cx, y + 9.0, cz], [5.0, 18.0, 5.0], "#f4f4f4", material="metal")
    b.cyl([cx, y + 12.0, cz], [5.2, 1.4, 5.2], BLUE)
    b.cyl([cx, y + 14.5, cz], [5.2, 0.6, 5.2], RED)
    b.cone([cx, y + 21.0, cz], [5.0, 6.0, 5.0], RED)
    b.sphere([cx, y + 9.0, cz + 2.2], [1.8, 1.8, 0.9], "#8ad8ff", material="glass")
    b.sphere([cx, y + 4.0, cz + 2.2], [1.4, 1.4, 0.9], "#8ad8ff", material="glass")
    # the train set: a loop of track round the plinth, and the train on it
    ring = 10.0
    for (x0, x1, z0, z1) in ((-ring, ring, cz - ring, cz - ring + 1.6),
                             (-ring, ring, cz + ring - 1.6, cz + ring),
                             (-ring, -ring + 1.6, cz - ring + 1.6, cz + ring - 1.6),
                             (ring - 1.6, ring, cz - ring + 1.6, cz + ring - 1.6)):
        slab(b, rect(x0, x1, z0, z1), F1 + 0.3, 0.3, "#5a4a3a")
    for x, colour in ((-5.0, RED), (-1.6, BLUE), (1.8, GREEN)):
        b.box([x, F1 + 1.2, cz + ring - 0.8], [3.0, 1.8, 1.2], colour)
    b.cyl([-5.8, F1 + 2.6, cz + ring - 0.8], [0.6, 1.0, 0.6], "#2a2a2a")
    # the giant teddy keeping watch
    tx, tz = 16.0, -2.0
    b.sphere([tx, F1 + 4.0, tz], [8.0, 8.0, 7.0], "#a87a4a")
    b.sphere([tx, F1 + 10.0, tz], [5.6, 5.4, 5.2], "#a87a4a")
    b.sphere([tx, F1 + 9.4, tz + 2.4], [2.4, 1.8, 1.4], "#d8b088", collide=False)
    b.sphere([tx - 2.2, F1 + 12.8, tz], [2.0, 2.0, 1.4], "#a87a4a", collide=False)
    b.sphere([tx + 2.2, F1 + 12.8, tz], [2.0, 2.0, 1.4], "#a87a4a", collide=False)
    b.box([tx, F1 + 7.3, tz + 2.6], [3.4, 1.0, 1.6], RED)


def _ground_floor(b: ArenaArea) -> None:
    y = F1
    _rocket(b)
    # the window displays
    for a, c in ((-80.0, -50.0), (-40.0, -14.0), (14.0, 40.0), (50.0, 80.0)):
        slab(b, rect(a + 1.0, c - 1.0, IZ1 - 3.6, IZ1), 1.6, 1.0, "#5a3a6a")
    top = 1.6
    place(b, "teddy_bear", -74.0, IZ1 - 1.8, top, 0)
    place(b, "toy_rocket", -66.0, IZ1 - 1.8, top)
    place(b, "jack_in_box", -58.0, IZ1 - 1.8, top)
    place(b, "gift_box", -34.0, IZ1 - 1.8, top)
    place(b, "toy_soldier", -27.0, IZ1 - 1.8, top)
    place(b, "plush_dino", -20.0, IZ1 - 1.8, top, 1)
    place(b, "beach_ball", 20.0, IZ1 - 1.8, top)
    place(b, "rocking_horse", 28.0, IZ1 - 1.8, top, 1)
    place(b, "gift_box", 35.0, IZ1 - 1.8, top)
    place(b, "toy_robot", 56.0, IZ1 - 1.8, top)
    place(b, "toy_drum", 64.0, IZ1 - 1.8, top)
    place(b, "toy_car", 73.0, IZ1 - 1.8, top, 1)
    # the tills
    for x in (-24.0, 24.0):
        stamp(b, fx.counter(16.0, body="#c8402a", top="#f4e8d0", doors="#e86a5a"), x, 21.0, y, 2)
    place(b, "cash_register", -28.0, 21.0, y + fx.COUNTER_TOP, 2)
    place(b, "cash_register", 28.0, 21.0, y + fx.COUNTER_TOP, 2)
    place(b, "gift_box", -20.0, 21.2, y + fx.COUNTER_TOP)
    place(b, "spinning_top", 20.0, 21.2, y + fx.COUNTER_TOP)
    # plush and dolls, the west wing
    for z in (-28.0, -12.0, 4.0):
        stamp(b, fx.shelf_unit(12.0, 3, colour="#f0a8c8", metal=False), IX0 + 1.2, z, y, 1)
    tops = [y + t for t in fx.shelf_tops(3)]
    for z, kind in ((-31.0, "teddy_bear"), (-25.0, "rubber_duck"), (-15.0, "rubber_duck"),
                    (-9.0, "teddy_bear"), (1.0, "teddy_bear"), (7.0, "rubber_duck")):
        place(b, kind, IX0 + 1.3, z, tops[1], 1)
    for z, kind in ((-29.0, "beach_ball"), (-12.0, "teddy_bear"), (5.0, "beach_ball")):
        place(b, kind, IX0 + 1.3, z, tops[2], 1)
    for x in (-64.0, -46.0):
        stamp(b, fx.shelf_unit(16.0, 2, colour="#f8d0e0", metal=False), x + 1.2, -10.0, y, 1)
        stamp(b, fx.shelf_unit(16.0, 2, colour="#f8d0e0", metal=False), x - 1.2, -10.0, y, 3)
    tops2 = [y + t for t in fx.shelf_tops(2)]
    for x, q in ((-62.7, 1), (-65.3, 3), (-44.7, 1), (-47.3, 3)):
        place(b, "rubber_duck", x, -15.0, tops2[1], q)
        place(b, "spinning_top", x, -5.0, tops2[1], q)
        place(b, "beach_ball" if q == 1 else "toy_block_c", x, -10.0, tops2[2], q)
    # the plush mountain
    for k, (w, h) in enumerate(((12.0, 2.0), (8.0, 2.0), (4.4, 2.0))):
        b.box([-74.0, y + 2.0 * k + h / 2.0, 20.0], [w, h, w], ["#f0a8c8", "#c8a8f0", "#a8d8f0"][k],
              material="")
    place(b, "teddy_bear", -74.0, 20.0, y + 6.0, 0)
    place(b, "plush_dino", -78.6, 16.0, y + 2.0, 3)
    place(b, "rubber_duck", -70.0, 23.6, y + 2.0, 0)
    place(b, "teddy_bear", -56.0, 24.0, y, 2)
    place(b, "plush_dino", -40.0, -24.0, y, 1)
    place(b, "plush_dino", -54.0, 6.0, y, 2)
    place(b, "teddy_bear", -36.0, 12.0, y, 3)
    place(b, "rubber_duck", -58.0, -26.0, y)
    # blocks and the ball pit, the east wing
    room_walls(b, rect(46.0, 82.0, -26.0, 4.0), 1.0, y, y + 2.4, BLUE,
               doors={"x-": [(-16.0, -8.0, y + 5.0)]})
    for i in range(4):
        for j in range(3):
            if (i, j) in ((0, 1),):
                continue
            px = 50.0 + i * 8.6 + (j % 2) * 2.0
            pz = -21.0 + j * 9.0
            place(b, "ball_pit_ball", px, pz, y)
    place(b, "ball_pit_ball", 58.6, -21.0, y + 1.6)
    place(b, "ball_pit_ball", 69.2, -12.0, y + 1.6)
    for x, z, kind in ((40.0, 20.0, "toy_block"), (41.9, 20.0, "toy_block_b"),
                       (40.95, 20.0, "toy_block_c"), (64.0, 26.0, "toy_block_b"),
                       (38.0, -18.0, "toy_block_c"), (86.0, -30.0, "toy_block")):
        yy = y + 1.8 if (x, z) == (40.95, 20.0) else y
        place(b, kind, x, z, yy)
    # the block castle
    for dx in (-6.0, -3.0, 3.0, 6.0):
        b.box([70.0 + dx, y + 1.5, 18.0], [3.0, 3.0, 3.0], [RED, YELLOW, GREEN, BLUE][int(dx + 6) % 4])
    for dx in (-6.0, 6.0):
        b.box([70.0 + dx, y + 4.5, 18.0], [3.0, 3.0, 3.0], PURPLE)
        b.cone([70.0 + dx, y + 7.5, 18.0], [3.4, 3.0, 3.4], RED)
    b.box([70.0, y + 4.5, 18.0], [9.0, 3.0, 3.0], YELLOW)
    place(b, "toy_soldier", 70.0, 22.0, y, 0)
    place(b, "jack_in_box", 80.0, 8.0, y)
    place(b, "toy_car", 36.0, 6.0, y, 1)
    place(b, "toy_car", 84.0, -4.0, y, 0)
    place(b, "spinning_top", 44.0, 12.0, y)
    stamp(b, fx.shelf_unit(12.0, 3, colour="#a8c8f0"), IX1 - 1.2, -14.0, y, 3)
    for z, kind in ((-18.0, "jack_in_box"), (-10.0, "xylophone")):
        place(b, kind, IX1 - 1.3, z, tops[1], 3)
    place(b, "spinning_top", IX1 - 1.3, -14.0, tops[2], 3)
    # round the atrium
    for x, z in ((-12.0, -26.0), (12.0, -26.0), (-12.0, 2.0)):
        place(b, "toy_soldier", x, z, y, 0)
    place(b, "gift_box", 6.0, 2.4, y)
    place(b, "spinning_top", -20.0, -16.0, y)
    place(b, "beach_ball", 20.0, -24.0, y)
    stamp(b, fx.rug(16.0, 6.0, "#3aa04a", "", YELLOW), 0.0, 12.0, y)


def _back_rooms(b: ArenaArea) -> None:
    y = F1
    # Tinker's workshop
    stamp(b, fx.counter(20.0, body="#7a5335", top="#5a3a24", doors="#9a7a5a"), -60.0, IZ0 + 1.8, y)
    stamp(b, fx.counter(14.0, body="#7a5335", top="#5a3a24", doors="#9a7a5a"), -26.0, IZ0 + 1.8, y)
    top = y + fx.COUNTER_TOP
    place(b, "toy_robot", -66.0, IZ0 + 1.6, top)
    place(b, "spinning_top", -58.0, IZ0 + 1.8, top)
    place(b, "toy_car", -50.0, IZ0 + 1.8, top, 1)
    place(b, "xylophone", -26.0, IZ0 + 1.8, top)
    place(b, "toy_robot", -84.0, -60.0, y, 1)
    place(b, "toy_robot", -84.0, -48.0, y, 1)
    place(b, "toy_robot", -40.0, -50.0, y, 2)
    place(b, "toy_drum", -30.0, -56.0, y)
    place(b, "jack_in_box", -70.0, -42.0, y)
    place(b, "toy_car", -18.0, -44.0, y, 2)
    stamp(b, fx.table(10.0, 5.0, top="#a07a52"), -52.0, -52.0, y)
    place(b, "toy_robot", -52.0, -52.0, y + fx.TABLE_TOP)
    place(b, "spinning_top", -48.0, -51.0, y + fx.TABLE_TOP)
    for k, x in enumerate((-80.0, -72.0, -64.0)):
        b.box([x, y + 7.0, IZ0 + 0.3], [5.0, 5.0, 0.6], "#5a3a24", decal="clockface")
    stamp(b, [cat.C(0.0, 0.0, 0.0, 6.0, 1.0, 6.0, "#5a5a5a"),
              cat.C(0.0, 1.0, 0.0, 1.2, 6.0, 1.2, "#8a8a8a", m="metal"),
              cat.B(0.0, 7.0, 0.0, 6.0, 1.2, 1.2, BRASS, m="metal"),
              cat.B(-2.6, 5.2, 0.0, 0.8, 2.0, 0.8, BRASS, m="metal"),
              cat.B(2.6, 5.2, 0.0, 0.8, 2.0, 0.8, BRASS, m="metal")], -78.0, -66.0, y)
    # the stockroom
    for x in (0.0, 16.0, 32.0):
        stamp(b, fx.shelf_unit(12.0, 3, colour="#8a9098"), x + 1.2, -58.0, y, 1)
        stamp(b, fx.shelf_unit(12.0, 3, colour="#8a9098"), x - 1.2, -58.0, y, 3)
    tops = [y + t for t in fx.shelf_tops(3)]
    for x, q in ((1.3, 1), (-1.3, 3), (17.3, 1), (14.7, 3), (33.3, 1), (30.7, 3)):
        place(b, "gift_box" if q == 1 else "board_games", x, -62.0, tops[1], q)
        place(b, "toy_block" if q == 1 else "gift_box", x, -54.0, tops[1], q)
        place(b, "board_games", x, -58.0, tops[2], q)
    place(b, "box_pallet", 8.0, -44.0, y)
    place(b, "box_pallet", 46.0, -66.0, y)
    place(b, "box_pallet", 40.0, -70.0, y)
    place(b, "gift_box", 40.0, -44.0, y)
    # the staff room: the seekers' pen
    x0, x1, z0, z1 = PEN
    for k in range(6):
        b.box([x1 - 1.2, y + 4.0, z0 + 3.0 + k * 3.0], [2.4, 8.0, 2.8], "#6a8aa8", material="metal")
        b.box([x1 - 2.42, y + 6.4, z0 + 3.0 + k * 3.0], [0.04, 0.6, 0.6], "#2a2a2a", collide=False)
    stamp(b, fx.table(8.0, 5.0, top="#e8e0d0"), 64.0, -62.0, y)
    stamp(b, fx.sofa("#6a8a5a", 9.0), 64.0, z0 + 1.8, y)
    b.box([x0 + 0.15, y + 6.0, -48.0], [0.3, 4.0, 6.0], "#c8a070", decal="ea25_menu")
    b.box([70.0, y + 10.8, ZB + 0.5], [9.0, 1.6, 0.4], YELLOW,
          decal=sign_decal("STAFF ONLY", YELLOW, "#1b2a35", 5.6))


def _upstairs(b: ArenaArea) -> None:
    y = F2
    # the games corner, west
    for x, z in ((-70.0, 18.0), (-50.0, 18.0), (-70.0, -4.0)):
        stamp(b, fx.table(8.0, 6.0, top="#3aa04a", legs="#2a6a3a"), x, z, y)
        place(b, "board_games", x, z, y + fx.TABLE_TOP)
    for z in (-28.0, -14.0):
        stamp(b, [cat.B(0.0, 0.0, 0.0, 6.0, 5.0, 4.0, "#f0c8d8"),
                  cat.B(0.0, 5.0, 0.0, 6.4, 1.4, 4.4, "#c84a6a"),
                  cat.B(0.0, 6.4, 0.0, 4.0, 1.2, 4.4, "#c84a6a"),
                  cat.B(-1.4, 1.0, 2.02, 1.2, 1.4, 0.04, "#8ad8ff"),
                  cat.B(1.4, 1.0, 2.02, 1.2, 1.4, 0.04, "#8ad8ff"),
                  cat.B(-1.4, 3.2, 2.02, 1.2, 1.4, 0.04, "#8ad8ff"),
                  cat.B(1.4, 3.2, 2.02, 1.2, 1.4, 0.04, "#8ad8ff")], IX0 + 2.0, z, y, 1)
    place(b, "board_games", -56.0, -20.0, y)
    place(b, "jack_in_box", -44.0, -4.0, y)
    place(b, "toy_block", -40.0, 26.0, y)
    place(b, "toy_block_b", -38.2, 26.0, y)
    place(b, "teddy_bear", -84.0, 28.0, y, 1)
    # the music corner, over the doors
    stamp(b, [cat.B(0.0, 0.0, 0.0, 8.0, 2.4, 3.0, "#1a1a1a"),
              cat.B(0.0, 2.4, 0.4, 7.6, 0.3, 1.6, "#f4f4f4", dec="keys"),
              cat.B(0.0, 2.4, -1.0, 8.0, 3.0, 1.0, "#1a1a1a")], 0.0, IZ1 - 1.5, y, 2)
    for x, kind in ((-14.0, "toy_drum"), (-8.0, "xylophone"), (8.0, "xylophone"),
                    (14.0, "toy_drum"), (-18.0, "toy_drum")):
        place(b, kind, x, 22.0, y)
    # outdoor toys, east
    for x, z, q in ((44.0, 24.0, 1), (54.0, 24.0, 1), (64.0, 24.0, 1), (74.0, 10.0, 0)):
        place(b, "rocking_horse", x, z, y, q)
    for x, z, q in ((46.0, -6.0, 0), (60.0, -12.0, 1), (80.0, -24.0, 2)):
        place(b, "toy_car", x, z, y, q)
    for x, z in ((70.0, -6.0), (84.0, 26.0), (40.0, -26.0)):
        place(b, "beach_ball", x, z, y)
    b.cyl([60.0, y + 1.2, 6.0], [10.0, 2.4, 10.0], BLUE)
    b.cyl([60.0, y + 2.44, 6.0], [8.6, 0.08, 8.6], "#1b1d20")
    # the space room
    for x, z in ((-70.0, -60.0), (-50.0, -46.0), (-24.0, -64.0), (-14.0, -44.0)):
        place(b, "toy_rocket", x, z, y)
    for x, z, q in ((-80.0, -44.0, 1), (-36.0, -56.0, 2), (-60.0, -68.0, 0)):
        place(b, "toy_robot", x, z, y, q)
    for x, z, s, c in ((-60.0, -56.0, 3.0, "#e86a3a"), (-30.0, -50.0, 2.0, "#5aa0e8"),
                       (-44.0, -64.0, 2.4, "#e8c86a")):
        b.cyl([x, C2 - 2.0, z], [0.1, 4.0, 0.1], "#2a2a2a", collide=False)
        b.sphere([x, C2 - 4.0 - s / 2.0, z], [s, s, s], c, collide=False)
    stamp(b, [cat.B(0.0, 0.0, 0.0, 8.0, 1.0, 8.0, "#8a8a9a"),
              cat.C(0.0, 1.0, 0.0, 6.0, 5.0, 6.0, "#c8ccd8", m="metal"),
              cat.K(0.0, 6.0, 0.0, 6.0, 4.0, 6.0, "#c8ccd8", m="metal"),
              cat.B(0.0, 2.0, 2.6, 2.0, 2.0, 0.2, "#8ad8ff", m="glass")], -40.0, -66.0, y)
    # the party room
    stamp(b, fx.table(16.0, 6.0, top="#f4f0e8", cloth="#f0c8d0"), 40.0, -56.0, y)
    for x in (34.0, 40.0, 46.0):
        place(b, "gift_box", x, -56.0, y + fx.TABLE_TOP)
    for x, z, c in ((30.0, -56.0, RED), (50.0, -56.0, BLUE), (40.0, -58.0, YELLOW)):
        b.box([x, y + fx.TABLE_TOP + 4.0, z], [0.06, 8.0, 0.06], "#c8c8c8")
        b.sphere([x, y + fx.TABLE_TOP + 9.2, z], [2.0, 2.4, 2.0], c, collide=False)
    # the bouncy castle
    bx, bz = 70.0, -58.0
    b.box([bx, y + 0.6, bz], [16.0, 1.2, 16.0], "#e85a8a")
    for dx, dz in ((-7.4, 0.0), (7.4, 0.0)):
        b.box([bx + dx, y + 3.6, bz + dz], [1.2, 4.8, 16.0], YELLOW)
    b.box([bx, y + 3.6, bz - 7.4], [13.6, 4.8, 1.2], BLUE)
    for dx in (-7.4, 7.4):
        for dz in (-7.4, 7.4):
            b.cyl([bx + dx, y + 7.0, bz + dz], [2.0, 2.0, 2.0], RED)
    place(b, "beach_ball", bx - 3.0, bz - 2.0, y + 1.2)
    place(b, "ball_pit_ball", bx + 3.0, bz + 1.0, y + 1.2)
    place(b, "gift_box", 16.0, -70.0, y)
    place(b, "gift_box", 10.0, -44.0, y)
    place(b, "teddy_bear", 84.0, -44.0, y, 3)


# ============================================================ the square
def _square(b: ArenaArea, s: Surfaces) -> None:
    s.lay(rect(-HALF[0], HALF[0], Z1, 118.0), 0.12, COBBLE)
    # the fountain
    fx0, fx1, fz0, fz1 = -10.0, 10.0, 70.0, 90.0
    room_walls(b, rect(fx0, fx1, fz0, fz1), 1.2, 0.0, 1.6, "#a8a098")
    slab(b, rect(fx0 + 1.2, fx1 - 1.2, fz0 + 1.2, fz1 - 1.2), 0.3, 0.3, "#4a5a6a")
    b.box([0.0, 0.9, 80.0], [17.6, 1.0, 17.6], "#5aa0d8", collide=False, material="glass", alpha=0.7)
    b.cyl([0.0, 3.0, 80.0], [2.0, 6.0, 2.0], "#a8a098")
    b.cyl([0.0, 6.4, 80.0], [7.0, 0.8, 7.0], "#a8a098")
    place(b, "teddy_bear", 0.0, 80.0, 6.8, 2)
    # the carousel: an octagonal deck, poles, a canopy, horses
    cx, cz = -78.0, 82.0
    slab(b, rect(cx - 9.0, cx + 9.0, cz - 9.0, cz + 9.0), 1.2, 1.2, "#f4e0a0")
    slab(b, rect(cx - 6.0, cx + 6.0, cz - 11.0, cz - 9.0), 1.2, 1.2, "#f4e0a0")
    slab(b, rect(cx - 6.0, cx + 6.0, cz + 9.0, cz + 11.0), 1.2, 1.2, "#f4e0a0")
    slab(b, rect(cx - 11.0, cx - 9.0, cz - 6.0, cz + 6.0), 1.2, 1.2, "#f4e0a0")
    slab(b, rect(cx + 9.0, cx + 11.0, cz - 6.0, cz + 6.0), 1.2, 1.2, "#f4e0a0")
    b.cyl([cx, 6.6, cz], [3.0, 10.8, 3.0], RED)
    for dx, dz in ((-6.0, -6.0), (6.0, -6.0), (-6.0, 6.0), (6.0, 6.0)):
        b.cyl([cx + dx, 6.6, cz + dz], [0.4, 10.8, 0.4], YELLOW, material="metal")
    b.cyl([cx, 12.4, cz], [24.0, 0.8, 24.0], RED)
    b.cone([cx, 15.2, cz], [24.0, 4.8, 24.0], TRIM, collide=False)
    b.sphere([cx, 18.0, cz], [1.6, 1.6, 1.6], YELLOW, collide=False)
    for dx, dz, q in ((0.0, -7.0, 1), (7.0, 0.0, 2), (0.0, 7.0, 3), (-7.0, 0.0, 0),
                      (-3.4, -3.4, 0), (3.4, 3.4, 2)):
        place(b, "rocking_horse", cx + dx, cz + dz, 1.2, q)
    # the kiosk, the balloon cart, the benches
    kx, kz = 78.0, 84.0
    b.box([kx, 2.0, kz], [12.0, 4.0, 6.0], SHOP_RED)
    b.box([kx, 4.1, kz], [12.6, 0.2, 6.6], CREAM)
    for dx in (-5.6, 5.6):
        b.box([kx + dx, 7.4, kz - 2.6], [0.4, 6.4, 0.4], TRIM)
    b.box([kx, 10.8, kz], [13.0, 0.6, 8.0], RED)
    b.box([kx, 11.6, kz - 3.6], [10.0, 1.0, 0.2], YELLOW,
          decal=sign_decal("TOYS & TREATS", YELLOW, SHOP_RED, 10.0))
    place(b, "gift_box", kx - 3.0, kz + 0.6, 4.2)
    place(b, "spinning_top", kx + 3.0, kz + 0.6, 4.2)
    place(b, "teddy_bear", kx + 8.0, kz + 6.0, 0.12, 2)
    place(b, "gift_box", kx - 8.0, kz + 6.0, 0.12)
    stamp(b, [cat.B(0.0, 0.0, 0.0, 4.0, 2.6, 2.6, "#3a8ad8"),
              cat.B(0.0, 2.6, 0.0, 4.4, 0.3, 3.0, YELLOW)], 34.0, 66.0, 0.12)
    for k, (dx, dz, c) in enumerate(((-1.4, 0.0, RED), (0.0, 0.6, YELLOW), (1.4, -0.4, GREEN),
                                     (0.6, 1.0, PURPLE))):
        b.box([34.0 + dx, 2.92 + 3.0, 66.0 + dz], [0.05, 6.0, 0.05], "#c8c8c8")
        b.sphere([34.0 + dx, 2.92 + 7.0, 66.0 + dz], [1.6, 2.0, 1.6], c, collide=False)
    for x, z, q in ((-30.0, 60.0, 0), (30.0, 96.0, 2), (-30.0, 100.0, 2), (50.0, 58.0, 0)):
        stamp(b, fx.bench(6.0), x, z, 0.12, q)
    for x in (-50.0, -20.0, 20.0, 50.0, 110.0, -110.0):
        stamp(b, fx.lamp_stand(11.0), x, 46.0, 0.12)
    for x, z in ((-120.0, 70.0), (120.0, 60.0), (-40.0, 104.0), (60.0, 104.0)):
        stamp(b, fx.raised_bed(6.0, 6.0, "#4a8a3a"), x, z, 0.12)
        b.tree(x, z, 1.72, 1.0, leaf_c="#4a9a3a")
    place(b, "toy_soldier", -12.0, Z1 + 4.0, 0.12)
    place(b, "toy_soldier", 12.0, Z1 + 4.0, 0.12)
    for x, z in ((-100.0, 44.0), (100.0, 44.0), (-140.0, 110.0), (140.0, 100.0)):
        place(b, "bin", x, z, 0.12)
    place(b, "beach_ball", 16.0, 94.0, 0.12)
    place(b, "potted_plant", -24.0, 40.0, 0.12)
    place(b, "potted_plant", 24.0, 40.0, 0.12)
    place(b, "gift_box", -140.0, 50.0, 0.12)
    place(b, "plush_dino", 136.0, 70.0, 0.12, 3)
    # the shopfronts round the square
    fronts = [(-HALF[0], -100.0, "#d8a878", "BAKERY"), (-100.0, -40.0, "#8ab0c8", "BOOKS"),
              (-40.0, 40.0, "#e8d8b8", "TOWN HALL"), (40.0, 100.0, "#c8a8d8", "SWEETS"),
              (100.0, HALF[0], "#a8c8a0", "CAFE")]
    for a, c, colour, name in fronts:
        b.box([(a + c) / 2.0, 11.0, 126.5], [c - a, 22.0, 17.0], colour)
        b.box([(a + c) / 2.0, 12.5, 117.95], [min(30.0, c - a - 8.0), 3.0, 0.1], "#2a2a3a",
              decal=sign_decal(name, "#2a2a3a", "#ffd27a", 6.0), collide=False)
        for x in range(int(a + 8), int(c - 6), 12):
            b.box([x + 3.0, 5.0, 117.95], [6.0, 6.0, 0.1], "#cfe8ff", material="glass", collide=False)


def _alleys(b: ArenaArea, s: Surfaces) -> None:
    s.lay(rect(-HALF[0], HALF[0], -HALF[1], Z0), 0.12, "#6a6a6a")
    s.lay(rect(X1, HALF[0], Z0, Z1), 0.12, "#7a7a78")
    s.lay(rect(-HALF[0], X0, Z0, Z1), 0.12, "#7a7a78")
    van(b, 0.0, -100.0, "x", colour="#f2c230", stripe=SHOP_RED, label="", y=0.12)
    for x, z in ((-40.0, -96.0), (40.0, -108.0), (60.0, -90.0)):
        place(b, "box_pallet", x, z, 0.12)
    for x, z in ((-60.0, -84.0), (-58.0, -84.0), (110.0, -40.0), (-110.0, 0.0), (-112.0, 2.0)):
        place(b, "bin", x, z, 0.12)
    for x, z in ((24.0, -90.0), (28.0, -92.0), (32.0, -89.0)):
        place(b, "traffic_cone", x, z, 0.12)
    for x, z in ((-120.0, -110.0), (-112.0, -112.0), (120.0, -100.0), (128.0, -96.0)):
        b.box([x, 2.6, z], [5.0, 5.0, 5.0], "#a07a52", decal="crate_logo")
    car(b, 130.0, -10.0, "z", colour="#3a8a5a", y=0.12)
    car(b, -130.0, -40.0, "z", colour="#c8402a", y=0.12)
    place(b, "gift_box", 120.0, 20.0, 0.12)
    place(b, "toy_car", -128.0, 20.0, 0.12, 0)
    place(b, "rubber_duck", 150.0, -120.0, 0.12)


def _edges(b: ArenaArea, rng: random.Random) -> None:
    perimeter(b, 32.0, "#8a5a4a", cap="#6a4a3a", rng=rng, ragged=4.0)
    skirt(b, HALF[0], HALF[1], "#6a6460")
    backdrop(b, "city", -4.0, rng, colours=["#8a6a5a", "#a08070", "#7a6a7a", "#9a8a7a"],
             depth=70.0)


# ================================================================ the meta
def _on(b: ArenaArea, level: float, x: float, z: float) -> float:
    return b.surface(x, z, level + 1.0)


def _meta(b: ArenaArea) -> None:
    for x, z in ((-40.0, 50.0), (-20.0, 50.0), (20.0, 50.0), (40.0, 50.0), (-50.0, 66.0),
                 (50.0, 72.0), (-30.0, 80.0), (30.0, 80.0), (-20.0, 100.0), (20.0, 104.0),
                 (-60.0, 94.0), (60.0, 92.0), (-100.0, 60.0), (100.0, 70.0), (0.0, 60.0),
                 (0.0, 104.0)):
        b.team_spawn("props", x, None, z, yaw=3.14159)
    x0, x1, z0, z1 = PEN
    for x in (58.0, 62.0, 66.0, 70.0, 74.0, 78.0):
        for z in (-42.0, -47.0):
            b.team_spawn("hunters", x, F1, z, yaw=0.0)
    b.mark("pen", 66.0, F1, -44.0, r=14.0)
    hides = [
        (F1, -80.0, -18.0), (F1, -70.0, -4.0), (F1, -56.0, -20.0), (F1, -56.0, 14.0),
        (F1, -36.0, 24.0), (F1, -64.0, 28.0), (F1, -20.0, 26.0), (F1, 20.0, 28.0),
        (F1, 40.0, 26.0), (F1, 62.0, 8.0), (F1, 64.0, -14.0), (F1, 40.0, -8.0),
        (F1, 84.0, 12.0), (F1, -14.0, -20.0), (F1, 14.0, -30.0), (F1, -34.0, -28.0),
        (F1, -70.0, -56.0), (F1, -30.0, -46.0), (F1, -20.0, -66.0), (F1, 8.0, -66.0),
        (F1, 24.0, -48.0), (F1, 44.0, -56.0),
        (F2, -80.0, 10.0), (F2, -60.0, 26.0), (F2, -44.0, -26.0), (F2, -10.0, 26.0),
        (F2, 20.0, 18.0), (F2, 50.0, 18.0), (F2, 80.0, 2.0), (F2, 46.0, -24.0),
        (F2, -60.0, -50.0), (F2, -24.0, -54.0), (F2, 20.0, -48.0), (F2, 56.0, -46.0),
        (0.12, -60.0, 90.0), (0.12, 60.0, 90.0), (0.12, 20.0, 66.0), (0.12, -110.0, 80.0),
        (0.12, 120.0, 80.0), (0.12, -20.0, -100.0), (0.12, 50.0, -100.0), (0.12, 130.0, -60.0),
        (0.12, -130.0, -70.0), (0.12, 140.0, 30.0), (0.12, -140.0, 30.0),
    ]
    for level, x, z in hides:
        b.mark("hide", x, _on(b, level, x, z), z)
    searches = [
        (F1, 0.0, 20.0, "the tills"), (F1, -60.0, 0.0, "the plush department"),
        (F1, -74.0, 28.0, "the plush mountain"), (F1, 40.0, -10.0, "the ball pit"),
        (F1, 60.0, 26.0, "the block castle"), (F1, 0.0, -28.0, "the rocket"),
        (F1, -50.0, -58.0, "the workshop"), (F1, 22.0, -46.0, "the stockroom"),
        (F2, -60.0, 8.0, "the games corner"), (F2, 0.0, 18.0, "the music corner"),
        (F2, 60.0, 20.0, "outdoor toys"), (F2, -50.0, -54.0, "the space room"),
        (F2, 30.0, -46.0, "the party room"), (F2, 70.0, -40.0, "the bouncy castle"),
        (0.12, -60.0, 70.0, "the carousel"), (0.12, 20.0, 74.0, "the fountain"),
        (0.12, 70.0, 100.0, "the kiosk"), (0.12, 0.0, -110.0, "the loading yard"),
        (0.12, 120.0, 0.0, "the east alley"), (0.12, -120.0, 0.0, "the west alley"),
    ]
    for level, x, z, name in searches:
        b.mark("search", x, _on(b, level, x, z), z, name=name)
        b.landmark(x, z, name)
    b.landmark(66.0, -50.0, "the staff room")
    b.camera(0.0, 70.0, 160.0, 0.0, 10.0, 0.0)
    b.camera(60.0, 22.0, 30.0, -10.0, 8.0, -20.0)
    b.camera(-150.0, 60.0, -130.0, 0.0, 6.0, 0.0)
    # the atrium sees most of both floors: a shorter clock keeps it even
    b.extra.update({"accent": "#f2c230", "twist": "blackout", "pen_key": "pen", "round_seconds": 165.0})


BRASS = "#c89a3a"


def build(b: ArenaArea) -> None:
    rng = random.Random(4207)
    ground(b, "#8a8478", soil="#5a4a38", material="")
    s = Surfaces(b)
    s.reserve(rect(X0 - 0.5, X1 + 0.5, Z0 - 0.5, Z1 + 0.5))
    s.reserve(rect(-10.0, 10.0, Z1, Z1 + 3.0))
    s.reserve(rect(-10.0, 10.0, 70.0, 90.0))
    s.reserve(rect(-89.0, -67.0, 71.0, 93.0))
    _edges(b, rng)
    _shell(b)
    _partitions(b)
    _paint(b)
    _stairs(b)
    _lights(b)
    _ground_floor(b)
    _back_rooms(b)
    _upstairs(b)
    _square(b, s)
    _alleys(b, s)
    _meta(b)
    cat.finish(b, "toy_block")
