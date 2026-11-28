"""Whalebone Atoll: a ring of white sand round a turquoise lagoon, and lying
across it the bones of a whale bigger than any ship -- its skull on the
north shore, its spine a bridge of vertebrae straight over the lagoon, its
ribs arching overhead like the frame of a cathedral, its flukes on the
south strand.

Layout (north is -z; the Scarlet Corsairs' ship off the west shore, the
Azure Buccaneers' off the east)::

    z -120  ===== rocks ===== THE SKULL (its jaw standing up behind) ===== rocks =====
    z  -94    dune                (the idol in its cranium)                 dune
    z  -64   try-works   ======= the north strand, the spine's stairs =======  try-works
   SCARLET   jawbone  ~~~~~~ THE LAGOON ~~~ the spine ~~~ THE LAGOON ~~~~~~  jawbone   BLUE
    QUEEN    arches,  ~~~~~~ ribs arching ~~ (the eye) ~~ ribs arching ~~~~~  arches,   MARLIN
             the dune ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  the dune
    z   37   scrimshaw hut       | the south strand, the tail |        scrimshaw hut
    z   64   tide pools, coral    the beached whaleboats            coral, tide pools
    z   86   the dune                    THE FLUKES                          the dune
    z  100  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~ the south sea ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The halves are mirror images: each crew has its wing of the atoll, its
jawbone arches, its try-works, its scrimshaw hut, its dunes and its tide
pools.  The skull, the spine and the flukes are as far from one ship as the
other.

The twist is the maelstrom (``extra["twist"] = "maelstrom"``): the lagoon
starts to turn round the eye under the middle of the spine
(``extra["vortex"]``).  Anybody in the water is dragged round and in, the
eye drowns, and the deep throws its treasure up onto the lagoon's beaches
(``rim`` marks) -- for whoever dares go and get it.  Up on the spine you
are safe, unless somebody knocks you off.
"""
from __future__ import annotations

import math
import random

from ..calamity_coast.town import skirt
from ..kit import ArenaArea, backdrop, flight, rect, slab
from .common import (IRON, PLANK, ROCK, ROCK_DARK, ROCK_LIGHT, SAND, SAND_WET, SEA_TOP, SEABED,
                     SHIP_X, SHORE_X, TIMBER, Isle, galleon)

HALF = (170.0, 120.0)
SKY = {"top": "#2f8ad8", "horizon": "#d8f4ff", "sun": [0.45, 0.6, 0.35], "clouds": 0.4,
       "tint": "#fff8ec"}
AMBIENT = "#b8c8d0"
GROUND = "#f0e2b4"
FOG = 900.0

