"""Blackout Relay -- capture the flag on Ironvale Relay.

Same flags, same three captures, four rules of its own:

**Muster waves.**  Both teams deploy out of the Relay in the middle of the
map, and the dead come back in waves rather than one at a time, so a team
arrives together instead of trickling into the same corner one body at a
time.  It is the single biggest difference between a round that feels like a
push and a round that feels like a queue.

**Outpost lockdown.**  While your own flag is off its pedestal, your team
stops spawning at the Relay and starts spawning in the two bunkers on your
half -- which is exactly where a carrier running for home has to come past.
Losing your flag never buries you; it moves you into the way.  The counter is
just as clear: take the bunkers before you take the flag.

**Overtime.**  The clock cannot end a round while a flag is away from home.
A grab in the last ten seconds is a real grab.

**Sudden death.**  Level when the clock finally stops, both flags reset and
the next capture wins it.

**The rotation.**  Ironvale is one map of several (app/game/maps/relay/):
when a round ends the server rolls one of the others at random, says where
it is going, and moves everybody there for the next round -- each map with
its own arrival sequence, its own relay, flags and outposts, and its own
length (Ironvale's long valley keeps its five captures and half an hour; the
rest are first to three in fifteen minutes).  A client is only ever sent the
map being played.

Everything else -- the flags themselves, pickups, returns, the shuffle vote
-- is inherited from :class:`CaptureTheFlag` unchanged.
"""
from __future__ import annotations

import math
import os
import random
import time
from typing import Any, Dict, List, Optional

from ..instance import Player, now
from ..maps import relay as relay_maps
from .capture_the_flag import CaptureTheFlag, Flag

WAVE_SECONDS = 5.0          # deploy every five seconds...
MIN_RESPAWN = 2.0           # ...but never inside two of dying
SUDDEN_DEATH_SECONDS = 180.0
ESCORT_RADIUS = 30.0        # how close is "escorting the carrier"
ESCORT_EVERY = 40           # ticks between escort payouts (two seconds)
ESCORT_POINTS = 2
DEFENCE_RADIUS = 60.0       # a kill this close to your own flag is a defence
DEFENCE_POINTS = 5


