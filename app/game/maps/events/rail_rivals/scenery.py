"""Scenery the railroads built since the first four share: locomotives on
show, camps, trestles, the high country's junipers and sage, bunting.

Everything here takes a ``base`` -- the height of the ground it stands on
-- because the newer lines run over rolling land (land.py) as often as
over the flat.  The rules are the kit's: solids abut, never overlap; what a
body can walk into is solid; thin things lie flat on something.
"""
from __future__ import annotations

import math
import random
from typing import Optional, Sequence, Tuple

from ..kit import (STEEL_DARK, WARM, WOOD, WOOD_DARK, WOOD_LIGHT, ArenaArea, building, flight,
                   gable, lantern, rect, sign_decal, slab, threshold, wall_sign)
from .rails import CREAM, GOLD, IRON, RAIL, RAIL_TOP, SLEEPER

Rect = Tuple[float, float, float, float]


def _place(x: float, z: float, along: str, u: float, w: float) -> Tuple[float, float]:
    """A point ``u`` along and ``w`` across something laid along ``along``."""
    return (x + u, z + w) if along == "x" else (x + w, z + u)


def _size(along: str, lu: float, h: float, lw: float):
    return [lu, h, lw] if along == "x" else [lw, h, lu]


# ============================================================== engines
def locomotive(b: ArenaArea, x: float, z: float, along: str = "x", facing: float = 1.0,
               colour: str = "#2a3a5a", trim: str = GOLD, base: float = 0.0,
               name: str = "", tender: bool = True, stack: str = "balloon") -> None:
    """A steam engine standing on its rails: drivers, the boiler and its
    bands, the smokebox and headlamp, the stack, the domes, the cab with
    its lit windows, the cowcatcher -- and its tender of cordwood behind.
    The body is solid (a step up onto the running board, a jump to the cab
    roof); the wheels and the rods are paint on it."""
    f = 1.0 if facing >= 0 else -1.0

    def at(u: float, w: float) -> Tuple[float, float]:
        return _place(x, z, along, u * f, w)

    y0 = base + RAIL_TOP
    # the frame and running boards
    cx, cz = at(-1.0, 0.0)
    b.box([cx, y0 + 1.4, cz], _size(along, 19.0, 1.8, 3.4), "#1e1c1a", material="metal")
    for side in (-1, 1):
        rx, rz = at(-1.0, side * 2.25)
        b.box([rx, y0 + 2.5, rz], _size(along, 17.0, 0.3, 1.1), "#2a2826", material="metal")
    # drivers: two pairs, big, and a pony truck under the front
    for u, r in ((-4.6, 2.0), (-0.4, 2.0), (4.6, 1.1)):
        for side in (-1, 1):
            wx, wz = at(u, side * 1.82)
            b.cyl([wx, y0 + r, wz], [r * 2.0, 0.3, r * 2.0], "#141210", collide=False,
                  material="metal", r=[math.pi / 2.0, 0, 0] if along == "x" else [0, 0, math.pi / 2.0])
            b.cyl([wx, y0 + r, wz], [r * 0.5, 0.36, r * 0.5], trim, collide=False,
                  material="metal", r=[math.pi / 2.0, 0, 0] if along == "x" else [0, 0, math.pi / 2.0])
    for side in (-1, 1):
        ax, az = at(-2.5, side * 2.02)
        b.box([ax, y0 + 2.0, az], _size(along, 4.6, 0.3, 0.1), "#8a8680", material="metal")
    # the boiler, its bands, the smokebox and its door
    bx, bz = at(0.8, 0.0)
    rot = [0, 0, math.pi / 2.0] if along == "x" else [math.pi / 2.0, 0, 0]
    b.cyl([bx, y0 + 4.4, bz], [3.4, 10.0, 3.4], colour, r=rot, collide=False, material="metal")
    for k in range(3):
        kx, kz = at(-2.6 + k * 3.2, 0.0)
        b.cyl([kx, y0 + 4.4, kz], [3.56, 0.3, 3.56], trim, r=rot, collide=False, material="metal")
    sx, sz = at(6.6, 0.0)
    b.cyl([sx, y0 + 4.4, sz], [3.6, 1.8, 3.6], "#1a1816", r=rot, collide=False, material="metal")
    hx, hz = at(7.56, 0.0)
    b.cyl([hx, y0 + 4.4, hz], [1.4, 0.12, 1.4], "#3a3836", r=rot, collide=False, material="metal")
    # the boiler is solid where a body can reach it: a box inside the round
    cx2, cz2 = at(1.6, 0.0)
    b.box([cx2, y0 + 4.2, cz2], _size(along, 11.6, 2.8, 2.6), "#141210", material="metal")
    # stack, domes, bell, whistle
    kx, kz = at(5.6, 0.0)
    if stack == "balloon":
        b.cyl([kx, y0 + 7.2, kz], [0.9, 2.6, 0.9], "#1a1816", material="metal")
        b.cone([kx, y0 + 9.0, kz], [2.8, 1.4, 2.8], "#1a1816", r=[math.pi, 0, 0])
        b.cyl([kx, y0 + 9.85, kz], [2.8, 0.3, 2.8], trim, material="metal")
    else:
        b.cyl([kx, y0 + 7.6, kz], [1.1, 3.4, 1.1], "#1a1816", material="metal")
        b.cyl([kx, y0 + 9.4, kz], [1.5, 0.3, 1.5], trim, material="metal")
    for u, h in ((3.0, 1.4), (-0.6, 1.1)):
        dx, dz = at(u, 0.0)
        b.cyl([dx, y0 + 6.1 + h / 2.0, dz], [1.5, h, 1.5], trim, material="metal")
        b.sphere([dx, y0 + 6.1 + h, dz], [1.5, 0.9, 1.5], trim, material="metal")
    lx, lz = at(7.0, 0.0)
    b.box([lx, y0 + 6.6, lz], [1.2, 1.2, 1.2], "#2a2826", material="metal")
    gx, gz = at(7.63, 0.0)
    b.box([gx, y0 + 6.6, gz], _size(along, 0.06, 0.8, 0.8), "#fff3c4", material="neon",
          collide=False)
    # the cowcatcher and buffer beam
    wx, wz = at(9.0, 0.0)
    b.box([wx, y0 + 1.4, wz], _size(along, 1.0, 1.6, 4.0), "#8a2a1c")
    cwx, cwz = at(9.95, 0.0)
    b.box([cwx, y0 + 0.9, cwz], _size(along, 0.9, 1.0, 3.2), "#6a6660", material="metal")
    # the cab: walls, roof, windows lit
    cbx, cbz = at(-6.6, 0.0)
    b.box([cbx, y0 + 4.75, cbz], _size(along, 4.4, 4.9, 4.4), colour)
    b.box([cbx, y0 + 7.4, cbz], _size(along, 5.2, 0.4, 5.0), "#1e1c1a", material="metal")
    for side in (-1, 1):
        wx2, wz2 = at(-6.2, side * 2.21)
        b.box([wx2, y0 + 5.8, wz2], _size(along, 2.2, 1.4, 0.04), "#ffd88a", material="neon",
              collide=False)
    if name:
        nx, nz = at(-6.6, 0.0)
        for side in (-1, 1):
            px, pz = at(-6.6, side * 2.23)
            b.box([px, y0 + 3.9, pz], _size(along, 3.6, 0.9, 0.04), trim, collide=False,
                  decal=sign_decal(name, trim, "#1a1816", 4.0))
    if not tender:
        return
    # the tender: cordwood heaped on it
    tx, tz = at(-13.2, 0.0)
    b.box([tx, y0 + 1.2, tz], _size(along, 7.2, 1.6, 3.6), "#1e1c1a", material="metal")
    b.box([tx, y0 + 3.4, tz], _size(along, 7.2, 2.8, 4.4), colour)
    b.box([tx, y0 + 4.95, tz], _size(along, 6.6, 0.3, 3.8), trim, material="metal")
    for k in range(4):
        for j in range(2):
            lx2, lz2 = at(-15.6 + k * 1.6, -0.9 + j * 1.8)
            b.cyl([lx2, y0 + 5.5, lz2], [0.9, 1.4, 0.9], "#8a6040",
                  r=[math.pi / 2.0, 0, 0] if along == "z" else [0, 0, math.pi / 2.0], collide=False)
    for u in (-15.4, -11.0):
        for side in (-1, 1):
            wx3, wz3 = at(u, side * 1.82)
            b.cyl([wx3, y0 + 0.9, wz3], [1.8, 0.3, 1.8], "#141210", collide=False, material="metal",
                  r=[math.pi / 2.0, 0, 0] if along == "x" else [0, 0, math.pi / 2.0])


