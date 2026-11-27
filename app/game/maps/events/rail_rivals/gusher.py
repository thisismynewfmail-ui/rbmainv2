"""Gusher Flats -- an oil boomtown on the prairie, the derricks thick as
trees and every second well about to come in.

Layout (north is -z; both tracks run west to east)::

    z -250  THE TANK FARM (four tanks       SPINDLE HILL: a dome thick with    DERRICK
            in their berms)                 derricks, the discovery well       CITY
            (lane a start) ---\\  W              on its crown          W  /--- (lane b end)
    z    0  GUSHER FLATS'      \\========== THE DIAMOND ============/    the OIL EXCHANGE
            Main Street (mud,   /   W   pipeline catwalk over both  W  \\    and the bank
            tent saloons)      /         lines                         \\--- PETROLIA
            (lane b start) ---/   SOUR CREEK: the wildcatters' camp,  W     (lane a end)
    z +250  THE REFINERY (stills,      the oil slick, the plank bridge
            cracking tower, flare)

``W``: the wells beside the lines, three on each, every one on its line's
outer side.  The twist (``gushers``): a well blows out every so often by
itself -- six seconds of hissing, then oil and fire, deadly at the wellhead
-- and the oil burns across its line, holding the cart short of the
flames.  Hold E at a wellhead's valve to set it blowing beside the other
company's line ahead of their cart; hold E at one that is hissing beside
your own to shut it.
"""
from __future__ import annotations

import math
import random

from ..kit import (WARM, WOOD, WOOD_DARK, WOOD_LIGHT, ArenaArea, backdrop, building, flight,
                   gable, ground, rect, room_walls, sign_decal, slab, threshold, wall_sign)
from ...lastlight.kit import lamp_post
from . import common, rails
from .land import Land, graded, lay_graded, world_lane
from .rails import beside, clear_of, fillet, mirror, storeyed, telegraph
from .scenery import outcrop, pup_tent, stub_track

HALF = (400.0, 250.0)
SKY = {"top": "#2e3a7a", "horizon": "#ff9448", "sun": [0.62, 0.2, -0.55],
       "clouds": 0.55, "tint": "#ffc488"}
AMBIENT = "#b08a6a"
GROUND = "#c8a84e"
FOG = 860.0

PRAIRIE = "#c8a84e"
PRAIRIE_DRY = "#dcbc62"
PRAIRIE_GREEN = "#8aa044"
PRAIRIE_GOLD = "#e0c070"
MUD = "#6a4630"
MUD_DARK = "#3e3024"
OIL = "#141210"
CRUDE = "#2a2420"
DERRICK = "#7a5a3a"
TANK = "#8a8a84"
BRICK = "#8a3a2a"
TIN = "#9a9a94"
CANVAS = "#e2d6b8"

ROUTE = fillet([(-372.0, -150.0), (-210.0, -150.0), (0.0, 0.0), (210.0, 150.0), (372.0, 150.0)],
               radius=80.0, step=5.0)
PROFILE = [(0.0, 0.0), (0.12, 0.0), (0.3, 4.0), (0.44, 1.0), (0.56, 1.0), (0.72, 5.0), (0.88, 0.0),
           (1.0, 0.0)]
LANE_A, YS = graded(ROUTE, PROFILE)
LANE_B = mirror(LANE_A)
LANES = (LANE_A, LANE_B)
LANE_OF = {"a": LANE_A, "b": LANE_B}

# the wells: lane, fraction along it, which side (its line's outer side), name
WELLS = (("a", 0.30, 1.0, "the Widow Maker"), ("a", 0.55, -1.0, "Big Bertha"), ("a", 0.78, -1.0, "Old Smoky"),
         ("b", 0.30, -1.0, "the Widow's Mite"), ("b", 0.55, 1.0, "Lucky Lil"), ("b", 0.78, 1.0, "Black Jack"))
WELL_OFF = 17.0                   # derrick centre from its line
VALVE_OFF = 12.4                  # the valve, at the derrick floor's edge toward the line

TANK_FARM = rect(-392.0, -250.0, -250.0, -184.0)
TANKS = ((-370.0, -220.0), (-336.0, -220.0), (-302.0, -220.0), (-268.0, -220.0))
REFINERY = rect(-392.0, -246.0, 184.0, 250.0)
HILL = (0.0, -168.0, 13.0, 74.0)
CREEK = [(-160.0, 176.0), (-100.0, 168.0), (-40.0, 184.0), (20.0, 174.0), (80.0, 188.0), (150.0, 176.0)]
STREET_X = -196.0
CATWALK_X = 115.0
CATWALK_Y = 12.0
EXCHANGE = rect(330.0, 384.0, -44.0, 44.0)

DEPOTS = (("a", 1 / 3.0, -1.0, "DISCOVERY SIDING", 1, "#7a3a2a"),
          ("a", 2 / 3.0, 1.0, "PIPELINE TANK", 2, "#2f4a6a"),
          ("b", 1 / 3.0, 1.0, "DISCOVERY SIDING SOUTH", 1, "#2f4a6a"),
          ("b", 2 / 3.0, -1.0, "PIPELINE TANK NORTH", 2, "#7a3a2a"))
COAL = ((-336.0, -100.0), (-336.0, 100.0), (-60.0, 0.0), (168.0, 0.0))

KEEP: list = []
BASES: dict = {}
WELL_SPOTS: list = []


