"""Harrow County Zoo -- golden hour on the last day it was open.

Layout (north is +z)::

   z +280 ------------------------ the service road ---------------------------
          AVIARY (netted,         GIRAFFE SAVANNAH         BIG CAT ROCKS
          a canopy walk)          (the high ground)        (island, moat, den)
   z +160 .....................  feeding platform  ..........................
          the panda grove   ===== the MONORAIL (a loop on stilts) =====
   z  +60 ------------- the terrace --------- PRIMATE ISLAND ----------------
          REPTILE HOUSE        |  VET HOSPITAL (safe room)  |   ELEPHANT HOUSE
          (a croc pool)        |                            |   and its yard
          PENGUIN COVE         |   the SEA LION ARENA       |   PETTING FARM
          (gallery under it)   |   (sunk, the lure)         |   (barn, goats)
          ice cream            THE PLAZA, flamingos, gift shop
   z -280 ======================== the gates, the car park ====================

Everybody deploys in the vet hospital in the middle of the zoo.

What makes it this place:

* **The monorail.**  A loop of track on stilts eighteen units up, all the
  way round the middle of the zoo, with stairs up at the station, by the
  aviary and by the big cats -- a ring of high ground you can run round.
  The train stalled on the north side: you walk through it.
* **Three levels.**  The zoo climbs the hill: the plaza, the arena and the
  houses on the bottom, a terrace up to the primates, the pandas and the
  aviary, and the savannah above that.  The sea lion arena is sunk into the
  ground and the penguins' gallery is under it.
* **The animals.**  They are all still here, behind their moats and their
  glass, and they watch you: giraffes, elephants, lions, a gorilla who does
  not care for Tanks, penguins swimming past the gallery window, flamingos
  that scatter, a crocodile under the reptile house's footbridge.
* **The show.**  The lure is the sea lion arena's announcer booth: play the
  showtime jingle and the horde goes down the tiers into the pool -- slow
  going, and the whole arena is a firing line.
"""
from __future__ import annotations

import math
import random
from typing import List, Sequence, Tuple

from .kit import (
    ASPHALT, CONCRETE, CONCRETE_DARK, FLOOR, GLASS, LAMP, STEEL, STEEL_DARK, WARM, WOOD,
    WOOD_DARK, WOOD_LIGHT, Area, Surfaces, barrel_spot, bench, boundary, building, bus, car,
    carve, chain_fence, crate, deploy_pad, flight, holed_wall, lamp_post, plate, post_sign,
    rect, room_walls, sign_decal, slab, solid_fence, strip_light, supply_ammo, supply_med,
    threshold, van, wall_sign)
from ..relay.kit import board_letters, ellipse_rects, mound, pine, ridge, tier_stack, tree

Rect = Tuple[float, float, float, float]

HALF = 280.0
SKY = {"top": "#3a4a8a", "horizon": "#f2a868", "sun": [0.62, 0.2, -0.5],
       "clouds": 0.34, "tint": "#ffd0a0"}
AMBIENT = "#8a7a78"

GRASS = "#5a7a3a"
SOIL = "#5a4a38"
PAVING = "#c8b89a"
PAVING_DARK = "#b0a080"
ROCK = "#9a8a72"
ROCK_DARK = "#80725e"
SAND = "#d8c08a"
TILE = "#e8e4da"
GREEN_TRIM = "#3a7a4a"
CREAM = "#f2e8d2"
TERRACOTTA = "#b8643a"

T1_TOP, T2_TOP = 4.0, 8.0
T1 = (-280.0, 280.0, 60.0, 280.0)
T2 = (-130.0, 130.0, 160.0, 280.0)

VET = (-46.0, 46.0, -28.0, 20.0)
VET_H = 13.0
VET_ROOF = VET_H + 1.2
VET_HOLE = (28.0, 44.0, -26.0, -18.0)

DECK = 19.0                                  # the monorail's walking surface
LOOP_OUT = (-104.0, 104.0, -44.0, 144.0)
LOOP_IN = (-96.0, 96.0, -36.0, 136.0)
PLATFORM = (-104.0, -60.0, -52.0, -44.0)

ARENA = (-54.0, 54.0, -130.0, -66.0)
ARENA_FLOOR = -6.0
ARENA_POOL = (-24.0, 24.0, -92.0, -72.0)
ARENA_BOOTH = (-10.0, 10.0, -146.0, -134.0)

PEN_POOL = (-200.0, -150.0, -168.0, -136.0)
GALLERY = (-204.0, -146.0, -192.0, -168.0)
GALLERY_FLOOR = -6.4
STAIR_W = (-220.0, -204.0, -188.0, -176.0)
STAIR_E = (-146.0, -130.0, -188.0, -176.0)

REPTILE = (-210.0, -130.0, -50.0, 30.0)
CROC = (-186.0, -154.0, -22.0, 10.0)

BARN = (140.0, 200.0, -50.0, -10.0)
YARD = (124.0, 240.0, -6.0, 44.0)
EPOOL = (206.0, 236.0, 12.0, 40.0)

FARM = (150.0, 200.0, -196.0, -156.0)
DUCKS = (126.0, 146.0, -138.0, -120.0)

GIFT = (40.0, 96.0, -244.0, -206.0)
FLAMINGOS = (-30.0, 30.0, -228.0, -208.0)

AVIARY = (-262.0, -150.0, 150.0, 262.0)
GIRAFFE_HOUSE = (-40.0, 10.0, 228.0, 270.0)
FEED = (30.0, 62.0, 166.0, 182.0)
FEED_TOP = 20.0

CAT_OUT = (156.0, 276.0, 140.0, 262.0)
CAT_IN = (168.0, 264.0, 152.0, 250.0)
CAT_C = (216.0, 201.0)
DEN_TUNNEL = (210.0, 222.0, 152.0, 200.0)
DEN_ROOM = (206.0, 226.0, 186.0, 200.0)

APE_OUT = (10.0, 72.0, 72.0, 124.0)
APE_IN = (22.0, 60.0, 84.0, 112.0)
PANDA = (-84.0, -36.0, 86.0, 128.0)


WALKS = [rect(-40.0, 40.0, -248.0, -146.0), rect(-130.0, 130.0, -160.0, -146.0),
         rect(-130.0, -116.0, -146.0, -40.0), rect(116.0, 130.0, -146.0, -40.0),
         rect(-130.0, 130.0, -62.0, -46.0), rect(-14.0, 14.0, 20.0, 44.0),
         rect(-130.0, 130.0, 30.0, 44.0), rect(-240.0, -130.0, -116.0, -100.0),
         rect(130.0, 240.0, -116.0, -100.0), rect(-14.0, 14.0, -46.0, -28.0),
         rect(-240.0, -226.0, -100.0, 44.0), rect(240.0, 254.0, -100.0, 44.0)]
TERRACE_WALKS = [rect(-140.0, 150.0, 60.0, 70.0), rect(-232.0, -140.0, 120.0, 132.0),
                 rect(144.0, 156.0, 70.0, 136.0)]
STATION_STAIR = (-100.0, -92.0, -92.0, -52.0)


def ground_y(x: float, z: float) -> float:
    """The top of whatever is underfoot on open ground: a walk, or grass
    (on the terraces, their tops)."""
    if z >= 60.0:
        top = T2_TOP if (T2[0] <= x <= T2[1] and z >= T2[2]) else T1_TOP
        return top + (0.3 if any(w[0] <= x <= w[1] and w[2] <= z <= w[3]
                                 for w in TERRACE_WALKS) else 0.0)
    return 0.3 if any(w[0] <= x <= w[1] and w[2] <= z <= w[3] for w in WALKS) else 0.0


def ring(outer: Rect, inner: Rect) -> List[Rect]:
    """The band between two rectangles, as four non-overlapping pieces."""
    return carve(outer, [inner])


def build(b: Area) -> None:
    rng = random.Random(0x200)
    b.extra.update({"weather": "motes", "accent": "#f2a868"})
    s = Surfaces(b)
    _ground(b, s)
    boundary(b, 30.0, "#3a4a2e", "#2a3a22", rng, horizon="forest")
    _terraces(b)
    _vet(b, s)
    _monorail(b, s)
    _arena(b, s)
    _penguins(b, s, rng)
    _reptiles(b, s)
    _elephants(b, s, rng)
    _farm(b, s, rng)
    _entrance(b, s, rng)
    _aviary(b, rng)
    _savannah(b, rng)
    _cats(b)
    _primates(b)
    _panda(b)
    _kiosks(b, s)
    _knolls(b, s, rng)
    _paths(b, s)
    _gardens(b, rng)
    _rigs(b)
    _zombie_spawns(b)
    for x, z, name in ((0, -4, "the vet hospital"), (0, -100, "the sea lion arena"),
                       (-82, -60, "the zoo station"), (0, 140, "the monorail"),
                       (-206, 206, "the aviary"), (-40, 200, "the savannah"),
                       (46, 174, "the feeding platform"), (216, 201, "the big cat rocks"),
                       (-170, -10, "the reptile house"), (170, -30, "the elephant house"),
                       (182, 20, "the elephant yard"), (-175, -160, "the penguin cove"),
                       (175, -160, "the petting farm"), (68, -225, "the gift shop"),
                       (0, -250, "the main gate"), (41, 98, "primate island"),
                       (-60, 108, "the panda grove"), (0, -216, "the flamingo pond")):
        b.landmark(float(x), float(z), name)
    b.camera(0.0, 60.0, -200.0, 0.0, 10.0, 0.0)
    b.camera(-100.0, 26.0, -70.0, 60.0, 10.0, 140.0)
    b.camera(150.0, 40.0, 100.0, 216.0, 10.0, 201.0)
    b.camera(-120.0, 10.0, -200.0, -175.0, -3.0, -150.0)


