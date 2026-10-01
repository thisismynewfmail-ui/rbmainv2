"""The infected of Last Light: what each kind is, and how one hunts.

**Kinds.**  The commons are the bulk of every wave -- shambling people in
whatever they died in, green-skinned, two dot eyes and a mouth hung open --
with a share of *runners* among them from the third wave on.  Eleven special
kinds are rarer, each with one trick that the team has to answer together,
and every fifth wave a Tank comes with them.  Each kind's numbers live in
:data:`KINDS`; what it *does* lives in the ``_think_<kind>`` methods below.

**Hunting.**  One horde field serves every infected in the area: a backwards
Dijkstra over the navigation graph from every survivor at once (so each
infected's downhill neighbour is the next step towards its *nearest*
survivor, by walking distance, not by line), recomputed about once a second
on a background thread.  A biled survivor and the area's lure are sources
with a head start, which is all "everything comes for the one covered in
bile" and "the bell draws them" need to be.  Close in, an infected that can
see a survivor on its own level walks straight at them; one blocked by a
wall it cannot path round (a survivor up on a car, a container, a ledge)
claws its way up it, so there is no perch the horde cannot reach.

**Cost.**  Bodies use the same collision as the bots' (``bots/body.py``) but
against a short list of nearby solids cached per infected, and an infected
far from every survivor is stepped a few times a second instead of twenty.
"""
from __future__ import annotations

import heapq
import math
import random
import threading
import time
from typing import Any, Dict, List, Optional, Sequence, Tuple

from ..bots import body as body_module
from ..bots import nav as nav_module
from ..instance import GRAVITY, JUMP_SPEED, now, ray_aabb

INF = 1e30
ZID_BASE = 100000          # infected ids never collide with player ids

# ------------------------------------------------------------------ kinds
# hp, speed, melee damage, melee reach, seconds between swings, score,
# hit box (width, height, depth, head bottom), and what the kill feed calls it
KINDS: Dict[str, Dict[str, Any]] = {
    "common":   dict(hp=45, speed=19.5, dmg=6, reach=4.2, rate=1.05, score=1,
                     box=(3.0, 5.4, 2.0, 4.0), name="Infected"),
    "runner":   dict(hp=34, speed=25.0, dmg=5, reach=4.2, rate=0.9, score=1,
                     box=(3.0, 5.4, 2.0, 4.0), name="Runner"),
    "bloater":  dict(hp=60, speed=12.5, dmg=4, reach=4.6, rate=1.3, score=5,
                     box=(4.6, 5.8, 3.8, 4.6), name="Bloater", special=True),
    "bomber":   dict(hp=70, speed=20.5, dmg=5, reach=4.2, rate=1.2, score=6,
                     box=(3.0, 5.4, 2.2, 4.0), name="Bomber", special=True),
    "leaper":   dict(hp=150, speed=21.0, dmg=6, reach=4.2, rate=0.9, score=6,
                     box=(3.0, 4.8, 2.2, 3.5), name="Leaper", special=True),
    "brute":    dict(hp=650, speed=15.0, dmg=14, reach=5.4, rate=1.4, score=10,
                     box=(4.8, 7.2, 3.6, 5.8), name="Brute", special=True),
    "spitter":  dict(hp=110, speed=17.0, dmg=5, reach=4.2, rate=1.2, score=6,
                     box=(2.8, 6.0, 2.0, 4.6), name="Spitter", special=True),
    "screamer": dict(hp=120, speed=18.0, dmg=4, reach=4.2, rate=1.2, score=7,
                     box=(2.8, 5.6, 2.0, 4.2), name="Screamer", special=True),
    "riot":     dict(hp=320, speed=14.5, dmg=11, reach=4.6, rate=1.2, score=8,
                     box=(3.6, 5.9, 2.6, 4.4), name="Riot", special=True),
    "captain":  dict(hp=420, speed=15.5, dmg=10, reach=4.6, rate=1.2, score=12,
                     box=(3.2, 6.4, 2.2, 4.8), name="Plague Captain", special=True),
    "hive":     dict(hp=260, speed=14.0, dmg=8, reach=4.6, rate=1.2, score=8,
                     box=(4.4, 6.0, 3.6, 4.6), name="Hive", special=True),
    "mite":     dict(hp=10, speed=27.0, dmg=3, reach=3.2, rate=0.7, score=0,
                     box=(1.6, 1.8, 1.6, 1.0), name="Mite"),
    "ronin":    dict(hp=380, speed=18.5, dmg=10, reach=4.8, rate=1.1, score=10,
                     box=(3.0, 5.8, 2.2, 4.4), name="Ronin", special=True),
    "burrower": dict(hp=220, speed=16.0, dmg=9, reach=4.4, rate=1.1, score=8,
                     box=(3.0, 5.4, 2.2, 4.0), name="Burrower", special=True),
    "tank":     dict(hp=3000, speed=17.5, dmg=34, reach=6.6, rate=1.6, score=40,
                     box=(6.4, 9.0, 4.6, 7.4), name="Tank", special=True,
                     boss=True),
}
KIND_CODES = ["common", "runner", "bloater", "bomber", "leaper", "brute",
              "spitter", "screamer", "riot", "captain", "hive", "mite", "ronin",
              "burrower", "tank"]
KIND_INDEX = {kind: i for i, kind in enumerate(KIND_CODES)}
SPECIALS = [k for k in KIND_CODES if KINDS[k].get("special") and k != "tank"]
# the wave each special first turns up in, and how often after that
UNLOCK = {"bloater": 1, "spitter": 1, "leaper": 2, "bomber": 2, "brute": 3,
          "screamer": 3, "riot": 4, "hive": 5, "burrower": 6, "ronin": 7,
          "captain": 8}
WEIGHT = {"bloater": 1.0, "spitter": 1.0, "leaper": 1.1, "bomber": 0.9,
          "brute": 0.7, "screamer": 0.6, "riot": 0.8, "hive": 0.7,
          "burrower": 0.7, "ronin": 0.6, "captain": 0.45}

# animation codes on the wire
A_WALK, A_RUN, A_ATTACK, A_LEAP, A_SCREAM, A_STUN, A_CLIMB, A_THROW, \
    A_RISE, A_PIN, A_CHARGE, A_SPIT, A_BURROW, A_GUARD, A_SLAM = range(15)
