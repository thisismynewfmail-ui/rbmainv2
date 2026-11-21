"""Harrow County Fair -- the last night of the fair, the lights just on.

Layout (north is +z)::

   z +280 ------------------------ the tree line --------------------------
          THE CORN MAZE        hay        THE FERRIS WHEEL      GRAIN
          (a lookout bridge    pyramid                          ELEVATOR
           in the middle)
   z +120 ================ THE MIDWAY: booths both sides =================
          LIVESTOCK BARNS      THE EXHIBITION HALL (safe room)   CAROUSEL
          (the prize bull)     the giant pumpkin                 HAUNTED HOUSE
   z  -60 ======================= the main path ============================
          the fair gate        THE DEMOLITION DERBY PIT          SWING RIDE
          the parking field    THE GRANDSTAND (the lure on top)  tractor pull
   z -280 ======================= the county road ==========================

Everybody deploys in the Exhibition Hall, among the quilts and the pies.

What makes it this place:

* **The rides.**  The Ferris wheel turns over the north end, lit; the
  carousel's horses go round and the swing ride's chairs fly out -- nobody
  on them.  You can stand on the carousel's floor while the horses go by.
* **The corn maze.**  A real maze, the walls of corn taller than a man,
  and the infected come out of it.  In the middle a lookout bridge stands
  over the corn; from up there you can see which way they are coming.
* **High ground.**  The grandstand's steps, the hay bale pyramid and the
  gallery on top of the grain elevator, the highest thing for miles.
* **The derby.**  The lure is the grandstand's announcer: start the
  demolition derby -- engines, horns, the crowd -- and the horde goes down
  into the mud pit among the wrecks, under the whole grandstand.
"""
from __future__ import annotations

import math
import random
from typing import Dict, List, Set, Tuple

from .kit import (
    ASPHALT, CONCRETE, CONCRETE_DARK, FLOOR, GLASS, LAMP, STEEL, STEEL_DARK, WARM, WOOD,
    WOOD_DARK, WOOD_LIGHT, Area, Surfaces, barrel_spot, bench, boundary, building, car, carve,
    crate, deploy_pad, flight, holed_wall, lamp_post, plate, post_sign, rect, room_walls,
    sign_decal, slab, solid_fence, strip_light, supply_ammo, supply_med, threshold, van,
    wall_sign)
from ..relay.kit import board_letters, boulder, mound, pine, tier_stack, tree

Rect = Tuple[float, float, float, float]

HALF = 280.0
SKY = {"top": "#2a2a5a", "horizon": "#e8885a", "sun": [-0.5, 0.12, -0.7],
       "clouds": 0.4, "tint": "#ffc898"}
AMBIENT = "#7a6a72"

GRASS = "#5a7a38"
DIRT = "#8a6a48"
MUD = "#5a4430"
PATH = "#b89a6a"
CORN = "#7a8a2a"
RED = "#c43a32"
WHITE = "#f2ece0"

HALL = (-40.0, 40.0, -20.0, 40.0)
HALL_H = 13.0
HALL_HOLE = (22.0, 38.0, -18.0, -10.0)
PIT = (-100.0, 100.0, -196.0, -130.0)
PIT_FLOOR = -3.0
STAND_Z = -200.0                     # the grandstand's front, its steps go back from here
BOOTH = (-12.0, 12.0, -248.0, -236.0)
BOOTH_Y = 12.0
MIDWAY = (-110.0, 262.0, 110.0, 130.0)
MAIN = (-262.0, 262.0, -76.0, -60.0)
SPINE = (-12.0, 12.0, -60.0, 110.0)
FERRIS = (0.0, 214.0)
FERRIS_R = 34.0
FERRIS_AXLE = 42.0
CAROUSEL = (176.0, 60.0)
SWINGS = (230.0, -150.0)
HAUNT = (150.0, 230.0, -48.0, 10.0)
BARN_A = (-262.0, -150.0, -46.0, 8.0)
BARN_B = (-262.0, -150.0, 26.0, 80.0)
MAZE_X0, MAZE_Z0, CELL, CELLS = -270.0, 142.0, 12.0, 11
TOWER_CELL = (5, 5)
HAY = (-80.0, 170.0)
SILOS = [(214.0, 236.0), (232.0, 236.0), (250.0, 236.0)]
SILO_H = 23.2
GALLERY = (206.0, 258.0, 228.0, 244.0)
PUMPKIN = (64.0, 100.0, -50.0, -26.0)
GATE = (-200.0, -150.0, -262.0, -254.0)
PULL = (120.0, 262.0, -250.0, -206.0)
PIGRACE = (54.0, 106.0, 30.0, 70.0)     # the pig races' track, out to its fence
PIG_ISLAND = (66.0, 94.0, 42.0, 58.0)
TOILETS = (-104.0, -80.0, 88.0, 94.0)


def build(b: Area) -> None:
    rng = random.Random(0xFA12)
    b.extra.update({"weather": "motes", "accent": "#ff8a5a"})
    s = Surfaces(b)
    _ground(b, s)
    boundary(b, 30.0, "#2e3a24", "#24301c", rng, horizon="forest")
    _hall(b, s)
    _derby(b, s)
    _midway(b, s, rng)
    _rides(b, s)
    _haunt(b, s)
    _barns(b, s, rng)
    _maze(b, s, rng)
    _elevator(b, s)
    _pumpkin(b, s)
    _pig_race(b, s)
    _sundries(b, s)
    _gate(b, s, rng)
    _country(b, s, rng)
    _paths(b, s)
    _rigs(b)
    _zombie_spawns(b, rng)
    for x, z, name in ((0, 10, "the exhibition hall"), (0, -224, "the grandstand"),
                       (0, -163, "the derby pit"), (80, 120, "the midway"),
                       (0, 214, "the ferris wheel"), (176, 60, "the carousel"),
                       (230, -150, "the swing ride"), (190, -20, "the haunted house"),
                       (-206, -19, "the cattle barn"), (-206, 53, "the hog barn"),
                       (-204, 206, "the corn maze"), (-80, 170, "the hay pyramid"),
                       (232, 214, "the grain elevator"), (82, -38, "the giant pumpkin"),
                       (-175, -240, "the fair gate"), (190, -228, "the tractor pull"),
                       (80, 50, "the pig races")):
        b.landmark(float(x), float(z), name)
    b.camera(0.0, 60.0, -150.0, 0.0, 20.0, 120.0)
    b.camera(-120.0, 40.0, 120.0, -204.0, 4.0, 206.0)
    b.camera(24.0, 24.0, -238.0, 0.0, -2.0, -160.0)
    b.camera(130.0, 22.0, 84.0, 176.0, 6.0, 60.0)
    b.camera(40.0, 18.0, 20.0, 84.0, 2.0, 52.0)


