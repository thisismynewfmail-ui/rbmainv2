"""The event worlds: one server, several areas, one round at a time.

Every event world is built the way Last Light is: a map holding four or more
separate places (app/game/maps/events/kit.py), only one of which is being
played, and a server that moves everybody to another of them -- with that
place's own arrival sequence -- once the current one has had its rounds.
:class:`ArenaWorld` is everything those worlds have in common, so each one
is only its own rules.

**A round** has three phases.  ``setup``: everybody is at their spawns in
the area and the countdown runs (on a new area it waits out the arrival
sequence first).  ``active``: the round itself, until the world decides it
is over or the clock runs out.  ``intermission``: the results card, and --
when the area has had ``ROUNDS_PER_AREA`` rounds -- the reel that lands on
the next area, picked at random from the others.

**Spawning** is per area, per team and per *stage*: a world whose front moves
(a cart past a depot, a site taken) returns ``spawn_stage(team)`` and its
team comes back further up.  In an ``ELIMINATION`` world the fallen, and
anybody who joins once the round is live, watch the living -- the client's
spectator camera tells the server whose shoulder it is over, and the bots
near *that* player run at full detail.

**Kit.**  A world can hand out its own items for a round (``set_loadout``):
a dodgeball, a revolver, a paint blaster.  They are hotbar entries in the
avatar's own format, so the HUD, the view model and other players' hands
all draw them with no special case; a kind listed in ``CUSTOM_KINDS`` is
fired through the world's own ``custom_fire`` instead of the engine's.

**Switchable solids** -- start gates, falling floors, a vault door -- live
outside the static map: they collide (on the server through
``_colliders_near``, on the client through Physics.setDynamic) only while
they are switched on.

**Nobody real here** and the round holds its breath, as Last Light's does:
every timer is held until somebody is, because the bots stand still too.

**Bots** play through hooks the runner calls (app/game/bots/runner.py):
``bot_role``, ``bot_objective``, ``bot_goal_weights``, ``bot_me`` and the
rest, each with a sensible default here.
"""
from __future__ import annotations

import math
import random
import time
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from .. import instance as engine
from ..gear import Minion
from ..instance import (EYE_HEIGHT, MAX_HEALTH, STOW_SLOT, GameInstance, Player,
                        normalise)
from ..maps.events import kit as arena_kit
from ...models import catalog

NEVER = 1e18
COLLIDER_CELL = 48.0


