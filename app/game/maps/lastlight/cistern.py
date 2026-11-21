"""The Underneath -- Harrow's floodworks, under the town, the night of the storm.

Layout (north is +z), all of it under one brick vault::

   z +280 --------------- the storm drains come in from under the streets ----
          THE LIGHT SHAFT        THE INTAKE CHANNELS (two, pouring)    the
          (a street grate,       |                    |                drain
           rain coming down)     |                    |                junction
   z +120 ======== the north gallery ==== bridges over the channels ==========
          THE WEIR     THE GREAT CISTERN: a forest of pillars        THE PUMP
          (a cascade   standing in black water, catwalks across      HALL
           down to the it on posts                                   (four pumps,
           low channel)                                               the pit)
   z -120 ======== the south gallery ========================================
          THE CAMP          THE GATEKEEPER'S OFFICE    THE OLD SUBWAY PLATFORM
          (somebody lived   (the safe room)            (a car left on the
           down here)                                   track, tiles, posters)
   z -280 -------------------------------------------------------------------

Everybody deploys in the gatekeeper's office, among the gauge boards.

What makes it this place:

* **Underground.**  A roof over everything, forty units up: brick vault,
  work lights on the ceiling, the dark between them.  The only sky is a
  street grate at the top of the light shaft, rain coming through it.
* **The cistern.**  Pillars every thirty units standing in waist-deep
  water; catwalks cross it on posts.  Below the catwalks, they wade.
* **The lure.**  In the pump hall, the control desk on the mezzanine: start
  the pumps, and they roar -- and the horde comes to the pit in front of
  them.
* **Levels.**  The weir's cascade down to the low channel, the pump pit,
  the mezzanine, the subway's trackbed and platform, the sunken channels.
"""
from __future__ import annotations

import math
import random
from typing import List, Tuple

from .kit import (
    CONCRETE, CONCRETE_DARK, FLOOR, HAZARD, STEEL, STEEL_DARK, WOOD, WOOD_DARK, WOOD_LIGHT, Area,
    Surfaces, barrel_spot, bench, boundary, building, carve, crate, deploy_pad, flight, holed_wall,
    plate, post_sign, rect, sign_decal, slab, strip_light, supply_ammo, supply_med, threshold,
    wall_sign)
from ..relay.kit import mound

Rect = Tuple[float, float, float, float]

HALF = 280.0
SKY = {"top": "#05060a", "horizon": "#14161c", "sun": [0.2, 0.9, 0.3],
       "clouds": 0.0, "tint": "#8a9ab8"}
AMBIENT = "#3a3a44"

VAULT = 40.0
WALL = "#6a3a2e"
WALL_DARK = "#4a2a22"
TILE = "#c8c8b8"
SLUDGE = "#2a2a24"
WATER = "#1a2a2a"

CISTERN = rect(-160.0, 100.0, -100.0, 100.0)
CIS_FLOOR = -4.0
CIS_WATER = -1.5
CHANNELS = [rect(-60.0, -44.0, 100.0, 280.0), rect(40.0, 56.0, 100.0, 280.0)]
CHAN_FLOOR = -2.5
CHAN_WATER = -1.0
WEIR = rect(-192.0, -160.0, -40.0, 40.0)
LOW = rect(-236.0, -192.0, -120.0, 120.0)
LOW_FLOOR = -10.0
LOW_WATER = -7.6
PUMPS = rect(140.0, 270.0, -80.0, 80.0)
PIT = rect(150.0, 260.0, -24.0, 16.0)
PIT_FLOOR = -8.0
MEZZ = rect(140.0, 270.0, -140.0, -120.0)
MEZZ_Y = 8.0
OFFICE = rect(-60.0, 0.0, -200.0, -160.0)
TRACK = rect(40.0, 270.0, -250.0, -232.0)
TRACK_FLOOR = -2.4
PLATFORM = rect(40.0, 270.0, -232.0, -206.0)
PLATFORM_Y = 1.2
SHAFT = rect(-220.0, -196.0, 196.0, 220.0)
CAMP = rect(-220.0, -120.0, -230.0, -170.0)


