"""Harrow Point Aquarium -- on the headland, the night the storm came in.

Layout (north is +z)::

   z +280 ========================= the coast road =============================
          staff yard            car park       the SHARK'S JAWS (the gate)
   z +150 .......................  the plaza  .................................
          JELLYFISH   [ REEF ]   THE GREAT HALL (whale overhead, the kelp tank,
          GALLERY     [ TANK ]   a balcony round it)  ==== SHARK TUNNEL ==== DEEP
                                                                              SEA
   z    0              the MARINE RESCUE CENTRE (safe room)    DOLPHIN STADIUM
   z  -90 ========== THE CLIFF (a stair cut down through it) ===================
          rock pools, the beach, the sea cave in the cliff, the research pier
   z -200 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~ the sea ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Everybody deploys in the Marine Rescue Centre, between the Great Hall and
the cliff.

What makes it this place:

* **Two levels and a cliff.**  The aquarium is on the headland, twelve
  units up; the beach, the rock pools and the pier are at the foot of the
  cliff, and the only ways between them are the stair cut down through the
  rock and the boulders at the west point.  The infected come up out of the
  sea and out of the cave in the cliff face.
* **Indoors.**  The Great Hall is forty units high, with a balcony round it
  and the reef behind a window the size of a wall; the shark tunnel is a
  glass corridor through the tank with the sharks going over; the jellyfish
  gallery is dark but for the jellies; the deep sea room has an octopus who
  watches you.
* **The show.**  The lure is the dolphin stadium's announcer: start the
  show and the horde goes for the pool on the cliff edge -- down off the
  poolside into the water, under the seats full of people with guns.
* **The storm.**  Rain, lightning over the sea, and the gulls blown about.
"""
from __future__ import annotations

import math
import random
from typing import List, Tuple

from .kit import (
    ASPHALT, CONCRETE, CONCRETE_DARK, FLOOR, GLASS, LAMP, STEEL, STEEL_DARK, WARM, WOOD,
    WOOD_DARK, WOOD_LIGHT, Area, Surfaces, barrel_spot, bench, boat, boundary, building, bus,
    car, carve, crate, deploy_pad, flight, holed_wall, lamp_post, plate, post_sign, rect,
    room_walls, sign_decal, slab, strip_light, supply_ammo, supply_med, threshold, van,
    wall_sign)
from ..relay.kit import board_letters, boulder, mound, pine, tier_stack

Rect = Tuple[float, float, float, float]

HALF = 280.0
SKY = {"top": "#04070e", "horizon": "#1a2a3a", "sun": [-0.3, 0.5, -0.6],
       "clouds": 0.62, "tint": "#8aa8c8"}
AMBIENT = "#52627a"

TOP = 12.0                                    # the headland
CLIFF_Z = -90.0
PLATEAU = (-280.0, 280.0, CLIFF_Z, 280.0)        # inside the boundary walls
NOTCH = (-70.0, -60.0, CLIFF_Z, -50.0)        # the stair cut through the cliff
CAVE = (0.0, 40.0, CLIFF_Z, -58.0)            # the sea cave under the stadium's west end
CAVE_ROOF = 9.0
SEA = (-280.0, 280.0, -280.0, -200.0)
SEA_BED = -4.0
WATER = -1.0

ROCK = "#6a6a64"
ROCK_DARK = "#555550"
SAND = "#c8b48a"
GRASS = "#4a6a44"
PAVING = "#9aa0a6"
BLUE_WALL = "#1a3a5a"
TANK_GLASS = "#3a8ac8"
WHITE = "#e8ecee"
TEAL = "#2a8a9a"

HALL = (-60.0, 60.0, 40.0, 140.0)
HALL_H = 40.0
BALCONY = 28.0
KELP = (-10.0, 10.0, 80.0, 100.0)
REEF = (-98.0, -60.0, 52.0, 128.0)
TANK = (58.0, 196.0, 64.0, 124.0)             # the shark tank, the tunnel through it
TUNNEL = (60.0, 196.0, 90.0, 98.0)
DEEP = (196.0, 240.0, 70.0, 118.0)
JELLY = (-180.0, -100.0, -20.0, 40.0)
RESCUE = (-44.0, 44.0, -36.0, 20.0)
RESCUE_H = 13.0
RESCUE_HOLE = (26.0, 42.0, -34.0, -26.0)
POOL = (90.0, 180.0, -86.0, -52.0)
POOL_BED = 8.0
POOL_WATER = 11.0
BOOTH = (124.0, 146.0, -12.0, 0.0)
PIER = (40.0, 52.0, -262.0, -200.0)
PIER_TOP = 2.0


def build(b: Area) -> None:
    rng = random.Random(0xA0A)
    del PAVE_KEEP[:]
    b.extra.update({"weather": "storm", "accent": "#4ac8e8"})
    s = Surfaces(b)
    _land(b, s)
    boundary(b, 30.0, "#2a3238", "#20262c", rng, horizon="fog")
    _hall(b, s)
    _reef(b)
    _sharks(b, s)
    _deep(b, s)
    _jellies(b, s)
    _rescue(b, s)
    _stadium(b, s)
    _plaza(b, s, rng)
    _cliff(b, s, rng)
    _shore(b, s, rng)
    _dressing(b, s, rng)
    _covers(b, s)
    _rigs(b)
    _zombie_spawns(b)
    for x, z, name in ((0, -8, "the rescue centre"), (0, 90, "the great hall"),
                       (-79, 90, "the reef"), (128, 94, "the shark tunnel"),
                       (218, 94, "the deep sea room"), (-140, 10, "the jellyfish gallery"),
                       (135, -60, "the dolphin stadium"), (-65, -70, "the cliff stair"),
                       (20, -74, "the sea cave"), (-120, -150, "the rock pools"),
                       (46, -232, "the pier"), (0, 196, "the shark's jaws"),
                       (100, 230, "the car park"), (-200, 200, "the staff yard"),
                       (-230, -60, "the west point"), (120, -150, "the beach")):
        b.landmark(float(x), float(z), name)
    b.camera(0.0, 60.0, -230.0, 0.0, 10.0, 0.0)
    b.camera(0.0, 34.0, 50.0, 0.0, 24.0, 120.0)
    b.camera(100.0, 18.0, 94.0, 180.0, 16.0, 94.0)
    b.camera(135.0, 36.0, 36.0, 135.0, 8.0, -70.0)


