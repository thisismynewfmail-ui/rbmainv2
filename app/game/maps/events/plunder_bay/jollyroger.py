"""Jolly Roger Fair: the pirates' own funfair on a cove at dusk -- the sky
going orange and violet, the bulbs coming on.  In the middle the big top,
red and white, open on every side, the idol on its podium in the circus
ring with the stands round it and a trapeze artist swinging overhead; up
the midway the booths -- coconut shy, duck shoot, hoopla -- with their
striped canopies and strings of lights; at its head the Ferris wheel
turning on its terrace, and along the cliff tops behind it the roller
coaster, the great Jolly Roger flying over all.  On either wing a
helter-skelter, the hall of mirrors, a carousel, the swinging galleon
ride, the fortune teller's tent and a hedge maze with a fountain at its
heart; along the beach the boardwalk -- high strikers, candy floss, grog
-- and a pier out to the fireworks barge moored in the bay.

Layout (north is -z; the Scarlet Corsairs' ship off the west shore, the
Azure Buccaneers' off the east)::

    z -120  ====== cliffs: THE ROLLER COASTER on top, THE JOLLY ROGER flying ======
    z  -86   helter-skelter  hall of     ( THE FERRIS WHEEL )   hall of   helter-skelter
                             mirrors       on its terrace       mirrors
    z  -46   carousel  fortune     booths | the midway | booths     fortune  carousel
   SCARLET   swinging galleon        ( THE BIG TOP: the idol )       swinging galleon  BLUE
    QUEEN    mound                                                          mound    MARLIN
    z   40   hedge maze                                                  hedge maze
    z   67   ================== THE BOARDWALK: strikers, stalls ==================
    z   82   beach            |pier|                                    beach
    z  110   ~~~~~~~~~~~~~~~~~~~~~~~ THE FIREWORKS BARGE ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The halves are mirror images.

The twist is the eruption -- here the fireworks barge going up
(``extra["twist"] = "eruption"``, ``extra["style"]["bomb"] = "rocket"``,
reworded by ``extra["twist_text"]``): somebody puts a torch to the powder
and the barge (``extra["vent"]``) fires its whole show into the fair --
rockets coming down on the pirates and on the open ground (``rain``
marks), and the prize gold blown out over the same spots.
"""
from __future__ import annotations

import math
import random

from ..calamity_coast.town import skirt
from ..kit import ArenaArea, backdrop, building, flight, rect, slab
from .common import PLANK, SAND, SAND_WET, SEA_TOP, SEABED, SHIP_X, SHORE_X, TIMBER, Isle, galleon

HALF = (170.0, 120.0)
SKY = {"top": "#2a2a6a", "horizon": "#ff9a6a", "sun": [-0.85, 0.16, 0.3], "clouds": 0.45, "tint": "#ffe4d0"}
AMBIENT = "#c8b0b8"
GROUND = "#5a8a4a"
FOG = 700.0

TURF = "#5a9a44"
EARTH = "#c8a878"
SAWDUST = "#d8b878"
RED = "#d83a32"
WHITE = "#f4f0e8"
GOLD = "#e8b830"
PINK = "#ff8ad8"
TEAL = "#2aa8a0"
PURPLE = "#8a3ac8"
BULB = "#fff0a0"
HEDGE = "#2e7a3a"
STONE = "#a89a88"
DECK = "#a87a4a"
SOUTH = 92.0                 # the waterline: the bay beyond
NORTH = -104.0               # the foot of the cliffs behind the fair
TERRACE = (-34.0, 34.0, NORTH, -66.0)
TER_Y = 3.0
HUB = (0.0, 23.0, -86.0)     # the Ferris wheel's hub
TOP_R = 22.0                 # the big top's ring of poles
CONE_R = 24.0
CONE_Y = 9.0
CONE_H = 13.0
BOARD = (-104.0, 104.0, 62.0, 72.0)
BOARD_Y = 1.6
PIER = (-4.0, 4.0, 72.0, 98.0)
BARGE = (0.0, 112.0)
BOOTHS = (((9.0, 19.0, -60.0, -52.0), "coconut", RED, WHITE), ((9.0, 19.0, -49.0, -41.0), "ducks", TEAL, GOLD),
          ((9.0, 19.0, -38.0, -30.0), "hoopla", PURPLE, PINK))       # east; mirrored
HELTER = (78.0, -88.0)
MIRRORS = (44.0, 66.0, -100.0, -80.0)
CAROUSEL = (70.0, -42.0)
FORTUNE = (100.0, -44.0)
SWING = (86.0, -14.0)
MAZE = (46.0, 78.0, 26.0, 56.0)
MOUND = (54.0, -14.0)
BANDSTAND = (0.0, 40.0)
CHAIRS = (21.0, -86.0)       # the chair-o-planes on the terrace (east; mirrored)
TOPIARY = (64.0, 2.0)
FLIGHTS_X = (-84.0, -42.0, 0.0, 42.0, 84.0)


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
    isle.land(TURF, holes=[west, east, south], soil="#5a4a38")
    for area in (west, east, south):
        slab(b, area, SEABED, 3.0, SAND_WET, studs=True)
    for k, top in enumerate((-1.0, -2.0)):
        colour = SAND if k == 0 else SAND_WET
        for sgn in (-1.0, 1.0):
            xa, xb = sorted((sgn * (SHORE_X + 3.0 * k), sgn * (SHORE_X + 3.0 * (k + 1))))
            b.box([(xa + xb) / 2.0, (SEABED + top) / 2.0, (NORTH + SOUTH + 6.0) / 2.0],
                  [xb - xa, top - SEABED, SOUTH + 6.0 - NORTH], colour, studs=True)
        za, zb = SOUTH + 3.0 * k, SOUTH + 3.0 * (k + 1)
        b.box([0.0, (SEABED + top) / 2.0, (za + zb) / 2.0], [2 * SHORE_X, top - SEABED, zb - za], colour,
              studs=True)
    for area in ((-hx, -SHORE_X, -hz, hz), (SHORE_X, hx, -hz, hz), (-SHORE_X, SHORE_X, SOUTH, hz)):
        isle.water(area, SEABED, colour="#2a7a9a", alpha=0.62)
    for x0, x1, z0, z1 in ((-hx - m - 300.0, -hx - m, -hz - m - 300.0, hz + m + 300.0),
                           (hx + m, hx + m + 300.0, -hz - m - 300.0, hz + m + 300.0),
                           (-hx - m, hx + m, hz + m, hz + m + 300.0)):
        b.box([(x0 + x1) / 2.0, (SEABED - 6.0 + SEA_TOP) / 2.0, (z0 + z1) / 2.0],
              [x1 - x0, SEA_TOP - SEABED + 6.0, z1 - z0], "#2a5a8a", material="glass", alpha=0.6, collide=False)
    # the ground covers: the midway's packed earth, the beach, the shore strips
    s = isle.s
    keep = [TERRACE, (-TOP_R - 1.0, TOP_R + 1.0, -TOP_R - 1.0, TOP_R + 1.0), BOARD, (PIER[0], PIER[1], BOARD[3], SOUTH)]
    for r, _k, _a, _b in BOOTHS:
        keep += [r, _m(r)]
    for r in (MIRRORS, MAZE):
        keep += [r, _m(r)]
    for r in keep:
        s.reserve(r)
    s.lay(rect(-7.0, 7.0, -62.0, -24.0), 0.08, EARTH)
    for x0, x1, z0, z1 in ((-SHORE_X, -102.0, NORTH, SOUTH), (102.0, SHORE_X, NORTH, SOUTH),
                           (-102.0, 102.0, BOARD[3], SOUTH)):
        s.lay(rect(x0, x1, z0, z1), 0.1, SAND)
    for sgn in (-1.0, 1.0):
        def X(x: float, sgn: float = sgn) -> float:
            return sgn * x
        isle.trail([(X(101.5), 15.0), (X(30.0), 15.0)], colour=EARTH)
        isle.trail([(X(30.0), -40.0), (X(30.0), 15.0)], colour=EARTH)
        isle.trail([(X(40.0), 15.0), (X(40.0), 58.0)], colour=EARTH)


