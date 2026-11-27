"""Lumen Caverns -- the show cave, the night the lights went out.

Layout (north is +z), every bit of it inside the rock::

   z +280 ##########################################################################
          THE CRYSTAL CHAMBER     THE CATHEDRAL ROOM: the Pillar of Ages,    THE OLD MINE
          (beams of selenite,     the stalagmite forest, the light show      (timbered
           a floor four up)       balcony (the lure), the bats               tunnels, carts,
                                                                             the hoist)
   z +104 ======================= THE LOST RIVER, wall to wall ======================
          THE GLOW-WORM GROTTO    THE GRAND GALLERY        THE CHASM: the rope bridge,
          (the still pool, the    THE RIMSTONE POOLS       the wishing pit, the stair down
           boardwalk)             (terraces of water)      to the explorer's camp
   z -182 ------ THE ELEVATOR LOBBY (the safe room), the gift kiosk ---- THE FOSSIL WALL
   z -280 ##########################################################################

Everybody deploys in the elevator lobby, where the tours start -- the lift
up to the surface stuck somewhere over their heads.

What makes it this place:

* **Inside the rock.**  The chambers and passages are all there is: solid
  rock round every one of them, a ceiling over every one -- low in the
  grotto and the mine, fifty up in the Cathedral Room.
* **Down.**  The Lost River to wade under its bridges, the rimstone
  terraces stepping down into their pools, the grotto's pool, and the
  chasm: twenty-four deep, a rope bridge across it, a stair down to where
  an explorer camped and did not come back up.
* **The lure.**  On the balcony in the Cathedral Room: start the light
  show, and the colours sweep the formations and the music swells -- and
  everything down here comes to see it.
* **In the dark.**  Glow-worms on the grotto's ceiling and in its water,
  the crystals glowing, bats on the cathedral roof, a mine cart that
  rolls by itself, the lift's light flickering up in its shaft.
"""
from __future__ import annotations

import math
import random
from typing import List, Tuple

from .kit import (
    CONCRETE, FLOOR, HAZARD, STEEL, STEEL_DARK, WARM, WOOD, WOOD_DARK, WOOD_LIGHT, Area, Surfaces,
    barrel_spot, boundary, building, carve, crate, deploy_pad, flight, plate, post_sign, rect,
    sign_decal, slab, supply_ammo, supply_med, threshold, wall_sign)
from ..relay.kit import rails

Rect = Tuple[float, float, float, float]

HALF = 280.0
ROOF = 50.0
SKY = {"top": "#020304", "horizon": "#0a0c10", "sun": [0.1, 0.95, 0.2],
       "clouds": 0.0, "tint": "#7a8aa8"}
AMBIENT = "#2e323e"

ROCK = "#5a5248"
ROCK_DARK = "#463f38"
ROCK_LIGHT = "#7a7064"
FLOWSTONE = "#c8b89a"
CAVE_FLOOR = "#6a6256"
PATH = "#8a8478"
CRYSTAL = "#e8f2f8"

LOBBY_HALL = rect(-70.0, 70.0, -262.0, -182.0)
LOBBY = rect(-50.0, 50.0, -250.0, -200.0)
GALLERY = rect(-40.0, 40.0, -182.0, 60.0)
RIMSTONE = rect(-160.0, -40.0, -150.0, -40.0)
BASIN = rect(-140.0, -60.0, -140.0, -50.0)
GROTTO = rect(-262.0, -160.0, -170.0, 10.0)
POOL = rect(-240.0, -182.0, -140.0, -30.0)
RIVER = rect(-280.0, 280.0, 60.0, 104.0)
CHANNEL = rect(-280.0, 280.0, 70.0, 94.0)
CATHEDRAL = rect(-60.0, 130.0, 104.0, 264.0)
CRYSTAL_ROOM = rect(-262.0, -76.0, 120.0, 264.0)
CRYSTAL_Y = 4.0
CHASM = rect(80.0, 262.0, -170.0, 44.0)
PIT = rect(150.0, 190.0, -150.0, 30.0)
PIT_FLOOR = -24.0
FOSSIL = rect(70.0, 200.0, -262.0, -186.0)
MINE = (rect(146.0, 262.0, 116.0, 128.0), rect(196.0, 208.0, 128.0, 262.0), rect(146.0, 262.0, 196.0, 208.0),
        rect(238.0, 250.0, 128.0, 262.0), rect(146.0, 160.0, 208.0, 230.0))
PASSAGES = ((rect(-76.0, -60.0, 170.0, 200.0), 20.0), (rect(-200.0, -176.0, 104.0, 120.0), 20.0),
            (rect(130.0, 146.0, 116.0, 128.0), 12.0), (rect(196.0, 208.0, 104.0, 116.0), 12.0),
            (rect(40.0, 80.0, -110.0, -90.0), 18.0), (rect(214.0, 238.0, 44.0, 60.0), 20.0),
            (rect(184.0, 200.0, -186.0, -170.0), 16.0))
# the open spaces and how high their ceilings are; the rock is everything else
CHAMBERS = ((GALLERY, 30.0), (LOBBY_HALL, 22.0), (RIMSTONE, 26.0), (GROTTO, 16.0), (RIVER, 24.0),
            (CATHEDRAL, ROOF), (CRYSTAL_ROOM, 34.0), (CHASM, 40.0), (FOSSIL, 22.0)) + \
    tuple((r, 12.0) for r in MINE) + PASSAGES
SHAFT = rect(240.0, 248.0, 252.0, 260.0)
# the lift shaft, behind the lobby's back wall and up through the roof
LIFT = rect(-5.5, 5.5, -261.0, -250.3)
LIFT_Z = -255.65
PILLAR = (40.0, 190.0)
BALCONY = rect(-56.0, -24.0, 232.0, 260.0)
BALCONY_Y = 8.0
# the light show's stands: one on the balcony, three in the room's corners
PROJECTORS = ((-28.0, BALCONY_Y, 250.0), (126.0, 0.0, 110.0), (-52.0, 0.0, 112.0), (124.0, 0.0, 246.0))


