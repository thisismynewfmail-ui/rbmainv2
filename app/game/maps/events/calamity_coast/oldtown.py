"""Old Town -- a walled market town on a river: the market square, the
town hall and its clock tower, the cathedral under scaffolding, lanes of
timbered houses, the old wooden bridge and the stone one, the mill, and
the castle on its hill in the south-west.

Layout (north is -z)::

    z -150  ======================== the north gate =========================
              timbered houses     THE MARKET SQUARE      THE CATHEDRAL
              (the west lanes)    the town hall and      (scaffolding,
                                  its clock tower        the bell tower)
    z  -10  ~~~~~~~~ THE RIVER ~~ old wooden bridge ~~ stone bridge ~~ mill ~~~
    z   20    THE OLD QUARTER: the inn, the bakery, timbered houses
    z   70    THE CASTLE HILL (y 16):      the orchard
              walls, the keep, the bailey
    z  150  ================================================================

The disasters: an **earthquake** (the old bridge, the scaffolding and a
stretch of the castle walk come down; get out in the open), the **great
fire** (it spreads from house to house; keep to the squares and the
riverside), a **flood** (the river rises: up the castle hill or a tower),
and a **hailstorm** (get under a roof).
"""
from __future__ import annotations

import random

from ..kit import ArenaArea, Surfaces, backdrop, flight, ground, perimeter, rect, slab
from . import town
from .town import bench, crate_pile, helipad, house, lookout_tower, solid, stairs, street_lamp

HALF = (170.0, 150.0)
SKY = {"top": "#6a8ab8", "horizon": "#e8dcc8", "sun": [0.4, 0.6, -0.5], "clouds": 0.6,
       "tint": "#fff0e0"}
AMBIENT = "#b0aca4"
GROUND = "#a89c88"
FOG = 700.0

COBBLE = "#9a9284"
STONE = "#b8ac98"
STONE_DARK = "#8a8070"
RIVER = "#4a7a8a"
TIMBER = "#4a3424"
PLASTER = ["#f0e4cc", "#e8d8b8", "#f4ecdc", "#e0d0b0", "#ecdcc4"]
ROOFS = ["#8a3a2a", "#6a3a2a", "#5a4a3a", "#7a4a3a"]

RIVER_Z = (-10.0, 20.0)
RIVER_BED = -8.0
RIVER_TOP = -3.0
HILL = (-170.0, -90.0, 70.0, 150.0)
HILL_TOP = 16.0
FIRE_HOUSES = []        # filled by _houses: (x, z) of every house that can burn


# ================================================================ the land
def _land(b: ArenaArea, s: Surfaces) -> None:
    hx, hz = HALF
    z0, z1 = RIVER_Z
    # the river: embankment walls inside the cut, the bed, the water
    for a, c in ((z0, z0 + 1.2), (z1 - 1.2, z1)):
        slab(b, rect(-hx, hx, a, c), 0.0, -RIVER_BED, STONE_DARK)
    slab(b, rect(-hx, hx, z0 + 1.2, z1 - 1.2), RIVER_BED, 4.0, "#6a6458")
    b.box([0.0, (RIVER_BED + RIVER_TOP) / 2.0, (z0 + z1) / 2.0], [2 * hx, RIVER_TOP - RIVER_BED,
          z1 - z0 - 2.4], RIVER, material="glass", alpha=0.6, collide=False)
    for x in (-150.0, 10.0, 150.0):
        flight(b, "z", z0 + 1.2 + 9.0, z0 + 1.2, x - 3.0, x + 3.0, RIVER_BED, 0.0, STONE_DARK,
               fill=RIVER_BED)
    # the stone bridge (it stays) and the old wooden one (an earthquake drops it)
    slab(b, rect(34.0, 50.0, z0 - 2.0, z1 + 2.0), 0.8, 0.8, STONE)
    for x in (35.0, 49.0):
        b.box([x, 2.0, (z0 + z1) / 2.0], [1.2, 2.4, z1 - z0 + 4.0], STONE)
    b.box([42.0, (RIVER_BED + 0.0) / 2.0, (z0 + z1) / 2.0], [8.0, -RIVER_BED, 6.0], STONE)
    with b.detached() as parts:
        slab(b, rect(-88.0, -78.0, z0 - 1.0, z1 + 1.0), 0.5, 0.5, "#8a6a44")
        for x in (-87.6, -78.4):
            b.box([x, 1.6, (z0 + z1) / 2.0], [0.3, 0.3, z1 - z0 + 2.0], "#6a4a2a")
    b.dynamic("oldbridge", parts, on=True, group="oldbridge")
    for x in (-88.6, -77.4):
        for z in (z0 - 1.6, z1 + 1.6):
            b.box([x, 1.4, z], [0.8, 2.8, 0.8], "#6a4a2a")
    # the castle hill and the stairs up it
    hx0, hx1, hz0, hz1 = HILL
    solid(b, rect(hx0, hx1, hz0, hz1), HILL_TOP, "#8a9a6a")
    stairs(b, "z", hz0 - 20.0, hz0, -104.0, -96.0, 0.0, HILL_TOP, STONE_DARK)
    stairs(b, "x", hx1 + 20.0, hx1, 120.0, 128.0, 0.0, HILL_TOP, STONE_DARK)
    # cobbles in the squares and lanes
    s.lay(rect(-50.0, 50.0, -95.0, -35.0), 0.15, COBBLE)
    s.lay(rect(-hx, hx, -30.0, -18.0), 0.15, COBBLE)
    s.lay(rect(-90.0, hx, 26.0, 36.0), 0.15, COBBLE)


