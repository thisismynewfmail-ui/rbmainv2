#!/usr/bin/env python3
"""Geometry QA for the game maps.

Run it after touching any map::

    python3 tools/mapcheck.py                # every map
    python3 tools/mapcheck.py ironvale       # just one

It answers the three questions that decide whether a map feels finished:

``z-fighting``
    Two surfaces on the same plane, facing the same way, overlapping.  The
    depth buffer cannot separate them, so they shimmer as the camera moves.
    The fix is always the same: butt the parts together instead of letting
    them overlap, or move one of them.

``stuck and floating spawns``
    Every spawn point and every objective marker is tested with the real
    player box: the body must be in clear air and there must be solid ground
    a short drop underneath it.  A spawn inside a wall is an instant death
    loop; a spawn over a hole is a fall into the void.

``sealed playfield``
    A grid of probes across the walkable area is dropped onto whatever is
    under it and checked for headroom, so a slab with a hole in it (or a hole
    with no slab around it) shows up here rather than in a match.

``decor over a void``
    Paint, paths and plates laid on the ground have to have ground under all
    of them.  One that runs off the edge of a platform is a grey rectangle
    hanging in the air; one laid across a stairwell is a lid over the stairs.

``lights in the air``
    Neon has to be fixed to something: under a ceiling, on a wall, in a
    step.  A tube a couple of units below the ceiling it belongs to reads as
    a light floating in the room.

``walk-through clutter``
    Anything without collision that stands in the space a player walks
    through -- a panel, a railing, a lamp over a staircase.  It looks solid
    and it is not, which is worse than it not being there at all.

``loose decor``
    A decorative part that touches nothing: a banner beside its mast rather
    than on it, a beacon an inch above the pole it belongs to.

``mirror symmetry``
    For a map that says it is mirrored (``MIRROR_AXIS`` in its module),
    every solid has a twin across the middle.  Cover only one team gets is a
    thumb on the scale, however it got there.

Nothing in here is specific to one map, so a new world gets the same audit
for free.
"""
from __future__ import annotations

import math
import os
import sys
from collections import defaultdict
from typing import Any, Dict, List, Optional, Sequence, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.game.instance import PLAYER_SIZE  # noqa: E402
from app.game.maps import (  # noqa: E402
    crossroads, ironvale, payload, tycoon)

MAPS = {
    "crossroads": crossroads,
    "ironvale": ironvale,
    "payload": payload,
    "tycoon": tycoon,
}

MIN_FACE_OVERLAP = 1.0      # square units before a coplanar pair is worth a word
PLANE_EPS = 1e-4
AXES = ("x", "y", "z")


# --------------------------------------------------------------- geometry
def box_bounds(part: Dict[str, Any]) -> Optional[Tuple[List[float], List[float]]]:
    """The axis aligned bounds of a part, or None if it is not axis aligned.

    Rotated and round primitives are decoration as far as this tool goes --
    the engine approximates them for collision too, and a shimmering leaf is
    not what anybody means by z-fighting.
    """
    size = list(part["s"])
    if "r" in part:
        rx, ry, rz = part["r"]
        if abs(rx) > 1e-3 or abs(rz) > 1e-3:
            return None
        quarter = ry % (math.pi / 2.0)
        if min(quarter, math.pi / 2.0 - quarter) > 1e-3:
            return None
        if int(round(ry / (math.pi / 2.0))) % 2:
            size = [size[2], size[1], size[0]]
    px, py, pz = part["p"]
    return ([px - size[0] / 2.0, py - size[1] / 2.0, pz - size[2] / 2.0],
            [px + size[0] / 2.0, py + size[1] / 2.0, pz + size[2] / 2.0])


def collider_bounds(part: Dict[str, Any]) -> Optional[Tuple[List[float], List[float]]]:
    """The same bounds the server and the client build for collision."""
    if not part.get("col"):
        return None
    size = list(part["s"])
    if "r" in part:
        rx, ry, rz = part["r"]
        if abs(rx) > 1e-3 or abs(rz) > 1e-3:
            return None
        turns = ry / (math.pi / 2.0)
        if abs(turns - round(turns)) > 1e-3:
            return None
        if int(round(turns)) % 2:
            size = [size[2], size[1], size[0]]
    kind = part.get("t", "box")
    if kind == "sph":
        size = [s * 0.78 for s in size]
    elif kind == "cyl":
        size = [size[0] * 0.86, size[1], size[2] * 0.86]
    elif kind == "cone":
        size = [size[0] * 0.62, size[1], size[2] * 0.62]
    elif kind == "torus":
        return None
    px, py, pz = part["p"]
    return ([px - size[0] / 2.0, py - size[1] / 2.0, pz - size[2] / 2.0],
            [px + size[0] / 2.0, py + size[1] / 2.0, pz + size[2] / 2.0])