def build(b: Area) -> None:
    rng = random.Random(0xCA7E)
    b.extra.update({"weather": "drips", "accent": "#6af2c8"})
    s = Surfaces(b)
    _ground(b, s)
    boundary(b, ROOF, ROCK_DARK, ROCK_DARK, rng)
    _rock(b)
    n0 = len(b.parts)          # everything from here on is something to keep clear of
    _lobby(b, s)
    _gallery(b, s, rng)
    _rimstone(b)
    _grotto(b, s)
    _river(b, s)
    _cathedral(b, s, rng)
    _crystals(b)
    _chasm(b, s)
    _fossils(b, s)
    _mine(b, s)
    _paths(b, s)
    _rigs(b)
    _zombie_spawns(b)
    _crags(b, rng, n0)
    for x, z, name in ((0, -225, "the elevator lobby"), (0, -60, "the grand gallery"), (-100, -95, "the rimstone pools"),
                       (-211, -85, "the glow-worm grotto"), (-150, 82, "the lost river"), (0, 82, "the river bridge"),
                       (35, 150, "the cathedral room"), (40, 190, "the pillar of ages"),
                       (-40, 246, "the light show balcony"), (-170, 190, "the crystal chamber"), (200, 160, "the old mine"),
                       (244, 250, "the hoist"), (120, -60, "the chasm"), (170, -60, "the rope bridge"),
                       (186, -18, "the wishing pit"), (170, -120, "the explorer's camp"), (135, -258, "the fossil wall"),
                       (130, -246, "the dig scaffold"), (60, -191, "the gift kiosk"), (-55, 64, "the boat dock"),
                       (0, -246, "the stuck elevator")):
        b.landmark(float(x), float(z), name)
    b.camera(10.0, 22.0, 110.0, 40.0, 20.0, 200.0)
    b.camera(-30.0, 12.0, -150.0, 0.0, 6.0, -40.0)
    b.camera(110.0, 14.0, -100.0, 170.0, -10.0, -40.0)
    b.camera(-200.0, 10.0, -30.0, -211.0, 4.0, -90.0)


# ================================================================ helpers
def _stalagmite(b: Area, x: float, z: float, y: float, h: float, w: float, colour: str = FLOWSTONE) -> None:
    b.cone([x, y + h / 2.0, z], [w, h, w], colour)


def _stalactite(b: Area, x: float, z: float, ceiling: float, h: float, w: float, colour: str = FLOWSTONE) -> None:
    b.cone([x, ceiling - h / 2.0, z], [w, h, w], colour, r=[math.pi, 0.0, 0.0], collide=False)


def _column(b: Area, x: float, z: float, y: float, ceiling: float, w: float, colour: str = FLOWSTONE) -> None:
    b.cyl([x, (y + ceiling) / 2.0, z], [w, ceiling - y, w], colour)
    b.cone([x, y + 1.5, z], [w * 1.6, 3.0, w * 1.6], colour)


def _uplight(b: Area, x: float, z: float, y: float, colour: str) -> None:
    """A tour lamp at a formation's foot: a squat steel can, the lens lit."""
    b.box([x, y + 0.5, z], [1.2, 1.0, 1.2], STEEL_DARK, material="metal")
    b.box([x, y + 1.05, z], [0.9, 0.1, 0.9], colour, material="neon")


# ================================================================ ground
def _ground(b: Area, s: Surfaces) -> None:
    h = b.half + b.margin
    holes = [CHANNEL, PIT, POOL, BASIN]
    for r in holes:
        s.reserve(r)
    pieces = carve(rect(-h, h, -h, h), holes)
    plate(b, pieces, 0.0, 0.6, CAVE_FLOOR, studs=True)
    plate(b, pieces, -0.6, 5.4, ROCK_DARK)


def _rock(b: Area) -> None:
    """The rock: solid from floor to roof everywhere that is not a chamber
    or a passage; over each chamber, the rock coming down to its ceiling;
    the roof over the whole cave."""
    open_rects = [r for r, _c in CHAMBERS]
    for k, piece in enumerate(carve(rect(-HALF, HALF, -HALF, HALF), open_rects)):
        b.box([(piece[0] + piece[1]) / 2.0, ROOF / 2.0, (piece[2] + piece[3]) / 2.0],
              [piece[1] - piece[0], ROOF, piece[3] - piece[2]], [ROCK, ROCK_DARK][k % 2])
    done: List[Rect] = []
    for r, ceiling in CHAMBERS:
        if ceiling < ROOF:
            holes = list(done) + ([SHAFT] if r == MINE[3] else []) + ([LIFT] if r == LOBBY_HALL else [])
            plate(b, carve(r, holes), ROOF, ROOF - ceiling, ROCK_DARK)
        done.append(r)
    h = b.half + b.margin
    slab(b, rect(-h, h, -h, h), ROOF + 2.0, 2.0, ROCK_DARK)


# ================================================================= lobby
def _lobby(b: Area, s: Surfaces) -> None:
    """The elevator lobby: where the tours start -- the ticket desk, the
    tour board, the geodes in their cases, the lift doors, shut, with the
    car stuck somewhere up the shaft -- the safe room.  Outside it, in the
    entrance hall, the gift kiosk."""
    x0, x1, z0, z1 = LOBBY
    s.reserve(LOBBY)
    building(b, LOBBY, 0.0, 12.0, "#d8d0c0", roof_colour="#5a5a56", floor_colour="#8a8070",
             doors={"z+": [(-10.0, 10.0, 9.0)], "x+": [(-230.0, -220.0, 9.0)]},
             windows={"z+": [(-44.0, -20.0, 3.5, 8.0), (20.0, 44.0, 3.5, 8.0)]},
             glass=True, lights="#f2ead8")
    threshold(b, LOBBY, "z+", (-10.0, 10.0))
    threshold(b, LOBBY, "x+", (-230.0, -220.0))
    wall_sign(b, 0.0, 10.6, z1 + 0.35, 30.0, 1.6, sign_decal("LUMEN CAVERNS  TOURS START HERE", "#d8d0c0", "#2a4a3a", 18.75),
              "z+", "#d8d0c0")
    floor = FLOOR
    for z in (-236.0, -218.0):
        for k in range(8):
            x = -38.0 + k * 10.8
            deploy_pad(b, x, z, floor, "#6af2c8", 4.8)
            b.safe_spawn(x, floor + 0.6, z, 0.0)
    # the lift doors in the back wall, the out-of-order sign
    b.box([0.0, floor + 4.5, z0 + 2.2], [8.0, 9.0, 0.4], "#8a9096", material="metal")
    b.box([0.0, floor + 4.5, z0 + 2.45], [0.1, 9.0, 0.1], "#2a2a2e", collide=False)
    b.box([6.0, floor + 4.0, z0 + 2.1], [1.0, 2.0, 0.2], STEEL_DARK)
    wall_sign(b, 0.0, floor + 10.2, z0 + 2.0 + 0.35, 10.0, 1.0, sign_decal("ELEVATOR OUT OF SERVICE", HAZARD, "#1b1b1b", 10.0),
              "z+", HAZARD)
    b.box([-30.0, floor + 1.6, z0 + 4.0], [14.0, 3.2, 3.0], WOOD_DARK)
    for k in range(2):
        b.box([x0 + 3.0, floor + 1.0, -240.0 + k * 12.0], [2.0, 2.0, 8.0], WOOD_DARK)
        b.box([x0 + 3.0, floor + 2.0 + 1.0, -240.0 + k * 12.0], [2.0, 2.0, 8.0], "#b8d8e8", material="glass", alpha=0.35)
        for j in range(3):
            b.sphere([x0 + 3.0, floor + 2.0 + 0.6, -242.4 + k * 12.0 + j * 2.4], [1.2, 1.2, 1.2],
                     ["#8a4ab8", "#3a8ac8", "#c84a6a"][(j + k) % 3])
    supply_ammo(b, 40.0, floor, -246.0, "z+")
    supply_med(b, -44.0, floor, -204.0, "x+")
    _lift_shaft(b)
    # the gift kiosk in the hall
    kx, kz = 60.0, -191.0
    b.box([kx, 1.6, kz], [12.0, 3.2, 3.0], "#8a5a3a")
    for (dx, dz) in ((-5.6, -1.2), (5.6, -1.2), (-5.6, 1.2), (5.6, 1.2)):
        b.box([kx + dx, 4.4, kz + dz], [0.6, 2.4, 0.6], WOOD_DARK)
    slab(b, rect(kx - 6.4, kx + 6.4, kz - 2.0, kz + 2.0), 6.2, 0.6, "#2a5a4a")
    for j in range(4):
        b.sphere([kx - 4.5 + j * 3.0, 3.2 + 0.6, kz], [1.2, 1.2, 1.2], ["#8a4ab8", "#e8e2d4", "#3a8ac8", "#c8a03a"][j])
    barrel_spot(b, -62.0, 0.0, -192.0)


