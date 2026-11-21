"""Redwater Cranberry Bogs -- harvest night, the bogs flooded and red.

Layout (north is +z)::

   z +280 ------------------------- the pine woods ---------------------------
          THE RESERVOIR, up on its       THE PUMP HOUSE      THE SAND PIT
          embankment; THE FLOODGATE      (the steam pump)    (the heaps, the
          on its crest, the flume                              screening plant)
   z +176 ======================= the north dike ==============================
          THE WEST BOG        ||  THE HARVEST BOG        || THE BUCKET ELEVATOR
          (the boardwalk, the ||  (the water reels, the  || THE RECEIVING SHED
           gazebo)            ||   booms, the berry pump)||  (the bins, the scale)
   z  +40 ======================= the cross dike ======== THE SCREENHOUSE =====
          THE DRY BOG         ||  THE DROWNED BOG        ||  (the safe room)
          (vines, the ditches,||  (left mid-harvest; the || THE CRANBERRY
           frost sprinklers)  ||   duck blind, HELP)     ||  FESTIVAL
   z -146 ======================= the south dike ==============================
          THE FARMHOUSE   THE WINDMILL   the harvester barn    the farm stand
   z -280 ======================== the county road ============================

Everybody deploys in the screenhouse, among the separators and the bins.

What makes it this place:

* **The bogs.**  Four of them, sunk below the dikes.  Three are flooded for
  the harvest, and the water is solid with floating berries, red from bank
  to bank: you wade in it, and so do they.  The dikes between are the only
  dry ground, and they are narrow.
* **The lure.**  Up on the reservoir's crest, the floodgate: open it and the
  flume roars, white water pouring into the harvest bog -- and the horde
  goes wading out into the middle after the noise.
* **High ground.**  The windmill's stage, the bucket elevator's head, the
  heaped sand, the reservoir's embankment, the duck blind on its stilts.
* **Somebody wrote HELP** with the floating booms, out in the drowned bog.
  It reads from the duck blind.
"""
from __future__ import annotations

import math
import random
from typing import List, Tuple

from .kit import (
    ASPHALT, BRICK, CONCRETE, CONCRETE_DARK, FLOOR, HAZARD, STEEL, STEEL_DARK, WARM, WOOD,
    WOOD_DARK, WOOD_LIGHT, Area, Surfaces, barrel_spot, bench, boundary, building, carve, crate,
    deploy_pad, flight, gable, house, lamp_post, plate, post_sign, rect, room_walls, sign_decal,
    slab, supply_ammo, supply_med, threshold, wall_sign)
from ..relay.kit import mound, pine, tier_stack, tree

Rect = Tuple[float, float, float, float]

HALF = 280.0
SKY = {"top": "#070b1c", "horizon": "#3a2c48", "sun": [0.35, 0.42, -0.62],
       "clouds": 0.3, "tint": "#b8c0e8"}
AMBIENT = "#5a5a7a"

GRASS = "#4a5a34"
PEAT = "#3a2a22"
VINES = "#5a2a2a"
BERRY = "#7a0c1c"
BOOM = "#f2a81a"
SAND = "#d8c89a"
SHINGLE = "#8a8a82"
WHITE = "#f2ece0"
RED = "#a8282e"
DIRT = "#7a6a4e"
PLANK = "#6a5a4a"

BOG_FLOOR = -3.0
WATER_TOP = -0.8
VINE_TOP = -2.0
DITCH_FLOOR = -4.0
DITCH_WATER = -2.8

BOG_WEST = (-262.0, -100.0, 48.0, 160.0)
BOG_HARVEST = (-84.0, 84.0, 48.0, 160.0)
BOG_DRY = (-262.0, -100.0, -130.0, 32.0)
BOG_DROWNED = (-84.0, 84.0, -130.0, 32.0)
DITCH_X = (-183.0, -179.0, -130.0, 32.0)
DITCH_Z = (-262.0, -100.0, -51.0, -47.0)

SCREEN = (104.0, 184.0, -20.0, 24.0)
SCREEN_H = 16.0
LOFT_Y = 9.4

RES = (-250.0, -40.0, 200.0, 262.0)
RES_BED = 1.0
RES_WATER = 4.2
CREST = 5.0
GATE = (-62.0, -42.0, 190.0, 200.0)
FLUME_X = -52.0
FLUME_Y = 8.0
PUMP = (-16.0, 20.0, 196.0, 222.0)
SANDPIT = (110.0, 270.0, 190.0, 272.0)
RECEIVING = (150.0, 250.0, 96.0, 136.0)
ELEVATOR = (134.0, 146.0, 136.0, 148.0)
ELEVATOR_TOP = 16.0
SCALE = (160.0, 180.0, 146.0, 162.0)
FARM = (-252.0, -212.0, -246.0, -206.0)
MILL = (-168.0, -152.0, -220.0, -204.0)
MILL_BASE = 4.5
MILL_LOFT = MILL_BASE + FLOOR + 9.0
BARN = (-120.0, -70.0, -252.0, -212.0)
STAGE = (220.0, 262.0, -110.0, -70.0)
STAND = (20.0, 60.0, -262.0, -250.0)
BLIND = (52.0, 68.0, -122.0, -106.0)
BLIND_Y = 3.0


def build(b: Area) -> None:
    rng = random.Random(0xB0C5)
    b.extra.update({"weather": "mist", "accent": "#e83a4a"})
    s = Surfaces(b)
    _ground(b, s)
    boundary(b, 30.0, "#1e2a1e", "#18221a", rng, horizon="forest")
    _flooded(b)
    _dry_bog(b)
    _boardwalk(b)
    _harvest(b, s)
    _drowned(b)
    _screenhouse(b, s)
    _reservoir(b, s)
    _pump_house(b, s)
    _sand_pit(b, s)
    _receiving(b, s, rng)
    _festival(b, s)
    _farm(b, s, rng)
    _windmill(b, s)
    _barn(b, s)
    _farm_stand(b, s)
    _country(b, s, rng)
    _paths(b, s)
    _rigs(b)
    _zombie_spawns(b)
    for x, z, name in ((144, 2, "the screenhouse"), (-140, 120, "the boardwalk"),
                       (-176, 120, "the gazebo"), (0, 104, "the harvest bog"),
                       (0, -50, "the drowned bog"), (-220, -90, "the dry bog"),
                       (-52, 195, "the floodgate"), (-145, 231, "the reservoir"),
                       (2, 209, "the pump house"), (190, 231, "the sand pit"),
                       (-232, -226, "the farmhouse"), (-160, -212, "the windmill"),
                       (-95, -232, "the harvester barn"), (200, 116, "the receiving shed"),
                       (140, 142, "the bucket elevator"), (241, -90, "the festival stage"),
                       (60, -114, "the duck blind"), (40, -256, "the farm stand")):
        b.landmark(float(x), float(z), name)
    b.camera(150.0, 40.0, 60.0, 0.0, -1.0, 100.0)
    b.camera(-100.0, 22.0, -10.0, -180.0, 0.0, 110.0)
    b.camera(20.0, 18.0, -150.0, 20.0, -1.0, -80.0)
    b.camera(-110.0, 26.0, -170.0, -160.0, 16.0, -212.0)


