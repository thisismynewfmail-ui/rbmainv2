"""Cedar Pines Camp -- a summer camp on a lake, the last hour of the sun.

Layout (north is +z)::

      z +280  ------------------------ the pines -------------------------------
              WEST CABINS        bathhouse   FIRE LOOKOUT      EAST CABINS
              (round a firepit)                                (round a firepit)
      z +120  .................................................................
              MESS HALL   |c|      RANGER STATION        PARKING + RV  <== gate
              dinner bell |r|      (the safe room)                       road
      z    0  OVERLOOK    |e|                                  ARCHERY RANGE
              RIDGE + the |e|  volleyball  AMPHITHEATRE
              OLD MINE    |k|  beach                BOATHOUSE
      z -124  ~~~~~~~~~~~~~~~~~~~~~ CEDAR LAKE (raft, island) ~~~~~~~~~~~~~~~~
      z -280  ------------------------ the far shore --------------------------

Everybody deploys in the ranger station.

Three things make this one different from the built-up places:

* **Water and wading.**  The lake is waist-deep over a stony bed and the
  creek is shallower still; both slow nobody down but both are open ground.
  The beach shelves gently, the boathouse and the dock stand over the water,
  and the raft and the island are islands of cover for anyone patient.
* **The ridge and the mine.**  The overlook is four terraces high, climbed by
  stairs cut between the tiers -- the best view of the camp there is.  Under
  it, a cutting leads into the old mine, and the mine is where the infected
  come out of: whoever holds its mouth holds back the west.
* **The trees.**  There are a lot of them, and their trunks are solid: they
  are cover from Spitters and line-of-sight breaks from everything else.

The dinner bell on the mess hall porch is the lure.
"""
from __future__ import annotations

import math
import random
from typing import List

from .kit import (
    CONCRETE, CONCRETE_DARK, COLD, FLOOR, GLASS, HAZARD, LAMP, STEEL,
    STEEL_DARK, WARM, WOOD, WOOD_DARK, WOOD_LIGHT, Area, Surfaces, barrel_spot,
    bench, boat, boundary, building, car, chain_fence, crate, deploy_pad,
    flight, flood, gable, holed_wall, house, lamp_post, pallet_stack, plate,
    carve, rect, room_walls, sandbags, sign_decal, slab, solid_fence,
    strip_light, supply_ammo, supply_med, threshold, van, wall_sign,
    watchtower)

HALF = 280.0
GRASS = "#4f6b34"
GRASS_DARK = "#435c2c"
DIRT = "#7a6448"
SAND = "#c8b48a"
LOG = "#7a5335"
LOG_DARK = "#5a3a22"
ROOF = "#3f5a3a"
ROCK = "#6b6250"
SKY = {"top": "#35366a", "horizon": "#f0a060", "sun": [-0.55, 0.16, 0.62],
       "clouds": 0.38, "tint": "#ffc080"}
AMBIENT = "#7a6a70"

LAKE = (-120.0, 140.0, -262.0, -124.0)
CREEK = (-118.0, -106.0, -124.0, 150.0)
BED = -4.0
CREEK_BED = -2.0
STATION = (-40.0, 40.0, 10.0, 60.0)
MESS = (-206.0, -132.0, 40.0, 110.0)


def build(b: Area) -> None:
    rng = random.Random(0xCED4)
    _ground(b)
    boundary(b, 30.0, "#24331f", "#1b2a18", rng, horizon="forest")
    s = Surfaces(b)
    for hole in (LAKE, CREEK):
        s.reserve(hole)
    keep_out: List = []
    _station(b, s, keep_out)
    _mess(b, s, keep_out)
    _ridge(b, s, keep_out)
    _lake(b, s, keep_out)
    _shore(b, s, keep_out, rng)
    _cabins(b, s, keep_out, rng)
    _east(b, s, keep_out, rng)
    _trails(b, s)
    _forest(b, rng, keep_out)
    _zombie_spawns(b)
    for x, z, name in ((0, 35, "the ranger station"), (-133, 75, "the mess hall"),
                       (-240, -50, "the overlook"), (-232, -40, "the old mine"),
                       (85, -130, "the boathouse"), (70, -70, "the amphitheatre"),
                       (-22, -202, "the raft"), (41, -215, "the island"),
                       (-205, 196, "the west cabins"), (200, 196, "the east cabins"),
                       (60, 150, "the fire lookout"), (150, 86, "the car park"),
                       (205, -15, "the archery range"), (-112, 0, "the creek")):
        b.landmark(float(x), float(z), name)


