"""MegaMart -- a supermarket on the edge of town: aisles of cereal boxes and
giant sodas, a produce hall, a bakery, the freezers, the checkouts, the
warehouse out back, a garden centre and a car park full of trolleys.

Layout (north is -z; the car park is to the south)::

    z -150  ============== the loading dock (lorry, pallets) ================
    z  -80  - WAREHOUSE (pallets, racks) -|- THE FREEZERS along the back -|
                                          |                              |  GARDEN
    z  -46       AISLES 1 - 7             |  PRODUCE HALL    BAKERY      |  CENTRE
                 (cereal, soda, rolls,    |  (melons and pumpkins)       |  (plants,
    z   -6        paint, flour...)        |                              |  gnomes,
    z   12       THE CHECKOUTS     service desk              SECURITY    |  shed)
    z   30  ====== windows === IN === OUT ========= windows === (pen) ====
             the car park: rows of cars, trolley shelters, the recycling
    z  150  ==================================================================

The seekers wait in the security office (the ``pen`` door into the
store).  The twist is the tannoy's flash sales (the rules' ``sale``).
"""
from __future__ import annotations

import random

from ..kit import (ArenaArea, Surfaces, backdrop, car, carve, ground, letters, perimeter,
                   rect, sign_decal, slab, strip_light, wall_sign)
from ...lastlight.kit import van
from . import catalogue as cat
from . import furniture as fx
from .catalogue import place, stamp
from .rooms import (PAINT, covering, door_holes, interior, openings, paint, partition, pen_door,
                    shell, skirt)

HALF = (180.0, 150.0)
SKY = {"top": "#7ab4e8", "horizon": "#e8f4f8", "sun": [0.35, 0.8, 0.4], "clouds": 0.5,
       "tint": "#ffffff"}
AMBIENT = "#b8c0c8"
GROUND = "#6a7078"
FOG = 760.0

TEAL = "#2ab0a0"
TEAL_DARK = "#1a7a70"
WALL = "#e8ecec"
TILE = "#eef0ee"
ASPHALT = "#4a4e54"
RED, YELLOW, BLUE, GREEN, ORANGE = "#d8402a", "#f2c230", "#3a8ad8", "#3aa04a", "#f08a2a"
TRIM = "#f4f4f4"

T = 1.2
F1, C1 = 0.6, 20.0
WALL_TOP = 20.6
X0, X1, Z0, Z1 = -110.0, 70.0, -80.0, 30.0
IX0, IX1, IZ0, IZ1 = X0 + T, X1 - T, Z0 + T, Z1 - T
P = 0.6
WAREHOUSE = rect(IX0, -20.0 - P / 2.0, IZ0, -58.0 - P / 2.0)
PEN = rect(48.0 + P / 2.0, IX1, 8.0 + P / 2.0, IZ1)
PEN_DOOR = (14.0, 20.0)
GONDOLAS = [-96.0, -84.0, -72.0, -60.0, -48.0, -36.0, -24.0]
SEGMENTS = [(-46.0, -28.0), (-24.0, -6.0)]
AISLES = ["CEREAL", "DRINKS", "HOUSEHOLD", "BAKING", "BREAKFAST", "PARTY", "DIY"]
# what stands on the floor of each aisle, off to one side: (x, z, kind, quarter)
FLOOR_DISPLAYS = [
    (-88.1, -31.0, "box_pallet", 0), (-91.9, -10.0, "flour_sack", 1),
    (-79.9, -31.0, "basket", 1), (-76.1, -12.0, "soda_bottle", 0),
    (-64.1, -33.0, "toilet_rolls", 0), (-67.9, -17.0, "box_pallet", 0),
    (-55.9, -42.0, "flour_sack", 1), (-52.1, -14.0, "basket", 0),
    (-40.1, -33.0, "box_pallet", 0), (-43.9, -10.0, "paint_can", 0),
    (-31.9, -32.0, "trolley", 0), (-28.1, -14.0, "box_pallet", 0),
]

FRONT = [(-30.0, -14.0, 0.0, 9.0), (4.0, 20.0, 0.0, 9.0),
         (-100.0, -40.0, 2.0, 12.0), (26.0, 44.0, 2.0, 12.0)]
BACK = [(-90.0, -74.0, 0.0, 12.0), (30.0, 36.0, 0.0, 9.0)]
WEST = [(0.0, 6.0, 0.0, 9.0), (10.0, 24.0, 2.0, 12.0)]
EAST = [(-20.0, -8.0, 0.0, 10.0), (-50.0, -30.0, 2.0, 12.0)]


# ================================================================ the store
def _shell(b: ArenaArea) -> None:
    shell(b, rect(X0, X1, Z0, Z1), 0.0, WALL_TOP, WALL,
          {"z+": FRONT, "z-": BACK, "x-": WEST, "x+": EAST}, frame=TEAL)
    slab(b, rect(IX0, IX1, IZ0, IZ1), F1, F1, "#c8ccc8")
    for a, c, _, _ in FRONT[:2]:
        slab(b, rect(a, c, IZ1, Z1), F1, F1, "#c8ccc8")
    for a, c, _, _ in BACK:
        slab(b, rect(a, c, Z0, IZ0), F1, F1, "#c8ccc8")
    slab(b, rect(X0, IX0, 0.0, 6.0), F1, F1, "#c8ccc8")
    slab(b, rect(IX1, X1, -20.0, -8.0), F1, F1, "#c8ccc8")
    slab(b, rect(IX0, IX1, IZ0, IZ1), WALL_TOP, WALL_TOP - C1, "#f4f6f4")
    slab(b, rect(X0 - 0.5, X1 + 0.5, Z0 - 0.5, Z1 + 0.5), WALL_TOP + 1.0, 1.0, "#5a6068")
    # the big teal fascia and the name
    b.box([-20.0, WALL_TOP + 3.4, Z1 + 0.3], [X1 - X0 + 1.0, 5.6, 0.6], TEAL)
    # channel letters, one board each, so the name stays crisp from the car park
    letters(b, -20.0, WALL_TOP + 3.4, Z1 + 0.6, "MEGAMART", 4.6, TEAL, TRIM)
    # a canopy over the doors
    slab(b, rect(-34.0, 24.0, Z1, Z1 + 6.0), 10.4, 0.6, TEAL)
    for x in (-33.0, 23.0):
        b.box([x, 5.0, Z1 + 5.4], [0.8, 9.8, 0.8], "#c8ccd0", material="metal")


