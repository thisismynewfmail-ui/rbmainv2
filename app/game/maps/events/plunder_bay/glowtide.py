"""Glowtide Lagoon: an island at the blue hour, the sky going violet over a
lagoon whose water lights up blue wherever it is stirred -- and in the
middle of the lagoon the moon temple, stepped like a wedding cake, the
idol on its crown, stone causeways out to it from three shores.  North,
a mangrove swamp with a boardwalk winding through it to a moon shrine;
on either wing the pearl divers' village on stilts in a tidal bay; on the
south strand their lantern festival, sky lanterns going up off the fire.

Layout (north is -z; the Scarlet Corsairs' ship off the west shore, the
Azure Buccaneers' off the east)::

    z -120  ============== the mangrove fringe, the cliffs ==============
    z  -84   mangroves  ( THE SWAMP: boardwalk, the moon shrine )  mangroves
    z  -58              ------------- the dike ---------------
   SCARLET   stilt village   ~~ causeway ~~ THE MOON TEMPLE ~~ causeway ~~   stilt village  BLUE
    QUEEN    in its bay      ~~~~~~~~~~~ THE LAGOON (it glows) ~~~~~~~~~~~   in its bay     MARLIN
    z   44                    -------------- causeway --------------
    z   76   palms, stalls          the festival fire, sky lanterns       stalls, palms
    z  100  ~~~~~~~~~~~~~~~~~~~~~~~~~ the south sea ~~~~~~~~~~~~~~~~~~~~~~~~~

The halves are mirror images.

The twist is the tide (``extra["twist"] = "tide"``): the sea falls from
high water to low and back in steps (switchable water sheets in the
``tide`` group, ``extra["levels"]``).  At high water the causeways are
knee-deep and the bays and the swamp are flooded; as it goes out the
causeways come dry, the bays and the swamp drain to mud, and the giant
clams on the lagoon floor give up their pearls (``sunken`` marks) -- for
as long as the tide stays out.
"""
from __future__ import annotations

import math
import random

from ..calamity_coast.town import skirt
from ..kit import ArenaArea, backdrop, building, flight, gable, rect, slab
from .common import PLANK, SEABED, SHIP_X, SHORE_X, THATCH, TIMBER, Isle, galleon

HALF = (170.0, 120.0)
SKY = {"top": "#121848", "horizon": "#e08a8a", "sun": [0.2, 0.42, 0.72], "clouds": 0.5, "tint": "#c8c0f0"}
AMBIENT = "#9098c8"
GROUND = "#4a7a5a"
FOG = 720.0

HIGH, MID, LOW, BED = -1.0, -3.0, -5.0, -6.0
TURF = "#4a7a5a"
SAND_D = "#d8c8a8"           # sand at dusk
SAND_W = "#b8a888"
MUD = "#5a5040"
STONE = "#8a9ab4"            # the moon temple's blue-grey stone
STONE_DARK = "#6a7894"
MOON = "#7ad8ff"
PEARL = "#f4f8ff"
LANTERN = "#ffb05a"
MANGROVE = "#2e5a3e"
ROOT = "#5a4a3a"
SEA_C = "#1a3a7a"
LAGOON_C = "#0e4a8a"
SOUTH = 100.0
NORTH = -100.0
LAGOON = (-56.0, 56.0, -56.0, 44.0)
RINGS = (-1.2, -2.4, -3.6, -4.8)
RING_W = 3.0
BEACH = (-1.2, -2.4, -3.6, -4.8)
BEACH_W = 3.0
CZ = -6.0                    # the temple's centre (z; x is 0)
TIERS = ((20.0, -4.0), (16.0, -2.0), (12.5, 1.0), (9.0, 4.0), (6.0, 7.0))
CAUSE_Y = -2.6               # the causeways' tops: knee-deep at high water
CAUSE_W = 3.0
SWAMP = (-60.0, 60.0, -100.0, -60.0)
WET_FLOOR = -2.4             # the swamp's and the bays' mud
BAY = (64.0, 100.0, -44.0, 4.0)
STILTS = ((70.0, 80.0, -38.0, -28.0, "z+"), (84.0, 94.0, -38.0, -28.0, "z+"), (76.0, 88.0, -8.0, 2.0, "z-"))
HUT_Y = 1.6
DECK_Y = 1.6                 # the bays' boardwalks
SWAMP_DECK = 1.0             # the swamp's boardwalk
SHRINE = (0.0, -84.0)
SUNKEN = ((-32.0, -32.0), (32.0, -32.0), (-34.0, 18.0), (34.0, 18.0), (0.0, -38.0), (-16.0, 28.0), (16.0, 28.0))
CORAL = ("#ff6a9a", "#ff9a5a", "#c86aff", "#ffd04a", "#5af0c8")


def _m(r):
    x0, x1, z0, z1 = r
    return (-x1, -x0, z0, z1)


