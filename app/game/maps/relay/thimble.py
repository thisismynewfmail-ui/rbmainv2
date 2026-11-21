"""Thimble Acre -- a back garden at golden hour, at the scale of a toy.

Everybody is the size of a toy soldier.  Two kids left their brick castles
at either end of the lawn -- a red one by the hedge, a blue one by the
shed -- and the flags are in their courtyards.  Both teams muster inside
the old flowerpot turned upside down in the middle of the lawn, each out
of a crack in its own side.

Layout (red to the west; mirrored about x = 0)::

      z +200  ============ the fence (a cat is watching over it) =============
      z +125  VEGETABLE BED: cabbages, carrot tops, tomato canes   MATCHBOX
      z  +53  ~~~~~~~~ THE HOSE: a tube you can run in, or on ~~~~~~~~~~~~~~
      z    0  CASTLE  -- stepping stones --  MOLE HILLS --  THE POT (relay)
      z  -70  grass tufts, the lost marble                           TIN CAN
      z -130  ROCKERY ....... THE POND: lily pads, a frog ......... ROCKERY
      z -200  ============ the fence (sunflowers behind it) =================

The hose is the runner's road: a tube from one castle's corner to the
other's, split open in four places, low enough to jump onto and walk.
"""
from __future__ import annotations

import math
import random

from . import kit
from .kit import (Half, halves, holed_wall,
                  rect, room_walls, slab, strip_light)

HALF = (300.0, 190.0)
SKY = {"top": "#5a8ad8", "horizon": "#ffd08a", "sun": [0.55, 0.25, -0.5],
       "clouds": 0.45, "tint": "#ffe0a8"}
AMBIENT = "#b8a88a"
GROUND = "#5aa03a"
FOG = 900.0

LAWN = "#5aa03a"
LAWN_DARK = "#4a8a30"
LAWN_LIGHT = "#6ab448"
SOIL = "#6a4a2a"
SOIL_DARK = "#5a3c20"
POT = "#c8643c"
POT_DARK = "#a84e2c"
POT_RIM = "#b85a34"
PLANK = "#a07a4a"
PLANK_DARK = "#7a5a34"
STONE = "#b8b0a0"
STONE_DARK = "#948c7c"
HOSE = "#3a9a3a"
HOSE_DARK = "#2a7a2a"
BRASS = "#c8a040"

POT_R = 38.0             # the flowerpot's half width
POT_TOP = 30.0
CASTLE = (226.0, 296.0, -56.0, 56.0)   # magnitudes
HOSE_Z = (66.0, 76.0)
HOSE_TOP = 8.0
FLAG_X = 268.0


def build(b: kit.RelayArea) -> None:
    rng = random.Random(0x7111)
    b.relay("the Old Pot", 50.0)
    b.intro = ["Thimble Acre -- the whole garden is a battlefield, and you are a toy.",
               "Muster in the upturned flowerpot; the flags are in the brick castles at "
               "each end of the lawn.",
               "The garden hose runs the length of the lawn. You can run inside it."]
    b.extra.update({"accent": "#ffb84a", "weather": "motes"})
    pond = rect(-62.0, 62.0, -150.0, -106.0)
    kit.ground(b, LAWN, soil=SOIL, holes=[pond])
    _pond(b, pond)
    _pot(b)
    _hose(b)
    for h in halves(b):
        _castle(b, h)
        _bed(b, h)
        _outposts(b, h)
        _rockery(b, h)
        _lawn(b, h, random.Random(0x6A55))
    _fence(b, rng)
    _easter_eggs(b)
    _landmarks(b)


