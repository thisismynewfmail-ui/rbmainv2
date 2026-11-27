"""Golden Spike Summit -- the last day of the race to finish the line, high
noon on the summit of a sage-and-juniper pass.

Layout (north is -z; both tracks run west to east)::

    z -250 ~~~~~~~~~~~~~~~~~~~~ the hills ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
           WEST GRADE     R  \\                 grandstand          SUMMIT   /--- SAGEBRUSH
           CAMP  -----====G===\\    the climb     the spike    /== RIDGE ==/      TERMINUS
             (lane a start)  U   \\                          /   north cut       (lane b end)
    z    0 COMMISSARY       L     \\===== THE CEREMONY ====/     LOOKOUT    SUMMIT HOTEL
                            C     /       GROUND (14 up)  \\     KNOB
           SAGE FLAT  -----=H====/      the engines        \\== south cut ===\\--- CEDAR SPRINGS
           CAMP           (trestles)     photographer               \\       STATION
    z +250 ~~~~~~~~~~~~~~~~~~~~ the hills ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The twist (``railhead``): neither line is finished.  Each has two gaps,
graded and ballasted and no rails -- the first on its trestle over
Rattlesnake Gulch, a stone's throw from the start, the second in its cut
through the Summit Ridge on the way down.  A cart stops where the rails
stop; a team carries rails from the stacks (the camps, the rail dumps on
the ceremony ground, the supply cars past the ridge) and lays them, one at
a time, from its own railhead -- and the other company can pull the last
one back up while the cart is not on it.

The land rolls (land.py): the lines climb fourteen units from the camps to
the saddle where they cross, and drop to the termini beyond the ridge.
"""
from __future__ import annotations

import math
import random

from ..kit import (WARM, WOOD, WOOD_DARK, WOOD_LIGHT, ArenaArea, backdrop, building, flight,
                   gable, ground, lantern, rect, room_walls, sign_decal, slab, threshold,
                   wall_sign)
from . import rails
from .land import Land, graded, lay_graded, side_point, world_lane
from .rails import (beside, buffer_stop, coal_heap, crate_stack, depot, fillet, flatcar, lever,
                    mirror, stair, storeyed, telegraph, wagon)
from .scenery import (bunting, camp_fire, cook_wagon, deck_ties, flag_pole, grandstand, juniper,
                      locomotive, outcrop, pup_tent, rail_stack, sage, skull, stub_track,
                      survey_stakes, trestle)

HALF = (400.0, 250.0)
SKY = {"top": "#3a6ab8", "horizon": "#f2e6c8", "sun": [0.3, 0.9, -0.25],
       "clouds": 0.35, "tint": "#fff2d8"}
AMBIENT = "#c8b89a"
GROUND = "#c8b47a"
FOG = 1000.0

SAGEBRUSH = "#c8b47a"
DRY = "#b8a068"
ROCK = "#a07a58"
ROCK_DARK = "#7a5a40"
ROCK_PALE = "#c09a72"
GULCH_FLOOR = "#a08a62"

ROUTE = fillet([(-372.0, -150.0), (-232.0, -150.0), (0.0, 0.0), (232.0, 150.0), (372.0, 150.0)],
               radius=80.0, step=5.0)
PROFILE = [(0.0, 0.0), (0.17, 0.0), (0.4, 14.0), (0.6, 14.0), (0.83, 0.0), (1.0, 0.0)]
LANE_A, YS = graded(ROUTE, PROFILE)
LANE_B = mirror(LANE_A)
SUMMIT = 14.0

GULCH = rect(-290.0, -254.0, -250.0, 250.0)
GULCH_Y = -12.0
TRESTLE = (-290.0, -254.0)          # x span of each line's trestle (gap one)
DECK = (82.0, 118.0)                # the trestle's span along each line
GAPS = [(84.0, 114.0), (515.0, 545.0)]
RIDGE_X = 97.0
STACKS = ((-300.0, -110.0), (-300.0, 110.0), (-62.0, 0.0), (62.0, 0.0), (226.0, -104.0),
          (226.0, 104.0))
COAL = ((-336.0, -100.0), (-336.0, 100.0), (-110.0, 0.0), (160.0, 0.0))
TOWERS = ((-160.0, -28.0), (-160.0, 28.0))

KEEP: list = []
BASES: dict = {}


