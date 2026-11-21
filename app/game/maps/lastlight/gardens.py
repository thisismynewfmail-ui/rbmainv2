"""Glasshouse Gardens -- the botanical gardens, the night the corpse flower bloomed.

Layout (north is +z)::

   z +280 ------------------------------ the boundary wall -------------------------
          THE FLYTRAP HOUSE     THE TITAN HOUSE (the corpse flower, the lure)    the boiler
                                                                                house
          THE LILY HOUSE        THE PALM HOUSE (the dome, the gallery)          THE DESERT
          (lily pads across                                                     HOUSE
           the pond)
   z   0 ==========================  the broad walk  =================================
          THE TREETOP WALKWAY   THE TOPIARY GARDEN (the fountain)    THE ROCKERY (the cascade)
          (through the          THE ORANGERY (the safe room)         THE JAPANESE GARDEN
           arboretum)                                                (the koi pond, the bridge,
                                                                      the pagoda)
   z -280 ------------------------------ the main gate -----------------------------

Everybody deploys in the Orangery, among the lemon trees.

What makes it this place:

* **The glasshouses.**  The Palm House with its dome, a gallery round the
  inside up a stair; the Lily House, crossed on the giant lily pads; the
  Desert House's dunes and cacti; the flytraps, which bite.
* **The lure.**  The corpse flower is blooming tonight, in its own tall
  glass house: open the vents, and the stink of it goes out over the
  gardens -- and the dead come to it.
* **High ground.**  The treetop walkway up in the arboretum and its
  lookout, the Palm House gallery, the rockery, the pagoda's steps.
* **At night.**  The topiary animals standing in the dark, the koi, the
  peacock that screams, the fireflies.
"""
from __future__ import annotations

import math
import random
from typing import List, Tuple

from .kit import (
    FLOOR, GLASS, STEEL_DARK, WARM, WOOD, WOOD_DARK, WOOD_LIGHT, Area, Surfaces, barrel_spot,
    bench, boundary, building, carve, deploy_pad, flight, gable, holed_wall, lamp_post, plate,
    rect, sign_decal, slab, supply_ammo, supply_med, threshold, wall_sign)
from ..relay.kit import mound, pine, tier_stack, tree

Rect = Tuple[float, float, float, float]

HALF = 280.0
SKY = {"top": "#081018", "horizon": "#2a3a3a", "sun": [-0.3, 0.55, 0.6],
       "clouds": 0.35, "tint": "#a8c8c0"}
AMBIENT = "#4a6a62"

LAWN = "#3a6a32"
GRAVEL = "#b8ac94"
HEDGE = "#2a5a26"
WHITE = "#e8ece8"
IRON = "#2a3a34"
BRICK_O = "#a85a3a"

PALM = rect(-90.0, 90.0, 60.0, 160.0)
PALM_H = 24.0
GALLERY_Y = 14.0
LILY = rect(-250.0, -150.0, 40.0, 130.0)
POND = rect(-238.0, -162.0, 52.0, 118.0)
DESERT = rect(150.0, 250.0, 40.0, 130.0)
FLYTRAP = rect(-250.0, -170.0, 170.0, 230.0)
TITAN = rect(-24.0, 24.0, 190.0, 238.0)
TITAN_H = 34.0
BOILER = rect(170.0, 230.0, 180.0, 230.0)
ORANGERY = rect(-60.0, 60.0, -150.0, -104.0)
TOPIARY = rect(-60.0, 60.0, -80.0, -20.0)
KOI = rect(140.0, 236.0, -170.0, -110.0)
ROCKERY = (180.0, -50.0)
WALK_Y = 16.0


def build(b: Area) -> None:
    rng = random.Random(0x6A2D)
    b.extra.update({"weather": "spores", "accent": "#b6ff8a"})
    s = Surfaces(b)
    _ground(b, s)
    boundary(b, 30.0, "#3a3a32", "#2e2e28", rng, horizon="forest")
    _palm_house(b, s, rng)
    _lily_house(b, s)
    _desert_house(b, s, rng)
    _flytrap_house(b, s)
    _titan_house(b, s)
    _boiler_house(b, s)
    _orangery(b, s)
    _topiary(b, s)
    _rockery(b, s)
    _japanese(b, s)
    _treetops(b, s, rng)
    _gate(b, s)
    _grounds(b, s, rng)
    _paths(b, s)
    _rigs(b)
    _zombie_spawns(b)
    for x, z, name in ((0, -127, "the orangery"), (0, 110, "the palm house"), (0, 150, "the gallery"),
                       (-200, 85, "the lily house"), (200, 85, "the desert house"), (-210, 200, "the flytrap house"),
                       (0, 214, "the titan house"), (200, 205, "the boiler house"), (0, -50, "the topiary garden"),
                       (180, -50, "the rockery"), (188, -140, "the koi pond"), (236, -200, "the pagoda"),
                       (-180, -80, "the treetop walkway"), (-230, -180, "the lookout"), (0, -250, "the main gate"),
                       (0, 10, "the broad walk"), (-100, -200, "the arboretum")):
        b.landmark(float(x), float(z), name)
    b.camera(0.0, 40.0, -20.0, 0.0, 20.0, 110.0)
    b.camera(-130.0, 30.0, -40.0, -200.0, 16.0, -100.0)
    b.camera(140.0, 20.0, -80.0, 200.0, 2.0, -150.0)
    b.camera(-100.0, 20.0, 100.0, -200.0, 0.0, 85.0)


