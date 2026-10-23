"""Summit Village -- a ski village at the foot of a long snow slope, a
frozen lake, a gorge with a rope bridge, an old silver mine on the far
bank, and the cable car up to the peak station and the observatory.

Layout (north is -z; the slope climbs to the north)::

    z -150  ======== THE PEAK (y 36): the top station, the observatory =========
            ////////// THE SLOPE: snow in long steps, lift pylons, ///////////
            ////////// avalanche fences, stranded skiers          ///////////
    z  -10  -- WEST BANK ---|gorge|-- THE VILLAGE: the lodge, chalets, the
                the old     |rope |   cafe, the chapel, the valley station
                mine, pines |bridge|
    z   84                  |     |   the hot spring    THE FROZEN LAKE
    z  150  ================|stone bridge|============== (the rink) =========

The disasters: an **avalanche** down three lanes of the slope (get behind
something, or inside), a **blizzard** (get inside or by a fire), an
**earthquake** that drops the rope bridge and the mine's scaffold (get out in
the open), and a **rockslide** down the west bank and the east road.
"""
from __future__ import annotations

import math
import random

from ..kit import ArenaArea, Surfaces, backdrop, flight, ground, perimeter, rect, slab
from . import town
from .town import bench, crate_pile, helipad, house, lookout_tower, solid, street_lamp

HALF = (170.0, 150.0)
SKY = {"top": "#5a8ac8", "horizon": "#e8f0f8", "sun": [0.3, 0.55, 0.5], "clouds": 0.5,
       "tint": "#f0f4ff"}
AMBIENT = "#b4bccc"
GROUND = "#eef2f6"
FOG = 700.0

SNOW = "#eef2f6"
SNOW_SHADE = "#dde6ee"
ICE = "#b8dcef"
ROCK = "#7a8088"
ROCK_DARK = "#5a6068"
TIMBER = "#6a4a2a"
PINE = "#2a5a3c"
WALLS = ["#8a5a3a", "#a06a44", "#7a4a2a", "#f0e8d8", "#c89a6a"]
ROOFS = ["#3a3a44", "#7a2a2a", "#2a4a3a", "#4a3a2a"]

GORGE = (-110.0, -80.0)          # x0, x1: the gorge runs north to south
GORGE_FLOOR = -24.0
SLOPE_FOOT = -10.0
STEP_RUN, STEP_RISE, STEPS = 5.0, 1.5, 23
PEAK = 36.0
LAKE = (60.0, 160.0, 84.0, 140.0)


def slope_top(z: float) -> float:
    """The height of the snow at ``z`` on the slope (0 below its foot)."""
    if z >= SLOPE_FOOT:
        return 0.0
    k = int(math.ceil((SLOPE_FOOT - z) / STEP_RUN - 1e-6))
    return PEAK if k > STEPS else k * STEP_RISE


