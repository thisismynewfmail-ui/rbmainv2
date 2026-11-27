"""Union Terminal -- the city's great station at dusk, and the race into it.

Layout (north is -z; both tracks run west to east)::

    z -240 ~~~~~~~~~~~~~~~~~~~~~~ THE UNION CANAL ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
           NORTH YARD  ---\\  M  [ UPPER TOWN, six up: GRAND HOTEL ]  | TRAIN SHED |
           (lane a start)  \\ A  [ PLAZA (fountain, statue) EXCHANGE]  | platforms  | CON-
    z    0 FREIGHT HOUSE    \\R  UNION TOWER  ====== THE THROAT ====| coaches    | COURSE
           SOUTH YARD  -----K/        (signal gantries)       \\----| (both lines|
           (lane b start)   E  [ GASWORKS HILL, four up: STORAGE, ]  |  end here) |
    z +240 ~~~~~~~~~~~~~~~~~T~~[ the gasholder, the retort house  ]~~~~~~~~~~~~~~

Both companies start in the freight yards at the west end, cross a
streetcar street, meet at the Grand Diamond under Union Tower, run the
throat under its signal gantries and race into the train shed -- lane a to
the south platforms, lane b to the north -- where the buffer stops face the
concourse.

The city stands on two levels.  The lines run low through the middle;
Upper Town sits six up on its retaining wall to the north (a grand stair
down from the plaza, side stairs at both ends), Gasworks Hill four up to
the south, and the canal below the quays.  Whoever holds the terraces
looks straight down on the race.

The twist is Dustbowl Gulch's: the signal.  Hold the cabin on top of Union
Tower, with nobody of theirs in it, and the junction signal is set against
the other company -- their cart stops short of the diamond.
"""
from __future__ import annotations

import math
import random

from ...lastlight.kit import lamp_post
from ..kit import (WARM, WOOD, WOOD_DARK, WOOD_LIGHT, ArenaArea, Surfaces, backdrop, building,
                   flight, gable, ground, lantern, rect, room_walls, sign_decal, slab, threshold,
                   wall_sign)
from . import rails
from .land import Land
from .rails import (boxcar, buffer_stop, clear_of, coal_heap, crate_stack, depot, fillet, flatcar,
                    lay_track, lever, mirror, stair, storeyed, telegraph)
from .scenery import coach, outcrop, stub_track

HALF = (400.0, 240.0)
SKY = {"top": "#1a2448", "horizon": "#e8865a", "sun": [0.72, 0.12, -0.5],
       "clouds": 0.4, "tint": "#ffb88a"}
AMBIENT = "#8a7f92"
GROUND = "#5a5652"
FOG = 900.0

COBBLE = "#5a5652"
COBBLE_DARK = "#4a4642"
PAVING = "#8a8478"
BRICK = "#8a3a2a"
BRICK_DARK = "#6a2a20"
STONE = "#c8bca4"
STONE_DARK = "#a89c84"
IRONWORK = "#3a4048"
GREEN = "#2f4a3a"

LANE_A = fillet([(-372.0, -150.0), (-210.0, -150.0), (0.0, 0.0), (210.0, 150.0), (340.0, 150.0)],
                radius=80.0, step=5.0)
LANE_B = mirror(LANE_A)
LANES = (LANE_A, LANE_B)

CANAL = rect(-392.0, 236.0, -236.0, -214.0)
CANAL_Y = -5.0
SHED = rect(228.0, 400.0, -206.0, 206.0)
PLATFORMS = ((108.0, 132.0), (48.0, 72.0), (-12.0, 12.0), (-72.0, -48.0), (-132.0, -108.0),
             (170.0, 200.0), (-200.0, -170.0))
COACH_TRACKS = (90.0, 30.0, -30.0, -90.0)
TOWER = (-46.0, 0.0)
STREET_X = -170.0
UPPER = rect(-110.0, 120.0, -210.0, -100.0)       # Upper Town, six up (a towpath below it)
UPPER_Y = 6.0
HILL = rect(-150.0, 110.0, 165.0, 236.0)          # Gasworks Hill, four up
HILL_Y = 4.0
PLAZA = rect(-36.0, 36.0, -206.0, -112.0)
HEAPS = ((-262.0, -42.0), (-262.0, 42.0))          # ballast stockpiles in the yards

KEEP: list = []


def build(b: ArenaArea) -> None:
    rng = random.Random(0x0710)
    del KEEP[:]
    b.extra.update({"accent": "#ffb35a", "twist": "signal",
                    "lanes": {"a": _world(b, LANE_A), "b": _world(b, LANE_B)},
                    "names": {"a": "the South Platforms line", "b": "the North Platforms line"}})
    ground(b, COBBLE, soil="#3a3632", holes=[CANAL])
    _land().build(b, COBBLE_DARK)
    _edge(b, rng)
    s = Surfaces(b)
    for path in LANES:
        lay_track(b, path)
    _yards(b, rng)
    _freight_house(b)
    _canal(b, rng)
    _street(b, s, rng)
    _tower(b)
    _throat(b)
    _terrace_ways(b)
    _plaza(b, rng)
    _hotel(b)
    _exchange(b)
    _gasworks(b, rng)
    _storage(b, rng)
    _market(b, rng)
    _footbridge(b)
    _shed(b, rng)
    _concourse(b)
    _depots(b)
    _levers(b)
    _coal(b, rng)
    _lamps(b)
    telegraph(b, LANE_A, -1.0, skip=_blocked)
    telegraph(b, LANE_B, 1.0, skip=_blocked)
    for x, z, name in ((-345, -150, "the North Yard"), (-345, 150, "the South Yard"),
                       (-352, 0, "the freight house"), (-120, -226, "the Union Canal"),
                       (STREET_X, 0, "Market Street"), (TOWER[0], 0, "Union Tower"),
                       (0, 0, "the Grand Diamond"), (100, 0, "the throat"),
                       (0, -160, "the fountain"), (0, -128, "the Baron's statue"),
                       (-76, -180, "the Grand Hotel"), (86, -180, "the Exchange"),
                       (0, -94, "the grand stair"), (5, -140, "Upper Town"),
                       (10, 198, "the gasholder"), (78, 196, "the retort house"),
                       (-102, 203, "Union Storage"), (-20, 172, "Gasworks Hill"),
                       (-262, 0, "the ballast heaps"), (222, 0, "the footbridge"),
                       (0, 110, "the covered market"), (61, 112, "the cab rank"),
                       (290, 0, "the train shed"), (372, 0, "the concourse clock"),
                       (290, 150, "the south platforms"), (290, -150, "the north platforms"),
                       (STREET_X, -40, "the stalled streetcar")):
        b.landmark(float(x), float(z), name)
    b.camera(-260.0, 60.0, -40.0, 0.0, 0.0, 0.0)
    b.camera(150.0, 40.0, -120.0, 290.0, 6.0, 0.0)
    b.camera(0.0, 70.0, 200.0, 0.0, 0.0, 0.0)


