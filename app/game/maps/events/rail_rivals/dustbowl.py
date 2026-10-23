"""Dustbowl Gulch -- a gold town at the mouth of a red-rock canyon, late
afternoon.

Layout (north is -z; both tracks run west to east)::

    z -230 ===================== THE CANYON WALL =============================
           RATTLESNAKE           BONANZA MINE  (headframe, stamp mill,     COPPER BLUFF
           SIDING   -------\\     ore bins, the powder shed, tents)   /---- TERMINUS
             lane a start   \\                                      /   lane b end
    z    0                   \\======= JUNCTION SQUARE =========== /
           DUSTBOWL          /        (signal tower, gates)         \\    GOLD CREEK
           DEPOT   ---------/   corrals, windmill, the coaling stage  \\--- STATION
             lane b start      MAIN STREET: saloon, bank, hotel, church  lane a end
    z +230 ===================== THE TOWN'S BACK LOTS =======================

Lane ``a`` starts in the canyon and finishes in town; lane ``b`` is its
mirror image, starting in town and finishing in the canyon, so both teams
race half the canyon and half the town and meet in the middle, where the
two tracks cross on the square.  Main Street has the rails laid down the
middle of it at both ends of town.
"""
from __future__ import annotations

import math
import random

from ..kit import (
    WARM, WOOD, WOOD_DARK, WOOD_LIGHT, ArenaArea, Surfaces, backdrop, building,
    gable, lantern, rect, room_walls, sign_decal, slab, threshold, wall_sign)
from . import rails
from .rails import (
    barrel, beside, boardwalk, boxcar, buffer_stop, caboose, cactus, clear_of,
    coal_heap, crate_stack, depot, false_front, fence_run, fillet, flatcar,
    handcar, hitching_post, lay_track, length, lever, mile_post, mirror, rock,
    saloon_interior, sleeper_pile, stair, store_interior, storeyed, telegraph,
    wagon, water_tower, windmill)

HALF = (390.0, 230.0)
SKY = {"top": "#3a5f9a", "horizon": "#f2b06a", "sun": [0.62, 0.32, -0.45],
       "clouds": 0.28, "tint": "#ffd8a0"}
AMBIENT = "#b49a80"
GROUND = "#c8a06e"
FOG = 900.0

SAND = "#c8a06e"
SAND_DARK = "#b48a5a"
CANYON = "#9a5a3a"
CANYON_DARK = "#7a442c"
CANYON_LIGHT = "#b8724a"
ADOBE = "#c89a6a"

LANE_A = fillet([(-362.0, -150.0), (-230.0, -150.0), (0.0, 0.0), (230.0, 150.0),
                 (362.0, 150.0)], radius=64.0, step=5.0)
LANE_B = mirror(LANE_A)

# what the mid-field pieces stand on, so the scattered rocks, cacti and
# crates laid afterwards keep off them
KEEP: list = []


def _free(area, margin: float = 3.0) -> bool:
    x0, x1, z0, z1 = area
    return all(x1 + margin <= k[0] or x0 - margin >= k[1] or
               z1 + margin <= k[2] or z0 - margin >= k[3] for k in KEEP)


def build(b: ArenaArea) -> None:
    rng = random.Random(0xD057)
    del KEEP[:]
    b.extra.update({"accent": "#f2a03a", "twist": "signal", "lanes": {"a": _world(b, LANE_A),
                                                   "b": _world(b, LANE_B)},
                    "names": {"a": "the canyon line", "b": "the Main Street line"}})
    _ground(b)
    _edge(b, rng)
    s = Surfaces(b)
    lay_track(b, LANE_A)
    lay_track(b, LANE_B)
    _yards(b)
    _stations(b)
    _depots(b)
    _levers(b)
    for kind, (hx, hz) in (("depot", (22.0, 10.0)), ("lever", (5.0, 5.0))):
        for entry in b.points.get(kind, []):
            x, z = entry["p"][0] - b.ox, entry["p"][2] - b.oz
            KEEP.append(rect(x - hx, x + hx, z - hz, z + hz))
    _square(b, rng)
    _town(b, s, rng)
    _midfield(b, rng)
    _canyon(b, rng)
    _coaling(b, rng)
    _scatter(b, rng)
    telegraph(b, LANE_A, -1.0)
    telegraph(b, LANE_B, 1.0)
    for f, label in ((0.25, "MP 1"), (0.5, "MP 2"), (0.75, "MP 3")):
        mile_post(b, LANE_A, f, 1.0, label)
        mile_post(b, LANE_B, f, -1.0, label)
    for x, z, name in ((-345, -150, "Rattlesnake Siding"), (-345, 150, "Dustbowl Depot"),
                       (0, 0, "Junction Square"), (345, 150, "Gold Creek Station"),
                       (345, -150, "Copper Bluff"), (0, -205, "the Bonanza Mine"),
                       (-95, -185, "the stamp mill"), (95, -190, "the powder shed"),
                       (-110, 168, "the Gilded Spur saloon"), (40, 180, "the bank"),
                       (150, 178, "the hotel"), (-30, 70, "the corrals"),
                       (-200, 0, "the west coaling stage"), (200, 0, "the east coaling stage"),
                       (260, 205, "the church"), (-140, -26, "the boxcar siding"),
                       (-150, 40, "Boot Hill"), (140, 26, "the timber siding"),
                       (150, -38, "the prospectors' camp"), (0, -112, "the Devil's Gate"),
                       (-140, -159, "the lookout butte"), (28, 58, "the bandstand")):
        b.landmark(float(x), float(z), name)
    b.camera(-300.0, 70.0, -30.0, 0.0, 0.0, 0.0)
    b.camera(260.0, 60.0, 40.0, 0.0, 4.0, 0.0)
    b.camera(0.0, 80.0, 200.0, 0.0, 0.0, -40.0)


def _world(b: ArenaArea, path):
    return [b.at(x, 0.0, z) for x, z in path]


# ================================================================== ground
def _ground(b: ArenaArea) -> None:
    hx, hz, m = b.half_x + b.margin, b.half_z + b.margin, b.margin
    del m
    # the canyon's red rock gives way to the town's sand along a ragged line,
    # band by band, never a ruler-straight one
    rng = random.Random(0x5A4D)
    bands = 15
    for i in range(bands):
        x0 = -hx + i * 2 * hx / bands
        x1 = -hx + (i + 1) * 2 * hx / bands
        edge = round(rng.uniform(-16.0, 12.0), 1)
        slab(b, rect(x0, x1, -hz, edge), 0.0, 0.6, CANYON_LIGHT, studs=True)
        slab(b, rect(x0, x1, edge, hz), 0.0, 0.6, SAND, studs=True)
    slab(b, rect(-hx, hx, -hz, hz), -0.6, 5.4, "#6a4a32")