# ================================================================ ground
def _ground(b: Area, s: Surfaces) -> None:
    h = b.half + b.margin
    bogs = [BOG_WEST, BOG_HARVEST, BOG_DRY, BOG_DROWNED]
    for r in bogs:
        s.reserve(r)
    pieces = carve(rect(-h, h, -h, h), bogs)
    plate(b, pieces, 0.0, 0.6, GRASS, studs=True, material="grass")
    plate(b, pieces, -0.6, 5.4, "#3a3024")


def _bank_steps(b: Area, r: Rect, side: str, a: float, c: float) -> None:
    """Two steps up out of a flooded bog, against its ``side`` bank, from
    ``a`` to ``c`` along it."""
    x0, x1, z0, z1 = r
    if side == "x-":
        flight(b, "x", x0 + 6.0, x0, a, c, BOG_FLOOR, 0.0, PLANK, fill=BOG_FLOOR)
    elif side == "x+":
        flight(b, "x", x1 - 6.0, x1, a, c, BOG_FLOOR, 0.0, PLANK, fill=BOG_FLOOR)
    elif side == "z-":
        flight(b, "z", z0 + 6.0, z0, a, c, BOG_FLOOR, 0.0, PLANK, fill=BOG_FLOOR)
    else:
        flight(b, "z", z1 - 6.0, z1, a, c, BOG_FLOOR, 0.0, PLANK, fill=BOG_FLOOR)


def _boom(b: Area, x0: float, x1: float, z0: float, z1: float) -> None:
    """A length of floating boom: from the bog floor to just over the
    water, so it reads as floating and you hop it."""
    b.box([(x0 + x1) / 2.0, (BOG_FLOOR - 0.4) / 2.0, (z0 + z1) / 2.0],
          [x1 - x0, -0.4 - BOG_FLOOR, z1 - z0], BOOM)


# ============================================================ the bogs
def _flooded(b: Area) -> None:
    """The three flooded bogs: a peat floor, the berry-red water, steps
    up the banks."""
    for r in (BOG_WEST, BOG_HARVEST, BOG_DROWNED):
        slab(b, r, BOG_FLOOR, 6.0 + BOG_FLOOR, PEAT, studs=True)
        b.water((r[0] + r[1]) / 2.0, (r[2] + r[3]) / 2.0, r[1] - r[0], r[3] - r[2], WATER_TOP, BERRY)
    for side, a in (("x-", 60.0), ("z+", -240.0), ("z+", -130.0), ("z-", -240.0)):
        _bank_steps(b, BOG_WEST, side, a, a + 8.0)
    for side, a in (("x+", 54.0), ("x+", 146.0), ("x-", 140.0), ("z-", -40.0), ("z-", 56.0),
                    ("z+", 20.0)):
        _bank_steps(b, BOG_HARVEST, side, a, a + 8.0)
    for side, a in (("z+", -20.0), ("z+", 40.0), ("x-", -60.0), ("x+", -90.0), ("x+", 0.0),
                    ("z-", -40.0)):
        _bank_steps(b, BOG_DROWNED, side, a, a + 8.0)


def _dry_bog(b: Area) -> None:
    """The dry bog: the vine beds a step down from the dikes, the ditches
    a step below them crossing in the middle, plank bridges over them, the
    frost sprinklers' risers in rows -- and something in the ditch."""
    beds = carve(BOG_DRY, [DITCH_X, DITCH_Z])
    plate(b, beds, VINE_TOP, 6.0 + VINE_TOP, VINES, studs=True, material="grass")
    for r in [DITCH_Z] + carve(DITCH_X, [DITCH_Z]):
        slab(b, r, DITCH_FLOOR, 6.0 + DITCH_FLOOR, PEAT, studs=True)
        b.water((r[0] + r[1]) / 2.0, (r[2] + r[3]) / 2.0, r[1] - r[0], r[3] - r[2], DITCH_WATER,
                "#2a3a3a")
    for x in (-236.0, -140.0):
        b.box([x, VINE_TOP + 0.2, -49.0], [7.0, 0.4, 8.0], WOOD_LIGHT, studs=True)
    for z in (-104.0, 6.0):
        b.box([-181.0, VINE_TOP + 0.2, z], [8.0, 0.4, 7.0], WOOD_LIGHT, studs=True)
    for (x, z) in _SPRINKLERS:
        b.box([x, VINE_TOP + 1.5, z], [0.5, 3.0, 0.5], "#8a8f94", material="metal")
        b.box([x, VINE_TOP + 3.2, z], [1.2, 0.4, 1.2], STEEL_DARK, material="metal")
    # the dry harvester, walked off and left in the vines
    hx, hz = -232.0, -10.0
    b.box([hx, VINE_TOP + 1.5, hz], [6.0, 3.0, 4.4], "#c8a83a", material="metal")
    b.box([hx + 1.0, VINE_TOP + 3.6, hz], [2.6, 1.2, 3.0], STEEL_DARK)
    b.box([hx - 4.6, VINE_TOP + 0.6, hz], [3.2, 1.2, 4.8], "#5a5f66", material="metal")
    for dz in (-1.6, 1.6):
        b.box([hx + 4.5, VINE_TOP + 3.0, hz + dz], [3.0, 0.4, 0.4], STEEL_DARK)
    # the bog body: whoever it was has been in the peat a long time
    bx, bz = -181.0, -112.0
    bone = "#c8b89a"
    b.box([bx, DITCH_FLOOR + 0.4, bz - 3.4], [1.2, 0.8, 1.2], bone)
    b.box([bx, DITCH_FLOOR + 0.25, bz - 1.4], [2.0, 0.5, 2.2], bone)
    for dx in (-0.5, 0.5):
        b.box([bx + dx, DITCH_FLOOR + 0.2, bz + 2.3], [0.4, 0.4, 3.4], bone)
    b.box([bx + 1.4, DITCH_FLOOR + 0.2, bz - 1.0], [0.4, 0.4, 2.6], bone)


_SPRINKLERS = [(x, z) for x in (-246.0, -216.0, -150.0, -118.0) for z in (-114.0, -80.0, -20.0, 16.0)]