# ================================================================ ground
def _ground(b: Area) -> None:
    h = b.half + b.margin
    pieces = carve(rect(-h, h, -h, h), [LAKE, CREEK])
    plate(b, pieces, 0.0, 0.6, GRASS, studs=True, material="grass")
    plate(b, pieces, -0.6, 5.4, "#5a4a38")
    slab(b, LAKE, BED, 2.0, "#4a5048", studs=True)
    slab(b, CREEK, CREEK_BED, 4.0, "#4a5048", studs=True)
    b.water((LAKE[0] + LAKE[1]) / 2.0, (LAKE[2] + LAKE[3]) / 2.0,
            LAKE[1] - LAKE[0], LAKE[3] - LAKE[2], -1.0, "#2f6a7a")
    b.water((CREEK[0] + CREEK[1]) / 2.0, (CREEK[2] + CREEK[3]) / 2.0,
            CREEK[1] - CREEK[0], CREEK[3] - CREEK[2], -0.8, "#3a7a8a")


# ======================================================== ranger station
def _station(b: Area, s: Surfaces, keep_out: List) -> None:
    x0, x1, z0, z1 = STATION
    s.reserve(rect(x0, x1, z0 - 7.0, z1))
    keep_out.append(rect(x0 - 10.0, x1 + 16.0, z0 - 12.0, z1 + 8.0))
    building(b, STATION, 0.0, 12.0, LOG, roof_colour=ROOF, floor_colour="#8a6a4a",
             doors={"z-": [(-8.0, 8.0, 10.0)], "x-": [(34.0, 46.0, 10.0)],
                    "x+": [(34.0, 46.0, 10.0)]},
             windows={"z-": [(-34.0, -16.0, 3.6, 8.4), (16.0, 34.0, 3.6, 8.4)],
                      "z+": [(-30.0, -10.0, 3.6, 8.4), (10.0, 30.0, 3.6, 8.4)]},
             glass=True, eave=1.4, lights=WARM)
    for side, span in (("z-", (-8.0, 8.0)), ("x-", (34.0, 46.0)), ("x+", (34.0, 46.0))):
        threshold(b, STATION, side, span)
    gable(b, STATION, 13.2, ROOF, "x", 3, 1.6, 0.0)
    # log courses round the outside, the way a cabin is built
    for k in range(4):
        y = 1.6 + k * 2.8
        for a, c in ((x0, -8.0), (8.0, x1)):
            b.box([(a + c) / 2.0, y, z0 - 0.15], [c - a, 0.5, 0.3], LOG_DARK)
    # the porch and its roof
    slab(b, rect(-18.0, 18.0, z0 - 7.0, z0), 1.2, 1.2, WOOD_LIGHT)
    for x in (-17.0, 17.0):
        b.box([x, 1.2 + 4.65, z0 - 6.2], [1.2, 9.3, 1.2], LOG_DARK)
    slab(b, rect(-19.0, 19.0, z0 - 7.0, z0), 11.1, 0.6, ROOF)
    wall_sign(b, 0.0, 12.0, z0 - 7.35, 20.0, 1.6,
              sign_decal("RANGER STATION", "#5a3a22", "#f2e2a8", 12.5), "z-",
              "#5a3a22")
    # inside: the pads, a desk with the radio, the map table, the bunks
    for row, z in enumerate((20.0, 29.0)):
        for x in (-34.0, -25.0, -16.0, -8.0, 8.0, 16.0, 25.0, 34.0):
            deploy_pad(b, x, z, FLOOR, "#7aa84a", 5.0)
            b.safe_spawn(x, FLOOR + 0.6, z, math.pi)
    b.box([0.0, FLOOR + 1.8, 44.0], [16.0, 3.6, 8.0], WOOD, studs=True)
    b.box([-26.0, FLOOR + 2.0, 54.0], [16.0, 4.0, 4.0], WOOD_DARK, studs=True)
    b.box([-26.0, FLOOR + 5.2, 54.0], [4.0, 2.4, 3.0], "#3a3f46")
    for x in (24.0, 34.0):
        b.box([x, FLOOR + 1.2, 52.0], [6.0, 2.4, 10.0], "#6b3a3a", studs=True)
    supply_ammo(b, -35.0, FLOOR, 42.0, "x+")
    supply_med(b, 36.4, FLOOR, 42.0, "x-")
    # the radio mast out back
    b.cyl([48.0, 20.0, 54.0], [2.0, 40.0, 2.0], STEEL_DARK, material="metal")
    for k in range(4):
        b.box([48.0, 8.0 + k * 9.0, 54.0], [6.0 - k * 1.0, 0.5, 0.5], STEEL,
              collide=False, material="metal")
    b.sphere([48.0, 40.6, 54.0], [1.4, 1.4, 1.4], "#ff3a2a", material="neon",
             collide=False)
    # the flagpole and the camp sign in front
    b.cyl([0.0, 12.0, -6.0], [0.8, 24.0, 0.8], "#d8d8d0", material="metal")
    b.box([3.4, 21.6, -6.0], [6.0, 3.6, 0.2], "#2f5f8a", collide=False)


