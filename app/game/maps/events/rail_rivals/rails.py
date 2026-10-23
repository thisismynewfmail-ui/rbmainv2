"""The frontier kit Rail Rivals' four areas are built from.

**Lanes.**  Every area has two tracks, lane ``a`` and lane ``b``, laid from
the west end to the east end.  Lane ``b`` is lane ``a`` mirrored across
z = 0, so the two are exactly the same length and cross each other at the
one point both pass through -- the junction in the middle of the area,
where the race always comes to blows.  A lane is a polyline with its
corners rounded off (:func:`fillet`), sampled every few units; the server
moves a cart along the same samples the client draws.

**Track.**  Ballast, sleepers and two rails, every one of them under the
height a player's feet sink to (0.45), so a track is something you walk
across, never something you trip over.  Straight runs are one piece each;
curves are short turned pieces, and neighbouring pieces stand a few
thousandths apart in height so no two of them ever share a plane.

**Furniture.**  Depots (where a team comes back once its cart has passed
them), the terminus, brake levers, coal heaps, water towers, telegraph
poles, and the false-fronted buildings of a frontier town.
"""
from __future__ import annotations

import math
import random
from typing import Dict, List, Optional, Sequence, Tuple

from ..kit import (
    STEEL_DARK, WARM, WOOD, WOOD_DARK, WOOD_LIGHT, ArenaArea, building, flight,
    gable, lantern, rect, sign_decal, slab, threshold, wall_sign)

Point = Tuple[float, float]

BALLAST_TOP = 0.18
SLEEPER_TOP = 0.30
RAIL_TOP = 0.44
GAUGE = 1.6            # rail centre either side of the lane's centre line
TRACK_W = 5.6          # ballast width
DEPOT_FRACTIONS = (1 / 3.0, 2 / 3.0)
LEVER_FRACTIONS = (0.42, 0.79)

IRON = "#5a5550"
RAIL = "#8c8a86"
SLEEPER = "#5e4630"
GRAVEL = "#7a6f62"
COAL = "#1f1d1c"
RED = "#b8322a"
BLUE = "#2f6aa8"
CREAM = "#efe2c4"
GOLD = "#e8b23a"


# ==================================================================== lanes
def fillet(points: Sequence[Point], radius: float = 26.0, step: float = 5.0
           ) -> List[Point]:
    """``points`` joined by straight runs with every corner rounded off to
    ``radius`` (less where the runs are too short), sampled every ``step``
    along the curves.  Straight runs keep only their two ends."""
    pts = [tuple(p) for p in points]
    out: List[Point] = [pts[0]]
    for i in range(1, len(pts) - 1):
        p0, p1, p2 = pts[i - 1], pts[i], pts[i + 1]
        ax, az = p0[0] - p1[0], p0[1] - p1[1]
        bx, bz = p2[0] - p1[0], p2[1] - p1[1]
        la, lb = math.hypot(ax, az), math.hypot(bx, bz)
        ax, az, bx, bz = ax / la, az / la, bx / lb, bz / lb
        cos_t = max(-1.0, min(1.0, ax * bx + az * bz))
        theta = math.acos(cos_t)               # the angle between the two runs
        if abs(math.pi - theta) < 1e-3:
            out.append(p1)
            continue
        cut = radius / math.tan(theta / 2.0)
        cut = min(cut, la * 0.48, lb * 0.48)
        r = cut * math.tan(theta / 2.0)
        s = (p1[0] + ax * cut, p1[1] + az * cut)
        e = (p1[0] + bx * cut, p1[1] + bz * cut)
        # the centre lies along the bisector
        mx, mz = ax + bx, az + bz
        ml = math.hypot(mx, mz)
        mx, mz = mx / ml, mz / ml
        dist = r / math.sin(theta / 2.0)
        cx, cz = p1[0] + mx * dist, p1[1] + mz * dist
        a0 = math.atan2(s[1] - cz, s[0] - cx)
        a1 = math.atan2(e[1] - cz, e[0] - cx)
        sweep = a1 - a0
        while sweep > math.pi:
            sweep -= 2 * math.pi
        while sweep < -math.pi:
            sweep += 2 * math.pi
        n = max(2, int(abs(sweep) * r / step))
        out.append(s)
        for k in range(1, n):
            a = a0 + sweep * k / n
            out.append((cx + math.cos(a) * r, cz + math.sin(a) * r))
        out.append(e)
    out.append(pts[-1])
    # drop points that landed on top of each other
    clean = [out[0]]
    for p in out[1:]:
        if math.hypot(p[0] - clean[-1][0], p[1] - clean[-1][1]) > 0.05:
            clean.append(p)
    return clean


def mirror(path: Sequence[Point]) -> List[Point]:
    return [(x, -z) for x, z in path]


def length(path: Sequence[Point]) -> float:
    return sum(math.hypot(path[i + 1][0] - path[i][0], path[i + 1][1] - path[i][1])
               for i in range(len(path) - 1))


def at(path: Sequence[Point], d: float) -> Tuple[float, float, float]:
    """(x, z, yaw) ``d`` units along the path; yaw faces along it."""
    d = max(0.0, d)
    for i in range(len(path) - 1):
        x0, z0 = path[i]
        x1, z1 = path[i + 1]
        seg = math.hypot(x1 - x0, z1 - z0)
        if d <= seg or i == len(path) - 2:
            f = min(1.0, d / seg) if seg > 0 else 0.0
            return (x0 + (x1 - x0) * f, z0 + (z1 - z0) * f, math.atan2(x1 - x0, z1 - z0))
        d -= seg
    x, z = path[-1]
    return (x, z, 0.0)


def beside(path: Sequence[Point], d: float, offset: float) -> Tuple[float, float, float]:
    """A point ``offset`` to the right of the path (negative: the left), and
    the yaw that faces back onto the track from there."""
    x, z, yaw = at(path, d)
    rx, rz = math.cos(yaw), -math.sin(yaw)
    px, pz = x + rx * offset, z + rz * offset
    return (px, pz, math.atan2(x - px, z - pz))


# ==================================================================== track
def lay_track(b: ArenaArea, path: Sequence[Point], *, base: float = 0.0,
              ballast: str = GRAVEL, sleeper: str = SLEEPER, rail: str = RAIL,
              sleeper_every: float = 3.2, skip: Sequence[Tuple[float, float]] = ()) -> None:
    """Lay a track along ``path`` on a surface whose top is ``base``.

    ``skip`` is (start, end) distances along the path where the bed is a
    bridge deck the caller builds: the rails and sleepers still run, the
    ballast does not."""
    def skipped(d0: float, d1: float) -> bool:
        return any(d0 < e and d1 > s for s, e in skip)

    walked = 0.0
    piece = 0
    for i in range(len(path) - 1):
        x0, z0 = path[i]
        x1, z1 = path[i + 1]
        seg = math.hypot(x1 - x0, z1 - z0)
        if seg < 0.05:
            continue
        yaw = math.atan2(x1 - x0, z1 - z0)
        mx, mz = (x0 + x1) / 2.0, (z0 + z1) / 2.0
        quarter = abs(math.sin(2 * yaw)) < 1e-4
        lift = 0.0 if quarter else 0.004 * (1 + piece % 2)
        overlap = 0.0 if quarter else 0.5
        r = None if quarter else [0.0, yaw, 0.0]
        if quarter:
            along_x = abs(math.sin(yaw)) > 0.5
        if not skipped(walked, walked + seg):
            top = base + BALLAST_TOP + lift
            height = top - (base - 0.3)
            size = [TRACK_W, height, seg + overlap]
            if quarter and along_x:
                size = [seg, height, TRACK_W]
            b.box([mx, base - 0.3 + height / 2.0, mz], size, ballast, r=r, collide=False)
        # the rails, either side
        rx, rz = math.cos(yaw), -math.sin(yaw)
        for side in (-1, 1):
            cx, cz = mx + rx * GAUGE * side, mz + rz * GAUGE * side
            h = RAIL_TOP - SLEEPER_TOP
            size = [0.36, h, seg + overlap]
            if quarter and along_x:
                size = [seg, h, 0.36]
            b.box([cx, base + SLEEPER_TOP + lift + h / 2.0, cz], size, rail, r=r,
                  collide=False, material="metal")
        # sleepers across the bed
        count = max(1, int(seg / sleeper_every))
        for k in range(count):
            f = (k + 0.5) / count
            sx, sz = x0 + (x1 - x0) * f, z0 + (z1 - z0) * f
            h = SLEEPER_TOP - BALLAST_TOP
            size = [4.8, h, 0.9]
            if quarter and along_x:
                size = [0.9, h, 4.8]
            b.box([sx, base + BALLAST_TOP + lift + h / 2.0, sz], size, sleeper, r=r,
                  collide=False)
        walked += seg
        piece += 1


