"""What Whodunit's four places share: named rooms (the case file's "seen
near the library" comes from these), the marks the rules and the bots use,
and a few fittings every grand old building has.

Marks:

``clue``    where a clue can turn up (on a floor, at floor height)
``roam``    the middle of a room: where a bot wanders to, and flees to
``stair``   each end of a staircase, with where the other end is (``to``)
start       the guests' spawns (``team_spawn("start", ...)``)

Room names are landmarks *with a height*, so the room over the library is
not mistaken for the library.
"""
from __future__ import annotations

from typing import Any, Dict, List, Sequence, Tuple

from ..kit import ArenaArea
from ..prop_panic.catalogue import BLACK, BRASS, C, CREAM, K, S, Part, stamp
from ..prop_panic.rooms import GLASS, openings, trim, window

# a door or a window in a wall: (start, end, bottom, top, kind), the kind
# "door" (trimmed round), "win" (glazed and framed) or "open" (a bare hole)
Hole = Tuple[float, float, float, float, str]


def room(b: ArenaArea, name: str, x: float, y: float, z: float,
         clues: Sequence[Tuple[float, float]] = (), roam: bool = True) -> None:
    """A named room: its landmark at (x, y, z), a ``roam`` mark there, and a
    ``clue`` mark at each (x, z) given, on the same floor."""
    b.landmarks.append({"p": b.at(x, y, z), "name": name})
    if roam:
        b.mark("roam", x, y, z)
    for cx, cz in clues:
        b.mark("clue", cx, y, cz)


def stair(b: ArenaArea, low: Tuple[float, float, float], high: Tuple[float, float, float]) -> None:
    """Both ends of a staircase, for the bots: a ``stair`` mark on the floor
    just off each end, carrying where the other end comes out (``to``).  A
    bot bound for another floor walks to the nearest one that takes it the
    right way rather than to the spot over (or under) where it is going."""
    b.mark("stair", *low, to=b.at(*high))
    b.mark("stair", *high, to=b.at(*low))


def chandelier(drop: float = 3.4, arms: int = 6, metal: str = BRASS,
               lamp: str = "#ffe2a8") -> List[Part]:
    """A chandelier hanging ``drop`` under a ceiling at y = 0 (stamp it at
    the ceiling's underside), candles round a ring."""
    import math
    parts: List[Part] = [
        C(0.0, -drop + 1.0, 0.0, 0.16, drop - 1.0, 0.16, BLACK, ghost=True),
        S(0.0, -drop + 0.4, 0.0, 3.6, 0.3, 3.6, metal, m="metal", ghost=True),
        S(0.0, -drop - 0.2, 0.0, 0.9, 0.9, 0.9, metal, m="metal", ghost=True),
    ]
    for k in range(arms):
        a = k * 2.0 * math.pi / arms
        x, z = math.cos(a) * 1.6, math.sin(a) * 1.6
        parts.append(C(x, -drop + 0.7, z, 0.24, 0.6, 0.24, CREAM, ghost=True))
        parts.append(K(x, -drop + 1.3, z, 0.24, 0.42, 0.24, lamp, m="neon", ghost=True))
    return parts


def candelabra(metal: str = BRASS) -> List[Part]:
    """Three candles on a stand, for a table or a mantel (y 0 is what it
    stands on)."""
    return [
        C(0.0, 0.0, 0.0, 0.7, 0.2, 0.7, metal, m="metal"),
        C(0.0, 0.2, 0.0, 0.16, 1.4, 0.16, metal, m="metal"),
        C(-0.5, 1.4, 0.0, 0.2, 0.7, 0.2, CREAM),
        C(0.0, 1.6, 0.0, 0.2, 0.7, 0.2, CREAM),
        C(0.5, 1.4, 0.0, 0.2, 0.7, 0.2, CREAM),
        K(-0.5, 2.1, 0.0, 0.16, 0.34, 0.16, "#ffd23a", m="neon", ghost=True),
        K(0.0, 2.3, 0.0, 0.16, 0.34, 0.16, "#ffd23a", m="neon", ghost=True),
        K(0.5, 2.1, 0.0, 0.16, 0.34, 0.16, "#ffd23a", m="neon", ghost=True),
    ]


def hang(b: ArenaArea, parts: Sequence[Part], x: float, ceiling: float, z: float) -> None:
    """Hang a light (drawn with its ceiling at y = 0) from a ceiling whose
    underside is at ``ceiling``."""
    stamp(b, parts, x, z, ceiling)