def build(b: Area) -> None:
    rng = random.Random(0xC157)
    b.extra.update({"weather": "drips", "accent": "#5ab8c8"})
    s = Surfaces(b)
    _ground(b, s)
    boundary(b, VAULT, WALL_DARK, WALL_DARK, rng)
    _vault(b)
    _cistern(b, s)
    _channels(b, s)
    _weir(b, s)
    _galleries(b, s)
    _pump_hall(b, s)
    _office(b, s)
    _subway(b, s)
    _camp(b, s, rng)
    _shaft(b, s)
    _rubble(b, s, rng)
    _rigs(b)
    _zombie_spawns(b)
    for x, z, name in ((-30, -180, "the gatekeeper's office"), (-30, 0, "the great cistern"),
                       (-27, 30, "the catwalks"), (-52, 190, "the west channel"), (48, 190, "the east channel"),
                       (-176, 0, "the weir"), (-214, 0, "the low channel"), (205, 30, "the pump hall"),
                       (205, -4, "the pump pit"), (205, -70, "the mezzanine"), (155, -219, "the subway platform"),
                       (155, -241, "the trackbed"), (-170, -200, "the camp"), (-208, 208, "the light shaft"),
                       (200, 200, "the drain junction"), (-30, 110, "the north gallery"),
                       (-30, -110, "the south gallery")):
        b.landmark(float(x), float(z), name)
    b.camera(-160.0, 14.0, -112.0, -30.0, -2.0, 30.0)
    b.camera(140.0, 16.0, -70.0, 220.0, 0.0, 20.0)
    b.camera(60.0, 10.0, -210.0, 180.0, 2.0, -232.0)
    b.camera(-190.0, 6.0, 150.0, -208.0, 20.0, 208.0)


# ================================================================ ground
def _ground(b: Area, s: Surfaces) -> None:
    h = b.half + b.margin
    holes = [CISTERN, WEIR, LOW, PIT, TRACK] + CHANNELS
    for r in holes:
        s.reserve(r)
    pieces = carve(rect(-h, h, -h, h), holes)
    plate(b, pieces, 0.0, 0.6, CONCRETE_DARK, studs=True)
    plate(b, pieces, -0.6, 11.4, "#3a3430")


def _vault(b: Area) -> None:
    """The roof over everything, with the street grate's hole in it, and
    work lights fixed to it in rows."""
    h = b.half + b.margin
    plate(b, carve(rect(-h, h, -h, h), [SHAFT]), VAULT + 2.0, 2.0, WALL_DARK)
    for z in (-240.0, -190.0, -140.0, -60.0, 20.0, 80.0, 150.0, 230.0):
        for x in (-230.0, -130.0, -30.0, 70.0, 170.0, 250.0):
            if SHAFT[0] - 4.0 < x < SHAFT[1] + 4.0 and SHAFT[2] - 4.0 < z < SHAFT[3] + 4.0:
                continue
            strip_light(b, x, z, VAULT, 12.0, "x", "#e8d8b0")


