"""Steamworks Caldera -- a geothermal power station in a volcano, at dusk.

The volcano went quiet a long time ago, but not cold: the caldera holds a
lake of steaming turquoise water, the rock steps down to it in black benches
with the glow still in their cracks, and the steam comes up through
everything.  Somebody built a power station in it.  The turbine hall
stands on an island in the lake -- both teams muster there, beside the
spinning turbines -- and the flags are kept up on the rim at either end,
in the wellhead stations, among the valves.  The steam pipes come down
from the wellheads to the hall on trestles high over the benches and the
lake, with a catwalk along the top: the fast way across, and the most
exposed thing in the crater.

Layout (red to the west; mirrored about x = 0)::

      z +180  CONTROL HUT (outpost)    COOLING TOWER    (and theirs)
      z  +50  rim .... benches .... ~~~ lake: footbridge, geysers ~~~
      z    0  WELLHEAD (flag) ===== the pipe bridge (y 16) ===== TURBINE HALL (island)
      z  -15  ===== steam tunnel: beside the flag -> the cut in the shore benches =====
      z  -50  ......................... ~~~ lake: stepping stones ~~~
      z -180  PUMP HOUSE (outpost)     COOLING TOWER

The benches rise from the lake shore to the rim in eight strides; the
steam tunnel is a cutting into the lowest three that becomes a tunnel
under the rest, and a stair up beside the flag.
"""
from __future__ import annotations

import math
import random

from . import kit
from .kit import (Half, carve, halves, holed_wall, rect, room_walls, slab, strip_light)

HALF = (310.0, 206.0)
SKY = {"top": "#2a2a4a", "horizon": "#e87a5a", "sun": [-0.5, 0.12, 0.4],
       "clouds": 0.45, "tint": "#ffb890"}
AMBIENT = "#ab9ca4"
GROUND = "#3a3a40"
FOG = 820.0

ROCK = ["#5a5560", "#4a4550", "#6a6470", "#524c58", "#6e6874", "#463f4a", "#625a68",
        "#544e5a"]
LAVA = "#ff6a2a"
STEEL = "#9aa0a8"
STEEL_DARK = "#5a6068"
PIPE = "#c8ccd0"
WATER = "#3ac8c8"
SAFETY = "#f2c21e"

RIM_Y = 16.0
LAKE = (90.0, 70.0)
LAKE_DEPTH = 3.0
ISLAND = (46.0, 32.0)
RINGS = [(LAKE[0] + 14.0 * k, LAKE[1] + 12.0 * k) for k in range(8)]
HALL = (40.0, 26.0)
HALL_H = 14.0
TUNNEL_Z = (-20.0, -10.0)
TUNNEL_X = (104.0, 256.0)
SHAFT = (256.0, 272.0)
WELL = (240.0, 296.0, -32.0, 32.0)
FLAG_X = 282.0
BRIDGE_Y = 16.0


def build(b: kit.RelayArea) -> None:
    rng = random.Random(0x57EA)
    b.relay("the Turbine Hall", 46.0)
    b.intro = ["Steamworks Caldera -- a geothermal power station in a volcano, at dusk.",
               "Muster in the turbine hall on the island; the flags are up on the rim in the "
               "wellhead stations. The pipe bridges cross high over everything -- in full view.",
               "A steam tunnel runs from beside each flag to a cut in the shore benches."]
    b.extra.update({"accent": "#ff9a5a", "weather": "steam"})
    lake = carve(rect(-LAKE[0], LAKE[0], -LAKE[1], LAKE[1]),
                 [rect(-ISLAND[0], ISLAND[0], -ISLAND[1], ISLAND[1])])
    kit.ground(b, ROCK[0], soil="#2a2a2e", holes=lake, material="")
    _lake(b, lake)
    _benches(b)
    for h in halves(b):
        _wellhead(b, h)
        _bridge(b, h)
        _outposts(b, h)
        _rim(b, h)
        _shore(b, h)
    _hall(b)
    _towers(b)
    _edge(b, rng)
    _landmarks(b)


