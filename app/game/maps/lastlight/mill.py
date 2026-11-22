"""Kettle Falls Mill -- a mill town in a river gorge, the autumn it ended.

Layout (north is +z)::

   z +280 ---------------- the woods over the top terrace -------------------
          (terraces climbing north)  ROW HOUSES               THE CHURCH
   z +160 ===================================================================
          THE COUNTING HOUSE    THE MILL YARD      boiler   THE DYE WORKS
          (safe room)           (the whistle)      house
          the millpond's shore  THE MILL (two floors, the roof, the belfry)
   z  +40 ~~~ THE MILLPOND ~~ THE DAM ~~~~~~~~ THE GORGE, the river 18 down ~~~
                                (the falls,   the waterwheel   covered  foot-
                                 the pool)    under the mill   bridge   bridge
   z  -40 ===================================================================
          the railway ======= THE DEPOT ======== the coal yard ==============
          the south hill and KETTLE HOUSE on top          knolls, the woods
   z -280 -------------------------------------------------------------------

Everybody deploys in the counting house, among the pay desks and the safe.

What makes it this place:

* **The gorge.**  Below the dam the river runs eighteen units down between
  rock walls; the falls come over the dam's notch into a plunge pool, the
  waterwheel turns under the mill, and the only ways across are the dam's
  crest, the covered bridge and the swaying footbridge.  Long stairs go down
  the cliffs.
* **The mill.**  Two floors -- the weave room's looms, the spinning room's
  frames -- a stair up to the roof and the belfry.
* **The lure.**  In the boiler house: blow the mill whistle, and the dead
  come back for the shift -- into the mill yard, as they always did.
* **High ground.**  The mill roof, the terraces of row houses, the hill
  under Kettle House, the coal heaps.
"""
from __future__ import annotations

import math
import random
from typing import Dict, List, Sequence, Tuple

from .kit import (
    BRICK, BRICK_DARK, CONCRETE, FLOOR, STEEL_DARK, WARM, WOOD, WOOD_DARK, WOOD_LIGHT, Area,
    Surfaces, barrel_spot, boundary, building, carve, crate, deploy_pad, flight, gable, holed_wall,
    lamp_post, plate, rect, room_walls, sign_decal, slab, strip_light, supply_ammo, supply_med,
    threshold, wall_sign)
from ..relay.kit import mound, pine, tier_stack, tree

Rect = Tuple[float, float, float, float]

HALF = 280.0
SKY = {"top": "#2e2e4e", "horizon": "#d8885a", "sun": [-0.6, 0.12, 0.55],
       "clouds": 0.55, "tint": "#ffc8a0"}
AMBIENT = "#7a6a6a"

GRASS = "#5a6a34"
SOIL = "#5a4630"
ROCK = "#6a6660"
COBBLE = "#6a6660"
STONE = "#8a8478"
WATER = "#2a4a5a"
MAPLE = "#c8582a"
GOLD = "#d8a02a"

POND = (-280.0, -60.0, -40.0, 40.0)
POND_BED = -6.0
POND_WATER = -2.0
DAM = (-60.0, -48.0, -40.0, 40.0)
DAM_TOP = 2.0
NOTCH = (-12.0, 12.0)
NOTCH_TOP = -2.4
GORGE = (-48.0, 280.0, -30.0, 30.0)
GORGE_BED = -18.0
RIVER = -15.6
POOL = (-48.0, -24.0, -20.0, 20.0)
POOL_BED = -21.0
DEEP = -24.0

MILL = (-30.0, 90.0, 40.0, 96.0)
UPPER = 14.4                       # the spinning room's floor (top)
MILL_TOP = 28.0
ROOF = MILL_TOP + 1.2
COUNTING = (-130.0, -80.0, 52.0, 92.0)
YARD = (-30.0, 90.0, 96.0, 150.0)
BOILER = (96.0, 126.0, 100.0, 132.0)
STACK = (134.0, 116.0)
COVERED = (150.0, 166.0)           # the covered bridge's x span
FOOT = (220.0, 226.0)              # the footbridge's x span
BOARDING = (176.0, 226.0, 44.0, 90.0)
STORE = (236.0, 276.0, 44.0, 80.0)
DYE = (176.0, 236.0, 104.0, 150.0)
DEPOT = (-40.0, 20.0, -100.0, -72.0)
TRACK_Z = (-64.0, -52.0)
MANSION = (-150.0, -100.0, -236.0, -206.0)
HILL_TOP = 10.0
WHEEL = (-10.0, 27.0)              # the waterwheel's x and z
WHEEL_Y = -9.6
WHEEL_R = 6.4


def build(b: Area) -> None:
    rng = random.Random(0x3111)
    b.extra.update({"weather": "leaves", "accent": "#e8883a"})
    s = Surfaces(b)
    _ground(b, s)
    boundary(b, 30.0, "#2a2a22", "#22221c", rng, horizon="forest")
    _river(b)
    _dam(b)
    _wheel(b)
    _mill(b, s)
    _counting_house(b, s)
    _yard(b, s)
    _bridges(b, s)
    _east_bank(b, s)
    _terraces(b, s, rng)
    _railway(b, s)
    _south_hill(b, s, rng)
    _country(b, s, rng)
    _paths(b, s)
    _rigs(b)
    _zombie_spawns(b)
    for x, z, name in ((-105, 72, "the counting house"), (0, 60, "the weave room"),
                       (30, 68, "the mill roof"), (30, 124, "the mill yard"),
                       (111, 116, "the boiler house"), (-54, 30, "the dam"),
                       (-36, 0, "the falls"), (100, 0, "the gorge"),
                       (158, 0, "the covered bridge"), (223, 0, "the footbridge"),
                       (201, 67, "the boarding house"), (256, 62, "the company store"),
                       (206, 127, "the dye works"), (20, 186, "the row houses"),
                       (145, 262, "the church"), (-10, -86, "the depot"),
                       (76, -105, "the coal yard"), (-125, -221, "Kettle House"),
                       (-170, 0, "the millpond")):
        b.landmark(float(x), float(z), name)
    b.camera(60.0, 30.0, -90.0, 0.0, -8.0, 30.0)
    b.camera(-20.0, 8.0, 10.0, -60.0, -8.0, 0.0)
    b.camera(140.0, 24.0, 160.0, 30.0, 10.0, 70.0)
    b.camera(-60.0, 26.0, -150.0, -125.0, 14.0, -221.0)


