"""Palm Key -- a resort island under a volcano: the beach and its huts, the
hotel with stairs to its roof, the pool and the tiki bar, the jungle with
the ruins of a stepped temple, and the volcano itself, smoking over the
west of the island.

Layout (north is -z; the sea is to the south)::

    z -150  ===== THE VOLCANO (west): ======== THE JUNGLE (east): ===========
                  stepped flanks up to         the temple ruins, the
                  a crater of lava             waterfall pool, the lookout
    z  -20  ---------------------------------------------------------------
                  THE RESORT: the hotel (stairs to the roof), the pool,
                  the tiki bar, the reception, bungalows on stilts
    z   70  ------------------- THE BEACH: palms, loungers, the lifeguard
    z  100  ==== the lagoon: the pier and the seaplane =======================
    z  150

The disasters: an **eruption** (lava floods the plain round the volcano and
bombs fall), a **hurricane** (gusts out to sea and falling coconuts), a
**tsunami** (get onto the temple, the volcano's upper flanks or the hotel
roof), and **sinkholes** opening under the resort's lawns.
"""
from __future__ import annotations

import random

from ..kit import ArenaArea, Surfaces, backdrop, flight, ground, perimeter, rect, slab
from . import town
from .town import crate_pile, helipad, house, lookout_tower, palm, pier, stairs

HALF = (170.0, 150.0)
SKY = {"top": "#3a8ae0", "horizon": "#f0e8c8", "sun": [0.55, 0.8, 0.25], "clouds": 0.4,
       "tint": "#fff0d0"}
AMBIENT = "#b8b4a4"
GROUND = "#5a9a3a"
FOG = 760.0

SAND = "#ecd8a0"
SAND_WET = "#d8c088"
LAWN = "#5a9a3a"
JUNGLE = "#3a7a2a"
ROCK = "#5a4e48"
ROCK_DARK = "#3a3230"
STONE = "#a89a7a"
LAGOON = "#2ab0c8"
LAVA = "#ff6a1a"
WOOD = "#9a7448"

SHORE = 100.0
SEABED = -6.0
SEA_TOP = -1.0
VOLCANO = (-100.0, -90.0, 56.0)       # centre x, z, half-size at the foot
TIERS = 15
TIER_RISE, TIER_STEP = 2.0, 3.2
TEMPLE = (100.0, -95.0)
# the sinkholes: pits under lawn that holds until the ground gives way
PITS = [(-40.0, 10.0), (10.0, 58.0), (60.0, 10.0), (100.0, 50.0), (-80.0, 50.0), (140.0, 8.0)]
PIT = 12.0
PIT_FLOOR = -8.0


# ================================================================ the land
def _land(b: ArenaArea, s: Surfaces) -> None:
    hx, hz = HALF
    m = b.margin
    sea = rect(-hx, hx, SHORE, hz + m)
    slab(b, sea, SEABED, 4.0, SAND_WET)
    b.box([0.0, (SEABED + SEA_TOP) / 2.0, (SHORE + 12.0 + hz) / 2.0],
          [2 * hx, SEA_TOP - SEABED, hz - SHORE - 12.0], LAGOON, material="glass", alpha=0.5,
          collide=False)
    # the beach shelves into the lagoon in two steps
    slab(b, rect(-hx, hx, SHORE, SHORE + 6.0), -2.0, 4.0, SAND)
    slab(b, rect(-hx, hx, SHORE + 6.0, SHORE + 12.0), -4.0, 2.0, SAND_WET)
    b.box([0.0, (-4.0 + SEA_TOP) / 2.0 + 0.0, SHORE + 9.0], [2 * hx, SEA_TOP - (-4.0), 6.0], LAGOON,
          material="glass", alpha=0.5, collide=False)
    for sx in (-1.0, 1.0):
        b.box([sx * (hx + m / 2.0), SEABED / 2.0, (SHORE + hz + m) / 2.0], [m, -SEABED, hz + m - SHORE],
              ROCK)
    s.lay(rect(-hx, hx, 70.0, SHORE), 0.15, SAND)
    s.lay(rect(-hx, hx, -150.0, -20.0), 0.1, JUNGLE)
    # the resort's paths
    s.lay(rect(-hx, hx, 28.0, 34.0), 0.2, "#d8ccb0")
    s.lay(rect(-4.0, 4.0, -20.0, 70.0), 0.2, "#d8ccb0")


