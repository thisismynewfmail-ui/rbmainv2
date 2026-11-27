"""St. Bride's Mount -- the tidal abbey, the night the tide came in over the causeway.

Layout (north is +z: the sea to the north, the mainland to the south)::

   z +280 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ the open sands, the sea ~~~~~~~~~~~~~~~~~~~~~
          ST. BRIDE'S ROCK            the north strand
          (the beacon)                THE ABBEY on its terrace: the church and its
          the chapel                  spire, the cloister, the great wheel, the abbot's
                                      lodging -- the great organ (the lure)
                                      THE UPPER VILLAGE: the cemetery, the parish church
                                      THE VILLAGE: the inn (the safe room), the omelette
                                      house, the souvenir shop
                                      THE RAMPARTS, the King's Gate
   z  -48 ================================ the causeway ==============================
          THE SANDS: channels, the stranded coach, the wreck, the sandbanks, the tide
   z -190 ----- the dyke -- THE SALT MEADOW (the sheep) -- THE CAR PARK -- the kiosk -----
   z -280

Everybody deploys in the Pilgrim's Rest, the inn at the top of the gate stair.

What makes it this place:

* **Up.**  The mount is a stack of terraces -- the strand inside the
  ramparts, the village, the upper village, the abbey terrace -- joined by
  stairs: the Grand Rue from the gate, the Grand Degre up to the abbey,
  back stairs round the far side.  Every level looks down on the one below.
* **The sands.**  All round, the flats: channels to wade, sandbanks, a
  coach that tried the causeway too late, a fishing boat on its side; and
  the tide, coming in and going out over them.
* **The lure.**  The great organ in the abbey church: play it, and the
  toccata rolls out over the bay -- and everything out on the sands turns
  and comes up the mount.
* **The great wheel.**  The monks' treadwheel, that hauled the abbey's
  stores up the rock, still turning.  Somebody is still walking it.
"""
from __future__ import annotations

import math
import random
from typing import List, Tuple

from .kit import (
    ASPHALT, FLOOR, HAZARD, LINE_WHITE, WARM, WOOD, WOOD_DARK, WOOD_LIGHT, Area, barrel_spot,
    boundary, boat, building, car, carve, crenels, deploy_pad, flight, gable, lamp_post, plate,
    post_sign, rect, room_walls, sign_decal, slab, supply_ammo, supply_med, threshold, wall_sign)
from ..relay.kit import mound, pine, tree

Rect = Tuple[float, float, float, float]

HALF = 280.0
SKY = {"top": "#0a1018", "horizon": "#3a4a58", "sun": [-0.4, 0.3, 0.8],
       "clouds": 0.6, "tint": "#b8c8d0"}
AMBIENT = "#4a5a66"

SAND = "#c8b48a"
SAND_WET = "#a8946a"
MEADOW = "#4a6a3a"
GRANITE = "#8a8a84"
GRANITE_DARK = "#6a6a66"
COBBLE = "#9a9488"
STONE = "#a49c8c"
SLATE = "#3a4048"
CREAM = "#e8e0cc"

MEADOW_Y = 2.0
DYKE_Z = -190.0
CAUSEWAY = rect(-8.0, 8.0, DYKE_Z, -48.0)
CAUSEWAY_Y = 2.0
T0 = rect(-110.0, 110.0, -48.0, 164.0)
T0_Y = 4.0
T1 = rect(-92.0, 92.0, -30.0, 150.0)
T1_Y = 10.0
T2 = rect(-70.0, 70.0, 10.0, 136.0)
T2_Y = 17.0
T3 = rect(-46.0, 46.0, 30.0, 124.0)
T3_Y = 24.0
RAMPART_Y = 12.0
INN = rect(-44.0, 24.0, -30.0, 4.0)
INN_H = 12.0
OMELETTE = rect(58.0, 88.0, -26.0, 4.0)
SHOP = rect(-88.0, -54.0, -26.0, 2.0)
PARISH = rect(48.0, 68.0, 56.0, 96.0)
CHURCH = rect(-14.0, 14.0, 52.0, 118.0)
CHURCH_H = 22.0
CLOISTER = rect(18.0, 44.0, 92.0, 122.0)
GARTH = rect(24.0, 38.0, 98.0, 116.0)
WHEEL = rect(-44.0, -22.0, 58.0, 84.0)
LODGING = rect(20.0, 44.0, 38.0, 66.0)
CHANNELS = (rect(-280.0, -130.0, 100.0, 118.0), rect(130.0, 280.0, -64.0, -46.0),
            rect(-70.0, 70.0, 200.0, 216.0))
CHANNEL_BED = -2.0
CHANNEL_WATER = -0.8
ROCK = (-190.0, 186.0)


def build(b: Area) -> None:
    rng = random.Random(0x5B21)
    b.extra.update({"weather": "mist", "accent": "#9ad8ff"})
    _ground(b)
    boundary(b, 30.0, "#2a3238", "#222a30", rng, horizon="forest")
    _mainland(b, rng)
    _causeway(b)
    _island(b)
    _ramparts(b)
    _inn(b)
    _village(b)
    _upper_village(b)
    _abbey(b)
    _cloister(b)
    _great_wheel(b)
    _lodging(b)
    _sands(b, rng)
    _rock(b)
    _details(b)
    _rigs(b)
    _zombie_spawns(b)
    for x, z, name in ((-10, -13, "the inn"), (0, -45, "the King's Gate"), (0, -120, "the causeway"),
                       (-160, -60, "the sands"), (-107, 60, "the ramparts"), (73, -11, "the omelette house"),
                       (-71, -12, "the souvenir shop"), (46, 0, "the Grand Rue"), (-58, 80, "the cemetery"),
                       (58, 50, "the parish church"), (0, 40, "the abbey"), (31, 107, "the cloister"),
                       (-33, 71, "the great wheel"), (0, 104, "the organ"), (32, 52, "the abbot's lodging"),
                       (-190, 186, "the beacon rock"), (200, -55, "the stranded coach"), (150, 120, "the wreck"),
                       (0, -240, "the car park"), (-180, -235, "the salt meadow"), (0, 157, "the north strand")):
        b.landmark(float(x), float(z), name)
    b.camera(-60.0, 34.0, -110.0, 0.0, 30.0, 60.0)
    b.camera(0.0, 30.0, 20.0, 0.0, 34.0, 90.0)
    b.camera(-140.0, 14.0, 60.0, -30.0, 24.0, 72.0)
    b.camera(60.0, 16.0, -70.0, 10.0, 12.0, -10.0)


