"""Starlite Drive-In -- a picture show under the stars on the Harrow County
line, the night the feature turned out to be the end of the world.

Layout (north is +z)::

   z +280 ------------------------ the woods ----------------------------------
          WATER     [======= THE SCREEN: climb the scaffold behind it =======]
          TOWER            the playground at its foot             . C .
     R              -- row --  speaker posts, '50s cars  -- row --  . O .
     A              -- row --                            -- row --  . R .
     I              -- row --   THE SNACK BAR (safe room) -- row -- . N .
     L                          the projection booth on its roof     . F .
     W              -- row --                            -- row --  . I .
     A   ~~~~~~~~~~~~~~~~~~~~~ the drainage ditch ~~~~~~~~~~~~~~~~~~~ . E .
     Y    JUNKYARD + the trailer   BOX OFFICE   MARQUEE   PUTT-PUTT + THE DINOSAUR
   z -280 ======================== the highway =================================

Everybody deploys in the snack bar, up on its mound in the middle of the
field, with the projection booth on its roof.

What makes it this place:

* **The screen.**  Fifty units of white, and behind it a steel scaffold of
  stairs and decks all the way to a walkway along its top -- the highest
  ground in the county and the best view of the field there is.  The
  picture never stops: the feature plays through every wave, the
  intermission card comes up between them, and when somebody cranks the
  sound the monster on the screen comes right up to the glass.
* **The rows.**  Nine rows of parking humps with a speaker post every few
  cars: no two steps of the field are level, the cars are cover a body can
  climb, and every row is a firing line facing the screen.
* **The corn.**  The infected come out of the corn on the east side, rows of
  it taller than a man, and out of the woods behind the screen, the ditch,
  the junkyard, the railway and the jammed highway.
* **The projector.**  The lure is the booth's sound desk: crank it up and the
  whole field's speakers blare the monster's roar, and the horde goes for
  the screen -- right across the front rows, under the guns on the roof.
"""
from __future__ import annotations

import math
import random
from typing import List

from .kit import (
    ASPHALT, ASPHALT_DARK, CONCRETE, CONCRETE_DARK, FLOOR, LAMP, LINE_YELLOW,
    STEEL, STEEL_DARK, WARM, WOOD, WOOD_DARK, WOOD_LIGHT, Area, Surfaces,
    barrel_spot, bench, boundary, building, car, carve, chain_fence, crate,
    deploy_pad, flight, holed_wall, lamp_post, plate, post_sign, rect, room_walls,
    sign_decal, slab, solid_fence, strip_light, supply_ammo, supply_med,
    threshold, wall_sign)
from ..relay.kit import board_letters, pine, rails, ridge, tier_stack

HALF = 280.0
SKY = {"top": "#04071a", "horizon": "#28305a", "sun": [0.32, 0.46, -0.58],
       "clouds": 0.16, "tint": "#a4b0ea"}
AMBIENT = "#566082"

GRASS = "#3f5a34"
SOIL = "#4a3f30"
GRAVEL = "#6e6a60"
HUMP = "#3a3d42"
SAND = "#c8b48a"
SCREEN_WHITE = "#e8e6dc"
FRAME = "#2a2d33"
BAR_WALL = "#f2efe6"
BAR_TRIM = "#3ab0b0"
BAR_RED = "#c43a32"
TILE = "#d8d0c0"
SODIUM = "#ffc46a"
BALLAST = "#7a7468"
CORN = "#6f8a2a"
TASSEL = "#c8b45a"
RUST = "#7a4a2a"

DITCH = rect(-150.0, 150.0, -160.0, -148.0)
DITCH_BED = -4.0
ROAD = rect(-16.0, 16.0, -262.0, -140.0)
HIGHWAY = rect(-280.0, 280.0, -280.0, -262.0)
FIELD = rect(-160.0, 160.0, -146.0, 198.0)
PLAYGROUND = rect(-62.0, 62.0, 198.0, 228.0)

ROWS_N = [176.0, 150.0, 124.0, 98.0, 72.0, 46.0]
ROWS_S = [-72.0, -98.0, -124.0]
ROW_X = 150.0
HUMP_TOP = 1.8

SCREEN = rect(-80.0, 80.0, 228.0, 250.0)       # the screen tower's base
FACE_Z = 228.0
BASE_TOP = 10.8
DECK1, DECK2, TOP = 26.0, 42.0, 61.8

MOUND0 = rect(-66.0, 66.0, -56.0, 30.0)
MOUND1 = rect(-58.0, 58.0, -50.0, 24.0)
BAR = rect(-48.0, 48.0, -44.0, 18.0)
BAR_Y = 3.2
BAR_H = 13.0
ROOF = BAR_Y + BAR_H + 1.2                      # 17.4
STAIR_HOLE = rect(28.0, 44.0, -42.0, -34.0)
BOOTH = rect(-16.0, 16.0, -24.0, 2.0)

EMBANK = (-238.0, -194.0)
RAIL_TOP = 7.8
TRACK_X = -216.0

JUNK = rect(-190.0, -60.0, -258.0, -168.0)
PUTT = rect(50.0, 170.0, -258.0, -168.0)
CORN_X = (172.0, 272.0)
CORN_Z = (-140.0, 270.0)

CAR_COLOURS = ["#7ac8c8", "#e8a0b0", "#f0e0a0", "#c83a3a", "#3a5a8a", "#2a2a2a",
               "#f2f2f2", "#8ac87a", "#e8a040"]


def build(b: Area) -> None:
    rng = random.Random(0x57A7)
    b.extra.update({"weather": "moths", "accent": "#7ae8e0"})
    _ground(b)
    boundary(b, 30.0, "#1c2a1e", "#14201a", rng, horizon="forest")
    s = Surfaces(b)
    s.reserve(DITCH)
    _screen(b, s)
    _playground(b, s)
    _snack_bar(b, s)
    _rows(b, s, rng)
    _entrance(b, s, rng)
    _railway(b, s, rng)
    _corn(b, s, rng)
    _junkyard(b, s, rng)
    _putt(b, s)
    _covers(b, s)
    _lights(b)
    _rigs(b)
    _zombie_spawns(b)
    for x, z, name in ((0, -14, "the snack bar"), (0, 238, "the screen"),
                       (0, 210, "the playground"), (-80, 150, "the front rows"),
                       (90, 110, "the east rows"), (-100, 60, "the west rows"),
                       (80, -100, "the back rows"), (0, -192, "the box office"),
                       (58, -232, "the marquee"), (-216, 90, "the railway"),
                       (-216, -20, "the boxcars"), (222, 60, "the corn"),
                       (-128, -214, "the junkyard"), (96, -214, "the putt-putt"),
                       (140, -200, "the dinosaur"), (-150, 252, "the water tower")):
        b.landmark(float(x), float(z), name)
    b.camera(0.0, 40.0, -150.0, 0.0, 20.0, 200.0)
    b.camera(-150.0, 70.0, 150.0, 0.0, 0.0, 0.0)
    b.camera(0.0, 74.0, 238.0, 0.0, 0.0, 40.0)
    b.camera(150.0, 30.0, -150.0, 60.0, 4.0, -220.0)


