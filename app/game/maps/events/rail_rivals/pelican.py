"""Pelican Wharf -- a bright little fishing town on a bay, its two lines
across the Cut on swing bridges.

Layout (north is -z; both tracks run west to east)::

    z -250 ~~~~~~~~~~~~~~~~~~~~~~~~ THE BAY ~~~~~~~~~~~~~~~~~~~~~~~~~~~~ (headland)
           ~  C  ~ pleasure pier, the beach,   fishing piers, the fish    LIGHTHOUSE
           ~  U  ~ the carousel & the slide    market, the net lofts       POINT
           ~  T  ~=====================\\                          /==== (lane b end)
    z    0 YARDS T  footbridge          \\=== PELICAN SQUARE ====/    GRAND PELICAN
           ~     ~=====================/   (the fountain)        \\       HOTEL
           ~     ~  CANNERY ROW: the cannery,     CHAPEL HILL: pastel  \\==== BAYSIDE
    z +250 ~     ~  the boatyard and its schooner  cottages climbing it   (lane a end)

The yards are on the west bank of the Cut, a ship channel from the bay to
the boatyard basin; both lines cross it on swing bridges right at the
start of the race, and a tall footbridge further along carries people over
when the bridges are open.  The rest of the town climbs from the beach up
over Pelican Square to Chapel Hill.

The twist is Redrock Mesa's, as swing bridges (``bridges``,
``bridge_style`` swing): hold E in the other company's bridge tender's hut
and their bridge swings open across the Cut (a bell, two seconds to get
off it); their cart waits at the bank until it closes -- by itself, or when
their own side gets to the hut.  A tug steams through while it is open.
Fall in the water and the harbour has you.
"""
from __future__ import annotations

import math
import random

from ..kit import (WARM, WOOD, WOOD_DARK, WOOD_LIGHT, ArenaArea, backdrop, building, carve,
                   flight, gable, ground, lantern, plate, rect, room_walls, sign_decal, slab,
                   threshold, wall_sign)
from ...lastlight.kit import lamp_post
from . import common, rails
from .land import Land, graded, lay_graded, world_lane
from .rails import clear_of, fillet, lay_track, mirror, storeyed, telegraph
from .scenery import outcrop

HALF = (400.0, 250.0)
SKY = {"top": "#3a86d8", "horizon": "#cfeaf8", "sun": [0.35, 0.78, 0.4],
       "clouds": 0.35, "tint": "#fff8ec"}
AMBIENT = "#9fb8c8"
GROUND = "#8ab84e"
FOG = 900.0

GRASS = "#8ab84e"
GRASS_LIGHT = "#a8c85a"
GRASS_DEEP = "#6a9a40"
SAND = "#f0dca8"
STONE = "#b8b0a0"
STONE_DARK = "#8a8478"
WATER = "#2a8ab0"
COBBLE = "#a8a094"
PASTELS = ("#f4b8c8", "#b8e8d0", "#fbe49a", "#b8d8f4", "#f8c89a", "#d8c8f0", "#f4f0e0")
TRIM = "#f8f6f0"
RED = "#d8322a"
NAVY = "#2a3a6a"

ROUTE = fillet([(-372.0, -150.0), (-100.0, -150.0), (0.0, 0.0), (100.0, 150.0), (372.0, 150.0)],
               radius=60.0, step=5.0)
PROFILE = [(0.0, 0.0), (0.22, 0.0), (0.33, 3.0), (0.45, 1.0), (0.55, 1.0), (0.7, 5.0), (0.86, 0.0),
           (1.0, 0.0)]
LANE_A, YS = graded(ROUTE, PROFILE)
LANE_B = mirror(LANE_A)
LANES = (LANE_A, LANE_B)
LANE_OF = {"a": LANE_A, "b": LANE_B}

CUT = (-250.0, -206.0)            # the ship channel's banks, west and east
SPAN = (-254.0, -202.0)           # each swing bridge's deck along x
PIVOT_X = -228.0
SEA_EDGE = -205.0                 # the shore: the bay is north of this
WATER_Y = -2.5
FLOOR_Y = -14.0
DROWN_Y = -6.0
DEEP_Y = -72.0                    # the only solid floor under the water
HEADLAND = rect(250.0, 330.0, -250.0, -205.0)
FOOTBRIDGE_Z = 70.0               # two footbridges, at -70 and +70
FOOTBRIDGE_Y = 18.0
CONTROL = rect(-300.0, -268.0, -14.0, 14.0)    # the Cut control house: both bridges' wheels
KNOLL = (-330.0, 0.0, 8.0, 64.0, 96.0)         # the harbour gardens' knoll: x, z, height, radii
LIFEBOAT = rect(-338.0, -308.0, -203.0, -183.0)
STORES = rect(-392.0, -334.0, 194.0, 238.0)    # the cannery stores in the south yard
SQUARE = rect(-34.0, 34.0, -30.0, 30.0)
CANNERY = rect(-190.0, -120.0, 176.0, 236.0)
HILL = (190.0, 150.0, 16.0, 86.0)
HOTEL = rect(326.0, 386.0, -46.0, 46.0)
LIGHTHOUSE = (290.0, -228.0)

DEPOTS = (("a", 1 / 3.0, 1.0, "SHORE ROAD", 1, "#d8322a"),
          ("a", 2 / 3.0, -1.0, "CHAPEL HILL", 2, "#2a3a6a"),
          ("b", 1 / 3.0, -1.0, "SHORE ROAD SOUTH", 1, "#2a3a6a"),
          ("b", 2 / 3.0, 1.0, "CHAPEL HILL NORTH", 2, "#d8322a"))
COAL = ((-336.0, -100.0), (-336.0, 100.0), (-60.0, 0.0), (150.0, 0.0))

KEEP: list = []
BASES: dict = {}


def build(b: ArenaArea) -> None:
    rng = random.Random(0x9E1C)
    del KEEP[:]
    BASES.clear()
    del LINES[:]
    del SHEEP[:]
    for rigs in (CLOCKS, VANES, FLAGS, LIGHTS, SMOKES, MINIMILLS, POND_SWANS, POND_FOUNTAIN):
        del rigs[:]
    MILL[0] = None
    span = [SPAN[0] + 372.0, SPAN[1] + 372.0]
    b.extra.update({"accent": "#ff6a5a", "twist": "bridges", "bridge_style": "swing",
                    "bridge_lamp_y": 6.4, "drown_y": DROWN_Y, "drown_what": "the harbour",
                    "lanes": {"a": world_lane(b, LANE_A, YS), "b": world_lane(b, LANE_B, YS)},
                    "names": {"a": "the Shore line", "b": "the Cannery line"},
                    "bridges": {"a": list(span), "b": list(span)}})
    land = _land()
    sea = rect(-b.half_x, b.half_x, -b.half_z - b.margin, SEA_EDGE)
    cut = rect(CUT[0], CUT[1], SEA_EDGE, b.half_z)
    ground(b, GRASS, soil="#6a5a44", holes=[r for r in carve(sea, [HEADLAND]) if r[3] - r[2] > 0.1] + [cut])
    land.build(b, GRASS)
    _water(b, rng)
    _edge(b, rng)
    for path in LANES:
        lay_graded(b, path, YS, ballast="#9a9488", skip=[tuple(span)], bare=[tuple(span)])
    common.start_yards(b, ("WHARF YARD", "CANNERY YARD"), (RED, NAVY), KEEP, post=TRIM,
                       sign_bg=TRIM, sign_fg=NAVY)
    _bridges(b)
    _footbridge(b, land)
    _control_house(b)
    _promenade(b, rng)
    _gardens(b, rng, land)
    _lifeboats(b, rng)
    _stores(b, rng)
    _harbour_houses(b, rng)
    _boat_sheds(b, rng)
    _yard_bits(b, rng)
    _crazy_golf(b, rng)
    _boating_pond(b, rng)
    _nets_and_smokehouse(b, rng)
    _beach(b, rng, land)
    _harbour(b, rng)
    _headland(b, rng)
    _square(b, rng)
    _cannery(b, rng)
    _hill(b, rng, land)
    _hotel(b, rng)
    common.termini(b, ("BAYSIDE", "LIGHTHOUSE POINT"), (NAVY, RED), KEEP, house=PASTELS[3], trim=NAVY,
                   sign_bg=TRIM, sign_fg=NAVY)
    common.place_depots(b, DEPOTS, LANE_OF, BASES, KEEP)
    common.place_levers(b, land, LANE_OF, KEEP)
    common.place_coal(b, COAL, BASES, rng, KEEP)
    _scatter(b, rng, land)
    telegraph(b, LANE_A, -1.0, ground=land.height, skip=_blocked)
    telegraph(b, LANE_B, 1.0, ground=land.height, skip=_blocked)
    _rigs(b)
    for x, z, name in ((-345, -150, "the wharf yard"), (-345, 150, "the cannery yard"),
                       (PIVOT_X, -150, "the north swing bridge"), (PIVOT_X, 150, "the south swing bridge"),
                       (PIVOT_X, 0, "the Cut"), (PIVOT_X, -FOOTBRIDGE_Z, "the north footbridge"),
                       (PIVOT_X, FOOTBRIDGE_Z, "the south footbridge"), (-284, 0, "the control house"),
                       (KNOLL[0], 0, "the bandstand"), (-312, 36, "the floral clock"),
                       (-312, -36, "the topiary pelican"), (-323, -193, "the lifeboat station"),
                       (-363, 216, "the cannery stores"),
                       (-140, -228, "the pleasure pier"), (-140, -244, "the carousel"), (-100, -190, "the beach"),
                       (30, -225, "the fishing piers"), (20, -180, "the fish market"), (70, -176, "the net lofts"),
                       (LIGHTHOUSE[0], LIGHTHOUSE[1], "the lighthouse"), (0, 0, "Pelican Square"),
                       (0, 6, "the pelican fountain"), (-155, 206, "the cannery"), (-90, 214, "the boatyard"),
                       (190, 150, "Chapel Hill"), (190, 120, "the chapel"), (356, 0, "the Grand Pelican Hotel"),
                       (345, 150, "Bayside"), (345, -150, "Lighthouse Point")):
        b.landmark(float(x), float(z), name)
    b.camera(-170.0, 40.0, -60.0, PIVOT_X, 0.0, -150.0)
    b.camera(-232.0, 30.0, 40.0, -300.0, 6.0, -10.0)
    b.camera(60.0, 46.0, -110.0, 0.0, 4.0, -210.0)
    b.camera(100.0, 50.0, 40.0, 190.0, 12.0, 150.0)


def _keep(area) -> None:
    KEEP.append(area)


def _blocked(x: float, z: float) -> bool:
    if CUT[0] - 4 < x < CUT[1] + 4 or z < SEA_EDGE + 3:
        return True
    return any(k[0] - 2 < x < k[1] + 2 and k[2] - 2 < z < k[3] + 2 for k in KEEP)


def _smooth(k: float) -> float:
    k = max(0.0, min(1.0, k))
    return k * k * (3.0 - 2.0 * k)


