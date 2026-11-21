"""Big Ear Array -- a radio telescope array in the high desert, at night.

The array listens to the sky, and tonight it is listening to you: every dish
on the field turns, all together, to point at whoever is carrying a flag
(static/js/worlds/blackout_relay_rigs.js), so where the carrier is is
written across the whole sky for both teams to read.  With no flag out they
go back to what they were doing -- following the light that has been
hanging over the corral since dusk.

Both teams muster in the control building at the hub.  Two arms of rail
run out from it east and west, dish stations along them, to the receiver
houses at the ends where the flags are.  North of the hub stands the Big
Ear itself on its stepped pedestal; south is the mesa with its mast.

Layout (red to the west; mirrored about x = 0)::

      z +150  ......... the corral, the windpump, the light in the sky .........
      z  +76  MAINT. SHED (outpost)    THE BIG EAR (pedestal)    (and theirs)
      z    0  RECEIVER ==dish==dish== |arroyo| ==dish== CONTROL BLDG == ...
      z  -21  ====== cable duct: receiver house -> culvert in the arroyo ======
      z -120  TRAILER (outpost)  cacti, outcrops   THE MESA + mast
      z -200  ============================================================

The arroyo is a dry wash six deep that crosses each half north to south,
under the rail trestle; the cable duct runs from a stair beside each flag
to a culvert in its outer bank.
"""
from __future__ import annotations

import math
import random

from . import kit
from .kit import (Half, carve, halves, holed_wall, rect, room_walls, slab, strip_light)

HALF = (310.0, 200.0)
SKY = {"top": "#04050c", "horizon": "#26244a", "sun": [-0.35, 0.55, 0.3],
       "clouds": 0.08, "tint": "#a8b8ff"}
AMBIENT = "#6a6c8a"
GROUND = "#a8865a"
FOG = 900.0

SAND = "#b8925e"
SAND_LIGHT = "#c8a46c"
SAND_DARK = "#9a784c"
ROCK = "#a0644a"
ROCK_DARK = "#7a4a36"
CONCRETE = "#c8c8c0"
CONCRETE_DARK = "#9a9a94"
STEEL = "#b8bec6"
METAL_SHED = "#c8ccd0"
SCREEN = "#7aff9a"
CACTUS = "#3a7a3e"
AMBER = "#ffb84a"

HUB = (40.0, 24.0)
HUB_H = 12.0
ARROYO_X = (108.0, 126.0)
ARROYO_DEPTH = 6.0
DUCT_Z = (-26.0, -16.0)
DUCT_X = (126.0, 276.0)
DUCT_FLOOR = -7.0
DUCT_STAIR = (262.0, 276.0)
HOUSE = (240.0, 296.0, -30.0, 30.0)
HOUSE_H = 14.0
FLAG_X = 268.0
STATIONS = (64.0, 160.0, 214.0)
RAIL_Z = 4.0
BIG_EAR = (0.0, 76.0)


def build(b: kit.RelayArea) -> None:
    rng = random.Random(0xB1E4)
    b.relay("the Control Building", 46.0)
    b.intro = ["Big Ear Array -- a radio telescope field in the desert, at night.",
               "Muster in the control building; the flags are in the receiver houses at the "
               "ends of the rails. Every dish on the field turns to follow a carried flag.",
               "A dry arroyo crosses each half; a cable duct runs from beside each flag to a "
               "culvert in the arroyo's bank."]
    b.extra.update({"accent": "#9ab8ff", "weather": "dust"})
    holes = []
    for h in halves(b):
        holes.append(h.r(ARROYO_X[0], ARROYO_X[1], -HALF[1] - b.margin, HALF[1] + b.margin))
        holes.append(h.r(DUCT_X[0], DUCT_X[1], DUCT_Z[0], DUCT_Z[1]))
    kit.ground(b, SAND, soil="#7a5a3a", holes=holes, material="")
    for h in halves(b):
        _arroyo(b, h)
        _duct(b, h)
        _rails(b, h)
        _stations(b, h)
        _receiver(b, h)
        _outposts(b, h)
        _desert(b, h, random.Random(0xDE5E))
    _hub(b)
    _big_ear(b)
    _mesa(b)
    _corral(b)
    _edge(b, rng)
    _sky(b)
    _landmarks(b)


