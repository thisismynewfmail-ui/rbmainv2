"""Ghost Fleet Cove: a moonlit cove where a whole fleet went down -- masts
standing up out of the black water, hulls rotting on the sand, and in the
middle of it all the flagship, sunk to her gunwales and still flying her
rags, the idol on her quarterdeck.  Above the cove a graveyard climbs a
hill in three steps to the crypt at the top; on either wing a beached
wreck and a drowned chapel.  Green lights drift over all of it.

Layout (north is -z; the Scarlet Corsairs' ship off the west shore, the
Azure Buccaneers' off the east)::

    z -120  ======= crags =======  THE CRYPT  ======= crags =======
    z  -66   cliffs     graves   ( the graveyard hill, three steps )   graves    cliffs
    z  -36   beached wreck            the well, the old timbers          beached wreck
   SCARLET   (its ghosts' den)   ------- the cove's north shore -------  (its ghosts' den)  BLUE
    QUEEN    the drowned chapel  ~~~ pier ~~ THE FLAGSHIP ~~ pier ~~~   the drowned chapel  MARLIN
    z  100   sunken masts       ~~~~~~~~~ the cove, out to sea ~~~~~~~~~      sunken masts

The halves are mirror images.  The crypt, the cove and the flagship are as
far from one ship as the other.

The twist is the ghosts (``extra["twist"] = "ghosts"``): the fog rises off
the wrecks and the dead crews climb out -- out of the crypt and out of the
beached wrecks (``barracks``) -- and march their beats (``patrol`` marks,
by ``route``: round the foot of the hill, round each wing), pistols
cocked, firing at any pirate they see.  A skeleton cut down drops its
purse.
"""
from __future__ import annotations

import math
import random

from ..calamity_coast.town import skirt
from ..kit import ArenaArea, backdrop, building, flight, gable, rect, slab
from .common import IRON, PLANK, SEA_TOP, SEABED, SHIP_X, SHORE_X, TIMBER, Isle, galleon

HALF = (170.0, 120.0)
SKY = {"top": "#081028", "horizon": "#34486e", "sun": [-0.35, 0.55, -0.55], "clouds": 0.4,
       "tint": "#a8c0f0"}
AMBIENT = "#7a8ab4"
GROUND = "#3e5a48"
FOG = 600.0

MOSS = "#3e5a48"             # the island's turf, dark and wet
MOSS_DARK = "#33503e"
SAND_NIGHT = "#a89a7a"
WET = "#8a7e62"
PATH = "#6a6a62"
STONE = "#7a7a86"
STONE_DARK = "#5a5a68"
ROT = "#3a3428"              # the wrecks' rotten timber
ROT_LIGHT = "#54463a"
GHOST = "#7aff9a"            # the ghost-light
BONE = "#e8e4d4"
SOUTH = 100.0
NORTH = -100.0               # the foot of the crags either side of the hill
BACK = -104.0                # the hill's back, against the crags
COVE = (-46.0, 46.0, 22.0, SOUTH)
# the graveyard hill: (half-width, front z, top) -- each step up and in
TIERS = ((60.0, -40.0, 2.0), (48.0, -54.0, 4.0), (36.0, -66.0, 6.0))
STAIR_W = 3.0                # the central stair's half-width
SIDE_STAIRS = ((66.0, 60.0, -80.0, -74.0), (54.0, 48.0, -94.0, -88.0), (42.0, 36.0, -86.0, -80.0))
CRYPT = (-10.0, 10.0, -98.0, -82.0)
SHIP = (-12.0, 12.0, 40.0, 76.0)       # the flagship's hull
DECK = 5.0
FORE_Y = 8.0
QUARTER_Y = 9.0
PIER_Z = (54.0, 60.0)
PIER_Y = 1.6
WRECK = (76.0, 100.0, -44.0, -28.0)    # each wing's beached wreck (east; mirrored): the ghosts' den
WRECK_DOOR = (84.0, 92.0)
CHAPEL = (76.0, 96.0, 30.0, 50.0)
MASTS = ((30.0, 34.0, 12.0), (34.0, 76.0, 9.0), (22.0, 92.0, 14.0))


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
    isle.land(MOSS, holes=[west, east, south, COVE], soil="#3a3428")
    for area in (west, east, south, COVE):
        slab(b, area, SEABED, 3.0, WET, studs=True)
    for k, top in enumerate((-1.0, -2.0)):
        colour = SAND_NIGHT if k == 0 else WET
        for sgn in (-1.0, 1.0):
            xa, xb = sorted((sgn * (SHORE_X + 3.0 * k), sgn * (SHORE_X + 3.0 * (k + 1))))
            b.box([(xa + xb) / 2.0, (SEABED + top) / 2.0, (NORTH + hz) / 2.0],
                  [xb - xa, top - SEABED, hz - NORTH], colour, studs=True)
            # the south shore either side of the cove's mouth
            xa, xb = sorted((sgn * COVE[1], sgn * SHORE_X))
            za, zb = SOUTH + 3.0 * k, SOUTH + 3.0 * (k + 1)
            b.box([(xa + xb) / 2.0, (SEABED + top) / 2.0, (za + zb) / 2.0], [xb - xa, top - SEABED, zb - za],
                  colour, studs=True)
    # the cove's own beaches, stepping down into it
    for k, top in enumerate((-1.0, -2.0)):
        colour = SAND_NIGHT if k == 0 else WET
        a, c = k * 4.0, (k + 1) * 4.0
        for sgn in (-1.0, 1.0):
            xa, xb = sorted((sgn * (COVE[1] - a), sgn * (COVE[1] - c)))
            b.box([(xa + xb) / 2.0, (SEABED + top) / 2.0, (COVE[2] + COVE[3]) / 2.0],
                  [xb - xa, top - SEABED, COVE[3] - COVE[2]], colour, studs=True)
        b.box([0.0, (SEABED + top) / 2.0, COVE[2] + (a + c) / 2.0], [2 * (COVE[1] - 8.0), top - SEABED, c - a],
              colour, studs=True)
    for area in ((-hx, -SHORE_X, -hz, hz), (SHORE_X, hx, -hz, hz), (-SHORE_X, SHORE_X, SOUTH, hz), COVE):
        isle.water(area, SEABED, colour="#1a3a4e", alpha=0.62)
    for x0, x1, z0, z1 in ((-hx - m - 300.0, -hx - m, -hz - m - 300.0, hz + m + 300.0),
                           (hx + m, hx + m + 300.0, -hz - m - 300.0, hz + m + 300.0),
                           (-hx - m, hx + m, hz + m, hz + m + 300.0)):
        b.box([(x0 + x1) / 2.0, (SEABED - 6.0 + SEA_TOP) / 2.0, (z0 + z1) / 2.0],
              [x1 - x0, SEA_TOP - SEABED + 6.0, z1 - z0], "#16303e", material="glass", alpha=0.68,
              collide=False)
    # covers: kept off everything that stands on the turf; paths, then
    # beaches and the darker moss
    s = isle.s
    keep = [(-TIERS[0][0], TIERS[0][0], BACK, TIERS[0][1])]
    keep += [WRECK, _m(WRECK), CHAPEL, _m(CHAPEL), (-3.0, 3.0, TIERS[0][1], TIERS[0][1] + 4.0),
             (-4.0, 4.0, -12.0, -4.0)]
    for near, far, z0, z1 in SIDE_STAIRS[:1]:
        keep += [(far, near, z0, z1), _m((far, near, z0, z1))]
    for r in keep:
        s.reserve(r)
    for sgn in (-1.0, 1.0):
        def X(x: float, sgn: float = sgn) -> float:
            return sgn * x
        isle.trail([(X(109.5), -15.0), (X(72.0), -15.0), (X(72.0), -77.0), (X(67.5), -77.0)], colour=PATH)
        isle.trail([(X(109.5), 15.0), (X(64.0), 15.0), (X(64.0), 57.0), (X(48.5), 57.0)], colour=PATH)
        isle.trail([(X(86.0), 15.0), (X(86.0), 27.5)], colour=PATH)
        isle.trail([(X(64.0), -15.0), (X(8.0), -15.0)], colour=PATH)
    isle.trail([(0.0, -36.0 + 2.5), (0.0, 19.5)], colour=PATH)
    for x0, x1, z0, z1 in ((-SHORE_X, -102.0, NORTH, SOUTH), (102.0, SHORE_X, NORTH, SOUTH),
                           (-102.0, COVE[0], 92.0, SOUTH), (COVE[1], 102.0, 92.0, SOUTH),
                           (-60.0, COVE[0], COVE[2], 92.0), (COVE[1], 60.0, COVE[2], 92.0),
                           (-60.0, 60.0, 12.0, COVE[2])):
        s.lay(rect(x0, x1, z0, z1), 0.1, SAND_NIGHT)
    for r in ((70.0, 104.0, -10.0, 8.0), (66.0, 100.0, 60.0, 90.0), (20.0, 40.0, -36.0, -20.0)):
        for rr in (r, _m(r)):
            s.lay(rect(*rr), 0.08, MOSS_DARK)