# ================================================================ helpers
def _house(b: Area, r: Rect, y0: float, height: float, colour: str, door_side: str,
           door: Tuple[float, float], windows: List[Tuple[float, float]] = ()) -> None:
    """A tall narrow village house on a terrace: slate roof stepped up to a
    ridge along its length, a door onto the street, windows above it."""
    x0, x1, z0, z1 = r
    win_side = door_side
    building(b, r, y0, height, colour, roof_colour=SLATE, floor_colour="#7a6a58",
             doors={door_side: [(door[0], door[1], y0 + 7.0)]},
             windows={win_side: [(a, c, y0 + 3.0, y0 + 6.5) for a, c in windows]},
             glass=True, lights=WARM)
    threshold(b, r, door_side, door, y0=y0)
    along = "x" if x1 - x0 >= z1 - z0 else "z"
    gable(b, r, y0 + height + 1.2, SLATE, along, tiers=3, rise=1.6, overhang=0.6)


def _coach(b: Area, x: float, z: float, y: float, colour: str, label: str) -> None:
    """A tour coach along x: chassis, the body, the window band, the name."""
    b.box([x, y + 0.7, z], [30.0, 1.4, 6.6], "#22262b")
    b.box([x, y + 1.4 + 3.0, z], [32.0, 6.0, 7.6], colour, studs=True)
    for side in (-1, 1):
        b.box([x + 1.0, y + 5.2, z + side * 3.86], [26.0, 1.8, 0.12], "#1f2a33")
        b.box([x, y + 3.0, z + side * 3.86], [16.0, 1.0, 0.12], colour,
              decal=sign_decal(label, colour, "#1b1b1b", 16.0))


# ================================================================ ground
def _ground(b: Area) -> None:
    """The sands at y = 0 everywhere but the channels; the mainland a
    grass bank two up behind the dyke."""
    h = b.half + b.margin
    meadow = rect(-b.half, b.half, -b.half, DYKE_Z)
    for r in CHANNELS:
        slab(b, r, CHANNEL_BED, 6.0 + CHANNEL_BED, SAND_WET, studs=True)
        b.water((r[0] + r[1]) / 2.0, (r[2] + r[3]) / 2.0, r[1] - r[0], r[3] - r[2], CHANNEL_WATER, "#2a4a52")
    pieces = carve(rect(-h, h, -h, h), list(CHANNELS) + [meadow])
    plate(b, pieces, 0.0, 0.6, SAND, studs=True)
    plate(b, pieces, -0.6, 5.4, "#8a7a5a")
    slab(b, meadow, MEADOW_Y, 0.6, MEADOW, studs=True, material="grass")
    slab(b, meadow, MEADOW_Y - 0.6, 7.4, "#5a4a38")


# ============================================================== mainland
def _mainland(b: Area, rng: random.Random) -> None:
    """The car park on the mainland, the shuttle waiting at its stop, the
    tide-times kiosk, the salt meadow where the sheep graze, the sign."""
    y = MEADOW_Y
    slab(b, rect(-60.0, 60.0, -268.0, -212.0), y + 0.3, 0.3, ASPHALT)
    for k in range(9):
        x = -48.0 + k * 12.0
        slab(b, rect(x - 0.3, x + 0.3, -266.0, -254.0), y + 0.35, 0.05, LINE_WHITE)
    _coach(b, -18.0, -228.0, y + 0.3, "#e8e8e8", "SHUTTLE TO THE MOUNT")
    for k, (x, z) in enumerate(((-42.0, -260.0), (-6.0, -260.0), (30.0, -260.0), (42.0, -222.0))):
        car(b, x, z, "z", ["#2a3a6a", "#8a2a24", "#e8e8e8", "#3a5a3a"][k], y=y + 0.3)
    kiosk = rect(72.0, 96.0, -252.0, -232.0)
    building(b, kiosk, y, 9.0, "#e8e0cc", roof_colour=SLATE, floor_colour="#8a8070",
             doors={"z+": [(80.0, 88.0, y + 7.0)]}, windows={"x-": [(-248.0, -236.0, y + 3.0, y + 6.5)]},
             glass=True, lights=WARM)
    threshold(b, kiosk, "z+", (80.0, 88.0), y0=y)
    wall_sign(b, 84.0, y + 8.0, -231.65, 18.0, 1.4, sign_decal("TIDE TIMES  TICKETS", "#e8e0cc", "#2a4a6a", 12.0),
              "z+", "#e8e0cc")
    supply_ammo(b, 90.0, y + FLOOR, -248.0, "x-")
    post_sign(b, 14.0, -198.0, y, 3.0, 12.0, 2.6,
              sign_decal("HIGH TIDE 21:47  CAUSEWAY CLOSED", HAZARD, "#1b1b1b", 4.6), "z-", HAZARD)
    post_sign(b, -14.0, -198.0, y, 3.0, 12.0, 2.6,
              sign_decal("THE TIDE COMES IN AS FAST AS A HORSE", CREAM, "#2a3a4a", 4.6), "z-", CREAM)
    # the salt meadow's fence along the dyke, and the meadow's sheds
    for k in range(-13, 14):
        x = k * 20.0
        if abs(x) < 14.0:
            continue
        b.box([x, y + 1.6, DYKE_Z - 3.0], [0.6, 3.2, 0.6], WOOD_DARK)
    for side in (-1, 1):
        b.box([side * 137.0, y + 1.2, DYKE_Z - 3.0], [246.0, 0.3, 0.3], WOOD)
    for (cx, cz) in ((-200.0, -250.0), (200.0, -250.0)):
        top = mound(b, cx, cz, 18.0, 12.0, 2, 1.2, [MEADOW, "#5a7a46"], y0=y)
        tree(b, cx, cz, top, rng.uniform(1.0, 1.3), WOOD, "#2a4a2a")
    barrel_spot(b, 50.0, y + 0.3, -216.0)
    barrel_spot(b, -120.0, y, -210.0)


