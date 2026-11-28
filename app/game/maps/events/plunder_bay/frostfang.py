"""Frostfang Floe: an island at the top of the world, crisp and blinding
white under a hard blue sky -- a galleon frozen fast into the pack ice in
the middle of it, the idol on her quarterdeck, six breathing holes in the
ice round her; to the north a glacier rising in three great steps of blue
ice with a grotto cut into its foot; on either wing a whalers' camp of
painted huts and smoking chimneys; to the south a shore of ice floes where
the penguins stand about.

Layout (north is -z; the Scarlet Corsairs' ship off the west shore, the
Azure Buccaneers' off the east)::

    z -120  ====== ice crags ======  THE GLACIER: three steps  ====== ice crags ======
    z  -84                        (the ice grotto in its foot)
    z  -60   whalers' huts   ----------- the glacier's face -----------   whalers' huts
   SCARLET   snowdrifts      o     THE FROZEN GALLEON in the ice     o   snowdrifts    BLUE
    QUEEN    the try-pot     o     (breathing holes all round her)   o   the try-pot   MARLIN
    z   60   spruces, a sled           the pack ice's edge              a sled, spruces
    z  100  ~~~~~~~~~~~ ice floes, penguins, the south sea ~~~~~~~~~~~

The halves are mirror images.  The galleon, the glacier and the grotto are
as far from one ship as the other.

The twist is the kraken, the frost kraken (``extra["twist"] = "kraken"``,
``extra["style"]["kraken"] = "frost"``): it comes up under the floe, its
tentacles bursting through the breathing holes (``tentacle`` marks) to
slam down on whoever is near (a ring shows where); cut one down and it
leaves a jewel.
"""
from __future__ import annotations

import math
import random

from ..calamity_coast.town import skirt
from ..kit import ArenaArea, backdrop, flight, rect, slab
from .common import IRON, PLANK, SEA_TOP, SEABED, SHIP_X, SHORE_X, TIMBER, Isle, galleon

HALF = (170.0, 120.0)
SKY = {"top": "#3a8ae0", "horizon": "#e8f4ff", "sun": [0.5, 0.42, -0.35], "clouds": 0.3, "tint": "#f4faff"}
AMBIENT = "#c4d4e4"
GROUND = "#f2f6fa"
FOG = 820.0

SNOW = "#f2f6fa"
SNOW_SHADE = "#dde8f2"
TRODDEN = "#c8d4e0"
ICE = "#bfe4f4"
ICE_DEEP = "#7ac0e0"
ICE_DARK = "#4a90b8"
FROZEN_SEA = "#2a7aa8"
WOOD = "#6a4a2e"
SPRUCE = "#2e5a3e"
SOUTH = 100.0
NORTH = -100.0               # the foot of the ice crags on the wings
SHEET = (-50.0, 50.0, -46.0, 46.0)     # the pack ice round the galleon
HOLES = ((-26.0, -20.0), (26.0, -20.0), (-26.0, 20.0), (26.0, 20.0), (0.0, -38.0), (0.0, 38.0))
HOLE_R = 4.5
# the glacier: three steps (half-width, front z, back z, top)
GLACIER = ((80.0, -60.0, -76.0, 7.0), (64.0, -76.0, -92.0, 13.0), (48.0, -92.0, -112.0, 19.0))
GROTTO = (-16.0, 16.0, -92.0, -82.0)   # the ice grotto in the glacier's foot
GROTTO_H = 10.0
TUNNEL_W = 5.0               # its passage's half-width
TUNNEL_H = 6.4
# the frozen galleon
SHIP = (-8.0, 8.0, -24.0, 24.0)
DECK = 5.0
FORE_Y = 8.0
QUARTER_Y = 9.0
HUTS = (((82.0, 96.0, -54.0, -42.0), "z+", "#c8302a"), ((98.0, 108.0, -36.0, -26.0), "x-", "#2a6ab8"),
        ((84.0, 98.0, 30.0, 42.0), "z-", "#e8b830"))
DRIFTS = ((66.0, 82.0, -34.0, -22.0), (84.0, 98.0, 48.0, 62.0), (88.0, 104.0, 74.0, 88.0),
          (40.0, 54.0, 76.0, 88.0))
IGLOOS = ((24.0, 36.0, 74.0, 86.0),)


def _m(r):
    x0, x1, z0, z1 = r
    return (-x1, -x0, z0, z1)