# ===================================================================== lake
def _lake(b: kit.RelayArea, lake) -> None:
    """The hot lake round the island: three deep, steaming, geysers in it,
    a footbridge north, stepping stones south."""
    for piece in lake:
        kit.channel(b, piece, LAKE_DEPTH, "#2a5a5a", studs=True)
        kit.water_sheet(b, piece, -0.8, WATER, 0.55)
    # the footbridge across the north water
    slab(b, rect(-5.0, 5.0, ISLAND[1], LAKE[1]), 0.8, 0.8, STEEL_DARK, studs=True)
    for sx in (-1, 1):
        b.box([sx * 5.3, 2.0, (ISLAND[1] + LAKE[1]) / 2.0], [0.6, 2.4, LAKE[1] - ISLAND[1]], SAFETY,
              material="metal")
    # stepping stones across the south water, a stride apart
    for z in (-38.0, -46.0, -54.0, -62.0):
        b.cyl([0.0, -LAKE_DEPTH / 2.0 + 0.2, z], [6.0, LAKE_DEPTH + 0.4, 6.0], ROCK[2], studs=True)
    # geysers in the lake: they gurgle, then go up
    for k, (x, z) in enumerate(((-66.0, 40.0), (66.0, 40.0), (-60.0, -50.0), (60.0, -50.0))):
        b.box([x, -LAKE_DEPTH + 0.6, z], [6.0, 1.2, 6.0], "#5a5a50", studs=True)
        b.rig("geyser", x, -LAKE_DEPTH + 1.2, z, h=34.0, every=29.0, seed=k * 7.3)


def _benches(b: kit.RelayArea) -> None:
    """The caldera's benches: eight strides of black rock from the shore up
    to the rim, the glow still in the cracks; the steam tunnels cut through
    the lowest three, the shaft stairs through them all."""
    hx, hz = HALF
    whole = rect(-hx, hx, -hz, hz)
    cuts, shafts = [], []
    for h in halves(b):
        cuts.append(h.r(TUNNEL_X[0], TUNNEL_X[1], TUNNEL_Z[0], TUNNEL_Z[1]))
        shafts.append(h.r(SHAFT[0], SHAFT[1], TUNNEL_Z[0], TUNNEL_Z[1]))
    tiers = []
    for k, (rx, rz) in enumerate(RINGS):
        tiers.append(carve(whole, [rect(-rx, rx, -rz, rz)] + shafts + (cuts if k < 3 else [])))
    kit.tier_stack(b, tiers, 0.0, [2.0], ROCK, studs=True)
    # the glow in the cracks: strips along the risers, pulsing (a rig)
    for k in (1, 3, 5):
        rx, rz = RINGS[k]
        for sz in (-1, 1):
            b.rig("lava_crack", 0.0, 2.0 * k + 1.0, sz * (rz - 0.05), w=rx * 1.6, yaw=0.0 if sz < 0 else math.pi,
                  seed=k + sz)


