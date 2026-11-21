"""The Orrery -- a clockwork arboretum at twilight.

A Victorian pleasure garden built round a brass orrery the size of a
church.  The lawns step down in terraces to the sunken plaza in the middle,
where the orrery's clockhouse stands under its sun: both teams muster in
it, and its roof, with a planet on a deck at each corner, is the high
ground everybody wants.  The flags are kept in the two glasshouses at the
ends of the garden, among the palms.

Layout (red to the west; mirrored about x = 0)::

      z +200  ============= the garden wall, the observatory beyond ===========
      z +110  TOPIARY .... GAZEBO (outpost) .... HEDGE WALK ...... TOPIARY
      z  +52  .......... planet decks over the plaza (north pair) ..........
      z    0  GLASSHOUSE -- garden -- terraces -- CLOCKHOUSE (relay) -- ...
      z  -30  ======= the gear tunnel: boiler room -> plaza stairs =========
      z  -52  .......... planet decks (south pair) .........................
      z -110  ROSE BEDS .... BANDSTAND (outpost) .... SUNDIAL ......
      z -200  =====================================================

Three terraces of two step down to the plaza from the garden level (6);
the gear tunnel runs under all of them, seven below the plaza, from a
stair in each glasshouse's boiler room to one in the plaza.
"""
from __future__ import annotations

import math
import random

from . import kit
from .kit import (Half, carve, flight, halves, holed_wall, rect, room_walls, slab,
                  strip_light)

HALF = (316.0, 200.0)
SKY = {"top": "#2a2458", "horizon": "#e08a7a", "sun": [-0.4, 0.12, 0.6],
       "clouds": 0.35, "tint": "#ffc8a8"}
AMBIENT = "#8a7a98"
GROUND = "#4a8a4a"
FOG = 820.0

LAWN = "#4a8a4a"
LAWN_LIGHT = "#5a9a52"
LAWN_DARK = "#3e7a40"
GRAVEL = "#c8bca0"
STONE = "#d8d0c0"
STONE_DARK = "#a8a090"
BRASS = "#c89a3a"
BRASS_DARK = "#8a6a28"
IRON = "#e8ece8"
GLASSY = "#bfe8e0"
HEDGE = "#2f6a36"
HEDGE_DARK = "#265a2c"
GAS = "#ffd890"

GARDEN = 6.0
RINGS = [(-80.0, 80.0, -70.0, 70.0), (-120.0, 120.0, -110.0, 110.0),
         (-160.0, 160.0, -150.0, 150.0)]       # the plaza and the two steps out of it
HOUSE = (32.0, 28.0)                            # the clockhouse's half sizes
ROOF = 15.4
GLASS = (226.0, 290.0, -50.0, 50.0)             # a glasshouse (magnitudes)
ANNEX = (290.0, 314.0, -44.0, -16.0)            # its boiler room
TUNNEL_Z = (-38.0, -26.0)
TUNNEL_FLOOR = -7.0
PLAZA_STAIR = (60.0, 84.0)                      # the tunnel's plaza end (magnitudes)
ANNEX_STAIR = (292.0, 312.0)
FLAG_X = 260.0


def build(b: kit.RelayArea) -> None:
    rng = random.Random(0x0EE7)
    b.relay("the Clockhouse", 48.0)
    b.intro = ["The Orrery -- a clockwork garden at twilight.",
               "Muster in the clockhouse under the brass sun; the flags are in the "
               "glasshouses at either end of the garden.",
               "A gear tunnel runs from each glasshouse's boiler room to the plaza."]
    b.extra.update({"accent": "#e8b860", "weather": "motes"})
    holes, wells = [], []
    for h in halves(b):
        holes.append(h.r(PLAZA_STAIR[0], ANNEX_STAIR[1], TUNNEL_Z[0], TUNNEL_Z[1]))
        wells.append(h.r(PLAZA_STAIR[0], PLAZA_STAIR[1], TUNNEL_Z[0], TUNNEL_Z[1]))
        wells.append(h.r(ANNEX_STAIR[0], ANNEX_STAIR[1], TUNNEL_Z[0], TUNNEL_Z[1]))
    kit.ground(b, LAWN, soil="#5a4a32", holes=holes)
    _terraces(b, wells)
    for h in halves(b):
        _tunnel(b, h)
    _clockhouse(b)
    _orrery(b)
    for h in halves(b):
        _glasshouse(b, h)
        _garden(b, h, random.Random(0x6A7D))
        _outposts(b, h)
    _edge(b, rng)
    _landmarks(b)