class BlackoutRelay(CaptureTheFlag):
    mode = "captures"
    friendly_fire = False

    captures_to_win = 5
    round_seconds = 1800.0     # half an hour: the map is long and so is a run
    flag_return_seconds = 45.0
    pickup_radius = 9.0       # the whole top of the pedestal counts
    capture_radius = 15.0

    wave_seconds = WAVE_SECONDS
    min_respawn = MIN_RESPAWN
    wave_origin = 0.0

    @staticmethod
    def build_map() -> Dict[str, Any]:
        return relay_maps.build()

    # ------------------------------------------------------------- lifecycle
    def setup(self) -> None:
        markers = self.map.get("markers", {})
        self.areas: Dict[str, Dict[str, Any]] = {
            a["id"]: a for a in markers.get("areas") or []}
        self.area_order = [a["id"] for a in markers.get("areas") or []]
        self.rng = random.Random()
        self._payloads: Dict[str, Dict[str, Any]] = {}
        self.area_id = self._first_area()
        self.next_area_id = ""
        self.captures = {"red": 0, "blue": 0}
        self.flags: Dict[str, Flag] = {}
        self.outposts: Dict[str, List[Dict[str, Any]]] = {}
        self._arm_area()
        self.round_ends = now() + self.round_seconds
        self.phase = "active"
        self.lockdown = {team: False for team in self.team_names()}
        self.overtime = False
        self.sudden_death = False
        self.sudden_death_ends = 0.0
        self.wave_origin = now()

    # ------------------------------------------------------------ the maps
    def _first_area(self) -> str:
        """Where a new server opens: anywhere in the rotation (or the map
        named by ``BLOCKHAVEN_RELAY_MAP``, which the tests use)."""
        forced = os.environ.get("BLOCKHAVEN_RELAY_MAP", "")
        if forced in self.areas:
            return forced
        return self.rng.choice(self.area_order) if self.area_order else ""

    @property
    def area(self) -> Dict[str, Any]:
        return self.areas[self.area_id]

    def area_markers(self) -> Dict[str, Any]:
        return self.area.get("markers") or {}

    def _arm_area(self) -> None:
        """The flags on their pedestals, the outposts and the round's length,
        as the current map has them."""
        markers = self.area_markers()
        self.flags = {team: Flag(team, list((markers.get("flag_%s" % team) or
                                             {"p": [0, 6, 0]})["p"]))
                      for team in self.team_names()}
        self.outposts = {team: list(markers.get("outpost_%s" % team) or [])
                         for team in self.team_names()}
        self.captures_to_win = int(markers.get("captures_to_win") or
                                   type(self).captures_to_win)
        self.round_seconds = float(markers.get("round_seconds") or
                                   type(self).round_seconds)

    def map_payload(self, player: Optional[Player] = None) -> Dict[str, Any]:
        cached = self._payloads.get(self.area_id)
        if cached is None:
            cached = relay_maps.area_payload(self.map, self.area_id)
            self._payloads[self.area_id] = cached
        return cached

    def flag_field(self, team: str) -> str:
        """The name of the bots' flow field to ``team``'s flag: one per map,
        since every map puts its flags somewhere else."""
        return "flag_%s@%s" % (team, self.area_id)

    def roll_next_area(self) -> str:
        """The next map, at random, never the one just played."""
        options = [a for a in self.area_order if a != self.area_id] or self.area_order
        return self.rng.choice(options)

    def reel(self) -> List[Dict[str, Any]]:
        return [{"id": a, "name": self.areas[a]["name"],
                 "accent": (self.areas[a].get("extra") or {}).get("accent", "#ffd27a")}
                for a in self.area_order]

    def move_to(self, area_id: str) -> bool:
        """Everybody to ``area_id`` (between rounds): the map, its arrival
        sequence and its flags.  The respawn that follows puts them in it."""
        if area_id not in self.areas:
            return False
        moved = area_id != self.area_id
        self.area_id = area_id
        self._arm_area()
        if not moved:
            return False
        markers = self.area_markers()
        payload = {"t": "brarea", "area": area_id, "name": self.area["name"],
                   "map": self.map_payload(), "round": self.round_number + 1,
                   "target": self.captures_to_win,
                   "minutes": int(round(self.round_seconds / 60.0)),
                   "accent": (self.area.get("extra") or {}).get("accent", "#ffd27a"),
                   "intro": True}
        for player in list(self.players.values()):
            player.send(payload)
            if player.brain is not None:
                player.brain.waypoints = []
                player.brain.dest_key = ""
        self.push_event("relay_area", what=self.area["name"])
        del markers
        return True

    def resume_area(self, area_id: Optional[str]) -> None:
        """A sleeping round wakes on the map it had got to: its flags, and
        everybody already seated put down at its musters."""
        if area_id in self.areas and area_id != self.area_id:
            self.area_id = area_id
            self._arm_area()
            for player in list(self.players.values()):
                self.spawn_player(player)
                if player.brain is not None:
                    player.brain.on_spawn()

    def describe(self) -> Dict[str, Any]:
        info = super().describe()
        info["summary"] = "%s · %d-%d" % (self.area["name"], self.captures.get("red", 0),
                                          self.captures.get("blue", 0))
        return info

    def on_player_ready(self, player: Player) -> None:
        super().on_player_ready(player)
        lines = list(self.area_markers().get("intro") or [])
        if self.area_id != "ironvale":
            lines.append("First to %d captures, %d minutes on the clock -- then the "
                         "server rolls the next map." % (self.captures_to_win,
                                                         int(self.round_seconds // 60)))
        for line in lines:
            player.send({"t": "chat", "kind": "system", "from": "", "id": 0,
                         "m": line, "at": time.time()})

    # -------------------------------------------------------------- respawn
    @property
    def respawn_seconds(self) -> float:
        """Time until the next deploy wave, never less than ``min_respawn``.

        The base class reads this the moment somebody dies and both starts
        their timer and tells their client the countdown with it, so a
        computed value here is all a wave needs -- there is no second clock
        to keep in step.
        """
        elapsed = now() - self.wave_origin
        remaining = self.wave_seconds - (elapsed % self.wave_seconds)
        if remaining < self.min_respawn:
            remaining += self.wave_seconds
        return round(remaining, 2)

    def spawn_points(self, team: str) -> List[Dict[str, Any]]:
        """Muster at the relay, or fall back to the outposts under lockdown."""
        flag = self.flags.get(team)
        if flag is not None and flag.state != "home":
            forward = self.outposts.get(team)
            if forward:
                return list(forward)
        spawns = (self.area.get("spawns") or {}).get(team) or []
        return list(spawns) or super().spawn_points(team)

    # ----------------------------------------------------------------- flow
    def round_state(self) -> Dict[str, Any]:
        state = super().round_state()
        if self.sudden_death:
            state["time_left"] = max(0, int(self.sudden_death_ends - now()))
        state.update({
            "overtime": self.overtime,
            "sudden_death": self.sudden_death,
            "lockdown": dict(self.lockdown),
            "wave": self.wave_seconds,
            "area": self.area_id,
            "area_name": self.area["name"],
            "next_area": self.next_area_id,
        })
        return state

    def on_tick(self, dt: float) -> None:
        super().on_tick(dt)
        if self.phase != "active":
            return
        self.update_lockdown()
        if self.tick_count % ESCORT_EVERY == 0:
            self.pay_escorts()

    def update_lockdown(self) -> None:
        for team, flag in self.flags.items():
            locked = flag.state != "home"
            if locked == self.lockdown.get(team):
                continue
            self.lockdown[team] = locked
            self.push_event("lockdown", team=team, on=locked)
            if locked:
                self.broadcast({"t": "chat", "kind": "system", "from": "",
                                "id": 0, "at": time.time(),
                                "m": "%s falls back to the bunkers -- cut the "
                                     "carrier off!" % team.upper()})
            else:
                self.broadcast({"t": "chat", "kind": "system", "from": "",
                                "id": 0, "at": time.time(),
                                "m": "%s is mustering at the Relay again."
                                     % team.upper()})

    def pay_escorts(self) -> None:
        """Points for staying with the flag runner, not just for the runner."""
        for flag in self.flags.values():
            if flag.state != "carried":
                continue
            carrier = self.players.get(flag.carrier or 0)
            if carrier is None or not carrier.alive:
                continue
            for player in self.players.values():
                if player is carrier or not player.alive:
                    continue
                if player.team != carrier.team:
                    continue
                if math.dist(player.pos, carrier.pos) <= ESCORT_RADIUS:
                    player.score += ESCORT_POINTS

    def on_kill(self, killer: Optional[Player], victim: Player,
                weapon_name: str) -> None:
        # who was carrying is only knowable before the base class drops it
        carrying = any(flag.carrier == victim.pid for flag in self.flags.values())
        super().on_kill(killer, victim, weapon_name)
        if killer is None or killer is victim:
            return
        self.badge(killer, "br_kills")
        if carrying:
            self.badge(killer, "br_carrier_kills")
        home = self.flags.get(killer.team)
        if home is not None and math.dist(victim.pos, home.home) <= DEFENCE_RADIUS:
            killer.score += DEFENCE_POINTS
            self.badge(killer, "br_defends")

    def return_flag(self, flag: Flag, by: Optional[Player] = None) -> None:
        super().return_flag(flag, by)
        if by is not None:
            self.badge(by, "br_returns")

    # ------------------------------------------------- overtime and the end
    def time_expired(self) -> None:
        moment = now()
        if self.sudden_death:
            if moment >= self.sudden_death_ends:
                self.end_round("", "Sudden death ran out -- honours even.")
            return
        if any(flag.state != "home" for flag in self.flags.values()):
            if not self.overtime:
                self.overtime = True
                self.push_event("overtime")
                self.system_message(
                    "OVERTIME -- this round does not end while a flag is out!")
            return
        self.overtime = False
        leader = max(self.captures, key=lambda t: self.captures[t])
        other = self.enemy_of(leader)
        if self.captures[leader] == self.captures[other]:
            self.start_sudden_death()
        else:
            self.end_round(leader, "Time up -- %s wins it %d-%d"
                           % (leader.upper(), self.captures[leader],
                              self.captures[other]))

    def start_sudden_death(self) -> None:
        self.sudden_death = True
        self.sudden_death_ends = now() + SUDDEN_DEATH_SECONDS
        for flag in self.flags.values():
            if flag.state != "home":
                self.return_flag(flag)
        self.push_event("sudden_death")
        self.system_message("SUDDEN DEATH -- the next capture takes it!")

    def capture(self, player: Player, flag: Flag) -> None:
        decider = self.sudden_death and self.phase == "active"
        clutch = self.overtime and self.phase == "active"
        super().capture(player, flag)
        self.badge(player, "br_captures")
        if clutch:
            self.badge(player, "br_clutch")
        if decider:
            self.badge(player, "br_sudden")
        if self.sudden_death and self.phase == "active":
            self.end_round(player.team,
                           "%s takes it in sudden death!" % player.team.upper())

    def end_round(self, winner: str, reason: str = "") -> None:
        live = self.phase == "active"
        if winner and live:
            for player in self.players.values():
                if player.team == winner:
                    self.badge(player, "br_wins")
                    self.badge(player, "br_map_%s" % self.area_id, 1, "max")
        super().end_round(winner, reason)
        if not live:
            return
        # roll where the server goes next, and say so while the card is up
        self.next_area_id = self.roll_next_area()
        nxt = self.areas[self.next_area_id]
        self.broadcast({"t": "brnext", "next": self.next_area_id, "name": nxt["name"],
                        "from": self.area_id, "reel": self.reel(),
                        "target": int(nxt["markers"].get("captures_to_win", 3)),
                        "minutes": int(round(float(nxt["markers"].get("round_seconds",
                                                                         900.0)) / 60.0))})
        self.system_message("Next map: %s -- the server moves there for the next round."
                            % nxt["name"])

    def restart_round(self) -> None:
        self.overtime = False
        self.sudden_death = False
        self.sudden_death_ends = 0.0
        self.lockdown = {team: False for team in self.team_names()}
        self.wave_origin = now()
        nxt = self.next_area_id or self.roll_next_area()
        self.next_area_id = ""
        self.move_to(nxt)
        super().restart_round()