def _land() -> Land:
    """The two terraces (their edges a band of brick: the retaining walls),
    the ballast heaps in the yards, everything else at street level -- and
    the lines' corridors held down to the rails."""
    hx, hz = HALF
    land = Land(rect(-hx, hx, -hz, hz), cell=5.0, step=1.0)

    def shape(x: float, z: float) -> float:
        if UPPER[0] <= x <= UPPER[1] and UPPER[2] <= z <= UPPER[3]:
            return UPPER_Y
        if HILL[0] <= x <= HILL[1] and HILL[2] <= z <= HILL[3]:
            return HILL_Y
        h = 0.0
        for hx0, hz0 in HEAPS:
            d = math.hypot(x - hx0, z - hz0)
            h = max(h, 4.5 * max(0.0, 1.0 - d / 16.0))
        return h

    land.add(shape)
    land.cut(CANAL)
    for path in LANES:
        land.pin_path(path, [0.0] * len(path), half=7.5, blend=6.0)

    def paint(x: float, z: float, h: float):
        for area in (UPPER, HILL):
            if area[0] <= x <= area[1] and area[2] <= z <= area[3]:
                edge = min(x - area[0], area[1] - x, area[3] - z if area is UPPER else z - area[2])
                if edge < 5.0:
                    return BRICK if area is UPPER else BRICK_DARK
                if area is UPPER:
                    return PAVING if PLAZA[0] <= x <= PLAZA[1] and PLAZA[2] <= z <= PLAZA[3] \
                        else "#6a6660"
                return "#4a4440"
        return "#7a7468" if h > 0.5 else None

    land.colour(paint)
    return land


def _world(b: ArenaArea, path):
    return [b.at(x, 0.0, z) for x, z in path]


def _keep(area) -> None:
    KEEP.append(area)


def _blocked(x: float, z: float) -> bool:
    if x > SHED[0] - 12.0 or CANAL[2] - 4 < z < CANAL[3] + 4:
        return True
    if abs(x - STREET_X) < 12.0:
        return True
    return any(k[0] - 2 < x < k[1] + 2 and k[2] - 2 < z < k[3] + 2 for k in KEEP)


# ==================================================================== edge
def _edge(b: ArenaArea, rng: random.Random) -> None:
    hx, hz, m = b.half_x, b.half_z, b.margin
    room_walls(b, rect(-hx - m, hx + m, -hz - m, hz + m), m, 0.0, 30.0, BRICK_DARK)
    # the city past the walls: the rooflines of the blocks behind
    for side in (-1, 1):
        for i in range(26):
            x = -hx + (i + 0.5) * (2 * hx) / 26.0
            top = rng.uniform(6.0, 26.0)
            b.box([x, 30.0 + top / 2.0, side * (hz + m / 2.0)], [2 * hx / 26.0 - 0.8, top, m + 1.0],
                  rng.choice([BRICK_DARK, "#5a4a4a", "#4a4a52"]), collide=False)
    backdrop(b, "city", 0.0, rng, ["#3a3a4a", "#4a4050", "#2e3040", "#504858"], depth=160.0)
    # the streets the backdrop's blocks stand in
    out = 220.0
    for x, z, w, d in ((0.0, -(hz + m + out / 2.0), 2 * (hx + m + out), out),
                       (0.0, hz + m + out / 2.0, 2 * (hx + m + out), out),
                       (-(hx + m + out / 2.0), 0.0, out, 2 * (hz + m)),
                       (hx + m + out / 2.0, 0.0, out, 2 * (hz + m))):
        b.box([x, -2.5, z], [w, 2.0, d], "#2a2a2e", collide=False)


# ================================================================= yards
def _yards(b: ArenaArea, rng: random.Random) -> None:
    """The freight yards the companies start from: a platform each, the
    sidings full of cars behind, a crane."""
    for lane, z, name, roof in (("a", -150.0, "NORTH YARD", "#7a2a20"),
                                ("b", 150.0, "SOUTH YARD", "#2a3a5a")):
        side = -1.0 if z < 0 else 1.0
        pz = z + side * 15.0
        rails.platform(b, rect(-376.0, -322.0, pz - 6.0, pz + 6.0))
        stair(b, "x", -319.0, -322.0, pz - 3.0, pz + 3.0, 0.0, 1.2, WOOD)
        rails.shelter(b, rect(-370.0, -334.0, pz - 3.4, pz + 3.4), 1.2, 9.0, roof, post=IRONWORK)
        b.box([-352.0, 1.2 + 9.6 + 1.2, pz], [30.0, 2.4, 0.5], rails.CREAM,
              decal=sign_decal(name, rails.CREAM, "#2a2a30", 12.5))
        for sx in (-373.0, -362.0, -354.0, -346.0, -338.0, -327.0):
            for w in (-1.4, 1.4):
                b.team_spawn(lane, sx, 1.51, pz + w, math.pi / 2.0, 0)
        buffer_stop(b, -372.0, z, math.pi / 2.0, roof)
        lantern(b, -326.0, 9.8, pz, WARM)
        b.mark("start", -362.0, 0.5, z, lane=lane)
        _keep(rect(-380.0, -318.0, pz - 8.0, pz + 8.0))
        # the siding behind the platform, a string of cars on it
        sz = pz + side * 22.0
        stub_track(b, -390.0, -250.0, sz)
        boxcar(b, -370.0, sz, "x", "#7a2a20" if lane == "a" else "#3a4a5a",
               "UNION FREIGHT" if lane == "a" else "CITY & WESTERN")
        flatcar(b, -344.0, sz, "x", "crates", rng)
        boxcar(b, -318.0, sz, "x", "#5a3a2a", "", door="shut")
        rails.caboose(b, -292.0, sz, "x", "#8a2a1c" if lane == "a" else "#2a4a6a")
        _keep(rect(-392.0, -248.0, sz - 5.0, sz + 5.0))
        # a yard crane by the siding
        cx, cz = -262.0, sz + side * 10.0
        b.box([cx, 6.0, cz], [3.0, 12.0, 3.0], IRONWORK, material="metal")
        b.box([cx + 6.0, 12.6, cz], [16.0, 1.2, 1.4], IRONWORK, material="metal")
        b.box([cx + 13.0, 9.0, cz], [0.2, 6.0, 0.2], "#8a8680", collide=False, material="metal")
        b.box([cx + 13.0, 5.6, cz], [2.0, 1.0, 2.0], "#c8a03a", material="metal", collide=False)
        _keep(rect(cx - 3.0, cx + 15.0, cz - 3.0, cz + 3.0))