# ================================================================ the land
def _land(isle: Isle) -> None:
    b = isle.b
    hx, hz = HALF
    m = b.margin
    west = (-hx - m, -SHORE_X, -hz - m, hz + m)
    east = (SHORE_X, hx + m, -hz - m, hz + m)
    south = (-SHORE_X, SHORE_X, SOUTH, hz + m)
    holes = [rect(x - HOLE_R, x + HOLE_R, z - HOLE_R, z + HOLE_R) for x, z in HOLES]
    isle.land(SNOW, holes=[west, east, south] + holes, soil="#8a9aaa")
    for area in [west, east, south] + holes:
        slab(b, area, SEABED, 3.0, "#5a7a94", studs=True)
    for k, top in enumerate((-1.0, -2.0)):
        colour = SNOW_SHADE if k == 0 else "#a8bccc"
        for sgn in (-1.0, 1.0):
            xa, xb = sorted((sgn * (SHORE_X + 3.0 * k), sgn * (SHORE_X + 3.0 * (k + 1))))
            b.box([(xa + xb) / 2.0, (SEABED + top) / 2.0, (NORTH + hz) / 2.0],
                  [xb - xa, top - SEABED, hz - NORTH], colour, studs=True)
        za, zb = SOUTH + 3.0 * k, SOUTH + 3.0 * (k + 1)
        b.box([0.0, (SEABED + top) / 2.0, (za + zb) / 2.0], [2 * SHORE_X, top - SEABED, zb - za], colour,
              studs=True)
    for area in ((-hx, -SHORE_X, -hz, hz), (SHORE_X, hx, -hz, hz), (-SHORE_X, SHORE_X, SOUTH, hz)):
        isle.water(area, SEABED, colour=FROZEN_SEA, alpha=0.62)
    for x0, x1, z0, z1 in ((-hx - m - 300.0, -hx - m, -hz - m - 300.0, hz + m + 300.0),
                           (hx + m, hx + m + 300.0, -hz - m - 300.0, hz + m + 300.0),
                           (-hx - m, hx + m, hz + m, hz + m + 300.0)):
        b.box([(x0 + x1) / 2.0, (SEABED - 6.0 + SEA_TOP) / 2.0, (z0 + z1) / 2.0],
              [x1 - x0, SEA_TOP - SEABED + 6.0, z1 - z0], "#1e6a98", material="glass", alpha=0.65, collide=False)
    # the breathing holes: a ledge of ice inside each, black water below
    for x, z in HOLES:
        r = (x - HOLE_R, x + HOLE_R, z - HOLE_R, z + HOLE_R)
        x0, x1, z0, z1 = r
        w = 1.5
        for xa, xb in ((x0, x0 + w), (x1 - w, x1)):
            b.box([(xa + xb) / 2.0, (SEABED - 1.5) / 2.0, z], [w, -1.5 - SEABED, z1 - z0], ICE_DEEP, studs=True)
        for za, zb in ((z0, z0 + w), (z1 - w, z1)):
            b.box([x, (SEABED - 1.5) / 2.0, (za + zb) / 2.0], [x1 - x0 - 2 * w, -1.5 - SEABED, zb - za], ICE_DEEP,
                  studs=True)
        isle.water(r, SEABED, colour="#123a5a", alpha=0.8)
    # the snowdrifts: snow heaped in steps
    for sgn in (-1.0, 1.0):
        for r in DRIFTS:
            xa, xb = sorted((sgn * r[0], sgn * r[1]))
            for k in range(3):
                inset = k * 2.6
                top = 0.9 * (k + 1)
                b.box([(xa + xb) / 2.0, top / 2.0, (r[2] + r[3]) / 2.0],
                      [xb - xa - 2 * inset, top, r[3] - r[2] - 2 * inset], (SNOW, SNOW_SHADE)[k % 2], studs=True)
    # covers: kept off what stands on the snow; paths first, then the pack
    # ice and the shore
    s = isle.s
    keep = [(-GLACIER[0][0], GLACIER[0][0], GLACIER[2][2], GLACIER[0][1])]
    keep += [rect(x - HOLE_R, x + HOLE_R, z - HOLE_R, z + HOLE_R) for x, z in HOLES]
    keep += [(SHIP[0] - 6.5, SHIP[1] + 6.5, SHIP[2] - 2.0, SHIP[3] + 4.0)]
    for (r, _d, _c) in HUTS:
        keep += [r, _m(r)]
    for r in DRIFTS:
        keep += [r, _m(r)]
    for r in ((50.0, 56.0, -60.0, -52.0), (70.0, 84.0, 50.0, 60.0), (98.0, 106.0, 56.0, 64.0)) + IGLOOS:
        keep += [r, _m(r)]
    for r in keep:
        s.reserve(r)
    for sgn in (-1.0, 1.0):
        def X(x: float, sgn: float = sgn) -> float:
            return sgn * x
        isle.trail([(X(109.5), -15.0), (X(53.0), -15.0), (X(53.0), -51.5)], colour=TRODDEN)
        isle.trail([(X(109.5), 15.0), (X(64.0), 15.0), (X(64.0), 70.0), (X(20.0), 70.0)], colour=TRODDEN)
        isle.trail([(X(89.0), -39.5), (X(89.0), -17.5)], colour=TRODDEN)
        isle.trail([(X(91.0), 27.5), (X(91.0), 17.5)], colour=TRODDEN)
    s.lay(rect(*SHEET), 0.1, ICE, material="glass")
    for x0, x1, z0, z1 in ((-SHORE_X, -102.0, NORTH, SOUTH), (102.0, SHORE_X, NORTH, SOUTH),
                           (-102.0, 102.0, 90.0, SOUTH)):
        s.lay(rect(x0, x1, z0, z1), 0.1, SNOW_SHADE)