def _edge(b: ArenaArea, rng: random.Random) -> None:
    hx, hz, m = b.half_x, b.half_z, b.margin
    # the canyon wall to the north is the tallest thing in the gulch
    room_walls(b, rect(-hx - m, hx + m, -hz - m, -hz), m, 0.0, 70.0, CANYON_DARK,
               sides=("z-",))
    room_walls(b, rect(-hx - m, hx + m, -hz - m, hz + m), m, 0.0, 34.0, CANYON,
               sides=("x-", "x+", "z+"))
    for i in range(22):
        x = -hx + (i + 0.5) * (2 * hx) / 22.0
        top = rng.uniform(12.0, 34.0)
        b.box([x, 70.0 + top / 2.0, -hz - m / 2.0], [2 * hx / 22.0 - 1.2, top, m + 1.0],
              rng.choice([CANYON_DARK, CANYON, "#8a4c32"]), collide=False)
    # the inside face of the canyon wall: buttresses and ledges, solid, so the
    # wall is a cliff and not a plain plane
    for i in range(16):
        x = -hx + 20.0 + i * (2 * hx - 40.0) / 15.0 + rng.uniform(-6, 6)
        if abs(x) < 26.0:
            continue                      # the mine's portal is there
        d = rng.uniform(8.0, 20.0)
        h = rng.uniform(28.0, 60.0)
        w = rng.uniform(14.0, 28.0)
        b.box([x, h / 2.0, -hz + d / 2.0], [w, h, d], rng.choice([CANYON, CANYON_DARK]))
        b.box([x + w * 0.1, h + 3.0, -hz + d * 0.4], [w * 0.6, 6.0, d * 0.7], CANYON_DARK)
    backdrop(b, "mesas", 0.0, rng, ["#a86a4a", "#b87a52", "#985a3e"],
             sides=("x-", "x+", "z+"), depth=140.0)


# =================================================================== yards
def _yards(b: ArenaArea) -> None:
    """The two starting yards at the west end, a freight shed between them
    so neither team starts in the other's sights."""
    for lane, path, z, name, roof in (("a", LANE_A, -150.0, "RATTLESNAKE SIDING", "#6a3a2a"),
                                      ("b", LANE_B, 150.0, "DUSTBOWL DEPOT", "#3a4a6a")):
        side = -1.0 if z < 0 else 1.0
        pz = z + side * 15.0
        rails.platform(b, rect(-376.0, -322.0, pz - 6.0, pz + 6.0))
        stair(b, "x", -319.0, -322.0, pz - 3.0, pz + 3.0, 0.0, 1.2, WOOD)
        rails.shelter(b, rect(-370.0, -334.0, pz - 3.4, pz + 3.4), 1.2, 9.0, roof)
        b.box([-352.0, 1.2 + 9.6 + 1.2, pz], [30.0, 2.4, 0.5], rails.CREAM,
              decal=sign_decal(name, rails.CREAM, "#3a2414", 12.5))
        # twelve spawns, between the shelter's posts and past its ends
        for sx in (-373.0, -362.0, -354.0, -346.0, -338.0, -327.0):
            for w in (-1.4, 1.4):
                b.team_spawn(lane, sx, 1.51, pz + w, math.pi / 2.0, 0)
        buffer_stop(b, -372.0, z, math.pi / 2.0, roof)
        # the engine shed behind the platform
        shed = rect(-386.0, -330.0, pz + side * 9.0, pz + side * 33.0)
        building(b, shed, 0.0, 16.0, "#7a5335", roof_colour=roof,
                 doors={("x+"): [(min(shed[2], shed[3]) + 4.0, max(shed[2], shed[3]) - 4.0, 13.0)]},
                 windows={"z-" if side > 0 else "z+": [(-376.0, -360.0, 6.0, 10.0),
                                                       (-354.0, -338.0, 6.0, 10.0)]},
                 glass=True, lights=WARM)
        gable(b, shed, 17.2, roof, "x", 4, 1.4, 0.6)
        lantern(b, -326.0, 9.8, pz, WARM)
        b.mark("start", -362.0, 0.5, z, lane=lane)
    # the long freight shed that keeps the two yards apart
    shed = rect(-382.0, -318.0, -70.0, 70.0)
    building(b, shed, 0.0, 18.0, "#8a6040", roof_colour="#4a3a2e",
             doors={"x+": [(-30.0, -14.0, 12.0), (14.0, 30.0, 12.0)]},
             windows={"z-": [(-370.0, -350.0, 8.0, 12.0)], "z+": [(-370.0, -350.0, 8.0, 12.0)]},
             glass=True, lights=WARM)
    gable(b, shed, 19.2, "#4a3a2e", "z", 5, 1.5, 1.0)
    for k in range(4):
        rails.crate_stack(b, -370.0 + (k % 2) * 16.0, -40.0 + k * 22.0, random.Random(k))
    wall_sign(b, -317.65, 14.0, 0.0, 40.0, 4.0,
              sign_decal("DUSTBOWL FREIGHT CO.", "#3a2414", rails.GOLD, 10.0), "x+", "#3a2414")


def _stations(b: ArenaArea) -> None:
    """The two termini at the east end."""
    for lane, path, z, name, roof in (("a", LANE_A, 150.0, "GOLD CREEK STATION", "#3a4a6a"),
                                      ("b", LANE_B, -150.0, "COPPER BLUFF TERMINUS", "#6a3a2a")):
        side = 1.0 if z > 0 else -1.0
        pz = z + side * 15.0
        rails.platform(b, rect(310.0, 380.0, pz - 6.0, pz + 6.0))
        stair(b, "x", 307.0, 310.0, pz - 3.0, pz + 3.0, 0.0, 1.2, WOOD)
        rails.shelter(b, rect(318.0, 372.0, pz - 3.4, pz + 3.4), 1.2, 9.0, roof)
        b.box([345.0, 1.2 + 9.6 + 1.2, pz], [44.0, 2.4, 0.5], rails.GOLD,
              decal=sign_decal(name, rails.GOLD, "#3a2414", 18.0))
        buffer_stop(b, 372.0, z, math.pi / 2.0, roof)
        house = rect(326.0, 378.0, pz + side * 8.0, pz + side * 30.0)
        building(b, house, 0.0, 14.0, "#9a6a44", roof_colour=roof,
                 doors={"x-": [(min(house[2], house[3]) + 7.0, max(house[2], house[3]) - 7.0, 9.0)]},
                 windows={"z-" if side > 0 else "z+": [(330.0, 344.0, 4.0, 9.0),
                                                       (356.0, 370.0, 4.0, 9.0)]},
                 glass=True, lights=WARM)
        threshold(b, house, "x-", (min(house[2], house[3]) + 7.0, max(house[2], house[3]) - 7.0))
        gable(b, house, 15.2, roof, "x", 4, 1.3, 0.8)
        # the station bell on a post: the finish line
        b.box([314.0, 6.5, z + side * 9.0], [0.8, 13.0, 0.8], WOOD_DARK)
        b.box([314.0, 12.6, z + side * 9.0], [2.2, 2.2, 2.2], rails.GOLD, material="metal",
              collide=False)
        b.mark("finish", 362.0, 0.5, z, lane=lane)