# ================================================================== land
def _land(b: Area, s: Surfaces) -> None:
    """The ground at the foot of the cliff, the sea, and the headland: a
    block twelve units high on it, with the stair notch, the cave and the
    dolphins' pool cut out."""
    h = b.half + b.margin
    pieces = carve(rect(-h, h, -h, h), [SEA])
    plate(b, pieces, 0.0, 0.6, SAND, studs=True)
    plate(b, pieces, -0.6, 5.4, "#8a7a5a")
    # the sea: shelving sand, then the bed; the water over all of it
    sx0, sx1, sz0, sz1 = SEA
    slab(b, rect(sx0, sx1, -212.0, sz1), -1.4, 2.0, "#a8987a", studs=True)
    slab(b, rect(sx0, sx1, -224.0, -212.0), -2.8, 2.0, "#8a8068", studs=True)
    slab(b, rect(sx0, sx1, sz0, -224.0), SEA_BED, 2.0, "#6a6a58", studs=True)
    b.water(0.0, (sz0 + sz1) / 2.0, sx1 - sx0, sz1 - sz0, WATER, "#1f4a5a")
    # the headland, cut for the stair, the cave and the pool
    plate(b, carve(PLATEAU, [NOTCH, CAVE, POOL]), TOP, TOP, "#4a5a3a", studs=True,
          material="grass")
    slab(b, CAVE, TOP, TOP - CAVE_ROOF, ROCK_DARK)


WALKS = [rect(-12.0, 12.0, 140.0, 196.0), rect(-110.0, 110.0, 150.0, 166.0),
         rect(-12.0, 12.0, 20.0, 40.0), rect(-90.0, 60.0, -50.0, -36.0),
         rect(-90.0, -76.0, -36.0, 40.0), rect(-110.0, -99.0, 40.0, 150.0),
         rect(-12.0, 12.0, -50.0, -36.0)]


def top_y(x: float, z: float) -> float:
    """What is underfoot on the headland: a walk, or its turf."""
    on = any(w[0] <= x <= w[1] and w[2] <= z <= w[3] for w in WALKS)
    return TOP + (0.3 if on else 0.0)


def _covers(b: Area, s: Surfaces) -> None:
    """Paving on the headland: slabs on its top, laid round what stands on
    it (the Surfaces are for the beach)."""
    laid: List[Rect] = []
    for w in WALKS:
        for piece in carve(w, PAVE_KEEP + laid):
            slab(b, piece, TOP + 0.3, 0.3, PAVING, studs=True)
        laid.append(w)


PAVE_KEEP: List[Rect] = []          # footprints on the headland the paving keeps off


def keep(r: Rect) -> Rect:
    PAVE_KEEP.append(r)
    return r


# ============================================================ great hall
def _hall(b: Area, s: Surfaces) -> None:
    x0, x1, z0, z1 = HALL
    y = TOP
    keep(rect(x0, x1, z0, z1))
    building(b, HALL, y, HALL_H, "#c8d0d8", roof_colour="#3a4a5a", floor_colour="#8aa0b0",
             doors={"z+": [(-12.0, 12.0, y + 14.0)], "z-": [(-8.0, 8.0, y + 11.0)],
                    "x+": [(TUNNEL[2], TUNNEL[3], y + 7.6)]},
             windows={"z+": [(-50.0, -20.0, y + 18.0, y + 34.0), (20.0, 50.0, y + 18.0, y + 34.0)],
                      "x-": [(REEF[2] + 2.0, REEF[3] - 2.0, y + 2.0, y + 34.0)]},
             glass=True, lights="#9fe8ff")
    for side, span in (("z+", (-12.0, 12.0)), ("z-", (-8.0, 8.0)), ("x+", (TUNNEL[2], TUNNEL[3]))):
        threshold(b, HALL, side, span, y0=y)
    floor = y + FLOOR
    # the balcony round all four walls, rails along its inner edge
    ring = [rect(x0 + 2.0, x1 - 2.0, z0 + 2.0, z0 + 12.0), rect(x0 + 2.0, x1 - 2.0, z1 - 12.0, z1 - 2.0),
            rect(x0 + 2.0, x0 + 12.0, z0 + 12.0, z1 - 12.0), rect(x1 - 12.0, x1 - 2.0, z0 + 12.0, z1 - 12.0)]
    for r in ring:
        slab(b, r, BALCONY, 1.0, "#a8b8c4", studs=True)
    inner = rect(x0 + 12.0, x1 - 12.0, z0 + 12.0, z1 - 12.0)
    ix0, ix1, iz0, iz1 = inner
    rail_c = "#3a4a5a"
    for (a, c, za, zb) in ((ix0, -38.0, iz0, iz0 + 0.6), (-30.0, 30.0, iz0, iz0 + 0.6),
                           (38.0, ix1, iz0, iz0 + 0.6), (ix0, ix1, iz1 - 0.6, iz1)):
        b.box([(a + c) / 2.0, BALCONY + 1.4, (za + zb) / 2.0], [c - a, 2.8, zb - za], rail_c,
              material="metal")
    for (xa, xb) in ((ix0, ix0 + 0.6), (ix1 - 0.6, ix1)):
        b.box([(xa + xb) / 2.0, BALCONY + 1.4, (iz0 + iz1) / 2.0], [0.6, 2.8, iz1 - iz0 - 1.2],
              rail_c, material="metal")
    # the stairs up, either side of the south door
    flight(b, "z", 72.0, iz0, 30.0, 38.0, floor, BALCONY, CONCRETE_DARK, fill=floor)
    flight(b, "z", 72.0, iz0, -38.0, -30.0, floor, BALCONY, CONCRETE_DARK, fill=floor)
    # the kelp tank in the middle: glass on posts, sand and rock inside
    kx0, kx1, kz0, kz1 = KELP
    kh = 30.0
    for (px, pz) in ((kx0, kz0), (kx1, kz0), (kx0, kz1), (kx1, kz1)):
        b.box([px, y + kh / 2.0, pz], [1.6, kh, 1.6], "#3a4a5a", material="metal")
    for (cx, cz, w, d) in (((kx0 + kx1) / 2.0, kz0, kx1 - kx0 - 1.6, 0.6),
                           ((kx0 + kx1) / 2.0, kz1, kx1 - kx0 - 1.6, 0.6),
                           (kx0, (kz0 + kz1) / 2.0, 0.6, kz1 - kz0 - 1.6),
                           (kx1, (kz0 + kz1) / 2.0, 0.6, kz1 - kz0 - 1.6)):
        b.box([cx, y + kh / 2.0, cz], [w, kh, d], TANK_GLASS, material="glass", alpha=0.35)
    slab(b, rect(kx0 + 0.3, kx1 - 0.3, kz0 + 0.3, kz1 - 0.3), y + 2.0, 2.0, "#c8b48a", studs=True)
    slab(b, rect(kx0, kx1, kz0, kz1), y + kh + 1.0, 1.0, "#3a4a5a")
    for k in range(7):
        kx = kx0 + 2.5 + (k * 2.6) % (kx1 - kx0 - 5.0)
        kz = kz0 + 2.5 + (k * 4.3) % (kz1 - kz0 - 5.0)
        b.box([kx, y + 2.0 + 11.0, kz], [0.8, 22.0, 0.3], "#3a8a3a")
    # benches, the information desk, the gift kiosk
    for (bx, bz) in ((-30.0, 110.0), (30.0, 110.0), (-20.0, 64.0), (20.0, 64.0)):
        bench(b, bx, bz, "x", "#5a6a7a", y=floor)
    b.box([0.0, floor + 1.7, 126.0], [20.0, 3.4, 4.0], TEAL, studs=True)
    supply_ammo(b, 44.0, BALCONY, 132.0, "z-")
    supply_med(b, -44.0, floor, 124.0, "x+")
    wall_sign(b, 0.0, y + 36.0, z1 + 0.5, 46.0, 3.2,
              sign_decal("HARROW POINT AQUARIUM", "#1a3a5a", "#9fe8ff", 14.4), "z+", "#1a3a5a")
    barrel_spot(b, 66.0, TOP, 146.0)
    # the roof rolls like a wave, and fins stand along the walls
    roof = y + HALL_H + 1.2
    for k, (za, zb, rise) in enumerate(((40.0, 60.0, 1.6), (60.0, 80.0, 3.6), (80.0, 100.0, 5.2),
                                        (100.0, 120.0, 3.6), (120.0, 140.0, 1.6))):
        slab(b, rect(x0 + 1.0, x1 - 1.0, za, zb), roof + rise, rise, "#3a6a8a" if k % 2 else "#4a7a9a",
             studs=True)
    for x in (-50.0, -30.0, -10.0, 10.0, 30.0, 50.0):
        b.box([x, y + HALL_H / 2.0, z1 + 0.6], [1.2, HALL_H, 1.2], "#e8ecee")