# =============================================================== the edges
def _edges(isle: Isle) -> None:
    b = isle.b
    hx, hz = HALF
    rng = isle.rng
    m = b.margin
    rocks = (STONE_DARK, "#4a4a58", STONE, "#3e3e4c")
    isle.cliffs("x", -TIERS[0][0], TIERS[0][0], -hz - m, BACK, rng.uniform(17.0, 20.0), rocks, green=MOSS_DARK,
                vines=False, recess=0.0)
    for sgn in (-1.0, 1.0):
        a0, a1 = sorted((sgn * TIERS[0][0], sgn * SHORE_X))
        isle.cliffs("x", a0, a1, -hz - m, NORTH, rng.uniform(22.0, 26.0), rocks, green=MOSS_DARK, vines=False)
        a0, a1 = sorted((sgn * SHORE_X, sgn * (hx + m)))
        isle.cliffs("x", a0, a1, -hz - m, NORTH, 30.0, rocks, base=SEABED, green=MOSS_DARK, step=14.5,
                    recess=0.0, vines=False)
        b.box([sgn * (hx + m / 2.0), (SEABED + 6.0) / 2.0, (NORTH + hz + m) / 2.0],
              [m, 6.0 - SEABED, hz + m - NORTH], STONE_DARK)
    b.box([0.0, (SEABED + 6.0) / 2.0, hz + m / 2.0], [2 * hx, 6.0 - SEABED, m], STONE_DARK)
    # the reefs' crowns: the ribs of older wrecks, black against the fog
    for k in range(18):
        z = NORTH + (k + 0.5) * (hz + m - NORTH) / 18.0
        for sgn in (-1.0, 1.0):
            b.box([sgn * (hx + m / 2.0) + rng.uniform(-1.0, 1.0), 6.0 + 1.0 + (k % 3) * 0.4, z],
                  [m - 2.0 - (k % 2) * 0.6, 2.0 + (k % 3) * 0.8, (hz + m - NORTH) / 18.0 - 2.0],
                  ROT if k % 3 == 0 else STONE_DARK)
    for k in range(18):
        x = -hx + (k + 0.5) * 2 * hx / 18.0
        b.box([x, 6.0 + 1.0 + (k % 3) * 0.4, hz + m / 2.0 + rng.uniform(-1.0, 1.0)],
              [2 * hx / 18.0 - 2.0, 2.0 + (k % 3) * 0.8, m - 2.0 - (k % 2) * 0.6],
              ROT if k % 3 == 1 else STONE_DARK)
    skirt(b, hx, hz, "#2a2a30", top=SEABED - 3.05)
    backdrop(b, "hills", 8.0, rng, sides=("z-",), colours=["#1e2a30", "#243238", "#1a242a"], depth=160.0)