# ================================================================== depots
def _depots(b: ArenaArea) -> None:
    depot(b, "a", LANE_A, 1 / 3.0, 1.0, "HOODOO HALT", 1, "#6a3a2a")
    depot(b, "a", LANE_A, 2 / 3.0, -1.0, "CORRAL CROSSING", 2, "#3a4a6a")
    depot(b, "b", LANE_B, 1 / 3.0, -1.0, "CORRAL CROSSING WEST", 1, "#3a4a6a")
    depot(b, "b", LANE_B, 2 / 3.0, 1.0, "HOODOO HALT EAST", 2, "#6a3a2a")


def _levers(b: ArenaArea) -> None:
    for lane, path, sides in (("a", LANE_A, (-1.0, 1.0)), ("b", LANE_B, (1.0, -1.0))):
        for index, (f, side) in enumerate(zip(rails.LEVER_FRACTIONS, sides)):
            lever(b, lane, path, f, side, index)


# ========================================================== junction square
def _square(b: ArenaArea, rng: random.Random) -> None:
    """Where the two lines cross: a signal tower to fight over, crossing
    gates, troughs and hay for cover."""
    # the signal tower, west of the crossing, between the two tracks
    tx, tz = -46.0, 0.0
    building(b, rect(tx - 8.0, tx + 8.0, tz - 8.0, tz + 8.0), 0.0, 12.0, "#8a5a3a",
             roof_colour="#3a2a22", floor_colour="#6a4e34",
             doors={"x-": [(-3.0, 3.0, 8.5)]},
             windows={"z-": [(tx - 5.0, tx + 5.0, 4.0, 8.0)], "z+": [(tx - 5.0, tx + 5.0, 4.0, 8.0)],
                      "x+": [(-5.0, 5.0, 4.0, 8.0)]}, glass=False, lights=WARM)
    threshold(b, rect(tx - 8.0, tx + 8.0, tz - 8.0, tz + 8.0), "x-", (-3.0, 3.0))
    # the signal cabin on top, set back from the roof's edge so there is a
    # walk round its front, and an outside stair up to that walk
    building(b, rect(tx - 5.0, tx + 5.0, tz - 5.0, tz + 5.0), 13.2, 9.0, "#9a6a44",
             roof_colour="#3a2a22", floor_colour="",
             doors={"z+": [(tx - 2.5, tx + 2.5, 13.2 + 7.0)]},
             windows={"z-": [(tx - 3.5, tx + 3.5, 16.0, 20.0)],
                      "x+": [(-3.5, 3.5, 16.0, 20.0)], "x-": [(-3.5, 3.5, 16.0, 20.0)]},
             glass=True, lights=WARM, studs_roof=True)
    stair(b, "z", tz + 24.0, tz + 8.0, tx - 12.0, tx - 8.0, 0.0, 13.2, WOOD)
    slab(b, rect(tx - 12.0, tx - 8.0, tz + 4.0, tz + 8.0), 13.2, 1.2, WOOD)
    b.mark("perch", tx, 13.2, tz + 6.5)
    # the cabin itself: whoever holds it sets the junction signal
    b.mark("signal", tx, 13.2, tz, r=4.4, top=22.2)
    for k, colour in enumerate(("#ff3a2a", "#3aff6a")):
        b.box([tx + 5.2, 20.6 + k * 1.0, tz], [0.4, 1.0, 1.0], colour, material="neon",
              collide=False)
    wall_sign(b, tx, 10.0, tz - 8.35, 12.0, 2.0,
              sign_decal("JUNCTION", rails.CREAM, "#3a2414", 6.0), "z-", rails.CREAM)
    # crossbuck signs at the four approaches
    for sx, sz in ((-22.0, -26.0), (22.0, 26.0), (-22.0, 26.0), (22.0, -26.0)):
        b.box([sx, 4.0, sz], [0.6, 8.0, 0.6], rails.CREAM)
        for rot in (0.6, -0.6):
            b.box([sx, 7.4, sz], [6.0, 0.8, 0.2], rails.CREAM, r=[0, 0, rot], collide=False,
                  decal=sign_decal("RAILROAD", rails.CREAM, "#1a1a1a", 7.5))
    # troughs, hay and a broken wagon: cover round the crossing
    for x, z, along in ((30.0, -6.0, "z"), (-12.0, 34.0, "x"), (14.0, -34.0, "x")):
        lx, lz = (8.0, 3.0) if along == "x" else (3.0, 8.0)
        b.box([x, 1.2, z], [lx, 2.4, lz], WOOD_DARK)
        b.box([x, 2.3, z], [lx - 0.8, 0.2, lz - 0.8], "#4a7a9a", material="glass", collide=False)
    for x, z in ((40.0, 12.0), (-36.0, 26.0), (58.0, -24.0), (-58.0, -20.0)):
        b.box([x, 2.0, z], [6.0, 4.0, 5.0], "#d8b860", studs=True)
        b.box([x + 0.4, 5.0, z], [4.4, 2.0, 3.6], "#c8a850", studs=True)
    wagon(b, 64.0, 2.0, "z", "#d8c8a8")