# ============================================================== cistern
def _cistern(b: Area, s: Surfaces) -> None:
    """The great cistern: a sunk floor under black water, the pillars in
    their rows up to the vault, catwalks crossing on posts, steps down at
    the edges."""
    x0, x1, z0, z1 = CISTERN
    deep = -12.0
    slab(b, CISTERN, CIS_FLOOR, CIS_FLOOR - deep, SLUDGE, studs=True)
    b.water((x0 + x1) / 2.0, (z0 + z1) / 2.0, x1 - x0, z1 - z0, CIS_WATER, WATER)
    walks = [rect(x0, x1, -43.0, -37.0), rect(x0, x1, 57.0, 63.0), rect(-93.0, -87.0, z0, z1),
             rect(27.0, 33.0, z0, z1)]
    for k, r in enumerate(walks):
        pieces = [r] if k < 2 else carve(r, walks[:2])
        plate(b, pieces, 1.0, 0.4, WOOD, studs=True)
    for (a, c, d, e) in walks:
        along_x = (c - a) > (e - d)
        if along_x:
            for x in range(int(a) + 10, int(c) - 4, 16):
                if abs(x + 90.0) < 6.0 or abs(x - 30.0) < 6.0:
                    continue
                for zz in (d + 0.4, e - 0.4):
                    b.box([float(x), (CIS_FLOOR + 0.6) / 2.0, zz], [0.8, 0.6 - CIS_FLOOR, 0.8], WOOD_DARK)
        else:
            for z in range(int(d) + 10, int(e) - 4, 16):
                if abs(z + 40.0) < 6.0 or abs(z - 60.0) < 6.0:
                    continue
                for xx in (a + 0.4, c - 0.4):
                    b.box([xx, (CIS_FLOOR + 0.6) / 2.0, float(z)], [0.8, 0.6 - CIS_FLOOR, 0.8], WOOD_DARK)
    # the pillars, every thirty units, clear of the catwalks
    for i in range(9):
        for j in range(7):
            px = x0 + 15.0 + i * 30.0
            pz = z0 + 10.0 + j * 30.0
            if any(r[0] - 4.0 < px < r[1] + 4.0 and r[2] - 4.0 < pz < r[3] + 4.0 for r in walks):
                continue
            b.box([px, (CIS_FLOOR + VAULT) / 2.0, pz], [6.0, VAULT - CIS_FLOOR, 6.0], WALL)
            b.box([px, VAULT - 1.5, pz], [8.0, 3.0, 8.0], WALL_DARK)
            b.box([px, CIS_FLOOR + 1.5, pz], [7.2, 3.0, 7.2], WALL_DARK)
    # steps down from the galleries at the catwalk ends and between
    for (side, a, c) in (("z-", -20.0, -12.0), ("z-", 60.0, 68.0), ("z+", -130.0, -122.0), ("z+", 70.0, 78.0),
                         ("x+", -80.0, -72.0), ("x+", 20.0, 28.0)):
        if side == "z-":
            flight(b, "z", z0 + 6.0, z0, a, c, CIS_FLOOR, 0.0, CONCRETE_DARK, fill=CIS_FLOOR)
        elif side == "z+":
            flight(b, "z", z1 - 6.0, z1, a, c, CIS_FLOOR, 0.0, CONCRETE_DARK, fill=CIS_FLOOR)
        else:
            flight(b, "x", x1 - 6.0, x1, a, c, CIS_FLOOR, 0.0, CONCRETE_DARK, fill=CIS_FLOOR)
    supply_ammo(b, -150.0, 0.0, 110.0, "z-")
    supply_med(b, 110.0, 0.0, 60.0, "x-")
    barrel_spot(b, -90.0, 1.0, -20.0)
    barrel_spot(b, 30.0, 1.0, 20.0)


def _channels(b: Area, s: Surfaces) -> None:
    """The intake channels, sunk in the floor, bringing the storm in from
    under the streets to spill into the cistern; footbridges over them."""
    for (x0, x1, z0, z1) in CHANNELS:
        slab(b, rect(x0, x1, z0, z1), CHAN_FLOOR, CHAN_FLOOR + 12.0, SLUDGE, studs=True)
        b.water((x0 + x1) / 2.0, (z0 + z1) / 2.0, x1 - x0, z1 - z0, CHAN_WATER, WATER)
        for zb in (140.0, 230.0):
            slab(b, rect(x0 - 1.0, x1 + 1.0, zb - 4.0, zb + 4.0), 1.0, 0.6, STEEL, studs=True, material="metal")
        # the culvert's mouth in the north wall
        b.box([(x0 + x1) / 2.0, 14.0, 279.0], [x1 - x0 + 8.0, 4.0, 2.0], WALL_DARK)
        for x in (x0 - 2.0, x1 + 2.0):
            b.box([x, 6.0, 279.0], [4.0, 12.0, 2.0], WALL_DARK)