def _reef(b: Area) -> None:
    """The reef tank behind the Great Hall's west wall: the whole wall is
    its window."""
    rx0, rx1, rz0, rz1 = REEF
    y = TOP
    keep(REEF)
    b.box([rx0 + 1.0, y + 18.0, (rz0 + rz1) / 2.0], [2.0, 36.0, rz1 - rz0], BLUE_WALL)
    for (za, zb) in ((rz0, rz0 + 2.0), (rz1 - 2.0, rz1)):
        b.box([(rx0 + 2.0 + rx1) / 2.0, y + 18.0, (za + zb) / 2.0], [rx1 - rx0 - 2.0, 36.0, zb - za],
              BLUE_WALL)
    slab(b, rect(rx0 + 2.0, rx1, rz0 + 2.0, rz1 - 2.0), y + 1.6, 1.6, "#d8c89a", studs=True)
    slab(b, REEF, y + 37.2, 1.2, "#3a4a5a")
    corals = ["#e8503a", "#f2a83a", "#e890b0", "#9a6ae8", "#3ab8a8", "#f2e03a"]
    for k in range(26):
        cx = rx0 + 4.0 + (k * 3.7) % (rx1 - rx0 - 8.0)
        cz = rz0 + 4.0 + (k * 9.1) % (rz1 - rz0 - 8.0)
        hh = 1.4 + (k * 1.7) % 5.0
        b.box([cx, y + 1.6 + hh / 2.0, cz], [2.0 + k % 3, hh, 2.0 + (k + 1) % 3], corals[k % 6],
              studs=True)
    boulder(b, rx0 + 10.0, rz0 + 20.0, y + 1.6, 2.4, "#6a6a64")
    boulder(b, rx0 + 14.0, rz1 - 18.0, y + 1.6, 2.0, "#6a6a64")


# ============================================================ shark tank
def _sharks(b: Area, s: Surfaces) -> None:
    tx0, tx1, tz0, tz1 = TANK
    y = TOP
    keep(rect(tx0, DEEP[1], tz0, tz1))
    # the tank's outer walls (the hall's east wall is its west side)
    th = 28.0
    for (a, c, d, e) in ((tx0 + 2.0, tx1, tz0, tz0 + 2.0), (tx0 + 2.0, tx1, tz1 - 2.0, tz1)):
        b.box([(a + c) / 2.0, y + th / 2.0, (d + e) / 2.0], [c - a, th, e - d], BLUE_WALL)
    holed_wall(b, "z", tx1 - 1.0, 2.0, tz0 + 2.0, tz1 - 2.0, y, y + th, BLUE_WALL,
               holes=[(TUNNEL[2], TUNNEL[3], y - 1.0, y + 7.6)])
    slab(b, rect(tx0 + 2.0, tx1, tz0, tz1), y + th + 1.2, 1.2, "#3a4a5a")
    # a shark's fin as big as a house on the tank's roof
    fy = y + th + 1.2
    for k in range(7):
        b.box([128.0 - k * 1.6, fy + 1.2 + k * 2.4, 94.0], [22.0 - k * 3.0, 2.4, 2.4], "#6a7a8a")
    plate(b, carve(rect(tx0 + 2.0, tx1 - 2.0, tz0 + 2.0, tz1 - 2.0), [TUNNEL]), y + 1.2, 1.2,
          "#c8b48a", studs=True)
    # the tunnel: a floor, glass walls and a glass roof through the middle
    ux0, ux1, uz0, uz1 = TUNNEL
    slab(b, rect(tx0 + 2.0, tx1 - 2.0, uz0, uz1), y + FLOOR + 1.2, FLOOR + 1.2, "#5a6a7a",
         studs=True)
    tunnel_top = y + 9.0
    for z in (uz0 - 0.2, uz1 + 0.2):
        b.box([(tx0 + 2.0 + tx1 - 2.0) / 2.0, (y + 1.6 + tunnel_top) / 2.0, z],
              [tx1 - tx0 - 4.0, tunnel_top - y - 1.6, 0.4], TANK_GLASS, material="glass", alpha=0.3)
    b.box([(tx0 + tx1) / 2.0, tunnel_top + 0.2, (uz0 + uz1) / 2.0],
          [tx1 - tx0 - 4.0, 0.4, uz1 - uz0 + 0.8], TANK_GLASS, material="glass", alpha=0.3)
    for k in range(6):
        x = tx0 + 14.0 + k * 22.0
        for z in (uz0 - 0.6, uz1 + 0.6):
            b.box([x, (y + 1.6 + tunnel_top) / 2.0 + 0.2, z], [1.2, tunnel_top - y - 1.2, 0.4],
                  "#3a4a5a", material="metal")
        b.box([x, tunnel_top + 0.6, (uz0 + uz1) / 2.0], [1.2, 0.4, uz1 - uz0 + 1.6], "#3a4a5a",
              material="metal")
    # rocks and wreckage on the tank floor
    for (rx, rz, sc) in ((80.0, 74.0, 2.0), (120.0, 112.0, 2.6), (160.0, 76.0, 1.8),
                         (176.0, 114.0, 2.2)):
        boulder(b, rx, rz, y + 1.2, sc, "#5a5a5a")
    b.box([140.0, y + 3.2, 76.0], [14.0, 4.0, 6.0], "#5a4a3a")
    b.box([136.0, y + 6.6, 76.0], [4.0, 2.8, 4.0], "#4a3a2e")
    wall_sign(b, HALL[1] + 0.5 - 2.5, y + 10.6, (TUNNEL[2] + TUNNEL[3]) / 2.0, 14.0, 1.8,
              sign_decal("SHARK TUNNEL  FEEDING 3PM", "#1a3a5a", "#9fe8ff", 7.8), "x-",
              "#1a3a5a")