# ==================================================================== land
def _land() -> Land:
    """The town's ground: the beach rising from the bay, swells through the
    middle, Chapel Hill in the south-east, the headland's rock."""
    hx, hz = HALF
    land = Land(rect(-hx, hx, -hz, hz), cell=10.0, step=1.0)

    def shape(x: float, z: float) -> float:
        if x < CUT[0]:
            # the west bank: the harbour gardens' knoll between the yards
            kx, kz, kh, krx, krz = KNOLL
            knoll = kh * _smooth(1.0 - math.hypot((x - kx) / krx, (z - kz) / krz))
            return max(0.0, knoll + 1.0 + 1.4 * math.sin(x / 23.0 + 1.0) * math.cos(z / 19.0))
        roll = 2.4 * math.sin(x / 47.0 + 0.3) * math.cos(z / 39.0) + 1.6 * math.cos(x / 29.0 - z / 61.0)
        rise = 5.0 * _smooth((z - SEA_EDGE) / 70.0)
        hx0, hz0, hh, hr = HILL
        hill = hh * _smooth(1.0 - math.hypot(x - hx0, z - hz0) / hr)
        head = 0.0
        if HEADLAND[0] - 20 < x < HEADLAND[1] + 20 and z < SEA_EDGE + 30:
            head = 10.0 * _smooth(1.0 - abs(x - (HEADLAND[0] + HEADLAND[1]) / 2.0) / 60.0)
        return max(0.0, rise * (2.0 + roll * 0.6) / 2.0 + roll * 0.5 + hill + head)

    land.add(shape)
    # the cottages, the chapel and the mill on Chapel Hill, each on a level
    # terrace of its own at the height the hill has there
    HILL_Y.clear()
    for x, z in HILL_SPOTS:
        y = float(round(land.height(x, z)))
        land.flatten(rect(x - 8.0, x + 8.0, z - 7.0, z + 7.0), y, blend=6.0)
        HILL_Y[(x, z)] = y
    hx0, hz0 = HILL[0], HILL[1]
    y = float(round(land.height(hx0, hz0)))
    land.flatten(rect(hx0 - 12.0, hx0 + 12.0, hz0 - 30.0, hz0 + 6.0), y, blend=8.0)
    HILL_Y["chapel"] = y
    y = float(round(land.height(*MILL_SPOT)))
    land.flatten(rect(MILL_SPOT[0] - 7.0, MILL_SPOT[0] + 7.0, MILL_SPOT[1] - 7.0, MILL_SPOT[1] + 7.0), y, blend=6.0)
    HILL_Y["mill"] = y
    land.cut(rect(CUT[0], CUT[1], -hz, hz))
    land.cut(rect(-hx, HEADLAND[0], -hz, SEA_EDGE))
    land.cut(rect(HEADLAND[1], hx, -hz, SEA_EDGE))
    fz = FOOTBRIDGE_Z
    flats = [(rect(-266.0, CUT[0], -205.0, 250.0), 0.0, 10.0),       # the promenade along the Cut
             (rect(-400.0, -298.0, -180.0, -130.0), 0.0, 10.0),      # the wharf yard
             (rect(-400.0, -290.0, -205.0, -178.0), 0.0, 8.0),       # the lifeboats, the boat sheds
             (rect(-400.0, -298.0, 130.0, 180.0), 0.0, 10.0),        # the cannery yard
             (rect(-400.0, -262.0, 186.0, 250.0), 0.0, 8.0),         # its stores and the smokehouse
             (rect(-388.0, -346.0, -122.0, -82.0), 0.6, 6.0),        # the crazy golf
             (rect(-388.0, -346.0, 82.0, 122.0), 0.0, 6.0),          # the boating pond
             (rect(-400.0, -384.0, -122.0, 122.0), 0.0, 8.0),        # the harbour houses
             (rect(CONTROL[0] - 4.0, CONTROL[1] + 4.0, CONTROL[2] - 6.0, CONTROL[3] + 6.0), 0.0, 10.0),
             (rect(KNOLL[0] - 12.0, KNOLL[0] + 12.0, -12.0, 12.0), KNOLL[2], 10.0),   # the bandstand
             (rect(-322.0, -302.0, 26.0, 46.0), 4.0, 8.0),           # the floral clock's terrace
             (rect(-322.0, -302.0, -46.0, -26.0), 4.0, 8.0),         # the topiary pelican's
             (rect(-286.0, -250.0, -fz - 4.0, -fz + 4.0), 0.0, 6.0),
             (rect(-286.0, -250.0, fz - 4.0, fz + 4.0), 0.0, 6.0),
             (rect(CUT[1], CUT[1] + 30.0, -205.0, 250.0), 0.0, 14.0),  # the east bank's quay
             (SQUARE, 1.0, 18.0),
             (rect(-82.0, -54.0, 34.0, 60.0), 1.0, 8.0), (rect(-82.0, -54.0, -60.0, -34.0), 1.0, 8.0),
             (rect(38.0, 66.0, -68.0, -42.0), 1.0, 8.0), (rect(38.0, 66.0, 42.0, 68.0), 1.0, 8.0),
             (rect(-32.0, -6.0, 48.0, 72.0), 1.0, 8.0), (rect(6.0, 32.0, -72.0, -48.0), 1.0, 8.0),
             (rect(CANNERY[0] - 10.0, CANNERY[1] + 60.0, CANNERY[2] - 10.0, 250.0), 0.0, 12.0),
             (rect(-170.0, -110.0, -205.0, -186.0), 0.0, 8.0),       # the pleasure pier's head
             (rect(-50.0, 110.0, -205.0, -160.0), 0.0, 10.0),        # the harbour front
             (rect(270.0, 310.0, -246.0, -210.0), 10.0, 6.0),         # the lighthouse's crown
             (rect(240.0, 400.0, -120.0, 120.0), 0.0, 14.0),          # the hotel and the stations
             (rect(296.0, 400.0, -205.0, -120.0), 0.0, 10.0),
             (rect(296.0, 400.0, 120.0, 250.0), 0.0, 10.0)]
    for area, y, blend in flats:
        land.flatten(area, y, blend)
    common.plan_depots(land, DEPOTS, LANE_OF, YS, BASES)
    common.plan_coal(land, COAL, BASES)
    for path in LANES:
        land.pin_path(path, YS, half=7.5, blend=12.0)

    def paint(x: float, z: float, h: float):
        if z < SEA_EDGE + 22 and h < 4.0 and x > CUT[1]:
            return SAND
        if HEADLAND[0] - 10 < x < HEADLAND[1] + 10 and z < SEA_EDGE + 16:
            return STONE if h > 6 else STONE_DARK
        if SQUARE[0] <= x <= SQUARE[1] and SQUARE[2] <= z <= SQUARE[3]:
            return COBBLE
        if h >= 12.0:
            return GRASS_LIGHT
        if h < 1.5:
            return GRASS_DEEP
        return None

    land.colour(paint)
    return land


# =================================================================== water
def _water(b: ArenaArea, rng: random.Random) -> None:
    """The bay along the north and the Cut down the west: stone quays, the
    beach running into the shallows, deep water under it all."""
    hx, hz, m = b.half_x, b.half_z, b.margin
    # the bay's floor and its water, out to the breakwater under the edge.
    # Nobody stands on the floors of the deep water -- the harbour has you
    # long before -- so they are not solid; the only solid thing under the
    # water is far down (DEEP_Y), deeper than any bot will choose to drop,
    # so no bot's route goes down into the water hoping for a way out.
    for r in carve(rect(-hx, hx, -hz, SEA_EDGE), [HEADLAND]):
        if r[3] - r[2] < 0.1:
            continue
        slab(b, r, FLOOR_Y, 2.0, "#3a5a5a", collide=False)
        slab(b, r, DEEP_Y, 1.0, "#1a2a2a")
        b.water((r[0] + r[1]) / 2.0, (r[2] + r[3]) / 2.0, r[1] - r[0], r[3] - r[2], WATER_Y + 0.8, WATER)
    # the Cut: its floor, its water, quay walls down both sides
    slab(b, rect(CUT[0], CUT[1], SEA_EDGE, hz), FLOOR_Y, 2.0, "#3a5a5a", collide=False)
    slab(b, rect(CUT[0], CUT[1], SEA_EDGE, hz), DEEP_Y, 1.0, "#1a2a2a")
    b.water((CUT[0] + CUT[1]) / 2.0, (SEA_EDGE + hz) / 2.0, CUT[1] - CUT[0], hz - SEA_EDGE, WATER_Y + 0.8, WATER)
    for x, side in ((CUT[0] + 0.8, -1.0), (CUT[1] - 0.8, 1.0)):
        b.box([x, (FLOOR_Y + 0.0) / 2.0, (SEA_EDGE - 0.4 + hz) / 2.0], [1.6, -FLOOR_Y, hz - SEA_EDGE + 0.4], STONE)
        b.box([x, 0.3, (SEA_EDGE - 0.4 + hz) / 2.0], [2.0, 0.6, hz - SEA_EDGE + 0.4], STONE_DARK)
    # the Cut's south end closed under the edge, and the bay's shore: a
    # stone quay west of the Cut, the beach east of it
    slab(b, rect(CUT[0], CUT[1], hz, hz + m), -6.0, -FLOOR_Y - 6.0 + 2.0, STONE_DARK)
    b.box([(-hx + CUT[0]) / 2.0, FLOOR_Y / 2.0 + 0.01, SEA_EDGE - 0.8], [CUT[0] + hx, -FLOOR_Y - 0.02, 1.6], STONE)
    b.box([(-hx + CUT[0]) / 2.0, 0.3, SEA_EDGE - 0.8], [CUT[0] + hx, 0.6, 2.0], STONE_DARK)
    # the shallows off the beach: two steps of sand, then the deep
    for k, (y, w) in enumerate(((-1.0, 8.0), (-2.0, 8.0))):
        z0 = SEA_EDGE - 8.0 * (k + 1)
        for x0, x1 in ((CUT[1], HEADLAND[0]), (HEADLAND[1], hx)):
            slab(b, rect(x0, x1, z0, z0 + w), y, -FLOOR_Y + y, SAND, studs=True)
    # bollards along the quays
    for z in range(-180, 240, 30):
        b.cyl([CUT[1] + 2.2, 1.0, float(z)], [1.0, 2.0, 1.0], "#2a2a2e", material="metal")
        b.cyl([CUT[0] - 2.2, 1.0, float(z)], [1.0, 2.0, 1.0], "#2a2a2e", material="metal")


# ==================================================================== edge
def _edge(b: ArenaArea, rng: random.Random) -> None:
    """A breakwater of great rocks along the bay's edge (the sea goes on
    beyond it, islands on the horizon), green downs round the rest."""
    hx, hz, m = b.half_x, b.half_z, b.margin
    room_walls(b, rect(-hx - m, hx + m, -hz - m, hz + m), m, 0.0, 18.0, "#6a8a4a", sides=("x-", "x+", "z+"))
    for i in range(40):
        x = -hx + (i + 0.5) * (2 * hx) / 40.0
        h = 12.0 + (i * 7 % 5)
        b.box([x, FLOOR_Y + (h - FLOOR_Y) / 2.0 + 0.003 * (i % 3), -hz - m / 2.0],
              [2 * hx / 40.0, h - FLOOR_Y, m - 0.04 * (i % 2)], ("#8a8478", "#9a9488", "#7a7468")[i % 3])
    # the open sea beyond, to the horizon, and its islands
    b.box([0.0, WATER_Y - 0.4, -hz - m - 300.0], [1600.0, 0.8, 600.0], WATER, collide=False, material="glass",
          alpha=0.85)
    for k, (x, z, w, h) in enumerate(((-260.0, -560.0, 120.0, 40.0), (180.0, -620.0, 160.0, 60.0),
                                      (420.0, -520.0, 90.0, 30.0))):
        b.sphere([x, WATER_Y - h * 0.3, z], [w, h * 1.6, w * 0.6], "#5a7a4a", collide=False)
    backdrop(b, "hills", 0.0, rng, ["#6a9a4a", "#7aa852", "#5a8a42"], sides=("x-", "x+", "z+"), depth=180.0)
    for side in (-1, 1):
        for i in range(10):
            z = -hz + (i + 0.5) * (2 * hz) / 10.0
            b.box([side * (hx + m / 2.0), 18.0 + 3.0, z], [m + 1.0 + (i % 3) * 0.13, 6.0, 2 * hz / 10.0 - 1.0],
                  "#7aa852", collide=False)


# ================================================================ bridges
def _bridges(b: ArenaArea) -> None:
    """A swing bridge on each line over the Cut: a steel deck on a round
    stone pier in mid-channel -- closed, lying along the line; open, turned
    along the channel -- its gate posts and lamps at the banks.  Both are
    worked from the control house on the west bank, halfway between."""
    x0, x1 = SPAN
    for lane, z in (("a", -150.0), ("b", 150.0)):
        b.cyl([PIVOT_X, (FLOOR_Y - 1.2) / 2.0, z], [12.0, -1.2 - FLOOR_Y, 12.0], STONE)
        b.cyl([PIVOT_X, -1.3, z], [12.6, 0.2, 12.6], STONE_DARK, collide=False)
        # the turning ring the deck rides on, yellow between pier and deck
        b.cyl([PIVOT_X, (-1.2 + rails.BALLAST_TOP - 1.0) / 2.0, z],
              [9.0, rails.BALLAST_TOP - 1.0 + 1.2, 9.0], "#e8b23a", collide=False, material="metal")
        for opened in (False, True):
            with b.detached() as parts:
                if not opened:
                    deck = rect(x0, x1, z - 6.0, z + 6.0)
                    slab(b, deck, rails.BALLAST_TOP, 1.0, RED, studs=True, material="metal")
                    lay_track(b, [(x0, z), (x1, z)], skip=[(0.0, 999.0)])
                    for e in (-1.0, 1.0):
                        for x in range(int(x0) + 3, int(x1), 7):
                            b.box([float(x), rails.BALLAST_TOP + 1.3, z + e * 5.6], [0.5, 2.6, 0.5], TRIM,
                                  material="metal")
                        b.box([(x0 + x1) / 2.0, rails.BALLAST_TOP + 2.8, z + e * 5.6], [x1 - x0 - 1.0, 0.4, 0.4],
                              TRIM, material="metal")
                else:
                    deck = rect(PIVOT_X - 6.0, PIVOT_X + 6.0, z - 26.0, z + 26.0)
                    slab(b, deck, rails.BALLAST_TOP, 1.0, RED, studs=True, material="metal")
                    lay_track(b, [(PIVOT_X, z - 26.0), (PIVOT_X, z + 26.0)], skip=[(0.0, 999.0)])
                    for e in (-1.0, 1.0):
                        for zz in range(int(z) - 23, int(z) + 26, 7):
                            b.box([PIVOT_X + e * 5.6, rails.BALLAST_TOP + 1.3, float(zz)], [0.5, 2.6, 0.5], TRIM,
                                  material="metal")
                        b.box([PIVOT_X + e * 5.6, rails.BALLAST_TOP + 2.8, z], [0.4, 0.4, 51.0], TRIM,
                              material="metal")
            b.dynamic("bridge_%s_%s" % (lane, "up" if opened else "down"), parts, on=not opened,
                      group="bridge_%s" % lane)
        # the gate posts and their lamps at both banks
        for x in (x0 - 2.0, x1 + 2.0):
            for e in (-1.0, 1.0):
                b.box([x, 3.0, z + e * 7.6], [0.8, 6.0, 0.8], TRIM)
                b.box([x, 6.4, z + e * 7.6], [1.2, 1.2, 1.2], "#2a2a2e", material="metal", collide=False)
        _keep(rect(x0 - 6.0, x1 + 6.0, z - 11.0, z + 11.0))