def _roof(b: ArenaArea) -> None:
    """Plant on the roof: air handlers, skylights over the aisles, vents."""
    y = WALL_TOP + 1.0
    for x, z in ((-92.0, -60.0), (-62.0, -60.0), (-2.0, -66.0), (34.0, -66.0), (52.0, 4.0)):
        b.box([x, y + 2.0, z], [10.0, 4.0, 7.0], "#c8ccd0", material="metal", decal="panels")
        for dx in (-2.5, 2.5):
            b.cyl([x + dx, y + 4.15, z], [3.6, 0.3, 3.6], "#3a3e44", material="metal")
        b.box([x - 6.0, y + 0.8, z], [2.0, 1.6, 1.6], "#9aa0a8", material="metal")
    for gx in GONDOLAS[1::2]:
        for zc in (-37.0, -15.0):
            b.box([gx, y + 0.25, zc], [7.0, 0.5, 12.0], "#5a6068")
            b.box([gx, y + 0.9, zc], [6.0, 0.8, 11.0], "#bfe8ff", material="glass", alpha=0.6)
    for x, z in ((-40.0, -66.0), (10.0, -20.0), (40.0, 0.0), (-100.0, 10.0), (-70.0, 16.0)):
        b.cyl([x, y + 1.5, z], [1.2, 3.0, 1.2], "#9aa0a8", material="metal")
        b.cyl([x, y + 3.2, z], [2.0, 0.4, 2.0], "#7a8088", material="metal")


def _partitions(b: ArenaArea) -> None:
    partition(b, "x", -58.0, IX0, -20.0 + P / 2.0, F1, C1, "#d8dcd8", [(-74.0, -62.0, 12.0)],
              trim_colour="#f2c230")
    partition(b, "z", -20.0, IZ0, -58.0 - P / 2.0, F1, C1, "#d8dcd8")
    partition(b, "x", 8.0, 48.0 - P / 2.0, IX1, F1, C1, "#c8d0d8")
    partition(b, "z", 48.0, 8.0 + P / 2.0, IZ1, F1, C1, "#c8d0d8", [(PEN_DOOR[0], PEN_DOOR[1], 9.0)],
              trim_colour=TEAL)
    pen_door(b, "z", 48.0, PEN_DOOR[0], PEN_DOOR[1], F1, 9.0, 0.5, "#a8b0b8")
    wall_sign(b, 48.0 - P / 2.0 - 0.35, F1 + 10.6, 17.0, 9.0, 1.6,
              sign_decal("SECURITY", YELLOW, "#1b2a35", 5.6), "x-", YELLOW)


def _paint(b: ArenaArea) -> None:
    def win(holes, lo, hi):
        return [h for h in holes if h[1] > lo and h[0] < hi]

    # the shop floor's own walls stop at the warehouse and the office
    paint(b, "z", IX0, 1, -58.0 + P / 2.0, IZ1, F1, C1, WALL, win(WEST, -58.0, IZ1))
    paint(b, "z", IX1, -1, IZ0, 8.0 - P / 2.0, F1, C1, "#d8f0d8", win(EAST, IZ0, 8.0))
    paint(b, "x", IZ0, 1, -20.0 + P / 2.0, IX1 - PAINT, F1, C1, "#c8e8f0", win(BACK, -20.0, IX1))
    paint(b, "x", IZ1, -1, IX0 + PAINT, 48.0 - P / 2.0, F1, C1, WALL, win(FRONT, IX0, 48.0))
    holes = [WAREHOUSE, rect(48.0 - P / 2.0, IX1 + 0.1, 8.0 - P / 2.0, IZ1 + 0.1),
             rect(-20.0 - P / 2.0, -20.0 + P / 2.0, IZ0, -58.0),
             rect(IX0, -20.0 + P / 2.0, -58.0 - P / 2.0, -58.0 + P / 2.0)]
    for piece in carve(rect(IX0, IX1, IZ0, IZ1), holes):
        covering(b, piece, F1, TILE)
    interior(b, WAREHOUSE, F1, C1, "#b8bcb8",
             {"x-": win(WEST, IZ0, -58.0), "z-": win(BACK, IX0, -20.0),
              "z+": door_holes([(-74.0, -62.0, 12.0)], F1)}, floor="#9a9e98")
    interior(b, PEN, F1, C1, "#c8d8e8", {"x-": door_holes([(14.0, 20.0, 9.0)], F1),
                                         "z+": win(FRONT, 48.0, IX1)}, floor="#5a6a7a")