def _volcano(b: ArenaArea, rng: random.Random) -> None:
    """Stepped flanks up to a crater ring with lava in it."""
    cx, cz, half = VOLCANO
    for k in range(TIERS):
        h = half - k * TIER_STEP
        top = (k + 1) * TIER_RISE
        colour = ROCK if k % 2 else ROCK_DARK
        if k < TIERS - 3:
            slab(b, rect(cx - h, cx + h, max(cz - h, -HALF[1]), cz + h), top, TIER_RISE, colour)
        else:
            # the crater: the top tiers are a ring round the lava
            hole = 8.0
            for x0, x1, z0, z1 in ((cx - h, cx + h, cz - h, cz - hole), (cx - h, cx + h, cz + hole, cz + h),
                                   (cx - h, cx - hole, cz - hole, cz + hole),
                                   (cx + hole, cx + h, cz - hole, cz + hole)):
                slab(b, rect(x0, x1, z0, z1), top, TIER_RISE, colour)
    crater = (TIERS - 3) * TIER_RISE
    b.box([cx, crater + 0.3, cz], [16.0, 0.6, 16.0], LAVA, material="neon")
    # smoke over the crater, high out of reach
    for k in range(4):
        b.sphere([cx + rng.uniform(-4, 4), crater + 30.0 + k * 9.0, cz + rng.uniform(-4, 4)],
                 [16.0 + k * 6.0, 10.0, 16.0 + k * 6.0], "#6a6a6a", collide=False, alpha=0.7)
    # lava streaks down the flanks: glowing strips laid on the tiers
    for k in range(TIERS - 3):
        h = half - k * TIER_STEP
        top = (k + 1) * TIER_RISE
        b.box([cx + 3.0, top + 0.02, cz + h - TIER_STEP / 2.0], [2.0, 0.04, TIER_STEP - 0.4], "#e8501a",
              collide=False)


def _temple(b: ArenaArea, rng: random.Random) -> None:
    """The temple ruins: nine stepped tiers with a stair up the front and a
    shrine on top."""
    tx, tz = TEMPLE
    for k in range(9):
        h = 22.0 - k * 2.2
        b.box([tx, 1.0 + k * 2.0, tz], [h * 2.0, 2.0, h * 2.0], STONE if k % 2 else "#988a6a",
              decal="bricks")
    top = 18.0
    house(b, (tx - 5.0, tx + 5.0, tz - 5.0, tz + 5.0), top, "#988a6a", "#5a5040", "z+",
          height=9.0, windows=False, rng=rng, furnish=False, tiers=2)
    b.mark("high", tx + 8.0, top, tz)
    b.mark("high", tx - 8.0, top, tz)
    for x in (tx - 12.0, tx + 12.0):
        b.box([x, 1.2, tz + 24.5], [2.4, 2.4, 2.4], STONE)
        b.box([x, 4.4, tz + 24.5], [1.8, 4.0, 1.8], "#7a8a5a")


