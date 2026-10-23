"""The pieces Calamity Coast's towns are built from: houses and shops a
person can shelter in, terraces and the stairs between them, towers with a
stair round the outside to a lookout, piers, palms and boats.

Everything a person can reach is solid and stands on something, the Last
Light way (app/game/maps/lastlight/kit.py).  The helpers put down the
*marks* the rules and the bots need as they build: a ``shelter`` under
every roof, a ``high`` place on every lookout.
"""
from __future__ import annotations

import math
import random
from typing import Optional, Sequence, Tuple

from ..kit import ArenaArea, building, flight, gable, letters, slab, threshold

Rect = Tuple[float, float, float, float]

WALL = 1.6                  # a town building's walls
FLOOR = 0.4                 # its floor pad (lastlight.kit.FLOOR)
DOOR_H = 8.6                # a doorway's head above the floor


def solid(b: ArenaArea, area: Rect, top: float, colour: str, edge: str = "",
          bottom: float = 0.0) -> None:
    """A block of ground standing ``top`` high (a terrace, a quay), with an
    optional coping strip along its top edges."""
    slab(b, area, top, top - bottom, colour)
    if edge:
        x0, x1, z0, z1 = area
        b.box([(x0 + x1) / 2.0, top + 0.15, (z0 + z1) / 2.0], [x1 - x0, 0.3, z1 - z0], edge,
              collide=False)


def stairs(b: ArenaArea, axis: str, near: float, far: float, lo: float, hi: float,
           y_near: float, y_far: float, colour: str, rails: str = "") -> None:
    """A straight flight between two levels; ``rails`` puts a handrail on
    each side (solid: they keep people on the stairs)."""
    flight(b, axis, near, far, lo, hi, y_near, y_far, colour, fill=min(y_near, y_far) - 0.3)
    if not rails:
        return
    top = max(y_near, y_far)
    length = abs(far - near)
    mid = (near + far) / 2.0
    for side in (lo - 0.3, hi + 0.3):
        if axis == "z":
            b.box([side, (top + 3.4 + min(y_near, y_far)) / 2.0, mid],
                  [0.6, top + 3.4 - min(y_near, y_far), length], rails)
        else:
            b.box([mid, (top + 3.4 + min(y_near, y_far)) / 2.0, side],
                  [length, top + 3.4 - min(y_near, y_far), 0.6], rails)


def house(b: ArenaArea, area: Rect, y0: float, colour: str, roof: str, door: str,
          height: float = 11.0, door_at: Optional[float] = None, windows: bool = True,
          gable_along: str = "", sign: str = "", sign_colours: Tuple[str, str] = ("#f4f0e8", "#2a2a2a"),
          shelter: bool = True, lights: str = "#fff0d0", tiers: int = 3,
          rng: Optional[random.Random] = None, furnish: bool = True) -> Tuple[float, float]:
    """A one-storey house or shop with a door on ``door`` ("x-", "x+", "z-",
    "z+"), glazed windows on the other sides and a stepped roof; a
    ``shelter`` mark inside.  Returns the doorway's centre (x, z)."""
    x0, x1, z0, z1 = area
    w, d = x1 - x0, z1 - z0
    along = (x0 + x1) / 2.0 if door in ("z-", "z+") else (z0 + z1) / 2.0
    c = door_at if door_at is not None else along
    span = (c - 3.0, c + 3.0)
    doors = {door: [(span[0], span[1], y0 + DOOR_H)]}
    win = {}
    if windows:
        sill, top = y0 + 3.4, y0 + 7.6
        for side in ("x-", "x+", "z-", "z+"):
            length = d if side in ("x-", "x+") else w
            lo = z0 if side in ("x-", "x+") else x0
            if length < 14.0:
                continue
            spots = [lo + length * 0.25, lo + length * 0.75]
            win[side] = [(s - 2.4, s + 2.4, sill, top) for s in spots
                         if side != door or abs(s - c) > 6.5]
    building(b, area, y0, height, colour, t=WALL, roof_colour=roof, roof_t=0.8,
             floor_colour="#8a7a64", doors=doors, windows=win, glass=True, lights=lights,
             studs_roof=False)
    threshold(b, area, door, span, WALL, y0)
    along_axis = gable_along or ("x" if w >= d else "z")
    gable(b, area, y0 + height + 0.8, roof, along_axis, tiers=tiers, rise=1.2, overhang=0.8)
    if sign:
        # a board over the door with the name in channel letters on it (a
        # name in one text decal blurs)
        bg, fg = sign_colours
        sw = min(w if door in ("z-", "z+") else d, 16.0) - 2.0
        y = y0 + DOOR_H + 1.6
        count = sum(0.55 if ch == " " else 1.0 for ch in sign)
        pitch = min(1.12, (sw - 0.6) / max(1.0, count))
        h = min(1.3, pitch / 0.86)
        if door == "z+":
            b.box([c, y, z1 + 0.3], [sw, 1.8, 0.6], bg)
            letters(b, c, y, z1 + 0.6, sign, h, bg, fg, "z+", depth=0.2, pitch=pitch)
        elif door == "z-":
            b.box([c, y, z0 - 0.3], [sw, 1.8, 0.6], bg)
            letters(b, c, y, z0 - 0.6, sign, h, bg, fg, "z-", depth=0.2, pitch=pitch)
        elif door == "x+":
            b.box([x1 + 0.3, y, c], [0.6, 1.8, sw], bg)
            letters(b, x1 + 0.6, y, c, sign, h, bg, fg, "x+", depth=0.2, pitch=pitch)
        else:
            b.box([x0 - 0.3, y, c], [0.6, 1.8, sw], bg)
            letters(b, x0 - 0.6, y, c, sign, h, bg, fg, "x-", depth=0.2, pitch=pitch)
    inner = (x0 + WALL, x1 - WALL, z0 + WALL, z1 - WALL)
    if furnish:
        _furnish(b, inner, y0 + FLOOR, door, rng or random.Random(int(x0 * 7 + z0 * 13)))
    if shelter:
        cx, cz = (inner[0] + inner[1]) / 2.0, (inner[2] + inner[3]) / 2.0
        # a little in from the door, clear of the table in the middle
        off = {"z+": (0.0, -0.22), "z-": (0.0, 0.22), "x+": (-0.22, 0.0), "x-": (0.22, 0.0)}[door]
        b.mark("shelter", cx + off[0] * (inner[1] - inner[0]), y0 + FLOOR,
               cz + off[1] * (inner[3] - inner[2]))
    if door == "z+":
        return c, z1
    if door == "z-":
        return c, z0
    if door == "x+":
        return x1, c
    return x0, c


