"""Monsoon Bazaar: a trading port on a river delta in the monsoon -- warm
rain falling on saffron and magenta awnings, canals crossed by humped
bridges, paper lanterns lit at noon, the smell of spice.  At the head of
the avenue the Company's customs house, white, with its clock tower and
its marines; at the foot of it the grand bazaar, a hall of columns under
a tiered roof with the idol on a dais in the middle, bunting strung round
its eaves; across the canal the fish market under a pagoda lighthouse, and
on either beach a fishing pier where a great cantilevered net dips into
the sea; on either wing the dyers' yards, silk drying on the lines, the
spice godowns, a white stupa hung with prayer flags, and a tea garden up
on its terrace -- a pavilion, a koi pond, a blossom tree shedding.  Off
the cliffs behind the town the monsoon torrents fall into the heads of
the side canals; puddles on every street, rain rings on the water, and a
rainbow over the cliffs when the sun breaks through.

Layout (north is -z; the Scarlet Corsairs' ship off the west shore, the
Azure Buccaneers' off the east)::

    z -120  ======== cliffs ==== falls ===== THE CUSTOMS HOUSE ===== falls ==== cliffs ========
    z  -88   the godown    |canal| stupa  shophouses || avenue || shophouses  stupa |canal|  the godown
    z  -46   dyers' yard   |canal|         the north street               |canal|   dyers' yard
   SCARLET   tea garden    ==br==     ( THE GRAND BAZAAR, the idol )      ==br==   tea garden  BLUE
    QUEEN    the boatyard  |canal|         the south street               |canal|  the boatyard MARLIN
    z   38   ~~~~~~~~~~~~~~ the great canal ~~~~ bridge ~~~~ the great canal ~~~~~~~~~~~~~~
    z   70   houses         the fish market    THE PAGODA     the fish market        houses
    z  100  ~~~~~~~ pier, net ~~~~~~~~~~~~~ the south sea ~~~~~~~~~~~~~ pier, net ~~~~~~~

The halves are mirror images.

The twist is the redcoats -- here the Company's marines (``extra["twist"]
= "redcoats"``, reworded by ``extra["twist_text"]``): the customs house's
gong sounds and the marines march out of its courtyard (``barracks``) to
walk their beats (``patrol`` marks, by ``route``) -- round the bazaar's
streets and over the bridge to the fish market -- firing at any pirate
they see, carriers first.  A marine cut down drops his purse.
"""
from __future__ import annotations

import math
import random

from ..calamity_coast.town import skirt
from ..kit import ArenaArea, backdrop, building, flight, gable, rect, slab
from .common import IRON, PLANK, SAND, SAND_WET, SEA_TOP, SEABED, SHIP_X, SHORE_X, TIMBER, Isle, galleon

HALF = (170.0, 120.0)
SKY = {"top": "#5a6a80", "horizon": "#c8ccc0", "sun": [0.3, 0.6, 0.4], "clouds": 0.9, "tint": "#f0ece0"}
AMBIENT = "#b8bab0"
GROUND = "#6a8a4a"
FOG = 640.0

TURF = "#5a8a44"
STREET = "#a89a88"
STREET_WET = "#8a8070"
WHITE = "#f0e8d8"
TILE = "#c84a3a"
SAFFRON = "#f0a830"
MAGENTA = "#d83a8a"
TEAL = "#2aa8a0"
INDIGO = "#3a4aa8"
LIME = "#8ac83a"
LANTERN = "#ffb05a"
CANAL_C = "#3a7a6a"
SOUTH = 100.0
NORTH = -104.0               # the foot of the cliffs behind the town
CANAL_EW = (-SHORE_X, SHORE_X, 34.0, 42.0)
CANAL_NS = (44.0, 52.0, NORTH, 34.0)  # east; mirrored -- the falls pour into its head
CANAL_FLOOR = SEABED
CUSTOMS = (-30.0, 30.0, -104.0, -72.0)
HALL = (-26.0, 26.0, -20.0, 20.0)
HALL_Y = 0.6
ROOF_Y = 10.0
NS_BRIDGES = (-50.0, -15.0, 15.0)      # the bridges over the side canals (z)
EW_BRIDGES = (0.0, 78.0)               # over the great canal (x; the second mirrored)
SHOPS = (((10.0, 22.0, -50.0, -36.0), "z+", SAFFRON, TEAL), ((24.0, 38.0, -50.0, -36.0), "z+", MAGENTA, SAFFRON),
         ((8.0, 20.0, -68.0, -54.0), "x-", TEAL, MAGENTA), ((60.0, 74.0, 52.0, 64.0), "z-", LIME, INDIGO),
         ((80.0, 94.0, 52.0, 64.0), "z-", INDIGO, SAFFRON), ((86.0, 100.0, -60.0, -48.0), "x-", WHITE, MAGENTA),
         ((62.0, 78.0, -8.0, 8.0), "x-", SAFFRON, TEAL))
