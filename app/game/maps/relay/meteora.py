"""Meteora -- monasteries on top of the rock pillars, a misty morning.

The valley is full of rock: pillars of conglomerate standing up out of the
meadows like the stumps of giants, and on the two tallest, at either end,
a monastery each, where the flags are kept in the churches.  You reach a
monastery up the switchback cut into its pillar's face -- or the hermits'
way: up a hermit's little pillar beside it, across a rope bridge into the
rock, through the tunnel inside and up the chimney into the courtyard.
Both teams muster in St. Ezra's, the chapel down in the valley.

Layout (red to the west; mirrored about x = 0)::

      z +196  ~~~~~~~~~~~ more pillars in the mist, beyond reach ~~~~~~~~~~~~~
      z +125  OLIVE PRESS (outpost)   olive grove   stone walls   beehives
      z  +74  MONASTERY PILLAR <- rope bridge - HERMIT PILLAR    rock stack
      z    0  MONASTERY (on top) | switchback ... meadow ... ST. EZRA'S + bell tower
      z  -74  MONASTERY PILLAR <- rope bridge - HERMIT PILLAR    rock stack
      z -121  ~~~~~~~~~~~~ the river, stepping stones, the mill ~~~~~~~~~~~~~~~
      z -160  SHEPHERD'S FOLD (outpost)   haystacks   the village

The pillars are four cliffs of eight; the switchback is two flights of
sixteen with a landing; each chimney is a tunnel eight high at the
pillar's middle and a stair up a shaft to the top.
"""
from __future__ import annotations

import math
import random

from . import kit
from .kit import (Half, carve, flight, halves, holed_wall, rect, room_walls, slab,
                  strip_light)

HALF = (320.0, 196.0)
SKY = {"top": "#7aa8d8", "horizon": "#f2e2c8", "sun": [0.55, 0.18, -0.6],
       "clouds": 0.5, "tint": "#fff0d8"}
AMBIENT = "#a8a8a0"
GROUND = "#6a8a4a"
FOG = 560.0

MEADOW = "#6a8a4a"
MEADOW_DARK = "#5a7a3e"
ROCK = "#a89880"
ROCK_DARK = "#8a7a64"
ROCK_LIGHT = "#bcae96"
WHITEWASH = "#ece6da"
TILE = "#b8582e"
TILE_DARK = "#984624"
WOOD = "#6a4a2a"
OLIVE = "#6a7a4a"
WATER = "#4a7a8a"

PILLAR_X = 244.0           # the monastery pillar's inward face (magnitude)
PILLAR_Z = 104.0
CLIFF = 8.0
TOP = 32.0
SWITCH_X = (232.0, 244.0)
HERMIT = (214.0, 238.0, 62.0, 86.0)
CHIMNEY_Z = (70.0, 78.0)
CHIMNEY_STAIR = (268.0, 284.0)
CHURCH = (266.0, 304.0, -18.0, 18.0)
FLAG_X = 290.0
RIVER_Z = (-130.0, -112.0)
RIVER_X = 216.0
CHAPEL = (40.0, 30.0)


def build(b: kit.RelayArea) -> None:
    rng = random.Random(0x3E7E)
    b.relay("St. Ezra's", 46.0)
    b.intro = ["Meteora -- monasteries on top of the rock, and mist in the valley.",
               "Muster in St. Ezra's chapel; the flags are in the monastery churches up "
               "on the two tallest pillars.",
               "Climb the switchback -- or the hermits' way: up the little pillar, over "
               "the rope bridge, and up the chimney inside the rock."]
    b.extra.update({"accent": "#f2d8a8", "weather": "mist"})
    river = rect(-RIVER_X, RIVER_X, RIVER_Z[0], RIVER_Z[1])
    kit.ground(b, MEADOW, soil="#5a4a32", holes=[river])
    _river(b, river)
    _chapel(b)
    for h in halves(b):
        _pillar(b, h)
        _switchback(b, h)
        _hermits(b, h)
        _monastery(b, h)
        _stacks(b, h)
        _valley(b, h)
        _outposts(b, h)
    _meadow(b)
    _edge(b, rng)
    _landmarks(b)