# =============================================================== the edges
def _edges(isle: Isle) -> None:
    b = isle.b
    hx, hz = HALF
    rng = isle.rng
    m = b.margin
    ices = (ICE, "#d4eef8", ICE_DEEP, "#a8d8ec")
    for sgn in (-1.0, 1.0):
        a0, a1 = sorted((sgn * GLACIER[0][0], sgn * SHORE_X))
        isle.cliffs("x", a0, a1, -hz - m, NORTH, rng.uniform(24.0, 28.0), ices, green=SNOW, vines=False)
        a0, a1 = sorted((sgn * SHORE_X, sgn * (hx + m)))
        isle.cliffs("x", a0, a1, -hz - m, NORTH, 32.0, ices, base=SEABED, green=SNOW, step=14.5, recess=0.0,
                    vines=False)
        b.box([sgn * (hx + m / 2.0), (SEABED + 6.0) / 2.0, (NORTH + hz + m) / 2.0],
              [m, 6.0 - SEABED, hz + m - NORTH], ICE_DEEP)
    b.box([0.0, (SEABED + 6.0) / 2.0, hz + m / 2.0], [2 * hx, 6.0 - SEABED, m], ICE_DEEP)
    # pack ice heaped along the breakwaters
    for k in range(18):
        z = NORTH + (k + 0.5) * (hz + m - NORTH) / 18.0
        for sgn in (-1.0, 1.0):
            b.box([sgn * (hx + m / 2.0) + rng.uniform(-1.0, 1.0), 6.0 + 1.0 + (k % 3) * 0.6, z],
                  [m - 2.0 - (k % 2) * 0.6, 2.0 + (k % 3) * 1.2, (hz + m - NORTH) / 18.0 - 2.0], ices[k % 4])
    for k in range(18):
        x = -hx + (k + 0.5) * 2 * hx / 18.0
        b.box([x, 6.0 + 1.0 + (k % 3) * 0.6, hz + m / 2.0 + rng.uniform(-1.0, 1.0)],
              [2 * hx / 18.0 - 2.0, 2.0 + (k % 3) * 1.2, m - 2.0 - (k % 2) * 0.6], ices[(k + 1) % 4])
    skirt(b, hx, hz, "#c8dce8", top=SEABED - 3.05)
    backdrop(b, "hills", 12.0, rng, sides=("z-",), colours=["#e8f0f8", "#d8e4f0", "#c8d8e8"], depth=160.0)
    # icebergs far out at sea
    for x, z, w, h in ((-380.0, -240.0, 60.0, 50.0), (420.0, 260.0, 80.0, 40.0), (480.0, -160.0, 40.0, 70.0),
                       (-460.0, 280.0, 70.0, 45.0)):
        b.box([x, h / 2.0 - 4.0, z], [w, h, w * 0.7], "#e8f6ff", collide=False)
        b.box([x + w * 0.1, h - 2.0, z], [w * 0.6, 8.0, w * 0.5], ICE, collide=False)