def _freight_house(b: ArenaArea) -> None:
    """The long brick freight house between the yards: it keeps the starts
    out of each other's sights, and its loft looks over both."""
    shed = rect(-386.0, -318.0, -62.0, 62.0)
    building(b, shed, 0.0, 16.0, BRICK, roof_colour="#3a3a40",
             doors={"x+": [(-28.0, -14.0, 11.0), (14.0, 28.0, 11.0)]},
             windows={"z-": [(-372.0, -352.0, 7.0, 11.0)], "z+": [(-372.0, -352.0, 7.0, 11.0)],
                      "x+": [(-50.0, -38.0, 7.0, 11.0), (38.0, 50.0, 7.0, 11.0)]},
             glass=True, lights=WARM)
    gable(b, shed, 17.2, "#3a3a40", "z", 5, 1.5, 1.0)
    threshold(b, shed, "x+", (-28.0, -14.0))
    threshold(b, shed, "x+", (14.0, 28.0))
    for k in range(4):
        crate_stack(b, -372.0 + (k % 2) * 18.0, -36.0 + k * 22.0, random.Random(k + 40))
    # the loft along the back wall, a stair up to it
    slab(b, rect(-384.0, -370.0, -60.0, 60.0), 8.0, 0.6, WOOD_LIGHT, studs=True)
    flight(b, "z", -30.0, -46.0, -370.0, -362.0, 0.0, 8.0, WOOD, fill=-0.3)
    b.mark("perch", -377.0, 8.0, 0.0)
    wall_sign(b, -317.65, 13.0, 0.0, 36.0, 3.6,
              sign_decal("UNION FREIGHT HOUSE", BRICK_DARK, rails.CREAM, 10.0), "x+", BRICK_DARK)
    _keep(rect(-390.0, -314.0, -66.0, 66.0))


# ================================================================== canal
def _canal(b: ArenaArea, rng: random.Random) -> None:
    """The Union Canal along the north wall: brick quays, the water low,
    two barges tied up, steps down at three places."""
    x0, x1, z0, z1 = CANAL
    slab(b, CANAL, CANAL_Y, 0.6, "#3a3a38", studs=True)
    b.water((x0 + x1) / 2.0, (z0 + z1) / 2.0, x1 - x0, z1 - z0, -2.6, "#2a3a42")
    for x in (-300.0, -20.0, 180.0):
        flight(b, "z", z0 + 9.0, z1, x - 3.0, x + 3.0, CANAL_Y, 0.0, STONE_DARK, fill=CANAL_Y - 0.3)
    for k, (x, load) in enumerate(((-200.0, "coal"), (80.0, "crates"))):
        bz = z0 + 6.0
        b.box([x, -2.4, bz], [26.0, 2.4, 7.0], "#4a3a2a")
        b.box([x, -1.0, bz], [26.4, 0.4, 7.4], "#2a2420")
        if load == "coal":
            b.box([x, -0.4, bz], [20.0, 0.8, 5.0], rails.COAL, studs=True)
        else:
            for c in range(3):
                b.box([x - 8.0 + c * 8.0, 0.8, bz], [5.0, 3.2, 5.0], WOOD)
        b.box([x + 11.5, 0.2, bz], [2.0, 1.6, 6.0], WOOD_DARK)
        # the mooring rope to a bollard on the quay
        b.cyl([x - 10.0, 0.6, z1 + 1.4], [0.8, 1.2, 0.8], IRONWORK, material="metal")
    _keep(rect(x0, x1, z0 - 2.0, z1 + 4.0))


# ================================================================= street
def _street(b: ArenaArea, s: Surfaces, rng: random.Random) -> None:
    """Market Street, north to south across both lines: cobbles, the tram
    rails let into them, the overhead wire on its poles, the crossing gates
    -- and a streetcar stalled between the lines."""
    x0, x1 = STREET_X - 8.0, STREET_X + 8.0
    s.lay(rect(x0, x1, CANAL[3] + 2.0, 236.0), 0.3, COBBLE_DARK, studs=True)
    for dx in (-3.4, 3.4):
        for rz in (-0.75, 0.75):
            b.box([STREET_X + dx + rz, 0.34, 11.0], [0.3, 0.08, 236.0 - CANAL[3] - 2.0 - 4.0],
                  "#8c8a86", collide=False, material="metal")
    cross = 150.0 / 210.0 * abs(STREET_X)
    for z in range(int(CANAL[3]) + 12, 230, 36):
        if any(abs(z - c) < 14 for c in (-cross, cross)):
            continue
        b.cyl([x1 + 1.2, 7.0, float(z)], [0.6, 14.0, 0.6], IRONWORK, material="metal")
        arm0, arm1 = STREET_X - 7.0, x1 + 1.2
        b.box([(arm0 + arm1) / 2.0, 13.6, float(z)], [arm1 - arm0, 0.3, 0.3], IRONWORK, collide=False,
              material="metal")
    b.box([STREET_X - 3.4, 13.41, 11.0], [0.08, 0.08, 236.0 - CANAL[3] - 2.0], "#2a2a2a", collide=False)
    # the streetcar, stalled, its pole off the wire
    tz = -40.0
    b.box([STREET_X - 3.4, 1.6, tz], [5.6, 2.2, 18.0], "#2a2826", material="metal")
    b.box([STREET_X - 3.4, 5.0, tz], [6.0, 4.8, 17.0], "#d8c890")
    b.box([STREET_X - 3.4, 3.5, tz], [6.1, 0.6, 17.1], GREEN)
    b.box([STREET_X - 3.4, 7.7, tz], [6.4, 0.6, 18.0], "#3a3a3a", material="metal")
    for side in (-1, 1):
        for k in range(5):
            b.box([STREET_X - 3.4 + side * 3.03, 5.6, tz - 6.4 + k * 3.2], [0.06, 1.6, 2.4],
                  "#ffe0a0", material="neon", collide=False)
    b.box([STREET_X - 3.4, 9.6, tz + 4.0], [0.16, 0.16, 7.0], "#2a2a2a", collide=False,
          r=[0.6, 0.0, 0.0])
    b.box([STREET_X - 3.4, 6.0, tz + 8.56], [3.6, 2.0, 0.06], "#1a1a1a", collide=False,
          decal=sign_decal("12 UNION STN", "#1a1a1a", "#ffd27a", 1.8))
    _keep(rect(x0 - 2.0, x1 + 2.0, tz - 10.0, tz + 10.0))
    # crossing gates where the street crosses each line
    for zc in (-cross, cross):
        for side in (-1, 1):
            gx, gz = STREET_X + side * 10.5, zc - side * 12.0
            b.box([gx, 2.0, gz], [0.8, 4.0, 0.8], rails.CREAM)
            b.box([gx, 3.6, gz + side * 4.0], [0.3, 0.3, 8.0], "#d8282a", collide=False)
            b.box([gx, 4.6, gz], [1.4, 0.8, 0.5], "#2a2a2a")


