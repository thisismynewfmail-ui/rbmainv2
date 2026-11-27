"""Blackpowder Fireworks Co. -- the works, the night before the Fourth.

Layout (north is +z)::

   z +280 ------------------------------- the tree line ---------------------------------
          THE PROVING     THE SHOW FIELD: the lancework frame, the mortar      BIG BERTHA
          GROUND (the     racks in rows, the firing line of sandbags,
          wheel frame,    THE FIRING BUNKER with the earth heaped over it      THE BURN PIT
          the spotter's   (the lure)
          tower)
   z +100 ==============================================================================
          THE MAGAZINES   THE TUBE SHOP   THE GIANT ROCKET   THE STAR RACKS   THE MIXING SHEDS
          (four, each                     (its gantry)       (the catwalk)    (each in its own
          under its                                                            horseshoe of
          mound)          THE ASSEMBLY HALL (BLACKPOWDER on the roof)          earth)
   z  -80 ===================== the yard road ===========================  THE CRATER
          THE RAIL SIDING (the boxcars, the dock) ...........................  (Shed No. 4)
          THE TEST POND   THE FIRE HALL   THE OFFICE (the safe room)     THE OUTLET STORE
                          the water tower                                (the gorilla on the roof)
   z -280 --------------------------------- the county road -----------------------------

Everybody deploys in the office, among the order books and the sample cases.

What makes it this place:

* **Built to go up one piece at a time.**  Nothing in a fireworks works
  stands near anything else without earth between: the magazines are
  buried in mounds, every mixing shed stands in its own horseshoe of earth
  open to the path, traverses shield the doors.  Climb them, fight over
  them -- and there are fuel drums everywhere.
* **The lure.**  In the firing bunker at the edge of the show field: light
  the finale, and for half a minute the whole show goes up -- the racks
  firing in rows, the wheels spinning, the lancework spelling it out over
  the field -- and every one of the dead comes to watch.
* **High ground.**  The giant rocket's gantry, the hall roof up its outside
  stair, the star racks' catwalk, the tube shop roof off the heap of
  bundles, the spotter's tower, the magazine mounds, the outlet roof with
  the gorilla.
* **The crater.**  Where Shed No. 4 stood until the third of July, 1958.
"""
from __future__ import annotations

import math
import random
from typing import List, Optional, Sequence, Tuple

from .kit import (
    ASPHALT, CONCRETE, CONCRETE_DARK, CONCRETE_LIGHT, FLOOR, HAZARD, LINE_YELLOW, PAVEMENT,
    STEEL, STEEL_DARK, WARM, WOOD, WOOD_DARK, WOOD_LIGHT, Area, Surfaces, barrel_spot, boundary,
    building, car, carve, crate, deploy_pad, flight, gable, lamp_post, plate, post_sign, rect,
    sandbags, sign_decal, slab, supply_ammo, supply_med, threshold, van, wall_sign, watchtower)
from ..relay.kit import board_letters, mound, pine, rails, tree

Rect = Tuple[float, float, float, float]

HALF = 280.0
SKY = {"top": "#070a1c", "horizon": "#3a2238", "sun": [0.3, 0.42, 0.7],
       "clouds": 0.25, "tint": "#d0b8d8"}
AMBIENT = "#5a4a5a"

GRASS = "#4a5a30"
EARTH = "#56663a"
EARTH_HI = "#627044"
RED = "#b8282a"
GOLD = "#e8b83a"
CREAM = "#efe6cc"
BRICK_RED = "#9a3a2a"
BALLAST = "#6e6a62"
GRAVEL = "#8a8270"
TUBE = "#2a2c2a"
CHAR = "#262220"

OFFICE = rect(-40.0, 40.0, -204.0, -160.0)
OFFICE_H = 13.0
TRACK = rect(-280.0, 104.0, -152.0, -140.0)
RAILS_Z = (-148.0, -144.0)
DOCK = rect(-140.0, -60.0, -140.0, -132.0)
DOCK_TOP = 2.4
HALL = rect(-60.0, 60.0, -60.0, -10.0)
HALL_H = 14.0
TUBES = rect(-130.0, -80.0, 10.0, 60.0)
TUBES_TOP = 12.6
CATWALK = rect(80.0, 150.0, 16.0, 54.0)
CATWALK_TOP = 12.6
ROCKET = (0.0, 56.0)
GANTRY = rect(-26.0, -12.0, 44.0, 68.0)
DECK1, DECK2 = 10.0, 20.0
FIRING = rect(-12.0, 12.0, 120.0, 132.0)
FIELD = rect(-160.0, 160.0, 140.0, 262.0)
STORE = rect(130.0, 230.0, -232.0, -190.0)
STORE_H = 12.0
POND = rect(-252.0, -168.0, -246.0, -186.0)
POND_BED = -4.0
POND_WATER = -1.0
RAFT = (-222.0, -220.0)
CRATER = rect(96.0, 152.0, -134.0, -86.0)
BURN = rect(206.0, 238.0, 132.0, 160.0)
FIREHALL = rect(-136.0, -96.0, -238.0, -206.0)
TOWER = (-64.0, -228.0)
MAG_X = (-258.0, -222.0)
MAGS = (-100.0, -40.0, 20.0, 80.0)
SHEDS = ((192.0, -60.0, "BLACK POWDER"), (192.0, 0.0, "STROBE"), (192.0, 60.0, "FLASH"),
         (246.0, -60.0, "COLOURS"), (246.0, 0.0, "STARS"), (246.0, 60.0, "LIFT CHARGE"))
RACK_ROWS = ((172.0, (-125.0, -75.0, -25.0, 25.0, 75.0, 125.0)),
             (200.0, (-100.0, -50.0, 0.0, 50.0, 100.0)),
             (228.0, (-125.0, -75.0, -25.0, 25.0, 75.0, 125.0)))
WHEELS = (-254.0, -236.0, -218.0, -200.0)
WHEEL_Z = 212.0
LANCE_Z = 250.0
BERTHA = (232.0, 214.0)


def build(b: Area) -> None:
    rng = random.Random(0xF12E)
    b.extra.update({"weather": "embers", "accent": "#ffb84a"})
    s = Surfaces(b)
    _ground(b, s)
    boundary(b, 30.0, "#1e2a1a", "#18221a", rng, horizon="forest")
    _office(b, s)
    _fire_hall(b, s)
    _water_tower(b, s)
    _store(b, s)
    _siding(b, s)
    _pond(b, s)
    _crater(b, s)
    _hall(b, s)
    _tube_shop(b, s)
    _star_racks(b, s)
    _rocket(b, s)
    _magazines(b, s)
    _sheds(b, s)
    _show_field(b, s)
    _proving_ground(b, s)
    _north_east(b, s)
    _country(b, s, rng)
    _paths(b, s)
    _rigs(b)
    _zombie_spawns(b)
    for x, z, name in ((0, -182, "the office"), (0, 200, "the show field"), (0, 126, "the firing bunker"),
                       (-215, -10, "the magazines"), (219, 0, "the mixing sheds"), (0, -35, "the assembly hall"),
                       (-105, 35, "the tube shop"), (115, 35, "the star racks"), (0, 30, "the giant rocket"),
                       (180, -244, "the outlet store"), (180, -180, "the gorilla"), (-40, -146, "the rail siding"),
                       (-100, -128, "the loading dock"), (-160, -216, "the test pond"), (124, -110, "the crater"),
                       (-227, 196, "the proving ground"), (-206, 150, "the spotter's tower"),
                       (222, 146, "the burn pit"), (232, 202, "Big Bertha"), (-116, -248, "the fire hall"),
                       (-64, -214, "the water tower")):
        b.landmark(float(x), float(z), name)
    b.camera(-40.0, 34.0, 10.0, 0.0, 24.0, 60.0)
    b.camera(0.0, 22.0, 96.0, 0.0, 6.0, 210.0)
    b.camera(150.0, 18.0, -40.0, 220.0, 2.0, 10.0)
    b.camera(110.0, 20.0, -150.0, 180.0, 14.0, -214.0)


# ================================================================ helpers
def _earthwork(b: Area, outer: Rect, hollow: Optional[Rect], levels: int, rise: float,
               shrink: float, grow: float, colours: Sequence[str], y0: float = 0.0) -> None:
    """Earth in tiers you can walk up: tier k is ``outer`` drawn in by
    ``shrink`` k times, less ``hollow`` let out by ``grow`` k times (so a
    berm round a shed leans back from it as it rises), ``rise`` above the
    tier under it."""
    for k in range(levels):
        o = rect(outer[0] + shrink * k, outer[1] - shrink * k, outer[2] + shrink * k, outer[3] - shrink * k)
        holes: List[Rect] = []
        if hollow is not None:
            holes.append(rect(hollow[0] - grow * k, hollow[1] + grow * k, hollow[2] - grow * k,
                              hollow[3] + grow * k))
        plate(b, carve(o, holes), y0 + rise * (k + 1), rise, colours[k % len(colours)], studs=True,
              material="grass")


