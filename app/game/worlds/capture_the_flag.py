"""Capture The Flag on Crossroads."""
from __future__ import annotations

import math
import random
import time
from typing import Any, Dict, List, Optional

from ..instance import GameInstance, Player, now
from ..maps import crossroads

CAPTURES_TO_WIN = 3
FLAG_RETURN_SECONDS = 22.0
ROUND_SECONDS = 600.0
PICKUP_RADIUS = 7.0
CAPTURE_RADIUS = 12.0
# A carrier this quiet has dropped off the network, not gone still: the
# client sends input every frame and pings every 2.5 seconds besides.
CARRIER_SILENCE = 8.0


class Flag:
    __slots__ = ("team", "home", "pos", "state", "carrier", "dropped_at",
                 "yaw")

    def __init__(self, team: str, home: List[float]):
        self.team = team
        self.home = list(home)
        self.pos = list(home)
        self.state = "home"      # home | carried | dropped
        self.carrier: Optional[int] = None
        self.dropped_at = 0.0
        self.yaw = 0.0           # which way it fell, so every drop looks different

    def payload(self, hold: float = 0.0) -> Dict[str, Any]:
        """What the client is told about this flag.

        A dropped flag carries the seconds left on its return with it, so the
        client can draw the countdown rather than guess at it -- and so the
        number on screen is the server's number, not a second clock that can
        drift away from it.
        """
        data = {"team": self.team, "state": self.state,
                "p": [round(v, 2) for v in self.pos],
                "carrier": self.carrier or 0,
                "home": [round(v, 2) for v in self.home]}
        if self.state == "dropped":
            data["left"] = round(max(0.0, hold - (now() - self.dropped_at)), 1)
            data["hold"] = round(hold, 1)
            data["yaw"] = round(self.yaw, 3)
        return data