# ============================================================ the glacier
def _glacier(isle: Isle) -> None:
    """The glacier: three steps of ice, each a set of blocks that never
    overlap -- with the passage and the grotto left hollow in its foot --
    the faces streaked blue, icicles off the edges, stairs cut up them."""
    b = isle.b
    rng = isle.rng
    (hw1, f1, k1, t1), (hw2, f2, k2, t2), (hw3, f3, k3, t3) = GLACIER
    gx0, gx1, gz0, gz1 = GROTTO
    tw = TUNNEL_W

    def block(x0: float, x1: float, z0: float, z1: float, y0: float, y1: float, colour: str) -> None:
        if x1 - x0 > 1e-3 and z1 - z0 > 1e-3 and y1 - y0 > 1e-3:
            b.box([(x0 + x1) / 2.0, (y0 + y1) / 2.0, (z0 + z1) / 2.0], [x1 - x0, y1 - y0, z1 - z0], colour)

    # the first step: its front strip, the passage through it; its sides
    # running back beside the second
    block(-hw1, -tw, k1, f1, 0.0, t1, ICE)
    block(tw, hw1, k1, f1, 0.0, t1, ICE)
    block(-tw, tw, k1, f1, TUNNEL_H, t1, ICE_DEEP)
    for sgn in (-1.0, 1.0):
        a, c = sorted((sgn * hw2, sgn * hw1))
        block(a, c, k3, k1, 0.0, t1, ICE)
    # the second: round the passage and the grotto
    block(-hw2, gx0, k2, k1, 0.0, t2, "#d4eef8")
    block(gx1, hw2, k2, k1, 0.0, t2, "#d4eef8")
    block(gx0, -tw, gz1, k1, 0.0, t2, "#d4eef8")
    block(tw, gx1, gz1, k1, 0.0, t2, "#d4eef8")
    block(-tw, tw, gz1, k1, TUNNEL_H, t2, ICE_DEEP)
    block(gx0, gx1, gz0, gz1, GROTTO_H, t2, ICE_DEEP)
    for sgn in (-1.0, 1.0):
        a, c = sorted((sgn * hw3, sgn * hw2))
        block(a, c, k3, k2, 0.0, t2, "#d4eef8")
    # the third, solid
    block(-hw3, hw3, k3, k2, 0.0, t3, ICE)
    # the snow lying on each step, and on the strips beside the steps above
    for hw, f, k, t in GLACIER:
        block(-hw, hw, k, f, t, t + 0.3, SNOW)
    for sgn in (-1.0, 1.0):
        a, c = sorted((sgn * hw2, sgn * hw1))
        block(a, c, k3, k1, t1, t1 + 0.3, SNOW)
        a, c = sorted((sgn * hw3, sgn * hw2))
        block(a, c, k3, k2, t2, t2 + 0.3, SNOW)
    # ice crags behind it: nothing to fall into off the back
    hz = HALF[1]
    isle.cliffs("x", -hw1, hw1, -hz - b.margin, k3, 30.0, (ICE, "#d4eef8", ICE_DEEP, "#a8d8ec"), green=SNOW,
                vines=False, recess=0.0, step=16.0)
    # the faces: blue streaks, clear ice set into them, icicles off the lips
    for n, (hw, f, k, t) in enumerate(GLACIER):
        y0 = 0.0 if n == 0 else GLACIER[n - 1][3]
        x = -hw + 3.0
        j = 0
        while x < hw - 3.0:
            stair = ((49.0, 57.0), (29.0, 37.0), (17.0, 25.0))[n]
            if not (abs(x) < tw + 1.5 and n == 0) and not (stair[0] < abs(x) < stair[1]):
                h = (t - y0) * rng.uniform(0.4, 0.9)
                b.box([x, t - h / 2.0, f + 0.15], [1.2, h, 0.3], (ICE_DEEP, "#a8d8ec", ICE_DARK)[j % 3],
                      collide=False)
                if j % 2 == 0:
                    b.cone([x + 1.4, t - 1.0, f + 0.5], [0.8, 2.0, 0.8], "#e8f8ff", collide=False,
                           r=[math.pi, 0.0, 0.0])
            x += 3.6
            j += 1
    # the stairs cut up the steps: from the snow, then step to step
    for sgn in (-1.0, 1.0):
        a, c = sorted((sgn * 50.0, sgn * 56.0))
        flight(b, "z", f1 + 8.0, f1, a, c, 0.0, t1, ICE_DEEP, fill=0.0)
        a, c = sorted((sgn * 30.0, sgn * 36.0))
        flight(b, "z", f2 + 6.0, f2, a, c, t1, t2, ICE_DEEP, fill=t1)
        a, c = sorted((sgn * 18.0, sgn * 24.0))
        flight(b, "z", f3 + 6.0, f3, a, c, t2, t3, ICE_DEEP, fill=t2)
    # on top: the frost beacon, a column of ice with blue fire in its crown
    b.box([0.0, t3 + 0.3 + 4.0, -104.0], [3.0, 8.0, 3.0], "#d4eef8")
    b.cyl([0.0, t3 + 0.3 + 8.4, -104.0], [3.6, 0.8, 3.6], IRON, material="metal")
    b.cone([0.0, t3 + 0.3 + 10.0, -104.0], [2.6, 2.6, 2.6], "#7ad8ff", material="neon", collide=False)
    b.rig("rr_flame", 0.0, t3 + 0.3 + 9.0, -104.0, s=1.2)
    isle.loot(0.0, t3 + 0.3, -98.0, "gem", "the top of the glacier")
    for sgn in (-1.0, 1.0):
        isle.loot(sgn * 40.0, t2 + 0.3, -84.0, "bar", "the glacier")
        isle.loot(sgn * 66.0, t1 + 0.3, -68.0, "any", "the glacier's first step")
    b.landmark(0.0, -100.0, "the glacier")


def _grotto(isle: Isle) -> None:
    """The ice grotto: a passage into the glacier's foot opening into a
    blue chamber, crystals growing out of its walls, treasure frozen into
    the floor."""
    b = isle.b
    gx0, gx1, gz0, gz1 = GROTTO
    s = isle.s
    for k, (x, z) in enumerate(((-12.0, -90.0), (12.0, -90.0), (-14.0, -84.0), (14.0, -84.0), (0.0, -91.0))):
        face = 1.0 if x < 0 else -1.0
        b.box([x, 0.7, z], [2.4, 1.4, 1.6], ICE_DEEP)
        for j in range(3):
            h = 2.2 + j * 0.8
            b.box([x + (j - 1) * 0.7, 1.4 + h / 2.0, z], [0.6, h, 0.6], ("#7ad8ff", "#bff4ff", "#5ab8ff")[j],
                  material="neon", collide=False, r=[0.0, 0.0, face * (0.25 - j * 0.12)])
    b.box([0.0, GROTTO_H - 0.2, (gz0 + gz1) / 2.0], [6.0, 0.4, 0.6], "#bff4ff", material="neon", collide=False)
    for z in (-64.0, -72.0, -79.0):
        b.box([0.0, TUNNEL_H - 0.2, z], [0.6, 0.4, 2.0], "#7ad8ff", material="neon", collide=False)
    isle.loot(0.0, 0.0, -86.0, "gem", "the ice grotto")
    isle.loot(-9.0, 0.0, -88.0, "bar", "the ice grotto")
    isle.loot(9.0, 0.0, -88.0, "bar", "the ice grotto")
    b.landmark(0.0, -86.0, "the ice grotto")