# =============================================================== the edges
def _edges(isle: Isle) -> None:
    b = isle.b
    hx, hz = HALF
    rng = isle.rng
    m = b.margin
    rocks = ("#7a5a4a", "#6a4a3e", "#8a6a58", "#5a4038")
    isle.cliffs("x", -SHORE_X, SHORE_X, -hz - m, NORTH, rng.uniform(13.0, 14.5), rocks, green="#3a7a3a",
                recess=0.0, step=14.0)
    for sgn in (-1.0, 1.0):
        a0, a1 = sorted((sgn * SHORE_X, sgn * (hx + m)))
        isle.cliffs("x", a0, a1, -hz - m, NORTH, 22.0, rocks, base=SEABED, green="#3a7a3a", step=14.5,
                    recess=0.0)
        b.box([sgn * (hx + m / 2.0), (SEABED + 6.0) / 2.0, (NORTH + hz + m) / 2.0],
              [m, 6.0 - SEABED, hz + m - NORTH], "#7a5a4a")
    b.box([0.0, (SEABED + 6.0) / 2.0, hz + m / 2.0], [2 * hx, 6.0 - SEABED, m], "#7a5a4a")
    for k in range(18):
        z = NORTH + (k + 0.5) * (hz + m - NORTH) / 18.0
        for sgn in (-1.0, 1.0):
            b.box([sgn * (hx + m / 2.0) + rng.uniform(-1.0, 1.0), 6.0 + 1.0 + (k % 3) * 0.4, z],
                  [m - 2.0 - (k % 2) * 0.6, 2.0 + (k % 3) * 0.8, (hz + m - NORTH) / 18.0 - 2.0],
                  (RED, GOLD, TEAL)[k % 3] if k % 4 == 0 else "#8a6a58")
    for k in range(18):
        x = -hx + (k + 0.5) * 2 * hx / 18.0
        b.box([x, 6.0 + 1.0 + (k % 3) * 0.4, hz + m / 2.0 + rng.uniform(-1.0, 1.0)],
              [2 * hx / 18.0 - 2.0, 2.0 + (k % 3) * 0.8, m - 2.0 - (k % 2) * 0.6],
              (PINK, GOLD, TEAL)[k % 3] if k % 4 == 1 else "#8a6a58")
    skirt(b, hx, hz, "#3a5a6a", top=SEABED - 3.05)
    backdrop(b, "hills", 10.0, rng, sides=("z-",), colours=["#3a5a4a", "#4a6a50", "#2e4a40"], depth=180.0)


# ======================================================= the coaster
COASTER = [(90.0, 28.0, -108.0), (76.0, 28.0, -108.0), (62.0, 30.0, -108.0), (48.0, 36.0, -108.0),
           (34.0, 42.0, -108.0), (22.0, 46.0, -108.0), (12.0, 44.0, -108.0), (2.0, 31.0, -108.0),
           (-8.0, 27.0, -108.0), (-18.0, 30.0, -108.0), (-28.0, 38.0, -108.0), (-38.0, 40.0, -108.0),
           (-48.0, 34.0, -108.0), (-58.0, 28.0, -108.0), (-68.0, 32.0, -108.0), (-78.0, 36.0, -108.0),
           (-88.0, 34.0, -108.0), (-94.0, 32.0, -110.0), (-96.0, 31.0, -112.0), (-94.0, 30.0, -114.0),
           (-88.0, 29.0, -116.0), (-76.0, 33.0, -116.0), (-62.0, 38.0, -116.0), (-50.0, 36.0, -116.0),
           (-38.0, 30.0, -116.0), (-24.0, 28.0, -116.0), (-10.0, 32.0, -116.0), (4.0, 36.0, -116.0),
           (18.0, 33.0, -116.0), (32.0, 29.0, -116.0), (46.0, 31.0, -116.0), (60.0, 34.0, -116.0),
           (74.0, 30.0, -116.0), (86.0, 28.5, -116.0), (92.0, 28.0, -114.0), (94.0, 28.0, -112.0),
           (92.0, 28.0, -110.0)]


def _coaster(isle: Isle) -> None:
    """The roller coaster along the cliff tops: red rails on white
    trestles, a lift hill up to the crest and the big drop, camelbacks, a
    turn at either end; the station at the east end.  The train is a rig
    running the same points."""
    b = isle.b
    n = len(COASTER)
    for k in range(n):
        ax, ay, az = COASTER[k]
        bx, by, bz = COASTER[(k + 1) % n]
        dx, dy, dz = bx - ax, by - ay, bz - az
        length = math.sqrt(dx * dx + dy * dy + dz * dz)
        yaw = math.atan2(dx, dz)
        pitch = -math.atan2(dy, math.hypot(dx, dz))
        if abs(pitch) < 0.003:
            pitch = 0.003          # a hair of a tilt: the rails are always drawn as turned parts
        mx, my, mz = (ax + bx) / 2.0, (ay + by) / 2.0, (az + bz) / 2.0
        cx, cz = math.cos(yaw), -math.sin(yaw)
        for e in (-0.8, 0.8):
            b.box([mx + cx * e, my, mz + cz * e], [0.3, 0.3, length + 0.2], "#e8302a", collide=False,
                  r=[pitch, yaw, 0.0])
        b.box([mx, my - 0.25, mz], [2.0, 0.2, length * 0.6], "#3a3a42", collide=False, r=[pitch, yaw, 0.0])
        ground = b.surface(ax, az, 80.0)
        b.cyl([ax, (ground + ay - 0.4) / 2.0, az], [0.7, ay - 0.4 - ground, 0.7], WHITE, collide=False)
        if k % 3 == 0:
            b.box([ax, ay - 0.5, az], [2.6, 0.3, 0.6], WHITE, collide=False, r=[0.0, yaw + 0.003, 0.0])
    # the station at the east end, its roof striped
    sx, sz = 83.0, -108.0
    top = b.surface(sx, sz, 80.0)
    b.box([sx, (top + 27.0) / 2.0, sz - 2.6], [12.0, 27.0 - top, 2.4], "#e8e0d0")
    b.box([sx, 27.0 + 0.2, sz - 2.6], [12.0, 0.4, 3.6], PLANK)
    for e in (-5.6, 5.6):
        b.box([sx + e, 27.4 + 2.2, sz - 3.4], [0.4, 4.4, 0.4], WHITE, collide=False)
    for k in range(6):
        b.box([sx - 5.0 + k * 2.0, 31.8, sz - 2.4], [2.0, 0.3, 4.8], (RED, WHITE)[k % 2], collide=False)
    b.rig("pb_coaster", 0.0, 0.0, 0.0, path=[list(p) for p in COASTER], cars=4)


def _jollyroger(isle: Isle) -> None:
    """The fair's flag: a great Jolly Roger on a mast on the cliffs."""
    b = isle.b
    x, z = 0.0, -112.0
    top = b.surface(x, z, 80.0)
    b.cyl([x, top + 17.0, z], [0.9, 34.0, 0.9], "#4a3020")
    b.sphere([x, top + 34.4, z], [1.4, 1.4, 1.4], GOLD, material="metal", collide=False)
    b.rig("pb_jollyroger", x + 0.45, top + 33.4, z, yaw=0.0, w=22.0, h=14.0)


