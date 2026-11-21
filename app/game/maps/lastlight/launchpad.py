"""Launch Complex 9 -- the night of the launch that never went.

Layout (north is +z)::

   z +280 ------------------- the scrub, the radar ---------------------------
          THE FUEL FARM            THE LAUNCH PAD (the moon rocket on its     the
          (the LOX sphere, the     mount over the flame trench, the            dunes
           kerosene tanks, berms)  umbilical tower)                            ~~~~
   z  +34 ===================== the crawlerway ============================== the
          THE BLOCKHOUSE           THE SERVICE STRUCTURE (parked, climbable)   beach
          (domed, the safe room)   camera bunkers                              ~~~~
   z -118 ===================== the beach road ==================== THE PRESS  the
          the canal (alligators)   THE HANGAR (a stage on its transporter)     SITE ocean
   z -280 -------------------------------------------------------------------

Everybody deploys in the blockhouse, among the consoles, behind the blast
door.

What makes it this place:

* **The rocket.**  On the pad in the middle, the moon rocket stands on its
  mount over the flame trench, venting, searchlights crossing it.
* **The lure.**  At the foot of the umbilical tower, the pad's control
  panel: resume the countdown, and ten seconds later the engines light in
  the trench -- fire and smoke out of both ends -- and the horde comes for
  the noise, onto the pad and down into the trench.
* **High ground.**  The service structure's three decks, the pad's tiers,
  the press bleachers, the dunes.
* **The coast.**  Surf on the beach to the east; to the west, the drainage
  canal, and what lives in it.
"""
from __future__ import annotations

import math
import random
from typing import List, Tuple

from .kit import (
    ASPHALT, CONCRETE, CONCRETE_DARK, CONCRETE_LIGHT, FLOOR, HAZARD, STEEL, STEEL_DARK, WARM,
    WOOD, WOOD_DARK, Area, Surfaces, barrel_spot, bench, boundary, building, carve, crate,
    deploy_pad, flight, gable, lamp_post, plate, post_sign, rect, room_walls, sign_decal, slab,
    supply_ammo, supply_med, threshold, wall_sign)
from ..relay.kit import mound, tier_stack

Rect = Tuple[float, float, float, float]

HALF = 280.0
SKY = {"top": "#04081a", "horizon": "#1a2a4a", "sun": [0.3, 0.6, -0.5],
       "clouds": 0.15, "tint": "#a8b8e8"}
AMBIENT = "#4a5272"

SCRUB = "#5a6a3a"
SAND = "#d8c8a0"
WHITE = "#eef0f2"
BLACK = "#1a1c20"
ORANGE = "#e8682a"

PAD = [rect(-56.0, 56.0, 34.0, 146.0), rect(-46.0, 46.0, 44.0, 136.0), rect(-36.0, 36.0, 54.0, 126.0)]
DECK = 6.0
TRENCH = rect(-76.0, 76.0, 82.0, 98.0)
TRENCH_FLOOR = -8.0
MOUNT_TOP = 14.0
ROCKET = (0.0, 90.0)
TOWER = rect(22.0, 34.0, 84.0, 96.0)
SERVICE = rect(-20.0, 20.0, -12.0, 12.0)
BLOCK = rect(-150.0, -100.0, -60.0, -20.0)
BLOCK_H = 12.0
HANGAR = rect(-40.0, 40.0, -220.0, -160.0)
CANAL = rect(-280.0, -256.0, -280.0, 280.0)
CANAL_BED = -4.0
OCEAN = rect(262.0, 280.0, -280.0, 280.0)
FARM = rect(-230.0, -110.0, 130.0, 210.0)
PRESS = rect(120.0, 180.0, -100.0, -82.0)
SWALE = rect(-256.0, -150.0, -196.0, -186.0)