# ================================================================ the arroyo
def _arroyo(b: kit.RelayArea, h: Half) -> None:
    """The dry wash: six deep, sandy, boulders and a cottonwood or two in
    it, steps down its banks, the rail trestle over it."""
    x0, x1 = ARROYO_X
    hz = HALF[1] + b.margin
    kit.channel(b, h.r(x0, x1, -hz, hz), ARROYO_DEPTH, SAND_DARK, studs=True)
    d = -ARROYO_DEPTH
    # steps down each bank, staggered so they never share the floor
    for z in (118.0, -132.0):
        h.flight_x(x0, x0 + 10.0, z, z + 10.0, 0.0, d, ROCK, fill=d)
    for z in (96.0, -108.0, 40.0):
        h.flight_x(x1, x1 - 10.0, z, z + 10.0, 0.0, d, ROCK, fill=d)
    # boulders and cottonwoods down the bed: cover in the wash
    for z, s in ((150.0, 1.4), (66.0, 1.2), (-44.0, 1.5), (-84.0, 1.1), (-160.0, 1.3)):
        kit.boulder(b, h.x((x0 + x1) / 2.0 + (2.0 if s > 1.25 else -2.0)), z, d, s, ROCK)
    for z in (-60.0, 136.0):
        kit.tree(b, h.x((x0 + x1) / 2.0), z, d, 1.1, "#6a5a3a", "#5a7a3a")
    # the rail trestle over it: posts at both banks
    for x in (x0 + 1.0, x1 - 1.0):
        for z in (-3.0, 3.0):
            h.box(x, d / 2.0, z, 1.6, ARROYO_DEPTH, 1.6, "#6a4a2e")


# ================================================================ the duct
def _duct(b: kit.RelayArea, h: Half) -> None:
    """The cable duct: from a stair beside the flag, under the field, out
    of a culvert in the arroyo's outer bank (a step up onto its bed)."""
    x0, x1 = DUCT_X
    z0, z1 = DUCT_Z
    area = h.r(x0, x1, z0, z1)
    mouth = "x-" if h.sx > 0 else "x+"
    kit.channel(b, area, -DUCT_FLOOR, "#4a4a50", wall_c="#5a5a60", studs=True,
                openings={mouth: [(z0, z1)]})
    well = h.r(DUCT_STAIR[0], DUCT_STAIR[1], z0, z1)
    kit.plate(b, carve(area, [well]), 0.0, 0.4, SAND, studs=True)
    h.flight_x(DUCT_STAIR[0], DUCT_STAIR[1], z0, z1, DUCT_FLOOR, 0.0, CONCRETE_DARK,
               fill=DUCT_FLOOR)
    zc = (z0 + z1) / 2.0
    # cable trays along the wall, lights every so often
    h.box((x0 + DUCT_STAIR[0]) / 2.0, DUCT_FLOOR + 4.0, z0 + 0.5, DUCT_STAIR[0] - x0 - 4.0, 0.4,
          1.0, "#2a2a30")
    for k, colour in enumerate(("#c42b20", "#2a6aa8", "#f2c21e")):
        h.box((x0 + DUCT_STAIR[0]) / 2.0, DUCT_FLOOR + 4.3, z0 + 0.5 + (k - 1) * 0.3,
              DUCT_STAIR[0] - x0 - 4.0, 0.2, 0.2, colour, collide=False)
    for x in range(int(x0) + 18, int(DUCT_STAIR[0]) - 8, 26):
        strip_light(b, h.x(float(x)), zc, -0.4, 4.0, "z", AMBER)
    # the culvert's mouth: a concrete frame in the bank
    for z in (z0 - 1.0, z1 + 1.0):
        h.box(x0 + 0.6, -3.15, z, 2.0, 5.3, 1.6, CONCRETE_DARK)
    h.box(x0 + 0.4, 0.0, zc, 2.0, 1.0, z1 - z0 + 4.0, CONCRETE_DARK)