def buffer_stop(b: ArenaArea, x: float, z: float, yaw: float, colour: str) -> None:
    """The end of the line: a timber stop with a red lamp on it."""
    turn = round(yaw / (math.pi / 2.0)) * (math.pi / 2.0)
    along_x = abs(math.sin(turn)) > 0.5
    size = [2.0, 3.0, 6.4] if along_x else [6.4, 3.0, 2.0]
    b.box([x, 1.5, z], size, WOOD_DARK)
    beam = [2.4, 1.0, 7.2] if along_x else [7.2, 1.0, 2.4]
    b.box([x, 3.5, z], beam, colour)
    b.box([x, 4.4, z], [0.8, 0.8, 0.8], "#ff3a2a", material="neon")


def distance_to(path: Sequence[Point], x: float, z: float) -> float:
    """How far (x, z) is from the nearest point of the path."""
    best = 1e9
    for i in range(len(path) - 1):
        ax, az = path[i]
        bx, bz = path[i + 1]
        dx, dz = bx - ax, bz - az
        seg = dx * dx + dz * dz
        f = 0.0 if seg <= 0 else max(0.0, min(1.0, ((x - ax) * dx + (z - az) * dz) / seg))
        best = min(best, math.hypot(ax + dx * f - x, az + dz * f - z))
    return best


def clear_of(area: Tuple[float, float, float, float], paths: Sequence[Sequence[Point]],
             margin: float = 12.0) -> bool:
    """Is the rectangle at least ``margin`` from every lane?  Tested round
    its edge and through its middle, every couple of units."""
    x0, x1, z0, z1 = area
    pts = []
    nx = max(2, int((x1 - x0) / 2.0))
    nz = max(2, int((z1 - z0) / 2.0))
    for i in range(nx + 1):
        x = x0 + (x1 - x0) * i / nx
        pts += [(x, z0), (x, z1), (x, (z0 + z1) / 2.0)]
    for k in range(nz + 1):
        z = z0 + (z1 - z0) * k / nz
        pts += [(x0, z), (x1, z), ((x0 + x1) / 2.0, z)]
    return all(distance_to(path, x, z) >= margin for path in paths for x, z in pts)


# ================================================================ furniture
def stair(b: ArenaArea, axis: str, near: float, far: float, lo: float, hi: float,
          y_near: float, y_far: float, colour: str = WOOD) -> None:
    """A flight of steps from ``near`` (at ``y_near``) to ``far``, solid only
    a little way below the lower end, so its foot never shares a plane with
    the bottom of the ground."""
    flight(b, axis, near, far, lo, hi, y_near, y_far, colour,
           fill=min(y_near, y_far) - 0.3)


def platform(b: ArenaArea, area: Tuple[float, float, float, float], top: float = 1.2,
             colour: str = WOOD_LIGHT, edge: str = "#d8c070") -> None:
    """A raised timber platform, with a painted safety line along its edges."""
    slab(b, area, top, top + 0.3, colour, studs=True)
    x0, x1, z0, z1 = area
    for zz in (z0 + 0.6, z1 - 0.6):
        b.box([(x0 + x1) / 2.0, top + 0.02, zz], [x1 - x0 - 1.2, 0.04, 0.5], edge,
              collide=False)


def shelter(b: ArenaArea, area: Tuple[float, float, float, float], floor: float,
            height: float, roof: str, post: str = WOOD_DARK) -> None:
    """Posts and a roof over part of a platform."""
    x0, x1, z0, z1 = area
    for px in (x0 + 0.6, x1 - 0.6):
        for pz in (z0 + 0.6, z1 - 0.6):
            b.box([px, floor + height / 2.0, pz], [1.0, height, 1.0], post)
    slab(b, rect(x0 - 1.0, x1 + 1.0, z0 - 1.0, z1 + 1.0), floor + height + 0.6, 0.6, roof)


def depot(b: ArenaArea, lane: str, path: Sequence[Point], fraction: float, side: float,
          name: str, stage: int, roof: str = "#5a3a2a", offset: float = 15.0) -> None:
    """A depot a team comes back to once its cart has passed it: a timber
    platform square to the world beside the track, a roofed shelter with
    the depot's name over it, steps at both ends, and eight spawns."""
    total = length(path)
    x, z, yaw = at(path, total * fraction)
    rx, rz = math.cos(yaw), -math.sin(yaw)
    along_x = abs(math.sin(yaw)) > 0.7
    hx, hz = (16.0, 6.0) if along_x else (6.0, 16.0)
    # far enough out that no corner of the square platform comes within a
    # cart's width of a track that runs past it at a slant
    offset = max(offset, abs(rx) * hx + abs(rz) * hz + 7.0)
    ox, oz = x + rx * side * offset, z + rz * side * offset
    platform(b, rect(ox - hx, ox + hx, oz - hz, oz + hz))
    if along_x:
        stair(b, "x", ox - hx - 3.0, ox - hx, oz - 3.0, oz + 3.0, 0.0, 1.2)
        stair(b, "x", ox + hx + 3.0, ox + hx, oz - 3.0, oz + 3.0, 0.0, 1.2)
    else:
        stair(b, "z", oz - hz - 3.0, oz - hz, ox - 3.0, ox + 3.0, 0.0, 1.2)
        stair(b, "z", oz + hz + 3.0, oz + hz, ox - 3.0, ox + 3.0, 0.0, 1.2)
    cover = rect(ox - hx * 0.55, ox + hx * 0.55, oz - hz * 0.55, oz + hz * 0.55)
    shelter(b, cover, 1.2, 8.0, roof)
    roof_top = 1.2 + 8.0 + 0.6
    face = math.atan2(x - ox, z - oz)
    board_w = (cover[1] - cover[0]) if along_x else (cover[3] - cover[2])
    deco = sign_decal(name, CREAM, "#3a2414", board_w / 2.2)
    turn = 0.0 if abs(face) < math.pi / 2 else math.pi
    if not along_x:
        turn = math.pi / 2.0 if face > 0 else -math.pi / 2.0
    b.box([ox, roof_top + 1.1, oz], [board_w, 2.2, 0.5], CREAM, decal=deco,
          r=[0, turn, 0])
    lantern(b, ox, roof_top - 0.6, oz, WARM)
    # two rows of four, clear of the shelter's posts
    for u in (-13.0, -4.0, 4.0, 13.0):
        for w in (-1.2, 1.2):
            sx, sz = (ox + u, oz + w) if along_x else (ox + w, oz + u)
            b.team_spawn(lane, sx, 1.2 + 0.31, sz, face, stage)
    b.mark("depot", ox, 1.5, oz, lane=lane, fraction=round(fraction, 4), name=name)