def build(b: ArenaArea) -> None:
    rng = random.Random(0x60D5)
    del KEEP[:]
    b.extra.update({"accent": "#e8b23a", "twist": "railhead",
                    "lanes": {"a": world_lane(b, LANE_A, YS), "b": world_lane(b, LANE_B, YS)},
                    "names": {"a": "the Overland grade", "b": "the Sage Flat line"},
                    "gaps": {"a": [list(g) for g in GAPS], "b": [list(g) for g in GAPS]},
                    "drown_what": "the gulch"})
    land = _land()
    _furniture_flats(land)
    _plan(land)
    ground(b, SAGEBRUSH, soil="#7a6448", holes=[GULCH])
    _gulch(b, rng)
    land.build(b, SAGEBRUSH)
    _edge(b, rng)
    _tracks(b)
    _camps(b, rng)
    _commissary(b)
    _ceremony(b, rng, land)
    _ridge(b, rng, land)
    _termini(b)
    _hotel(b)
    _depots(b, land)
    _levers(b, land)
    _stacks(b, land)
    _coal(b, rng, land)
    _scatter(b, rng, land)
    telegraph(b, LANE_A, -1.0, ground=land.height, skip=lambda x, z: _blocked(x, z))
    telegraph(b, LANE_B, 1.0, ground=land.height, skip=lambda x, z: _blocked(x, z))
    for x, z, name in ((-345, -150, "West Grade Camp"), (-345, 150, "Sage Flat Camp"),
                       (-352, 0, "the commissary"), (-272, 0, "Rattlesnake Gulch"),
                       (-272, -150, "the north trestle"), (-272, 150, "the south trestle"),
                       (-150, -100, "the Overland grade"), (-150, 100, "the Sage Flat climb"),
                       (0, -30, "the ceremony ground"), (0, -22, "the golden spike"),
                       (0, -64, "the grandstand"), (0, 40, "the photographer's stand"),
                       (0, 66, "the meeting engines"), (-62, 0, "the west rail dump"),
                       (62, 0, "the east rail dump"), (RIDGE_X, 0, "Lookout Knob"),
                       (RIDGE_X, -64, "the north cut"), (RIDGE_X, 64, "the south cut"),
                       (345, 150, "Cedar Springs Station"), (345, -150, "Sagebrush Terminus"),
                       (352, 0, "the Summit Hotel"), (230, -100, "the supply cars")):
        b.landmark(float(x), float(z), name)
    b.camera(-330.0, 40.0, -60.0, -272.0, 0.0, -150.0)
    b.camera(0.0, 50.0, 120.0, 0.0, 14.0, 0.0)
    b.camera(170.0, 46.0, 0.0, RIDGE_X, 14.0, 60.0)


def _blocked(x: float, z: float) -> bool:
    """A pole would stand in something: the gulch, a building, the ridge cuts."""
    if GULCH[0] - 4 < x < GULCH[1] + 4:
        return True
    return any(k[0] - 2 < x < k[1] + 2 and k[2] - 2 < z < k[3] + 2 for k in KEEP)


def _keep(area) -> None:
    KEEP.append(area)


# ==================================================================== land
def _land() -> Land:
    """The pass: a broad saddle in the middle, the ground rising to the
    hills north and south, the Summit Ridge across the east, knolls."""
    hx, hz = HALF
    # ten-unit cells in one-unit terraces: the hills read as hills and stay
    # a few hundred boxes, not thousands (the line's own cells are finer)
    land = Land(rect(-hx, hx, -hz, hz), cell=10.0, step=1.0)

    def shape(x: float, z: float) -> float:
        backbone = SUMMIT * math.exp(-(x / 210.0) ** 2)
        basin = 14.0 * max(0.0, (abs(z) - 95.0) / 155.0) ** 1.5
        ridge = 13.0 * math.exp(-((x - RIDGE_X) / 19.0) ** 2)
        knolls = 1.6 * math.sin(x / 37.0 + 1.3) * math.sin(z / 29.0) + \
            1.1 * math.cos(x / 23.0) * math.sin(z / 41.0 + 0.7)
        west = 0.0 if x > -240 else max(0.0, 1.0 - (-240 - x) / 40.0)
        return max(0.0, backbone * (1.0 if x > -240 else west) + basin + ridge + knolls)

    land.add(shape)
    land.cut(GULCH)
    for path in (LANE_A, LANE_B):
        land.pin_path(path, YS, half=7.5, blend=14.0)
    land.colour(lambda x, z, h: ROCK if h > 19.0 else (ROCK_PALE if h > 15.5 and abs(x - RIDGE_X) < 30
                                                       else (DRY if _patchy(x, z) else None)))
    return land


def _patchy(x: float, z: float) -> bool:
    """Where the ground is baked bare: drifting blobs, nothing like a grid."""
    v = math.sin(x / 53.0 + 0.7) * math.cos(z / 41.0) + 0.6 * math.sin((x + z) / 37.0 + 2.1) + \
        0.35 * math.cos((x - 2.0 * z) / 29.0)
    return v > 0.72


def _depot_spot(path, f: float, side: float):
    """Where rails.depot will put a depot's platform (its centre, half
    sizes), so the ground can be levelled for it first."""
    total = rails.length(path)
    x, z, yaw = rails.at(path, total * f)
    rx, rz = math.cos(yaw), -math.sin(yaw)
    along_x = abs(math.sin(yaw)) > 0.7
    hx, hz = (16.0, 6.0) if along_x else (6.0, 16.0)
    offset = max(15.0, abs(rx) * hx + abs(rz) * hz + 7.0)
    return x + rx * side * offset, z + rz * side * offset, hx, hz