def _lights(b: ArenaArea) -> None:
    for x in (-102.0, -90.0, -78.0, -66.0, -54.0, -42.0, -30.0, -18.0, 0.0, 20.0, 40.0, 60.0):
        strip_light(b, x, -26.0, C1, 36.0, "z")
        if x < 40.0:
            strip_light(b, x, 18.0, C1, 12.0, "z")
    for x in (-90.0, -60.0, -36.0):
        strip_light(b, x, -68.0, C1, 14.0, "z")
    strip_light(b, 58.0, 18.0, C1, 12.0, "z")


# ============================================================ the shelves
PRODUCTS = [
    ["cereal_box", "cereal_box", "cereal_box"],
    ["soda_bottle", "soda_bottle", "basket"],
    ["toilet_rolls", "toilet_rolls", "fire_extinguisher"],
    ["flour_sack", "cheese_wheel", "flour_sack"],
    ["cereal_box", "basket", "cheese_wheel"],
    ["soda_bottle", "cereal_box", "toilet_rolls"],
    ["paint_can", "paint_can", "paint_can"],
]


# the packets that fill each aisle's shelves round its props: (width,
# height range, colours, decal)
PACKETS = [
    (1.3, (2.0, 2.6), ["#f2c230", "#d8402a", "#3a8ad8", "#f08a2a"], "ea25_barlabel"),
    (0.8, (1.8, 2.6), ["#c8202e", "#3a8a5a", "#f2c230", "#e8eaec"], "cola"),
    (1.6, (1.6, 2.4), ["#e8f0f8", "#8ac8f0", "#f0f0f0", "#c8e8c8"], ""),
    (1.4, (1.4, 2.2), ["#f4ece0", "#e8d8b0", "#c8a070", "#f0e0c8"], "ea24_feedlabel"),
    (1.0, (1.4, 2.0), ["#d8402a", "#a050d0", "#f2c230", "#2a6ab0"], "ea25_chocbar"),
    (1.2, (1.6, 2.4), ["#ec4aa0", "#3a72d0", "#f0be2c", "#2f9e5c"], "ea25_wrappers"),
    (1.2, (1.4, 1.8), ["#8a9098", "#c8402a", "#2a6ab0", "#f2c230"], ""),
]


