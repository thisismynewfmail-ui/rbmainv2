"""Silverpine Pass -- a snowbound summit line between a silver mine and a
logging camp, first thing on a winter morning.

Layout (north is -z; both tracks run west to east)::

    z -250 ================= THE MOUNTAIN (Silver Crown Mine) ==================
           NORTH YARD     falls  SILVERPINE    the mine, the tipple   SILVER CROWN
           (coaling twr)   \\    LAKE (frozen)   the smelter            (lane b end)
             lane a -----\\  \\===trestle======\\           /==SNOW SHED==/
    z    0      the woods  | footbridge      SUMMIT JUNCTION  the plow shed
             lane b -----/  /===trestle======/           \\==SNOW SHED==\\
           SOUTH YARD           the boathouse   the lodge, the rink     TIMBERLINE
           (coaling twr)                         the sawmill, log decks (lane a end)
    z +250 ================== THE FOREST ========================================

Both lines cross Silverpine Lake on trestles (the ice is seven units down,
and walkable: a footbridge and the docks' stairs come and go from it), meet
at the summit, and run through a snow shed each -- a roofed gallery with a
solid uphill wall, slits to shoot through, and a roof to fight on -- before
the long drop to the termini.  Snowdrifts come down on the track here; the
rules have pushers dig them out.
"""
from __future__ import annotations

import math
import random

from ..kit import (
    WARM, WOOD, WOOD_DARK, ArenaArea, backdrop, building, flight, ground, lantern,
    perimeter, rect, sign_decal, slab, threshold, wall_sign)
from . import rails
from .rails import (
    barrel, beside, boxcar, buffer_stop, caboose, clear_of, coal_heap,
    coaling_tower, crate_stack, depot, fillet, fir, flatcar, handcar, lay_track,
    length, lever, log_pile, mile_post, mirror, rock, sleeper_pile, snow_shed,
    snowy_gable, span_of, split_at, stair, telegraph, wagon, water_tower, yard)

HALF = (400.0, 250.0)
SKY = {"top": "#4f78b0", "horizon": "#dfe8f2", "sun": [0.35, 0.42, 0.55],
       "clouds": 0.55, "tint": "#eaf2ff"}
AMBIENT = "#aab6ca"
GROUND = "#e8eef4"
FOG = 620.0

SNOW = "#eef2f6"
SNOW_SHADE = "#d4dde8"
ICE = "#a8d0e8"
ICE_DARK = "#7aaed0"
ROCK = "#7a8088"
ROCK_DARK = "#5a6068"
ROCK_LIGHT = "#9aa0a8"
PINE = "#2a5a3c"
PINE_DARK = "#1e4a30"
LOG = "#7a5232"
LOG_DARK = "#5a3a22"
STONE = "#8a8a86"

LAKE_X = (-150.0, -80.0)
LAKE_Z = (-150.0, 150.0)
ICE_TOP = -7.0
BRIDGE_X = (-156.0, -74.0)
SHED_X = (74.0, 154.0)

_CORNERS = [(-372.0, -170.0), (-262.0, -170.0), (-180.0, -90.0), (-40.0, -90.0),
            (40.0, 90.0), (180.0, 90.0), (262.0, 170.0), (372.0, 170.0)]
LANE_A = split_at(fillet(_CORNERS, radius=36.0, step=4.0), xs=BRIDGE_X + SHED_X)
LANE_B = mirror(LANE_A)

# the lake: a long finger of ice, with a bay off each shore and narrower
# ends, so its edge is never a ruler line
LAKE = [rect(LAKE_X[0], LAKE_X[1], LAKE_Z[0], LAKE_Z[1]),
        rect(-164.0, -150.0, -40.0, 30.0), rect(-80.0, -66.0, 10.0, 60.0),
        rect(-140.0, -96.0, -172.0, -150.0), rect(-136.0, -100.0, 150.0, 168.0)]

KEEP: list = []


def _free(area, margin: float = 3.0) -> bool:
    x0, x1, z0, z1 = area
    return all(x1 + margin <= k[0] or x0 - margin >= k[1] or
               z1 + margin <= k[2] or z0 - margin >= k[3] for k in KEEP)


def _wet(x0: float, x1: float, z0: float, z1: float, margin: float = 2.0) -> bool:
    """Does the rectangle touch the lake?"""
    return any(x1 + margin > h[0] and x0 - margin < h[1] and
               z1 + margin > h[2] and z0 - margin < h[3] for h in LAKE)