# ================================================================= terraces
def _terraces(b: kit.RelayArea, holes) -> None:
    """The bowl: three steps of two up from the plaza to the garden."""
    hx, hz = HALF
    whole = rect(-hx, hx, -hz, hz)
    tiers = []
    colours = [STONE_DARK, LAWN_LIGHT, LAWN]
    for ring in RINGS:
        tiers.append(carve(whole, [ring] + list(holes)))
    kit.tier_stack(b, tiers, 0.0, [2.0], colours, studs=True)
    # gravel paths across each step at the cardinal points, a step of stone
    for k, ring in enumerate(RINGS):
        y = 2.0 * (k + 1)
        for sz in (-1, 1):
            b.box([0.0, y + 0.04, sz * (ring[3] + 6.0)], [16.0, 0.08, 12.0], GRAVEL, collide=False)
    # urns on the corners of the first step
    for sx in (-1, 1):
        for sz in (-1, 1):
            x, z = sx * (RINGS[0][1] + 6.0), sz * (RINGS[0][3] + 6.0)
            b.cyl([x, 2.0 + 1.5, z], [4.0, 3.0, 4.0], STONE)
            b.cyl([x, 2.0 + 4.0, z], [5.0, 2.0, 5.0], STONE_DARK)
            b.sphere([x, 2.0 + 6.5, z], [5.0, 4.0, 5.0], "#c84a6a", collide=False)


# ================================================================== tunnel
def _tunnel(b: kit.RelayArea, h: Half) -> None:
    """The gear tunnel: the orrery's drive shaft runs down it, gears turn
    in the walls, and it comes up in the plaza and the boiler room."""
    z0, z1 = TUNNEL_Z
    area = h.r(PLAZA_STAIR[0], ANNEX_STAIR[1], z0, z1)
    kit.channel(b, area, -TUNNEL_FLOOR, "#5a5048", wall_c="#4a4038", studs=True)
    # the plaza's stair, up towards the clockhouse
    h.flight_x(PLAZA_STAIR[1], PLAZA_STAIR[0], z0, z1, TUNNEL_FLOOR, 0.0, STONE, fill=TUNNEL_FLOOR)
    # a low iron rail each side of the open stairwell in the plaza
    for z in (z0 - 0.5, z1 + 0.5):
        h.box((PLAZA_STAIR[0] + 80.0) / 2.0, 1.6, z, 80.0 - PLAZA_STAIR[0], 3.2, 1.0, IRON,
              material="metal")
    # the boiler room's stair, down from the annex floor
    h.flight_x(ANNEX_STAIR[1], ANNEX_STAIR[0], z0, z1, GARDEN, TUNNEL_FLOOR, STONE_DARK,
               fill=TUNNEL_FLOOR)
    # the shaft and the gears, lit by the odd lamp in the ceiling
    shaft_y = TUNNEL_FLOOR + 6.0
    for x in range(96, 280, 24):
        h.box(float(x), shaft_y, z0 + 1.2, 18.0, 1.2, 1.2, BRASS_DARK, material="metal")
        h.cyl(float(x) + 9.0, shaft_y, z0 + 0.9, 5.0, 0.6, 5.0, BRASS, material="metal",
              r=[math.pi / 2.0, 0.0, 0.0], collide=False)
        strip_light(b, h.x(float(x)), (z0 + z1) / 2.0, 0.0, 6.0, "x", GAS)