# ===================================================== the Ferris wheel
def _terrace(isle: Isle) -> None:
    """The Ferris wheel's terrace: a stone platform up flights from the
    midway and from either side, flower beds and lamps along its edge; the
    wheel turning over its machine house, its A-frames standing either
    side; the ticket booth."""
    b = isle.b
    x0, x1, z0, z1 = TERRACE
    b.box([0.0, TER_Y / 2.0, (z0 + z1) / 2.0], [x1 - x0, TER_Y, z1 - z0], STONE)
    b.box([0.0, TER_Y + 0.05, (z0 + z1) / 2.0], [x1 - x0 - 1.2, 0.1, z1 - z0 - 1.2], "#c8b8a0", studs=True)
    top = TER_Y + 0.1
    flight(b, "z", z1 + 4.0, z1, -8.0, 8.0, 0.0, TER_Y, STONE, rise=0.75)
    for sgn in (-1.0, 1.0):
        flight(b, "x", sgn * (x1 + 4.0), sgn * x1, -92.0, -82.0, 0.0, TER_Y, STONE, rise=0.75)
    # the machine house under the wheel and the A-frames either side of it
    hx, hy, hz = HUB
    b.box([hx, top + 1.5, hz], [9.0, 3.0, 5.0], "#c8302a")
    b.box([hx, top + 3.15, hz], [9.6, 0.3, 5.6], GOLD, material="metal")
    for e in (-1.0, 1.0):
        for side in (-1.0, 1.0):
            fx, fz = hx + side * 9.0, hz + e * 3.2
            b.box([fx, top + 0.5, fz], [1.8, 1.0, 1.8], "#8a8a92", material="metal")
            dx, dy, dz = hx - fx, hy - (top + 1.0), (hz + e * 1.8) - fz
            length = math.sqrt(dx * dx + dy * dy + dz * dz)
            b.box([(fx + hx) / 2.0, (top + 1.0 + hy) / 2.0, (fz + hz + e * 1.8) / 2.0], [0.8, length, 0.8],
                  WHITE, collide=False, r=[math.atan2(dz, dy), 0.0, -math.asin(dx / length)])
    b.rig("pb_ferris", hx, hy, hz, yaw=0.0, r=14.0, n=10)
    isle.loot(hx + 6.4, top, hz + 5.6, "gem", "the Ferris wheel")
    # flower beds and lamps round the edge, the ticket booth, benches
    for sgn in (-1.0, 1.0):
        for z in (-98.0, -76.0):
            x = sgn * 28.0
            b.box([x, top + 0.35, z], [6.0, 0.7, 2.4], "#8a6a4a")
            b.box([x, top + 0.75, z], [5.6, 0.1, 2.0], "#4a3a2a", collide=False)
            for k in range(5):
                b.sphere([x - 2.2 + k * 1.1, top + 1.05, z], [0.8, 0.6, 0.8], (RED, GOLD, PINK, WHITE, PURPLE)[k],
                         collide=False)
        for z in (-100.0, -78.0, -70.0):
            x = sgn * 32.5
            b.cyl([x, top + 2.4, z], [0.4, 4.8, 0.4], "#2a2a32", material="metal")
            b.sphere([x, top + 5.2, z], [1.2, 1.2, 1.2], BULB, material="neon")
        b.box([sgn * 14.0, top + 0.5, -70.0], [4.0, 1.0, 1.2], DECK)
        b.box([sgn * 14.0, top + 1.4, -70.6], [4.0, 1.2, 0.2], DECK)
    for x in (-12.0, 12.0):
        b.box([x, top + 2.0, -96.0], [4.0, 4.0, 3.0], RED)
        b.box([x, top + 4.2, -96.0], [4.8, 0.4, 3.8], GOLD)
        b.box([x, top + 2.4, -94.44], [2.4, 1.2, 0.12], "#2a2a32", collide=False)
    # the chair-o-planes either side of the wheel, a low fence round each
    for sgn in (-1.0, 1.0):
        cx, cz = sgn * CHAIRS[0], CHAIRS[1]
        b.cyl([cx, top + 0.3, cz], [5.0, 0.6, 5.0], GOLD, material="metal")
        b.cyl([cx, top + 0.6 + 4.9, cz], [1.4, 9.8, 1.4], WHITE)
        b.cyl([cx, top + 0.6 + 3.0, cz], [1.6, 0.6, 1.6], RED)
        b.cyl([cx, top + 0.6 + 6.2, cz], [1.6, 0.6, 1.6], RED)
        b.rig("pb_chairs", cx, top, cz, h=10.4, r=3.6, len=4.4, n=12, seed=2.0 + sgn,
              colour=RED if sgn < 0 else TEAL)
        for k in range(16):
            a = (k + 0.5) * math.tau / 16.0
            b.box([cx + math.sin(a) * 8.6, top + 0.5, cz + math.cos(a) * 8.6], [0.3, 1.0, 0.3], WHITE)
        # cafe tables under parasols along the front of the terrace
        for tx in (19.0, 26.0):
            x = sgn * tx
            b.cyl([x, top + 0.5, -71.0], [2.0, 1.0, 2.0], WHITE)
            b.cyl([x, top + 3.2 + 0.0, -71.0], [0.2, 6.4, 0.2], WHITE)
            b.cone([x, top + 6.9, -71.0], [4.6, 1.4, 4.6], (RED, TEAL)[int(tx) % 2], collide=False)
            for e in (-1.0, 1.0):
                b.box([x + e * 1.8, top + 0.35, -71.0], [0.8, 0.7, 0.8], GOLD)
    b.landmark(hx, hz, "the Ferris wheel")


# ========================================================= the big top
def _bigtop(isle: Isle) -> None:
    """The big top: a ring of poles holding up a great cone of red and
    white canvas, the sides rolled up so it is open all round; bunting on
    its guy ropes, its flag flying.  Inside, sawdust, the circus ring with
    the idol on its podium, the stands in the four corners, two king poles
    with the trapeze platforms and the trapeze swinging between them."""
    b = isle.b
    for k in range(16):
        a = k * math.tau / 16.0
        x, z = math.sin(a) * TOP_R, math.cos(a) * TOP_R
        b.cyl([x, CONE_Y / 2.0, z], [0.9, CONE_Y, 0.9], (RED, WHITE)[k % 2])
        b.box([x, CONE_Y - 0.4, z], [1.3, 0.8, 1.3], GOLD, material="metal")
    b.cone([0.0, CONE_Y + CONE_H / 2.0, 0.0], [2 * CONE_R, CONE_H, 2 * CONE_R], RED, collide=False)
    slope = math.atan2(CONE_H, CONE_R)
    slant = math.hypot(CONE_H, CONE_R)
    up = 0.4 * slant / 0.9
    for k in range(8):
        a = k * math.tau / 8.0
        r = CONE_R - up * math.cos(slope) + 0.12 * math.sin(slope)
        y = CONE_Y + up * math.sin(slope) + 0.12 * math.cos(slope)
        b.add("tri", [math.sin(a) * r, y, math.cos(a) * r], [2 * math.pi * CONE_R / 16.0, slant / 0.9, 1.5], WHITE,
              collide=False, r=[-(math.pi / 2.0 - slope), a, 0.0])
    for j in range(32):
        a = (j + 0.5) * math.tau / 32.0
        b.add("tri", [math.sin(a) * (CONE_R + 0.15), CONE_Y - 0.5, math.cos(a) * (CONE_R + 0.15)], [4.6, 1.6, 1.0],
              (GOLD, RED)[j % 2], collide=False, r=[0.0, a, math.pi])
    b.cyl([0.0, CONE_Y + CONE_H + 2.0, 0.0], [0.3, 4.0, 0.3], "#4a3020", collide=False)
    b.rig("rr_flag", 0.15, CONE_Y + CONE_H + 3.6, 0.0, yaw=0.0, w=4.0, h=2.4, colours=[RED, GOLD, RED, GOLD])
    for k in range(4):
        a = (k + 0.5) * math.tau / 4.0
        sx, sz = math.sin(a) * 34.0, math.cos(a) * 34.0
        b.box([sx, 0.4, sz], [0.6, 0.8, 0.6], "#6a4a2a")
        b.rig("pb_bunting", math.sin(a) * TOP_R, CONE_Y - 0.2, math.cos(a) * TOP_R, q=(sx, 0.8, sz), sag=0.6, size=0.9)
    # inside: the sawdust, the ring, the podium and the idol
    b.cyl([0.0, 0.05, 0.0], [2 * TOP_R - 1.0, 0.1, 2 * TOP_R - 1.0], SAWDUST, collide=False)
    b.add("torus", [0.0, 0.3, 0.0], [15.0, 1.2, 15.0], RED, collide=False)
    b.cyl([0.0, 0.4, 0.0], [11.0, 0.8, 11.0], RED)
    b.cyl([0.0, 0.62, 0.0], [11.06, 0.24, 11.06], WHITE, collide=False)
    b.box([0.0, 0.85, 0.0], [9.6, 0.1, 9.6], GOLD, material="metal")
    isle.idol(0.0, 0.9, 0.0, colour="#c8b898")
    # the stands, stepping up into the four corners
    for sx in (-1.0, 1.0):
        for sz in (-1.0, 1.0):
            for k, a0 in enumerate((6.0, 9.0, 12.0)):
                xa, xb = sorted((sx * a0, sx * 15.0))
                za, zb = sorted((sz * a0, sz * 15.0))
                b.box([(xa + xb) / 2.0, k * 0.9 + 0.45, (za + zb) / 2.0], [xb - xa, 0.9, zb - za], (RED, GOLD, TEAL)[k])
    isle.loot(13.5, 2.7, -13.5, "gem", "the big top's stands")
    isle.loot(-13.5, 2.7, 13.5, "gem", "the big top's stands")
    isle.loot(-13.5, 2.7, -13.5, "bar", "the big top's stands")
    isle.loot(13.5, 2.7, 13.5, "bar", "the big top's stands")
    isle.loot(0.0, None, -8.5, "any", "the circus ring")
    isle.loot(0.0, None, 8.5, "any", "the circus ring")
    # the king poles, the trapeze platforms on them, the trapeze between
    for z in (-10.0, 10.0):
        b.cyl([0.0, 10.5, z], [1.2, 21.0, 1.2], "#c8a040", material="metal")
        b.box([0.0, 12.2, z - 1.4 * (1 if z > 0 else -1)], [2.4, 0.3, 1.6], WHITE, collide=False)
    b.rig("pb_trapeze", 0.0, 19.4, 0.0, yaw=math.pi / 2.0, len=7.0)
    # lights strung under the canvas
    for k in range(8):
        a = (k + 0.25) * math.tau / 8.0
        r = 14.0
        y = CONE_Y + (CONE_R - r) * math.tan(slope)
        b.box([math.sin(a) * r, y - 0.9, math.cos(a) * r], [0.08, 1.8, 0.08], "#4a3a2a", collide=False)
        b.sphere([math.sin(a) * r, y - 2.1, math.cos(a) * r], [0.9, 0.9, 0.9], (BULB, PINK, "#7af0ff")[k % 3],
                 material="neon", collide=False)
    b.landmark(0.0, 0.0, "the big top")