# ================================================================ the land
def _land(b: ArenaArea, s: Surfaces, rng: random.Random) -> None:
    hx, hz = HALF
    g0, g1 = GORGE
    # the slope, step by step, and the peak's plateau
    for k in range(1, STEPS + 1):
        z1 = SLOPE_FOOT - (k - 1) * STEP_RUN
        z0 = z1 - STEP_RUN
        solid(b, rect(-hx, hx, z0, z1), k * STEP_RISE, SNOW if k % 2 else SNOW_SHADE)
    solid(b, rect(-hx, hx, -hz, SLOPE_FOOT - STEPS * STEP_RUN), PEAK, SNOW)
    # the gorge: its rock walls, the river at the bottom, a stair out
    # (the linings stand inside the cut, back to back with the ground's edge)
    for x0, x1 in ((g0, g0 + 3.0), (g1 - 3.0, g1)):
        slab(b, rect(x0, x1, SLOPE_FOOT + 0.6, hz), 0.0, -GORGE_FLOOR, ROCK_DARK)
    slab(b, rect(g0, g1, SLOPE_FOOT, SLOPE_FOOT + 0.6), 0.0, -GORGE_FLOOR, ROCK_DARK)
    slab(b, rect(g0 + 3.0, g1 - 3.0, SLOPE_FOOT + 0.6, hz), GORGE_FLOOR, 4.0, "#6a6a62")
    b.box([(g0 + g1) / 2.0, GORGE_FLOOR + 0.5, (SLOPE_FOOT + 0.6 + hz) / 2.0],
          [g1 - g0 - 8.0, 0.6, hz - SLOPE_FOOT - 0.6], "#5a9ab8", material="glass", alpha=0.7,
          collide=False)
    flight(b, "z", 118.0, 146.0, g0 + 3.0, g0 + 11.0, GORGE_FLOOR, 0.0, ROCK, fill=GORGE_FLOOR)
    for k in range(8):
        z = SLOPE_FOOT + 10.0 + k * 17.0
        b.box([g1 - 6.0 - (k % 2) * 6.0, GORGE_FLOOR + 1.2, z], [3.0, 2.4, 2.6], ROCK)
    # the stone bridge, and the rope bridge (an earthquake drops it)
    slab(b, rect(g0 - 3.0, g1 + 3.0, 104.0, 116.0), 0.6, 0.6, "#8a8478")
    for x in (g0 + 5.0, g1 - 5.0):
        b.box([x, (GORGE_FLOOR + 0.0) / 2.0, 110.0], [4.0, -GORGE_FLOOR, 8.0], "#8a8478")
    for z in (104.6, 115.4):
        b.box([(g0 + g1) / 2.0, 1.6, z], [g1 - g0 + 6.0, 2.0, 1.2], "#8a8478")
    with b.detached() as parts:
        slab(b, rect(g0 - 1.0, g1 + 1.0, 28.0, 34.0), 0.4, 0.4, "#8a6a44")
        for z in (28.3, 33.7):
            b.box([(g0 + g1) / 2.0, 2.6, z], [g1 - g0 + 2.0, 0.3, 0.3], "#c8b080")
    b.dynamic("bridge", parts, on=True, group="bridge")
    for x in (g0 - 1.6, g1 + 1.6):
        for z in (27.4, 34.6):
            b.box([x, 2.0, z], [0.8, 4.0, 0.8], TIMBER)
    # the frozen lake and the rink on it
    lx0, lx1, lz0, lz1 = LAKE
    s.lay(rect(lx0, lx1, lz0, lz1), 0.12, ICE)
    for x0, x1, z in ((90.0, 130.0, 96.0), (90.0, 130.0, 124.0)):
        b.box([(x0 + x1) / 2.0, 0.12 + 0.8, z], [x1 - x0, 1.6, 0.6], "#f4f4f4")
    for x in (90.0, 130.0):
        b.box([x, 0.12 + 0.8, 110.0], [0.6, 1.6, 27.4], "#f4f4f4")
    # the village's packed-snow lanes
    s.lay(rect(-80.0, hx, 30.0, 38.0), 0.1, "#c8ccd0")
    s.lay(rect(-4.0, 4.0, SLOPE_FOOT, 84.0), 0.1, "#c8ccd0")


