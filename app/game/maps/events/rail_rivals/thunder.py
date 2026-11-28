"""Thunder Junction -- a prairie division point with a storm coming in,
where both race lines cross the transcontinental main line.

Layout (north is -z; the race tracks run west to east, the main line north
to south through the middle)::

    z -250 ===== THE BREAKS ======[ NORTH PORTAL ]====== THE BREAKS ==========
           ENGINE HOUSE  coaling    DEADMAN'S CUT       section house   livery
           turntable     tower      (road bridge)        water tank     barn
           (lane a start)--\\        DEPOT + ORDER BOARD |          /--- FREIGHT
    z    0 SOD HOUSE  windpump \\=== THE STAR DIAMOND ===   ICE HOUSE  FRONT ST
           wheat shocks        //   TJ TOWER + PHONE    |  lumber   \\--- STATION
           (lane b start)--/        BUFFALO CREEK COULEE (the Big Fill)
           GRAIN ELEVATORS          hobo jungle under the culvert   water tower
    z +250 ===== THE BREAKS ======[ SOUTH PORTAL ]====== THE BREAKS ==========

Both companies start in the yards at the west end, climb over the west
swell and come down into the Bottoms, where their lines cross each other
and the main line at once: the Star Diamond.  Then over the east swell,
past the ice house, to the town and its two stations.

The twist (``sweep``, style ``freight``): every minute or so a through
freight comes down the main line -- out of the north portal or the south --
and while it does both crossings are shut, the gates down and the bells
going.  A cart short of its crossing waits at the stop board; a cart on the
crossing goes over if its company pushes it and is rolled back off it if
not.  Anybody on the main line when it comes is under it.  Hold E at a call
box -- the telegraph in the depot's bay, the telephone by the tower -- and
the next freight comes now: on their cart, if you time it.

The main line runs in Deadman's Cut through the breaks to the north (the
county road crosses it on a bridge) and over Buffalo Creek on the Big Fill
to the south, with a culvert under it -- the two ways across the main line
with no train to worry about.
"""
from __future__ import annotations

import math
import random

from ...lastlight.kit import lamp_post
from ..kit import (WARM, WOOD, WOOD_DARK, WOOD_LIGHT, ArenaArea, backdrop, building, carve,
                   flight, gable, ground, lantern, plate, rect, room_walls, sign_decal, slab,
                   threshold, wall, wall_sign)
from . import rails
from .land import Land, graded, height_at, lay_graded, world_lane
from .rails import (beside, boxcar, buffer_stop, caboose, clear_of, coal_heap, crate_stack,
                    depot, fillet, handcar, lay_track, lever, mirror, sleeper_pile, stair,
                    storeyed, telegraph)
from .scenery import locomotive, outcrop, stub_track

HALF = (400.0, 250.0)
SKY = {"top": "#232a34", "horizon": "#b9b48e", "sun": [-0.7, 0.13, 0.35],
       "clouds": 0.95, "tint": "#c4ccc0"}
AMBIENT = "#7a8478"
GROUND = "#7f9150"
FOG = 820.0

GRASS = "#7f9150"
GRASS_DRY = "#a39c5e"
GRASS_DEEP = "#647a3e"
CLAY = "#8a6a4a"
CLAY_DARK = "#6e5038"
CLAY_PALE = "#a8865c"
EARTH = "#6a5640"
STONE = "#a89c84"
STONE_DARK = "#7a7062"
DEPOT_YELLOW = "#d8b860"
DEPOT_TRIM = "#6a3e24"
BRICK = "#8a3a2a"
ELEVATOR = "#8a3428"
ELEVATOR_DARK = "#6a2a22"
IRONWORK = "#3a3c40"
WHITE = "#e8e2d4"

ROUTE = fillet([(-372.0, -150.0), (-210.0, -150.0), (0.0, 0.0), (210.0, 150.0), (372.0, 150.0)],
               radius=80.0, step=5.0)
PROFILE = [(0.0, 0.0), (0.13, 0.0), (0.3, 6.0), (0.43, 0.0), (0.57, 0.0), (0.72, 6.0),
           (0.87, 0.0), (1.0, 0.0)]
LANE_A, YS = graded(ROUTE, PROFILE)
LANE_B = mirror(LANE_A)
LANES = (LANE_A, LANE_B)

MAIN_X = 0.0
MAIN_END = 440.0                  # the main line runs on out of sight past the portals
MAIN = [(MAIN_X, -MAIN_END), (MAIN_X, MAIN_END)]
PORTAL_W = 7.5                    # half the portals' width
PORTAL_H = 15.0
SPEED, LENGTH, HALF_W = 40.0, 230.0, 4.0
WIND = [0.8, 0.35]                # the storm's wind, toward +x and +z
WIND_YAW = math.atan2(-0.916, -0.4)   # facing into it

COULEE = rect(-140.0, 140.0, 150.0, 206.0)
FILL = rect(-12.0, 12.0, 150.0, 206.0)
CULVERT = (174.0, 182.0)          # z span of the culvert through the fill
FLOOR_Y = -8.0
TURNTABLE = (-250.0, -205.0)
TT_R = 17.0
TT_PIT = rect(-268.0, -232.0, -223.0, -187.0)
ENGINE_HOUSE = rect(-376.0, -300.0, -240.0, -196.0)
STALLS = (-233.0, -223.0, -213.0, -203.0)
COALING = (-196.0, -218.0)
ELEVATORS = (rect(-362.0, -344.0, 200.0, 218.0), rect(-332.0, -312.0, 198.0, 218.0),
             rect(-300.0, -278.0, 196.0, 220.0))
DEPOT_HOUSE = rect(-36.0, -14.0, -104.0, -64.0)
BAY = rect(-14.0, -10.0, -88.0, -80.0)
PLATFORM_N = rect(-14.0, -6.0, -112.0, -56.0)
TOWER_HOUSE = rect(-36.0, -18.0, 64.0, 92.0)
PHONE = rect(-14.0, -10.0, 80.0, 88.0)
PLATFORM_S = rect(-14.0, -6.0, 56.0, 112.0)
BRIDGE_Z = (-191.0, -179.0)
BRIDGE_Y = 14.0
ICE_HOUSE = rect(76.0, 136.0, -26.0, 26.0)
ICE_Y = 4.0
TOWN = rect(250.0, 392.0, -112.0, 112.0)
STREET = (292.0, 308.0)           # Front Street, north to south
SOD = (-176.0, 0.0)
CELLAR = (-150.0, 26.0)
PUMP = (-196.0, -22.0)
WASH = [(-320.0, -112.0), (-292.0, -60.0), (-280.0, -30.0), (-262.0, 10.0), (-250.0, 40.0),
        (-238.0, 92.0)]                  # the dry wash down the west wedge
KNOLLS = ((-250.0, -78.0, 7.0, 42.0), (232.0, 38.0, 7.5, 42.0), (92.0, -178.0, 6.0, 40.0),
          (-96.0, 128.0, 5.0, 36.0))
SCHOOL = rect(-112.0, -88.0, -172.0, -150.0)
BUNKS_Z = 112.0

DEPOTS = (("a", 1 / 3.0, 1.0, "PRAIRIE SIDING", 1, "#7a3a2a"),
          ("a", 2 / 3.0, -1.0, "EAST SWELL TANK", 2, "#2f4a6a"),
          ("b", 1 / 3.0, -1.0, "PRAIRIE SIDING SOUTH", 1, "#2f4a6a"),
          ("b", 2 / 3.0, 1.0, "EAST SWELL TANK NORTH", 2, "#7a3a2a"))
COAL = ((-336.0, -100.0), (-336.0, 100.0), (-64.0, 0.0), (168.0, 0.0))

KEEP: list = []
BASES: dict = {}


def build(b: ArenaArea) -> None:
    rng = random.Random(0x7A3D)
    del KEEP[:]
    BASES.clear()
    cross = 0.0
    for lane_path in LANES:
        cross = _cross_s(lane_path)
    b.extra.update({
        "accent": "#ffc24a", "twist": "sweep",
        "lanes": {"a": world_lane(b, LANE_A, YS), "b": world_lane(b, LANE_B, YS)},
        "names": {"a": "the Bottoms line", "b": "the Swell line"},
        "sweep": {"style": "freight", "path": [b.at(x, 0.0, z) for x, z in MAIN],
                  "speed": SPEED, "length": LENGTH, "half": HALF_W,
                  "cross": {"a": round(cross, 2), "b": round(cross, 2)},
                  "show": [MAIN_END - b.half_z - 10.0, MAIN_END + b.half_z + 10.0],
                  "gates": _gate_specs(b)},
    })
    land = _land()
    ground(b, GRASS, soil="#5a4632", holes=[COULEE, TT_PIT])
    land.build(b, GRASS)
    _edge(b, rng)
    _tracks(b)
    _coulee(b, rng)
    _yards(b, rng)
    _engine_house(b, rng)
    _turntable(b)
    _coaling(b, rng)
    _elevators(b, rng)
    _homestead(b, rng, land)
    _depot(b, rng)
    _tower(b, rng)
    _crossing(b)
    _cut(b, land)
    _section(b, rng, land)
    _ice_house(b, rng)
    _lumber(b, rng, land)
    _school(b, rng)
    _bunk_cars(b, rng)
    _bottoms(b, rng)
    _haystacks(b, rng, land)
    _town(b, rng)
    _termini(b, rng)
    _depots(b)
    _levers(b, land)
    _coal(b, rng)
    _scatter(b, rng, land)
    telegraph(b, LANE_A, -1.0, ground=land.height, skip=_blocked)
    telegraph(b, LANE_B, 1.0, ground=land.height, skip=_blocked)
    telegraph(b, [(MAIN_X, -236.0), (MAIN_X, 140.0)], 1.0, every=44.0, ground=land.height,
              skip=_blocked)
    _rigs(b)
    for x, z, name in ((-345, -150, "the roundhouse yard"), (-345, 150, "the elevator yard"),
                       (-338, -218, "the engine house"), (TURNTABLE[0], TURNTABLE[1], "the turntable"),
                       (COALING[0], COALING[1], "the coaling tower"),
                       (-322, 208, "the grain elevators"), (-250, 208, "the concrete bins"),
                       (SOD[0], SOD[1], "the sod house"), (PUMP[0], PUMP[1], "the windpump"),
                       (CELLAR[0], CELLAR[1], "the storm cellar"), (-110, 0, "the wheat field"),
                       (0, 0, "the Star Diamond"), (-25, -84, "Thunder Junction depot"),
                       (-12, -84, "the operator's bay"), (-27, 78, "TJ Tower"),
                       (-12, 84, "the tower telephone"), (0, -185, "the county road bridge"),
                       (0, -210, "Deadman's Cut"), (0, -248, "the north portal"),
                       (0, 248, "the south portal"), (0, 178, "the Big Fill"),
                       (-60, 180, "the hobo jungle"), (70, 178, "Buffalo Creek"),
                       (40, -110, "the section house"), (24, -70, "the water tank"),
                       (106, 0, "the ice house"), (141, 0, "the icing dock"),
                       (60, 100, "the lumber yard"), (300, 0, "Front Street"),
                       (270, -60, "the Junction Beanery"), (334, -60, "the Drovers' Hotel"),
                       (334, 70, "the church"), (270, 60, "the land office"),
                       (345, -150, "the freight station"), (345, 150, "the passenger station"),
                       (262, -205, "the livery barn"), (300, 205, "the town water tower"),
                       (-140, -98, "the west swell"), (160, 110, "the east swell")):
        b.landmark(float(x), float(z), name)
    b.camera(-150.0, 40.0, -40.0, 0.0, 0.0, 0.0)
    b.camera(60.0, 45.0, -150.0, 0.0, 6.0, -60.0)
    b.camera(-80.0, 30.0, 150.0, 0.0, -4.0, 178.0)


def _cross_s(path) -> float:
    """How far along the main line a lane crosses it."""
    best, best_d = 0.0, 1e9
    for (x0, z0), (x1, z1) in zip(path, path[1:]):
        if (x0 - MAIN_X) * (x1 - MAIN_X) <= 0 and x1 != x0:
            f = (MAIN_X - x0) / (x1 - x0)
            z = z0 + (z1 - z0) * f
            if abs(z) < best_d:
                best, best_d = z, abs(z)
    return best + MAIN_END


def _keep(area) -> None:
    KEEP.append(area)


def _blocked(x: float, z: float) -> bool:
    if abs(x - MAIN_X) < 12.0 or (COULEE[0] - 4 < x < COULEE[1] + 4 and COULEE[2] - 4 < z < COULEE[3] + 4):
        return True
    return any(k[0] - 2 < x < k[1] + 2 and k[2] - 2 < z < k[3] + 2 for k in KEEP)


def _track_y(d: float) -> float:
    return height_at(LANE_A, YS, d)


def _smooth(k: float) -> float:
    k = max(0.0, min(1.0, k))
    return k * k * (3.0 - 2.0 * k)