# ================================================================ ground
def _ground(b: Area, s: Surfaces) -> None:
    h = b.half + b.margin
    holes = [POND, DAM, GORGE]
    for r in holes:
        s.reserve(r)
    pieces = carve(rect(-h, h, -h, h), holes)
    plate(b, pieces, 0.0, 0.6, GRASS, studs=True, material="grass")
    plate(b, pieces, -0.6, 5.4, SOIL)


def _river(b: Area) -> None:
    """The millpond above the dam; below it the gorge -- rock walls under
    the soil, the bed, the plunge pool, the river -- and the stairs down."""
    slab(b, POND, POND_BED, POND_BED - DEEP, "#4a4a40", studs=True)
    b.water((POND[0] + POND[1]) / 2.0, 0.0, POND[1] - POND[0], POND[3] - POND[2], POND_WATER, WATER)
    gx0, gx1, gz0, gz1 = GORGE
    for z0, z1 in ((gz1, gz1 + 10.0), (gz0 - 10.0, gz0)):
        slab(b, rect(gx0, gx1, z0, z1), -6.0, -6.0 - DEEP, ROCK, studs=True)
    plate(b, carve(GORGE, [POOL]), GORGE_BED, GORGE_BED - DEEP, "#4a4a40", studs=True)
    slab(b, POOL, POOL_BED, POOL_BED - DEEP, "#3a3a34", studs=True)
    b.water((gx0 + gx1) / 2.0, 0.0, gx1 - gx0, gz1 - gz0, RIVER, WATER)
    # the stairs down the cliffs: two on the north wall, two on the south
    flight(b, "x", 96.0, 60.0, 24.0, 30.0, GORGE_BED, 0.0, ROCK, fill=GORGE_BED)
    flight(b, "x", 36.0, 0.0, -30.0, -24.0, GORGE_BED, 0.0, ROCK, fill=GORGE_BED)
    flight(b, "x", 180.0, 216.0, -30.0, -24.0, GORGE_BED, 0.0, ROCK, fill=GORGE_BED)
    flight(b, "x", 268.0, 232.0, 24.0, 30.0, GORGE_BED, 0.0, ROCK, fill=GORGE_BED)
    # out of the plunge pool
    flight(b, "x", -30.0, -24.0, -6.0, 6.0, POOL_BED, GORGE_BED, ROCK, fill=POOL_BED)
    # boulders in the river
    for (x, z, sc) in ((40.0, -12.0, 1.6), (90.0, 14.0, 1.3), (190.0, -6.0, 1.8), (250.0, 10.0, 1.4)):
        b.sphere([x, GORGE_BED + 1.6 * sc, z], [5.0 * sc, 3.4 * sc, 4.4 * sc], "#7a7670")


def _dam(b: Area) -> None:
    """The dam: stone, its crest a walk between the banks, the notch where
    the falls go over bridged by planks."""
    x0, x1, z0, z1 = DAM
    for (a, c) in ((z0, NOTCH[0]), (NOTCH[1], z1)):
        b.box([(x0 + x1) / 2.0, (DEEP + DAM_TOP) / 2.0, (a + c) / 2.0], [x1 - x0, DAM_TOP - DEEP, c - a], STONE,
              studs=True)
    b.box([(x0 + x1) / 2.0, (DEEP + NOTCH_TOP) / 2.0, 0.0], [x1 - x0, NOTCH_TOP - DEEP, NOTCH[1] - NOTCH[0]],
          "#7a7468")
    slab(b, rect(x0 + 2.0, x1 - 2.0, NOTCH[0], NOTCH[1]), DAM_TOP, 0.4, WOOD, studs=True)
    for x in (x0 + 2.3, x1 - 2.3):
        b.box([x, DAM_TOP + 0.6, 0.0], [0.6, 1.2, NOTCH[1] - NOTCH[0]], WOOD_DARK)
    barrel_spot(b, -54.0, DAM_TOP, -30.0)
    barrel_spot(b, 130.0, GORGE_BED, -22.0)
    wall_sign(b, x1 + 0.35, DAM_TOP - 2.0, 24.0, 12.0, 1.8,
              sign_decal("KETTLE FALLS  1846", STONE, "#2a2a2a", 6.7), "x+", STONE)


def _wheel(b: Area) -> None:
    """The overshot wheel under the mill, in the gorge against the north
    cliff: the axle in the rock, the flume along the cliff from the dam to
    its top (the wheel itself turns: a rig)."""
    wx, wz = WHEEL
    b.cyl([wx, WHEEL_Y, wz], [2.0, 6.0, 2.0], STEEL_DARK, r=[math.pi / 2.0, 0, 0], collide=False)
    b.box([wx, WHEEL_Y, 28.5], [3.0, 3.0, 3.0], STEEL_DARK)
    fx0, fx1 = -48.0, wx - WHEEL_R + 0.4
    slab(b, rect(fx0, fx1, 25.0, 29.0), -3.0, 0.4, WOOD)
    for z in (24.75, 29.25):
        b.box([(fx0 + fx1) / 2.0, -2.7, z], [fx1 - fx0, 1.4, 0.5], WOOD_DARK)
    for x in (-40.0, -30.0, -20.0):
        b.box([x, -4.0, 27.25], [0.8, 1.2, 5.5], WOOD_DARK)


# ================================================================== mill
def _storeys(b: Area, area: Rect, levels: Sequence[Tuple[float, float]], colour: str,
             holes: Dict[str, List[List[Tuple[float, float, float, float]]]], t: float = 2.0) -> None:
    """Walls a storey at a time, so windows on one floor can sit right over
    the ones below: the two walls facing along x run the full depth."""
    x0, x1, z0, z1 = area
    for k, (ya, yb) in enumerate(levels):
        def h(side: str) -> List[Tuple[float, float, float, float]]:
            per = holes.get(side, [])
            return per[k] if k < len(per) else []
        holed_wall(b, "z", x0 + t / 2.0, t, z0, z1, ya, yb, colour, h("x-"), glass=True)
        holed_wall(b, "z", x1 - t / 2.0, t, z0, z1, ya, yb, colour, h("x+"), glass=True)
        holed_wall(b, "x", z0 + t / 2.0, t, x0 + t, x1 - t, ya, yb, colour, h("z-"), glass=True)
        holed_wall(b, "x", z1 - t / 2.0, t, x0 + t, x1 - t, ya, yb, colour, h("z+"), glass=True)


