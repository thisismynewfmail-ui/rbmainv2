"""Saddleback Observatory -- twin summits, an observatory on each, the
aurora over them.

The mountain has two tops and a saddle between, and somebody put a
telescope on each top and a cable car up to both.  The flags are kept on
the observing floors, under the telescopes, in the domes; both teams
muster in the cable car's mid-station down in the saddle, under the turning
bullwheel, and the cabins go up and down the cables over everybody's heads.

The mountains are steps of snow you can walk up anywhere -- except where
the rock breaks out in a cliff band, twice on the way to the top, and the
only ways past are the stairs cut at the trails: up the middle and up each
flank.  Or the old service tunnel: from the mountain's foot, under it all,
to a stair that comes up inside the dome.

Layout (red to the west; mirrored about x = 0)::

      z +128  REFUGE (outpost) ......... THE TARN (ice) ........ (and theirs)
      z  +70  trail ..... cliff | cliff ..........................
      z    0  OBSERVATORY (summit, flag) == cable == MID-STATION (relay) == ...
      z  -18  ====== service tunnel: the mountain's foot -> stair inside the dome ======
      z  -70  trail ..... cliff | cliff ..........................
      z -128  SKI SCHOOL (outpost) ...... the weather station, boulders (and a yeti)
"""
from __future__ import annotations

import math
import random

from . import kit
from .kit import (Half, carve, halves, holed_wall, rect, room_walls, slab, strip_light)

HALF = (310.0, 200.0)
SKY = {"top": "#04060f", "horizon": "#1a2a48", "sun": [0.2, 0.6, -0.5],
       "clouds": 0.1, "tint": "#a8c8ff"}
AMBIENT = "#7a8aa8"
GROUND = "#e8eef6"
FOG = 900.0

SNOW = "#eef2f8"
SNOW_SHADE = "#d4dcea"
ROCK = "#5a6070"
ROCK_DARK = "#454a58"
ICE = "#c2e2f2"
CONCRETE = "#c8ccd0"
STEEL = "#9aa0a8"
STEEL_DARK = "#5a6068"
WARM = "#ffd890"

PEAK_X = 262.0
PEAK_R = (150.0, 170.0)
RISES = [2.0, 2.0, 2.0, 8.0, 2.0, 2.0, 2.0, 8.0, 2.0, 2.0, 2.0, 2.0]
SUMMIT = sum(RISES)                     # 36
CLIFFS = (3, 7)
TRAILS_Z = (0.0, 70.0, -70.0)
OBS = (236.0, 288.0, -26.0, 26.0)
OBS_H = 14.0
FLAG_X = 270.0
TUNNEL_Z = (-22.0, -14.0)
TUNNEL_X = (112.0, 240.0)
WELL = (240.0, 258.0, -22.0, -6.0)
STATION = (40.0, 24.0)
STATION_Y = 4.0
STATION_H = 14.0


def _frac(k: int) -> float:
    return 1.0 - k * 0.068


def _edge(k: int, z: float) -> float:
    """Where tier ``k`` of a mountain begins (its distance from the middle
    of the map) in the z band that holds ``z`` -- the same arithmetic as
    kit.ellipse_rects, so a stair can be butted against the cliff."""
    rx, rz = PEAK_R[0] * _frac(k), PEAK_R[1] * _frac(k)
    band = 6.0
    kk = math.floor(z / band)
    mid = abs((kk + 0.5) * band)
    half = rx * math.sqrt(max(0.0, 1.0 - (mid / rz) ** 2))
    half = math.floor(half)
    return PEAK_X - half


def build(b: kit.RelayArea) -> None:
    rng = random.Random(0x5ADD)
    b.relay("the Mid-Station", 46.0)
    b.intro = ["Saddleback Observatory -- twin summits, a telescope on each, the aurora over "
               "them.",
               "Muster in the cable car's mid-station in the saddle; the flags are under the "
               "telescopes in the domes. The cliff bands can only be climbed at the trails.",
               "An old service tunnel runs from each mountain's foot to a stair inside its dome."]
    b.extra.update({"accent": "#7affc8", "weather": "snow"})
    kit.ground(b, SNOW, soil="#8a8a94", material="")
    for h in halves(b):
        _mountain(b, h)
        _tunnel(b, h)
        _trails(b, h)
        _observatory(b, h)
        _outposts(b, h)
        _saddle(b, h)
    _station(b)
    _tarn(b)
    _edge_(b, rng)
    _sky(b)
    _landmarks(b)