def build(b: ArenaArea) -> None:
    rng = random.Random(0x5117)
    del KEEP[:]
    b.extra.update({"accent": "#8fd0ff", "twist": "drifts",
                    "lanes": {"a": _world(b, LANE_A), "b": _world(b, LANE_B)},
                    "names": {"a": "the north line", "b": "the south line"},
                    "bridges": [list(span_of(LANE_A, BRIDGE_X[0], BRIDGE_X[1], -100, -80))]})
    ground(b, SNOW, soil=ROCK_DARK, material="plastic", holes=LAKE)
    perimeter(b, 46.0, ROCK, SNOW, rng, ragged=26.0)
    backdrop(b, "peaks", 0.0, rng, [ROCK, ROCK_DARK, "#6a7480"], depth=170.0)
    backdrop(b, "pines", 0.0, rng, [PINE_DARK, PINE], sides=("z+", "x-"), depth=70.0)
    _lake(b, rng)
    for path in (LANE_A, LANE_B):
        a, c = span_of(path, BRIDGE_X[0], BRIDGE_X[1], -100.0, 100.0)
        lay_track(b, path, skip=[(a + 0.01, c - 0.01)])
    _bridges(b)
    _yards(b)
    _termini(b)
    _depots(b)
    for kind, (hx, hz) in (("depot", (24.0, 12.0)), ("lever", (5.0, 5.0))):
        for entry in b.points.get(kind, []):
            x, z = entry["p"][0] - b.ox, entry["p"][2] - b.oz
            KEEP.append(rect(x - hx, x + hx, z - hz, z + hz))
    _sheds(b)
    _summit(b, rng)
    _mine(b, rng)
    _camp(b, rng)
    _lodge(b, rng)
    _woods(b, rng)
    _coaling(b, rng)
    _scatter(b, rng)
    telegraph(b, LANE_A, -1.0)
    telegraph(b, LANE_B, 1.0)
    for f, label in ((0.12, "MP 1"), (0.5, "MP 2"), (0.88, "MP 3")):
        mile_post(b, LANE_A, f, -1.0, label)
        mile_post(b, LANE_B, f, 1.0, label)
    for x, z, name in ((-350, -170, "the north yard"), (-350, 170, "the south yard"),
                       (350, -170, "Silver Crown"), (350, 170, "Timberline"),
                       (-115, 0, "Silverpine Lake"), (-115, -90, "the north trestle"),
                       (-115, 90, "the south trestle"), (0, 0, "Summit Junction"),
                       (114, -90, "the north snow shed"), (114, 90, "the south snow shed"),
                       (0, -205, "the Silver Crown Mine"), (-118, -190, "Silverpine Falls"),
                       (230, -215, "the smelter"), (235, 220, "the sawmill"),
                       (0, 200, "the lodge"), (-300, 0, "the fire lookout"),
                       (58, 0, "the plow shed"), (-70, 125, "the boathouse")):
        b.landmark(float(x), float(z), name)
    b.camera(-260.0, 60.0, 40.0, -110.0, -4.0, 0.0)
    b.camera(240.0, 55.0, -20.0, 110.0, 6.0, 90.0)
    b.camera(0.0, 70.0, 180.0, 0.0, 0.0, -30.0)


def _world(b: ArenaArea, path):
    return [b.at(x, 0.0, z) for x, z in path]


def _lane_free(area, margin: float = 9.0) -> bool:
    return clear_of(area, (LANE_A, LANE_B), margin)


# ==================================================================== lake
def _lake(b: ArenaArea, rng: random.Random) -> None:
    """Ice seven units down, rock banks lined to the bottom, docks with
    stairs at both shores, a fishing camp on the ice, and the frozen falls
    at the north end."""
    for h in LAKE:
        slab(b, h, ICE_TOP, 1.4, ICE, studs=False)
    # the banks: the ground's soil only goes six down, so a lining of rock
    # closes the last unit round every edge of the hole (each strip carved
    # round the lake and round the strips already laid, so none overlap)
    from ..kit import carve
    laid = []
    for h in LAKE:
        x0, x1, z0, z1 = h
        for r in (rect(x0 - 1.0, x0, z0 - 1.0, z1 + 1.0), rect(x1, x1 + 1.0, z0 - 1.0, z1 + 1.0),
                  rect(x0, x1, z0 - 1.0, z0), rect(x0, x1, z1, z1 + 1.0)):
            for p in carve(r, LAKE + laid):
                if p[1] - p[0] > 0.05 and p[3] - p[2] > 0.05:
                    slab(b, p, -6.0, -6.0 - ICE_TOP, ROCK_DARK)
                    laid.append(p)
    KEEP.extend(LAKE)
    # cracks and fishing holes on the ice (paint)
    for k in range(9):
        x = rng.uniform(LAKE_X[0] + 8, LAKE_X[1] - 8)
        z = rng.uniform(-130.0, 130.0)
        if abs(abs(z) - 90.0) < 12.0 or abs(z) < 8.0:
            continue
        b.cyl([x, ICE_TOP + 0.02, z], [2.2, 0.04, 2.2], "#2a4a60", collide=False)
    for k in range(7):
        x = rng.uniform(LAKE_X[0] + 6, LAKE_X[1] - 6)
        z = rng.uniform(-140.0, 140.0)
        b.box([x, ICE_TOP + 0.015 + k * 0.001, z], [rng.uniform(8, 16), 0.03, 0.3], "#d8ecf8",
              r=[0, rng.uniform(0, math.pi), 0], collide=False)
    # the ice-fishing camp: three huts, a sled and a stack of traps
    for x, z, colour in ((-128.0, -40.0, "#b8322a"), (-104.0, -52.0, "#2f6aa8"),
                         (-118.0, 46.0, "#d8a83a")):
        building(b, rect(x - 4.0, x + 4.0, z - 3.5, z + 3.5), ICE_TOP, 7.0, colour,
                 roof_colour="#4a3a2e", doors={"z+": [(x - 2.0, x + 2.0, ICE_TOP + 6.2)]},
                 lights="", studs_roof=False)
        slab(b, rect(x - 4.6, x + 4.6, z - 4.1, z + 4.1), ICE_TOP + 7.0 + 1.2 + 0.4, 0.4, SNOW)
        b.box([x + 2.6, ICE_TOP + 8.7, z - 1.6], [0.8, 1.8, 0.8], "#3a3632")
    wagon(b, -96.0, 20.0, "z", "#c8d8e0")
    # docks with stairs down onto the ice, both shores
    for x0, x1, z, near, far, xs in ((-150.0, -136.0, -120.0, -136.0, -150.0, None),
                                     (-150.0, -136.0, 120.0, -136.0, -150.0, None),
                                     (-94.0, -80.0, -60.0, -94.0, -80.0, None),
                                     (-94.0, -80.0, 130.0, -94.0, -80.0, None)):
        flight(b, "x", near, far, z - 3.0, z + 3.0, ICE_TOP, 0.0, WOOD, fill=ICE_TOP)
    # the frozen falls: a rock step north of the lake, the falls hanging
    # frozen down its face into the lake's tip, a path up its west side
    b.box([-118.0, 10.0, -194.0], [52.0, 20.0, 36.0], ROCK)
    b.box([-121.0, 23.0, -199.0], [40.0, 6.0, 26.0], ROCK_DARK)
    b.box([-112.0, 27.5, -203.0], [22.0, 3.0, 14.0], ROCK)
    for x, z, w, h, d in ((-146.5, -192.0, 5.0, 13.0, 16.0), (-89.5, -190.0, 5.0, 16.0, 22.0),
                          (-100.0, -207.0, 12.0, 24.0, 13.0)):
        b.box([x, h / 2.0, z], [w, h, d], ROCK_DARK)
    for k, (x, w, top) in enumerate(((-136.0, 4.6, 16.0), (-130.5, 5.4, 20.0),
                                     (-124.4, 5.0, 20.0), (-118.6, 5.6, 20.0),
                                     (-112.6, 5.0, 18.0), (-106.8, 5.4, 20.0),
                                     (-101.0, 4.4, 13.0))):
        b.box([x, top / 2.0, -175.6 + (k % 2) * 0.05], [w, top, 0.8 + (k % 2) * 0.1],
              (ICE, "#bfe0f2", ICE_DARK)[k % 3])
    slab(b, rect(-152.0, -144.0, -196.0, -184.0), 20.0, 20.3, ROCK_LIGHT)
    stair(b, "z", -166.0, -184.0, -152.0, -144.0, 0.0, 20.0, ROCK_LIGHT)
    b.mark("perch", -118.0, 20.0, -180.0)
    KEEP.append(rect(-156.0, -86.0, -214.0, -164.0))