def _mill(b: Area, s: Surfaces) -> None:
    """The mill: brick, two floors -- the weave room's looms, the spinning
    room's frames -- a stair up to the roof, the belfry on the ridge."""
    x0, x1, z0, z1 = MILL
    s.reserve(rect(x0, x1, z0, z1))
    low = [(a, a + 6.0, 4.0, 10.0) for a in (-22.0, -10.0, 2.0, 14.0, 26.0, 38.0, 66.0, 78.0)]
    low_n = [(a, a + 6.0, 4.0, 10.0) for a in (-22.0, -10.0, 2.0, 44.0, 56.0, 68.0, 80.0)]
    high = [(a, a + 6.0, 18.0, 24.0) for a in (-22.0, -10.0, 2.0, 14.0, 26.0, 38.0, 50.0, 62.0, 74.0)]
    side_high = [(a, a + 6.0, 18.0, 24.0) for a in (50.0, 62.0, 74.0)]
    holes = {
        "z-": [low + [(50.0, 60.0, -1.0, 10.0)], high],
        "z+": [low_n + [(20.0, 36.0, -1.0, 10.0)], high],
        "x-": [[(46.0, 52.0, 4.0, 10.0), (60.0, 70.0, -1.0, 10.0), (76.0, 82.0, 4.0, 10.0)], side_high],
        "x+": [[(46.0, 52.0, 4.0, 10.0), (60.0, 70.0, -1.0, 10.0), (76.0, 82.0, 4.0, 10.0)], side_high],
    }
    _storeys(b, MILL, [(0.0, UPPER - 0.4), (UPPER - 0.4, MILL_TOP)], BRICK, holes)
    t = 2.0
    inner = rect(x0 + t, x1 - t, z0 + t, z1 - t)
    slab(b, inner, FLOOR, FLOOR, "#8a7a62")
    for side, span in (("z-", (50.0, 60.0)), ("z+", (20.0, 36.0)), ("x-", (60.0, 70.0)), ("x+", (60.0, 70.0))):
        threshold(b, MILL, side, span)
    stair_hole = rect(x0 + t, -6.0, z0 + t, 48.0)
    plate(b, carve(inner, [stair_hole]), UPPER, 0.6, WOOD, studs=True)
    flight(b, "x", -26.0, -6.0, z0 + t, 48.0, FLOOR, UPPER, WOOD_DARK, fill=FLOOR)
    b.box([-17.0, UPPER + 0.6, 48.3], [22.0, 1.2, 0.6], WOOD_DARK)
    roof_hole = rect(64.0, 84.0, 88.0, z1 - t)
    plate(b, carve(rect(x0, x1, z0, z1), [roof_hole]), ROOF, 1.2, "#4a4a48", studs=True)
    flight(b, "x", 64.0, 84.0, 88.0, z1 - t, UPPER, ROOF, WOOD_DARK, fill=UPPER)
    room_walls(b, rect(x0, x1, z0, z1), 1.2, ROOF, ROOF + 2.4, BRICK_DARK)
    for z in (52.0, 66.0, 80.0):
        strip_light(b, 30.0, z, UPPER - 0.6, 100.0, "x", WARM)
        strip_light(b, 30.0, z, MILL_TOP, 100.0, "x", WARM)
    # the weave room: looms in rows
    for zr in (56.0, 70.0, 84.0):
        for x in (-16.0, 0.0, 16.0, 32.0, 48.0, 64.0):
            b.box([x, FLOOR + 1.6, zr], [6.0, 3.2, 4.0], "#6a5a4a")
            b.box([x, FLOOR + 4.2, zr - 1.6], [6.0, 2.0, 0.6], WOOD_DARK)
            b.box([x - 2.6, FLOOR + 3.7, zr + 1.2], [0.6, 1.0, 0.6], STEEL_DARK)
    supply_med(b, 84.0, FLOOR, 46.0, "x-")
    supply_ammo(b, -20.0, FLOOR, 90.0, "z-")
    # the spinning room: frames in rows
    for zr in (62.0, 78.0):
        for (a, c) in ((-20.0, 8.0), (16.0, 44.0)):
            b.box([(a + c) / 2.0, UPPER + 1.6, zr], [c - a, 3.2, 3.0], "#7a6a52")
            b.box([(a + c) / 2.0, UPPER + 3.6, zr], [c - a - 2.0, 0.8, 1.6], "#c8b8a0")
    for (x, z) in ((60.0, 56.0), (70.0, 56.0), (65.0, 66.0)):
        b.box([x, UPPER + 1.8, z], [5.0, 3.6, 5.0], "#e8e0cc", studs=True)
    supply_ammo(b, 36.0, UPPER, 46.0, "z+")
    barrel_spot(b, 54.0, UPPER, 88.0)
    # the belfry on the roof
    for x in (23.0, 37.0):
        for z in (61.0, 75.0):
            b.box([x, ROOF + 5.0, z], [1.2, 10.0, 1.2], "#e8e0cc")
    slab(b, rect(21.0, 39.0, 59.0, 77.0), ROOF + 10.8, 0.8, "#4a4a48")
    slab(b, rect(24.0, 36.0, 62.0, 74.0), ROOF + 12.0, 1.2, "#4a4a48")
    slab(b, rect(27.0, 33.0, 65.0, 71.0), ROOF + 13.2, 1.2, "#4a4a48")
    b.box([30.0, ROOF + 14.6, 68.0], [0.3, 2.8, 0.3], STEEL_DARK)
    wall_sign(b, 30.0, MILL_TOP - 2.5, z1 + 0.35, 50.0, 3.0,
              sign_decal("KETTLE FALLS MANUFACTURING CO", "#e8e0cc", BRICK_DARK, 16.7), "z+", "#e8e0cc")
    supply_ammo(b, 0.0, ROOF, 60.0, "x+")