DEPOTS = (("a", 1 / 3.0, -1.0, "HALFWAY TANK", 1, "#7a3a2a"),
          ("a", 2 / 3.0, 1.0, "RIDGE SIDING", 2, "#2f4a6a"),
          ("b", 1 / 3.0, 1.0, "HALFWAY TANK SOUTH", 1, "#2f4a6a"),
          ("b", 2 / 3.0, -1.0, "RIDGE SIDING NORTH", 2, "#7a3a2a"))


def _plan(land: Land) -> None:
    """Level the ground under everything that stands on the hills, each at
    the height the hill has there (the depots at their track's height)."""
    BASES.clear()
    for lane, f, side, _name, _stage, _roof in DEPOTS:
        path = LANE_A if lane == "a" else LANE_B
        ox, oz, hx, hz = _depot_spot(path, f, side)
        base = round(_track_y(rails.length(path) * f) * 2.0) / 2.0
        land.flatten(rect(ox - hx - 4.0, ox + hx + 4.0, oz - hz - 1.0, oz + hz + 1.0), base, blend=8.0)
        BASES[(lane, f)] = base
    for key, spots, pad in (("stack", STACKS, (10.0, 4.0)), ("coal", COAL, (5.5, 5.5)),
                            ("tower", TOWERS, (10.0, 10.0))):
        for x, z in spots:
            y = round(land.height(x, z) * 2.0) / 2.0
            x0, x1 = (x - pad[0], x + pad[0]) if key != "tower" else (x - 10.0, x + 22.0)
            land.flatten(rect(x0, x1, z - pad[1], z + pad[1]), y, blend=6.0)
            BASES[(key, x, z)] = y
    knob = round(land.height(RIDGE_X, 0.0) * 2.0) / 2.0
    land.flatten(rect(RIDGE_X - 6.0, RIDGE_X + 6.0, -6.0, 24.0), knob, blend=6.0)
    BASES["knob"] = knob


def _furniture_flats(land: Land) -> None:
    """The ground under everything built is level: the camps and termini at
    the ground, the ceremony ground at the summit."""
    for area, y in ((rect(-400.0, -296.0, -250.0, 250.0), 0.0), (rect(296.0, 400.0, -250.0, 250.0), 0.0),
                    (rect(-48.0, 48.0, -82.0, -16.0), SUMMIT), (rect(-48.0, 48.0, 16.0, 82.0), SUMMIT),
                    (rect(-80.0, -44.0, -18.0, 18.0), SUMMIT), (rect(44.0, 70.0, -18.0, 18.0), SUMMIT)):
        land.flatten(area, y, blend=14.0)


# ================================================================== the edge
def _edge(b: ArenaArea, rng: random.Random) -> None:
    hx, hz, m = b.half_x, b.half_z, b.margin
    room_walls(b, rect(-hx - m, hx + m, -hz - m, hz + m), m, 0.0, 44.0, ROCK_DARK)
    for side in (-1, 1):
        for i in range(24):
            x = -hx + (i + 0.5) * (2 * hx) / 24.0
            top = rng.uniform(8.0, 22.0)
            b.box([x, 44.0 + top / 2.0, side * (hz + m / 2.0)], [2 * hx / 24.0 - 1.0, top, m + 1.0],
                  rng.choice([ROCK, ROCK_DARK, "#8a6a4a"]), collide=False)
    backdrop(b, "peaks", 0.0, rng, ["#8a7a8a", "#9a8a98", "#7a6a7a"], depth=180.0)