# ==================================================================== land
def _depot_spot(path, f: float, side: float):
    total = rails.length(path)
    x, z, yaw = rails.at(path, total * f)
    rx, rz = math.cos(yaw), -math.sin(yaw)
    along_x = abs(math.sin(yaw)) > 0.7
    hx, hz = (16.0, 6.0) if along_x else (6.0, 16.0)
    offset = max(15.0, abs(rx) * hx + abs(rz) * hz + 7.0)
    return x + rx * side * offset, z + rz * side * offset, hx, hz


def _land() -> Land:
    """The prairie: long low swells, two broad rises the lines climb over,
    the breaks rearing up along the north and south edges (banded clay), and
    the Bottoms flat round the diamond.  Everything built stands on its own
    levelled ground."""
    hx, hz = HALF
    land = Land(rect(-hx, hx, -hz, hz), cell=10.0, step=1.0)

    def shape(x: float, z: float) -> float:
        swell = 3.6 * math.sin(x / 61.0 + 0.4) * math.cos(z / 47.0) + \
            2.6 * math.cos(x / 37.0 - 0.9) * math.sin(z / 53.0 + 1.1) + \
            1.2 * math.sin((x + z) / 23.0)
        west = 8.0 * math.exp(-((x + 140.0) / 75.0) ** 2) * math.exp(-(z / 170.0) ** 2)
        east = 8.0 * math.exp(-((x - 160.0) / 75.0) ** 2) * math.exp(-(z / 170.0) ** 2)
        knolls = sum(h * _smooth(1.0 - math.hypot(x - kx, z - kz) / r) for kx, kz, h, r in KNOLLS)
        breaks = 19.0 * _smooth((abs(z) - 150.0) / 85.0)
        return max(0.0, 3.0 + swell + west + east + knolls + breaks)

    land.add(shape)
    # the dry wash: the ground falls away to its gravel bed along the line of it
    land.scale(lambda x, z: 0.08 + 0.92 * _smooth((rails.distance_to(WASH, x, z) - 6.0) / 20.0))
    land.cut(COULEE)
    land.cut(TT_PIT)
    # level ground under the yards, the town, the buildings
    flats = [(rect(-400.0, -296.0, -244.0, -120.0), 0.0, 10.0),    # the roundhouse yard
             (rect(-400.0, -200.0, 120.0, 238.0), 0.0, 10.0),      # the elevator yard
             (rect(-296.0, -170.0, -232.0, -176.0), 0.0, 10.0),    # turntable, coaling
             (rect(-36.0, 36.0, -28.0, 28.0), 0.0, 26.0),          # the Bottoms
             (rect(-44.0, -2.0, -118.0, -50.0), 0.0, 10.0),        # the depot
             (rect(-44.0, -2.0, 50.0, 118.0), 0.0, 10.0),          # the tower
             (rect(240.0, 400.0, -120.0, 120.0), 0.0, 20.0),       # the town
             (rect(296.0, 400.0, -244.0, -120.0), 0.0, 10.0),      # the freight station
             (rect(296.0, 400.0, 120.0, 244.0), 0.0, 10.0),        # the passenger station
             (rect(230.0, 296.0, -232.0, -176.0), 0.0, 10.0),      # the livery barn
             (rect(270.0, 330.0, 176.0, 232.0), 0.0, 10.0),        # the water tower
             (rect(66.0, 160.0, -40.0, 40.0), ICE_Y, 14.0),        # the ice house terrace
             (rect(-206.0, -136.0, -34.0, 40.0), 2.0, 16.0),       # the homestead
             (rect(14.0, 70.0, -130.0, -54.0), 0.0, 12.0),         # section house, tank
             (rect(14.0, 74.0, 70.0, 136.0), 0.0, 12.0),           # the lumber yard
             (rect(SCHOOL[0] - 10.0, SCHOOL[1] + 6.0, SCHOOL[2] - 6.0, SCHOOL[3] + 10.0), 3.0, 12.0),
             (rect(-124.0, -56.0, BUNKS_Z - 8.0, BUNKS_Z + 10.0), 0.0, 10.0),   # the bunk cars
             (rect(14.0, 34.0, -8.0, 8.0), 0.0, 10.0),             # the watchman's shanty
             (rect(-42.0, -24.0, -6.0, 6.0), 0.0, 8.0)]            # the rail pile
    for area, y, blend in flats:
        land.flatten(area, y, blend)
    # the county road's bridge over the cut, on banks raised to carry it
    land.flatten(rect(-60.0, -10.0, -198.0, -172.0), BRIDGE_Y - 0.6, 16.0)
    land.flatten(rect(10.0, 60.0, -198.0, -172.0), BRIDGE_Y - 0.6, 16.0)
    # the depots at their tracks' heights
    for lane, f, side, _name, _stage, _roof in DEPOTS:
        path = LANE_A if lane == "a" else LANE_B
        ox, oz, dhx, dhz = _depot_spot(path, f, side)
        base = round(_track_y(rails.length(path) * f) * 2.0) / 2.0
        land.flatten(rect(ox - dhx - 4.0, ox + dhx + 4.0, oz - dhz - 1.0, oz + dhz + 1.0), base, blend=8.0)
        BASES[(lane, f)] = base
    for x, z in COAL:
        land.flatten(rect(x - 5.5, x + 5.5, z - 5.5, z + 5.5), round(land.height(x, z)), blend=6.0)
        BASES[("coal", x, z)] = float(round(land.height(x, z)))
    # the lines: the race tracks on their grades, the main line level --
    # gently into the Bottoms, a sheer cut through the breaks
    for path in LANES:
        land.pin_path(path, YS, half=7.5, blend=12.0)
    mid = [(MAIN_X, z) for z in range(-140, 141, 10)]
    land.pin_path(mid, [0.0] * len(mid), half=7.5, blend=18.0)
    for z0, z1 in ((-260, -140), (140, 260)):
        cut = [(MAIN_X, float(z)) for z in range(z0, z1 + 1, 10)]
        land.pin_path(cut, [0.0] * len(cut), half=7.5, blend=1.0)

    def paint(x: float, z: float, h: float):
        if h < 0.9 and rails.distance_to(WASH, x, z) < 14.0:
            return "#b0a07a"                     # the wash's gravel bed
        if h > 12.5:
            return (CLAY, CLAY_DARK, CLAY_PALE)[int(h) % 3]
        if h > 9.5 and abs(z) > 150:
            return CLAY_PALE
        if COULEE[0] - 12 < x < COULEE[1] + 12 and COULEE[2] - 14 < z < COULEE[2]:
            return GRASS_DEEP
        if _patchy(x, z):
            return GRASS_DRY
        # the swells banded by height, so their shape reads at a glance:
        # lush in the hollows, sun-cured on the crowns
        if h < 1.5:
            return GRASS_DEEP
        if h >= 9.0:
            return "#9a9658"
        if h >= 6.0:
            return "#8a9554"
        return None

    land.colour(paint)
    return land


def _patchy(x: float, z: float) -> bool:
    v = math.sin(x / 47.0 + 1.3) * math.cos(z / 39.0) + 0.6 * math.sin((x - z) / 33.0 + 0.4) + \
        0.35 * math.cos((x + 2.0 * z) / 27.0)
    return v > 0.7


# ==================================================================== edge
def _edge(b: ArenaArea, rng: random.Random) -> None:
    """The breaks along the north and south, a low prairie horizon east and
    west; the main line's two portals in the breaks."""
    hx, hz, m = b.half_x, b.half_z, b.margin
    room_walls(b, rect(-hx - m, hx + m, -hz - m, hz + m), m, 0.0, 26.0, CLAY_DARK, sides=("x-", "x+"))
    for side in (-1, 1):
        zc = side * (hz + m / 2.0)
        # the wall either side of the portal, and over it
        wall(b, "x", zc, m, -hx, hx, 0.0, 40.0, CLAY_DARK,
             gaps=[(MAIN_X - PORTAL_W, MAIN_X + PORTAL_W, PORTAL_H)])
        # the dark of the tunnel, a few units in
        b.box([MAIN_X, PORTAL_H / 2.0, side * (hz + m * 0.7)], [PORTAL_W * 2.0, PORTAL_H, m * 0.6],
              "#0a0a0c")
        # the portal's stone face: piers, the arch ring, the date stone
        face = side * (hz - 0.6)
        for px in (MAIN_X - PORTAL_W - 1.6, MAIN_X + PORTAL_W + 1.6):
            b.box([px, (PORTAL_H + 3.0) / 2.0, face], [3.2, PORTAL_H + 3.0, 1.2], STONE)
        b.box([MAIN_X, PORTAL_H + 1.5, face], [PORTAL_W * 2.0, 3.0, 1.2], STONE)
        b.box([MAIN_X, PORTAL_H + 4.0, face - side * 0.1], [PORTAL_W * 2.0 + 10.0, 2.0, 1.0], STONE_DARK)
        b.box([MAIN_X, PORTAL_H + 1.5, face - side * 0.65], [4.0, 1.8, 0.1], "#c8bca4", collide=False,
              decal=sign_decal("1887", "#c8bca4", "#4a4038", 3.0))
        # ragged crest of the breaks along the wall
        for i in range(30):
            x = -hx + (i + 0.5) * (2 * hx) / 30.0
            top = rng.uniform(4.0, 16.0)
            b.box([x, 40.0 + top / 2.0, zc], [2 * hx / 30.0 - 1.0, top, m + 1.0 + (i % 3) * 0.13],
                  rng.choice([CLAY, CLAY_DARK, CLAY_PALE]), collide=False)
    backdrop(b, "hills", 0.0, rng, ["#5a6a3a", "#6a7a44", "#4a5a32"], sides=("x-", "x+"), depth=200.0)
    backdrop(b, "mesas", 0.0, rng, [CLAY_DARK, "#7a5a40", "#5a4434"], sides=("z-", "z+"), depth=120.0)


# ================================================================= tracks
def _tracks(b: ArenaArea) -> None:
    for path in LANES:
        lay_graded(b, path, YS)
    # the main line: in the area from portal to portal, the Big Fill's top
    # its bed over the coulee
    lay_track(b, [(MAIN_X, -b.half_z - 6.0), (MAIN_X, b.half_z + 6.0)])
    # the stop boards short of the diamond
    for lane, path, side in (("a", LANE_A, 1.0), ("b", LANE_B, -1.0)):
        d = _lane_cross_d(path) - 13.0
        x, z, yaw = beside(path, d, side * 5.6)
        b.cyl([x, 2.0, z], [0.5, 4.0, 0.5], WOOD_DARK)
        b.box([x, 4.6, z], [2.6, 1.6, 2.6], WHITE, collide=False, r=[0.0, yaw, 0.0],
              decal=sign_decal("STOP", WHITE, "#b8322a", 2.0))
        _keep(rect(x - 1.5, x + 1.5, z - 1.5, z + 1.5))


def _lane_cross_d(path) -> float:
    """How far along a lane it crosses the main line."""
    walked = 0.0
    for (x0, z0), (x1, z1) in zip(path, path[1:]):
        seg = math.hypot(x1 - x0, z1 - z0)
        if (x0 - MAIN_X) * (x1 - MAIN_X) <= 0 and x1 != x0:
            return walked + seg * (MAIN_X - x0) / (x1 - x0)
        walked += seg
    return walked / 2.0


def _gate_specs(b: ArenaArea):
    """The crossing gates (their arms the client's): on each lane, one on
    each side of the main line, right of the way the cart comes."""
    out = []
    for lane, path in (("a", LANE_A), ("b", LANE_B)):
        d_x = _lane_cross_d(path)
        for along, side in ((-11.0, 1.0), (11.0, -1.0)):
            x, z, yaw = beside(path, d_x + along, side * 4.8)
            lx, lz, lyaw = rails.at(path, d_x + along)
            ax, az = lx - x, lz - z
            arm_yaw = math.atan2(ax, az)
            fx, fz = math.sin(lyaw), math.cos(lyaw)
            facing = -1.0 if along < 0 else 1.0
            lamps = [b.at(x + fx * facing * 0.7 * k + fx * -facing * 0.0, 4.4, z + fz * facing * 0.7 * k)
                     for k in (-1, 1)]
            out.append({"p": b.at(x, 4.2, z), "yaw": round(arm_yaw, 4), "len": 8.6, "lane": lane,
                        "lamps": lamps, "post": [round(x, 2), round(z, 2)], "face": round(lyaw, 4)})
    return out