def _weir(b: Area, s: Surfaces) -> None:
    """The overflow weir: the cistern spills over its crest and down the
    cascade steps into the low channel, which runs the length of the west
    side under a catwalk."""
    wx0, wx1, wz0, wz1 = WEIR
    tops = [-1.6, -3.6, -5.6, -7.6]
    for k, top in enumerate(tops):
        a = wx1 - (k + 1) * 8.0
        slab(b, rect(a, a + 8.0, wz0, wz1), top, top + 12.0, CONCRETE, studs=True)
    lx0, lx1, lz0, lz1 = LOW
    slab(b, LOW, LOW_FLOOR, 2.0, SLUDGE, studs=True)
    b.water((lx0 + lx1) / 2.0, 0.0, lx1 - lx0, lz1 - lz0, LOW_WATER, WATER)
    # out of the low channel, at both ends
    flight(b, "z", lz0 + 10.0, lz0, lx0 + 6.0, lx0 + 14.0, LOW_FLOOR, 0.0, CONCRETE_DARK, fill=LOW_FLOOR)
    flight(b, "z", lz1 - 10.0, lz1, lx0 + 6.0, lx0 + 14.0, LOW_FLOOR, 0.0, CONCRETE_DARK, fill=LOW_FLOOR)
    # the catwalk along it, on brackets from the west wall
    slab(b, rect(lx0, lx0 + 5.0, lz0 + 10.0, lz1 - 10.0), 1.0, 0.4, STEEL, studs=True, material="metal")
    for z in range(int(lz0) + 20, int(lz1) - 10, 24):
        b.box([lx0 + 2.5, 0.0, float(z)], [5.0, 1.2, 0.8], STEEL_DARK)
    post_sign(b, -166.0, -48.0, 0.0, 2.0, 12.0, 1.6, sign_decal("OVERFLOW  KEEP CLEAR", HAZARD, "#1b1b1b", 7.5),
              "x+", HAZARD)


def _galleries(b: Area, s: Surfaces) -> None:
    """The galleries round the cistern and the walls that make the rooms
    and tunnels beyond them, arches through; a balustrade at the cistern's
    edge with gaps where the steps go down."""
    x0, x1, z0, z1 = CISTERN
    # the balustrade
    gaps_s = [(-20.0, -12.0), (60.0, 68.0), (-93.0, -87.0), (27.0, 33.0)]
    gaps_n = [(-130.0, -122.0), (70.0, 78.0), (-93.0, -87.0), (27.0, 33.0), (-60.0, -44.0), (40.0, 56.0)]
    for (z, gaps) in ((z0 - 0.6, gaps_s), (z1 + 0.6, gaps_n)):
        holed_wall(b, "x", z, 1.2, x0, x1, 0.0, 1.4, CONCRETE, [(a, c, -1.0, 2.0) for a, c in gaps])
    holed_wall(b, "z", x1 + 0.6, 1.2, z0 - 1.2, z1 + 1.2, 0.0, 1.4, CONCRETE,
               [(-80.0, -72.0, -1.0, 2.0), (20.0, 28.0, -1.0, 2.0), (-43.0, -37.0, -1.0, 2.0), (57.0, 63.0, -1.0, 2.0)])
    # the walls dividing the underneath: arches (doorways) through
    arch = 14.0
    # the north gallery's back wall, with the channels and a way to the shaft
    holed_wall(b, "x", 141.0, 2.0, -280.0, 280.0, 0.0, VAULT, WALL,
               [(-210.0, -196.0, -1.0, arch), (-62.0, -42.0, -6.0, arch), (38.0, 58.0, -6.0, arch),
                (150.0, 170.0, -1.0, arch)])
    # the south gallery's back wall: the office, the camp, the subway
    holed_wall(b, "x", -141.0, 2.0, -280.0, 280.0, 0.0, VAULT, WALL,
               [(-180.0, -166.0, -1.0, arch), (-40.0, -20.0, -1.0, arch), (90.0, 110.0, -1.0, arch)])
    # the pump hall's west wall
    holed_wall(b, "z", 131.0, 2.0, -140.0, 140.0, 0.0, VAULT, WALL,
               [(-10.0, 10.0, -1.0, arch), (50.0, 66.0, -1.0, arch), (-110.0, -96.0, -1.0, arch)])
    # the weir's walls, between the gallery and the low channel
    holed_wall(b, "z", -237.0, 2.0, -140.0, 140.0, 0.0, VAULT, WALL,
               [(-132.0, -122.0, -1.0, arch), (122.0, 132.0, -1.0, arch)])