def _resort(b: ArenaArea, rng: random.Random) -> None:
    y = 0.2
    # the hotel, with an outside stair to the roof
    house(b, (-20.0, 30.0, 4.0, 26.0), y, "#f4ecd8", "#c87a4a", "z+", height=21.0,
          sign="HOTEL PARADISO", sign_colours=("#c87a4a", "#f4f0e8"), rng=rng, tiers=3)
    # (up the back wall, clear of the front door)
    flight(b, "x", -20.0, 10.0, -2.0, 4.0, y, y + 21.8, "#e8dcc0", fill=y - 0.3)
    for x, z in ((-12.0, 20.0), (22.0, 10.0)):
        b.mark("high", x, y + 21.8, z)
    # the pool and its loungers
    b.box([60.0, y + 0.6, 50.0], [26.0, 1.2, 14.0], "#f4f4f4")
    b.box([60.0, y + 1.22, 50.0], [23.0, 0.04, 11.0], "#5ad8f0", material="glass", alpha=0.8,
          collide=False)
    for x in (48.0, 54.0, 66.0, 72.0):
        b.box([x, y + 0.6, 60.0], [2.4, 1.2, 5.0], "#f4f4f4")
    # the tiki bar and the reception
    house(b, (-70.0, -48.0, 40.0, 58.0), y, "#9a7448", "#c8a050", "z+", height=10.0,
          sign="TIKI BAR", sign_colours=("#5a3a1a", "#f2c230"), rng=rng, tiers=4)
    house(b, (110.0, 140.0, -2.0, 20.0), y, "#f0e0c0", "#3a8a6a", "z+", height=11.0,
          sign="RECEPTION", sign_colours=("#3a8a6a", "#f4f4f4"), rng=rng)
    # bungalows on stilts, stairs up to their decks
    for k, (x, z) in enumerate(((-140.0, 40.0), (-115.0, 58.0), (135.0, 50.0), (155.0, 30.0))):
        deck = 4.0
        slab(b, rect(x - 8.0, x + 8.0, z - 7.0, z + 7.0), deck, 0.6, WOOD)
        for dx in (-7.4, 7.4):
            for dz in (-6.4, 6.4):
                b.box([x + dx, (deck - 0.6 + y) / 2.0, z + dz], [0.8, deck - 0.6 - y, 0.8], "#6a4a2a")
        house(b, (x - 6.0, x + 6.0, z - 5.0, z + 4.0), deck, ["#f4ecd8", "#e8f0d8"][k % 2],
              "#c8a050", "z+", height=9.0, windows=False, rng=rng, furnish=False, tiers=4)
        stairs(b, "z", z + 7.0 + 5.0, z + 7.0, x + 3.0, x + 7.0, y, deck, WOOD)
    for x, z in ((-100.0, 20.0), (-30.0, 50.0), (80.0, 28.0), (40.0, -8.0), (150.0, -10.0),
                 (-150.0, 10.0), (-60.0, -6.0)):
        palm(b, x, z, y, 13.0 + (abs(x) % 3), rng)


def _sinkholes(b: ArenaArea) -> None:
    """Under each patch of lawn, a pit with a stair out; the lawn over it is
    a switchable solid that gives way when the rules say."""
    for k, (x, z) in enumerate(PITS):
        h = PIT / 2.0
        for x0, x1, z0, z1 in ((x - h, x - h + 0.6, z - h, z + h), (x + h - 0.6, x + h, z - h, z + h),
                               (x - h + 0.6, x + h - 0.6, z - h, z - h + 0.6),
                               (x - h + 0.6, x + h - 0.6, z + h - 0.6, z + h)):
            slab(b, rect(x0, x1, z0, z1), -0.6, -PIT_FLOOR - 0.6, ROCK)
        slab(b, rect(x - h + 0.6, x + h - 0.6, z - h + 0.6, z + h - 0.6), PIT_FLOOR, 2.0, ROCK_DARK)
        b.box([x, PIT_FLOOR + 0.3, z], [PIT - 1.4, 0.6, PIT - 1.4], "#3a7a8a", material="glass",
              alpha=0.7, collide=False)
        flight(b, "x", x - h + 0.6 + 8.0, x - h + 0.6, z + h - 3.6, z + h - 0.6, PIT_FLOOR, -0.6,
               ROCK, fill=PIT_FLOOR)
        with b.detached() as parts:
            slab(b, rect(x - h, x + h, z - h, z + h), 0.0, 0.6, LAWN)
        b.dynamic("sink%d" % k, parts, on=True, group="sink%d" % k)


