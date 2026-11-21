"""Lantern Terraces -- a tea estate on the night of the lantern festival.

A valley between two hills of tea, terraced all the way up in rows of
bushes that follow the contours.  The whole estate is out for the festival:
a thousand lanterns strung from the pagoda in the courtyard, the dragon
waiting on its poles, fireworks set up by the stage, lanterns floating
down the koi streams.  Both teams muster in the pagoda's halls; the flags
are in the tea houses on top of the hills.

Layout (red to the west; mirrored about x = 0)::

      z +196  ~~~~~~~~ the mountains, and the full moon over them ~~~~~~~~~~~~~
      z +120  TEA TERRACES   BAMBOO GROVE   ~stream~   TEA KIOSK (outpost)
      z    0  TEA HOUSE / terraces / ~stream~ bridge ~ COURTYARD: THE PAGODA
      z -120  TEA TERRACES   BAMBOO GROVE   ~stream~   SHRINE PAVILION (outpost)
      z -145  ==== the old tea cellar: a sunken lane into the hill, a stair
                   up to the top terrace behind the tea house ====

Six terraces of two up each hill, each with its row of tea along its lip
(a gap every third bush to walk through) and a stone stair straight up the
middle.  The streams run the length of the valley, a step and a fall
down, crossed by three arched bridges and a line of stepping stones.
"""
from __future__ import annotations

import math
import random

from . import kit
from .kit import (Half, carve, flight, halves, holed_wall, rect, room_walls, slab,
                  strip_light)

HALF = (320.0, 196.0)
SKY = {"top": "#08112a", "horizon": "#3a2a4a", "sun": [0.2, 0.45, 0.8],
       "clouds": 0.25, "tint": "#ffd8a8"}
AMBIENT = "#5a5a7a"
GROUND = "#3a5a2e"
FOG = 760.0

GRASS = "#3a5a2e"
TEA = "#2e6a2a"
TEA_LIGHT = "#3a7a32"
EARTH = "#5a4430"
EARTH_DARK = "#4a3826"
STONE = "#8a8a84"
STONE_DARK = "#6e6e68"
PAVING = "#9a968c"
LACQUER = "#a8281c"
LACQUER_DARK = "#7a1c14"
TILE = "#2a3a3a"
GOLD = "#e8b84a"
BAMBOO = "#5a9a3a"
PAPER = "#ffd8a0"
LANTERN = "#ff6a2a"
WATER = "#2a5a6a"

TERRACE_X = 196.0          # where the first terrace starts (magnitude)
TERRACE_STEP = 12.0
TIERS = 6
WAVE = 6.0
BAND = 10.0
TOP = 2.0 * TIERS
STREAM_X = (122.0, 140.0)
STREAM_DEPTH = 5.0
COURT = (76.0, 70.0)
PAGODA = (24.0, 20.0)
PAGODA_TOP = 12.0
CELLAR_Z = (-150.0, -140.0)
CELLAR_STAIR = (300.0, 316.0)
TEAHOUSE = (268.0, 312.0, -36.0, 36.0)
FLAG_X = 290.0
BRIDGES = (-110.0, 0.0, 110.0)


def _x0(k: int, zc: float) -> float:
    """Where terrace ``k`` starts (magnitude), on the contour at ``zc``."""
    return TERRACE_X + TERRACE_STEP * k + WAVE * math.sin(zc / 35.0 + k * 0.6)


def build(b: kit.RelayArea) -> None:
    rng = random.Random(0x1A7E)
    b.relay("the Lantern Pagoda", 40.0)
    b.intro = ["Lantern Terraces -- the tea estate on the night of the festival.",
               "Muster in the pagoda; the flags are in the tea houses on top of the hills.",
               "The old tea cellar runs through each hill from a sunken lane on the "
               "south side up to the top terrace."]
    b.extra.update({"accent": "#ff8a3a", "weather": "motes"})
    streams = [h.r(STREAM_X[0], STREAM_X[1], -HALF[1], HALF[1]) for h in halves(b)]
    kit.ground(b, GRASS, soil=EARTH_DARK, holes=streams)
    for h in halves(b):
        _terraces(b, h)
        _stream(b, h)
        _teahouse(b, h)
        _bamboo(b, h)
        _outposts(b, h)
        _paths(b, h)
    _courtyard(b)
    _pagoda(b)
    _lantern_lines(b)
    _festival(b)
    _edge(b, rng)
    _landmarks(b)