def _deep(b: Area, s: Surfaces) -> None:
    """The deep sea room at the end of the tunnel: dark, an octopus in the
    big tank on the far wall, an anglerfish in the small one."""
    dx0, dx1, dz0, dz1 = DEEP
    y = TOP
    building(b, DEEP, y, 14.0, "#1a2a3a", roof_colour="#2a3a4a", floor_colour="#2a3440",
             doors={"x-": [(TUNNEL[2], TUNNEL[3], y + 7.6)], "z+": [(212.0, 224.0, y + 10.0)]},
             lights="#3a6aff")
    threshold(b, DEEP, "x-", (TUNNEL[2], TUNNEL[3]), y0=y)
    threshold(b, DEEP, "z+", (212.0, 224.0), y0=y)
    floor = y + FLOOR
    b.box([dx1 - 4.0, floor + 5.0, 94.0], [4.0, 10.0, 26.0], "#0a1a2a")
    b.box([dx1 - 6.1, floor + 5.0, 94.0], [0.2, 8.0, 24.0], TANK_GLASS, material="glass", alpha=0.4)
    b.box([216.0, floor + 2.0, dz0 + 4.0], [10.0, 4.0, 4.0], "#0a1a2a")
    b.box([216.0, floor + 2.0, dz0 + 6.1], [9.0, 3.4, 0.2], TANK_GLASS, material="glass", alpha=0.4)
    supply_ammo(b, dx0 + 6.0, floor, dz1 - 6.0, "x+")
    supply_med(b, dx0 + 6.0, floor, dz0 + 6.0, "x+")


# ============================================================ jellyfish
def _jellies(b: Area, s: Surfaces) -> None:
    jx0, jx1, jz0, jz1 = JELLY
    y = TOP
    keep(JELLY)
    building(b, JELLY, y, 16.0, "#1a2030", roof_colour="#2a3040", floor_colour="#141a24",
             doors={"x+": [(4.0, 16.0, y + 11.0)], "z+": [(-146.0, -134.0, y + 11.0)],
                    "z-": [(-146.0, -134.0, y + 11.0)]},
             lights="#5a6aff")
    for side, span in (("x+", (4.0, 16.0)), ("z+", (-146.0, -134.0)), ("z-", (-146.0, -134.0))):
        threshold(b, JELLY, side, span, y0=y)
    floor = y + FLOOR
    # the jellies' tanks: glass columns on dark plinths, in two rows
    for k, (cx, cz) in enumerate(((-168.0, 0.0), (-168.0, 24.0), (-112.0, 0.0), (-112.0, 24.0),
                                  (-150.0, -8.0), (-130.0, 32.0), (-150.0, 32.0), (-130.0, -8.0))):
        b.box([cx, floor + 0.6, cz], [7.0, 1.2, 7.0], "#0a0e18")
        b.box([cx, floor + 1.2 + 6.0, cz], [6.0, 12.0, 6.0], "#3a6aff", material="glass", alpha=0.25)
        b.box([cx, floor + 13.4 + 0.0, cz], [7.0, 1.0, 7.0], "#0a0e18")
    supply_ammo(b, -174.0, floor, -14.0, "z+")
    wall_sign(b, jx1 + 0.5, y + 13.0, 10.0, 22.0, 2.4,
              sign_decal("JELLYFISH GALLERY", "#1a2030", "#9ab8ff", 9.2), "x+", "#1a2030")
    barrel_spot(b, jx0 - 6.0, TOP, -14.0)


# ======================================================= rescue centre
def _rescue(b: Area, s: Surfaces) -> None:
    x0, x1, z0, z1 = RESCUE
    y = TOP
    keep(RESCUE)
    head = y + 10.0
    building(b, RESCUE, y, RESCUE_H, WHITE, roof_colour="#3a4a5a", floor_colour="#c8d0d4",
             doors={"z+": [(-8.0, 8.0, head)], "z-": [(-8.0, 8.0, head)],
                    "x-": [(-14.0, -2.0, head)], "x+": [(-14.0, -2.0, head)]},
             windows={"z-": [(-40.0, -14.0, y + 3.6, y + 8.4), (14.0, 24.0, y + 3.6, y + 8.4)],
                      "z+": [(-40.0, -14.0, y + 3.6, y + 8.4), (14.0, 40.0, y + 3.6, y + 8.4)]},
             glass=True, roof_holes=[RESCUE_HOLE], parapet=3.0, lights=LAMP)
    for side in ("z+", "z-"):
        threshold(b, RESCUE, side, (-8.0, 8.0), y0=y)
    for side in ("x-", "x+"):
        threshold(b, RESCUE, side, (-14.0, -2.0), y0=y)
    for zz in (z0 - 0.15, z1 + 0.15):
        for a, c in ((x0, -10.0), (10.0, x1)):
            b.box([(a + c) / 2.0, y + 11.6, zz], [c - a, 1.2, 0.3], TEAL)
    wall_sign(b, 0.0, y + 11.2, z1 + 0.5, 34.0, 2.4,
              sign_decal("MARINE RESCUE CENTRE", TEAL, "#f2f2f2", 14.0), "z+", TEAL)
    floor = y + FLOOR
    for z in (8.0, -2.0):
        for x in (-36.0, -27.0, -18.0, -9.0, 9.0, 18.0, 27.0, 36.0):
            deploy_pad(b, x, z, floor, "#4ac8e8", 5.0)
            b.safe_spawn(x, floor + 0.6, z, 0.0)
    # the turtle hospital: low tanks along the south wall, a table, the stair
    for k, tx in enumerate((-36.0, -22.0, -8.0)):
        b.box([tx, floor + 1.4, -28.0], [10.0, 2.8, 8.0], "#c8d0d4")
        b.box([tx, floor + 2.85, -28.0], [9.0, 0.1, 7.0], "#3a8ab8", material="glass", alpha=0.7)
    b.box([10.0, floor + 1.8, -22.0], [8.0, 3.6, 5.0], "#a8adb2", material="metal")
    flight(b, "x", 16.0, 42.0, -34.0, -26.0, floor, y + RESCUE_H + 1.2, CONCRETE_DARK, fill=floor)
    supply_ammo(b, -30.0, floor, 14.0, "z-")
    supply_med(b, 30.0, floor, 14.0, "z-")
    roof = y + RESCUE_H + 1.2
    def rail(xa, xb, za, zb):
        b.box([(xa + xb) / 2.0, roof + 1.6, (za + zb) / 2.0], [xb - xa, 3.2, zb - za], STEEL,
              material="metal")
    rail(RESCUE_HOLE[0], RESCUE_HOLE[1], RESCUE_HOLE[3], RESCUE_HOLE[3] + 0.6)
    rail(RESCUE_HOLE[0] - 0.6, RESCUE_HOLE[0], RESCUE_HOLE[2], RESCUE_HOLE[3] + 0.6)
    supply_ammo(b, -30.0, roof, 8.0, "z-")
    keep(rect(-66.0, -54.0, -8.0, 12.0))
    van(b, -60.0, 2.0, "z", "#f2f2f2", stripe=TEAL, lights="#3ab8e8", label="MARINE RESCUE",
        y=TOP)
    barrel_spot(b, 52.0, TOP, -30.0)


