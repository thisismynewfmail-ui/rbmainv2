"""Polderhaven -- a polder in spring, below the sea and kept dry by mills.

Nothing here is flat, however it looks from the dike: the land is ditched
and banked and terraced, the canals sit below it and the dikes above it,
and the farms and the church stand on their mounds (terps) out of the wet.
Two great windmills hold the flags, one at each end, their sails going
round in the team's colours; both teams muster in the steam pumping
station in the middle, whose beam engine heaves away at the water -- and
works harder still while a flag is out.

Layout (red to the west; mirrored about x = 0)::

      z +130  WINDMILL TERP ... tulips ... FARMHOUSE (outpost) .. CHURCH TERP
      z    0  WINDMILL (flag) =dike= ~canal~ =bridge= pasture == PUMPING STATION
      z  -21  ====== drain tunnel: the mill's cellar -> sluice in the canal bank ======
      z  -65  ......................... the station's basin, the quay ...............
      z -120  tulips .............. CHEESE WAREHOUSE (outpost) .. pasture
      z -196  =========================================================================

Each half has a canal four deep running north to south with its dike on
the outer bank (three strides up, a road along the top), a white
drawbridge on the main road and footbridges north and south; the tulip
fields lie between the dike and the mill.  The drain tunnel is the
mill's own: from a stair beside the flag, under the dike, out through the
sluice gate into the canal.
"""
from __future__ import annotations

import math
import random

from . import kit
from .kit import (Half, carve, halves, holed_wall, rect, room_walls, slab, strip_light)

HALF = (310.0, 196.0)
SKY = {"top": "#4a8ae8", "horizon": "#e8f2fa", "sun": [0.45, 0.75, 0.35],
       "clouds": 0.75, "tint": "#fff8e8"}
AMBIENT = "#b8c0c8"
GROUND = "#5aa040"
FOG = 900.0

GRASS = "#5aa040"
GRASS_DARK = "#4a8a34"
GRASS_LIGHT = "#6ab44a"
SOIL = "#6a4a2e"
BRICK_RED = "#a84a32"
BRICK_DARK = "#7a3424"
STONE = "#c8c0b0"
WATER = "#3a7a9a"
WHITE = "#f4f2ea"
MILL_WOOD = "#3a4a3a"
THATCH = "#8a7a5a"
DIKE_TOP = "#9a9890"

STATION = (34.0, 24.0)
STATION_H = 14.0
CANAL_X = (118.0, 138.0)
CANAL_DEPTH = 4.0
WATER_Y = -1.4
DIKE_X = (142.0, 172.0)
DIKE_Z = 176.0
TERP_TOP = 4.0
MILL_X = 270.0
MILL_BASE = (250.0, 290.0, -20.0, 20.0)
MILL_ROOM_H = 10.0
DRAIN_Z = (-16.0, -6.0)
DRAIN_X = (138.0, 288.0)
DRAIN_FLOOR = -6.0
DRAIN_STAIR = (276.0, 288.0)
BASIN = (-60.0, 60.0, -92.0, -40.0)
TULIPS = ["#e8302a", "#f2c21e", "#f07aa8", "#ffffff", "#8a4ac8", "#f28a2a"]


def build(b: kit.RelayArea) -> None:
    rng = random.Random(0x7011)
    b.relay("the Pumping Station", 44.0)
    b.intro = ["Polderhaven -- spring in the polder, below the sea and kept dry by the mills.",
               "Muster in the pumping station; the flags are in the great windmills at either "
               "end, past the canal, over the dike and through the tulips.",
               "Each mill drains through a tunnel from beside the flag to a sluice in the canal."]
    b.extra.update({"accent": "#ffb84a", "weather": "petals"})
    holes = [rect(BASIN[0], BASIN[1], BASIN[2], BASIN[3])]
    for h in halves(b):
        holes.append(h.r(CANAL_X[0], CANAL_X[1], -HALF[1] - b.margin, HALF[1] + b.margin))
        holes.append(h.r(DRAIN_X[0], DRAIN_X[1], DRAIN_Z[0], DRAIN_Z[1]))
    kit.ground(b, GRASS, soil=SOIL, holes=holes)
    _basin(b)
    for h in halves(b):
        _canal(b, h)
        _drain(b, h)
        _dike(b, h)
        _mill(b, h)
        _tulips(b, h)
        _outposts(b, h)
        _pasture(b, h, random.Random(0xC0E5))
    _station(b)
    _church(b)
    _edge(b, rng)
    _life(b)
    _landmarks(b)


