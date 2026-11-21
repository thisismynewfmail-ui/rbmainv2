"""Rooftops of Harrow Heights -- across the roofs, a snowy night in December.

Layout (north is +z); the streets are far below::

   z +280  [tower]          THE BROWNSTONES, the church         [tower]
   z  +96 ========= THE HIGH LINE (an old freight line, a park now, at 30) ====
   z  +72  THE           |  THE PENTHOUSE (30)  | THE ROOF GARDEN (26)  |  THE
           CONSTRUCTION  |  (the safe room)     | the water tower       |  DEPARTMENT
           SITE (a steel |------- alley --------+-------- alley --------|  STORE (30)
           frame, decks  |  THE BILLBOARD (34)  | THE FACTORY (22),     |  (the tree,
           to 40, the    |  (the lure)          | sawtooth roof         |   the sleigh)
   z  -72  crane)        |                      |                       |
   z  -96 ================ the south street ===================================
           [tower]         THE SKYLINE LOUNGE (26), the rooftop parking (16)  [tower]
   z -280

Everybody deploys in the penthouse, among the glass and the snow outside.

What makes it this place:

* **Up here.**  The fight is on the roofs: each building a different height,
  bridges of planks and steps across the alleys and the streets, a long way
  down to the street if you go over -- and the long stairs up from it.
* **The lure.**  On the tallest roof, the billboard: light it, and the
  giant neon cola bottle pours, buzzing, over the whole block -- the horde
  comes up for it.
* **High ground.**  The billboard's catwalk, the construction site's top
  deck, the High Line, the factory's sawtooth.
* **December.**  Snow on every roof, a tree on the department store with
  the sleigh and the reindeer, string lights over the lounge, steam off
  the vents.
"""
from __future__ import annotations

import math
import random
from typing import Dict, List, Tuple

from .kit import (
    BRICK, CONCRETE, CONCRETE_DARK, FLOOR, GLASS, HAZARD, STEEL, STEEL_DARK, WARM, WOOD, WOOD_DARK,
    WOOD_LIGHT, Area, Surfaces, barrel_spot, bench, boundary, building, car, carve, deploy_pad,
    flight, lamp_post, plate, rect, room_walls, sign_decal, slab, supply_ammo, supply_med,
    threshold, van, wall_sign)
from ..relay.kit import tier_stack

Rect = Tuple[float, float, float, float]

HALF = 280.0
SKY = {"top": "#0a0e1e", "horizon": "#3a3a52", "sun": [0.2, 0.5, -0.6],
       "clouds": 0.7, "tint": "#c8d0f0"}
AMBIENT = "#5a5e78"

SNOW = "#eef2f6"
STREET = "#5a5e66"
STONE = "#8a8478"

NW = rect(-86.0, -6.0, 6.0, 72.0)
NE = rect(6.0, 86.0, 6.0, 72.0)
SW = rect(-86.0, -6.0, -72.0, -6.0)
SE = rect(6.0, 86.0, -72.0, -6.0)
H_NW, H_NE, H_SW, H_SE = 28.0, 26.0, 34.0, 22.0
STORE = rect(110.0, 240.0, -66.0, 66.0)
H_STORE = 30.0
BAR = rect(-86.0, 86.0, -160.0, -96.0)
H_BAR = 26.0
ANNEX = rect(-86.0, 86.0, -230.0, -160.0)
H_ANNEX = 16.0
FRAME = rect(-170.0, -110.0, -50.0, 50.0)
HIGHLINE = rect(-280.0, 280.0, 76.0, 92.0)
H_LINE = 30.0
BROWN = rect(-86.0, 86.0, 104.0, 140.0)
PENT = rect(-76.0, -26.0, 22.0, 60.0)