# ================================================================ terraces
def _terraces(b: kit.RelayArea, h: Half) -> None:
    """Six terraces up the hill, each along its contour, each with its row
    of tea at the lip, and the cellar cut through the bottom four."""
    zs = []
    z = -HALF[1]
    while z < HALF[1] - 1e-6:
        zs.append((z, min(HALF[1], z + BAND)))
        z += BAND
    cellar = h.r(TERRACE_X - 4.0, CELLAR_STAIR[1], CELLAR_Z[0], CELLAR_Z[1])
    stairwell = h.r(CELLAR_STAIR[0], CELLAR_STAIR[1], CELLAR_Z[0], CELLAR_Z[1])
    tiers = []
    for k in range(TIERS):
        rects = []
        for z0, z1 in zs:
            x0 = round(_x0(k, (z0 + z1) / 2.0), 2)
            rects.append(h.r(x0, HALF[0], z0, z1))
        cut = [cellar] if k < 4 else [stairwell]
        pieces = []
        for r in rects:
            pieces.extend(carve(r, cut))
        tiers.append(pieces)
    kit.tier_stack(b, tiers, 0.0, [2.0], [EARTH, EARTH_DARK], studs=True)
    # the tea: a row along each terrace's lip, a gap every third bush, and
    # none across the stone stair up the middle or the cellar lane
    for k in range(TIERS):
        y = 2.0 * (k + 1)
        for i, (z0, z1) in enumerate(zs):
            if i % 3 == 2 or abs((z0 + z1) / 2.0) < 12.0:
                continue
            if CELLAR_Z[0] - 2.0 < (z0 + z1) / 2.0 < CELLAR_Z[1] + 2.0 and k < 4:
                continue
            x0 = round(_x0(k, (z0 + z1) / 2.0), 2)
            h.box(x0 + 2.2, y + 1.2, (z0 + z1) / 2.0, 2.4, 2.4, z1 - z0 - 0.8,
                  TEA if (i + k) % 2 else TEA_LIGHT, studs=True)
    # lights along the cellar lane and in the tunnel's roof
    for x in range(int(TERRACE_X) + 8, int(CELLAR_STAIR[0]), 16):
        ceiling = 8.0 if x >= _x0(4, -145.0) + 2.0 else None
        if ceiling is not None:
            strip_light(b, h.x(float(x)), (CELLAR_Z[0] + CELLAR_Z[1]) / 2.0, ceiling, 6.0, "z",
                        "#ffb86a")
    # the cellar's stair up to the top terrace, and a rail round its head
    h.flight_x(CELLAR_STAIR[0], CELLAR_STAIR[1], CELLAR_Z[0], CELLAR_Z[1], 0.0, TOP, STONE,
               fill=0.0)
    h.box(CELLAR_STAIR[0] - 0.6, TOP + 1.5, (CELLAR_Z[0] + CELLAR_Z[1]) / 2.0, 1.2, 3.0,
          CELLAR_Z[1] - CELLAR_Z[0], LACQUER_DARK)
    for z in (CELLAR_Z[0] - 0.6, CELLAR_Z[1] + 0.6):
        h.box((CELLAR_STAIR[0] + CELLAR_STAIR[1]) / 2.0 - 1.0, TOP + 1.5, z,
              CELLAR_STAIR[1] - CELLAR_STAIR[0] - 2.0, 3.0, 1.2, LACQUER_DARK)
    # barrels of tea in the cellar lane
    for x in (214.0, 232.0):
        h.cyl(x, 2.0, CELLAR_Z[0] + 2.4, 3.6, 4.0, 3.6, "#6a4a2a")


