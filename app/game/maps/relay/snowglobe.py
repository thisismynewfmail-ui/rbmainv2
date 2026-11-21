"""Snowglobe Hollow -- a village inside a snow globe on a mantelpiece.

It never stops snowing in Snowglobe Hollow, and every so often somebody
picks the globe up and shakes it.  The village is an alpine town round its
square -- the town hall under its clock tower, a carousel, a toy train that
goes round and round, a church, a skating pond -- and on the hills at the
two ends of the globe stand the chalets where the flags are kept.  Both
teams muster in the town hall.  The world is round, because a globe is:
its wooden base curves all the way about, and overhead the glass curves
away into a living room the size of the sky -- the fire, the mantel clock,
and an eye, now and then, looking in.

Layout (red to the west; mirrored about x = 0)::

            ,------------------ the globe's base, round -----------------.
      z +125  BAKERY (outpost)   .... THE CHURCH ....   BAKERY (outpost)
      z  +42  TOY SHOP  THE SNOWY OWL       fountain        (and theirs)
      z    0  CHALET HILL == main street == TOWN HALL + clock == ... HILL
      z  -42  CHEESE SHOP  POST OFFICE  ICE CAVE   carousel
      z -125  SKI HUT (outpost)  ski jump  .. THE SKATING POND ..
            `------------------------------------------------------------'

The toy train runs round the square; under each chalet hill an ice tunnel
runs from a stair by the flag down and along to an ice cave on the edge of
the village -- the flag's back door.
"""
from __future__ import annotations

import math
import random

from . import kit
from .kit import (Half, carve, halves, holed_wall, rect, room_walls, slab, strip_light)

HALF = (300.0, 190.0)
SKY = {"top": "#3a3048", "horizon": "#c89a7a", "sun": [0.3, 0.6, 0.5],
       "clouds": 0.2, "tint": "#ffe8d0"}
AMBIENT = "#b0a8c0"
GROUND = "#eef2f6"
FOG = 760.0

SNOW = "#f2f5f8"
SNOW_SHADE = "#dde4ec"
ICE = "#c2e2f2"
ICE_DEEP = "#8ec0d8"
TIMBER = "#7a4e2e"
TIMBER_DARK = "#4e3220"
PLASTER = "#f2ead8"
SLATE = "#4a5060"
COBBLE = "#a29ea8"
PINE = "#2a5a3a"
GOLD = "#e8c050"
WARM = "#ffcf7a"
BASE = "#6a2e22"            # the globe's wooden base

WALL_H = 44.0               # the base, high enough that nothing in the globe looks over it
HALL = (36.0, 26.0)
HALL_TOP = 14.0
LOOP = (70.0, 62.0)          # the toy train's loop round the square
HILL_TOP = 10.0
CHALET = (240.0, 292.0, -36.0, 36.0)
CHALET_H = 14.0
FLAG_X = 266.0
TUNNEL_Z = (-30.0, -20.0)
TUNNEL_X = (150.0, 286.0)
TUNNEL_FLOOR = -8.0
CAVE_STAIR = (150.0, 164.0)
CELLAR_STAIR = (268.0, 286.0)
POND = (-58.0, 58.0, -168.0, -112.0)


def edge(x: float) -> float:
    """How far the round base lets you go north or south at ``x``: a
    squircle, round but roomy at the ends where the chalets are."""
    hx, hz = HALF
    f = min(1.0, abs(x) / hx)
    return hz * (1.0 - f ** 4) ** 0.25


def build(b: kit.RelayArea) -> None:
    rng = random.Random(0x5E0B)
    b.relay("the Town Hall", 44.0)
    b.intro = ["Snowglobe Hollow -- a village in a snow globe, and somebody keeps shaking it.",
               "Muster in the town hall; the flags are in the chalets up on the hills at the "
               "two ends of the globe.",
               "Each chalet has a stair beside the flag down to an ice tunnel -- it comes up at "
               "an ice cave on the edge of the village."]
    b.extra.update({"accent": "#bfe8ff", "weather": "snow"})
    tunnels = [h.r(TUNNEL_X[0], TUNNEL_X[1], TUNNEL_Z[0], TUNNEL_Z[1]) for h in halves(b)]
    kit.ground(b, SNOW, soil="#8a8a90", holes=tunnels, material="")
    _base(b)
    for h in halves(b):
        _tunnel(b, h)
        _hill(b, h)
        _chalet(b, h)
        _street(b, h, random.Random(0x51ED))
        _outposts(b, h)
        _ski_jump(b, h)
        _forts(b, h)
        _pines(b, h)
    _hall(b)
    _square(b)
    _loop(b)
    _church(b)
    _pond(b)
    _room(b)
    _landmarks(b)
    del rng