def build(b: ArenaArea) -> None:
    rng = random.Random(0x0115)
    del KEEP[:]
    BASES.clear()
    _plan_wells()
    b.extra.update({"accent": "#ffb030", "twist": "gushers",
                    "lanes": {"a": world_lane(b, LANE_A, YS), "b": world_lane(b, LANE_B, YS)},
                    "names": {"a": "the Discovery line", "b": "the Sour Creek line"}})
    land = _land()
    ground(b, PRAIRIE, soil="#5a4a34", holes=[])
    land.build(b, PRAIRIE)
    _edge(b, rng)
    for path in LANES:
        lay_graded(b, path, YS, ballast="#6a5a48")
    common.start_yards(b, ("TANK FARM YARD", "REFINERY YARD"), ("#7a3a2a", "#2f4a6a"), KEEP)
    _wells(b, rng, land)
    _tank_farm(b, rng)
    _refinery(b, rng)
    _hill(b, rng, land)
    _boomtown(b, rng)
    _creek(b, rng, land)
    _catwalk(b, land)
    _exchange(b, rng)
    common.termini(b, ("PETROLIA", "DERRICK CITY"), ("#2f4a6a", "#7a3a2a"), KEEP, house="#9a7a54",
                   trim="#4a3a2e")
    common.place_depots(b, DEPOTS, LANE_OF, BASES, KEEP)
    common.place_levers(b, land, LANE_OF, KEEP)
    common.place_coal(b, COAL, BASES, rng, KEEP)
    _pumpjacks(b, land)
    _scatter(b, rng, land)
    telegraph(b, LANE_A, -1.0, ground=land.height, skip=_blocked)
    telegraph(b, LANE_B, 1.0, ground=land.height, skip=_blocked)
    _rigs(b)
    for x, z, name in ((-345, -150, "the tank farm yard"), (-345, 150, "the refinery yard"),
                       (-320, -220, "the tank farm"), (-330, 220, "the refinery"), (-300, 220, "the cracking tower"),
                       (-268, 236, "the flare stack"), (0, -168, "Spindle Hill"), (0, -196, "the discovery well"),
                       (STREET_X, 0, "Main Street"), (STREET_X - 18, -40, "the Gusher Hotel"),
                       (STREET_X + 18, 30, "the Gazette"), (0, 0, "the diamond"), (CATWALK_X, 0, "the pipeline catwalk"),
                       (-60, 196, "the wildcatters' camp"), (40, 170, "Sour Creek"), (100, 196, "the oil slick"),
                       (356, 0, "the Oil Exchange"), (345, 150, "Petrolia"), (345, -150, "Derrick City"),
                       (168, 0, "the pump station")):
        b.landmark(float(x), float(z), name)
    for (lane, f, side, name), spot in zip(WELLS, WELL_SPOTS):
        b.landmark(spot["dx"], spot["dz"], name)
    b.camera(-140.0, 40.0, -30.0, 0.0, 4.0, 0.0)
    b.camera(60.0, 50.0, -90.0, 0.0, 10.0, -168.0)
    b.camera(-260.0, 40.0, 120.0, -320.0, 8.0, 220.0)


def _keep(area) -> None:
    KEEP.append(area)


def _blocked(x: float, z: float) -> bool:
    return any(k[0] - 2 < x < k[1] + 2 and k[2] - 2 < z < k[3] + 2 for k in KEEP)


def _smooth(k: float) -> float:
    k = max(0.0, min(1.0, k))
    return k * k * (3.0 - 2.0 * k)


def _plan_wells() -> None:
    """Where each well's derrick, valve and burning stretch go."""
    del WELL_SPOTS[:]
    for lane, f, side, name in WELLS:
        path = LANE_OF[lane]
        d = rails.length(path) * f
        dx, dz, _yaw = beside(path, d, side * WELL_OFF)
        vx, vz, _ = beside(path, d, side * VALVE_OFF)
        lx, lz, lyaw = rails.at(path, d)
        WELL_SPOTS.append({"lane": lane, "d": d, "dx": dx, "dz": dz, "vx": vx, "vz": vz, "name": name,
                           "side": side, "yaw": lyaw})


# ==================================================================== land
def _land() -> Land:
    """Low rolling prairie with Spindle Hill's dome in the north, Sour
    Creek's valley in the south, berms round the tanks."""
    hx, hz = HALF
    land = Land(rect(-hx, hx, -hz, hz), cell=10.0, step=1.0)

    def shape(x: float, z: float) -> float:
        roll = 2.6 * math.sin(x / 57.0 + 0.6) * math.cos(z / 49.0 - 0.3) + \
            1.8 * math.cos(x / 31.0 + 1.1) * math.sin(z / 43.0) + 1.0 * math.sin((x - z) / 21.0)
        hx0, hz0, hh, hr = HILL
        dome = hh * _smooth(1.0 - math.hypot(x - hx0, z - hz0) / hr)
        rim = 3.0 * _smooth((abs(z) - 190.0) / 50.0)
        return max(0.0, 4.0 + roll + dome + rim)

    land.add(shape)
    land.scale(lambda x, z: 0.12 + 0.88 * _smooth((rails.distance_to(CREEK, x, z) - 5.0) / 22.0))
    flats = [(rect(-400.0, -246.0, -250.0, -120.0), 0.0, 12.0),
             (rect(-400.0, -240.0, 120.0, 250.0), 0.0, 12.0),
             (rect(STREET_X - 40.0, STREET_X + 38.0, -96.0, 96.0), 1.0, 14.0),
             (rect(-24.0, 24.0, -22.0, 22.0), 1.0, 16.0),
             (rect(-12.0, 12.0, -210.0, -186.0), 16.0, 6.0),
             (rect(240.0, 400.0, -250.0, 250.0), 0.0, 16.0),
             (rect(150.0, 186.0, -14.0, 14.0), 2.0, 10.0),
             (rect(-90.0, -30.0, 186.0, 216.0), 1.0, 10.0)]
    for area, y, blend in flats:
        land.flatten(area, y, blend)
    for spot in WELL_SPOTS:
        y = float(round(land.height(spot["dx"], spot["dz"])))
        land.flatten(rect(spot["dx"] - 8.0, spot["dx"] + 8.0, spot["dz"] - 8.0, spot["dz"] + 8.0), y, blend=8.0)
        spot["y"] = y
    common.plan_depots(land, DEPOTS, LANE_OF, YS, BASES)
    common.plan_coal(land, COAL, BASES)
    for path in LANES:
        land.pin_path(path, YS, half=7.5, blend=12.0)
    # the wells' levelled floors after the lines have had their way
    for spot in WELL_SPOTS:
        spot["y"] = land.height(spot["dx"], spot["dz"])

    def paint(x: float, z: float, h: float):
        if rails.distance_to(CREEK, x, z) < 9.0 and h < 1.6:
            return "#4a5a3a"
        if any(math.hypot(x - s["dx"], z - s["dz"]) < 13.0 for s in WELL_SPOTS):
            return MUD_DARK
        if STREET_X - 8 < x < STREET_X + 8 and -96 < z < 96:
            return MUD
        if h >= 12.0:
            return PRAIRIE_GOLD
        if h >= 8.0:
            return PRAIRIE_DRY
        if h < 2.0:
            return PRAIRIE_GREEN
        if h < 3.5:
            return "#b0a048"
        return None

    land.colour(paint)
    return land