def lever(b: ArenaArea, lane: str, path: Sequence[Point], fraction: float,
          side: float, index: int) -> None:
    """A brake lever beside the track: the iron stand is the map's, the
    handle is drawn by the client from the lever's state."""
    total = length(path)
    x, z, yaw = beside(path, total * fraction, side * 6.5)
    b.box([x, 0.6, z], [2.4, 1.2, 2.4], IRON, material="metal")
    b.box([x, 1.6, z], [1.2, 0.8, 1.2], STEEL_DARK, material="metal")
    # a striped warning plate on the ground round it
    b.box([x, 0.02, z], [5.0, 0.04, 5.0], "#d8b23a", collide=False, decal="hazard")
    b.mark("lever", x, 2.0, z, lane=lane, fraction=round(fraction, 4), index=index,
           yaw=round(yaw, 3))


def coal_heap(b: ArenaArea, x: float, z: float, rng: random.Random) -> None:
    """A heap of coal with a shovel in it: walk up and take a sack."""
    b.box([x, 0.7, z], [7.0, 1.4, 7.0], "#2a2725", studs=True)
    for k in range(9):
        a = k * 2.4
        r = 1.0 + (k % 3) * 0.9
        b.sphere([x + math.cos(a) * r, 1.6 + (2 - k % 3) * 0.3, z + math.sin(a) * r],
                 [2.4, 1.6, 2.2], COAL, collide=False)
    b.box([x + 1.6, 2.4, z - 1.2], [0.25, 3.4, 0.25], WOOD, collide=False, r=[0.3, 0.6, 0.2])
    b.mark("coal", x, 1.4, z)


def water_tower(b: ArenaArea, x: float, z: float, colour: str = "#7a5335",
                height: float = 16.0, side: float = 1.0) -> None:
    """A trackside water tank on stilts, and a stack of crates beside it a
    jump apart up to the walkway (the walkway is a sniper's nest, solid).
    Nobody climbs a ladder in this engine; everybody jumps up crates."""
    for dx in (-3.5, 3.5):
        for dz in (-3.5, 3.5):
            b.box([x + dx, height / 2.0, z + dz], [1.0, height, 1.0], WOOD_DARK)
    # the walkway goes right round the tank, wide enough to stand on
    slab(b, rect(x - 8.0, x + 8.0, z - 8.0, z + 8.0), height + 0.6, 0.6, WOOD)
    b.cyl([x, height + 0.6 + 4.5, z], [9.0, 9.0, 9.0], colour)
    b.cone([x, height + 0.6 + 9.0 + 1.6, z], [10.0, 3.2, 10.0], "#4a3a2a", collide=False)
    for k in range(3):
        b.cyl([x, height + 0.6 + 1.5 + k * 3.0, z], [9.1, 0.35, 9.1], IRON,
              material="metal")
    # three crates, each a hop higher, the top one beside the walkway
    top = height + 0.6
    for k in range(3):
        h = top * (3 - k) / 4.0
        cx = x + side * (10.2 + k * 4.0)
        b.box([cx, h / 2.0, z], [4.0, h, 4.4], (WOOD, WOOD_LIGHT, "#9a7048")[k], studs=True)
    b.mark("perch", x, height + 0.6, z)


def telegraph(b: ArenaArea, path: Sequence[Point], side: float, every: float = 60.0,
              colour: str = WOOD_DARK) -> None:
    """Telegraph poles along a lane, a crossbar each."""
    total = length(path)
    d = every * 0.5
    while d < total:
        x, z, yaw = beside(path, d, side * 10.0)
        b.cyl([x, 7.0, z], [0.8, 14.0, 0.8], colour)
        b.box([x, 13.0, z], [4.0, 0.4, 0.4], colour, r=[0, yaw + math.pi / 2.0, 0],
              collide=False)
        d += every


def mile_post(b: ArenaArea, path: Sequence[Point], fraction: float, side: float,
              label: str) -> None:
    total = length(path)
    x, z, yaw = beside(path, total * fraction, side * 4.6)
    b.box([x, 1.2, z], [0.7, 2.4, 0.7], CREAM)
    b.box([x, 2.6, z], [1.6, 0.9, 0.3], CREAM, collide=False, r=[0, yaw, 0],
          decal=sign_decal(label, CREAM, "#2a1a0e", 1.6 / 0.9))


# ================================================================ buildings
def storeyed(b: ArenaArea, area: Tuple[float, float, float, float], heights: Sequence[float],
             colour: str, *, roof: str = "#4a3a2e", floor: str = "#6a4e34",
             doors: Optional[Dict[str, Sequence[Tuple[float, float, float]]]] = None,
             windows: Sequence[Dict[str, Sequence[Tuple[float, float, float, float]]]] = (),
             wells: Sequence[Tuple[float, float, float, float]] = (), glass: bool = True,
             lights: str = WARM, parapet: float = 0.0) -> List[float]:
    """A building of several storeys: each storey's walls are a band of
    their own, with that storey's windows in it, so windows can stack one
    over another; every floor above the ground has ``wells`` cut out of it
    for the stairs.  Returns the height of each floor."""
    from ..kit import carve, plate, strip_light
    x0, x1, z0, z1 = area
    y = 0.0
    levels = []
    for k, h in enumerate(heights):
        last = k == len(heights) - 1
        wins = windows[k] if k < len(windows) else {}
        building(b, area, y, h, colour, roof=last, roof_colour=roof,
                 floor_colour=floor if k == 0 else "", doors=doors if k == 0 else None,
                 windows=wins, glass=glass, lights=lights if last else "",
                 parapet=parapet if last else 0.0)
        levels.append(y + (FLOOR_PAD if k == 0 else 0.0))
        if not last:
            inner = rect(x0 + 2.0, x1 - 2.0, z0 + 2.0, z1 - 2.0)
            plate(b, carve(inner, list(wells)), y + h, 0.8, floor)
            if lights:
                along = (x1 - x0) >= (z1 - z0)
                length = (x1 - x0 - 12.0) if along else (z1 - z0 - 12.0)
                cx, cz = (x0 + x1) / 2.0, (z0 + z1) / 2.0
                if not any(w[0] - 2 < cx + (length / 2 if along else 1) and
                           w[1] + 2 > cx - (length / 2 if along else 1) and
                           w[2] - 2 < cz + (1 if along else length / 2) and
                           w[3] + 2 > cz - (1 if along else length / 2) for w in wells):
                    strip_light(b, cx, cz, y + h - 0.8, length, "x" if along else "z", lights)
        y += h
    return levels


FLOOR_PAD = 0.4