# ================================================================ ground
def _ground(b: Area) -> None:
    h = b.half + b.margin
    pieces = carve(rect(-h, h, -h, h), [DITCH])
    plate(b, pieces, 0.0, 0.6, GRASS, studs=True, material="grass")
    plate(b, pieces, -0.6, 5.4, SOIL)
    # the ditch: a stony bed, a trickle of water, and the road over it on
    # fill (the culvert under it is too low to walk)
    for x0, x1 in ((DITCH[0], ROAD[0]), (ROAD[1], DITCH[1])):
        slab(b, rect(x0, x1, DITCH[2], DITCH[3]), DITCH_BED, 2.0, "#4a4638", studs=True)
        b.water((x0 + x1) / 2.0, (DITCH[2] + DITCH[3]) / 2.0, x1 - x0, DITCH[3] - DITCH[2],
                -3.0, "#2f4a3a")
    slab(b, rect(ROAD[0], ROAD[1], DITCH[2], DITCH[3]), 0.0, 6.0, SOIL)
    # two plank footbridges over it
    for x in (-100.0, 100.0):
        slab(b, rect(x - 4.0, x + 4.0, DITCH[2] - 2.0, DITCH[3] + 2.0), 0.9, 0.9, WOOD_LIGHT,
             studs=True)
        for z in (DITCH[2] - 1.5, DITCH[3] + 1.5):
            for dx in (-3.6, 3.6):
                b.box([x + dx, 2.3, z], [0.8, 2.8, 0.8], WOOD_DARK)


def _covers(b: Area, s: Surfaces) -> None:
    """Everything laid on the ground, once every footprint is reserved."""
    s.lay(PLAYGROUND, 0.4, SAND, studs=True)
    s.lay(HIGHWAY, 0.3, ASPHALT, studs=False)
    s.lay(ROAD, 0.3, ASPHALT, studs=False)
    s.lay(FIELD, 0.3, GRAVEL, studs=True)
    s.lay(rect(160.0, 172.0, -150.0, 272.0), 0.3, "#7a6448", studs=True)     # farm track
    # paint on the highway and the road in
    for k in range(-13, 14):
        if -250.0 < k * 20.0 < -184.0:
            continue
        b.box([k * 20.0, 0.32, -271.0], [10.0, 0.04, 0.8], LINE_YELLOW, collide=False)
    for z in range(-250, -140, 18):
        if -206 < z < -180:
            continue
        b.box([0.0, 0.32, float(z)], [0.8, 0.04, 8.0], "#d9dcd6", collide=False)
    slab(b, rect(ROAD[0], ROAD[1], DITCH[2], DITCH[3]), 0.3, 0.3, ASPHALT)


# ================================================================ screen
def _screen(b: Area, s: Surfaces) -> None:
    x0, x1, z0, z1 = SCREEN
    s.reserve(rect(x0 - 2.0, x1 + 2.0, z0 - 1.0, z1 + 28.0))
    building(b, SCREEN, 0.0, BASE_TOP - 1.2, "#4a5058", roof_colour="#3a3f46",
             floor_colour="#5a5f66", doors={"z-": [(-6.0, 6.0, 8.0)], "z+": [(46.0, 56.0, 8.0)]},
             windows={"z-": [(-60.0, -40.0, 3.0, 7.0), (40.0, 60.0, 3.0, 7.0)]},
             glass=True, lights=LAMP)
    threshold(b, SCREEN, "z-", (-6.0, 6.0))
    threshold(b, SCREEN, "z+", (46.0, 56.0))
    # the screen house: the generator, spare speakers on a rack, a cot
    b.box([-60.0, FLOOR + 3.0, 241.0], [14.0, 6.0, 10.0], "#5a6a4a", material="metal")
    b.box([-60.0, FLOOR + 6.6, 241.0], [2.0, 1.2, 2.0], STEEL_DARK)
    for k in range(3):
        b.box([-20.0, FLOOR + 1.0 + k * 2.4, 246.0], [24.4, 0.4, 3.0], WOOD)
        for j in range(6):
            b.box([-30.0 + j * 4.0, FLOOR + 1.9 + k * 2.4, 246.0], [1.6, 1.4, 1.2], "#5a5f66")
    for x in (-32.6, -7.4):
        b.box([x, FLOOR + 3.4, 246.0], [0.8, 6.8, 3.2], WOOD_DARK)
    b.box([30.0, FLOOR + 1.0, 244.0], [12.0, 2.0, 6.0], "#6a5a4a", studs=True)
    supply_med(b, 64.0, FLOOR, 238.0, "x-")
    supply_ammo(b, -70.0, FLOOR, 233.0, "x+")
    # the screen itself, and the black masking round it
    b.box([0.0, (BASE_TOP + 60.8) / 2.0, FACE_Z + 1.0], [x1 - x0, 60.8 - BASE_TOP, 2.0],
          SCREEN_WHITE)
    b.box([0.0, 62.3, FACE_Z + 1.0], [x1 - x0 + 4.0, 3.0, 2.0], FRAME)
    for sx in (-1, 1):
        b.box([sx * (x1 + 1.0), 30.4, FACE_Z + 1.0], [2.0, 60.8, 2.0], FRAME)
    # the scaffold behind it: decks, flights between them, columns
    slab(b, rect(-4.0, 80.0, 230.0, 250.0), DECK1, 1.0, STEEL, studs=True, material="metal")
    slab(b, rect(-80.0, 40.0, 230.0, 250.0), DECK2, 1.0, STEEL, studs=True, material="metal")
    slab(b, rect(-40.0, 80.0, 230.0, 244.0), TOP, 1.0, STEEL, studs=True, material="metal")
    slab(b, rect(-80.0, -40.0, 230.0, 234.0), TOP, 1.0, STEEL, studs=True, material="metal")
    flight(b, "z", 276.0, 250.0, -70.0, -62.0, 0.0, BASE_TOP, STEEL_DARK, fill=0.0)
    flight(b, "x", -40.0, -4.0, 236.0, 244.0, BASE_TOP, DECK1, STEEL_DARK, fill=BASE_TOP)
    flight(b, "x", 76.0, 40.0, 236.0, 244.0, DECK1, DECK2, STEEL_DARK, fill=DECK1)
    flight(b, "x", -76.0, -40.0, 236.0, 244.0, DECK2, TOP, STEEL_DARK, fill=DECK2)
    for x in (-78.0, -40.0, 0.0, 40.0, 78.0):
        b.box([x, (BASE_TOP + TOP - 1.0) / 2.0, 248.6], [1.2, TOP - 1.0 - BASE_TOP, 1.2],
              STEEL_DARK, material="metal")
    # railings: the decks' open edges, leaving the flights their ways on
    def rail(xa, xb, za, zb, y):
        b.box([(xa + xb) / 2.0, y + 1.6, (za + zb) / 2.0], [xb - xa, 3.2, zb - za], STEEL,
              material="metal")
    rail(-2.0, 78.0, 249.4, 250.0, DECK1)        # deck 1, north edge (column side)
    rail(-80.0, 38.0, 249.4, 250.0, DECK2)
    rail(-38.0, 80.0, 243.4, 244.0, TOP)
    rail(79.4, 80.0, 230.0, 243.4, TOP)
    rail(-80.0, -79.4, 230.0, 234.0, TOP)
    rail(-80.0, -40.6, 234.0, 234.6, TOP)
    # (the masking along the top of the screen stands two units proud of the
    # top deck: that is its parapet)
    supply_ammo(b, 62.0, TOP, 238.0, "x-")
    wall_sign(b, 0.0, 6.0, z1 + 0.4, 30.0, 2.4,
              sign_decal("NO CLIMBING THE SCREEN", "#c43a32", "#f2f2f2", 12.0), "z+", "#c43a32")


