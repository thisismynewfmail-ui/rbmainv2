"""Where a bot can walk, and how to get from here to there.

**The graph.**  The map is sampled on a grid every few units; at each column
every surface a player could stand on -- with a player's full height of clear
air above it -- becomes a node, so the tunnel, the road over it and the
bunker roof above that are three nodes in one column.  Neighbouring nodes join
when a player could make the move: a step, a jump (up to the height a jump
actually reaches) or a drop.  Every edge is swept with the player's box first,
which is what stops a path walking through a wall thinner than the grid.

**Getting about.**  Fixed objectives (flags, bases, spawn rooms, the cart
track, tycoon pads) get a *flow field*: one backwards Dijkstra from the
target, after which every bot anywhere on the map knows its next step in
constant time.  Anything that moves gets a budgeted A*, and a path is
string-pulled across open ground so bots walk straight lines rather than
staircase along the grid.

**Cost.**  Building Ironvale's graph takes well under a second on a desktop and
a few seconds on a Raspberry Pi, so it happens on a background thread when the
host starts and is cached on disk keyed by the map's own geometry: a restart
reads it back in milliseconds.
"""
from __future__ import annotations

import hashlib
import heapq
import json
import math
import os
import threading
import time
from array import array
from typing import Any, Dict, List, Optional, Sequence, Tuple

from ..instance import PLAYER_SIZE

STEP_UP = 2.1          # matches Physics.STEP_HEIGHT in the client
JUMP_UP = 8.2          # a jump peaks at ~9.3 with gravity 62 and speed 34
DROP_MAX = 34.0        # the furthest a bot will choose to drop
SPACING = 4.0
BUCKET = 8.0
INF = 1e30
VERSION = 3

CACHE_DIR = None       # set lazily from app.config


def _cache_dir():
    global CACHE_DIR
    if CACHE_DIR is None:
        from ... import config
        CACHE_DIR = config.DATA_DIR / "navcache"
    return CACHE_DIR