def stub_track(b: ArenaArea, x0: float, x1: float, z: float, base: float = 0.0,
               along: str = "x") -> None:
    """A short length of track on the ground (no ballast: sleepers lie on
    the dirt) for a display engine or a car to stand on."""
    lo, hi = min(x0, x1), max(x0, x1)
    n = max(1, int((hi - lo) / 3.0))
    for k in range(n):
        u = lo + (k + 0.5) * (hi - lo) / n
        px, pz = (u, z) if along == "x" else (z, u)
        b.box([px, base + 0.15, pz], _size(along, 0.9, 0.3, 4.8), SLEEPER)
    for side in (-1, 1):
        px, pz = ((lo + hi) / 2.0, z + side * 1.6) if along == "x" else (z + side * 1.6, (lo + hi) / 2.0)
        b.box([px, base + 0.37, pz], _size(along, hi - lo, 0.14, 0.36), RAIL, collide=False,
              material="metal")


# ================================================================= camps
def pup_tent(b: ArenaArea, x: float, z: float, along: str = "x", colour: str = "#d8ccae",
             base: float = 0.0, length: float = 7.0) -> None:
    """A two-man A tent: canvas pitched either side of a ridge pole on two
    uprights.  The canvas is two leaning panels; what you bump into is the
    low block of bedrolls and kit inside, so you go round it or over it."""
    half, ridge = 2.6, 3.4
    b.box([x, base + 0.6, z], _size(along, length - 0.6, 1.2, half * 1.6), "#8a7a5a")
    lean = math.atan2(half, ridge)
    slope = math.hypot(half, ridge)
    for side in (-1, 1):
        px, pz = _place(x, z, along, 0.0, side * half / 2.0)
        if along == "x":
            r = [side * lean, 0.0, 0.0]
            size = [length, slope, 0.12]
        else:
            r = [0.0, 0.0, -side * lean]
            size = [0.12, slope, length]
        b.box([px, base + ridge / 2.0, pz], size, colour if side < 0 else "#c8bc9e", r=r, collide=False)
    for end in (-1, 1):
        ux, uz = _place(x, z, along, end * (length / 2.0 + 0.2), 0.0)
        b.box([ux, base + ridge / 2.0, uz], [0.3, ridge, 0.3], WOOD_DARK)
    rx, rz = _place(x, z, along, 0.0, 0.0)
    b.box([rx, base + ridge + 0.1, rz], _size(along, length + 0.8, 0.2, 0.2), WOOD_DARK, collide=False)


