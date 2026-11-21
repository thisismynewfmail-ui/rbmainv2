"""Saltglass Flats -- a dry lake of salt at night, under a lightning storm.

Nothing grows out here, and nothing stops the lightning: the salt is
studded with fulgurites, glass the bolts made of it, and the old power
company's lightning rods still stand in rows.  Both teams muster in
Capacitor Hall in the middle of the pan, under its two Tesla coils.  The
flags are in the salt works on the mesas at either end.

Layout (red to the west; mirrored about x = 0)::

      z +190  ..................... THE DRAGLINE (cab, boom) ...................
      z +120  ======== the north wash: a dry channel, salt arches over it ========
      z  +70  FULGURITES      PUMP SHED (outpost)           LIGHTNING RODS
      z    0  MESA / SALT WORKS ---- the pan ---- CAPACITOR HALL ---- ...
      z  -70  FULGURITES      PUMP SHED (outpost)           LIGHTNING RODS
      z -120  ======== the south wash ===========================================
      z -160  ................... the S.S. OPTIMIST, high and dry ...............

The washes are the runner's roads: seven down, under arches of crust,
from the foot of one mesa to the foot of the other, with a way in at the
middle.  The mesas step up in threes to the salt works on top.
"""
from __future__ import annotations

import math
import random

from . import kit
from .kit import (CONCRETE, CONCRETE_DARK, STEEL, STEEL_DARK, Half, flight, halves,
                  holed_wall, rect, room_walls, slab, strip_light)

HALF = (322.0, 196.0)
SKY = {"top": "#120e24", "horizon": "#4a3a5a", "sun": [0.2, 0.4, 0.7],
       "clouds": 0.9, "tint": "#b8a8e8"}
AMBIENT = "#6a6488"
GROUND = "#e2ddd2"
FOG = 700.0

SALT = "#e2ddd2"
SALT_DARK = "#c8c2b4"
SALT_LIGHT = "#f0ece4"
CRACK = "#a8a294"
MESA = "#c8b8a0"
MESA_DARK = "#b0a088"
WASH = "#b8ae9a"
GLASSY = "#7ad8e8"
COIL = "#c87a3a"
ARC = "#bfe8ff"

WASH_Z = (110.0, 130.0)          # the north wash (the south one is its mirror in z)
WASH_X = 262.0
WASH_DEPTH = 7.0
HALL = (50.0, 30.0)
HALL_ROOF = 15.4
MESA_X = (210.0, 322.0)
WORKS = (250.0, 306.0, -36.0, 36.0)
FLAG_X = 278.0
RODS = ((120.0, 40.0), (120.0, -40.0), (164.0, 0.0), (90.0, 76.0), (90.0, -76.0))
FULGURITES = ((206.0, 104.0), (186.0, -66.0), (70.0, 36.0), (200.0, 40.0), (66.0, -40.0))
HOODOOS = ((290.0, 150.0), (176.0, 176.0), (60.0, -176.0), (290.0, -128.0), (196.0, 142.0),
           (150.0, -178.0))
SPEED_Z = (-106.0, -98.0)       # the land-speed course, painted across the pan


def build(b: kit.RelayArea) -> None:
    rng = random.Random(0x5A17)
    b.relay("Capacitor Hall", 60.0)
    b.intro = ["Saltglass Flats -- a dry salt lake, and a storm with nothing to hit.",
               "Muster in Capacitor Hall; the flags are in the salt works up on the mesas.",
               "The dry washes north and south run from mesa to mesa, under the salt."]
    b.extra.update({"accent": "#9fe8ff", "weather": "storm"})
    washes = [rect(-WASH_X, WASH_X, WASH_Z[0], WASH_Z[1]),
              rect(-WASH_X, WASH_X, -WASH_Z[1], -WASH_Z[0])]
    kit.ground(b, SALT, soil="#9a9080", holes=washes, material="")
    for wash in washes:
        _wash(b, wash)
    _hall(b)
    _dragline(b)
    _boat(b)
    for h in halves(b):
        _mesa(b, h)
        _works(b, h)
        _field(b, h)
        _outposts(b, h)
    _speedway(b)
    _hall_yard(b)
    for h in halves(b):
        _power_line(b, h)
        _hoodoos(b, h)
        _machines(b, h)
        _works_detail(b, h)
        _rod_scorch(b, h)
    _wash_detail(b)
    _mirages(b)
    _crust(b, random.Random(0xC20))
    _edge(b, rng)
    _landmarks(b)


