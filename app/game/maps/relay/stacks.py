"""The Grand Stacks -- the reading room of a library the size of a cathedral.

Indoors, all of it: under a ceiling of skylights, shelves taller than houses
stand in rows off the long nave, and their tops are a second floor -- a grid
of catwalks over the bays, bridges across the nave -- for anyone who takes
the library steps up.  Both teams muster in the rotunda in the middle,
under its dome, round the great globe; the flags lie on the map tables in
the Atlas Room (west) and the Chart Room (east).  Books fly about the dome.
A librarian who has been dead a long time keeps order, and does not care
for gunfire.

Layout (red to the west; mirrored about x = 0)::

      z +150  READING ROOM (outpost) .. card catalogue ..  study tables
      z  +86  ============ the north aisle =============================
      z  +46  | shelf | bay | shelf | bay | ...  (catwalks on top, y 20)
      z    0  ATLAS ROOM === the nave === ROTUNDA (globe; relay) === ...
      z  -29  ====== the archive, under the bays: atlas room -> south bay ======
      z  -46  | shelf | bay | shelf | bay | ...
      z  -86  ============ the south aisle =============================
      z -150  BINDERY (outpost) .. card catalogue ..  study tables

The archive is a corridor of rolling stacks eight below the floor, from a
stair beside each flag to a stair up into the first south bay by the
rotunda.
"""
from __future__ import annotations

import math
import random

from . import kit
from .kit import (Half, carve, halves, holed_wall, rect, room_walls, slab, strip_light)

HALF = (300.0, 190.0)
SKY = {"top": "#6a8ab8", "horizon": "#e8e0d0", "sun": [0.3, 0.85, 0.2],
       "clouds": 0.5, "tint": "#fff0d8"}
AMBIENT = "#d4c8b4"
GROUND = "#7a4a2e"
FOG = 700.0

FLOOR = "#7a4a2e"
FLOOR_DARK = "#5a3420"
PANEL = "#6a3e22"
PANEL_DARK = "#4a2a16"
MARBLE = "#e8e0d0"
MARBLE_DARK = "#c8bca8"
BRASS = "#c8a040"
GREEN_LAMP = "#3a8a4a"
RUG = "#8a2a2a"
BOOKS = ["#8a2a2a", "#2a4a8a", "#2a6a3a", "#c89a3a", "#5a2a6a", "#a85a2a", "#3a3a3a", "#e8d8b0"]

CEILING = 48.0
SHELF_H = 20.0
SHELVES = (80.0, 104.0, 128.0, 152.0, 176.0, 200.0, 224.0)
BAY_Z = (16.0, 76.0)
AISLE_Z = (76.0, 96.0)
ROTUNDA = (36.0, 30.0)
WING_X = 64.0
HALL_H = 22.0
BASE = (236.0, 292.0, -40.0, 40.0)
BASE_H = 22.0
FLAG_X = 268.0
ARCHIVE_Z = (-34.0, -24.0)
ARCHIVE_X = (86.0, 284.0)
ARCHIVE_FLOOR = -8.0
BASE_STAIR = (270.0, 284.0)
BAY_STAIR = (86.0, 100.0)


def build(b: kit.RelayArea) -> None:
    rng = random.Random(0x5AC5)
    b.relay("the Rotunda", 50.0)
    b.intro = ["The Grand Stacks -- a library the size of a cathedral, and you are overdue.",
               "Muster in the rotunda by the globe; the flags lie on the map tables in the Atlas "
               "Room and the Chart Room. Take the library steps up: the shelf tops are a floor.",
               "The archive runs under the south bays from beside each flag. Please keep your "
               "voices down."]
    b.extra.update({"accent": "#e8c070"})
    archives = [h.r(ARCHIVE_X[0], ARCHIVE_X[1], ARCHIVE_Z[0], ARCHIVE_Z[1]) for h in halves(b)]
    kit.ground(b, FLOOR, soil="#3a2a1e", holes=archives, material="wood")
    for h in halves(b):
        _archive(b, h)
        _nave(b, h)
        _shelves(b, h, random.Random(0xB00C))
        _base(b, h)
        _outposts(b, h)
        _catalogue(b, h)
    _rotunda(b)
    _hall(b)
    _life(b)
    _landmarks(b)
    del rng