# ================================================================ the hill
def _hill(isle: Isle) -> None:
    """The graveyard hill: three steps of turf, each a strip that never
    overlaps another, a stair straight up the middle to the crypt and stairs
    up the sides from the wings; the graves in rows."""
    b = isle.b
    rng = isle.rng
    for k, (hw, front, top) in enumerate(TIERS):
        colour = (MOSS, MOSS_DARK)[k % 2]
        if k + 1 < len(TIERS):
            hw2, front2, _t = TIERS[k + 1]
            b.box([0.0, top / 2.0, (front2 + front) / 2.0], [2 * hw, top, front - front2], colour, studs=True)
            for sgn in (-1.0, 1.0):
                b.box([sgn * (hw2 + hw) / 2.0, top / 2.0, (BACK + front2) / 2.0], [hw - hw2, top, front2 - BACK],
                      colour, studs=True)
        else:
            b.box([0.0, top / 2.0, (BACK + front) / 2.0], [2 * hw, top, front - BACK], colour, studs=True)
        # a dry-stone retaining wall along each step's face
        y0 = 0.0 if k == 0 else TIERS[k - 1][2]
        for sgn in (-1.0, 1.0):
            a, c = STAIR_W + 1.0, hw
            b.box([sgn * (a + c) / 2.0, (y0 + top) / 2.0, front + 0.3], [c - a, top - y0, 0.6], STONE_DARK)
    # the central stair, and the stairs up the sides
    for k, (hw, front, top) in enumerate(TIERS):
        below = 0.0 if k == 0 else TIERS[k - 1][2]
        flight(b, "z", front + 4.0, front, -STAIR_W, STAIR_W, below, top, STONE, fill=below, rise=1.0)
        for sgn in (-1.0, 1.0):
            b.cyl([sgn * (STAIR_W + 0.5), below + 1.4, front + 3.4], [0.5, 2.8, 0.5], IRON, material="metal")
            b.box([sgn * (STAIR_W + 0.5), below + 3.1, front + 3.4], [0.8, 0.6, 0.8], GHOST, material="neon")
    for k, (near, far, z0, z1) in enumerate(SIDE_STAIRS):
        below = 0.0 if k == 0 else TIERS[k - 1][2]
        for sgn in (-1.0, 1.0):
            flight(b, "x", sgn * near, sgn * far, z0, z1, below, TIERS[k][2], STONE, fill=below)
    # the graves: headstones and crosses in crooked rows, a fresh grave or two
    spots = []
    for k, (hw, front, top) in enumerate(TIERS[:2]):
        front2 = TIERS[k + 1][1]
        for row in range(2):
            z = front - 3.5 - row * 5.0
            if z < front2 + 1.5:
                continue
            x = STAIR_W + 5.0
            while x < hw - 3.0:
                spots.append((x + rng.uniform(-0.6, 0.6), top, z + rng.uniform(-0.5, 0.5)))
                x += rng.uniform(4.6, 6.4)
    for k, (hw, front, top) in enumerate(TIERS[:2]):
        hw2 = TIERS[k + 1][0]
        for z in (-62.0, -76.0, -100.0):
            if z > TIERS[k + 1][1]:
                continue
            spots.append(((hw + hw2) / 2.0 + rng.uniform(-1.0, 1.0), top, z + rng.uniform(-1.0, 1.0)))
    # (none on the fresh grave)
    spots = [p for p in spots if not (20.0 < p[0] < 29.0 and -64.0 < p[2] < -55.0)]
    for x, y, z in spots:
        for sgn in (-1.0, 1.0):
            px = sgn * x
            kind = int(abs(x * 7 + z * 3)) % 4
            if kind == 0:
                b.box([px, y + 1.3, z], [0.5, 2.6, 0.5], STONE)
                b.box([px, y + 1.9, z], [1.8, 0.5, 0.5], STONE)
            elif kind == 1:
                b.box([px, y + 0.9, z], [2.6, 1.8, 4.4], STONE_DARK)
                b.box([px, y + 1.9, z], [2.8, 0.2, 4.6], STONE)
            else:
                h = 2.0 + (kind - 2) * 0.6
                b.box([px, y + h / 2.0, z], [1.5, h, 0.5], STONE if kind == 2 else "#8a8a94")
                b.box([px, y + h + 0.15, z], [1.1, 0.3, 0.5], STONE_DARK)
    for sgn in (-1.0, 1.0):
        x, z = sgn * 24.0, -60.0
        b.box([x, TIERS[1][2] + 0.03, z], [2.2, 0.06, 4.0], "#2a2018", collide=False)
        b.box([x + sgn * 2.2, TIERS[1][2] + 0.4, z], [1.6, 0.8, 3.6], "#4a3a2a")
        isle.dig(x, TIERS[1][2], z + 4.2, "a fresh grave")
    # dead trees on the hill, moss hanging off them
    for x, z, y in ((52.0, -68.0, TIERS[0][2]), (40.0, -96.0, TIERS[1][2]), (22.0, -86.0, TIERS[2][2])):
        for sgn in (-1.0, 1.0):
            _dead_tree(isle, sgn * x, z, y, 10.0 + abs(x) * 0.06)
    b.landmark(0.0, -50.0, "the graveyard")


def _dead_tree(isle: Isle, x: float, z: float, y: float, h: float) -> None:
    """A dead tree: a black trunk, bare branches, grey moss trailing off
    them (see-through: a curtain, not a wall)."""
    b = isle.b
    b.cyl([x, y + h / 2.0, z], [1.1, h, 1.1], "#2a2620")
    for k, a in enumerate((0.4, 2.2, 4.0, 5.4)):
        yy = y + h * (0.55 + (k % 3) * 0.14)
        b.box([x + math.cos(a) * 1.8, yy + 0.8, z + math.sin(a) * 1.8], [4.0, 0.4, 0.4], "#2a2620",
              collide=False, r=[0.0, -a, 0.45])
        b.box([x + math.cos(a) * 3.0, yy - 0.9, z + math.sin(a) * 3.0], [0.9, 3.0, 0.2], "#8a9a8a", alpha=0.6,
              collide=False, r=[0.0, -a, 0.0])


