"""Sleeping instances: a world round that exists without a server running it.

An instance with only bots in it does not need a simulation -- nobody is
there to see one -- but it does need to *be* somewhere: the world browser
lists it with its player count and phase, its bots' profiles say they are
playing it, and a real player can press Join on it at any moment and must
walk into a round that has been going on all along.

So a sleeping instance is a handful of numbers advanced in closed form:

* **Capture the flag** (both maps): captures arrive as a Poisson process whose
  rate follows the size and skill of each team; a team reaching the target
  ends the round, which votes, restarts and goes again.  The clock runs out
  the way it does in a live round.
* **Payload**: the cart advances at a rate set by attackers against
  defenders, checkpoints add time, rounds swap sides, three wins take the
  match.
* **Burger Tycoon**: every crew earns its restaurant's real income (plus the
  fryer and freezer when the crew is the grinding kind) and buys the next
  upgrade the moment it can afford it -- the same upgrade table, the same
  prices, the same order as a live plot.

Nothing here is ticked.  :meth:`advance` jumps straight from the last update
to now, however long that was, by walking from one event to the next, so an
instance nobody has looked at for an hour costs exactly as much as one looked
at a second ago.  When a player joins, :meth:`wake_state` hands the host
everything it needs to build the live round mid-flight; when the last player
leaves, :meth:`from_live` takes the live round back.
"""
from __future__ import annotations

import math
import random
from typing import Any, Dict, List, Optional

TEAMS = ("red", "blue")


def poisson(rng: random.Random, lam: float) -> int:
    if lam <= 0:
        return 0
    if lam > 40:
        return max(0, int(round(rng.gauss(lam, math.sqrt(lam)))))
    limit = math.exp(-lam)
    k, p = 0, 1.0
    while True:
        p *= rng.random()
        if p <= limit:
            return k
        k += 1


class Member:
    __slots__ = ("team", "joined", "seg_start", "k", "d", "s", "rounds",
                 "skill", "objective")

    def __init__(self, team: str, now: float, skill: float, objective: float):
        self.team = team
        self.joined = now
        self.seg_start = now
        self.k = 0
        self.d = 0
        self.s = 0
        self.rounds = 0
        self.skill = skill
        self.objective = objective

    def dump(self) -> List[Any]:
        return [self.team, int(self.joined), int(self.seg_start), self.k,
                self.d, self.s, self.rounds, round(self.skill, 3),
                round(self.objective, 3)]

    @classmethod
    def load(cls, row: List[Any]) -> "Member":
        m = cls(row[0], row[1], row[7], row[8])
        m.seg_start, m.k, m.d, m.s, m.rounds = row[2], row[3], row[4], row[5], row[6]
        return m


# Kill and death rates per minute of play for a mid-skill bot, per mode.
COMBAT = {"captures": 0.9, "payload": 1.05, "endless": 0.08}


