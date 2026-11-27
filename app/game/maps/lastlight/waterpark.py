"""Splash Kingdom -- the water park, the last night of the season.

Layout (north is +z)::

   z +280 ------- the staff lot -------- the chlorine store ---------------------------
          THE WAVE POOL: the beach at the south end stepping down to the deep
          end, the wave machine's house behind it (the lure); cabanas either
          side, the lifeguard chairs                   THE KRAKEN (the slide tower)
                                                       and its splash basin
   z  +33 ============================ the promenade ===================================
          THE LAZY RIVER round VOLCANO ISLAND   FORT SPLASHMORE on the      THE DIVE POOL
          (the bridges)                         splash pad (the big bucket) (drained; the
                                                THE SNACK SHACK             high boards)
          LIFEGUARD HQ (the safe room)   KING SPLASH   THE GIFT SHOP
   z -237 ---------------------- the fence, the gate ---------------------------------
          THE CAR PARK

Everybody deploys in Lifeguard HQ, between the rescue boards and the lockers.

What makes it this place:

* **Water at every level.**  Pools you can wade -- the wave pool's beach
  stepping down to the deep end, the lazy river's channel round the
  island, the splash basin -- and the one you cannot swim in: the dive pool,
  drained, ten deep, a pit with stairs down and high boards over it.
* **Up.**  Fort Splashmore's decks under the big bucket, the Kraken's three
  platforms up its switchback stairs, the volcano's terraces, the high
  boards, the lifeguard chairs -- everywhere to stand over the water.
* **The lure.**  In the wave machine's house: sound the horn, and the
  waves start rolling down the pool -- and every one of the dead in the
  park comes down to the beach.
* **At night.**  The pools glowing, steam coming off them into the cold,
  the bucket filling and tipping, inner tubes drifting round the river on
  their own.  One of them has a passenger.
"""
from __future__ import annotations

import math
import random
from typing import Tuple

from .kit import (
    ASPHALT, CONCRETE, FLOOR, HAZARD, WARM, WOOD, WOOD_DARK, WOOD_LIGHT, Area, Surfaces,
    barrel_spot, boundary, building, bus, car, carve, deploy_pad, flight, lamp_post, plate,
    post_sign, rect, sign_decal, slab, supply_ammo, supply_med, tent, threshold, van, wall_sign)
from ..relay.kit import board_letters, rails

Rect = Tuple[float, float, float, float]

HALF = 280.0
SKY = {"top": "#081420", "horizon": "#2a4a5a", "sun": [0.2, 0.35, 0.8],
       "clouds": 0.4, "tint": "#b0d0d8"}
AMBIENT = "#4a6a72"

DECK = "#c8c4b8"
SANDY = "#e0cc9a"
TILE = "#3ab8c8"
TILE_DEEP = "#2a8aa8"
RUBBER = "#3a6ac8"
GRASS = "#4a7a3a"
STUCCO = "#e8d0a0"
TEAL = "#2ac8c8"
CORAL = "#ff7a5a"
SUNNY = "#ffd84a"
PURPLE = "#7a3aa8"
POOL_WATER = "#3ac8d8"

CAR_PARK = rect(-280.0, 280.0, -280.0, -238.0)
FENCE = (-238.0, -236.0)
GATE = (-24.0, 24.0)
HQ = rect(-120.0, -40.0, -228.0, -188.0)
GIFT = rect(40.0, 110.0, -228.0, -200.0)
KING = (0.0, -204.0)
LAZY_OUT = rect(-262.0, -92.0, -162.0, 8.0)
LAZY_IN = rect(-248.0, -106.0, -148.0, -6.0)
LAZY_BED = -2.0
LAZY_WATER = -0.8
VOLCANO = rect(-215.0, -139.0, -115.0, -39.0)
PAD = rect(20.0, 112.0, -160.0, -66.0)
D1 = rect(40.0, 90.0, -132.0, -100.0)
D2 = rect(50.0, 80.0, -126.0, -106.0)
D3 = rect(58.0, 72.0, -120.0, -112.0)
SNACK = rect(132.0, 174.0, -156.0, -128.0)
DIVE = rect(150.0, 210.0, -60.0, 0.0)
DIVE_BED = -10.0
PROM = rect(-280.0, 280.0, 26.0, 40.0)
WAVE = rect(-90.0, 70.0, 80.0, 210.0)
WAVE_BANDS = ((80.0, 110.0, -1.0), (110.0, 140.0, -2.0), (140.0, 170.0, -3.0), (170.0, 210.0, -4.0))
WAVE_WATER = -0.5
MACHINE = rect(-50.0, 30.0, 216.0, 240.0)
KRAKEN = rect(150.0, 170.0, 110.0, 130.0)
BASIN = rect(180.0, 240.0, 60.0, 130.0)
BASIN_BED = -3.0
BASIN_WATER = -0.6
CHLORINE = rect(120.0, 170.0, 248.0, 272.0)
STAFF_LOT = rect(-260.0, -120.0, 248.0, 276.0)