# ================================================================= bridges
def _bridges(b: ArenaArea) -> None:
    """Both lines cross the lake on a timber trestle, decks at track height,
    bents down to the ice, and a rail along each edge; a footbridge crosses
    in the middle for anyone on foot."""
    for z in (-90.0, 90.0):
        deck = rect(BRIDGE_X[0], BRIDGE_X[1], z - 6.0, z + 6.0)
        slab(b, deck, rails.BALLAST_TOP, 1.0, "#6a5040", studs=True)
        for x in range(int(LAKE_X[0]) + 6, int(LAKE_X[1]) - 2, 8):
            b.box([x, (ICE_TOP - 0.82) / 2.0, z], [1.2, -0.82 - ICE_TOP - 0.6, 11.0], LOG_DARK)
            b.box([x, -1.12, z], [1.6, 0.6, 12.0], LOG)
        for e in (-1.0, 1.0):
            for x in range(int(BRIDGE_X[0]) + 2, int(BRIDGE_X[1]), 6):
                b.box([x, rails.BALLAST_TOP + 1.3, z + e * 5.6], [0.5, 2.6, 0.5], LOG_DARK)
            b.box([(BRIDGE_X[0] + BRIDGE_X[1]) / 2.0, rails.BALLAST_TOP + 2.5, z + e * 5.6],
                  [BRIDGE_X[1] - BRIDGE_X[0], 0.4, 0.4], LOG)
        KEEP.append(rect(BRIDGE_X[0] - 4.0, BRIDGE_X[1] + 4.0, z - 8.0, z + 8.0))
    # the footbridge, a step up from the shore at both ends
    foot = rect(-172.0, -74.0, -3.0, 3.0)
    slab(b, foot, 0.5, 0.5, WOOD, studs=True)
    for x in range(-160, -74, 10):
        if LAKE_X[0] < x < LAKE_X[1] or -164 < x < -150:
            b.box([x, (ICE_TOP + 0.0) / 2.0, 0.0], [1.0, -ICE_TOP, 1.0], LOG_DARK)
    for e in (-1.0, 1.0):
        for x in range(-170, -74, 8):
            b.box([x, 1.7, e * 2.7], [0.4, 2.4, 0.4], LOG_DARK)
        b.box([-123.0, 2.7, e * 2.7], [96.0, 0.3, 0.3], LOG)
    KEEP.append(rect(foot[0], foot[1], -5.0, 5.0))


# =================================================================== yards
def _yards(b: ArenaArea) -> None:
    """The two starting yards at the west end, each with a coaling tower
    astride its line and an engine house behind."""
    for lane, z, side, name, roof in (("a", -170.0, -1.0, "SILVERPINE NORTH YARD", "#6a3a2a"),
                                      ("b", 170.0, 1.0, "SILVERPINE SOUTH YARD", "#2a4a6a")):
        area = yard(b, lane, -380.0, -326.0, z, side, name, roof)
        slab(b, rect(area[0] + 0.1, area[1] - 0.1, area[2] + 0.1, area[3] - 0.1), 1.2 + 0.3, 0.3,
             SNOW)
        coaling_tower(b, -296.0, z, "x")
        house = rect(-392.0, -344.0, -244.0, -214.0) if side < 0 else \
            rect(-392.0, -344.0, 214.0, 244.0)
        building(b, house, 0.0, 16.0, "#6a4a30", roof_colour=roof,
                 doors={"x+": [(house[2] + 6.0, house[3] - 6.0, 13.0)]},
                 windows={"z+" if side < 0 else "z-": [(-386.0, -372.0, 6.0, 10.0),
                                                       (-364.0, -350.0, 6.0, 10.0)]},
                 glass=True, lights=WARM)
        threshold(b, house, "x+", (house[2] + 6.0, house[3] - 6.0))
        snowy_gable(b, house, 17.2, roof, "x", 4, 1.4, 0.6)
        KEEP.append(rect(-400.0, -280.0, min(z, area[2]) - 12.0, max(z, area[3]) + 12.0))
        KEEP.append(house)
    # a snowplow engine waits on a stub between the yards
    lay_track(b, [(-390.0, 0.0), (-330.0, 0.0)])
    buffer_stop(b, -386.0, 0.0, math.pi / 2.0, rails.RED)
    _plow(b, -356.0, 0.0)
    KEEP.append(rect(-392.0, -326.0, -6.0, 6.0))