def _playground(b: Area, s: Surfaces) -> None:
    y = 0.4
    # the swing frame (the swings are rigs)
    for x in (-48.0, -24.0):
        for dz in (-3.0, 3.0):
            b.cyl([x, y + 6.0, 212.0 + dz], [0.9, 12.0, 0.9], "#c43a32", material="metal")
    b.box([-36.0, y + 12.4, 212.0], [25.0, 0.8, 0.8], "#c43a32", material="metal")
    # the slide: a ladder of steps up to a deck, a stepped chute down
    flight(b, "x", -6.0, 4.0, 216.0, 222.0, y, y + 7.0, "#3a7ac8", fill=y)
    slab(b, rect(4.0, 12.0, 214.0, 224.0), y + 7.0, 1.0, "#f2b01e", studs=True)
    for k in range(6):
        top = y + 7.0 - (k + 1) * 1.1
        b.box([8.0, top - 0.5, 214.0 - k * 2.4 - 1.2], [5.0, 1.0, 2.4], "#e8c83a")
    b.box([8.0, y + 0.3, 199.3], [5.0, 0.6, 1.0], "#e8c83a")
    for lx in (4.6, 11.4):
        for lz in (214.6, 223.4):
            b.box([lx, y + 3.0, lz], [0.8, 6.0, 0.8], "#3a7ac8")
    for x in (4.4, 11.6):
        b.box([x, y + 8.0 + 1.0, 219.0], [0.8, 2.0, 10.0], "#3a7ac8")
    # the merry-go-round's deck (its rails turn: a rig) and a seesaw
    b.cyl([32.0, y + 0.4, 208.0], [13.0, 0.8, 13.0], "#c8c0b0", material="metal")
    b.box([48.0, y + 1.0, 220.0], [1.6, 2.0, 1.6], STEEL_DARK)
    b.box([48.0, y + 2.3, 220.0], [14.0, 0.6, 1.6], "#3a8ac8")
    # the climbing frame
    for dx in (-5.0, 5.0):
        for dz in (-5.0, 5.0):
            b.box([-6.0 + dx, y + 4.0, 204.0 + dz], [0.6, 8.0, 0.6], "#e8782a")
    for dz in (-5.0, 0.0, 5.0):
        b.box([-6.0, y + 8.3, 204.0 + dz], [10.6, 0.6, 0.6], "#e8782a")
    # the sandbox
    for (x, z, w, d) in ((-40.0, 199.6, 16.0, 1.2), (-40.0, 206.4, 16.0, 1.2),
                         (-48.6, 203.0, 1.2, 8.0), (-31.4, 203.0, 1.2, 8.0)):
        b.box([x, y + 0.4, z], [w, 0.8, d], WOOD_LIGHT)
    b.box([-42.0, y + 0.9, 203.0], [1.6, 1.0, 1.6], "#c43a32")
    post_sign(b, 56.0, 201.0, y, 4.0, 12.0, 2.6, sign_decal("PLAYGROUND CLOSES AT SHOWTIME",
                                                             "#2f5f8a", "#f2f2f2", 4.6),
              "z-", "#2f5f8a")