# ================================================================== washes
def _wash(b: kit.RelayArea, area) -> None:
    """A dry wash: a channel seven down, its bed cracked, salt arches over
    it, stairs at its ends and a way down in the middle."""
    kit.channel(b, area, WASH_DEPTH, WASH, wall_c="#8a8070", studs=True)
    x0, x1, z0, z1 = area
    zc = (z0 + z1) / 2.0
    north = zc > 0
    # arches: slabs of crust over the wash, high enough to walk under
    for x in (-180.0, -84.0, 84.0, 180.0):
        slab(b, rect(x - 7.0, x + 7.0, z0, z1), 0.0, 1.0, SALT_DARK, studs=True)
        b.box([x, -1.6, z0 + 0.6], [10.0, 1.2, 1.2], SALT_DARK)
        b.box([x, -1.6, z1 - 0.6], [10.0, 1.2, 1.2], SALT_DARK)
    for sx in (-1, 1):
        # the end stairs, up to the pan at the foot of each mesa
        flight(b, "x", sx * (x1 - 22.0), sx * x1, z0, z1, -WASH_DEPTH, 0.0, MESA_DARK,
               fill=-WASH_DEPTH)
        # a way down in the middle, along the side away from the hall
        side = (z1 - 6.0, z1) if north else (z0, z0 + 6.0)
        flight(b, "x", sx * 46.0, sx * 22.0, side[0], side[1], -1.8, -WASH_DEPTH, MESA_DARK,
               fill=-WASH_DEPTH)
    # cracks across the bed, and the odd dead shrub
    for k in range(9):
        x = -220.0 + k * 55.0
        b.box([x, -WASH_DEPTH + 0.04, zc], [1.2, 0.08, z1 - z0 - 2.0], CRACK, collide=False)
    for x in (-130.0, 130.0):
        b.cyl([x, -WASH_DEPTH + 1.0, zc + (3.0 if north else -3.0)], [3.0, 2.0, 3.0],
              "#6a5a40")


# ==================================================================== hall
def _hall(b: kit.RelayArea) -> None:
    """Capacitor Hall: two muster bays and the switch room between them, two
    Tesla coils on the roof with the storm crawling between them."""
    hx, hz = HALL
    area = rect(-hx, hx, -hz, hz)
    top = HALL_ROOF - 1.4
    room_walls(b, area, 3.0, 0.0, top, "#5a5e68",
               doors={"x-": [(-7.0, 7.0, 10.0)], "x+": [(-7.0, 7.0, 10.0)],
                      "z-": [(-6.0, 6.0, 9.0)], "z+": [(-6.0, 6.0, 9.0)]})
    for sx in (-1, 1):
        holed_wall(b, "z", sx * 18.0, 2.0, -hz + 3.0, hz - 3.0, 0.0, top, "#4a4e58",
                   holes=[(-6.0, 6.0, -1.0, 9.0)])
    slab(b, area, HALL_ROOF, 1.4, CONCRETE_DARK, studs=True)
    room_walls(b, area, 1.0, HALL_ROOF, HALL_ROOF + 3.0, "#4a4e58",
               doors={"z+": [(-40.0, -30.0, HALL_ROOF + 3.0), (30.0, 40.0, HALL_ROOF + 3.0)],
                      "z-": [(-40.0, -30.0, HALL_ROOF + 3.0), (30.0, 40.0, HALL_ROOF + 3.0)]})
    for sx in (-1, 1):
        for sz in (-1, 1):
            flight(b, "z", sz * (hz + 24.0), sz * hz, *sorted((sx * 30.0, sx * 40.0)), 0.0,
                   HALL_ROOF, CONCRETE, fill=0.0)
    # the coils
    for sx in (-1, 1):
        x = sx * 20.0
        b.box([x, HALL_ROOF + 2.0, 0.0], [12.0, 4.0, 12.0], STEEL_DARK, material="metal",
              studs=True)
        b.cyl([x, HALL_ROOF + 4.0 + 11.0, 0.0], [6.0, 22.0, 6.0], COIL, material="metal")
        for k in range(6):
            b.cyl([x, HALL_ROOF + 6.0 + k * 3.4, 0.0], [6.6, 0.6, 6.6], "#e8a85a",
                  material="metal", collide=False)
        b.cyl([x, HALL_ROOF + 27.0, 0.0], [16.0, 3.4, 16.0], "#c8ccd2", material="metal",
              collide=False)
        b.sphere([x, HALL_ROOF + 29.0, 0.0], [4.0, 4.0, 4.0], ARC, material="neon",
                 collide=False)
    # the arc between them, crawling along the cable strung from cap to cap
    b.box([0.0, HALL_ROOF + 27.0 + 1.6, 0.0], [40.0, 0.2, 0.2], "#3a3e46", collide=False)
    b.box([0.0, HALL_ROOF + 29.0, 0.0], [36.0, 0.6, 0.6], ARC, material="neon", collide=False)
    # inside: the switch room's knife switches and gauges
    b.box([0.0, 5.0, hz - 4.5], [26.0, 10.0, 3.0], "#2a2e36", material="metal")
    for i in range(5):
        b.box([-10.0 + i * 5.0, 7.0, hz - 6.05], [1.0, 3.4, 0.1], "#e8e0c8", collide=False)
        b.cyl([-10.0 + i * 5.0, 3.5, hz - 6.05], [2.2, 0.1, 2.2], "#ffe8a0", material="neon",
              collide=False, r=[math.pi / 2.0, 0.0, 0.0])
    strip_light(b, 0.0, 0.0, top, 40.0, "z", ARC)
    for h in halves(b):
        for i in range(3):
            for j in (-1, 1):
                b.muster(h.team, h.x(23.0 + 7.0 * i), 0.0, j * 15.0, h.yaw_out, size=5.6)
        h.sign(hx - 3.36, 11.4, 0.0, 12.0, 3.4, "sign_%s" % h.team, "x+")
        strip_light(b, h.x(34.0), 0.0, top, 46.0, "z", "#ffe2a8")
        h.box(hx + 7.0, 2.4, -16.0, 8.0, 4.8, 8.0, h.dark, studs=True)
        h.box(hx + 7.0, 2.0, 16.0, 8.0, 4.0, 8.0, SALT_DARK, studs=True)
    kit.board_letters(b, 0.0, top - 3.0, hz, "CAPACITOR HALL", 2.6, "#2a2e36", ARC, solid=False)
    kit.board_letters(b, 0.0, top - 3.0, -hz, "CAPACITOR HALL", 2.6, "#2a2e36", ARC,
                      facing="z-", solid=False)