# =========================================================== the midway
def _booth(isle: Isle, r, face: str, kind: str, wall: str, trim: str) -> None:
    """A game booth on the midway: three walls, a counter across the
    front, a striped canopy with bulbs along its edge, the prizes on
    shelves -- teddy bears, goldfish in bags -- and the game: coconuts on
    their posts, ducks on their rail, or bottles for the hoopla."""
    b = isle.b
    x0, x1, z0, z1 = r
    cz = (z0 + z1) / 2.0
    out = -1.0 if face == "x-" else 1.0
    front, back = (x0, x1) if face == "x-" else (x1, x0)
    h = 7.0
    b.box([(x0 + x1) / 2.0, 0.2, cz], [x1 - x0, 0.4, z1 - z0], DECK)
    b.box([back + out * 0.2, 0.4 + h / 2.0, cz], [0.4, h, z1 - z0 - 0.8], wall)
    for zz in (z0 + 0.2, z1 - 0.2):
        b.box([(x0 + x1) / 2.0 - out * 0.2, 0.4 + h / 2.0, zz], [x1 - x0 - 0.4, h, 0.4], wall)
    b.box([front - out * 0.6, 1.0, cz], [1.2, 1.2, z1 - z0 - 0.8], trim)
    b.box([front - out * 0.6, 1.66, cz], [1.4, 0.12, z1 - z0 - 0.6], "#6a3a1a")
    for k in range(5):
        zz = z0 + (k + 0.5) * (z1 - z0) / 5.0
        b.box([(x0 + x1) / 2.0 + out * 0.75, 0.4 + h + 0.15, zz], [x1 - x0 + 1.5, 0.3, (z1 - z0) / 5.0],
              (wall, WHITE)[k % 2])
    for k in range(6):
        zz = z0 + 0.6 + k * (z1 - z0 - 1.2) / 5.0
        b.sphere([front + out * 1.5, 0.4 + h - 0.15, zz], [0.36, 0.36, 0.36], BULB, material="neon", collide=False)
    b.box([(x0 + x1) / 2.0, 0.4 + h + 1.2, cz - (z1 - z0) / 2.0 + 0.3], [x1 - x0 - 1.0, 1.8, 0.3], trim,
          collide=False)
    # the prizes on shelves along the back wall
    for k, y in enumerate((2.6, 3.9, 5.2)):
        b.box([back + out * 0.7, y, cz], [0.6, 0.12, z1 - z0 - 1.2], "#6a3a1a")
        for j in range(4):
            zz = z0 + 1.6 + j * (z1 - z0 - 3.2) / 3.0
            colour = (PINK, "#8a5a3a", TEAL, GOLD)[(j + k) % 4]
            b.sphere([back + out * 0.7, y + 0.41, zz], [0.6, 0.7, 0.5], colour, collide=False)
            b.sphere([back + out * 0.7, y + 0.95, zz], [0.45, 0.45, 0.4], colour, collide=False)
    if kind == "coconut":
        for j in range(4):
            zz = z0 + 1.4 + j * (z1 - z0 - 2.8) / 3.0
            px = back + out * 2.0
            b.cyl([px, 0.4 + 0.9, zz], [0.2, 1.8, 0.2], "#c8a060")
            b.sphere([px, 0.4 + 2.05, zz], [0.7, 0.7, 0.7], "#5a3a1e", collide=False)
    elif kind == "ducks":
        b.box([back + out * 2.0, 1.4, cz], [0.6, 2.0, z1 - z0 - 1.0], "#3a6ac8")
        b.rig("pb_ducks", back + out * 2.0, 2.4, cz, yaw=math.pi / 2.0, w=z1 - z0 - 2.0, n=5)
    else:
        b.box([back + out * 2.0, 0.9, cz], [1.6, 1.0, z1 - z0 - 2.0], "#6a3a1a")
        for j in range(5):
            zz = z0 + 1.6 + j * (z1 - z0 - 3.2) / 4.0
            b.cyl([back + out * 2.0, 1.4 + 0.45, zz], [0.4, 0.9, 0.4], ("#3a8a4a", "#c8a040", "#3a6ac8")[j % 3],
                  material="glass", alpha=0.8, collide=False)
    isle.loot(front - out * 0.6, 1.72, cz, "any", {"coconut": "the coconut shy", "ducks": "the duck shoot",
                                                     "hoopla": "the hoopla stall"}[kind])


def _midway(isle: Isle) -> None:
    b = isle.b
    for r, kind, wall, trim in BOOTHS:
        _booth(isle, r, "x-", kind, wall, trim)
        _booth(isle, _m(r), "x+", kind, wall, trim)
    for z in (-56.0, -45.0, -34.0):
        b.rig("rr_lights", -7.5, 7.3, z, q=(7.5, 7.3, z), n=12, sag=1.2)
    b.rig("rr_lights", -7.5, 7.3, -50.5, q=(7.5, 7.3, -39.5), n=12, sag=1.6)


# ============================================================ the wings
def _helter(isle: Isle, sgn: float) -> None:
    """A helter-skelter: a striped tower with a cone of a roof and a flag,
    the slide winding round it twice to a mat at its foot."""
    b = isle.b
    x, z = sgn * HELTER[0], HELTER[1]
    for k in range(4):
        b.cyl([x, 2.0 + k * 4.0, z], [7.0, 4.0, 7.0], (RED, WHITE)[k % 2])
    b.cyl([x, 16.3, z], [8.2, 0.6, 8.2], GOLD, material="metal")
    b.cone([x, 16.6 + 2.5, z], [8.0, 5.0, 8.0], RED, collide=False)
    b.cyl([x, 22.6, z], [0.2, 2.0, 0.2], "#4a3020", collide=False)
    b.rig("rr_flag", x + 0.1, 23.4, z, yaw=0.0, w=2.6, h=1.6, colours=[GOLD, RED])
    turns, steps = 2.0, 40
    y_top, y_end, rr = 15.2, 1.6, 5.0
    for k in range(steps):
        a0 = sgn * (k / steps) * turns * math.tau
        a1 = sgn * ((k + 1) / steps) * turns * math.tau
        y0 = y_top - (y_top - y_end) * k / steps
        y1 = y_top - (y_top - y_end) * (k + 1) / steps
        am = (a0 + a1) / 2.0
        chord = 2 * rr * math.sin(abs(a1 - a0) / 2.0)
        drop = y0 - y1
        b.box([x + math.sin(am) * rr, (y0 + y1) / 2.0, z + math.cos(am) * rr],
              [math.hypot(chord, drop) + 0.1, 0.3, 2.2], "#ffd84a", collide=False,
              r=[0.0, am, -sgn * math.atan2(drop, chord)])
    end = sgn * turns * math.tau
    mx, mz = x + math.sin(end) * (rr + 2.0), z + math.cos(end) * (rr + 2.0)
    b.box([mx, 0.3, mz], [3.6, 0.6, 3.6], "#3a6ac8")
    b.box([x, 1.6, z + 3.56], [1.8, 3.2, 0.12], "#4a3020", collide=False)
    isle.loot(mx, 0.6, mz, "any", "the helter-skelter")
    b.landmark(x, z, "the west helter-skelter" if sgn < 0 else "the east helter-skelter")


