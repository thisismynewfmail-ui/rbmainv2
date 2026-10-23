"""Port Sunny -- a seaside town climbing the hill from its harbour: the
quay, the fish market and the boats; the high street of shops; three
terraces of cottages, the church and the town hall; and the clifftop park
with the helipad at the very top.  A lighthouse stands on the rocks off the
east end.

Layout (north is -z; the sea is to the south)::

    z -150  ============ THE CLIFFTOP PARK (y 32): helipad, cafe, mast ===========
    z  -86  ---- TERRACE 3 (y 24): the town hall, the water tower, houses -------
    z  -50  ---- TERRACE 2 (y 16): the church and its belfry, the school -------
    z  -14  ---- TERRACE 1 (y 8): cottages and their gardens --------------------
    z   22  ==== THE HIGH STREET (y 0): shops against the terrace wall ==========
    z   60  ---- THE QUAY: the fish market, the coastguard tower, the crane -----
    z   92  ==== the harbour: piers, boats ====================  the lighthouse
    z  150

The disasters: a **tsunami** (get above the second terrace), a
**lightning storm** and a **meteor shower** (get under a roof), and a
**tornado** that walks the high street.
"""
from __future__ import annotations

import random

from ..kit import ArenaArea, Surfaces, backdrop, gable, ground, letters, perimeter, rect, slab
from ...lastlight.kit import boat
from . import town
from .town import (bench, bollard, crate_pile, helipad, house, lookout_tower, palm, pier,
                   solid, stairs, street_lamp)

HALF = (170.0, 150.0)
SKY = {"top": "#4a8ad8", "horizon": "#d8ecf8", "sun": [0.45, 0.75, 0.35], "clouds": 0.6,
       "tint": "#fff4e0"}
AMBIENT = "#a8b4c4"
GROUND = "#b8b0a0"
FOG = 760.0

STONE = "#b8ae9c"
STONE_DARK = "#8a8274"
PAVING = "#c8c0b0"
ROAD = "#4a4e54"
SAND = "#e0cc98"
SEA = "#2a7ab0"
WOOD = "#8a6a44"
ROOFS = ["#9a4a3a", "#3a5a7a", "#5a6a4a", "#7a3a3a", "#4a4a5a"]
WALLS = ["#f4ecd8", "#e8d8c0", "#d8e8f0", "#f0d8d0", "#e0ecd8", "#f8f0c8"]

QUAY_EDGE = 92.0
SEABED = -6.0
SEA_TOP = -1.0
TERRACES = [(8.0, -14.0, 22.0), (16.0, -50.0, -14.0), (24.0, -86.0, -50.0),
            (32.0, -150.0, -86.0)]            # (top, z0, z1)
STAIRS = [
    # (x, lower level, upper level, wall z): flights up each terrace wall
    (-120.0, 0.0, 8.0, 22.0), (0.0, 0.0, 8.0, 22.0), (120.0, 0.0, 8.0, 22.0),
    (-60.0, 8.0, 16.0, -14.0), (60.0, 8.0, 16.0, -14.0), (150.0, 8.0, 16.0, -14.0),
    (-150.0, 16.0, 24.0, -50.0), (-10.0, 16.0, 24.0, -50.0), (100.0, 16.0, 24.0, -50.0),
    (-90.0, 24.0, 32.0, -86.0), (40.0, 24.0, 32.0, -86.0), (150.0, 24.0, 32.0, -86.0),
]
STAIR_W = 8.0
STAIR_RUN = 10.0