# ================================================================== the pot
def _pot(b: kit.RelayArea) -> None:
    """The flowerpot turned upside down: a hall with a muster bay each side,
    the drainage hole a skylight in the middle, a crack each way out."""
    r, t = POT_R, 3.0
    area = rect(-r, r, -r, r)
    room_walls(b, area, t, 0.0, POT_TOP, POT,
               doors={"x-": [(-7.0, 7.0, 11.0)], "x+": [(-7.0, 7.0, 11.0)],
                      "z-": [(-6.0, 6.0, 10.0)], "z+": [(-6.0, 6.0, 10.0)]})
    # the rim (the pot's lip, now at the bottom): a band round the base
    room_walls(b, rect(-r - 1.5, r + 1.5, -r - 1.5, r + 1.5), 1.5, 0.0, 5.0, POT_RIM,
               doors={"x-": [(-7.0, 7.0, 5.0)], "x+": [(-7.0, 7.0, 5.0)],
                      "z-": [(-6.0, 6.0, 5.0)], "z+": [(-6.0, 6.0, 5.0)]})
    # the base (now the roof), with its drainage hole
    hole = rect(-7.0, 7.0, -7.0, 7.0)
    kit.plate(b, kit.carve(area, [hole]), POT_TOP + 2.0, 2.0, POT_DARK, studs=True)
    kit.hazard_rim(b, hole, POT_TOP + 2.0)
    for sx in (-1, 1):
        holed_wall(b, "z", sx * 15.0, 2.0, -r + t, r - t, 0.0, POT_TOP, POT_DARK,
                   holes=[(-6.0, 6.0, -1.0, 9.0)])
    # a stack of seed trays up the north side to the top
    for sx in (-1, 1):
        kit.flight(b, "z", r + 26.0, r + 1.5, *sorted((sx * 20.0, sx * 30.0)), 0.0,
                   POT_TOP + 2.0, "#4a6a8a", fill=0.0)
    # the light down the drainage hole
    b.cyl([0.0, 0.08, 0.0], [12.0, 0.1, 12.0], "#fff0b0", collide=False, material="neon",
          alpha=0.5)
    for h in halves(b):
        for i in range(3):
            for j in (-1, 1):
                b.muster(h.team, h.x(19.5 + 5.6 * i), 0.0, j * 15.0, h.yaw_out, size=5.0)
        h.sign(r - t - 0.36, 22.0, 0.0, 12.0, 3.4, "sign_%s" % h.team, "x+")
        strip_light(b, h.x(26.0), 0.0, POT_TOP, 46.0, "z", "#ffe2a8")
        # a crumb of pot by each crack: cover stepping out
        h.box(r + 8.0, 2.5, -15.0, 7.0, 5.0, 7.0, POT_DARK, studs=True)
        h.box(r + 8.0, 2.0, 15.0, 6.0, 4.0, 6.0, POT_RIM, studs=True)
    kit.board_letters(b, 0.0, 22.0, r, "LITTLE FERN", 2.6, POT_DARK, "#f2e2c8",
                      solid=False)


# ================================================================= the hose
def _hose(b: kit.RelayArea) -> None:
    """The garden hose: a tube the length of the lawn, split in four places."""
    z0, z1 = HOSE_Z
    x_end = 204.0
    cuts = [(-176.0, -164.0), (-86.0, -74.0), (74.0, 86.0), (164.0, 176.0)]
    t = 1.0
    for z in (z0 + t / 2.0, z1 - t / 2.0):
        holed_wall(b, "x", z, t, -x_end, x_end, 0.0, HOSE_TOP - 1.0, HOSE,
                   holes=[(a, c, -1.0, HOSE_TOP) for a, c in cuts])
    for (a, c) in [(-x_end, cuts[0][0]), (cuts[0][1], cuts[1][0]), (cuts[1][1], cuts[2][0]),
                   (cuts[2][1], cuts[3][0]), (cuts[3][1], x_end)]:
        slab(b, rect(a, c, z0, z1), HOSE_TOP, 1.0, HOSE_DARK, studs=True)
        # a stripe down the top, the way a hose has one
        b.box([(a + c) / 2.0, HOSE_TOP + 0.04, (z0 + z1) / 2.0], [c - a, 0.08, 1.4], "#d8d040",
              collide=False)
        strip_light(b, (a + c) / 2.0, (z0 + z1) / 2.0, HOSE_TOP - 1.0, max(2.0, c - a - 4.0),
                    "x", "#a8ffb0")
    # brass couplings at both ends
    for sx in (-1, 1):
        x = sx * (x_end + 2.0)
        b.box([x, 4.5, (z0 + z1) / 2.0], [4.0, 9.0, 1.4], BRASS, material="metal")
        b.box([x, 4.5, z0 - 0.7], [4.0, 9.0, 1.4], BRASS, material="metal")
        b.box([x, 4.5, z1 + 0.7], [4.0, 9.0, 1.4], BRASS, material="metal")