def _lift_shaft(b: Area) -> None:
    """The lift's shaft behind the lobby: four steel posts from the floor
    up through the hall's roof to the surface, cross-braced -- the car
    (a rig) stuck in it over the heads of anybody who walks under."""
    zf, zb = -251.0, -260.3
    for x in (-4.7, 4.7):
        for z in (zf, zb):
            b.box([x, (ROOF + 0.5) / 2.0, z], [0.6, ROOF + 0.5, 0.6], STEEL_DARK, material="metal")
    # out of reach, up the hole: rings of steel
    for y in (22.0, 27.0, 32.0, 37.0, 42.0, 47.0):
        for x in (-4.7, 4.7):
            b.box([x, y, LIFT_Z], [0.4, 0.4, zf - zb - 0.6], STEEL_DARK, material="metal")
        for z in (zf, zb):
            b.box([0.0, y, z], [8.8, 0.4, 0.4], STEEL_DARK, material="metal")
    # within reach, the bracing is only a lattice you could put a hand through
    span = zf - zb - 0.6
    for (y0, y1) in ((4.0, 12.0), (12.0, 20.0)):
        h = y1 - y0
        length = math.hypot(span, h)
        tilt = math.atan2(h, span)
        for x in (-4.7, 4.7):
            for sign in (-1.0, 1.0):
                b.box([x, (y0 + y1) / 2.0, LIFT_Z], [0.25, 0.25, length], "#4a5056", r=[sign * tilt, 0.0, 0.0],
                      collide=False, material="metal", alpha=0.9)
        b.box([0.0, y1, zb], [8.8, 0.3, 0.3], "#4a5056", collide=False, material="metal", alpha=0.9)
    wall_sign(b, 0.0, 9.0, LOBBY_HALL[2] + 0.35, 7.0, 1.0, sign_decal("NO 1 SHAFT  KEEP CLEAR", HAZARD, "#1b1b1b", 7.0),
              "z+", HAZARD)


def _gallery(b: Area, s: Surfaces, rng: random.Random) -> None:
    """The Grand Gallery: the main way through, the tour path down its
    middle, stalagmites and columns along both sides, the frozen waterfall
    of flowstone down the west wall, coloured lamps at their feet."""
    x0, x1, z0, z1 = GALLERY
    ceiling = 30.0
    for k in range(10):
        z = z0 + 14.0 + k * 22.0
        for side in (-1, 1):
            if side < 0 and -150.0 < z < -40.0:
                continue
            x = side * (30.0 - (k % 3) * 2.0)
            _stalagmite(b, x, z, 0.0, 4.0 + (k * 7 % 5) * 1.6, 3.0 + (k % 2))
            _stalactite(b, x + side * 2.0, z + 6.0, ceiling, 3.0 + (k * 5 % 4) * 1.4, 2.6)
    for (x, z) in ((-24.0, -176.0), (22.0, -134.0), (24.0, 16.0), (-24.0, 46.0)):
        _column(b, x, z, 0.0, ceiling, 4.0)
    # the frozen waterfall: flowstone in steps down the east wall, climbable
    for k in range(5):
        slab(b, rect(x1 - 10.0 + k * 2.0, x1, -20.0, -4.0), 2.0 * (k + 1), 2.0, FLOWSTONE, studs=True)
    for (x, z, c) in ((-26.0, -160.0, "#3af2a8"), (26.0, -110.0, "#a83af2"), (24.0, -8.0, "#f2a83a"), (-24.0, 30.0, "#3aa8f2")):
        _uplight(b, x, z, 0.0, c)
    supply_ammo(b, 24.0, 0.0, 0.0, "x-")
    barrel_spot(b, -20.0, 0.0, 20.0)


def _rimstone(b: Area) -> None:
    """The rimstone pools: terraces of still water stepping down into the
    floor, each held by its own lip of stone, down to the deepest pool."""
    x0, x1, z0, z1 = BASIN
    for k in range(4):
        outer = rect(x0 + 8.0 * k, x1 - 8.0 * k, z0 + 6.0 * k, z1 - 6.0 * k)
        inner = rect(x0 + 8.0 * (k + 1), x1 - 8.0 * (k + 1), z0 + 6.0 * (k + 1), z1 - 6.0 * (k + 1))
        top = -1.6 * (k + 1)
        pieces = carve(outer, [inner]) if k < 3 else [outer]
        plate(b, pieces, top, 8.0 + top, FLOWSTONE if k % 2 == 0 else "#b8a88a", studs=True)
        for p in pieces:
            b.box([(p[0] + p[1]) / 2.0, top + 0.3, (p[2] + p[3]) / 2.0], [p[1] - p[0], 0.6, p[3] - p[2]], "#3a8a8a",
                  collide=False, material="glass", alpha=0.72)
    supply_med(b, -150.0, 0.0, -100.0, "x+")
    for (x, z) in ((-50.0, -140.0), (-150.0, -46.0)):
        _stalagmite(b, x, z, 0.0, 7.0, 4.0)


def _grotto(b: Area, s: Surfaces) -> None:
    """The Glow-Worm Grotto: a low chamber over a still black pool, its
    ceiling alive with lights; a boardwalk across the water on posts, two
    little boats tied to it."""
    x0, x1, z0, z1 = POOL
    slab(b, POOL, -3.0, 3.0, ROCK_DARK, studs=True)
    b.water((x0 + x1) / 2.0, (z0 + z1) / 2.0, x1 - x0, z1 - z0, -0.8, "#0a2a2a")
    walk = rect(x0, x1, -90.0, -84.0)
    slab(b, walk, 0.6, 0.6, WOOD, studs=True)
    for x in (x0 + 8.0, x0 + 22.0, x0 + 36.0, x0 + 50.0):
        for z in (-89.6, -84.4):
            b.box([x, -1.5, z], [0.8, 3.0, 0.8], WOOD_DARK)
    for (bx, bz) in ((-226.0, -100.0), (-196.0, -74.0)):
        b.box([bx, -1.1, bz], [8.0, 1.2, 3.6], "#3a5a6a")
        b.box([bx, -0.3, bz], [0.6, 0.4, 3.0], WOOD)
    post_sign(b, -176.0, -96.0, 0.0, 3.0, 8.0, 1.8, sign_decal("GLOW-WORM GROTTO  QUIET PLEASE", "#2a3a3a", "#6af2c8", 4.4),
              "x-", "#2a3a3a")
    supply_med(b, -206.0, 0.6, -87.0, "z+")
    for (x, z) in ((-250.0, -160.0), (-170.0, 0.0), (-250.0, -10.0)):
        _stalagmite(b, x, z, 0.0, 5.0, 3.6)