# ================================================================ helpers
def _glasshouse(b: Area, r: Rect, h: float, doors: dict, frame: str = WHITE, roof: bool = True,
                floor_holes: List[Rect] = ()) -> None:
    """A glasshouse: a low brick plinth, the walls all glass between white
    iron mullions, a glass roof; ``doors`` as building() takes them."""
    x0, x1, z0, z1 = r
    t = 1.0
    for side in ("x-", "x+", "z-", "z+"):
        along_z = side in ("x-", "x+")
        lo, hi = (z0, z1) if along_z else (x0 + t, x1 - t)
        holes = [(a, c, -1.0, head) for a, c, head in doors.get(side, [])]
        cursor = lo + 2.0
        while cursor + 6.0 < hi - 1.0:
            a, c = cursor, cursor + 6.0
            if not any(a < hc + 1.0 and c > ha - 1.0 for ha, hc, _, _ in holes):
                holes.append((a, c, 2.4, h - 2.0))
            cursor += 8.0
        at = {"x-": x0 + t / 2.0, "x+": x1 - t / 2.0, "z-": z0 + t / 2.0, "z+": z1 - t / 2.0}[side]
        holed_wall(b, "z" if along_z else "x", at, t, lo, hi, 0.0, h, frame, holes, glass=True)
    plate(b, carve(rect(x0 + t, x1 - t, z0 + t, z1 - t), list(floor_holes)), FLOOR, FLOOR, "#7a6a52")
    if roof:
        slab(b, r, h + 0.6, 0.6, GLASS, material="glass", alpha=0.35)


# ================================================================ ground
def _ground(b: Area, s: Surfaces) -> None:
    h = b.half + b.margin
    holes = [POND, KOI]
    for r in holes:
        s.reserve(r)
    pieces = carve(rect(-h, h, -h, h), holes)
    plate(b, pieces, 0.0, 0.6, LAWN, studs=True, material="grass")
    plate(b, pieces, -0.6, 5.4, "#4a3a2a")


# ============================================================== palm house
def _palm_house(b: Area, s: Surfaces, rng: random.Random) -> None:
    """The Palm House: glass walls and roof, the dome stepping up over the
    middle; inside, palms and a pool, and the gallery round the walls up a
    stair."""
    x0, x1, z0, z1 = PALM
    s.reserve(rect(x0 - 2.0, x1 + 2.0, z0 - 2.0, z1 + 2.0))
    _glasshouse(b, PALM, PALM_H, {"z-": [(-8.0, 8.0, 12.0)], "x-": [(80.0, 90.0, 10.0)],
                                  "x+": [(80.0, 90.0, 10.0)], "z+": [(-8.0, 8.0, 10.0)]}, roof=False)
    roof = PALM_H + 0.6
    dome = rect(-40.0, 40.0, 80.0, 140.0)
    plate(b, carve(PALM, [dome]), roof, 0.6, GLASS, material="glass", alpha=0.35)
    for k in range(4):
        inset = k * 8.0
        r = rect(dome[0] + inset, dome[1] - inset, dome[2] + inset, dome[3] - inset)
        ring = carve(r, [rect(r[0] + 8.0, r[1] - 8.0, r[2] + 8.0, r[3] - 8.0)]) if k < 3 else [r]
        plate(b, ring, roof + 4.0 * (k + 1), 0.6, GLASS, material="glass", alpha=0.35)
        for (a, c, d, e) in ((r[0], r[0] + 0.8, r[2], r[3]), (r[1] - 0.8, r[1], r[2], r[3])):
            b.box([(a + c) / 2.0, roof + 4.0 * k + 2.0 - 0.3, (d + e) / 2.0], [c - a, 4.0 - 0.6, e - d], WHITE)
        for (a, c, d, e) in ((r[0] + 0.8, r[1] - 0.8, r[2], r[2] + 0.8), (r[0] + 0.8, r[1] - 0.8, r[3] - 0.8, r[3])):
            b.box([(a + c) / 2.0, roof + 4.0 * k + 2.0 - 0.3, (d + e) / 2.0], [c - a, 4.0 - 0.6, e - d], WHITE)
    # the gallery round the inside, its posts, its rail, the stair up
    inner = rect(x0 + 1.0, x1 - 1.0, z0 + 1.0, z1 - 1.0)
    ring = carve(inner, [rect(x0 + 7.0, x1 - 7.0, z0 + 7.0, z1 - 7.0)])
    plate(b, ring, GALLERY_Y, 0.6, WOOD, studs=True)
    for x in (-60.0, -30.0, 30.0, 60.0):
        for z in (z0 + 6.4, z1 - 6.4):
            b.box([x, (FLOOR + GALLERY_Y - 0.6) / 2.0, z], [0.8, GALLERY_Y - 0.6 - FLOOR, 0.8], WHITE)
    for z in (90.0, 130.0):
        for x in (x0 + 6.4, x1 - 6.4):
            b.box([x, (FLOOR + GALLERY_Y - 0.6) / 2.0, z], [0.8, GALLERY_Y - 0.6 - FLOOR, 0.8], WHITE)
    flight(b, "z", z0 + 27.0, z0 + 7.0, -77.0, -71.0, FLOOR, GALLERY_Y, WOOD_DARK, fill=FLOOR)
    for (a, c, d, e) in ((x0 + 7.0, x1 - 7.0, z1 - 7.0, z1 - 6.4), (x0 + 6.4, x0 + 7.0, z0 + 7.0, z1 - 7.0),
                         (x1 - 7.0, x1 - 6.4, z0 + 7.0, z1 - 7.0), (x0 + 7.0, -77.0, z0 + 6.4, z0 + 7.0),
                         (-71.0, x1 - 7.0, z0 + 6.4, z0 + 7.0)):
        b.box([(a + c) / 2.0, GALLERY_Y + 0.6, (d + e) / 2.0], [c - a, 1.2, e - d], IRON)
    # the palms and the pool under the dome
    for (x, z, sc) in ((-24.0, 96.0, 2.2), (24.0, 96.0, 2.0), (-24.0, 128.0, 2.4), (24.0, 128.0, 2.1), (-60.0, 110.0, 1.6),
                       (60.0, 110.0, 1.7)):
        _palm(b, x, z, sc)
    for (a, c, d, e) in ((-14.0, 14.0, 104.0, 104.8), (-14.0, 14.0, 119.2, 120.0), (-14.0, -13.2, 104.8, 119.2),
                         (13.2, 14.0, 104.8, 119.2)):
        b.box([(a + c) / 2.0, FLOOR + 0.8, (d + e) / 2.0], [c - a, 1.6, e - d], "#8a8478")
    b.water(0.0, 112.0, 26.4, 14.4, FLOOR + 1.4, "#2a6a5a")
    wall_sign(b, 0.0, 13.5, z0 - 0.35, 30.0, 2.6, sign_decal("THE PALM HOUSE  1852", WHITE, IRON, 11.5), "z-", WHITE)
    supply_ammo(b, 60.0, GALLERY_Y, z1 - 4.0, "z-")
    supply_med(b, -70.0, FLOOR, 140.0, "x+")
    barrel_spot(b, 40.0, FLOOR, 72.0)