# ================================================================ the rails
def _rails(b: kit.RelayArea, h: Half) -> None:
    """Two rails on a gravel bed from the hub to the receiver house: the
    dishes ride on them, and so do you."""
    x0, x1 = HUB[0], HOUSE[0]
    stations = [h.r(x - 10.0, x + 10.0, -10.0, 10.0) for x in STATIONS]
    kit.plate(b, carve(h.r(x0, x1, -RAIL_Z, RAIL_Z), stations), 0.6, 0.6, "#8a8a84", studs=True)
    for z in (-2.2, 2.2):
        h.box((x0 + x1) / 2.0, 0.85, z, x1 - x0, 0.5, 0.5, STEEL, material="metal", collide=False)
    for x in range(int(x0) + 4, int(x1), 8):
        if ARROYO_X[0] - 1 < x < ARROYO_X[1] + 1 or any(abs(x - sx) < 11.0 for sx in STATIONS):
            continue
        h.box(float(x), 0.66, 0.0, 1.2, 0.12, 7.0, "#5a4a3a", collide=False)


def _stations(b: kit.RelayArea, h: Half) -> None:
    """The dish stations along the rails: a stepped concrete base on the
    track, a platform under the dish you can climb to, the dish itself
    turning on its yoke (a rig) to follow the carried flag."""
    for k, x in enumerate(STATIONS):
        tiers = [[h.r(x - 10.0, x + 10.0, -10.0, 10.0)], [h.r(x - 7.0, x + 7.0, -7.0, 7.0)],
                 [h.r(x - 5.0, x + 5.0, -5.0, 5.0)]]
        kit.tier_stack(b, tiers, 0.0, [2.0], [CONCRETE_DARK, CONCRETE, CONCRETE_DARK], studs=True)
        b.rig("radio_dish", h.x(x), 6.0, 0.0, d=24.0 + k * 2.0, mast=12.0, seed=k + h.sx * 3)
        # a cable box at its foot, the station number stencilled on the base
        h.box(x + 12.0, 1.5, -6.0, 3.0, 3.0, 4.0, "#3a3a40")
        h.box(x, 1.0, -10.06, 6.0, 1.6, 0.1, "#f2f2e8", collide=False,
              decal=kit.sign_decal("%s-%d" % ("W" if h.sx < 0 else "E", k + 1), "#f2f2e8",
                                   "#2a2a30", 3.75), r=[0.0, math.pi, 0.0])