# =============================================================== the castles
def _castle(b: kit.RelayArea, h: Half) -> None:
    """A kid's brick castle in the team's colour: studded walls, four
    towers, a gate towards the lawn, side doors, a back door, a rampart
    walk -- and the flag on a plinth in the courtyard."""
    x0, x1, z0, z1 = CASTLE
    y = 4.0
    # the patio it stands on: two steps of paving
    kit.tier_stack(b, [[h.r(x0 - 14.0, x1 + 4.0, z0 - 20.0, z1 + 20.0)],
                       [h.r(x0 - 7.0, x1 + 4.0, z0 - 12.0, z1 + 12.0)]], 0.0, [2.0],
                   [STONE_DARK, STONE], studs=True)
    top = y + 18.0
    t = 4.0
    area = h.r(x0, x1, z0, z1)
    room_walls(b, area, t, y, top, h.colour,
               doors={h.inward: [(-9.0, 9.0, y + 12.0)],
                      "z-": [(*h.xs(256.0, 268.0), y + 10.0)],
                      "z+": [(*h.xs(256.0, 268.0), y + 10.0)],
                      h.outward: [(-6.0, 6.0, y + 10.0)]},
               studs=True)
    # the rampart walk inside the front wall, and its stairs
    h.slab(x0 + t, x0 + t + 8.0, z0 + t, z1 - t, top - 4.0, 1.2, h.dark, studs=True)
    for sz in (-1, 1):
        h.flight_x(x0 + t + 22.0, x0 + t + 8.0, sz * 30.0, sz * 40.0, y, top - 4.0, h.light,
                   fill=y)
    kit.crenels(b, "z", h.x(x0 + 1.5), z0 + 2.0, z1 - 2.0, top, h.light, every=8.0,
                thickness=3.0, gaps=[(-10.0, 10.0)])
    # four towers at the corners, taller than the walls, solid
    for zc in (z0, z1):
        for xc in (x0, x1):
            h.box(xc, (y + top + 8.0) / 2.0 + 0.0, zc, 12.0, top + 8.0 - y, 12.0, h.dark,
                  studs=True)
            h.box(xc, top + 9.0, zc, 13.0, 2.0, 13.0, h.light, studs=True)
    top_y = kit.pedestal(b, h.x(FLAG_X), 0.0, y, h.colour, h.neon, base=STONE_DARK)
    b.flag(h.team, h.x(FLAG_X), top_y, 0.0)
    kit.banner_mast(b, h.x(x1), z1, top + 10.0, 22.0, h.team, h.inward)
    # toy blocks lying about the courtyard: cover
    for x, z, s, c in ((246.0, -26.0, 6.0, "#f2c21e"), (250.0, 30.0, 5.0, "#3a9a3a"),
                       (284.0, -36.0, 5.0, "#ffffff")):
        h.box(x, y + s / 2.0, z, s * 1.6, s, s, c, studs=True)