def _palm(b: Area, x: float, z: float, sc: float, y: float = FLOOR) -> None:
    h = 7.0 * sc
    b.cyl([x, y + h / 2.0, z], [1.2 * sc, h, 1.2 * sc], "#7a6a4a")
    for k in range(7):
        yaw = k / 7.0 * math.pi * 2.0
        b.box([x + math.sin(yaw) * 2.2 * sc, y + h + 0.2 + k * 0.03, z + math.cos(yaw) * 2.2 * sc], [1.4 * sc, 0.2, 4.6 * sc],
              "#2a6a2a", r=[0, yaw, 0], collide=False)
    b.sphere([x, y + h + 0.3, z], [1.8 * sc, 1.4 * sc, 1.8 * sc], "#3a7a2a", collide=False)


# ============================================================ lily house
def _lily_house(b: Area, s: Surfaces) -> None:
    """The Lily House: a glasshouse round a pond, and in the pond the giant
    water lilies -- pads you can stand on, a stepping way across."""
    x0, x1, z0, z1 = LILY
    s.reserve(rect(x0 - 2.0, x1 + 2.0, z0 - 2.0, z1 + 2.0))
    _glasshouse(b, LILY, 16.0, {"x+": [(80.0, 90.0, 10.0)], "z-": [(-205.0, -195.0, 10.0)]}, floor_holes=[POND])
    px0, px1, pz0, pz1 = POND
    slab(b, POND, -3.0, 3.0, "#2a3a2a", studs=True)
    b.water((px0 + px1) / 2.0, (pz0 + pz1) / 2.0, px1 - px0, pz1 - pz0, -0.8, "#1a4a3a")
    for (x, z, d) in ((-170.0, 85.0, 8.0), (-181.0, 92.0, 9.0), (-193.0, 84.0, 8.0), (-205.0, 92.0, 10.0),
                      (-218.0, 82.0, 8.0), (-228.0, 92.0, 7.0), (-190.0, 104.0, 8.0), (-212.0, 64.0, 9.0),
                      (-176.0, 66.0, 7.0)):
        b.cyl([x, -0.8, z], [d, 0.6, d], "#3a7a3a")
        b.cyl([x, -2.05, z], [1.0, 1.9, 1.0], "#2a4a2a")
    for k, x in enumerate((-226.0, -200.0, -176.0)):
        b.box([x, 2.0, 124.0], [10.0, 4.0, 4.0], WOOD_DARK)
    supply_ammo(b, -160.0, FLOOR, 46.0, "z+")
    barrel_spot(b, -240.0, FLOOR, 124.0)


def _desert_house(b: Area, s: Surfaces, rng: random.Random) -> None:
    """The Desert House: dunes heaped inside the glass, cacti standing in
    them, rocks."""
    x0, x1, z0, z1 = DESERT
    s.reserve(rect(x0 - 2.0, x1 + 2.0, z0 - 2.0, z1 + 2.0))
    _glasshouse(b, DESERT, 18.0, {"x-": [(80.0, 90.0, 10.0)], "z-": [(195.0, 205.0, 10.0)]})
    for (cx, cz, rx, rz) in ((175.0, 110.0, 18.0, 12.0), (222.0, 64.0, 20.0, 14.0)):
        mound(b, cx, cz, rx, rz, 3, 1.2, ["#d8b878", "#c8a868", "#b89858"], y0=FLOOR)
    for (x, z, h) in ((165.0, 60.0, 9.0), (200.0, 100.0, 12.0), (238.0, 110.0, 8.0), (190.0, 54.0, 6.0),
                      (214.0, 86.0, 10.0)):
        b.box([x, FLOOR + h / 2.0, z], [1.8, h, 1.8], "#4a7a3a")
        b.box([x + 1.6, FLOOR + h * 0.55, z], [1.4, 1.2, 1.2], "#4a7a3a")
        b.box([x + 2.0, FLOOR + h * 0.55 + 1.6, z], [1.0, 3.2, 1.0], "#4a7a3a")
        b.sphere([x, FLOOR + h + 0.4, z], [1.2, 0.8, 1.2], "#e8588a", collide=False)
    for (x, z) in ((230.0, 120.0), (160.0, 120.0)):
        b.sphere([x, FLOOR + 2.0, z], [6.0, 4.0, 5.0], "#a8886a")
    supply_med(b, 244.0, FLOOR, 50.0, "x-")