def _paths(b: kit.RelayArea, h: Half) -> None:
    """The stone stair up the middle of the hill (paint on each terrace's
    tread), lantern posts beside it, and a stone lantern at its foot."""
    bands = [-11.0, -1.0, 9.0]          # the contour bands the stair crosses
    for k in range(TIERS):
        y = 2.0 * (k + 1)
        x0 = max(_x0(k, zc) for zc in bands)
        x1 = min(_x0(k + 1, zc) for zc in bands) if k + 1 < TIERS else TEAHOUSE[0]
        h.box((x0 + x1) / 2.0, y + 0.03, 0.0, x1 - x0, 0.06, 14.0, PAVING, collide=False)
        for z in (-9.0, 9.0):
            h.cyl(x0 + 3.0, y + 3.0, z, 0.6, 6.0, 0.6, "#3a2a1a")
            h.box(x0 + 3.0, y + 6.4, z, 1.6, 0.8, 1.6, "#3a2a1a", collide=False)
            h.sphere(x0 + 3.0, y + 7.6, z, 1.8, 2.2, 1.8, LANTERN, material="neon",
                     collide=False)
    # the stone lantern at the foot of the stair
    x = TERRACE_X - 10.0
    h.box(x, 0.8, 0.0 + 18.0, 4.0, 1.6, 4.0, STONE_DARK)
    h.box(x, 3.6, 18.0, 1.6, 4.0, 1.6, STONE)
    h.box(x, 6.3, 18.0, 3.4, 1.4, 3.4, STONE)
    h.box(x, 6.3, 18.0, 1.0, 0.8, 3.5, PAPER, material="neon", collide=False)
    h.box(x, 7.6, 18.0, 4.2, 1.2, 4.2, STONE_DARK)


# ================================================================== streams
def _stream(b: kit.RelayArea, h: Half) -> None:
    """A koi stream down the valley: three arched bridges, stepping stones,
    koi and lanterns on the water, a stair out at each end."""
    x0, x1 = STREAM_X
    area = h.r(x0, x1, -HALF[1], HALF[1])
    kit.channel(b, area, STREAM_DEPTH, "#4a4e48", studs=True)
    kit.water_sheet(b, area, -1.4, WATER, 0.68)
    xm = (x0 + x1) / 2.0
    # the arched bridges: a hump of steps up to a deck over the water
    for zc in BRIDGES:
        deck = h.r(x0 - 2.0, x1 + 2.0, zc - 6.0, zc + 6.0)
        slab(b, deck, 2.0, 0.8, LACQUER)
        for side in (-1, 1):
            h.box(x0 - 5.0 if side < 0 else x1 + 5.0, 0.6, zc, 6.0, 1.2, 12.0, STONE, studs=True)
        for z in (zc - 6.6, zc + 6.6):
            h.box(xm, 3.2, z, x1 - x0 + 4.0, 2.4, 1.2, LACQUER_DARK)
            for xx in (x0 - 1.0, x1 + 1.0):
                h.box(xx, 5.0, z, 1.4, 1.2, 1.4, GOLD, material="metal")
    # stepping stones across between the bridges
    for zc in (-55.0, 55.0):
        for k in range(3):
            h.cyl(x0 + 3.0 + k * 6.0, -0.6, zc + (k - 1) * 1.5, 4.6, 1.6, 4.6, STONE_DARK,
                  studs=True)
    # a stair out of the stream at each end, against the edge of the world
    for sz in (-1, 1):
        flight(b, "z", sz * (HALF[1] - 20.0), sz * HALF[1], *h.xs(x0, x1), -STREAM_DEPTH, 0.0,
               STONE, fill=-STREAM_DEPTH)
    # koi, lily pads and floating lanterns
    rng = random.Random(0xC01)
    for k in range(9):
        z = -170.0 + k * 40.0 + rng.uniform(-8.0, 8.0)
        x = x0 + rng.uniform(3.0, x1 - x0 - 3.0)
        if any(abs(z - zc) < 9.0 for zc in BRIDGES):
            continue
        h.sphere(x, -2.2, z, 2.0, 0.8, 0.8, "#ff7a2a" if k % 2 else "#f2f2f2", collide=False)
        h.cyl(x + 2.0, -1.38, z + 3.0, 3.0, 0.08, 3.0, "#3a7a3a", collide=False)
        h.box(x - 2.0, -1.0, z - 4.0, 1.4, 0.8, 1.4, LANTERN, material="neon", collide=False)
        h.box(x - 2.0, -1.36, z - 4.0, 1.8, 0.12, 1.8, "#3a2a1a", collide=False)