# ================================================================= gulch
def _gulch(b: ArenaArea, rng: random.Random) -> None:
    """Rattlesnake Gulch: a dry wash twelve deep across the whole area, its
    walls banded rock, a creek bed of pale stones down the middle, ways down
    and up at both ends and in the middle -- and the two trestles over it."""
    x0, x1, z0, z1 = GULCH
    slab(b, GULCH, GULCH_Y, 0.6, GULCH_FLOOR, studs=True)
    # the walls under the ground's own soil, and the ends, under the
    # boundary, closed right up to the ground
    for x, w in ((x0 - 3.0, 6.0), (x1 + 3.0, 6.0)):
        b.box([x, (GULCH_Y - 0.6 - 6.0) / 2.0, 0.0], [w, -6.0 - GULCH_Y + 0.6, z1 - z0 + 32.0], ROCK_DARK)
    for z in (z0 - 8.0, z1 + 8.0):
        b.box([(x0 + x1) / 2.0, (GULCH_Y - 0.6 - 6.0) / 2.0, z], [x1 - x0, -6.0 - GULCH_Y + 0.6, 16.0],
              ROCK_DARK)
    # the creek bed: a meander of pale gravel
    step = (z1 - z0 - 24.0) / 17.0
    for k in range(17):
        z = z0 + 12.0 + (k + 0.5) * step
        x = (x0 + x1) / 2.0 + math.sin(k * 0.9) * 8.0
        b.box([x, GULCH_Y + 0.08 + (k % 2) * 0.004, z], [5.0, 0.16, step], "#b8ac90", collide=False)
    # boulders on the floor and ledges in the walls
    for k in range(14):
        z = z0 + 20.0 + k * (z1 - z0 - 40.0) / 13.0
        if any(abs(z - c) < 16 for c in (-150.0, 150.0, 0.0, -205.0, 205.0)):
            continue
        x = x0 + 4.0 + (k * 7 % 5) * 6.0
        outcrop(b, x, z, rng.uniform(3.0, 6.0), rng.uniform(1.6, 3.2), rng.uniform(3.0, 5.0),
                base=GULCH_Y, colour=rng.choice([ROCK, ROCK_PALE, ROCK_DARK]))
    # ways down and up: rocky stairs off both banks at the middle and the ends
    for zc in (0.0, -205.0, 205.0):
        flight(b, "x", x0 + 14.0, x0, zc - 4.0, zc + 4.0, GULCH_Y, 0.0, ROCK_PALE, fill=GULCH_Y - 0.3)
        flight(b, "x", x1 - 14.0, x1, zc - 4.0, zc + 4.0, GULCH_Y, 0.0, ROCK_PALE, fill=GULCH_Y - 0.3)
    # an old prospector's rocker and his skull of a steer
    b.box([x0 + 8.0, GULCH_Y + 1.0, 60.0], [6.0, 2.0, 2.4], WOOD_DARK)
    b.box([x0 + 8.0, GULCH_Y + 2.3, 60.0], [5.0, 0.6, 2.0], "#8a7a5a")
    skull(b, x1 - 6.0, -60.0, base=GULCH_Y, yaw=0.6)
    skull(b, x0 + 10.0, 110.0, base=GULCH_Y, yaw=2.1)
    # the trestles: level with the banks, the gap in the line on each
    for z in (-150.0, 150.0):
        trestle(b, TRESTLE[0], TRESTLE[1], z, 0.0, GULCH_Y, half=7.0)
        deck_ties(b, TRESTLE[0] + 1.0, TRESTLE[1] - 1.0, z, 0.0)
        stakes = [(TRESTLE[0] + 3.0 + k * 6.0, 0.0, z + s * 3.4) for k in range(5) for s in (-1, 1)]
        survey_stakes(b, stakes)


# ================================================================= tracks
def _tracks(b: ArenaArea) -> None:
    """Both lines: no ballast over the trestles (the deck is the bed), and
    nothing on the bed in the gaps -- the client lays those rails as the
    players do."""
    for path in (LANE_A, LANE_B):
        lay_graded(b, path, YS, skip=[DECK], bare=GAPS)


# ================================================================== camps
def _camps(b: ArenaArea, rng: random.Random) -> None:
    """The end-of-track camps at the west end: the platform the company
    starts from, the tents, the cook wagon and its fire, the forge, the
    supply cars and their rails."""
    for lane, z, name, roof in (("a", -150.0, "WEST GRADE CAMP", "#7a3a2a"),
                                ("b", 150.0, "SAGE FLAT CAMP", "#2f4a6a")):
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
        # the tents in two rows behind the platform
        for row in range(2):
            for k in range(4):
                tx = -380.0 + k * 13.0
                tz = pz + side * (18.0 + row * 12.0)
                pup_tent(b, tx, tz, "z", "#e2d6b8" if (k + row) % 2 else "#d4c6a4")
        _keep(rect(-386.0, -326.0, min(pz + side * 12.0, pz + side * 36.0),
                   max(pz + side * 12.0, pz + side * 36.0)))
        # the mess: a big tent, the cook wagon, the fire
        mz = pz + side * 50.0
        building(b, rect(-376.0, -346.0, mz - 9.0, mz + 9.0), 0.0, 6.0, "#e8dcc0", t=0.8,
                 roof_colour="#e8dcc0", roof_t=0.6, floor_colour="#8a7a5a",
                 doors={"x+": [(mz - 4.0, mz + 4.0, 5.0)]}, lights=WARM, studs_roof=False)
        gable(b, rect(-376.0, -346.0, mz - 9.0, mz + 9.0), 6.6, "#e8dcc0", "x", tiers=3, rise=1.2,
              overhang=0.0)
        threshold(b, rect(-376.0, -346.0, mz - 9.0, mz + 9.0), "x+", (mz - 4.0, mz + 4.0), t=0.8)
        cook_wagon(b, -332.0, mz + side * 4.0, "x")
        camp_fire(b, -330.0, mz - side * 8.0)
        _keep(rect(-380.0, -320.0, min(mz - 12.0, mz + 12.0), max(mz - 12.0, mz + 12.0)))
        # the forge: an anvil, a glowing hearth under a lean-to
        fz = pz + side * 72.0
        b.box([-360.0, 1.2, fz], [4.0, 2.4, 3.0], "#6a6460")
        b.box([-360.0, 2.5, fz], [3.0, 0.2, 2.0], "#ff8a3a", material="neon", collide=False)
        b.box([-352.0, 1.0, fz], [2.0, 2.0, 1.2], "#2a2826", material="metal")
        rails.shelter(b, rect(-366.0, -348.0, fz - 4.0, fz + 4.0), 0.0, 7.0, "#5a4a3a")
        # the supply cars on their siding, south of the line toward the shed
        sz = z - side * 26.0
        for k, load in enumerate(("rails", "timber", "rails")):
            flatcar(b, -365.0 + k * 22.0, sz, "x", load, rng)
        _keep(rect(-378.0, -300.0, sz - 4.0, sz + 4.0))
        sign_z = z - side * 10.0
        b.box([-300.0, 2.5, sign_z], [0.6, 5.0, 0.6], WOOD_DARK)
        b.box([-300.0, 5.6, sign_z], [10.0, 2.0, 0.3], rails.CREAM,
              decal=sign_decal("END OF TRACK  SUMMIT 6 MI", rails.CREAM, "#3a2414", 5.0))