# ============================================================ receiver houses
def _receiver(b: kit.RelayArea, h: Half) -> None:
    """The receiver house at the end of the rails: corrugated metal, the
    team's stripe round it, the flag inside among the racks, the duct's
    stair beside it -- and the lattice mast outside, blinking."""
    x0, x1, z0, z1 = HOUSE
    top = HOUSE_H
    area = h.r(x0, x1, z0, z1)
    room_walls(b, area, 2.0, 0.0, top, METAL_SHED, material="metal",
               doors={h.inward: [(-8.0, 8.0, 10.0)],
                      "z-": [(*h.xs(250.0, 262.0), 9.0)], "z+": [(*h.xs(250.0, 262.0), 9.0)],
                      h.outward: [(6.0, 14.0, 9.0)]})
    slab(b, h.r(x0 - 1.0, x1 + 1.0, z0 - 1.0, z1 + 1.0), top + 1.2, 1.2, "#8a8e94", studs=True)
    # the team's stripe round the walls, ribs of the corrugation
    for z in (z0 - 0.06, z1 + 0.06):
        h.box((x0 + x1) / 2.0, 11.5, z, x1 - x0 - 0.2, 1.4, 0.1, h.colour, collide=False)
    for x in (x0 - 0.06, x1 + 0.06):
        h.box(x, 11.5, 0.0, 0.1, 1.4, z1 - z0 - 0.2, h.colour, collide=False)
    # inside: racks of receivers either side, blinking; the flag in the middle
    for xx in (248.0, 286.0):
        for sz in (-1, 1):
            h.box(xx, 4.0, sz * 22.0, 4.0, 8.0, 8.0, "#2a2e36", studs=True)
            # (lights on the face towards the flag)
            b.rig("rack_lights", h.x(xx + (2.06 if xx < 268 else -2.06)), 4.0, sz * 22.0,
                  yaw=h.yaw_out if xx < 268 else h.yaw_in, seed=xx + sz)
    top_y = kit.pedestal(b, h.x(FLAG_X), 0.0, 0.0, h.colour, h.neon, base=CONCRETE_DARK)
    b.flag(h.team, h.x(FLAG_X), top_y, 0.0)
    strip_light(b, h.x((x0 + x1) / 2.0), 0.0, top, 46.0, "x", "#d8f0ff")
    # the duct stair's well, railed
    sx0, sx1 = DUCT_STAIR
    tz0, tz1 = DUCT_Z
    h.box(sx0 - 0.6, 1.5, (tz0 + tz1) / 2.0, 1.2, 3.0, tz1 - tz0, STEEL, material="metal")
    h.box((sx0 + sx1) / 2.0, 1.5, tz1 + 0.6, sx1 - sx0 - 2.4, 3.0, 1.2, STEEL, material="metal")
    # small dishes on the roof, turning with the big ones
    for xx, zz in ((250.0, 18.0), (284.0, -18.0)):
        b.rig("radio_dish", h.x(xx), top + 2.4, zz, d=6.0, mast=2.0, seed=xx + h.sx)
    # the lattice mast: four legs, its warning lights blinking
    mx, mz = 282.0, 52.0
    for dx in (-2.0, 2.0):
        for dz in (-2.0, 2.0):
            h.box(mx + dx, 30.0, mz + dz, 0.8, 60.0, 0.8, "#d8d8d8", material="metal")
    for k in range(6):
        h.box(mx, 6.0 + k * 10.0, mz, 4.8, 0.6, 4.8, "#d8d8d8", material="metal", collide=False)
    for k, y in enumerate((30.0, 61.0)):
        b.rig("blinker", h.x(mx), y, mz, c="#ff3020", period=1.6, seed=k * 0.4 + h.sx)
    banner = kit.banner_mast
    banner(b, h.x(x0 - 8.0), -40.0, 0.0, 24.0, h.team, h.inward)
    # the generator shed and its fuel tank: cover by the door
    h.box(232.0, 4.0, 44.0, 12.0, 8.0, 10.0, "#6a6e74", studs=True)
    h.cyl(232.0, 3.0, 58.0, 8.0, 6.0, 8.0, "#e8e8e0")
    b.rig("blinker", h.x(232.0), 8.4, 44.0, c="#7aff7a", period=2.2, seed=h.sx * 2.0)
    h.car(220.0, -52.0, "x", "#c8c0a8")


# ================================================================== outposts
def _outposts(b: kit.RelayArea, h: Half) -> None:
    """The maintenance shed (north) and the astronomers' trailer (south),
    where a team falls back to while its flag is away.  The trailer has the
    printout on its wall: WOW!"""
    kit.outpost_room(h, 160.0, 200.0, 96.0, 132.0, 0.0, "#9aa0a8", "#6a7078", height=11.0,
                     door_w=12.0, pads=2, lights="#d8f0ff")
    h.box(180.0, 8.0, 96.0 - 0.36, 14.0, 2.6, 0.7, "#f2c21e", collide=False,
          r=[0.0, math.pi, 0.0], decal=kit.sign_decal("MAINT.", "#f2c21e", "#2a2a30", 5.4))
    for k in range(3):
        h.cyl(206.0, 3.0, 104.0 + k * 7.0, 5.0, 6.0, 5.0, ["#c42b20", "#2a6aa8", "#e8e8e0"][k])
    kit.outpost_room(h, 160.0, 200.0, -136.0, -104.0, 0.0, "#e8e0d0", "#a8a090", height=10.0,
                     door_w=12.0, pads=2, lights=AMBER)
    for z in (-136.06, -103.94):
        h.box(180.0, 5.0, z, 39.8, 1.2, 0.1, "#3a8ac8", collide=False)
    # the printout, taped to the wall inside
    h.box(180.0, 6.0, -133.0 + 0.0 + 0.06, 6.0, 4.0, 0.1, "#f8f8f0", collide=False,
          decal=kit.sign_decal("6EQUJ5  WOW!", "#f8f8f0", "#c42b20", 1.5))
    h.box(166.0, 2.0, -130.0, 4.0, 4.0, 6.0, "#5a4a3a", studs=True)
    b.rig("crt", h.x(166.0), 4.6, -130.0, yaw=h.yaw_out, w=3.0, seed=h.sx * 5)