# ================================================================= tower
def _tower(b: ArenaArea) -> None:
    """Union Tower: the interlocking at the Grand Diamond, brick below and
    the signal cabin on top (the twist's cabin), a stair up the outside."""
    tx, tz = TOWER
    base = rect(tx - 8.0, tx + 8.0, tz - 8.0, tz + 8.0)
    building(b, base, 0.0, 12.0, BRICK, roof_colour="#3a3a40", floor_colour="#6a5a4a",
             doors={"x-": [(-3.0, 3.0, 8.5)]},
             windows={"z-": [(tx - 5.0, tx + 5.0, 4.0, 8.0)], "z+": [(tx - 5.0, tx + 5.0, 4.0, 8.0)],
                      "x+": [(-5.0, 5.0, 4.0, 8.0)]}, glass=True, lights=WARM)
    threshold(b, base, "x-", (-3.0, 3.0))
    building(b, rect(tx - 5.0, tx + 5.0, tz - 5.0, tz + 5.0), 13.2, 9.0, "#c8b898",
             roof_colour="#3a3a40", floor_colour="",
             doors={"z+": [(tx - 2.5, tx + 2.5, 13.2 + 7.0)]},
             windows={"z-": [(tx - 3.5, tx + 3.5, 16.0, 20.0)],
                      "x+": [(-3.5, 3.5, 16.0, 20.0)], "x-": [(-3.5, 3.5, 16.0, 20.0)]},
             glass=True, lights=WARM, studs_roof=True)
    stair(b, "z", tz + 24.0, tz + 8.0, tx - 12.0, tx - 8.0, 0.0, 13.2, "#6a6a70")
    slab(b, rect(tx - 12.0, tx - 8.0, tz + 4.0, tz + 8.0), 13.2, 1.2, "#6a6a70")
    b.mark("perch", tx, 13.2, tz + 6.5)
    b.mark("signal", tx, 13.2, tz, r=4.4, top=22.2)
    for k, colour in enumerate(("#ff3a2a", "#3aff6a")):
        b.box([tx + 5.2, 20.6 + k * 1.0, tz], [0.4, 1.0, 1.0], colour, material="neon", collide=False)
    wall_sign(b, tx, 10.0, tz - 8.35, 12.0, 2.0,
              sign_decal("UNION TOWER", rails.CREAM, "#2a2a30", 6.0), "z-", rails.CREAM)
    _keep(rect(tx - 13.0, tx + 9.0, tz - 9.0, tz + 25.0))


def _throat(b: ArenaArea) -> None:
    """The throat east of the diamond: two signal gantries spanning both
    lines, a semaphore over each track, the relay huts between."""
    for gx in (64.0, 140.0):
        zl = 150.0 / 210.0 * gx
        posts = (-(zl + 16.0), 0.0, zl + 16.0)
        for pz in posts:
            b.box([gx, 8.5, pz], [1.4, 17.0, 1.4], IRONWORK, material="metal")
        b.box([gx, 17.6, 0.0], [1.6, 1.2, 2.0 * (zl + 16.0) + 1.4], IRONWORK, material="metal")
        for side in (-1, 1):
            sz = side * zl
            b.box([gx, 19.4, sz], [0.4, 2.4, 0.4], IRONWORK, material="metal")
            b.box([gx + 0.3, 20.2, sz + 1.4], [0.1, 0.5, 2.6], "#d8282a", collide=False,
                  r=[0.5 if side > 0 else -0.5, 0.0, 0.0])
            b.box([gx, 19.4, sz - 0.45], [0.5, 0.5, 0.5], "#3aff6a", material="neon", collide=False)
        # the relay hut by the middle post
        b.box([gx + 6.0, 2.0, 0.0], [5.0, 4.0, 4.0], "#6a6a70", material="metal")
        b.box([gx + 6.0, 4.3, 0.0], [5.6, 0.6, 4.6], "#3a3a40")
        _keep(rect(gx - 2.0, gx + 9.0, -3.0, 3.0))
        for pz in posts:
            _keep(rect(gx - 2.0, gx + 2.0, pz - 2.0, pz + 2.0))