# ================================================================= coulee
def _coulee(b: ArenaArea, rng: random.Random) -> None:
    """Buffalo Creek's coulee: a grassy draw eight deep, its north side
    stepping down in benches, its south side the raw cutbank of the breaks;
    the creek winding down it; the Big Fill carrying the main line over it
    with the stone culvert through its foot; the hobo jungle in its lee."""
    x0, x1, z0, z1 = COULEE
    rings = [rect(x0, x1, z0, z1), rect(x0 + 5.0, x1 - 5.0, z0 + 5.0, z1 - 5.0),
             rect(x0 + 10.0, x1 - 10.0, z0 + 10.0, z1 - 10.0), rect(x0 + 15.0, x1 - 15.0, z0 + 15.0, z1 - 15.0)]
    colours = (GRASS_DEEP, "#5a6e38", "#6a6a42", "#7a7050")
    for k in range(3):
        plate(b, carve(rings[k], [rings[k + 1], FILL]), -2.0 * (k + 1), 10.0 - 2.0 * (k + 1), colours[k],
              studs=True)
    plate(b, carve(rings[3], [FILL]), FLOOR_Y, 2.0, colours[3], studs=True)
    # the Big Fill: solid to the main line's bed, the culvert through its foot
    fx0, fx1, fz0, fz1 = FILL
    c0, c1 = CULVERT
    b.box([0.0, -5.0, (fz0 + c0) / 2.0], [fx1 - fx0, 10.0, c0 - fz0], EARTH)
    b.box([0.0, -5.0, (c1 + fz1) / 2.0], [fx1 - fx0, 10.0, fz1 - c1], EARTH)
    b.box([0.0, -1.0, (c0 + c1) / 2.0], [fx1 - fx0, 2.0, c1 - c0], STONE)
    b.box([0.0, -9.0, (c0 + c1) / 2.0], [fx1 - fx0, 2.0, c1 - c0], STONE_DARK, studs=True)
    for x in (fx0 - 0.4, fx1 + 0.4):
        # the headwalls: stone round the culvert's mouth
        for z in (c0 - 1.2, c1 + 1.2):
            b.box([x, -5.0, z], [0.8, 6.0, 2.4], STONE)
        b.box([x, -1.6, (c0 + c1) / 2.0], [0.8, 1.2, c1 - c0], STONE)
        b.box([x, -0.6, (c0 + c1) / 2.0], [1.0, 0.8, c1 - c0 + 6.0], STONE_DARK)
    # hobo signs chalked on the west headwall: "kind lady", "good water"
    b.box([fx0 - 0.82, -4.6, c0 - 1.2], [0.04, 1.2, 1.6], WHITE, collide=False,
          decal=sign_decal("+ o", STONE, WHITE, 1.4))
    b.box([fx0 - 0.82, -4.6, c1 + 1.2], [0.04, 1.2, 1.6], WHITE, collide=False,
          decal=sign_decal("~ ^", STONE, WHITE, 1.4))
    # the creek, winding down the floor and through the culvert
    n = 24
    step = (x1 - x0 - 30.0) / n
    for k in range(n):
        x = x0 + 15.0 + (k + 0.5) * step
        z = (c0 + c1) / 2.0 + (0.0 if abs(x) < 16 else math.sin(k * 0.7) * 3.0)
        b.water(x, z, step + 0.4, 4.0 + (k % 2) * 0.01, FLOOR_Y + 0.26 + (k % 2) * 0.006, "#4a6a72")
    # stepping stones and a plank footbridge
    for k, x in enumerate((-90.0, -86.5, -83.0)):
        b.box([x, FLOOR_Y + 0.35, 178.0 + (k - 1) * 1.8], [2.0, 0.7, 2.0], STONE_DARK)
    b.box([70.0, FLOOR_Y + 0.9, 178.0], [3.0, 0.4, 10.0], WOOD)
    for z in (173.5, 182.5):
        b.box([70.0, FLOOR_Y + 0.35, z], [3.2, 0.7, 1.0], WOOD_DARK)
    # the hobo jungle: a lean-to of old boards, a fire, a coffee can, logs
    hx, hz = -60.0, 186.0
    b.box([hx, FLOOR_Y + 2.0, hz + 3.6], [8.0, 4.0, 0.4], "#7a6a52")
    b.box([hx, FLOOR_Y + 4.2, hz + 1.6], [8.4, 0.3, 4.6], "#6a5a42", r=[-0.35, 0.0, 0.0], collide=False)
    for x in (hx - 3.8, hx + 3.8):
        b.box([x, FLOOR_Y + 1.6, hz + 0.0], [0.4, 3.2, 0.4], WOOD_DARK)
    b.cyl([hx + 1.0, FLOOR_Y + 0.3, hz - 5.0], [3.0, 0.6, 3.0], "#4a4440")
    b.cone([hx + 1.0, FLOOR_Y + 1.2, hz - 5.0], [1.6, 1.4, 1.6], "#ff8a2a", material="neon", collide=False)
    b.cyl([hx + 2.2, FLOOR_Y + 1.0, hz - 4.4], [0.6, 0.8, 0.6], "#8a8680", material="metal", collide=False)
    for a in (0.0, 2.1, 4.2):
        b.cyl([hx + 1.0 + math.cos(a) * 3.4, FLOOR_Y + 0.5, hz - 5.0 + math.sin(a) * 3.4], [1.0, 1.0, 1.0],
              "#6a4a30")
    b.box([hx - 2.0, FLOOR_Y + 0.5, hz + 1.8], [3.0, 1.0, 1.2], "#a8885a")
    b.box([hx - 4.6, FLOOR_Y + 1.6, hz - 2.0], [0.15, 3.2, 0.15], WOOD_DARK)
    b.sphere([hx - 4.6, FLOOR_Y + 3.6, hz - 2.0], [1.2, 1.0, 1.2], "#b84a3a", collide=False)
    # cottonwoods along the benches and the cutbank's foot
    for x, z, y in ((-118.0, 160.0, -2.0), (-96.0, 197.0, -4.0), (-30.0, 160.0, -2.0), (40.0, 197.0, -4.0),
                    (96.0, 160.0, -2.0), (118.0, 196.0, -4.0), (-60.0, 168.0, -6.0)):
        _cottonwood(b, x, z, y, rng)
    _keep(rect(x0 - 4.0, x1 + 4.0, z0 - 4.0, z1 + 4.0))


def _cottonwood(b: ArenaArea, x: float, z: float, base: float, rng: random.Random,
                s: float = 1.0) -> None:
    b.cyl([x, base + 4.0 * s, z], [1.4 * s, 8.0 * s, 1.4 * s], "#6a5a48")
    b.box([x + 1.6 * s, base + 7.0 * s, z], [3.0 * s, 0.6 * s, 0.6 * s], "#6a5a48", collide=False,
          r=[0.0, 0.0, 0.5])
    for k in range(4):
        a = k * 1.7 + rng.uniform(0, 0.5)
        b.sphere([x + math.cos(a) * 2.4 * s, base + (9.0 + (k % 2) * 1.6) * s, z + math.sin(a) * 2.4 * s],
                 [6.0 * s, 4.6 * s, 6.0 * s], rng.choice(["#5a7a3a", "#6a8a42", "#4e6e34"]), collide=False)


# ================================================================== yards
def _yards(b: ArenaArea, rng: random.Random) -> None:
    """The yards the companies start from: a platform each, a string of
    cars on the siding behind."""
    for lane, z, name, roof in (("a", -150.0, "ROUNDHOUSE YARD", "#7a3a2a"),
                                ("b", 150.0, "ELEVATOR YARD", "#2f4a6a")):
        side = -1.0 if z < 0 else 1.0
        pz = z + side * 15.0
        rails.platform(b, rect(-376.0, -322.0, pz - 6.0, pz + 6.0))
        stair(b, "x", -319.0, -322.0, pz - 3.0, pz + 3.0, 0.0, 1.2, WOOD)
        rails.shelter(b, rect(-370.0, -334.0, pz - 3.4, pz + 3.4), 1.2, 9.0, roof)
        b.box([-352.0, 1.2 + 9.6 + 1.2, pz], [30.0, 2.4, 0.5], rails.CREAM,
              decal=sign_decal(name, rails.CREAM, "#3a2414", 12.5))
        for sx in (-373.0, -362.0, -354.0, -346.0, -338.0, -327.0):
            for w in (-1.4, 1.4):
                b.team_spawn(lane, sx, 1.51, pz + w, math.pi / 2.0, 0)
        buffer_stop(b, -372.0, z, math.pi / 2.0, roof)
        lantern(b, -326.0, 9.8, pz, WARM)
        b.mark("start", -362.0, 0.5, z, lane=lane)
        _keep(rect(-380.0, -318.0, pz - 8.0, pz + 8.0))
        # the siding behind the platform
        sz = pz + side * 16.0
        stub_track(b, -392.0, -300.0, sz)
        if lane == "a":
            boxcar(b, -380.0, sz, "x", "#7a2e22", "PRAIRIE & PACIFIC")
            rails.flatcar(b, -354.0, sz, "x", "timber", rng)
            caboose(b, -330.0, sz, "x", "#a8281e")
        else:
            boxcar(b, -380.0, sz, "x", "#6a3a26", "GRAIN", door="shut")
            boxcar(b, -354.0, sz, "x", "#7a2e22", "GRAIN", door="shut")
            caboose(b, -330.0, sz, "x", "#2a4a6a")
        _keep(rect(-394.0, -298.0, sz - 5.0, sz + 5.0))


# ============================================================ engine house
def _engine_house(b: ArenaArea, rng: random.Random) -> None:
    """The brick engine house under the breaks: four stalls with their tall
    doors on the turntable, two engines in for the night, the smoke jacks
    on the roof, the machine shop's bench and the oil house."""
    x0, x1, z0, z1 = ENGINE_HOUSE
    doors = [(z - 4.0, z + 4.0, 12.0) for z in STALLS]
    building(b, ENGINE_HOUSE, 0.0, 15.0, BRICK, roof_colour="#3a3a3e",
             doors={"x+": doors, "z+": [(-352.0, -344.0, 7.0)]},
             windows={"z+": [(-372.0, -360.0, 6.0, 11.0), (-336.0, -324.0, 6.0, 11.0), (-316.0, -306.0, 6.0, 11.0)],
                      "x-": [(-232.0, -222.0, 6.0, 11.0), (-214.0, -204.0, 6.0, 11.0)]},
             glass=True, lights=WARM, floor_colour="#4a4642")
    for z in STALLS:
        threshold(b, ENGINE_HOUSE, "x+", (z - 4.0, z + 4.0))
    threshold(b, ENGINE_HOUSE, "z+", (-352.0, -344.0))
    gable(b, ENGINE_HOUSE, 16.2, "#3a3a3e", "x", 3, 1.2, 0.6)
    # the smoke jacks over the stalls
    for z in STALLS:
        b.box([-330.0, 21.8, z], [2.0, 2.4, 2.0], "#2a2a2c", material="metal")
    # stall tracks inside and out to the turntable's rim
    for k, z in enumerate(STALLS):
        stub_track(b, x0 + 3.0, x1 - 1.0, z)
        ang = math.atan2(z - TURNTABLE[1], x1 - TURNTABLE[0])
        rim = (TURNTABLE[0] + math.cos(ang) * TT_R, TURNTABLE[1] + math.sin(ang) * TT_R)
        lay_track(b, [(x1, z), rim])
    locomotive(b, -326.0, STALLS[1], "x", facing=1.0, colour="#1e2a22", name="No. 14")
    locomotive(b, -330.0, STALLS[3], "x", facing=1.0, colour="#2a1e1e", name="No. 9", tender=True)
    # the machine shop's bench and a lathe at the back
    b.box([-370.0, 1.6, -218.0], [3.0, 1.6, 16.0], WOOD_DARK)
    b.box([-370.0, 2.8, -222.0], [2.0, 1.2, 3.0], "#5a5a5e", material="metal")
    crate_stack(b, -366.0, -238.0 + 4.0, rng)
    # the oil house beside it
    oil = rect(-296.0, -284.0, -246.0, -236.0)
    building(b, oil, 0.0, 6.0, "#7a6a5a", roof_colour="#3a3a3e", doors={"z+": [(-292.0, -288.0, 5.0)]})
    threshold(b, oil, "z+", (-292.0, -288.0))
    for k in range(3):
        rails.barrel(b, -282.0, -232.0 + k * 2.4, "#3a4a5a")
    _keep(rect(x0 - 2.0, x1 + 2.0, z0 - 2.0, z1 + 2.0))
    _keep(rect(oil[0] - 2.0, oil[1] + 6.0, oil[2] - 1.0, oil[3] + 6.0))