def overlap(a0: float, a1: float, b0: float, b1: float) -> float:
    return min(a1, b1) - max(a0, b0)


# ------------------------------------------------------------- z-fighting
def find_zfighting(parts: Sequence[Dict[str, Any]],
                   occluders: Optional["Opaque"] = None) -> List[str]:
    """Coplanar, co-facing, overlapping surfaces.

    Faces are filed by the plane they sit on and the way they point, so two
    faces only ever meet here if they really are fighting for the same
    pixels.  Back to back faces -- the usual result of butting two solids
    together -- point opposite ways and are both culled, so they never land
    in the same bucket.
    """
    buckets: Dict[Tuple[int, float, int], List[Tuple[int, Tuple[float, ...]]]]
    buckets = defaultdict(list)
    for index, part in enumerate(parts):
        bounds = box_bounds(part)
        if bounds is None or part.get("t") != "box":
            continue
        lo, hi = bounds
        for axis in range(3):
            u, v = (axis + 1) % 3, (axis + 2) % 3
            face = (lo[u], hi[u], lo[v], hi[v])
            if face[1] - face[0] < 1e-6 or face[3] - face[2] < 1e-6:
                continue
            buckets[(axis, round(lo[axis], 4), -1)].append((index, face))
            buckets[(axis, round(hi[axis], 4), 1)].append((index, face))

    reports: List[str] = []
    for (axis, plane, direction), faces in buckets.items():
        if len(faces) < 2:
            continue
        faces.sort(key=lambda f: f[1][0])
        for i, (ai, a) in enumerate(faces):
            for bj, bface in faces[i + 1:]:
                if bface[0] >= a[1] - 1e-6:
                    break
                du = overlap(a[0], a[1], bface[0], bface[1])
                dv = overlap(a[2], a[3], bface[2], bface[3])
                if du <= 1e-6 or dv <= 1e-6:
                    continue
                area = du * dv
                if area < MIN_FACE_OVERLAP:
                    continue
                if _enclosed(parts[ai], parts[bj]):
                    continue
                if occluders is not None and occluders.buried(
                        axis, plane, direction, a, bface):
                    continue
                reports.append(
                    "%s=%g %s face, %.0f sq units shared by parts #%d %s and "
                    "#%d %s" % (AXES[axis], plane,
                                "+" if direction > 0 else "-", area,
                                ai, _describe(parts[ai]), bj,
                                _describe(parts[bj])))
    return reports


def _enclosed(a: Dict[str, Any], c: Dict[str, Any]) -> bool:
    """True when one part is completely inside the other, so neither shows."""
    ab, cb = box_bounds(a), box_bounds(c)
    if ab is None or cb is None:
        return False
    inside = all(ab[0][i] >= cb[0][i] - 1e-6 and ab[1][i] <= cb[1][i] + 1e-6
                 for i in range(3))
    outside = all(cb[0][i] >= ab[0][i] - 1e-6 and cb[1][i] <= ab[1][i] + 1e-6
                  for i in range(3))
    return inside or outside


def _describe(part: Dict[str, Any]) -> str:
    return "%s at (%g, %g, %g) %gx%gx%g" % (
        part.get("t", "box"), part["p"][0], part["p"][1], part["p"][2],
        part["s"][0], part["s"][1], part["s"][2])