def _mirrors(isle: Isle, sgn: float) -> None:
    """The hall of mirrors: a purple funhouse with gilt trim, a marquee of
    bulbs and great mirrors either side of its door; inside, a little maze
    of mirror panels, the treasure at the back."""
    b = isle.b
    x0, x1 = sorted((sgn * MIRRORS[0], sgn * MIRRORS[1]))
    z0, z1 = MIRRORS[2], MIRRORS[3]
    cx = (x0 + x1) / 2.0
    building(b, rect(x0, x1, z0, z1), 0.0, 9.0, PURPLE, t=0.8, roof_colour="#5a2a8a", roof_t=0.6,
             floor_colour="#3a2a4a", doors={"z+": [(cx - 3.0, cx + 3.0, 7.0)]}, lights=PINK, studs_roof=False)
    for e in (-1.0, 1.0):
        b.box([cx + e * 6.5, 4.0, z1 + 0.07], [3.4, 6.0, 0.1], "#d8e8f0", material="metal", collide=False)
        b.box([cx + e * 6.5, 4.0, z1 + 0.03], [3.9, 6.5, 0.06], GOLD, material="metal", collide=False)
    b.box([cx, 9.6 + 0.9, z1 - 0.4], [12.0, 1.8, 0.4], GOLD)
    b.box([cx, 9.6 + 0.9, z1 - 0.15], [11.0, 1.2, 0.12], PINK, material="neon", collide=False)
    for k in range(12):
        b.sphere([x0 + 1.0 + k * (x1 - x0 - 2.0) / 11.0, 8.9, z1 + 0.25], [0.4, 0.4, 0.4], BULB, material="neon",
                 collide=False)
    # inside: mirror panels to find a way round
    for px, pz0, pz1 in ((cx - 4.0, z0 + 0.8, z0 + 12.0), (cx + 4.0, z0 + 7.0, z1 - 0.8)):
        b.box([px, 3.6, (pz0 + pz1) / 2.0], [0.3, 6.4, pz1 - pz0], "#c8dce8", material="metal")
    isle.loot(x0 + 2.4, 0.4, z0 + 2.4, "gem", "the hall of mirrors")
    isle.loot(x1 - 2.4, 0.4, z0 + 2.4, "bar", "the hall of mirrors")
    b.landmark(cx, (z0 + z1) / 2.0, "the west hall of mirrors" if sgn < 0 else "the east hall of mirrors")


def _carousel(isle: Isle, sgn: float) -> None:
    b = isle.b
    x, z = sgn * CAROUSEL[0], CAROUSEL[1]
    b.cyl([x, 0.5, z], [17.0, 1.0, 17.0], GOLD, material="metal")
    b.cyl([x, 0.02, z], [19.0, 0.04, 19.0], "#c8302a", collide=False)
    b.rig("rr_carousel", x, 0.45, z, r=7.0)
    isle.loot(x + sgn * 6.4, 1.0, z, "any", "the carousel")
    b.landmark(x, z, "the west carousel" if sgn < 0 else "the east carousel")


def _swing(isle: Isle, sgn: float) -> None:
    """The swinging galleon: two A-frames of white girders, the axle
    across their tops, the boat swinging on its arms between them; a
    fence round it and the operator's box."""
    b = isle.b
    x, z = sgn * SWING[0], SWING[1]
    ay = 18.0
    for e in (-3.4, 3.4):
        for f in (-7.0, 7.0):
            fx, fz = x + e, z + f
            b.box([fx, 0.4, fz], [1.4, 0.8, 1.4], "#8a8a92", material="metal")
            dz, dy = z - fz, ay - 0.8
            length = math.hypot(dz, dy)
            b.box([fx, 0.8 + dy / 2.0, (fz + z) / 2.0], [0.7, length, 0.7], WHITE, collide=False,
                  r=[math.atan2(dz, dy), 0.0, 0.0])
        b.box([x + e, ay + 0.2, z], [1.0, 1.0, 1.0], GOLD, material="metal")
    b.cyl([x, ay + 0.2, z], [0.6, 7.6, 0.6], "#8a8a92", material="metal", collide=False, r=[0.0, 0.0, math.pi / 2.0])
    b.rig("pb_swingship", x, ay + 0.2, z, yaw=0.0, arm=10.0, cycle=36.0, seed=1.0 + sgn,
          colour="#8a4a2a" if sgn < 0 else "#2a4a8a", sail=RED if sgn < 0 else "#2a6ab8")
    for xx in (x - 5.4, x + 5.4):
        for zz in (z - 9.0, z + 9.0):
            b.box([xx, 0.6, zz], [0.4, 1.2, 0.4], "#6a4a2a")
    for zz in (z - 9.0, z + 9.0):
        b.box([x, 1.05, zz], [10.4, 0.2, 0.2], "#6a4a2a")
    b.box([x + sgn * 6.8, 1.4, z + 8.0], [2.4, 2.8, 2.4], GOLD)
    b.box([x + sgn * 6.8, 2.95, z + 8.0], [2.8, 0.3, 2.8], RED)
    b.landmark(x, z, "the west swinging galleon" if sgn < 0 else "the east swinging galleon")


def _fortune(isle: Isle, sgn: float) -> None:
    """The fortune teller: a purple tent open towards the fair, a table
    with a glowing crystal ball, a painted caravan beside it."""
    b = isle.b
    x, z = sgn * FORTUNE[0], FORTUNE[1]
    w = 7.0
    for ex in (-1.0, 1.0):
        for ez in (-1.0, 1.0):
            b.cyl([x + ex * (w / 2.0 - 0.3), 2.95, z + ez * (w / 2.0 - 0.3)], [0.5, 5.9, 0.5], GOLD, material="metal")
    back = x + sgn * (w / 2.0 - 0.15)
    b.box([back, 2.95, z], [0.3, 5.9, w - 1.2], PURPLE)
    for ez in (-1.0, 1.0):
        b.box([x + sgn * 0.85, 2.95, z + ez * (w / 2.0 - 0.15)], [4.7, 5.9, 0.3], PURPLE)
    b.box([x, 6.1, z], [w + 0.6, 0.4, w + 0.6], "#5a2a8a")
    b.cone([x, 6.3 + 2.0, z], [w + 0.4, 4.0, w + 0.4], PURPLE, collide=False)
    b.sphere([x, 10.5, z], [0.8, 0.8, 0.8], GOLD, material="metal", collide=False)
    b.cyl([x + sgn * 1.2, 0.6, z], [2.4, 1.2, 2.4], "#3a1a3a")
    b.sphere([x + sgn * 1.2, 1.6, z], [1.0, 1.0, 1.0], "#bfe8ff", material="glass", alpha=0.6, collide=False)
    b.sphere([x + sgn * 1.2, 1.6, z], [0.5, 0.5, 0.5], "#7af0ff", material="neon", collide=False)
    isle.loot(x - sgn * 0.4, None, z + 1.6, "any", "the fortune teller's tent")
    # the caravan: painted red and gold, wheels, a curved roof, steps
    cx, cz = x - sgn * 1.0, z - 12.0
    b.box([cx, 2.9, cz], [4.0, 3.4, 8.0], "#c8302a")
    b.box([cx, 4.75, cz], [4.4, 0.3, 8.4], GOLD)
    b.cyl([cx, 4.9, cz], [4.2, 1.6, 8.2], "#3a6ac8", collide=False, r=[math.pi / 2.0, 0.0, 0.0])
    for ex in (-2.1, 2.1):
        for ez in (-2.6, 2.6):
            b.cyl([cx + ex, 1.2, cz + ez], [2.4, 0.3, 2.4], GOLD, collide=False, r=[0.0, 0.0, math.pi / 2.0])
    b.box([cx, 0.6, cz + 4.6], [1.6, 1.2, 1.2], "#6a3a1a")
    b.box([cx, 2.7, cz + 4.02], [1.4, 2.6, 0.08], "#ffd84a", collide=False)


def _maze(isle: Isle, sgn: float) -> None:
    """A hedge maze: two rings of hedge, the way in on the side towards
    the fair and from the boardwalk, a hedge across the outer path so one
    way round is a dead end; at its heart a fountain, a golden mermaid on
    it, and the treasure."""
    b = isle.b
    x0, x1 = sorted((sgn * MAZE[0], sgn * MAZE[1]))
    z0, z1 = MAZE[2], MAZE[3]
    t, h = 1.2, 4.8
    inner = (x0 + 6.0, x1 - 6.0, z0 + 6.0, z1 - 6.0)
    cx, cz = (x0 + x1) / 2.0, (z0 + z1) / 2.0
    near = x0 if sgn > 0 else x1          # the side towards the fair
    far = x1 if sgn > 0 else x0

    def hedge(xa: float, xb: float, za: float, zb: float) -> None:
        xa, xb = sorted((xa, xb))
        za, zb = sorted((za, zb))
        b.box([(xa + xb) / 2.0, h / 2.0, (za + zb) / 2.0], [xb - xa, h, zb - za], HEDGE)
        b.box([(xa + xb) / 2.0, h + 0.1, (za + zb) / 2.0], [xb - xa - 0.2, 0.2, zb - za - 0.2], "#3a8a44",
              collide=False)

    # the outer ring: in from the fair's side and from the boardwalk's
    hedge(x0, x1, z0, z0 + t)
    hedge(x0, cx - 2.0, z1 - t, z1)
    hedge(cx + 2.0, x1, z1 - t, z1)
    hedge(near, near + sgn * t, z0 + t, cz - 2.0)
    hedge(near, near + sgn * t, cz + 2.0, z1 - t)
    hedge(far - sgn * t, far, z0 + t, z1 - t)
    # the inner ring: in from the north
    ix0, ix1, iz0, iz1 = inner
    hedge(ix0, cx - 2.0, iz0, iz0 + t)
    hedge(cx + 2.0, ix1, iz0, iz0 + t)
    hedge(ix0, ix1, iz1 - t, iz1)
    hedge(ix0, ix0 + t, iz0 + t, iz1 - t)
    hedge(ix1 - t, ix1, iz0 + t, iz1 - t)
    # across the outer path on the north: that way is a dead end
    bx = cx - sgn * 5.0
    hedge(bx - 0.6, bx + 0.6, z0 + t, iz0)
    # the fountain at the heart
    b.cyl([cx, 0.5, cz], [6.0, 1.0, 6.0], STONE)
    b.cyl([cx, 0.92, cz], [5.2, 0.16, 5.2], "#4ab8d8", material="glass", alpha=0.7, collide=False)
    b.cyl([cx, 1.6, cz], [1.0, 1.2, 1.0], STONE)
    b.sphere([cx, 2.7, cz], [1.2, 1.4, 1.0], GOLD, material="metal", collide=False)
    b.rig("rr_fountain", cx, 2.2, cz, h=3.0, n=6, r=1.6)
    isle.loot(cx, None, cz - 4.6, "gem", "the hedge maze")
    b.landmark(cx, cz, "the west hedge maze" if sgn < 0 else "the east hedge maze")