# ==================================================================== desert
def _desert(b: kit.RelayArea, h: Half, rng: random.Random) -> None:
    """Saguaros, outcrops of red rock, scrub -- and the tumbleweeds."""
    for x, z, s in ((90.0, 60.0, 1.2), (150.0, -60.0, 1.0), (200.0, 150.0, 1.3),
                    (70.0, -90.0, 0.9), (236.0, -96.0, 1.1), (140.0, 160.0, 0.9)):
        _saguaro(b, h, x, z, s)
    for x, z, rx, rz, lv in ((80.0, -110.0, 14.0, 10.0, 3), (220.0, 120.0, 22.0, 16.0, 4),
                             (176.0, 54.0, 12.0, 10.0, 2), (250.0, -150.0, 20.0, 16.0, 3)):
        kit.mound(b, h.x(x), z, rx, rz, lv, 2.0, [ROCK_DARK, ROCK, ROCK_DARK, ROCK], band=4.0)
    for x, z, s in ((60.0, 40.0, 1.3), (96.0, -40.0, 1.1), (190.0, -30.0, 1.4),
                    (140.0, 80.0, 1.0), (250.0, 80.0, 1.2)):
        kit.boulder(b, h.x(x), z, 0.0, s, ROCK)
    for x, z in ((80.0, 120.0), (176.0, -170.0), (270.0, 120.0)):
        h.sphere(x, 1.2, z, 4.0, 2.4, 4.0, "#8a8a4a", collide=False)
    b.rig("tumbleweed", h.x(60.0), 0.0, 190.0, q=[h.x(220.0), 0.0, -190.0], r=2.2,
          speed=7.0, seed=h.sx * 1.7)
    del rng


def _saguaro(b: kit.RelayArea, h: Half, x: float, z: float, s: float) -> None:
    """A saguaro: a trunk you cannot walk through, arms up."""
    y0 = b.surface(h.x(x), z, 20.0)
    hgt = 16.0 * s
    h.cyl(x, y0 + hgt / 2.0, z, 2.6 * s, hgt, 2.6 * s, CACTUS)
    h.sphere(x, y0 + hgt, z, 2.6 * s, 1.6 * s, 2.6 * s, CACTUS, collide=False)
    for side, at, up in ((-1, 0.45, 0.32), (1, 0.6, 0.26)):
        ax = x + side * 2.6 * s
        h.cyl(ax, y0 + hgt * at, z, 2.4 * s, 1.8 * s, 1.8 * s, CACTUS, collide=False,
              r=[0.0, 0.0, math.pi / 2.0])
        h.cyl(ax + side * 1.0 * s, y0 + hgt * at + hgt * up / 2.0, z, 1.8 * s, hgt * up, 1.8 * s,
              CACTUS, collide=False)
        h.sphere(ax + side * 1.0 * s, y0 + hgt * (at + up), z, 1.8 * s, 1.2 * s, 1.8 * s, CACTUS,
                 collide=False)