def _village(b: ArenaArea, rng: random.Random) -> None:
    y = 0.0
    # the ski lodge with its great fireplace
    house(b, (-64.0, -18.0, -6.0, 24.0), y, "#7a4a2a", "#3a3a44", "z+", height=14.0,
          sign="SUMMIT LODGE", sign_colours=("#3a2414", "#f4e0b0"), rng=rng, tiers=4)
    b.box([-41.0, y + 3.4, -3.4], [8.0, 6.8, 2.4], "#7a6a5a", decal="bricks")
    b.box([-41.0, y + 1.4, -2.0], [4.0, 1.6, 0.4], "#ff8a2a", material="neon")
    b.mark("heat", -41.0, y + 0.4, 2.0, r=10.0)
    chalets = [(10.0, 34.0, -4.0, 14.0, "z+"), (44.0, 68.0, -4.0, 14.0, "z+"),
               (80.0, 104.0, -4.0, 14.0, "z+"), (116.0, 140.0, -4.0, 14.0, "z+"),
               (10.0, 34.0, 44.0, 62.0, "z-"), (80.0, 104.0, 44.0, 62.0, "z-"),
               (120.0, 144.0, 44.0, 62.0, "z-"), (-60.0, -36.0, 44.0, 62.0, "z-")]
    for k, (x0, x1, z0, z1, door) in enumerate(chalets):
        house(b, (x0, x1, z0, z1), y, WALLS[k % len(WALLS)], ROOFS[k % len(ROOFS)], door,
              height=10.0, rng=rng, tiers=4)
    house(b, (44.0, 68.0, 44.0, 62.0), y, "#f0e8d8", "#7a2a2a", "z-", height=11.0,
          sign="CAFE", sign_colours=("#7a2a2a", "#f4f0e8"), rng=rng)
    b.mark("heat", 56.0, y + 0.4, 52.0, r=8.0)
    house(b, (-30.0, -6.0, 44.0, 64.0), y, "#e8e0d0", "#3a3a44", "z-", height=13.0,
          sign="CHAPEL", sign_colours=("#3a3a44", "#f4f0e8"), rng=rng, gable_along="z", tiers=4)
    house(b, (150.0, 168.0, -4.0, 22.0), y, "#a06a44", "#2a4a3a", "x-", height=10.0,
          sign="SKI HIRE", sign_colours=("#2a4a3a", "#f4f0e8"), rng=rng)
    # the valley station of the cable car
    house(b, (-4.0 - 10.0, 4.0 + 10.0, 66.0, 82.0), y, "#c8ccd4", "#c8302a", "z-", height=12.0,
          sign="CABLE CAR", sign_colours=("#c8302a", "#f4f4f4"), rng=rng)
    # campfires round the village: fire pits to warm up by
    for x, z in ((-40.0, 38.0), (40.0, 26.0), (110.0, 26.0), (-130.0, 60.0)):
        _campfire(b, x, z, y)
    # the hot spring by the lake
    b.box([30.0, 0.3, 110.0], [22.0, 0.6, 18.0], ROCK)
    b.box([30.0, 0.62, 110.0], [18.0, 0.04, 14.0], "#7ad8e8", material="glass", alpha=0.75,
          collide=False)
    for x, z in ((20.0, 102.0), (40.0, 118.0)):
        b.box([x, 1.5, z], [3.0, 1.8, 3.0], ROCK)
    b.mark("heat", 30.0, 0.6, 110.0, r=12.0)
    # lamps, benches, sledges, skis in racks
    for x in range(-60, 170, 30):
        street_lamp(b, float(x), 28.0, y, 10.0)
    for x in (-10.0, 76.0, 126.0):
        bench(b, x, 40.0, y + 0.1, "x")
    for x, z in ((-20.0, 26.0), (70.0, 40.0)):
        b.box([x, 1.0, z], [6.0, 2.0, 1.0], TIMBER)
        for k in range(5):
            b.box([x - 2.4 + k * 1.2, 3.4, z + 0.3], [0.3, 6.8, 0.2], ["#c8302a", "#2a6ac8", "#f2c230"][k % 3])
    crate_pile(b, 146.0, 34.0, 0.1, rng, "#8a6a44")


def _campfire(b: ArenaArea, x: float, z: float, y: float) -> None:
    for k in range(8):
        a = k * math.pi / 4.0
        b.box([x + math.cos(a) * 2.2, y + 0.4, z + math.sin(a) * 2.2], [1.0, 0.8, 1.0], ROCK)
    b.box([x, y + 0.3, z], [2.0, 0.6, 2.0], "#4a3a2a")
    b.cone([x, y + 0.6 + 1.0, z], [1.6, 2.0, 1.6], "#ff8a2a", material="neon")
    b.mark("heat", x, y, z + 4.5, r=8.0)