# ============================================================== terraces
def _terrace_ways(b: ArenaArea) -> None:
    """The ways up: Upper Town's grand stair down from the plaza toward the
    diamond, a stair at each end of its wall; two broad stairs up Gasworks
    Hill; lamps at the tops."""
    y = UPPER_Y
    flight(b, "z", UPPER[3] + 14.0, UPPER[3], -20.0, 20.0, 0.0, y, STONE, fill=-0.3)
    for x in (-24.0, 24.0):
        b.box([x, 1.6, UPPER[3] + 7.0], [4.0, 3.2, 14.0], STONE_DARK)
        b.box([x, 3.4, UPPER[3] + 7.0], [4.4, 0.4, 14.4], STONE)
    flight(b, "x", UPPER[0] - 14.0, UPPER[0], -140.0, -128.0, 0.0, y, STONE, fill=-0.3)
    flight(b, "x", UPPER[1] + 14.0, UPPER[1], -140.0, -128.0, 0.0, y, STONE, fill=-0.3)
    for x0, x1 in ((-42.0, -26.0), (60.0, 76.0)):
        flight(b, "z", HILL[2] - 10.0, HILL[2], x0, x1, 0.0, HILL_Y, "#6a6260", fill=-0.3)
    _keep(rect(-26.0, 26.0, UPPER[3], UPPER[3] + 15.0))
    _keep(rect(UPPER[0] - 15.0, UPPER[0], -141.0, -127.0))
    _keep(rect(UPPER[1], UPPER[1] + 15.0, -141.0, -127.0))
    for x0, x1 in ((-42.0, -26.0), (60.0, 76.0)):
        _keep(rect(x0 - 1.0, x1 + 1.0, HILL[2] - 11.0, HILL[2]))
    # iron railings along the top of Upper Town's wall, gaps at the stairs
    z = UPPER[3] - 0.4
    for a, c in ((UPPER[0], -20.0), (20.0, UPPER[1])):
        span = c - a
        if span <= 1.0:
            continue
        b.box([(a + c) / 2.0, y + 1.5, z], [span, 0.3, 0.3], IRONWORK, material="metal")
        for k in range(int(span // 6.0) + 1):
            px = a + 0.3 + k * (span - 0.6) / max(1, int(span // 6.0))
            b.box([px, y + 0.75, z], [0.3, 1.5, 0.3], IRONWORK, material="metal")


# ================================================================== plaza
def _plaza(b: ArenaArea, rng: random.Random) -> None:
    """Union Plaza on Upper Town: the fountain, the Baron on his pedestal,
    benches and flower beds -- and the drop to the diamond below."""
    area = PLAZA
    y0 = UPPER_Y
    # the fountain: a round basin, a column, two tiers and the water
    fx, fz = 0.0, -162.0
    b.cyl([fx, y0 + 0.7, fz], [18.0, 1.4, 18.0], STONE)
    b.cyl([fx, y0 + 1.42, fz], [16.4, 0.06, 16.4], "#4a8aa8", material="glass", alpha=0.8, collide=False)
    b.cyl([fx, y0 + 3.2, fz], [2.4, 4.6, 2.4], STONE_DARK)
    b.cyl([fx, y0 + 5.6, fz], [8.0, 0.6, 8.0], STONE)
    b.cyl([fx, y0 + 7.4, fz], [1.2, 3.0, 1.2], STONE_DARK)
    b.cyl([fx, y0 + 9.0, fz], [4.0, 0.4, 4.0], STONE)
    b.sphere([fx, y0 + 10.0, fz], [1.6, 2.0, 1.6], "#9ad8f0", alpha=0.6, collide=False)
    _keep(rect(fx - 10.0, fx + 10.0, fz - 10.0, fz + 10.0))
    # the railroad baron in bronze, top hat and all, pointing down the line
    sx, sz = 0.0, -128.0
    b.box([sx, y0 + 2.0, sz], [5.0, 4.0, 5.0], STONE)
    b.box([sx, y0 + 4.3, sz], [5.6, 0.6, 5.6], STONE_DARK)
    bronze = "#6a5a3a"
    b.box([sx, y0 + 6.4, sz], [2.2, 3.6, 1.4], bronze, material="metal")
    b.box([sx, y0 + 9.0, sz], [1.4, 1.6, 1.4], bronze, material="metal")
    b.box([sx, y0 + 10.4, sz], [1.2, 1.2, 1.2], bronze, material="metal")
    b.box([sx, y0 + 9.85, sz], [2.0, 0.12, 2.0], bronze, material="metal", collide=False)
    b.box([sx + 1.6, y0 + 8.0, sz + 0.8], [0.5, 0.5, 2.6], bronze, material="metal", collide=False,
          r=[0.3, 0.4, 0.0])
    wall_sign(b, sx, y0 + 2.4, sz + 2.85, 4.0, 1.0,
              sign_decal("CORNELIUS UNION 1871", STONE, "#3a3a30", 4.0), "z+", STONE)
    _keep(rect(sx - 4.0, sx + 4.0, sz - 4.0, sz + 4.0))
    for x, z in ((-28.0, -140.0), (28.0, -140.0), (-28.0, -184.0), (28.0, -184.0)):
        b.box([x, y0 + 0.6, z], [10.0, 1.2, 4.0], "#5a4a3a")
        b.sphere([x, y0 + 1.6, z], [9.0, 1.4, 3.2], "#4a7a3a", collide=False)
        for k in range(3):
            b.sphere([x - 3.0 + k * 3.0, y0 + 2.2, z], [1.2, 1.0, 1.2],
                     ["#d83a4a", "#e8c83a", "#e8e2d4"][k], collide=False)
        _keep(rect(x - 6.0, x + 6.0, z - 3.0, z + 3.0))
    for x, z, along in ((-14.0, -146.0, "x"), (14.0, -146.0, "x"), (-14.0, -178.0, "x"),
                        (14.0, -178.0, "x")):
        b.box([x, y0 + 0.9, z], [5.0, 0.3, 1.4], WOOD)
        b.box([x, y0 + 1.6, z - 0.6], [5.0, 1.2, 0.2], WOOD)
        for dx in (-2.0, 2.0):
            b.box([x + dx, y0 + 0.45, z], [0.3, 0.9, 1.2], IRONWORK, material="metal")
    _keep(area)


def _hotel(b: ArenaArea) -> None:
    """The Grand Hotel on the plaza's west side: three storeys, its stair
    up through the floors to a top floor that looks over the diamond."""
    y = UPPER_Y
    area = rect(-104.0, -48.0, -208.0, -150.0)
    well = rect(-100.0, -88.0, -204.0, -190.0)
    levels = storeyed(b, area, [11.0, 10.0, 10.0], STONE, roof="#4a3a3a", base=y,
                      doors={"x+": [(-186.0, -172.0, y + 9.0)]},
                      windows=[{"x+": [(-204.0, -192.0, y + 3.5, y + 8.0), (-166.0, -154.0, y + 3.5, y + 8.0)],
                                "z+": [(-98.0, -84.0, y + 3.5, y + 8.0), (-70.0, -56.0, y + 3.5, y + 8.0)]},
                               {"x+": [(-204.0, -192.0, y + 14.0, y + 19.0), (-184.0, -174.0, y + 14.0, y + 19.0),
                                       (-166.0, -154.0, y + 14.0, y + 19.0)],
                                "z+": [(-98.0, -84.0, y + 14.0, y + 19.0), (-70.0, -56.0, y + 14.0, y + 19.0)]},
                               {"x+": [(-204.0, -192.0, y + 24.0, y + 29.0), (-184.0, -174.0, y + 24.0, y + 29.0),
                                       (-166.0, -154.0, y + 24.0, y + 29.0)],
                                "z+": [(-98.0, -84.0, y + 24.0, y + 29.0), (-70.0, -56.0, y + 24.0, y + 29.0)]}],
                      wells=[well])
    threshold(b, area, "x+", (-186.0, -172.0))
    for k, top in enumerate((y + 11.0, y + 21.0)):
        y0 = levels[k]
        flight(b, "z", -190.0, -204.0, -100.0, -88.0, y0, top, WOOD_DARK, fill=y0 - 0.3)
    b.mark("perch", -66.0, y + 21.0, -178.0)
    wall_sign(b, -47.65, y + 33.0, -179.0, 30.0, 3.4,
              sign_decal("GRAND HOTEL", "#4a3a3a", "#ffd27a", 8.8), "x+", "#4a3a3a")
    for z in (-204.0, -156.0):
        lantern(b, -46.2, y + 9.0, z, WARM)
    _keep(rect(area[0] - 2.0, area[1] + 4.0, area[2], area[3] + 2.0))


def _exchange(b: ArenaArea) -> None:
    """The Exchange on the plaza's east side: a columned front, the trading
    floor inside, the board of prices lit up."""
    y = UPPER_Y
    area = rect(54.0, 118.0, -208.0, -150.0)
    building(b, area, y, 16.0, STONE, roof_colour="#5a5a5e", floor_colour="#8a8070",
             doors={"x-": [(-186.0, -170.0, y + 11.0)]},
             windows={"x-": [(-204.0, -192.0, y + 4.0, y + 11.0), (-164.0, -154.0, y + 4.0, y + 11.0)],
                      "z+": [(60.0, 76.0, y + 4.0, y + 11.0), (96.0, 112.0, y + 4.0, y + 11.0)]},
             glass=True, lights=WARM)
    threshold(b, area, "x-", (-186.0, -170.0))
    slab(b, rect(42.0, 54.0, -208.0, -150.0), y + 1.2, 1.5, STONE_DARK, studs=True)
    flight(b, "x", 38.0, 42.0, -184.0, -172.0, y, y + 1.2, STONE, fill=y - 0.3)
    for z in (-204.0, -194.0, -184.0, -168.0, -158.0, -153.0):
        b.cyl([44.0, y + 1.2 + 7.4, z], [1.8, 14.8, 1.8], STONE)
    slab(b, rect(42.0, 54.0, -208.0, -150.0), y + 1.2 + 14.8 + 1.4, 1.4, STONE_DARK)
    b.box([114.0, y + 7.0, -178.0], [0.4, 6.0, 24.0], "#1a1a1a")
    for k in range(10):
        b.box([113.77, y + 5.0 + (k % 4) * 1.2, -188.0 + k * 2.2], [0.06, 0.6, 1.6],
              "#3aff6a" if k % 3 else "#ff4a3a", material="neon", collide=False)
    wall_sign(b, 41.65, y + 13.0, -178.0, 26.0, 2.6,
              sign_decal("THE EXCHANGE", STONE_DARK, "#2a2a30", 10.0), "x-", STONE_DARK)
    _keep(rect(36.0, 120.0, -208.0, -148.0))


# ================================================================ gasworks
def _gasworks(b: ArenaArea, rng: random.Random) -> None:
    """The gasworks south of the lines: the gasholder in its iron frame,
    the retort house and its chimney, the coal for the retorts."""
    y = HILL_Y
    gx, gz = 10.0, 198.0
    b.cyl([gx, y + 13.0, gz], [44.0, 26.0, 44.0], "#5a6a6a", material="metal")
    b.cyl([gx, y + 26.3, gz], [44.4, 0.6, 44.4], "#3a4a4a", material="metal")
    b.cone([gx, y + 28.0, gz], [40.0, 3.0, 40.0], "#4a5a5a", collide=False)
    for k in range(10):
        a = k / 10.0 * math.pi * 2.0
        px, pz = gx + math.cos(a) * 25.0, gz + math.sin(a) * 25.0
        if pz > 236.0:
            continue
        b.box([px, y + 17.0, pz], [1.6, 34.0, 1.6], IRONWORK, material="metal")
    for ring in (y + 18.0, y + 33.0):
        for k in range(10):
            a0 = k / 10.0 * math.pi * 2.0
            a1 = (k + 1) / 10.0 * math.pi * 2.0
            x0, z0 = gx + math.cos(a0) * 25.0, gz + math.sin(a0) * 25.0
            x1, z1 = gx + math.cos(a1) * 25.0, gz + math.sin(a1) * 25.0
            b.box([(x0 + x1) / 2.0, ring, (z0 + z1) / 2.0], [0.8, 0.8, math.hypot(x1 - x0, z1 - z0)],
                  IRONWORK, collide=False, material="metal", r=[0.0, math.atan2(x1 - x0, z1 - z0), 0.0])
    wall_sign(b, gx, y + 18.0, gz - 22.4, 16.0, 2.6,
              sign_decal("UNION GAS LIGHT CO.", "#3a4a4a", "#e8e2d4", 6.1), "z-", "#3a4a4a")
    _keep(rect(gx - 27.0, gx + 27.0, gz - 27.0, gz + 27.0))
    # the retort house and its stack
    area = rect(48.0, 108.0, 176.0, 216.0)
    building(b, area, y, 14.0, BRICK, roof_colour="#3a3a40",
             doors={"z-": [(56.0, 68.0, y + 10.0), (88.0, 100.0, y + 10.0)]},
             windows={"z-": [(72.0, 84.0, y + 5.0, y + 10.0)], "x+": [(184.0, 196.0, y + 5.0, y + 10.0)]},
             glass=True, lights="#ff9a4a")
    gable(b, area, y + 15.2, "#3a3a40", "x", 4, 1.4, 0.8)
    threshold(b, area, "z-", (56.0, 68.0))
    threshold(b, area, "z-", (88.0, 100.0))
    for k in range(3):
        b.box([60.0 + k * 18.0, y + 2.0, 212.0], [10.0, 4.0, 4.0], "#4a3a32")
        b.box([60.0 + k * 18.0, y + 2.0, 209.9], [6.0, 2.0, 0.2], "#ff8a3a", material="neon", collide=False)
    b.cyl([100.0, y + 24.0, 228.0], [6.0, 48.0, 6.0], BRICK_DARK)
    b.cyl([100.0, y + 48.6, 228.0], [6.8, 1.2, 6.8], "#3a2a22")
    _keep(rect(46.0, 110.0, 174.0, 234.0))


def _storage(b: ArenaArea, rng: random.Random) -> None:
    """Union Storage: a brick warehouse with a loading dock along its front."""
    y = HILL_Y
    area = rect(-142.0, -62.0, 180.0, 230.0)
    building(b, area, y, 14.0, BRICK_DARK, roof_colour="#3a3a40",
             doors={"z-": [(-130.0, -118.0, y + 9.0), (-86.0, -74.0, y + 9.0)]},
             windows={"z-": [(-110.0, -94.0, y + 6.0, y + 10.0)]}, glass=True, lights=WARM)
    threshold(b, area, "z-", (-130.0, -118.0))
    threshold(b, area, "z-", (-86.0, -74.0))
    slab(b, rect(-142.0, -62.0, 172.0, 180.0), y + 1.6, 1.9, "#6a6a66", studs=True)
    for x in (-136.0, -68.0):
        flight(b, "z", 172.0 - 4.0, 172.0, x - 3.0, x + 3.0, y, y + 1.6, "#6a6a66", fill=y - 0.3)
    for k in range(3):
        b.box([-126.0 + k * 22.0, y + 1.6 + 1.6, 176.0], [4.0, 3.2, 4.0], WOOD, studs=True)
    wall_sign(b, -102.0, y + 11.0, 179.65, 34.0, 2.6,
              sign_decal("UNION STORAGE CO.", BRICK_DARK, rails.CREAM, 13.0), "z-", BRICK_DARK)
    _keep(rect(-146.0, -58.0, 166.0, 232.0))


def _market(b: ArenaArea, rng: random.Random) -> None:
    """The covered market in the low town south of the tower: an iron roof
    on columns over a raised floor, rows of stalls under it -- cover in the
    open ground between the lines -- and a rank of cabs waiting by it."""
    area = rect(-30.0, 30.0, 90.0, 130.0)
    slab(b, area, 0.6, 0.9, "#6a6460", studs=True)
    for x in (-30.0, 30.0):
        flight(b, "x", x + (-3.0 if x < 0 else 3.0), x, 104.0, 116.0, 0.0, 0.6, "#6a6460", fill=-0.3)
    for x in (-28.0, -9.33, 9.33, 28.0):
        for z in (92.0, 128.0):
            b.cyl([x, 0.6 + 4.5, z], [1.0, 9.0, 1.0], IRONWORK, material="metal")
    slab(b, rect(-32.0, 32.0, 88.0, 132.0), 0.6 + 9.6, 0.6, "#3a4a42")
    slab(b, rect(-26.0, 26.0, 94.0, 126.0), 0.6 + 11.2, 1.6, "#4a5a52")
    produce = ("#d83a2a", "#e8c83a", "#6aa83a", "#e8862a", "#8a4ab8", "#efe2c4")
    for row, z in enumerate((100.0, 120.0)):
        for k in range(4):
            x = -21.0 + k * 14.0
            b.box([x, 0.6 + 1.0, z], [9.0, 2.0, 3.0], "#6a4a32")
            for j in range(3):
                b.box([x - 3.0 + j * 3.0, 0.6 + 2.3, z], [2.4, 0.6, 2.2], produce[(k + j + row) % len(produce)])
            b.box([x, 0.6 + 4.4, z - (1.8 if row == 0 else -1.8)], [9.4, 0.2, 1.6],
                  ("#c82a2a", "#2a5a8a", "#2a7a3a", "#c8a03a")[k], collide=False,
                  r=[0.25 if row == 0 else -0.25, 0.0, 0.0])
            for dx in (-4.2, 4.2):
                b.box([x + dx, 0.6 + 2.0 + 1.2, z - (1.4 if row == 0 else -1.4)], [0.2, 2.6, 0.2], WOOD_DARK)
    wall_sign(b, 0.0, 0.6 + 9.0, 131.0 + 0.36, 20.0, 1.6,
              sign_decal("UNION MARKET", "#3a4a42", "#ffd27a", 12.5), "z+", "#3a4a42")
    _keep(rect(-34.0, 34.0, 86.0, 134.0))
    # the cab rank: two hansoms and their horse troughs
    for k, x in enumerate((52.0, 70.0)):
        b.box([x, 1.8, 112.0], [5.0, 3.0, 4.0], "#1a1a1e")
        b.box([x, 3.6, 112.0], [5.4, 0.6, 4.4], "#2a2a2e")
        for side in (-1, 1):
            b.cyl([x + 1.4, 1.6, 112.0 + side * 2.3], [3.2, 0.3, 3.2], "#3a2a1e", collide=False,
                  r=[math.pi / 2.0, 0.0, 0.0])
        b.box([x - 4.6, 0.6, 112.0], [3.4, 1.2, 1.6], WOOD_DARK)
        b.box([x - 4.6, 1.22, 112.0], [2.8, 0.04, 1.0], "#4a7a9a", material="glass", collide=False)
    _keep(rect(44.0, 76.0, 108.0, 116.0))


# =============================================================== the shed
def _footbridge(b: ArenaArea) -> None:
    """The station footbridge across the throat, twelve up: a deck from wall
    to wall over both lines, stairs at both ends -- the view down the
    platforms and back along the throat."""
    x0, x1, y = 218.0, 226.0, 12.0
    slab(b, rect(x0, x1, -196.0, 196.0), y, 0.6, "#6a6a70", studs=True)
    for z in (-196.0, -100.0, 0.0, 100.0, 196.0):
        for x in (x0 + 0.6, x1 - 0.6):
            b.box([x, (y - 0.6) / 2.0, z - (0.6 if z > 0 else -0.6) * (abs(z) > 190)],
                  [1.0, y - 0.6, 1.0], IRONWORK, material="metal")
    for side in (-1, 1):
        b.box([x0 + 0.2, y + 1.6, 0.0], [0.4, 3.2, 392.0], IRONWORK, material="metal") if side < 0 else \
            b.box([x1 - 0.2, y + 1.6, 0.0], [0.4, 3.2, 392.0], IRONWORK, material="metal")
    for z in (-196.0, 196.0):
        lo, hi = (z, z + 20.0) if z < 0 else (z - 20.0, z)
        near, far = (z + 20.0, z) if z < 0 else (z - 20.0, z)
    flight(b, "x", x0 - 20.0, x0, -200.0, -192.0, 0.0, y, "#6a6a70", fill=-0.3)
    flight(b, "x", x0 - 20.0, x0, 192.0, 200.0, 0.0, y, "#6a6a70", fill=-0.3)
    b.mark("perch", 222.0, y, 0.0)
    for z in (-150.0, 150.0):
        b.box([222.0, y - 1.2, z], [8.4, 1.6, 0.4], "#2a2a30", collide=False)
    _keep(rect(x0 - 22.0, x1 + 2.0, -202.0, 202.0))


def _shed(b: ArenaArea, rng: random.Random) -> None:
    """The train shed: brick side walls with tall arched windows, a roof of
    iron arches and glass, the platforms between the tracks, a string of
    coaches waiting at each, columns holding the roof's girders."""
    x0, x1, z0, z1 = SHED
    for side in (-1, 1):
        wz = side * (z1 - 1.0)
        for k in range(8):
            px0 = x0 + k * (x1 - x0) / 8.0
            px1 = x0 + (k + 1) * (x1 - x0) / 8.0
            pier = 4.0
            b.box([px0 + pier / 2.0, 9.0, wz], [pier, 18.0, 2.0], BRICK)
            b.box([(px0 + pier + px1) / 2.0, 2.5, wz], [px1 - px0 - pier, 5.0, 2.0], BRICK)
            b.box([(px0 + pier + px1) / 2.0, 16.0, wz], [px1 - px0 - pier, 4.0, 2.0], BRICK)
            b.box([(px0 + pier + px1) / 2.0, 9.5, wz], [px1 - px0 - pier, 9.0, 0.3], "#9ab8c8",
                  material="glass", alpha=0.45)
        b.box([(x0 + x1) / 2.0, 18.6, wz], [x1 - x0, 1.2, 2.6], STONE_DARK)
    # the roof: iron arches every sixteen units, glass between (all far over
    # anybody's head)
    rise, n = 26.0, 12
    for k in range(int((x1 - x0) // 16.0) + 1):
        ax = x0 + 2.0 + k * 16.0
        if ax > x1 - 1.0:
            break
        for j in range(n):
            a0, a1 = math.pi * j / n, math.pi * (j + 1) / n
            za, zb = -math.cos(a0) * z1, -math.cos(a1) * z1
            ya, yb = 19.2 + math.sin(a0) * rise, 19.2 + math.sin(a1) * rise
            run = math.hypot(zb - za, yb - ya)
            b.box([ax, (ya + yb) / 2.0, (za + zb) / 2.0], [1.0, 1.0, run], IRONWORK, collide=False,
                  material="metal", r=[-math.atan2(yb - ya, zb - za), 0.0, 0.0])
    for j in range(n):
        a0, a1 = math.pi * j / n, math.pi * (j + 1) / n
        za, zb = -math.cos(a0) * z1, -math.cos(a1) * z1
        ya, yb = 19.4 + math.sin(a0) * rise, 19.4 + math.sin(a1) * rise
        run = math.hypot(zb - za, yb - ya)
        b.box([(x0 + x1) / 2.0, (ya + yb) / 2.0, (za + zb) / 2.0], [x1 - x0, 0.2, run], "#a8c8d8",
              collide=False, material="glass", alpha=0.3, r=[-math.atan2(yb - ya, zb - za), 0.0, 0.0])
    # the platforms, with steps up off the tracks at their open ends
    for (pa, pc) in PLATFORMS:
        px0 = 240.0
        rails.platform(b, rect(px0, 340.0, pa, pc), edge="#e8e2d4")
        stair(b, "x", px0 - 3.0, px0, (pa + pc) / 2.0 - 3.0, (pa + pc) / 2.0 + 3.0, 0.0, 1.2, "#7a7a7e")
        mid = (pa + pc) / 2.0
        for k in range(3):
            cx = 262.0 + k * 30.0
            b.cyl([cx, 1.2 + 8.4, mid], [1.2, 16.8, 1.2], IRONWORK, material="metal")
            if k == 1 and abs(mid) < 140:
                b.box([cx + 6.0, 1.2 + 0.9, mid], [5.0, 0.3, 1.4], WOOD)
                b.box([cx + 6.0, 1.2 + 1.6, mid + 0.6], [5.0, 1.2, 0.2], WOOD)
        b.box([290.0, 18.6, mid], [100.0, 1.4, 1.4], IRONWORK, material="metal")
        lantern(b, 247.0, 10.0, mid, WARM, post=0.0) if False else None
    # the coaches waiting at the platforms
    liveries = (("#2f4a3a", "UNION LIMITED"), ("#5a2a2a", "CITY EXPRESS"),
                ("#2a3a5a", "NIGHT OWL"), ("#4a3a2a", "VALLEY MAIL"))
    for (tz, (colour, name)) in zip(COACH_TRACKS, liveries):
        stub_track(b, 240.0, 338.0, tz)
        for k, cx in enumerate((256.0, 284.0, 312.0)):
            coach(b, cx, tz, "x", colour, name=name if k == 1 else "", length=26.0)
        buffer_stop(b, 337.0, tz, math.pi / 2.0, IRONWORK)
    # the two racing lines' buffers, and the finish
    for lane, z in (("a", 150.0), ("b", -150.0)):
        buffer_stop(b, 338.0, z, math.pi / 2.0, "#8a2a1c" if lane == "a" else "#2a4a6a")
        b.mark("finish", 330.0, 0.5, z, lane=lane)
    _keep(rect(x0 - 4.0, x1, z0, z1))


def _concourse(b: ArenaArea) -> None:
    """The concourse at the head of the platforms: marble, the clock on its
    column in the middle, ticket windows down both sides, a balcony along
    the back wall with stairs up at both ends."""
    area = rect(340.0, 400.0, -204.0, 204.0)
    slab(b, area, 1.2, 1.5, "#d8d0c0", studs=True)
    # the clock: a column and a four-faced head
    b.cyl([372.0, 1.2 + 5.0, 0.0], [2.4, 10.0, 2.4], "#3a3a40", material="metal")
    b.box([372.0, 1.2 + 12.0, 0.0], [5.0, 5.0, 5.0], "#c8a03a", material="metal")
    for dx, dz, w, d in ((2.54, 0.0, 0.06, 3.6), (-2.54, 0.0, 0.06, 3.6), (0.0, 2.54, 3.6, 0.06),
                         (0.0, -2.54, 3.6, 0.06)):
        b.box([372.0 + dx, 1.2 + 12.0, dz], [w, 3.6, d], "#f2ead8", material="neon", collide=False)
    b.cone([372.0, 1.2 + 15.8, 0.0], [5.6, 2.6, 5.6], "#3a3a40", collide=False)
    # ticket windows on both sides
    for side in (-1, 1):
        z = side * 190.0
        b.box([368.0, 1.2 + 3.0, z], [40.0, 6.0, 4.0], "#6a4a32")
        for k in range(4):
            b.box([352.0 + k * 10.0, 1.2 + 3.6, z - side * 2.04], [4.0, 2.4, 0.06], "#ffe0a0",
                  material="neon", collide=False)
        wall_sign(b, 368.0, 1.2 + 7.4, z - side * 2.35, 30.0, 1.6,
                  sign_decal("TICKETS", "#6a4a32", "#ffd27a", 18.75), "z-" if side > 0 else "z+", "#6a4a32")
    # the balcony along the back wall and its stairs
    slab(b, rect(388.0, 400.0, -150.0, 150.0), 10.2, 0.6, WOOD_LIGHT, studs=True)
    for z in (-150.0, 150.0):
        lo, hi = (z - 14.0, z) if z < 0 else (z, z + 14.0)
        flight(b, "z", (z - 14.0) if z < 0 else (z + 14.0), z, 388.0, 396.0, 1.2, 10.2, WOOD, fill=0.9)
    for z in range(-140, 150, 28):
        b.box([388.4, 10.2 + 0.8, float(z)], [0.4, 1.6, 0.4], IRONWORK, material="metal")
    b.box([388.4, 10.2 + 1.7, 0.0], [0.3, 0.2, 300.0], IRONWORK, material="metal")
    b.mark("perch", 394.0, 10.2, 0.0)
    # benches in rows before the clock
    for k in range(4):
        for side in (-1, 1):
            z = side * (30.0 + k * 22.0)
            b.box([358.0, 1.2 + 0.9, z], [6.0, 0.3, 1.6], WOOD)
            b.box([358.0, 1.2 + 1.7, z + side * 0.7], [6.0, 1.4, 0.2], WOOD)
    wall_sign(b, 399.0 - 0.36, 18.0, 0.0, 60.0, 5.0,
              sign_decal("UNION TERMINAL", "#3a3a40", "#ffd27a", 12.0), "x-", "#3a3a40")


# ============================================================ the furniture
def _depots(b: ArenaArea) -> None:
    depot(b, "a", LANE_A, 1 / 3.0, -1.0, "MARKET STREET", 1, "#7a2a20")
    depot(b, "a", LANE_A, 2 / 3.0, -1.0, "GASWORKS HALT", 2, "#2a3a5a")
    depot(b, "b", LANE_B, 1 / 3.0, 1.0, "MARKET STREET SOUTH", 1, "#2a3a5a")
    depot(b, "b", LANE_B, 2 / 3.0, 1.0, "EXCHANGE HALT", 2, "#7a2a20")
    for entry in b.points.get("depot", []):
        x, z = entry["p"][0] - b.ox, entry["p"][2] - b.oz
        _keep(rect(x - 22.0, x + 22.0, z - 10.0, z + 10.0))


def _levers(b: ArenaArea) -> None:
    for lane, path, sides in (("a", LANE_A, (-1.0, 1.0)), ("b", LANE_B, (1.0, -1.0))):
        for index, (f, side) in enumerate(zip(rails.LEVER_FRACTIONS, sides)):
            lever(b, lane, path, f, side, index)
    for entry in b.points.get("lever", []):
        x, z = entry["p"][0] - b.ox, entry["p"][2] - b.oz
        _keep(rect(x - 4.0, x + 4.0, z - 4.0, z + 4.0))


def _coal(b: ArenaArea, rng: random.Random) -> None:
    for x, z, y in ((-336.0, -100.0, 0.0), (-336.0, 100.0, 0.0), (40.0, 180.0, HILL_Y), (176.0, 0.0, 0.0)):
        coal_heap(b, x, z, rng, base=y)
        _keep(rect(x - 5.0, x + 5.0, z - 5.0, z + 5.0))


def _lamps(b: ArenaArea) -> None:
    """Gas lamps along the yards, round the plaza and down the street."""
    spots = [(-40.0, -116.0), (40.0, -116.0), (-40.0, -204.0), (40.0, -204.0),
             (STREET_X + 11.0, -150.0), (STREET_X + 11.0, 150.0), (-230.0, -110.0), (-230.0, 110.0),
             (0.0, 120.0), (-120.0, 140.0), (160.0, -120.0), (200.0, 200.0), (-46.0, 170.0)]
    for x, z in spots:
        if not clear_of(rect(x - 1.0, x + 1.0, z - 1.0, z + 1.0), LANES, 9.0):
            continue
        if any(k[0] - 1 < x < k[1] + 1 and k[2] - 1 < z < k[3] + 1 for k in KEEP):
            continue
        y = UPPER_Y if (UPPER[0] < x < UPPER[1] and UPPER[2] < z < UPPER[3]) else \
            (HILL_Y if (HILL[0] < x < HILL[1] and HILL[2] < z < HILL[3]) else 0.0)
        lamp_post(b, x, z, h=13.0, colour=IRONWORK, light="#ffcf7a", y=y)