# ================================================================== water
def _canal(b: kit.RelayArea, h: Half) -> None:
    """The canal: four deep, the water over its bed, the white drawbridge
    on the main road and footbridges north and south."""
    x0, x1 = CANAL_X
    hz = HALF[1] + b.margin
    area = h.r(x0, x1, -hz, hz)
    kit.channel(b, area, CANAL_DEPTH, "#4a5a4a", studs=True)
    kit.water_sheet(b, area, WATER_Y, WATER, 0.62)
    # the drawbridge: a white bascule over the main road, its counterweight
    # beams up over it on their portal (the deck does not lift)
    deck = h.r(x0 - 2.0, x1 + 2.0, -7.0, 7.0)
    slab(b, deck, 0.8, 0.8, "#8a7a6a", studs=True)
    for z in (-7.4, 7.4):
        h.box((x0 + x1) / 2.0, 1.6, z, x1 - x0 + 4.0, 1.6, 0.8, WHITE)
    for x in (x0 + 1.0, x1 - 1.0):
        for z in (-6.2, 6.2):
            h.box(x, 6.5, z, 1.2, 11.4, 1.2, WHITE)
    for z in (-6.2, 6.2):
        h.box((x0 + x1) / 2.0, 12.8, z, x1 - x0, 1.2, 1.2, WHITE)
    b.rig("bascule", h.x((x0 + x1) / 2.0), 13.4, 0.0, w=x1 - x0, yaw=h.yaw_in)
    # footbridges north and south: plank decks a step up
    for z in (128.0, -150.0):
        slab(b, h.r(x0 - 1.0, x1 + 1.0, z - 3.0, z + 3.0), 0.6, 0.6, "#8a6a48", studs=True)
        for zz in (z - 3.2, z + 3.2):
            h.box((x0 + x1) / 2.0, 1.8, zz, x1 - x0 + 2.0, 0.4, 0.4, "#6a4a2e")
    # a clog in the canal: somebody lost a big one
    h.box((x0 + x1) / 2.0, -3.0, -84.0, 6.0, 2.4, 14.0, "#f2c21e", studs=True)
    h.box((x0 + x1) / 2.0, -2.6, -79.3, 5.6, 3.2, 3.4, "#f2c21e")


def _basin(b: kit.RelayArea) -> None:
    """The station's basin south of it, where the water goes: a stone quay
    all round, steps down at each end, a boat tied up."""
    x0, x1, z0, z1 = BASIN
    kit.channel(b, rect(x0, x1, z0, z1), CANAL_DEPTH, "#4a5a4a", studs=True)
    kit.water_sheet(b, rect(x0, x1, z0, z1), WATER_Y, WATER, 0.62)
    for sx in (-1, 1):
        kit.flight(b, "x", sx * x1, sx * (x1 - 10.0), -76.0, -64.0, 0.0, -CANAL_DEPTH, STONE,
                   fill=-CANAL_DEPTH)
    for x in range(-56, 60, 14):
        b.cyl([float(x), 1.0, z1 + 1.4], [1.2, 2.0, 1.2], "#2a2a2a", material="metal")
    b.box([0.0, -2.4, -60.0], [10.0, 3.2, 24.0], "#2a5a7a", studs=True)
    b.box([0.0, 0.0, -66.0], [7.0, 2.4, 8.0], "#e8e4d8")