def _furnish(b: ArenaArea, inner: Rect, y: float, door: str, rng: random.Random) -> None:
    """A table and two chairs in the room's far half, a cupboard on the
    back wall: enough to read as somebody's front room."""
    x0, x1, z0, z1 = inner
    w, d = x1 - x0, z1 - z0
    if w < 8.0 or d < 8.0:
        return
    back = {"z+": (0.0, -1.0), "z-": (0.0, 1.0), "x+": (-1.0, 0.0), "x-": (1.0, 0.0)}[door]
    cx, cz = (x0 + x1) / 2.0, (z0 + z1) / 2.0
    tx, tz = cx + back[0] * w * 0.18, cz + back[1] * d * 0.18
    wood = rng.choice(["#7a5335", "#8a6a4a", "#6a4a2a"])
    b.box([tx, y + 2.85, tz], [4.0, 0.3, 3.0], wood)
    for sx in (-1.6, 1.6):
        for sz in (-1.1, 1.1):
            b.box([tx + sx, y + 1.35, tz + sz], [0.4, 2.7, 0.4], wood)
    # the cupboard against the back wall
    if back[1]:
        bz = z0 + 1.0 if back[1] < 0 else z1 - 1.0
        b.box([cx, y + 3.0, bz], [5.0, 6.0, 2.0], wood)
    else:
        bx = x0 + 1.0 if back[0] < 0 else x1 - 1.0
        b.box([bx, y + 3.0, cz], [2.0, 6.0, 5.0], wood)