def _rings(b: ArenaArea, area, tops, width: float, floor: float, colours) -> None:
    """Banks stepping down inside a hole, one strip per step all the way
    round, never overlapping."""
    x0, x1, z0, z1 = area
    for k, top in enumerate(tops):
        a, c = k * width, (k + 1) * width
        colour = colours[k % len(colours)]
        for xa, xb in ((x0 + a, x0 + c), (x1 - c, x1 - a)):
            b.box([(xa + xb) / 2.0, (floor + top) / 2.0, (z0 + z1) / 2.0],
                  [xb - xa, top - floor, (z1 - a) - (z0 + a)], colour, studs=True)
        for za, zb in ((z0 + a, z0 + c), (z1 - c, z1 - a)):
            b.box([(x0 + x1) / 2.0, (floor + top) / 2.0, (za + zb) / 2.0], [(x1 - c) - (x0 + c), top - floor, zb - za],
                  colour, studs=True)


# ================================================================ the land
def _land(isle: Isle) -> None:
    b = isle.b
    hx, hz = HALF
    m = b.margin
    west = (-hx - m, -SHORE_X, -hz - m, hz + m)
    east = (SHORE_X, hx + m, -hz - m, hz + m)
    south = (-SHORE_X, SHORE_X, SOUTH, hz + m)
    bays = [BAY, _m(BAY)]
    isle.land(TURF, holes=[west, east, south, LAGOON, SWAMP] + bays, soil="#4a3e34")
    for area in (west, east, south, LAGOON):
        slab(b, area, BED, 3.0, SAND_W, studs=True)
    for area in [SWAMP] + bays:
        slab(b, area, WET_FLOOR, 3.0, MUD, studs=True)
    # the beaches, stepping down into the sea
    for k, top in enumerate(BEACH):
        colour = SAND_D if k < 2 else SAND_W
        for sgn in (-1.0, 1.0):
            xa, xb = sorted((sgn * (SHORE_X + BEACH_W * k), sgn * (SHORE_X + BEACH_W * (k + 1))))
            b.box([(xa + xb) / 2.0, (BED + top) / 2.0, (NORTH + hz) / 2.0],
                  [xb - xa, top - BED, hz - NORTH], colour, studs=True)
        za, zb = SOUTH + BEACH_W * k, SOUTH + BEACH_W * (k + 1)
        b.box([0.0, (BED + top) / 2.0, (za + zb) / 2.0], [2 * SHORE_X, top - BED, zb - za], colour, studs=True)
    _rings(b, LAGOON, RINGS, RING_W, BED, (SAND_D, SAND_D, SAND_W, SAND_W))
    for area in [SWAMP] + bays:
        _rings(b, area, (-1.2,), 3.0, WET_FLOOR, ("#6a6048",))
    # the ground covers: kept off what stands on the turf
    s = isle.s
    keep = [(-3.0, 3.0, 76.0, 84.0)]
    for r in ((22.0, 38.0, 62.0, 72.0),):
        keep += [r, _m(r)]
    for r in keep:
        s.reserve(r)
    for sgn in (-1.0, 1.0):
        def X(x: float, sgn: float = sgn) -> float:
            return sgn * x
        isle.trail([(X(109.5), -15.0), (X(102.5), -15.0)], colour="#c8b898")
        isle.trail([(X(61.5), -15.0), (X(61.5), -6.0), (X(58.5), -6.0)], colour="#c8b898")
        isle.trail([(X(109.5), 15.0), (X(60.0), 15.0), (X(60.0), 52.0), (X(6.0), 52.0)], colour="#c8b898")
        isle.trail([(X(82.0), -46.5), (X(82.0), -68.0), (X(62.5), -68.0)], colour="#c8b898")
    isle.trail([(0.0, 52.0), (0.0, 46.5)], colour="#c8b898")
    for x0, x1, z0, z1 in ((-SHORE_X, -102.0, NORTH, SOUTH), (102.0, SHORE_X, NORTH, SOUTH),
                           (-102.0, 102.0, 88.0, SOUTH), (-56.0, 56.0, 44.0, 50.0)):
        s.lay(rect(x0, x1, z0, z1), 0.1, SAND_D)
    for r in ((66.0, 108.0, -98.0, -50.0), (64.0, 100.0, 22.0, 46.0)):
        for rr in (r, _m(r)):
            s.lay(rect(*rr), 0.08, "#3e6a4a")


def _water(isle: Isle) -> None:
    """The sea at three heights, switched by the tide (high water on): the
    open sea and the lagoon at every height, the swamp and the bays only
    while the water is over their mud."""
    b = isle.b
    hx, hz = HALF
    m = b.margin
    seas = [(-hx, -SHORE_X, NORTH, hz), (SHORE_X, hx, NORTH, hz), (-SHORE_X, SHORE_X, SOUTH, hz)]
    for key, level in (("tide_hi", HIGH), ("tide_mid", MID), ("tide_lo", LOW)):
        with b.detached() as parts:
            for area in seas:
                isle.water(area, BED, level, colour=SEA_C, alpha=0.6)
            isle.water(LAGOON, BED, level, colour=LAGOON_C, alpha=0.62)
            if level > WET_FLOOR:
                for area in (SWAMP, BAY, _m(BAY)):
                    isle.water(area, WET_FLOOR, level, colour="#2a5a6a", alpha=0.55)
        b.dynamic(key, parts, on=(key == "tide_hi"), group="tide")
    for x0, x1, z0, z1 in ((-hx - m - 300.0, -hx - m, -hz - m - 300.0, hz + m + 300.0),
                           (hx + m, hx + m + 300.0, -hz - m - 300.0, hz + m + 300.0),
                           (-hx - m, hx + m, hz + m, hz + m + 300.0)):
        b.box([(x0 + x1) / 2.0, (BED - 2.0 + HIGH) / 2.0, (z0 + z1) / 2.0],
              [x1 - x0, HIGH - BED + 2.0, z1 - z0], "#16306a", material="glass", alpha=0.62, collide=False)