# ================================================================ ground
def _ground(b: Area, s: Surfaces) -> None:
    h = b.half + b.margin
    holes = [ARENA, PEN_POOL, GALLERY, STAIR_W, STAIR_E, CROC, EPOOL, FLAMINGOS, DUCKS]
    for hole in holes:
        s.reserve(hole)
    pieces = carve(rect(-h, h, -h, h), holes)
    plate(b, pieces, 0.0, 0.6, GRASS, studs=True, material="grass")
    plate(b, pieces, -0.6, 5.4, SOIL)
    # the shallow ponds: a bed and a skin of water
    for pond, bed, top, colour in ((FLAMINGOS, -1.6, -0.5, "#5a9aa8"),
                                   (DUCKS, -2.0, -0.6, "#4a8a8a"),
                                   (EPOOL, -4.0, -0.8, "#5a8a7a"),
                                   (CROC, -4.0, -0.8, "#3a5a3a")):
        slab(b, pond, bed, 2.0, "#5a5a48", studs=True)
        x0, x1, z0, z1 = pond
        b.water((x0 + x1) / 2.0, (z0 + z1) / 2.0, x1 - x0, z1 - z0, top, colour)


def _terraces(b: Area) -> None:
    """The hill the zoo climbs: a terrace across the north half, the
    savannah above that, with the moats dug down through the terrace."""
    holes = ring(CAT_OUT, CAT_IN) + ring(APE_OUT, APE_IN)
    plate(b, carve(T1, holes), T1_TOP, T1_TOP, "#5f7f3c", studs=True, material="grass")
    slab(b, T2, T2_TOP, T2_TOP - T1_TOP, "#6a8a40", studs=True, material="grass")
    # the retaining walls' coping, the stairs up through them
    flight(b, "z", 44.0, 60.0, -14.0, 14.0, 0.0, T1_TOP, PAVING_DARK, fill=0.0)
    flight(b, "z", 44.0, 60.0, -232.0, -220.0, 0.0, T1_TOP, PAVING_DARK, fill=0.0)
    flight(b, "z", 44.0, 60.0, 248.0, 260.0, 0.0, T1_TOP, PAVING_DARK, fill=0.0)
    flight(b, "z", 148.0, 160.0, -76.0, -64.0, T1_TOP, T2_TOP, PAVING_DARK, fill=T1_TOP)
    flight(b, "z", 148.0, 160.0, 100.0, 112.0, T1_TOP, T2_TOP, PAVING_DARK, fill=T1_TOP)
    # the moats' floors: gravel at the bottom, four units down
    for piece in ring(CAT_OUT, CAT_IN) + ring(APE_OUT, APE_IN):
        b.box([(piece[0] + piece[1]) / 2.0, 0.15, (piece[2] + piece[3]) / 2.0],
              [piece[1] - piece[0], 0.3, piece[3] - piece[2]], "#8a8070", collide=False)


# ========================================================= vet hospital
def _vet(b: Area, s: Surfaces) -> None:
    x0, x1, z0, z1 = VET
    s.reserve(VET)
    head = 10.0
    building(b, VET, 0.0, VET_H, CREAM, roof_colour="#4a5a4a", floor_colour=TILE,
             doors={"z+": [(-8.0, 8.0, head)], "z-": [(-8.0, 8.0, head)],
                    "x-": [(-12.0, 0.0, head)], "x+": [(-12.0, 0.0, head)]},
             windows={"z+": [(-40.0, -14.0, 3.6, 8.4), (14.0, 40.0, 3.6, 8.4)],
                      "z-": [(-40.0, -14.0, 3.6, 8.4), (14.0, 26.0, 3.6, 8.4)]},
             glass=True, roof_holes=[VET_HOLE], parapet=3.0, lights=LAMP)
    for side in ("z+", "z-"):
        threshold(b, VET, side, (-8.0, 8.0))
    for side in ("x-", "x+"):
        threshold(b, VET, side, (-12.0, 0.0))
    for zz in (z0 - 0.15, z1 + 0.15):
        for a, c in ((x0, -10.0), (10.0, x1)):
            b.box([(a + c) / 2.0, 11.6, zz], [c - a, 1.2, 0.3], GREEN_TRIM)
    wall_sign(b, 0.0, 11.2, z1 + 0.5, 34.0, 2.4,
              sign_decal("ZOO VETERINARY HOSPITAL", GREEN_TRIM, "#f2f2f2", 14.0), "z+",
              GREEN_TRIM)
    wall_sign(b, 0.0, 11.2, z0 - 0.5, 20.0, 2.4,
              sign_decal("STAFF ONLY", GREEN_TRIM, "#f2f2f2", 8.3), "z-", GREEN_TRIM)
    floor = FLOOR
    for z in (8.0, -2.0):
        for x in (-36.0, -27.0, -18.0, -9.0, 9.0, 18.0, 27.0, 36.0):
            deploy_pad(b, x, z, floor, "#f2a868", 5.0)
            b.safe_spawn(x, floor + 0.6, z, 0.0)
    # the surgery: the table under its lamp, the X-ray box, the cages
    b.box([-20.0, floor + 1.8, -18.0], [10.0, 3.6, 5.0], "#a8adb2", material="metal")
    b.box([-20.0, floor + 3.8, -18.0], [8.0, 0.4, 3.6], "#e8e8e8")
    b.box([-34.0, floor + 5.5, -26.6], [8.0, 6.0, 0.6], "#cfe8ff", material="neon")
    for k in range(3):
        for j in range(2):
            b.box([-42.0, floor + 1.6 + j * 3.4, -22.0 + k * 5.0], [6.0, 3.2, 4.6],
                  "#8a8f94", material="metal")
            b.box([-38.95, floor + 1.6 + j * 3.4, -22.0 + k * 5.0], [0.1, 2.4, 3.6],
                  "#2a2d31", collide=False)
    # the pharmacy shelves and the stair to the roof
    b.box([10.0, floor + 4.0, -26.0], [14.0, 8.0, 3.0], WOOD_DARK)
    for k in range(3):
        b.box([10.0, floor + 2.0 + k * 2.4, -24.4], [13.0, 0.3, 0.2], "#e8e8e8")
    flight(b, "x", 18.0, 44.0, -26.0, -18.0, floor, VET_ROOF, CONCRETE_DARK, fill=floor)
    supply_ammo(b, -42.5, floor, 12.0, "x+")
    supply_med(b, 42.0, floor, 10.0, "x-")
    def rail(xa, xb, za, zb, y):
        b.box([(xa + xb) / 2.0, y + 1.6, (za + zb) / 2.0], [xb - xa, 3.2, zb - za], STEEL,
              material="metal")
    rail(VET_HOLE[0], VET_HOLE[1], VET_HOLE[3], VET_HOLE[3] + 0.6, VET_ROOF)
    rail(VET_HOLE[0] - 0.6, VET_HOLE[0], VET_HOLE[2], VET_HOLE[3] + 0.6, VET_ROOF)
    supply_ammo(b, -30.0, VET_ROOF, 8.0, "z-")
    # the animal ambulance outside
    van(b, 60.0, -2.0, "z", "#f2f2f2", stripe="#3a7a4a", lights="#f2a83a", label="ZOO VET")
    barrel_spot(b, -52.0, 0.0, -24.0)