def _mound(isle: Isle, sgn: float) -> None:
    """A picnic mound: grass in three steps, a lantern tree on top with a
    bench under it."""
    b = isle.b
    x, z = sgn * MOUND[0], MOUND[1]
    for k, (w, top) in enumerate(((16.0, 0.8), (11.0, 1.6), (6.0, 2.4))):
        b.box([x, top / 2.0, z], [w, top, w], ("#5aa04a", "#64aa50", "#6ab456")[k])
    b.cyl([x, 2.4 + 3.5, z], [0.8, 7.0, 0.8], "#5a3a2a")
    b.sphere([x, 2.4 + 8.6, z], [6.4, 4.2, 6.4], "#3a8a44", collide=False)
    for k in range(5):
        a = k * math.tau / 5.0
        b.box([x + math.cos(a) * 2.0, 2.4 + 6.4, z + math.sin(a) * 2.0], [0.06, 0.9, 0.06], "#4a3a2a", collide=False)
        b.sphere([x + math.cos(a) * 2.0, 2.4 + 5.8, z + math.sin(a) * 2.0], [0.6, 0.6, 0.6],
                 (RED, GOLD, PINK, TEAL, BULB)[k], material="neon", collide=False)
    b.box([x - sgn * 2.2, 2.4 + 0.45, z + 1.2], [0.9, 0.9, 2.6], DECK)
    isle.loot(x + sgn * 1.6, 2.4, z - 1.6, "any", "the picnic mound")


def _bandstand(isle: Isle) -> None:
    """The bandstand on the lawn south of the big top: a white platform
    under a red and white roof, bulbs round its eaves, the pirate band on
    it -- drum, fiddle, squeezebox and horn -- and the notes rising."""
    b = isle.b
    x, z = BANDSTAND
    b.box([x, 0.6, z], [12.0, 1.2, 12.0], WHITE)
    b.box([x, 1.25, z], [11.4, 0.1, 11.4], "#c8302a", collide=False)
    flight(b, "z", z + 8.0, z + 6.0, x - 3.0, x + 3.0, 0.0, 1.2, WHITE, rise=0.6)
    for ex in (-5.4, 5.4):
        for ez in (-5.4, 5.4):
            b.cyl([x + ex, 1.2 + 3.2, z + ez], [0.5, 6.4, 0.5], GOLD, material="metal")
    b.box([x, 7.8, z], [13.0, 0.4, 13.0], RED)
    b.cone([x, 8.0 + 1.5, z], [12.0, 3.0, 12.0], WHITE, collide=False)
    b.sphere([x, 11.3, z], [0.8, 0.8, 0.8], GOLD, material="metal", collide=False)
    for k in range(20):
        u = (k + 0.5) / 5.0
        side, f = divmod(k, 5)
        f = (f + 0.5) / 5.0 * 13.0 - 6.5
        bx, bz = ((f, -6.6), (6.6, f), (-f, 6.6), (-6.6, -f))[side]
        b.sphere([x + bx, 7.45, z + bz], [0.36, 0.36, 0.36], BULB, material="neon", collide=False)
    # the band
    for k, (bx, bz, instrument) in enumerate(((-2.6, -2.2, "drum"), (2.6, -2.2, "fiddle"), (-2.6, 2.0, "squeeze"),
                                               (2.6, 2.0, "horn"))):
        px, pz = x + bx, z + bz
        y = 1.3
        b.box([px, y + 1.0, pz], [1.2, 2.0, 0.9], "#0d69ac")
        b.box([px, y + 2.9, pz], [1.6, 1.8, 1.0], (RED, "#c4281c", "#2a6ab8", RED)[k])
        b.box([px, y + 4.2, pz], [1.0, 0.9, 0.9], "#f5cd30")
        b.box([px, y + 4.85, pz], [1.4, 0.4, 1.3], "#1a1a22")
        if instrument == "drum":
            b.cyl([px, y + 2.2, pz + 1.2], [1.6, 1.2, 1.6], "#e8e0d0")
        elif instrument == "fiddle":
            b.box([px + 0.6, y + 3.3, pz + 0.75], [0.4, 0.9, 0.5], "#8a4a1a")
        elif instrument == "squeeze":
            b.box([px, y + 2.8, pz + 0.75], [1.4, 0.8, 0.5], "#c8302a")
        else:
            b.cone([px, y + 3.4, pz + 0.95], [0.9, 0.9, 0.9], GOLD, material="metal", collide=False)
    b.rig("pb_notes", x, 6.0, z, n=9, seed=3.0)
    isle.loot(x, 1.2, z + 4.2, "any", "the bandstand")
    b.landmark(x, z, "the bandstand")


def _arch(isle: Isle) -> None:
    """The fair's arch over the foot of the midway: striped pillars, the
    beam across with bulbs along it, the skull and crossbones on top."""
    b = isle.b
    z = -26.0
    for x in (-8.6, 8.6):
        for k in range(3):
            b.box([x, 1.5 + k * 3.0, z], [1.4, 3.0, 1.4], (RED, WHITE, RED)[k])
        b.sphere([x, 9.7, z], [1.4, 1.4, 1.4], GOLD, material="metal", collide=False)
    b.box([0.0, 10.4 + 0.7, z], [16.4, 1.4, 1.2], "#1a1a22")
    for k in range(12):
        b.sphere([-7.2 + k * 14.4 / 11.0, 10.4 + 0.7, z + 0.75], [0.4, 0.4, 0.4], BULB, material="neon", collide=False)
    b.sphere([0.0, 13.3, z], [3.0, 3.0, 0.8], WHITE, collide=False)
    for e in (-0.6, 0.6):
        b.sphere([e, 13.5, z + 0.36], [0.9, 1.0, 0.2], "#1a1a22", collide=False)
        b.box([0.0, 11.9, z - 0.1], [5.0, 0.6, 0.4], WHITE, collide=False, r=[0.0, 0.0, e])


def _topiary(isle: Isle, sgn: float) -> None:
    """A topiary elephant in a flower bed, clipped out of the hedge."""
    b = isle.b
    x, z = sgn * TOPIARY[0], TOPIARY[1]
    b.box([x, 0.3, z], [12.0, 0.6, 14.0], "#7a5a3a")
    b.box([x, 0.65, z], [11.4, 0.1, 13.4], "#4a3a2a", collide=False)
    for k in range(10):
        a = k * math.tau / 10.0
        b.sphere([x + math.cos(a) * 5.0, 0.95, z + math.sin(a) * 6.0], [0.9, 0.6, 0.9],
                 (RED, GOLD, PINK, WHITE, PURPLE)[k % 5], collide=False)
    for ex in (-1.8, 1.8):
        for ez in (-2.6, 2.6):
            b.cyl([x + ex, 0.6 + 1.4, z + ez], [1.6, 2.8, 1.6], HEDGE)
    b.sphere([x, 0.6 + 4.6, z], [7.0, 5.2, 9.0], HEDGE)
    b.sphere([x, 0.6 + 6.4, z + sgn * 0.0 + 4.8], [4.0, 4.0, 4.0], "#358a40")
    for e in (-1.0, 1.0):
        b.sphere([x + e * 2.1, 0.6 + 6.6, z + 4.4], [0.6, 3.2, 2.8], "#2a6a34", collide=False)
    for k in range(3):
        b.sphere([x, 0.6 + 5.6 - k * 1.3, z + 6.9 + k * 0.3], [1.1, 1.3, 1.1], "#358a40", collide=False)
    b.sphere([x, 0.6 + 4.2, z - 4.8], [0.6, 0.6, 0.8], "#2a6a34", collide=False)