# ==================================================================== town
def _town(b: ArenaArea, s: Surfaces, rng: random.Random) -> None:
    lanes = (LANE_A, LANE_B)
    # north side of Main Street (facing south), from the west end to the east
    north = [(-300.0, "MERCANTILE", "store"), (-258.0, "BARBER", "store"),
             (-150.0, "GULCH GAZETTE", "store"), (-108.0, "THE GILDED SPUR", "saloon"),
             (-62.0, "ASSAY OFFICE", "store"), (-20.0, "POST OFFICE", "store"),
             (22.0, "SHERIFF", "jail"), (64.0, "BLACKSMITH", "smith"),
             (106.0, "UNDERTAKER", "store"), (150.0, "BATHHOUSE", "store"),
             (190.0, "FEED & SEED", "store")]
    for x, name, kind in north:
        area = rect(x - 18.0, x + 18.0, 112.0, 134.0)
        if not clear_of(rect(area[0] - 1.0, area[1] + 1.0, area[2], 140.0 + 6.0), lanes, 9.0):
            continue
        colour = rng.choice(["#9a6a44", "#8a5a3a", "#a87a50", "#7a5335", ADOBE])
        if kind == "saloon":
            _saloon(b, area, "z+", name)
        elif kind == "jail":
            _jail(b, area, "z+")
        elif kind == "smith":
            _smithy(b, area, "z+")
        else:
            false_front(b, area, "z+", colour, name, rng=rng,
                        interior=store_interior)
    # south side of Main Street (facing north)
    south = [(-330.0, "LIVERY", "barn"), (-282.0, "DRY GOODS", "store"),
             (-236.0, "TELEGRAPH", "store"), (-190.0, "LAUNDRY", "store"),
             (-146.0, "CHINA & GLASS", "store"), (-100.0, "DOCTOR", "store"),
             (-50.0, "OPERA HOUSE", "opera"), (40.0, "DUSTBOWL SAVINGS & LOAN", "bank"),
             (150.0, "GRAND PALACE HOTEL", "hotel"), (224.0, "GENERAL STORE", "store"),
             (266.0, "SADDLERY", "store"), (306.0, "GUNSMITH", "store")]
    for x, name, kind in south:
        wide = 30.0 if kind in ("bank", "opera") else (34.0 if kind == "hotel" else 18.0)
        area = rect(x - wide, x + wide, 166.0, 190.0) if kind in ("bank", "hotel", "opera") \
            else rect(x - 18.0, x + 18.0, 166.0, 188.0)
        if not clear_of(rect(area[0], area[1], 160.0 - 6.0, area[3]), lanes, 9.0):
            continue
        colour = rng.choice(["#9a6a44", "#8a5a3a", "#a87a50", "#b08458", ADOBE])
        if kind == "bank":
            _bank(b, area)
        elif kind == "hotel":
            _hotel(b, area)
        elif kind == "opera":
            false_front(b, area, "z-", "#8a3a2a", name, rng=rng, front=8.0,
                        sign_bg="#2a1410", sign_fg="#ffd27a", height=14.0)
        elif kind == "barn":
            _barn(b, area)
        else:
            false_front(b, area, "z-", colour, name, rng=rng, interior=store_interior)
    # the church at the east end of town, on its own, steeple and bell
    church = rect(246.0, 282.0, 196.0, 222.0)
    building(b, church, 0.0, 16.0, "#efe6d6", roof_colour="#5a4a42", floor_colour="#8a6a4a",
             doors={"z-": [(258.0, 270.0, 11.0)]},
             windows={"x-": [(200.0, 206.0, 6.0, 12.0), (212.0, 218.0, 6.0, 12.0)],
                      "x+": [(200.0, 206.0, 6.0, 12.0), (212.0, 218.0, 6.0, 12.0)]},
             glass=True, lights=WARM)
    threshold(b, church, "z-", (258.0, 270.0))
    gable(b, church, 17.2, "#5a4a42", "z", 5, 1.6, 0.8)
    b.box([264.0, 30.0, 200.0], [9.0, 22.0, 9.0], "#efe6d6")
    b.cone([264.0, 47.0, 200.0], [10.0, 12.0, 10.0], "#5a4a42", collide=False)
    b.box([264.0, 36.0, 195.4], [3.0, 3.0, 0.4], rails.GOLD, material="metal", collide=False)
    b.box([264.0, 54.0, 200.0], [0.6, 4.0, 0.6], rails.CREAM, collide=False)
    b.box([264.0, 54.6, 200.0], [2.6, 0.6, 0.6], rails.CREAM, collide=False)
    # hitching posts and barrels along the boardwalks
    for x in (-280.0, -170.0, -80.0, 10.0, 120.0, 210.0, 290.0):
        if clear_of(rect(x - 4.0, x + 4.0, 141.0, 143.0), lanes, 6.0):
            hitching_post(b, x, 142.6, "x")
        if clear_of(rect(x - 2.0, x + 6.0, 157.0, 159.0), lanes, 6.0):
            hitching_post(b, x + 14.0, 157.4, "x")
    # back lots behind the south side: outhouses, a well, a wagon
    for x in (-300.0, -200.0, -120.0, 90.0, 200.0):
        b.box([x, 4.5, 205.0], [5.0, 9.0, 5.0], "#7a5335")
        b.box([x, 9.4, 205.0], [6.0, 0.8, 6.0], "#5a4632")
    b.cyl([-20.0, 1.6, 210.0], [6.0, 3.2, 6.0], "#8a8478")
    b.box([-20.0, 6.5, 210.0], [7.0, 0.6, 1.0], WOOD_DARK)
    for dx in (-3.2, 3.2):
        b.box([-20.0 + dx, 4.8, 210.0], [0.6, 2.8, 0.6], WOOD_DARK)
    wagon(b, 60.0, 212.0, "x")
    # between Main Street and the square: corrals, a windmill, hay
    for cx, cz in ((-40.0, 76.0), (60.0, 64.0)):
        if not clear_of(rect(cx - 22.0, cx + 22.0, cz - 16.0, cz + 16.0), lanes, 8.0):
            continue
        fence_run(b, cx - 22.0, cz - 16.0, cx + 22.0, cz - 16.0)
        fence_run(b, cx - 22.0, cz + 16.0, cx + 22.0, cz + 16.0)
        fence_run(b, cx - 22.0, cz - 16.0, cx - 22.0, cz - 2.0)
        fence_run(b, cx - 22.0, cz + 2.0, cx - 22.0, cz + 16.0)
        fence_run(b, cx + 22.0, cz - 16.0, cx + 22.0, cz + 16.0)
        b.box([cx, 2.0, cz], [6.0, 4.0, 5.0], "#d8b860", studs=True)
    windmill(b, 10.0, 92.0)