# =================================================================== mesas
def _mesa(b: kit.RelayArea, h: Half) -> None:
    """The mesa at the team's end: three steps of salt rock up to the works."""
    x0, x1 = MESA_X
    kit.tier_stack(b, [[h.r(x0, x1, -92.0, 92.0)], [h.r(x0 + 9.0, x1, -84.0, 84.0)],
                       [h.r(x0 + 18.0, x1, -76.0, 76.0)]], 0.0, [2.0],
                   [MESA_DARK, MESA, MESA_DARK], studs=True)
    # boulders of rock salt on the steps
    for x, z, s in ((216.0, 60.0, 1.4), (222.0, -40.0, 1.2), (214.0, -80.0, 1.6)):
        kit.boulder(b, h.x(x), z, 0.0, s, "#d8d0c0")


def _works(b: kit.RelayArea, h: Half) -> None:
    """The salt works on the mesa: the evaporation shed (the flag inside),
    stockpiles of salt, a conveyor gantry and the brine pans."""
    x0, x1, z0, z1 = WORKS
    y = 6.0
    top = y + 16.0
    area = h.r(x0, x1, z0, z1)
    room_walls(b, area, 3.0, y, top, "#8a8e96",
               doors={h.inward: [(-9.0, 9.0, y + 11.0)],
                      "z-": [(*h.xs(270.0, 286.0), y + 10.0)], "z+": [(*h.xs(270.0, 286.0), y + 10.0)],
                      h.outward: [(-6.0, 6.0, y + 9.0)]})
    kit.tier_stack(b, [[area], [h.r(x0 + 4.0, x1 - 4.0, z0 + 6.0, z1 - 6.0)],
                       [h.r(x0 + 8.0, x1 - 8.0, z0 + 12.0, z1 - 12.0)]], top, [1.4, 2.0, 2.0],
                   ["#6a6e76", "#7a7e86", "#6a6e76"], studs=True)
    strip_light(b, h.x(FLAG_X), 0.0, top, 50.0, "z", "#ffe2a8")
    top_y = kit.pedestal(b, h.x(FLAG_X), 0.0, y, h.colour, h.neon, base=CONCRETE_DARK)
    b.flag(h.team, h.x(FLAG_X), top_y, 0.0)
    kit.banner_mast(b, h.x(x1 - 6.0), 44.0, y, 30.0, h.team, h.inward)
    # inside: salt bins along the walls
    for z in (-26.0, 26.0):
        h.box(262.0, y + 2.5, z, 10.0, 5.0, 6.0, SALT_LIGHT, studs=True)
    # stockpiles: cones of salt, solid
    for x, z in ((240.0, 56.0), (240.0, -56.0)):
        h.cone(x, y + 9.0, z, 22.0, 18.0, 22.0, SALT_LIGHT)
    # the conveyor up to the north pile, on legs, overhead
    for k in range(3):
        h.box(256.0 - k * 6.0, y + 6.0 + k * 1.5, 46.0, 1.0, 12.0 + k * 3.0, 1.0, STEEL)
    h.box(250.0, y + 13.5, 46.0, 22.0, 1.2, 3.0, "#3a3e46", material="metal", collide=False,
          r=[0.0, 0.0, 0.0])
    # brine pans behind the shed, a step down, pink with algae
    for z in (-60.0, 60.0):
        h.box(300.0, y + 0.6, z, 26.0, 1.2, 20.0, "#d8d0c0", studs=True)
        h.box(300.0, y + 1.24, z, 22.0, 0.08, 16.0, "#e8a8b8", collide=False, material="glass",
              alpha=0.8)