# ============================================================= monorail
def _monorail(b: Area, s: Surfaces) -> None:
    legs = [rect(-104.0, 104.0, -44.0, -36.0), rect(-104.0, 104.0, 136.0, 144.0),
            rect(-104.0, -96.0, -36.0, 136.0), rect(96.0, 104.0, -36.0, 136.0)]
    for leg in legs:
        slab(b, leg, DECK, 1.0, "#d8dcd8", studs=True)
    # the beam under the deck, and the stilts
    for leg in legs:
        x0, x1, z0, z1 = leg
        b.box([(x0 + x1) / 2.0, DECK - 1.8, (z0 + z1) / 2.0],
              [max(2.0, x1 - x0 - 4.0) if x1 - x0 > 9 else 3.0, 1.6,
               max(2.0, z1 - z0 - 4.0) if z1 - z0 > 9 else 3.0], "#9aa0a6")
    stilts = []
    for x in (-78.0, -52.0, -26.0, 26.0, 52.0, 78.0):
        stilts += [(x, -40.0), (x, 140.0)]
    for z in (-14.0, 12.0, 38.0, 90.0, 116.0):
        stilts += [(-100.0, z), (100.0, z)]
    stilts += [(-100.0, -40.0), (100.0, -40.0), (-100.0, 140.0), (100.0, 140.0), (0.0, 140.0)]
    for x, z in stilts:
        base = T1_TOP if z >= 60.0 else 0.0
        b.box([x, (base + DECK - 2.6) / 2.0, z], [3.0, DECK - 2.6 - base, 3.0], "#b8bcc0")
    # the rails along both edges, open where the stairs come up
    room_walls(b, LOOP_OUT, 0.6, DECK, DECK + 1.4, "#3a7a4a",
               doors={"z-": [(-104.0, -60.0, DECK + 3.0)], "x-": [(96.0, 104.0, DECK + 3.0)],
                      "x+": [(136.0, 144.0, DECK + 3.0)]})
    room_walls(b, rect(-96.6, 96.6, -36.6, 136.6), 0.6, DECK, DECK + 1.4, "#3a7a4a")
    # the station: a platform off the south-west corner, a canopy, the stair
    slab(b, PLATFORM, DECK, 1.0, "#d8dcd8", studs=True)
    for x in (-102.0, -62.0):
        b.box([x, (DECK - 1.0) / 2.0, -50.0], [2.4, DECK - 1.0, 2.4], "#b8bcc0")
    b.box([-104.0 + 0.3, DECK + 0.7, -48.0], [0.6, 1.4, 8.0], "#3a7a4a")
    b.box([-76.0, DECK + 0.7, -51.7], [32.0, 1.4, 0.6], "#3a7a4a")
    b.box([-102.0, DECK + 0.7, -51.7], [3.2, 1.4, 0.6], "#3a7a4a")
    s.reserve(STATION_STAIR)
    flight(b, "z", -92.0, -52.0, -100.0, -92.0, 0.0, DECK, "#9aa0a6", fill=0.0)
    for x in (-103.0, -61.0):
        for z in (-51.0, -45.0):
            b.cyl([x, DECK + 4.5, z], [0.8, 9.0, 0.8], "#3a7a4a", material="metal")
    slab(b, rect(-105.0, -59.0, -53.0, -43.0), DECK + 9.6, 0.6, "#f2a868")
    wall_sign(b, -80.0, DECK + 10.6, -53.4, 20.0, 1.8, sign_decal("ZOO STATION", "#3a7a4a",
                                                                 "#f2f2f2", 11.0), "z-",
              "#3a7a4a")
    supply_ammo(b, -70.0, DECK, -48.0, "z+")
    barrel_spot(b, -110.0, 0.0, -60.0)
    # the other two ways up: by the aviary and by the big cats
    flight(b, "x", -140.0, -104.0, 96.0, 104.0, T1_TOP, DECK, "#9aa0a6", fill=T1_TOP)
    flight(b, "x", 144.0, 104.0, 136.0, 144.0, T1_TOP, DECK, "#9aa0a6", fill=T1_TOP)
    # the train, stalled on the north side: you walk through it
    for x0, x1, nose in ((-40.0, -6.0, -1), (-4.0, 30.0, 1)):
        car_r = rect(x0, x1, 136.6, 143.4)
        building(b, car_r, DECK, 7.0, "#f2f2f2", t=0.4, roof_colour="#3a7a4a", roof_t=0.6,
                 doors={"x-": [(137.4, 142.6, DECK + 6.2)], "x+": [(137.4, 142.6, DECK + 6.2)]},
                 windows={"z-": [(x0 + 3.0, x1 - 3.0, DECK + 3.0, DECK + 5.6)],
                          "z+": [(x0 + 3.0, x1 - 3.0, DECK + 3.0, DECK + 5.6)]},
                 glass=True, lights=WARM)
        b.box([(x0 + x1) / 2.0, DECK + 2.4, 136.5], [x1 - x0 - 0.8, 0.6, 0.2], "#3a7a4a")
        b.box([(x0 + x1) / 2.0, DECK + 2.4, 143.5], [x1 - x0 - 0.8, 0.6, 0.2], "#3a7a4a")
    b.box([-5.0, DECK + 0.6, 140.0], [3.0, 1.2, 1.2], "#5a5f66")


# ================================================================ arena
def _arena(b: Area, s: Surfaces) -> None:
    """The sea lion arena: sunk into the ground, seats in steps down three
    sides to the pool and its rock, the stage wall on the fourth."""
    x0, x1, z0, z1 = ARENA
    floor = rect(-30.0, 30.0, -100.0, -66.0)
    tiers = [rect(-38.0, 38.0, -110.0, -66.0), rect(-46.0, 46.0, -120.0, -66.0),
             rect(-54.0, 54.0, -130.0, -66.0)]
    tops = [-4.5, -3.0, -1.5]
    plate(b, carve(floor, [ARENA_POOL]), ARENA_FLOOR, 5.0, "#a8b4b8", studs=True)
    inner = floor
    colours = ["#4a7aa8", "#e8e2d4", "#4a7aa8"]
    for k, tier in enumerate(tiers):
        plate(b, carve(tier, [inner]), tops[k], tops[k] - ARENA_FLOOR + 5.0, colours[k],
              studs=True)
        inner = tier
    # the pool, its rock, and the stage wall behind
    slab(b, ARENA_POOL, -9.0, 2.0, "#3a6a8a", studs=True)
    b.water(0.0, -82.0, 48.0, 20.0, -6.6, "#2f7aa8")
    tier_stack(b, [[rect(-6.0, 6.0, -86.0, -78.0)], [rect(-3.0, 3.0, -84.0, -80.0)]], -9.0,
               [3.8, 1.4], [ROCK, ROCK_DARK])
    b.box([0.0, 6.0, -64.0], [112.0, 12.0, 4.0], "#3a6a9a")
    b.box([0.0, 12.6, -64.0], [116.0, 1.2, 5.0], "#f2f2f2")
    for k in range(7):
        b.box([-48.0 + k * 16.0, 2.2, -66.1], [10.0, 4.4, 0.2], "#5a9ac8")
    board_letters(b, 0.0, 7.6, -66.0, "SPLASH SHOW", 4.0, "#3a6a9a", "#f2f2f2", facing="z-",
                  solid=True)
    # the announcer's booth at the top of the seats, its horns on a pole
    s.reserve(ARENA_BOOTH)
    building(b, ARENA_BOOTH, 0.0, 9.0, "#f2f2f2", roof_colour="#3a6a9a",
             floor_colour="#8a7a6a", doors={"z+": [(-4.0, 4.0, 7.4)]},
             windows={"z+": [(-9.0, -5.0, 3.4, 7.0), (5.0, 9.0, 3.4, 7.0)]}, glass=True,
             lights=WARM)
    threshold(b, ARENA_BOOTH, "z+", (-4.0, 4.0))
    b.box([0.0, FLOOR + 1.6, -143.0], [12.0, 3.2, 3.0], "#5a5f66")
    b.set_lure(0.0, FLOOR, -139.0, "the showtime jingle", "Play the showtime jingle",
               "ll_showtime", (0.0, -6.0, -82.0))
    supply_ammo(b, 13.6 + 3.0, 0.0, -140.0, "x+")
    b.cyl([-14.0, 8.0, -140.0], [0.8, 16.0, 0.8], STEEL_DARK, material="metal")
    for dx, turn in ((-1.4, -0.4), (1.4, 0.4)):
        b.cone([-14.0 + dx, 15.0, -138.6], [1.6, 2.4, 1.6], "#c8c8c8", r=[-1.2, turn, 0],
               collide=False)
    barrel_spot(b, 60.0, 0.0, -140.0)