# ================================================================ the land
def _land(b: ArenaArea, s: Surfaces) -> None:
    hx, hz = HALF
    m = b.margin
    sea = rect(-hx - m, hx + m, QUAY_EDGE, hz + m)
    slab(b, sea, SEABED, 4.0, SAND)
    b.box([0.0, (SEABED + SEA_TOP) / 2.0, (QUAY_EDGE + hz) / 2.0],
          [2 * hx, SEA_TOP - SEABED, hz - QUAY_EDGE], SEA, material="glass",
          alpha=0.55, collide=False)
    # the side walls of the world go all the way down to the seabed
    for sx in (-1.0, 1.0):
        b.box([sx * (hx + m / 2.0), (SEABED + 0.0) / 2.0, (QUAY_EDGE + hz + m) / 2.0],
              [m, -SEABED, hz + m - QUAY_EDGE], "#8a8274")
    # the quay wall and its coping
    b.box([0.0, (SEABED + 0.0) / 2.0, QUAY_EDGE + 0.3], [2 * hx, -SEABED, 0.6], STONE_DARK)
    b.box([0.0, 0.25, QUAY_EDGE - 0.4], [2 * hx, 0.5, 1.6], STONE)
    # the terraces, each a block of masonry, and the stairs up their walls
    for top, z0, z1 in TERRACES:
        solid(b, rect(-hx, hx, z0, z1), top, STONE if top < 30 else "#9aa88a")
    for x, lo, hi, wall in STAIRS:
        near = wall + STAIR_RUN
        stairs(b, "z", near, wall, x - STAIR_W / 2.0, x + STAIR_W / 2.0, lo, hi, STONE_DARK)
    # the high street: road, pavements, the promenade
    s.lay(rect(-hx, hx, 44.0, 56.0), 0.12, ROAD)
    s.lay(rect(-hx, hx, 22.0, 60.0), 0.2, PAVING)
    s.lay(rect(-hx, hx, 60.0, QUAY_EDGE - 1.2), 0.2, "#b0a898")
    for x in range(-160, 165, 20):
        b.box([float(x), 0.135, 50.0], [8.0, 0.03, 0.6], "#e8e8e0", collide=False)
    # steps down from the quay to the water, three places
    for x in (-150.0, -40.0, 70.0):
        stairs(b, "z", QUAY_EDGE + 9.0, QUAY_EDGE + 0.6, x - 3.0, x + 3.0, SEABED, 0.0, STONE_DARK)