# =============================================================== the edges
def _edges(isle: Isle) -> None:
    b = isle.b
    hx, hz = HALF
    rng = isle.rng
    m = b.margin
    rocks = ("#5a6070", "#4a5060", "#6a7080", "#545a6a")
    isle.cliffs("x", -SHORE_X, SHORE_X, -hz - m, NORTH, rng.uniform(20.0, 24.0), rocks, green=MANGROVE, step=14.0,
                recess=0.0)
    for sgn in (-1.0, 1.0):
        a0, a1 = sorted((sgn * SHORE_X, sgn * (hx + m)))
        isle.cliffs("x", a0, a1, -hz - m, NORTH, 30.0, rocks, base=BED, green=MANGROVE, step=14.5, recess=0.0,
                    vines=False)
        b.box([sgn * (hx + m / 2.0), (BED + 6.0) / 2.0, (NORTH + hz + m) / 2.0],
              [m, 6.0 - BED, hz + m - NORTH], "#4a5060")
    b.box([0.0, (BED + 6.0) / 2.0, hz + m / 2.0], [2 * hx, 6.0 - BED, m], "#4a5060")
    for k in range(18):
        z = NORTH + (k + 0.5) * (hz + m - NORTH) / 18.0
        for sgn in (-1.0, 1.0):
            b.box([sgn * (hx + m / 2.0) + rng.uniform(-1.0, 1.0), 6.0 + 1.0 + (k % 3) * 0.4, z],
                  [m - 2.0 - (k % 2) * 0.6, 2.0 + (k % 3) * 0.8, (hz + m - NORTH) / 18.0 - 2.0],
                  CORAL[k % len(CORAL)] if k % 4 == 0 else "#5a6070")
    for k in range(18):
        x = -hx + (k + 0.5) * 2 * hx / 18.0
        b.box([x, 6.0 + 1.0 + (k % 3) * 0.4, hz + m / 2.0 + rng.uniform(-1.0, 1.0)],
              [2 * hx / 18.0 - 2.0, 2.0 + (k % 3) * 0.8, m - 2.0 - (k % 2) * 0.6],
              CORAL[(k + 2) % len(CORAL)] if k % 4 == 1 else "#5a6070")
    skirt(b, hx, hz, "#3a3a44", top=BED - 3.05)
    backdrop(b, "hills", 10.0, rng, sides=("z-",), colours=["#24304a", "#2c3a52", "#1e2a40"], depth=160.0)


def _galleon_feet(isle: Isle) -> None:
    """The galleons and their piers stand on a seabed lower than most (the
    tide needs the room): their hulls and posts carried down to it, so
    nothing hangs in the air when the sea goes out."""
    b = isle.b
    for side in (-1.0, 1.0):
        sx = side * SHIP_X
        inward = -side

        def X(u: float) -> float:
            return sx + inward * u

        for u0, u1, v0, v1 in ((-8.0, 8.0, -28.0, 26.0), (-5.0, 5.0, 26.0, 32.0)):
            xa, xb = sorted((X(u0), X(u1)))
            b.box([(xa + xb) / 2.0, (BED + SEABED) / 2.0, (v0 + v1) / 2.0], [xb - xa, SEABED - BED, v1 - v0],
                  "#3e2816")
        for u in (8.8, 13.2):
            for v in (-17.0, -9.0, 0.0, 9.0, 17.0):
                b.cyl([X(u), (BED + SEABED) / 2.0, v], [1.0, SEABED - BED, 1.0], TIMBER)
        for u in (20.0, 27.0):
            for v in (-17.2, -12.8, 12.8, 17.2):
                b.cyl([X(u), (BED + SEABED) / 2.0, v], [1.0, SEABED - BED, 1.0], TIMBER)