# =================================================================== pillar
def _pillar_rects(h: Half, k: int):
    """The monastery pillar's footprint at cliff ``k``: a flat face towards
    the valley (the switchback is cut into it), rounded at the back."""
    inset = 3.0 * k
    zmax = PILLAR_Z - inset
    out = []
    band = 8.0
    z = -zmax
    while z < zmax - 1e-6:
        z1 = min(zmax, z + band)
        zc = abs((z + z1) / 2.0)
        back = HALF[0] if zc < zmax - 24.0 else HALF[0] - (zc - (zmax - 24.0)) * 1.2
        out.append(h.r(PILLAR_X, back, z, z1))
        z = z1
    return out


def _pillar(b: kit.RelayArea, h: Half) -> None:
    """The monastery's pillar: four cliffs of eight, the chimney tunnel
    through the third and its shaft through the third and fourth."""
    tunnels = [h.r(PILLAR_X, CHIMNEY_STAIR[0], sz * CHIMNEY_Z[0], sz * CHIMNEY_Z[1])
               for sz in (-1, 1)]
    shafts = [h.r(CHIMNEY_STAIR[0], CHIMNEY_STAIR[1], sz * CHIMNEY_Z[0], sz * CHIMNEY_Z[1])
              for sz in (-1, 1)]
    tiers = []
    for k in range(4):
        cut = tunnels + shafts if k == 2 else (shafts if k == 3 else [])
        pieces = []
        for r in _pillar_rects(h, k):
            pieces.extend(carve(r, cut))
        tiers.append(pieces)
    kit.tier_stack(b, tiers, 0.0, [CLIFF], [ROCK_DARK, ROCK, ROCK_DARK, ROCK_LIGHT],
                   studs=True)
    # strata: a band of darker rock along the face at each cliff's foot
    for k in range(1, 4):
        h.box(PILLAR_X - 0.1, k * CLIFF + 0.6, 0.0 + 0.0, 0.2, 1.2, 60.0, "#7a6a54",
              collide=False)
    for sz in (-1, 1):
        z0, z1 = sorted((sz * CHIMNEY_Z[0], sz * CHIMNEY_Z[1]))
        # the chimney stair, up the shaft to the courtyard
        h.flight_x(CHIMNEY_STAIR[0], CHIMNEY_STAIR[1], z0, z1, 2.0 * CLIFF, TOP, ROCK_LIGHT,
                   fill=2.0 * CLIFF)
        # candles in niches along the tunnel
        for x in (250.0, 260.0):
            h.box(x, 2.0 * CLIFF + 3.2, z0 + 0.4 if sz > 0 else z1 - 0.4, 1.2, 1.2, 0.8,
                  "#ffcf7a", material="neon", collide=False)
        strip_light(b, h.x((PILLAR_X + CHIMNEY_STAIR[0]) / 2.0), (z0 + z1) / 2.0, 3.0 * CLIFF,
                    16.0, "x", "#ffcf7a")
        # a rail round the shaft's head in the courtyard
        h.box(CHIMNEY_STAIR[0] - 0.6, TOP + 1.5, (z0 + z1) / 2.0, 1.2, 3.0, z1 - z0, ROCK_DARK)
        for z in (z0 - 0.6, z1 + 0.6):
            h.box((CHIMNEY_STAIR[0] + CHIMNEY_STAIR[1]) / 2.0 - 1.0, TOP + 1.5, z,
                  CHIMNEY_STAIR[1] - CHIMNEY_STAIR[0] - 2.0, 3.0, 1.2, ROCK_DARK)
    # a goat on a ledge of the north cliff, looking down
    gx, gz = 258.0, 100.0 - 6.0
    h.box(gx, 2 * CLIFF + 0.0 + 1.6, gz, 3.0, 1.4, 1.6, "#f2f0e8", collide=False)
    h.box(gx + 1.8, 2 * CLIFF + 2.4, gz, 1.0, 1.2, 1.0, "#f2f0e8", collide=False)
    h.cone(gx + 2.2, 2 * CLIFF + 3.4, gz, 0.4, 1.0, 0.4, "#5a4a3a", collide=False)


