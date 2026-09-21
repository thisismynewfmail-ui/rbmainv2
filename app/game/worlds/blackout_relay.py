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

Everything else -- the flags themselves, pickups, returns, the shuffle vote
-- is inherited from :class:`CaptureTheFlag` unchanged.
"""
from __future__ import annotations

import math
import time
from typing import Any, Dict, List, Optional

from ..instance import Player, now
from ..maps import ironvale
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

    captures_to_win = 3
    round_seconds = 600.0
    flag_return_seconds = 20.0
    pickup_radius = 9.0       # the whole top of the pedestal counts
    capture_radius = 15.0

    wave_seconds = WAVE_SECONDS
    min_respawn = MIN_RESPAWN
    wave_origin = 0.0

    @staticmethod
    def build_map() -> Dict[str, Any]:
        return ironvale.build()

    # ------------------------------------------------------------- lifecycle
    def setup(self) -> None:
        super().setup()
        markers = self.map.get("markers", {})
        self.outposts: Dict[str, List[Dict[str, Any]]] = {
            team: list(markers.get("outpost_%s" % team) or [])
            for team in self.team_names()
        }
        self.lockdown = {team: False for team in self.team_names()}
        self.overtime = False
        self.sudden_death = False
        self.sudden_death_ends = 0.0
        self.wave_origin = now()

    def on_player_ready(self, player: Player) -> None:
        super().on_player_ready(player)
        for line in (
                "Ironvale Relay -- deploy from the Relay, run the flag home.",
                "Lose your own flag and your team falls back to the bunkers,"
                " right across the carrier's way out.",
                "There is a hatch behind every keep. The tunnels come out"
                " inside all four bunkers."):
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
        """Muster at the Relay, or fall back to the bunkers under lockdown."""
        flag = self.flags.get(team)
        if flag is not None and flag.state != "home":
            forward = self.outposts.get(team)
            if forward:
                return list(forward)
        return super().spawn_points(team)

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
        super().on_kill(killer, victim, weapon_name)
        if killer is None or killer is victim:
            return
        home = self.flags.get(killer.team)
        if home is not None and math.dist(victim.pos, home.home) <= DEFENCE_RADIUS:
            killer.score += DEFENCE_POINTS

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
        super().capture(player, flag)
        if self.sudden_death and self.phase == "active":
            self.end_round(player.team,
                           "%s takes it in sudden death!" % player.team.upper())

    def restart_round(self) -> None:
        self.overtime = False
        self.sudden_death = False
        self.sudden_death_ends = 0.0
        self.lockdown = {team: False for team in self.team_names()}
        self.wave_origin = now()
        super().restart_round()