# ============================================================ penguins
def _penguins(b: Area, s: Surfaces, rng: random.Random) -> None:
    """The cove: rockwork round a deep pool, and the gallery dug in beside
    it -- a long dark room with a window into the water, stairs down at
    each end."""
    px0, px1, pz0, pz1 = PEN_POOL
    slab(b, PEN_POOL, -8.0, 2.0, "#4a6a7a", studs=True)
    for (a, c, d, e) in ((px0, px1, pz1 - 0.8, pz1), (px0, px0 + 0.8, pz0, pz1 - 0.8),
                         (px1 - 0.8, px1, pz0, pz1 - 0.8)):
        b.box([(a + c) / 2.0, -7.0, (d + e) / 2.0], [c - a, 2.0, e - d], "#6a7a7a")
    b.water((px0 + px1) / 2.0, (pz0 + pz1) / 2.0, px1 - px0, pz1 - pz0, -1.0, "#3a8ab8")
    # the gallery: floor, walls, the window, a roof at ground level
    gx0, gx1, gz0, gz1 = GALLERY
    slab(b, GALLERY, GALLERY_FLOOR, 2.0, "#3a4a5a", studs=True)
    room_walls(b, rect(gx0, gx1, gz0, gz1 - 1.0), 1.0, GALLERY_FLOOR, -0.6, "#5a6a7a",
               doors={"x-": [(STAIR_W[2], STAIR_W[3], -0.6)],
                      "x+": [(STAIR_E[2], STAIR_E[3], -0.6)]}, sides=("x-", "x+", "z-"))
    holed_wall(b, "x", gz1 - 0.5, 1.0, gx0, gx1, GALLERY_FLOOR, -0.6, "#5a6a7a",
               holes=[(px0 + 2.0, px1 - 2.0, GALLERY_FLOOR + 0.6, -1.6)], glass=True)
    slab(b, GALLERY, 0.0, 0.6, "#8a9aa8", studs=True)
    for k in range(4):
        strip_light(b, gx0 + 8.0 + k * 14.0, (gz0 + gz1) / 2.0 - 2.0, -0.6, 6.0, "x",
                    "#9fe8ff")
    flight(b, "x", STAIR_W[0], STAIR_W[1], STAIR_W[2], STAIR_W[3], 0.0, GALLERY_FLOOR,
           CONCRETE_DARK, fill=GALLERY_FLOOR - 2.0)
    flight(b, "x", STAIR_E[1], STAIR_E[0], STAIR_E[2], STAIR_E[3], 0.0, GALLERY_FLOOR,
           CONCRETE_DARK, fill=GALLERY_FLOOR - 2.0)
    for st, open_side in ((STAIR_W, "x-"), (STAIR_E, "x+")):
        sx0, sx1, sz0, sz1 = st
        for z in (sz0 - 0.4, sz1 + 0.4):
            b.box([(sx0 + sx1) / 2.0, 1.6, z], [sx1 - sx0, 3.2, 0.8], STEEL, material="metal")
    b.box([(px0 + px1) / 2.0, 2.0, pz0 - 0.4], [px1 - px0, 4.0, 0.8], GLASS,
          material="glass", alpha=0.42)
    supply_med(b, -175.0, GALLERY_FLOOR, -188.6, "z+")
    wall_sign(b, -175.0, -2.4, gz0 + 1.4, 22.0, 1.6,
              sign_decal("PENGUINS -- UNDERWATER GALLERY", "#1b2a35", "#9fe8ff", 13.7), "z+",
              "#1b2a35")
    # the rockwork round the other three sides, the penguins' slide
    for k, (r, top) in enumerate(((rect(-214.0, -200.0, -168.0, -124.0), 3.0),
                                  (rect(-200.0, -150.0, -136.0, -124.0), 2.6),
                                  (rect(-150.0, -138.0, -168.0, -124.0), 3.4))):
        slab(b, r, top, top, ROCK if k % 2 else ROCK_DARK, studs=True)
    for r, base, top in ((rect(-212.0, -204.0, -160.0, -140.0), 3.0, 6.0),
                         (rect(-190.0, -166.0, -134.0, -126.0), 2.6, 5.4),
                         (rect(-148.0, -140.0, -150.0, -130.0), 3.4, 6.6)):
        slab(b, r, top, top - base, ROCK)
    s.reserve(rect(-214.0, -138.0, -168.0, -124.0))
    wall_sign(b, -137.6, 1.8, -146.0, 12.0, 2.2, sign_decal("PENGUIN COVE", "#f2f2f2",
                                                            "#1b2a35", 5.4), "x+", "#f2f2f2")


# ============================================================ reptiles
def _reptiles(b: Area, s: Surfaces) -> None:
    x0, x1, z0, z1 = REPTILE
    s.reserve(REPTILE)
    building(b, REPTILE, 0.0, 16.0, "#6a7a5a", roof_colour="#3a4a32",
             doors={"x+": [(-14.0, -2.0, 11.0)], "z-": [(-178.0, -166.0, 11.0)],
                    "x-": [(2.0, 14.0, 11.0)]},
             windows={}, lights="#5aa86a")
    inner = rect(x0 + 2.0, x1 - 2.0, z0 + 2.0, z1 - 2.0)
    plate(b, carve(inner, [CROC]), FLOOR, FLOOR, "#4a5a42")
    for side, span in (("x+", (-14.0, -2.0)), ("z-", (-178.0, -166.0)), ("x-", (2.0, 14.0))):
        threshold(b, REPTILE, side, span)
    # the footbridge over the crocodile pool, glass along both sides
    slab(b, rect(-174.0, -166.0, -24.0, 12.0), 1.2, 0.8, WOOD_LIGHT, studs=True)
    for x in (-173.7, -166.3):
        b.box([x, 1.2 + 1.4, -6.0], [0.6, 2.8, 36.0], GLASS, material="glass", alpha=0.4)
    # terrariums round the walls: glass fronts, lit, with something in them
    for k, (cx, cz, w, d, face) in enumerate((
            (-198.0, 24.0, 12.0, 6.0, "z-"), (-182.0, 24.0, 12.0, 6.0, "z-"),
            (-148.0, 24.0, 12.0, 6.0, "z-"), (-205.0, -32.0, 6.0, 12.0, "x+"),
            (-205.0, -16.0, 6.0, 12.0, "x+"), (-135.0, -30.0, 6.0, 12.0, "x-"),
            (-198.0, -45.0, 12.0, 6.0, "z+"), (-148.0, -45.0, 12.0, 6.0, "z+"))):
        b.box([cx, FLOOR + 4.5, cz], [w, 9.0, d], "#2a3a2a")
        off = {"z-": (0.0, -d / 2.0 - 0.1), "z+": (0.0, d / 2.0 + 0.1),
               "x+": (w / 2.0 + 0.1, 0.0), "x-": (-w / 2.0 - 0.1, 0.0)}[face]
        gw, gd = (w - 1.0, 0.2) if face[0] == "z" else (0.2, d - 1.0)
        b.box([cx + off[0], FLOOR + 4.5, cz + off[1]], [gw, 7.0, gd], "#8adaa8",
              material="neon", collide=False, alpha=0.5)
    # the python's tank, big, in the north-east corner
    b.box([-142.0, FLOOR + 3.0, 16.0], [14.0, 6.0, 10.0], "#3a4a2a")
    b.box([-149.1, FLOOR + 3.0, 16.0], [0.2, 5.0, 9.0], "#8adaa8", material="neon",
          collide=False, alpha=0.5)
    supply_med(b, -137.0, FLOOR, 4.0, "x-")
    supply_ammo(b, -200.0, FLOOR, -4.0, "x+")
    wall_sign(b, x1 + 0.5, 13.0, -8.0, 22.0, 2.4,
              sign_decal("REPTILE HOUSE", "#3a4a32", "#c8f0a0", 9.2), "x+", "#3a4a32")


# ============================================================ elephants
def _elephants(b: Area, s: Surfaces, rng: random.Random) -> None:
    x0, x1, z0, z1 = BARN
    s.reserve(BARN)
    building(b, BARN, 0.0, 22.0, "#b8a078", roof_colour=TERRACOTTA, floor_colour="#a89068",
             doors={"z+": [(160.0, 180.0, 18.0)], "x-": [(-36.0, -24.0, 11.0)]},
             windows={"z-": [(146.0, 156.0, 12.0, 18.0), (184.0, 194.0, 12.0, 18.0)]},
             glass=True, lights=WARM)
    threshold(b, BARN, "z+", (160.0, 180.0))
    threshold(b, BARN, "x-", (-36.0, -24.0))
    # hay in the barn, stacked in steps along the east wall
    for k, (hx, hz, h) in enumerate(((190.0, -42.0, 2.4), (190.0, -36.0, 4.8),
                                     (190.0, -30.0, 7.2))):
        b.box([hx, FLOOR + h / 2.0, hz], [8.0, h, 6.0], "#d8c070", studs=True)
    supply_med(b, 194.0, FLOOR, -18.0, "x-")
    barrel_spot(b, 204.0, 0.0, -44.0)
    # the yard: sand, the pool, a log; a wall round it to keep them in
    yx0, yx1, yz0, yz1 = YARD
    s.reserve(YARD)
    plate(b, carve(YARD, [EPOOL]), 0.4, 0.4, SAND, studs=True)
    for (a, c, d, e) in ((yx0, yx1, yz1 - 1.6, yz1), (yx1 - 1.6, yx1, yz0, yz1 - 1.6)):
        b.box([(a + c) / 2.0, 0.4 + 1.6, (d + e) / 2.0], [c - a, 3.2, e - d], ROCK)
    b.box([186.0, 1.4, 34.0], [16.0, 2.0, 2.4], WOOD_DARK)
    # the viewing deck along the yard's west side, up a few steps
    deck = rect(112.0, 124.0, 0.0, 40.0)
    s.reserve(deck)
    slab(b, deck, 5.0, 5.0, WOOD, studs=True)
    flight(b, "z", -10.0, 0.0, 112.0, 124.0, 0.0, 5.0, WOOD_DARK, fill=0.0)
    b.box([123.7, 5.0 + 1.4, 20.0], [0.6, 2.8, 40.0], GLASS, material="glass", alpha=0.42)
    b.box([112.3, 5.0 + 1.4, 20.0], [0.6, 2.8, 40.0], WOOD_DARK)
    b.box([118.0, 5.0 + 1.4, 39.7], [10.8, 2.8, 0.6], WOOD_DARK)
    supply_ammo(b, 118.0, 5.0, 34.0, "x+")
    wall_sign(b, 180.0, 20.0, z1 + 0.5, 22.0, 2.6,
              sign_decal("ELEPHANT HOUSE", TERRACOTTA, "#f2e8d2", 8.5), "z+", TERRACOTTA)