# ================================================================ the base
def _base(b: kit.RelayArea) -> None:
    """The globe's wooden base, round all the way about (in axis-aligned
    steps, so all of it is solid), a gold band along its top, and the glass
    curving up and over (a rig, so it can catch the light)."""
    hx, hz, m = HALF[0], HALF[1], b.margin
    step = 6.0
    bands = []
    x = 0.0
    while x < hx + m:
        xb = min(x + step, hx + m)
        ze = round(edge(xb), 1) if xb < hx else 0.0
        bands.append((x, xb, ze))
        x = xb
    # merge runs of the same depth
    merged = []
    for band in bands:
        if merged and abs(merged[-1][2] - band[2]) < 0.05:
            merged[-1] = (merged[-1][0], band[1], band[2])
        else:
            merged.append(band)
    for sx in (-1, 1):
        for xa, xb, ze in merged:
            lo, hi = sorted((sx * xa, sx * xb))
            for sz in (-1, 1):
                z0, z1 = sorted((sz * ze, sz * (hz + m)))
                if z1 - z0 < 0.05:
                    continue
                b.box([(lo + hi) / 2.0, WALL_H / 2.0, (z0 + z1) / 2.0], [hi - lo, WALL_H, z1 - z0],
                      BASE)
                # the gold band, a hair over the top
                b.box([(lo + hi) / 2.0, WALL_H + 0.5, (z0 + z1) / 2.0], [hi - lo, 1.0, z1 - z0],
                      GOLD, material="metal", collide=False)
    b.rig("glass_dome", 0.0, WALL_H + 1.0, 0.0, hx=hx + m, hz=hz + m, h=170.0)
    # drifts against the base where it curves in, the last shake's leavings
    for sx in (-1, 1):
        for sz in (-1, 1):
            x = sx * 196.0
            z = sz * (edge(196.0) - 14.0)
            kit.mound(b, x, z, 22.0, 12.0, 2, 1.6, [SNOW_SHADE, SNOW], band=4.0)


# ================================================================ tunnels
def _tunnel(b: kit.RelayArea, h: Half) -> None:
    """The ice tunnel: from the cellar stair beside the flag, down under
    the hill and along to the ice cave on the edge of the village."""
    x0, x1 = TUNNEL_X
    z0, z1 = TUNNEL_Z
    area = h.r(x0, x1, z0, z1)
    kit.channel(b, area, -TUNNEL_FLOOR, ICE, wall_c=ICE_DEEP, studs=True)
    # the roof where the hill does not cover it
    wells = [h.r(CAVE_STAIR[0], CAVE_STAIR[1], z0, z1), h.r(CELLAR_STAIR[0], CELLAR_STAIR[1], z0, z1)]
    kit.plate(b, carve(area, wells), 0.0, 0.6, SNOW, studs=True)
    # up to the cave (rising inward), down from the chalet (falling inward)
    h.flight_x(CAVE_STAIR[1], CAVE_STAIR[0], z0, z1, TUNNEL_FLOOR, 0.0, ICE, fill=TUNNEL_FLOOR)
    h.flight_x(CELLAR_STAIR[1], CELLAR_STAIR[0], z0, z1, HILL_TOP, TUNNEL_FLOOR, ICE,
               fill=TUNNEL_FLOOR)
    zc = (z0 + z1) / 2.0
    for x in range(int(x0) + 24, int(CELLAR_STAIR[0]) - 6, 20):
        strip_light(b, h.x(float(x)), zc, -0.6 if x < 188 else 0.0, 5.0, "z", "#9fe8ff")
    # icicles from the roof, columns of ice: cover down there
    for x in (196.0, 236.0):
        h.box(x, TUNNEL_FLOOR + 3.0, z0 + 2.0, 2.4, 6.0, 2.4, ICE_DEEP)
        h.box(x + 6.0, TUNNEL_FLOOR + 3.0, z1 - 2.0, 2.0, 6.0, 2.0, ICE_DEEP)
    # the ice cave's mouth: walls of ice each side of the stairwell and
    # behind it, open towards the village
    for z in (z0 - 1.0, z1 + 1.0):
        h.box((CAVE_STAIR[0] + CAVE_STAIR[1]) / 2.0, 2.5, z, CAVE_STAIR[1] - CAVE_STAIR[0], 5.0,
              2.0, ICE_DEEP, studs=True)
    h.box(CAVE_STAIR[1] + 1.5, 3.5, zc, 3.0, 7.0, z1 - z0 + 4.0, ICE_DEEP, studs=True)
    for z, s in ((z0 - 4.0, 1.5), (z1 + 4.0, 1.2)):
        kit.boulder(b, h.x(CAVE_STAIR[1] + 4.0), z, 0.0, s, "#a8d8f0")
    h.sign(CAVE_STAIR[1] - 0.36, 5.4, zc, 8.0, 2.4,
           kit.sign_decal("ICE CAVE", "#d8f0ff", "#1a4a6a", 3.3), "x-")


# ==================================================================== hills
def _hill(b: kit.RelayArea, h: Half) -> None:
    """The chalet's hill: five steps of drifted snow, each a stride high,
    the cellar stair's well cut through the top."""
    cut = [h.r(CELLAR_STAIR[0], CELLAR_STAIR[1], TUNNEL_Z[0], TUNNEL_Z[1])]
    hx = HALF[0]
    tiers = []
    for k in range(5):
        pieces = []
        for r in kit.ellipse_rects(h.x(FLAG_X), 0.0, 78.0 - 10.0 * k, 122.0 - 17.0 * k, band=6.0):
            r = (max(r[0], -hx), min(r[1], hx), r[2], r[3])
            if r[1] - r[0] > 1.0:
                pieces.extend(carve(r, cut))
        tiers.append(pieces)
    kit.tier_stack(b, tiers, 0.0, [2.0], [SNOW_SHADE, SNOW, SNOW_SHADE, SNOW, SNOW_SHADE],
                   studs=True)