GODOWN = (60.0, 96.0, -100.0, -76.0)
MARKET = (14.0, 32.0, 54.0, 64.0)
PAGODA = (0.0, 70.0)
TEA = (84.0, 104.0, -10.0, 10.0)       # the tea garden's terrace (east; mirrored)
TEA_Y = 1.6
STUPA = (31.0, -63.0)
PIER = (64.0, 70.0)                     # the fishing pier's deck (x; mirrored)
PIER_Y = 1.6
PUDDLES = ((0.0, -60.0, 3.0, 2.2), (-2.0, -44.0, 2.4, 1.6), (20.0, -28.0, 3.6, 2.0), (-26.0, -30.0, 2.6, 2.0),
           (-36.0, 8.0, 2.0, 3.0), (36.0, -10.0, 2.2, 2.6), (14.0, 28.0, 3.0, 1.8), (-18.0, 50.0, 2.6, 1.6),
           (24.0, 49.0, 3.2, 2.0), (37.0, 70.0, 1.8, 2.8), (-10.0, 84.0, 3.0, 1.8), (-37.0, 62.0, 1.8, 2.2))


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
    canals = [CANAL_EW, CANAL_NS, _m(CANAL_NS)]
    isle.land(TURF, holes=[west, east, south] + canals, soil="#5a4a38")
    for area in (west, east, south):
        slab(b, area, SEABED, 3.0, SAND_WET, studs=True)
    for area in canals:
        slab(b, area, CANAL_FLOOR, 3.0, "#4a5a48", studs=True)
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
        isle.water(area, SEABED, colour="#3a7a8a", alpha=0.6)
    for area in canals:
        isle.water(area, CANAL_FLOOR, colour=CANAL_C, alpha=0.62)
    for x0, x1, z0, z1 in ((-hx - m - 300.0, -hx - m, -hz - m - 300.0, hz + m + 300.0),
                           (hx + m, hx + m + 300.0, -hz - m - 300.0, hz + m + 300.0),
                           (-hx - m, hx + m, hz + m, hz + m + 300.0)):
        b.box([(x0 + x1) / 2.0, (SEABED - 6.0 + SEA_TOP) / 2.0, (z0 + z1) / 2.0],
              [x1 - x0, SEA_TOP - SEABED + 6.0, z1 - z0], "#2a6a7a", material="glass", alpha=0.6, collide=False)
    # the canals' stone lips (broken where the bridges cross and where one
    # canal runs into another), and the ghats: steps down to the water
    ew_gaps = [(-SHORE_X, -81.0), (-75.0, -52.0), (-44.0, -5.0), (5.0, 44.0), (52.0, 75.0), (81.0, SHORE_X)]
    for xa, xb in ew_gaps:
        for zz in (CANAL_EW[2] - 0.4, CANAL_EW[3] + 0.4):
            b.box([(xa + xb) / 2.0, 0.25, zz], [xb - xa, 0.5, 0.8], "#8a8478")
    for sgn in (-1.0, 1.0):
        x0, x1 = sorted((sgn * CANAL_NS[0], sgn * CANAL_NS[1]))
        for xx in (x0 - 0.4, x1 + 0.4):
            for za, zb in ((NORTH, -53.0), (-47.0, -18.0), (-12.0, 12.0), (18.0, CANAL_EW[2] - 0.8)):
                b.box([xx, 0.25, (za + zb) / 2.0], [0.8, 0.5, zb - za], "#8a8478")
        # a ghat on each side canal's outer bank, and two on the great canal
        flight(b, "x", sgn * CANAL_NS[1], sgn * (CANAL_NS[1] - 3.6), -36.0, -28.0, 0.0, CANAL_FLOOR + 0.4,
               "#a89a88", fill=CANAL_FLOOR)
        xa, xb = sorted((sgn * 58.0, sgn * 66.0))
        flight(b, "z", CANAL_EW[2], CANAL_EW[2] + 3.6, xa, xb, 0.0, CANAL_FLOOR + 0.4, "#a89a88", fill=CANAL_FLOOR)
        xa, xb = sorted((sgn * 20.0, sgn * 28.0))
        flight(b, "z", CANAL_EW[3], CANAL_EW[3] - 3.6, xa, xb, 0.0, CANAL_FLOOR + 0.4, "#a89a88", fill=CANAL_FLOOR)
    # the ground covers: streets kept clear of the buildings and bridges
    s = isle.s
    keep = [CUSTOMS, HALL, (-6.0, 6.0, 28.0, 48.0)]
    for r, _d, _c, _a in SHOPS:
        keep += [r, _m(r)]
    for r in (GODOWN, MARKET, (78.0 - 4.0, 78.0 + 4.0, 28.0, 48.0), (38.0, 58.0, -53.5, -46.5),
              (38.0, 58.0, -18.5, -11.5), (38.0, 58.0, 11.5, 18.5), (58.0, 100.0, -44.0, -28.0),
              (60.0, 96.0, 18.0, 30.0), (56.0, 60.0, -38.0, -26.0)):
        keep += [r, _m(r)]
    keep += [(PAGODA[0] - 8.0, PAGODA[0] + 8.0, PAGODA[1] - 8.0, PAGODA[1] + 8.0)]
    for r in keep:
        s.reserve(r)
    # the avenue, the streets round the bazaar, the harbour streets
    for r in ((-5.0, 5.0, -72.0, -34.0), (-42.0, 42.0, -34.0, -22.0), (-42.0, -30.0, -22.0, 22.0),
              (30.0, 42.0, -22.0, 22.0), (-42.0, 42.0, 22.0, 33.2), (-40.0, 40.0, 46.0, 54.0),
              (-40.0, -34.0, 54.0, 88.0), (34.0, 40.0, 54.0, 88.0), (-40.0, 40.0, 80.0, 88.0)):
        s.lay(rect(*r), 0.12, STREET)
    for sgn in (-1.0, 1.0):
        def X(x: float, sgn: float = sgn) -> float:
            return sgn * x
        isle.trail([(X(109.5), -15.0), (X(57.5), -15.0)], colour=STREET_WET)
        isle.trail([(X(109.5), 15.0), (X(57.5), 15.0)], colour=STREET_WET)
    for x0, x1, z0, z1 in ((-SHORE_X, -102.0, NORTH, SOUTH), (102.0, SHORE_X, NORTH, SOUTH),
                           (-102.0, 102.0, 90.0, SOUTH)):
        s.lay(rect(x0, x1, z0, z1), 0.1, SAND)


# =============================================================== the edges
def _edges(isle: Isle) -> None:
    b = isle.b
    hx, hz = HALF
    rng = isle.rng
    m = b.margin
    rocks = ("#7a6a5a", "#6a5a4a", "#8a7a68", "#5a4c40")
    isle.cliffs("x", -SHORE_X, SHORE_X, -hz - m, NORTH, rng.uniform(22.0, 26.0), rocks, green="#4a8a3a",
                recess=0.0, step=14.0)
    for sgn in (-1.0, 1.0):
        a0, a1 = sorted((sgn * SHORE_X, sgn * (hx + m)))
        isle.cliffs("x", a0, a1, -hz - m, NORTH, 32.0, rocks, base=SEABED, green="#4a8a3a", step=14.5,
                    recess=0.0)
        b.box([sgn * (hx + m / 2.0), (SEABED + 6.0) / 2.0, (NORTH + hz + m) / 2.0],
              [m, 6.0 - SEABED, hz + m - NORTH], "#7a6a5a")
    b.box([0.0, (SEABED + 6.0) / 2.0, hz + m / 2.0], [2 * hx, 6.0 - SEABED, m], "#7a6a5a")
    for k in range(18):
        z = NORTH + (k + 0.5) * (hz + m - NORTH) / 18.0
        for sgn in (-1.0, 1.0):
            b.box([sgn * (hx + m / 2.0) + rng.uniform(-1.0, 1.0), 6.0 + 1.0 + (k % 3) * 0.4, z],
                  [m - 2.0 - (k % 2) * 0.6, 2.0 + (k % 3) * 0.8, (hz + m - NORTH) / 18.0 - 2.0],
                  (SAFFRON, MAGENTA, TEAL)[k % 3] if k % 4 == 0 else "#8a7a68")
    for k in range(18):
        x = -hx + (k + 0.5) * 2 * hx / 18.0
        b.box([x, 6.0 + 1.0 + (k % 3) * 0.4, hz + m / 2.0 + rng.uniform(-1.0, 1.0)],
              [2 * hx / 18.0 - 2.0, 2.0 + (k % 3) * 0.8, m - 2.0 - (k % 2) * 0.6],
              (TEAL, SAFFRON, MAGENTA)[k % 3] if k % 4 == 1 else "#8a7a68")
    skirt(b, hx, hz, "#4a5a48", top=SEABED - 3.05)
    backdrop(b, "hills", 12.0, rng, sides=("z-",), colours=["#3a6a3a", "#4a7a44", "#2e5a32"], depth=180.0)


# ============================================================ the bridges
def _hump(isle: Isle, axis: str, at: float, a: float, c: float, w: float) -> None:
    """A humped stone bridge over a canal: steps up off each bank to a crest
    over the water, a parapet down each side; ``axis`` is the way it runs,
    ``at`` its centre line across, ``a``..``c`` the water it spans."""
    b = isle.b
    tops = (0.5, 1.0, 1.5)
    run = 2.0

    def put(u0: float, u1: float, y0: float, y1: float, v0: float, v1: float, colour: str) -> None:
        if axis == "z":
            b.box([(v0 + v1) / 2.0, (y0 + y1) / 2.0, (u0 + u1) / 2.0], [v1 - v0, y1 - y0, u1 - u0], colour)
        else:
            b.box([(u0 + u1) / 2.0, (y0 + y1) / 2.0, (v0 + v1) / 2.0], [u1 - u0, y1 - y0, v1 - v0], colour)

    v0, v1 = at - w / 2.0, at + w / 2.0
    for k, top in enumerate(tops):
        put(a - run * (len(tops) - k), a - run * (len(tops) - k - 1), 0.0, top, v0, v1, "#b8aa94")
        put(c + run * (len(tops) - k - 1), c + run * (len(tops) - k), 0.0, top, v0, v1, "#b8aa94")
    put(a, c, 1.4, 2.0, v0, v1, "#c8baa4")
    put(a, c, CANAL_FLOOR, 1.4, v0 + 0.6, v0 + 1.6, "#9a8a78")
    put(a, c, CANAL_FLOOR, 1.4, v1 - 1.6, v1 - 0.6, "#9a8a78")
    for vv in (v0 + 0.25, v1 - 0.25):
        put(a - 0.5, c + 0.5, 2.0, 2.9, vv - 0.25, vv + 0.25, "#a8987e")