def _crypt(isle: Isle) -> None:
    """The crypt at the top of the hill: stone, a porch of columns under a
    pediment, its door open on the dark; inside, the sarcophagi -- one of
    them open.  The ghosts come down the hill from here."""
    b = isle.b
    x0, x1, z0, z1 = CRYPT
    y = TIERS[-1][2]
    building(b, rect(x0, x1, z0, z1), y, 10.0, STONE, t=1.2, roof_colour=STONE_DARK, roof_t=0.8,
             floor_colour="#4a4a54", doors={"z+": [(-3.0, 3.0, y + 6.5)]}, lights=GHOST, studs_roof=False)
    gable(b, rect(x0, x1, z0, z1), y + 10.8, STONE_DARK, "z", tiers=3, rise=1.2, overhang=0.6)
    # the porch: four columns, an architrave, the pediment over it
    for x in (-7.5, -4.5, 4.5, 7.5):
        b.cyl([x, y + 4.0, z1 + 3.0], [1.4, 8.0, 1.4], "#9a9aa4")
    b.box([0.0, y + 8.5, z1 + 2.5], [20.0, 1.0, 5.0], STONE)
    b.box([0.0, y + 9.4, z1 + 2.5], [16.0, 0.8, 4.4], STONE_DARK)
    b.box([0.0, y + 10.1, z1 + 2.5], [10.0, 0.6, 3.8], STONE)
    b.box([0.0, y + 9.1, z1 + 5.03], [3.0, 1.2, 0.06], GHOST, material="neon", collide=False)
    # inside: three stone coffins, green candles on them, one lid pushed off
    for k, x in enumerate((-5.0, 0.0, 5.0)):
        b.box([x, y + 0.4 + 0.8, -93.0], [2.6, 1.6, 5.0], "#6a6a74")
        if k != 1:
            b.box([x, y + 0.4 + 1.75, -93.0], [2.9, 0.3, 5.3], "#8a8a94")
            b.cyl([x + 0.8, y + 0.4 + 2.2, -91.6], [0.3, 0.6, 0.3], "#e8e4d4")
            b.box([x + 0.8, y + 0.4 + 2.65, -91.6], [0.2, 0.3, 0.2], GHOST, material="neon", collide=False)
        else:
            b.box([x + 2.4, y + 0.4 + 0.15, -88.6], [2.9, 0.3, 5.3], "#8a8a94", r=[0.0, 0.4, 0.0])
    isle.loot(0.0, y + 0.4, -87.0, "gem", "the crypt")
    b.landmark(0.0, -90.0, "the crypt")


# ============================================================ the flagship
def _flagship(isle: Isle) -> None:
    """The flagship, sunk to her gunwales in the middle of the cove: her
    hull black and weeded, her decks still above the water -- the waist,
    the forecastle and the quarterdeck with the idol on it -- broken masts
    in rags of green sail, the lanterns in her stern windows still lit."""
    b = isle.b
    x0, x1, z0, z1 = SHIP
    b.box([0.0, (SEABED + DECK) / 2.0, (z0 + z1) / 2.0], [x1 - x0, DECK - SEABED, z1 - z0], ROT)
    b.box([0.0, (SEABED + FORE_Y) / 2.0, (34.0 + z0) / 2.0], [18.0, FORE_Y - SEABED, z0 - 34.0], ROT_LIGHT)
    b.box([0.0, (DECK + FORE_Y) / 2.0, (z0 + 48.0) / 2.0], [x1 - x0, FORE_Y - DECK, 48.0 - z0], ROT_LIGHT)
    b.box([0.0, (DECK + QUARTER_Y) / 2.0, (66.0 + z1) / 2.0], [x1 - x0, QUARTER_Y - DECK, z1 - 66.0], ROT_LIGHT)
    b.box([0.0, (SEABED + 12.0) / 2.0, (z1 + 80.0) / 2.0], [22.0, 12.0 - SEABED, 80.0 - z1], ROT)
    # the weed at her waterline, the gold of her old trim, holes stove in
    for sgn in (-1.0, 1.0):
        b.box([sgn * (x1 + 0.05), -0.6, (z0 + z1) / 2.0], [0.1, 0.8, z1 - z0], "#2a5a3a", collide=False)
        b.box([sgn * (x1 + 0.05), 3.6, (z0 + z1) / 2.0], [0.1, 0.5, z1 - z0], "#8a7030", collide=False)
        for zz in (46.0, 63.0):
            b.box([sgn * (x1 + 0.05), 1.4, zz], [0.1, 2.2, 3.0], "#141210", collide=False)
    # the stairs up to the forecastle and the quarterdeck, both sides
    for sgn in (-1.0, 1.0):
        a, c = sorted((sgn * 4.0, sgn * 8.0))
        flight(b, "z", 52.0, 48.0, a, c, DECK, FORE_Y, ROT_LIGHT, fill=DECK)
        flight(b, "z", 62.0, 66.0, a, c, DECK, QUARTER_Y, ROT_LIGHT, fill=DECK)
    # bulwarks: along the waist (gaps where the piers come aboard), round
    # the forecastle and the quarterdeck
    for sgn in (-1.0, 1.0):
        for za, zb in ((48.0, PIER_Z[0]), (PIER_Z[1], 66.0)):
            b.box([sgn * (x1 - 0.3), DECK + 0.7, (za + zb) / 2.0], [0.6, 1.4, zb - za], ROT_LIGHT)
        b.box([sgn * (x1 - 0.3), FORE_Y + 0.6, (z0 + 48.0) / 2.0], [0.6, 1.2, 48.0 - z0], ROT_LIGHT)
        b.box([sgn * (x1 - 0.3), QUARTER_Y + 0.6, (66.0 + z1) / 2.0], [0.6, 1.2, z1 - 66.0], ROT_LIGHT)
    b.box([0.0, FORE_Y + 0.6, 34.3], [18.0, 1.2, 0.6], ROT_LIGHT)
    # her figurehead: a skeleton reaching out over the water
    b.box([0.0, 5.2, 33.2], [1.2, 3.6, 1.6], BONE)
    b.sphere([0.0, 7.6, 33.0], [1.4, 1.5, 1.4], BONE)
    b.box([0.0, 6.2, 32.4], [3.6, 0.4, 0.4], BONE)
    b.cyl([0.0, 9.0, 30.0], [0.8, 9.0, 0.8], ROT_LIGHT, collide=False, r=[1.15, 0.0, 0.0])
    # the masts, broken, their sails in rags, black flags on what is left
    for x, z, base, top, d in ((0.0, 42.0, FORE_Y, 22.0, 1.4), (0.0, 57.0, DECK, 28.0, 1.8),
                               (0.0, 74.6, QUARTER_Y, 21.0, 1.4)):
        b.cyl([x, (base + top) / 2.0, z], [d, top - base, d], ROT)
        b.cone([x, top + 0.8, z], [d, 1.6, d], ROT, collide=False)
        yard = top - 4.0
        b.box([x, yard, z], [16.0, 0.6, 0.6], ROT)
        for k in range(4):
            if k == 2:
                continue
            h = 6.6 - (k % 2) * 2.0
            b.box([x - 6.0 + k * 4.0, yard - 0.3 - h / 2.0, z + 0.36], [3.4, h, 0.12], "#a8c8a8", alpha=0.4,
                  collide=False)
        b.rig("rr_flag", x, top - 0.2, z, yaw=math.pi / 2.0, w=4.0, h=2.4, colours=["#141414", "#202020"])
    b.box([0.0, 21.0, 57.0], [4.0, 0.6, 4.0], ROT)
    b.box([0.0, 21.8, 57.0], [3.8, 1.0, 3.8], ROT_LIGHT, alpha=0.9)
    # the quarterdeck: the idol's altar, the wheel
    isle.idol(0.0, QUARTER_Y, 70.0, colour="#4a4a54")
    b.cyl([-7.0, QUARTER_Y + 1.6, 74.0], [0.5, 3.2, 0.5], ROT_LIGHT)
    b.cyl([-7.0, QUARTER_Y + 3.4, 73.6], [3.0, 0.3, 3.0], "#6a4a2e", collide=False, r=[math.pi / 2.0, 0.0, 0.0])
    # her lanterns, still lit: on posts at the corners, in the stern windows
    for x, z, y in ((-10.6, 41.0, FORE_Y), (10.6, 41.0, FORE_Y), (-10.6, 75.0, QUARTER_Y),
                    (10.6, 75.0, QUARTER_Y)):
        b.cyl([x, y + 1.6, z], [0.4, 3.2, 0.4], IRON, material="metal")
        b.box([x, y + 3.6, z], [1.0, 1.2, 1.0], GHOST, material="neon")
    for k in range(4):
        b.box([-7.5 + k * 5.0, 7.0, 80.05], [2.6, 2.4, 0.1], GHOST, material="neon", collide=False)
    # treasure about her decks
    isle.loot(0.0, DECK, 56.0 + 4.0, "bar", "the flagship's waist")
    isle.loot(-6.0, FORE_Y, 38.0, "any", "the flagship's forecastle")
    isle.loot(6.0, FORE_Y, 38.0, "any", "the flagship's forecastle")
    b.landmark(0.0, 58.0, "the flagship")