def _causeway(b: Area) -> None:
    """The causeway across the sands: a road on a stone bank, low parapets
    with gaps, lamps on the parapet, the tide gauge beside it."""
    x0, x1, z0, z1 = CAUSEWAY
    y = CAUSEWAY_Y
    slab(b, CAUSEWAY, y, y, "#8a8478", studs=True)
    gaps = ((-160.0, -154.0), (-110.0, -104.0), (-72.0, -66.0))
    for side in (-1, 1):
        cursor = z0
        for g0, g1 in gaps + ((z1, z1),):
            if g0 - cursor > 0.5:
                b.box([side * 7.5, y + 0.6, (cursor + g0) / 2.0], [1.0, 1.2, g0 - cursor], GRANITE)
            cursor = g1
    for z in (-176.0, -136.0, -90.0, -64.0):
        for side in (-1, 1):
            lamp_post(b, side * 7.5, z, h=8.0, light="#ffe2a8", y=y + 1.2)
    # the tide gauge on the sands beside the road
    b.box([18.0, 4.0, -120.0], [0.8, 8.0, 0.8], "#e8e8e8")
    for k in range(4):
        b.box([18.0, 1.0 + k * 2.0, -120.0 - 0.45], [1.2, 0.5, 0.1], "#c8282a")
    barrel_spot(b, 14.0, 0.0, -100.0)


# ================================================================ island
def _island(b: Area) -> None:
    """The rock in terraces: the strand inside the ramparts, the village,
    the upper village, the abbey terrace -- each a level of cobbles on the
    one below -- and the stairs between them."""
    slab(b, T0, T0_Y, T0_Y, GRANITE_DARK, studs=True)
    slab(b, T1, T1_Y, T1_Y - T0_Y, COBBLE, studs=True)
    slab(b, T2, T2_Y, T2_Y - T1_Y, COBBLE, studs=True)
    slab(b, T3, T3_Y, T3_Y - T2_Y, STONE, studs=True)
    # the gate stair up into the village; the Grand Rue on to the upper
    # village; the Grand Degre up to the abbey; and the back ways round
    flight(b, "z", -42.0, T1[2], -8.0, 8.0, T0_Y, T1_Y, GRANITE, fill=T0_Y)
    flight(b, "z", -6.0, T2[2], 40.0, 52.0, T1_Y, T2_Y, GRANITE, fill=T1_Y)
    flight(b, "x", -86.0, T2[0], 46.0, 56.0, T1_Y, T2_Y, GRANITE, fill=T1_Y)
    flight(b, "z", 158.0, T1[3], -8.0, 8.0, T0_Y, T1_Y, GRANITE, fill=T0_Y)
    flight(b, "z", 14.0, T3[2], -6.0, 6.0, T2_Y, T3_Y, STONE, fill=T2_Y)
    flight(b, "z", 134.0, T3[3], -6.0, 6.0, T2_Y, T3_Y, STONE, fill=T2_Y)
    # off the rock onto the sands: the north strand, and the posterns
    flight(b, "z", 172.0, T0[3], -40.0, -30.0, 0.0, T0_Y, GRANITE_DARK, fill=0.0)
    flight(b, "x", -118.0, T0[0], 38.0, 46.0, 0.0, T0_Y, GRANITE_DARK, fill=0.0)
    flight(b, "x", 118.0, T0[1], 38.0, 46.0, 0.0, T0_Y, GRANITE_DARK, fill=0.0)
    # balustrades along the upper edges, with the stairheads left open
    for (x0, x1) in ((-70.0, 40.0), (52.0, 70.0)):
        b.box([(x0 + x1) / 2.0, T2_Y + 0.6, T2[2] + 0.4], [x1 - x0, 1.2, 0.8], STONE)
    for (x0, x1) in ((-46.0, -6.0), (6.0, 46.0)):
        b.box([(x0 + x1) / 2.0, T3_Y + 0.6, T3[2] + 0.4], [x1 - x0, 1.2, 0.8], STONE)
    for (z0, z1) in ((30.8, 58.0), (84.0, 124.0)):
        b.box([T3[0] + 0.4, T3_Y + 0.6, (z0 + z1) / 2.0], [0.8, 1.2, z1 - z0], STONE)
    barrel_spot(b, 30.0, T0_Y, -36.0)
    barrel_spot(b, -30.0, T0_Y, 156.0)
    barrel_spot(b, 30.0, T2_Y, 14.0)
    barrel_spot(b, -30.0, T3_Y, 36.0)