# ================================================================ ground
def _ground(b: Area, s: Surfaces) -> None:
    h = b.half + b.margin
    s.reserve(PIT)
    pieces = carve(rect(-h, h, -h, h), [PIT])
    plate(b, pieces, 0.0, 0.6, GRASS, studs=True, material="grass")
    plate(b, pieces, -0.6, 5.4, "#5a4a34")


def _paths(b: Area, s: Surfaces) -> None:
    for r in (MIDWAY, MAIN, SPINE, rect(-150.0, -110.0, 112.0, 128.0),
              rect(-262.0, -100.0, -76.0, -60.0), rect(-185.0, -165.0, -254.0, -76.0),
              rect(100.0, 116.0, -196.0, -76.0), rect(-12.0, 12.0, 130.0, 188.0),
              rect(-216.0, -150.0, 112.0, 128.0)):
        s.lay(r, 0.3, PATH, studs=True)
    s.lay(PULL, 0.4, DIRT, studs=True)
    s.lay(rect(-280.0, 280.0, -280.0, -266.0), 0.3, ASPHALT)


# ===================================================== exhibition hall
def _hall(b: Area, s: Surfaces) -> None:
    x0, x1, z0, z1 = HALL
    s.reserve(HALL)
    head = 10.0
    building(b, HALL, 0.0, HALL_H, WHITE, roof_colour=RED, floor_colour="#c8b090",
             doors={"z+": [(-8.0, 8.0, head)], "z-": [(-8.0, 8.0, head)],
                    "x-": [(4.0, 16.0, head)], "x+": [(4.0, 16.0, head)]},
             windows={"z+": [(-34.0, -14.0, 3.6, 8.4), (14.0, 34.0, 3.6, 8.4)],
                      "z-": [(-34.0, -14.0, 3.6, 8.4)]},
             glass=True, roof_holes=[HALL_HOLE], parapet=3.0, lights=WARM)
    for side in ("z+", "z-"):
        threshold(b, HALL, side, (-8.0, 8.0))
    for side in ("x-", "x+"):
        threshold(b, HALL, side, (4.0, 16.0))
    wall_sign(b, 0.0, 11.6, z1 + 0.5, 28.0, 2.4,
              sign_decal("EXHIBITION HALL  HOME ARTS", RED, "#f2ece0", 11.7), "z+", RED)
    floor = FLOOR
    for z in (28.0, 18.0):
        for x in (-34.0, -25.0, -16.0, -7.0, 7.0, 16.0, 25.0, 34.0):
            deploy_pad(b, x, z, floor, "#ff8a5a", 5.0)
            b.safe_spawn(x, floor + 0.6, z, math.pi)
    # quilts on the walls, the pie tables, the blue ribbons
    quilts = ["#c43a5a", "#3a7ac8", "#e8b83a", "#5aa86a", "#9a5ac8", "#e8783a"]
    for k in range(6):
        qx = -32.0 + k * 13.0
        if -10.0 < qx < 10.0:
            continue
        b.box([qx, 7.0, z0 + 2.06], [8.0, 6.0, 0.12], quilts[k], collide=False)
    for (tx, tz) in ((-24.0, 0.0), (0.0, 0.0), (24.0, 0.0)):
        b.box([tx, floor + 1.6, tz], [14.0, 0.4, 5.0], WHITE)
        b.box([tx, floor + 0.7, tz], [12.0, 1.4, 3.0], WOOD_DARK)
        for j in range(4):
            b.cyl([tx - 4.5 + j * 3.0, floor + 2.2, tz], [2.2, 0.8, 2.2], "#d8a050")
    flight(b, "x", 12.0, 38.0, -18.0, -10.0, floor, HALL_H + 1.2, CONCRETE_DARK, fill=floor)
    supply_ammo(b, -30.0, floor, -14.0, "z+")
    supply_med(b, -34.0, floor, 8.0, "x+")
    roof = HALL_H + 1.2
    for (xa, xb, za, zb) in ((HALL_HOLE[0], HALL_HOLE[1], HALL_HOLE[3], HALL_HOLE[3] + 0.6),
                             (HALL_HOLE[0] - 0.6, HALL_HOLE[0], HALL_HOLE[2], HALL_HOLE[3] + 0.6)):
        b.box([(xa + xb) / 2.0, roof + 1.6, (za + zb) / 2.0], [xb - xa, 3.2, zb - za], STEEL,
              material="metal")
    supply_ammo(b, -28.0, roof, 26.0, "z-")
    barrel_spot(b, 48.0, 0.0, -14.0)