def _piers(isle: Isle) -> None:
    """The piers out to the flagship from either shore of the cove, a stair
    up her bow from the north shore."""
    b = isle.b
    za, zb = PIER_Z
    for sgn in (-1.0, 1.0):
        xa, xb = sorted((sgn * COVE[1], sgn * 16.0))
        n = 10
        for k in range(n):
            px = xa + (k + 0.5) * (xb - xa) / n
            b.box([px, PIER_Y - 0.25, (za + zb) / 2.0], [(xb - xa) / n - 0.3, 0.5, zb - za],
                  PLANK if k % 2 else "#7a5a3a")
        for dz in (za + 0.4, zb - 0.4):
            b.box([(xa + xb) / 2.0, PIER_Y - 0.75, dz], [xb - xa, 0.5, 0.8], TIMBER)
        for px in (xa + 1.0, (xa + xb) / 2.0, xb - 1.0):
            for dz in (za + 0.4, zb - 0.4):
                b.cyl([px, (SEABED + PIER_Y - 1.0) / 2.0, dz], [0.8, PIER_Y - 1.0 - SEABED, 0.8], TIMBER)
        # posts with lanterns along it
        for px in (xa + 6.0, xb - 6.0):
            b.cyl([px, PIER_Y + 1.6, za + 0.3], [0.4, 3.2, 0.4], TIMBER)
            b.box([px, PIER_Y + 3.6, za + 0.3], [0.8, 1.0, 0.8], GHOST, material="neon")
        # the boarding stair up her side
        flight(b, "x", sgn * 16.0, sgn * SHIP[1], za, zb, PIER_Y, DECK, ROT_LIGHT, fill=SEABED)
        isle.loot(sgn * 30.0, PIER_Y, (za + zb) / 2.0, "any", "the pier")
    flight(b, "z", COVE[2], 34.0, -3.0, 3.0, 0.0, FORE_Y, ROT_LIGHT, fill=SEABED)


def _masts(isle: Isle) -> None:
    """Masts of the drowned fleet standing up out of the cove, yards and
    rags still on them."""
    b = isle.b
    for x, z, h in MASTS:
        for sgn in (-1.0, 1.0):
            px = sgn * x
            b.cyl([px, (SEABED + h) / 2.0, z], [1.2, h - SEABED, 1.2], ROT)
            b.box([px, h - 2.4, z], [9.0, 0.5, 0.5], ROT)
            b.box([px - sgn * 1.6, h - 5.0, z + 0.35], [4.0, 4.4, 0.1], "#a8c8a8", alpha=0.35, collide=False)
            b.cone([px, h + 0.6, z], [1.2, 1.2, 1.2], ROT, collide=False)
    # a crow's nest on the tallest, a lantern in it
    for sgn in (-1.0, 1.0):
        x, z, h = MASTS[2]
        b.cyl([sgn * x, h - 1.0, z], [3.4, 1.2, 3.4], ROT_LIGHT)
        b.box([sgn * x, h + 0.3, z], [1.0, 1.4, 1.0], GHOST, material="neon")