def _ramparts(b: Area) -> None:
    """The walls round the foot of the rock: thick enough to walk along,
    merlons on the seaward side, the King's Gate in the south wall between
    its towers, posterns east and west, stairs up from inside."""
    y0, y1 = T0_Y, RAMPART_Y
    for r in (rect(-110.0, -8.0, -48.0, -42.0), rect(8.0, 110.0, -48.0, -42.0),
              rect(-110.0, -104.0, -42.0, 38.0), rect(-110.0, -104.0, 46.0, 164.0),
              rect(104.0, 110.0, -42.0, 38.0), rect(104.0, 110.0, 46.0, 164.0)):
        slab(b, r, y1, y1 - y0, GRANITE)
    slab(b, rect(-8.0, 8.0, -48.0, -42.0), y1, 1.2, GRANITE)
    for (lo, hi) in ((-110.0, -8.0), (8.0, 110.0)):
        crenels(b, "x", -47.4, lo, hi, y1, GRANITE, every=6.0, size=3.0, height=2.0, thickness=1.2)
    for at in (-109.4, 109.4):
        for (lo, hi) in ((-42.0, 38.0), (46.0, 164.0)):
            crenels(b, "z", at, lo, hi, y1, GRANITE, every=6.0, size=3.0, height=2.0, thickness=1.2)
    # the gate towers either side of the causeway's end, out on the sands
    for (x0, x1) in ((-20.0, -8.0), (8.0, 20.0)):
        tower = rect(x0, x1, -58.0, -48.0)
        slab(b, tower, 18.0, 18.0, GRANITE, studs=True)
        crenels(b, "x", -57.4, x0, x1, 18.0, GRANITE, every=4.0, size=2.0, height=2.0, thickness=1.2)
    wall_sign(b, 0.0, y1 - 0.6, -48.35, 6.0, 1.2, sign_decal("THE KING'S GATE", GRANITE, "#1a1a1a", 5.0), "z-", GRANITE)
    for k in range(5):
        b.box([-6.0 + k * 3.0, 10.2, -45.0], [0.4, 1.2, 0.4], "#3a3a3a")
    b.box([0.0, 10.65, -45.0], [12.4, 0.3, 0.4], "#3a3a3a")
    # stairs up onto the wall from the lower street
    flight(b, "x", 20.0, 44.0, -42.0, -38.0, T0_Y, y1, GRANITE_DARK, fill=T0_Y)
    flight(b, "x", -20.0, -44.0, -42.0, -38.0, T0_Y, y1, GRANITE_DARK, fill=T0_Y)
    supply_ammo(b, -80.0, y1, -45.0, "z+")


# ================================================================ village
def _inn(b: Area) -> None:
    """The Pilgrim's Rest, at the top of the gate stair: the taproom with
    the fire, the bar, the coats on their pegs -- the safe room."""
    x0, x1, z0, z1 = INN
    y = T1_Y
    building(b, INN, y, INN_H, CREAM, roof_colour=SLATE, floor_colour="#7a5a3a",
             doors={"z-": [(-8.0, 8.0, y + 8.0)], "x+": [(-20.0, -12.0, y + 8.0)]},
             windows={"z-": [(-38.0, -16.0, y + 3.0, y + 7.0), (12.0, 20.0, y + 3.0, y + 7.0)],
                      "x-": [(-24.0, -8.0, y + 3.0, y + 7.0)],
                      "z+": [(-36.0, -20.0, y + 3.0, y + 7.0), (0.0, 16.0, y + 3.0, y + 7.0)]},
             glass=True, lights=WARM)
    threshold(b, INN, "z-", (-8.0, 8.0), y0=y)
    threshold(b, INN, "x+", (-20.0, -12.0), y0=y)
    gable(b, INN, y + INN_H + 1.2, SLATE, "x", tiers=3, rise=1.6, overhang=0.8)
    wall_sign(b, -26.0, y + 9.6, z0 - 0.35, 14.0, 1.6, sign_decal("THE PILGRIM'S REST", CREAM, "#5a2a1a", 8.8), "z-",
              CREAM)
    floor = y + FLOOR
    for z in (-20.0, -6.0):
        for k in range(8):
            x = -37.0 + k * 8.0
            deploy_pad(b, x, z, floor, "#9ad8ff", 4.8)
            b.safe_spawn(x, floor + 0.6, z, 0.0)
    # the bar along the back wall, the hearth in the west wall
    b.box([-12.0, floor + 1.6, 0.4], [22.0, 3.2, 3.2], WOOD_DARK)
    b.box([-12.0, floor + 3.2 + 0.15, 0.3], [22.4, 0.3, 3.4], WOOD_LIGHT)
    b.box([x0 + 3.0, floor + 2.4, -26.0], [2.0, 4.8, 3.0], "#5a5a56")
    b.box([x0 + 2.6, floor + 5.6, -26.0], [1.2, 1.6, 4.0], "#4a4a46")
    supply_ammo(b, 16.0, floor, -1.0, "z-")
    supply_med(b, x0 + 4.6, floor, -2.0, "x+")