def _commissary(b: ArenaArea) -> None:
    """The commissary and paymaster's office between the two camps: it keeps
    the starts out of each other's sights, and its loft looks over both."""
    shed = rect(-386.0, -318.0, -64.0, 64.0)
    building(b, shed, 0.0, 16.0, "#8a6a48", roof_colour="#4a3a2e",
             doors={"x+": [(-26.0, -12.0, 11.0), (12.0, 26.0, 11.0)]},
             windows={"z-": [(-370.0, -352.0, 7.0, 11.0)], "z+": [(-370.0, -352.0, 7.0, 11.0)],
                      "x+": [(-50.0, -36.0, 7.0, 11.0), (36.0, 50.0, 7.0, 11.0)]},
             glass=True, lights=WARM)
    gable(b, shed, 17.2, "#4a3a2e", "z", 5, 1.5, 1.0)
    threshold(b, shed, "x+", (-26.0, -12.0))
    threshold(b, shed, "x+", (12.0, 26.0))
    for k in range(4):
        crate_stack(b, -372.0 + (k % 2) * 18.0, -36.0 + k * 22.0, random.Random(k))
    b.box([-334.0, 1.6, 0.0], [10.0, 3.2, 3.0], "#5a3a22")
    b.box([-334.0, 3.4, 0.0], [10.4, 0.4, 3.4], "#3a2414")
    wall_sign(b, -317.65, 13.0, 0.0, 36.0, 3.6,
              sign_decal("COMMISSARY & PAYMASTER", "#3a2414", rails.GOLD, 10.0), "x+", "#3a2414")
    _keep(rect(-390.0, -314.0, -68.0, 68.0))