def camp_fire(b: ArenaArea, x: float, z: float, base: float = 0.0) -> None:
    """A ring of stones, a heap of embers, a pot on a tripod."""
    for k in range(8):
        a = k / 8.0 * math.pi * 2.0
        b.box([x + math.cos(a) * 2.0, base + 0.3, z + math.sin(a) * 2.0], [0.9, 0.6, 0.9],
              "#8a8478")
    b.sphere([x, base + 0.3, z], [2.2, 0.6, 2.2], "#ff8a3a", material="neon", collide=False)
    for k in range(3):
        a = k / 3.0 * math.pi * 2.0
        b.box([x + math.cos(a) * 1.2, base + 2.0, z + math.sin(a) * 1.2], [0.2, 4.2, 0.2],
              WOOD_DARK, r=[math.sin(a) * 0.3, 0, -math.cos(a) * 0.3], collide=False)
    b.sphere([x, base + 2.0, z], [1.3, 1.0, 1.3], "#2a2826", material="metal")


def cook_wagon(b: ArenaArea, x: float, z: float, along: str = "x", base: float = 0.0) -> None:
    """A chuck wagon: the bed, the hooped canvas, the chuck box at the back."""
    b.box([x, base + 1.6, z], _size(along, 10.0, 1.4, 4.4), "#7a5335")
    # the canvas over its hoops, lying along the wagon
    b.cyl([x, base + 3.2, z], [4.4, 8.4, 4.4], "#efe6d0", collide=False,
          r=[0, 0, math.pi / 2.0] if along == "x" else [math.pi / 2.0, 0, 0])
    bx, bz = _place(x, z, along, -5.6, 0.0)
    b.box([bx, base + 2.2, bz], _size(along, 1.2, 2.6, 4.0), WOOD_DARK)
    for end in (-1, 1):
        for side in (-1, 1):
            wx, wz = _place(x, z, along, end * 3.4, side * 2.4)
            b.cyl([wx, base + 1.3, wz], [2.6, 0.3, 2.6], "#3a2a1e", collide=False,
                  r=[math.pi / 2.0, 0, 0] if along == "x" else [0, 0, math.pi / 2.0])