def _quay(b: ArenaArea, rng: random.Random) -> None:
    y = 0.2
    # the fish market: a long roof on posts over the stalls
    x0, x1, z0, z1 = -100.0, -50.0, 66.0, 86.0
    for x in (x0 + 1.0, x0 + 13.0, x0 + 25.0, x0 + 37.0, x1 - 1.0):
        for z in (z0 + 1.0, z1 - 1.0):
            b.box([x, y + 5.5, z], [1.2, 11.0, 1.2], "#4a5a6a", material="metal")
    slab(b, rect(x0 - 1.0, x1 + 1.0, z0 - 1.0, z1 + 1.0), y + 11.8, 0.8, "#5a7a8a")
    gable(b, rect(x0 - 1.0, x1 + 1.0, z0 - 1.0, z1 + 1.0), y + 11.8, "#5a7a8a", "x", tiers=3,
          rise=1.0, overhang=0.0)
    b.box([(x0 + x1) / 2.0, y + 9.6, z1 + 1.3], [24.0, 2.0, 0.6], "#f4f0e8")
    letters(b, (x0 + x1) / 2.0, y + 9.6, z1 + 1.6, "FISH MARKET", 1.5, "#f4f0e8", "#2a4a6a",
            "z+", depth=0.2)
    for k, x in enumerate((-92.0, -80.0, -68.0, -56.0)):
        b.box([x, y + 1.4, 72.0], [8.0, 2.8, 3.0], "#e8e4dc")
        b.box([x, y + 2.95, 72.0], [7.6, 0.3, 2.6], "#bfe8ff", material="glass", alpha=0.7)
        b.box([x, y + 1.4, 80.0], [8.0, 2.8, 3.0], "#e8e4dc")
    for x in (-86.0, -62.0):
        b.mark("shelter", x, y, 76.0)
    crate_pile(b, -96.0, 88.6, y, rng, "#3a7ab0")
    # the coastguard tower and its office
    house(b, (6.0, 40.0, 64.0, 82.0), y, "#f4f4f4", "#c8302a", "z+", sign="COASTGUARD",
          sign_colours=("#c8302a", "#f4f4f4"), rng=rng)
    lookout_tower(b, 54.0, 74.0, y, 22.0, "#f4f4f4", "#9a9aa0", core=10.0, width=5.0,
                  cap="#c8302a")
    # the crane, the bollards, the nets and crates
    cx, cz = 100.0, 82.0
    for dx in (-3.0, 3.0):
        for dz in (-3.0, 3.0):
            b.box([cx + dx, y + 9.0, cz + dz], [1.0, 18.0, 1.0], "#e8b030", material="metal")
    b.box([cx, y + 18.6, cz], [8.0, 1.2, 8.0], "#e8b030", material="metal")
    b.box([cx, y + 21.2, cz], [5.0, 4.0, 5.0], "#d89a20", material="metal")
    b.box([cx, y + 22.0, cz + 11.0], [1.4, 1.4, 18.0], "#e8b030", material="metal")
    b.box([cx, y + 17.0, cz + 19.0], [0.2, 9.4, 0.2], "#2a2a2a", collide=False)
    b.box([cx, y + 11.8, cz + 19.0], [1.6, 1.0, 1.6], "#3a3a3a", material="metal")
    for x in range(-160, 165, 24):
        if -132 < x < -118 or -8 < x < 8 or 92 < x < 108:
            continue
        bollard(b, float(x) + 4.0, QUAY_EDGE - 2.4, y)
    for x, z in ((-30.0, 84.0), (-24.0, 76.0), (140.0, 70.0), (-140.0, 72.0)):
        crate_pile(b, x, z, y, rng)
    for x, z in ((-120.0, 66.0), (80.0, 66.0)):
        b.box([x, y + 0.6, z], [6.0, 1.2, 4.0], "#3a6a4a", decal="netting")
    # the bandstand on the promenade
    bx, bz = -10.0, 64.0
    slab(b, rect(bx - 7.0, bx + 7.0, bz - 5.0, bz + 5.0), y + 1.2, 1.0, "#f4f0e8")
    for dx in (-6.2, 6.2):
        for dz in (-4.2, 4.2):
            b.box([bx + dx, y + 1.2 + 4.0, bz + dz], [0.6, 8.0, 0.6], "#f4f0e8")
    slab(b, rect(bx - 7.6, bx + 7.6, bz - 5.6, bz + 5.6), y + 9.8, 0.6, "#2a6a8a")
    b.cone([bx, y + 9.8 + 1.4, bz], [14.0, 2.8, 10.0], "#2a6a8a")
    b.mark("shelter", bx, y + 1.2, bz)


def _harbour(b: ArenaArea, rng: random.Random) -> None:
    deck = 0.6
    pier(b, -130.0, -122.0, QUAY_EDGE, 132.0, deck, SEABED)
    pier(b, -4.0, 4.0, QUAY_EDGE, 128.0, deck, SEABED)
    slab(b, rect(-14.0, 14.0, 128.0, 136.0), deck, 0.6, WOOD)
    for x in (-13.4, 13.4):
        b.cyl([x, (SEABED + deck - 0.6) / 2.0, 132.0], [1.0, deck - 0.6 - SEABED, 1.0], "#5a4030")
    pier(b, 96.0, 104.0, QUAY_EDGE, 124.0, deck, SEABED)
    # boats alongside
    boat(b, -112.0, 112.0, "z", length=26.0, colour="#f4f4f4", base=SEABED)
    boat(b, 16.0, 108.0, "z", length=24.0, colour="#c8402a", base=SEABED)
    boat(b, 114.0, 110.0, "z", length=22.0, colour="#2a6a9a", base=SEABED, cabin=False)
    boat(b, -60.0, 124.0, "x", length=28.0, colour="#e8c040", base=SEABED)
    # the lighthouse on its rocks, with a causeway out to it
    slab(b, rect(126.0, 168.0, 100.0, 146.0), 4.0, 10.0, "#7a7a76")
    slab(b, rect(130.0, 164.0, 104.0, 142.0), 6.0, 2.0, "#8a8a84")
    from ..kit import flight
    flight(b, "z", QUAY_EDGE, 100.0, 132.0, 140.0, 0.0, 4.0, STONE_DARK, fill=SEABED)
    stairs(b, "z", 100.5, 104.0, 132.0, 140.0, 4.0, 6.0, STONE_DARK)
    lookout_tower(b, 150.0, 124.0, 6.0, 30.0, "#f4f4f4", "#9a9aa0", core=10.0, width=5.0,
                  cap="#2a2a2a", start="z-", lantern="#fff6c0", bands=("#f4f4f4", "#c8302a"))