# ============================================================ snack bar
def _snack_bar(b: Area, s: Surfaces) -> None:
    s.reserve(MOUND0)
    tier_stack(b, [[MOUND0], [MOUND1]], 0.0, [1.6], ["#5a7a44", "#4f6b3a"], studs=True)
    x0, x1, z0, z1 = BAR
    y = BAR_Y
    head = y + 10.0
    building(b, BAR, y, BAR_H, BAR_WALL, roof_colour="#3a3d42", floor_colour=TILE,
             doors={"z+": [(-8.0, 8.0, head)], "z-": [(-38.0, -26.0, head)],
                    "x-": [(-12.0, 0.0, head)], "x+": [(-12.0, 0.0, head)]},
             windows={"z+": [(-42.0, -14.0, y + 3.6, y + 8.4), (14.0, 42.0, y + 3.6, y + 8.4)],
                      "x-": [(4.0, 14.0, y + 3.6, y + 8.4)],
                      "x+": [(4.0, 14.0, y + 3.6, y + 8.4)]},
             glass=True, roof_holes=[STAIR_HOLE], parapet=3.0,
             parapet_gaps={"x-": [(-6.0, 4.0)]}, lights=WARM)
    for side, span in (("z+", (-8.0, 8.0)), ("z-", (-38.0, -26.0)), ("x-", (-12.0, 0.0)),
                       ("x+", (-12.0, 0.0))):
        threshold(b, BAR, side, span, y0=y)
    # the red band and the turquoise trim round the outside
    for zz, out in ((z0 - 0.15, -1), (z1 + 0.15, 1)):
        for a, c in ((x0, -12.0), (12.0, x1)) if out > 0 else ((x0, x1),):
            b.box([(a + c) / 2.0, y + 12.4, zz], [c - a, 1.2, 0.3], BAR_RED)
    for xx in (x0 - 0.15, x1 + 0.15):
        b.box([xx, y + 12.4, (z0 + z1) / 2.0], [0.3, 1.2, z1 - z0], BAR_RED)
    wall_sign(b, 0.0, y + 11.2, z1 + 0.5, 22.0, 2.4,
              sign_decal("SNACK BAR", BAR_TRIM, "#f2f2f2", 9.0), "z+", BAR_TRIM)
    floor = y + FLOOR
    # the pads: two rows of eight across the dining room
    for z in (8.0, -2.0):
        for x in (-36.0, -27.0, -18.0, -9.0, 9.0, 18.0, 27.0, 36.0):
            deploy_pad(b, x, z, floor, "#7ae8e0", 5.0)
            b.safe_spawn(x, floor + 0.6, z, 0.0)
    # the counter, the kitchen behind it, the stair up to the roof
    b.box([-17.0, floor + 1.7, -18.0], [54.0, 3.4, 4.0], BAR_TRIM, studs=True)
    b.box([-17.0, floor + 3.6, -18.0], [55.0, 0.4, 4.6], "#e8e2d4")
    b.box([-43.0, floor + 2.2, -33.0], [6.0, 4.4, 8.0], "#a8adb2", material="metal")
    b.box([-43.0, floor + 4.5, -33.0], [5.0, 0.2, 7.0], "#ff8a3a", material="neon")
    b.box([-18.0, floor + 3.0, -39.0], [6.0, 6.0, 4.0], "#c43a32")
    b.box([-18.0, floor + 4.0, -36.9], [4.4, 3.6, 0.2], "#ffe8a0", material="neon")
    b.box([-4.0, floor + 3.5, -39.5], [6.0, 7.0, 3.0], "#e8e8e8", material="metal")
    b.box([8.0, floor + 2.0, -38.0], [8.0, 4.0, 5.0], "#8a8f94", material="metal")
    wall_sign(b, -10.0, y + 9.4, z0 + 2.4, 30.0, 3.0,
              sign_decal("HOT DOGS 25c  POPCORN  SODA", "#1b2a35", "#ffe28a", 10.0), "z+",
              "#1b2a35")
    flight(b, "x", 18.0, 44.0, -42.0, -34.0, floor, ROOF, CONCRETE_DARK, fill=floor)
    supply_ammo(b, -42.5, floor, 12.0, "x+")
    supply_med(b, 43.2, floor, 10.0, "x-")
    for (x, z) in ((-40.0, -28.0), (36.0, -24.0)):
        b.cyl([x, floor + 1.6, z], [5.0, 0.4, 5.0], "#e8e2d4")
        b.cyl([x, floor + 0.7, z], [0.8, 1.4, 0.8], STEEL_DARK)
    # the roof: the rail round the stair hole, the booth, the sign
    def rail(xa, xb, za, zb):
        b.box([(xa + xb) / 2.0, ROOF + 1.6, (za + zb) / 2.0], [xb - xa, 3.2, zb - za], STEEL,
              material="metal")
    rail(STAIR_HOLE[0], STAIR_HOLE[1], STAIR_HOLE[3], STAIR_HOLE[3] + 0.6)
    rail(STAIR_HOLE[0] - 0.6, STAIR_HOLE[0], STAIR_HOLE[2], STAIR_HOLE[3] + 0.6)
    bx0, bx1, bz0, bz1 = BOOTH
    building(b, BOOTH, ROOF, 9.0, "#d8d4c8", roof_colour="#3a3d42", floor_colour="#6a5a4a",
             doors={"z-": [(-4.0, 4.0, ROOF + 8.0)]},
             windows={"z+": [(-7.0, 7.0, ROOF + 4.0, ROOF + 7.0)],
                      "x-": [(-14.0, -6.0, ROOF + 4.0, ROOF + 7.0)],
                      "x+": [(-14.0, -6.0, ROOF + 4.0, ROOF + 7.0)]},
             glass=True, lights="#ffb86a")
    threshold(b, BOOTH, "z-", (-4.0, 4.0), y0=ROOF)
    bfloor = ROOF + FLOOR
    # the projector (its reels turn: a rig), the sound desk, film cans
    b.box([0.0, bfloor + 2.0, -6.0], [5.0, 4.0, 12.0], "#4a4f58", material="metal")
    b.box([0.0, bfloor + 4.6, -2.0], [3.0, 1.2, 4.0], "#3a3f46", material="metal")
    b.cyl([0.0, bfloor + 3.0, -0.6], [2.0, 2.0, 2.0], "#2a2d31", r=[math.pi / 2.0, 0, 0],
          collide=False)
    b.box([-9.0, bfloor + 1.8, -18.0], [10.0, 3.6, 4.0], "#5a4a3a", studs=True)
    b.box([-9.0, bfloor + 3.8, -18.4], [8.0, 0.4, 2.4], "#2a2a2a")
    for k in range(4):
        b.cyl([10.0, bfloor + 0.4 + k * 0.8, -18.0], [3.0, 0.8, 3.0], "#8a8f94",
              material="metal")
    b.set_lure(-9.0, bfloor, -14.0, "the movie's sound", "Crank up the movie's sound",
               "ll_movie", (0.0, 0.4, 206.0))
    supply_ammo(b, 34.0, ROOF, 8.0, "z-")
    # the flying saucer prop on its pole over the booth (it spins: a rig)
    b.cyl([10.0, ROOF + 10.2 + 4.0, -20.0], [1.0, 8.0, 1.0], STEEL_DARK, material="metal")
    # a giant hot dog on a post over the west end
    b.box([-38.0, ROOF + 4.0, 10.0], [1.0, 8.0, 1.0], STEEL_DARK)
    b.box([-38.0, ROOF + 9.0, 10.0], [12.0, 2.0, 3.0], "#d8a050")
    b.box([-38.0, ROOF + 10.4, 10.0], [14.0, 1.4, 2.0], "#b8482a")
    b.box([-38.0, ROOF + 11.2, 10.0], [10.0, 0.3, 0.6], "#f2c83a")
    # the fire stair up the west side, onto a landing at the gap in the rail
    flight(b, "z", -40.0, -6.0, -56.0, -50.0, BAR_Y, ROOF, STEEL_DARK, fill=BAR_Y)
    slab(b, rect(-56.0, -48.0, -6.0, 4.0), ROOF, 1.0, STEEL, studs=True, material="metal")
    for z in (-5.4, 3.4):
        b.box([-55.4, (BAR_Y + ROOF - 1.0) / 2.0, z], [0.8, ROOF - 1.0 - BAR_Y, 0.8], STEEL_DARK)
    rail_box = (rect(-56.0, -55.4, -6.0 + 0.0, 4.0), rect(-55.4, -48.0, 3.4, 4.0))
    for r in rail_box:
        b.box([(r[0] + r[1]) / 2.0, ROOF + 1.6, (r[2] + r[3]) / 2.0], [r[1] - r[0], 3.2,
                                                                       r[3] - r[2]], STEEL,
              material="metal")
    # propane round the back
    for x in (-20.0, -12.0):
        b.box([x, BAR_Y + 2.0, z0 - 4.0], [3.6, 4.0, 3.6], "#e8e8e8", material="metal")
    barrel_spot(b, -52.0, BAR_Y, -47.0)
    barrel_spot(b, 52.0, BAR_Y, -47.0)