# ================================================================ wellheads
def _wellhead(b: kit.RelayArea, h: Half) -> None:
    """The wellhead station on the rim: a steel shed over the well, the
    valve trees standing in it, the flag among them, the shaft stair down
    to the steam tunnel beside it -- and the pipes going out to the bridge."""
    x0, x1, z0, z1 = WELL
    y = RIM_Y
    top = y + 14.0
    area = h.r(x0, x1, z0, z1)
    room_walls(b, area, 2.0, y, top, STEEL, material="metal",
               doors={h.inward: [(-6.0, 6.0, y + 9.0)],
                      "z-": [(*h.xs(276.0, 286.0), y + 8.0)], "z+": [(*h.xs(256.0, 266.0), y + 8.0)],
                      h.outward: [(10.0, 18.0, y + 8.0)]})
    slab(b, h.r(x0 - 1.0, x1 + 1.0, z0 - 1.0, z1 + 1.0), top + 1.2, 1.2, STEEL_DARK, studs=True)
    for z in (z0 - 0.06, z1 + 0.06):
        h.box((x0 + x1) / 2.0, y + 11.6, z, x1 - x0 - 0.2, 1.2, 0.1, h.colour, collide=False)
    # the valve trees: stacks of flanges and wheels (cover round the flag)
    for xx, zz in ((256.0, 18.0), (272.0, 22.0), (292.0, -22.0)):
        h.cyl(xx, y + 3.0, zz, 3.0, 6.0, 3.0, "#c84a2a", material="metal")
        h.cyl(xx, y + 6.6, zz, 4.0, 1.2, 4.0, STEEL_DARK, material="metal")
        h.cyl(xx, y + 7.4, zz, 3.4, 0.4, 3.4, SAFETY, collide=False)
        b.rig("pressure_gauge", h.x(xx), y + 4.6, zz + 1.6, r=1.0, seed=xx)
    # the shaft stair beside the flag, railed
    sx0, sx1 = SHAFT
    tz0, tz1 = TUNNEL_Z
    h.flight_x(sx0, sx1, tz0, tz1, 0.0, y, STEEL_DARK, fill=0.0)
    h.box(sx0 - 0.6, y + 1.5, (tz0 + tz1) / 2.0, 1.2, 3.0, tz1 - tz0, SAFETY, material="metal")
    h.box((sx0 + sx1) / 2.0 - 0.6, y + 1.5, tz1 + 0.6, sx1 - sx0 - 1.2, 3.0, 1.2, SAFETY,
          material="metal")
    h.box((sx0 + sx1) / 2.0 - 0.6, y + 1.5, tz0 - 0.6, sx1 - sx0 - 1.2, 3.0, 1.2, SAFETY,
          material="metal")
    top_y = kit.pedestal(b, h.x(FLAG_X), 0.0, y, h.colour, h.neon, base=STEEL_DARK, wide=18.0,
                         top_w=12.0)
    b.flag(h.team, h.x(FLAG_X), top_y, 0.0)
    strip_light(b, h.x((x0 + x1) / 2.0), 0.0, top, 44.0, "x", "#ffd8a0")
    kit.banner_mast(b, h.x(x0 - 10.0), 46.0, y, 24.0, h.team, h.inward)
    # a steam vent outside, roaring
    h.box(226.0, y + 1.0, -48.0, 4.0, 2.0, 4.0, "#5a5a50", studs=True)
    b.rig("steam", h.x(226.0), y + 2.2, -48.0, n=8, c="#eef0f2", team=h.team)


# ==================================================================== bridge
def _bridge(b: kit.RelayArea, h: Half) -> None:
    """The pipe bridge: the two big steam pipes from the wellhead to the
    hall, on steel trestles over the benches and the lake, a catwalk with
    rails along the top -- level with the rim and the hall's roof."""
    x0, x1 = HALL[0], RINGS[-1][0]
    y = BRIDGE_Y
    h.slab(x0, x1, -3.0, 3.0, y, 0.8, STEEL_DARK, studs=True)
    for z in (-3.3, 3.3):
        h.box((x0 + x1) / 2.0, y + 1.2, z, x1 - x0, 2.4, 0.6, SAFETY, material="metal")
    # the pipes, under the walk (decoration: you walk on the grating)
    for z in (-1.8, 1.8):
        h.cyl((x0 + x1) / 2.0 + 1.0, y - 1.6, z, 2.4, x1 - x0 + 2.0, 2.4, PIPE, collide=False,
              material="metal", r=[0.0, 0.0, math.pi / 2.0])
    # trestles down to whatever is under them
    for x in range(int(x0) + 12, int(x1), 24):
        # (over the lake, down to its bed: surface() never looks below 0)
        if ISLAND[0] < x < LAKE[0]:
            ground = -LAKE_DEPTH
        else:
            ground = b.surface(h.x(float(x)), 0.0, y - 2.0)
        hgt = y - 0.8 - ground
        for z in (-2.6, 2.6):
            h.box(float(x), ground + hgt / 2.0, z, 1.2, hgt, 1.2, STEEL_DARK, material="metal")
        b.rig("steam", h.x(float(x) + 6.0), y - 1.0, 0.0, n=3, c="#f4f6f8")