def _switchback(b: kit.RelayArea, h: Half) -> None:
    """The switchback cut up the face: up to a landing, back the other way
    to the top, a wall of rock along its open side."""
    x0, x1 = SWITCH_X
    mid = (x0 + x1) / 2.0
    # first flight: south to north, up to the landing
    h.flight_z(-56.0, -6.0, mid, x1, 0.0, 2.0 * CLIFF, ROCK_LIGHT, fill=0.0)
    h.slab(x0, x1, -6.0, 2.0, 2.0 * CLIFF, 2.0 * CLIFF, ROCK)
    # second flight: back south, beside the first, up to the top
    h.flight_z(-6.0, -56.0, x0, mid, 2.0 * CLIFF, TOP, ROCK_LIGHT, fill=2.0 * CLIFF)
    h.slab(x0, x1, -64.0, -56.0, TOP, 4.0, ROCK, studs=True)
    # the rock wall along the top landing's outer edge
    h.box(x0 - 0.6, TOP + 1.4, -60.0, 1.2, 2.8, 8.0, ROCK_DARK)
    # a shrine with a candle on the landing
    h.box(x0 + 2.0, 2.0 * CLIFF + 2.0, 0.0, 2.4, 4.0, 2.4, WHITEWASH)
    h.box(x0 + 2.0, 2.0 * CLIFF + 4.6, 0.0, 3.0, 1.2, 3.0, TILE)
    h.box(x0 + 3.26, 2.0 * CLIFF + 2.4, 0.0, 0.1, 1.0, 0.8, "#ffcf7a", material="neon",
          collide=False)


def _hermits(b: kit.RelayArea, h: Half) -> None:
    """A hermit's pillar beside the monastery's, north and south: a stair
    up its side, a hut on top, a rope bridge across into the rock."""
    x0, x1, z0, z1 = HERMIT
    for sz in (-1, 1):
        za, zb = sorted((sz * z0, sz * z1))
        kit.tier_stack(b, [[h.r(x0, x1, za, zb)], [h.r(x0, x1 - 1.0, za + 1.0, zb - 1.0)]], 0.0,
                       [CLIFF], [ROCK_DARK, ROCK], studs=True)
        # the stair up its west side, rising towards the monastery's end
        near, far = (sz * (z1 + 26.0), sz * (z1 - 2.0))
        h.flight_z(near, far, x0 - 6.0, x0, 0.0, 2.0 * CLIFF, ROCK_LIGHT, fill=0.0)
        # the hut: four walls and a tile roof, a door to the bridge side
        hut = h.r(x0 + 5.0, x0 + 15.0, za + 6.0, zb - 6.0)
        room_walls(b, hut, 1.0, 2.0 * CLIFF, 2.0 * CLIFF + 7.0, WHITEWASH,
                   doors={h.outward: [((za + zb) / 2.0 - 2.5, (za + zb) / 2.0 + 2.5, 2.0 * CLIFF + 5.5)]})
        slab(b, hut, 2.0 * CLIFF + 8.0, 1.0, TILE, studs=True)
        # the rope bridge into the rock: planks, rope rails on posts
        cz0, cz1 = sorted((sz * CHIMNEY_Z[0], sz * CHIMNEY_Z[1]))
        h.slab(x1 - 1.0, PILLAR_X, cz0, cz1, 2.0 * CLIFF, 0.6, WOOD)
        for z in (cz0, cz1):
            for x in (x1 + 0.4, PILLAR_X - 0.4):
                h.box(x, 2.0 * CLIFF + 1.6, z, 0.6, 3.2, 0.6, "#4a3a22")
            h.box((x1 + PILLAR_X) / 2.0, 2.0 * CLIFF + 2.9, z, PILLAR_X - x1 - 1.4, 0.2, 0.2,
                  "#c8b888", collide=False)
        # the tunnel's mouth, framed in timber
        h.box(PILLAR_X - 0.5, 2.0 * CLIFF + 7.4, (cz0 + cz1) / 2.0, 1.2, 1.2, cz1 - cz0 + 2.4,
              "#4a3a22", collide=False)