def _turntable(b: ArenaArea) -> None:
    """The turntable: a pit two deep with its ring rail and the bridge across
    it on its centre pivot (walk the bridge or drop into the pit)."""
    cx, cz = TURNTABLE
    px0, px1, pz0, pz1 = TT_PIT
    slab(b, TT_PIT, -2.0, 3.0, "#5a544c", studs=True)
    # the ground round the circle, strip by strip
    strip = 4.0
    z = pz0
    while z < pz1 - 1e-6:
        zm = z + strip / 2.0
        dz = abs(zm - cz)
        chord = math.sqrt(max(0.0, TT_R * TT_R - dz * dz))
        for a, c in ((px0, cx - chord), (cx + chord, px1)):
            if c - a > 0.05:
                b.box([(a + c) / 2.0, -1.0, zm], [c - a, 2.0, strip], GRASS_DRY, studs=True)
        z += strip
    # the ring rail and the pivot
    for k in range(24):
        a = k * math.tau / 24.0
        b.box([cx + math.cos(a) * (TT_R - 1.2), -1.8, cz + math.sin(a) * (TT_R - 1.2)],
              [0.4, 0.4, 2 * math.pi * (TT_R - 1.2) / 24.0 + 0.2], rails.RAIL, collide=False,
              r=[0.0, -a, 0.0], material="metal")
    b.cyl([cx, -1.0, cz], [3.0, 2.0, 3.0], "#4a4a4e", material="metal")
    # the bridge: a deck on the pivot, its rails, a cab for the operator
    b.box([cx, -0.4, cz], [2 * TT_R - 0.6, 0.8, 4.6], "#3a3a3e", material="metal")
    for side in (-1.6, 1.6):
        b.box([cx, 0.2, cz + side], [2 * TT_R - 0.6, 0.4, 0.36], rails.RAIL, collide=False, material="metal")
    b.box([cx + TT_R - 3.0, 2.0, cz - 3.2], [2.4, 4.0, 1.8], "#5a3a2a")
    b.box([cx + TT_R - 3.0, 4.2, cz - 3.2], [2.8, 0.4, 2.2], "#3a3a3e")
    _keep(rect(px0 - 2.0, px1 + 2.0, pz0 - 2.0, pz1 + 2.0))


def _coaling(b: ArenaArea, rng: random.Random) -> None:
    """The coaling tower astride the service track, the sand house and the
    ash pit; a stair up the tower's side to the bunker roof."""
    x, z = COALING
    stub_track(b, TURNTABLE[0] + TT_R + 1.0, -150.0, z)
    rails.coaling_tower(b, x, z, "x", height=13.0)
    flight(b, "z", z + 28.0, z + 8.5, x - 3.0, x + 3.0, 0.0, 23.8, WOOD, fill=-0.3)
    b.mark("perch", x, 23.8, z + 4.0)
    # the sand house and its drier stack
    sand = rect(-176.0, -160.0, -238.0, -226.0)
    building(b, sand, 0.0, 7.0, "#8a7a62", roof_colour="#3a3a3e", doors={"x-": [(-234.0, -230.0, 6.0)]})
    threshold(b, sand, "x-", (-234.0, -230.0))
    b.cyl([-164.0, 10.0, -232.0], [1.2, 6.0, 1.2], "#2a2a2c", material="metal")
    # the ash pit between the rails, glowing a little
    b.box([x + 16.0, 0.05, z], [8.0, 0.1, 3.0], "#ff6a2a", material="neon", collide=False)
    sleeper_pile(b, -160.0, -204.0, "x")
    _keep(rect(x - 9.0, x + 9.0, z - 9.0, z + 30.0))
    _keep(rect(sand[0] - 2.0, sand[1] + 2.0, sand[2] - 2.0, sand[3] + 2.0))
    _keep(rect(-170.0, -150.0, -210.0, -198.0))
    _keep(rect(TURNTABLE[0] + TT_R, -148.0, z - 3.0, z + 3.0))


# ============================================================== elevators
def _elevators(b: ArenaArea, rng: random.Random) -> None:
    """The grain elevators, the prairie's skyline: three wooden houses, red,
    each with its headhouse on top, the wagon drive through the middle one,
    the concrete bins beside, a car under the spout of each, the scale
    house -- and the lightning rod on the tallest."""
    heights = (34.0, 40.0, 46.0)
    names = ("FARMERS", "UNION", "THUNDER JCT. GRAIN CO.")
    for k, (area, h) in enumerate(zip(ELEVATORS, heights)):
        x0, x1, z0, z1 = area
        cx, cz = (x0 + x1) / 2.0, (z0 + z1) / 2.0
        w = x1 - x0
        if k == 1:
            # the wagon drive through its foot, north to south
            b.box([x0 + 2.0, h / 2.0, cz], [4.0, h, z1 - z0], ELEVATOR)
            b.box([x1 - 2.0, h / 2.0, cz], [4.0, h, z1 - z0], ELEVATOR)
            b.box([cx, (h + 9.0) / 2.0, cz], [w - 8.0, h - 9.0, z1 - z0], ELEVATOR)
            slab(b, rect(x0 + 4.0, x1 - 4.0, z0, z1), 0.2, 0.2, "#6a5a48")
        else:
            b.box([cx, h / 2.0, cz], [w, h, z1 - z0], ELEVATOR)
        # the headhouse and its little gable
        b.box([cx, h + 4.0, cz], [w * 0.5, 8.0, (z1 - z0) * 0.7], ELEVATOR_DARK)
        gable(b, rect(cx - w * 0.25, cx + w * 0.25, cz - (z1 - z0) * 0.35, cz + (z1 - z0) * 0.35),
              h + 8.0, "#3a3a3e", "z", 2, 1.2, 0.4)
        # the name down the face, white on red
        b.box([cx, h * 0.62, z0 - 0.06], [w - 2.0, 3.4, 0.1], WHITE, collide=False,
              decal=sign_decal(names[k], ELEVATOR, WHITE, w - 3.0))
        # trim at the eaves
        b.box([cx, h - 0.4, z0 - 0.2], [w + 0.2, 0.8, 0.3], "#e8dcc8", collide=False)
        # the spout swung down to the car on the siding
        b.box([cx, h * 0.45, z0 - 5.0], [0.9, 0.9, 13.0], "#7a7a74", r=[0.85, 0.0, 0.0], collide=False,
              material="metal")
        _keep(rect(x0 - 2.0, x1 + 2.0, z0 - 2.0, z1 + 2.0))
    # the lightning rod on the tallest (the storm finds it: rr_weather)
    tall = ELEVATORS[2]
    tx, tz = (tall[0] + tall[1]) / 2.0, (tall[2] + tall[3]) / 2.0
    b.cyl([tx, heights[2] + 8.0 + 2.4 * 2 + 4.0, tz], [0.3, 8.0, 0.3], "#8a8680", material="metal")
    b.sphere([tx, heights[2] + 8.0 + 2.4 * 2 + 8.2, tz], [0.8, 0.8, 0.8], "#c8c0b0", material="metal")
    # the annex on the first, and the stair to its roof (a perch)
    annex = rect(-378.0, -362.0, 202.0, 216.0)
    building(b, annex, 0.0, 10.0, ELEVATOR_DARK, roof_colour="#3a3a3e",
             doors={"z-": [(-374.0, -368.0, 7.0)]}, windows={"x-": [(205.0, 213.0, 4.0, 7.0)]})
    threshold(b, annex, "z-", (-374.0, -368.0))
    flight(b, "x", -396.0, -378.0, 204.0, 210.0, 0.0, 11.2, WOOD, fill=-0.3)
    b.mark("perch", -370.0, 11.2, 209.0)
    # the concrete bins
    for k, x in enumerate((-262.0, -250.0, -238.0)):
        b.cyl([x, 15.0, 208.0], [11.4, 30.0, 11.4], "#c8c0b0")
        b.cyl([x, 30.4, 208.0], [11.8, 0.8, 11.8], "#a8a090")
    b.box([-250.0, 33.0, 208.0], [28.0, 4.4, 6.0], "#b8b0a0")
    _keep(rect(-270.0, -230.0, 200.0, 216.0))
    # the siding along the front, a car spotted under each spout
    stub_track(b, -392.0, -220.0, 189.0)
    for x, colour in ((-353.0, "#6a3a26"), (-322.0, "#7a2e22"), (-289.0, "#5a2a22")):
        boxcar(b, x, 189.0, "x", colour, "GRAIN", door="open")
    _keep(rect(-394.0, -218.0, 184.0, 194.0))
    # the scale house and a grain wagon waiting on the scale
    scale = rect(-232.0, -216.0, 180.0, 192.0)
    building(b, scale, 0.0, 6.0, "#a8885a", roof_colour="#5a3a2a", doors={"z-": [(-226.0, -222.0, 5.0)]},
             windows={"x-": [(183.0, 189.0, 2.6, 5.0)]}, glass=True, lights=WARM)
    threshold(b, scale, "z-", (-226.0, -222.0))
    gable(b, scale, 7.2, "#5a3a2a", "x", 2, 1.0, 0.6)
    b.box([-210.0, 0.1, 186.0], [6.0, 0.2, 10.0], "#5a5a5e", collide=False, material="metal")
    rails.wagon(b, -210.0, 186.0, "z", "#7a5a3a")
    _keep(rect(scale[0] - 2.0, -204.0, scale[2] - 2.0, scale[3] + 2.0))


# ============================================================ homestead
def _homestead(b: ArenaArea, rng: random.Random, land: Land) -> None:
    """A homesteader's claim on the west swell: the sod house dug into the
    rise (a door and two little windows, grass on its roof), the windpump
    and its stock tank, the garden, the washing on the line, the storm
    cellar's mound -- and the wheat shocks standing in the stubble."""
    base = 2.0
    sx, sz = SOD
    house = rect(sx - 10.0, sx + 10.0, sz - 7.0, sz + 7.0)
    building(b, house, base, 6.0, "#6a5a40", t=1.6, roof_colour="#6a8a42", roof_t=1.4,
             doors={"x+": [(sz - 2.0, sz + 2.0, base + 5.0)]},
             windows={"x+": [(sz - 6.0, sz - 3.6, base + 2.6, base + 4.2), (sz + 3.6, sz + 6.0, base + 2.6, base + 4.2)]},
             glass=True, lights=WARM, floor_colour="#5a4a34")
    threshold(b, house, "x+", (sz - 2.0, sz + 2.0), t=1.6, y0=base)
    # sod courses on the walls and grass tufts on the roof
    for k in range(3):
        b.box([sx, base + 1.6 + k * 1.6, sz - 7.06], [20.0, 0.2, 0.1], "#4a3e2c", collide=False)
    b.cyl([sx - 5.0, base + 9.0, sz + 2.0], [1.0, 2.6, 1.0], "#5a5a5e", material="metal")
    # inside: a stove, a table, a bed
    b.box([sx - 7.0, base + 1.4, sz - 4.0], [2.0, 2.0, 2.0], "#2a2a2c", material="metal")
    b.box([sx, base + 1.2, sz], [3.0, 0.3, 2.0], WOOD)
    b.box([sx - 6.0, base + 0.9, sz + 3.6], [5.0, 1.0, 2.4], "#8a6a4a")
    _keep(rect(house[0] - 2.0, house[1] + 3.0, house[2] - 2.0, house[3] + 2.0))
    # the windpump on its tower over the stock tank
    px, pz = PUMP
    for dx in (-2.2, 2.2):
        for dz in (-2.2, 2.2):
            b.box([px + dx * 0.45, base + 9.0, pz + dz * 0.45], [0.4, 18.0, 0.4], "#7a7a74", material="metal",
                  r=[dz * 0.06, 0.0, -dx * 0.06], collide=False)
    b.box([px, base + 9.0, pz], [1.2, 18.0, 1.2], "#6a6a64", material="metal")
    b.box([px, base + 17.6, pz], [3.0, 0.4, 3.0], "#5a5a54", material="metal")
    b.cyl([px + 6.0, base + 1.2, pz], [8.0, 2.4, 8.0], "#7a7a74", material="metal")
    b.cyl([px + 6.0, base + 2.0, pz], [7.2, 0.4, 7.2], "#4a6a72", collide=False, material="glass", alpha=0.8)
    _keep(rect(px - 3.0, px + 11.0, pz - 5.0, pz + 5.0))
    # the garden: rows of green, a scarecrow
    for k in range(5):
        b.box([sx + 22.0, base + 0.4, sz - 18.0 + k * 3.0], [14.0, 0.8, 1.2], "#4a6a2a", studs=True)
    b.box([sx + 30.0, base + 3.0, sz - 12.0], [0.3, 6.0, 0.3], WOOD_DARK)
    b.box([sx + 30.0, base + 4.6, sz - 12.0], [3.6, 0.3, 0.3], WOOD_DARK, collide=False)
    b.box([sx + 30.0, base + 4.2, sz - 12.0], [1.6, 2.0, 0.8], "#5a6a8a", collide=False)
    b.sphere([sx + 30.0, base + 5.8, sz - 12.0], [1.1, 1.1, 1.1], "#d8c08a", collide=False)
    b.cone([sx + 30.0, base + 6.6, sz - 12.0], [2.6, 0.9, 2.6], "#c8a040", collide=False)
    _keep(rect(sx + 14.0, sx + 32.0, sz - 20.0, sz - 4.0))
    # the washing line's posts (the washing is a rig)
    for x in (sx + 14.0, sx + 30.0):
        b.box([x, base + 3.0, sz + 14.0], [0.4, 6.0, 0.4], WOOD_DARK)
    _keep(rect(sx + 13.0, sx + 31.0, sz + 13.0, sz + 15.0))
    # the storm cellar: a mound with a slanting door, a room inside it
    cx, cz = CELLAR
    mound = rect(cx - 7.0, cx + 7.0, cz - 6.0, cz + 6.0)
    building(b, mound, base, 4.0, "#6a5a40", t=1.4, roof_colour="#6a8a42", roof_t=1.0,
             doors={"x-": [(cz - 1.8, cz + 1.8, base + 3.4)]}, floor_colour="#4a3e2c")
    threshold(b, mound, "x-", (cz - 1.8, cz + 1.8), t=1.4, y0=base)
    b.box([cx - 7.6, base + 2.0, cz], [0.3, 3.6, 4.0], "#5a4030", r=[0.0, 0.0, 0.3], collide=False)
    b.box([cx + 2.0, base + 1.0, cz + 3.6], [4.0, 1.6, 1.4], WOOD)
    b.box([cx + 5.1, base + 2.0, cz - 1.5], [1.0, 0.2, 4.6], WOOD_DARK)
    for k in range(4):
        b.box([cx + 5.1, base + 2.5, cz - 3.0 + k * 1.0], [0.6, 0.8, 0.6], "#c8a040", collide=False)
    _keep(rect(mound[0] - 3.0, mound[1] + 2.0, mound[2] - 2.0, mound[3] + 2.0))
    # the wheat shocks standing in rows in the stubble
    for row in range(5):
        for k in range(6):
            x = -128.0 + k * 11.0 + (row % 2) * 5.0
            z = -24.0 + row * 12.0
            if not clear_of(rect(x - 2.0, x + 2.0, z - 2.0, z + 2.0), LANES, 11.0):
                continue
            if _blocked(x, z):
                continue
            y = land.height(x, z)
            b.cone([x, y + 2.0, z], [3.2, 4.0, 3.2], "#c8a850")
            b.cyl([x, y + 2.6, z], [2.2, 0.4, 2.2], "#a88a3a", collide=False)
            KEEP.append(rect(x - 2.0, x + 2.0, z - 2.0, z + 2.0))