# ================================================================ the archive
def _archive(b: kit.RelayArea, h: Half) -> None:
    """The archive: eight down, rolling stacks along its walls (cover), a
    stair up beside the flag and another up into the first south bay."""
    x0, x1 = ARCHIVE_X
    z0, z1 = ARCHIVE_Z
    area = h.r(x0, x1, z0, z1)
    kit.channel(b, area, -ARCHIVE_FLOOR, FLOOR_DARK, wall_c=PANEL_DARK, studs=False)
    wells = [h.r(BASE_STAIR[0], BASE_STAIR[1], z0, z1), h.r(BAY_STAIR[0], BAY_STAIR[1], z0, z1)]
    kit.plate(b, carve(area, wells), 0.0, 0.6, FLOOR, studs=False, material="wood")
    h.flight_x(BASE_STAIR[1], BASE_STAIR[0], z0, z1, 0.0, ARCHIVE_FLOOR, MARBLE_DARK,
               fill=ARCHIVE_FLOOR)
    h.flight_x(BAY_STAIR[1], BAY_STAIR[0], z0, z1, ARCHIVE_FLOOR, 0.0, MARBLE_DARK,
               fill=ARCHIVE_FLOOR)
    zc = (z0 + z1) / 2.0
    # rolling stacks: shelving on rails, staggered either wall
    for k, x in enumerate(range(int(BAY_STAIR[1]) + 10, int(BASE_STAIR[0]) - 8, 18)):
        z = z0 + 2.2 if k % 2 == 0 else z1 - 2.2
        h.box(float(x), ARCHIVE_FLOOR + 3.0, z, 8.0, 6.0, 3.4, "#5a5a60", studs=True)
        h.box(float(x), ARCHIVE_FLOOR + 3.0, z + (1.76 if k % 2 == 0 else -1.76), 7.6, 5.4, 0.1,
              BOOKS[k % len(BOOKS)], collide=False)
        strip_light(b, h.x(float(x) + 9.0), zc, -0.6, 4.0, "z", "#ffe8b0")
    h.box((BASE_STAIR[0] + BAY_STAIR[1]) / 2.0, ARCHIVE_FLOOR + 0.04, zc,
          BASE_STAIR[0] - BAY_STAIR[1] - 4.0, 0.08, 1.0, BRASS, collide=False)


# ================================================================== the nave
def _nave(b: kit.RelayArea, h: Half) -> None:
    """The nave from the rotunda's wing to the base: a long runner of
    carpet, reading tables with green lamps in the middle (cover), and the
    library steps up onto the shelf tops at its inner end."""
    x0, x1 = WING_X, BASE[0]
    h.box((x0 + x1) / 2.0, 0.04, 0.0, x1 - x0, 0.08, 14.0, RUG, collide=False)
    for x in (92.0, 140.0, 188.0):
        h.box(x, 1.4, 0.0, 10.0, 2.8, 5.0, PANEL, studs=True)
        for dz in (-1.4, 1.4):
            h.cyl(x + 2.0 * (1 if dz > 0 else -1), 3.2, dz, 1.2, 0.8, 1.2, GREEN_LAMP, collide=False)
            h.box(x + 2.0 * (1 if dz > 0 else -1), 3.75, dz, 0.6, 0.3, 0.6, "#fff0b0", material="neon",
                  collide=False)
    # the library steps up to the shelf tops, both sides
    for sz in (-1, 1):
        h.flight_x(WING_X + 2.0, SHELVES[0] - 2.0, sz * 18.0, sz * 26.0, 0.0, SHELF_H, PANEL,
                   fill=0.0)
    # bridges across the nave on the shelf tops
    for x in (SHELVES[1], SHELVES[4]):
        h.slab(x - 3.0, x + 3.0, -BAY_Z[0], BAY_Z[0], SHELF_H, 1.0, PANEL_DARK, studs=True)
        for xx in (x - 2.8, x + 2.8):
            h.box(xx, SHELF_H + 1.2, 0.0, 0.4, 2.4, 2.0 * BAY_Z[0] - 2.0, BRASS, material="metal")


def _shelves(b: kit.RelayArea, h: Half, rng: random.Random) -> None:
    """The shelves: rows off the nave north and south, taller than a house,
    books on both faces, their tops walkable and joined by catwalks down
    each bay row; rolling ladders on brass rails."""
    z0, z1 = BAY_Z
    for sz in (-1, 1):
        zlo, zhi = sorted((sz * z0, sz * z1))
        zc = (zlo + zhi) / 2.0
        for k, x in enumerate(SHELVES):
            h.box(x, SHELF_H / 2.0, zc, 4.0, SHELF_H, zhi - zlo, PANEL_DARK)
            # books, shelf by shelf, both faces
            for row in range(5):
                y = 1.8 + row * 3.8
                for side in (-1, 1):
                    colour = BOOKS[(k * 3 + row + (side + 1)) % len(BOOKS)]
                    h.box(x + side * 2.06, y + 1.3, zc, 0.1, 2.6, zhi - zlo - 2.0, colour,
                          collide=False)
            h.box(x, SHELF_H + 0.3, zc, 4.6, 0.6, zhi - zlo + 0.6, PANEL, studs=True)
        # the catwalk down the row on top of the shelves
        # (a hair under the shelves' caps where it crosses them)
        h.slab(SHELVES[0] - 2.0, SHELVES[-1] + 2.0, sz * 44.0, sz * 50.0, SHELF_H + 0.5, 0.45,
               PANEL, studs=True)
        b.rig("library_ladder", h.x(SHELVES[2] + 2.3), 0.0, zc, len=zhi - zlo - 6.0,
              h=SHELF_H, yaw=h.yaw_out, seed=sz + h.sx)
    del rng