# ================================================================ monastery
def _monastery(b: kit.RelayArea, h: Half) -> None:
    """The monastery on top: a wall round the pillar's edge, the church
    with its dome (the flag inside, under the icons), the cells, the
    winch house with its basket hanging over the drop."""
    y = TOP
    x0, x1, z0, z1 = CHURCH
    top = y + 14.0
    area = h.r(x0, x1, z0, z1)
    room_walls(b, area, 2.0, y, top, WHITEWASH,
               doors={h.inward: [(-6.0, 6.0, y + 10.0)],
                      "z-": [(*h.xs(282.0, 292.0), y + 9.0)], "z+": [(*h.xs(282.0, 292.0), y + 9.0)]})
    slab(b, area, top + 1.2, 1.2, TILE, studs=True)
    # the drum and the dome over the crossing
    h.box((x0 + x1) / 2.0, top + 1.2 + 3.0, 0.0, 14.0, 6.0, 14.0, WHITEWASH, collide=False)
    h.sphere((x0 + x1) / 2.0, top + 1.2 + 7.0, 0.0, 14.0, 10.0, 14.0, TILE_DARK, collide=False)
    h.box((x0 + x1) / 2.0, top + 1.2 + 13.0, 0.0, 0.4, 3.0, 0.4, "#e8c84a", collide=False)
    h.box((x0 + x1) / 2.0, top + 1.2 + 13.6, 0.0, 1.6, 0.4, 0.4, "#e8c84a", collide=False)
    # the icon screen at the east end, gold, and its candles
    h.box(x1 - 2.6, y + 5.0, 0.0, 0.6, 8.0, 20.0, "#c89a3a", material="metal")
    for z in (-6.0, 0.0, 6.0):
        h.box(x1 - 2.96, y + 6.0, z, 0.1, 3.6, 2.6, ["#2a4a8a", "#8a2a2a", "#2a6a4a"][int(z / 6) + 1],
              collide=False)
    strip_light(b, h.x((x0 + x1) / 2.0), 0.0, top, 30.0, "z", "#ffcf7a")
    top_y = kit.pedestal(b, h.x(FLAG_X), 0.0, y, h.colour, h.neon, base=ROCK_DARK)
    b.flag(h.team, h.x(FLAG_X), top_y, 0.0)
    kit.banner_mast(b, h.x(x0 - 4.0), 24.0, y, 24.0, h.team, h.inward)
    # the wall round the top, chest high, open where the routes arrive
    edge = h.r(PILLAR_X + 1.0, HALF[0], -PILLAR_Z + 3.0 * 3 + 1.0, PILLAR_Z - 3.0 * 3 - 1.0)
    room_walls(b, edge, 1.2, y, y + 3.2, ROCK_LIGHT, sides=(h.inward,),
               doors={h.inward: [(-64.0, -54.0, y + 3.2), (-8.0, 8.0, y + 3.2)]})
    # cells along the north and south, roofed, doors on the courtyard
    for sz in (-1, 1):
        za, zb = sorted((sz * 40.0, sz * 58.0))
        cells = h.r(258.0, 306.0, za, zb)
        room_walls(b, cells, 1.4, y, y + 9.0, WHITEWASH,
                   doors={"z-" if sz > 0 else "z+": [(*h.xs(266.0, 272.0), y + 7.0),
                                                     (*h.xs(290.0, 296.0), y + 7.0)]})
        slab(b, cells, y + 10.2, 1.2, TILE, studs=True)
    # the winch house on the north-west corner, its basket over the drop
    h.box(252.0, y + 4.0, 92.0, 8.0, 8.0, 8.0, WHITEWASH)
    h.box(252.0, y + 8.6, 92.0, 9.0, 1.2, 9.0, TILE)
    h.box(PILLAR_X - 3.0, y + 9.8, 92.0, 9.0, 1.0, 1.0, WOOD, collide=False)
    h.box(PILLAR_X - 6.6, y - 2.0, 92.0, 0.2, 22.6, 0.2, "#c8b888", collide=False)
    h.box(PILLAR_X - 6.6, y - 14.6, 92.0, 3.6, 2.6, 3.6, "#a07a4a", collide=False)
    # cypresses and a bell on its frame
    for z in (-34.0, 34.0):
        h.cyl(312.0, y + 2.0, z, 1.4, 4.0, 1.4, WOOD)
        h.cone(312.0, y + 11.0, z, 5.0, 16.0, 5.0, "#2a4a2a", collide=False)
    h.box(262.0, y + 4.0, -30.0, 1.0, 8.0, 1.0, WOOD)
    h.box(262.0, y + 4.0, -24.0, 1.0, 8.0, 1.0, WOOD)
    h.box(262.0, y + 8.5, -27.0, 1.0, 1.0, 7.0, WOOD)
    h.cone(262.0, y + 6.7, -27.0, 2.4, 2.6, 2.4, "#b8882a", collide=False)