def _slope(b: ArenaArea, rng: random.Random) -> None:
    """Lift pylons up the slope, avalanche fences to hide behind, the
    cable car's line, and the pines along the sides."""
    for z in (-30.0, -60.0, -90.0, -118.0):
        y = slope_top(z)
        for x in (-140.0, 150.0):
            b.cyl([x, y + 7.0, z], [1.2, 14.0, 1.2], "#5a6068", material="metal")
            b.box([x, y + 14.4, z], [6.0, 0.8, 0.8], "#5a6068", material="metal")
    # avalanche fences: solid snow-fence panels across the fall line
    for x, z in ((-70.0, -40.0), (-20.0, -55.0), (50.0, -40.0), (90.0, -70.0), (-60.0, -95.0),
                 (10.0, -100.0), (130.0, -105.0), (-110.0, -70.0), (140.0, -45.0)):
        y = slope_top(z)
        b.box([x, y + 2.5, z + 0.3], [18.0, 5.0, 0.6], TIMBER, decal="planks")
        b.mark("shelter", x, y, z + 2.6)
    # the cable car line: a pylon behind the valley station, one on the top
    # station's roof, the cable between them and two cabins on it
    (za, ya), (zb, yb) = (88.0, 16.0), (-137.0, 60.0)
    roof = PEAK + 12.0 + 0.8 + 3 * 1.2 - 0.2
    b.cyl([0.0, ya / 2.0, za], [1.6, ya, 1.6], "#5a6068", material="metal")
    b.cyl([0.0, (roof + yb) / 2.0, zb], [1.6, yb - roof, 1.6], "#5a6068", material="metal")
    length = math.hypot(za - zb, yb - ya)
    tilt = math.atan2(-(za - zb), yb - ya)
    for x in (-0.9, 0.9):
        b.cyl([x, (ya + yb) / 2.0, (za + zb) / 2.0], [0.25, length, 0.25], "#2a2a2a",
              collide=False, r=[tilt, 0.0, 0.0])
    for k, z in enumerate((-20.0, -70.0)):
        y = ya + (yb - ya) * (za - z) / (za - zb)
        b.box([0.0, y - 4.2, z], [4.0, 4.0, 5.0], "#c8302a" if k else "#2a6ac8")
        b.box([0.0, y - 1.6, z], [0.3, 1.2, 0.3], "#3a3a3a")
    for x in range(-160, 165, 22):
        for z in (-25.0, -80.0, -128.0):
            if abs(x) < 20 or abs(x + 60) < 14 or abs(x - 50) < 14 or -120 < x < -60 or \
                    -30 < x < 20 and z == -80.0 or 100 < x < 140:
                continue
            zz = z + rng.uniform(-3.0, 3.0)
            b.pine(float(x) + rng.uniform(-4, 4), zz, slope_top(zz), 0.9, leaf_c=PINE)


def _peak(b: ArenaArea, rng: random.Random) -> None:
    y = PEAK
    helipad(b, -40.0, -138.0, y, 11.0)
    house(b, (-14.0, 14.0, -146.0, -128.0), y, "#c8ccd4", "#c8302a", "z+", height=12.0,
          sign="TOP STATION", sign_colours=("#c8302a", "#f4f4f4"), rng=rng)
    # the observatory and its dome
    house(b, (60.0, 84.0, -146.0, -128.0), y, "#e8ecf0", "#5a6068", "z+", height=10.0,
          rng=rng, furnish=False)
    b.sphere([72.0, y + 10.0 + 4.4 + 2.0, -137.0], [14.0, 10.0, 14.0], "#d8dce4")
    b.box([72.0, y + 21.0, -137.0], [2.0, 3.0, 8.0], "#3a3a44")
    lookout_tower(b, 130.0, -138.0, y, 14.0, "#7a8088", "#5a6068", core=8.0, width=4.0,
                  cap="#5a6068", start="x-")
    for x, z in ((-120.0, -140.0), (-150.0, -132.0), (110.0, -130.0), (40.0, -144.0)):
        b.pine(x, z, y, 1.0, leaf_c=PINE)


def _west_bank(b: ArenaArea, rng: random.Random) -> None:
    """The old silver mine: its shed, the adit into the hill, the timber
    scaffold walkway over the gorge's edge (an earthquake drops it)."""
    y = 0.0
    house(b, (-160.0, -134.0, 0.0, 18.0), y, "#7a5a3a", "#4a3a2a", "z+", height=10.0,
          sign="SILVER MINE", sign_colours=("#3a2414", "#d8d0c0"), rng=rng)
    house(b, (-168.0, -146.0, 120.0, 140.0), y, "#8a6a4a", "#3a3a44", "x+", height=10.0, rng=rng)
    with b.detached() as parts:
        slab(b, rect(-128.0, -112.0, 70.0, 90.0), 8.0, 0.6, "#8a6a44")
        for x in (-127.4, -112.6):
            b.box([x, 9.0, 80.0], [0.4, 1.4, 20.0], TIMBER)
    b.dynamic("scaffold", parts, on=True, group="scaffold")
    for x in (-127.0, -113.0):
        for z in (70.6, 89.4):
            b.box([x, 3.7, z], [1.0, 7.4, 1.0], TIMBER)
    flight(b, "z", 100.0, 90.0, -126.0, -120.0, 0.0, 8.0, "#8a6a44", fill=-0.3)
    for x in (-160.0, -146.0, -126.0, -150.0, -138.0, -160.0, -130.0, -150.0):
        z = rng.uniform(30.0, 145.0)
        if 64.0 < z < 104.0 and x > -132.0:
            continue
        b.pine(x, z, 0.0, 1.0 + rng.uniform(-0.1, 0.2), leaf_c=PINE)
    crate_pile(b, -150.0, 40.0, 0.1, rng, "#8a6a44")
    b.box([-140.0, 1.0, 50.0], [6.0, 2.0, 3.0], "#5a4a3a")
    b.box([-140.0, 2.6, 50.0], [5.0, 1.2, 2.4], "#7a7a7a")