# =========================================================== the galleon
def _galleon(isle: Isle) -> None:
    """The frozen galleon: a ship caught by the winter and held, her hull
    in the ice to the gunwales, her decks white, her sails frozen stiff,
    icicles off every yard -- the idol on her quarterdeck."""
    b = isle.b
    x0, x1, z0, z1 = SHIP
    b.box([0.0, DECK / 2.0, (z0 + z1) / 2.0], [x1 - x0, DECK, z1 - z0], WOOD)
    b.box([0.0, (DECK + FORE_Y) / 2.0, (16.0 + z1) / 2.0], [x1 - x0, FORE_Y - DECK, z1 - 16.0], "#7a5a3a")
    b.box([0.0, FORE_Y / 2.0, z1 + 2.0], [10.0, FORE_Y, 4.0], "#7a5a3a")
    b.box([0.0, (DECK + QUARTER_Y) / 2.0, (z0 - 2.0 + (-14.0)) / 2.0 + 1.0], [x1 - x0, QUARTER_Y - DECK, 10.0],
          "#7a5a3a")
    b.box([0.0, 12.0 / 2.0, z0 - 1.0], [x1 - x0 - 1.0, 12.0, 2.0], WOOD)
    # snow on her decks, the gold of her trim, frost up her sides
    b.box([0.0, DECK + 0.15, (-14.0 + 16.0) / 2.0], [x1 - x0 - 1.2, 0.3, 30.0 - 0.2], SNOW, collide=False)
    for sgn in (-1.0, 1.0):
        b.box([sgn * (x1 + 0.05), 3.6, (z0 + z1) / 2.0], [0.1, 0.5, z1 - z0], "#c8a040", collide=False)
        b.box([sgn * (x1 + 0.05), 1.0, (z0 + z1) / 2.0], [0.1, 2.0, z1 - z0], "#e8f4fc", collide=False)
    # the ramps of hard snow up her sides, the stairs aboard
    for sgn in (-1.0, 1.0):
        flight(b, "x", sgn * 14.0, sgn * x1, -3.0, 3.0, 0.0, DECK, SNOW_SHADE, fill=0.0)
        a, c = sorted((sgn * 2.5, sgn * 6.5))
        flight(b, "z", 12.0, 16.0, a, c, DECK, FORE_Y, "#7a5a3a", fill=DECK)
        flight(b, "z", -10.0, -14.0, a, c, DECK, QUARTER_Y, "#7a5a3a", fill=DECK)
        for za, zb in ((-14.0, -3.0), (3.0, 16.0)):
            b.box([sgn * (x1 - 0.3), DECK + 0.6, (za + zb) / 2.0], [0.6, 1.2, zb - za], "#7a5a3a")
        b.box([sgn * (x1 - 0.3), FORE_Y + 0.6, (16.0 + z1) / 2.0], [0.6, 1.2, z1 - 16.0], "#7a5a3a")
        b.box([sgn * (x1 - 0.3), QUARTER_Y + 0.6, (z0 + (-14.0)) / 2.0], [0.6, 1.2, 10.0], "#7a5a3a")
    # masts, yards and frozen sails, icicles hanging off them
    for z, base, top in ((20.0, FORE_Y, 24.0), (1.0, DECK, 30.0), (-22.6, QUARTER_Y, 22.0)):
        b.cyl([0.0, (base + top) / 2.0, z], [1.4, top - base, 1.4], WOOD)
        for yard in (top - 3.0, top - 9.0):
            if yard <= base + 4.0:
                continue
            b.box([0.0, yard, z], [14.0, 0.6, 0.6], WOOD)
            b.box([0.0, yard - 2.9, z + 0.36], [12.0, 5.2, 0.12], "#f4f8fc", alpha=0.92, collide=False)
            for k in range(6):
                b.cone([-5.5 + k * 2.2, yard - 6.0, z + 0.4], [0.5, 1.4, 0.5], "#e8f8ff", collide=False,
                       r=[math.pi, 0.0, 0.0])
        b.rig("rr_flag", 0.0, top - 0.2, z, yaw=math.pi / 2.0, w=4.0, h=2.4, colours=["#141414", "#f4f0e0"])
    # the idol on her quarterdeck, the wheel frozen at the helm
    isle.idol(0.0, QUARTER_Y, -18.0, colour="#8aa0b4")
    b.cyl([5.6, QUARTER_Y + 1.6, -21.0], [0.5, 3.2, 0.5], WOOD)
    b.cyl([5.6, QUARTER_Y + 3.3, -20.6], [2.8, 0.3, 2.8], "#7a5a3a", collide=False, r=[math.pi / 2.0, 0.0, 0.0])
    # her hold's hatch open, lantern light in it
    b.box([0.0, DECK + 0.32, 8.0], [3.2, 0.04, 3.2], "#1a1410", collide=False)
    b.box([0.0, DECK + 0.36, 8.0], [1.6, 0.04, 1.6], "#ffb05a", material="neon", collide=False)
    isle.loot(-4.0, DECK, 8.0, "bar", "the frozen galleon")
    isle.loot(3.0, FORE_Y, 21.0, "any", "the frozen galleon's forecastle")
    isle.loot(-3.0, DECK, -6.0, "any", "the frozen galleon")
    b.landmark(0.0, 0.0, "the frozen galleon")