# ================================================================ derby
def _derby(b: Area, s: Surfaces) -> None:
    """The demolition derby pit: mud, concrete walls, the wrecks; the
    grandstand's steps up behind it, its roof, the announcer on top."""
    x0, x1, z0, z1 = PIT
    slab(b, PIT, PIT_FLOOR, 3.0, MUD, studs=True)
    for (a, c, d, e) in ((x0, x1, z1 - 1.0, z1), (x0, x0 + 1.0, z0, z1 - 1.0),
                         (x1 - 1.0, x1, z0, z1 - 1.0)):
        b.box([(a + c) / 2.0, (PIT_FLOOR + 1.0) / 2.0, (d + e) / 2.0], [c - a, 1.0 - PIT_FLOOR, e - d],
              CONCRETE, studs=True)
    for (cx, cz, along, colour, number) in ((-60.0, -150.0, "x", "#3a7ac8", 13),
                                            (-20.0, -176.0, "z", "#e8c83a", 7),
                                            (30.0, -146.0, "x", "#c43a32", 66),
                                            (64.0, -180.0, "z", "#5aa86a", 22),
                                            (-74.0, -184.0, "z", "#f2ece0", 99),
                                            (8.0, -160.0, "x", "#e890b0", 8)):
        _derby_car(b, cx, cz, along, colour, number, PIT_FLOOR)
    for (tx, tz) in ((-90.0, -140.0), (90.0, -140.0), (-90.0, -188.0), (90.0, -188.0)):
        for k in range(3):
            b.cyl([tx, PIT_FLOOR + 0.6 + k * 1.2, tz], [4.0, 1.2, 4.0], "#1b1d20")
    barrel_spot(b, -40.0, PIT_FLOOR, -136.0)
    barrel_spot(b, 50.0, PIT_FLOOR, -190.0)
    # the steps of the grandstand, rising south from the pit's rim
    s.reserve(rect(x0 - 8.0, x1 + 8.0, -250.0, z0))
    tiers = []
    for k in range(8):
        tiers.append([rect(x0, x1, STAND_Z - 4.0 * (k + 1) - (18.0 if k == 7 else 0.0),
                           STAND_Z - 4.0 * k)])
    for k in range(8):
        slab(b, tiers[k][0], 1.5 * (k + 1), 1.5 * (k + 1), ["#e8e2d4", "#c43a32"][k % 2], studs=True)
    top = 12.0
    for x in (x0 - 0.4, x1 + 0.4):
        b.box([x, top / 2.0 + 1.0, STAND_Z - 25.0], [0.8, top + 2.0, 50.0], "#5a5f66")
    # its roof on posts
    for x in (-96.0, -48.0, 0.0, 48.0, 96.0):
        b.box([x, (top + 26.0) / 2.0, -244.0], [1.2, 26.0 - top, 1.2], "#5a5f66", material="metal")
        b.box([x, (6.0 + 26.0) / 2.0, -214.0], [1.0, 26.0 - 6.0, 1.0], "#5a5f66", material="metal")
    slab(b, rect(x0 - 2.0, x1 + 2.0, -248.0, -210.0), 26.6, 0.6, RED)
    # the announcer's booth on top, the lure's desk in it
    building(b, BOOTH, BOOTH_Y, 8.0, WHITE, roof_colour=RED, floor_colour="#8a7a6a",
             doors={"z+": [(-4.0, 4.0, BOOTH_Y + 6.8)]},
             windows={"z+": [(-11.0, -5.0, BOOTH_Y + 3.0, BOOTH_Y + 6.6),
                             (5.0, 11.0, BOOTH_Y + 3.0, BOOTH_Y + 6.6)]}, glass=True, lights=WARM)
    threshold(b, BOOTH, "z+", (-4.0, 4.0), y0=BOOTH_Y)
    b.box([0.0, BOOTH_Y + FLOOR + 1.6, -244.4], [14.0, 3.2, 3.0], "#5a5f66")
    b.set_lure(0.0, BOOTH_Y + FLOOR, -242.0, "the demolition derby", "Start the demolition derby",
               "ll_derby", (0.0, PIT_FLOOR, -163.0))
    supply_ammo(b, 30.0, top, -244.0, "z+")
    barrel_spot(b, -60.0, top, -244.0)
    wall_sign(b, 0.0, 27.8, -209.6, 40.0, 2.4, sign_decal("DEMOLITION DERBY  TONITE", RED, "#f2ece0",
                                                         16.7), "z+", RED)


# ================================================================ midway
def _midway(b: Area, s: Surfaces, rng: random.Random) -> None:
    """Booths both sides of the midway: an awning, a counter, the prizes
    -- and the games: the ducks, ring toss, the strength tester, the
    dunk tank; a first aid tent at the end."""
    names = ["RING TOSS", "DUCK SHOOT", "BALLOON DARTS", "CORN DOGS", "LEMONADE", "GUESS YOUR WEIGHT",
             "HOOP SHOT", "FUNNEL CAKE"]
    stripes = [RED, "#3a7ac8", "#e8b83a", "#5aa86a"]
    for k in range(8):
        x = -86.0 + k * 40.0
        if k == 2:
            continue                      # the way through to the wheel and the hall
        for side, zz in ((1, MIDWAY[3]), (-1, MIDWAY[2])):
            if side < 0 and k == 6:
                continue
            z0, z1 = (zz, zz + 12.0) if side > 0 else (zz - 12.0, zz)
            r = rect(x - 10.0, x + 10.0, z0, z1)
            s.reserve(r)
            back = z1 - 0.5 if side > 0 else z0 + 0.5
            front = z0 + 1.6 if side > 0 else z1 - 1.6
            b.box([x, 4.5, back], [18.4, 9.0, 1.0], stripes[(k + (side > 0)) % 4])
            for xx in (x - 9.6, x + 9.6):
                b.box([xx, 4.5, (z0 + z1) / 2.0], [0.8, 9.0, 11.0], WHITE)
            b.box([x, 1.6, front], [18.4, 3.2, 1.6], WOOD, studs=True)
            slab(b, rect(x - 10.6, x + 10.6, z0 - (2.0 if side > 0 else 0.0),
                         z1 + (0.0 if side > 0 else 2.0)), 9.6, 0.6, stripes[(k + 1) % 4])
            wall_sign(b, x, 10.5, front - side * 1.25, 16.0, 1.8,
                      sign_decal(names[(k + (side < 0) * 3) % 8], "#f2ece0", RED, 8.9),
                      "z-" if side > 0 else "z+", "#f2ece0")
            if side > 0 and k == 1:
                continue                  # the duck shoot's ducks run along its back
            for j in range(4):
                b.box([x - 6.0 + j * 4.0, 6.0, back - side * 1.2], [2.0, 2.0, 1.4],
                      ["#e890b0", "#f2d83a", "#8ad8e8", "#c8a070"][j])
    # the strength tester and its bell, the dunk tank
    sx, sz = 14.0, 102.0
    b.box([sx, 0.3 + 1.0, sz], [5.0, 2.0, 5.0], "#5a5f66")
    b.box([sx, 0.3 + 12.0, sz], [1.2, 20.0, 1.2], RED)
    b.cyl([sx, 0.3 + 22.6, sz], [3.0, 1.2, 3.0], "#e8c83a", material="metal")
    dx, dz = -62.0, 104.0
    b.box([dx, 0.3 + 2.4, dz], [10.0, 4.8, 8.0], "#3a7ac8")
    b.box([dx, 0.3 + 4.85, dz], [9.0, 0.1, 7.0], "#5ab8e8", material="glass", alpha=0.7, collide=False)
    b.box([dx, 0.3 + 10.0, dz + 3.4], [8.0, 10.0, 1.0], "#e8e8e8")
    supply_ammo(b, -46.0, 0.3, 124.0, "z+")
    barrel_spot(b, 100.0, 0.0, 104.0)
    # the first aid tent at the east end
    tent = rect(224.0, 252.0, 92.0, 108.0)
    s.reserve(tent)
    building(b, tent, 0.0, 9.0, WHITE, t=0.8, roof_colour=WHITE, roof_t=0.6, floor_colour="#8a8a7a",
             doors={"z+": [(234.0, 242.0, 7.6)]}, lights=WARM)
    threshold(b, tent, "z+", (234.0, 242.0), t=0.8)
    supply_med(b, 238.0, FLOOR, 96.6, "z+")
    wall_sign(b, 238.0, 8.0, 108.45, 10.0, 2.0, sign_decal("FIRST AID", WHITE, RED, 5.0), "z+", WHITE)