def _village(b: Area) -> None:
    """The lower village round the inn: the omelette house with its pan for
    a sign, the souvenir shop's snow globes, the street lamps."""
    y = T1_Y
    # Mother Bride's: omelettes beaten in copper bowls and cooked over a fire
    x0, x1, z0, z1 = OMELETTE
    building(b, OMELETTE, y, 10.0, "#d8c8a8", roof_colour=SLATE, floor_colour="#8a6a4a",
             doors={"x-": [(-16.0, -8.0, y + 7.5)]}, windows={"z-": [(64.0, 82.0, y + 3.0, y + 7.0)]},
             glass=True, lights=WARM)
    threshold(b, OMELETTE, "x-", (-16.0, -8.0), y0=y)
    gable(b, OMELETTE, y + 11.2, SLATE, "z", tiers=3, rise=1.6, overhang=0.6)
    wall_sign(b, x0 - 0.35, y + 8.6, -6.0, 14.0, 1.4, sign_decal("MOTHER BRIDE'S OMELETTES", "#d8c8a8", "#7a2a1a", 10.0),
              "x-", "#d8c8a8")
    b.cyl([x0 - 0.3, y + 8.6, -18.0], [3.6, 0.3, 3.6], "#b8743a", r=[0.0, 0.0, math.pi / 2.0], collide=False,
          material="metal")
    floor = y + FLOOR
    b.box([x1 - 3.0, floor + 2.0, -11.0], [2.0, 4.0, 8.0], "#5a5a56")
    b.box([x1 - 3.0, floor + 4.0 + 0.6, -11.0], [2.0, 1.2, 8.6], "#3a3a3a")
    for (tx, tz) in ((68.0, -18.0), (68.0, -4.0), (78.0, -18.0)):
        b.box([tx, floor + 1.4, tz], [4.0, 0.4, 4.0], WOOD)
        b.box([tx, floor + 0.6, tz], [1.0, 1.2, 1.0], WOOD_DARK)
    supply_ammo(b, 80.0, floor, 0.0, "z-")
    # the souvenir shop
    x0, x1, z0, z1 = SHOP
    building(b, SHOP, y, 10.0, "#c8d8e0", roof_colour=SLATE, floor_colour="#8a8a86",
             doors={"x+": [(-16.0, -8.0, y + 7.5)]}, windows={"z-": [(-82.0, -60.0, y + 3.0, y + 7.0)]},
             glass=True, lights="#fff2d8")
    threshold(b, SHOP, "x+", (-16.0, -8.0), y0=y)
    gable(b, SHOP, y + 11.2, SLATE, "z", tiers=3, rise=1.6, overhang=0.6)
    wall_sign(b, x1 + 0.35, y + 8.6, -6.0, 12.0, 1.4, sign_decal("SOUVENIRS", "#c8d8e0", "#2a4a6a", 8.6), "x+",
              "#c8d8e0")
    for k in range(3):
        b.box([-80.0 + k * 9.0, floor + 2.0, -2.0], [6.0, 4.0, 2.0], WOOD_LIGHT)
        for j in range(3):
            b.sphere([-82.0 + k * 9.0 + j * 2.0, floor + 4.0 + 0.6, -2.0], [1.2, 1.2, 1.2], "#d8f0ff",
                     material="glass", alpha=0.6)
    supply_med(b, -83.0, floor, -20.0, "x+")
    for (x, z) in ((32.0, -24.0), (-50.0, -24.0), (86.0, 60.0), (-86.0, 110.0), (60.0, 140.0)):
        lamp_post(b, x, z, h=9.0, light="#ffd8a8", y=y)


def _upper_village(b: Area) -> None:
    """The upper village: the houses along the street under the abbey wall,
    the cemetery on the west side with its calvary, the parish church of St.
    Bride's-on-the-Rock on the east."""
    y = T2_Y
    for (r, colour, door, wins) in (
            (rect(-66.0, -44.0, 18.0, 30.0), "#e8e0cc", (-58.0, -52.0), [(-64.0, -60.0), (-50.0, -46.0)]),
            (rect(-38.0, -12.0, 18.0, 30.0), "#d8c0a0", (-28.0, -22.0), [(-36.0, -30.0), (-20.0, -14.0)]),
            (rect(12.0, 34.0, 18.0, 30.0), "#c8d0c8", (20.0, 26.0), [(14.0, 18.0), (28.0, 32.0)])):
        _house(b, r, y, 11.0, colour, "z-", door, wins)
    # the cemetery
    for row in range(4):
        for k in range(5):
            x = -66.0 + row * 5.0
            z = 64.0 + k * 9.0
            b.box([x, y + 1.2, z], [0.8, 2.4, 2.2], "#9a9a94")
    b.box([-58.0, y + 0.6, 112.0], [6.0, 1.2, 6.0], STONE)
    b.box([-58.0, y + 1.2 + 0.6, 112.0], [4.0, 1.2, 4.0], STONE)
    b.box([-58.0, y + 2.4 + 4.0, 112.0], [0.8, 8.0, 0.8], STONE)
    b.box([-58.0, y + 2.4 + 6.0, 112.0], [4.0, 0.8, 0.8], STONE)
    for (x, z) in ((-50.0, 44.0), (-66.0, 96.0), (-50.0, 120.0)):
        pine(b, x, z, y, 1.0, WOOD_DARK, "#1e3a26")
    # the parish church
    x0, x1, z0, z1 = PARISH
    building(b, PARISH, y, 14.0, STONE, roof_colour=SLATE, floor_colour="#8a8070",
             doors={"z-": [(54.0, 62.0, y + 9.0)]},
             windows={"x+": [(64.0, 70.0, y + 5.0, y + 11.0), (80.0, 86.0, y + 5.0, y + 11.0)]},
             glass=True, lights="#ffd8a8")
    threshold(b, PARISH, "z-", (54.0, 62.0), y0=y)
    gable(b, PARISH, y + 15.2, SLATE, "z", tiers=3, rise=1.8, overhang=0.6)
    b.box([58.0, y + 15.2 + 5.4 + 3.0, z0 + 3.0], [3.0, 6.0, 3.0], STONE)
    b.box([58.0, y + 15.2 + 5.4 + 6.0 + 0.3, z0 + 3.0], [3.6, 0.6, 3.6], SLATE)
    floor = y + FLOOR
    for k in range(5):
        b.box([54.0, floor + 0.8, 64.0 + k * 5.0], [6.0, 1.6, 1.4], WOOD)
        b.box([63.0, floor + 0.8, 64.0 + k * 5.0], [5.0, 1.6, 1.4], WOOD)
    b.box([58.0, floor + 1.6, 92.0], [6.0, 3.2, 2.4], "#e8e2d4")
    supply_med(b, 63.0, floor, 88.0, "x-")