def _holes(isle: Isle) -> None:
    """The breathing holes round the galleon: where the kraken comes up."""
    b = isle.b
    for x, z in HOLES:
        b.mark("tentacle", x, SEABED, z)
        for k in range(8):
            a = k * math.tau / 8.0 + 0.3
            r = HOLE_R + 0.6
            b.box([x + math.cos(a) * r, 0.25, z + math.sin(a) * r], [1.6, 0.5, 1.2], ("#e8f8ff", ICE)[k % 2],
                  collide=False, r=[0.0, -a, 0.0])
    b.landmark(0.0, 38.0, "the breathing holes")


# ================================================================ the wings
def _spruce(isle: Isle, x: float, z: float, h: float) -> None:
    """A spruce weighed down with snow: a trunk, tiers of dark green
    going up to a point, snow lying on every tier."""
    b = isle.b
    y = isle.top(x, z)
    b.cyl([x, y + 1.2, z], [0.9, 2.4, 0.9], WOOD)
    for k in range(4):
        w = h * 0.55 * (1.0 - k * 0.2)
        yy = y + 2.0 + k * h * 0.2
        b.cone([x, yy + h * 0.14, z], [w, h * 0.3, w], SPRUCE, collide=k == 0)
        b.cone([x, yy + h * 0.25, z], [w * 0.6, h * 0.1, w * 0.6], SNOW, collide=False)


def _half(isle: Isle, sgn: float) -> None:
    """One crew's wing (mirrored for the other): the whalers' camp --
    painted huts with snow on their roofs, the try-pot, barrels, a sled --
    spruces, a fishing shack on the shore."""
    b = isle.b
    rng = isle.rng
    west = sgn < 0

    def X(x: float) -> float:
        return sgn * x

    for k, (area, door, paint) in enumerate(HUTS):
        x0, x1 = sorted((X(area[0]), X(area[1])))
        if door in ("x-", "x+") and west:
            door = "x+" if door == "x-" else "x-"
        dx, dz = isle.hut(rect(x0, x1, area[2], area[3]), door, colour=paint, roof=SNOW, height=7.0)
        cx = x1 - 1.6 if sgn > 0 else x0 + 1.6
        b.box([cx, 6.5, area[2] + 1.6], [1.6, 13.0, 1.6], "#7a7a84")
        b.rig("rr_smoke", cx, 13.4, area[2] + 1.6, wind=[0.8, 0.3], rate=0.25, h=16.0, size=1.4, colour="#e8ecf0")
        isle.loot((x0 + x1) / 2.0, 0.4, (area[2] + area[3]) / 2.0, "bar" if k == 0 else "any", "a whalers' hut")
    # the try-pot: a fire under an iron cauldron, barrels of oil by it
    tx, tz = X(77.0), 55.0
    b.box([tx, 1.2, tz], [8.0, 2.4, 6.0], "#8a5040")
    b.cyl([tx, 3.2, tz], [5.0, 1.6, 5.0], IRON, material="metal")
    b.cyl([tx, 4.05, tz], [4.2, 0.1, 4.2], "#c8a050", collide=False)
    b.box([tx, 0.9, tz + 3.05], [2.4, 1.2, 0.1], "#ff7a2a", material="neon", collide=False)
    b.rig("rr_smoke", tx, 4.4, tz, wind=[0.6, 0.4], rate=0.2, h=14.0, size=1.6, colour="#8a8480")
    for k in range(3):
        isle.barrel(X(71.0 + k * 3.2), 63.0, colour="#5a3a22")
    # a dog sled with its load, the harness laid out in the snow
    sx, sz = X(72.0), -4.0
    for e in (-1.0, 1.0):
        b.box([sx + e * 1.2, 0.2, sz], [0.3, 0.4, 7.0], WOOD)
    b.box([sx, 0.9, sz], [3.0, 0.4, 5.6], "#8a6a44")
    isle.crates(sx - 1.2, sz - 1.8, y=1.1, n=2)
    b.box([sx, 0.04, sz + 6.0], [0.3, 0.08, 5.0], "#5a4a3a", collide=False)
    # a fishing shack on the shore, its hole in the ice beside it
    fx0, fx1 = sorted((X(98.0), X(106.0)))
    isle.hut(rect(fx0, fx1, 56.0, 64.0), "z+", colour="#3a7a8a", roof=SNOW, height=6.0)
    isle.loot((fx0 + fx1) / 2.0, 0.4, 60.0, "gem", "the fishing shack")
    # spruces, rocks breaking through the snow, a flagpole
    for x, z, h in ((66.0, -52.0, 12.0), (72.0, 76.0, 13.0), (104.0, 84.0, 11.0), (92.0, -84.0, 14.0),
                    (86.0, -92.0, 12.0), (106.0, -70.0, 12.0), (100.0, 4.0, 11.0), (78.0, 30.0, 12.0)):
        if isle.clear(X(x), z, 3.0):
            _spruce(isle, X(x), z, h)
    for x, z, w in ((88.0, -72.0, 4.0), (60.0, 88.0, 3.4), (104.0, 50.0, 3.0)):
        if isle.clear(X(x), z, 3.0):
            isle.rock(X(x), z, w, w * 0.8, w * 0.6, colour="#6a7480", cap=SNOW)
    isle.flag(X(108.0), 0.0, None, "#c8302a" if west else "#2a6ab8", h=11.0)
    # X's and loot
    isle.dig(X(78.0), None, -10.0, "the whalers' camp")
    isle.dig(X(60.0), None, 40.0, "the snowfield")
    isle.dig(X(96.0), None, -64.0, "under the crags")
    isle.dig(X(80.0), None, 86.0, "the south shore")
    isle.dig(X(40.0), None, -54.0, "the glacier's foot")
    isle.loot(X(104.0), None, -40.0, "any", "the shore")
    isle.loot(X(74.0), None, 24.0, "any", "the snowfield")
    isle.loot(X(40.0), None, 60.0, "any", "the pack ice's edge")
    isle.loot(X(36.0), None, 0.0, "gem", "the pack ice")