# ============================================================ mess hall
def _mess(b: Area, s: Surfaces, keep_out: List) -> None:
    x0, x1, z0, z1 = MESS
    s.reserve(rect(x0, x1, z0 - 8.0, z1))
    keep_out.append(rect(x0 - 10.0, x1 + 10.0, z0 - 14.0, z1 + 10.0))
    building(b, MESS, 0.0, 16.0, LOG, roof_colour=ROOF, floor_colour="#8a6a4a",
             doors={"z-": [(-176.0, -162.0, 12.0)], "x+": [(60.0, 72.0, 11.0)],
                    "z+": [(-148.0, -138.0, 10.0)]},
             windows={"z-": [(-200.0, -182.0, 4.0, 9.0), (-156.0, -138.0, 4.0, 9.0)],
                      "x-": [(52.0, 70.0, 4.0, 9.0), (82.0, 100.0, 4.0, 9.0)],
                      "x+": [(84.0, 100.0, 4.0, 9.0)]},
             glass=True, eave=1.6, lights=WARM)
    for side, span in (("z-", (-176.0, -162.0)), ("x+", (60.0, 72.0)),
                       ("z+", (-148.0, -138.0))):
        threshold(b, MESS, side, span)
    gable(b, MESS, 17.2, ROOF, "z", 4, 1.8, 0.0)
    # the long tables
    for x in (-194.0, -182.0, -154.0, -142.0):
        b.box([x, FLOOR + 1.8, 68.0], [4.0, 3.6, 34.0], WOOD_LIGHT, studs=True)
        for dx in (-3.6, 3.6):
            b.box([x + dx, FLOOR + 1.0, 68.0], [1.6, 2.0, 34.0], WOOD_DARK)
    # the kitchen counter at the back, and the stone fireplace on the west
    b.box([-169.0, FLOOR + 2.2, 100.0], [44.0, 4.4, 4.0], "#a8adb2",
          material="metal")
    supply_ammo(b, -196.0, FLOOR, 102.0, "x+")
    supply_med(b, -140.0, FLOOR, 46.0, "x-")
    b.box([x0 + 3.0, 6.0, 75.0], [4.0, 12.0, 16.0], "#8a8478")
    b.box([x0 + 3.0, 1.6, 75.0], [4.2, 3.0, 8.0], "#2a1a12", collide=False)
    b.box([x0 - 2.0, 15.0, 75.0], [6.0, 30.0, 8.0], "#8a8478")
    # the porch, and the dinner bell hung under its roof
    slab(b, rect(-188.0, -150.0, z0 - 8.0, z0), 1.2, 1.2, WOOD_LIGHT)
    for x in (-187.0, -151.0):
        b.box([x, 1.2 + 4.95, z0 - 7.2], [1.2, 9.9, 1.2], LOG_DARK)
    slab(b, rect(-189.0, -149.0, z0 - 8.0, z0), 11.7, 0.6, ROOF)
    b.box([-169.0, 10.8, z0 - 4.0], [0.4, 0.6, 0.4], STEEL_DARK, collide=False)
    b.box([-169.0, 9.4, z0 - 4.0], [3.2, 2.2, 0.4], "#c8a02a", material="metal",
          collide=False)
    b.set_lure(-169.0, 1.2, z0 - 3.0, "the dinner bell", "Ring the dinner bell",
               "dinner", (-169.0, 0.0, z0 - 20.0))
    wall_sign(b, -169.0, 13.6, z0 - 8.35, 26.0, 2.6,
              sign_decal("CEDAR PINES MESS HALL", "#5a3a22", "#f2e2a8", 10.0),
              "z-", "#5a3a22")
    b.box([-169.0, 12.75, z0 - 8.35], [1.0, 1.0, 0.7], "#5a3a22")
    # propane tanks round the back
    for x in (-196.0, -186.0):
        b.cyl([x, 2.0, z1 + 5.0], [4.0, 4.0, 8.0], "#e8e8e8", material="metal",
              r=[math.pi / 2.0, 0, 0], collide=False)
        b.box([x, 2.0, z1 + 5.0], [3.4, 4.0, 7.0], "#e8e8e8", alpha=0.0)
    barrel_spot(b, -204.0, 0.0, z1 + 8.0)
    barrel_spot(b, -134.0, 0.0, z1 + 6.0)