def _bridges(isle: Isle) -> None:
    for sgn in (-1.0, 1.0):
        x0, x1 = sorted((sgn * CANAL_NS[0], sgn * CANAL_NS[1]))
        for z in NS_BRIDGES:
            _hump(isle, "x", z, x0, x1, 6.0)
    _hump(isle, "z", 0.0, CANAL_EW[2], CANAL_EW[3], 10.0)
    for sgn in (-1.0, 1.0):
        _hump(isle, "z", sgn * EW_BRIDGES[1], CANAL_EW[2], CANAL_EW[3], 6.0)


# ========================================================= the customs house
def _customs(isle: Isle) -> None:
    """The Company's customs house: a walled compound, white, its gate on
    the avenue; the house across the back of the courtyard with an arcade
    and a dome, the treasury inside; the clock tower over the gate; the
    gong; the Company's flag.  The marines muster in the courtyard."""
    b = isle.b
    x0, x1, z0, z1 = CUSTOMS
    t = 2.0
    h = 6.0
    b.box([(x0 + x1) / 2.0, h / 2.0, z0 + t / 2.0], [x1 - x0, h, t], WHITE)
    for xa, xb in ((x0, -5.0), (5.0, x1)):
        b.box([(xa + xb) / 2.0, h / 2.0, z1 - t / 2.0], [xb - xa, h, t], WHITE)
    for xx in (x0 + t / 2.0, x1 - t / 2.0):
        b.box([xx, h / 2.0, (z0 + z1) / 2.0], [t, h, z1 - z0 - 2 * t], WHITE)
    for xx in range(int(x0) + 2, int(x1) - 1, 4):
        if -6 <= xx <= 6:
            continue
        b.box([float(xx), h + 0.5, z1 - t / 2.0], [1.6, 1.0, t], "#e0d8c8")
    slab(b, rect(x0 + t, x1 - t, z0 + t, z1 - t), 0.12, 0.12, "#c8bca8", studs=True)
    # the house: white, an arcade along its front, its roof and dome
    hx0, hx1, hz0, hz1 = -22.0, 22.0, z0 + t, -88.0
    building(b, rect(hx0, hx1, hz0, hz1), 0.12, 11.0, WHITE, t=1.0, roof_colour=TILE, roof_t=0.8,
             floor_colour="#b8a890", doors={"z+": [(-4.0, 4.0, 7.12)]}, lights=LANTERN, studs_roof=False)
    gable(b, rect(hx0, hx1, hz0, hz1), 0.12 + 11.8, TILE, "x", tiers=3, rise=1.2, overhang=0.8)
    b.sphere([0.0, 0.12 + 11.8 + 3.6 + 2.0, (hz0 + hz1) / 2.0], [8.0, 6.0, 8.0], "#e8e0d0")
    b.cone([0.0, 0.12 + 11.8 + 3.6 + 5.6, (hz0 + hz1) / 2.0], [1.2, 2.4, 1.2], "#c8a040", material="metal",
           collide=False)
    for x in (-18.0, -12.0, -6.0, 6.0, 12.0, 18.0):
        b.cyl([x, 0.12 + 3.4, hz1 + 2.4], [1.2, 6.8, 1.2], "#f4f0e4")
    b.box([0.0, 0.12 + 7.2, hz1 + 2.4], [40.0, 0.8, 3.6], WHITE)
    # the treasury inside: the Company's gold on the tables
    for k, x in enumerate((-12.0, 0.0, 12.0)):
        b.box([x, 0.52 + 0.6, -97.0], [6.0, 1.2, 3.0], "#7a5a3a")
        isle.loot(x, 0.52 + 1.2, -97.0, "bar" if k != 1 else "gem", "the customs house treasury")
    # the clock tower over the gate's east side, the clock on it telling the time
    tx0, tx1, tz0, tz1 = 7.0, 13.0, z1 - 6.5, z1 + 0.5
    b.box([(tx0 + tx1) / 2.0, 11.0, (tz0 + tz1) / 2.0], [tx1 - tx0, 22.0, tz1 - tz0], WHITE)
    b.box([(tx0 + tx1) / 2.0, 22.6, (tz0 + tz1) / 2.0], [tx1 - tx0 + 1.0, 1.2, tz1 - tz0 + 1.0], "#e0d8c8")
    b.cone([(tx0 + tx1) / 2.0, 25.2, (tz0 + tz1) / 2.0], [7.6, 4.0, 7.6], TILE)
    b.cyl([(tx0 + tx1) / 2.0, 18.0, tz1 + 0.06], [4.4, 0.12, 4.4], "#f8f4e8", collide=False,
          r=[math.pi / 2.0, 0.0, 0.0])
    b.rig("rr_clock", (tx0 + tx1) / 2.0, 18.0, tz1 + 0.15, r=2.0, yaw=0.0)
    # the gong in the courtyard, the flag over the gate
    gx, gz = -12.0, -80.0
    for e in (-1.6, 1.6):
        b.box([gx + e, 2.6, gz], [0.5, 5.2, 0.5], "#6a3a22")
    b.box([gx, 5.4, gz], [4.2, 0.5, 0.6], "#6a3a22")
    b.cyl([gx, 3.0, gz], [2.6, 0.3, 2.6], "#c8a040", material="metal", collide=False, r=[math.pi / 2.0, 0.0, 0.0])
    b.box([gx, 4.55, gz], [0.08, 1.2, 0.08], "#4a3a2a", collide=False)
    b.cyl([-10.0, 0.12 + 7.0, z1 - 1.0], [0.5, 14.0, 0.5], TIMBER)
    b.rig("rr_flag", -10.0, 13.6, z1 - 1.0, yaw=math.pi / 2.0, w=5.0, h=3.0,
          colours=["#c8302a", "#f4f0e0", "#c8302a", "#f4f0e0"])
    # cannons either side of the gate
    for x in (-16.0, 16.0):
        b.box([x, 0.12 + 0.8, z1 - 5.0], [2.4, 1.4, 3.2], "#4a3a2a")
        b.cyl([x, 0.12 + 1.8, z1 - 3.4], [1.0, 3.6, 1.0], IRON, material="metal", collide=False,
              r=[math.pi / 2.0 - 0.15, 0.0, 0.0])
    b.landmark(0.0, -88.0, "the customs house")