def _saloon(b: ArenaArea, area, facing: str, name: str) -> None:
    """The Gilded Spur: two storeys, a balcony over the boardwalk, a bar
    downstairs and a stair up the back to the rooms."""
    x0, x1, z0, z1 = area
    mid = (x0 + x1) / 2.0
    front = [(x0 + 4.0, x0 + 12.0), (x1 - 12.0, x1 - 4.0)]
    well = rect(x0 + 2.0, x0 + 18.0, z0 + 2.0, z0 + 9.0) if facing == "z+" else \
        rect(x0 + 2.0, x0 + 18.0, z1 - 9.0, z1 - 2.0)
    storeyed(b, area, [11.0, 11.0], "#8a3a2a", roof="#3a2a22",
             doors={facing: [(mid - 4.0, mid + 4.0, 8.5)]},
             windows=[{facing: [(a, c, 3.0, 7.0) for a, c in front]},
                      {facing: [(a, c, 14.0, 19.0) for a, c in front] +
                       [(mid - 3.0, mid + 3.0, 11.0, 19.0)]}],
             wells=[well])
    threshold(b, area, facing, (mid - 4.0, mid + 4.0))
    # the stair up the back wall, under its well
    if facing == "z+":
        stair(b, "x", x0 + 18.0, x0 + 3.0, z0 + 3.0, z0 + 8.0, 0.4, 11.0)
        saloon_interior(b, rect(x0, x1, z0 + 9.0, z1), "z-")
    else:
        stair(b, "x", x0 + 18.0, x0 + 3.0, z1 - 8.0, z1 - 3.0, 0.4, 11.0)
        saloon_interior(b, rect(x0, x1, z0, z1 - 9.0), "z+")
    # the balcony out front: the porch roof, stepped onto through the
    # upstairs door, with a solid rail round it
    depth = 6.0
    walk = rect(x0, x1, z1, z1 + depth) if facing == "z+" else rect(x0, x1, z0 - depth, z0)
    slab(b, walk, 0.8, 0.8, WOOD_LIGHT, studs=True)
    for k in range(4):
        px = x0 + 0.6 + k * (x1 - x0 - 1.2) / 3.0
        pz = walk[3] - 0.6 if facing == "z+" else walk[2] + 0.6
        b.box([px, 0.8 + 5.1, pz], [0.8, 10.2, 0.8], WOOD_DARK)
    slab(b, walk, 11.6, 0.6, WOOD)
    rail_z = walk[3] - 0.3 if facing == "z+" else walk[2] + 0.3
    b.box([mid, 12.5, rail_z], [x1 - x0, 1.8, 0.6], WOOD_DARK)
    top = 22.0 + 1.2
    face_z = z1 - 1.0 if facing == "z+" else z0 + 1.0
    b.box([mid, top + 4.0, face_z], [x1 - x0, 8.0, 2.0], "#8a3a2a")
    wall_sign(b, mid, top + 4.0, z1 + 0.35 if facing == "z+" else z0 - 0.35, 28.0, 5.0,
              sign_decal(name, "#2a1410", rails.GOLD, 5.6), facing, "#2a1410")
    b.mark("perch", mid, 11.6, (walk[2] + walk[3]) / 2.0)


def _jail(b: ArenaArea, area, facing: str) -> None:
    x0, x1, z0, z1 = area
    mid = (x0 + x1) / 2.0
    building(b, area, 0.0, 12.0, "#8a8478", roof_colour="#4a4642", floor_colour="#6a6460",
             doors={facing: [(mid - 3.5, mid + 3.5, 8.5)]},
             windows={facing: [(x0 + 4.0, x0 + 10.0, 4.0, 8.0)]}, boards=True, lights=WARM)
    threshold(b, area, facing, (mid - 3.5, mid + 3.5))
    # the cell at the back: bars you can shoot through, not walk through
    cz = z0 + 6.0 if facing == "z+" else z1 - 6.0
    for k in range(8):
        b.box([x1 - 14.0 + k * 1.6, 0.4 + 4.2, cz], [0.35, 8.4, 0.35], "#3a3a3a",
              material="metal")
    boardwalk(b, area, facing, 6.0, 8.8)
    wall_sign(b, mid, 13.6, z1 + 0.35 if facing == "z+" else z0 - 0.35, 16.0, 2.4,
              sign_decal("SHERIFF", "#2a2a2a", rails.GOLD, 6.6), facing, "#2a2a2a")


def _smithy(b: ArenaArea, area, facing: str) -> None:
    """Open-fronted: a forge glowing at the back, an anvil, a water barrel."""
    x0, x1, z0, z1 = area
    mid = (x0 + x1) / 2.0
    building(b, area, 0.0, 12.0, "#5a4a3e", roof_colour="#3a3230",
             doors={facing: [(x0 + 3.0, x1 - 3.0, 10.0)]}, lights=WARM)
    back = z0 + 4.0 if facing == "z+" else z1 - 4.0
    b.box([mid, 2.2, back], [8.0, 4.4, 4.0], "#6a6460")
    b.box([mid, 4.5, back], [6.0, 0.3, 3.0], "#ff7a2a", material="neon", collide=False)
    b.box([mid, 9.0, back], [3.0, 6.0, 3.0], "#4a4642")
    b.box([mid + 6.0, 1.6, (z0 + z1) / 2.0], [3.0, 3.2, 1.6], "#3a3a3a", material="metal")
    barrel(b, x0 + 4.0, (z0 + z1) / 2.0, "#5a6a7a")


def _bank(b: ArenaArea, area) -> None:
    """Dustbowl Savings & Loan: brick, a vault at the back, a roof you can
    climb onto from the stair in the side alley."""
    x0, x1, z0, z1 = area
    mid = (x0 + x1) / 2.0
    building(b, area, 0.0, 16.0, "#9a4f3a", roof_colour="#5a3a2e", floor_colour="#8a7a6a",
             doors={"z-": [(mid - 4.0, mid + 4.0, 10.0)]},
             windows={"z-": [(x0 + 5.0, x0 + 15.0, 4.0, 10.0), (x1 - 15.0, x1 - 5.0, 4.0, 10.0)]},
             glass=True, lights=WARM, parapet=2.0)
    threshold(b, area, "z-", (mid - 4.0, mid + 4.0))
    b.box([mid, 0.4 + 2.0, z0 + 10.0], [x1 - x0 - 12.0, 4.0, 2.0], WOOD_DARK)
    b.box([mid, 0.4 + 5.0, z1 - 4.0], [12.0, 10.0, 4.0], "#5a5a5e", material="metal")
    b.cyl([mid, 0.4 + 5.0, z1 - 6.1], [5.0, 0.3, 5.0], rails.GOLD, material="metal",
          collide=False, r=[math.pi / 2.0, 0, 0])
    stair(b, "z", z0 + 2.0, z1 - 2.0, x1 + 1.0, x1 + 5.0, 0.0, 17.2, "#7a7068")
    wall_sign(b, mid, 13.0, z0 - 0.35, 40.0, 3.0,
              sign_decal("DUSTBOWL SAVINGS & LOAN", "#2a1410", rails.GOLD, 13.0), "z-", "#2a1410")
    b.mark("perch", mid, 17.2, mid * 0 + (z0 + z1) / 2.0)