def _hydrant(b: Area, x: float, z: float) -> None:
    b.cyl([x, 1.2, z], [1.4, 2.4, 1.4], "#c42b20", material="metal")
    b.cyl([x, 2.6, z], [1.6, 0.4, 1.6], "#c42b20", material="metal")
    b.box([x, 1.6, z], [2.4, 0.6, 0.6], "#c42b20", material="metal")


def _mortar_rack(b: Area, x: float, z: float) -> None:
    """A rack of mortar tubes on the grass: ten in two rows in a wooden
    frame, the shells already down them."""
    b.box([x, 0.5, z], [12.0, 1.0, 5.0], WOOD_DARK)
    for i in range(5):
        for j in range(2):
            b.cyl([x - 4.4 + i * 2.2, 1.0 + 1.6, z - 1.1 + j * 2.2], [1.6, 3.2, 1.6], TUBE)
    for side in (-1, 1):
        b.box([x + side * 5.7, 1.0 + 1.5, z], [0.6, 3.0, 5.0], WOOD)


# ================================================================ ground
def _ground(b: Area, s: Surfaces) -> None:
    h = b.half + b.margin
    holes = [POND, CRATER, BURN]
    for r in holes:
        s.reserve(r)
    pieces = carve(rect(-h, h, -h, h), holes)
    plate(b, pieces, 0.0, 0.6, GRASS, studs=True, material="grass")
    plate(b, pieces, -0.6, 5.4, "#4a3a2a")


# ================================================================ office
def _office(b: Area, s: Surfaces) -> None:
    """The office: the order books, the sample cases, the old man in his
    frame -- the safe room.  Brick, a porch on the road side, the flag."""
    x0, x1, z0, z1 = OFFICE
    s.reserve(OFFICE)
    building(b, OFFICE, 0.0, OFFICE_H, BRICK_RED, roof_colour="#3a3a3a", floor_colour="#8a7a62",
             doors={"z+": [(-8.0, 8.0, 10.0)], "z-": [(-8.0, 8.0, 10.0)]},
             windows={"z+": [(-34.0, -16.0, 4.0, 9.0), (16.0, 34.0, 4.0, 9.0)],
                      "z-": [(-34.0, -16.0, 4.0, 9.0), (16.0, 34.0, 4.0, 9.0)],
                      "x-": [(-196.0, -168.0, 4.0, 9.0)],
                      "x+": [(-200.0, -188.0, 4.0, 9.0), (-176.0, -164.0, 4.0, 9.0)]},
             glass=True, lights=WARM)
    threshold(b, OFFICE, "z+", (-8.0, 8.0))
    threshold(b, OFFICE, "z-", (-8.0, 8.0))
    gable(b, OFFICE, OFFICE_H + 1.2, "#3a3a3a", "x", tiers=3, rise=1.5)
    wall_sign(b, 0.0, 11.9, z0 - 0.35, 34.0, 1.8,
              sign_decal("BLACKPOWDER FIREWORKS CO.  EST. 1911", BRICK_RED, GOLD, 34.0 / 1.8), "z-", BRICK_RED)
    # the porch over the front door, on two white posts
    slab(b, rect(-12.0, 12.0, z0 - 8.0, z0), 10.6, 0.6, "#3a3a3a")
    for x in (-11.4, 11.4):
        b.box([x, 5.0, z0 - 7.4], [1.2, 10.0, 1.2], CREAM)
    # the hedges either side of the front walk, the flag on its pole
    for x in (-11.0, 11.0):
        b.box([x, 1.0, -231.0], [2.0, 2.0, 38.0], "#2a4a26", studs=True)
    b.box([-24.0, 0.6, -226.0], [3.0, 1.2, 3.0], CONCRETE)
    b.cyl([-24.0, 1.2 + 15.0, -226.0], [1.0, 30.0, 1.0], "#d8d8d8", material="metal")
    b.sphere([-24.0, 31.6, -226.0], [1.6, 1.6, 1.6], GOLD, material="metal")
    post_sign(b, 22.0, -250.0, 0.0, 3.0, 12.0, 2.4,
              sign_decal("VISITORS REPORT TO THE OFFICE", CREAM, BRICK_RED, 5.0), "z-", CREAM)
    floor = FLOOR
    for z in (-174.0, -190.0):
        for k in range(8):
            x = -33.0 + k * 9.4
            deploy_pad(b, x, z, floor, "#ffb84a", 4.8)
            b.safe_spawn(x, floor + 0.6, z, 0.0)
    # the sample cases along the west wall: a shell of every kind under glass
    shells = ["#c83a3a", "#3a6ac8", "#e8c83a", "#3ac86a", "#c83ac8", "#e8e8e8"]
    for k, z in enumerate((-196.0, -182.0, -168.0)):
        b.box([x0 + 3.0, floor + 0.6, z], [2.0, 1.2, 10.0], WOOD_DARK)
        b.box([x0 + 3.0, floor + 1.2 + 1.2, z], [2.0, 2.4, 10.0], "#b8d8e8", material="glass", alpha=0.35)
        for j in range(3):
            b.sphere([x0 + 3.0, floor + 1.2 + 0.8, z - 3.0 + j * 3.0], [1.4, 1.4, 1.4], shells[(k * 3 + j) % 6])
    # the order desk with the ledger open on it, and the safe
    b.box([22.0, floor + 1.5, -199.0], [12.0, 3.0, 3.0], WOOD)
    b.box([22.0, floor + 3.0 + 0.15, -199.0], [3.0, 0.3, 2.0], CREAM)
    b.box([34.0, floor + 2.5, -199.0], [4.0, 5.0, 4.0], "#2a2a2e", material="metal")
    b.box([34.0, floor + 2.8, -201.06], [1.0, 1.0, 0.12], GOLD, material="metal", collide=False)
    # filing cabinets under the old man, who founded the place and is
    # watching to see what you do with it
    for z in (-185.5, -182.0, -178.5):
        b.box([37.0, floor + 2.2, z], [2.0, 4.4, 3.0], "#6a6f76", material="metal")
    b.box([37.94, 8.4, -182.0], [0.12, 4.4, 3.6], GOLD, collide=False)
    b.box([37.82, 8.4, -182.0], [0.12, 3.6, 2.8], "#3a2a2a", collide=False)
    b.sphere([37.7, 8.6, -182.0], [0.12, 1.6, 1.2], "#e8c8a8", collide=False)
    for side in (-1, 1):
        b.box([37.7, 8.2, -182.0 + side * 0.65], [0.12, 1.0, 0.3], "#d8d8d8", collide=False)
    b.box([37.7, 9.8, -182.0], [0.12, 0.9, 1.0], "#1a1a1a", collide=False)
    wall_sign(b, 38.0 - 0.35, 11.4, -182.0, 4.0, 0.8, sign_decal("E. J. BLACKPOWDER 1911", "#3a2a1a", GOLD, 5.0),
              "x-", "#3a2a1a")
    supply_ammo(b, -24.0, floor, -199.5, "z+")
    supply_med(b, 12.0, floor, -164.0, "z-")