def _flytrap_house(b: Area, s: Surfaces) -> None:
    """The carnivorous plant house: beds of pitcher plants, and the giant
    flytraps, which close on anything that comes near (a rig)."""
    x0, x1, z0, z1 = FLYTRAP
    s.reserve(rect(x0 - 2.0, x1 + 2.0, z0 - 2.0, z1 + 2.0))
    _glasshouse(b, FLYTRAP, 14.0, {"x+": [(195.0, 205.0, 10.0)], "z-": [(-215.0, -205.0, 10.0)]})
    for (x, z) in ((-236.0, 186.0), (-236.0, 214.0), (-210.0, 220.0), (-184.0, 214.0)):
        b.box([x, FLOOR + 0.8, z], [8.0, 1.6, 6.0], "#5a4a3a")
    for (x, z) in ((-225.0, 200.0), (-198.0, 196.0)):
        for k in range(3):
            b.cyl([x + (k - 1) * 3.0, FLOOR + 2.4, z + (k % 2) * 2.0], [1.4, 4.8, 1.4], "#7a2a3a")
    wall_sign(b, x1 + 0.35, 10.0, 210.0, 12.0, 1.6, sign_decal("KEEP HANDS CLEAR", WHITE, "#a82a2a", 7.5), "x+", WHITE)
    barrel_spot(b, -176.0, FLOOR, 180.0)


def _titan_house(b: Area, s: Surfaces) -> None:
    """The Titan House: a tall glass tower for the one plant -- the corpse
    flower, blooming tonight; the vent controls by the door are the lure."""
    x0, x1, z0, z1 = TITAN
    s.reserve(rect(x0 - 2.0, x1 + 2.0, z0 - 2.0, z1 + 2.0))
    _glasshouse(b, TITAN, TITAN_H, {"z-": [(-6.0, 6.0, 11.0)]})
    cx, cz = 0.0, 216.0
    b.cyl([cx, FLOOR + 1.6, cz], [14.0, 3.2, 14.0], "#6a5a4a")
    b.cyl([cx, FLOOR + 3.2 + 7.0, cz], [3.0, 14.0, 3.0], "#d8c890")
    b.box([12.0, FLOOR + 1.6, 196.0], [4.0, 3.2, 2.0], "#4a5060", material="metal")
    b.set_lure(12.0, FLOOR, 199.5, "the corpse flower", "Open the vents", "ll_stink", (0.0, 0.0, 200.0))
    wall_sign(b, 0.0, 14.0, z0 - 0.35, 20.0, 2.4, sign_decal("TITAN ARUM  IN BLOOM", WHITE, "#6a2a6a", 8.3), "z-", WHITE)
    supply_ammo(b, -14.0, FLOOR, 232.0, "z-")


def _boiler_house(b: Area, s: Surfaces) -> None:
    """The boiler house that heats the glass, and the potting sheds."""
    x0, x1, z0, z1 = BOILER
    s.reserve(rect(x0 - 2.0, x1 + 2.0, z0 - 2.0, z1 + 2.0))
    building(b, BOILER, 0.0, 12.0, BRICK_O, roof_colour="#4a3a3a", floor_colour="#6a6058",
             doors={"z-": [(190.0, 200.0, 9.0)]}, windows={"x-": [(190.0, 200.0, 4.0, 8.0)]}, glass=True, lights=WARM)
    threshold(b, BOILER, "z-", (190.0, 200.0))
    gable(b, BOILER, 12.0 + 1.2, "#4a3a3a", "x", tiers=3, rise=1.4)
    b.box([222.0, 13.2 + 4.2 + 8.0, 205.0], [3.0, 16.0, 3.0], BRICK_O)
    b.box([185.0, FLOOR + 2.0, 220.0], [10.0, 4.0, 6.0], STEEL_DARK, material="metal")
    b.box([214.0, FLOOR + 1.6, 188.0], [10.0, 3.2, 4.0], WOOD_LIGHT)
    supply_med(b, 220.0, FLOOR, 198.0, "x-")
    barrel_spot(b, 160.0, 0.0, 196.0)