def _drain(b: kit.RelayArea, h: Half) -> None:
    """The mill's drain: a stair down beside the flag, a brick tunnel under
    the tulips and the dike, out through the sluice into the canal (a step
    up onto its bed)."""
    x0, x1 = DRAIN_X
    z0, z1 = DRAIN_Z
    area = h.r(x0, x1, z0, z1)
    kit.channel(b, area, -DRAIN_FLOOR, "#5a4a3e", studs=True)
    well = h.r(DRAIN_STAIR[0], DRAIN_STAIR[1], z0, z1)
    kit.plate(b, carve(area, [well]), 0.0, 0.4, GRASS, studs=True)
    h.flight_x(DRAIN_STAIR[1], DRAIN_STAIR[0], z0, z1, TERP_TOP, DRAIN_FLOOR, BRICK_DARK,
               fill=DRAIN_FLOOR)
    zc = (z0 + z1) / 2.0
    for x in range(int(x0) + 14, int(DRAIN_STAIR[0]) - 6, 22):
        strip_light(b, h.x(float(x)), zc, -0.4, 4.0, "z", "#ffd890")
    # the sluice gate's frame in the bank, its wheel
    for z in (z0 - 1.0, z1 + 1.0):
        h.box(x0 + 0.6, -2.3, z, 2.0, 3.6, 1.6, STONE)
    h.box(x0 + 0.4, 0.0, zc, 2.0, 1.0, z1 - z0 + 4.0, STONE)
    h.cyl(x0 + 0.4, 0.7, zc, 1.8, 0.4, 1.8, "#6a4a2e", collide=False)


# ===================================================================== dikes
def _dike(b: kit.RelayArea, h: Half) -> None:
    """The dike on the canal's outer bank: three strides up to a road along
    the top -- high ground the length of the map -- with a windmill pumping
    on it at each end and a boy with his finger in it."""
    x0, x1 = DIKE_X
    drain = [h.r(DRAIN_X[0], DRAIN_X[1], DRAIN_Z[0], DRAIN_Z[1])]
    tiers = []
    for k in range(3):
        r = h.r(x0 + 4.0 * k, x1 - 4.0 * k, -DIKE_Z + 6.0 * k, DIKE_Z - 6.0 * k)
        tiers.append([r])
    kit.tier_stack(b, tiers, 0.0, [2.0], [GRASS_DARK, GRASS, GRASS_LIGHT], studs=True)
    # the road along the top: a strip of tarmac, white posts
    top = 6.0
    h.box((x0 + x1) / 2.0, top + 0.04, 0.0, 8.0, 0.08, 2 * (DIKE_Z - 12.0), DIKE_TOP,
          collide=False)
    for z in range(-150, 151, 30):
        h.box(x0 + 10.0, top + 1.0, float(z), 0.6, 2.0, 0.6, WHITE)
    # the little mills along the dike, pumping
    for z in (150.0, -150.0):
        _little_mill(b, h, (x0 + x1) / 2.0, top, z)
    # the boy with his finger in the dike (on its canal face)
    bx, bz = x0 - 0.6, 60.0
    h.box(bx - 1.0, -2.2, bz, 1.0, 1.8, 1.2, "#2a4a8a", collide=False)
    h.box(bx - 1.0, -0.7, bz, 1.0, 1.4, 1.6, "#c42b20", collide=False)
    h.box(bx - 1.0, 0.5, bz, 1.0, 1.0, 1.0, "#f5cd30", collide=False)
    h.box(bx - 0.4, -0.5, bz + 1.1, 0.8, 0.3, 0.3, "#f5cd30", collide=False)
    del drain