def _beach(b: ArenaArea, rng: random.Random) -> None:
    y = 0.15
    for k in range(8):
        x = -150.0 + k * 40.0 + rng.uniform(-6, 6)
        palm(b, x, 76.0 + rng.uniform(0, 8), y, 14.0, rng)
    for x in (-120.0, -90.0, -20.0, 10.0, 80.0, 110.0):
        b.box([x, y + 0.6, 90.0], [2.4, 1.2, 5.0], "#f4f4f4")
        b.cyl([x + 3.0, y + 3.0, 90.0], [0.3, 6.0, 0.3], "#8a8a8a")
        b.cone([x + 3.0, y + 6.0 + 0.8, 90.0], [6.0, 1.6, 6.0], ["#e85a5a", "#5a8ae8", "#f2c230"][int(x) % 3])
    # the lifeguard tower, the beach bar, the volleyball net
    lookout_tower(b, -40.0, 86.0, y, 10.0, "#f4f4f4", "#c8302a", core=5.0, width=3.4,
                  cap="#c8302a")
    house(b, (120.0, 140.0, 78.0, 94.0), y, "#9a7448", "#e8c070", "z+", height=10.0,
          sign="SURF SHACK", sign_colours=("#2a8ab0", "#f4f4f4"), rng=rng, tiers=4)
    for x in (30.0, 50.0):
        b.box([x, y + 4.0, 82.0], [0.4, 8.0, 0.4], "#4a4a4a")
    b.box([40.0, y + 6.6, 82.0], [20.0, 2.0, 0.1], "#f4f4f4", decal="netting", collide=False)
    # the pier and the seaplane at its end
    pier(b, 40.0, 48.0, SHORE, 140.0, 0.6, SEABED)
    slab(b, rect(30.0, 58.0, 140.0, 148.0), 0.6, 0.6, WOOD)
    for x in (30.6, 57.4):
        b.cyl([x, (SEABED + 0.0) / 2.0, 144.0], [1.0, -SEABED, 1.0], "#5a4030")
    px, pz = 74.0, 136.0
    for dx in (-3.0, 3.0):
        b.box([px + dx, -0.6, pz], [1.6, 1.6, 14.0], "#e8e8e8")
        b.box([px + dx, 0.8, pz - 2.0], [0.4, 1.2, 0.4], "#3a3a3a")
    b.box([px, 2.6, pz], [3.0, 2.6, 12.0], "#f2c230")
    b.box([px, 3.4, pz - 1.0], [22.0, 0.4, 3.4], "#f2c230")
    b.box([px, 4.4, pz + 5.4], [0.4, 2.4, 2.0], "#c8302a")
    b.box([px, 3.2, pz - 6.8], [1.2, 1.2, 1.6], "#3a3a3a")


def _jungle(b: ArenaArea, rng: random.Random) -> None:
    y = 0.1
    for k in range(26):
        x = rng.uniform(-30.0, 165.0)
        z = rng.uniform(-145.0, -26.0)
        if abs(x - TEMPLE[0]) < 30.0 and abs(z - TEMPLE[1]) < 34.0:
            continue
        if 20.0 < x < 50.0 and -130.0 < z < -100.0:
            continue
        if rng.random() < 0.5:
            palm(b, x, z, y, 12.0 + rng.uniform(0, 4), rng)
        else:
            b.tree(x, z, y, 1.2 + rng.uniform(0, 0.4), leaf_c=JUNGLE)
    # the waterfall pool by the lookout
    b.box([35.0, y + 0.4, -115.0], [24.0, 0.8, 18.0], ROCK)
    b.box([35.0, y + 0.82, -115.0], [20.0, 0.04, 14.0], LAGOON, material="glass", alpha=0.75,
          collide=False)
    lookout_tower(b, 60.0, -132.0, y, 18.0, "#7a6a4a", "#5a4a32", core=7.0, width=4.0,
                  cap="#5a4a32", start="x-")
    crate_pile(b, 140.0, -40.0, y, rng, "#8a6a44")
    helipad(b, 140.0, -130.0, y, 11.0)