# =============================================================== orangery
def _orangery(b: Area, s: Surfaces) -> None:
    """The Orangery: brick, tall glass along the front, citrus trees in
    their tubs -- the safe room."""
    x0, x1, z0, z1 = ORANGERY
    s.reserve(rect(x0 - 2.0, x1 + 2.0, z0 - 2.0, z1 + 2.0))
    building(b, ORANGERY, 0.0, 15.0, BRICK_O, roof_colour="#3a3a3a", floor_colour="#c8b898",
             doors={"z+": [(-8.0, 8.0, 11.0)], "x-": [(-132.0, -122.0, 10.0)], "x+": [(-132.0, -122.0, 10.0)]},
             windows={"z+": [(-54.0, -42.0, 2.4, 12.0), (-34.0, -20.0, 2.4, 12.0), (20.0, 34.0, 2.4, 12.0),
                             (42.0, 54.0, 2.4, 12.0)],
                      "z-": [(-40.0, -20.0, 5.0, 11.0), (20.0, 40.0, 5.0, 11.0)]},
             glass=True, lights=WARM)
    for side, span in (("z+", (-8.0, 8.0)), ("x-", (-132.0, -122.0)), ("x+", (-132.0, -122.0))):
        threshold(b, ORANGERY, side, span)
    gable(b, ORANGERY, 15.0 + 1.2, "#3a3a3a", "x", tiers=3, rise=1.6)
    wall_sign(b, 0.0, 13.6, z1 + 0.35, 24.0, 2.0, sign_decal("THE ORANGERY", BRICK_O, "#f2e6c8", 12.0), "z+", BRICK_O)
    floor = FLOOR
    for z in (-120.0, -132.0):
        for k in range(8):
            x = -45.0 + k * 12.85
            deploy_pad(b, x, z, floor, "#b6ff8a", 4.6)
            b.safe_spawn(x, floor + 0.6, z, 0.0)
    for x in (-52.0, -26.0, 26.0, 52.0):
        b.box([x, floor + 1.2, -144.0], [3.0, 2.4, 3.0], "#8a5a3a")
        b.sphere([x, floor + 4.4, -144.0], [4.4, 4.0, 4.4], "#3a6a2a", collide=False)
    supply_ammo(b, -6.0, floor, -144.0, "z+")
    supply_med(b, 8.0, floor, -146.6, "z+")


def _topiary(b: Area, s: Surfaces) -> None:
    """The topiary garden: animals clipped out of hedge standing round the
    fountain -- an elephant, a bear, a giraffe, a rabbit -- and a low hedge
    round it all."""
    x0, x1, z0, z1 = TOPIARY
    s.reserve(TOPIARY)
    for (a, c, d, e) in ((x0, -6.0, z0, z0 + 2.0), (6.0, x1, z0, z0 + 2.0), (x0, -6.0, z1 - 2.0, z1), (6.0, x1, z1 - 2.0, z1),
                         (x0, x0 + 2.0, z0 + 2.0, z1 - 2.0), (x1 - 2.0, x1, z0 + 2.0, z1 - 2.0)):
        b.box([(a + c) / 2.0, 1.4, (d + e) / 2.0], [c - a, 2.8, e - d], HEDGE, studs=True, material="grass")
    # the fountain
    b.cyl([0.0, 0.6, -50.0], [16.0, 1.2, 16.0], "#9a9488")
    for (a, c, d, e) in ((-7.0, 7.0, -57.0, -56.0), (-7.0, 7.0, -44.0, -43.0), (-7.0, -6.0, -56.0, -44.0),
                         (6.0, 7.0, -56.0, -44.0)):
        b.box([(a + c) / 2.0, 1.9, (d + e) / 2.0], [c - a, 1.4, e - d], "#9a9488")
    b.water(0.0, -50.0, 12.0, 12.0, 2.2, "#3a7a8a")
    b.cyl([0.0, 1.2 + 2.5, -50.0], [2.0, 5.0, 2.0], "#9a9488")
    # the animals
    _animal(b, "elephant", -36.0, -40.0)
    _animal(b, "bear", 36.0, -40.0)
    _animal(b, "giraffe", -36.0, -64.0)
    _animal(b, "rabbit", 36.0, -64.0)
    barrel_spot(b, 20.0, 0.0, -30.0)


def _animal(b: Area, kind: str, x: float, z: float) -> None:
    if kind == "elephant":
        b.box([x, 4.0, z], [5.0, 5.0, 9.0], HEDGE, material="grass")
        for (dx, dz) in ((-1.6, -3.0), (1.6, -3.0), (-1.6, 3.0), (1.6, 3.0)):
            b.box([x + dx, 0.75, z + dz], [1.4, 1.5, 1.4], HEDGE, material="grass")
        b.box([x, 5.6, z + 5.6], [3.6, 3.6, 2.2], HEDGE, material="grass")
        b.box([x, 3.0, z + 7.0], [1.0, 4.0, 1.0], HEDGE, material="grass")
    elif kind == "bear":
        b.box([x, 3.5, z], [5.0, 7.0, 4.0], HEDGE, material="grass")
        b.box([x, 8.6, z], [3.6, 3.2, 3.2], HEDGE, material="grass")
        for dx in (-1.4, 1.4):
            b.box([x + dx, 10.6, z], [1.0, 0.8, 1.0], HEDGE, material="grass")
    elif kind == "giraffe":
        b.box([x, 5.0, z], [3.4, 3.4, 6.0], HEDGE, material="grass")
        for (dx, dz) in ((-1.0, -2.0), (1.0, -2.0), (-1.0, 2.0), (1.0, 2.0)):
            b.box([x + dx, 1.65, z + dz], [1.0, 3.3, 1.0], HEDGE, material="grass")
        b.box([x, 9.6, z + 2.4], [1.4, 6.0, 1.4], HEDGE, material="grass")
        b.box([x, 13.2, z + 3.2], [1.8, 1.4, 2.8], HEDGE, material="grass")
    else:
        b.box([x, 2.0, z], [4.0, 4.0, 4.0], HEDGE, material="grass")
        b.box([x, 5.2, z + 0.8], [2.8, 2.4, 2.8], HEDGE, material="grass")
        for dx in (-0.7, 0.7):
            b.box([x + dx, 8.4, z + 0.8], [0.8, 4.0, 0.8], HEDGE, material="grass")