# ========================================================== the moon temple
def _temple(isle: Isle) -> None:
    """The moon temple: five tiers of blue-grey stone stacked in the
    lagoon, the lowest two drowned at high water; stairs up every face of
    the upper tiers (up the north face from the lagoon floor too); crescent
    moons carved and glowing; four obelisks with moonstones; the idol on
    the crown."""
    b = isle.b
    prev = BED
    for k, (h, top) in enumerate(TIERS):
        b.box([0.0, (prev + top) / 2.0, CZ], [2 * h, top - prev, 2 * h], (STONE, STONE_DARK)[k % 2])
        prev = top
    # the stairs: tier to tier up every face from the second up; up the
    # north face from the floor and the first tier
    for k in range(len(TIERS) - 1):
        h0, y0 = TIERS[k]
        h1, y1 = TIERS[k + 1]
        faces = ("n", "s", "e", "w") if k >= 1 else ("n",)
        for face in faces:
            if face in ("n", "s"):
                sgn = -1.0 if face == "n" else 1.0
                flight(b, "z", CZ + sgn * h0, CZ + sgn * h1, -2.5, 2.5, y0, y1, STONE_DARK, fill=y0, rise=1.0)
            else:
                sgn = 1.0 if face == "e" else -1.0
                flight(b, "x", sgn * h0, sgn * h1, CZ - 2.5, CZ + 2.5, y0, y1, STONE_DARK, fill=y0, rise=1.0)
    h0, y0 = TIERS[0]
    flight(b, "z", CZ - h0 - 4.0, CZ - h0, -2.5, 2.5, BED, y0, STONE_DARK, fill=BED, rise=1.0)
    # crescent moons carved in the third tier's faces, glowing; a band of
    # runes round the fourth
    h2, y2 = TIERS[2]
    y1 = TIERS[1][1]
    for sgn in (-1.0, 1.0):
        for dx in (-7.0, 7.0):
            b.add("crescent", [dx, (y1 + y2) / 2.0, CZ + sgn * (h2 + 0.08)], [2.2, 2.4, 0.16], MOON,
                  material="neon", collide=False, r=[0.0, 0.0 if sgn > 0 else math.pi, 0.0])
            b.add("crescent", [sgn * (h2 + 0.08), (y1 + y2) / 2.0, CZ + dx], [2.2, 2.4, 0.16], MOON,
                  material="neon", collide=False, r=[0.0, sgn * math.pi / 2.0, 0.0])
    h3, y3 = TIERS[3]
    for sgn in (-1.0, 1.0):
        for a, c in ((-h3, -2.8), (2.8, h3)):
            b.box([(a + c) / 2.0, y3 - 0.5, CZ + sgn * (h3 + 0.05)], [c - a, 0.3, 0.1], MOON, material="neon",
                  collide=False)
            b.box([sgn * (h3 + 0.05), y3 - 0.5, CZ + (a + c) / 2.0], [0.1, 0.3, c - a], MOON, material="neon",
                  collide=False)
    # the obelisks at the third tier's corners, moonstones on top
    for sx in (-1.0, 1.0):
        for sz in (-1.0, 1.0):
            x, z = sx * (h2 - 1.6), CZ + sz * (h2 - 1.6)
            b.box([x, y2 + 3.0, z], [1.4, 6.0, 1.4], STONE)
            b.box([x, y2 + 6.3, z], [1.0, 0.6, 1.0], STONE_DARK)
            b.sphere([x, y2 + 7.2, z], [1.2, 1.2, 1.2], PEARL, material="neon")
    # the idol on the crown, glowing pools of light round it
    h4, y4 = TIERS[4]
    isle.idol(0.0, y4, CZ, colour=STONE_DARK)
    # (beside the stairs, never on them)
    isle.loot(5.5, y2, CZ - h2 + 1.5, "gem", "the moon temple")
    isle.loot(-h2 + 1.6, y2, CZ + 5.0, "bar", "the moon temple")
    isle.loot(h2 - 1.6, y2, CZ + 5.0, "bar", "the moon temple")
    isle.loot(6.0, y1, CZ + TIERS[1][0] - 1.5, "any", "the temple's steps")
    b.landmark(0.0, CZ, "the moon temple")


def _causeways(isle: Isle) -> None:
    """Stone causeways to the temple from the west, east and south shores:
    knee-deep at high water, dry once the tide is out; posts along them,
    moon-lamps on the posts."""
    b = isle.b
    h1 = TIERS[1][0]
    for sgn in (-1.0, 1.0):
        xa, xb = sorted((sgn * h1, sgn * 50.0))
        b.box([(xa + xb) / 2.0, (BED + CAUSE_Y) / 2.0, CZ], [xb - xa, CAUSE_Y - BED, 2 * CAUSE_W], STONE)
        flight(b, "x", sgn * 50.0, sgn * LAGOON[1], CZ - CAUSE_W, CZ + CAUSE_W, CAUSE_Y, 0.0, STONE, fill=BED,
               rise=1.0)
        for x in (24.0, 34.0, 44.0):
            for dz in (-CAUSE_W + 0.4, CAUSE_W - 0.4):
                b.box([sgn * x, CAUSE_Y + 1.0, CZ + dz], [0.8, 2.0, 0.8], STONE_DARK)
                b.box([sgn * x, CAUSE_Y + 2.3, CZ + dz], [0.7, 0.6, 0.7], MOON, material="neon")
        isle.loot(sgn * 30.0, CAUSE_Y, CZ, "any", "the causeway")
    za, zb = CZ + h1, 38.0
    b.box([0.0, (BED + CAUSE_Y) / 2.0, (za + zb) / 2.0], [2 * CAUSE_W, CAUSE_Y - BED, zb - za], STONE)
    flight(b, "z", 38.0, LAGOON[3], -CAUSE_W, CAUSE_W, CAUSE_Y, 0.0, STONE, fill=BED, rise=1.0)
    for z in (18.0, 28.0):
        for dx in (-CAUSE_W + 0.4, CAUSE_W - 0.4):
            b.box([dx, CAUSE_Y + 1.0, z], [0.8, 2.0, 0.8], STONE_DARK)
            b.box([dx, CAUSE_Y + 2.3, z], [0.7, 0.6, 0.7], MOON, material="neon")
    isle.loot(0.0, CAUSE_Y, 24.0, "any", "the causeway")