def build(b: Area) -> None:
    rng = random.Random(0x1A9C)
    b.extra.update({"weather": "moths", "accent": "#e8682a"})
    s = Surfaces(b)
    _ground(b, s)
    boundary(b, 30.0, "#1a2218", "#161c14", rng, horizon="forest")
    _water(b)
    _pad(b, s)
    _rocket(b)
    _tower(b)
    _service(b, s)
    _blockhouse(b, s)
    _fuel_farm(b, s)
    _hangar(b, s)
    _press(b, s)
    _bunkers(b, s)
    _coast(b, s, rng)
    _scrub(b, s, rng)
    _country(b, s, rng)
    _paths(b, s)
    _rigs(b)
    _zombie_spawns(b)
    for x, z, name in ((-125, -40, "the blockhouse"), (0, 60, "the launch pad"),
                       (-66, 90, "the flame trench"), (28, 74, "the umbilical tower"),
                       (0, 0, "the service structure"), (-170, 170, "the fuel farm"),
                       (0, -190, "the hangar"), (150, -92, "the press site"),
                       (155, -64, "the countdown clock"), (180, 200, "the radar"),
                       (250, 0, "the beach"), (220, 80, "the dunes"), (-268, 0, "the canal"),
                       (0, -80, "the crawlerway"), (90, 60, "the camera bunker"),
                       (-90, 130, "the north bunker")):
        b.landmark(float(x), float(z), name)
    b.camera(-80.0, 30.0, -30.0, 0.0, 40.0, 90.0)
    b.camera(60.0, 12.0, 40.0, 0.0, 24.0, 90.0)
    b.camera(-150.0, 14.0, -110.0, -125.0, 6.0, -40.0)
    b.camera(200.0, 14.0, -40.0, 260.0, 0.0, 20.0)


# ================================================================ ground
def _ground(b: Area, s: Surfaces) -> None:
    h = b.half + b.margin
    holes = [TRENCH, CANAL, OCEAN, SWALE]
    for r in holes:
        s.reserve(r)
    pieces = carve(rect(-h, h, -h, h), holes)
    plate(b, pieces, 0.0, 0.6, SCRUB, studs=True, material="grass")
    plate(b, pieces, -0.6, 5.4, "#6a5a40")


def _water(b: Area) -> None:
    """The drainage canal along the west edge; the ocean coming in on the
    east, its bed shelving down from the beach."""
    slab(b, CANAL, CANAL_BED, 6.0 + CANAL_BED, "#3a3a2a", studs=True)
    b.water((CANAL[0] + CANAL[1]) / 2.0, 0.0, CANAL[1] - CANAL[0], CANAL[3] - CANAL[2], -1.4, "#2a3a2a")
    flight(b, "x", -262.0, -256.0, -10.0, -2.0, CANAL_BED, 0.0, CONCRETE_DARK, fill=CANAL_BED)
    slab(b, SWALE, -2.0, 4.0, "#3a3a2a", studs=True)
    b.water((SWALE[0] + SWALE[1]) / 2.0, (SWALE[2] + SWALE[3]) / 2.0, SWALE[1] - SWALE[0], SWALE[3] - SWALE[2],
            -1.0, "#2a3a2a")
    ox0, ox1, oz0, oz1 = OCEAN
    plate(b, [rect(ox0, 270.0, oz0, oz1)], -1.2, 4.8, SAND, studs=True)
    plate(b, [rect(270.0, ox1, oz0, oz1)], -2.6, 3.4, "#c8b890", studs=True)
    b.water((ox0 + ox1) / 2.0, 0.0, ox1 - ox0, oz1 - oz0, -0.4, "#1a3a5a")