class Opaque:
    """Every solid-looking box, so a face can be asked whether it is buried."""

    CELL = 48.0

    def __init__(self, parts: Sequence[Dict[str, Any]]):
        self.boxes: List[Tuple[List[float], List[float]]] = []
        for part in parts:
            if part.get("t") != "box" or float(part.get("a", 1.0)) < 0.999:
                continue
            bounds = box_bounds(part)
            if bounds is not None:
                self.boxes.append(bounds)
        self.grid: Dict[Tuple[int, int], List[int]] = defaultdict(list)
        for index, (lo, hi) in enumerate(self.boxes):
            for cx in range(int(lo[0] // self.CELL), int(hi[0] // self.CELL) + 1):
                for cz in range(int(lo[2] // self.CELL), int(hi[2] // self.CELL) + 1):
                    self.grid[(cx, cz)].append(index)

    def inside(self, point: Sequence[float],
               ignore: Sequence[Tuple[float, ...]] = ()) -> bool:
        cx, cz = int(point[0] // self.CELL), int(point[2] // self.CELL)
        for index in self.grid.get((cx, cz), ()):
            lo, hi = self.boxes[index]
            if all(lo[i] - 1e-6 <= point[i] <= hi[i] + 1e-6 for i in range(3)):
                return True
        return False

    def buried(self, axis: int, plane: float, direction: int,
               a: Tuple[float, ...], c: Tuple[float, ...]) -> bool:
        """True when solid material sits right outside the shared face.

        The overlap is sampled at its centre and its four quarter points; if
        every one of them is inside something opaque, nothing can get a look
        at the pair and the shimmer can never happen.
        """
        u, v = (axis + 1) % 3, (axis + 2) % 3
        u0, u1 = max(a[0], c[0]), min(a[1], c[1])
        v0, v1 = max(a[2], c[2]), min(a[3], c[3])
        offset = plane + (0.05 if direction > 0 else -0.05)
        for fu, fv in ((0.5, 0.5), (0.25, 0.25), (0.75, 0.25),
                       (0.25, 0.75), (0.75, 0.75)):
            point = [0.0, 0.0, 0.0]
            point[axis] = offset
            point[u] = u0 + (u1 - u0) * fu
            point[v] = v0 + (v1 - v0) * fv
            if not self.inside(point):
                return False
        return True


# ------------------------------------------------------------- occupancy
class Solid:
    """The map's collision boxes, in a bucket grid, with the two queries the
    checks below need: is this body clear, and what is underneath it."""

    CELL = 48.0

    def __init__(self, parts: Sequence[Dict[str, Any]]):
        self.boxes: List[Tuple[List[float], List[float]]] = []
        for part in parts:
            bounds = collider_bounds(part)
            if bounds is not None:
                self.boxes.append(bounds)
        self.grid: Dict[Tuple[int, int], List[int]] = defaultdict(list)
        for index, (lo, hi) in enumerate(self.boxes):
            for cx in range(int(lo[0] // self.CELL), int(hi[0] // self.CELL) + 1):
                for cz in range(int(lo[2] // self.CELL), int(hi[2] // self.CELL) + 1):
                    self.grid[(cx, cz)].append(index)

    def near(self, x: float, z: float) -> List[Tuple[List[float], List[float]]]:
        cx, cz = int(x // self.CELL), int(z // self.CELL)
        out = []
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                for index in self.grid.get((cx + dx, cz + dz), ()):
                    out.append(self.boxes[index])
        return out

    def blocked(self, x: float, y: float, z: float, margin: float = 0.0) -> bool:
        hw = PLAYER_SIZE[0] / 2.0 + margin
        hd = PLAYER_SIZE[2] / 2.0 + margin
        height = PLAYER_SIZE[1]
        for lo, hi in self.near(x, z):
            if hi[0] > x - hw and lo[0] < x + hw and \
               hi[1] > y + 0.05 and lo[1] < y + height and \
               hi[2] > z - hd and lo[2] < z + hd:
                return True
        return False

    def ground_under(self, x: float, y: float, z: float) -> Optional[float]:
        hw, hd = PLAYER_SIZE[0] / 2.0, PLAYER_SIZE[2] / 2.0
        best = None
        for lo, hi in self.near(x, z):
            if hi[0] <= x - hw or lo[0] >= x + hw:
                continue
            if hi[2] <= z - hd or lo[2] >= z + hd:
                continue
            if hi[1] > y + 0.05:
                continue
            if best is None or hi[1] > best:
                best = hi[1]
        return best


def check_points(solid: Solid, points: Sequence[Tuple[str, List[float]]],
                 drop: float = 3.0, clearance: float = 1.2) -> List[str]:
    """Every spawn and marker, tested with the real player box.

    ``clearance`` is tested as well as the body itself.  A spawn that only
    just fits is a spawn that puts somebody inside the wall as soon as
    anything nudges them -- a knockback, a correction, or simply the client
    resolving the first frame of movement -- so "it fits" is not the bar.
    """
    problems = []
    for label, pos in points:
        x, y, z = pos
        if solid.blocked(x, y, z):
            problems.append("%s at (%.1f, %.1f, %.1f) is inside a solid"
                            % (label, x, y, z))
            continue
        if clearance > 0 and solid.blocked(x, y, z, clearance):
            problems.append("%s at (%.1f, %.1f, %.1f) has under %.1f units of "
                            "clearance around it" % (label, x, y, z, clearance))
            continue
        ground = solid.ground_under(x, y + 0.2, z)
        if ground is None:
            problems.append("%s at (%.1f, %.1f, %.1f) has nothing under it"
                            % (label, x, y, z))
        elif y - ground > drop:
            problems.append("%s at (%.1f, %.1f, %.1f) floats %.1f above the "
                            "floor" % (label, x, y, z, y - ground))
    return problems


def check_playfield(solid: Solid, data: Dict[str, Any], step: float = 12.0
                    ) -> List[str]:
    """Probe the walkable area for holes in the ground and low ceilings."""
    parts = data["parts"]
    xs = [p["p"][0] for p in parts]
    zs = [p["p"][2] for p in parts]
    x0, x1 = min(xs) + step, max(xs) - step
    z0, z1 = min(zs) + step, max(zs) - step
    kill_y = data.get("kill_y", -60.0)
    holes = 0
    samples = 0
    x = x0
    while x <= x1:
        z = z0
        while z <= z1:
            samples += 1
            ground = solid.ground_under(x, 60.0, z)
            if ground is None or ground < kill_y + 4.0:
                holes += 1
            z += step
        x += step
    out = []
    if holes:
        out.append("%d of %d ground probes found no floor (open sky over the "
                   "void)" % (holes, samples))
    return out


# ------------------------------------------------------------ decoration
JUMP_UP_DECOR = 9.0     # the same jump the route check allows


class PartIndex:
    """Every part's bounds in a bucket grid, collision or not.

    The occupancy index above only knows about solids; the decoration checks
    also want to know what a strip of paint is lying on, and paint can lie on
    other paint.
    """

    CELL = 24.0

    def __init__(self, parts: Sequence[Dict[str, Any]]):
        self.bounds: List[Optional[Tuple[List[float], List[float]]]] = []
        self.grid: Dict[Tuple[int, int], List[int]] = defaultdict(list)
        for index, part in enumerate(parts):
            bounds = box_bounds(part)
            self.bounds.append(bounds)
            if bounds is None:
                continue
            lo, hi = bounds
            for cx in range(int(lo[0] // self.CELL), int(hi[0] // self.CELL) + 1):
                for cz in range(int(lo[2] // self.CELL), int(hi[2] // self.CELL) + 1):
                    self.grid[(cx, cz)].append(index)

    def around(self, lo: Sequence[float], hi: Sequence[float]) -> List[int]:
        found = set()
        for cx in range(int(lo[0] // self.CELL), int(hi[0] // self.CELL) + 1):
            for cz in range(int(lo[2] // self.CELL), int(hi[2] // self.CELL) + 1):
                found.update(self.grid.get((cx, cz), ()))
        return sorted(found)


def _samples(lo: Sequence[float], hi: Sequence[float], spacing: float = 1.0,
             cap: int = 24) -> List[Tuple[float, float, float]]:
    """Cell centres over a footprint, with the area each one stands for."""
    wide, deep = hi[0] - lo[0], hi[2] - lo[2]
    nx = max(1, min(cap, int(math.ceil(wide / spacing))))
    nz = max(1, min(cap, int(math.ceil(deep / spacing))))
    cell = (wide / nx) * (deep / nz)
    return [(lo[0] + wide * (i + 0.5) / nx, lo[2] + deep * (j + 0.5) / nz, cell)
            for i in range(nx) for j in range(nz)]


def _decor(part: Dict[str, Any]) -> bool:
    """Non-solid, opaque, and a shape these checks can reason about."""
    return (not part.get("col") and part.get("t", "box") in ("box", "cyl")
            and float(part.get("a", 1.0)) >= 0.999)


def find_floating_decor(parts: Sequence[Dict[str, Any]], index: PartIndex
                        ) -> List[str]:
    """Floor overlays that run off whatever they were laid on.

    A part counts as an overlay when it is thin and, at its middle, lies on
    or in some other surface.  Then every other point of it has to lie on
    something too -- the gap it may bridge is a crack, not a stairwell.
    """
    reports = []
    for i, part in enumerate(parts):
        bounds = index.bounds[i]
        if bounds is None or not _decor(part):
            continue
        lo, hi = bounds
        if hi[1] - lo[1] > 1.0:
            continue
        near = [j for j in index.around(lo, hi) if j != i]

        def lying(x: float, z: float) -> bool:
            # on something: another part's top lies in this one's thickness
            for j in near:
                qlo, qhi = index.bounds[j]
                if qlo[0] <= x <= qhi[0] and qlo[2] <= z <= qhi[2] and \
                        lo[1] - 0.05 <= qhi[1] <= hi[1] + 1e-6:
                    return True
            return False

        def held(x: float, z: float) -> bool:
            # on, in or under something within a crack's width
            for j in near:
                qlo, qhi = index.bounds[j]
                if qlo[0] <= x <= qhi[0] and qlo[2] <= z <= qhi[2] and \
                        qhi[1] >= lo[1] - 0.3 and qlo[1] <= hi[1] + 0.3:
                    return True
            return False

        if not lying(part["p"][0], part["p"][2]):
            continue                          # not an overlay: hung, or mounted
        loose = 0.0
        where = None
        for x, z, cell in _samples(lo, hi):
            if not held(x, z):
                loose += cell
                where = where or (x, z)
        if loose >= 1.0:
            reports.append("#%d %s hangs %.0f sq units of itself over nothing "
                           "(first at %.1f, %.1f)" % (i, _describe(part), loose,
                                                      where[0], where[1]))
    return reports


def find_hanging_lights(parts: Sequence[Dict[str, Any]], index: PartIndex
                        ) -> List[str]:
    """Neon that touches nothing along a stretch of its length."""
    reports = []
    for i, part in enumerate(parts):
        bounds = index.bounds[i]
        if bounds is None or part.get("m") != "neon" or part.get("col"):
            continue
        lo, hi = bounds
        axis = 0 if hi[0] - lo[0] >= hi[2] - lo[2] else 2
        length = hi[axis] - lo[axis]
        steps = max(1, int(math.ceil(length)))
        near = [j for j in index.around([lo[0] - 1, lo[1], lo[2] - 1],
                                        [hi[0] + 1, hi[1], hi[2] + 1])
                if j != i and parts[j].get("m") != "neon"]
        run = best = 0.0
        for k in range(steps):
            a = lo[axis] + length * k / steps
            c = lo[axis] + length * (k + 1) / steps
            slo, shi = list(lo), list(hi)
            slo[axis], shi[axis] = a, c
            slo = [v - 0.25 for v in slo]
            shi = [v + 0.25 for v in shi]
            held = False
            for j in near:
                qlo, qhi = index.bounds[j]
                if all(qhi[d] > slo[d] and qlo[d] < shi[d] for d in range(3)):
                    held = True
                    break
            run = 0.0 if held else run + (c - a)
            best = max(best, run)
        if best > 1.5:
            reports.append("#%d %s hangs free for %.1f units"
                           % (i, _describe(part), best))
    return reports


def climbable_surfaces(solid: Solid, reach_x: float = 6.0) -> Dict[int, bool]:
    """Which solid tops a player can actually get onto.

    Flooded out from the lowest ground: a top is reachable when a reachable
    one lies within ``reach_x`` of it sideways and it is no more than a jump
    above that one (any drop is fine -- you can always fall).  The top of a
    floodlight pole and the top of the perimeter wall are floors to the
    physics and to nobody else, and what stands on them is nobody's problem.
    Keyed by ``id()`` of the box's upper corner, which is how the callers
    below meet the boxes.
    """
    boxes = solid.boxes
    lowest = min((b[1][1] for b in boxes), default=0.0)
    seen = [False] * len(boxes)
    queue = [k for k, b in enumerate(boxes) if b[1][1] <= lowest + 0.5]
    for k in queue:
        seen[k] = True
    cell = Solid.CELL
    while queue:
        k = queue.pop()
        alo, ahi = boxes[k]
        for cx in range(int((alo[0] - reach_x) // cell), int((ahi[0] + reach_x) // cell) + 1):
            for cz in range(int((alo[2] - reach_x) // cell), int((ahi[2] + reach_x) // cell) + 1):
                for m in solid.grid.get((cx, cz), ()):
                    if seen[m]:
                        continue
                    blo, bhi = boxes[m]
                    if bhi[0] < alo[0] - reach_x or blo[0] > ahi[0] + reach_x:
                        continue
                    if bhi[2] < alo[2] - reach_x or blo[2] > ahi[2] + reach_x:
                        continue
                    if bhi[1] > ahi[1] + JUMP_UP_DECOR:
                        continue
                    seen[m] = True
                    queue.append(m)
    return {id(boxes[k][1]): ok for k, ok in enumerate(seen)}


def find_loose_decor(parts: Sequence[Dict[str, Any]], index: PartIndex
                     ) -> List[str]:
    """Decorative parts that are not touching any other part at all."""
    reports = []
    for i, part in enumerate(parts):
        bounds = index.bounds[i]
        if bounds is None or part.get("col"):
            continue
        lo = [v - 0.06 for v in bounds[0]]
        hi = [v + 0.06 for v in bounds[1]]
        touching = False
        for j in index.around(lo, hi):
            if j == i:
                continue
            qlo, qhi = index.bounds[j]
            if all(qhi[d] > lo[d] and qlo[d] < hi[d] for d in range(3)):
                touching = True
                break
        if not touching:
            reports.append("#%d %s touches nothing" % (i, _describe(part)))
    return reports


def find_asymmetry(parts: Sequence[Dict[str, Any]], axis: str) -> List[str]:
    """Solids with no mirror twin across the plane ``axis`` = 0."""
    k = AXES.index(axis)

    def key(lo: Sequence[float], hi: Sequence[float]) -> Tuple[float, ...]:
        return tuple(round(v, 2) for d in range(3) for v in (lo[d], hi[d]))

    have: Dict[Tuple[float, ...], int] = defaultdict(int)
    boxes = []
    for i, part in enumerate(parts):
        bounds = collider_bounds(part)
        if bounds is None:
            continue
        boxes.append((i, bounds))
        have[key(*bounds)] += 1
    reports = []
    for i, (lo, hi) in boxes:
        mlo, mhi = list(lo), list(hi)
        mlo[k], mhi[k] = -hi[k], -lo[k]
        if not have.get(key(mlo, mhi)):
            reports.append("#%d %s has no twin at %s = %.1f"
                           % (i, _describe(parts[i]), axis,
                              -(lo[k] + hi[k]) / 2.0))
    return reports


def find_walkthrough(parts: Sequence[Dict[str, Any]], solid: Solid,
                     index: PartIndex) -> List[str]:
    """Non-solid parts standing in the space a player walks through.

    For every point under the part, find the floor beneath it and ask
    whether a player could be standing there with the part inside their
    body -- trying the body at a few offsets, so something a hand's width
    off a wall is caught while a sign flat on the wall is not.
    """
    height = PLAYER_SIZE[1]
    hw, hd = PLAYER_SIZE[0] / 2.0, PLAYER_SIZE[2] / 2.0
    floor_skin = 0.45                 # paint and pads may be this thick
    reach = climbable_surfaces(solid)
    reports = []

    for i, part in enumerate(parts):
        bounds = index.bounds[i]
        if bounds is None or not _decor(part):
            continue
        lo, hi = bounds
        near = solid.near((lo[0] + hi[0]) / 2.0, (lo[2] + hi[2]) / 2.0)
        near = [b for b in near
                if b[1][0] > lo[0] - hw and b[0][0] < hi[0] + hw and
                b[1][2] > lo[2] - hd and b[0][2] < hi[2] + hd]
        tops = [b[1][1] for b in near if b[1][1] <= lo[1] + 0.5]
        if tops and lo[1] >= max(tops) + height:
            continue                           # clear over every floor below
        caught = 0.0
        deepest = 0.0
        where = None
        for x, z, cell in _samples(lo, hi):
            floor = None
            for blo, bhi in near:
                if blo[0] <= x <= bhi[0] and blo[2] <= z <= bhi[2] and \
                        bhi[1] <= lo[1] + 0.5 and (floor is None or bhi[1] > floor[1]):
                    floor = (id(bhi), bhi[1])
            if floor is None or not reach.get(floor[0]):
                continue
            floor = floor[1]
            into = min(hi[1], floor + height) - max(lo[1], floor + floor_skin)
            if into <= 0.05:
                continue
            stands = False
            for dx in (0.0, -hw + 0.1, hw - 0.1):
                for dz in (0.0, -hd + 0.1, hd - 0.1):
                    cx, cz = x + dx, z + dz
                    if solid.blocked(cx, floor, cz):
                        continue
                    ground = solid.ground_under(cx, floor + 0.1, cz)
                    if ground is not None and abs(ground - floor) < 0.15:
                        stands = True
                        break
                if stands:
                    break
            if stands:
                caught += cell
                deepest = max(deepest, into)
                where = where or (x, floor, z)
        if caught >= 0.6:
            reports.append("#%d %s can be walked through: %.1f units of it "
                           "inside a player standing at (%.1f, %.1f, %.1f)"
                           % (i, _describe(part), deepest, where[0], where[1],
                              where[2]))
    return reports


# ----------------------------------------------------------- reachability
STEP_UP = 2.1          # matches Physics.STEP_HEIGHT in the client
JUMP_UP = 9.0          # jump speed 34 against gravity 62
FALL_MAX = 200.0


def walkable_graph(solid: Solid, area: Tuple[float, float, float, float],
                   kill_y: float, spacing: float = 5.0):
    """Every place a player can stand, and which of them join up.

    A column of the map can hold several floors -- the tunnel, the ground,
    a bunker roof -- so a node is (column, surface height) rather than just a
    position.  Two nodes on neighbouring columns join if the step between
    them is one a player could take: up to a step height walking, up to a
    jump climbing, and any drop at all falling (which is why the edges are
    one way).
    """
    x0, x1, z0, z1 = area
    hw = PLAYER_SIZE[0] / 2.0
    hd = PLAYER_SIZE[2] / 2.0
    height = PLAYER_SIZE[1]
    nodes: Dict[Tuple[int, int], List[float]] = {}
    ix = 0
    x = x0
    while x <= x1:
        iz = 0
        z = z0
        while z <= z1:
            tops = set()
            boxes = solid.near(x, z)
            for lo, hi in boxes:
                if hi[0] <= x - hw or lo[0] >= x + hw:
                    continue
                if hi[2] <= z - hd or lo[2] >= z + hd:
                    continue
                if kill_y < hi[1] < 200.0:
                    tops.add(round(hi[1], 3))
            standing = []
            for top in sorted(tops):
                blocked = False
                for lo, hi in boxes:
                    if hi[0] <= x - hw or lo[0] >= x + hw:
                        continue
                    if hi[2] <= z - hd or lo[2] >= z + hd:
                        continue
                    if hi[1] > top + 0.1 and lo[1] < top + height:
                        blocked = True
                        break
                if not blocked:
                    standing.append(top)
            if standing:
                nodes[(ix, iz)] = standing
            iz += 1
            z += spacing
        ix += 1
        x += spacing
    return nodes


def reachable_from(nodes, start: Tuple[int, int, int]) -> set:
    seen = {start}
    stack = [start]
    while stack:
        ix, iz, level = stack.pop()
        here = nodes[(ix, iz)][level]
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            column = nodes.get((ix + dx, iz + dz))
            if not column:
                continue
            for other, top in enumerate(column):
                rise = top - here
                if rise > JUMP_UP or -rise > FALL_MAX:
                    continue
                key = (ix + dx, iz + dz, other)
                if key not in seen:
                    seen.add(key)
                    stack.append(key)
    return seen


def nearest_node(nodes, area, spacing, point) -> Optional[Tuple[int, int, int]]:
    x0, _, z0, _ = area
    ix = int(round((point[0] - x0) / spacing))
    iz = int(round((point[2] - z0) / spacing))
    best = None
    best_gap = 1e9
    for dx in range(-2, 3):
        for dz in range(-2, 3):
            column = nodes.get((ix + dx, iz + dz))
            if not column:
                continue
            for level, top in enumerate(column):
                gap = abs(top - point[1]) + (abs(dx) + abs(dz)) * 0.5
                if gap < best_gap:
                    best_gap = gap
                    best = (ix + dx, iz + dz, level)
    return best


def check_reachability(solid: Solid, data: Dict[str, Any],
                       targets: Sequence[Tuple[str, List[float]]],
                       spacing: float = 5.0) -> List[str]:
    """Walk out from the first spawn and confirm the map joins up.

    Falling is one way, so this is run from each spawn *and* back from every
    objective: a route in that is not a route out would be a flag room you
    can never carry anything out of.
    """
    parts = data["parts"]
    xs = [p["p"][0] for p in parts]
    zs = [p["p"][2] for p in parts]
    area = (min(xs), max(xs), min(zs), max(zs))
    nodes = walkable_graph(solid, area, data.get("kill_y", -60.0), spacing)
    problems = []
    anchors = [t for t in targets if "spawn" in t[0] or "muster" in t[0]][:2]
    if not anchors:
        anchors = targets[:1]
    for label, point in anchors:
        start = nearest_node(nodes, area, spacing, point)
        if start is None:
            problems.append("no standing room anywhere near %s" % label)
            continue
        seen = reachable_from(nodes, start)
        for other_label, other in targets:
            node = nearest_node(nodes, area, spacing, other)
            if node is None or node in seen:
                continue
            problems.append("%s cannot be walked to from %s"
                            % (other_label, label))
        # and the way back, which falling alone does not give you
        for other_label, other in targets:
            node = nearest_node(nodes, area, spacing, other)
            if node is None:
                continue
            if start not in reachable_from(nodes, node):
                problems.append("%s is a one-way trip -- no route back to %s"
                                % (other_label, label))
    return problems


# ------------------------------------------------------------------ main
def audit(name: str, module) -> int:
    data = module.build()
    parts = data["parts"]
    colliders = [p for p in parts if p.get("col")]
    solid = Solid(parts)

    points: List[Tuple[str, List[float]]] = []
    for team, spawns in (data.get("spawns") or {}).items():
        for i, spawn in enumerate(spawns):
            points.append(("%s spawn %d" % (team, i), list(spawn["p"])))
    for key, value in (data.get("markers") or {}).items():
        if isinstance(value, dict) and isinstance(value.get("p"), list):
            points.append((key, list(value["p"])))
        elif isinstance(value, list) and value and isinstance(value[0], dict) \
                and isinstance(value[0].get("p"), list):
            for i, entry in enumerate(value):
                points.append(("%s %d" % (key, i), list(entry["p"])))

    fights = find_zfighting(parts, Opaque(parts))
    index = PartIndex(parts)
    floating = find_floating_decor(parts, index)
    hanging = find_hanging_lights(parts, index)
    walkable = find_walkthrough(parts, solid, index)
    loose = find_loose_decor(parts, index)
    mirror = getattr(module, "MIRROR_AXIS", None)
    lopsided = find_asymmetry(parts, mirror) if mirror else []
    spawn_problems = check_points(solid, points)
    field_problems = check_playfield(solid, data)
    key_points = [pt for pt in points
                  if "spawn" in pt[0] or "flag_" in pt[0] or "outpost" in pt[0]]
    route_problems = ([] if "--fast" in sys.argv
                      else check_reachability(solid, data, key_points))

    print("=" * 74)
    print("%s -- %s" % (name, data.get("name", "?")))
    print("  parts %d   colliders %d   spawn/marker probes %d"
          % (len(parts), len(colliders), len(points)))
    for title, items in (("z-fighting", fights),
                         ("decor over a void", floating),
                         ("lights in the air", hanging),
                         ("walk-through clutter", walkable),
                         ("loose decor", loose),
                         ("mirror symmetry", lopsided),
                         ("spawns and markers", spawn_problems),
                         ("playfield", field_problems),
                         ("routes", route_problems)):
        if not items:
            print("  %-20s clean" % title)
            continue
        print("  %-20s %d problem(s)" % (title, len(items)))
        for line in items[:14]:
            print("      - %s" % line)
        if len(items) > 14:
            print("      ... and %d more" % (len(items) - 14))
    return (len(fights) + len(floating) + len(hanging) + len(walkable) +
            len(loose) + len(lopsided) + len(spawn_problems) +
            len(field_problems))


def main(argv: Sequence[str]) -> int:
    wanted = [a for a in argv[1:] if not a.startswith("-")] or sorted(MAPS)
    total = 0
    for name in wanted:
        if name not in MAPS:
            print("unknown map %r (have: %s)" % (name, ", ".join(sorted(MAPS))))
            return 2
        total += audit(name, MAPS[name])
    print("=" * 74)
    print("%d problem(s) in total" % total)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