def _edges(b: ArenaArea, rng: random.Random) -> None:
    perimeter(b, 68.0, "#7a8088", cap="#eef2f6", rng=rng, ragged=6.0)
    town.skirt(b, HALF[0], HALF[1], "#dde6ee", top=GORGE_FLOOR - 4.05)
    backdrop(b, "peaks", 50.0, rng, colours=["#dde6ee", "#c8d4e0", "#eef2f6"])


# ================================================================ the meta
def _meta(b: ArenaArea) -> None:
    for x in (-72.0, -64.0, -54.0, -46.0):
        for z in (31.0, 35.0):
            b.team_spawn("red", x, None, z, yaw=0.0)
    for x in (66.0, 74.0, 82.0, 98.0):
        for z in (31.0, 35.0):
            b.team_spawn("blue", x, None, z, yaw=0.0)
    for x, z in ((-70.0, -136.0), (-100.0, -130.0), (30.0, -132.0), (100.0, -134.0),
                 (160.0, -130.0), (-150.0, -140.0)):
        b.mark("high", x, PEAK, z)
    for x, z in ((0.0, 20.0), (-20.0, 76.0), (60.0, 76.0), (110.0, 74.0), (140.0, 74.0),
                 (-140.0, 100.0), (-150.0, 30.0), (100.0, 110.0), (140.0, 130.0),
                 (70.0, 30.0), (-60.0, 76.0)):
        b.mark("open", x, 0.1 if x < 60 or z < 84 else 0.12, z)
    for x, z in ((-41.0, 26.0), (22.0, 16.0), (56.0, 16.0), (92.0, 16.0), (128.0, 16.0),
                 (22.0, 42.0), (92.0, 42.0), (-48.0, 42.0), (-18.0, 66.0), (56.0, 64.0),
                 (-147.0, 20.0), (0.0, 64.0), (159.0, 9.0)):
        b.mark("debris", x, 0.0, z)
    stranded = [(-50.0, "a skier halfway up"), (-100.0, "a skier near the top"),
                (-40.0, "a snowboarder"), (-75.0, "a skier by the pylons")]
    for (z, name), x in zip(stranded, (-30.0, 60.0, 120.0, -120.0)):
        b.mark("stranded", x, slope_top(z), z, name=name)
    for x, y, z, name in ((-95.0, GORGE_FLOOR, 60.0, "the bottom of the gorge"),
                          (110.0, 0.12, 110.0, "the ice rink"), (30.0, 0.6, 112.0, "the hot spring"),
                          (-120.0, 8.0, 80.0, "the mine scaffold"), (-150.0, 0.0, 60.0, "the woods"),
                          (150.0, 0.12, 130.0, "the far side of the lake"),
                          (-140.0, 0.0, 135.0, "the woodcutter's hut"), (160.0, 0.0, 40.0, "the ski hire")):
        b.mark("stranded", x, y, z, name=name)
    for x, y, z in ((-80.0 + 10.0, 0.1, 34.0), (0.0, 0.1, 40.0), (40.0, 0.1, 34.0),
                    (130.0, 0.1, 34.0), (-140.0, 0.0, 90.0), (70.0, 0.12, 100.0),
                    (-40.0, slope_top(-60.0), -60.0), (80.0, slope_top(-110.0), -110.0),
                    (40.0, PEAK, -140.0), (150.0, 0.1, -2.0)):
        b.mark("crate", x, y, z)
    for x, z, name in ((-41.0, 10.0, "the lodge"), (0.0, 74.0, "the cable car"), (56.0, 52.0, "the cafe"),
                       (-18.0, 54.0, "the chapel"), (110.0, 110.0, "the frozen lake"),
                       (30.0, 110.0, "the hot spring"), (-95.0, 31.0, "the rope bridge"),
                       (-95.0, 110.0, "the stone bridge"), (-147.0, 9.0, "the silver mine"),
                       (-120.0, 80.0, "the scaffold"), (0.0, -60.0, "the slope"),
                       (0.0, -137.0, "the top station"), (72.0, -137.0, "the observatory"),
                       (159.0, 9.0, "the ski hire")):
        b.landmark(x, z, name)
    b.camera(0.0, 60.0, 150.0, 0.0, 6.0, 0.0)
    b.camera(-160.0, 70.0, -150.0, 0.0, 10.0, 0.0)
    b.camera(150.0, 30.0, 120.0, -20.0, 4.0, 20.0)
    b.extra.update({"accent": "#7ab8e8", "disasters": DISASTERS})