class Dormant:
    """One sleeping instance of one world."""

    def __init__(self, world: Dict[str, Any], inst_id: int, now: float,
                 rng: Optional[random.Random] = None, cap: float = 0.8):
        self.world_id = world["id"]
        self.mode = world.get("mode", "captures")
        self.max = int(world.get("max_players", 16))
        self.id = int(inst_id)
        self.rng = rng or random.Random()
        self.members: Dict[int, Member] = {}
        self.created = now
        self.updated = now
        self.round = 1
        self.phase = "active"
        self.phase_until = 0.0
        self.round_started = now
        self.rounds_ended = 0
        # how full the bots let this one get before they open another
        self.cap = max(1, min(self.max, int(round(self.max * cap))))
        if self.mode == "captures":
            relay = self.world_id == "blackout_relay"
            self.target = 5 if relay else 3
            self.round_len = 1800.0 if relay else 600.0
            self.rate = 0.085 if relay else 0.21   # captures/min, full team
            self.captures = {"red": 0, "blue": 0}
        elif self.mode == "payload":
            self.attackers, self.defenders = "blue", "red"
            self.progress = 0.0
            self.checkpoints = 0
            self.round_wins = {"red": 0, "blue": 0}
            self.phase = "setup"
            self.phase_until = now + 18.0
            self.round_ends = self.phase_until + 420.0
        else:
            from ..game.worlds import burger_tycoon as tycoon
            self.tycoon = tycoon
            self.plots: List[Dict[str, Any]] = [
                {"members": [], "built": [], "coins": 0.0, "bank": 0.0,
                 "earned": 0.0, "claimed": 0.0} for _ in range(8)]

    # ------------------------------------------------------------ members
    @property
    def count(self) -> int:
        return len(self.members)

    def room(self) -> int:
        return self.max - len(self.members)

    def team_counts(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for member in self.members.values():
            counts[member.team] = counts.get(member.team, 0) + 1
        return counts

    def add(self, uid: int, now: float, skill: float = 0.5,
            objective: float = 0.6) -> str:
        self.advance(now)
        if self.mode == "endless":
            team = self._pick_plot(uid, now)
        else:
            counts = self.team_counts()
            team = min(TEAMS, key=lambda t: (counts.get(t, 0), self.rng.random()))
        self.members[uid] = Member(team, now, skill, objective)
        return team

    def _pick_plot(self, uid: int, now: float) -> str:
        free = [i for i, p in enumerate(self.plots) if not p["members"]]
        if free and self.rng.random() < 0.75:
            index = self.rng.choice(free)
        else:
            open_plots = [i for i, p in enumerate(self.plots) if len(p["members"]) < 4]
            if not open_plots:
                index = 0
            else:
                index = max(open_plots, key=lambda i: (len(self.plots[i]["members"])
                                                       + self.rng.random() * 2))
        plot = self.plots[index]
        if not plot["members"]:
            plot.update({"built": [], "coins": float(self.tycoon.START_COINS),
                         "bank": 0.0, "earned": 0.0, "claimed": now})
        plot["members"].append(uid)
        return "plot_%d" % index

    def remove(self, uid: int, now: float) -> Optional[Member]:
        self.advance(now)
        member = self.members.pop(uid, None)
        if member is not None and self.mode == "endless":
            for plot in self.plots:
                if uid in plot["members"]:
                    plot["members"].remove(uid)
                    if not plot["members"]:
                        plot.update({"built": [], "coins": 0.0, "bank": 0.0,
                                     "earned": 0.0, "claimed": 0.0})
        return member

    # ------------------------------------------------------------ advance
    def advance(self, now: float, pace: float = 1.0) -> None:
        dt = now - self.updated
        if dt <= 0.5:
            return
        start = self.updated
        self.updated = now
        if not self.members:
            return
        if self.mode == "captures":
            self._advance_ctf(start, now, pace)
        elif self.mode == "payload":
            self._advance_payload(start, now, pace)
        else:
            self._advance_tycoon(dt, pace)

    def _team_strength(self, team: str) -> float:
        total = 0.0
        for member in self.members.values():
            if member.team == team:
                total += 0.5 + member.skill * 0.7 + member.objective * 0.5
        return total

    def _advance_ctf(self, start: float, now: float, pace: float) -> None:
        t = start
        full = self.max / 2.0
        while t < now:
            if self.phase in ("voting", "restarting", "ended"):
                if now < self.phase_until:
                    return
                t = self.phase_until
                self._new_round(t)
                continue
            strengths = {team: self._team_strength(team) for team in TEAMS}
            rates = {team: self.rate * pace / 60.0 * min(1.4, strengths[team] / max(1.0, full))
                     for team in TEAMS}
            # a team with nobody on it cannot capture anything
            total = sum(r for team, r in rates.items() if strengths[team] > 0)
            round_end = self.round_started + self.round_len
            nxt = t + (self.rng.expovariate(total) if total > 0 else 1e12)
            if nxt >= min(now, round_end):
                if round_end <= now:
                    t = round_end
                    red, blue = self.captures["red"], self.captures["blue"]
                    self._end_round(t, "red" if red > blue else ("blue" if blue > red else ""))
                    continue
                return
            t = nxt
            roll = self.rng.random() * total
            team = "red" if roll < rates["red"] else "blue"
            self.captures[team] += 1
            carriers = [m for m in self.members.values() if m.team == team]
            if carriers:
                weights = [0.2 + m.objective for m in carriers]
                who = self.rng.choices(carriers, weights)[0]
                who.s += 60
            if self.captures[team] >= self.target:
                self._end_round(t, team)

    def _end_round(self, t: float, winner: str) -> None:
        self.rounds_ended += 1
        for member in self.members.values():
            if member.team == winner:
                member.s += 50
        self.phase = "voting"
        # 8s of scores, 30s of voting, 4s to restart
        self.phase_until = t + 42.0

    def _new_round(self, t: float) -> None:
        self.round += 1
        self.phase = "active"
        self.round_started = t
        for member in self.members.values():
            member.k = 0
            member.d = 0
        if self.mode == "captures":
            self.captures = {"red": 0, "blue": 0}
            # the shuffle vote passes now and then
            if self.rng.random() < 0.3:
                ids = list(self.members)
                self.rng.shuffle(ids)
                for index, uid in enumerate(ids):
                    self.members[uid].team = TEAMS[index % 2]
        elif self.mode == "payload":
            self.round_wins = {"red": 0, "blue": 0}
            self.attackers, self.defenders = "blue", "red"
            self._reset_cart(t)

    def _reset_cart(self, t: float) -> None:
        self.progress = 0.0
        self.checkpoints = 0
        self.phase = "setup"
        self.phase_until = t + 18.0
        self.round_ends = self.phase_until + 420.0

    def _advance_payload(self, start: float, now: float, pace: float) -> None:
        t = start
        while t < now:
            if self.phase in ("voting", "restarting", "ended"):
                if now < self.phase_until:
                    return
                t = self.phase_until
                self._new_round(t)
                continue
            if self.phase == "intermission":
                if now < self.phase_until:
                    return
                t = self.phase_until
                self.attackers, self.defenders = self.defenders, self.attackers
                for member in self.members.values():
                    member.team = "red" if member.team == "blue" else "blue"
                    member.k = member.d = 0
                self.round += 1
                self._reset_cart(t)
                continue
            if self.phase == "setup":
                if now < self.phase_until:
                    return
                t = self.phase_until
                self.phase = "active"
                continue
            # active: move the cart in one-minute steps
            step = min(now, self.round_ends, t + 60.0) - t
            if step <= 0:
                self._finish_payload(t, self.defenders)
                continue
            push = self._team_strength(self.attackers)
            hold = self._team_strength(self.defenders)
            if push <= 0:
                rate = 0.0
            else:
                ratio = push / max(0.6, push + hold * 0.9)
                rate = 0.00135 * pace * (0.35 + ratio * 1.4) * self.rng.uniform(0.4, 1.6)
            self.progress = min(1.0, self.progress + rate * step)
            t += step
            fractions = (0.34, 0.68, 1.0)
            while self.checkpoints < 3 and self.progress >= fractions[self.checkpoints]:
                self.checkpoints += 1
                if self.checkpoints < 3:
                    self.round_ends += 90.0
            if self.progress >= 1.0:
                self._finish_payload(t, self.attackers)
            elif t >= self.round_ends:
                self._finish_payload(t, self.defenders)

    def _finish_payload(self, t: float, winner: str) -> None:
        self.round_wins[winner] = self.round_wins.get(winner, 0) + 1
        for member in self.members.values():
            if member.team == winner:
                member.s += 50
        self.rounds_ended += 1
        if self.round_wins[winner] >= 3:
            self.phase = "voting"
            self.phase_until = t + 42.0
        else:
            self.phase = "intermission"
            self.phase_until = t + 8.0

    def _advance_tycoon(self, dt: float, pace: float) -> None:
        upgrades = self.tycoon.UPGRADES
        for plot in self.plots:
            if not plot["members"]:
                continue
            grinders = sum(self.members[u].objective for u in plot["members"]
                           if u in self.members)
            remaining = dt * pace
            guard = 0
            while remaining > 0 and guard < 40:
                guard += 1
                income = plot.get("income")
                if income is None or plot.get("income_n") != len(plot["built"]):
                    income = sum(self.tycoon.UPGRADES_BY_ID[u]["income"]
                                 for u in plot["built"] if u in self.tycoon.UPGRADES_BY_ID)
                    plot["income"], plot["income_n"] = income, len(plot["built"])
                active = 0.0
                if "fryer" in plot["built"]:
                    active += 95 / 3.5 * min(1.0, grinders * 0.5)
                if "freezer" in plot["built"]:
                    active += 380 / 6.0 * min(1.0, grinders * 0.35)
                # nobody stands on the collector every second, and the
                # early game is spent running about more than earning
                rate = income * 0.5 + active * 0.3 + 1.2
                nxt = next((u for u in upgrades if u["id"] not in plot["built"]
                            and all(r in plot["built"] for r in u["req"])), None)
                if nxt is None:
                    plot["earned"] += rate * remaining
                    plot["bank"] = min(self.tycoon.BANK_CAP,
                                       plot["bank"] + income * remaining * 0.1)
                    break
                need = nxt["cost"] - plot["coins"]
                wait = need / rate if need > 0 else 0.0
                if wait > remaining:
                    plot["coins"] += rate * remaining
                    plot["earned"] += rate * remaining
                    break
                remaining -= wait
                plot["coins"] += rate * wait - nxt["cost"]
                plot["earned"] += rate * wait
                plot["built"].append(nxt["id"])
                builder = self.rng.choice(plot["members"])
                if builder in self.members:
                    self.members[builder].s += 20

    # ------------------------------------------------------------ describe
    def describe(self) -> Dict[str, Any]:
        return {"id": self.id, "count": len(self.members), "max": self.max,
                "phase": self.phase, "round": self.round, "dormant": True,
                "humans": 0, "bots": len(self.members)}

    def summary(self) -> str:
        if self.mode == "captures":
            return "%d-%d" % (self.captures["red"], self.captures["blue"])
        if self.mode == "payload":
            return "cart %d%% (%d-%d)" % (int(self.progress * 100),
                                         self.round_wins["red"], self.round_wins["blue"])
        built = sum(len(p["built"]) for p in self.plots)
        return "%d builds" % built

    # --------------------------------------------------------- statistics
    def sample_segment(self, member: Member, now: float) -> Dict[str, int]:
        """What one bot did while this instance slept, for its game stats."""
        minutes = max(0.0, now - member.seg_start) / 60.0
        base = COMBAT.get(self.mode, 0.5)
        kills = poisson(self.rng, base * minutes * (0.35 + member.skill * 1.3))
        deaths = poisson(self.rng, base * minutes * (1.45 - member.skill * 0.9))
        score = kills * 10 + int(minutes * (6 + member.objective * 10))
        rounds = max(0, self.rounds_ended - member.rounds)
        wins = sum(1 for _ in range(rounds) if self.rng.random() < 0.35 + member.skill * 0.3)
        return {"kills": kills, "deaths": deaths, "score": score,
                "playtime": int(minutes * 60), "rounds": rounds, "wins": wins}

    def scoreboard_fill(self, member: Member, now: float) -> None:
        """Give a member a believable score line for the round in progress."""
        since = max(member.joined, self.round_started)
        minutes = max(0.0, now - since) / 60.0
        base = COMBAT.get(self.mode, 0.5)
        member.k += poisson(self.rng, base * minutes * (0.35 + member.skill * 1.3))
        member.d += poisson(self.rng, base * minutes * (1.45 - member.skill * 0.9))
        member.s += member.k * 10 + int(minutes * (4 + member.objective * 8))

    # --------------------------------------------------------------- wake
    def wake_state(self, now: float) -> Dict[str, Any]:
        """Everything a host needs to build this round live, mid-flight."""
        self.advance(now)
        state: Dict[str, Any] = {"mode": self.mode, "round": self.round,
                                 "phase": self.phase,
                                 "phase_left": max(0.0, self.phase_until - now)}
        if self.mode == "captures":
            state["captures"] = dict(self.captures)
            state["time_left"] = max(30.0, self.round_started + self.round_len - now)
            # a flag is often out when you arrive
            if self.phase == "active" and self.rng.random() < 0.35:
                state["flag_out"] = self.rng.choice(TEAMS)
        elif self.mode == "payload":
            state.update({"attackers": self.attackers, "progress": self.progress,
                          "checkpoints": self.checkpoints,
                          "round_wins": dict(self.round_wins),
                          "time_left": max(20.0, self.round_ends - now),
                          "setup_left": max(0.0, self.phase_until - now)
                          if self.phase == "setup" else 0.0})
        else:
            state["plots"] = [{"members": list(p["members"]), "built": list(p["built"]),
                               "coins": int(p["coins"]), "bank": int(p["bank"]),
                               "earned": int(p["earned"])} for p in self.plots]
        return state

    def from_live(self, live: Dict[str, Any], now: float) -> None:
        """Adopt the state of a live round that has just gone to sleep."""
        self.updated = now
        self.round = int(live.get("round", self.round) or 1)
        phase = live.get("phase") or "active"
        self.phase = phase if phase in ("active", "voting", "setup",
                                        "intermission", "restarting",
                                        "ended") else "active"
        self.phase_until = now + float(live.get("phase_left", 0) or 0)
        if self.phase in ("ended", "restarting"):
            self.phase = "voting"
            self.phase_until = max(self.phase_until, now + 10.0)
        if self.mode == "captures":
            caps = live.get("captures") or {}
            self.captures = {t: int(caps.get(t, 0) or 0) for t in TEAMS}
            left = float(live.get("time_left", 300) or 300)
            self.round_started = now - max(0.0, self.round_len - left)
        elif self.mode == "payload":
            self.attackers = live.get("attackers") or "blue"
            self.defenders = "red" if self.attackers == "blue" else "blue"
            self.progress = float(live.get("progress", 0) or 0)
            self.checkpoints = int(live.get("checkpoints", 0) or 0)
            wins = live.get("round_wins") or {}
            self.round_wins = {t: int(wins.get(t, 0) or 0) for t in TEAMS}
            self.round_ends = now + float(live.get("time_left", 300) or 300)
        else:
            plots = live.get("plots") or []
            for index, plot in enumerate(plots[:8]):
                mine = [u for u in plot.get("members", []) if u in self.members]
                self.plots[index] = {"members": mine,
                                     "built": list(plot.get("built", [])) if mine else [],
                                     "coins": float(plot.get("coins", 0)) if mine else 0.0,
                                     "bank": float(plot.get("bank", 0)) if mine else 0.0,
                                     "earned": float(plot.get("earned", 0)) if mine else 0.0,
                                     "claimed": now}

    # -------------------------------------------------------------- persist
    def dump(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "world": self.world_id, "id": self.id, "round": self.round,
            "phase": self.phase, "phase_until": self.phase_until,
            "round_started": self.round_started, "rounds_ended": self.rounds_ended,
            "updated": self.updated, "cap": self.cap, "created": self.created,
            "members": {str(uid): m.dump() for uid, m in self.members.items()}}
        if self.mode == "captures":
            data["captures"] = self.captures
        elif self.mode == "payload":
            data.update({"attackers": self.attackers, "progress": self.progress,
                         "checkpoints": self.checkpoints, "round_wins": self.round_wins,
                         "round_ends": self.round_ends})
        else:
            data["plots"] = self.plots
        return data

    @classmethod
    def load(cls, world: Dict[str, Any], data: Dict[str, Any]) -> "Dormant":
        inst = cls(world, int(data["id"]), float(data.get("created", 0)))
        for key in ("round", "phase", "phase_until", "round_started",
                    "rounds_ended", "updated", "cap"):
            if key in data:
                setattr(inst, key, data[key])
        inst.members = {int(uid): Member.load(row)
                        for uid, row in (data.get("members") or {}).items()}
        if inst.mode == "captures" and "captures" in data:
            inst.captures = data["captures"]
        elif inst.mode == "payload":
            for key in ("attackers", "progress", "checkpoints", "round_wins",
                        "round_ends"):
                if key in data:
                    setattr(inst, key, data[key])
            inst.defenders = "red" if inst.attackers == "blue" else "blue"
        elif "plots" in data:
            inst.plots = data["plots"]
        return inst

    def warm(self, now: float) -> None:
        """Start partway through, as if it had been running a while."""
        if self.mode == "captures":
            elapsed = self.rng.uniform(0.05, 0.85) * self.round_len
            self.round_started = now - elapsed
            self.round = self.rng.randint(1, 6)
            self.updated = now - elapsed
        elif self.mode == "payload":
            self.round = self.rng.randint(1, 3)
            self.updated = now - self.rng.uniform(30, 400)
            self.phase_until = self.updated + 18
            self.round_ends = self.phase_until + 420
        else:
            self.updated = now - self.rng.uniform(300, 2400)
            for plot in self.plots:
                if plot["members"]:
                    plot["claimed"] = self.updated
        for member in self.members.values():
            member.joined = min(member.joined, self.updated + self.rng.uniform(0, 120))
        self.advance(now)