# =================================================================== field
def _field(b: kit.RelayArea, h: Half) -> None:
    """The pan between the mesas and the hall: rows of lightning rods,
    fulgurite clusters, a weather mast."""
    for x, z in RODS:
        h.box(x, 1.0, z, 6.0, 2.0, 6.0, CONCRETE, studs=True)
        h.cyl(x, 2.0 + 18.0, z, 1.2, 36.0, 1.2, STEEL, material="metal")
        h.cyl(x, 38.5, z, 0.6, 3.0, 0.6, "#d8e2e8", material="metal", collide=False)
        h.sphere(x, 40.2, z, 1.2, 1.2, 1.2, ARC, material="neon", collide=False)
    rng = random.Random(0xF06)
    for cx, cz in FULGURITES:
        for k in range(5):
            dx, dz = rng.uniform(-6.0, 6.0), rng.uniform(-6.0, 6.0)
            hgt = rng.uniform(6.0, 18.0)
            w = rng.uniform(1.6, 3.0)
            h.box(cx + dx, hgt / 2.0, cz + dz, w, hgt, w * 0.8, GLASSY, material="glass",
                  alpha=0.72)
    # the weather mast by the hall: anemometer and all
    h.box(78.0, 1.0, 0.0, 5.0, 2.0, 5.0, CONCRETE, studs=True)
    h.cyl(78.0, 2.0 + 12.0, 0.0, 1.0, 24.0, 1.0, STEEL_DARK, material="metal")
    for a in range(3):
        ang = a * 2.0 * math.pi / 3.0
        h.box(78.0 + math.cos(ang) * 1.6, 26.1, math.sin(ang) * 1.6, 3.2, 0.3, 0.3, STEEL,
              collide=False, r=[0.0, ang, 0.0])


# ================================================================ outposts
def _outposts(b: kit.RelayArea, h: Half) -> None:
    """The brine pump sheds out on the pan: where a team falls back to
    while its flag is out."""
    for sz in (-1, 1):
        zlo, zhi = sorted((sz * 58.0, sz * 96.0))
        kit.outpost_room(h, 138.0, 180.0, zlo, zhi, 0.0, "#9a8a7a", CONCRETE_DARK,
                         height=11.0, door_w=12.0, pads=2)
        h.cyl(174.0, 12.2 + 3.0, sz * 64.0, 3.0, 6.0, 3.0, STEEL_DARK, material="metal")
        h.box(176.0, 2.0, sz * 92.0, 4.0, 4.0, 6.0, "#4a6a8a",
              material="metal", studs=True)


# =================================================================== crust
def _crust(b: kit.RelayArea, rng: random.Random) -> None:
    """Plates of salt crust heaved up across the pan -- a step or a knee
    high -- and the cracks between them."""
    keep = [rect(-HALL[0] - 30.0, HALL[0] + 30.0, -HALL[1] - 30.0, HALL[1] + 30.0),
            rect(-WASH_X - 8.0, WASH_X + 8.0, WASH_Z[0] - 8.0, WASH_Z[1] + 8.0),
            rect(-WASH_X - 8.0, WASH_X + 8.0, -WASH_Z[1] - 8.0, -WASH_Z[0] + 8.0),
            rect(-40.0, 40.0, 140.0, 196.0), rect(-30.0, 30.0, -182.0, -138.0),
            rect(-210.0, 210.0, -112.0, -94.0), rect(-10.0, 10.0, -96.0, -58.0),
            rect(-30.0, 30.0, 32.0, 50.0), rect(-30.0, 30.0, -50.0, -32.0),
            rect(-WASH_X, WASH_X, 136.0, 148.0), rect(-WASH_X, WASH_X, -148.0, -136.0)]
    for sx in (-1, 1):
        keep.append(rect(min(sx * 200.0, sx * 322.0), max(sx * 200.0, sx * 322.0), -100.0, 100.0))
        for x, z in RODS + ((78.0, 0.0),):
            keep.append(rect(sx * x - 6.0, sx * x + 6.0, z - 6.0, z + 6.0))
        for cx, cz in FULGURITES:
            keep.append(rect(sx * cx - 10.0, sx * cx + 10.0, cz - 10.0, cz + 10.0))
        keep.append(rect(min(sx * 136.0, sx * 182.0), max(sx * 136.0, sx * 182.0), -98.0, -56.0))
        keep.append(rect(min(sx * 136.0, sx * 182.0), max(sx * 136.0, sx * 182.0), 56.0, 98.0))
        keep.append(rect(min(sx * 94.0, sx * 114.0), max(sx * 94.0, sx * 114.0), -94.0, -76.0))
        for x, z in HOODOOS:
            keep.append(rect(sx * x - 9.0, sx * x + 9.0, z - 9.0, z + 9.0))
        for x, z in ((236.0, 156.0), (236.0, -156.0), (120.0, 168.0)):
            keep.append(rect(sx * x - 18.0, sx * x + 18.0, z - 14.0, z + 14.0))
    placed = []
    tries = 0
    while len(placed) < 26 and tries < 900:
        tries += 1
        w, d = rng.uniform(14.0, 34.0), rng.uniform(12.0, 28.0)
        x, z = rng.uniform(20.0, 196.0), rng.uniform(-186.0, 186.0)
        r = rect(x - w / 2.0, x + w / 2.0, z - d / 2.0, z + d / 2.0)
        mr = rect(-r[1], -r[0], r[2], r[3])
        if any(k[0] < r[1] + 4 and k[1] > r[0] - 4 and k[2] < r[3] + 4 and k[3] > r[2] - 4
               for k in keep + placed):
            continue
        if any(k[0] < mr[1] + 4 and k[1] > mr[0] - 4 and k[2] < mr[3] + 4 and k[3] > mr[2] - 4
               for k in keep + placed):
            continue
        hgt = rng.choice((0.6, 1.2, 1.8))
        colour = rng.choice((SALT_LIGHT, SALT, SALT_DARK))
        for rr in (r, mr):
            slab(b, rr, hgt, hgt, colour, studs=True)
            placed.append(rr)
    # cracks: hairlines on the open pan
    for k in range(14):
        x, z = rng.uniform(16.0, 190.0), rng.uniform(-90.0, 90.0)
        ln = rng.uniform(10.0, 26.0)
        r = rect(x - ln / 2.0, x + ln / 2.0, z - 0.4, z + 0.4)
        if any(k2[0] < r[1] and k2[1] > r[0] and k2[2] < r[3] and k2[3] > r[2] for k2 in keep + placed):
            continue
        for sx in (-1, 1):
            b.box([sx * x, 0.03, z], [ln, 0.06, 0.8], CRACK, collide=False)