def _counting_house(b: Area, s: Surfaces) -> None:
    """The counting house, where they were paid: stone, the paymaster's
    cage across one end, the safe, the desks -- the safe room."""
    x0, x1, z0, z1 = COUNTING
    s.reserve(rect(x0 - 2.0, x1 + 2.0, z0 - 2.0, z1 + 2.0))
    head = 10.0
    building(b, COUNTING, 0.0, 13.0, STONE, roof_colour="#3a3a3a", floor_colour="#8a7a62",
             doors={"x+": [(68.0, 78.0, head)], "z-": [(-110.0, -100.0, head)], "z+": [(-112.0, -102.0, head)]},
             windows={"z-": [(-126.0, -118.0, 4.0, 9.0), (-92.0, -84.0, 4.0, 9.0)],
                      "x-": [(58.0, 66.0, 4.0, 9.0), (78.0, 86.0, 4.0, 9.0)],
                      "z+": [(-126.0, -118.0, 4.0, 9.0), (-94.0, -86.0, 4.0, 9.0)]},
             glass=True, lights=WARM)
    for side, span in (("x+", (68.0, 78.0)), ("z-", (-110.0, -100.0)), ("z+", (-112.0, -102.0))):
        threshold(b, COUNTING, side, span)
    gable(b, COUNTING, 13.0 + 1.2, "#3a3a3a", "x", tiers=3, rise=1.5)
    wall_sign(b, x1 + 0.35, 11.0, 72.0, 22.0, 2.2, sign_decal("COUNTING HOUSE", STONE, "#2a2a2a", 10.0),
              "x+", STONE)
    floor = FLOOR
    for z in (78.0, 64.0):
        for k in range(8):
            x = -124.5 + k * 4.9
            deploy_pad(b, x, z, floor, "#e8883a", 4.4)
            b.safe_spawn(x, floor + 0.6, z, -math.pi / 2.0)
    # the paymaster's window across the north-east corner, the safe behind it
    b.box([-90.0, floor + 1.6, 84.0], [16.0, 3.2, 1.0], WOOD_DARK)
    b.box([-90.0, floor + 5.0, 84.0], [16.0, 3.6, 0.3], "#c8a83a", material="metal", alpha=0.5)
    b.box([-86.0, floor + 2.4, 88.0], [3.6, 4.8, 3.6], "#2a2a2a", material="metal")
    supply_ammo(b, -120.0, floor, 57.0, "z+")
    supply_med(b, -96.0, floor, 55.4, "z+")
    barrel_spot(b, -74.0, 0.0, 100.0)


def _yard(b: Area, s: Surfaces) -> None:
    """The mill yard: cobbles, cotton bales stacked, a wagon; the boiler
    house with its stack, and the whistle in it -- the lure."""
    s.lay(YARD, 0.3, COBBLE, studs=True)
    for (x, z, n) in ((-14.0, 110.0, 3), (10.0, 140.0, 2), (64.0, 112.0, 3), (78.0, 140.0, 2)):
        for k in range(n):
            b.box([x + k * 5.2, 0.3 + 1.6, z], [5.0, 3.2, 4.0], "#e8e0cc", studs=True)
        b.box([x + 2.6, 0.3 + 4.8, z], [5.0, 2.6, 4.0], "#d8d0bc", studs=True)
    wx, wz = 40.0, 132.0
    b.box([wx, 0.3 + 2.2, wz], [12.0, 1.0, 6.0], WOOD)
    for dx in (-4.0, 4.0):
        for dz in (-3.4, 3.4):
            b.cyl([wx + dx, 0.3 + 1.6, wz + dz], [3.2, 0.5, 3.2], WOOD_DARK, r=[math.pi / 2.0, 0, 0], collide=False)
    b.box([wx, 0.3 + 0.85, wz], [10.0, 1.7, 3.0], WOOD_DARK)
    b.box([wx - 2.0, 0.3 + 4.2, wz], [6.0, 3.0, 5.0], "#e8e0cc", studs=True)
    # the boiler house and the stack
    x0, x1, z0, z1 = BOILER
    s.reserve(rect(x0 - 1.0, x1 + 1.0, z0 - 1.0, z1 + 1.0))
    building(b, BOILER, 0.0, 14.0, BRICK, roof_colour="#3a3a3a", floor_colour="#5a5650",
             doors={"x-": [(108.0, 118.0, 10.0)]}, windows={"z-": [(102.0, 110.0, 5.0, 10.0)]},
             glass=True, lights=WARM)
    threshold(b, BOILER, "x-", (108.0, 118.0))
    b.box([111.0, FLOOR + 3.0, 126.0], [20.0, 6.0, 8.0], "#3a3f46", material="metal")
    b.box([118.0, FLOOR + 1.5, 112.0], [4.0, 3.0, 4.0], STEEL_DARK, material="metal")
    b.set_lure(111.0, FLOOR, 112.0, "the mill whistle", "Blow the mill whistle", "ll_whistle",
               (30.0, 0.3, 124.0))
    sx, sz = STACK
    s.reserve(rect(sx - 4.0, sx + 4.0, sz - 4.0, sz + 4.0))
    b.box([sx, 25.0, sz], [6.0, 50.0, 6.0], BRICK_DARK)
    b.box([sx, 50.6, sz], [7.0, 1.2, 7.0], "#3a3a3a")
    b.box([118.0, 14.0 + 1.2 + 1.6, 106.0], [1.0, 3.2, 1.0], "#c8a83a", material="metal")
    supply_ammo(b, 102.0, FLOOR, 106.0, "x+")
    barrel_spot(b, 88.0, 0.3, 146.0)