class ArenaWorld(GameInstance):
    engine = "arena"
    mode = "arena"
    shuffle_enabled = False
    friendly_fire = False
    respawn_seconds = 4.0

    # ---- the world's own numbers (each subclass sets what it needs)
    MAP = None                   # the map package: build()
    TEAMS: Sequence[str] = ("red", "blue")
    TEAM_NAMES: Dict[str, str] = {"red": "Red", "blue": "Blue"}
    FFA = False                  # every player for themselves (team "ffa")
    ROUNDS_PER_AREA = 1
    INTRO_SECONDS = 7.2          # the arrival sequence on a new area
    SETUP_SECONDS = 10.0         # the countdown before a round goes live
    ROUND_SECONDS = 360.0        # 0: no clock
    RESULTS_SECONDS = 15.0
    ELIMINATION = False          # the fallen watch until the next round
    BALANCE = True               # even the teams up between rounds
    WARMUP_FIRE = False          # may people shoot during the countdown
    CATCHES_FALLS = False        # the world sends fallers back itself (an obby)
    FREEZE_COUNTDOWN = False     # everybody stands still at their spawn through the countdown
    CUSTOM_KINDS: Tuple[str, ...] = ()
    HELD_TIMERS: Tuple[str, ...] = ()   # extra timers to hold with nobody here
    LOGO = ""                    # what the arrival sequence and cards say
    BOT_REVENGE = 1.0
    BOT_CHATTER: List[str] = ["gg", "lol", "nice", "lets go", "anyone", "go go"]

    @classmethod
    def build_map(cls) -> Dict[str, Any]:
        return cls.MAP.build()

    # ============================================================== setup
    def setup(self) -> None:
        markers = self.map.get("markers", {})
        self.area_order = [a["id"] for a in markers.get("areas", [])]
        self.areas: Dict[str, Dict[str, Any]] = {a["id"]: a for a in markers.get("areas", [])}
        self.rng = random.Random()
        self._payloads: Dict[str, Dict[str, Any]] = {}
        self.area_id = self.rng.choice(self.area_order)
        self.area_round = 0
        self.wins: Dict[str, int] = {}
        self._next_area_id: Optional[str] = None
        self._shuffle_next = False
        self.round_ends = 0.0
        self.round_started = engine.now()
        self.live_since = 0.0
        self.results: Dict[str, Any] = {}
        self.dyn_on: Dict[str, bool] = {}
        self._dyn_boxes: List[Tuple[List[float], List[float]]] = []
        self._dyn_grid: Dict[Tuple[int, int], List[int]] = {}
        self._me_tick = 0
        # the round the instance is made with counts as the area's first
        self._first_round = False
        self._arm_area()
        self.phase = "setup"
        self.phase_until = engine.now() + self.INTRO_SECONDS + self.SETUP_SECONDS
        nav = getattr(self.host, "nav", None)
        if nav is not None and not nav.ready:
            nav.build_async()
        self.world_setup()
        self.round_setup()

    def world_setup(self) -> None:
        """Subclass hook: once, when the instance is made."""

    def round_setup(self) -> None:
        """Subclass hook: the objective as it stands before a round in the
        current area (the carts at the start, the props in their places)."""

    # ------------------------------------------------------------- teams
    def team_names(self) -> List[str]:
        return ["ffa"] if self.FFA else list(self.TEAMS)

    def team_name(self, team: str) -> str:
        return self.TEAM_NAMES.get(team, team.title())

    # ------------------------------------------------------------- areas
    @property
    def area(self) -> Dict[str, Any]:
        return self.areas[self.area_id]

    def area_extra(self, key: str, default: Any = None) -> Any:
        return (self.area.get("extra") or {}).get(key, default)

    def map_payload(self, player: Optional[Player] = None) -> Dict[str, Any]:
        cached = self._payloads.get(self.area_id)
        if cached is None:
            cached = arena_kit.area_payload(self.map, self.area_id)
            self.decorate_payload(cached)
            self._payloads[self.area_id] = cached
        return cached

    def decorate_payload(self, payload: Dict[str, Any]) -> None:
        """Subclass hook: anything more the client should know about the
        area than its parts and markers."""

    def _arm_area(self) -> None:
        self.dyn_on = {key: bool(d.get("on", True))
                       for key, d in (self.area.get("dynamic") or {}).items()}
        self._rebuild_dynamic()

    def _next_area(self) -> str:
        options = [a for a in self.area_order if a != self.area_id] or self.area_order
        return self.rng.choice(options)

    def accent(self, area_id: Optional[str] = None) -> str:
        area = self.areas.get(area_id or self.area_id) or {}
        return (area.get("extra") or {}).get("accent", "#ffd27a")

    # ------------------------------------------------- switchable solids
    def set_dynamic(self, key: str, on: bool) -> None:
        if key not in self.dyn_on or self.dyn_on[key] == bool(on):
            return
        self.dyn_on[key] = bool(on)
        self._rebuild_dynamic()
        self.broadcast({"t": "adyn", "on": {key: bool(on)}})
        if on:
            self._settle_on(key)

    def set_dynamic_group(self, group: str, on: bool) -> None:
        self.set_dynamic_keys([key for key, d in (self.area.get("dynamic") or {}).items()
                               if d.get("group") == group], on)

    def set_dynamic_keys(self, keys: Sequence[str], on: bool) -> None:
        """Switch several solids at once (one message, one rebuild)."""
        changed = {}
        for key in keys:
            if key in self.dyn_on and self.dyn_on[key] != bool(on):
                self.dyn_on[key] = bool(on)
                changed[key] = bool(on)
        if changed:
            self._rebuild_dynamic()
            self.broadcast({"t": "adyn", "on": changed})
            for key, value in changed.items():
                if value:
                    self._settle_on(key)

    def _settle_on(self, key: str) -> None:
        """A solid just switched on under somebody's feet (a bridge deck
        coming down at the bank, a floor sliding back): anybody it came up
        through by no more than a step stands on it now, the way walking
        onto it would have put them."""
        boxes = ((self.area.get("dynamic") or {}).get(key) or {}).get("boxes") or []
        if not boxes:
            return
        for player in self.players.values():
            if not player.alive:
                continue
            x, y, z = player.pos
            for lo, hi in boxes:
                if lo[0] < x + 1.5 and hi[0] > x - 1.5 and lo[2] < z + 0.9 and hi[2] > z - 0.9 \
                        and lo[1] < y + 5.0 and hi[1] > y and hi[1] - y <= 2.1:
                    player.pos[1] = hi[1]
                    if player.brain is None:
                        self.correct(player)
                    break

    def _rebuild_dynamic(self) -> None:
        boxes = []
        for key, d in (self.area.get("dynamic") or {}).items():
            if self.dyn_on.get(key):
                for lo, hi in d.get("boxes") or []:
                    boxes.append((list(lo), list(hi)))
        grid: Dict[Tuple[int, int], List[int]] = {}
        for index, (lo, hi) in enumerate(boxes):
            for cx in range(int(math.floor(lo[0] / COLLIDER_CELL)),
                            int(math.floor(hi[0] / COLLIDER_CELL)) + 1):
                for cz in range(int(math.floor(lo[2] / COLLIDER_CELL)),
                                int(math.floor(hi[2] / COLLIDER_CELL)) + 1):
                    grid.setdefault((cx, cz), []).append(index)
        self._dyn_boxes = boxes
        self._dyn_grid = grid

    def _colliders_near(self, lo, hi):
        out = super()._colliders_near(lo, hi)
        if not self._dyn_boxes:
            return out
        seen = set()
        extra = []
        for cx in range(int(math.floor(lo[0] / COLLIDER_CELL)),
                        int(math.floor(hi[0] / COLLIDER_CELL)) + 1):
            for cz in range(int(math.floor(lo[2] / COLLIDER_CELL)),
                            int(math.floor(hi[2] / COLLIDER_CELL)) + 1):
                for index in self._dyn_grid.get((cx, cz), ()):
                    if index not in seen:
                        seen.add(index)
                        extra.append(self._dyn_boxes[index])
        return out + extra if extra else out

    # =========================================================== players
    def pick_team(self, player: Player) -> str:
        if self.FFA:
            return "ffa"
        return super().pick_team(player)

    def in_play(self, player: Player) -> bool:
        """Alive, in the round, and not watching it from the sidelines."""
        return player.alive and not player.extra.get("out")

    def playing(self) -> List[Player]:
        return [p for p in self.players.values() if self.in_play(p)]

    def humans_here(self) -> bool:
        return any(p.brain is None for p in self.players.values())

    def spawn_stage(self, team: str) -> int:
        """Subclass hook: which of the team's spawn stages it comes back at."""
        return 0

    def spawn_points(self, team: str) -> List[Dict[str, Any]]:
        spawns = self.area.get("spawns") or {}
        key = team if team in spawns else ("all" if "all" in spawns else
                                           (next(iter(spawns)) if spawns else ""))
        points = list(spawns.get(key) or [])
        if not points:
            return super().spawn_points(team)
        stage = self.spawn_stage(team)
        staged = [p for p in points if int(p.get("stage", 0)) == stage]
        return staged or [p for p in points if int(p.get("stage", 0)) == 0] or points

    def spawn_player(self, player: Player) -> None:
        late = self.ELIMINATION and self.phase == "active" and \
            not player.extra.get("in_round")
        if late or player.extra.get("out"):
            self.park(player)
            return
        player.extra["in_round"] = True
        super().spawn_player(player)
        self.on_spawned(player)
        self._send_me(player, force=True)

    def on_spawned(self, player: Player) -> None:
        """Subclass hook: a player just came into the area (a round start or
        a respawn)."""

    def park(self, player: Player) -> None:
        """Out of the round: dead, invisible and unhittable, watching."""
        player.extra["out"] = True
        player.alive = False
        player.health = 0
        player.respawn_at = NEVER
        cams = self.area.get("cameras") or []
        if cams:
            player.pos = list(cams[0]["p"])
        else:
            c = self.area["centre"]
            player.pos = [c[0], 40.0, c[2]]
        player.vel = [0.0, 0.0, 0.0]
        player.send({"t": "died", "in": -1, "by": "", "spectate": True})
        self._send_me(player, force=True)

    def reset_player(self, player: Player) -> None:
        """Subclass hook: clear a player's per-round state."""

    def respawn_for_round(self, player: Player) -> None:
        for key in ("out", "in_round", "using", "watching"):
            player.extra.pop(key, None)
        self.reset_player(player)
        if player.extra.get("loadout") is not None:
            self.set_loadout(player, None, quiet=True)
        self.spawn_player(player)
        if player.brain is not None:
            player.brain.on_spawn()

    def on_player_join(self, player: Player) -> None:
        """Subclass hook (the base one does nothing either)."""

    def on_player_ready(self, player: Player) -> None:
        area = self.area
        player.send({"t": "aarea", "area": self.area_id, "name": area["name"],
                     "round": self.round_number, "area_round": self.area_round + 1,
                     "rounds": self.ROUNDS_PER_AREA, "intro": False, "join": True,
                     "logo": self.LOGO or self.world["name"], "accent": self.accent(),
                     "phase": self.phase, "left": round(max(0.0, self.phase_until -
                                                            engine.now()), 1)})
        # everybody else's kit, as anyone may see it
        for other in self.players.values():
            if other is not player and other.extra.get("loadout") is not None:
                player.send({"t": "aload", "id": other.pid,
                             "hotbar": other.extra.get("public_loadout",
                                                       other.extra.get("loadout"))})
        for line in self.welcome_lines(player):
            player.send({"t": "chat", "kind": "system", "from": "", "id": 0,
                         "m": line, "at": time.time()})
        if player.extra.get("out"):
            # joined a round already under way: they watch it (said again
            # now the client has its world, since the spawn came first)
            player.send({"t": "died", "in": -1, "by": "", "spectate": True})
        self._send_me(player, force=True)

    def welcome_lines(self, player: Player) -> List[str]:
        """Subclass hook: the chat lines a joining player is greeted with."""
        return ["%s -- %s." % (self.world["name"], self.area["name"])]

    # ------------------------------------------------------------ loadouts
    def set_loadout(self, player: Player, items: Optional[Sequence[Any]],
                    public: Optional[Sequence[Any]] = None, quiet: bool = False) -> None:
        """Give ``player`` the world's own kit (``None`` hands back their
        own).  ``public`` is what everybody else is told they carry, where
        that is a secret (a culprit's knife)."""
        if items is None:
            player.extra.pop("loadout", None)
            player.extra.pop("public_loadout", None)
        else:
            slots = list(items)[:catalog.HOTBAR_SIZE]
            slots += [None] * (catalog.HOTBAR_SIZE - len(slots))
            player.extra["loadout"] = slots
            if public is not None:
                shown = list(public)[:catalog.HOTBAR_SIZE]
                shown += [None] * (catalog.HOTBAR_SIZE - len(shown))
                player.extra["public_loadout"] = shown
            else:
                player.extra.pop("public_loadout", None)
        first = next((i for i in range(catalog.HOTBAR_SIZE) if player.weapon(i)), 0)
        player.slot = first
        player.stowed = player.weapon(first) is None
        player.reset_ammo()
        player.reload_until = 0.0
        mine = player.extra.get("loadout")
        player.send({"t": "aload", "id": player.pid, "hotbar": mine, "you": 1,
                     "slot": player.slot, "quiet": bool(quiet)})
        shown = player.extra.get("public_loadout", mine)
        self.broadcast({"t": "aload", "id": player.pid, "hotbar": shown},
                       exclude=player.pid)
        self.broadcast({"t": "slot", "id": player.pid,
                        "i": STOW_SLOT if player.stowed else player.slot},
                       exclude=player.pid)

    @staticmethod
    def item(item_id: str, name: str, stats: Dict[str, Any],
             parts: Sequence[Dict[str, Any]], **data: Any) -> Dict[str, Any]:
        """A hotbar entry for a world's own kit, in the avatar's format."""
        body = {"stats": dict(stats), "parts": [dict(p) for p in parts]}
        body.update(data)
        return {"inv_id": 0, "item_id": item_id, "name": name, "slot": "usable",
                "tier": "normal", "data": body}

    # ================================================================ input
    def max_speed(self, player: Player) -> float:
        return super().max_speed(player) * max(0.05, self.move_scale(player))

    def move_scale(self, player: Player) -> float:
        """Subclass hook: how fast this player may move (1 = normal)."""
        return 1.0

    def can_jump(self, player: Player) -> bool:
        return not self.held_still(player)

    def held_still(self, player: Player) -> bool:
        """Subclass hook: a player who may not move at all right now.  By
        default, everybody through the countdown of a world that freezes it
        (``FREEZE_COUNTDOWN``): they look about from their spawn, and go at
        GO.  The client is told (``held`` in the per-player state) and stops
        its own body; a bot's brain stops its own."""
        return self.FREEZE_COUNTDOWN and self.phase == "setup" and self.in_play(player)

    def handle_input(self, player: Player, message: Dict[str, Any]) -> None:
        if self.held_still(player):
            with self.lock:
                try:
                    player.yaw = float(message.get("y", player.yaw))
                    player.pitch = float(message.get("pi", player.pitch))
                except (TypeError, ValueError):
                    pass
                moment = engine.now()
                pos = message.get("p")
                if isinstance(pos, list) and len(pos) == 3:
                    try:
                        moved = math.dist([float(v) for v in pos], player.pos)
                    except (TypeError, ValueError):
                        moved = 0.0
                    if moved > 1.0 and moment - player.extra.get("held_corrected", 0) > 0.4:
                        player.extra["held_corrected"] = moment
                        self.correct(player)
            return
        super().handle_input(player, message)

    def can_fire(self, player: Player) -> bool:
        if not self.in_play(player):
            return False
        if self.phase == "active":
            return True
        return self.phase == "setup" and self.WARMUP_FIRE

    def handle_fire(self, player: Player, message: Dict[str, Any]) -> None:
        with self.lock:
            if not self.can_fire(player) or player.stowed:
                return
            stats = player.weapon_stats()
            if stats.get("kind") in self.CUSTOM_KINDS:
                # the world's own kind of weapon: the same rate limit and
                # aim checks the engine applies, then the world's own rules
                moment = engine.now()
                if moment < player.next_fire or moment < player.reload_until:
                    return
                rpm = float(stats.get("rpm", 120) or 120)
                direction = message.get("d")
                if not (isinstance(direction, list) and len(direction) == 3):
                    return
                try:
                    direction = normalise([float(v) for v in direction])
                except (TypeError, ValueError):
                    return
                player.next_fire = moment + max(0.03, 60.0 / max(1.0, rpm))
                origin = [player.pos[0], player.pos[1] + EYE_HEIGHT, player.pos[2]]
                self.custom_fire(player, stats, direction, origin)
                return
        super().handle_fire(player, message)

    def custom_fire(self, player: Player, stats: Dict[str, Any],
                    direction: List[float], origin: List[float]) -> None:
        """Subclass hook: a world's own kind of weapon was fired."""

    def on_action(self, player: Player, message: Dict[str, Any]) -> None:
        kind = message.get("k")
        if kind == "use":
            player.extra["using"] = True
            self.use(player, message)
        elif kind == "unuse":
            player.extra.pop("using", None)
            self.unuse(player)
        elif kind == "watch":
            try:
                player.extra["watching"] = max(0, int(message.get("id") or 0))
            except (TypeError, ValueError):
                player.extra["watching"] = 0
        else:
            self.world_action(player, kind, message)

    def use(self, player: Player, message: Dict[str, Any]) -> None:
        """Subclass hook: E (or right mouse with nothing to scope) pressed."""

    def unuse(self, player: Player) -> None:
        """Subclass hook: E let go."""

    def world_action(self, player: Player, kind: Any, message: Dict[str, Any]) -> None:
        """Subclass hook: any other action the world's client sends."""

    # ============================================================ hitting
    def can_hurt(self, attacker: Player, victim: Player) -> bool:
        """May ``attacker`` hurt ``victim`` right now?"""
        if self.phase != "active" or attacker is victim:
            return False
        if not self.in_play(victim) or not self.in_play(attacker):
            return False
        return self.FFA or attacker.team != victim.team or self.friendly_fire

    def scale_damage(self, victim: Player, attacker: Optional[Player], amount: float,
                     weapon: str, headshot: bool) -> float:
        """Subclass hook: change (or cancel, with 0) a hit before it lands."""
        return amount

    def apply_damage(self, victim, attacker, amount: float, weapon_name: str,
                     headshot: bool = False) -> None:
        if isinstance(victim, Minion):
            super().apply_damage(victim, attacker, amount, weapon_name, headshot)
            return
        if not isinstance(victim, Player):
            self.hit_thing(victim, attacker, amount, weapon_name, headshot)
            return
        if isinstance(attacker, Player) and attacker is not victim and \
                not self.can_hurt(attacker, victim):
            return
        amount = self.scale_damage(victim, attacker, amount, weapon_name, headshot)
        if amount <= 0:
            return
        super().apply_damage(victim, attacker, amount, weapon_name, headshot)

    def hit_thing(self, thing, attacker, amount: float, weapon: str, headshot: bool) -> None:
        """Subclass hook: something that is not a player was hit."""

    def hostiles_for(self, player: Player):
        """What a bot here fights: whoever it may hurt."""
        if not self.in_play(player):
            return
        for other in self.players.values():
            if other is not player and self.in_play(other) and self.can_hurt(player, other):
                yield other

    def kill(self, victim, killer, weapon_name: str, headshot: bool = False) -> None:
        if not isinstance(victim, Player):
            return
        if not victim.alive:
            return
        super().kill(victim, killer, weapon_name, headshot)
        if self.ELIMINATION and self.phase == "active":
            victim.respawn_at = NEVER
            victim.extra["out"] = True
        self.after_kill(killer if isinstance(killer, Player) else None, victim, weapon_name)
        self._send_me(victim, force=True)

    def after_kill(self, killer: Optional[Player], victim: Player, weapon: str) -> None:
        """Subclass hook: somebody went down (the kill feed is already out)."""

    # ============================================================== rounds
    def go_live(self) -> None:
        moment = engine.now()
        self.phase = "active"
        self.live_since = moment
        self.round_ends = moment + self.ROUND_SECONDS if self.ROUND_SECONDS else 0.0
        self.broadcast({"t": "aphase", "phase": "active", "round": self.round_number,
                        "left": self.ROUND_SECONDS})
        self.on_live()
        self.broadcast({"t": "state", "s": self.full_state()})

    def on_live(self) -> None:
        """Subclass hook: the countdown is over and the round is on."""

    def time_up(self) -> None:
        """The clock ran out: by default the leader takes it."""
        self.finish_round(self.leader(), "time")

    def leader(self) -> str:
        """Subclass hook: who is ahead (a team, or in a free-for-all a
        player's name), "" for nobody."""
        return ""

    def finish_round(self, winner: str, reason: str = "", headline: str = "",
                     winner_name: str = "") -> None:
        """The round is over: the card, the reports, and where next."""
        if self.phase != "active":
            return
        moment = engine.now()
        self.phase = "intermission"
        self.phase_until = moment + self.RESULTS_SECONDS
        self.area_round += 1
        shuffle = self.area_round >= self.ROUNDS_PER_AREA
        nxt = self._next_area() if shuffle else self.area_id
        self._next_area_id = nxt
        self._shuffle_next = shuffle
        if winner and not self.FFA:
            self.wins[winner] = self.wins.get(winner, 0) + 1
        winners = [p for p in self.players.values() if self.player_won(p, winner)]
        for player in self.players.values():
            won = player in winners
            if won:
                player.score += 25
            self.host.report_round(self, player, won=won)
        self.on_round_over(winner, reason, winners)
        rows = self.results_rows()
        name = winner_name or (self.team_name(winner) if winner and not self.FFA else winner)
        card = {"t": "aend", "winner": winner, "winner_name": name,
                "reason": reason, "headline": headline or self.headline(winner, reason),
                "rows": rows[:24], "columns": self.result_columns(),
                "area": self.area["name"], "area_id": self.area_id,
                "next": self.areas[nxt]["name"], "next_id": nxt, "shuffle": shuffle,
                "in": self.RESULTS_SECONDS, "round": self.round_number,
                "area_round": self.area_round, "rounds": self.ROUNDS_PER_AREA,
                "logo": self.LOGO or self.world["name"],
                "awards": self.awards(winner),
                "reel": [{"id": a, "name": self.areas[a]["name"],
                          "accent": self.accent(a)} for a in self.area_order]}
        card.update(self.result_extra(winner))
        self.results = card
        self.broadcast(card)
        if shuffle:
            self.system_message("Round over -- %s. The server moves on to %s!"
                                % (card["headline"], self.areas[nxt]["name"]))
        else:
            self.system_message("Round over -- %s. Round %d of %d at %s is next."
                                % (card["headline"], self.area_round + 1,
                                   self.ROUNDS_PER_AREA, self.area["name"]))
        if self.bots is not None:
            self.bots.on_round_end(winner if not self.FFA else name, reason)

    def player_won(self, player: Player, winner: str) -> bool:
        if not winner:
            return False
        if self.FFA:
            return player.username == winner
        return player.team == winner

    def headline(self, winner: str, reason: str) -> str:
        if not winner:
            return "nobody wins"
        if self.FFA:
            return "%s wins" % winner
        return "%s win" % self.team_name(winner)

    def on_round_over(self, winner: str, reason: str, winners: List[Player]) -> None:
        """Subclass hook: badges and anything else to book at the end."""

    def results_rows(self) -> List[Dict[str, Any]]:
        """Subclass hook: one row per player for the card, best first."""
        rows = [{"id": p.pid, "name": p.username, "team": p.team, "score": p.score,
                 "kills": p.kills, "deaths": p.deaths} for p in self.players.values()]
        rows.sort(key=lambda r: (-r["score"], r["name"].lower()))
        return rows

    def result_columns(self) -> List[List[str]]:
        """[field, heading] pairs the card's table shows."""
        return [["kills", "Kills"], ["deaths", "Deaths"], ["score", "Score"]]

    def awards(self, winner: str) -> List[str]:
        """Subclass hook: a few lines of who did what this round."""
        return []

    def result_extra(self, winner: str) -> Dict[str, Any]:
        return {}

    def next_round(self) -> None:
        self.start_round(self._next_area_id if self._shuffle_next else self.area_id)

    def assign_teams(self, moved: bool) -> None:
        """Even the teams out between rounds: the bots move first, then
        whoever has been on the bigger side the shortest time."""
        if self.FFA or not self.BALANCE or len(self.TEAMS) < 2:
            return
        for _ in range(len(self.players)):
            counts = {t: 0 for t in self.TEAMS}
            for p in self.players.values():
                if p.team in counts:
                    counts[p.team] += 1
            big = max(counts, key=counts.get)
            small = min(counts, key=counts.get)
            if counts[big] - counts[small] <= 1:
                return
            movers = sorted((p for p in self.players.values() if p.team == big),
                            key=lambda p: (p.brain is None, -p.joined_at))
            if not movers:
                return
            mover = movers[0]
            mover.team = small
            mover.send({"t": "team", "team": small})
            self.broadcast({"t": "teams", "map": {mover.pid: small}})

    def start_round(self, area_id: Optional[str] = None) -> None:
        moment = engine.now()
        previous = self.area_id
        self.area_id = area_id if area_id in self.areas else self.area_id
        moved = self.area_id != previous or self._first_round
        self._first_round = False
        if moved:
            self.area_round = 0
            self._arm_area()
        self._next_area_id = None
        self._shuffle_next = False
        self.round_number += 1
        self.phase = "setup"
        self.phase_until = moment + (self.INTRO_SECONDS if moved else 0.0) + self.SETUP_SECONDS
        self.round_started = moment
        self.round_ends = 0.0
        self.projectiles.clear()
        self.gear.reset()
        self.results = {}
        self.assign_teams(moved)
        self.round_setup()
        payload = {"t": "aarea", "area": self.area_id, "name": self.area["name"],
                   "round": self.round_number, "area_round": self.area_round + 1,
                   "rounds": self.ROUNDS_PER_AREA, "intro": moved,
                   "logo": self.LOGO or self.world["name"], "accent": self.accent(),
                   "phase": "setup", "left": round(self.phase_until - moment, 1)}
        if moved:
            payload["map"] = self.map_payload()
        for player in list(self.players.values()):
            player.kills = 0
            player.deaths = 0
            player.send(payload)
            self.respawn_for_round(player)
        self.broadcast({"t": "round_start", "round": self.round_number,
                        "state": self.full_state()})
        if moved:
            self.system_message("Round %d: %s. Get ready!" % (self.round_number,
                                                              self.area["name"]))
        else:
            self.system_message("Round %d: %s again (%d of %d here)."
                                % (self.round_number, self.area["name"],
                                   self.area_round + 1, self.ROUNDS_PER_AREA))
        self.push_event("arena_area", what=self.area["name"], n=self.area_round + 1,
                        retry=not moved)
        if self.bots is not None:
            self.bots.on_round_start()

    # ================================================================ tick
    def hold(self, dt: float) -> None:
        """Nobody real here: every timer waits for them."""
        self.phase_until += dt
        if self.round_ends:
            self.round_ends += dt
        self.live_since += dt
        for name in self.HELD_TIMERS:
            value = getattr(self, name, None)
            if isinstance(value, (int, float)) and value:
                setattr(self, name, value + dt)
        self.on_hold(dt)

    def on_hold(self, dt: float) -> None:
        """Subclass hook: hold anything else that runs on the clock."""

    def on_tick(self, dt: float) -> None:
        if not self.humans_here():
            self.hold(dt)
            return
        moment = engine.now()
        if self.phase == "setup":
            self.setup_tick(dt, moment)
            if moment >= self.phase_until:
                self.go_live()
        elif self.phase == "active":
            self.round_tick(dt, moment)
            if self.phase == "active" and self.round_ends and moment >= self.round_ends:
                self.time_up()
        elif self.phase == "intermission":
            self.intermission_tick(dt, moment)
            if moment >= self.phase_until:
                self.next_round()
        self._me_tick += 1
        if self._me_tick % 5 == 0:
            for player in list(self.players.values()):
                self._send_me(player)

    def setup_tick(self, dt: float, moment: float) -> None:
        """Subclass hook: every tick of the countdown."""

    def round_tick(self, dt: float, moment: float) -> None:
        """Subclass hook: every tick of the round; call finish_round to end it."""

    def intermission_tick(self, dt: float, moment: float) -> None:
        """Subclass hook: every tick of the results card."""

    def _tick_phase(self, moment: float) -> None:
        """The engine's own end-of-round vote does not apply here."""

    # ============================================================== state
    def me_state(self, player: Player) -> Dict[str, Any]:
        """Subclass hook: this player's own state, beyond the basics."""
        return {}

    def _send_me(self, player: Player, force: bool = False) -> None:
        if player.ws is None:
            return
        me = {"team": player.team, "out": bool(player.extra.get("out")),
              "role": player.extra.get("role", ""), "held": bool(self.held_still(player))}
        me.update(self.me_state(player))
        if not force and me == player.extra.get("_ame"):
            return
        player.extra["_ame"] = me
        payload = {"t": "ame"}
        payload.update(me)
        player.send(payload)

    def hud_state(self) -> Dict[str, Any]:
        """Subclass hook: what the HUD shows (scores, bars, objective)."""
        return {}

    def round_state(self) -> Dict[str, Any]:
        moment = engine.now()
        state = {
            "arena": 1, "area": self.area_id, "area_name": self.area["name"],
            "aphase": self.phase,
            "phase_left": round(max(0.0, self.phase_until - moment), 1),
            "time_left": round(max(0.0, self.round_ends - moment), 1)
            if self.phase == "active" and self.round_ends else
            (self.ROUND_SECONDS if self.phase == "setup" else 0.0),
            "round_n": self.round_number, "area_round": self.area_round + 1,
            "rounds_per_area": self.ROUNDS_PER_AREA, "dyn": dict(self.dyn_on),
            "wins": dict(self.wins), "ffa": self.FFA,
            "out": [p.pid for p in self.players.values() if p.extra.get("out")],
        }
        state.update(self.hud_state())
        return state

    def score_row(self, player: Player, row: Dict[str, Any]) -> None:
        """Subclass hook: the world's own scoreboard columns."""

    def scoreboard(self) -> List[Dict[str, Any]]:
        rows = super().scoreboard()
        for row in rows:
            player = self.players.get(row["id"])
            if player is None:
                continue
            row["out"] = bool(player.extra.get("out"))
            row["alive"] = bool(player.alive)
            row["role"] = player.extra.get("role", "")
            self.score_row(player, row)
        return rows

    def snapshot(self) -> Dict[str, Any]:
        payload = super().snapshot()
        extra = self.snapshot_extra()
        if extra:
            payload["ax"] = extra
        return payload

    def snapshot_extra(self) -> Any:
        """Subclass hook: moving things (a cart, a ball) every tick."""
        return None

    def describe(self) -> Dict[str, Any]:
        info = super().describe()
        info["summary"] = "Round %d · %s" % (max(1, self.round_number), self.area["name"])
        return info

    # ======================================================== sleep / wake
    def sleep_state(self) -> Dict[str, Any]:
        moment = engine.now()
        state = {"area": self.area_id, "area_round": self.area_round,
                 "between": self.phase != "active", "wins": dict(self.wins),
                 "time_left": max(0.0, self.round_ends - moment)
                 if self.phase == "active" and self.round_ends else self.ROUND_SECONDS}
        state.update(self.sleep_extra())
        return state

    def sleep_extra(self) -> Dict[str, Any]:
        """Subclass hook: the objective's state, for the sleeping round."""
        return {}

    def resume(self, state: Dict[str, Any]) -> None:
        """Pick a sleeping round back up: the same area, and the round as
        far on as it had got (or the next one, between rounds)."""
        area = state.get("area")
        if area not in self.areas:
            area = self.rng.choice(self.area_order)
        self.wins = {str(k): int(v) for k, v in (state.get("wins") or {}).items()}
        self.round_number = max(0, int(state.get("round", 1) or 1) - 1)
        self._first_round = True
        self.start_round(area)
        self.area_round = max(0, min(self.ROUNDS_PER_AREA - 1,
                                     int(state.get("area_round", 0) or 0)))
        if not state.get("between") and state.get("phase", "active") == "active":
            left = float(state.get("time_left", self.ROUND_SECONDS) or self.ROUND_SECONDS)
            # straight into the round, a woken one has no countdown
            self.go_live()
            if self.ROUND_SECONDS:
                self.round_ends = engine.now() + max(30.0, min(self.ROUND_SECONDS, left))
            progress = float(state.get("progress", 0.0) or 0.0)
            self.resume_progress(max(0.0, min(0.95, progress)), state)

    def resume_progress(self, progress: float, state: Dict[str, Any]) -> None:
        """Subclass hook: a woken round is ``progress`` of the way through
        -- set the objective to match (carts part-way up the track)."""

    # ================================================================ bots
    def attention_points(self) -> List[List[float]]:
        """Where somebody real is looking: their own position, or whoever a
        spectating person is watching."""
        out = []
        for player in self.players.values():
            if player.brain is not None:
                continue
            if player.alive:
                out.append(list(player.pos))
            watching = self.players.get(int(player.extra.get("watching", 0) or 0))
            if watching is not None:
                out.append(list(watching.pos))
        return out

    def bot_tick(self, moment: float) -> None:
        """Subclass hook: once a tick, before the bots think."""

    def bot_role(self, brain) -> str:
        return "player"

    def aim_heights(self, target) -> Optional[Tuple[float, float]]:
        """Subclass hook: where on ``target`` a bot aims (body, head) above
        its feet, when that is not a person's chest and head."""
        return None

    def bot_goal_weights(self, brain, weights: Dict[str, float]) -> Dict[str, float]:
        return weights

    def bot_push(self, player: Player) -> Optional[Tuple[float, float]]:
        """Subclass hook: a horizontal drift (vx, vz) the world puts on a
        bot's body this tick -- the gale or the current a person feels as
        a ``knock`` -- or None."""
        return None

    def bot_gravity(self, player: Player) -> float:
        """Subclass hook: how hard gravity pulls on a bot's body this tick
        (1 = normal; a feather that makes a person's browser fall slowly
        makes a bot fall slowly too)."""
        return 1.0

    def bot_urgent(self, brain) -> bool:
        return False

    def bot_objective(self, brain) -> None:
        """Subclass hook: what a bot does about the objective.  The default
        roams the area."""
        if not brain.waypoints:
            spot = self.random_spot(brain.rng)
            if spot is not None:
                brain.go(spot, "roam%d" % int(spot[0] * 7 + spot[2]))

    def random_spot(self, rng, near: Optional[Sequence[float]] = None,
                    radius: Optional[float] = None) -> Optional[List[float]]:
        """A walkable point in the current area (near ``near``, if given)."""
        nav = getattr(self.host, "nav", None)
        if nav is None or not nav.ready:
            return None
        if near is None:
            near = self.area["centre"]
            hx, hz = self.area.get("half") or [200, 200]
            radius = radius or min(hx, hz) * 0.95
        node = nav.random_node(rng, near, radius or 60.0)
        if node < 0:
            return None
        point = nav.point(node)
        rx = self.area["rect"]
        if not (rx[0] <= point[0] <= rx[1] and rx[2] <= point[2] <= rx[3]):
            return None
        return point

    def bot_context(self) -> List[str]:
        """Subclass hook: the round as a bot would describe it to itself."""
        return []

    def bot_game_state(self) -> Dict[str, Any]:
        from ...models import event_worlds
        module = event_worlds.by_id(self.world_id)
        moment = engine.now()
        context = ["You are playing %s, in %s." % (self.world["name"], self.area["name"])]
        if self.phase == "setup":
            context.append("The round is about to start.")
        elif self.phase == "intermission":
            context.append("The round just ended: %s." % (self.results.get("headline") or
                                                         "it is over"))
            if self._shuffle_next and self._next_area_id:
                context.append("The server is moving everybody to %s next."
                               % self.areas[self._next_area_id]["name"])
        context.extend(self.bot_context())
        jobs = []
        if self.bots is not None:
            for brain in list(self.bots.brains.values())[:24]:
                jobs.append({"name": brain.p.username, "team": brain.p.team,
                             "role": getattr(brain, "role", ""),
                             "doing": brain.p.extra.get("bot_doing", "")})
        return {"arena": True, "context": context, "area_name": self.area["name"],
                "summary": self.describe().get("summary", ""), "ffa": self.FFA,
                "team_names": dict(self.TEAM_NAMES),
                "tone": getattr(module, "PROMPT", "") if module else "",
                "time_left": round(max(0.0, self.round_ends - moment))
                if self.phase == "active" and self.round_ends else None,
                "bot_jobs": jobs}

    def bot_me(self, brain) -> Dict[str, Any]:
        """Subclass hook: a bot's own part in the round, as context lines."""
        p = brain.p
        lines = []
        if p.extra.get("out"):
            lines.append("you are out of this round and watching the rest")
        elif not self.FFA and p.team:
            lines.append("you are on %s" % self.team_name(p.team))
        doing = p.extra.get("bot_doing")
        if doing:
            lines.append(str(doing))
        return {"context": lines}

    def bot_spread(self, players: List[Player]) -> None:
        """Subclass hook: place a woken round's bots about the area."""
        for player in players:
            if player.brain is not None:
                player.brain.on_spawn()

    def doing(self, brain, text: str) -> None:
        """Note what a bot is up to (the Bots Zone shows it, and its chat
        knows it)."""
        brain.p.extra["bot_doing"] = text

    def callout(self, brain, lines: Sequence[str], key: str, chance: float = 1.0,
                every: float = 25.0, team: bool = False) -> bool:
        """A bot shouts one of ``lines`` in quick chat ("run!", "evac's
        clear") when the world's ``callouts`` setting is on and the people
        playing have quick reactions on.  ``key`` keeps one bot from saying
        the same sort of thing twice inside ``every`` seconds; chatty
        personas shout more, and the runner caps quick chat per minute."""
        setting = getattr(self, "setting", None)
        if setting is not None and not setting("callouts"):
            return False
        runner = brain.runner
        cfg = runner.cfg
        if not runner.humans or not lines or \
                not cfg.get("messages_quick_reactions", True) or \
                not cfg.get("messages_ingame_chat", True):
            return False
        moment = engine.now()
        said = brain.p.extra.setdefault("callouts", {})
        if moment - said.get(key, -999.0) < every:
            return False
        if brain.rng.random() > chance * (0.3 + brain.t("chatty", 0.4)):
            return False
        said[key] = moment
        from ..bots.brain import styled
        text = styled(brain.rng.choice(list(lines)), brain.traits, brain.rng)
        runner.queue_chat(brain, text, brain.rng.uniform(0.4, 1.8), quick=True,
                          team=team and bool(brain.p.team))
        return True


def ffa_leader(players: Iterable[Player], key) -> str:
    """The name of whoever is ahead by ``key``, "" if nobody is."""
    best, best_v = "", None
    for p in players:
        v = key(p)
        if best_v is None or v > best_v:
            best, best_v = p.username, v
    return best if best_v else ""
