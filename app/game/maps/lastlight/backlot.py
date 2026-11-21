"""Silver Screen Studios -- the backlot, on the night of a night shoot.

Layout (north is +z)::

   z +280 ------ the hill, and the studio's name on it in letters -----------
          SOUND STAGE 7       PROP WAREHOUSE       SOUND STAGE 9
          (the moon set)      the water tower      (the castle hall)
   z +100 ================= the studio street, the tour tram ==============
          WESTERN STREET      THE COMMISSARY       NEW YORK STREET
          (false fronts,      (safe room),         (brownstones, fire
          Boot Hill)          make-up trailers     escapes, the subway set)
   z  -70 ===================== the tram loop ==============================
          THE TANK (a pirate ship, a painted sky)  THE WAR SET (trenches,
                                                   the church, the pyro)
   z -280 ======= the main gate, the guard's booth, the car park ===========

Everybody deploys in the commissary, the studio's canteen, in the middle.

What makes it this place:

* **Nothing is what it seems.**  Every building on the western street and
  New York street is a front with nothing behind it but scaffolding --
  and behind the upper windows of every front a gallery runs the length of
  the street, so the street is a shooting gallery from both sides.  The
  subway entrance on New York street goes down to a platform set with a
  train that goes nowhere.
* **Inside the stages.**  Sound stage seven is the moon: grey craters, the
  lander, a black sky; sound stage nine a castle's great hall with a
  dragon over the throne.  Both have catwalks up in the lights.
* **The tank and the war.**  A pirate ship sits in the water tank under a
  painted sky; the war set has trenches, shell holes and a ruined church.
* **Action.**  The lure is the war set's special effects: fire them and
  the pyro goes off down the whole set and the horde goes for the bangs --
  into the trenches, under the guns on the church tower.
* **The costumes.**  The infected were the cast: cowboys, knights,
  pirates, astronauts, a gorilla.
"""
from __future__ import annotations

import math
import random
from typing import List, Sequence, Tuple

from .kit import (
    ASPHALT, CONCRETE, CONCRETE_DARK, FLOOR, GLASS, LAMP, LINE_WHITE, STEEL, STEEL_DARK,
    WARM, WOOD, WOOD_DARK, WOOD_LIGHT, Area, Surfaces, barrel_spot, bench, boat, boundary,
    building, car, carve, crate, deploy_pad, flight, holed_wall, lamp_post, plate, post_sign,
    rect, room_walls, sandbags, sign_decal, slab, strip_light, supply_ammo, supply_med,
    threshold, van, wall_sign)
from ..relay.kit import board_letters, boulder, mound, ridge, tier_stack

Rect = Tuple[float, float, float, float]

HALF = 280.0
SKY = {"top": "#070a18", "horizon": "#2a2a4a", "sun": [0.4, 0.5, -0.55],
       "clouds": 0.2, "tint": "#a8a8e0"}
AMBIENT = "#5a5a78"

DIRT = "#a8865a"
GRASS = "#4a6438"
STAGE = "#c8c4b8"
STAGE_ROOF = "#5a5f66"
MOON = "#9a9a98"

WEST_Z = (10.0, 40.0)                     # the western street's dirt road
WEST_X = (-256.0, -84.0)
NY_Z = (8.0, 40.0)
NY_X = (84.0, 256.0)
STREET = (-280.0, 280.0, 96.0, 116.0)     # the studio street, west to east
LOOP = (-280.0, 280.0, -82.0, -66.0)      # the tram loop's south run
COMMISSARY = (-40.0, 40.0, -30.0, 30.0)
COMM_H = 13.0
COMM_HOLE = (22.0, 38.0, -28.0, -20.0)
STAGE7 = (-256.0, -126.0, 128.0, 248.0)
STAGE9 = (126.0, 256.0, 128.0, 248.0)
STAGE_H = 40.0
WAREHOUSE = (-46.0, 46.0, 176.0, 232.0)
TANK = (-250.0, -96.0, -214.0, -104.0)
TANK_BED = -4.0
WAR = (84.0, 256.0, -220.0, -100.0)
TRENCH = [(96.0, 244.0, -150.0, -142.0), (150.0, 158.0, -200.0, -150.0)]
TRENCH_FLOOR = -5.0
SUBWAY = (172.0, 216.0, -36.0, -8.0)      # the platform set under New York street
SUBWAY_FLOOR = -8.0
SUB_STAIR = (176.0, 188.0, -8.0, 8.0)     # where the fourth south front would be
WEST_XS = [-232.0 + k * 28.0 for k in range(5)]
NY_XS = [90.0 + k * 28.0 for k in range(6)]
BOOT_HILL = (-258.0, 50.0, 16.0, 14.0)
GATE_Z = -250.0


def build(b: Area) -> None:
    rng = random.Random(0xF11)
    b.extra.update({"weather": "dust", "accent": "#ffd84a"})
    s = Surfaces(b)
    _ground(b, s)
    boundary(b, 30.0, "#3a3a2e", "#2a2a22", rng, horizon="city")
    _hill(b)
    _commissary(b, s)
    _western(b, s, rng)
    _newyork(b, s, rng)
    _stage7(b, s)
    _stage9(b, s)
    _warehouse(b, s)
    _tank(b, s)
    _war(b, s, rng)
    _gate(b, s, rng)
    _roads(b, s)
    _lights(b)
    _rigs(b)
    _zombie_spawns(b)
    for x, z, name in ((0, 0, "the commissary"), (-170, 25, "the western street"),
                       (-240, 60, "boot hill"), (-150, 54, "the saloon"),
                       (170, 25, "new york street"), (196, -22, "the subway set"),
                       (-190, 188, "the moon set"), (190, 188, "the castle hall"),
                       (0, 204, "the prop warehouse"), (70, 160, "the water tower"),
                       (-173, -160, "the pirate ship"), (170, -170, "the war set"),
                       (230, -120, "the church"), (0, -250, "the main gate"),
                       (-150, -250, "the car park"), (0, 106, "the studio street")):
        b.landmark(float(x), float(z), name)
    b.camera(0.0, 70.0, -200.0, 0.0, 10.0, 40.0)
    b.camera(-100.0, 14.0, 25.0, -240.0, 6.0, 25.0)
    b.camera(-150.0, 30.0, 140.0, -200.0, 4.0, 200.0)
    b.camera(100.0, 30.0, -100.0, 200.0, 0.0, -180.0)


# ================================================================ ground
def _ground(b: Area, s: Surfaces) -> None:
    h = b.half + b.margin
    holes = [TANK] + TRENCH + [SUBWAY, SUB_STAIR]
    for hole in holes:
        s.reserve(hole)
    pieces = carve(rect(-h, h, -h, h), holes)
    plate(b, pieces, 0.0, 0.6, GRASS, studs=True, material="grass")
    plate(b, pieces, -0.6, 5.4, "#5a4a38")