def _rockery(b: Area, s: Surfaces) -> None:
    """The rockery: a heap of rock in tiers with alpines in its crannies, and
    a stream coming down it in steps to a pool at the foot."""
    cx, cz = ROCKERY
    s.reserve(rect(cx - 36.0, cx + 36.0, cz - 28.0, cz + 28.0))
    top = mound(b, cx, cz, 34.0, 26.0, 5, 2.0, ["#8a8478", "#7a7468", "#9a9488"], shrink=0.3)
    for (x, z) in ((cx - 20.0, cz - 10.0), (cx + 16.0, cz + 8.0), (cx - 6.0, cz + 14.0)):
        b.sphere([x, b.surface(x, z, 30.0) + 1.2, z], [4.0, 2.6, 3.4], "#a8a498")
    pool = rect(cx - 8.0, cx + 8.0, cz - 34.0, cz - 26.0)
    s.reserve(pool)
    for (a, c, d, e) in ((pool[0], pool[1], pool[2], pool[2] + 0.8), (pool[0], pool[0] + 0.8, pool[2] + 0.8, pool[3]),
                         (pool[1] - 0.8, pool[1], pool[2] + 0.8, pool[3])):
        b.box([(a + c) / 2.0, 0.6, (d + e) / 2.0], [c - a, 1.2, e - d], "#8a8478")
    b.water(cx, cz - 29.6, 14.4, 7.2, 0.9, "#3a7a8a")
    supply_ammo(b, cx, top, cz, "z-")