# ================================================================ mountains
def _mountain(b: kit.RelayArea, h: Half) -> None:
    """A mountain: ten tiers of snow and rock up to the summit -- two of
    them cliff bands too tall to step -- with the service tunnel cut
    through the lowest three and its stairwell through all of them."""
    cut_tunnel = h.r(TUNNEL_X[0], TUNNEL_X[1], TUNNEL_Z[0], TUNNEL_Z[1])
    cut_well = h.r(WELL[0], WELL[1], WELL[2], WELL[3])
    hx = HALF[0]
    tiers = []
    for k in range(len(RISES)):
        f = _frac(k)
        pieces = []
        cuts = [cut_well] + ([cut_tunnel] if k < 3 else [])
        for r in kit.ellipse_rects(h.x(PEAK_X), 0.0, PEAK_R[0] * f, PEAK_R[1] * f, band=6.0):
            r = (max(r[0], -hx), min(r[1], hx), r[2], r[3])
            if r[1] - r[0] > 1.0:
                pieces.extend(carve(r, cuts))
        tiers.append(pieces)
    colours = [SNOW_SHADE, SNOW, SNOW_SHADE, ROCK, SNOW, SNOW_SHADE, SNOW, ROCK_DARK, SNOW_SHADE,
               SNOW, SNOW_SHADE, SNOW]
    kit.tier_stack(b, tiers, 0.0, RISES, colours, studs=True)
    # rock spires on the flanks: jagged, solid -- cover, and the mountain's
    # skyline
    for x, z, s in ((168.0, 112.0, 1.0), (196.0, -118.0, 1.2), (136.0, -52.0, 0.8),
                    (214.0, 96.0, 0.9)):
        y = b.surface(h.x(x), z, 60.0)
        for k, (w, hh) in enumerate(((8.0, 10.0), (5.6, 7.0), (3.0, 5.0))):
            base = y + sum(dd for _w, dd in ((8.0, 10.0), (5.6, 7.0), (3.0, 5.0))[:k]) * s
            h.box(x + k * 0.8, base + hh * s / 2.0, z - k * 0.6, w * s, hh * s, w * s,
                  ROCK_DARK if k % 2 == 0 else ROCK)
        h.cone(x + 1.6, y + 22.0 * s + 1.2, z - 1.2, 2.6 * s, 2.4, 2.6 * s, SNOW, collide=False)


def _tunnel(b: kit.RelayArea, h: Half) -> None:
    """The service tunnel: a cutting at the mountain's foot becoming a
    tunnel under it, then a stair in two flights up inside the dome."""
    z0, z1 = TUNNEL_Z
    x0, x1 = TUNNEL_X
    zc = (z0 + z1) / 2.0
    for x in range(int(x0) + 40, int(x1) - 4, 24):
        strip_light(b, h.x(float(x)), zc, 6.0, 4.0, "z", "#9fe8ff")
    wx0, wx1, wz0, wz1 = WELL
    mid = SUMMIT / 2.0
    # up the first flight (in the tunnel's band), a landing, back up the second
    h.flight_x(wx0, wx1 - 2.0, z0, z1, 0.0, mid, CONCRETE, fill=0.0)
    h.slab(wx1 - 2.0, wx1, wz0, wz1, mid, mid, CONCRETE, studs=True)
    h.flight_x(wx1 - 2.0, wx0, z1, wz1, mid, SUMMIT, CONCRETE, fill=0.0)
    # its portal at the foot: a concrete frame, a sign
    for z in (z0 - 1.0, z1 + 1.0):
        h.box(x0 + 0.6, 3.0, z, 2.0, 6.0, 1.6, CONCRETE)
    h.box(x0 + 0.4, 6.6, zc, 2.0, 1.2, z1 - z0 + 4.0, CONCRETE)


def _trails(b: kit.RelayArea, h: Half) -> None:
    """The trails: stairs cut up the cliff bands -- up the middle and up each
    flank -- each within one band of the terraces, so it butts square
    against the cliff."""
    for k, bands in ((CLIFFS[0], ((6.0, 12.0), (66.0, 72.0), (-72.0, -66.0))),
                     (CLIFFS[1], ((6.0, 12.0), (36.0, 42.0), (-42.0, -36.0)))):
        lo = sum(RISES[:k])
        hi = lo + RISES[k]
        for zl, zh in bands:
            far = _edge(k, (zl + zh) / 2.0)
            h.flight_x(far - 10.0, far, zl, zh, lo, hi, ROCK, fill=lo)