def lookout_tower(b: ArenaArea, cx: float, cz: float, y0: float, height: float,
                  colour: str, stair_colour: str, core: float = 12.0, width: float = 5.0,
                  cap: str = "", start: str = "z+", lantern: str = "",
                  bands: Sequence[str] = ()) -> float:
    """A square tower with a stair climbing once round the outside -- four
    flights, one up each face, with a landing at every corner -- to a
    railed gallery on top.  ``start`` is the face the first flight climbs.
    Returns the gallery's floor height (a ``high`` mark is put there)."""
    h = core / 2.0
    if bands:
        # painted in bands, a lighthouse's stripes: the core in stacked blocks
        n = max(2, int(height // 5.0))
        for k in range(n):
            ya, yb = y0 + height * k / n, y0 + height * (k + 1) / n
            b.box([cx, (ya + yb) / 2.0, cz], [core, yb - ya, core], bands[k % len(bands)])
    else:
        b.box([cx, y0 + height / 2.0, cz], [core, height, core], colour)
    rise = height / 4.0
    order = ["z+", "x+", "z-", "x-"]
    k0 = order.index(start)
    for k in range(4):
        face = order[(k0 + k) % 4]
        ya, yb = y0 + rise * k, y0 + rise * (k + 1)
        out = h + width / 2.0
        # each flight runs the length of its face from one corner to the next
        if face == "z+":
            flight(b, "x", cx - h, cx + h, cz + h, cz + h + width, ya, yb, stair_colour, fill=ya - 0.3)
            corner = (cx + out, cz + out)
        elif face == "x+":
            flight(b, "z", cz + h, cz - h, cx + h, cx + h + width, ya, yb, stair_colour, fill=ya - 0.3)
            corner = (cx + out, cz - out)
        elif face == "z-":
            flight(b, "x", cx + h, cx - h, cz - h - width, cz - h, ya, yb, stair_colour, fill=ya - 0.3)
            corner = (cx - out, cz - out)
        else:
            flight(b, "z", cz - h, cz + h, cx - h - width, cx - h, ya, yb, stair_colour, fill=ya - 0.3)
            corner = (cx - out, cz + out)
        if k < 3:
            b.box([corner[0], yb - 0.3, corner[1]], [width, 0.6, width], stair_colour)
    top = y0 + height
    gw = core + 2 * width
    b.box([cx, top + 0.3, cz], [gw, 0.6, gw], cap or colour)
    for side in (-1, 1):
        b.box([cx + side * (gw / 2.0 - 0.3), top + 2.2, cz], [0.6, 3.2, gw - 1.2], cap or colour)
        b.box([cx, top + 2.2, cz + side * (gw / 2.0 - 0.3)], [gw, 3.2, 0.6], cap or colour)
    if lantern:
        b.cyl([cx, top + 0.6 + 3.0, cz], [5.0, 6.0, 5.0], "#cfe8ff", material="glass", alpha=0.45)
        b.box([cx, top + 0.6 + 2.4, cz], [2.0, 2.4, 2.0], lantern, material="neon")
        b.box([cx, top + 0.6 + 0.6, cz], [3.0, 1.2, 3.0], "#3a3a3a", material="metal")
        b.cone([cx, top + 0.6 + 7.4, cz], [6.4, 2.8, 6.4], "#c8302a")
    b.mark("high", cx + core / 2.0 + width / 2.0 - 1.0, top + 0.6, cz)
    return top + 0.6


def palm(b: ArenaArea, x: float, z: float, y: float, h: float = 14.0,
         rng: Optional[random.Random] = None) -> None:
    """A palm: a leaning trunk of stacked rings and a crown of fronds high
    out of reach."""
    rng = rng or random.Random(int(x * 3 + z * 7))
    lean = rng.uniform(-0.12, 0.12), rng.uniform(-0.12, 0.12)
    n = int(h // 2.0)
    for k in range(n):
        f = k / float(n)
        b.cyl([x + lean[0] * h * f, y + 1.0 + k * 2.0, z + lean[1] * h * f],
              [1.3 - 0.4 * f, 2.0, 1.3 - 0.4 * f], "#8a6a44" if k % 2 else "#7a5a38")
    tx, tz = x + lean[0] * h, z + lean[1] * h
    top = y + n * 2.0
    b.sphere([tx, top + 0.4, tz], [1.8, 1.4, 1.8], "#6a5a2a")
    for a in range(6):
        ang = a * math.pi / 3.0 + rng.uniform(-0.2, 0.2)
        b.sphere([tx + math.cos(ang) * 3.4, top + 0.2, tz + math.sin(ang) * 3.4],
                 [6.2 if a % 2 else 5.4, 0.9, 2.2], "#3a8a3a", collide=False,
                 r=[0.0, -ang, 0.0])


def pier(b: ArenaArea, x0: float, x1: float, z0: float, z1: float, deck: float, bed: float,
         wood: str = "#8a6a44", post: str = "#5a4030", every: float = 8.0) -> None:
    """A timber pier: a deck on posts from the seabed."""
    slab(b, (x0, x1, z0, z1), deck, 0.6, wood)
    n = max(1, int((z1 - z0) // every))
    for k in range(n + 1):
        z = z0 + 0.6 + k * (z1 - z0 - 1.2) / n
        for x in (x0 + 0.6, x1 - 0.6):
            b.cyl([x, (bed + deck - 0.6) / 2.0, z], [1.0, deck - 0.6 - bed, 1.0], post)
    for x in (x0 + 0.3, x1 - 0.3):
        b.box([x, deck + 1.95, (z0 + z1) / 2.0], [0.5, 0.3, z1 - z0], post)
        for k in range(n + 1):
            z = z0 + 0.6 + k * (z1 - z0 - 1.2) / n
            b.box([x, deck + 0.9, z], [0.4, 1.8, 0.4], post)


def bollard(b: ArenaArea, x: float, z: float, y: float) -> None:
    b.cyl([x, y + 0.9, z], [1.2, 1.8, 1.2], "#2a2a2a", material="metal")
    b.cyl([x, y + 1.95, z], [1.6, 0.3, 1.6], "#2a2a2a", material="metal")


def crate_pile(b: ArenaArea, x: float, z: float, y: float, rng: random.Random,
               colour: str = "#a07a52") -> None:
    """Fish boxes and crates, stacked unevenly."""
    sizes = [(3.0, 2.0, 3.0), (2.6, 2.6, 2.6), (3.4, 1.6, 2.4)]
    k = 0
    for dx, dz in ((0.0, 0.0), (3.4, 0.4), (0.4, 3.2)):
        w, h, d = sizes[k % 3]
        b.box([x + dx, y + h / 2.0, z + dz], [w, h, d], colour, decal="planks")
        if rng.random() < 0.5:
            w2, h2, d2 = sizes[(k + 1) % 3]
            b.box([x + dx + 0.2, y + h + h2 / 2.0, z + dz - 0.1], [w2 - 0.6, h2, d2 - 0.6],
                  "#b88a5a", decal="planks")
        k += 1


def bench(b: ArenaArea, x: float, z: float, y: float, along: str = "x",
          wood: str = "#7a5335") -> None:
    if along == "x":
        b.box([x, y + 1.7, z], [6.0, 0.3, 2.0], wood)
        b.box([x, y + 2.8, z - 0.85], [6.0, 1.8, 0.3], wood)
        for sx in (-2.6, 2.6):
            b.box([x + sx, y + 0.775, z], [0.3, 1.55, 2.0], "#2a2a2a")
    else:
        b.box([x, y + 1.7, z], [2.0, 0.3, 6.0], wood)
        b.box([x - 0.85, y + 2.8, z], [0.3, 1.8, 6.0], wood)
        for sz in (-2.6, 2.6):
            b.box([x, y + 0.775, z + sz], [2.0, 1.55, 0.3], "#2a2a2a")


def street_lamp(b: ArenaArea, x: float, z: float, y: float, h: float = 12.0,
                colour: str = "#2a3a3a", light: str = "#ffe8b0") -> None:
    b.cyl([x, y + h / 2.0, z], [0.7, h, 0.7], colour, material="metal")
    b.box([x, y + h + 0.3, z], [1.8, 0.6, 1.8], colour, material="metal")
    b.box([x, y + h - 0.45, z], [1.2, 0.9, 1.2], light, material="neon")


def car(b: ArenaArea, x: float, z: float, y: float, along: str, colour: str) -> None:
    from ..kit import car as _car
    _car(b, x, z, along, colour=colour, y=y, length=10.0)


def helipad(b: ArenaArea, x: float, z: float, y: float, r: float = 12.0) -> None:
    """The evacuation point: a painted pad with lights round it."""
    b.cyl([x, y + 0.25, z], [r * 2.0, 0.5, r * 2.0], "#3a3e44")
    b.cyl([x, y + 0.52, z], [r * 1.7, 0.04, r * 1.7], "#f2c230", collide=False)
    b.cyl([x, y + 0.56, z], [r * 1.5, 0.04, r * 1.5], "#3a3e44", collide=False)
    # the H: two uprights and the bar between them
    b.box([x - 3.2, y + 0.6, z], [1.6, 0.04, 8.0], "#f4f4f4", collide=False)
    b.box([x + 3.2, y + 0.6, z], [1.6, 0.04, 8.0], "#f4f4f4", collide=False)
    b.box([x, y + 0.6, z], [4.8, 0.04, 1.6], "#f4f4f4", collide=False)
    for k in range(8):
        a = k * math.pi / 4.0
        lx, lz = x + math.cos(a) * (r - 0.6), z + math.sin(a) * (r - 0.6)
        b.box([lx, y + 0.8, lz], [0.6, 0.6, 0.6], "#7aff8a", material="neon")
    b.mark("evac", x, y + 0.5, z, r=r)


def skirt(b: ArenaArea, half_x: float, half_z: float, colour: str, reach: float = 220.0,
          top: float = -0.05) -> None:
    """Ground beyond the edge of the world, under the scenery out there, so
    the backdrop stands on something; a hair under the area's own ground
    (or under its seabed, where there is a sea)."""
    b.box([0.0, top - 1.0, 0.0], [2 * (half_x + reach), 2.0, 2 * (half_z + reach)], colour,
          collide=False)