# ===================================================================== bases
def _base(b: kit.RelayArea, h: Half) -> None:
    """The Atlas Room / Chart Room: panelled, a gallery round it on brass
    rails, the flag on the great map table by the fire, globes on stands,
    tall windows, the archive stair beside the table."""
    x0, x1, z0, z1 = BASE
    area = h.r(x0, x1, z0, z1)
    room_walls(b, area, 3.0, 0.0, BASE_H, PANEL,
               doors={h.inward: [(-9.0, 9.0, 12.0)],
                      "z-": [(*h.xs(248.0, 260.0), 10.0)], "z+": [(*h.xs(248.0, 260.0), 10.0)],
                      h.outward: [(-5.0, 5.0, 9.0)]})
    slab(b, area, BASE_H + 1.2, 1.2, PANEL_DARK, studs=True)
    name = "ATLAS ROOM" if h.team == "red" else "CHART ROOM"
    h.box(x0 - 0.36, 15.0, 0.0, 20.0, 3.0, 0.7, PANEL_DARK, collide=False,
          r=[0.0, math.pi / 2.0, 0.0], decal=kit.sign_decal(name, PANEL_DARK, BRASS, 6.7))
    # the map table, the flag on it
    h.box(FLAG_X, 1.5, 0.0, 26.0, 3.0, 18.0, PANEL_DARK, studs=True)
    h.box(FLAG_X, 3.04, 0.0, 24.0, 0.08, 16.0, "#d8c8a0", collide=False)
    top_y = kit.pedestal(b, h.x(FLAG_X), 0.0, 3.0, h.colour, h.neon, base=PANEL, wide=14.0,
                         top_w=9.0)
    b.flag(h.team, h.x(FLAG_X), top_y, 0.0)
    # the fire on the back wall, globes on stands, armchairs
    h.box(x1 - 4.0, 4.0, 22.0, 3.0, 8.0, 12.0, MARBLE, studs=True)
    b.rig("hearth_fire", h.x(x1 - 6.0), 0.0, 22.0, w=6.0, h=4.0, yaw=h.yaw_in)
    for xx, zz in ((248.0, 30.0), (288.0, -30.0)):
        h.cyl(xx, 2.0, zz, 1.2, 4.0, 1.2, BRASS, material="metal")
        b.rig("globe", h.x(xx), 6.4, zz, r=2.4, seed=xx)
    for xx, zz in ((250.0, -30.0), (282.0, 30.0)):
        h.box(xx, 1.6, zz, 4.4, 3.2, 4.4, "#5a2a2a", studs=True)
    # tall windows on the outward wall, light coming in
    for zz in (-14.0, 10.0):
        h.box(x1 - 3.06, 13.0, zz, 0.1, 14.0, 6.0, "#fff4d8", material="neon", collide=False)
    # the archive stair's well, railed
    sx0, sx1 = BASE_STAIR
    tz0, tz1 = ARCHIVE_Z
    h.box(sx0 - 0.6, 1.5, (tz0 + tz1) / 2.0, 1.2, 3.0, tz1 - tz0, BRASS, material="metal")
    h.box((sx0 + sx1) / 2.0 - 0.6, 1.5, tz1 + 0.6, sx1 - sx0 - 1.2, 3.0, 1.2, BRASS,
          material="metal")
    strip_light(b, h.x((x0 + x1) / 2.0), 0.0, BASE_H, 40.0, "x", "#ffe8b0")
    kit.banner_mast(b, h.x(x0 - 8.0), -60.0, 0.0, 22.0, h.team, h.inward)