def _houses(b: ArenaArea, rng: random.Random) -> None:
    """The timbered houses of the west lanes, the east end and the old
    quarter; each one a place the great fire can take."""
    blocks = [
        # (x0, x1, z0, z1, door)
        (-166.0, -144.0, -140.0, -122.0, "z+"), (-138.0, -116.0, -140.0, -122.0, "z+"),
        (-110.0, -88.0, -140.0, -122.0, "z+"), (-166.0, -144.0, -100.0, -82.0, "z-"),
        (-138.0, -116.0, -100.0, -82.0, "z-"), (-110.0, -88.0, -100.0, -82.0, "x+"),
        (-166.0, -144.0, -66.0, -46.0, "z+"), (-138.0, -116.0, -66.0, -46.0, "z+"),
        (-110.0, -88.0, -66.0, -46.0, "z+"), (124.0, 146.0, -66.0, -44.0, "z+"),
        (150.0, 168.0, -66.0, -44.0, "z+"), (-80.0, -58.0, 40.0, 58.0, "z-"),
        (-50.0, -28.0, 40.0, 58.0, "z-"), (60.0, 82.0, 40.0, 58.0, "z-"),
        (-80.0, -58.0, 70.0, 88.0, "z+"), (-50.0, -28.0, 70.0, 88.0, "z+"),
        (60.0, 82.0, 70.0, 88.0, "z+"), (90.0, 112.0, 40.0, 58.0, "z-"),
    ]
    for k, (x0, x1, z0, z1, door) in enumerate(blocks):
        house(b, (x0, x1, z0, z1), 0.0, PLASTER[k % len(PLASTER)], ROOFS[k % len(ROOFS)], door,
              height=11.0 + (k % 3) * 1.0, rng=rng, tiers=4)
        # the timbers: dark bands across the front, a beam over the door
        xc, zc = (x0 + x1) / 2.0, (z0 + z1) / 2.0
        FIRE_HOUSES.append((xc, zc))
    # the inn, the bakery, the blacksmith
    house(b, (0.0, 40.0, 40.0, 62.0), 0.0, "#f0e4cc", "#5a3a2a", "z-", height=13.0,
          sign="THE OLD BELL INN", sign_colours=(TIMBER, "#f2d890"), rng=rng, tiers=4)
    house(b, (-20.0, -4.0, 70.0, 88.0), 0.0, "#f4ecdc", "#8a3a2a", "z+", height=11.0,
          sign="BAKERY", sign_colours=("#8a3a2a", "#f4f0e8"), rng=rng, tiers=3)
    house(b, (20.0, 44.0, 70.0, 88.0), 0.0, "#8a8478", "#3a3a3a", "z+", height=10.0,
          sign="SMITHY", sign_colours=("#2a2a2a", "#e8a050"), rng=rng, tiers=3)
    for x, z in ((20.0, 51.0), (-12.0, 79.0), (32.0, 79.0)):
        FIRE_HOUSES.append((x, z))