def _roads(b: Area, s: Surfaces) -> None:
    """The asphalt, laid last round everything that stands on the ground."""
    s.lay(STREET, 0.3, ASPHALT)
    s.lay(LOOP, 0.3, ASPHALT)
    for r in (rect(-12.0, 12.0, -250.0, -82.0), rect(-12.0, 12.0, 30.0, 96.0),
              rect(-280.0, -260.0, -66.0, 96.0), rect(260.0, 280.0, -66.0, 96.0),
              rect(-12.0, 12.0, 116.0, 176.0)):
        s.lay(r, 0.3, ASPHALT)
    s.lay(rect(WEST_X[0], WEST_X[1], WEST_Z[0], WEST_Z[1]), 0.4, DIRT, studs=True)
    s.lay(rect(NY_X[0], NY_X[1], NY_Z[0], NY_Z[1]), 0.3, "#4a4e54")
    s.lay(rect(-280.0, 280.0, -280.0, -262.0), 0.3, ASPHALT)
    for x in range(-270, 280, 24):
        b.box([float(x), 0.32, 106.0], [10.0, 0.04, 0.8], "#e8c83a", collide=False)


# ================================================================= hill
def _hill(b: Area) -> None:
    """The hill behind the lot, the studio's name on it in letters as tall
    as a house, lit."""
    ridge(b, -280.0, 280.0, 254.0, 280.0, 3, 2.0, ["#4a5a38", "#40502e", "#4a5a38"],
          inset=4.0, inset_x=0.0)
    board_letters(b, 0.0, 44.0, 290.0, "HARROW STUDIOS", 13.0, "#f2f2ec", "#f2f2ec", facing="z-",
                  solid=False)
    for k in range(14):
        b.box([-74.0 + k * 11.2, 34.0, 290.4], [0.6, 8.0, 0.6], "#5a5f66", collide=False)


# ============================================================ commissary
def _commissary(b: Area, s: Surfaces) -> None:
    x0, x1, z0, z1 = COMMISSARY
    s.reserve(COMMISSARY)
    head = 10.0
    building(b, COMMISSARY, 0.0, COMM_H, "#e8d8b8", roof_colour="#7a3a2a", floor_colour="#c8b898",
             doors={"z+": [(-8.0, 8.0, head)], "z-": [(-8.0, 8.0, head)],
                    "x-": [(-6.0, 6.0, head)], "x+": [(-6.0, 6.0, head)]},
             windows={"z+": [(-36.0, -14.0, 3.6, 8.4), (14.0, 36.0, 3.6, 8.4)],
                      "z-": [(-36.0, -14.0, 3.6, 8.4)]},
             glass=True, roof_holes=[COMM_HOLE], parapet=3.0, lights=WARM)
    for side in ("z+", "z-"):
        threshold(b, COMMISSARY, side, (-8.0, 8.0))
    for side in ("x-", "x+"):
        threshold(b, COMMISSARY, side, (-6.0, 6.0))
    # the awning over the front, the sign over that
    slab(b, rect(-14.0, 14.0, z1, z1 + 6.0), 10.8, 0.6, "#c43a32")
    for x in (-13.0, 13.0):
        b.cyl([x, 5.25, z1 + 5.4], [0.7, 10.5, 0.7], "#3a3a3a", material="metal")
    wall_sign(b, 0.0, 12.2, z1 + 0.5, 26.0, 2.4,
              sign_decal("THE COMMISSARY", "#7a3a2a", "#f2e0a0", 10.8), "z+", "#7a3a2a")
    floor = FLOOR
    for z in (10.0, 0.0):
        for x in (-34.0, -25.0, -16.0, -7.0, 7.0, 16.0, 25.0, 34.0):
            deploy_pad(b, x, z, floor, "#ffd84a", 5.0)
            b.safe_spawn(x, floor + 0.6, z, 0.0)
    # the serving line, the kitchen, the stair to the roof
    b.box([-14.0, floor + 1.7, -16.0], [36.0, 3.4, 3.4], "#a8adb2", material="metal")
    b.box([-14.0, floor + 3.55, -16.0], [37.0, 0.3, 3.8], "#e8e8e8")
    b.box([-30.0, floor + 2.0, -24.0], [8.0, 4.0, 4.0], "#5a5f66", material="metal")
    b.box([-30.0, floor + 4.1, -24.0], [7.0, 0.2, 3.4], "#ff8a3a", material="neon")
    flight(b, "x", 12.0, 38.0, -28.0, -20.0, floor, COMM_H + 1.2, CONCRETE_DARK, fill=floor)
    supply_ammo(b, -24.0, floor, 24.0, "z-")
    supply_med(b, 24.0, floor, 24.0, "z-")
    roof = COMM_H + 1.2
    for (xa, xb, za, zb) in ((COMM_HOLE[0], COMM_HOLE[1], COMM_HOLE[3], COMM_HOLE[3] + 0.6),
                             (COMM_HOLE[0] - 0.6, COMM_HOLE[0], COMM_HOLE[2], COMM_HOLE[3] + 0.6)):
        b.box([(xa + xb) / 2.0, roof + 1.6, (za + zb) / 2.0], [xb - xa, 3.2, zb - za], STEEL,
              material="metal")
    supply_ammo(b, -28.0, roof, 6.0, "z-")
    # the make-up trailers and the director's chair out front
    for k, tx in enumerate((-70.0, -52.0)):
        tr = rect(tx - 6.0, tx + 6.0, -26.0, 4.0)
        s.reserve(tr)
        building(b, tr, 0.8, 8.0, "#e8e8e2", roof_colour="#8a8f94",
                 doors={"x+": [(-18.0, -10.0, 7.6)]}, windows={"x+": [(-4.0, 2.0, 4.0, 6.8)]},
                 glass=True, lights="#ffe8c8")
        threshold(b, tr, "x+", (-18.0, -10.0), y0=0.8)
        slab(b, rect(tx - 6.0, tx + 6.0, -26.0, 4.0), 0.8, 0.8, "#3a3a3a")
        wall_sign(b, tx + 6.5, 6.6, -6.0, 6.0, 1.4,
                  sign_decal(("STAR", "MAKE-UP")[k], "#f2f2f2", "#c43a32", 4.3), "x+", "#f2f2f2")
    supply_med(b, -70.0, 0.8, -20.0, "x+")
    b.box([20.0, 0.6, 44.0], [3.0, 1.2, 2.6], "#3a2a1a")
    b.box([20.0, 1.35, 44.0], [2.8, 0.3, 2.4], "#2a2a2a")
    b.box([20.0, 3.0, 45.15], [2.8, 3.0, 0.3], "#2a2a2a",
          decal=sign_decal("DIRECTOR", "#2a2a2a", "#f2f2f2", 0.93))
    barrel_spot(b, 50.0, 0.0, -20.0)