def build(b: Area) -> None:
    rng = random.Random(0x5AA7)
    b.extra.update({"weather": "steam", "accent": "#4ae8f2"})
    s = Surfaces(b)
    _ground(b, s)
    boundary(b, 30.0, "#2a3a3a", "#223030", rng, horizon="city")
    _entrance(b, s)
    _hq(b, s)
    _gift_shop(b, s)
    _lazy_river(b, s)
    _fort(b, s)
    _snack_shack(b, s)
    _dive_pool(b, s)
    _wave_pool(b, s)
    _machine_house(b, s)
    _kraken(b, s)
    _staff(b, s)
    _grounds(b, s, rng)
    _paths(b, s)
    _rigs(b)
    _zombie_spawns(b)
    for x, z, name in ((-80, -208, "Lifeguard HQ"), (0, -236, "the gate"), (0, -258, "the car park"),
                       (0, -204, "King Splash"), (75, -214, "the gift shop"), (-255, -77, "the lazy river"),
                       (-177, -77, "the volcano"), (65, -116, "Fort Splashmore"), (65, -110, "the big bucket"),
                       (153, -142, "the snack shack"), (180, -30, "the dive pool"), (182, 8, "the high boards"),
                       (-10, 140, "the wave pool"), (-10, 228, "the wave machine"), (-111, 150, "the cabanas"),
                       (77, 120, "the lifeguard chair"), (160, 120, "the Kraken"), (210, 95, "the splash basin"),
                       (145, 260, "the chlorine store"), (-190, 262, "the staff lot"), (0, 33, "the promenade")):
        b.landmark(float(x), float(z), name)
    b.camera(-40.0, 30.0, 40.0, -10.0, 0.0, 150.0)
    b.camera(110.0, 34.0, 60.0, 165.0, 18.0, 110.0)
    b.camera(-120.0, 26.0, 10.0, -177.0, 8.0, -77.0)
    b.camera(110.0, 24.0, -40.0, 180.0, -6.0, -30.0)


# ================================================================ helpers
def _palm(b: Area, x: float, z: float, sc: float, y: float = 0.0) -> None:
    """A park palm: a ringed trunk and a crown of fronds."""
    h = 9.0 * sc
    b.cyl([x, y + h / 2.0, z], [1.2 * sc, h, 1.2 * sc], "#8a6a4a")
    for k in range(7):
        yaw = k / 7.0 * math.pi * 2.0
        b.box([x + math.sin(yaw) * 2.4 * sc, y + h + 0.2 + k * 0.03, z + math.cos(yaw) * 2.4 * sc],
              [1.4 * sc, 0.2, 5.0 * sc], "#2a7a3a", r=[0, yaw, 0], collide=False)
    b.sphere([x, y + h + 0.3, z], [1.8 * sc, 1.4 * sc, 1.8 * sc], "#3a8a3a", collide=False)


def _lifeguard_chair(b: Area, x: float, z: float, facing: float) -> None:
    """A lifeguard's chair: four legs, the seat up high under its umbrella,
    a steep stair up the back.  ``facing`` +1 looks toward +x."""
    for dx in (-1.6, 1.6):
        for dz in (-1.6, 1.6):
            b.box([x + dx, 3.0, z + dz], [0.6, 6.0, 0.6], "#f2f2ee")
    slab(b, rect(x - 2.0, x + 2.0, z - 2.0, z + 2.0), 6.4, 0.4, CORAL, studs=True)
    b.box([x - facing * 1.8, 7.6, z], [0.4, 2.4, 4.0], "#f2f2ee")
    b.cyl([x, 9.2, z], [0.3, 5.6, 0.3], "#f2f2ee")
    b.cone([x, 12.4, z], [6.0, 1.2, 6.0], CORAL, collide=False)
    flight(b, "z", z - 8.0, z - 2.0, x - 1.0, x + 1.0, 0.0, 6.4, "#f2f2ee", fill=0.0)


def _deck_legs(b: Area, r: Rect, top: float, base: float, colour: str) -> None:
    for (x, z) in ((r[0] + 0.4, r[2] + 0.4), (r[1] - 0.4, r[2] + 0.4), (r[0] + 0.4, r[3] - 0.4), (r[1] - 0.4, r[3] - 0.4)):
        b.box([x, (base + top - 0.6) / 2.0, z], [0.8, top - 0.6 - base, 0.8], colour)


def _bridge(b: Area, deck: Rect, axis: str, colour: str) -> None:
    """A footbridge over the lazy river high enough to wade under: the
    deck, and a stair up to it from either bank."""
    top = 4.6
    slab(b, deck, top, 0.6, colour, studs=True)
    x0, x1, z0, z1 = deck
    if axis == "z":
        flight(b, "z", z0 - 10.0, z0, x0, x1, 0.0, top, colour, fill=0.0)
        flight(b, "z", z1 + 10.0, z1, x0, x1, 0.0, top, colour, fill=0.0)
    else:
        flight(b, "x", x0 - 10.0, x0, z0, z1, 0.0, top, colour, fill=0.0)
        flight(b, "x", x1 + 10.0, x1, z0, z1, 0.0, top, colour, fill=0.0)


# ================================================================ ground
def _ground(b: Area, s: Surfaces) -> None:
    h = b.half + b.margin
    channel = carve(LAZY_OUT, [LAZY_IN])
    holes = channel + [DIVE, WAVE, BASIN]
    for r in holes:
        s.reserve(r)
    pieces = carve(rect(-h, h, -h, h), holes)
    plate(b, pieces, 0.0, 0.6, GRASS, studs=True, material="grass")
    plate(b, pieces, -0.6, 5.4, "#5a4a38")