def _snowfield(isle: Isle) -> None:
    """The snowfield south of the pack ice: igloos to shelter in, snowmen
    somebody built, seracs of ice standing up out of the snow -- and a
    tentacle of the kraken's, frozen where it broke through one winter."""
    b = isle.b
    for sgn in (-1.0, 1.0):
        for r in IGLOOS:
            x0, x1 = sorted((sgn * r[0], sgn * r[1]))
            z0, z1 = r[2], r[3]
            cx, cz = (x0 + x1) / 2.0, (z0 + z1) / 2.0
            t = 1.0
            b.box([cx, 3.0, z0 + t / 2.0], [x1 - x0, 6.0, t], SNOW_SHADE)
            for xa, xb in ((x0, cx - 1.6), (cx + 1.6, x1)):
                b.box([(xa + xb) / 2.0, 3.0, z1 - t / 2.0], [xb - xa, 6.0, t], SNOW_SHADE)
            for xx in (x0 + t / 2.0, x1 - t / 2.0):
                b.box([xx, 3.0, cz], [t, 6.0, z1 - z0 - 2 * t], SNOW_SHADE)
            for k, inset in enumerate((0.0, 1.6, 3.2)):
                b.box([cx, 6.0 + 0.5 + k, cz], [x1 - x0 - 2 * inset, 1.0, z1 - z0 - 2 * inset], (SNOW, SNOW_SHADE)[k % 2])
            for k in range(4):
                b.box([x0 - 0.05, 1.0 + k * 1.4, cz], [0.1, 0.06, z1 - z0 - 1.0], "#c8d8e4", collide=False)
            isle.loot(cx, 0.0, cz - 1.0, "gem" if sgn < 0 else "gem", "an igloo")
        # snowmen
        for x, z in ((14.0, 62.0), (60.0, 86.0)):
            px = sgn * x
            b.sphere([px, 1.4, z], [3.2, 2.8, 3.2], SNOW)
            b.sphere([px, 3.6, z], [2.4, 2.2, 2.4], SNOW, collide=False)
            b.sphere([px, 5.3, z], [1.7, 1.6, 1.7], SNOW, collide=False)
            b.cone([px, 5.3, z + 1.2], [0.4, 1.2, 0.4], "#ff8a2a", collide=False, r=[math.pi / 2.0, 0.0, 0.0])
            for dx in (-0.35, 0.35):
                b.sphere([px + dx, 5.6, z + 0.75], [0.25, 0.25, 0.25], "#1a1a1a", collide=False)
            b.box([px, 6.35, z], [1.4, 0.5, 1.4], "#1a1a22", collide=False)
            b.box([px, 4.5, z], [2.2, 0.4, 0.5], "#c8302a" if sgn < 0 else "#2a6ab8", collide=False)
        # seracs: blades of ice standing up out of the snow
        for x, z in ((44.0, 56.0), (56.0, 30.0), (82.0, 70.0), (20.0, 90.0)):
            px = sgn * x
            for k, (dx, dz, w, h) in enumerate(((0.0, 0.0, 2.4, 7.0), (2.0, 1.2, 1.6, 4.6), (-1.6, 1.6, 1.8, 3.4),
                                                (1.0, -1.8, 1.4, 5.4))):
                b.box([px + sgn * dx, h / 2.0, z + dz], [w, h, w * 0.8], (ICE, "#d4eef8", ICE_DEEP, "#a8d8ec")[k])
    # the frozen tentacle, arching up out of the snow and back into it
    pts = []
    for i in range(15):
        u = i / 14.0
        pts.append((0.0, 15.0 * math.sin(u * math.pi) + 0.6, 50.0 + u * 16.0))
    for i in range(1, len(pts)):
        (x0, y0, z0), (x1, y1, z1) = pts[i - 1], pts[i]
        w = 3.4 - 1.8 * abs(i / 14.0 - 0.35)
        b.box([0.0, (y0 + y1) / 2.0, (z0 + z1) / 2.0], [w, math.hypot(y1 - y0, z1 - z0) + 0.6, w],
              ("#a8d8ec", "#c8e8f8")[i % 2], collide=False, r=[math.atan2(z1 - z0, y1 - y0), 0.0, 0.0])
        if i % 3 == 0:
            b.sphere([0.0 - w / 2.0 - 0.3, (y0 + y1) / 2.0, (z0 + z1) / 2.0], [0.9, 0.9, 0.9], "#f0faff",
                     collide=False, r=[0.0, 0.0, 0.2])
    for z in (50.0, 66.0):
        b.box([0.0, 1.0, z], [4.4, 2.0, 4.4], ICE_DEEP)
    b.landmark(0.0, 58.0, "the frozen tentacle")