# ========================================================== false fronts
def front(b: Area, x0: float, x1: float, z: float, out: int, height: float, colour: str,
          trim: str, sign: str, door: float = 8.0, gallery: float = 9.0) -> None:
    """A false front along x at ``z`` facing ``out`` (+1: toward +z): the
    wall with a door through it and upper windows; behind it the scaffold
    and a gallery along the backs of the upper windows."""
    mid = (x0 + x1) / 2.0
    back = z - out * 10.0
    holes = [(mid - door / 2.0, mid + door / 2.0, -1.0, gallery - 0.8)]
    for k in (0, 2):
        wx = x0 + (x1 - x0) * (k + 0.5) / 3.0
        holes.append((wx - 2.6, wx + 2.6, gallery + 2.2, gallery + 6.4))
    holed_wall(b, "x", z, 1.0, x0, x1, 0.0, height, colour, holes=holes)
    # the stepped top, the trim, the name
    b.box([mid, height + 1.0, z], [(x1 - x0) * 0.6, 2.0, 0.9], colour)
    b.box([mid, height + 2.6, z], [(x1 - x0) * 0.3, 1.2, 0.8], colour)
    b.box([mid, gallery + 0.6, z + out * 0.6], [x1 - x0 - 2.0, 0.6, 0.2], trim)
    wall_sign(b, mid, height - 2.6, z + out * 0.85, (x1 - x0) * 0.7, 2.4,
              sign_decal(sign, trim, "#f2e8d2", (x1 - x0) * 0.7 / 2.4), "z+" if out > 0 else "z-",
              trim)
    # the scaffold behind: posts, the gallery, a rail along its back with a
    # gap at the west end for the stair up
    g0, g1 = sorted((z - out * 0.5, back))
    slab(b, rect(x0, x1, g0, g1), gallery, 0.8, WOOD_LIGHT, studs=True)
    for k in range(4):
        px = x0 + 1.0 + k * (x1 - x0 - 2.0) / 3.0
        b.box([px, (gallery - 0.8) / 2.0, back + out * 0.6], [0.8, gallery - 0.8, 0.8], WOOD_DARK)
        b.box([px, (gallery + height) / 2.0, back + out * 0.6], [0.6, height - gallery, 0.6],
              WOOD_DARK)
    b.box([x0 + 16.5, gallery + 1.4, back + out * 0.3], [13.0, 2.8, 0.6], WOOD_DARK)


def _western(b: Area, s: Surfaces, rng: random.Random) -> None:
    """Five fronts a side down a dirt street, Boot Hill past its west end."""
    names_n = ["SALOON", "BANK", "HOTEL", "SHERIFF", "UNDERTAKER"]
    names_s = ["BARBER", "ASSAY OFFICE", "LIVERY", "TELEGRAPH", "GUNSMITH"]
    colours = ["#a8784a", "#c89a6a", "#8a5a3a", "#b88a5a", "#9a6a4a"]
    trims = ["#5a2a1a", "#2a3a5a", "#3a5a2a", "#5a4a1a", "#1a1a1a"]
    zn, zs = WEST_Z[1] + 8.5, WEST_Z[0] - 8.5
    for k, x in enumerate(WEST_XS):
        hgt = 18.0 + (k % 3) * 2.0
        front(b, x, x + 24.0, zn, -1, hgt, colours[k], trims[k], names_n[k])
        front(b, x, x + 24.0, zs, 1, hgt - 2.0, colours[(k + 3) % 5], trims[(k + 2) % 5], names_s[k])
        s.reserve(rect(x, x + 24.0, zn - 0.5, zn + 10.0))
        s.reserve(rect(x, x + 24.0, zs - 10.0, zs + 0.5))
        # the board walks in front, and a stair up the back to the gallery
        slab(b, rect(x, x + 24.0, WEST_Z[1], zn - 0.5), 1.2, 1.2, WOOD, studs=True)
        slab(b, rect(x, x + 24.0, zs + 0.5, WEST_Z[0]), 1.2, 1.2, WOOD, studs=True)
        flight(b, "z", zn + 26.0, zn + 10.0, x + 2.0, x + 9.0, 0.0, 9.0, WOOD_DARK, fill=0.0)
        flight(b, "z", zs - 26.0, zs - 10.0, x + 2.0, x + 9.0, 0.0, 9.0, WOOD_DARK, fill=0.0)
    y0 = 0.4                                   # the dirt's top
    # hitching rails, a trough, the stagecoach
    for x in (-150.0, -122.0):
        b.box([x, y0 + 1.8, WEST_Z[0] + 3.0], [6.0, 0.4, 0.4], WOOD_DARK)
        for dx in (-2.8, 2.8):
            b.box([x + dx, y0 + 0.8, WEST_Z[0] + 3.0], [0.4, 1.6, 0.4], WOOD_DARK)
    b.box([-210.0, y0 + 1.0, WEST_Z[1] - 3.0], [8.0, 2.0, 2.4], WOOD)
    b.box([-210.0, y0 + 2.05, WEST_Z[1] - 3.0], [7.2, 0.1, 1.6], "#3a6a8a", material="glass",
          alpha=0.7, collide=False)
    sx, sz = -168.0, 26.0
    b.box([sx, y0 + 1.6, sz], [9.0, 3.2, 5.0], "#2a1a12", alpha=0.0)
    b.box([sx, y0 + 4.8, sz], [12.0, 5.6, 6.0], "#3a1a1a", studs=True)
    b.box([sx, y0 + 8.0, sz], [12.4, 0.8, 6.4], "#2a1a12")
    b.box([sx - 7.0, y0 + 6.0, sz], [2.0, 1.4, 5.0], "#5a3a22")
    for (dx, dz) in ((-4.0, -3.2), (4.0, -3.2), (-4.0, 3.2), (4.0, 3.2)):
        b.cyl([sx + dx, y0 + 1.8, sz + dz], [3.6, 0.6, 3.6], "#6a4a2a", r=[math.pi / 2.0, 0, 0],
              collide=False)
    barrel_spot(b, -190.0, y0, WEST_Z[1] - 3.0)
    barrel_spot(b, -112.0, y0, WEST_Z[0] + 3.0)
    supply_ammo(b, -224.0, 9.0, zn + 5.0, "z-")
    supply_ammo(b, -140.0, 9.0, zs - 5.0, "z+")
    supply_med(b, -168.0, 9.0, zn + 5.0, "z-")
    # Boot Hill: graves on a mound past the street's west end
    cx, cz, rx, rz = BOOT_HILL
    s.reserve(rect(cx - rx, cx + rx, cz - rz, cz + rz))
    top = mound(b, cx, cz, rx, rz, 3, 1.6, ["#6a7a4a", "#5a6a3a", "#6a7a4a"])
    for k, (gx, gz) in enumerate(((-262.0, 46.0), (-254.0, 48.0), (-258.0, 54.0))):
        b.box([gx, top + 1.6, gz], [0.5, 3.2, 0.5], WOOD_DARK)
        b.box([gx, top + 2.4, gz], [2.0, 0.5, 0.5], WOOD_DARK)
    b.cyl([cx + 6.0, top + 7.0, cz + 4.0], [1.6, 14.0, 1.6], "#4a3a2a")
    b.box([cx + 9.0, top + 12.0, cz + 4.0], [7.0, 1.0, 1.0], "#4a3a2a")


