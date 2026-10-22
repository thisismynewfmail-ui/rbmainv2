"""The round-and-area engine every arena world runs on.

**A world** is one map holding four (or more) separate places.  A round is
played in one of them: a short **setup** (find your feet, read the twist,
get to your spawn), the **active** round under the world's own rules, then
the **results** card.  After ``ROUNDS_PER_AREA`` rounds in one place the
server shuffles to another at random -- the results card spins a reel of the
places and lands on it, and arriving plays that place's own arrival sequence.
Only the place being played is ever sent to a client.

**What a world writes** is its rules, through a handful of hooks:

``arm_area``        put the round's entities in place (pickups, carts, NPCs)
``assign_teams``    teams and roles at the start of a round (swaps, secrets)
``round_begin``     the whistle: setup is over
``active_tick``     the round itself, every tick
``round_check``     ``(winner, reason)`` when the round is decided, else None
``time_up``         the same, when the clock runs out
``on_use``          E pressed (``start_channel`` for anything held)
``arena_fire``      a world tool fired (``kind: "arena"`` items)
``result_rows``     the results table
``player_pub``      what everyone may see about a player (a disguise, a bag)
``player_me``       what only that player sees (a secret role)

**The shared machinery**: teams balanced as people join, spawn rooms per
team or role in every place, elimination (the dead watch until the next
round) or respawns, hold-E channels with a progress bar, loadouts a world
lends and takes back, entities the client draws, round twists, results and
badges, speech events for the bots, and the sleeping-round hand-off.

**A round with nobody real in it holds its breath**: its clocks stop and
nothing moves until somebody is back, exactly like Last Light, so a round of
bots costs nothing while it waits to be put to sleep.
"""
from __future__ import annotations

import math
import random
import time
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

from ..instance import (EYE_HEIGHT, MAX_HEALTH, GameInstance, Player, now,
                        ray_aabb, vec_len)
from ..gear import Minion
from ...models import catalog
from . import kit
from .entities import ENT_PID_BASE, Ent, Track, flat_dist

NEVER = 1e18
USE_RANGE = 7.5

TEAM_DEFAULTS = {
    "red": {"name": "Red", "colour": "#c4281c", "light": "#ff9a90"},
    "blue": {"name": "Blue", "colour": "#0d69ac", "light": "#9ecbff"},
    "ffa": {"name": "Everyone", "colour": "#e0a040", "light": "#ffe08a"},
}


class Channel:
    """Somebody holding E on something: a vault, a dig site, a computer."""

    __slots__ = ("key", "label", "secs", "done", "cancel", "point", "radius",
                 "progress", "check", "rate", "data")

    def __init__(self, key: str, label: str, secs: float, point: Sequence[float],
                 radius: float, done: Callable[[], None],
                 cancel: Optional[Callable[[], None]] = None,
                 check: Optional[Callable[[], bool]] = None, rate: float = 1.0):
        self.key, self.label, self.secs = key, label, max(0.1, float(secs))
        self.done, self.cancel, self.check = done, cancel, check
        self.point, self.radius = list(point), float(radius)
        self.progress = 0.0
        self.rate = rate
        self.data: Dict[str, Any] = {}