def _hotel(b: ArenaArea, area) -> None:
    """The Grand Palace Hotel: two storeys of rooms over Main Street, a
    balcony the length of the front, and a stair to the roof round the
    side for anybody who wants the best view of the street."""
    x0, x1, z0, z1 = area
    mid = (x0 + x1) / 2.0
    bays = [(x0 + 5.0 + k * 13.0, x0 + 11.0 + k * 13.0) for k in range(5)]
    well = rect(x0 + 2.0, x0 + 18.0, z1 - 9.0, z1 - 2.0)
    storeyed(b, area, [11.0, 11.0], "#b08458", roof="#4a3a2e",
             doors={"z-": [(mid - 5.0, mid + 5.0, 9.0)]},
             windows=[{"z-": [bays[0], bays[1], bays[3], bays[4]] and
                       [(a, c, 3.0, 8.0) for a, c in (bays[0], bays[1], bays[3], bays[4])]},
                      {"z-": [(a, c, 14.0, 19.0) for a, c in bays],
                       "x-": [(z0 + 6.0, z0 + 12.0, 14.0, 19.0)],
                       "x+": [(z0 + 6.0, z0 + 12.0, 14.0, 19.0)]}],
             wells=[well])
    threshold(b, area, "z-", (mid - 5.0, mid + 5.0))
    stair(b, "x", x0 + 18.0, x0 + 3.0, z1 - 8.0, z1 - 3.0, 0.4, 11.0)
    # the front desk and the lobby's settees
    b.box([mid, 0.4 + 2.0, z1 - 14.0], [18.0, 4.0, 2.4], WOOD_DARK)
    for dx in (-14.0, 14.0):
        b.box([mid + dx, 0.4 + 1.2, z0 + 8.0], [8.0, 2.4, 3.0], "#6a2a2a")
    # the balcony out front at the first floor
    walk = rect(x0, x1, z0 - 6.0, z0)
    slab(b, walk, 0.8, 0.8, WOOD_LIGHT, studs=True)
    for k in range(6):
        b.box([x0 + 0.6 + k * (x1 - x0 - 1.2) / 5.0, 0.8 + 5.1, z0 - 5.4], [0.8, 10.2, 0.8],
              WOOD_DARK)
    slab(b, walk, 11.6, 0.6, WOOD)
    b.box([mid, 12.5, z0 - 5.7], [x1 - x0, 1.8, 0.6], WOOD_DARK)
    # the stair up the east side to the roof
    stair(b, "z", z1 + 0.0, z0 + 2.0, x1 + 0.0, x1 + 5.0, 0.0, 23.2)
    b.box([mid, 26.4, z0 + 1.0], [x1 - x0, 6.4, 2.0], "#b08458")
    wall_sign(b, mid, 26.4, z0 - 0.35, 48.0, 4.6,
              sign_decal("GRAND PALACE HOTEL", "#3a1a12", rails.GOLD, 10.4), "z-", "#3a1a12")
    b.mark("perch", mid, 23.2, (z0 + z1) / 2.0)
    b.mark("perch", mid, 11.6, z0 - 3.0)


def _barn(b: ArenaArea, area) -> None:
    x0, x1, z0, z1 = area
    building(b, area, 0.0, 16.0, "#8a2e24", roof_colour="#4a2a22",
             doors={"z-": [(x0 + 8.0, x1 - 8.0, 13.0)]}, lights=WARM)
    gable(b, area, 17.2, "#4a2a22", "z", 5, 1.6, 0.8)
    for k in range(3):
        b.box([x0 + 6.0 + k * 10.0, 2.0, z1 - 5.0], [6.0, 4.0, 5.0], "#d8b860", studs=True)