# ================================================================ the plaza
def _plaza(isle: Isle) -> None:
    """The ground at the foot of the hill: the old well, timbers the sea
    threw up, anchors, rowboats on the cove's north shore."""
    b = isle.b
    # the well
    b.cyl([0.0, 0.7, -8.0], [6.0, 1.4, 6.0], STONE)
    b.cyl([0.0, 1.41, -8.0], [4.6, 0.02, 4.6], "#0a1418", collide=False)
    for sgn in (-1.0, 1.0):
        b.box([sgn * 2.6, 3.2, -8.0], [0.5, 3.8, 0.5], TIMBER)
    b.box([0.0, 5.2, -8.0], [6.0, 0.4, 0.5], TIMBER)
    b.box([0.0, 5.7, -8.0], [6.4, 0.6, 3.0], ROT_LIGHT)
    b.cyl([0.0, 3.8, -8.0], [0.9, 1.0, 0.9], "#6a4a2e")
    b.box([0.0, 4.65, -8.0], [0.1, 0.7, 0.1], "#c8a878", collide=False)
    isle.dig(0.0, None, -16.0, "by the well")
    for sgn in (-1.0, 1.0):
        def X(x: float) -> float:
            return sgn * x
        # timbers thrown up by the sea, a fallen yard, an anchor half buried
        b.box([X(22.0), 0.6, -2.0], [12.0, 1.2, 1.2], ROT)
        b.box([X(30.0), 0.5, 4.0], [1.0, 1.0, 9.0], ROT_LIGHT)
        b.box([X(16.0), 0.06, 6.0], [3.0, 0.12, 0.4], IRON, material="metal", collide=False, r=[0.0, 0.5, 0.0])
        b.box([X(15.0), 1.4, 6.6], [0.5, 2.8, 0.5], IRON, material="metal")
        b.box([X(15.0), 2.6, 6.6], [2.4, 0.4, 0.4], IRON, material="metal")
        isle.barrel(X(34.0), -22.0, colour=ROT_LIGHT)
        isle.barrel(X(37.0), -20.4, colour=ROT_LIGHT)
        # rowboats drawn up on the cove's north shore
        for k, x in enumerate((28.0, 36.0)):
            by = isle.top(X(x), 17.0)
            b.box([X(x), by + 0.7, 17.0], [3.0, 1.4, 7.0], ("#3a4a5a", ROT_LIGHT)[k])
            b.box([X(x), by + 1.45, 17.0], [2.6, 0.1, 6.4], "#1a1a1a")
        # lantern posts along the shore
        for x in (12.0, 40.0):
            y = isle.top(X(x), 20.0)
            b.cyl([X(x), y + 2.0, 20.0], [0.4, 4.0, 0.4], IRON, material="metal")
            b.box([X(x), y + 4.5, 20.0], [0.9, 1.0, 0.9], GHOST, material="neon")
        isle.loot(X(24.0), None, -12.0, "any", "the old timbers")
        isle.loot(X(42.0), None, 18.0, "any", "the cove's shore")
        isle.dig(X(30.0), None, -30.0, "under the hill")
        isle.dig(X(20.0), None, 14.0, "the north shore")
    b.landmark(0.0, -8.0, "the old well")


# ================================================================ the wings
def _wreck(isle: Isle, sgn: float) -> None:
    """A beached wreck on the wing: its hull broken open on the side
    towards the island, a scrap of deck still over its stern -- the ghosts
    of her crew climb out of it."""
    b = isle.b

    def X(x: float) -> float:
        return sgn * x

    x0, x1 = sorted((X(WRECK[0]), X(WRECK[1])))
    z0, z1 = WRECK[2], WRECK[3]
    t = 1.2
    b.box([(x0 + x1) / 2.0, 0.4, (z0 + z1) / 2.0], [x1 - x0 - 2 * t, 0.8, z1 - z0 - 2 * t], "#4a3a2a")
    b.box([(x0 + x1) / 2.0, 3.0, z0 + t / 2.0], [x1 - x0, 6.0, t], ROT)
    for xx in (x0 + t / 2.0, x1 - t / 2.0):
        b.box([xx, 3.0, (z0 + z1) / 2.0], [t, 6.0, z1 - z0 - 2 * t], ROT)
    for a, c, h in ((WRECK[0], WRECK_DOOR[0], 5.0), (WRECK_DOOR[1], WRECK[1], 4.2)):
        wa, wb = sorted((X(a), X(c)))
        b.box([(wa + wb) / 2.0, h / 2.0, z1 - t / 2.0], [wb - wa, h, t], ROT)
    # the scrap of deck over the end towards the sea, splintered at its edge
    da, db = sorted((X(88.0), X(WRECK[1])))
    b.box([(da + db) / 2.0, 6.3, (z0 + z1) / 2.0], [db - da, 0.6, z1 - z0], ROT_LIGHT)
    for k in range(4):
        b.box([X(88.0 - 0.5 * (k % 2)), 6.2, z0 + 2.0 + k * 3.6], [1.4, 0.6, 2.4], ROT_LIGHT)
    # her stripe, the ghost-light inside her, a mast stump
    b.box([(x0 + x1) / 2.0, 4.6, z0 - 0.05], [x1 - x0, 0.5, 0.1], "#8a7030", collide=False)
    b.box([X(83.0), 3.0, z0 + t + 0.05], [3.0, 1.0, 0.1], GHOST, material="neon", collide=False)
    b.cyl([X(94.0), 6.6 + 4.0, -36.0], [1.2, 8.0, 1.2], ROT)
    b.rig("rr_flag", X(94.0), 14.4, -36.0, yaw=math.pi / 2.0, w=3.0, h=2.0, colours=["#141414", "#222222"])
    b.rig("pb_wisps", X(88.0), 3.0, -36.0, r=10.0, n=5, seed=sgn * 3.0)
    isle.loot(X(95.0), 0.8, -36.0, "gem", "the beached wreck")
    b.landmark(X(88.0), -36.0, "the %s wreck" % ("west" if sgn < 0 else "east"))