DISASTERS = [
    {"id": "avalanche", "name": "Avalanche", "line": "Get behind something solid -- or inside!",
     "seconds": 42.0, "safe": ["shelter"],
     "parts": [{"kind": "front", "what": "snow", "weapon": "the avalanche", "speed": 16.0,
                "depth": 18.0, "dps": 80.0,
                "lanes": [{"pts": [[-50.0, -150.0], [-50.0, 70.0]], "w": 40.0, "delay": 0.0},
                          {"pts": [[30.0, -150.0], [30.0, 70.0]], "w": 40.0, "delay": 5.0},
                          {"pts": [[110.0, -150.0], [110.0, 70.0]], "w": 40.0, "delay": 10.0},
                          {"pts": [[-10.0, -150.0], [-10.0, 70.0]], "w": 36.0, "delay": 20.0},
                          {"pts": [[150.0, -150.0], [150.0, 70.0]], "w": 30.0, "delay": 24.0}]}]},
    {"id": "blizzard", "name": "Blizzard", "line": "Get inside, or get by a fire!", "seconds": 48.0,
     "safe": ["heat", "shelter"],
     "parts": [{"kind": "cold", "rate": 0.07, "dps": 9.0},
               {"kind": "wind", "dir": [1.0, 0.0], "strength": 9.0, "gust": [5.0, 5.0]}]},
    {"id": "quake", "name": "Earthquake", "line": "Out in the open, away from the buildings!",
     "seconds": 40.0, "safe": ["open"],
     "parts": [{"kind": "quake", "collapse": [[8.0, "bridge"], [18.0, "scaffold"]], "power": 1.0,
                "names": {"bridge": "the rope bridge", "scaffold": "the mine scaffold"}},
               {"kind": "strikes", "what": "debris", "aim": "marks", "marks": "debris",
                "every": [0.5, 1.0], "r": 6.0, "damage": 45.0, "warn": 1.5}]},
    {"id": "rockslide", "name": "Rockslide", "line": "Off the west bank and the east road!",
     "seconds": 40.0, "safe": ["shelter", "open"],
     "parts": [{"kind": "front", "what": "rocks", "weapon": "the rockslide", "speed": 14.0,
                "depth": 14.0, "dps": 70.0,
                "lanes": [{"pts": [[-140.0, -150.0], [-140.0, 150.0]], "w": 50.0, "delay": 0.0},
                          {"pts": [[160.0, -150.0], [160.0, 84.0]], "w": 20.0, "delay": 6.0}]},
               {"kind": "strikes", "what": "boulder", "every": [0.8, 1.6], "r": 6.0,
                "damage": 55.0, "warn": 1.6}]},
]


def build(b: ArenaArea) -> None:
    rng = random.Random(3117)
    hx, hz = HALF
    ground(b, GROUND, soil="#8a8a90", material="", holes=[rect(GORGE[0], GORGE[1], SLOPE_FOOT, hz)])
    s = Surfaces(b)
    s.reserve(rect(-hx, hx, -hz, SLOPE_FOOT))
    s.reserve(rect(GORGE[0] - 3.0, GORGE[1] + 3.0, SLOPE_FOOT, hz))
    _edges(b, rng)
    _land(b, s, rng)
    _village(b, rng)
    _slope(b, rng)
    _peak(b, rng)
    _west_bank(b, rng)
    _meta(b)