def _fire_hall(b: Area, s: Surfaces) -> None:
    """The works' own fire brigade -- there is no other out here: the engine
    house with the old pumper in it, the hose tower with the alarm bell,
    the bucket rack."""
    x0, x1, z0, z1 = FIREHALL
    s.reserve(FIREHALL)
    building(b, FIREHALL, 0.0, 12.0, "#8a2a24", roof_colour="#3a3a3a", floor_colour="#7a7670",
             doors={"z-": [(-128.0, -104.0, 10.0)], "z+": [(-122.0, -114.0, 9.0)]},
             windows={"x-": [(-230.0, -214.0, 4.0, 9.0)]}, glass=True, lights=WARM)
    threshold(b, FIREHALL, "z-", (-128.0, -104.0))
    threshold(b, FIREHALL, "z+", (-122.0, -114.0))
    wall_sign(b, -116.0, 11.0, z0 - 0.35, 24.0, 1.6,
              sign_decal("WORKS FIRE BRIGADE", "#8a2a24", CREAM, 15.0), "z-", "#8a2a24")
    # the hose tower against the east wall, the bell up in its open top
    b.box([-91.0, 12.0, -217.0], [10.0, 24.0, 10.0], "#8a2a24")
    for dx in (-1, 1):
        for dz in (-1, 1):
            b.box([-91.0 + dx * 4.4, 24.0 + 2.5, -217.0 + dz * 4.4], [1.2, 5.0, 1.2], "#8a2a24")
    slab(b, rect(-97.0, -85.0, -223.0, -211.0), 30.0, 1.0, "#3a3a3a")
    # the pumper: a red engine with brass, the ladder on top
    fx, fz = -116.0, -222.0
    floor = FLOOR
    b.box([fx, floor + 1.4, fz], [5.0, 1.0, 17.0], "#1b1d20")
    b.box([fx, floor + 1.9 + 1.4, fz + 2.0], [6.0, 2.8, 12.0], "#c42b20", material="metal")
    b.box([fx, floor + 1.9 + 1.2, fz - 6.5], [6.0, 2.4, 5.0], "#c42b20", material="metal")
    b.box([fx, floor + 4.3 + 0.8, fz - 5.6], [5.6, 1.6, 0.3], "#b8d8e8", material="glass", alpha=0.5)
    b.box([fx, floor + 4.7 + 0.25, fz + 2.0], [3.0, 0.5, 14.0], WOOD_LIGHT)
    b.cyl([fx, floor + 4.3 + 0.6, fz - 8.2], [1.0, 1.2, 1.0], GOLD, material="metal")
    for ex in (-5.6, 5.4):
        for side in (-1, 1):
            b.cyl([fx + side * 2.9, floor + 1.5, fz + ex], [3.0, 0.8, 3.0], "#1b1d20",
                  r=[0.0, 0.0, math.pi / 2.0], collide=False)
    # the hose on its board inside, and the bucket rack on the back wall
    b.box([-129.0, 4.0, -208.5], [8.0, 6.0, 1.0], WOOD)
    for k in range(3):
        b.cyl([-131.6 + k * 2.6, 4.0, -209.3], [2.4, 0.6, 2.4], "#c8a868", r=[math.pi / 2.0, 0.0, 0.0],
              collide=False)
    b.box([-129.0, 3.0, z1 + 0.5], [10.0, 0.4, 1.0], WOOD_DARK)
    for k in range(5):
        b.cyl([-133.0 + k * 2.0, 3.2 + 0.7, z1 + 1.0], [1.2, 1.4, 1.2], "#c42b20")
    for x in (-133.6, -124.4):
        b.box([x, 1.4, z1 + 0.5], [0.6, 2.8, 1.0], WOOD_DARK)
    supply_ammo(b, -102.0, floor, -232.0, "x-")
    _hydrant(b, -142.0, -246.0)


def _water_tower(b: Area, s: Surfaces) -> None:
    """The water tower the brigade draws on: legs, braces, the tank with the
    company's colours round it."""
    x, z = TOWER
    s.reserve(rect(x - 7.0, x + 7.0, z - 7.0, z + 7.0))
    for dx in (-1, 1):
        for dz in (-1, 1):
            b.box([x + dx * 5.4, 13.0, z + dz * 5.4], [1.2, 26.0, 1.2], STEEL_DARK, material="metal")
    for y in (8.0, 17.0):
        for dz in (-1, 1):
            b.box([x, y, z + dz * 5.4], [9.6, 0.6, 0.6], STEEL_DARK, material="metal")
        for dx in (-1, 1):
            b.box([x + dx * 5.4, y, z], [0.6, 0.6, 9.6], STEEL_DARK, material="metal")
    b.cyl([x, 26.0 + 5.0, z], [16.0, 10.0, 16.0], "#8a9096", material="metal")
    b.cyl([x, 31.0, z], [16.4, 2.6, 16.4], RED, material="metal")
    b.cone([x, 36.0 + 2.0, z], [17.0, 4.0, 17.0], "#5a6066", material="metal")
    wall_sign(b, x, 33.6, z - 8.0 - 0.35, 4.0, 1.6, sign_decal("BP", "#8a9096", RED, 2.5), "z-", "#8a9096")


# ================================================================ store
def _store(b: Area, s: Surfaces) -> None:
    """The outlet on the county road: aisles of boxed rockets and fountains
    inside, the tent sale in the lot, and up on the roof, swaying on its
    tethers, the giant inflatable gorilla with a rocket in its fist."""
    x0, x1, z0, z1 = STORE
    s.reserve(STORE)
    building(b, STORE, 0.0, STORE_H, "#e8d8b8", roof_colour="#5a5a5a", floor_colour="#8a8a86",
             doors={"z-": [(170.0, 190.0, 9.0)], "z+": [(200.0, 210.0, 9.0)]},
             windows={"z-": [(136.0, 164.0, 3.0, 9.0), (196.0, 224.0, 3.0, 9.0)]},
             glass=True, lights="#fff2d8")
    threshold(b, STORE, "z-", (170.0, 190.0))
    threshold(b, STORE, "z+", (200.0, 210.0))
    wall_sign(b, 180.0, 10.6, z0 - 0.35, 64.0, 2.4,
              sign_decal("FIREWORKS OUTLET   BUY 1 GET 6 FREE", RED, GOLD, 64.0 / 2.4), "z-", RED)
    floor = FLOOR
    colours = ["#e83a3a", "#3a7ae8", "#e8c83a", "#3ac87a", "#c83ae8", "#ff8a2a"]
    for i, x in enumerate((146.0, 160.0, 200.0, 214.0)):
        b.box([x, floor + 2.1, -212.0], [3.0, 4.2, 24.0], "#d8d8d0")
        for k in range(5):
            b.box([x, floor + 4.2 + 0.6, -222.0 + k * 5.0], [2.4, 1.2, 3.6], colours[(i + k) % 6])
    b.box([192.0, floor + 1.6, -226.0], [8.0, 3.2, 3.0], RED)
    b.box([194.0, floor + 3.2 + 0.6, -226.0], [2.0, 1.2, 1.6], "#2a2a2e", material="metal")
    supply_med(b, 140.0, floor, -194.0, "z-")
    # the stair up the east wall to the roof
    roof = STORE_H + 1.2
    flight(b, "z", -186.0, -226.0, x1, x1 + 6.0, 0.0, roof, STEEL_DARK, fill=0.0)
    s.reserve(rect(x1, x1 + 6.0, -226.0, -186.0))
    b.box([186.0, roof + 0.6, -214.0], [6.0, 1.2, 6.0], "#3a3a3a", material="metal")
    for (x, z) in ((150.0, -224.0), (222.0, -224.0)):
        b.box([x, roof + 1.0, z], [3.0, 2.0, 3.0], "#4a4f56", material="metal")
    supply_ammo(b, 220.0, roof, -200.0, "x-")
    # the tent sale out front, on the lot
    lot = 0.3
    for k, x in enumerate((152.0, 208.0)):
        z = -245.0
        for (px, pz) in ((x - 7.6, z - 5.6), (x + 7.6, z - 5.6), (x - 7.6, z + 5.6), (x + 7.6, z + 5.6)):
            b.box([px, lot + 4.0, pz], [0.8, 8.0, 0.8], "#e8e8e8")
        top = lot + 8.0 + 0.6
        slab(b, rect(x - 8.4, x + 8.4, z - 6.4, z + 6.4), top, 0.6, ["#c8382a", "#2a5ac8"][k])
        wall_sign(b, x, top + 0.8, z - 6.0, 12.0, 1.6, sign_decal("TENT SALE", CREAM, RED, 7.5), "z-", CREAM)
        b.box([x, lot + 1.4, z], [12.0, 2.8, 4.0], WOOD_LIGHT)
        for j in range(4):
            b.box([x - 4.5 + j * 3.0, lot + 2.8 + 0.8, z], [2.2, 1.6, 2.6], colours[(j + k * 2) % 6])
    car(b, 116.0, -245.0, "z", "#2a3a6a", y=lot)
    car(b, 252.0, -245.0, "z", "#e8e8e8", y=lot)
    car(b, 248.0, -208.0, "z", "#8a2a24")
    barrel_spot(b, 180.0, lot, -238.0)
    barrel_spot(b, 240.0, 0.0, -190.0)