# ======================================================== ceremony ground
def _ceremony(b: ArenaArea, rng: random.Random, land: Land) -> None:
    """Where the rails meet, fourteen up: the grandstand for the dignitaries,
    the table with the laurel tie and the golden spike, the two engines
    nose to nose for the photograph, the photographer's stand, flags and
    bunting, and the rail dumps either side."""
    y = SUMMIT
    grandstand(b, rect(-28.0, 28.0, -74.0, -56.0), "z+", base=y, tiers=4)
    _keep(rect(-30.0, 30.0, -76.0, -54.0))
    # the table, the laurel tie, the spike on its cushion
    b.box([0.0, y + 1.4, -24.0], [8.0, 0.4, 3.0], "#efe2c4")
    for dx in (-3.4, 3.4):
        for dz in (-1.1, 1.1):
            b.box([dx, y + 0.6, -24.0 + dz], [0.4, 1.2, 0.4], WOOD_DARK)
    b.box([0.0, y + 1.75, -24.0], [5.0, 0.3, 1.2], "#5a3a22")
    b.box([0.0, y + 2.0, -24.0], [1.6, 0.2, 1.0], "#a8222a", collide=False)
    b.box([0.0, y + 2.6, -24.0], [0.25, 1.0, 0.25], rails.GOLD, material="metal", collide=False)
    b.box([0.0, y + 3.15, -24.0], [0.5, 0.15, 0.5], rails.GOLD, material="metal", collide=False)
    b.box([2.6, y + 1.7, -24.0], [0.5, 0.2, 2.0], "#c8c8cc", material="metal", collide=False)
    _keep(rect(-6.0, 6.0, -28.0, -20.0))
    # the photographer's stand: a scaffold with the camera on top (a perch)
    px, pz = 0.0, 40.0
    for dx in (-3.4, 3.4):
        for dz in (-3.4, 3.4):
            b.box([px + dx, y + 5.0, pz + dz], [0.8, 10.0, 0.8], WOOD_DARK)
    slab(b, rect(px - 4.2, px + 4.2, pz - 4.2, pz + 4.2), y + 10.6, 0.6, WOOD_LIGHT, studs=True)
    stair(b, "z", pz + 4.2 + 17.0, pz + 4.2, px - 2.0, px + 2.0, y, y + 10.6, WOOD)
    b.box([px, y + 12.4, pz - 1.0], [2.0, 1.6, 2.6], "#2a2420")
    b.cyl([px, y + 12.4, pz - 2.6], [1.0, 0.8, 1.0], "#8a8680", material="metal",
          r=[math.pi / 2.0, 0, 0], collide=False)
    b.box([px, y + 12.3, pz + 0.35], [2.2, 1.4, 0.1], "#1a1a1a", collide=False)
    b.mark("perch", px, y + 10.6, pz)
    _keep(rect(px - 6.0, px + 6.0, pz - 6.0, pz + 23.0))
    # the two engines, nose to nose on a stub of track
    stub_track(b, -42.0, 42.0, 66.0, base=y)
    locomotive(b, -14.0, 66.0, "x", 1.0, colour="#7a1a1a", trim=rails.GOLD, base=y, name="COMET")
    locomotive(b, 14.0, 66.0, "x", -1.0, colour="#1a3a6a", trim="#d8d8d0", base=y, name="IRON DUKE",
               stack="straight")
    _keep(rect(-44.0, 44.0, 60.0, 72.0))
    # flags round the ground, bunting between them
    poles = [(-34.0, -40.0), (34.0, -40.0), (-40.0, 26.0), (40.0, 26.0), (-20.0, -50.0), (20.0, -50.0)]
    colours = ["#c4281c", "#2f6aa8", "#efe2c4", rails.GOLD, "#c4281c", "#2f6aa8"]
    for (fx, fz), c in zip(poles, colours):
        flag_pole(b, fx, fz, base=y, colour=c)
    for (ax, az), (cx, cz) in ((poles[4], poles[5]), (poles[0], poles[4]), (poles[5], poles[1])):
        bunting(b, (ax, y + 12.0, az), (cx, y + 12.0, cz))
    # a band's chairs and a bass drum by the grandstand
    for k in range(6):
        b.box([-24.0 + k * 3.2, y + 0.6, -48.0], [1.4, 1.2, 1.4], "#5a3a22")
    b.cyl([18.0, y + 1.2, -48.0], [2.4, 1.6, 2.4], "#efe2c4", r=[math.pi / 2.0, 0, 0], collide=False)
    b.box([18.0, y + 0.3, -48.0], [2.4, 0.6, 1.6], WOOD_DARK)
    # the telegraph tent, the key that will send the word
    building(b, rect(-46.0, -32.0, 40.0, 52.0), y, 5.0, "#e8dcc0", t=0.8, roof_colour="#e8dcc0",
             roof_t=0.6, floor_colour="#8a7a5a", doors={"x+": [(43.0, 49.0, 4.2)]}, lights=WARM,
             studs_roof=False)
    threshold(b, rect(-46.0, -32.0, 40.0, 52.0), "x+", (43.0, 49.0), t=0.8)
    b.box([-42.0, y + 1.1, 46.0], [3.0, 0.3, 1.6], WOOD_DARK)
    b.box([-42.0, y + 1.35, 46.0], [0.5, 0.2, 0.3], "#c8a03a", material="metal", collide=False)
    wall_sign(b, -39.0, y + 4.2, 52.35, 5.0, 1.0, sign_decal("D-O-N-E", "#3a2414", rails.GOLD, 5.0),
              "z+", "#3a2414")
    _keep(rect(-48.0, -30.0, 38.0, 54.0))


# ================================================================== ridge
def _ridge(b: ArenaArea, rng: random.Random, land: Land) -> None:
    """The Summit Ridge across the east: both lines go through it in cuts
    (the second gap is in each), and between the cuts it rises to Lookout
    Knob, where the surveyors' tower stands."""
    # rock walls up the sides of each cut
    for path in (LANE_A, LANE_B):
        for d in range(505, 560, 9):
            for side in (-1.0, 1.0):
                x, z, _yaw, y = side_point(path, YS, float(d), side * 11.5)
                h = land.height(x, z)
                if h < y + 2.0:
                    continue
                outcrop(b, x, z, rng.uniform(4.0, 6.0), rng.uniform(2.5, 4.5), rng.uniform(4.0, 6.0),
                        base=h, colour=rng.choice([ROCK, ROCK_DARK]), cap=ROCK_PALE)
        stakes = []
        for g0, g1 in GAPS[1:]:
            for k in range(5):
                for s in (-1.0, 1.0):
                    x, z, _yaw, y = side_point(path, YS, g0 + 3.0 + k * 6.0, s * 3.4)
                    stakes.append((x, land.height(x, z), z))
        survey_stakes(b, stakes)
    # the survey tower on Lookout Knob
    top = BASES["knob"]
    for dx in (-3.0, 3.0):
        for dz in (-3.0, 3.0):
            b.box([RIDGE_X + dx, top + 4.5, dz], [0.8, 9.0, 0.8], WOOD_DARK)
    slab(b, rect(RIDGE_X - 4.0, RIDGE_X + 4.0, -4.0, 4.0), top + 9.6, 0.6, WOOD_LIGHT, studs=True)
    stair(b, "z", 4.0 + 17.0, 4.0, RIDGE_X - 1.8, RIDGE_X + 1.8, top, top + 9.6, WOOD)
    for k in range(3):
        a = k / 3.0 * math.pi * 2.0
        b.box([RIDGE_X + 1.0 + math.cos(a) * 0.9, top + 10.9, 1.0 + math.sin(a) * 0.9], [0.2, 2.4, 0.2],
              "#8a6a4a", r=[math.sin(a) * 0.25, 0, -math.cos(a) * 0.25], collide=False)
    b.box([RIDGE_X + 1.0, top + 12.3, 1.0], [1.2, 0.6, 0.6], "#c8a03a", material="metal")
    b.mark("perch", RIDGE_X, top + 9.6, 0.0)
    _keep(rect(RIDGE_X - 6.0, RIDGE_X + 6.0, -6.0, 24.0))