# ================================================================== depot
def _depot(b: ArenaArea, rng: random.Random) -> None:
    """Thunder Junction's depot on the main line: two storeys of yellow
    clapboard on a raised floor, the waiting room and the ticket office, the
    operator's bay out on the platform with his telegraph (a call box), the
    train-order board over it, the agent's rooms upstairs."""
    base = 1.2
    x0, x1, z0, z1 = DEPOT_HOUSE
    storeyed(b, DEPOT_HOUSE, [8.0, 7.0], DEPOT_YELLOW, roof=DEPOT_TRIM, base=base,
             doors={"x-": [(-88.0, -80.0, base + 7.0)], "x+": [(-87.4, -80.6, base + 7.0), (-72.0, -66.0, base + 7.0)],
                    "z+": [(-28.0, -22.0, base + 7.0)]},
             windows=[{"x-": [(-100.0, -94.0, base + 2.6, base + 6.0), (-74.0, -68.0, base + 2.6, base + 6.0)],
                       "z-": [(-32.0, -26.0, base + 2.6, base + 6.0)]},
                      {"x+": [(-100.0, -94.0, base + 10.6, base + 13.6), (-78.0, -72.0, base + 10.6, base + 13.6)],
                       "x-": [(-100.0, -94.0, base + 10.6, base + 13.6), (-78.0, -72.0, base + 10.6, base + 13.6)],
                       "z+": [(-30.0, -20.0, base + 10.6, base + 13.6)]}],
             wells=[rect(x0 + 2.0, x0 + 8.0, z0 + 2.0, z0 + 14.0)])
    flight(b, "z", z0 + 16.0, z0 + 2.0, x0 + 2.0, x0 + 8.0, base + 0.4, base + 8.0, WOOD, fill=base)
    gable(b, DEPOT_HOUSE, base + 15.0 + 1.2, DEPOT_TRIM, "z", 4, 1.2, 1.0)
    for side, span in (("x-", (-88.0, -80.0)), ("x+", (-72.0, -66.0)), ("z+", (-28.0, -22.0))):
        threshold(b, DEPOT_HOUSE, side, span, y0=base)
    # the raised floor's foundation, and steps up to the doors
    b.box([(x0 + x1) / 2.0, base / 2.0, (z0 + z1) / 2.0], [x1 - x0, base, z1 - z0], STONE_DARK)
    stair(b, "x", x0 - 2.0, x0, -87.5, -80.5, 0.0, base)
    stair(b, "z", z1 + 2.0, z1, -28.0, -22.0, 0.0, base)
    # the ticket office: a counter and a grille; benches in the waiting room
    b.box([-25.0, base + 1.6, -76.0], [12.0, 1.4, 1.0], WOOD_DARK)
    b.box([-25.0, base + 3.6, -76.0], [12.0, 2.6, 0.1], "#c8a040", collide=False, material="metal")
    for z in (-96.0, -90.0):
        b.box([-31.0, base + 0.9, z], [4.0, 1.0, 1.4], WOOD)
    wall_sign(b, x0 - 0.36, base + 9.4, -84.0, 18.0, 2.4,
              sign_decal("THUNDER JUNCTION", DEPOT_TRIM, rails.CREAM, 9.0), "x-", DEPOT_TRIM)
    wall_sign(b, x1 + 0.36, base + 9.4, -94.0, 12.0, 2.2,
              sign_decal("THUNDER JCT.", DEPOT_TRIM, rails.CREAM, 6.0), "x+", DEPOT_TRIM)
    b.mark("perch", -20.0, base + 8.4, -96.0)
    # the platform along the main line
    rails.platform(b, PLATFORM_N, top=base)
    stair(b, "z", PLATFORM_N[2] - 3.0, PLATFORM_N[2], -13.0, -7.0, 0.0, base)
    stair(b, "z", PLATFORM_N[3] + 3.0, PLATFORM_N[3], -13.0, -7.0, 0.0, base)
    # the operator's bay: windows up and down the line, his desk, the key
    building(b, BAY, base, 7.0, DEPOT_YELLOW, t=0.6, roof_colour=DEPOT_TRIM,
             doors={"x-": [(BAY[2] + 0.6, BAY[3] - 0.6, base + 7.0)]},
             windows={"x+": [(-87.0, -81.0, base + 2.6, base + 6.0)], "z-": [(-13.4, -10.6, base + 2.6, base + 6.0)],
                      "z+": [(-13.4, -10.6, base + 2.6, base + 6.0)]}, glass=True, lights=WARM)
    b.box([-11.2, base + 1.4, -84.0], [1.2, 1.8, 6.0], WOOD_DARK)
    b.box([-11.2, base + 2.35, -86.0], [0.8, 0.1, 1.4], "#d8d0b8", collide=False)
    b.mark("call", -12.0, base + 0.4, -84.0, name="the depot telegraph")
    # the train-order board's mast (its blades are a rig)
    b.box([-8.2, base + 6.5, -84.0], [0.6, 13.0, 0.6], "#3a3a3e", material="metal")
    lantern(b, -8.2, base, -70.0, WARM, post=9.0)
    # the flagpole at the platform's end (the flag is a rig)
    b.cyl([-8.2, base + 7.0, -58.0], [0.4, 14.0, 0.4], "#d8d8d0", material="metal")
    b.sphere([-8.2, base + 14.2, -58.0], [0.7, 0.7, 0.7], rails.GOLD, material="metal")
    # baggage carts and milk cans on the platform
    rails.barrel(b, -9.0, -60.0, "#8a8a84", y=base)
    rails.barrel(b, -9.0, -62.0, "#8a8a84", y=base)
    b.box([-10.0, base + 1.0, -104.0], [3.0, 1.0, 6.0], "#6a5a3a")
    for z in (-106.0, -102.0):
        b.cyl([-10.0, base + 0.5, z], [1.0, 1.0, 1.0], "#2a2a2c", r=[0.0, 0.0, math.pi / 2.0], collide=False)
    # the agent's chicken coop out back
    coop = rect(-58.0, -48.0, -96.0, -88.0)
    building(b, coop, 0.0, 3.6, "#c8b898", roof_colour="#6a3e24", doors={"x+": [(-93.0, -91.0, 2.6)]})
    for k in range(3):
        b.sphere([-53.0 + k * 2.0, 0.6, -84.0 - k * 1.4], [0.9, 0.8, 1.1], WHITE, collide=False)
        b.box([-53.0 + k * 2.0, 1.1, -83.5 - k * 1.4], [0.2, 0.3, 0.2], "#c8281e", collide=False)
    _keep(rect(x0 - 4.0, PLATFORM_N[1] + 1.0, PLATFORM_N[2] - 4.0, PLATFORM_N[3] + 4.0))
    _keep(rect(coop[0] - 2.0, coop[1] + 2.0, coop[2] - 2.0, coop[3] + 8.0))


# ================================================================== tower
def _tower(b: ArenaArea, rng: random.Random) -> None:
    """TJ Tower across the diamond from the depot: the relay room below,
    the lever room above with windows all round (a perch), an outside stair
    -- and the dispatcher's telephone in its box on the platform (a call
    box)."""
    base = 0.0
    x0, x1, z0, z1 = TOWER_HOUSE
    storeyed(b, TOWER_HOUSE, [8.0, 8.0], BRICK, roof="#3a3a3e", base=base,
             doors={"z-": [(-30.0, -24.0, 7.0)]},
             windows=[{"z+": [(-32.0, -22.0, 3.0, 6.0)], "x-": [(70.0, 76.0, 3.0, 6.0)]},
                      {"x+": [(68.0, 88.0, 10.0, 14.4)], "x-": [(68.0, 88.0, 10.0, 14.4)],
                       "z-": [(-34.0, -20.0, 10.0, 14.4)], "z+": [(-34.0, -20.0, 10.0, 14.4)]}],
             wells=[rect(x0 + 2.0, x0 + 8.0, z1 - 14.0, z1 - 2.0)])
    flight(b, "z", z1 - 16.0, z1 - 2.0, x0 + 2.0, x0 + 8.0, 0.4, 8.0, WOOD, fill=0.0)
    gable(b, TOWER_HOUSE, 16.0 + 1.2, "#3a3a3e", "x", 3, 1.2, 1.0)
    threshold(b, TOWER_HOUSE, "z-", (-30.0, -24.0))
    # the lever frame along the windows, the levers in a row
    b.box([x1 - 3.0, 8.9, (z0 + z1) / 2.0], [1.6, 1.0, 18.0], "#3a3a3e", material="metal")
    for k in range(12):
        colour = ("#c8281e", "#2a2a2a", "#e8c83a")[k % 3]
        b.box([x1 - 3.0, 10.8, z0 + 5.0 + k * 1.5], [0.25, 3.0, 0.25], colour, collide=False,
              r=[0.0, 0.0, -0.25 if k % 2 else 0.2])
    wall_sign(b, x0 - 0.36, 15.3, (z0 + z1) / 2.0, 12.0, 1.6,
              sign_decal("TJ TOWER", "#3a3a3e", rails.CREAM, 7.5), "x-", "#3a3a3e")
    b.mark("perch", (x0 + x1) / 2.0 + 2.0, 8.4, (z0 + z1) / 2.0 - 6.0)
    # the platform along the main line and the telephone's box on it
    rails.platform(b, PLATFORM_S, top=1.2)
    stair(b, "z", PLATFORM_S[2] - 3.0, PLATFORM_S[2], -13.0, -7.0, 0.0, 1.2)
    stair(b, "z", PLATFORM_S[3] + 3.0, PLATFORM_S[3], -13.0, -7.0, 0.0, 1.2)
    building(b, PHONE, 1.2, 7.0, "#3a5a3a", t=0.6, roof_colour="#3a3a3e",
             doors={"x-": [(PHONE[2] + 0.6, PHONE[3] - 0.6, 8.2)]},
             windows={"x+": [(81.0, 87.0, 3.8, 7.2)], "z-": [(-13.4, -10.6, 3.8, 7.2)],
                      "z+": [(-13.4, -10.6, 3.8, 7.2)]}, glass=True, lights=WARM)
    b.box([-10.9, 4.6, 84.0], [0.6, 1.6, 1.0], "#5a3a22")
    b.box([-10.75, 5.0, 84.6], [0.3, 0.6, 0.3], "#1a1a1a", collide=False)
    b.box([-10.8, 3.4, 84.0], [0.6, 0.6, 2.2], WOOD_DARK)
    # the line's own telephone out on the platform, on a post by the booth:
    # it is worked from the platform (the booth is too snug to stand in)
    b.box([-6.6, 3.2, 84.0], [0.5, 4.0, 0.5], WOOD_DARK)
    b.box([-6.6, 5.4, 84.0], [0.9, 1.6, 1.2], "#5a3a22")
    b.box([-7.1, 5.8, 84.0], [0.1, 0.6, 0.5], "#1a1a1a", collide=False)
    b.mark("call", -8.0, 1.6, 84.0, name="the tower telephone")
    lantern(b, -8.2, 1.2, 70.0, WARM, post=9.0)
    # a pile of new ties and rails by the tower, a handcar on its stub
    sleeper_pile(b, -52.0, 100.0, "x")
    stub_track(b, -64.0, -40.0, 114.0)
    handcar(b, -52.0, 114.0, "x")
    _keep(rect(x0 - 4.0, PLATFORM_S[1] + 1.0, PLATFORM_S[2] - 4.0, PLATFORM_S[3] + 4.0))
    _keep(rect(-66.0, -38.0, 94.0, 118.0))