# ================================================================ siding
def _siding(b: Area, s: Surfaces) -> None:
    """The rail siding: ballast, sleepers and rails in from the west to the
    buffer stop, two boxcars placarded EXPLOSIVES at the loading dock."""
    x0, x1, z0, z1 = TRACK
    zc = (z0 + z1) / 2.0
    s.lay(TRACK, 0.3, BALLAST, studs=True)
    x = x0 + 2.0
    while x < x1 - 6.0:
        b.box([x, 0.4, zc], [1.2, 0.2, 7.0], "#4a3a2a")
        x += 4.0
    rail_x0, rail_x1 = x0 + 1.0, x1 - 4.0
    for z in RAILS_Z:
        b.box([(rail_x0 + rail_x1) / 2.0, 0.65, z], [rail_x1 - rail_x0, 0.3, 0.5], "#6a6f76", material="metal")
    b.box([x1 - 2.5, 0.3 + 1.3, zc], [2.0, 2.6, 8.0], RED)
    b.box([x1 - 2.5, 0.3 + 2.6 + 0.4, zc], [1.4, 0.8, 9.0], "#2a2a2e")
    for k, x in enumerate((-110.0, -80.0)):
        b.box([x, 1.15, zc], [20.0, 0.7, 5.0], "#2a2a2e")
        b.box([x, 1.5 + 4.8, zc], [24.0, 9.6, 7.6], ["#8a2a24", "#5a3a2a"][k], studs=True)
        for side in (-1, 1):
            b.box([x + 5.0, 1.5 + 4.6, zc + side * 3.9], [6.0, 8.0, 0.2], "#4a3a30")
            b.box([x - 5.0, 7.4, zc + side * 3.86], [7.0, 2.4, 0.12], CREAM, collide=False,
                  decal=sign_decal("EXPLOSIVES", CREAM, RED, 7.0 / 2.4))
    s.reserve(rect(DOCK[0] - 6.0, DOCK[1] + 6.0, DOCK[2], DOCK[3]))
    slab(b, DOCK, DOCK_TOP, DOCK_TOP, CONCRETE, studs=True)
    flight(b, "x", DOCK[0] - 6.0, DOCK[0], DOCK[2], DOCK[3], 0.0, DOCK_TOP, CONCRETE_DARK, fill=0.0)
    flight(b, "x", DOCK[1] + 6.0, DOCK[1], DOCK[2], DOCK[3], 0.0, DOCK_TOP, CONCRETE_DARK, fill=0.0)
    for (x, z) in ((-130.0, -136.0), (-125.5, -136.0), (-90.0, -135.6)):
        crate(b, x, DOCK_TOP, z, 4.0, "#8a6a4a")
    crate(b, -127.75, DOCK_TOP + 4.0, -136.0, 3.6, "#7a5a3a")
    supply_med(b, -104.0, DOCK_TOP, -133.6, "z-")
    # a forklift left by the dock
    b.box([-48.0, 1.4, -128.0], [5.0, 2.0, 7.0], HAZARD, material="metal")
    b.box([-48.0, 3.6, -129.5], [4.6, 2.4, 3.0], "#2a2a2e")
    b.box([-48.0, 4.2, -133.2], [4.0, 5.6, 0.6], "#3a3a3e", material="metal")
    b.box([-48.0, 0.6, -135.0], [4.0, 0.4, 3.4], "#3a3a3e", material="metal")
    barrel_spot(b, -150.0, 0.0, -128.0)
    barrel_spot(b, -64.0, 0.0, -122.0)


# ================================================================== pond
def _pond(b: Area, s: Surfaces) -> None:
    """The test pond, where the water shells are tried: black water, the
    firing raft out on it, a jetty, steps down off the east bank."""
    x0, x1, z0, z1 = POND
    slab(b, POND, POND_BED, 2.0, "#3a3a2a", studs=True)
    b.water((x0 + x1) / 2.0, (z0 + z1) / 2.0, x1 - x0, z1 - z0, POND_WATER, "#14262a")
    flight(b, "x", x1 - 8.0, x1, -230.0, -218.0, POND_BED, 0.0, CONCRETE_DARK, fill=POND_BED)
    # the jetty
    slab(b, rect(x1 - 12.0, x1, -206.0, -200.0), 0.6, 0.6, WOOD, studs=True)
    for z in (-205.6, -200.4):
        b.box([x1 - 11.6, POND_BED / 2.0, z], [0.8, -POND_BED, 0.8], WOOD_DARK)
    # the raft, moored, with its mortars
    rx, rz = RAFT
    slab(b, rect(rx - 10.0, rx + 10.0, rz - 8.0, rz + 8.0), -0.4, 1.0, WOOD, studs=True)
    for dx in (-1, 1):
        for dz in (-1, 1):
            b.box([rx + dx * 9.4, (POND_BED - 1.4) / 2.0, rz + dz * 7.4], [1.0, -1.4 - POND_BED, 1.0], WOOD_DARK)
    for i in range(3):
        b.cyl([rx - 4.0 + i * 4.0, -0.4 + 1.6, rz], [1.8, 3.2, 1.8], TUBE)
    b.box([rx, -0.4 + 0.6, rz + 5.0], [6.0, 1.2, 3.0], "#4a5060", material="metal")
    # reeds along the north bank
    for k in range(9):
        x = x0 + 6.0 + k * 9.0
        b.cyl([x, (POND_BED + 3.0) / 2.0, z1 - 2.0 - (k % 3)], [0.4, 3.0 - POND_BED, 0.4], "#4a5a2a")
    post_sign(b, x1 + 4.0, -234.0, 0.0, 3.0, 8.0, 2.0, sign_decal("TEST POND  LIVE SHELLS", HAZARD, "#1b1b1b", 4.0),
              "x+", HAZARD)
    _hydrant(b, x1 + 6.0, -194.0)


# ================================================================ crater
def _crater(b: Area, s: Surfaces) -> None:
    """Where Shed No. 4 stood until the third of July, 1958: a crater in
    rings down to the cracked floor, charred stumps of posts, the beam that
    came down here from somewhere, and the stone on the rim."""
    x0, x1, z0, z1 = CRATER
    base = -10.0
    shades = ["#4a4232", "#423a2c", "#3a3226", "#32302a"]
    for k in range(4):
        outer = rect(x0 + 6.0 * k, x1 - 6.0 * k, z0 + 6.0 * k, z1 - 6.0 * k)
        top = -2.0 * (k + 1)
        if k < 3:
            inner = rect(x0 + 6.0 * (k + 1), x1 - 6.0 * (k + 1), z0 + 6.0 * (k + 1), z1 - 6.0 * (k + 1))
            plate(b, carve(outer, [inner]), top, top - base, shades[k], studs=True)
        else:
            slab(b, outer, top, top - base, shades[k], studs=True)
    floor = -8.0
    b.box([119.0, floor + 0.4, -111.0], [8.0, 0.6, 6.0], CONCRETE_DARK, r=[0.14, 0.4, 0.1], collide=False)
    b.box([129.0, floor + 0.5, -108.0], [6.0, 0.6, 5.0], CONCRETE_DARK, r=[-0.2, -0.3, 0.12], collide=False)
    b.box([127.0, floor + 3.0, -112.0], [0.8, 7.0, 0.8], "#3a3a3e", r=[0.5, 0.2, 0.35], collide=False)
    b.box([118.0, floor + 0.3, -106.0], [3.6, 0.3, 6.6], "#3a2a1a", r=[0.0, 0.5, 0.06], collide=False)
    for (x, y, z, h) in ((100.0, -2.0, -100.0, 4.0), (148.0, -2.0, -120.0, 3.0), (110.0, -4.0, -124.0, 5.0),
                         (138.0, -4.0, -96.0, 2.4), (116.0, -6.0, -104.0, 3.4), (131.0, -6.0, -115.0, 2.0)):
        b.cyl([x, y + h / 2.0, z], [1.4, h, 1.4], CHAR)
    # the memorial on the north rim
    b.box([124.0, 1.2, -83.0], [9.0, 2.4, 2.0], "#8a8a86")
    wall_sign(b, 124.0, 1.4, -84.35, 7.0, 1.4,
              sign_decal("SHED No. 4  JULY 3 1958", "#6a6a66", CREAM, 5.0), "z-", "#6a6a66")
    b.cyl([121.0, 2.6, -84.2], [2.2, 0.5, 2.2], "#2a5a2a", r=[math.pi / 2.0 - 0.2, 0.0, 0.0], collide=False)
    # two trees that never grew back
    for (x, z) in ((90.0, -126.0), (158.0, -96.0)):
        b.cyl([x, 5.0, z], [1.6, 10.0, 1.6], CHAR)
        b.box([x + 1.6, 8.0, z], [3.2, 0.5, 0.5], CHAR, r=[0.0, 0.3, 0.6], collide=False)
        b.box([x - 1.4, 9.0, z + 0.6], [2.8, 0.5, 0.5], CHAR, r=[0.0, -0.4, -0.7], collide=False)