# ==================================================================== stacks
def _stacks(b: kit.RelayArea, h: Half) -> None:
    """Rock stacks in the valley: high ground with a stair round each, a
    lone tree on one, prayer flags on the other."""
    for (cx, cz, r), extra in (((132.0, 48.0, 14.0), "tree"), ((150.0, -52.0, 12.0), "flags")):
        tiers = []
        for k in range(3):
            f = 1.0 - k * 0.12
            tiers.append(kit.ellipse_rects(h.x(cx), cz, r * f, r * 1.2 * f, band=4.0))
        kit.tier_stack(b, tiers, 0.0, [4.0], [ROCK_DARK, ROCK, ROCK_LIGHT], studs=True)
        # a stair up its inward side onto the first cliff (the rest is a jump)
        edge = cx - math.floor(r * math.sqrt(1.0 - (2.0 / (r * 1.2)) ** 2))
        h.flight_x(edge - 12.0, edge, cz - 3.0, cz + 3.0, 0.0, 4.0, ROCK_LIGHT, fill=0.0)
        if extra == "tree":
            h.cyl(cx, 12.0 + 4.0, cz, 1.6, 8.0, 1.6, WOOD)
            h.sphere(cx, 12.0 + 10.0, cz, 10.0, 8.0, 10.0, OLIVE, collide=False)
        else:
            h.cyl(cx, 12.0 + 6.0, cz, 0.6, 12.0, 0.6, WOOD)
            for k in range(6):
                h.box(cx + 1.0 + k * 1.4, 12.0 + 11.0 - k * 0.6, cz, 1.4, 1.0, 0.1,
                      ["#c42b20", "#f2c21e", "#3a9a3a", "#2a6aa8", "#f2f2f2", "#c42b20"][k],
                      collide=False)