# ================================================================== rows
def _rows(b: Area, s: Surfaces, rng: random.Random) -> None:
    for zc in ROWS_N + ROWS_S:
        hump = rect(-ROW_X, ROW_X, zc - 6.0, zc + 6.0)
        s.reserve(hump)
        slab(b, hump, HUMP_TOP, HUMP_TOP, HUMP, studs=True)
        # speaker posts along the crest
        for k in range(12):
            x = -132.0 + k * 24.0
            b.cyl([x, HUMP_TOP + 2.3, zc], [0.7, 4.6, 0.7], "#8a8f94", material="metal")
            b.box([x, HUMP_TOP + 5.2, zc], [1.4, 1.2, 1.0], "#5a5f66", material="metal")
            for side in (-1, 1):
                b.box([x + side * 1.2, HUMP_TOP + 4.9, zc], [1.0, 1.4, 1.2], "#3a3f46",
                      material="metal")
        # cars in about a third of the places, nose to the screen
        for k in range(13):
            x = -144.0 + k * 24.0
            if rng.random() > (0.42 if zc > 0 else 0.3) or (zc, k) in ((176.0, 9), (150.0, 1)):
                continue
            colour = rng.choice(CAR_COLOURS)
            car(b, x + rng.uniform(-2.0, 2.0), zc, "z", colour, length=10.0, y=HUMP_TOP)
    # a convertible in the front row with its top down, and a car that
    # took a speaker post with it on the way out
    b.box([72.0, HUMP_TOP + 1.85, 176.0], [5.0, 2.5, 10.0], "#e83a5a", material="metal")
    b.box([72.0, HUMP_TOP + 3.4, 174.0], [4.4, 0.6, 3.0], "#f2f2f2")
    b.box([72.0, HUMP_TOP + 3.8, 178.6], [4.6, 1.4, 0.4], "#8fb8c8", alpha=0.5)
    car(b, 22.0, 59.0, "x", "#3a5a8a", length=11.0, wrecked=True, y=0.3)
    # the old car whose battery is not quite dead (its lights and horn: a rig)
    car(b, -120.0, 150.0, "z", "#7ac8c8", length=10.0, y=HUMP_TOP)
    b.box([31.0, 0.65, 59.0], [4.6, 0.7, 0.7], "#8a8f94", material="metal")


# ============================================================== entrance
def _entrance(b: Area, s: Surfaces, rng: random.Random) -> None:
    # the box office in the middle of the road in, under its canopy
    booth = rect(-6.0, 6.0, -200.0, -186.0)
    s.reserve(booth)
    building(b, booth, 0.0, 9.0, BAR_WALL, roof_colour=BAR_RED, floor_colour=TILE,
             doors={"z-": [(-4.0, 4.0, 7.4)]},
             windows={"x-": [(-196.0, -190.0, 3.4, 7.2)], "x+": [(-196.0, -190.0, 3.4, 7.2)]},
             glass=True, lights=WARM)
    threshold(b, booth, "z-", (-4.0, 4.0))
    b.box([0.0, FLOOR + 1.6, -190.0], [5.0, 3.2, 2.0], "#5a4a3a")
    for sx in (-1, 1):
        for z in (-203.0, -183.0):
            b.cyl([sx * 20.0, 6.4, z], [1.2, 12.8, 1.2], BAR_TRIM, material="metal")
    slab(b, rect(-22.0, 22.0, -205.0, -181.0), 13.6, 0.8, BAR_TRIM)
    for z in (-198.0, -188.0):
        strip_light(b, 0.0, z, 12.8, 36.0, "x", "#fff2b0")
    supply_med(b, 10.0, 0.3, -192.0, "x+")
    barrel_spot(b, 12.0, 0.3, -210.0)
    wall_sign(b, 0.0, 10.6, -200.4, 10.0, 1.8, sign_decal("TICKETS", BAR_RED, "#f2f2f2", 5.5),
              "z-", BAR_RED)
    # the marquee on its two pylons, facing the highway and the field
    for x in (40.0, 76.0):
        b.cyl([x, 22.0, -236.0], [3.0, 44.0, 3.0], "#2a3a4a", material="metal")
    b.box([58.0, 23.0, -236.0], [34.0, 14.0, 2.6], "#1a2430")
    for side, facing in ((-1, "z-"), (1, "z+")):
        z = -236.0 + side * 1.65
        wall_sign(b, 58.0, 25.6, z, 30.0, 3.4, sign_decal("TONIGHT  ATTACK OF THE BLOCK PEOPLE",
                                                          "#f2f2e6", "#1b1b1b", 8.8),
                  facing, "#f2f2e6")
        wall_sign(b, 58.0, 20.4, z, 30.0, 3.4, sign_decal("PLUS  IT CAME FROM HARROW COUNTY",
                                                          "#f2f2e6", "#c43a32", 8.8),
                  facing, "#f2f2e6")
    board_letters(b, 58.0, 34.6, -237.6, "STARLITE", 5.8, "#1a2430", "#ffd84a", facing="z-",
                  solid=False)
    board_letters(b, 58.0, 34.6, -234.4, "STARLITE", 5.8, "#1a2430", "#ffd84a", facing="z+",
                  solid=False)
    b.box([58.0, 34.6, -236.0], [36.0, 7.0, 3.2], "#1a2430", collide=False)
    # abandoned cars on the highway: everybody tried to leave at once
    for x, colour, along in ((-260.0, "#c8a83a", "x"), (-178.0, "#3a5a6a", "x"),
                             (-60.0, "#8a2a24", "x"), (110.0, "#f2f2f2", "z"),
                             (150.0, "#2a2a2a", "x"), (230.0, "#7ac8c8", "x")):
        car(b, x, -270.0 + rng.uniform(-3.0, 3.0), along, colour, length=11.0,
            wrecked=x in (-60.0, 150.0), y=0.3)
    post_sign(b, -30.0, -258.0, 0.0, 8.0, 14.0, 4.0,
              sign_decal("HARROW 12  ->", "#2f6a3a", "#f2f2f2", 3.5), "z-", "#2f6a3a")