def _river(b: Area, s: Surfaces) -> None:
    """The Lost River, in from under the west wall and out under the east:
    wade-deep, two bridges over it high enough to wade under, the boat dock
    with the tour boats tied up."""
    x0, x1, z0, z1 = CHANNEL
    slab(b, CHANNEL, -4.0, 2.0, ROCK_DARK, studs=True)
    b.water(0.0, (z0 + z1) / 2.0, x1 - x0, z1 - z0, -1.4, "#1a3a4a")
    for bx in (0.0, 202.0):
        slab(b, rect(bx - 8.0, bx + 8.0, z0 - 2.0, z1 + 2.0), 2.0, 0.6, WOOD, studs=True)
        for z in (z0 - 1.4, z1 + 1.4):
            for side in (-1, 1):
                b.box([bx + side * 7.6, 0.7, z], [0.8, 1.4, 0.8], WOOD_DARK)
    slab(b, rect(-70.0, -40.0, z0 - 4.0, z0 + 4.0), 0.6, 0.6, WOOD, studs=True)
    for x in (-68.0, -42.0):
        b.box([x, -2.0, z0 + 3.4], [0.8, 4.0, 0.8], WOOD_DARK)
    for k, bx in enumerate((-62.0, -48.0)):
        b.box([bx, -1.4, z0 + 9.0], [6.0, 1.2, 9.0], ["#c8a03a", "#3a7a8a"][k])
        b.box([bx, -0.6, z0 + 9.0], [5.0, 0.4, 0.6], WOOD)
    post_sign(b, -36.0, z0 - 6.0, 0.0, 3.0, 8.0, 1.8, sign_decal("LOST RIVER BOAT TOURS", "#2a4a5a", "#e8e2d4", 4.4), "z+",
              "#2a4a5a")
    barrel_spot(b, 120.0, 0.0, 64.0)
    barrel_spot(b, -120.0, 0.0, 100.0)