# ==================================================================== edge
def _edge(b: ArenaArea, rng: random.Random) -> None:
    hx, hz, m = b.half_x, b.half_z, b.margin
    room_walls(b, rect(-hx - m, hx + m, -hz - m, hz + m), m, 0.0, 22.0, "#7a6a48")
    for side in (-1, 1):
        for i in range(26):
            x = -hx + (i + 0.5) * (2 * hx) / 26.0
            top = rng.uniform(3.0, 9.0)
            b.box([x, 22.0 + top / 2.0, side * (hz + m / 2.0)], [2 * hx / 26.0 - 1.0, top, m + 1.0 + (i % 3) * 0.13],
                  rng.choice(["#8a7a52", "#7a6a48", "#6a5a3e"]), collide=False)
    backdrop(b, "hills", 0.0, rng, ["#8a8a52", "#7a7a4a", "#9a9058"], depth=180.0)
    # derricks on the far hills, the field going on past the fence
    for k in range(18):
        side = -1 if k % 2 else 1
        x = -380.0 + k * 45.0 + rng.uniform(-10, 10)
        z = side * (hz + m + rng.uniform(40.0, 120.0))
        _derrick(b, x, z, 0.0, solid=False, height=rng.uniform(18.0, 26.0), footing=False)


# ================================================================= wells
def _derrick(b: ArenaArea, x: float, z: float, base: float, solid: bool = True,
             height: float = 24.0, colour: str = DERRICK, footing: bool = True) -> None:
    """A wooden derrick: four legs leaning in to the crown block, girts and
    braces between them, the derrick floor at its foot."""
    spread, top = 4.2, 1.0
    lean = math.atan2(spread - top, height)
    for sx in (-1, 1):
        for sz in (-1, 1):
            mx, mz = x + sx * (spread + top) / 2.0, z + sz * (spread + top) / 2.0
            b.box([mx, base + height / 2.0, mz], [0.6, height + 0.4, 0.6], colour, collide=False,
                  r=[-sz * lean, 0.0, sx * lean])
    for k in range(1, 6):
        f = k / 5.0
        w = (spread - (spread - top) * f) * 2.0
        y = base + height * f
        for sz in (-1, 1):
            b.box([x, y, z + sz * w / 2.0], [w, 0.3, 0.3], colour, collide=False)
        for sx in (-1, 1):
            b.box([x + sx * w / 2.0, y, z], [0.3, 0.3, w], colour, collide=False)
    b.box([x, base + height + 0.6, z], [2.6, 1.2, 2.6], "#5a3e28", collide=False)
    if solid:
        slab(b, rect(x - spread - 0.6, x + spread + 0.6, z - spread - 0.6, z + spread + 0.6), base + 1.2, 1.2,
             WOOD, studs=True)
    elif footing:
        b.box([x, base + 0.6, z], [spread * 2.0 + 1.2, 1.2, spread * 2.0 + 1.2], WOOD_DARK, collide=False)


def _wells(b: ArenaArea, rng: random.Random, land: Land) -> None:
    """The six wells by the lines: each its derrick on a mud-black pad, the
    wellhead and its valve wheel at the floor's edge, the engine shed and
    the band wheel behind, a sign with its name."""
    for k, spot in enumerate(WELL_SPOTS):
        x, z, y = spot["dx"], spot["dz"], spot["y"]
        _derrick(b, x, z, y)
        # the casing pipe up through the floor, the valve and its wheel by
        # the edge toward the line
        b.cyl([x, y + 2.4, z], [1.0, 2.4, 1.0], "#3a3a3e", material="metal")
        vx, vz = spot["vx"], spot["vz"]
        b.box([vx, y + 1.8, vz], [1.0, 1.2, 1.0], "#4a4a4e", material="metal")
        b.cyl([vx, y + 2.5, vz], [1.8, 0.2, 1.8], "#c83a2a", material="metal", collide=False)
        # a pipe from the casing to the valve
        b.box([(x + vx) / 2.0, y + 1.6, (z + vz) / 2.0], [abs(vx - x) + 0.5, 0.4, abs(vz - z) + 0.5], "#3a3a3e",
              material="metal", collide=False)
        b.mark("well", vx, y + 1.2, vz, lane=spot["lane"], d=round(spot["d"], 2),
               head=b.at(x, y + 2.4, z), name=spot["name"])
        # the engine shed and its stack on the far side
        away = -spot["side"]
        ex, ez, _ = beside(LANE_OF[spot["lane"]], spot["d"], spot["side"] * (WELL_OFF + 9.0))
        shed = rect(ex - 3.5, ex + 3.5, ez - 3.0, ez + 3.0)
        building(b, shed, y, 5.0, "#6a5a48", roof_colour="#3a3a3e", lights="")
        b.cyl([ex + 2.0, y + 8.0, ez], [0.8, 6.0, 0.8], "#2a2a2c", material="metal")
        del away
        wall_sign(b, x, y + 4.6, z + (5.6 if spot["dz"] > 0 else -5.6), 6.0, 1.2,
                  sign_decal(spot["name"].upper(), "#5a3e28", "#e8d8b0", 5.0),
                  "z+" if spot["dz"] > 0 else "z-", "#5a3e28")
        _keep(rect(min(x, ex) - 8.0, max(x, ex) + 8.0, min(z, ez) - 8.0, max(z, ez) + 8.0))