def _pump_hall(b: Area, s: Surfaces) -> None:
    """The pump hall: four great pumps on their plinth, the motor houses on
    top, the manifold; the pit in front of them, sunk to the intakes; the
    mezzanine along the south wall with the control desk -- the lure."""
    px0, px1, pz0, pz1 = PIT
    slab(b, PIT, PIT_FLOOR, PIT_FLOOR + 12.0, SLUDGE, studs=True)
    b.water((px0 + px1) / 2.0, (pz0 + pz1) / 2.0, px1 - px0, pz1 - pz0, PIT_FLOOR + 1.6, WATER)
    flight(b, "x", px0 + 8.0, px0, -10.0, -2.0, PIT_FLOOR, 0.0, CONCRETE_DARK, fill=PIT_FLOOR)
    flight(b, "x", px1 - 8.0, px1, 2.0, 10.0, PIT_FLOOR, 0.0, CONCRETE_DARK, fill=PIT_FLOOR)
    s.reserve(rect(140.0, 270.0, 20.0, 70.0))
    slab(b, rect(150.0, 262.0, 22.0, 62.0), 2.0, 2.0, CONCRETE, studs=True)
    for k, x in enumerate((165.0, 192.0, 219.0, 246.0)):
        b.cyl([x, 2.0 + 9.0, 40.0], [16.0, 18.0, 16.0], "#3a5a6a", material="metal")
        b.box([x, 2.0 + 18.0 + 3.0, 40.0], [10.0, 6.0, 10.0], "#5a6a7a", material="metal")
        b.box([x, 2.0 + 18.0 + 6.6, 40.0], [3.0, 1.2, 3.0], STEEL_DARK)
        b.box([x, (PIT_FLOOR + 6.0) / 2.0, 14.0], [4.0, 6.0 - PIT_FLOOR, 4.0], STEEL_DARK, material="metal")
        b.box([x, 5.0, 24.0], [4.0, 2.0, 16.0], STEEL_DARK, material="metal")
        wall_sign(b, x, 2.0 + 9.0, 31.65, 6.0, 1.6, sign_decal("NO %d" % (k + 1), "#3a5a6a", "#e8e8e8", 3.8), "z-",
                  "#3a5a6a")
    b.box([205.5, 2.0 + 20.0, 54.0], [96.0, 3.0, 3.0], STEEL, material="metal")
    # the mezzanine and its stair, the desk
    mx0, mx1, mz0, mz1 = MEZZ
    slab(b, MEZZ, MEZZ_Y, 0.6, STEEL, studs=True, material="metal")
    for x in (150.0, 180.0, 210.0, 240.0, 262.0):
        b.box([x, (MEZZ_Y - 0.6) / 2.0, mz1 - 0.6], [1.2, MEZZ_Y - 0.6, 1.2], STEEL_DARK)
    b.box([(mx0 + 16.0 + mx1) / 2.0, MEZZ_Y + 0.6, mz1 - 0.3], [mx1 - mx0 - 16.0, 1.2, 0.6], HAZARD)
    flight(b, "z", mz1 + 16.0, mz1, mx0 + 6.0, mx0 + 12.0, 0.0, MEZZ_Y, STEEL_DARK, fill=0.0)
    b.box([205.0, MEZZ_Y + 1.4, -134.0], [16.0, 2.8, 3.0], "#4a5060", material="metal")
    b.box([205.0, MEZZ_Y + 3.2, -134.6], [16.0, 0.8, 1.2], "#2a2e36")
    b.set_lure(205.0, MEZZ_Y, -130.0, "the pumps", "Start the pumps", "ll_pumps", (205.0, PIT_FLOOR, -4.0))
    wall_sign(b, 205.0, MEZZ_Y + 9.0, -140.0 + 0.35, 30.0, 3.0,
              sign_decal("HARROW FLOODWORKS  PUMP HALL", "#e8e0cc", WALL_DARK, 10.0), "z+", "#e8e0cc")
    supply_ammo(b, 250.0, MEZZ_Y, -130.0, "x-")
    supply_med(b, 170.0, 0.0, -56.0, "z+")
    barrel_spot(b, 240.0, 0.0, 74.0)