# ==================================================================== valley
def _valley(b: kit.RelayArea, h: Half) -> None:
    """The meadows on this half: field walls, an olive grove, beehives,
    the village and the mill by the river."""
    # dry-stone field walls, waist high, with gaps
    for x0, x1, z in ((60.0, 110.0, 96.0), (120.0, 176.0, 96.0), (60.0, 100.0, -96.0),
                      (112.0, 170.0, -92.0)):
        h.box((x0 + x1) / 2.0, 1.6, z, x1 - x0, 3.2, 2.4, ROCK_DARK, studs=True)
    # olive grove north
    for x, z in ((70.0, 130.0), (92.0, 150.0), (114.0, 126.0), (88.0, 176.0), (130.0, 164.0)):
        h.cyl(x, 3.0, z, 1.8, 6.0, 1.8, "#5a4a3a")
        h.sphere(x, 8.0, z, 9.0, 6.0, 9.0, OLIVE, collide=False)
        h.sphere(x + 2.0, 7.0, z - 1.6, 6.0, 4.0, 6.0, "#7a8a5a", collide=False)
    # beehives in a row by the grove
    for k in range(4):
        h.box(150.0 + k * 5.0, 1.6, 176.0, 3.0, 3.2, 3.0, "#e8d8b0", studs=True)
        h.box(150.0 + k * 5.0, 3.5, 176.0, 3.6, 0.6, 3.6, "#c8b890")
    # the village across the river: two houses and a little church
    for (x0, x1, z0, z1, door) in ((60.0, 84.0, -176.0, -152.0, "z+"),
                                   (100.0, 128.0, -184.0, -158.0, "z+")):
        area = h.r(x0, x1, z0, z1)
        kit.building(b, area, 0.0, 10.0, WHITEWASH, roof=True, roof_colour=TILE,
                     doors={door: [(*h.xs((x0 + x1) / 2.0 - 3.0, (x0 + x1) / 2.0 + 3.0), 7.0)]},
                     windows={h.face("x-"): [(z0 + 6.0, z0 + 10.0, 3.0, 6.0)]}, lights="")
        kit.gable(b, area, 11.2, TILE, along="x" if x1 - x0 > z1 - z0 else "z", tiers=3, rise=1.4)
    # haystacks by the fold
    for x, z in ((214.0, -150.0), (226.0, -166.0)):
        h.cyl(x, 3.0, z, 7.0, 6.0, 7.0, "#d8b860")
        h.cone(x, 7.6, z, 7.4, 3.2, 7.4, "#c8a850", collide=False)
    # the mill on the river, its wheel turning (it does not)
    area = h.r(170.0, 194.0, -110.0, -90.0)
    room_walls(b, area, 1.4, 0.0, 10.0, WHITEWASH, doors={"z+": [(*h.xs(178.0, 186.0), 7.0)]})
    slab(b, area, 11.2, 1.2, TILE, studs=True)
    h.cyl(182.0, 4.0, -111.4, 12.0, 1.6, 12.0, WOOD, collide=False, r=[math.pi / 2.0, 0.0, 0.0])


# ==================================================================== river
def _river(b: kit.RelayArea, river) -> None:
    """The river across the south of the valley: a stony bed, stepping
    stones, a footbridge, a stair out at each end."""
    kit.channel(b, river, 5.0, "#6a6a5a", studs=True)
    kit.water_sheet(b, river, -1.6, WATER, 0.64)
    x0, x1, z0, z1 = river
    for sx in (-1, 1):
        flight(b, "x", sx * (x1 - 20.0), sx * x1, z0, z1, -5.0, 0.0, ROCK_LIGHT, fill=-5.0)
        for k in range(3):
            b.cyl([sx * 60.0, -0.8, z0 + 3.0 + k * 6.0], [5.0, 1.6, 5.0], ROCK, studs=True)
    # the footbridge in the middle, timber on stone piers
    slab(b, rect(-6.0, 6.0, z0 - 3.0, z1 + 3.0), 1.4, 1.4, WOOD)
    for x in (-5.6, 5.6):
        b.box([x, 2.6, (z0 + z1) / 2.0], [0.8, 2.4, z1 - z0 + 6.0], "#4a3a22")