# ================================================================ rides
def _rides(b: Area, s: Surfaces) -> None:
    """The Ferris wheel's towers and loading deck, the carousel's floor and
    pole, the swing ride's mast: the turning parts are rigs."""
    fx, fz = FERRIS
    s.reserve(rect(fx - 30.0, fx + 30.0, fz - 16.0, fz + 16.0))
    for dx in (-12.0, 12.0):
        for dz in (-6.0, 6.0):
            b.box([fx + dx * 0.4, FERRIS_AXLE / 2.0, fz + dz], [2.0, FERRIS_AXLE, 2.0], "#e8e8e8",
                  material="metal")
        b.box([fx + dx * 1.6, 3.0, fz], [2.0, 6.0, 14.0], "#e8e8e8")
    b.box([fx, FERRIS_AXLE, fz], [11.0, 3.0, 13.0], "#e8e8e8", material="metal")
    slab(b, rect(fx - 10.0, fx + 10.0, fz - 16.0, fz - 7.0), 2.0, 2.0, WOOD, studs=True)
    flight(b, "z", fz - 26.0, fz - 16.0, fx - 6.0, fx + 6.0, 0.0, 2.0, WOOD_DARK, fill=0.0)
    wall_sign(b, fx, 9.0, fz - 7.35, 22.0, 2.6, sign_decal("SKY WHEEL", "#f2ece0", RED, 8.5), "z-",
              "#f2ece0")
    # the carousel: a floor you can stand on, the pole, the canopy above
    cx, cz = CAROUSEL
    s.reserve(rect(cx - 18.0, cx + 18.0, cz - 18.0, cz + 18.0))
    b.cyl([cx, 0.6, cz], [34.0, 1.2, 34.0], "#c8a060")
    b.cyl([cx, 8.4, cz], [5.0, 14.4, 5.0], "#e8c83a", material="metal")
    barrel_spot(b, cx + 22.0, 0.0, cz - 16.0)
    # the swing ride's mast
    wx, wz = SWINGS
    s.reserve(rect(wx - 6.0, wx + 6.0, wz - 6.0, wz + 6.0))
    b.box([wx, 1.0, wz], [10.0, 2.0, 10.0], "#5a5f66")
    b.cyl([wx, 2.0 + 15.0, wz], [3.0, 30.0, 3.0], "#e8e8e8", material="metal")


# ======================================================== haunted house
def _haunt(b: Area, s: Surfaces) -> None:
    """A dark ride: in through the monster's mouth, round a dark winding
    track past the coffin and the skeletons, out the back."""
    x0, x1, z0, z1 = HAUNT
    s.reserve(HAUNT)
    building(b, HAUNT, 0.0, 16.0, "#3a2a3a", roof_colour="#1a141a", floor_colour="#1a1a1e",
             doors={"x-": [(-30.0, -18.0, 11.0)], "x+": [(-10.0, 2.0, 9.0)]}, lights="#8a3ac8")
    threshold(b, HAUNT, "x-", (-30.0, -18.0))
    threshold(b, HAUNT, "x+", (-10.0, 2.0))
    # partitions make the track wind
    holed_wall(b, "z", 172.0, 1.2, z0 + 2.0, z1 - 2.0, FLOOR, 12.0, "#2a1a2a",
               holes=[(z1 - 16.0, z1 - 6.0, -1.0, 10.0)])
    holed_wall(b, "z", 200.0, 1.2, z0 + 2.0, z1 - 2.0, FLOOR, 12.0, "#2a1a2a",
               holes=[(z0 + 6.0, z0 + 16.0, -1.0, 10.0)])
    for dz in (-1.2, 1.2):
        b.box([(x0 + x1) / 2.0, FLOOR + 0.1, (z0 + z1) / 2.0 + dz], [x1 - x0 - 6.0, 0.2, 0.3], "#5a5f66",
              collide=False)
    b.box([186.0, FLOOR + 1.0, -40.0], [8.0, 2.0, 3.0], "#2a1a12")
    b.box([186.0, FLOOR + 2.2, -40.0], [8.4, 0.4, 3.4], "#4a2a1a")
    supply_ammo(b, 218.0, FLOOR, 2.0, "x-")
    supply_med(b, 156.0, FLOOR, -42.0, "x+")
    # the monster's face round the door: eyes, teeth, a sign
    b.box([x0 - 0.6, 14.0, -24.0], [1.2, 4.0, 22.0], "#5a2a5a")
    for dz in (-31.0, -17.0):
        b.box([x0 - 0.7, 14.0, dz], [0.2, 3.0, 4.0], "#c8ff3a", material="neon", collide=False)
    for k in range(5):
        b.box([x0 - 0.6, 10.4, -29.0 + k * 2.5], [1.2, 1.4, 1.2], "#f2f2e6")
    wall_sign(b, (x0 + x1) / 2.0, 14.0, z1 + 0.5, 30.0, 3.0,
              sign_decal("HOUSE OF HORRORS", "#1a141a", "#c8ff3a", 10.0), "z+", "#1a141a")