def _street(b: ArenaArea, rng: random.Random) -> None:
    """The shops along the foot of the first terrace, their doors on the
    street."""
    y = 0.2
    shops = [(-166.0, -146.0, "SURF SHOP"), (-144.0, -126.0, "BAKERY"),
             (-114.0, -94.0, "ANCHOR INN"), (-92.0, -70.0, "CHIPS"), (-68.0, -46.0, "BANK"),
             (-44.0, -22.0, "POST OFFICE"), (-20.0, -6.0, "ICE CREAM"),
             (6.0, 28.0, "CHEMIST"), (30.0, 52.0, "BOOKS"), (54.0, 76.0, "TOYS"),
             (78.0, 100.0, "GROCER"), (102.0, 116.0, "CAFE"), (126.0, 146.0, "BIKES"),
             (148.0, 166.0, "GIFTS")]
    for k, (x0, x1, name) in enumerate(shops):
        h = 11.0 + (k % 3) * 1.4
        house(b, (x0, x1, 22.0, 40.0), y, WALLS[k % len(WALLS)], ROOFS[k % len(ROOFS)], "z+",
              height=h, sign=name, sign_colours=(ROOFS[(k + 2) % len(ROOFS)], "#f4f0e8"),
              rng=rng, tiers=2, gable_along="x")
    # parked cars, lamps, benches and palms
    for x, colour in ((-150.0, "#c8402a"), (-70.0, "#3a6ab0"), (20.0, "#e8e8e8"),
                      (90.0, "#3a8a5a"), (140.0, "#f2c230")):
        town.car(b, x, 53.5, 0.12, "x", colour)
    for x in range(-150, 160, 30):
        street_lamp(b, float(x), 42.0, y)
        street_lamp(b, float(x) + 15.0, 58.0, y)
    for x in (-130.0, -50.0, 30.0, 110.0):
        bench(b, x, 59.0, y, "x")
    for x in (-160.0, -100.0, -40.0, 40.0, 100.0, 160.0):
        palm(b, x, 62.5, y, 14.0, rng)
    # the ice cream kiosk on the promenade
    b.box([60.0, y + 3.0, 64.0], [6.0, 6.0, 4.0], "#f8c8d8")
    b.box([60.0, y + 6.4, 64.0], [7.0, 0.8, 5.0], "#e85a8a")
    b.cone([60.0, y + 8.4, 64.0], [3.0, 3.2, 3.0], "#f4e0b0")