# ================================================================== hall
def _hall(b: Area, s: Surfaces) -> None:
    """The assembly hall, where the shells are made up: long benches with
    the shells on them, the crates, the rules on the wall; the company's
    name in letters on the roof, and the stair up the outside to them."""
    x0, x1, z0, z1 = HALL
    s.reserve(HALL)
    building(b, HALL, 0.0, HALL_H, "#c8b898", roof_colour="#5a5a5a", floor_colour="#8a8070",
             doors={"z+": [(-10.0, 10.0, 11.0)], "z-": [(-10.0, 10.0, 11.0)], "x-": [(-40.0, -30.0, 10.0)]},
             windows={"z+": [(-50.0, -30.0, 4.0, 10.0), (30.0, 50.0, 4.0, 10.0)],
                      "z-": [(-50.0, -30.0, 4.0, 10.0), (30.0, 50.0, 4.0, 10.0)],
                      "x+": [(-40.0, -30.0, 4.0, 10.0)]},
             glass=True, lights=WARM)
    for side, span in (("z+", (-10.0, 10.0)), ("z-", (-10.0, 10.0)), ("x-", (-40.0, -30.0))):
        threshold(b, HALL, side, span)
    roof = HALL_H + 1.2
    flight(b, "z", -14.0, -56.0, x1, x1 + 6.0, 0.0, roof, STEEL_DARK, fill=0.0)
    s.reserve(rect(x1, x1 + 6.0, -56.0, -14.0))
    board_letters(b, 0.0, roof + 2.0, z1 - 3.0, "BLACKPOWDER", 4.0, RED, GOLD, facing="z+", solid=True)
    for (x, z) in ((-40.0, -40.0), (40.0, -40.0), (-22.0, -30.0), (22.0, -30.0)):
        b.box([x, roof + 1.2, z], [5.0, 2.4, 5.0], "#6a6a6a", material="metal")
        b.box([x, roof + 2.4 + 0.3, z], [6.0, 0.6, 6.0], "#5a5a5a", material="metal")
    # a traverse of earth in front of the west door
    s.reserve(rect(-76.0, -66.0, -56.0, -14.0))
    _earthwork(b, rect(-76.0, -66.0, -56.0, -14.0), None, 2, 2.0, 2.0, 0.0, [EARTH, EARTH_HI])
    floor = FLOOR
    tones = ["#c8a868", "#a8886a", "#d8b878", "#8a6a4a"]
    for z in (-24.0, -46.0):
        for x in (-40.0, -22.0, 22.0, 40.0):
            b.box([x, floor + 1.4, z], [14.0, 2.8, 5.0], WOOD)
            for k in range(4):
                if x == 22.0 and z == -24.0 and k == 3:
                    continue
                b.sphere([x - 4.5 + k * 3.0, floor + 2.8 + 1.0, z], [2.0, 2.0, 2.0], tones[k])
    b.cyl([26.5, floor + 2.8 + 1.0, -24.0], [1.6, 2.0, 1.6], "#b8d8e8", material="glass", alpha=0.5)
    for (x, z) in ((-52.0, -52.0), (-47.0, -52.0), (-52.0, -47.0), (52.0, -52.0)):
        crate(b, x, floor, z, 4.0, "#8a5a3a")
    crate(b, -52.0, floor + 4.0, -52.0, 3.4, "#7a4a2a")
    wall_sign(b, x1 - 2.0 - 0.35, 9.0, -20.0, 16.0, 2.0,
              sign_decal("NO SPARKS  NO SMOKING  NO KIDDING", CREAM, RED, 8.0), "x-", CREAM)
    wall_sign(b, x0 + 2.0 + 0.35, 9.0, -50.0, 12.0, 2.0,
              sign_decal("DAYS WITHOUT AN INCIDENT  0", CREAM, "#1b1b1b", 6.0), "x+", CREAM)
    supply_med(b, -54.0, floor, -16.0, "x+")
    supply_ammo(b, 50.0, floor, -16.0, "x-")
    barrel_spot(b, 70.0, 0.0, -8.0)


def _tube_shop(b: Area, s: Surfaces) -> None:
    """The tube shop: a shed open on every side over the stock of paper
    tubes standing on end, the rolling machine, the glue; outside, a heap of
    tube bundles a step at a time to its roof."""
    x0, x1, z0, z1 = TUBES
    s.reserve(TUBES)
    slab(b, TUBES, 0.3, 0.3, CONCRETE)
    under = TUBES_TOP - 0.6
    for x in (x0 + 0.6, (x0 + x1) / 2.0, x1 - 0.6):
        for z in (z0 + 0.6, (z0 + z1) / 2.0, z1 - 0.6):
            b.box([x, (0.3 + under) / 2.0, z], [1.2, under - 0.3, 1.2], WOOD_DARK)
    slab(b, TUBES, TUBES_TOP, 0.6, "#5a5a5a", studs=True)
    for i in range(4):
        for j in range(3):
            h = 3.0 + ((i * 3 + j * 5) % 4) * 1.5
            b.cyl([x0 + 10.0 + i * 4.0, 0.3 + h / 2.0, z0 + 10.0 + j * 4.0], [3.4, h, 3.4],
                  CREAM if (i + j) % 2 else "#d8c8a8")
    b.box([-96.0, 0.3 + 2.0, 46.0], [10.0, 4.0, 6.0], "#5a5f66", material="metal")
    b.cyl([-96.0, 0.3 + 4.0 + 1.2, 46.0], [2.4, 9.0, 2.4], CREAM, r=[0.0, 0.0, math.pi / 2.0], collide=False)
    b.cyl([-112.0, 0.3 + 1.6, 48.0], [4.0, 3.2, 4.0], "#8a8f94", material="metal")
    for k in range(3):
        b.cyl([-122.0, 0.3 + 2.5, 40.0 + k * 5.0], [5.0, 2.0, 5.0], "#c8b898", r=[math.pi / 2.0, 0.0, 0.0],
              collide=False)
        b.box([-122.0, 0.3 + 0.2, 40.0 + k * 5.0], [2.0, 0.4, 2.0], WOOD_DARK)
    # the heap of bundles to the roof
    s.reserve(rect(x1, x1 + 30.0, 14.0, 24.0))
    for i in range(6):
        top = 1.8 * (i + 1)
        xa = x1 + 30.0 - 5.0 * i
        b.box([xa - 2.5, top / 2.0, 19.0], [5.0, top, 10.0], ["#d8c8a8", CREAM][i % 2], studs=True)
    wall_sign(b, (x0 + x1) / 2.0, TUBES_TOP + 1.0, z0 + 0.35, 16.0, 2.0,
              sign_decal("TUBE SHOP", "#5a5a5a", CREAM, 8.0), "z-", "#5a5a5a")
    barrel_spot(b, -70.0, 0.0, 44.0)


def _star_racks(b: Area, s: Surfaces) -> None:
    """The star racks: the coloured stars drying on their trays, tier on
    tier, in three long frames under a catwalk -- red, green, blue, gold,
    violet, orange, glowing faintly in the dark."""
    x0, x1, z0, z1 = CATWALK
    s.reserve(CATWALK)
    colours = ["#ff3a3a", "#3a8aff", "#3aff7a", "#ffd84a", "#c83aff", "#ff8a2a"]
    under = CATWALK_TOP - 0.6
    for k, z in enumerate((22.0, 35.0, 48.0)):
        for x in (x0 + 1.5, x1 - 1.5):
            b.box([x, under / 2.0, z], [1.0, under, 1.0], WOOD_DARK)
        for t in range(4):
            y = 2.0 + t * 2.6
            b.box([(x0 + x1) / 2.0, y, z], [x1 - x0 - 4.0, 0.3, 4.0], WOOD_LIGHT)
            b.box([(x0 + x1) / 2.0, y + 0.3, z], [x1 - x0 - 6.0, 0.3, 3.0], colours[(k * 4 + t) % 6],
                  material="neon")
    slab(b, CATWALK, CATWALK_TOP, 0.6, WOOD, studs=True)
    rails(b, CATWALK, CATWALK_TOP, 3.2, WOOD_DARK, 0.8, gaps={"z-": [(x1 - 8.0, x1 - 2.0)]})
    flight(b, "z", -14.0, z0, x1 - 8.0, x1 - 2.0, 0.0, CATWALK_TOP, WOOD_DARK, fill=0.0)
    s.reserve(rect(x1 - 8.0, x1 - 2.0, -14.0, z0))
    post_sign(b, x1 - 12.0, -12.0, 0.0, 3.0, 8.0, 1.8, sign_decal("STAR RACKS", CREAM, "#3a2a1a", 4.4), "z-", CREAM)
    supply_ammo(b, 100.0, CATWALK_TOP, 30.0, "z+")
    barrel_spot(b, 72.0, 0.0, 40.0)