# ======================================================== New York street
def _newyork(b: Area, s: Surfaces, rng: random.Random) -> None:
    """Brownstone fronts, fire escapes up the north side, the subway
    entrance where the fourth south front would be."""
    names_n = ["DELI", "HOTEL ASTOR", "PAWN", "DINER", "THEATRE", "RECORDS"]
    names_s = ["LAUNDRY", "BANK", "PHARMACY", "", "BOOKS", "TAILOR"]
    zn, zs = NY_Z[1] + 8.5, NY_Z[0] - 8.5
    for k, x in enumerate(NY_XS):
        hgt = 26.0 + (k % 3) * 3.0
        front(b, x, x + 24.0, zn, -1, hgt, ["#8a4a3a", "#7a5a4a", "#6a3a2a"][k % 3], "#1a1a1a",
              names_n[k])
        s.reserve(rect(x, x + 24.0, zn - 0.5, zn + 10.0))
        slab(b, rect(x, x + 24.0, NY_Z[1], zn - 0.5), 0.8, 0.8, "#9a9a92", studs=True)
        flight(b, "z", zn + 26.0, zn + 10.0, x + 2.0, x + 9.0, 0.0, 9.0, "#3a3a3a", fill=0.0)
        if k == 3:
            continue
        front(b, x, x + 24.0, zs, 1, hgt - 3.0, ["#7a4a3a", "#8a6a5a"][k % 2], "#2a2a3a", names_s[k])
        s.reserve(rect(x, x + 24.0, zs - 10.0, zs + 0.5))
        slab(b, rect(x, x + 24.0, zs + 0.5, NY_Z[0]), 0.8, 0.8, "#9a9a92", studs=True)
        flight(b, "z", zs - 26.0, zs - 10.0, x + 2.0, x + 9.0, 0.0, 9.0, "#3a3a3a", fill=0.0)
    # fire escapes up three of the north fronts: two landings and a flight
    # up to each, switching back
    for x in (114.0, 170.0, 226.0):
        lz0, lz1 = NY_Z[1] + 2.0, zn - 0.5
        slab(b, rect(x - 6.0, x + 18.0, lz0, lz1), 9.0, 0.6, "#2a2a2a", studs=True)
        slab(b, rect(x - 6.0, x + 6.0, lz0, lz1), 17.0, 0.6, "#2a2a2a", studs=True)
        flight(b, "x", x - 18.0, x - 6.0, lz0, lz0 + 4.0, 0.8, 9.0, "#2a2a2a", fill=0.8)
        flight(b, "x", x + 18.0, x + 6.0, lz1 - 4.0, lz1, 9.0, 17.0, "#2a2a2a", fill=9.0)
        b.box([x + 6.0, 9.0 + 1.2, lz0 + 0.2], [24.0, 2.4, 0.4], "#2a2a2a", material="metal")
        b.box([x, 17.0 + 1.2, lz0 + 0.2], [12.0, 2.4, 0.4], "#2a2a2a", material="metal")
    # the subway entrance, down to the platform set
    sx0, sx1, sz0, sz1 = SUB_STAIR
    flight(b, "z", sz1, sz0, sx0, sx1, 0.0, SUBWAY_FLOOR, CONCRETE_DARK, fill=SUBWAY_FLOOR - 2.0)
    for x in (sx0 - 0.4, sx1 + 0.4):
        b.box([x, 1.6, (sz0 + sz1) / 2.0], [0.8, 3.2, sz1 - sz0], "#2a5a3a", material="metal")
    post_sign(b, sx1 + 4.0, 4.0, 0.0, 4.0, 8.0, 2.0,
              sign_decal("SUBWAY", "#2a5a3a", "#f2f2f2", 4.0), "z+", "#2a5a3a")
    px0, px1, pz0, pz1 = SUBWAY
    slab(b, SUBWAY, SUBWAY_FLOOR, 2.0, "#5a5a52", studs=True)
    room_walls(b, SUBWAY, 1.0, SUBWAY_FLOOR, -0.6, "#d8d8c8", doors={"z+": [(sx0, sx1, -0.6)]})
    slab(b, SUBWAY, 0.0, 0.6, "#5a5a5a")
    for k in range(3):
        strip_light(b, px0 + 8.0 + k * 13.0, (pz0 + pz1) / 2.0, -0.6, 8.0, "x", "#f2f2d8")
    b.box([(px0 + px1) / 2.0, SUBWAY_FLOOR + 3.6, pz0 + 4.0], [px1 - px0 - 4.0, 7.2, 5.0],
          "#a8adb2", material="metal")
    for k in range(4):
        b.box([px0 + 7.0 + k * 9.5, SUBWAY_FLOOR + 4.6, pz0 + 6.56], [5.0, 2.4, 0.12], "#ffe8a0",
              material="neon", collide=False)
    wall_sign(b, 204.0, SUBWAY_FLOOR + 5.8, pz1 - 1.5, 16.0, 1.6,
              sign_decal("HARROW ST  UPTOWN", "#2a2a2a", "#f2f2f2", 10.0), "z-", "#2a2a2a")
    supply_ammo(b, px1 - 6.0, SUBWAY_FLOOR, pz1 - 6.0, "x-")
    # the street: a cab, a hot dog cart, a newsstand, a phone box, hydrants
    car(b, 130.0, 24.0, "x", "#f2c81a", length=11.0, y=0.3)
    b.box([234.0, 0.3 + 2.3, 16.0], [6.0, 4.6, 3.6], "#c8c8c8", material="metal")
    b.box([234.0, 0.3 + 4.8, 16.0], [7.0, 0.4, 4.6], "#e83a3a")
    b.box([142.0, 0.8 + 4.0, NY_Z[1] + 4.0], [6.0, 8.0, 4.0], "#2a4a2a")
    b.box([102.0, 0.8 + 4.0, NY_Z[0] - 4.0], [3.0, 8.0, 3.0], "#c43a32")
    for x in (120.0, 200.0):
        b.box([x, 0.8 + 0.8, NY_Z[1] + 1.4], [1.0, 1.6, 1.0], "#c43a32")
    barrel_spot(b, 150.0, 0.3, 12.0)
    supply_med(b, 214.0, 9.0, zn + 5.0, "z-")
    supply_ammo(b, 126.0, 9.0, zn + 5.0, "z-")


# ========================================================== sound stages
def _stage(b: Area, s: Surfaces, r: Rect, west: bool, name: str, lights: str) -> float:
    """A sound stage: a hangar with a big door onto the studio street and a
    small one at the side, catwalks up in the grid and a stair up to them.
    Returns the catwalks' height."""
    x0, x1, z0, z1 = r
    s.reserve(r)
    mid = (x0 + x1) / 2.0
    side = "x+" if west else "x-"
    building(b, r, 0.0, STAGE_H, STAGE, roof_colour=STAGE_ROOF, floor_colour="#3a3a3a",
             doors={"z-": [(mid - 16.0, mid + 16.0, 24.0)], side: [(z0 + 20.0, z0 + 30.0, 9.0)]},
             lights=lights)
    threshold(b, r, "z-", (mid - 16.0, mid + 16.0))
    threshold(b, r, side, (z0 + 20.0, z0 + 30.0))
    board_letters(b, mid, 31.0, z0, name, 6.0, STAGE, "#1a1a1a", facing="z-", solid=False)
    cy = 26.0
    for cz in (z0 + 30.0, z1 - 30.0):
        slab(b, rect(x0 + 2.0, x1 - 2.0, cz - 3.0, cz + 3.0), cy, 0.6, "#3a3a3a", studs=True)
        b.box([mid, cy + 1.3, cz + 2.7], [x1 - x0 - 4.0, 2.6, 0.6], "#2a2a2a", material="metal")
    cx0, cx1 = (x0 + 2.0, x0 + 8.0) if west else (x1 - 8.0, x1 - 2.0)
    slab(b, rect(cx0, cx1, z0 + 33.0, z1 - 33.0), cy, 0.6, "#3a3a3a", studs=True)
    flight(b, "z", z0 + 3.0, z0 + 27.0, cx0, cx1, FLOOR, cy, "#3a3a3a", fill=FLOOR)
    return cy