# ============================================================ the bazaar
def _bazaar(isle: Isle) -> None:
    """The grand bazaar: a hall of columns on a stone platform under a
    three-tiered roof, open on every side; stalls in rows, piled with
    spice and silk; lanterns hanging from the beams; the idol on its dais
    in the middle."""
    b = isle.b
    x0, x1, z0, z1 = HALL
    b.box([0.0, HALL_Y / 2.0, 0.0], [x1 - x0, HALL_Y, z1 - z0], "#c8b8a0")
    for x in (-24.0, -8.0, 8.0, 24.0):
        for z in (-18.0, -6.0, 6.0, 18.0):
            if abs(x) < 10.0 and abs(z) < 10.0:
                continue
            b.cyl([x, HALL_Y + (ROOF_Y - HALL_Y) / 2.0, z], [1.4, ROOF_Y - HALL_Y, 1.4], "#8a3a2a")
            b.box([x, ROOF_Y - 0.5, z], [2.2, 1.0, 2.2], SAFFRON)
    slab(b, rect(x0 - 2.0, x1 + 2.0, z0 - 2.0, z1 + 2.0), ROOF_Y + 0.8, 0.8, TILE)
    slab(b, rect(-20.0, 20.0, -15.0, 15.0), ROOF_Y + 2.2, 1.4, "#b83a2a")
    slab(b, rect(-13.0, 13.0, -9.0, 9.0), ROOF_Y + 3.6, 1.4, TILE)
    slab(b, rect(-7.0, 7.0, -4.0, 4.0), ROOF_Y + 4.8, 1.2, "#b83a2a")
    b.cone([0.0, ROOF_Y + 6.2, 0.0], [2.4, 2.8, 2.4], "#e8b830", material="metal")
    for sx in (-1.0, 1.0):
        for sz in (-1.0, 1.0):
            b.box([sx * (x1 + 1.3), ROOF_Y + 1.3, sz * (z1 + 1.3)], [1.4, 1.0, 1.4], "#e8b830", material="metal")
    # the stalls: rows of tables under the roof, a clear cross of aisles
    goods = ((SAFFRON, "cone"), (MAGENTA, "sph"), ("#c8402a", "cone"), (LIME, "sph"), (TEAL, "cyl"),
             (INDIGO, "cyl"))
    k = 0
    for sx in (-1.0, 1.0):
        for z in (-14.0, -9.0, 9.0, 14.0):
            x = sx * 16.0
            b.box([x, HALL_Y + 0.6, z], [8.0, 1.2, 2.4], "#7a5a3a")
            colour, shape = goods[k % len(goods)]
            for j in range(3):
                px = x - 2.6 + j * 2.6
                if shape == "cone":
                    b.cone([px, HALL_Y + 1.2 + 0.6, z], [1.8, 1.2, 1.8], colour, collide=False)
                elif shape == "sph":
                    b.sphere([px, HALL_Y + 1.2 + 0.5, z], [1.6, 1.0, 1.6], colour, collide=False)
                else:
                    b.cyl([px, HALL_Y + 1.2 + 0.6, z], [1.0, 1.2, 1.0], colour)
            k += 1
    # lanterns hanging from the roof on cords
    for x, z in ((-16.0, -12.0), (16.0, -12.0), (-16.0, 12.0), (16.0, 12.0), (0.0, -14.0), (0.0, 14.0),
                 (-14.0, 0.0), (14.0, 0.0)):
        b.box([x, ROOF_Y - 0.9, z], [0.1, 1.8, 0.1], "#4a3a2a", collide=False)
        b.box([x, ROOF_Y - 2.4, z], [1.0, 1.2, 1.0], (LANTERN, "#ff6a5a", "#ffd86a")[int(abs(x + z)) % 3],
              material="neon", collide=False)
    # the idol's dais in the middle
    b.box([0.0, HALL_Y + 0.3, 0.0], [10.0, 0.6, 10.0], "#a8987e")
    isle.idol(0.0, HALL_Y + 0.6, 0.0, colour="#b8a888")
    isle.loot(-16.0, HALL_Y, -11.5, "gem", "the grand bazaar")
    isle.loot(16.0, HALL_Y, 11.5, "gem", "the grand bazaar")
    isle.loot(-16.0, HALL_Y, 11.5, "bar", "the grand bazaar")
    isle.loot(16.0, HALL_Y, -11.5, "bar", "the grand bazaar")
    b.landmark(0.0, 0.0, "the grand bazaar")


# =========================================================== the town
def _shophouse(isle: Isle, r, door: str, wall: str, awning: str) -> None:
    """A shophouse: two storeys under a tiled roof, its shop open to the
    street under a striped awning, lanterns hung along it, shuttered
    windows above."""
    b = isle.b
    x0, x1, z0, z1 = r
    cx, cz = (x0 + x1) / 2.0, (z0 + z1) / 2.0
    along = cx if door in ("z-", "z+") else cz
    building(b, rect(x0, x1, z0, z1), 0.0, 10.0, wall, t=0.8, roof_colour=TILE, roof_t=0.6, floor_colour=PLANK,
             doors={door: [(along - 3.0, along + 3.0, 7.0)]}, lights=LANTERN, studs_roof=False)
    gable(b, rect(x0, x1, z0, z1), 10.6, TILE, "x" if x1 - x0 >= z1 - z0 else "z", tiers=3, rise=1.0, overhang=0.8)
    out = -1.0 if door in ("z-", "x-") else 1.0
    if door in ("z-", "z+"):
        face = z0 if door == "z-" else z1
        w = x1 - x0
        for k in range(4):
            b.box([x0 + (k + 0.5) * w / 4.0, 7.55, face + out * 1.5], [w / 4.0, 0.3, 3.0],
                  (awning, "#f4ece0")[k % 2])
        for e in (-1.0, 1.0):
            b.box([cx + e * (w / 2.0 - 1.0), 7.2, face + out * 2.6], [0.8, 0.4, 0.8], LANTERN, material="neon",
                  collide=False)
        for e in (-1.0, 1.0):
            b.box([cx + e * w * 0.25, 8.7, face + out * 0.06], [2.0, 1.6, 0.12], "#2a5a8a", collide=False)
    else:
        face = x0 if door == "x-" else x1
        d = z1 - z0
        for k in range(4):
            b.box([face + out * 1.5, 7.55, z0 + (k + 0.5) * d / 4.0], [3.0, 0.3, d / 4.0],
                  (awning, "#f4ece0")[k % 2])
        for e in (-1.0, 1.0):
            b.box([face + out * 2.6, 7.2, cz + e * (d / 2.0 - 1.0)], [0.8, 0.4, 0.8], LANTERN, material="neon",
                  collide=False)
        for e in (-1.0, 1.0):
            b.box([face + out * 0.06, 8.7, cz + e * d * 0.25], [0.12, 1.6, 2.0], "#2a5a8a", collide=False)
    isle.loot(cx, 0.4, cz, "any", "a shophouse")