def _rocket(b: Area, s: Surfaces) -> None:
    """The giant rocket: the works' sign since 1911, a skyrocket six storeys
    tall standing on its fins in the middle of the works, and the painters'
    gantry beside it -- two decks, and an arm across to the rocket."""
    cx, cz = ROCKET
    gx0, gx1, gz0, gz1 = GANTRY
    s.reserve(rect(gx0 - 2.0, cx + 12.0, 18.0, gz1 + 2.0))
    base = 1.0
    slab(b, rect(cx - 11.0, cx + 11.0, cz - 11.0, cz + 11.0), base, base, CONCRETE_LIGHT, studs=True)
    b.cyl([cx, base + 6.0 + 16.0, cz], [9.0, 32.0, 9.0], RED)
    for y in (base + 12.0, base + 24.0, base + 34.0):
        b.cyl([cx, y, cz], [9.4, 2.0, 9.4], GOLD)
    b.cone([cx, base + 38.0 + 5.0, cz], [9.6, 10.0, 9.6], GOLD)
    b.sphere([cx, base + 48.6, cz], [1.6, 1.6, 1.6], "#fff2a8", material="neon", collide=False)
    b.cyl([cx, base + 5.0, cz], [5.0, 2.0, 5.0], "#3a3a3a")
    b.cyl([cx + 1.5, base + 2.0, cz], [0.4, 4.0, 0.4], "#c8a868")
    for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        if dx:
            b.box([cx + dx * 7.5, base + 4.0, cz], [6.0, 8.0, 1.2], GOLD)
            b.box([cx + dx * 6.0, base + 11.0, cz], [3.0, 6.0, 1.2], GOLD)
        else:
            b.box([cx, base + 4.0, cz + dz * 7.5], [1.2, 8.0, 6.0], GOLD)
            b.box([cx, base + 11.0, cz + dz * 6.0], [1.2, 6.0, 3.0], GOLD)
    wall_sign(b, cx, base + 28.0, cz - 4.5 - 0.35, 4.0, 2.4, sign_decal("BOOM", RED, GOLD, 4.0 / 2.4), "z-", RED)
    post_sign(b, cx + 9.0, cz - 16.0, 0.0, 2.6, 10.0, 2.2,
              sign_decal("WORLDS LARGEST SKYROCKET  NOT TO BE LIT", CREAM, "#3a2a1a", 4.5), "z-", CREAM)
    # the gantry: deck one up a flight from the south, deck two up a flight
    # on deck one, the arm across to the rocket
    slab(b, GANTRY, DECK1, 0.6, STEEL, studs=True, material="metal")
    for (x, z) in ((gx0 + 0.4, gz0 + 0.4), (gx1 - 0.4, gz0 + 0.4), (gx0 + 0.4, gz1 - 0.4), (gx1 - 0.4, gz1 - 0.4)):
        b.box([x, (DECK1 - 0.6) / 2.0, z], [0.8, DECK1 - 0.6, 0.8], STEEL_DARK, material="metal")
    flight(b, "z", 20.0, gz0, gx0, gx0 + 6.0, 0.0, DECK1, STEEL_DARK, fill=0.0)
    well = rect(gx0, gx0 + 6.0, gz0 + 4.0, gz1)
    plate(b, carve(GANTRY, [well]), DECK2, 0.6, STEEL, studs=True, material="metal")
    flight(b, "z", gz1, gz0 + 4.0, gx0, gx0 + 6.0, DECK1, DECK2, STEEL_DARK, fill=DECK1)
    for (x, z) in ((gx0 + 0.4, gz0 + 0.4), (gx1 - 0.4, gz0 + 0.4), (gx1 - 0.4, gz1 - 0.4), (gx0 + 6.4, gz1 - 0.4)):
        b.box([x, (DECK1 + DECK2 - 0.6) / 2.0, z], [0.8, DECK2 - 0.6 - DECK1, 0.8], STEEL_DARK, material="metal")
    top = DECK2 + 1.6
    b.box([(gx0 + gx1) / 2.0, top, gz0 + 0.4], [gx1 - gx0, 3.2, 0.8], STEEL_DARK, material="metal")
    b.box([gx0 + 0.4, top, gz0 + 2.4], [0.8, 3.2, 3.2], STEEL_DARK, material="metal")
    b.box([gx0 + 6.4, top, (gz0 + 8.0 + gz1) / 2.0], [0.8, 3.2, gz1 - gz0 - 8.0], STEEL_DARK, material="metal")
    b.box([(gx0 + 6.8 + gx1) / 2.0, top, gz1 - 0.4], [gx1 - gx0 - 6.8, 3.2, 0.8], STEEL_DARK, material="metal")
    arm = (53.0, 59.0)
    b.box([gx1 - 0.4, top, (gz0 + 0.8 + arm[0]) / 2.0], [0.8, 3.2, arm[0] - gz0 - 0.8], STEEL_DARK, material="metal")
    b.box([gx1 - 0.4, top, (arm[1] + gz1 - 0.8) / 2.0], [0.8, 3.2, gz1 - 0.8 - arm[1]], STEEL_DARK, material="metal")
    slab(b, rect(gx1, cx - 4.4, arm[0], arm[1]), DECK2, 0.6, STEEL, studs=True, material="metal")
    for z in (arm[0] + 0.4, arm[1] - 0.4):
        b.box([(gx1 + cx - 4.4) / 2.0, top, z], [cx - 4.4 - gx1, 3.2, 0.8], STEEL_DARK, material="metal")
    b.cyl([gx1 + 2.0, DECK2 + 1.0, arm[0] + 2.4], [1.6, 2.0, 1.6], RED)
    supply_med(b, -16.0, DECK2, gz0 + 2.4, "z+")
    barrel_spot(b, 14.0, 0.3, 36.0)


# ============================================================= magazines
def _magazines(b: Area, s: Surfaces) -> None:
    """The magazines down the west side: four concrete stores, each buried
    in its mound with only the headwall showing -- the steel doors stood
    open, the number; inside, the crates of finished shells in rows."""
    bx0, bx1 = MAG_X
    height = 8.8
    for k, zc in enumerate(MAGS):
        bz0, bz1 = zc - 14.0, zc + 14.0
        r = rect(bx0, bx1, bz0, bz1)
        s.reserve(rect(bx0 - 12.0, bx1, bz0 - 12.0, bz1 + 12.0))
        building(b, r, 0.0, height, CONCRETE_DARK, roof_colour=CONCRETE_DARK, floor_colour="#5a5a5a",
                 doors={"x+": [(zc - 4.0, zc + 4.0, 7.0)]}, lights="#e8c8a0")
        threshold(b, r, "x+", (zc - 4.0, zc + 4.0))
        _earthwork(b, rect(bx0 - 12.0, bx1, bz0 - 12.0, bz1 + 12.0), rect(bx0, bx1 + 20.0, bz0, bz1),
                   5, 2.0, 2.4, 0.0, [EARTH, EARTH_HI])
        roof = height + 1.2
        slab(b, rect(bx0 - 2.4, bx1 - 9.6, bz0 - 2.4, bz1 + 2.4), roof + 2.0, 2.0, EARTH, studs=True,
             material="grass")
        slab(b, rect(bx0 + 1.0, bx1 - 16.0, bz0 + 2.0, bz1 - 2.0), roof + 4.0, 2.0, EARTH_HI, studs=True,
             material="grass")
        b.cyl([bx0 + 8.0, roof + 4.0 + 1.5, zc], [1.6, 3.0, 1.6], STEEL_DARK, material="metal")
        b.cyl([bx0 + 8.0, roof + 7.0 + 0.3, zc], [3.0, 0.6, 3.0], STEEL_DARK, material="metal")
        for side in (-1, 1):
            b.box([bx1 + 0.5, 1.6, zc + side * 20.0], [1.0, 3.2, 12.0], CONCRETE)
            b.box([bx1 + 0.3, 0.3 + 3.35, zc + side * 6.0], [0.6, 6.7, 4.0], "#5a6066", material="metal")
        wall_sign(b, bx1 + 0.35, 8.0, zc, 9.0, 1.2, sign_decal("MAGAZINE %d" % (k + 1), CREAM, RED, 7.5), "x+", CREAM)
        s.lay(rect(bx1, bx1 + 12.0, zc - 10.0, zc + 10.0), 0.3, CONCRETE)
        for j in range(5):
            crate(b, bx0 + 4.5, FLOOR, bz0 + 5.0 + j * 4.5, 4.0, "#7a5a3a")
        for i in range(3):
            for zz in (bz0 + 4.0, bz1 - 4.0):
                crate(b, bx0 + 11.0 + i * 5.0, FLOOR, zz, 4.0, "#8a6a4a")
        crate(b, bx0 + 4.5, FLOOR + 4.0, bz0 + 9.5, 3.4, "#6a4a2a")
        if k == 1:
            supply_med(b, bx1 - 6.0, FLOOR, bz0 + 3.6, "z+")
        if k == 2:
            supply_ammo(b, bx1 - 6.0, FLOOR, bz1 - 4.0, "z-")
        barrel_spot(b, bx1 + 8.0, 0.0, zc + 13.0)