# ================================================================ termini
def _termini(b: ArenaArea) -> None:
    for lane, z, name, roof in (("a", 150.0, "CEDAR SPRINGS STATION", "#2f4a6a"),
                                ("b", -150.0, "SAGEBRUSH TERMINUS", "#7a3a2a")):
        side = 1.0 if z > 0 else -1.0
        pz = z + side * 15.0
        rails.platform(b, rect(310.0, 380.0, pz - 6.0, pz + 6.0))
        stair(b, "x", 307.0, 310.0, pz - 3.0, pz + 3.0, 0.0, 1.2, WOOD)
        rails.shelter(b, rect(318.0, 372.0, pz - 3.4, pz + 3.4), 1.2, 9.0, roof)
        b.box([345.0, 1.2 + 9.6 + 1.2, pz], [44.0, 2.4, 0.5], rails.GOLD,
              decal=sign_decal(name, rails.GOLD, "#3a2414", 18.0))
        buffer_stop(b, 372.0, z, math.pi / 2.0, roof)
        house = rect(326.0, 378.0, pz + side * 8.0, pz + side * 30.0)
        building(b, house, 0.0, 14.0, "#9a7a54", roof_colour=roof,
                 doors={"x-": [(min(house[2], house[3]) + 7.0, max(house[2], house[3]) - 7.0, 9.0)]},
                 windows={"z-" if side > 0 else "z+": [(330.0, 344.0, 4.0, 9.0), (356.0, 370.0, 4.0, 9.0)]},
                 glass=True, lights=WARM)
        threshold(b, house, "x-", (min(house[2], house[3]) + 7.0, max(house[2], house[3]) - 7.0))
        gable(b, house, 15.2, roof, "x", 4, 1.3, 0.8)
        b.box([314.0, 6.5, z + side * 9.0], [0.8, 13.0, 0.8], WOOD_DARK)
        b.box([314.0, 12.6, z + side * 9.0], [2.2, 2.2, 2.2], rails.GOLD, material="metal", collide=False)
        b.mark("finish", 362.0, 0.5, z, lane=lane)
        _keep(rect(304.0, 382.0, min(pz - 8.0, house[2]) - 2.0, max(pz + 8.0, house[3]) + 2.0))
        # a stage coach waiting for the passengers
        wagon(b, 300.0, pz + side * 40.0, "x", "#7a1a1a")


def _hotel(b: ArenaArea) -> None:
    """The Summit Hotel between the termini, two storeys and a balcony."""
    area = rect(324.0, 384.0, -40.0, 40.0)
    storeyed(b, area, [11.0, 10.0], "#c8a878", roof="#5a3a2a",
             doors={"x-": [(-6.0, 6.0, 9.0)]},
             windows=[{"x-": [(-34.0, -18.0, 3.5, 8.0), (18.0, 34.0, 3.5, 8.0)]},
                      {"x-": [(-34.0, -22.0, 14.0, 19.0), (-6.0, 6.0, 14.0, 19.0), (22.0, 34.0, 14.0, 19.0)]}],
             wells=[rect(366.0, 380.0, -36.0, -24.0)])
    threshold(b, area, "x-", (-6.0, 6.0))
    flight(b, "z", -24.0, -36.0, 366.0, 380.0, 0.0, 11.0, WOOD, fill=-0.3)
    slab(b, rect(316.0, 324.0, -30.0, 30.0), 11.6, 0.6, WOOD, studs=True)
    flight(b, "z", 30.0 + 18.0, 30.0, 316.0, 324.0, 0.0, 11.6, WOOD, fill=-0.3)
    for z in (-28.0, -10.0, 10.0, 28.0):
        b.box([316.6, 5.5, z], [0.8, 11.0, 0.8], WOOD_DARK)
    wall_sign(b, 323.65, 19.0, 0.0, 30.0, 3.4, sign_decal("SUMMIT HOTEL", "#5a3a2a", rails.CREAM, 9.0),
              "x-", "#5a3a2a")
    b.mark("perch", 320.0, 11.6, 0.0)
    _keep(rect(312.0, 388.0, -44.0, 44.0))