def _terraces(b: ArenaArea, rng: random.Random) -> None:
    # terrace 1: cottages with front gardens
    y1 = 8.0
    for k, (x0, x1) in enumerate(((-166.0, -142.0), (-132.0, -108.0), (-96.0, -72.0),
                                  (-40.0, -16.0), (-4.0, 18.0), (30.0, 54.0), (80.0, 104.0),
                                  (118.0, 142.0))):
        house(b, (x0, x1, 0.0, 16.0), y1, WALLS[(k + 2) % len(WALLS)], ROOFS[k % len(ROOFS)],
              "z+", height=10.0, rng=rng)
        b.box([(x0 + x1) / 2.0 + 7.0, y1 + 1.0, 19.0], [3.0, 2.0, 3.0], "#3a7a3a")
    for x in (-150.0, -55.0, 66.0, 160.0):
        palm(b, x, 12.0, y1, 12.0, rng)
    # terrace 2: the church, its belfry, the school, houses
    y2 = 16.0
    house(b, (-104.0, -64.0, -46.0, -22.0), y2, "#d8d0c0", "#5a5a6a", "z+", height=16.0,
          sign="ST PETER'S", sign_colours=("#3a3a4a", "#f4e8c8"), rng=rng, tiers=4,
          gable_along="z")
    lookout_tower(b, -50.0, -34.0, y2, 22.0, "#c8c0b0", "#8a8274", core=9.0, width=4.5,
                  cap="#5a5a6a")
    # the church square: the town's muster point, a second way out
    helipad(b, -120.0, -32.0, y2, 9.0)
    house(b, (0.0, 40.0, -46.0, -24.0), y2, "#f0d8a0", "#7a3a3a", "z+", height=12.0,
          sign="SCHOOL", sign_colours=("#2a4a8a", "#f4f4f4"), rng=rng)
    for k, (x0, x1) in enumerate(((66.0, 90.0), (112.0, 136.0), (-160.0, -136.0))):
        house(b, (x0, x1, -42.0, -24.0), y2, WALLS[k % len(WALLS)], ROOFS[(k + 3) % len(ROOFS)],
              "z+", height=10.0, rng=rng)
    # terrace 3: the town hall, the water tower, houses, the memorial
    y3 = 24.0
    house(b, (-40.0, 10.0, -82.0, -58.0), y3, "#e8e0cc", "#3a5a4a", "z+", height=15.0,
          sign="TOWN HALL", sign_colours=("#3a5a4a", "#f4f0e0"), rng=rng, tiers=4)
    lookout_tower(b, 130.0, -68.0, y3, 16.0, "#8a9aa8", "#6a7a88", core=10.0, width=4.5,
                  cap="#5a6a78")
    for k, (x0, x1) in enumerate(((-166.0, -142.0), (-126.0, -102.0), (56.0, 80.0),
                                  (86.0, 110.0))):
        house(b, (x0, x1, -80.0, -62.0), y3, WALLS[(k + 4) % len(WALLS)], ROOFS[(k + 1) % len(ROOFS)],
              "z+", height=10.0, rng=rng)
    b.box([30.0, y3 + 1.0, -66.0], [6.0, 2.0, 6.0], STONE_DARK)
    b.box([30.0, y3 + 6.0, -66.0], [2.6, 8.0, 2.6], STONE)
    b.cone([30.0, y3 + 11.0, -66.0], [2.6, 2.0, 2.6], STONE)


def _park(b: ArenaArea, rng: random.Random) -> None:
    y = 32.0
    helipad(b, 0.0, -120.0, y, 12.0)
    house(b, (-84.0, -54.0, -136.0, -110.0), y, "#f4f0e8", "#2a6a8a", "z+", height=10.0,
          sign="CLIFFTOP CAFE", sign_colours=("#2a6a8a", "#f4f0e8"), rng=rng)
    house(b, (56.0, 86.0, -136.0, -112.0), y, "#e8ecf0", "#c8302a", "z+", height=10.0,
          sign="RADIO STATION", sign_colours=("#c8302a", "#f4f4f4"), rng=rng)
    # the radio mast
    mx, mz = 120.0, -130.0
    for dx in (-2.0, 2.0):
        for dz in (-2.0, 2.0):
            b.box([mx + dx, y + 14.0, mz + dz], [0.6, 28.0, 0.6], "#c8302a", material="metal")
    for k in range(1, 7):
        b.box([mx, y + k * 4.0, mz], [4.6, 0.4, 4.6], "#f4f4f4", material="metal")
    b.box([mx, y + 28.6, mz], [1.2, 1.2, 1.2], "#ff4a3a", material="neon")
    for x, z in ((-140.0, -100.0), (-120.0, -140.0), (-30.0, -100.0), (40.0, -98.0),
                 (150.0, -100.0), (100.0, -100.0), (-150.0, -128.0)):
        b.tree(x, z, y, 1.0, leaf_c="#3a7a3a")
    for x in (-40.0, 40.0):
        bench(b, x, -134.0, y, "x")
    # the viewing telescopes on the cliff edge
    for x in (-110.0, 70.0):
        b.cyl([x, y + 1.6, -90.0], [0.6, 3.2, 0.6], "#3a3a3a", material="metal")
        b.box([x, y + 3.6, -90.0], [0.8, 0.8, 2.4], "#3a6a8a", material="metal")