# ============================================================== railway
def _railway(b: Area, s: Surfaces, rng: random.Random) -> None:
    x0, x1 = EMBANK
    s.reserve(rect(x0, x1, -280.0, 280.0))
    ridge(b, x0, x1, -280.0, 280.0, 3, RAIL_TOP / 3.0, [BALLAST, "#6e685c", BALLAST],
          inset=0.0, inset_x=4.0)
    # the track: two rails on sleepers
    for z in range(-276, 280, 8):
        b.box([TRACK_X, RAIL_TOP + 0.15, float(z)], [9.0, 0.3, 1.6], "#4a3a2a", collide=False)
    for dx in (-2.5, 2.5):
        b.box([TRACK_X + dx, RAIL_TOP + 0.5, 0.0], [0.5, 0.4, 559.0], "#8a8f94",
              material="metal")
    # the stalled freight: a diesel, boxcars, a tank car
    top = RAIL_TOP
    def underframe(z0, z1):
        b.box([TRACK_X, top + 0.7, (z0 + z1) / 2.0], [7.0, 1.4, z1 - z0 - 2.0], "#1b1d20")
        for z in (z0 + 4.0, z1 - 4.0):
            for dx in (-2.6, 2.6):
                b.cyl([TRACK_X + dx, top + 1.1, z], [2.2, 1.0, 2.2], "#2a2d31",
                      r=[0, 0, math.pi / 2.0], collide=False)
    # the locomotive
    underframe(150.0, 178.0)
    b.box([TRACK_X, top + 5.6, 160.0], [7.6, 8.4, 18.0], "#e8b81a", material="metal")
    b.box([TRACK_X, top + 6.6, 173.0], [8.6, 10.4, 8.0], "#1b1d20", material="metal")
    b.box([TRACK_X, top + 9.0, 177.1], [6.0, 3.0, 0.2], "#8fb8c8", alpha=0.6, collide=False)
    b.box([TRACK_X, top + 4.4, 177.2], [1.6, 1.6, 0.4], "#fff6c0", material="neon")
    b.box([TRACK_X, top + 10.0, 151.0], [4.0, 1.2, 2.0], "#3a3f46")
    # boxcars: the second one stands open, the third has crates to climb it
    cars = [(118.0, "#8a3a2a"), (88.0, "#5a3a2a"), (-30.0, "#6a4a2a"), (-60.0, "#8a3a2a"),
            (-92.0, "#3a4a5a")]
    for z0, colour in cars:
        underframe(z0, z0 + 26.0)
        b.box([TRACK_X, top + 1.4 + 4.3, z0 + 13.0], [8.6, 8.6, 26.0], colour, studs=True)
        for side in (-1, 1):
            b.box([TRACK_X + side * 4.36, top + 5.4, z0 + 13.0], [0.12, 6.6, 8.0], "#2a2d31",
                  collide=False)
    # the open boxcar: a floor, walls with both doors rolled back, a roof
    z0 = 0.0
    underframe(z0, z0 + 26.0)
    box = rect(TRACK_X - 4.3, TRACK_X + 4.3, z0, z0 + 26.0)
    slab(b, box, top + 2.0, 0.6, "#5a4030")
    room_walls(b, box, 0.6, top + 2.0, top + 10.4, "#7a4a2a",
               doors={"x-": [(z0 + 9.0, z0 + 17.0, top + 9.4)],
                      "x+": [(z0 + 9.0, z0 + 17.0, top + 9.4)]})
    slab(b, box, top + 11.0, 0.6, "#5a3a2a", studs=True)
    b.box([TRACK_X - 1.0, top + 3.6, z0 + 4.0], [5.0, 3.2, 4.0], WOOD, studs=True)
    supply_ammo(b, TRACK_X, top + 2.0, z0 + 22.0, "z-")
    # the tank car: FLAMMABLE, and the fuel drums beside it
    underframe(32.0, 56.0)
    b.box([TRACK_X, top + 1.4 + 3.6, 44.0], [7.6, 7.2, 20.0], "#1b1d20", material="metal")
    b.box([TRACK_X, top + 1.4 + 7.6, 44.0], [2.0, 0.8, 2.0], "#3a3f46", material="metal")
    for side, facing in ((-1, "x-"), (1, "x+")):
        wall_sign(b, TRACK_X + side * 4.15, top + 5.0, 44.0, 9.0, 2.2,
                  sign_decal("FLAMMABLE", "#c43a32", "#f2f2f2", 4.0), facing, "#c43a32")
    barrel_spot(b, TRACK_X + 10.0, RAIL_TOP, 36.0)
    barrel_spot(b, TRACK_X + 10.0, RAIL_TOP, 52.0)
    # crates up onto the third boxcar's roof
    crate(b, TRACK_X + 7.2, top, -14.0, 5.0, WOOD)
    crate(b, TRACK_X + 7.2, top + 5.0, -18.0, 5.0, WOOD_LIGHT)
    # the water tower beside the line, past the end of the screen
    for dx in (-8.0, 8.0):
        for dz in (-8.0, 8.0):
            b.cyl([-150.0 + dx, 18.0, 252.0 + dz], [1.6, 36.0, 1.6], "#5a5f66", material="metal")
    for y in (12.0, 24.0):
        for dz in (-8.0, 8.0):
            b.box([-150.0, y, 252.0 + dz], [16.0, 0.6, 0.6], "#5a5f66", collide=False)
    b.cyl([-150.0, 43.0, 252.0], [24.0, 14.0, 24.0], "#c8c4b8", material="metal")
    b.cone([-150.0, 52.0, 252.0], [25.0, 4.0, 25.0], "#8a3a2a")
    wall_sign(b, -150.0, 43.0, 239.8, 16.0, 3.4, sign_decal("STARLITE", "#c8c4b8", "#c43a32",
                                                            4.7), "z-", "#c8c4b8")
    # the woods behind the line
    for k in range(22):
        z = -250.0 + k * 24.0 + rng.uniform(-6.0, 6.0)
        pine(b, rng.uniform(-272.0, -246.0), z, 0.0, rng.uniform(1.6, 2.4))


# ================================================================= corn
def _corn(b: Area, s: Surfaces, rng: random.Random) -> None:
    clearing = (214.0, 246.0, 40.0, 72.0)          # the scarecrow's
    s.reserve(rect(CORN_X[0], CORN_X[1] + 3.0, CORN_Z[0], CORN_Z[1]))
    gaps = [(-70.0, -62.0), (10.0, 18.0), (100.0, 108.0), (190.0, 198.0)]
    x = CORN_X[0] + 2.0
    while x < CORN_X[1]:
        cuts = list(gaps) + [(z, z + 7.0) for z in (rng.uniform(-130, 250),
                                                    rng.uniform(-130, 250))]
        if clearing[0] - 2 < x < clearing[1] + 2:
            cuts.append((clearing[2], clearing[3]))
        cuts.sort()
        z = CORN_Z[0]
        for a, c in cuts + [(CORN_Z[1], CORN_Z[1])]:
            if a - z > 4.0:
                b.box([x, 5.0, (z + a) / 2.0], [2.4, 10.0, a - z], CORN, studs=True,
                      material="grass")
                b.box([x, 10.3, (z + a) / 2.0], [1.4, 0.6, a - z - 0.6], TASSEL)
            z = max(z, c)
        x += 8.0
    # the scarecrow in its clearing, the crows on him (a rig)
    cx, cz = (clearing[0] + clearing[1]) / 2.0, (clearing[2] + clearing[3]) / 2.0
    b.box([cx, 6.0, cz], [1.0, 12.0, 1.0], WOOD_DARK)
    b.box([cx, 9.0, cz], [10.0, 0.8, 0.8], WOOD_DARK)
    b.box([cx, 8.6, cz], [3.2, 3.6, 2.0], "#8a3a2a")
    b.box([cx, 11.4, cz], [2.4, 2.4, 2.4], "#d8c08a")
    b.cyl([cx, 12.9, cz], [4.4, 0.4, 4.4], "#b89a5a")
    b.cyl([cx, 13.6, cz], [2.4, 1.2, 2.4], "#b89a5a")
    # a tractor left at the edge of the corn
    tx, tz = 166.0, -100.0
    b.box([tx, 3.0, tz], [5.0, 4.0, 10.0], "#3a7a3a", material="metal")
    b.box([tx, 6.6, tz - 2.0], [4.4, 3.2, 4.0], "#2a3a2a")
    for dz, size in ((-3.4, 4.4), (3.6, 2.6)):
        for side in (-1, 1):
            b.cyl([tx + side * 3.1, size / 2.0, tz + dz], [size, 1.2, size], "#1b1d20",
                  r=[0, 0, math.pi / 2.0], collide=False)
            b.box([tx + side * 3.1, size / 2.0, tz + dz], [1.2, size, size], "#1b1d20",
                  alpha=0.0)
    barrel_spot(b, 162.0, 0.3, -86.0)