# =============================================================== clockhouse
def _clockhouse(b: kit.RelayArea) -> None:
    """The orrery's clockhouse: a muster hall each side, the gear room
    between them, and its roof the base of the orrery."""
    hx, hz = HOUSE
    area = rect(-hx, hx, -hz, hz)
    top = ROOF - 1.4
    room_walls(b, area, 3.0, 0.0, top, STONE,
               doors={"x-": [(-7.0, 7.0, 10.0)], "x+": [(-7.0, 7.0, 10.0)],
                      "z-": [(-4.0, 4.0, 9.0)], "z+": [(-4.0, 4.0, 9.0)]})
    for sx in (-1, 1):
        holed_wall(b, "z", sx * 12.0, 2.0, -hz + 3.0, hz - 3.0, 0.0, top, STONE_DARK,
                   holes=[(-6.0, 6.0, -1.0, 9.0)])
    slab(b, area, ROOF, 1.4, BRASS_DARK, studs=True)
    room_walls(b, area, 1.0, ROOF, ROOF + 3.0, BRASS,
               doors={"z+": [(-14.0, -6.0, ROOF + 3.0), (6.0, 14.0, ROOF + 3.0),
                             (-28.0, -20.0, ROOF + 3.0), (20.0, 28.0, ROOF + 3.0)],
                      "z-": [(-14.0, -6.0, ROOF + 3.0), (6.0, 14.0, ROOF + 3.0),
                             (-28.0, -20.0, ROOF + 3.0), (20.0, 28.0, ROOF + 3.0)]},
               material="metal")
    for sx in (-1, 1):
        for sz in (-1, 1):
            flight(b, "z", sz * (hz + 24.0), sz * hz, *sorted((sx * 6.0, sx * 14.0)), 0.0,
                   ROOF, STONE_DARK, fill=0.0)
    # the gear room: a great wheel on the back wall, a pendulum
    for sz in (-1, 1):
        b.cyl([0.0, 7.0, sz * (hz - 3.6)], [14.0, 1.2, 14.0], BRASS, material="metal",
              r=[math.pi / 2.0, 0.0, 0.0], collide=False)
    b.cyl([0.0, top - 4.0, 0.0], [0.5, 8.0, 0.5], BRASS_DARK, collide=False)
    b.sphere([0.0, top - 8.6, 0.0], [2.4, 2.4, 2.4], BRASS, collide=False, material="metal")
    strip_light(b, 0.0, 0.0, top, 40.0, "z", GAS)
    for h in halves(b):
        for i in range(3):
            for j in (-1, 1):
                b.muster(h.team, h.x(16.0 + 4.5 * i), 0.0, j * 14.0, h.yaw_out, size=4.2)
        h.sign(hx - 3.36, 11.0, 0.0, 10.0, 3.0, "sign_%s" % h.team, "x+")
        strip_light(b, h.x(22.0), 0.0, top, 40.0, "z", GAS)
        h.box(hx + 7.0, 2.5, -15.0, 7.0, 5.0, 7.0, STONE_DARK, studs=True)
        h.box(hx + 7.0, 2.0, 15.0, 6.0, 4.0, 6.0, BRASS_DARK, studs=True, material="metal")