def _plow(b: ArenaArea, x: float, z: float, facing: float = 1.0) -> None:
    """A rotary snowplow: a boxy body on trucks, the big rotor housing at the
    front, its blades painted on."""
    boxcar(b, x, z, "x", "#b8322a", "SILVERPINE", door="shut", length=18.0)
    fx = x + facing * 10.6
    b.box([fx, 4.4, z], [3.2, 7.2, 7.0], "#2a2826", material="metal")
    b.cyl([fx + facing * 1.62, 4.4, z], [6.4, 0.04, 6.4], "#e8b23a", collide=False,
          r=[0, 0, math.pi / 2.0], material="metal")
    for k in range(4):
        a = k * math.pi / 4.0
        b.box([fx + facing * 1.66, 4.4, z], [0.04, 5.6, 0.5], "#2a2826", collide=False,
              r=[a, 0, 0])


# ================================================================== termini
def _termini(b: ArenaArea) -> None:
    for lane, z, side, name, roof in (("a", 170.0, 1.0, "TIMBERLINE", "#2a4a6a"),
                                      ("b", -170.0, -1.0, "SILVER CROWN", "#6a3a2a")):
        area = yard(b, lane, 326.0, 380.0, z, side, name, roof, sign=(rails.GOLD, "#3a2414"),
                    end="finish")
        slab(b, rect(area[0] + 0.1, area[1] - 0.1, area[2] + 0.1, area[3] - 0.1), 1.5, 0.3, SNOW)
        house = rect(332.0, 384.0, z + side * 24.0, z + side * 46.0) if side > 0 else \
            rect(332.0, 384.0, z - 46.0, z - 24.0)
        building(b, house, 0.0, 13.0, STONE, roof_colour=roof, floor_colour="#6a5a4a",
                 doors={"x-": [(house[2] + 6.0, house[3] - 6.0, 9.0)]},
                 windows={"z-" if side > 0 else "z+": [(336.0, 350.0, 4.0, 9.0),
                                                       (362.0, 376.0, 4.0, 9.0)]},
                 glass=True, lights=WARM)
        threshold(b, house, "x-", (house[2] + 6.0, house[3] - 6.0))
        snowy_gable(b, house, 14.2, roof, "x", 4, 1.3, 0.8)
        KEEP.append(rect(300.0, 400.0, min(z, area[2], house[2]) - 8.0,
                         max(z, area[3], house[3]) + 8.0))


# ================================================================== depots
def _depots(b: ArenaArea) -> None:
    depot(b, "a", LANE_A, 0.2, 1.0, "LAKESIDE", 1, "#6a3a2a")
    depot(b, "a", LANE_A, 0.8, -1.0, "SAWMILL SIDING", 2, "#2a4a6a")
    depot(b, "b", LANE_B, 0.2, -1.0, "LAKESIDE SOUTH", 1, "#2a4a6a")
    depot(b, "b", LANE_B, 0.8, 1.0, "TIPPLE SIDING", 2, "#6a3a2a")
    for lane, path, sides in (("a", LANE_A, (-1.0, 1.0)), ("b", LANE_B, (1.0, -1.0))):
        for index, (f, side) in enumerate(zip((0.41, 0.64), sides)):
            lever(b, lane, path, f, side, index)


# ================================================================== sheds
def _sheds(b: ArenaArea) -> None:
    """A snow shed over each line on the east side of the summit, its solid
    wall on the uphill (outer) side."""
    snow_shed(b, SHED_X[0], SHED_X[1], -90.0, -1.0)
    snow_shed(b, SHED_X[0], SHED_X[1], 90.0, 1.0)
    for z in (-90.0, 90.0):
        KEEP.append(rect(SHED_X[0] - 4.0, SHED_X[1] + 4.0, z - 16.0, z + 16.0))
        wall_sign(b, (SHED_X[0] + SHED_X[1]) / 2.0, 15.6, z + (-1 if z < 0 else 1) * 10.05,
                  30.0, 2.4, sign_decal("SNOW SHED No. %d" % (1 if z < 0 else 2), "#3a2414",
                                        rails.CREAM, 12.5),
                  "z+" if z > 0 else "z-", "#3a2414")
    # snow fences up the slopes above each shed
    for z in (-120.0, 120.0):
        for k in range(5):
            x = SHED_X[0] + 6.0 + k * 16.0
            b.box([x, 1.6, z], [12.0, 3.2, 0.4], LOG_DARK)
            for e in (-5.6, 0.0, 5.6):
                b.box([x + e, 2.0, z], [0.5, 4.0, 0.5], LOG)