# ============================================================ stadium
def _stadium(b: Area, s: Surfaces) -> None:
    px0, px1, pz0, pz1 = POOL
    keep(rect(69.2, 200.8, CLIFF_Z, 14.0))
    # the pool: a bed, its water; glass along the cliff edge
    slab(b, POOL, POOL_BED, POOL_BED, "#3a7aa8", studs=True)
    b.water((px0 + px1) / 2.0, (pz0 + pz1) / 2.0, px1 - px0, pz1 - pz0, POOL_WATER, "#2f8ab8")
    b.box([(px0 + px1) / 2.0, TOP + 2.0, CLIFF_Z + 0.3], [px1 - px0 + 20.0, 4.0, 0.6], GLASS,
          material="glass", alpha=0.4)
    # the poolside, then the seats in steps up away from it, facing the sea
    tops = [TOP + 1.5, TOP + 3.0, TOP + 4.5, TOP + 6.0]
    starts = [-44.0, -36.0, -28.0, -20.0]
    colours = ["#2a8a9a", "#e8ecee", "#2a8a9a", "#e8ecee"]
    for k in range(4):
        slab(b, rect(70.0, 200.0, starts[k], (starts[k + 1] if k < 3 else -10.0)), tops[k],
             tops[k] - TOP, colours[k], studs=True)
    slab(b, rect(70.0, 200.0, -10.0, 2.0), tops[3], tops[3] - TOP, "#2a8a9a", studs=True)
    for x in (69.6, 200.4):
        b.box([x, TOP + 3.6, -21.0], [0.8, 7.2, 46.0], "#3a4a5a")
    flight(b, "z", 14.0, 2.0, 100.0, 108.0, TOP, tops[3], CONCRETE_DARK, fill=TOP)
    # the announcer's booth on top, the lure's desk in it
    building(b, BOOTH, tops[3], 9.0, WHITE, roof_colour=TEAL, floor_colour="#8a7a6a",
             doors={"z-": [(130.0, 140.0, tops[3] + 7.4)]},
             windows={"z-": [(126.0, 129.0, tops[3] + 3.4, tops[3] + 7.0),
                             (141.0, 144.0, tops[3] + 3.4, tops[3] + 7.0)]}, glass=True,
             lights=WARM)
    threshold(b, BOOTH, "z-", (130.0, 140.0), y0=tops[3])
    b.box([135.0, tops[3] + FLOOR + 1.6, -3.6], [12.0, 3.2, 3.0], "#5a5f66")
    b.set_lure(135.0, tops[3] + FLOOR, -6.0, "the dolphin show", "Start the dolphin show",
               "ll_dolphin", ((px0 + px1) / 2.0, POOL_BED, (pz0 + pz1) / 2.0))
    supply_ammo(b, 112.0, tops[3], -4.0, "z-")
    wall_sign(b, 135.0, tops[3] + 10.4, BOOTH[2] - 0.5, 20.0, 2.2,
              sign_decal("DOLPHIN COVE", TEAL, "#f2f2f2", 9.0), "z-", TEAL)
    barrel_spot(b, 76.0, TOP, -48.0)
    barrel_spot(b, 194.0, TOP, -48.0)