def _orrery(b: kit.RelayArea) -> None:
    """The orrery over the clockhouse: the sun on its column, and a planet
    on a deck at each corner, bridged to the roof."""
    b.cyl([0.0, ROOF + 18.0, 0.0], [8.0, 36.0, 8.0], BRASS_DARK, material="metal")
    b.sphere([0.0, ROOF + 44.0, 0.0], [26.0, 26.0, 26.0], "#ffb84a", material="neon",
             collide=False)
    b.cyl([0.0, ROOF + 44.0, 0.0], [44.0, 0.6, 44.0], BRASS, material="metal",
          collide=False, r=[0.25, 0.0, 0.1])
    # the armillary bands the sun is held in
    b.box([0.0, ROOF + 44.0, 0.0], [30.0, 1.2, 1.2], BRASS, material="metal", collide=False)
    b.box([0.0, ROOF + 44.0, 0.0], [1.2, 1.2, 30.0], BRASS, material="metal", collide=False)
    b.box([0.0, ROOF + 44.0, 0.0], [1.0, 30.0, 1.0], BRASS, material="metal", collide=False)
    planets = [("#4a7ad8", 7.0), ("#d86a3a", 6.0)]
    for sx in (-1, 1):
        for k, sz in enumerate((1, -1)):
            x, z = sx * 24.0, sz * 52.0
            deck = rect(x - 9.0, x + 9.0, z - 9.0, z + 9.0)
            slab(b, deck, ROOF, 1.4, BRASS_DARK, studs=True)
            # the deck stands on a brass column
            b.cyl([x, (ROOF - 1.4) / 2.0, z], [4.0, ROOF - 1.4, 4.0], BRASS, material="metal")
            colour, size = planets[k]
            b.sphere([x, ROOF + size * 0.39, z], [size, size, size], colour)
            if k == 1:
                b.cyl([x, ROOF + size * 0.39, z], [size * 2.0, 0.3, size * 2.0], "#e8d8a8",
                      collide=False, r=[0.3, 0.0, 0.0])
            # the bridge to the roof: an arm of the orrery
            bridge = rect(min(x - 4.0 * sx, x + 4.0 * sx), max(x - 4.0 * sx, x + 4.0 * sx),
                          min(sz * HOUSE[1], z - sz * 9.0), max(sz * HOUSE[1], z - sz * 9.0))
            slab(b, bridge, ROOF, 1.0, BRASS, studs=True, material="metal")
            # its rails
            for dx in (-4.4, 4.4):
                b.box([x + dx, ROOF + 1.2, (bridge[2] + bridge[3]) / 2.0],
                      [0.8, 2.4, bridge[3] - bridge[2]], BRASS_DARK, material="metal")


# ================================================================ glasshouse
def _glasshouse(b: kit.RelayArea, h: Half) -> None:
    """A glasshouse at the team's end: iron frames, glass you can see
    through and not walk through, palms, a fountain, the flag in the
    middle -- and the boiler room out the back."""
    x0, x1, z0, z1 = GLASS
    y = GARDEN
    top = y + 20.0
    area = h.r(x0, x1, z0, z1)
    t = 1.0
    doors = {h.inward: [(-8.0, 8.0, y + 11.0)],
             "z-": [(*h.xs(250.0, 262.0), y + 10.0)], "z+": [(*h.xs(250.0, 262.0), y + 10.0)],
             h.outward: [(-25.0, -19.0, y + 9.0)]}
    room_walls(b, area, t, y, top, GLASSY, doors=doors, material="glass", alpha=0.36)
    # the iron frame: posts every ten, a beam round the top
    for x in range(int(x0), int(x1) + 1, 8):
        for z in (z0, z1):
            if abs(x - 256) < 9:
                continue
            h.box(float(x), y + (top - y) / 2.0, z + (0.0 if True else 0.0), 1.2, top - y, 1.6, IRON,
                  material="metal")
    for z in range(int(z0) + 10, int(z1), 10):
        if abs(z) < 10:
            continue
        for x in (x0, x1):
            if x == x1 and -28 < z < -16:
                continue
            h.box(x, y + (top - y) / 2.0, float(z), 1.6, top - y, 1.2, IRON, material="metal")
    # the roof: a glass ridge over an iron grid
    kit.tier_stack(b, [[area], [h.r(x0 + 8.0, x1 - 8.0, z0 + 10.0, z1 - 10.0)],
                       [h.r(x0 + 16.0, x1 - 16.0, z0 + 20.0, z1 - 20.0)]], top,
                   [1.0, 4.0, 4.0], [IRON, GLASSY, GLASSY], studs=False, material="glass")
    strip_light(b, h.x((x0 + x1) / 2.0), 0.0, top, 70.0, "z", GAS)
    top_y = kit.pedestal(b, h.x(FLAG_X), 0.0, y, h.colour, h.neon, base=STONE_DARK)
    b.flag(h.team, h.x(FLAG_X), top_y, 0.0)
    kit.banner_mast(b, h.x(282.0), 62.0, y, 30.0, h.team, h.inward)
    # palms in their beds, a fountain by the door
    for x, z in ((238.0, -34.0), (238.0, 34.0), (278.0, 36.0), (276.0, -8.0)):
        h.box(x, y + 1.0, z, 8.0, 2.0, 8.0, "#8a5a3a", studs=True)
        h.cyl(x, y + 2.0 + 7.0, z, 1.6, 14.0, 1.6, "#8a6a4a")
        for k in range(5):
            a = k * 2 * math.pi / 5
            h.box(x + math.cos(a) * 3.0, y + 16.0, z + math.sin(a) * 3.0, 6.0, 0.6, 2.4,
                  "#3a8a3a", collide=False, r=[0.0, a, 0.3])
    h.cyl(240.0, y + 1.0, 0.0, 10.0, 2.0, 10.0, STONE)
    h.cyl(240.0, y + 2.04, 0.0, 8.0, 0.1, 8.0, "#5ab8c8", collide=False, material="glass",
          alpha=0.7)
    h.cyl(240.0, y + 3.5, 0.0, 1.6, 3.0, 1.6, STONE_DARK)
    # the boiler room, brick, with the tunnel stair in it
    ax0, ax1, az0, az1 = ANNEX
    aarea = h.r(ax0, ax1, az0, az1)
    room_walls(b, aarea, 2.0, y, y + 12.0, "#8a4a3a",
               doors={h.inward: [(-25.0, -19.0, y + 9.0)]})
    slab(b, aarea, y + 13.2, 1.2, "#6a3a2a", studs=True)
    h.cyl(ax1 - 6.0, y + 16.0, az1 - 4.0, 3.0, 8.0, 3.0, "#5a3a2a")
    h.box(ax0 + 6.0, y + 3.0, az1 - 3.5, 6.0, 6.0, 3.0, "#3a3a3a", material="metal")
    strip_light(b, h.x((ax0 + ax1) / 2.0), (az0 + az1) / 2.0, y + 12.0, 14.0, "x", "#ff9a5a")