class CaptureTheFlag(GameInstance):
    """Classic capture the flag.

    The tunables are class attributes rather than bare module constants so a
    world built on this one can retune the round without a second copy of the
    rules; the defaults are the numbers Crossroads has always played with.
    """

    mode = "captures"
    friendly_fire = False
    captures_to_win = CAPTURES_TO_WIN
    flag_return_seconds = FLAG_RETURN_SECONDS
    round_seconds = ROUND_SECONDS
    pickup_radius = PICKUP_RADIUS
    capture_radius = CAPTURE_RADIUS

    @staticmethod
    def build_map() -> Dict[str, Any]:
        return crossroads.build()

    def setup(self) -> None:
        markers = self.map.get("markers", {})
        self.flags: Dict[str, Flag] = {}
        for team in ("red", "blue"):
            marker = markers.get("flag_%s" % team, {"p": [0, 6, 0]})
            self.flags[team] = Flag(team, list(marker["p"]))
        self.captures = {"red": 0, "blue": 0}
        self.round_ends = now() + self.round_seconds
        self.phase = "active"

    def team_names(self) -> List[str]:
        return ["red", "blue"]

    def flag_payloads(self) -> Dict[str, Any]:
        return {team: flag.payload(self.flag_return_seconds)
                for team, flag in self.flags.items()}

    def broadcast_flags(self) -> None:
        self.broadcast({"t": "flags", "f": self.flag_payloads()})

    def enemy_of(self, team: str) -> str:
        return "blue" if team == "red" else "red"

    # ------------------------------------------------------------------ flow
    def round_state(self) -> Dict[str, Any]:
        return {
            "captures": dict(self.captures),
            "flags": self.flag_payloads(),
            "time_left": max(0, int(self.round_ends - now())),
            "target": self.captures_to_win,
            "teams": self.team_counts(),
        }

    def team_counts(self) -> Dict[str, int]:
        counts = {"red": 0, "blue": 0}
        for player in self.players.values():
            if player.team in counts:
                counts[player.team] += 1
        return counts

    def on_player_leave(self, player: Player) -> None:
        for flag in self.flags.values():
            if flag.carrier == player.pid:
                self.drop_flag(flag, player.pos)

    def on_kill(self, killer: Optional[Player], victim: Player,
                weapon_name: str) -> None:
        for flag in self.flags.values():
            if flag.carrier == victim.pid:
                self.drop_flag(flag, victim.pos)
                if killer is not None:
                    killer.score += 15
                    self.system_message("%s defended the %s flag!"
                                        % (killer.username, flag.team))

    def drop_flag(self, flag: Flag, position) -> None:
        flag.state = "dropped"
        flag.carrier = None
        # Let it fall to whatever is under it.  A carrier shot off a roof or
        # over a stairwell used to leave the flag hanging at the height they
        # died at, which reads as a bug and is unreachable besides.
        ground = self.ray_world([position[0], position[1] + 2.0, position[2]],
                                [0.0, -1.0, 0.0], 120.0)
        resting = position[1] + 2.0 - ground + 1.2
        flag.pos = [position[0], min(position[1] + 2.0, resting), position[2]]
        flag.yaw = random.uniform(-math.pi, math.pi)
        flag.dropped_at = now()
        self.push_event("flag_drop", team=flag.team, p=flag.pos,
                        yaw=round(flag.yaw, 3), hold=self.flag_return_seconds)
        self.broadcast_flags()

    def return_flag(self, flag: Flag, by: Optional[Player] = None) -> None:
        flag.state = "home"
        flag.carrier = None
        flag.pos = list(flag.home)
        self.push_event("flag_return", team=flag.team,
                        by=by.username if by else "")
        if by is not None:
            by.score += 8
            self.system_message("%s returned the %s flag."
                                % (by.username, flag.team))
        else:
            self.system_message("The %s flag returned to base." % flag.team)
        self.broadcast_flags()

    def on_tick(self, dt: float) -> None:
        if self.phase != "active":
            return
        moment = now()
        for flag in self.flags.values():
            if flag.state == "carried":
                carrier = self.players.get(flag.carrier or 0)
                if carrier is None or not carrier.alive:
                    self.drop_flag(flag, flag.pos)
                    continue
                # A carrier whose connection has gone quiet is not standing
                # there deciding what to do -- they are gone.  The world
                # takes longer than this to give up on the player, and the
                # objective must not wait that out: it lands where they were
                # and both teams can go and contest it.
                if moment - carrier.last_message > CARRIER_SILENCE:
                    self.drop_flag(flag, carrier.pos)
                    self.system_message("%s lost connection -- the %s flag"
                                        " is on the ground."
                                        % (carrier.username, flag.team))
                    continue
                flag.pos = [carrier.pos[0], carrier.pos[1] + 5.6, carrier.pos[2]]
            elif flag.state == "dropped":
                if moment - flag.dropped_at > self.flag_return_seconds:
                    self.return_flag(flag)

        for player in list(self.players.values()):
            if not player.alive:
                continue
            # A body that has stopped talking to us cannot take, return or
            # capture anything.  Without this, one that died on top of a
            # flag picks it straight back up on the tick after the check
            # above puts it down, over and over, until the world lets go of
            # the connection.
            if moment - player.last_message > CARRIER_SILENCE:
                continue
            enemy_flag = self.flags[self.enemy_of(player.team)]
            own_flag = self.flags[player.team]
            # pick up the enemy flag
            if enemy_flag.state in ("home", "dropped"):
                if math.dist(player.pos, enemy_flag.pos) < self.pickup_radius:
                    enemy_flag.state = "carried"
                    enemy_flag.carrier = player.pid
                    player.score += 5
                    self.push_event("flag_take", team=enemy_flag.team,
                                    by=player.username, pid=player.pid)
                    self.system_message("%s picked up the %s flag!"
                                        % (player.username, enemy_flag.team))
                    self.broadcast_flags()
                    continue
            # return our own dropped flag by touching it
            if own_flag.state == "dropped" and \
                    math.dist(player.pos, own_flag.pos) < self.pickup_radius:
                self.return_flag(own_flag, player)
                continue
            # capture
            if enemy_flag.state == "carried" and enemy_flag.carrier == player.pid:
                if own_flag.state == "home" and \
                        math.dist(player.pos, own_flag.home) < self.capture_radius:
                    self.capture(player, enemy_flag)

        if moment >= self.round_ends:
            self.time_expired()

    def time_expired(self) -> None:
        """What the clock running out means.  Worlds with overtime override it."""
        leader = max(self.captures, key=lambda t: self.captures[t])
        other = self.enemy_of(leader)
        if self.captures[leader] == self.captures[other]:
            self.end_round("", "Time up -- it's a draw!")
        else:
            self.end_round(leader, "Time up -- %s leads %d-%d"
                           % (leader.upper(), self.captures[leader],
                              self.captures[other]))

    def capture(self, player: Player, flag: Flag) -> None:
        self.captures[player.team] += 1
        player.score += 60
        flag.state = "home"
        flag.carrier = None
        flag.pos = list(flag.home)
        self.push_event("flag_capture", team=player.team, by=player.username,
                        score=dict(self.captures))
        self.system_message("%s CAPTURED the %s flag! (%s %d - %d %s)"
                            % (player.username, flag.team,
                               "RED", self.captures["red"],
                               self.captures["blue"], "BLUE"))
        self.broadcast_flags()
        if self.captures[player.team] >= self.captures_to_win:
            self.end_round(player.team,
                           "%s captured %d flags" % (player.team.upper(),
                                                     self.captures_to_win))

    def restart_round(self) -> None:
        self.captures = {"red": 0, "blue": 0}
        for flag in self.flags.values():
            flag.state = "home"
            flag.carrier = None
            flag.pos = list(flag.home)
        self.round_ends = now() + self.round_seconds
        super().restart_round()
        self.broadcast_flags()