# =================================================================== chapel
def _chapel(b: kit.RelayArea) -> None:
    """St. Ezra's in the valley: a cross-in-square chapel, a muster hall
    each side of the nave, the bell tower north of it."""
    cx, cz = CHAPEL
    area = rect(-cx, cx, -cz, cz)
    top = 14.0
    room_walls(b, area, 3.0, 0.0, top, WHITEWASH,
               doors={"x-": [(-7.0, 7.0, 10.0)], "x+": [(-7.0, 7.0, 10.0)],
                      "z-": [(-6.0, 6.0, 9.0)], "z+": [(-6.0, 6.0, 9.0)]})
    for sx in (-1, 1):
        holed_wall(b, "z", sx * 14.0, 2.0, -cz + 3.0, cz - 3.0, 0.0, top, "#d8d0c0",
                   holes=[(-6.0, 6.0, -1.0, 9.0)])
    slab(b, area, top + 1.4, 1.4, TILE, studs=True)
    b.box([0.0, top + 1.4 + 3.0, 0.0], [16.0, 6.0, 16.0], WHITEWASH)
    b.sphere([0.0, top + 1.4 + 6.0 + 2.0, 0.0], [16.0, 10.0, 16.0], TILE_DARK, collide=False)
    b.box([0.0, top + 1.4 + 6.0 + 7.6, 0.0], [0.4, 3.0, 0.4], "#e8c84a", collide=False)
    # the icon screen and the chandelier
    b.box([0.0, 6.0, cz - 4.5], [20.0, 10.0, 2.0], "#c89a3a", material="metal")
    b.cyl([0.0, top - 3.0, 0.0], [8.0, 0.6, 8.0], "#c89a3a", material="metal", collide=False)
    for k in range(8):
        a = k * math.pi / 4.0
        b.box([math.cos(a) * 3.4, top - 2.4, math.sin(a) * 3.4], [0.5, 0.8, 0.5], "#ffcf7a",
              material="neon", collide=False)
    b.box([0.0, top - 1.5, 0.0], [0.2, 3.0, 0.2], "#3a2a1a", collide=False)
    # the bell tower north of the chapel, its bell up in the arch
    tz = cz + 14.0
    b.box([0.0, 13.0, tz], [10.0, 26.0, 10.0], WHITEWASH)
    b.box([0.0, 26.6, tz], [11.0, 1.2, 11.0], TILE)
    b.box([0.0, 30.0, tz], [6.0, 5.6, 6.0], WHITEWASH, collide=False)
    b.cone([0.0, 28.6, tz], [3.6, 3.6, 3.6], "#b8882a", collide=False)
    b.box([0.0, 33.4, tz], [7.0, 1.2, 7.0], TILE, collide=False)
    for h in halves(b):
        for i in range(3):
            for j in (-1, 1):
                b.muster(h.team, h.x(19.0 + 5.5 * i), 0.0, j * 13.0, h.yaw_out, size=5.0)
        h.sign(cx - 3.36, 11.0, 0.0, 10.0, 3.0, "sign_%s" % h.team, "x+")
        strip_light(b, h.x(27.0), 0.0, top, 40.0, "z", "#ffcf7a")
        h.box(cx + 7.0, 2.0, -14.0, 6.0, 4.0, 6.0, ROCK_DARK, studs=True)
        h.box(cx + 7.0, 1.6, 14.0, 5.0, 3.2, 5.0, "#a07a4a", studs=True)
        # cypress pair at the door
        for z in (-20.0, 20.0):
            h.cyl(cx + 4.0, 1.5, z, 1.2, 3.0, 1.2, WOOD)
            h.cone(cx + 4.0, 9.0, z, 4.0, 14.0, 4.0, "#2a4a2a", collide=False)