# =============================================================== plaza
def _plaza(b: Area, s: Surfaces, rng: random.Random) -> None:
    y = TOP
    # the shark's jaws: the gate you walk in through, teeth and all
    jx, jz = 0.0, 196.0
    keep(rect(jx - 16.0, jx + 16.0, jz - 4.0, jz + 4.0))
    for side in (-1, 1):
        b.box([jx + side * 13.0, y + 7.0, jz], [6.0, 14.0, 8.0], "#7a8a9a", studs=True)
        b.box([jx + side * 10.5, y + 15.0, jz], [5.0, 6.0, 7.6], "#7a8a9a", studs=True)
    b.box([jx, y + 19.5, jz], [25.0, 5.0, 7.2], "#7a8a9a", studs=True)
    for k in range(9):
        tx = jx - 9.6 + k * 2.4
        b.box([tx, y + 16.0, jz - 2.8], [1.2, 2.6, 1.2], "#f2f2e6", collide=False)
    for k in range(5):
        for side in (-1, 1):
            b.box([jx + side * 10.2, y + 3.0 + k * 2.4, jz - 3.0], [1.2, 1.2, 1.2], "#f2f2e6")
    b.box([jx - 6.0, y + 21.0, jz - 3.66], [2.4, 2.4, 0.12], "#141414", collide=False)
    b.box([jx + 6.0, y + 21.0, jz - 3.66], [2.4, 2.4, 0.12], "#141414", collide=False)
    b.box([jx, y + 26.0, jz], [2.0, 8.0, 6.0], "#7a8a9a", studs=True)
    # the ticket pavilion and the fountain
    pav = keep(rect(-60.0, -30.0, 170.0, 190.0))
    building(b, pav, y, 10.0, WHITE, roof_colour=TEAL, floor_colour="#c8d0d4",
             doors={"x+": [(174.0, 186.0, y + 8.0)]}, windows={"z-": [(-56.0, -34.0, y + 3.4, y + 7.6)]},
             glass=True, lights=WARM)
    threshold(b, pav, "x+", (174.0, 186.0), y0=y)
    supply_med(b, -54.6, y + FLOOR, 180.0, "x+")
    fx, fz = 40.0, 178.0
    keep(rect(fx - 9.0, fx + 9.0, fz - 9.0, fz + 9.0))
    b.box([fx, y + 1.0, fz], [18.0, 2.0, 18.0], "#a8b0b8", studs=True)
    b.box([fx, y + 2.05, fz], [16.0, 0.1, 16.0], "#3a8ab8", material="glass", alpha=0.7)
    b.box([fx, y + 4.0, fz], [2.4, 4.0, 2.4], "#a8b0b8")
    b.box([fx, y + 7.0, fz], [5.0, 2.0, 1.4], "#7a8a9a")
    # the car park on the road, the bus that brought the school
    for k, (cx, cz, along) in enumerate(((80.0, 236.0, "z"), (100.0, 236.0, "z"), (140.0, 236.0, "z"),
                                         (180.0, 236.0, "z"), (100.0, 262.0, "x"), (200.0, 262.0, "x"))):
        car(b, cx, cz, along, ["#c8a83a", "#3a5a6a", "#8a2a24", "#f2f2f2", "#2a2a2a", "#4a7a3a"][k],
            length=11.0, wrecked=k == 2, y=TOP)
        keep(rect(cx - 6.0, cx + 6.0, cz - 6.0, cz + 6.0))
    barrel_spot(b, 150.0, TOP, 250.0)
    # the staff yard: the life-support plant, its filter tanks and pumps
    for (tx, tz) in ((-220.0, 180.0), (-200.0, 180.0), (-220.0, 206.0), (-200.0, 206.0)):
        b.cyl([tx, y + 7.0, tz], [10.0, 14.0, 10.0], "#8a9aa8", material="metal")
        b.cyl([tx, y + 14.4, tz], [10.4, 0.8, 10.4], "#5a6a7a", material="metal")
    b.box([-210.0, y + 0.6, 193.0], [32.0, 1.2, 2.0], "#3a6a8a", material="metal")
    b.box([-210.0, y + 3.0, 232.0], [30.0, 6.0, 12.0], "#5a6a7a", material="metal")
    supply_ammo(b, -240.0, y, 200.0, "x+")
    barrel_spot(b, -180.0, TOP, 200.0)
    for k in range(10):
        pine(b, rng.uniform(-270.0, -150.0), rng.uniform(250.0, 272.0), TOP, rng.uniform(1.4, 2.0))
    # lamps along the walks
    for (lx, lz) in ((-20.0, 160.0), (20.0, 160.0), (-80.0, 30.0), (-20.0, -44.0), (40.0, -44.0),
                     (-100.0, 100.0), (60.0, 30.0)):
        lamp_post(b, lx, lz, h=14.0, light=LAMP, y=top_y(lx, lz))


# =============================================================== cliff
def _cliff(b: Area, s: Surfaces, rng: random.Random) -> None:
    """The cliff face: rock ledges along its foot, the stair cut down
    through it, boulders to scramble at the west point, the cave."""
    nx0, nx1, nz0, nz1 = NOTCH
    flight(b, "z", nz0, nz1, nx0, nx1, 0.0, TOP, ROCK, fill=0.0)
    for x in (nx0 - 0.5, nx1 + 0.5):
        b.box([x, TOP + 1.4, (nz0 + nz1) / 2.0], [1.0, 2.8, nz1 - nz0], STEEL, material="metal")
    post_sign(b, nx1 + 4.0, nz1 + 3.0, top_y(nx1 + 4.0, nz1 + 3.0), 3.0, 12.0, 2.0,
              sign_decal("CLIFF STAIR  TO THE BEACH", "#f2f2f2", "#1a3a5a", 6.0), "z+", "#f2f2f2")
    # the cave's mouth: a rock lintel, a rope across it, the dark inside
    cx0, cx1, cz0, cz1 = CAVE
    for k in range(4):
        boulder(b, cx0 + 6.0 + k * 9.0, cz1 - 4.0, 0.0, 1.2 + (k % 2) * 0.4, ROCK_DARK)
    supply_med(b, cx1 - 6.0, 0.0, cz1 - 9.0, "z-")
    # the scramble at the west point: boulders in steps up the cliff
    tier_stack(b, [[rect(-246.0, -226.0, CLIFF_Z - 18.0 + k * 3.0, CLIFF_Z)] for k in range(6)],
               0.0, [2.0], [ROCK_DARK, ROCK], studs=True)
    s.reserve(rect(-246.0, -226.0, CLIFF_Z - 18.0, CLIFF_Z))
    # rock ledges along the cliff's foot
    for x in range(-270, 270, 26):
        if -80 < x < -50 or -10 < x < 50 or -256 < x < -216:
            continue
        w = rng.uniform(10.0, 18.0)
        hgt = rng.uniform(2.0, 5.0)
        r = rect(float(x), float(x) + w, CLIFF_Z - rng.uniform(5.0, 9.0), CLIFF_Z)
        s.reserve(r)
        slab(b, r, hgt, hgt, ROCK_DARK if x % 52 else ROCK, studs=True)