# ================================================================== summit
def _summit(b: ArenaArea, rng: random.Random) -> None:
    """Where the lines cross: the summit station on the west side, the
    plow shed and a water tower on the east, a cairn on the high point."""
    station = rect(-62.0, -36.0, -14.0, 14.0)
    building(b, station, 0.0, 10.0, STONE, roof_colour="#3a3a44", floor_colour="#6a5a4a",
             doors={"x+": [(-4.0, 4.0, 7.5)], "x-": [(-4.0, 4.0, 7.5)]},
             windows={"z-": [(-58.0, -50.0, 3.5, 7.5), (-48.0, -40.0, 3.5, 7.5)],
                      "z+": [(-58.0, -50.0, 3.5, 7.5), (-48.0, -40.0, 3.5, 7.5)]},
             glass=True, lights=WARM)
    threshold(b, station, "x+", (-4.0, 4.0))
    threshold(b, station, "x-", (-4.0, 4.0))
    snowy_gable(b, station, 11.2, "#3a3a44", "z", 4, 1.4, 1.0)
    wall_sign(b, -35.65, 8.6, 0.0, 14.0, 1.8,
              sign_decal("SUMMIT  7,000 FT", rails.CREAM, "#2a2a34", 7.8), "x+", rails.CREAM)
    KEEP.append(rect(-64.0, -34.0, -16.0, 16.0))
    # the plow shed: a long engine house on a stub, its doors open west
    shed = rect(46.0, 92.0, -14.0, 14.0)
    lay_track(b, [(30.0, 0.0), (88.0, 0.0)])
    building(b, shed, 0.0, 15.0, "#6a4a30", roof_colour="#3a2e26",
             doors={"x-": [(-8.0, 8.0, 12.0)]},
             windows={"z-": [(56.0, 66.0, 6.0, 10.0), (72.0, 82.0, 6.0, 10.0)],
                      "z+": [(56.0, 66.0, 6.0, 10.0), (72.0, 82.0, 6.0, 10.0)]},
             glass=True, lights=WARM)
    snowy_gable(b, shed, 16.2, "#3a2e26", "x", 4, 1.4, 0.6)
    _plow(b, 70.0, 0.0, -1.0)
    buffer_stop(b, 86.0, 0.0, math.pi / 2.0, rails.RED)
    KEEP.append(rect(28.0, 94.0, -16.0, 16.0))
    water_tower(b, 30.0, -36.0)
    KEEP.append(rect(20.0, 56.0, -46.0, -26.0))
    # the cairn and its flag on the high point north of the crossing
    for k, (w, h) in enumerate(((7.0, 1.6), (5.0, 1.6), (3.0, 1.6))):
        b.box([-6.0, 0.8 + k * 1.6, -40.0], [w, h, w], STONE)
    b.box([-6.0, 8.8, -40.0], [0.3, 8.0, 0.3], WOOD_DARK)
    b.box([-4.7, 11.6, -40.0], [2.4, 1.6, 0.1], "#c4281c", collide=False)
    KEEP.append(rect(-10.0, -2.0, -44.0, -36.0))
    # troughs of coal, the signal post and a few crates round the diamond
    for x, z in ((-22.0, 16.0), (22.0, -16.0)):
        crate_stack(b, x, z, rng)
        KEEP.append(rect(x - 3.0, x + 3.0, z - 3.0, z + 3.0))
    for x, z in ((-16.0, -20.0), (16.0, 20.0)):
        b.box([x, 4.0, z], [0.6, 8.0, 0.6], rails.IRON, material="metal")
        b.box([x, 7.4, z], [1.4, 2.4, 0.8], "#2a2826", material="metal")
        b.box([x, 7.9, z + 0.42], [0.6, 0.6, 0.04], "#ff3a2a", material="neon", collide=False)
        b.box([x, 6.9, z + 0.42], [0.6, 0.6, 0.04], "#3aff6a", material="neon", collide=False)