# ======================================================= the vegetable bed
def _bed(b: kit.RelayArea, h: Half) -> None:
    """A raised bed of giant vegetables on the north lawn."""
    x0, x1, z0, z1 = 40.0, 132.0, 82.0, 170.0
    area = h.r(x0, x1, z0, z1)
    room_walls(b, area, 2.0, 0.0, 6.0, PLANK, studs=True,
               doors={h.inward: [(110.0, 124.0, 6.0)], "z-": [(*h.xs(80.0, 94.0), 6.0)]})
    slab(b, (area[0] + 2.0, area[1] - 2.0, z0 + 2.0, z1 - 2.0), 4.0, 4.0, SOIL, studs=True)
    # steps of soil up into it where the boards are gapped
    h.box(117.0, 1.0, z1 - 10.0 + 0.0, 4.0, 2.0, 14.0, SOIL_DARK, studs=True)
    h.box(87.0, 1.0, z0 - 2.0 + 0.0, 14.0, 2.0, 4.0, SOIL_DARK, studs=True)
    for x, z in ((60.0, 104.0), (96.0, 150.0), (64.0, 146.0)):
        h.sphere(x, 4.0 + 7.0, z, 18.0, 16.0, 18.0, "#7ab84a")
        h.sphere(x + 2.0, 4.0 + 12.0, z - 1.0, 12.0, 10.0, 12.0, "#9ad86a", collide=False)
    for x, z in ((100.0, 104.0), (112.0, 126.0)):
        h.cone(x, 4.0 + 1.0, z, 5.0, 2.0, 5.0, "#e87a2a")
        for k in range(3):
            h.cone(x + (k - 1) * 1.6, 4.0 + 8.0, z, 3.0, 12.0, 3.0, "#3a8a2a", collide=False)
    # tomato canes, tied at the top, tomatoes hanging
    for x, z in ((48.0, 128.0), (120.0, 160.0)):
        for dx, dz in ((-4.0, 0.0), (4.0, 0.0), (0.0, 5.0)):
            h.cyl(x + dx, 4.0 + 14.0, z + dz, 0.8, 28.0, 0.8, "#c8a870")
        h.sphere(x - 2.0, 4.0 + 12.0, z + 2.0, 4.0, 4.0, 4.0, "#d82a1a", collide=False)
        h.sphere(x + 2.5, 4.0 + 18.0, z + 1.0, 3.6, 3.6, 3.6, "#e83a2a", collide=False)
        h.sphere(x, 4.0 + 22.0, z + 4.0, 3.0, 3.0, 3.0, "#5a9a2a", collide=False)


# ================================================================ outposts
def _outposts(b: kit.RelayArea, h: Half) -> None:
    """A matchbox (north) and a tipped-over tin can (south): where a team
    falls back to while its flag is out."""
    kit.outpost_room(h, 150.0, 196.0, 112.0, 150.0, 0.0, "#d8c8a0", "#c42b20", height=11.0,
                     door_w=12.0, pads=2)
    h.box(173.0, 11.0 + 1.2 + 0.04, 131.0, 30.0, 0.08, 20.0, "#2a4a8a", collide=False)
    kit.outpost_room(h, 150.0, 196.0, -150.0, -112.0, 0.0, "#b8c0c8", "#8a9098",
                     height=11.0, door_w=12.0, pads=2)
    h.box(173.0, 6.0, -112.0 + 0.36 - 0.36 + 0.0 - 0.0, 30.0, 4.0, 0.12, "#e8c84a",
          collide=False)


# ================================================================== rockery
def _rockery(b: kit.RelayArea, h: Half) -> None:
    """A rockery of stepped stones on the south lawn: high ground over the
    pond, a long view down the lane."""
    kit.mound(b, h.x(118.0), -168.0, 34.0, 26.0, 4, 2.0,
              [STONE_DARK, STONE, "#a8a090", STONE], band=6.0)
    for x, z, s in ((100.0, -146.0, 1.6), (136.0, -176.0, 2.0), (90.0, -178.0, 1.3)):
        kit.boulder(b, h.x(x), z, 0.0, s, "#8a8478")
    # alpines on the rockery's top: purple and white cushions
    for x, z, c in ((114.0, -170.0, "#a86ad8"), (124.0, -164.0, "#f2f2f2")):
        h.sphere(x, 8.0 + 1.2, z, 5.0, 2.4, 5.0, c, collide=False)