class ArenaWorld(GameInstance):
    mode = "arena"
    friendly_fire = False
    shuffle_enabled = False
    respawn_seconds = 4.0

    MAP = None                     # the map package (build() / area modules)
    TEAMS: Sequence[str] = ("red", "blue")
    TEAM_INFO: Dict[str, Dict[str, str]] = {}
    FFA = False                    # one team, everybody can hit everybody
    ROUNDS_PER_AREA = 2
    FIRST_SETUP = 18.0             # a new place: look round (the intro plays)
    SETUP_SECONDS = 12.0
    ROUND_SECONDS = 300.0
    END_SECONDS = 9.0              # the results card
    MOVE_EXTRA = 4.5               # ...and the reel, when the place changes
    ELIMINATION = False            # the dead stay down until the next round
    SWAP_TEAMS = False             # sides swap every round
    BALANCE = True
    TWISTS: Dict[str, Dict[str, str]] = {}
    TWIST_CHANCE = 0.3
    TWIST_FROM = 2                 # the first round (in a place) a twist may come
    RESULT_COLS: Sequence[Tuple[str, str]] = (("score", "Score"),)
    PLAN = None                    # the bots' plan (app/game/arena/bots.py)
    HELP: Sequence[str] = ()       # lines told to whoever joins

    @classmethod
    def build_map(cls) -> Dict[str, Any]:
        return cls.MAP.build()

    # ================================================================ setup
    def setup(self) -> None:
        markers = self.map.get("markers", {})
        self.areas: Dict[str, Dict[str, Any]] = {a["id"]: a for a in markers.get("areas", [])}
        self.area_order: List[str] = [a["id"] for a in markers.get("areas", [])]
        self.rng = random.Random()
        self.area_id = self.rng.choice(self.area_order)
        self.rounds_here = 0
        self.round_number = 1
        self.phase = "setup"
        self.phase_until = now() + self.FIRST_SETUP
        self.round_ends = 0.0
        self.round_started = now()
        self.scores: Dict[str, float] = {t: 0 for t in self.team_names()}
        self.twist = ""
        self.last_twist = ""
        self.next_area_id: Optional[str] = None
        self.ents: Dict[int, Ent] = {}
        self._ent_seq = 1
        self._ent_changed: Dict[int, Ent] = {}
        self._ent_gone: List[int] = []
        self._payloads: Dict[str, Dict[str, Any]] = {}
        self.channels: Dict[int, Channel] = {}
        self._pub: Dict[int, Dict[str, Any]] = {}
        self._me_tick = 0
        self.round_log: List[str] = []
        self.last_result: Dict[str, Any] = {}
        if self.FFA:
            self.friendly_fire = True
        nav = getattr(self.host, "nav", None)
        if nav is not None and not getattr(nav, "ready", True):
            nav.build_async()
        self.world_setup()
        self.arm_area()

    def world_setup(self) -> None:
        """Hook: once, when the instance is made."""

    # ================================================================ teams
    def team_names(self) -> List[str]:
        return ["ffa"] if self.FFA else list(self.TEAMS)

    def team_info(self, team: str) -> Dict[str, str]:
        info = dict(TEAM_DEFAULTS.get(team, {"name": team.title(), "colour": "#e0a040",
                                             "light": "#ffe08a"}))
        info.update(self.TEAM_INFO.get(team, {}))
        return info

    def pick_team(self, player: Player) -> str:
        teams = self.team_names()
        if len(teams) == 1:
            return teams[0]
        counts = {t: 0 for t in teams}
        for other in self.players.values():
            if other is not player and other.team in counts:
                counts[other.team] += 1
        return min(teams, key=lambda t: (counts[t], self.rng.random()))

    def assign_teams(self, moved: bool) -> None:
        """Hook: teams (and roles) at the start of every round.  The default
        swaps sides when the world says so and levels them otherwise."""
        players = list(self.players.values())
        teams = self.team_names()
        if len(teams) < 2:
            return
        if self.SWAP_TEAMS and not moved:
            for p in players:
                if p.team in teams:
                    p.team = teams[(teams.index(p.team) + 1) % len(teams)]
        elif moved:
            self.rng.shuffle(players)
            for index, p in enumerate(players):
                p.team = teams[index % len(teams)]
        self.level_teams()
        for p in players:
            p.send({"t": "team", "team": p.team})
        self.broadcast({"t": "teams", "map": {p.pid: p.team for p in self.players.values()}})

    def level_teams(self) -> None:
        teams = self.team_names()
        if len(teams) < 2 or not self.BALANCE:
            return
        for _ in range(len(self.players)):
            counts = {t: [p for p in self.players.values() if p.team == t] for t in teams}
            big = max(teams, key=lambda t: len(counts[t]))
            small = min(teams, key=lambda t: len(counts[t]))
            if len(counts[big]) - len(counts[small]) <= 1:
                break
            mover = sorted(counts[big], key=lambda p: (p.brain is None, self.rng.random()))[0]
            mover.team = small

    def players_on(self, team: str) -> List[Player]:
        return [p for p in self.players.values() if p.team == team]

    def humans_here(self) -> bool:
        return any(p.brain is None for p in self.players.values())

    # ================================================================ areas
    @property
    def area(self) -> Dict[str, Any]:
        return self.areas[self.area_id]

    def area_data(self, key: str, default: Any = None) -> Any:
        return (self.area.get("data") or {}).get(key, default)

    def points(self, kind: str) -> List[Dict[str, Any]]:
        return list((self.area.get("points") or {}).get(kind, []))

    def map_payload(self, player: Optional[Player] = None) -> Dict[str, Any]:
        cached = self._payloads.get(self.area_id)
        if cached is None:
            cached = kit.area_payload(self.map, self.area_id)
            self._payloads[self.area_id] = cached
        return cached

    def _pick_next(self) -> str:
        options = [a for a in self.area_order if a != self.area_id] or self.area_order
        return self.rng.choice(options)

    def arm_area(self) -> None:
        """Hook: the round's entities, in the current place."""

    def landmark_near(self, pos: Sequence[float], within: float = 90.0) -> str:
        best, best_d = "", within
        for mark in self.area.get("landmarks") or []:
            d = flat_dist(mark["p"], pos)
            if d < best_d:
                best, best_d = mark["name"], d
        return best

    # ============================================================== spawning
    def spawn_key(self, player: Player) -> str:
        """Which of the place's spawn rooms this player comes out of."""
        return player.team

    def spawn_points(self, team: str) -> List[Dict[str, Any]]:
        spawns = self.area.get("spawns") or {}
        player = getattr(self, "_spawning", None)
        key = self.spawn_key(player) if player is not None else team
        points = spawns.get(key) or spawns.get(team) or []
        if not points:
            points = [s for group in spawns.values() for s in group]
        return list(points) or [{"p": list(self.area["centre"]), "yaw": 0.0}]

    def spawn_player(self, player: Player) -> None:
        self._spawning = player
        try:
            super().spawn_player(player)
        finally:
            self._spawning = None
        player.extra.pop("out", None)
        self.after_spawn(player)
        self.mark_pub(player)
        self.send_me(player, force=True)
        if player.brain is not None:
            player.brain.on_spawn()

    def after_spawn(self, player: Player) -> None:
        """Hook: just spawned (statuses, loadouts, carried things)."""

    def place_at(self, player: Player, pos: Sequence[float], yaw: Optional[float] = None) -> None:
        """Move somebody without a respawn (a jail cell, a freezer pod)."""
        player.pos = [float(pos[0]), float(pos[1]), float(pos[2])]
        player.last_ground_pos = list(player.pos)
        player.vel = [0.0, 0.0, 0.0]
        player.extra["tp_grace"] = now() + 0.8
        if yaw is not None:
            player.yaw = float(yaw)
        if player.brain is not None:
            player.brain.ground = list(player.pos)
            player.brain.airborne = True
            player.brain.vy = 0.0
            player.brain.waypoints = []
        else:
            player.send({"t": "spawn", "p": player.pos, "yaw": player.yaw,
                         "hp": int(player.health), "prot": 0, "stowed": player.stowed})

    # ------------------------------------------------------------ players
    def on_player_join(self, player: Player) -> None:
        player.extra["ar"] = {}
        if self.ELIMINATION and self.phase in ("active", "ended"):
            self.knock_out(player, quiet=True)
        self.player_joined(player)

    def player_joined(self, player: Player) -> None:
        """Hook: a joiner, after the team is chosen."""

    def on_player_ready(self, player: Player) -> None:
        area = self.area
        player.send({"t": "ar_area", "area": self.area_id, "name": area["name"],
                     "round": self.round_number, "in_area": self.rounds_here + 1,
                     "of": self.ROUNDS_PER_AREA, "intro": False, "join": True,
                     "twist": self.twist, **self._twist_text()})
        player.send({"t": "ar_ents", "all": [e.row() for e in self.ents.values()]})
        for line in self.help_lines(player):
            player.send({"t": "chat", "kind": "system", "from": "", "id": 0, "m": line,
                         "at": time.time()})
        if player.extra.get("out"):
            player.send({"t": "died", "in": -1, "by": "", "spectate": True})
        self.send_me(player, force=True)

    def help_lines(self, player: Player) -> List[str]:
        lines = ["%s -- %s." % (self.world["name"], self.area["name"])]
        lines.extend(self.HELP)
        if player.extra.get("out"):
            lines.append("A round is on: you join in at the next one. Click to switch who "
                         "you watch.")
        return lines

    def on_player_leave(self, player: Player) -> None:
        self.channels.pop(player.pid, None)
        self._pub.pop(player.pid, None)
        self.player_left(player)

    def player_left(self, player: Player) -> None:
        """Hook: somebody left the round."""

    # ======================================================== elimination
    def knock_out(self, player: Player, quiet: bool = False) -> None:
        """Out until the next round: spectating (the elimination worlds)."""
        player.alive = False
        player.health = 0
        player.respawn_at = NEVER
        player.extra["out"] = True
        self.channels.pop(player.pid, None)
        self.mark_pub(player)
        if not quiet:
            player.send({"t": "died", "in": -1, "by": "", "spectate": True})
        self.send_me(player, force=True)

    def alive_players(self, team: Optional[str] = None) -> List[Player]:
        return [p for p in self.players.values() if p.alive and not p.extra.get("out")
                and (team is None or p.team == team)]

    def kill(self, victim, killer, weapon_name: str, headshot: bool = False) -> None:
        if isinstance(victim, Ent):
            self.ent_killed(victim, killer, weapon_name)
            return
        if not victim.alive:
            return
        super().kill(victim, killer, weapon_name, headshot)
        self.channels.pop(victim.pid, None)
        if self.ELIMINATION:
            victim.respawn_at = NEVER
            victim.extra["out"] = True
            victim.send({"t": "died", "in": -1, "by": getattr(killer, "username", "") or
                         weapon_name, "spectate": True})
        self.mark_pub(victim)
        self.send_me(victim, force=True)

    # ============================================================== damage
    def targetables(self, shooter) -> Iterable[Any]:
        """Hook: entities somebody can shoot (robots, decoys, vault doors)."""
        return ()

    def nearest_player_hit(self, shooter, origin, direction, max_dist: float):
        victim, best, head = super().nearest_player_hit(shooter, origin, direction, max_dist)
        for ent in self.targetables(shooter):
            if not ent.alive:
                continue
            lo, hi = ent.hitbox()
            hit = ray_aabb(origin, direction, lo, hi)
            if hit is None or hit >= best:
                continue
            hlo, hhi = ent.head_box()
            victim, best = ent, hit
            head = ray_aabb(origin, direction, hlo, hhi) is not None
        return victim, best, head

    def apply_damage(self, victim, attacker, amount: float, weapon_name: str,
                     headshot: bool = False) -> None:
        if isinstance(victim, Minion):
            self.gear.hurt_minion(victim, attacker, amount, weapon_name)
            return
        if isinstance(victim, Ent):
            self.hurt_ent(victim, attacker, amount, weapon_name, headshot)
            return
        amount = self.adjust_damage(victim, attacker, float(amount), weapon_name, headshot)
        if amount <= 0:
            return
        super().apply_damage(victim, attacker, amount, weapon_name, headshot)

    def adjust_damage(self, victim: Player, attacker, amount: float, weapon: str,
                      headshot: bool) -> float:
        """Hook: what a hit does to a player (0 for none)."""
        return amount

    def hurt_ent(self, ent: Ent, attacker, amount: float, weapon: str,
                 headshot: bool = False) -> None:
        """Hook: an entity was hit.  The default knocks hit points off it."""
        if ent.hp <= 0 or not ent.alive:
            return
        ent.hp -= amount
        if attacker is not None and hasattr(attacker, "send"):
            attacker.send({"t": "dealt", "a": round(amount, 1), "hs": headshot,
                           "target": ent.pid, "hp": max(0, int(ent.hp))})
        if ent.hp <= 0:
            self.ent_killed(ent, attacker, weapon)
        else:
            self.touch_ent(ent)

    def ent_killed(self, ent: Ent, killer, weapon: str) -> None:
        """Hook: an entity was destroyed."""
        self.drop_ent(ent)

    def entity(self, eid: Optional[int]):
        if eid is None:
            return None
        found = self.players.get(eid)
        if found is not None:
            return found
        if eid >= ENT_PID_BASE:
            return self.ents.get(eid - ENT_PID_BASE)
        return None

    def hostiles_for(self, player: Player):
        """What a bot in this world fights: by default the other team (or,
        free for all, everyone), plus whatever the world says is a target."""
        if player.extra.get("out") or not player.alive:
            return
        for other in self.players.values():
            if other is player or not other.alive or other.extra.get("out"):
                continue
            if other.team == player.team and not self.friendly_fire:
                continue
            if self.can_target(player, other):
                yield other
        for ent in self.targetables(player):
            if ent.alive:
                yield ent

    def can_target(self, player: Player, other: Player) -> bool:
        """Hook: may this player's bot go for that one?"""
        return True

    # -------------------------------------------------------------- shoves
    def _knock_out(self, player, velocity) -> None:
        self.knock_player(player, velocity)

    def knock_player(self, player, velocity: Sequence[float]) -> None:
        """A shove, for a person (their browser moves them) or a bot (its
        body does)."""
        if not getattr(player, "alive", False):
            return
        if getattr(player, "brain", None) is not None:
            player.brain.knock(velocity)
        elif hasattr(player, "send"):
            player.send({"t": "knock", "v": [round(v, 2) for v in velocity]})

    def launch(self, player, velocity: Sequence[float], secs: float = 1.6) -> None:
        """A jump pad, a cannon, a blast: the host lets them fly."""
        player.extra["launch_until"] = now() + secs
        self.knock_player(player, velocity)

    # ============================================================ channels
    def start_channel(self, player: Player, key: str, label: str, secs: float,
                      point: Sequence[float], done: Callable[[], None],
                      cancel: Optional[Callable[[], None]] = None,
                      check: Optional[Callable[[], bool]] = None,
                      radius: float = USE_RANGE + 1.5, rate: float = 1.0) -> Channel:
        current = self.channels.get(player.pid)
        if current is not None and current.key == key:
            return current
        channel = Channel(key, label, secs, point, radius, done, cancel, check, rate)
        self.channels[player.pid] = channel
        player.extra["using"] = True
        self.send_me(player, force=True)
        return channel

    def channelling(self, player: Player, key: str = "") -> bool:
        ch = self.channels.get(player.pid)
        return ch is not None and (not key or ch.key == key)

    def channels_on(self, key: str) -> List[Tuple[Player, Channel]]:
        out = []
        for pid, ch in self.channels.items():
            p = self.players.get(pid)
            if p is not None and ch.key == key:
                out.append((p, ch))
        return out

    def stop_channel(self, player: Player, finished: bool = False) -> None:
        ch = self.channels.pop(player.pid, None)
        if ch is not None and not finished and ch.cancel is not None:
            try:
                ch.cancel()
            except Exception:
                pass
        self.send_me(player, force=True)

    def _tick_channels(self, dt: float) -> None:
        for pid, ch in list(self.channels.items()):
            p = self.players.get(pid)
            if p is None or not p.alive or p.extra.get("out") or not p.extra.get("using") \
                    or flat_dist(p.pos, ch.point) > ch.radius or \
                    abs(p.pos[1] - ch.point[1]) > 9.0 or \
                    (ch.check is not None and not ch.check()):
                if p is not None:
                    self.stop_channel(p)
                else:
                    self.channels.pop(pid, None)
                continue
            ch.progress += dt * ch.rate
            if ch.progress >= ch.secs:
                self.channels.pop(pid, None)
                try:
                    ch.done()
                finally:
                    self.send_me(p, force=True)

    # ============================================================= actions
    def on_action(self, player: Player, message: Dict[str, Any]) -> None:
        kind = message.get("k")
        if kind == "use":
            player.extra["using"] = True
            if player.alive and not player.extra.get("out") and \
                    self.phase in ("setup", "active") and player.pid not in self.channels:
                self.on_use(player)
        elif kind == "unuse":
            player.extra["using"] = False
            if player.pid in self.channels:
                self.stop_channel(player)
        elif kind == "watch":
            try:
                player.extra["watching"] = max(0, int(message.get("id") or 0))
            except (TypeError, ValueError):
                player.extra["watching"] = 0
        else:
            self.on_world_action(player, kind, message)

    def on_use(self, player: Player) -> None:
        """Hook: E pressed."""

    def on_world_action(self, player: Player, kind: Any, message: Dict[str, Any]) -> None:
        """Hook: anything else the world's client sends as an ``act``."""

    def near_point(self, player, kind: str, radius: float = USE_RANGE
                   ) -> Optional[Tuple[int, Dict[str, Any]]]:
        best, best_d = None, radius
        for index, point in enumerate(self.points(kind)):
            d = flat_dist(player.pos, point["p"])
            if d < best_d and abs(player.pos[1] - point["p"][1]) < 8.0:
                best, best_d = (index, point), d
        return best

    def near_ent(self, player, kinds: Sequence[str], radius: float = USE_RANGE,
                 test: Optional[Callable[[Ent], bool]] = None) -> Optional[Ent]:
        best, best_d = None, radius
        for ent in self.ents.values():
            if ent.kind not in kinds or not ent.alive:
                continue
            if test is not None and not test(ent):
                continue
            d = flat_dist(player.pos, ent.pos)
            if d < best_d and abs(player.pos[1] - ent.pos[1]) < 9.0:
                best, best_d = ent, d
        return best

    # =============================================================== tools
    def handle_fire(self, player: Player, message: Dict[str, Any]) -> None:
        stats = player.weapon_stats() if not player.stowed else {}
        if stats.get("kind") != "arena":
            if not self.may_fire(player):
                return
            super().handle_fire(player, message)
            return
        with self.lock:
            if not player.alive or player.extra.get("out") or \
                    self.phase not in ("active", "setup"):
                return
            if not self.gear.can_fire(player):
                return
            moment = now()
            if moment < player.next_fire:
                return
            rpm = float(stats.get("rpm", 60) or 60)
            player.next_fire = moment + max(0.05, 60.0 / max(1.0, rpm))
            direction = message.get("d")
            if not (isinstance(direction, list) and len(direction) == 3):
                return
            try:
                d = [float(direction[0]), float(direction[1]), float(direction[2])]
            except (TypeError, ValueError):
                return
            length = vec_len(d) or 1.0
            d = [d[0] / length, d[1] / length, d[2] / length]
            origin = [player.pos[0], player.pos[1] + EYE_HEIGHT, player.pos[2]]
            self.arena_fire(player, stats, d, origin)

    def may_fire(self, player: Player) -> bool:
        """Hook: may this player use a real weapon right now?"""
        return not player.extra.get("out")

    def arena_fire(self, player: Player, stats: Dict[str, Any], direction, origin) -> None:
        """Hook: a world tool (``kind: "arena"``) was used."""

    def look_ent(self, player: Player, kinds: Sequence[str], reach: float,
                 direction, origin) -> Optional[Ent]:
        """The entity of one of ``kinds`` a player is looking at, in reach."""
        best, best_d = None, reach
        wall = self.ray_world(origin, direction, reach)
        for ent in self.ents.values():
            if ent.kind not in kinds or not ent.alive:
                continue
            lo, hi = ent.hitbox()
            pad = 0.6
            hit = ray_aabb(origin, direction, [lo[0] - pad, lo[1] - pad, lo[2] - pad],
                           [hi[0] + pad, hi[1] + pad, hi[2] + pad])
            if hit is not None and hit < best_d and hit <= wall + 1.0:
                best, best_d = ent, hit
        return best

    # ============================================================ loadouts
    def give_loadout(self, player: Player, items: Sequence[Optional[Dict[str, Any]]],
                     slot: int = 0) -> None:
        """Lend this player the world's own hotbar (until ``restore_loadout``)."""
        if "own_hotbar" not in player.extra:
            player.extra["own_hotbar"] = list(player.avatar.get("hotbar") or [])
        hotbar = list(items)[:catalog.HOTBAR_SIZE]
        hotbar += [None] * (catalog.HOTBAR_SIZE - len(hotbar))
        self._set_hotbar(player, hotbar, slot)

    def restore_loadout(self, player: Player) -> None:
        own = player.extra.pop("own_hotbar", None)
        if own is None:
            return
        hotbar = list(own) + [None] * (catalog.HOTBAR_SIZE - len(own))
        first = next((i for i, item in enumerate(hotbar) if item), 0)
        self._set_hotbar(player, hotbar, first)

    def _set_hotbar(self, player: Player, hotbar: List[Optional[Dict[str, Any]]],
                    slot: int) -> None:
        avatar = dict(player.avatar)
        avatar["hotbar"] = hotbar
        player.avatar = avatar
        if not (0 <= slot < len(hotbar)) or not hotbar[slot]:
            slot = next((i for i, item in enumerate(hotbar) if item), 0)
        player.slot = slot
        player.stowed = False
        player.reload_until = 0.0
        player.reset_ammo()
        payload = {"t": "ar_loadout", "id": player.pid, "hotbar": hotbar, "slot": slot}
        self.broadcast(payload)

    # ============================================================ entities
    def spawn_ent(self, kind: str, pos: Sequence[float], yaw: float = 0.0, s: Any = 0,
                  live: bool = False, team: str = "world", hp: float = 0.0,
                  size: Sequence[float] = (3.0, 4.0, 3.0), name: str = "") -> Ent:
        ent = Ent(self._ent_seq, kind, pos, yaw, s, live, team, hp, size, name)
        self._ent_seq += 1
        self.ents[ent.id] = ent
        self._ent_changed[ent.id] = ent
        return ent

    def touch_ent(self, ent: Ent) -> None:
        """Something about ``ent`` changed that the clients should see."""
        if ent.id in self.ents:
            self._ent_changed[ent.id] = ent

    def drop_ent(self, ent: Ent) -> None:
        ent.alive = False
        if self.ents.pop(ent.id, None) is not None:
            self._ent_changed.pop(ent.id, None)
            self._ent_gone.append(ent.id)

    def clear_ents(self) -> None:
        self.ents.clear()
        self._ent_changed.clear()
        self._ent_gone = []
        self.broadcast({"t": "ar_ents", "all": []})

    def ents_of(self, *kinds: str) -> List[Ent]:
        return [e for e in self.ents.values() if e.kind in kinds]

    def _flush_ents(self) -> None:
        if not self._ent_changed and not self._ent_gone:
            return
        payload: Dict[str, Any] = {"t": "ar_ents"}
        if self._ent_changed:
            payload["u"] = [e.row() for e in self._ent_changed.values()]
        if self._ent_gone:
            payload["d"] = list(self._ent_gone)
        self._ent_changed = {}
        self._ent_gone = []
        self.broadcast(payload)

    # ====================================================== public / private
    def player_pub(self, player: Player) -> Dict[str, Any]:
        """Hook: what everybody may see about a player (a disguise, a role
        that is not a secret, a bag on their back)."""
        return {}

    def mark_pub(self, player: Player) -> None:
        pub = self.player_pub(player)
        if player.extra.get("out"):
            pub = dict(pub, x=1)
        if self._pub.get(player.pid) != pub:
            self._pub[player.pid] = pub
            self.broadcast({"t": "ar_pub", "id": player.pid, "f": pub})

    def player_me(self, player: Player) -> Dict[str, Any]:
        """Hook: what only this player sees about themselves."""
        return {}

    def send_me(self, player: Player, force: bool = False) -> None:
        if player.ws is None:
            return
        ch = self.channels.get(player.pid)
        me = {"team": player.team, "out": bool(player.extra.get("out")),
              "chan": [ch.label, round(min(1.0, ch.progress / ch.secs), 2)] if ch else None}
        me.update(self.player_me(player))
        if not force and me == player.extra.get("_arme"):
            return
        player.extra["_arme"] = me
        payload = {"t": "ar_me"}
        payload.update(me)
        player.send(payload)

    # ============================================================== rounds
    def _twist_text(self) -> Dict[str, str]:
        info = self.TWISTS.get(self.twist) or {}
        return {"twist_name": info.get("name", ""), "twist_blurb": info.get("blurb", "")}

    def roll_twist(self) -> str:
        if not self.TWISTS or self.rounds_here + 1 < self.TWIST_FROM:
            return ""
        if self.rng.random() >= self.TWIST_CHANCE:
            return ""
        options = [t for t in self.TWISTS if t != self.last_twist] or list(self.TWISTS)
        return self.rng.choice(options)

    def round_length(self) -> float:
        return float(self.ROUND_SECONDS)

    def begin_round(self) -> None:
        moment = now()
        self.phase = "active"
        self.round_started = moment
        self.round_ends = moment + self.round_length()
        self.phase_until = self.round_ends
        self.round_log = []
        self.round_begin()
        info = self._twist_text()
        self.broadcast({"t": "ar_round", "on": True, "round": self.round_number,
                        "in_area": self.rounds_here + 1, "of": self.ROUNDS_PER_AREA,
                        "twist": self.twist, "secs": round(self.round_length()), **info,
                        **self.round_banner()})
        text = self.round_banner().get("title", "Go!")
        if info["twist_name"]:
            text += " (%s: %s)" % (info["twist_name"], info["twist_blurb"])
        self.system_message(text)
        self.push_event("ar_go", what=self.area["name"], n=self.round_number,
                        twist=info["twist_name"])
        for p in self.players.values():
            self.send_me(p, force=True)

    def round_begin(self) -> None:
        """Hook: setup is over."""

    def round_banner(self) -> Dict[str, str]:
        """Hook: the words on the go banner."""
        return {"title": "Round %d -- go!" % self.round_number, "sub": ""}

    def round_check(self, moment: float) -> Optional[Tuple[str, str]]:
        """Hook: ``(winner, reason)`` once the round is decided."""
        return None

    def time_up(self) -> Tuple[str, str]:
        """Hook: who wins when the clock runs out."""
        if self.scores:
            best = max(self.scores, key=lambda t: self.scores[t])
            if list(self.scores.values()).count(self.scores[best]) == 1:
                return best, "Time is up."
        return "", "Time is up -- a draw."

    def winner_label(self, winner: str) -> Tuple[str, str]:
        """(headline, colour) for the results card."""
        if not winner:
            return "DRAW", "#6f8095"
        if winner in self.team_names():
            info = self.team_info(winner)
            return "%s WINS" % info["name"].upper(), info["colour"]
        player = self.players.get(int(winner)) if str(winner).isdigit() else None
        if player is not None:
            return "%s WINS" % player.username.upper(), "#e0a040"
        return str(winner).upper(), "#e0a040"

    def player_won(self, player: Player, winner: str) -> bool:
        if not winner:
            return False
        if winner in self.team_names():
            return player.team == winner
        return str(player.pid) == str(winner)

    def result_rows(self) -> List[Dict[str, Any]]:
        rows = []
        for p in self.players.values():
            row = {"id": p.pid, "name": p.username, "team": p.team, "score": p.score,
                   "kills": p.kills, "deaths": p.deaths}
            row.update(self.result_extra(p))
            rows.append(row)
        rows.sort(key=lambda r: (-float(r.get(self.RESULT_COLS[0][0], 0) or 0),
                                 r["name"].lower()))
        return rows

    def result_extra(self, player: Player) -> Dict[str, Any]:
        """Hook: this player's extra columns on the results card."""
        return {}

    def end_round(self, winner: str, reason: str = "") -> None:
        if self.phase == "ended":
            return
        moment = now()
        self.phase = "ended"
        for p in list(self.players.values()):
            if p.pid in self.channels:
                self.stop_channel(p)
        moving = self.rounds_here + 1 >= self.ROUNDS_PER_AREA and len(self.area_order) > 1
        nxt = self._pick_next() if moving else self.area_id
        self.next_area_id = nxt
        secs = self.END_SECONDS + (self.MOVE_EXTRA if moving else 0.0)
        self.phase_until = moment + secs
        headline, colour = self.winner_label(winner)
        self.round_finished(winner)
        card = {"t": "ar_end", "winner": winner, "title": headline, "colour": colour,
                "reason": reason, "rows": self.result_rows()[:24],
                "cols": [list(c) for c in self.RESULT_COLS],
                "moving": moving, "area": self.area["name"], "area_id": self.area_id,
                "next": self.areas[nxt]["name"], "next_id": nxt, "in": round(secs, 1),
                "in_area": self.rounds_here + 1, "of": self.ROUNDS_PER_AREA,
                "scores": {k: round(v, 1) for k, v in self.scores.items()},
                "reel": [{"id": a, "name": self.areas[a]["name"]} for a in self.area_order],
                "mvp": self.round_mvp()}
        self.last_result = card
        self.broadcast(card)
        for p in self.players.values():
            self.host.report_round(self, p, won=self.player_won(p, winner))
        self.system_message("%s %s" % (headline.title() if winner else "A draw.", reason))
        if moving:
            self.system_message("Next: %s." % self.areas[nxt]["name"])
        sides = {}
        for team in self.team_names():
            if winner in self.team_names():
                sides[team] = (("Your team won the round: %s" % reason, "ally")
                               if team == winner else
                               ("Your team lost the round: %s" % reason, "victim"))
        winner_name = ""
        if winner and winner not in self.team_names():
            found = self.players.get(int(winner)) if str(winner).isdigit() else None
            winner_name = found.username if found else str(winner)
        self.say("ar_end", by=winner_name, by_team=winner if winner in self.team_names() else "",
                 actor="You won the round! %s" % reason,
                 sides=sides, default=("The round just ended: %s %s" % (headline.title(), reason),
                                       "neutral"),
                 next=self.areas[nxt]["name"] if moving else "")
        if self.bots is not None:
            self.bots.on_round_end(winner if winner in self.team_names() else "", reason)

    def round_finished(self, winner: str) -> None:
        """Hook: the round is decided (badges for the winners go here)."""

    def round_mvp(self) -> str:
        best = max(self.players.values(), key=lambda p: (p.score, -p.pid), default=None)
        return best.username if best is not None else ""

    def next_round(self) -> None:
        nxt = self.next_area_id or self.area_id
        moved = nxt != self.area_id
        if moved:
            self.rounds_here = 0
        else:
            self.rounds_here += 1
        self.start_round(nxt, moved)

    def start_round(self, area_id: str, moved: bool) -> None:
        moment = now()
        for p in list(self.players.values()):
            if p.pid in self.channels:
                self.stop_channel(p)
        self.clear_ents()
        self.projectiles.clear()
        self.gear.reset()
        self.area_id = area_id
        self.next_area_id = None
        self.round_number += 1
        self.last_twist = self.twist or self.last_twist
        self.twist = self.roll_twist()
        self.scores = {t: 0 for t in self.team_names()}
        self.phase = "setup"
        self.phase_until = moment + (self.FIRST_SETUP if moved else self.SETUP_SECONDS)
        self.round_ends = 0.0
        self.assign_teams(moved)
        self.arm_area()
        payload = {"t": "ar_area", "area": self.area_id, "name": self.area["name"],
                   "round": self.round_number, "in_area": self.rounds_here + 1,
                   "of": self.ROUNDS_PER_AREA, "intro": moved, "twist": self.twist,
                   **self._twist_text()}
        if moved:
            payload["map"] = self.map_payload()
        for p in list(self.players.values()):
            p.kills = 0
            p.deaths = 0
            p.extra.pop("out", None)
            self.reset_player(p)
            p.send(payload)
            p.alive = False
            self.spawn_player(p)
        self.broadcast({"t": "ar_ents", "all": [e.row() for e in self.ents.values()]})
        self._ent_changed = {}
        self._ent_gone = []
        self.broadcast({"t": "round_start", "round": self.round_number,
                        "state": self.full_state()})
        if moved:
            self.system_message("Round %d: %s. %d seconds to get ready."
                                % (self.round_number, self.area["name"],
                                   int(self.FIRST_SETUP)))
        else:
            self.system_message("Round %d: %s again (round %d of %d here)."
                                % (self.round_number, self.area["name"],
                                   self.rounds_here + 1, self.ROUNDS_PER_AREA))
        self.say("ar_area", what=self.area["name"], n=self.rounds_here + 1, retry=not moved,
                 default=(("The server just moved everybody to %s." % self.area["name"])
                          if moved else
                          ("Another round at %s (round %d of %d here)."
                           % (self.area["name"], self.rounds_here + 1, self.ROUNDS_PER_AREA)),
                          "neutral"))
        if self.bots is not None:
            self.bots.on_round_start()

    def reset_player(self, player: Player) -> None:
        """Hook: per-round state off a player before they respawn."""
        for key in ("using",):
            player.extra.pop(key, None)

    # ================================================================ tick
    def _tick_phase(self, moment: float) -> None:
        """The arena's phases run in on_tick, not the base vote cycle."""

    def on_tick(self, dt: float) -> None:
        moment = now()
        if not self.humans_here():
            # nobody real here: the round holds its breath
            self.phase_until += dt
            if self.round_ends:
                self.round_ends += dt
            self.hold(dt)
            return
        self._tick_channels(dt)
        self.world_tick(dt, moment)
        if self.phase == "setup":
            self.setup_tick(dt, moment)
            if moment >= self.phase_until:
                self.begin_round()
        elif self.phase == "active":
            self.active_tick(dt, moment)
            if self.phase == "active":
                result = self.round_check(moment)
                if result is not None:
                    self.end_round(*result)
                elif moment >= self.round_ends:
                    self.end_round(*self.time_up())
        elif self.phase == "ended":
            if moment >= self.phase_until:
                self.next_round()
        self._me_tick += 1
        if self._me_tick % 5 == 0:
            for p in self.players.values():
                self.send_me(p)
        self._flush_ents()

    def hold(self, dt: float) -> None:
        """Hook: nobody real is here; push the world's own timers on by dt."""

    def world_tick(self, dt: float, moment: float) -> None:
        """Hook: every tick in every phase (entities that animate)."""

    def setup_tick(self, dt: float, moment: float) -> None:
        """Hook: every tick of setup."""

    def active_tick(self, dt: float, moment: float) -> None:
        """Hook: every tick of the round."""

    def time_left(self) -> float:
        if self.phase == "active":
            return max(0.0, self.round_ends - now())
        return max(0.0, self.phase_until - now())

    # ================================================================ wire
    def snapshot(self) -> Dict[str, Any]:
        payload = super().snapshot()
        live = [e.row() for e in self.ents.values() if e.live]
        if live:
            payload["es"] = live
        return payload

    def round_state(self) -> Dict[str, Any]:
        moment = now()
        out = {
            "area": self.area_id, "area_name": self.area["name"],
            "aphase": self.phase, "time_left": round(self.time_left(), 1),
            "phase_left": round(max(0.0, self.phase_until - moment), 1),
            "in_area": self.rounds_here + 1, "of": self.ROUNDS_PER_AREA,
            "scores": {k: round(v, 1) for k, v in self.scores.items()},
            "twist": self.twist, "twist_name": self._twist_text()["twist_name"],
            "alive": len(self.alive_players()), "count": len(self.players),
            "pub": {str(pid): f for pid, f in self._pub.items() if f},
        }
        out.update(self.state_extra())
        return out

    def state_extra(self) -> Dict[str, Any]:
        """Hook: the world's own numbers in the once-a-second state."""
        return {}

    def scoreboard(self) -> List[Dict[str, Any]]:
        rows = super().scoreboard()
        for row in rows:
            p = self.players.get(row["id"])
            if p is not None:
                row.update(self.result_extra(p))
                row["out"] = bool(p.extra.get("out"))
        return rows

    def describe(self) -> Dict[str, Any]:
        info = super().describe()
        info["summary"] = "Round %d · %s" % (self.rounds_here + 1, self.area["name"])
        return info

    # ============================================================== speech
    def say(self, kind: str, by: str = "", by_team: str = "", actor: str = "",
            sides: Optional[Dict[str, Tuple[str, str]]] = None,
            default: Tuple[str, str] = ("", "neutral"), **data: Any) -> None:
        """A speech event: something the bots in the round might talk about,
        written up once from every side (``sides[team]``), for whoever did it
        (``actor``) and for everybody else (``default``)."""
        payload = dict(data)
        payload.update({"by": by, "by_team": by_team, "actor": actor,
                        "sides": {k: list(v) for k, v in (sides or {}).items()},
                        "default": list(default), "world": self.world_id})
        self.round_log.append(default[0] or kind)
        del self.round_log[:-12]
        # straight to the bots, never broadcast: a write-up can name a secret
        # (who the Murderer is) that only the bot it is written for may read
        if self.bots is not None:
            self.bots.on_game_event(kind, payload)

    def bot_lines(self) -> List[str]:
        """Hook: what anyone in the round can see right now, as plain lines,
        for the bots' language model."""
        return []

    def bot_plan(self, runner):
        return self.PLAN(runner) if self.PLAN is not None else None

    # =========================================================== sleep/wake
    def sleep_state(self) -> Dict[str, Any]:
        return {"area": self.area_id, "rounds_here": self.rounds_here,
                "round": self.round_number,
                "scores": {k: round(v, 1) for k, v in self.scores.items()}}

    def resume(self, state: Dict[str, Any]) -> None:
        """Pick a sleeping round back up: the same place, the next round."""
        area = state.get("area")
        if area not in self.areas:
            area = self.rng.choice(self.area_order)
        here = max(0, min(self.ROUNDS_PER_AREA - 1, int(state.get("rounds_here", 0) or 0)))
        self.round_number = max(0, int(state.get("round", 1) or 1) - 1)
        moved = area != self.area_id
        self.rounds_here = here
        self.start_round(area, moved)
        self.rounds_here = here