# ============================================================== entrance
def _entrance(b: Area, s: Surfaces) -> None:
    """The fence with the gate in it under the park's arch, the turnstiles,
    the ticket booths outside, King Splash on his plinth inside."""
    z0, z1 = FENCE
    for (x0, x1) in ((-280.0, GATE[0] - 4.0), (GATE[1] + 4.0, 280.0)):
        b.box([(x0 + x1) / 2.0, 2.5, (z0 + z1) / 2.0], [x1 - x0, 5.0, z1 - z0], STUCCO)
        b.box([(x0 + x1) / 2.0, 5.3, (z0 + z1) / 2.0], [x1 - x0, 0.6, z1 - z0 + 0.6], TEAL)
    for x in (GATE[0] - 2.0, GATE[1] + 2.0):
        b.box([x, 7.0, (z0 + z1) / 2.0], [4.0, 14.0, 4.0], TEAL)
    b.box([0.0, 15.0, (z0 + z1) / 2.0], [GATE[1] - GATE[0] + 8.0, 2.0, 2.4], TEAL)
    board_letters(b, 0.0, 17.6, (z0 + z1) / 2.0, "SPLASH KINGDOM", 3.2, SUNNY, PURPLE, facing="z-", solid=True)
    for x in (-12.0, 0.0, 12.0):
        b.box([x, 0.3 + 0.7, (z0 + z1) / 2.0], [1.0, 1.4, 1.6], "#8a8f94", material="metal")
    for side in (-1, 1):
        booth = rect(side * 30.0 - 6.0, side * 30.0 + 6.0, -254.0, -244.0)
        building(b, booth, 0.3, 8.0, STUCCO, roof_colour=TEAL, floor_colour="#8a8a86",
                 doors={"z+": [(side * 30.0 - 2.0, side * 30.0 + 2.0, 0.3 + 6.5)]},
                 windows={"z-": [(side * 30.0 - 4.0, side * 30.0 + 4.0, 3.5, 6.5)]}, glass=True, lights=WARM)
        threshold(b, booth, "z+", (side * 30.0 - 2.0, side * 30.0 + 2.0), y0=0.3)
        wall_sign(b, side * 30.0, 9.6, -254.35, 10.0, 1.4, sign_decal("TICKETS", STUCCO, PURPLE, 7.1), "z-", STUCCO)
    # King Splash: the park's frog king, crowned, trident up, spouting
    kx, kz = KING
    b.box([kx, 1.0, kz], [8.0, 2.0, 8.0], "#d8d0c0")
    b.sphere([kx, 5.0, kz], [6.0, 6.0, 5.0], "#4aa83a")
    b.sphere([kx, 9.0, kz + 0.5], [5.0, 4.0, 4.4], "#4aa83a")
    for side in (-1, 1):
        b.sphere([kx + side * 1.4, 10.8, kz + 1.6], [1.6, 1.6, 1.6], "#f2f2ee")
        b.sphere([kx + side * 1.4, 10.9, kz + 2.3], [0.7, 0.7, 0.4], "#1a1a1a")
        b.sphere([kx + side * 2.6, 2.6, kz + 1.0], [2.4, 1.4, 3.0], "#3a8a2a")
    b.cyl([kx, 11.6, kz], [2.6, 1.2, 2.6], "#e8c35a", material="metal")
    b.box([kx + 3.6, 7.0, kz], [0.4, 12.0, 0.4], "#e8c35a", material="metal")
    b.box([kx + 3.6, 13.2, kz], [2.0, 0.4, 0.4], "#e8c35a", material="metal")
    post_sign(b, -18.0, -226.0, 0.3, 3.0, 12.0, 2.6, sign_decal("WELCOME TO SPLASH KINGDOM", "#f2f2ee", PURPLE, 4.6),
              "z-", "#f2f2ee")
    post_sign(b, 18.0, -226.0, 0.3, 3.0, 12.0, 2.6, sign_decal("LAST NIGHT OF THE SEASON", SUNNY, "#1b1b1b", 4.6),
              "z-", SUNNY)


def _hq(b: Area, s: Surfaces) -> None:
    """Lifeguard HQ and first aid: the lockers, the rescue boards on the
    wall, the PA desk, the lost property -- the safe room."""
    x0, x1, z0, z1 = HQ
    s.reserve(rect(x0 - 2.0, x1 + 2.0, z0 - 2.0, z1 + 2.0))
    y = 0.3
    slab(b, rect(x0 - 2.0, x1 + 2.0, z0 - 2.0, z1 + 2.0), y, y, CONCRETE)
    building(b, HQ, y, 11.0, "#f2f2ee", roof_colour=CORAL, floor_colour="#8aa8b0",
             doors={"z+": [(-88.0, -72.0, y + 8.5)], "x+": [(-214.0, -206.0, y + 8.5)]},
             windows={"z+": [(-114.0, -96.0, y + 3.5, y + 7.5), (-64.0, -46.0, y + 3.5, y + 7.5)],
                      "x-": [(-220.0, -196.0, y + 3.5, y + 7.5)]},
             glass=True, lights="#f2fbff")
    threshold(b, HQ, "z+", (-88.0, -72.0), y0=y)
    threshold(b, HQ, "x+", (-214.0, -206.0), y0=y)
    wall_sign(b, -80.0, y + 9.8, z1 + 0.35, 22.0, 1.6, sign_decal("LIFEGUARD HQ  FIRST AID", "#c42b20", "#f2f2ee", 13.75),
              "z+", "#c42b20")
    floor = y + FLOOR
    for z in (-216.0, -200.0):
        for k in range(8):
            x = -112.0 + k * 9.4
            deploy_pad(b, x, z, floor, "#4ae8f2", 4.8)
            b.safe_spawn(x, floor + 0.6, z, 0.0)
    for k in range(6):
        b.box([-116.0 + k * 3.2, floor + 3.0, z0 + 3.0], [3.0, 6.0, 2.0], ["#3a6ac8", "#c83a3a"][k % 2], material="metal")
    for k in range(3):
        b.box([x1 - 2.2, floor + 4.5, -224.0 + k * 3.0], [0.4, 8.0, 2.0], [CORAL, SUNNY, TEAL][k])
    b.box([-60.0, floor + 1.5, z0 + 3.2], [10.0, 3.0, 2.4], WOOD_DARK)
    b.box([-60.0, floor + 3.0 + 0.6, z0 + 3.0], [1.6, 1.2, 1.0], "#2a2a2e", material="metal")
    b.box([-48.0, floor + 1.2, z0 + 3.4], [4.0, 2.4, 3.0], "#8a5a3a")
    supply_ammo(b, -52.0, floor, -194.0, "x-")
    supply_med(b, -112.0, floor, -192.0, "z-")