def _market(b: ArenaArea, rng: random.Random) -> None:
    y = 0.15
    # the town hall and its clock tower
    house(b, (-44.0, 0.0, -136.0, -104.0), 0.0, "#e8dcc4", "#5a5a6a", "z+", height=15.0,
          sign="TOWN HALL", sign_colours=("#3a3a4a", "#f2d890"), rng=rng, tiers=4)
    lookout_tower(b, 14.0, -120.0, 0.0, 26.0, "#d8ccb4", "#8a8070", core=8.0, width=4.0,
                  cap="#5a5a6a", start="z+")
    b.box([14.0, 20.0, -115.9], [5.0, 5.0, 0.2], "#f4ecd8", decal="clockface")
    # the fountain and the market stalls
    b.cyl([0.0, y + 0.8, -65.0], [12.0, 1.6, 12.0], STONE)
    b.cyl([0.0, y + 1.625, -65.0], [10.4, 0.05, 10.4], "#5a9ab0", material="glass", alpha=0.75,
          collide=False)
    b.cyl([0.0, y + 1.6 + 2.0, -65.0], [1.6, 4.0, 1.6], STONE)
    b.sphere([0.0, y + 6.2, -65.0], [2.4, 1.6, 2.4], STONE)
    for k, (x, z) in enumerate(((-34.0, -80.0), (-34.0, -50.0), (34.0, -80.0), (34.0, -50.0),
                                (-18.0, -42.0), (18.0, -42.0))):
        b.box([x, y + 1.4, z], [8.0, 2.8, 4.0], "#8a6a44")
        for dx in (-3.8, 3.8):
            b.box([x + dx, y + 2.8 + 2.2, z - 1.8], [0.3, 4.4, 0.3], "#6a4a2a")
        b.box([x, y + 7.4, z - 1.0], [9.0, 0.4, 5.0], ["#c8302a", "#2a6ac8", "#e8c040"][k % 3])
        b.box([x, y + 2.8 + 0.6, z + 0.6], [7.0, 1.2, 2.0], ["#e86a2a", "#7ac83a", "#c83a5a"][k % 3])
    for x, z in ((-46.0, -60.0), (46.0, -60.0), (-46.0, -90.0), (46.0, -90.0)):
        street_lamp(b, x, z, y, 11.0)
    for x in (-20.0, 20.0):
        bench(b, x, -88.0, y, "x")


def _cathedral(b: ArenaArea, rng: random.Random) -> None:
    """The cathedral, its bell tower, and the scaffolding up its north side
    (an earthquake brings it down)."""
    house(b, (60.0, 110.0, -136.0, -96.0), 0.0, "#d8ccb4", "#4a4a5a", "z+", height=22.0,
          sign="CATHEDRAL", sign_colours=("#3a3a4a", "#f2d890"), rng=rng, tiers=6,
          gable_along="z")
    lookout_tower(b, 126.0, -104.0, 0.0, 32.0, "#c8bca4", "#8a8070", core=9.0, width=4.5,
                  cap="#4a4a5a", start="x+")
    b.cone([126.0, 32.6 + 6.0, -104.0], [9.0, 12.0, 9.0], "#4a4a5a")
    for x in (64.0, 106.0):
        for z in (-142.0, -139.0):
            b.box([x, 9.0, z], [0.5, 18.0, 0.5], "#8a8a8a", material="metal")
    with b.detached() as parts:
        for y in (6.0, 12.0, 18.0):
            slab(b, rect(63.0, 107.0, -142.6, -138.4), y, 0.4, "#8a6a44")
    b.dynamic("scaffold", parts, on=True, group="scaffold")
    flight(b, "x", 113.4, 107.0, -142.6, -138.4, 0.0, 6.0, "#8a6a44", fill=-0.3)


def _castle(b: ArenaArea, rng: random.Random) -> None:
    """The castle on the hill: a curtain wall with a gate and a walk along
    its top, the keep, the bailey (the muster point)."""
    y = HILL_TOP
    x0, x1, z0, z1 = -164.0, -100.0, 84.0, 144.0
    t, h = 3.0, 9.0
    for a, c in ((x0, -136.0), (-128.0, x1)):
        b.box([(a + c) / 2.0, y + h / 2.0, z0 + t / 2.0], [c - a, h, t], STONE)
    b.box([(x0 + x1) / 2.0, y + h / 2.0, z1 - t / 2.0], [x1 - x0, h, t], STONE)
    for x in (x0 + t / 2.0, x1 - t / 2.0):
        b.box([x, y + h / 2.0, (z0 + z1) / 2.0], [t, h, z1 - z0 - 2 * t], STONE)
    for x in (-136.0, -128.0):
        b.box([x, y + h + 1.2, z0 + t / 2.0], [1.2, 2.4, t], STONE_DARK)
    # crenels along the walls, and the walk on the west wall's inner side
    for k in range(9):
        b.box([x0 + 4.0 + k * 7.0, y + h + 0.8, z1 - t / 2.0], [3.0, 1.6, t], STONE_DARK)
    with b.detached() as parts:
        slab(b, rect(x0 + t, x0 + t + 4.0, z0 + t + 6.0, z1 - t - 6.0), y + 6.0, 0.6, "#8a6a44")
    b.dynamic("walkway", parts, on=True, group="walkway")
    flight(b, "z", z0 + t + 0.6, z0 + t + 6.0, x0 + t, x0 + t + 4.0, y, y + 6.0, STONE_DARK,
           fill=y - 0.3)
    lookout_tower(b, -124.0, 126.0, y, 18.0, STONE, STONE_DARK, core=10.0, width=4.5,
                  cap=STONE_DARK, start="z-")
    helipad(b, -132.0, 104.0, y, 9.0)