# =========================================================== the dragline
def _dragline(b: kit.RelayArea) -> None:
    """A dead dragline excavator north of the washes: climb to its cab roof
    for the longest view on the pan."""
    y = 0.0
    b.cyl([0.0, y + 2.0, 172.0], [40.0, 4.0, 40.0], "#4a4e56", material="metal")
    b.box([0.0, y + 4.0 + 7.0, 172.0], [44.0, 14.0, 26.0], "#d8a83a", material="metal")
    b.box([0.0, y + 18.0 + 0.6, 172.0], [36.0, 1.2, 22.0], "#b8882a", material="metal",
          studs=True)
    for sx in (-1, 1):
        flight(b, "z", 146.0, 159.0, *sorted((sx * 14.0, sx * 22.0)), 0.0, y + 19.2,
               STEEL_DARK, fill=0.0)
    b.box([0.0, y + 19.2 + 4.0, 168.0], [12.0, 8.0, 10.0], "#2a3038", material="metal")
    b.box([0.0, y + 22.0, 162.9], [10.0, 3.0, 0.2], "#9fd8e8", collide=False, material="glass",
          alpha=0.6)
    # the boom, swung out over the pan, its bucket hanging from it (scenery)
    b.box([40.0, y + 40.0, 176.0], [92.0, 3.0, 3.0], "#d8a83a", material="metal",
          collide=False, r=[0.0, 0.0, 0.42])
    b.box([80.0, y + 30.0, 176.0], [0.4, 30.0, 0.4], "#2a2a2a", collide=False)
    b.box([80.0, y + 13.0, 176.0], [10.0, 6.0, 8.0], "#6a5a3a", material="metal", collide=False)
    letters_y = y + 11.0
    kit.board_letters(b, 0.0, letters_y, 159.0, "PAN-AM SALT CO", 2.4, "#d8a83a", "#3a2a1a",
                      facing="z-", solid=False)


def _boat(b: kit.RelayArea) -> None:
    """The S.S. Optimist: a rowing boat on the salt, miles from any water."""
    z = -160.0
    b.box([0.0, 1.6, z], [8.0, 3.2, 20.0], "#e8e0d0")
    b.box([0.0, 1.6, z + 11.0], [5.0, 3.2, 2.0], "#e8e0d0")
    b.box([0.0, 3.3, z], [7.0, 0.4, 2.0], "#a07a4a")
    b.box([4.05, 2.2, z], [0.1, 1.2, 14.0], "#3a6aa8", collide=False)
    b.box([-4.05, 2.2, z], [0.1, 1.2, 14.0], "#3a6aa8", collide=False)
    b.box([0.0, 2.2, z - 10.05], [6.0, 1.6, 0.1], "#e8e0d0", collide=False,
          decal=kit.sign_decal("S.S. OPTIMIST", "#e8e0d0", "#1d3a6a", 6.0 / 1.6))
    b.box([2.6, 3.6, z + 2.0], [0.5, 0.5, 9.0], "#8a6a4a", collide=False, r=[0.0, 0.4, 0.0])