# ================================================================== outposts
def _outposts(b: kit.RelayArea, h: Half) -> None:
    """The control hut (north) and the pump house (south), up on the rim:
    where a team falls back to while its flag is out."""
    y = RIM_Y
    kit.outpost_room(h, 110.0, 160.0, 166.0, 198.0, y, "#c8c8c0", STEEL_DARK, height=11.0,
                     door_w=12.0, pads=2, lights="#ffd8a0")
    h.box(135.0, y + 8.6, 166.0 - 0.36, 16.0, 2.4, 0.7, SAFETY, collide=False,
          r=[0.0, math.pi, 0.0], decal=kit.sign_decal("CONTROL", SAFETY, "#2a2a30", 6.7))
    kit.outpost_room(h, 110.0, 160.0, -198.0, -166.0, y, "#8a5a3a", STEEL_DARK, height=11.0,
                     door_w=12.0, pads=2, lights="#ffd8a0")
    h.box(135.0, y + 8.6, -166.0 + 0.36, 16.0, 2.4, 0.7, SAFETY, collide=False,
          decal=kit.sign_decal("PUMP HOUSE", SAFETY, "#2a2a30", 6.7))
    for k in range(3):
        h.cyl(170.0, y + 2.0, -176.0 - k * 7.0, 5.0, 4.0, 5.0, "#3a6aa8", material="metal")


def _rim(b: kit.RelayArea, h: Half) -> None:
    """The rim near the wellhead: scoria mounds, a transformer yard with
    its pylon, warning signs."""
    y = RIM_Y
    for x, z, rx, rz in ((210.0, -110.0, 18.0, 16.0), (260.0, 110.0, 22.0, 18.0),
                         (212.0, 140.0, 12.0, 10.0)):
        kit.mound(b, h.x(x), z, rx, rz, 3, 2.0, ROCK[2:5], band=4.0, y0=y)
    for k in range(3):
        h.box(232.0 + k * 9.0, y + 3.0, 78.0, 6.0, 6.0, 5.0, "#6a7078", studs=True)
    for dx in (-2.0, 2.0):
        for dz in (-2.0, 2.0):
            h.box(250.0 + dx, y + 14.0, 92.0 + dz, 0.6, 28.0, 0.6, STEEL, material="metal")
    b.rig("blinker", h.x(250.0), y + 28.6, 92.0, c="#ff3020", period=1.5, seed=h.sx)
    h.box(200.0, y + 2.5, 20.0, 6.0, 4.0, 0.6, SAFETY,
          decal=kit.sign_decal("DANGER STEAM", SAFETY, "#2a2a30", 1.5))


def _shore(b: kit.RelayArea, h: Half) -> None:
    """The lake shore and the benches above it: a jetty, mud pots, a wrecked
    survey buggy, the pipeline's valve house."""
    # a jetty out over the water
    h.slab(76.0, LAKE[0], 44.0, 50.0, 0.6, 0.6, "#6a5a4a", studs=True)
    for x, z in ((100.0, -40.0), (110.0, 36.0)):
        b.rig("steam", h.x(x), b.surface(h.x(x), z, 20.0) + 0.2, z, n=4, c="#e8ecee")
    h.car(122.0, -60.0, "x", "#c86a2a", y=b.surface(h.x(122.0), -60.0, 20.0), wrecked=True)