# ================================================================= ridge
TIERS = [rect(-268.0, -190.0, -110.0, 10.0), rect(-268.0, -202.0, -98.0, -2.0),
         rect(-268.0, -214.0, -86.0, -14.0), rect(-268.0, -226.0, -74.0, -26.0)]
TUNNEL = rect(-250.0, -190.0, -46.0, -34.0)
CHAMBER = rect(-264.0, -250.0, -58.0, -22.0)


def _ridge(b: Area, s: Surfaces, keep_out: List) -> None:
    """The overlook: four terraces of rock, stairs between them, and the
    old mine running in under the top two."""
    s.reserve(TIERS[0])
    keep_out.append(rect(-280.0, -170.0, -124.0, 24.0))
    for k, tier in enumerate(TIERS):
        holes = [TUNNEL, CHAMBER] if k < 2 else []
        plate(b, carve(tier, holes), 4.0 * (k + 1), 4.0,
              ROCK if k % 2 == 0 else "#5d5a48", studs=True)
    # the stairs between the terraces, each standing on the tier below
    flight(b, "x", -176.0, -190.0, -84.0, -76.0, 0.0, 4.0, ROCK, fill=0.0)
    flight(b, "x", -190.0, -202.0, -66.0, -58.0, 4.0, 8.0, ROCK, fill=4.0)
    flight(b, "x", -202.0, -214.0, -10.0, -2.0, 8.0, 12.0, ROCK, fill=8.0)
    flight(b, "z", -14.0, -26.0, -232.0, -226.0 + 0.0, 12.0, 16.0, ROCK,
           fill=12.0)
    flight(b, "x", -214.0, -226.0, -84.0, -78.0, 12.0, 16.0, ROCK, fill=12.0)
    # the overlook itself: a bench, a flag, a lookout scope, and ammunition
    top = 16.0
    bench(b, -246.0, -50.0, "z", y=top)
    b.cyl([-232.0, top + 1.6, -36.0], [1.0, 3.2, 1.0], STEEL_DARK)
    b.box([-232.0, top + 3.6, -36.0], [2.4, 0.8, 1.2], STEEL_DARK)
    b.cyl([-258.0, top + 9.0, -30.0], [0.6, 18.0, 0.6], "#d8d8d0")
    b.box([-255.3, top + 16.4, -30.0], [5.0, 3.0, 0.2], "#2f6b3a", collide=False)
    supply_ammo(b, -250.0, top, -70.0, "z+")
    # the cutting and the mine: timber sets, lanterns, a cart on its rails
    for x in (-246.0, -236.0, -226.0, -216.0):
        for z in (TUNNEL[2] + 0.6, TUNNEL[3] - 0.6):
            b.box([x, 4.0, z], [1.2, 8.0, 1.2], WOOD_DARK)
        b.box([x, 7.6, (TUNNEL[2] + TUNNEL[3]) / 2.0], [1.2, 0.8, 11.6],
              WOOD_DARK)
        b.box([x + 0.7, 5.6, TUNNEL[3] - 0.6], [0.2, 0.8, 0.6], "#ffb03a",
              material="neon", collide=False)
    for dz in (-2.0, 2.0):
        b.box([(TUNNEL[0] + TUNNEL[1]) / 2.0 - 4.0, 0.15, -40.0 + dz],
              [64.0, 0.3, 0.5], "#5a5f66", collide=False)
    # the ore cart, run off its rails against the chamber's back wall, so
    # the tunnel and the chamber mouth are clear for everyone
    b.box([-261.5, 2.0, -40.0], [4.0, 3.2, 6.0], "#6a4a32",
          material="metal")
    b.box([-261.5, 0.5, -40.0], [3.0, 1.0, 5.0], "#2a2d31")
    b.box([-213.5, 9.0, -40.0], [1.0, 2.0, 14.0], WOOD_DARK)
    wall_sign(b, -212.65, 10.0, -40.0, 10.0, 1.8,
              sign_decal("CEDAR No.2 MINE", "#5a3a22", "#e8d8a8", 10 / 1.8),
              "x+", "#5a3a22")
    strip_light(b, -238.0, -40.0, 8.0, 20.0, "x", "#ffb03a")
    strip_light(b, -257.0, -40.0, 8.0, 20.0, "z", "#ffb03a")
    for z in (-54.0, -26.0):
        crate(b, -260.0, 0.0, z, 4.0, WOOD)
    supply_ammo(b, -261.0, 0.0, -46.5, "x+")
    barrel_spot(b, -254.0, 0.0, -28.0)
    barrel_spot(b, -200.0, 0.0, -44.0)


