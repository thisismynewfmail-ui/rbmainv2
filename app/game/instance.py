"""The shared game-instance engine.

Every world subclasses :class:`GameInstance`.  The base class owns everything
that is common to all of them: players, server-authoritative movement checks,
hit detection, damage, the kill feed, chat, respawning, the end-of-round
shuffle vote and the playtime/visit accounting.

Authority rules
---------------
* The client simulates its own movement (so it feels responsive) but the
  server validates every update: distance travelled per tick is capped, a
  player that never touches the ground is snapped back, and the server's copy
  of the position is what every other player and every hit test sees.
* Shots are validated against the server's copy of positions, the server's
  fire-rate timer and the server's ammo count.  A modified client can send
  whatever it likes; it cannot fire faster, reach further or hit through a
  wall.
* Scores, kills, health, currency and objective progress exist only on the
  server and are broadcast down.
"""
from __future__ import annotations

import json
import math
import random
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

from ..models import catalog

TICK_RATE = 20
TICK_DT = 1.0 / TICK_RATE
GRAVITY = 62.0
WALK_SPEED = 22.0
SPRINT_MULT = 1.0
JUMP_SPEED = 34.0
MAX_HEALTH = 100
RESPAWN_SECONDS = 4.0
PLAYER_SIZE = (3.2, 5.4, 2.0)
HEAD_MIN_Y = 4.0
HEAD_MAX_Y = 5.45
# Must match Avatar.EYE_HEIGHT in static/js/engine/avatar.js, otherwise the
# crosshair and the server's shot origin disagree.
EYE_HEIGHT = 5.05
CHAT_MAX = 160
VISIT_SECONDS = 30
# How long a connection may say nothing before the world lets it go.  The
# client pings every 2.5 seconds from a timer, and browsers keep timers
# running (slowly) in a background tab, so a player who alt-tabs still
# counts as present.  A socket that has gone away without closing -- a
# killed tab, a laptop lid, a dropped link -- does not, and it must not be
# able to hold a flag, a seat against the player cap or a place on the
# scoreboard for the rest of the round.
SILENT_SECONDS = 45.0
# Collision broad-phase bucket size.  Wide enough that a big map does not
# build a huge dictionary, tight enough that one shot only tests the handful
# of solids actually near its line.
COLLIDER_CELL = 48.0
COLLIDER_CELL_Y = 32.0

DEFAULT_WEAPON = {
    "kind": "hitscan", "damage": 20, "headshot": 2.0, "rpm": 240, "mag": 12,
    "reload": 1.5, "spread": 1.0, "pellets": 1, "range": 200, "auto": False,
    "reserve": 60,
}


def now() -> float:
    return time.monotonic()


def clamp(value: float, low: float, high: float) -> float:
    return low if value < low else (high if value > high else value)


def vec_len(v) -> float:
    return math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])


def normalise(v) -> List[float]:
    length = vec_len(v)
    if length < 1e-6:
        return [0.0, 0.0, 1.0]
    return [v[0] / length, v[1] / length, v[2] / length]


def ray_aabb(origin, direction, box_min, box_max) -> Optional[float]:
    """Slab test. Returns the distance to the near hit, or None."""
    tmin, tmax = 0.0, float("inf")
    for axis in range(3):
        o, d = origin[axis], direction[axis]
        lo, hi = box_min[axis], box_max[axis]
        if abs(d) < 1e-8:
            if o < lo or o > hi:
                return None
            continue
        inv = 1.0 / d
        t1 = (lo - o) * inv
        t2 = (hi - o) * inv
        if t1 > t2:
            t1, t2 = t2, t1
        tmin = max(tmin, t1)
        tmax = min(tmax, t2)
        if tmin > tmax:
            return None
    return tmin if tmin >= 0 else (tmax if tmax >= 0 else None)


# What the client sends, and the server broadcasts, for "hands empty".  It is
# deliberately outside the hotbar so a renderer that simply indexes the hotbar
# with it gets nothing, which is exactly what should be drawn.
STOW_SLOT = -1