# ============================================================= turbine hall
def _hall(b: kit.RelayArea) -> None:
    """The turbine hall on its island: a muster hall each end, the turbine
    floor between with its two machines spinning, glazing high up, a
    railed roof the pipe bridges come in level with."""
    hx, hz = HALL
    area = rect(-hx, hx, -hz, hz)
    room_walls(b, area, 3.0, 0.0, HALL_H, "#b8bcc0",
               doors={"x-": [(-7.0, 7.0, 10.0)], "x+": [(-7.0, 7.0, 10.0)],
                      "z-": [(-5.0, 5.0, 9.0)], "z+": [(-5.0, 5.0, 9.0)]},
               material="metal")
    for sx in (-1, 1):
        holed_wall(b, "z", sx * 14.0, 2.0, -hz + 3.0, hz - 3.0, 0.0, HALL_H, STEEL_DARK,
                   holes=[(-6.0, 6.0, -1.0, 9.0)])
    slab(b, area, HALL_H + 1.2, 1.2, STEEL_DARK, studs=True)
    kit.rails(b, area, HALL_H + 1.2, h=2.4, c=SAFETY, t=0.6,
              gaps={"x-": [(-3.0, 3.0)], "x+": [(-3.0, 3.0)]})
    # the turbines: low casings (cover), the rotors spinning in them
    for z in (-12.0, 12.0):
        b.box([0.0, 2.2, z], [22.0, 4.4, 6.0], "#2a6a8a", studs=True)
        b.rig("turbine", 0.0, 4.4, z, len=22.0, r=2.6, seed=z)
    b.box([0.0, 1.4, 0.0], [6.0, 2.8, 4.0], "#3a3a40", studs=True)
    b.rig("pressure_gauge", 0.0, 4.0, 2.06, r=1.4, seed=1.0, whistle=True)
    for sx in (-1, 1):
        b.box([sx * 20.0, 12.0, hz - 3.06], [10.0, 3.0, 0.1], "#ffd8a0", material="neon",
              collide=False)
    strip_light(b, 0.0, 0.0, HALL_H, 40.0, "z", "#ffd8a0")
    for h in halves(b):
        for i in range(3):
            for j in (-1, 1):
                b.muster(h.team, h.x(18.0 + 5.0 * i), 0.0, j * 13.0, h.yaw_out, size=4.4)
        h.sign(hx - 3.36, 11.0, 0.0, 10.0, 3.0, "sign_%s" % h.team, "x+")
        strip_light(b, h.x(27.0), 0.0, HALL_H, 40.0, "z", "#ffd8a0")
        h.box(hx + 3.0, 2.0, -16.0, 4.0, 4.0, 6.0, STEEL_DARK, studs=True)
        h.box(hx + 3.0, 1.6, 16.0, 4.0, 3.2, 5.0, "#5a5a60", studs=True)


def _towers(b: kit.RelayArea) -> None:
    """The cooling towers on the north and south rim: great waisted
    concrete funnels, plumes rolling out of them."""
    y = RIM_Y
    for sz in (-1, 1):
        z = sz * 182.0
        for k in range(10):
            f = k / 9.0
            r = 22.0 - 10.0 * math.sin(f * math.pi * 0.85)
            b.cyl([0.0, y + 2.4 + k * 4.4, z], [r * 2.0, 4.4, r * 2.0], "#c8c4bc" if k % 3 else "#b8b4ac")
        b.rig("cooling_plume", 0.0, y + 46.0, z, r=16.0, seed=sz)
        b.rig("gulls", 0.0, y + 60.0, z, n=5, r=30.0, c="#1e1e24")


def _edge(b: kit.RelayArea, rng: random.Random) -> None:
    """The crater's lip all round, the volcano's flanks beyond."""
    hx, hz, m = HALF[0], HALF[1], b.margin
    room_walls(b, rect(-hx - m, hx + m, -hz - m, hz + m), m, 0.0, RIM_Y + 12.0, ROCK[1],
               studs=True)
    kit.backdrop(b, "peaks", RIM_Y + 12.0, rng, colours=["#3a3440", "#2a2632", "#46404c"],
                 sides=("x-", "x+", "z-", "z+"), depth=60.0)


def _landmarks(b: kit.RelayArea) -> None:
    for x, z, name in ((0, 0, "the turbine hall"), (0, 182, "the north tower"),
                       (0, -182, "the south tower"), (0, 52, "the footbridge"),
                       (0, -50, "the stepping stones")):
        b.landmark(float(x), float(z), name)
    for sx, team in ((-1, "red"), (1, "blue")):
        b.landmark(sx * 268.0, 0.0, "the %s wellhead" % team)
        for x, z, name in ((135, 182, "the control hut"), (135, -182, "the pump house"),
                           (120, 0, "the pipe bridge"), (104, -15, "the steam tunnel")):
            b.landmark(sx * float(x), float(z), "%s (%s side)" % (name, team))
    b.camera(-150.0, 70.0, 150.0, 0.0, 10.0, 0.0)
    b.camera(150.0, 70.0, -150.0, 0.0, 10.0, 0.0)
    b.camera(0.0, 90.0, -190.0, 0.0, 14.0, 0.0)