# ================================================================== lake
def _lake(b: Area, s: Surfaces, keep_out: List) -> None:
    lx0, lx1, lz0, lz1 = LAKE
    keep_out.append(rect(lx0 - 6.0, lx1 + 6.0, lz0 - 6.0, lz1 + 6.0))
    # the beach: a gentle shelf of sand down into the water
    flight(b, "z", lz1 - 30.0, lz1, -60.0, 20.0, BED, 0.0, SAND, fill=BED,
           rise=0.8)
    s.lay(rect(-60.0, 20.0, lz1, lz1 + 12.0), 0.2, SAND)
    # steps up out of the water elsewhere round the shore
    for x0, x1 in ((-96.0, -86.0), (110.0, 120.0)):
        flight(b, "z", lz1 - 10.0, lz1, x0, x1, BED, 0.0, ROCK, fill=BED, rise=2.0)
    flight(b, "z", lz0 + 10.0, lz0, 0.0, 10.0, BED, 0.0, ROCK, fill=BED, rise=2.0)
    flight(b, "x", lx1 - 10.0, lx1, -200.0, -190.0, BED, 0.0, ROCK, fill=BED,
           rise=2.0)
    flight(b, "x", lx0 + 10.0, lx0, -200.0, -190.0, BED, 0.0, ROCK, fill=BED,
           rise=2.0)
    # the boathouse, half on the shore and half over the water
    bx0, bx1, bz0, bz1 = 60.0, 110.0, -150.0, -112.0
    s.reserve(rect(bx0, bx1, lz1, bz1))
    slab(b, rect(bx0, bx1, bz0, bz1), 2.0, 2.0 - BED, "#6a5a42")
    building(b, (bx0, bx1, bz0, bz1), 2.0, 10.0, "#8a3a2a", roof_colour="#3a3a3a",
             floor_colour="", doors={"z+": [(78.0, 92.0, 10.6)],
                                      "z-": [(66.0, 104.0, 10.0)]},
             windows={"x-": [(-140.0, -122.0, 5.6, 9.6)],
                      "x+": [(-140.0, -122.0, 5.6, 9.6)]}, glass=True,
             lights=WARM, eave=1.0)
    gable(b, (bx0, bx1, bz0, bz1), 13.2, "#3a3a3a", "z", 3, 1.4, 0.0)
    for x in (70.0, 84.0, 98.0):
        b.box([x, 3.0, -138.0], [4.0, 2.0, 18.0], "#c84a2a" if x != 84.0 else "#2f6b8a",
              studs=True)
    supply_ammo(b, 104.0, 2.0, -118.0, "x-")
    wall_sign(b, 85.0, 11.0, bz1 + 0.35, 18.0, 1.6,
              sign_decal("BOATHOUSE", "#8a3a2a", "#f2e2a8", 11.0), "z+", "#8a3a2a")
    # the dock out into the lake, and the boats tied to it
    slab(b, rect(78.0, 92.0, -214.0, bz0), 2.0, 1.0, WOOD_LIGHT, studs=True)
    for z in (-160.0, -180.0, -200.0, -212.0):
        for x in (79.0, 91.0):
            b.cyl([x, (BED + 1.0) / 2.0, z], [1.6, 1.0 - BED, 1.6], WOOD_DARK)
    boat(b, 104.0, -186.0, "z", 22.0, "#d8d8d0", deck=1.0, cabin=False)
    boat(b, 66.0, -196.0, "z", 18.0, "#c84a2a", deck=1.0, cabin=False)
    lamp_post(b, 85.0, -212.0, 8.0, y=2.0)
    barrel_spot(b, 88.0, 2.0, -160.0)
    # the swimming raft
    slab(b, rect(-30.0, -14.0, -210.0, -194.0), 0.8, 0.8, WOOD_LIGHT, studs=True)
    for x in (-29.0, -15.0):
        for z in (-209.0, -195.0):
            b.box([x, (BED + 0.0) / 2.0, z], [1.2, -BED, 1.2], WOOD_DARK)
    b.box([-15.0, 2.8, -202.0], [1.0, 4.0, 1.0], STEEL)
    b.box([-17.5, 4.95, -202.0], [6.0, 0.3, 2.0], WOOD_LIGHT)
    # the island: a mound of rock with two pines on it
    slab(b, rect(26.0, 56.0, -230.0, -200.0), 1.0, 1.0 - BED, ROCK, studs=True)
    slab(b, rect(32.0, 50.0, -224.0, -206.0), 2.6, 1.6, GRASS_DARK, studs=True,
         material="grass")
    b.pine(36.0, -210.0, 2.6, 1.5, WOOD_DARK, "#2a4a2a")
    b.pine(46.0, -220.0, 2.6, 1.2, WOOD_DARK, "#2a4a2a")
    crate(b, 44.0, 2.6, -209.0, 3.0, WOOD)