# ==================================================================== mine
def _mine(b: ArenaArea, rng: random.Random) -> None:
    """The Silver Crown Mine in the mountain north of the summit: its
    portal, the ore tipple on stilts with a stair up, the bunkhouses, and
    the smelter with its stacks further east."""
    hz = b.half_z
    # the portal, timbered, with a short adit into the rock
    from ..kit import room_walls
    room_walls(b, rect(-14.0, 14.0, -hz, -hz + 26.0), 2.0, 0.0, 14.0, ROCK_DARK,
               doors={"z+": [(-7.0, 7.0, 11.0)]})
    slab(b, rect(-15.0, 15.0, -hz, -hz + 26.0), 15.2, 1.2, ROCK_DARK)
    slab(b, rect(-14.6, 14.6, -hz + 0.4, -hz + 25.6), 15.8, 0.6, SNOW)
    b.box([0.0, 12.0, -hz + 26.7], [20.0, 2.0, 1.4], LOG_DARK)
    for dx in (-9.0, 9.0):
        b.box([dx, 5.5, -hz + 26.7], [2.0, 11.0, 1.4], LOG_DARK)
    wall_sign(b, 0.0, 16.6, -hz + 25.5, 20.0, 2.0,
              sign_decal("SILVER CROWN MINE", rails.CREAM, "#2a2a34", 10.0), "z+", rails.CREAM)
    lantern(b, 0.0, 14.0, -hz + 14.0, WARM)
    lay_track(b, [(0.0, -hz + 4.0), (0.0, -150.0)], sleeper_every=2.4)
    for k in range(3):
        z = -hz + 10.0 + k * 22.0
        b.box([0.0, 2.2, z], [4.4, 3.2, 6.0], "#5a5550", material="metal")
        b.box([0.0, 4.3, z], [4.0, 1.0, 5.4], "#c8ccd0", material="metal")
    KEEP.append(rect(-16.0, 16.0, -hz, -148.0))
    # the ore tipple: a timber bin on stilts over the mine track, stair up
    tx, tz = 0.0, -168.0
    for dx in (-7.0, 7.0):
        for dz in (-6.0, 6.0):
            b.box([tx + dx, 7.5, tz + dz], [1.4, 15.0, 1.4], LOG_DARK)
    b.box([tx, 19.0, tz], [16.0, 8.0, 14.0], "#6a4a30")
    slab(b, rect(tx - 9.0, tx + 9.0, tz - 8.0, tz + 8.0), 23.8, 0.8, "#3a2e26")
    slab(b, rect(tx - 8.6, tx + 8.6, tz - 7.6, tz + 7.6), 24.3, 0.5, SNOW)
    slab(b, rect(tx + 8.0, tx + 22.0, tz - 3.0, tz + 3.0), 15.0, 0.8, WOOD)
    stair(b, "x", tx + 40.0, tx + 22.0, tz - 3.0, tz + 3.0, 0.0, 15.0, WOOD)
    b.mark("perch", tx + 15.0, 15.0, tz)
    KEEP.append(rect(tx - 10.0, tx + 42.0, tz - 9.0, tz + 9.0))
    # bunkhouses along the mountain's foot
    for x in (-50.0, 46.0):
        cabin = rect(x - 12.0, x + 12.0, -238.0, -220.0)
        if not _lane_free(cabin) or not _free(cabin):
            continue
        building(b, cabin, 0.0, 9.0, LOG, roof_colour="#3a2e26", floor_colour="#5a4632",
                 doors={"z+": [(x - 2.0, x + 2.0, 7.0)]},
                 windows={"z+": [(x - 9.0, x - 5.0, 3.5, 6.5), (x + 5.0, x + 9.0, 3.5, 6.5)]},
                 glass=True, lights=WARM)
        threshold(b, cabin, "z+", (x - 2.0, x + 2.0))
        snowy_gable(b, cabin, 10.2, "#3a2e26", "x", 3, 1.4, 0.8)
        b.box([x + 8.0, 13.0, -229.0], [2.0, 4.0, 2.0], STONE)
        KEEP.append(cabin)
    # the smelter: a big stone hall, two brick stacks, slag heaps
    hall = rect(196.0, 264.0, -240.0, -196.0)
    building(b, hall, 0.0, 20.0, STONE, roof_colour="#3a3a44", floor_colour="#4a4a4a",
             doors={"z+": [(214.0, 226.0, 12.0), (236.0, 248.0, 12.0)]},
             windows={"x-": [(-230.0, -206.0, 10.0, 16.0)], "x+": [(-230.0, -206.0, 10.0, 16.0)]},
             glass=True, lights="#ffb35a")
    threshold(b, hall, "z+", (214.0, 226.0))
    threshold(b, hall, "z+", (236.0, 248.0))
    for x in (208.0, 252.0):
        b.box([x, 21.2 + 14.0, -228.0], [6.0, 28.0, 6.0], "#8a3a2a")
        b.box([x, 21.2 + 28.6, -228.0], [7.0, 1.2, 7.0], "#6a2a1e")
    wall_sign(b, 230.0, 17.0, -195.65, 30.0, 2.6,
              sign_decal("SILVER CROWN SMELTING CO.", "#2a2a34", rails.CREAM, 11.5), "z+",
              "#2a2a34")
    KEEP.append(rect(hall[0] - 2.0, hall[1] + 2.0, hall[2], hall[3] + 4.0))
    for x, z in ((180.0, -214.0), (284.0, -222.0)):
        rock(b, x, z, 12.0, 6.0, 10.0, "#3a3632")
        KEEP.append(rect(x - 7.0, x + 7.0, z - 6.0, z + 6.0))
    # ore cars waiting on a spur in front of the smelter
    lay_track(b, [(190.0, -180.0), (290.0, -180.0)])
    buffer_stop(b, 192.0, -180.0, math.pi / 2.0, rails.RED)
    buffer_stop(b, 288.0, -180.0, math.pi / 2.0, rails.RED)
    flatcar(b, 214.0, -180.0, "x", "crates", rng)
    boxcar(b, 240.0, -180.0, "x", "#5a5a64", "SILVER CROWN", door="open")
    caboose(b, 266.0, -180.0, "x", "#6a3a2a")
    KEEP.append(rect(188.0, 292.0, -185.0, -175.0))


# ================================================================ the camp
def _camp(b: ArenaArea, rng: random.Random) -> None:
    """Timberline's logging camp south-east of the summit: the sawmill and
    its log deck, the cookhouse, bunks, and log piles everywhere."""
    mill = rect(204.0, 270.0, 200.0, 244.0)
    building(b, mill, 0.0, 18.0, LOG, roof_colour="#3a2e26", floor_colour="#5a4632",
             doors={"z-": [(214.0, 230.0, 12.0), (244.0, 260.0, 12.0)]},
             windows={"x-": [(212.0, 232.0, 8.0, 13.0)], "x+": [(212.0, 232.0, 8.0, 13.0)]},
             glass=False, boards=True, lights=WARM)
    threshold(b, mill, "z-", (214.0, 230.0))
    threshold(b, mill, "z-", (244.0, 260.0))
    snowy_gable(b, mill, 19.2, "#3a2e26", "x", 5, 1.5, 1.0)
    # the saw inside and its carriage
    b.box([237.0, 2.0, 222.0], [30.0, 4.0, 4.0], LOG_DARK)
    b.cyl([237.0, 6.0, 222.0], [7.0, 0.3, 7.0], "#c8ccd0", r=[math.pi / 2.0, 0, 0],
          material="metal", collide=False)
    b.box([237.0, 4.6, 222.0], [1.4, 1.2, 1.0], rails.IRON, material="metal")
    wall_sign(b, 237.0, 15.0, 199.65, 30.0, 2.6,
              sign_decal("TIMBERLINE LUMBER CO.", "#3a2414", rails.CREAM, 11.5), "z-", "#3a2414")
    KEEP.append(rect(mill[0] - 2.0, mill[1] + 2.0, mill[2] - 4.0, mill[3]))
    # the log deck in front: piles in rows, a step up per row
    for x, z, along in ((300.0, 214.0, "x"), (300.0, 234.0, "x"), (176.0, 226.0, "z")):
        spot = rect(x - 9.0, x + 9.0, z - 6.0, z + 6.0) if along == "x" else \
            rect(x - 6.0, x + 6.0, z - 9.0, z + 9.0)
        if _lane_free(spot) and _free(spot, 1.0):
            log_pile(b, x, z, along, 16.0, 3)
            KEEP.append(spot)
    # cookhouse and two bunks east of the junction's south side
    for x, z, name in ((92.0, 214.0, "COOKHOUSE"), (128.0, 226.0, "BUNKS")):
        cabin = rect(x - 12.0, x + 12.0, z - 9.0, z + 9.0)
        if not _lane_free(cabin) or not _free(cabin):
            continue
        building(b, cabin, 0.0, 9.0, LOG, roof_colour="#3a2e26", floor_colour="#5a4632",
                 doors={"z-": [(x - 2.0, x + 2.0, 7.0)]},
                 windows={"z-": [(x - 9.0, x - 5.0, 3.5, 6.5), (x + 5.0, x + 9.0, 3.5, 6.5)]},
                 glass=True, lights=WARM)
        threshold(b, cabin, "z-", (x - 2.0, x + 2.0))
        snowy_gable(b, cabin, 10.2, "#3a2e26", "x", 3, 1.4, 0.8)
        wall_sign(b, x, 8.0, z - 9.35, 10.0, 1.4,
                  sign_decal(name, "#3a2414", rails.CREAM, 7.0), "z-", "#3a2414")
        KEEP.append(cabin)
    # a log train on the camp spur
    lay_track(b, [(150.0, 180.0), (300.0, 180.0)])
    buffer_stop(b, 152.0, 180.0, math.pi / 2.0, rails.BLUE)
    buffer_stop(b, 298.0, 180.0, math.pi / 2.0, rails.BLUE)
    flatcar(b, 176.0, 180.0, "x", "timber", rng)
    flatcar(b, 200.0, 180.0, "x", "timber", rng)
    handcar(b, 222.0, 180.0, "x")
    KEEP.append(rect(148.0, 302.0, 175.0, 185.0))