# ================================================================ sheds
def _sheds(b: Area, s: Surfaces) -> None:
    """The mixing sheds, out east where a mistake costs one shed and not the
    works: six little wooden houses, each in its own horseshoe of earth open
    to the path, a drum turning in each, the bench of jars."""
    jars = ["#2a2a2a", "#c8c8c8", "#e8d84a", "#c83a3a", "#3a6ac8", "#3ac86a"]
    for i, (x, z, name) in enumerate(SHEDS):
        shed = rect(x - 8.0, x + 8.0, z - 6.0, z + 6.0)
        outer = rect(x - 22.0, x + 24.0, z - 22.0, z + 22.0)
        s.reserve(outer)
        building(b, shed, 0.0, 8.0, WOOD_LIGHT, roof_colour="#5a3a2a", floor_colour="#7a6a52",
                 doors={"x-": [(z - 3.0, z + 3.0, 6.5)]}, windows={"z+": [(x - 4.0, x + 4.0, 3.0, 5.5)]},
                 glass=True, lights=WARM)
        threshold(b, shed, "x-", (z - 3.0, z + 3.0))
        gable(b, shed, 8.0 + 1.2, "#5a3a2a", "x", tiers=2, rise=1.2, overhang=0.6)
        _earthwork(b, outer, rect(x - 30.0, x + 12.0, z - 10.0, z + 10.0), 3, 2.0, 2.0, 2.0, [EARTH, EARTH_HI])
        wall_sign(b, x - 8.35, 7.2, z, 7.0, 1.0, sign_decal(name, CREAM, "#3a2a1a", 7.0), "x-", CREAM)
        wall_sign(b, x, 6.8, z + 4.0 - 0.35, 6.0, 1.0, sign_decal("NO IRON TOOLS", HAZARD, "#1b1b1b", 6.0),
                  "z-", HAZARD)
        b.box([x + 3.0, FLOOR + 1.0, z], [3.0, 2.0, 5.0], STEEL_DARK, material="metal")
        b.box([x - 2.0, FLOOR + 1.4, z - 2.8], [7.0, 2.8, 2.4], WOOD)
        for j in range(4):
            b.cyl([x - 4.4 + j * 1.6, FLOOR + 2.8 + 0.6, z - 2.8], [1.0, 1.2, 1.0], jars[(i + j) % 6])
        if i % 2 == 0:
            barrel_spot(b, x - 15.0, 0.0, z + 5.0)
    supply_ammo(b, 195.0, 0.0, 30.0, "z-")


# ============================================================ show field
def _show_field(b: Area, s: Surfaces) -> None:
    """The show field: the mortar racks out on the grass in rows with the
    cables run to them, the firing line of sandbags, the lancework frame at
    the back against the berm, and the firing bunker -- earth heaped up
    both ends of it and over the top, the window on the field, the panel
    (the lure)."""
    x0, x1, z0, z1 = FIELD
    s.reserve(rect(x0, x1, z0, 280.0))
    for z, xs in RACK_ROWS:
        for x in xs:
            _mortar_rack(b, x, z)
        b.box([0.0, 0.05, z - 3.6], [xs[-1] - xs[0], 0.1, 0.3], "#c8382a", collide=False)
    cable_end = RACK_ROWS[-1][0] - 3.6
    b.box([2.0, 0.05, (132.0 + cable_end) / 2.0], [0.3, 0.1, cable_end - 132.0], "#c8382a", collide=False)
    for k in range(-5, 6):
        if k:
            sandbags(b, k * 28.0, 146.0, 20.0, "x")
    # the lancework frame
    for x in (-36.0, -12.0, 12.0, 36.0):
        b.box([x, 9.0, LANCE_Z], [1.2, 18.0, 1.2], WOOD_DARK)
    for y in (4.0, 10.0, 16.0):
        b.box([0.0, y, LANCE_Z], [74.0, 0.6, 0.6], WOOD)
    _earthwork(b, rect(x0, x1, 262.0, 276.0), None, 3, 1.6, 2.0, 0.0, [EARTH, EARTH_HI])
    # the firing bunker
    s.reserve(rect(-24.0, 24.0, 116.0, 136.0))
    building(b, FIRING, 0.0, 6.0, CONCRETE, roof_colour=CONCRETE_DARK, floor_colour="#6a6a6a",
             doors={"z-": [(-4.0, 4.0, 5.4)]}, windows={"z+": [(-8.0, 8.0, 3.2, 4.4)]}, glass=True,
             lights="#ffe8c8")
    threshold(b, FIRING, "z-", (-4.0, 4.0))
    for side in (-1, 1):
        for k in range(3):
            xa, xb = sorted((side * 12.0, side * (24.0 - 4.0 * k)))
            slab(b, rect(xa, xb, 116.0, 136.0), 2.0 * (k + 1), 2.0, [EARTH, EARTH_HI][k % 2], studs=True,
                 material="grass")
    slab(b, rect(-8.0, 8.0, 122.0, 130.0), 6.0 + 1.2 + 1.2, 1.2, EARTH, studs=True, material="grass")
    floor = FLOOR
    b.box([6.0, floor + 1.4, 128.8], [6.0, 2.8, 2.4], "#4a5060", material="metal")
    b.box([6.0, floor + 2.8 + 0.3, 128.6], [1.4, 0.6, 1.4], RED)
    b.box([-5.0, floor + 1.0, 128.0], [5.0, 2.0, 3.0], WOOD)
    b.box([-6.0, floor + 2.0 + 0.6, 128.4], [1.8, 1.2, 1.4], "#3a4a3a", material="metal")
    b.set_lure(6.0, floor, 125.8, "the finale", "Light the finale", "ll_finale", (0.0, 0.0, 200.0))
    post_sign(b, -10.0, 114.0, 0.0, 2.6, 8.0, 1.8, sign_decal("FIRING POINT", HAZARD, "#1b1b1b", 4.4), "z-", HAZARD)
    supply_ammo(b, -60.0, 0.0, 154.0, "z-")
    barrel_spot(b, 60.0, 0.0, 156.0)
    barrel_spot(b, -100.0, 0.0, 214.0)
    barrel_spot(b, 140.0, 0.0, 240.0)


def _proving_ground(b: Area, s: Surfaces) -> None:
    """The proving ground in the north-west corner, where a new product is
    tried before it goes in a show: the wheel frame with its Catherine
    wheels, the sandbags to watch from, the spotter's tower."""
    s.reserve(rect(-262.0, -192.0, 190.0, 216.0))
    for x in WHEELS:
        b.box([x, 7.0, WHEEL_Z], [1.4, 14.0, 1.4], WOOD_DARK)
    b.box([(WHEELS[0] + WHEELS[-1]) / 2.0, 14.6, WHEEL_Z], [WHEELS[-1] - WHEELS[0] + 4.0, 1.2, 1.6], WOOD)
    sandbags(b, (WHEELS[0] + WHEELS[-1]) / 2.0, 196.0, 52.0, "x")
    s.reserve(rect(-243.0, -204.0, 142.0, 158.0))
    watchtower(b, -236.0, 150.0, 14.0, WOOD, stair="x+")
    s.reserve(rect(-272.0, -228.0, 232.0, 268.0))
    top = mound(b, -250.0, 250.0, 22.0, 18.0, 3, 1.6, [GRASS, EARTH])
    for (dx, dz, sc) in ((-6.0, 4.0, 1.3), (6.0, -4.0, 1.1), (2.0, 8.0, 1.0)):
        pine(b, -250.0 + dx, 250.0 + dz, top, sc)
    barrel_spot(b, -200.0, 0.0, 180.0)