def build(b: Area) -> None:
    rng = random.Random(0x5EA7)
    b.extra.update({"weather": "snow", "accent": "#e83a4a"})
    s = Surfaces(b)
    _ground(b, s)
    boundary(b, 30.0, "#1c222b", "#181d24", rng, horizon="city")
    _towers(b, s, rng)
    _central(b, s, rng)
    _penthouse(b)
    _garden(b)
    _billboard(b)
    _factory(b)
    _bridges(b)
    _store(b, s, rng)
    _lounge(b, s, rng)
    _highline(b, s, rng)
    _brownstones(b, s, rng)
    _construction(b, s)
    _streets(b, s, rng)
    _rigs(b)
    _zombie_spawns(b)
    for x, z, name in ((-51, 41, "the penthouse"), (-46, -40, "the billboard"), (46, 40, "the roof garden"),
                       (70, 60, "the water tower"), (46, -40, "the factory roof"), (0, 84, "the high line"),
                       (-140, 0, "the construction site"), (-200, 0, "the crane"), (175, 0, "the department store"),
                       (175, 30, "the christmas tree"), (0, -128, "the skyline lounge"), (40, -120, "the hot tub"),
                       (0, -200, "the rooftop parking"), (0, -84, "the south street"), (98, 0, "the east street"),
                       (0, 0, "the alleys"), (0, 120, "the brownstones")):
        b.landmark(float(x), float(z), name)
    b.camera(-40.0, 48.0, -120.0, 0.0, 30.0, 0.0)
    b.camera(60.0, 36.0, 0.0, -46.0, 42.0, -40.0)
    b.camera(-100.0, 44.0, 60.0, -150.0, 20.0, 0.0)
    b.camera(100.0, 40.0, -40.0, 175.0, 36.0, 30.0)