def _boardwalk(b: Area) -> None:
    """The boardwalk over the west bog: out from the middle dike to the
    gazebo, then south to the cross dike, on posts in the water."""
    deck = 1.0
    run_a = rect(-166.0, -100.0, 117.0, 123.0)
    gaz = rect(-186.0, -166.0, 110.0, 130.0)
    run_c = rect(-180.0, -174.0, 48.0, 110.0)
    for r in (run_a, gaz, run_c):
        slab(b, r, deck, 0.4, WOOD_LIGHT, studs=True)

    def post(x: float, z: float) -> None:
        b.box([x, (BOG_FLOOR + deck - 0.4) / 2.0, z], [0.8, deck - 0.4 - BOG_FLOOR, 0.8], WOOD_DARK)

    for x in (-110.0, -122.0, -134.0, -146.0, -158.0):
        post(x, 117.4)
        post(x, 122.6)
    for z in (56.0, 68.0, 80.0, 92.0, 104.0):
        post(-179.6, z)
        post(-174.4, z)
    for x in (-185.6, -166.4):
        for z in (110.4, 129.6):
            post(x, z)
    # the gazebo: posts, a stepped roof, benches, a rail on the west
    for x in (-185.0, -167.0):
        for z in (111.0, 129.0):
            b.box([x, deck + 4.5, z], [0.8, 9.0, 0.8], WHITE)
    slab(b, rect(-187.0, -165.0, 109.0, 131.0), deck + 9.6, 0.6, "#5a3a3a")
    slab(b, rect(-183.0, -169.0, 113.0, 127.0), deck + 10.8, 1.2, "#5a3a3a")
    slab(b, rect(-179.0, -173.0, 117.0, 123.0), deck + 12.0, 1.2, "#4a2a2a")
    bench(b, -176.0, 113.0, "x", y=deck)
    bench(b, -176.0, 127.0, "x", y=deck)
    b.box([-185.6, deck + 0.7, 120.0], [0.8, 1.4, 16.8], WHITE)
    barrel_spot(b, -170.0, deck, 126.0)


def _harvest(b: Area, s: Surfaces) -> None:
    """The harvest bog: the booms corralling the berries against the east
    bank where the pump lifts them up the elevator into the truck; the two
    water reels out in the middle, churning."""
    _boom(b, 39.4, 40.6, 65.4, 98.0)
    _boom(b, 39.4, 40.6, 106.0, 142.6)
    _boom(b, 40.6, 84.0, 65.4, 66.6)
    _boom(b, 40.6, 84.0, 141.4, 142.6)
    _boom(b, -70.0, -40.0, 150.0, 151.2)
    # the pump at the bank, the elevator up over the dike, the truck
    b.box([80.0, (BOG_FLOOR + 1.0) / 2.0, 104.0], [8.0, 1.0 - BOG_FLOOR, 6.0], "#4a6a8a", material="metal")
    s.reserve(rect(84.0, 120.0, 100.0, 108.0))
    for k, top in enumerate((2.0, 4.0, 6.0)):
        x0 = 84.0 + k * 5.4
        b.box([x0 + 2.7, top / 2.0, 104.0], [5.4, top, 4.0], "#3a3f46", studs=True)
    _berry_truck(b, 112.0, 104.0)
    # the water reels' frames: the reel itself turns (a rig)
    for (x, z) in ((-30.0, 90.0), (10.0, 130.0)):
        b.box([x, (BOG_FLOOR - 0.2) / 2.0, z], [8.0, -0.2 - BOG_FLOOR, 6.0], "#c8a83a", material="metal")
        b.box([x - 2.0, 0.6, z], [3.0, 1.6, 3.0], STEEL_DARK)
        b.box([x - 2.0, 2.6, z], [0.4, 2.4, 0.4], STEEL_DARK)
    supply_ammo(b, -110.0, 0.0, 179.0, "z-")


def _berry_truck(b: Area, x: float, z: float) -> None:
    """A stake truck along x with a load of berries heaped in the bed."""
    b.box([x, 1.6, z], [14.0, 1.6, 6.0], "#2a2f36", material="metal")
    b.box([x + 5.0, 4.2, z], [4.0, 3.6, 5.6], "#8a2a24", material="metal")
    b.box([x + 5.6, 4.8, z], [2.6, 1.6, 5.8], "#1d2226")
    for dz in (-2.8, 2.8):
        b.box([x - 2.0, 3.6, z + dz], [9.6, 2.4, 0.4], WOOD)
    b.box([x - 6.6, 3.6, z], [0.4, 2.4, 5.2], WOOD)
    b.box([x - 1.9, 3.2, z], [9.0, 1.6, 5.2], "#9a1a2a", studs=True)
    for dx in (-4.0, 4.0):
        for dz in (-3.0, 3.0):
            b.cyl([x + dx, 1.1, z + dz], [2.2, 0.8, 2.2], "#1b1d20", r=[math.pi / 2.0, 0, 0],
                  collide=False)


def _drowned(b: Area) -> None:
    """The drowned bog, left mid-harvest: a water reel on its side, the
    booms broken loose -- and laid out on the water in booms, HELP, to be
    read from the duck blind at its south-east corner."""
    # H E L P, each letter 12 wide and 16 tall, reading from the south
    stroke = 1.2
    z0, z1 = -100.0, -84.0
    letters = [
        (12.0, [(0.0, stroke, z0, z1), (12.0 - stroke, 12.0, z0, z1), (stroke, 12.0 - stroke, -92.6, -91.4)]),
        (-6.0, [(0.0, stroke, z0, z1), (stroke, 12.0, z1 - stroke, z1),
                (stroke, 10.0, -92.6, -91.4), (stroke, 12.0, z0, z0 + stroke)]),
        (-24.0, [(0.0, stroke, z0, z1), (stroke, 12.0, z0, z0 + stroke)]),
        (-42.0, [(0.0, stroke, z0, z1), (stroke, 12.0, z1 - stroke, z1),
                 (12.0 - stroke, 12.0, -92.0, z1 - stroke), (stroke, 12.0 - stroke, -92.0, -90.8)]),
    ]
    for left, strokes in letters:
        for (a, c, d, e) in strokes:
            # a letter is drawn with +x on the reader's left
            _boom(b, left + 12.0 - c, left + 12.0 - a, d, e)
    # broken booms, drifting
    _boom(b, -70.0, -52.0, 10.0, 11.2)
    _boom(b, 30.0, 31.2, -40.0, -20.0)
    # the capsized reel
    b.box([-40.0, (BOG_FLOOR - 0.6) / 2.0, -10.0], [8.0, -0.6 - BOG_FLOOR, 5.0], "#c8a83a", material="metal")
    b.box([-40.0, -1.2, -4.2], [9.0, 3.6, 2.4], "#5a5f66", material="metal")
    b.box([-37.0, 0.6, -10.0], [2.6, 2.4, 2.6], STEEL_DARK)
    # the duck blind: up the steps from the south dike, on its stilts
    flight(b, "z", -130.0, -122.0, 56.0, 64.0, 0.0, BLIND_Y, WOOD_DARK, fill=BOG_FLOOR)
    bx0, bx1, bz0, bz1 = BLIND
    slab(b, BLIND, BLIND_Y, 0.4, WOOD, studs=True)
    for x in (bx0 + 0.4, bx1 - 0.4):
        for z in (bz0 + 0.4, bz1 - 0.4):
            b.box([x, (BOG_FLOOR + BLIND_Y - 0.4) / 2.0, z], [0.8, BLIND_Y - 0.4 - BOG_FLOOR, 0.8],
                  WOOD_DARK)
    room_walls(b, BLIND, 0.6, BLIND_Y, BLIND_Y + 3.0, "#5a5a3a", sides=("x-", "x+", "z+"))
    for x in (bx0 + 0.3, bx1 - 0.3):
        for z in (bz0 + 0.3, bz1 - 0.3):
            b.box([x, BLIND_Y + 3.0 + 1.2, z], [0.6, 2.4, 0.6], WOOD_DARK)
    slab(b, rect(bx0 - 0.6, bx1 + 0.6, bz0 - 0.6, bz1 + 0.6), BLIND_Y + 6.0, 0.6, "#4a4a2a")
    supply_ammo(b, 60.0, BLIND_Y, -110.0, "z-")
    barrel_spot(b, 74.0, 0.0, -152.0)