# =============================================================== diamond
def _crossing(b: ArenaArea) -> None:
    """The Star Diamond: three lines crossing on one plank floor, the
    crossing gates (posts and crossbucks; the arms and lamps are drawn as
    the freight comes), a lamp on a pole at each corner."""
    for z in (-6.0, 0.0, 6.0):
        b.box([0.0, 0.13, z], [12.0, 0.08, 5.4], "#6a5238", collide=False)
    for gate in b.extra["sweep"]["gates"]:
        x, z = gate["post"]
        face = gate["face"]
        b.box([x, 4.3, z], [0.7, 8.6, 0.7], WHITE)
        b.box([x, 0.6, z], [1.6, 1.2, 1.6], STONE_DARK)
        # the counterweight behind the pivot
        ay = gate["yaw"]
        b.box([x - math.sin(ay) * 0.8, 4.2, z - math.cos(ay) * 0.8], [1.0, 1.0, 1.0], "#2a2a2c",
              material="metal", collide=False)
        # the lamp heads, facing the way the carts come
        for lamp in gate["lamps"]:
            lx, lz = lamp[0] - b.ox, lamp[2] - b.oz
            b.box([lx, 4.4, lz], [0.9, 0.9, 0.9], "#1a1a1a", collide=False, r=[0.0, face, 0.0])
        # the crossbuck over it all
        for tilt in (math.pi / 4.0, -math.pi / 4.0):
            b.box([x, 7.6, z], [5.0, 0.8, 0.12], WHITE, collide=False, r=[0.0, face + math.pi / 2.0, tilt],
                  decal=sign_decal("RAILROAD", WHITE, "#1a1a1a", 4.0))
        b.cone([x, 9.0, z], [1.0, 0.8, 1.0], "#2a2a2c", collide=False)
        _keep(rect(x - 2.0, x + 2.0, z - 2.0, z + 2.0))
    for x, z in ((-16.0, -22.0), (16.0, 22.0), (-16.0, 22.0), (16.0, -22.0)):
        lamp_post(b, x, z, 12.0, light=WARM)
        _keep(rect(x - 1.0, x + 1.0, z - 1.0, z + 1.0))


# ==================================================================== cut
def _cut(b: ArenaArea, land: Land) -> None:
    """Deadman's Cut: the county road's timber bridge over the main line
    where it goes into the breaks, a road up each bank to it."""
    z0, z1 = BRIDGE_Z
    deck = rect(-16.0, 16.0, z0, z1)
    slab(b, deck, BRIDGE_Y, 0.8, WOOD, studs=True)
    for z in (z0 + 0.3, z1 - 0.3):
        b.box([0.0, BRIDGE_Y + 1.6, z], [32.0, 0.3, 0.3], WOOD_DARK)
        for x in range(-14, 15, 4):
            b.box([float(x), BRIDGE_Y + 0.8, z], [0.4, 1.6, 0.4], WOOD_DARK)
    # the bents: two timber trestles standing in the cut either side of the line
    for x in (-8.0, 8.0):
        b.box([x, (BRIDGE_Y - 0.8) / 2.0, (z0 + z1) / 2.0], [1.2, BRIDGE_Y - 0.8, 1.2], WOOD_DARK)
        b.box([x, (BRIDGE_Y - 0.8) / 2.0, z0 + 1.0], [1.2, BRIDGE_Y - 0.8, 1.2], WOOD_DARK)
        b.box([x, (BRIDGE_Y - 0.8) / 2.0, z1 - 1.0], [1.2, BRIDGE_Y - 0.8, 1.2], WOOD_DARK)
    b.mark("perch", 0.0, BRIDGE_Y, (z0 + z1) / 2.0)
    # the road's ruts on the banks
    for x0, x1 in ((-58.0, -16.0), (16.0, 58.0)):
        b.box([(x0 + x1) / 2.0, BRIDGE_Y - 0.6 + 0.02, (z0 + z1) / 2.0], [x1 - x0, 0.04, 6.0], "#8a7458",
              collide=False)
    b.box([-30.0, BRIDGE_Y + 1.2, z1 + 3.0], [3.0, 2.4, 0.3], WHITE, collide=False,
          decal=sign_decal("COUNTY RD", WHITE, "#2a2a2a", 2.6))
    b.cyl([-30.0, BRIDGE_Y - 0.6 + 0.6, z1 + 3.0], [0.3, 1.2, 0.3], WOOD_DARK)
    _keep(rect(-60.0, 60.0, z0 - 4.0, z1 + 4.0))


# ================================================================ section
def _section(b: ArenaArea, rng: random.Random, land: Land) -> None:
    """The section house where the track gang bunks, its tool shed, and the
    big water tank over the main line."""
    house = rect(30.0, 54.0, -122.0, -100.0)
    building(b, house, 0.0, 8.0, "#c8a878", roof_colour="#5a3a2a",
             doors={"x-": [(-114.0, -108.0, 7.0)]}, windows={"z+": [(36.0, 42.0, 3.0, 6.0), (44.0, 50.0, 3.0, 6.0)]},
             glass=True, lights=WARM, floor_colour="#6a4e34")
    threshold(b, house, "x-", (-114.0, -108.0))
    gable(b, house, 9.2, "#5a3a2a", "x", 3, 1.2, 0.8)
    for k in range(3):
        b.box([50.0, 1.2, -118.0 + k * 5.0], [5.0, 1.0, 2.6], "#8a6a4a")
    b.cyl([36.0, 12.0, -104.0], [1.0, 3.0, 1.0], "#3a3a3e", material="metal")
    _keep(rect(house[0] - 3.0, house[1] + 2.0, house[2] - 2.0, house[3] + 2.0))
    # the water tank: a big one on a steel tower, its spout swung clear
    tx, tz = 26.0, -70.0
    for dx in (-4.0, 4.0):
        for dz in (-4.0, 4.0):
            b.box([tx + dx, 9.0, tz + dz], [0.9, 18.0, 0.9], IRONWORK, material="metal")
    slab(b, rect(tx - 7.5, tx + 7.5, tz - 7.5, tz + 7.5), 18.6, 0.6, WOOD)
    b.cyl([tx, 18.6 + 5.0, tz], [12.0, 10.0, 12.0], "#7a5335")
    b.cone([tx, 18.6 + 10.0 + 1.8, tz], [13.0, 3.6, 13.0], "#4a3a2a", collide=False)
    for k in range(3):
        b.cyl([tx, 20.0 + k * 3.4, tz], [12.1, 0.3, 12.1], rails.IRON, material="metal")
    b.cyl([tx, 32.2 + 2.0, tz], [0.25, 4.0, 0.25], "#8a8680", material="metal", collide=False)
    b.box([tx - 7.0, 20.6, tz], [6.0, 0.8, 0.8], "#3a3a3e", material="metal", r=[0.0, 0.0, -0.3],
          collide=False)
    flight(b, "x", tx + 22.0, tx + 7.5, tz - 2.0, tz + 2.0, 0.0, 18.6, WOOD, fill=-0.3)
    b.mark("perch", tx - 6.4, 18.6, tz - 6.4)
    _keep(rect(tx - 8.0, tx + 24.0, tz - 8.0, tz + 8.0))
    # the tool shed and the speeder on its stub
    shed = rect(56.0, 66.0, -96.0, -86.0)
    building(b, shed, 0.0, 5.0, "#8a6a4a", roof_colour="#5a3a2a", doors={"x-": [(-93.0, -89.0, 4.4)]})
    threshold(b, shed, "x-", (-93.0, -89.0))
    stub_track(b, 36.0, 56.0, -91.0)
    handcar(b, 46.0, -91.0, "x")
    _keep(rect(34.0, 68.0, -98.0, -84.0))