def false_front(b: ArenaArea, area: Tuple[float, float, float, float], facing: str,
                colour: str, sign: str, *, height: float = 12.0, front: float = 6.0,
                trim: str = CREAM, sign_bg: str = "#3a2414", sign_fg: str = "#f2d79a",
                porch: float = 6.0, rng: Optional[random.Random] = None,
                windows: bool = True, interior=None, roof: str = "#4a3a2e") -> None:
    """A frontier store: a hollow timber building whose front wall rises
    ``front`` above its roof with the shop's name on it, a boardwalk porch
    with a roof on posts, a door and windows."""
    x0, x1, z0, z1 = area
    w = (x1 - x0) if facing in ("z-", "z+") else (z1 - z0)
    mid = (x0 + x1) / 2.0 if facing in ("z-", "z+") else (z0 + z1) / 2.0
    door = (mid - 3.5, mid + 3.5, 8.5)
    wins = []
    if windows and w > 20:
        wins = [(mid - w * 0.38, mid - w * 0.18, 3.0, 7.0), (mid + w * 0.18, mid + w * 0.38, 3.0, 7.0)]
    building(b, area, 0.0, height, colour, roof_colour=roof, floor_colour="#6a4e34",
             doors={facing: [door]}, windows={facing: wins}, glass=True, lights=WARM)
    threshold(b, area, facing, (door[0], door[1]))
    # the false front: the facade wall carried on up above the roof
    t = 2.0
    top = height + 1.2
    if facing == "z-":
        b.box([mid, top + front / 2.0, z0 + t / 2.0], [x1 - x0, front, t], colour)
        b.box([mid, top + front + 0.4, z0 + t / 2.0], [x1 - x0 + 1.0, 0.8, t + 0.6], trim)
        wall_sign(b, mid, top + front * 0.5, z0 - 0.35, w * 0.8, front * 0.7,
                  sign_decal(sign, sign_bg, sign_fg, w * 0.8 / (front * 0.7)), "z-", sign_bg)
    elif facing == "z+":
        b.box([mid, top + front / 2.0, z1 - t / 2.0], [x1 - x0, front, t], colour)
        b.box([mid, top + front + 0.4, z1 - t / 2.0], [x1 - x0 + 1.0, 0.8, t + 0.6], trim)
        wall_sign(b, mid, top + front * 0.5, z1 + 0.35, w * 0.8, front * 0.7,
                  sign_decal(sign, sign_bg, sign_fg, w * 0.8 / (front * 0.7)), "z+", sign_bg)
    elif facing == "x-":
        b.box([x0 + t / 2.0, top + front / 2.0, mid], [t, front, z1 - z0], colour)
        b.box([x0 + t / 2.0, top + front + 0.4, mid], [t + 0.6, 0.8, z1 - z0 + 1.0], trim)
        wall_sign(b, x0 - 0.35, top + front * 0.5, mid, w * 0.8, front * 0.7,
                  sign_decal(sign, sign_bg, sign_fg, w * 0.8 / (front * 0.7)), "x-", sign_bg)
    else:
        b.box([x1 - t / 2.0, top + front / 2.0, mid], [t, front, z1 - z0], colour)
        b.box([x1 - t / 2.0, top + front + 0.4, mid], [t + 0.6, 0.8, z1 - z0 + 1.0], trim)
        wall_sign(b, x1 + 0.35, top + front * 0.5, mid, w * 0.8, front * 0.7,
                  sign_decal(sign, sign_bg, sign_fg, w * 0.8 / (front * 0.7)), "x+", sign_bg)
    if porch > 0:
        boardwalk(b, area, facing, porch, roof_y=height * 0.72)
    if interior is not None:
        interior(b, area, facing)


def boardwalk(b: ArenaArea, area: Tuple[float, float, float, float], facing: str,
              depth: float, roof_y: float = 9.0, deck: float = 0.8) -> None:
    """The plank walk in front of a store, and the porch roof over it on
    posts."""
    x0, x1, z0, z1 = area
    if facing == "z-":
        walk = rect(x0, x1, z0 - depth, z0)
        posts = [(x, z0 - depth + 0.6) for x in (x0 + 0.6, (x0 + x1) / 2.0 - 5.0,
                                                 (x0 + x1) / 2.0 + 5.0, x1 - 0.6)]
    elif facing == "z+":
        walk = rect(x0, x1, z1, z1 + depth)
        posts = [(x, z1 + depth - 0.6) for x in (x0 + 0.6, (x0 + x1) / 2.0 - 5.0,
                                                 (x0 + x1) / 2.0 + 5.0, x1 - 0.6)]
    elif facing == "x-":
        walk = rect(x0 - depth, x0, z0, z1)
        posts = [(x0 - depth + 0.6, z) for z in (z0 + 0.6, (z0 + z1) / 2.0 - 5.0,
                                                 (z0 + z1) / 2.0 + 5.0, z1 - 0.6)]
    else:
        walk = rect(x1, x1 + depth, z0, z1)
        posts = [(x1 + depth - 0.6, z) for z in (z0 + 0.6, (z0 + z1) / 2.0 - 5.0,
                                                 (z0 + z1) / 2.0 + 5.0, z1 - 0.6)]
    slab(b, walk, deck, deck, WOOD_LIGHT, studs=True)
    for px, pz in posts:
        b.box([px, deck + (roof_y - deck) / 2.0, pz], [0.8, roof_y - deck, 0.8], WOOD_DARK)
    slab(b, walk, roof_y + 0.5, 0.5, "#5a4632")


def saloon_interior(b: ArenaArea, area, facing: str) -> None:
    """A bar along the back, round tables, a piano."""
    x0, x1, z0, z1 = area
    if facing in ("z-", "z+"):
        back = z1 - 5.0 if facing == "z-" else z0 + 5.0
        b.box([(x0 + x1) / 2.0, 0.4 + 2.0, back], [x1 - x0 - 10.0, 4.0, 2.4], WOOD_DARK)
        b.box([(x0 + x1) / 2.0, 0.4 + 4.1, back], [x1 - x0 - 9.0, 0.3, 3.0], WOOD_LIGHT)
        for k, tx in enumerate((x0 + 9.0, (x0 + x1) / 2.0, x1 - 9.0)):
            tz = (z0 + z1) / 2.0 + (2.0 if k % 2 else -2.0)
            b.cyl([tx, 0.4 + 1.6, tz], [4.4, 0.3, 4.4], WOOD)
            b.cyl([tx, 0.4 + 0.75, tz], [0.8, 1.5, 0.8], WOOD_DARK)
        b.box([x0 + 4.0, 0.4 + 2.2, (z0 + z1) / 2.0], [2.6, 4.4, 6.0], "#2a1a12")
    else:
        back = x1 - 5.0 if facing == "x-" else x0 + 5.0
        b.box([back, 0.4 + 2.0, (z0 + z1) / 2.0], [2.4, 4.0, z1 - z0 - 10.0], WOOD_DARK)
        b.box([back, 0.4 + 4.1, (z0 + z1) / 2.0], [3.0, 0.3, z1 - z0 - 9.0], WOOD_LIGHT)
        for k, tz in enumerate((z0 + 9.0, (z0 + z1) / 2.0, z1 - 9.0)):
            tx = (x0 + x1) / 2.0 + (2.0 if k % 2 else -2.0)
            b.cyl([tx, 0.4 + 1.6, tz], [4.4, 0.3, 4.4], WOOD)
            b.cyl([tx, 0.4 + 0.75, tz], [0.8, 1.5, 0.8], WOOD_DARK)


def store_interior(b: ArenaArea, area, facing: str) -> None:
    """A counter and shelves of goods along the walls."""
    x0, x1, z0, z1 = area
    if facing in ("z-", "z+"):
        back = z1 - 4.0 if facing == "z-" else z0 + 4.0
        b.box([(x0 + x1) / 2.0, 0.4 + 2.6, back], [x1 - x0 - 8.0, 5.2, 2.0], WOOD_DARK)
        for k in range(3):
            b.box([(x0 + x1) / 2.0, 0.4 + 1.2 + k * 1.6, back - 1.3],
                  [x1 - x0 - 9.0, 0.2, 0.6], ["#c8862a", "#6a8a3a", "#8a3a2a"][k])
        b.box([(x0 + x1) / 2.0, 0.4 + 1.8, (z0 + z1) / 2.0], [12.0, 3.6, 2.6], WOOD)
    else:
        back = x1 - 4.0 if facing == "x-" else x0 + 4.0
        b.box([back, 0.4 + 2.6, (z0 + z1) / 2.0], [2.0, 5.2, z1 - z0 - 8.0], WOOD_DARK)
        b.box([(x0 + x1) / 2.0, 0.4 + 1.8, (z0 + z1) / 2.0], [2.6, 3.6, 12.0], WOOD)