# ================================================================= shore
def _shore(b: Area, s: Surfaces, keep_out: List, rng: random.Random) -> None:
    # the amphitheatre: a stage, a fire pit, rows of log benches
    keep_out.append(rect(40.0, 100.0, -104.0, -40.0))
    slab(b, rect(56.0, 84.0, -100.0, -86.0), 1.6, 1.6, WOOD_LIGHT, studs=True)
    for x in (57.0, 83.0):
        b.box([x, 1.6 + 5.0, -99.0], [1.2, 10.0, 1.2], LOG_DARK)
    slab(b, rect(55.0, 85.0, -101.0, -94.0), 12.2, 0.6, ROOF)
    b.cyl([70.0, 0.6, -76.0], [8.0, 1.2, 8.0], "#6a6460")
    b.cone([70.0, 2.4, -76.0], [3.6, 3.0, 3.6], "#ff8a2a", material="neon",
           collide=False)
    for row, z in enumerate((-66.0, -58.0, -50.0)):
        for x in (52.0, 70.0, 88.0):
            b.box([x, 1.0, z], [12.0 + row * 2.0, 2.0, 2.4], LOG_DARK)
    # the volleyball court on the sand by the beach
    s.lay(rect(-60.0, 0.0, -112.0, -84.0), 0.3, SAND)
    keep_out.append(rect(-66.0, 6.0, -118.0, -78.0))
    for x in (-58.0, -2.0):
        b.box([x, 0.3 + 4.5, -98.0], [0.8, 9.0, 0.8], "#d8d8d0")
    b.box([-30.0, 6.3, -98.0], [55.2, 3.0, 0.3], "#e8e8e8", alpha=0.5)
    # the camp's shore path lamps
    for x in (-80.0, -20.0, 40.0, 120.0):
        lamp_post(b, x, -112.0, 10.0, colour=LOG_DARK, light=WARM)
    # the creek: two footbridges and the banks either side of them
    for z in (-40.0, 66.0):
        slab(b, rect(-124.0, -100.0, z - 5.0, z + 5.0), 1.6, 1.0, WOOD_LIGHT,
             studs=True)
        for x0, x1 in ((-124.0, -118.0), (-106.0, -100.0)):
            slab(b, rect(x0, x1, z - 5.0, z + 5.0), 0.6, 0.6, WOOD_DARK)
        for z_edge in (z - 4.6, z + 4.6):
            b.box([-112.0, 3.0, z_edge], [24.0, 2.8, 0.8], WOOD_DARK)
        keep_out.append(rect(-130.0, -94.0, z - 10.0, z + 10.0))
    keep_out.append(rect(-124.0, -100.0, -130.0, 156.0))