# ========================================================== the boardwalk
def _boardwalk(isle: Isle) -> None:
    """The boardwalk along the beach: a stone sea wall with planks on top,
    flights up from the fair and down to the sand, a rail along its edge,
    lamp posts with strings of lights between them, the stalls and the
    high strikers; the pier out into the bay to the fireworks barge."""
    b = isle.b
    x0, x1, z0, z1 = BOARD
    b.box([0.0, 0.6, (z0 + z1) / 2.0], [x1 - x0 - 0.4, 1.2, z1 - z0 - 0.4], STONE)
    b.box([0.0, BOARD_Y - 0.2, (z0 + z1) / 2.0], [x1 - x0, 0.4, z1 - z0], DECK)
    for fx in FLIGHTS_X:
        flight(b, "z", z0 - 4.0, z0, fx - 4.0, fx + 4.0, 0.0, BOARD_Y, DECK, rise=0.8)
        if abs(fx) > 1.0:
            flight(b, "z", z1 + 4.0, z1, fx - 4.0, fx + 4.0, 0.1, BOARD_Y, DECK, rise=0.8)
    # the rail along the sea side, broken at the flights and the pier
    gaps = sorted([(fx - 4.0, fx + 4.0) for fx in FLIGHTS_X if abs(fx) > 1.0] + [(PIER[0], PIER[1])])
    edges = [x0] + [v for g in gaps for v in g] + [x1]
    for k in range(0, len(edges), 2):
        xa, xb = edges[k], edges[k + 1]
        if xb - xa < 1.0:
            continue
        b.box([(xa + xb) / 2.0, BOARD_Y + 1.05, z1 - 0.3], [xb - xa, 0.2, 0.2], WHITE)
        for k2 in range(int((xb - xa) // 4.0) + 1):
            px = min(xb - 0.2, xa + 0.2 + k2 * 4.0)
            b.box([px, BOARD_Y + 0.5, z1 - 0.3], [0.3, 1.0, 0.3], WHITE)
    # lamp posts, the lights strung between them
    lamps = [-96.0, -72.0, -50.0, -28.0, -8.0, 8.0, 28.0, 50.0, 72.0, 96.0]
    for lx in lamps:
        b.cyl([lx, BOARD_Y + 3.0, z0 + 0.6], [0.4, 6.0, 0.4], "#2a2a32", material="metal")
        b.sphere([lx, BOARD_Y + 6.4, z0 + 0.6], [1.1, 1.1, 1.1], BULB, material="neon")
    for k in range(len(lamps) - 1):
        b.rig("rr_lights", lamps[k], BOARD_Y + 5.9, z0 + 0.6, q=(lamps[k + 1], BOARD_Y + 5.9, z0 + 0.6), n=14, sag=1.4)
    # the pier and its end, out over the beach and into the bay
    px0, px1, pz0, pz1 = PIER
    b.box([0.0, 0.6, (z1 + SOUTH) / 2.0], [px1 - px0 - 0.4, 1.2, SOUTH - z1], STONE)
    b.box([0.0, BOARD_Y - 0.2, (pz0 + pz1) / 2.0], [px1 - px0, 0.4, pz1 - pz0], DECK)
    b.box([0.0, BOARD_Y - 0.2, pz1 + 3.0], [16.0, 0.4, 6.0], DECK)
    for z in (94.0, 97.4):
        for xx in (px0 + 0.5, px1 - 0.5):
            b.cyl([xx, (SEABED + BOARD_Y - 0.4) / 2.0, z], [0.8, BOARD_Y - 0.4 - SEABED, 0.8], TIMBER)
    for xx in (-7.4, 7.4):
        b.cyl([xx, (SEABED + BOARD_Y - 0.4) / 2.0, pz1 + 5.4], [0.8, BOARD_Y - 0.4 - SEABED, 0.8], TIMBER)
        b.cyl([xx, BOARD_Y + 2.0, pz1 + 5.4], [0.4, 4.0, 0.4], TIMBER)
        b.sphere([xx, BOARD_Y + 4.5, pz1 + 5.4], [1.0, 1.0, 1.0], BULB, material="neon")
    isle.loot(0.0, BOARD_Y, pz1 + 3.0, "any", "the end of the pier")
    b.landmark(0.0, (z0 + z1) / 2.0, "the boardwalk")
    b.landmark(0.0, pz1, "the pier")


def _stall(isle: Isle, x: float, kind: str) -> None:
    """A stall on the boardwalk: a counter under a striped canopy on four
    posts, the goods on it -- candy floss, grog, roast chestnuts."""
    b = isle.b
    z0 = BOARD[2]
    y = BOARD_Y
    cz = z0 + 2.4
    b.box([x, y + 0.6, cz], [6.0, 1.2, 1.8], (PINK if kind == "floss" else "#8a5a3a"))
    for ex in (-2.8, 2.8):
        for ez in (-0.7, 2.0):
            b.cyl([x + ex, y + 3.7, cz + ez], [0.3, 7.4, 0.3], WHITE)
    for k in range(6):
        b.box([x - 2.5 + k * 1.0, y + 7.55, cz + 0.65], [1.0, 0.3, 3.4],
              ((PINK if kind == "floss" else RED), WHITE)[k % 2])
    if kind == "floss":
        for k in range(3):
            b.sphere([x - 1.8 + k * 1.8, y + 1.75, cz], [1.0, 1.1, 1.0], ("#ffb8e8", "#bfe8ff", "#ffb8e8")[k],
                     collide=False)
    elif kind == "grog":
        for k in range(3):
            b.cyl([x - 1.8 + k * 1.8, y + 1.8, cz], [1.0, 1.2, 1.0], "#7a4a28")
            b.cyl([x - 1.8 + k * 1.8, y + 1.8, cz], [1.06, 0.16, 1.06], "#3a3a42", material="metal", collide=False)
    else:
        b.cyl([x, y + 1.5, cz], [1.6, 0.6, 1.6], "#3a3a42", material="metal")
        b.rig("rr_smoke", x, y + 1.9, cz, wind=[0.4, 0.5], rate=0.3, h=7.0, size=0.8, colour="#c8c0b8")
    isle.loot(x + 2.0, y + 1.2, cz, "any", {"floss": "the candy floss stall", "grog": "the grog stand",
                                            "chestnuts": "the chestnut stall"}[kind])


def _striker(isle: Isle, x: float) -> None:
    b = isle.b
    z = BOARD[2] + 5.0
    y = BOARD_Y
    b.box([x, y + 0.2, z], [2.4, 0.4, 2.4], RED)
    b.box([x, y + 4.4, z - 0.6], [0.7, 8.4, 0.4], WHITE)
    for k in range(6):
        b.box([x, y + 1.4 + k * 1.2, z - 0.83], [0.8, 0.5, 0.06], (GOLD, RED, TEAL)[k % 3], collide=False)
    b.box([x, y + 8.75, z - 0.6], [1.0, 0.3, 0.6], GOLD, material="metal")
    b.rig("pb_striker", x, y + 0.4, z - 0.6, yaw=math.pi, h=8.4, every=4.2, seed=x * 0.1)


# ============================================================== the barge
def _barge(isle: Isle) -> None:
    """The fireworks barge moored in the bay: mortar racks and crates of
    rockets on its deck, the pyrotechnician's shed, signal flags."""
    b = isle.b
    x, z = BARGE
    b.box([x, -0.3, z], [24.0, 3.0, 10.0], "#5a4a3e")
    b.box([x, 1.25, z], [23.6, 0.1, 9.6], PLANK, collide=False)
    for k, mx in enumerate((-7.0, 0.0, 7.0)):
        b.box([x + mx, 1.2 + 0.6, z - 1.4], [4.0, 1.2, 2.6], "#3a3a42", material="metal")
        for j in range(4):
            b.cyl([x + mx - 1.5 + j * 1.0, 2.4 + 0.9, z - 1.4], [0.6, 1.8, 0.6],
                  ("#c8302a", "#3a6ac8", GOLD, "#3ac85a")[j], collide=False)
    for k in range(3):
        b.box([x - 9.6 + k * 1.3, 1.7, z + 3.0], [1.2, 1.0, 1.2], ("#c8302a", GOLD, "#c8302a")[k])
    for k in range(2):
        b.box([x - 8.95 + k * 1.3, 2.7, z + 3.0], [1.2, 1.0, 1.2], (GOLD, "#c8302a")[k])
    b.box([x + 8.0, 1.2 + 1.6, z + 2.6], [3.6, 3.2, 3.0], "#8a6a4a")
    b.box([x + 8.0, 4.55, z + 2.6], [4.0, 0.3, 3.4], RED)
    b.cyl([x - 10.5, 1.2 + 4.0, z], [0.3, 8.0, 0.3], TIMBER, collide=False)
    b.rig("rr_flag", x - 10.35, 8.8, z, yaw=0.0, w=3.0, h=1.8, colours=[RED, GOLD, "#3a6ac8"])
    b.landmark(x, z, "the fireworks barge")


# ============================================================== one wing
def _half(isle: Isle, sgn: float) -> None:
    b = isle.b
    rng = isle.rng

    def X(x: float) -> float:
        return sgn * x

    _helter(isle, sgn)
    _mirrors(isle, sgn)
    _carousel(isle, sgn)
    _swing(isle, sgn)
    _fortune(isle, sgn)
    _maze(isle, sgn)
    _mound(isle, sgn)
    _topiary(isle, sgn)
    _stall(isle, X(20.0), "floss")
    _stall(isle, X(60.0), "chestnuts" if sgn > 0 else "grog")
    _striker(isle, X(32.0))
    # palms, parasols and a sandcastle on the beach; flags; lamps
    for x, z in ((106.0, -90.0), (106.0, -40.0), (106.0, 40.0), (104.0, 80.0), (90.0, 86.0), (50.0, 88.0),
                 (24.0, 86.0), (94.0, -70.0), (40.0, -70.0), (96.0, 54.0)):
        px, pz = X(x + rng.uniform(-1.0, 1.0)), z + rng.uniform(-1.0, 1.0)
        if isle.clear(px, pz, 2.0):
            isle.palm(px, pz, h=rng.uniform(11.0, 15.0))
    for k, (x, z) in enumerate(((36.0, 80.0), (64.0, 82.0), (82.0, 78.0))):
        y = isle.top(X(x), z)
        b.cyl([X(x), y + 3.2, z], [0.2, 6.4, 0.2], WHITE)
        b.cone([X(x), y + 6.9, z], [4.6, 1.4, 4.6], (RED, TEAL, GOLD)[k], collide=False)
        b.box([X(x) + 1.6, y + 0.3, z + 1.2], [1.2, 0.6, 2.6], (WHITE, PINK, "#7af0ff")[k])
    cx, cz = X(56.0), 76.5
    y = isle.top(cx, cz)
    b.box([cx, y + 0.5, cz], [3.0, 1.0, 3.0], "#e8d098")
    b.box([cx, y + 1.4, cz], [1.8, 0.8, 1.8], "#e8d098")
    for ex in (-1.3, 1.3):
        for ez in (-1.3, 1.3):
            b.cyl([cx + ex, y + 1.3, cz + ez], [0.7, 0.6, 0.7], "#e8d098", collide=False)
    b.box([cx, y + 2.15, cz], [0.06, 0.7, 0.06], "#4a3a2a", collide=False)
    isle.flag(X(108.0), 0.0, None, RED if sgn < 0 else "#2a6ab8", h=11.0)
    for x, z in ((40.0, -24.0), (40.0, 22.0), (96.0, -24.0), (96.0, 22.0), (60.0, -60.0)):
        y = isle.top(X(x), z)
        b.cyl([X(x), y + 2.8, z], [0.4, 5.6, 0.4], "#2a2a32", material="metal")
        b.sphere([X(x), y + 6.0, z], [1.1, 1.1, 1.1], (BULB, PINK, "#7af0ff")[int(x) % 3], material="neon")
    # X's and loot about the wing
    isle.dig(X(30.0), None, 84.0, "the beach")
    isle.dig(X(76.0), None, 86.0, "the far beach")
    isle.dig(X(106.0), None, -70.0, "the shore")
    isle.dig(X(58.0), None, -58.0, "behind the carousel")
    isle.dig(X(51.0), None, 29.4, "the maze's dead end")
    isle.dig(X(24.0), TER_Y + 0.1, -100.0, "the Ferris wheel's terrace")
    isle.loot(X(104.0), None, -16.0, "any", "the shore")
    isle.loot(X(88.0), None, 82.0, "any", "the beach")


def _rain(isle: Isle) -> None:
    """Where the barge's rockets come down and the prize gold lands: open
    ground all over the fair (both halves alike)."""
    b = isle.b
    spots = [(30.0, -4.0), (30.0, 28.0), (50.0, -48.0), (92.0, -66.0), (88.0, -32.0), (54.0, -8.0),
             (100.0, 4.0), (96.0, 40.0), (40.0, 46.0), (60.0, 67.0), (20.0, 67.0), (40.0, 82.0),
             (86.0, 82.0), (22.0, -74.0), (22.0, -98.0), (66.0, 10.0)]
    for x, z in spots:
        for sgn in (-1.0, 1.0):
            px = sgn * x
            b.mark("rain", px, b.surface(px, z, 4.0), z)
    for x, z in ((0.0, -46.0), (0.0, -31.0), (0.0, 30.0), (0.0, 52.0), (0.0, 84.0)):
        b.mark("rain", x, b.surface(x, z, 4.0), z)


# ================================================================ meta
def _meta(isle: Isle) -> None:
    b = isle.b
    for x, z, name in ((0.0, -40.0, "the midway"), (0.0, -112.0, "the roller coaster"),
                       (-SHIP_X, 0.0, "the Scarlet Queen"), (SHIP_X, 0.0, "the Blue Marlin")):
        b.landmark(x, z, name)
    b.camera(0.0, 48.0, 118.0, 0.0, 10.0, -16.0)
    b.camera(-112.0, 34.0, 60.0, -10.0, 8.0, -24.0)
    b.camera(56.0, 26.0, -46.0, 0.0, 22.0, -90.0)
    b.camera(-30.0, 9.0, 30.0, 0.0, 7.0, 0.0)
    b.extra.update({"twist": "eruption", "water": SEA_TOP, "eruption_every": [52.0, 70.0], "eruption_for": 26.0,
                    "warn": 6.0, "vent": [BARGE[0], 3.0, BARGE[1]], "style": {"bomb": "rocket"},
                    "twist_line": "the fireworks barge is going up",
                    "twist_text": {"warn": "THE FIREWORKS BARGE IS LIT!",
                                   "warnSub": "Somebody has put a torch to the powder...",
                                   "on": "FIREWORKS!",
                                   "onSub": "Rockets are raining on the fair -- and the prize gold with them",
                                   "off": "The barge has burnt itself out", "chip": "FIREWORKS"}})
    b.rig("pb_firework", -70.0, 0.0, 150.0, every=6.4, h=70.0, seed=1.0)
    b.rig("pb_firework", 70.0, 0.0, 150.0, every=7.9, h=60.0, seed=4.0)
    b.rig("pb_skylanterns", 0.0, 2.0, 82.0, n=10, h=150.0, r=12.0, life=28.0, seed=2.0, wind=[0.3, -0.8])
    b.rig("pb_lanterns", 0.0, SEA_TOP, 104.0, n=10, w=180.0, d=12.0, seed=5.0)
    for sgn in (-1.0, 1.0):
        b.rig("rr_swan", sgn * 30.0, SEA_TOP, 104.0, r=5.0, seed=sgn * 2.0)
        b.rig("rr_swan", sgn * 48.0, SEA_TOP, 108.0, r=4.0, seed=sgn * 5.0)
        b.rig("pb_parrots", sgn * 80.0, 24.0, 40.0, r=14.0, n=4, seed=sgn * 3.0)
        b.rig("rr_surf", sgn * (SHORE_X + 6.5), SEA_TOP + 0.3, -40.0, w=80.0, yaw=sgn * math.pi / 2.0)
        b.rig("rr_surf", sgn * (SHORE_X + 6.5), SEA_TOP + 0.3, 60.0, w=50.0, yaw=sgn * math.pi / 2.0)
    b.rig("rr_surf", 0.0, SEA_TOP + 0.3, SOUTH + 6.5, w=2 * SHORE_X - 10.0, yaw=0.0)
    b.rig("pb_dolphins", 0.0, SEA_TOP, 140.0, r=30.0, n=3, seed=2.0)
    b.rig("rr_gulls", 0.0, 40.0, 80.0, r=40.0, n=5, seed=6)


def build(b: ArenaArea) -> None:
    rng = random.Random(0x7011)
    isle = Isle(b, rng)
    _land(isle)
    _edges(isle)
    _coaster(isle)
    _jollyroger(isle)
    _terrace(isle)
    _bigtop(isle)
    _midway(isle)
    _bandstand(isle)
    _arch(isle)
    _half(isle, -1.0)
    _half(isle, 1.0)
    _boardwalk(isle)
    _barge(isle)
    _rain(isle)
    galleon(isle, "red", 0.0)
    galleon(isle, "blue", 0.0)
    _meta(isle)