# ==================================================================== props
def barrel(b: ArenaArea, x: float, z: float, colour: str = "#7a5335", y: float = 0.0) -> None:
    b.cyl([x, y + 1.6, z], [2.6, 3.2, 2.6], colour)
    for k in (0.5, 2.7):
        b.cyl([x, y + k, z], [2.75, 0.3, 2.75], IRON, collide=False, material="metal")


def crate_stack(b: ArenaArea, x: float, z: float, rng: random.Random,
                colour: str = WOOD) -> None:
    b.box([x, 2.0, z], [4.0, 4.0, 4.0], colour, studs=True)
    if rng.random() < 0.6:
        b.box([x + rng.uniform(-0.4, 0.4), 5.5, z + rng.uniform(-0.4, 0.4)],
              [3.0, 3.0, 3.0], WOOD_LIGHT, studs=True)


def cactus(b: ArenaArea, x: float, z: float, scale: float = 1.0) -> None:
    """A saguaro, arms and all, solid: nobody walks through a cactus."""
    h = 8.0 * scale
    b.cyl([x, h / 2.0, z], [1.6 * scale, h, 1.6 * scale], "#4a7a3a")
    b.cyl([x + 1.8 * scale, h * 0.55, z], [1.0 * scale, 3.0 * scale, 1.0 * scale], "#4a7a3a")
    b.box([x + 1.1 * scale, h * 0.42, z], [2.0 * scale, 0.9 * scale, 0.9 * scale], "#4a7a3a")
    b.cyl([x - 1.6 * scale, h * 0.7, z], [0.9 * scale, 2.6 * scale, 0.9 * scale], "#4a7a3a")
    b.box([x - 1.0 * scale, h * 0.6, z], [1.7 * scale, 0.8 * scale, 0.8 * scale], "#4a7a3a")


def rock(b: ArenaArea, x: float, z: float, w: float, h: float, d: float,
         colour: str, y: float = 0.0) -> None:
    """A boulder that is solid all the way up: stacked boxes, the top one
    smaller, so it reads as a rock and climbs like one."""
    b.box([x, y + h * 0.35, z], [w, h * 0.7, d], colour)
    b.box([x + w * 0.06, y + h * 0.85, z - d * 0.05], [w * 0.7, h * 0.3, d * 0.72], colour)


