"""Rolling ground for the railroads built since the first four.

**The land.**  A :class:`Land` is a heightfield over part of an area, built
as boxes that stand on the area's ground plate: each cell's height is
rounded to a step (half a unit by default) and every run of cells of one
height and one colour is merged into a single box, so a hillside is a few
dozen terraces rather than thousands of blocks.  No step is ever more than
a body can walk up, so the whole of it is ground to fight over; where a
hill has to be a cliff, a map builds the cliff itself.

**The line on it.**  :func:`graded` gives a lane a height at every point
from a profile (distance along the line to height), adding points where
the profile bends so the grade changes where the profile says.  The cells
the track runs over are *pinned* to the track (:meth:`Land.pin_path`) on a
finer step, a little under it, so the ballast always lies on the ground.
:func:`lay_graded` lays the track itself: sleepers and rails pitched up
and down the grade with the line.
"""
from __future__ import annotations

import math
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from ..kit import ArenaArea
from .rails import (BALLAST_TOP, GAUGE, GRAVEL, RAIL, RAIL_TOP, SLEEPER, SLEEPER_TOP,
                    TRACK_W)

Point = Tuple[float, float]
Rect = Tuple[float, float, float, float]


# ==================================================================== lanes
def densify(path: Sequence[Point], step: float = 8.0) -> List[Point]:
    """``path`` with points added every ``step`` along its straight runs."""
    out: List[Point] = [tuple(path[0])]
    for i in range(len(path) - 1):
        (x0, z0), (x1, z1) = path[i], path[i + 1]
        seg = math.hypot(x1 - x0, z1 - z0)
        n = max(1, int(seg // step))
        for k in range(1, n):
            f = k / float(n)
            out.append((round(x0 + (x1 - x0) * f, 4), round(z0 + (z1 - z0) * f, 4)))
        out.append(tuple(path[i + 1]))
    return out


def cumulative(path: Sequence[Point]) -> List[float]:
    cum = [0.0]
    for i in range(len(path) - 1):
        cum.append(cum[-1] + math.hypot(path[i + 1][0] - path[i][0], path[i + 1][1] - path[i][1]))
    return cum


def profile_at(profile: Sequence[Tuple[float, float]], d: float) -> float:
    """A piecewise-straight height profile [(distance, height), ...]."""
    if d <= profile[0][0]:
        return profile[0][1]
    for (d0, y0), (d1, y1) in zip(profile, profile[1:]):
        if d <= d1:
            f = 0.0 if d1 <= d0 else (d - d0) / (d1 - d0)
            return y0 + (y1 - y0) * f
    return profile[-1][1]


def graded(path: Sequence[Point], profile: Sequence[Tuple[float, float]],
           step: float = 8.0) -> Tuple[List[Point], List[float]]:
    """The lane's points (densified) and a height for each, from a profile
    given as fractions of the line's length: [(0.0, 0), (0.3, 8), ...]."""
    pts = densify(path, step)
    cum = cumulative(pts)
    total = cum[-1]
    prof = [(f * total, y) for f, y in profile]
    return pts, [round(profile_at(prof, d), 3) for d in cum]


def height_at(path: Sequence[Point], ys: Sequence[float], d: float) -> float:
    cum = cumulative(path)
    d = max(0.0, min(cum[-1], d))
    for i in range(len(cum) - 1):
        if d <= cum[i + 1] or i == len(cum) - 2:
            seg = cum[i + 1] - cum[i]
            f = 0.0 if seg <= 0 else (d - cum[i]) / seg
            return ys[i] + (ys[i + 1] - ys[i]) * f
    return ys[-1]


def nearest_on(path: Sequence[Point], ys: Sequence[float], x: float, z: float
               ) -> Tuple[float, float]:
    """(distance from the line, the line's height there) for (x, z)."""
    best, best_y = 1e9, 0.0
    for i in range(len(path) - 1):
        ax, az = path[i]
        bx, bz = path[i + 1]
        dx, dz = bx - ax, bz - az
        seg = dx * dx + dz * dz
        f = 0.0 if seg <= 0 else max(0.0, min(1.0, ((x - ax) * dx + (z - az) * dz) / seg))
        d = math.hypot(ax + dx * f - x, az + dz * f - z)
        if d < best:
            best, best_y = d, ys[i] + (ys[i + 1] - ys[i]) * f
    return best, best_y


def world_lane(b: ArenaArea, path: Sequence[Point], ys: Sequence[float]) -> List[List[float]]:
    """The lane as the server and the client take it: [x, y, z] points."""
    return [b.at(x, y, z) for (x, z), y in zip(path, ys)]


# ===================================================================== land
class Land:
    """A heightfield over ``area`` in cells of ``cell`` units, built as
    merged boxes standing on the ground (y = 0) up to each cell's height."""

    def __init__(self, area: Rect, cell: float = 4.0, step: float = 0.5):
        self.x0, self.x1, self.z0, self.z1 = area
        self.cell = float(cell)
        self.step = float(step)
        self.nx = max(1, int(round((self.x1 - self.x0) / self.cell)))
        self.nz = max(1, int(round((self.z1 - self.z0) / self.cell)))
        self.h = [[0.0] * self.nx for _ in range(self.nz)]
        self.pin: List[List[Optional[float]]] = [[None] * self.nx for _ in range(self.nz)]
        self.hole = [[False] * self.nx for _ in range(self.nz)]
        self.paint: List[List[Optional[str]]] = [[None] * self.nx for _ in range(self.nz)]

    # ------------------------------------------------------------- cells
    def centre(self, i: int, j: int) -> Point:
        return (self.x0 + (i + 0.5) * self.cell, self.z0 + (j + 0.5) * self.cell)

    def cells(self, area: Optional[Rect] = None):
        for j in range(self.nz):
            for i in range(self.nx):
                x, z = self.centre(i, j)
                if area is None or (area[0] <= x <= area[1] and area[2] <= z <= area[3]):
                    yield i, j, x, z

    # ----------------------------------------------------------- shaping
    def add(self, fn: Callable[[float, float], float]) -> None:
        for i, j, x, z in self.cells():
            self.h[j][i] += fn(x, z)

    def lift(self, fn: Callable[[float, float], float]) -> None:
        """Raise every cell to at least ``fn(x, z)``."""
        for i, j, x, z in self.cells():
            self.h[j][i] = max(self.h[j][i], fn(x, z))

    def scale(self, fn: Callable[[float, float], float]) -> None:
        for i, j, x, z in self.cells():
            self.h[j][i] *= fn(x, z)

    def flatten(self, area: Rect, y: float = 0.0, blend: float = 0.0) -> None:
        """Pin ``area`` to ``y`` (a building's footprint, a yard), easing the
        ground round it toward ``y`` over ``blend`` units."""
        x0, x1, z0, z1 = area
        for i, j, x, z in self.cells():
            dx = max(x0 - x, 0.0, x - x1)
            dz = max(z0 - z, 0.0, z - z1)
            d = math.hypot(dx, dz)
            if d <= 0.0:
                self.pin[j][i] = y
            elif blend > 0 and d < blend and self.pin[j][i] is None:
                k = d / blend
                self.h[j][i] = y + (self.h[j][i] - y) * (k * k * (3 - 2 * k))

    def cut(self, area: Rect) -> None:
        """No land at all in ``area`` (water, a pit, something built)."""
        for i, j, x, z in self.cells(area):
            self.hole[j][i] = True

    def colour(self, fn: Callable[[float, float, float], Optional[str]]) -> None:
        """A colour per cell from (x, z, height); None keeps the default."""
        for i, j, x, z in self.cells():
            self.paint[j][i] = fn(x, z, self.top(i, j))

    def pin_path(self, path: Sequence[Point], ys: Sequence[float], half: float = 7.0,
                 blend: float = 12.0, under: float = 0.06, fine: float = 0.25) -> None:
        """Bring the ground to the track: cells within ``half`` of the line
        are pinned just under it (on a ``fine`` step), and those out to
        ``blend`` beyond are eased toward it so the line runs in a shallow
        cutting or along a low embankment."""
        for i, j, x, z in self.cells():
            d, y = nearest_on(path, ys, x, z)
            if d <= half:
                q = math.floor((y - under) / fine) * fine
                old = self.pin[j][i]
                self.pin[j][i] = q if old is None else min(old, q)
            elif d <= half + blend and self.pin[j][i] is None:
                k = (d - half) / blend
                self.h[j][i] = y + (self.h[j][i] - y) * (k * k * (3 - 2 * k))

    # ------------------------------------------------------------ reading
    def top(self, i: int, j: int) -> float:
        if self.hole[j][i]:
            return 0.0
        pinned = self.pin[j][i]
        if pinned is not None:
            return max(0.0, pinned)
        return max(0.0, round(self.h[j][i] / self.step) * self.step)

    def height(self, x: float, z: float) -> float:
        """The built height of the ground at (x, z) (0 outside the land)."""
        i = int((x - self.x0) // self.cell)
        j = int((z - self.z0) // self.cell)
        if 0 <= i < self.nx and 0 <= j < self.nz:
            return self.top(i, j)
        return 0.0

    def highest(self, area: Rect) -> float:
        return max([self.top(i, j) for i, j, _x, _z in self.cells(area)] or [0.0])

    # ------------------------------------------------------------- build
    def build(self, b: ArenaArea, default: str, studs: bool = True,
              material: str = "") -> int:
        """Greedy-merge equal cells into boxes and add them; returns how many."""
        done = [[False] * self.nx for _ in range(self.nz)]
        count = 0
        for j in range(self.nz):
            for i in range(self.nx):
                if done[j][i]:
                    continue
                top = self.top(i, j)
                if top <= 0.01 or self.hole[j][i]:
                    done[j][i] = True
                    continue
                key = (top, self.paint[j][i])
                i1 = i
                while i1 + 1 < self.nx and not done[j][i1 + 1] and not self.hole[j][i1 + 1] and \
                        (self.top(i1 + 1, j), self.paint[j][i1 + 1]) == key:
                    i1 += 1
                j1 = j
                while j1 + 1 < self.nz and all(
                        not done[j1 + 1][k] and not self.hole[j1 + 1][k] and
                        (self.top(k, j1 + 1), self.paint[j1 + 1][k]) == key for k in range(i, i1 + 1)):
                    j1 += 1
                for jj in range(j, j1 + 1):
                    for ii in range(i, i1 + 1):
                        done[jj][ii] = True
                x0 = self.x0 + i * self.cell
                x1 = self.x0 + (i1 + 1) * self.cell
                z0 = self.z0 + j * self.cell
                z1 = self.z0 + (j1 + 1) * self.cell
                b.box([(x0 + x1) / 2.0, top / 2.0, (z0 + z1) / 2.0], [x1 - x0, top, z1 - z0],
                      self.paint[j][i] or default, studs=studs, material=material)
                count += 1
        return count


# ==================================================================== track
def cut_at(path: Sequence[Point], ys: Sequence[float], distances: Sequence[float]
           ) -> Tuple[List[Point], List[float]]:
    """``path`` and its heights with a point added at each of ``distances``
    along it (where one is not already), so a piece can start or end there."""
    cum = cumulative(path)
    want = sorted(d for d in distances if 0.0 < d < cum[-1])
    pts: List[Point] = [tuple(path[0])]
    hs: List[float] = [ys[0]]
    k = 0
    for i in range(len(path) - 1):
        while k < len(want) and want[k] <= cum[i] + 1e-6:
            k += 1
        while k < len(want) and want[k] < cum[i + 1] - 1e-6:
            seg = cum[i + 1] - cum[i]
            f = (want[k] - cum[i]) / seg if seg > 0 else 0.0
            (x0, z0), (x1, z1) = path[i], path[i + 1]
            pts.append((x0 + (x1 - x0) * f, z0 + (z1 - z0) * f))
            hs.append(ys[i] + (ys[i + 1] - ys[i]) * f)
            k += 1
        pts.append(tuple(path[i + 1]))
        hs.append(ys[i + 1])
    return pts, hs


def lay_graded(b: ArenaArea, path: Sequence[Point], ys: Sequence[float], *,
               ballast: str = GRAVEL, sleeper: str = SLEEPER, rail: str = RAIL,
               sleeper_every: float = 3.2, skip: Sequence[Tuple[float, float]] = (),
               bare: Sequence[Tuple[float, float]] = ()) -> None:
    """Lay a track along ``path`` at heights ``ys``: a level piece where the
    line is level, pieces pitched with the grade where it climbs; a straight
    run at one grade is one piece, however many points it has.

    ``skip`` (start, end distances) is a bridge deck the caller builds (no
    ballast); ``bare`` is ballast and nothing on it (an unfinished stretch
    whose rails the client draws as they are laid)."""
    edges = [d for span in list(skip) + list(bare) for d in span]
    path, ys = cut_at(path, ys, edges)
    cum = cumulative(path)

    def within(spans, d0: float, d1: float) -> bool:
        mid = (d0 + d1) / 2.0
        return any(s <= mid <= e for s, e in spans)

    # the runs: consecutive segments of one heading, one grade, one kind
    runs: List[List[float]] = []
    for i in range(len(path) - 1):
        (x0, z0), (x1, z1) = path[i], path[i + 1]
        seg = cum[i + 1] - cum[i]
        if seg < 0.05:
            continue
        yaw = math.atan2(x1 - x0, z1 - z0)
        grade = (ys[i + 1] - ys[i]) / seg
        kind = (within(skip, cum[i], cum[i + 1]), within(bare, cum[i], cum[i + 1]))
        if runs:
            last = runs[-1]
            if abs(last[4] - yaw) < 1e-5 and abs(last[5] - grade) < 1e-5 and last[6] == kind and \
                    abs(last[1] - cum[i]) < 1e-6:
                last[1] = cum[i + 1]
                last[8] = (x1, z1, ys[i + 1])
                continue
        runs.append([cum[i], cum[i + 1], 0, 0, yaw, grade, kind, (x0, z0, ys[i]), (x1, z1, ys[i + 1])])
    for piece, (d0, d1, _a, _b, yaw, grade, (skipped, bared), (x0, z0, y0), (x1, z1, y1)) in enumerate(runs):
        seg = d1 - d0
        dy = y1 - y0
        pitch = math.atan2(dy, seg)
        run = math.hypot(seg, dy)
        mx, mz, my = (x0 + x1) / 2.0, (z0 + z1) / 2.0, (y0 + y1) / 2.0
        level = abs(dy) < 1e-4
        quarter = level and abs(math.sin(2 * yaw)) < 1e-4
        lift = 0.0 if quarter else 0.004 * (1 + piece % 2)
        overlap = 0.0 if quarter else 0.5
        r = None if quarter else [-pitch, yaw, 0.0]
        along_x = quarter and abs(math.sin(yaw)) > 0.5
        rx, rz = math.cos(yaw), -math.sin(yaw)
        if not skipped:
            under = 0.3 if level else 0.75
            top = my + BALLAST_TOP + lift
            height = top - (my - under)
            size = [TRACK_W, height, run + overlap]
            if along_x:
                size = [run, height, TRACK_W]
            b.box([mx, my - under + height / 2.0, mz], size, ballast, r=r, collide=False)
        if bared:
            continue
        for side in (-1, 1):
            cx, cz = mx + rx * GAUGE * side, mz + rz * GAUGE * side
            h = RAIL_TOP - SLEEPER_TOP
            size = [0.36, h, run + overlap]
            if along_x:
                size = [run, h, 0.36]
            b.box([cx, my + SLEEPER_TOP + lift + h / 2.0, cz], size, rail, r=r,
                  collide=False, material="metal")
        count = max(1, int(seg / sleeper_every))
        for k in range(count):
            f = (k + 0.5) / count
            sx, sz, sy = x0 + (x1 - x0) * f, z0 + (z1 - z0) * f, y0 + dy * f
            h = SLEEPER_TOP - BALLAST_TOP
            size = [4.8, h, 0.9]
            if along_x:
                size = [0.9, h, 4.8]
            b.box([sx, sy + BALLAST_TOP + lift + h / 2.0, sz], size, sleeper, r=r,
                  collide=False)


def spans_of(path: Sequence[Point], fractions: Sequence[Tuple[float, float]]
             ) -> List[Tuple[float, float]]:
    """(start, end) distances from fractions of the line's length."""
    total = cumulative(path)[-1]
    return [(a * total, c * total) for a, c in fractions]


def side_point(path: Sequence[Point], ys: Sequence[float], d: float, offset: float
               ) -> Tuple[float, float, float, float]:
    """(x, z, yaw facing the track, the track's height) ``offset`` to the
    right of the line ``d`` along it."""
    cum = cumulative(path)
    d = max(0.0, min(cum[-1], d))
    for i in range(len(cum) - 1):
        if d <= cum[i + 1] or i == len(cum) - 2:
            (ax, az), (bx, bz) = path[i], path[i + 1]
            seg = cum[i + 1] - cum[i]
            f = 0.0 if seg <= 0 else (d - cum[i]) / seg
            x, z = ax + (bx - ax) * f, az + (bz - az) * f
            y = ys[i] + (ys[i + 1] - ys[i]) * f
            yaw = math.atan2(bx - ax, bz - az)
            px, pz = x + math.cos(yaw) * offset, z - math.sin(yaw) * offset
            return px, pz, math.atan2(x - px, z - pz), y
    x, z = path[-1]
    return x, z, 0.0, ys[-1]


def mirror_keys(points: Dict[str, Sequence[Point]]) -> Dict[str, List[Point]]:
    return {k: [(x, -z) for x, z in v] for k, v in points.items()}