# ================================================================= teahouse
def _teahouse(b: kit.RelayArea, h: Half) -> None:
    """The tea house on top of the hill: lacquered posts, paper screens,
    a roof of three flared eaves -- and the flag before the tea table."""
    x0, x1, z0, z1 = TEAHOUSE
    y = TOP
    top = y + 14.0
    area = h.r(x0, x1, z0, z1)
    room_walls(b, area, 2.0, y, top, "#e8d8b8",
               doors={h.inward: [(-8.0, 8.0, y + 10.0)],
                      "z-": [(*h.xs(284.0, 296.0), y + 9.0)], "z+": [(*h.xs(284.0, 296.0), y + 9.0)],
                      h.outward: [(-5.0, 5.0, y + 8.0)]})
    # lacquered posts at the corners and between the screens
    for xx in (x0, (x0 + x1) / 2.0, x1):
        for zz in (z0, z1):
            h.box(xx, y + 7.5, zz, 2.6, 15.0, 2.6, LACQUER)
    # screens: lit paper panels set into the walls
    for zz, face in ((z0 - 0.06, -1), (z1 + 0.06, 1)):
        for xx in (274.0, 304.0):
            h.box(xx, y + 6.0, zz, 7.0, 5.0, 0.1, PAPER, material="neon", collide=False)
    # three flared eaves, stepped up
    slab(b, h.r(x0 - 6.0, x1 + 6.0, z0 - 6.0, z1 + 6.0), top + 1.2, 1.2, TILE, studs=True)
    slab(b, h.r(x0 + 2.0, x1 - 2.0, z0 + 4.0, z1 - 4.0), top + 4.2, 3.0, LACQUER_DARK)
    slab(b, h.r(x0 - 2.0, x1 + 2.0, z0 + 0.0, z1 + 0.0), top + 5.4, 1.2, TILE, studs=True)
    slab(b, h.r(x0 + 8.0, x1 - 8.0, z0 + 10.0, z1 - 10.0), top + 8.4, 3.0, LACQUER_DARK)
    slab(b, h.r(x0 + 4.0, x1 - 4.0, z0 + 6.0, z1 - 6.0), top + 9.6, 1.2, TILE, studs=True)
    for xx in (x0 - 6.0, x1 + 6.0):
        for zz in (z0 - 6.0, z1 + 6.0):
            h.box(xx, top + 1.0, zz, 1.0, 0.8, 1.0, GOLD, material="metal", collide=False)
    strip_light(b, h.x((x0 + x1) / 2.0), 0.0, top, 60.0, "z", PAPER)
    top_y = kit.pedestal(b, h.x(FLAG_X), 0.0, y, h.colour, h.neon, base=STONE_DARK)
    b.flag(h.team, h.x(FLAG_X), top_y, 0.0)
    kit.banner_mast(b, h.x(x1 + 4.0), 46.0, y, 26.0, h.team, h.inward)
    # the tea tables, low, with their cushions: cover in the room
    for xx, zz in ((276.0, -22.0), (276.0, 22.0), (304.0, -22.0), (304.0, 22.0)):
        h.box(xx, y + 1.2, zz, 6.0, 2.4, 6.0, "#6a3a22", studs=True)
        h.cyl(xx, y + 2.6, zz, 1.2, 0.6, 1.2, "#e8e0d0", collide=False)
    # the tea garden on top: a maple, stone lanterns, a well
    for zz in (-60.0, 60.0):
        h.cyl(282.0, y + 5.0, zz, 2.0, 10.0, 2.0, "#5a3a22")
        h.sphere(282.0, y + 12.0, zz, 12.0, 8.0, 12.0, "#c8381c", collide=False)
    h.cyl(306.0, y + 1.5, 66.0, 6.0, 3.0, 6.0, STONE_DARK)
    h.box(306.0, y + 5.0, 66.0, 0.8, 4.0, 6.6, "#3a2a1a", collide=False)