def _edges(b: ArenaArea, rng: random.Random) -> None:
    perimeter(b, 56.0, "#8a8274", cap="#6a7a5a", rng=rng, ragged=4.0, gaps=("z+",))
    town.skirt(b, HALF[0], HALF[1], "#6a7a5a", top=SEABED - 4.05)
    backdrop(b, "hills", 30.0, rng, sides=("x-", "x+", "z-"), colours=["#6a8a5a", "#5a7a4a"])
    # out to sea: a breakwater of rocks along the far edge, and the open
    # water going on past it to the horizon
    hx, hz = HALF
    m = b.margin
    b.box([0.0, (SEABED + 14.0) / 2.0, hz + m / 2.0], [2 * hx, 14.0 - SEABED, m], "#7a7a76")
    for k in range(18):
        x = -hx + (k + 0.5) * 2 * hx / 18.0
        b.box([x, 14.0 + 1.0 + (k % 3) * 0.4, hz + m / 2.0 + rng.uniform(-1.0, 1.0)],
              [2 * hx / 18.0 - 2.0, 2.0 + (k % 3) * 0.8, m - 2.0 - (k % 2) * 0.6], "#8a8a84",
              collide=False)
    b.box([0.0, (SEABED + SEA_TOP) / 2.0, hz + m + 110.0], [2 * (hx + m) + 440.0, SEA_TOP - SEABED, 220.0],
          SEA, material="glass", alpha=0.55, collide=False)


# ================================================================ the meta
def _meta(b: ArenaArea) -> None:
    for k in range(8):
        b.team_spawn("red", -150.0 + k * 14.0, None, 48.0 if k % 2 else 32.0, yaw=0.0)
        b.team_spawn("blue", 52.0 + k * 14.0, None, 48.0 if k % 2 else 32.0, yaw=0.0)
    for x, y, z in ((-140.0, 32.0, -96.0), (-100.0, 32.0, -146.0), (-30.0, 32.0, -140.0),
                    (30.0, 32.0, -96.0), (100.0, 32.0, -116.0), (160.0, 32.0, -140.0),
                    (-130.0, 24.0, -56.0), (-60.0, 24.0, -54.0), (60.0, 24.0, -54.0),
                    (160.0, 24.0, -56.0), (-20.0, 24.0, -54.0), (16.0, 32.0, -146.0)):
        b.mark("high", x, y, z)
    stranded = [
        (-126.0, 0.6, 128.0, "the west pier"), (0.0, 0.6, 133.0, "the pier head"),
        (100.0, 0.6, 121.0, "the east pier"), (136.0, 6.0, 108.0, "the lighthouse rocks"),
        (-10.0, 1.2, 64.0, "the bandstand"), (100.0, 0.2, 72.0, "the crane"),
        (-150.0, 0.2, 86.0, "the quay steps"), (150.0, 0.2, 86.0, "the end of the quay"),
        (-75.0, 0.2, 76.0, "the fish market"), (-160.0, 0.2, 48.0, "the high street"),
        (160.0, 0.2, 36.0, "the gift shop"), (60.0, 0.2, 70.0, "the ice cream kiosk"),
    ]
    for x, y, z, name in stranded:
        b.mark("stranded", x, y, z, name=name)
    for x, y, z in ((-130.0, 0.2, 64.0), (30.0, 0.2, 64.0), (120.0, 0.2, 64.0),
                    (-80.0, 8.0, 20.0), (60.0, 8.0, 20.0), (-140.0, 16.0, -18.0),
                    (60.0, 16.0, -18.0), (-60.0, 24.0, -54.0), (90.0, 24.0, -54.0),
                    (-120.0, 32.0, -120.0), (60.0, 32.0, -100.0)):
        b.mark("crate", x, y, z)
    for x, z, name in ((0.0, 60.0, "the promenade"), (-75.0, 76.0, "the fish market"),
                       (54.0, 74.0, "the coastguard tower"), (150.0, 124.0, "the lighthouse"),
                       (0.0, 110.0, "the harbour"), (-120.0, 48.0, "the west end"),
                       (120.0, 48.0, "the east end"), (0.0, 8.0, "the cottages"),
                       (-80.0, -34.0, "the church"), (20.0, -35.0, "the school"),
                       (-15.0, -70.0, "the town hall"), (130.0, -68.0, "the water tower"),
                       (0.0, -120.0, "the helipad"), (-69.0, -123.0, "the clifftop cafe"),
                       (120.0, -130.0, "the radio mast")):
        b.landmark(x, z, name)
    b.camera(0.0, 70.0, 150.0, 0.0, 10.0, 0.0)
    b.camera(-160.0, 50.0, 80.0, 0.0, 6.0, 40.0)
    b.camera(150.0, 60.0, -150.0, 0.0, 12.0, -30.0)
    b.extra.update({"accent": "#2a8ad8", "disasters": DISASTERS})