# ============================================================== observatory
def _observatory(b: kit.RelayArea, h: Half) -> None:
    """The observatory on the summit: a drum of white walls, the observing
    floor inside with the flag under the telescope, the dome on top turning
    (a rig) -- and its slit opening on whatever the telescope follows."""
    x0, x1, z0, z1 = OBS
    y = SUMMIT
    top = y + OBS_H
    area = h.r(x0, x1, z0, z1)
    room_walls(b, area, 2.0, y, top, "#f2f2ee",
               doors={h.inward: [(-6.0, 6.0, y + 9.0)],
                      "z-": [(*h.xs(262.0, 274.0), y + 8.0)], "z+": [(*h.xs(262.0, 274.0), y + 8.0)]})
    slab(b, area, top + 1.2, 1.2, "#c8ccd0", studs=True)
    for z in (z0 - 0.06, z1 + 0.06):
        h.box((x0 + x1) / 2.0, y + 11.0, z, x1 - x0 - 0.2, 1.2, 0.1, h.colour, collide=False)
    b.rig("observatory_dome", h.x((x0 + x1) / 2.0), top + 1.2, 0.0, r=22.0, yaw=h.yaw_in, team=h.team)
    # the observing floor: the telescope's pier, the flag beside it
    h.box(252.0, y + 3.0, 14.0, 4.0, 6.0, 4.0, STEEL_DARK, studs=True)
    top_y = kit.pedestal(b, h.x(FLAG_X), 0.0, y, h.colour, h.neon, base=STEEL_DARK, wide=18.0,
                         top_w=12.0)
    b.flag(h.team, h.x(FLAG_X), top_y, 0.0)
    for xx, zz in ((282.0, 18.0), (282.0, -18.0)):
        h.box(xx, y + 1.6, zz, 4.0, 3.2, 6.0, "#3a3a44", studs=True)
        b.rig("crt", h.x(xx - 2.06), y + 4.4, zz, yaw=h.yaw_in, w=3.0, seed=xx + zz)
    # the stairwell's head inside, railed
    wx0, wx1, wz0, wz1 = WELL
    h.box(wx1 + 0.6, y + 1.5, (wz0 + wz1) / 2.0, 1.2, 3.0, wz1 - wz0, STEEL, material="metal")
    h.box((wx0 + wx1) / 2.0 + 1.0, y + 1.5, wz0 - 0.6, wx1 - wx0 - 2.0, 3.0, 1.2, STEEL,
          material="metal")
    h.box((wx0 + 4.0 + wx1) / 2.0, y + 1.5, wz1 + 0.6, wx1 - wx0 - 4.0, 3.0, 1.2, STEEL,
          material="metal")
    strip_light(b, h.x((x0 + x1) / 2.0), 0.0, top, 40.0, "x", "#ffe8c8")
    kit.banner_mast(b, h.x(x0 - 8.0), 34.0, b.surface(h.x(x0 - 8.0), 34.0, y + 1.0), 22.0, h.team,
                    h.inward)


# ================================================================== outposts
def _outposts(b: kit.RelayArea, h: Half) -> None:
    """The refuge (north) and the ski school (south) down in the saddle:
    where a team falls back to while its flag is out."""
    kit.outpost_room(h, 80.0, 120.0, 110.0, 146.0, 0.0, "#7a4e2e", "#4a5060", height=11.0,
                     door_w=12.0, pads=2, lights=WARM)
    kit.gable(b, h.r(80.0, 120.0, 110.0, 146.0), 12.2, SNOW, along="x", tiers=3, rise=2.0)
    h.box(100.0, 8.6, 110.0 - 0.36, 12.0, 2.4, 0.7, "#c42b20", collide=False,
          r=[0.0, math.pi, 0.0], decal=kit.sign_decal("REFUGE", "#c42b20", "#ffffff", 5.0))
    kit.outpost_room(h, 80.0, 120.0, -146.0, -110.0, 0.0, "#e8e0d0", "#4a5060", height=11.0,
                     door_w=12.0, pads=2, lights=WARM)
    kit.gable(b, h.r(80.0, 120.0, -146.0, -110.0), 12.2, SNOW, along="x", tiers=3, rise=2.0)
    h.box(100.0, 8.6, -110.0 + 0.36, 12.0, 2.4, 0.7, "#2a6aa8", collide=False,
          decal=kit.sign_decal("SKI SCHOOL", "#2a6aa8", "#ffffff", 5.0))
    for k in range(3):
        h.box(124.6, 4.0, -120.0 + k * 3.0, 0.6, 8.0, 0.6, ["#c42b20", "#2a6aa8", "#f2c21e"][k])