class NavGrid:
    def __init__(self, name: str, map_data: Dict[str, Any],
                 colliders: Sequence[Tuple[List[float], List[float]]],
                 spacing: float = SPACING):
        self.name = name
        self.map = map_data
        self.boxes = list(colliders)
        self.spacing = spacing
        self.ready = False
        self.building = False
        self.error = ""
        self.fields: Dict[str, array] = {}
        self._field_lock = threading.Lock()
        self._pending_fields: List[Tuple[str, int]] = []
        parts = map_data.get("parts", [])
        xs = [p["p"][0] for p in parts] or [0.0]
        zs = [p["p"][2] for p in parts] or [0.0]
        self.x0 = min(xs) - spacing
        self.z0 = min(zs) - spacing
        self.nx = int((max(xs) - self.x0) / spacing) + 3
        self.nz = int((max(zs) - self.z0) / spacing) + 3
        self.kill_y = float(map_data.get("kill_y", -60.0))
        self.px = array("f")
        self.py = array("f")
        self.pz = array("f")
        self.cols: Dict[int, Tuple[int, ...]] = {}
        self.out_off = array("I")
        self.out_to = array("I")
        self.out_cost = array("f")
        self.in_off = array("I")
        self.in_to = array("I")
        self.in_cost = array("f")
        self.build_ms = 0.0

    # ---------------------------------------------------------------- build
    def key(self) -> str:
        digest = hashlib.sha1()
        digest.update(("%s|%s|%d" % (self.name, self.spacing, VERSION)).encode())
        for lo, hi in self.boxes:
            digest.update(("%.2f,%.2f,%.2f,%.2f,%.2f,%.2f;" % (
                lo[0], lo[1], lo[2], hi[0], hi[1], hi[2])).encode())
        return digest.hexdigest()[:16]

    def build_async(self) -> None:
        if self.ready or self.building:
            return
        self.building = True
        threading.Thread(target=self._build_safely, daemon=True,
                         name="nav-%s" % self.name).start()

    def _build_safely(self) -> None:
        try:
            if not self._load_cache():
                self.build()
                self._save_cache()
            self.ready = True
        except Exception as exc:          # a bad map must not take the host down
            self.error = str(exc)
        finally:
            self.building = False

    def build(self) -> None:
        started = time.time()
        boxes = self.boxes
        grid: Dict[Tuple[int, int], List[int]] = {}
        for index, (lo, hi) in enumerate(boxes):
            for cx in range(int(math.floor(lo[0] / BUCKET)), int(math.floor(hi[0] / BUCKET)) + 1):
                for cz in range(int(math.floor(lo[2] / BUCKET)), int(math.floor(hi[2] / BUCKET)) + 1):
                    grid.setdefault((cx, cz), []).append(index)
        hw, hd, height = PLAYER_SIZE[0] / 2.0, PLAYER_SIZE[2] / 2.0, PLAYER_SIZE[1]
        px, py, pz = self.px, self.py, self.pz
        cols: Dict[int, Tuple[int, ...]] = {}

        def near(x0, x1, z0, z1):
            seen = set()
            for cx in range(int(math.floor(x0 / BUCKET)), int(math.floor(x1 / BUCKET)) + 1):
                for cz in range(int(math.floor(z0 / BUCKET)), int(math.floor(z1 / BUCKET)) + 1):
                    for index in grid.get((cx, cz), ()):
                        if index not in seen:
                            seen.add(index)
                            yield boxes[index]

        for ix in range(self.nx):
            x = self.x0 + ix * self.spacing
            for iz in range(self.nz):
                z = self.z0 + iz * self.spacing
                overlap = [(lo[1], hi[1]) for lo, hi in near(x - hw, x + hw, z - hd, z + hd)
                           if hi[0] > x - hw and lo[0] < x + hw and hi[2] > z - hd and lo[2] < z + hd]
                if not overlap:
                    continue
                tops = sorted({round(h, 2) for _l, h in overlap if self.kill_y < h < 220.0})
                ids = []
                for top in tops:
                    if any(h > top + 0.1 and l < top + height for l, h in overlap):
                        continue
                    ids.append(len(px))
                    px.append(x)
                    py.append(top)
                    pz.append(z)
                if ids:
                    cols[ix * self.nz + iz] = tuple(ids)
        self.cols = cols

        def blocked(xa, za, xb, zb, y0, y1) -> bool:
            lx, hx = min(xa, xb) - hw * 0.8, max(xa, xb) + hw * 0.8
            lz, hz = min(za, zb) - hd * 0.8, max(za, zb) + hd * 0.8
            for lo, hi in near(lx, hx, lz, hz):
                if hi[0] > lx and lo[0] < hx and hi[2] > lz and lo[2] < hz \
                        and hi[1] > y0 and lo[1] < y1:
                    return True
            return False

        out: List[List[Tuple[int, float]]] = [[] for _ in range(len(px))]
        diag = self.spacing * math.sqrt(2.0)
        for key, ids in cols.items():
            ix, iz = divmod(key, self.nz)
            for dx, dz in ((1, 0), (0, 1), (1, 1), (1, -1)):
                jx, jz = ix + dx, iz + dz
                if not (0 <= jz < self.nz):
                    continue
                other = cols.get(jx * self.nz + jz)
                if not other:
                    continue
                if dx and dz:
                    # no corner cutting: both sides of the diagonal must be open
                    if ix * self.nz + jz not in cols or jx * self.nz + iz not in cols:
                        continue
                flat = diag if (dx and dz) else self.spacing
                for a in ids:
                    for b in other:
                        rise = py[b] - py[a]
                        if abs(rise) > DROP_MAX:
                            continue
                        top = max(py[a], py[b])
                        if blocked(px[a], pz[a], px[b], pz[b], top + 0.15, top + height):
                            continue
                        up_ab = rise
                        cost_ab = flat + (4.0 if up_ab > STEP_UP else 0.0) + max(0.0, up_ab) * 0.4
                        cost_ba = flat + (4.0 if -up_ab > STEP_UP else 0.0) + max(0.0, -up_ab) * 0.4
                        if up_ab <= JUMP_UP:
                            out[a].append((b, cost_ab))
                        if -up_ab <= JUMP_UP:
                            out[b].append((a, cost_ba))
        self._pack(out)
        self.build_ms = (time.time() - started) * 1000.0

    def _pack(self, out: List[List[Tuple[int, float]]]) -> None:
        n = len(out)
        incoming: List[List[Tuple[int, float]]] = [[] for _ in range(n)]
        self.out_off = array("I", [0])
        self.out_to = array("I")
        self.out_cost = array("f")
        for a, edges in enumerate(out):
            for b, cost in edges:
                self.out_to.append(b)
                self.out_cost.append(cost)
                incoming[b].append((a, cost))
            self.out_off.append(len(self.out_to))
        self.in_off = array("I", [0])
        self.in_to = array("I")
        self.in_cost = array("f")
        for b, edges in enumerate(incoming):
            for a, cost in edges:
                self.in_to.append(a)
                self.in_cost.append(cost)
            self.in_off.append(len(self.in_to))

    # ---------------------------------------------------------------- cache
    def _cache_path(self):
        return _cache_dir() / ("%s-%s.nav" % (self.name, self.key()))

    def _save_cache(self) -> None:
        try:
            path = self._cache_path()
            path.parent.mkdir(parents=True, exist_ok=True)
            header = {"cols": [[k, list(v)] for k, v in self.cols.items()],
                      "sizes": {name: len(getattr(self, name)) for name in (
                          "px", "py", "pz", "out_off", "out_to", "out_cost",
                          "in_off", "in_to", "in_cost")}}
            temp = str(path) + ".tmp"
            with open(temp, "wb") as handle:
                blob = json.dumps(header).encode()
                handle.write(len(blob).to_bytes(4, "little"))
                handle.write(blob)
                for name in ("px", "py", "pz", "out_off", "out_to", "out_cost",
                             "in_off", "in_to", "in_cost"):
                    handle.write(getattr(self, name).tobytes())
            os.replace(temp, str(path))
        except OSError:
            pass

    def _load_cache(self) -> bool:
        path = self._cache_path()
        try:
            with open(path, "rb") as handle:
                size = int.from_bytes(handle.read(4), "little")
                header = json.loads(handle.read(size).decode())
                for name, code in (("px", "f"), ("py", "f"), ("pz", "f"),
                                   ("out_off", "I"), ("out_to", "I"), ("out_cost", "f"),
                                   ("in_off", "I"), ("in_to", "I"), ("in_cost", "f")):
                    data = array(code)
                    count = int(header["sizes"][name])
                    data.frombytes(handle.read(count * data.itemsize))
                    if len(data) != count:
                        return False
                    setattr(self, name, data)
            self.cols = {int(k): tuple(v) for k, v in header["cols"]}
            return True
        except (OSError, ValueError, KeyError):
            return False

    # ---------------------------------------------------------------- query
    @property
    def size(self) -> int:
        return len(self.px)

    def column(self, x: float, z: float) -> Tuple[int, int]:
        return (int(round((x - self.x0) / self.spacing)),
                int(round((z - self.z0) / self.spacing)))

    def nearest(self, pos: Sequence[float], reach: int = 2) -> int:
        """The node a position stands on (or nearest to), or -1."""
        if not self.ready:
            return -1
        ix, iz = self.column(pos[0], pos[2])
        best, best_score = -1, INF
        for r in range(0, reach + 1):
            for dx in range(-r, r + 1):
                for dz in range(-r, r + 1):
                    if max(abs(dx), abs(dz)) != r:
                        continue
                    ids = self.cols.get((ix + dx) * self.nz + (iz + dz))
                    if not ids:
                        continue
                    for node in ids:
                        dy = self.py[node] - pos[1]
                        # prefer the floor under the feet over the roof above
                        vertical = abs(dy) * (3.0 if dy > 2.6 else 1.0)
                        score = vertical + math.hypot(self.px[node] - pos[0],
                                                      self.pz[node] - pos[2])
                        if score < best_score:
                            best, best_score = node, score
            if best >= 0 and r >= 1:
                break
        return best

    def point(self, node: int) -> List[float]:
        return [self.px[node], self.py[node], self.pz[node]]

    def neighbours(self, node: int):
        for k in range(self.out_off[node], self.out_off[node + 1]):
            yield self.out_to[k], self.out_cost[k]

    # --------------------------------------------------------------- fields
    def field(self, name: str, target: Sequence[float]) -> Optional[array]:
        """Distance-to-target for every node, built once (in the background)."""
        found = self.fields.get(name)
        if found is not None:
            return found
        if not self.ready:
            return None
        with self._field_lock:
            if name in self.fields or any(p[0] == name for p in self._pending_fields):
                return self.fields.get(name)
            node = self.nearest(target, 3)
            if node < 0:
                return None
            self._pending_fields.append((name, node))
            if len(self._pending_fields) == 1:
                threading.Thread(target=self._field_worker, daemon=True,
                                 name="nav-field").start()
        return None

    def _field_worker(self) -> None:
        while True:
            with self._field_lock:
                if not self._pending_fields:
                    return
                name, node = self._pending_fields[0]
            dist = self._dijkstra(node)
            with self._field_lock:
                self.fields[name] = dist
                self._pending_fields.pop(0)
            time.sleep(0.01)

    def _dijkstra(self, target: int) -> array:
        """Backwards Dijkstra: every node's distance *to* ``target``.

        Run in doubles and stored as float32 afterwards; comparing heap
        entries against rounded float32 values skips nodes on a big map.
        """
        n = self.size
        dist = [INF] * n
        dist[target] = 0.0
        heap = [(0.0, target)]
        in_off, in_to, in_cost = self.in_off, self.in_to, self.in_cost
        pops = 0
        while heap:
            d, v = heapq.heappop(heap)
            if d > dist[v]:
                continue
            pops += 1
            if pops % 4000 == 0:
                time.sleep(0)          # let the tick thread in
            for k in range(in_off[v], in_off[v + 1]):
                u = in_to[k]
                nd = d + in_cost[k]
                if nd < dist[u]:
                    dist[u] = nd
                    heapq.heappush(heap, (nd, u))
        return array("f", dist)

    def downhill(self, node: int, dist: array) -> int:
        """The next node towards a field's target, or -1 at the target."""
        best, best_cost = -1, dist[node]
        for k in range(self.out_off[node], self.out_off[node + 1]):
            v = self.out_to[k]
            cost = dist[v] + self.out_cost[k] * 0.01
            if cost < best_cost:
                best, best_cost = v, cost
        return best

    def follow(self, node: int, dist: array, steps: int = 40) -> List[int]:
        path = []
        current = node
        for _ in range(steps):
            nxt = self.downhill(current, dist)
            if nxt < 0:
                break
            path.append(nxt)
            current = nxt
        return path

    # ------------------------------------------------------------------ A*
    def astar(self, start: int, goal: int, budget: int = 1500) -> Optional[List[int]]:
        if start < 0 or goal < 0:
            return None
        if start == goal:
            return [goal]
        px, pz = self.px, self.pz
        gx, gz = px[goal], pz[goal]
        came: Dict[int, int] = {start: -1}
        cost: Dict[int, float] = {start: 0.0}
        heap = [(math.hypot(px[start] - gx, pz[start] - gz), 0.0, start)]
        best, best_h = start, INF
        expanded = 0
        while heap and expanded < budget:
            _f, g, node = heapq.heappop(heap)
            if g > cost.get(node, INF):
                continue
            expanded += 1
            if node == goal:
                best = goal
                break
            h = math.hypot(px[node] - gx, pz[node] - gz)
            if h < best_h:
                best, best_h = node, h
            for k in range(self.out_off[node], self.out_off[node + 1]):
                nxt = self.out_to[k]
                ng = g + self.out_cost[k]
                if ng < cost.get(nxt, INF):
                    cost[nxt] = ng
                    came[nxt] = node
                    heapq.heappush(heap, (ng + math.hypot(px[nxt] - gx, pz[nxt] - gz), ng, nxt))
        # out of budget: go as far as it got towards the goal
        path = []
        node = best
        while node != -1 and node != start:
            path.append(node)
            node = came.get(node, -1)
        path.reverse()
        return path or None

    # ------------------------------------------------------------- smoothing
    def clear_line(self, a: Sequence[float], b: Sequence[float]) -> bool:
        """Whether a straight walk from a to b stays on walkable ground at a
        steady height -- used to cut corners out of grid paths."""
        dx, dz = b[0] - a[0], b[2] - a[2]
        length = math.hypot(dx, dz)
        steps = max(1, int(length / (self.spacing * 0.5)))
        for s in range(1, steps):
            f = s / float(steps)
            x, z = a[0] + dx * f, a[2] + dz * f
            y = a[1] + (b[1] - a[1]) * f
            ix, iz = self.column(x, z)
            ids = self.cols.get(ix * self.nz + iz)
            if not ids:
                return False
            if not any(abs(self.py[n] - y) <= STEP_UP for n in ids):
                return False
        return True

    def smooth(self, start: Sequence[float], nodes: List[int], limit: int = 10) -> List[List[float]]:
        """Grid path -> waypoints, skipping every node a straight line can."""
        points = [self.point(n) for n in nodes]
        if not points:
            return []
        out: List[List[float]] = []
        anchor = list(start)
        index = 0
        while index < len(points):
            reach = index
            for j in range(min(len(points) - 1, index + limit), index, -1):
                if abs(points[j][1] - anchor[1]) <= STEP_UP and self.clear_line(anchor, points[j]):
                    reach = j
                    break
            out.append(points[reach])
            anchor = points[reach]
            index = reach + 1
        return out

    def random_node(self, rng, near: Optional[Sequence[float]] = None,
                    radius: float = 80.0, tries: int = 30) -> int:
        if not self.ready or not self.size:
            return -1
        for _ in range(tries):
            if near is None:
                node = rng.randrange(self.size)
            else:
                x = near[0] + rng.uniform(-radius, radius)
                z = near[2] + rng.uniform(-radius, radius)
                ix, iz = self.column(x, z)
                ids = self.cols.get(ix * self.nz + iz)
                if not ids:
                    continue
                node = rng.choice(ids)
            if self.out_off[node + 1] - self.out_off[node] >= 3:
                return node
        return -1


_grids: Dict[str, NavGrid] = {}
_grids_lock = threading.Lock()


def for_map(name: str, map_data: Dict[str, Any], colliders) -> NavGrid:
    """One graph per map per host process, shared by all its instances."""
    with _grids_lock:
        grid = _grids.get(name)
        if grid is None:
            grid = NavGrid(name, map_data, colliders)
            _grids[name] = grid
        return grid