def _cathedral(b: Area, s: Surfaces, rng: random.Random) -> None:
    """The Cathedral Room: fifty up to the roof, the Pillar of Ages in the
    middle on its stepped foot, the stalagmite forest, the flowstone
    terraces up the north wall, the chandelier of stalactites, and the
    balcony where the light show is run from (the lure)."""
    x0, x1, z0, z1 = CATHEDRAL
    px, pz = PILLAR
    s.reserve(rect(px - 18.0, px + 18.0, pz - 18.0, pz + 18.0))
    slab(b, rect(px - 18.0, px + 18.0, pz - 18.0, pz + 18.0), 2.0, 2.0, FLOWSTONE, studs=True)
    slab(b, rect(px - 14.0, px + 14.0, pz - 14.0, pz + 14.0), 4.0, 2.0, FLOWSTONE, studs=True)
    b.cyl([px, (4.0 + ROOF) / 2.0, pz], [22.0, ROOF - 4.0, 22.0], "#d8c8a8")
    for k in range(6):
        a = k / 6.0 * math.pi * 2.0
        b.cyl([px + math.cos(a) * 9.0, 4.0 + 4.0, pz + math.sin(a) * 9.0], [6.0, 8.0, 6.0], "#c8b898")
    # the stalagmite forest in the east of the room
    for k in range(14):
        x = 80.0 + (k % 4) * 11.0 + (k // 4) * 3.0
        z = 120.0 + (k // 4) * 32.0 + (k % 3) * 4.0
        _stalagmite(b, x, z, 0.0, 6.0 + (k * 7 % 6) * 2.0, 4.0 + (k % 3))
    # flowstone terraces up the north wall to a ledge
    for k in range(6):
        slab(b, rect(30.0, 110.0, z1 - 14.0 + k * 2.0, z1), 2.0 * (k + 1), 2.0, FLOWSTONE if k % 2 else "#b8a888", studs=True)
    # the chandelier: stalactites hanging in a ring over the middle
    for k in range(12):
        a = k / 12.0 * math.pi * 2.0
        _stalactite(b, 20.0 + math.cos(a) * 14.0, 150.0 + math.sin(a) * 10.0, ROOF, 8.0 + (k % 3) * 4.0, 3.0)
    _stalactite(b, 20.0, 150.0, ROOF, 18.0, 6.0)
    # the balcony and its console
    bx0, bx1, bz0, bz1 = BALCONY
    s.reserve(rect(bx0, -10.0, bz0, bz1))
    slab(b, BALCONY, BALCONY_Y, BALCONY_Y, ROCK_LIGHT, studs=True)
    flight(b, "x", -10.0, bx1, 236.0, 244.0, 0.0, BALCONY_Y, ROCK_LIGHT, fill=0.0)
    rails(b, BALCONY, BALCONY_Y, 2.4, STEEL_DARK, 0.6, gaps={"x+": [(236.0, 244.0)]})
    b.box([-44.0, BALCONY_Y + 1.4, 254.0], [10.0, 2.8, 2.4], "#3a3e48", material="metal")
    for k in range(5):
        b.box([-48.0 + k * 2.0, BALCONY_Y + 2.85, 253.6], [1.4, 0.1, 1.0],
              ["#ff3a5a", "#3af2a8", "#3a8aff", "#ffd84a", "#c83aff"][k], material="neon", collide=False)
    b.set_lure(-44.0, BALCONY_Y, 250.6, "the light show", "Start the light show", "ll_lightshow", (px, 0.0, pz))
    supply_ammo(b, -32.0, BALCONY_Y, 256.0, "x-")
    for (x, z, c) in ((px - 20.0, pz, "#ff3a5a"), (px + 20.0, pz, "#3a8aff"), (px, pz - 20.0, "#3af2a8"), (px, pz + 20.0, "#ffd84a")):
        _uplight(b, x, z, 0.0, c)
    barrel_spot(b, -40.0, 0.0, 130.0)
    barrel_spot(b, 110.0, 0.0, 200.0)
    # the light show's moving heads stand on these (the heads themselves
    # turn, so they are drawn by the rig)
    for (x, y, z) in PROJECTORS:
        b.box([x, y + 0.1, z], [2.4, 0.2, 2.4], STEEL_DARK, material="metal")
        b.cyl([x, y + 1.1, z], [0.5, 1.8, 0.5], STEEL_DARK)
        b.box([x, y + 1.95, z], [1.4, 0.1, 1.4], "#2a2c30", material="metal")


def _crystals(b: Area) -> None:
    """The Crystal Chamber: a floor four up from the river, and over it the
    selenite -- beams as long as a bus lying across each other on standing
    crystals, a climbing frame of them, glowing."""
    x0, x1, z0, z1 = CRYSTAL_ROOM
    y = CRYSTAL_Y
    slab(b, CRYSTAL_ROOM, y, y, "#8a8478", studs=True)
    flight(b, "z", 104.0, z0, -200.0, -176.0, 0.0, y, ROCK_LIGHT, fill=0.0)
    flight(b, "x", -60.0, x1, 170.0, 200.0, 0.0, y, ROCK_LIGHT, fill=0.0)
    for (cx, cz, h, w) in ((-230.0, 150.0, 14.0, 4.0), (-240.0, 236.0, 20.0, 5.0), (-120.0, 240.0, 16.0, 4.0),
                           (-110.0, 140.0, 10.0, 3.6), (-200.0, 244.0, 12.0, 4.0), (-150.0, 140.0, 8.0, 4.0)):
        b.box([cx, y + h / 2.0, cz], [w, h, w], CRYSTAL, material="glass", alpha=0.75)
    # a staircase of crystals, each a step up on the last, to a beam right
    # across the room on a crystal at its far end
    for k in range(7):
        top = y + 2.0 * (k + 1)
        slab(b, rect(-200.0 + 6.0 * k, -194.0 + 6.0 * k, 180.0, 186.0), top, top - y, CRYSTAL, material="glass",
             alpha=0.75)
    beam_top = y + 14.0
    slab(b, rect(-100.0, -94.0, 180.0, 186.0), beam_top, beam_top - y, CRYSTAL, material="glass", alpha=0.75)
    slab(b, rect(-158.0, -100.0, 180.0, 186.0), beam_top, 3.0, CRYSTAL, material="glass", alpha=0.75)
    for (x0c, x1c, z0c, z1c, h) in ((-226.0, -212.0, 210.0, 214.0, 3.0), (-170.0, -150.0, 214.0, 218.0, 2.4),
                                    (-136.0, -132.0, 150.0, 170.0, 3.0)):
        slab(b, rect(x0c, x1c, z0c, z1c), y + h, h, CRYSTAL, material="glass", alpha=0.75)
    for (cx, cz, a, c) in ((-180.0, 190.0, 0.7, 0.4), (-130.0, 200.0, -0.5, 0.8), (-210.0, 130.0, 0.4, -0.3)):
        b.box([cx, y + 22.0, cz], [3.0, 16.0, 3.0], CRYSTAL, r=[a, c, 0.2], collide=False, material="glass", alpha=0.6)
    supply_ammo(b, -100.0, y, 200.0, "x-")
    barrel_spot(b, -250.0, y, 250.0)


def _chasm(b: Area, s: Surfaces) -> None:
    """The chasm: a crack in the floor twenty-four deep down the middle of
    its chamber; the rope bridge over it, the wishing pit's balcony, the
    stair down the west side to the bottom, where the explorer camped."""
    x0, x1, z0, z1 = PIT
    slab(b, PIT, PIT_FLOOR, 6.0, ROCK_DARK, studs=True)
    plate(b, carve(rect(x0 - 4.0, x1 + 4.0, z0 - 4.0, z1 + 4.0), [PIT]), -6.0, 6.0 - PIT_FLOOR, ROCK_DARK)
    flight(b, "z", -110.0, z0, x0, x0 + 6.0, PIT_FLOOR, 0.0, ROCK_LIGHT, fill=PIT_FLOOR)
    # the rope bridge: planks sagging to the middle, a post at each end
    for k in range(10):
        sag = -1.2 * math.sin(math.pi * (k + 0.5) / 10.0)
        bx = x0 + 2.0 + k * 4.0
        b.box([bx, sag - 0.15, -60.0], [3.6, 0.3, 4.0], WOOD_LIGHT)
    for x in (x0 - 1.0, x1 + 1.0):
        for z in (-62.6, -57.4):
            b.cyl([x, 1.8, z], [0.8, 3.6, 0.8], WOOD_DARK)
    # the wishing pit's balcony out over the drop
    slab(b, rect(x1 - 8.0, x1, -24.0, -12.0), 0.0, 0.6, ROCK_LIGHT, studs=True)
    b.box([x1 - 7.6, 1.2, -18.0], [0.8, 2.4, 12.0], STEEL_DARK)
    b.box([x1 - 4.0, 1.2, -23.6], [6.4, 2.4, 0.8], STEEL_DARK)
    b.box([x1 - 4.0, 1.2, -12.4], [6.4, 2.4, 0.8], STEEL_DARK)
    post_sign(b, x1 + 6.0, -18.0, 0.0, 3.0, 8.0, 1.8, sign_decal("WISHING PIT  DROP A COIN", "#2a2a2e", "#e8c35a", 4.4), "x-",
              "#2a2a2e")
    for k in range(9):
        b.cyl([x1 - 10.0 + (k % 3) * 2.0, PIT_FLOOR + 0.05, -20.0 + (k // 3) * 2.0], [0.6, 0.1, 0.6], "#e8c35a",
              material="metal", collide=False)
    # the explorer's camp at the bottom: the tarp, the bedroll, the lantern, the journal
    for (x, z) in ((166.0, -128.0), (178.0, -128.0), (166.0, -116.0), (178.0, -116.0)):
        b.box([x, PIT_FLOOR + 2.5, z], [0.4, 5.0, 0.4], WOOD_DARK)
    slab(b, rect(165.0, 179.0, -129.0, -115.0), PIT_FLOOR + 5.4, 0.4, "#3a5a3a")
    b.box([172.0, PIT_FLOOR + 0.3, -122.0], [3.0, 0.6, 6.0], "#5a3a2a")
    b.box([176.0, PIT_FLOOR + 0.5, -118.0], [1.6, 1.0, 1.2], "#8a6a3a")
    supply_med(b, 168.0, PIT_FLOOR, -112.0, "z-")
    supply_ammo(b, 230.0, 0.0, -100.0, "x-")
    for (x, z) in ((100.0, -160.0), (250.0, 30.0), (100.0, 30.0), (250.0, -160.0)):
        _stalagmite(b, x, z, 0.0, 8.0, 4.0)
    barrel_spot(b, 120.0, 0.0, 0.0)
    barrel_spot(b, 220.0, 0.0, -140.0)


def _fossils(b: Area, s: Surfaces) -> None:
    """The fossil wall: a sea monster forty long set in the south face of
    its chamber, the dig scaffold in front of it, the tools, the
    generator that ran out."""
    x0, x1, z0, z1 = FOSSIL
    face = z0 + 0.4
    bone = "#e8dcc0"
    b.box([96.0, 10.0, face], [10.0, 3.0, 0.8], bone)
    b.box([89.0, 10.6, face], [4.0, 1.2, 0.8], bone)
    for k in range(14):
        x = 104.0 + k * 3.0
        y = 10.0 + math.sin(k * 0.45) * 1.5
        b.box([x, y, face], [2.4, 1.6, 0.8], bone)
        if 2 <= k <= 9:
            b.box([x, y - 2.6, face], [0.6, 3.4, 0.8], bone)
    for (fx, fy) in ((112.0, 6.2), (132.0, 6.6)):
        b.box([fx, fy, face], [5.0, 1.2, 0.8], bone, r=[0.0, 0.0, -0.4])
    b.box([148.0, 11.0, face], [4.0, 4.0, 0.8], bone, r=[0.0, 0.0, 0.6])
    scaffold = rect(100.0, 160.0, z0 + 4.0, z0 + 12.0)
    s.reserve(rect(100.0, 172.0, z0 + 4.0, z0 + 12.0))
    slab(b, scaffold, 6.0, 0.6, WOOD, studs=True)
    for (x, z) in ((100.4, z0 + 4.4), (159.6, z0 + 4.4), (100.4, z0 + 11.6), (159.6, z0 + 11.6), (130.0, z0 + 11.6)):
        b.box([x, 2.7, z], [0.8, 5.4, 0.8], WOOD_DARK)
    flight(b, "x", 172.0, 160.0, z0 + 6.0, z0 + 12.0, 0.0, 6.0, WOOD_DARK, fill=0.0)
    b.box([130.0, 7.2, z0 + 11.6], [60.0, 1.2, 0.8], WOOD_DARK)
    supply_ammo(b, 110.0, 6.0, z0 + 8.0, "z+")
    for (x, z) in ((80.0, -200.0), (180.0, -230.0)):
        crate(b, x, 0.0, z, 4.0, "#7a5a3a")
    b.box([185.0, 1.6, -205.0], [5.0, 3.2, 3.0], "#c8a03a", material="metal")
    wall_sign(b, 185.0, 2.0, -206.85, 4.0, 1.0, sign_decal("OUT OF FUEL", "#c8a03a", "#1b1b1b", 4.0), "z-", "#c8a03a")
    post_sign(b, 90.0, -220.0, 0.0, 3.0, 8.0, 1.8, sign_decal("THE FOSSIL WALL  DO NOT TOUCH", "#e8dcc0", "#3a2a1a", 4.4),
              "x+", "#e8dcc0")
    barrel_spot(b, 160.0, 0.0, -200.0)


def _mine(b: Area, s: Surfaces) -> None:
    """The old silver mine off the cathedral: timbered tunnels, rails down
    the main drive with carts on them, the dynamite alcove, the hoist at
    the end of the east drive with its rope up the shaft."""
    def crossing(r: Rect, line: Rect) -> bool:
        # a frame where another drive crosses this one would stand in the way
        return any(o is not r and o[0] < line[1] and o[1] > line[0] and o[2] < line[3] and o[3] > line[2]
                   for o in MINE)

    for r in MINE[:4]:
        x0, x1, z0, z1 = r
        along_x = x1 - x0 > z1 - z0
        n = int(((x1 - x0) if along_x else (z1 - z0)) // 12.0)
        for k in range(1, n):
            line = rect(x0 + k * 12.0 - 0.5, x0 + k * 12.0 + 0.5, z0, z1) if along_x else \
                rect(x0, x1, z0 + k * 12.0 - 0.5, z0 + k * 12.0 + 0.5)
            if crossing(r, line):
                continue
            if along_x:
                x = x0 + k * 12.0
                for z in (z0 + 0.5, z1 - 0.5):
                    b.box([x, 5.7, z], [1.0, 11.4, 1.0], WOOD_DARK)
                b.box([x, 11.7, (z0 + z1) / 2.0], [1.0, 0.6, z1 - z0], WOOD_DARK)
            else:
                z = z0 + k * 12.0
                for x in (x0 + 0.5, x1 - 0.5):
                    b.box([x, 5.7, z], [1.0, 11.4, 1.0], WOOD_DARK)
                b.box([(x0 + x1) / 2.0, 11.7, z], [x1 - x0, 0.6, 1.0], WOOD_DARK)
    for z in (120.0, 124.0):
        b.box([204.0, 0.15, z], [116.0, 0.3, 0.4], "#6a6f76", material="metal")
    b.box([240.0, 1.0, 122.0], [5.0, 1.4, 4.4], "#2a2a2e")
    b.box([240.0, 2.7, 122.0], [6.0, 2.0, 5.0], "#5a5a5e", studs=True)
    for (x, z) in ((150.0, 214.0), (150.0, 222.0), (155.0, 226.0)):
        crate(b, x, 0.0, z, 3.6, "#8a3a2a")
    wall_sign(b, 146.35, 6.0, 219.0, 8.0, 1.4, sign_decal("DANGER  DYNAMITE", "#8a3a2a", "#f2e8d8", 5.7), "x+", "#8a3a2a")
    supply_ammo(b, 155.0, 0.0, 212.0, "z+")
    for (x, z) in ((158.0, 218.0), (158.0, 210.5)):
        barrel_spot(b, x, 0.0, z)
    # the hoist: the winch on its frame, the rope up the shaft
    b.box([244.0, 1.6, 256.0], [6.0, 3.2, 3.0], WOOD_DARK)
    b.cyl([244.0, 4.2, 256.0], [2.4, 6.0, 2.4], "#5a4a3a", r=[0.0, 0.0, math.pi / 2.0], collide=False)
    b.box([244.0, 30.0, 256.0], [0.3, 40.0, 0.3], "#8a7a5a", collide=False)
    supply_med(b, 244.0, 0.0, 247.0, "z-")


def _paths(b: Area, s: Surfaces) -> None:
    """The tour path: concrete, down the gallery from the lobby door to
    the river bridge, round the cathedral, along the chasm's west ledge."""
    for r in (rect(-6.0, 6.0, -200.0, 68.0), rect(-6.0, 6.0, 96.0, 140.0), rect(-6.0, 80.0, 134.0, 146.0),
              rect(84.0, 96.0, -150.0, 30.0), rect(6.0, 40.0, -106.0, -94.0)):
        s.lay(r, 0.3, PATH, studs=True)


# =============================================================== the rock
# where the walls get their crags: each chamber, its ceiling, its floor, how
# far the rock may come out into it
CRAGGY = ((GALLERY, 30.0, 0.0, 4.0), (LOBBY_HALL, 22.0, 0.0, 3.0), (RIMSTONE, 26.0, 0.0, 5.0),
          (GROTTO, 16.0, 0.0, 5.0), (RIVER, 24.0, 0.0, 2.5), (CATHEDRAL, ROOF, 0.0, 6.0),
          (CRYSTAL_ROOM, 34.0, CRYSTAL_Y, 5.0), (CHASM, 40.0, 0.0, 6.0), (FOSSIL, 22.0, 0.0, 4.0))
# the ceilings that get lumps of rock hanging from them (the grotto's is
# the glow-worms', the lobby hall's the lift's)
LUMPY = ((GALLERY, 30.0), (RIMSTONE, 26.0), (RIVER, 24.0), (CATHEDRAL, ROOF), (CRYSTAL_ROOM, 34.0),
         (CHASM, 40.0), (FOSSIL, 22.0))
# breakdown: heaps of fallen roof on the floor, (x, z, how big)
HEAPS = ((-38.0, 160.0, 14.0), (225.0, -50.0, 14.0), (85.0, -245.0, 12.0), (-175.0, -158.0, 10.0))


def _in_rock(x: float, z: float) -> bool:
    if abs(x) >= HALF or abs(z) >= HALF:
        return False
    return not any(r[0] <= x <= r[1] and r[2] <= z <= r[3] for r, _c in CHAMBERS)


class _Clear:
    """What the rock has to keep clear of: every part laid since the rock
    went in (formations, signs, supplies, paths, pools), the spawns, the
    supply and barrel points and the lure -- and the crags it has put in
    already, which it may touch but not cut into."""

    def __init__(self, b: Area, n0: int):
        self.boxes: List[Tuple[float, float, float, float, float, float]] = []
        for part in b.parts[n0:]:
            px, py, pz = part["p"]
            sx, sy, sz = part["s"]
            if "r" in part and any(abs(v) > 1e-3 for v in part["r"]):
                sx = sy = sz = max(sx, sy, sz)
            self.boxes.append((px - sx / 2 - b.ox, px + sx / 2 - b.ox, py - sy / 2, py + sy / 2,
                               pz - sz / 2 - b.oz, pz + sz / 2 - b.oz))
        self.points: List[Tuple[float, float, float]] = []
        for entry in b.zspawns:
            if "local" in entry:
                self.points.append((entry["local"][0], entry["local"][1], 5.0))
        for entry in b.safe:
            self.points.append((entry["p"][0] - b.ox, entry["p"][2] - b.oz, 5.0))
        for entries in b.points.values():
            for entry in entries:
                self.points.append((entry["p"][0] - b.ox, entry["p"][2] - b.oz, 4.0))
        if b.lure:
            self.points.append((b.lure["p"][0] - b.ox, b.lure["p"][2] - b.oz, 5.0))
        self.mine: List[Tuple[float, float, float, float, float, float]] = []

    def free(self, x0: float, x1: float, y0: float, y1: float, z0: float, z1: float,
             margin: float = 1.5) -> bool:
        for f in self.boxes:
            if f[0] < x1 + margin and f[1] > x0 - margin and f[2] < y1 and f[3] > y0 and \
                    f[4] < z1 + margin and f[5] > z0 - margin:
                return False
        for f in self.mine:
            if f[0] < x1 - 1e-3 and f[1] > x0 + 1e-3 and f[2] < y1 - 1e-3 and f[3] > y0 + 1e-3 and \
                    f[4] < z1 - 1e-3 and f[5] > z0 + 1e-3:
                return False
        for (px, pz, r) in self.points:
            dx = max(x0 - px, 0.0, px - x1)
            dz = max(z0 - pz, 0.0, pz - z1)
            if dx * dx + dz * dz < r * r:
                return False
        return True

    def take(self, box: Tuple[float, float, float, float, float, float]) -> None:
        self.mine.append(box)


def _crags(b: Area, rng: random.Random, n0: int) -> None:
    """The rock coming out of the walls, hanging off the roofs and lying in
    heaps where it fell: no chamber is a box.

    Along every stretch of wall that is solid rock behind (never across a
    way through), crags a few strides wide: a ledge at the foot you step
    up on, often a shoulder above it you can jump to, and sometimes the
    rock going on up into the roof.  Lumps hang off the high ceilings, and
    in a few places the roof has come down in heaps you climb over."""
    clear = _Clear(b, n0)
    for (r, ceiling, floor, reach) in CRAGGY:
        _wall_crags(b, rng, clear, r, ceiling, floor, reach)
    for (r, ceiling) in LUMPY:
        _ceiling_lumps(b, rng, clear, r, ceiling)
    for (x, z, size) in HEAPS:
        _heap(b, rng, clear, x, z, size)


def _wall_crags(b: Area, rng: random.Random, clear: _Clear, r: Rect, ceiling: float, floor: float,
                reach: float) -> None:
    x0, x1, z0, z1 = r
    for side in ("x-", "x+", "z-", "z+"):
        along_z = side[0] == "x"
        lo, hi = (z0, z1) if along_z else (x0, x1)
        at = {"x-": x0, "x+": x1, "z-": z0, "z+": z1}[side]
        out = -0.5 if side[1] == "-" else 0.5
        # the solid stretches of this wall, a little in from their ends
        spans, start = [], None
        t = lo
        while t <= hi + 1e-6:
            solid = _in_rock(at + out, t) if along_z else _in_rock(t, at + out)
            if solid and start is None:
                start = t
            if (not solid or t + 1.0 > hi + 1e-6) and start is not None:
                end = t if solid else t - 1.0
                spans.append((start + reach + 1.0, end - reach - 1.0))
                start = None
            t += 1.0
        for a, c in spans:
            pos = a
            while c - pos >= 3.0:
                w = min(rng.uniform(5.0, 12.0), c - pos)
                if rng.random() < 0.2:
                    pos += w
                    continue
                _crag(b, rng, clear, side, at, pos, pos + w, ceiling, floor, reach)
                pos += w


def _crag(b: Area, rng: random.Random, clear: _Clear, side: str, at: float, a: float, c: float,
          ceiling: float, floor: float, reach: float) -> None:
    """One crag on a wall at ``at`` from ``a`` to ``c`` along it: tiers
    stacked on each other, each set further back and narrower."""
    inward = 1.0 if side[1] == "-" else -1.0
    flow = rng.random() < 0.15
    colours = ((FLOWSTONE, "#b8a888", "#a89878") if flow else (ROCK_LIGHT, ROCK, ROCK_DARK))
    depth = rng.uniform(2.0, reach)
    tiers = [(rng.uniform(1.4, 2.0), depth)]
    if rng.random() < 0.7 and depth > 2.2:
        tiers.append((rng.uniform(5.0, 9.0), depth - rng.uniform(0.8, 1.3)))
        if rng.random() < 0.45 and tiers[-1][1] > 1.8:
            tiers.append((ceiling + 0.5 - floor, tiers[-1][1] - rng.uniform(0.7, 1.1)))
    y = floor
    inset = 0.0
    for k, (top, d) in enumerate(tiers):
        y1 = floor + top
        if y1 <= y + 0.5:
            break
        ia, ic = a + inset, c - inset
        if ic - ia < 2.0:
            break
        lo_n, hi_n = (at, at + d) if inward > 0 else (at - d, at)
        if side[0] == "x":
            vis = (lo_n, hi_n, y + 0.01, min(y1, ceiling), ia, ic)
        else:
            vis = (ia, ic, y + 0.01, min(y1, ceiling), lo_n, hi_n)
        if not clear.free(*vis):
            break
        # the box itself runs half a unit back into the rock
        back_lo, back_hi = (at - 0.5, at + d) if inward > 0 else (at - d, at + 0.5)
        if side[0] == "x":
            cx, cz, sx, sz = (back_lo + back_hi) / 2.0, (ia + ic) / 2.0, back_hi - back_lo, ic - ia
        else:
            cx, cz, sx, sz = (ia + ic) / 2.0, (back_lo + back_hi) / 2.0, ic - ia, back_hi - back_lo
        b.box([cx, (y + y1) / 2.0, cz], [sx, y1 - y, sz], colours[min(k, 2)], studs=k < 2)
        clear.take(vis)
        y = y1
        inset += rng.uniform(0.4, 1.0)


def _ceiling_lumps(b: Area, rng: random.Random, clear: _Clear, r: Rect, ceiling: float) -> None:
    x0, x1, z0, z1 = r
    px, pz = PILLAR
    n = int((x1 - x0) * (z1 - z0) / 700.0)
    for _k in range(n * 3):
        if n <= 0:
            break
        w, d, h = rng.uniform(6.0, 16.0), rng.uniform(6.0, 16.0), rng.uniform(2.0, 5.0)
        cx, cz = rng.uniform(x0 + 2.0 + w / 2.0, x1 - 2.0 - w / 2.0), rng.uniform(z0 + 2.0 + d / 2.0, z1 - 2.0 - d / 2.0)
        if r == CATHEDRAL:
            e = math.hypot((cx - px) / 50.0, (cz - pz) / 40.0)
            if 0.7 < e < 1.3 or (abs(cx - 20.0) < 20.0 and abs(cz - 180.0) < 16.0):
                continue
        if r == RIVER and cx < -250.0:
            continue
        box = (cx - w / 2.0, cx + w / 2.0, ceiling - h - 1.0, ceiling, cz - d / 2.0, cz + d / 2.0)
        if not clear.free(*box, margin=1.0):
            continue
        b.box([cx, ceiling - h / 2.0 + 0.25, cz], [w, h + 0.5, d], ROCK_DARK if rng.random() < 0.6 else ROCK)
        clear.take(box)
        n -= 1


def _heap(b: Area, rng: random.Random, clear: _Clear, x: float, z: float, size: float) -> None:
    """Breakdown: blocks of fallen roof in a heap, each a step up on the
    one under it."""
    y = 0.0
    w, d = size, size * rng.uniform(0.7, 1.0)
    cx, cz = x, z
    for k in range(3):
        top = y + rng.uniform(1.4, 2.0)
        vis = (cx - w / 2.0, cx + w / 2.0, y + 0.01, top, cz - d / 2.0, cz + d / 2.0)
        if not clear.free(*vis, margin=1.5 if k == 0 else 0.0):
            break
        b.box([cx, (y + top) / 2.0, cz], [w, top - y, d], (ROCK_LIGHT, ROCK, "#8a8070")[k], studs=True)
        clear.take(vis)
        nw, nd = w * rng.uniform(0.5, 0.7), d * rng.uniform(0.5, 0.7)
        cx += rng.uniform(-1.0, 1.0) * (w - nw) / 2.0 * 0.8
        cz += rng.uniform(-1.0, 1.0) * (d - nd) / 2.0 * 0.8
        w, d, y = nw, nd, top
        if w < 3.0 or d < 3.0:
            break


# ================================================================ rigs
def _rigs(b: Area) -> None:
    px, pz = PILLAR
    b.rig("light_show", px, 30.0, pz, 0.0, lamps_path=[[x, y + 2.0, z] for (x, y, z) in PROJECTORS])
    b.rig("glowworms", (GROTTO[0] + GROTTO[1]) / 2.0, 16.0, (GROTTO[2] + GROTTO[3]) / 2.0, 0.0,
          area=list(GROTTO), pool=list(POOL), water=-0.8, n=180)
    b.rig("crystal_glow", -170.0, CRYSTAL_Y, 190.0, 0.0,
          points=[[-230.0, CRYSTAL_Y + 8.0, 150.0], [-240.0, CRYSTAL_Y + 12.0, 236.0], [-120.0, CRYSTAL_Y + 9.0, 240.0],
                  [-110.0, CRYSTAL_Y + 6.0, 140.0], [-160.0, CRYSTAL_Y + 12.0, 183.0], [-97.0, CRYSTAL_Y + 10.0, 183.0]])
    b.rig("cave_bats", 20.0, ROOF, 180.0, 0.0, n=24, q=[px, 30.0, pz])
    b.rig("mine_cart", 190.0, 0.3, 122.0, 0.0, x0=152.0, x1=230.0)
    b.rig("stuck_elevator", 0.0, 17.0, LIFT_Z, 0.0, cable=ROOF)
    b.rig("river_flow", 0.0, -1.4, 82.0, 0.0, area=list(CHANNEL), n=40)
    b.rig("falls", -279.0, 18.0, 82.0, 0.0, w=22.0, drop=19.4)
    b.rig("work_lamps", 204.0, 12.0, 160.0, 0.0,
          lamps=[[170.0, 12.0, 122.0], [226.0, 12.0, 122.0], [202.0, 12.0, 170.0], [202.0, 12.0, 230.0],
                 [244.0, 12.0, 160.0], [180.0, 12.0, 202.0]])
    b.rig("drip_rings", -100.0, -1.0, -95.0, 0.0,
          points=[[-136.0, -1.0, -95.0], [-128.0, -2.6, -110.0], [-120.0, -4.2, -80.0], [-100.0, -5.8, -95.0],
                  [-211.0, -0.8, -110.0], [-196.0, -0.8, -50.0]])
    b.rig("rope_rails", (PIT[0] + PIT[1]) / 2.0, 0.0, -60.0, 0.0, x0=PIT[0] - 1.0, x1=PIT[1] + 1.0, z0=-62.6, z1=-57.4)
    b.rig("lantern_glow", 176.0, PIT_FLOOR, -118.0, 0.0, points=[[176.0, PIT_FLOOR + 1.2, -118.0]])


# ============================================================== spawns
def _zombie_spawns(b: Area) -> None:
    for (x, z) in ((250.0, 122.0), (202.0, 250.0), (244.0, 140.0), (180.0, 202.0), (153.0, 222.0),
                   (250.0, -100.0), (240.0, 20.0), (100.0, 250.0), (60.0, 250.0), (120.0, 112.0),
                   (180.0, -240.0), (190.0, -200.0), (-250.0, -160.0), (-250.0, 0.0), (-270.0, 64.0),
                   (270.0, 100.0), (-30.0, 50.0), (-150.0, -45.0)):
        b.zombie_spawn(x, z, "")
    for (x, z) in ((-230.0, 250.0), (-130.0, 130.0), (-250.0, 130.0)):
        b.zombie_spawn(x, z, "", y=CRYSTAL_Y)
    for (x, z) in ((170.0, -40.0), (176.0, 20.0)):
        b.zombie_spawn(x, z, "", y=PIT_FLOOR)
    for (x, z) in ((-200.0, 82.0), (100.0, 82.0), (250.0, 82.0)):
        b.zombie_spawn(x, z, "water", y=-4.0)
    b.zombie_spawn(-225.0, -60.0, "water", y=-3.0)
    b.zombie_spawn(-100.0, -95.0, "water", y=-6.4)