# ============================================================== junkyard
def _junkyard(b: Area, s: Surfaces, rng: random.Random) -> None:
    x0, x1, z0, z1 = JUNK
    chain_fence(b, x0, z1, -132.0, z1, 9.0)
    chain_fence(b, -116.0, z1, x1, z1, 9.0)
    chain_fence(b, x1, z0, x1, -214.0, 9.0)
    chain_fence(b, x1, -200.0, x1, z1, 9.0)
    # crushed cars, stacked in steps you can climb
    colours = ["#5a3a2a", "#3a4a5a", "#6a5a3a", "#4a4a4a", "#7a3a2a", "#3a5a3a"]
    for (sx, sz, n) in ((-176.0, -186.0, 3), (-176.0, -192.0, 2), (-176.0, -198.0, 1),
                        (-150.0, -246.0, 3), (-139.0, -246.0, 2), (-128.0, -246.0, 1),
                        (-80.0, -246.0, 2)):
        for k in range(n):
            b.box([sx, 1.2 + k * 2.4, sz], [11.0, 2.4, 6.0], rng.choice(colours), studs=True,
                  material="metal")
    # tyres
    for (tx, tz) in ((-150.0, -180.0), (-142.0, -182.0), (-96.0, -178.0)):
        for k in range(3):
            b.cyl([tx, 0.6 + k * 1.2, tz], [4.0, 1.2, 4.0], "#1b1d20")
    # the scrap crane and its magnet (the magnet swings: a rig)
    b.box([-150.0, 4.0, -212.0], [10.0, 8.0, 10.0], "#e8b81a", material="metal")
    b.box([-150.0, 10.0, -212.0], [6.0, 4.0, 6.0], "#2a2d31")
    b.box([-150.0, 20.0, -212.0], [2.0, 16.0, 2.0], "#e8b81a", material="metal")
    # the manager's trailer: a bed, the TV, the fridge, and what he kept
    trailer = rect(-112.0, -78.0, -206.0, -190.0)
    s.reserve(rect(-114.0, -76.0, -208.0, -186.0))
    slab(b, rect(-114.0, -76.0, -208.0, -188.0), 1.2, 1.2, "#5a5f66")
    building(b, trailer, 1.2, 8.0, "#e8e2c8", roof_colour="#8a8f94", floor_colour="#8a6f52",
             doors={"z+": [(-103.0, -95.0, 8.4)]},
             windows={"z+": [(-110.0, -105.0, 4.4, 7.6), (-90.0, -82.0, 4.4, 7.6)],
                      "z-": [(-104.0, -88.0, 4.4, 7.6)]}, glass=True, lights=WARM)
    threshold(b, trailer, "z+", (-103.0, -95.0), y0=1.2)
    tfloor = 1.2 + FLOOR
    b.box([-106.0, tfloor + 0.6, -200.0], [8.0, 1.2, 8.0], "#6a4a6a", studs=True)
    b.box([-84.0, tfloor + 2.2, -202.4], [4.0, 4.4, 3.0], "#e8e8e8")
    supply_med(b, -83.0, tfloor, -196.0, "x-")
    supply_ammo(b, -95.0, tfloor, -202.0, "z+")
    barrel_spot(b, -124.0, 0.0, -196.0)
    barrel_spot(b, -168.0, 0.0, -232.0)
    post_sign(b, -124.0, -164.0, 0.0, 7.0, 14.0, 2.6,
              sign_decal("SAL'S SALVAGE  NO TRESPASSING", "#e8b81a", "#1b1b1b", 5.4),
              "z+", "#e8b81a")


# ============================================================== putt-putt
def _green(b: Area, g, top: float = 0.6) -> None:
    """A putting green on a low platform, kerbed all round."""
    slab(b, g, top, top, "#3a8a3a", studs=True)
    gx0, gx1, gz0, gz1 = g
    for (cx, cz, w, d) in (((gx0 + gx1) / 2.0, gz0 + 0.4, gx1 - gx0, 0.8),
                           ((gx0 + gx1) / 2.0, gz1 - 0.4, gx1 - gx0, 0.8),
                           (gx0 + 0.4, (gz0 + gz1) / 2.0, 0.8, gz1 - gz0 - 1.6),
                           (gx1 - 0.4, (gz0 + gz1) / 2.0, 0.8, gz1 - gz0 - 1.6)):
        b.box([cx, top + 0.4, cz], [w, 0.8, d], "#e8e2d4")


