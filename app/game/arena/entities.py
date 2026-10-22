"""The moving and changing things in an arena round.

Everything that is not the static map -- a cart on its track, a dodgeball
on the floor, a dig site, a robot on the march, a disguise decoy, a vault
door, a tornado -- is an :class:`Ent`.  The client draws each one from a
short row, ``[id, kind, x, y, z, yaw, state]``, by its kind (each world's
client plugin knows its own kinds).

Two kinds of change reach the client:

* **live** entities (they move every tick: carts, robots, balls in flight)
  ride in the snapshot as ``es`` rows;
* every other change -- something appearing, going, or changing state --
  is batched by the world into one ``ar_ents`` message per tick.

An entity can also be something people shoot at (``hp`` > 0): it has the
hitbox, ``pid`` and ``alive`` the engine's hit tests and the bots' targeting
expect, which is how robots, decoys and vault doors take damage through the
same paths players do.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Sequence, Tuple

ENT_PID_BASE = 300000        # entity pids: past players and the gear's minions


class Ent:
    __slots__ = ("id", "pid", "kind", "pos", "yaw", "s", "data", "live", "alive",
                 "team", "hp", "max_hp", "size", "vel", "username", "brain", "npc",
                 "extra", "aim_heights", "solid")

    def __init__(self, ident: int, kind: str, pos: Sequence[float], yaw: float = 0.0,
                 s: Any = 0, live: bool = False, team: str = "world",
                 hp: float = 0.0, size: Sequence[float] = (3.0, 4.0, 3.0),
                 name: str = "") -> None:
        self.id = ident
        self.pid = ENT_PID_BASE + ident
        self.kind = kind
        self.pos = [float(pos[0]), float(pos[1]), float(pos[2])]
        self.yaw = float(yaw)
        self.s = s
        self.data: Dict[str, Any] = {}
        self.live = live
        self.alive = True
        self.team = team
        self.hp = float(hp)
        self.max_hp = float(hp)
        self.size = (float(size[0]), float(size[1]), float(size[2]))
        self.vel = [0.0, 0.0, 0.0]
        self.username = name or kind.replace("_", " ").title()
        self.brain = None
        self.npc = True
        self.extra: Dict[str, Any] = {}
        self.aim_heights = (self.size[1] * 0.5, self.size[1] * 0.85)
        self.solid = False

    # ------------------------------------------------------------ wire
    def row(self) -> List[Any]:
        out: List[Any] = [self.id, self.kind, round(self.pos[0], 2), round(self.pos[1], 2),
                          round(self.pos[2], 2), round(self.yaw, 3), self.s]
        return out

    # --------------------------------------------------------- hit tests
    def hitbox(self) -> Tuple[List[float], List[float]]:
        w, h, d = self.size
        x, y, z = self.pos
        return ([x - w / 2, y, z - d / 2], [x + w / 2, y + h, z + d / 2])

    def head_box(self) -> Tuple[List[float], List[float]]:
        w, h, d = self.size
        x, y, z = self.pos
        return ([x - w * 0.3, y + h * 0.75, z - d * 0.3], [x + w * 0.3, y + h, z + d * 0.3])

    def centre(self) -> List[float]:
        return [self.pos[0], self.pos[1] + self.size[1] * 0.5, self.pos[2]]

    def send(self, payload: Dict[str, Any]) -> None:
        """Entities have no connection; the engine's sends land here."""


# ================================================================== tracks
class Track:
    """A polyline anything can ride: a cart's rails, a convoy's road, a
    robot's march.  ``point_at(d)`` is where you are ``d`` units along it and
    which way you face."""

    def __init__(self, points: Sequence[Sequence[float]]):
        self.points = [list(map(float, p)) for p in points]
        self.lengths: List[float] = []
        total = 0.0
        for a, b in zip(self.points, self.points[1:]):
            seg = math.dist(a, b)
            self.lengths.append(seg)
            total += seg
        self.length = total

    def point_at(self, distance: float) -> Tuple[List[float], float]:
        distance = max(0.0, min(self.length, distance))
        for (a, b), seg in zip(zip(self.points, self.points[1:]), self.lengths):
            if distance <= seg:
                f = 0.0 if seg < 1e-6 else min(1.0, distance / seg)
                pos = [a[i] + (b[i] - a[i]) * f for i in range(3)]
                return pos, math.atan2(b[0] - a[0], b[2] - a[2])
            distance -= seg
        last, prev = self.points[-1], self.points[-2]
        return list(last), math.atan2(last[0] - prev[0], last[2] - prev[2])

    def nearest(self, pos: Sequence[float]) -> Tuple[float, float]:
        """(distance along the track, distance from it) of the closest point."""
        best_d, best_along, run = 1e18, 0.0, 0.0
        for (a, b), seg in zip(zip(self.points, self.points[1:]), self.lengths):
            if seg < 1e-6:
                continue
            t = ((pos[0] - a[0]) * (b[0] - a[0]) + (pos[2] - a[2]) * (b[2] - a[2])) / (seg * seg)
            t = max(0.0, min(1.0, t))
            px, pz = a[0] + (b[0] - a[0]) * t, a[2] + (b[2] - a[2]) * t
            d = math.hypot(pos[0] - px, pos[2] - pz)
            if d < best_d:
                best_d, best_along = d, run + seg * t
            run += seg
        return best_along, best_d


def flat_dist(a: Sequence[float], b: Sequence[float]) -> float:
    return math.hypot(a[0] - b[0], a[2] - b[2])
