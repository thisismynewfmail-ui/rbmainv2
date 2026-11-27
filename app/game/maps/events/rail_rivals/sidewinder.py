"""Sidewinder Dunes -- a borax line across a sea of sand, with a sandstorm
on the horizon.

Layout (north is -z; both tracks run west to east)::

    z -250  BORAX WORKS: refinery, vats,        dunes            dunes     BORAX
            cottonball heaps, the 20-mule team                              JUNCTION
            (lane a start) ---\\          DRY WELLS: the ghost town      /--- (lane b end)
    z    0  THE LOST ENGINE   \\  dunes  half under the sand  ===X===  THE DUNE SEA   FURNACE
            in its hollow      /           (saloon, bank, church)  \\  the stranded   SPRINGS
            (lane b start) ---/       SALT PAN and its mirage        \\  schooner     MISSION
    z +250  OASIS HALT: the spring, palms,       THE BONEYARD (the sea      (lane a end)
            the caravanserai, the camels         serpent in the rock)

The land is dunes: barchans marching east before the wind, a gentle back
on the west and a steep slip face on the east, horns trailing downwind.
The lines run in cuttings through them and on banks across the troughs.

The twist is Silverpine's, in sand (``drifts``, ``drift_style`` sand):
every so often the wind lays a drift across the track ahead of a cart and
its company has to dig it out (hold E by it; two diggers dig twice as
fast).
"""
from __future__ import annotations

import math
import random

from ..kit import (WARM, WOOD, WOOD_DARK, WOOD_LIGHT, ArenaArea, backdrop, building, carve,
                   flight, gable, ground, lantern, plate, rect, room_walls, sign_decal, slab,
                   threshold, wall, wall_sign)
from . import common, rails
from .land import Land, graded, lay_graded, world_lane
from .rails import clear_of, fillet, mirror, storeyed, telegraph
from .scenery import locomotive, outcrop, pup_tent, stub_track

HALF = (400.0, 250.0)
SKY = {"top": "#7a9ec4", "horizon": "#f0d6a6", "sun": [0.42, 0.62, -0.4],
       "clouds": 0.35, "tint": "#ffe8c4"}
AMBIENT = "#c8b08c"
GROUND = "#e0c48a"
FOG = 880.0

SAND = "#e0c48a"
SAND_LIGHT = "#ecd6a4"
SAND_PALE = "#f2e2b8"
SAND_DARK = "#c8a66c"
SAND_RED = "#d8a878"
ADOBE = "#c89a6a"
ADOBE_DARK = "#a87a50"
BORAX = "#f2f0e6"
ROCK = "#a8784e"
ROCK_DARK = "#7e5838"
BLEACHED = "#b8a080"          # old wood gone grey in the sun
PALM = "#4e7a3a"

ROUTE = fillet([(-372.0, -150.0), (-210.0, -150.0), (0.0, 0.0), (210.0, 150.0), (372.0, 150.0)],
               radius=80.0, step=5.0)
PROFILE = [(0.0, 0.0), (0.12, 0.0), (0.27, 5.0), (0.4, 2.0), (0.5, 0.0), (0.6, 2.0), (0.73, 6.0),
           (0.88, 0.0), (1.0, 0.0)]
LANE_A, YS = graded(ROUTE, PROFILE)
LANE_B = mirror(LANE_A)
LANES = (LANE_A, LANE_B)
LANE_OF = {"a": LANE_A, "b": LANE_B}

# the barchans: centre, height, size (the wind blows toward +x)
DUNES = ((-200.0, -96.0, 8.0, 62.0), (-128.0, 62.0, 9.0, 64.0), (-112.0, -42.0, 8.0, 58.0),
         (-230.0, 40.0, 7.0, 52.0), (60.0, -200.0, 10.0, 70.0), (-58.0, -210.0, 9.0, 64.0),
         (-150.0, -216.0, 10.0, 66.0), (150.0, 58.0, 11.0, 76.0), (200.0, -40.0, 16.0, 118.0),
         (140.0, -116.0, 9.0, 64.0), (124.0, 200.0, 9.0, 64.0), (-142.0, 206.0, 9.0, 62.0),
         (-46.0, 208.0, 8.0, 58.0), (226.0, 180.0, 8.0, 54.0), (250.0, -200.0, 9.0, 60.0),
         (-20.0, -172.0, 6.0, 44.0))
# (the backs climb no faster than a body can walk -- 1.5 h / r under 0.2 -- the
# slip faces are the cliffs)
WIND = [1.0, 0.15]

BORAX_WORKS = rect(-392.0, -250.0, -250.0, -178.0)
REFINERY = rect(-392.0, -352.0, -246.0, -210.0)
OASIS = rect(-392.0, -250.0, 178.0, 250.0)
SERAI = rect(-392.0, -342.0, 190.0, 246.0)
POOL = rect(-326.0, -290.0, 204.0, 232.0)
POOL_RIM = rect(-327.2, -288.8, 202.8, 233.2)
ENGINE_HOLLOW = rect(-190.0, -140.0, 0.0, 20.0)
STREET = (-8.0, 8.0)              # Dry Wells' Main Street, north from the diamond
SALOON = rect(-40.0, -10.0, -110.0, -80.0)
HOTEL = rect(-40.0, -10.0, -150.0, -120.0)
BANK = rect(10.0, 30.0, -110.0, -90.0)
CHURCH = rect(10.0, 40.0, -150.0, -120.0)
STORE = rect(-40.0, -20.0, -70.0, -50.0)
SALT = rect(-40.0, 40.0, 70.0, 130.0)
FOSSIL = (92.0, 162.0)
SHIP = (176.0, -6.0)
SHIP_Y = 11.0                     # she lies on the Great Dune's back
MISSION = rect(326.0, 386.0, -50.0, 50.0)

DEPOTS = (("a", 1 / 3.0, 1.0, "BORATE SIDING", 1, "#7a3a2a"),
          ("a", 2 / 3.0, -1.0, "SAND HILLS TANK", 2, "#2f4a6a"),
          ("b", 1 / 3.0, -1.0, "BORATE SIDING SOUTH", 1, "#2f4a6a"),
          ("b", 2 / 3.0, 1.0, "SAND HILLS TANK NORTH", 2, "#7a3a2a"))
COAL = ((-336.0, -100.0), (-336.0, 100.0), (-60.0, 0.0), (120.0, 0.0))

KEEP: list = []
BASES: dict = {}