# ========================================================= screenhouse
def _screenhouse(b: Area, s: Surfaces) -> None:
    """The screenhouse, where the berries were sorted: the separators along
    the south wall, a loft over the east end up a stair, the cupola."""
    x0, x1, z0, z1 = SCREEN
    s.reserve(rect(x0 - 2.0, x1 + 2.0, z0 - 2.0, z1 + 2.0))
    head = 10.0
    building(b, SCREEN, 0.0, SCREEN_H, SHINGLE, roof_colour="#4a4a48", floor_colour="#8a7a62",
             doors={"x-": [(-2.0, 8.0, head)], "z+": [(116.0, 126.0, head)],
                    "z-": [(132.0, 142.0, head)], "x+": [(-6.0, 4.0, 8.0)]},
             windows={"z+": [(136.0, 152.0, 4.0, 8.0), (166.0, 180.0, LOFT_Y + 1.6, LOFT_Y + 5.0)],
                      "z-": [(110.0, 124.0, 4.0, 8.0), (166.0, 180.0, LOFT_Y + 1.6, LOFT_Y + 5.0)],
                      "x+": [(8.0, 18.0, LOFT_Y + 1.6, LOFT_Y + 5.0)],
                      "x-": [(12.0, 20.0, 4.0, 8.0)]},
             glass=True, lights=WARM, no_lights=[rect(162.0, 184.0, -20.0, 24.0)])
    for side, span in (("x-", (-2.0, 8.0)), ("z+", (116.0, 126.0)), ("z-", (132.0, 142.0)),
                       ("x+", (-6.0, 4.0))):
        threshold(b, SCREEN, side, span)
    gable(b, SCREEN, SCREEN_H + 1.2, "#4a4a48", "x", tiers=4, rise=1.6)
    ridge = SCREEN_H + 1.2 + 4 * 1.6
    b.box([144.0, ridge + 2.0, 2.0], [8.0, 4.0, 8.0], WHITE)
    slab(b, rect(139.0, 149.0, -3.0, 7.0), ridge + 4.6, 0.6, "#4a4a48")
    wall_sign(b, x0 - 0.35, 12.5, 2.0, 30.0, 3.0,
              sign_decal("REDWATER CRANBERRY CO  1888", WHITE, RED, 10.0), "x-", WHITE)
    floor = FLOOR
    for z in (9.0, -1.0):
        for k in range(8):
            x = 112.0 + k * 6.3
            deploy_pad(b, x, z, floor, "#e83a4a", 5.0)
            b.safe_spawn(x, floor + 0.6, z, -math.pi / 2.0)
    # the separators: bounce boards stepped down a cabinet, a hopper on top
    for x in (146.0, 158.0):
        b.box([x, floor + 3.5, -14.0], [8.0, 7.0, 6.0], "#8a6a4a")
        b.box([x, floor + 7.9, -14.0], [6.0, 1.8, 4.0], "#6a5a4a")
        for k in range(3):
            b.box([x, floor + 1.4 + k * 2.0, -10.8], [6.0, 0.3, 0.4], WOOD_LIGHT)
    supply_ammo(b, 112.0, floor, -15.4, "z+")
    supply_med(b, 128.0, floor, -16.6, "z+")
    for z in (19.4, 15.0):
        crate(b, 108.6, floor, z, 4.0, "#8a5a3a")
    crate(b, 108.6, floor + 4.0, 17.2, 4.0, "#7a4a2a")
    # the loft over the east end, its rail, the stair along the north wall
    slab(b, rect(164.0, 182.0, -18.0, 22.0), LOFT_Y, 0.6, WOOD, studs=True)
    for z in (-12.0, 4.0):
        b.box([164.6, (floor + LOFT_Y - 0.6) / 2.0, z], [1.2, LOFT_Y - 0.6 - floor, 1.2], WOOD_DARK)
    b.box([164.4, LOFT_Y + 0.6, -1.0], [0.8, 1.2, 34.0], WOOD_DARK)
    flight(b, "x", 144.0, 164.0, 16.0, 22.0, floor, LOFT_Y, WOOD_DARK, fill=floor)
    supply_ammo(b, 174.0, LOFT_Y, 0.0, "x-")
    barrel_spot(b, 96.0, 0.0, -12.0)
    barrel_spot(b, 190.0, 0.0, 30.0)


# ============================================================ reservoir
def _reservoir(b: Area, s: Surfaces) -> None:
    """The reservoir up on its embankment, two tiers to the crest; the
    floodgate house on the south crest, its handwheel the lure; the flume
    running out over the dike road on trestles to spill into the harvest
    bog."""
    rx0, rx1, rz0, rz1 = RES
    outer = rect(rx0 - 18.0, rx1 + 18.0, rz0 - 16.0, rz1 + 14.0)
    inner = rect(rx0 - 12.0, rx1 + 12.0, rz0 - 10.0, rz1 + 8.0)
    s.reserve(outer)
    plate(b, carve(outer, [inner]), 2.5, 2.5, GRASS, studs=True, material="grass")
    plate(b, carve(inner, [RES]), CREST, CREST, "#55663e", studs=True, material="grass")
    slab(b, RES, RES_BED, RES_BED, PEAT, studs=True)
    b.water((rx0 + rx1) / 2.0, (rz0 + rz1) / 2.0, rx1 - rx0, rz1 - rz0, RES_WATER, "#1a2a3a")
    # up from the dike road, and up from beside the pump house
    flight(b, "z", 176.0, 184.0, -80.0, -72.0, 0.0, 2.5, CONCRETE, fill=0.0)
    flight(b, "z", 184.0, 190.0, -80.0, -72.0, 2.5, CREST, CONCRETE, fill=2.5)
    flight(b, "x", -14.0, -22.0, 240.0, 248.0, 0.0, 2.5, CONCRETE, fill=0.0)
    flight(b, "x", -22.0, -28.0, 240.0, 248.0, 2.5, CREST, CONCRETE, fill=2.5)
    # and back out of the water
    flight(b, "z", 212.0, 200.0, -150.0, -142.0, RES_BED, CREST, CONCRETE, fill=RES_BED)
    flight(b, "x", -238.0, -250.0, 230.0, 238.0, RES_BED, CREST, CONCRETE, fill=RES_BED)
    # the floodgate house
    gx0, gx1, gz0, gz1 = GATE
    building(b, GATE, CREST, 7.0, CONCRETE, roof_colour=CONCRETE_DARK, floor_colour="#6a6a6a",
             doors={"x-": [(191.0, 199.0, CREST + 6.0)]},
             windows={"z-": [(-58.0, -46.0, CREST + 3.0, CREST + 5.6)]}, glass=True, lights=WARM)
    threshold(b, GATE, "x-", (191.0, 199.0), y0=CREST)
    fy = CREST + FLOOR
    b.box([FLUME_X, fy + 1.5, 196.6], [3.0, 3.0, 2.4], STEEL_DARK, material="metal")
    b.cyl([FLUME_X, fy + 3.4, 196.6], [0.8, 0.8, 0.8], STEEL)
    b.cyl([FLUME_X, fy + 3.95, 196.6], [3.6, 0.3, 3.6], "#c43a32", material="metal")
    b.set_lure(FLUME_X, fy, 194.0, "the floodgate", "Open the floodgate", "ll_floodgate",
               (0.0, BOG_FLOOR, 104.0))
    wall_sign(b, gx0 + 10.0, CREST + 6.2, gz0 - 0.35, 14.0, 1.6,
              sign_decal("DANGER  FLOODGATE", "#f2d23a", "#1b1b1b", 8.7), "z-", "#f2d23a")
    # the flume: a trough on trestles, over the road, out over the bog
    fz0, fz1 = 156.0, gz0
    slab(b, rect(FLUME_X - 2.5, FLUME_X + 2.5, fz0, fz1), FLUME_Y, 0.4, WOOD)
    for dx in (-2.75, 2.75):
        b.box([FLUME_X + dx, FLUME_Y + 0.4, (fz0 + fz1) / 2.0], [0.5, 1.6, fz1 - fz0], WOOD_DARK)
    for (z, foot) in ((187.0, 2.5), (178.0, 0.0), (158.0, BOG_FLOOR)):
        for dx in (-2.0, 2.0):
            top = FLUME_Y - 0.4
            b.box([FLUME_X + dx, (foot + top) / 2.0, z], [0.8, top - foot, 0.8], WOOD_DARK)
    barrel_spot(b, -90.0, 0.0, 182.0)
    supply_med(b, -110.0, CREST, 194.0, "z-")