# ================================================================ barns
def _barns(b: Area, s: Surfaces, rng: random.Random) -> None:
    for k, (r, name) in enumerate(((BARN_A, "CATTLE BARN"), (BARN_B, "HOG BARN"))):
        x0, x1, z0, z1 = r
        s.reserve(r)
        building(b, r, 0.0, 15.0, "#a83a2a", roof_colour="#5a5f66", floor_colour="#8a6f52",
                 doors={"x+": [((z0 + z1) / 2.0 - 8.0, (z0 + z1) / 2.0 + 8.0, 12.0)],
                        "x-": [((z0 + z1) / 2.0 - 5.0, (z0 + z1) / 2.0 + 5.0, 9.0)]},
                 windows={"z+": [(x0 + 10.0, x0 + 30.0, 8.0, 12.0), (x1 - 30.0, x1 - 10.0, 8.0, 12.0)]},
                 glass=True, lights=WARM)
        threshold(b, r, "x+", ((z0 + z1) / 2.0 - 8.0, (z0 + z1) / 2.0 + 8.0))
        threshold(b, r, "x-", ((z0 + z1) / 2.0 - 5.0, (z0 + z1) / 2.0 + 5.0))
        gable_top = 15.0 + 1.2
        for i in range(3):
            inset = (z1 - z0) / 2.0 * (i + 1) / 3.6
            slab(b, rect(x0, x1, z0 + inset, z1 - inset), gable_top + 1.4 * (i + 1), 1.4, "#5a5f66")
        # pens down both sides, the aisle up the middle, hay at the end
        for side in (-1, 1):
            zz = (z0 + z1) / 2.0 + side * 12.0
            for j in range(4):
                px = x0 + 14.0 + j * 22.0
                b.box([px, FLOOR + 1.6, zz + side * 0.4], [0.6, 3.2, 12.6], WOOD_LIGHT)
            b.box([(x0 + x1) / 2.0 - 2.0, FLOOR + 1.6, (z0 + z1) / 2.0 + side * 5.3], [x1 - x0 - 30.0, 3.2, 0.6],
                  WOOD_LIGHT)
        for j in range(3):
            b.box([x0 + 6.0, FLOOR + 1.2 * (j + 1), (z0 + z1) / 2.0 - 14.0 + j * 6.0],
                  [6.0, 2.4 * (j + 1), 5.0], "#d8c070", studs=True)
        wall_sign(b, x1 + 0.5, 13.0, (z0 + z1) / 2.0, 20.0, 2.4,
                  sign_decal(name, "#a83a2a", "#f2ece0", 8.3), "x+", "#a83a2a")
        barrel_spot(b, x1 + 6.0, 0.0, z1 - 6.0)
    supply_med(b, -256.0, FLOOR, -40.0, "x+")
    supply_ammo(b, -256.0, FLOOR, 74.0, "x+")


# ================================================================= maze
def _maze_layout(rng: random.Random) -> Set[Tuple[int, int, int, int]]:
    """A perfect maze on the grid: the set of open joins between cells."""
    seen = {(0, 0)}
    stack = [(0, 0)]
    joins: Set[Tuple[int, int, int, int]] = set()
    while stack:
        cx, cz = stack[-1]
        options = [(cx + dx, cz + dz) for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1))
                   if 0 <= cx + dx < CELLS and 0 <= cz + dz < CELLS and (cx + dx, cz + dz) not in seen]
        if not options:
            stack.pop()
            continue
        nx, nz = rng.choice(options)
        joins.add((min(cx, nx), min(cz, nz), max(cx, nx), max(cz, nz)))
        seen.add((nx, nz))
        stack.append((nx, nz))
    # a few extra openings so it is a maze with loops, not one long corridor
    for _ in range(12):
        cx, cz = rng.randrange(CELLS - 1), rng.randrange(CELLS - 1)
        if rng.random() < 0.5:
            joins.add((cx, cz, cx + 1, cz))
        else:
            joins.add((cx, cz, cx, cz + 1))
    # the lookout's cell and its neighbours are open round the tower
    tx, tz = TOWER_CELL
    for dx, dz in ((1, 0), (0, 1)):
        joins.add((tx, tz, tx + dx, tz + dz))
        joins.add((tx - dx, tz - dz, tx, tz))
    return joins