# ============================================================ the furniture
def _depots(b: ArenaArea, land: Land) -> None:
    for lane, f, side, name, stage, roof in DEPOTS:
        path = LANE_A if lane == "a" else LANE_B
        depot(b, lane, path, f, side, name, stage, roof, base=BASES[(lane, f)])
        entry = b.points["depot"][-1]
        ox, oz = entry["p"][0] - b.ox, entry["p"][2] - b.oz
        _keep(rect(ox - 22.0, ox + 22.0, oz - 10.0, oz + 10.0))
    del land


def _track_y(d: float) -> float:
    from .land import height_at
    return height_at(LANE_A, YS, d)


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


def _stacks(b: ArenaArea, land: Land) -> None:
    """The rail stacks: one at each camp, the two rail dumps on the
    ceremony ground, the supply cars past the ridge."""
    for x, z in STACKS:
        rail_stack(b, x, z, "x", base=BASES[("stack", x, z)])
        _keep(rect(x - 9.0, x + 9.0, z - 4.0, z + 4.0))


def _coal(b: ArenaArea, rng: random.Random, land: Land) -> None:
    for x, z in COAL:
        coal_heap(b, x, z, rng, base=BASES[("coal", x, z)])
        _keep(rect(x - 5.0, x + 5.0, z - 5.0, z + 5.0))
    for x, z in TOWERS:
        _tower(b, x, z, BASES[("tower", x, z)])
        _keep(rect(x - 10.0, x + 22.0, z - 10.0, z + 10.0))


# ================================================================ scatter
def _scatter(b: ArenaArea, rng: random.Random, land: Land) -> None:
    """Junipers and sage over the hills, outcrops, a few skulls -- never on
    a line, a building or a gulch edge."""
    paths = (LANE_A, LANE_B)
    tries = 0
    placed = 0
    hx, hz = HALF
    while placed < 150 and tries < 1600:
        tries += 1
        x, z = rng.uniform(-hx + 10.0, hx - 10.0), rng.uniform(-hz + 10.0, hz - 10.0)
        if GULCH[0] - 10 < x < GULCH[1] + 10:
            continue
        if not rails.clear_of(rect(x - 4.0, x + 4.0, z - 4.0, z + 4.0), paths, 12.0):
            continue
        if _blocked(x, z) or any(k[0] - 6 < x < k[1] + 6 and k[2] - 6 < z < k[3] + 6 for k in KEEP):
            continue
        base = land.height(x, z)
        if abs(land.height(x + 3.0, z) - base) > 0.6 or abs(land.height(x, z + 3.0) - base) > 0.6:
            continue
        roll = rng.random()
        if roll < 0.32:
            juniper(b, x, z, base=base, s=rng.uniform(0.8, 1.3))
        elif roll < 0.82:
            sage(b, x, z, base=base, s=rng.uniform(0.8, 1.4))
        elif roll < 0.97:
            outcrop(b, x, z, rng.uniform(3.0, 6.0), rng.uniform(1.4, 3.0), rng.uniform(3.0, 5.0),
                    base=base, colour=rng.choice([ROCK, ROCK_PALE]))
        else:
            skull(b, x, z, base=base, yaw=rng.uniform(0, 6.3))
        KEEP.append(rect(x - 3.0, x + 3.0, z - 3.0, z + 3.0))
        placed += 1


def _tower(b: ArenaArea, x: float, z: float, base: float) -> None:
    """The Halfway Tank's water tower, on its levelled ground: the tank on
    stilts, the walkway round it (a perch) and the crates up to it."""
    height = 16.0
    for dx in (-3.5, 3.5):
        for dz in (-3.5, 3.5):
            b.box([x + dx, base + height / 2.0, z + dz], [1.0, height, 1.0], WOOD_DARK)
    slab(b, rect(x - 8.0, x + 8.0, z - 8.0, z + 8.0), base + height + 0.6, 0.6, WOOD)
    b.cyl([x, base + height + 0.6 + 4.5, z], [9.0, 9.0, 9.0], "#7a5335")
    b.cone([x, base + height + 0.6 + 9.0 + 1.6, z], [10.0, 3.2, 10.0], "#4a3a2a", collide=False)
    for k in range(3):
        b.cyl([x, base + height + 0.6 + 1.5 + k * 3.0, z], [9.1, 0.35, 9.1], rails.IRON, material="metal")
    top = height + 0.6
    for k in range(3):
        h = top * (3 - k) / 4.0
        cx = x + 10.2 + k * 4.0
        b.box([cx, base + h / 2.0, z], [4.0, h, 4.4], (WOOD, WOOD_LIGHT, "#9a7048")[k], studs=True)
    b.mark("perch", x, base + height + 0.6, z)