# ============================================================== ice house
def _ice_house(b: ArenaArea, rng: random.Random) -> None:
    """The ice house on the east swell's shoulder, where the fruit cars are
    iced: a great timber barn full of sawdust and ice, the icing dock up
    along its east end (a perch), two reefers on the siding below it."""
    base = ICE_Y
    x0, x1, z0, z1 = ICE_HOUSE
    building(b, ICE_HOUSE, base, 14.0, "#9a7a54", roof_colour="#4a3a2e",
             doors={"x-": [(-6.0, 6.0, base + 10.0)], "z-": [(96.0, 104.0, base + 8.0)],
                    "z+": [(108.0, 116.0, base + 8.0)]},
             windows={"z-": [(80.0, 88.0, base + 9.0, base + 12.0), (120.0, 128.0, base + 9.0, base + 12.0)],
                      "z+": [(80.0, 88.0, base + 9.0, base + 12.0), (120.0, 128.0, base + 9.0, base + 12.0)]},
             glass=False, lights=WARM, floor_colour="#a8946a")
    for side, span in (("x-", (-6.0, 6.0)), ("z-", (96.0, 104.0)), ("z+", (108.0, 116.0))):
        threshold(b, ICE_HOUSE, side, span, y0=base)
    gable(b, ICE_HOUSE, base + 15.2, "#4a3a2e", "x", 4, 1.4, 1.0)
    wall_sign(b, x0 - 0.36, base + 12.0, 0.0, 22.0, 2.4,
              sign_decal("PRAIRIE ICE CO.", "#4a3a2e", rails.CREAM, 10.0), "x-", "#4a3a2e")
    # inside: the ice blocks stacked in sawdust (cover)
    for k in range(6):
        bx = 84.0 + (k % 3) * 14.0
        bz = -14.0 + (k // 3) * 28.0
        for j in range(2):
            b.box([bx, base + 0.4 + 1.6 + j * 3.2, bz], [6.0, 3.2, 6.0], "#cfe6f0", material="glass",
                  alpha=0.9)
        b.box([bx, base + 0.4 + 0.1, bz], [8.0, 0.2, 8.0], "#c8a870", collide=False)
    # the icing dock along the east end, up at the cars' roofs, and its stair
    dock = rect(x1, x1 + 10.0, -24.0, 24.0)
    slab(b, dock, base + 9.0, 0.8, WOOD, studs=True)
    for z in (-22.0, -8.0, 8.0, 22.0):
        b.box([x1 + 9.0, base + 4.1, z], [1.0, 9.0, 1.0], WOOD_DARK)
    flight(b, "z", -40.0, -24.0, x1 + 2.0, x1 + 8.0, base, base + 9.0, WOOD, fill=base - 0.3)
    for k in range(5):
        b.box([x1 + 4.0, base + 9.0 + 1.0, -16.0 + k * 8.0], [2.0, 2.0, 2.0], "#cfe6f0", material="glass",
              alpha=0.9)
    b.box([x1 + 9.6, base + 10.4, 0.0], [0.3, 1.2, 48.0], WOOD_DARK)
    b.mark("perch", x1 + 5.0, base + 9.0, 4.0)
    # the siding below the dock, two reefers on it
    stub_track(b, -60.0, 60.0, x1 + 16.0, base=base, along="z")
    for z, label in ((-18.0, "PRAIRIE FRUIT EXPRESS"), (12.0, "PRAIRIE FRUIT EXPRESS")):
        boxcar(b, x1 + 16.0, z, "z", "#d8b048", label, door="shut", base=base)
    _keep(rect(x0 - 4.0, x1 + 22.0, -62.0, 62.0))


# ================================================================= lumber
def _lumber(b: ArenaArea, rng: random.Random, land: Land) -> None:
    """The lumber yard south of the line: stacks of boards in rows (cover to
    fight through), a lean-to shed, a wagon half loaded."""
    for row in range(3):
        for k in range(4):
            x = 24.0 + k * 13.0
            z = 80.0 + row * 16.0
            h = 3.0 + ((row + k) % 3) * 1.6
            b.box([x, h / 2.0, z], [9.0, h, 4.0], ("#c89a62", "#b8875a", "#d8aa72")[(row + k) % 3], studs=True)
            b.box([x, h + 0.2, z], [9.2, 0.4, 0.5], "#8a6040", collide=False)
    shed = rect(16.0, 72.0, 124.0, 132.0)
    for x in (17.0, 35.0, 53.0, 71.0):
        b.box([x, 4.0, 128.0], [0.8, 8.0, 0.8], WOOD_DARK)
    slab(b, shed, 8.6, 0.6, "#5a3a2a")
    rails.wagon(b, 44.0, 142.0, "x", "#6a4a30")
    _keep(rect(14.0, 74.0, 74.0, 148.0))


# =============================================================== the rest
def _school(b: ArenaArea, rng: random.Random) -> None:
    """The one-room schoolhouse on its rise north of the depot: the bell in
    its little tower, the desks in rows, the stove -- and the sum still on
    the blackboard from the last lesson."""
    base = 3.0
    x0, x1, z0, z1 = SCHOOL
    building(b, SCHOOL, base, 9.0, WHITE, roof_colour="#6a2a22", doors={"x+": [(-164.0, -158.0, base + 7.0)]},
             windows={"z-": [(-108.0, -102.0, base + 3.0, base + 7.0), (-98.0, -92.0, base + 3.0, base + 7.0)],
                      "z+": [(-108.0, -102.0, base + 3.0, base + 7.0), (-98.0, -92.0, base + 3.0, base + 7.0)]},
             glass=True, lights=WARM, floor_colour="#8a6a4a")
    threshold(b, SCHOOL, "x+", (-164.0, -158.0), y0=base)
    gable(b, SCHOOL, base + 10.2, "#6a2a22", "x", 3, 1.3, 0.8)
    # the bell tower over the door, its bell and a rope down
    b.box([x1 - 3.0, base + 16.0, -161.0], [4.0, 3.0, 4.0], WHITE)
    b.cone([x1 - 3.0, base + 19.6, -161.0], [5.0, 3.0, 5.0], "#6a2a22")
    b.cone([x1 - 3.0, base + 16.0, -161.0], [1.6, 1.6, 1.6], "#c8a040", material="metal", collide=False)
    # desks in rows, the teacher's desk, the stove, the blackboard
    for row in range(3):
        for k in range(3):
            b.box([x0 + 6.0 + row * 4.0, base + 1.2, -168.0 + k * 4.0], [2.0, 0.3, 2.4], WOOD)
            b.box([x0 + 6.0 + row * 4.0, base + 0.7, -168.0 + k * 4.0], [0.4, 1.0, 0.4], WOOD_DARK)
    b.box([x1 - 6.0, base + 1.4, -161.0], [2.0, 1.4, 4.0], WOOD_DARK)
    b.box([x0 + 2.6, base + 1.4, -153.0], [1.8, 2.0, 1.8], "#2a2a2c", material="metal")
    b.box([x0 + 1.25, base + 4.6, -161.0], [0.1, 3.4, 12.0], "#2a3a30", collide=False,
          decal=sign_decal("A TRAIN LEAVES CHICAGO AT 40 MPH...", "#2a3a30", "#e8e8e0", 12.0))
    b.mark("perch", x1 - 3.0, base + 10.2, -168.0)
    # the privy and the swing
    b.box([x0 - 6.0, base + 3.0, z1 - 2.0], [3.0, 6.0, 3.0], "#8a6a4a")
    b.box([x0 - 6.0, base + 6.2, z1 - 2.0], [3.6, 0.4, 3.6], "#6a2a22")
    for z in (z0 + 2.0, z0 + 8.0):
        b.box([x1 + 3.0, base + 3.0, z], [0.4, 6.0, 0.4], WOOD_DARK)
    b.box([x1 + 3.0, base + 6.2, z0 + 5.0], [0.4, 0.4, 6.4], WOOD_DARK)
    b.box([x1 + 3.0, base + 1.4, z0 + 5.0], [1.2, 0.2, 2.0], WOOD, collide=False)
    for z in (z0 + 4.2, z0 + 5.8):
        b.box([x1 + 3.0, base + 3.75, z], [0.08, 4.5, 0.08], "#c8b898", collide=False)
    _keep(rect(x0 - 9.0, x1 + 5.0, z0 - 2.0, z1 + 2.0))


def _bunk_cars(b: ArenaArea, rng: random.Random) -> None:
    """Where the extra gang lives: two old boxcars on a spur, windows cut in
    them, stovepipes through their roofs, a table and a washtub between."""
    z = BUNKS_Z
    stub_track(b, -126.0, -56.0, z)
    for x, colour in ((-108.0, "#6a3a26"), (-78.0, "#5a2a22")):
        boxcar(b, x, z, "x", colour, "BUNK CAR", door="open")
        for k in (-6.0, 6.0):
            b.box([x + k, 6.2, z - 3.05], [2.4, 1.6, 0.1], "#ffd88a", material="neon", collide=False)
            b.box([x + k, 6.2, z + 3.05], [2.4, 1.6, 0.1], "#ffd88a", material="neon", collide=False)
        b.cyl([x - 8.0, 9.6, z], [0.8, 2.4, 0.8], "#2a2a2c", material="metal")
    b.box([-93.0, 1.2, z - 8.0], [5.0, 0.3, 2.4], WOOD)
    b.box([-93.0, 0.6, z - 8.0], [0.6, 1.2, 0.6], WOOD_DARK)
    b.cyl([-86.0, 0.6, z - 8.5], [2.2, 1.2, 2.2], "#8a8680", material="metal")
    _keep(rect(-128.0, -54.0, z - 11.0, z + 6.0))


def _bottoms(b: ArenaArea, rng: random.Random) -> None:
    """The Bottoms round the diamond: the crossing watchman's shanty (his
    stove going, his flag and lantern by the door) and a pile of rails."""
    sx, sz = 24.0, 0.0
    shanty = rect(sx - 3.0, sx + 3.0, sz - 3.0, sz + 3.0)
    building(b, shanty, 0.0, 6.0, "#3a5a3a", t=0.5, roof_colour="#3a3a3e", doors={"x-": [(-1.4, 1.4, 5.0)]},
             windows={"z-": [(sx - 1.4, sx + 1.4, 2.6, 4.6)], "z+": [(sx - 1.4, sx + 1.4, 2.6, 4.6)]},
             glass=True, lights=WARM)
    threshold(b, shanty, "x-", (-1.4, 1.4), t=0.5)
    b.cyl([sx + 1.6, 8.0, sz + 1.6], [0.5, 2.6, 0.5], "#2a2a2c", material="metal")
    b.box([sx - 3.4, 2.4, sz + 2.2], [0.15, 4.8, 0.15], WOOD_DARK)
    b.box([sx - 3.4, 4.4, sz + 2.8], [0.06, 1.0, 1.2], "#c8281e", collide=False)
    _keep(rect(sx - 5.0, sx + 4.0, sz - 4.0, sz + 4.0))
    # the rail pile: new rails on chocks, cover in the open
    for end in (-1, 1):
        b.box([-33.0 + end * 6.0, 0.4, 0.0], [1.0, 0.8, 5.2], rails.SLEEPER)
    for layer in range(3):
        for k in range(5 - layer):
            b.box([-33.0, 0.8 + layer * 0.5 + 0.25, -2.0 + layer * 0.5 + k * 1.0], [15.0, 0.5, 0.6],
                  rails.RAIL, material="metal")
    _keep(rect(-42.0, -24.0, -4.0, 4.0))


def _haystacks(b: ArenaArea, rng: random.Random, land: Land) -> None:
    """Haystacks on the east swell, round-topped, each one somebody's cover,
    and the hay wagon left among them."""
    spots = ((196.0, -36.0), (214.0, -6.0), (204.0, 28.0), (238.0, 70.0), (252.0, -60.0), (222.0, -88.0))
    for x, z in spots:
        if not clear_of(rect(x - 5.0, x + 5.0, z - 5.0, z + 5.0), LANES, 11.0) or _blocked(x, z):
            continue
        y = land.height(x, z)
        b.box([x, y + 1.6, z], [7.0, 3.2, 7.0], "#c8b060")
        b.sphere([x, y + 3.4, z], [8.0, 5.0, 8.0], "#d8c070", collide=False)
        b.box([x, y + 4.0, z], [5.0, 1.6, 5.0], "#d8c070")
        _keep(rect(x - 5.0, x + 5.0, z - 5.0, z + 5.0))


# =================================================================== town
def _town(b: ArenaArea, rng: random.Random) -> None:
    """Front Street between the stations: the Junction Beanery (the eating
    house, a veranda along it), the land office, the Drovers' Hotel with
    its balcony (a perch), the bank, the general store, the church at the
    head of the street with its steeple and bell."""
    s0, s1 = STREET
    b.box([(s0 + s1) / 2.0, 0.03, 0.0], [s1 - s0, 0.06, 220.0], "#8a7458", collide=False)
    # west side: the Beanery and the land office
    bean = rect(254.0, 288.0, -96.0, -36.0)
    storeyed(b, bean, [9.0, 8.0], "#c8b898", roof="#6a3a2a",
             doors={"x+": [(-70.0, -62.0, 8.0)]},
             windows=[{"x+": [(-92.0, -80.0, 3.0, 7.0), (-52.0, -40.0, 3.0, 7.0)]},
                      {"x+": [(-92.0, -82.0, 11.0, 15.0), (-70.0, -62.0, 11.0, 15.0), (-50.0, -40.0, 11.0, 15.0)]}],
             wells=[rect(256.0, 262.0, -94.0, -82.0)])
    flight(b, "z", -80.0, -94.0, 256.0, 262.0, 0.4, 9.0, WOOD, fill=0.0)
    threshold(b, bean, "x+", (-70.0, -62.0))
    gable(b, bean, 18.2, "#6a3a2a", "z", 4, 1.2, 1.0)
    slab(b, rect(288.0, 292.0, -96.0, -36.0), 0.4, 0.4, WOOD_LIGHT)
    for z in (-94.0, -78.0, -52.0, -38.0):
        b.box([291.4, 4.5, z], [0.6, 8.2, 0.6], WOOD_DARK)
    slab(b, rect(287.0, 293.0, -97.0, -35.0), 9.2, 0.4, "#6a3a2a")
    wall_sign(b, 288.36, 7.8, -66.0, 20.0, 2.0,
              sign_decal("JUNCTION BEANERY", "#6a3a2a", rails.CREAM, 9.0), "x+", "#6a3a2a")
    for k in range(4):
        b.box([270.0, 1.4, -88.0 + k * 12.0], [10.0, 0.3, 3.6], WOOD)
        b.box([270.0, 0.7, -88.0 + k * 12.0], [1.0, 1.4, 1.0], WOOD_DARK)
    _keep(rect(bean[0] - 2.0, 294.0, bean[2] - 2.0, bean[3] + 2.0))
    office = rect(258.0, 284.0, 40.0, 80.0)
    rails.false_front(b, office, "x+", "#a8886a", "LAND OFFICE", height=10.0, porch=5.0)
    _keep(rect(office[0] - 2.0, office[1] + 7.0, office[2] - 2.0, office[3] + 2.0))
    # east side: the hotel, the bank, the store
    hotel = rect(312.0, 356.0, -96.0, -30.0)
    storeyed(b, hotel, [9.0, 8.0, 8.0], "#b8a080", roof="#3a3a3e",
             doors={"x-": [(-68.0, -58.0, 8.0)]},
             windows=[{"x-": [(-92.0, -80.0, 3.0, 7.0), (-46.0, -34.0, 3.0, 7.0)]},
                      {"x-": [(-92.0, -84.0, 11.0, 15.0), (-74.0, -66.0, 11.0, 15.0), (-56.0, -48.0, 11.0, 15.0),
                              (-40.0, -32.0, 11.0, 15.0)]},
                      {"x-": [(-92.0, -84.0, 19.0, 23.0), (-74.0, -66.0, 19.0, 23.0), (-56.0, -48.0, 19.0, 23.0),
                              (-40.0, -32.0, 19.0, 23.0)]}],
             wells=[rect(348.0, 354.0, -94.0, -80.0)], parapet=1.6)
    flight(b, "z", -80.0, -94.0, 348.0, 354.0, 0.4, 9.0, WOOD, fill=0.0)
    threshold(b, hotel, "x-", (-68.0, -58.0))
    slab(b, rect(306.0, 312.0, -94.0, -32.0), 9.2, 0.6, WOOD, studs=True)
    flight(b, "z", -112.0, -94.0, 306.0, 312.0, 0.0, 9.2, WOOD, fill=-0.3)
    for z in (-92.0, -74.0, -50.0, -34.0):
        b.box([306.6, 4.3, z], [0.6, 8.6, 0.6], WOOD_DARK)
    b.box([306.3, 10.4, -63.0], [0.3, 1.2, 60.0], WOOD_DARK)
    wall_sign(b, 311.64, 27.4, -63.0, 24.0, 2.6,
              sign_decal("DROVERS' HOTEL", "#3a3a3e", rails.CREAM, 10.0), "x-", "#3a3a3e")
    b.mark("perch", 309.0, 9.2, -63.0)
    _keep(rect(304.0, hotel[1] + 2.0, hotel[2] - 2.0, hotel[3] + 2.0))
    bank = rect(316.0, 346.0, -18.0, 18.0)
    building(b, bank, 0.0, 12.0, "#a89c84", roof_colour="#4a4a4e", doors={"x-": [(-4.0, 4.0, 9.0)]},
             windows={"x-": [(-14.0, -8.0, 3.0, 9.0), (8.0, 14.0, 3.0, 9.0)]}, glass=True, lights=WARM,
             parapet=1.4)
    threshold(b, bank, "x-", (-4.0, 4.0))
    for z in (-6.0, 6.0):
        b.cyl([314.6, 6.0, z], [1.4, 12.0, 1.4], "#d8d0c0")
    wall_sign(b, 315.64, 13.0, 0.0, 14.0, 2.0, sign_decal("STOCKMEN'S BANK", "#4a4a4e", rails.GOLD, 7.0),
              "x-", "#4a4a4e")
    b.box([340.0, 1.6, 0.0], [3.0, 3.2, 3.0], "#3a3a3e", material="metal")
    _keep(rect(312.0, bank[1] + 2.0, bank[2] - 2.0, bank[3] + 2.0))
    store = rect(318.0, 350.0, 26.0, 52.0)
    rails.false_front(b, store, "x-", "#8a6a4a", "GENERAL STORE", height=9.0, porch=5.0,
                      interior=rails.store_interior)
    _keep(rect(310.0, store[1] + 2.0, store[2] - 2.0, store[3] + 2.0))
    # the church at the south end, facing up the street, steeple and bell
    church = rect(314.0, 350.0, 62.0, 90.0)
    building(b, church, 0.0, 12.0, WHITE, roof_colour="#4a4a52", doors={"x-": [(72.0, 80.0, 9.0)]},
             windows={"z-": [(322.0, 328.0, 4.0, 10.0), (336.0, 342.0, 4.0, 10.0)],
                      "z+": [(322.0, 328.0, 4.0, 10.0), (336.0, 342.0, 4.0, 10.0)]}, glass=True, lights=WARM)
    threshold(b, church, "x-", (72.0, 80.0))
    gable(b, church, 13.2, "#4a4a52", "x", 4, 1.4, 0.8)
    b.box([318.0, 20.6, 76.0], [7.0, 14.8, 7.0], WHITE)
    b.box([318.0, 29.0, 76.0], [6.0, 2.0, 6.0], "#4a4a52")
    b.cone([318.0, 34.0, 76.0], [6.0, 8.0, 6.0], "#4a4a52")
    b.box([318.0, 25.5, 72.45], [3.0, 3.0, 0.1], "#1a1a1a", collide=False)
    for k in range(5):
        b.box([326.0 + k * 4.0, 1.0, 70.0], [3.0, 0.5, 1.2], WOOD)
        b.box([326.0 + k * 4.0, 1.0, 82.0], [3.0, 0.5, 1.2], WOOD)
    _keep(rect(church[0] - 2.0, church[1] + 2.0, church[2] - 2.0, church[3] + 2.0))
    # hitching rails and a wagon in the street, lamps along it
    for z in (-24.0, 20.0):
        rails.hitching_post(b, 290.0, z, "z")
    rails.wagon(b, 300.0, -10.0, "z", "#6a3a2a")
    for z in (-100.0, -20.0, 30.0, 100.0):
        lamp_post(b, 294.0 if z < 0 else 306.0, z, 11.0, light=WARM)


def _termini(b: ArenaArea, rng: random.Random) -> None:
    """The two stations at the east end: the freight station on the Swell
    line (lane b), the passenger station on the Bottoms line (lane a); the
    livery barn and the town's water tower behind them."""
    for lane, z, name, roof in (("a", 150.0, "PASSENGER STATION", "#2f4a6a"),
                                ("b", -150.0, "FREIGHT STATION", "#7a3a2a")):
        side = 1.0 if z > 0 else -1.0
        pz = z + side * 15.0
        rails.platform(b, rect(310.0, 380.0, pz - 6.0, pz + 6.0))
        stair(b, "x", 307.0, 310.0, pz - 3.0, pz + 3.0, 0.0, 1.2, WOOD)
        rails.shelter(b, rect(318.0, 372.0, pz - 3.4, pz + 3.4), 1.2, 9.0, roof)
        b.box([345.0, 1.2 + 9.6 + 1.2, pz], [44.0, 2.4, 0.5], rails.GOLD,
              decal=sign_decal("THUNDER JCT. " + name, rails.GOLD, "#3a2414", 18.0))
        buffer_stop(b, 372.0, z, math.pi / 2.0, roof)
        house = rect(326.0, 378.0, pz + side * 8.0, pz + side * 28.0)
        building(b, house, 0.0, 12.0, DEPOT_YELLOW, roof_colour=DEPOT_TRIM,
                 doors={"x-": [(min(house[2], house[3]) + 6.0, max(house[2], house[3]) - 6.0, 9.0)]},
                 windows={"z-" if side > 0 else "z+": [(330.0, 344.0, 4.0, 9.0), (356.0, 370.0, 4.0, 9.0)]},
                 glass=True, lights=WARM)
        threshold(b, house, "x-", (min(house[2], house[3]) + 6.0, max(house[2], house[3]) - 6.0))
        gable(b, house, 13.2, DEPOT_TRIM, "x", 4, 1.3, 0.8)
        b.mark("finish", 362.0, 0.5, z, lane=lane)
        _keep(rect(304.0, 382.0, min(pz - 8.0, house[2]) - 2.0, max(pz + 8.0, house[3]) + 2.0))
    # the freight station's dock: crates, a wagon backed up to it
    for k in range(3):
        crate_stack(b, 300.0 - k * 9.0, -186.0, random.Random(k + 70))
    rails.wagon(b, 290.0, -200.0, "x", "#5a3a2a")
    _keep(rect(278.0, 306.0, -206.0, -180.0))
    # the livery barn, its hay loft open (a perch)
    barn = rect(236.0, 268.0, -226.0, -196.0)
    building(b, barn, 0.0, 9.0, "#8a2a22", roof_colour="#4a3a2e", doors={"z+": [(248.0, 260.0, 8.0)]})
    gable(b, barn, 10.2, "#4a3a2e", "x", 4, 1.6, 0.8)
    slab(b, rect(238.0, 266.0, -224.0, -212.0), 6.0, 0.6, WOOD_LIGHT, studs=True)
    flight(b, "z", -200.0, -212.0, 240.0, 245.0, 0.0, 6.0, WOOD, fill=-0.3)
    for k in range(4):
        b.box([250.0 + k * 3.6, 7.2, -220.0], [3.0, 2.4, 3.0], "#d8c070")
    b.mark("perch", 256.0, 6.0, -218.0)
    _keep(rect(barn[0] - 2.0, barn[1] + 2.0, barn[2] - 2.0, barn[3] + 6.0))
    # the town's water tower
    rails.water_tower(b, 300.0, 204.0, "#7a5335", height=18.0)
    _keep(rect(288.0, 324.0, 192.0, 216.0))


# ============================================================ furniture
def _depots(b: ArenaArea) -> None:
    for lane, f, side, name, stage, roof in DEPOTS:
        path = LANE_A if lane == "a" else LANE_B
        depot(b, lane, path, f, side, name, stage, roof, base=BASES[(lane, f)])
        entry = b.points["depot"][-1]
        ox, oz = entry["p"][0] - b.ox, entry["p"][2] - b.oz
        _keep(rect(ox - 22.0, ox + 22.0, oz - 10.0, oz + 10.0))


def _levers(b: ArenaArea, land: Land) -> None:
    for lane, path, sides in (("a", LANE_A, (-1.0, 1.0)), ("b", LANE_B, (1.0, -1.0))):
        for index, (f, side) in enumerate(zip(rails.LEVER_FRACTIONS, sides)):
            total = rails.length(path)
            x, z, _yaw = beside(path, total * f, side * 6.5)
            base = land.height(x, z)
            level = all(abs(land.height(x + dx, z + dz) - base) < 1e-6
                        for dx in (-2.6, 2.6) for dz in (-2.6, 2.6))
            lever(b, lane, path, f, side, index, base=base, plate=level)
            _keep(rect(x - 4.0, x + 4.0, z - 4.0, z + 4.0))


def _coal(b: ArenaArea, rng: random.Random) -> None:
    for x, z in COAL:
        coal_heap(b, x, z, rng, base=BASES[("coal", x, z)])
        _keep(rect(x - 5.0, x + 5.0, z - 5.0, z + 5.0))


def _scatter(b: ArenaArea, rng: random.Random, land: Land) -> None:
    """Prairie clutter on the swells: tufts, stones, buffalo bones, a few
    lone trees -- never on a line, in a yard or at a building."""
    tries = placed = 0
    hx, hz = HALF
    while placed < 110 and tries < 1600:
        tries += 1
        x, z = rng.uniform(-hx + 10.0, hx - 10.0), rng.uniform(-hz + 14.0, hz - 14.0)
        if abs(x - MAIN_X) < 16.0 or abs(z) > 200.0:
            continue
        if not rails.clear_of(rect(x - 4.0, x + 4.0, z - 4.0, z + 4.0), LANES, 12.0):
            continue
        if _blocked(x, z) or any(k[0] - 6 < x < k[1] + 6 and k[2] - 6 < z < k[3] + 6 for k in KEEP):
            continue
        base = land.height(x, z)
        if abs(land.height(x + 3.0, z) - base) > 0.6 or abs(land.height(x, z + 3.0) - base) > 0.6:
            continue
        roll = rng.random()
        if roll < 0.55:
            for k in range(3):
                b.cone([x + (k - 1) * 0.9, base + 0.7, z + (k % 2) * 0.7], [1.2, 1.4, 1.2],
                       rng.choice(["#a89a58", "#8a9a50", "#b8a868"]), collide=False)
        elif roll < 0.8:
            outcrop(b, x, z, rng.uniform(2.0, 4.0), rng.uniform(1.0, 1.8), rng.uniform(2.0, 3.6),
                    base=base, colour=rng.choice([STONE, STONE_DARK, "#9a8a70"]))
        elif roll < 0.92:
            _cottonwood(b, x, z, base, rng, s=rng.uniform(0.7, 1.0))
        else:
            # a buffalo skull bleaching in the grass
            b.box([x, base + 0.5, z], [1.6, 1.0, 2.0], "#e8e0cc")
            for side in (-1, 1):
                b.box([x + side * 1.1, base + 1.2, z + 0.2], [0.8, 0.3, 0.3], "#d8d0bc", collide=False,
                      r=[0.0, 0.0, side * 0.5])
        KEEP.append(rect(x - 3.0, x + 3.0, z - 3.0, z + 3.0))
        placed += 1


# =================================================================== rigs
def _rigs(b: ArenaArea) -> None:
    """What moves: the storm (rain, lightning, a strike on the tall
    elevator's rod now and then), a twister walking the horizon, the
    windpump, the vane on the depot, the washing, tumbleweeds, smoke from
    the engine house and the sod house, the order board and the sounder."""
    tall = ELEVATORS[2]
    rod = [(tall[0] + tall[1]) / 2.0, 46.0 + 8.0 + 4.8 + 8.2, (tall[2] + tall[3]) / 2.0]
    b.rig("rr_weather", 0.0, 0.0, 0.0, weather="storm", wind=[0.8, 0.35],
          rods=[b.at(*rod), b.at(26.0, 36.4, -70.0)])
    b.rig("rr_twister", 560.0, 0.0, -400.0, q=[380.0, 0.0, -540.0], h=170.0, s=1.2, seed=1.7)
    b.rig("rr_windpump", PUMP[0], 2.0 + 19.4, PUMP[1], yaw=WIND_YAW, r=4.6)
    b.rig("rr_vane", -25.0, 1.2 + 15.0 + 1.2 + 4.8 + 0.2, -84.0, s=1.4, yaw=WIND_YAW)
    b.rig("rr_vane", 318.0, 38.0, 76.0, s=1.6, yaw=WIND_YAW)
    b.rig("rr_clothesline", SOD[0] + 22.0, 2.0 + 5.8, SOD[1] + 14.0, w=16.0)
    for k, (a, c) in enumerate((((-140.0, 2.0, -40.0), (-60.0, 0.0, -10.0)),
                                (((-120.0, 2.0, 40.0)), (-20.0, 0.0, 30.0)),
                                ((60.0, 0.0, -30.0), (200.0, 4.0, -20.0)),
                                ((150.0, 4.0, 60.0), (250.0, 0.0, 40.0)))):
        b.rig("rr_tumbleweed", a[0], a[1], a[2], q=list(c), speed=9.0 + k, seed=k * 1.3)
    for z in STALLS[1::2]:
        b.rig("rr_smoke", -330.0, 23.2, z, wind=[0.8, 0.35], rate=0.18, h=26.0, colour="#5a5856")
    b.rig("rr_smoke", SOD[0] - 5.0, 2.0 + 10.4, SOD[1] + 2.0, wind=[0.8, 0.35], rate=0.3, h=14.0,
          size=1.0, colour="#9a948c")
    b.rig("rr_smoke", 36.0, 13.6, -104.0, wind=[0.8, 0.35], rate=0.3, h=14.0, size=1.0, colour="#9a948c")
    b.rig("rr_order_board", -8.2, 1.2 + 13.0, -84.0, yaw=math.pi / 2.0)
    b.rig("rr_sounder", -11.2, 1.2 + 2.3, -83.0, yaw=math.pi / 2.0, call="TJ")
    b.rig("rr_flag", -8.2, 1.2 + 13.8, -58.0, w=4.0, h=2.4, yaw=WIND_YAW,
          colours=["#c8281e", WHITE, "#2f4a8a"])