def _footbridge(b: ArenaArea, land: Land) -> None:
    """The footbridges high over the Cut, for when the bridges are open:
    lattice towers on each bank, a stair up each, the walkway between --
    one north of the control house, one south."""
    y = FOOTBRIDGE_Y
    for z in (-FOOTBRIDGE_Z, FOOTBRIDGE_Z):
        slab(b, rect(CUT[0] - 6.0, CUT[1] + 6.0, z - 2.5, z + 2.5), y, 0.6, NAVY, material="metal")
        for e in (-1.0, 1.0):
            b.box([(CUT[0] + CUT[1]) / 2.0, y + 1.4, z + e * 2.3], [CUT[1] - CUT[0] + 12.0, 0.3, 0.3], TRIM,
                  material="metal")
            for k in range(1, 6):
                b.box([CUT[0] - 6.0 + k * (CUT[1] - CUT[0] + 12.0) / 6.0, y + 0.7, z + e * 2.3], [0.3, 1.1, 0.3],
                      TRIM, material="metal")
        for x in (CUT[0] - 4.0, CUT[1] + 4.0):
            for e in (-1.0, 1.0):
                b.box([x, (y - 0.6) / 2.0, z + e * 2.0], [0.8, y - 0.6, 0.8], NAVY, material="metal")
        for x0, x1 in ((CUT[0] - 6.0, CUT[0] - 30.0), (CUT[1] + 6.0, CUT[1] + 30.0)):
            g = land.height(x1, z)
            flight(b, "x", x1, x0, z - 2.5, z + 2.5, g, y, NAVY, fill=g - 0.3)
        # a lifebelt on each tower
        b.cyl([CUT[0] - 4.0, 9.0, z - 2.5], [2.4, 0.4, 2.4], "#ff6a3a", r=[math.pi / 2.0, 0, 0], collide=False)
        b.mark("perch", (CUT[0] + CUT[1]) / 2.0, y, z)
        _keep(rect(CUT[0] - 32.0, CUT[1] + 32.0, z - 4.0, z + 4.0))


# ========================================================= control house
def _control_house(b: ArenaArea) -> None:
    """The Cut control house on the west quay, halfway between the bridges:
    cream walls, a red roof, a clock tower with a face to every quarter and
    a cockerel on top.  Inside, a wheel for each bridge against the wall on
    the Cut side -- No. 1 (the Shore line's) at the north end, No. 2 (the
    Cannery line's) at the south -- so both companies come running to the
    same room."""
    x0, x1, z0, z1 = CONTROL
    cream = "#f4ecd8"
    building(b, CONTROL, 0.0, 9.0, cream, roof_colour=RED, floor_colour="#8a6a4a",
             doors={"z-": [(-287.0, -279.0, 7.0)], "z+": [(-287.0, -279.0, 7.0)], "x-": [(-3.0, 3.0, 7.0)]},
             windows={"x+": [(-4.0, 4.0, 3.6, 7.6)],
                      "x-": [(-12.0, -6.0, 3.4, 6.8), (6.0, 12.0, 3.4, 6.8)],
                      "z-": [(-297.0, -291.0, 3.4, 6.8), (-275.0, -271.0, 3.4, 6.8)],
                      "z+": [(-297.0, -291.0, 3.4, 6.8), (-275.0, -271.0, 3.4, 6.8)]},
             glass=True, lights=WARM)
    for side in ("z-", "z+"):
        threshold(b, CONTROL, side, (-287.0, -279.0))
    threshold(b, CONTROL, "x-", (-3.0, 3.0))
    gable(b, CONTROL, 10.2, RED, "z", 3, 1.2, 0.6)
    # navy quoins and plinth, window boxes in flower, canopies over the doors
    for xx in (x0 - 0.3, x1 + 0.3):
        for zz in (z0 - 0.3, z1 + 0.3):
            b.box([xx, 4.5, zz], [1.4, 9.0, 1.4], NAVY)
    for zz in (z0 - 0.25, z1 + 0.25):
        for a, c in ((x0 + 0.8, -287.4), (-278.6, x1 - 0.8)):
            b.box([(a + c) / 2.0, 0.4, zz], [c - a, 0.8, 0.5], NAVY)
    b.box([x1 + 0.25, 0.4, (z0 + z1) / 2.0], [0.5, 0.8, z1 - z0 - 1.6], NAVY)
    for a, c in ((z0 + 0.8, -3.4), (3.4, z1 - 0.8)):
        b.box([x0 - 0.25, 0.4, (a + c) / 2.0], [0.5, 0.8, c - a], NAVY)
    for zz in (-9.0, 9.0):
        b.box([x0 - 0.9, 3.0, zz], [1.2, 0.6, 6.4], "#8a5a3a")
        b.sphere([x0 - 0.9, 3.6, zz], [1.2, 0.8, 6.0], ("#ff6a8a", "#ffd84a")[zz > 0], collide=False)
    for zz, e in ((z0, -1.0), (z1, 1.0)):
        b.box([-283.0, 7.6, zz + e * 1.6], [12.4, 0.4, 3.2], RED)
        for xx in (-288.8, -277.2):
            b.box([xx, 3.7, zz + e * 2.9], [0.4, 7.4, 0.4], TRIM)
    # the wheels, the boards over them naming the bridges
    inner = x1 - 2.0
    for lane, z, name in (("a", -8.0, "No.1  SHORE LINE"), ("b", 8.0, "No.2  CANNERY LINE")):
        wx = inner - 2.3
        b.box([wx, 1.6, z], [3.0, 3.2, 3.4], "#4a4a4e", material="metal")
        b.cyl([wx, 3.9, z], [2.2, 3.0, 2.2], "#e8b23a", r=[math.pi / 2.0, 0, 0], collide=False, material="metal")
        b.cyl([wx - 1.65, 2.2, z], [3.6, 0.3, 3.6], "#c8902a", r=[0, 0, math.pi / 2.0], collide=False,
              material="metal")
        for k in range(4):
            b.box([wx - 1.85, 2.2, z], [0.2, 4.6, 0.36], "#8a5a2a", r=[k * math.pi / 4.0, 0, 0], collide=False)
        wall_sign(b, inner - 0.36, 6.4, z, 6.6, 1.5, sign_decal(name, TRIM, NAVY, 6.0), "x-", TRIM)
        b.mark("winch", wx - 4.0, 1.0, z, lane=lane)
    # the tender's desk, the stove, the harbour chart on the wall
    b.box([x0 + 4.0, 1.4, -2.0], [3.0, 0.3, 6.0], WOOD)
    b.box([x0 + 4.0, 0.6, -2.0], [2.6, 1.2, 5.6], WOOD_DARK)
    b.cyl([x0 + 4.0, 1.0, 6.0], [2.0, 2.0, 2.0], "#2a2a2e", material="metal")
    b.cyl([x0 + 4.0, 5.5, 6.0], [0.6, 7.0, 0.6], "#2a2a2e", material="metal", collide=False)
    wall_sign(b, x0 + 2.36, 5.0, -2.0, 5.0, 3.0, sign_decal("THE CUT", "#d8e8f0", NAVY, 5.0), "x+", "#d8e8f0")
    wall_sign(b, x1 + 0.36, 8.2, 0.0, 14.0, 1.6, sign_decal("CUT CONTROL", NAVY, TRIM, 9.0), "x+", NAVY)
    # the clock tower over the ridge
    tx, tz = -284.0, 0.0
    b.box([tx, 17.2, tz], [6.2, 15.6, 6.2], cream)
    b.box([tx, 25.0, tz], [7.0, 0.6, 7.0], NAVY)
    b.box([tx, 12.2, tz], [6.6, 0.5, 6.6], NAVY)
    b.cone([tx, 27.8, tz], [7.4, 5.0, 7.4], NAVY)
    for yaw, dx, dz in ((math.pi / 2.0, 1.0, 0.0), (-math.pi / 2.0, -1.0, 0.0), (0.0, 0.0, 1.0),
                        (math.pi, 0.0, -1.0)):
        cx, cz = tx + dx * 3.1, tz + dz * 3.1
        rot = [0, 0, math.pi / 2.0] if dx else [math.pi / 2.0, 0, 0]
        b.cyl([cx + dx * 0.05, 20.6, cz + dz * 0.05], [5.6, 0.3, 5.6], NAVY, r=rot, collide=False)
        b.cyl([cx + dx * 0.2, 20.6, cz + dz * 0.2], [4.8, 0.3, 4.8], "#fbf6e8", r=rot, collide=False)
        CLOCKS.append(((cx + dx * 0.36, 20.6, cz + dz * 0.36), yaw, 0.0, 2.2))
    VANES.append((tx, 30.3, tz))
    # the flagstaff at the north-west corner
    b.cyl([x0 - 2.0, 8.0, z0 - 2.0], [0.6, 16.0, 0.6], TRIM, material="metal")
    FLAGS.append(((x0 - 2.0, 15.4, z0 - 2.0), [RED, TRIM, NAVY]))
    for x, z in ((x0 - 2.0, z0 - 6.0), (x0 - 2.0, z1 + 6.0)):
        lamp_post(b, x, z, 9.0, light=WARM)
    _keep(rect(x0 - 4.0, x1 + 4.0, z0 - 8.0, z1 + 8.0))