def _stage7(b: Area, s: Surfaces) -> None:
    """The moon: grey craters, the lander, a flag, a black sky."""
    x0, x1, z0, z1 = STAGE7
    cy = _stage(b, s, STAGE7, True, "STAGE 7", "#e8e8ff")
    y = FLOOR
    slab(b, rect(x0 + 2.0, x1 - 2.0, z0 + 2.0, z1 - 2.0), y + 0.2, 0.2, MOON, studs=True)
    y += 0.2
    for (cx, cz, rr) in ((-220.0, 200.0, 12.0), (-170.0, 170.0, 9.0), (-150.0, 216.0, 7.0)):
        for k in range(8):
            a = k * math.pi / 4.0
            b.box([cx + math.cos(a) * rr, y + 0.6, cz + math.sin(a) * rr], [4.0, 1.2, 4.0], "#8a8a88",
                  studs=True)
    for (cx, cz) in ((-236.0, 160.0), (-140.0, 236.0)):
        mound(b, cx, cz, 10.0, 8.0, 2, 1.2, ["#8a8a88", "#9a9a98"], y0=y)
    # the lander: four legs, the body, a ladder of steps, the hatch on top
    lx, lz = -190.0, 196.0
    for dx in (-5.0, 5.0):
        for dz in (-5.0, 5.0):
            b.box([lx + dx, y + 2.5, lz + dz], [0.8, 5.0, 0.8], "#c8b040", material="metal")
            b.cyl([lx + dx * 1.2, y + 0.2, lz + dz * 1.2], [2.0, 0.4, 2.0], "#c8b040",
                  material="metal")
    slab(b, rect(lx - 6.0, lx + 6.0, lz - 6.0, lz + 6.0), y + 9.0, 4.0, "#d8c040", studs=True)
    b.box([lx, y + 11.0, lz], [7.0, 4.0, 7.0], "#c8c8c8", material="metal")
    for k in range(4):
        b.box([lx, y + 1.1 + k * 2.0, lz - 7.0 - k * 1.6 + 4.8], [3.0, 2.2, 1.6], "#c8c8c8")
    b.cyl([-160.0, y + 6.0, 180.0], [0.4, 12.0, 0.4], "#e8e8e8", material="metal")
    b.box([-157.0, y + 10.6, 180.0], [6.0, 3.6, 0.1], "#e8e8e8", collide=False)
    # the black sky on the back wall, the stars on it
    b.box([(x0 + x1) / 2.0, STAGE_H / 2.0, z1 - 2.3], [x1 - x0 - 4.0, STAGE_H - 4.0, 0.6], "#050508")
    for k in range(40):
        sx = x0 + 6.0 + (k * 37.3) % (x1 - x0 - 12.0)
        sy = 6.0 + (k * 13.7) % (STAGE_H - 12.0)
        b.box([sx, sy, z1 - 2.65], [0.4, 0.4, 0.1], "#f2f2ff", material="neon", collide=False)
    supply_ammo(b, -230.0, cy, z1 - 30.0 + 0.0, "z-")
    supply_med(b, -140.0, y, 150.0, "x-")


def _stage9(b: Area, s: Surfaces) -> None:
    """The castle's great hall: a dais and a throne under the dragon, a
    stair up to a gallery, the long table, torches."""
    x0, x1, z0, z1 = STAGE9
    cy = _stage(b, s, STAGE9, False, "STAGE 9", "#ffd8a0")
    y = FLOOR
    stone = "#8a8478"
    # the plywood stone walls in front of the stage's own, on two sides
    b.box([x0 + 3.0, 14.0 + y, (z0 + z1) / 2.0], [2.0, 28.0, z1 - z0 - 8.0], stone, studs=True)
    b.box([(x0 + x1) / 2.0, 14.0 + y, z1 - 3.0], [x1 - x0 - 8.0, 28.0, 2.0], stone, studs=True)
    # the dais and the throne
    tier_stack(b, [[rect(170.0, 214.0, 222.0, 240.0)], [rect(178.0, 206.0, 228.0, 240.0)]], y,
               [1.6, 1.6], ["#6a2a2a", "#7a3a3a"])
    b.box([192.0, y + 3.2 + 3.0, 236.0], [6.0, 6.0, 3.0], "#c8a040")
    b.box([192.0, y + 3.2 + 7.6, 237.2], [6.0, 3.2, 0.6], "#c8a040")
    # the gallery along the west wall, the stair up to it
    gal = rect(x0 + 4.0, x0 + 14.0, z0 + 40.0, z1 - 10.0)
    slab(b, gal, y + 12.0, 0.8, WOOD_DARK, studs=True)
    for gz in range(int(z0) + 44, int(z1) - 10, 14):
        b.box([x0 + 13.4, y + 5.6, float(gz)], [1.2, 11.2, 1.2], stone)
    b.box([x0 + 13.7, y + 13.4, (z0 + 40.0 + z1 - 10.0) / 2.0 + 6.0], [0.6, 2.8, z1 - z0 - 62.0],
          "#3a2a1a")
    flight(b, "z", z0 + 16.0, z0 + 40.0, x0 + 4.0, x0 + 12.0, y, y + 12.0, stone, fill=y)
    supply_ammo(b, x0 + 9.0, y + 12.0, z1 - 20.0, "x+")
    # the long table, the benches, the banners, the torches
    b.box([190.0, y + 2.0, 180.0], [8.0, 0.6, 40.0], WOOD, studs=True)
    for dz in (-14.0, 0.0, 14.0):
        b.box([190.0, y + 0.85, 180.0 + dz], [6.0, 1.7, 2.0], WOOD_DARK)
    for dx in (-6.0, 6.0):
        b.box([190.0 + dx, y + 1.0, 180.0], [2.0, 2.0, 40.0], WOOD_LIGHT)
    for k, bx in enumerate((150.0, 170.0, 214.0, 234.0)):
        b.box([bx, 20.0, z1 - 4.2], [6.0, 12.0, 0.4], ["#8a1a1a", "#1a3a8a"][k % 2], collide=False)
    for bz in (160.0, 190.0, 220.0):
        b.box([x0 + 4.6, y + 8.0, bz], [1.2, 1.0, 1.2], "#3a2a1a")
        b.box([x0 + 4.6, y + 9.0, bz], [0.8, 1.2, 0.8], "#ffa83a", material="neon")
    supply_med(b, 236.0, y, 150.0, "x-")
    barrel_spot(b, x1 + 6.0, 0.0, z0 + 14.0)