def _little_mill(b: kit.RelayArea, h: Half, x: float, y: float, z: float) -> None:
    """A little drainage mill on the dike: a thatched cone of a body, its
    sails turning."""
    h.box(x, y + 2.0, z, 8.0, 4.0, 8.0, BRICK_RED, studs=True)
    h.cone(x, y + 11.0, z, 8.0, 14.0, 8.0, THATCH)
    h.box(x, y + 18.6, z, 3.0, 2.4, 4.0, MILL_WOOD, collide=False)
    b.rig("windmill_sails", h.x(x - 2.4), y + 18.6, z, yaw=h.yaw_in, r=11.0, c="#f4f2ea",
          seed=z * 0.1 + h.sx, rate=0.9)


# ==================================================================== mills
def _mill(b: kit.RelayArea, h: Half) -> None:
    """The great windmill on its terp at the team's end: a brick base (the
    mill room, the flag in it), the stage round its top -- the walk round
    the mill, a stair up each side -- the smock tapering above, the cap and
    the sails going round in the team's colours."""
    x0, x1, z0, z1 = MILL_BASE
    y = TERP_TOP
    # the terp: two strides of mound round the mill
    cut = [h.r(DRAIN_STAIR[0], DRAIN_STAIR[1], DRAIN_Z[0], DRAIN_Z[1])]
    tiers = []
    for k in range(2):
        pieces = []
        for r in kit.ellipse_rects(h.x(MILL_X), 0.0, 62.0 - 8.0 * k, 84.0 - 12.0 * k, band=6.0):
            r = (max(r[0], -HALF[0]), min(r[1], HALF[0]), r[2], r[3])
            if r[1] - r[0] > 1.0:
                pieces.extend(carve(r, cut))
        tiers.append(pieces)
    kit.tier_stack(b, tiers, 0.0, [2.0], [GRASS_DARK, GRASS], studs=True)
    top = y + MILL_ROOM_H
    area = h.r(x0, x1, z0, z1)
    room_walls(b, area, 2.0, y, top, BRICK_RED,
               doors={h.inward: [(-7.0, 7.0, y + 8.0)],
                      "z-": [(*h.xs(258.0, 268.0), y + 8.0)], "z+": [(*h.xs(258.0, 268.0), y + 8.0)]})
    slab(b, area, top + 1.0, 1.0, "#6a5a4a", studs=True)
    # the stage: a rail round the base's roof, stairs up each side
    kit.rails(b, area, top + 1.0, h=2.6, c=WHITE, t=0.6,
              gaps={"z-": [h.xs(282.0, 288.0)], "z+": [h.xs(282.0, 288.0)]})
    for sz in (-1, 1):
        h.flight_z(sz * 40.0, sz * 20.0, 282.0, 288.0, y, top + 1.0, "#8a6a48", fill=0.0)
    # the smock: three tiers of weatherboard tapering, the cap
    sy = top + 1.0
    for k, w in enumerate((32.0, 26.0, 20.0)):
        hgt = 10.0 - k
        h.box(MILL_X, sy + hgt / 2.0, 0.0, w, hgt, w, MILL_WOOD if k % 2 == 0 else "#4a5a4a")
        sy += hgt
    h.box(MILL_X, sy + 1.0, 0.0, 22.0, 2.0, 22.0, "#2a3a2a")
    kit.gable(b, h.r(MILL_X - 11.0, MILL_X + 11.0, -11.0, 11.0), sy + 2.0, "#2a3a2a", along="x",
              tiers=3, rise=2.0, overhang=0.0)
    # the windows of the smock, lit
    for k, wy in enumerate((top + 6.0, top + 15.0)):
        h.box(MILL_X - 16.06 + k * 3.0, wy, 0.0, 0.1, 3.0, 2.4, "#ffe8a8", material="neon",
              collide=False)
    # the sails, in front of the cap, turning (a rig: the team's cloth)
    b.rig("windmill_sails", h.x(x0 - 3.0), sy + 1.0, 0.0, yaw=h.yaw_in, r=29.0, c=h.light,
          stripe=h.colour, seed=h.sx, rate=0.45, axle=MILL_X - 11.0 - (x0 - 3.0))
    # the mill room: the flag among the sacks and the great wheel
    top_y = kit.pedestal(b, h.x(264.0), 0.0, y, h.colour, h.neon, base=BRICK_DARK, wide=20.0,
                         top_w=13.0)
    b.flag(h.team, h.x(264.0), top_y, 0.0)
    for xx, zz in ((256.0, 14.0), (256.0, -14.0), (284.0, 12.0)):
        h.box(xx, y + 1.4, zz, 4.0, 2.8, 3.0, "#e8dcc0", studs=True)
    h.cyl(286.0, y + 6.0, 16.0, 0.6, 12.0 - 0.0, 0.6, "#6a4a2e", collide=False)
    strip_light(b, h.x(270.0), 0.0, top, 30.0, "x", "#ffe8b0")
    # the drain stair's well, railed
    sx0, sx1 = DRAIN_STAIR
    tz0, tz1 = DRAIN_Z
    h.box(sx0 - 0.6, y + 1.5, (tz0 + tz1) / 2.0, 1.2, 3.0, tz1 - tz0, "#6a4a2e")
    h.box((sx0 + sx1) / 2.0 - 0.6, y + 1.5, tz1 + 0.6, sx1 - sx0 - 1.2, 3.0, 1.2, "#6a4a2e")
    kit.banner_mast(b, h.x(x0 - 12.0), 34.0, b.surface(h.x(x0 - 12.0), 34.0, 20.0), 24.0, h.team,
                    h.inward)
    # a haycart and a stork's nest on a pole by the mill
    gy = b.surface(h.x(232.0), -46.0, 20.0)
    h.box(232.0, gy + 1.2, -46.0, 10.0, 2.4, 6.0, "#8a6a48", studs=True)
    h.box(232.0, gy + 3.6, -46.0, 8.0, 2.4, 5.0, "#d8c070", studs=True)
    h.cyl(232.0, 10.0, 52.0, 1.0, 20.0, 1.0, "#6a4a2e")
    h.cyl(232.0, 20.6, 52.0, 5.0, 1.2, 5.0, "#8a7a5a")
    b.rig("stork", h.x(232.0), 21.2, 52.0, seed=h.sx * 2.0)