def _gift_shop(b: Area, s: Surfaces) -> None:
    """The gift shop: floaties, beach balls, towels with the King on them."""
    x0, x1, z0, z1 = GIFT
    s.reserve(rect(x0 - 2.0, x1 + 2.0, z0 - 2.0, z1 + 2.0))
    y = 0.3
    slab(b, rect(x0 - 2.0, x1 + 2.0, z0 - 2.0, z1 + 2.0), y, y, CONCRETE)
    building(b, GIFT, y, 10.0, SUNNY, roof_colour=PURPLE, floor_colour="#8a8a86",
             doors={"z+": [(66.0, 84.0, y + 8.0)]}, windows={"z+": [(44.0, 62.0, y + 3.0, y + 7.0), (88.0, 106.0, y + 3.0, y + 7.0)]},
             glass=True, lights="#fff2d8")
    threshold(b, GIFT, "z+", (66.0, 84.0), y0=y)
    wall_sign(b, 75.0, y + 8.9, z1 + 0.35, 24.0, 1.4, sign_decal("THE ROYAL GIFT SHOP", SUNNY, PURPLE, 17.0), "z+", SUNNY)
    floor = y + FLOOR
    balls = [CORAL, TEAL, SUNNY, "#3a6ac8", "#f2f2ee"]
    for k in range(3):
        x = 52.0 + k * 22.0
        b.box([x, floor + 1.6, -216.0], [12.0, 3.2, 3.0], WOOD_LIGHT)
        for j in range(4):
            b.sphere([x - 4.5 + j * 3.0, floor + 3.2 + 1.0, -216.0], [2.0, 2.0, 2.0], balls[(k + j) % 5])
    supply_ammo(b, 104.0, floor, -224.0, "z+")
    supply_med(b, 46.0, floor, -224.4, "z+")


# ============================================================ lazy river
def _lazy_river(b: Area, s: Surfaces) -> None:
    """The lazy river: a channel round Volcano Island, wade-deep, four
    footbridges high enough to float under; on the island the volcano in
    terraces with the lava glowing in its top and the falls down its face."""
    for r in carve(LAZY_OUT, [LAZY_IN]):
        slab(b, r, LAZY_BED, 6.0 + LAZY_BED, TILE, studs=True)
        b.water((r[0] + r[1]) / 2.0, (r[2] + r[3]) / 2.0, r[1] - r[0], r[3] - r[2], LAZY_WATER, POOL_WATER)
    _bridge(b, rect(-180.0, -172.0, -164.0, -146.0), "z", WOOD)
    _bridge(b, rect(-180.0, -172.0, -8.0, 10.0), "z", WOOD)
    _bridge(b, rect(-264.0, -246.0, -80.0, -72.0), "x", WOOD)
    _bridge(b, rect(-108.0, -90.0, -80.0, -72.0), "x", WOOD)
    s.reserve(VOLCANO)
    for k in range(8):
        r = rect(VOLCANO[0] + 4.0 * k, VOLCANO[1] - 4.0 * k, VOLCANO[2] + 4.0 * k, VOLCANO[3] - 4.0 * k)
        slab(b, r, 2.0 * (k + 1), 2.0, ["#5a4a3a", "#4a3a2e"][k % 2], studs=True)
    vx, vz = (VOLCANO[0] + VOLCANO[1]) / 2.0, (VOLCANO[2] + VOLCANO[3]) / 2.0
    b.box([vx, 16.05, vz], [8.0, 0.1, 8.0], "#ff4a1a", material="neon", collide=False)
    supply_med(b, vx + 6.0, 16.0, vz + 6.0, "z-")
    for (x, z) in ((-236.0, -136.0), (-118.0, -136.0), (-236.0, -18.0), (-120.0, -20.0), (-160.0, -130.0)):
        _palm(b, x, z, 1.0)
    barrel_spot(b, -225.0, 0.0, -60.0)


# ================================================================ fort
def _fort(b: Area, s: Surfaces) -> None:
    """Fort Splashmore on the splash pad: three decks of timber stepping
    up, rails round them, the sprayers round the pad, and on top the big
    bucket on its gantry, filling."""
    s.reserve(PAD)
    slab(b, PAD, 0.3, 0.3, RUBBER, studs=True)
    for r, top, base in ((D1, 5.0, 0.3), (D2, 10.0, 5.0), (D3, 15.0, 10.0)):
        slab(b, r, top, 0.6, WOOD, studs=True)
        _deck_legs(b, r, top, base, WOOD_DARK)
    flight(b, "z", -150.0, D1[2], 40.0, 46.0, 0.3, 5.0, WOOD_DARK, fill=0.3)
    flight(b, "x", 88.0, D2[1], -126.0, -120.0, 5.0, 10.0, WOOD_DARK, fill=5.0)
    flight(b, "z", -108.0, D3[3], 62.0, 68.0, 10.0, 15.0, WOOD_DARK, fill=10.0)
    rails(b, D1, 5.0, 2.4, SUNNY, 0.6, gaps={"z-": [(40.0, 46.0)]})
    rails(b, D2, 10.0, 2.4, CORAL, 0.6, gaps={"x+": [(-126.0, -120.0)]})
    rails(b, D3, 15.0, 2.4, TEAL, 0.6, gaps={"z+": [(62.0, 68.0)]})
    for x in (59.2, 70.8):
        b.box([x, 15.0 + 5.0, -116.0], [1.2, 10.0, 1.2], PURPLE)
    b.box([65.0, 25.6, -116.0], [13.0, 1.2, 1.4], PURPLE)
    wall_sign(b, 65.0, 7.4, D1[2] - 0.35, 18.0, 1.6, sign_decal("FORT SPLASHMORE", SUNNY, PURPLE, 11.25), "z-", SUNNY)
    for (x, z) in ((28.0, -150.0), (28.0, -76.0), (104.0, -150.0), (104.0, -76.0), (98.0, -94.0), (30.0, -112.0)):
        b.cyl([x, 0.3 + 1.6, z], [0.8, 3.2, 0.8], TEAL, material="metal")
    supply_ammo(b, 60.0, 5.0, -104.0, "z-")
    barrel_spot(b, 106.0, 0.3, -120.0)