# ============================================================== tank farm
def _tank_farm(b: ArenaArea, rng: random.Random) -> None:
    """The tank farm: four steel tanks of crude, each in its earth berm
    (a fire wall to climb over), a stair round the first to its roof (a
    perch), pipes between them on low stands."""
    for k, (x, z) in enumerate(TANKS):
        # the berm: a square of earth banked round the tank
        for side in (-1, 1):
            b.box([x, 1.2, z + side * 15.0], [32.0, 2.4, 2.4], "#6a5a3a", studs=True)
            b.box([x + side * 15.0, 1.2, z], [2.4, 2.4, 27.6], "#6a5a3a", studs=True)
        b.cyl([x, 8.0, z], [22.0, 16.0, 22.0], ("#c8c8c0", "#d8d0b0", "#c0c8c8", "#d0c8c0")[k], material="metal")
        b.cyl([x, 16.4, z], [22.6, 0.8, 22.6], "#5a5a5e", material="metal")
        b.cone([x, 18.0, z], [21.0, 2.4, 21.0], "#6a6a6a", material="metal")
        for ring in range(3):
            b.cyl([x, 3.0 + ring * 5.0, z], [22.2, 0.3, 22.2], "#6a6a66", material="metal", collide=False)
        logo = (("GUSHER OIL", "#c8281e"), ("STAR CRUDE", "#2f6aa8"), ("LONE PINE", "#3a8a3a"),
                ("SUNSET OIL", "#e8902a"))[k]
        b.box([x, 10.0, z + 11.2], [12.0, 3.6, 0.4], logo[1], collide=False, decal=sign_decal(logo[0], logo[1], "#fff6d8", 10.0))
        b.box([x, 13.4, z + 11.1], [6.0, 0.6, 0.4], "#fff6d8", collide=False)
        _keep(rect(x - 17.0, x + 17.0, z - 17.0, z + 17.0))
    # the stair up the first tank's side and the walk round its roof
    x, z = TANKS[0]
    flight(b, "x", x + 32.0, x + 9.5, z + 11.6, z + 14.0, 0.0, 16.0, "#5a5a5e", fill=-0.3)
    b.mark("perch", x + 4.0, 17.2, z + 4.0)
    # pipes between the tanks on stands
    for k in range(len(TANKS) - 1):
        x0, x1 = TANKS[k][0] + 11.0, TANKS[k + 1][0] - 11.0
        b.box([(x0 + x1) / 2.0, 2.0, -204.0], [x1 - x0, 1.0, 1.0], "#4a4a4e", material="metal")
        for xx in (x0 + 2.0, x1 - 2.0):
            b.box([xx, 0.75, -204.0], [0.6, 1.5, 0.6], "#3a3a3e", material="metal")


# =============================================================== refinery
def _refinery(b: ArenaArea, rng: random.Random) -> None:
    """The refinery: three stills over their brick fireboxes (glowing), the
    cracking tower with its platforms (the top one a perch), the flare
    stack burning off the gas, the boiler house, the pipe rack."""
    for k in range(3):
        x, z = -374.0 + k * 16.0, 214.0
        b.box([x, 2.5, z], [10.0, 5.0, 18.0], BRICK, studs=True)
        b.box([x, 1.6, z - 9.06], [4.0, 2.0, 0.1], "#ff7a2a", material="neon", collide=False)
        b.cyl([x, 8.2, z], [8.0, 16.0, 8.0], "#6a6a6a", r=[math.pi / 2.0, 0.0, 0.0], material="metal")
        b.cyl([x, 12.8, z + 4.0], [1.0, 4.0, 1.0], "#4a4a4e", material="metal")
        _keep(rect(x - 6.0, x + 6.0, z - 10.0, z + 10.0))
    # the cracking tower and its stair of platforms
    tx, tz = -300.0, 220.0
    b.cyl([tx, 15.0, tz], [8.0, 30.0, 8.0], "#7a7a74", material="metal")
    for k, y in enumerate((8.0, 16.0, 24.0)):
        slab(b, rect(tx - 7.0, tx + 7.0, tz - 7.0, tz + 7.0), y, 0.5, "#4a4a4e", material="metal")
    for k, (y0, y1) in enumerate(((0.0, 8.0), (8.0, 16.0), (16.0, 24.0))):
        if k % 2 == 0:
            flight(b, "x", tx + 7.0 + 10.0, tx + 7.0, tz + 3.0 if k == 0 else tz - 6.5, tz + 6.5 if k == 0 else tz - 3.0,
                   y0, y1, "#5a5a5e", fill=y0 - 0.3 if k else -0.3)
        else:
            flight(b, "x", tx - 7.0 - 10.0, tx - 7.0, tz - 6.5, tz - 3.0, y0, y1, "#5a5a5e", fill=y0 - 0.3)
    b.mark("perch", tx + 4.0, 24.0, tz + 4.0)
    _keep(rect(tx - 19.0, tx + 19.0, tz - 9.0, tz + 9.0))
    # the flare stack
    fx, fz = -264.0, 238.0
    b.cyl([fx, 13.0, fz], [1.6, 26.0, 1.6], "#5a5a5e", material="metal")
    b.box([fx, 1.0, fz], [4.0, 2.0, 4.0], "#3a3a3e", material="metal")
    _keep(rect(fx - 3.0, fx + 3.0, fz - 3.0, fz + 3.0))
    # the boiler house and its stack
    boiler = rect(-330.0, -312.0, 232.0, 248.0)
    building(b, boiler, 0.0, 8.0, BRICK, roof_colour="#3a3a3e", doors={"z-": [(-324.0, -318.0, 6.0)]})
    threshold(b, boiler, "z-", (-324.0, -318.0))
    b.cyl([-314.0, 18.0, 244.0], [2.6, 20.0, 2.6], "#5a3a2e")
    _keep(rect(boiler[0] - 2.0, boiler[1] + 2.0, boiler[2] - 2.0, boiler[3] + 2.0))
    # the pipe rack along the front of it all
    for x in range(-384, -256, 12):
        b.box([float(x), 3.0, 196.0], [0.6, 6.0, 0.6], "#4a4a4e", material="metal")
    b.box([-320.0, 6.2, 196.0], [128.0, 0.6, 2.4], "#3a3a3e", material="metal")
    for k in range(3):
        b.cyl([-320.0, 7.0, 195.4 + k * 0.8], [0.6, 128.0, 0.6], ("#6a6a66", "#8a5a3a", "#5a6a7a")[k],
              r=[0.0, 0.0, math.pi / 2.0], material="metal", collide=False)
    _keep(rect(-386.0, -254.0, 194.0, 198.0))