def build(b: ArenaArea) -> None:
    rng = random.Random(0x51DE)
    del KEEP[:]
    BASES.clear()
    b.extra.update({"accent": "#ffb84a", "twist": "drifts", "drift_style": "sand",
                    "lanes": {"a": world_lane(b, LANE_A, YS), "b": world_lane(b, LANE_B, YS)},
                    "names": {"a": "the Borax line", "b": "the Oasis line"}})
    land = _land()
    ground(b, SAND, soil="#b8945e", material="", holes=[POOL_RIM])
    land.build(b, SAND, material="")
    _edge(b, rng)
    for path in LANES:
        lay_graded(b, path, YS, ballast="#a89070")
    common.start_yards(b, ("BORAX WORKS", "OASIS HALT"), ("#7a3a2a", "#2f4a6a"), KEEP,
                       post=BLEACHED)
    _borax(b, rng)
    _oasis(b, rng)
    _lost_engine(b, rng)
    _ghost_town(b, rng)
    _salt_pan(b, rng)
    _fossil(b, rng)
    _schooner(b, rng)
    _pumping(b, rng)
    _mission(b, rng)
    common.termini(b, ("FURNACE SPRINGS", "BORAX JUNCTION"), ("#2f4a6a", "#7a3a2a"), KEEP,
                   house=ADOBE, trim=ADOBE_DARK, house_fn=_adobe_station)
    common.place_depots(b, DEPOTS, LANE_OF, BASES, KEEP)
    common.place_levers(b, land, LANE_OF, KEEP)
    common.place_coal(b, COAL, BASES, rng, KEEP)
    _scatter(b, rng, land)
    telegraph(b, LANE_A, -1.0, ground=land.height, skip=_blocked)
    telegraph(b, LANE_B, 1.0, ground=land.height, skip=_blocked)
    _rigs(b)
    for x, z, name in ((-345, -150, "the borax works yard"), (-345, 150, "the oasis halt"),
                       (-372, -228, "the refinery"), (-305, -230, "the evaporating vats"),
                       (-300, -194, "the cottonball heaps"), (-240, -196, "the twenty-mule team"),
                       (-308, 218, "the spring"), (-367, 218, "the caravanserai"),
                       (-280, 196, "the camel lines"), (-165, 10, "the lost engine"),
                       (0, 0, "the diamond"), (0, -100, "Dry Wells"), (-25, -95, "the Last Drop saloon"),
                       (20, -100, "the bank"), (25, -135, "the buried church"), (-25, -135, "the hotel"),
                       (-30, -60, "the store"), (0, 100, "the salt pan"), (FOSSIL[0], FOSSIL[1], "the Boneyard"),
                       (SHIP[0], SHIP[1], "the stranded schooner"), (214, -46, "the Great Dune"),
                       (150, 58, "the dune sea"), (230, 92, "the pumping station"),
                       (356, 0, "Furnace Springs mission"), (345, 150, "Furnace Springs station"),
                       (345, -150, "Borax Junction"), (-128, 62, "the west dunes"), (-112, -42, "Sidewinder Hill")):
        b.landmark(float(x), float(z), name)
    b.camera(-150.0, 44.0, -20.0, 0.0, 4.0, -60.0)
    b.camera(100.0, 50.0, 80.0, 176.0, 8.0, -6.0)
    b.camera(-300.0, 40.0, 60.0, -330.0, 4.0, 218.0)


def _keep(area) -> None:
    KEEP.append(area)


def _blocked(x: float, z: float) -> bool:
    return any(k[0] - 2 < x < k[1] + 2 and k[2] - 2 < z < k[3] + 2 for k in KEEP)


def _smooth(k: float) -> float:
    k = max(0.0, min(1.0, k))
    return k * k * (3.0 - 2.0 * k)


def barchan(x: float, z: float, cx: float, cz: float, h: float, r: float) -> float:
    """A crescent dune's height at (x, z): the long gentle back to the west,
    the steep slip face to the east, the horns trailing downwind."""
    v = (z - cz) / r
    if abs(v) >= 1.0:
        return 0.0
    u = (x - cx) / r - 0.55 * v * v
    lat = (1.0 - v * v) ** 2
    if u <= -1.0 or u >= 0.3:
        return 0.0
    prof = _smooth(1.0 + u) if u <= 0.0 else 1.0 - u / 0.3
    return h * prof * lat


def _banks(x: float, z: float) -> float:
    """Sand banked up the windward walls of Dry Wells: up the saloon and
    the hotel to their upper floors, up the church's north side to its
    eaves -- the town is being buried from the west."""
    out = 0.0
    if -112.0 <= x <= -40.0 and -156.0 <= z <= -74.0:
        k = _smooth((x + 112.0) / 72.0)
        ends = _smooth(min(z + 156.0, -74.0 - z) / 16.0)
        out = max(out, 9.2 * k * ends)
    if 10.0 <= x <= 40.0 and -218.0 <= z <= -150.0:
        k = _smooth((z + 218.0) / 68.0)
        ends = _smooth(min(x - 10.0, 40.0 - x) / 8.0) * 0.4 + 0.6
        out = max(out, 9.6 * k * ends)
    return out


# ==================================================================== land
def _land() -> Land:
    hx, hz = HALF
    land = Land(rect(-hx, hx, -hz, hz), cell=10.0, step=1.0)

    def shape(x: float, z: float) -> float:
        ripple = 1.3 * math.sin(x / 33.0 + z / 71.0) + 0.9 * math.cos(x / 19.0 - z / 41.0 + 1.2)
        dunes = max([barchan(x, z, cx, cz, h, r) for cx, cz, h, r in DUNES] + [0.0])
        return max(0.0, 2.0 + ripple + dunes, _banks(x, z))

    land.add(shape)
    land.cut(POOL_RIM)
    flats = [(rect(-400.0, -244.0, -250.0, -120.0), 0.0, 12.0),     # borax works and yard
             (rect(-400.0, -244.0, 120.0, 250.0), 0.0, 12.0),       # the oasis and its yard
             (ENGINE_HOLLOW, 0.0, 0.0),                             # the lost engine's hollow
             (rect(-272.0, -136.0, -212.0, -188.0), 0.0, 12.0),     # the mule team's road
             (rect(-30.0, 30.0, -36.0, 36.0), 0.0, 18.0),           # round the diamond
             (rect(STREET[0] - 2.0, STREET[1] + 2.0, -160.0, -36.0), 0.0, 4.0),
             (SALOON, 0.0, 0.0), (HOTEL, 0.0, 0.0), (BANK, 0.0, 0.0), (CHURCH, 0.0, 0.0),
             (STORE, 0.0, 0.0),
             (SALT, 0.6, 10.0),
             (rect(FOSSIL[0] - 24.0, FOSSIL[0] + 24.0, FOSSIL[1] - 18.0, FOSSIL[1] + 18.0), 2.0, 10.0),
             (rect(SHIP[0] - 40.0, SHIP[0] + 30.0, SHIP[1] - 10.0, SHIP[1] + 10.0), SHIP_Y, 26.0),
             (rect(210.0, 250.0, 76.0, 110.0), 0.0, 10.0),          # the pumping station
             (rect(250.0, 400.0, -250.0, 250.0), 0.0, 16.0)]        # the town at the east end
    for area, y, blend in flats:
        land.flatten(area, y, blend)
    common.plan_depots(land, DEPOTS, LANE_OF, YS, BASES)
    common.plan_coal(land, COAL, BASES)
    for path in LANES:
        land.pin_path(path, YS, half=7.5, blend=10.0)

    def paint(x: float, z: float, h: float):
        if SALT[0] <= x <= SALT[1] and SALT[2] <= z <= SALT[3]:
            return SAND_PALE
        if h >= 14.0:
            return SAND_PALE
        if h >= 9.0:
            return SAND_LIGHT
        if h >= 5.0:
            return None
        if h >= 2.5:
            return SAND_RED if math.sin(x / 23.0 + z / 31.0) > 0.55 else None
        return SAND_DARK

    land.colour(paint)
    return land