# ================================================================== pad
def _pad(b: Area, s: Surfaces) -> None:
    """The pad: three concrete tiers to the deck, the flame trench through
    it and out both ends, stairs out of the trench, the launch mount on its
    legs over the trench, the control panel (the lure)."""
    s.reserve(PAD[0])
    for k, r in enumerate(PAD):
        plate(b, carve(r, [TRENCH]), 2.0 * (k + 1), 2.0, [CONCRETE, CONCRETE_LIGHT, CONCRETE][k], studs=True)
    tx0, tx1, tz0, tz1 = TRENCH
    slab(b, TRENCH, TRENCH_FLOOR, 2.0, CONCRETE_DARK, studs=True)
    for (z0, z1) in ((tz0 - 6.0, tz0), (tz1, tz1 + 6.0)):
        slab(b, rect(tx0, tx1, z0, z1), -6.0, 4.0, CONCRETE_DARK)
    flight(b, "x", 60.0, tx1, tz0, tz1, TRENCH_FLOOR, 0.0, CONCRETE_DARK, fill=TRENCH_FLOOR)
    flight(b, "x", -60.0, tx0, tz0, tz1, TRENCH_FLOOR, 0.0, CONCRETE_DARK, fill=TRENCH_FLOOR)
    # the deflector in the trench's middle, a wedge in steps
    for k in range(3):
        b.box([0.0, TRENCH_FLOOR + 0.75 + k * 1.5, 90.0], [14.0 - k * 4.0, 1.5, tz1 - tz0], "#8a6a5a")
    # the mount: a deck over the trench on four legs, the hole for the engines
    mx = rect(-12.0, 12.0, 78.0, 102.0)
    plate(b, carve(mx, [rect(-7.0, 7.0, 83.0, 97.0)]), MOUNT_TOP, 4.0, STEEL_DARK, studs=True,
          material="metal")
    for x in (-10.0, 10.0):
        for (z0, z1) in ((78.0, 82.0), (98.0, 102.0)):
            b.box([x, (DECK + MOUNT_TOP - 4.0) / 2.0, (z0 + z1) / 2.0], [3.0, MOUNT_TOP - 4.0 - DECK, z1 - z0],
                  STEEL_DARK, material="metal")
    # the pad's control panel at the tower's foot, and the lure on it
    b.box([18.0, DECK + 1.6, 72.0], [6.0, 3.2, 2.4], "#4a5060", material="metal")
    b.box([18.0, DECK + 3.4, 72.4], [5.6, 0.4, 1.6], "#2a2e36")
    b.set_lure(18.0, DECK, 69.0, "the countdown", "Resume the countdown", "ll_countdown",
               (0.0, TRENCH_FLOOR, 90.0))
    wall_sign(b, 18.0, DECK + 1.6, 70.45, 5.0, 1.6, sign_decal("PAD 9 ARM", "#4a5060", "#f2d23a", 3.1), "z-",
              "#4a5060")
    supply_ammo(b, -24.0, DECK, 64.0, "x+")
    supply_med(b, 24.0, DECK, 116.0, "z-")
    barrel_spot(b, -30.0, DECK, 120.0)
    barrel_spot(b, 40.0, 4.0, 50.0)


def _rocket(b: Area) -> None:
    """The moon rocket: three stages, white and black, the capsule and its
    escape tower, fins at the base; on the mount over the trench."""
    x, z = ROCKET
    y = MOUNT_TOP
    for (h, r, c) in ((6.0, 6.6, WHITE), (6.0, 6.6, BLACK), (14.0, 6.6, WHITE), (2.0, 6.8, BLACK),
                      (10.0, 6.3, WHITE), (6.0, 6.3, BLACK), (4.0, 6.3, WHITE), (2.0, 5.4, CONCRETE_LIGHT),
                      (8.0, 4.4, WHITE), (4.0, 4.4, BLACK)):
        b.cyl([x, y + h / 2.0, z], [r * 2.0, h, r * 2.0], c, material="metal")
        y += h
    b.cone([x, y + 3.0, z], [8.0, 6.0, 8.0], WHITE, material="metal")
    y += 6.0
    b.box([x, y + 4.0, z], [0.8, 8.0, 0.8], ORANGE)
    b.cone([x, y + 8.6, z], [1.6, 1.2, 1.6], ORANGE)
    for (dx, dz, w, d) in ((7.6, 0.0, 2.6, 0.8), (-7.6, 0.0, 2.6, 0.8), (0.0, 7.6, 0.8, 2.6), (0.0, -7.6, 0.8, 2.6)):
        b.box([x + dx, MOUNT_TOP + 4.0, z + dz], [w, 8.0, d], BLACK)


def _tower(b: Area) -> None:
    """The umbilical tower beside it: four legs to the top, bracing high up,
    the swing arms across to the rocket, the hammerhead crane."""
    x0, x1, z0, z1 = TOWER
    top = 84.0
    for x in (x0 + 1.0, x1 - 1.0):
        for z in (z0 + 1.0, z1 - 1.0):
            b.box([x, (DECK + top) / 2.0, z], [2.0, top - DECK, 2.0], ORANGE, material="metal")
    for k in range(6):
        y = 16.0 + k * 12.0
        slab(b, rect(x0 + 2.0, x1 - 2.0, z0, z1), y, 0.6, STEEL_DARK, material="metal")
    slab(b, rect(x0 - 4.0, x1 + 4.0, z0 - 4.0, z1 + 4.0), top + 1.2, 1.2, ORANGE, material="metal")
    b.box([(x0 + x1) / 2.0 - 10.0, top + 1.8, (z0 + z1) / 2.0], [36.0, 1.2, 1.6], ORANGE, material="metal")
    for (y, reach) in ((30.0, 6.4), (50.0, 6.2), (70.0, 4.4)):
        b.box([(x0 + ROCKET[0] + reach) / 2.0, y, ROCKET[1]], [x0 - ROCKET[0] - reach, 1.4, 3.0], STEEL,
              material="metal")