# ================================================================== hill
def _hill(b: ArenaArea, rng: random.Random, land: Land) -> None:
    """Spindle Hill: the salt dome the boom started on, its slopes a forest
    of derricks and the discovery well on its crown -- the gilded wellhead
    on its plinth, its plaque, the first barrel."""
    hx0, hz0, _h, hr = HILL
    spots = ((-34.0, -160.0), (30.0, -150.0), (-12.0, -128.0), (44.0, -186.0), (-46.0, -196.0), (18.0, -214.0),
             (-28.0, -226.0), (60.0, -130.0))
    for x, z in spots:
        y = land.height(x, z)
        if abs(land.height(x + 4.0, z) - y) > 1.2 or abs(land.height(x, z + 4.0) - y) > 1.2:
            y = min(y, land.height(x + 4.0, z), land.height(x, z + 4.0))
        _derrick(b, x, z, y, solid=False, height=rng.uniform(20.0, 26.0),
                 colour=rng.choice([DERRICK, "#6a4a30", "#8a6a48"]))
        _keep(rect(x - 6.0, x + 6.0, z - 6.0, z + 6.0))
    # the discovery well on the crown
    y = 16.0
    b.box([0.0, y + 0.8, -198.0], [6.0, 1.6, 6.0], "#a89c84")
    b.cyl([0.0, y + 3.0, -198.0], [1.4, 3.0, 1.4], "#c8a040", material="metal")
    b.cyl([0.0, y + 4.8, -198.0], [2.4, 0.4, 2.4], "#c8a040", material="metal")
    wall_sign(b, 0.0, y + 1.0, -194.6, 5.0, 1.2, sign_decal("DISCOVERY WELL 1901", "#a89c84", "#3a2a1a", 4.6), "z+",
              "#a89c84")
    rails.barrel(b, 4.0, -194.0, CRUDE, y=y)
    b.mark("perch", -6.0, y, -192.0)
    _keep(rect(-12.0, 12.0, -210.0, -186.0))