# ============================================================ warehouse
def _warehouse(b: Area, s: Surfaces) -> None:
    """An open-fronted shed full of the studio's giant props, and the water
    tower beside it."""
    x0, x1, z0, z1 = WAREHOUSE
    s.reserve(WAREHOUSE)
    hgt = 26.0
    slab(b, rect(x0, x1, z0, z1), FLOOR, FLOOR, "#6a6a62", studs=True)
    b.box([(x0 + x1) / 2.0, (hgt + FLOOR) / 2.0, z1 - 1.0], [x1 - x0, hgt - FLOOR, 2.0], "#8a8a7a")
    for x in (x0 + 1.0, x1 - 1.0):
        b.box([x, (hgt + FLOOR) / 2.0, (z0 + z1 - 2.0) / 2.0], [2.0, hgt - FLOOR, z1 - z0 - 2.0],
              "#8a8a7a")
    for x in (-24.0, 0.0, 24.0):
        b.box([x, (hgt + FLOOR) / 2.0, z0 + 1.0], [1.6, hgt - FLOOR, 1.6], "#5a5f66",
              material="metal")
    slab(b, rect(x0, x1, z0, z1), hgt + 1.2, 1.2, "#5a5f66", studs=True)
    y = FLOOR
    # a giant donut, a gorilla's hand, a dinosaur's skull, a rubber duck
    b.cyl([-28.0, y + 1.6, 196.0], [14.0, 3.2, 14.0], "#d8a050")
    b.cyl([-28.0, y + 3.4, 196.0], [12.0, 0.4, 12.0], "#e890b0")
    b.cyl([-28.0, y + 3.6, 196.0], [4.0, 0.8, 4.0], "#6a6a62")
    for k in range(4):
        b.box([-6.0 + k * 3.0, y + 2.0 + (k % 2), 214.0], [2.4, 4.0 + (k % 2) * 2.0, 2.4], "#2a2a2e")
    b.box([-1.5, y + 1.0, 210.0], [12.0, 2.0, 8.0], "#2a2a2e")
    b.box([24.0, y + 4.0, 200.0], [10.0, 8.0, 14.0], "#e8e0cc")
    b.box([24.0, y + 2.0, 210.0], [8.0, 3.0, 6.0], "#e8e0cc")
    for k in range(4):
        b.box([20.6 + k * 2.2, y + 0.6, 213.4], [0.8, 1.2, 0.8], "#e8e0cc")
    b.box([22.0, y + 5.4, 193.0], [2.0, 2.0, 0.2], "#1a1a1a", collide=False)
    b.box([26.0, y + 5.4, 193.0], [2.0, 2.0, 0.2], "#1a1a1a", collide=False)
    b.box([0.0, y + 4.0, 186.0], [10.0, 8.0, 8.0], "#f2d83a", studs=True)
    b.box([1.0, y + 9.6, 186.0], [6.0, 5.0, 6.0], "#f2d83a", studs=True)
    b.box([1.0, y + 9.4, 189.6], [3.0, 1.2, 1.4], "#e8783a")
    supply_ammo(b, 38.0, y, 222.0, "x-")
    barrel_spot(b, -40.0, 0.0, 168.0)
    # the water tower
    tx, tz = 70.0, 160.0
    for dx in (-6.0, 6.0):
        for dz in (-6.0, 6.0):
            b.cyl([tx + dx, 16.0, tz + dz], [1.4, 32.0, 1.4], "#5a5f66", material="metal")
    b.cyl([tx, 38.0, tz], [18.0, 12.0, 18.0], "#c8c8c0", material="metal")
    b.cone([tx, 46.0, tz], [19.0, 4.0, 19.0], "#5a5f66")
    wall_sign(b, tx, 38.0, tz - 9.4, 14.0, 3.0, sign_decal("HARROW STUDIOS", "#c8c8c0", "#1a3a6a",
                                                           4.6), "z-", "#c8c8c0")


# ================================================================ tank
def _tank(b: Area, s: Surfaces) -> None:
    """The water tank: a pirate ship in it, the painted sky behind it, the
    wave machine at the far end, a gangplank out to the ship."""
    x0, x1, z0, z1 = TANK
    slab(b, TANK, TANK_BED, 2.0, "#4a5a5a", studs=True)
    b.water((x0 + x1) / 2.0, (z0 + z1) / 2.0, x1 - x0, z1 - z0, -1.0, "#2a6a8a")
    # the painted sky along the tank's west end
    sky = rect(-262.0, -254.0, z0 - 6.0, z1 + 6.0)
    s.reserve(sky)
    b.box([(sky[0] + sky[1]) / 2.0, 20.0, (sky[2] + sky[3]) / 2.0], [sky[1] - sky[0], 40.0,
                                                                     sky[3] - sky[2]], "#5a9ad8")
    for k, (cz, cy, w) in enumerate(((-190.0, 30.0, 26.0), (-150.0, 22.0, 34.0), (-118.0, 32.0, 20.0),
                                     (-170.0, 12.0, 18.0))):
        b.box([sky[1] + 0.06, cy, cz], [0.12, 6.0, w], "#f2f4f8", collide=False)
    for k in range(3):
        b.box([sky[1] + 0.9, 12.0 + k * 10.0, (sky[2] + sky[3]) / 2.0], [1.8, 0.6, sky[3] - sky[2] - 4.0],
              "#5a5f66", material="metal")
    # the ship: a hull from the bed up, a deck, the castle at the stern, masts
    hx0, hx1, hz0, hz1 = -206.0, -146.0, -172.0, -150.0
    deck = 6.0
    b.box([(hx0 + hx1) / 2.0, (TANK_BED + deck - 1.0) / 2.0, (hz0 + hz1) / 2.0],
          [hx1 - hx0, deck - 1.0 - TANK_BED, hz1 - hz0], "#5a3a22")
    slab(b, rect(hx0, hx1, hz0, hz1), deck, 1.0, "#8a6a4a", studs=True)
    for z in (hz0 + 0.4, hz1 - 0.4):
        b.box([(hx0 + 14.0 + hx1) / 2.0, deck + 1.2, z], [hx1 - hx0 - 14.0, 2.4, 0.8], "#5a3a22")
    slab(b, rect(hx0, hx0 + 14.0, hz0, hz1), deck + 5.0, 5.0, "#6a4a2a", studs=True)
    flight(b, "x", hx0 + 24.0, hx0 + 14.0, hz0 + 7.0, hz0 + 15.0, deck, deck + 5.0, "#6a4a2a",
           fill=deck)
    b.box([hx1 + 4.0, deck - 0.5, (hz0 + hz1) / 2.0], [8.0, 1.0, 6.0], "#5a3a22")
    for mx in (-188.0, -164.0):
        b.cyl([mx, deck + 14.0, (hz0 + hz1) / 2.0], [1.2, 28.0, 1.2], "#4a3a2a")
        b.box([mx, deck + 18.0, (hz0 + hz1) / 2.0], [1.0, 12.0, 18.0], "#e8e0cc", collide=False)
        b.box([mx, deck + 25.0, (hz0 + hz1) / 2.0], [0.8, 0.8, 20.0], "#4a3a2a", collide=False)
    # the gangplank from the tank's edge to the deck
    flight(b, "z", z1, hz1, -184.0, -176.0, 0.0, deck, WOOD, fill=TANK_BED)
    supply_ammo(b, hx0 + 6.0, deck + 5.0, (hz0 + hz1) / 2.0, "x+")
    barrel_spot(b, -170.0, deck, hz0 + 4.0)
    # the wave machine at the east end, the wind machine beside the tank
    b.box([x1 - 4.0, 2.0, (z0 + z1) / 2.0], [6.0, 12.0, 30.0], "#5a5f66", material="metal")
    b.box([-80.0, 4.0, -150.0], [6.0, 8.0, 6.0], "#3a3f46", material="metal")
    for k in range(5):
        b.box([x0 + 4.0 + k * 30.0, 1.2, z1 + 1.0], [1.0, 2.4, 1.0], "#e8c83a")