def _abbey(b: Area) -> None:
    """The abbey church on the top of the rock: the nave of pews, the altar,
    the great organ behind it (the lure), the stepped slate roof and the
    spire with St. Bride on top in gold."""
    x0, x1, z0, z1 = CHURCH
    y = T3_Y
    lancets = [(60.0, 66.0), (74.0, 80.0), (88.0, 94.0), (106.0, 112.0)]
    building(b, CHURCH, y, CHURCH_H, STONE, roof_colour=SLATE, floor_colour="#8a8070",
             doors={"z-": [(-4.0, 4.0, y + 12.0)], "x+": [(98.0, 104.0, y + 9.0)]},
             windows={"x-": [(a, c, y + 6.0, y + 18.0) for a, c in lancets],
                      "x+": [(a, c, y + 6.0, y + 18.0) for a, c in lancets[:3]]},
             glass=True, lights="#ffd8a8")
    threshold(b, CHURCH, "z-", (-4.0, 4.0), y0=y)
    threshold(b, CHURCH, "x+", (98.0, 104.0), y0=y)
    roof = y + CHURCH_H + 1.2
    gable(b, CHURCH, roof, SLATE, "z", tiers=3, rise=2.0, overhang=1.0)
    # the spire off the ridge, and the saint on top of it
    ridge = roof + 3 * 2.0
    b.box([0.0, ridge + 6.4, 85.0], [5.0, 12.8, 6.0], STONE)
    b.box([0.0, ridge + 12.8 + 4.0, 85.0], [3.4, 8.0, 4.0], STONE)
    b.cone([0.0, ridge + 20.8 + 4.0, 85.0], [3.4, 8.0, 3.4], SLATE)
    gold = "#e8c35a"
    b.box([0.0, ridge + 28.8 + 1.4, 85.0], [1.0, 2.8, 0.8], gold, material="metal")
    b.sphere([0.0, ridge + 28.8 + 3.2, 85.0], [0.9, 0.9, 0.9], gold, material="metal")
    b.box([0.6, ridge + 28.8 + 2.6, 85.0], [0.2, 4.0, 0.2], gold, material="metal")
    b.box([0.6, ridge + 28.8 + 4.0, 85.0], [1.2, 0.2, 0.2], gold, material="metal")
    wall_sign(b, 0.0, y + 15.0, z0 - 0.35, 10.0, 1.6, sign_decal("ABBEY OF ST. BRIDE", STONE, "#2a2a2a", 6.25), "z-", STONE)
    floor = y + FLOOR
    for k in range(8):
        z = 60.0 + k * 4.6
        for (xa, xb) in ((-11.0, -3.0), (3.0, 11.0)):
            b.box([(xa + xb) / 2.0, floor + 0.8, z], [xb - xa, 1.6, 1.4], WOOD)
            b.box([(xa + xb) / 2.0, floor + 1.6 + 0.8, z + 0.5], [xb - xa, 1.6, 0.4], WOOD_DARK)
    b.box([0.0, floor + 1.6, 101.0], [6.0, 3.2, 2.4], "#e8e2d4")
    b.box([0.0, floor + 3.2 + 0.1, 101.0], [6.4, 0.2, 2.8], "#c8282a")
    # the organ: its case against the north wall, the pipes on it, the console
    b.box([0.0, floor + 1.5, z1 - 2.0 - 1.5], [22.0, 3.0, 3.0], WOOD_DARK)
    for k in range(11):
        h = 6.0 + (5 - abs(k - 5)) * 1.6
        b.cyl([-10.0 + k * 2.0, floor + 3.0 + h / 2.0, z1 - 2.0 - 1.5], [1.2, h, 1.2], "#c8b070", material="metal")
    b.box([0.0, floor + 1.4, 109.0], [8.0, 2.8, 3.0], WOOD_DARK)
    b.box([0.0, floor + 2.8 + 0.8, 110.2], [7.0, 1.6, 0.6], WOOD)
    b.set_lure(0.0, floor, 104.6, "the great organ", "Play the great organ", "ll_organ", (0.0, y, 85.0))
    supply_ammo(b, -8.5, floor, 108.4, "x+")
    for (x, z) in ((-30.0, 40.0), (34.0, 76.0)):
        lamp_post(b, x, z, h=9.0, light="#ffd8a8", y=y)
    b.cyl([-26.0, y + 1.2, 108.0], [4.0, 2.4, 4.0], STONE)
    b.box([-26.0, y + 4.8, 108.0], [5.0, 0.4, 0.6], WOOD_DARK)
    for side in (-1, 1):
        b.box([-26.0 + side * 2.2, y + 2.4, 108.0], [0.4, 4.8, 0.4], WOOD_DARK)


def _cloister(b: Area) -> None:
    """The cloister: a covered walk on slender columns round the garth --
    the garden in the middle, its well and its one tree."""
    x0, x1, z0, z1 = CLOISTER
    y = T3_Y
    room_walls(b, CLOISTER, 1.2, y, y + 8.0, STONE, doors={"x-": [(98.0, 104.0, y + 7.0)]})
    gx0, gx1, gz0, gz1 = GARTH
    plate(b, carve(CLOISTER, [GARTH]), y + 8.6, 0.6, SLATE)
    for k in range(5):
        x = gx0 + k * (gx1 - gx0) / 4.0
        for z in (gz0, gz1):
            b.cyl([x, y + 4.0, z], [1.0, 8.0, 1.0], "#c8c0b0")
    for k in range(1, 4):
        z = gz0 + k * (gz1 - gz0) / 4.0
        for x in (gx0, gx1):
            b.cyl([x, y + 4.0, z], [1.0, 8.0, 1.0], "#c8c0b0")
    slab(b, rect(gx0 + 1.0, gx1 - 1.0, gz0 + 1.0, gz1 - 1.0), y + 0.3, 0.3, "#3a6a32", studs=True, material="grass")
    b.cyl([31.0, y + 0.3 + 1.0, 110.0], [3.0, 2.0, 3.0], STONE)
    tree(b, 31.0, 102.0, y + 0.3, 0.8, WOOD, "#2a5a2a")