def _lagoon_floor(isle: Isle) -> None:
    """The lagoon's floor: giant clams with pearls in them (what the low
    tide gives up), coral heads, anemones, a pearl diver's sunken boat."""
    b = isle.b
    for k, (x, z) in enumerate(SUNKEN):
        b.mark("sunken", x, BED, z)
        cx = x + (2.6 if x >= 0 else -2.6)
        b.sphere([cx, BED + 0.6, z], [3.6, 1.2, 2.8], "#b8a8c8")
        b.sphere([cx, BED + 1.6, z - 0.8], [3.4, 0.9, 2.6], "#c8b8d8", collide=False, r=[0.5, 0.0, 0.0])
        b.sphere([cx, BED + 1.25, z], [0.9, 0.9, 0.9], PEARL, material="neon", collide=False)
    for k, (x, z, y) in enumerate(((44.0, -40.0, BED), (40.0, 30.0, BED), (26.0, -46.0, RINGS[3]),
                                    (48.0, 6.0, RINGS[3]), (24.0, 26.0, BED), (38.0, -16.0, BED))):
        for sgn in (-1.0, 1.0):
            px = sgn * x
            b.sphere([px, y + 1.0, z], [3.0, 2.4, 3.0], CORAL[k % len(CORAL)])
            b.sphere([px + sgn * 1.4, y + 0.6, z - 1.2], [1.6, 1.4, 1.6], CORAL[(k + 2) % len(CORAL)])
            b.cyl([px, y + 2.4, z], [0.5, 0.6, 0.5], ("#ff8ad8", "#8affd8")[k % 2], material="neon", collide=False)
    # a pearl diver's boat, sunk on the floor west of the temple
    b.box([-30.0, BED + 0.6, 10.0], [3.0, 1.2, 8.0], "#5a3a22")
    b.box([-30.0, BED + 1.25, 10.0], [2.6, 0.1, 7.4], "#2a1a10", collide=False)
    b.landmark(0.0, 30.0, "the lagoon")


# ================================================================ the swamp
def _mangrove(isle: Isle, x: float, z: float, y: float, h: float) -> None:
    """A mangrove: its trunk up off a tangle of prop roots, a broad dark
    crown."""
    b = isle.b
    b.cyl([x, y + h / 2.0, z], [1.3, h, 1.3], ROOT)
    for k in range(5):
        a = k * 1.26 + x * 0.1
        b.cyl([x + math.cos(a) * 1.4, y + 1.2, z + math.sin(a) * 1.4], [0.4, 3.0, 0.4], ROOT, collide=False,
              r=[math.sin(a) * 0.6, 0.0, -math.cos(a) * 0.6])
    for k, (dx, dz, w) in enumerate(((0.0, 0.0, 9.0), (2.4, 1.6, 6.0), (-2.2, -1.4, 6.4))):
        b.sphere([x + dx, y + h + 0.8 + k * 0.4, z + dz], [w, 2.6, w * 0.9], (MANGROVE, "#386a48", "#2a5038")[k],
                 collide=False)