def _pump_house(b: Area, s: Surfaces) -> None:
    x0, x1, z0, z1 = PUMP
    s.reserve(rect(x0 - 1.0, x1 + 1.0, z0 - 2.0, z1 + 1.0))
    building(b, PUMP, 0.0, 13.0, BRICK, roof_colour="#3a3a3a", floor_colour="#6a6a62",
             doors={"z-": [(-2.0, 8.0, 10.0)]},
             windows={"x+": [(200.0, 206.0, 5.0, 9.0), (212.0, 218.0, 5.0, 9.0)],
                      "z+": [(-8.0, 0.0, 5.0, 9.0), (6.0, 14.0, 5.0, 9.0)]},
             glass=True, lights=WARM)
    threshold(b, PUMP, "z-", (-2.0, 8.0))
    b.box([14.0, 14.2 + 8.0, 218.0], [3.0, 16.0, 3.0], BRICK)
    b.box([2.0, FLOOR + 1.0, 211.0], [10.0, 2.0, 6.0], "#3a3f46", material="metal")
    b.box([-4.2, FLOOR + 2.0, 211.0], [2.4, 4.0, 3.0], STEEL_DARK, material="metal")
    # the main down to the reservoir
    b.box([-22.0, 4.0, 209.0], [12.0, 3.0, 3.0], "#5a5f66", material="metal")
    b.box([-19.0, 1.25, 209.0], [1.0, 2.5, 1.0], STEEL_DARK)
    wall_sign(b, 2.0, 11.2, z0 - 0.35, 18.0, 2.0, sign_decal("PUMP HOUSE NO 2", "#e8e0cc", "#3a2a22", 9.0),
              "z-", "#e8e0cc")
    supply_ammo(b, 14.0, FLOOR, 200.0, "z+")
    barrel_spot(b, 26.0, 0.0, 200.0)


def _sand_pit(b: Area, s: Surfaces) -> None:
    """The sand pit: the heap in terraces you can climb, a smaller one by
    the road, the screening plant on its legs, a loader."""
    s.reserve(SANDPIT)
    tier_stack(b, [[rect(130.0, 250.0, 200.0, 262.0)], [rect(140.0, 240.0, 206.0, 256.0)],
                   [rect(152.0, 228.0, 212.0, 250.0)], [rect(164.0, 216.0, 218.0, 244.0)]],
               0.0, [2.0], [SAND, "#cbb98a"])
    tier_stack(b, [[rect(112.0, 128.0, 250.0, 270.0)], [rect(115.0, 125.0, 254.0, 266.0)]],
               0.0, [2.0], ["#cbb98a", SAND])
    # the screening plant: four legs, the hopper and screen on them
    for x in (254.0, 266.0):
        for z in (196.0, 212.0):
            b.box([x, 5.0, z], [1.0, 10.0, 1.0], STEEL_DARK)
    b.box([260.0, 11.5, 204.0], [14.0, 3.0, 18.0], "#c8a83a", material="metal")
    b.box([260.0, 14.0, 204.0], [10.0, 2.0, 14.0], "#5a5f66", material="metal")
    # the loader, its bucket down
    lx, lz = 140.0, 190.0
    b.box([lx, 2.0, lz], [10.0, 4.0, 6.0], "#e8a81a", material="metal")
    b.box([lx + 2.0, 5.6, lz], [4.0, 3.2, 5.0], "#2a2f36")
    b.box([lx - 6.5, 1.2, lz], [3.0, 2.4, 7.0], "#5a5f66", material="metal")
    supply_ammo(b, 190.0, 8.0, 231.0, "z+")