STRAND = "#f0e2b4"           # the atoll's white sand
GROVE = "#7ab85a"            # the palm groves' grass
PATH = "#e2cc98"
BONE = "#efe8d6"
BONE_SHADE = "#d8cfb4"
BONE_DARK = "#b8ad92"
LAGOON_C = "#3ad0d8"
CORAL = ("#ff7a8a", "#ff9a5a", "#c86aff", "#ffd04a", "#ff5ab8")
BED = -5.0                   # the lagoon's floor: chest-deep
LAGOON = (-66.0, 66.0, -58.0, 46.0)
RINGS = (-1.2, -2.4, -3.6)   # its banks, stepping down
RING_W = 4.0
SOUTH = 100.0                # the south shore
NORTH = -98.0                # the foot of the rocks either side of the skull
SPINE_Y = 6.0                # the top of the vertebrae over the lagoon
SPINE = (-3.0, 3.0)          # the spine's width
VORTEX = (0.0, -6.0)
SKULL = (-18.0, 18.0, -104.0, -78.0)
RIB_Z = (-46.0, -33.0, -20.0, -7.0, 6.0, 19.0, 32.0)
CAMP = (80.0, 98.0, -56.0, -42.0)          # the try-works, east side (mirrored west)
HUT = (82.0, 98.0, 30.0, 44.0)             # the scrimshaw hut
POOLS = ((86.0, 64.0, 7.0), (70.0, 80.0, 5.0))
DUNES = ((30.0, 52.0, -94.0, -78.0), (86.0, 104.0, -8.0, 8.0), (88.0, 108.0, 76.0, 96.0))
DUNE_STEP = 0.9
FLUKES = (-38.0, 38.0, 78.0, 100.0)        # kept clear of the ground covers


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
    pools = [rect(x - r, x + r, z - r, z + r) for x, z, r in POOLS] + \
            [rect(-x - r, -x + r, z - r, z + r) for x, z, r in POOLS]
    isle.land(STRAND, holes=[west, east, south, LAGOON] + pools, soil="#c8b48a")
    for area in (west, east, south):
        slab(b, area, SEABED, 3.0, SAND_WET, studs=True)
    # the beaches down into the open sea
    for k, top in enumerate((-1.0, -2.0)):
        colour = SAND if k == 0 else SAND_WET
        for sgn in (-1.0, 1.0):
            xa, xb = sorted((sgn * (SHORE_X + 3.0 * k), sgn * (SHORE_X + 3.0 * (k + 1))))
            b.box([(xa + xb) / 2.0, (SEABED + top) / 2.0, (NORTH + hz) / 2.0],
                  [xb - xa, top - SEABED, hz - NORTH], colour, studs=True)
        za, zb = SOUTH + 3.0 * k, SOUTH + 3.0 * (k + 1)
        b.box([0.0, (SEABED + top) / 2.0, (za + zb) / 2.0], [2 * SHORE_X, top - SEABED, zb - za], colour,
              studs=True)
    for area in ((-hx, -SHORE_X, -hz, hz), (SHORE_X, hx, -hz, hz), (-SHORE_X, SHORE_X, SOUTH, hz)):
        isle.water(area, SEABED, colour="#2aa8c8")
    for x0, x1, z0, z1 in ((-hx - m - 300.0, -hx - m, -hz - m - 300.0, hz + m + 300.0),
                           (hx + m, hx + m + 300.0, -hz - m - 300.0, hz + m + 300.0),
                           (-hx - m, hx + m, hz + m, hz + m + 300.0)):
        b.box([(x0 + x1) / 2.0, (SEABED - 6.0 + SEA_TOP) / 2.0, (z0 + z1) / 2.0],
              [x1 - x0, SEA_TOP - SEABED + 6.0, z1 - z0], "#2a98c0", material="glass", alpha=0.6,
              collide=False)
    # the lagoon: its floor, its banks stepping down, its turquoise water
    x0, x1, z0, z1 = LAGOON
    slab(b, LAGOON, BED, 3.0, "#e8dcae", studs=True)
    for k, top in enumerate(RINGS):
        a, c = k * RING_W, (k + 1) * RING_W
        colour = SAND if k == 0 else (SAND_WET if k == 1 else "#d8c890")
        for xa, xb in ((x0 + a, x0 + c), (x1 - c, x1 - a)):
            b.box([(xa + xb) / 2.0, (BED + top) / 2.0, (z0 + z1) / 2.0],
                  [xb - xa, top - BED, (z1 - a) - (z0 + a)], colour, studs=True)
        for za, zb in ((z0 + a, z0 + c), (z1 - c, z1 - a)):
            b.box([0.0, (BED + top) / 2.0, (za + zb) / 2.0], [(x1 - c) - (x0 + c), top - BED, zb - za], colour,
                  studs=True)
    isle.water(LAGOON, BED, colour=LAGOON_C, alpha=0.5)
    # the tide pools: little basins in the strand
    for x, z, r in POOLS:
        for sgn in (-1.0, 1.0):
            pr = rect(sgn * x - r, sgn * x + r, z - r, z + r)
            slab(b, pr, -1.4, 3.0, "#d8c890", studs=True)
            isle.water(pr, -1.4, -0.4, colour="#5ae0e8", alpha=0.55)
    # the dunes: sand heaped up in steps
    for sgn in (-1.0, 1.0):
        for r in DUNES:
            xa, xb = sorted((sgn * r[0], sgn * r[1]))
            for k in range(3):
                inset = k * 3.0
                top = DUNE_STEP * (k + 1)
                b.box([(xa + xb) / 2.0, top / 2.0, (r[2] + r[3]) / 2.0],
                      [xb - xa - 2 * inset, top, r[3] - r[2] - 2 * inset],
                      STRAND if k % 2 == 0 else "#e8d8a4", studs=True)
    # covers: kept off what stands on the strand itself; the paths first,
    # then the groves round them
    s = isle.s
    for r in (CAMP, _m(CAMP), HUT, _m(HUT), FLUKES) + DUNES + tuple(_m(d) for d in DUNES):
        s.reserve(r)
    for sgn in (-1.0, 1.0):
        def X(x: float, sgn: float = sgn) -> float:
            return sgn * x
        isle.trail([(X(109.5), -15.0), (X(76.0), -15.0), (X(76.0), -64.0), (X(24.0), -64.0)], colour=PATH)
        isle.trail([(X(109.5), 15.0), (X(74.0), 15.0), (X(74.0), 52.0), (X(12.0), 52.0)], colour=PATH)
    for sgn in (-1.0, 1.0):
        for gx0, gx1, gz0, gz1 in ((80.0, 108.0, -36.0, 26.0), (30.0, 62.0, 58.0, 76.0)):
            xa, xb = sorted((sgn * gx0, sgn * gx1))
            s.lay(rect(xa, xb, gz0, gz1), 0.12, GROVE)