def _edges(b: ArenaArea, rng: random.Random) -> None:
    hx, hz = HALF
    m = b.margin
    perimeter(b, 52.0, "#4a6a3a", cap="#3a7a2a", rng=rng, ragged=6.0, gaps=("z+",))
    town.skirt(b, hx, hz, "#3a6a2a", top=PIT_FLOOR - 4.05)
    backdrop(b, "hills", 30.0, rng, sides=("x-", "x+", "z-"), colours=["#3a7a2a", "#4a8a3a"])
    b.box([0.0, (SEABED + 12.0) / 2.0, hz + m / 2.0], [2 * hx, 12.0 - SEABED, m], ROCK)
    for k in range(16):
        x = -hx + (k + 0.5) * 2 * hx / 16.0
        b.box([x, 12.0 + 1.0 + (k % 3) * 0.4, hz + m / 2.0 + rng.uniform(-1.0, 1.0)],
              [2 * hx / 16.0 - 2.0, 2.0 + (k % 3) * 0.8, m - 2.0 - (k % 2) * 0.6], "#6a5e58",
              collide=False)
    b.box([0.0, (SEABED + SEA_TOP) / 2.0, hz + m + 110.0], [2 * (hx + m) + 440.0, SEA_TOP - SEABED, 220.0],
          LAGOON, material="glass", alpha=0.5, collide=False)


# ================================================================ the meta
def _meta(b: ArenaArea) -> None:
    for x in (-124.0, -116.0, -108.0, -100.0, -92.0, -84.0, -76.0, -68.0):
        b.team_spawn("red", x, None, 31.0, yaw=0.0)
    for x in (80.0, 88.0, 96.0, 104.0, 112.0, 120.0, 128.0, 136.0):
        b.team_spawn("blue", x, None, 31.0, yaw=0.0)
    cx, cz, half = VOLCANO
    for k in (8, 9):
        top = (k + 1) * TIER_RISE
        h = half - k * TIER_STEP - 1.6
        b.mark("high", cx + h, top, cz)
        b.mark("high", cx - h, top, cz)
    for x, y, z, name in ((-60.0, 0.15, 92.0, "the beach"), (44.0, 0.6, 138.0, "the end of the pier"),
                          (50.0, 0.6, 146.0, "the seaplane dock"), (-100.0, 6.0, -42.0, "the volcano's foot"),
                          (-60.0, 10.0, -90.0, "the volcano's flank"), (100.0, 0.1, -66.0, "the temple steps"),
                          (35.0, 0.9, -115.0, "the waterfall pool"), (60.0, 1.4, 58.0, "the pool"),
                          (150.0, 0.15, 92.0, "the surf shack"), (-140.0, 4.0, 46.0, "a bungalow deck"),
                          (-150.0, 0.1, -30.0, "the lava fields"), (130.0, 0.1, -110.0, "the jungle")):
        b.mark("stranded", x, y, z, name=name)
    for x, y, z in ((-100.0, 0.2, 30.0), (0.0, 0.2, 31.0), (80.0, 0.2, 31.0), (150.0, 0.2, 31.0),
                    (-60.0, 0.15, 80.0), (100.0, 0.15, 80.0), (40.0, 0.1, -60.0), (140.0, 0.1, -80.0),
                    (-30.0, 0.1, -40.0), (-130.0, 0.2, 0.0)):
        b.mark("crate", x, y, z)
    for x, z, name in ((5.0, 15.0, "the hotel"), (60.0, 50.0, "the pool"), (-59.0, 49.0, "the tiki bar"),
                       (125.0, 9.0, "the reception"), (0.0, 85.0, "the beach"), (44.0, 125.0, "the pier"),
                       (74.0, 136.0, "the seaplane"), (-100.0, -90.0, "the volcano"),
                       (100.0, -95.0, "the temple"), (35.0, -115.0, "the waterfall"),
                       (140.0, -130.0, "the helipad"), (-130.0, 46.0, "the bungalows"),
                       (130.0, 86.0, "the surf shack")):
        b.landmark(x, z, name)
    b.camera(40.0, 70.0, 150.0, 0.0, 6.0, 0.0)
    b.camera(-30.0, 60.0, -10.0, -100.0, 14.0, -90.0)
    b.camera(170.0, 50.0, -150.0, 60.0, 6.0, -40.0)
    holes = [{"key": "sink%d" % k, "p": [x, 0.0, z], "r": PIT / 2.0} for k, (x, z) in enumerate(PITS)]
    disasters = [dict(d) for d in DISASTERS]
    for d in disasters:
        for part in d["parts"]:
            if part["kind"] == "sinkholes":
                part["holes"] = holes
    b.extra.update({"accent": "#ff8a3a", "disasters": disasters})