class Player:
    """One connected participant."""

    __slots__ = ("pid", "user_id", "username", "avatar", "ws", "team",
                 "pos", "vel", "yaw", "pitch", "anim", "grounded", "health",
                 "alive", "respawn_at", "kills", "deaths", "score", "assists",
                 "slot", "stowed", "ammo", "reserve", "reload_until",
                 "next_fire",
                 "joined_at", "last_input", "last_pos_time", "playtime",
                 "visit_recorded", "chat_times", "airborne_since",
                 "last_ground_pos", "spawn_protect_until", "connected",
                 "vote", "extra", "last_damage_from", "last_damage_at",
                 "seq", "corrections", "ping", "streak", "last_seen_alive",
                 "last_message",
                 "coins", "plot", "session_key", "flags", "admin")

    def __init__(self, pid: int, user_id: int, username: str,
                 avatar: Dict[str, Any], ws, admin: bool = False):
        self.pid = pid
        self.user_id = user_id
        self.username = username
        self.avatar = avatar
        self.ws = ws
        self.admin = admin
        self.team = ""
        self.pos = [0.0, 5.0, 0.0]
        self.vel = [0.0, 0.0, 0.0]
        self.yaw = 0.0
        self.pitch = 0.0
        self.anim = "idle"
        self.grounded = True
        self.health = MAX_HEALTH
        self.alive = True
        self.respawn_at = 0.0
        self.kills = 0
        self.deaths = 0
        self.score = 0
        self.assists = 0
        self.slot = 0
        # Hands empty, weapon still chosen.  Keeping the slot means the ammo
        # and the reload state survive putting something away and taking it
        # back out, which is why this is a flag and not slot = -1.
        self.stowed = False
        self.ammo = [0] * catalog.HOTBAR_SIZE
        self.reserve = [0] * catalog.HOTBAR_SIZE
        self.reload_until = 0.0
        self.next_fire = 0.0
        self.joined_at = now()
        self.last_input = now()
        # Anything at all arriving from this connection, not just movement:
        # a dead player waiting on a respawn sends no input, and the client
        # pings every couple of seconds whether or not it is drawing frames.
        self.last_message = now()
        self.last_pos_time = now()
        self.playtime = 0.0
        self.visit_recorded = False
        self.chat_times: List[float] = []
        self.airborne_since = 0.0
        self.last_ground_pos = [0.0, 5.0, 0.0]
        self.spawn_protect_until = 0.0
        self.connected = True
        self.vote: Optional[bool] = None
        self.extra: Dict[str, Any] = {}
        self.last_damage_from: Optional[int] = None
        self.last_damage_at = 0.0
        self.seq = 0
        self.corrections = 0
        self.ping = 0
        self.streak = 0
        self.last_seen_alive = now()
        self.coins = 0
        self.plot: Optional[int] = None
        self.flags: Dict[str, Any] = {}

    # ------------------------------------------------------------- weapons
    def held_slot(self) -> int:
        """The slot as everyone else sees it: -1 while the hands are empty.

        The wire carries one number because the renderer only asks one
        question -- what is in this player's hands -- and an index that is
        not in the hotbar answers it without a second field to keep in step.
        """
        return -1 if self.stowed else self.slot

    def weapon(self, slot: Optional[int] = None) -> Optional[Dict[str, Any]]:
        slot = self.slot if slot is None else slot
        if not (0 <= slot < catalog.HOTBAR_SIZE):
            return None
        entry = self.avatar.get("hotbar", [])
        if slot >= len(entry) or not entry[slot]:
            return None
        return entry[slot]

    def weapon_stats(self, slot: Optional[int] = None) -> Dict[str, Any]:
        item = self.weapon(slot)
        if not item:
            return dict(DEFAULT_WEAPON)
        stats = dict(DEFAULT_WEAPON)
        stats.update((item.get("data") or {}).get("stats") or {})
        return stats

    def reset_ammo(self) -> None:
        for i in range(catalog.HOTBAR_SIZE):
            stats = self.weapon_stats(i)
            self.ammo[i] = int(stats.get("mag", 0) or 0)
            self.reserve[i] = int(stats.get("reserve", 0) or 0)

    def hitbox(self) -> Tuple[List[float], List[float]]:
        w, h, d = PLAYER_SIZE
        x, y, z = self.pos
        return ([x - w / 2, y, z - d / 2], [x + w / 2, y + h, z + d / 2])

    def head_box(self) -> Tuple[List[float], List[float]]:
        x, y, z = self.pos
        return ([x - 0.9, y + HEAD_MIN_Y, z - 0.8],
                [x + 0.9, y + HEAD_MAX_Y, z + 0.8])

    def public(self) -> Dict[str, Any]:
        """What everyone else is told about this player.

        The position is in here because the welcome payload carries it: a
        joining client used to fall back to the middle of the map and get
        yanked to its real spawn a few ticks later by a correction, which on
        a big map is a visible drop from the sky.  Remote players get their
        first position from the same field instead of waiting a frame for
        the next snapshot.
        """
        return {
            "id": self.pid, "uid": self.user_id, "name": self.username,
            "team": self.team, "avatar": self.avatar, "hp": self.health,
            "alive": self.alive, "kills": self.kills, "deaths": self.deaths,
            "score": self.score, "slot": self.held_slot(), "admin": self.admin,
            "coins": self.coins, "plot": self.plot,
            "pos": [round(v, 2) for v in self.pos], "yaw": round(self.yaw, 3),
        }

    def send(self, payload: Dict[str, Any]) -> None:
        if not self.connected or self.ws is None:
            return
        try:
            self.ws.send_json(payload)
        except Exception:
            self.connected = False


class Projectile:
    __slots__ = ("pid_owner", "team", "pos", "vel", "stats", "born", "kind",
                 "ident")
    _next_id = 1

    def __init__(self, owner: Player, pos, vel, stats, kind="rocket"):
        self.pid_owner = owner.pid
        self.team = owner.team
        self.pos = list(pos)
        self.vel = list(vel)
        self.stats = stats
        self.born = now()
        self.kind = kind
        self.ident = Projectile._next_id
        Projectile._next_id += 1