def _swamp(isle: Isle) -> None:
    """The mangrove swamp: flooded at high water, mud at low; a boardwalk
    winding through it on posts, out to the moon shrine on its islet."""
    b = isle.b
    x0, x1, z0, z1 = SWAMP
    # the boardwalk: along the swamp, a spur to the shrine, spurs to the dike
    legs = [(-60.0, 60.0, -70.0, -66.0), (-2.0, 2.0, -78.0, -70.0), (28.0, 32.0, -66.0, -60.0),
            (-32.0, -28.0, -66.0, -60.0)]
    for lx0, lx1, lz0, lz1 in legs:
        b.box([(lx0 + lx1) / 2.0, SWAMP_DECK - 0.2, (lz0 + lz1) / 2.0], [lx1 - lx0, 0.4, lz1 - lz0], PLANK)
        along_x = lx1 - lx0 > lz1 - lz0
        n = max(2, int((max(lx1 - lx0, lz1 - lz0)) // 7.0))
        for k in range(n + 1):
            f = k / float(n)
            if along_x:
                px = lx0 + 0.6 + f * (lx1 - lx0 - 1.2)
                pts = [(px, lz0 + 0.5), (px, lz1 - 0.5)]
            else:
                pz = lz0 + 0.6 + f * (lz1 - lz0 - 1.2)
                pts = [(lx0 + 0.5, pz), (lx1 - 0.5, pz)]
            for px, pz in pts:
                b.cyl([px, (WET_FLOOR + SWAMP_DECK - 0.4) / 2.0, pz], [0.6, SWAMP_DECK - 0.4 - WET_FLOOR, 0.6], TIMBER)
    for x in (-50.0, -26.0, -10.0, 10.0, 26.0, 50.0):
        b.cyl([x, SWAMP_DECK + 1.6, -66.4], [0.36, 3.2, 0.36], TIMBER)
        b.box([x, SWAMP_DECK + 3.5, -66.4], [0.9, 1.1, 0.9], LANTERN, material="neon")
    # the moon shrine on its islet
    sx, sz = SHRINE
    b.box([sx, (WET_FLOOR + SWAMP_DECK) / 2.0, sz], [14.0, SWAMP_DECK - WET_FLOOR, 12.0], STONE_DARK)
    b.box([sx, SWAMP_DECK + 0.1, sz], [12.0, 0.2, 10.0], STONE, collide=False)
    b.add("crescent", [sx, SWAMP_DECK + 0.2 + 4.2, sz - 3.0], [7.0, 8.4, 0.8], STONE, collide=False)
    b.add("crescent", [sx, SWAMP_DECK + 0.2 + 4.2, sz - 2.55], [6.2, 7.6, 0.1], MOON, material="neon",
          collide=False)
    b.box([sx, SWAMP_DECK + 0.7, sz + 0.5], [2.4, 1.4, 1.6], STONE)
    for dx in (-5.4, 5.4):
        for dz in (-4.4, 4.4):
            b.cyl([sx + dx, SWAMP_DECK + 1.2, sz + dz], [0.5, 2.4, 0.5], STONE)
            b.sphere([sx + dx, SWAMP_DECK + 2.7, sz + dz], [0.8, 0.8, 0.8], MOON, material="neon")
    isle.loot(sx, SWAMP_DECK + 0.2, sz + 3.0, "gem", "the moon shrine")
    # the mangroves, standing in the water
    for x, z in ((48.0, -88.0), (38.0, -78.0), (20.0, -90.0), (14.0, -76.0), (52.0, -76.0), (30.0, -94.0),
                 (44.0, -74.0), (8.0, -94.0), (24.0, -80.0)):
        for sgn in (-1.0, 1.0):
            _mangrove(isle, sgn * x, z, WET_FLOOR, 8.0 + (abs(x) % 5) * 0.6)
    isle.loot(-44.0, SWAMP_DECK, -68.0, "any", "the swamp boardwalk")
    isle.loot(44.0, SWAMP_DECK, -68.0, "any", "the swamp boardwalk")
    b.landmark(0.0, -84.0, "the moon shrine")
    b.landmark(0.0, -68.0, "the swamp")


# ================================================================ the wings
def _bay(isle: Isle, sgn: float) -> None:
    """The pearl divers' village: huts on stilts in a tidal bay, boardwalks
    between them, canoes tied up, lanterns lit -- flooded at high water,
    mud underneath when the tide goes out."""
    b = isle.b

    def X(x: float) -> float:
        return sgn * x

    for k, (hx0, hx1, hz0, hz1, door) in enumerate(STILTS):
        x0, x1 = sorted((X(hx0), X(hx1)))
        cxd = (x0 + x1) / 2.0
        building(b, rect(x0, x1, hz0, hz1), HUT_Y, 6.8, ("#a8845a", "#b8946a", "#987450")[k], t=0.6,
                 roof_colour=THATCH, roof_t=0.6, floor_colour=PLANK, doors={door: [(cxd - 1.6, cxd + 1.6, HUT_Y + 5.0)]},
                 lights=LANTERN, studs_roof=False)
        gable(b, rect(x0, x1, hz0, hz1), HUT_Y + 7.4, THATCH, "x", tiers=3, rise=1.0, overhang=0.6)
        for px in (x0 + 0.5, x1 - 0.5, cxd):
            for pz in (hz0 + 0.5, hz1 - 0.5):
                b.cyl([px, (WET_FLOOR + HUT_Y) / 2.0, pz], [0.7, HUT_Y - WET_FLOOR, 0.7], TIMBER)
        dz = hz1 + 0.3 if door == "z+" else hz0 - 0.3
        for e in (-1.0, 1.0):
            b.box([cxd + e * 2.6, HUT_Y + 4.2, dz], [0.6, 0.8, 0.6], LANTERN, material="neon", collide=False)
        isle.loot(cxd, HUT_Y + 0.4, (hz0 + hz1) / 2.0, "gem" if k == 2 else "any", "a stilt hut")
    # the boardwalks: across the bay, and out to each hut's door
    legs = [(64.0, 100.0, -17.0, -13.0), (73.0, 77.0, -28.0, -17.0), (87.0, 91.0, -28.0, -17.0),
            (80.0, 84.0, -13.0, -8.0)]
    for lx0, lx1, lz0, lz1 in legs:
        xa, xb = sorted((X(lx0), X(lx1)))
        b.box([(xa + xb) / 2.0, DECK_Y - 0.2, (lz0 + lz1) / 2.0], [xb - xa, 0.4, lz1 - lz0], PLANK)
        long_x = xb - xa > lz1 - lz0
        n = max(1, int(max(xb - xa, lz1 - lz0) // 7.0))
        for k in range(n + 1):
            f = k / float(n)
            if long_x:
                px = xa + 0.6 + f * (xb - xa - 1.2)
                pts = [(px, lz0 + 0.5), (px, lz1 - 0.5)]
            else:
                pz = lz0 + 0.6 + f * (lz1 - lz0 - 1.2)
                pts = [(xa + 0.5, pz), (xb - 0.5, pz)]
            for px, pz in pts:
                b.cyl([px, (WET_FLOOR + DECK_Y - 0.4) / 2.0, pz], [0.6, DECK_Y - 0.4 - WET_FLOOR, 0.6], TIMBER)
    for x in (68.0, 82.0, 96.0):
        b.cyl([X(x), DECK_Y + 1.6, -13.4], [0.36, 3.2, 0.36], TIMBER)
        b.box([X(x), DECK_Y + 3.5, -13.4], [0.9, 1.1, 0.9], LANTERN, material="neon")
    isle.loot(X(70.0), DECK_Y, -15.0, "any", "the long boardwalk")
    b.rig("pb_sampan", X(96.0), HIGH, -22.0, yaw=0.2 * sgn, tide=True, floor=WET_FLOOR, seed=sgn * 2.0,
          colour="#7a4a2a")
    b.rig("pb_sampan", X(68.0), HIGH, -6.0, yaw=-0.3 * sgn, tide=True, floor=WET_FLOOR, seed=sgn * 5.0,
          colour="#3a5a7a", roof="#d8a860")
    b.landmark(X(82.0), -20.0, "the %s stilt village" % ("west" if sgn < 0 else "east"))


def _half(isle: Isle, sgn: float) -> None:
    """One crew's wing (mirrored for the other): the stilt village in its
    bay, mangroves to the north, palms and the festival's stalls south."""
    b = isle.b
    rng = isle.rng
    west = sgn < 0

    def X(x: float) -> float:
        return sgn * x

    _bay(isle, sgn)
    # mangroves along the north of the wing
    for x, z in ((70.0, -90.0), (88.0, -94.0), (104.0, -84.0), (72.0, -56.0), (96.0, -60.0), (104.0, -50.0),
                 (92.0, -78.0), (68.0, -76.0)):
        if isle.clear(X(x), z, 3.0):
            _mangrove(isle, X(x), z, isle.top(X(x), z), 7.0 + (x % 4) * 0.5)
    # the festival's stall: a striped awning on posts, its table of pearls
    sx0, sx1 = sorted((X(22.0), X(38.0)))
    for px in (sx0 + 0.5, sx1 - 0.5):
        for pz in (62.5, 71.5):
            b.cyl([px, 2.4, pz], [0.5, 4.8, 0.5], TIMBER)
    for k in range(4):
        b.box([sx0 + (k + 0.5) * (sx1 - sx0) / 4.0, 5.05, 67.0], [(sx1 - sx0) / 4.0, 0.3, 10.0],
              ("#c8302a", "#f4ece0")[k % 2] if west else ("#2a6ab8", "#f4ece0")[k % 2])
    b.box([(sx0 + sx1) / 2.0, 1.0, 67.0], [sx1 - sx0 - 3.0, 2.0, 3.0], "#8a6a44")
    for k in range(8):
        b.sphere([sx0 + 2.4 + k * 1.4, 2.25, 67.0 + (k % 2) * 0.6 - 0.3], [0.6, 0.5, 0.6], PEARL, material="neon",
                 collide=False)
    isle.loot((sx0 + sx1) / 2.0, None, 74.5, "any", "the festival stalls")
    # lantern poles along the strand, canoes drawn up, palms
    for x, z in ((20.0, 56.0), (46.0, 56.0), (66.0, 70.0), (90.0, 66.0), (104.0, 40.0), (104.0, -32.0)):
        y = isle.top(X(x), z)
        b.cyl([X(x), y + 2.4, z], [0.4, 4.8, 0.4], TIMBER)
        b.box([X(x), y + 5.2, z], [1.0, 1.2, 1.0], ("#ff8a4a", "#ffd86a", "#ff6a8a")[int(x) % 3], material="neon")
    for k, (x, z) in enumerate(((84.0, 92.0), (94.0, 90.0))):
        y = isle.top(X(x), z)
        b.box([X(x), y + 0.6, z], [2.6, 1.2, 8.0], ("#3a5a7a", "#7a4a2a")[k])
        b.box([X(x), y + 1.25, z], [2.2, 0.1, 7.4], "#2a1a10", collide=False)
    for x, z in ((106.0, -60.0), (106.0, 60.0), (100.0, 80.0), (70.0, 90.0), (50.0, 82.0), (100.0, 26.0),
                 (74.0, 50.0), (88.0, 32.0)):
        px, pz = X(x + rng.uniform(-1.0, 1.0)), z + rng.uniform(-1.0, 1.0)
        if isle.clear(px, pz, 2.0):
            isle.palm(px, pz, h=rng.uniform(12.0, 16.0))
    for x, z in ((96.0, 72.0), (58.0, 90.0), (80.0, -84.0)):
        if isle.clear(X(x), z, 3.0):
            isle.bush(X(x), z, size=3.0, colour="#3e7a4a")
    isle.flag(X(108.0), 0.0, None, "#c8302a" if west else "#2a6ab8", h=11.0)
    # X's and loot about the wing
    isle.dig(X(90.0), None, 52.0, "the south palms")
    isle.dig(X(98.0), None, -70.0, "the mangroves")
    isle.dig(X(66.0), None, 30.0, "the strand")
    isle.dig(X(76.0), None, 80.0, "the festival")
    isle.dig(X(106.0), None, 8.0, "the beach")
    isle.loot(X(104.0), None, -40.0, "any", "the beach")
    isle.loot(X(84.0), None, 20.0, "any", "the palms")
    isle.loot(X(70.0), None, -60.0, "any", "the mangroves")
    isle.loot(X(42.0), None, 90.0, "any", "the south strand")


def _festival(isle: Isle) -> None:
    """The festival fire on the south strand, the sky lanterns going up off
    it."""
    b = isle.b
    x, z = 0.0, 80.0
    y = isle.top(x, z)
    for k in range(10):
        a = k * math.tau / 10.0
        b.box([x + math.cos(a) * 3.6, y + 0.5, z + math.sin(a) * 3.6], [1.4, 1.0, 1.4], "#6a6a74")
    for k in range(5):
        a = k * math.tau / 5.0
        b.box([x + math.cos(a) * 0.9, y + 1.6, z + math.sin(a) * 0.9], [0.5, 3.4, 0.5], TIMBER, collide=False,
              r=[math.sin(a) * 0.35, 0.0, -math.cos(a) * 0.35])
    b.cone([x, y + 1.8, z], [3.0, 3.6, 3.0], "#ff8a2a", material="neon", collide=False)
    b.cone([x, y + 1.4, z], [1.8, 2.4, 1.8], "#ffd04a", material="neon", collide=False)
    b.rig("rr_flame", x, y + 2.6, z, s=1.8)
    b.rig("rr_smoke", x, y + 5.0, z, wind=[0.5, 0.3], rate=0.25, h=24.0, size=2.2, colour="#6a5a6a")
    b.rig("pb_skylanterns", x, y + 4.0, z, n=14, h=150.0, r=8.0, life=28.0, seed=1.0)
    isle.dig(-12.0, None, 86.0, "by the festival fire")
    isle.dig(12.0, None, 86.0, "by the festival fire")
    isle.loot(0.0, None, 70.0, "gem", "the festival fire")
    b.landmark(x, z, "the festival fire")


# ================================================================ meta
def _meta(isle: Isle) -> None:
    b = isle.b
    for x, z, name in ((-SHIP_X, 0.0, "the Scarlet Queen"), (SHIP_X, 0.0, "the Blue Marlin")):
        b.landmark(x, z, name)
    b.camera(0.0, 46.0, 112.0, 0.0, 4.0, -10.0)
    b.camera(-110.0, 40.0, 50.0, -10.0, 2.0, -10.0)
    b.camera(44.0, 26.0, -44.0, 0.0, 4.0, -6.0)
    b.camera(-36.0, 18.0, 30.0, 0.0, 6.0, -6.0)
    b.extra.update({"twist": "tide", "water": HIGH, "levels": [HIGH, MID, LOW], "tide_every": [52.0, 70.0],
                    "tide_for": 28.0, "warn": 5.0,
                    "twist_text": {"warn": "THE GLOWTIDE IS EBBING",
                                   "warnSub": "The lagoon is draining off the moon temple...",
                                   "onSub": "Pearls in the clams on the lagoon floor -- grab them before the sea "
                                            "comes back"}})
    # the glow: sparkles where the water moves, lanterns floating on it,
    # jellies in the deep, light round anybody wading -- all riding the tide
    b.rig("pb_glow", 0.0, HIGH, -6.0, n=70, w=100.0, d=92.0, seed=3.0, tide=True,
          colours=["#5af0ff", "#7affd8", "#4ab8ff", "#b8fff0"])
    b.rig("pb_lanterns", 0.0, HIGH, 0.0, n=18, w=90.0, d=80.0, seed=2.0, tide=True)
    b.rig("pb_jellyfish", 30.0, BED + 0.6, -30.0, r=14.0, n=5, seed=1.0)
    b.rig("pb_jellyfish", -30.0, BED + 0.6, 22.0, r=14.0, n=5, seed=4.0)
    b.rig("pb_wake", 0.0, HIGH, 0.0, w=2 * HALF[0] + 40.0, d=2 * HALF[1] + 40.0)
    b.rig("pb_dolphins", 0.0, HIGH, 200.0, r=60.0, n=5, seed=2.0)
    for sgn in (-1.0, 1.0):
        b.rig("pb_glow", sgn * 130.0, HIGH, 0.0, n=30, w=30.0, d=200.0, seed=sgn * 5.0, tide=True,
              colours=["#5af0ff", "#4ab8ff", "#b8fff0"])
        b.rig("pb_wisps", sgn * 30.0, 2.0, -84.0, r=20.0, n=8, seed=sgn * 3.0, colour="#e8ff7a")
        b.rig("pb_wisps", sgn * 86.0, 3.0, -76.0, r=14.0, n=6, seed=sgn * 7.0, colour="#e8ff7a")
        b.rig("rr_surf", sgn * (SHORE_X + 1.5), HIGH + 0.3, -40.0, w=80.0, yaw=sgn * math.pi / 2.0, tide=True,
              high=HIGH, ebb=2.6)
        b.rig("rr_surf", sgn * (SHORE_X + 1.5), HIGH + 0.3, 60.0, w=60.0, yaw=sgn * math.pi / 2.0, tide=True,
              high=HIGH, ebb=2.6)
        b.rig("pb_crabs", sgn * 108.0, 0.2, -50.0, q=[sgn * 108.0, 0.2, -20.0], n=3, seed=sgn * 2.0)
    b.rig("rr_surf", 0.0, HIGH + 0.3, SOUTH + 1.5, w=2 * SHORE_X - 10.0, yaw=0.0, tide=True, high=HIGH, ebb=2.6)
    b.rig("rr_gulls", 0.0, 36.0, 40.0, r=40.0, n=4, seed=3)


def build(b: ArenaArea) -> None:
    rng = random.Random(0x6107)
    isle = Isle(b, rng)
    _land(isle)
    _water(isle)
    _edges(isle)
    _temple(isle)
    _causeways(isle)
    _lagoon_floor(isle)
    _swamp(isle)
    _half(isle, -1.0)
    _half(isle, 1.0)
    _festival(isle)
    galleon(isle, "red", 0.0)
    galleon(isle, "blue", 0.0)
    _galleon_feet(isle)
    _meta(isle)