# ===================================================================== pond
def _pond(b: kit.RelayArea, pond) -> None:
    """The pond south of the pot: lily pads to step across on, a frog."""
    kit.channel(b, pond, 4.0, "#3a4a3a", studs=True)
    kit.water_sheet(b, pond, -1.2, "#3a7a8a", 0.62)
    for x, z, s in ((-40.0, -118.0, 10.0), (-20.0, -136.0, 9.0), (0.0, -122.0, 11.0),
                    (20.0, -136.0, 9.0), (40.0, -118.0, 10.0)):
        b.cyl([x, -1.3, z], [s, 2.6, s], "#4a8a3a", studs=True)
    b.sphere([2.0, 1.4, -122.0], [3.0, 2.2, 2.6], "#6aa84a", collide=False)
    for dx in (-0.8, 0.8):
        b.sphere([2.0 + dx, 2.5, -121.0], [0.8, 0.8, 0.8], "#e8e040", collide=False)
    # flat stones round the rim, a step out of the water
    for x in (-58.0, 58.0):
        b.box([x, -1.0, -128.0], [7.0, 2.0, 18.0], STONE, studs=True)


# ===================================================================== lawn
def _lawn(b: kit.RelayArea, h: Half, rng: random.Random) -> None:
    """Grass tufts (solid blades, real cover), mole hills, stepping stones
    from the castle gate, and the lost marble."""
    for x, z in ((86.0, -48.0), (140.0, 22.0), (198.0, -86.0), (60.0, -84.0),
                 (176.0, 70.0), (110.0, -12.0)):
        n = 5
        for k in range(n):
            a = k * 2 * math.pi / n + 0.4
            hgt = 12.0 + (k * 7 % 5) * 2.0
            h.box(x + math.cos(a) * 3.0, hgt / 2.0, z + math.sin(a) * 3.0, 1.6, hgt, 1.6,
                  LAWN_LIGHT if k % 2 else LAWN_DARK)
    for x, z, r in ((96.0, 26.0, 18.0), (160.0, -40.0, 20.0)):
        kit.mound(b, h.x(x), z, r, r * 0.8, 3, 2.0, [SOIL_DARK, SOIL, SOIL_DARK], band=4.0)
    for k in range(5):
        x = 76.0 + k * 30.0
        z = 6.0 * math.sin(k * 1.3)
        h.cyl(x, 0.4, z, 9.0, 0.8, 9.0, STONE, studs=True)
    h.sphere(206.0, 3.0, -30.0, 6.0, 6.0, 6.0, "#4a8ad8", material="glass", alpha=0.75)
    del rng