# ==================================================================== edge
def _edge(b: ArenaArea, rng: random.Random) -> None:
    """Dune crests and red rock round the edge, a mesa country beyond."""
    hx, hz, m = b.half_x, b.half_z, b.margin
    room_walls(b, rect(-hx - m, hx + m, -hz - m, hz + m), m, 0.0, 30.0, ROCK)
    for side in (-1, 1):
        for i in range(28):
            x = -hx + (i + 0.5) * (2 * hx) / 28.0
            top = rng.uniform(4.0, 14.0)
            b.box([x, 30.0 + top / 2.0, side * (hz + m / 2.0)], [2 * hx / 28.0 - 1.0, top, m + 1.0 + (i % 3) * 0.13],
                  rng.choice([ROCK, ROCK_DARK, SAND_DARK]), collide=False)
    backdrop(b, "mesas", 0.0, rng, ["#b8865a", "#a8784e", "#c8946a"], depth=160.0)


# ============================================================ borax works
def _borax(b: ArenaArea, rng: random.Random) -> None:
    """The borax works at the west end: the refinery with its boiler house
    and stack, the evaporating vats (white crystal on their floors), the
    cottonball heaps, and the twenty-mule team waiting at the dock with its
    two great wagons and the water tank behind."""
    x0, x1, z0, z1 = REFINERY
    storeyed(b, REFINERY, [10.0, 8.0], "#9a5a3a", roof="#4a3a32",
             doors={"z+": [(-380.0, -372.0, 8.0)], "x+": [(-232.0, -224.0, 8.0)]},
             windows=[{"z+": [(-366.0, -358.0, 4.0, 8.0)]},
                      {"z+": [(-388.0, -380.0, 13.0, 16.0), (-366.0, -358.0, 13.0, 16.0)],
                       "x+": [(-242.0, -234.0, 13.0, 16.0), (-222.0, -214.0, 13.0, 16.0)]}],
             wells=[rect(x0 + 2.0, x0 + 8.0, z0 + 2.0, z0 + 14.0)])
    flight(b, "z", z0 + 16.0, z0 + 2.0, x0 + 2.0, x0 + 8.0, 0.4, 10.0, WOOD, fill=0.0)
    threshold(b, REFINERY, "z+", (-380.0, -372.0))
    threshold(b, REFINERY, "x+", (-232.0, -224.0))
    gable(b, REFINERY, 19.2, "#4a3a32", "x", 3, 1.2, 0.8)
    wall_sign(b, (x0 + x1) / 2.0, 15.0, z1 + 0.36, 26.0, 2.4,
              sign_decal("PACIFIC BORAX CO.", "#4a3a32", BORAX, 11.0), "z+", "#4a3a32")
    b.mark("perch", x0 + 14.0, 10.4, z0 + 8.0)
    # the boiler house and its stack
    boiler = rect(-352.0, -334.0, -246.0, -230.0)
    building(b, boiler, 0.0, 10.0, "#8a5a3a", roof_colour="#3a3a3e", doors={"z+": [(-346.0, -340.0, 7.0)]})
    threshold(b, boiler, "z+", (-346.0, -340.0))
    b.cyl([-343.0, 24.0, -240.0], [3.4, 26.0, 3.4], "#6a4a3a")
    b.cyl([-343.0, 37.4, -240.0], [4.0, 0.8, 4.0], "#3a3a3e", material="metal")
    _keep(rect(x0 - 2.0, -332.0, z0 - 2.0, z1 + 2.0))
    # the vats: low walls round crystal floors, walkways between
    for row in range(3):
        for k in range(3):
            vx0, vz0 = -326.0 + k * 18.0, -246.0 + row * 12.0
            vat = rect(vx0, vx0 + 14.0, vz0, vz0 + 9.0)
            room_walls(b, vat, 0.8, 0.0, 2.0, "#8a6a4a")
            slab(b, rect(vx0 + 0.8, vx0 + 13.2, vz0 + 0.8, vz0 + 8.2), 0.4, 0.4, BORAX, studs=True)
    _keep(rect(-328.0, -270.0, -248.0, -208.0))
    # the cottonball heaps
    for x, z, s in ((-302.0, -194.0, 1.0), (-284.0, -200.0, 0.8), (-320.0, -190.0, 0.7)):
        b.box([x, 1.6 * s, z], [10.0 * s, 3.2 * s, 8.0 * s], BORAX, studs=True)
        b.sphere([x, 3.4 * s, z], [8.0 * s, 4.0 * s, 6.4 * s], BORAX, collide=False)
        _keep(rect(x - 6.0 * s, x + 6.0 * s, z - 5.0 * s, z + 5.0 * s))
    # the loading dock and the twenty-mule team
    slab(b, rect(-268.0, -256.0, -214.0, -186.0), 1.6, 1.6, WOOD_LIGHT, studs=True)
    for k, (wx, colour) in enumerate(((-238.0, "#c8b090"), (-216.0, "#c8b090"), (-196.0, "#5a4a3a"))):
        _mule_wagon(b, wx, -200.0, colour, tank=k == 2)
    for k in range(10):
        for side in (-1.4, 1.4):
            _mule(b, -182.0 + k * 4.2, -200.0 + side, rng)
    b.box([-140.0, 1.2, -200.0], [1.0, 2.4, 3.0], WOOD_DARK)
    wall_sign(b, -262.0, 4.0, -185.5, 10.0, 1.6, sign_decal("20 MULE TEAM", WOOD_DARK, BORAX, 6.0), "z+",
              WOOD_DARK)
    _keep(rect(-270.0, -136.0, -216.0, -184.0))


def _mule_wagon(b: ArenaArea, x: float, z: float, colour: str, tank: bool = False) -> None:
    """One of the great borax wagons: a deep box on wheels taller than a
    man (the rear ones bigger), or the water tank that follows them."""
    if tank:
        b.cyl([x, 4.2, z], [5.0, 12.0, 5.0], "#5a5a5e", r=[0.0, 0.0, math.pi / 2.0], material="metal")
    else:
        b.box([x, 4.4, z], [16.0, 4.4, 6.0], colour)
        b.box([x, 6.8, z], [16.4, 0.4, 6.4], WOOD_DARK)
        b.box([x, 7.4, z], [14.0, 1.0, 4.6], BORAX, studs=True)
    for side in (-1, 1):
        for u, r in ((-5.0, 3.0), (5.0, 2.2)):
            b.cyl([x + u, r, z + side * 3.4], [r * 2.0, 0.5, r * 2.0], "#4a3a2a",
                  r=[math.pi / 2.0, 0.0, 0.0], collide=False)
    b.box([x, 1.8, z], [15.0, 1.0, 4.0], WOOD_DARK)