def _great_wheel(b: Area) -> None:
    """The great wheel: the monks' treadwheel, in its own stone house on the
    seaward edge of the terrace, that hauled the stores up the rock on a
    rope through the big window.  It still turns."""
    x0, x1, z0, z1 = WHEEL
    y = T3_Y
    building(b, WHEEL, y, 20.0, STONE, roof_colour=SLATE, floor_colour="#7a6a58",
             doors={"x+": [(66.0, 76.0, y + 10.0)]}, windows={"x-": [(62.0, 80.0, y + 4.0, y + 18.0)]},
             lights=WARM)
    threshold(b, WHEEL, "x+", (66.0, 76.0), y0=y)
    gable(b, WHEEL, y + 21.2, SLATE, "z", tiers=3, rise=1.6, overhang=0.6)
    floor = y + FLOOR
    # the frame: a post either side, the axle across between them, east
    # to west, so the wheel shows face on through the seaward window
    for x in (-40.0, -26.0):
        b.box([x, floor + 4.6, 71.0], [1.6, 9.2, 1.6], WOOD_DARK)
    b.box([-33.0, floor + 9.4, 71.0], [16.0, 1.2, 1.2], WOOD_DARK)
    wall_sign(b, x1 + 0.35, y + 15.0, 71.0, 10.0, 1.4, sign_decal("THE GREAT WHEEL", STONE, "#2a2a2a", 7.1), "x+", STONE)


def _lodging(b: Area) -> None:
    """The abbot's lodging: his library, his desk, the chest of the abbey's
    papers."""
    x0, x1, z0, z1 = LODGING
    y = T3_Y
    building(b, LODGING, y, 12.0, "#b8b0a0", roof_colour=SLATE, floor_colour="#6a5a48",
             doors={"x-": [(46.0, 54.0, y + 8.0)]}, windows={"z-": [(26.0, 38.0, y + 3.0, y + 8.0)]},
             glass=True, lights=WARM)
    threshold(b, LODGING, "x-", (46.0, 54.0), y0=y)
    gable(b, LODGING, y + 13.2, SLATE, "x", tiers=3, rise=1.6, overhang=0.6)
    floor = y + FLOOR
    for k in range(3):
        b.box([x1 - 3.0, floor + 3.0, z0 + 7.0 + k * 7.0], [2.0, 6.0, 5.0], WOOD_DARK)
    b.box([30.0, floor + 1.4, 58.0], [7.0, 2.8, 3.4], WOOD)
    b.box([24.0, floor + 1.0, z1 - 4.0], [5.0, 2.0, 3.0], "#5a3a2a")
    supply_med(b, 36.0, floor, z1 - 3.6, "z-")
    supply_ammo(b, 30.0, T3_Y, 34.0, "z+")


# ================================================================= sands
def _sands(b: Area, rng: random.Random) -> None:
    """The flats round the mount: sandbanks, the coach that tried the
    causeway too late and went into the channel, a fishing boat left high
    on the sand, posts of an old weir."""
    for (cx, cz, rx, rz) in ((-150.0, 30.0, 20.0, 14.0), (150.0, 40.0, 22.0, 14.0), (-100.0, -120.0, 22.0, 12.0),
                             (110.0, -130.0, 20.0, 12.0), (60.0, 250.0, 24.0, 12.0), (-220.0, -40.0, 18.0, 14.0),
                             (220.0, 160.0, 20.0, 14.0), (-120.0, 240.0, 22.0, 12.0)):
        mound(b, cx, cz, rx, rz, 2, 0.8, [SAND, SAND_WET])
    _coach(b, 200.0, -55.0, CHANNEL_BED, "#2a5a8a", "ST BRIDE TOURS")
    boat(b, 150.0, 120.0, "x", length=26.0, colour="#c83a2a", deck=4.0, cabin=True, base=0.0)
    for k in range(9):
        b.cyl([-60.0 + k * 6.0, 1.2, -170.0 + (k % 2) * 2.0], [0.8, 2.4, 0.8], WOOD_DARK)
    barrel_spot(b, 160.0, 0.0, -40.0)
    barrel_spot(b, -170.0, 0.0, 80.0)


def _rock(b: Area) -> None:
    """St. Bride's Rock, off the mount's north-west: a hump of granite with
    the beacon on it, and the little pilgrims' chapel at its foot."""
    cx, cz = ROCK
    top = mound(b, cx, cz, 24.0, 20.0, 3, 1.6, [SAND_WET, GRANITE_DARK, GRANITE], shrink=0.5)
    b.cyl([cx, top + 8.0, cz], [5.0, 16.0, 5.0], "#e8e8e2")
    b.cyl([cx, top + 16.0 + 1.6, cz], [4.0, 3.2, 4.0], "#b8d8e8", material="glass", alpha=0.5)
    b.cone([cx, top + 19.2 + 1.5, cz], [5.0, 3.0, 5.0], "#c8282a")
    chapel = rect(-160.0, -146.0, 150.0, 162.0)
    building(b, chapel, 0.0, 8.0, "#d8d0c0", roof_colour=SLATE, floor_colour="#7a6a58",
             doors={"x+": [(153.0, 159.0, 6.5)]}, lights=WARM)
    threshold(b, chapel, "x+", (153.0, 159.0))
    gable(b, chapel, 9.2, SLATE, "x", tiers=2, rise=1.6, overhang=0.6)
    b.box([-156.8, FLOOR + 1.0, 156.0], [2.0, 2.0, 4.0], "#e8e2d4")
    barrel_spot(b, -176.0, 0.0, 150.0)