# =================================================================== lodge
def _lodge(b: ArenaArea, rng: random.Random) -> None:
    """The Silverpine Lodge south of the summit: two storeys of log and
    stone, a balcony all along the front, an outside stair to its roof
    deck, and the skating rink and benches out front."""
    lodge = rect(-30.0, 30.0, 196.0, 230.0)
    building(b, lodge, 0.0, 9.0, STONE, roof_colour="#3a2e26", floor_colour="#6a4e34",
             doors={"z-": [(-4.0, 4.0, 7.2)]},
             windows={"z-": [(-24.0, -12.0, 3.2, 6.8), (12.0, 24.0, 3.2, 6.8)],
                      "x-": [(204.0, 222.0, 3.2, 6.8)], "x+": [(204.0, 222.0, 3.2, 6.8)]},
             glass=True, lights=WARM, roof=False)
    threshold(b, lodge, "z-", (-4.0, 4.0))
    from ..kit import carve, plate
    plate(b, carve(lodge, [rect(6.0, 22.0, 200.0, 206.0)]), 10.0, 1.0, "#5a4632")
    building(b, lodge, 10.0, 8.0, LOG, roof_colour="#3a2e26", floor_colour="",
             doors={"z-": [(-3.0, 3.0, 16.2)]},
             windows={"z-": [(-26.0, -14.0, 13.0, 16.4), (14.0, 26.0, 13.0, 16.4)],
                      "x-": [(204.0, 222.0, 13.0, 16.4)], "x+": [(204.0, 222.0, 13.0, 16.4)]},
             glass=True, lights=WARM, roof_holes=[rect(-22.0, -8.0, 224.0, 229.0)],
             parapet=1.4)
    # the inside stair to the upper floor and the hatch to the roof
    stair(b, "x", 22.0, 6.0, 200.0, 206.0, 0.0, 10.0, WOOD)
    stair(b, "x", -8.0, -22.0, 224.0, 229.0, 10.0, 19.2, WOOD)
    # the balcony along the front, with its rail
    slab(b, rect(-30.0, 30.0, 188.0, 196.0), 10.0, 0.6, WOOD)
    for x in range(-28, 30, 7):
        b.box([x, 4.7, 188.6], [1.0, 9.4, 1.0], LOG_DARK)
        b.box([x, 11.2, 188.4], [0.4, 2.4, 0.4], LOG_DARK)
    b.box([0.0, 12.4, 188.4], [60.0, 0.4, 0.4], LOG)
    wall_sign(b, 0.0, 20.6, 195.65, 28.0, 3.0,
              sign_decal("SILVERPINE LODGE", "#3a2414", rails.GOLD, 9.3), "z-", "#3a2414")
    KEEP.append(rect(-32.0, 32.0, 186.0, 232.0))
    # the rink: ice laid on the snow, a low board round it, benches
    rink = rect(-26.0, 26.0, 140.0, 172.0)
    b.box([0.0, 0.03, 156.0], [52.0, 0.06, 32.0], ICE, collide=False)
    for x0, x1, z0, z1 in ((-27.0, 27.0, 139.0, 140.0), (-27.0, 27.0, 172.0, 173.0)):
        b.box([(x0 + x1) / 2.0 - 7.0, 0.6, (z0 + z1) / 2.0], [x1 - x0 - 14.0, 1.2, 1.0],
              "#efe2c4")
        b.box([x1 - 3.0, 0.6, (z0 + z1) / 2.0], [6.0, 1.2, 1.0], "#efe2c4")
    for x in (-27.0 + 0.5, 27.0 - 0.5):
        b.box([x, 0.6, 156.0], [1.0, 1.2, 32.0], "#efe2c4")
    for x in (-14.0, 0.0, 14.0):
        b.box([x, 0.8, 178.0], [6.0, 0.5, 1.6], LOG)
        for e in (-2.4, 2.4):
            b.box([x + e, 0.3, 178.0], [0.5, 0.6, 1.4], LOG_DARK)
    KEEP.append(rect(rink[0] - 2.0, rink[1] + 2.0, rink[2] - 2.0, rink[3] + 8.0))
    # the boathouse on the lake's east shore, steps to the ice inside
    house = rect(-66.0, -46.0, 112.0, 138.0)
    building(b, house, 0.0, 9.0, LOG, roof_colour="#3a2e26",
             doors={"x-": [(118.0, 132.0, 7.5)], "x+": [(122.0, 128.0, 7.0)]},
             lights=WARM)
    snowy_gable(b, house, 10.2, "#3a2e26", "z", 3, 1.4, 0.8)
    threshold(b, house, "x+", (122.0, 128.0))
    KEEP.append(rect(house[0] - 2.0, house[1] + 2.0, house[2] - 2.0, house[3] + 2.0))