# =============================================================== the edges
def _edges(isle: Isle) -> None:
    """The north is black rock either side of the skull; the other three
    sides are reefs of coral rock out in the sea."""
    b = isle.b
    hx, hz = HALF
    rng = isle.rng
    m = b.margin
    rocks = (ROCK_DARK, "#5a5a62", ROCK, "#6a6a70")
    for sgn in (-1.0, 1.0):
        a0, a1 = sorted((sgn * 17.0, sgn * SHORE_X))
        isle.cliffs("x", a0, a1, -hz - m, NORTH, rng.uniform(15.0, 18.0), rocks, green="#5a9a4a",
                    vines=False)
        a0, a1 = sorted((sgn * SHORE_X, sgn * (hx + m)))
        isle.cliffs("x", a0, a1, -hz - m, NORTH, 30.0, rocks, base=SEABED, green="#5a9a4a",
                    step=14.5, recess=0.0, vines=False)
        b.box([sgn * (hx + m / 2.0), (SEABED + 6.0) / 2.0, (NORTH + hz + m) / 2.0],
              [m, 6.0 - SEABED, hz + m - NORTH], "#c8a890")
    b.box([0.0, (SEABED + 6.0) / 2.0, hz + m / 2.0], [2 * hx, 6.0 - SEABED, m], "#c8a890")
    # the reef's crown: coral rock in pinks and ochres along the top
    for k in range(18):
        z = NORTH + (k + 0.5) * (hz + m - NORTH) / 18.0
        for sgn in (-1.0, 1.0):
            b.box([sgn * (hx + m / 2.0) + rng.uniform(-1.0, 1.0), 6.0 + 1.0 + (k % 3) * 0.4, z],
                  [m - 2.0 - (k % 2) * 0.6, 2.0 + (k % 3) * 0.8, (hz + m - NORTH) / 18.0 - 2.0],
                  CORAL[k % len(CORAL)] if k % 3 == 0 else "#d8b8a0")
    for k in range(18):
        x = -hx + (k + 0.5) * 2 * hx / 18.0
        b.box([x, 6.0 + 1.0 + (k % 3) * 0.4, hz + m / 2.0 + rng.uniform(-1.0, 1.0)],
              [2 * hx / 18.0 - 2.0, 2.0 + (k % 3) * 0.8, m - 2.0 - (k % 2) * 0.6],
              CORAL[(k + 1) % len(CORAL)] if k % 3 == 0 else "#d8b8a0")
    skirt(b, hx, hz, "#d8c890", top=SEABED - 3.05)
    backdrop(b, "hills", 8.0, rng, sides=("z-",), colours=["#3a7a5a", "#4a8a62", "#2e6a4e"], depth=160.0)
    # far atolls on the horizon
    for x, z, w in ((-460.0, -300.0, 90.0), (420.0, 330.0, 120.0), (520.0, -220.0, 70.0),
                    (-520.0, 260.0, 80.0)):
        b.sphere([x, -2.0, z], [w, 8.0, w * 0.6], STRAND, collide=False)
        b.sphere([x + w * 0.1, 3.0, z], [w * 0.5, 10.0, w * 0.3], "#3a8a3a", collide=False)