# ================================================================ cabins
def _cabins(b: Area, s: Surfaces, keep_out: List, rng: random.Random) -> None:
    clusters = [
        ((-206.0, 198.0), [(rect(-262.0, -238.0, 186.0, 206.0), "x+"),
                           (rect(-262.0, -238.0, 222.0, 242.0), "x+"),
                           (rect(-218.0, -194.0, 236.0, 256.0), "z-"),
                           (rect(-174.0, -150.0, 222.0, 242.0), "x-"),
                           (rect(-174.0, -150.0, 160.0, 180.0), "x-"),
                           (rect(-218.0, -194.0, 140.0, 160.0), "z+")]),
        ((200.0, 198.0), [(rect(238.0, 262.0, 186.0, 206.0), "x-"),
                          (rect(238.0, 262.0, 222.0, 242.0), "x-"),
                          (rect(188.0, 212.0, 236.0, 256.0), "z-"),
                          (rect(144.0, 168.0, 222.0, 242.0), "x+"),
                          (rect(144.0, 168.0, 160.0, 180.0), "x+")]),
    ]
    colours = [LOG, "#8a6040", "#6a4a30", "#7a5a3a"]
    roofs = [ROOF, "#5a3a2a", "#3a4a3a"]
    for (cx, cz), cabins in clusters:
        keep_out.append(rect(cx - 64.0, cx + 64.0, cz - 64.0, cz + 64.0))
        for i, (area, facing) in enumerate(cabins):
            house(b, area, facing, colours[i % len(colours)], roofs[i % len(roofs)],
                  height=11.0, enterable=i % 3 != 2, rng=rng, door_w=7.0,
                  porch_depth=5.0, trim=LOG_DARK)
        # the firepit in the middle, and logs round it
        b.cyl([cx, 0.6, cz], [9.0, 1.2, 9.0], "#6a6460")
        b.cone([cx, 2.4, cz], [4.0, 3.0, 4.0], "#ff8a2a", material="neon",
               collide=False)
        for dx, dz, along in ((-11.0, 0.0, "z"), (11.0, 0.0, "z"), (0.0, -11.0, "x"),
                              (0.0, 11.0, "x")):
            w, d = (2.4, 10.0) if along == "z" else (10.0, 2.4)
            b.box([cx + dx, 1.0, cz + dz], [w, 2.0, d], LOG_DARK)
        lamp_post(b, cx + 18.0, cz - 18.0, 10.0, colour=LOG_DARK, light=WARM)
    supply_med(b, -256.0, FLOOR, 238.0, "x+")
    supply_med(b, 256.0, FLOOR, 238.0, "x-")
    # the bathhouse between the station and the west cabins
    area = (-70.0, -30.0, 120.0, 150.0)
    s.reserve(rect(*area))
    keep_out.append(rect(-80.0, -20.0, 110.0, 160.0))
    building(b, area, 0.0, 10.0, "#c8c0b0", roof_colour="#5a5a52",
             floor_colour="#d8d8d0", doors={"z-": [(-56.0, -44.0, 9.0)]},
             windows={"z+": [(-66.0, -34.0, 7.0, 9.0)]}, glass=True, lights=COLD)
    threshold(b, area, "z-", (-56.0, -44.0))
    holed_wall(b, "z", -50.0, 1.0, 122.0 + 8.0, 148.0, FLOOR, 10.0, "#d8d8d0")
    supply_med(b, -64.0, FLOOR, 144.0, "x+")
    wall_sign(b, -50.0, 9.2, 119.65, 12.0, 1.4,
              sign_decal("SHOWERS", "#c8c0b0", "#2a4a6a", 12 / 1.4), "z-", "#c8c0b0")
    # the fire lookout, north of the station
    keep_out.append(rect(40.0, 80.0, 100.0, 170.0))
    watchtower(b, 60.0, 156.0, 30.0, LOG_DARK, "z-")
    supply_ammo(b, 58.0, 30.8, 158.0, "z-")


# ================================================================== east
def _east(b: Area, s: Surfaces, keep_out: List, rng: random.Random) -> None:
    # the car park, the RV and the road out through the gate
    s.lay(rect(100.0, 200.0, 62.0, 112.0), 0.25, "#8a7a62")
    s.lay(rect(200.0, HALF, 80.0, 94.0), 0.25, DIRT)
    keep_out.append(rect(94.0, 280.0, 56.0, 118.0))
    van(b, 126.0, 74.0, "x", "#e8e2d0", "#7a5a3a", 30.0, y=0.25)
    car(b, 160.0, 72.0, "z", "#6a3a2a", y=0.25)
    car(b, 176.0, 72.0, "z", "#3a5a6a", y=0.25)
    car(b, 150.0, 100.0, "x", "#2a2a2a", wrecked=True, y=0.25)
    car(b, 120.0, 102.0, "x", "#c8a83a", y=0.25)
    barrel_spot(b, 140.0, 0.25, 86.0)
    supply_ammo(b, 106.0, 0.25, 92.0, "x+")
    # the gate: two log posts, the beam and the sign
    for z in (77.0, 97.0):
        b.box([230.0, 9.0, z], [2.4, 18.0, 2.4], LOG_DARK)
    b.box([230.0, 18.9, 87.0], [2.6, 1.8, 24.0], LOG_DARK)
    wall_sign(b, 231.65, 16.0, 87.0, 18.0, 3.0,
              sign_decal("CEDAR PINES CAMP", "#5a3a22", "#f2e2a8", 6.0), "x+",
              "#5a3a22")
    # the archery range
    keep_out.append(rect(146.0, 266.0, -64.0, 34.0))
    for z in (-40.0, -20.0, 0.0, 20.0):
        b.cyl([252.0, 5.0, z], [8.0, 8.0, 1.4], "#d8c87a", r=[math.pi / 2.0, 0, 0],
              collide=False)
        b.box([252.0, 5.0, z], [6.4, 8.0, 1.2], "#d8c87a", alpha=0.0)
        b.box([252.0, 1.0, z - 1.4], [1.0, 2.0, 1.0], WOOD_DARK)
        b.box([252.0, 1.0, z + 1.4], [1.0, 2.0, 1.0], WOOD_DARK)
    for z in (-50.0, 30.0):
        b.box([160.0, 5.0, z], [1.2, 10.0, 1.2], LOG_DARK)
    slab(b, rect(156.0, 164.0, -54.0, 34.0), 10.6, 0.6, ROOF)
    b.box([160.0, 5.0, -10.0], [1.2, 10.0, 1.2], LOG_DARK)
    for z in (-30.0, 10.0):
        b.box([166.0, 1.5, z], [2.0, 3.0, 12.0], WOOD_LIGHT)
    barrel_spot(b, 170.0, 0.0, -56.0)
    # a supply shed by the range
    area = (176.0, 200.0, -110.0, -90.0)
    s.reserve(rect(*area))
    keep_out.append(rect(170.0, 206.0, -116.0, -84.0))
    building(b, area, 0.0, 9.0, LOG, roof_colour=ROOF, floor_colour="#8a6a4a",
             doors={"z+": [(184.0, 192.0, 8.0)]}, boards=True, lights=WARM)
    threshold(b, area, "z+", (184.0, 192.0))
    gable(b, area, 10.2, ROOF, "x", 2, 1.4, 0.0)
    for x in (180.0, 196.0):
        crate(b, x, FLOOR, -106.0, 4.0, WOOD)