def fence_run(b: ArenaArea, x0: float, z0: float, x1: float, z1: float,
              colour: str = WOOD, height: float = 3.6, every: float = 8.0) -> None:
    """A split-rail fence: solid posts, rails between them."""
    dx, dz = x1 - x0, z1 - z0
    run = math.hypot(dx, dz)
    count = max(1, int(run // every))
    yaw = math.atan2(dx, dz)
    for k in range(count + 1):
        f = k / float(count)
        b.box([x0 + dx * f, height / 2.0, z0 + dz * f], [0.8, height, 0.8], WOOD_DARK)
    square = abs(math.sin(2 * yaw)) < 1e-4
    for y in (height * 0.45, height * 0.85):
        if square:
            # a rail you can stand beside is a rail you cannot walk through
            size = [0.35, 0.4, run] if abs(dx) < 1e-6 else [run, 0.4, 0.35]
            b.box([(x0 + x1) / 2.0, y, (z0 + z1) / 2.0], size, colour)
        else:
            b.box([(x0 + x1) / 2.0, y, (z0 + z1) / 2.0], [0.35, 0.4, run], colour,
                  r=[0, yaw, 0], collide=False)


def wagon(b: ArenaArea, x: float, z: float, along: str = "x",
          canvas: str = "#e8dcc0") -> None:
    """A covered wagon: a solid bed, wheels, and the canvas over hoops."""
    lx, lz = (12.0, 5.6) if along == "x" else (5.6, 12.0)
    b.box([x, 2.2, z], [lx, 1.6, lz], WOOD)
    for sx in (-1, 1):
        for sz in (-1, 1):
            wx = x + sx * (lx / 2.0 - 2.0 if along == "x" else lx / 2.0 + 0.3)
            wz = z + sz * (lz / 2.0 + 0.3 if along == "x" else lz / 2.0 - 2.0)
            b.cyl([wx, 1.6, wz], [3.2, 0.5, 3.2], WOOD_DARK, collide=False,
                  r=[math.pi / 2.0, 0, 0] if along == "x" else [0, 0, math.pi / 2.0])
    b.box([x, 4.6, z], [lx - 1.0, 3.2, lz - 0.2], canvas)


def hitching_post(b: ArenaArea, x: float, z: float, along: str = "x") -> None:
    lx, lz = (8.0, 0.5) if along == "x" else (0.5, 8.0)
    for k in (-1, 1):
        px = x + (k * 3.6 if along == "x" else 0.0)
        pz = z + (0.0 if along == "x" else k * 3.6)
        b.box([px, 1.6, pz], [0.6, 3.2, 0.6], WOOD_DARK)
    b.box([x, 3.0, z], [lx, 0.5, lz], WOOD)
    b.box([x + (0 if along == "x" else 2.2), 0.9, z + (2.2 if along == "x" else 0)],
          [lx - 1.0 if along == "x" else 2.4, 1.8, 2.4 if along == "x" else lz - 1.0],
          "#6a4a2a")


def windmill(b: ArenaArea, x: float, z: float, height: float = 22.0, y: float = 0.0) -> None:
    """A wind pump: a lattice tower and a vaned wheel."""
    for dx in (-2.0, 2.0):
        for dz in (-2.0, 2.0):
            b.box([x + dx * 0.6, y + height / 2.0, z + dz * 0.6], [0.5, height, 0.5], IRON,
                  material="metal")
    b.box([x, y + height + 0.5, z], [2.4, 1.0, 2.4], IRON, material="metal")
    b.box([x, y + height + 1.2, z + 1.3], [1.2, 1.2, 0.6], IRON, material="metal",
          collide=False)
    for k in range(10):
        a = k * math.pi / 5.0 + 0.1
        # each vane points out from the hub, its root on the hub
        b.box([x + math.cos(a) * 2.4, y + height + 1.2 + math.sin(a) * 2.4, z + 1.4],
              [4.2, 0.9, 0.12], "#c8c0b0", r=[0, 0, a], collide=False)
    b.box([x, y + height + 1.2, z - 2.6], [0.2, 2.0, 4.0], "#b8322a", collide=False)


def gold_sign(b: ArenaArea, x: float, y: float, z: float, w: float, h: float,
              text: str, facing: str) -> None:
    """A big painted sign board on two posts, solid: whoever hops onto a
    post meets the board, not their own head through it."""
    for k in (-1, 1):
        if facing in ("z-", "z+"):
            b.box([x + k * (w / 2.0 - 0.8), y / 2.0, z], [0.8, y, 0.8], WOOD_DARK)
        else:
            b.box([x, y / 2.0, z + k * (w / 2.0 - 0.8)], [0.8, y, 0.8], WOOD_DARK)
    wall_sign(b, x, y + h / 2.0, z, w, h, sign_decal(text, "#3a2414", GOLD, w / h), facing,
              "#3a2414")


# ========================================================== rolling stock
CAR_FLOOR = 1.24        # top of the trucks: a car's body sits on this


def _trucks(b: ArenaArea, x: float, z: float, along: str, length: float,
            width: float = 5.2) -> None:
    """Two four-wheeled trucks under a car, solid from the rail tops up, the
    wheels only just proud of their sides."""
    for end in (-1, 1):
        off = end * (length / 2.0 - 3.4)
        cx, cz = (x + off, z) if along == "x" else (x, z + off)
        size = [4.6, CAR_FLOOR - RAIL_TOP, width] if along == "x" else \
            [width, CAR_FLOOR - RAIL_TOP, 4.6]
        b.box([cx, (RAIL_TOP + CAR_FLOOR) / 2.0, cz], size, IRON, material="metal")
        for wheel in (-1.3, 1.3):
            wx, wz = (cx + wheel, cz) if along == "x" else (cx, cz + wheel)
            b.cyl([wx, (RAIL_TOP + CAR_FLOOR) / 2.0 + 0.01, wz],
                  [0.76, width + 0.08, 0.76], "#2a2826", collide=False, material="metal",
                  r=[math.pi / 2.0, 0, 0] if along == "x" else [0, 0, math.pi / 2.0])


def _buffers(b: ArenaArea, x: float, z: float, along: str, length: float) -> None:
    """The buffer beams at both ends of a car: a step up off the ground,
    and from there a jump to the roof."""
    for end in (-1, 1):
        off = end * (length / 2.0 + 0.6)
        if along == "x":
            b.box([x + off, 1.6, z], [1.2, 1.0, 3.2], IRON, material="metal")
        else:
            b.box([x, 1.6, z + off], [3.2, 1.0, 1.2], IRON, material="metal")


def boxcar(b: ArenaArea, x: float, z: float, along: str = "x", colour: str = "#8a3a2a",
           label: str = "", door: str = "open", length: float = 22.0) -> None:
    """A parked boxcar: solid body and roof, a door open on the side that
    faces ``door`` ("open" -- both sides -- or "shut"), buffers at the ends.
    The roof is a jump and a climb up from the ground: a fine place to
    stand, and nothing to hide under."""
    width, top = 6.0, 8.2
    _trucks(b, x, z, along, length)
    size = [length, top - CAR_FLOOR, width] if along == "x" else [width, top - CAR_FLOOR, length]
    b.box([x, (CAR_FLOOR + top) / 2.0, z], size, colour)
    roof = [length + 0.4, 0.4, width + 0.6] if along == "x" else [width + 0.6, 0.4, length + 0.4]
    b.box([x, top + 0.2, z], roof, "#4a4642", material="metal")
    walk = [length - 1.0, 0.1, 1.2] if along == "x" else [1.2, 0.1, length - 1.0]
    b.box([x, top + 0.45, z], walk, WOOD_DARK, collide=False)
    for side in (-1, 1):
        # the doorway, a dark panel just proud of the side, and the slid-back
        # door beside it
        if along == "x":
            face = z + side * width / 2.0
            if door == "open":
                b.box([x, 4.2, face + side * 0.02], [5.6, 5.4, 0.04], "#1c1714", collide=False)
                b.box([x + 5.8, 4.3, face + side * 0.16], [5.8, 5.8, 0.3], colour)
            else:
                b.box([x, 4.3, face + side * 0.16], [5.8, 5.8, 0.3], colour)
            if label:
                wall_sign(b, x - length * 0.3, 6.9, face - side * 0.3, length * 0.32, 1.1,
                          sign_decal(label, colour, CREAM, length * 0.32 / 1.1),
                          "z+" if side > 0 else "z-", colour)
        else:
            face = x + side * width / 2.0
            if door == "open":
                b.box([face + side * 0.02, 4.2, z], [0.04, 5.4, 5.6], "#1c1714", collide=False)
                b.box([face + side * 0.16, 4.3, z + 5.8], [0.3, 5.8, 5.8], colour)
            else:
                b.box([face + side * 0.16, 4.3, z], [0.3, 5.8, 5.8], colour)
            if label:
                wall_sign(b, face - side * 0.3, 6.9, z - length * 0.3, length * 0.32, 1.1,
                          sign_decal(label, colour, CREAM, length * 0.32 / 1.1),
                          "x+" if side > 0 else "x-", colour)
    _buffers(b, x, z, along, length)


def caboose(b: ArenaArea, x: float, z: float, along: str = "x",
            colour: str = RED) -> None:
    """The guard's van: a short body, a cupola on the roof with lit windows,
    open platforms at both ends with rails round them."""
    length, width, top = 18.0, 6.0, 7.6
    _trucks(b, x, z, along, length)
    body = length - 5.0
    size = [body, top - CAR_FLOOR, width] if along == "x" else [width, top - CAR_FLOOR, body]
    b.box([x, (CAR_FLOOR + top) / 2.0, z], size, colour)
    roof = [body + 0.6, 0.4, width + 0.6] if along == "x" else [width + 0.6, 0.4, body + 0.6]
    b.box([x, top + 0.2, z], roof, "#3a3632")
    cup = [5.0, 3.0, 4.6] if along == "x" else [4.6, 3.0, 5.0]
    b.box([x, top + 1.9, z], cup, colour)
    b.box([x, top + 3.6, z], [cup[0] + 0.6, 0.4, cup[2] + 0.6], "#3a3632")
    for side in (-1, 1):
        if along == "x":
            b.box([x, top + 2.1, z + side * (cup[2] / 2.0 + 0.02)], [3.6, 1.2, 0.04],
                  "#ffd27a", material="neon", collide=False)
        else:
            b.box([x + side * (cup[0] / 2.0 + 0.02), top + 2.1, z], [0.04, 1.2, 3.6],
                  "#ffd27a", material="neon", collide=False)
    for end in (-1, 1):
        off = end * (body / 2.0 + 1.25)
        cx, cz = (x + off, z) if along == "x" else (x, z + off)
        deck = [2.5, 0.4, width] if along == "x" else [width, 0.4, 2.5]
        b.box([cx, CAR_FLOOR + 0.2, cz], deck, WOOD_DARK)
        rail_off = end * (body / 2.0 + 2.3)
        rx, rz = (x + rail_off, z) if along == "x" else (x, z + rail_off)
        rail = [0.2, 0.2, width - 2.4] if along == "x" else [width - 2.4, 0.2, 0.2]
        b.box([rx, CAR_FLOOR + 3.4, rz], rail, IRON, material="metal")
        for s in (-1, 1):
            px, pz = (rx, z + s * (width / 2.0 - 1.3)) if along == "x" else \
                (x + s * (width / 2.0 - 1.3), rz)
            b.box([px, CAR_FLOOR + 0.4 + 1.6, pz], [0.2, 3.2, 0.2], IRON, material="metal")


def flatcar(b: ArenaArea, x: float, z: float, along: str, load: str,
            rng: random.Random, length: float = 20.0) -> None:
    """A flatcar with a load lashed down: "timber", "rails", "crates" or
    "tanks".  The deck is waist height, the load is cover."""
    width, deck = 6.0, CAR_FLOOR + 0.7
    _trucks(b, x, z, along, length)
    size = [length, deck - CAR_FLOOR, width] if along == "x" else [width, deck - CAR_FLOOR, length]
    b.box([x, (CAR_FLOOR + deck) / 2.0, z], size, "#4a3a2e", studs=True)
    # stake pockets and stakes along both edges
    for k in range(4):
        off = -length / 2.0 + 2.0 + k * (length - 4.0) / 3.0
        for side in (-1, 1):
            px, pz = (x + off, z + side * (width / 2.0 - 0.2)) if along == "x" else \
                (x + side * (width / 2.0 - 0.2), z + off)
            b.box([px, deck + 1.2, pz], [0.4, 2.4, 0.4], WOOD_DARK)
    span = length - 3.0

    def piece(off: float, y: float, w: float, h: float, l: float, colour: str,
              **kw) -> None:
        cx, cz = (x + off, z) if along == "x" else (x, z + off)
        s = [l, h, w] if along == "x" else [w, h, l]
        b.box([cx, y + h / 2.0, cz], s, colour, **kw)

    if load == "timber":
        for layer in range(3):
            for k in range(4 - layer):
                across = -1.8 + (layer * 0.6) + k * 1.2
                cx, cz = (x, z + across) if along == "x" else (x + across, z)
                s = [span - layer * 1.2, 1.1, 1.1] if along == "x" else [1.1, 1.1, span - layer * 1.2]
                b.box([cx, deck + 0.55 + layer * 1.1, cz], s,
                      rng.choice(["#9a7048", "#8a6040", "#a87a50"]))
    elif load == "rails":
        for layer in range(4):
            piece(0.0, deck + layer * 0.5, 4.4 - layer * 0.6, 0.5, span, RAIL, material="metal")
    elif load == "tanks":
        for k in (-1, 1):
            off = k * span / 4.0
            cx, cz = (x + off, z) if along == "x" else (x, z + off)
            b.cyl([cx, deck + 2.4, cz], [4.8, 4.8, 4.8], "#5a6a72", material="metal")
            b.cyl([cx, deck + 4.95, cz], [5.0, 0.3, 5.0], "#3a3836", material="metal")
            b.cyl([cx, deck + 5.25, cz], [1.4, 0.3, 1.4], "#3a3836", material="metal")
    else:
        count = max(1, min(3, int((span + 0.6) // 5.4)))
        for k in range(count):
            off = 0.0 if count == 1 else -span / 2.0 + 2.6 + k * (span - 5.2) / (count - 1)
            piece(off, deck, 4.6, 4.0, 4.6, WOOD)
            if k != 1:
                piece(off + 0.3, deck + 4.0, 3.4, 3.0, 3.4, WOOD_LIGHT)


def sleeper_pile(b: ArenaArea, x: float, z: float, along: str = "x",
                 layers: int = 4) -> None:
    """New sleepers stacked crosswise, as a track gang leaves them: solid,
    and knee-to-chest high depending on the stack."""
    for layer in range(layers):
        y = layer * 0.7
        across = (layer % 2 == 0) == (along == "x")
        for k in range(5):
            off = -2.4 + k * 1.2
            if across:
                b.box([x, y + 0.35, z + off], [5.0, 0.7, 0.9], SLEEPER)
            else:
                b.box([x + off, y + 0.35, z], [0.9, 0.7, 5.0], SLEEPER)


def handcar(b: ArenaArea, x: float, z: float, along: str = "x") -> None:
    """A pump trolley parked on a spur."""
    deck = [7.0, 0.5, 5.0] if along == "x" else [5.0, 0.5, 7.0]
    b.box([x, RAIL_TOP + 0.6, z], [deck[0] - 1.0, 0.7, deck[2] - 1.2], IRON, material="metal")
    b.box([x, RAIL_TOP + 1.2, z], deck, WOOD)
    b.box([x, RAIL_TOP + 2.8, z], [0.8, 2.8, 0.8], IRON, material="metal")
    beam = [6.0, 0.4, 0.4] if along == "x" else [0.4, 0.4, 6.0]
    b.box([x, RAIL_TOP + 4.4, z], beam, IRON, material="metal")
    for k in (-1, 1):
        hx, hz = (x + k * 2.8, z) if along == "x" else (x, z + k * 2.8)
        b.box([hx, RAIL_TOP + 4.4, hz], [0.3, 0.3, 3.2] if along == "x" else [3.2, 0.3, 0.3],
              WOOD_DARK)


# ================================================================ helpers
def split_at(path: Sequence[Point], xs: Sequence[float] = (),
             zs: Sequence[float] = ()) -> List[Point]:
    """``path`` with a point added wherever a straight run crosses one of
    ``xs`` (or ``zs``), so a bridge deck can start and end exactly where the
    ballast does."""
    out: List[Point] = [tuple(path[0])]
    for i in range(len(path) - 1):
        (x0, z0), (x1, z1) = path[i], path[i + 1]
        cuts = []
        for x in xs:
            if (x0 - x) * (x1 - x) < 0:
                cuts.append((x - x0) / (x1 - x0))
        for z in zs:
            if (z0 - z) * (z1 - z) < 0:
                cuts.append((z - z0) / (z1 - z0))
        for f in sorted(cuts):
            out.append((round(x0 + (x1 - x0) * f, 4), round(z0 + (z1 - z0) * f, 4)))
        out.append(tuple(path[i + 1]))
    return out


def span_of(path: Sequence[Point], x0: float, x1: float, z0: float, z1: float
            ) -> Tuple[float, float]:
    """The stretch (start, end distance) of ``path`` inside a rectangle."""
    walked, first, last = 0.0, None, None
    for i in range(len(path) - 1):
        (ax, az), (bx, bz) = path[i], path[i + 1]
        seg = math.hypot(bx - ax, bz - az)
        mx, mz = (ax + bx) / 2.0, (az + bz) / 2.0
        if x0 <= mx <= x1 and z0 <= mz <= z1:
            first = walked if first is None else first
            last = walked + seg
        walked += seg
    return (first or 0.0, last or 0.0)


def yard(b: ArenaArea, lane: str, x0: float, x1: float, z: float, side: float,
         name: str, roof: str, sign: Tuple[str, str] = (CREAM, "#3a2414"),
         yaw: float = math.pi / 2.0, end: str = "start") -> Tuple[float, float, float, float]:
    """A station platform beside the track at ``z`` from ``x0`` to ``x1``
    (``side`` +1 puts it on the +z side): steps at its open end, a roofed
    shelter, the name board, a buffer stop on the line, and -- for a
    ``start`` yard -- twelve spawns, or -- for a ``finish`` -- the station
    bell.  Returns the platform's rectangle."""
    pz = z + side * 15.0
    area = rect(x0, x1, pz - 6.0, pz + 6.0)
    platform(b, area)
    west = end == "start"
    if west:
        stair(b, "x", x1 + 3.0, x1, pz - 3.0, pz + 3.0, 0.0, 1.2, WOOD)
    else:
        stair(b, "x", x0 - 3.0, x0, pz - 3.0, pz + 3.0, 0.0, 1.2, WOOD)
    inner = rect(x0 + 6.0, x1 - 12.0, pz - 3.4, pz + 3.4) if west else \
        rect(x0 + 12.0, x1 - 6.0, pz - 3.4, pz + 3.4)
    shelter(b, inner, 1.2, 9.0, roof)
    width = inner[1] - inner[0] - 6.0
    b.box([(inner[0] + inner[1]) / 2.0, 1.2 + 9.6 + 1.2, pz], [width, 2.4, 0.5], sign[0],
          decal=sign_decal(name, sign[0], sign[1], width / 2.4))
    stop_x = x0 + 4.0 if west else x1 - 4.0
    buffer_stop(b, stop_x, z, yaw, roof)
    if west:
        xs = [x0 + 3.0, x0 + 14.0, x0 + 22.0, x0 + 30.0, x0 + 38.0, x1 - 5.0]
        for sx in xs:
            for w in (-1.4, 1.4):
                b.team_spawn(lane, sx, 1.51, pz + w, yaw, 0)
        b.mark("start", stop_x + 10.0, 0.5, z, lane=lane)
    else:
        b.box([x0 + 4.0, 6.5, z + side * 9.0], [0.8, 13.0, 0.8], WOOD_DARK)
        b.box([x0 + 4.0, 12.6, z + side * 9.0], [2.2, 2.2, 2.2], GOLD, material="metal",
              collide=False)
        b.mark("finish", stop_x - 10.0, 0.5, z, lane=lane)
    lantern(b, (x1 - 3.0) if west else (x0 + 3.0), 9.8, pz, WARM)
    return area


def fir(b: ArenaArea, x: float, z: float, scale: float = 1.0, leaf: str = "#2a5a3c",
        snow: str = "", trunk: str = "#5a3a22", y: float = 0.0) -> None:
    """A tall fir: the trunk is solid, the tiers start above a player's head
    (so nobody's face is ever inside a branch) and narrow to the tip; a
    ``snow`` colour lays a cap on every tier."""
    h = 9.0 * scale
    b.cyl([x, y + h / 2.0, z], [1.6 * scale, h, 1.6 * scale], trunk)
    base = y + max(6.2, 4.6 * scale)
    for i in range(4):
        w = (11.0 - i * 2.4) * scale
        th = 5.4 * scale
        cy = base + th / 2.0 + i * 3.4 * scale
        b.cone([x, cy, z], [w, th, w], leaf, collide=False)
        if snow:
            b.cone([x, cy + th * 0.32, z], [w * 0.5, th * 0.36, w * 0.5], snow,
                   collide=False)


def log_pile(b: ArenaArea, x: float, z: float, along: str = "x", length: float = 14.0,
             rows: int = 3, colour: str = "#8a6040", end: str = "#c8a070") -> None:
    """Felled logs stacked in a pyramid, chocked at the ends: solid, and a
    step up per row."""
    for row in range(rows):
        count = rows - row + 1
        for k in range(count):
            across = (k - (count - 1) / 2.0) * 1.9
            y = 0.95 + row * 1.6
            if along == "x":
                b.box([x, y, z + across], [length - row * 0.6, 1.8, 1.8], colour)
                for e in (-1, 1):
                    b.box([x + e * ((length - row * 0.6) / 2.0 + 0.02), y, z + across],
                          [0.04, 1.4, 1.4], end, collide=False)
            else:
                b.box([x + across, y, z], [1.8, 1.8, length - row * 0.6], colour)
                for e in (-1, 1):
                    b.box([x + across, y, z + e * ((length - row * 0.6) / 2.0 + 0.02)],
                          [1.4, 1.4, 0.04], end, collide=False)
    for e in (-1, 1):
        half = (rows + 1) * 1.9 / 2.0 + 0.5
        if along == "x":
            b.box([x + e * (length / 2.0 - 1.5), 1.6, z - half], [0.6, 3.2, 0.6], WOOD_DARK)
            b.box([x + e * (length / 2.0 - 1.5), 1.6, z + half], [0.6, 3.2, 0.6], WOOD_DARK)
        else:
            b.box([x - half, 1.6, z + e * (length / 2.0 - 1.5)], [0.6, 3.2, 0.6], WOOD_DARK)
            b.box([x + half, 1.6, z + e * (length / 2.0 - 1.5)], [0.6, 3.2, 0.6], WOOD_DARK)


def snow_shed(b: ArenaArea, x0: float, x1: float, z: float, uphill: float,
              wood: str = "#6a4a30", roof: str = "#4a3a2e", snow: str = "#eef2f6",
              height: float = 12.0, half: float = 8.0) -> None:
    """A snow shed over the line from ``x0`` to ``x1``: a solid timber wall on
    the uphill side (``uphill`` -1 is -z) with slits to shoot through, posts
    every few units on the downhill side, a roof you can stand on (snow on
    it) and a stair up the outside of the uphill wall.  Lanterns light the
    inside."""
    wall_z = z + uphill * half
    open_z = z - uphill * half
    t = 1.2
    # the uphill wall, slits every 12 units
    count = max(1, int(round((x1 - x0) / 12.0)))
    seg = (x1 - x0) / count
    for i in range(count):
        k = x0 + i * seg
        mid = k + seg / 2.0
        b.box([mid, 2.4, wall_z], [seg, 4.8, t], wood)
        b.box([k + (seg - 4.0) / 2.0, 6.1, wall_z], [seg - 4.0, 2.6, t], wood)
        b.box([k + seg - 1.0, 6.1, wall_z], [2.0, 2.6, t], wood)
        b.box([mid, (7.4 + height) / 2.0, wall_z], [seg, height - 7.4, t], wood)
    # the open side: posts and a beam
    n = max(2, int((x1 - x0) / 7.5))
    for i in range(n + 1):
        px = x0 + 0.6 + i * (x1 - x0 - 1.2) / n
        b.box([px, height / 2.0, open_z], [1.2, height, 1.2], wood)
    b.box([(x0 + x1) / 2.0, height - 0.6, open_z], [x1 - x0 - 0.2, 1.2, 1.4], wood)
    # the roof, its snow, and the lanterns under it
    slab(b, rect(x0 - 1.0, x1 + 1.0, z - half - 1.4, z + half + 1.4), height + 1.0, 1.0, roof)
    slab(b, rect(x0 - 0.6, x1 + 0.6, z - half - 1.0, z + half + 1.0), height + 1.6, 0.6, snow)
    for i in range(int((x1 - x0) // 20)):
        lantern(b, x0 + 10.0 + i * 20.0, height, z, WARM)
    # a flight up the outside of the uphill wall to the roof's edge
    roof_top = height + 1.6
    edge = z + uphill * (half + 1.4)
    lo, hi = sorted((edge, edge + uphill * 5.0))
    run = roof_top * 1.7
    flight(b, "x", x0 + 4.0 + run, x0 + 4.0, lo, hi, 0.0, roof_top, wood, fill=-0.3)


def snowy_gable(b: ArenaArea, area: Tuple[float, float, float, float], y: float,
                colour: str, along: str = "x", tiers: int = 4, rise: float = 1.4,
                overhang: float = 1.0, snow: str = "#eef2f6") -> None:
    """A stepped roof with snow lying on every step."""
    gable(b, area, y, colour, along, tiers, rise, overhang)
    x0, x1, z0, z1 = area
    x0, x1, z0, z1 = x0 - overhang, x1 + overhang, z0 - overhang, z1 + overhang
    for i in range(tiers):
        if along == "x":
            inset = (z1 - z0) / 2.0 * (i + 1) / (tiers + 0.6)
            r = (x0 + 0.1, x1 - 0.1, z0 + inset + 0.1, z1 - inset - 0.1)
        else:
            inset = (x1 - x0) / 2.0 * (i + 1) / (tiers + 0.6)
            r = (x0 + inset + 0.1, x1 - inset - 0.1, z0 + 0.1, z1 - 0.1)
        slab(b, r, y + rise * (i + 1) + 0.3, 0.3, snow)


def coaling_tower(b: ArenaArea, x: float, z: float, along: str = "x",
                  colour: str = "#6a4a30", height: float = 13.0) -> None:
    """A timber coaling tower astride the line: four legs either side of the
    track, the bunker on top, and a chute swung up over the rails."""
    for a in (-5.0, 5.0):
        for c in (-6.2, 6.2):
            px, pz = (x + a, z + c) if along == "x" else (x + c, z + a)
            b.box([px, height / 2.0, pz], [1.4, height, 1.4], WOOD_DARK)
    size = [14.0, 10.0, 16.0] if along == "x" else [16.0, 10.0, 14.0]
    b.box([x, height + 5.0, z], size, colour)
    b.box([x, height + 10.4, z], [size[0] + 1.0, 0.8, size[2] + 1.0], "#3a2e26")
    b.box([x, height + 11.3, z], [size[0] - 4.0, 1.0, size[2] - 4.0], COAL, studs=True)
    chute = [3.0, 1.0, 5.0] if along == "x" else [5.0, 1.0, 3.0]
    b.box([x, height - 0.5, z], chute, IRON, material="metal")