# =================================================================== tulips
def _tulips(b: kit.RelayArea, h: Half) -> None:
    """The bulb fields between the dike and the mill: beds of tulips in
    bands of colour, a stride high or less, ditches between."""
    for sz in (-1, 1):
        z_near, z_far = (40.0, 172.0)
        rows = int((z_far - z_near) // 6.0)
        for k in range(rows):
            z = sz * (z_near + 3.0 + k * 6.0)
            hgt = 1.0 if k % 2 else 1.4
            colour = TULIPS[(k + (0 if sz > 0 else 3)) % len(TULIPS)]
            h.box(196.0, hgt / 2.0, z, 36.0, hgt, 4.4, SOIL, studs=False)
            h.box(196.0, hgt + 0.3, z, 35.0, 0.6, 3.6, colour, collide=False)
            for x in (182.0, 196.0, 210.0):
                h.box(x, hgt + 0.9, z, 1.2, 0.6, 1.2, "#3a8a3a", collide=False)
    # a bulb shed past the southern field
    h.box(196.0, 4.0, -180.0, 12.0, 8.0, 10.0, "#e8e0d0", studs=True)


# ================================================================ outposts
def _outposts(b: kit.RelayArea, h: Half) -> None:
    """The farmhouse (north) and the cheese warehouse (south), each up on
    its own little terp: where a team falls back to while its flag is out."""
    for sz, name in ((1, "farm"), (-1, "cheese")):
        zlo, zhi = sorted((sz * 98.0, sz * 138.0))
        kit.mound(b, h.x(82.0), sz * 118.0, 34.0, 30.0, 1, 2.0, [GRASS_DARK], band=4.0)
        if name == "farm":
            kit.outpost_room(h, 62.0, 102.0, zlo, zhi, 2.0, WHITE, "#3a4a3a", height=11.0,
                             door_w=12.0, pads=2, lights="#ffe8b0")
            kit.gable(b, h.r(62.0, 102.0, zlo, zhi), 14.2, "#8a7a5a", along="x", tiers=4,
                      rise=2.0)
            h.box(98.0, 18.0, sz * 118.0, 3.0, 8.0, 3.0, BRICK_RED)
            b.rig("steam", h.x(98.0), 22.4, sz * 118.0, n=5, c="#e8ecee")
        else:
            kit.outpost_room(h, 62.0, 102.0, zlo, zhi, 2.0, "#f2c21e", "#a84a32", height=11.0,
                             door_w=12.0, pads=2, lights="#ffe8b0")
            # wheels of cheese stacked in the corners the pads leave free
            for xx, zz in ((92.0, -131.0), (72.0, -105.0)):
                h.cyl(xx, 2.0 + 1.2, zz, 6.0, 2.4, 6.0, "#f2c21e", studs=True)
                h.cyl(xx, 2.0 + 3.6, zz, 5.6, 2.4, 5.6, "#e8b81a", studs=True)
            h.box(82.0, 9.4, sz * 98.0 - sz * 0.36, 16.0, 3.0, 0.7, "#f2c21e", collide=False,
                  r=[0.0, 0.0 if sz < 0 else math.pi, 0.0],
                  decal=kit.sign_decal("KAAS", "#f2c21e", "#7a3424", 5.3))


def _pasture(b: kit.RelayArea, h: Half, rng: random.Random) -> None:
    """The pasture between the station and the canal: ditched, a stile or
    two, cows and sheep, a hay rick, pollard willows along the ditch."""
    for z in (52.0, -52.0):
        h.box(84.0, 1.2, z, 40.0, 2.4, 3.0, GRASS_DARK, studs=True)
    for x, z in ((54.0, 66.0), (66.0, 70.0), (102.0, 66.0), (110.0, -40.0), (52.0, -110.0)):
        h.cyl(x, 2.5, z, 2.0, 5.0, 2.0, "#6a5a3a")
        h.sphere(x, 6.2, z, 6.0, 4.4, 6.0, "#7aa84a", collide=False)
    h.cyl(96.0, 3.0, -64.0, 8.0, 6.0, 8.0, "#d8c070", studs=True)
    h.cone(96.0, 7.6, -64.0, 9.0, 3.2, 9.0, "#c8b060")
    for k, (x, z, yaw) in enumerate(((70.0, 30.0, 0.6), (96.0, -26.0, 2.2))):
        b.rig("cow", h.x(x), 0.0, z, yaw=yaw * h.sx, seed=k)
    for k, (x, z) in enumerate(((60.0, -150.0), (76.0, -164.0), (100.0, 160.0))):
        b.rig("sheep", h.x(x), 0.0, z, yaw=k * 1.7, seed=k + h.sx * 5)
    del rng


# ================================================================== station
def _station(b: kit.RelayArea) -> None:
    """The steam pumping station: two muster wings either side of the
    engine hall, where the beam engine rocks and the flywheel turns, a
    stepped gable, and the chimney smoking."""
    hx, hz = STATION
    area = rect(-hx, hx, -hz, hz)
    room_walls(b, area, 3.0, 0.0, STATION_H, BRICK_RED,
               doors={"x-": [(-7.0, 7.0, 10.0)], "x+": [(-7.0, 7.0, 10.0)],
                      "z-": [(-5.0, 5.0, 9.0)], "z+": [(-5.0, 5.0, 9.0)]})
    for sx in (-1, 1):
        holed_wall(b, "z", sx * 13.0, 2.0, -hz + 3.0, hz - 3.0, 0.0, STATION_H, BRICK_DARK,
                   holes=[(-6.0, 6.0, -1.0, 9.0)])
    slab(b, area, STATION_H + 1.2, 1.2, "#5a5a60", studs=True)
    kit.gable(b, rect(-hx - 1.0, hx + 1.0, -hz - 1.0, hz + 1.0), STATION_H + 1.2, "#7a3424",
              along="x", tiers=5, rise=2.0)
    # the engine: its cylinder, the column the beam rocks on, the flywheel
    # (the cylinder one side of the column, the flywheel's bearing the
    # other: the same block twice, so the hall is as fair as the map)
    for sx in (-1, 1):
        b.box([sx * 9.0, 3.0, 8.0], [4.0, 6.0, 4.0], "#3a3a40", studs=True)
    b.box([0.0, 5.0, 8.0], [2.0, 10.0, 2.0], "#2a6a4a")
    b.rig("beam_engine", 0.0, 0.0, 8.0, pivot_p=[0.0, 10.6, 8.0], cyl_p=[-9.0, 6.0, 8.0],
          wheel_p=[9.0, 7.8, 9.2], flags=True)
    b.box([0.0, 1.2, -14.0], [10.0, 2.4, 4.0], "#3a3a40", studs=True)
    strip_light(b, 0.0, 0.0, STATION_H, 40.0, "z", "#ffe8b0")
    # the chimney behind, smoking
    b.box([0.0, 24.0, hz + 6.0], [6.0, 48.0, 6.0], BRICK_DARK)
    b.box([0.0, 48.6, hz + 6.0], [7.4, 1.2, 7.4], STONE)
    b.rig("steam", 0.0, 49.4, hz + 6.0, n=8, c="#d8dce0", flags=True)
    for h in halves(b):
        for i in range(3):
            for j in (-1, 1):
                b.muster(h.team, h.x(17.0 + 5.0 * i), 0.0, j * 13.0, h.yaw_out, size=4.4)
        h.sign(hx - 3.36, 11.4, 0.0, 10.0, 3.0, "sign_%s" % h.team, "x+")
        strip_light(b, h.x(24.0), 0.0, STATION_H, 40.0, "z", "#ffe8b0")
        h.box(hx + 7.0, 2.0, -14.0, 6.0, 4.0, 6.0, BRICK_DARK, studs=True)
        h.box(hx + 7.0, 1.6, 14.0, 5.0, 3.2, 5.0, "#5a5a60", studs=True)
    b.box([0.0, 11.6, -hz - 0.36], [18.0, 2.6, 0.7], STONE, collide=False,
          decal=kit.sign_decal("GEMAAL 1878", STONE, "#3a2a1a", 6.9), r=[0.0, math.pi, 0.0])


def _church(b: kit.RelayArea) -> None:
    """The church on its terp north of the station: a brick tower with a
    clock and a carillon, the bells ringing a capture."""
    kit.mound(b, 0.0, 128.0, 46.0, 40.0, 2, 2.0, [GRASS_DARK, GRASS], band=4.0, shrink=0.9)
    y = 4.0
    area = rect(-16.0, 16.0, 112.0, 150.0)
    room_walls(b, area, 2.0, y, y + 13.0, BRICK_RED, doors={"z-": [(-4.0, 4.0, y + 8.0)]})
    slab(b, area, y + 14.2, 1.2, "#4a4a50", studs=True)
    kit.gable(b, area, y + 14.2, "#4a4a50", along="z", tiers=4, rise=2.2)
    # the tower: brick to the clock, an open belfry over it, the spire
    b.box([0.0, y + 16.0, 106.0], [10.0, 32.0, 10.0], BRICK_DARK)
    b.rig("round_clock", 0.0, y + 26.0, 100.94, yaw=math.pi, r=3.6, chime=True)
    for sx in (-1, 1):
        for sz in (-1, 1):
            b.box([sx * 4.2, y + 36.0, 106.0 + sz * 4.2], [1.6, 8.0, 1.6], BRICK_DARK)
    b.box([0.0, y + 40.6, 106.0], [11.0, 1.2, 11.0], STONE)
    b.cone([0.0, y + 47.2, 106.0], [10.0, 12.0, 10.0], "#3a5a4a", collide=False)
    b.rig("church_bell", 0.0, y + 39.6, 106.0, s=0.7)
    for z in (122.0, 130.0, 138.0):
        for sx in (-1, 1):
            b.box([sx * 7.0, y + 1.2, z], [7.0, 2.4, 2.0], "#6a4a2e", studs=True)


def _edge(b: kit.RelayArea, rng: random.Random) -> None:
    """The sea dike all round: the polder's edge, grassed, with the sea
    beyond it to the north and a line of poplars to the south."""
    hx, hz, m = HALF[0], HALF[1], b.margin
    room_walls(b, rect(-hx - m, hx + m, -hz - m, hz + m), m, 0.0, 18.0, GRASS_DARK, studs=True)
    b.box([0.0, -0.5, hz + m + 150.0], [1400.0, 2.0, 300.0], "#3a7aa8", collide=False,
          material="glass", alpha=0.9)
    kit.backdrop(b, "pines", 18.0, rng, colours=["#3a6a3a", "#4a7a3a", "#2f5a30"],
                 sides=("x-", "x+", "z-"), depth=40.0)


def _life(b: kit.RelayArea) -> None:
    """What moves: barges down the canals, cyclists along the dikes, ducks,
    a kite on the church terp, clouds."""
    hz = HALF[1]
    for h in halves(b):
        xc = (CANAL_X[0] + CANAL_X[1]) / 2.0
        b.rig("canal_boat", h.x(xc), WATER_Y, -hz + 20.0, q=[h.x(xc), WATER_Y, hz - 20.0],
              speed=4.0, seed=h.sx * 3.0, c=h.colour)
        b.rig("cyclist", h.x((DIKE_X[0] + DIKE_X[1]) / 2.0 - 1.5), 6.0, -150.0,
              q=[h.x((DIKE_X[0] + DIKE_X[1]) / 2.0 - 1.5), 6.0, 150.0], speed=9.0,
              seed=h.sx, c=h.colour)
        b.rig("cyclist", h.x((DIKE_X[0] + DIKE_X[1]) / 2.0 + 1.5), 6.0, 150.0,
              q=[h.x((DIKE_X[0] + DIKE_X[1]) / 2.0 + 1.5), 6.0, -150.0], speed=7.0,
              seed=h.sx + 5.0, c="#f2c21e")
        b.rig("duck", h.x(xc), WATER_Y, 90.0, r=6.0, seed=h.sx)
    b.rig("kite", 20.0, 4.0, 150.0, seed=1.0)
    b.rig("clouds", 0.0, 220.0, 0.0, n=9, r=520.0)


def _landmarks(b: kit.RelayArea) -> None:
    for x, z, name in ((0, 0, "the pumping station"), (0, -66, "the basin"),
                       (0, 128, "the church")):
        b.landmark(float(x), float(z), name)
    for sx, team in ((-1, "red"), (1, "blue")):
        b.landmark(sx * 270.0, 0.0, "the %s windmill" % team)
        for x, z, name in ((82, 118, "the farmhouse"), (82, -118, "the cheese warehouse"),
                           (128, 0, "the drawbridge"), (157, 0, "the dike"),
                           (138, -11, "the sluice"), (203, 100, "the tulips")):
            b.landmark(sx * float(x), float(z), "%s (%s side)" % (name, team))
    b.camera(-150.0, 70.0, 150.0, 0.0, 10.0, 0.0)
    b.camera(150.0, 70.0, -150.0, 0.0, 10.0, 0.0)
    b.camera(0.0, 90.0, -185.0, 0.0, 14.0, 0.0)