def _bridges(b: Area, s: Surfaces) -> None:
    """Across the gorge: the covered bridge on its piers, the footbridge on
    its cables (they sway: a rig)."""
    gz0, gz1 = GORGE[2], GORGE[3]
    cx0, cx1 = COVERED
    slab(b, rect(cx0, cx1, gz0, gz1), 0.4, 1.2, WOOD, studs=True)
    for (z0, z1) in ((-14.0, -8.0), (8.0, 14.0)):
        b.box([(cx0 + cx1) / 2.0, (GORGE_BED - 0.8) / 2.0, (z0 + z1) / 2.0],
              [cx1 - cx0 + 2.0, -0.8 - GORGE_BED, z1 - z0], STONE, studs=True)
    windows = [(z, z + 6.0, 4.0, 8.0) for z in (-24.0, -12.0, 0.0, 12.0)]
    for x in (cx0 + 0.6, cx1 - 0.6):
        holed_wall(b, "z", x, 1.2, gz0, gz1, 0.4, 10.0, "#8a2a24", windows)
    slab(b, rect(cx0 - 1.0, cx1 + 1.0, gz0 - 1.0, gz1 + 1.0), 11.0, 1.0, "#4a4a48")
    gable(b, rect(cx0, cx1, gz0, gz1), 11.0, "#4a4a48", "z", tiers=3, rise=1.4, overhang=1.0)
    for z in (-15.0, 15.0):
        strip_light(b, (cx0 + cx1) / 2.0, z, 10.0, 6.0, "x", WARM)
    for z in (gz0 - 0.35, gz1 + 0.35):
        wall_sign(b, (cx0 + cx1) / 2.0, 9.2, z, 12.0, 1.6,
                  sign_decal("WALK YOUR HORSE", "#e8e0cc", "#2a2a2a", 7.5), "z-" if z < 0 else "z+", "#e8e0cc")
    # the footbridge
    fx0, fx1 = FOOT
    slab(b, rect(fx0, fx1, gz0, gz1), 0.4, 0.6, WOOD_LIGHT, studs=True)
    for x in (fx0 + 0.3, fx1 - 0.3):
        b.box([x, 1.0, 0.0], [0.6, 1.2, gz1 - gz0], WOOD_DARK)
    for z in (gz0 - 0.6, gz1 + 0.6):
        for x in (fx0 - 0.6, fx1 + 0.6):
            b.box([x, 7.0, z], [1.2, 14.0, 1.2], WOOD_DARK)
        b.box([(fx0 + fx1) / 2.0, 14.4, z], [fx1 - fx0 + 2.4, 0.8, 1.2], WOOD_DARK)


def _east_bank(b: Area, s: Surfaces) -> None:
    """East of the mill: the boarding house, the company store, the dye
    works with its vats and the cloth on the racks."""
    s.reserve(rect(BOARDING[0] - 2.0, BOARDING[1] + 2.0, BOARDING[2] - 2.0, BOARDING[3] + 2.0))
    building(b, BOARDING, 0.0, 14.0, "#c8b8a0", roof_colour="#5a3a2a", floor_colour="#8a7a62",
             doors={"x-": [(60.0, 70.0, 10.0)], "z+": [(196.0, 206.0, 10.0)]},
             windows={"z-": [(182.0, 188.0, 4.0, 9.0), (196.0, 202.0, 4.0, 9.0), (212.0, 218.0, 4.0, 9.0)],
                      "x+": [(52.0, 58.0, 4.0, 9.0), (74.0, 80.0, 4.0, 9.0)]},
             glass=True, lights=WARM)
    threshold(b, BOARDING, "x-", (60.0, 70.0))
    threshold(b, BOARDING, "z+", (196.0, 206.0))
    gable(b, BOARDING, 14.0 + 1.2, "#5a3a2a", "x", tiers=3, rise=1.5)
    wall_sign(b, BOARDING[0] - 0.35, 11.6, 65.0, 20.0, 2.0, sign_decal("BOARDING HOUSE", "#c8b8a0", "#3a2a1a", 10.0),
              "x-", "#c8b8a0")
    for (x, z) in ((186.0, 54.0), (186.0, 80.0), (216.0, 54.0)):
        b.box([x, FLOOR + 1.2, z], [8.0, 0.8, 4.4], "#c8c0b0")
        b.box([x, FLOOR + 0.2, z], [8.4, 0.4, 4.8], WOOD_DARK)
    supply_med(b, 220.0, FLOOR, 86.6, "z-")
    s.reserve(rect(STORE[0] - 2.0, STORE[1] + 2.0, STORE[2] - 2.0, STORE[3] + 2.0))
    building(b, STORE, 0.0, 12.0, "#8a5a3a", roof_colour="#3a3a3a", floor_colour="#8a7a62",
             doors={"x-": [(56.0, 66.0, 9.0)]}, windows={"z+": [(242.0, 254.0, 3.0, 8.0), (260.0, 270.0, 3.0, 8.0)]},
             glass=True, lights=WARM)
    threshold(b, STORE, "x-", (56.0, 66.0))
    wall_sign(b, STORE[0] - 0.35, 10.6, 62.0, 18.0, 2.0, sign_decal("COMPANY STORE", "#8a5a3a", "#f2e6c8", 9.0),
              "x-", "#8a5a3a")
    for z in (50.0, 74.0):
        b.box([260.0, FLOOR + 1.6, z], [24.0, 3.2, 2.0], WOOD, studs=True)
    supply_ammo(b, 268.0, FLOOR, 62.0, "x-")
    # the dye works: a shed roof on posts, the vats, the racks
    x0, x1, z0, z1 = DYE
    s.reserve(rect(x0 - 2.0, x1 + 2.0, z0 - 2.0, z1 + 2.0))
    for x in (x0, (x0 + x1) / 2.0, x1):
        for z in (z0, z1):
            b.box([x, 6.0, z], [1.2, 12.0, 1.2], WOOD_DARK)
    slab(b, rect(x0 - 1.0, x1 + 1.0, z0 - 1.0, z1 + 1.0), 12.6, 0.6, "#4a4a48")
    for k, (x, colour) in enumerate(((186.0, "#2a3a8a"), (198.0, "#a8182a"), (210.0, "#3a7a2a"),
                                     (222.0, "#d8a02a"))):
        for (a, c, d, e) in ((x - 4.0, x + 4.0, 112.0, 112.6), (x - 4.0, x + 4.0, 119.4, 120.0),
                             (x - 4.0, x - 3.4, 112.6, 119.4), (x + 3.4, x + 4.0, 112.6, 119.4)):
            b.box([(a + c) / 2.0, 1.6, (d + e) / 2.0], [c - a, 3.2, e - d], "#6a5a4a")
        slab(b, rect(x - 3.4, x + 3.4, 112.6, 119.4), 1.0, 1.0, "#3a3a34")
        b.water(x, 116.0, 6.8, 6.8, 2.6, colour)
    for z in (132.0, 142.0):
        b.box([(x0 + x1) / 2.0, 9.0, z], [x1 - x0 - 4.0, 0.4, 0.4], WOOD_DARK)
        for x in (x0 + 2.0, x1 - 2.0):
            b.box([x, 4.4, z], [0.8, 8.8, 0.8], WOOD_DARK)
    barrel_spot(b, 240.0, 0.0, 100.0)