DISASTERS = [
    {"id": "eruption", "name": "Eruption", "line": "Get away from the volcano -- the lava is coming!",
     "seconds": 46.0, "safe": ["shelter", "high"],
     "parts": [{"kind": "level", "medium": "lava", "from": -2.0, "to": 5.0, "rise": 18.0, "fall": 8.0,
                "dps": 40.0, "rect": [-170.0, -30.0, -150.0, -24.0]},
               {"kind": "strikes", "what": "lava_bomb", "every": [0.4, 0.8], "r": 7.0, "damage": 55.0,
                "warn": 1.8, "rect": [-170.0, 30.0, -150.0, 40.0]}]},
    {"id": "hurricane", "name": "Hurricane", "line": "Get inside, or in the lee of something!",
     "seconds": 46.0, "safe": ["shelter"],
     "parts": [{"kind": "wind", "dir": [0.0, 1.0], "strength": 18.0, "gust": [5.0, 3.0]},
               {"kind": "strikes", "what": "coconut", "every": [0.6, 1.2], "r": 4.0, "damage": 25.0,
                "warn": 1.2},
               {"kind": "rain", "what": "storm", "dps": 0.0}]},
    {"id": "tsunami", "name": "Tsunami", "line": "Up the temple, the volcano or the hotel roof!",
     "seconds": 46.0, "safe": ["high"],
     "parts": [{"kind": "level", "medium": "water", "from": SEA_TOP, "to": 14.0, "rise": 20.0,
                "fall": 10.0, "dps": 26.0, "flow": [0.0, -1.0]}]},
    {"id": "sinkholes", "name": "Sinkholes", "line": "Stay off the lawns -- the ground is giving way!",
     "seconds": 42.0, "safe": ["shelter", "high"],
     "parts": [{"kind": "sinkholes", "every": [3.5, 6.0], "warn": 3.0, "floor": -3.0, "holes": []}]},
]


def build(b: ArenaArea) -> None:
    rng = random.Random(5512)
    hx, hz = HALF
    m = b.margin
    pits = [rect(x - PIT / 2.0, x + PIT / 2.0, z - PIT / 2.0, z + PIT / 2.0) for x, z in PITS]
    ground(b, GROUND, soil="#6a5a40", material="grass", holes=[rect(-hx - m, hx + m, SHORE, hz + m)] + pits)
    s = Surfaces(b)
    for p in pits:
        s.reserve(p)
    cx, cz, half = VOLCANO
    s.reserve(rect(cx - half, cx + half, -hz, cz + half))
    s.reserve(rect(TEMPLE[0] - 22.0, TEMPLE[0] + 22.0, TEMPLE[1] - 22.0, TEMPLE[1] + 22.0))
    _edges(b, rng)
    _land(b, s)
    _volcano(b, rng)
    _temple(b, rng)
    _resort(b, rng)
    _sinkholes(b)
    _beach(b, rng)
    _jungle(b, rng)
    _meta(b)