class GameInstance:
    """Base class for every world."""

    mode = "generic"
    friendly_fire = False
    shuffle_enabled = True
    respawn_seconds = RESPAWN_SECONDS

    def __init__(self, host, world_def: Dict[str, Any], instance_id: int,
                 map_data: Dict[str, Any]):
        self.host = host
        self.world = world_def
        self.world_id = world_def["id"]
        self.instance_id = instance_id
        self.map = map_data
        self.colliders = self._build_colliders(map_data)
        self.collider_grid = self._build_collider_grid(self.colliders)
        self.max_players = int(world_def.get("max_players", 16))
        self.players: Dict[int, Player] = {}
        self.projectiles: List[Projectile] = []
        self.lock = threading.RLock()
        self.tick_count = 0
        self.created_at = now()
        self.next_pid = 1
        self.round_number = 1
        self.phase = "active"          # active | ended | voting | restarting
        self.phase_until = 0.0
        self.vote_open = False
        self.vote_ends = 0.0
        self.events: List[Dict[str, Any]] = []
        self.chat_log: List[Dict[str, Any]] = []
        self.last_broadcast_state = 0.0
        self.setup()

    # ------------------------------------------------------------ lifecycle
    def setup(self) -> None:
        """Subclass hook, called once at construction."""

    def on_tick(self, dt: float) -> None:
        """Subclass hook, called every tick with the state lock held."""

    def on_player_join(self, player: Player) -> None:
        """State changes for a joining player (team assignment and so on)."""

    def on_player_ready(self, player: Player) -> None:
        """Called once the welcome payload has been sent.

        Anything a world wants to *send* a joining player belongs here, so the
        client can rely on ``welcome`` always arriving first.
        """

    def on_player_leave(self, player: Player) -> None:
        pass

    def on_kill(self, killer: Optional[Player], victim: Player,
                weapon_name: str) -> None:
        pass

    def on_action(self, player: Player, message: Dict[str, Any]) -> None:
        pass

    def round_state(self) -> Dict[str, Any]:
        return {}

    def pick_team(self, player: Player) -> str:
        teams = self.team_names()
        if not teams:
            return ""
        counts = {t: 0 for t in teams}
        for other in self.players.values():
            if other.team in counts:
                counts[other.team] += 1
        return min(teams, key=lambda t: (counts[t], t))

    def team_names(self) -> List[str]:
        return ["red", "blue"]

    # ------------------------------------------------------------- geometry
    @staticmethod
    def _build_colliders(map_data: Dict[str, Any]) -> List[Tuple[List[float], List[float]]]:
        boxes = []
        for part in map_data.get("parts", []):
            if not part.get("col"):
                continue
            size = list(part["s"])
            if "r" in part:
                rx, ry, rz = part["r"]
                if abs(rx) > 1e-3 or abs(rz) > 1e-3:
                    continue
                if abs(ry % (math.pi / 2.0)) > 1e-3:
                    continue
                if int(round(ry / (math.pi / 2.0))) % 2:
                    size = [size[2], size[1], size[0]]
            kind = part.get("t", "box")
            if kind == "sph":
                size = [s * 0.78 for s in size]
            elif kind == "cyl":
                size = [size[0] * 0.86, size[1], size[2] * 0.86]
            elif kind == "cone":
                size = [size[0] * 0.62, size[1], size[2] * 0.62]
            elif kind == "torus":
                continue
            px, py, pz = part["p"]
            boxes.append(([px - size[0] / 2, py - size[1] / 2, pz - size[2] / 2],
                          [px + size[0] / 2, py + size[1] / 2, pz + size[2] / 2]))
        return boxes

    @staticmethod
    def _build_collider_grid(
            boxes: List[Tuple[List[float], List[float]]]
    ) -> Dict[Tuple[int, int, int], List[int]]:
        """Bucket the collision boxes so a shot only tests what is near it.

        Without this every pellet is one slab test per solid on the map, and
        a shotgun fires eight of them twice a second per player.  The buckets
        are coarse and a query asks for the ray's whole bounding box, so what
        comes back is always a superset of what the ray could possibly reach:
        the answer is unchanged, only the work is.
        """
        grid: Dict[Tuple[int, int, int], List[int]] = {}
        for index, (lo, hi) in enumerate(boxes):
            for cx in range(int(math.floor(lo[0] / COLLIDER_CELL)),
                            int(math.floor(hi[0] / COLLIDER_CELL)) + 1):
                for cy in range(int(math.floor(lo[1] / COLLIDER_CELL_Y)),
                                int(math.floor(hi[1] / COLLIDER_CELL_Y)) + 1):
                    for cz in range(int(math.floor(lo[2] / COLLIDER_CELL)),
                                    int(math.floor(hi[2] / COLLIDER_CELL)) + 1):
                        grid.setdefault((cx, cy, cz), []).append(index)
        return grid

    def _colliders_near(self, lo, hi) -> List[Tuple[List[float], List[float]]]:
        """Every solid whose bucket overlaps the box ``lo``..``hi``."""
        grid = self.collider_grid
        if not grid:
            return self.colliders
        boxes = self.colliders
        seen: set = set()
        out = []
        for cx in range(int(math.floor(lo[0] / COLLIDER_CELL)),
                        int(math.floor(hi[0] / COLLIDER_CELL)) + 1):
            for cy in range(int(math.floor(lo[1] / COLLIDER_CELL_Y)),
                            int(math.floor(hi[1] / COLLIDER_CELL_Y)) + 1):
                for cz in range(int(math.floor(lo[2] / COLLIDER_CELL)),
                                int(math.floor(hi[2] / COLLIDER_CELL)) + 1):
                    for index in grid.get((cx, cy, cz), ()):
                        if index in seen:
                            continue
                        seen.add(index)
                        out.append(boxes[index])
        return out

    def ray_world(self, origin, direction, max_dist: float) -> float:
        """Distance to the first solid surface along a ray (or max_dist)."""
        best = max_dist
        end = [origin[i] + direction[i] * max_dist for i in range(3)]
        lo = [min(origin[i], end[i]) for i in range(3)]
        hi = [max(origin[i], end[i]) for i in range(3)]
        for box_lo, box_hi in self._colliders_near(lo, hi):
            if (origin[0] < box_lo[0] and direction[0] <= 0) or \
               (origin[0] > box_hi[0] and direction[0] >= 0):
                continue
            hit = ray_aabb(origin, direction, box_lo, box_hi)
            if hit is not None and 0.0 <= hit < best:
                best = hit
        return best

    def line_of_sight(self, a, b) -> bool:
        delta = [b[0] - a[0], b[1] - a[1], b[2] - a[2]]
        dist = vec_len(delta)
        if dist < 0.01:
            return True
        direction = [delta[0] / dist, delta[1] / dist, delta[2] / dist]
        return self.ray_world(a, direction, dist) >= dist - 0.35

    # ------------------------------------------------------------- spawning
    def spawn_points(self, team: str) -> List[Dict[str, Any]]:
        spawns = self.map.get("spawns", {})
        if team in spawns and spawns[team]:
            return spawns[team]
        merged: List[Dict[str, Any]] = []
        for value in spawns.values():
            merged.extend(value)
        return merged or [{"p": [0, 6, 0], "yaw": 0}]

    def spawn_player(self, player: Player) -> None:
        points = self.spawn_points(player.team)
        best = None
        best_score = -1.0
        random.shuffle(points)
        for point in points[:8]:
            score = 1000.0
            for other in self.players.values():
                if other is player or not other.alive:
                    continue
                d = math.dist(other.pos, point["p"])
                if other.team != player.team:
                    score = min(score, d)
                else:
                    score = min(score, d * 3.0)
            if score > best_score:
                best_score = score
                best = point
        point = best or points[0]
        player.pos = [float(point["p"][0]), float(point["p"][1]),
                      float(point["p"][2])]
        player.last_ground_pos = list(player.pos)
        player.vel = [0.0, 0.0, 0.0]
        player.yaw = float(point.get("yaw", 0.0))
        player.pitch = 0.0
        player.health = MAX_HEALTH
        player.alive = True
        player.grounded = True
        player.airborne_since = 0.0
        player.spawn_protect_until = now() + 2.0
        player.reset_ammo()
        player.reload_until = 0.0
        # Putting something away belongs to the life you did it in: coming
        # back with empty hands and no way to tell why would read as a bug.
        was_stowed = player.stowed
        player.stowed = False
        player.send({"t": "spawn", "p": player.pos, "yaw": player.yaw,
                     "hp": player.health, "prot": 2.0, "stowed": False})
        if was_stowed:
            self.broadcast({"t": "slot", "id": player.pid, "i": player.slot},
                           exclude=player.pid)
        self.broadcast({"t": "respawned", "id": player.pid, "p": player.pos,
                        "hp": player.health}, exclude=player.pid)

    # -------------------------------------------------------------- players
    def add_player(self, user_id: int, username: str, avatar: Dict[str, Any],
                   ws, admin: bool = False) -> Player:
        with self.lock:
            pid = self.next_pid
            self.next_pid += 1
            player = Player(pid, user_id, username, avatar, ws, admin)
            player.team = self.pick_team(player)
            self.players[pid] = player
            self.spawn_player(player)
            self.on_player_join(player)
            payload = {
                "t": "welcome",
                "you": player.public(),
                "world": {
                    "id": self.world_id, "name": self.world["name"],
                    "mode": self.world.get("mode"),
                    "max_players": self.max_players,
                    "instance": self.instance_id,
                    "round_label": self.world.get("round_label", ""),
                    "team_count": self.world.get("team_count", 2),
                    "shuffle": self.world.get("shuffle", True),
                },
                "map": self.map,
                "players": [p.public() for p in self.players.values()],
                "state": self.full_state(),
                "tick_rate": TICK_RATE,
                "constants": {
                    "gravity": GRAVITY, "walk": WALK_SPEED, "jump": JUMP_SPEED,
                    "size": list(PLAYER_SIZE), "respawn": self.respawn_seconds,
                },
                "chat": self.chat_log[-25:],
            }
            player.send(payload)
            self.broadcast({"t": "join", "player": player.public()},
                           exclude=pid)
            self.on_player_ready(player)
            self.system_message("%s joined the server." % username)
            return player

    def drop_user(self, user_id: int, reason: str = "",
                  keep_pid: int = 0) -> int:
        """Disconnect every connection belonging to one account.

        Used to enforce one live session per player: opening a world in a
        second window pulls the first one out of whatever it was in before the
        new connection is allowed to join.  The socket is closed rather than
        just forgotten, so the reader thread unwinds and ``remove_player``
        runs through the normal path (stats flushed, everybody told).
        """
        with self.lock:
            doomed = [p for p in self.players.values()
                      if p.user_id == user_id and p.pid != keep_pid]
        for player in doomed:
            try:
                player.send({"t": "kicked", "reason": reason or
                             "You opened this game in another window."})
            except Exception:
                pass
            player.connected = False
            try:
                if player.ws is not None:
                    player.ws.close()
            except Exception:
                pass
            self.remove_player(player.pid)
        return len(doomed)

    def remove_player(self, pid: int) -> None:
        with self.lock:
            player = self.players.pop(pid, None)
            if player is None:
                return
            player.connected = False
            self.on_player_leave(player)
            self.flush_player_stats(player, final=True)
            self.broadcast({"t": "leave", "id": pid})
            self.system_message("%s left the server." % player.username)

    def flush_player_stats(self, player: Player, final: bool = False) -> None:
        elapsed = now() - player.joined_at
        player.playtime = elapsed
        self.host.report_player(self, player, final=final)

    # ---------------------------------------------------------- broadcasting
    def broadcast(self, payload: Dict[str, Any], exclude: Optional[int] = None,
                  team: Optional[str] = None) -> None:
        for pid, player in list(self.players.items()):
            if exclude is not None and pid == exclude:
                continue
            if team is not None and player.team != team:
                continue
            player.send(payload)

    def system_message(self, text: str, kind: str = "system") -> None:
        entry = {"t": "chat", "kind": kind, "m": text, "from": "", "id": 0,
                 "at": time.time()}
        self.chat_log.append(entry)
        del self.chat_log[:-120]
        self.broadcast(entry)

    def push_event(self, kind: str, **data: Any) -> None:
        payload = {"t": "evt", "k": kind}
        payload.update(data)
        self.broadcast(payload)

    # ------------------------------------------------------------- messages
    def handle(self, player: Player, message: Dict[str, Any]) -> None:
        kind = message.get("t")
        player.last_message = now()
        if kind == "in":
            self.handle_input(player, message)
        elif kind == "fire":
            self.handle_fire(player, message)
        elif kind == "reload":
            self.handle_reload(player)
        elif kind == "slot":
            self.handle_slot(player, message)
        elif kind == "chat":
            self.handle_chat(player, message)
        elif kind == "vote":
            self.handle_vote(player, message)
        elif kind == "respawn":
            with self.lock:
                if not player.alive and now() >= player.respawn_at:
                    self.spawn_player(player)
        elif kind == "act":
            with self.lock:
                self.on_action(player, message)
        elif kind == "ping":
            player.send({"t": "pong", "c": message.get("c"),
                         "st": round(time.time() * 1000)})

    # -------------------------------------------------------------- movement
    def handle_input(self, player: Player, message: Dict[str, Any]) -> None:
        with self.lock:
            if not player.alive:
                return
            pos = message.get("p")
            if not (isinstance(pos, list) and len(pos) == 3):
                return
            try:
                pos = [float(pos[0]), float(pos[1]), float(pos[2])]
            except (TypeError, ValueError):
                return
            if any(math.isnan(v) or math.isinf(v) or abs(v) > 5000 for v in pos):
                self.correct(player)
                return
            moment = now()
            dt = max(0.016, min(0.5, moment - player.last_pos_time))
            player.last_pos_time = moment
            player.last_input = moment

            # Horizontal speed cap (with headroom for knockback and lag).
            dx = pos[0] - player.pos[0]
            dz = pos[2] - player.pos[2]
            travelled = math.hypot(dx, dz)
            allowance = self.max_speed(player) * dt * 1.9 + 2.0
            if travelled > allowance:
                player.corrections += 1
                if player.corrections > 2:
                    self.correct(player)
                    return
                scale = allowance / travelled
                pos[0] = player.pos[0] + dx * scale
                pos[2] = player.pos[2] + dz * scale
            else:
                player.corrections = max(0, player.corrections - 1)

            # Vertical: rising faster than a jump, or hovering, is rejected.
            dy = pos[1] - player.pos[1]
            if dy > JUMP_SPEED * dt * 1.9 + 1.5:
                self.correct(player)
                return
            grounded = bool(message.get("g"))
            if grounded:
                player.airborne_since = 0.0
                player.last_ground_pos = list(pos)
            else:
                if player.airborne_since == 0.0:
                    player.airborne_since = moment
                elif moment - player.airborne_since > 9.0:
                    player.pos = list(player.last_ground_pos)
                    player.airborne_since = 0.0
                    self.correct(player)
                    return
            if pos[1] < self.map.get("kill_y", -60.0):
                player.pos = pos
                self.kill(player, None, "the void")
                return

            player.pos = pos
            player.grounded = grounded
            vel = message.get("v")
            if isinstance(vel, list) and len(vel) == 3:
                try:
                    player.vel = [float(vel[0]), float(vel[1]), float(vel[2])]
                except (TypeError, ValueError):
                    player.vel = [0.0, 0.0, 0.0]
            try:
                player.yaw = float(message.get("y", player.yaw))
                player.pitch = clamp(float(message.get("pi", player.pitch)),
                                     -1.55, 1.55)
            except (TypeError, ValueError):
                pass
            anim = message.get("a")
            if isinstance(anim, str) and len(anim) < 12:
                player.anim = anim
            seq = message.get("seq")
            if isinstance(seq, int):
                player.seq = seq

    def max_speed(self, player: Player) -> float:
        return WALK_SPEED * SPRINT_MULT

    def correct(self, player: Player) -> None:
        player.send({"t": "correct", "p": player.pos, "seq": player.seq})

    # -------------------------------------------------------------- shooting
    def handle_slot(self, player: Player, message: Dict[str, Any]) -> None:
        """Draw a hotbar item, or -- with i = -1 -- put the held one away.

        The client sends -1 when the key for the slot already in hand is
        pressed again.  It is checked here rather than trusted, because
        whether a player is holding a weapon decides whether they may fire.
        """
        try:
            slot = int(message.get("i", 0))
        except (TypeError, ValueError):
            return
        with self.lock:
            if slot == STOW_SLOT:
                if player.stowed:
                    return
                player.stowed = True
                player.reload_until = 0.0
                # Same short delay as drawing something: stowing must not be
                # a way to skip the pause between weapons.
                player.next_fire = max(player.next_fire, now() + 0.25)
                self.broadcast({"t": "slot", "id": player.pid, "i": STOW_SLOT},
                               exclude=player.pid)
                player.send({"t": "you", "slot": player.slot, "stowed": True,
                             "ammo": player.ammo[player.slot],
                             "reserve": player.reserve[player.slot]})
                return
            if not (0 <= slot < catalog.HOTBAR_SIZE):
                return
            if player.weapon(slot) is None:
                return
            player.slot = slot
            player.stowed = False
            player.reload_until = 0.0
            player.next_fire = max(player.next_fire, now() + 0.25)
            self.broadcast({"t": "slot", "id": player.pid, "i": slot},
                           exclude=player.pid)
            player.send({"t": "you", "slot": slot, "stowed": False,
                         "ammo": player.ammo[slot],
                         "reserve": player.reserve[slot]})

    def handle_reload(self, player: Player) -> None:
        with self.lock:
            if player.stowed:
                return
            stats = player.weapon_stats()
            if stats.get("kind") == "melee":
                return
            slot = player.slot
            mag = int(stats.get("mag", 0) or 0)
            if mag <= 0 or player.ammo[slot] >= mag or player.reserve[slot] <= 0:
                return
            if player.reload_until > now():
                return
            player.reload_until = now() + float(stats.get("reload", 1.5))
            player.send({"t": "reloading", "time": float(stats.get("reload", 1.5))})
            self.broadcast({"t": "anim", "id": player.pid, "a": "reload"},
                           exclude=player.pid)

    def finish_reload(self, player: Player) -> None:
        stats = player.weapon_stats()
        slot = player.slot
        mag = int(stats.get("mag", 0) or 0)
        need = mag - player.ammo[slot]
        take = min(need, player.reserve[slot])
        player.ammo[slot] += take
        player.reserve[slot] -= take
        player.reload_until = 0.0
        player.send({"t": "you", "ammo": player.ammo[slot],
                     "reserve": player.reserve[slot], "slot": slot})

    def handle_fire(self, player: Player, message: Dict[str, Any]) -> None:
        with self.lock:
            if not player.alive or self.phase not in ("active", "setup"):
                return
            # Nothing in your hands, nothing to fire.  The client stops this
            # too; this is the half that a modified client cannot skip.
            if player.stowed:
                return
            moment = now()
            if moment < player.next_fire or moment < player.reload_until:
                return
            stats = player.weapon_stats()
            slot = player.slot
            kind = stats.get("kind", "hitscan")
            rpm = float(stats.get("rpm", 240) or 240)
            player.next_fire = moment + max(0.03, 60.0 / max(1.0, rpm))

            direction = message.get("d")
            if not (isinstance(direction, list) and len(direction) == 3):
                return
            try:
                direction = normalise([float(direction[0]), float(direction[1]),
                                       float(direction[2])])
            except (TypeError, ValueError):
                return

            origin = [player.pos[0], player.pos[1] + EYE_HEIGHT, player.pos[2]]
            if kind == "melee":
                self.do_melee(player, direction, stats)
                self.broadcast({"t": "fx", "k": "swing", "id": player.pid},
                               exclude=player.pid)
                return
            if kind == "support":
                if player.ammo[slot] <= 0:
                    self.handle_reload(player)
                    return
                player.ammo[slot] -= 1
                self.do_support(player, direction, stats, origin)
                player.send({"t": "you", "ammo": player.ammo[slot],
                             "reserve": player.reserve[slot], "slot": slot})
                return

            if player.ammo[slot] <= 0:
                self.handle_reload(player)
                return
            player.ammo[slot] -= 1
            player.spawn_protect_until = 0.0
            player.send({"t": "you", "ammo": player.ammo[slot],
                         "reserve": player.reserve[slot], "slot": slot})

            if kind == "projectile":
                speed = float(stats.get("speed", 70))
                proj = Projectile(player,
                                  [origin[0] + direction[0] * 2.0,
                                   origin[1] + direction[1] * 2.0,
                                   origin[2] + direction[2] * 2.0],
                                  [direction[0] * speed, direction[1] * speed,
                                   direction[2] * speed], stats)
                self.projectiles.append(proj)
                self.broadcast({"t": "proj", "id": proj.ident,
                                "p": proj.pos, "v": proj.vel,
                                "o": player.pid})
                return

            self.do_hitscan(player, origin, direction, stats)
            self.broadcast({"t": "fx", "k": "shot", "id": player.pid,
                            "o": origin, "d": direction,
                            "w": (player.weapon() or {}).get("item_id", "")},
                           exclude=player.pid)

    def do_hitscan(self, player: Player, origin, direction,
                   stats: Dict[str, Any]) -> None:
        pellets = int(stats.get("pellets", 1) or 1)
        spread = float(stats.get("spread", 1.0)) * math.pi / 180.0
        max_range = float(stats.get("range", 200))
        weapon_name = (player.weapon() or {}).get("name", "Unknown")
        hits = 0
        rng = random.Random()
        for _ in range(pellets):
            aim = direction
            if spread > 0:
                yaw_off = rng.gauss(0, spread * 0.5)
                pitch_off = rng.gauss(0, spread * 0.5)
                aim = self._offset_direction(direction, yaw_off, pitch_off)
            wall = self.ray_world(origin, aim, max_range)
            victim, distance, headshot = self.nearest_player_hit(
                player, origin, aim, min(wall, max_range))
            if victim is None:
                continue
            damage = float(stats.get("damage", 20))
            if headshot:
                damage *= float(stats.get("headshot", 1.0))
            falloff = float(stats.get("falloff", 0.0))
            if falloff > 0:
                ratio = clamp(distance / max_range, 0.0, 1.0)
                damage *= (1.0 - falloff * ratio)
            hits += 1
            self.apply_damage(victim, player, damage, weapon_name, headshot)
        if hits:
            player.send({"t": "hit", "n": hits})

    @staticmethod
    def _offset_direction(direction, yaw_off, pitch_off):
        yaw = math.atan2(direction[0], direction[2]) + yaw_off
        pitch = math.asin(clamp(direction[1], -1.0, 1.0)) + pitch_off
        cos_p = math.cos(pitch)
        return [math.sin(yaw) * cos_p, math.sin(pitch), math.cos(yaw) * cos_p]

    def nearest_player_hit(self, shooter: Player, origin, direction,
                           max_dist: float):
        best_victim = None
        best_dist = max_dist
        best_head = False
        for other in self.players.values():
            if other is shooter or not other.alive:
                continue
            if other.team == shooter.team and not self.friendly_fire:
                continue
            if now() < other.spawn_protect_until:
                continue
            lo, hi = other.hitbox()
            distance = ray_aabb(origin, direction, lo, hi)
            if distance is None or distance >= best_dist:
                continue
            hlo, hhi = other.head_box()
            head_hit = ray_aabb(origin, direction, hlo, hhi)
            best_victim = other
            best_dist = distance
            best_head = head_hit is not None
        return best_victim, best_dist, best_head

    def do_melee(self, player: Player, direction, stats: Dict[str, Any]) -> None:
        reach = float(stats.get("range", 9.0))
        arc = float(stats.get("arc", 0.55))
        origin = [player.pos[0], player.pos[1] + 3.4, player.pos[2]]
        weapon_name = (player.weapon() or {}).get("name", "Fists")
        hit_any = 0
        for other in list(self.players.values()):
            if other is player or not other.alive:
                continue
            if other.team == player.team and not self.friendly_fire:
                continue
            if now() < other.spawn_protect_until:
                continue
            target = [other.pos[0], other.pos[1] + 2.6, other.pos[2]]
            delta = [target[0] - origin[0], target[1] - origin[1],
                     target[2] - origin[2]]
            distance = vec_len(delta)
            if distance > reach:
                continue
            unit = normalise(delta)
            if (unit[0] * direction[0] + unit[1] * direction[1]
                    + unit[2] * direction[2]) < (1.0 - arc):
                continue
            if not self.line_of_sight(origin, target):
                continue
            hit_any += 1
            self.apply_damage(other, player, float(stats.get("damage", 30)),
                              weapon_name, False)
            knock = float(stats.get("knockback", 0))
            if knock:
                other.send({"t": "knock", "v": [unit[0] * knock, knock * 0.35,
                                                unit[2] * knock]})
        if hit_any:
            player.send({"t": "hit", "n": hit_any})

    def do_support(self, player: Player, direction, stats: Dict[str, Any],
                   origin) -> None:
        reach = float(stats.get("range", 14.0))
        healed = 0
        best = None
        best_dot = 0.55
        for other in self.players.values():
            if not other.alive or other.team != player.team or other is player:
                continue
            target = [other.pos[0], other.pos[1] + 3.0, other.pos[2]]
            delta = [target[0] - origin[0], target[1] - origin[1],
                     target[2] - origin[2]]
            if vec_len(delta) > reach:
                continue
            unit = normalise(delta)
            dot = (unit[0] * direction[0] + unit[1] * direction[1]
                   + unit[2] * direction[2])
            if dot > best_dot:
                best_dot = dot
                best = other
        amount = float(stats.get("heal", 30))
        if best is not None:
            healed = self.heal(best, amount, player)
            player.send({"t": "hit", "n": 1, "heal": healed})
            player.score += 1
        else:
            self.heal(player, float(stats.get("self_heal", amount * 0.6)), player)

    def heal(self, target: Player, amount: float,
             source: Optional[Player] = None) -> int:
        before = target.health
        target.health = int(clamp(target.health + amount, 0, MAX_HEALTH))
        gained = target.health - before
        if gained:
            target.send({"t": "heal", "hp": target.health, "amt": gained,
                         "by": source.username if source else ""})
        return gained

    # ---------------------------------------------------------------- damage
    def apply_damage(self, victim: Player, attacker: Optional[Player],
                     amount: float, weapon_name: str,
                     headshot: bool = False) -> None:
        if not victim.alive or amount <= 0:
            return
        if now() < victim.spawn_protect_until:
            return
        amount = float(amount)
        victim.health -= amount
        victim.last_damage_from = attacker.pid if attacker else None
        victim.last_damage_at = now()
        victim.send({"t": "dmg", "hp": max(0, int(victim.health)),
                     "a": round(amount, 1),
                     "from": attacker.pos if attacker else victim.pos,
                     "by": attacker.username if attacker else "",
                     "hs": headshot})
        if attacker is not None:
            attacker.send({"t": "dealt", "a": round(amount, 1),
                           "hs": headshot, "target": victim.pid,
                           "hp": max(0, int(victim.health))})
        if victim.health <= 0:
            self.kill(victim, attacker, weapon_name, headshot)

    def kill(self, victim: Player, killer: Optional[Player],
             weapon_name: str, headshot: bool = False) -> None:
        if not victim.alive:
            return
        victim.alive = False
        victim.health = 0
        victim.deaths += 1
        victim.streak = 0
        victim.respawn_at = now() + self.respawn_seconds
        if killer is not None and killer is not victim:
            killer.kills += 1
            killer.score += 10
            killer.streak += 1
        elif killer is victim:
            victim.score = max(0, victim.score - 5)
        self.broadcast({
            "t": "kill",
            "k": killer.username if killer else "",
            "kid": killer.pid if killer else 0,
            "kteam": killer.team if killer else "",
            "v": victim.username, "vid": victim.pid, "vteam": victim.team,
            "w": weapon_name, "hs": headshot,
            "streak": killer.streak if killer else 0,
        })
        victim.send({"t": "died", "in": self.respawn_seconds,
                     "by": killer.username if killer else weapon_name})
        self.on_kill(killer, victim, weapon_name)

    # ------------------------------------------------------------------ chat
    def handle_chat(self, player: Player, message: Dict[str, Any]) -> None:
        text = message.get("m")
        if not isinstance(text, str):
            return
        text = " ".join(text.split())[:CHAT_MAX]
        if not text:
            return
        moment = now()
        player.chat_times = [t for t in player.chat_times if moment - t < 10.0]
        if len(player.chat_times) >= 6:
            player.send({"t": "chat", "kind": "system", "from": "",
                         "m": "You are talking too fast.", "at": time.time()})
            return
        player.chat_times.append(moment)
        team_only = bool(message.get("team"))
        entry = {"t": "chat", "from": player.username, "id": player.pid,
                 "uid": player.user_id, "team": player.team, "m": text,
                 "kind": "team" if team_only else "all", "at": time.time(),
                 "admin": player.admin}
        if team_only:
            self.broadcast(entry, team=player.team)
        else:
            self.chat_log.append(entry)
            del self.chat_log[:-120]
            self.broadcast(entry)

    # ------------------------------------------------------------- vote/round
    def handle_vote(self, player: Player, message: Dict[str, Any]) -> None:
        with self.lock:
            if not self.vote_open:
                return
            player.vote = bool(message.get("v"))
            self.broadcast_vote()

    def broadcast_vote(self) -> None:
        yes = sum(1 for p in self.players.values() if p.vote is True)
        no = sum(1 for p in self.players.values() if p.vote is False)
        total = max(1, len(self.players))
        self.broadcast({"t": "vote", "open": self.vote_open, "yes": yes,
                        "no": no, "total": total,
                        "needed": math.ceil(total * 0.8),
                        "ends_in": max(0.0, round(self.vote_ends - now(), 1))})

    def start_vote(self) -> None:
        from .. import config
        if not (self.shuffle_enabled and self.world.get("shuffle", True)):
            self.phase = "restarting"
            self.phase_until = now() + 6.0
            return
        self.vote_open = True
        self.vote_ends = now() + config.SHUFFLE_VOTE_SECONDS
        self.phase = "voting"
        self.phase_until = self.vote_ends
        for player in self.players.values():
            player.vote = None
        self.system_message(
            "Round over -- vote to shuffle the teams! (%ds)"
            % config.SHUFFLE_VOTE_SECONDS)
        self.broadcast_vote()

    def resolve_vote(self) -> None:
        from .. import config
        yes = sum(1 for p in self.players.values() if p.vote is True)
        total = max(1, len(self.players))
        ratio = yes / float(total)
        self.vote_open = False
        if ratio >= config.SHUFFLE_VOTE_RATIO:
            self.shuffle_teams()
            self.system_message(
                "Teams shuffled! (%d/%d voted yes)" % (yes, total))
        else:
            self.system_message(
                "Not enough votes to shuffle (%d/%d) -- teams stay as they are."
                % (yes, total))
        self.broadcast({"t": "vote", "open": False, "yes": yes,
                        "no": total - yes, "total": total,
                        "result": ratio >= config.SHUFFLE_VOTE_RATIO})
        self.phase = "restarting"
        self.phase_until = now() + 4.0

    def shuffle_teams(self) -> None:
        teams = self.team_names()
        if not teams:
            return
        players = list(self.players.values())
        random.shuffle(players)
        for index, player in enumerate(players):
            player.team = teams[index % len(teams)]
            player.send({"t": "team", "team": player.team})
        self.broadcast({"t": "teams",
                        "map": {p.pid: p.team for p in self.players.values()}})

    def end_round(self, winner: str, reason: str = "") -> None:
        self.phase = "ended"
        self.phase_until = now() + 8.0
        self.broadcast({"t": "round_end", "winner": winner, "reason": reason,
                        "scores": self.scoreboard()})
        for player in self.players.values():
            if player.team == winner:
                player.score += 50
            self.host.report_round(self, player, won=player.team == winner)

    def scoreboard(self) -> List[Dict[str, Any]]:
        rows = [{"id": p.pid, "name": p.username, "uid": p.user_id,
                 "team": p.team, "kills": p.kills, "deaths": p.deaths,
                 "score": p.score, "ping": p.ping, "coins": p.coins}
                for p in self.players.values()]
        rows.sort(key=lambda r: (-r["score"], -r["kills"], r["name"].lower()))
        return rows

    def restart_round(self) -> None:
        self.round_number += 1
        self.phase = "active"
        self.projectiles.clear()
        for player in self.players.values():
            player.vote = None
            player.kills = 0
            player.deaths = 0
            self.spawn_player(player)
        self.broadcast({"t": "round_start", "round": self.round_number,
                        "state": self.full_state()})
        self.system_message("Round %d -- go!" % self.round_number)

    # ------------------------------------------------------------------ tick
    def full_state(self) -> Dict[str, Any]:
        state = {
            "phase": self.phase,
            "round": self.round_number,
            "players": len(self.players),
            "max_players": self.max_players,
            "instance": self.instance_id,
            "scoreboard": self.scoreboard(),
            "vote_open": self.vote_open,
            "vote_ends_in": max(0.0, round(self.vote_ends - now(), 1))
            if self.vote_open else 0.0,
        }
        state.update(self.round_state())
        return state

    def snapshot(self) -> Dict[str, Any]:
        rows = []
        for player in self.players.values():
            rows.append([
                player.pid,
                round(player.pos[0], 2), round(player.pos[1], 2),
                round(player.pos[2], 2),
                round(player.yaw, 3), round(player.pitch, 3),
                player.anim, int(player.health), player.held_slot(),
                1 if player.alive else 0,
            ])
        payload: Dict[str, Any] = {"t": "snap", "k": self.tick_count, "ps": rows}
        if self.projectiles:
            payload["pr"] = [[p.ident, round(p.pos[0], 2), round(p.pos[1], 2),
                              round(p.pos[2], 2)] for p in self.projectiles]
        return payload

    def step_projectiles(self, dt: float) -> None:
        if not self.projectiles:
            return
        alive: List[Projectile] = []
        for proj in self.projectiles:
            proj.vel[1] -= GRAVITY * 0.35 * dt
            start = list(proj.pos)
            proj.pos[0] += proj.vel[0] * dt
            proj.pos[1] += proj.vel[1] * dt
            proj.pos[2] += proj.vel[2] * dt
            delta = [proj.pos[0] - start[0], proj.pos[1] - start[1],
                     proj.pos[2] - start[2]]
            travel = vec_len(delta)
            direction = normalise(delta)
            exploded = False
            if travel > 0:
                wall = self.ray_world(start, direction, travel)
                victim, distance, _ = self.nearest_player_hit(
                    self._owner(proj), start, direction, min(wall, travel))
                if victim is not None:
                    proj.pos = [start[0] + direction[0] * distance,
                                start[1] + direction[1] * distance,
                                start[2] + direction[2] * distance]
                    exploded = True
                elif wall < travel:
                    proj.pos = [start[0] + direction[0] * wall,
                                start[1] + direction[1] * wall,
                                start[2] + direction[2] * wall]
                    exploded = True
            if proj.pos[1] < self.map.get("kill_y", -60) or \
                    now() - proj.born > 8.0:
                exploded = True
            if exploded:
                self.explode(proj)
            else:
                alive.append(proj)
        self.projectiles = alive

    def _owner(self, proj: Projectile) -> Player:
        owner = self.players.get(proj.pid_owner)
        if owner is not None:
            return owner
        ghost = Player(-1, 0, "", {}, None)
        ghost.team = proj.team
        return ghost

    def explode(self, proj: Projectile) -> None:
        stats = proj.stats
        radius = float(stats.get("splash", 8.0))
        splash = float(stats.get("splash_damage", stats.get("damage", 50)))
        owner = self.players.get(proj.pid_owner)
        weapon_name = "Blast Launcher"
        self.broadcast({"t": "fx", "k": "explode", "p": proj.pos,
                        "r": radius, "id": proj.ident})
        for player in list(self.players.values()):
            if not player.alive:
                continue
            centre = [player.pos[0], player.pos[1] + 2.6, player.pos[2]]
            distance = math.dist(centre, proj.pos)
            if distance > radius:
                continue
            falloff = 1.0 - (distance / radius) ** 1.4
            same_team = owner is not None and player.team == owner.team
            if player is owner:
                damage = splash * falloff * float(stats.get("self_damage", 0.4))
            elif same_team and not self.friendly_fire:
                damage = 0.0
            else:
                damage = splash * falloff
            knock = float(stats.get("knockback", 20)) * falloff
            if player is owner:
                # the owner gets a stronger shove than a bystander, which is
                # what makes a floor-aimed rocket a usable jump
                knock *= float(stats.get("self_knockback", 1.0))
            if knock > 0:
                push = normalise([centre[0] - proj.pos[0],
                                  max(0.4, centre[1] - proj.pos[1]),
                                  centre[2] - proj.pos[2]])
                player.send({"t": "knock",
                             "v": [push[0] * knock, abs(push[1]) * knock * 1.15,
                                   push[2] * knock]})
            if damage > 0.5:
                self.apply_damage(player, owner, damage, weapon_name, False)

    def tick(self) -> None:
        with self.lock:
            self.tick_count += 1
            moment = now()
            for player in list(self.players.values()):
                if not player.connected:
                    continue
                if not player.alive and moment >= player.respawn_at:
                    if self.phase in ("active", "setup"):
                        self.spawn_player(player)
                if player.reload_until and moment >= player.reload_until:
                    self.finish_reload(player)
                if not player.visit_recorded and \
                        (moment - player.joined_at) >= VISIT_SECONDS:
                    player.visit_recorded = True
                    self.host.report_visit(self, player)
            self.drop_silent(moment)
            self.step_projectiles(TICK_DT)
            self.on_tick(TICK_DT)
            if self.phase == "ended" and moment >= self.phase_until:
                self.start_vote()
            elif self.phase == "voting" and moment >= self.vote_ends:
                self.resolve_vote()
            elif self.phase == "restarting" and moment >= self.phase_until:
                self.restart_round()
            self.broadcast(self.snapshot())
            if moment - self.last_broadcast_state > 1.0:
                self.last_broadcast_state = moment
                self.broadcast({"t": "state", "s": self.full_state()})
                if self.vote_open:
                    self.broadcast_vote()

    def drop_silent(self, moment: float) -> None:
        """Let go of connections that have stopped saying anything.

        Called from the tick.  The socket is closed as well as forgotten, so
        the reader thread sitting on it unwinds and runs its own clean-up;
        ``remove_player`` is happy to be called twice, and it is the one
        that tells everybody and files the stats.
        """
        for player in list(self.players.values()):
            if moment - player.last_message < SILENT_SECONDS:
                continue
            player.connected = False
            try:
                if player.ws is not None:
                    player.ws.close()
            except Exception:
                pass
            self.remove_player(player.pid)

    # ------------------------------------------------------------------ info
    def describe(self) -> Dict[str, Any]:
        return {
            "id": self.instance_id,
            "players": [{"user_id": p.user_id, "name": p.username,
                         "team": p.team, "score": p.score, "kills": p.kills}
                        for p in self.players.values()],
            "count": len(self.players),
            "max": self.max_players,
            "phase": self.phase,
            "round": self.round_number,
            "uptime": round(now() - self.created_at, 1),
            "state": self.round_state(),
        }

    def is_full(self) -> bool:
        return len(self.players) >= self.max_players

    def is_empty(self) -> bool:
        return not self.players