def _service(b: Area, s: Surfaces) -> None:
    """The mobile service structure, rolled back off the pad onto its rails:
    three decks stepping up, stairs between them on the outside -- the
    best view on the complex."""
    s.reserve(rect(-42.0, 22.0, -14.0, 14.0))
    x0, x1, z0, z1 = SERVICE
    for x in (-16.0, 16.0):
        b.box([x, 0.35, -11.0], [1.2, 0.7, 90.0], STEEL_DARK, material="metal")
    decks = [(rect(x0, x1, z0, z1), 10.0), (rect(x0, x1, z0, 0.0), 20.0), (rect(x0, 0.0, z0, 0.0), 30.0)]
    for r, top in decks:
        slab(b, r, top, 0.6, "#8a8f94", studs=True, material="metal")
    for (x, z) in ((x0 + 0.6, z0 + 0.6), (x1 - 0.6, z0 + 0.6), (x0 + 0.6, z1 - 0.6), (x1 - 0.6, z1 - 0.6),
                   (x0 + 0.6, 0.0), (x1 - 0.6, 0.0)):
        b.box([x, (10.0 - 0.6) / 2.0, z], [1.2, 10.0 - 0.6, 1.2], "#c8382a", material="metal")
    for (x, z) in ((x0 + 0.6, z0 + 0.6), (x1 - 0.6, z0 + 0.6), (x0 + 0.6, -0.6), (x1 - 0.6, -0.6)):
        b.box([x, 10.0 + (10.0 - 0.6) / 2.0, z], [1.2, 10.0 - 0.6, 1.2], "#c8382a", material="metal")
    for (x, z) in ((x0 + 0.6, z0 + 0.6), (-0.6, z0 + 0.6), (x0 + 0.6, -0.6), (-0.6, -0.6)):
        b.box([x, 20.0 + (10.0 - 0.6) / 2.0, z], [1.2, 10.0 - 0.6, 1.2], "#c8382a", material="metal")
    flight(b, "x", -40.0, x0, z0, z0 + 6.0, 0.0, 10.0, STEEL_DARK, fill=0.0)
    flight(b, "z", 10.0, 0.0, 8.0, 14.0, 10.0, 20.0, STEEL_DARK, fill=10.0)
    flight(b, "x", 16.0, 0.0, -12.0, -6.0, 20.0, 30.0, STEEL_DARK, fill=20.0)
    for (a, c, d, e, y) in ((x0, x1, z1 - 0.6, z1, 10.0), (x0, -0.6, -0.6, 0.0, 30.0),
                            (x0, x0 + 0.6, z0, -0.6, 30.0)):
        b.box([(a + c) / 2.0, y + 0.6, (d + e) / 2.0], [c - a, 1.2, e - d], HAZARD)
    supply_ammo(b, -10.0, 30.0, -6.0, "z+")
    barrel_spot(b, -10.0, 10.0, 6.0)