def _details(b: Area) -> None:
    """Buttresses down the faces of the terraces, the houses on the
    village's east and west sides, the fish stall on the north strand, the
    abbey's hives, a rowing boat left on the sand, the quicksand signs."""
    for x in (-86.0, -74.0, -62.0, -50.0, 30.0, 46.0, 70.0, 82.0):
        b.box([x, (T0_Y + T1_Y) / 2.0, T1[2] - 0.5], [1.6, T1_Y - T0_Y, 1.0], GRANITE)
    for z in (0.0, 20.0, 60.0, 80.0, 100.0, 120.0, 140.0):
        for side in (-1, 1):
            b.box([side * (T1[1] + 0.5), (T0_Y + T1_Y) / 2.0, z], [1.0, T1_Y - T0_Y, 1.6], GRANITE)
    for x in (-64.0, -52.0, -40.0, -28.0, -16.0, 16.0, 28.0, 60.0):
        b.box([x, (T1_Y + T2_Y) / 2.0, T2[2] - 0.5], [1.6, T2_Y - T1_Y, 1.0], GRANITE)
    for z in (30.0, 70.0, 90.0, 110.0, 130.0):
        for side in (-1, 1):
            b.box([side * (T2[1] + 0.5), (T1_Y + T2_Y) / 2.0, z], [1.0, T2_Y - T1_Y, 1.6], GRANITE)
    for (r, colour, side, door, wins) in (
            (rect(72.0, 90.0, 26.0, 50.0), "#e8d8c0", "x-", (34.0, 40.0), [(28.0, 32.0), (42.0, 48.0)]),
            (rect(72.0, 90.0, 66.0, 92.0), "#d0d8d0", "x-", (76.0, 82.0), [(68.0, 74.0), (84.0, 90.0)]),
            (rect(-90.0, -72.0, 66.0, 92.0), "#e0d0b8", "x+", (76.0, 82.0), [(68.0, 74.0), (84.0, 90.0)]),
            (rect(-90.0, -72.0, 116.0, 140.0), "#d8d0c8", "x+", (125.0, 131.0), [(118.0, 123.0), (133.0, 138.0)])):
        _house(b, r, T1_Y, 10.0, colour, side, door, wins)
    # the fish stall on the north strand of the village
    for (x, z) in ((30.4, 138.4), (49.6, 138.4), (30.4, 147.6), (49.6, 147.6)):
        b.box([x, T1_Y + 3.5, z], [0.8, 7.0, 0.8], WOOD_DARK)
    slab(b, rect(30.0, 50.0, 138.0, 148.0), T1_Y + 7.6, 0.6, "#2a5a8a")
    b.box([40.0, T1_Y + 1.3, 141.0], [16.0, 2.6, 3.0], WOOD_LIGHT)
    b.box([40.0, T1_Y + 2.6 + 0.2, 141.0], [15.0, 0.4, 2.4], "#b8d8e0")
    # the abbey's hives along the north wall of the upper village
    for k in range(4):
        x = 20.0 + k * 6.0
        b.box([x, T2_Y + 1.2, 130.0], [2.0, 2.4, 2.0], "#e8d8a8")
        b.box([x, T2_Y + 2.4 + 0.2, 130.0], [2.6, 0.4, 2.6], "#8a6a3a")
    # a rowing boat left on the sand south-west of the rock
    b.box([-40.0, 0.6, -80.0], [8.0, 1.2, 3.0], "#3a5a6a")
    for dx in (-2.0, 1.5):
        b.box([-40.0 + dx, 1.4, -80.0], [0.6, 0.4, 2.6], WOOD)
    b.box([-36.4, 1.6, -80.0], [0.8, 0.8, 2.0], "#3a5a6a")
    for (x, z, facing) in ((-150.0, -10.0, "x+"), (130.0, 80.0, "x-"), (-60.0, 236.0, "z-")):
        post_sign(b, x, z, 0.0, 3.0, 8.0, 2.0, sign_decal("DANGER  QUICKSAND", HAZARD, "#1b1b1b", 4.0), facing, HAZARD)


# ================================================================ rigs
def _rigs(b: Area) -> None:
    b.rig("tide", 0.0, 0.0, 45.0, 0.0, area=[-280.0, 280.0, DYKE_Z, 280.0])
    b.rig("great_wheel", -33.0, T3_Y + FLOOR + 9.4, 71.0, 0.0, r=7.0)
    b.rig("organ_pipes", 0.0, T3_Y + FLOOR + 3.0, 114.5, 0.0, n=11)
    b.rig("abbey_windows", 0.0, T3_Y + 12.0, 0.0, 0.0,
          panes_path=[[CHURCH[0] - 0.06, T3_Y + 12.0, (a + c) / 2.0] for a, c in
                      ((60.0, 66.0), (74.0, 80.0), (88.0, 94.0), (106.0, 112.0))] +
                     [[CHURCH[1] + 0.06, T3_Y + 12.0, (a + c) / 2.0] for a, c in
                      ((60.0, 66.0), (74.0, 80.0), (88.0, 94.0))])
    b.rig("sheep", -180.0, MEADOW_Y, -235.0, 0.0, area=[-262.0, -100.0, -268.0, -200.0], n=9)
    b.rig("sheep", 180.0, MEADOW_Y, -235.0, 0.0, area=[110.0, 262.0, -268.0, -200.0], n=7)
    b.rig("gulls", 0.0, 60.0, 60.0, 0.0, n=10, r=110.0)
    b.rig("beacon", ROCK[0], 22.4, ROCK[1], 0.0, colour="#ffe8a8")
    b.rig("weathervane", 58.0, T2_Y + 15.2 + 5.4 + 6.6, PARISH[2] + 3.0, 0.0)
    for (x, y, z) in ((-7.5, CAUSEWAY_Y + 1.2 + 7.6, -90.0), (-50.0, T1_Y + 8.6, -24.0)):
        b.rig("moth_swarm", x, y, z, 0.0)


# ============================================================== spawns
def _zombie_spawns(b: Area) -> None:
    for (x, z) in ((-250.0, -150.0), (-200.0, -70.0), (-250.0, 40.0), (-232.0, 140.0), (-262.0, 250.0),
                   (-150.0, 262.0), (-60.0, 262.0), (60.0, 262.0), (150.0, 258.0), (250.0, 236.0),
                   (262.0, 120.0), (232.0, 40.0), (262.0, -110.0), (200.0, -150.0), (-130.0, -150.0),
                   (130.0, -100.0), (-140.0, 70.0), (150.0, 0.0), (-60.0, 190.0), (60.0, 190.0),
                   (-240.0, -240.0), (240.0, -240.0), (-150.0, -262.0), (150.0, -262.0), (-190.0, 186.0)):
        b.zombie_spawn(x, z, "")
    for (x, z) in ((-200.0, 109.0), (240.0, -55.0), (-40.0, 208.0), (40.0, 208.0)):
        b.zombie_spawn(x, z, "water", y=CHANNEL_BED)