# ================================================================= farm
def _farm(b: Area, s: Surfaces, rng: random.Random) -> None:
    x0, x1, z0, z1 = FARM
    s.reserve(FARM)
    building(b, FARM, 0.0, 18.0, "#a83a2a", roof_colour="#5a5f66", floor_colour="#8a6f52",
             doors={"x-": [(-184.0, -168.0, 14.0)], "z+": [(168.0, 182.0, 12.0)]},
             windows={"x+": [(-186.0, -176.0, 8.0, 12.0)]}, glass=True, lights=WARM)
    threshold(b, FARM, "x-", (-184.0, -168.0))
    threshold(b, FARM, "z+", (168.0, 182.0))
    # the loft along the east side, a stair up to it, hay up there
    loft_top = 9.4
    slab(b, rect(176.0, 198.0, -194.0, -158.0), loft_top, 0.8, WOOD, studs=True)
    flight(b, "x", 160.0, 176.0, -194.0, -186.0, FLOOR, loft_top, WOOD_DARK, fill=FLOOR)
    b.box([176.3, loft_top + 1.4, -172.0], [0.6, 2.8, 26.0], WOOD_DARK)
    for k in range(2):
        b.box([190.0, loft_top + 1.2 * (k + 1), -164.0 - k * 6.0], [8.0, 2.4 * (k + 1), 5.0],
              "#d8c070", studs=True)
    supply_ammo(b, 192.0, loft_top, -186.0, "x-")
    supply_med(b, 156.0, FLOOR, -160.0, "z-")
    barrel_spot(b, 146.0, 0.0, -198.0)
    # the pens and the goats' mountain
    solid_fence(b, 120.0, -150.0, 150.0, -150.0, 3.0, WOOD_LIGHT, WOOD_DARK, 10.0)
    solid_fence(b, 120.0, -200.0, 120.0, -160.0, 3.0, WOOD_LIGHT, WOOD_DARK, 10.0)
    s.reserve(rect(206.0, 240.0, -146.0, -112.0))
    tier_stack(b, [[rect(206.0, 240.0, -146.0, -112.0)], [rect(212.0, 234.0, -140.0, -118.0)],
                   [rect(218.0, 228.0, -134.0, -124.0)]], 0.0, [2.0, 2.0, 2.0],
               [ROCK, ROCK_DARK, ROCK])
    solid_fence(b, 202.0, -150.0, 244.0, -150.0, 3.0, WOOD_LIGHT, WOOD_DARK, 10.0)
    wall_sign(b, 175.0, 14.0, z1 + 0.5, 20.0, 2.4,
              sign_decal("PETTING FARM", "#a83a2a", "#f2e8d2", 8.3), "z+", "#a83a2a")


# ============================================================== entrance
def _entrance(b: Area, s: Surfaces, rng: random.Random) -> None:
    gate_z = -252.0
    # the wall along the front, the gate in the middle, a service gate
    for xa, xb in ((-280.0, -30.0), (30.0, 140.0), (156.0, 280.0)):
        b.box([(xa + xb) / 2.0, 1.6, gate_z], [xb - xa, 3.2, 1.0], CREAM, studs=True)
        n = max(1, int(round((xb - xa) / 16.0)))
        for k in range(1, n):
            x = xa + (xb - xa) * k / n
            b.box([x, 2.2, gate_z], [1.8, 4.4, 1.8], GREEN_TRIM)
    for x in (140.0, 156.0):
        b.box([x, 3.0, gate_z], [2.0, 6.0, 2.0], GREEN_TRIM)
    for x in (-27.0, 27.0):
        b.box([x, 11.0, gate_z], [6.0, 22.0, 6.0], CREAM, studs=True)
        b.box([x, 22.6, gate_z], [7.0, 1.2, 7.0], GREEN_TRIM)
    b.box([0.0, 19.0, gate_z], [48.0, 4.0, 4.0], GREEN_TRIM)
    board_letters(b, 0.0, 19.0, gate_z - 2.0, "HARROW ZOO", 3.4, GREEN_TRIM, "#f2e8d2",
                  facing="z-", solid=False)
    board_letters(b, 0.0, 19.0, gate_z + 2.0, "COME AGAIN", 3.4, GREEN_TRIM, "#f2e8d2",
                  facing="z+", solid=False)
    # a giraffe and an elephant cut out of steel, up on the arch
    b.box([-12.0, 22.5, gate_z], [6.0, 3.0, 1.0], "#e8b83a", collide=False)
    b.box([-10.0, 27.0, gate_z], [1.4, 6.0, 1.0], "#e8b83a", collide=False)
    b.box([-9.0, 30.4, gate_z], [3.0, 1.6, 1.0], "#e8b83a", collide=False)
    b.box([12.0, 22.9, gate_z], [7.0, 3.8, 1.0], "#8a9aa8", collide=False)
    b.box([16.2, 22.6, gate_z], [1.4, 2.6, 1.0], "#8a9aa8", collide=False)
    for x in (-16.0, -6.0, 6.0, 16.0):
        b.box([x, 1.6, gate_z], [2.0, 3.2, 3.0], "#8a8f94", material="metal")
    # the ticket booths outside the gate
    for bx in (-44.0, 44.0):
        booth = rect(bx - 6.0, bx + 6.0, gate_z - 14.0, gate_z - 4.0)
        s.reserve(booth)
        building(b, booth, 0.0, 9.0, CREAM, roof_colour=GREEN_TRIM,
                 doors={"z+": [(bx - 4.0, bx + 4.0, 7.4)]},
                 windows={"z-": [(bx - 4.0, bx + 4.0, 3.4, 7.0)]}, glass=True, lights=WARM)
        threshold(b, booth, "z+", (bx - 4.0, bx + 4.0))
    # the car park outside, and the school bus that brought a class
    s.lay(rect(-280.0, 280.0, -280.0, -253.0), 0.3, ASPHALT)
    for k, x in enumerate((-220.0, -180.0, -140.0, 120.0, 160.0, 200.0, 240.0)):
        car(b, x, -270.0, "z" if k % 2 else "x", ["#c8a83a", "#3a5a6a", "#8a2a24", "#f2f2f2",
                                               "#2a2a2a", "#4a7a3a", "#7a4a8a"][k],
            length=11.0, y=0.3, wrecked=k == 2)
    bus(b, -80.0, -268.0, "x", label="HARROW SCHOOLS")
    # the gift shop: plush toys, a giant plush giraffe, first aid
    gx0, gx1, gz0, gz1 = GIFT
    s.reserve(GIFT)
    building(b, GIFT, 0.0, 12.0, CREAM, roof_colour=TERRACOTTA, floor_colour=TILE,
             doors={"x-": [(-232.0, -218.0, 10.0)]},
             windows={"x-": [(-242.0, -236.0, 3.6, 8.4), (-214.0, -208.0, 3.6, 8.4)],
                      "z+": [(50.0, 86.0, 3.6, 8.4)]}, glass=True, lights=WARM)
    threshold(b, GIFT, "x-", (-232.0, -218.0))
    plush = ["#e8b83a", "#8a9aa8", "#f2f2f2", "#c88a4a", "#e890b0", "#5a8a3a"]
    for k in range(3):
        sx = 58.0 + k * 14.0
        b.box([sx, FLOOR + 1.8, -236.0], [10.0, 3.6, 3.0], WOOD)
        for j in range(4):
            b.box([sx - 3.6 + j * 2.4, FLOOR + 4.4, -236.0], [1.8, 1.6, 1.8], plush[(k + j) % 6])
    b.box([86.0, FLOOR + 2.0, -214.0], [3.0, 4.0, 5.0], "#e8b83a")
    b.box([86.0, FLOOR + 6.0, -212.0], [1.6, 4.0, 1.6], "#e8b83a")
    b.box([86.0, FLOOR + 9.0, -210.6], [2.0, 2.0, 3.4], "#e8b83a")
    b.box([60.0, FLOOR + 1.7, -214.0], [10.0, 3.4, 4.0], GREEN_TRIM, studs=True)
    supply_med(b, 92.4 - 1.0, FLOOR, -226.0, "x-")
    supply_ammo(b, 46.0, FLOOR, -240.0, "z+")
    barrel_spot(b, 100.0, 0.0, -200.0)
    wall_sign(b, gx0 - 0.5, 10.6, -225.0, 20.0, 2.4,
              sign_decal("GIFT SHOP", TERRACOTTA, "#f2e8d2", 8.3), "x-", TERRACOTTA)
    # the zoo map board on the plaza
    b.box([-40.0, 3.3, -196.0], [1.0, 6.0, 1.0], WOOD_DARK)
    b.box([-34.0, 3.3, -196.0], [1.0, 6.0, 1.0], WOOD_DARK)
    wall_sign(b, -37.0, 6.7, -196.0, 12.0, 6.0,
              sign_decal("ZOO MAP  YOU ARE HERE  PLEASE DO NOT FEED THE INFECTED", "#f2e8d2",
                         "#3a5a2a", 2.0), "z-", "#f2e8d2")