# ============================================================== boomtown
def _boomtown(b: ArenaArea, rng: random.Random) -> None:
    """Gusher Flats itself, three months old: Main Street a river of mud,
    plank walks along it, the Gusher Hotel (two storeys of raw lumber, a
    perch on its balcony), the Gazette, the lease office, two tent saloons,
    and a tank wagon sunk to its hubs."""
    base = 1.0
    x0 = STREET_X
    b.box([x0, base + 0.04, 0.0], [14.0, 0.08, 188.0], MUD_DARK, collide=False)
    for side in (-1, 1):
        slab(b, rect(x0 + side * 7.0 - 2.0, x0 + side * 7.0 + 2.0, -90.0, 90.0), base + 0.6, 0.6, WOOD_LIGHT)
    # west side: the hotel, the lease office
    hotel = rect(x0 - 36.0, x0 - 10.0, -70.0, -20.0)
    storeyed(b, hotel, [9.0, 8.0], "#b84a3a", roof="#3a2a2a", base=base,
             doors={"x+": [(-50.0, -42.0, base + 8.0)]},
             windows=[{"x+": [(-66.0, -58.0, base + 3.0, base + 7.0), (-34.0, -26.0, base + 3.0, base + 7.0)]},
                      {"x+": [(-66.0, -58.0, base + 11.0, base + 15.0), (-50.0, -42.0, base + 11.0, base + 15.0),
                              (-34.0, -26.0, base + 11.0, base + 15.0)]}],
             wells=[rect(hotel[0] + 2.0, hotel[0] + 8.0, hotel[2] + 2.0, hotel[2] + 14.0)])
    flight(b, "z", hotel[2] + 16.0, hotel[2] + 2.0, hotel[0] + 2.0, hotel[0] + 8.0, base + 0.4, base + 9.0, WOOD,
           fill=base)
    threshold(b, hotel, "x+", (-50.0, -42.0), y0=base)
    gable(b, hotel, base + 17.0 + 1.2, "#5a3a2a", "z", 4, 1.2, 1.0)
    slab(b, rect(x0 - 10.0, x0 - 6.0, -68.0, -22.0), base + 9.6, 0.6, WOOD, studs=True)
    for z in (-66.0, -45.0, -24.0):
        b.box([x0 - 6.6, base + 4.8, z], [0.6, 9.6, 0.6], WOOD_DARK)
    flight(b, "z", -86.0, -68.0, x0 - 10.0, x0 - 6.0, base, base + 9.6, WOOD, fill=base - 0.3)
    wall_sign(b, x0 - 9.64, base + 15.0, -45.0, 18.0, 2.2, sign_decal("GUSHER HOTEL", "#f2ece0", "#b8322a", 8.0),
              "x+", "#f2ece0")
    b.mark("perch", x0 - 8.0, base + 9.6, -45.0)
    _keep(rect(hotel[0] - 2.0, x0 - 5.0, -88.0, hotel[3] + 2.0))
    lease = rect(x0 - 32.0, x0 - 10.0, 10.0, 40.0)
    rails.false_front(b, lease, "x+", "#d8a83a", "LEASES BOUGHT & SOLD", height=9.0, porch=0.0,
                      trim="#f2ece0", sign_bg="#2a3a6a", sign_fg="#ffe08a")
    _keep(rect(lease[0] - 2.0, lease[1] + 2.0, lease[2] - 2.0, lease[3] + 2.0))
    # east side: the Gazette and two tent saloons
    gazette = rect(x0 + 10.0, x0 + 30.0, 16.0, 44.0)
    rails.false_front(b, gazette, "x-", "#3a8a8a", "THE GUSHER GAZETTE", height=9.0, porch=0.0,
                      trim="#f2ece0", sign_bg="#f2ece0", sign_fg="#1a2a3a")
    b.box([x0 + 20.0, base + 1.4, 30.0], [3.0, 2.6, 3.0], "#2a2a2e", material="metal")
    _keep(rect(gazette[0] - 2.0, gazette[1] + 2.0, gazette[2] - 2.0, gazette[3] + 2.0))
    for k, (z0, name) in enumerate(((-70.0, "THE DRY HOLE"), (-34.0, "LADY LUCK"))):
        tent = rect(x0 + 10.0, x0 + 32.0, z0, z0 + 24.0)
        building(b, tent, base, 6.0, "#9a7a54", roof=False, doors={"x-": [(z0 + 8.0, z0 + 16.0, base + 6.0)]},
                 floor_colour="#6a4e34")
        threshold(b, tent, "x-", (z0 + 8.0, z0 + 16.0), y0=base)
        stripe = ("#c8281e", "#2f6aa8")[k]
        for tier, (inset, y) in enumerate(((0.0, 6.0), (3.0, 7.4), (6.0, 8.6))):
            slab(b, rect(tent[0] - 0.6, tent[1] + 0.6, z0 + inset - 0.6, z0 + 24.0 - inset + 0.6), base + y + 0.3, 0.3,
                 CANVAS if tier % 2 == 0 else stripe)
        b.box([x0 + 21.0, base + 10.4, z0 + 12.0], [0.2, 2.4, 1.6], stripe, collide=False)
        b.box([x0 + 21.0, base + 9.6, z0 + 12.0], [0.2, 1.2, 0.2], WOOD_DARK)
        wall_sign(b, x0 + 9.64, base + 7.4, z0 + 12.0, 12.0, 1.8, sign_decal(name, stripe, "#fff2c8", 6.0), "x-",
                  stripe)
        b.box([x0 + 24.0, base + 1.6, z0 + 12.0], [2.0, 1.4, 14.0], WOOD_DARK)
        _keep(rect(tent[0] - 2.0, tent[1] + 2.0, tent[2] - 2.0, tent[3] + 2.0))
    # the tank wagon sunk in the mud, its mules unhitched and sulking
    b.cyl([x0 + 1.0, base + 2.4, 60.0], [4.0, 9.0, 4.0], "#3a3a3e", r=[math.pi / 2.0, 0.0, 0.0], material="metal")
    for dz in (-3.0, 3.0):
        for side in (-1, 1):
            b.cyl([x0 + 1.0 + side * 2.4, base + 0.6, 60.0 + dz], [2.6, 0.4, 2.6], "#4a3a2a",
                  r=[0.0, 0.0, math.pi / 2.0], collide=False)
    _keep(rect(x0 - 3.0, x0 + 5.0, 54.0, 66.0))
    for z in (-90.0, -10.0, 70.0):
        lamp_post(b, x0 + 9.4, z, 11.0, light=WARM)
    for z in (-90.0, -10.0, 70.0):
        lamp_post(b, x0 - 7.0, z + 30.0, 11.0, light=WARM)
    # the billboard at the south end of the street
    bx, bz = x0 + 2.0, 104.0
    for dx in (-8.0, 8.0):
        b.box([bx + dx, base + 5.0, bz], [0.8, 10.0, 0.8], WOOD_DARK)
    b.box([bx, base + 10.0, bz], [22.0, 7.0, 0.6], "#f2ece0",
          decal=sign_decal("GUSHER FLATS! BIGGEST STRIKE IN THE WEST", "#f2ece0", "#c8281e", 20.0))
    b.box([bx, base + 13.8, bz], [22.6, 0.6, 1.0], "#c8281e")
    _keep(rect(bx - 12.0, bx + 12.0, bz - 2.0, bz + 2.0))
    # Doc Pettibone's medicine show: a gaudy wagon, its stage let down
    wx, wz = x0 - 22.0, 66.0
    b.box([wx, base + 3.4, wz], [12.0, 4.4, 5.6], "#7a2a6a")
    b.box([wx, base + 5.9, wz], [12.4, 0.6, 6.0], "#e8b23a")
    b.box([wx, base + 3.6, wz + 2.86], [9.0, 1.8, 0.1], "#e8b23a", collide=False,
          decal=sign_decal("DR PETTIBONE'S ELIXIR", "#e8b23a", "#7a2a6a", 8.0))
    for dx in (-4.0, 4.0):
        for side in (-1, 1):
            b.cyl([wx + dx, base + 1.2, wz + side * 3.0], [2.4, 0.4, 2.4], "#e8b23a", r=[math.pi / 2.0, 0.0, 0.0],
                  collide=False)
    slab(b, rect(wx - 6.0, wx + 6.0, wz - 7.4, wz - 2.8), base + 1.6, 0.4, "#c8281e", studs=True)
    for k in range(5):
        b.box([wx - 4.0 + k * 2.0, base + 2.0, wz - 6.6], [0.5, 0.8, 0.5], ("#3a8a3a", "#c8281e", "#2f6aa8")[k % 3],
              collide=False)
    _keep(rect(wx - 7.0, wx + 7.0, wz - 8.0, wz + 4.0))