# ============================================================ high country
def juniper(b: ArenaArea, x: float, z: float, base: float = 0.0, s: float = 1.0) -> None:
    """A twisted juniper: a short trunk, a ragged dark crown above head
    height."""
    b.cyl([x, base + 2.6 * s, z], [1.2 * s, 5.2 * s, 1.2 * s], "#6a4a32")
    b.sphere([x, base + 6.8 * s, z], [7.0 * s, 4.6 * s, 6.4 * s], "#4a6a44", collide=False)
    b.sphere([x + 1.8 * s, base + 7.8 * s, z - 1.2 * s], [4.0 * s, 3.4 * s, 4.0 * s], "#3e5e3a",
             collide=False)


def sage(b: ArenaArea, x: float, z: float, base: float = 0.0, s: float = 1.0,
         colour: str = "#8a9a78") -> None:
    """A clump of sagebrush, knee high: you walk through it."""
    b.sphere([x, base + 0.7 * s, z], [2.6 * s, 1.6 * s, 2.4 * s], colour, collide=False)
    b.sphere([x + 0.9 * s, base + 0.6 * s, z + 0.6 * s], [1.6 * s, 1.2 * s, 1.6 * s], "#7a8a6a",
             collide=False)


def outcrop(b: ArenaArea, x: float, z: float, w: float, h: float, d: float,
            base: float = 0.0, colour: str = "#9a7a5a", cap: Optional[str] = None) -> None:
    """A block of bare rock with a smaller one on its top: cover, and a step
    up."""
    b.box([x, base + h / 2.0, z], [w, h, d], colour)
    b.box([x + w * 0.12, base + h + h * 0.22, z - d * 0.1], [w * 0.55, h * 0.44, d * 0.6],
          cap or colour)


def skull(b: ArenaArea, x: float, z: float, base: float = 0.0, yaw: float = 0.0) -> None:
    """A steer's skull bleaching in the sun, horns and all."""
    b.sphere([x, base + 0.45, z], [1.2, 0.9, 1.6], "#efe8d8", collide=False)
    c, s = math.cos(yaw), math.sin(yaw)
    for side in (-1, 1):
        hx, hz = x + side * 1.3 * c, z - side * 1.3 * s
        b.cone([hx, base + 0.75, hz], [0.4, 1.6, 0.4], "#e8dcc0",
               r=[0, yaw, side * 1.2], collide=False)


# ================================================================ festivity
def bunting(b: ArenaArea, a: Tuple[float, float, float], c: Tuple[float, float, float],
            colours: Sequence[str] = ("#c4281c", "#efe2c4", "#2f6aa8"), every: float = 1.6) -> None:
    """A line of pennants from point ``a`` to point ``c`` (x, y, z), sagging
    in the middle, every pennant a little cone hanging point down."""
    dx, dy, dz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
    span = math.hypot(dx, dz)
    n = max(2, int(span / every))
    yaw = math.atan2(dx, dz)
    depth = min(2.2, span * 0.06)

    def at(f: float):
        return (a[0] + dx * f, a[1] + dy * f - math.sin(math.pi * f) * depth, a[2] + dz * f)

    for k in range(n + 1):
        f = k / float(n)
        px, py, pz = at(f)
        # the line itself, a short rod to the next pennant along the sag
        if k < n:
            qx, qy, qz = at((k + 1) / float(n))
            run = math.hypot(qx - px, qz - pz)
            b.box([(px + qx) / 2.0, (py + qy) / 2.0, (pz + qz) / 2.0],
                  [0.1, 0.1, math.hypot(run, qy - py) + 0.06], "#3a2a1e",
                  r=[-math.atan2(qy - py, run), yaw, 0.002], collide=False)
        if 0 < k < n:
            b.cone([px, py - 0.75, pz], [0.9, 1.3, 0.2], colours[k % len(colours)],
                   r=[math.pi, yaw, 0], collide=False)