def _japanese(b: Area, s: Surfaces) -> None:
    """The Japanese garden: the koi pond sunk in the lawn and the red bridge
    arching over it, stone lanterns, the bamboo, the pagoda on its rise,
    the teahouse."""
    x0, x1, z0, z1 = KOI
    slab(b, KOI, -2.5, 2.5, "#3a4a3a", studs=True)
    b.water((x0 + x1) / 2.0, (z0 + z1) / 2.0, x1 - x0, z1 - z0, -0.6, "#1a4a4a")
    flight(b, "z", z1 - 8.0, z1, 150.0, 158.0, -2.5, 0.0, "#8a8478", fill=-2.5)
    flight(b, "z", z0 + 8.0, z0, 220.0, 228.0, -2.5, 0.0, "#8a8478", fill=-2.5)
    # the bridge: posts in the water, the deck arching in steps
    bx0, bx1 = 182.0, 194.0
    tops = [0.6, 1.6, 2.6, 3.4, 2.6, 1.6, 0.6]
    span = (z1 - z0) / len(tops)
    for k, top in enumerate(tops):
        a = z0 + k * span
        slab(b, rect(bx0, bx1, a, a + span), top, 0.5, "#b8322a", studs=True)
        for x in (bx0 + 0.4, bx1 - 0.4):
            b.box([x, (-2.5 + top - 0.5) / 2.0, a + span / 2.0], [0.8, top - 0.5 + 2.5, 0.8], "#8a2a22")
    for x in (bx0 + 0.3, bx1 - 0.3):
        for k, top in enumerate(tops):
            a = z0 + k * span
            b.box([x, top + 0.6, a + span / 2.0], [0.6, 1.2, span], "#c8382a")
    # stone lanterns
    for (x, z) in ((150.0, -100.0), (230.0, -100.0), (150.0, -180.0)):
        b.box([x, 1.0, z], [1.6, 2.0, 1.6], "#9a9488")
        b.box([x, 3.0, z], [2.4, 2.0, 2.4], "#8a8478")
        b.box([x, 4.4, z], [3.2, 0.8, 3.2], "#9a9488")
    # the pagoda on its rise
    px, pz = 236.0, -206.0
    s.reserve(rect(px - 22.0, px + 22.0, pz - 22.0, pz + 22.0))
    tier_stack(b, [[rect(px - 20.0, px + 20.0, pz - 20.0, pz + 20.0)], [rect(px - 14.0, px + 14.0, pz - 14.0, pz + 14.0)]],
               0.0, [1.6], ["#8a8478", "#9a9488"])
    py = 3.2
    building(b, rect(px - 8.0, px + 8.0, pz - 8.0, pz + 8.0), py, 7.0, "#c8382a", roof_colour="#2a2a2a",
             floor_colour="#8a6a4a", doors={"z+": [(px - 3.0, px + 3.0, py + 6.0)]}, lights=WARM)
    threshold(b, rect(px - 8.0, px + 8.0, pz - 8.0, pz + 8.0), "z+", (px - 3.0, px + 3.0), y0=py)
    y = py + 7.0 + 1.2
    for k, w in enumerate((22.0, 13.0, 18.0, 10.0, 14.0, 7.0)):
        if k % 2 == 0:
            slab(b, rect(px - w / 2.0, px + w / 2.0, pz - w / 2.0, pz + w / 2.0), y + 0.8, 0.8, "#2a2a2a")
            y += 0.8
        else:
            b.box([px, y + 2.0, pz], [w, 4.0, w], "#c8382a")
            y += 4.0
    b.box([px, y + 3.0, pz], [0.6, 6.0, 0.6], "#d8b84a")
    # the bamboo grove
    for k in range(14):
        bx = 150.0 + (k % 7) * 3.4
        bz = -200.0 - (k // 7) * 4.0 + (k % 3) * 0.6
        b.cyl([bx, 9.0, bz], [0.8, 18.0, 0.8], "#5a8a3a")
    supply_med(b, 164.0, 0.0, -106.0, "z+")
    barrel_spot(b, 210.0, 0.0, -96.0)


def _treetops(b: Area, s: Surfaces, rng: random.Random) -> None:
    """The arboretum's treetop walkway: a deck up at sixteen on posts,
    turning between the great trees, platforms round two of the trunks, the
    lookout tower at the far end; stairs up at both ends."""
    w = 6.0
    legs = [rect(-140.0, -100.0, -60.0, -54.0), rect(-146.0, -140.0, -120.0, -54.0), rect(-230.0, -146.0, -120.0, -114.0),
            rect(-236.0, -230.0, -190.0, -114.0)]
    plats = [rect(-152.0, -134.0, -126.0, -108.0), rect(-242.0, -224.0, -126.0, -108.0)]
    for r in legs:
        plate(b, carve(r, plats), WALK_Y, 0.6, WOOD_LIGHT, studs=True)
        x0, x1, z0, z1 = r
        along_x = (x1 - x0) > (z1 - z0)
        if along_x:
            for x in range(int(x0) + 6, int(x1) - 2, 14):
                for z in (z0 + 0.4, z1 - 0.4):
                    b.box([float(x), (WALK_Y - 0.6) / 2.0, z], [0.8, WALK_Y - 0.6, 0.8], WOOD_DARK)
        else:
            for z in range(int(z0) + 6, int(z1) - 2, 14):
                for x in (x0 + 0.4, x1 - 0.4):
                    b.box([x, (WALK_Y - 0.6) / 2.0, float(z)], [0.8, WALK_Y - 0.6, 0.8], WOOD_DARK)
    for r in plats:
        slab(b, r, WALK_Y, 0.6, WOOD, studs=True)
    flight(b, "x", -68.0, -100.0, -60.0, -54.0, 0.0, WALK_Y, WOOD_DARK, fill=0.0)
    # the lookout at the far end
    lx, lz = -233.0, -200.0
    slab(b, rect(lx - 8.0, lx + 8.0, lz - 8.0, lz + 10.0), WALK_Y, 0.6, WOOD, studs=True)
    for x in (lx - 7.4, lx + 7.4):
        for z in (lz - 7.4, lz + 9.4):
            b.box([x, (WALK_Y - 0.6) / 2.0, z], [0.8, WALK_Y - 0.6, 0.8], WOOD_DARK)
    flight(b, "z", lz + 4.0, lz - 6.0, lx - 6.0, lx, WALK_Y, WALK_Y + 10.0, WOOD_DARK, fill=WALK_Y)
    slab(b, rect(lx - 8.0, lx + 8.0, lz - 8.0 - 8.0, lz - 6.0), WALK_Y + 10.0, 0.6, WOOD, studs=True)
    for x in (lx - 7.4, lx + 7.4):
        b.box([x, (WALK_Y + 10.0 - 0.6) / 2.0, lz - 15.4], [0.8, WALK_Y + 10.0 - 0.6, 0.8], WOOD_DARK)
        b.box([x, WALK_Y + (10.0 - 0.6) / 2.0, lz - 6.6], [0.8, 10.0 - 0.6, 0.8], WOOD_DARK)
    b.box([lx, WALK_Y + 10.0 + 0.6, lz - 15.7], [16.0, 1.2, 0.6], WOOD_DARK)
    supply_ammo(b, lx + 3.0, WALK_Y + 10.0, lz - 11.0, "z+")
    # the great trees the walkway goes among
    for (x, z) in ((-120.0, -80.0), (-162.0, -96.0), (-190.0, -136.0), (-214.0, -100.0), (-120.0, -140.0),
                   (-250.0, -150.0), (-180.0, -170.0)):
        tree(b, x, z, 0.0, 2.4, "#5a4030", rng.choice(["#2a5a2e", "#3a6a32", "#2a4a28"]))
    supply_med(b, -143.0, WALK_Y, -112.0, "z-")
    barrel_spot(b, -233.0, WALK_Y, -121.0)


def _gate(b: Area, s: Surfaces) -> None:
    """The main gate: stone piers, the iron gates standing open, the ticket
    kiosk."""
    for x in (-14.0, 14.0):
        b.box([x, 7.0, -262.0], [4.0, 14.0, 4.0], "#9a9488")
        b.sphere([x, 15.0, -262.0], [3.2, 3.2, 3.2], "#9a9488")
    for x in (-24.0, 24.0):
        b.box([x, 6.0, -258.0], [0.6, 12.0, 10.0], IRON)
    b.box([0.0, 14.4, -262.0], [24.0, 1.2, 1.2], IRON)
    kiosk = rect(30.0, 44.0, -262.0, -250.0)
    s.reserve(rect(28.0, 46.0, -264.0, -248.0))
    building(b, kiosk, 0.0, 9.0, "#3a5a3a", roof_colour="#2a2a2a", floor_colour="#6a6058",
             doors={"x+": [(-260.0, -252.0, 7.0)]}, windows={"z+": [(32.0, 42.0, 3.6, 6.6)]}, glass=True, lights=WARM)
    threshold(b, kiosk, "x+", (-260.0, -252.0))
    wall_sign(b, 0.0, 16.0, -262.0, 22.0, 2.0, sign_decal("HARROW BOTANIC GARDENS", "#9a9488", IRON, 11.0),
              "z-", "#9a9488")
    supply_ammo(b, -40.0, 0.0, -240.0, "z+")


def _grounds(b: Area, s: Surfaces, rng: random.Random) -> None:
    """Lawns with knolls, specimen trees, beds, benches, lamps along the
    walks, the sundial."""
    for (cx, cz, rx, rz) in ((-120.0, 30.0, 22.0, 14.0), (110.0, -40.0, 20.0, 12.0), (-80.0, -200.0, 24.0, 18.0),
                             (90.0, -220.0, 22.0, 16.0), (-110.0, 220.0, 18.0, 14.0), (120.0, 240.0, 20.0, 14.0)):
        s.reserve(rect(cx - rx, cx + rx, cz - rz, cz + rz))
        top = mound(b, cx, cz, rx, rz, 2, 1.4, ["#3a6a32", "#447a3a"])
        tree(b, cx, cz, top, rng.uniform(1.3, 1.7), "#5a4030", rng.choice(["#2a5a2e", "#5a2a5a", "#3a6a32"]))
    s.reserve(rect(18.0, 22.0, 28.0, 32.0))
    b.box([20.0, 1.6, 30.0], [2.0, 3.2, 2.0], "#9a9488")
    b.box([20.0, 3.4, 30.0], [3.6, 0.4, 3.6], "#c8b878", material="metal")
    for (x, z) in ((-30.0, 10.0), (30.0, 10.0), (-30.0, -10.0), (30.0, -10.0)):
        bench(b, x, z, "x")
    for (x, z) in ((-100.0, 0.0), (-40.0, 0.0), (40.0, 0.0), (100.0, 0.0), (10.0, -90.0), (10.0, -190.0), (130.0, -69.0),
                   (-160.0, 0.0), (160.0, 0.0)):
        lamp_post(b, x, z + 9.0, h=11.0, light="#d8ffc8")
    for k in range(10):
        pine(b, -260.0 + k * 52.0 + rng.uniform(-4.0, 4.0), 268.0, 0.0, rng.uniform(1.4, 1.8))
    barrel_spot(b, -120.0, 0.0, 66.0)
    barrel_spot(b, 130.0, 0.0, 150.0)


def _paths(b: Area, s: Surfaces) -> None:
    for r in (rect(-270.0, 270.0, -6.0, 6.0), rect(-6.0, 6.0, -250.0, 58.0), rect(-6.0, 6.0, 162.0, 188.0),
              rect(-148.0, -92.0, 80.0, 90.0), rect(92.0, 148.0, 80.0, 90.0), rect(-206.0, -196.0, 6.0, 38.0),
              rect(196.0, 206.0, 6.0, 38.0), rect(-168.0, -26.0, 196.0, 204.0), rect(190.0, 200.0, 132.0, 178.0),
              rect(62.0, 180.0, -130.0, -124.0), rect(-100.0, -62.0, -130.0, -124.0)):
        s.lay(r, 0.3, GRAVEL, studs=True)


# ================================================================ rigs
def _rigs(b: Area) -> None:
    b.rig("corpse_flower", 0.0, FLOOR + 3.2, 216.0, 0.0, vents=[[0.0, TITAN_H + 0.6, 214.0]])
    b.rig("flytraps", -210.0, FLOOR, 200.0, 0.0,
          traps=[[-236.0, FLOOR + 1.6, 186.0], [-236.0, FLOOR + 1.6, 214.0], [-210.0, FLOOR + 1.6, 220.0],
                 [-184.0, FLOOR + 1.6, 214.0]])
    b.rig("koi", 188.0, -0.6, -140.0, 0.0, area=[144.0, 232.0, -166.0, -114.0], n=9)
    b.rig("fountain", 0.0, 6.2, -50.0, 0.0, pool=2.2, r=5.0)
    b.rig("stream", ROCKERY[0], 10.0, ROCKERY[1], 0.0, steps=5, pool_p=[ROCKERY[0], 0.9, ROCKERY[1] - 29.6])
    b.rig("fireflies", -180.0, 6.0, -120.0, 0.0, area=[-250.0, -100.0, -200.0, -40.0], n=40)
    b.rig("misters", 0.0, PALM_H - 1.0, 110.0, 0.0,
          heads=[[-60.0, PALM_H - 1.0, 80.0], [60.0, PALM_H - 1.0, 80.0], [-60.0, PALM_H - 1.0, 140.0],
                 [60.0, PALM_H - 1.0, 140.0], [0.0, PALM_H - 1.0, 70.0]])
    b.rig("peacock", 0.0, 0.0, -40.0, 0.0, area=[-50.0, 50.0, -76.0, -24.0])
    b.rig("lantern_glow", 0.0, 0.0, 0.0, 0.0, points=[[150.0, 3.0, -100.0], [230.0, 3.0, -100.0], [150.0, 3.0, -180.0]])
    b.rig("moth_swarm", -40.0, 10.0, 9.0, 0.0)


# ============================================================== spawns
def _zombie_spawns(b: Area) -> None:
    for (x, z) in ((-270.0, 260.0), (-140.0, 268.0), (60.0, 266.0), (260.0, 260.0), (270.0, 150.0), (270.0, 20.0),
                   (270.0, -80.0), (-270.0, 150.0), (-270.0, 20.0), (-270.0, -60.0), (-260.0, -250.0), (-140.0, -262.0),
                   (120.0, -262.0), (260.0, -262.0), (100.0, 180.0), (-120.0, 160.0), (130.0, 40.0), (-110.0, 50.0),
                   (-262.0, -150.0), (-160.0, -230.0), (240.0, -60.0), (-20.0, 260.0), (210.0, 160.0), (262.0, -170.0)):
        b.zombie_spawn(x, z, "")
    for (x, z) in ((170.0, -160.0), (220.0, -120.0)):
        b.zombie_spawn(x, z, "water", y=-2.5)