# ================================================================== creek
def _creek(b: ArenaArea, rng: random.Random, land: Land) -> None:
    """Sour Creek: oil on its water in rainbow sheens, a plank bridge over
    it, the wildcatters' camp on its bank (their cable-tool rig thumping,
    the walking beam is a rig), and the slick where a well ran wild."""
    for (x0, z0), (x1, z1) in zip(CREEK, CREEK[1:]):
        steps = max(1, int(math.hypot(x1 - x0, z1 - z0) / 10.0))
        for k in range(steps):
            f = (k + 0.5) / steps
            x, z = x0 + (x1 - x0) * f, z0 + (z1 - z0) * f
            y = land.height(x, z)
            b.water(x, z, 11.0, 6.0 + (k % 2) * 0.01, y + 0.3 + (k % 2) * 0.006, "#3a5a52")
    # the plank bridge
    bx = -40.0
    by = land.height(bx, 184.0) + 1.6
    slab(b, rect(bx - 3.0, bx + 3.0, 172.0, 196.0), by, 0.4, WOOD)
    for z in (173.0, 195.0):
        b.box([bx, (by - 0.4) / 2.0 + land.height(bx, z) / 2.0, z], [6.4, max(0.4, by - 0.4 - land.height(bx, z)), 1.0],
              WOOD_DARK)
    # the wildcatters' camp: the rig, its derrick, the boiler, tents
    cx, cz = -60.0, 202.0
    y = 1.0
    _derrick(b, cx - 18.0, cz, y, solid=True, height=20.0)
    b.box([cx - 6.0, y + 3.0, cz], [1.4, 6.0, 1.4], WOOD_DARK)
    b.cyl([cx + 6.0, y + 2.0, cz + 6.0], [4.0, 4.0, 4.0], "#3a3a3e", material="metal")
    b.cyl([cx + 6.0, y + 6.0, cz + 6.0], [0.8, 4.0, 0.8], "#2a2a2c", material="metal")
    for k in range(3):
        pup_tent(b, cx + 18.0 + k * 10.0, cz + 8.0, "z", CANVAS if k % 2 else "#d4c6a4", base=y)
    _keep(rect(cx - 26.0, cx + 26.0, cz - 10.0, cz + 14.0))
    # the slick: black and glossy, a dead bird and a sign
    sx, sz = 100.0, 198.0
    y2 = land.height(sx, sz)
    BUBBLE_Y[0] = y2
    b.box([sx, y2 + 0.05, sz], [22.0, 0.1, 12.0], OIL, collide=False, material="glass", alpha=0.95)
    b.cyl([sx - 13.0, y2 + 1.6, sz], [0.4, 3.2, 0.4], WOOD_DARK)
    b.box([sx - 13.0, y2 + 3.6, sz], [3.4, 1.2, 0.3], "#e8dcc0", decal=sign_decal("NO SMOKING", "#e8dcc0", "#b8322a", 3.0))
    _keep(rect(sx - 15.0, sx + 12.0, sz - 7.0, sz + 7.0))


# =============================================================== catwalk
def _catwalk(b: ArenaArea, land: Land) -> None:
    """The pipeline north to south on its trestle, high over both lines,
    with a catwalk along it -- a way over the race, and a stair down at
    each end and in the middle."""
    x = CATWALK_X
    z0, z1 = -200.0, 200.0
    slab(b, rect(x - 2.0, x + 2.0, z0, z1), CATWALK_Y, 0.4, "#4a4a4e", material="metal")
    b.cyl([x + 3.4, CATWALK_Y + 1.2, 0.0], [2.4, z1 - z0, 2.4], "#3a3a3e", r=[math.pi / 2.0, 0.0, 0.0],
          material="metal")
    for z in range(int(z0), int(z1) + 1, 20):
        zz = float(z)
        if any(abs(zz - lz) < 12.0 for lz in (85.7, -85.7)):
            continue
        g = land.height(x, zz)
        for dx in (-2.0, 3.4):
            b.box([x + dx, (g + CATWALK_Y - 0.4) / 2.0, zz], [0.8, CATWALK_Y - 0.4 - g, 0.8], "#3a3a3e",
                  material="metal")
    for zz in (z0, z1):
        side = -1.0 if zz < 0 else 1.0
        g = land.height(x, zz + side * 16.5)
        flight(b, "z", zz + side * 16.0, zz, x - 2.0, x + 2.0, g, CATWALK_Y, "#4a4a4e", fill=g - 0.3)
    g = land.height(x - 18.5, 0.0)
    flight(b, "x", x - 18.0, x - 2.0, -2.0, 2.0, g, CATWALK_Y, "#4a4a4e", fill=g - 0.3)
    b.mark("perch", x, CATWALK_Y, -40.0)
    b.mark("perch", x, CATWALK_Y, 40.0)
    _keep(rect(x - 20.0, x + 6.0, z0 - 18.0, z1 + 18.0))
    # the pump station by it
    house = rect(152.0, 184.0, -12.0, 12.0)
    building(b, house, 2.0, 9.0, BRICK, roof_colour="#3a3a3e", doors={"x-": [(-4.0, 4.0, 9.0)]},
             windows={"z-": [(160.0, 168.0, 6.0, 9.0)], "z+": [(160.0, 168.0, 6.0, 9.0)]}, glass=True, lights=WARM)
    threshold(b, house, "x-", (-4.0, 4.0), y0=2.0)
    b.cyl([176.0, 18.0, 6.0], [2.0, 14.0, 2.0], "#3a3a3e", material="metal")
    _keep(rect(150.0, 186.0, -14.0, 14.0))


# ============================================================== exchange
def _exchange(b: ArenaArea, rng: random.Random) -> None:
    """The Oil Exchange between the two stations: brick, two storeys, the
    great chalkboard of the day's prices in its hall, the bank beside."""
    x0, x1, z0, z1 = EXCHANGE
    storeyed(b, EXCHANGE, [10.0, 8.0], BRICK, roof="#3a3a3e",
             doors={"x-": [(-6.0, 6.0, 9.0)]},
             windows=[{"x-": [(-38.0, -28.0, 3.0, 8.0), (-18.0, -10.0, 3.0, 8.0), (10.0, 18.0, 3.0, 8.0),
                              (28.0, 38.0, 3.0, 8.0)]},
                      {"x-": [(-38.0, -28.0, 12.0, 16.0), (-18.0, -10.0, 12.0, 16.0), (10.0, 18.0, 12.0, 16.0),
                              (28.0, 38.0, 12.0, 16.0)]}],
             wells=[rect(x1 - 8.0, x1 - 2.0, z0 + 2.0, z0 + 14.0)], parapet=1.4)
    flight(b, "z", z0 + 16.0, z0 + 2.0, x1 - 8.0, x1 - 2.0, 0.4, 10.0, WOOD, fill=0.0)
    threshold(b, EXCHANGE, "x-", (-6.0, 6.0))
    b.box([x1 - 2.1, 5.0, 0.0], [0.2, 6.0, 40.0], "#1e2a22", collide=False,
          decal=sign_decal("CRUDE 3c   SPINDLE 4c   SOUR 2c   ? ? ?", "#1e2a22", "#e8e8e0", 40.0))
    wall_sign(b, x0 - 0.36, 15.0, 0.0, 30.0, 2.6, sign_decal("OIL EXCHANGE", "#3a3a3e", "#f2d79a", 12.0), "x-",
              "#3a3a3e")
    for z in (-12.0, 12.0):
        b.cyl([x0 - 1.4, 5.0, z], [1.4, 10.0, 1.4], "#d8d0c0")
    b.mark("perch", x1 - 10.0, 10.4, 20.0)
    _keep(rect(x0 - 4.0, x1 + 2.0, z0 - 2.0, z1 + 2.0))