def _chalet(b: kit.RelayArea, h: Half) -> None:
    """A chalet on the hill: a stone base, timber above, shutters in the
    team's colours, a balcony across its front with a stair up at each end,
    a steep roof deep in snow -- and the flag in the great room, by the
    fire, with the cellar stair beside it."""
    x0, x1, z0, z1 = CHALET
    y = HILL_TOP
    top = y + CHALET_H
    area = h.r(x0, x1, z0, z1)
    doors = {h.inward: [(-8.0, 8.0, y + 7.0)],
             "z-": [(*h.xs(250.0, 260.0), y + 8.0)], "z+": [(*h.xs(250.0, 260.0), y + 8.0)],
             h.outward: [(6.0, 14.0, y + 8.0)]}
    room_walls(b, area, 2.0, y, y + 4.0, "#8a8a92", doors=doors)
    room_walls(b, area, 2.0, y + 4.0, top, TIMBER,
               doors={side: [(a, c, head) for a, c, head in spans if head > y + 4.0]
                      for side, spans in doors.items()})
    # windows: lit panes, shutters in the team's colours
    for z in (z0 - 0.06, z1 + 0.06):
        for xx in (272.0, 284.0):
            h.box(xx, y + 9.0, z, 5.0, 3.6, 0.1, "#ffe8a8", material="neon", collide=False)
            for dx in (-3.6, 3.6):
                h.box(xx + dx, y + 9.0, z, 2.0, 4.6, 0.12, h.colour, collide=False)
    # the roof: a slab and a steep gable, snow on every step, icicles
    slab(b, h.r(x0 - 3.0, x1 + 3.0, z0 - 3.0, z1 + 3.0), top + 1.2, 1.2, SLATE, studs=True)
    kit.gable(b, h.r(x0 - 3.0, x1 + 3.0, z0 - 3.0, z1 + 3.0), top + 1.2, SNOW, along="x",
              tiers=4, rise=2.0)
    for z in (z0 - 3.6, z1 + 3.6):
        for k in range(6):
            h.cone(x0 + 4.0 + k * 8.6, top - 0.2, z, 0.8, 2.4, 0.8, ICE, collide=False,
                   r=[math.pi, 0.0, 0.0])
    # the chimney and its smoke
    h.box(286.0, top + 7.0, 22.0, 4.0, 12.0, 4.0, "#8a8a92")
    b.rig("steam", h.x(286.0), top + 13.2, 22.0, n=7, c="#d8dce4")
    # the balcony across the front, a stair up to it at each end
    bx0 = x0 - 6.4          # (off the hill's whole-unit terrace edges)
    h.slab(bx0, x0, -28.0, 28.0, y + 8.0, 1.0, TIMBER_DARK, studs=True)
    h.box(bx0 + 0.4, y + 9.6, 0.0, 0.8, 3.2, 40.0, TIMBER_DARK)
    for sz in (-1, 1):
        # (the hill is a step lower out where the stair starts)
        h.flight_z(sz * 46.0, sz * 28.0, bx0, x0, y - 2.0, y + 8.0, TIMBER, fill=0.0)
        h.box(bx0 + 1.0, y + 3.5, sz * 22.0, 1.6, 7.0, 1.6, TIMBER_DARK)
    # the great room: the hearth on the back wall, the flag before it,
    # armchairs, a rug, skis on the wall
    h.box(x1 - 4.0, y + 4.0, 16.0, 4.0, 8.0, 14.0, "#8a8a92", studs=True)
    h.box(x1 - 6.06, y + 2.2, 16.0, 0.1, 2.8, 6.0, "#ff8a2a", material="neon", collide=False)
    b.rig("hearth_fire", h.x(x1 - 6.6), y, 16.0, w=5.0, h=4.0)
    top_y = kit.pedestal(b, h.x(FLAG_X), 0.0, y, h.colour, h.neon, base=TIMBER_DARK)
    b.flag(h.team, h.x(FLAG_X), top_y, 0.0)
    kit.banner_mast(b, h.x(x0 - 10.0), 52.0, b.surface(h.x(x0 - 10.0), 52.0, 40.0), 26.0,
                    h.team, h.inward)
    for xx, zz in ((250.0, 24.0), (282.0, 4.0)):
        h.box(xx, y + 1.6, zz, 4.4, 3.2, 4.4, h.dark, studs=True)
    h.box(254.0, y + 0.05, 24.0, 10.0, 0.1, 8.0, h.light, collide=False)
    for k in range(3):
        h.box(x0 + 2.3 + 0.0, y + 7.0, -16.0 + k * 2.2, 0.6, 9.0, 0.8,
              ["#c42b20", "#f2c21e", "#2a6aa8"][k], collide=False)
    # the cellar stair's well, railed on its open sides
    sx0, sx1 = CELLAR_STAIR
    tz0, tz1 = TUNNEL_Z
    h.box(sx0 - 0.6, y + 1.5, (tz0 + tz1) / 2.0, 1.2, 3.0, tz1 - tz0, TIMBER_DARK)
    h.box((sx0 + sx1) / 2.0 - 0.6, y + 1.5, tz1 + 0.6, sx1 - sx0 - 1.2, 3.0, 1.2, TIMBER_DARK)
    h.box((sx0 + sx1) / 2.0 - 0.6, y + 1.5, tz0 - 0.6, sx1 - sx0 - 1.2, 3.0, 1.2, TIMBER_DARK)
    strip_light(b, h.x((x0 + x1) / 2.0), 0.0, top, 40.0, "x", WARM)