def _snack_shack(b: Area, s: Surfaces) -> None:
    """Kraken Bites: hot dogs and slushies, the tables under their
    umbrellas on the deck in front."""
    x0, x1, z0, z1 = SNACK
    s.reserve(rect(x0 - 2.0, x1 + 2.0, z0 - 30.0, z1 + 2.0))
    y = 0.3
    slab(b, rect(x0 - 2.0, x1 + 2.0, z0 - 30.0, z1 + 2.0), y, y, CONCRETE)
    building(b, SNACK, y, 9.0, CORAL, roof_colour=TEAL, floor_colour="#8a8a86",
             doors={"x-": [(-146.0, -138.0, y + 7.0)]}, windows={"z-": [(138.0, 168.0, y + 3.0, y + 6.5)]},
             glass=True, lights="#fff2d8")
    threshold(b, SNACK, "x-", (-146.0, -138.0), y0=y)
    wall_sign(b, 153.0, y + 7.8, z0 - 0.35, 20.0, 1.4, sign_decal("KRAKEN BITES", CORAL, "#f2f2ee", 14.3), "z-", CORAL)
    floor = y + FLOOR
    b.box([153.0, floor + 1.6, -132.0], [30.0, 3.2, 2.4], "#e8e8e2")
    b.box([136.0, floor + 2.6, z1 - 3.6], [4.0, 5.2, 2.6], "#c8d8e0", material="metal")
    supply_ammo(b, 166.0, floor, -150.0, "z+")
    supply_med(b, 140.0, floor, -150.4, "z+")
    for (tx, tz) in ((140.0, -168.0), (156.0, -168.0), (170.0, -176.0), (146.0, -182.0)):
        b.box([tx, y + 1.5, tz], [4.0, 0.4, 4.0], "#f2f2ee")
        b.box([tx, y + 0.65, tz], [0.8, 1.3, 0.8], "#8a8f94")
        b.cyl([tx, y + 1.7 + 2.6, tz], [0.3, 5.2, 0.3], "#8a8f94")
        b.cone([tx, y + 7.4, tz], [6.0, 1.2, 6.0], [CORAL, TEAL, SUNNY, PURPLE][int(tx) % 4], collide=False)


def _dive_pool(b: Area, s: Surfaces) -> None:
    """The dive pool, drained for the winter: ten deep, the tiles stained,
    the drain grate, a stair down one side -- and over it the boards, five
    and ten up, on their tower."""
    x0, x1, z0, z1 = DIVE
    slab(b, DIVE, DIVE_BED, 6.0, TILE_DEEP, studs=True)
    plate(b, carve(rect(x0 - 4.0, x1 + 4.0, z0 - 4.0, z1 + 4.0), [DIVE]), -6.0, 10.0, TILE_DEEP)
    flight(b, "z", -40.0, z0, x0, x0 + 6.0, DIVE_BED, 0.0, TILE, fill=DIVE_BED)
    b.box([180.0, DIVE_BED + 0.05, -30.0], [6.0, 0.1, 6.0], "#2a2a2e", collide=False)
    for (x, z) in ((x1 - 0.06, -40.0), (x1 - 0.06, -20.0)):
        b.box([x, -4.0, z], [0.1, 1.2, 2.4], "#bff8ff", material="neon", collide=False)
    b.box([x0 + 0.06, -4.0, -10.0], [0.1, 1.2, 2.4], "#bff8ff", material="neon", collide=False)
    for (x, z, c) in ((190.0, -46.0, "#ff6aa8"), (166.0, -12.0, SUNNY)):
        b.sphere([x, DIVE_BED + 1.2, z], [4.0, 2.4, 3.0], c)
    # the tower: the five-metre platform, the ten up over it, the boards out
    p1, p2 = rect(170.0, 190.0, 2.0, 12.0), rect(178.0, 190.0, 6.0, 12.0)
    s.reserve(rect(160.0, 190.0, 2.0, 12.0))
    slab(b, p1, 5.0, 0.6, "#f2f2ee", studs=True)
    _deck_legs(b, p1, 5.0, 0.0, "#c8c8c2")
    slab(b, p2, 10.0, 0.6, "#f2f2ee", studs=True)
    _deck_legs(b, p2, 10.0, 5.0, "#c8c8c2")
    flight(b, "x", 160.0, p1[0], 6.0, 12.0, 0.0, 5.0, "#e8e8e2", fill=0.0)
    flight(b, "x", p1[0], p2[0], 6.0, 12.0, 5.0, 10.0, "#e8e8e2", fill=5.0)
    b.box([179.5, 4.8, -4.0], [3.0, 0.4, 12.0], "#3a8ac8")
    b.box([185.5, 9.8, -4.0], [3.0, 0.4, 20.0], "#3a8ac8")
    b.box([p2[1] - 0.4, 11.6, 9.0], [0.8, 3.2, 6.0], "#c8c8c2")
    b.box([(p2[0] + 0.8 + p2[1] - 0.8) / 2.0, 11.6, p2[3] - 0.4], [p2[1] - p2[0] - 1.6, 3.2, 0.8], "#c8c8c2")
    supply_med(b, 174.0, 5.0, 4.6, "z+")
    post_sign(b, 146.0, 4.0, 0.0, 3.0, 8.0, 2.0, sign_decal("POOL CLOSED  NO DIVING", HAZARD, "#1b1b1b", 4.0), "x-", HAZARD)