# ============================================================ the speedway
def _speedway(b: kit.RelayArea) -> None:
    """The land-speed course painted across the pan (the flats are famous
    for it): the black line, the mile boards, the skid marks -- and what is
    left of the last car that tried, nose down in the salt."""
    z0, z1 = SPEED_Z
    zc = (z0 + z1) / 2.0
    b.box([0.0, 0.03, zc], [400.0, 0.06, z1 - z0], "#1b1b1f", collide=False)
    for x in range(-190, 200, 20):
        b.box([float(x), 0.07, zc], [8.0, 0.04, 0.8], "#f2f2f2", collide=False)
    for k, x in enumerate((-180.0, -120.0, -60.0, 60.0, 120.0, 180.0)):
        b.cyl([x, 3.0, z0 - 3.0], [0.8, 6.0, 0.8], "#d8d8d8")
        b.box([x, 6.6, z0 - 3.0], [5.0, 3.0, 0.4], "#e85a1a",
              decal=kit.sign_decal("MILE %d" % (abs(k - 2.5) + 0.5), "#e85a1a", "#ffffff",
                                   5.0 / 3.0))
    # skid marks swerving off the course to the wreck
    for k in range(6):
        for sx in (-1, 1):
            b.box([sx * (3.0 + k * 0.6), 0.04, z0 + 4.0 + k * 3.6], [1.0, 0.06, 3.8], "#3a3a40",
                  collide=False)
    # the rocket car: on its belly, nose in the salt, its parachute out
    cz = -76.0
    b.box([0.0, 2.2, cz], [6.0, 4.4, 26.0], "#c8ccd2", material="metal")
    b.box([0.0, 4.9, cz - 4.0], [3.6, 1.0, 6.0], "#2a3a4a", material="glass")
    b.box([0.0, 6.0, cz + 10.0], [0.8, 3.0, 5.0], "#c42b20")
    for sx in (-1, 1):
        b.box([sx * 4.5, 1.2, cz + 9.0], [3.0, 0.6, 5.0], "#c42b20")
    b.cone([0.0, 2.2, cz - 15.6], [5.0, 5.2, 5.0], "#c8ccd2", collide=False,
           r=[-math.pi / 2.0, 0.0, 0.0])
    b.box([0.0, 3.2, cz + 13.05], [4.0, 2.4, 0.1], "#1b1b1b", collide=False)
    b.sphere([0.0, 1.2, cz + 20.0], [9.0, 2.4, 7.0], "#f2f2f2", collide=False)
    b.sphere([2.6, 1.0, cz + 23.0], [5.0, 1.8, 4.0], "#e85a1a", collide=False)
    kit.board_letters(b, 0.0, 2.6, cz - 13.0, "SPIRIT", 1.6, "#c8ccd2", "#c42b20",
                      facing="z-", solid=False, depth=0.1)
    # a timing tower on each side of the course
    for h in halves(b):
        x0, x1, tz0, tz1 = 96.0, 112.0, -92.0, -78.0
        area = h.r(x0, x1, tz0, tz1)
        room_walls(b, area, 1.2, 0.0, 8.0, "#e8e0d0",
                   doors={h.inward: [(-89.0, -83.0, 7.0)]})
        slab(b, area, 9.2, 1.2, "#3a3e46", studs=True)
        room_walls(b, area, 0.8, 9.2, 11.6, "#e8e0d0",
                   doors={"z+": [(*h.xs(x0 + 2.0, x0 + 6.0), 11.6)]})
        h.flight_z(-64.0, tz1, x0 + 2.0, x0 + 6.0, 0.0, 9.2, "#9aa0a6", fill=0.0)
        for xx in (x0 + 0.6, x1 - 0.6):
            h.box(xx, 14.6, tz0 + 0.6, 1.2, 6.0, 1.2, "#3a3e46")
        h.slab(x0, x1, tz0, tz0 + 6.0, 18.2, 0.6, "#c42b20")
        h.box((x0 + x1) / 2.0, 15.2, tz0 - 0.06, 10.0, 2.4, 0.1, "#1b1b1b", collide=False)
        h.box((x0 + x1) / 2.0, 15.2, tz0 - 0.12, 8.0, 1.2, 0.06, "#ff4a2a", material="neon",
              collide=False)


def _hall_yard(b: kit.RelayArea) -> None:
    """Outside Capacitor Hall: the step-up transformers by the doors, the
    cable trays up the walls to the coils, the warning signs."""
    hx, hz = HALL
    for sx in (-1, 1):
        for sz in (-1, 1):
            x, z = sx * 16.0, sz * (hz + 7.0)
            b.box([x, 0.5, z], [10.0, 1.0, 8.0], CONCRETE, studs=True)
            b.box([x, 4.5, z], [7.0, 7.0, 5.0], "#5d6b62", material="metal")
            for k in range(3):
                b.box([x - 2.0 + k * 2.0, 4.5, z + sz * 2.55], [1.0, 5.0, 0.1], "#4d5a52",
                      collide=False)
            b.cyl([x, 9.4, z], [1.0, 2.8, 1.0], "#d8e2e8")
            # the tray up the wall to the roof
            b.box([sx * 24.0, (HALL_ROOF + 9.0) / 2.0, sz * (hz + 0.3)], [2.0, HALL_ROOF - 9.0 + 0.0, 0.6],
                  "#3a3e46", material="metal", collide=False)
    for sz in (-1, 1):
        b.box([-24.0, 9.0, sz * (hz + 0.36)], [8.0, 3.0, 0.7], "#f2c21e", collide=False,
              r=[0.0, 0.0 if sz > 0 else math.pi, 0.0],
              decal=kit.sign_decal("DANGER", "#f2c21e", "#1b1b1b", 8.0 / 3.0))
        b.box([24.0, 9.0, sz * (hz + 0.36)], [8.0, 3.0, 0.7], "#f2c21e", collide=False,
              r=[0.0, 0.0 if sz > 0 else math.pi, 0.0],
              decal=kit.sign_decal("1,000,000 V", "#f2c21e", "#1b1b1b", 8.0 / 3.0))