# =================================================================== town
def _street(b: kit.RelayArea, h: Half, rng: random.Random) -> None:
    """The main street from the square to the hill: shops each side under
    deep snow, lamps, a woodshed, chimneys smoking."""
    houses = [  # x0, x1, z0, z1, door side, colour, sign
        (82.0, 110.0, 28.0, 54.0, "z-", "#f2e0c8", ("TOYS", "#c42b20")),
        (118.0, 150.0, 26.0, 58.0, "z-", PLASTER, ("THE SNOWY OWL", "#2a5a3a")),
        (160.0, 184.0, 30.0, 56.0, "z-", "#e8d8e8", ("CLOCKS", "#4a3a6a")),
        (82.0, 110.0, -54.0, -28.0, "z+", "#f2e8c0", ("CHEESE", "#c8901e")),
        (118.0, 146.0, -58.0, -36.0, "z+", "#e0e8f0", ("POST", "#c42b20")),
    ]
    for x0, x1, z0, z1, door, colour, (name, sign_bg) in houses:
        area = h.r(x0, x1, z0, z1)
        xc = (x0 + x1) / 2.0
        height = 12.0 if (x1 - x0) < 30 else 14.0
        kit.building(b, area, 0.0, height, colour, roof=True, roof_colour=SLATE,
                     doors={door: [(*h.xs(xc - 3.0, xc + 3.0), 7.5)]},
                     windows={door: [(*h.xs(x0 + 3.0, x0 + 8.0), 3.5, 7.0),
                                     (*h.xs(x1 - 8.0, x1 - 3.0), 3.5, 7.0)]},
                     glass=True, lights=WARM)
        kit.gable(b, area, height + 1.2, SNOW, along="x", tiers=4, rise=2.0)
        face = z0 if door == "z-" else z1
        out = -1.0 if door == "z-" else 1.0
        aspect = max(2.0, len(name) * 0.55)
        h.box(xc, height - 2.4, face + out * 0.36, min(x1 - x0 - 4.0, 3.0 * aspect), 3.0, 0.7,
              sign_bg, collide=False, r=[0.0, 0.0 if out > 0 else math.pi, 0.0],
              decal=kit.sign_decal(name, sign_bg, "#fff4d8", aspect))
        # window boxes of red geraniums under the snow
        h.box(x0 + 5.5, 2.8, face + out * 0.9, 5.0, 1.0, 1.6, "#8a3a1c")
        h.box(x0 + 5.5, 3.5, face + out * 0.9, 4.4, 0.4, 1.2, "#e8f0f4", collide=False)
        # a chimney, smoking
        h.box(x1 - 5.0, height + 9.0, (z0 + z1) / 2.0, 3.0, 8.0, 3.0, "#8a8a92")
        b.rig("steam", h.x(x1 - 5.0), height + 13.4, (z0 + z1) / 2.0, n=5, c="#d8dce4")
    # the inn's hanging sign on a bracket, and a sledge by its door
    h.box(134.0, 9.0, 24.6, 0.6, 0.6, 4.0, "#2a2a30")
    h.box(134.0, 7.0, 22.8, 0.3, 3.6, 3.0, "#2a5a3a", collide=False,
          decal=kit.sign_decal("OWL", "#2a5a3a", "#fff4d8", 0.83), r=[0.0, math.pi / 2.0, 0.0])
    h.box(126.0, 0.6, 20.0, 7.0, 0.6, 2.8, "#c42b20")
    # the woodshed: an open shelter with log stacks (cover)
    h.slab(172.0, 196.0, -50.0, -30.0, 9.2, 1.0, TIMBER_DARK, studs=True)
    for xx in (173.0, 195.0):
        for zz in (-49.0, -31.0):
            h.box(xx, 4.35, zz, 1.4, 8.7, 1.4, TIMBER_DARK)
    for k, (xx, zz) in enumerate(((178.0, -44.0), (188.0, -44.0), (183.0, -36.0))):
        h.box(xx, 2.0, zz, 8.0, 4.0, 4.0, "#8a5a3a", studs=True)
    # lamps down the street, their flames guttering
    for x in (78.0, 114.0, 142.0, 192.0):        # (clear of the ice cave at 150-166)
        for z in (-21.0, 21.0):
            kit.lamp_post(b, h.x(x), z, 0.0, 10.0, WARM, "#2a2a30")
            b.rig("gaslight", h.x(x), 9.8, z, seed=x * 0.1 + z + h.sx)
    # cobbles under the snow along the street
    h.box(128.0, 0.04, 0.0, 116.0, 0.08, 30.0, COBBLE, collide=False)
    del rng