# ================================================================ the whale
def _skull(isle: Isle) -> None:
    """A sperm whale's skull on the north shore, bigger than a church: the
    cranium a hall with a stepped dome, its doorway on the lagoon side where
    the spine meets it, an eye socket each side for a window -- and the
    idol on its altar inside."""
    b = isle.b
    x0, x1, z0, z1 = SKULL
    t = 2.4
    h = 14.0
    # the walls: open in the south (the door) and at each eye socket
    b.box([(x0 + x1) / 2.0, h / 2.0, z0 + t / 2.0], [x1 - x0, h, t], BONE)
    for xa, xb in ((x0, -5.0), (5.0, x1)):
        b.box([(xa + xb) / 2.0, h / 2.0, z1 - t / 2.0], [xb - xa, h, t], BONE)
    b.box([0.0, (9.0 + h) / 2.0, z1 - t / 2.0], [10.0, h - 9.0, t], BONE)
    for xx in (x0 + t / 2.0, x1 - t / 2.0):
        for za, zb, y0, y1 in ((z0 + t, -95.0, 0.0, h), (-87.0, z1 - t, 0.0, h), (-95.0, -87.0, 0.0, 4.0),
                               (-95.0, -87.0, 10.0, h)):
            b.box([xx, (y0 + y1) / 2.0, (za + zb) / 2.0], [t, y1 - y0, zb - za],
                  BONE_SHADE if y1 < h else BONE)
    slab(b, rect(x0 + t, x1 - t, z0 + t, z1 - t), 0.2, 0.2, "#d8cfb4", studs=True)
    # the dome: tiers stepping in
    for k in range(4):
        inset = k * 3.2
        slab(b, rect(x0 - 0.6 + inset, x1 + 0.6 - inset, z0 - 0.6 + inset, z1 + 0.6 - inset),
             h + 1.4 * (k + 1), 1.4, BONE if k % 2 == 0 else BONE_SHADE)
    # the heavy brow over the door, and the dark rims of the eye sockets
    b.box([0.0, h - 1.0, z1 + 1.5], [18.0, 2.0, 3.0], BONE_SHADE)
    # its face: deep dark sockets under the brow, the blowhole's slot, and
    # the doorway its mouth -- fangs hanging over it (out of reach), tusks
    # standing either side
    for sgn in (-1.0, 1.0):
        b.box([sgn * 10.5, 9.6, z1 + 0.15], [5.6, 3.6, 0.3], "#3a3430", collide=False)
        b.box([sgn * 10.5, 9.6, z1 + 0.35], [2.4, 1.6, 0.1], "#ffb84a", material="neon", collide=False)
        b.cone([sgn * 6.6, 2.6, z1 + 1.0], [1.6, 5.2, 1.6], "#fffaf0")
    b.box([0.0, 11.4, z1 + 0.15], [2.0, 1.2, 0.3], "#3a3430", collide=False)
    for k in range(5):
        b.cone([-4.0 + k * 2.0, 8.0, z1 + 0.6], [1.2, 2.0, 1.2], "#fffaf0", collide=False,
               r=[math.pi, 0.0, 0.0])
    for xx, sgn in ((x0, -1.0), (x1, 1.0)):
        b.box([xx + sgn * 0.3, 11.0, -91.0], [0.6, 2.0, 10.0], BONE_DARK)
    # barnacles crusting the walls, and the old harpoons still in them
    for k in range(8):
        bx = x0 + 3.0 + k * 4.3
        if abs(bx) < 6.5:
            continue            # not in the doorway
        b.sphere([bx, 1.0 + (k % 3) * 2.6, z1 + 0.3], [1.2, 1.0, 0.8], "#9a968a", collide=False)
    for sgn in (-1.0, 1.0):
        for k in range(3):
            b.cyl([sgn * (x1 + 1.6), 8.0 + k * 1.6, -100.0 + k * 3.0], [0.3, 4.0, 0.3], IRON,
                  material="metal", collide=False, r=[0.0, 0.0, sgn * 1.2])
    # inside: the idol's altar, lit by the eye sockets; lanterns on the walls
    isle.idol(0.0, 0.2, -94.0, colour=BONE_SHADE)
    for xx, sgn in ((x0 + t, 1.0), (x1 - t, -1.0)):
        for zz in (-99.0, -83.0):
            b.box([xx + sgn * 0.25, 7.0, zz], [0.5, 0.8, 0.8], IRON, material="metal")
            b.box([xx + sgn * 0.3, 7.9, zz], [0.6, 1.0, 0.6], "#ffc86a", material="neon")
    # (on its floor: under the dome, not on it)
    isle.loot(0.0, 0.2, -86.0, "gem", "the skull")
    isle.loot(-10.0, 0.2, -97.0, "bar", "the skull")
    isle.loot(10.0, 0.2, -97.0, "bar", "the skull")


def _mandible(isle: Isle) -> None:
    """The lower jaw, standing on end behind the skull like a tusk: two long
    bones rising from the rocks, meeting at the tip far overhead, a row of
    teeth along each -- the atoll's landmark, seen from everywhere."""
    b = isle.b
    z_base, z_tip = -107.0, -118.0
    for sgn in (-1.0, 1.0):
        p0 = (sgn * 6.0, 0.0, z_base)
        p1 = (sgn * 7.0, 30.0, z_base + 4.0)
        p2 = (sgn * 1.0, 50.0, z_tip)
        prev = p0
        n = 14
        for i in range(1, n + 1):
            t = i / float(n)
            pt = tuple((1 - t) ** 2 * p0[j] + 2 * (1 - t) * t * p1[j] + t * t * p2[j] for j in range(3))
            dy, dz = pt[1] - prev[1], pt[2] - prev[2]
            seg = math.hypot(dy, dz)
            rx = math.atan2(dz, dy)
            w = 3.2 - 1.6 * t
            mid = [(prev[0] + pt[0]) / 2.0, (prev[1] + pt[1]) / 2.0, (prev[2] + pt[2]) / 2.0]
            b.box(mid, [w, seg + 0.6, w * 1.3], BONE if i % 2 else BONE_SHADE, collide=False,
                  r=[rx, 0.0, 0.0])
            if 3 <= i <= n - 2:
                b.cone([mid[0] - sgn * (w / 2.0 + 0.5), mid[1], mid[2] + 0.4], [1.2, 2.2, 1.2], "#fffaf0",
                       collide=False, r=[0.0, 0.0, sgn * 1.4])
            prev = pt
    b.box([0.0, 0.8, z_base], [16.0, 1.6, 4.0], BONE_DARK)