def _power_line(b: kit.RelayArea, h: Half) -> None:
    """The old power line along the pan, north and south: wooden poles,
    crossarms, sagging wire -- and one pole the storm brought down."""
    for sz in (-1, 1):
        z = sz * 142.0
        xs = [40.0, 100.0, 160.0, 220.0, 280.0]
        for k, x in enumerate(xs):
            if sz < 0 and k == 2:
                # down: lying across the strip, its top in the salt
                h.box(x - 8.0, 0.7, z, 22.0, 1.4, 1.4, "#6a4a2a")
                h.box(x - 17.0, 0.3, z, 0.6, 0.6, 7.0, "#5a3a1a")
                continue
            h.cyl(x, 11.0, z, 1.4, 22.0, 1.4, "#6a4a2a")
            h.box(x, 21.2, z, 0.6, 0.6, 9.0, "#5a3a1a", collide=False)
            for dz in (-3.6, 0.0, 3.6):
                h.cyl(x, 21.9, z + dz, 0.5, 0.8, 0.5, "#d8e8f0", collide=False)
        for (xa, xb) in zip(xs[:-1], xs[1:]):
            if sz < 0 and (xa == 160.0 or xb == 160.0):
                continue
            for dz in (-3.6, 0.0, 3.6):
                h.box((xa + xb) / 2.0, 22.35, z + dz, xb - xa, 0.12, 0.12, "#1b1b1b",
                      collide=False)


def _hoodoos(b: kit.RelayArea, h: Half) -> None:
    """Salt hoodoos: pillars the wind has carved, each under a cap of
    harder crust -- cover, and something to steer by."""
    rng = random.Random(0x400D)
    for x, z in HOODOOS:
        hgt = rng.uniform(12.0, 22.0)
        w = rng.uniform(5.0, 7.0)
        tiers = 3
        y = 0.0
        for k in range(tiers):
            seg = hgt / tiers
            ww = w * (1.0 - 0.16 * k)
            h.box(x, y + seg / 2.0, z, ww, seg, ww * 0.9, [SALT_DARK, MESA, SALT_DARK][k])
            y += seg
        h.box(x, y + 1.0, z, w * 1.5, 2.0, w * 1.3, MESA_DARK, studs=True)
        h.box(x + w * 0.9, 1.0, z - w * 0.4, w * 0.8, 2.0, w * 0.7, SALT_LIGHT, studs=True)


def _machines(b: kit.RelayArea, h: Half) -> None:
    """A salt harvester parked north of each mesa, a brine tanker south,
    a scraper half buried by the north rods."""
    # the harvester: scoop, conveyor, hopper, big wheels
    x, z = 236.0, 156.0
    h.box(x, 5.0, z, 26.0, 8.0, 14.0, "#d8a83a", material="metal")
    h.box(x - 10.0, 11.0, z, 6.0, 4.0, 8.0, "#2a3038", material="metal")
    h.box(x - 12.05, 11.0, z, 0.1, 2.6, 6.0, "#9fd8e8", collide=False, material="glass")
    h.box(x + 6.0, 11.5, z, 12.0, 5.0, 10.0, "#b8882a", material="metal", studs=True)
    h.box(x + 6.0, 14.1, z, 11.0, 0.2, 9.0, SALT_LIGHT, collide=False)
    h.box(x - 16.0, 2.0, z, 6.0, 3.0, 14.0, "#8a8e96", material="metal")
    for dx in (-8.0, 8.0):
        for dz in (-7.6, 7.6):
            h.cyl(x + dx, 3.0, z + dz, 6.0, 1.6, 6.0, "#1b1b1f", collide=False,
                  r=[math.pi / 2.0, 0.0, 0.0])
    # the brine tanker: cab and tank
    x, z = 236.0, -156.0
    h.box(x, 3.0, z, 30.0, 4.0, 8.0, "#3a3e46", material="metal")
    h.box(x - 12.0, 7.5, z, 6.0, 5.0, 7.0, "#c42b20", material="metal")
    h.box(x - 15.05, 8.0, z, 0.1, 2.4, 5.0, "#9fd8e8", collide=False, material="glass")
    h.cyl(x + 3.0, 8.6, z, 7.0, 20.0, 7.0, "#c8ccd2", material="metal", collide=False,
          r=[0.0, 0.0, math.pi / 2.0])
    h.box(x + 3.0, 7.0, z, 18.0, 2.0, 5.0, "#a8acb2", material="metal")
    # a scraper blade abandoned by the north rods
    h.box(120.0, 1.6, 168.0, 14.0, 3.2, 2.0, "#8a5a2a", material="metal")
    h.box(120.0, 3.6, 172.0, 8.0, 4.0, 6.0, "#d8a83a", material="metal", studs=True)