def _blockhouse(b: Area, s: Surfaces) -> None:
    """The blockhouse: concrete walls, a stepped dome, periscopes through
    the top, slits of blast glass facing the pad; inside, the consoles; the
    blast door round behind its baffle wall."""
    x0, x1, z0, z1 = BLOCK
    s.reserve(rect(x0 - 2.0, x1 + 2.0, z0 - 14.0, z1 + 2.0))
    building(b, BLOCK, 0.0, BLOCK_H, CONCRETE, roof_colour=CONCRETE_LIGHT, floor_colour="#6a6a6a",
             doors={"z-": [(-130.0, -120.0, 9.0)]},
             windows={"z+": [(-142.0, -134.0, 6.0, 8.0), (-129.0, -121.0, 6.0, 8.0), (-116.0, -108.0, 6.0, 8.0)]},
             glass=True, lights="#e8f2ff")
    threshold(b, BLOCK, "z-", (-130.0, -120.0))
    for k in range(4):
        inset = 4.0 + k * 4.0
        slab(b, rect(x0 + inset, x1 - inset, z0 + inset, z1 - inset), BLOCK_H + 1.2 + 2.0 * (k + 1), 2.0,
             CONCRETE_LIGHT)
    top = BLOCK_H + 1.2 + 8.0
    for (x, z) in ((-130.0, -38.0), (-120.0, -42.0)):
        b.box([x, top + 1.5, z], [1.2, 3.0, 1.2], STEEL_DARK)
        b.box([x, top + 3.4, z + 0.6], [1.4, 0.8, 2.4], STEEL_DARK)
    # the baffle in front of the door
    b.box([-125.0, 4.0, z0 - 11.0], [24.0, 8.0, 2.0], CONCRETE_DARK)
    wall_sign(b, -125.0, 6.0, z0 - 12.35, 16.0, 2.2, sign_decal("BLOCKHOUSE 9", CONCRETE_DARK, "#f2d23a", 7.3),
              "z-", CONCRETE_DARK)
    floor = FLOOR
    for z in (-50.0, -40.0):
        for k in range(8):
            x = -144.0 + k * 5.6
            deploy_pad(b, x, z, floor, "#e8682a", 4.6)
            b.safe_spawn(x, floor + 0.6, z, 0.0)
    # the consoles along the north wall, facing the slits
    for x in (-142.0, -129.0, -116.0):
        b.box([x, floor + 1.4, -27.0], [10.0, 2.8, 3.0], "#5a6070")
        b.box([x, floor + 3.2, -26.0], [10.0, 0.8, 1.0], "#3a4050")
    for (x, z) in ((-104.0, -56.0), (-146.0, -56.0)):
        crate(b, x, floor, z, 3.0, "#5a5a50")
    supply_ammo(b, -106.0, floor, -30.0, "x-")
    supply_med(b, -110.0, floor, -56.6, "z+")


def _fuel_farm(b: Area, s: Surfaces) -> None:
    """The fuel farm: the liquid oxygen sphere on its legs, the kerosene
    tanks, the pipes, low berms round it all with gaps to come in by."""
    x0, x1, z0, z1 = FARM
    s.reserve(FARM)
    for (a, c, d, e) in ((x0, x1, z0, z0 + 6.0), (x0, x1, z1 - 6.0, z1), (x0, x0 + 6.0, z0 + 6.0, z1 - 6.0),
                         (x1 - 6.0, x1, z0 + 6.0, z1 - 6.0)):
        pieces = carve(rect(a, c, d, e), [rect(-180.0, -160.0, z0 - 1.0, z0 + 7.0), rect(x1 - 7.0, x1 + 1.0, 160.0, 180.0)])
        plate(b, pieces, 1.6, 1.6, "#5a6a3a", studs=True, material="grass")
    sx, sz = -150.0, 170.0
    b.sphere([sx, 16.0, sz], [24.0, 24.0, 24.0], WHITE, material="metal")
    for k in range(6):
        a = k / 6.0 * math.pi * 2.0
        b.box([sx + math.cos(a) * 9.0, 3.3, sz + math.sin(a) * 9.0], [1.4, 6.6, 1.4], STEEL_DARK)
    for (tx, tz) in ((-200.0, 150.0), (-200.0, 190.0)):
        b.cyl([tx, 8.0, tz], [14.0, 16.0, 14.0], "#c8c8c0", material="metal")
        b.cyl([tx, 16.4, tz], [12.0, 0.8, 12.0], STEEL_DARK)
    b.box([-175.0, 0.8, 170.0], [22.0, 1.6, 1.6], STEEL, material="metal")
    b.box([-120.0, 0.8, 170.0], [12.0, 1.6, 1.6], STEEL, material="metal")
    post_sign(b, -150.0, 152.0, 0.0, 3.0, 10.0, 1.6, sign_decal("LOX  NO SMOKING", WHITE, "#c8382a", 6.3), "z-", WHITE)
    supply_ammo(b, -125.0, 0.0, 195.0, "z-")
    barrel_spot(b, -215.0, 0.0, 170.0)
    barrel_spot(b, -180.0, 0.0, 146.0)