def _terraces(b: Area, s: Surfaces, rng: random.Random) -> None:
    """North of the mill the ground climbs in terraces: a row of houses on
    each, stairs between, the church on the top one."""
    s.reserve(rect(-280.0, 280.0, 160.0, 280.0))
    tier_stack(b, [[rect(-280.0, 280.0, 160.0, 280.0)], [rect(-280.0, 280.0, 204.0, 280.0)],
                   [rect(-280.0, 280.0, 244.0, 280.0)]], 0.0, [4.0], ["#5a6a34", "#55663e", "#4f6038"])
    for (a, c) in ((-112.0, -100.0), (-46.0, -34.0), (152.0, 164.0), (250.0, 258.0)):
        flight(b, "z", 152.0, 160.0, a, c, 0.0, 4.0, STONE, fill=0.0)
    for x in (-150.0, 60.0, 200.0):
        flight(b, "z", 196.0, 204.0, x, x + 8.0, 4.0, 8.0, STONE, fill=4.0)
    for x in (-100.0, 100.0):
        flight(b, "z", 236.0, 244.0, x, x + 8.0, 8.0, 12.0, STONE, fill=8.0)
    # the rows of houses
    for (y, z0, z1, x0, x1) in ((4.0, 174.0, 194.0, -60.0, 100.0), (8.0, 216.0, 234.0, -240.0, -120.0),
                                (8.0, 216.0, 234.0, 0.0, 120.0)):
        doors = [(x, x + 8.0, y + 8.0) for x in range(int(x0) + 6, int(x1) - 10, 20)]
        wins = [(x + 11.0, x + 16.0, y + 3.6, y + 8.0) for x in range(int(x0) + 6, int(x1) - 20, 20)]
        r = rect(x0, x1, z0, z1)
        building(b, r, y, 12.0, ["#9a4f3a", "#8a5a3a", "#a86a4a"][int(y) % 3], roof_colour="#4a3a3a",
                 floor_colour="#8a7a62", doors={"z-": doors}, windows={"z-": wins, "z+": wins},
                 glass=True, lights=WARM)
        for (a, c, _) in doors:
            threshold(b, r, "z-", (a, c), y0=y)
        gable(b, r, y + 12.0 + 1.2, "#4a3a3a", "x", tiers=3, rise=1.4)
        for k, (a, c, _) in enumerate(doors):
            if k % 2 == 0:
                b.box([(a + c) / 2.0 + 10.0, y + 12.0 + 1.2 + 4.2 + 1.5, (z0 + z1) / 2.0], [2.0, 3.0, 2.0], BRICK_DARK)
    supply_ammo(b, 80.0, 4.0, 200.0, "z-")
    supply_med(b, -180.0, 8.0, 238.0, "z-")
    wall_sign(b, 20.0, 4.0 + 9.5, 173.65, 30.0, 2.6,
              sign_decal("WE WANT BREAD AND ROSES TOO", "#e8e0cc", "#a8182a", 11.5), "z-", "#e8e0cc")
    for x in (17.0, 43.0):
        b.box([x, 4.0 + 3.0, 200.0], [0.8, 6.0, 0.8], WOOD_DARK)
    b.box([30.0, 9.6, 200.0], [25.2, 0.4, 0.4], WOOD_DARK)
    # the church on the top terrace
    ch = rect(120.0, 170.0, 248.0, 276.0)
    building(b, ch, 12.0, 16.0, "#e8e2d4", roof_colour="#3a3a3a", floor_colour="#8a7a62",
             doors={"z-": [(140.0, 150.0, 12.0 + 10.0)]},
             windows={"x-": [(252.0, 258.0, 16.0, 24.0), (264.0, 270.0, 16.0, 24.0)],
                      "x+": [(252.0, 258.0, 16.0, 24.0), (264.0, 270.0, 16.0, 24.0)]},
             glass=True, lights=WARM)
    threshold(b, ch, "z-", (140.0, 150.0), y0=12.0)
    gable(b, ch, 12.0 + 16.0 + 1.2, "#3a3a3a", "z", tiers=4, rise=1.6)
    b.box([145.0, 12.0 + 16.0 + 1.2 + 6.4 + 5.0, 252.0], [6.0, 10.0, 6.0], "#e8e2d4")
    b.box([145.0, 12.0 + 16.0 + 1.2 + 6.4 + 10.0 + 3.0, 252.0], [0.6, 6.0, 0.6], "#e8e2d4")
    for k in range(4):
        b.box([138.0 + (k % 2) * 14.0, 12.0 + FLOOR + 1.0, 258.0 + (k // 2) * 8.0], [10.0, 2.0, 2.4], WOOD)
    barrel_spot(b, 180.0, 12.0, 262.0)


def _railway(b: Area, s: Surfaces) -> None:
    """The railway along the south bank: ballast, rails, the depot and its
    platform, a locomotive and two boxcars standing; the coal yard."""
    z0, z1 = TRACK_Z
    s.lay(rect(-280.0, 280.0, z0, z1), 0.3, "#7a7670", studs=True)
    for z in (-60.0, -56.0):
        b.box([0.0, 0.5, z], [560.0, 0.4, 0.4], "#5a5f66", material="metal")
    x0, x1, dz0, dz1 = DEPOT
    s.reserve(rect(x0 - 2.0, x1 + 2.0, dz0, z0))
    building(b, DEPOT, 0.0, 12.0, "#a86a3a", roof_colour="#4a3a2a", floor_colour="#8a7a62",
             doors={"z+": [(-16.0, -6.0, 9.0)], "z-": [(0.0, 8.0, 9.0)]},
             windows={"z+": [(-34.0, -24.0, 3.6, 8.0), (4.0, 14.0, 3.6, 8.0)],
                      "x-": [(-92.0, -84.0, 3.6, 8.0)]},
             glass=True, lights=WARM)
    threshold(b, DEPOT, "z+", (-16.0, -6.0))
    threshold(b, DEPOT, "z-", (0.0, 8.0))
    gable(b, DEPOT, 12.0 + 1.2, "#4a3a2a", "x", tiers=3, rise=1.4)
    slab(b, rect(x0 - 2.0, x1 + 2.0, dz1, z0), 1.2, 1.2, CONCRETE, studs=True)
    wall_sign(b, -10.0, 10.6, dz1 + 0.35, 20.0, 2.2, sign_decal("KETTLE FALLS", "#a86a3a", "#f2e6c8", 9.1),
              "z+", "#a86a3a")
    supply_med(b, -30.0, FLOOR, -96.6, "z+")
    supply_ammo(b, 12.0, FLOOR, -80.0, "z-")
    # the train: a locomotive and two boxcars, standing on the rails
    y = 0.7
    lx = 80.0
    b.box([lx, y + 1.4, -58.0], [24.0, 2.8, 7.0], "#2a2a2e", material="metal")
    b.cyl([lx + 2.0, y + 5.0, -58.0], [5.0, 16.0, 5.0], "#2a2a2e", r=[0, 0, math.pi / 2.0], collide=False)
    b.box([lx + 3.0, y + 5.0, -58.0], [14.0, 4.4, 4.4], "#2a2a2e", alpha=0.0)
    b.box([lx - 8.0, y + 6.0, -58.0], [7.0, 6.4, 7.0], "#3a2a24", material="metal")
    b.box([lx - 8.0, y + 9.6, -58.0], [8.0, 0.8, 8.0], "#2a2a2e")
    b.box([lx + 8.0, y + 9.6, -58.0], [1.6, 4.8, 1.6], "#2a2a2e")
    b.box([lx + 12.6, y + 1.0, -58.0], [1.2, 2.0, 6.0], "#8a2a24", material="metal")
    for k, bx in enumerate((112.0, 140.0)):
        b.box([bx, y + 5.8, -58.0], [24.0, 9.6, 7.6], ["#8a2a24", "#5a3a2a"][k], studs=True)
        b.box([bx, y + 0.5, -58.0], [20.0, 1.0, 5.0], "#2a2a2e")
        b.box([bx, y + 5.8, -61.85], [6.0, 7.0, 0.1], WOOD_DARK, collide=False)
    # the coal yard
    for (cx, cz, rx, rz, lv) in ((60.0, -100.0, 16.0, 10.0, 3), (96.0, -112.0, 12.0, 9.0, 2)):
        s.reserve(rect(cx - rx, cx + rx, cz - rz, cz + rz))
        mound(b, cx, cz, rx, rz, lv, 1.6, ["#1a1a1e", "#222226"])
    barrel_spot(b, 40.0, 0.0, -80.0)


def _south_hill(b: Area, s: Surfaces, rng: random.Random) -> None:
    """The hill south of the railway, and on its top Kettle House, the
    owner's: a porch over the valley, the widow's walk on the roof."""
    s.reserve(rect(-262.0, 22.0, -278.0, -162.0))
    top = mound(b, -120.0, -220.0, 140.0, 56.0, 5, 2.0, ["#4f6038", GRASS, "#55663e"], shrink=0.5)
    x0, x1, z0, z1 = MANSION
    building(b, MANSION, top, 14.0, "#e8e2d4", roof_colour="#3a3a4a", floor_colour="#8a6f52",
             doors={"z+": [(-130.0, -120.0, top + 10.0)]},
             windows={"z+": [(-146.0, -138.0, top + 4.0, top + 9.0), (-112.0, -104.0, top + 4.0, top + 9.0)],
                      "z-": [(-140.0, -132.0, top + 4.0, top + 9.0), (-118.0, -110.0, top + 4.0, top + 9.0)],
                      "x-": [(-226.0, -216.0, top + 4.0, top + 9.0)], "x+": [(-226.0, -216.0, top + 4.0, top + 9.0)]},
             glass=True, lights=WARM)
    threshold(b, MANSION, "z+", (-130.0, -120.0), y0=top)
    gable(b, MANSION, top + 14.0 + 1.2, "#3a3a4a", "x", tiers=3, rise=1.6)
    slab(b, rect(-140.0, -110.0, z1, z1 + 6.0), top + 1.0, 1.0, WOOD_LIGHT)
    for x in (-139.4, -110.6):
        b.box([x, top + 1.0 + 4.5, z1 + 5.4], [1.2, 9.0, 1.2], "#e8e2d4")
    slab(b, rect(-141.0, -109.0, z1, z1 + 6.6), top + 10.6, 0.6, "#3a3a4a")
    supply_ammo(b, -144.0, top + FLOOR, -230.0, "z+")
    barrel_spot(b, -90.0, top, -214.0)
    for (x, z) in ((-200.0, -250.0), (-40.0, -240.0), (-170.0, -190.0), (-70.0, -196.0)):
        tree(b, x, z, b.surface(x, z, 30.0), rng.uniform(1.1, 1.4), WOOD, MAPLE)


def _country(b: Area, s: Surfaces, rng: random.Random) -> None:
    """Knolls with maples in their colours, the woods along the edges,
    lamps."""
    s.reserve(rect(-230.0, -170.0, 90.0, 130.0))
    top = mound(b, -200.0, 110.0, 30.0, 20.0, 2, 1.6, ["#4f6038", GRASS])
    tree(b, -200.0, 110.0, top, 1.4, WOOD, MAPLE)
    # the orchard hill, apple trees in rows up its terraces, the cider house
    s.reserve(rect(100.0, 260.0, -268.0, -162.0))
    mound(b, 180.0, -215.0, 80.0, 53.0, 4, 1.8, ["#4f6038", GRASS, "#55663e", "#5a6a34"], shrink=0.4)
    for row in range(5):
        for col in range(7):
            ox = 126.0 + col * 18.0 + (row % 2) * 9.0
            oz = -250.0 + row * 17.0
            if ((ox - 180.0) / 76.0) ** 2 + ((oz + 215.0) / 50.0) ** 2 > 0.8:
                continue
            tree(b, ox, oz, b.surface(ox, oz, 30.0), 0.8, WOOD, ["#5a7a2a", "#6a8a2a"][(row + col) % 2])
    cider = rect(60.0, 96.0, -152.0, -128.0)
    s.reserve(rect(58.0, 98.0, -154.0, -126.0))
    building(b, cider, 0.0, 11.0, "#8a5a3a", roof_colour="#4a3a2a", floor_colour="#7a6a52",
             doors={"z+": [(70.0, 80.0, 8.5)]}, windows={"x+": [(-146.0, -140.0, 3.6, 7.6)]},
             glass=True, lights=WARM)
    threshold(b, cider, "z+", (70.0, 80.0))
    gable(b, cider, 11.0 + 1.2, "#4a3a2a", "x", tiers=3, rise=1.4)
    b.box([88.0, FLOOR + 2.0, -144.0], [6.0, 4.0, 6.0], WOOD_DARK)
    b.cyl([88.0, FLOOR + 5.0, -144.0], [1.0, 2.0, 1.0], STEEL_DARK)
    for k in range(3):
        b.box([66.0, FLOOR + 1.5, -146.0 + k * 4.4], [4.0, 3.0, 4.0], "#6a4a2a")
    wall_sign(b, 78.0, 9.6, -127.65, 16.0, 1.8, sign_decal("SWEET CIDER", "#8a5a3a", "#f2e6c8", 8.9), "z+", "#8a5a3a")
    supply_ammo(b, 78.0, FLOOR, -148.0, "z+")
    for (x, z) in ((-240.0, 60.0), (-160.0, 130.0), (-250.0, 140.0), (60.0, -150.0), (180.0, -110.0),
                   (-30.0, -140.0), (260.0, 120.0)):
        tree(b, x, z, 0.0, rng.uniform(1.1, 1.5), WOOD, [MAPLE, GOLD, "#a83a24", "#c87a2a"][int(abs(x)) % 4])
    for k in range(9):
        px = -270.0 + k * 30.0 + rng.uniform(-4.0, 4.0)
        pine(b, px, -272.0, b.surface(px, -272.0, 30.0), rng.uniform(1.2, 1.6))
    for (x, z) in ((-40.0, 34.0), (100.0, 39.5), (200.0, 39.5), (-40.0, -34.0), (100.0, -34.0),
                   (-60.0, -50.0), (60.0, -50.0), (-100.0, 150.0), (120.0, 150.0)):
        lamp_post(b, x, z, h=12.0, light=WARM)


def _paths(b: Area, s: Surfaces) -> None:
    for r in (rect(-80.0, -30.0, 64.0, 76.0), rect(-30.0, 280.0, 32.0, 38.0), rect(152.0, 164.0, 38.0, 152.0),
              rect(152.0, 164.0, -52.0, -32.0), rect(-280.0, -62.0, 42.0, 50.0), rect(-46.0, -34.0, 42.0, 152.0),
              rect(-112.0, -100.0, 94.0, 152.0), rect(220.0, 226.0, -52.0, -32.0), rect(220.0, 226.0, 32.0, 44.0),
              rect(-280.0, 280.0, -48.0, -42.0)):
        s.lay(r, 0.3, "#8a7a5a", studs=True)


# ================================================================ rigs
def _rigs(b: Area) -> None:
    wx, wz = WHEEL
    b.rig("waterwheel", wx, WHEEL_Y, wz, 0.0, r=WHEEL_R, spout_p=[wx - WHEEL_R + 0.4, -2.8, 27.0])
    b.rig("falls", DAM[1] + 0.2, NOTCH_TOP, 0.0, 0.0, w=NOTCH[1] - NOTCH[0], drop=NOTCH_TOP - RIVER)
    b.rig("river_flow", 120.0, RIVER, 0.0, 0.0, area=[-20.0, 276.0, -26.0, 26.0], n=36)
    b.rig("mill_bell", 30.0, ROOF + 8.6, 68.0, 0.0)
    b.rig("whistle_steam", 118.0, 14.0 + 1.2 + 3.2, 106.0, 0.0, stack_p=[STACK[0], 51.2, STACK[1]])
    b.rig("loom_ghost", 32.0, FLOOR + 3.2, 70.0, 0.0)
    b.rig("footbridge_cables", (FOOT[0] + FOOT[1]) / 2.0, 14.4, 0.0, 0.0, w=FOOT[1] - FOOT[0] + 1.2,
          z0=GORGE[2] - 0.6, z1=GORGE[3] + 0.6, deck=0.4)
    b.rig("cloth_racks", (DYE[0] + DYE[1]) / 2.0, 9.0, 137.0, 0.0, w=DYE[1] - DYE[0] - 8.0, rows=[132.0, 142.0])
    b.rig("clothesline", 30.0, 9.6, 200.0, 0.0, w=26.0)
    crate(b, -76.5, 0.0, 58.0, 3.0, WOOD)
    b.rig("mill_cat", -76.5, 3.0, 58.0, -math.pi / 2.0)
    b.rig("rowboat", -150.0, POND_WATER, 10.0, 0.0, area=[-250.0, -80.0, -30.0, 30.0])
    for (x, z) in ((-40.0, 34.0), (100.0, -34.0)):
        b.rig("moth_swarm", x, 10.0, z, 0.0)


# ============================================================== spawns
def _zombie_spawns(b: Area) -> None:
    for (x, z) in ((60.0, -10.0), (130.0, 16.0), (200.0, -14.0), (250.0, 0.0)):
        b.zombie_spawn(x, z, "water", y=GORGE_BED)
    for (x, z) in ((-200.0, -20.0), (-240.0, 20.0), (-250.0, -30.0)):
        b.zombie_spawn(x, z, "water", y=POND_BED)
    for (x, z) in ((-272.0, 150.0), (272.0, 190.0), (272.0, 110.0), (-272.0, -120.0), (-250.0, -150.0),
                   (272.0, -100.0), (272.0, -200.0), (180.0, -270.0), (40.0, -272.0), (-272.0, 60.0),
                   (114.0, -140.0), (-220.0, 190.0), (40.0, -190.0), (-60.0, -150.0)):
        b.zombie_spawn(x, z, "")
    for (x, z, y) in ((-272.0, 260.0, 12.0), (-60.0, 270.0, 12.0), (60.0, 270.0, 12.0), (220.0, 270.0, 12.0),
                      (200.0, 230.0, 8.0)):
        b.zombie_spawn(x, z, "", y=y)