def _outposts(b: kit.RelayArea, h: Half) -> None:
    """The bakery (north) and the ski hut (south): where a team falls back
    to while its flag is out."""
    kit.outpost_room(h, 150.0, 190.0, 100.0, 136.0, 0.0, "#f2d8b8", SLATE, height=11.0,
                     door_w=12.0, pads=2, lights=WARM)
    kit.gable(b, h.r(150.0, 190.0, 100.0, 136.0), 12.2, SNOW, along="x", tiers=3, rise=2.0)
    h.box(170.0, 8.6, 100.0 - 0.36, 12.0, 3.0, 0.7, "#c8901e", collide=False,
          r=[0.0, math.pi, 0.0], decal=kit.sign_decal("BAKERY", "#c8901e", "#fff4d8", 4.0))
    h.box(186.0, 16.0, 118.0, 3.0, 8.0, 3.0, "#8a8a92")
    b.rig("steam", h.x(186.0), 20.4, 118.0, n=6, c="#e8e0d0")
    kit.outpost_room(h, 150.0, 190.0, -136.0, -100.0, 0.0, TIMBER, SLATE, height=11.0,
                     door_w=12.0, pads=2, lights=WARM)
    kit.gable(b, h.r(150.0, 190.0, -136.0, -100.0), 12.2, SNOW, along="x", tiers=3, rise=2.0)
    for k in range(3):
        h.box(148.6, 4.0, -126.0 + k * 3.0, 0.6, 8.0, 0.6, ["#c42b20", "#2a6aa8", "#f2c21e"][k])
    h.box(170.0, 8.6, -100.0 + 0.36, 12.0, 3.0, 0.7, "#2a6aa8", collide=False,
          decal=kit.sign_decal("SKI HUT", "#2a6aa8", "#ffffff", 4.0))


def _ski_jump(b: kit.RelayArea, h: Half) -> None:
    """A ski jump by the ski hut: a timber tower with a stair up its back,
    a deck at the top you can see the whole globe from, the in-run sloping
    away towards the pond."""
    deck = (214.0, 228.0, -152.0, -134.0)
    top = 18.0
    h.flight_x(196.0, 214.0, -150.0, -140.0, 0.0, top, TIMBER, fill=0.0)
    h.slab(deck[0], deck[1], deck[2], deck[3], top, 1.2, TIMBER_DARK, studs=True)
    for xx in (deck[0] + 1.0, deck[1] - 1.0):
        for zz in (deck[2] + 1.0, deck[3] - 1.0):
            h.box(xx, (top - 1.2) / 2.0, zz, 1.6, top - 1.2, 1.6, TIMBER_DARK)
    kit.rails(b, h.r(deck[0], deck[1], deck[2], deck[3]), top, h=2.6, c=TIMBER_DARK, t=0.6,
              gaps={h.inward: [(-150.0, -140.0)], "z+": [(*h.xs(218.0, 224.0),)]})
    # the in-run: packed snow stepping down north off the deck (the quick
    # way down, and a second way up)
    h.flight_z(-134.0, -108.0, 218.0, 224.0, top, 0.0, SNOW_SHADE, fill=0.0)
    # sledges and a snowman at its foot
    for dz in (-4.0, 4.0):
        h.box(204.0, 0.6, -126.0 + dz, 5.0, 0.6, 2.4, "#c42b20")
    _snowman(b, h, 204.0, -104.0)


def _snowman(b: kit.RelayArea, h: Half, x: float, z: float, s: float = 1.0) -> None:
    h.sphere(x, 3.0 * s, z, 7.0 * s, 6.0 * s, 7.0 * s, SNOW)
    h.sphere(x, 7.6 * s, z, 5.0 * s, 4.6 * s, 5.0 * s, SNOW, collide=False)
    h.sphere(x, 11.0 * s, z, 3.6 * s, 3.4 * s, 3.6 * s, SNOW, collide=False)
    h.cyl(x, 13.6 * s, z, 2.6 * s, 2.4 * s, 2.6 * s, "#1b1b1b", collide=False)
    h.cyl(x, 12.55 * s, z, 3.8 * s, 0.3 * s, 3.8 * s, "#1b1b1b", collide=False)
    h.cone(x - 2.0 * s, 11.0 * s, z, 0.6 * s, 2.4 * s, 0.6 * s, "#e87a2a", collide=False,
           r=[0.0, 0.0, 1.57])
    h.box(x, 9.4 * s, z, 4.6 * s, 0.8 * s, 4.6 * s, "#c42b20", collide=False)