# ================================================================ helpers
def _block(b: Area, r: Rect, h: float, colour: str, rng: random.Random, gaps: Dict[str, list] = None,
           lit: float = 0.3, parapet: bool = True, roof_colour: str = SNOW) -> None:
    """A solid building: its body, a skin of snow on the roof (its top at
    ``h``), a few windows lit on its faces, a parapet with gaps."""
    x0, x1, z0, z1 = r
    b.box([(x0 + x1) / 2.0, (h - 0.4) / 2.0, (z0 + z1) / 2.0], [x1 - x0, h - 0.4, z1 - z0], colour)
    slab(b, r, h, 0.4, roof_colour, studs=True)
    for side in ("x-", "x+", "z-", "z+"):
        along = side in ("z-", "z+")
        lo, hi = (x0, x1) if along else (z0, z1)
        face = {"x-": x0, "x+": x1, "z-": z0, "z+": z1}[side]
        out = -1.0 if side in ("x-", "z-") else 1.0
        rows = int((h - 6.0) // 7.0)
        cols = int((hi - lo - 6.0) // 9.0)
        for i in range(rows):
            for j in range(cols):
                if rng.random() > lit:
                    continue
                u = lo + 5.0 + j * 9.0 + 2.0
                y = 5.0 + i * 7.0 + 1.5
                c = rng.choice(["#ffd27a", "#ffe8b0", "#cfe8ff", "#ffb35a"])
                if along:
                    b.box([u, y, face + out * 0.06], [3.0, 3.0, 0.12], c, material="neon", collide=False)
                else:
                    b.box([face + out * 0.06, y, u], [0.12, 3.0, 3.0], c, material="neon", collide=False)
    if parapet:
        room_walls(b, r, 0.8, h, h + 1.2, colour,
                   doors={side: [(a, c, h + 1.2) for a, c in spans] for side, spans in (gaps or {}).items()})


def _steps(b: Area, axis: str, a: float, c: float, lo: float, hi: float, y_a: float, y_c: float,
           colour: str = WOOD) -> None:
    """A bridge of planks across a gap from ``a`` (at ``y_a``) to ``c`` (at
    ``y_c``), stepping two units at a time where the ends differ."""
    n = max(1, int(round(abs(y_c - y_a) / 2.0)) + 1)
    run = (c - a) / n
    for k in range(n):
        y = y_a + (y_c - y_a) * (k / max(1, n - 1)) if n > 1 else y_a
        p, q = sorted((a + run * k, a + run * (k + 1)))
        if axis == "x":
            slab(b, rect(p, q, lo, hi), y, 0.6, colour, studs=True)
        else:
            slab(b, rect(lo, hi, p, q), y, 0.6, colour, studs=True)


# ================================================================ ground
def _ground(b: Area, s: Surfaces) -> None:
    h = b.half + b.margin
    plate(b, [rect(-h, h, -h, h)], 0.0, 0.6, STREET, studs=True)
    plate(b, [rect(-h, h, -h, h)], -0.6, 5.4, "#3a3a3a")


def _towers(b: Area, s: Surfaces, rng: random.Random) -> None:
    """The towers in the corner blocks: tall, dark, a few windows lit --
    the city all round; nobody gets up those."""
    for (r, h, c) in ((rect(-280.0, -160.0, 110.0, 280.0), 96.0, "#2a2e38"), (rect(160.0, 280.0, 110.0, 280.0), 84.0, "#30343e"),
                      (rect(-280.0, -110.0, -280.0, -110.0), 72.0, "#2a2e38"), (rect(110.0, 280.0, -280.0, -110.0), 104.0, "#262a34")):
        s.reserve(r)
        _block(b, r, h, c, rng, lit=0.22, parapet=False, roof_colour="#3a3e48")


def _central(b: Area, s: Surfaces, rng: random.Random) -> None:
    """The central block: four buildings of four heights round the alleys."""
    for r in (NW, NE, SW, SE):
        s.reserve(r)
    _block(b, NW, H_NW, BRICK, rng, gaps={"x+": [(40.0, 46.0), (60.0, 66.0)], "z-": [(-60.0, -54.0)], "x-": [(30.0, 36.0)],
                                          "z+": [(-50.0, -40.0)]})
    _block(b, NE, H_NE, "#8a6a52", rng, gaps={"x-": [(60.0, 66.0)], "z-": [(50.0, 56.0)], "x+": [(40.0, 46.0)],
                                               "z+": [(40.0, 50.0)]})
    _block(b, SW, H_SW, "#5a5e6a", rng, gaps={"z+": [(-60.0, -54.0)], "x+": [(-40.0, -34.0)]})
    _block(b, SE, H_SE, "#7a5a4a", rng, gaps={"z+": [(50.0, 56.0)], "x-": [(-40.0, -34.0)], "x+": [(-54.0, -48.0)],
                                               "z-": [(40.0, 46.0)]})
    # the stairs up from the alley and the street
    flight(b, "z", 10.0, 46.0, -6.0, 0.0, 0.0, H_NW, STEEL_DARK, fill=0.0)
    flight(b, "z", -10.0, -54.0, 86.0, 92.0, 0.0, H_SE, STEEL_DARK, fill=0.0)


def _penthouse(b: Area) -> None:
    """The penthouse on the brick building's roof: glass on every side, a
    terrace in the snow -- the safe room."""
    x0, x1, z0, z1 = PENT
    y = H_NW
    building(b, PENT, y, 12.0, "#e8e8e0", roof_colour="#3a3a42", floor_colour="#8a7a62",
             doors={"z-": [(-56.0, -46.0, y + 9.0)], "x+": [(36.0, 46.0, y + 9.0)]},
             windows={"z-": [(-74.0, -60.0, y + 2.0, y + 10.0), (-42.0, -28.0, y + 2.0, y + 10.0)],
                      "z+": [(-74.0, -52.0, y + 2.0, y + 10.0), (-48.0, -28.0, y + 2.0, y + 10.0)],
                      "x-": [(26.0, 56.0, y + 2.0, y + 10.0)]},
             glass=True, lights=WARM)
    threshold(b, PENT, "z-", (-56.0, -46.0), y0=y)
    threshold(b, PENT, "x+", (36.0, 46.0), y0=y)
    floor = y + FLOOR
    for z in (50.0, 40.0):
        for k in range(8):
            x = -71.0 + k * 5.4
            deploy_pad(b, x, z, floor, "#e83a4a", 4.6)
            b.safe_spawn(x, floor + 0.6, z, math.pi)
    b.box([-72.0, floor + 1.0, 30.0], [4.0, 2.0, 10.0], "#3a3a42")
    supply_ammo(b, -40.0, floor, 27.0, "z+")
    supply_med(b, -32.0, floor, 26.4, "z+")
    wall_sign(b, -51.0, y + 13.6, z1 + 0.35, 18.0, 1.6, sign_decal("THE HEIGHTS", "#e8e8e0", "#1a1a2a", 11.2), "z+",
              "#e8e8e0")
    for (x, z) in ((-80.0, 12.0), (-20.0, 12.0)):
        b.box([x, y + 1.2, z], [3.0, 2.4, 3.0], "#5a4a3a")
        b.sphere([x, y + 3.8, z], [3.6, 3.2, 3.6], "#2a4a2a", collide=False)
    barrel_spot(b, -14.0, y, 66.0)


def _garden(b: Area) -> None:
    """The roof garden: planters under snow, a greenhouse frame, benches, the
    water tower on its legs, the stair bulkhead."""
    y = H_NE
    for (x, z) in ((20.0, 20.0), (36.0, 20.0), (20.0, 36.0), (36.0, 36.0)):
        b.box([x, y + 0.8, z], [10.0, 1.6, 10.0], WOOD_DARK)
        slab(b, rect(x - 4.4, x + 4.4, z - 4.4, z + 4.4), y + 1.9, 0.3, SNOW)
    gx0, gx1, gz0, gz1 = 50.0, 70.0, 14.0, 30.0
    for x in (gx0, gx1):
        for z in (gz0, gz1):
            b.box([x, y + 4.0, z], [0.6, 8.0, 0.6], "#e8e8e8")
    slab(b, rect(gx0 - 0.3, gx1 + 0.3, gz0 - 0.3, gz1 + 0.3), y + 8.4, 0.4, GLASS, material="glass", alpha=0.4)
    bench(b, 28.0, 50.0, "x", y=y)
    bench(b, 28.0, 60.0, "x", y=y)
    wx, wz = 70.0, 60.0
    for dx in (-4.0, 4.0):
        for dz in (-4.0, 4.0):
            b.box([wx + dx, y + 5.0, wz + dz], [1.0, 10.0, 1.0], WOOD_DARK)
    slab(b, rect(wx - 5.0, wx + 5.0, wz - 5.0, wz + 5.0), y + 10.6, 0.6, WOOD_DARK)
    b.cyl([wx, y + 10.6 + 6.0, wz], [12.0, 12.0, 12.0], "#8a6a4a")
    b.cone([wx, y + 10.6 + 12.0 + 2.0, wz], [13.0, 4.0, 13.0], "#5a4a3a", collide=False)
    b.box([16.0, y + 4.0, 66.0], [8.0, 8.0, 8.0], "#7a5a4a")
    supply_ammo(b, 50.0, y, 46.0, "z+")
    supply_med(b, 78.0, y, 30.0, "x-")


def _billboard(b: Area) -> None:
    """The billboard on the tallest roof: legs, the board, the catwalk along
    its foot with its stair, the switch box -- the lure."""
    y = H_SW
    for x in (-70.0, -46.0, -22.0):
        for z in (-50.0, -44.0):
            b.box([x, y + 12.0, z], [1.2, 24.0, 1.2], STEEL_DARK, material="metal")
    b.box([-46.0, y + 16.0, -51.0], [56.0, 16.0, 1.2], "#1a1a22")
    slab(b, rect(-74.0, -18.0, -49.4, -45.0), y + 7.6, 0.6, STEEL, studs=True, material="metal")
    flight(b, "x", -10.0, -18.0, -49.4, -45.0, y, y + 7.6, STEEL_DARK, fill=y)
    b.box([-46.0, y + 7.6 + 0.6, -45.3], [56.0, 1.2, 0.6], HAZARD)
    b.box([-46.0, y + 1.6, -34.0], [4.0, 3.2, 2.0], "#4a5060", material="metal")
    b.set_lure(-46.0, y, -31.0, "the billboard", "Light the billboard", "ll_neon", (-46.0, y, -40.0))
    wall_sign(b, -46.0, y + 1.6, -32.65, 3.6, 1.2, sign_decal("POWER", "#4a5060", HAZARD, 3.0), "z+", "#4a5060")
    supply_ammo(b, -60.0, y, -20.0, "z+")
    barrel_spot(b, -78.0, y, -20.0)


def _factory(b: Area) -> None:
    """The factory's sawtooth roof: ridges of steps running east-west, the
    glass on their north faces, the vent stacks."""
    x0, x1, z0, z1 = SE
    y = H_SE
    for k, zc in enumerate((-60.0, -40.0, -20.0)):
        tiers = [[rect(x0 + 8.0, x1 - 8.0, zc - 6.0, zc + 6.0)], [rect(x0 + 8.0, x1 - 8.0, zc - 6.0, zc + 2.0)],
                 [rect(x0 + 8.0, x1 - 8.0, zc - 6.0, zc - 2.0)]]
        tier_stack(b, tiers, y, [2.0], ["#9a9a92", "#8a8a82"])
        b.box([(x0 + x1) / 2.0, y + 4.0, zc + 2.0 + 0.1], [x1 - x0 - 16.0, 2.0, 0.2], "#8ab8c8", material="glass",
              alpha=0.6)
    for (x, z) in ((16.0, -10.0), (76.0, -10.0)):
        b.cyl([x, y + 5.0, z], [2.4, 10.0, 2.4], STEEL_DARK, material="metal")
    supply_med(b, 76.0, y, -68.6, "z+")
    barrel_spot(b, 12.0, y, -66.0)


def _bridges(b: Area) -> None:
    """Across the alleys and the streets: planks, stepping where the roofs
    differ."""
    _steps(b, "x", -6.0, 6.0, 60.0, 66.0, H_NW, H_NE)
    _steps(b, "z", -6.0, 6.0, -60.0, -54.0, H_SW, H_NW)
    _steps(b, "z", 6.0, -6.0, 50.0, 56.0, H_NE, H_SE)
    _steps(b, "x", -6.0, 6.0, -40.0, -34.0, H_SW, H_SE)
    _steps(b, "x", -110.0, -86.0, 30.0, 36.0, H_NW, H_NW)
    _steps(b, "x", 86.0, 110.0, 40.0, 46.0, H_NE, H_STORE, STEEL)
    _steps(b, "z", -72.0, -96.0, 40.0, 46.0, H_SE, H_BAR)
    _steps(b, "z", 72.0, 76.0, -50.0, -40.0, H_NW, H_LINE)
    _steps(b, "z", 72.0, 76.0, 40.0, 50.0, H_NE, H_LINE)


def _store(b: Area, s: Surfaces, rng: random.Random) -> None:
    """The department store: its roof dressed for Christmas -- the tree, the
    sleigh and the reindeer up on the parapet -- and its name in lights."""
    s.reserve(STORE)
    _block(b, STORE, H_STORE, "#a85a4a", rng, gaps={"x-": [(40.0, 46.0)], "z-": [(200.0, 206.0)]})
    flight(b, "x", 236.0, 200.0, -72.0, -66.0, 0.0, H_STORE, STEEL_DARK, fill=0.0)
    y = H_STORE
    tx, tz = 175.0, 30.0
    b.cyl([tx, y + 2.0, tz], [2.4, 4.0, 2.4], WOOD_DARK)
    for k in range(5):
        b.cone([tx, y + 4.0 + k * 4.0 + 2.5, tz], [18.0 - k * 3.4, 6.0, 18.0 - k * 3.4], "#2a5a2a", collide=False)
    # the sleigh
    sx, sz = 150.0, -30.0
    b.box([sx, y + 1.9, sz], [6.0, 2.6, 12.0], "#a8182a")
    b.box([sx, y + 4.2, sz - 4.0], [6.0, 2.0, 2.0], "#a8182a")
    for dx in (-2.6, 2.6):
        b.box([sx + dx, y + 0.3, sz], [0.6, 0.6, 14.0], "#d8b84a", material="metal")
    wall_sign(b, 175.0, y - 3.0, 66.35, 60.0, 5.0, sign_decal("HARROW & SONS", "#a85a4a", "#fff2c8", 12.0), "z+",
              "#a85a4a")
    supply_ammo(b, 220.0, y, 50.0, "x-")
    supply_med(b, 120.0, y, -56.6, "z+")
    barrel_spot(b, 230.0, y, -50.0)


def _lounge(b: Area, s: Surfaces, rng: random.Random) -> None:
    """The Skyline Lounge on the south roof: the canopy, the bar, the hot
    tub, the chairs, the dance floor under string lights; behind it, down a
    stair, the rooftop parking with cars nobody will drive down again."""
    s.reserve(BAR)
    s.reserve(ANNEX)
    _block(b, BAR, H_BAR, "#6a5a7a", rng, gaps={"z+": [(40.0, 46.0)], "z-": [(-20.0, -12.0)], "x-": [(-136.0, -130.0)]})
    _block(b, ANNEX, H_ANNEX, CONCRETE, rng, gaps={"z+": [(-20.0, -12.0)]}, lit=0.15)
    y = H_BAR
    flight(b, "z", -176.0, -160.0, -20.0, -12.0, H_ANNEX, H_BAR, CONCRETE_DARK, fill=H_ANNEX)
    flight(b, "z", -100.0, -136.0, -92.0, -86.0, 0.0, H_BAR, STEEL_DARK, fill=0.0)
    for x in (-40.0, -10.0, 20.0):
        for z in (-140.0, -116.0):
            b.box([x, y + 5.0, z], [0.8, 10.0, 0.8], "#2a2a32")
    slab(b, rect(-44.0, 24.0, -144.0, -112.0), y + 10.6, 0.6, "#2a2a32")
    b.box([-30.0, y + 1.6, -136.0], [20.0, 3.2, 2.4], "#3a2a3a", studs=True)
    hx0, hx1, hz0, hz1 = 34.0, 46.0, -126.0, -114.0
    for (a, c, d, e) in ((hx0, hx1, hz0, hz0 + 0.8), (hx0, hx1, hz1 - 0.8, hz1), (hx0, hx0 + 0.8, hz0 + 0.8, hz1 - 0.8),
                         (hx1 - 0.8, hx1, hz0 + 0.8, hz1 - 0.8)):
        b.box([(a + c) / 2.0, y + 1.2, (d + e) / 2.0], [c - a, 2.4, e - d], "#c8c8d0")
    slab(b, rect(hx0 + 0.8, hx1 - 0.8, hz0 + 0.8, hz1 - 0.8), y + 0.8, 0.8, "#3a8ab8")
    b.water((hx0 + hx1) / 2.0, (hz0 + hz1) / 2.0, hx1 - hx0 - 1.6, hz1 - hz0 - 1.6, y + 2.0, "#3a9ac8")
    for k in range(4):
        b.box([-60.0 + k * 8.0, y + 0.6, -104.0], [3.0, 1.2, 6.0], "#e8e8e8")
    slab(b, rect(-20.0, 10.0, -130.0, -118.0), y + 0.2, 0.2, "#2a2a4a", collide=False)
    wall_sign(b, 0.0, y - 3.0, -95.65, 40.0, 4.0, sign_decal("SKYLINE LOUNGE", "#6a5a7a", "#ff8ad8", 10.0), "z+",
              "#6a5a7a")
    supply_ammo(b, -70.0, y, -150.0, "z+")
    supply_med(b, 70.0, y, -153.4, "z+")
    # the parked cars up on the annex
    for k, (x, z) in enumerate(((-60.0, -200.0), (-30.0, -200.0), (30.0, -190.0), (60.0, -210.0))):
        car(b, x, z, "z", ["#8a2a24", "#3a5a6a", "#e8e8e8", "#2a3a2a"][k], length=11.0, y=H_ANNEX)
    barrel_spot(b, 0.0, H_ANNEX, -215.0)
    barrel_spot(b, -50.0, y, -100.0)


def _highline(b: Area, s: Surfaces, rng: random.Random) -> None:
    """The High Line: the old freight viaduct along the north street, a park
    now -- planters, benches, a rail on each side with gaps for the bridges;
    stairs down to the street at both ends."""
    x0, x1, z0, z1 = HIGHLINE
    slab(b, HIGHLINE, H_LINE, 1.2, CONCRETE_DARK)
    slab(b, rect(x0, x1, z0 + 0.8, z1 - 0.8), H_LINE + 0.3, 0.3, SNOW, studs=True)
    for x in range(-260, 270, 40):
        for z in (78.0, 90.0):
            b.box([float(x), (H_LINE - 1.2) / 2.0, z], [2.4, H_LINE - 1.2, 2.4], STEEL_DARK)
    rail_gaps = {z0: [(-50.0, -40.0), (40.0, 50.0)], z1: [(-150.0, -144.0), (6.0, 12.0), (144.0, 150.0)]}
    for z, gaps in rail_gaps.items():
        zc = z + 0.4 if z == z0 else z - 0.4
        cursor = x0
        for (a, c) in sorted(gaps) + [(x1, x1)]:
            if a > cursor:
                b.box([(cursor + a) / 2.0, H_LINE + 0.6, zc], [a - cursor, 1.2, 0.8], STEEL_DARK)
            cursor = c
    for k, x in enumerate((-200.0, -110.0, 0.0, 110.0, 200.0)):
        b.box([x, H_LINE + 0.3 + 0.8, 84.0], [8.0, 1.6, 4.0], WOOD_DARK)
        slab(b, rect(x - 3.6, x + 3.6, 82.4, 85.6), H_LINE + 0.3 + 1.9, 0.3, SNOW)
        bench(b, x + 14.0, 84.0, "x", y=H_LINE + 0.3)
    flight(b, "x", 114.0, 150.0, z1, z1 + 6.0, 0.0, H_LINE + 0.3, STEEL_DARK, fill=0.0)
    flight(b, "x", -114.0, -150.0, z1, z1 + 6.0, 0.0, H_LINE + 0.3, STEEL_DARK, fill=0.0)
    supply_ammo(b, 60.0, H_LINE + 0.3, 84.0, "x+")
    barrel_spot(b, -60.0, H_LINE + 0.3, 84.0)


def _brownstones(b: Area, s: Surfaces, rng: random.Random) -> None:
    """A row of brownstones along the north street, each its own height, the
    pigeon coop on one of them; the church spire behind."""
    x0, x1, z0, z1 = BROWN
    s.reserve(rect(x0, x1, z0, 280.0))
    for k in range(6):
        a = x0 + k * (x1 - x0) / 6.0
        r = rect(a, a + (x1 - x0) / 6.0, z0, z1)
        h = [18.0, 20.0, 22.0, 20.0, 18.0, 22.0][k]
        _block(b, r, h, ["#6a3a2a", "#7a4a32", "#5a3424"][k % 3], rng, parapet=False, lit=0.4)
    b.box([-14.0, 22.0 + 3.0, 122.0], [10.0, 6.0, 8.0], WOOD)
    flight(b, "z", 104.0, 92.0, 6.0, 12.0, 20.0, H_LINE + 0.3, STEEL_DARK, fill=0.0)
    b.box([0.0, 14.0, 210.0], [80.0, 28.0, 80.0], STONE)
    b.box([0.0, 28.0 + 15.0, 180.0], [14.0, 30.0, 14.0], STONE)
    b.cone([0.0, 58.0 + 12.0, 180.0], [14.0, 24.0, 14.0], "#4a4a52", collide=False)
    b.box([0.0, 58.0 + 24.0 + 3.0, 180.0], [0.6, 6.0, 0.6], "#d8b84a", collide=False)


def _construction(b: Area, s: Surfaces) -> None:
    """The construction site west of the block: a steel frame going up, its
    decks of planks at ten, twenty, thirty and forty with stairs between,
    the yard round it, the tower crane."""
    s.reserve(rect(-280.0, -110.0, -72.0, 72.0))
    x0, x1, z0, z1 = FRAME
    for x in (-168.0, -149.0, -130.0, -111.2):
        for z in (-48.0, -24.0, 0.0, 24.0, 48.0):
            b.box([x, 22.0, z], [1.2, 44.0, 1.2], "#c86a2a", material="metal")
    decks = [(10.0, [rect(x0, x1, z0, z1)]), (20.0, [rect(x0, x1, z0, 26.0)]), (30.0, [rect(x0, x1, -26.0, z1)]),
             (40.0, [rect(-150.0, x1, -26.0, 26.0)])]
    for y, rs in decks:
        for r in rs:
            plate(b, carve(r, _frame_holes(y)), y, 0.6, WOOD_LIGHT, studs=True)
    flight(b, "x", -200.0, x0, -50.0, -44.0, 0.0, 10.0, STEEL_DARK, fill=0.0)
    flight(b, "z", 40.0, 26.0, -160.0, -154.0, 10.0, 20.0, STEEL_DARK, fill=10.0)
    flight(b, "z", -40.0, -26.0, -128.0, -122.0, 20.0, 30.0, STEEL_DARK, fill=20.0)
    flight(b, "x", -164.0, -150.0, 10.0, 16.0, 30.0, 40.0, STEEL_DARK, fill=30.0)
    # the yard: stacks of girders, the site office, the crane
    for (x, z) in ((-200.0, -60.0), (-240.0, 30.0)):
        for k in range(3):
            b.box([x, 0.6 + k * 1.2, z], [24.0, 1.2, 7.4 - k * 2.0], "#c86a2a", material="metal")
    so = rect(-260.0, -230.0, -66.0, -50.0)
    building(b, so, 0.0, 9.0, "#d8c83a", roof_colour="#5a5a5a", floor_colour="#6a6a62",
             doors={"z+": [(-250.0, -242.0, 7.0)]}, windows={"z+": [(-238.0, -233.0, 3.6, 6.4)]}, glass=True, lights=WARM)
    threshold(b, so, "z+", (-250.0, -242.0))
    b.box([-200.0, 30.0, 0.0], [3.0, 60.0, 3.0], "#e8c83a", material="metal")
    b.box([-200.0, 61.0, 0.0], [5.0, 2.0, 5.0], "#e8c83a", material="metal")
    supply_ammo(b, -140.0, 40.0, 0.0, "x+")
    supply_med(b, -250.0, FLOOR, -62.6, "z+")
    barrel_spot(b, -130.0, 10.0, -40.0)


def _frame_holes(y: float) -> List[Rect]:
    """Where a deck is left open above a stair coming up through it."""
    if y == 20.0:
        return [rect(-160.0, -154.0, 26.0, 40.0)]
    if y == 30.0:
        return [rect(-128.0, -122.0, -40.0, -26.0)]
    if y == 40.0:
        return [rect(-164.0, -150.0, 10.0, 16.0)]
    return []


def _streets(b: Area, s: Surfaces, rng: random.Random) -> None:
    """The streets far below: snow at the kerbs, cars left where they
    stopped, a bus, the hot dog cart, the newsstand, lamps."""
    for (x, z, along, c) in ((-98.0, -30.0, "z", "#e8c83a"), (98.0, 20.0, "z", "#3a5a8a"), (-40.0, -84.0, "x", "#8a2a24"),
                             (30.0, -84.0, "x", "#e8e8e8"), (-160.0, -84.0, "x", "#5a3a6a")):
        car(b, x, z, along, c, length=11.0, wrecked=rng.random() < 0.3)
    van(b, 160.0, -84.0, "x", "#c8c8c0")
    b.box([0.0, 2.0, -79.0], [3.0, 4.0, 5.0], "#c8382a")
    b.box([0.0, 4.6, -79.0], [4.0, 1.2, 6.0], "#f2d23a")
    b.box([-98.0, 4.0, 60.0], [5.0, 8.0, 3.0], "#2a5a3a")
    for (x, z) in ((-108.0, -60.0), (-108.0, 60.0), (108.0, -60.0), (108.0, 60.0), (-60.0, -74.0), (60.0, -74.0),
                   (-60.0, -94.0), (60.0, -94.0)):
        lamp_post(b, x, z, h=12.0, light=WARM)


# ================================================================ rigs
def _rigs(b: Area) -> None:
    b.rig("billboard_neon", -46.0, H_SW + 16.0, -50.3, 0.0, w=54.0, h=15.0)
    b.rig("christmas_lights", 175.0, H_STORE + 4.0, 30.0, 0.0, levels=5)
    b.rig("reindeer", 150.0, H_STORE, -18.0, 0.0, n=4)
    b.rig("string_lights", -10.0, H_BAR + 10.0, -128.0, 0.0,
          poles=[[-40.0, -140.0], [20.0, -140.0], [20.0, -116.0], [-40.0, -116.0]])
    b.rig("steam_vents", 0.0, 0.0, 0.0, 0.0,
          points=[[16.0, H_SE + 10.0, -10.0], [76.0, H_SE + 10.0, -10.0], [40.0, H_BAR + 2.0, -120.0],
                  [0.0, 0.0, -84.0], [-98.0, 0.0, 20.0], [98.0, 0.0, -30.0]])
    b.rig("crane_jib", -200.0, 62.0, 0.0, 0.0, r=60.0)
    b.rig("pigeons", -14.0, 26.0, 122.0, 0.0, n=8)
    b.rig("searchlights", 0.0, 0.0, 0.0, 0.0, lights=[[130.0, -50.0], [220.0, 50.0]], aim=[175.0, 140.0, 0.0],
          y0=H_STORE + 2.0)
    b.rig("moth_swarm", -60.0, 10.0, -94.0, 0.0)


# ============================================================== spawns
def _zombie_spawns(b: Area) -> None:
    for (x, z) in ((-98.0, -60.0), (-98.0, -150.0), (98.0, -60.0), (98.0, 60.0), (-60.0, -84.0), (60.0, -84.0),
                   (-160.0, -84.0), (170.0, -84.0), (-250.0, -84.0), (250.0, -84.0), (-240.0, 84.0), (60.0, 84.0),
                   (-200.0, 84.0), (200.0, 84.0), (0.0, -40.0), (0.0, -60.0), (-200.0, -40.0), (-230.0, 40.0),
                   (260.0, 0.0), (-98.0, -200.0), (98.0, -200.0), (-98.0, 200.0), (98.0, 200.0)):
        b.zombie_spawn(x, z, "")
    for (x, z, y) in ((200.0, 84.0, H_LINE + 0.3), (-80.0, -66.0, H_SW), (230.0, 60.0, H_STORE)):
        b.zombie_spawn(x, z, "", y=y)