def _chapel(isle: Isle, sgn: float) -> None:
    """The drowned chapel: its walls broken down to different heights, the
    roof long gone, pews rotting, green candles on the altar."""
    b = isle.b
    rng = isle.rng

    def X(x: float) -> float:
        return sgn * x

    x0, x1 = sorted((X(CHAPEL[0]), X(CHAPEL[1])))
    z0, z1 = CHAPEL[2], CHAPEL[3]
    t = 1.2
    slab(b, rect(x0 + t, x1 - t, z0 + t, z1 - t), 0.3, 0.3, "#6a6a72", studs=True)
    # the walls in pieces: the door in the north wall, gaps where they fell
    pieces = [("z", z0 + t / 2.0, (CHAPEL[0], 82.0), 7.5), ("z", z0 + t / 2.0, (90.0, CHAPEL[1]), 5.0),
              ("z", z1 - t / 2.0, (CHAPEL[0], 84.0), 4.0), ("z", z1 - t / 2.0, (88.0, CHAPEL[1]), 8.0),
              ("x", CHAPEL[0] + t / 2.0, (z0 + t, 38.0), 6.0), ("x", CHAPEL[0] + t / 2.0, (42.0, z1 - t), 3.0),
              ("x", CHAPEL[1] - t / 2.0, (z0 + t, z1 - t), 9.0)]
    for axis, at, (a, c), h in pieces:
        if axis == "z":
            pa, pc = sorted((X(a), X(c)))
            b.box([(pa + pc) / 2.0, h / 2.0, at], [pc - pa, h, t], STONE)
        else:
            b.box([X(at), h / 2.0, (a + c) / 2.0], [t, h, c - a], STONE)
    # the tall east wall: its window, lit green from somewhere
    b.box([X(CHAPEL[1] - t - 0.05), 5.6, 40.0], [0.1, 3.4, 2.2], GHOST, material="neon", collide=False)
    b.box([X(CHAPEL[1] - t - 0.05), 7.5, 40.0], [0.1, 0.6, 1.4], GHOST, material="neon", collide=False)
    # the altar, the candles on it; the pews
    ax = X(92.0)
    b.box([ax, 0.3 + 0.8, 40.0], [2.4, 1.6, 5.0], STONE_DARK)
    for dz in (-1.6, 0.0, 1.6):
        b.cyl([ax, 1.9 + 0.4, 40.0 + dz], [0.3, 0.8, 0.3], BONE)
        b.box([ax, 2.85, 40.0 + dz], [0.2, 0.3, 0.2], GHOST, material="neon", collide=False)
    for k in range(4):
        for dz in (-5.0, 5.0):
            if (k + int(dz > 0)) % 3 == 2:
                continue
            b.box([X(80.0 + k * 2.8), 0.3 + 0.5, 40.0 + dz], [1.0, 1.0, 5.0], ROT_LIGHT)
    isle.loot(X(88.6), 0.3, 40.0, "gem", "the drowned chapel")
    # the bell tower's stump at the corner, its bell fallen beside it
    tx, tz = X(CHAPEL[0] - 2.2), z0 - 2.2
    b.box([tx, 6.0, tz], [4.4, 12.0, 4.4], STONE_DARK)
    b.cone([X(CHAPEL[0] - 5.4), 1.0, z0 - 1.0], [2.4, 2.0, 2.4], "#7a6a3a", material="metal")
    # a few graves by the chapel
    for k, (x, z) in enumerate(((100.0, 34.0), (102.0, 42.0), (100.0, 50.0), (78.0, 56.0), (86.0, 58.0))):
        h = 1.8 + (k % 3) * 0.4
        b.box([X(x), h / 2.0, z], [0.5, h, 1.4], STONE)
    b.landmark(X(86.0), 40.0, "the %s chapel" % ("west" if sgn < 0 else "east"))


def _half(isle: Isle, sgn: float) -> None:
    """One crew's wing (mirrored for the other): the beached wreck its
    ghosts come out of, the drowned chapel, lanterns, dead trees, rocks."""
    b = isle.b
    rng = isle.rng
    west = sgn < 0

    def X(x: float) -> float:
        return sgn * x

    _wreck(isle, sgn)
    _chapel(isle, sgn)
    # lantern posts round the ghosts' beat, dead trees, rocks, drowned palms
    for x, z in ((56.0, -24.0), (56.0, 22.0), (108.0, -24.0), (108.0, 22.0)):
        y = isle.top(X(x), z)
        b.cyl([X(x), y + 2.2, z], [0.4, 4.4, 0.4], IRON, material="metal")
        b.box([X(x), y + 4.9, z], [0.9, 1.0, 0.9], GHOST, material="neon")
    for x, z in ((80.0, -64.0), (96.0, -70.0), (68.0, 70.0), (100.0, 84.0), (52.0, 86.0)):
        _dead_tree(isle, X(x), z, isle.top(X(x), z), 11.0)
    for x, z, w in ((88.0, -84.0, 4.0), (104.0, 64.0, 3.2), (60.0, 76.0, 3.6), (76.0, -2.0, 3.0)):
        isle.rock(X(x), z, w, w * 0.8, w * 0.6, colour=STONE_DARK, cap=MOSS_DARK)
    isle.flag(X(108.0), 2.0, None, "#c8302a" if west else "#2a6ab8", h=11.0)
    # X's and loot about the wing
    isle.dig(X(96.0), None, -56.0, "under the crags")
    isle.dig(X(66.0), None, 36.0, "by the chapel")
    isle.dig(X(92.0), None, 70.0, "the south moss")
    isle.dig(X(66.0), None, -40.0, "by the wreck")
    isle.loot(X(104.0), None, -40.0, "any", "the beach")
    isle.loot(X(80.0), None, 8.0, "any", "the moss")
    isle.loot(X(56.0), None, 50.0, "any", "the cove's edge")
    isle.loot(X(84.0), None, -90.0, "any", "under the crags")
    isle.loot(X(54.0), TIERS[0][2], -70.0, "bar", "the graveyard")


# ============================================================== the glow
def _mushrooms(isle: Isle, x: float, z: float, n: int, seed: float) -> None:
    """A clump of glowing toadstools, cyan and violet, on whatever is
    underfoot."""
    b = isle.b
    y = isle.top(x, z)
    for k in range(n):
        a = seed + k * 2.39
        r = 0.6 + (k % 3) * 0.7
        px, pz = x + math.cos(a) * r, z + math.sin(a) * r
        h = 0.5 + (k % 4) * 0.25
        b.cyl([px, y + h / 2.0, pz], [0.24, h, 0.24], "#d8e8e0", collide=False)
        b.sphere([px, y + h + 0.1, pz], [0.9 - (k % 3) * 0.15, 0.4, 0.9 - (k % 3) * 0.15],
                 ("#5ae8ff", "#c86aff", "#7aff9a")[k % 3], material="neon", collide=False)