def _shore(isle: Isle) -> None:
    """The south shore: floes of ice afloat in the sea -- one to the next --
    seals hauled out on them, penguins about."""
    b = isle.b
    rng = isle.rng
    for k, (x, z, w, d) in enumerate(((-70.0, 106.0, 10.0, 7.0), (-46.0, 112.0, 8.0, 8.0), (-22.0, 106.0, 9.0, 6.0),
                                       (0.0, 113.0, 12.0, 8.0))):
        for sgn in ((1.0,) if x == 0.0 else (-1.0, 1.0)):
            px = sgn * x
            b.box([px, -1.0, z], [w, 1.2, d], ("#f4faff", "#e0f0f8")[k % 2], studs=True)
            b.box([px + 0.4, -0.36, z - 0.2], [w - 2.0, 0.08, d - 2.0], ICE, collide=False)
    for sgn in (-1.0, 1.0):
        b.sphere([sgn * 46.0, 0.2, 112.0], [3.4, 1.4, 1.6], "#7a8088")
        b.sphere([sgn * 47.6, 0.6, 112.0], [1.2, 1.1, 1.1], "#7a8088")
    b.rig("pb_penguins", -46.0, -0.4, 112.0, r=3.0, n=3, seed=1.0)
    b.rig("pb_penguins", 0.0, -0.4, 113.0, r=4.0, n=4, seed=2.0)
    b.rig("pb_penguins", 22.0, -0.4, 106.0, r=3.0, n=3, seed=3.0)
    b.rig("pb_penguins", -60.0, 0.1, 94.0, r=8.0, n=6, seed=4.0)
    b.rig("pb_penguins", 60.0, 0.1, 94.0, r=8.0, n=6, seed=5.0)
    isle.loot(0.0, -0.4, 113.0, "gem", "the ice floes")
    b.landmark(0.0, 108.0, "the ice floes")


# ================================================================ meta
def _meta(isle: Isle) -> None:
    b = isle.b
    for x, z, name in ((-90.0, -40.0, "the west whalers' camp"), (90.0, -40.0, "the east whalers' camp"),
                       (-SHIP_X, 0.0, "the Scarlet Queen"), (SHIP_X, 0.0, "the Blue Marlin")):
        b.landmark(x, z, name)
    b.camera(0.0, 50.0, 112.0, 0.0, 6.0, -20.0)
    b.camera(-110.0, 40.0, 50.0, -10.0, 6.0, -10.0)
    b.camera(46.0, 34.0, -30.0, 0.0, 12.0, -90.0)
    b.camera(-40.0, 20.0, 40.0, 0.0, 6.0, 0.0)
    b.extra.update({"twist": "kraken", "water": SEA_TOP, "kraken_every": [52.0, 70.0], "kraken_for": 30.0,
                    "warn": 5.0, "style": {"kraken": "frost"}, "kraken_hp": 320.0,
                    "twist_text": {"warn": "THE ICE IS CRACKING", "warnSub": "Something huge is moving under the floe...",
                                   "on": "THE FROST KRAKEN!",
                                   "onSub": "Tentacles through the breathing holes -- stay clear of the rings, "
                                            "or cut one down for a jewel",
                                   "off": "The frost kraken sinks under the ice"}})
    b.rig("rr_weather", 0.0, 0.0, 0.0, weather="snow", wind=[0.6, 0.3])
    b.rig("pb_whale", 320.0, SEA_TOP, -40.0, r=70.0, seed=2.0)
    b.rig("pb_whale", -340.0, SEA_TOP, 120.0, r=60.0, seed=5.0, s=0.9)
    for sgn in (-1.0, 1.0):
        b.rig("rr_surf", sgn * (SHORE_X + 6.5), SEA_TOP + 0.3, -40.0, w=80.0, yaw=sgn * math.pi / 2.0)
        b.rig("rr_surf", sgn * (SHORE_X + 6.5), SEA_TOP + 0.3, 60.0, w=60.0, yaw=sgn * math.pi / 2.0)
        b.rig("rr_gulls", sgn * 80.0, 30.0, 20.0, r=24.0, n=3, seed=sgn * 4.0)
    b.rig("pb_glow", 0.0, 0.2, 0.0, n=40, w=100.0, d=90.0, seed=6.0, lift=0.4,
          colours=["#ffffff", "#e8fcff", "#c8f0ff"])


def build(b: ArenaArea) -> None:
    rng = random.Random(0xF205)
    isle = Isle(b, rng)
    _land(isle)
    _edges(isle)
    _glacier(isle)
    _grotto(isle)
    _galleon(isle)
    _holes(isle)
    _half(isle, -1.0)
    _half(isle, 1.0)
    _snowfield(isle)
    _shore(isle)
    galleon(isle, "red", 0.0)
    galleon(isle, "blue", 0.0)
    _meta(isle)