def flag_pole(b: ArenaArea, x: float, z: float, base: float = 0.0, height: float = 14.0,
              colour: str = "#c4281c") -> None:
    b.cyl([x, base + height / 2.0, z], [0.5, height, 0.5], "#d8d4cc", material="metal")
    b.sphere([x, base + height + 0.3, z], [0.8, 0.8, 0.8], GOLD, material="metal")
    b.box([x + 1.6, base + height - 1.2, z], [3.0, 1.8, 0.08], colour, collide=False,
          r=[0, 0.0, 0.02])


def grandstand(b: ArenaArea, area: Rect, facing: str, base: float = 0.0, tiers: int = 4,
               colour: str = "#efe2c4", roof: str = "#c4281c") -> None:
    """Tiers of benches stepping up away from ``facing``, a back wall and a
    striped roof on posts: a perch, and a long way to fall off the back."""
    x0, x1, z0, z1 = area
    depth = (z1 - z0) if facing in ("z+", "z-") else (x1 - x0)
    tier_d = depth / float(tiers)
    for k in range(tiers):
        top = base + 1.2 * (k + 1)
        if facing == "z+":
            r = rect(x0, x1, z1 - tier_d * (k + 1), z1 - tier_d * k)
        elif facing == "z-":
            r = rect(x0, x1, z0 + tier_d * k, z0 + tier_d * (k + 1))
        elif facing == "x+":
            r = rect(x1 - tier_d * (k + 1), x1 - tier_d * k, z0, z1)
        else:
            r = rect(x0 + tier_d * k, x0 + tier_d * (k + 1), z0, z1)
        slab(b, r, top, top - base, colour if k % 2 == 0 else WOOD_LIGHT, studs=True)
    roof_y = base + 1.2 * tiers + 8.0
    back = {"z+": (x0, x1, z0, z0 + 0.8), "z-": (x0, x1, z1 - 0.8, z1),
            "x+": (x0, x0 + 0.8, z0, z1), "x-": (x1 - 0.8, x1, z0, z1)}[facing]
    for k in range(4):
        if facing in ("z+", "z-"):
            px = x0 + 0.6 + k * (x1 - x0 - 1.2) / 3.0
            for pz in (z0 + 0.4, z1 - 0.4):
                if (facing == "z+" and pz < z1 - 1.0) or (facing == "z-" and pz > z0 + 1.0):
                    continue
                b.box([px, (base + 1.2 + roof_y) / 2.0, pz], [0.6, roof_y - base - 1.2, 0.6], WOOD_DARK)
        else:
            pz = z0 + 0.6 + k * (z1 - z0 - 1.2) / 3.0
            for px in (x0 + 0.4, x1 - 0.4):
                if (facing == "x+" and px < x1 - 1.0) or (facing == "x-" and px > x0 + 1.0):
                    continue
                b.box([px, (base + 1.2 + roof_y) / 2.0, pz], [0.6, roof_y - base - 1.2, 0.6], WOOD_DARK)
    top = base + 1.2 * tiers
    b.box([(back[0] + back[1]) / 2.0, (top + roof_y) / 2.0, (back[2] + back[3]) / 2.0],
          [back[1] - back[0], roof_y - top, back[3] - back[2]], WOOD)
    stripes = 6
    for k in range(stripes):
        if facing in ("z+", "z-"):
            r = rect(x0 - 1.0 + k * (x1 - x0 + 2.0) / stripes, x0 - 1.0 + (k + 1) * (x1 - x0 + 2.0) / stripes,
                     z0 - 1.0, z1 + 1.0)
        else:
            r = rect(x0 - 1.0, x1 + 1.0, z0 - 1.0 + k * (z1 - z0 + 2.0) / stripes,
                     z0 - 1.0 + (k + 1) * (z1 - z0 + 2.0) / stripes)
        slab(b, r, roof_y + 0.5 + (k % 2) * 0.01, 0.5, roof if k % 2 == 0 else CREAM)