def _glow(isle: Isle) -> None:
    """What lights the cove at night: toadstools glowing round the dead
    trees and the graves, candles left on headstones, and the ghost-light
    standing up off the crypt where everybody can see it."""
    b = isle.b
    for k, (x, z) in enumerate(((50.0, -70.0), (30.0, -46.0), (14.0, -60.0), (66.0, 72.0), (98.0, 80.0),
                                (54.0, 88.0), (80.0, -60.0), (92.0, -66.0), (70.0, -8.0), (100.0, 46.0),
                                (40.0, 2.0), (52.0, -30.0))):
        for sgn in (-1.0, 1.0):
            _mushrooms(isle, sgn * x, z, 4 + k % 3, k * 1.7 + (0.0 if sgn > 0 else 0.9))
    for sgn in (-1.0, 1.0):
        for x, z, y in ((11.0, -43.5, TIERS[0][2]), (36.0, -48.5, TIERS[0][2]), (17.0, -57.5, TIERS[1][2])):
            b.cyl([sgn * x, y + 0.3, z - 1.0], [0.3, 0.6, 0.3], BONE)
            b.box([sgn * x, y + 0.75, z - 1.0], [0.2, 0.3, 0.2], GHOST, material="neon", collide=False)
    # the ghost-light: a pale green column standing up off the crypt's roof
    b.cyl([0.0, 40.0, -90.0], [6.0, 44.0, 6.0], GHOST, material="neon", alpha=0.12, collide=False)
    b.cyl([0.0, 40.0, -90.0], [2.4, 44.0, 2.4], "#c8ffd8", material="neon", alpha=0.2, collide=False)


# ============================================================ the ghosts
def _ghosts(isle: Isle) -> None:
    """Where the dead come from and where they walk.  ``barracks`` in order
    crypt, west wreck, east wreck (twice over): the n-th ghost to rise
    walks route n % 3 -- the crypt's down the hill and round the foot of
    it, each wreck's round its own wing.  Each route's first three points
    are the way out; it loops from the fourth on."""
    b = isle.b
    ty = TIERS[-1][2]
    for k in range(2):
        dx = (-2.4, 2.4)[k]
        b.mark("barracks", dx, ty, -74.0)
        b.mark("barracks", -88.0 + dx, 0.8, -36.0)
        b.mark("barracks", 88.0 + dx, 0.8, -36.0)
    t1, t2, t3 = (t[2] for t in TIERS)
    f1, f2, f3 = (t[1] for t in TIERS)
    s = 0.12
    crypt = [(0.0, t3, -70.0), (0.0, t3, f3), (0.0, t2, f3 + 4.0),
             (0.0, t2, f2), (0.0, t1, f2 + 4.0), (0.0, t1, f1), (0.0, 0.0, f1 + 4.0), (0.0, s, -28.0),
             (-44.0, s, -28.0), (-44.0, s, 12.0), (44.0, s, 12.0), (44.0, s, -28.0), (0.0, s, -28.0),
             (0.0, 0.0, f1 + 4.0), (0.0, t1, f1), (0.0, t1, f2 + 4.0)]
    routes = [crypt]
    for sgn in (-1.0, 1.0):
        routes.append([(sgn * 88.0, 0.8, -32.0), (sgn * 88.0, s, -26.0), (sgn * 88.0, s, -20.0),
                       (sgn * 60.0, s, -20.0), (sgn * 60.0, s, 18.0), (sgn * 104.0, s, 18.0),
                       (sgn * 104.0, s, -20.0), (sgn * 88.0, s, -20.0)])
    for r, points in enumerate(routes):
        for i, (x, y, z) in enumerate(points):
            b.mark("patrol", x, y, z, route=r, i=i)


# ================================================================ meta
def _meta(isle: Isle) -> None:
    b = isle.b
    for x, z, name in ((0.0, 40.0, "the cove"), (-SHIP_X, 0.0, "the Scarlet Queen"),
                       (SHIP_X, 0.0, "the Blue Marlin")):
        b.landmark(x, z, name)
    b.camera(64.0, 38.0, 108.0, 0.0, 6.0, 20.0)
    b.camera(-100.0, 36.0, 60.0, -10.0, 6.0, 0.0)
    b.camera(40.0, 30.0, -20.0, 0.0, 8.0, -90.0)
    b.camera(-34.0, 16.0, 40.0, 0.0, 8.0, 64.0)
    b.extra.update({"twist": "ghosts", "water": SEA_TOP, "ghosts_every": [48.0, 64.0], "ghosts_for": 30.0,
                    "warn": 6.0})
    b.rig("rr_weather", 0.0, 0.0, 0.0, weather="mist", wind=[0.4, 0.2])
    b.rig("pb_ghostship", -320.0, SEA_TOP, 230.0, q=[320.0, SEA_TOP, 230.0], seed=1.0, s=1.2)
    b.rig("pb_ghostship", 330.0, SEA_TOP, -60.0, q=[330.0, SEA_TOP, 120.0], seed=4.0, s=0.9)
    b.rig("pb_wisps", 0.0, 9.0, -60.0, r=30.0, n=10, seed=1.0)
    b.rig("pb_wisps", 0.0, 2.0, 60.0, r=34.0, n=10, seed=2.0)
    b.rig("pb_glow", 0.0, SEA_TOP + 0.05, 62.0, n=40, w=80.0, d=70.0, seed=5.0,
          colours=["#7aff9a", "#5ae8c8", "#b8ffd0", "#7ad8ff"])
    for sgn in (-1.0, 1.0):
        b.rig("pb_wisps", sgn * 86.0, 3.0, 40.0, r=12.0, n=5, seed=sgn * 6.0)
        b.rig("rr_surf", sgn * (SHORE_X + 6.5), SEA_TOP + 0.3, -50.0, w=80.0, yaw=sgn * math.pi / 2.0)
        b.rig("rr_surf", sgn * (SHORE_X + 6.5), SEA_TOP + 0.3, 60.0, w=60.0, yaw=sgn * math.pi / 2.0)
        b.rig("pb_crabs", sgn * 108.0, 0.2, -60.0, q=[sgn * 108.0, 0.2, -24.0], n=3, seed=sgn * 2.0,
              colour="#8a9aa8")


def build(b: ArenaArea) -> None:
    rng = random.Random(0x6057)
    isle = Isle(b, rng)
    _land(isle)
    _edges(isle)
    _hill(isle)
    _crypt(isle)
    _flagship(isle)
    _piers(isle)
    _masts(isle)
    _plaza(isle)
    _half(isle, -1.0)
    _half(isle, 1.0)
    _glow(isle)
    _ghosts(isle)
    galleon(isle, "red", 0.0)
    galleon(isle, "blue", 0.0)
    _meta(isle)