def _mule(b: ArenaArea, x: float, z: float, rng: random.Random) -> None:
    coat = rng.choice(["#6a5a4a", "#7a6a58", "#5a4a3a"])
    b.box([x, 2.4, z], [3.0, 1.6, 1.2], coat)
    for dx in (-1.1, 1.1):
        b.box([x + dx, 0.8, z], [0.3, 1.6, 0.8], coat)
    b.box([x + 1.9, 3.2, z], [1.2, 1.0, 0.8], coat, collide=False)
    b.box([x + 1.9, 4.0, z], [0.2, 0.8, 0.5], coat, collide=False)


# ================================================================== oasis
def _oasis(b: ArenaArea, rng: random.Random) -> None:
    """The oasis halt: the spring in its stone rim under the palms, the
    caravanserai's walled court with rooms round it (its roof walk a
    perch), the well and its windlass, and the camels -- the Army's, by
    the sign."""
    x0, x1, z0, z1 = POOL
    slab(b, POOL, -1.6, 2.4, "#7a6a4a", studs=True)
    b.water((x0 + x1) / 2.0, (z0 + z1) / 2.0, x1 - x0, z1 - z0, -0.3, "#3a8a9a")
    room_walls(b, POOL_RIM, 1.2, -4.0, 0.4, "#b8a070")
    # rocks and rushes round the spring's edge
    for k, (rx, rz) in enumerate(((x0 - 3.0, z0 + 5.0), (x0 + 12.0, z0 - 3.0), (x1 + 3.0, z0 + 9.0),
                                   (x1 - 6.0, z1 + 3.0), (x0 + 4.0, z1 + 3.0), (x1 + 3.0, z1 - 4.0))):
        outcrop(b, rx, rz, 3.0 + (k % 3), 1.2 + (k % 2) * 0.8, 2.6 + (k % 2), colour="#a89070")
    for k, (rx, rz) in enumerate(((x0 + 1.4, z0 + 1.4), (x1 - 1.4, z0 + 1.6), (x0 + 1.6, z1 - 1.4),
                                   (x1 - 1.6, z1 - 1.8), ((x0 + x1) / 2.0, z0 + 1.4))):
        for j in range(3):
            b.cone([rx + (j - 1) * 0.6, -1.6 + 1.6, rz + (j % 2) * 0.5], [0.7, 3.2 + j * 0.4, 0.7],
                   "#5a7a3a" if j % 2 else "#6a8a42")
    for k, (px, pz) in enumerate(((x0 - 6.0, z0 - 4.0), (x1 + 6.0, z0 - 2.0), (x0 - 8.0, z1 + 4.0),
                                   (x1 + 5.0, z1 + 6.0), ((x0 + x1) / 2.0, z1 + 9.0), (x0 - 16.0, (z0 + z1) / 2.0))):
        _palm(b, px, pz, 0.0, 14.0 + (k % 3) * 3.0, rng)
    _keep(rect(x0 - 18.0, x1 + 8.0, z0 - 6.0, z1 + 12.0))
    # the caravanserai
    sx0, sx1, sz0, sz1 = SERAI
    room_walls(b, SERAI, 2.0, 0.0, 9.0, ADOBE, doors={"x+": [(212.0, 222.0, 7.0)]})
    for x in range(int(sx0) + 2, int(sx1) - 1, 12):
        b.box([x + 6.0, 9.4, sz0 + 1.0], [12.4, 0.8, 2.0], ADOBE_DARK)
        b.box([x + 6.0, 9.4, sz1 - 1.0], [12.4, 0.8, 2.0], ADOBE_DARK)
    # rooms along the north and south walls, a roof walk over them
    for zz0, zz1 in ((sz0 + 2.0, sz0 + 12.0), (sz1 - 12.0, sz1 - 2.0)):
        room = rect(sx0 + 2.0, sx1 - 14.0, zz0, zz1)
        facing = "z+" if zz0 < (sz0 + sz1) / 2.0 else "z-"
        building(b, room, 0.0, 6.0, ADOBE, roof_colour=ADOBE_DARK,
                 doors={facing: [(sx0 + 8.0, sx0 + 12.0, 5.0), (sx0 + 22.0, sx0 + 26.0, 5.0)]},
                 lights=WARM)
        threshold(b, room, facing, (sx0 + 8.0, sx0 + 12.0))
        threshold(b, room, facing, (sx0 + 22.0, sx0 + 26.0))
    flight(b, "x", sx1 - 2.0 - 12.0 + 12.0, sx1 - 14.0, sz0 + 3.0, sz0 + 8.0, 0.0, 7.2, ADOBE_DARK, fill=-0.3)
    b.mark("perch", sx0 + 20.0, 7.2, sz0 + 7.0)
    # the well and its windlass in the court
    cx, cz = (sx0 + sx1) / 2.0 - 6.0, (sz0 + sz1) / 2.0
    b.cyl([cx, 1.2, cz], [5.0, 2.4, 5.0], "#a89070")
    b.cyl([cx, 2.3, cz], [3.6, 0.3, 3.6], "#2a3a42", collide=False)
    for dz in (-2.6, 2.6):
        b.box([cx, 3.6, cz + dz], [0.4, 4.0, 0.4], WOOD_DARK)
    b.cyl([cx, 5.2, cz], [0.6, 5.6, 0.6], WOOD, r=[math.pi / 2.0, 0.0, 0.0], collide=False)
    _keep(rect(sx0 - 2.0, sx1 + 2.0, sz0 - 2.0, sz1 + 2.0))
    # the camels, kneeling and standing, and the Army's sign
    for k, (x, z, kneel) in enumerate(((-284.0, 194.0, False), (-272.0, 198.0, True), (-262.0, 192.0, False),
                                       (-274.0, 210.0, True))):
        _camel(b, x, z, kneel, rng)
        _keep(rect(x - 4.0, x + 4.0, z - 3.0, z + 3.0))
    b.cyl([-292.0, 2.0, 186.0], [0.4, 4.0, 0.4], WOOD_DARK)
    wall_sign(b, -292.0, 4.8, 186.0, 7.0, 1.6, sign_decal("U.S. CAMEL CORPS", BLEACHED, "#3a2414", 5.0), "z-",
              BLEACHED)
    # tents of the drivers
    for k in range(3):
        tx, tz = -300.0 + k * 14.0, 240.0
        pup_tent(b, tx, tz, "x", ("#e8dcc0", "#d8c0a0", "#e0d0b0")[k], length=8.0)
        _keep(rect(tx - 5.0, tx + 5.0, tz - 4.0, tz + 4.0))