# flag bits on the wire
F_ENRAGED, F_HIDDEN, F_GUARD, F_FUSE, F_CHARGING, F_PINNING, F_STUNNED, \
    F_LURED = (1, 2, 4, 8, 16, 32, 64, 128)

VARIANTS = 8               # common looks per area (the client draws them)


class Zombie:
    """One infected.  Duck-typed enough like a Player that the bots can
    target it and the kill feed can name it."""

    __slots__ = ("pid", "kind", "variant", "pos", "vel", "yaw", "pitch",
                 "health", "max_health", "alive", "team", "username", "brain",
                 "npc", "grounded", "speed", "dmg", "state", "state_until",
                 "next_attack", "target", "last_seen", "born", "waypoints",
                 "path_at", "node", "airborne", "vy", "boxes", "boxes_at",
                 "enraged_until", "data", "anim", "flags", "hit_wall",
                 "progress", "progress_at", "climb_from", "last_step",
                 "wave", "score_value", "lured", "damage_by", "kills", "score",
                 "streak", "deaths", "last_ground_pos", "spawned_at", "seen_by")

    def __init__(self, zid: int, kind: str, pos: Sequence[float], variant: int,
                 hp: float, speed: float, dmg: float, wave: int):
        info = KINDS[kind]
        self.pid = zid
        self.kind = kind
        self.variant = variant
        self.pos = [float(pos[0]), float(pos[1]), float(pos[2])]
        self.vel = [0.0, 0.0, 0.0]
        self.yaw = 0.0
        self.pitch = 0.0
        self.health = float(hp)
        self.max_health = float(hp)
        self.alive = True
        self.team = "infected"
        self.username = info["name"]
        self.brain = None
        self.npc = True
        self.grounded = True
        self.speed = speed
        self.dmg = dmg
        self.state = "walk"
        self.state_until = 0.0
        self.next_attack = 0.0
        self.target: Optional[int] = None
        moment = now()
        self.last_seen = moment
        self.born = moment
        self.spawned_at = moment
        self.waypoints: List[List[float]] = []
        self.path_at = 0.0
        self.node = -1
        self.airborne = True
        self.vy = 0.0
        self.boxes: List[Any] = []
        self.boxes_at = [1e9, 1e9, 1e9]
        self.enraged_until = 0.0
        self.data: Dict[str, Any] = {}
        self.anim = A_WALK
        self.flags = 0
        self.hit_wall = False
        self.progress = list(self.pos)
        self.progress_at = moment
        self.climb_from: Optional[float] = None
        self.last_step = moment
        self.wave = wave
        self.score_value = int(info["score"])
        self.lured = False
        self.damage_by: Dict[int, float] = {}
        self.kills = self.score = self.streak = self.deaths = 0
        self.last_ground_pos = list(self.pos)
        self.seen_by = 0

    # -------------------------------------------------------------- shape
    @property
    def info(self) -> Dict[str, Any]:
        return KINDS[self.kind]

    @property
    def hidden(self) -> bool:
        return self.state == "burrow"

    def hitbox(self):
        w, h, d, _head = KINDS[self.kind]["box"]
        x, y, z = self.pos
        return ([x - w / 2, y, z - d / 2], [x + w / 2, y + h, z + d / 2])

    def head_box(self):
        w, h, d, head = KINDS[self.kind]["box"]
        x, y, z = self.pos
        hw = min(1.0, w * 0.3)
        return ([x - hw, y + head, z - hw], [x + hw, y + h + 0.1, z + hw])

    @property
    def aim_heights(self) -> Tuple[float, float]:
        """Where a bot aims: the chest, and the head."""
        _w, h, _d, head = KINDS[self.kind]["box"]
        return (h * 0.55, (head + h) / 2.0)

    def centre(self) -> List[float]:
        return [self.pos[0], self.pos[1] + KINDS[self.kind]["box"][1] * 0.55,
                self.pos[2]]

    def send(self, payload: Dict[str, Any]) -> None:
        """Infected have no socket: everything said to them is dropped."""

    def row(self) -> List[Any]:
        return [self.pid, KIND_INDEX[self.kind], self.variant,
                round(self.pos[0], 2), round(self.pos[1], 2), round(self.pos[2], 2),
                round(self.yaw, 2), self.anim,
                max(0, min(100, int(round(100.0 * self.health / self.max_health)))),
                self.flags]


class NpcShot:
    """Something an infected throws: acid, a plague bolt, a chunk of road."""

    __slots__ = ("ident", "kind", "pos", "vel", "gravity", "owner", "damage",
                 "splash", "born")
    _next = 1

    def __init__(self, kind: str, pos, vel, gravity: float, owner: int,
                 damage: float, splash: float):
        self.ident = NpcShot._next
        NpcShot._next += 1
        self.kind = kind
        self.pos = list(pos)
        self.vel = list(vel)
        self.gravity = gravity
        self.owner = owner
        self.damage = damage
        self.splash = splash
        self.born = now()


def ballistic(start: Sequence[float], goal: Sequence[float], speed: float,
              gravity: float) -> List[float]:
    """A launch velocity that lands near ``goal``: the low arc if ``speed``
    reaches, otherwise a 45-degree lob as far as it goes."""
    dx, dy, dz = goal[0] - start[0], goal[1] - start[1], goal[2] - start[2]
    flat = math.hypot(dx, dz) or 0.01
    v2 = speed * speed
    disc = v2 * v2 - gravity * (gravity * flat * flat + 2 * dy * v2)
    if disc >= 0 and gravity > 0:
        angle = math.atan2(v2 - math.sqrt(disc), gravity * flat)
    elif gravity > 0:
        angle = math.pi / 4
    else:
        angle = math.atan2(dy, flat)
    return [dx / flat * speed * math.cos(angle), speed * math.sin(angle),
            dz / flat * speed * math.cos(angle)]