def _river_side(b: ArenaArea, rng: random.Random) -> None:
    """The mill and its wheel, boats tied up, the riverside walk."""
    y = 0.15
    house(b, (110.0, 140.0, 24.0, 44.0), 0.0, "#d8ccb4", "#5a4a3a", "z+", height=12.0,
          sign="THE MILL", sign_colours=(TIMBER, "#f2d890"), rng=rng, tiers=4)
    b.cyl([125.0, 2.0, RIVER_Z[1] - 1.2 - 0.4], [12.0, 0.8, 12.0], "#6a4a2a", collide=False,
          r=[1.5708, 0.0, 0.0])
    for x in range(-160, 165, 32):
        street_lamp(b, float(x), -24.0, 0.15, 10.0)
        street_lamp(b, float(x) + 16.0, 30.0, 0.15, 10.0)
    for x in (-120.0, -40.0, 90.0):
        bench(b, x, -20.0, 0.15, "x")
    crate_pile(b, 150.0, 50.0, y, rng, "#8a6a44")
    crate_pile(b, -60.0, -30.0 + 12.0, y, rng, "#8a6a44")
    # the orchard on the east of the old quarter
    for k in range(10):
        b.tree(110.0 + (k % 5) * 12.0, 100.0 + (k // 5) * 22.0, 0.0, 0.8, leaf_c="#4a8a3a")


def _edges(b: ArenaArea, rng: random.Random) -> None:
    perimeter(b, 48.0, "#a89c88", cap="#7a7064", rng=rng, ragged=4.0)
    town.skirt(b, HALF[0], HALF[1], "#7a8a5a", top=RIVER_BED - 4.05)
    backdrop(b, "hills", 30.0, rng, colours=["#7a9a5a", "#6a8a4a", "#8aa06a"])


# ================================================================ the meta
def _meta(b: ArenaArea) -> None:
    for x in (-40.0, -32.0, -24.0, -16.0):
        for z in (-56.0, -72.0):
            b.team_spawn("red", x, None, z, yaw=0.0)
    for x in (16.0, 24.0, 32.0, 40.0):
        for z in (-56.0, -72.0):
            b.team_spawn("blue", x, None, z, yaw=0.0)
    for x, z in ((-150.0, 76.0), (-110.0, 76.0), (-96.0, 148.0 - 4.0), (-150.0, 148.0 - 4.0)):
        b.mark("high", x, HILL_TOP, z)
    for x, z in ((0.0, -50.0), (-25.0, -65.0), (25.0, -65.0), (0.0, -90.0), (-140.0, 104.0),
                 (-112.0, 104.0), (130.0, 120.0), (160.0, 100.0), (40.0, 31.0), (-120.0, -24.0),
                 (120.0, -24.0)):
        b.mark("open", x, 0.15 if z < 0 and z > -100 else (HILL_TOP if x < -90 and z > 70 else 0.0), z)
    for x, z in FIRE_HOUSES:
        b.mark("fire", x, 0.0, z)
    for x, z in FIRE_HOUSES[::2] + [(-22.0, -100.0), (85.0, -92.0), (125.0, 48.0), (20.0, 66.0)]:
        b.mark("debris", x + 6.0, 0.0, z + 6.0)
    stranded = [(-83.0, 0.5, 5.0, "the old bridge"), (10.0, RIVER_BED, -4.0, "the riverbed"),
                (125.0, 0.0, 50.0, "the mill"), (85.0, 0.0, -144.0, "the scaffolding"),
                (-155.0, 0.0, -110.0, "the west lanes"), (150.0, 0.0, -30.0, "the east end"),
                (-160.0, HILL_TOP + 6.0, 110.0, "the castle walk"), (140.0, 0.0, 140.0, "the orchard"),
                (0.0, 0.15, -78.0, "the market"), (-70.0, 0.0, 64.0, "the old quarter"),
                (-100.0, 0.15, 31.0, "the riverside"), (150.0, 0.0, 70.0, "the far lanes")]
    for x, y, z, name in stranded:
        b.mark("stranded", x, y, z, name=name)
    for x, y, z in ((-60.0, 0.15, -24.0), (60.0, 0.15, -24.0), (-30.0, 0.15, -90.0),
                    (30.0, 0.15, -40.0), (-140.0, 0.0, -30.0), (100.0, 0.0, -70.0),
                    (-60.0, 0.15, 31.0), (80.0, 0.15, 31.0), (-140.0, HILL_TOP, 96.0),
                    (130.0, 0.0, 70.0)):
        b.mark("crate", x, y, z)
    for x, z, name in ((0.0, -65.0, "the market square"), (-22.0, -120.0, "the town hall"),
                       (14.0, -120.0, "the clock tower"), (85.0, -116.0, "the cathedral"),
                       (126.0, -104.0, "the bell tower"), (-83.0, 5.0, "the old bridge"),
                       (42.0, 5.0, "the stone bridge"), (125.0, 34.0, "the mill"),
                       (20.0, 51.0, "the inn"), (-130.0, -90.0, "the west lanes"),
                       (-132.0, 110.0, "the castle"), (-124.0, 126.0, "the keep"),
                       (130.0, 110.0, "the orchard"), (-40.0, 60.0, "the old quarter")):
        b.landmark(x, z, name)
    b.camera(0.0, 70.0, 150.0, 0.0, 6.0, -20.0)
    b.camera(-170.0, 60.0, 150.0, -60.0, 10.0, 20.0)
    b.camera(150.0, 50.0, -150.0, 40.0, 6.0, -60.0)
    b.extra.update({"accent": "#e8a050", "disasters": DISASTERS})


DISASTERS = [
    {"id": "quake", "name": "Earthquake", "line": "Out into the squares, away from the walls!",
     "seconds": 42.0, "safe": ["open"],
     "parts": [{"kind": "quake", "power": 1.2,
                "collapse": [[7.0, "oldbridge"], [15.0, "scaffold"], [24.0, "walkway"]],
                "names": {"oldbridge": "the old bridge", "scaffold": "the cathedral scaffolding",
                          "walkway": "the castle walk"}},
               {"kind": "strikes", "what": "debris", "aim": "marks", "marks": "debris",
                "every": [0.4, 0.9], "r": 6.0, "damage": 45.0, "warn": 1.5}]},
    {"id": "fire", "name": "The Great Fire", "line": "Keep to the squares and the river!",
     "seconds": 48.0, "safe": ["open", "high"],
     "parts": [{"kind": "fire", "start": 2, "spread": 7.0, "burn": 26.0, "reach": 34.0, "r": 9.0,
                "dps": 22.0}]},
    {"id": "flood", "name": "Flood", "line": "The river is rising -- up the castle hill!",
     "seconds": 46.0, "safe": ["high"],
     "parts": [{"kind": "level", "medium": "water", "from": RIVER_TOP, "to": 8.0, "rise": 20.0,
                "fall": 10.0, "dps": 24.0, "flow": [1.0, 0.0]}]},
    {"id": "hail", "name": "Hailstorm", "line": "Get under a roof!", "seconds": 44.0,
     "safe": ["shelter"],
     "parts": [{"kind": "rain", "what": "hail", "dps": 6.0},
               {"kind": "strikes", "what": "hail", "every": [0.3, 0.6], "r": 3.0, "damage": 18.0,
                "warn": 1.0, "open": True}]},
]


def build(b: ArenaArea) -> None:
    rng = random.Random(8841)
    hx, hz = HALF
    m = b.margin
    FIRE_HOUSES.clear()
    ground(b, GROUND, soil="#6a5a44", material="", holes=[rect(-hx - m, hx + m, RIVER_Z[0], RIVER_Z[1])])
    s = Surfaces(b)
    s.reserve(rect(*HILL))
    _edges(b, rng)
    _land(b, s)
    _houses(b, rng)
    _market(b, rng)
    _cathedral(b, rng)
    _castle(b, rng)
    _river_side(b, rng)
    _meta(b)