# ================================================================== outposts
def _outposts(b: kit.RelayArea, h: Half) -> None:
    """The reading room (north) and the bindery (south): where a team falls
    back to while its flag is out."""
    for sz in (1, -1):
        zlo, zhi = sorted((sz * 128.0, sz * 168.0))
        kit.outpost_room(h, 130.0, 180.0, zlo, zhi, 0.0, PANEL, PANEL_DARK, height=12.0,
                         door_w=12.0, pads=2, lights="#ffe8b0")
        label = "READING ROOM" if sz > 0 else "BINDERY"
        face = zlo if sz > 0 else zhi
        h.box(155.0, 9.6, face - sz * 0.36, 18.0, 2.4, 0.7, PANEL_DARK, collide=False,
              r=[0.0, math.pi if sz > 0 else 0.0, 0.0],
              decal=kit.sign_decal(label, PANEL_DARK, BRASS, 7.5))
    # the bindery's press, the reading room's lectern
    h.box(186.0, 3.0, -150.0, 6.0, 6.0, 6.0, "#3a3a40", studs=True)
    h.box(186.0, 2.0, 150.0, 4.0, 4.0, 3.0, PANEL_DARK, studs=True)
    b.rig("lectern_book", h.x(186.0), 4.0, 150.0, yaw=h.yaw_in, seed=h.sx)


def _catalogue(b: kit.RelayArea, h: Half) -> None:
    """The card catalogue: rows of cabinets, chest high, between the aisles
    and the outposts -- a maze to fight through -- and study tables with
    their green lamps further out."""
    for sz in (1, -1):
        for k, x in enumerate((70.0, 86.0, 102.0, 118.0)):
            for j, z in enumerate((108.0, 124.0, 140.0, 156.0, 172.0)):
                if (k + j) % 2:
                    continue
                h.box(x, 2.4, sz * z, 10.0, 4.8, 6.0, "#8a5a32", studs=True)
                h.box(x, 2.4, sz * z - sz * 3.05, 9.0, 4.0, 0.1, "#c8a060", collide=False)
        for x in (200.0, 224.0):
            for z in (118.0, 150.0):
                h.box(x, 1.6, sz * z, 12.0, 3.2, 6.0, PANEL, studs=True)
                h.cyl(x, 3.6, sz * z, 1.2, 0.8, 1.2, GREEN_LAMP, collide=False)
        # the aisle's runner
        h.box(150.0, 0.04, sz * 86.0, 160.0, 0.08, 8.0, "#2a4a3a", collide=False)


# =============================================================== the rotunda
def _rotunda(b: kit.RelayArea) -> None:
    """The rotunda: marble, its doors to the aisles north and south, the
    great globe turning on its stand in the middle, and over it the dome --
    stepped rings up to the oculus -- where the books fly."""
    hx, hz = ROTUNDA
    area = rect(-hx, hx, -hz, hz)
    room_walls(b, area, 3.0, 0.0, HALL_H, MARBLE,
               doors={"z-": [(-7.0, 7.0, 12.0)], "z+": [(-7.0, 7.0, 12.0)],
                      "x-": [(-6.0, 6.0, 10.0)], "x+": [(-6.0, 6.0, 10.0)]})
    # the stand and the globe
    b.cyl([0.0, 2.0, 0.0], [12.0, 4.0, 12.0], MARBLE_DARK, studs=True)
    b.cyl([0.0, 7.0, 0.0], [3.0, 6.0, 3.0], BRASS, material="metal")
    b.rig("globe", 0.0, 22.0, 0.0, r=12.0, seed=0.0, big=True)
    # the dome: rings stepping in over the room to an open oculus
    y = HALL_H
    for k in range(6):
        inset = 4.0 + k * 4.0
        ring = rect(-hx - 2.0 + inset - 4.0, hx + 2.0 - inset + 4.0, -hz - 2.0 + inset - 4.0,
                    hz + 2.0 - inset + 4.0)
        hole = rect(-hx + inset, hx - inset, -hz + inset, hz - inset)
        kit.plate(b, carve(ring, [hole]), y + 3.0, 3.0, MARBLE if k % 2 == 0 else MARBLE_DARK,
                  studs=False)
        y += 3.0
    # the SILENCE sign over the north door
    b.box([0.0, 15.0, hz - 3.36], [16.0, 2.6, 0.7], MARBLE_DARK, collide=False,
          r=[0.0, math.pi, 0.0], decal=kit.sign_decal("SILENCE PLEASE", MARBLE_DARK, "#4a2a16", 6.2))