# ================================================================== bamboo
def _bamboo(b: kit.RelayArea, h: Half) -> None:
    """Groves of giant bamboo north and south between the streams and the
    hills: a forest of stems to fight through, a lantern lost in it."""
    rng = random.Random(0xBAB0)
    for sz in (-1, 1):
        placed = []
        tries = 0
        while len(placed) < 38 and tries < 600:
            tries += 1
            x = rng.uniform(148.0, 190.0)
            z = sz * rng.uniform(64.0, 186.0)
            if any(math.hypot(x - px, z - pz) < 5.0 for px, pz in placed):
                continue
            placed.append((x, z))
            hgt = rng.uniform(22.0, 34.0)
            w = rng.uniform(1.3, 2.0)
            h.cyl(x, hgt / 2.0, z, w, hgt, w, BAMBOO if len(placed) % 3 else "#6aa84a")
            for k in range(1, int(hgt // 7)):
                h.cyl(x, k * 7.0, z, w * 1.18, 0.5, w * 1.18, "#4a7a2a", collide=False)
            h.sphere(x, hgt + 1.0, z, 8.0, 3.0, 8.0, "#4a8a3a", collide=False)
    h.box(170.0, 1.0, 120.0, 2.0, 2.0, 2.0, LANTERN, material="neon")


# ================================================================ outposts
def _outposts(b: kit.RelayArea, h: Half) -> None:
    """A tea kiosk (north) and a shrine pavilion (south): where a team
    falls back to while its flag is out."""
    for sz in (-1, 1):
        zlo, zhi = sorted((sz * 80.0, sz * 118.0))
        kit.outpost_room(h, 82.0, 116.0, zlo, zhi, 0.0, "#e8d8b8", TILE, height=11.0,
                         door_w=12.0, pads=2, lights=PAPER)
        area = h.r(82.0, 116.0, zlo, zhi)
        slab(b, (area[0] - 3.0, area[1] + 3.0, zlo - 3.0, zhi + 3.0), 13.4, 1.2, TILE, studs=True)
        for xx in (82.0, 116.0):
            for zz in (zlo, zhi):
                h.box(xx, 6.0, zz, 2.4, 12.0, 2.4, LACQUER)


# =============================================================== courtyard
def _courtyard(b: kit.RelayArea) -> None:
    """The festival courtyard: a raised stone court round the pagoda, a
    moon gate north and south, stalls, the stage."""
    cx, cz = COURT
    slab(b, rect(-cx, cx, -cz, cz), 2.0, 2.0, PAVING, studs=True)
    for sx in (-1, 1):
        b.box([sx * (cx - 4.0), 2.03, 0.0], [6.0, 0.06, 2 * cz - 8.0], STONE_DARK, collide=False)
    # moon gates: a wall with a round gate through it, north and south
    for sz in (-1, 1):
        z = sz * (cz - 4.0)
        holed_wall(b, "x", z, 2.0, -30.0, 30.0, 2.0, 16.0, "#e8e0d0",
                   holes=[(-6.0, 6.0, 1.0, 13.0)])
        b.add("torus", [0.0, 9.0, z], [16.0, 16.0, 3.0], STONE, collide=False)
        b.box([0.0, 16.6, z], [64.0, 1.2, 4.0], TILE, studs=True)
    # stalls along the court: posts, a cloth roof, lanterns for sale
    for sx in (-1, 1):
        for k, z in enumerate((-46.0, 46.0)):
            x = sx * 52.0
            for dx in (-5.0, 5.0):
                for dz in (-3.0, 3.0):
                    b.cyl([x + dx, 2.0 + 3.5, z + dz], [0.6, 7.0, 0.6], "#5a3a22")
            b.box([x, 9.2, z], [12.0, 0.4, 8.0], LACQUER if k else "#2a6aa8", collide=False)
            b.box([x, 3.4, z + 2.0], [10.0, 2.8, 2.0], "#7a5a3a", studs=True)
            for dx in (-3.0, 0.0, 3.0):
                b.sphere([x + dx, 7.2, z], [1.6, 2.0, 1.6], LANTERN, material="neon",
                         collide=False)
                b.box([x + dx, 8.4, z], [0.2, 0.6, 0.2], "#3a2a1a", collide=False)


def _pagoda(b: kit.RelayArea) -> None:
    """The Lantern Pagoda: two muster halls and a shrine on the ground
    floor, a balcony round the first roof, four more tiers above."""
    px, pz = PAGODA
    y = 2.0
    top = y + PAGODA_TOP
    area = rect(-px, px, -pz, pz)
    room_walls(b, area, 2.0, y, top, "#e8d8b8",
               doors={"x-": [(-6.0, 6.0, y + 9.0)], "x+": [(-6.0, 6.0, y + 9.0)],
                      "z-": [(-5.0, 5.0, y + 9.0)], "z+": [(-5.0, 5.0, y + 9.0)]})
    for sx in (-1, 1):
        holed_wall(b, "z", sx * 8.0, 2.0, -pz + 2.0, pz - 2.0, y, top, LACQUER_DARK,
                   holes=[(-5.0, 5.0, y - 1.0, y + 8.0)])
    # the balcony: the first roof, railed, with stairs up from the court
    ring = rect(-px - 6.0, px + 6.0, -pz - 6.0, pz + 6.0)
    slab(b, ring, top + 1.2, 1.2, TILE, studs=True)
    room_walls(b, ring, 0.8, top + 1.2, top + 3.6, LACQUER,
               doors={"z+": [(-px - 6.0, -px + 2.0, top + 3.6), (px - 2.0, px + 6.0, top + 3.6)],
                      "z-": [(-px - 6.0, -px + 2.0, top + 3.6), (px - 2.0, px + 6.0, top + 3.6)]})
    for sx in (-1, 1):
        for sz in (-1, 1):
            flight(b, "z", sz * (pz + 6.0 + 22.0), sz * (pz + 6.0),
                   *sorted((sx * (px - 2.0), sx * (px + 6.0))), y, top + 1.2, STONE, fill=y)
    # the tiers above: each a little smaller, each with its flared eave
    yy = top + 1.2
    for k in range(4):
        w, d = px - 4.0 - k * 4.0, pz - 4.0 - k * 3.0
        hh = 8.0 - k * 0.8
        b.box([0.0, yy + hh / 2.0, 0.0], [2 * w, hh, 2 * d], "#e8d8b8" if k % 2 else LACQUER)
        yy += hh
        b.box([0.0, yy + 0.6, 0.0], [2 * w + 8.0, 1.2, 2 * d + 8.0], TILE, studs=True)
        for sx in (-1, 1):
            for sz in (-1, 1):
                b.box([sx * (w + 3.6), yy + 1.4, sz * (d + 3.6)], [1.0, 0.4, 1.0], GOLD,
                      material="metal", collide=False)
        yy += 1.2
    b.cyl([0.0, yy + 6.0, 0.0], [1.2, 12.0, 1.2], GOLD, material="metal", collide=False)
    for k in range(4):
        b.cyl([0.0, yy + 3.0 + k * 2.2, 0.0], [3.0 - k * 0.5, 0.6, 3.0 - k * 0.5], GOLD,
              material="metal", collide=False)
    # inside: the shrine between the halls, incense, the muster pads
    b.box([0.0, y + 2.0, pz - 4.0], [8.0, 4.0, 3.0], LACQUER_DARK, studs=True)
    b.box([0.0, y + 4.6, pz - 4.0], [2.0, 1.2, 1.0], GOLD, material="metal", collide=False)
    strip_light(b, 0.0, 0.0, top, 30.0, "z", PAPER)
    for h in halves(b):
        for i in range(3):
            for j in (-1, 1):
                b.muster(h.team, h.x(12.4 + 3.3 * i), y, j * 11.0, h.yaw_out, size=3.2)
        h.sign(px - 2.36, y + 10.6, 0.0, 9.0, 2.6, "sign_%s" % h.team, "x+")
        strip_light(b, h.x(15.0), 0.0, top, 30.0, "z", PAPER)
        h.box(px + 7.0, y + 2.0, -12.0, 5.0, 4.0, 5.0, STONE_DARK, studs=True)
        h.box(px + 7.0, y + 1.6, 12.0, 4.0, 3.2, 4.0, LACQUER_DARK, studs=True)


def _lantern_lines(b: kit.RelayArea) -> None:
    """Strings of lanterns from the pagoda's balcony corners to tall poles
    at the court's corners, red and gold, swaying (they do not)."""
    px, pz = PAGODA
    cx, cz = COURT
    corner_y = 2.0 + PAGODA_TOP + 1.2 + 2.4
    pole_h = 18.0
    for sx in (-1, 1):
        for sz in (-1, 1):
            pxp, pzp = sx * (cx - 10.0), sz * (cz - 14.0)
            b.cyl([pxp, 2.0 + pole_h / 2.0, pzp], [1.0, pole_h, 1.0], LACQUER_DARK)
            b.sphere([pxp, 2.0 + pole_h + 0.6, pzp], [1.6, 1.6, 1.6], GOLD, collide=False,
                     material="metal")
            ax, az = sx * (px + 6.0), sz * (pz + 6.0)
            # the line itself as short runs of rope, axis-aligned in steps,
            # each holding a lantern
            n = 6
            for k in range(1, n):
                f = k / float(n)
                x = ax + (pxp - ax) * f
                z = az + (pzp - az) * f
                yl = corner_y + (2.0 + pole_h - corner_y) * f - 1.6 * math.sin(f * math.pi)
                b.box([x, yl, z], [0.3, 0.3, 0.3], "#2a1a12", collide=False)
                b.sphere([x, yl - 1.4, z], [1.8, 2.4, 1.8], LANTERN if k % 2 else GOLD,
                         material="neon", collide=False)
                b.box([x, yl - 0.35, z], [0.2, 0.5, 0.2], "#2a1a12", collide=False)


def _festival(b: kit.RelayArea) -> None:
    """The dragon on its poles, the stage and its drums, the fireworks, the
    lucky cat waving at the stall, a dragon kite over the valley."""
    # the dragon: a long body of segments on poles, a head, a tail
    for k in range(9):
        x = -32.0 + k * 8.0
        z = 34.0 + math.cos(x * 0.12) * 3.0
        b.cyl([x, 2.0 + 3.0, z], [0.6, 6.0, 0.6], "#5a3a22")
        b.sphere([x, 2.0 + 7.4, z], [7.0, 4.2, 4.4], LACQUER if k % 2 else GOLD, collide=False)
    # the head at the west end, the tail at the east, each on its pole
    z_end = 34.0 + math.cos(40.0 * 0.12) * 3.0
    for sx in (-1, 1):
        b.cyl([sx * 40.0, 2.0 + 3.0, z_end], [0.6, 6.0, 0.6], "#5a3a22")
    b.box([-40.0, 2.0 + 8.0, z_end], [6.0, 5.0, 5.0], LACQUER, collide=False)
    b.box([-43.2, 2.0 + 8.6, z_end], [0.4, 1.0, 3.6], "#f2f2f2", collide=False)
    b.cone([40.0, 2.0 + 8.0, z_end], [3.0, 6.0, 3.0], GOLD, collide=False,
           r=[0.0, 0.0, -math.pi / 2.0])
    # the stage south of the pagoda, with two drums
    slab(b, rect(-18.0, 18.0, -46.0, -34.0), 4.0, 2.0, "#6a3a22", studs=True)
    for sx in (-1, 1):
        b.cyl([sx * 10.0, 4.0 + 2.2, -40.0], [5.0, 4.4, 5.0], LACQUER)
        b.cyl([sx * 10.0, 4.0 + 4.44, -40.0], [4.6, 0.08, 4.6], "#e8d8b8", collide=False)
    # firework mortars, ready
    for sx in (-1, 1):
        for k in range(3):
            b.cyl([sx * (40.0 + k * 3.0), 2.0 + 2.0, -60.0], [2.0, 4.0, 2.0], "#3a3a3a")
    # the lucky cat on the north-west stall's counter, waving
    x, z = -52.0, 48.0
    b.box([x, 4.8 + 1.8, z + 2.0], [2.2, 3.6, 2.0], "#f2f2f2", collide=False)
    b.box([x, 4.8 + 4.4, z + 2.0], [2.6, 2.0, 2.2], "#f2f2f2", collide=False)
    b.box([x + 1.4, 4.8 + 4.6, z + 2.0], [0.8, 1.8, 0.8], "#f2f2f2", collide=False)
    b.box([x, 4.8 + 3.2, z + 3.05], [0.8, 0.8, 0.1], GOLD, collide=False)
    # a dragon kite high over the valley, its string down to a pole
    b.box([0.0, 70.0, 120.0], [10.0, 6.0, 0.4], LACQUER, collide=False)
    b.box([0.0, 66.0, 120.0], [0.6, 2.0, 0.4], GOLD, collide=False)
    b.box([0.0, 63.4, 120.0], [1.4, 3.2, 0.3], LACQUER, collide=False)


# ===================================================================== edge
def _edge(b: kit.RelayArea, rng: random.Random) -> None:
    """Mountains round the valley under the full moon -- with the rabbit
    in it, the way the festival tells it."""
    hx, hz, m = HALF[0], HALF[1], b.margin
    room_walls(b, rect(-hx - m, hx + m, -hz - m, hz + m), m, 0.0, 30.0, "#3a4a32")
    kit.backdrop(b, "peaks", 20.0, rng, colours=["#1a2232", "#222a3a", "#1a1e2a"], depth=80.0)
    mz = hz + m + 160.0
    b.sphere([60.0, 150.0, mz + 1.0], [96.0, 96.0, 2.0], "#3a3a4a", collide=False)
    b.sphere([60.0, 150.0, mz], [90.0, 90.0, 2.0], "#fff0c8", material="neon", collide=False)
    for dx, dy, s in ((-8.0, -6.0, 12.0), (6.0, 4.0, 8.0), (10.0, 12.0, 4.0), (14.0, 12.0, 4.0)):
        b.sphere([60.0 + dx, 150.0 + dy, mz - 1.2], [s, s * 0.8, 1.0], "#e8d8b0", collide=False)


def _landmarks(b: kit.RelayArea) -> None:
    for x, z, name in ((0, 0, "the Lantern Pagoda"), (0, -40, "the stage"),
                       (0, 66, "the north moon gate"), (0, -66, "the south moon gate"),
                       (-12, 34, "the dragon")):
        b.landmark(float(x), float(z), name)
    for sx, team in ((-1, "red"), (1, "blue")):
        b.landmark(sx * 290.0, 0.0, "the %s tea house" % team)
        for x, z, name in ((131, 0, "the bridge"), (99, 99, "the tea kiosk"),
                           (99, -99, "the shrine pavilion"), (170, 120, "the north bamboo"),
                           (170, -120, "the south bamboo"), (250, -145, "the tea cellar")):
            b.landmark(sx * float(x), float(z), "%s (%s side)" % (name, team))
    b.camera(-110.0, 60.0, 150.0, 0.0, 12.0, 0.0)
    b.camera(150.0, 50.0, -150.0, 0.0, 12.0, 0.0)
    b.camera(-260.0, 50.0, 100.0, -150.0, 6.0, 0.0)