def _hangar(b: Area, s: Surfaces) -> None:
    """The assembly hangar: the big door open to the crawlerway, a stage
    lying on its transporter, the gantry crane, and in a corner on a crate,
    the chimp in his little suit."""
    x0, x1, z0, z1 = HANGAR
    s.reserve(rect(x0 - 2.0, x1 + 2.0, z0 - 2.0, z1 + 2.0))
    building(b, HANGAR, 0.0, 22.0, "#c8ccd0", roof_colour="#8a9098", floor_colour="#8a8a86",
             doors={"z+": [(-30.0, 30.0, 18.0)], "x-": [(-196.0, -186.0, 9.0)]},
             windows={"x+": [(-212.0, -200.0, 12.0, 18.0), (-184.0, -172.0, 12.0, 18.0)]},
             glass=True, lights="#e8f2ff")
    threshold(b, HANGAR, "z+", (-30.0, 30.0))
    threshold(b, HANGAR, "x-", (-196.0, -186.0))
    gable(b, HANGAR, 22.0 + 1.2, "#8a9098", "x", tiers=4, rise=2.0)
    wall_sign(b, 0.0, 20.0, z1 + 0.35, 40.0, 3.0, sign_decal("HANGAR AF  ASSEMBLY", "#c8ccd0", "#1a2a5a", 13.3),
              "z+", "#c8ccd0")
    floor = FLOOR
    b.box([0.0, floor + 1.4, -195.0], [44.0, 2.8, 8.0], STEEL_DARK, material="metal")
    b.box([0.0, floor + 2.8 + 4.6, -195.0], [40.0, 9.2, 9.2], WHITE, material="metal")
    for dx in (-12.0, 4.0):
        b.box([dx, floor + 2.8 + 4.6, -195.0], [3.0, 9.4, 9.4], BLACK, material="metal")
    b.box([-21.0, floor + 2.8 + 4.6, -195.0], [2.0, 6.0, 6.0], "#5a5f66", material="metal")
    for x in (-34.0, 34.0):
        b.box([x, 9.0, -175.0], [1.6, 18.0, 1.6], ORANGE)
    b.box([0.0, 18.6, -175.0], [69.6, 1.2, 1.6], ORANGE)
    crate(b, 32.0, floor, -214.0, 4.0, "#6a6a5a")
    crate(b, 27.5, floor, -214.0, 4.0, "#5a5a4a")
    supply_ammo(b, -30.0, floor, -214.0, "z+")
    supply_med(b, 34.6, floor, -200.0, "x-")
    barrel_spot(b, 30.0, 0.0, -150.0)
    barrel_spot(b, -30.0, 0.0, -150.0)


def _press(b: Area, s: Surfaces) -> None:
    """The press site: bleachers facing the pad, and the countdown clock on
    its posts (the clock's face is a rig: it still says HOLD)."""
    x0, x1, z0, z1 = PRESS
    s.reserve(rect(x0 - 2.0, x1 + 2.0, z0 - 2.0, -52.0))
    tier_stack(b, [[rect(x0, x1, z0, z1)], [rect(x0, x1, z0, z1 - 6.0)], [rect(x0, x1, z0, z1 - 12.0)]], 0.0,
               [1.6], ["#b6bcc1", "#9aa0a6"])
    for x in (136.0, 174.0):
        b.box([x, 8.0, -64.0], [1.2, 16.0, 1.2], STEEL_DARK)
    b.box([155.0, 18.0, -64.0], [40.0, 8.0, 1.4], "#1a1a1e")
    wall_sign(b, 155.0, 22.8, -64.35, 18.0, 1.6, sign_decal("COUNTDOWN", "#1a1a1e", "#e8e8e8", 11.2), "z-",
              "#1a1a1e")
    supply_ammo(b, 128.0, 4.8, -96.0, "z+")
    barrel_spot(b, 186.0, 0.0, -70.0)


def _bunkers(b: Area, s: Surfaces) -> None:
    """The camera bunkers round the pad: little domed boxes with a slot to
    film through, a door at the back."""
    for (cx, cz, facing) in ((90.0, 60.0, "x-"), (-90.0, 130.0, "x+")):
        r = rect(cx - 8.0, cx + 8.0, cz - 6.0, cz + 6.0)
        s.reserve(rect(cx - 9.0, cx + 9.0, cz - 7.0, cz + 7.0))
        back = "x+" if facing == "x-" else "x-"
        building(b, r, 0.0, 7.0, CONCRETE, roof_colour=CONCRETE_LIGHT, floor_colour="#6a6a6a",
                 doors={back: [(cz - 4.0, cz + 4.0, 6.0)]},
                 windows={facing: [(cz - 3.0, cz + 3.0, 3.6, 4.6)]}, glass=True, lights="#e8f2ff")
        threshold(b, r, back, (cz - 4.0, cz + 4.0))
        slab(b, rect(cx - 5.0, cx + 5.0, cz - 3.0, cz + 3.0), 7.0 + 1.2 + 1.6, 1.6, CONCRETE_LIGHT)
    supply_med(b, 90.0, FLOOR, 62.6, "z-")