def _works_detail(b: kit.RelayArea, h: Half) -> None:
    """The salt works' yard: pallets of bagged salt, a water tower, the
    office shack, floodlights, the company's name over the door."""
    y = 6.0
    for x, z in ((236.0, 24.0), (236.0, -24.0)):
        for k in range(2):
            h.box(x, y + 0.3 + k * 2.2, z, 7.0, 0.6, 7.0, "#a07a4a")
            h.box(x, y + 1.5 + k * 2.2, z, 6.4, 1.6, 6.4, "#f2f0ea", studs=True)
    # water tower on the back corner
    x, z = 310.0, 76.0
    for dx in (-3.0, 3.0):
        for dz in (-3.0, 3.0):
            h.box(x + dx, y + 6.0, z + dz, 0.9, 12.0, 0.9, STEEL_DARK)
    h.cyl(x, y + 16.0, z, 10.0, 8.0, 10.0, "#8a8e96", material="metal")
    h.cone(x, y + 21.5, z, 11.0, 3.0, 11.0, "#6a6e76", collide=False)
    # the office shack by the stockpile
    area = h.r(290.0, 312.0, -84.0, -70.0)
    room_walls(b, area, 1.0, y, y + 9.0, "#b8aa94",
               doors={h.inward: [(-80.0, -74.0, y + 7.0)]})
    slab(b, area, y + 10.0, 1.0, "#6a5a4a", studs=True)
    h.box(301.0, y + 5.0, -70.0 + 0.06, 6.0, 2.4, 0.1, "#9fd8e8", collide=False,
          material="glass", alpha=0.6)
    for z in (-60.0, 60.0):
        kit.floodlight(b, h.x(226.0), z, y, 20.0)
    kit.board_letters(b, h.x(WORKS[0]), y + 13.0, 0.0, "SALTGLASS MINING", 2.2, "#3a3e46",
                      "#f2f0ea", facing=h.inward, solid=False)


def _rod_scorch(b: kit.RelayArea, h: Half) -> None:
    """Every rod has been hit: a scorch round its foot and splashes of
    glass where the salt melted."""
    for x, z in RODS:
        h.cyl(x, 0.03, z, 16.0, 0.06, 16.0, "#4a4a52", collide=False)
        for k in range(4):
            a = k * math.pi / 2.0 + 0.4
            h.box(x + math.cos(a) * 6.4, 0.08, z + math.sin(a) * 6.4, 2.4, 0.06, 1.2, GLASSY,
                  collide=False, material="glass", alpha=0.8)


def _wash_detail(b: kit.RelayArea) -> None:
    """What the washes hold: a cow skull, a tyre, salt crystals growing on
    the walls."""
    y = -WASH_DEPTH
    for sz in (-1, 1):
        z = sz * 120.0
        b.sphere([sz * 40.0, y + 1.0, z], [2.4, 2.0, 3.2], "#f2ead8", collide=False)
        b.cone([sz * 40.0 - 1.6, y + 1.6, z - 1.0], [0.8, 2.6, 0.8], "#f2ead8", collide=False,
               r=[0.0, 0.0, 1.0])
        b.cone([sz * 40.0 + 1.6, y + 1.6, z - 1.0], [0.8, 2.6, 0.8], "#f2ead8", collide=False,
               r=[0.0, 0.0, -1.0])
        b.add("torus", [sz * -150.0, y + 0.5, z], [5.0, 5.0, 2.0], "#1b1b1f", collide=False,
              r=[math.pi / 2.0, 0.0, 0.0])
    for sx in (-1, 1):
        for k, x in enumerate((60.0, 112.0, 214.0)):
            for zz in (WASH_Z[0], -WASH_Z[1]):
                b.box([sx * x, y + 2.0 + k, zz + 0.8], [2.0, 2.0, 1.6], "#e8f4f8",
                      material="glass", alpha=0.75)


def _mirages(b: kit.RelayArea) -> None:
    """Water that is not there, shimmering on the far corners of the pan."""
    for sx in (-1, 1):
        for x, z in ((60.0, 170.0), (100.0, -160.0)):
            b.box([sx * x, 0.04, z], [30.0, 0.08, 10.0], "#8ac8e8", collide=False,
                  material="glass", alpha=0.35)


# ===================================================================== edge
def _edge(b: kit.RelayArea, rng: random.Random) -> None:
    """The edge of the pan: low buttes all round, and the storm over them."""
    hx, hz, m = HALF[0], HALF[1], b.margin
    room_walls(b, rect(-hx - m, hx + m, -hz - m, hz + m), m, 0.0, 26.0, "#8a7a6a")
    kit.backdrop(b, "mesas", 0.0, rng, colours=["#4a3e4a", "#5a4a54", "#3e3442"], depth=70.0)


def _landmarks(b: kit.RelayArea) -> None:
    for x, z, name in ((0, 0, "Capacitor Hall"), (0, 172, "the dragline"),
                       (0, 120, "the north wash"), (0, -120, "the south wash"),
                       (0, -160, "the S.S. Optimist")):
        b.landmark(float(x), float(z), name)
    for sx, team in ((-1, "red"), (1, "blue")):
        b.landmark(sx * 278.0, 0.0, "the %s salt works" % team)
        for x, z, name in ((159, 77, "the north pump shed"), (159, -77, "the south pump shed"),
                           (120, 40, "the lightning rods")):
            b.landmark(sx * float(x), float(z), "%s (%s side)" % (name, team))
    b.camera(-170.0, 60.0, -150.0, 0.0, 10.0, 0.0)
    b.camera(170.0, 60.0, 150.0, 0.0, 10.0, 0.0)
    b.camera(0.0, 70.0, -190.0, 0.0, 14.0, 20.0)