def _spine(isle: Isle) -> None:
    """The spine: vertebrae marching across the lagoon from the north strand
    to the south, each a block of bone with its processes jutting out at the
    sides, a stair of bone down onto the sand at each end.  The discs
    between are a hand lower: a bumpy road over the water."""
    b = isle.b
    x0, x1 = SPINE
    za, zb = LAGOON[2], LAGOON[3]
    flight(b, "z", za - 12.0, za, x0, x1, 0.0, SPINE_Y, BONE_SHADE, fill=0.0, rise=1.0)
    flight(b, "z", zb + 12.0, zb, x0, x1, 0.0, SPINE_Y, BONE_SHADE, fill=0.0, rise=1.0)
    n = 17
    pitch = (zb - za) / n
    for k in range(n):
        z0 = za + k * pitch
        z1 = zb if k == n - 1 else z0 + pitch - 0.8
        b.box([0.0, (BED + SPINE_Y) / 2.0, (z0 + z1) / 2.0], [x1 - x0, SPINE_Y - BED, z1 - z0],
              BONE if k % 2 else "#e8e0ca")
        # the transverse processes out each side, under the deck
        for sgn in (-1.0, 1.0):
            b.box([sgn * 5.2, SPINE_Y - 0.6, (z0 + z1) / 2.0], [4.4, 0.8, 2.0], BONE_SHADE, collide=False)
            b.box([sgn * 3.4, SPINE_Y - 2.4, (z0 + z1) / 2.0], [0.8, 2.6, 3.0], BONE_DARK)
        # the spinous process standing up from the middle -- low enough to step on
        b.box([0.0, SPINE_Y + 0.3, (z0 + z1) / 2.0], [1.4, 0.6, 2.2], BONE_SHADE)
        if k < n - 1:
            b.box([0.0, (BED + SPINE_Y - 0.4) / 2.0, z1 + 0.4], [x1 - x0 - 0.6, SPINE_Y - 0.4 - BED, 0.8],
                  BONE_DARK)
    # the tail: vertebrae getting smaller across the south strand to the flukes
    z = zb + 13.0
    for k, (hgt, w) in enumerate(((1.6, 5.0), (1.3, 4.6), (1.0, 4.2), (0.7, 3.8))):
        b.box([0.0, hgt / 2.0, z + 2.0], [w, hgt, 4.0], BONE if k % 2 else BONE_SHADE)
        z += 5.2
    isle.loot(0.0, None, -6.0, "gem", "the spine")
    isle.loot(0.0, None, -36.0, "bar", "the spine")
    isle.loot(0.0, None, 24.0, "bar", "the spine")


def _ribs(isle: Isle) -> None:
    """The ribs: great curved bones springing from the spine, arching high
    over the water and coming down into the lagoon either side, where their
    feet stand on the bottom -- solid, coral-crusted, barnacled."""
    b = isle.b
    last = len(RIB_Z) - 1
    for k, z in enumerate(RIB_Z):
        swell = math.sin(k / float(last) * math.pi)
        reach = 40.0 + 8.0 * swell
        peak = 24.0 + 8.0 * swell
        for sgn in (-1.0, 1.0):
            # a quadratic curve: off the spine's side, up over, down to the foot
            p0 = (6.0, SPINE_Y - 1.0)
            p1 = (reach * 0.42, peak * 1.6)
            p2 = (reach, 5.2)
            n = 12
            prev = p0
            for i in range(1, n + 1):
                t = i / float(n)
                x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0]
                y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]
                dx, dy = x - prev[0], y - prev[1]
                ang = math.atan2(dy, dx)
                w = 2.6 - 0.8 * t
                b.box([sgn * (prev[0] + x) / 2.0, (prev[1] + y) / 2.0, z],
                      [math.hypot(dx, dy) + 0.5, w, w + 0.4], BONE if i % 3 else BONE_SHADE, collide=False,
                      r=[0.0, 0.0, ang if sgn > 0 else math.pi - ang])
                prev = (x, y)
            # the foot, standing on the lagoon's floor: solid, crusted
            fx = sgn * reach
            b.box([fx, (BED + 5.2) / 2.0, z], [2.6, 5.2 - BED, 3.0], BONE_SHADE)
            b.sphere([fx + sgn * 1.6, BED + 1.6, z + 0.8], [2.4, 2.8, 2.4], CORAL[k % len(CORAL)])
            b.sphere([fx - sgn * 1.4, SEA_TOP - 0.4, z - 1.0], [1.2, 1.0, 1.2], "#9a968a", collide=False)