def _trails(b: Area, s: Surfaces) -> None:
    """Dirt paths joining the places people walk between."""
    for area in (rect(-6.0, 6.0, -112.0, 3.0),       # station to the beach
                 rect(-96.0, -40.0, 30.0, 40.0),     # station to the mess
                 rect(-100.0, -94.0, -40.0, 71.0),   # the creek-side path
                 rect(40.0, 100.0, 30.0, 40.0),      # station to the car park
                 rect(-6.0, 6.0, 60.0, 196.0),       # station to the north
                 rect(-150.0, 144.0, 192.0, 202.0),  # between the two circles
                 rect(6.0, 60.0, -46.0, -36.0)):     # to the amphitheatre
        s.lay(area, 0.12, DIRT)


def _forest(b: Area, rng: random.Random, keep_out: List) -> None:
    """Pines everywhere nothing else is; their trunks are solid."""
    H = HALF

    def clear(x: float, z: float, pad: float = 6.0) -> bool:
        return not any(r[0] - pad < x < r[1] + pad and r[2] - pad < z < r[3] + pad
                       for r in keep_out)

    placed = 0
    tries = 0
    while placed < 150 and tries < 4000:
        tries += 1
        x = rng.uniform(-H + 10.0, H - 10.0)
        z = rng.uniform(-H + 10.0, H - 10.0)
        if not clear(x, z):
            continue
        # thinner in the middle of the camp, thick towards the edges
        edge = max(abs(x), abs(z)) / H
        if rng.random() > 0.25 + edge * 0.9:
            continue
        keep_out.append(rect(x - 4.0, x + 4.0, z - 4.0, z + 4.0))
        roll = rng.random()
        if roll < 0.78:
            b.pine(x, z, 0.0, rng.uniform(1.1, 1.8), WOOD_DARK,
                   rng.choice(["#2a4a2a", "#24402a", "#30502e"]))
        elif roll < 0.92:
            b.tree(x, z, 0.0, rng.uniform(1.0, 1.4), LOG,
                   rng.choice(["#3f6b2f", "#4a7a2f"]))
        else:
            b.rock(x, z, 0.0, rng.uniform(1.0, 2.0), "#6b6a62")
        placed += 1


def _zombie_spawns(b: Area) -> None:
    pts = [
        # the treeline all round
        (-250, 272), (-160, 272), (-80, 272), (0, 272), (80, 272), (160, 272),
        (250, 272), (-272, 120), (-272, 60), (272, 220), (272, 150), (272, 40),
        (272, -40), (272, -120), (272, -200), (-272, -160), (-272, -250),
        # the far shore and the water
        (-200, -272), (-60, -272), (60, -272), (200, -272), (-80, -236),
        (110, -246), (-100, -150),
        # the mine
        (-258, -30), (-258, -52), (-244, -40),
        # behind the cabins and the mess hall
        (-150, 270), (-185, 124), (150, 120),
    ]
    for x, z in pts:
        tag = ""
        if LAKE[0] < x < LAKE[1] and LAKE[2] < z < LAKE[3]:
            tag = "water"
        elif CHAMBER[0] - 2 < x < TUNNEL[1] and CHAMBER[2] - 2 < z < CHAMBER[3] + 2:
            tag = "mine"
        y = BED if tag == "water" else (0.0 if tag == "mine" else None)
        b.zombie_spawn(float(x), float(z), tag, y=y)