def _coast(b: Area, s: Surfaces, rng: random.Random) -> None:
    """The dunes along the beach, sea oats on them; the beach; a lifeguard
    stand nobody used."""
    s.lay(rect(240.0, OCEAN[0], -280.0, 280.0), 0.3, SAND, studs=True)
    for (cz, rz) in ((-200.0, 26.0), (-120.0, 22.0), (-40.0, 28.0), (60.0, 30.0), (150.0, 24.0), (230.0, 26.0)):
        s.reserve(rect(206.0, 238.0, cz - rz, cz + rz))
        mound(b, 222.0, cz, 16.0, rz, 3, 1.6, ["#d8c8a0", "#c8b890", "#b8a880"])
    for (x, z) in ((244.0, -80.0), (244.0, 100.0)):
        for dx in (-1.6, 1.6):
            for dz in (-1.6, 1.6):
                b.box([x + dx, 0.3 + 3.0, z + dz], [0.5, 6.0, 0.5], WOOD)
        slab(b, rect(x - 2.4, x + 2.4, z - 2.4, z + 2.4), 6.3 + 0.4, 0.4, WOOD, studs=True)
    supply_ammo(b, 250.0, 0.3, 10.0, "x-")
    barrel_spot(b, 250.0, 0.3, -30.0)


def _country(b: Area, s: Surfaces, rng: random.Random) -> None:
    """The radar on its tower, palmettos in the scrub, floodlight masts."""
    rx, rz = 180.0, 200.0
    s.reserve(rect(rx - 8.0, rx + 8.0, rz - 8.0, rz + 8.0))
    for dx in (-5.0, 5.0):
        for dz in (-5.0, 5.0):
            b.box([rx + dx, 10.0, rz + dz], [1.2, 20.0, 1.2], STEEL_DARK)
    slab(b, rect(rx - 7.0, rx + 7.0, rz - 7.0, rz + 7.0), 20.8, 0.8, STEEL, material="metal")
    b.box([rx, 22.0, rz], [3.0, 2.4, 3.0], "#e8e8e8")
    for (x, z) in ((-60.0, 220.0), (120.0, 140.0), (-200.0, 40.0), (-220.0, -80.0),
                   (-80.0, -150.0), (100.0, -240.0), (-160.0, -230.0), (140.0, 60.0), (-40.0, -260.0)):
        _palmetto(b, x, z, rng.uniform(0.9, 1.3))
    for (x, z) in ((-70.0, 30.0), (70.0, 30.0), (-70.0, 150.0), (70.0, 150.0)):
        b.cyl([x, 13.0, z], [1.8, 26.0, 1.8], STEEL_DARK, material="metal")
        b.box([x, 27.4, z], [6.0, 2.8, 4.0], STEEL, material="metal")
    for (x, z) in ((-120.0, -112.0), (-40.0, -112.0), (60.0, -112.0), (160.0, -112.0)):
        lamp_post(b, x, z, h=12.0, light=WARM)


def _scrub(b: Area, s: Surfaces, rng: random.Random) -> None:
    """The ground isn't flat: blast berms round the pad (gaps for the
    crawlerway and the trench mouths), hummocks of scrub with palmettos on
    them across the open ground."""
    for (a, c, d, e) in ((58.0, 66.0, 20.0, 70.0), (58.0, 66.0, 110.0, 164.0), (-66.0, -58.0, 20.0, 70.0),
                         (-66.0, -58.0, 110.0, 164.0), (-66.0, -24.0, 168.0, 178.0), (24.0, 66.0, 168.0, 178.0)):
        s.reserve(rect(a, c, d, e))
        tier_stack(b, [[rect(a, c, d, e)], [rect(a + 2.0, c - 2.0, d + 2.0, e - 2.0)]], 0.0, [1.5],
                   ["#5a6a3a", "#6a7a44"])
    for (cx, cz, rx, rz) in ((110.0, -20.0, 20.0, 14.0), (-60.0, -90.0, 18.0, 14.0), (-200.0, -10.0, 24.0, 18.0),
                             (60.0, 222.0, 22.0, 16.0), (-40.0, 250.0, 20.0, 14.0), (150.0, 120.0, 18.0, 16.0),
                             (-226.0, 250.0, 18.0, 14.0), (110.0, -190.0, 20.0, 16.0), (-196.0, 80.0, 16.0, 12.0)):
        s.reserve(rect(cx - rx, cx + rx, cz - rz, cz + rz))
        top = mound(b, cx, cz, rx, rz, 2, 1.2, ["#5a6a3a", "#66763e"])
        _palmetto(b, cx + rng.uniform(-3.0, 3.0), cz + rng.uniform(-2.0, 2.0), rng.uniform(0.9, 1.2), top)