# ================================================================== field
class HordeField:
    """Distance from every node to the nearest survivor, kept fresh.

    Sources carry a starting cost, so a survivor covered in bile (cost 0)
    out-draws one standing 120 units nearer (cost 120), and the lure (cost
    0 while it sounds, with everyone else at 150) pulls the whole area.
    """

    def __init__(self, nav):
        self.nav = nav
        self.dist: Optional[List[float]] = None
        self.sources: List[Tuple[int, float]] = []
        self.version = 0
        self._lock = threading.Lock()
        self._wanted: Optional[List[Tuple[int, float]]] = None
        self._busy = False
        self.computed_at = 0.0

    def request(self, sources: List[Tuple[int, float]]) -> None:
        if not sources:
            return
        with self._lock:
            self._wanted = sources
            if self._busy:
                return
            self._busy = True
        threading.Thread(target=self._worker, daemon=True,
                         name="horde-field").start()

    def _worker(self) -> None:
        while True:
            with self._lock:
                sources = self._wanted
                self._wanted = None
                if sources is None:
                    self._busy = False
                    return
            try:
                dist = self._dijkstra(sources)
            except Exception:
                dist = None
            if dist is not None:
                self.dist = dist
                self.sources = sources
                self.version += 1
                self.computed_at = now()
            time.sleep(0.02)

    def _dijkstra(self, sources: List[Tuple[int, float]]) -> List[float]:
        nav = self.nav
        dist = [INF] * nav.size
        heap = []
        for node, cost in sources:
            if 0 <= node < len(dist) and cost < dist[node]:
                dist[node] = cost
                heap.append((cost, node))
        heapq.heapify(heap)
        in_off, in_to, in_cost = nav.in_off, nav.in_to, nav.in_cost
        pops = 0
        while heap:
            d, v = heapq.heappop(heap)
            if d > dist[v]:
                continue
            pops += 1
            if pops % 3000 == 0:
                time.sleep(0)
            for k in range(in_off[v], in_off[v + 1]):
                u = in_to[k]
                nd = d + in_cost[k]
                if nd < dist[u]:
                    dist[u] = nd
                    heapq.heappush(heap, (nd, u))
        return dist

    def clear(self) -> None:
        with self._lock:
            self._wanted = None
        self.dist = None
        self.sources = []