# ============================================================= wave pool
def _wave_pool(b: Area, s: Surfaces) -> None:
    """The wave pool: a beach at the south end and the floor stepping down
    to the deep end under the machine house; the cabanas along both sides,
    the lifeguard chairs, the lights in the walls."""
    x0, x1, z0, z1 = WAVE
    for (za, zb, top) in WAVE_BANDS:
        slab(b, rect(x0, x1, za, zb), top, 6.0 + top, TILE if top > -3.0 else TILE_DEEP, studs=True)
    b.water((x0 + x1) / 2.0, (z0 + z1) / 2.0, x1 - x0, z1 - z0, WAVE_WATER, POOL_WATER)
    s.lay(rect(x0, x1, 70.0, z0), 0.3, SANDY, studs=True)
    for x in (x0 + 0.06, x1 - 0.06):
        for z in (120.0, 160.0, 195.0):
            b.box([x, -2.4, z], [0.1, 1.0, 2.4], "#bff8ff", material="neon", collide=False)
    for (x0c, door_side) in ((-118.0, "x+"), (84.0, "x-")):
        for z in (96.0, 126.0, 156.0, 186.0):
            cab = rect(x0c, x0c + 14.0, z, z + 14.0)
            s.reserve(cab)
            tent(b, cab, 7.0, [CORAL, TEAL, SUNNY, PURPLE][int(z) % 4], doors={door_side: [(z + 4.0, z + 10.0, 6.8)]})
    supply_med(b, -111.0, FLOOR, 102.0, "z-")
    _lifeguard_chair(b, -97.0, 150.0, 1.0)
    _lifeguard_chair(b, 77.0, 120.0, -1.0)
    s.reserve(rect(-100.0, -94.0, 142.0, 152.0))
    s.reserve(rect(74.0, 80.0, 112.0, 122.0))
    for (x, z) in ((-100.0, 76.0), (80.0, 76.0), (-100.0, 205.0), (80.0, 205.0)):
        _palm(b, x, z, 1.1, 0.3)
    barrel_spot(b, -60.0, 0.3, 74.0)


def _machine_house(b: Area, s: Surfaces) -> None:
    """The wave machine's house behind the deep end: the pumps, the
    paddle drive, the control desk with the horn button (the lure)."""
    x0, x1, z0, z1 = MACHINE
    s.reserve(rect(x0 - 2.0, x1 + 2.0, z0 - 4.0, z1 + 2.0))
    y = 0.3
    slab(b, rect(x0 - 2.0, x1 + 2.0, z0 - 4.0, z1 + 2.0), y, y, CONCRETE)
    building(b, MACHINE, y, 12.0, "#c8d8d8", roof_colour=TEAL, floor_colour="#7a8a8a",
             doors={"z-": [(-14.0, -6.0, y + 9.0)], "z+": [(10.0, 18.0, y + 9.0)]},
             windows={"z-": [(-42.0, -24.0, y + 4.0, y + 8.0), (6.0, 24.0, y + 4.0, y + 8.0)]},
             glass=True, lights="#f2fbff")
    threshold(b, MACHINE, "z-", (-14.0, -6.0), y0=y)
    threshold(b, MACHINE, "z+", (10.0, 18.0), y0=y)
    wall_sign(b, -10.0, y + 10.6, z0 - 0.35, 30.0, 1.6, sign_decal("WAVES IN 10 SECONDS", SUNNY, "#c42b20", 18.75), "z-", SUNNY)
    floor = y + FLOOR
    for k in range(3):
        b.box([-40.0 + k * 12.0, floor + 2.5, 232.0], [8.0, 5.0, 8.0], "#5a6a72", material="metal")
        b.cyl([-40.0 + k * 12.0, floor + 6.0, 232.0], [2.0, 2.0, 2.0], "#8a9aa2", material="metal")
    b.box([16.0, floor + 1.4, 221.0], [8.0, 2.8, 2.4], "#4a5060", material="metal")
    b.box([16.0, floor + 2.8 + 0.3, 221.4], [1.6, 0.6, 1.2], "#c42b20")
    b.set_lure(16.0, floor, 224.2, "the wave machine", "Sound the wave horn", "ll_wavehorn", (-10.0, WAVE_WATER, 145.0))
    supply_ammo(b, 24.0, floor, 236.0, "x-")