def _palmetto(b: Area, x: float, z: float, sc: float, y: float = 0.0) -> None:
    """A cabbage palm: a ringed trunk and a burst of fronds up top."""
    h = 10.0 * sc
    b.cyl([x, y + h / 2.0, z], [1.4 * sc, h, 1.4 * sc], "#7a6a52")
    for k in range(7):
        yaw = k / 7.0 * math.pi * 2.0
        b.box([x + math.sin(yaw) * 2.4 * sc, y + h + 0.2, z + math.cos(yaw) * 2.4 * sc], [1.6 * sc, 0.2, 5.0 * sc],
              "#3a6a2a", r=[0, yaw, 0], collide=False)
    b.sphere([x, y + h + 0.4, z], [2.0 * sc, 1.6 * sc, 2.0 * sc], "#4a7a2a", collide=False)


def _paths(b: Area, s: Surfaces) -> None:
    for r in (rect(-14.0, -4.0, -160.0, 34.0), rect(4.0, 14.0, -160.0, 34.0)):
        s.lay(r, 0.3, "#9a968a", studs=True)
    for r in (rect(-256.0, 240.0, -128.0, -118.0), rect(-130.0, -120.0, -118.0, -74.0),
              rect(140.0, 150.0, -118.0, -102.0), rect(-110.0, -100.0, -14.0, 120.0),
              rect(-160.0, -110.0, 118.0, 126.0)):
        s.lay(r, 0.3, ASPHALT, studs=False)


# ================================================================ rigs
def _rigs(b: Area) -> None:
    x, z = ROCKET
    b.rig("rocket_launch", x, MOUNT_TOP, z, 0.0, trench=TRENCH_FLOOR, tx0=TRENCH[0], tx1=TRENCH[1], r=6.6)
    b.rig("searchlights", 0.0, 0.0, 90.0, 0.0, lights=[[-70.0, 30.0], [70.0, 30.0], [-70.0, 150.0], [70.0, 150.0]],
          aim=[0.0, 50.0, 90.0], y0=27.0)
    b.rig("countdown_clock", 155.0, 18.0, -64.8, math.pi, w=38.0, h=7.0)
    b.rig("radar_dish", 180.0, 23.2, 200.0, 0.0)
    b.rig("beacons", 0.0, 0.0, 0.0, 0.0,
          points=[[28.0, 86.0, 90.0], [-150.0, 28.4, 170.0], [180.0, 26.0, 200.0], [0.0, 98.0, 90.0]])
    b.rig("gators", -268.0, -1.4, 0.0, 0.0, area=[-276.0, -260.0, -240.0, 240.0], n=4)
    b.rig("surf", 266.0, -0.4, 0.0, 0.0, z0=-276.0, z1=276.0)
    b.rig("pelicans", 230.0, 40.0, 0.0, 0.0)
    b.rig("space_chimp", 32.0, FLOOR + 4.0, -214.0, math.pi)
    b.rig("moth_swarm", -120.0, 10.0, -112.0, 0.0)


# ============================================================== spawns
def _zombie_spawns(b: Area) -> None:
    for (x, z) in ((-268.0, 200.0), (-268.0, 80.0), (-268.0, -150.0), (-268.0, -250.0)):
        b.zombie_spawn(x, z, "water", y=CANAL_BED)
    for (x, z) in ((272.0, 220.0), (272.0, 120.0), (272.0, -60.0), (272.0, -180.0)):
        b.zombie_spawn(x, z, "water", y=-2.6)
    for (x, z) in ((-200.0, 272.0), (-80.0, 272.0), (40.0, 272.0), (130.0, 272.0), (240.0, 272.0),
                   (-240.0, -272.0), (-100.0, -272.0), (90.0, -272.0), (200.0, -272.0), (200.0, 250.0),
                   (-240.0, 120.0), (100.0, 230.0), (-30.0, 200.0), (60.0, 180.0), (150.0, 10.0),
                   (180.0, -180.0), (-200.0, -170.0), (-60.0, -250.0)):
        b.zombie_spawn(x, z, "")