# =================================================================== garden
def _garden(b: kit.RelayArea, h: Half, rng: random.Random) -> None:
    """Topiary, hedge walks, gas lamps and flower beds on the garden level,
    and the long lawn down the middle to the glasshouse door."""
    y = GARDEN
    # topiary: spheres and cones on stems, cover for anyone standing by one
    for x, z, kind in ((182.0, 160.0, "ball"), (214.0, 120.0, "cone"), (196.0, -170.0, "cone"),
                       (176.0, -168.0, "ball"), (208.0, 70.0, "ball"), (204.0, -74.0, "cone")):
        h.box(x, y + 1.0, z, 6.0, 2.0, 6.0, STONE_DARK, studs=True)
        if kind == "ball":
            h.sphere(x, y + 7.0, z, 10.0, 10.0, 10.0, HEDGE)
        else:
            h.cone(x, y + 8.0, z, 10.0, 12.0, 10.0, HEDGE)
    # the hedge walk: a hedge run with gaps, north and south
    for z in (178.0, -186.0):
        for xa, xb in ((170.0, 200.0), (212.0, 250.0), (262.0, 300.0)):
            h.box((xa + xb) / 2.0, y + 3.5, z, xb - xa, 7.0, 6.0, HEDGE_DARK, studs=True)
    # rose beds, low enough to step onto
    for x, z in ((236.0, 84.0), (270.0, 84.0), (236.0, -84.0), (270.0, -84.0)):
        h.box(x, y + 0.8, z, 20.0, 1.6, 10.0, "#6a4a2a", studs=True)
        for k in range(5):
            h.sphere(x - 8.0 + k * 4.0, y + 2.6, z + (k % 2) * 2.0 - 1.0, 3.0, 2.6, 3.0,
                     ["#d82a4a", "#f2f2f2", "#e86a8a"][k % 3], collide=False)
    # gas lamps along the lawn to the glasshouse door
    for x in (176.0, 200.0, 224.0):
        for z in (-16.0, 16.0):
            kit.lamp_post(b, h.x(x), z, y, 11.0, GAS, "#2a2a2a")
    # benches facing the lawn
    for x in (188.0, 212.0):
        kit.bench(b, h.x(x), 24.0, along="x", y=y)
        kit.bench(b, h.x(x), -24.0, along="x", y=y)
    # in the bowl: a sundial (south) and a lily basin (north), on the steps
    h.cyl(100.0, 2.0 + 1.2, -96.0, 6.0, 2.4, 6.0, STONE)
    h.box(100.0, 2.0 + 3.4, -96.0, 1.0, 2.0, 4.0, BRASS, material="metal", collide=False)
    h.cyl(100.0, 2.0 + 0.8, 96.0, 12.0, 1.6, 12.0, STONE)
    h.cyl(100.0, 2.0 + 1.64, 96.0, 10.0, 0.1, 10.0, "#4a8aa8", collide=False, material="glass",
          alpha=0.7)
    del rng