# =================================================================== woods
def _woods(b: ArenaArea, rng: random.Random) -> None:
    """Firs wherever there is room, and a fire lookout in the western woods
    between the two yards."""
    # the lookout: a cabin on four legs, stair up its side
    lx, lz = -300.0, 0.0
    if lx:
        for dx in (-5.0, 5.0):
            for dz in (-5.0, 5.0):
                b.box([lx + dx, 9.0, lz + dz], [1.2, 18.0, 1.2], LOG_DARK)
        building(b, rect(lx - 7.0, lx + 7.0, lz - 7.0, lz + 7.0), 18.0, 7.0, LOG,
                 roof_colour="#3a2e26", floor_colour="#5a4632",
                 doors={"x+": [(-2.0, 2.0, 18.0 + 6.6)]},
                 windows={"z-": [(lx - 5.0, lx + 5.0, 20.0, 23.6)],
                          "z+": [(lx - 5.0, lx + 5.0, 20.0, 23.6)],
                          "x-": [(-5.0, 5.0, 20.0, 23.6)]}, glass=False, lights=WARM)
        snowy_gable(b, rect(lx - 7.0, lx + 7.0, lz - 7.0, lz + 7.0), 26.2, "#3a2e26", "z", 3,
                    1.2, 0.8)
        slab(b, rect(lx + 7.0, lx + 12.0, lz - 3.0, lz + 3.0), 18.0 + 0.6, 0.6, WOOD)
        stair(b, "z", lz + 32.0, lz + 3.0, lx + 7.0, lx + 12.0, 0.0, 18.6, WOOD)
        b.mark("perch", lx, 18.6, lz)
        KEEP.append(rect(lx - 9.0, lx + 14.0, lz - 9.0, lz + 34.0))
    # firs: thick in the west and along the south edge, scattered elsewhere
    spots = []
    for k in range(70):
        spots.append((rng.uniform(-392.0, -170.0), rng.uniform(-150.0, 150.0)))
    for k in range(40):
        spots.append((rng.uniform(-380.0, 380.0), rng.uniform(196.0, 244.0)))
    for k in range(30):
        spots.append((rng.uniform(-60.0, 380.0), rng.uniform(-150.0, 150.0)))
    for k in range(20):
        spots.append((rng.uniform(-380.0, 380.0), rng.uniform(-244.0, -196.0)))
    placed = []
    for x, z in spots:
        s = rng.uniform(1.0, 1.7)
        foot = rect(x - 6.0 * s, x + 6.0 * s, z - 6.0 * s, z + 6.0 * s)
        if not _lane_free(foot, 6.0) or not _free(foot, 1.0) or _wet(*foot):
            continue
        if any(math.hypot(x - px, z - pz) < 9.0 for px, pz in placed):
            continue
        if abs(x) > b.half_x - 6.0 or abs(z) > b.half_z - 6.0:
            continue
        placed.append((x, z))
        fir(b, x, z, s, rng.choice([PINE, PINE_DARK, "#2e6444"]), SNOW)
        KEEP.append(rect(x - 1.5 * s, x + 1.5 * s, z - 1.5 * s, z + 1.5 * s))


# ================================================================ coaling
def _coaling(b: ArenaArea, rng: random.Random) -> None:
    for x, z in ((-30.0, 34.0), (30.0, -60.0), (-200.0, 0.0), (190.0, 0.0)):
        coal_heap(b, x, z, rng)
        KEEP.append(rect(x - 5.0, x + 5.0, z - 5.0, z + 5.0))


# ================================================================ scatter
def _scatter(b: ArenaArea, rng: random.Random) -> None:
    """Rocks poking through the snow, and the track gang's leavings."""
    for k in range(40):
        x = rng.uniform(-380.0, 380.0)
        z = rng.uniform(-240.0, 240.0)
        w = rng.uniform(4.0, 9.0)
        h = rng.uniform(3.0, 8.0)
        spot = rect(x - w, x + w, z - w, z + w)
        if not _lane_free(spot, 8.0) or not _free(spot) or _wet(*spot, 4.0):
            continue
        if abs(x) > b.half_x - w - 2 or abs(z) > b.half_z - w - 2:
            continue
        rock(b, x, z, w * 1.4, h, w * 1.1, rng.choice([ROCK, ROCK_DARK, ROCK_LIGHT]))
        b.box([x, h * 0.7 + 0.15, z], [w * 1.0, 0.3, w * 0.8], SNOW_SHADE, collide=False)
        KEEP.append(spot)
    total = length(LANE_A)
    for f, side in ((0.07, 1.0), (0.33, -1.0), (0.55, 1.0), (0.7, -1.0), (0.93, 1.0)):
        for path, sgn in ((LANE_A, 1.0), (LANE_B, -1.0)):
            x, z, _ = beside(path, total * f, side * sgn * 12.0)
            x, z = round(x), round(z)
            spot = rect(x - 3.0, x + 3.0, z - 3.0, z + 3.0)
            if _lane_free(spot, 7.0) and _free(spot) and not _wet(*spot):
                if (f * 100) % 2 < 1:
                    sleeper_pile(b, x, z, "x", 3)
                else:
                    barrel(b, x - 1.2, z, "#4a5a6a")
                    barrel(b, x + 1.4, z + 0.6, "#4a5a6a")
                KEEP.append(spot)