# =============================================================== aviary
def _aviary(b: Area, rng: random.Random) -> None:
    x0, x1, z0, z1 = AVIARY
    y = T1_TOP
    top = y + 30.0
    mesh = "#5a6a5a"
    # mesh walls on posts, a door on the south side and one on the east
    def mesh_wall(axis, at, lo, hi, gaps):
        cursor = lo
        for a, c in sorted(gaps) + [(hi, hi)]:
            if a - cursor > 0.5:
                if axis == "x":
                    b.box([(cursor + a) / 2.0, y + 15.0, at], [a - cursor, 30.0, 0.3], mesh,
                          material="metal", alpha=0.3)
                else:
                    b.box([at, y + 15.0, (cursor + a) / 2.0], [0.3, 30.0, a - cursor], mesh,
                          material="metal", alpha=0.3)
            cursor = c
        n = int((hi - lo) // 14)
        for k in range(n + 1):
            u = lo + (hi - lo) * k / n
            if any(a - 0.8 < u < c + 0.8 for a, c in gaps):
                continue
            p = [u, y + 16.0, at] if axis == "x" else [at, y + 16.0, u]
            b.cyl(p, [1.2, 32.0, 1.2], "#3a4a3a", material="metal")
    mesh_wall("x", z0, x0, x1, [(-214.0, -200.0)])
    mesh_wall("x", z1, x0, x1, [])
    mesh_wall("z", x0, z0, z1, [])
    mesh_wall("z", x1, z0, z1, [(190.0, 204.0)])
    for gx in (-213.4, -200.6):
        b.box([gx, y + 8.0, z0], [1.2, 16.0, 1.2], "#3a4a3a")
    b.box([-207.0, y + 16.4, z0], [14.0, 0.8, 1.2], "#3a4a3a")
    b.box([-207.0, y + 16.8 + 6.6, z0], [14.0, 13.2, 0.3], mesh, material="metal", alpha=0.3)
    for gz in (190.6, 203.4):
        b.box([x1, y + 8.0, gz], [1.2, 16.0, 1.2], "#3a4a3a")
    b.box([x1, y + 16.4, 197.0], [1.2, 0.8, 14.0], "#3a4a3a")
    b.box([x1, y + 16.8 + 6.6, 197.0], [0.3, 13.2, 14.0], mesh, material="metal", alpha=0.3)
    b.box([(x0 + x1) / 2.0, top + 0.15, (z0 + z1) / 2.0], [x1 - x0, 0.3, z1 - z0], mesh,
          material="metal", alpha=0.22)
    # the canopy walk: up the west side and across to a deck among the trees
    land = y + 9.0
    canopy = y + 18.0
    flight(b, "z", 170.0, 206.0, -254.0, -246.0, y, land, WOOD, fill=y)
    slab(b, rect(-254.0, -238.0, 206.0, 222.0), land, 0.8, WOOD_LIGHT, studs=True)
    for (px, pz) in ((-253.0, 221.0), (-239.0, 221.0), (-239.0, 207.0)):
        b.box([px, (y + land - 0.8) / 2.0, pz], [1.0, land - 0.8 - y, 1.0], WOOD_DARK)
    flight(b, "x", -238.0, -206.0, 214.0, 222.0, land, canopy, WOOD, fill=y)
    deck = rect(-206.0, -178.0, 196.0, 232.0)
    slab(b, deck, canopy, 0.8, WOOD_LIGHT, studs=True)
    for (px, pz) in ((-205.0, 197.0), (-179.0, 197.0), (-205.0, 231.0), (-179.0, 231.0)):
        b.box([px, (y + canopy - 0.8) / 2.0, pz], [1.2, canopy - 0.8 - y, 1.2], WOOD_DARK)
    for (rx, rz, w, d) in ((-192.3, 196.3, 27.4, 0.6), (-192.3, 231.7, 27.4, 0.6),
                           (-178.3, 214.0, 0.6, 36.0)):
        b.box([rx, canopy + 1.4, rz], [w, 2.8, d], WOOD_DARK)
    b.box([-205.7, canopy + 1.4, 205.3], [0.6, 2.8, 17.4], WOOD_DARK)
    b.box([-205.7, canopy + 1.4, 226.7], [0.6, 2.8, 9.4], WOOD_DARK)
    supply_ammo(b, -192.0, canopy, 226.0, "z-")
    # the trees: the big one in the middle that the deck is built round
    for (tx, tz, sc) in ((-192.0, 180.0, 1.6), (-232.0, 236.0, 1.6), (-236.0, 160.0, 1.4),
                         (-224.0, 252.0, 1.5), (-160.0, 166.0, 1.3)):
        tree(b, tx, tz, y, sc, "#6a4a2a", "#3f8a3a")
    # the pond and the waterfall over the rocks at the back
    slab(b, rect(-176.0, -152.0, 236.0, 260.0), y + 6.0, 6.0, ROCK, studs=True)
    slab(b, rect(-172.0, -156.0, 244.0, 258.0), y + 10.0, 4.0, ROCK_DARK, studs=True)
    b.water(-164.0, 226.0, 24.0, 16.0, y + 0.4, "#3a8ab8")


# ============================================================= savannah
def _savannah(b: Area, rng: random.Random) -> None:
    y = T2_TOP
    # acacias: thin trunks, flat crowns up out of reach
    for (tx, tz) in ((-100.0, 190.0), (-70.0, 250.0), (30.0, 230.0), (80.0, 200.0),
                     (50.0, 205.0), (-110.0, 262.0)):
        b.cyl([tx, y + 6.0, tz], [1.6, 12.0, 1.6], "#7a5a3a")
        b.cyl([tx, y + 13.0, tz], [14.0, 2.0, 14.0], "#6a8a3a", collide=False)
        b.cyl([tx, y + 14.4, tz], [10.0, 0.8, 10.0], "#7a9a4a", collide=False)
    # the water hole and the rocks round it
    b.box([-20.0, y + 0.12, 186.0], [24.0, 0.24, 14.0], "#4a8aa8", collide=False, alpha=0.8)
    for (rx, rz, s_) in ((-36.0, 180.0, 2.0), (2.0, 192.0, 1.6), (60.0, 250.0, 2.4)):
        b.sphere([rx, y + 1.6 * s_, rz], [5.0 * s_, 3.4 * s_, 4.4 * s_], ROCK)
    # the giraffe house: tall doors, a hay rack high on the wall
    gx0, gx1, gz0, gz1 = GIRAFFE_HOUSE
    building(b, GIRAFFE_HOUSE, y, 26.0, "#c8a878", roof_colour=TERRACOTTA, floor_colour="#a89068",
             doors={"z-": [(-30.0, -10.0, y + 22.0)]},
             windows={"x+": [(236.0, 262.0, y + 14.0, y + 20.0)]}, glass=True, lights=WARM)
    threshold(b, GIRAFFE_HOUSE, "z-", (-30.0, -10.0), y0=y)
    b.box([-15.0, y + 18.0, 266.4], [24.0, 4.0, 3.0], "#8a6a3a")
    supply_med(b, 4.0, y + FLOOR, 250.0, "x-")
    barrel_spot(b, 16.0, y, 236.0)
    # the feeding platform: up at giraffe height, stairs, a hay box
    fx0, fx1, fz0, fz1 = FEED
    slab(b, FEED, FEED_TOP, 1.0, WOOD_LIGHT, studs=True)
    for (px, pz) in ((fx0 + 1.0, fz0 + 1.0), (fx1 - 1.0, fz0 + 1.0), (fx0 + 1.0, fz1 - 1.0),
                     (fx1 - 1.0, fz1 - 1.0)):
        b.box([px, (y + FEED_TOP - 1.0) / 2.0, pz], [1.4, FEED_TOP - 1.0 - y, 1.4], WOOD_DARK)
    flight(b, "x", 92.0, fx1, 170.0, 178.0, y, FEED_TOP, WOOD, fill=y)
    for (rx, rz, w, d) in ((46.0, fz0 + 0.3, 32.0, 0.6), (46.0, fz1 - 0.3, 32.0, 0.6),
                           (fx0 + 0.3, 174.0, 0.6, 14.8)):
        b.box([rx, FEED_TOP + 1.4, rz], [w, 2.8, d], WOOD_DARK)
    b.box([fx1 - 0.3, FEED_TOP + 1.4, 168.3], [0.6, 2.8, 3.4], WOOD_DARK)
    b.box([fx1 - 0.3, FEED_TOP + 1.4, 179.7], [0.6, 2.8, 3.4], WOOD_DARK)
    b.box([40.0, FEED_TOP + 1.2, 178.0], [6.0, 2.4, 3.0], "#d8c070", studs=True)
    supply_ammo(b, 54.0, FEED_TOP, 178.4, "z-")
    wall_sign(b, 46.0, FEED_TOP + 4.6, fz1 + 0.1, 16.0, 2.2,
              sign_decal("FEED THE GIRAFFES", "#e8b83a", "#3a2a1a", 7.3), "z+", "#e8b83a")


# ================================================================= cats
def _cats(b: Area) -> None:
    """The big cats' rock: an island in a dry moat, its rock in steps, and
    a den in it you can get into from the moat."""
    cx, cz = CAT_C
    y = T1_TOP
    rises = [4.0, 4.0, 4.0, 4.0]
    fracs = [0.9, 0.7, 0.5, 0.3]
    top = y
    for k, f in enumerate(fracs):
        rects = ellipse_rects(cx, cz, 46.0 * f, 46.0 * f, 6.0)
        rects = [r for r in rects if r[0] >= CAT_IN[0] and r[1] <= CAT_IN[1]
                 and r[2] >= CAT_IN[2] and r[3] <= CAT_IN[3]]
        holes = [DEN_TUNNEL, DEN_ROOM] if k < 2 else []
        pieces = [p for r in rects for p in carve(r, holes)]
        plate(b, pieces, top + rises[k], rises[k], ROCK if k % 2 == 0 else ROCK_DARK, studs=True)
        top += rises[k]
    # (the den: a cut from the moat into the rock, and a cave at its end
    # under the third step, where the lions sleep and the infected wait)
    # the glass along the visitors' side of the moat, and a warning
    b.box([216.0, y + 2.0, CAT_OUT[2] - 0.3], [120.0, 4.0, 0.6], GLASS, material="glass",
          alpha=0.42)
    wall_sign(b, 182.0, y + 2.0, CAT_OUT[2] - 0.95, 30.0, 2.6,
              sign_decal("DANGER  DO NOT CLIMB  DO NOT FEED THE INFECTED", "#c43a32", "#f2f2f2",
                         11.5), "z-", "#c43a32")
    wall_sign(b, 250.0, y + 2.0, CAT_OUT[2] - 0.95, 20.0, 2.6,
              sign_decal("BIG CAT ROCKS", "#e8b83a", "#3a2a1a", 7.7), "z-", "#e8b83a")


# ============================================================= primates
def _primates(b: Area) -> None:
    x0, x1, z0, z1 = APE_IN
    y = T1_TOP
    # the climbing frame: posts, platforms, ropes overhead
    for (px, pz) in ((28.0, 90.0), (54.0, 90.0), (28.0, 106.0), (54.0, 106.0)):
        b.cyl([px, y + 7.0, pz], [1.6, 14.0, 1.6], "#6a4a2a")
    slab(b, rect(26.0, 34.0, 88.0, 96.0), y + 6.0, 0.8, WOOD)
    slab(b, rect(48.0, 56.0, 100.0, 108.0), y + 10.0, 0.8, WOOD)
    b.box([41.0, y + 13.6, 90.0], [26.0, 0.3, 0.3], "#c8a868", collide=False)
    b.sphere([36.0, y + 1.6, 104.0], [6.0, 3.4, 5.0], ROCK)
    post_sign(b, 41.0, APE_OUT[2] - 1.0, y, 3.0, 16.0, 2.2,
              sign_decal("PRIMATE ISLAND", "#3a7a4a", "#f2f2f2", 7.3), "z-", "#3a7a4a")


# ================================================================ panda
def _panda(b: Area) -> None:
    x0, x1, z0, z1 = PANDA
    y = T1_TOP
    for k in range(26):
        bx = x0 + 3.0 + (k * 7.3) % (x1 - x0 - 6.0)
        bz = z0 + 3.0 + (k * 11.7) % (z1 - z0 - 6.0)
        if -72.0 < bx < -48.0 and 84.0 < bz < 118.0:
            continue
        b.cyl([bx, y + 7.0, bz], [0.7, 14.0, 0.7], "#6a9a3a")
        b.box([bx + 0.6, y + 13.0, bz], [2.4, 0.2, 0.8], "#7aaa4a", collide=False)
    # the platform the panda sleeps on, and the stair up to it
    slab(b, rect(-70.0, -50.0, 100.0, 116.0), y + 8.0, 1.0, WOOD, studs=True)
    for (px, pz) in ((-69.0, 101.0), (-51.0, 101.0), (-69.0, 115.0), (-51.0, 115.0)):
        b.box([px, y + 3.5, pz], [1.2, 7.0, 1.2], WOOD_DARK)
    flight(b, "z", 86.0, 100.0, -66.0, -58.0, y, y + 8.0, WOOD_DARK, fill=y)
    post_sign(b, -78.0, z0 - 2.0, y, 3.0, 18.0, 2.2,
              sign_decal("MEI MEI IS SLEEPING", "#f2f2f2", "#1b1b1b", 8.2), "z-", "#f2f2f2")


# ================================================================ kiosks
def _kiosks(b: Area, s: Surfaces) -> None:
    # the ice cream kiosk with a cone on its roof
    ice = rect(-76.0, -64.0, -186.0, -174.0)
    s.reserve(ice)
    building(b, ice, 0.0, 8.0, "#f2e8f2", roof_colour="#e890b0",
             doors={"z-": [(-74.0, -66.0, 6.6)]}, windows={"z+": [(-74.0, -66.0, 3.4, 6.4)]},
             glass=True, lights=WARM)
    threshold(b, ice, "z-", (-74.0, -66.0))
    b.cone([-70.0, 12.2, -180.0], [4.0, 6.0, 4.0], "#d8a050", r=[math.pi, 0, 0])
    b.sphere([-70.0, 15.6, -180.0], [4.6, 3.6, 4.6], "#f2c8d8")
    barrel_spot(b, -60.0, 0.0, -170.0)
    # a popcorn cart and a snack stand up on the terrace
    b.box([70.0, 2.7, -150.0], [6.0, 4.8, 4.0], "#c43a32", studs=True)
    b.box([70.0, 5.9, -150.0], [5.0, 1.6, 3.4], "#f2e0a0", material="glass", alpha=0.7)
    stand = rect(120.0, 136.0, 88.0, 100.0)
    building(b, stand, T1_TOP, 8.0, "#f2e8d2", roof_colour="#3a7a4a",
             doors={"z-": [(124.0, 132.0, T1_TOP + 6.6)]}, glass=True, lights=WARM)
    threshold(b, stand, "z-", (124.0, 132.0), y0=T1_TOP)
    supply_ammo(b, 128.0, T1_TOP + FLOOR, 95.6, "z-")
    barrel_spot(b, 140.0, T1_TOP, 94.0)
    # benches and lamps along the walks
    for (x, z, along) in ((-30.0, -170.0, "x"), (30.0, -170.0, "x"), (-123.0, -60.0, "z"),
                          (123.0, -80.0, "z"), (-60.0, 37.0, "x"), (60.0, 37.0, "x"),
                          (-80.0, 65.0, "x"), (80.0, 65.0, "x")):
        bench(b, x, z, along, WOOD_LIGHT, y=ground_y(x, z))
    for (x, z) in ((-40.0, -150.0), (40.0, -150.0), (-80.0, -110.0), (80.0, -110.0),
                   (-70.0, 32.0), (70.0, 32.0), (-120.0, 0.0), (120.0, -10.0),
                   (-120.0, 120.0), (130.0, 120.0), (0.0, 120.0), (-40.0, 66.0),
                   (40.0, 66.0)):
        lamp_post(b, x, z, h=14.0, light=WARM, y=ground_y(x, z))


# ================================================================ knolls
def _knolls(b: Area, s: Surfaces, rng: random.Random) -> None:
    """The lawns are landscaped: knolls with trees on them in the open
    ground, and a berm along each side of the zoo."""
    for (cx, cz, rx, rz, levels) in ((-150.0, -226.0, 26.0, 18.0, 3), (160.0, -228.0, 28.0, 16.0, 3),
                                     (-72.0, -6.0, 13.0, 22.0, 2), (76.0, -26.0, 12.0, 10.0, 2),
                                     (-250.0, -170.0, 16.0, 30.0, 2)):
        s.reserve(rect(cx - rx, cx + rx, cz - rz, cz + rz))
        top = mound(b, cx, cz, rx, rz, levels, 1.4, ["#5f8040", "#557636", "#5f8040"])
        tree(b, cx + rng.uniform(-3.0, 3.0), cz + rng.uniform(-3.0, 3.0), top,
             rng.uniform(1.1, 1.5), "#7a5335", "#3f8a3a")
    for x0, x1 in ((-276.0, -244.0), (256.0, 276.0)):
        s.reserve(rect(x0, x1, -100.0, 40.0))
        ridge(b, x0, x1, -100.0, 40.0, 3, 1.4, ["#5f8040", "#557636", "#5f8040"], inset=4.0,
              inset_x=4.0)
        for z in (-80.0, -40.0, 0.0, 26.0):
            pine(b, (x0 + x1) / 2.0, z, 4.2, rng.uniform(1.3, 1.7))
    mound(b, 220.0, 100.0, 34.0, 22.0, 3, 1.4, ["#6a8a44", "#5f8040", "#6a8a44"], y0=T1_TOP)
    tree(b, 220.0, 100.0, T1_TOP + 4.2, 1.4, "#7a5335", "#3f8a3a")


# =============================================================== gardens
def _gardens(b: Area, rng: random.Random) -> None:
    """Trees along the walks, planters, the topiary by the gate, the little
    tour train parked on the plaza, picnic tables, a rise on the savannah."""
    for (x, z) in ((-60.0, -230.0), (-60.0, -200.0), (60.0, -190.0), (-100.0, -140.0),
                   (100.0, -130.0), (-140.0, -20.0), (140.0, 60.0 - 0.0), (-150.0, 50.0),
                   (-30.0, 52.0), (30.0, 52.0), (-250.0, -40.0), (260.0, -60.0),
                   (-180.0, -230.0), (220.0, -240.0)):
        tree(b, x, z, ground_y(x, z), rng.uniform(1.0, 1.4), "#7a5335", "#3f8a3a")
    for (x, z) in ((-200.0, 100.0), (-160.0, 90.0), (200.0, 80.0), (240.0, 110.0),
                   (-240.0, 140.0), (-110.0, 150.0), (120.0, 150.0)):
        tree(b, x, z, T1_TOP, rng.uniform(1.1, 1.5), "#7a5335", "#3f8a3a")
    # planters round the vet hospital's doors and the flamingos
    for (x, z, w, d) in ((-20.0, 24.0, 8.0, 3.0), (20.0, 24.0, 8.0, 3.0),
                         (-20.0, -32.0, 8.0, 3.0), (20.0, -32.0, 8.0, 3.0),
                         (-36.0, -218.0, 3.0, 16.0), (36.0, -218.0, 3.0, 16.0)):
        y = ground_y(x, z)
        b.box([x, y + 0.8, z], [w, 1.6, d], "#a89a82", studs=True)
        for k in range(int(max(w, d) // 2.0)):
            fx = x - w / 2.0 + 1.0 + (k * 2.0 if w > d else 0.0)
            fz = z - d / 2.0 + 1.0 + (k * 2.0 if d >= w else 0.0)
            b.box([fx, y + 2.0, fz], [1.2, 0.8, 1.2], ["#e8503a", "#f2c83a", "#e890b0",
                                                    "#9a6ae8"][k % 4])
    # topiary animals either side of the gate: an elephant and a giraffe
    hedge = "#3a6a2a"
    ty = ground_y(-60.0, -244.0)
    b.box([-62.0, ty + 3.5, -244.0], [10.0, 5.0, 5.0], hedge, studs=True)
    for dx in (-3.5, 3.5):
        for dz in (-1.6, 1.6):
            b.box([-62.0 + dx, ty + 0.5, -244.0 + dz], [1.6, 1.0, 1.4], hedge)
    b.box([-67.6, ty + 4.2, -244.0], [2.0, 4.0, 3.6], hedge)
    b.box([-68.4, ty + 1.6, -244.0], [1.2, 1.6 + 1.2, 1.2], hedge)
    b.box([62.0, ty + 3.0, -244.0], [6.0, 4.0, 3.0], hedge, studs=True)
    for dx in (-2.2, 2.2):
        b.box([62.0 + dx, ty + 0.5, -244.0], [1.2, 1.0, 1.2], hedge)
    b.box([64.4, ty + 8.0, -244.0], [1.4, 6.0, 1.4], hedge)
    b.box([65.6, ty + 11.6, -244.0], [3.0, 1.6, 1.6], hedge)
    # the tour train, parked on the plaza: an engine and two open cars
    ty = ground_y(0.0, -170.0)
    b.box([-14.0, ty + 3.0, -170.0], [8.0, 6.0, 6.0], "#3a7a4a", studs=True)
    b.box([-14.0, ty + 7.0, -170.0], [8.4, 0.6, 6.4], "#f2a868")
    b.cyl([-17.0, ty + 8.6, -170.0], [1.6, 2.6, 1.6], "#2a2d31")
    for k, x in enumerate((-2.0, 12.0)):
        b.box([x, ty + 1.6, -170.0], [12.0, 1.0, 6.0], "#f2a868", studs=True)
        b.box([x, ty + 3.0, -167.3], [12.0, 1.8, 0.6], "#f2a868")
        b.box([x, ty + 3.0, -172.7], [12.0, 1.8, 0.6], "#f2a868")
        b.box([x, ty + 2.8, -170.0], [1.6, 1.4, 4.8], "#c43a32")
        b.box([x, ty + 0.55, -170.0], [10.0, 1.1, 4.0], "#2a2d31")
    b.box([-14.0, ty + 0.55, -170.0], [6.0, 1.1, 5.0], "#2a2d31")
    # picnic tables by the snack stand on the terrace
    for (x, z) in ((100.0, 108.0), (112.0, 118.0), (126.0, 112.0)):
        b.box([x, T1_TOP + 2.0, z], [8.0, 0.6, 4.0], WOOD_LIGHT, studs=True)
        b.box([x, T1_TOP + 0.85, z], [1.0, 1.7, 3.0], WOOD_DARK)
        for dz in (-3.4, 3.4):
            b.box([x, T1_TOP + 0.9, z + dz], [8.0, 0.4, 1.4], WOOD_LIGHT)
            b.box([x, T1_TOP + 0.35, z + dz], [1.0, 0.7, 1.0], WOOD_DARK)
    # a rise in the savannah's north-east corner, rock on top
    tier_stack(b, [[rect(70.0, 126.0, 222.0, 276.0)], [rect(80.0, 120.0, 232.0, 272.0)],
                   [rect(92.0, 112.0, 244.0, 266.0)]], T2_TOP, [1.6, 1.6, 1.6],
               ["#7a9a48", "#6a8a40", "#7a9a48"])
    b.sphere([102.0, T2_TOP + 4.8 + 1.4, 255.0], [6.0, 3.0, 5.0], ROCK)


# ================================================================ paths
def _paths(b: Area, s: Surfaces) -> None:
    """The walks, laid last round everything reserved; the terrace's are
    slabs on the terrace."""
    for w in WALKS:
        s.lay(w, 0.3, PAVING, studs=True)
    for w in TERRACE_WALKS:
        slab(b, w, T1_TOP + 0.3, 0.3, PAVING_DARK, studs=True)


# ================================================================== rigs
def _rigs(b: Area) -> None:
    y1, y2 = T1_TOP, T2_TOP
    b.rig("giraffe", -60.0, y2, 210.0, 0.0, area=[-120.0, 120.0, 172.0, 224.0], seed=1)
    b.rig("giraffe", 40.0, y2, 236.0, 0.0, area=[-110.0, 60.0, 184.0, 270.0], seed=2,
          scale=0.85)
    b.rig("elephant", 170.0, 0.4, 16.0, 0.0, area=[136.0, 200.0, 4.0, 36.0], seed=1)
    b.rig("elephant", 220.0, 0.4, 20.0, 0.0, area=[150.0, 228.0, 2.0, 30.0], seed=3,
          scale=0.7)
    b.rig("big_cat", CAT_C[0], y1 + 16.0, CAT_C[1], 0.0, r=9.0, seed=1, mane=True)
    b.rig("big_cat", CAT_C[0], y1 + 8.0, CAT_C[1], 0.0, r=28.0, seed=2, mane=False)
    b.rig("flamingos", 0.0, -1.6, -218.0, 0.0, n=9, area=[-26.0, 26.0, -224.0, -212.0])
    b.rig("penguins", -175.0, 0.0, -152.0, 0.0, n=8, pool=list(PEN_POOL),
          rocks=[[-207.0, 3.0, -150.0], [-178.0, 2.6, -130.0], [-144.0, 3.4, -140.0],
                 [-208.0, 6.0, -146.0], [-178.0, 5.4, -130.0]])
    b.rig("sea_lion", 0.0, -9.0 + 3.8 + 1.4, -82.0, math.pi)
    b.rig("aviary_birds", -206.0, y1 + 14.0, 206.0, 0.0, n=14, r=40.0)
    b.rig("waterfall", -164.0, y1 + 10.0, 243.4, math.pi, w=12.0, h=9.6)
    b.rig("crocodile", -170.0, -1.0, -6.0, 0.0, area=list(CROC))
    b.rig("python", -142.0, FLOOR + 1.0, 16.0, 0.0)
    b.rig("gorilla", 41.0, y1, 98.0, 0.0)
    b.rig("panda", -60.0, y1 + 8.0, 108.0, 0.4)
    b.rig("goats", 223.0, 6.0, -129.0, 0.0, n=4, steps=[[212.0, 2.0, -144.0],
                                                       [216.0, 4.0, -130.0],
                                                       [223.0, 6.0, -129.0],
                                                       [236.0, 2.0, -116.0]])
    b.rig("ducks", 136.0, -0.6, -129.0, 0.0, n=5, area=list(DUCKS))
    b.rig("beacon", 12.0, DECK + 7.6, 140.0, 0.0, colour="#ff8a2a")


# ================================================================ spawns
def _zombie_spawns(b: Area) -> None:
    pts = [
        # the car park and the road along the front
        (-250, -270, ""), (-170, -276, ""), (-40, -276, ""), (60, -276, ""), (180, -276, ""),
        (262, -270, ""),
        # the service road along the back, and the woods each side
        (-270, 100, ""), (-270, -60, ""),
        (-270, -220, ""), (270, -60, ""), (270, 100, ""), (270, -220, ""),
        # the farm's field and the service gate
        (148, -240, ""), (230, -230, ""),
    ]
    for x, z, tag in pts:
        b.zombie_spawn(float(x), float(z), tag)
    for x, z in ((216.0, 170.0), (216.0, 193.0)):
        b.zombie_spawn(x, z, "den", y=T1_TOP)
    for x, z in ((162.0, 200.0), (270.0, 200.0), (16.0, 98.0)):
        b.zombie_spawn(x, z, "moat", y=0.0)
    for x, z in ((-190.0, -150.0), (-160.0, -144.0)):
        b.zombie_spawn(x, z, "water", y=-8.0)
    b.zombie_spawn(-180.0, -14.0, "water", y=-4.0)
    b.zombie_spawn(-240.0, 250.0, "aviary", y=T1_TOP)
    for x in (-120.0, 0.0, 120.0):
        b.zombie_spawn(x, 272.0, "", y=T2_TOP if abs(x) < 125.0 else T1_TOP)