def _office(b: Area, s: Surfaces) -> None:
    """The gatekeeper's office: tiled, the gauge boards, the desk, the bunks
    for the night men -- the safe room."""
    x0, x1, z0, z1 = OFFICE
    s.reserve(rect(x0 - 2.0, x1 + 2.0, z0 - 2.0, z1 + 2.0))
    building(b, OFFICE, 0.0, 14.0, TILE, roof_colour=CONCRETE_DARK, floor_colour="#6a6a62",
             doors={"z+": [(-40.0, -20.0, 11.0)], "x+": [(-186.0, -176.0, 10.0)]},
             windows={"z+": [(-56.0, -46.0, 4.0, 9.0), (-14.0, -4.0, 4.0, 9.0)]},
             glass=True, lights="#e8f0d8")
    threshold(b, OFFICE, "z+", (-40.0, -20.0))
    threshold(b, OFFICE, "x+", (-186.0, -176.0))
    wall_sign(b, -30.0, 12.4, z1 + 0.35, 26.0, 2.0, sign_decal("GATEKEEPER", TILE, WALL_DARK, 13.0), "z+", TILE)
    floor = FLOOR
    for z in (-172.0, -186.0):
        for k in range(8):
            x = -54.0 + k * 6.0
            deploy_pad(b, x, z, floor, "#5ab8c8", 4.8)
            b.safe_spawn(x, floor + 0.6, z, 0.0)
    for k in range(4):
        b.box([-50.0 + k * 9.0, 7.0, z0 + 2.06], [7.0, 6.0, 0.12], "#e8e0cc", collide=False)
    supply_ammo(b, -6.0, floor, -194.0, "x-")
    supply_med(b, -54.0, floor, -196.6, "z+")


def _subway(b: Area, s: Surfaces) -> None:
    """The old subway platform the floodworks swallowed: the trackbed sunk
    beside it, rails, a car left on the line; the platform's tiles, its
    benches, the posters, the stair down."""
    tx0, tx1, tz0, tz1 = TRACK
    slab(b, TRACK, TRACK_FLOOR, TRACK_FLOOR + 12.0, "#4a4a44", studs=True)
    for z in (tz0 + 5.0, tz1 - 5.0):
        b.box([(tx0 + tx1) / 2.0, TRACK_FLOOR + 0.2, z], [tx1 - tx0, 0.4, 0.4], "#8a8f94", material="metal")
    x0, x1, z0, z1 = PLATFORM
    s.reserve(PLATFORM)
    slab(b, PLATFORM, PLATFORM_Y, PLATFORM_Y, TILE, studs=True)
    flight(b, "z", tz1 - 6.0, tz1, 250.0, 258.0, TRACK_FLOOR, PLATFORM_Y, CONCRETE_DARK, fill=TRACK_FLOOR)
    holed_wall(b, "x", z1 + 1.0, 2.0, x0, x1, 0.0, 18.0, TILE, [(90.0, 110.0, -1.0, 12.0)])
    b.box([x0 + (x1 - x0) / 2.0, PLATFORM_Y + 0.05, z0 + 0.6], [x1 - x0, 0.1, 1.2], HAZARD, collide=False)
    # the car
    cx = 150.0
    cz = (tz0 + tz1) / 2.0
    b.box([cx, -2.0 + 5.0, cz], [60.0, 10.0, 12.0], "#8a2a24", material="metal")
    b.box([cx, 8.4, cz], [60.0, 0.8, 11.0], "#5a1a18", material="metal")
    for k in range(6):
        b.box([cx - 25.0 + k * 10.0, 4.0, cz + 6.05], [5.0, 3.0, 0.1], "#e8d8a0", material="glass",
              collide=False, alpha=0.6)
    wall_sign(b, cx, 1.0, cz + 6.35, 14.0, 1.4, sign_decal("HARROW HEIGHTS", "#8a2a24", "#f2f2f2", 10.0),
              "z+", "#8a2a24")
    for x in (80.0, 120.0, 190.0, 230.0):
        bench(b, x, z1 - 4.0, "x", y=PLATFORM_Y)
    for k, x in enumerate((70.0, 140.0, 210.0)):
        b.box([x, PLATFORM_Y + 6.0, z1 - 0.06], [10.0, 6.0, 0.12], ["#c8582a", "#3a7ac8", "#d8a02a"][k], collide=False)
    wall_sign(b, 170.0, PLATFORM_Y + 11.0, z1 - 0.35, 30.0, 2.6, sign_decal("FLOODWORKS  ALIGHT HERE", TILE, "#1b1b1b", 11.5),
              "z-", TILE)
    supply_ammo(b, 255.0, PLATFORM_Y, -212.0, "z+")
    barrel_spot(b, 60.0, PLATFORM_Y, -220.0)