# ================================================================ scatter
PUMP_Y: dict = {}
BUBBLE_Y = [0.0]


def _pumpjacks(b: ArenaArea, land: Land) -> None:
    """Where the pumpjacks stand: a concrete pad under each, levelled into
    the ground it is on (the jacks themselves are rigs)."""
    for x, z in ((-86.0, -150.0), (64.0, -92.0), (-96.0, 88.0), (150.0, 112.0), (210.0, -110.0), (-250.0, -60.0),
                 (-250.0, 60.0), (250.0, 66.0)):
        y = land.height(x, z)
        PUMP_Y[(x, z)] = y + 0.4
        b.box([x, y + 0.2, z], [6.0, 0.4, 13.0], "#8a8680")
        _keep(rect(x - 8.0, x + 8.0, z - 8.0, z + 8.0))


def _scatter(b: ArenaArea, rng: random.Random, land: Land) -> None:
    """Oil-field clutter: barrels, pipe lengths, a broken wheel, tar pools,
    scrub -- never on a line or anything built."""
    tries = placed = 0
    hx, hz = HALF
    while placed < 110 and tries < 1800:
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
        if roll < 0.3:
            for k in range(rng.randint(1, 3)):
                rails.barrel(b, x + k * 2.8, z + (k % 2) * 1.6, rng.choice([CRUDE, "#5a3a22", "#3a4a5a"]), y=base)
        elif roll < 0.5:
            for k in range(3):
                b.cyl([x, base + 0.5 + k * 0.9, z + (k - 1) * 0.3], [0.9, 8.0, 0.9], "#5a5a5e",
                      r=[0.0, 0.0, math.pi / 2.0], material="metal")
        elif roll < 0.75:
            b.sphere([x, base + 0.8, z], [2.6, 1.6, 2.4], rng.choice(["#7a8a4a", "#8a8a50"]), collide=False)
        else:
            outcrop(b, x, z, rng.uniform(2.0, 3.6), rng.uniform(0.8, 1.6), rng.uniform(2.0, 3.0), base=base,
                    colour=rng.choice(["#8a7a5a", "#6a5a40"]))
        KEEP.append(rect(x - 4.0, x + 4.0, z - 4.0, z + 4.0))
        placed += 1


# =================================================================== rigs
def _rigs(b: ArenaArea) -> None:
    wind = [0.8, 0.3]
    b.rig("rr_flame", -264.0, 26.0, 238.0, s=1.4, wind=wind)
    b.rig("rr_walking_beam", -66.0, 1.0 + 7.0, 202.0, yaw=math.pi / 2.0, l=14.0)
    for x, z, y in ((-314.0, 244.0, 28.0), (-343.0, -240.0, 0.0)):
        if y > 0:
            b.rig("rr_smoke", x, y, z, wind=wind, rate=0.16, h=30.0, colour="#3a3634", size=2.6)
    for spot in WELL_SPOTS:
        ex, ez, _ = beside(LANE_OF[spot["lane"]], spot["d"], spot["side"] * (WELL_OFF + 9.0))
        b.rig("rr_smoke", ex + 2.0, spot["y"] + 11.0, ez, wind=wind, rate=0.3, h=12.0, size=1.0, colour="#6a6460")
    b.rig("rr_smoke", 176.0, 25.0, 6.0, wind=wind, rate=0.2, h=20.0, colour="#5a5450")
    # the Big Strike, gushing for weeks out past the fence
    b.rig("rr_smoke", 520.0, 0.0, -420.0, wind=wind, rate=0.12, h=120.0, n=14, size=8.0, colour="#1e1a18")
    for k, (a, c) in enumerate((((-240.0, 4.0, -40.0), (-120.0, 4.0, -10.0)), ((40.0, 4.0, 60.0), (180.0, 4.0, 80.0)),
                                ((60.0, 4.0, -60.0), (200.0, 4.0, -40.0)))):
        b.rig("rr_tumbleweed", a[0], a[1], a[2], q=list(c), speed=10.0 + k, seed=k * 1.9)
    b.rig("rr_flag", EXCHANGE[0] + 4.0, 22.0, 0.0, w=4.0, h=2.4, yaw=math.atan2(-wind[0], -wind[1]),
          colours=["#c8281e", "#f2ece0", "#2f4a8a"])
    # strings of coloured lights zig-zagging over Main Street
    x0 = STREET_X
    for k, z in enumerate((-90.0, -10.0, 70.0)):
        b.rig("rr_lights", x0 + 9.4, 1.0 + 11.6, z, q=[x0 - 7.0, 1.0 + 11.6, z + 30.0], n=16, sag=2.6)
        if k < 2:
            b.rig("rr_lights", x0 - 7.0, 1.0 + 11.6, z + 30.0, q=[x0 + 9.4, 1.0 + 11.6, z + 80.0], n=18, sag=3.0)
    # pumpjacks nodding over the field
    for k, (x, z, yaw) in enumerate(((-86.0, -150.0, 0.4), (64.0, -92.0, 1.9), (-96.0, 88.0, 2.6), (150.0, 112.0, 1.1),
                                     (210.0, -110.0, 0.2), (-250.0, -60.0, 1.5), (-250.0, 60.0, 3.1), (250.0, 66.0, 2.2))):
        b.rig("rr_pumpjack", x, PUMP_Y.get((x, z), 0.0), z, yaw=yaw, seed=k * 1.7, rate=1.1 + (k % 3) * 0.2,
              colour=("#c8a02a", "#c8281e", "#2f6aa8", "#3a8a3a")[k % 4])
    b.rig("rr_bubbles", 100.0, BUBBLE_Y[0] + 0.12, 198.0, w=18.0, d=9.0, n=8)