def _saddle(b: kit.RelayArea, h: Half) -> None:
    """The saddle: drifts and boulders, a weather station, a frozen-in
    snowcat, the yeti's rock."""
    for x, z, rx, rz in ((60.0, 60.0, 16.0, 10.0), (70.0, -70.0, 18.0, 12.0)):
        kit.mound(b, h.x(x), z, rx, rz, 2, 2.0, [SNOW_SHADE, SNOW], band=4.0)
    for x, z, s in ((50.0, -100.0, 1.8), (90.0, 40.0, 1.3), (40.0, 150.0, 1.5)):
        kit.boulder(b, h.x(x), z, 0.0, s, ROCK)
    h.box(60.0, 2.4, -40.0, 12.0, 4.8, 6.0, "#e8a020", studs=True)
    h.box(56.0, 5.6, -40.0, 5.0, 2.4, 5.6, "#3a4a5a")
    # the weather station: a mast, its anemometer spinning
    h.box(96.0, 6.0, -90.0, 0.8, 12.0, 0.8, STEEL, material="metal")
    b.rig("anemometer", h.x(96.0), 12.4, -90.0, seed=h.sx)
    # a skier down the south flank: the path sampled off the snow itself, so
    # they hop down the steps and fly off the cliff bands
    path = []
    for k in range(15):
        u = k / 14.0
        x, z = (PEAK_X - 34.0) + (128.0 - (PEAK_X - 34.0)) * u, -30.0 + (-110.0 + 30.0) * u
        path.append(b.at(h.x(x), b.surface(h.x(x), z, 60.0), z))
    b.rig("skier", h.x(PEAK_X - 34.0), SUMMIT, -30.0, path=path, seed=h.sx, c=h.colour)


# ================================================================== station
def _station(b: kit.RelayArea) -> None:
    """The mid-station in the saddle, on its little knoll: the halls either
    side of the cable hall, the bullwheel turning on the roof, the cables
    going up to both summits with the cabins on them."""
    kit.mound(b, 0.0, 0.0, 70.0, 46.0, 2, 2.0, [SNOW_SHADE, SNOW], band=4.0, shrink=0.85)
    y = STATION_Y
    hx, hz = STATION
    area = rect(-hx, hx, -hz, hz)
    room_walls(b, area, 3.0, y, y + STATION_H, CONCRETE,
               doors={"x-": [(-7.0, 7.0, y + 10.0)], "x+": [(-7.0, 7.0, y + 10.0)],
                      "z-": [(-5.0, 5.0, y + 9.0)], "z+": [(-5.0, 5.0, y + 9.0)]})
    for sx in (-1, 1):
        holed_wall(b, "z", sx * 13.0, 2.0, -hz + 3.0, hz - 3.0, y, y + STATION_H, STEEL_DARK,
                   holes=[(-6.0, 6.0, y - 1.0, y + 9.0)])
    top = y + STATION_H + 1.2
    slab(b, area, top, 1.2, "#4a5060", studs=True)
    # the bullwheel on the roof, turning; a cabin parked in the hall
    b.box([0.0, top + 2.0, 0.0], [4.0, 4.0, 4.0], STEEL_DARK, studs=True)
    b.rig("bullwheel", 0.0, top + 4.4, 0.0, r=9.0)
    b.box([0.0, y + 2.0, 0.0], [8.0, 4.0, 6.0], "#c42b20", studs=True)
    b.box([0.0, y + 5.0, 0.0], [8.4, 2.0, 6.4], "#e8e8e0", collide=False)
    strip_light(b, 0.0, 0.0, y + STATION_H, 40.0, "z", WARM)
    for h in halves(b):
        for i in range(3):
            for j in (-1, 1):
                b.muster(h.team, h.x(17.0 + 5.0 * i), y, j * 13.0, h.yaw_out, size=4.4)
        h.sign(hx - 3.36, y + 10.0, 0.0, 10.0, 3.0, "sign_%s" % h.team, "x+")
        strip_light(b, h.x(25.0), 0.0, y + STATION_H, 40.0, "z", WARM)
        # the cable up to this side's summit, a cabin on it, the towers it
        # runs over (solid: their feet are cover)
        b.rig("cable_car", 0.0, top + 4.4, 0.0, q=[h.x(OBS[0] - 6.0), SUMMIT + OBS_H + 4.0, 0.0],
              seed=h.sx, c=h.colour)
        for k, x in enumerate((96.0, 168.0)):
            ground = b.surface(h.x(x), 8.0, 60.0)
            tower_h = (top + 4.4) + (SUMMIT + OBS_H + 4.0 - top - 4.4) * (x - 0.0) / (OBS[0] - 6.0) - ground - 3.0
            h.box(x, ground + tower_h / 2.0, 8.0, 2.0, tower_h, 2.0, STEEL, material="metal")
            h.box(x, ground + tower_h / 2.0, -8.0, 2.0, tower_h, 2.0, STEEL, material="metal")
            h.box(x, ground + tower_h + 0.6, 0.0, 2.4, 1.2, 20.0, STEEL_DARK, material="metal")
        h.box(hx + 7.0, y + 2.0, -14.0, 6.0, 4.0, 6.0, STEEL_DARK, studs=True)
        h.box(hx + 7.0, y + 1.6, 14.0, 5.0, 3.2, 5.0, "#5a6070", studs=True)