def _putt(b: Area, s: Surfaces) -> None:
    greens = [rect(56.0, 72.0, -236.0, -206.0), rect(78.0, 112.0, -252.0, -240.0),
              rect(56.0, 72.0, -256.0, -242.0), rect(150.0, 166.0, -254.0, -230.0),
              rect(150.0, 166.0, -222.0, -200.0)]
    for g in greens:
        s.reserve(g)
        _green(b, g)
    # the hill hole: a green that climbs in three steps
    hill = rect(80.0, 110.0, -232.0, -212.0)
    s.reserve(hill)
    tier_stack(b, [[hill], [rect(86.0, 104.0, -228.0, -216.0)],
                   [rect(91.0, 99.0, -225.0, -219.0)]], 0.0, [1.4],
               ["#3a8a3a", "#45964a", "#3a8a3a"])
    b.cyl([95.0, 4.4, -222.0], [1.4, 0.4, 1.4], "#1b1d20", collide=False)
    # the windmill stands on the first green (its sails turn: a rig)
    b.box([64.0, 0.6 + 8.0, -216.0], [8.0, 16.0, 8.0], "#c8a878", studs=True)
    b.cone([64.0, 0.6 + 18.5, -216.0], [10.0, 5.0, 10.0], "#8a3a2a")
    b.box([64.0, 0.6 + 2.5, -220.06], [3.0, 5.0, 0.12], "#3a2a1a", collide=False)
    # the clubhouse: ammunition and first aid on the counter
    hut = rect(60.0, 86.0, -198.0, -180.0)
    s.reserve(hut)
    building(b, hut, 0.0, 10.0, "#f2e6c8", roof_colour="#3a8a3a", floor_colour=TILE,
             doors={"z-": [(68.0, 76.0, 8.0)]}, windows={"x+": [(-194.0, -184.0, 3.6, 7.6)]},
             glass=True, lights=WARM)
    threshold(b, hut, "z-", (68.0, 76.0))
    b.box([73.0, FLOOR + 1.7, -183.4], [20.0, 3.4, 2.4], "#3a8a3a", studs=True)
    for k in range(5):
        b.box([66.0 + k * 1.2, FLOOR + 4.6 + 0.0, -182.3], [0.3, 2.6, 0.3], "#c8c8c8",
              collide=False)
    supply_ammo(b, 65.2, FLOOR, -190.0, "x+")
    supply_med(b, 81.2, FLOOR, -192.0, "x-")
    wall_sign(b, 73.0, 11.0, -198.4, 16.0, 3.0, sign_decal("STARLITE PUTT-PUTT", "#3a8a3a",
                                                           "#f2f2f2", 5.3), "z-", "#3a8a3a")
    barrel_spot(b, 92.0, 0.0, -186.0)
    barrel_spot(b, 120.0, 0.0, -252.0)
    # the dinosaur: fibreglass, climbable up its tail onto its back
    s.reserve(rect(128.0, 152.0, -250.0, -170.0))
    dx = 140.0
    b.box([dx, 15.0, -200.0], [10.0, 8.0, 20.0], "#5a8a3a", studs=True)
    for side in (-1, 1):
        b.box([dx + side * 2.5, 5.5, -196.0], [3.5, 11.0, 5.0], "#4f7a34")
        b.box([dx + side * 4.0, 14.0, -189.0], [1.4, 1.4, 3.0], "#4f7a34")
    b.box([dx, 21.0, -188.0], [6.0, 6.0, 6.0], "#5a8a3a")
    b.box([dx, 25.0, -181.0], [7.0, 6.0, 12.0], "#5a8a3a", studs=True)
    b.box([dx, 21.5, -180.2], [6.0, 2.0, 10.0], "#4f7a34")
    for side in (-1, 1):
        b.box([dx + side * 3.56, 26.4, -179.0], [0.12, 1.0, 1.4], "#f2e03a", material="neon",
              collide=False)
    for k in range(4):
        b.box([dx - 2.2 + k * 1.45, 22.2, -174.8], [0.6, 0.8, 0.6], "#f2f2e6")
    for k in range(9):
        top = 17.0 - k * 2.0
        width = 8.0 - k * 0.5
        b.box([dx, top - 1.2, -212.0 - k * 4.0], [width, 2.4, 4.0], "#5a8a3a", studs=True)
    post_sign(b, 122.0, -176.0, 0.0, 4.0, 12.0, 2.6,
              sign_decal("DON'T FEED REX", "#f2f2f2", "#3a6a2a", 4.6), "z-", "#f2f2f2")


# ================================================================ lights
def _lights(b: Area) -> None:
    for x in (-156.0, 156.0):
        for z in (186.0, 112.0, 30.0, -50.0, -110.0):
            lamp_post(b, x, z, h=20.0, light=SODIUM, y=0.3)
    for x, z in ((-60.0, -150.0 - 14.0), (60.0, -164.0), (-130.0, -172.0), (110.0, -172.0)):
        lamp_post(b, x, z, h=16.0, light=SODIUM)


# ================================================================== rigs
def _rigs(b: Area) -> None:
    b.rig("movie_screen", 0.0, (BASE_TOP + 60.8) / 2.0, FACE_Z - 0.05, math.pi,
          w=158.0, h=49.4)
    b.rig("projector_beam", 0.0, ROOF + FLOOR + 4.6, 2.2, 0.0,
          to_p=[0.0, (BASE_TOP + 60.8) / 2.0, FACE_Z - 0.2], w=158.0, h=49.4)
    b.rig("film_reels", 0.0, ROOF + FLOOR + 6.6, -6.0, 0.0)
    b.rig("flying_saucer", 10.0, ROOF + 10.2 + 8.6, -20.0, 0.0)
    b.rig("swing_set", -36.0, 0.4 + 12.0, 212.0, 0.0, n=3, span=24.0)
    b.rig("merry_go_round", 32.0, 0.4 + 0.8, 208.0, 0.0, r=6.2)
    b.rig("marquee_lights", 58.0, 23.0, -236.0, 0.0, w=34.0, h=14.0, d=2.6,
          star_p=[58.0, 44.4, -236.0])
    b.rig("golf_windmill", 64.0, 12.6, -220.2, 0.0, r=9.0)
    b.rig("scrap_magnet", -150.0, 28.0, -212.0, 0.0, arm=16.0)
    b.rig("crows", 230.0, 13.0, 56.0, 0.0, n=6)
    b.rig("jalopy", -120.0, HUMP_TOP, 150.0, 0.0)
    for x, z in ((-156.0, 186.0), (156.0, 112.0), (-156.0, 30.0), (156.0, -50.0),
                 (-60.0, -164.0), (110.0, -172.0)):
        b.rig("moth_swarm", x, (20.0 if abs(x) == 156.0 else 16.0) - 1.4 + 0.3, z, 0.0)


# ================================================================ spawns
def _zombie_spawns(b: Area) -> None:
    pts = [
        # the corn
        (266, -132, "corn"), (234, -100, "corn"), (202, -20, "corn"), (266, 22, "corn"),
        (202, 140, "corn"), (250, 150, "corn"), (218, 230, "corn"), (266, 262, "corn"),
        # behind the screen, the woods
        (-120, 272, ""), (-20, 272, ""), (60, 272, ""), (130, 266, ""),
        (-262, -200, ""), (-262, -60, ""), (-262, 80, ""), (-262, 200, ""),
        # the jammed highway
        (-250, -271, ""), (-120, -271, ""), (30, -271, ""), (170, -271, ""), (262, -271, ""),
        # the junkyard and the putt-putt
        (-182, -250, ""), (-70, -230, ""), (166, -254, ""),
    ]
    for x, z, tag in pts:
        b.zombie_spawn(float(x), float(z), tag)
    # along the line, up on the embankment
    for z in (-270.0, 270.0, 220.0):
        b.zombie_spawn(TRACK_X, z, "rail", y=RAIL_TOP)
    # the ditch
    for x in (-120.0, 120.0):
        b.zombie_spawn(x, -154.0, "ditch", y=DITCH_BED)