def _camp(b: Area, s: Surfaces, rng: random.Random) -> None:
    """Somebody lived down here: mattresses, a barrel for a fire, crates for
    a table, a line strung with washing, the candles on a shelf."""
    x0, x1, z0, z1 = CAMP
    for (x, z) in ((-200.0, -214.0), (-188.0, -214.0), (-140.0, -180.0)):
        b.box([x, 0.4, z], [5.0, 0.8, 9.0], "#6a6a8a")
    b.cyl([-170.0, 2.0, -200.0], [3.2, 4.0, 3.2], "#6a4a3a", material="metal")
    for (x, z) in ((-160.0, -196.0), (-180.0, -192.0)):
        crate(b, x, 0.0, z, 3.0, WOOD)
    crate(b, -170.0, 0.0, -186.0, 4.0, WOOD_DARK)
    b.box([-150.0, 6.0, -226.0], [16.0, 0.4, 3.0], WOOD_LIGHT)
    for x in (-157.6, -142.4):
        b.box([x, 2.9, -226.0], [0.8, 5.8, 3.0], WOOD_DARK)
    wall_sign(b, -205.0, 8.0, -141.0 - 1.35, 16.0, 3.0, sign_decal("THEY HEAR THE PUMPS", WALL, "#e8e0cc", 5.3), "z-",
              WALL)
    supply_med(b, -214.0, 0.0, -176.0, "z-")
    barrel_spot(b, -130.0, 0.0, -160.0)


def _shaft(b: Area, s: Surfaces) -> None:
    """The light shaft: a square well up through the vault to a street
    grate; the rain comes through it, and the street lamp's light."""
    x0, x1, z0, z1 = SHAFT
    for (a, c, d, e) in ((x0 - 2.0, x0, z0 - 2.0, z1 + 2.0), (x1, x1 + 2.0, z0 - 2.0, z1 + 2.0),
                         (x0, x1, z0 - 2.0, z0), (x0, x1, z1, z1 + 2.0)):
        b.box([(a + c) / 2.0, VAULT + 2.0 + 10.0, (d + e) / 2.0], [c - a, 20.0, e - d], WALL_DARK)
    for k in range(5):
        b.box([x0 + 2.0 + k * 5.0, VAULT + 22.0 + 0.4, (z0 + z1) / 2.0], [0.8, 0.8, z1 - z0], STEEL_DARK)
    b.box([(x0 + x1) / 2.0, 0.6, (z0 + z1) / 2.0], [8.0, 1.2, 8.0], "#4a4a40")
    supply_ammo(b, x1 - 4.0, 0.0, z1 - 10.0, "x-")