def _forts(b: kit.RelayArea, h: Half) -> None:
    """Snowball forts in the lanes north and south of the square: walls of
    snow blocks a stride high, cover for the crossing, a pile of snowballs
    behind each."""
    for sz in (-1, 1):
        z = sz * 84.0
        h.box(104.0, 1.6, z, 14.0, 3.2, 3.0, SNOW_SHADE, studs=True)
        h.box(110.0, 1.6, z + sz * 6.0, 3.0, 3.2, 9.0, SNOW_SHADE, studs=True)
        h.box(98.0, 3.6, z, 4.0, 0.8, 3.0, SNOW, studs=True)
        for k in range(4):
            h.sphere(104.0 + (k % 2) * 1.6, 0.9 + (k // 2) * 1.3, z + sz * 3.4, 1.8, 1.8, 1.8,
                     "#ffffff", collide=False)
    _snowman(b, h, 64.0, 96.0, 1.1)
    _snowman(b, h, 202.0, 76.0, 0.9)


def _pines(b: kit.RelayArea, h: Half) -> None:
    """Pines heavy with snow round the village and up the hill's flanks."""
    for x, z, s in ((212.0, 120.0, 1.3), (232.0, 140.0, 1.1), (200.0, 150.0, 0.9),
                    (216.0, -96.0, 1.0), (60.0, 150.0, 1.2), (96.0, 160.0, 1.0),
                    (60.0, -96.0, 1.0), (96.0, -150.0, 1.1), (252.0, 104.0, 1.2),
                    (252.0, -106.0, 1.1)):
        kit.pine(b, h.x(x), z, b.surface(h.x(x), z, 30.0), s, TIMBER_DARK, PINE, snow=SNOW)


# ==================================================================== hall
def _hall(b: kit.RelayArea) -> None:
    """The town hall: two muster halls and the council chamber between
    them, a steep roof, and the clock tower over it all, its four faces
    counting the round down."""
    hx, hz = HALL
    area = rect(-hx, hx, -hz, hz)
    room_walls(b, area, 3.0, 0.0, HALL_TOP, PLASTER,
               doors={"x-": [(-7.0, 7.0, 10.0)], "x+": [(-7.0, 7.0, 10.0)],
                      "z-": [(-5.0, 5.0, 9.0)], "z+": [(-5.0, 5.0, 9.0)]})
    for sx in (-1, 1):
        holed_wall(b, "z", sx * 13.0, 2.0, -hz + 3.0, hz - 3.0, 0.0, HALL_TOP, TIMBER,
                   holes=[(-6.0, 6.0, -1.0, 9.0)])
    slab(b, area, HALL_TOP + 1.2, 1.2, SLATE, studs=True)
    kit.gable(b, rect(-hx - 2.0, hx + 2.0, -hz - 2.0, hz + 2.0), HALL_TOP + 1.2, SNOW,
              along="x", tiers=4, rise=2.6)
    # the clock tower out of the ridge: four faces (rigs), a lantern of a
    # belfry, a gilded spire
    tower_base = HALL_TOP + 1.2 + 4 * 2.6
    b.box([0.0, tower_base + 11.0, 0.0], [14.0, 22.0, 14.0], "#e8d8c0")
    for yaw, (x, z) in ((0.0, (0.0, 7.0)), (math.pi, (0.0, -7.0)), (math.pi / 2.0, (7.0, 0.0)),
                        (-math.pi / 2.0, (-7.0, 0.0))):
        b.rig("round_clock", x, tower_base + 14.0, z, yaw=yaw, r=5.0, chime=yaw == 0.0)
    b.box([0.0, tower_base + 22.6, 0.0], [16.0, 1.2, 16.0], TIMBER_DARK, studs=True)
    for sx in (-1, 1):
        for sz in (-1, 1):
            b.box([sx * 6.4, tower_base + 26.2, sz * 6.4], [1.6, 6.0, 1.6], TIMBER_DARK)
    b.box([0.0, tower_base + 29.8, 0.0], [16.0, 1.2, 16.0], TIMBER_DARK)
    b.rig("church_bell", 0.0, tower_base + 28.6, 0.0, s=1.3)
    b.cone([0.0, tower_base + 37.4, 0.0], [15.0, 14.0, 15.0], SLATE, collide=False)
    b.sphere([0.0, tower_base + 44.6, 0.0], [1.8, 1.8, 1.8], GOLD, material="metal", collide=False)
    # inside: the council table, the town's crest over the north door
    b.box([0.0, 1.6, 0.0], [14.0, 3.2, 6.0], TIMBER_DARK, studs=True)
    b.cyl([0.0, 10.4, hz - 3.06], [5.0, 0.12, 5.0], GOLD, collide=False,
          r=[math.pi / 2.0, 0.0, 0.0])
    strip_light(b, 0.0, 0.0, HALL_TOP, 40.0, "z", WARM)
    for h in halves(b):
        for i in range(3):
            for j in (-1, 1):
                b.muster(h.team, h.x(17.0 + 5.0 * i), 0.0, j * 13.0, h.yaw_out, size=4.4)
        h.sign(hx - 3.36, 11.4, 0.0, 10.0, 3.0, "sign_%s" % h.team, "x+")
        strip_light(b, h.x(24.0), 0.0, HALL_TOP, 40.0, "z", WARM)
        h.box(hx + 7.0, 2.0, -14.0, 6.0, 4.0, 6.0, TIMBER_DARK, studs=True)
        h.box(hx + 7.0, 1.6, 14.0, 5.0, 3.2, 5.0, "#8a8a92", studs=True)


def _square(b: kit.RelayArea) -> None:
    """The square round the town hall: cobbles under the snow, a frozen
    fountain, the music-box carousel, stalls selling hot chestnuts."""
    for sx in (-1, 1):
        b.box([sx * 53.0, 0.03, 0.0], [26.0, 0.06, 92.0], COBBLE, collide=False)
    for sz in (-1, 1):
        b.box([0.0, 0.03, sz * 38.0], [80.0, 0.06, 18.0], COBBLE, collide=False)
    # the frozen fountain north of the hall
    b.cyl([0.0, 1.0, 44.0], [14.0, 2.0, 14.0], "#8a8a92", studs=True)
    b.cyl([0.0, 2.06, 44.0], [12.0, 0.12, 12.0], ICE, collide=False, material="glass", alpha=0.7)
    b.cyl([0.0, 4.0, 44.0], [2.0, 4.0, 2.0], "#8a8a92")
    b.sphere([0.0, 6.6, 44.0], [3.6, 1.8, 3.6], ICE, collide=False)
    for k in range(6):
        a = k * math.pi / 3.0
        b.cone([math.cos(a) * 1.2, 5.6, 44.0 + math.sin(a) * 1.2], [0.5, 1.4, 0.5], ICE,
               collide=False, r=[math.pi, 0.0, 0.0])
    # the carousel south of the hall: its round floor is a step to stand on;
    # the horses and the canopy turn over it (a rig, with a music box)
    b.cyl([0.0, 0.6, -46.0], [24.0, 1.2, 24.0], "#c8a060", studs=True)
    b.cyl([0.0, 7.0, -46.0], [2.4, 12.0, 2.4], GOLD, material="metal")
    b.rig("carousel", 0.0, 1.2, -46.0, r=11.0, h=11.0)
    # chestnut stalls
    for sx in (-1, 1):
        x = sx * 52.0
        for dx in (-4.0, 4.0):
            b.cyl([x + dx, 3.5, 40.0], [0.6, 7.0, 0.6], TIMBER_DARK)
        b.box([x, 7.6, 40.0], [11.0, 1.2, 7.0], "#c42b20" if sx < 0 else "#2a6aa8", collide=False)
        b.box([x, 2.0, 42.0], [9.0, 4.0, 2.0], TIMBER, studs=True)
        b.cyl([x, 4.6, 42.0], [2.0, 1.2, 2.0], "#3a3a3a", collide=False)
        b.rig("steam", x, 5.4, 42.0, n=4, c="#e8e0d8")


def _loop(b: kit.RelayArea) -> None:
    """The toy train's loop round the square: a track bed a step high,
    rails on it, a little station -- and the train itself, round and round
    (a rig: it whistles when it passes you)."""
    lx, lz = LOOP
    t = 4.0
    for sz in (-1, 1):
        slab(b, rect(-lx - t / 2.0, lx + t / 2.0, sz * lz - t / 2.0, sz * lz + t / 2.0), 0.8, 0.8,
             "#6a5a4a")
    for sx in (-1, 1):
        slab(b, rect(sx * lx - t / 2.0, sx * lx + t / 2.0, -lz + t / 2.0, lz - t / 2.0), 0.8, 0.8,
             "#6a5a4a")
    for sz in (-1, 1):
        for dz in (-1.0, 1.0):
            b.box([0.0, 1.0, sz * lz + dz], [2 * lx + t, 0.4, 0.4], "#9a9aa0", material="metal",
                  collide=False)
    for sx in (-1, 1):
        for dx in (-1.0, 1.0):
            b.box([sx * lx + dx, 1.0, 0.0], [0.4, 0.4, 2 * lz - t], "#9a9aa0", material="metal",
                  collide=False)
    b.rig("toy_train", 0.0, 1.2, 0.0, hx=lx, hz=lz, speed=9.0, cars=4)
    # the station on the north run
    b.box([0.0, 0.3, lz + 6.0], [24.0, 0.6, 6.0], "#8a8a92", studs=True)
    for sx in (-1, 1):
        b.cyl([sx * 10.0, 4.0, lz + 7.0], [0.6, 7.4, 0.6], TIMBER_DARK)
    b.box([0.0, 8.2, lz + 6.5], [26.0, 1.2, 8.0], "#c42b20", collide=False)
    b.box([0.0, 6.8, lz + 8.6], [8.0, 1.6, 0.3], "#f2ead8", collide=False,
          decal=kit.sign_decal("HOLLOW", "#f2ead8", "#2a2a30", 5.0))


def _church(b: kit.RelayArea) -> None:
    """The little church north of the square: its onion dome, its bell,
    pews inside, candles in the windows."""
    area = rect(-18.0, 18.0, 100.0, 150.0)
    room_walls(b, area, 2.0, 0.0, 14.0, PLASTER, doors={"z-": [(-5.0, 5.0, 9.0)]})
    slab(b, area, 15.2, 1.2, SLATE, studs=True)
    kit.gable(b, area, 15.2, SNOW, along="z", tiers=4, rise=2.2)
    b.box([0.0, 21.6, 104.0], [10.0, 12.8, 8.0], PLASTER)
    for sx in (-1, 1):
        for sz in (-1, 1):
            b.box([sx * 4.2, 31.0, 104.0 + sz * 3.2], [1.6, 6.0, 1.6], PLASTER)
    b.box([0.0, 34.6, 104.0], [11.0, 1.2, 9.0], SLATE)
    b.sphere([0.0, 39.4, 104.0], [10.0, 9.0, 10.0], "#3a6a4a", collide=False)
    b.cone([0.0, 45.4, 104.0], [2.0, 6.0, 2.0], GOLD, collide=False)
    b.rig("church_bell", 0.0, 33.8, 104.0, s=0.8, yaw=math.pi / 2.0)
    strip_light(b, 0.0, 125.0, 14.0, 40.0, "z", WARM)
    for z in (114.0, 122.0, 130.0, 138.0):
        for sx in (-1, 1):
            b.box([sx * 8.0, 1.2, z], [8.0, 2.4, 2.0], TIMBER_DARK, studs=True)
    for sx in (-1, 1):
        b.box([sx * 18.06, 8.0, 126.0], [0.1, 4.0, 3.0], "#ffd890", material="neon",
              collide=False)


def _pond(b: kit.RelayArea) -> None:
    """The skating pond: ice you can run on, skaters going round and round
    (rigs), benches and lanterns on the bank."""
    x0, x1, z0, z1 = POND
    slab(b, rect(x0, x1, z0, z1), 0.6, 0.6, ICE, material="glass", alpha=0.92)
    for k in range(3):
        b.rig("skater", 0.0, 0.6, (z0 + z1) / 2.0, rx=40.0 - k * 8.0, rz=18.0 - k * 3.0,
              seed=k * 2.1, c=["#c42b20", "#2a6aa8", "#2a8a4a"][k], speed=0.32 + k * 0.05)
    for sx in (-1, 1):
        kit.bench(b, sx * 40.0, -104.0, along="x")
        kit.lamp_post(b, sx * 66.0, -140.0, 0.0, 9.0, WARM, "#2a2a30")
        b.rig("gaslight", sx * 66.0, 8.8, -140.0, seed=sx * 4.0)


# ============================================================ beyond the glass
def _room(b: kit.RelayArea) -> None:
    """The living room beyond the glass: the mantelpiece the globe stands
    on, the fire, the clock on the mantel (counting the round down) -- and
    the eye that comes to the glass now and then."""
    hx, hz, m = HALF[0], HALF[1], b.margin
    zf = hz + m
    b.box([0.0, -20.0, zf + 120.0], [1300.0, 40.0, 240.0], "#5a2a1a", collide=False)
    b.box([0.0, 70.0, zf + 250.0], [560.0, 180.0, 40.0], "#7a4a3a", collide=False)
    b.box([0.0, 30.0, zf + 229.8], [320.0, 100.0, 0.4], "#2a1a12", collide=False)
    b.rig("hearth_fire", 0.0, 0.0, zf + 226.0, w=200.0, h=70.0, big=True)
    # the mantel clock, off to the east: a round_clock face the size of a house
    b.box([400.0, 110.0, zf + 90.0], [180.0, 220.0, 80.0], "#c8a060", collide=False)
    b.rig("round_clock", 400.0, 140.0, zf + 49.6, yaw=math.pi, r=60.0)
    # a window to the west, and the night (and the snow) outside it
    b.box([-470.0, 105.0, zf + 120.0], [20.0, 270.0, 400.0], "#d8c8a8", collide=False)
    b.box([-459.8, 140.0, zf + 120.0], [0.4, 160.0, 120.0], "#1a2a4a", collide=False)
    b.box([-459.4, 140.0, zf + 120.0], [0.4, 160.0, 6.0], "#f2ead8", collide=False)
    b.box([-459.3, 140.0, zf + 120.0], [0.4, 6.0, 120.0], "#f2ead8", collide=False)
    b.rig("giant_eye", hx + m + 40.0, 120.0, 0.0, yaw=-math.pi / 2.0, s=1.0)
    b.rig("snow_shake", 0.0, 40.0, 0.0, every=150.0)


def _landmarks(b: kit.RelayArea) -> None:
    for x, z, name in ((0, 0, "the town hall"), (0, 44, "the fountain"),
                       (0, 125, "the church"), (0, -140, "the skating pond"),
                       (0, -46, "the carousel"), (0, 68, "the station")):
        b.landmark(float(x), float(z), name)
    for sx, team in ((-1, "red"), (1, "blue")):
        b.landmark(sx * 266.0, 0.0, "the %s chalet" % team)
        for x, z, name in ((170, 118, "the bakery"), (170, -118, "the ski hut"),
                           (221, -143, "the ski jump"), (157, -25, "the ice cave"),
                           (134, 42, "the Snowy Owl"), (184, -40, "the woodshed")):
            b.landmark(sx * float(x), float(z), "%s (%s side)" % (name, team))
    b.camera(-150.0, 70.0, 150.0, 0.0, 10.0, 0.0)
    b.camera(150.0, 70.0, -150.0, 0.0, 10.0, 0.0)
    b.camera(0.0, 90.0, -175.0, 0.0, 14.0, 0.0)