def _north_east(b: Area, s: Surfaces) -> None:
    """Out past the sheds: the burn pit, where the duds go, smouldering; and
    BIG BERTHA on her trailer -- the forty-eight inch shell, the show's
    closer, waiting to be taken to the field."""
    x0, x1, z0, z1 = BURN
    inner = rect(x0 + 4.0, x1 - 4.0, z0 + 4.0, z1 - 4.0)
    plate(b, carve(BURN, [inner]), -2.0, 4.0, "#3a3028", studs=True)
    slab(b, inner, -4.0, 2.0, "#2a2420", studs=True)
    b.box([(x0 + x1) / 2.0, -3.95, (z0 + z1) / 2.0], [16.0, 0.1, 12.0], "#1a1a1a", collide=False)
    for (x, z, size) in ((214.0, 140.0, 2.6), (230.0, 152.0, 2.2), (226.0, 138.0, 1.8)):
        b.box([x, -4.0 + size / 2.0, z], [size, size, size], CHAR, studs=True)
    for (x, z) in ((x0 - 1.0, z0 - 1.0), (x1 + 1.0, z0 - 1.0), (x0 - 1.0, z1 + 1.0), (x1 + 1.0, z1 + 1.0)):
        b.cyl([x, 1.6, z], [0.8, 3.2, 0.8], HAZARD)
    for (cx, cz, w, d) in (((x0 + x1) / 2.0, z0 - 1.0, x1 - x0 + 2.0, 0.2),
                           ((x0 + x1) / 2.0, z1 + 1.0, x1 - x0 + 2.0, 0.2),
                           (x0 - 1.0, (z0 + z1) / 2.0, 0.2, z1 - z0 + 2.0),
                           (x1 + 1.0, (z0 + z1) / 2.0, 0.2, z1 - z0 + 2.0)):
        b.box([cx, 2.6, cz], [w, 0.2, d], "#c8382a")
    post_sign(b, x0 - 6.0, (z0 + z1) / 2.0, 0.0, 3.0, 8.0, 1.8,
              sign_decal("BURN PIT  DUDS ONLY", HAZARD, "#1b1b1b", 4.4), "x-", HAZARD)
    # Big Bertha on her trailer
    bx, bz = BERTHA
    s.reserve(rect(bx - 18.0, bx + 14.0, bz - 5.0, bz + 5.0))
    b.box([bx, 3.6, bz], [26.0, 1.2, 8.0], "#3a3a3e", material="metal")
    b.box([bx - 15.0, 2.4, bz], [4.0, 0.6, 1.0], "#3a3a3e", material="metal")
    b.box([bx - 16.4, 1.05, bz], [0.6, 2.1, 0.6], "#3a3a3e", material="metal")
    for ex in (6.0, 9.6):
        for side in (-1, 1):
            b.cyl([bx + ex, 1.5, bz + side * 3.6], [3.0, 1.0, 3.0], "#1b1d20", r=[math.pi / 2.0, 0.0, 0.0],
                  collide=False)
    for dx in (-3.5, 3.5):
        b.box([bx + dx, 4.2 + 1.0, bz], [1.6, 2.0, 7.0], WOOD)
    b.sphere([bx, 4.2 + 5.2, bz], [10.4, 10.4, 10.4], "#c8a868")
    b.cyl([bx, 4.2 + 10.4 + 1.0, bz], [0.6, 2.0, 0.6], "#3a2a1a")
    wall_sign(b, bx, 3.6, bz - 4.35, 14.0, 1.2, sign_decal("BIG BERTHA  48 IN.  SHOW CLOSER", "#3a3a3e", GOLD, 11.7),
              "z-", "#3a3a3e")
    barrel_spot(b, 256.0, 0.0, 236.0)


# =============================================================== country
def _country(b: Area, s: Surfaces, rng: random.Random) -> None:
    """Hills with trees between the parts of the works, pines in the
    corners, lamps along the roads, hydrants, the warning signs."""
    for (cx, cz) in ((-150.0, -30.0), (110.0, -30.0), (110.0, 100.0), (-110.0, 100.0), (-170.0, -110.0),
                     (60.0, -110.0), (85.0, -215.0), (-170.0, 118.0)):
        s.reserve(rect(cx - 16.0, cx + 16.0, cz - 12.0, cz + 12.0))
        top = mound(b, cx, cz, 16.0, 12.0, 2, 1.4, [GRASS, EARTH])
        tree(b, cx, cz, top, rng.uniform(1.1, 1.4), WOOD, "#2a4a2a")
    for (x, z, sc) in ((266.0, 266.0, 1.4), (252.0, 270.0, 1.2), (268.0, 246.0, 1.1), (262.0, -168.0, 1.3),
                       (-268.0, -232.0, 1.3), (-266.0, -214.0, 1.1), (268.0, 112.0, 1.2), (-270.0, 140.0, 1.2)):
        pine(b, x, z, 0.0, sc)
    for (x, z) in ((-14.0, -120.0), (14.0, 4.0), (-46.0, 100.0), (46.0, 100.0), (-192.0, -20.0),
                   (174.0, -120.0), (176.0, 100.0), (-14.0, -240.0), (14.0, -240.0)):
        lamp_post(b, x, z, h=12.0, light="#ffd8a8")
    for (x, z) in ((40.0, -134.0), (-66.0, -86.0), (152.0, 6.0)):
        _hydrant(b, x, z)
    for (x, z, facing) in ((-16.0, 108.0, "z-"), (156.0, -90.0, "x+"), (-192.0, 60.0, "x+")):
        post_sign(b, x, z, 0.0, 3.0, 10.0, 2.0, sign_decal("NO SMOKING  NO FLAMES", HAZARD, "#1b1b1b", 5.0),
                  facing, HAZARD)
    van(b, -30.0, -110.0, "x", "#e8e8e8", stripe=RED, label="BLACKPOWDER SHOW TEAM")


def _paths(b: Area, s: Surfaces) -> None:
    s.lay(rect(-280.0, 280.0, -267.4, -266.6), 0.3, LINE_YELLOW)
    for r, colour in ((rect(-280.0, 280.0, -276.0, -258.0), ASPHALT),
                      (rect(100.0, 270.0, -258.0, -232.0), ASPHALT),
                      (rect(-8.0, 8.0, -258.0, -204.0), PAVEMENT),
                      (rect(-130.0, -102.0, -258.0, -238.0), CONCRETE),
                      (rect(-8.0, 8.0, -160.0, -60.0), ASPHALT),
                      (rect(-210.0, 160.0, -80.0, -68.0), ASPHALT),
                      (rect(-8.0, 8.0, -10.0, 14.0), ASPHALT),
                      (rect(-40.0, 40.0, 14.0, 98.0), CONCRETE_LIGHT),
                      (rect(-8.0, 8.0, 98.0, 116.0), ASPHALT),
                      (rect(-210.0, -198.0, -130.0, 116.0), GRAVEL),
                      (rect(158.0, 168.0, -190.0, 90.0), GRAVEL),
                      (rect(168.0, 212.0, -190.0, -180.0), GRAVEL),
                      (rect(-168.0, -136.0, -206.0, -200.0), GRAVEL)):
        s.lay(r, 0.3, colour, studs=colour in (GRAVEL, CONCRETE_LIGHT))


# ================================================================ rigs
def _rigs(b: Area) -> None:
    b.rig("show_finale", 0.0, 0.0, 200.0, 0.0,
          racks_path=[[x, 4.2, z] for z, xs in RACK_ROWS for x in xs],
          raft_p=[RAFT[0], 2.8, RAFT[1]])
    b.rig("catherine_wheels", (WHEELS[0] + WHEELS[-1]) / 2.0, 9.0, WHEEL_Z - 0.8, 0.0,
          hubs_path=[[x, 9.0, WHEEL_Z - 0.8] for x in WHEELS])
    b.rig("lancework", 0.0, 10.0, LANCE_Z - 0.4, math.pi, w=72.0, h=12.0)
    b.rig("inflatable_ape", 186.0, STORE_H + 1.2 + 1.2, -214.0, math.pi)
    b.rig("sparklers", 26.5, FLOOR + 2.8 + 2.0, -24.0, 0.0)
    b.rig("tumblers", 219.0, 0.0, 0.0, 0.0, drums_path=[[x + 3.0, FLOOR + 2.0 + 1.6, z] for x, z, _ in SHEDS])
    b.rig("colour_flames", 244.0, FLOOR + 2.8 + 1.2, -62.8, 0.0)
    b.rig("burn_pit", (BURN[0] + BURN[1]) / 2.0, -3.9, (BURN[2] + BURN[3]) / 2.0, 0.0)
    b.rig("fire_bell", -91.0, 27.4, -217.0, 0.0)
    b.rig("rocket_fuse", ROCKET[0], 1.0, ROCKET[1], 0.0)
    b.rig("works_flag", -24.0, 30.6, -226.0, math.pi / 2.0)
    b.rig("searchlights", 0.0, 0.0, 0.0, 0.0, lights=[[150.0, -224.0], [222.0, -224.0]],
          aim=[186.0, 26.0, -214.0], y0=STORE_H + 1.2 + 2.2)
    for (x, z) in ((-46.0, 100.0), (174.0, -120.0)):
        b.rig("moth_swarm", x, 11.6, z, 0.0)


# ============================================================== spawns
def _zombie_spawns(b: Area) -> None:
    for (x, z) in ((-268.0, 268.0), (-120.0, 272.0), (0.0, 272.0), (120.0, 272.0), (268.0, 268.0),
                   (270.0, 180.0), (270.0, 120.0), (-270.0, 170.0), (-200.0, 236.0), (-150.0, 200.0),
                   (150.0, 200.0), (60.0, 250.0), (-60.0, 250.0), (275.0, 30.0), (275.0, -100.0),
                   (270.0, -160.0), (150.0, -270.0), (40.0, -272.0), (-100.0, -272.0), (-268.0, -268.0),
                   (-272.0, -165.0), (-275.0, -10.0), (-185.0, 60.0), (-60.0, 110.0), (60.0, 116.0),
                   (120.0, -40.0), (-120.0, -100.0), (30.0, -110.0)):
        b.zombie_spawn(x, z, "")
    for (x, z) in ((-236.0, -200.0), (-190.0, -238.0)):
        b.zombie_spawn(x, z, "water", y=POND_BED)
    b.zombie_spawn(124.0, -110.0, "", y=-8.0)
    b.zombie_spawn(222.0, 146.0, "", y=-4.0)