# ======================================================================= hub
def _hub(b: kit.RelayArea) -> None:
    """The control building: a muster hall each end, the control room
    between them -- consoles, screens full of noise, a coffee machine --
    and a stair up to the roof each side of the south door."""
    hx, hz = HUB
    area = rect(-hx, hx, -hz, hz)
    room_walls(b, area, 3.0, 0.0, HUB_H, CONCRETE,
               doors={"x-": [(-7.0, 7.0, 10.0)], "x+": [(-7.0, 7.0, 10.0)],
                      "z-": [(-5.0, 5.0, 9.0)], "z+": [(-5.0, 5.0, 9.0)]})
    for sx in (-1, 1):
        holed_wall(b, "z", sx * 13.0, 2.0, -hz + 3.0, hz - 3.0, 0.0, HUB_H, CONCRETE_DARK,
                   holes=[(-6.0, 6.0, -1.0, 9.0)])
    slab(b, area, HUB_H + 1.2, 1.2, "#7a7a78", studs=True)
    kit.rails(b, area, HUB_H + 1.2, h=2.4, c=STEEL, t=0.6,
              gaps={"z-": [(-16.0, -8.0), (8.0, 16.0)]})
    for sx in (-1, 1):
        kit.flight(b, "z", -hz - 24.0, -hz, *sorted((sx * 8.0, sx * 16.0)), 0.0, HUB_H + 1.2,
                   CONCRETE_DARK, fill=0.0)
    # the control room: a horseshoe of consoles and their screens
    for x, z, yaw in ((-6.0, 14.0, math.pi), (6.0, 14.0, math.pi), (0.0, -14.0, 0.0)):
        b.box([x, 1.6, z], [10.0, 3.2, 3.0], "#3a3e46", studs=True)
        b.rig("crt", x, 4.4, z, yaw=yaw, w=3.6, seed=x + z)
    b.box([0.0, 8.0, hz - 3.06], [18.0, 6.0, 0.1], "#0a1a12", collide=False)
    b.rig("crt", 0.0, 8.0, hz - 3.2, yaw=math.pi, w=16.0, seed=9.0, big=True)
    b.box([0.0, 2.0, -19.0], [2.4, 4.0, 2.0], "#c8c8c0", studs=True)
    strip_light(b, 0.0, 0.0, HUB_H, 40.0, "z", "#d8f0ff")
    for h in halves(b):
        for i in range(3):
            for j in (-1, 1):
                b.muster(h.team, h.x(17.0 + 5.0 * i), 0.0, j * 13.0, h.yaw_out, size=4.4)
        h.sign(hx - 3.36, 10.0, 0.0, 10.0, 3.0, "sign_%s" % h.team, "x+")
        strip_light(b, h.x(26.0), 0.0, HUB_H, 40.0, "z", "#d8f0ff")
        h.box(hx + 7.0, 2.0, -14.0, 6.0, 4.0, 6.0, CONCRETE_DARK, studs=True)
        h.box(hx + 7.0, 1.6, 14.0, 5.0, 3.2, 5.0, "#5a5a60", studs=True)
    # the sign by the road in
    b.box([0.0, 3.0, -64.0], [22.0, 6.0, 1.2], "#f2f2e8",
          decal=kit.sign_decal("BIG EAR ARRAY", "#f2f2e8", "#2a3a6a", 3.67))
    for sx in (-1, 1):
        b.box([sx * 10.0, 1.5, -64.0], [1.0, 3.0, 1.0], "#5a5a60")


def _big_ear(b: kit.RelayArea) -> None:
    """The Big Ear: the great dish on its stepped pedestal north of the
    hub -- five strides up to a platform under it, and it turns too."""
    cx, cz = BIG_EAR
    tiers = [[rect(cx - 15.0 + 2.0 * k, cx + 15.0 - 2.0 * k, cz - 15.0 + 2.0 * k,
                   cz + 15.0 - 2.0 * k)] for k in range(5)]
    kit.tier_stack(b, tiers, 0.0, [2.0], [CONCRETE_DARK, CONCRETE], studs=True)
    b.rig("radio_dish", cx, 10.0, cz, d=56.0, mast=22.0, seed=0.0, big=True)
    b.box([cx, 1.0, cz - 15.06], [12.0, 1.6, 0.1], "#f2f2e8", collide=False,
          decal=kit.sign_decal("BIG EAR", "#f2f2e8", "#2a3a6a", 7.5), r=[0.0, math.pi, 0.0])


def _mesa(b: kit.RelayArea) -> None:
    """The mesa south of the hub: six strides of red rock up to a table
    top, a mast with a light on it, and a coyote who howls at the moon."""
    top = kit.mound(b, 0.0, -156.0, 74.0, 40.0, 6, 2.0,
                    [ROCK_DARK, ROCK, ROCK_DARK, ROCK, ROCK_DARK, "#b0745a"], band=4.0,
                    shrink=0.45)
    for dx in (-1.5, 1.5):
        for dz in (-1.5, 1.5):
            b.box([dx, top + 20.0, -156.0 + dz], [0.6, 40.0, 0.6], "#d8d8d8", material="metal")
    b.rig("blinker", 0.0, top + 40.8, -156.0, c="#ff3020", period=1.4, seed=0.3)
    b.rig("coyote", 26.0, top, -150.0, yaw=0.3)
    b.box([0.0, top + 1.5, -164.0], [6.0, 3.0, 4.0], "#5a5a60", studs=True)