def _maze(b: Area, s: Surfaces, rng: random.Random) -> None:
    """The corn maze: walls of corn between the cells of a maze, posts at
    the corners, a way in from the south and the east, the lookout bridge
    over the middle -- and the hay bale pyramid beside it."""
    span = CELL * CELLS
    s.reserve(rect(MAZE_X0 - 1.2, MAZE_X0 + span + 1.2, MAZE_Z0 - 1.2, MAZE_Z0 + span + 1.2))
    joins = _maze_layout(rng)
    hgt = 10.0
    posts: Set[Tuple[int, int]] = set()

    def wall_x(i: int, j: int) -> None:          # along x, on the line z = j
        x0 = MAZE_X0 + i * CELL + 1.2
        z = MAZE_Z0 + j * CELL
        b.box([x0 + (CELL - 2.4) / 2.0, hgt / 2.0, z], [CELL - 2.4, hgt, 2.4], CORN, studs=True,
              material="grass")
        posts.add((i, j))
        posts.add((i + 1, j))

    def wall_z(i: int, j: int) -> None:          # along z, on the line x = i
        z0 = MAZE_Z0 + j * CELL + 1.2
        x = MAZE_X0 + i * CELL
        b.box([x, hgt / 2.0, z0 + (CELL - 2.4) / 2.0], [2.4, hgt, CELL - 2.4], CORN, studs=True,
              material="grass")
        posts.add((i, j))
        posts.add((i, j + 1))

    for i in range(CELLS):
        for j in range(CELLS):
            if j + 1 < CELLS and (i, j, i, j + 1) not in joins:
                wall_x(i, j + 1)
            if i + 1 < CELLS and (i, j, i + 1, j) not in joins:
                wall_z(i + 1, j)
    for i in range(CELLS):
        if i not in (CELLS // 2, CELLS // 2 + 1):
            wall_x(i, 0)
        wall_x(i, CELLS)
    for j in range(CELLS):
        wall_z(0, j)
        if j != CELLS // 2:
            wall_z(CELLS, j)
    for (i, j) in posts:
        b.box([MAZE_X0 + i * CELL, (hgt + 0.6) / 2.0, MAZE_Z0 + j * CELL], [2.4, hgt + 0.6, 2.4],
              "#6a7a24", studs=True, material="grass")
    # the lookout bridge in the middle cell: four legs, a deck, a stair
    tx, tz = TOWER_CELL
    cx = MAZE_X0 + (tx + 0.5) * CELL
    cz = MAZE_Z0 + (tz + 0.5) * CELL
    deck = 14.0
    slab(b, rect(cx - 4.0, cx + 4.0, cz - 4.0, cz + 4.0), deck, 0.8, WOOD_LIGHT, studs=True)
    for dx in (-3.4, 3.4):
        for dz in (-3.4, 3.4):
            b.box([cx + dx, (deck - 0.8) / 2.0, cz + dz], [0.8, deck - 0.8, 0.8], WOOD_DARK)
    flight(b, "z", cz + 4.0 + CELL - 1.2 - 0.0, cz + 4.0, cx - 2.6, cx + 2.6, 0.0, deck, WOOD,
           fill=0.0)
    for (rx, rz, w, d) in ((cx, cz - 3.7, 8.0, 0.6), (cx - 3.7, cz, 0.6, 6.8), (cx + 3.7, cz, 0.6, 6.8)):
        b.box([rx, deck + 1.4, rz], [w, 2.8, d], WOOD_DARK)
    supply_ammo(b, cx, deck, cz - 1.0, "z+")
    post_sign(b, MAZE_X0 + span / 2.0, MAZE_Z0 - 6.0, 0.0, 4.0, 14.0, 2.2,
              sign_decal("CORN MAZE  ENTER IF YOU DARE", "#f2ece0", "#3a5a1a", 6.4), "z-", "#f2ece0")
    # the hay bale pyramid
    hx, hz = HAY
    s.reserve(rect(hx - 15.0, hx + 15.0, hz - 15.0, hz + 15.0))
    tier_stack(b, [[rect(hx - 15.0 + k * 3.0, hx + 15.0 - k * 3.0, hz - 15.0 + k * 3.0,
                         hz + 15.0 - k * 3.0)] for k in range(5)], 0.0, [2.0], ["#d8c070", "#c8b060"])
    supply_ammo(b, hx, 10.0, hz, "z-")


# ======================================================= grain elevator
def _elevator(b: Area, s: Surfaces) -> None:
    gx0, gx1, gz0, gz1 = GALLERY
    s.reserve(rect(gx0 - 2.0, gx1 + 2.0, 194.0, gz1 + 2.0))
    for (sx, sz) in SILOS:
        b.cyl([sx, SILO_H / 2.0, sz], [16.0, SILO_H, 16.0], "#c8c4b8")
    slab(b, GALLERY, SILO_H + 0.8, 0.8, "#8a8f94", studs=True, material="metal")
    for (a, c, d, e) in ((gx0, gx1, gz1 - 0.6, gz1), (gx0, gx0 + 0.6, gz0 + 0.6, gz1 - 0.6),
                         (gx1 - 0.6, gx1, gz0 + 0.6, gz1 - 0.6), (gx0 + 22.0, gx1, gz0, gz0 + 0.6)):
        b.box([(a + c) / 2.0, SILO_H + 0.8 + 1.4, (d + e) / 2.0], [c - a, 2.8, e - d], "#5a5f66",
              material="metal")
    # the stair: along the south, a landing, up onto the gallery
    flight(b, "x", 206.0, 222.0, 196.0, 202.0, 0.0, 12.0, "#5a5f66", fill=0.0)
    slab(b, rect(222.0, 228.0, 196.0, 208.0), 12.0, 0.8, "#8a8f94", studs=True)
    for (px, pz) in ((227.4, 196.6), (227.4, 207.4)):
        b.box([px, 5.6, pz], [0.8, 11.2, 0.8], "#5a5f66")
    flight(b, "z", 208.0, gz0, 222.0, 228.0, 12.0, SILO_H + 0.8, "#5a5f66", fill=12.0)
    b.box([239.0, 4.0, 210.0], [10.0, 8.0, 10.0], "#a83a2a")
    supply_ammo(b, 248.0, SILO_H + 0.8, 236.0, "x-")
    barrel_spot(b, 252.0, 0.0, 208.0)
    wall_sign(b, 232.0, 18.0, 227.6, 26.0, 3.0, sign_decal("HARROW CO-OP", "#c8c4b8", "#a83a2a", 8.7),
              "z-", "#c8c4b8")


# =============================================================== pumpkin
def _pumpkin(b: Area, s: Surfaces) -> None:
    x0, x1, z0, z1 = PUMPKIN
    s.reserve(PUMPKIN)
    slab(b, PUMPKIN, 2.0, 2.0, WOOD, studs=True)
    flight(b, "z", z0 - 6.0, z0, 76.0, 88.0, 0.0, 2.0, WOOD_DARK, fill=0.0)
    b.sphere([82.0, 2.0 + 5.0, -38.0], [14.0, 10.0, 13.0], "#e8782a")
    b.cyl([82.0, 2.0 + 10.6, -38.0], [1.2, 2.4, 1.2], "#4a6a2a")
    b.box([70.0, 2.0 + 1.0, -30.0], [6.0, 2.0, 4.0], "#8a8f94", material="metal")
    wall_sign(b, 82.0, 2.0 + 13.6, z1 - 1.0, 18.0, 2.4,
              sign_decal("BIGGEST PUMPKIN 1204 LBS", "#3a7ac8", "#f2ece0", 7.5), "z-", "#3a7ac8")
    b.box([82.0, 2.0 + 7.0, z1 - 0.6], [1.0, 14.0, 1.0], WOOD_DARK)


# ============================================================ pig races
def _pig_race(b: Area, s: Surfaces) -> None:
    """The pig races: a dirt oval round a grass island, a board fence with
    a way in from the west, bleachers along the east side; the pigs (a
    rig) go round in their racing silks."""
    x0, x1, z0, z1 = PIGRACE
    s.reserve(PIG_ISLAND)
    s.lay(PIGRACE, 0.4, DIRT, studs=True)
    s.reserve(rect(x0 - 2.0, 122.0, z0 - 2.0, z1 + 2.0))
    ix0, ix1, iz0, iz1 = PIG_ISLAND
    b.box([(ix0 + ix1) / 2.0, 1.0, (iz0 + iz1) / 2.0], [ix1 - ix0, 2.0, iz1 - iz0], GRASS, studs=True,
          material="grass")
    post_sign(b, 80.0, 50.0, 2.0, 5.0, 16.0, 3.0, sign_decal("PIG RACES  4PM 6PM 8PM", RED, WHITE, 5.3),
              "z-", RED)
    # the fence, with a gap on the west to walk in by
    fh = 2.2
    for (a, c, d, e) in ((x0 - 0.6, x1 + 0.6, z0 - 0.6, z0), (x0 - 0.6, x1 + 0.6, z1, z1 + 0.6),
                         (x1, x1 + 0.6, z0, z1), (x0 - 0.6, x0, z0, 46.0), (x0 - 0.6, x0, 54.0, z1)):
        b.box([(a + c) / 2.0, fh / 2.0, (d + e) / 2.0], [c - a, fh, e - d], WHITE)
    # the bleachers
    tier_stack(b, [[rect(108.0, 120.0, 32.0, 68.0)], [rect(112.0, 120.0, 32.0, 68.0)],
                   [rect(116.0, 120.0, 32.0, 68.0)]], 0.0, [1.4], ["#c8c4b8", "#a8a49a"])
    supply_ammo(b, 126.0, 0.0, 50.0, "x-")
    barrel_spot(b, 112.0, 0.0, 76.0)


def _sundries(b: Area, s: Surfaces) -> None:
    """The fair's odds and ends: picnic tables by the food stands, the
    portable toilets behind the booths (one of them occupied), hay bales
    stacked about for cover."""
    for (x, z) in ((-30.0, 84.0), (50.0, 86.0)):
        b.box([x, 2.6, z], [8.0, 0.4, 3.4], WOOD_LIGHT, studs=True)
        for dx in (-3.2, 3.2):
            b.box([x + dx, 1.2, z], [0.6, 2.4, 2.6], WOOD_DARK)
        for dz in (-3.6, 3.6):
            bench(b, x, z + dz, "x")
    x0, x1, z0, z1 = TOILETS
    s.reserve(rect(x0 - 1.0, x1 + 1.0, z0 - 1.0, z1))
    for k in range(4):
        tx = x0 + 3.0 + k * 6.0
        b.box([tx, 4.0, (z0 + z1) / 2.0], [5.0, 8.0, z1 - z0], "#3a7ac8")
        b.box([tx, 8.3, (z0 + z1) / 2.0], [5.4, 0.6, z1 - z0 + 0.4], WHITE)
        if k == 2:
            continue                      # the occupied one: its door is a rig, rattling
        b.box([tx, 3.6, z0 - 0.1], [3.0, 6.6, 0.2], "#2a5a98")
        b.box([tx, 6.0, z0 - 0.25], [1.6, 0.5, 0.1], "#3aa84a")
    for (x, z) in ((40.0, -104.0), (-56.0, -100.0), (130.0, -96.0), (-130.0, 28.0), (176.0, 160.0)):
        for dx in (-3.2, 3.2):
            b.box([x + dx, 1.3, z], [6.0, 2.6, 3.4], "#d8c070", studs=True)
        b.box([x, 3.9, z], [3.4, 2.6, 6.0], "#c8b060", studs=True)


def _derby_car(b: Area, x: float, z: float, along: str, colour: str, number: int, y: float) -> None:
    """A derby car: painted loud, its number on the doors and on a board
    on the roof, the glass knocked out, the nose already pushed in."""
    length, w = 11.0, 5.0

    def box(cx, cy, cz, sx, sy, sz, c, **kw):
        if along == "x":
            b.box([x + cx, y + cy, z + cz], [sx, sy, sz], c, **kw)
        else:
            b.box([x + cz, y + cy, z + cx], [sz, sy, sx], c, **kw)

    box(0.6, 1.85, 0.0, length - 1.2, 2.5, w, colour, material="metal")
    box(-4.9, 1.75, 0.0, 1.4, 1.9, w - 0.6, "#8a8f94", material="metal")
    box(-0.4, 3.85, 0.0, 5.0, 1.5, w - 0.6, "#1d2226", material="metal")
    box(-0.4, 4.75, 0.0, 4.4, 0.3, w - 1.2, colour, material="metal")
    label = sign_decal(str(number), WHITE, "#1b1b1b", 1.7)
    for side in (-1, 1):
        if along == "x":
            b.box([x + 0.6, y + 1.85, z + side * (w / 2.0 + 0.1)], [3.0, 1.8, 0.2], WHITE,
                  r=[0, 0.0 if side > 0 else math.pi, 0], decal=label)
            b.box([x - 0.4, y + 5.8, z + side * 0.2], [3.0, 1.8, 0.3], WHITE,
                  r=[0, 0.0 if side > 0 else math.pi, 0], decal=label)
        else:
            b.box([x + side * (w / 2.0 + 0.1), y + 1.85, z + 0.6], [3.0, 1.8, 0.2], WHITE,
                  r=[0, math.pi / 2.0 * side, 0], decal=label)
            b.box([x + side * 0.2, y + 5.8, z - 0.4], [3.0, 1.8, 0.3], WHITE,
                  r=[0, math.pi / 2.0 * side, 0], decal=label)
        for end in (-1, 1):
            if along == "x":
                b.cyl([x + end * length * 0.32, y + 1.1, z + side * (w / 2.0 - 0.2)],
                      [2.2, 0.9, 2.2], "#1b1d20", r=[math.pi / 2.0, 0, 0], collide=False)
            else:
                b.cyl([x + side * (w / 2.0 - 0.2), y + 1.1, z + end * length * 0.32],
                      [2.2, 0.9, 2.2], "#1b1d20", r=[0, 0, math.pi / 2.0], collide=False)


# ================================================================== gate
def _gate(b: Area, s: Surfaces, rng: random.Random) -> None:
    x0, x1, z0, z1 = GATE
    for x in (x0, x1):
        b.box([x, 9.0, (z0 + z1) / 2.0], [3.0, 18.0, 3.0], RED)
    b.box([(x0 + x1) / 2.0, 17.0, (z0 + z1) / 2.0], [x1 - x0 - 3.0, 3.0, 2.0], WHITE)
    board_letters(b, (x0 + x1) / 2.0, 17.0, (z0 + z1) / 2.0 - 1.0, "COUNTY FAIR", 2.4, WHITE, RED,
                  facing="z-", solid=False)
    for k, bx in enumerate((-212.0, -138.0)):
        booth = rect(bx - 5.0, bx + 5.0, -250.0, -240.0)
        s.reserve(booth)
        building(b, booth, 0.0, 8.0, WHITE, roof_colour=RED, doors={"z+": [(bx - 4.0, bx + 4.0, 6.6)]},
                 windows={"z-": [(bx - 3.0, bx + 3.0, 3.0, 6.0)]}, glass=True, lights=WARM)
        threshold(b, booth, "z+", (bx - 4.0, bx + 4.0))
    supply_med(b, -212.0, 0.0, -246.6, "z+")
    # the parking field: pickups on the grass, a horse trailer
    for k, (cx, cz) in enumerate(((-250.0, -220.0), (-230.0, -220.0), (-250.0, -186.0), (-110.0, -226.0),
                                  (-120.0, -192.0))):
        car(b, cx, cz, "z", ["#8a2a24", "#3a5a6a", "#e8e8e8", "#c8a83a", "#2a4a2a"][k], length=12.0,
            wrecked=k == 4)
    b.box([-196.0, 4.0, -204.0], [7.0, 8.0, 18.0], "#c8c4b8", material="metal")
    barrel_spot(b, -140.0, 0.0, -220.0)


def _country(b: Area, s: Surfaces, rng: random.Random) -> None:
    """The tractor pull's sled and tractor, knolls in the open grass, the
    trees along the north, string lights and lamps."""
    b.box([140.0, 0.4 + 2.4, -228.0], [14.0, 4.8, 10.0], "#e8c83a", material="metal")
    b.box([140.0, 0.4 + 6.0, -228.0], [10.0, 2.4, 8.0], "#5a5f66", material="metal")
    tx, tz = 166.0, -228.0
    b.box([tx, 0.4 + 3.0, tz], [10.0, 4.0, 5.0], "#3a7a3a", material="metal")
    b.box([tx - 2.0, 0.4 + 6.6, tz], [4.0, 3.2, 4.4], "#2a3a2a")
    for dx, size in ((-3.4, 5.2), (3.6, 3.0)):
        for side in (-1, 1):
            b.cyl([tx + dx, 0.4 + size / 2.0, tz + side * 3.2], [size, 1.2, size], "#1b1d20",
                  r=[math.pi / 2.0, 0, 0], collide=False)
            b.box([tx + dx, 0.4 + size / 2.0, tz + side * 3.2], [size, size, 1.2], "#1b1d20", alpha=0.0)
    for (cx, cz, rx, rz) in ((-60.0, 40.0, 14.0, 22.0), (-220.0, -130.0, 18.0, 14.0), (120.0, 180.0, 22.0, 18.0),
                             (-110.0, -110.0, 18.0, 14.0), (150.0, -120.0, 14.0, 12.0)):
        s.reserve(rect(cx - rx, cx + rx, cz - rz, cz + rz))
        top = mound(b, cx, cz, rx, rz, 2, 1.4, ["#628040", "#5a7a38"])
        tree(b, cx, cz, top, rng.uniform(1.0, 1.4), "#7a5335", "#3f7a3a")
    for k in range(14):
        px = -250.0 + k * 38.0 + rng.uniform(-6.0, 6.0)
        if px < -128.0 or px > 196.0:
            continue
        pine(b, px, 272.0, 0.0, rng.uniform(1.4, 2.0))
    for (x, z, y) in ((-26.0, 120.0, 0.3), (54.0, 120.0, 0.3), (134.0, 120.0, 0.3), (214.0, 120.0, 0.3),
                      (-120.0, -68.0, 0.3), (60.0, -68.0, 0.3), (-20.0, -86.0, 0.0), (140.0, -86.0, 0.0)):
        lamp_post(b, x, z, h=14.0, light=WARM, y=y)


# ================================================================== rigs
def _rigs(b: Area) -> None:
    fx, fz = FERRIS
    b.rig("ferris_wheel", fx, FERRIS_AXLE, fz, 0.0, r=FERRIS_R, n=16)
    b.rig("fair_carousel", CAROUSEL[0], 1.2, CAROUSEL[1], 0.0, r=13.0, n=12)
    b.rig("swing_ride", SWINGS[0], 32.0, SWINGS[1], 0.0, n=12, r=10.0)
    b.rig("duck_gallery", -46.0, 5.4, 140.0 - 0.0, 0.0, w=16.0)
    b.rig("strength_bell", 14.0, 0.3, 102.0, 0.0)
    b.rig("prize_bull", -230.0, FLOOR, -31.0, 0.0)
    b.rig("pigs", -210.0, FLOOR, 41.0, 0.0, n=5, area=[-246.0, -170.0, 34.0, 47.0])
    b.rig("chickens", -150.0, 0.0, 0.0, 0.0, n=7, area=[-146.0, -120.0, -40.0, 20.0])
    b.rig("haunt_popups", 190.0, FLOOR, -20.0, 0.0,
          spots_p=[[160.0, FLOOR, -40.0], [186.0, FLOOR, 2.0], [214.0, FLOOR, -40.0], [186.0, FLOOR, -36.0]])
    b.rig("balloons", 124.6, 9.6, 109.4, 0.0, n=9)
    b.rig("derby_lights", 0.0, 26.0, -209.0, 0.0, w=200.0)
    b.rig("pig_race", 80.0, 0.4, 50.0, 0.0, a=20.0, c=14.0, n=6)
    b.rig("porta_knock", TOILETS[0] + 15.0, 0.0, TOILETS[2], 0.0)
    for (x, z) in ((-80.0, 120.0), (240.0, 120.0)):
        b.rig("moth_swarm", x, 9.0, z, 0.0)


# ================================================================ spawns
def _zombie_spawns(b: Area, rng: random.Random) -> None:
    for (i, j) in ((1, 2), (9, 1), (3, 9), (8, 8), (1, 6), (9, 5)):
        b.zombie_spawn(MAZE_X0 + (i + 0.5) * CELL, MAZE_Z0 + (j + 0.5) * CELL, "maze", y=0.0)
    b.zombie_spawn(200.0, -20.0, "haunt", y=FLOOR)
    pts = [(-240.0, -274.0), (-60.0, -274.0), (60.0, -274.0), (240.0, -274.0),
           (-100.0, 272.0), (40.0, 268.0), (160.0, 272.0), (-272.0, 110.0), (-272.0, -120.0),
           (272.0, 60.0), (272.0, -60.0), (272.0, 160.0), (-160.0, -200.0), (240.0, -190.0),
           (-272.0, 280.0 - 20.0), (110.0, 240.0), (-40.0, 250.0), (-130.0, 90.0), (120.0, -30.0)]
    for x, z in pts:
        b.zombie_spawn(x, z, "")