def _rubble(b: Area, s: Surfaces, rng: random.Random) -> None:
    """Where the vault has let go: rubble heaps on the gallery floors and in
    the junction, brick and timber."""
    for (cx, cz, rx, rz) in ((200.0, 200.0, 26.0, 20.0), (-120.0, 200.0, 20.0, 14.0), (120.0, 200.0, 16.0, 14.0),
                             (-90.0, -250.0, 18.0, 12.0), (230.0, -150.0, 18.0, 14.0)):
        s.reserve(rect(cx - rx, cx + rx, cz - rz, cz + rz))
        mound(b, cx, cz, rx, rz, 3, 1.4, [WALL_DARK, "#5a3a2e", "#3a2a22"])
    barrel_spot(b, 160.0, 0.0, 230.0)
    barrel_spot(b, -20.0, 0.0, 124.0)
    barrel_spot(b, 190.0, 0.0, -170.0)
    supply_ammo(b, 236.0, 0.0, 244.0, "x-")


# ================================================================ rigs
def _rigs(b: Area) -> None:
    for (x0, x1, z0, z1) in CHANNELS:
        b.rig("storm_inflow", (x0 + x1) / 2.0, CHAN_WATER, 200.0, 0.0, w=x1 - x0, z0=z0, z1=z1, pour=CIS_WATER)
    b.rig("weir_cascade", WEIR[1], CIS_WATER, 0.0, 0.0, w=WEIR[3] - WEIR[2], drop=CIS_WATER - LOW_WATER, run=WEIR[1] - WEIR[0])
    b.rig("pumps", 205.0, 2.0, 40.0, 0.0, xs=[165.0, 192.0, 219.0, 246.0], pit=PIT_FLOOR + 1.6)
    b.rig("light_shaft", (SHAFT[0] + SHAFT[1]) / 2.0, VAULT + 22.0, (SHAFT[2] + SHAFT[3]) / 2.0, 0.0,
          w=SHAFT[1] - SHAFT[0])
    b.rig("work_lamps", 0.0, VAULT, 0.0, 0.0,
          lamps=[[-120.0, VAULT, -20.0], [0.0, VAULT, 50.0], [60.0, VAULT, -70.0], [-60.0, VAULT, 120.0],
                 [205.0, VAULT, 30.0], [155.0, VAULT, -219.0]])
    b.rig("barrel_fire", -170.0, 4.0, -200.0, 0.0)
    b.rig("sewer_gator", 48.0, CHAN_WATER, 220.0, 0.0, area=[42.0, 54.0, 110.0, 270.0])
    b.rig("paper_boat", -52.0, CHAN_WATER, 200.0, 0.0, z0=110.0, z1=270.0)
    b.rig("rats", 0.0, 0.0, 0.0, 0.0,
          runs=[[-150.0, -116.0, 100.0, -116.0], [150.0, 116.0, -150.0, 116.0], [60.0, -204.0, 260.0, -204.0]])
    b.rig("flood_siren", 205.0, MEZZ_Y + 12.0, -79.0, 0.0)


# ============================================================== spawns
def _zombie_spawns(b: Area) -> None:
    for (x0, x1, z0, z1) in CHANNELS:
        for z in (250.0, 180.0):
            b.zombie_spawn((x0 + x1) / 2.0, z, "water", y=CHAN_FLOOR)
    for (x, z) in ((-130.0, 80.0), (70.0, 80.0), (-130.0, -20.0), (80.0, 30.0), (-60.0, 85.0)):
        b.zombie_spawn(x, z, "water", y=CIS_FLOOR)
    for (x, z) in ((-214.0, 100.0), (-214.0, -100.0), (-214.0, 40.0)):
        b.zombie_spawn(x, z, "water", y=LOW_FLOOR)
    for (x, z) in ((250.0, 250.0), (180.0, 260.0), (-250.0, 250.0), (-120.0, 250.0), (100.0, 250.0),
                   (260.0, 120.0), (260.0, -120.0), (-260.0, -260.0), (-258.0, -60.0), (250.0, -160.0),
                   (0.0, 250.0), (-180.0, 160.0)):
        b.zombie_spawn(x, z, "")
    b.zombie_spawn(240.0, -241.0, "", y=TRACK_FLOOR)
    b.zombie_spawn(-260.0, 120.0, "")
    b.zombie_spawn(100.0, -264.0, "")