def _kraken(b: Area, s: Surfaces) -> None:
    """The Kraken: the slide tower, three platforms up switchback stairs, a
    kraken's head for a roof with its arms round the legs, two tubes
    corkscrewing down into the splash basin -- where the rubber duck is."""
    x0, x1, z0, z1 = KRAKEN
    s.reserve(rect(x0, x1, 86.0, z1))
    p1, p2, p3 = 8.0, 16.0, 24.0
    slab(b, KRAKEN, p1, 0.6, PURPLE, studs=True)
    _deck_legs(b, KRAKEN, p1, 0.0, "#5a2a7a")
    flight(b, "z", 86.0, z0, x0, x0 + 6.0, 0.0, p1, "#5a2a7a", fill=0.0)
    well2 = rect(x0, x0 + 6.0, z0 + 4.0, z1)
    plate(b, carve(KRAKEN, [well2]), p2, 0.6, PURPLE, studs=True)
    flight(b, "z", z1, z0 + 4.0, x0, x0 + 6.0, p1, p2, "#5a2a7a", fill=p1)
    well3 = rect(x1 - 6.0, x1, z0, z1 - 4.0)
    plate(b, carve(KRAKEN, [well3]), p3, 0.6, PURPLE, studs=True)
    flight(b, "z", z0 + 2.0, z1 - 4.0, x1 - 6.0, x1, p2, p3, "#5a2a7a", fill=p2)
    for (x, z) in ((x0 + 0.4, z0 + 0.4), (x1 - 0.4, z0 + 0.4), (x1 - 0.4, z1 - 0.4), (x0 + 6.4, z1 - 0.4)):
        b.box([x, (p1 + p2 - 0.6) / 2.0, z], [0.8, p2 - 0.6 - p1, 0.8], "#5a2a7a")
    for (x, z) in ((x0 + 0.4, z0 + 0.4), (x1 - 6.4, z0 + 0.4), (x0 + 6.4, z1 - 0.4), (x1 - 0.4, z1 - 0.4)):
        b.box([x, (p2 + p3 - 0.6) / 2.0, z], [0.8, p3 - 0.6 - p2, 0.8], "#5a2a7a")
    rails(b, rect(x0, x1 - 6.0, z0, z1), p3, 3.0, TEAL, 0.6, sides=("x-", "z-", "z+"))
    # the kraken's head over the top deck, on four posts
    for (x, z) in ((x0 + 1.0, z0 + 1.0), (x1 - 7.0, z0 + 1.0), (x0 + 1.0, z1 - 1.0), (x1 - 7.0, z1 - 1.0)):
        b.box([x, p3 + 4.0, z], [0.8, 8.0, 0.8], "#5a2a7a")
    slab(b, rect(x0, x1 - 6.0, z0, z1), p3 + 8.6, 0.6, "#5a2a7a")
    b.sphere([157.0, p3 + 14.0, 120.0], [16.0, 10.0, 18.0], "#8a3ab8", collide=False)
    for side in (-1, 1):
        b.sphere([157.0 + side * 4.0, p3 + 13.0, 128.6], [3.4, 3.4, 1.6], SUNNY, collide=False)
        b.sphere([157.0 + side * 4.0, p3 + 13.0, 129.4], [1.4, 2.2, 0.8], "#1a1a1a", collide=False)
    for k in (0, 1, 2, 3, 5):
        a = k / 6.0 * math.pi * 2.0
        b.cyl([160.0 + math.cos(a) * 12.0, 3.0, 120.0 + math.sin(a) * 12.0], [1.6, 6.0, 1.6], "#8a3ab8")
    post_sign(b, 162.0, 84.0, 0.0, 3.0, 12.0, 2.4, sign_decal("THE KRAKEN", PURPLE, SUNNY, 5.0), "z-", PURPLE)
    supply_ammo(b, 160.0, p2, 120.0, "x-")
    # the splash basin, its steps, the duck
    bx0, bx1, bz0, bz1 = BASIN
    slab(b, BASIN, BASIN_BED, 6.0 + BASIN_BED, TILE, studs=True)
    b.water((bx0 + bx1) / 2.0, (bz0 + bz1) / 2.0, bx1 - bx0, bz1 - bz0, BASIN_WATER, POOL_WATER)
    flight(b, "x", bx0 + 8.0, bx0, 70.0, 80.0, BASIN_BED, 0.0, TILE, fill=BASIN_BED)
    b.sphere([222.0, BASIN_BED + 4.0, 80.0], [10.0, 7.0, 13.0], SUNNY)
    b.sphere([222.0, BASIN_BED + 8.6, 85.0], [6.0, 6.0, 6.0], SUNNY)
    b.box([222.0, BASIN_BED + 8.2, 88.6], [2.4, 1.0, 2.4], "#ff8a1a")
    for side in (-1, 1):
        b.sphere([222.0 + side * 1.6, BASIN_BED + 9.6, 87.6], [0.8, 0.8, 0.6], "#1a1a1a")


# ================================================================= staff
def _staff(b: Area, s: Surfaces) -> None:
    """Behind the scenes: the staff lot, the chlorine store with its drums
    (keep back), the maintenance golf carts."""
    x0, x1, z0, z1 = CHLORINE
    s.reserve(CHLORINE)
    building(b, CHLORINE, 0.0, 9.0, "#b8c0c0", roof_colour="#5a6a6a", floor_colour="#7a8080",
             doors={"z-": [(130.0, 140.0, 7.5)]}, lights="#f2fbff")
    threshold(b, CHLORINE, "z-", (130.0, 140.0))
    wall_sign(b, 155.0, 7.0, z0 - 0.35, 18.0, 1.4, sign_decal("CHLORINE  KEEP BACK", HAZARD, "#1b1b1b", 12.9), "z-", HAZARD)
    for k in range(4):
        b.cyl([126.0 + k * 3.0, FLOOR + 1.6, z1 - 4.0], [2.4, 3.2, 2.4], "#e8e8e2", material="metal")
    supply_ammo(b, 160.0, FLOOR, 266.0, "x-")
    for (x, z) in ((116.0, 252.0), (174.0, 252.0), (116.0, 268.0), (176.0, 262.0)):
        barrel_spot(b, x, 0.0, z)
    van(b, -200.0, 262.0, "x", "#f2f2ee", stripe=TEAL, label="SPLASH KINGDOM STAFF", y=0.3)
    for k in range(2):
        cx = -150.0 + k * 10.0
        b.box([cx, 0.3 + 0.8, 258.0], [4.0, 1.6, 6.0], "#f2f2ee")
        b.box([cx, 4.65, 257.0], [4.2, 0.3, 5.0], "#3a8a3a")
        for dz in (-2.0, 2.0):
            b.box([cx + 1.8, 3.2, 258.0 + dz], [0.3, 2.6, 0.3], "#3a3a3a")


