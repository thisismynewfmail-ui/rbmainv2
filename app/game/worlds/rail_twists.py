"""The twists of Rail Rivals' newer railroads (app/game/worlds/rail_rivals.py).

Dustbowl Gulch, Silverpine Pass, Redrock Mesa and Lantern Deep keep their
twists in the world itself.  Every line built since names one of these by
its area's ``extra["twist"]``; the world makes the matching :class:`Twist`
at the start of each race and hands it the race at every point where a
twist can matter:

``setup``       read the area (its ``extra`` and ``points``), reset state
``on_live``     the race has started: start the clocks
``tick``        once a tick, with everybody playing
``limit``       how far a cart may roll right now, and why (a stop)
``drive``       a cart's speed this tick, when the twist moves it itself
``crew``        extra pushers the twist lends a cart (the circus elephant)
``what_here``   what holding E does where a player stands
``do``          the hold is done: do it
``state``       what the client draws and the HUD says
``carrying``    what a player has on their back (a rail, a bucket)
``drop``        a player died or the round ended: put it down
``flee``        a place a bot should get to, now (out of harm's way)
``bot_job``     an errand worth running for this bot right now
``job_valid``   is a bot's errand still worth running
``observe`` / ``selftest``  what the headless tests watch for

A twist's numbers are its own; what it shares with the old ones is the
vocabulary -- carts stop with a ``held`` reason, a hold of E is an ``act``
with a ``kind`` and a ``key``, and things that happen go out as ``rrx``
messages (``k`` = the twist's own kinds) and speech events (``rr_*``).
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .. import instance as engine

Act = Tuple[str, Any, float]
Stop = Tuple[float, str]


def flat(a: Sequence[float], b: Sequence[float]) -> float:
    return math.hypot(a[0] - b[0], a[2] - b[2])


class Twist:
    """The do-nothing twist every real one starts from."""

    kind = ""
    welcome = ""
    # speech the twist pushes, the stats its jobs count under, and the
    # end-of-round award for the best at it: (stat, title, "did %d things")
    jobs: Tuple[str, ...] = ()
    award: Optional[Tuple[str, str, str]] = None
    # acts that count their own progress (a dig shared by several diggers)
    continuous: Tuple[str, ...] = ()
    job_lines: Dict[str, List[str]] = {}

    def __init__(self, world):
        self.w = world

    # ------------------------------------------------------------ round
    def setup(self, area: Dict[str, Any], extra: Dict[str, Any],
              points: Dict[str, List[Dict[str, Any]]], moment: float) -> None:
        pass

    def on_live(self, moment: float) -> None:
        pass

    def tick(self, playing: List[Any], dt: float, moment: float) -> None:
        pass

    # ------------------------------------------------------------ carts
    def limit(self, cart, moment: float) -> Optional[Stop]:
        return None

    def drive(self, cart, pushers: List[Any], contested: bool, braked: bool,
              dt: float, moment: float) -> Optional[float]:
        """A speed for the cart this tick (negative rolls it back), or None
        for the usual push-and-roll."""
        return None

    def crew(self, cart, moment: float) -> int:
        return 0

    def floor(self, cart) -> float:
        """How far back a cart this twist rolls back may go."""
        return 0.0

    # ------------------------------------------------------- holding E
    def what_here(self, player, moment: float) -> Optional[Act]:
        return None

    def do(self, player, kind: str, key: Any, moment: float) -> bool:
        return False

    def act_progress(self, player, act: Dict[str, Any]) -> Optional[float]:
        return None

    # ----------------------------------------------------------- people
    def carrying(self, player) -> str:
        return str(player.extra.get("carry") or "")

    def drop(self, player) -> None:
        player.extra.pop("carry", None)

    def move_scale(self, player) -> Optional[float]:
        return 0.86 if self.carrying(player) else None

    def me(self, player) -> Dict[str, Any]:
        kind = self.carrying(player)
        return {"carry": kind} if kind else {}

    def drown_what(self, player) -> Optional[str]:
        return None

    # ------------------------------------------------------------ state
    def state(self, moment: float) -> Dict[str, Any]:
        return {}

    def context(self) -> List[str]:
        return []

    # ------------------------------------------------------------- bots
    def urgent(self, brain) -> bool:
        return False

    def flee(self, brain) -> Optional[List[float]]:
        return None

    def carry_job(self, brain) -> Optional[Dict[str, Any]]:
        """Where a bot carrying something takes it."""
        return None

    def bot_job(self, brain, own, rival, moment: float) -> Optional[Dict[str, Any]]:
        return None

    def job_valid(self, job: Dict[str, Any], team: str) -> Optional[bool]:
        return None

    # ------------------------------------------------------------ tests
    def observe(self) -> Dict[str, Any]:
        return {}

    def selftest(self, observations: List[Dict[str, Any]]) -> List[Tuple[str, bool, Any]]:
        return []

    # -------------------------------------------------------- helpers
    def lane_team(self, lane: str) -> str:
        return self.w._lane_team(lane)

    def cart_on(self, lane: str):
        return self.w.carts.get(self.lane_team(lane))

    def near(self, player, point: Sequence[float], r: float, dy: float = 4.0) -> bool:
        return flat(player.pos, point) <= r and abs(player.pos[1] - point[1]) <= dy

    def event(self, kind: str, player, team: str, **extra: Any) -> None:
        self.w._event(kind, player, team, **extra)

    def send(self, msg: Dict[str, Any]) -> None:
        self.w.broadcast(msg)

    def stat(self, player, key: str, amount: float = 1.0) -> None:
        self.w._stat(player, key, amount)

    def score(self, player, points: int, stat: str = "", badge: str = "") -> None:
        player.score += points
        if stat:
            self.stat(player, stat)
        if badge:
            self.w.badge(player, badge)


TWISTS: Dict[str, type] = {}


def register(cls: type) -> type:
    TWISTS[cls.kind] = cls
    return cls


def make(world, kind: str) -> Optional[Twist]:
    cls = TWISTS.get(kind)
    return cls(world) if cls is not None else None


def now() -> float:
    return engine.now()


# ======================================================== the railhead
RAIL_LEN = 6.0            # track one rail lays
LAY_R = 6.5               # how close to the railhead you lay one
LAY_HOLD = 1.1
PULL_HOLD = 2.0
STACK_R = 6.0
STACK_HOLD = 0.7


@register
class Railhead(Twist):
    """Golden Spike Summit: the line is not finished.

    Each lane has gaps (``extra["gaps"][lane]``: start and end distances) --
    graded and ballasted, no rails.  A cart stops at the end of what is
    laid.  Anybody can take a rail from a stack (``points["rails"]``) and
    carry it (slowly); a team lays its rails on its *own* line's first
    unfinished gap, a rail at a time, from the railhead -- before its cart
    gets there, if it is smart.  The other team can pull the last-laid rail
    back up while the cart is not on it, and walks off with it."""

    kind = "railhead"
    welcome = ("The line is not finished: carry rails from the stacks and hold E at "
               "your railhead to lay them. Pull up theirs before their cart gets there.")
    jobs = ("rails", "pulled")
    award = ("rails", "Spike Driver", "laid %d rails")
    job_lines = {"fetch_rail": ["getting rails", "rails for the railhead", "on rails"],
                 "pull_rail": ["pulling up their rails", "stealing a rail lol"]}

    def setup(self, area, extra, points, moment):
        self.gaps: Dict[str, List[Dict[str, Any]]] = {}
        for lane, spans in (extra.get("gaps") or {}).items():
            path = self.w.lanes.get(lane)
            if path is None:
                continue
            rows = []
            for span in spans:
                d0, d1 = float(span[0]), float(span[1])
                need = max(1, int(math.ceil((d1 - d0) / RAIL_LEN - 1e-6)))
                rows.append({"d0": d0, "d1": d1, "need": need, "laid": 0, "said": False})
            self.gaps[lane] = sorted(rows, key=lambda g: g["d0"])
        self.stacks = [list(m["p"]) for m in points.get("rails", [])]
        self.laid_total = 0
        self.pulled_total = 0
        self.carried = 0

    # ------------------------------------------------------------ lanes
    def open_gap(self, lane: str) -> Optional[Dict[str, Any]]:
        for gap in self.gaps.get(lane, []):
            if gap["laid"] < gap["need"]:
                return gap
        return None

    def head_d(self, gap: Dict[str, Any]) -> float:
        """How far along its line the laid track of a gap reaches."""
        return min(gap["d1"], gap["d0"] + gap["laid"] * RAIL_LEN)

    def head_point(self, lane: str, gap: Dict[str, Any]) -> List[float]:
        return self.w.lanes[lane].point(self.head_d(gap) + 1.5)

    def limit(self, cart, moment):
        gap = self.open_gap(cart.lane)
        if gap is None or cart.d > gap["d1"]:
            return None
        return (max(0.0, self.head_d(gap) - 3.5), "railhead")

    # -------------------------------------------------------- holding E
    def what_here(self, player, moment):
        team = player.team
        own = self.w.lane_for(team)
        carrying = self.carrying(player) == "rail"
        if carrying:
            gap = self.open_gap(own)
            if gap is not None and self.near(player, self.head_point(own, gap), LAY_R, 5.0):
                return ("lay", own, LAY_HOLD)
            return None
        if player.extra.get("coal"):
            return None
        # their railhead: pull up the last rail they laid
        for lane in self.gaps:
            if lane == own:
                continue
            gap = self.open_gap(lane)
            if gap is None or gap["laid"] <= 0:
                continue
            cart = self.cart_on(lane)
            if cart is not None and cart.d >= self.head_d(gap) - RAIL_LEN - 8.0:
                continue                      # the cart is on it: it stays down
            last = self.w.lanes[lane].point(self.head_d(gap) - RAIL_LEN / 2.0)
            if self.near(player, last, LAY_R, 5.0):
                return ("pull", lane, PULL_HOLD)
        for stack in self.stacks:
            if self.near(player, stack, STACK_R, 4.0):
                return ("rail", tuple(stack), STACK_HOLD)
        return None

    def do(self, player, kind, key, moment):
        if kind == "rail":
            player.extra["carry"] = "rail"
            self.carried += 1
            player.send({"t": "rrx", "k": "rail", "on": 1})
            return True
        if kind == "lay":
            gap = self.open_gap(key)
            if gap is None or self.carrying(player) != "rail":
                return True
            player.extra.pop("carry", None)
            gap["laid"] += 1
            self.laid_total += 1
            self.score(player, 6, "rails", "rr_rails")
            done = gap["laid"] >= gap["need"]
            self.send({"t": "rrx", "k": "lay", "lane": key, "laid": gap["laid"],
                       "need": gap["need"], "by": player.username, "done": 1 if done else 0})
            if done:
                self.score(player, 10)
                self.event("rr_railhead", player, self.lane_team(key),
                           what=self.w._place(self.w.lanes[key].point(gap["d1"])))
            self.w._broadcast_state()
            return True
        if kind == "pull":
            gap = self.open_gap(key)
            if gap is None or gap["laid"] <= 0 or self.carrying(player):
                return True
            gap["laid"] -= 1
            self.pulled_total += 1
            player.extra["carry"] = "rail"
            self.score(player, 6, "pulled", "rr_rails_pulled")
            victim = self.lane_team(key)
            self.send({"t": "rrx", "k": "pull", "lane": key, "laid": gap["laid"],
                       "need": gap["need"], "by": player.username})
            self.event("rr_rail_pulled", player, victim)
            self.w._broadcast_state()
            return True
        return False

    # ------------------------------------------------------------ state
    def state(self, moment):
        out = {}
        for lane, gaps in self.gaps.items():
            out[lane] = [{"d0": round(g["d0"], 1), "d1": round(g["d1"], 1), "need": g["need"],
                          "laid": g["laid"]} for g in gaps]
        return {"gaps": out}

    def context(self):
        lines = []
        for lane in sorted(self.gaps):
            gap = self.open_gap(lane)
            if gap is not None:
                lines.append("%s's line has %d of %d rails laid at its next gap." % (
                    self.w.team_name(self.lane_team(lane)), gap["laid"], gap["need"]))
        return lines

    # ------------------------------------------------------------- bots
    def _carriers(self, team: str) -> int:
        return sum(1 for p in self.w.playing() if p.team == team and self.carrying(p) == "rail")

    def carry_job(self, brain):
        p = brain.p
        own = self.w.lane_for(p.team)
        gap = self.open_gap(own)
        if gap is None:
            # nowhere to lay it: put it down and get back to the race
            p.extra.pop("carry", None)
            return None
        return {"k": "lay", "at": self.head_point(own, gap), "r": LAY_R - 2.0,
                "key": "lay%s%d" % (own, int(gap["d0"])), "say": "laying a rail at the railhead"}

    def urgent(self, brain):
        return self.carrying(brain.p) == "rail"

    def _stack_near(self, pos) -> Optional[List[float]]:
        best, best_d = None, 1e9
        for stack in self.stacks:
            d = flat(stack, pos)
            if d < best_d:
                best, best_d = stack, d
        return best

    def bot_job(self, brain, own, rival, moment):
        p = brain.p
        rng = brain.rng
        role = brain.role
        twist = self.w.pct("twist")
        gap = self.open_gap(own.lane)
        if gap is not None and gap["d0"] - own.d < 320.0 and role in ("pusher", "flex") and \
                self._carriers(p.team) < 3 and rng.random() < 0.35 + twist * 0.6:
            head = self.head_point(own.lane, gap)
            stack = self._stack_near(head) if flat(head, p.pos) < 220 else self._stack_near(p.pos)
            if stack is not None:
                return {"k": "fetch_rail", "at": [stack[0], max(0.0, stack[1] - 1.4), stack[2]],
                        "r": STACK_R - 2.0, "key": "stack%d%d" % (int(stack[0]), int(stack[2])),
                        "say": "fetching a rail for the railhead", "for": 40.0}
        raiding = role == "raider" or (role == "flex" and rival.fraction > own.fraction + 0.08)
        theirs = self.open_gap(rival.lane)
        if raiding and theirs is not None and theirs["laid"] > 0 and \
                0.0 < theirs["d0"] - rival.d < 200.0 and rng.random() < 0.3 + twist * 0.5:
            last = self.w.lanes[rival.lane].point(self.head_d(theirs) - RAIL_LEN / 2.0)
            return {"k": "pull_rail", "lane": rival.lane, "at": last, "r": LAY_R - 2.0,
                    "key": "pull%s%d" % (rival.lane, int(theirs["d0"])),
                    "say": "pulling up their rails", "for": 35.0}
        return None

    def job_valid(self, job, team):
        kind = job["k"]
        if kind == "fetch_rail":
            own = self.w.lane_for(team)
            return self.open_gap(own) is not None
        if kind == "pull_rail":
            gap = self.open_gap(job["lane"])
            cart = self.cart_on(job["lane"])
            return gap is not None and gap["laid"] > 0 and \
                (cart is None or cart.d < self.head_d(gap) - RAIL_LEN - 8.0)
        return None

    # ------------------------------------------------------------ tests
    def observe(self):
        return {"laid": self.laid_total, "pulled": self.pulled_total, "carried": self.carried,
                "open": sum(1 for gaps in self.gaps.values() for g in gaps if g["laid"] < g["need"])}

    def selftest(self, observations):
        laid = max([o.get("laid", 0) for o in observations] or [0])
        carried = max([o.get("carried", 0) for o in observations] or [0])
        return [("somebody carries rails from a stack", carried > 0, carried),
                ("somebody lays rails at a railhead", laid > 0, laid)]


# =========================================================== the sweep
SWEEP_EVERY = (50.0, 70.0)    # seconds between one and the next, uncalled
SWEEP_HOLD = 13.0             # how far short of the crossing a cart is held
SWEEP_CLEAR = 7.0             # how far past it a cart is clear of it
SWEEP_ROLL = 4.0              # how fast an abandoned cart is rolled back off it
SWEEP_DY = 7.0
SWEEP_WARN = 150.0            # how far off a coming head sends bots off the line
CALL_R = 4.6
CALL_HOLD = 2.5
CALL_REST = 14.0              # after one has gone by, how long before the next can be called
CALL_SOON = 14.0              # no calling one that is due sooner than this anyway

SWEEP_STYLES = {
    "freight": {"what": "the through freight", "held": "freight",
                "welcome": ("A through freight comes down the main line every minute or so. "
                            "When the crossing bells ring your cart is held short of the "
                            "crossing -- and anybody on the main line is in its way. Hold E "
                            "at a call box to call the next one down on their cart."),
                "context": "the through freight"},
    "stampede": {"what": "the stampede", "held": "stampede",
                 "welcome": ("Every minute or so the herd breaks and stampedes down the cattle "
                             "trail across both lines. Your cart is held short of the trail "
                             "while it runs -- and anybody on the trail is trampled. Hold E at "
                             "a corral gate to turn the herd loose on their cart."),
                 "context": "the stampede"},
}


@register
class Sweep(Twist):
    """Thunder Junction: something big comes through across both lines on
    a timetable -- a through freight on the main line (``extra["sweep"]``:
    its ``path`` in world coordinates, ``speed``, ``length``, ``half`` its
    half-width, ``style``).

    From the moment it sets off -- out of sight, beyond the area -- until
    its tail has cleared, each line's crossing is shut: a cart short of it
    is held at the stop line, and a cart already on it goes over if its own
    company pushes it, or is rolled back off it if they do not (or the
    other lot are on it).  Anybody on the line where it passes is killed.
    Anyone can hold E at a call box (``points["call"]``) to send the next
    one down now -- on the other cart, if they time it."""

    kind = "sweep"
    jobs = ("called", "beat")
    award = ("called", "Train Dispatcher", "called the freight down %d times")
    job_lines = {"call": ["calling the freight down", "freight on them lol", "calling it in"]}

    def setup(self, area, extra, points, moment):
        from .rail_rivals import Lane, _crossing
        spec = extra.get("sweep") or {}
        self.style = str(spec.get("style") or "freight")
        look = SWEEP_STYLES.get(self.style, SWEEP_STYLES["freight"])
        self.what = look["what"]
        self.reason = look["held"]
        self.welcome = look["welcome"]
        self.track = Lane(spec.get("path") or [[0.0, 0.0, -1.0], [0.0, 0.0, 1.0]])
        self.speed = float(spec.get("speed", 40.0))
        self.length = float(spec.get("length", 230.0))
        self.half = float(spec.get("half", 4.0))
        every = spec.get("every") or SWEEP_EVERY
        self.every = (float(every[0]), float(every[1]))
        self.cross: Dict[str, Tuple[float, float]] = {}
        for lane, path in self.w.lanes.items():
            self.cross[lane] = _crossing(path, self.track)
        self.calls = [list(m["p"]) for m in points.get("call", [])]
        self.phase = "idle"
        self.next_at = moment + 1e9
        self.t0 = 0.0
        self.dir = 1
        self.count = 0
        self.called_by: Optional[Tuple[int, str]] = None
        self.call_ok = moment
        self.credited = False
        self.beaten: Dict[str, bool] = {}
        self.last_d: Dict[str, float] = {}
        self.passes = 0
        self.calls_made = 0
        self.hits = 0
        self.held_seen = 0
        self.beats = 0

    def on_live(self, moment):
        self.next_at = moment + self.w.rng.uniform(*self.every) * 0.5
        self.call_ok = moment + CALL_REST

    # ------------------------------------------------------------ train
    def head(self, moment: float) -> float:
        """How far the head has come from its own end of the line."""
        return (moment - self.t0) * self.speed if self.phase == "run" else -1e9

    def travel(self, s: float) -> float:
        """A distance along the line, counted the way this one is going."""
        return s if self.dir > 0 else self.track.length - s

    def closed(self, lane: str, moment: float) -> bool:
        if self.phase != "run" or lane not in self.cross:
            return False
        tail = self.head(moment) - self.length
        return tail < self.travel(self.cross[lane][1]) + 6.0

    def start(self, moment: float, caller=None) -> None:
        self.phase = "run"
        self.t0 = moment
        self.dir = 1 if self.count % 2 == 0 else -1
        self.count += 1
        self.credited = False
        self.beaten = {}
        self.called_by = (caller.pid, caller.team) if caller is not None else None
        self.send({"t": "rrx", "k": "sweep", "on": 1, "dir": self.dir, "n": self.count,
                   "speed": self.speed, "len": self.length,
                   "by": caller.username if caller is not None else "",
                   "team": caller.team if caller is not None else ""})
        if caller is not None:
            self.event("rr_freight_called", caller, self.w.rival(caller.team))
        self.w._broadcast_state()

    def finish(self, moment: float) -> None:
        self.phase = "idle"
        self.passes += 1
        self.next_at = moment + self.w.rng.uniform(*self.every)
        self.call_ok = moment + CALL_REST
        self.called_by = None
        self.send({"t": "rrx", "k": "sweep", "on": 0})
        self.w._broadcast_state()

    def in_way(self, pos: Sequence[float], moment: float, ahead: float = 3.0) -> bool:
        """Is this spot under the train right now?"""
        s, off = self.track.project(pos[0], pos[2])
        if off > self.half or abs(pos[1] - self.track.height(s)) > SWEEP_DY:
            return False
        u = self.travel(s)
        head = self.head(moment)
        return head - self.length - 2.0 <= u <= head + ahead

    def tick(self, playing, dt, moment):
        if self.phase == "idle":
            if moment >= self.next_at:
                self.start(moment)
            return
        for player in playing:
            if self.in_way(player.pos, moment):
                self.hits += 1
                self.w.kill(player, None, self.what)
        head = self.head(moment)
        for lane, (d_x, s_x) in self.cross.items():
            cart = self.cart_on(lane)
            if cart is None:
                continue
            last = self.last_d.get(lane, cart.d)
            self.last_d[lane] = cart.d
            if not self.closed(lane, moment):
                continue
            if cart.held == self.reason:
                self.held_seen += 1
                self._credit(cart, moment)
            # over the crossing with the bells going and the train not there yet
            if last < d_x <= cart.d and head < self.travel(s_x) and not self.beaten.get(lane):
                self.beaten[lane] = True
                self.beats += 1
                pushers = [p for p in playing if p.pid in cart.pushers]
                for p in pushers:
                    self.score(p, 10, "beat", "rr_beat_freight")
                self.send({"t": "rrx", "k": "beat", "lane": lane, "team": cart.team})
                self.event("rr_beat_freight", pushers[0] if pushers else None, cart.team)
        if head >= self.track.length + self.length + 10.0:
            self.finish(moment)

    def _credit(self, cart, moment: float) -> None:
        """The one who called this train down, when it holds the other cart."""
        if self.credited or self.called_by is None:
            return
        pid, team = self.called_by
        if cart.team == team:
            return
        self.credited = True
        caller = self.w.players.get(pid)
        if caller is not None:
            self.score(caller, 10, "", "rr_freight_calls")

    # ------------------------------------------------------------ carts
    def limit(self, cart, moment):
        if not self.closed(cart.lane, moment):
            return None
        stop = self.cross[cart.lane][0] - SWEEP_HOLD
        if cart.d <= stop + 0.05:
            return (stop, self.reason)
        return None

    def drive(self, cart, pushers, contested, braked, dt, moment):
        if not self.closed(cart.lane, moment):
            return None
        d_x = self.cross[cart.lane][0]
        if d_x - SWEEP_HOLD + 0.05 < cart.d < d_x + SWEEP_CLEAR:
            if pushers and not contested and not braked:
                return None
            return -SWEEP_ROLL
        return None

    def floor(self, cart):
        return self.cross[cart.lane][0] - SWEEP_HOLD if cart.lane in self.cross else 0.0

    # -------------------------------------------------------- holding E
    def callable(self, moment: float) -> bool:
        return self.phase == "idle" and moment >= self.call_ok and self.next_at - moment > CALL_SOON

    def what_here(self, player, moment):
        if player.extra.get("coal") or not self.callable(moment):
            return None
        for i, box in enumerate(self.calls):
            if self.near(player, box, CALL_R, 4.0):
                return ("call", i, CALL_HOLD)
        return None

    def do(self, player, kind, key, moment):
        if kind != "call":
            return False
        if not self.callable(moment):
            return True
        self.calls_made += 1
        self.score(player, 4, "called")
        self.start(moment, player)
        return True

    # ------------------------------------------------------------ state
    def state(self, moment):
        out: Dict[str, Any] = {"phase": self.phase, "style": self.style}
        if self.phase == "run":
            out.update({"dir": self.dir, "head": round(self.head(moment), 1),
                        "speed": self.speed, "len": self.length, "n": self.count})
        else:
            out["next"] = round(max(0.0, self.next_at - moment), 1)
            out["call"] = 1 if self.callable(moment) else 0
        return {"sweep": out}

    def context(self):
        moment = now()
        if self.phase == "run":
            return ["%s is coming through: both crossings are shut until it has gone by, "
                    "and anybody on the line is in its way." % self.what.capitalize()]
        return ["%s is due in about %d seconds%s." % (
            self.what.capitalize(), max(0, int(self.next_at - moment)),
            "; a call box can bring it now" if self.callable(moment) else "")]

    # ------------------------------------------------------------- bots
    def _danger(self, pos: Sequence[float], moment: float) -> Optional[Tuple[float, float]]:
        """(distance along the line, which side) if this spot is in the way
        of a train that is coming or going by."""
        if self.phase != "run":
            return None
        s, off = self.track.project(pos[0], pos[2])
        if off > self.half + 6.0 or abs(pos[1] - self.track.height(s)) > SWEEP_DY:
            return None
        u = self.travel(s)
        head = self.head(moment)
        if head - self.length - 4.0 <= u <= head + SWEEP_WARN:
            return s, off
        return None

    def urgent(self, brain):
        return self._danger(brain.p.pos, now()) is not None

    def flee(self, brain):
        p = brain.p
        danger = self._danger(p.pos, now())
        if danger is None:
            return None
        s, _off = danger
        x, z, yaw = self.track.at(s)
        rx, rz = math.cos(yaw), -math.sin(yaw)
        side = 1.0 if (p.pos[0] - x) * rx + (p.pos[2] - z) * rz >= 0 else -1.0
        out = self.half + 10.0
        self.w.doing(brain, "getting off the line -- %s" % self.what)
        return [x + rx * side * out, p.pos[1], z + rz * side * out]

    def _box_near(self, pos) -> Tuple[int, Optional[List[float]]]:
        best, best_i, best_d = None, -1, 1e9
        for i, box in enumerate(self.calls):
            d = flat(box, pos)
            if d < best_d:
                best, best_i, best_d = box, i, d
        return best_i, best

    def _worth_calling(self, team: str) -> bool:
        own = self.w.carts.get(team)
        rival = self.w.carts.get(self.w.rival(team))
        if own is None or rival is None or rival.lane not in self.cross:
            return False
        to_go = self.cross[rival.lane][0] - rival.d
        mine = self.cross[own.lane][0] - own.d
        return SWEEP_HOLD + 1.0 < to_go < 80.0 and not (-SWEEP_CLEAR < mine < 100.0)

    def bot_job(self, brain, own, rival, moment):
        if not self.calls or not self.callable(moment) or not self._worth_calling(brain.p.team):
            return None
        rng = brain.rng
        if brain.role not in ("raider", "flex") and rng.random() > 0.2:
            return None
        if rng.random() > 0.25 + self.w.pct("twist") * 0.6:
            return None
        i, box = self._box_near(brain.p.pos)
        if box is None or flat(box, brain.p.pos) > 170.0:
            return None
        return {"k": "call", "at": [box[0], box[1], box[2]], "r": CALL_R - 1.6,
                "key": "call%d" % i, "say": "calling %s down on their cart" % self.what,
                "for": 25.0}

    def job_valid(self, job, team):
        if job["k"] != "call":
            return None
        return self.callable(now()) and self._worth_calling(team)

    # ------------------------------------------------------------ tests
    def observe(self):
        return {"passes": self.passes, "calls": self.calls_made, "hits": self.hits,
                "held": self.held_seen, "beats": self.beats, "phase": self.phase}

    def selftest(self, observations):
        passes = max([o.get("passes", 0) for o in observations] or [0])
        held = max([o.get("held", 0) for o in observations] or [0])
        calls = max([o.get("calls", 0) for o in observations] or [0])
        return [("trains come through on the timetable", passes >= 2, passes),
                ("a cart is held at a crossing, or a train is called down",
                 held > 0 or calls > 0, {"held": held, "calls": calls})]


# ========================================================== the gushers
GUSH_EVERY = (40.0, 58.0)     # between one well blowing and the next, left alone
GUSH_WARN = 6.0               # the hiss before it blows
GUSH_R = 10.0                 # deadly this close to the wellhead
GUSH_EDGE = 16.0              # a bad burn out to here
FIRE_SECONDS = 13.0           # how long the spilled oil burns on the track
FIRE_HALF = 9.0               # the burning stretch either side of its middle
FIRE_HOLD = 4.0               # how far short of the flames a cart stops
FIRE_BURN = 22.0              # damage a second standing in it
WELL_REST = 26.0              # a well that has blown is spent this long
VALVE_R = 4.4
VALVE_OPEN = 2.0
VALVE_SHUT = 1.4


@register
class Gushers(Twist):
    """Gusher Flats: the wells beside the lines (``points["well"]``: each
    a wellhead ``p``, the ``lane`` it stands by and how far along it
    ``d``).  Every so often one blows out of its own accord -- a hiss for
    six seconds, then a column of oil and fire: deadly at the wellhead, a
    burn round it -- and the oil it throws burns across its line for a
    while, holding any cart short of the flames.

    Anyone can open a quiet well's valve (hold E at it) to set it blowing
    now -- by the other company's line, just ahead of their cart, if they
    are any good -- and anyone can shut it again while it hisses."""

    kind = "gushers"
    welcome = ("The wells blow out by themselves, and the burning oil holds a cart short of the "
               "flames. Hold E at a wellhead's valve to set it blowing beside their line -- or to "
               "shut one that is hissing beside yours.")
    jobs = ("gushers", "capped")
    award = ("gushers", "Wildcatter", "set %d wells blowing")
    job_lines = {"open_valve": ["opening a valve on them", "gusher time lol", "blowing a well"],
                 "shut_valve": ["capping that well", "shutting the valve", "well about to blow on us"]}

    def setup(self, area, extra, points, moment):
        self.wells: List[Dict[str, Any]] = []
        for i, m in enumerate(points.get("well", [])):
            lane = str(m.get("lane") or "a")
            path = self.w.lanes.get(lane)
            d = float(m.get("d", 0.0))
            if path is None:
                continue
            self.wells.append({"i": i, "p": list(m["p"]), "head": list(m.get("head") or m["p"]),
                               "lane": lane, "d": d, "state": "idle",
                               "until": 0.0, "rest": 0.0, "by": None, "fire": 0.0,
                               "name": str(m.get("name") or "a well")})
        self.next_at = moment + 1e9
        self.blowouts = 0
        self.opened = 0
        self.capped = 0
        self.held_seen = 0
        self.burned = 0

    def on_live(self, moment):
        self.next_at = moment + self.w.rng.uniform(*GUSH_EVERY) * 0.6

    # ------------------------------------------------------------ wells
    def _hissing(self) -> Optional[Dict[str, Any]]:
        for well in self.wells:
            if well["state"] == "warn":
                return well
        return None

    def _start(self, well, moment: float, by=None) -> None:
        well["state"] = "warn"
        well["until"] = moment + GUSH_WARN
        well["by"] = (by.pid, by.team) if by is not None else None
        self.send({"t": "rrx", "k": "gush", "i": well["i"], "state": "warn", "in": GUSH_WARN,
                   "by": by.username if by is not None else "", "team": by.team if by is not None else ""})
        if by is not None:
            self.event("rr_gusher_opened", by, self.lane_team(well["lane"]),
                       what=self.w._place(well["p"]))
        self.w._broadcast_state()

    def _blow(self, well, playing, moment: float) -> None:
        well["state"] = "fire"
        well["fire"] = moment + FIRE_SECONDS
        well["rest"] = moment + WELL_REST
        self.blowouts += 1
        self.next_at = moment + self.w.rng.uniform(*GUSH_EVERY)
        wx, wy, wz = well["head"]
        for player in playing:
            dist = math.hypot(player.pos[0] - wx, player.pos[2] - wz)
            if abs(player.pos[1] - wy) > 12.0:
                continue
            if dist < GUSH_R:
                self.w.apply_damage(player, None, 95.0, "the gusher")
            elif dist < GUSH_EDGE:
                self.w.apply_damage(player, None, 35.0, "the gusher")
        self.send({"t": "rrx", "k": "gush", "i": well["i"], "state": "blow"})
        self.w._broadcast_state()

    def _fire_span(self, well) -> Tuple[float, float]:
        return well["d"] - FIRE_HALF, well["d"] + FIRE_HALF

    def tick(self, playing, dt, moment):
        if not self.wells:
            return
        hissing = self._hissing()
        if hissing is None and moment >= self.next_at:
            quiet = [w for w in self.wells if w["state"] == "idle" and moment >= w["rest"]]
            if quiet:
                self._start(self.w.rng.choice(quiet), moment)
        for well in self.wells:
            if well["state"] == "warn" and moment >= well["until"]:
                self._blow(well, playing, moment)
            elif well["state"] == "fire":
                if moment >= well["fire"]:
                    well["state"] = "idle"
                    well["by"] = None
                    self.send({"t": "rrx", "k": "gush", "i": well["i"], "state": "out"})
                    self.w._broadcast_state()
                    continue
                # the burning stretch: anybody standing in it burns
                path = self.w.lanes[well["lane"]]
                d0, d1 = self._fire_span(well)
                for player in playing:
                    d, off = path.project(player.pos[0], player.pos[2])
                    if d0 <= d <= d1 and off < 4.5 and abs(player.pos[1] - path.height(d)) < 5.0:
                        self.burned += 1
                        self.w.apply_damage(player, None, FIRE_BURN * dt, "the burning oil")
                # the cart it holds: credit whoever set it blowing
                cart = self.cart_on(well["lane"])
                if cart is not None and cart.held == "fire":
                    self.held_seen += 1
                    if well["by"] is not None:
                        pid, team = well["by"]
                        well["by"] = None
                        caller = self.w.players.get(pid)
                        if caller is not None and team != cart.team:
                            self.score(caller, 10, "", "rr_gushers")

    # ------------------------------------------------------------ carts
    def limit(self, cart, moment):
        stops = []
        for well in self.wells:
            if well["state"] != "fire" or well["lane"] != cart.lane:
                continue
            d0, _d1 = self._fire_span(well)
            if cart.d <= d0 - FIRE_HOLD + 0.05:
                stops.append((d0 - FIRE_HOLD, "fire"))
        return min(stops) if stops else None

    # -------------------------------------------------------- holding E
    def what_here(self, player, moment):
        if player.extra.get("coal"):
            return None
        for well in self.wells:
            if not self.near(player, well["p"], VALVE_R, 5.0):
                continue
            if well["state"] == "warn":
                return ("shut", well["i"], VALVE_SHUT)
            if well["state"] == "idle" and moment >= well["rest"] and self._hissing() is None:
                return ("open", well["i"], VALVE_OPEN)
        return None

    def do(self, player, kind, key, moment):
        if kind not in ("open", "shut"):
            return False
        well = next((w for w in self.wells if w["i"] == key), None)
        if well is None:
            return True
        if kind == "open":
            if well["state"] != "idle" or moment < well["rest"] or self._hissing() is not None:
                return True
            self.opened += 1
            self.score(player, 4, "gushers")
            self._start(well, moment, player)
            return True
        if well["state"] != "warn":
            return True
        well["state"] = "idle"
        well["rest"] = moment + 10.0
        well["by"] = None
        self.capped += 1
        self.score(player, 8, "capped", "rr_capped")
        self.next_at = max(self.next_at, moment + 14.0)
        self.send({"t": "rrx", "k": "gush", "i": well["i"], "state": "shut", "by": player.username,
                   "team": player.team})
        self.event("rr_gusher_capped", player, player.team, what=self.w._place(well["p"]))
        self.w._broadcast_state()
        return True

    # ------------------------------------------------------------ state
    def state(self, moment):
        out = []
        for well in self.wells:
            row = {"s": well["state"]}
            if well["state"] == "warn":
                row["left"] = round(max(0.0, well["until"] - moment), 1)
            elif well["state"] == "fire":
                row["left"] = round(max(0.0, well["fire"] - moment), 1)
            elif moment < well["rest"]:
                row["rest"] = round(well["rest"] - moment, 1)
            out.append(row)
        return {"wells": out}

    def context(self):
        lines = []
        for well in self.wells:
            team = self.w.team_name(self.lane_team(well["lane"]))
            if well["state"] == "warn":
                lines.append("A well beside %s's line is hissing and about to blow." % team)
            elif well["state"] == "fire":
                lines.append("Oil is burning across %s's line." % team)
        return lines

    # ------------------------------------------------------------- bots
    def _danger_well(self, pos) -> Optional[Dict[str, Any]]:
        for well in self.wells:
            if well["state"] == "warn" and flat(pos, well["head"]) < GUSH_EDGE + 3.0:
                return well
        return None

    def urgent(self, brain):
        return self._danger_well(brain.p.pos) is not None or self._in_fire(brain.p.pos)

    def _in_fire(self, pos) -> bool:
        for well in self.wells:
            if well["state"] != "fire":
                continue
            path = self.w.lanes[well["lane"]]
            d, off = path.project(pos[0], pos[2])
            d0, d1 = self._fire_span(well)
            if d0 - 2 <= d <= d1 + 2 and off < 7.0:
                return True
        return False

    def flee(self, brain):
        p = brain.p
        well = self._danger_well(p.pos)
        if well is not None:
            # somebody of ours shutting it stays put; everybody else runs
            job = p.extra.get("rr_job") or {}
            if job.get("k") == "shut_valve" and flat(p.pos, well["p"]) < VALVE_R:
                return None
            hx, hz = well["head"][0], well["head"][2]
            dx, dz = p.pos[0] - hx, p.pos[2] - hz
            dist = max(0.1, math.hypot(dx, dz))
            k = (GUSH_EDGE + 8.0) / dist
            self.w.doing(brain, "getting clear of the well")
            return [hx + dx * k, p.pos[1], hz + dz * k]
        if self._in_fire(p.pos):
            for well in self.wells:
                if well["state"] != "fire":
                    continue
                path = self.w.lanes[well["lane"]]
                d, _off = path.project(p.pos[0], p.pos[2])
                x, z, yaw = path.at(d)
                rx, rz = math.cos(yaw), -math.sin(yaw)
                side = 1.0 if (p.pos[0] - x) * rx + (p.pos[2] - z) * rz >= 0 else -1.0
                self.w.doing(brain, "out of the fire")
                return [x + rx * side * 10.0, p.pos[1], z + rz * side * 10.0]
        return None

    def bot_job(self, brain, own, rival, moment):
        rng = brain.rng
        twist = self.w.pct("twist")
        team = brain.p.team
        # a well hissing beside our own line: somebody near shuts it
        for well in self.wells:
            if well["state"] == "warn" and well["lane"] == own.lane and \
                    flat(well["p"], brain.p.pos) < 70.0 and well["until"] - moment > 2.2 and \
                    rng.random() < 0.3 + twist * 0.6:
                return {"k": "shut_valve", "i": well["i"], "at": list(well["p"]), "r": VALVE_R - 1.6,
                        "key": "shut%d" % well["i"], "say": "shutting the valve on a hissing well",
                        "for": 8.0}
        if self._hissing() is not None:
            return None
        if brain.role not in ("raider", "flex") and rng.random() > 0.2:
            return None
        # a quiet well a little ahead of their cart: open it
        best = None
        for well in self.wells:
            if well["lane"] != rival.lane or well["state"] != "idle" or moment < well["rest"]:
                continue
            ahead = well["d"] - FIRE_HALF - rival.d
            if 20.0 < ahead < 70.0 and flat(well["p"], brain.p.pos) < 150.0:
                best = well
                break
        if best is None or rng.random() > 0.25 + twist * 0.6:
            return None
        return {"k": "open_valve", "i": best["i"], "at": list(best["p"]), "r": VALVE_R - 1.6,
                "key": "open%d" % best["i"], "say": "opening a well's valve by their line", "for": 25.0}

    def job_valid(self, job, team):
        well = next((w for w in self.wells if w["i"] == job.get("i")), None)
        if job["k"] == "shut_valve":
            return well is not None and well["state"] == "warn"
        if job["k"] == "open_valve":
            if well is None or well["state"] != "idle" or now() < well["rest"] or self._hissing() is not None:
                return False
            rival = self.w.carts.get(self.w.rival(team))
            return rival is not None and -5.0 < well["d"] - FIRE_HALF - rival.d < 80.0
        return None

    # ------------------------------------------------------------ tests
    def observe(self):
        return {"blowouts": self.blowouts, "opened": self.opened, "capped": self.capped,
                "held": self.held_seen, "burned": self.burned}

    def selftest(self, observations):
        blowouts = max([o.get("blowouts", 0) for o in observations] or [0])
        return [("the wells blow out", blowouts >= 2, blowouts)]