def _flukes(isle: Isle) -> None:
    """The flukes on the south strand: two great blades of bone spreading
    from the tail's last vertebra, low walls to hide behind."""
    b = isle.b
    z = 86.0
    b.box([0.0, 1.5, z - 1.0], [6.0, 3.0, 6.0], BONE_SHADE)
    for sgn in (-1.0, 1.0):
        for k in range(5):
            x = sgn * (6.0 + k * 6.0)
            hgt = 3.4 - k * 0.45
            b.box([x, hgt / 2.0, z + k * 1.2], [6.2, hgt, 5.0 - k * 0.6], BONE if k % 2 else BONE_SHADE)
        b.box([sgn * 34.0, 0.7, z + 7.6], [4.0, 1.4, 3.0], BONE_DARK)
        isle.campfire(sgn * 46.0, 96.0)
    isle.dig(-18.0, None, 96.0, "the flukes")
    isle.dig(18.0, None, 96.0, "the flukes")
    isle.loot(0.0, None, 94.0, "any", "the flukes")


# ================================================================ the wings
def _half(isle: Isle, sgn: float) -> None:
    """One crew's wing of the atoll (mirrored for the other): the jawbone
    arches over the paths up from the pier, the try-works with its smoking
    pots, the scrimshaw carver's hut, the tide pools, palms and coral."""
    b = isle.b
    rng = isle.rng
    west = sgn < 0

    def X(x: float) -> float:
        return sgn * x

    # ---- the jawbone arches over the paths from the pier
    for z in (-15.0, 15.0):
        ax = X(100.0)
        for e in (-1.0, 1.0):
            b.box([ax, 2.0, z + e * 4.6], [2.0, 4.0, 1.6], BONE_SHADE)
            for k in range(8):
                t = (k + 0.5) / 8.0
                y = 4.0 + math.sin(t * math.pi / 2.0) * 9.0
                zz = z + e * 4.6 * (1.0 - t)
                b.box([ax, y, zz], [1.4, 1.8, 1.4], BONE if k % 2 else BONE_SHADE, collide=False,
                      r=[e * (0.9 - t * 0.9), 0.0, 0.0])
        b.box([ax, 13.2, z], [1.8, 1.4, 1.8], BONE_DARK, collide=False, r=[0.0, 0.4, 0.0])
    # ---- the try-works: a brick furnace with two great iron pots
    cx0, cx1 = sorted((X(CAMP[0]), X(CAMP[1])))
    cz0, cz1 = CAMP[2], CAMP[3]
    b.box([(cx0 + cx1) / 2.0, 1.8, (cz0 + cz1) / 2.0], [cx1 - cx0, 3.6, cz1 - cz0], "#a8503a")
    b.box([(cx0 + cx1) / 2.0, 3.75, (cz0 + cz1) / 2.0], [cx1 - cx0 - 1.0, 0.3, cz1 - cz0 - 1.0], "#8a4030")
    for k in range(2):
        px = cx0 + 4.5 + k * 9.0
        b.cyl([px, 4.7, (cz0 + cz1) / 2.0], [6.4, 1.6, 6.4], IRON, material="metal")
        b.cyl([px, 5.55, (cz0 + cz1) / 2.0], [5.4, 0.1, 5.4], "#c8a050", collide=False)
        b.box([px, 1.2, cz1 + 0.05], [2.4, 1.6, 0.1], "#ff7a2a", material="neon", collide=False)
    chim = cx0 + 1.4 if west else cx1 - 1.4
    b.box([chim, 6.0, cz0 + 1.6], [1.8, 12.0, 1.8], "#8a4030")
    b.rig("rr_smoke", chim, 12.4, cz0 + 1.6, wind=[0.6, 0.4], rate=0.22, h=20.0, size=1.8, colour="#6a6460")
    for k in range(3):
        isle.barrel(X(70.0 - k * 3.4), -50.0)
    isle.crates(X(102.0), -60.0, n=3)
    isle.loot((cx0 + cx1) / 2.0, None, cz0 - 4.0, "bar", "the try-works")
    # ---- the scrimshaw hut: driftwood walls, a bench of carved teeth
    hx0, hx1 = sorted((X(HUT[0]), X(HUT[1])))
    door = isle.hut(rect(hx0, hx1, HUT[2], HUT[3]), "z-", colour="#c8a880", roof="#e8705a")
    b.box([door[0], 7.5, HUT[2] - 0.15], [4.6, 1.0, 0.3], TIMBER, collide=False)
    for e in (-1.0, 1.0):
        b.cone([door[0] + e * 4.4, 3.0, HUT[2] - 1.2], [1.4, 6.0, 1.4], BONE)
    mx, mz = (hx0 + hx1) / 2.0, (HUT[2] + HUT[3]) / 2.0
    b.box([mx, 1.0, mz + 3.0], [6.0, 1.2, 2.4], PLANK)
    b.cyl([mx, 1.9, mz + 3.0], [0.6, 4.0, 0.6], BONE, collide=False, r=[math.pi / 2.0, 0.6, 0.0])
    isle.loot(mx, 0.4, mz - 1.0, "gem", "the scrimshaw hut")
    # ---- harpoons racked by the path, a beached whaleboat
    for k in range(4):
        b.cyl([X(106.0), 3.2, 28.0 + k * 1.6], [0.3, 6.4, 0.3], TIMBER)
        b.cone([X(106.0), 6.9, 28.0 + k * 1.6], [0.6, 1.0, 0.6], IRON, material="metal", collide=False)
    bx, bz = X(50.0), 84.0
    by = isle.top(bx, bz)
    b.box([bx, by + 0.8, bz], [4.0, 1.6, 12.0], "#e8e0d0")
    b.box([bx, by + 1.65, bz], [4.2, 0.1, 12.2], "#c84a3a", collide=False)
    for k in range(3):
        b.box([bx, by + 1.85, bz - 3.0 + k * 3.0], [3.2, 0.3, 0.5], PLANK)
    b.cyl([bx + sgn * 1.4, by + 1.9, bz + 1.0], [0.3, 7.0, 0.3], TIMBER, collide=False,
          r=[math.pi / 2.0, 0.2, 0.0])
    isle.loot(bx, None, bz - 8.0, "any", "the whaleboat")
    # ---- tide pools: coral heads and starfish in the shallow basins
    for x, z, r in POOLS:
        for k in range(3):
            a = k * 2.1 + (0.4 if west else 0.0)
            b.sphere([X(x) + math.cos(a) * r * 0.55, -0.9, z + math.sin(a) * r * 0.55], [2.0, 1.6, 2.0],
                     CORAL[(k + int(x)) % len(CORAL)])
        b.box([X(x) + 1.2, -1.35, z - 1.4], [1.2, 0.1, 1.2], "#ff6a4a", collide=False, r=[0.0, 0.6, 0.0])
        isle.loot(X(x), -1.4, z, "gem", "the tide pools")
    # ---- coral heads in the lagoon's shallows and on its floor
    for x, z, y in ((60.0, -30.0, RINGS[1]), (58.0, 12.0, RINGS[1]), (40.0, 40.0, RINGS[1]),
                    (30.0, -52.0, RINGS[1]), (30.0, -12.0, BED), (20.0, 28.0, BED), (46.0, 2.0, BED),
                    (14.0, -40.0, BED)):
        b.sphere([X(x), y + 1.0, z], [3.0, 2.4, 3.0], CORAL[int(abs(x + z)) % len(CORAL)])
        b.sphere([X(x) + 1.6, y + 0.6, z - 1.2], [1.6, 1.4, 1.6], CORAL[int(abs(x - z)) % len(CORAL)])
    isle.loot(X(18.0), BED, 8.0, "gem", "the lagoon floor")
    isle.loot(X(48.0), BED, -24.0, "bar", "the lagoon floor")
    # ---- palms, bushes, driftwood, rocks
    for x, z in ((106.0, -50.0), (108.0, 34.0), (92.0, -24.0), (80.0, 22.0), (40.0, 62.0),
                 (56.0, 70.0), (34.0, 88.0), (96.0, 56.0), (70.0, -74.0), (64.0, -84.0), (95.0, 0.0),
                 (98.0, 86.0), (86.0, -30.0), (100.0, 22.0)):
        px, pz = X(x + rng.uniform(-1.0, 1.0)), z + rng.uniform(-1.0, 1.0)
        if isle.clear(px, pz, 2.0):
            isle.palm(px, pz, h=rng.uniform(12.0, 18.0))
    for x, z in ((70.0, -36.0), (60.0, -76.0), (46.0, 76.0), (104.0, -34.0)):
        if isle.clear(X(x), z, 3.0):
            isle.bush(X(x), z, size=3.0, colour="#4a9a4a")
    for x, z, w in ((82.0, 88.0, 4.0), (108.0, 52.0, 3.2), (56.0, -70.0, 3.6)):
        if isle.clear(X(x), z, 3.0):
            isle.rock(X(x), z, w, w * 0.8, w * 0.6, colour=ROCK_LIGHT, cap=ROCK)
    for x, z in ((88.0, 50.0), (62.0, 56.0)):
        b.box([X(x), isle.top(X(x), z) + 0.4, z], [6.0, 0.8, 0.9], "#b8a888", r=[0.0, 0.4 * sgn, 0.0])
    isle.flag(X(106.0), 0.0, None, "#c8302a" if west else "#2a6ab8", h=11.0)
    # ---- X's and loot
    isle.dig(X(96.0), None, -30.0, "the palm grove")
    isle.dig(X(64.0), None, 64.0, "the south grove")
    isle.dig(X(86.0), None, 50.0, "behind the hut")
    isle.dig(X(44.0), None, -72.0, "under the skull")
    isle.dig(X(95.0), None, 4.0, "the dune")
    isle.loot(X(104.0), None, -40.0, "any", "the beach")
    isle.loot(X(90.0), None, 20.0, "any", "the palm grove")
    isle.loot(X(30.0), None, 70.0, "any", "the south strand")
    isle.loot(X(41.0), None, -86.0, "any", "the north dune")