def _hall(b: kit.RelayArea) -> None:
    """The muster wings either side of the rotunda, and the great hall round
    everything: its walls, its ceiling of skylights."""
    hx, hz = ROTUNDA
    for h in halves(b):
        # the wing: its outer wall (and door), its long walls out from the
        # rotunda's, a roof
        kit.wall(b, "z", h.x(WING_X - 1.5), 3.0, -hz, hz, 0.0, 16.0, MARBLE_DARK,
                 gaps=[(-7.0, 7.0, 11.0)])
        for sz in (-1, 1):
            h.box((hx + WING_X - 3.0) / 2.0, 8.0, sz * (hz - 1.5), WING_X - hx - 3.0, 16.0, 3.0,
                  MARBLE_DARK)
        h.slab(hx, WING_X, -hz, hz, 17.2, 1.2, MARBLE, studs=True)
        for i in range(3):
            for j in (-1, 1):
                b.muster(h.team, h.x(hx + 7.0 + 7.0 * i), 0.0, j * 13.0, h.yaw_out, size=4.6)
        h.sign(WING_X - 3.36, 12.6, 0.0, 10.0, 3.0, "sign_%s" % h.team, "x+")
        strip_light(b, h.x((hx + WING_X) / 2.0), 0.0, 16.0, 40.0, "z", "#ffe8b0")
        h.box(WING_X + 6.0, 2.0, -14.0, 6.0, 4.0, 6.0, PANEL_DARK, studs=True)
        h.box(WING_X + 6.0, 1.6, 14.0, 5.0, 3.2, 5.0, MARBLE_DARK, studs=True)
    # the great hall's walls and its ceiling: skylights over the nave and
    # the aisles, the rotunda's oculus open to the sky
    hx2, hz2, m = HALF[0], HALF[1], b.margin
    room_walls(b, rect(-hx2 - m, hx2 + m, -hz2 - m, hz2 + m), m, 0.0, CEILING, "#e8dcc4")
    # a dark wainscot round the foot of the walls
    for sx in (-1, 1):
        b.box([sx * (hx2 + 0.05), 3.0, 0.0], [0.1, 6.0, 2 * hz2], PANEL_DARK, collide=False)
    for sz in (-1, 1):
        b.box([0.0, 3.0, sz * (hz2 + 0.05)], [2 * hx2, 6.0, 0.1], PANEL_DARK, collide=False)
    whole = rect(-hx2 - m, hx2 + m, -hz2 - m, hz2 + m)
    lights = [rect(-WING_X - 172.0, WING_X + 172.0, -8.0, 8.0),
              rect(-230.0, 230.0, 82.0, 90.0), rect(-230.0, 230.0, -90.0, -82.0),
              rect(-hx, hx, -hz, hz)]
    kit.plate(b, carve(whole, lights), CEILING + 2.0, 2.0, "#d8c8a8", studs=False)
    for r in lights[:3]:
        b.box([(r[0] + r[1]) / 2.0, CEILING + 1.0, (r[2] + r[3]) / 2.0],
              [r[1] - r[0], 0.4, r[3] - r[2]], "#e8f4ff", material="glass", alpha=0.25)


def _life(b: kit.RelayArea) -> None:
    """The books that fly, the librarian, the light coming down."""
    b.rig("book_flock", 0.0, 30.0, 0.0, n=14, r=22.0)
    b.rig("book_flock", 0.0, 34.0, 0.0, n=8, r=120.0, long=True)
    b.rig("librarian", 0.0, 0.0, 86.0, q=[0.0, 0.0, -86.0], r=200.0)
    for x in (-180.0, -100.0, 100.0, 180.0):
        b.rig("light_shaft", x, CEILING, 0.0, w=16.0, d=8.0, h=CEILING)
    for z in (86.0, -86.0):
        b.rig("light_shaft", 0.0, CEILING, z, w=60.0, d=8.0, h=CEILING)


def _landmarks(b: kit.RelayArea) -> None:
    for x, z, name in ((0, 0, "the rotunda"), (0, 86, "the north aisle"),
                       (0, -86, "the south aisle")):
        b.landmark(float(x), float(z), name)
    for sx, team in ((-1, "red"), (1, "blue")):
        b.landmark(sx * 264.0, 0.0, "the %s map room" % team)
        for x, z, name in ((155, 148, "the reading room"), (155, -148, "the bindery"),
                           (150, 0, "the nave"), (93, -29, "the archive stair"),
                           (152, 47, "the shelf tops"), (94, 140, "the card catalogue")):
            b.landmark(sx * float(x), float(z), "%s (%s side)" % (name, team))
    b.camera(-150.0, 36.0, 120.0, 0.0, 10.0, 0.0)
    b.camera(150.0, 36.0, -120.0, 0.0, 10.0, 0.0)
    b.camera(0.0, 40.0, -150.0, 0.0, 14.0, 0.0)