# =============================================================== grounds
def _grounds(b: Area, s: Surfaces, rng: random.Random) -> None:
    """The car park, the promenade's lamps and palms, deck chairs, signs."""
    for k, (x, z) in enumerate(((-200.0, -258.0), (-170.0, -266.0), (-110.0, -258.0), (90.0, -266.0),
                                (150.0, -258.0), (210.0, -266.0))):
        car(b, x, z, "z", ["#2a3a6a", "#8a2a24", "#e8e8e8", "#3a5a3a", SUNNY, "#2a2a2e"][k], y=0.3)
    bus(b, -40.0, -262.0, "x", "#e0a62a", length=30.0, label="CAMP SUNSHINE")
    for x in (-240.0, -160.0, -60.0, 60.0, 160.0, 240.0):
        lamp_post(b, x, 28.0, h=11.0, light="#bff8ff", y=0.3)
    for x in (-200.0, -120.0, 100.0, 200.0, 260.0):
        _palm(b, x, 44.0, 1.0)
    for k in range(5):
        x = -60.0 + k * 22.0
        b.box([x, 0.3 + 0.7, 64.0], [3.0, 0.4, 6.0], "#f2f2ee")
        b.box([x, 0.3 + 1.6, 61.6], [3.0, 1.6, 0.4], "#f2f2ee")
        b.box([x, 0.3 + 0.25, 64.0], [2.4, 0.5, 5.4], "#c8c8c2")
    post_sign(b, -100.0, 22.0, 0.0, 3.0, 10.0, 2.4, sign_decal("WAVE POOL  THE KRAKEN  LAZY RIVER", "#f2f2ee", PURPLE, 4.2),
              "z-", "#f2f2ee")
    barrel_spot(b, -40.0, 0.3, 33.0)
    barrel_spot(b, 120.0, 0.3, 33.0)
    barrel_spot(b, 220.0, 0.3, -250.0)


def _paths(b: Area, s: Surfaces) -> None:
    for r, colour in ((CAR_PARK, ASPHALT), (rect(-280.0, 280.0, -236.0, -170.0), DECK), (PROM, DECK),
                      (rect(-96.0, 76.0, 44.0, 214.0), DECK), (rect(-60.0, 40.0, 210.0, 246.0), DECK),
                      (rect(120.0, 250.0, 50.0, 140.0), DECK), (rect(140.0, 220.0, -70.0, 18.0), DECK),
                      (rect(-6.0, 6.0, -170.0, 26.0), DECK), (STAFF_LOT, ASPHALT),
                      (rect(110.0, 180.0, 240.0, 248.0), DECK)):
        s.lay(r, 0.3, colour, studs=colour == DECK)


# ================================================================ rigs
def _rigs(b: Area) -> None:
    b.rig("wave_pool", (WAVE[0] + WAVE[1]) / 2.0, WAVE_WATER, (WAVE[2] + WAVE[3]) / 2.0, 0.0, area=list(WAVE))
    b.rig("tipping_bucket", 65.0, 23.8, -116.0, 0.0)
    loop = [[-255.0, LAZY_WATER, -155.0], [-99.0, LAZY_WATER, -155.0], [-99.0, LAZY_WATER, 1.0],
            [-255.0, LAZY_WATER, 1.0]]
    b.rig("lazy_tubes", -177.0, LAZY_WATER, -77.0, 0.0, loop_path=loop, n=7)
    b.rig("volcano_falls", (VOLCANO[0] + VOLCANO[1]) / 2.0, 16.0, VOLCANO[3], 0.0, steps=8)
    b.rig("sprayers", 66.0, 0.3, -113.0, 0.0,
          heads=[[28.0, 3.5, -150.0], [28.0, 3.5, -76.0], [104.0, 3.5, -150.0], [104.0, 3.5, -76.0],
                 [98.0, 3.5, -94.0], [30.0, 3.5, -112.0]])
    b.rig("king_spout", KING[0], 9.0, KING[1] + 2.6, 0.0)
    b.rig("kraken_slides", 170.0, 24.0, 118.0, 0.0, basin_p=[200.0, BASIN_WATER, 100.0])
    b.rig("pool_float", -10.0, WAVE_WATER, 150.0, 0.0, area=[-80.0, 60.0, 100.0, 200.0])
    for (x, z) in ((-60.0, 28.0), (160.0, 28.0)):
        b.rig("moth_swarm", x, 10.6, z, 0.0)


# ============================================================== spawns
def _zombie_spawns(b: Area) -> None:
    for (x, z) in ((-240.0, -262.0), (-120.0, -270.0), (40.0, -270.0), (120.0, -270.0), (250.0, -262.0),
                   (-200.0, 266.0), (-140.0, 268.0), (40.0, 264.0), (268.0, 200.0), (268.0, 100.0),
                   (268.0, 0.0), (268.0, -100.0), (268.0, -200.0), (-270.0, 200.0), (-270.0, 120.0),
                   (-270.0, 60.0), (-272.0, -200.0), (-226.0, -26.0), (110.0, -150.0), (196.0, -110.0),
                   (-150.0, 33.0), (100.0, 33.0)):
        b.zombie_spawn(x, z, "")
    b.zombie_spawn(180.0, -40.0, "", y=DIVE_BED)
    for (x, z) in ((-255.0, -100.0), (-140.0, -155.0), (-99.0, -40.0)):
        b.zombie_spawn(x, z, "water", y=LAZY_BED)
    b.zombie_spawn(-10.0, 190.0, "water", y=-4.0)
    b.zombie_spawn(200.0, 115.0, "water", y=BASIN_BED)