def _half(isle: Isle, sgn: float) -> None:
    """One crew's wing (mirrored for the other): the shophouses, the spice
    godown, the dyers' yard with silk on the lines, the tea house, the
    boatyard, the fish market and the harbour's houses."""
    b = isle.b
    rng = isle.rng
    west = sgn < 0

    def X(x: float) -> float:
        return sgn * x

    for r, door, wall, awning in SHOPS:
        x0, x1 = sorted((X(r[0]), X(r[1])))
        if door in ("x-", "x+") and west:
            door = "x+" if door == "x-" else "x-"
        _shophouse(isle, (x0, x1, r[2], r[3]), door, wall, awning)
    # ---- the godown: a long warehouse for the spice, its bays open
    gx0, gx1 = sorted((X(GODOWN[0]), X(GODOWN[1])))
    gz0, gz1 = GODOWN[2], GODOWN[3]
    building(b, rect(gx0, gx1, gz0, gz1), 0.0, 10.0, "#d8c8a8", t=1.0, roof_colour="#8a5a3a", roof_t=0.8,
             floor_colour="#9a8a70", doors={"z+": [(gx0 + 4.0, gx0 + 12.0, 7.0), (gx1 - 12.0, gx1 - 4.0, 7.0)]},
             lights=LANTERN, studs_roof=False)
    gable(b, rect(gx0, gx1, gz0, gz1), 10.8, "#8a5a3a", "x", tiers=3, rise=1.2, overhang=0.8)
    for k in range(6):
        x = gx0 + 6.0 + k * 4.6
        b.box([x, 1.0, gz1 - 6.0], [3.0, 2.0, 2.6], (SAFFRON, "#c8402a", "#8a5a2a", LIME, MAGENTA, "#e8d070")[k],
              studs=True)
        if k % 2 == 0:
            b.box([x, 2.8, gz1 - 6.0], [2.6, 1.6, 2.2], ("#c8402a", SAFFRON, "#8a5a2a")[k // 2], studs=True)
    isle.loot((gx0 + gx1) / 2.0, 0.4, gz0 + 6.0, "gem", "the spice godown")
    for k in range(4):
        isle.crates(X(64.0 + k * 7.0), -72.0 + (k % 2) * 1.0, n=2 + k % 2)
    # ---- the dyers' yard: vats of colour, silk drying on the lines
    for k, (x, colour) in enumerate(((64.0, MAGENTA), (72.0, SAFFRON), (80.0, TEAL), (88.0, INDIGO),
                                     (96.0, "#c8302a"))):
        b.cyl([X(x), 0.8, -32.0], [4.4, 1.6, 4.4], "#7a5a3a")
        b.cyl([X(x), 1.61, -32.0], [3.8, 0.04, 3.8], colour, collide=False)
    for k, z in enumerate((-42.0, -38.0)):
        for e in (-1.0, 1.0):
            b.cyl([X(80.0 + e * 17.0), 3.2, z], [0.4, 6.4, 0.4], TIMBER)
        b.rig("rr_clothesline", X(80.0), 6.2, z, w=33.0,
              colours=[MAGENTA, SAFFRON, TEAL, INDIGO, "#c8302a"] if k == 0 else [LIME, "#ff8ad8", SAFFRON, TEAL, MAGENTA])
    isle.loot(X(80.0), None, -24.0, "any", "the dyers' yard")
    # ---- the boatyard by the great canal: a boat up on blocks, timber
    bx, bz = X(78.0), 24.0
    for e in (-3.0, 3.0):
        b.box([bx + e, 0.6, bz], [1.4, 1.2, 1.4], "#8a8478")
    b.box([bx, 2.2, bz], [10.0, 2.0, 3.6], "#6a4a2e")
    b.box([bx, 3.3, bz], [9.0, 0.2, 3.0], "#3a2a1a", collide=False)
    for k in range(3):
        b.box([X(64.0), 0.3 + k * 0.6, 24.0 + (k % 2) * 0.4], [6.0, 0.6, 1.0], TIMBER)
    isle.loot(X(90.0), None, 24.0, "any", "the boatyard")
    # ---- the fish market: an open shed of stalls, ice and fish on them
    mx0, mx1 = sorted((X(MARKET[0]), X(MARKET[1])))
    mz0, mz1 = MARKET[2], MARKET[3]
    for px in (mx0 + 0.5, mx1 - 0.5, (mx0 + mx1) / 2.0):
        for pz in (mz0 + 0.5, mz1 - 0.5):
            b.cyl([px, 3.2, pz], [0.6, 6.4, 0.6], TIMBER)
    for k in range(3):
        b.box([mx0 + (k + 0.5) * (mx1 - mx0) / 3.0, 6.55, (mz0 + mz1) / 2.0], [(mx1 - mx0) / 3.0, 0.3, mz1 - mz0 + 1.0],
              (TEAL, "#f4ece0", TEAL)[k])
    for k in range(2):
        tz = mz0 + 3.0 + k * 4.0
        b.box([(mx0 + mx1) / 2.0, 0.6, tz], [mx1 - mx0 - 3.0, 1.2, 1.8], "#7a5a3a")
        b.box([(mx0 + mx1) / 2.0, 1.25, tz], [mx1 - mx0 - 3.4, 0.1, 1.5], "#d8eef4", collide=False)
        for j in range(5):
            b.box([mx0 + 3.0 + j * 3.0, 1.4, tz], [1.8, 0.2, 0.7], ("#8aa0b4", "#c8a0a0", "#a0b8a0")[j % 3],
                  collide=False)
    isle.loot((mx0 + mx1) / 2.0, None, mz1 + 2.0, "any", "the fish market")
    _teagarden(isle, sgn)
    _stupa(isle, sgn)
    _pier(isle, sgn)
    # ---- palms, lantern posts, rain barrels, a flag
    for x, z in ((106.0, -86.0), (104.0, -36.0), (106.0, 30.0), (100.0, 74.0), (70.0, 82.0), (52.0, 90.0),
                 (96.0, 40.0 + 6.0), (58.0, -72.0)):
        px, pz = X(x + rng.uniform(-1.0, 1.0)), z + rng.uniform(-1.0, 1.0)
        if isle.clear(px, pz, 2.0):
            isle.palm(px, pz, h=rng.uniform(12.0, 16.0))
    for x, z in ((40.0, -30.0), (100.0, -15.0 + 4.0), (60.0, 46.0), (88.0, 44.0)):
        y = isle.top(X(x), z)
        b.cyl([X(x), y + 2.6, z], [0.4, 5.2, 0.4], TIMBER)
        b.box([X(x), y + 5.6, z], [1.0, 1.2, 1.0], (LANTERN, "#ff6a5a", "#ffd86a")[int(x) % 3], material="neon")
    for x, z in ((40.0, -60.0), (56.0, -6.0)):
        isle.barrel(X(x), z, colour="#5a6a7a")
    isle.flag(X(108.0), 0.0, None, "#c8302a" if west else "#2a6ab8", h=11.0)
    # ---- X's and loot
    isle.dig(X(40.5), None, -70.0, "behind the stupa")
    isle.dig(X(96.0), None, -64.0, "the dyers' yard")
    isle.dig(X(102.0), None, 0.0, "the tea garden")
    isle.dig(X(50.0), None, 74.0, "the harbour")
    isle.dig(X(86.0), None, 84.0, "the south beach")
    isle.loot(X(104.0), None, -50.0, "any", "the beach")
    isle.loot(X(36.0), None, 6.0, "any", "the bazaar's streets")
    isle.loot(X(66.0), None, 74.0, "any", "the harbour")


def _teagarden(isle: Isle, sgn: float) -> None:
    """The tea garden: a stone terrace up a flight from each side, lawn on
    top; a pavilion under a tiered roof with the tea table set; a raised
    koi pond, lily pads on it; stone lanterns at the heads of the stairs;
    two bonsai pines and a blossom tree shedding its petals."""
    b = isle.b

    def X(x: float) -> float:
        return sgn * x

    x0, x1 = sorted((X(TEA[0]), X(TEA[1])))
    z0, z1 = TEA[2], TEA[3]
    cx = (x0 + x1) / 2.0
    top = TEA_Y + 0.1
    b.box([cx, TEA_Y / 2.0, 0.0], [x1 - x0, TEA_Y, z1 - z0], "#a89a88")
    b.box([cx, TEA_Y + 0.05, 0.0], [x1 - x0 - 1.2, 0.1, z1 - z0 - 1.2], "#6aa84a", studs=True)
    xa, xb = sorted((X(90.0), X(98.0)))
    flight(b, "z", z0 - 2.0, z0, xa, xb, 0.0, TEA_Y, "#b8aa94", rise=0.8)
    flight(b, "z", z1 + 2.0, z1, xa, xb, 0.0, TEA_Y, "#b8aa94", rise=0.8)
    flight(b, "x", X(TEA[1] + 2.0), X(TEA[1]), -4.0, 4.0, 0.0, TEA_Y, "#b8aa94", rise=0.8)
    flight(b, "x", X(TEA[0] - 2.0), X(TEA[0]), -4.0, 4.0, 0.0, TEA_Y, "#b8aa94", rise=0.8)
    # the pavilion: four red posts, a roof in four tiers turned up at the corners
    px, pz = X(97.5), -4.0
    for ex in (-3.0, 3.0):
        for ez in (-3.0, 3.0):
            b.cyl([px + ex, top + 2.95, pz + ez], [0.7, 5.9, 0.7], "#a83a2a")
    for k, (w, h, colour) in enumerate(((9.4, 0.4, TILE), (7.0, 0.6, "#b83a2a"), (4.4, 0.6, TILE),
                                        (2.0, 0.6, "#b83a2a"))):
        y0 = top + 5.9 + (0.0, 0.4, 1.0, 1.6)[k]
        b.box([px, y0 + h / 2.0, pz], [w, h, w], colour)
    for ex in (-1.0, 1.0):
        for ez in (-1.0, 1.0):
            b.box([px + ex * 4.35, top + 6.45, pz + ez * 4.35], [0.6, 0.3, 0.6], "#e8b830", material="metal",
                  collide=False)
    b.cone([px, top + 8.1 + 0.6, pz], [1.0, 1.2, 1.0], "#e8b830", material="metal", collide=False)
    b.box([px, top + 0.3, pz], [2.6, 0.6, 1.6], "#6a3a22")
    b.sphere([px - 0.5, top + 0.85, pz], [0.6, 0.5, 0.6], "#3a6a5a", collide=False)
    for e in (-1.0, 1.0):
        b.box([px + 0.5, top + 0.66, pz + e * 0.4], [0.24, 0.12, 0.24], "#f4f0e4", collide=False)
        b.box([px, top + 0.125, pz + e * 1.7], [1.6, 0.25, 1.2], (MAGENTA, SAFFRON)[e > 0])
    isle.loot(px + 0.6, top + 0.6, pz, "gem", "the tea pavilion")
    # the koi pond: a stone rim, dark water, lily pads; the koi circling in it
    qx, qz = X(89.0), 4.0
    for ex, ez, w, d in ((-3.3, 0.0, 0.6, 7.2), (3.3, 0.0, 0.6, 7.2), (0.0, -3.3, 6.0, 0.6), (0.0, 3.3, 6.0, 0.6)):
        b.box([qx + ex, top + 0.3, qz + ez], [w, 0.6, d], "#c8bca8")
    b.box([qx, top + 0.03, qz], [6.0, 0.06, 6.0], "#1e4a4a", collide=False)
    b.box([qx, (top + 0.06 + top + 0.35) / 2.0, qz], [6.0, 0.29, 6.0], "#3a8a9a", material="glass", alpha=0.55,
          collide=False)
    for lx, lz, r in ((-1.6, -1.2, 1.0), (1.4, 1.5, 0.8), (1.8, -1.8, 0.7)):
        b.cyl([qx + lx, top + 0.37, qz + lz], [r, 0.04, r], "#4a9a3a", collide=False)
    b.sphere([qx - 1.6, top + 0.45, qz - 1.2], [0.3, 0.2, 0.3], "#ff8ad8", collide=False)
    b.rig("pb_koi", qx, top + 0.35, qz, r=2.4, n=5)
    # stone lanterns at the heads of the north and south stairs
    for lx, lz in ((88.8, -8.8), (99.2, -8.8), (88.8, 8.8), (99.2, 8.8)):
        x = X(lx)
        b.box([x, top + 0.2, lz], [1.0, 0.4, 1.0], "#b8aa94")
        b.box([x, top + 1.0, lz], [0.5, 1.2, 0.5], "#b8aa94")
        b.box([x, top + 2.05, lz], [1.1, 0.9, 1.1], "#c8bca8")
        b.box([x, top + 2.05, lz], [0.8, 0.5, 1.16], LANTERN, material="neon")
        b.box([x, top + 2.65, lz], [1.5, 0.3, 1.5], "#a89a88")
        b.box([x, top + 3.0, lz], [0.5, 0.4, 0.5], "#a89a88")
    # bonsai pines: a crooked trunk, flat clouds of needles
    for bx, bz in ((86.0, -6.0), (91.0, -2.0)):
        x = X(bx)
        b.cyl([x, top + 0.7, bz], [0.5, 1.4, 0.5], "#5a3a2a")
        b.sphere([x, top + 1.7, bz], [2.4, 0.9, 2.4], "#2e6a3a")
        b.sphere([x + sgn * 0.7, top + 2.4, bz + 0.4], [1.6, 0.7, 1.6], "#3a7a44", collide=False)
    # the blossom tree, its petals falling on the lawn
    tx, tz = X(101.0), 6.0
    b.cyl([tx, top + 3.45, tz], [0.9, 6.9, 0.9], "#5a3a2a")
    b.box([tx + sgn * 1.2, top + 5.8, tz - 0.4], [0.4, 3.2, 0.4], "#5a3a2a", collide=False,
          r=[0.0, 0.0, -sgn * 0.6])
    b.sphere([tx, top + 7.9, tz], [6.0, 3.6, 6.0], "#f8b8d0", collide=False)
    b.sphere([tx - sgn * 1.5, top + 7.3, tz + 1.5], [4.0, 2.6, 4.0], "#ffc8dc", collide=False)
    b.sphere([tx + sgn * 1.5, top + 7.5, tz - 1.2], [4.4, 2.8, 4.4], "#f0a0c0", collide=False)
    b.rig("pb_petals", tx, top + 6.6, tz, r=3.5, h=6.6, n=20, seed=sgn * 2.0)


def _stupa(isle: Isle, sgn: float) -> None:
    """A white stupa behind the shophouses: two plinths, the drum and the
    dome, the gilded tower on top with the Buddha's eyes looking out from
    its four faces and its spire of rings; prayer flags from the spire to
    poles at the corners; butter lamps along the steps; incense smoking."""
    b = isle.b
    x, z = sgn * STUPA[0], STUPA[1]
    b.box([x, 0.5, z], [12.0, 1.0, 12.0], "#e8e0d0")
    b.box([x, 1.5, z], [8.4, 1.0, 8.4], "#f0e8d8")
    b.cyl([x, 2.6, z], [6.4, 1.2, 6.4], "#f4f0e4")
    b.sphere([x, 5.6, z], [6.4, 5.6, 6.4], "#f8f4ec")
    b.box([x, 8.9, z], [2.4, 1.6, 2.4], "#e8b830", material="metal")
    for ax, az, rot in ((0.0, 1.0, False), (0.0, -1.0, False), (1.0, 0.0, True), (-1.0, 0.0, True)):
        for e in (-0.5, 0.5):
            ex, ez = (ax * 1.2 + 0.0, e) if rot else (e, az * 1.2)
            sx, sz = ((0.04, 0.6), (0.05, 0.25)) if rot else ((0.6, 0.04), (0.25, 0.05))
            ox, oz = (ax * 0.02, 0.0) if rot else (0.0, az * 0.02)
            ox2, oz2 = (ax * 0.035, 0.0) if rot else (0.0, az * 0.035)
            b.box([x + ex + ox, 9.1, z + ez + oz], [sx[0], 0.3, sx[1]], "#f4f4f4", collide=False)
            b.box([x + ex + ox2, 9.1, z + ez + oz2], [sz[0], 0.25, sz[1]], "#2a3a8a", collide=False)
    for k in range(7):
        d = 2.0 - k * 0.2
        b.cyl([x, 9.7 + k * 0.4 + 0.2, z], [d, 0.4, d], "#e8b830", material="metal", collide=False)
    b.cone([x, 12.5 + 0.6, z], [2.2, 1.2, 2.2], "#e8b830", material="metal", collide=False)
    b.cyl([x, 14.1, z], [0.2, 0.8, 0.2], "#e8b830", material="metal", collide=False)
    flags = ["#3a6ac8", "#f4f0e8", "#c8302a", "#3a9a4a", "#f0c830"]
    for ex in (-5.6, 5.6):
        for ez in (-5.6, 5.6):
            b.cyl([x + ex, 1.0 + 2.5, z + ez], [0.3, 5.0, 0.3], TIMBER)
            b.rig("pb_bunting", x, 13.4, z, q=(x + ex, 6.0, z + ez), sag=0.5, size=0.8, colours=flags)
    for k in range(5):
        b.box([x - 2.4 + k * 1.2, 1.15, z + 5.75], [0.3, 0.3, 0.3], "#ffd86a", material="neon", collide=False)
    b.cyl([x, 0.6, z + 8.0], [1.6, 1.2, 1.6], "#8a6a3a", material="metal")
    b.rig("rr_smoke", x, 1.3, z + 8.0, wind=[0.5, 0.3], rate=0.25, h=6.0, size=0.6, colour="#d8d0c8")
    b.landmark(x, z, "the west stupa" if sgn < 0 else "the east stupa")


def _pier(isle: Isle, sgn: float) -> None:
    """A fishing pier off the south beach: a stone quay, plank deck on
    posts out into the sea, a platform at the end with a great cantilevered
    net on its frame that dips into the water and hauls up full."""
    b = isle.b

    def X(x: float) -> float:
        return sgn * x

    xa, xb = sorted((X(PIER[0]), X(PIER[1])))
    cx = (xa + xb) / 2.0
    flight(b, "z", 89.0, 92.0, xa, xb, 0.0, PIER_Y, PLANK, rise=0.8)
    b.box([cx, 0.6, 96.0], [xb - xa - 0.4, 1.2, 8.0], "#8a7a68")
    b.box([cx, PIER_Y - 0.2, 99.0], [xb - xa, 0.4, 14.0], PLANK)
    pa, pb = sorted((X(60.0), X(74.0)))
    b.box([(pa + pb) / 2.0, PIER_Y - 0.2, 110.0], [pb - pa, 0.4, 8.0], PLANK)
    for z in (101.0, 104.5):
        for xx in (xa + 0.6, xb - 0.6):
            b.cyl([xx, (SEABED + PIER_Y - 0.4) / 2.0, z], [0.8, PIER_Y - 0.4 - SEABED, 0.8], TIMBER)
    for z in (107.0, 113.4):
        for xx in (pa + 0.6, pb - 0.6):
            b.cyl([xx, (SEABED + PIER_Y - 0.4) / 2.0, z], [0.8, PIER_Y - 0.4 - SEABED, 0.8], TIMBER)
    for xx in (pa + 0.6, pb - 0.6):
        b.cyl([xx, PIER_Y + 2.0, 113.4], [0.4, 4.0, 0.4], TIMBER)
        b.box([xx, PIER_Y + 4.5, 113.4], [0.9, 1.0, 0.9], LANTERN, material="neon")
    isle.crates(X(62.2), 108.2, y=PIER_Y, n=2)
    isle.barrel(X(62.4), 111.8, y=PIER_Y, colour="#6a7a5a")
    isle.loot(X(66.0), PIER_Y, 111.0, "any", "the fishing pier")
    b.rig("pb_fishnet", X(73.2), PIER_Y, 110.0, yaw=sgn * math.pi / 2.0, len=14.0, seed=1.0 + sgn)


def _falls(isle: Isle) -> None:
    """The monsoon torrents: a waterfall off the cliffs into the head of
    each side canal, rocks either side of the lip, rain rings down the
    canal it feeds."""
    b = isle.b
    for sgn in (-1.0, 1.0):
        x = sgn * (CANAL_NS[0] + CANAL_NS[1]) / 2.0
        top = b.surface(x, NORTH - 2.0, 80.0)
        for e in (-1.0, 1.0):
            b.box([x + e * 5.0, top + 0.9, NORTH - 1.0], [2.4, 1.8, 1.6], "#6a5a4a", collide=False)
        b.rig("pb_falls", x, top + 0.05, NORTH, yaw=0.0, w=7.0, drop=top - SEA_TOP)
        b.rig("pb_ripples", x, SEA_TOP, (NORTH + CANAL_NS[3]) / 2.0, w=7.0, d=CANAL_NS[3] - NORTH - 4.0, n=34,
              seed=sgn * 5.0)
    b.rig("pb_ripples", 0.0, SEA_TOP, (CANAL_EW[2] + CANAL_EW[3]) / 2.0, w=2 * SHORE_X - 4.0, d=7.0, n=44, seed=9.0)


def _festoons(isle: Isle) -> None:
    """Bunting round the bazaar's eaves and across the avenue between the
    shophouses; puddles on the streets with the rain ringing in them; the
    rainbow over the cliffs."""
    b = isle.b
    ring = [(-24.0, 0.0, -18.0), (-8.0, 0.0, -18.0), (8.0, 0.0, -18.0), (24.0, 0.0, -18.0), (24.0, 0.0, -6.0),
            (24.0, 0.0, 6.0), (24.0, 0.0, 18.0), (8.0, 0.0, 18.0), (-8.0, 0.0, 18.0), (-24.0, 0.0, 18.0),
            (-24.0, 0.0, 6.0), (-24.0, 0.0, -6.0)]
    b.rig("pb_bunting", 0.0, ROOF_Y - 1.0, 0.0, path=ring, loop=True, sag=0.6, size=0.9)
    for z, half in ((-64.0, 8.0), (-58.0, 8.0), (-46.0, 10.0), (-40.0, 10.0)):
        b.rig("pb_bunting", -half, 9.4, z, q=(half, 9.4, z), sag=1.0)
    for x, z, w, d in PUDDLES:
        b.box([x, 0.135, z], [w, 0.03, d], "#8a98a8", material="glass", alpha=0.5, collide=False)
    b.rig("pb_ripples", 0.0, 0.16, 0.0, spots=[[x, z, min(w, d) / 2.0] for x, z, w, d in PUDDLES],
          n=2 * len(PUDDLES), seed=2.0)
    b.rig("pb_rainbow", -40.0, -70.0, -440.0, yaw=math.atan2(-40.0, -440.0), r=320.0, a=0.24)


def _pagoda(isle: Isle) -> None:
    """The pagoda lighthouse over the harbour: five tiers, each roof
    turned up at its corners, its lamp at the top lit for the boats."""
    b = isle.b
    x, z = PAGODA
    b.box([x, 0.6, z], [14.0, 1.2, 14.0], "#a89a88")
    y = 1.2
    for k in range(5):
        w = 10.0 - k * 1.4
        h = 5.0 - k * 0.5
        b.box([x, y + h / 2.0, z], [w, h, w], ("#c8302a", WHITE)[k % 2])
        rw = w + 3.0
        b.box([x, y + h + 0.3, z], [rw, 0.6, rw], TILE)
        for sx in (-1.0, 1.0):
            for sz in (-1.0, 1.0):
                b.box([x + sx * rw / 2.0, y + h + 0.9, z + sz * rw / 2.0], [0.8, 0.6, 0.8], "#e8b830",
                      material="metal", collide=False)
        y += h + 0.6
    b.cyl([x, y + 1.2, z], [3.0, 2.4, 3.0], "#fff4c8", material="glass", alpha=0.5, collide=False)
    b.cyl([x, y + 1.2, z], [1.4, 1.8, 1.4], "#fff0a0", material="neon", collide=False)
    b.cone([x, y + 3.4, z], [3.6, 2.0, 3.6], TILE)
    b.rig("rr_lighthouse", x, y + 1.2, z, len=200.0, rate=0.45)
    b.box([x, 2.4, z + 5.06], [3.0, 2.4, 0.12], "#3a2a1a", collide=False)
    b.landmark(x, z, "the pagoda lighthouse")


def _patrols(isle: Isle) -> None:
    """The marines: six out of the courtyard (``barracks``); three beats
    (``patrol``) -- each route's first three points the way out of the
    gate and down the avenue, its loop from the fourth on: round the west
    of the bazaar and back, round the east and back, and over the great
    canal's bridge round the fish market."""
    b = isle.b
    for k in range(6):
        b.mark("barracks", -4.8 + (k % 3) * 4.8, 0.24, -84.0 + (k // 3) * 3.0)
    s = 0.24
    out = [(0.0, s, -78.0), (0.0, s, -70.0), (0.0, s, -28.0)]
    west = [(-36.0, s, -28.0), (-36.0, s, 27.0), (-9.0, s, 27.0), (-36.0, s, 27.0), (-36.0, s, -28.0), (0.0, s, -28.0)]
    east = [(36.0, s, -28.0), (36.0, s, 27.0), (9.0, s, 27.0), (36.0, s, 27.0), (36.0, s, -28.0), (0.0, s, -28.0)]
    south = [(36.0, s, -28.0), (36.0, s, 27.0), (0.0, s, 27.0), (0.0, 0.5, 30.0), (0.0, 2.0, 35.0), (0.0, 2.0, 41.0),
             (0.0, 0.5, 46.0), (0.0, s, 50.0), (-37.0, s, 50.0), (-37.0, s, 84.0), (37.0, s, 84.0), (37.0, s, 50.0),
             (0.0, s, 50.0), (0.0, 0.5, 46.0), (0.0, 2.0, 41.0), (0.0, 2.0, 35.0), (0.0, 0.5, 30.0), (0.0, s, 27.0),
             (36.0, s, 27.0), (36.0, s, -28.0), (0.0, s, -28.0)]
    for r, loop in enumerate((west, east, south)):
        for i, (x, y, z) in enumerate(out + loop):
            b.mark("patrol", x, y, z, route=r, i=i)


# ================================================================ meta
def _meta(isle: Isle) -> None:
    b = isle.b
    for x, z, name in ((-78.0, -88.0, "the west godown"), (78.0, -88.0, "the east godown"),
                       (-80.0, -36.0, "the west dyers' yard"), (80.0, -36.0, "the east dyers' yard"),
                       (0.0, 38.0, "the great canal"), (-23.0, 59.0, "the west fish market"),
                       (23.0, 59.0, "the east fish market"),
                       (-SHIP_X, 0.0, "the Scarlet Queen"), (SHIP_X, 0.0, "the Blue Marlin")):
        b.landmark(x, z, name)
    b.camera(0.0, 44.0, 112.0, 0.0, 6.0, -10.0)
    b.camera(-110.0, 40.0, 50.0, -10.0, 6.0, -10.0)
    b.camera(40.0, 30.0, -40.0, 0.0, 10.0, -90.0)
    b.camera(-40.0, 16.0, 30.0, 0.0, 6.0, 0.0)
    b.extra.update({"twist": "redcoats", "water": SEA_TOP, "redcoats_every": [50.0, 66.0], "redcoats_for": 30.0,
                    "warn": 6.0,
                    "twist_line": "the Company's marines are out",
                    "twist_text": {"warn": "THE CUSTOMS GONG IS SOUNDING",
                                   "warnSub": "The Company's marines are turning out...",
                                   "on": "THE MARINES!", "onSub": "They shoot any pirate they see -- carriers first",
                                   "off": "The marines march back to the customs house", "chip": "MARINES"}})
    b.rig("rr_weather", 0.0, 0.0, 0.0, weather="rain", wind=[0.4, 0.3])
    b.rig("pb_lanterns", 0.0, SEA_TOP, 38.0, n=14, w=200.0, d=6.0, seed=3.0)
    for sgn in (-1.0, 1.0):
        b.rig("pb_lanterns", sgn * 48.0, SEA_TOP, -16.0, n=6, w=6.0, d=90.0, seed=sgn * 4.0)
        b.rig("pb_sampan", sgn * 48.0, SEA_TOP, -34.0, yaw=0.0, seed=sgn * 2.0, colour="#8a4a2a", roof="#c8a060")
        b.rig("pb_sampan", sgn * 54.0, SEA_TOP, 38.0, yaw=math.pi / 2.0, seed=sgn * 6.0, colour="#2a6a8a",
              roof="#d8a040")
        b.rig("pb_parrots", sgn * 80.0, 22.0, 60.0, r=14.0, n=4, seed=sgn * 3.0)
        b.rig("rr_smoke", sgn * 23.0, 2.0, 66.0, wind=[0.6, 0.4], rate=0.2, h=10.0, size=1.2, colour="#a8a098")
        b.rig("rr_surf", sgn * (SHORE_X + 6.5), SEA_TOP + 0.3, -40.0, w=80.0, yaw=sgn * math.pi / 2.0)
        b.rig("rr_surf", sgn * (SHORE_X + 6.5), SEA_TOP + 0.3, 70.0, w=50.0, yaw=sgn * math.pi / 2.0)
    b.rig("rr_surf", 0.0, SEA_TOP + 0.3, SOUTH + 6.5, w=2 * SHORE_X - 10.0, yaw=0.0)
    b.rig("rr_gulls", 0.0, 36.0, 70.0, r=36.0, n=5, seed=4)


def build(b: ArenaArea) -> None:
    rng = random.Random(0x3050)
    isle = Isle(b, rng)
    _land(isle)
    _edges(isle)
    _bridges(isle)
    _customs(isle)
    _bazaar(isle)
    _half(isle, -1.0)
    _half(isle, 1.0)
    _pagoda(isle)
    _falls(isle)
    _festoons(isle)
    _patrols(isle)
    galleon(isle, "red", 0.0)
    galleon(isle, "blue", 0.0)
    _meta(isle)