def _packets(b: ArenaArea, rng: random.Random, aisle: int, x: float, lo: float, hi: float,
             y: float, facing: int) -> None:
    """A row of packets along a shelf from ``lo`` to ``hi`` (z), their labels
    to the aisle (``facing`` +1 looks along +x)."""
    width, (h0, h1), colours, decal = PACKETS[aisle]
    n = int((hi - lo + 0.1) // (width + 0.1))
    if n < 1:
        return
    start = (lo + hi) / 2.0 - (n * (width + 0.1) - 0.1) / 2.0 + width / 2.0
    turn = 1.5708 * facing
    for k in range(n):
        h = round(rng.uniform(h0, h1), 1)
        b.box([x, y + h / 2.0, start + k * (width + 0.1)], [width, h, 1.6], rng.choice(colours),
              r=[0.0, turn, 0.0], decal=decal if decal and rng.random() < 0.7 else "")


def _aisles(b: ArenaArea) -> None:
    y = F1
    rng = random.Random(512)
    tops = [y + t for t in fx.shelf_tops(3)]
    colours = ["#e8eaec", "#f0e8e0"]
    for g, gx in enumerate(GONDOLAS):
        stock = PRODUCTS[g]
        for s, (z0, z1) in enumerate(SEGMENTS):
            zc = (z0 + z1) / 2.0
            w = z1 - z0
            stamp(b, fx.shelf_unit(w, 3, colour=colours[g % 2]), gx + 1.2, zc, y, 1)
            stamp(b, fx.shelf_unit(w, 3, colour=colours[g % 2]), gx - 1.2, zc, y, 3)
            for side, q in ((1.3, 1), (-1.3, 3)):
                for level in (0, 1, 2):
                    edge = z0 + 0.4
                    for k, dz in enumerate((-5.6, 0.0, 5.6)):
                        if (g + s + level + k + (q == 3)) % 3 == 2:
                            continue
                        kind = stock[(k + level) % len(stock)]
                        place(b, kind, gx + side, zc + dz, tops[level], q)
                        _packets(b, rng, g, gx + side * 1.08, edge, zc + dz - 1.1, tops[level],
                                 1 if q == 1 else -1)
                        edge = zc + dz + 1.1
                    _packets(b, rng, g, gx + side * 1.08, edge, z1 - 0.4, tops[level],
                             1 if q == 1 else -1)
        # the aisle sign hanging over the front end of the gondola
        b.box([gx, 16.0, -4.0], [9.0, 2.0, 0.3], TEAL,
              decal=sign_decal("%d %s" % (g + 1, AISLES[g]), TEAL, TRIM, 4.5))
        for dx in (-3.6, 3.6):
            b.cyl([gx + dx, 18.5, -4.0], [0.12, 3.0, 0.12], "#8a9098")
    for gx in GONDOLAS[::2]:
        place(b, "wet_floor", gx + 6.0, -26.0, y, 0)
    # floor displays down the aisles and stands at the gondolas' ends: more
    # to blend in with on the floor, and no aisle to see straight down
    for x, z, kind, q in FLOOR_DISPLAYS:
        place(b, kind, x, z, y, q)
    for g, gx in enumerate(GONDOLAS):
        stock = PRODUCTS[g]
        ends = [y + t for t in fx.shelf_tops(2)]
        for z, q in ((SEGMENTS[0][0] - 1.2, 2), (SEGMENTS[1][1] + 1.2, 0)):
            stamp(b, fx.shelf_unit(4.6, 2, colour=TEAL if g % 2 else "#e8eaec"), gx, z, y, q)
            front = z + (0.1 if q == 0 else -0.1)
            for level in (0, 1):
                place(b, stock[level % len(stock)], gx - 1.0, front, ends[level], q)
                place(b, stock[(level + 1) % len(stock)], gx + 1.0, front, ends[level], q)
    place(b, "basket", -102.0, -20.0, y, 1)
    place(b, "trolley", -102.0, -40.0, y, 0)
    place(b, "trolley", -66.0, -26.0, y, 1)
    place(b, "basket", -30.0, -2.0, y, 2)
    place(b, "fire_extinguisher", IX0 + 0.6, -6.0, y)
    place(b, "fire_extinguisher", IX1 - 0.6, 4.0, y)
    place(b, "fire_extinguisher", -21.0, -56.8, y)


def _fresh(b: ArenaArea) -> None:
    y = F1
    # the produce hall: tables of fruit and crates of veg
    for x in (8.0, 22.0, 36.0):
        for z in (-36.0, -18.0):
            stamp(b, fx.table(8.0, 5.0, top="#a07a52", legs="#7a5335", h=2.6), x, z, y)
            place(b, "watermelon" if (x + z) % 4 else "pumpkin", x - 2.2, z, y + 2.6)
            place(b, "pumpkin" if (x + z) % 4 else "watermelon", x + 2.2, z, y + 2.6, 1)
    for x, z in ((2.0, -4.0), (14.0, -4.0), (28.0, -4.0), (42.0, -4.0)):
        b.box([x, y + 1.0, z], [4.0, 2.0, 4.0], "#a07a52", decal="planks")
        place(b, "pumpkin" if x > 20 else "watermelon", x, z, y + 2.0)
    place(b, "pumpkin", 2.0, -46.0, y)
    place(b, "watermelon", 44.0, -46.0, y, 1)
    # islands of crates heaped with fruit between the tables
    fruit = ["#f08a2a", "#c8302a", "#f2d23a", "#5aa03a", "#8a3a8a", "#e8c838"]
    k = 0
    for ix in (6.0, 34.0):
        for dx in (-2.2, 2.2):
            for dz in (-0.8, 0.8):
                colour = fruit[k % len(fruit)]
                k += 1
                cx, cz = ix + dx, -27.0 + dz
                b.box([cx, y + 0.8, cz], [4.0, 1.6, 1.4], "#a07a52", decal="planks")
                b.box([cx, y + 1.75, cz], [3.6, 0.3, 1.0], colour)
                for sx in (-1.1, 0.0, 1.1):
                    b.sphere([cx + sx, y + 2.2, cz], [0.7, 0.7, 0.7], colour)
    # the bakery and its counter
    stamp(b, fx.counter(16.0, body="#c8a070", top="#f4ece0", doors="#e8d0b0"), IX1 - 1.8, -38.0, y, 3)
    top = y + fx.COUNTER_TOP
    for z in (-44.0, -40.0, -36.0, -32.0):
        b.box([IX1 - 1.6, top + 0.5, z], [1.4, 1.0, 2.6], "#d8a868", collide=True)
    place(b, "cheese_wheel", IX1 - 1.8, -42.0, top)
    place(b, "cheese_wheel", IX1 - 1.8, -34.0, top)
    wall_sign(b, IX1 - PAINT - 0.35, F1 + 9.0, -38.0, 10.0, 2.4,
              sign_decal("BAKERY", ORANGE, TRIM, 4.2), "x-", ORANGE)
    # the freezers along the back wall
    for k, x in enumerate(range(-14, 66, 8)):
        stamp(b, [cat.B(0.0, 0.0, 0.0, 7.6, 10.0, 3.4, "#e8f0f4", m="metal"),
                  cat.B(0.0, 1.0, 1.72, 7.0, 8.4, 0.06, "#bfe8ff", m="glass"),
                  cat.B(0.0, 10.0, 0.0, 7.8, 1.0, 3.6, TEAL),
                  cat.B(0.0, 4.0, 1.0, 6.6, 0.2, 1.2, "#c8ccd0"),
                  cat.B(0.0, 7.0, 1.0, 6.6, 0.2, 1.2, "#c8ccd0")], x, IZ0 + 1.7, y)
    place(b, "water_cooler", 26.0, IZ0 + 5.6, y)
    place(b, "fire_extinguisher", 38.0, IZ0 + 4.6, y)
    place(b, "wet_floor", 12.0, -60.0, y, 1)


def _front(b: ArenaArea) -> None:
    y = F1
    for x in (-100.0, -90.0, -80.0, -70.0, -60.0, -50.0):
        stamp(b, fx.till_counter(8.0, 3.0), x, 16.0, y, 1)
        place(b, "cash_register", x, 19.0, y + 3.0, 1)
        b.cyl([x + 1.2, y + 7.0, 12.4], [0.2, 4.0, 0.2], "#8a9098")
        b.box([x + 1.2, y + 9.4, 12.4], [1.0, 1.0, 1.0], ["#7aff8a", "#ff6a5a"][int(x) % 2],
              material="neon")
    for x in (-95.0, -75.0, -55.0):
        place(b, "basket", x, 6.0, y, 0)
    stamp(b, fx.counter(10.0, body=TEAL, top="#f4f4f4", doors="#3ac0b0"), -6.0, 22.0, y, 2)
    place(b, "cash_register", -8.0, 22.0, y + fx.COUNTER_TOP, 2)
    wall_sign(b, -6.0, y + 10.0, IZ1 - PAINT - 0.35, 10.0, 1.8,
              sign_decal("CUSTOMER SERVICE", TEAL, TRIM, 5.5), "z-", TEAL)
    for x in (-40.0, -44.0):
        place(b, "trolley", x, 22.0, y, 2)
    place(b, "potted_plant", 22.0, 26.0, y)
    place(b, "potted_plant", -36.0, 26.0, y)
    place(b, "water_cooler", 30.0, 26.0, y)
    # the security office: the seekers' pen
    x0, x1, z0, z1 = PEN
    stamp(b, fx.counter(12.0, body="#3a4a5a", top="#2a2a2a", doors="#4a5a6a"), 60.0, z0 + 1.8, y)
    for k, x in enumerate((55.0, 60.0, 65.0)):
        b.box([x, y + fx.COUNTER_TOP + 1.6, z0 + 0.8], [4.0, 3.0, 0.4], "#1a2a2a",
              decal="neongrid")
    for k in range(4):
        b.box([x1 - 1.2, y + 4.0, 14.0 + k * 3.0], [2.4, 8.0, 2.8], "#6a7a8a", material="metal")
    place(b, "water_cooler", 51.0, 11.5, y, hide=False)
    place(b, "dining_chair", 57.0, 13.4, y, 2, hide=False)
    place(b, "dining_chair", 63.0, 13.4, y, 2, hide=False)


def _warehouse(b: ArenaArea) -> None:
    y = F1
    for x in (-100.0, -50.0):
        stamp(b, fx.shelf_unit(14.0, 4, colour="#3a6aa8"), x, IZ0 + 1.2, y)
    tops = [y + t for t in fx.shelf_tops(4)]
    for x, level, kind in ((-104.0, 1, "toilet_rolls"), (-98.0, 1, "flour_sack"),
                           (-54.0, 1, "paint_can"), (-46.0, 1, "toilet_rolls"),
                           (-102.0, 2, "flour_sack"), (-48.0, 2, "cereal_box"),
                           (-96.0, 3, "toilet_rolls"), (-52.0, 3, "paint_can")):
        place(b, kind, x, IZ0 + 1.4, tops[level])
    for x, z in ((-100.0, -66.0), (-60.0, -72.0), (-52.0, -64.0), (-40.0, -72.0), (-30.0, -64.0),
                 (-90.0, -62.0)):
        place(b, "box_pallet", x, z, y)
    for x, z in ((-66.0, -62.0), (-64.0, -62.0)):
        place(b, "toilet_rolls", x, z, y)
    place(b, "flour_sack", -46.0, -76.0, y)
    place(b, "flour_sack", -44.0, -76.0, y)
    place(b, "traffic_cone", -72.0, -76.0, y)
    # the forklift
    stamp(b, [cat.B(0.0, 0.0, 0.0, 3.6, 2.4, 5.0, YELLOW),
              cat.B(0.0, 2.4, -0.8, 3.4, 3.0, 2.6, "#2a2a2a"),
              cat.B(0.0, 5.4, -0.8, 3.6, 0.3, 3.0, YELLOW),
              cat.B(-1.2, 0.0, 2.65, 0.3, 6.0, 0.3, "#3a3a3a", m="metal"),
              cat.B(1.2, 0.0, 2.65, 0.3, 6.0, 0.3, "#3a3a3a", m="metal"),
              cat.B(0.0, 0.2, 3.6, 3.0, 0.2, 1.6, "#3a3a3a", m="metal")], -76.0, -70.0, y, 1)


# ============================================================ outside
def _car_park(b: ArenaArea, s: Surfaces) -> None:
    s.lay(rect(-HALF[0], HALF[0], Z1, Z1 + 6.0), 0.3, "#a8a8a0")
    s.lay(rect(-HALF[0], HALF[0], Z1 + 6.0, HALF[1]), 0.1, ASPHALT)
    for z in (60.0, 90.0, 120.0):
        for x in range(-170, 175, 10):
            b.box([x, 0.11, z], [0.4, 0.02, 10.0], "#e8e8e0", collide=False)
    rng = random.Random(77)
    colours = ["#c8402a", "#3a6ab0", "#e8e8e8", "#2a2a2a", "#f2c230", "#3a8a5a", "#8a3a6a"]
    for z in (60.0, 90.0, 120.0):
        for x in range(-165, 170, 10):
            if rng.random() < 0.45 or -60 < x < -40 or 30 < x < 50:
                continue
            car(b, x, z, "z", colour=rng.choice(colours), y=0.1, length=9.5)
    # trolley shelters
    for sx, sz in ((-50.0, 75.0), (40.0, 105.0)):
        for dx in (-5.0, 5.0):
            for dz in (-4.0, 4.0):
                b.box([sx + dx, 4.1, sz + dz], [0.4, 8.0, 0.4], "#8a9098", material="metal")
        slab(b, rect(sx - 5.6, sx + 5.6, sz - 4.6, sz + 4.6), 8.6, 0.5, TEAL)
        b.box([sx, 1.6, sz - 4.0], [9.6, 0.3, 0.2], "#8a9098", material="metal")
        for k, dz in enumerate((-1.0, 2.6)):
            place(b, "trolley", sx - 2.0 + k * 4.0, sz + dz * 0.4, 0.1, k % 2 * 2)
    for x in (-120.0, -80.0, -20.0, 20.0, 80.0, 120.0):
        stamp(b, fx.lamp_stand(14.0), x, 75.0, 0.1)
        stamp(b, fx.lamp_stand(14.0), x, 105.0, 0.1)
    # the recycling
    b.box([-160.0, 3.1, 44.0], [14.0, 6.0, 6.0], "#2a6a4a")
    for x in (-170.0, -150.0, -146.0, -142.0):
        place(b, "bin", x, 50.0, 0.1)
    for x, z in ((110.0, 50.0), (114.0, 54.0), (118.0, 50.0), (-20.0, 136.0)):
        place(b, "traffic_cone", x, z, 0.1)
    for x, z, q in ((-100.0, 44.0, 0), (60.0, 140.0, 2), (150.0, 75.0, 1), (-140.0, 132.0, 3)):
        place(b, "trolley", x, z, 0.1, q)
    place(b, "basket", 16.0, 40.0, 0.3)
    place(b, "potted_plant", -36.0, 33.0, 0.3)
    place(b, "potted_plant", 24.0, 33.0, 0.3)
    # the bus stop by the road
    stamp(b, [cat.B(-3.2, 0.0, 0.0, 0.3, 8.0, 0.3, "#b8bcc2"), cat.B(3.2, 0.0, 0.0, 0.3, 8.0, 0.3, "#b8bcc2"),
              cat.B(0.0, 0.0, -1.2, 6.1, 8.0, 0.2, "#cfe8ff", m="glass", a=0.4),
              cat.B(0.0, 8.0, -0.3, 7.2, 0.4, 3.0, TEAL)], 150.0, 140.0, 0.1, 2)
    stamp(b, fx.bench(5.0), 150.0, 140.0, 0.1, 2)


def _garden_centre(b: ArenaArea, s: Surfaces) -> None:
    gx0, gx1, gz0, gz1 = X1, HALF[0], -60.0, Z1
    s.lay(rect(gx0, gx1, gz0, gz1), 0.12, "#b8a888")
    # the fence: open at the store's doors, a gate to the car park and one north
    for a, c in ((gx0, 100.0), (116.0, gx1)):
        b.box([(a + c) / 2.0, 3.0, gz1 - 0.5], [c - a, 6.0, 0.3], "#3a6a3a", decal="netting")
    for a, c in ((gx0, 120.0), (130.0, gx1)):
        b.box([(a + c) / 2.0, 3.0, gz0 + 0.5], [c - a, 6.0, 0.3], "#3a6a3a", decal="netting")
    b.box([gx0 + 3.0, 7.6, gz1 + 0.5], [18.0, 2.4, 0.4], GREEN,
          decal=sign_decal("GARDEN CENTRE", GREEN, TRIM, 7.5))
    y = 0.12
    for x in (88.0, 116.0):
        for z in (-42.0, -22.0, -2.0):
            stamp(b, fx.table(12.0, 4.0, top="#7a5335", legs="#543923", h=2.6), x, z, y, 1)
            for dz, kind in ((-4.0, "flower_pot"), (0.0, "potted_plant"), (4.0, "flower_pot")):
                place(b, kind, x, z + dz, y + 2.6)
    # the gnome stand
    for k in range(3):
        b.box([150.0, y + 0.8 + k * 1.6, -40.0 + k * 2.0], [12.0, 1.6 + k * 0.0, 8.0 - k * 2.0], "#a07a52")
    for k in range(3):
        for dx in (-3.6, 0.0, 3.6):
            if k == 2 and dx == 0.0:
                continue
            place(b, "garden_gnome", 150.0 + dx, -42.6 + k * 2.0 + 1.6, y + 1.6 * (k + 1), 0)
    for x, z in ((140.0, 4.0), (150.0, 14.0), (162.0, -6.0)):
        place(b, "birdbath", x, z, y)
    place(b, "wheelbarrow", 134.0, -52.0, y, 1)
    place(b, "wheelbarrow", 172.0, 20.0, y, 0)
    for x, z in ((100.0, 18.0), (128.0, -10.0), (170.0, -48.0)):
        place(b, "watering_can", x, z, y, 1)
    for x, z in ((78.0, -54.0), (102.0, -54.0), (140.0, 24.0), (176.0, 4.0), (128.0, 18.0),
                 (106.0, 8.0)):
        place(b, "potted_plant", x, z, y)
    for x, z in ((80.0, 22.0), (84.0, 22.0), (164.0, -30.0)):
        place(b, "flour_sack", x, z, y)
    # the display shed
    sx0, sx1, sz0, sz1 = 152.0, 172.0, 6.0, 22.0
    t = 0.6
    openings(b, "z", sx0 + t / 2.0, t, sz0, sz1, y, y + 8.0, "#7a5335", [(11.0, 17.0, y - 1.0, y + 6.8)])
    openings(b, "z", sx1 - t / 2.0, t, sz0, sz1, y, y + 8.0, "#7a5335",
             [(11.0, 17.0, y + 3.0, y + 5.6)], glass=True)
    openings(b, "x", sz0 + t / 2.0, t, sx0 + t, sx1 - t, y, y + 8.0, "#7a5335")
    openings(b, "x", sz1 - t / 2.0, t, sx0 + t, sx1 - t, y, y + 8.0, "#7a5335",
             [(158.0, 166.0, y + 3.0, y + 5.6)], glass=True)
    slab(b, rect(sx0 - 0.6, sx1 + 0.6, sz0 - 0.6, sz1 + 0.6), y + 8.6, 0.6, "#3a4a3a")
    slab(b, rect(sx0 + t, sx1 - t, sz0 + t, sz1 - t), y + 0.3, 0.3, "#a07a52")
    slab(b, rect(sx0, sx0 + t, 11.0, 17.0), y + 0.3, 0.3, "#a07a52")
    place(b, "garden_gnome", 168.0, 10.0, y + 0.3, 3)
    place(b, "watering_can", 168.0, 18.0, y + 0.3, 3)
    place(b, "flower_pot", 160.0, 19.6, y + 0.3)


def _yards(b: ArenaArea, s: Surfaces) -> None:
    s.lay(rect(-HALF[0], HALF[0], -HALF[1], Z0), 0.1, "#8a8e90")
    s.lay(rect(-HALF[0], X0, Z0, Z1), 0.1, "#8a8e90")
    s.lay(rect(X1, HALF[0], Z0, -60.0), 0.1, "#8a8e90")
    # lorry bays painted on the yard
    for x in (-110.0, -96.0, -68.0, -54.0):
        b.box([x, 0.11, -118.0], [0.4, 0.02, 40.0], "#f2c230", collide=False)
    # shipping containers and the cardboard baler's bales
    for x, z, colour in ((100.0, -128.0, "#c8402a"), (128.0, -128.0, "#2a6ab0"),
                         (114.0, -104.0, "#3a8a5a")):
        b.box([x, 5.1, z], [24.0, 10.0, 9.0], colour, material="metal", decal="panels")
        b.box([x + 12.1, 5.1, z], [0.2, 9.0, 8.0], "#5a5e64", material="metal")
    for x, z in ((60.0, -134.0), (65.0, -134.0), (70.0, -134.0), (60.0, -139.0), (65.0, -139.0)):
        b.box([x, 2.1, z], [4.6, 4.0, 4.6], "#b08a5a", decal="straw")
    b.box([62.5, 6.1, -136.5], [4.6, 4.0, 4.6], "#b08a5a", decal="straw")
    # a skip
    stamp(b, [cat.B(0.0, 0.0, 0.0, 12.0, 0.6, 6.0, YELLOW, m="metal"),
              cat.B(0.0, 0.6, -2.85, 12.0, 4.4, 0.3, YELLOW, m="metal"),
              cat.B(0.0, 0.6, 2.85, 12.0, 4.4, 0.3, YELLOW, m="metal"),
              cat.B(-5.85, 0.6, 0.0, 0.3, 4.4, 5.4, YELLOW, m="metal"),
              cat.B(5.85, 0.6, 0.0, 0.3, 4.4, 5.4, YELLOW, m="metal"),
              cat.B(0.0, 0.6, 0.0, 11.4, 1.6, 5.4, "#7a6a58")], 20.0, -96.0, 0.1)
    # the staff shelter by the back door
    stamp(b, [cat.B(-4.0, 0.0, 0.0, 0.3, 8.0, 0.3, "#8a9098", m="metal"),
              cat.B(4.0, 0.0, 0.0, 0.3, 8.0, 0.3, "#8a9098", m="metal"),
              cat.B(0.0, 0.0, -1.6, 7.7, 7.0, 0.2, "#cfe8ff", m="glass", a=0.4),
              cat.B(0.0, 8.0, -0.4, 9.0, 0.4, 4.0, TEAL)], 46.0, -90.0, 0.1)
    stamp(b, fx.bench(6.0), 46.0, -90.6, 0.1)
    # the dock outside the warehouse door, its bumpers and its sign
    slab(b, rect(-96.0, -68.0, -88.0, Z0), 1.2, 1.1, "#a8aca8")
    for x in (-92.0, -84.0, -76.0, -72.0):
        b.box([x, 0.6, -88.3], [1.2, 0.9, 0.6], "#2a2a2a")
    wall_sign(b, -82.0, 14.0, Z0 - 0.35, 14.0, 2.0,
              sign_decal("DELIVERIES", YELLOW, "#1b2a35", 7.0), "z-", YELLOW)
    for x in (-100.0, -64.0, 33.0):
        b.box([x, 13.0, Z0 - 0.4], [1.6, 1.0, 0.8], "#3a3e44", material="metal")
        b.box([x, 12.3, Z0 - 0.4], [1.2, 0.4, 0.6], "#fff2c8", material="neon")
    van(b, -82.0, -106.0, "z", colour="#e8ecec", stripe=TEAL, length=24.0, y=0.1, front=-1)
    for x, z in ((-50.0, -100.0), (-40.0, -110.0), (-20.0, -96.0), (20.0, -120.0), (60.0, -100.0)):
        place(b, "box_pallet", x, z, 0.1)
    for x, z in ((20.0, -86.0), (24.0, -86.0), (-120.0, -60.0)):
        place(b, "bin", x, z, 0.1)
    for x, z in ((0.0, -130.0), (4.0, -134.0), (90.0, -120.0)):
        place(b, "traffic_cone", x, z, 0.1)
    for x, z in ((100.0, -140.0), (106.0, -140.0), (-150.0, -130.0)):
        b.box([x, 2.6, z], [5.0, 5.0, 5.0], "#a07a52", decal="crate_logo")
    car(b, -140.0, -20.0, "z", colour="#3a6ab0", y=0.1)
    b.box([X0 - 0.3, 5.0, 14.0], [0.6, 3.0, 2.4], "#3a4a5a")
    place(b, "fire_extinguisher", -112.0, -40.0, 0.1)
    place(b, "trolley", -130.0, 10.0, 0.1, 1)
    place(b, "bin", -114.0, -10.0, 0.1)


def _edges(b: ArenaArea, rng: random.Random) -> None:
    perimeter(b, 30.0, "#7a7e84", cap="#5a5e64", rng=rng, ragged=3.0)
    skirt(b, HALF[0], HALF[1], "#5a5e64")
    backdrop(b, "city", -4.0, rng, colours=["#8a8e94", "#a0a4aa", "#7a7e88", "#9a9088"],
             depth=70.0)


# ================================================================ the meta
def _on(b: ArenaArea, level: float, x: float, z: float) -> float:
    return b.surface(x, z, level + 1.0)


def _meta(b: ArenaArea) -> None:
    for x, z in ((-60.0, 44.0), (-30.0, 44.0), (0.0, 44.0), (30.0, 44.0), (60.0, 44.0),
                 (-50.0, 52.0), (-45.0, 64.0), (40.0, 66.0), (-10.0, 74.0), (10.0, 76.0),
                 (-90.0, 44.0), (90.0, 44.0), (-130.0, 80.0), (130.0, 80.0), (0.0, 104.0),
                 (-30.0, 105.0)):
        b.team_spawn("props", x, None, z, yaw=3.14159)
    for x in (52.0, 55.5, 59.0, 62.5):
        for z in (18.5, 22.0, 25.5):
            b.team_spawn("hunters", x, F1, z, yaw=-1.5708)
    b.mark("pen", 58.0, F1, 20.0, r=12.0)
    hides = [
        (F1, -102.0, -30.0), (F1, -90.0, -15.0), (F1, -78.0, -40.0), (F1, -66.0, -10.0),
        (F1, -54.0, -36.0), (F1, -42.0, -15.0), (F1, -30.0, -40.0), (F1, -18.0, -20.0),
        (F1, -78.0, -20.0), (F1, -66.0, -38.0), (F1, 15.0, -27.0), (F1, 30.0, -10.0),
        (F1, 44.0, -30.0), (F1, 58.0, -20.0), (F1, 10.0, -60.0), (F1, 40.0, -64.0),
        (F1, -85.0, 4.0), (F1, -64.0, 4.0), (F1, -20.0, 10.0), (F1, 30.0, 16.0),
        (F1, -96.0, -70.0), (F1, -70.0, -66.0), (F1, -46.0, -70.0), (F1, -28.0, -70.0),
        (0.12, 100.0, -30.0), (0.12, 130.0, -30.0), (0.12, 160.0, -50.0), (0.12, 100.0, 10.0),
        (0.12, 144.0, 10.0), (0.12, 176.0, -20.0),
        (0.1, -130.0, 60.0), (0.1, 130.0, 90.0), (0.1, -86.0, 105.0), (0.1, 80.0, 135.0),
        (0.1, -160.0, 70.0), (0.1, 160.0, 120.0), (0.1, 0.0, 120.0),
        (0.1, -40.0, -100.0), (0.1, 40.0, -110.0), (0.1, -130.0, -100.0), (0.1, 130.0, -100.0),
        (0.1, -140.0, 0.0), (0.1, -150.0, -50.0),
    ]
    for level, x, z in hides:
        b.mark("hide", x, _on(b, level, x, z), z)
    searches = [
        (F1, -90.0, -2.0, "aisle 1"), (F1, -66.0, -36.0, "aisle 3"), (F1, -42.0, -21.0, "aisle 5"),
        (F1, -18.0, -50.0, "the back aisle"), (F1, 22.0, -27.0, "the produce hall"),
        (F1, 56.0, -40.0, "the bakery"), (F1, 30.0, -66.0, "the freezers"),
        (F1, -75.0, 8.0, "the checkouts"), (F1, -6.0, 14.0, "customer service"),
        (F1, -60.0, -66.0, "the warehouse"),
        (0.12, 100.0, -12.0, "the garden centre"), (0.12, 150.0, -30.0, "the gnome stand"),
        (0.12, 162.0, 14.0, "the display shed"),
        (0.1, -60.0, 104.0, "the car park"), (0.1, 60.0, 76.0, "the car park"),
        (0.1, -150.0, 56.0, "the recycling"), (0.1, -50.0, 84.0, "the trolley shelter"),
        (0.1, -60.0, -120.0, "the loading dock"), (0.1, -140.0, -40.0, "the side road"),
        (0.1, 150.0, 132.0, "the bus stop"),
    ]
    for level, x, z, name in searches:
        b.mark("search", x, _on(b, level, x, z), z, name=name)
        b.landmark(x, z, name)
    b.landmark(58.0, 20.0, "the security office")
    b.camera(-20.0, 70.0, 165.0, -20.0, 8.0, 0.0)
    b.camera(-104.0, 17.0, 26.0, -40.0, 3.0, -30.0)
    b.camera(180.0, 50.0, -80.0, 120.0, 4.0, -10.0)
    # one big room with long sight lines: a shorter clock keeps it even
    b.extra.update({"accent": "#2ab0a0", "twist": "sale", "pen_key": "pen", "round_seconds": 160.0})


def build(b: ArenaArea) -> None:
    rng = random.Random(9031)
    ground(b, GROUND, soil="#4a4a48", material="")
    s = Surfaces(b)
    s.reserve(rect(X0 - 0.5, X1 + 0.5, Z0 - 0.5, Z1 + 0.5))
    s.reserve(rect(-96.0, -68.0, -88.0, Z0))
    _edges(b, rng)
    _shell(b)
    _roof(b)
    _partitions(b)
    _paint(b)
    _lights(b)
    _aisles(b)
    _fresh(b)
    _front(b)
    _warehouse(b)
    _car_park(b, s)
    _garden_centre(b, s)
    _yards(b, s)
    _meta(b)
    cat.finish(b, "cereal_box")