# ================================================================== outposts
def _outposts(b: kit.RelayArea, h: Half) -> None:
    """The gazebo (north) and the bandstand (south) on the garden level:
    where a team falls back to while its flag is out."""
    y = GARDEN
    for sz, name in ((1, "gazebo"), (-1, "bandstand")):
        zlo, zhi = sorted((sz * 96.0, sz * 140.0))
        kit.outpost_room(h, 166.0, 206.0, zlo, zhi, y, "#e8e0d0", "#4a6a5a", height=11.0,
                         door_w=12.0, pads=2, lights=GAS)
        # a pointed roof over the flat one, for the look of it
        area = h.r(166.0, 206.0, zlo, zhi)
        kit.gable(b, area, y + 11.0 + 1.2, "#3a5a4a", along="x", tiers=3, rise=1.4)
        del name


# ===================================================================== edge
def _edge(b: kit.RelayArea, rng: random.Random) -> None:
    """The garden wall, brick with stone coping, and the twilight beyond:
    an observatory dome to the north, poplars all round."""
    hx, hz, m = HALF[0], HALF[1], b.margin
    room_walls(b, rect(-hx - m, hx + m, -hz - m, hz + m), m, 0.0, 30.0, "#8a5a4a")
    for sx in (-1, 1):
        b.box([sx * (hx + m / 2.0), 31.0, 0.0], [m + 2.0, 2.0, 2 * (hz + m) - 4.0], STONE,
              collide=False)
    for sz in (-1, 1):
        b.box([0.0, 31.0, sz * (hz + m / 2.0)], [2 * hx - 4.0, 2.0, m + 2.0], STONE,
              collide=False)
    kit.backdrop(b, "pines", 30.0, rng, colours=["#1f3a2a", "#23402e", "#1a3224"],
                 sides=("x-", "x+", "z-"), depth=50.0)
    b.box([0.0, 40.0, hz + m + 40.0], [70.0, 80.0, 60.0], "#c8c0b0", collide=False)
    b.sphere([0.0, 80.0, hz + m + 40.0], [62.0, 56.0, 56.0], "#e8e4dc", collide=False)
    b.box([0.0, 92.0, hz + m + 12.0], [8.0, 30.0, 0.6], "#1a1a2a", collide=False)


def _landmarks(b: kit.RelayArea) -> None:
    for x, z, name in ((0, 0, "the Clockhouse"), (0, 52, "the north planets"),
                       (0, -52, "the south planets"), (0, 100, "the lily basin")):
        b.landmark(float(x), float(z), name)
    for sx, team in ((-1, "red"), (1, "blue")):
        b.landmark(sx * 258.0, 0.0, "the %s glasshouse" % team)
        for x, z, name in ((186, 118, "the gazebo"), (186, -118, "the bandstand"),
                           (72, -32, "the tunnel stairs"), (302, -30, "the boiler room")):
            b.landmark(sx * float(x), float(z), "%s (%s side)" % (name, team))
    b.camera(-140.0, 60.0, 150.0, 0.0, 10.0, 0.0)
    b.camera(150.0, 50.0, -140.0, 0.0, 12.0, 0.0)
    b.camera(0.0, 70.0, -180.0, 0.0, 14.0, 0.0)