def _corral(b: kit.RelayArea) -> None:
    """The corral north of the Big Ear: a rail fence, a trough, the
    windpump creaking round -- and a cow, who has the light in the sky's
    attention."""
    x0, x1, z0, z1 = -34.0, 34.0, 132.0, 176.0
    for z in (z0, z1):
        for k in range(9):
            x = x0 + k * (x1 - x0) / 8.0
            b.box([x, 2.0, z], [0.8, 4.0, 0.8], "#6a4a2e")
        for y in (1.6, 3.2):
            b.box([0.0, y, z], [x1 - x0, 0.4, 0.4], "#8a6a4a")
    for x in (x0, x1):
        for k in range(1, 5):
            z = z0 + k * (z1 - z0) / 5.0
            b.box([x, 2.0, z], [0.8, 4.0, 0.8], "#6a4a2e")
        for y in (1.6, 3.2):
            b.box([x, y, (z0 + z1) / 2.0], [0.4, 0.4, z1 - z0 - 0.8], "#8a6a4a")
    b.box([0.0, 1.2, 146.0], [12.0, 2.4, 4.0], "#8a8a84", studs=True)
    b.box([0.0, 2.46, 146.0], [11.0, 0.12, 3.0], "#4a7a9a", collide=False, material="glass",
          alpha=0.7)
    # the windpump: a lattice tower, the wheel turning
    for dx in (-2.0, 2.0):
        for dz in (-2.0, 2.0):
            b.box([dx, 12.0, 166.0 + dz], [0.6, 24.0, 0.6], "#9a9a94", material="metal")
    b.box([0.0, 24.4, 166.0], [5.0, 0.8, 5.0], "#7a7a74", material="metal")
    b.rig("windpump", 0.0, 26.5, 166.0, r=6.0, yaw=0.0)
    b.rig("cow", -14.0, 0.0, 152.0, yaw=1.2)


def _edge(b: kit.RelayArea, rng: random.Random) -> None:
    """A wire fence round the field on a low bank, the desert going on to
    the mountains, the moon."""
    hx, hz, m = HALF[0], HALF[1], b.margin
    room_walls(b, rect(-hx - m, hx + m, -hz - m, hz + m), m, 0.0, 22.0, "#8a6440")
    for sx in (-1, 1):
        b.box([sx * (hx + m / 2.0), 22.5, 0.0], [m, 1.0, 2 * (hz + m)], "#a87a50",
              collide=False)
    for sz in (-1, 1):
        b.box([0.0, 22.5, sz * (hz + m / 2.0)], [2 * hx, 1.0, m], "#a87a50", collide=False)
    kit.backdrop(b, "mesas", 22.0, rng, colours=["#3a2a3a", "#2a2236", "#4a3040"],
                 sides=("x-", "x+", "z-", "z+"), depth=60.0)


def _sky(b: kit.RelayArea) -> None:
    """Stars by the thousand, satellites crossing, the moon -- and the
    light over the corral that the dishes keep coming back to."""
    b.rig("starfield", 0.0, 0.0, 0.0, r=620.0, n=110, seed=3)
    b.rig("moon", -380.0, 300.0, 420.0, r=46.0)
    b.rig("ufo", 0.0, 120.0, 154.0, r=40.0, cow_p=[-14.0, 0.0, 152.0])
    b.rig("satellites", 0.0, 0.0, 0.0, r=600.0, n=3)


def _landmarks(b: kit.RelayArea) -> None:
    for x, z, name in ((0, 0, "the control building"), (0, 76, "the Big Ear"),
                       (0, -156, "the mesa"), (0, 154, "the corral")):
        b.landmark(float(x), float(z), name)
    for sx, team in ((-1, "red"), (1, "blue")):
        b.landmark(sx * 268.0, 0.0, "the %s receiver house" % team)
        for x, z, name in ((180, 114, "the maintenance shed"), (180, -120, "the trailer"),
                           (117, 0, "the trestle"), (126, -21, "the culvert"),
                           (64, 0, "dish one"), (160, 0, "dish two"), (214, 0, "dish three")):
            b.landmark(sx * float(x), float(z), "%s (%s side)" % (name, team))
    b.camera(-150.0, 70.0, 150.0, 0.0, 10.0, 0.0)
    b.camera(150.0, 70.0, -150.0, 0.0, 10.0, 0.0)
    b.camera(0.0, 90.0, -185.0, 0.0, 14.0, 0.0)