# ================================================================ mid-field
def _midfield(b: ArenaArea, rng: random.Random) -> None:
    """What stands between the tracks and the edges: two sidings of parked
    cars (cover a pusher can duck behind and a raider can stand on), Boot
    Hill, a prospectors' camp, the Devil's Gate arch, a lookout butte, the
    bandstand, and the track gang's sleeper piles along both lines."""
    lanes = (LANE_A, LANE_B)
    # ---- the boxcar siding, west of the square on the canyon side
    z = -26.0
    lay_track(b, [(-192.0, z), (-94.0, z)])
    buffer_stop(b, -190.0, z, math.pi / 2.0, rails.RED)
    buffer_stop(b, -96.0, z, math.pi / 2.0, rails.RED)
    boxcar(b, -173.0, z, "x", "#8a3a2a", "DUSTBOWL & PACIFIC")
    boxcar(b, -147.0, z, "x", "#6a4a32", "BONANZA ORE", door="shut")
    flatcar(b, -122.0, z, "x", "timber", rng)
    handcar(b, -104.0, z, "x")
    KEEP.append(rect(-194.0, -92.0, z - 5.0, z + 5.0))
    for x, zz in ((-160.0, -40.0), (-128.0, -12.0)):
        sleeper_pile(b, x, zz, "x", 3)
        KEEP.append(rect(x - 3.0, x + 3.0, zz - 3.0, zz + 3.0))
    gold_board(b, -100.0, z - 9.0, "BOXCAR SIDING", "z-")

    # ---- Boot Hill: three terraces, a step each, headstones on all of them
    hill = rect(-176.0, -124.0, 22.0, 58.0)
    for k, (dx, dz) in enumerate(((0.0, 0.0), (8.0, 6.0), (16.0, 11.0))):
        slab(b, rect(hill[0] + dx, hill[1] - dx, hill[2] + dz, hill[3] - dz), 1.8 * (k + 1),
             1.8 + 0.3, ("#b48a5a", "#a87e52", "#9c744c")[k], studs=True)
    KEEP.append(hill)
    stones = [(-171.0, 25.5), (-163.0, 25.5), (-137.0, 25.5), (-129.0, 25.5),
              (-171.0, 54.5), (-155.0, 54.5), (-145.0, 54.5), (-129.0, 54.5),
              (-164.0, 31.0), (-136.0, 31.0), (-164.0, 49.0), (-136.0, 49.0)]
    for i, (x, zz) in enumerate(stones):
        y = 1.8 if zz in (25.5, 54.5) else 3.6
        if i % 3 == 0:
            b.box([x, y + 1.4, zz], [0.5, 2.8, 0.5], WOOD_DARK)
            b.box([x, y + 2.1, zz], [1.8, 0.4, 0.5], WOOD_DARK)
        else:
            b.box([x, y + 1.0, zz], [1.8, 2.0, 0.6], "#9a948a")
            b.box([x, y + 2.15, zz], [1.4, 0.3, 0.6], "#8a847a")
    # the dead tree and the marker at the top
    b.cyl([-150.0, 5.4 + 5.0, 40.0], [1.4, 10.0, 1.4], "#5a4632")
    for a, h in ((0.6, 7.5), (2.4, 8.6), (4.1, 9.4)):
        b.box([-150.0 + math.cos(a) * 1.6, 5.4 + h, 40.0 + math.sin(a) * 1.6],
              [3.0, 0.5, 0.5], "#5a4632", r=[0, -a, 0.5], collide=False)
    gold_board(b, -150.0, 18.0, "BOOT HILL", "z-")
    fence_run(b, -176.0, 18.0, -158.0, 18.0)
    fence_run(b, -142.0, 18.0, -124.0, 18.0)

    # ---- the timber siding, east of the square on the town side
    z = 26.0
    lay_track(b, [(94.0, z), (194.0, z)])
    buffer_stop(b, 96.0, z, math.pi / 2.0, rails.BLUE)
    buffer_stop(b, 192.0, z, math.pi / 2.0, rails.BLUE)
    caboose(b, 108.0, z, "x", rails.RED)
    flatcar(b, 131.0, z, "x", "tanks", rng)
    flatcar(b, 155.0, z, "x", "rails", rng)
    flatcar(b, 179.0, z, "x", "crates", rng)
    KEEP.append(rect(92.0, 196.0, z - 5.0, z + 5.0))
    for x, zz in ((126.0, 40.0), (164.0, 12.0)):
        sleeper_pile(b, x, zz, "z", 4)
        KEEP.append(rect(x - 3.0, x + 3.0, zz - 3.0, zz + 3.0))
    gold_board(b, 100.0, z + 9.0, "TIMBER SIDING", "z+")

    # ---- the prospectors' camp, east of the square on the canyon side
    for x, zz in ((136.0, -26.0), (166.0, -30.0)):
        b.box([x, 0.8, zz], [12.0, 1.6, 10.0], "#5a4632")
        b.box([x, 3.2, zz], [10.0, 3.2, 8.0], "#e8dcc0")
        b.box([x, 5.6, zz], [7.0, 1.6, 8.0], "#e8dcc0")
    # the sluice: a long trough on trestles, the creek long gone
    for k in range(4):
        b.box([122.0 + k * 10.0, 1.2, -48.0], [1.0, 2.4, 3.0], WOOD_DARK)
    b.box([137.0, 3.0, -48.0], [34.0, 1.2, 3.4], WOOD)
    b.box([137.0, 3.65, -48.0], [33.0, 0.1, 2.4], "#6a8aa0", collide=False)
    # the fire pit and the coffee pot on its tripod
    b.cyl([150.0, 0.4, -40.0], [5.0, 0.8, 5.0], "#6a645c")
    b.cone([150.0, 1.5, -40.0], [2.6, 1.4, 2.6], "#ff9a3a", material="neon")
    wagon(b, 176.0, -46.0, "x", "#d8c8a8")
    gold_board(b, 128.0, -60.0, "STAKED CLAIM", "z-")
    KEEP.append(rect(118.0, 184.0, -62.0, -18.0))

    # ---- the Devil's Gate: a rock arch you walk under, north of the square
    for x in (-15.0, 15.0):
        rock(b, x, -112.0, 10.0, 26.0, 12.0, CANYON)
    b.box([0.0, 27.0, -112.0], [44.0, 6.0, 14.0], CANYON)
    b.box([2.0, 31.5, -112.5], [30.0, 3.0, 10.0], CANYON_DARK)
    b.box([-12.0, 21.5, -112.0], [6.0, 5.0, 12.0], CANYON)
    b.box([12.0, 21.5, -112.0], [6.0, 5.0, 12.0], CANYON)
    KEEP.append(rect(-24.0, 24.0, -120.0, -104.0))

    # ---- the lookout butte, with a stair cut up its east face
    butte = rect(-156.0, -124.0, -172.0, -146.0)
    b.box([-140.0, 5.0, -159.0], [32.0, 10.0, 26.0], CANYON_DARK)
    b.box([-142.0, 10.6, -160.0], [24.0, 1.2, 18.0], CANYON)
    stair(b, "x", -110.0, -124.0, -156.0, -150.0, 0.0, 10.0, CANYON_LIGHT)
    b.mark("perch", -142.0, 11.2, -160.0)
    KEEP.append(rect(butte[0], -108.0, butte[2], butte[3]))

    # ---- the bandstand between the square and Main Street
    stand = rect(20.0, 36.0, 50.0, 66.0)
    slab(b, stand, 1.6, 1.9, "#efe2c4", studs=True)
    for px in (20.8, 35.2):
        for pz in (50.8, 65.2):
            b.box([px, 1.6 + 4.0, pz], [0.8, 8.0, 0.8], "#efe2c4")
    slab(b, rect(19.0, 37.0, 49.0, 67.0), 10.2, 0.6, "#b8322a")
    b.box([28.0, 11.2, 58.0], [12.0, 1.4, 12.0], "#a82a22")
    b.box([28.0, 12.4, 58.0], [6.0, 1.0, 6.0], "#982420")
    for k in range(3):
        b.box([24.0 + k * 4.0, 2.6, 62.0], [1.6, 2.0, 1.6], "#3a2414")
    KEEP.append(stand)

    # ---- the track gang's sleeper piles and rail racks along both lines
    total = length(LANE_A)
    for f, side in ((0.18, 1.0), (0.47, -1.0), (0.58, 1.0), (0.9, -1.0)):
        for path, sgn in ((LANE_A, 1.0), (LANE_B, -1.0)):
            x, zz, _ = beside(path, total * f, side * sgn * 12.0)
            x, zz = round(x), round(zz)
            spot = rect(x - 3.0, x + 3.0, zz - 3.0, zz + 3.0)
            if clear_of(spot, lanes, 7.0) and _free(spot):
                sleeper_pile(b, x, zz, "x" if (f * 10) % 2 < 1 else "z", 3 + int(f * 10) % 2)
                KEEP.append(spot)


def gold_board(b: ArenaArea, x: float, z: float, text: str, facing: str) -> None:
    rails.gold_sign(b, x, 5.0, z, max(12.0, len(text) * 1.3), 2.4, text, facing)