# ================================================================== horde
class Horde:
    """Every infected in one instance, and everything they do.

    ``world`` is the :class:`LastLight` instance; the horde calls back into
    it to hurt survivors (``world.infected_hits``), to pin, bile and knock
    them, and to report deaths (``world.on_infected_death``).
    """

    def __init__(self, world):
        self.world = world
        self.rng = random.Random()
        self.zombies: Dict[int, Zombie] = {}
        self.shots: List[NpcShot] = []
        self.pools: List[Dict[str, Any]] = []   # acid on the ground
        self.corpses: List[Tuple[float, List[float]]] = []
        self.next_id = ZID_BASE
        self.field: Optional[HordeField] = None
        self.field_at = 0.0
        self.tick = 0
        self.frozen = False

    # --------------------------------------------------------------- basics
    @property
    def nav(self):
        nav = getattr(self.world.host, "nav", None)
        if nav is None or not nav.ready:
            return None
        if self.field is None or self.field.nav is not nav:
            self.field = HordeField(nav)
        return nav

    def alive(self) -> List[Zombie]:
        return list(self.zombies.values())

    def count(self, kinds: Optional[Sequence[str]] = None) -> int:
        if kinds is None:
            return len(self.zombies)
        return sum(1 for z in self.zombies.values() if z.kind in kinds)

    def clear(self) -> None:
        self.zombies.clear()
        self.shots.clear()
        self.pools.clear()
        self.corpses.clear()
        if self.field is not None:
            self.field.clear()

    def spawn(self, kind: str, pos: Sequence[float], hp: float, dmg: float,
              wave: int, variant: Optional[int] = None,
              rise: bool = False) -> Zombie:
        info = KINDS[kind]
        speed = info["speed"]
        if kind == "common":
            speed *= self.rng.uniform(0.92, 1.08)
        if variant is None:
            variant = self.rng.randrange(VARIANTS)
        zid = self.next_id
        self.next_id += 1
        z = Zombie(zid, kind, pos, variant, hp, speed, dmg, wave)
        z.yaw = self.rng.uniform(-math.pi, math.pi)
        if rise:
            z.state = "rise"
            z.state_until = now() + 1.4
            z.anim = A_RISE
        # nothing uses its trick the moment it appears
        moment = now()
        z.data.update({
            "leap_at": moment + self.rng.uniform(1.5, 3.0),
            "charge_at": moment + self.rng.uniform(2.5, 4.0),
            "spit_at": moment + self.rng.uniform(2.0, 4.0),
            "scream_at": moment + self.rng.uniform(3.0, 5.0),
            "raise_at": moment + self.rng.uniform(6.0, 9.0),
            "bolt_at": moment + 1.5,
            "dash_at": moment + self.rng.uniform(2.0, 3.5),
            "burrow_at": moment + self.rng.uniform(4.0, 9.0),
            "rock_at": moment + 8.0,
            "slam_at": moment + 4.0,
        })
        self.zombies[zid] = z
        return z

    # ----------------------------------------------------------------- step
    def step(self, dt: float, survivors: List[Any]) -> None:
        """One tick for the whole horde.  ``survivors`` are the field's
        living players (standing, downed or pinned)."""
        self.tick += 1
        moment = now()
        if self.frozen:
            return
        nav = self.nav
        if nav is not None and moment - self.field_at > 0.9 and survivors:
            self.field_at = moment
            self._request_field(nav, survivors, moment)
        self._step_shots(dt, survivors)
        if self.tick % 10 == 0:
            self._step_pools(survivors, moment)
        if not self.zombies:
            return
        standing = [s for s in survivors if not s.extra.get("downed")]
        for z in list(self.zombies.values()):
            if not z.alive:
                continue
            near = self._nearest(z, survivors)
            distance = near[1] if near else 1e9
            # far from everyone: a few steps a second is plenty
            stride = 1 if distance < 140 else (3 if distance < 320 else 6)
            if (self.tick + z.pid) % stride:
                continue
            step_dt = min(0.35, moment - z.last_step) if stride > 1 else dt
            z.last_step = moment
            try:
                self._think(z, near, survivors, standing, step_dt, moment, nav)
            except Exception:
                import traceback
                traceback.print_exc()
                z.waypoints = []
        if self.tick % 2 == 0:
            self._separate()

    def _request_field(self, nav, survivors, moment: float) -> None:
        sources: List[Tuple[int, float]] = []
        lure = self.world.lure_focus()
        base = 150.0 if lure is not None else 0.0
        for s in survivors:
            node = nav.nearest(s.pos, 2, standing=True)
            if node < 0:
                node = nav.nearest(s.pos, 4)
            if node < 0:
                continue
            cost = base
            if s.extra.get("biled_until", 0) > moment:
                cost = max(0.0, base - 130.0)
            sources.append((node, cost))
        if lure is not None:
            node = nav.nearest(lure, 4)
            if node >= 0:
                sources.append((node, 0.0))
        self.field.request(sources)

    @staticmethod
    def _nearest(z: Zombie, survivors) -> Optional[Tuple[Any, float]]:
        best, best_d = None, 1e9
        zx, zy, zz = z.pos
        for s in survivors:
            dx, dy, dz = s.pos[0] - zx, (s.pos[1] - zy) * 1.6, s.pos[2] - zz
            d = math.sqrt(dx * dx + dy * dy + dz * dz)
            if d < best_d:
                best, best_d = s, d
        return (best, best_d) if best is not None else None

    # ---------------------------------------------------------------- think
    def _think(self, z: Zombie, near, survivors, standing, dt: float,
               moment: float, nav) -> None:
        target = near[0] if near else None
        distance = near[1] if near else 1e9
        z.flags = 0
        if moment < z.enraged_until:
            z.flags |= F_ENRAGED
        if z.lured:
            z.flags |= F_LURED
        # a biled survivor nearby takes precedence over the nearest one
        biled = self._biled_near(z, survivors, moment)
        if biled is not None:
            target, distance = biled, math.dist(biled.pos, z.pos)
        z.target = target.pid if target is not None else None
        state = z.state
        if state == "rise":
            z.anim = A_RISE
            if moment >= z.state_until:
                z.state = "walk"
            return
        if state == "stun":
            z.anim = A_STUN
            z.flags |= F_STUNNED
            self._fall(z, dt)
            if moment >= z.state_until:
                z.state = "walk"
            return
        handler = getattr(self, "_think_" + z.kind, None)
        if handler is not None and handler(z, target, distance, survivors,
                                           standing, dt, moment, nav):
            return
        self._hunt(z, target, distance, dt, moment, nav)

    def _biled_near(self, z: Zombie, survivors, moment: float):
        best, best_d = None, 90.0
        for s in survivors:
            if s.extra.get("biled_until", 0) > moment:
                d = math.dist(s.pos, z.pos)
                if d < best_d:
                    best, best_d = s, d
        return best

    # ------------------------------------------------------------- hunting
    def _hunt(self, z: Zombie, target, distance: float, dt: float,
              moment: float, nav, speed_mult: float = 1.0,
              attack: bool = True) -> None:
        """Go for ``target``; hit it when in reach."""
        speed = z.speed * speed_mult
        if moment < z.enraged_until:
            speed *= 1.3
        if self.world.wave_overdue():
            speed *= 1.15
        if target is not None and attack:
            reach = z.info["reach"]
            dy = target.pos[1] - z.pos[1]
            flat = math.hypot(target.pos[0] - z.pos[0], target.pos[2] - z.pos[2])
            if flat < reach and -3.0 < dy < 4.6:
                self._face(z, target.pos)
                z.anim = A_ATTACK
                z.waypoints = []
                if moment >= z.next_attack:
                    z.next_attack = moment + z.info["rate"] * self.rng.uniform(0.85, 1.15)
                    self.world.infected_hits(z, target, z.dmg, z.info["name"])
                self._fall(z, dt)
                return
        self._move(z, target, distance, speed, dt, moment, nav)

    def _move(self, z: Zombie, target, distance: float, speed: float,
              dt: float, moment: float, nav) -> None:
        goal = None
        direct = False
        if target is not None and distance < 18.0:
            dy = target.pos[1] - z.pos[1]
            if abs(dy) < 2.6 or (dy > 0 and distance < 7.0):
                if nav is None or abs(dy) > 2.6 or \
                        nav.clear_line(z.pos, [target.pos[0], z.pos[1], target.pos[2]]):
                    goal = target.pos
                    direct = True
        if goal is None:
            if not z.waypoints or moment >= z.path_at:
                self._plan(z, target, nav, moment)
            if z.waypoints:
                goal = z.waypoints[0]
                if math.hypot(goal[0] - z.pos[0], goal[2] - z.pos[2]) < 1.2:
                    z.waypoints.pop(0)
                    goal = z.waypoints[0] if z.waypoints else None
            elif target is not None:
                goal = target.pos
        vx = vz = 0.0
        if goal is not None:
            dx, dz = goal[0] - z.pos[0], goal[2] - z.pos[2]
            flat = math.hypot(dx, dz)
            if flat > 0.3:
                vx, vz = dx / flat * speed, dz / flat * speed
                rise = goal[1] - z.pos[1]
                if not z.airborne and rise > body_module.STEP_HEIGHT + 0.1 and \
                        flat < 7.0 and rise <= nav_module.JUMP_UP + 0.5:
                    z.airborne = True
                    z.vy = JUMP_SPEED
                # a wall in the way of somebody above: climb it
                if z.hit_wall and rise > body_module.STEP_HEIGHT and \
                        (direct or flat < 8.0):
                    if z.climb_from is None:
                        z.climb_from = z.pos[1]
                    if z.pos[1] - z.climb_from < 26.0:
                        z.vy = 15.0
                        z.airborne = True
                        z.anim = A_CLIMB
                if z.climb_from is not None and not z.hit_wall and not z.airborne:
                    z.climb_from = None
            self._face(z, goal, rate=dt * 9.0)
        z.vel = [vx, z.vy, vz]
        self._body(z, vx, vz, dt)
        if z.anim != A_CLIMB or not z.hit_wall:
            z.anim = A_RUN if speed > 22.0 or z.kind in ("runner", "mite") else A_WALK
        self._progress(z, moment)

    def _plan(self, z: Zombie, target, nav, moment: float) -> None:
        z.path_at = moment + self.rng.uniform(0.7, 1.2)
        if nav is None:
            z.waypoints = [list(target.pos)] if target is not None else []
            return
        node = nav.nearest(z.pos, 2, standing=True)
        if node < 0:
            node = nav.nearest(z.pos, 4)
        z.node = node
        field = self.field.dist if self.field is not None else None
        nodes: List[int] = []
        if node >= 0 and field is not None and node < len(field) and field[node] < INF:
            nodes = self._follow(nav, node, field, 14)
        elif node >= 0 and target is not None:
            goal = nav.nearest(target.pos, 3)
            nodes = nav.astar(node, goal, 600) or []
        if nodes:
            z.waypoints = nav.smooth(z.pos, nodes, 10)[:4]
        elif target is not None:
            z.waypoints = [list(target.pos)]
        else:
            z.waypoints = []

    @staticmethod
    def _follow(nav, node: int, dist: List[float], steps: int) -> List[int]:
        out_off, out_to, out_cost = nav.out_off, nav.out_to, nav.out_cost
        path: List[int] = []
        current = node
        for _ in range(steps):
            best, best_cost = -1, dist[current]
            for k in range(out_off[current], out_off[current + 1]):
                v = out_to[k]
                cost = dist[v] + out_cost[k] * 0.01
                if cost < best_cost:
                    best, best_cost = v, cost
            if best < 0:
                break
            path.append(best)
            current = best
        return path

    def _progress(self, z: Zombie, moment: float) -> None:
        if moment - z.progress_at < 4.0:
            return
        moved = math.dist(z.progress, z.pos)
        z.progress = list(z.pos)
        z.progress_at = moment
        if moved < 1.2 and z.state in ("walk",):
            # stuck: hop, re-plan, and if it keeps up the world moves it
            z.data["stuck"] = z.data.get("stuck", 0) + 1
            z.waypoints = []
            z.path_at = 0.0
            if not z.airborne:
                z.airborne = True
                z.vy = JUMP_SPEED * 0.8
        else:
            z.data["stuck"] = 0

    # ---------------------------------------------------------------- body
    def _boxes(self, z: Zombie) -> List[Any]:
        pos = z.pos
        if abs(pos[0] - z.boxes_at[0]) > 4.0 or abs(pos[2] - z.boxes_at[2]) > 4.0 \
                or abs(pos[1] - z.boxes_at[1]) > 6.0:
            lo = [pos[0] - 12.0, pos[1] - 12.0, pos[2] - 12.0]
            hi = [pos[0] + 12.0, pos[1] + 18.0, pos[2] + 12.0]
            z.boxes = [b for b in self.world._colliders_near(lo, hi)
                       if b[1][0] > lo[0] and b[0][0] < hi[0] and b[1][2] > lo[2]
                       and b[0][2] < hi[2] and b[1][1] > lo[1] and b[0][1] < hi[1]]
            z.boxes_at = list(pos)
        return z.boxes

    def _body(self, z: Zombie, vx: float, vz: float, dt: float) -> None:
        z.vy -= GRAVITY * dt
        vel = [vx, z.vy, vz]
        result = body_module.move(self._boxes(z), z.pos, vel, dt)
        z.hit_wall = result.hit_wall
        if result.grounded and vel[1] <= 0:
            z.airborne = False
            z.vy = 0.0
            z.last_ground_pos = list(z.pos)
        else:
            z.airborne = True
            z.vy = vel[1]
        z.grounded = not z.airborne
        if z.pos[1] < self.world.map.get("kill_y", -80.0) + 6.0:
            # fell out of the world: back where it last stood
            z.pos = list(z.last_ground_pos)
            z.vy = 0.0

    def _fall(self, z: Zombie, dt: float) -> None:
        """Stand still, but keep gravity and the floor."""
        if z.airborne or z.vy:
            self._body(z, 0.0, 0.0, dt)
        z.vel = [0.0, z.vy, 0.0]

    @staticmethod
    def _face(z: Zombie, point: Sequence[float], rate: float = 1.0) -> None:
        want = math.atan2(point[0] - z.pos[0], point[2] - z.pos[2])
        diff = (want - z.yaw + math.pi) % (2 * math.pi) - math.pi
        z.yaw += diff * min(1.0, rate)

    def _separate(self) -> None:
        cells: Dict[Tuple[int, int], List[Zombie]] = {}
        for z in self.zombies.values():
            if z.hidden or z.state in ("pin",):
                continue
            cells.setdefault((int(z.pos[0] // 5.0), int(z.pos[2] // 5.0)), []).append(z)
        for (cx, cz), group in cells.items():
            others = []
            for dx in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    others.extend(cells.get((cx + dx, cz + dz), ()))
            for a in group:
                ra = KINDS[a.kind]["box"][0] * 0.42
                px = pz = 0.0
                for b in others:
                    if b is a:
                        continue
                    dx, dz = a.pos[0] - b.pos[0], a.pos[2] - b.pos[2]
                    if abs(a.pos[1] - b.pos[1]) > 4.0:
                        continue
                    want = ra + KINDS[b.kind]["box"][0] * 0.42
                    d2 = dx * dx + dz * dz
                    if d2 >= want * want:
                        continue
                    d = math.sqrt(d2) or 0.01
                    push = (want - d) * 0.5
                    if d2 < 1e-4:
                        dx, dz, d = self.rng.uniform(-1, 1), self.rng.uniform(-1, 1), 1.0
                    px += dx / d * push
                    pz += dz / d * push
                if px or pz:
                    px, pz = max(-0.6, min(0.6, px)), max(-0.6, min(0.6, pz))
                    nx, nz = a.pos[0] + px, a.pos[2] + pz
                    if not body_module.blocked(self._boxes(a), nx, a.pos[1], nz):
                        a.pos[0], a.pos[2] = nx, nz

    # ============================================================ specials
    def _think_bloater(self, z, target, distance, survivors, standing, dt,
                       moment, nav) -> bool:
        return False           # its trick is dying (see on_death)

    def _think_bomber(self, z, target, distance, survivors, standing, dt,
                      moment, nav) -> bool:
        fuse = z.data.get("fuse")
        if fuse is None and target is not None and distance < 8.5:
            z.data["fuse"] = moment + 1.3
            self.world.zfx("fuse", z)
            fuse = z.data["fuse"]
        if fuse is not None:
            z.flags |= F_FUSE
            if moment >= fuse:
                self.world.kill_infected(z, None, cause="fuse")
                return True
            self._hunt(z, target, distance, dt, moment, nav, speed_mult=0.75,
                       attack=False)
            return True
        return False

    def _think_leaper(self, z, target, distance, survivors, standing, dt,
                      moment, nav) -> bool:
        if z.state == "pin":
            victim = self.world.players.get(z.data.get("victim", 0))
            if victim is None or not victim.alive or \
                    victim.extra.get("pinned_by") != z.pid:
                self._release(z, moment, stun=0.8)
                return True
            z.anim = A_PIN
            z.flags |= F_PINNING
            z.pos = [victim.pos[0] - math.sin(victim.yaw) * 1.2, victim.pos[1],
                     victim.pos[2] - math.cos(victim.yaw) * 1.2]
            z.vy = 0.0
            if moment >= z.next_attack:
                z.next_attack = moment + 0.5
                self.world.infected_hits(z, victim, z.dmg * 0.75, "Leaper",
                                         quiet=True)
            return True
        if z.state == "leap":
            z.anim = A_LEAP
            self._body(z, z.vel[0], z.vel[2], dt)
            # a survivor in the way: pinned
            for s in standing:
                if s.extra.get("pinned_by") or s.extra.get("downed"):
                    continue
                if math.hypot(s.pos[0] - z.pos[0], s.pos[2] - z.pos[2]) < 3.4 and \
                        -2.0 < z.pos[1] - s.pos[1] < 5.0:
                    if self.world.pin(s, z):
                        z.state = "pin"
                        z.data["victim"] = s.pid
                        z.next_attack = moment + 0.4
                        return True
            if (not z.airborne and moment > z.state_until - 1.2) or moment >= z.state_until:
                z.state = "walk"
                z.data["leap_at"] = moment + self.rng.uniform(3.0, 5.0)
            return True
        if target is not None and 12.0 < distance < 58.0 and \
                moment >= z.data.get("leap_at", 0) and not z.airborne and \
                not target.extra.get("pinned_by") and not target.extra.get("downed") \
                and self.world.line_of_sight(
                    [z.pos[0], z.pos[1] + 3.0, z.pos[2]],
                    [target.pos[0], target.pos[1] + 3.0, target.pos[2]]):
            z.state = "leap"
            z.state_until = moment + 2.0
            aim = [target.pos[0] + target.vel[0] * 0.35, target.pos[1] + 1.0,
                   target.pos[2] + target.vel[2] * 0.35]
            vel = ballistic(z.pos, aim, 58.0, GRAVITY)
            z.vel = vel
            z.vy = vel[1]
            z.airborne = True
            self._face(z, aim)
            self.world.zfx("pounce", z)
            return True
        return False

    def _release(self, z: Zombie, moment: float, stun: float = 1.5) -> None:
        victim = self.world.players.get(z.data.pop("victim", 0))
        if victim is not None and victim.extra.get("pinned_by") == z.pid:
            self.world.unpin(victim)
        z.state = "stun"
        z.state_until = moment + stun
        z.data["leap_at"] = moment + stun + 3.0

    def _think_brute(self, z, target, distance, survivors, standing, dt,
                     moment, nav) -> bool:
        if z.state == "charge":
            z.anim = A_CHARGE
            z.flags |= F_CHARGING
            heading = z.data["heading"]
            speed = 50.0
            self._body(z, heading[0] * speed, heading[1] * speed, dt)
            hit = z.data.setdefault("hit", [])
            for s in standing:
                if s.pid in hit:
                    continue
                if math.hypot(s.pos[0] - z.pos[0], s.pos[2] - z.pos[2]) < 4.0 and \
                        abs(s.pos[1] - z.pos[1]) < 5.0:
                    hit.append(s.pid)
                    self.world.infected_hits(z, s, 24.0 * z.dmg / 14.0, "Brute",
                                             knock=[heading[0] * 70.0, 32.0,
                                                    heading[1] * 70.0])
            if z.hit_wall or moment >= z.state_until:
                z.state = "stun" if z.hit_wall else "walk"
                z.state_until = moment + (2.4 if z.hit_wall else 0.0)
                z.data["charge_at"] = moment + self.rng.uniform(7, 10)
                z.data.pop("hit", None)
                if z.hit_wall:
                    self.world.zfx("thud", z)
            return True
        if target is not None and 14.0 < distance < 70.0 and \
                moment >= z.data["charge_at"] and not z.airborne \
                and abs(target.pos[1] - z.pos[1]) < 3.0 and self.world.line_of_sight(
                    [z.pos[0], z.pos[1] + 3.0, z.pos[2]],
                    [target.pos[0], target.pos[1] + 3.0, target.pos[2]]):
            dx, dz = target.pos[0] - z.pos[0], target.pos[2] - z.pos[2]
            flat = math.hypot(dx, dz) or 1.0
            z.data["heading"] = (dx / flat, dz / flat)
            z.state = "charge"
            z.state_until = moment + 2.3
            self._face(z, target.pos)
            self.world.zfx("charge", z)
            return True
        return False

    def _think_spitter(self, z, target, distance, survivors, standing, dt,
                       moment, nav) -> bool:
        if z.state == "spit":
            z.anim = A_SPIT
            self._fall(z, dt)
            if moment >= z.state_until:
                z.state = "walk"
            return True
        if target is not None and 18.0 < distance < 75.0 and \
                moment >= z.data["spit_at"]:
            mouth = [z.pos[0], z.pos[1] + 5.4, z.pos[2]]
            aim = [target.pos[0], target.pos[1] + 1.0, target.pos[2]]
            if self.world.line_of_sight(mouth, [aim[0], aim[1] + 2.0, aim[2]]):
                vel = ballistic(mouth, aim, 62.0, GRAVITY * 0.7)
                self.shots.append(NpcShot("acid", mouth, vel, GRAVITY * 0.7, z.pid,
                                          0.0, 7.0))
                z.data["spit_at"] = moment + self.rng.uniform(8.0, 11.0)
                z.state = "spit"
                z.state_until = moment + 0.7
                self._face(z, aim)
                self.world.zfx("spit", z)
                return True
        # keeps its distance while the acid does the work
        if target is not None and distance < 16.0 and moment < z.data.get("spit_at", 0):
            return self._back_off(z, target, dt, moment)
        return False

    def _back_off(self, z: Zombie, target, dt: float, moment: float) -> bool:
        dx, dz = z.pos[0] - target.pos[0], z.pos[2] - target.pos[2]
        flat = math.hypot(dx, dz) or 1.0
        nx, nz = dx / flat, dz / flat
        ahead = [z.pos[0] + nx * 4.0, z.pos[1], z.pos[2] + nz * 4.0]
        nav = self.nav
        if nav is not None and not nav.walkable(*ahead):
            return False
        speed = z.speed * 0.8
        self._face(z, target.pos)
        self._body(z, nx * speed, nz * speed, dt)
        z.vel = [nx * speed, z.vy, nz * speed]
        z.anim = A_WALK
        return True

    def _think_screamer(self, z, target, distance, survivors, standing, dt,
                        moment, nav) -> bool:
        if z.state == "scream":
            z.anim = A_SCREAM
            self._fall(z, dt)
            if moment >= z.state_until:
                z.state = "walk"
            return True
        if target is not None and distance < 80.0 and \
                moment >= z.data["scream_at"]:
            if self.world.line_of_sight([z.pos[0], z.pos[1] + 4.5, z.pos[2]],
                                        [target.pos[0], target.pos[1] + 3.0, target.pos[2]]):
                z.state = "scream"
                z.state_until = moment + 1.8
                z.data["scream_at"] = moment + self.rng.uniform(16.0, 22.0)
                self._face(z, target.pos)
                self.world.scream(z)
                return True
        if target is not None and distance < 26.0:
            return self._back_off(z, target, dt, moment)
        return False

    def _think_captain(self, z, target, distance, survivors, standing, dt,
                       moment, nav) -> bool:
        if moment >= z.data["raise_at"]:
            z.data["raise_at"] = moment + self.rng.uniform(13.0, 17.0)
            if self.world.raise_dead(z):
                z.state = "scream"
                z.state_until = moment + 1.2
                z.anim = A_SCREAM
                return True
        if z.state == "scream":
            z.anim = A_SCREAM
            self._fall(z, dt)
            if moment >= z.state_until:
                z.state = "walk"
            return True
        if target is not None and 10.0 < distance < 90.0 and \
                moment >= z.data.get("bolt_at", 0):
            hand = [z.pos[0], z.pos[1] + 4.6, z.pos[2]]
            aim = [target.pos[0] + target.vel[0] * 0.3, target.pos[1] + 3.0,
                   target.pos[2] + target.vel[2] * 0.3]
            if self.world.line_of_sight(hand, aim):
                d = [aim[i] - hand[i] for i in range(3)]
                length = math.sqrt(sum(v * v for v in d)) or 1.0
                vel = [v / length * 70.0 for v in d]
                self.shots.append(NpcShot("bolt", hand, vel, 0.0, z.pid,
                                          z.dmg * 1.3, 0.0))
                z.data["bolt_at"] = moment + self.rng.uniform(2.3, 3.2)
                self._face(z, aim)
                self.world.zfx("bolt", z)
        if target is not None and distance < 26.0:
            return self._back_off(z, target, dt, moment)
        if target is not None and distance < 55.0:
            self._face(z, target.pos, rate=dt * 6.0)
            self._fall(z, dt)
            z.anim = A_WALK
            return True
        return False

    def _think_ronin(self, z, target, distance, survivors, standing, dt,
                     moment, nav) -> bool:
        if z.state == "dash":
            z.anim = A_CHARGE
            heading = z.data["heading"]
            self._body(z, heading[0] * 62.0, heading[1] * 62.0, dt)
            if moment >= z.state_until or z.hit_wall:
                z.state = "slash"
                z.state_until = moment + 0.35
            return True
        if z.state == "slash":
            z.anim = A_ATTACK
            self._fall(z, dt)
            if moment >= z.state_until:
                for s in standing:
                    dx, dz = s.pos[0] - z.pos[0], s.pos[2] - z.pos[2]
                    if math.hypot(dx, dz) < 7.5 and abs(s.pos[1] - z.pos[1]) < 4.0:
                        self.world.infected_hits(z, s, z.dmg * 2.4, "Ronin")
                self.world.zfx("slash", z)
                z.state = "open"
                z.state_until = moment + 1.4
            return True
        if z.state == "open":
            z.anim = A_STUN
            self._fall(z, dt)
            if moment >= z.state_until:
                z.state = "walk"
            return True
        if target is not None and 9.0 < distance < 28.0 and \
                moment >= z.data.get("dash_at", 0) and \
                abs(target.pos[1] - z.pos[1]) < 3.0 and self.world.line_of_sight(
                    [z.pos[0], z.pos[1] + 3.0, z.pos[2]],
                    [target.pos[0], target.pos[1] + 3.0, target.pos[2]]):
            dx, dz = target.pos[0] - z.pos[0], target.pos[2] - z.pos[2]
            flat = math.hypot(dx, dz) or 1.0
            z.data["heading"] = (dx / flat, dz / flat)
            z.data["dash_at"] = moment + self.rng.uniform(4.5, 6.5)
            z.state = "dash"
            z.state_until = moment + max(0.15, (flat - 4.0) / 62.0)
            self._face(z, target.pos)
            self.world.zfx("dash", z)
            return True
        z.flags |= F_GUARD
        z.anim = A_GUARD if target is not None and distance < 40 else z.anim
        return False

    def _think_burrower(self, z, target, distance, survivors, standing, dt,
                        moment, nav) -> bool:
        if z.state == "burrow":
            z.anim = A_BURROW
            z.flags |= F_HIDDEN
            if target is None or moment >= z.state_until:
                self._surface(z, None, moment)
                return True
            if math.hypot(target.pos[0] - z.pos[0], target.pos[2] - z.pos[2]) < 3.0:
                self._surface(z, target, moment)
                return True
            self._move(z, target, distance, 32.0, dt, moment, nav)
            z.anim = A_BURROW
            return True
        if target is not None and distance > 22.0 and \
                moment >= z.data.get("burrow_at", 0) and not z.airborne:
            z.state = "burrow"
            z.state_until = moment + 9.0
            self.world.zfx("burrow", z)
            return True
        return False

    def _surface(self, z: Zombie, target, moment: float) -> None:
        z.state = "rise"
        z.state_until = moment + 0.8
        z.data["burrow_at"] = moment + self.rng.uniform(9.0, 13.0)
        self.world.zfx("surface", z)
        if target is not None:
            self.world.infected_hits(z, target, z.dmg * 2.2, "Burrower",
                                     knock=[0.0, 46.0, 0.0])

    def _think_tank(self, z, target, distance, survivors, standing, dt,
                    moment, nav) -> bool:
        enraged = z.health < z.max_health * 0.35
        if enraged:
            z.flags |= F_ENRAGED
            if not z.data.get("raged"):
                z.data["raged"] = True
                self.world.zfx("roar", z)
        if z.state in ("throw", "slam"):
            z.anim = A_THROW if z.state == "throw" else A_SLAM
            self._fall(z, dt)
            if z.state == "throw" and target is not None:
                self._face(z, target.pos, rate=dt * 6)
            if moment >= z.state_until:
                if z.state == "throw" and target is not None:
                    hand = [z.pos[0], z.pos[1] + 10.0, z.pos[2]]
                    aim = [target.pos[0] + target.vel[0] * 0.6, target.pos[1] + 1.0,
                           target.pos[2] + target.vel[2] * 0.6]
                    vel = ballistic(hand, aim, 75.0, GRAVITY * 0.8)
                    self.shots.append(NpcShot("rock", hand, vel, GRAVITY * 0.8, z.pid,
                                              z.dmg * 0.9, 9.0))
                    self.world.zfx("throw", z)
                elif z.state == "slam":
                    for s in standing:
                        dx, dz = s.pos[0] - z.pos[0], s.pos[2] - z.pos[2]
                        flat = math.hypot(dx, dz)
                        if flat < 11.0 and abs(s.pos[1] - z.pos[1]) < 4.0:
                            flat = flat or 1.0
                            self.world.infected_hits(
                                z, s, z.dmg * 0.45, "Tank",
                                knock=[dx / flat * 55.0, 40.0, dz / flat * 55.0])
                    self.world.zfx("slam", z)
                z.state = "walk"
            return True
        close = [s for s in standing
                 if math.hypot(s.pos[0] - z.pos[0], s.pos[2] - z.pos[2]) < 10.0]
        if len(close) >= 2 and moment >= z.data.get("slam_at", 0):
            z.state = "slam"
            z.state_until = moment + 0.9
            z.data["slam_at"] = moment + 6.0
            return True
        if target is not None and 26.0 < distance < 150.0 and \
                moment >= z.data.get("rock_at", 0) and self.world.line_of_sight(
                    [z.pos[0], z.pos[1] + 9.0, z.pos[2]],
                    [target.pos[0], target.pos[1] + 3.0, target.pos[2]]):
            z.state = "throw"
            z.state_until = moment + 1.1
            z.data["rock_at"] = moment + self.rng.uniform(6.5, 9.0)
            return True
        # the punch: big damage, sends people flying
        if target is not None:
            flat = math.hypot(target.pos[0] - z.pos[0], target.pos[2] - z.pos[2])
            if flat < z.info["reach"] and abs(target.pos[1] - z.pos[1]) < 6.0:
                self._face(z, target.pos)
                z.anim = A_ATTACK
                if moment >= z.next_attack:
                    z.next_attack = moment + (1.1 if enraged else 1.6)
                    flat = flat or 1.0
                    dx, dz = target.pos[0] - z.pos[0], target.pos[2] - z.pos[2]
                    self.world.infected_hits(z, target, z.dmg, "Tank",
                                             knock=[dx / flat * 80.0, 42.0,
                                                    dz / flat * 80.0])
                    self.world.zfx("punch", z)
                self._fall(z, dt)
                return True
        self._move(z, target, distance, z.speed * (1.3 if enraged else 1.0), dt,
                   moment, nav)
        return True

    # ============================================================== shots
    def _step_shots(self, dt: float, survivors) -> None:
        if not self.shots:
            return
        keep: List[NpcShot] = []
        moment = now()
        for shot in self.shots:
            start = list(shot.pos)
            shot.vel[1] -= shot.gravity * dt
            shot.pos = [shot.pos[i] + shot.vel[i] * dt for i in range(3)]
            delta = [shot.pos[i] - start[i] for i in range(3)]
            travel = math.sqrt(sum(v * v for v in delta))
            landed = False
            hit = None
            if travel > 0:
                direction = [v / travel for v in delta]
                wall = self.world.ray_world(start, direction, travel)
                for s in survivors:
                    lo, hi = s.hitbox()
                    t = ray_aabb(start, direction, lo, hi)
                    if t is not None and t <= min(wall, travel):
                        hit = s
                        wall = t
                if hit is not None or wall < travel:
                    shot.pos = [start[i] + direction[i] * min(wall, travel) for i in range(3)]
                    landed = True
            if moment - shot.born > 6.0 or shot.pos[1] < self.world.map.get("kill_y", -80):
                landed = True
            if landed:
                self.world.shot_landed(shot, hit)
            else:
                keep.append(shot)
        self.shots = keep

    def add_pool(self, pos: Sequence[float], radius: float, seconds: float) -> None:
        moment = now()
        self.pools.append({"p": [round(pos[0], 2), round(pos[1], 2), round(pos[2], 2)],
                           "r": radius, "until": moment + seconds, "born": moment})
        del self.pools[:-12]

    def _step_pools(self, survivors, moment: float) -> None:
        """Acid hurts whoever stands in it, more the longer it has sat."""
        if not self.pools:
            return
        self.pools = [p for p in self.pools if p["until"] > moment]
        for pool in self.pools:
            age = moment - pool["born"]
            dps = 4.0 + min(1.0, age / 3.0) * 11.0
            px, py, pz = pool["p"]
            for s in survivors:
                if math.hypot(s.pos[0] - px, s.pos[2] - pz) < pool["r"] and \
                        -1.5 < s.pos[1] - py < 3.0:
                    self.world.acid_burn(s, dps * 0.5)