# =============================================================== shore
def _shore(b: Area, s: Surfaces, rng: random.Random) -> None:
    # rock pools: low walls round shallow water
    for (cx, cz) in ((-150.0, -140.0), (-110.0, -160.0), (-190.0, -175.0), (150.0, -130.0),
                     (190.0, -160.0)):
        r = rect(cx - 8.0, cx + 8.0, cz - 6.0, cz + 6.0)
        s.reserve(r)
        for (a, c, d, e) in ((r[0], r[1], r[2], r[2] + 1.6), (r[0], r[1], r[3] - 1.6, r[3]),
                             (r[0], r[0] + 1.6, r[2] + 1.6, r[3] - 1.6),
                             (r[1] - 1.6, r[1], r[2] + 1.6, r[3] - 1.6)):
            b.box([(a + c) / 2.0, 1.0, (d + e) / 2.0], [c - a, 2.0, e - d], ROCK, studs=True)
        b.box([cx, 0.1, cz], [12.8, 0.2, 8.8], "#3a7a8a", material="glass", alpha=0.6,
              collide=False)
    for k in range(18):
        bx = rng.uniform(-260.0, 260.0)
        bz = rng.uniform(-196.0, -110.0)
        if any(abs(bx - x) < 14.0 and abs(bz - z) < 12.0 for (x, z) in ((46.0, -200.0),
                                                                     (-65.0, -96.0),
                                                                     (20.0, -96.0))):
            continue
        boulder(b, bx, bz, 0.0, rng.uniform(1.0, 2.4), ROCK if k % 2 else ROCK_DARK)
    # the research pier out over the water, its hut at the end, a boat
    px0, px1, pz0, pz1 = PIER
    slab(b, PIER, PIER_TOP, 0.8, WOOD_LIGHT, studs=True)
    for z in range(int(pz0) + 4, int(pz1), 12):
        for x in (px0 + 1.0, px1 - 1.0):
            b.cyl([x, (PIER_TOP - 0.8 + SEA_BED) / 2.0, float(z)], [1.2, PIER_TOP - 0.8 - SEA_BED, 1.2],
                  WOOD_DARK)
    for x in (px0 + 0.3, px1 - 0.3):
        b.box([x, PIER_TOP + 1.2, (pz0 + 14.0 + pz1) / 2.0], [0.6, 2.4, pz1 - pz0 - 14.0], WOOD_DARK)
    hut = rect(36.0, 56.0, -276.0, -262.0)
    slab(b, rect(34.0, 58.0, -278.0, -262.0), PIER_TOP, 0.8, WOOD_LIGHT, studs=True)
    for (x, z) in ((35.0, -277.0), (57.0, -277.0)):
        b.cyl([x, (PIER_TOP - 0.8 + SEA_BED) / 2.0, z], [1.2, PIER_TOP - 0.8 - SEA_BED, 1.2], WOOD_DARK)
    building(b, hut, PIER_TOP, 9.0, "#c8c0b0", roof_colour="#5a3a2a",
             doors={"z+": [(42.0, 50.0, PIER_TOP + 7.4)]}, windows={"x-": [(-272.0, -266.0, PIER_TOP + 3.4,
                                                                            PIER_TOP + 7.0)]},
             glass=True, lights=WARM)
    threshold(b, hut, "z+", (42.0, 50.0), y0=PIER_TOP)
    supply_ammo(b, 50.0, PIER_TOP + FLOOR, -272.0, "z+")
    boat(b, 70.0, -236.0, "z", 28.0, "#e8e8e8", deck=1.4, cabin=True, base=SEA_BED)
    barrel_spot(b, 44.0, PIER_TOP, -205.0)
    # a mermaid on a rock out in the water
    b.sphere([-90.0, SEA_BED + 3.0, -240.0], [9.0, 8.0, 8.0], ROCK)
    b.box([-90.0, SEA_BED + 7.8, -240.0], [1.4, 2.0, 1.0], "#5a9a8a")
    b.box([-90.0, SEA_BED + 9.6, -240.0], [1.2, 1.6, 0.8], "#d8b8a0")
    b.box([-90.0, SEA_BED + 10.9, -240.0], [1.0, 1.0, 1.0], "#d8b8a0")
    b.box([-90.0, SEA_BED + 11.2, -240.4], [1.2, 1.4, 0.4], "#c8783a")