def _palm(b: ArenaArea, x: float, z: float, base: float, h: float, rng: random.Random) -> None:
    """A date palm: a ringed trunk leaning a little, the fronds drooping
    from its crown, a cluster of dates."""
    lean = rng.uniform(-1.4, 1.4)
    for k in range(int(h // 2)):
        f = k * 2.0 / h
        b.cyl([x + lean * f, base + 1.0 + k * 2.0, z], [1.2 - f * 0.3, 2.0, 1.2 - f * 0.3],
              "#8a6a48" if k % 2 else "#7a5a3a", collide=k == 0)
    top = [x + lean, base + h, z]
    for k in range(7):
        a = k * math.tau / 7.0 + rng.uniform(0, 0.3)
        b.box([top[0] + math.cos(a) * 3.0, top[1] - 0.6, top[2] + math.sin(a) * 3.0], [6.0, 0.15, 1.4],
              PALM if k % 2 else "#5e8a42", collide=False, r=[0.0, -a, -0.35])
    b.sphere([top[0], top[1] - 0.4, top[2]], [1.6, 1.2, 1.6], "#6a7a3a", collide=False)
    b.sphere([top[0] + 0.6, top[1] - 1.4, top[2]], [0.9, 1.0, 0.9], "#a85a2a", collide=False)


def _camel(b: ArenaArea, x: float, z: float, kneel: bool, rng: random.Random) -> None:
    hide = rng.choice(["#c8a070", "#b8905e"])
    y = 1.4 if kneel else 4.0
    b.box([x, y, z], [5.0, 2.2, 2.2], hide)
    b.sphere([x, y + 1.6, z], [2.4, 1.8, 2.0], hide, collide=False)
    if not kneel:
        for dx in (-1.8, 1.8):
            for dz in (-0.7, 0.7):
                b.box([x + dx, 1.4, z + dz], [0.5, 2.8, 0.5], hide)
    b.box([x + 3.0, y + 1.9, z], [0.9, 3.0, 0.9], hide, collide=False)
    b.box([x + 3.6, y + 3.2, z], [1.8, 0.9, 0.9], hide, collide=False)
    b.box([x - 0.4, y + 2.7, z], [1.6, 0.3, 2.4], "#a83a2a", collide=False)


# ============================================================ the engine
def _lost_engine(b: ArenaArea, rng: random.Random) -> None:
    """The Sidewinder itself: the engine that went into the storm of '82
    and never came out, found again in a hollow between the dunes, its
    tender behind it, sand to its axles -- and the vultures overhead."""
    x0, x1, z0, z1 = ENGINE_HOLLOW
    stub_track(b, x0 + 2.0, x1 - 2.0, (z0 + z1) / 2.0)
    locomotive(b, -158.0, (z0 + z1) / 2.0, "x", facing=1.0, colour="#5a4a3a", trim="#a8885a",
               name="SIDEWINDER")
    # sand drifted up its wheels and over the cowcatcher
    for k, (x, w, h) in enumerate(((-150.0, 6.0, 1.6), (-162.0, 8.0, 1.1), (-174.0, 7.0, 1.3))):
        b.box([x, h / 2.0, (z0 + z1) / 2.0], [w, h, 6.0], SAND_LIGHT, studs=True)
    b.box([-150.0, 0.2, (z0 + z1) / 2.0 - 4.0], [3.0, 0.4, 0.4], "#e8e0cc", collide=False)
    _keep(rect(x0 - 2.0, x1 + 2.0, z0 - 2.0, z1 + 2.0))


# ============================================================ ghost town
def _ghost_town(b: ArenaArea, rng: random.Random) -> None:
    """Dry Wells, the town the dunes came for: Main Street running north
    from the diamond, the saloon and the hotel on the windward side half
    under a dune -- their upper floors open to the sand -- the bank with
    its vault door hanging open, the church buried to its eaves, the store
    with its porch fallen in."""
    s0, s1 = STREET
    b.box([0.0, 0.03, -98.0], [s1 - s0, 0.06, 116.0], "#c8aa78", collide=False)
    # the saloon: the dune banks against its west wall to the upper floor
    x0, x1, z0, z1 = SALOON
    storeyed(b, SALOON, [8.0, 7.0], BLEACHED, roof="#6a5a48",
             doors={"x+": [(-99.0, -91.0, 7.0)]},
             windows=[{"x+": [(-108.0, -102.0, 3.0, 6.0), (-88.0, -82.0, 3.0, 6.0)]},
                      {"x-": [(-104.0, -86.0, 8.4, 14.0)], "x+": [(-108.0, -102.0, 10.0, 13.0), (-88.0, -82.0, 10.0, 13.0)]}],
             wells=[rect(x0 + 6.0, x0 + 18.0, z0 + 2.0, z0 + 7.0)], glass=False)
    flight(b, "x", x0 + 4.0, x0 + 18.0, z0 + 2.0, z0 + 7.0, 0.4, 8.0, WOOD, fill=0.0)
    threshold(b, SALOON, "x+", (-99.0, -91.0))
    wall_sign(b, x1 + 0.36, 16.0, (z0 + z1) / 2.0, 20.0, 2.6,
              sign_decal("THE LAST DROP", "#6a5a48", "#e8d8b0", 8.0), "x+", "#6a5a48")
    # inside: the bar and its back shelf of bottles, the piano, the tables
    # -- the last customer still at his -- and sand drifted in at the back
    b.box([-30.0, 1.6, -96.0], [3.0, 1.4, 12.0], WOOD_DARK)
    b.box([-36.4, 3.0, -96.0], [1.2, 4.0, 12.0], "#5a3a22")
    for k in range(6):
        b.box([-35.7, 3.6 + (k % 2) * 1.2, -100.0 + k * 1.6], [0.4, 0.9, 0.4],
              ("#3a6a3a", "#6a3a22", "#c8a040")[k % 3], collide=False)
    b.box([-14.0, 1.8, -84.0], [2.0, 3.2, 6.0], "#2a1a12")
    b.box([-14.0, 2.6, -84.0], [2.2, 0.2, 5.6], "#f2ece0", collide=False)
    for k in range(3):
        b.box([-22.0, 1.0, -104.0 + k * 6.0], [3.0, 0.3, 3.0], WOOD)
        b.box([-22.0, 0.5, -104.0 + k * 6.0], [0.5, 1.0, 0.5], WOOD_DARK)
    sx_, sz_ = -22.0, -98.0
    b.box([sx_ + 2.2, 0.8, sz_], [1.4, 1.6, 1.4], WOOD)
    b.box([sx_ + 2.2, 2.6, sz_], [0.9, 2.0, 0.7], "#e8e0cc")
    b.box([sx_ + 2.2, 4.0, sz_], [0.8, 0.8, 0.8], "#ece4d0")
    b.box([sx_ + 2.2, 4.55, sz_], [1.0, 0.3, 1.0], "#5a3a22", collide=False)
    b.box([sx_ + 1.2, 3.2, sz_], [1.2, 0.3, 0.3], "#e8e0cc", collide=False)
    b.box([sx_ + 0.4, 1.3, sz_], [0.3, 0.3, 0.3], "#3a6a3a", collide=False)
    for k, (w, h) in enumerate(((8.0, 4.0), (6.0, 2.4), (4.0, 1.0))):
        b.box([-39.0 + w / 2.0 - 0.4 + 0.4, 0.4 + h / 2.0, -96.0], [w - 0.8 + 0.0, h, 22.0 - k * 4.0], SAND_LIGHT,
              studs=True)
    b.mark("perch", -25.0, 8.4, -88.0)
    # the hotel: three storeys, the dune to its second
    hx0, hx1, hz0, hz1 = HOTEL
    storeyed(b, HOTEL, [8.0, 7.0, 7.0], "#b8a88a", roof="#5a4a3a",
             doors={"x+": [(-139.0, -131.0, 7.0)]},
             windows=[{"x+": [(-148.0, -142.0, 3.0, 6.0), (-128.0, -122.0, 3.0, 6.0)]},
                      {"x-": [(-146.0, -124.0, 8.4, 14.0)], "x+": [(-148.0, -142.0, 10.0, 13.0), (-128.0, -122.0, 10.0, 13.0)]},
                      {"x+": [(-148.0, -142.0, 17.0, 20.0), (-128.0, -122.0, 17.0, 20.0)]}],
             wells=[rect(hx0 + 6.0, hx0 + 18.0, hz0 + 2.0, hz0 + 7.0)], glass=False)
    flight(b, "x", hx0 + 4.0, hx0 + 18.0, hz0 + 2.0, hz0 + 7.0, 0.4, 8.0, WOOD, fill=0.0)
    threshold(b, HOTEL, "x+", (-139.0, -131.0))
    wall_sign(b, hx1 + 0.36, 23.0, (hz0 + hz1) / 2.0, 18.0, 2.4,
              sign_decal("GRAND HOTEL", "#5a4a3a", "#e8d8b0", 8.0), "x+", "#5a4a3a")
    # the bank, its vault door hanging open on the gold
    bx0, bx1, bz0, bz1 = BANK
    building(b, BANK, 0.0, 10.0, "#a89c84", roof_colour="#5a5a5e", doors={"x-": [(-104.0, -96.0, 8.0)]},
             windows={"x-": [(-108.0, -106.0, 3.0, 7.0), (-94.0, -92.0, 3.0, 7.0)]}, glass=False, parapet=1.4)
    threshold(b, BANK, "x-", (-104.0, -96.0))
    b.box([bx1 - 4.0, 3.0, (bz0 + bz1) / 2.0], [4.0, 6.0, 8.0], "#3a3a3e", material="metal")
    b.box([bx1 - 6.05, 3.0, (bz0 + bz1) / 2.0], [0.1, 4.6, 4.0], "#1a1a1a", collide=False)
    b.cyl([bx1 - 8.0, 3.0, (bz0 + bz1) / 2.0 + 3.6], [4.4, 0.6, 4.4], "#5a5a5e",
          r=[0.0, 0.0, math.pi / 2.0], material="metal", collide=False)
    for k in range(3):
        b.box([bx1 - 4.0, 1.0 + k * 0.6, (bz0 + bz1) / 2.0 - 1.0 + (k % 2) * 0.8], [1.6, 0.5, 0.8], rails.GOLD,
              material="metal", collide=False)
    wall_sign(b, bx0 - 0.36, 11.0, (bz0 + bz1) / 2.0, 14.0, 1.8, sign_decal("BANK", "#5a5a5e", "#e8d8b0", 5.0),
              "x-", "#5a5a5e")
    # the church, buried to its eaves on the west: in by the belfry
    cx0, cx1, cz0, cz1 = CHURCH
    building(b, CHURCH, 0.0, 10.0, "#e8dcc8", roof_colour="#6a5a4a", doors={"x-": [(-139.0, -131.0, 8.0)]},
             windows={"z-": [(16.0, 22.0, 3.0, 8.0), (28.0, 34.0, 3.0, 8.0)],
                      "z+": [(16.0, 22.0, 3.0, 8.0), (28.0, 34.0, 3.0, 8.0)]}, glass=False, lights=WARM)
    threshold(b, CHURCH, "x-", (-139.0, -131.0))
    gable(b, CHURCH, 11.2, "#6a5a4a", "x", 4, 1.2, 0.6)
    b.box([cx0 + 4.0, 16.0, -135.0], [6.0, 8.0, 6.0], "#e8dcc8")
    b.cone([cx0 + 4.0, 23.0, -135.0], [7.0, 6.0, 7.0], "#6a5a4a")
    b.cone([cx0 + 4.0, 16.0, -135.0], [2.0, 2.0, 2.0], "#a88a4a", material="metal", collide=False)
    for k in range(4):
        b.box([cx0 + 12.0 + k * 4.0, 1.0, -132.0], [2.6, 0.5, 6.0], BLEACHED)
    # the store, its porch roof collapsed onto the boardwalk
    sx0, sx1, sz0, sz1 = STORE
    building(b, STORE, 0.0, 8.0, "#a88a6a", roof_colour="#5a4a3a", doors={"x+": [(-64.0, -58.0, 6.0)]},
             windows={"x+": [(-68.0, -66.0, 2.6, 5.6), (-56.0, -54.0, 2.6, 5.6)]}, glass=False)
    threshold(b, STORE, "x+", (-64.0, -58.0))
    wall_sign(b, sx1 + 0.36, 9.6, (sz0 + sz1) / 2.0, 14.0, 1.8, sign_decal("MERCANTILE", "#5a4a3a", "#e8d8b0", 6.0),
              "x+", "#5a4a3a")
    b.box([sx1 + 2.0, 0.3, (sz0 + sz1) / 2.0], [4.0, 0.6, 18.0], BLEACHED)
    b.box([sx1 + 2.0, 1.6, (sz0 + sz1) / 2.0 + 2.0], [4.4, 0.3, 14.0], "#6a5a48", collide=False,
          r=[0.0, 0.0, 0.5])
    for area in (SALOON, HOTEL, BANK, CHURCH, STORE):
        _keep(rect(area[0] - 3.0, area[1] + 3.0, area[2] - 3.0, area[3] + 3.0))
    # hitching rails gone grey, a water trough dry as bone
    rails.hitching_post(b, -6.0, -70.0, "z")
    b.box([6.0, 0.8, -76.0], [2.0, 1.6, 6.0], BLEACHED)


# ================================================================ salt pan
def _salt_pan(b: ArenaArea, rng: random.Random) -> None:
    """The salt pan south of the diamond: crusted white, cracked into
    plates, the bones of a land yacht left on it -- and the lake that is
    always just beyond it (a mirage: a rig)."""
    x0, x1, z0, z1 = SALT
    for i in range(8):
        for j in range(6):
            if (i + j) % 3 == 0:
                continue
            px = x0 + 5.0 + i * 10.0 + (j % 2) * 2.0
            pz = z0 + 5.0 + j * 10.0
            h = 0.15 + ((i * 7 + j * 3) % 4) * 0.05
            b.box([px, 0.6 + h / 2.0, pz], [8.4, h, 8.4], "#f8f4ea")
    # the land yacht: a hull on three wheels, its mast down and its sail torn
    yx, yz = 12.0, 108.0
    b.box([yx, 1.6, yz], [10.0, 1.2, 3.0], BLEACHED)
    b.box([yx - 4.0, 1.0, yz], [1.0, 1.0, 8.0], WOOD_DARK)
    for x, z in ((yx - 4.0, yz - 4.0), (yx - 4.0, yz + 4.0), (yx + 4.6, yz)):
        b.cyl([x, 1.0, z], [2.0, 0.4, 2.0], "#4a3a2a", r=[math.pi / 2.0, 0.0, 0.0], collide=False)
    b.box([yx + 6.0, 1.2, yz + 2.0], [12.0, 0.4, 0.4], WOOD_DARK, collide=False, r=[0.0, 0.3, 0.0])
    b.box([yx + 6.0, 0.9, yz + 4.0], [8.0, 0.1, 5.0], "#e8e0d0", collide=False, r=[0.0, 0.3, 0.0])
    _keep(rect(x0, x1, z0, z1))


# ================================================================= fossil
def _fossil(b: ArenaArea, rng: random.Random) -> None:
    """The Boneyard: a sea serpent's skeleton breaking out of a red rock
    ridge, its spine arching over the sand, its skull as big as a wagon."""
    fx, fz = FOSSIL
    base = 2.0
    outcrop(b, fx - 14.0, fz + 4.0, 12.0, 7.0, 10.0, base=base, colour=ROCK)
    outcrop(b, fx + 14.0, fz - 2.0, 10.0, 5.0, 8.0, base=base, colour=ROCK_DARK)
    # the spine: vertebrae on an arch, ribs off them
    for k in range(17):
        f = k / 16.0
        x = fx - 14.0 + f * 28.0
        y = base + 2.0 + math.sin(f * math.pi) * 8.0
        b.box([x, y, fz], [2.4, 2.0 + (k % 2) * 0.1, 1.6 + (k % 2) * 0.14], "#e8e0cc", collide=k in (0, 16))
        if 2 <= k <= 14 and k % 2 == 0:
            for side in (-1, 1):
                b.box([x, y - 2.2, fz + side * 2.0], [0.4, 4.0, 0.4], "#ded4bc", collide=False,
                      r=[side * 0.5, 0.0, 0.0])
    # the skull, jaws open, half out of the rock
    sx = fx + 20.0
    sz = fz + 0.5
    b.box([sx, base + 2.0, sz], [6.0, 3.0, 4.0], "#e8e0cc")
    b.box([sx + 4.0, base + 1.05, sz], [5.0, 1.0, 3.0], "#ded4bc")
    b.box([sx + 3.6, base + 3.4, sz], [5.0, 1.0, 3.2], "#e8e0cc", collide=False, r=[0.0, 0.0, 0.25])
    for side in (-1, 1):
        b.box([sx - 1.0, base + 3.0, sz + side * 2.05], [1.2, 1.2, 0.1], "#1a1a1a", collide=False)
    # the professor's dig: stakes and a string grid, a sieve, his tent
    for k in range(4):
        b.box([fx - 10.0 + k * 7.0, base + 1.0, fz - 9.0], [0.3, 2.0, 0.3], WOOD_DARK)
    b.box([fx - 14.0, base + 1.4, fz - 13.0], [5.0, 2.8, 4.0], "#e8dcc0")
    b.box([fx - 14.0, base + 3.0, fz - 13.0], [5.4, 0.4, 2.4], "#d8c8a8")
    _keep(rect(fx - 28.0, fx + 28.0, fz - 16.0, fz + 14.0))


# =============================================================== schooner
def _schooner(b: ArenaArea, rng: random.Random) -> None:
    """The Desert Queen: a two-masted schooner lying in the dune sea where
    the old inland sea left her, her hull half full of sand, her deck a
    perch, a mast still standing (its rag of a sail is a rig)."""
    sx, sz = SHIP
    base = SHIP_Y
    # the hull in stepped strakes, narrowing to the bow (east) and stern
    for k, (w, y) in enumerate(((10.0, 1.0), (12.0, 2.6), (13.0, 4.2))):
        for u in range(-5, 6):
            length = 5.0
            taper = 1.0 - (abs(u) / 6.5) ** 2
            width = max(2.0, w * taper)
            b.box([sx + u * length, base + y - 0.8 + 0.8, sz], [length + 0.02, 1.6, width],
                  "#6a4a30" if k % 2 else "#5a3e28")
    slab(b, rect(sx - 26.0, sx + 26.0, sz - 5.6, sz + 5.6), base + 5.6, 0.6, WOOD, studs=True)
    b.box([sx - 22.0, base + 7.2, sz], [8.0, 3.0, 8.0], "#5a3e28")
    b.box([sx - 22.0, base + 8.9, sz], [8.6, 0.4, 8.6], WOOD_DARK)
    for x in (sx - 8.0, sx + 10.0):
        b.cyl([x, base + 18.0, sz], [1.0, 24.0, 1.0], "#6a4a30")
        b.box([x, base + 24.0, sz], [0.6, 0.6, 12.0], "#6a4a30", collide=False)
    b.box([sx + 30.0, base + 6.0, sz], [10.0, 0.6, 0.6], "#6a4a30", collide=False, r=[0.0, 0.0, 0.3])
    wall_sign(b, sx + 18.0, base + 3.4, sz + 6.9, 10.0, 1.4, sign_decal("DESERT QUEEN", "#5a3e28", "#e8c870", 6.0),
              "z+", "#5a3e28")
    flight(b, "x", sx - 36.0, sx - 26.0, sz - 2.0, sz + 2.0, base, base + 5.6, BLEACHED, fill=base - 0.3)
    b.mark("perch", sx + 2.0, base + 5.6, sz + 3.0)
    _keep(rect(sx - 38.0, sx + 36.0, sz - 9.0, sz + 9.0))


# =============================================================== pumping
def _pumping(b: ArenaArea, rng: random.Random) -> None:
    """The pumping station on the aquifer: a steam pump house, the tall
    tank for the engines, the windmill that helps when the boiler's down."""
    house = rect(212.0, 230.0, 80.0, 94.0)
    building(b, house, 0.0, 8.0, ADOBE, roof_colour="#4a3a32", doors={"x-": [(84.0, 90.0, 6.0)]})
    threshold(b, house, "x-", (84.0, 90.0))
    b.cyl([226.0, 12.0, 84.0], [1.4, 8.0, 1.4], "#3a3a3e", material="metal")
    rails.water_tower(b, 240.0, 100.0, "#7a5335", height=16.0)
    for dx in (-1.5, 1.5):
        for dz in (-1.5, 1.5):
            b.box([252.0 + dx, 10.0, 84.0 + dz], [0.4, 20.0, 0.4], "#6a6a64", material="metal")
    b.box([252.0, 20.2, 84.0], [3.6, 0.4, 3.6], "#5a5a54", material="metal")
    _keep(rect(208.0, 262.0, 76.0, 112.0))


# ================================================================ mission
def _mission(b: ArenaArea, rng: random.Random) -> None:
    """Furnace Springs: the old mission between the two stations, now the
    railroad's hotel -- adobe arcades round a courtyard, the bell tower
    (a perch), the date palms."""
    x0, x1, z0, z1 = MISSION
    building(b, MISSION, 0.0, 10.0, ADOBE, roof_colour=ADOBE_DARK, t=1.6,
             doors={"x-": [(-6.0, 6.0, 8.0)]},
             windows={"x-": [(-40.0, -30.0, 3.0, 7.0), (-20.0, -12.0, 3.0, 7.0), (12.0, 20.0, 3.0, 7.0),
                             (30.0, 40.0, 3.0, 7.0)]}, lights=WARM, floor_colour="#a8784e",
             roof_holes=[rect(x0 + 14.0, x1 - 14.0, z0 + 14.0, z1 - 14.0)])
    threshold(b, MISSION, "x-", (-6.0, 6.0), t=1.6)
    # the arcade along the front
    slab(b, rect(x0 - 8.0, x0, z0, z1), 0.4, 0.4, "#b88a5a")
    for z in range(int(z0) + 4, int(z1) - 3, 9):
        b.box([x0 - 7.0, 4.0, float(z)], [1.6, 8.0, 1.6], ADOBE)
    slab(b, rect(x0 - 8.6, x0, z0 - 0.6, z1 + 0.6), 9.0, 1.0, ADOBE_DARK)
    # the bell tower over the gate, its stair up the inside of the court
    b.box([x0 - 4.0, 14.5, 0.0], [8.0, 11.0, 8.0], ADOBE)
    b.box([x0 - 4.0, 21.0, 0.0], [9.0, 2.0, 9.0], ADOBE_DARK)
    b.cone([x0 - 4.0, 18.0, 0.0], [2.4, 2.4, 2.4], "#a88a4a", material="metal", collide=False)
    flight(b, "z", z0 + 36.0, z0 + 14.0, x0 + 16.0, x0 + 22.0, 0.4, 11.2, ADOBE_DARK, fill=0.0)
    b.mark("perch", x0 + 6.0, 11.2, z0 + 8.0)
    wall_sign(b, x0 - 8.96, 10.4, 0.0, 22.0, 2.2, sign_decal("FURNACE SPRINGS", ADOBE_DARK, "#f2e2b8", 9.0),
              "x-", ADOBE_DARK)
    for k, (px, pz) in enumerate(((x0 - 18.0, -40.0), (x0 - 18.0, 40.0), (x0 - 24.0, -14.0), (x0 - 24.0, 18.0))):
        _palm(b, px, pz, 0.0, 15.0 + (k % 2) * 3.0, rng)
    _keep(rect(x0 - 26.0, x1 + 2.0, z0 - 2.0, z1 + 2.0))


def _adobe_station(b: ArenaArea, area, side: float, roof: str) -> None:
    lo, hi = min(area[2], area[3]), max(area[2], area[3])
    building(b, area, 0.0, 11.0, ADOBE, roof_colour=ADOBE_DARK, t=1.4,
             doors={"x-": [(lo + 6.0, hi - 6.0, 9.0)]},
             windows={"z-" if side > 0 else "z+": [(330.0, 344.0, 4.0, 8.0), (356.0, 370.0, 4.0, 8.0)]},
             glass=True, lights=WARM)
    threshold(b, area, "x-", (lo + 6.0, hi - 6.0), t=1.4)
    for k in range(5):
        b.box([328.0 + k * 12.0, 12.4, (area[2] + area[3]) / 2.0], [1.4, 1.6, hi - lo + 0.4], ADOBE_DARK)


# ================================================================ scatter
def _scatter(b: ArenaArea, rng: random.Random, land: Land) -> None:
    """Desert clutter: creosote and saltbush, a few cactuses, sun-bleached
    skulls, rocks -- never on a line or anything built."""
    tries = placed = 0
    hx, hz = HALF
    while placed < 120 and tries < 1800:
        tries += 1
        x, z = rng.uniform(-hx + 10.0, hx - 10.0), rng.uniform(-hz + 10.0, hz - 10.0)
        if not clear_of(rect(x - 4.0, x + 4.0, z - 4.0, z + 4.0), LANES, 12.0):
            continue
        if _blocked(x, z) or any(k[0] - 5 < x < k[1] + 5 and k[2] - 5 < z < k[3] + 5 for k in KEEP):
            continue
        base = land.height(x, z)
        if abs(land.height(x + 3.0, z) - base) > 0.6 or abs(land.height(x, z + 3.0) - base) > 0.6:
            continue
        roll = rng.random()
        if roll < 0.45:
            b.sphere([x, base + 0.9, z], [2.6, 1.8, 2.4], rng.choice(["#7a8a4a", "#8a9050", "#6a7a40"]),
                     collide=False)
        elif roll < 0.62:
            if base < 0.1:
                rails.cactus(b, x, z, rng.uniform(0.7, 1.1))
            else:
                b.cyl([x, base + 2.0, z], [1.0, 4.0, 1.0], "#5a7a3a")
        elif roll < 0.85:
            outcrop(b, x, z, rng.uniform(2.0, 4.0), rng.uniform(1.0, 2.0), rng.uniform(2.0, 3.6), base=base,
                    colour=rng.choice([ROCK, ROCK_DARK, SAND_RED]))
        else:
            b.box([x, base + 0.5, z], [1.6, 1.0, 2.0], "#ece4d0")
            for side in (-1, 1):
                b.box([x + side * 1.1, base + 1.2, z + 0.2], [0.8, 0.3, 0.3], "#e0d8c4", collide=False,
                      r=[0.0, 0.0, side * 0.5])
        KEEP.append(rect(x - 3.0, x + 3.0, z - 3.0, z + 3.0))
        placed += 1


# =================================================================== rigs
def _rigs(b: ArenaArea) -> None:
    b.rig("rr_weather", 0.0, 0.0, 0.0, weather="dust", wind=WIND)
    b.rig("rr_haboob", 620.0, 0.0, 340.0, q=[-200.0, 0.0, 560.0], h=120.0, w=900.0, seed=0.4)
    for k, (a, c) in enumerate((((-120.0, 8.0, -12.0), (-96.0, 6.0, -26.0)), ((40.0, 3.0, 150.0), (70.0, 3.0, 140.0)),
                                ((150.0, 6.0, 100.0), (176.0, 4.0, 114.0)))):
        b.rig("rr_sidewinder", a[0], a[1], a[2], q=list(c), seed=k * 2.3)
    b.rig("rr_vultures", -158.0, 46.0, 10.0, r=26.0)
    b.rig("rr_vultures", FOSSIL[0], 52.0, FOSSIL[1], r=22.0, n=2)
    for k, (a, c) in enumerate((((-260.0, 2.0, -60.0), (-140.0, 4.0, -20.0)), ((-60.0, 1.0, 30.0), (60.0, 1.0, 40.0)),
                                ((40.0, 2.0, -40.0), (180.0, 6.0, -30.0)), ((220.0, 1.0, 120.0), (320.0, 0.0, 110.0)))):
        b.rig("rr_tumbleweed", a[0], a[1], a[2], q=list(c), speed=11.0 + k, seed=k * 1.7)
    b.rig("rr_smoke", -343.0, 38.0, -240.0, wind=WIND, rate=0.16, h=30.0, colour="#8a8078")
    b.rig("rr_mirage", 0.0, 0.6, 100.0, w=70.0, d=50.0)
    b.rig("rr_flag", SHIP[0] - 8.0, 3.0 + 30.0, SHIP[1], w=4.0, h=2.6, yaw=math.atan2(-WIND[0], -WIND[1]),
          colours=["#d8cfc0", "#b8ac98"])
    b.rig("rr_windpump", 252.0, 16.0 + 4.4, 84.0, yaw=math.atan2(-WIND[0], -WIND[1]), r=4.0)