# ==================================================================== fence
def _fence(b: kit.RelayArea, rng: random.Random) -> None:
    """The garden fence all round: planks taller than a house to a toy, the
    sky over it -- a cat on the north fence, sunflowers over the south."""
    hx, hz, m = HALF[0], HALF[1], b.margin
    room_walls(b, rect(-hx - m, hx + m, -hz - m, hz + m), m, 0.0, 70.0, PLANK_DARK)
    for i in range(24):
        x = -hx + (i + 0.5) * (2 * hx) / 24.0
        for sz in (-1, 1):
            b.box([x, 70.0 + 3.0, sz * (hz + m / 2.0)], [2 * hx / 24.0 - 1.4, 6.0, m + 0.6],
                  PLANK if i % 2 else "#b08a5a", collide=False)
    for i in range(9):
        z = -hz + (i + 0.5) * (2 * hz) / 9.0
        for sx in (-1, 1):
            b.box([sx * (hx + m / 2.0), 70.0 + 3.0, z], [m + 0.6, 6.0, 2 * hz / 9.0 - 1.4],
                  PLANK if i % 2 else "#b08a5a", collide=False)
    # the cat, chin on the fence top, watching the game
    cx, cz = 60.0, hz + m / 2.0
    b.sphere([cx, 88.0, cz], [34.0, 28.0, 26.0], "#e8a04a", collide=False)
    for dx in (-10.0, 10.0):
        b.cone([cx + dx, 104.0, cz], [10.0, 14.0, 8.0], "#e8a04a", collide=False)
        b.sphere([cx + dx * 0.8, 92.0, cz - 12.0], [5.0, 6.0, 2.0], "#f2f2d8", collide=False)
        b.sphere([cx + dx * 0.8, 92.0, cz - 13.2], [2.0, 4.0, 1.0], "#1b1b1b", collide=False)
    b.sphere([cx, 85.0, cz - 13.0], [3.0, 2.0, 1.6], "#e88a8a", collide=False)
    for dx in (-14.0, 14.0):
        b.sphere([cx + dx, 76.0, cz - 6.0], [12.0, 7.0, 16.0], "#e8a04a", collide=False)
    # sunflowers over the south fence
    for k, x in enumerate((-180.0, -70.0, 40.0, 150.0, 250.0)):
        hgt = 96.0 + (k % 3) * 12.0
        z = -(hz + m / 2.0)
        b.cyl([x, 70.0 + (hgt - 70.0) / 2.0 + 3.0, z], [3.0, hgt - 70.0, 3.0], "#4a8a2a",
              collide=False)
        b.cyl([x, hgt + 4.0, z - 2.0], [30.0, 3.0, 30.0], "#f2c21e", collide=False,
              r=[math.pi / 2.0 - 0.3, 0.0, 0.0])
        b.cyl([x, hgt + 4.0, z - 3.6], [14.0, 2.0, 14.0], "#5a3a1a", collide=False,
              r=[math.pi / 2.0 - 0.3, 0.0, 0.0])
    # the house over the east end, the shed over the west
    b.box([hx + m + 55.0, 90.0, 0.0], [110.0, 180.0, 300.0], "#d8c8b0", collide=False)
    b.box([hx + m - 0.2 + 0.0, 110.0, -60.0], [0.4, 30.0, 26.0], "#ffe8a8", material="neon",
          collide=False)
    b.box([-hx - m - 45.0, 60.0, 30.0], [90.0, 120.0, 140.0], "#6a7a5a", collide=False)
    del rng


def _easter_eggs(b: kit.RelayArea) -> None:
    """A toy soldier lying in the grass, and a ladybird on a cabbage."""
    b.box([30.0, 0.8, -70.0], [6.0, 1.6, 2.6], "#4a6a2a", collide=False)
    b.box([34.2, 0.9, -70.0], [2.6, 1.8, 2.4], "#4a6a2a", collide=False)
    b.box([25.0, 0.7, -70.4], [5.0, 1.0, 0.9], "#4a6a2a", collide=False)
    b.sphere([-58.0, 21.0, 104.0], [3.0, 2.0, 3.0], "#d8221a", collide=False)
    b.sphere([-58.0, 21.4, 105.6], [1.4, 1.2, 1.2], "#1b1b1b", collide=False)


def _landmarks(b: kit.RelayArea) -> None:
    for x, z, name in ((0, 0, "the Old Pot"), (0, -128, "the pond"), (0, 53, "the hose")):
        b.landmark(float(x), float(z), name)
    for sx, team in ((-1, "red"), (1, "blue")):
        b.landmark(sx * 261.0, 0.0, "the %s castle" % team)
        for x, z, name in ((86, 126, "the vegetable bed"), (173, 131, "the matchbox"),
                           (173, -131, "the tin can"), (118, -168, "the rockery")):
            b.landmark(sx * float(x), float(z), "%s (%s side)" % (name, team))
    b.camera(-160.0, 60.0, -150.0, 0.0, 8.0, 0.0)
    b.camera(170.0, 70.0, 160.0, 0.0, 6.0, 0.0)
    b.camera(0.0, 80.0, -180.0, 0.0, 10.0, 40.0)