def _rims(isle: Isle) -> None:
    """The lagoon's beaches, all the way round: where the maelstrom throws
    up what the deep has kept."""
    b = isle.b
    x0, x1, z0, z1 = LAGOON
    for x, z in ((x0 - 4.0, -40.0), (x0 - 4.0, -10.0), (x0 - 4.0, 20.0), (x1 + 4.0, -40.0), (x1 + 4.0, -10.0),
                 (x1 + 4.0, 20.0), (-40.0, z0 - 4.0), (40.0, z0 - 4.0), (-24.0, z1 + 4.0), (24.0, z1 + 4.0),
                 (-50.0, z1 + 4.0), (50.0, z1 + 4.0)):
        b.mark("rim", x, isle.top(x, z), z)


# ================================================================ meta
def _meta(isle: Isle) -> None:
    b = isle.b
    for x, z, name in ((0.0, -90.0, "the skull"), (0.0, -6.0, "the spine"), (0.0, 88.0, "the flukes"),
                       (-40.0, -10.0, "the west lagoon"), (40.0, -10.0, "the east lagoon"),
                       (-89.0, -49.0, "the west try-works"), (89.0, -49.0, "the east try-works"),
                       (-90.0, 37.0, "the west scrimshaw hut"), (90.0, 37.0, "the east scrimshaw hut"),
                       (-95.0, 0.0, "the west dune"), (95.0, 0.0, "the east dune"),
                       (-SHIP_X, 0.0, "the Scarlet Queen"), (SHIP_X, 0.0, "the Blue Marlin")):
        b.landmark(x, z, name)
    b.camera(0.0, 70.0, 118.0, 0.0, 4.0, -10.0)
    b.camera(-120.0, 44.0, 70.0, -20.0, 6.0, -10.0)
    b.camera(60.0, 30.0, -40.0, 0.0, 10.0, -90.0)
    b.camera(-56.0, 16.0, 56.0, 0.0, 10.0, -20.0)
    b.extra.update({"twist": "maelstrom", "water": SEA_TOP, "maelstrom_every": [52.0, 70.0],
                    "maelstrom_for": 26.0, "warn": 6.0, "vortex": [VORTEX[0], BED, VORTEX[1]],
                    "vortex_r": 26.0})
    # the life of the place: whales far out, dolphins, gulls, parrots, crabs,
    # the sun glittering on the lagoon, the surf
    b.rig("pb_whale", 330.0, SEA_TOP, -40.0, r=70.0, seed=1.0)
    b.rig("pb_whale", -360.0, SEA_TOP, 80.0, r=60.0, seed=6.0, s=0.8)
    b.rig("pb_dolphins", 0.0, SEA_TOP, 190.0, r=60.0, n=5, seed=2.0)
    for k, (x, z) in enumerate(((-60.0, -70.0), (60.0, -70.0), (0.0, 60.0), (-120.0, 0.0), (120.0, 0.0))):
        b.rig("rr_gulls", x, 26.0 + (k % 3) * 4.0, z, r=22.0 + k * 3.0, n=4 + k % 2, seed=k)
    for sgn in (-1.0, 1.0):
        b.rig("pb_parrots", sgn * 94.0, 22.0, -6.0, r=16.0, n=4, seed=sgn * 2.0)
        b.rig("pb_crabs", sgn * 109.0, 0.1, -70.0, q=[sgn * 109.0, 0.1, -30.0], n=3, seed=sgn * 3.0)
        b.rig("pb_crabs", sgn * 20.0, 0.1, 98.0, q=[sgn * 60.0, 0.1, 98.0], n=3, seed=sgn * 5.0)
        b.rig("pb_glow", sgn * 34.0, SEA_TOP + 0.05, -6.0, n=36, w=50.0, d=90.0, seed=sgn * 7.0,
              colours=["#ffffff", "#e8fcff", "#c8f8ff"])
    b.rig("rr_surf", 0.0, SEA_TOP + 0.3, SOUTH + 6.5, w=2 * SHORE_X - 10.0, yaw=0.0)
    for sgn in (-1.0, 1.0):
        b.rig("rr_surf", sgn * (SHORE_X + 6.5), SEA_TOP + 0.3, -50.0, w=70.0, yaw=sgn * math.pi / 2.0)
        b.rig("rr_surf", sgn * (SHORE_X + 6.5), SEA_TOP + 0.3, 70.0, w=50.0, yaw=sgn * math.pi / 2.0)


def build(b: ArenaArea) -> None:
    rng = random.Random(0xB0E5)
    isle = Isle(b, rng)
    _land(isle)
    _edges(isle)
    _skull(isle)
    _mandible(isle)
    _spine(isle)
    _ribs(isle)
    _flukes(isle)
    _half(isle, -1.0)
    _half(isle, 1.0)
    _rims(isle)
    galleon(isle, "red", 0.0)
    galleon(isle, "blue", 0.0)
    _meta(isle)