def _receiving(b: Area, s: Surfaces, rng: random.Random) -> None:
    """The receiving shed: a roof on posts over the berry bins and a
    truck; the bucket elevator beside it with the long stair up to its
    head; the scale house and its plate."""
    x0, x1, z0, z1 = RECEIVING
    s.reserve(rect(x0 - 2.0, x1 + 2.0, z0 - 2.0, z1 + 2.0))
    for x in (150.0, 175.0, 200.0, 225.0, 250.0):
        for z in (96.0, 136.0):
            b.box([x, 7.0, z], [1.2, 14.0, 1.2], STEEL_DARK)
    slab(b, rect(148.0, 252.0, 94.0, 138.0), 14.6, 0.6, "#6a6a66")
    for k, x in enumerate((158.0, 168.0, 182.0, 192.0, 232.0, 242.0)):
        for z in (104.0, 128.0):
            crate(b, x, 0.0, z, 4.4, "#8a5a3a")
            if (k + int(z)) % 3 != 0:
                crate(b, x, 4.4, z, 4.4, "#7a4a2a")
    _berry_truck(b, 212.0, 116.0)
    barrel_spot(b, 196.0, 0.0, 116.0)
    supply_med(b, 244.0, 0.0, 116.0, "x-")
    # the bucket elevator and its stair
    ex0, ex1, ez0, ez1 = ELEVATOR
    s.reserve(rect(98.0, ex1 + 2.0, ez0 - 2.0, ez1 + 2.0))
    b.box([(ex0 + ex1) / 2.0, (ELEVATOR_TOP - 0.6) / 2.0, (ez0 + ez1) / 2.0],
          [ex1 - ex0, ELEVATOR_TOP - 0.6, ez1 - ez0], "#8a8f94", material="metal")
    slab(b, rect(ex0 - 2.0, ex1 + 2.0, ez0 - 2.0, ez1 + 2.0), ELEVATOR_TOP, 0.6, STEEL, studs=True,
         material="metal")
    flight(b, "x", 100.0, ex0 - 2.0, 140.0, 146.0, 0.0, ELEVATOR_TOP, STEEL_DARK, fill=0.0)
    b.box([141.0, ELEVATOR_TOP + 3.0, 142.0], [6.0, 6.0, 6.0], "#c8a83a", material="metal")
    b.box([141.0, ELEVATOR_TOP + 9.0, 142.0], [2.4, 6.0, 2.4], "#8a8f94", material="metal")
    for (a, c, d, e) in ((ex1 + 1.4, ex1 + 2.0, ez0 - 2.0, ez1 + 2.0),
                         (ex0 - 2.0, ex1 + 1.4, ez1 + 1.4, ez1 + 2.0),
                         (ex0 - 2.0, ex1 + 1.4, ez0 - 2.0, ez0 - 1.4)):
        b.box([(a + c) / 2.0, ELEVATOR_TOP + 0.6, (d + e) / 2.0], [c - a, 1.2, e - d], HAZARD)
    supply_ammo(b, 136.0, ELEVATOR_TOP, 137.0, "z+")
    # the scale house
    sx0, sx1, sz0, sz1 = SCALE
    s.reserve(SCALE)
    building(b, SCALE, 0.0, 9.0, WHITE, roof_colour=RED, floor_colour="#8a7a62",
             doors={"x+": [(150.0, 158.0, 7.6)]}, windows={"z-": [(164.0, 176.0, 3.6, 6.6)]},
             glass=True, lights=WARM)
    threshold(b, SCALE, "x+", (150.0, 158.0))
    s.lay(rect(182.0, 206.0, 146.0, 162.0), 0.3, STEEL, studs=True)
    wall_sign(b, (sx0 + sx1) / 2.0, 7.2, sz0 - 0.35, 14.0, 1.8, sign_decal("WEIGH STATION", WHITE, RED, 7.8),
              "z-", WHITE)


def _festival(b: Area, s: Surfaces) -> None:
    """The cranberry festival on the field east of the screenhouse: the
    stage and the Cranberry Queen's throne, the parade float with its giant
    berry, hay bales for seats, the juice stand, a bog in a tank."""
    x0, x1, z0, z1 = STAGE
    s.reserve(rect(x0 - 10.0, x1, z0, z1))
    slab(b, STAGE, 3.0, 3.0, WOOD, studs=True)
    flight(b, "x", 212.0, x0, -94.0, -86.0, 0.0, 3.0, WOOD_DARK, fill=0.0)
    b.box([x1 - 0.5, 3.0 + 6.0, (z0 + z1) / 2.0], [1.0, 12.0, z1 - z0], RED)
    wall_sign(b, x1 - 1.35, 12.0, (z0 + z1) / 2.0, 30.0, 4.0,
              sign_decal("CRANBERRY FESTIVAL", RED, WHITE, 7.5), "x-", RED)
    # the throne
    b.box([256.0, 3.0 + 1.0, -90.0], [4.0, 2.0, 5.0], "#c8a83a")
    b.box([258.6, 3.0 + 4.0, -90.0], [1.2, 8.0, 5.0], "#c8a83a")
    b.box([258.6, 3.0 + 8.6, -90.0], [1.2, 1.2, 1.2], "#e83a4a")
    # the hay bale seats, facing the stage
    for row, x in enumerate((176.0, 190.0)):
        for z in (-104.0, -94.0, -84.0, -74.0):
            b.box([x, 1.3, z + (row * 2.0)], [4.0, 2.6, 8.0], "#d8c070", studs=True)
    # the parade float: a flatbed and the giant cranberry on it
    fx, fz = 160.0, -60.0
    b.box([fx, 1.2, fz], [24.0, 2.4, 10.0], "#3a7a3a", studs=True)
    b.sphere([fx + 2.0, 2.4 + 6.0, fz], [12.0, 12.0, 12.0], "#b01a2a")
    b.box([fx + 2.0, 2.4 + 12.8, fz], [1.0, 1.6, 1.0], "#5a3a1a")
    b.box([fx - 6.0, 2.4 + 1.2, fz], [4.0, 2.4, 6.0], WHITE)
    post_sign(b, fx - 10.5, fz, 2.4, 3.0, 10.0, 2.4, sign_decal("TASTE THE RED", WHITE, RED, 4.2), "x-", WHITE)
    for (x, z) in ((166.0, -120.0), (166.0, -72.0), (214.0, -120.0), (214.0, -66.0)):
        b.box([x, 6.0, z], [0.6, 12.0, 0.6], WHITE)
    # the juice stand
    jx, jz = 230.0, -30.0
    s.reserve(rect(jx - 7.0, jx + 7.0, jz - 5.0, jz + 5.0))
    b.box([jx, 1.6, jz - 3.0], [12.0, 3.2, 2.0], WOOD, studs=True)
    for dx in (-5.6, 5.6):
        b.box([jx + dx, 4.5, jz + 2.0], [0.8, 9.0, 0.8], WHITE)
        b.box([jx + dx, 6.1, jz - 2.6], [0.8, 5.8, 0.8], WHITE)
    b.box([jx, 9.3, jz], [14.0, 0.6, 10.0], RED)
    wall_sign(b, jx, 10.6, jz - 4.65, 12.0, 2.0, sign_decal("CRAN JUICE 25c", WHITE, RED, 6.0), "z-", WHITE)
    # the bog in a tank, for the visitors to see a harvest up close
    tx0, tx1, tz0, tz1 = 196.0, 212.0, -56.0, -46.0
    s.reserve(rect(tx0, tx1, tz0, tz1))
    for (a, c, d, e) in ((tx0, tx1, tz0, tz0 + 0.8), (tx0, tx1, tz1 - 0.8, tz1),
                         (tx0, tx0 + 0.8, tz0 + 0.8, tz1 - 0.8), (tx1 - 0.8, tx1, tz0 + 0.8, tz1 - 0.8)):
        b.box([(a + c) / 2.0, 1.6, (d + e) / 2.0], [c - a, 3.2, e - d], "#3a7ac8")
    slab(b, rect(tx0 + 0.8, tx1 - 0.8, tz0 + 0.8, tz1 - 0.8), 1.6, 1.6, PEAT)
    b.water((tx0 + tx1) / 2.0, (tz0 + tz1) / 2.0, tx1 - tx0 - 1.6, tz1 - tz0 - 1.6, 2.8, BERRY)
    supply_ammo(b, 236.0, 3.0, -76.0, "z+")
    barrel_spot(b, 186.0, 0.0, -50.0)