# ============================================================= war set
def _war(b: Area, s: Surfaces, rng: random.Random) -> None:
    """Trenches dug into the lot, sandbags, wire, craters, a plywood tank,
    the front of a church with its tower -- and the special effects."""
    for t in TRENCH:
        slab(b, t, TRENCH_FLOOR, 2.0, "#5a4a38", studs=True)
        for k in range(int((max(t[1] - t[0], t[3] - t[2])) // 6)):
            if t[1] - t[0] > t[3] - t[2]:
                b.box([t[0] + 3.0 + k * 6.0, TRENCH_FLOOR + 0.15, (t[2] + t[3]) / 2.0],
                      [4.6, 0.3, 3.0], WOOD, collide=False)
            else:
                b.box([(t[0] + t[1]) / 2.0, TRENCH_FLOOR + 0.15, t[2] + 3.0 + k * 6.0],
                      [3.0, 0.3, 4.6], WOOD, collide=False)
    # steps out of the trenches at each end
    flight(b, "x", 108.0, 96.0, -150.0, -142.0, TRENCH_FLOOR, 0.0, "#5a4a38",
           fill=TRENCH_FLOOR)
    flight(b, "x", 232.0, 244.0, -150.0, -142.0, TRENCH_FLOOR, 0.0, "#5a4a38",
           fill=TRENCH_FLOOR)
    flight(b, "z", -188.0, -200.0, 150.0, 158.0, TRENCH_FLOOR, 0.0, "#5a4a38",
           fill=TRENCH_FLOOR)
    for (x, z) in ((110.0, -138.0), (140.0, -154.0), (190.0, -138.0), (230.0, -154.0),
                   (164.0, -170.0), (144.0, -190.0)):
        sandbags(b, x, z, 10.0, "x" if abs(z + 146.0) > 5 else "z", 3.0)
    for (cx, cz) in ((120.0, -116.0), (200.0, -196.0), (240.0, -180.0)):
        mound(b, cx, cz, 9.0, 7.0, 2, 1.0, ["#6a5a40", "#5a4a32"])
        s.reserve(rect(cx - 9.0, cx + 9.0, cz - 7.0, cz + 7.0))
    for z in (-126.0, -164.0):
        for k in range(10):
            b.box([100.0 + k * 14.0, 0.8, z], [10.0, 1.6, 0.4], "#5a5a5a", material="metal")
    # the plywood tank
    b.box([200.0, 3.0, -126.0], [18.0, 6.0, 10.0], "#5a6a3a", studs=True)
    b.box([198.0, 7.6, -126.0], [9.0, 3.2, 7.0], "#4a5a32")
    b.box([207.0, 7.8, -126.0], [12.0, 1.2, 1.2], "#4a5a32")
    # the church: a front with a door, the tower beside it, a stair up it
    cx0, cx1, cz = 210.0, 250.0, -108.0
    holed_wall(b, "x", cz, 2.0, cx0, cx1, 0.0, 22.0, "#a8a090",
               holes=[(226.0, 234.0, -1.0, 12.0), (215.0, 221.0, 14.0, 20.0), (239.0, 245.0, 14.0, 20.0)])
    b.box([230.0, 23.0, cz], [10.0, 2.0, 2.0], "#a8a090")
    tower = rect(250.0, 262.0, -116.0, -100.0)
    s.reserve(tower)
    building(b, tower, 0.0, 26.0, "#a8a090", roof_colour="#5a4a3a", t=1.6,
             doors={"z-": [(252.0, 260.0, 8.0)]}, windows={"x-": [(-112.0, -104.0, 20.0, 24.0)],
                                                         "z+": [(253.0, 259.0, 20.0, 24.0)]},
             roof=False, lights="")
    threshold(b, tower, "z-", (252.0, 260.0), t=1.6)
    slab(b, rect(251.6, 260.4, -105.0, -101.6), 18.0, 0.8, WOOD, studs=True)
    flight(b, "z", -114.4, -105.0, 251.8, 260.2, 0.0, 18.0, WOOD_DARK, fill=0.0)
    # the effects desk under its awning: the lure
    s.reserve(rect(114.0, 130.0, -100.0, -90.0))
    b.box([122.0, 1.8, -96.0], [12.0, 3.6, 4.0], "#3a3a3a", studs=True)
    for x in (114.4, 129.6):
        b.cyl([x, 5.0, -91.0], [0.6, 10.0, 0.6], "#5a5f66", material="metal")
    slab(b, rect(114.0, 130.0, -100.0, -90.0), 10.6, 0.6, "#c43a32")
    b.set_lure(122.0, 0.0, -92.4, "the special effects", "Fire the special effects", "ll_pyro",
               (170.0, TRENCH_FLOOR, -146.0))
    supply_ammo(b, 136.0, 0.0, -94.0, "x-")
    supply_med(b, 108.0, 0.0, -94.0, "x+")
    barrel_spot(b, 104.0, 0.0, -104.0)
    barrel_spot(b, 186.0, 0.0, -186.0)


# ================================================================== gate
def _gate(b: Area, s: Surfaces, rng: random.Random) -> None:
    """The studio's gate in its wall, the guard's booth, the car park, the
    executive building in its deco and the searchlights for the premiere."""
    z = GATE_Z
    for xa, xb in ((-280.0, -26.0), (26.0, 280.0)):
        b.box([(xa + xb) / 2.0, 1.6, z], [xb - xa, 3.2, 1.2], "#e8dcc0", studs=True)
    for x in (-23.0, 23.0):
        b.box([x, 12.0, z], [6.0, 24.0, 6.0], "#e8dcc0", studs=True)
        b.box([x, 24.6, z], [7.0, 1.2, 7.0], "#c8a040")
    b.box([0.0, 22.0, z], [40.0, 4.0, 4.6], "#e8dcc0")
    board_letters(b, 0.0, 22.0, z - 2.3, "HARROW STUDIOS", 3.0, "#e8dcc0", "#2a2a3a", facing="z-",
                  solid=False)
    board_letters(b, 0.0, 22.0, z + 2.3, "HARROW STUDIOS", 3.0, "#e8dcc0", "#2a2a3a", facing="z+",
                  solid=False)
    booth = rect(30.0, 40.0, z + 4.0, z + 14.0)
    s.reserve(booth)
    building(b, booth, 0.0, 9.0, "#e8dcc0", roof_colour="#c8a040",
             doors={"z+": [(31.0, 39.0, 7.4)]}, windows={"x-": [(z + 6.0, z + 12.0, 3.4, 7.0)]},
             glass=True, lights=WARM)
    threshold(b, booth, "z+", (31.0, 39.0))
    b.box([28.6, 5.0, z + 4.6], [0.6, 10.0, 0.6], "#c43a32")
    # the executive building: two floors, a stepped tower in the middle
    ex = rect(-206.0, -126.0, -246.0, -222.0)
    s.reserve(ex)
    building(b, ex, 0.0, 12.0, "#e8dcc0", roof_colour="#8a7a5a", floor_colour="#8a6a4a",
             doors={"z+": [(-172.0, -160.0, 10.0)]},
             windows={"z+": [(-200.0, -180.0, 3.6, 9.0), (-152.0, -132.0, 3.6, 9.0)],
                      "z-": [(-200.0, -132.0, 3.6, 9.0)]},
             glass=True, lights=WARM)
    threshold(b, ex, "z+", (-172.0, -160.0))
    for k, (w, d) in enumerate(((30.0, 16.0), (20.0, 12.0), (10.0, 8.0))):
        slab(b, rect(-166.0 - w / 2.0, -166.0 + w / 2.0, -234.0 - d / 2.0, -234.0 + d / 2.0),
             13.2 + 4.0 * (k + 1), 4.0, "#e8dcc0" if k % 2 == 0 else "#c8a040", studs=True)
    b.box([-166.0, 13.2 + 14.0, -234.0], [1.0, 4.0, 1.0], "#c8a040")
    supply_med(b, -200.0, FLOOR, -228.0, "x+")
    supply_ammo(b, -132.0, FLOOR, -240.0, "x-")
    # the car park
    for k, (cx, along) in enumerate(((-230.0, "z"), (-200.0, "z"), (-100.0, "z"), (90.0, "z"),
                                     (150.0, "z"), (210.0, "z"), (240.0, "x"))):
        car(b, cx, -270.0, along, ["#2a2a2a", "#f2f2f2", "#8a2a24", "#c8a040", "#3a5a6a", "#e8e8e8",
                                   "#4a3a6a"][k], length=11.0, y=0.3, wrecked=k == 3)
    barrel_spot(b, -60.0, 0.3, -268.0)
    # the premiere's searchlights on their trailers either side of the gate
    for x in (-48.0, 48.0):
        b.box([x, 1.4, z - 18.0], [6.0, 2.8, 8.0], "#3a3a3a", material="metal")
        b.cyl([x, 4.0, z - 18.0], [3.0, 2.4, 3.0], "#5a5f66", material="metal")


def _lights(b: Area) -> None:
    from .kit import flood
    for (x, z) in ((-60.0, 70.0), (60.0, 70.0), (-60.0, -50.0), (60.0, -50.0), (-200.0, -60.0),
                   (210.0, -60.0), (-90.0, 150.0), (100.0, 150.0)):
        flood(b, x, z, 0.0, 26.0, LAMP)
    for (x, z) in ((-30.0, 106.0 + 12.0), (30.0, 94.0), (-150.0, 106.0 + 12.0), (150.0, 94.0)):
        lamp_post(b, x, z, h=14.0, light=LAMP, y=0.0)


# ================================================================== rigs
def _rigs(b: Area) -> None:
    for x in (-48.0, 48.0):
        b.rig("searchlight", x, 5.4, GATE_Z - 18.0, 0.0, seed=1 if x < 0 else 2)
    b.rig("camera_crane", 176.0, 0.0, -112.0, 0.0)
    b.rig("stage_lights", -191.0, 26.0, 158.0, 0.0, span=120.0, n=6)
    b.rig("stage_lights", -191.0, 26.0, 218.0, 0.0, span=120.0, n=6)
    b.rig("stage_lights", 191.0, 26.0, 158.0, 0.0, span=120.0, n=6, warm=1)
    b.rig("stage_lights", 191.0, 26.0, 218.0, 0.0, span=120.0, n=6, warm=1)
    b.rig("dragon_head", 192.0, 20.0, STAGE9[3] - 4.2, math.pi)
    b.rig("earth_globe", -190.0, 30.0, 236.0, 0.0)
    b.rig("tumbleweeds", -170.0, 0.4, 25.0, 0.0, x0=WEST_X[0], x1=WEST_X[1], z0=WEST_Z[0] + 2.0,
          z1=WEST_Z[1] - 2.0, n=4)
    b.rig("ship_flag", -188.0, 6.0 + 28.0, -161.0, 0.0)
    b.rig("wind_machine", -80.0, 4.0, -146.8, 0.0)
    b.rig("flying_saucer", 0.0, 18.0, 206.0, 0.0)
    b.rig("pyro", 170.0, TRENCH_FLOOR, -146.0, 0.0,
          shots=[[100.0, -146.0], [124.0, -146.0], [150.0, -146.0], [176.0, -146.0], [204.0, -146.0],
                 [230.0, -146.0], [154.0, -176.0], [154.0, -196.0]], floor=TRENCH_FLOOR)
    b.rig("beacon", 70.0, 48.0, 160.0, 0.0, colour="#ff3a2a")


# ================================================================ spawns
def _zombie_spawns(b: Area) -> None:
    top = 4.8
    for gx, gz in ((-262.0, 46.0), (-254.0, 48.0), (-258.0, 54.0)):
        b.zombie_spawn(gx, gz + 2.0, "grave")
    for x, z in ((-230.0, -120.0), (-110.0, -200.0)):
        b.zombie_spawn(x, z, "water", y=TANK_BED)
    for x, z in ((240.0, -146.0), (154.0, -194.0)):
        b.zombie_spawn(x, z, "trench", y=TRENCH_FLOOR)
    b.zombie_spawn(208.0, -20.0, "subway", y=SUBWAY_FLOOR)
    for x, z in ((-246.0, 238.0), (-136.0, 238.0)):
        b.zombie_spawn(x, z, "stage", y=FLOOR + 0.2)
    for x, z in ((136.0, 140.0), (246.0, 140.0)):
        b.zombie_spawn(x, z, "stage", y=FLOOR)
    for x in (-200.0, 0.0, 200.0):
        b.zombie_spawn(x, 267.0, "", y=6.0)
    for x, z in ((-240.0, -270.0), (-110.0, -272.0), (110.0, -272.0), (250.0, -268.0)):
        b.zombie_spawn(x, z, "", y=0.3)
    for x, z in ((-272.0, -20.0), (272.0, -20.0), (-272.0, 150.0), (272.0, 150.0), (-100.0, 140.0),
                 (100.0, 130.0), (-60.0, 236.0)):
        b.zombie_spawn(x, z, "")