# ============================================================= dressing
def _dressing(b: Area, s: Surfaces, rng: random.Random) -> None:
    """Dunes on the headland, a fence along the cliff with telescopes on
    it, the lookout at the west point; on the beach a lifeguard tower,
    beach huts, driftwood and a rowboat; palms and flags on the plaza; a
    touch pool in the Great Hall."""
    # dunes, marram grass on the tops
    for (cx, cz, rx, rz) in ((-220.0, 80.0, 30.0, 22.0), (-180.0, -54.0, 26.0, 18.0),
                             (232.0, 30.0, 26.0, 30.0), (232.0, 200.0, 30.0, 26.0),
                             (150.0, 170.0, 22.0, 12.0)):
        keep(rect(cx - rx, cx + rx, cz - rz, cz + rz))
        top = mound(b, cx, cz, rx, rz, 3, 1.4, ["#8a9a5a", "#7a8a4a", "#9aaa6a"], y0=TOP)
        for k in range(5):
            b.box([cx + (k - 2) * 2.6, top + 1.2, cz + rng.uniform(-3.0, 3.0)], [0.4, 2.4, 0.4],
                  "#a8b86a")
    # the fence along the cliff's edge, west of the stadium, with gaps at
    # the stair and over the cave
    for (xa, xb) in ((-272.0, -248.0), (-224.0, -71.0), (-59.0, -2.0), (42.0, 68.0)):
        b.box([(xa + xb) / 2.0, TOP + 1.5, CLIFF_Z + 0.4], [xb - xa, 0.4, 0.4], "#8a8f94",
              material="metal")
        n = max(1, int((xb - xa) // 8))
        for k in range(n + 1):
            b.box([xa + (xb - xa) * k / n, TOP + 1.0, CLIFF_Z + 0.4], [0.5, 2.0, 0.5], "#6a6f74",
                  material="metal")
    for x in (-140.0, -20.0, 50.0):
        b.cyl([x, TOP + 1.6, CLIFF_Z + 4.0], [0.6, 3.2, 0.6], "#3a4a5a", material="metal")
        b.box([x, TOP + 3.6, CLIFF_Z + 4.0], [1.0, 1.0, 2.4], "#3a6a8a", material="metal")
    # the lookout tower on the west point, a stair up it
    lx, lz = -250.0, -70.0
    keep(rect(lx - 8.0, lx + 8.0, lz - 8.0, lz + 30.0))
    for dx in (-5.0, 5.0):
        for dz in (-5.0, 5.0):
            b.box([lx + dx, TOP + 9.0, lz + dz], [1.2, 18.0, 1.2], "#e8ecee")
    slab(b, rect(lx - 6.0, lx + 6.0, lz - 6.0, lz + 6.0), TOP + 18.8, 0.8, WOOD_LIGHT, studs=True)
    room_walls(b, rect(lx - 6.0, lx + 6.0, lz - 6.0, lz + 6.0), 0.6, TOP + 18.8, TOP + 21.4,
               "#e8ecee", doors={"z+": [(lx - 2.6, lx + 2.6, TOP + 22.0)]})
    flight(b, "z", lz + 28.0, lz + 6.0, lx - 2.6, lx + 2.6, TOP, TOP + 18.8, WOOD, fill=TOP)
    slab(b, rect(lx - 7.0, lx + 7.0, lz - 7.0, lz + 7.0), TOP + 26.6, 0.6, "#c43a32")
    for dx in (-5.6, 5.6):
        for dz in (-5.6, 5.6):
            b.box([lx + dx, TOP + 23.6, lz + dz], [0.6, 4.8, 0.6], "#e8ecee")
    supply_ammo(b, lx, TOP + 18.8, lz - 3.0, "z+")
    # the beach: a lifeguard tower, the huts, driftwood, a rowboat
    gx, gz = 120.0, -170.0
    s.reserve(rect(gx - 4.0, gx + 4.0, gz - 4.0, gz + 20.0))
    for dx in (-3.0, 3.0):
        for dz in (-3.0, 3.0):
            b.box([gx + dx, 4.0, gz + dz], [0.8, 8.0, 0.8], "#e8ecee")
    slab(b, rect(gx - 4.0, gx + 4.0, gz - 4.0, gz + 4.0), 8.8, 0.8, WOOD_LIGHT)
    flight(b, "z", gz + 18.0, gz + 4.0, gx - 2.0, gx + 2.0, 0.0, 8.8, WOOD, fill=0.0)
    b.box([gx, 13.2, gz], [8.8, 0.6, 8.8], "#c43a32")
    for dx in (-4.0, 4.0):
        b.box([gx + dx, 10.9, gz - 4.0], [0.5, 4.0, 0.5], "#e8ecee")
    huts = ["#e8503a", "#3a8ac8", "#f2c83a", "#3ab88a", "#e890b0"]
    for k, hx in enumerate((-40.0, -26.0, -12.0, 70.0, 84.0)):
        hut = rect(hx - 5.0, hx + 5.0, -128.0, -118.0)
        s.reserve(hut)
        building(b, hut, 0.0, 8.0, huts[k], roof_colour="#f2f2f2",
                 doors={"z-": [(hx - 4.0, hx + 4.0, 6.6)]}, lights="")
    for (dx_, dz_, w) in ((-200.0, -190.0, 9.0), (10.0, -186.0, 7.0), (200.0, -192.0, 8.0)):
        b.box([dx_, 0.6, dz_], [w, 1.2, 1.4], "#a89070")
    rb = (-60.0, -180.0)
    b.box([rb[0], 1.0, rb[1]], [10.0, 2.0, 4.6], "#3a6a8a", material="metal")
    b.box([rb[0], 2.2, rb[1]], [9.0, 0.4, 3.6], "#f2f2f2")
    # palms and flags on the plaza, a touch pool in the hall
    for (px, pz) in ((-40.0, 160.0), (40.0, 158.0), (-80.0, 156.0), (80.0, 156.0)):
        y0 = top_y(px, pz)
        for k in range(4):
            b.box([px + k * 0.4, y0 + 1.5 + k * 3.0, pz], [1.2, 3.0, 1.2], "#8a6a4a")
        for a in range(5):
            ang = a * math.tau / 5.0
            b.box([px + 1.6 + math.cos(ang) * 2.6, y0 + 12.4, pz + math.sin(ang) * 2.6],
                  [4.0, 0.3, 1.4], "#3a8a3a", r=[0, -ang, 0.25], collide=False)
    for (fx, fz) in ((-24.0, 186.0), (24.0, 186.0)):
        y0 = top_y(fx, fz)
        b.cyl([fx, y0 + 9.0, fz], [0.6, 18.0, 0.6], "#e8ecee", material="metal")
        b.box([fx + 2.6, y0 + 16.0, fz], [5.0, 3.0, 0.2], TEAL, collide=False)
    floor = TOP + FLOOR
    b.box([-30.0, floor + 1.4, 90.0], [12.0, 2.8, 8.0], "#3a6a8a", studs=True)
    b.box([-30.0, floor + 2.85, 90.0], [11.0, 0.1, 7.0], "#3a8ab8", material="glass", alpha=0.6,
          collide=False)
    for k in range(4):
        b.box([-34.0 + k * 2.6, floor + 3.0, 88.0 + (k % 2) * 3.0], [1.0, 0.2, 1.0], "#e8783a",
              collide=False)


# ================================================================== rigs
def _rigs(b: Area) -> None:
    b.rig("whale_skeleton", 0.0, TOP + 36.0, 70.0, 0.3)
    b.rig("fish_school", 0.0, TOP + 16.0, 90.0, 0.0, area=[KELP[0] + 1.6, KELP[1] - 1.6, KELP[2] + 1.6,
                                                            KELP[3] - 1.6], y0=TOP + 5.0, y1=TOP + 28.0,
          n=14, seed=1)
    b.rig("fish_school", -79.0, TOP + 14.0, 90.0, 0.0, area=[REEF[0] + 3.0, REEF[1] - 4.0, REEF[2] + 3.0,
                                                              REEF[3] - 3.0], y0=TOP + 4.0, y1=TOP + 32.0,
          n=26, seed=2)
    b.rig("sharks", 127.0, TOP + 12.0, 94.0, 0.0, area=[TANK[0] + 6.0, TANK[1] - 6.0, TANK[2] + 6.0,
                                                         TANK[3] - 6.0], y0=TOP + 10.5, y1=TOP + 25.0, n=4)
    b.rig("octopus", DEEP[1] - 4.0, TOP + FLOOR + 2.0, 94.0, -math.pi / 2.0)
    b.rig("anglerfish", 216.0, TOP + FLOOR + 2.0, DEEP[2] + 4.0, 0.0)
    for k, (cx, cz) in enumerate(((-168.0, 0.0), (-168.0, 24.0), (-112.0, 0.0), (-112.0, 24.0),
                                  (-150.0, -8.0), (-130.0, 32.0), (-150.0, 32.0), (-130.0, -8.0))):
        b.rig("jellyfish", cx, TOP + FLOOR + 1.2 + 6.0, cz, 0.0, n=3, seed=k,
              colour=["#9ab8ff", "#ff9ad8", "#9affe8", "#ffd89a"][k % 4])
    b.rig("dolphins", (POOL[0] + POOL[1]) / 2.0, POOL_WATER, (POOL[2] + POOL[3]) / 2.0, 0.0,
          area=list(POOL), bed=POOL_BED)
    b.rig("turtles", -22.0, TOP + FLOOR + 2.8, -28.0, 0.0, tanks=[[-36.0, -28.0], [-22.0, -28.0],
                                                                [-8.0, -28.0]])
    b.rig("gulls", 0.0, 40.0, -120.0, 0.0, n=8, r=90.0)
    b.rig("surf", 0.0, WATER, -200.0, 0.0, w=560.0)
    b.rig("buoy", 90.0, WATER, -258.0, 0.0)


# ================================================================ spawns
def _zombie_spawns(b: Area) -> None:
    for x in (-240.0, -160.0, -80.0, 10.0, 120.0, 200.0, 260.0):
        b.zombie_spawn(x, -236.0, "water", y=SEA_BED)
    for x in (-200.0, -40.0, 150.0):
        b.zombie_spawn(x, -218.0, "water", y=-2.8)
    for x, z in ((12.0, -70.0), (30.0, -66.0)):
        b.zombie_spawn(x, z, "cave", y=0.0)
    pts = [(-262.0, 262.0), (-120.0, 270.0), (60.0, 272.0), (180.0, 272.0), (262.0, 262.0),
           (-268.0, 120.0), (-268.0, 20.0), (268.0, 180.0), (268.0, 20.0), (268.0, -40.0),
           (-268.0, -40.0)]
    for x, z in pts:
        b.zombie_spawn(x, z, "", y=TOP)
    for x, z in ((-260.0, -120.0), (-120.0, -100.0), (100.0, -110.0), (250.0, -120.0),
                 (220.0, -180.0)):
        b.zombie_spawn(x, z, "", y=0.0)