# =============================================================== trestles
def trestle(b: ArenaArea, x0: float, x1: float, z: float, deck: float, floor: float,
            half: float = 7.0, along: str = "x", wood: str = "#7a5838",
            every: float = 6.0) -> None:
    """A timber trestle carrying a level deck at ``deck`` (its top) from
    ``x0`` to ``x1`` over ground at ``floor``: a bent of posts every few
    units with a cap and crossed braces, the deck, a walk and a rail down
    each side.  The track itself (rails, sleepers) is laid on it by the
    caller with no ballast."""
    lo, hi = min(x0, x1), max(x0, x1)
    n = max(2, int(round((hi - lo) / every)))
    t = 0.8
    for k in range(n + 1):
        u = lo + 0.5 + k * (hi - lo - 1.0) / n
        for w in (-half + 0.8, -2.4, 2.4, half - 0.8):
            px, pz = _place(0.0, z, along, u, w) if along == "x" else _place(z, 0.0, along, u, w)
            b.box([px, (floor + deck - t) / 2.0, pz], [0.9, deck - t - floor, 0.9], wood)
        cx, cz = _place(0.0, z, along, u, 0.0) if along == "x" else _place(z, 0.0, along, u, 0.0)
        b.box([cx, deck - t - 0.4, cz], _size(along, 1.0, 0.8, half * 2.0), "#5a4028")
        # crossed braces in the bent, a lattice you see through
        rise = deck - t - 0.8 - floor
        if rise > 3.0:
            ang = math.atan2(rise, half * 2.0 - 1.6)
            length = math.hypot(rise, half * 2.0 - 1.6)
            for sgn in (-1, 1):
                b.box([cx, floor + rise / 2.0, cz], _size(along, 0.4, length, 0.4) if along == "x"
                      else [0.4, length, 0.4], "#5a4028", collide=False, alpha=0.95,
                      r=[sgn * (math.pi / 2.0 - ang), 0, 0] if along == "x" else [0, 0, sgn * (math.pi / 2.0 - ang)])
    area = rect(lo, hi, z - half, z + half) if along == "x" else rect(z - half, z + half, lo, hi)
    slab(b, area, deck, t, "#6a4a30", studs=True)
    for side in (-1, 1):
        for k in range(n + 1):
            u = lo + 0.5 + k * (hi - lo - 1.0) / n
            px, pz = _place(0.0, z, along, u, side * (half - 0.3)) if along == "x" else \
                _place(z, 0.0, along, u, side * (half - 0.3))
            b.box([px, deck + 0.7, pz], [0.4, 1.4, 0.4], WOOD_DARK)
        rx, rz = _place(0.0, z, along, (lo + hi) / 2.0, side * (half - 0.3)) if along == "x" else \
            _place(z, 0.0, along, (lo + hi) / 2.0, side * (half - 0.3))
        b.box([rx, deck + 1.55, rz], _size(along, hi - lo, 0.3, 0.3), WOOD_DARK)


def deck_ties(b: ArenaArea, x0: float, x1: float, z: float, deck: float,
              along: str = "x", every: float = 2.4) -> None:
    """Bare timbers across a trestle's deck where the rails will go."""
    lo, hi = min(x0, x1), max(x0, x1)
    n = max(1, int((hi - lo) / every))
    for k in range(n):
        u = lo + (k + 0.5) * (hi - lo) / n
        px, pz = (u, z) if along == "x" else (z, u)
        b.box([px, deck + 0.12, pz], _size(along, 0.8, 0.24, 6.0), SLEEPER, collide=False)


def rail_stack(b: ArenaArea, x: float, z: float, along: str = "x", base: float = 0.0,
               length: float = 14.0) -> None:
    """New rails stacked on timber chocks, the stack a team takes them from
    (the server's ``rails`` point: E for a rail)."""
    for end in (-1, 1):
        cx, cz = _place(x, z, along, end * (length / 2.0 - 1.5), 0.0)
        b.box([cx, base + 0.4, cz], _size(along, 1.0, 0.8, 5.2), SLEEPER)
    for layer in range(4):
        for k in range(5 - layer):
            w = -2.0 + layer * 0.5 + k * 1.0
            px, pz = _place(x, z, along, 0.0, w)
            b.box([px, base + 0.8 + layer * 0.5 + 0.25, pz], _size(along, length, 0.5, 0.6), RAIL,
                  material="metal")
    b.mark("rails", x, base + 1.4, z)


def survey_stakes(b: ArenaArea, points: Sequence[Tuple[float, float, float]]) -> None:
    """Little stakes with red rags: where the line is to go."""
    for (x, y, z) in points:
        b.box([x, y + 0.6, z], [0.3, 1.2, 0.3], WOOD_LIGHT)
        b.box([x, y + 1.25, z], [0.5, 0.3, 0.06], "#d83a2a", collide=False)