# ================================================================ farm
def _farm(b: Area, s: Surfaces, rng: random.Random) -> None:
    """The farmhouse, facing the bogs across its yard; the clothesline."""
    s.reserve(rect(FARM[0] - 2.0, FARM[1] + 2.0, FARM[2] - 2.0, FARM[3] + 8.0))
    house(b, FARM, "z+", WHITE, "#5a3a3a", height=13.0, rng=rng)
    for x in (-206.0, -182.0):
        b.box([x, 4.0, -250.0], [0.8, 8.0, 0.8], WOOD_DARK)
    b.box([-194.0, 7.8, -250.0], [23.2, 0.4, 0.4], WOOD_DARK)
    for (x, z) in ((-266.0, -196.0), (-200.0, -262.0), (-266.0, -258.0)):
        tree(b, x, z, 0.0, 1.3, WOOD, "#2f5a34")
    supply_med(b, -246.0, FLOOR, -242.6, "z+")


def _windmill(b: Area, s: Surfaces) -> None:
    """The old smock mill on its knoll: in at the east door, up the stair
    to the loft, out onto the stage over the bogs; the sails on the west
    face (a rig)."""
    s.reserve(rect(-188.0, -132.0, -240.0, -184.0))
    tier_stack(b, [[rect(-186.0, -134.0, -238.0, -186.0)], [rect(-180.0, -140.0, -232.0, -192.0)],
                   [rect(-174.0, -146.0, -226.0, -198.0)]], 0.0, [1.5], ["#4f6038", GRASS])
    x0, x1, z0, z1 = MILL
    building(b, MILL, MILL_BASE, 18.0, SHINGLE, roof_colour="#4a4a48", floor_colour=WOOD,
             doors={"x+": [(-217.0, -209.0, MILL_BASE + 8.0)]},
             windows={"z+": [(-164.0, -156.0, MILL_LOFT, MILL_LOFT + 6.5)]}, lights=WARM,
             no_lights=[rect(x0, x1, -212.0, z1)])
    threshold(b, MILL, "x+", (-217.0, -209.0), y0=MILL_BASE)
    gable(b, MILL, MILL_BASE + 18.0 + 1.2, "#4a4a48", "x", tiers=3, rise=1.5)
    slab(b, rect(x0 + 2.0, x1 - 2.0, -210.0, z1 - 2.0), MILL_LOFT, 0.6, WOOD, studs=True)
    flight(b, "z", z0 + 2.0, -210.0, x0 + 2.0, x0 + 7.0, MILL_BASE + FLOOR, MILL_LOFT, WOOD_DARK,
           fill=MILL_BASE + FLOOR)
    # the stage
    slab(b, rect(-170.0, -150.0, z1, z1 + 4.0), MILL_LOFT, 0.6, WOOD, studs=True)
    for x in (-169.4, -160.0, -150.6):
        b.box([x, (MILL_BASE + MILL_LOFT - 0.6) / 2.0, z1 + 3.4], [0.8, MILL_LOFT - 0.6 - MILL_BASE, 0.8],
              WOOD_DARK)
    b.box([-160.0, MILL_LOFT + 0.6, z1 + 3.7], [20.0, 1.2, 0.6], WOOD_DARK)
    for x in (-169.7, -150.3):
        b.box([x, MILL_LOFT + 0.6, z1 + 1.7], [0.6, 1.2, 3.4], WOOD_DARK)
    supply_med(b, -158.0, MILL_BASE + FLOOR, -207.4, "z-")
    barrel_spot(b, -140.0, 0.0, -180.0)


def _barn(b: Area, s: Surfaces) -> None:
    """The harvester barn: the old picking machines in a row, the scoops
    hung on the wall, hay at the back."""
    x0, x1, z0, z1 = BARN
    s.reserve(BARN)
    building(b, BARN, 0.0, 14.0, "#8a2a24", roof_colour="#4a4a48", floor_colour="#7a6a52",
             doors={"z+": [(-102.0, -88.0, 11.0)], "x-": [(-236.0, -228.0, 9.0)]},
             windows={"x+": [(-244.0, -236.0, 5.0, 9.0), (-228.0, -220.0, 5.0, 9.0)]},
             glass=True, lights=WARM)
    threshold(b, BARN, "z+", (-102.0, -88.0))
    threshold(b, BARN, "x-", (-236.0, -228.0))
    gable(b, BARN, 14.0 + 1.2, "#4a4a48", "x", tiers=3, rise=1.6)
    for k, x in enumerate((-110.0, -95.0, -80.0)):
        b.box([x, FLOOR + 1.4, -242.0], [6.0, 2.8, 8.0], ["#c8a83a", "#8a2a24", "#3a6a3a"][k], material="metal")
        b.box([x, FLOOR + 3.6, -245.0], [4.0, 1.6, 2.0], STEEL_DARK)
        b.box([x, FLOOR + 0.6, -237.4], [5.0, 1.2, 1.2], "#5a5f66")
    for k in range(5):
        b.box([x0 + 8.0 + k * 8.0, 8.0, z0 + 2.06], [4.0, 3.0, 0.12], WOOD_LIGHT, collide=False)
    for k in range(3):
        b.box([x1 - 6.0, FLOOR + 1.3 + k * 2.6, z1 - 6.0], [6.0, 2.6, 4.0 - k * 0.6], "#d8c070", studs=True)
    supply_ammo(b, -76.0, FLOOR, -226.0, "z+")


def _farm_stand(b: Area, s: Surfaces) -> None:
    """The farm stand on the county road: berries by the quart and an honor
    box for the money."""
    x0, x1, z0, z1 = STAND
    s.reserve(STAND)
    for x in (x0 + 0.6, x1 - 0.6):
        for z in (z0 + 0.6, z1 - 0.6):
            b.box([x, 4.5, z], [1.2, 9.0, 1.2], WOOD_DARK)
    slab(b, rect(x0 - 1.0, x1 + 1.0, z0 - 1.0, z1 + 1.0), 9.6, 0.6, RED)
    b.box([(x0 + x1) / 2.0, 1.6, z0 + 3.0], [x1 - x0 - 4.0, 3.2, 2.4], WOOD, studs=True)
    for k in range(5):
        b.box([x0 + 5.0 + k * 6.0, 3.6, z0 + 3.0], [3.0, 0.8, 1.8], "#9a1a2a", studs=True)
    b.box([x1 - 5.0, 4.0, z0 + 3.0], [1.6, 1.6, 1.6], "#3a5a8a")
    wall_sign(b, (x0 + x1) / 2.0, 10.8, z0 - 0.65, 26.0, 2.4,
              sign_decal("FRESH CRANBERRIES  HONOR BOX", WHITE, RED, 10.8), "z-", WHITE)