DISASTERS = [
    {"id": "tsunami", "name": "Tsunami", "line": "Get above the second terrace!", "seconds": 46.0,
     "safe": ["high"],
     "parts": [{"kind": "level", "medium": "water", "from": SEA_TOP, "to": 20.0, "rise": 20.0,
                "fall": 10.0, "dps": 26.0, "flow": [0.0, -1.0]}]},
    {"id": "lightning", "name": "Lightning Storm", "line": "Get under a roof!", "seconds": 45.0,
     "safe": ["shelter"],
     "parts": [{"kind": "strikes", "what": "lightning", "every": [0.45, 0.9], "r": 5.0,
                "damage": 75.0, "warn": 1.3, "open": True},
               {"kind": "rain", "what": "storm", "dps": 0.0}]},
    {"id": "meteors", "name": "Meteor Shower", "line": "Find a roof -- and stay under it!",
     "seconds": 44.0, "safe": ["shelter"],
     "parts": [{"kind": "strikes", "what": "meteor", "every": [0.3, 0.7], "r": 8.0,
                "damage": 60.0, "warn": 2.0}]},
    {"id": "tornado", "name": "Tornado", "line": "Get inside, away from the high street!",
     "seconds": 48.0, "safe": ["shelter", "high"],
     "parts": [{"kind": "tornado", "path": [[-150.0, 50.0], [150.0, 50.0]], "speed": 8.0,
                "r": 28.0, "core": 9.0, "dps": 25.0},
               {"kind": "strikes", "what": "debris", "every": [1.0, 2.0], "r": 5.0,
                "damage": 35.0, "warn": 1.5}]},
]


def build(b: ArenaArea) -> None:
    rng = random.Random(7120)
    hx, hz = HALF
    m = b.margin
    ground(b, GROUND, soil="#7a6a54", material="", holes=[rect(-hx - m, hx + m, QUAY_EDGE, hz + m)])
    s = Surfaces(b)
    for top, z0, z1 in TERRACES:
        s.reserve(rect(-hx, hx, z0, z1))
    for x, lo, hi, wall in STAIRS:
        if lo == 0.0:
            s.reserve(rect(x - STAIR_W / 2.0, x + STAIR_W / 2.0, wall, wall + STAIR_RUN))
    _edges(b, rng)
    _land(b, s)
    _quay(b, rng)
    _harbour(b, rng)
    _street(b, rng)
    _terraces(b, rng)
    _park(b, rng)
    _meta(b)