def _tarn(b: kit.RelayArea) -> None:
    """The tarn north of the station: frozen over, its ice to run on."""
    slab(b, rect(-46.0, 46.0, 84.0, 140.0), 0.4, 0.4, ICE, material="glass", alpha=0.9)
    for sx in (-1, 1):
        kit.boulder(b, sx * 50.0, 150.0, 0.0, 1.4, ROCK)


def _edge_(b: kit.RelayArea, rng: random.Random) -> None:
    """The ridge falling away all round, the range beyond."""
    hx, hz, m = HALF[0], HALF[1], b.margin
    room_walls(b, rect(-hx - m, hx + m, -hz - m, hz + m), m, 0.0, SUMMIT + 12.0, ROCK_DARK,
               studs=True)
    kit.backdrop(b, "peaks", SUMMIT + 12.0, rng, colours=["#c8d0e0", "#a8b4c8", "#e0e8f4"],
                 sides=("x-", "x+", "z-", "z+"), depth=60.0)


def _sky(b: kit.RelayArea) -> None:
    """The aurora, the stars, the moon -- and the yeti."""
    b.rig("aurora", 0.0, 210.0, 60.0, w=700.0, n=5)
    b.rig("starfield", 0.0, 0.0, 0.0, r=640.0, n=120, seed=11)
    b.rig("moon", 420.0, 260.0, -380.0, r=40.0)
    b.rig("yeti", -50.0, 0.0, -100.0, yaw=0.6)
    for h in halves(b):
        b.rig("snow_plume", h.x(PEAK_X), SUMMIT + OBS_H + 6.0, 0.0, seed=h.sx)


def _landmarks(b: kit.RelayArea) -> None:
    for x, z, name in ((0, 0, "the mid-station"), (0, 112, "the tarn")):
        b.landmark(float(x), float(z), name)
    for sx, team in ((-1, "red"), (1, "blue")):
        b.landmark(sx * 262.0, 0.0, "the %s observatory" % team)
        for x, z, name in ((100, 128, "the refuge"), (100, -128, "the ski school"),
                           (150, 7, "the middle trail"), (150, 70, "the north trail"),
                           (150, -70, "the south trail"), (112, -18, "the service tunnel")):
            b.landmark(sx * float(x), float(z), "%s (%s side)" % (name, team))
    b.camera(-150.0, 70.0, 150.0, 0.0, 10.0, 0.0)
    b.camera(150.0, 70.0, -150.0, 0.0, 10.0, 0.0)
    b.camera(0.0, 90.0, -185.0, 0.0, 14.0, 0.0)