# ================================================================== outposts
def _outposts(b: kit.RelayArea, h: Half) -> None:
    """The olive press (north) and the shepherd's fold (south): where a team
    falls back to while its flag is out."""
    kit.outpost_room(h, 150.0, 192.0, 112.0, 148.0, 0.0, WHITEWASH, TILE, height=11.0,
                     door_w=12.0, pads=2, lights="#ffcf7a")
    h.cyl(156.0 + 0.0, 2.0, 140.0, 5.0, 4.0, 5.0, ROCK)
    kit.outpost_room(h, 150.0, 192.0, -172.0, -140.0, 0.0, "#c8b890", "#8a6a4a",
                     height=10.0, door_w=10.0, pads=2, lights="#ffcf7a")


# ==================================================================== meadow
def _meadow(b: kit.RelayArea) -> None:
    """The valley floor round St. Ezra's: low swells of meadow a step high,
    a path of flagstones from the chapel each way, sheep."""
    for sx in (-1, 1):
        for cx, cz, rx, rz in ((80.0, 50.0, 22.0, 16.0), (96.0, -50.0, 20.0, 14.0),
                               (190.0, 20.0, 18.0, 26.0)):
            kit.mound(b, sx * cx, cz, rx, rz, 2, 2.0, [MEADOW_DARK, MEADOW], band=4.0)
        for k in range(8):
            x = 52.0 + k * 22.0
            b.box([sx * x, 0.04, 2.0 * math.sin(k)], [8.0, 0.08, 6.0], ROCK_LIGHT, collide=False)
    for x, z in ((-40.0, 120.0), (-30.0, 128.0), (36.0, 112.0), (24.0, -70.0)):
        b.sphere([x, 1.6, z], [4.0, 2.6, 2.8], "#f2f0e8", collide=False)
        b.sphere([x + 2.2, 2.2, z], [1.4, 1.4, 1.2], "#2a2a2a", collide=False)


# ====================================================================== edge
def _edge(b: kit.RelayArea, rng: random.Random) -> None:
    """More pillars standing in the mist beyond the valley."""
    hx, hz, m = HALF[0], HALF[1], b.margin
    room_walls(b, rect(-hx - m, hx + m, -hz - m, hz + m), m, 0.0, 40.0, ROCK_DARK)
    for i in range(16):
        x = -hx + 20.0 + i * (2 * hx - 40.0) / 15.0
        for sz in (-1, 1):
            hgt = 30.0 + (i * 17 % 7) * 12.0
            w = 26.0 + (i % 3) * 5.0
            b.box([x, 40.0 + hgt / 2.0, sz * (hz + m / 2.0)], [w, hgt, m + 0.4 + (i % 3) * 0.2],
                  [ROCK, ROCK_DARK, ROCK_LIGHT][i % 3], collide=False)
            b.box([x, 40.0 + hgt + 1.0, sz * (hz + m / 2.0)], [w * 0.7, 2.0, m * 0.7],
                  "#5a7a4a", collide=False)
    kit.backdrop(b, "hills", 30.0, rng, colours=["#8a9a7a", "#7a8a6a"], sides=("x-", "x+"),
                 depth=60.0)


def _landmarks(b: kit.RelayArea) -> None:
    for x, z, name in ((0, 0, "St. Ezra's"), (0, 44, "the bell tower"), (0, -121, "the footbridge")):
        b.landmark(float(x), float(z), name)
    for sx, team in ((-1, "red"), (1, "blue")):
        b.landmark(sx * 285.0, 0.0, "the %s monastery" % team)
        for x, z, name in ((238, -30, "the switchback"), (226, 74, "the north hermit"),
                           (226, -74, "the south hermit"), (132, 48, "the tree stack"),
                           (150, -52, "the flag stack"), (171, 130, "the olive press"),
                           (171, -144, "the shepherd's fold"), (182, -100, "the mill")):
            b.landmark(sx * float(x), float(z), "%s (%s side)" % (name, team))
    b.camera(-140.0, 70.0, 150.0, 0.0, 12.0, 0.0)
    b.camera(150.0, 70.0, -150.0, 0.0, 12.0, 0.0)
    b.camera(-180.0, 60.0, 40.0, -280.0, 30.0, 0.0)