# ============================================================= promenade
def _promenade(b: ArenaArea, rng: random.Random) -> None:
    """The west quay's promenade: benches looking over the Cut, lamps, two
    old cannons either side of the control house, and narrowboats moored
    along the quay -- painted bright, flowers on their roofs, stoves lit."""
    for z in (-118.0, -98.0, -46.0, -32.0, 32.0, 46.0, 98.0, 118.0):
        x = -258.6
        b.box([x, 1.2, z], [1.6, 0.4, 5.0], WOOD)
        for e in (-1.0, 1.0):
            b.box([x, 0.5, z + e * 2.0], [1.4, 1.0, 0.5], "#2a2a2e", material="metal")
        b.box([x - 0.95, 2.1, z], [0.3, 1.4, 5.0], WOOD)
        _keep(rect(x - 2.0, x + 2.0, z - 3.0, z + 3.0))
    for z in (-112.0, -30.0, 30.0, 112.0):
        lamp_post(b, -263.0, z, 10.0, light=WARM)
    for z in (-24.0, 24.0):
        b.box([-262.0, 0.6, z], [3.2, 1.2, 2.4], "#5a4030")
        b.cyl([-260.6, 1.9, z], [1.2, 5.4, 1.2], "#2a2a2e", r=[0, 0, math.pi / 2.0], collide=False, material="metal")
        b.sphere([-263.4, 1.9, z], [1.4, 1.4, 1.4], "#2a2a2e", collide=False, material="metal")
        for e in (-1.0, 1.0):
            b.cyl([-262.0, 0.9, z + e * 1.35], [1.8, 0.3, 1.8], "#3a2a1e", r=[math.pi / 2.0, 0, 0], collide=False)
        for k in range(3):
            b.sphere([-264.8 + (k % 2) * 0.9, 0.5 + (k // 2) * 0.8, z + 0.5 - (k % 2)], [1.0, 1.0, 1.0], "#2a2a2e",
                     collide=False, material="metal")
        _keep(rect(-266.0, -258.0, z - 3.0, z + 3.0))
    # the narrowboats along the quay
    for k, (zc, hull, trim) in enumerate(((-100.0, RED, "#fbe49a"), (-38.0, "#2a7a5a", "#f4b8c8"),
                                          (38.0, NAVY, "#f8c89a"), (100.0, "#e8b23a", "#2a3a6a"))):
        x0, x1 = CUT[0] + 2.0, CUT[0] + 7.2
        xc = (x0 + x1) / 2.0
        b.box([xc, -1.1, zc], [x1 - x0, 3.0, 24.0], "#1e1e24")
        b.box([xc, 0.15, zc], [x1 - x0 + 0.1, 0.5, 23.6], hull, collide=False)
        b.box([xc, 1.8, zc + 1.0], [3.6, 2.8, 15.0], hull)
        b.box([xc, 3.35, zc + 1.0], [3.9, 0.3, 15.4], "#3a3a40")
        for e in (-1.0, 1.0):
            for w in range(4):
                b.box([xc + e * 1.85, 2.2, zc - 4.8 + w * 3.6], [0.12, 1.0, 1.8], trim, collide=False)
        b.box([xc, 1.0, zc - 9.0], [2.0, 1.2, 0.3], trim, collide=False)
        b.box([xc, 1.2, zc - 11.0], [0.3, 1.6, 0.3], WOOD_DARK, collide=False)
        b.cyl([xc + 1.0, 4.3, zc + 6.0], [0.7, 1.6, 0.7], "#2a2a2e", material="metal")
        SMOKES.append((xc + 1.0, 5.2, zc + 6.0))
        for f in range(3):
            fz = zc - 4.0 + f * 3.2
            b.cyl([xc - 0.8, 3.85, fz], [1.0, 0.7, 1.0], "#a86a3a", collide=False)
            b.sphere([xc - 0.8, 4.5, fz], [1.2, 0.8, 1.2], ("#ff6a8a", "#ffd84a", "#c86aff")[(f + k) % 3],
                     collide=False)
        b.cyl([xc, 1.9, zc + 8.8], [1.6, 0.3, 1.6], "#ff6a3a", r=[math.pi / 2.0, 0, 0], collide=False)
        _keep(rect(x0 - 1.0, x1 + 1.0, zc - 13.0, zc + 13.0))


# =============================================================== gardens
def _palm(b: ArenaArea, x: float, z: float, base: float, h: float = 10.0) -> None:
    """A cabbage palm: a ringed trunk, a burst of spiky fronds at the top."""
    n = 5
    for k in range(n):
        b.cyl([x + k * 0.12, base + h * (k + 0.5) / n, z], [1.3 - k * 0.1, h / n + 0.05, 1.3 - k * 0.1],
              ("#8a6a48", "#7a5a3a")[k % 2], collide=(k == 0))
    top = base + h
    for k in range(8):
        a = k * math.pi / 4.0
        b.box([x + 0.5 + math.cos(a) * 1.6, top + 0.3, z + math.sin(a) * 1.6], [4.4, 0.25, 0.9], "#4e8a3a",
              r=[0, -a, -0.45], collide=False)
    b.sphere([x + 0.5, top, z], [1.6, 1.4, 1.6], "#5a9a42", collide=False)


def _gardens(b: ArenaArea, rng: random.Random, land: Land) -> None:
    """The harbour gardens on the knoll behind the control house: the
    bandstand on top (strings of lights out to the lamps round it), rings
    of bedding plants, a floral clock telling the time on its terrace, a
    pelican clipped out of box hedge on the other, palms."""
    kx, kz, kh = KNOLL[0], KNOLL[1], KNOLL[2]
    # the bandstand
    b.cyl([kx, kh + 0.6, kz], [17.0, 1.2, 17.0], STONE)
    b.cyl([kx, kh + 1.25, kz], [15.6, 0.1, 15.6], "#c8a070", collide=False)
    for k in range(8):
        a = k * math.pi / 4.0 + math.pi / 8.0
        b.cyl([kx + math.cos(a) * 6.8, kh + 4.2, kz + math.sin(a) * 6.8], [0.6, 6.0, 0.6], TRIM, material="metal")
    b.cyl([kx, kh + 7.6, kz], [16.4, 0.8, 16.4], TRIM)
    b.cone([kx, kh + 10.2, kz], [17.2, 4.4, 17.2], RED)
    b.cone([kx, kh + 11.9, kz], [6.4, 1.8, 6.4], TRIM)
    b.sphere([kx, kh + 13.1, kz], [1.2, 1.2, 1.2], "#e8b23a", material="metal", collide=False)
    b.mark("perch", kx + 3.0, kh + 1.2, kz)
    _keep(rect(kx - 10.0, kx + 10.0, kz - 10.0, kz + 10.0))
    for k in range(4):
        a = k * math.pi / 2.0 + math.pi / 4.0
        lx, lz = kx + math.cos(a) * 22.0, kz + math.sin(a) * 22.0
        ly = land.height(lx, lz)
        lamp_post(b, lx, lz, 10.0, light=WARM, y=ly)
        LIGHTS.append(((kx + math.cos(a) * 8.0, kh + 7.4, kz + math.sin(a) * 8.0), (lx, ly + 10.0, lz)))
        _keep(rect(lx - 2.0, lx + 2.0, lz - 2.0, lz + 2.0))
    # the bedding: two rings of raised beds, gaps for the paths
    for ring, (r, cols) in enumerate(((19.0, ("#ff4a5a", "#ffffff")), (31.0, ("#ffd84a", "#a86aff")))):
        n = int(2 * math.pi * r / 4.6)
        for k in range(n):
            a = k * 2 * math.pi / n
            if min(abs(((a + math.pi / 4.0) % (math.pi / 2.0)) - math.pi / 4.0), 9.0) < 0.2:
                continue
            x, z = kx + math.cos(a) * r, kz + math.sin(a) * r * 1.2
            if CONTROL[0] - 6.0 < x or abs(z) > 92.0:
                continue
            h = min(land.height(x - 1.3, z - 1.3), land.height(x + 1.3, z + 1.3),
                    land.height(x - 1.3, z + 1.3), land.height(x + 1.3, z - 1.3))
            top = max(land.height(x - 1.3, z - 1.3), land.height(x + 1.3, z + 1.3),
                      land.height(x - 1.3, z + 1.3), land.height(x + 1.3, z - 1.3))
            b.box([x, (h - 0.4 + top + 0.7) / 2.0, z], [2.6, top + 0.7 - h + 0.4, 2.6], STONE_DARK)
            b.box([x, top + 0.9, z], [2.2, 0.4, 2.2], cols[k % 2], studs=True)
            _keep(rect(x - 2.0, x + 2.0, z - 2.0, z + 2.0))
    # the floral clock on its terrace, tipped to the promenade
    cx, cz, cy = -312.0, 36.0, 4.0
    b.cyl([cx, cy + 1.15, cz], [17.0, 2.3, 17.0], STONE)
    tilt = 0.21
    for k, (rad, col) in enumerate(((16.0, "#3a8a3a"), (14.2, "#ff4a5a"), (11.6, "#ffffff"), (9.0, "#ffd84a"),
                                    (6.4, "#a86aff"), (3.6, "#ff8a3a"))):
        b.cyl([cx, cy + 2.35 + k * 0.05, cz], [rad, 0.3, rad], col, r=[0, 0, -tilt], collide=False)
    for k in range(12):
        a = k * math.pi / 6.0
        nx, nz = cx - math.cos(a) * 7.4, cz + math.sin(a) * 7.4
        b.box([nx, cy + 2.75 + (cx - nx) * math.tan(tilt), nz], [0.9, 0.3, 0.9] if k % 3 else [1.4, 0.3, 1.4],
              "#1a1a1e", r=[0, 0, -tilt], collide=False)
    CLOCKS.append(((cx, cy + 3.0, cz), math.pi / 2.0, math.pi / 2.0 - tilt, 7.0))
    _keep(rect(cx - 10.0, cx + 10.0, cz - 10.0, cz + 10.0))
    # the topiary pelican on the other terrace
    px, pz, py = -312.0, -36.0, 4.0
    b.box([px, py + 1.15, pz], [16.0, 2.3, 8.0], STONE)
    hedge = "#3a7a3a"
    b.sphere([px, py + 5.4, pz], [8.0, 6.4, 5.4], hedge, collide=False)
    b.sphere([px + 4.2, py + 9.0, pz], [2.0, 5.0, 2.0], hedge, collide=False)
    b.sphere([px + 4.6, py + 11.8, pz], [3.0, 2.8, 2.8], hedge, collide=False)
    b.box([px + 6.4, py + 11.3, pz], [3.2, 1.1, 1.6], "#e8a830", collide=False)
    b.sphere([px + 6.2, py + 10.5, pz], [2.6, 1.4, 1.5], "#d8902a", collide=False)
    b.sphere([px - 1.0, py + 6.0, pz - 2.6], [6.4, 3.0, 1.4], "#2e6a2e", collide=False)
    b.sphere([px - 1.0, py + 6.0, pz + 2.6], [6.4, 3.0, 1.4], "#2e6a2e", collide=False)
    b.sphere([px + 5.4, py + 12.4, pz - 1.0], [0.5, 0.5, 0.5], "#1a1a1a", collide=False)
    b.sphere([px + 5.4, py + 12.4, pz + 1.0], [0.5, 0.5, 0.5], "#1a1a1a", collide=False)
    _keep(rect(px - 8.0, px + 8.0, pz - 6.0, pz + 6.0))
    # palms round the gardens and along the promenade
    for x, z in ((-300.0, -60.0), (-300.0, 60.0), (-356.0, -44.0), (-356.0, 44.0), (-344.0, -80.0),
                 (-344.0, 80.0), (-262.0, -84.0), (-262.0, 84.0), (-262.0, -136.0), (-262.0, 136.0)):
        if any(k[0] - 2 < x < k[1] + 2 and k[2] - 2 < z < k[3] + 2 for k in KEEP):
            continue
        _palm(b, x, z, land.height(x, z) - 0.2, 10.0 + (abs(int(x + z)) % 3) * 1.5)
        _keep(rect(x - 2.0, x + 2.0, z - 2.0, z + 2.0))


# ============================================================= lifeboats
def _lifeboats(b: ArenaArea, rng: random.Random) -> None:
    """The lifeboat station on the bay: the boathouse, its doors open on the
    slipway, the lifeboat on its cradle ready to go, and the coastguard's
    lookout beside it with a stair up (a perch over the yard)."""
    x0, x1, z0, z1 = LIFEBOAT
    building(b, LIFEBOAT, 0.0, 11.0, TRIM, roof_colour=RED, floor_colour="#8a7a6a",
             doors={"z-": [(x0 + 6.0, x1 - 6.0, 9.0)], "z+": [(x0 + 4.0, x0 + 8.0, 6.4)]},
             windows={"x-": [(z0 + 4.0, z0 + 8.0, 4.0, 7.0), (z1 - 8.0, z1 - 4.0, 4.0, 7.0)],
                      "x+": [(z0 + 4.0, z0 + 8.0, 4.0, 7.0), (z1 - 8.0, z1 - 4.0, 4.0, 7.0)]},
             glass=True, lights=WARM)
    threshold(b, LIFEBOAT, "z-", (x0 + 6.0, x1 - 6.0))
    threshold(b, LIFEBOAT, "z+", (x0 + 4.0, x0 + 8.0))
    gable(b, LIFEBOAT, 12.2, RED, "z", 3, 1.2, 0.6)
    wall_sign(b, (x0 + x1) / 2.0, 10.6, z0 - 0.36, 16.0, 1.4, sign_decal("LIFEBOAT", RED, TRIM, 8.0), "z-", RED)
    # the lifeboat on its cradle, bow to the sea
    cx = (x0 + x1) / 2.0
    b.box([cx, 0.5, (z0 + z1) / 2.0], [3.0, 1.0, 12.0], "#5a4a3a")
    b.box([cx, 2.4, (z0 + z1) / 2.0], [5.0, 2.8, 13.0], "#2a4a8a")
    b.box([cx, 3.9, (z0 + z1) / 2.0], [5.2, 0.3, 13.2], "#ff6a2a")
    b.box([cx, 5.4, (z0 + z1) / 2.0 + 1.5], [3.4, 2.8, 5.0], "#ff6a2a")
    b.box([cx, 7.0, (z0 + z1) / 2.0 + 1.5], [3.6, 0.4, 5.2], TRIM)
    b.box([cx, 1.6, z0 + 0.2 - 2.0], [3.0, 3.2, 3.6], "#2a4a8a", collide=False)
    # the slipway down into the bay
    for k in range(9):
        zz = z0 - 1.0 - k * 3.0
        top = -0.4 - k * 0.5
        b.box([cx, top - 1.0, zz - 1.5], [12.0, 2.0, 3.0], ("#8a7a5a", "#7a6a4a")[k % 2])
        for e in (-1.0, 1.0):
            b.box([cx + e * 2.2, top + 0.1, zz - 1.5], [0.5, 0.2, 3.0], "#5a5a60", material="metal",
                  collide=False)
    _keep(rect(x0 - 2.0, x1 + 2.0, z0 - 30.0, z1 + 2.0))
    # the coastguard lookout
    lx0, lx1, lz0, lz1 = x1 + 6.0, x1 + 14.0, z0 + 1.0, z0 + 9.0
    b.box([(lx0 + lx1) / 2.0, 6.0, (lz0 + lz1) / 2.0], [lx1 - lx0, 12.0, lz1 - lz0], STONE)
    slab(b, rect(lx0 - 1.0, lx1 + 1.0, lz0 - 1.0, lz1 + 1.0), 12.4, 0.4, "#8a6a4a")
    for xx in (lx0 - 0.6, lx1 + 0.6):
        for zz in (lz0 - 0.6, lz1 + 0.6):
            b.box([xx, 15.0, zz], [0.4, 4.8, 0.4], TRIM)
    slab(b, rect(lx0 - 1.6, lx1 + 1.6, lz0 - 1.6, lz1 + 1.6), 17.8, 0.4, RED)
    b.box([(lx0 + lx1) / 2.0, 13.4, lz0 - 0.9], [lx1 - lx0 + 2.0, 1.6, 0.2], TRIM)
    b.box([(lx0 + lx1) / 2.0, 13.4, lz1 + 0.9], [lx1 - lx0 + 2.0, 1.6, 0.2], TRIM)
    flight(b, "z", lz1 + 18.0, lz1 + 1.0, lx0, lx0 + 4.0, 0.0, 12.4, STONE_DARK, fill=0.0)
    b.mark("perch", (lx0 + lx1) / 2.0 + 1.0, 12.4, (lz0 + lz1) / 2.0)
    FLAGS.append(((lx1 + 0.6, 21.0, lz0 - 0.6), ["#2a4a8a", "#f2ece0", "#ff6a2a"]))
    b.cyl([lx1 + 0.6, 19.4, lz0 - 0.6], [0.3, 3.2, 0.3], TRIM, collide=False)
    _keep(rect(lx0 - 2.0, lx1 + 2.0, lz0 - 2.0, lz1 + 20.0))


# ================================================================ stores
def _stores(b: ArenaArea, rng: random.Random) -> None:
    """The cannery stores in the south yard: a long brick warehouse with the
    brand painted on it, a loading dock stacked with cases, barrels and
    lobster pots, and a hand crane on the quay."""
    x0, x1, z0, z1 = STORES
    storeyed(b, STORES, [8.0, 6.0], "#b8503a", roof="#4a5a6a",
             doors={"x+": [(z0 + 6.0, z0 + 14.0, 7.0), (z1 - 14.0, z1 - 6.0, 7.0)]},
             windows=[{"x+": [(z0 + 18.0, z0 + 22.0, 3.0, 6.0), (z1 - 22.0, z1 - 18.0, 3.0, 6.0)]},
                      {"x+": [(z0 + 4.0, z0 + 10.0, 10.0, 12.6), (z0 + 19.0, z0 + 25.0, 10.0, 12.6),
                              (z1 - 10.0, z1 - 4.0, 10.0, 12.6)]}])
    for z in (z0 + 10.0, z1 - 10.0):
        threshold(b, STORES, "x+", (z - 4.0, z + 4.0))
    wall_sign(b, x1 + 0.36, 16.4, (z0 + z1) / 2.0, 30.0, 2.4,
              sign_decal("PELICAN BRAND STORES", "#f2ece0", "#2a5a9a", 16.0), "x+", "#f2ece0")
    # cases, barrels and pots along the dock
    for k in range(10):
        cx, cz = x1 + 4.0 + (k % 2) * 3.2, z0 + 4.0 + k * 4.0
        if z0 + 5.0 < cz < z0 + 15.0 or z1 - 15.0 < cz < z1 - 5.0:
            continue
        h = 1.4 + (k % 3) * 1.4
        b.box([cx, h / 2.0, cz], [2.8, h, 2.8], ("#2a5a9a", "#d8322a", "#e8b23a", "#3a8a5a")[k % 4], studs=True)
    for k in range(6):
        b.cyl([x1 + 12.0 + (k % 3) * 2.6, 1.3, z0 + 20.0 + (k // 3) * 2.6], [2.2, 2.6, 2.2], "#8a5a3a")
    for k in range(4):
        b.box([x1 + 18.0, 0.8 + (k % 2) * 1.6, z1 - 10.0 + (k // 2) * 2.4], [2.4, 1.6, 2.2], "#c8a070")
    _keep(rect(x0 - 2.0, x1 + 22.0, z0 - 2.0, z1 + 2.0))
    # the hand crane on the quay
    qx, qz = CUT[0] - 6.0, 214.0
    b.box([qx, 0.6, qz], [4.0, 1.2, 4.0], STONE_DARK)
    b.box([qx, 7.2, qz], [1.2, 12.0, 1.2], "#2a3a6a", material="metal")
    b.box([qx + 4.0, 12.6, qz], [9.0, 0.8, 0.8], "#2a3a6a", material="metal", r=[0, 0, 0.18])
    b.box([qx + 8.0, 9.4, qz], [0.15, 6.0, 0.15], "#2a2a2e", collide=False)
    b.box([qx + 8.0, 5.8, qz], [2.4, 1.4, 1.8], "#c8a070", collide=False)
    _keep(rect(qx - 3.0, qx + 3.0, qz - 3.0, qz + 3.0))


# ======================================================== harbour houses
def _harbour_houses(b: ArenaArea, rng: random.Random) -> None:
    """A row of tall harbour houses along the west edge behind the gardens,
    each its own bright colour, bay windows, chimneys smoking."""
    z = -112.0
    k = 0
    while z < 112.0:
        w = 26.0 + (k % 3) * 3.0
        if z + w > 114.0:
            w = 114.0 - z
        h = 15.0 + (k % 4) * 2.5
        colour = ("#e85a5a", "#5ab0d8", "#fbe49a", "#7ac87a", "#f8a85a", "#c88ae8", "#f4b8c8")[k % 7]
        b.box([-393.0, h / 2.0, z + w / 2.0], [14.0, h, w - 0.4], colour)
        b.box([-393.0, h + 0.5, z + w / 2.0], [15.0, 1.0, w], ("#3a3a48", RED, NAVY)[k % 3])
        for row in range(int(h // 5)):
            for col in range(int(w // 6)):
                wz = z + 3.0 + col * (w - 6.0) / max(1, int(w // 6) - 1) if int(w // 6) > 1 else z + w / 2.0
                b.box([-385.9, 2.6 + row * 4.6, wz], [0.2, 2.2, 1.8], "#a8d8f0", material="glass", alpha=0.85,
                      collide=False)
                b.box([-385.7, 1.4 + row * 4.6, wz], [0.6, 0.4, 2.4], TRIM, collide=False)
        b.box([-385.4, 2.8, z + w / 2.0], [1.4, 5.6, 3.0], "#5a3a2a")
        b.box([-393.0 + 3.0, h + 2.6, z + 4.0], [1.6, 3.2, 1.6], "#b8705a")
        if k % 2 == 0:
            SMOKES.append((-390.0, h + 4.4, z + 4.0))
        z += w
        k += 1
    _keep(rect(-400.0, -384.0, -114.0, 114.0))


# ============================================================ boat sheds
def _boat_sheds(b: ArenaArea, rng: random.Random) -> None:
    """Old boats turned keel-up and roofed over as fishermen's sheds by the
    bay, tarred black with a door cut in the stern; lobster pots stacked,
    floats on a line, and a whelk stall under a striped awning."""
    for k, (x, z, door) in enumerate(((-388.0, -192.0, "#d8322a"), (-372.0, -192.0, "#2f6aa8"),
                                      (-356.0, -192.0, "#e8b23a"))):
        b.box([x, 1.2, z], [8.0, 2.4, 16.0], "#3a3030")
        b.sphere([x, 2.4, z], [8.6, 7.0, 17.0], "#2a2424")
        b.box([x, 2.0, z + 8.05], [2.6, 4.0, 0.3], door, collide=False)
        b.box([x, 5.4, z], [0.6, 0.8, 16.6], "#5a4a3a", collide=False)
        b.cyl([x + 2.0, 5.4, z - 4.0], [0.8, 2.0, 0.8], "#5a5a60", material="metal", collide=False)
        _keep(rect(x - 5.0, x + 5.0, z - 9.0, z + 9.0))
    for k in range(9):
        x, z = -350.0 + (k % 3) * 2.4, -200.0 + (k // 3) * 0.0
        y = 0.8 + (k // 3) * 1.6
        b.box([x, y, z], [2.2, 1.6, 2.6], "#8a6a4a")
        b.box([x, y + 0.85, z], [2.3, 0.1, 2.7], "#5a4a3a", collide=False)
    _keep(rect(-353.0, -345.0, -203.0, -197.0))
    for x in (-394.0, -362.0):
        b.box([x, 3.5, -180.0], [0.5, 7.0, 0.5], WOOD_DARK)
    for k in range(10):
        b.sphere([-391.0 + k * 3.0, 6.36, -180.0], [1.0, 1.0, 1.0],
                 ("#ff6a2a", "#ffd84a", "#2f6aa8", "#d8322a")[k % 4], collide=False)
    b.box([-378.0, 6.85, -180.0], [32.0, 0.1, 0.1], "#2a2a2e", collide=False)
    _keep(rect(-396.0, -360.0, -182.0, -178.0))
    # the whelk stall
    sx, sz = -302.0, -128.0
    b.box([sx, 1.4, sz], [8.0, 2.8, 3.0], TRIM)
    b.box([sx, 2.9, sz], [8.4, 0.2, 3.4], "#c8a070")
    for k in range(6):
        b.box([sx - 3.5 + k * 1.4, 6.2, sz - 1.4], [1.4, 0.3, 4.6], RED if k % 2 else TRIM, collide=False)
    for e in (-1.0, 1.0):
        b.box([sx + e * 3.9, 4.6, sz + 1.3], [0.3, 3.4, 0.3], TRIM)
        b.box([sx + e * 3.9, 4.6, sz - 3.5], [0.3, 3.4, 0.3], TRIM)
    for k in range(4):
        b.cyl([sx - 2.4 + k * 1.6, 3.2, sz], [1.0, 0.4, 1.0], ("#f2ece0", "#e8b0a0")[k % 2], collide=False)
    wall_sign(b, sx, 7.0, sz + 1.6, 7.0, 1.2, sign_decal("WHELKS & COCKLES", TRIM, RED, 6.0), "z+", TRIM)
    _keep(rect(sx - 5.0, sx + 5.0, sz - 4.0, sz + 3.0))


# ============================================================ yard bits
def _yard_bits(b: ArenaArea, rng: random.Random) -> None:
    """A water crane beside each line where it leaves its yard (its arm
    swung back off the track), and an old rowing boat full of flowers."""
    for side in (-1.0, 1.0):
        z = side * 150.0
        cx, cz = -306.0, z - side * 9.0
        b.cyl([cx, 0.5, cz], [3.0, 1.0, 3.0], STONE_DARK)
        b.cyl([cx, 5.0, cz], [1.4, 8.0, 1.4], "#2a3a6a", material="metal")
        b.box([cx + 3.0, 9.4, cz], [6.6, 1.0, 1.0], "#2a3a6a", material="metal")
        b.cyl([cx + 6.0, 8.0, cz], [0.8, 2.0, 0.8], "#3a3a40", material="metal", collide=False)
        b.sphere([cx, 9.8, cz], [1.6, 1.4, 1.6], "#c8902a", material="metal", collide=False)
        _keep(rect(cx - 2.5, cx + 2.5, cz - 2.5, cz + 2.5))
        px, pz = -334.0, z - side * 18.0
        b.box([px, 0.7, pz], [3.6, 1.4, 9.0], ("#2f6aa8", "#d8322a")[side > 0])
        b.box([px, 1.45, pz], [3.0, 0.1, 8.4], "#6a4a30", collide=False)
        for k in range(5):
            b.sphere([px + (k % 2 - 0.5) * 1.2, 1.9, pz - 3.2 + k * 1.6], [1.4, 0.9, 1.4],
                     ("#ff6a8a", "#ffd84a", "#ffffff", "#c86aff", "#ff8a3a")[k], collide=False)
        _keep(rect(px - 2.5, px + 2.5, pz - 5.5, pz + 5.5))


# =========================================================== crazy golf
def _crazy_golf(b: ArenaArea, rng: random.Random) -> None:
    """Crazy golf on the gardens' north-west corner: greens ringed by low
    kerbs, a windmill with turning sails to putt through, a little red and
    white lighthouse, a bridge over a rill, flags in the holes."""
    x0, x1, z0, z1 = -386.0, -348.0, -120.0, -84.0
    y = 0.6
    for k, (gx0, gx1, gz0, gz1) in enumerate(((x0, -369.0, z0, -104.0), (-366.0, x1, z0, -104.0),
                                              (x0, -369.0, -100.0, z1), (-366.0, x1, -100.0, z1))):
        b.box([(gx0 + gx1) / 2.0, y + 0.1, (gz0 + gz1) / 2.0], [gx1 - gx0 - 1.0, 0.2, gz1 - gz0 - 1.0],
              ("#4ab04a", "#3aa03a")[k % 2], studs=True)
        for zz in (gz0, gz1):
            b.box([(gx0 + gx1) / 2.0, y + 0.45, zz], [gx1 - gx0, 0.9, 0.6], TRIM)
        for xx in (gx0, gx1):
            b.box([xx, y + 0.45, (gz0 + gz1) / 2.0], [0.6, 0.9, gz1 - gz0 - 1.2], TRIM)
        hx, hz = gx1 - 3.0, gz0 + 3.0
        b.cyl([hx, y + 0.22, hz], [0.8, 0.06, 0.8], "#1a1a1a", collide=False)
        b.box([hx, y + 2.2, hz], [0.12, 4.0, 0.12], TRIM, collide=False)
        b.box([hx + 0.7, y + 3.7, hz], [1.4, 0.9, 0.06], ("#d8322a", "#ffd84a", "#2f6aa8", "#ff6a2a")[k],
              collide=False)
    # the windmill on hole one
    mx, mz = -378.0, -112.0
    b.box([mx, y + 3.0, mz], [4.0, 5.6, 4.0], "#f4b8c8")
    b.cone([mx, y + 7.0, mz], [5.0, 2.8, 5.0], RED)
    MINIMILLS.append((mx, y + 5.0, mz + 2.3))
    # the lighthouse on hole two
    lx, lz = -356.0, -112.0
    for k in range(4):
        b.cyl([lx, y + 0.9 + k * 1.6, lz], [3.0 - k * 0.3, 1.6, 3.0 - k * 0.3], RED if k % 2 else TRIM)
    b.cyl([lx, y + 7.3, lz], [1.8, 1.2, 1.8], "#fff6c8", material="neon", collide=False)
    b.cone([lx, y + 8.6, lz], [2.2, 1.4, 2.2], RED, collide=False)
    # the hump-backed bridge on hole three, the giant ball on four
    b.box([-377.0, y + 0.8, -92.0], [4.0, 1.2, 6.0], "#c8a070")
    b.sphere([-356.0, y + 1.6, -92.0], [3.0, 3.0, 3.0], TRIM)
    wall_sign(b, -367.0, 2.4, z1 + 1.0, 10.0, 1.6, sign_decal("CRAZY GOLF", "#ffd84a", RED, 6.0), "z+", "#ffd84a")
    b.box([-367.0, 0.8, z1 + 1.0], [0.4, 1.6, 0.4], WOOD_DARK)
    _keep(rect(x0 - 2.0, x1 + 2.0, z0 - 2.0, z1 + 3.0))


# ========================================================== boating pond
def _boating_pond(b: ArenaArea, rng: random.Random) -> None:
    """The boating pond on the south-west corner: shallow (wade in, no
    harm done), its rim of stone, swan pedalos bobbing, a kiosk renting
    them out."""
    x0, x1, z0, z1 = -384.0, -350.0, 86.0, 116.0
    b.box([(x0 + x1) / 2.0, 0.05, (z0 + z1) / 2.0], [x1 - x0 - 2.0, 0.1, z1 - z0 - 2.0], "#3a6a7a")
    b.water((x0 + x1) / 2.0, (z0 + z1) / 2.0, x1 - x0 - 2.0, z1 - z0 - 2.0, 0.5, "#4ab0d8")
    for zz in (z0, z1):
        b.box([(x0 + x1) / 2.0, 0.6, zz], [x1 - x0, 1.2, 2.0], STONE)
    for xx in (x0, x1):
        b.box([xx, 0.6, (z0 + z1) / 2.0], [2.0, 1.2, z1 - z0 - 2.0], STONE)
    b.cyl([(x0 + x1) / 2.0, 1.0, (z0 + z1) / 2.0], [4.0, 2.0, 4.0], STONE)
    b.cyl([(x0 + x1) / 2.0, 2.6, (z0 + z1) / 2.0], [1.2, 1.2, 1.2], STONE_DARK)
    POND_FOUNTAIN.append(((x0 + x1) / 2.0, 3.2, (z0 + z1) / 2.0))
    for k, (sx, sz, yaw) in enumerate(((-374.0, 95.0, 0.4), (-360.0, 106.0, 2.2), (-372.0, 108.0, 4.0))):
        POND_SWANS.append((sx, 0.3, sz, yaw, k))
    kx, kz = -342.0, 120.0
    b.box([kx, 2.4, kz], [6.0, 4.8, 5.0], "#5ab0d8")
    b.box([kx, 5.0, kz], [6.6, 0.4, 5.6], TRIM)
    for k in range(5):
        b.box([kx - 2.4 + k * 1.2, 5.3, kz], [1.2, 0.2, 6.0], "#2a3a6a" if k % 2 else TRIM, collide=False)
    wall_sign(b, kx - 3.36, 3.6, kz, 4.4, 1.0, sign_decal("SWANS 2d", TRIM, NAVY, 3.0), "x-", TRIM)
    _keep(rect(x0 - 2.0, x1 + 2.0, z0 - 2.0, z1 + 2.0))
    _keep(rect(kx - 4.0, kx + 4.0, kz - 3.5, kz + 3.5))


# ===================================================== nets, smokehouse
def _nets_and_smokehouse(b: ArenaArea, rng: random.Random) -> None:
    """The cannery yard's drying ground -- nets hung between tall poles in
    a row -- and the kipper smokehouse by the quay, tarred black, its
    louvred ridge smoking."""
    for k in range(6):
        x = -392.0 + k * 9.0
        b.box([x, 5.0, 182.0], [0.6, 10.0, 0.6], WOOD_DARK)
        if k < 5:
            b.box([x + 4.5, 6.0, 182.0], [8.4, 7.6, 0.12], ("#2a5a5a", "#3a4a6a", "#5a3a3a")[k % 3],
                  collide=False, material="glass", alpha=0.7)
            b.box([x + 4.5, 9.9, 182.0], [9.0, 0.15, 0.15], "#c8b898", collide=False)
            for f in range(3):
                b.sphere([x + 2.0 + f * 2.5, 2.4, 182.0], [0.8, 0.8, 0.8], ("#ff6a2a", "#ffd84a")[f % 2],
                         collide=False)
    _keep(rect(-394.0, -344.0, 180.0, 184.0))
    sx0, sx1, sz0, sz1 = -300.0, -284.0, 200.0, 232.0
    building(b, rect(sx0, sx1, sz0, sz1), 0.0, 14.0, "#2a2424", roof_colour="#3a3030",
             doors={"x+": [(212.0, 220.0, 7.0)]}, windows={}, glass=False, lights=WARM)
    threshold(b, rect(sx0, sx1, sz0, sz1), "x+", (212.0, 220.0))
    for k in range(4):
        b.box([(sx0 + sx1) / 2.0, 16.6, sz0 + 4.0 + k * 8.0], [6.0, 2.4, 3.0], "#3a3030")
        SMOKES.append(((sx0 + sx1) / 2.0, 18.2, sz0 + 4.0 + k * 8.0))
    wall_sign(b, sx1 + 0.36, 10.0, (sz0 + sz1) / 2.0, 12.0, 1.6, sign_decal("KIPPERS", "#ffd84a", "#2a2424", 6.0),
              "x+", "#ffd84a")
    for k in range(5):
        b.box([sx1 + 4.0, 0.7 + (k % 2) * 1.4, sz0 + 3.0 + k * 3.0], [3.0, 1.4, 2.6], "#c8a070")
    _keep(rect(sx0 - 2.0, sx1 + 7.0, sz0 - 2.0, sz1 + 2.0))


# ================================================================== beach
def _beach(b: ArenaArea, rng: random.Random, land: Land) -> None:
    """The beach and its pleasure pier: striped bathing huts in a row, the
    pier on its piles out over the bay to the carousel and the
    helter-skelter (a perch at its top), deck chairs, a sandcastle."""
    for k in range(7):
        x = -186.0 + k * 9.0
        z = -196.0
        y = land.height(x, z)
        colour = (RED, "#2f6aa8", "#e8b23a", "#3a9a5a")[k % 4]
        b.box([x, y + 2.4, z], [6.0, 4.8, 5.0], TRIM)
        for st in range(3):
            b.box([x - 2.0 + st * 2.0, y + 2.4, z + 2.51], [0.9, 4.8, 0.02], colour, collide=False)
        b.box([x, y + 5.2, z], [6.6, 0.6, 5.6], colour)
        _keep(rect(x - 4.0, x + 4.0, z - 3.0, z + 3.0))
    # the pleasure pier
    px0, px1 = -156.0, -124.0
    slab(b, rect(px0, px1, -250.0 + 2.0, SEA_EDGE + 4.0), 1.0, 0.6, "#c8a070", studs=True)
    for x in (px0 + 1.0, px1 - 1.0, (px0 + px1) / 2.0):
        for z in range(-246, -200, 8):
            b.cyl([x, (FLOOR_Y + 0.4) / 2.0, float(z)], [1.2, 0.4 - FLOOR_Y, 1.2], "#6a5a48")
    for e in (px0 + 0.3, px1 - 0.3):
        b.box([e, 2.2, -224.0], [0.3, 0.3, 46.0], TRIM)
        for z in range(-246, -202, 6):
            b.box([e, 1.6, float(z)], [0.3, 1.2, 0.3], TRIM)
    # the helter-skelter: a striped tower, its stair inside, the slide round it
    hx, hz = -132.0, -236.0
    b.cyl([hx, 1.0 + 9.0, hz], [7.0, 18.0, 7.0], TRIM)
    for k in range(6):
        b.cyl([hx, 1.0 + 1.5 + k * 3.0, hz], [7.2, 1.5, 7.2], RED if k % 2 else "#2f6aa8", collide=False)
    b.cone([hx, 1.0 + 21.0, hz], [8.0, 6.0, 8.0], RED)
    slab(b, rect(hx - 4.0, hx + 4.0, hz - 4.0, hz + 4.0), 1.0 + 18.4, 0.4, "#c8a070")
    flight(b, "z", hz + 16.0, hz + 4.0, hx - 2.0, hx + 2.0, 1.0, 1.0 + 18.4, "#c8a070", fill=0.7)
    b.mark("perch", hx, 1.0 + 18.4, hz - 1.0)
    _keep(rect(px0 - 2.0, px1 + 2.0, -250.0, SEA_EDGE + 6.0))
    # deck chairs, a windbreak, a sandcastle with a flag
    for k in range(5):
        x, z = -110.0 + k * 9.0, -194.0 + (k % 2) * 3.0
        y = land.height(x, z)
        b.box([x, y + 1.6, z], [2.4, 1.6, 3.0], (RED, "#e8b23a", "#2f6aa8")[k % 3], collide=False)
        b.box([x, y + 0.4, z], [2.6, 0.8, 3.2], WOOD)
        _keep(rect(x - 2.0, x + 2.0, z - 2.0, z + 2.0))
    cx, cz = -70.0, -198.0
    y = land.height(cx, cz)
    b.box([cx, y + 1.0, cz], [5.0, 2.0, 5.0], "#e8d098", studs=True)
    for dx in (-2.0, 2.0):
        for dz in (-2.0, 2.0):
            b.cyl([cx + dx, y + 2.6, cz + dz], [1.2, 1.4, 1.2], "#e8d098")
    b.box([cx, y + 3.6, cz], [0.1, 2.2, 0.1], WOOD_DARK)
    b.box([cx + 0.6, y + 4.4, cz], [1.1, 0.7, 0.05], RED)
    _keep(rect(cx - 4.0, cx + 4.0, cz - 4.0, cz + 4.0))


# =============================================================== harbour
def _harbour(b: ArenaArea, rng: random.Random) -> None:
    """The fishing harbour: three piers on their piles into the bay with
    boats moored at them in every colour, the fish market under striped
    awnings (the catch on its ice), the net lofts, lobster pots."""
    for k, x in enumerate((-30.0, 20.0, 70.0)):
        slab(b, rect(x - 4.0, x + 4.0, -246.0, SEA_EDGE + 2.0), 0.8, 0.6, "#b89a6a", studs=True)
        for z in range(-244, -204, 8):
            for e in (-3.4, 3.4):
                b.cyl([x + e, (FLOOR_Y + 0.2) / 2.0, float(z)], [1.0, 0.2 - FLOOR_Y, 1.0], "#5a4a3a")
        # the boats moored either side
        for j, side in enumerate((-1.0, 1.0)):
            bx, bz = x + side * 9.0, -232.0 + j * 10.0
            _boat(b, bx, bz, PASTELS[(k * 2 + j) % len(PASTELS)] if j else (RED, "#2f6aa8", "#e8b23a")[k], rng)
        lantern(b, x, 0.8, -244.0, WARM, post=6.0)
        _keep(rect(x - 16.0, x + 16.0, -250.0, SEA_EDGE + 4.0))
    # the fish market: three stalls under striped awnings, fish on ice
    for k in range(3):
        mx, mz = -6.0 + k * 22.0, -184.0
        b.box([mx, 1.4, mz], [14.0, 2.8, 5.0], "#d8d0c0")
        b.box([mx, 2.85, mz], [13.4, 0.1, 4.4], "#e8f4f8", collide=False)
        for f in range(6):
            b.box([mx - 5.0 + f * 2.0, 3.05, mz - 1.0 + (f % 2) * 1.6], [1.6, 0.3, 0.6],
                  ("#a8b8c8", "#c8d0d8", "#d87a5a")[f % 3], collide=False)
        for post in (-6.6, 6.6):
            for e in (-3.0, 3.0):
                b.box([mx + post, 3.8, mz + e], [0.4, 7.6, 0.4], WOOD_DARK)
        for st in range(7):
            b.box([mx - 6.0 + st * 2.0, 7.9, mz], [2.0, 0.3, 7.4], RED if st % 2 else TRIM,
                  collide=False if st % 2 else True)
        _keep(rect(mx - 8.0, mx + 8.0, mz - 5.0, mz + 5.0))
    # the net lofts, tall and tarred, nets hung to dry from the gallery
    for k, (lx, colour) in enumerate(((66.0, "#3a3030"), (84.0, "#4a3a32"))):
        loft = rect(lx - 7.0, lx + 7.0, -184.0, -168.0)
        building(b, loft, 0.0, 14.0, colour, roof_colour="#2a2a2e", doors={"z-": [(lx - 2.0, lx + 2.0, 6.0)]},
                 lights=WARM)
        threshold(b, loft, "z-", (lx - 2.0, lx + 2.0))
        gable(b, loft, 15.2, "#2a2a2e", "x", 3, 1.4, 0.6)
        for n in range(3):
            b.box([lx - 4.0 + n * 4.0, 9.0, -184.05], [2.6, 6.0, 0.1], ("#3a6a8a", "#8a6a3a", "#5a8a5a")[n],
                  collide=False)
        _keep(rect(loft[0] - 2.0, loft[1] + 2.0, loft[2] - 2.0, loft[3] + 2.0))
    # lobster pots stacked on the quay, a harbour master's office
    for k in range(6):
        b.box([40.0 + (k % 3) * 2.6, 0.9 + (k // 3) * 1.8, -195.0], [2.4, 1.8, 2.4], "#a86a3a")
    office = rect(100.0, 116.0, -190.0, -176.0)
    building(b, office, 0.0, 8.0, PASTELS[3], roof_colour=NAVY, doors={"x-": [(-186.0, -182.0, 6.4)]},
             windows={"z-": [(103.0, 113.0, 3.0, 6.0)]}, glass=True, lights=WARM)
    threshold(b, office, "x-", (-186.0, -182.0))
    gable(b, office, 9.2, NAVY, "x", 2, 1.0, 0.6)
    b.box([108.0, 12.0, -183.0], [0.3, 6.0, 0.3], TRIM)
    _keep(rect(38.0, 118.0, -197.0, -174.0))


def _boat(b: ArenaArea, x: float, z: float, hull: str, rng: random.Random) -> None:
    """A little fishing boat at her mooring: a painted hull, a wheelhouse,
    a mast with a furled sail."""
    y = WATER_Y + 0.3
    b.box([x, y + 0.6, z], [4.2, 1.6, 9.0], hull)
    b.box([x, y + 0.6, z + 4.9], [2.6, 1.4, 1.2], hull)
    b.box([x, y + 1.45, z], [3.8, 0.1, 8.4], "#c8a070", collide=False)
    b.box([x, y + 2.6, z - 1.8], [2.6, 2.2, 2.6], TRIM)
    b.box([x, y + 3.8, z - 1.8], [3.0, 0.3, 3.0], NAVY)
    b.box([x, y + 6.0, z + 1.8], [0.25, 8.0, 0.25], "#6a4a30")
    b.box([x, y + 3.4, z + 2.8], [0.5, 0.5, 2.6], "#e8dcc0", collide=False)


# ================================================================ headland
def _headland(b: ArenaArea, rng: random.Random) -> None:
    """The lighthouse on the rocky headland: red and white bands, the
    gallery round its lantern (a perch), the keeper's cottage, the
    foghorn."""
    lx, lz = LIGHTHOUSE
    base = 10.0
    for k in range(7):
        b.cyl([lx, base + 2.5 + k * 5.0, lz], [9.0 - k * 0.5, 5.0, 9.0 - k * 0.5], RED if k % 2 else TRIM)
    top = base + 35.0
    slab(b, rect(lx - 5.0, lx + 5.0, lz - 5.0, lz + 5.0), top + 0.4, 0.4, "#2a2a2e", material="metal")
    for e in (-1, 1):
        b.box([lx + e * 4.8, top + 1.4, lz], [0.2, 2.0, 9.8], "#2a2a2e", material="metal")
        b.box([lx, top + 1.4, lz + e * 4.8], [9.4, 2.0, 0.2], "#2a2a2e", material="metal")
    b.cyl([lx, top + 2.6, lz], [4.2, 4.4, 4.2], "#cfeaf8", material="glass", alpha=0.5, collide=False)
    b.cone([lx, top + 6.2, lz], [5.6, 2.8, 5.6], RED)
    # the stair: round the outside of the tower's lower half, then a ladder-stair
    flight(b, "x", lx + 26.0, lx + 5.0, lz - 2.0, lz + 2.0, base, top + 0.4, "#5a5a5e", fill=base - 0.3)
    b.mark("perch", lx - 2.0, top + 0.4, lz - 2.0)
    cottage = rect(lx - 26.0, lx - 10.0, lz - 4.0, lz + 10.0)
    building(b, cottage, base, 7.0, TRIM, roof_colour=RED, doors={"x+": [(lz + 1.0, lz + 5.0, base + 6.0)]},
             windows={"z+": [(lx - 22.0, lx - 14.0, base + 2.6, base + 5.6)]}, glass=True, lights=WARM)
    threshold(b, cottage, "x+", (lz + 1.0, lz + 5.0), y0=base)
    gable(b, cottage, base + 8.2, RED, "x", 3, 1.2, 0.6)
    b.cyl([lx + 12.0, base + 1.5, lz + 10.0], [2.0, 3.0, 2.0], "#c8a040", material="metal")
    b.cone([lx + 12.0, base + 3.6, lz + 10.0], [3.0, 1.6, 3.0], "#c8a040", material="metal", r=[math.pi, 0, 0])
    for k in range(5):
        outcrop(b, HEADLAND[0] + 6.0 + k * 15.0, SEA_EDGE - 30.0 + (k % 2) * 10.0, 6.0, 4.0, 5.0,
                base=land_rock(k), colour=(STONE, STONE_DARK)[k % 2])
    _keep(rect(lx - 28.0, lx + 28.0, lz - 8.0, lz + 14.0))


def land_rock(k: int) -> float:
    return 2.0 + (k % 3) * 1.5


# ================================================================= square
def _square(b: ArenaArea, rng: random.Random) -> None:
    """Pelican Square, where the lines cross: cobbles, the pelican fountain
    (a bronze bird spouting into the basin), benches, a bandstand, flower
    tubs, and the pastel houses round it."""
    y = 1.0
    fx, fz = 0.0, 18.0
    b.cyl([fx, y + 0.6, fz], [12.0, 1.2, 12.0], STONE)
    b.cyl([fx, y + 1.25, fz], [10.6, 0.1, 10.6], "#5ab0d8", collide=False, material="glass", alpha=0.85)
    b.cyl([fx, y + 2.6, fz], [2.0, 2.8, 2.0], STONE_DARK)
    b.sphere([fx, y + 5.0, fz], [2.4, 2.2, 3.0], "#8a6a3a", material="metal")
    b.box([fx, y + 6.4, fz + 1.4], [0.6, 1.6, 0.6], "#8a6a3a", material="metal")
    b.box([fx, y + 7.2, fz + 2.6], [0.5, 0.5, 2.6], "#c8902a", material="metal")
    b.sphere([fx, y + 7.0, fz + 2.6], [0.8, 0.9, 1.6], "#a87a3a", material="metal")
    _keep(rect(fx - 7.0, fx + 7.0, fz - 7.0, fz + 7.0))
    for k, (x, z) in enumerate(((-20.0, 26.0), (20.0, 26.0), (-26.0, -4.0), (26.0, -4.0))):
        b.box([x, y + 0.7, z], [5.0, 0.4, 1.6], WOOD)
        b.box([x, y + 0.35, z], [0.5, 0.7, 1.4], "#2a2a2e", material="metal")
        b.cyl([x + 4.0, y + 0.8, z], [2.4, 1.6, 2.4], "#a86a3a")
        b.sphere([x + 4.0, y + 2.0, z], [2.6, 1.6, 2.6], ("#ff6a8a", "#ffd84a", "#c86aff", "#ff8a3a")[k],
                 collide=False)
        _keep(rect(x - 3.0, x + 6.0, z - 2.0, z + 2.0))
    # the pastel houses round the square, each its own colour, flower boxes
    houses = (rect(-80.0, -56.0, 36.0, 58.0), rect(-80.0, -56.0, -58.0, -36.0), rect(40.0, 64.0, -66.0, -44.0),
              rect(40.0, 64.0, 44.0, 66.0), rect(-30.0, -8.0, 50.0, 70.0), rect(8.0, 30.0, -70.0, -50.0))
    for k, area in enumerate(houses):
        colour = PASTELS[k % len(PASTELS)]
        storeyed(b, area, [7.0, 6.0], colour, roof=(RED, NAVY, "#3a8a6a")[k % 3], base=y,
                 doors={"z+" if area[2] < 0 else "z-": [(area[0] + 8.0, area[0] + 12.0, y + 6.0)]},
                 windows=[{"z+" if area[2] < 0 else "z-": [(area[0] + 2.0, area[0] + 6.0, y + 2.4, y + 5.4),
                                                          (area[1] - 6.0, area[1] - 2.0, y + 2.4, y + 5.4)]},
                          {"z+" if area[2] < 0 else "z-": [(area[0] + 3.0, area[0] + 8.0, y + 8.6, y + 11.6),
                                                          (area[1] - 8.0, area[1] - 3.0, y + 8.6, y + 11.6)]}])
        side = "z+" if area[2] < 0 else "z-"
        threshold(b, area, side, (area[0] + 8.0, area[0] + 12.0), y0=y)
        gable(b, area, y + 13.0 + 1.2, (RED, NAVY, "#3a8a6a")[k % 3], "x", 3, 1.2, 0.6)
        fz2 = area[3] + 0.4 if side == "z+" else area[2] - 0.4
        for wx in (area[0] + 4.0, area[1] - 4.0):
            b.box([wx, y + 2.0, fz2], [3.2, 0.6, 0.6], "#8a5a3a")
            b.sphere([wx, y + 2.6, fz2], [3.0, 0.8, 0.8], ("#ff6a8a", "#ffd84a", "#ff8a3a")[k % 3], collide=False)
        _keep(rect(area[0] - 2.0, area[1] + 2.0, area[2] - 2.0, area[3] + 2.0))
    for x, z in ((-36.0, -30.0), (36.0, 30.0), (36.0, -30.0), (-36.0, 30.0)):
        lamp_post(b, x, z, 10.0, light=WARM, y=y)


# ================================================================ cannery
def _cannery(b: ArenaArea, rng: random.Random) -> None:
    """Cannery Row: the Pelican Brand cannery on the Cut (its sign as big
    as the building, its stack smoking), the conveyor up from the quay,
    stacks of cases in every label colour, and the boatyard with a
    schooner on the slipway, half planked."""
    x0, x1, z0, z1 = CANNERY
    storeyed(b, CANNERY, [10.0, 8.0], "#c8604a", roof="#5a6a7a",
             doors={"x+": [(196.0, 208.0, 9.0)], "z-": [(-178.0, -170.0, 8.0)]},
             windows=[{"x+": [(184.0, 192.0, 3.0, 8.0), (212.0, 220.0, 3.0, 8.0)],
                       "z-": [(-160.0, -150.0, 3.0, 8.0), (-140.0, -130.0, 3.0, 8.0)]},
                      {"x+": [(184.0, 192.0, 12.0, 16.0), (200.0, 208.0, 12.0, 16.0), (216.0, 224.0, 12.0, 16.0)],
                       "z-": [(-182.0, -172.0, 12.0, 16.0), (-160.0, -150.0, 12.0, 16.0), (-140.0, -130.0, 12.0, 16.0)]}],
             wells=[rect(x0 + 2.0, x0 + 8.0, z0 + 2.0, z0 + 14.0)])
    flight(b, "z", z0 + 16.0, z0 + 2.0, x0 + 2.0, x0 + 8.0, 0.4, 10.0, WOOD, fill=0.0)
    threshold(b, CANNERY, "x+", (196.0, 208.0))
    threshold(b, CANNERY, "z-", (-178.0, -170.0))
    gable(b, CANNERY, 19.2, "#5a6a7a", "x", 4, 1.3, 0.8)
    b.box([(x0 + x1) / 2.0, 23.0, z0 - 0.1], [52.0, 6.0, 0.5], "#f2ece0",
          decal=sign_decal("PELICAN BRAND SARDINES", "#f2ece0", "#2a5a9a", 30.0))
    b.box([(x0 + x1) / 2.0, 26.4, z0 - 0.1], [52.6, 0.8, 0.7], RED)
    b.cyl([x1 - 8.0, 26.0, z1 - 8.0], [3.4, 20.0, 3.4], "#8a3a2a")
    b.mark("perch", x0 + 12.0, 10.4, z0 + 6.0)
    _keep(rect(x0 - 2.0, x1 + 2.0, z0 - 2.0, z1 + 2.0))
    # the conveyor up from the Cut's quay to the loft door
    b.box([x0 - 16.0, 6.0, z0 + 14.0], [30.0, 0.8, 3.0], "#4a4a4e", material="metal", r=[0.0, 0.0, 0.32],
          collide=False)
    for x in (x0 - 26.0, x0 - 12.0):
        b.box([x, 2.6, z0 + 14.0], [0.6, 5.2, 0.6], "#3a3a3e", material="metal")
    # cases of tins in label colours, stacked as cover
    for k in range(8):
        cx = -110.0 + (k % 4) * 9.0
        cz = 186.0 + (k // 4) * 12.0
        h = 2.0 + (k % 3) * 1.6
        b.box([cx, h / 2.0, cz], [6.0, h, 4.0], ("#2a5a9a", "#d8322a", "#e8b23a", "#3a8a5a")[k % 4], studs=True)
        b.box([cx, h + 0.05, cz], [5.6, 0.1, 3.6], "#f2ece0", collide=False)
    _keep(rect(-114.0, -74.0, 182.0, 202.0))
    # the boatyard: the slipway down to the Cut, a schooner on it half planked
    sx, sz = -86.0, 228.0
    for k in range(10):
        b.box([sx - 18.0 + k * 4.0, 0.6, sz], [3.6, 1.2, 10.0], "#8a7a5a")
    for k in range(9):
        u = k - 4
        h = 4.0 + 3.0 * (1.0 - (u / 5.0) ** 2)
        b.box([sx + u * 3.4, 1.2 + h / 2.0, sz - 3.2], [0.5, h, 0.5], "#c8a070")
        b.box([sx + u * 3.4, 1.2 + h / 2.0, sz + 3.2], [0.5, h, 0.5], "#c8a070")
        b.box([sx + u * 3.4, 1.2 + h, sz], [0.5, 0.5, 7.0], "#c8a070")
    for k in range(3):
        b.box([sx - 6.0 + k * 3.0, 1.2 + 1.6 + k * 1.2, sz - 3.4], [14.0 - k * 2.0, 1.2, 0.3], "#7a5a3a")
    b.box([sx, 14.0, sz], [0.6, 18.0, 0.6], "#6a4a30")
    _keep(rect(sx - 22.0, sx + 22.0, sz - 8.0, sz + 8.0))


# ================================================================== hill
def _hill(b: ArenaArea, rng: random.Random, land: Land) -> None:
    """Chapel Hill: pastel cottages stepping up its flank each on its own
    terrace, a stair lane between them, washing on lines, and the white
    chapel on the crown with its bell (a perch on its steps)."""
    hx0, hz0, hh, _hr = HILL
    for k, (x, z) in enumerate(HILL_SPOTS):
        if not clear_of(rect(x - 9.0, x + 9.0, z - 8.0, z + 8.0), LANES, 11.0) or _blocked(x, z):
            continue
        y = HILL_Y.get((x, z), land.height(x, z)) - 0.4
        cottage = rect(x - 7.0, x + 7.0, z - 6.0, z + 6.0)
        building(b, cottage, y + 0.4, 7.0, PASTELS[(k + 2) % len(PASTELS)], roof_colour=(RED, NAVY, "#3a8a6a")[k % 3],
                 doors={"z-": [(x - 1.6, x + 1.6, y + 5.8)]},
                 windows={"z-": [(x - 6.0, x - 3.0, y + 2.4, y + 5.0), (x + 3.0, x + 6.0, y + 2.4, y + 5.0)]},
                 glass=True, lights=WARM)
        threshold(b, cottage, "z-", (x - 1.6, x + 1.6), y0=y + 0.4)
        gable(b, cottage, y + 8.6, (RED, NAVY, "#3a8a6a")[k % 3], "x", 3, 1.0, 0.5)
        _keep(rect(x - 9.0, x + 9.0, z - 9.0, z + 8.0))
    # the chapel on the crown
    cy = HILL_Y.get("chapel", float(round(land.height(hx0, hz0))))
    chapel = rect(hx0 - 9.0, hx0 + 9.0, hz0 - 16.0, hz0 + 4.0)
    building(b, chapel, cy, 9.0, TRIM, roof_colour=NAVY, doors={"z-": [(hx0 - 2.0, hx0 + 2.0, cy + 7.0)]},
             windows={"x-": [(hz0 - 12.0, hz0 - 8.0, cy + 3.0, cy + 7.0), (hz0 - 4.0, hz0, cy + 3.0, cy + 7.0)],
                      "x+": [(hz0 - 12.0, hz0 - 8.0, cy + 3.0, cy + 7.0), (hz0 - 4.0, hz0, cy + 3.0, cy + 7.0)]},
             glass=True, lights=WARM)
    threshold(b, chapel, "z-", (hx0 - 2.0, hx0 + 2.0), y0=cy)
    gable(b, chapel, cy + 10.2, NAVY, "z", 4, 1.2, 0.6)
    b.box([hx0, cy + 15.0, hz0 - 16.0 + 3.0], [5.0, 8.0, 5.0], TRIM)
    b.cone([hx0, cy + 21.0, hz0 - 13.0], [6.0, 4.0, 6.0], NAVY)
    b.cone([hx0, cy + 15.6, hz0 - 13.0], [1.8, 1.8, 1.8], "#c8a040", material="metal", collide=False)
    b.mark("perch", hx0 + 6.0, cy, hz0 - 18.0)
    _keep(rect(chapel[0] - 3.0, chapel[1] + 3.0, chapel[2] - 12.0, chapel[3] + 3.0))
    # the tower mill on the hill's shoulder (its sails are a rig)
    mx, mz = MILL_SPOT
    my = HILL_Y.get("mill", float(math.floor(land.height(mx, mz))))
    b.cyl([mx, my + 9.0, mz], [9.0, 18.0, 9.0], "#e8e0d0")
    b.cyl([mx, my + 18.4, mz], [7.6, 0.8, 7.6], NAVY)
    b.box([mx, my + 2.6, mz - 4.4], [3.0, 5.2, 0.4], "#6a4a30")
    MILL[0] = (mx, my + 20.6, mz)
    _keep(rect(mx - 6.0, mx + 6.0, mz - 6.0, mz + 6.0))
    # hedgerows in flower along the terraces, cover to fight over
    for k, (x0, x1, z) in enumerate(((120.0, 150.0, 162.0), (206.0, 246.0, 136.0), (150.0, 186.0, 232.0),
                                     (226.0, 258.0, 182.0))):
        if not clear_of(rect(x0, x1, z - 1.5, z + 1.5), LANES, 10.0) or _blocked((x0 + x1) / 2.0, z):
            continue
        for x in range(int(x0), int(x1), 5):
            y = land.height(float(x) + 2.5, z)
            b.box([float(x) + 2.5, y + 1.2, z], [5.0, 2.4, 2.6], GRASS_DEEP)
            b.sphere([float(x) + 2.5, y + 2.6, z], [2.0, 0.8, 1.6], ("#ff6a8a", "#ffd84a", "#c86aff", "#ffffff")[(x // 5 + k) % 4],
                     collide=False)
        _keep(rect(x0, x1, z - 2.0, z + 2.0))
    # the washing lines' posts between cottages (the washing is a rig)
    for k, (x, z) in enumerate(((158.0, 128.0), (230.0, 154.0), (182.0, 196.0))):
        y = land.height(x, z)
        for dx in (-8.0, 8.0):
            b.box([x + dx, y + 3.0, z], [0.4, 6.0, 0.4], WOOD_DARK)
        LINES.append((x, y + 5.8, z))
        _keep(rect(x - 9.0, x + 9.0, z - 1.0, z + 1.0))
    # the sheep's grazing ground
    for cx, cz in ((206.0, 170.0), (140.0, 232.0)):
        SHEEP.append((cx, cz, [land.height(cx + math.cos(i * 1.2566) * 8.0, cz + math.sin(i * 1.2566) * 8.0)
                                for i in range(5)]))


MILL: list = [None]
LINES: list = []
SHEEP: list = []
CLOCKS: list = []
MINIMILLS: list = []
POND_SWANS: list = []
POND_FOUNTAIN: list = []
VANES: list = []
FLAGS: list = []
LIGHTS: list = []
SMOKES: list = []
HILL_SPOTS = ((150.0, 110.0), (166.0, 92.0), (214.0, 98.0), (232.0, 120.0), (146.0, 186.0), (170.0, 206.0),
              (220.0, 196.0), (240.0, 168.0), (128.0, 140.0), (252.0, 142.0), (196.0, 222.0), (126.0, 214.0),
              (262.0, 204.0), (186.0, 84.0))
MILL_SPOT = (238.0, 232.0)
HILL_Y: dict = {}


# ================================================================== hotel
def _hotel(b: ArenaArea, rng: random.Random) -> None:
    """The Grand Pelican Hotel between the stations: three storeys of
    seaside white with a striped awning, corner turrets and a veranda (a
    perch on its roof)."""
    x0, x1, z0, z1 = HOTEL
    storeyed(b, HOTEL, [9.0, 7.0, 7.0], TRIM, roof=RED,
             doors={"x-": [(-6.0, 6.0, 8.0)]},
             windows=[{"x-": [(-40.0, -30.0, 3.0, 7.0), (-20.0, -10.0, 3.0, 7.0), (10.0, 20.0, 3.0, 7.0),
                              (30.0, 40.0, 3.0, 7.0)]},
                      {"x-": [(-40.0, -32.0, 11.0, 14.0), (-24.0, -16.0, 11.0, 14.0), (-4.0, 4.0, 11.0, 14.0),
                              (16.0, 24.0, 11.0, 14.0), (32.0, 40.0, 11.0, 14.0)]},
                      {"x-": [(-40.0, -32.0, 18.0, 21.0), (-24.0, -16.0, 18.0, 21.0), (-4.0, 4.0, 18.0, 21.0),
                              (16.0, 24.0, 18.0, 21.0), (32.0, 40.0, 18.0, 21.0)]}],
             wells=[rect(x1 - 8.0, x1 - 2.0, z0 + 2.0, z0 + 14.0)], parapet=1.2)
    flight(b, "z", z0 + 16.0, z0 + 2.0, x1 - 8.0, x1 - 2.0, 0.4, 9.0, WOOD, fill=0.0)
    threshold(b, HOTEL, "x-", (-6.0, 6.0))
    slab(b, rect(x0 - 8.0, x0, z0 + 4.0, z1 - 4.0), 0.4, 0.4, "#c8a070")
    for z in range(int(z0) + 6, int(z1) - 3, 10):
        b.box([x0 - 7.0, 4.5, float(z)], [0.8, 9.0, 0.8], TRIM)
    slab(b, rect(x0 - 8.6, x0, z0 + 3.4, z1 - 3.4), 9.6, 0.6, "#c8a070", studs=True)
    for st in range(9):
        z = z0 + 4.0 + st * (z1 - z0 - 8.0) / 9.0
        b.box([x0 - 4.3, 10.2, z + (z1 - z0 - 8.0) / 18.0], [8.6, 0.6, (z1 - z0 - 8.0) / 9.0], RED if st % 2 else TRIM,
              collide=False)
    flight(b, "z", z1 + 14.0, z1 - 3.4, x0 - 8.0, x0 - 2.0, 0.0, 9.6, WOOD, fill=-0.3)
    b.mark("perch", x0 - 4.0, 9.6, 0.0)
    for zz in (z0, z1):
        b.cyl([x0 + 2.0, 26.0, zz], [6.0, 6.0, 6.0], TRIM)
        b.cone([x0 + 2.0, 31.0, zz], [7.0, 5.0, 7.0], RED)
    wall_sign(b, x0 - 0.36, 24.0, 0.0, 30.0, 2.6, sign_decal("GRAND PELICAN HOTEL", RED, TRIM, 12.0), "x-", RED)
    _keep(rect(x0 - 10.0, x1 + 2.0, z0 - 6.0, z1 + 16.0))


# ================================================================ scatter
def _scatter(b: ArenaArea, rng: random.Random, land: Land) -> None:
    """Seaside clutter: tufts of marram and sea pinks, rocks, crab pots, an
    upturned dinghy, a ship's figurehead in the grass."""
    tries = placed = 0
    hx, hz = HALF
    while placed < 90 and tries < 1600:
        tries += 1
        x, z = rng.uniform(CUT[1] + 10.0, hx - 10.0), rng.uniform(SEA_EDGE + 8.0, hz - 10.0)
        if not clear_of(rect(x - 4.0, x + 4.0, z - 4.0, z + 4.0), LANES, 12.0):
            continue
        if _blocked(x, z) or any(k[0] - 5 < x < k[1] + 5 and k[2] - 5 < z < k[3] + 5 for k in KEEP):
            continue
        base = land.height(x, z)
        if abs(land.height(x + 3.0, z) - base) > 0.6 or abs(land.height(x, z + 3.0) - base) > 0.6:
            continue
        roll = rng.random()
        if roll < 0.5:
            for k in range(3):
                b.cone([x + (k - 1) * 0.9, base + 0.7, z + (k % 2) * 0.7], [1.2, 1.4, 1.2],
                       rng.choice(["#9ab85a", "#ff8ab0", "#b8c86a"]), collide=False)
        elif roll < 0.75:
            outcrop(b, x, z, rng.uniform(2.0, 3.6), rng.uniform(0.8, 1.6), rng.uniform(2.0, 3.0), base=base,
                    colour=rng.choice([STONE, STONE_DARK]))
        elif roll < 0.9:
            b.box([x, base + 0.6, z], [3.2, 1.2, 6.0], rng.choice([RED, "#2f6aa8", "#e8b23a"]))
        else:
            b.box([x, base + 0.9, z], [2.4, 1.8, 2.4], "#a86a3a")
        KEEP.append(rect(x - 4.0, x + 4.0, z - 4.0, z + 4.0))
        placed += 1


# =================================================================== rigs
def _rigs(b: ArenaArea) -> None:
    wind = [0.6, 0.4]
    b.rig("rr_lighthouse", LIGHTHOUSE[0], 10.0 + 35.0 + 2.6, LIGHTHOUSE[1], len=220.0, rate=0.5)
    b.rig("rr_carousel", -140.0, 1.0, -222.0, r=6.5)
    b.rig("rr_fountain", 0.0, 2.4, 18.0, h=4.0, r=3.2)
    b.rig("rr_fountain", 0.0, 1.0 + 7.4, 20.6, h=2.0, r=1.2, n=1)
    for k, (x, z) in enumerate(((-140.0, -230.0), (30.0, -228.0), (140.0, -232.0), (-228.0, -40.0),
                                (PIVOT_X, 150.0), (290.0, -200.0))):
        b.rig("rr_gulls", x, 22.0 + (k % 3) * 4.0, z, r=24.0 + k * 3.0, n=4 + k % 3, seed=k)
    for k, (x, z, yaw) in enumerate(((-34.0, -246.5, 0.5), (24.0, -246.5, 2.0), (74.0, -246.5, 3.6),
                                     (CUT[1] + 2.2, -120.0, 1.6), (CUT[1] + 2.2, 90.0, -1.2))):
        b.rig("rr_pelican", x, 2.2 if x > CUT[1] + 3 else 2.2, z, yaw=yaw, seed=k * 0.37)
    for k, (x, r, col) in enumerate(((-80.0, 70.0, RED), (160.0, 90.0, "#2f6aa8"), (40.0, 120.0, "#e8b23a"))):
        b.rig("rr_sailboat", x, WATER_Y + 0.2, -420.0, r=r, speed=0.03 + k * 0.01, colour=col, seed=k * 2.0)
    b.rig("rr_surf", 60.0, WATER_Y + 0.3, -222.0, w=160.0, yaw=0.0)
    b.rig("rr_surf", -110.0, WATER_Y + 0.3, -222.0, w=60.0, yaw=0.0)
    b.rig("rr_smoke", CANNERY[1] - 8.0, 36.2, CANNERY[3] - 8.0, wind=wind, rate=0.18, h=26.0, colour="#c8c0b8")
    b.rig("rr_flag", HOTEL[0] + 2.0, 33.6, HOTEL[2], w=4.0, h=2.4, yaw=math.atan2(-wind[0], -wind[1]),
          colours=[RED, TRIM, NAVY])
    b.rig("rr_flag", 108.0, 15.0, -183.0, w=3.6, h=2.2, yaw=math.atan2(-wind[0], -wind[1]),
          colours=["#f2ece0", "#2f6aa8", "#f2ece0"])
    b.rig("rr_lights", -36.0, 11.6, -30.0, q=[36.0, 11.6, 30.0], n=20, sag=3.0)
    b.rig("rr_lights", 36.0, 11.6, -30.0, q=[-36.0, 11.6, 30.0], n=20, sag=3.0)
    if MILL[0] is not None:
        mx, my, mz = MILL[0]
        b.rig("rr_mill_sails", mx, my, mz - 4.0, yaw=math.pi, r=11.0, cap=NAVY)
    for x, y, z in LINES:
        b.rig("rr_clothesline", x, y, z, w=16.0)
    for cx, cz, ys in SHEEP:
        b.rig("rr_sheep", cx, ys[0], cz, n=5, r=10.0, ys=ys)
    for (x, y, z), yaw, tilt, r in CLOCKS:
        b.rig("rr_clock", x, y, z, yaw=yaw, tilt=tilt, r=r, seconds=RED if r > 4 else "")
    for x, y, z in VANES:
        b.rig("rr_vane", x, y, z, yaw=math.atan2(-wind[0], -wind[1]))
    for (x, y, z), colours in FLAGS:
        b.rig("rr_flag", x, y, z, w=4.0, h=2.4, yaw=math.atan2(-wind[0], -wind[1]), colours=colours)
    for a, q in LIGHTS:
        b.rig("rr_lights", a[0], a[1], a[2], q=list(q), n=12, sag=2.0)
    for x, y, z in SMOKES:
        b.rig("rr_smoke", x, y, z, wind=wind, rate=0.3, h=14.0, size=1.4, colour="#d8d4cc")
    b.rig("rr_gulls", -323.0, 26.0, -215.0, r=22.0, n=5, seed=11)
    for x, y, z in MINIMILLS:
        b.rig("rr_mill_sails", x, y, z, yaw=0.0, r=3.4, cap=RED, sail="#ffffff")
    for x, y, z, yaw, k in POND_SWANS:
        b.rig("rr_swan", x, y, z, yaw=yaw, seed=k * 1.7, r=3.0)
    for x, y, z in POND_FOUNTAIN:
        b.rig("rr_fountain", x, y, z, h=3.0, r=1.6, n=1)