# ============================================================ country
def _country(b: Area, s: Surfaces, rng: random.Random) -> None:
    """Knolls with trees on the open ground east and south, the Redwater
    family plot on its rise, the billboard on the county road, pines along
    the north woods, lamps along the dikes."""
    for (cx, cz, rx, rz, lv) in ((240.0, 40.0, 24.0, 18.0, 3), (250.0, 170.0, 20.0, 14.0, 2),
                                 (100.0, -205.0, 22.0, 16.0, 2), (150.0, -100.0, 14.0, 12.0, 2)):
        s.reserve(rect(cx - rx, cx + rx, cz - rz, cz + rz))
        top = mound(b, cx, cz, rx, rz, lv, 1.4, ["#4f6038", GRASS])
        tree(b, cx, cz, top, rng.uniform(1.1, 1.4), WOOD, "#2f5a34")
    # the family plot: headstones on the rise, the founder's obelisk, a yew
    s.reserve(rect(170.0, 230.0, -229.0, -181.0))
    top = mound(b, 200.0, -205.0, 30.0, 24.0, 3, 1.2, ["#4f6038", GRASS], shrink=0.6)
    for k, (x, z) in enumerate(((192.0, -209.0), (196.0, -209.0), (204.0, -209.0), (208.0, -209.0),
                                (192.0, -201.0), (196.0, -201.0), (208.0, -201.0))):
        b.box([x, top + 1.1 + (k % 2) * 0.2, z], [1.8, 2.2 + (k % 2) * 0.4, 0.5], "#8a8a86")
    b.box([200.0, top + 3.0, -205.0], [1.6, 6.0, 1.6], "#9a9a94")
    b.box([200.0, top + 0.4, -205.0], [3.0, 0.8, 3.0], "#7a7a76")
    tree(b, 212.0, -205.0, top, 1.2, WOOD_DARK, "#1f3a26")
    post_sign(b, 200.0, -196.0, top, 1.6, 8.0, 1.6, sign_decal("REDWATER 1888", "#8a8a86", "#2a2a2a", 5.0),
              "z+", "#8a8a86")
    # the billboard by the road
    for x in (108.0, 132.0):
        b.box([x, 7.0, -236.0], [1.0, 14.0, 1.0], WOOD_DARK)
    wall_sign(b, 120.0, 16.0, -236.85, 28.0, 7.0,
              sign_decal("REDWATER  THE PRIDE OF HARROW COUNTY", WHITE, RED, 4.0), "z-", WHITE)
    for k in range(10):
        x = -260.0 + k * 22.0 + rng.uniform(-4.0, 4.0)
        pine(b, x, 278.5, 0.0, rng.uniform(1.2, 1.6))
    for (x, z) in ((40.0, 268.0), (70.0, 274.0), (96.0, 262.0), (272.0, 160.0), (272.0, 60.0),
                   (-272.0, -170.0)):
        pine(b, x, z, 0.0, rng.uniform(1.2, 1.5))
    for (x, z) in ((-99.0, 33.0), (-99.0, -60.0), (-99.0, 100.0), (99.0, 33.0), (99.0, -60.0),
                   (-180.0, 175.0), (0.0, 175.0), (-180.0, -145.0), (20.0, -145.0), (99.0, 128.0)):
        lamp_post(b, x, z, h=12.0, light=WARM)


def _paths(b: Area, s: Surfaces) -> None:
    for r in (rect(-262.0, 100.0, 162.0, 174.0), rect(-98.0, -86.0, -146.0, 176.0),
              rect(-278.0, -264.0, -146.0, 176.0), rect(86.0, 98.0, -146.0, 176.0),
              rect(-262.0, 100.0, 34.0, 46.0), rect(-262.0, 100.0, -144.0, -132.0),
              rect(100.0, 210.0, -40.0, -30.0), rect(-6.0, 6.0, -264.0, -146.0),
              rect(-236.0, -228.0, -198.0, -146.0), rect(-104.0, -88.0, -210.0, -146.0)):
        s.lay(r, 0.3, DIRT, studs=True)
    s.lay(rect(-280.0, 280.0, -280.0, -266.0), 0.3, ASPHALT)


# ================================================================ rigs
def _rigs(b: Area) -> None:
    b.rig("water_reel", -30.0 + 4.6, WATER_TOP, 90.0, 0.0)
    b.rig("water_reel", 10.0 + 4.6, WATER_TOP, 130.0, 0.0)
    b.rig("berry_raft", 62.0, WATER_TOP, 104.0, 0.0, area=[42.0, 83.0, 68.0, 140.0], n=26)
    b.rig("floodgate", FLUME_X, CREST + FLOOR + 4.1, 196.6, 0.0, z0=156.0, z1=GATE[2],
          trough=FLUME_Y, pour=WATER_TOP)
    b.rig("frost_sprinklers", -181.0, VINE_TOP + 3.4, -49.0, 0.0,
          heads=[[x, VINE_TOP + 3.4, z] for (x, z) in _SPRINKLERS])
    b.rig("pump_engine", 2.0, FLOOR + 2.0, 211.0, 0.0, stack_p=[14.0, 30.2, 218.0])
    b.rig("windmill_sails", MILL[0] - 0.6, 24.0, -212.0, -math.pi / 2.0, r=12.0)
    b.rig("heron", -200.0, BOG_FLOOR, 90.0, 0.0, area=[-250.0, -120.0, 60.0, 150.0])
    b.rig("bog_hand", 40.0, WATER_TOP, -112.0, 0.0)
    b.rig("decoys", 38.0, WATER_TOP, -104.0, 0.0, area=[24.0, 50.0, -126.0, -90.0], n=6)
    b.rig("frogs", -181.0, VINE_TOP, -49.0, 0.0,
          spots_p=[[-186.0, VINE_TOP, -70.0], [-176.0, VINE_TOP, -20.0], [-200.0, VINE_TOP, -45.0],
                   [-150.0, VINE_TOP, -53.0], [-186.0, VINE_TOP, 10.0], [-120.0, VINE_TOP, -45.0]])
    b.rig("weathervane", 144.0, SCREEN_H + 1.2 + 4 * 1.6 + 4.6, 2.0, 0.0)
    b.rig("clothesline", -194.0, 7.8, -250.0, 0.0, w=24.0)
    b.rig("bunting", 190.0, 0.0, -93.0, 0.0,
          poles=[[166.0, -120.0], [166.0, -72.0], [214.0, -66.0], [214.0, -120.0]], h=12.0)
    for (x, z) in ((-99.0, 100.0), (99.0, 33.0)):
        b.rig("moth_swarm", x, 10.0, z, 0.0)


# ============================================================== spawns
def _zombie_spawns(b: Area) -> None:
    for (x, z) in ((-240.0, 70.0), (-130.0, 150.0), (-230.0, 146.0), (-60.0, 120.0), (20.0, 70.0),
                   (-60.0, 64.0), (-70.0, -120.0), (-60.0, -20.0), (-20.0, -10.0), (20.0, -60.0)):
        b.zombie_spawn(x, z, "water", y=BOG_FLOOR)
    for (x, z) in ((-250.0, -120.0), (-110.0, 20.0), (-240.0, 20.0), (-140.0, -90.0)):
        b.zombie_spawn(x, z, "", y=VINE_TOP)
    for (x, z) in ((-272.0, 0.0), (-272.0, -100.0), (272.0, 100.0), (272.0, -60.0), (60.0, 276.0),
                   (276.0, 180.0), (-200.0, -274.0), (100.0, -274.0), (240.0, -274.0), (-40.0, -274.0),
                   (150.0, 172.0), (-272.0, 150.0)):
        b.zombie_spawn(x, z, "")