# ================================================================== canyon
def _canyon(b: ArenaArea, rng: random.Random) -> None:
    lanes = (LANE_A, LANE_B)
    # the Bonanza Mine: a timbered portal into the canyon wall, a short adit
    # with ore carts in it, and the headframe over the shaft beside it
    hz = b.half_z
    portal_z = -hz
    room_walls(b, rect(-14.0, 14.0, portal_z, portal_z + 30.0), 2.0, 0.0, 14.0, "#5a3a26",
               doors={"z+": [(-7.0, 7.0, 11.0)]})
    slab(b, rect(-15.0, 15.0, portal_z, portal_z + 30.0), 15.2, 1.2, "#5a3a26")
    # the timbered portal stands just proud of the rock face
    b.box([0.0, 12.0, portal_z + 30.7], [20.0, 2.0, 1.4], WOOD_DARK)
    for dx in (-9.0, 9.0):
        b.box([dx, 5.5, portal_z + 30.7], [2.0, 11.0, 1.4], WOOD_DARK)
    wall_sign(b, 0.0, 16.2, portal_z + 29.5, 18.0, 2.0,
              sign_decal("BONANZA MINE", rails.CREAM, "#3a2414", 9.0), "z+", rails.CREAM)
    for k in range(2):
        b.box([-6.0 + k * 12.0, 2.2, portal_z + 12.0], [4.0, 3.2, 6.0], "#5a5550", material="metal")
        b.box([-6.0 + k * 12.0, 4.3, portal_z + 12.0], [3.6, 1.0, 5.4], rails.GOLD)
    lantern(b, 0.0, 14.0, portal_z + 18.0, WARM)
    # the headframe: four legs, a platform halfway and one on top, a wheel
    hx, hz2 = 40.0, -186.0
    if clear_of(rect(hx - 10.0, hx + 10.0, hz2 - 10.0, hz2 + 10.0), lanes, 8.0):
        for dx in (-7.0, 7.0):
            for dz in (-7.0, 7.0):
                b.box([hx + dx, 15.0, hz2 + dz], [1.4, 30.0, 1.4], WOOD_DARK)
        slab(b, rect(hx - 8.0, hx + 8.0, hz2 - 8.0, hz2 + 8.0), 15.0, 0.8, WOOD)
        slab(b, rect(hx - 8.0, hx + 8.0, hz2 - 8.0, hz2 + 8.0), 30.6, 0.8, WOOD)
        stair(b, "x", hx - 22.0, hx - 8.0, hz2 - 3.0, hz2 + 3.0, 0.0, 15.0, WOOD)
        b.cyl([hx, 34.6, hz2], [7.0, 0.8, 7.0], rails.IRON, collide=False,
              r=[0, 0, math.pi / 2.0], material="metal")
        b.mark("perch", hx, 15.0, hz2)
    # the stamp mill: a tall timber building, ore chute down its side
    mill = rect(-118.0, -74.0, -214.0, -168.0)
    if clear_of(mill, lanes, 8.0):
        building(b, mill, 0.0, 24.0, "#7a5335", roof_colour="#4a3a2e", floor_colour="#5a4a3e",
                 doors={"z+": [(-102.0, -90.0, 12.0)]},
                 windows={"x+": [(-200.0, -186.0, 12.0, 18.0)], "x-": [(-200.0, -186.0, 12.0, 18.0)]},
                 glass=False, boards=True, lights=WARM)
        threshold(b, mill, "z+", (-102.0, -90.0))
        gable(b, mill, 25.2, "#4a3a2e", "z", 4, 1.6, 0.6)
        for k in range(5):
            b.box([-110.0 + k * 7.0, 0.4 + 4.0, -196.0], [3.0, 8.0, 3.0], "#4a4642", material="metal")
            b.box([-110.0 + k * 7.0, 0.4 + 9.0, -196.0], [1.2, 2.0, 1.2], rails.IRON,
                  material="metal")
        wall_sign(b, -96.0, 20.0, -167.65, 30.0, 3.0,
                  sign_decal("BONANZA STAMP MILL", rails.CREAM, "#3a2414", 10.0), "z+", rails.CREAM)
    # the powder shed: little, stone, fenced off, and a warning on the door
    shed = rect(84.0, 106.0, -206.0, -188.0)
    if clear_of(shed, lanes, 8.0):
        building(b, shed, 0.0, 9.0, "#8a8478", roof_colour="#4a4642",
                 doors={"z+": [(91.0, 99.0, 7.0)]}, lights=WARM)
        wall_sign(b, 95.0, 8.2, -187.65, 12.0, 1.6,
                  sign_decal("DANGER - POWDER", "#c4281c", "#ffffff", 7.5), "z+", "#c4281c")
        for k in range(3):
            barrel(b, 88.0 + k * 4.0, -201.0, "#8a2a1c")
    # tents, ore bins and hoodoos up and down the canyon floor
    for x in (-180.0, -150.0, 140.0, 170.0):
        z = -200.0
        if clear_of(rect(x - 7.0, x + 7.0, z - 6.0, z + 6.0), lanes, 6.0):
            b.box([x, 0.8, z], [12.0, 1.6, 10.0], "#5a4632")
            b.box([x, 3.2, z], [10.0, 3.2, 8.0], "#e8dcc0")
            b.box([x, 5.6, z], [7.0, 1.6, 8.0], "#e8dcc0")
    for k in range(10):
        x = rng.uniform(-300.0, 300.0)
        z = rng.uniform(-205.0, -40.0)
        w = rng.uniform(6.0, 12.0)
        h = rng.uniform(10.0, 26.0)
        if abs(x) < 26 and z < -170:
            continue
        if clear_of(rect(x - w, x + w, z - w, z + w), lanes, 9.0) and \
                _free(rect(x - w, x + w, z - w, z + w)) and \
                clear_of(rect(x - w, x + w, z - w, z + w), [[(-60, -40), (60, -40)]], 0.0):
            rock(b, x, z, w * 1.4, h, w * 1.2, rng.choice([CANYON, CANYON_DARK, CANYON_LIGHT]))
    for x in (-250.0, -60.0, 120.0, 250.0):
        z = -110.0 if x < 0 else -100.0
        if clear_of(rect(x - 8.0, x + 8.0, z - 5.0, z + 5.0), lanes, 6.0):
            b.box([x, 2.2, z], [10.0, 4.4, 6.0], WOOD_DARK)
            b.box([x, 4.6, z], [9.0, 0.6, 5.0], rails.GOLD, collide=False)


# ================================================================ coaling
def _coaling(b: ArenaArea, rng: random.Random) -> None:
    """A coaling stage and a water tower each side of the square, and two
    more heaps out in the canyon and behind the town."""
    for x in (-200.0, 200.0):
        coal_heap(b, x, 0.0, rng)
        water_tower(b, x + (24.0 if x > 0 else -24.0), 0.0, side=1.0 if x > 0 else -1.0)
    coal_heap(b, -30.0, -150.0, rng)
    coal_heap(b, 30.0, 150.0, rng)


# ================================================================= scatter
def _scatter(b: ArenaArea, rng: random.Random) -> None:
    lanes = (LANE_A, LANE_B)
    for k in range(26):
        x = rng.uniform(-360.0, 360.0)
        z = rng.uniform(-30.0, 100.0) if k % 2 else rng.uniform(-60.0, 40.0)
        if clear_of(rect(x - 4.0, x + 4.0, z - 4.0, z + 4.0), lanes, 7.0) and \
                _free(rect(x - 4.0, x + 4.0, z - 4.0, z + 4.0)) and \
                clear_of(rect(x - 4.0, x + 4.0, z - 4.0, z + 4.0),
                         [[(-60.0, -12.0), (60.0, -12.0)], [(-60.0, 12.0), (60.0, 12.0)]], 30.0):
            if rng.random() < 0.55:
                cactus(b, x, z, rng.uniform(0.8, 1.2))
            elif rng.random() < 0.5:
                barrel(b, x, z)
            else:
                crate_stack(b, x, z, rng)