def rails(b: ArenaArea, area: Tuple[float, float, float, float], y: float, open_side: str,
          colour: str, height: float = 3.2, t: float = 0.4) -> None:
    """A banister round a hole in a floor at ``y``, outside its edge, on
    every side but ``open_side`` (where the stairs arrive).  The sides along
    z run the full length; the ones along x fit between them."""
    x0, x1, z0, z1 = area
    h = height / 2.0
    if open_side != "x-":
        b.box([x0 - t / 2.0, y + h, (z0 + z1) / 2.0], [t, height, z1 - z0 + 2 * t], colour)
    if open_side != "x+":
        b.box([x1 + t / 2.0, y + h, (z0 + z1) / 2.0], [t, height, z1 - z0 + 2 * t], colour)
    if open_side != "z-":
        b.box([(x0 + x1) / 2.0, y + h, z0 - t / 2.0], [x1 - x0, height, t], colour)
    if open_side != "z+":
        b.box([(x0 + x1) / 2.0, y + h, z1 + t / 2.0], [x1 - x0, height, t], colour)


class Walls:
    """Every wall of a building, kept so a room's paint can find the doors
    and windows in its own walls (on both storeys, for a hall two storeys
    high).  ``add`` records a wall; ``build`` puts them all up with their
    door trims, window frames and glass; ``holes_for`` gives a room's paint
    its holes, side by side."""

    def __init__(self, trim: str, frame: str) -> None:
        self.trim = trim
        self.frame = frame
        self.walls: List[Dict[str, Any]] = []

    def add(self, axis: str, at: float, lo: float, hi: float, y0: float, y1: float, colour: str,
            holes: Sequence[Hole] = (), t: float = 0.6, floor: float = -1e9, out: int = 1) -> None:
        """A wall along ``axis`` standing at ``at``, from ``lo`` to ``hi``
        and ``y0`` to ``y1``.  ``floor`` is where a door's trim starts when
        the wall goes down past the floor (an outside wall from the ground);
        ``out`` is the side its windows' outside is on."""
        self.walls.append({"axis": axis, "at": at, "lo": lo, "hi": hi, "y0": y0, "y1": y1,
                           "colour": colour, "holes": list(holes), "t": t,
                           "floor": max(y0, floor), "out": out})

    def build(self, b: ArenaArea) -> None:
        for w in self.walls:
            axis, at, t = w["axis"], w["at"], w["t"]
            openings(b, axis, at, t, w["lo"], w["hi"], w["y0"], w["y1"], w["colour"],
                     [h[:4] for h in w["holes"]])
            for a, c, bottom, top, kind in w["holes"]:
                if kind == "door":
                    trim(b, axis, at, t, a, c, w["floor"], top, self.trim)
                elif kind == "win" and bottom > w["y0"] + 1e-6:
                    if axis == "z":
                        b.box([at, (bottom + top) / 2.0, (a + c) / 2.0], [t * 0.3, top - bottom, c - a],
                              GLASS, material="glass", alpha=0.42)
                    else:
                        b.box([(a + c) / 2.0, (bottom + top) / 2.0, at], [c - a, top - bottom, t * 0.3],
                              GLASS, material="glass", alpha=0.42)
                    window(b, axis, at, t, a, c, bottom, top, self.frame, out=w["out"])

    def holes_for(self, inner: Tuple[float, float, float, float], y0: float, y1: float
                  ) -> Dict[str, List[Tuple[float, float, float, float]]]:
        """The paint holes on each side of a room whose walls' faces enclose
        ``inner``, from ``y0`` to ``y1``: a door's hole takes in its trim, a
        doorway reaches under the floor, and a door in a wall that starts
        above this room's floor (a gallery's) starts where that wall does."""
        x0, x1, z0, z1 = inner
        out: Dict[str, List[Tuple[float, float, float, float]]] = {"x-": [], "x+": [], "z-": [],
                                                                   "z+": []}
        for w in self.walls:
            if w["y1"] <= y0 + 1e-6 or w["y0"] >= y1 - 1e-6:
                continue
            half = w["t"] / 2.0
            if w["axis"] == "z":
                span = (z0, z1)
                sides = [s for s, face, wall in (("x-", x0, w["at"] + half), ("x+", x1, w["at"] - half))
                         if abs(face - wall) < 0.05]
            else:
                span = (x0, x1)
                sides = [s for s, face, wall in (("z-", z0, w["at"] + half), ("z+", z1, w["at"] - half))
                         if abs(face - wall) < 0.05]
            if not sides or w["hi"] <= span[0] + 1e-6 or w["lo"] >= span[1] - 1e-6:
                continue
            for a, c, bottom, top, kind in w["holes"]:
                if c <= span[0] or a >= span[1] or top <= y0 or bottom >= y1:
                    continue
                doorway = bottom <= w["y0"] + 1e-6
                if kind == "door":
                    a, c, top = a - 0.5, c + 0.5, top + 0.5
                if doorway:
                    bottom = y0 - 1.0 if w["y0"] <= y0 + 1e-6 else w["y0"]
                for side in sides:
                    out[side].append((a, c, bottom, top))
        return out
